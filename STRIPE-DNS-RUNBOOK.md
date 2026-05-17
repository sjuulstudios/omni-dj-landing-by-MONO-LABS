# Stripe Live + DNS — Switch Runbook

> Stap-voor-stap checklist om Clip Live van Stripe TEST-mode naar LIVE-mode te brengen, plus DNS + TLS opzet voor het launch-domein. Geschreven na een volledige code-audit op 2026-05-12.

## TL;DR — wat is er al en wat moet jij doen

**✅ Klaar (code-side, geverifieerd):**

- `billing.py` Stripe SDK wrapper — netjes met `_configured` fail-safe, Dutch error messages, dedup via `customer_email`
- `/api/billing/{health,config,checkout,portal}` endpoints in `app.py` — Bearer auth + JSON-payload validatie + correcte HTTP-codes
- Supabase Edge Function `supabase/functions/stripe-webhook/index.ts` — signature verification, idempotente DB-writes, 4 event-types
- Frontend `startCheckout()` + `openCustomerPortal()` + `handleBillingRedirect()` + `pollProfileForUpgrade()` (12 polls × 2.5s = 30s timeout)
- TEST-mode flow end-to-end live getest: HTTP 200, valide `cs_test_*` sessions, Stripe-hosted checkout URL retourneert HTTP 200 met TLS

**⚠ Jij moet doen (operationeel — kan niet zonder jouw credentials):**

1. Stripe Live activeren (account-verificatie)
2. Live products + prices opnieuw maken in Stripe Dashboard
3. Domein kopen + DNS configureren
4. Webhook endpoint registreren in Stripe Dashboard
5. Edge Function deployen + secrets zetten
6. `.env` updaten met live keys + restart server
7. Echte test-transactie met je eigen pas

---

## DEEL A — Stripe Live activeren

### A1. Account-verificatie afronden

1. Log in op https://dashboard.stripe.com
2. Klik linksonder op het toggle "Test mode" om naar Live mode te schakelen
3. Als de toggle disabled is → Stripe vraagt eerst om bedrijfsinfo: KvK-nummer (Sjuul Studios), BTW-nummer, bankrekening, bestuurder-info, ID-verificatie
4. Wacht op verificatie-bevestiging van Stripe (kan paar uur tot 1-2 dagen duren)

### A2. Live products + prices opnieuw maken

Test-mode products bestaan NIET in Live-mode. Je moet ze handmatig dupliceren.

In het Stripe Dashboard met Live-mode AAN:

1. **Products → Add product**
   - Naam: `Clip Live — Pro`
   - Pricing: Recurring, € maandbedrag, EUR
   - → Save → kopieer de **price_id** (begint met `price_`)

2. **Add product** nogmaals:
   - Naam: `Clip Live — Studio`
   - Pricing: Recurring, € maandbedrag, EUR
   - → Save → kopieer de **price_id**

Bewaar beide price_id's apart, je hebt ze straks nodig voor `.env`.

### A3. Live API keys ophalen

1. **Developers → API keys** (met Live-mode toggle AAN)
2. Kopieer:
   - **Publishable key** — begint met `pk_live_...`
   - **Secret key** — klik "Reveal", begint met `sk_live_...`

⚠ **Belangrijk**: deze keys zijn ECHT — een lek = echte geld-transacties. Bewaar in een password manager, nooit in git committen.

---

## DEEL B — Domein + DNS

### B1. Domein kopen

Mijn aanbeveling qua TLD: `.app` of `.live` voor herkenbaarheid. Voorbeelden van vrije namen kun je checken via https://www.namecheap.com of https://www.cloudflare.com/products/registrar/.

Cloudflare Registrar is iets goedkoper en bevat gratis SSL + DNS, dus mijn voorkeur als je nog geen voorkeur hebt.

### B2. DNS-architectuur

Drie hosts heb je nodig:

| Subdomain | Doel | Wat draait er |
|---|---|---|
| `cliplive.app` (root) | Marketing landing page | Statische site of Vercel/Netlify |
| `app.cliplive.app` | De Flask-app waar gebruikers inloggen | Jouw server / Mac / VPS |
| (Supabase URL is al `lbabsffxefkrxwzkbzar.supabase.co`) | Auth + DB + webhook edge function | Bestaat al |

⚠ **Cruciaal**: de Flask-app draait nu op jouw Mac op `127.0.0.1:5555`. Voor productie moet die ergens publiek bereikbaar staan. Drie opties:

- **A. Packaged .dmg/.exe distribueren** (zoals in `Clip Live/.claude/CLAUDE.md` als toekomstig doel staat): elke user runt de Flask-app lokaal, geen publiek domein nodig voor de app zelf. Alleen het marketing-domein `cliplive.app`. **Mijn voorkeur** — past bij de privacy- en upload-architectuur en is wat in jouw productplan staat.
- **B. SaaS-stijl deployment** op een VPS (Hetzner / DigitalOcean / Fly.io). Vereist herarchitectuur — alle videofiles moeten in cloud storage, ffmpeg moet in een container. Veel werk. Niet aanbevolen voor launch.
- **C. Hybrid**: marketing op cliplive.app, app blijft lokaal voor de eerste batch users.

Als je voor **A** of **C** kiest, hoef je ALLEEN het marketing-domein op te zetten. Geen `app.cliplive.app` nodig.

### B3. DNS records (voor marketing-domein)

Bij Cloudflare Registrar — DNS-tabblad:

```
Type   Name   Content                       Proxy
A      @      <Vercel/Netlify IP>           Aan
CNAME  www    cliplive.app                  Aan
```

Bij Vercel of Netlify: hun docs vertellen welke IP/CNAME exact moet. Standaard krijg je gratis TLS-cert via Let's Encrypt.

### B4. Email setup (optioneel maar aangeraden)

Voor `support@cliplive.app` / `noreply@cliplive.app`:

- Gebruik **Cloudflare Email Routing** (gratis) om mail naar je bestaande Gmail door te sturen
- Of **Resend** / **Postmark** als je transactional mail wilt versturen (welcome emails, password reset, invoice receipts)

DNS-records om spam-flagging te voorkomen:

```
TXT  @  "v=spf1 include:_spf.google.com ~all"  (als je via Cloudflare→Gmail routeert)
```

DKIM + DMARC records krijg je van je email-provider.

---

## DEEL C — Webhook deployen + Stripe registreren

### C1. Edge Function deployen

De webhook function staat al in `supabase/functions/stripe-webhook/index.ts`. Check of hij deployed is:

```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
supabase functions list
```

Als `stripe-webhook` er niet in staat:

```
supabase functions deploy stripe-webhook --no-verify-jwt
```

⚠ Vlag `--no-verify-jwt` is essentieel — Stripe stuurt geen Supabase JWTs, het stuurt zijn eigen `stripe-signature` header die de function zelf valideert.

Na deploy krijg je een URL terug. Die ziet eruit als:

```
https://lbabsffxefkrxwzkbzar.supabase.co/functions/v1/stripe-webhook
```

Bewaar die URL — straks plak je 'm in Stripe.

### C2. Edge Function secrets zetten

De Edge Function leest 5 secrets uit Supabase, NIET uit je lokale `.env`. Zet ze via:

```
supabase secrets set STRIPE_SECRET_KEY=sk_live_jouwSecretKey
supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_komtNa_C3
supabase secrets set STRIPE_PRICE_ID_PRO=price_uitA2
supabase secrets set STRIPE_PRICE_ID_STUDIO=price_uitA2
```

`SUPABASE_URL` en `SUPABASE_SERVICE_ROLE_KEY` worden automatisch ingespoten — niet zelf zetten.

### C3. Webhook registreren in Stripe Dashboard

In Stripe Dashboard (Live mode AAN):

1. **Developers → Webhooks → Add endpoint**
2. **Endpoint URL**: plak de Supabase function URL uit C1
3. **Events to send** — selecteer EXACT deze 4:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Save → Stripe geeft je een **signing secret** (begint met `whsec_`) → kopieer
5. Ga terug naar C2 en update `STRIPE_WEBHOOK_SECRET` met deze waarde

### C4. Webhook testen vanuit Stripe Dashboard

Stripe heeft een ingebouwde "Send test webhook" knop:

1. Klik je webhook endpoint open
2. Klik "Send test webhook" → kies `checkout.session.completed`
3. Verifieer: Response is 200, `received: true` in body

Als je een 400 ziet met "Bad signature" → je `STRIPE_WEBHOOK_SECRET` in Supabase klopt niet.
Als je een 500 ziet → check Supabase function logs via `supabase functions logs stripe-webhook`.

---

## DEEL D — .env update + server restart

### D1. .env updaten

Open `/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter/.env` en vervang de Stripe-block. **Maak eerst een backup**:

```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
cp .env .env.pre-live.bak
```

Pas dan in `.env` aan:

```
STRIPE_SECRET_KEY=sk_live_jouwSecretKey
STRIPE_PUBLISHABLE_KEY=pk_live_jouwPublishableKey
STRIPE_PRICE_ID_PRO=price_uitA2
STRIPE_PRICE_ID_STUDIO=price_uitA2
STRIPE_WEBHOOK_SECRET=whsec_uitC3
```

⚠ De `STRIPE_WEBHOOK_SECRET` in `.env` is alleen voor je Flask-app's eigen sanity-check (`/api/billing/health`). De ECHTE webhook-verificatie gebeurt in Supabase met de secret die je in C2 hebt gezet — die TWEE moeten dezelfde waarde hebben.

### D2. Server restarten

```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
./start.sh
```

(Of via `_restart.sh` als die nog bestaat — die handelt pkill + restart in één.)

### D3. Health-check

Open http://127.0.0.1:5555/api/billing/health in je browser. Verwacht:

```
{
  "configured": {
    "price_id_pro": true,
    "price_id_studio": true,
    "publishable_key": true,
    "secret_key": true,
    "webhook_secret": true
  },
  "ok": true,
  "test_mode": false      ← was true, moet nu FALSE zijn
}
```

`test_mode: false` is je groene vinkje dat de live-keys actief zijn.

---

## DEEL E — Echte test-transactie

⚠ Dit kost je geld. Maar je krijgt het terug door later via Customer Portal te cancellen + refunden in Stripe Dashboard.

### E1. Maak een nieuw test-account aan

Gebruik je echte email (NIET het `+wftest17` adres) zodat je de receipt mailtjes kunt zien. Bijvoorbeeld `business+livetest1@sjuulstudios.com`.

### E2. Doorloop checkout

1. Login op http://127.0.0.1:5555
2. Klik upgrade → Pro plan
3. Op de Stripe-hosted checkout: vul **je echte creditcard** in (Stripe accepteert geen test-cards in live mode)
4. Betaal

### E3. Verifieer in volgorde

1. **Stripe Dashboard** → Payments → check dat de payment binnenkwam
2. **Stripe Dashboard** → Customers → check dat er een nieuwe Customer is aangemaakt
3. **Stripe Dashboard** → Subscriptions → check dat er een active subscription staat
4. **Stripe Dashboard** → Webhooks → klik op je endpoint → bekijk Recent deliveries — `checkout.session.completed` moet 200 OK zijn
5. **Supabase Dashboard** → Table Editor → `profiles` → zoek je nieuwe user → check `plan = pro`, `stripe_customer_id` gevuld, `stripe_subscription_id` gevuld, `quota_reset_date` = ~30 dagen
6. **Frontend** → de account-chip moet "Pro" tonen
7. **Frontend** → klik "Manage subscription" → Customer Portal opent → cancel subscription
8. **Wacht op de period-end** (of fast-forward in Stripe Dashboard via "Cancel immediately") → de webhook moet `subscription.deleted` afhandelen → check profile.plan = 'free' weer

### E4. Refund jezelf

Stripe Dashboard → Payments → klik je test-betaling → Refund. Geld komt 5-10 werkdagen terug op je pas.

---

## DEEL F — Productie-hardening (optioneel maar belangrijk)

### F1. EU VAT inschakelen

In `billing.py` line 182 staat nu `'automatic_tax': {'enabled': False}`. Voor een NL-onderneming met EU-klanten **moet je BTW** rekenen.

1. Stripe Dashboard → **Tax** → activeer Stripe Tax
2. Voeg je BTW-nummer toe + tax registration voor NL
3. In de code: flip `'enabled': False` naar `'enabled': True`

Stripe rekent dan automatisch het juiste BTW-percentage gebaseerd op customer billing country.

### F2. Reverse-proxy / TLS lokaal

Als gebruikers de Flask-app lokaal draaien (`127.0.0.1:5555`), heb je geen TLS nodig voor de app zelf. Maar Stripe Checkout REQUIRES https success/cancel URLs in live mode. Dat is een issue.

Twee oplossingen:

- **A. Custom protocol handler**: registreer `cliplive://` URI scheme bij macOS/Windows, redirect daarheen ipv https. Vereist .dmg/.exe packaging met dat schema geregistreerd.
- **B. Use Stripe's `localhost` exception**: Stripe accepteert `http://localhost:5555/?billing=success` als success/cancel URL in LIVE mode (alleen localhost — niet 127.0.0.1 of een LAN IP). Pas dan `app.py` line 1352-1354 aan om altijd `localhost` te gebruiken.

Optie B is de snelste. Patch:

```python
# In api_billing_checkout, replace request.host_url.rstrip('/') with:
base = 'http://localhost:5555'  # Stripe requires localhost or https in live mode
```

### F3. Webhook idempotency-key dedup

De huidige webhook handler is idempotent in DB-writes (UPSERT-stijl `.update()`) maar slaat geen processed event-IDs op. Voor productie aangeraden: voeg een `webhook_events` tabel toe en check `event.id` voor je een handler runt. Niet kritiek voor launch, wel nice-to-have.

### F4. Quota-reset bij plan-change

In de huidige webhook: bij `subscription.updated` (bijv. Pro → Studio upgrade) wordt **alleen `plan`** geüpdatet, niet `quota_reset_date` of `usage_this_period`. Dat kan resulteren in: een gebruiker upgradet van Pro naar Studio, maar zijn quota loopt nog van de oude Pro-cycle. Mogelijk gewenst (geen reset = eerlijker), mogelijk niet (gebruiker verwacht reset bij upgrade). Beslis bewust.

### F5. Failed payment → soft-disable

Op `invoice.payment_failed` doet de huidige webhook alleen een `console.warn`. Stripe handelt retries automatisch via dunning, maar na 4 mislukte attempts cancelt Stripe de subscription. Dan komt `subscription.deleted` binnen en wordt user naar free gedowngrade. Werkt, maar geeft de user geen email/UI-melding dat z'n betaling mislukte. Overweging.

---

## Volgorde voor de switch

Mijn aanbeveling om te volgen:

1. ✅ **Deel A** (Stripe Live + products) — kan vandaag, wacht alleen op verificatie
2. ✅ **Deel C1+C2** (webhook deploy + secrets in Supabase) — kan ook vandaag, in TEST mode
3. ⏸ **Deel B** (domein + DNS) — alleen nodig als je niet voor packaged .dmg gaat. Kan parallel
4. **Deel C3+C4** (webhook in Stripe registreren + testen) — pas zodra A klaar is
5. **Deel D** (.env update + restart) — laatste stap voor switch
6. **Deel E** (echte test-transactie) — direct na D
7. **Deel F** (hardening) — na launch, in de eerste week iteratief

---

## Bekend te testen / open issues

Tijdens de audit gevonden — niet blokkerend voor launch maar weet ervan:

- **Webhook function deploy-status onbekend**: ik kan vanaf hier niet zien of `stripe-webhook` daadwerkelijk deployed staat in jouw Supabase project. Stap C1 moet je zelf verifiëren.
- **Pro + Studio prijs-bedragen**: niet gevalideerd in deze audit. Check in Stripe dashboard dat ze kloppen met wat je communiceert op je landing page.
- **Success-URL host**: huidige code gebruikt `request.host_url` dat `127.0.0.1:5555` produceert. In live mode moet dit minimaal `localhost` worden — zie Deel F2.
- **30-day quota cycle**: webhook zet `quota_reset_date = now + 30 days` op eerste checkout. Maar wat resetcyclus na maand 2+? Check of er een aparte cronjob/scheduled task is die maandelijks reset, anders blijft de date stuck. Niet in deze audit gecheckt.
- **EU VAT staat UIT**: zie F1, fix vóór eerste paying customer in EU.

---

## Status op moment van schrijven (2026-05-12)

- Stripe TEST-mode: ✅ volledig functioneel, alle endpoints reageren correct
- Stripe LIVE-mode: ⏳ wacht op jouw stappen in Deel A
- Supabase Edge Function: 📄 code staat klaar, deploy-status onbekend
- Domein: ⏳ nog niet gekozen
- DNS: ⏳ nog niet geconfigureerd
- TLS: ⏳ N/A tot domein gekozen is
