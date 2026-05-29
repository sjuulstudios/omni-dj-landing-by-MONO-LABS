# SESSIE 31 — Rebuild & smoketest runbook

> **Voor Sjuul.** Eén commando per regel, geen markdown fences,
> alle paden tussen quotes (spaties!). Stop bij elke vraag/error en
> rapporteer wat je ziet.

Sessie 31 voegt vier dingen toe bovenop sessie 30:

1. BPM/Key corner-stamp staat nu force-uit (alle nieuwe + her-gecutte clips zijn schoon)
2. Nieuwe tracking-modus "Fit (no zoom)" — letterbox, hele beeld blijft zichtbaar
3. Watermark feature is live (was eerst "Coming soon")
4. Brand Stack secties zijn nu inklapbaar

## Stap 0 — Vóór je iets bouwt: dev-server smoketest

Server starten (als hij nog niet draait):

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
./start.sh

Open in browser: http://127.0.0.1:5555

Check de volgende punten, één voor één:

1. Login werkt nog steeds (sessie 30c auto-refresh is niet geraakt)
2. Open een bestaande Lisa Korver clip in de editor → preview heeft GEEN "144 BPM · 4B" stamp meer rechtsboven (oude clips die nog niet gerecut zijn houden hun stamp tot recut; nieuwe en gerecutte clips zijn schoon)
3. Klik op Track in de editor → er staan nu DRIE knoppen in de segmented control: "Fit (no zoom)" (default, aan), "Follow horizontally", "Follow + zoom"
4. Klik "Fit (no zoom)" → hint-tekst zegt "The whole scene is visible — no crop, no zoom" en er volgt een automatische recut. Na ~10 seconden toont de preview het hele beeld met zwarte balken boven/onder
5. Klik "Follow horizontally" → hint switcht naar "Crops to 9:16 at full source height. The camera pans left-right between the keyframes..."
6. Ga naar Brand Stack (Scene 06) → de secties (Style, Fonts, Logo, Watermark, BPM & Key stamp...) zijn nu inklapbaar. Klik op een sectie-header → ze klapt dicht (chevron draait). Default: alleen de eerste sectie open
7. In Brand Stack → Watermark sectie → "Coming soon" label is weg. Upload een PNG of JPG (max 2 MB) → toast "Watermark added". Zet de toggle aan → kies hoek (br/tr/bl/tl/center) → schuif opacity (10–100%) en size (5–60%). Refresh de pagina → instellingen blijven bewaard
8. Recut een clip met watermark aan → het uitgevoerde mp4 heeft de watermark in de gekozen hoek met de gekozen opacity en size

Als één van deze 8 punten faalt, stop en meld het.

## Stap 1 — Edge function update-usage deployen

Als je deze stap in sessie 30 al gedaan hebt: skip. Anders:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
supabase functions deploy update-usage

Verwacht: "Deployed Function update-usage". Geen --no-verify-jwt flag.

Controleer dat de service-role key in de Supabase secrets staat:

supabase secrets list

SUPABASE_SERVICE_ROLE_KEY moet aanwezig zijn.

## Stap 2 — Build de .dmg

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
./build_macos.sh dmg

Verwacht: ~5 minuten. Output staat in dist/. Het script faalt als er
secrets (.env, *service_role*) in de bundle lekken — dat is geen bug,
dat is de defensieve scan uit sessie 30.

Als de build slaagt, ligt er:

dist/Clip Live.app
dist/Clip Live.dmg

## Stap 3 — Smoketest op de gebundelde .dmg

Sluit alle dev-servers af (Ctrl+C in de terminal die ./start.sh draait).

Open de .dmg en sleep "Clip Live.app" naar /Applications. Voor het
eerste startup-grant van Gatekeeper:

xattr -dr com.apple.quarantine "/Applications/Clip Live.app"

Daarna: rechts-klik → Open. Bevestig de Gatekeeper-prompt.

Log in met je bestaande account. Doe een mini-upload van een korte
DJ-set (mag een 30 sec test-mp4 zijn) en controleer:

1. Upload werkt zonder "supabase_admin niet geconfigureerd" error
2. Quota gaat van 0/2 naar 1/2 (of jouw plan-limiet)
3. Een clip in de editor toont GEEN BPM-stamp
4. Track-drawer toont drie opties incl. "Fit (no zoom)"
5. Brand Stack secties zijn inklapbaar
6. Watermark upload werkt

## Stap 4 — Bevestig en rapporteer

Stuur me terug:

- ✅ Welke stappen werkten?
- ❌ Welke faalden, met de exacte error?
- Een screenshot van een recut clip met watermark, om te bevestigen
  dat de overlay echt in de mp4 zit (niet alleen in de preview)

## Bekende beperking

Bestaande clips die in sessie 30 (of eerder) zijn gecut met BPM-stamp
houden die stamp tot ze gerecut worden. Dat is geen bug — de stamp zit
"baked in" in die mp4-bestanden. Klik in de editor "Re-cut" (of trigger
een tracking-change die een recut forceert) om ze schoon te krijgen.

## Backups in deze sessie

- dj-clip-cutter/app.py.pre-sessie31.bak
- dj-clip-cutter/cutter.py.pre-sessie31.bak
- dj-clip-cutter/static/index.html.pre-sessie31.bak
