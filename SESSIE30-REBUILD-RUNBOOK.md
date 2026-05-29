# SESSIE 30 — Rebuild & smoketest runbook

> **Voor Sjuul.** Eén commando per regel, geen markdown fences eromheen,
> alle paden tussen quotes (spaties!). Stop bij elke vraag/error en
> rapporteer wat je ziet.

## Stap 0 — Vóór je iets bouwt

Controleer dat de dev-server lokaal nog werkt met de nieuwe code:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
./start.sh

Open in een browser: http://127.0.0.1:5555

Check minstens:

1. Login werkt
2. Sidebar toont "Workstation of: [jouw naam]" (niet je email)
3. Drop-a-set knop heeft een rustige sound-wave halo animatie
4. Cloud sync card in sidebar heeft een "Pro" badge (als je op een Free account zit)
5. Settings → Profile sectie is zichtbaar en de Save-knop werkt
6. Upload een korte testset → check dat de laadtekst nu "Reading your live DJ set..." / "Listening for the drops..." toont (geen meer "FFmpeg · VideoToolbox")
7. Open een clip in de editor → klik Track → Auto-track → na "Generated X keyframes" moet je een toast "Re-rendering clip with tracking applied…" zien en daarna "Tracked crop applied. Your clip now follows the DJ." De preview moet meebewegen.

Als één van deze faalt, stop en meld het.

## Stap 1 — Edge function deployen (BETA-BLOCKER FIX)

Dit moet als eerst gebeuren want anders kan de gebundelde .app niet uploaden.

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
supabase functions deploy update-usage

Verwacht: "Deployed Function update-usage". Geen `--no-verify-jwt` flag —
JWT-verificatie moet aanstaan.

Controleer ook dat de Supabase project nog de bestaande secret heeft:

supabase secrets list

`SUPABASE_SERVICE_ROLE_KEY` moet in de lijst staan. Die is nodig binnen
de edge function. Zo niet, draai:

supabase secrets set SUPABASE_SERVICE_ROLE_KEY=eyJ... (jouw key)

## Stap 2 — Supabase RLS-policy voor profile updates

Voor de nieuwe `/api/profile` endpoint moet er een RLS-policy bestaan
die users hun eigen `profiles`-rij laat updaten. Controleer in Supabase
dashboard → Authentication → Policies → tabel `profiles`:

Een policy met operatie `UPDATE` en USING/WITH CHECK = `auth.uid() = id`
moet aanwezig zijn. Als die er niet is, voeg toe via SQL Editor:

create policy "Users update own profile"
on public.profiles for update
using ( auth.uid() = id )
with check ( auth.uid() = id );

Anders krijgen mensen in de bundle een 401 bij Save in Settings → Profile.

## Stap 3 — .dmg bouwen

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
./build_macos.sh dmg

Duurt 3-8 minuten. De nieuwe secret-scan in stap 3 van het script faalt
de build als er een `.env` of service_role file in de bundle staat (er
hoort er geen te zijn). Als dat alarm afgaat: stop, vraag mij.

Output:

dist/Clip Live.app
dist/Clip Live.dmg

## Stap 4 — Smoketest in de gebundelde .app

xattr -dr com.apple.quarantine "/Applications/Clip Live.app"

(De-quarantine alleen nodig als je de .app eerst naar /Applications hebt
gesleept vanuit de .dmg. Voor rechtstreeks testen kan dat ook vanuit
dist/.)

open "dist/Clip Live.app"

Verwacht: browser opent op http://127.0.0.1:5555.

Test in volgorde:

1. Login werkt
2. Sidebar toont "Workstation of: [jouw naam]"
3. Settings → Diagnostics → Download logs ZIP werkt (uit Sessie 29)
4. Settings → Profile → wijzig je naam → Save → sidebar update direct
5. Upload een korte testset (kleine MP4, <100 MB)
6. **DIT IS DE KRITIEKE TEST:** de upload mag niet meer crashen met
   "supabase_admin niet geconfigureerd". Quota moet van 0/2 naar 1/2 gaan.
7. Open een clip in de editor → Auto-track → preview en export moeten
   meebewegen met de DJ
8. Probeer de Cloud sync card in de sidebar — moet upgrade-modal openen
   (je test-account is Free)

Als één van deze faalt: stop, kopieer de exacte foutmelding, vraag mij.

## Stap 5 — Optioneel: legacy job cleanup uitvoeren

Uit Sessie 29 staat er nog een cleanup-script klaar voor 18 owner-less
job folders:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
python3 scripts/cleanup_legacy_jobs.py

Dat is dry-run. Lijst eruit checken. Daarna echt opruimen:

python3 scripts/cleanup_legacy_jobs.py --apply

## Rollback

Als iets fundamenteel niet werkt, ga terug naar pre-sessie30:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
cp app.py.pre-sessie30.bak app.py
cp auth.py.pre-sessie30.bak auth.py
cp static/index.html.pre-sessie30.bak static/index.html

(De edge function `update-usage` kun je laten staan, die breekt niets als
hij niet aangeroepen wordt.)
