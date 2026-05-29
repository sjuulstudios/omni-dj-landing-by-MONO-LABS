# Omni DJ — LESSONS LEARNED

> **Wat is dit:** patroon-bibliotheek met terugkerende bugs, werkmanieren die werken, en vaakgestelde vragen + canonieke antwoorden. Bedoeld voor snelle raadpleging vóór je iets aanraakt dat eerder is uitgezocht.
>
> **Wanneer raadplegen:**
> - Vóór je aan een bug werkt: scan sectie 1 — staat 'ie er al? Dan zijn er diagnose-stappen of een eerdere fix
> - Vóór je een nieuwe feature bouwt of test draait: scan sectie 2 voor de standaard werkmanier
> - Bij twijfel hoe iets werkt of waar iets staat: scan sectie 3
>
> Aangemaakt: 2026-05-26, op basis van scan van HANDOVER.md (sessies 1–39).

---

## 1. Terugkerende bugs (anti-patronen)

### 🔴 Duplicate clips bug

- **Symptoom:** clips tonen identieke video i.p.v. unieke drops
- **Status:** **terugkerend** — staat al in CLAUDE.md als waarschuwing
- **Hoe vaak gezien:** meermaals, zeker tot sessie 24. NIET gereproduceerd in sessie 24 (Lisa Korver 26 clips + Franky Rizardo 151 clips allemaal unieke start/end/peak)
- **Waar te kijken:** `cutter.py` rond `process_clips`. Bij twijfel: check of clip-start tijden uniek zijn vóór ffmpeg-call
- **Regel:** check eerst of het probleem nog bestaat vóór je gaat fixen — het is in sessie 24 mogelijk al opgelost

### 🔴 .app build vs dev-server gedrag verschilt (ffmpeg-paden)

- **Symptoom:** in `./start.sh` werkt alles, in de gebundelde `.app` faalt iets stilletjes (clips renderen niet, processen hangen)
- **Status:** **actief open bug** sessie 39 — clips renderen niet in .app
- **Oorzaak-patroon:** ffmpeg-pad klopt niet vanuit de `.app` bundle, OF schrijfrechten op `~/Library/Application Support/Omni DJ/`
- **Diagnose-recept:**
  1. `"/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter/dist/Omni DJ.app/Contents/Resources/bin/ffmpeg" -version`
  2. `find ~/Library/Application\ Support/Clip\ Live/ -name "*.log" -o -name "*.json" 2>/dev/null | head -10`
  3. App via terminal draaien: `"/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter/dist/Omni DJ.app/Contents/MacOS/Omni DJ" 2>&1 | grep -i "error\|fail\|ffmpeg"`
- **Regel:** elke bug die alleen in de .app voorkomt → eerst ffmpeg-pad + schrijfrechten checken
- **Bonus-historie:** in sessie 27 was `webbrowser.open` ook al een .app-only bug — werd vervangen door `subprocess.run(['open', url])`. Patroon: macOS bundling breekt subtiele cross-platform-gewoontes

### 🔴 Cache-buster URL bouwt dubbele `?` (sessie 32e — "de killer")

- **Symptoom:** "Clip file not yet rendered" overlay na recut, terwijl ffmpeg de file ECHT heeft geschreven
- **Oorzaak:** `?v=<timestamp>` werd naïef APPENDED ná `withAuth()`. Maar `withAuth()` voegt altijd `?token=<JWT>` toe → finale URL = `/api/clip/x/y.mp4?token=xxx?v=123` → backend parseert `token = "xxx?v=123"` → `_require_job_access(..., allow_query_token=True)` faalt → 403
- **Fix:** `const joiner = newSrc.indexOf('?') >= 0 ? '&' : '?'; newSrc += joiner + 'v=' + ts;`
- **Regel:** bij elke URL-mutatie die query-strings appendt — eerst checken of `?` al bestaat. Geldt voor cache-busters, tracking-params, alles. Ook in retry-onerror handlers

### 🔴 Large-file pipeline hang

- **Symptoom:** bij grote audiobestanden (>4 GB / >2u) loopt de pipeline soms vast
- **Status:** in sessie 24 NIET gereproduceerd (Franky Rizardo 7.8 GB door volledige pipeline). Mogelijk verholpen door LARGE_FILE_PIPELINE auto-trigger (>7200s threshold) uit sessie 22
- **Regel:** test met Franky Rizardo set (7.8 GB, 3:54u) vóór je claimt dat large-file werkt

### Browser-tab race condition / file picker 2 clicks

- **Symptoom:** file picker opent na 2 clicks i.p.v. 1, of meerdere browsertabs spawnen
- **Oorzaak:** pywebview race condition met file picker
- **Fix (sessie 37/38):** `openFilePicker()` helper met 120ms `setTimeout`. Plus `multiprocessing.freeze_support()` ALLEREERST in `launcher.py` (vóór alle andere imports)
- **Regel:** PyInstaller-bundle race conditions altijd via `multiprocessing.freeze_support()` als eerste

### 1:1 aspect ratio render bug (gemeld 2026-05-10)

- **Symptoom:** klik op "1:1" in aspect-rail → toast "Could not render 1:1: ffmpeg failed"
- **Status:** **mogelijk nog open** — gemeld sessie 16, fix in sessie 18 (zie `_build_oneone_segment` in cutter.py — escape komma's binnen `min()` met `\,`)
- **Regel:** ffmpeg filter-chain bugs zijn altijd source-aspect-afhankelijk. Test op zowel landscape (1920×1080) als vertical (1080×1920) sources

### Stretch-bug (sessies 32–32d, meerdere iteraties)

- **Symptoom:** "split_at must be > 0.5 s from each end" toast bij stretch
- **Oorzaak-patroon:** `editorTrimAtPlayhead` had 5 branches met inconsistente drempels (0.4 / 0.55 / 0.05) + gebruikte `dur = v.duration || clip.duration` — twee verschillende waardes. Browser-decoded `v.duration` kan ~0.1s afwijken door codec-rounding
- **Echte fix (sessie 32d):** `hasBand = (Math.abs(t.inSec) > 0.05) || (Math.abs(t.outSec - dur) > 0.05)` — vangt ook pure-stretch (beide handles naar buiten). Single source of truth = `clip.duration`. `if (hasBand) → /api/recut` else `→ /api/split-clip`
- **Regel:** als je drempels vergelijkt tussen frontend en backend — synchroniseer ze in beide. Browser-decoded duration ≠ analyzer duration

### Email Confirmation blokt signups in test

- **Symptoom:** `.test` en `.example` TLDs worden door Supabase geweigerd. Free plan rate-limit: 2 signups/uur per email-domein
- **Workaround:** Email Confirmation UIT in Supabase dashboard → Auth → Sign In/Up
- **🟡 BELANGRIJK voor v1.0:** weer aanzetten zodra eigen SMTP (SendGrid/Postmark/Resend) is gekoppeld. NIET vergeten vóór paid launch
- **Regel:** voor test-accounts altijd echte TLDs gebruiken (`.com`, `.nl`), niet `.test`

### Hardcoded `omnidj.com` in landing

- **Symptoom:** `landing/index.html` heeft `https://omnidj.com/` HARDCODED op meerdere plekken (canonical URL, og:image, og:url)
- **Status:** nog niet gefixt — wacht op DNS-cutover
- **Regel:** search-and-replace naar `https://omnidj.com/` doen pas wanneer DNS gekoppeld is, anders breken og-images en Google-indexering tijdens transitie. In één commit met de cutover

---

## 2. Werkmanieren die werken

### End-to-end test op verse upload uit testset-folder

- **Wanneer:** na elke wijziging in pipeline (analyzer / cutter / tracking / export)
- **Hoe:** kies een set uit `dj-clip-cutter/CLIP DROP DJ-SETS/`:
  - **Lisa Korver x Hör Berlin** (424 MB, 55 min) — snelle smoketest, 30 clips
  - **Franky Rizardo Peru Set** (7.8 GB, 3:54u, 151 cues) — grote-set stress-test
  - **Ediine x Hör Berlin** — alternatief
  - **Don Diablo Live Set**
  - **Housy Good vibes set 30min** — minimale test
- **Wat checken:** analyzer (BPM, key, cue-count), cutting (alle clips gerenderd?), editor (trim/stretch/playhead/ratio-switch), export (alle 4 codec-varianten)
- **Waarom:** vangt 90% van de regressies vroeg

### Backup vóór risky changes

- **Patroon:** `bestand.pre-sessieNN.bak` of `bestand.pre-<feature>.bak`
- **Voorbeelden:** `app.py.pre-sessie31.bak`, `static/index.html.pre-sessie32d.bak`, `analyzer.py.pre-sessie24.bak`
- **Wanneer:** vóór elke wijziging in `app.py`, `cutter.py`, `analyzer.py`, of grote stukken `static/index.html`
- **Bonus:** alle .bak files worden door `build_macos.sh` defensief gestript uit de bundle (sessie 27), dus ze schaden niet

### Frontend-only changes = hard-refresh

- **Patroon:** als je alleen `static/index.html` aanraakt → geen server-restart nodig, alleen ⌘+Shift+R in browser
- **Wanneer wel restart:** als je `app.py`, `cutter.py`, `analyzer.py`, `auth.py`, `billing.py` aanraakt
- **Wanneer wel rebuild (.app):** ALTIJD na elke code-change — PyInstaller bakt `index.html` in de bundle, dev-server serveert altijd de oude versie

### Verificatie-recept vóór "klaar" zeggen

- `python3 -m py_compile app.py auth.py cutter.py billing.py analyzer.py` → moet OK zijn
- `node --check` op extracted inline JS-blok uit `static/index.html` → moet OK zijn
- Bracket-balans check `{}/[]/()` in HTML — vóór en na identiek
- `<button>` count vóór en na: identiek tenzij je expres UI hebt verwijderd

### Diagnose → voorstel → wacht op "ja" → uitvoeren

- Sjuul is niet-technisch op dev-niveau — altijd uitleggen wat een commando doet
- Nooit meerdere stappen tegelijk geven
- Eén commando per regel, paden gequote
- Geen markdown fences rond shell-commando's (Sjuul kopieert direct)

### Commit-na-elke-fix met betekenisvolle messages

- Patroon: `fix: <wat>`, `feat: <wat>`, `refactor: <wat>`
- Voorbeelden uit sessie 39: `fix: editor drawers — positioning, overlap en contrast`, `feat: native file picker voor DJ sets — geen 4GB limiet meer`

### Plan-documenten vóór grote refactors

- **Wanneer:** bij refactors >100 regels code of met race-condition risico's
- **Patroon:** `SESSIENN-<FEATURE>-PLAN.md` in project root
- **Voorbeelden:** `SESSIE33-RECUT-QUEUE-PLAN.md`, `SESSIE34-PASSWORD-RESET-PLAN.md`, `SESSIE34-CAPTION-FONTS-PLAN.md`
- **Inhoud:** architectuur, edge cases, beslispunten voor Sjuul, schatting in uren
- **Waarom:** Sjuul kan reviewen zonder dat ik direct begin te bouwen

### Runbooks voor handmatige Sjuul-stappen

- **Patroon:** `SESSIENN-REBUILD-RUNBOOK.md` of `<FEATURE>-RUNBOOK.md`
- **Voorbeelden:** `SESSIE30-REBUILD-RUNBOOK.md`, `SESSIE31-REBUILD-RUNBOOK.md`, `STRIPE-DNS-RUNBOOK.md`
- **Wanneer maken:** als er meer dan 2 stappen zijn die Sjuul handmatig moet doen (deploy, rebuild, smoketest)

---

## 3. Vaakgestelde vragen + canonieke antwoorden

### "Hoe start ik de app?"

Dev-server: `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter" && ./start.sh` → browser naar http://127.0.0.1:5555

`.app` bundle: dubbelklik `dist/Omni DJ.app`, of via terminal voor debug-output: `"/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter/dist/Omni DJ.app/Contents/MacOS/Omni DJ"`

### "Werkt deze fix ook in de .app build?"

**Belangrijke onderscheid:** dev-server (`./start.sh`) en gebundelde `.app` gedragen zich anders:

- **ffmpeg-pad:** dev-server gebruikt systeem-ffmpeg (Homebrew of PATH), `.app` gebruikt `Contents/Resources/bin/ffmpeg`
- **Werk-paden:** dev-server schrijft naar `dj-clip-cutter/output/`, `.app` schrijft naar `~/Library/Application Support/Omni DJ/`
- **Browser-open:** dev-server gebruikt `webbrowser.open()`, `.app` MOET `subprocess.run(['open', url])` (sessie 27 fix)
- **Schrijfrechten:** `.app` kan schrijfrechten-issues hebben in App Support folder
- **Frontend serving:** PyInstaller bakt `index.html` in de bundle → na elke frontend-change MOET je rebuilden
- **Regel:** test elke wijziging in beide modi voordat je "klaar" zegt

### "Waar staan de backups?"

- Per-sessie backups: `dj-clip-cutter/*.pre-sessieNN.bak` of `static/index.html.pre-sessieNN.bak`
- Handover origineel (2026-05-26): `HANDOVER.md.backup-2026-05-26` + `.backups/HANDOVER-pre-compact-2026-05-26.md`
- .bak archief (sessie 27): `_bak-archive-2026-05-17.tar.gz` (64 oude .bak files opgeruimd)

### "Welke testsets kan ik gebruiken?"

Allemaal in `dj-clip-cutter/CLIP DROP DJ-SETS/`:

- Lisa Korver x Hör Berlin (424 MB, 55 min, 30 clips) — snelle smoketest
- Franky Rizardo Peru Set (7.8 GB, 3:54u, 151 cues) — large-file stress
- Ediine x Hör Berlin
- Don Diablo Live Set
- Housy Good vibes set 30min

Reeds verwerkte jobs op disk (sessie 24, voor regressie-vergelijking):
- `ac7373ae` — Lisa pre-fix, 26 clips, 72 BPM stamp
- `94d6c9c7` — Franky Rizardo, 151 proxy clips, 129 BPM, subject_signature locked uit clip 1
- `00abd848` — Lisa post-fix, 30 clips, 144 BPM stamp
- `46716f96` + `3a4eb44d` — oude Ediine sets

### "Hoe deploy ik een edge function?"

```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"
supabase functions deploy <function-name>
```

Edge functions die bestaan: `create-checkout-session`, `create-portal-session`, `update-usage`, Stripe-webhook (laatste MET `--no-verify-jwt`, andere ZONDER).

### "Hoe weet ik welke sessie het laatst is?"

Bovenaan `HANDOVER.md` staat `Laatste update:` met datum + sessienummer. Het STATUS-blok daaronder is de meest recente sessie. Sessies 1–26 staan in `HANDOVER-ARCHIVE.md`.

### "Waar staan de plan-documenten?"

Project root (naast `HANDOVER.md`):

- `SESSIE30-REBUILD-RUNBOOK.md` — edge function deploy + rebuild + retest
- `SESSIE31-REBUILD-RUNBOOK.md` — dmg-stappen
- `SESSIE33-RECUT-QUEUE-PLAN.md` — background recut-queue refactor
- `SESSIE34-PASSWORD-RESET-PLAN.md` — security-critical, vóór beta-launch
- `SESSIE34-CAPTION-FONTS-PLAN.md` — feature
- `STRIPE-DNS-RUNBOOK.md` — Stripe live mode + DNS

### "Wat is uit scope?"

Definitief uit scope (NIET meer voorstellen, zie sessie 33):

- Beta-onboarding-flyer
- Beta-uitnodigingsmail
- Legacy job cleanup (al opgeruimd, 0 kandidaten)

### "Hoe gaat email werken?"

Beslissing sessie 36: **Google Workspace ($6/mo)** voor omnidj.com. Superieure deliverability tov TransIP/iCloud. Eerst Google Workspace opzetten → krijg MX/SPF/DKIM-waarden → invullen in Cloudflare DNS.

### "Welke werkmappen zijn er?"

- **Hoofd-app + alles privé:** `~/Documents/Claude/Projects/Omni DJ/` (git met baseline + ongepushte changes)
- **Landing publiek deploy:** `~/Documents/Claude/Projects/clipdrop-landing-deploy/` (eigen git, gekoppeld aan GitHub `sjuulstudios/omnidj.com-by-MONO-LABS`)
- **Originele landing in Omni DJ:** `~/Documents/Claude/Projects/Omni DJ/landing/` (de SOURCE of truth — als je hier iets wijzigt, óók in clipdrop-landing-deploy zetten en pushen)

---

## Hoe dit bestand bijhouden

- Bij elke nieuwe terugkerende bug: voeg toe aan sectie 1 met symptoom + oorzaak-patroon + fix-recept + regel
- Bij elke werkmanier die zich bewijst: voeg toe aan sectie 2 met wanneer-te-gebruiken
- Bij elke vraag die Sjuul vaker stelt: voeg toe aan sectie 3 met canoniek antwoord
- Linken vanuit HANDOVER.md zodra een nieuw patroon zich vormt
