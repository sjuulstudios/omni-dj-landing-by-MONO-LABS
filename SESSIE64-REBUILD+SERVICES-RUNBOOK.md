# Sessie 64 (2026-05-30) — Runbook: .app rebuild + externe services

> Dit is jouw stap-voor-stap draaiboek. Alle terminal-regels zijn letterlijk
> bedoeld: kopieer ze 1 voor 1, draai, en lees de uitleg voordat je de volgende doet.
> Doe NIET meerdere stappen tegelijk. Bij twijfel: stop en vraag.

---

## Status na sessie 64 (wat Claude deze sessie heeft gecheckt)

Stap 1 (git) is KLAAR en geverifieerd:
- Rebrand-commit `f1211ff` ("Rebrand: Clip Live -> Omni DJ") staat op `main`.
- Feature-branch is ge-merged, working tree schoon (alleen `system_fonts_cache.json` is een gegenereerde cache, niet relevant).

Code-side klaar voor rebuild (geverifieerd door Claude):
- Alle 9 kritische Python-bestanden compileren schoon.
- Geen achtergebleven `CLIP_LIVE_` env-vars of `clipLive.` localStorage-keys in de code.
- `OmniDJ.spec` correct: bundle-ID `com.monolabs.omnidj`, naam "Omni DJ", CFBundleName goed.
  (Claude fixte 1 cosmetisch comment in de spec-docstring; geen functioneel effect.)
- `build_macos.sh` en `entitlements.plist` aanwezig; geen oude namen in build-script.

TWEE DINGEN OM TE WETEN VOOR JE BOUWT:
1. Het app-icoon (zwarte bolletjes op witte achtergrond) staat klaar als losse
   onderdelen in `static/`, maar de `.icns` zelf moet jij 1x op je Mac maken (het
   tool `iconutil` is Mac-only). Doe dat in stap B0 hieronder. Sla je dat over, dan
   bouwt de app gewoon met het generieke Mac-icoon (spec valt graceful terug).
2. In de PLAN-REBRAND staan rebuild-stap 4 (handmatig pyinstaller) en stap 5
   (build_macos.sh) allebei. Dat is dubbel: `build_macos.sh` draait pyinstaller al
   zelf. Gebruik daarom alleen `build_macos.sh dmg` (stap B4 hieronder). Niet allebei.

---

# STAP 2 — .app rebuild (op jouw Mac)

> Dit kan Claude niet voor je doen: PyInstaller draait op jouw Mac, niet in de sandbox.

## B0. App-icoon maken (1x, zwarte bolletjes op wit)

De icoon-onderdelen staan al klaar in `static/`: `icon.svg`, `icon_1024.png`, de map
`Omni DJ.iconset` (alle 10 maten) en het script `make_icns.sh`. Maak de echte .icns:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/static"

Daarna:

./make_icns.sh

Resultaat: `static/icon.icns`. De OmniDJ.spec pikt dit automatisch op bij de build.
(Werkt make_icns.sh niet, draai dan handmatig: iconutil -c icns "Omni DJ.iconset" -o icon.icns)

## B1. Smoketest dev-server eerst (branding klopt voor je bouwt)

Open Terminal en plak:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"

Daarna:

./start.sh

Open in je browser:

http://127.0.0.1:5555

Controleer met je ogen:
- Titel/branding = "Omni DJ"
- Inloggen werkt (en zet `omniDj.session` in localStorage, niet `clipLive.session`)
- Een upload + analyse + export werkt

Stop de dev-server daarna met Ctrl+C in de Terminal.

## B2. Venv activeren + tooling checken

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"

source venv/bin/activate

which pyinstaller || pip install pyinstaller dmgbuild

(Eerste deel checkt of pyinstaller er is. Staat hij er niet, dan installeert de
tweede helft pyinstaller + dmgbuild. Beide draaien is veilig.)

## B3. Oude build-artefacten weggooien

rm -rf build/ dist/

(Dit verwijdert alleen de vorige PyInstaller-output. De broncode blijft ongemoeid.)

## B4. De bundle bouwen (1 commando doet alles)

./build_macos.sh dmg

Het argument `dmg` zorgt dat naast de .app ook de .dmg wordt gemaakt. Het script draait
zelf PyInstaller met OmniDJ.spec en kopieert ffmpeg + ffprobe in de bundle. Vereist dat
ffmpeg op je Mac geinstalleerd is (anders: brew install ffmpeg). Resultaat na 5 a 10 min:

dist/Omni DJ.app
dist/Omni DJ.dmg

## B5. De bundle testen

open "dist/Omni DJ.app"

Controleer:
- Opent de browser op de juiste poort
- Branding = Omni DJ
- Een volledige analyse + export werkt VANUIT de .app (niet alleen dev-server)

## B6. Oude app vervangen in /Applications

Eerst de oude weg (let op: de oude heette "Clip Live"):

rm -rf "/Applications/Clip Live.app"

Dan de nieuwe erin:

cp -R "dist/Omni DJ.app" "/Applications/"

## B7. Alleen als de app niet wil starten: oude bundle-cache wissen

rm -rf ~/Library/Saved\ Application\ State/com.sjuulstudios.cliplive.savedState

(Dit is een opruim-stap voor een vastgelopen oude bundle-state. Overslaan als de
app gewoon start.)

---

# STAP 3 — Externe services rebrand naar omnidj.com

> Dashboards (Supabase / Stripe / Cloudflare) vereisen jouw login. Claude kan deze
> niet voor je doen. Doe ze in deze volgorde. Alles is TEST-mode; geen users, geen
> migratie-risico.

## 3A. Supabase (project ref blijft `lbabsffxefkrxwzkbzar`)

1. https://supabase.com/dashboard → kies het project (oude naam "Clip Live"/"Clip Drop").
2. Settings → General → Project name → "Omni DJ" → Save.
3. Authentication → Email Templates → voor elk template (Confirm signup, Magic Link,
   Change Email, Reset Password):
   - "Clip Live"/"Clip Drop" → "Omni DJ"
   - `clipdroplive.com` / `djclips.nl` → `omnidj.com`
   - Reset Password extra checken: footer + sender-naam. Save per template.
4. Authentication → URL Configuration:
   - Site URL: `https://omnidj.com` (of lokaal `http://127.0.0.1:5555` als nog niet live)
   - Redirect URLs (toevoegen/vervangen):
     - `http://127.0.0.1:5555/static/reset-password.html`
     - `https://omnidj.com/reset-password`
   - Oude `clipdroplive.com` / `djclips.nl` entries verwijderen. Save.
5. (Optioneel, branding) Project Settings → Authentication → SMTP Settings:
   - Enable custom SMTP, sender `omnidj@monohq-labs.com`, naam "Omni DJ",
     host/port/user/pass van je provider. Save → test-mail.
     (Bij Google Workspace voor monohq-labs.com: App-Password of SMTP-relay nodig.)
6. Admin-whitelist. SQL Editor → New query. Check eerst je schema:

   select * from profiles limit 5;

   Dan (pas adressen aan naar je echte admin-adressen):

   update profiles set plan = 'unlimited', is_admin = true
   where email in ('omnidj@monohq-labs.com', 'sjuul@monohq-labs.com');

   Run → controleer dat de rows geüpdatet zijn.

## 3B. Stripe (price-IDs blijven hetzelfde, TEST-mode)

Pro = `price_1TUoYNA5DKhJaSAF6xynooY9` · Studio = `price_1TUoZCA5DKhJaSAFI7AMgAbA`

1. https://dashboard.stripe.com → Settings → Business settings → Public details:
   - Public business name: `Omni DJ` (of `MONO LABS`)
   - Statement descriptor: `OMNI DJ` (max 22 tekens)
   - Branding: logo + kleuren (optioneel). Save.
2. Product catalog → open elk product:
   - "Clip Live — Pro" → "Omni DJ — Pro"
   - "Clip Live — Studio" → "Omni DJ — Studio"
   - Check description-velden op oude namen. Save per product.
3. Developers → Webhooks: check dat endpoint
   `https://lbabsffxefkrxwzkbzar.supabase.co/functions/v1/stripe-webhook`
   bestaat + enabled is. Geen URL-wijziging nodig.
4. Settings → Billing → Customer portal: logo + naam "Clip Live" → "Omni DJ". Save.
5. LIVE-mode: UIT SCOPE deze sessie. Eerst TEST-mode stabiel onder nieuwe naam,
   daarna pas live (zie STRIPE-DNS-RUNBOOK.md).

## 3C. Cloudflare (omnidj.com vanaf scratch)

> Registrar = TransIP (door jou bevestigd). Stap 2 is daarop afgestemd.
> Let op: e-mail voor monohq-labs.com loopt los van omnidj.com; check dat je geen
> bestaande MX/mail-records van omnidj.com weggooit als je die al gebruikt.

1. https://dash.cloudflare.com → Add a site → `omnidj.com` → plan Free.
   Cloudflare scant bestaande DNS-records; verwijder ongebruikte default-records.
2. Cloudflare geeft 2 nameservers (`xxx.ns.cloudflare.com` + `yyy.ns.cloudflare.com`).
   omnidj.com staat bij TransIP, dus:
   - Log in op TransIP → Mijn Domeinen → omnidj.com.
   - Tab Nameservers → kies "Gebruik eigen nameservers" (niet de TransIP-defaults).
   - Verwijder de bestaande TransIP-nameservers, vul beide Cloudflare-nameservers in.
   - Save.
   (Propagatie: 5 min tot 24 u. Cloudflare mailt zodra actief. Pas DAARNA stap 3 en 4.)
3. Zodra "Active": SSL/TLS → Overview → Full (of Full strict met origin-cert).
   Edge Certificates → Always Use HTTPS → On.
4. DNS-records voor de landing: volledige set in
   `PLAN-DNS-TRANSIP-CLOUDFLARE-2026-05-28.md`.
5. Pages-deploy: in `omnidj.com/` repo → `npm run build` → `out/` → Cloudflare Pages
   (zie PLAN-DNS-doc).

## 3D. Vervolg (later, eigen plannen)

- Google Workspace mail-routing voor monohq-labs.com (App-password/SMTP-relay) →
  PLAN-REBRAND sectie 5.4.
- Apple Developer codesigning → PLAN-APPLE-DEVELOPER-2026-05-28.md.
- Stripe LIVE-mode → STRIPE-DNS-RUNBOOK.md (pas nadat omnidj.com werkt).

---

## Wat deze sessie nog code-side is gedaan (naast de runbook)

- Landing-check: de actieve site `omnidj.com/` is schoon (domeinen + meta-tags op
  omnidj.com). 1 echte fix gedaan: mega-menu item "ClipDrop" → "Drop detection" in
  `omnidj.com/lib/content/megamenu.ts`. (Oude `landing/README.md` heeft nog
  `clipdrop-live-landing`-verwijzingen, maar dat is de verouderde losse landing, niet
  zichtbaar voor bezoekers; bewust gelaten.)
- App-icoon: zwarte bolletjes op witte afgeronde achtergrond, geleverd in `static/`
  (`icon.svg`, `icon_1024.png`, `Omni DJ.iconset/`, `make_icns.sh`). .icns maak je in
  stap B0.

## Open vraag

1. Welke admin-emails moeten unlimited krijgen in Supabase (3A.6)? Nu staat er
   `omnidj@monohq-labs.com` + `sjuul@monohq-labs.com` in de SQL. Pas aan als anders.
