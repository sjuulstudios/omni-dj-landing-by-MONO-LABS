# Sessie 65 (2026-05-30) - Externe services rebrand checklist (gecorrigeerd)

> Vervangt de service-stappen uit SESSIE64-REBUILD+SERVICES-RUNBOOK.md sectie 3.
> Reden: de admin-SQL in dat oude runbook klopte niet met je echte database-schema.
> Hieronder staat de gecorrigeerde versie. Dashboards (Supabase UI / Stripe / Cloudflare)
> vereisen jouw login; die kan ik niet voor je doen. De admin-SQL heb ik wel al via de
> Supabase-connectie geprobeerd (zie 3A.6).
>
> Doe de stappen 1 voor 1. Bij twijfel: stop en vraag.

---

## Wat ik deze sessie al heb gedaan (klaar, niets meer aan doen)

1. **App-icoon `.icns` is gemaakt** - staat in `Omni DJ/static/icon.icns`.
   Gebouwd uit je `icon_1024.png` met de volledige modern icon-set (16 t/m 1024px,
   incl. alle @2x Retina-maten). `OmniDJ.spec` pikt dit automatisch op bij de build
   (regels 121 + 138). Je hoeft `make_icns.sh` NIET meer te draaien.

2. **Supabase admin-SQL gecontroleerd tegen je echte schema.** De `profiles`-tabel heeft
   GEEN `is_admin`-kolom en GEEN `unlimited`-plan. Het oude runbook-commando zou dus
   gefaald zijn. De juiste waarden zijn `role = 'admin'` en `plan = 'studio'`
   (studio = onbeperkt gebruik, limit = null). De gecorrigeerde SQL heb ik gedraaid op
   `omnidj@monohq-labs.com` + `sjuul@monohq-labs.com`; die raakte 0 rijen omdat die
   accounts nog niet bestaan in de database. Draai 'm opnieuw NADAT die accounts zich
   hebben aangemeld (zie 3A.6).

---

## STAP 2 - .app rebuild (op jouw Mac)

> Het icoon is nu klaar, dus stap B0 uit het oude runbook (make_icns.sh) sla je over.
> De rest van de rebuild blijft hetzelfde. Korte versie hieronder; volledige uitleg
> staat in SESSIE64-REBUILD+SERVICES-RUNBOOK.md sectie STAP 2 (B1 t/m B7).

Open Terminal en plak 1 voor 1:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"

source venv/bin/activate

which pyinstaller || pip install pyinstaller dmgbuild

rm -rf build/ dist/

./build_macos.sh dmg

Resultaat na 5 a 10 min: dist/Omni DJ.app + dist/Omni DJ.dmg (nu met jouw icoon).
Daarna testen + in /Applications zetten zoals B5/B6 in het oude runbook.

---

## STAP 3 - Externe services rebrand naar omnidj.com

### 3A. Supabase (project ref `lbabsffxefkrxwzkbzar`, huidige naam "Clip Drop Live")

1. https://supabase.com/dashboard -> kies project "Clip Drop Live".
2. Settings -> General -> Project name -> "Omni DJ" -> Save.
3. Authentication -> Email Templates -> per template (Confirm signup, Magic Link,
   Change Email, Reset Password):
   - "Clip Live" / "Clip Drop" / "Clip Drop Live" -> "Omni DJ"
   - `clipdroplive.com` / `djclips.nl` -> `omnidj.com`
   - Reset Password extra checken: footer + sender-naam. Save per template.
4. Authentication -> URL Configuration:
   - Site URL: `https://omnidj.com` (of lokaal `http://127.0.0.1:5555` zolang nog niet live)
   - Redirect URLs (toevoegen/vervangen):
     - `http://127.0.0.1:5555/static/reset-password.html`
     - `https://omnidj.com/reset-password`
   - Oude `clipdroplive.com` / `djclips.nl` entries verwijderen. Save.
5. (Optioneel, branding) Project Settings -> Authentication -> SMTP Settings:
   - Enable custom SMTP, sender `omnidj@monohq-labs.com`, naam "Omni DJ",
     host/port/user/pass van je provider. Save -> test-mail.

6. **Admin-whitelist (GECORRIGEERD - gebruik DIT, niet het oude runbook-commando).**
   SQL Editor -> New query. Draai dit PAS NADAT je admin-accounts zich hebben aangemeld:

   update public.profiles
   set plan = 'studio', role = 'admin'
   where email in ('omnidj@monohq-labs.com', 'sjuul@monohq-labs.com');

   Controleer met:

   select email, plan, role from public.profiles
   where email in ('omnidj@monohq-labs.com', 'sjuul@monohq-labs.com');

   Verwacht: 2 rijen, beide plan=studio, role=admin.

   > Let op: je bestaande echte admin is nu `business@sjuulstudios.com`
   > (role=admin, plan=pro). Wil je die ook onbeperkt? Voeg 'm toe aan de `in (...)`-lijst.
   > Geldige role-waarden: 'user', 'beta', 'admin'. Geldige plans: 'free', 'pro', 'studio'.

### 3B. Stripe (TEST-mode, price-IDs blijven gelijk)

Pro = `price_1TUoYNA5DKhJaSAF6xynooY9` · Studio = `price_1TUoZCA5DKhJaSAFI7AMgAbA`

1. https://dashboard.stripe.com -> Settings -> Business settings -> Public details:
   - Public business name: `Omni DJ` (of `MONO LABS`)
   - Statement descriptor: `OMNI DJ` (max 22 tekens)
   - Logo + kleuren optioneel. Save.
2. Product catalog -> per product:
   - "Clip Live - Pro" -> "Omni DJ - Pro"
   - "Clip Live - Studio" -> "Omni DJ - Studio"
   - Description-velden op oude namen checken. Save per product.
3. Developers -> Webhooks: check dat endpoint
   `https://lbabsffxefkrxwzkbzar.supabase.co/functions/v1/stripe-webhook`
   bestaat + enabled is. Geen URL-wijziging nodig.
4. Settings -> Billing -> Customer portal: logo + naam "Clip Live" -> "Omni DJ". Save.
5. LIVE-mode: UIT SCOPE. Eerst TEST-mode stabiel onder nieuwe naam.

### 3C. Cloudflare (omnidj.com vanaf scratch, registrar = TransIP)

1. https://dash.cloudflare.com -> Add a site -> `omnidj.com` -> plan Free.
   Cloudflare scant bestaande DNS; verwijder ongebruikte default-records.
   LET OP: gooi geen bestaande MX/mail-records van omnidj.com weg als je die al gebruikt.
2. Cloudflare geeft 2 nameservers. omnidj.com staat bij TransIP, dus:
   - TransIP -> Mijn Domeinen -> omnidj.com -> tab Nameservers.
   - Kies "Gebruik eigen nameservers", verwijder TransIP-defaults, vul beide
     Cloudflare-nameservers in. Save. (Propagatie 5 min - 24 u.)
3. Zodra "Active": SSL/TLS -> Overview -> Full. Edge Certificates -> Always Use HTTPS -> On.
4. DNS-records voor de landing: volledige set in PLAN-DNS-TRANSIP-CLOUDFLARE-2026-05-28.md.
5. Pages-deploy: `omnidj.com/` repo -> `npm run build` -> `out/` -> Cloudflare Pages.

### 3D. Later (eigen plannen)

- Google Workspace mail-routing monohq-labs.com -> PLAN-REBRAND sectie 5.4.
- Apple Developer codesigning -> PLAN-APPLE-DEVELOPER-2026-05-28.md.
- Stripe LIVE-mode -> STRIPE-DNS-RUNBOOK.md (pas nadat omnidj.com werkt).

---

## Volgorde-advies

1. Supabase 3A (rename + templates + URL config) - laagste risico, geen DNS-afhankelijkheid.
2. Stripe 3B - onafhankelijk van DNS.
3. Cloudflare 3C - start de nameserver-wissel vroeg want propagatie duurt het langst.
4. .app rebuild (STAP 2) - kan parallel, hangt nergens van af.
5. Admin-SQL 3A.6 - pas nadat je admin-accounts bestaan.
