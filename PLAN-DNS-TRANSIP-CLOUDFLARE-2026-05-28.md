# DNS-migratie TransIP → Cloudflare + Landingspagina-hosting

> **Sessie 60 (2026-05-28). Onderdeel van `PLAN-BETA-LAUNCH-2026-05-28.md` Track C.**
>
> Doel: domein `omnidj.com` via Cloudflare laten lopen, landingspagina hosten via Cloudflare Pages, email-routing naar bestaande `monohq-labs.com` mailbox, SPF/DKIM/DMARC voor email-deliverability.
>
> Verwachte tijd: 1u actief werk + 1 tot 24u DNS-propagatie passief.

---

## 0. Voorwaarden

- TransIP-login werkt + 2FA paraat
- Cloudflare-account (gratis tier voldoende) — of nieuw aanmaken
- Toegang tot `monohq-labs.com` DNS (Cloudflare? TransIP? noteer waar)
- Beslissing genomen: landingspagina-content komt via Claude (`landing/index.html` + assets)

---

## 1. Cloudflare account klaarzetten

Sla over als je al een Cloudflare-account hebt.

1. Ga naar https://dash.cloudflare.com/sign-up
2. Maak account aan met `omnidj@monohq-labs.com` (consistent met afzender-strategie).
3. Verifieer email.
4. 2FA aanzetten (Settings → Authentication).

---

## 2. Domein `omnidj.com` toevoegen aan Cloudflare

1. Cloudflare dashboard → **Add a Site**.
2. Voer in: `omnidj.com`.
3. Kies plan: **Free**.
4. Cloudflare scant TransIP's huidige DNS. Aangezien je niks gekoppeld hebt, vindt 'ie niks of alleen TransIP-defaults.
5. Cloudflare geeft je **twee nameservers**, bijvoorbeeld:
   - `liam.ns.cloudflare.com`
   - `olga.ns.cloudflare.com`
   - (Echte namen variëren per account, neem de namen die Cloudflare jou geeft.)
6. **Noteer deze twee nameservers.** Je hebt ze nodig in Stap 3.
7. Klik nog NIET op "Done, check nameservers" — eerst Stap 3 uitvoeren.

---

## 3. Nameservers wisselen bij TransIP

**LET OP.** Vanaf het moment dat je nameservers wisselt, neemt Cloudflare DNS-control over. Alle DNS-records moeten daarna in Cloudflare staan, niet meer in TransIP. Aangezien je niks gekoppeld hebt, is het risico minimaal.

1. Log in op https://www.transip.nl/cp/
2. Ga naar **Domeinen → omnidj.com**.
3. Tab **Naamservers** (of "Nameservers").
4. Kies **Eigen nameservers gebruiken** (standaard staat TransIP).
5. Voer de twee Cloudflare-nameservers in die je in Stap 2 punt 6 noteerde.
6. **Save.**
7. TransIP toont een waarschuwing over downtime. Bevestig (niks van waarde gekoppeld dus geen probleem).

**Propagatie.** Duurt 1 tot 24u, meestal binnen 2u. Cloudflare stuurt je een email zodra ze het detecteren.

**Check tussendoor:**
```
dig +short NS omnidj.com
```
Zodra je daar de Cloudflare-namen ziet, ben je live. Voor die tijd zie je TransIP-namen of leeg.

---

## 4. DNS-records configureren in Cloudflare

Zodra nameservers actief zijn, ga naar **Cloudflare dashboard → omnidj.com → DNS → Records** en voeg toe:

### 4a. Web-records

| Type | Name | Content | Proxy | TTL |
|---|---|---|---|---|
| `CNAME` | `@` (= apex `omnidj.com`) | `omnidj-landing.pages.dev` | Proxied (oranje wolk) | Auto |
| `CNAME` | `www` | `omnidj-landing.pages.dev` | Proxied | Auto |
| `CNAME` | `app` | `omnidj-landing.pages.dev` | Proxied | Auto |
| `CNAME` | `downloads` | `omnidj-downloads.r2.cloudflarestorage.com` (later) | Proxied | Auto |

**Toelichting.**
- `omnidj-landing.pages.dev` is de Pages-deploy URL die je in Stap 5 krijgt. Voor nu placeholder, vul echte in zodra Pages live is.
- `app.omnidj.com` reserveert subdomein voor latere web-app (niet voor beta nodig, alvast).
- `downloads.omnidj.com` reserveert subdomein voor DMG-hosting.

### 4b. Email-routing records

Zorg dat email naar `omnidj@omnidj.com` doorgestuurd wordt naar `omnidj@monohq-labs.com`. Cloudflare Email Routing is gratis en ideaal hiervoor.

1. Ga naar **Cloudflare dashboard → omnidj.com → Email → Email Routing**.
2. Klik **Get Started**.
3. Cloudflare voegt automatisch toe:
   - `MX` records (3 stuks, Cloudflare email-servers)
   - `TXT` `@` met SPF: `"v=spf1 include:_spf.mx.cloudflare.net ~all"`
4. **Add destination address:** `omnidj@monohq-labs.com`. Verifieer per email.
5. **Add custom address rule:**
   - From: `omnidj@omnidj.com` → To: `omnidj@monohq-labs.com`
   - Optioneel: `sjuul@omnidj.com` → `sjuul@monohq-labs.com`
   - Catch-all: `*@omnidj.com` → `omnidj@monohq-labs.com` (vangt alle typos)

**Result.** Mails naar `omnidj@omnidj.com` komen aan in je `monohq-labs.com` inbox.

### 4c. DKIM + DMARC voor uitgaande email

Cloudflare Email Routing is alleen voor INKOMENDE. Voor UITGAANDE mail vanuit Supabase/Resend met als afzender `omnidj@monohq-labs.com` heb je DKIM nodig op `monohq-labs.com` zelf (niet op omnidj.com).

**Belangrijk.** SMTP afzender is `omnidj@monohq-labs.com`, dus SPF/DKIM/DMARC moeten op `monohq-labs.com` staan. Voor `omnidj.com` heb je dat alleen nodig als je ooit mails verzendt met `From: anything@omnidj.com`.

**Voor `monohq-labs.com`** (waar Supabase via Resend/SMTP gaat verzenden):
- Kijk waar `monohq-labs.com` DNS staat (waarschijnlijk Cloudflare of TransIP).
- Voeg Resend's DKIM-records toe (Resend genereert ze in dashboard).
- SPF: `"v=spf1 include:_spf.resend.com ~all"` als je via Resend stuurt.
- DMARC: `"v=DMARC1; p=quarantine; rua=mailto:omnidj@monohq-labs.com"`.

**Voor `omnidj.com`** (preventief):
- DMARC alleen: `TXT _dmarc` → `"v=DMARC1; p=reject; rua=mailto:omnidj@monohq-labs.com"`.
  Voorkomt dat scammers vanaf `*@omnidj.com` spoofen.
- SPF al gezet door Cloudflare Email Routing in 4b.

---

## 5. Cloudflare Pages project voor landingspagina

1. **Cloudflare dashboard → Workers & Pages → Create application → Pages.**
2. Twee opties:

### 5a. Optie 1 — Git-connect (aanbeveling voor lange termijn)

- Connect GitHub-account.
- Maak nieuwe repo `omnidj-landing` (kan ook bestaande repo zijn met `landing/` folder als subfolder).
- Push de `landing/`-folder daarheen.
- Cloudflare detecteert auto-deploy bij elke push naar `main`.
- Build settings: framework = None, build command = leeg, output directory = `/`.

### 5b. Optie 2 — Direct upload (sneller voor v1)

- Klik **Direct upload**.
- Zip de `landing/`-folder van `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/landing/`.
- Upload zip.
- Project-naam: `omnidj-landing`.

3. Wacht ~1 min op deploy.
4. Cloudflare geeft je een URL `https://omnidj-landing.pages.dev`.
5. **Test in browser.** Pagina moet laden.

---

## 6. Custom domain koppelen aan Pages

1. **Cloudflare Pages → omnidj-landing → Custom domains.**
2. **Set up a custom domain → `omnidj.com`.**
3. Cloudflare bevestigt dat 't intern routeert via de eerder gemaakte CNAME records.
4. Herhaal voor `www.omnidj.com`.
5. Wacht ~1 min op SSL-cert provisioning.
6. **Test:** `https://omnidj.com` moet je landingspagina tonen.

---

## 7. Cloudflare R2 voor DMG-hosting

R2 is Cloudflare's S3-equivalent, gratis tot 10GB storage + onbeperkt egress (voor downloads ideaal).

1. **Cloudflare dashboard → R2.**
2. Activeer R2 (vereist credit card op file, geen kosten onder limiet).
3. **Create bucket** → naam `omnidj-downloads`.
4. **Settings → Public Access** → enable + connect aan custom domain.
5. Maak in DNS een CNAME `downloads` naar de R2 public endpoint (Cloudflare doet dat semi-auto).
6. Upload je DMG (na Stap 8 in master plan):
   ```
   # via Cloudflare dashboard upload OF via wrangler:
   wrangler r2 object put omnidj-downloads/Omni-DJ-1.0.0.dmg \
     --file "dist/Omni DJ.dmg"
   ```
7. Test: `https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg` moet downloaden.

**Alternatief.** Als R2 te veel gedoe is: gewoon de DMG in `landing/assets/` zetten en als statische asset via Pages serveren. Werkt prima onder 25MB, voor grotere bestanden wordt Pages traag.

---

## 8. Verificatie-checklist

| Check | Hoe testen | Expected |
|---|---|---|
| Nameservers actief | `dig +short NS omnidj.com` | 2x cloudflare.com |
| Apex resolveert | `dig +short omnidj.com` | Cloudflare-IPs (proxied) |
| HTTPS werkt | curl `https://omnidj.com` | 200 + landing-HTML |
| `www` redirect of toont | browser | toont landing |
| Email-routing | stuur mail naar `omnidj@omnidj.com` | komt aan op `omnidj@monohq-labs.com` |
| SPF | `dig +short TXT omnidj.com \| grep spf` | `include:_spf.mx.cloudflare.net` |
| DMARC | `dig +short TXT _dmarc.omnidj.com` | `v=DMARC1; p=reject; ...` |
| DMG-download | klik op landing-pagina | DMG downloadt zonder errors |

---

## 9. Rollback

Als iets misgaat tijdens de wisseling:

1. **DNS-records corrupt:** in Cloudflare → DNS → Records → delete + opnieuw aanmaken volgens Stap 4.
2. **Nameservers werken niet:** terug naar TransIP defaults via Stap 3 (omgekeerd). Cloudflare DNS verdwijnt dan, maar je kunt opnieuw beginnen.
3. **Email-routing kapot:** disable in Cloudflare Email Routing en val terug op direct `monohq-labs.com` mailen.
4. **Pages-deploy stuk:** roll back via Cloudflare Pages → Deployments → vorige deployment "Rollback to this".

---

## 10. Open items voor latere sessies

- **CDN tuning.** Cache rules voor `/assets/*` op forever (1 jaar), HTML on origin (5 min).
- **WAF.** Default Cloudflare Free tier is OK, later Pro voor bot-protection.
- **Analytics.** Cloudflare Web Analytics gratis, in dashboard activeren.
- **Status page.** Eventueel een `status.omnidj.com` via Statuspage.io of een simpele Pages.
- **Subdomain `app.omnidj.com`.** Voor later web-app versie. CNAME staat al klaar.

---

## 11. Volgende actie

Na deze sessie:
1. Update `HANDOVER.md` met DNS-status.
2. Door naar `PLAN-BETA-LAUNCH-2026-05-28.md` Stap 6 (Supabase URLs + custom SMTP).
3. Of parallel: Stap 7 (landingspagina-content invullen + deployen).
