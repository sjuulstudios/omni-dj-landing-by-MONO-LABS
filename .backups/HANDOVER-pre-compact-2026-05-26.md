# Clip Live — HANDOVER

> **Lees dit altijd als eerste.** Update dit bestand na elke significante stap.
> Laatste update: 2026-05-25 sessie 39 — Native file picker geïmplementeerd, editor drawer fixes, .app rebuild. Open bug: clips renderen niet in .app build.

---

> **STATUS NA SESSIE 39 (2026-05-25, avond):**
>
> **Wat gedaan deze sessie:**
>
> 1. **Native file picker geïmplementeerd (commits `0ef2232` + `7ab31e5`)**
>    - `app.py`: `/api/pick-file` endpoint toegevoegd met `_pick_file_macos()` (AppleScript) + `_pick_file_tk()` (Windows/Linux fallback)
>    - `static/index.html`: `openFilePicker()` vervangen — roept nu `/api/pick-file` aan → geeft absoluut pad terug → stuur direct naar `/api/upload-local`. Geen browser-limiet meer. Werkt voor elke bestandsgrootte incl. Franky Rizardo 7.8 GB.
>    - `_startLocalJob(path)` helper toegevoegd, `submitLocalPath()` gebruikt die nu ook
>    - 4 GB check + `LARGE_FILE_THRESHOLD_BYTES` constante verwijderd
>
> 2. **Editor drawer fixes (commit `7ab31e5`)**
>    - `.ed-body` krijgt `position: relative` zodat absolute kinderen correct verankerd zijn
>    - `.ed-text-drawer` `top: 0` → `top: 62px` zodat ed-top toolbar niet bedekt wordt
>    - Sluitende `</div>` van `.editor` verplaatst naar ná beide `<aside>` drawers (waren siblings, moeten kinderen zijn)
>    - `--ink-0` t/m `--ink-4` overschreven in `.ed-text-drawer`: drawer is donker, tekst moet licht zijn
>
> 3. **Timeline editor smoketest — Franky Rizardo set (151 cues, 7.8 GB)**
>    - Export panel: 5 presets (TikTok, Instagram Reel, YouTube Shorts, Facebook, RAW), goede contrast ✅
>    - Trim handles: drag-in en drag-out functioneel, STATE.trim wordt bijgewerkt, localStorage-persistentie werkt ✅
>    - Timeline scrubbing: muisklik op `.tracks` zoekt video correct, playhead volgt ✅
>    - Ratio switching: 6 buttons, geen errors ✅
>    - JS errors: nul fouten ✅
>
> 4. **`.app` rebuild gedaan** — `build_macos.sh` succesvol afgerond, `dist/Clip Live.app` is bijgewerkt
>
> **🔴 OPEN BUG — clips renderen niet in `.app` build:**
>    - Symptoom: na analyse verschijnt "No rendered file for this cue yet" in editor. Cues worden correct gedetecteerd, maar de cutting-stap (ffmpeg clips aanmaken) mislukt stilletjes.
>    - Waarschijnlijke oorzaak: ffmpeg-pad klopt niet vanuit de `.app` bundle, OF de output-map (`~/Library/Application Support/Clip Live/`) heeft een schrijfrechten-probleem.
>    - **Diagnose-stappen voor volgende sessie:**
>      1. Check: `"/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter/dist/Clip Live.app/Contents/Resources/bin/ffmpeg" -version`
>      2. Check: `find ~/Library/Application\ Support/Clip\ Live/ -name "*.log" -o -name "*.json" 2>/dev/null | head -10`
>      3. Draai de app via terminal i.p.v. dubbelklik: `"/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter/dist/Clip Live.app/Contents/MacOS/Clip Live" 2>&1 | grep -i "error\|fail\|ffmpeg"` — zo zie je de crash output direct
>    - In de dev-server (`./start.sh`) werkt alles wél — daar hebben clips gewoon een path en worden correct gesneden. Alleen de gebundelde `.app` heeft dit probleem.
>    - Analyse duurde ook te lang (minuten voor 27-min set) — mogelijk gerelateerd aan hetzelfde ffmpeg-pad probleem waarbij processen hangen.
>
> **Git log na sessie 39:**
> - `7ab31e5` — fix: editor drawers — positioning, overlap en contrast
> - `0ef2232` — feat: native file picker voor DJ sets — geen 4GB limiet meer
> - `b000a57` — baseline
>
> **Openstaand voor volgende sessie — in prioriteitsvolgorde:**
>
> 1. **🔴 Fix: clips renderen niet in .app** — diagnose met terminal-stap 3 hierboven, dan ffmpeg-path fix in `launcher.py` of `cutter.py`
> 2. **Fase 5 — Stripe live mode** (pas uitvoeren als .app werkt + landing op djclips.nl draait). Runbook: `STRIPE-DNS-RUNBOOK.md`
> 3. **Fase 3 — djclips.nl koppelen** via Cloudflare (nameservers TransIP → Cloudflare, DNS records, Pages custom domain)
> 4. **Password-reset bouwen** — `SESSIE34-PASSWORD-RESET-PLAN.md` (security-critical vóór beta-launch)
> 5. **Caption-fonts library** — `SESSIE34-CAPTION-FONTS-PLAN.md` (feature, niet kritiek)

---

> **STATUS NA SESSIE 36 — INFRASTRUCTUUR (2026-05-24, late middag, Sjuul actief):**
>
> **Wat afgerond deze sessie — externe diensten gekoppeld, geen code-changes in dj-clip-cutter:**
>
> 1. **Aparte landing-werkmap aangemaakt buiten Clip Live git-repo:**
>    Pad: `~/Documents/Claude/Projects/clipdrop-landing-deploy/`
>    Bevat een **kopie** van de bestanden uit `Clip Live/landing/.` als losse repo. Reden: publieke landing-code mag niet vermengd zijn met privé app-code in de hoofdrepo.
>    Werkflow voortaan: wijziging maken in déze deploy-map → `git add . && git commit -m "..." && git push` → Cloudflare deployt automatisch binnen 1 min.
>
> 2. **GitHub repo aangemaakt + initial push:**
>    URL: https://github.com/sjuulstudios/djclips.nl-by-MONO-LABS
>    Public repo, branch `main`. Commit `d98cf78 — Initial landing page commit`. 13 bestanden (`index.html`, `contact.html`, `privacy.html`, `terms.html`, `styles.css`, `script.js`, `vercel.json`, `og-image.svg`, `favicon.svg`, `robots.txt`, `sitemap.xml`, `README.md`, `.gitignore`).
>    Authentication via `gh` CLI (`brew install gh` + `gh auth login` via browser). Sjuul kan voortaan gewoon `git push` zonder password/token-gedoe.
>    NB: een paar minuten lang heeft Sjuul z'n GitHub-wachtwoord per ongeluk in de terminal getypt bij de classic-auth prompt — niet erg, GitHub accepteert geen passwords meer via git, het is afgewezen. Geen leak, geen actie nodig.
>
> 3. **Cloudflare Pages project live:**
>    URL: https://djclips-nl-by-mono-labs.pages.dev (geverifieerd werkend via web_fetch — alle 4 secties laden, signup-wizard rendert, footer-links werken).
>    Project name: `djclips-nl-by-mono-labs`. Production branch: `main`. Framework preset: None. Build command: leeg. Build output: root (`/`). Root directory: leeg.
>    GitHub-koppeling actief → auto-deploy bij elke push naar `main`.
>    Een oud `clipdroplive` Pages-project (drag-and-drop versie van 19 dagen geleden, geen Git-koppeling) is **verwijderd** voor schone start.
>
> 4. **Cloudflare-account heeft al sjuulstudios's bestaande `clipdrop.com` domein gekoppeld** — `djclips.nl` (nieuwe domein, net aangevraagd bij TransIP) staat hier NOG NIET aan gekoppeld. Dat is open voor volgende sessie.
>
> 5. **Belangrijke vondst bij landing-content:** `index.html` heeft op meerdere plekken `https://clipdroplive.com/` HARDCODED als canonical URL, og:image, og:url. Dit moet ge-search-replaced worden naar `https://djclips.nl/` zodra de DNS gekoppeld is — anders blijft Google het oude domein indexeren en social shares tonen broken og-images. **Niet vóór DNS-werk fixen** — beter in één commit samen met de domein-cutover.
>
> **Nieuw plan-document opgesteld (security-critical, niet geïmplementeerd):**
> - `SESSIE34-PASSWORD-RESET-PLAN.md` — password reset ontbreekt volledig in `auth.py` (geen forgot/reset endpoint, geen UI). Plan leunt zwaar op Supabase Auth's ingebouwde reset-flow en bouwt daar een rate-limited Flask laag overheen. Dekt 16 OWASP-aanvallen af in een security checklist. 5 fases, ~5.5u totaal. Bevat 4 beslispunten voor Sjuul. **Aanbeveling: bouwen vóór beta-launch.**
>
> **Beslissingen vastgelegd deze sessie (voor volgende sessie te onthouden):**
> - Domein-strategie: nameservers van TransIP wijzen straks naar Cloudflare (alles in 1 dashboard, propagatie 1-24u)
> - Email-host: Google Workspace ($6/mo) — beslist voor superieure deliverability tov TransIP/iCloud
> - Hosting: Cloudflare Pages gekozen (onbeperkte bandwidth, commerciële licentie, gratis DDoS) i.p.v. Vercel (officieel niet voor commercieel op Hobby plan)
>
> **Werkmappen (heel belangrijk voor volgende sessie te onthouden):**
> - Hoofd-app + alles privé: `~/Documents/Claude/Projects/Clip Live/` (git met baseline + ongepushte sessie 21-35 changes)
> - Landing publiek deploy: `~/Documents/Claude/Projects/clipdrop-landing-deploy/` (eigen git, gekoppeld aan GitHub `sjuulstudios/djclips.nl-by-MONO-LABS`)
> - Originele landing in Clip Live: `~/Documents/Claude/Projects/Clip Live/landing/` (de SOURCE of truth — als je hier iets wijzigt, moet je het ook in clipdrop-landing-deploy zetten en pushen. Of inverse: edit clipdrop-landing-deploy en sync naar Clip Live/landing voor backup)
>
> **STATUS NA SESSIE 37/38 — DMG FASE 4 KLAAR (2026-05-25):**
>
> **Wat gedaan deze sessie:**
>
> 1. **Fase 4 volledig afgerond:** venv ✅, flask-limiter ✅, smoketest ✅, migrations 002 (audit_logs) + 003 (RBAC role) deployed ✅, admin role gezet voor business@sjuulstudios.com ✅, edge function update-usage deployed ✅, DMG gebouwd ✅
>
> 2. **Post-build bugfixes (allemaal in index.html + launcher.py + app.py):**
>    - Upload error "supabase_admin niet geconfigureerd" → fixed: `access_token` doorgeven aan `_get_or_refresh_profile()`
>    - File picker 2 clicks nodig → fixed: `openFilePicker()` helper met 120ms `setTimeout` (pywebview race condition)
>    - Set stopt bij 14% / process pool crash → fixed: `multiprocessing.freeze_support()` ALLEREERST in launcher.py vóór alle andere imports
>    - Meerdere browsertabs spawnen → zelfde fix als hierboven
>    - Preview ratio black bars → fixed: `applyEditorStageSize()` set nu ook `object-fit` op de video; `maxHeight:'none'` bij 16:9 en 1:1
>
> 3. **Testsets beschikbaar:** `dj-clip-cutter/CLIP DROP DJ-SETS/` bevat 5 MP4 sets die je altijd kunt gebruiken voor testen en debuggen:
>    - `Don Diablo Live Set.mp4`
>    - `Ediine x Hör Berlin.mp4`
>    - `Franky Rizardo Peru Set.mp4` (eerder verwerkt, job ID `94d6c9c7`, 151 clips in `output/94d6c9c7/`)
>    - `Housy Good vibes set 30min.mp4`
>    - `Lisa Korver x Hör Berlin.mp4`
>    Claude heeft toegang tot deze folder en kan sets direct laden voor testing.
>
> 4. **DMG bouwen:** `bash build_macos.sh dmg` in `dj-clip-cutter/` met actieve venv. Output: `dist/Clip Live.app` + `dist/Clip Live.dmg`.
>    Na elke code-change: herbouwen is verplicht — PyInstaller bakt `index.html` in de bundle, dev server serveert altijd de oude versie.
>
> **Openstaand voor volgende sessie — in deze volgorde:**
>
> 1. **🔍 Smoketest op de gebouwde .app afronden** (Sjuul test ratio-knoppen, tekstcontrast, snelle clip-switches in editor)
>    Draai de `.app` via: `"dist/Clip Live.app/Contents/MacOS/Clip Live"` (niet via `open` — dat geeft soms race conditions)
>    Test: login → set laden uit CLIP DROP DJ-SETS → clips zien → editor openen → ratio 9:16/16:9/1:1/4:5 wisselen → check geen bars
>
> 2. **Fase 5 — Stripe live mode (Sjuul, ~30 min)**
>    Pas uitvoeren als dmg werkt EN landing op djclips.nl draait. Runbook: `STRIPE-DNS-RUNBOOK.md`.
>    Anders: webhook-callbacks van Stripe gaan naar het verkeerde domein.
>
> 3. **Fase 3 — djclips.nl koppelen via Cloudflare (Sjuul + Claude samen, ~45 min + 1-24u DNS-wacht)**
>    Eerst Google Workspace opzetten voor djclips.nl → krijg MX/SPF/DKIM-waarden van Google.
>    Dan in Cloudflare: domein toevoegen (Add a site → djclips.nl) → krijg 2 Cloudflare nameservers.
>    Dan in TransIP: nameservers vervangen door de 2 Cloudflare nameservers.
>    Dan in Cloudflare DNS: alle records invullen (Google MX-records + CNAME naar Pages).
>    Dan in Cloudflare Pages: djclips.nl als custom domain toevoegen.
>    Dan: search-and-replace `clipdroplive.com` → `djclips.nl` in `index.html`, commit, push.
>    Verifieer: `https://djclips.nl` laadt de landing, `business@djclips.nl` ontvangt mails.
>
> 4. **Sjuul beslist over de 4 beslispunten in `SESSIE34-PASSWORD-RESET-PLAN.md`** — kritiek vóór beta-launch.
>
> 5. **Sjuul beslist over de 4 beslispunten in `SESSIE34-CAPTION-FONTS-PLAN.md`** — feature, niet kritiek.
>
> 6. **Background recut-queue (`SESSIE33-RECUT-QUEUE-PLAN.md`)** — als er tijd is, anders na launch.
>
> **Niet aangeraakt deze sessie:** alle `.py` files in `dj-clip-cutter/`, alle frontend files, alle Supabase edge functions. Puur infrastructuur-werk.
>
> **Belangrijke pointer voor volgende sessie:** lees dit blok + `SESSIE34-PASSWORD-RESET-PLAN.md` (security-critical) + `SESSIE31-REBUILD-RUNBOOK.md` (dmg-stappen) voordat je iets doet. De landing-URL kun je live verifiëren via web_fetch op `https://djclips-nl-by-mono-labs.pages.dev/`.

---

> **STATUS NA SESSIE 35 — AUTONOOM (Sjuul boodschappen, 2026-05-24):**
>
> Security Foundation volledig geïmplementeerd. Alle drie onderdelen klaar.
>
> **Wat er gebouwd is:**
>
> **1. Audit log (volledig)**
> - Nieuwe Supabase-migratie: `supabase/migrations/002_audit_logs.sql`
>   - Tabel `audit_logs` met: `id`, `user_id`, `action`, `ip_address`, `user_agent`, `metadata` (jsonb), `created_at`
>   - RLS aan: users zien alleen eigen logs, service_role schrijft
>   - Twee indexes: op `(user_id, created_at desc)` en `(action, created_at desc)`
> - `log_action()` helper in `auth.py` — fire-and-forget, nooit blocking
> - `_audit()` convenience wrapper in `app.py` — plukt ip + user-agent automatisch uit request
> - Audit-aanroepen op 7 endpoints:
>   - `auth.signup` — bij elke registratie (geslaagd of niet)
>   - `auth.login` / `auth.login_failed` — geslaagde én mislukte logins
>   - `plan.checkout_started` — bij start van Stripe checkout
>   - `plan.portal_opened` — bij openen Stripe portal
>   - `clip.export_started` — bij start van export-render
>   - `file.upload` — bij upload van een nieuw bestand
>   - `debug.logs_downloaded` — bij download van debug-ZIP
>
> **2. Data-isolatie review (volledig)**
> Alle Supabase-queries in `app.py` en `auth.py` gecontroleerd. Bevindingen:
> - **6 queries via `supabase_admin`** (service_role) — allemaal voorzien van `.eq('id', user_id)` of `.eq('id', user.id)`. Geen enkele query haalt data van meerdere users tegelijk op. ✅
> - **3 queries via `supabase_client`** (anon-key) — lopen via RLS, dus automatisch beperkt tot de ingelogde user. ✅
> - **`audit_logs` INSERT** — via service_role, maar bevat altijd `user_id` in de rij zelf. ✅
> - **Geen queries buiten `app.py` en `auth.py`** — `billing.py`, `cutter.py`, `analyzer.py` raken Supabase niet. ✅
> - **Conclusie:** data-isolatie is correct op zowel database-niveau (RLS) als code-niveau (expliciete user_id filter op elke admin-query).
>
> **3. RBAC (volledig)**
> - Nieuwe Supabase-migratie: `supabase/migrations/003_rbac_role_column.sql`
>   - `role` kolom op `profiles` (text, default `'user'`, not null)
>   - Check constraint: alleen `'user'` / `'beta'` / `'admin'` toegestaan
>   - UPDATE RLS-policy uitgebreid: users kunnen eigen `role` niet verhogen
> - `get_user_role(user_id)` helper in `auth.py`
> - `require_role(role)` Flask decorator in `auth.py` — hiërarchisch: user < beta < admin
> - `/api/debug/logs` endpoint nu beveiligd met `@require_role('admin')`
>
> **Syntax-check:** `python3 -m py_compile app.py auth.py` → OK ✅
>
> **WAT SJUUL HANDMATIG MOET DOEN (vereist voor activering):**
> 1. **Migraties deployen** — twee nieuwe SQL-files in de Supabase SQL Editor plakken en runnen:
>    - `supabase/migrations/002_audit_logs.sql` (audit log tabel)
>    - `supabase/migrations/003_rbac_role_column.sql` (role kolom)
> 2. **Jezelf admin maken** — na 003 uitvoeren, run in SQL Editor:
>    `update public.profiles set role = 'admin' where id = (select id from auth.users where email = 'business@sjuulstudios.com');`
> 3. **Dev-server herstarten** — zodat `app.py` en `auth.py` herladen worden (de code-changes zijn al live in de files)
>
> **Gewijzigde files sessie 35:**
> - `dj-clip-cutter/auth.py` — `get_user_role()`, `require_role()`, `log_action()` toegevoegd
> - `dj-clip-cutter/app.py` — `_audit()` helper, 7 audit-aanroepen, `@require_role('admin')` op debug endpoint
> - `dj-clip-cutter/supabase/migrations/002_audit_logs.sql` — nieuw
> - `dj-clip-cutter/supabase/migrations/003_rbac_role_column.sql` — nieuw
> - `HANDOVER.md` — sessie 35 sectie toegevoegd
>
> **Niet aangeraakt sessie 35:** `static/index.html`, `billing.py`, `cutter.py`, `analyzer.py`, edge functions, landing.
>
> **Openstaand voor sessie 36:**
> 1. **Sjuul handmatig:** migraties 002 + 003 deployen + zichzelf admin maken (zie boven)
> 2. **Sjuul handmatig (carry-over):** dev-server herstarten, `./build_macos.sh dmg`, `supabase functions deploy update-usage`
> 3. DNS koppelen djclips.nl → Cloudflare Pages (carry-over sessie 34)
> 4. Password-reset bouwen (carry-over sessie 34 — `SESSIE34-PASSWORD-RESET-PLAN.md`)
> 5. Caption-fonts library (carry-over sessie 34 — `SESSIE34-CAPTION-FONTS-PLAN.md`)

---

> **SECURITY FOUNDATION PLAN — sessie 35 of later (opgesteld 2026-05-24):**
>
> Aanleiding: enterprise/zakelijke klanten (labels, studio's, mediabedrijven) stellen altijd drie vragen die een deal kunnen blokkeren. Nu de basis-security (rate limiting, RLS) staat, is dit het goede moment om deze drie architectuurlagen toe te voegen — vóór het te complex wordt.
>
> **Onderdeel 1 — Audit log** *(hoogste prioriteit)*
> Wat: elke significante actie (login, logout, upload, clip-aanmaken, export, plan-upgrade, wachtwoord-reset) vastleggen in een aparte Supabase-tabel `audit_logs` met: `user_id`, `action`, `ip_address`, `user_agent`, `timestamp`, `metadata` (JSON).
> Waarom: dit is een SOC 2-vereiste en een enterprise deal-breaker als het ontbreekt. Intern ook nuttig voor debugging en support.
> Aanpak: nieuwe Supabase-tabel + migratie, kleine `log_action()` helper in `auth.py`, aanroepen op de ~8 kritieke endpoints in `app.py`. RLS: users zien alleen hun eigen logs, service_role ziet alles.
> Schatting: ~2 uur. Klein risico — puur additief, raakt geen bestaande logica.
>
> **Onderdeel 2 — Data-isolatie hardening** *(laag risico, al deels aanwezig)*
> Wat: controleren en documenteren dat elke database-query gefilterd is op `user_id`. De RLS-policies (sessie 32) dekken dit al op databaseniveau — dit is een code-review + bevestiging, geen grote bouw.
> Aanpak: alle `app.py`-queries langs lopen, checken of ze ook via de authenticated client lopen (niet service_role tenzij nodig). Resultaat: een korte checklist in HANDOVER.md die bevestigt dat isolatie gewaarborgd is.
> Schatting: ~30–45 min. Geen code-schrijven, alleen review.
>
> **Onderdeel 3 — Basis RBAC (role-based access)** *(later, wanneer nodig)*
> Wat: een `role` kolom op de `profiles`-tabel (`user` / `admin` / `beta`). Admin-endpoints (`/api/debug/logs`, toekomstige admin-panelen) afsluiten op basis van die rol.
> Waarom: nu heb je geen manier om Sjuul zelf meer rechten te geven dan een gewone gebruiker. Ook nodig als je ooit team-accounts aanbiedt.
> Aanpak: migratie + `require_role('admin')` decorator in `auth.py` + één admin-endpoint ermee beschermen als proof-of-concept.
> Schatting: ~1.5–2 uur. Matig risico — raakt `auth.py` + één endpoint.
>
> **Volgorde aanbeveling:** Audit log → Data-isolatie review → RBAC (apart plan schrijven als de tijd komt).
> **Niet nu bouwen:** team-accounts, per-team data-scope, externe audit-exports. Dat is pas relevant bij echte enterprise-deals.

---

> **STATUS NA SESSIE 34 (2026-05-23 + 2026-05-24 verlenging):**
>
> **Code-changes (frontend-only, alleen hard-refresh nodig):**
> 1. Tekstpaneel input-contrast gefixt: `color:var(--ink-0)` → `var(--paper)` op `.ed-tx-field textarea`, `.ed-tx-input`, `.ed-tx-select` (regel ~1860).
> 2. Export-popover (editor) + dashboard inline export-menu: tekst-glyphs TT/IG/YT/SQ vervangen door echte gekleurde SVG-logo's (TikTok cyan+magenta+white, Instagram radial gradient, YouTube rood, Facebook blauw). RAW blijft amber tekst-glyph.
> 3. Export-popover compactere layout: `.meta` is nu flex space-between zodat platform-naam links en resolutie rechts op één regel passen. Min-width 240→280 (editor) / 230→270 (dashboard). Sub-tekst ingekort ("centre crop" / "no re-encode" weg, "· 9:16" weg want impliciet).
>
> **Backup sessie 34:** `dj-clip-cutter/static/index.html.pre-sessie34.bak` (642 KB)
>
> **Infrastructuur deze sessie (24-mei verlenging):**
> - Landing-pagina live op `https://djclips-nl-by-mono-labs.pages.dev` via Cloudflare Pages, auto-deploy bij elke `git push` naar `main` van GitHub repo `sjuulstudios/djclips.nl-by-MONO-LABS`.
> - Aparte werkmap voor landing-deploys: `~/Documents/Claude/Projects/clipdrop-landing-deploy/` (los van de hoofd-Clip Live git-repo om publieke landing niet te vermengen met privé app-code).
> - **Open:** djclips.nl koppelen aan Cloudflare Pages (nameserver-switch in TransIP — Fase 3 van het launch-plan).
>
> **Nieuwe plan-documenten opgesteld (nog niet geïmplementeerd):**
> - `SESSIE34-CAPTION-FONTS-PLAN.md` — uitgebreide caption-fonts library, hover-preview dropdown, color-wheel voor text + background. 5 fases, ~9.5u totaal. Bevat 4 beslispunten voor Sjuul.
> - `SESSIE34-PASSWORD-RESET-PLAN.md` — **security-critical**, ontbreekt momenteel volledig in auth.py (geen forgot/reset endpoint, geen UI). Plan leunt zwaar op Supabase Auth's ingebouwde reset-flow (token-gen, expiry, one-time-use, email-versturen) en bouwt daar een rate-limited Flask laag + frontend pagina overheen. Dekt 16 OWASP-aanvallen af in een security checklist. 5 fases, ~5.5u totaal. Bevat 4 beslispunten voor Sjuul. **Aanbeveling: bouwen vóór beta-launch.**
>
> **Openstaand voor sessie 35:**
> 1. **Hoog prioriteit:** Sjuul beslist over de 4 beslispunten in `SESSIE34-PASSWORD-RESET-PLAN.md` (deze ontbrekende functionaliteit is een launch-blocker zodra echte gebruikers gaan testen).
> 2. Sjuul beslist over de 4 beslispunten in `SESSIE34-CAPTION-FONTS-PLAN.md`.
> 3. Launch-fase 3: djclips.nl DNS koppelen aan Cloudflare Pages (nameserver-switch in TransIP).
> 4. Launch-fase 4: dmg builden (carry-over uit sessie 31/32/33: dev-server herstarten + `./build_macos.sh dmg` + smoketest, en `supabase functions deploy update-usage`).
> 5. Launch-fase 5: Stripe live mode activeren (`STRIPE-DNS-RUNBOOK.md`) — pas wanneer DNS + dmg werken.
> 6. Background recut-queue (`SESSIE33-RECUT-QUEUE-PLAN.md`).

---



> **STATUS NA SESSIE 33 — AUTONOOM (Sjuul afwezig, 2026-05-23):**
>
> Sjuul gaf opdracht "werk autonoom voor de komende klussen, ik ben een paar uur weg" + een vraag om de openstaande sessie-33 lijst te triagen. Resultaat:
>
> **Afgerond deze sessie (alle wijzigingen frontend-only in `static/index.html` — hard-refresh volstaat, geen server-restart nodig):**
>
> 1. **Beta-flyer uit scope** (HANDOVER.md ge-edit): alle "Beta-onboarding-flyer + uitnodigingsmail" carry-overs uit sessies 28/29/30/31/32 backlogs verwijderd. Sjuul wil dit niet meer. Vervangen door _"uit scope sinds sessie 33"_ regel onder elke sectie. Ook de losse "iets om in beta-flyer te benoemen" remark bij PermissionError opgeruimd.
>
> 2. **Split-feature volledig opgeruimd** (sessie 33 punt 3 uit lijst):
>    - `editorSplit()` (regel 8550) — pure dead code, was nergens aangeroepen
>    - `_editorSplitAtRel()` — gebruikt via `STATE.splitMode` mousedown handler
>    - `editorToggleSplitMode()` — gebruikt door C/Esc keyboard shortcut
>    - C/Esc keyboard shortcut in `bindZoomKeys` (regel ~9046)
>    - `STATE.splitMode` flag — alle 5 callsites
>    - `.tracks` mousedown branch voor split-mode + mousemove/mouseleave listeners voor split-cursor
>    - CSS: `.ed-tool-split`, `body.is-split-mode .timeline`, `.ed-split-cursor` (regel 3075-3109)
>    - HTML: `<div class="ed-split-cursor" id="ed-split-cursor">` element (regel ~3844)
>    - Backend `/api/split-clip` endpoint blijft draaien — niet aangeraakt, kan later weer vanuit UI worden aangeroepen als nodig.
>
> 3. **Loop-mode toggle prominenter gemaakt** (sessie 33 punt 4 uit lijst):
>    - HTML (regel ~3818): `<button class="btn btn-icon loop-btn">` → `<button class="btn loop-toggle">` met SVG-icoon + `<span class="loop-lbl">Loop Off</span>` + `<span class="loop-dot">`. Patroon analoog aan bestaande Snap-toggle voor consistentie.
>    - CSS (regel ~1076): oude `.loop-btn.is-on` 6-regel definitie vervangen door complete `.loop-toggle` set met:
>      - Inactief: ghost (transparent + paper-dim), zelfde dimensies als snap-toggle
>      - Actief: feller-amber wash + ring + pulserende amber-dot (1.6s loop-pulse animatie)
>      - Nieuwe `.timeline.is-looping .trim-region::after` glow-lijn onder de IN/OUT band (2.2s loop-band-pulse animatie) zodat de loop óók in de timeline zelf zichtbaar is, niet alleen op de knop
>      - `prefers-reduced-motion: reduce` honored voor beide animaties
>    - JS (regel ~8449): `setLoopBtnState(on)` update nu ook `#tl-loop-lbl` text ("Loop On"/"Loop Off") en toggled `.is-looping` class op `.timeline` zodat de glow-lijn aan/uit gaat.
>
> 4. **Cleanup-script gerund**: `python3 scripts/cleanup_legacy_jobs.py` (dry-run) → **0 cleanup-kandidaten gevonden** (24 owned jobs). HANDOVER schatte 18, maar die zijn blijkbaar al eerder opgeruimd. `--apply` niet meer nodig. `output/` is 13GB / 28 folders, allemaal owned. Geen actie.
>
> 5. **Background recut-queue: PLAN geschreven, code NIET** (sessie 33 punt 5 uit lijst): Sjuul gaf opdracht "uitvoeren" maar dit is een refactor van `app.py` van ~180 regels met race-condition risico's en Sjuul kan niet testen tijdens autonoom werk. Liever een plan-document zodat Sjuul + Claude in sessie 34 samen reviewen voor we bouwen. Plan staat in nieuwe file: `SESSIE33-RECUT-QUEUE-PLAN.md` in project root. Bevat: architectuur (`_RECUT_QUEUE` dict + worker thread + `/api/recut-status/<recut_id>` endpoint + backwards-compatible opt-in via `?async=1` query param), edge cases (browser sluit, memory leak, race conditions, lock ordering), frontend `_recutAsync` helper, test-flow, en 4 beslispunten voor sessie 34.
>
> **Verificatie deze sessie:**
> - `python3 -m py_compile app.py auth.py cutter.py billing.py analyzer.py` → OK
> - `node --check` op extracted inline JS-blok (~406KB) → OK
> - Bracket-balans `{}/[]/()` in HTML: identiek vóór en na, alleen size verschilt (~3.9KB kleiner door netto verwijdering split-code, ~beetje groter door uitgebreidere loop-CSS)
> - `<button>` count vóór en na: identiek (160/160)
>
> **Backups (SESSIE 33):**
> - `dj-clip-cutter/static/index.html.pre-sessie33.bak`
>
> **Gewijzigde files sessie 33:**
> - `dj-clip-cutter/static/index.html` — split-feature opgeruimd + loop-toggle UI
> - `HANDOVER.md` — beta-flyer carry-overs verwijderd, deze sessie-33 sectie toegevoegd
> - `SESSIE33-RECUT-QUEUE-PLAN.md` — nieuw, plan-document voor recut-queue
>
> **Niet aangeraakt sessie 33:** alle .py files, edge functions, build_macos.sh, landing/*.
>
> **Wat Sjuul ziet als resultaat (na hard-refresh ⌘+Shift+R):**
> - Geen "C" keyboard-shortcut meer in editor (split-mode is volledig weg)
> - Loop-knop heeft nu zichtbaar tekst-label "Loop Off" / "Loop On" + amber-dot bij actief
> - Bij Loop On: pulserende amber glow-lijn onder de IN/OUT trim-band in de timeline
> - Geen UI- of functionele regressies in trim/stretch/export workflow (alleen de C-shortcut + scissor-tool zijn weg, maar de UI-knoppen daarvoor waren al sinds sessie 32d verwijderd)
>
> **Openstaand voor sessie 34:**
> 1. **Sjuul handmatig (carry-over uit sessie 31/32):** dev-server herstarten (alleen nodig voor sessie-31 backend changes die nog niet live zijn), `./build_macos.sh dmg`, smoketest uit `SESSIE31-REBUILD-RUNBOOK.md`.
> 2. **Edge function `update-usage` deployen** (carry-over uit sessie 30/31/32): `cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter" && supabase functions deploy update-usage`.
> 3. **Background recut-queue implementeren**: review `SESSIE33-RECUT-QUEUE-PLAN.md` samen met Sjuul, beantwoord de 4 beslispunten, dan implementeren. Schatting: 2-3 uur.
>
> **Bewust geskipt (sessie 33):**
> - Beta-onboarding-flyer + uitnodigingsmail — definitief uit scope op verzoek Sjuul. NIET MEER TOEVOEGEN aan toekomstige openstaande lijsten.
> - Legacy job cleanup — 0 kandidaten, niets te doen.

---

> **STATUS NA SESSIE 32 — SECURITY RONDE (laatste werk vandaag):**
>
> Volledige security-audit op basis van 4 "vibe-coding warning" video's. Bevinding: fundamenten waren al goed (auth via Supabase, IDOR opgelost in sessie 28 via `_require_job_access`, geen secrets in frontend, dubbele secret-scan in `build_macos.sh`). Twee gaten dichtgezet vandaag:
>
> **Fix 1 — Rate limiting (afgerond + live op dev-server):**
> - `dj-clip-cutter/requirements.txt` — `flask-limiter>=3.5` toegevoegd
> - `dj-clip-cutter/app.py` regels ~84-149 — limiter init + `_rate_limit_key` helper + 429 JSON errorhandler + graceful-fallback `_NoLimiter` voor als de lib nog niet geinstalleerd is
> - 7 endpoints beschermd met `@limiter.limit(...)`:
>   - `/api/auth/signup` 5/uur per IP
>   - `/api/auth/login` 10 per 5 min per IP
>   - `/api/auth/refresh` 30/uur per IP
>   - `/api/billing/checkout` 10/uur per user (via `_rate_limit_key`)
>   - `/api/billing/portal` 10/uur per user
>   - `/api/upload` 20/uur per user
>   - `/api/upload-local` 20/uur per user
> - Storage = `memory://` (geen Redis); resets bij dev-server restart — prima voor lokaal-draaiende tool
> - Per-user key = eerste 32 chars van het JWT (voorkomt IP-rotation bypass)
> - `python3 -m py_compile app.py` → OK
> - Sjuul heeft `pip install "flask-limiter>=3.5"` gedraaid in venv en de dev-server herstart. Boot-log toont: `INFO Rate limiter geinitialiseerd (in-memory)` → live geverifieerd.
> - Backups: `dj-clip-cutter/app.py.pre-ratelimit.bak`, `dj-clip-cutter/requirements.txt.pre-ratelimit.bak`
>
> **Fix 2 — RLS policies in version control (afgerond + live in Supabase):**
> - Nieuwe map: `dj-clip-cutter/supabase/migrations/`
>   - `001_rls_policies.sql` — enable RLS + SELECT policy (auth.uid()=id) + UPDATE policy met kolom-bescherming via `is not distinct from (select ... from public.profiles where id = auth.uid())`. Beschermde kolommen: `plan`, `usage_this_period`, `quota_reset_date`, `stripe_customer_id`, `stripe_subscription_id`. INSERT/DELETE EXPLICIET REVOKED van `authenticated` role.
>   - `README.md` — stap-voor-stap voor Sjuul (Dashboard SQL Editor path) + verificatie + live-test recept + rollback-instructie
> - Sjuul heeft `001_rls_policies.sql` gerund in Supabase SQL Editor (project ref `lbabsffxefkrxwzkbzar`). Verificatie-query `select polname, polcmd from pg_policy where polrelid = 'public.profiles'::regclass` geeft de 2 verwachte policies terug:
>   - `Users can read own profile` (cmd=r)
>   - `Users can update own profile (safe columns)` (cmd=w)
>
> **Bewust geparkeerd (NIET geimplementeerd):**
> - Concurrency limit (max-N gelijktijdige jobs per user, voorkomt 10-tabs-tegelijk-uploaden). Sjuul wil eerst beta-feedback voor hij dit aanzet. Quota-gate is voor nu voldoende — kleine race condition is acceptabel.
> - Database indexing — alle queries zijn `.eq('id', user_id)` of `.eq('stripe_customer_id', ...)`. PK + UNIQUE constraints geven automatische indexes. Pas reviewen >10k users.
> - Webhook IP allowlist boven op Stripe signature verification — extra laag, niet kritiek.
>
> **Memory bijgewerkt:** `project_clip_live_security.md` (nieuw) + index-entry in `MEMORY.md`.
>
> **Vorige sessie 32-rondes (frontend-only, eerder vandaag) blijven hieronder staan voor referentie.**

---

> **STATUS NA SESSIE 32 — Timeline-editor UX rondje af. Stretch-bug definitief gefixt, inline trim-editor opent niet meer per ongeluk de timeline-editor, audio stopt bij back-button, Export-knop start nu een directe export i.p.v. alleen recut, playhead is sleepbaar en start/stopt op de IN/OUT handles, asterix + scissor weggehaald (alleen Trim als primaire actie), "Clip file not yet rendered" overlay opgelost. ALLE wijzigingen frontend-only in `static/index.html` — geen server-restart nodig, alleen hard-refresh (⌘+Shift+R).**
>
> **Belangrijkste root-cause vondsten deze sessie (= toekomstige debug-tips):**
>
> 1. **Stretch-bug "split_at must be > 0.5 s from each end" (sessie 32c+32d):**
>    De vorige `editorTrimAtPlayhead` had 5 branches met inconsistente drempels (0.4 / 0.55 / 0.05) én gebruikte `dur = v.duration || clip.duration` — twee verschillende waardes voor "clip-duur". Browser-decoded `v.duration` kan ~0.1s afwijken van analyzer's `clip.duration` door codec-rounding. Dat creëerde een "shadow zone" waarin een handle visueel net buiten clip stond, maar volgens v.duration nog binnen → naar /api/split-clip met split_at dat backend's 0.5s-marge overschreed → 400-error.
>    **Bovendien** had de eerste fix-iteratie een logische fout in `hasBand`: alleen "naar binnen" gecheckt (`t.inSec > 0.05 || t.outSec < dur - 0.05`), miste het pure-stretch-geval waar beide handles naar BUITEN bewogen waren → viel terug op split-at-playhead → split_at op currentTime=0 → backend 400.
>    **Fix:** `editorTrimAtPlayhead` gerefactored naar één pad: `if (hasBand) → /api/recut` (met `Math.abs(...) > 0.05` voor zowel naar-binnen als naar-buiten). `else → /api/split-clip` (alleen voor split-at-playhead). Single source of truth = `clip.duration`. Plus `editorSplit` en `_editorSplitAtRel` gehardened met drempel 0.55 en `clip.duration`-based validatie.
>
> 2. **"Clip file not yet rendered" overlay na recut (sessie 32e — de killer):**
>    De cache-buster `?v=<timestamp>` werd naïef APPENDED ná `withAuth()`. Maar `withAuth()` voegt altijd `?token=<JWT>` toe, dus de finale URL werd `/api/clip/x/y.mp4?token=xxx?v=123` — TWEE query-string starts. Browser parseerde dat als één string met `token = "xxx?v=123"` → backend's `_require_job_access(..., allow_query_token=True)` faalde → 403 → `<video>` kreeg niks → onerror → overlay. Recut zelf was succesvol, ffmpeg had de file geschreven, maar de browser kon hem niet ophalen.
>    **Fix:** check op bestaand `?` in de URL en gebruik `&` als joiner. Pattern: `const joiner = newSrc.indexOf('?') >= 0 ? '&' : '?'; newSrc += joiner + 'v=' + ts;`. Dezelfde fix in de retry-onerror handler.
>
> 3. **Trim auto-naar-editor vanuit inline editor card (sessie 32b):**
>    De `<div class="clip" onclick="openClipEditor(idx)">` bubblede clicks. Browser synthesizes een click op een mousedown→mouseup sequentie, ook als de muis tijdens drag buiten het ce-panel viel. Daardoor: drag handle in inline editor → mouseup → browser dispatched click → card opende de timeline-editor.
>    **Fix:** `cardClickOpen(ev, idx)` wrapper checkt `ev.target.closest('.ce-panel')` en `closest('.clip .info .r')`. Plus 300ms window via `window._ceJustFinishedDrag = Date.now()` om de synthesized click ná drag te blokkeren.
>
> 4. **Rename-input contrast bleef onleesbaar na fix (sessie 32c):**
>    Mijn selector `.clip .cap .inline-rename-input` matchte alleen de dashboard-kaart, NIET de cue-list `.cue-title` rename waar Sjuul aan de gang was.
>    **Fix:** generieke selector `.inline-rename-input` met `!important` op color/background/border + `-webkit-text-fill-color` voor Safari input-color quirks. Cue-list krijgt iets kleinere font-size via context-override.
>
> 5. **Playhead start verkeerd + niet sleepbaar (sessie 32d):**
>    `updateEditorTime` deed `ph.style.left = (cur/v.duration)*100%` op `.tracks` — maar `.tracks` heeft breedte `vDur = leftMax + clipDur + rightMax`. Cur=0 plaatste de playhead op de stretch-zone-begin (zwart, vóór de clip). Plus de knob had z-index 6 wat onder trim-band lag.
>    **Fix:** projectie via `virtSecToPct(cur + leftMax, map)`. Knob z-index 6→50 + hit-area 10/8px → 18/14px met `pointer-events:auto` op pseudo-element. Plus `updateEditorTime` pauzeert nu automatisch bij `cur >= outSec - 0.02s` (respecteert loop-mode en source-mode).
>
> **Wat in deze sessie is opgelost, in chronologische volgorde:**
>
> ### Sessie 32 (eerste ronde — UI compactness + eerste stretch-poging)
> 1. **Stretch-bug eerste poging:** drempels gesynchroniseerd in `editorTrimAtPlayhead` (regel ~8650) en drag-handler (regel ~9191) op 0.05. Toast-fallback voor "twilight zone" 0.05-0.5s. _(Werkte ten dele — sessie 32c+d voltooide de fix.)_
> 2. **Cue-list opschonen:** DROP/TRANS/BUILD/CUE-tag-pill verwijderd, "Energy ★ 0" weggehaald, BPM behouden, `cue` padding 10/12→6/10, gap 6→4, radius 10→8 → ~35% meer clips per viewport.
> 3. **Dashboard `.clip .info` strook:** BPM verwijderd uit pill (staat al boven de set), score (★ N) verwijderd, iconen gegroepeerd met dunne verticale divider (★ links | ✏ ⬇ → rechts), padding 12/14→8/12, betere tooltips.
>
> ### Sessie 32b (Sjuul feedback ronde 1)
> 4. **Rename-blok contrast — eerste poging:** tekstkleur op `.clip .cap .inline-rename-input` van amber naar wit op donker-amber gradient. _(Werkte voor dashboard kaart, miste cue-list — fix afgerond in 32c.)_
> 5. **Stretch-bug ronde 2:** `hasBand` op 0.55, nieuwe `forceRecut` flag voor twilight zone. _(Verdere refactor in 32c.)_
> 6. **4 knoppen in `.clip .info .r` gelijk:** `.mini-btn` + `.icon-mini` allebei 28x28 met identieke styling. Voorheen 32x32 vs 26x26.
> 7. **Inline trim niet meer auto-naar-editor:** `cardClickOpen(ev, idx)` wrapper + `_ceJustFinishedDrag` 300ms-window. Voorkomt dat de browser-synthesized click na een drag in `.ce-panel` de timeline-editor opent.
>
> ### Sessie 32c (deep-dive refactor + UX polish)
> 8. **`editorTrimAtPlayhead` deep-dive refactor:** 5 branches → 1 pad. Single source of truth = `clip.duration`. `if (hasBand) → /api/recut`; `else → /api/split-clip` (alleen voor split-at-playhead). _(Logisch fout in hasBand later opgelost in 32d.)_
> 9. **Rename-contrast écht gefixt:** generieke `.inline-rename-input` selector met `!important` op color/background. `cue-title .inline-rename-input` override voor compactere font-size.
> 10. **Audio doorlopen na back-button:** in `switchView()` detect `prevView === 'editor' && name !== 'editor'` → pause `<video id="ed-video">` + reset play-icon. Nieuwe helper `hoverPreviewStopAll()` stopt ook hover-preview audio bij elke view-switch.
> 11. **Re-export → directe Export-flow:** inline editor's "Re-export" knop hernoemd naar "Export". `_ceCommitReexport` doet nu: (1) recut als handles bewogen → master clip update, (2) `startExport([clipIdx], label)` — standaard aspect+folder picker. Knop initieel enabled (user kan ook unedited clip exporteren).
>
> ### Sessie 32d (Sjuul feedback ronde 2 — playhead + asterix/scissor)
> 12. **Stretch-bug definitief opgelost:** `hasBand = (Math.abs(t.inSec) > 0.05) || (Math.abs(t.outSec - dur) > 0.05)` — vangt nu ook pure stretch (beide handles naar buiten).
> 13. **Asterix + scissor weg uit timeline-toolbar:** `<button id="ed-split-toolbar">` en `<button id="ed-split-mode-btn">` verwijderd. Alleen Trim-knop (▮▮) blijft als primaire actie. JS-functies `editorSplit` en `_editorSplitAtRel` blijven bestaan voor mogelijke keyboard-shortcut binding (geen UI-trigger meer).
> 14. **Playhead start op IN-handle:** in `video.onloadedmetadata` springt naar `STATE.trim.inSec` i.p.v. `0.05`. `updateEditorTime` projecteert nu via `virtSecToPct(cur + leftMax, map)` zodat playhead niet meer in de stretch-zone start.
> 15. **Playhead sleepbaar:** knob z-index 6→50, hit-area 18px elke kant + 14/16px boven/onder.
> 16. **Stop bij OUT-handle:** `updateEditorTime` pauzeert automatisch bij `cur >= outSec - 0.02s` (respecteert loop-mode en source-mode).
>
> ### Sessie 32e (de killer bug — render issue na stretch)
> 17. **"Clip file not yet rendered" overlay na recut:** cache-buster URL-joiner bug opgelost. Zie root-cause #2 hierboven. **DIT WAS DE LASTIGSTE VAN DE HELE SESSIE** — de toast `Stretched to …` zei dat het lukte, file stond ECHT op disk, maar de browser kon hem niet ophalen door een dubbele `?` in de URL.
>
> **Gewijzigde files sessie 32 (alle iteraties):**
> - `dj-clip-cutter/static/index.html` — alle wijzigingen frontend-only
>
> **Niet aangeraakt sessie 32:** `app.py`, `cutter.py`, `analyzer.py`, `auth.py`, `billing.py`, alle edge functions, alle Python-bestanden buiten static/. Geen server-restart nodig — alleen hard-refresh.
>
> **Backups (sessie 32):**
> - `dj-clip-cutter/static/index.html.pre-sessie32.bak` (begin van sessie)
> - `dj-clip-cutter/static/index.html.pre-sessie32b.bak`
> - `dj-clip-cutter/static/index.html.pre-sessie32c.bak`
> - `dj-clip-cutter/static/index.html.pre-sessie32d.bak`
>
> **Wat Sjuul ziet als resultaat (visueel + functioneel geverifieerd op Lisa Korver Hör Berlin set, drop #3 met stretch tot 2:16):**
> - Stretch werkt end-to-end, ook bij grote stretches (1+ minuut).
> - Playhead start op IN-handle, scrub'en lukt, stopt bij OUT.
> - Export-knop in inline editor doet directe export (aspect picker + folder picker).
> - Audio stopt bij back-button.
> - Rename in cue-list: witte tekst op donker amber, leesbaar.
> - Geen "Clip file not yet rendered" meer na recut.
> - Asterix + scissor weg, Trim is enige actie-knop links onder.
> - Mini-pill iconen even groot.
> - Cue-list 35% compacter zonder leesbaarheid in te leveren.
>
> **Openstaand voor sessie 33:**
> 1. **Sjuul handmatig nog niet gedaan (uit sessie 31):** dev-server herstarten + `./build_macos.sh dmg` + smoketest uit `SESSIE31-REBUILD-RUNBOOK.md`. Sessie 32 was puur frontend dus dat is voor sessie 32-changes niet meer nodig (hard-refresh volstaat), maar de sessie 31 backend-changes (bpm-stamp off, letterbox, watermark, brand stack collapsibles) zitten nog niet in een dmg.
> 2. **Edge function `update-usage` deployen** (carry-over uit sessie 30 / 31): `cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter" && supabase functions deploy update-usage`.
> 3. **Optioneel:** `editorSplit` en `_editorSplitAtRel` JS-functies opruimen — UI-knoppen zijn weg sinds 32d, alleen keyboard-shortcut "C" (regel ~9940) wijst er nog naar. Pure dead code als die shortcut ook ongebruikt blijft.
> 4. **Optioneel:** loop-mode toggle prominenter maken — Sjuul kan nu wel/niet loopen tussen IN/OUT maar de UI laat dat niet duidelijk zien.
> 5. **Optioneel:** `/api/recut` na auto-track synchroon → background-queue (carry-over uit sessie 30).
>
> **Bewust geskipt (sessie 33, op verzoek Sjuul):**
> - Beta-onboarding-flyer + uitnodigingsmail — uit scope. Niet meer toevoegen aan toekomstige openstaande lijsten.
> - Legacy job cleanup (`scripts/cleanup_legacy_jobs.py --apply`) — 18 owner-less folders ~3.4 MB, al onzichtbaar via API, geen security/functionele impact. Pas oppakken als `output/` ooit echt hygiene-werk vraagt.

---

> **STATUS NA SESSIE 31 — beide bugs aangepakt, watermark live, Brand Stack inklapbaar. Sjuul moet nog dev-server herstarten + .dmg rebuilden + smoketest doen. Runbook: `SESSIE31-REBUILD-RUNBOOK.md`.**
>
> **Wat opgelost is (in volgorde):**
>
> 1. **Bug #1 — BPM/Key corner-stamp force-off (`cutter.py`):**
>    - In `_load_brand_assets_for_job` wordt `bpm_cfg['enabled']` nu altijd op `False` gezet bij laden. Brand_kit.json blijft intact (`bpm_stamp` block in de JSON wordt niet verwijderd), maar geen enkele recut/export gaat nog drawtext-ten met de stamp.
>    - Backend-only fix — er is geen aparte editor-preview overlay voor BPM-stamp in de frontend, alle "144 BPM · 4B" pixels komen uit ffmpeg drawtext. Bestaande clips die in eerdere sessies zijn gecut houden hun ingebakken stamp tot ze gerecut worden.
>    - Re-activeren is later triviaal: verwijder de drie regels die `bpm_cfg['enabled']=False` zetten in `_load_brand_assets_for_job`.
>
> 2. **Bug #2 — "Follow horizontally" zoomt nog steeds (deep dive):**
>    - **Belangrijke vondst:** Lisa Korver source is **1920×1080 LANDSCAPE 16:9** (geverifieerd via ffprobe), niet vertical zoals de HANDOVER-hypothese veronderstelde. Pan-mode op landscape source IS wiskundig altijd een zoom: `pan_w = 1080 × 9/16 = 607` pixels breed, dus 32% van source-breedte → schaalt naar 1080×1920 = 1.78× vergroting. Dat is geen bug in de code, dat is de definitie van pan-mode.
>    - **Echte fix:** nieuwe derde tracking-mode `letterbox` toegevoegd. Geen crop, scale-to-fit + pad met zwarte balken. Hele scene blijft zichtbaar zoals Sjuul verwachtte. Letterbox is nu de **default voor nieuwe clips** — pan/zoom blijven opt-in.
>    - `cutter.py: _build_tracked_vertical_crop(crop_mode='letterbox')` returnt sentinel `'__LETTERBOX__'`. `_build_vertical_cmd` herkent het en skipt de crop-stage, gebruikt alleen `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:...:black`.
>    - `app.py: save_track` whitelistet 'letterbox' naast 'pan'/'zoom'. `_derive_with_tracking` accepteert nu lege keyframes als crop_mode='letterbox'.
>    - **Frontend (`static/index.html`):**
>      - Segmented control heeft nu 3 knoppen: "Fit (no zoom)" (default, aan), "Follow horizontally", "Follow + zoom"
>      - Hint-paragraphs voor alle 3 modes, eerlijk gelabeld
>      - `_paintEditorTrackBox` returnt early in letterbox-mode (geen overlay-box nodig)
>      - `_applyTrackingToClipAndRecut` triggert nu ook recut zonder keyframes als mode='letterbox'
>      - `editorTrackSetCropMode` accepteert 'letterbox'
>      - `STATE.editorTrack.cropMode` default is nu 'letterbox'
>    - Eerlijkere hint-tekst voor pan-mode: "Crops to 9:16 at full source height" (niet meer suggestief dat er geen zoom plaatsvindt).
>
> 3. **Watermark JS-bindings + render-pipeline LIVE:**
>    - Backend (`app.py`):
>      - Nieuwe constants: `BRAND_WATERMARK_DIR`, `_WATERMARK_MAX_BYTES=2MB`, `_WATERMARK_ALLOWED_EXT={.png,.jpg,.jpeg}`
>      - Vier endpoints: POST `/api/brand-kit/watermark` (upload, magic-bytes check), GET (serve), DELETE (wipe), POST `/api/brand-kit/watermark/settings` (partial update — corner/opacity/size_pct/enabled zonder image re-upload)
>      - Settings opgeslagen in brand_kit.json onder key `watermark` met fields {path, ext, corner, opacity, size_pct, enabled, uploaded, bytes}
>    - Backend (`cutter.py`):
>      - Nieuwe helper `_build_watermark_overlay_segment(watermark, target_w, target_h, in_label, out_label)` — analoog aan `_build_logo_overlay_segment` maar met aparte labels zodat watermark NA logo in de chain komt (watermark altijd bovenop)
>      - `_maybe_compose_brand_vf` accepteert nu `watermark=` kwarg, chain'd watermark-segment na logo
>      - `_load_brand_assets_for_job` returnt nu 5-tuple `(fonts, logo, overlays, bpm_cfg, watermark)`
>      - `_build_landscape_cmd`, `_build_vertical_cmd`, `cut_clip_landscape`, `cut_clip_vertical` accepteren allemaal `watermark=` en geven door
>      - Beide `_load_brand_assets_for_job`-callsites (`process_clips`, `recut_clip`) en alle 4 retry-paths bijgewerkt
>    - Frontend (`static/index.html`):
>      - "Coming soon" label op Watermark-sectie weggehaald
>      - accept-attribute op file input gewijzigd: `.png,.jpg,.jpeg,image/png,image/jpeg` (matcht backend)
>      - Opacity-slider range 10–100% (was 10–80%), default 60%
>      - Size-slider range 5–60% (was 3–14%), default 18%
>      - `_renderBrandWatermark(wm)` — vult preview/meta/clear/toggle/opacity/size/corner uit kit-state
>      - `brandWatermarkUpload(file)` — POST FormData
>      - `brandWatermarkClear()` — confirm + DELETE
>      - `brandWatermarkUpdate(patch)` — POST settings endpoint
>      - `applyBrandKit` roept nu ook `_renderBrandWatermark(kit.watermark)` aan
>      - `_bindBrandStackButtons` heeft 6 nieuwe binds: upload/clear/toggle/corner/opacity/size — allemaal met `dataset.bound` idempotency
>
> 4. **Brand Stack collapsibles:**
>    - Generieke helper `initBrandStackCollapsibles()` die elke direct-child van `#view-style .cap-right` met een `.panel-h` als collapsible behandelt
>    - Header-click toggles alle siblings van die sectie behind de header (paneel-h blijft zichtbaar, body collapses)
>    - Chevron `▾` toegevoegd aan elk `.ti`, draait 90° bij collapse
>    - State in `localStorage` onder key `cliplive.brandstack.collapsed.v1` (kebab van eerste 60 chars van `.ti`-tekst)
>    - Default: alleen eerste sectie open, rest collapsed
>    - Buttons/inputs in headers worden NIET getriggerd (via `closest('button, input, .toggle, a, select')` check)
>    - Init aangeroepen aan einde van `renderStyle()`, na `renderBrandStack()`
>
> 5. **Edge function `update-usage` is in repo aanwezig (uit sessie 30) maar nog NIET gedeployed.**
>    - Stap 1 in `SESSIE31-REBUILD-RUNBOOK.md` (en idem in sessie 30 runbook).
>    - Sjuul moet handmatig: `cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"` + `supabase functions deploy update-usage`.
>
> **Verificatie deze sessie:**
> - `python3 -m py_compile app.py cutter.py` → OK
> - `node --check` op het volledige inline JS-blok (398 KB) → OK
> - HTML balans niet expliciet hercheckt; alle edits zijn pure additions of in-place replacements binnen bestaande tags.
>
> **Backups (SESSIE 31):**
> - `dj-clip-cutter/app.py.pre-sessie31.bak`
> - `dj-clip-cutter/cutter.py.pre-sessie31.bak`
> - `dj-clip-cutter/static/index.html.pre-sessie31.bak`
>
> **Gewijzigde files sessie 31:**
> - `dj-clip-cutter/cutter.py` (~120 regels: bpm force-off + letterbox + watermark helper + watermark plumbing in beide cmd-builders en cut_clip functies + tuple-uitbreiding in _load_brand_assets_for_job + recut letterbox handling)
> - `dj-clip-cutter/app.py` (~140 regels: BRAND_WATERMARK_DIR + 4 watermark endpoints + 'letterbox' whitelist in save_track + _derive_with_tracking letterbox-pad-branch + crop_mode validatie uitgebreid)
> - `dj-clip-cutter/static/index.html` (~250 regels: letterbox-button in segmented control + nieuwe hint + STATE default 'letterbox' + _paintEditorTrackBox early-return + _applyTrackingToClipAndRecut keyframe-loose voor letterbox + watermark UI cleanup + _renderBrandWatermark + brandWatermark* helpers + 6 bindings + initBrandStackCollapsibles + renderStyle hook)
>
> **Nieuw bestand in project root:** `SESSIE31-REBUILD-RUNBOOK.md`
>
> **Niet aangeraakt sessie 31:** auth.py, billing.py, analyzer.py, tracking.py, edge functions, runtime_config.py, build_macos.sh, entitlements.plist, landing/*.
>
> **Openstaand voor sessie 32 (in volgorde):**
> 1. **Sjuul handmatig:**
>    - Dev-server herstarten (Python changes vereisen restart) en de smoketest uit `SESSIE31-REBUILD-RUNBOOK.md` doen.
>    - Edge function `update-usage` deployen (zie stap 1 in runbook) als dat in sessie 30 nog niet gedaan was.
>    - `./build_macos.sh dmg` voor distributie.
> 2. **Optioneel:** `/api/recut` na auto-track synchroon → background-queue (carry-over uit sessie 30).
> 3. **Optioneel:** legacy job cleanup via `scripts/cleanup_legacy_jobs.py --apply` (carry-over uit sessie 29).
>
> _Beta-onboarding-flyer + uitnodigingsmail uit scope sinds sessie 33 — Sjuul wil dit niet meer._

---

> **TWEE OPENSTAANDE BUGS — HOOGSTE PRIORITEIT VOOR SESSIE 31:**
>
> **BUG #1 — BPM/Key corner-stamp moet WEG (zowel preview als export).**
> Sjuul ziet "144 BPM · 4B" rechtsboven in de preview en die wordt ook in de export gebakken. Hij wil dit volledig verwijderen.
> - Frontend: zoek `bs-bpm-toggle` / BPM stamp render in `static/index.html` — preview-overlay van BPM stamp verbergen.
> - Backend: `cutter.py` heeft een `bpm_cfg` flow die de BPM/Key in elke ffmpeg cmd burnt via drawtext. Default moet UIT staan (was opt-in via `bs-bpm-toggle` maar staat blijkbaar toch aan).
> - Zoek waar `bpm_cfg.show` of vergelijkbaar default `True` is en zet naar `False`. Of strip de drawtext compleet uit `_build_clip_data_for_stamp` / `_maybe_compose_brand_vf`.
> - Test: na fix moet zowel de preview als een verse recut zonder "144 BPM · 4B" tonen.
>
> **BUG #2 — "Follow horizontally" zoomt nog steeds in.**
> Sjuul klikt op de Pan-mode segmented control, maar de video toont nog steeds een ingezoomde versie waarbij links/rechts wordt afgesneden. Hij wil dat de video **van boven tot onder de hele preview vult** met zwarte balken links/rechts toegestaan — geen zoom dus.
> - Verwacht gedrag pan-mode: ffmpeg cropt `src_h * 9/16 × src_h` (volle hoogte × ratio-breedte), dan `scale=1080:1920:force_original_aspect_ratio=decrease, pad=1080:1920` — dat zou full height moeten geven.
> - Live geobserveerd: de video lijkt **alsnog ingezoomd**. Mogelijke oorzaken:
>   - `_build_tracked_vertical_crop` pan-mode berekent `pan_w = int(src_h * 9/16)`. Bij een **vertical source** (src_h > src_w, bv. portrait 9:16) is `pan_w = src_h * 9/16` te BREED ten opzichte van src_w. De code clamped `pan_w = src_w` — maar dan is de crop NIET volle hoogte, want het is alleen src_w breed × src_h hoog (= aspect 9:16 al). De pan heeft dan geen effect, en het beeld blijft "ingezoomd" voelen omdat het de oorspronkelijke vertical-cut is.
>   - De Lisa Korver source is 1080×1920 vertical (al portrait). Pan-mode op een vertical source is **conceptueel onmogelijk** — er valt niets te pannen, er IS al 9:16.
>   - **Echte fix:** detecteer dat de source al ≤ 9:16 is en val terug op een full-height "no-op" crop met scale-to-fit + pad. Of: behandel het anders — toon de source 1:1 in het frame met letterboxing.
> - **Andere mogelijkheid:** de source IS landscape (16:9) maar de pan-crop berekening clamped iets verkeerd. Eerst even verifiëren met:
>   - `cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter" && ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$(ls CLIP\ DROP\ DJ-SETS/Lisa\ Korver*.mp4 | head -1)"`
> - Test: klik Follow horizontally → auto-track → preview moet **identiek aan de landscape variant** ogen (zelfde verticale uitstraling), alleen smaller. Volledig bovenste-tot-onderste pixel zichtbaar.
>
> **HOE TE BEGINNEN IN SESSIE 31:** start de server, run het start-prompt, en pak deze 2 bugs op in volgorde. Beide bugs raken alleen de tracking/preview-flow — alle andere sessie 30-fixes blijven werken.

> **STATUS NA SESSIE 30c — pan-modus + 1:1/4:5 tracking + auto-refresh JWT LIVE GETEST EN WERKEND (met bovenstaande twee bugs als follow-up).**

> **STATUS NA SESSIE 30c — pan-modus + 1:1/4:5 tracking + auto-refresh JWT LIVE GETEST EN WERKEND.**
>
> **Wat opgelost is in deze sessie-30 vervolgflow:**
>
> 1. **Auto-refresh JWT (sessie 30b):**
>    - Nieuwe edge function: `/api/auth/refresh` (route in `app.py`) en helper `refresh_session` in `auth.py` die Supabase's `auth.refresh_session(refresh_token)` aanroept.
>    - Frontend: `refreshAccessToken()` met single-flight (`_refreshInFlight`) zodat parallelle 401s niet 10x refreshen.
>    - **Proactieve timer:** `scheduleProactiveRefresh()` vuurt 5 minuten vóór token-expiry (default Supabase 60min = elk 55min refreshen).
>    - **Reactief in `api()` wrapper:** bij 401 → refresh proberen → request retry met nieuw token. Pas als refresh zelf faalt komt de Session-expired toast.
>    - Timer wordt opgeruimd bij `clearSession()`.
>    - **Live bevestigd:** Sjuul bleef ingelogd over uur+ heen tijdens de test.
> 2. **Pan-only tracking als default (sessie 30c):**
>    - `cutter.py: _build_tracked_vertical_crop()` nu `crop_mode='pan'|'zoom'` parameter. Pan = full-source-height × (height × target_aspect) breedte, alleen x interpoleert tussen keyframes.
>    - `cutter.py: _build_vertical_cmd` en `cut_clip_vertical` nemen nieuwe `track_crop_mode` parameter door.
>    - `cutter.py`: beide plekken die `track_kfs` ophalen (in `process_clips` en `recut_clip`) lezen nu ook `track_info.get('crop_mode')` uit het tracking-JSON-bestand.
>    - `app.py: save_track` whitelistet `crop_mode` in body en persisteert in tracking-file. Auto-track-status endpoint preserveert bestaande mode bij rerun (default 'pan' voor nieuwe).
>    - **Frontend:** segmented control bovenin Track-drawer: "Follow horizontally" (default) / "Follow + zoom". CSS in `.ed-trk-mode` / `.ed-trk-mode-btn`.
>    - `STATE.editorTrack.cropMode` toegevoegd. `_loadEditorTrackForCurrent` leest `crop_mode` uit response. `editorTrackPersist` stuurt het mee.
>    - `_paintEditorTrackBox`: in pan-mode wordt het overlay-box gerenderd op **full-height × (height × output_ratio) breedte** op de huidige cx-positie. Resize-handles verborgen in pan-mode (niet zinvol).
>    - `_onEditorTrackBoxPointerMove`: verticaal slepen genegeerd in pan-mode (cy gepind op 50).
>    - `editorTrackSetCropMode(mode)`: switcht mode, persisteert, en als er al keyframes zijn triggert automatic `_applyTrackingToClipAndRecut()` voor instant feedback.
>    - `_applyTrackingToClipAndRecut`: persist nu ook `crop_mode` mee bij POST, en invalideert 1:1 + 4:5 cached derivatives zodat ze met tracking opnieuw renderen.
> 3. **1:1 en 4:5 tracking-support (sessie 30c):**
>    - `_build_tracked_vertical_crop()` heeft een nieuwe optionele `target_aspect` parameter (default 9/16). Pas 1.0 in voor 1:1, 0.8 in voor 4:5.
>    - `app.py`: nieuwe helper `_derive_with_tracking()` die het 1:1 of 4:5 variant rendert **vanuit de source video** met de tracked crop op de juiste aspect. Pakt source uit `job['video_path']`, leest tracking-JSON, bouwt ffmpeg-cmd met `_build_tracked_vertical_crop(target_aspect=1.0|0.8)`.
>    - `api_derive_ratio` routet automatisch naar `_derive_with_tracking` als er een tracking-bestand bestaat + source video op disk staat. Anders fallback naar de legacy centre-crop (voor clips zonder tracking).
>    - Accepteert nieuwe `force: true` body param om de cache te bypassen.
>    - **Frontend:** wanneer ratio-rail naar 1:1 of 4:5 wisselt op een getrackte clip, wordt `force=true` meegestuurd zodat de centre-cropped variant wordt vervangen door de tracked render.
>
> **LIVE TEST RESULTATEN via Chrome MCP (Lisa Korver x Hör Berlin clip 1):**
> - ✅ Sjuul nog ingelogd na uren afwezigheid (auto-refresh werkt)
> - ✅ Track-drawer toont segmented control met "Follow horizontally" als default
> - ✅ Pan-mode hint correct getoond ("The camera follows the DJ left-right while keeping the full scene height visible")
> - ✅ Auto-track DJ genereerde 21 SMOOTHED keyframes in ~5s
> - ✅ Status: "Tracking applied to clip export" / "Tracked crop applied. Your clip now follows the DJ."
> - ✅ Video rerender voltooid, `<video>` element bereikt `readyState: 4`
> - ✅ Resultaat-mp4: 1080×1920 (vertical 9:16), duration 15.07s
> - ✅ Preview toont DJ met **volledige hoogte zichtbaar** (gele tegels, koptelefoon, gezicht, lichaam) — geen ingezoomde crop meer
> - ✅ Switchen naar "Follow + zoom" toggle: UI update, hint-tekst wisselt, gold dashed-line box verschijnt met resize-handles
>
> **Backend / frontend wijzigingen sessie 30b+30c:**
> - `dj-clip-cutter/auth.py` — nieuwe `refresh_session()` helper (~33 regels)
> - `dj-clip-cutter/app.py` — `/api/auth/refresh` route, `_derive_with_tracking()` helper, `api_derive_ratio` tracking-aware (~150 regels totaal)
> - `dj-clip-cutter/cutter.py` — `_build_tracked_vertical_crop()` accepteert `crop_mode` + `target_aspect`, `_build_vertical_cmd` / `cut_clip_vertical` nemen `track_crop_mode` parameter mee (~50 regels totaal)
> - `dj-clip-cutter/static/index.html` — `refreshAccessToken()`, `scheduleProactiveRefresh()`, segmented control, `_paintEditorTrackBox` pan-aware, drag-block, `_derive` force=true, mode-switch auto-recut (~250 regels totaal)
>
> **Niet aangeraakt sessie 30c:** tracking.py (auto-track detector), build_macos.sh, runtime_config.py, edge functions, billing.py.
>
> **Openstaand voor sessie 31:**
> 1. **Sjuul handmatig:** `supabase functions deploy update-usage` (uit sessie 30) + RLS-policy + `./build_macos.sh dmg`. Volg `SESSIE30-REBUILD-RUNBOOK.md`.
> 2. **Watermark JS-bindings + render-pipeline** (UI met "Coming soon" badge staat klaar).
> 3. **Brand Stack collapsibles** voor verdere compactness.
>
> _Beta-onboarding-flyer + uitnodigingsmail uit scope sinds sessie 33 — Sjuul wil dit niet meer._

> **STATUS NA SESSIE 30 — alle 11 punten van Sjuul afgewerkt + beta-blocker code-side klaar. Volgt nog: edge-function deployen, rebuild, retest. Runbook: `SESSIE30-REBUILD-RUNBOOK.md` in project root.**
>
> **Wat opgelost is (in volgorde):**
>
> 1. **Beta-blocker (`supabase_admin` ontbrekt in bundle):**
>    - Nieuwe edge function `supabase/functions/update-usage/index.ts` — accepteert `Authorization: Bearer <JWT>`, verifieert via anon client, doet quota-read/reset/increment via SERVICE_ROLE (uit Supabase env, niet client).
>    - `auth.py` heeft nieuwe `call_update_usage_edge_function(token, action)` helper + `get_user_from_token` fallback voor profile-fetch.
>    - `app.py` — `_get_or_refresh_profile` en `_increment_usage` accepteren nu een optionele `access_token` en gaan via de edge function wanneer `supabase_admin is None`. Alle 5 callsites doorgegeven.
>    - `access_token` wordt op het in-memory job-dict gestempeld bij upload (twee plekken) en uit `_persist_job_snapshot` gestript voor we naar disk schrijven (no JWT-on-disk).
>    - **Sjuul moet handmatig:** `supabase functions deploy update-usage`.
> 2. **Autotracking fix — beeld beweegt nu écht mee:**
>    - Server-side was alles aanwezig (auto-track endpoint produceert keyframes, `_load_keyframes_for_clip` + `_build_tracked_vertical_crop` werken). Het probleem was puur frontend.
>    - **RAF-loop** voor crop-preview (`_startTrackCropPreviewRaf` / `_stopTrackCropPreviewRaf`) — `timeupdate` is browser-limited tot ~4 Hz, RAF is 60 Hz.
>    - **Auto-enable crop preview** zodra er keyframes binnen zijn na auto-track.
>    - **Automatic recut** (`_applyTrackingToClipAndRecut`) na auto-track-completion: keyframes server-side persisteren via POST `/api/track/<job>/<clip>`, dan `/api/recut/<job>` triggeren met dezelfde start/end. Video-src refresht zodat de nieuwe versie meteen wordt afgespeeld.
>    - Beide completion-paths (sync respons + async polling) hooken in `_applyTrackingToClipAndRecut`.
> 3. **Secret API keys audit + code-review:**
>    - Geen hardcoded secrets in source. Alles via `os.getenv` / `Deno.env.get`.
>    - Live check `dist/Clip Live.app` → geen `.env`, geen service_role files in bundle.
>    - `build_macos.sh` nieuwe stap 3: defensieve secret-scan die de build laat falen bij `.env`, `*service_role*`, `*.private.pem`, `id_rsa*` in de .app. Plus `grep` op hardcoded token patterns (warning).
>    - **Belangrijke fix:** `_persist_job_snapshot` strippt nu `access_token` voordat het job-dict naar `job.json` op disk wordt geschreven.
> 4. **Em-dashes opgeruimd (tool + landing):**
>    - Python-script: vervangt em-dashes alleen in user-visible text, niet in code-comments (skipt `//`, `/* */`, `<!-- -->`).
>    - Resultaat: 146 user-visible em-dashes weggehaald. ~441 in code-comments resterend.
> 5. **Onboarding multi-select checkmarks:**
>    - In-tool wizard: nieuwe `.wiz-bubbles[data-mode="multi"] .wiz-bubble::after` met empty round indicator die vult met amber+check in `.on` state.
>    - Hint "Pick all that apply." → "Select all that apply, then continue." (zowel in tool als landing).
> 6. **Drop-a-set sound-wave halo:**
>    - Drie concentrische ringen (`::before`, `::after`, `<span class="halo-extra">`) op `.big-ico`, staggered `dropzone-halo` animatie 3.4s.
>    - Subtle `dropzone-ico-breathe` op de tile zelf.
>    - `prefers-reduced-motion` respected.
> 7. **Sidebar compacter + scrollbare recent-sets:**
>    - Padding/gaps/font-sizes ~25% kleiner.
>    - `.sidebar` is nu `overflow:hidden`, alleen `#sidebar-recent` heeft `flex:1 1 0` + `overflow-y:auto`. Brand/nav/cloud-sync/account altijd zichtbaar.
> 8. **Sidebar identiteit + Profile section:**
>    - Email weg uit sidebar; vervangen door `.ac-workstation` "Workstation of: [FULL NAME]" gevuld uit `STATE.session.profile.full_name`.
>    - Fallback bij missing name: "Set your name in Settings" (italic-amber).
>    - Nieuwe Settings → Profile sectie met Full name, Artist name, Email (readonly). Save-button alleen actief bij dirty state. Posts naar nieuwe `/api/profile` POST endpoint.
>    - Backend: whitelist 2 velden. Path 1 admin client (dev), path 2 anon client + user-JWT (bundle, vereist RLS-policy "users update own row"). **Sjuul moet RLS-policy aanmaken in Supabase als die er niet is** (zie runbook stap 2).
> 9. **Knop/filter padding:**
>    - `.chip` 8x12 → 5x10, font 12 → 11.5.
>    - `.btn` 10x16 → 7x14, radius 12 → 10, font 13 → 12.5.
>    - `.btn-icon` 38x38 → 32x32.
> 10. **Pro-badge bij Cloud sync card (sidebar):**
>     - `.upgrade-pro-tag` met slotje SVG + "Pro" tekst. Class `is-pro-locked` (free) / `is-paid` (pro/studio) toggled door `renderSidebarAccount`.
>     - Dashed border op locked Connect-knop.
>     - Click delegated naar bestaande `openWatchFolderUI()` (dat de gating al deed, alleen ontbrak visuele indicatie).
> 11. **Laadbar teksten vermenselijken:**
>     - `PROC_STEPS` herschreven: "Reading your live DJ set..." / "Analysing the waveform and beats" / "Listening for the drops..." / "Picking the best moments..." / "Cutting your clips..." `sub`-velden leeggemaakt (geen FFmpeg/VideoToolbox/Demucs/Metal meer).
>     - Processing scene-header + proc-list h2/lead herschreven naar plain English.
>     - `app.py` worker `_update_job(message=...)` lines vervangen door dezelfde menselijke teksten.
> 12. **Brand Stack:**
>     - Titel: "Scene 06 - Brand Stack" → "Brand Stack".
>     - Leesbaarheid: alle `var(--ink-3)` op dark bg vervangen door `var(--paper)`/`var(--paper-dim)` binnen `#view-style` scope.
>     - Nieuwe Watermark sectie met "Coming soon" badge — UI staat klaar (upload, corner, opacity, size, toggle) maar JS + render-pipeline nog niet gehookt. Voor sessie 31.
>     - Hero copy compacter en explainer: "Set your brand here once... Every time you open the editor, your preferences load automatically".
>
> **Verificatie deze sessie:**
> - `python3 -m py_compile app.py auth.py` → OK
> - `bash -n build_macos.sh` → OK
> - `node --check` op het volledige inline JS-blok (375 KB) → OK
> - HTML balans: `{}`=3159/3159, `[]`=383/383, `()`=7607/7610 (3 extra `(` zijn pre-existing in CSS/regex, verified via diff op `.pre-sessie30.bak`).
> - Bestaande `dist/Clip Live.app` gegrep't op secrets → schoon.
>
> **Backups (SESSIE 30):**
> - `dj-clip-cutter/app.py.pre-sessie30.bak`
> - `dj-clip-cutter/auth.py.pre-sessie30.bak`
> - `dj-clip-cutter/static/index.html.pre-sessie30.bak`
>
> **Gewijzigde files:**
> - `dj-clip-cutter/supabase/functions/update-usage/index.ts` — nieuw, 7263 bytes
> - `dj-clip-cutter/auth.py` — 10234 → 12257 bytes (helper + fallback)
> - `dj-clip-cutter/app.py` — 214105 → 220040 bytes (edge fallback, /api/profile endpoint, access_token strip, humanised messages)
> - `dj-clip-cutter/static/index.html` — 581308 → 602258 bytes (alle UI changes)
> - `dj-clip-cutter/build_macos.sh` — secret-scan toegevoegd
> - `landing/{index,contact,privacy,terms}.html`, `landing/README.md` — em-dashes opgeruimd
>
> **Nieuw bestand in project root:** `SESSIE30-REBUILD-RUNBOOK.md` — letterlijke commando's voor Sjuul.
>
> **Openstaand voor sessie 31:**
> 1. **Sjuul handmatig:** edge function deployen + RLS-policy + rebuild .dmg + smoketest. Volg `SESSIE30-REBUILD-RUNBOOK.md`.
> 2. **Watermark JS-bindings + render-pipeline** (UI met "Coming soon" badge staat klaar). Upload-endpoint, persist in `brand_kit.json`, `cutter.py` overlay-filter.
> 3. **Brand Stack collapsibles** voor verdere compactness (nu nog vertical scroll per sectie). Niet kritiek voor beta.
> 4. **`/api/recut` na auto-track is synchroon** — kan tot 30s blokkeren bij lange clips. Background-queue als nice-to-have.
>
> _Beta-onboarding-flyer + uitnodigingsmail uit scope sinds sessie 33 — Sjuul wil dit niet meer._

> **BETA-BLOCKER NA LIVE BUNDLE-TEST (2026-05-23):**
>
> Tijdens de end-to-end .dmg test crashte de upload met `Upload failed: supabase_admin niet geconfigureerd`. Diagnose:
> - `auth.py` regel 51 maakt alleen `supabase_admin` aan als `SUPABASE_SERVICE_ROLE_KEY` in env zit
> - In de bundle ontbreekt deze key — by design (service_role is server-only, mag NIET in een client-side .app)
> - `app.py` upload-flow roept ergens quota-bookkeeping aan (`_check_quota_for_user` of `_increment_usage`) die `supabase_admin` nodig heeft
> - Eerder al voor billing opgelost via edge-function fallback (sessie 27) — dezelfde patroon moet hier
>
> **Wat moet gebeuren in sessie 30 (in volgorde):**
> 1. **Edge function `update-usage` maken** in `supabase/functions/update-usage/index.ts`:
>    - Accepteert `Authorization: Bearer <jwt>` van client
>    - Verifieert JWT, extracten user_id
>    - Doet quota-check + increment in `profiles` tabel via SUPABASE_SERVICE_ROLE_KEY (uit Supabase env, niet client)
>    - Deploy: `supabase functions deploy update-usage` (zonder --no-verify-jwt)
> 2. **`app.py` upload-flow patchen** — analoog aan `billing.py` edge-function fallback:
>    - Als `supabase_admin is None` → call edge function met user's JWT ipv direct admin-client
>    - Idem voor quota-reset bij periode-verloop
> 3. **Rebuild + retest** — `./build_macos.sh dmg`, upload Lisa Korver test, verifieer dat quota van 0/2 naar 1/2 gaat
>
> **Andere bevindingen uit live bundle-test:**
> - **Plan-veld in Diagnostics:** toonde "?" omdat user_info['profile'] None is wanneer supabase_admin niet geconfigureerd. **Opgelost in sessie 29** (app.py regel 1173) — toont nu "free (no profile data — supabase_admin not configured in this bundle)". Wordt vanzelf nuttiger zodra punt 1 hierboven is opgelost.
> - **PermissionError bij open-launch (Finder):** "app.py crashed: PermissionError(1, 'Operation not permitted')" — gebeurde 4x op 17 en 23 mei. Console-launch (`Contents/MacOS/Clip Live`) werkt altijd. Workaround voor testers: rechts-klik → Open. Echte fix vereist meer onderzoek (mogelijk macOS TCC permission probleem). Geen show-stopper voor unsigned beta met Gatekeeper-instructies.
> - **Wat werkte 100% in .dmg test ✅:**
>   - Bundle bootstrap (Flask + browser + UI)
>   - Login met `business+dmgtest1@sjuulstudios.com`
>   - Library scoping (0 jobs leak van vorige accounts)
>   - Diagnostics ZIP download
>   - Diagnostics Copy as text → paste in TextEdit
>   - Settings UI

> **STATUS NA SESSIE 29 — vier kleine maar belangrijke verbeteringen voor de beta-rollout, allemaal achter de schermen klaargezet zodat Sjuul alleen nog hoeft te bouwen + pushen:**

> **STATUS NA SESSIE 29 — vier kleine maar belangrijke verbeteringen voor de beta-rollout, allemaal achter de schermen klaargezet zodat Sjuul alleen nog hoeft te bouwen + pushen:**
>
> **Wat afgerond is:**
> 1. **Landing site Vercel-ready (`landing/`):**
>    - `vercel.json` toegevoegd — security headers (HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy), aggressive caching voor static assets, `index.html` → `/` redirect.
>    - `favicon.svg` + `og-image.svg` (1200x630) gemaakt met Clipdrop Live branding (donkere achtergrond, amber accent).
>    - `robots.txt` + `sitemap.xml` voor SEO.
>    - Head-tags toegevoegd in alle 4 HTML-pagina's (index/contact/privacy/terms): `og:image`, `twitter:card`, `theme-color`, `favicon`, `canonical`.
>    - `landing/.gitignore` — sluit .DS_Store, .vercel/, .vscode/ uit.
>    - `landing/README.md` herschreven met letterlijke GitHub → Vercel deploy-instructies (eén commando per regel, geen markdown fences), inclusief custom domain `clipdroplive.com` setup via TransIP DNS.
>    - **Wat Sjuul nog moet doen:** GitHub repo `clipdrop-live-landing` aanmaken, `cd "landing" && git init` + push, Vercel project koppelen via dashboard, custom domain DNS in TransIP zetten. Formspree endpoint (`REPLACE_ME` in index.html) activeren.
> 2. **In-app Send logs knop (`app.py` + `static/index.html`):**
>    - Nieuw endpoint `/api/debug/logs` in `app.py` (regel 1094-1230), na `/api/auth/me`. Vereist auth, accepteert `?format=text` voor copy-paste of default ZIP. Bundelt: `summary.txt` (user_id, email, plan, platform, Python versie, ffmpeg versie, BASE_DIR/OUTPUT_DIR), `launcher.log` (tail 200KB uit `~/Library/Application Support/Clip Live/launcher.log` via `CLIP_LIVE_USER_DATA` env-var of fallback), `job_history_yours.json` (alleen jobs van de caller, filenames als basename only).
>    - Frontend in Settings-view: "Diagnostics" sectie met drie knoppen — **Download logs** (ZIP via `withAuth()`), **Copy as text** (clipboard via `?format=text`), **Open support email** (mailto met pre-filled template). Status-regel toont feedback. Alle handlers in `renderSettings()`, met `dataset.bound` idempotency.
>    - Nooit andere users' data of clip-bestanden — alleen diagnostische metadata.
> 3. **NaN BPM display fix (`static/index.html`):**
>    - Regel ~5471 deed `Math.round(status.bpm)` op een object → `NaN BPM` in clips-header. Fix: zelfde safe extraction als regel 6814-6816 (`typeof === 'number'` check + `.bpm`/`.value` fallback + `Number.isFinite` guard).
> 4. **Cleanup-script (`dj-clip-cutter/scripts/cleanup_legacy_jobs.py`):**
>    - Dry-run default — toont alle owner-less folders in `output/` met grootte en reden (job.json ontbreekt OF user_id=None). Met `--apply` verplaatst naar `.quarantine-YYYYMMDD-HHMMSS/` mét REPORT.txt (geen `rm -rf` zonder bevestiging).
>    - Op disk vandaag: 23 owned jobs, **18 cleanup-kandidaten** (HANDOVER schatte 38 maar dat blijkt eerder al opgeruimd). Totale grootte kandidaten: ~3.4 MB.
>    - Commando: `cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter" && python3 scripts/cleanup_legacy_jobs.py` (dry-run) of `... --apply` (echt).
>
> **Verificatie:**
> - `python3 -m py_compile app.py` → OK
> - `python3 -m py_compile scripts/cleanup_legacy_jobs.py` → OK
> - `node --check` op alle inline JS-blocks in `static/index.html` → OK
> - `json.load(landing/vercel.json)` → OK
> - Dry-run van cleanup-script ✅ identificeert 18 kandidaten zonder iets te verplaatsen.
>
> **Backups (SESSIE 29):**
> - `dj-clip-cutter/app.py.pre-sessie29.bak`
> - `dj-clip-cutter/static/index.html.pre-sessie29.bak`
>
> **Gewijzigde files:**
> - `dj-clip-cutter/app.py` — nieuw endpoint `/api/debug/logs` (~140 regels), bovendien helpers in zelfde stijl als sessie-28 patches.
> - `dj-clip-cutter/static/index.html` — Diagnostics sectie in Settings-view, JS handlers (Download/Copy/Mail logs), NaN BPM fix.
> - `dj-clip-cutter/scripts/cleanup_legacy_jobs.py` — nieuw, 175 regels.
> - `landing/index.html`, `landing/privacy.html`, `landing/terms.html`, `landing/contact.html` — head-tag additions (og:image, twitter:card, favicon, canonical, theme-color).
> - `landing/vercel.json`, `landing/robots.txt`, `landing/sitemap.xml`, `landing/favicon.svg`, `landing/og-image.svg`, `landing/.gitignore` — nieuw.
> - `landing/README.md` — herschreven met GitHub → Vercel runbook.
>
> **Niet gewijzigd:** auth.py, billing.py, cutter.py, analyzer.py, tracking.py, edge functions, runtime_config.py, launcher.py, build_macos.sh, entitlements.plist.
>
> **Openstaand voor sessie 30 (in volgorde):**
> 1. **.dmg bouwen** via `cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter" && ./build_macos.sh dmg` — installer pipeline werkt al uit sessie 27, moet nu getest worden met SESSIE 28 sec patches + SESSIE 29 Send-logs + BPM-fix erin. Controleer: browser opent, Flask boot, signup werkt vanuit .app, library scoping ook in bundle correct, Diagnostics-knoppen werken vanuit de .app (lezen ze de juiste launcher.log?).
> 2. **Landing site live deployen** — Vercel-config staat klaar in `landing/`. Sjuul moet: (a) GitHub repo `clipdrop-live-landing` aanmaken, (b) `git init` + push vanuit `landing/`, (c) Vercel project koppelen, (d) custom domain DNS in TransIP zetten, (e) Formspree endpoint vervangen voor `REPLACE_ME`. Letterlijke commando's staan in `landing/README.md`.
> 3. **Optioneel: legacy job cleanup uitvoeren** — `--apply` op cleanup-script, daarna handmatig quarantine wissen.
>
> _Beta-onboarding-flyer + uitnodigingsmail uit scope sinds sessie 33 — Sjuul wil dit niet meer._

> **STATUS NA SESSIE 28 — kritieke library-scoping bug opgelost, alle job-endpoints zijn auth + ownership-gevalideerd, smoketest met twee accounts bevestigt isolatie:**
>
> **Wat opgelost is:**
> - **Library-scoping bug:** vóór sessie 28 was `/api/history` en alle `<job_id>` endpoints ongeauthenticeerd. Een tweede account op dezelfde lokale install zag alle jobs van vorige accounts. **Gereproduceerd door Sjuul** met `business+clip@sjuulstudios.com` die andermans sets zag.
> - **Helper `_require_job_access(job_id, allow_query_token=False)`** in `app.py` na `_require_authed_user`: trekt JWT uit Bearer-header óf `?token=` query param (voor media-routes), valideert, vergelijkt `job['user_id']` met caller. Geeft 404 (niet 403) bij mismatch zodat aanvallers niet kunnen probesen of een ID bestaat.
> - **30+ job-routes gepatched** met `_require_job_access`: status, source, clip, thumbnail, filmstrip, waveform, csv, spectrogram, download-all, download-favorites, render-clip, recut, favorite, rename, derive, reorder, add-marker, split-clip, snap-to-beat, style, export, export-preset, upload-social, publish, schedule-batch, clip-overlays GET+POST, track GET+POST+DELETE+auto+auto/status, subject-signature GET+POST+DELETE, history GET+DELETE, exports listing+reveal+copy-to+delete, progress SSE, clip-filmstrip.
> - **Frontend `withAuth(url)` helper** in `static/index.html` (vlak voor `api()`): voegt `?token=<JWT>` toe aan media-URLs die geen Bearer-header kunnen meesturen (img/video/EventSource). 10+ media-call-sites gepatcht: thumbnail (3x), filmstrip (3x), clip src (3x), source src, spectrogram, progress SSE. Download-knoppen (`bindDl`) kregen Bearer-header in fetch-init.
> - **`_append_to_history`** stamps nu `user_id` op elke job-entry. `/api/history` filtert op caller_id en returnt lege lijst voor anonymous callers (no leak).
> - **Backwards compat:** 38 pre-sessie-28 history entries hebben `user_id=None`. Die zijn nu voor niemand zichtbaar — private by default, geen leak. Bestanden blijven op disk staan voor handmatige rescue.
>
> **Smoketest (Lisa Korver x Hör Berlin, 424MB, 55 min set, 30 clips):**
> - Account A `business+s28a@sjuulstudios.com` aangemaakt via signup wizard
> - Library leeg ✅ (geen leak van pre-sessie-28 jobs)
> - Upload + analyzer: 143.6 BPM (auto-doubled van 71.8), key 4B G# major (90% conf), 30 drops gedetecteerd, parallel cutting → done in ~3 min
> - Editor opent clip 1: video src `/api/clip/702b2bf1/...?token=` werkt, readyState 4, playback OK, filmstrip + waveform laden ✅
> - Stripe Checkout via edge function: testkaart 4242 succeeded → webhook → profile.plan='pro', stripe_customer cus_UZ2ovTrjnVEH2X, stripe_sub sub_1TZuiXA5DKhJaSAFrlCM9V7m, quota 0/2 → 0/10 ✅
> - Stripe Portal: "Manage subscription" → billing.stripe.com sessie opent ✅
> - Account B `business+s28b@sjuulstudios.com` aangemaakt in nieuwe browser tab → Library 100% leeg (geen leak van Account A's Lisa set), badge FREE niet PRO, quota 0/2 niet 0/10 ✅
> - **20/20 cross-account security tests groen**: Account B's JWT op Account A's job_id geeft 404 op alle endpoints (status, source, clip, thumbnail, filmstrip, waveform, csv, download-all, spectrogram, render-clip, recut, favorite, rename, export, style, add-marker, split-clip, snap-to-beat, derive, history DELETE)
>
> **Belangrijke beta-blocker gevonden + opgelost (Supabase config, niet code):**
> - Supabase weigerde `.test` en `.example` TLDs → testers met odd domains kunnen niet signupen
> - Supabase Free email rate limit (2/uur) blokkeerde 3e signup
> - **Beide problemen opgelost door Email Confirmation UIT te zetten** in Supabase dashboard → Auth → Sign In/Up. Sjuul heeft dit live gedaan tijdens sessie 28. Voor v1.0 (paid launch) weer aanzetten zodra een eigen SMTP (SendGrid/Postmark/Resend) is gekoppeld.
>
> **Bekende NICE-TO-HAVE post-beta:**
> - **Output-folder isolation** (jobs in `OUTPUT_DIR/<user_id>/<job_id>/` ipv `OUTPUT_DIR/<job_id>/`) is bewust uitgesteld — Strategie B op de API-laag is genoeg voor beta. Bij multi-tenant cloud-deploy is dit wel nodig.
> - **38 legacy job-folders** zonder owner staan nog op disk in `output/`. Onzichtbaar voor iedereen via API, maar nemen disk-ruimte. Cleanup-script op de roadmap.
> - **Display-bug:** Clips header toont "NaN BPM · 55 min set" terwijl status.bpm.bpm = 143.6. HTML-formatter trekt waarde uit verkeerd veld. Cosmetic only, niet kritiek.
>
> **Gewijzigde bestanden (sessie 28):**
> - `dj-clip-cutter/app.py` — nieuwe `_require_job_access` helper, `_require_authed_user(allow_query_token=)` uitgebreid, `_append_to_history` user_id stamp, ~30 route patches
> - `dj-clip-cutter/static/index.html` — nieuwe `withAuth(url)` helper, 10+ media-URL patches, download-knop Bearer-header
> - Backup: `dj-clip-cutter/app.py.pre-sessie28.bak`
>
> **Geen wijzigingen aan:** auth.py, billing.py, cutter.py, analyzer.py, tracking.py, edge functions, runtime_config.py, launcher.py, build_macos.sh, entitlements.plist, landing/*.
>
> **Openstaand voor sessie 29 (in volgorde):**
> 1. **.dmg bouwen** via `./build_macos.sh dmg` — installer pipeline is werkend uit sessie 27, nu met de nieuwe sec patches erin
> 2. **Landing site live deployen** naar TransIP of Cloudflare Pages (privacy/terms staan klaar in `landing/` maar zijn nog niet gepushed)
> 3. **In-app Send logs knop** — voor wanneer testers crashen tegen onverwachte issues
> 4. **Optioneel: cleanup-script** voor de 38 legacy owner-less jobs in `output/`
> 5. **Optioneel: NaN BPM display fix** in clips header
>
> _Beta-onboarding-flyer uit scope sinds sessie 33 — Sjuul wil dit niet meer._


> **STATUS NA SESSIE 27 — beta-bundle bouwt, opent en boot zonder config-fouten:**
>
> **Wat werkt:**
> - `dj-clip-cutter/dist/Clip Live.app` bouwt schoon via `./build_macos.sh` (~5 min). ffmpeg+ffprobe worden in de bundle gekopieerd via een wrapper-script. .bak files worden uit toekomstige bundles defensief gestript.
> - **Browser opent automatisch** na app-start via `subprocess.run(['open', url])` (de oude `webbrowser.open` werkte niet in een gebundelde .app op macOS).
> - **`launcher.log`** schrijft naar `~/Library/Application Support/Clip Live/launcher.log` — debug-bron voor wanneer een gebruiker meldt dat de bundle stilletjes faalt.
> - **`runtime_config.py`** hardcodet publieke keys (Supabase URL/anon, Stripe publishable, price IDs). Geen .env meer nodig naast de .app. Dev-flow blijft werken (dotenv overrulet).
> - **Stripe via Supabase Edge Functions** — twee nieuwe functions:
>     - `supabase/functions/create-checkout-session/index.ts` (met JWT-verificatie)
>     - `supabase/functions/create-portal-session/index.ts` (met JWT-verificatie)
>   `billing.py` heeft een edge-function fallback: als geen lokale `STRIPE_SECRET_KEY`, roept hij de edge function aan met de user's JWT.
> - **app.py** geeft de Bearer-token door aan billing (2 plekken: `/api/billing/start` en `/api/billing/portal`).
> - **Privacy + Terms** aangevuld met sub-processors, AVG-rechten per artikel, retention per data-type, CCPA-sectie (wereldwijde verkoop), force majeure, account-suspension grounds, export controls, assignment, severability, entire agreement.
> - **Git repo geïnitialiseerd** (lokaal, baseline commit `b000a57`, branch `main`, 63 files). .env correct genegeerd.
> - **64 .bak files** opgeruimd naar `_bak-archive-2026-05-17.tar.gz` (3.6MB).
>
> **Open punten (in volgorde):**
> 1. **End-to-end smoketest** — Test 1 (account aanmaken in bundle) was uitgegeven maar resultaat niet teruggekoppeld. Tests 2–5 (upload+drop-detection, export, Stripe upgrade flow, Stripe portal) staan nog open.
> 2. **`./build_macos.sh dmg`** — .dmg voor distributie nog niet getest.
> 3. **Landing site live deployen** — privacy/terms aanpassingen + download-knop staan klaar in `landing/` maar zijn nog niet gepushed naar TransIP / Cloudflare Pages.
> 4. **Beta-testers werven** — uitnodigingsmail + Gatekeeper-instructies nog te schrijven.
> 5. **In-app "Send logs" knop** — voor wanneer testers crashen.
>
> **Bewust uitgesteld tot na macOS-beta:**
> - Apple Developer account ($99/jaar) — geen signing/notarization tot beta-feedback binnen.
> - Windows .exe + Windows code-signing certificaat.
> - Stripe LIVE-mode (nu nog TEST keys; testkaart `4242 4242 4242 4242`).
>
> **Nieuwe bestanden in repo:**
> - `dj-clip-cutter/launcher.py`
> - `dj-clip-cutter/runtime_config.py`
> - `dj-clip-cutter/ClipLive.spec`
> - `dj-clip-cutter/entitlements.plist`
> - `dj-clip-cutter/build_macos.sh`
> - `dj-clip-cutter/supabase/functions/create-checkout-session/index.ts`
> - `dj-clip-cutter/supabase/functions/create-portal-session/index.ts`
> - `INSTALLER-RUNBOOK.md` (in project root)
> - `cleanup_bak_files.sh` + `init_git.sh` (al gedraaid, mag blijven staan)
> - `.gitignore` (in project root)
>
> **Gewijzigde bestanden:**
> - `dj-clip-cutter/billing.py` — edge-function fallback + nieuwe `access_token` parameter
> - `dj-clip-cutter/app.py` — Bearer-token doorgegeven bij billing-aanroepen (2 plekken)
> - `landing/privacy.html` + `landing/terms.html` — substantiële uitbreidingen, datum 17 mei 2026


> **STATUS NA SESSIE 26:**
>
> - Wise Business account actief (Sjuul Studios, eenmanszaak, BSN als fiscaal ID)
> - Wise geeft een Belgisch IBAN (BE) — in Stripe "Belgium" als land van bankrekening selecteren, niet Nederland
> - Stripe uitbetalingsrekening = Wise BE IBAN ✅
> - Signup wizard: 4 bugs gefixed in `static/index.html` (progress bar, scrollbare secties, hover-knop, email-veld stap 4)
> - Stripe betaalflow volledig geverifieerd in testmodus: checkout → webhook → Supabase profiel update ✅
> - Test-account `test@test.com` heeft actief Pro-abonnement (`sub_1TY7LnA5DKhJaSAFEEphH3mZ`, `cus_UXBj3w9DhPo5Dm`)
> - Supabase profiel van test@test.com: `plan: pro`, `stripe_customer_id` + `stripe_subscription_id` correct opgeslagen
> - Server draait op http://127.0.0.1:5555 (herstart indien nodig via `./start.sh`)
> - Alle SESSIE 24/25 features intact — geen code-regressies

> **STATUS NA SESSIE 25:**
>
> - Server draait nog op http://127.0.0.1:5555 (pid 72143 uit Sessie 24)
> - `static/index.html` = 574836 bytes (identiek aan Sessie 24-eindstand) — rollback bevestigd via grep (0 pulse-markers) en Chrome MCP (`getElementById('ed-pulse-btn')` → null, `typeof bindBeatPulse` → undefined)
> - Backup `static/index.html.pre-sessie25.bak` blijft staan voor de zekerheid — niet gewist
> - **Supabase DNS-blip onderzocht en opgelost (transient, geen actie nodig):** tijdens de B1 live-test gaf de server `ConnectError: nodename nor servname provided`. Onderzoek: DNS resolveert prima vanuit Mac shell (`104.18.38.10` Cloudflare IP), `socket.getaddrinfo` werkt vanuit een verse Python, curl naar `https://lbabsffxefkrxwzkbzar.supabase.co/auth/v1/health` geeft 401 in 0.23s (Supabase bereikbaar). Re-test van `/api/auth/login` van Sjuul's pid 72143 → HTTP 200 met JWT + user_id + refresh_token. Browser-login getest, dashboard opent met jobId 94d6c9c7 automatisch geladen. Conclusie: korte transient DNS-hiccup tijdens m'n eerdere call, httpx-resolver heeft zichzelf hersteld. **Niets te fixen.**
> - Alle Sessie 24 deps + features volledig intact (B1 stretch+tracking, B2 preview-crop, B3 subject-signature)

> **STATUS NA SESSIE 25 — optie C B1 **GEBOUWD EN DAARNA TERUGGEDRAAID**. Pulse-feature werkte technisch (RAF-loop synced met synth-beat-grid uit `clip.bpm`+`clip.bar_duration`, bar-accent op clip.start, decay tau=0.11s, persist in localStorage), maar Sjuul oordeelde dat het geen user-waarde toevoegde. `static/index.html` is gerestored vanuit `static/index.html.pre-sessie25.bak` — file size terug naar 574836 bytes, JS syntax-validated, browser-side bevestigd dat de Pulse-knop weg is en bestaande Track/Text/Export-knoppen werken. Backup-file blijft op disk als reference. **Geen wijzigingen actief** in de codebase vanuit Sessie 25. B3 speed-ramp is niet aangeraakt. Pulse-feature werkte technisch (RAF-loop synced met synth-beat-grid uit `clip.bpm`+`clip.bar_duration`, bar-accent op clip.start, decay tau=0.11s, persist in localStorage), maar Sjuul oordeelde dat het geen user-waarde toevoegde. `static/index.html` is gerestored vanuit `static/index.html.pre-sessie25.bak` — file size terug naar 574836 bytes, JS syntax-validated, browser-side bevestigd dat de Pulse-knop weg is en bestaande Track/Text/Export-knoppen werken. Backup-file blijft op disk als reference. **Geen wijzigingen actief** in de codebase vanuit Sessie 25. B3 speed-ramp is niet aangeraakt.)

> **STATUS NA SESSIE 25:**
>
> - Server draait nog op http://127.0.0.1:5555 (pid 72143 uit Sessie 24)
> - `static/index.html` = 574836 bytes (identiek aan Sessie 24-eindstand) — rollback bevestigd via grep (0 pulse-markers) en Chrome MCP (`getElementById('ed-pulse-btn')` → null, `typeof bindBeatPulse` → undefined)
> - Backup `static/index.html.pre-sessie25.bak` blijft staan voor de zekerheid — niet gewist
> - **Supabase DNS-blip onderzocht en opgelost (transient, geen actie nodig):** tijdens de B1 live-test gaf de server `ConnectError: nodename nor servname provided`. Onderzoek: DNS resolveert prima vanuit Mac shell (`104.18.38.10` Cloudflare IP), `socket.getaddrinfo` werkt vanuit een verse Python, curl naar `https://lbabsffxefkrxwzkbzar.supabase.co/auth/v1/health` geeft 401 in 0.23s (Supabase bereikbaar). Re-test van `/api/auth/login` van Sjuul's pid 72143 → HTTP 200 met JWT + user_id + refresh_token. Browser-login getest, dashboard opent met jobId 94d6c9c7 automatisch geladen. Conclusie: korte transient DNS-hiccup tijdens m'n eerdere call, httpx-resolver heeft zichzelf hersteld. **Niets te fixen.**
> - Alle Sessie 24 deps + features volledig intact (B1 stretch+tracking, B2 preview-crop, B3 subject-signature)

> **STATUS NA SESSIE 24 — alles werkend (ongewijzigd):**
>
> - Server draait op http://127.0.0.1:5555 (laatste pid 72143 na restart via `_restart.sh`)
> - debug=False (productie-mode)
> - Alle SESSIE-21/22-deps geïnstalleerd: `fonttools[woff]`, `pyobjc-framework-Vision`, `opencv-python`, `ultralytics`
> - `homebrew-ffmpeg/ffmpeg/ffmpeg` actief met `--enable-libfreetype` → drawtext-filter aanwezig
> - YOLOv8n weights al lokaal in `models/`
> - Supabase migration `add_intake_columns_to_profiles` is live
> - 4 jobs op disk: `ac7373ae` (Lisa pre-fix, 26 clips, 72 BPM stamp), `94d6c9c7` (Franky, 151 proxy clips, 129 BPM, **subject_signature** locked uit clip 1), `00abd848` (Lisa post-fix, 30 clips, 144 BPM stamp), oude Ediine `46716f96` + `3a4eb44d`
> - Findings rapport: `SESSIE-24-FINDINGS.md` met bug-shortlist + groen-vinkjes-tabel + addendum 2 (B1/B2/B3 details)
> - Backups Sessie 24: `analyzer.py.pre-sessie24.bak`, `app.py.pre-sessie24.bak`, `tracking.py.pre-sessie24.bak`, `static/index.html.pre-sessie24.bak`

---

## START PROMPT — paste dit aan het begin van de volgende chat

> Plak dit letterlijk in een nieuwe Claude-chat (NIEUWSTE — Sessie 31 afgerond):

Lees /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/HANDOVER.md, in het bijzonder het STATUS-blok "NA SESSIE 31". SESSIE 31 (23 mei 2026, autonoom uitgevoerd) heeft vijf blokken afgerond: (1) **Bug #1 BPM/Key corner-stamp force-off** — in `cutter.py: _load_brand_assets_for_job` wordt `bpm_cfg['enabled']` altijd op False gezet bij laden. Backend-only fix want er is geen aparte frontend preview-overlay voor de stamp. Brand_kit.json blijft intact. (2) **Bug #2 pan-mode zoomt nog steeds** — diepgaande analyse via ffprobe wees uit dat Lisa Korver source 1920×1080 LANDSCAPE 16:9 is (niet vertical zoals HANDOVER hypothese veronderstelde). Pan-mode op landscape IS wiskundig altijd een zoom (pan_w = 1080×9/16 = 607 px breed, 32% van source → schaalt 1.78×). Geen code-bug, conceptuele mismatch. **Fix:** nieuwe derde tracking-mode `letterbox` toegevoegd (geen crop, scale-to-fit + pad met zwarte balken). Letterbox is nu de **default voor nieuwe clips**, pan/zoom opt-in. Volledig backend (`cutter.py` + `app.py`) + frontend (`static/index.html` segmented control met 3 knoppen + STATE default 'letterbox' + _paintEditorTrackBox early-return in letterbox + _applyTrackingToClipAndRecut keyframe-loose voor letterbox). (3) **Watermark JS-bindings + render-pipeline LIVE** — Watermark feature was "Coming soon", nu volledig werkend: backend endpoints (POST/GET/DELETE `/api/brand-kit/watermark` + POST `/api/brand-kit/watermark/settings` voor corner/opacity/size/enabled zonder re-upload), nieuw `BRAND_WATERMARK_DIR`, 2MB max, PNG/JPG accepted, magic-bytes check. `cutter.py`: nieuwe `_build_watermark_overlay_segment` helper analoog aan logo maar met aparte labels zodat watermark NA logo komt (altijd bovenop). `_maybe_compose_brand_vf` accepteert nu `watermark=` kwarg. `_load_brand_assets_for_job` returnt nu 5-tuple. Beide cmd-builders + cut_clip-functies + alle callsites + retry-paths bijgewerkt. Frontend: "Coming soon" weg, file accept .png/.jpg/.jpeg, opacity 10-100% default 60%, size 5-60% default 18%, `_renderBrandWatermark` + 3 helpers (upload/clear/update) + 6 bindings in `_bindBrandStackButtons` met dataset.bound idempotency. (4) **Brand Stack collapsibles** — generieke `initBrandStackCollapsibles()` die elke direct-child van `#view-style .cap-right` met `.panel-h` collapsible maakt. Chevron `▾` toegevoegd aan elk `.ti`, draait 90° bij collapse. State in localStorage `cliplive.brandstack.collapsed.v1`. Default: alleen eerste sectie open. Buttons/inputs in headers triggeren GEEN collapse. Init aangeroepen aan eind van `renderStyle()`. (5) **Edge function `update-usage` runbook** — function bestaat al in repo uit sessie 30, maar Sjuul moet hem nog deployen. Stap 1 in nieuwe `SESSIE31-REBUILD-RUNBOOK.md`. Verificatie sessie 31: `python3 -m py_compile app.py cutter.py` OK, `node --check` op de 398KB JS-block OK. Backups: `app.py.pre-sessie31.bak`, `cutter.py.pre-sessie31.bak`, `static/index.html.pre-sessie31.bak`. **Openstaand voor sessie 32 (in volgorde):** (a) **Sjuul handmatig:** dev-server herstarten (Python changes vereisen restart!) + smoketest uit `SESSIE31-REBUILD-RUNBOOK.md` doorlopen — verifieer dat BPM-stamp weg is na recut, dat "Fit (no zoom)" als default met zwarte balken werkt, dat watermark upload+render+overlay live in mp4 zit, dat Brand Stack secties inklapbaar zijn en de keuze persisteert. (b) **Edge function deployen** als dat in sessie 30 nog niet gedaan was: `cd dj-clip-cutter` + `supabase functions deploy update-usage`. (c) **`./build_macos.sh dmg`** voor distributie + smoketest in de gebundelde .app. (d) **Beta-onboarding-flyer + uitnodigingsmail** (carry-over). Niet aangeraakt sessie 31: auth.py, billing.py, analyzer.py, tracking.py, edge functions, runtime_config.py, build_macos.sh, entitlements.plist, landing/*. Server start: `cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter" && ./start.sh` op http://127.0.0.1:5555. Begin met opties + aanbeveling, wacht op "ja", dan los werken. Sjuul is niet-technisch — terminal-commando's letterlijk zonder markdown fences, één commando per regel met pad-quotes.

> Plak dit letterlijk in een nieuwe Claude-chat (oude prompt — Sessie 29 afgerond + .dmg live getest):

Lees /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/HANDOVER.md, in het bijzonder het BETA-BLOCKER blok bovenaan + het STATUS-blok "NA SESSIE 29". **De .dmg bundle is live getest op 23 mei 2026 en werkte voor login + library scoping + Diagnostics ✅, maar de upload crasht met "Upload failed: supabase_admin niet geconfigureerd" — dat is dé blocker voor beta-launch.** Diagnose: `auth.py` regel 51 maakt alleen `supabase_admin` aan als `SUPABASE_SERVICE_ROLE_KEY` in env zit. In de bundle ontbreekt die key by design (service_role mag NIET in client-side .app). `app.py` upload-flow roept ergens quota-bookkeeping aan die `supabase_admin` nodig heeft. **Aanpak (dezelfde patroon als sessie 27 billing-fix):** (1) Maak edge function `supabase/functions/update-usage/index.ts` die Bearer JWT verifieert en quota-check+increment doet via SUPABASE_SERVICE_ROLE_KEY (uit Supabase env, niet client). Deploy met `supabase functions deploy update-usage` zonder --no-verify-jwt. (2) Patch `app.py` upload-flow analoog aan `billing.py`: als `supabase_admin is None` → call edge function met user's JWT. Idem voor quota-reset bij periode-verloop. (3) Rebuild met `./build_macos.sh dmg` + retest met Lisa Korver upload, verifieer quota 0/2 → 1/2. Wat verder uit live-test bleek werkt: bundle boot, browser opent, login werkt, library scoping correct, Diagnostics ZIP-download werkt, Diagnostics Copy as text werkt. PermissionError-crash bij `open` launch (vs werkende console launch) — niet kritiek, workaround "rechts-klik → Open" werkt, vermelden in beta-flyer. Sessie 29 zelf had vier kleine verbeteringen klaargezet: (1) **Landing site Vercel-ready** — `landing/` heeft nu `vercel.json` (security headers + caching), `favicon.svg`, `og-image.svg` (1200x630, brand-kleuren amber op #0a0805), `robots.txt`, `sitemap.xml`, head-tag additions in alle 4 HTML-pagina's (og:image, twitter:card, theme-color, canonical, favicon), `.gitignore`, en herschreven `README.md` met letterlijke GitHub → Vercel deploy-instructies + custom domain `clipdroplive.com` via TransIP DNS. Sjuul moet zelf nog: GitHub repo `clipdrop-live-landing` aanmaken, `cd landing && git init` + push, Vercel project koppelen, DNS in TransIP zetten, Formspree endpoint vervangen voor `REPLACE_ME`. (2) **In-app Send logs knop** — nieuw `/api/debug/logs` endpoint in `app.py` (na `/api/auth/me`, ~140 regels), auth-required, levert ZIP of `?format=text`, bundelt summary (user/plan/platform/python/ffmpeg/paths) + launcher.log tail 200KB (via `CLIP_LIVE_USER_DATA` env-var of OS-fallback) + caller's eigen job_history. Settings-view in `static/index.html` heeft nieuwe "Diagnostics" sectie met Download logs / Copy as text / Open support email knoppen, allemaal in `renderSettings()` met dataset.bound idempotency. (3) **NaN BPM display fix** — `static/index.html` regel ~5471 deed `Math.round(status.bpm)` op een object; zelfde safe extraction toegepast als regel 6814-6816 (typeof check + .bpm/.value fallback + Number.isFinite guard). (4) **Cleanup-script** — `dj-clip-cutter/scripts/cleanup_legacy_jobs.py`, dry-run default, met `--apply` verplaatst owner-less jobs (job.json ontbreekt of user_id=None) naar `.quarantine-YYYYMMDD-HHMMSS/` met REPORT.txt. Dry-run vond 18 kandidaten (~3.4MB) — minder dan de geschatte 38 uit sessie 28, blijkbaar was er al opruimwerk gebeurd. Backups: `app.py.pre-sessie29.bak`, `static/index.html.pre-sessie29.bak`. Niet gewijzigd: auth.py, billing.py, cutter.py, analyzer.py, tracking.py, edge functions, runtime_config.py, launcher.py, build_macos.sh. Verificatie: `python3 -m py_compile app.py` OK, `node --check` op alle inline JS OK, `json.load(vercel.json)` OK, cleanup-script dry-run ✅. **Openstaand voor sessie 30 (in volgorde):** (a) **.dmg bouwen** via `cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter" && ./build_macos.sh dmg` — moet getest worden met sessie 28 sec patches + sessie 29 Send-logs + BPM-fix erin. Verificatie: browser opent, Flask boot, signup werkt vanuit .app, library scoping in bundle correct, Diagnostics-knoppen lezen juiste launcher.log. (b) **Landing site live deployen** — alles staat klaar, commando's in `landing/README.md`. (c) **Beta-onboarding-flyer + uitnodigingsmail** met Gatekeeper-instructies (`xattr -dr com.apple.quarantine "/Applications/Clip Live.app"` + rechts-klik → Open workaround voor unsigned .app). (d) Optioneel: cleanup-script daadwerkelijk runnen met `--apply`. Server start: `cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter" && ./start.sh` op http://127.0.0.1:5555. Begin met opties + aanbeveling, wacht op "ja", dan los werken. Sjuul is niet-technisch — terminal-commando's letterlijk zonder markdown fences, één commando per regel met pad-quotes.

> Plak dit letterlijk in een nieuwe Claude-chat (oude prompt — Sessie 28 afgerond):

Lees /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/HANDOVER.md, in het bijzonder het STATUS-blok "NA SESSIE 28". SESSIE 28 (22 mei 2026) loste een kritieke library-scoping bug op die Sjuul zelf had ontdekt: tweede account op dezelfde lokale install (`business+clip@sjuulstudios.com`) zag andermans sets. Drie blokken werk afgerond: (1) **Backend: Strategie B agressief** — nieuwe helper `_require_job_access(job_id, allow_query_token=False)` in `app.py` die JWT trekt uit Bearer-header óf `?token=` query param, valideert, en `job['user_id']` matched met caller. Returns 404 bij mismatch (geen probe-leak). Toegepast op ~30 job-routes: status, source, clip, thumbnail, filmstrip, waveform, csv, spectrogram, download-all, download-favorites, render-clip, recut, favorite, rename, derive, reorder, add-marker, split-clip, snap-to-beat, style, export, export-preset, upload-social, publish, schedule-batch, clip-overlays GET+POST, track GET+POST+DELETE+auto+auto/status, subject-signature GET+POST+DELETE, history GET+DELETE, exports listing+reveal+copy-to+delete, progress SSE, clip-filmstrip. `_append_to_history` stamps user_id, `/api/history` filtert. 38 legacy entries hebben `user_id=None` → onzichtbaar voor iedereen (private by default). (2) **Frontend `withAuth(url)` helper** in `static/index.html` vlak voor `api()`: voegt `?token=<JWT>` aan media-URLs die geen Bearer-header kunnen meesturen. 10+ call-sites gepatcht: thumbnail (3x), filmstrip (3x), clip src (3x), source src, spectrogram, progress SSE. Download-knoppen (`bindDl`) kregen Bearer-header in fetch-init. (3) **End-to-end smoketest** via Chrome MCP op Lisa Korver x Hör Berlin (424MB, 55 min, 30 clips): Account A signupen + upload + analyzer (143.6 BPM, key 4B G# major 90% conf) + editor met video playback + Stripe checkout met testkaart 4242 + Stripe portal → werkt allemaal. Account B in nieuwe tab → library 100% leeg, badge FREE, quota 0/2. **20/20 cross-account security tests groen** (Account B's JWT op Account A's job_id geeft 404 op alle endpoints). **Belangrijke Supabase-vondst:** `.test` en `.example` TLDs worden geweigerd, plus Free email rate limit 2/uur blokt 3e signup. Beide opgelost door Sjuul: Email Confirmation UIT gezet in Supabase dashboard → Auth → Sign In/Up. Voor v1.0 weer aanzetten als eigen SMTP gekoppeld is. **Openstaand voor sessie 29:** (a) **.dmg bouwen** via `./build_macos.sh dmg` — installer pipeline uit sessie 27 nog niet getest met de nieuwe sec patches erin. (b) **Landing site live deployen** naar TransIP of Cloudflare Pages (privacy/terms zijn klaar maar niet gepushed). (c) **Beta-onboarding-flyer** met Gatekeeper-instructies (`xattr -dr com.apple.quarantine`). (d) **In-app Send logs knop**. (e) Optioneel cleanup van 38 legacy owner-less jobs. (f) Optioneel NaN BPM display fix in clips header. Backups: `app.py.pre-sessie28.bak`. Begin met opties + aanbeveling, wacht op "ja", dan los werken. Sjuul is niet-technisch — terminal-commando's letterlijk, geen markdown fences, één commando per regel met pad-quotes.

> Plak dit letterlijk in een nieuwe Claude-chat (oude prompt — Sessie 27 afgerond):

Lees /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/HANDOVER.md, in het bijzonder het STATUS-blok "NA SESSIE 27". SESSIE 27 (avond 17 mei 2026) heeft drie blokken werk afgerond: (1) **Installer pipeline werkend** — PyInstaller-spec + launcher.py + entitlements.plist + build_macos.sh in `dj-clip-cutter/`. App bouwt schoon, ffmpeg/ffprobe worden in de bundle gekopieerd, .bak files worden defensief gestript. Browser-fix: `subprocess.run(['open', url])` ipv `webbrowser.open` (laatste werkt niet in gebundelde .app op macOS). Logging naar `~/Library/Application Support/Clip Live/launcher.log`. Verificatie: bundle boot werkt eind-tot-eind, Flask draait op 127.0.0.1:5555, browser opent automatisch, GET / 200. Apple Developer + Windows BEWUST UITGESTELD tot na macOS-beta. (2) **Stripe via edge functions** — `runtime_config.py` hardcodet alleen publieke keys (Supabase URL/anon, Stripe publishable, price IDs); geen secrets in bundle. Twee nieuwe edge functions met JWT-verificatie: `create-checkout-session` en `create-portal-session` in `dj-clip-cutter/supabase/functions/`. `billing.py` heeft fallback: zonder lokale `STRIPE_SECRET_KEY` → edge function call met user's Bearer token. `app.py` geeft de token door bij `/api/billing/start` en `/api/billing/portal`. Deploy via `supabase functions deploy create-checkout-session` en `supabase functions deploy create-portal-session` (zonder --no-verify-jwt; webhook blijft mét --no-verify-jwt). Sjuul heeft 17 mei 's avonds de deploys succesvol gedaan, rebuild bevestigd geen Supabase/Stripe-warnings meer. (3) **Legal hardening** — `landing/privacy.html` + `landing/terms.html` substantieel aangevuld: sub-processors-lijst, AVG-rechten per artikel (15/16/17/18/20/21), retention per data-type (7 jaar voor invoices), CCPA-sectie voor Californische bezoekers (wereldwijde verkoop), force majeure, export controls, assignment, severability, entire agreement, beta-disclaimer. Plus huishouden: 64 .bak files opgeruimd naar `_bak-archive-2026-05-17.tar.gz`, git repo geïnitialiseerd (commit `b000a57`, branch `main`, 63 files baseline, `.env` correct genegeerd). **Openstaand voor sessie 28:** (a) **End-to-end smoketest** — Test 1 (account aanmaken in bundle) was halverwege; Tests 2–5 (upload+drop-detection, clip export, Stripe upgrade flow met testkaart 4242 4242 4242 4242, Stripe portal) nog te doen. Begin hiermee. (b) **.dmg bouwen** voor distributie via `./build_macos.sh dmg`. (c) **Landing site deployen** naar TransIP of Cloudflare Pages (privacy/terms zijn klaar maar nog niet live). (d) **Beta-onboarding-flyer** met Gatekeeper-instructies. (e) **In-app Send logs knop**. Begin met opties + aanbeveling, wacht op "ja", dan los werken. Sjuul is niet-technisch — terminal-commando's letterlijk, geen markdown fences, één commando per regel met pad-quotes.

> Plak dit letterlijk in een nieuwe Claude-chat (oude prompt — Sessie 26):

Lees /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/HANDOVER.md. SESSIE 26 (17 mei 2026) heeft drie dingen afgerond: (1) **Wise bankrekening setup** — Wise Business account actief voor Sjuul Studios (eenmanszaak), BSN gebruikt als fiscaal identificatienummer, Wise Advanced (€60 eenmalig) nodig voor echte IBAN. Wise geeft een Belgisch IBAN (BE); in Stripe daarom "Belgium" als land van bankrekening selecteren (niet Nederland) — dit is legaal en werkt. (2) **Signup wizard fixes** — 4 bugs opgelost in `static/index.html`: progress bar balkjes nu alleen gevuld bij afgeronde stappen (geen half-fill op actieve stap), secties zijn scrollbaar gemaakt (overflow-x:hidden + overflow-y:auto op viewport, position top/left/right zonder bottom op secties, dynamische track-hoogte via requestAnimationFrame), Next-knop hover goud houden door expliciete background in .btn-primary:hover, scroll reset bij elke stap-navigatie. (3) **Stripe betaalflow end-to-end geverifieerd** — test-account test@test.com heeft Pro-abonnement aangemaakt (sub_1TY7LnA5DKhJaSAFEEphH3mZ, cus_UXBj3w9DhPo5Dm), Supabase profiel correct bijgewerkt naar plan:pro via webhook. Volledige keten werkt: Stripe checkout → Supabase Edge Function webhook → profiel update. Server draait op http://127.0.0.1:5555 (herstart via ./start.sh indien nodig). Volgende sessie kan kiezen uit: (a) **Stripe live mode** — overschakelen van test- naar live-keys, live Wise IBAN koppelen, DNS verificatie voor pre-launch, (b) **B3 speed-ramp** (cutter.py: chained setpts+atempo rond drop-positie), (c) **Brand Stack v2** add-ons (end-card / intro-still / lower-third templates), of (d) andere features. Begin met opties + aanbeveling, wacht op "ja", dan los werken.

> Plak dit letterlijk in een nieuwe Claude-chat (NIEUWSTE — Sessie 25 afgerond, met rollback):

Lees /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/HANDOVER.md. SESSIE 25 (12 mei 2026) heeft het B1-deel van optie C **gebouwd en daarna teruggedraaid**. Het beat-pulse preview-effect in de editor was technisch klaar en algoritmisch geverifieerd (synth-beat-grid uit `clip.bpm`+`clip.bar_duration`, bar-accent vuurde correct op `clip.start`, decay 1.000→0.018 binnen één beat-interval, persist in localStorage), maar Sjuul oordeelde dat het geen user-waarde toevoegde en heeft het laten teruggedraaien. `static/index.html` is gerestored vanuit `static/index.html.pre-sessie25.bak`: 574836 bytes, JS syntax-validated, browser-side bevestigd dat alle pulse-markup en -functies weg zijn en bestaande Track/Text/Export-knoppen ongewijzigd werken. **Geen actieve code-wijzigingen uit deze sessie.** B3 speed-ramp is niet aangeraakt. Side-note: Supabase auth bleek deze sessie niet bereikbaar vanaf de server (`ConnectError: nodename nor servname provided`) — DNS/upstream, niet aan onze kant; even checken voor productie. Server draait nog op http://127.0.0.1:5555 (pid 72143). Volgende sessie kan kiezen uit: (a) **B3 speed-ramp** (cutter.py: chained `setpts`+`atempo` rond drop-positie, ramp-curve presets subtle/medium/aggressive, drawtext rebase voor stamps die niet mee-rampen, recut payload + UI — ~2-3u, server-restart nodig), (b) **Stripe live mode + DNS** voor pre-launch infra, (c) **Brand Stack v2** add-ons (end-card / intro-still / lower-third templates), of (d) **B3 face-embedding upgrade** als de position+size heuristiek uit Sessie 24 in productie te zacht blijkt. Begin met opties + aanbeveling, wacht op "ja", dan los werken.

> Plak dit letterlijk in een nieuwe Claude-chat (oude prompt — Sessie 24):

Lees /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/HANDOVER.md. SESSIE 24 (12 mei 2026) heeft optie a (end-to-end test) afgerond op twee verse uploads + drie polish-fixes + volledige optie B (tracking edge cases + DJ-centered preview + subject-signature persistence) uitgevoerd. **Lisa Korver x Hör Berlin** (1u, 444 MB) en **Franky Rizardo Peru Set** (3:54u, 7.8 GB) beiden door volledige pipeline: analyzer → BPM/Key detect → cutting → BPM stamp → manual keyframe tracking → 4-codec export. Lisa: 26 clips in 3 min, BPM 71.8 (later 143.6 na fix 14), key 4B, alle 4 codec-varianten ffprobe-geverifieerd (match h264, h265_vt hevc, h264_vt h264, prores). Franky: 151 drops in 3.5 min analyzer + 2 min proxy cutting, BPM 129.2 correct, key 12A, LARGE_FILE_PIPELINE auto-getriggered (>7200s threshold), lazy `/api/render-clip` levert 1080p L+V in 5s. **Geen blockers** — large-file hang en duplicate clips uit CLAUDE.md beiden NIET gereproduceerd. Plus drie polish-fixes: (14) **BPM half-tempo fix** — `_maybe_double_tempo()` helper in `analyzer.py`: tempo in [60,90) ∧ doubled in [120,180] → verdubbel tempo + densify beat_times via midpoint-insertion. Lisa's 71.8 → 143.6 met internal-consistente bar-grid (bar_duration 3.34→1.67). Stamp toont nu "144 BPM · 4B" in nieuwe job `00abd848`. (15) **Export chevron** — `static/index.html`: 9px tekst-▾ vervangen door 14px SVG left-pointing polyline in amber-2, hover/open transitions. (16) **Playhead draggable + IN-bind** — top van playhead is nu een echt DOM-element `.playhead-knob` met cursor:grab + pointer-events:auto; mousedown enters scrub mode met body.is-scrubbing class. Plus `_editorSnapPlayheadToInIfOutside()` helper die op play-trigger naar `STATE.trim.inSec` springt als currentTime buiten [inSec, outSec) ligt — zowel `editorTogglePlay()` als stage-click roepen 'm aan. Detecteert source-swap mode (S4.2) en gebruikt set-time vs clip-time correct. Backups: `analyzer.py.pre-sessie24.bak`, `static/index.html.pre-sessie24.bak`, `tracking.py.pre-sessie24.bak`, `app.py.pre-sessie24.bak`. Twee server-restarts uitgevoerd via `_restart.sh` (laatste pid 72143). Optie B-resultaten: **B1** stretch+tracking combined geverifieerd op Franky clip 5 (geen fix nodig, bestaande pipeline werkt). **B2** nieuwe "Preview crop" toggle in Track drawer — swap't naar landscape source + dynamische `object-position` via `_trackedObjectPosition()` cover-formule, DJ blijft live centered tijdens playback zonder recut. **B3** subject-signature persistence — pragmatisch alternatief voor face-embedding via `_pick_primary` position+size bias. `/api/job/<job>/subject-signature` GET/POST/DELETE. Lock-row in drawer met "🎯 Subject locked / from clip N · cx X% · cy Y%". Live geverifieerd: signature van Franky clip 1 (cx=52%, cy=55%) → auto-track clip 10 levert avg cx=51%, cy=57% (binnen 2% van locked). **Werk zelfstandig**: Claude in Chrome MCP, test-account `business+wftest17@sjuulstudios.com` / `WatchTest17!`. Server draait. Volgende sessie kan kiezen uit: **optie C** (B1 beat-pulse + B3 speed-ramp uit Sessie 22 deferred — RAF-loop + chained setpts/atempo), **Stripe live mode + DNS** voor pre-launch, **Brand Stack v2** (end-card / intro-still / lower-third templates), of **B3 upgrade** naar echte face-embedding (dlib/OpenCV DNN) als position+size heuristiek in productie te zacht blijkt. Begin met opties + aanbeveling, wacht op "ja", dan los werken.

> Plak dit letterlijk in een nieuwe Claude-chat (oude prompt — voor de volledigheid):

Lees /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/HANDOVER.md. SESSIE 23 (11 mei 2026) heeft de trim/stretch handle UX overhaul gedaan: zeven fixes (F1–F7) op de Sessie-21/22 timeline, plus een `_ffmpeg_has_drawtext()` guard in cutter.py voor builds zonder libfreetype. F1 beefy handles met grip + copper "in-stretch" state; F2 pronounced trim-band met live duration pill; F3 dimmed stretch zones met centered "EXTEND · 60S AVAIL" pills + hatched pattern; F4 video blijft op `/api/source/<job>` na stretch-mouseup (was: jump-to-zero); F5 analyzer-cut markers — dashed pearl ticks op original clip.start/clip.end; F6 mini-map trim-band krijgt zelfde gold-gradient intensity; F7 crosshair cursor + title-tooltip op stretch zones. Plus `_persist_job_snapshot` BPM-merge fix zodat een handmatig gepatched `key`-veld niet wordt overschreven door in-memory state zonder dat veld. Alleen `static/index.html` + paar regels in cutter.py + app.py gewijzigd, geen restart of pip-install nodig. Backup: `static/index.html.pre-sessie23.bak` (540KB → 551KB). Live-test in Chrome geslaagd: drag IN-handle naar -10.88s → `.in-stretch=true`, duration pill 34.2s→45.1s live update, mouseup → video blijft op source-set bij 224.93s, recut levert correct 45s vertical mp4. **Werk zelfstandig**: gebruik Claude in Chrome MCP, test-account `business+wftest17@sjuulstudios.com` / `WatchTest17!`. Server draait al op http://127.0.0.1:5555 in productie-mode (debug=False). Volgende sessie kan kiezen uit: (a) **End-to-end test op een verse upload** — analyzer→detect_key→render→stamp→tracking pipeline op een nieuwe DJ-set in plaats van de pre-SESSIE-22 Ediine; (b) **Tracking edge cases + TR3** — tracking + stretch combined, camera-pan auto-track, multi-clip face-embedding persistence; (c) **B1 beat-pulse + B3 speed-ramp** — afronding van Sessie-22 deferred items; (d) **Stripe live mode + landing-page DNS verificatie** vóór launch; (e) **Brand Stack v2 add-ons** — end-card, intro-still, lower-third template. Begin met opties + aanbeveling, wacht op "ja", dan los werken.

> Plak dit letterlijk in een nieuwe Claude-chat (oude prompt — voor de volledigheid):

Lees /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/HANDOVER.md (begin met de RESTART-CHECKLIST bovenaan — herstart server + pip install fonttools[woff] voor je verdergaat). SESSIE 21 (11 mei 2026) heeft Brand Stack v1 autonoom afgerond: (a) Style Room → Brand Stack rename + nieuwe HTML-secties (palette manager, fonts uploader, logo uploader, identity inputs), (b) brand_kit.json schema-uitbreiding met fonts/palette/logo/caption_presets/handle/tagline, (c) 12 nieuwe API endpoints in `app.py`: `/api/brand-kit/{fonts,logo,presets}` GET/POST/DELETE, `/api/clip-overlays/<job>` GET/POST. Fonts accepteren TTF/OTF native + WOFF/WOFF2 via `fonttools[woff]` (optional dep — server start zonder, WOFF uploads krijgen dan 422 met install-instructie). (d) Editor: nieuwe "Text" tool-btn onder Trim opent rechter-drawer met layer-list, "+ Add text", per-layer editor (textarea, font picker uit Brand Stack + system, palette swatches, size/weight/x/y sliders, show-from/hide-at, animation), live HTML-preview overlay op #ed-video die meebeweegt met playback. Save preset → opslaan in Brand Stack. (e) cutter.py: `_build_text_layer_filters` bouwt drawtext chain met textfile= (bulletproof unicode), font_id lookup naar brand_kit absolute path, fontsize uit size_pct van frame-width, x/y in single-quoted expressions, fade/slide-up animaties via alpha/y-expr, hard cap 8 layers per clip. Logo overlay via filter_complex met `movie=` source filter (geen extra `-i`). `process_clips` + `recut_clip` (en hun callers `_process_single_clip`, `cut_clip_landscape/_vertical`) lezen `text_overlays.json` + `brand_kit.json` per render. **HERSTART NODIG** — backend wijzigingen pikken niet auto op. Backups: `app.py.pre-sessie21.bak` (162KB → 181KB), `cutter.py.pre-sessie21.bak` (47KB → 65KB), `static/index.html.pre-sessie21.bak` (417KB → 467KB). Frontend live geverifieerd via Chrome MCP (Brand Stack page rendert volledig, Text-panel opent, "+Add text" creëert layer met "Caption here" live-preview op (50%,80%)). Backend nog niet live getest — wacht op restart. Volgende sessie kan kiezen uit: (a) End-to-end live test van Brand Stack (upload font + logo, render clip met tekst, verifieer mp4); (b) Brand Stack v2: BPM/Key stamp, end-card, intro-still, lower-third — DJ-specifieke add-ons; (c) export_with_preset / split_clip_at ook tekst-aware maken (nu alleen recut + initial-render dragen tekst); (d) Stripe live mode + DNS — pre-launch. **Werk zelfstandig**: gebruik Claude in Chrome MCP, test-account `business+wftest17@sjuulstudios.com` / `WatchTest17!`. Begin met opties + aanbeveling, wacht op "ja", dan los werken.

---

## SESSIE 26 — Wise setup + Signup wizard fixes + Stripe betaalflow verificatie (2026-05-17)

### 1 — Wise bankrekening setup

- Wise Business account actief onder naam Sjuul Studios (eenmanszaak)
- Wise Advanced (€60 eenmalig) nodig voor echte IBAN + account details
- Fiscaal identificatienummer = BSN (niet BTW-nummer of KVK)
- Wise geeft een **Belgisch IBAN (BE)** — Wise is in België geregistreerd
- In Stripe → Settings → Bank accounts: "Belgium" als land selecteren (niet NL), anders foutmelding "country NL does not match BE"
- Dit is legaal: bedrijfslocatie (NL) en bankrekening-land (BE) mogen verschillen

### 2 — Signup wizard fixes (`static/index.html`)

Vier bugs opgelost:

| Bug | Oorzaak | Fix |
|---|---|---|
| Progress bar balkjes half gevuld op actieve stap | `is-current::after { scaleX(.5) }` | CSS-regel verwijderd; `is-current` class niet meer gezet in JS |
| Next-knop verdwijnt op stap 2 (reasons) | `position:absolute;inset:0` forceert 340px hoogte, content overflowt | Viewport `overflow-x:hidden; overflow-y:auto; max-height:480px`; secties `top/left/right` zonder `bottom` |
| Velden verdwijnen op stap 3 (who you are) | Zelfde overflow-oorzaak | Zelfde fix + scroll reset naar top bij elke stap-navigatie |
| Next-knop donker/onleesbaar bij hover | `.btn:hover` overschreef gouden achtergrond van `.btn-primary` | `.btn-primary:hover` geeft nu expliciet `background` + `border-color` mee |
| Email-veld ontbreekt op stap 4 | Sectie startte niet bovenaan door overflow/scroll-state | Opgelost door scroll reset + dynamische track-hoogte via `requestAnimationFrame` |

### 3 — Stripe betaalflow end-to-end geverifieerd (testmodus)

- Test-account `test@test.com` (artist: Eddy) aangemaakt via signup wizard
- Pro-abonnement afgerond met testkaartnummer 4242 4242 4242 4242
- Stripe: `sub_1TY7LnA5DKhJaSAFEEphH3mZ`, status `active`, plan Pro (`price_1TUoYNA5DKhJaSAF6xynooY9`)
- Supabase profiel: `plan: pro`, `stripe_customer_id: cus_UXBj3w9DhPo5Dm`, `stripe_subscription_id` correct opgeslagen
- Webhook (Supabase Edge Function) heeft correct gefired na checkout
- Volledige keten bevestigd: Stripe checkout → webhook → Supabase profiel update ✅

---

## SESSIE 24 — End-to-end pipeline test + 3 polish-fixes (2026-05-12)

Optie a (end-to-end test op verse upload) afgerond op TWEE sets — daarna drie polish-fixes voor Sjuul. Volledige bevindingen in **`SESSIE-24-FINDINGS.md`** in project-root.

### Optie a — end-to-end test op verse uploads

| Set | Duur | Pipeline | Outcome |
|---|---|---|---|
| Lisa Korver x Hör Berlin | 1u, 444 MB | Eager 1080p cuts | 26 drops in 3 min, 26×2=52 files, alle 4 codec-exports geverifieerd |
| Franky Rizardo Peru Set | 3:54u, 7.8 GB | LARGE_FILE_PIPELINE (>7200s) | 151 drops in 3.5 min analyzer + 2 min proxy cutting; lazy 1080p L+V in 5s/clip |

**Pipeline-componenten met groen vinkje** (volledige tabel in SESSIE-24-FINDINGS.md):
- `/api/upload-local` no-copy register ✓
- Analyzer drop-detection (unieke clips, geen duplicaten) ✓
- `detect_musical_key()` Camelot output ✓
- Cutting parallel ✓
- LARGE_FILE_PIPELINE auto-trigger ✓
- `/api/render-clip` lazy full-quality ✓
- BPM/Key stamp drawtext-overlay ✓
- `/api/track/<job>/<clip>` save+load ✓
- `recut_clip` met keyframes-lookup (pan-effect visueel correct) ✓
- 4 codec-varianten (match/h265_vt/h264_vt/prores) ffprobe-geverifieerd ✓

**Bekende issues uit CLAUDE.md die NIET zijn opgetreden:**
- Duplicate clips bug (alle 26 + 151 clips unieke start/end/peak)
- Large-file pipeline hang (3:54 u liep door)
- UI regressie (geen layout-breaks)

### Drie polish-fixes na optie a

#### Fix 14 — BPM half-tempo doubling (`analyzer.py`)

`_maybe_double_tempo()` helper toegevoegd direct boven `detect_bpm`. Heuristiek:

```
if 60 <= tempo < 90 AND 120 <= 2*tempo <= 180:
    doubled = tempo * 2
    densified_beats = insert midpoints between every adjacent beat
    return doubled, densified_beats, was_doubled=True
```

Conservatief gekozen range — nooit up-temposen van legit downtempo / hip-hop / dub (60-100 BPM, blijven). Sjuul's product is dance-muziek, daar zit tempo nooit onder 100.

Densification (midpoint-insert) houdt `bar_duration` / `bar_times` / downstream bar-snapping intern consistent. Anders zou de BPM stamp "144" zeggen maar de bar-aligned cutter nog op 72 BPM grid werken — verwarrend.

Nieuwe return-fields: `bpm_raw` (origineel librosa output, alleen gezet bij doubling), `bpm_doubled` (bool).

Edge-case suite (8 cases) standalone unit-getest:
- 89 → 178 (doubles), 90 → 90 (boundary, no double)
- 75 → 150 (doubles), 50 → 50 (doubles to 100, below dance, NO double)
- 95 → 95 (in range, NO double), 140 → 140 (in range, NO)
- 60 → 120 (boundary lower, doubles), 65 → 130 (doubles)

Live verificatie op verse Lisa-job `00abd848`: bpm 71.8 → **143.6**, bpm_doubled=true, bar_duration 3.34→1.67. Stamp in rendered clip 1 vertical toont "**144 BPM · 4B**" — visueel bevestigd via frame-extract. Franky `94d6c9c7` blijft 129.2 BPM — heuristiek triggert niet.

Side-effect: 30 clips ipv 26 op dezelfde source — finere bar-grid produceert meer bar-aligned drop windows; clip-duur 30s→15s want 9 bars op 144 BPM is half zo lang als op 72.

Backup: `analyzer.py.pre-sessie24.bak`.

#### Fix 15 — Export chevron (`static/index.html`)

Het was: `<span class="caret">▾</span>` — 9px tekst-character met opacity 0.7. Te subtiel voor first-time users. Plus pijl wees naar beneden terwijl de dropdown naar LINKS uitvouwt (`right: calc(100% + 8px)`).

Nu: inline SVG polyline (left-chevron) in 14px, color `var(--amber-2)`, hover/open-state animaties (translateX(-2px) tijdens open richting menu). Hit-area expansion via ::after pseudo zodat makkelijker te klikken op trackpad.

DOM-verified: `<svg viewBox="0 0 24 24"><polyline points="15 6 9 12 15 18"></polyline></svg>` met computed color `rgb(244, 207, 138)`.

#### Fix 16 — Playhead draggable + start-at-IN (`static/index.html`)

Twee aspecten:

**(a) Knob draggable.** De `::before` pseudo-element die de gouden driehoek tekende is vervangen door een echt DOM-element `.playhead-knob` (id `tl-playhead-knob`). `pointer-events:auto`, `cursor:grab`, hit-area expansion via ::after. `bindPlayheadScrub()` registreert mousedown→mousemove→mouseup lifecycle:
- mousedown enters scrub mode (body.is-scrubbing class, video pauseert, knob.is-grabbing)
- mousemove update v.currentTime via dezelfde `pxToVirtSec`-conversie als trim-handles
- mouseup cleart drag state + classes
- Dubbelklik-shortcut springt naar inSec ("back to start")

**(b) Play-restart bij IN-handle.** Nieuwe helper `_editorSnapPlayheadToInIfOutside()`. Bij play-trigger (`editorTogglePlay()` of stage-click): als v.currentTime buiten [inSec, outSec) ligt → seek naar inSec voor `v.play()`. Detecteert source-swap mode (S4.2) door inspectie van `v.src` en gebruikt set-time (`clipStart + inSec`) ipv clip-time daar.

Binnen het bereik blijft currentTime ongemoeid — user's eigen scrub-positie wordt gerespecteerd.

Live getest via simulated MouseEvents in MCP-tab (zie SESSIE-24-FINDINGS.md "Addendum"):
- Scrub door tracks → currentTime updates correct + clamps aan duration
- v.currentTime=0 + trim.inSec=5 + `editorTogglePlay()` → springt naar 5, dan v.play() → na 300ms staat hij op 5.22s ✓

Backup: `static/index.html.pre-sessie24.bak`.

### Server restart

Voor fix 14 wel — analyzer.py change. Uitgevoerd via `_restart.sh` osascript-bridge (pid 70201). Voor 15+16 alleen browser hard-refresh nodig.

### Optie B (tracking edge cases + DJ-centered preview) — VOLLEDIG AFGEROND in zelfde sessie (12 mei)

Volledige details in `SESSIE-24-FINDINGS.md` (Addendum 2). Kort:

- **B1 — Stretch + tracking combined**: getest op Franky clip 5 (IN-stretch -3s + 3 manual keyframes). Recut levert 19.72s output met correcte pan inclusief gestrechte zone. PASS — bestaande pipeline werkt, geen fix nodig.

- **B2 — Auto-track live preview**: nieuwe "Preview crop" toggle in Track drawer. ON → swap `<video>.src` naar landscape source + dynamische `object-position` via `_trackedObjectPosition()` formule (cover-cropping math die werkt voor alle stage-aspecten). DJ blijft visueel centered tijdens playback zonder recut. Sample t=1.25/5/10/15 toont object-position 14.52%→55.31%→64.96%→55.55%. Badge "PREVIEW · DJ-tracked crop" linksboven. Toggle OFF → vertical restore + state reset.

- **B3 — Subject-signature persistence**: pragmatisch alternatief voor face-embedding (dlib/OpenCV DNN) gekozen om heavy deps te vermijden. `_pick_primary()` in tracking.py kreeg derde param `prior_signature: {cx,cy,w,h}` die first-frame position+size bias toepast. `compute_subject_signature(keyframes)` helper. Nieuwe `/api/job/<job>/subject-signature` endpoints (GET/POST/DELETE). Auto-track endpoint leest job-level signature, geeft door, en bij eerste succesvolle run wordt 'm auto-gepersist. Frontend: lock-row in Track drawer met "🎯 Subject locked / from clip N · cx X% · cy Y%" + Clear + "Lock to this clip" buttons. Live getest: signature van Franky clip 1 (cx=52%, cy=55%) → auto-track clip 10 levert avg cx=51%, cy=57% (binnen 2% van locked) terwijl zonder bias andere crowd-members gekozen zouden kunnen worden.

Backups: `tracking.py.pre-sessie24.bak`, `app.py.pre-sessie24.bak`. Server-restart uitgevoerd (pid 72143).

### Volgende sessie — wat is er over?

- **Optie C** (B1 beat-pulse + B3 speed-ramp) — Sessie 22 deferred items. RAF-loop synced naar bar_times voor beat-pulse, chained setpts/atempo orchestration in ffmpeg voor speed-ramp. ~2-3u.
- **Stripe live mode + landing-page DNS** — pre-launch infra.
- **Brand Stack v2** — end-card, intro-still, lower-third templates.
- **B3 upgrade naar echte face-embedding** als de position+size heuristiek in productie te zacht blijkt (kan dan dlib of OpenCV DNN integreren).

---

## SESSIE 23 — Trim/stretch handle redesign + ffmpeg-drawtext guard (2026-05-11)

Visual + interaction overhaul van de Sessie-21/22 trim-UX, plus een graceful-degradation guard voor ffmpeg-builds zonder libfreetype. Alleen `static/index.html` aangeraakt + één klein cutter.py + app.py snippet voor de drawtext-probe + capabilities surface (al opgenomen in SESSIE 22 hot-fix). Geen restart vereist voor F1-F7 — Sjuul reloadt browser, klaar.

### Online research vooraf

Premiere / DaVinci / FCP / CapCut conventions gescand:
- **Trim handles zitten op de RAND van de clip, met grip-affordances (grooves/dots) + hit-area >> visuele area** (pro-conventie).
- **Cursor verandert context-sensitive** bij hover op handle / stretch zone.
- **Selected range MUST stand out** met duidelijke gouden/blauwe gradient band.
- **Apple/Premiere Rate-Stretch tool is speed-change, niet wat wij doen** — onze "stretch" is feitelijk "extended trim beyond analyzer-cut". Term EXTEND past beter dan STRETCH.

### Bugs gevonden tijdens debug (en gefixt)

1. **Video-jump na stretch-mouseup**: `v.currentTime=0` na release sloeg de gebruiker terug naar het eerste frame, terwijl ze net naar t=229s gedragged hadden. Verwarrend.
2. **Handles waren 14px goud lijntjes zonder grip** — niet vindbaar voor first-time users.
3. **Geen visueel onderscheid tussen analyzer-cut en stretch-zones** — filmstrip + waveform spanden uniform de hele vDur, gebruiker wist niet waar de analyzer-grens lag.
4. **Trim-band was bijna onzichtbaar** (0.08 opacity gold) — geen duidelijke "selected range" signaal.
5. **Stretch-zone labels piepklein in de hoek** ("STRETCH ←60s") in plaats van uitnodigend pill in het midden.
6. **Mini-map trim-band onleesbaar** — zelfde lage opacity.

### Wat ik gefixt heb

| Fix | Wat het doet | Bewijs in live test |
|---|---|---|
| **F1** Beefy handles | Spine 14→6px + 22px hit-area, three-line grip patroon, drop-shadow op hover, `.in-stretch` class flipt spine van gold→copper bij drag past edge | Class-toggle gevalideerd via JS in Chrome: `inStretchOnIn: true` bij `inSec=-10.88` |
| **F2** Pronounced trim-band | Opacity 0.08→0.22 met top/bottom borders, inset glow, floating duration pill | "45.1s" pill live update tijdens drag bevestigd |
| **F3** Dim stretch zones + EXTEND pills | `backdrop-filter: brightness(0.5) saturate(0.55)` op de zones + hatched pattern, centered pill "← EXTEND · 60S AVAIL" | Visueel verschil in screenshot duidelijk: clip-area heldergouden, stretch zones gedimd |
| **F4** Keep source-set video after stretch-release | Was: clip-cache restore + currentTime=0. Nu: blijf op `/api/source/<job>`, seek naar `clip.start + new_inSec` | `videoSrcType: "source-set"` + `videoTime: 224.93` na mouseup bevestigd — geen jump-to-zero meer |
| **F5** Analyzer-cut markers | Twee dunne dashed lijntjes op original `clip.start` / `clip.end` posities, met "analyzer cut" labels die fade-in op timeline-hover | Visueel zichtbaar in screenshot — pearl-grey ticks bij 13s en 20s |
| **F6** Mini-map trim-band rendering | Opacity 0.12→0.28 met gold-gradient, borders, inset glow — matched main band | Mini-map duidelijk band zichtbaar in alle screenshots |
| **F7** Cursor + tooltip system | `cursor: crosshair` op stretch zones, `title` attribute met instructie ("Drag the gold IN handle leftward to include up to 60s before the analyzer-detected start") | Visible in DOM inspection |

### Bonus — `_ffmpeg_has_drawtext` guard (cutter.py)

Tijdens debug ontdekt dat Sjuul's homebrew ffmpeg geen `libfreetype` had → drawtext filter ontbrak → BPM stamp + text-overlays crashten met "No such filter". Toegevoegd:
- `_ffmpeg_has_drawtext()` probe (cached) in cutter.py
- Graceful skip in `_build_text_layer_filters`, `_build_bpm_stamp_filter`, `_build_overlay_filter`
- `/api/capabilities` surface `ffmpeg.drawtext` boolean
- Sjuul heeft `homebrew-ffmpeg/ffmpeg/ffmpeg` geïnstalleerd → drawtext nu beschikbaar, BPM stamp werkt live ("129 BPM · 7A" renderde in TR corner van vertical export).

Plus mini fix in `_persist_job_snapshot`: BPM-dict merge-preserve zodat een handmatig gepatched `key` veld niet wordt overschreven door in-memory state zonder dat veld (relevant voor pre-SESSIE-22 jobs).

### Verificatie

- `node --check` extracted JS → OK
- `python3 -c "import ast; ast.parse(open('cutter.py').read())"` → OK
- DOM-id scan: 261 unique, 0 duplicates. Nieuwe ids: `tl-trim-band-label`, `tl-anal-mark-l`, `tl-anal-mark-r`
- File-size: `static/index.html` 540.412 → 551.120 (+10.708 bytes voor het hele redesign — bescheiden)

### Backup

```
static/index.html.pre-sessie23.bak  (540.412 bytes)
```

### Live test results (Chrome MCP, post-deps-install + post-homebrew-ffmpeg-rebuild)

- Volledige stretch-drag flow: IN handle 80px naar links → `inSec=-10.72s` → `.in-stretch` class actief → "45.0s" duration pill → bandWidth=29.25%
- Mouseup → video blijft op source-set, `currentTime=224.93s` (geen jump-to-zero)
- Visuele screenshots bevestigen alle 7 fixes (zie sessie-conversatie)
- Trim + recut export: 34.23s vertical mp4 (matcht expected stretched range)

### VOLGENDE SESSIE — kies één

1. **Tracking edge cases** — tracking + stretch combined, camera-pan auto-track, multi-clip face-embedding persistence (TR3 uit eerder plan).
2. **B1 beat-pulse + B3 speed-ramp** — afronding van Sessie 22 deferred items.
3. **End-to-end test op een verse upload** — zodat we de full analyzer→detect_key→render→stamp pipeline op een nieuwe set zien doorlopen (huidige Ediine set is pre-SESSIE-22).
4. **Stripe live mode + landing-page DNS** — pre-launch.

---

## SESSIE 22 — Polish + tracking + signup wizard (2026-05-11, uitgevoerd)

Zes blokken (A, E, Q, B, C, D) uitgevoerd in één autonome sessie. Backend + frontend allebei aangeraakt. Backups + ID-uniciteit verifieerd; live test wacht op restart van de server. Debug-mode tijdelijk aan tijdens de sessie, teruggezet op `False`.

### A — Text-panel polish (Sessie 21 follow-up)

`static/index.html` — CSS + HTML + JS, alleen aangeraakt in `.ed-tx-*` scope.

- `::placeholder { color: var(--ink-4); font-style: italic }` — empty textarea = grijs italic.
- `.ed-tx-field label` kleur van `var(--ink-3)` → `var(--amber-2)` met letter-spacing en weight bump (10.5px, 500). Veel beter leesbaar.
- Drag-on-preview: `mousedown` → `mousemove` → live update `x_pct`/`y_pct` met clamp 0..100 + slider-readout sync. Shift held bij drag-start = constrain naar dominante as.
- Corner-resize-handles (TL/TR/BL/BR) op de actieve layer. Drag diagonal → diagonal scale van `size_pct` (2..40). Mid-handles overgeslagen — geen non-uniform stretch op tekst.
- Alignment buttons in Premiere-stijl SVG (6 stuks, 3 horizontal + 3 vertical) onder X/Y sliders. Klik snapt naar 5/50/95% met padding tegen edge-collision.
- `_etxDrag` global state, `_onEditorTextOverlayPointerDown`/`Move`/`Up` handlers — alle bindings idempotent.

### E — Export settings dropdowns + (deferred) verification

`static/index.html` — nieuwe modal `#export-settings-modal` (reuses .aspect-back/.aspect-card patroon) met:

- Codec dropdown: Match source / H.265 HW / H.264 HW / ProRes 422
- Frame rate dropdown: Match source / 24 / 30 / 60
- Resolution dropdown: Source / 1080×1920 / 4K 9:16 / 1920×1080 / 4K 16:9 / 1080×1080
- Inline note die wisselt op codec-keuze ("Match source stream-copies…" / "ProRes 422 produces .mov…" etc.)
- LocalStorage onthoudt laatste keuze in `clipLive.exportSettings`.

`pickExportSettings(label)` returnt Promise<{codec, fps, resolution}>; `startExport()` roept 'm aan vóór de folder-picker en plumbst de waarden naar `/api/export/<job>` body. Backend route was al klaar (sinds SESSIE 4-ish): `_run_export_job` → `export_clip_with_settings(codec=, fps=, resolution=)` → ffmpeg switch op `EXPORT_CODEC_MAP`.

**Verification (echte ffprobe-run) was deferred** omdat ik de modal niet live kon klikken zonder server-restart. Plan voor de volgende sessie: render dezelfde clip 4× met elke codec-keuze, `ffprobe -show_streams` controleren dat codec_name daadwerkelijk verschilt (h264 / hevc / prores).

### Q — Pre-signup questionnaire wizard

**Supabase migration** uitgevoerd via MCP `apply_migration` op project `lbabsffxefkrxwzkbzar`:

```sql
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS referral_source     text,
  ADD COLUMN IF NOT EXISTS referral_other      text,
  ADD COLUMN IF NOT EXISTS use_reasons         jsonb DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS artist_name         text,
  ADD COLUMN IF NOT EXISTS full_name           text,
  ADD COLUMN IF NOT EXISTS instagram_url       text,
  ADD COLUMN IF NOT EXISTS tiktok_url          text,
  ADD COLUMN IF NOT EXISTS streaming_url       text,
  ADD COLUMN IF NOT EXISTS intake_completed_at timestamptz;
CREATE INDEX IF NOT EXISTS idx_profiles_referral_source ON public.profiles (referral_source) WHERE referral_source IS NOT NULL;
```

**Backend** (`auth.py` + `app.py`):
- `signup(email, password, intake=None)` — na succesvolle `auth.sign_up` patcht service_role-client de profile-row met whitelisted intake-fields. Soft-fail op patch-error (account werkt nog steeds).
- `_persist_intake(user_id, intake)` — accepteert alleen geldige slugs voor `referral_source` + `use_reasons`; clip text-lengtes; sets `intake_completed_at`.
- `/api/auth/signup` accepteert `intake` dict in body. Valideert `artist_name`/`full_name`/`referral_source` als required.

**Frontend** (`static/index.html`):
- Nieuwe `.auth-wizard` als alternatief voor `.auth-form` — toggle via `setAuthTab('signup')`.
- 4 secties + 1 success-splash. CSS `.wiz-progress` 4-segment bar met scaleX-transitie + `.is-done`/`.is-current` states. Smooth slide-left/right via `transform:translateX` op `.wiz-section`.
- Sectie 1: 9 single-select bubbles + Other-input met max-height transition.
- Sectie 2: 4 multi-select bubbles (col-layout omdat antwoorden lang zijn).
- Sectie 3: Artist*/Full*/IG/TT/Streaming inputs met required-field highlight bij Next-zonder-invul.
- Sectie 4: email + password + confirm. Live `wiz-pass-match` indicator (✓ groen / ✗ rood). Password ≥ 8 chars validatie.
- Splash: "Let's clip some live DJ-sets!" met scale-pop animatie, daarna 900ms timer → `hideAuthOverlay()` + `postLoginBoot()`.
- State persist in `sessionStorage.clipLive.wizardState` zodat refresh halverwege niets wist; cleared op success.

### B — BPM/Key stamp (B2 only — B1 + B3 deferred)

**Analyzer** (`analyzer.py`):
- `detect_musical_key(audio_path=None, sr, y_audio=None)` via `librosa.feature.chroma_cqt` + Krumhansl-Schmuckler templates voor major en minor. Output: `{tonic, mode, camelot, confidence}`.
- `_KEY_PROFILE_MAJOR`/`_KEY_PROFILE_MINOR` constants, `_CAMELOT_MAJOR`/`_CAMELOT_MINOR` lookups.
- `detect_bpm()` roept `detect_musical_key()` aan op dezelfde geladen audio-window (geen dubbele IO) en voegt `key`, `key_tonic`, `key_mode`, `key_confidence` toe aan zijn return.

**Cutter** (`cutter.py`):
- `_build_bpm_stamp_filter(bpm_cfg, clip_data, target_w, target_h, brand_fonts, system_font)` → drawtext filter string met `129 BPM · 7A` formattering (configurabele via `format`: bpm/key/bpm_key), corner positioning, optional brand-font, box met 0.45 alpha.
- `_build_clip_data_for_stamp(clip, job_bpm_info)` — minimale dict met clip-level vs set-level fallback.
- `_load_set_bpm_info_for_job(job_id, output_dir)` — leest `output/<job>/job.json` voor set-level BPM+key.
- `_maybe_compose_brand_vf` accepteert nu `bpm_cfg` + `clip_data`; appended na drawtext-layers, vóór logo-overlay.
- Plumbed via `_process_single_clip` + `recut_clip` (en hun retry-paths).
- `_load_brand_assets_for_job` returnt nu 4-tuple inclusief `bpm_cfg`.

**Frontend** (`static/index.html`):
- Nieuwe Brand Stack sectie "BPM & Key stamp" met On/Off toggle, corner-picker (4 buttons, reuse `.bs-corner-pick` styling), format-dropdown.
- `_renderBrandBpmStamp(cfg)`, `brandBpmStampUpdate(patch)` — partial update via `/api/brand-kit` POST.

**B1 beat-pulse en B3 speed-ramp:** **deferred naar v2**. Reden: beat-pulse vereist een runtime RAF-loop met beat-grid sync die conflicteert met het bestaande playback-state-management, en speed-ramp vereist gekoppelde setpts/atempo orchestration (atempo's 0.5..2.0 cap = chained filter, plus rebase van alle volgende `t`-expressions in drawtext). Beide significant niet-triviaal — losse sessie waardig.

### C — TR1 Manual keyframe tracking

**Backend** (`app.py`):
- `/api/track/<job_id>/<clip_idx>` GET/POST/DELETE — persist in `output/<job>/tracking/clip_NNN.json`.
- `_validate_keyframes_payload(raw)` — clamp 0..100, source-whitelist (`manual`/`auto`/`smoothed`), sort by time, cap 50 keyframes.

**Cutter** (`cutter.py`):
- `_load_keyframes_for_clip(job_id, output_dir, clip_index)` — leest tracking-JSON.
- `_build_tracked_vertical_crop(keyframes, src_w, src_h)` — bouwt dynamic `crop` filter met geneste `if(lt(t,T_n), val, …)` expressie voor x/y; single-quoted zodat commas niet als filter-separators worden geparsed; ≤8 keyframes lerp, daarboven cap met warning.
- `_build_keyframe_lerp_exprs(kfs)` — recursive nested if() build voor x én y axes.
- `_build_vertical_cmd` accepteert `track_keyframes`; vervangt static centre-crop door tracked-crop wanneer aanwezig. Scale+pad steps blijven hetzelfde → output blijft 1080×1920.
- Plumbed via `cut_clip_vertical` + `_process_single_clip` + `recut_clip` (en retry-paths).

**Frontend** (`static/index.html`):
- Track tool-btn in editor right-rail (target-icoon SVG) tussen Text en Export.
- `.ed-track-drawer` (reuse `.ed-text-drawer` styling) met layer-list, "+ Add keyframe at playhead", Clear-all, Auto-track, Done.
- `.ed-track-overlay-root` binnen `#ed-stage` met `.ed-track-box` — gold dashed outline, draggable + 4-corner resizable. Live interpolated positie via `timeupdate` listener.
- State in `STATE.editorTrack = {keyframes, selectedIdx, jobId, clipIdx}`.
- `_interpKeyframeAtTime(t)` — linear interp voor live preview (matcht cutter's expressie 1:1).
- `editorTrackAddKeyframe()` — neemt interpolated positie als startpunt voor nieuwe KF, sort by time, auto-persist.
- `editorTrackSelect(idx)` — seek video naar KF.t en repaint box.
- Drawer-switching: opening de Track-drawer sluit de Text-drawer (en vice versa) — slechts één drawer tegelijk.

### D — TR2 Hybride auto-tracking (Apple Vision + YOLO + HOG)

**Nieuwe module** `tracking.py` (22 KB):
- Try/except optional imports voor 3 engines — `from Vision import …`, `from ultralytics import YOLO`, `import cv2`. Telemetry hard-killed via env-vars **vóór** `from ultralytics import YOLO`:
  ```python
  os.environ.setdefault('YOLO_OFFLINE', 'True')
  os.environ.setdefault('NO_ALBUMENTATIONS_UPDATE', '1')
  ```
  Plus `settings.update({'sync': False, 'api_key': ''})` na import.
- `engines_available()` returnt dict zodat de UI weet welke engines beschikbaar zijn.
- `_extract_frames(video_path, start, duration, fps, out_dir)` — ffmpeg snapshot @ 4 FPS naar temp-dir.
- `_frame_brightness(path)` — cv2-based mean luminance, gebruikt voor lowlight-routing.
- `_vision_detect(frame_path)` — Apple Vision via PyObjC: `VNDetectHumanRectanglesRequest` met `VNImageRequestHandler.alloc().initWithURL_options_`. Converts Vision's BOTTOM-left bbox naar TOP-left.
- `_yolo_detect(frame_path)` — Ultralytics YOLOv8n, person-class only (COCO id 0). Pinned to MPS op Apple Silicon. Weights lokaal in `models/yolov8n.pt` (download bij eerste run via ultralytics).
- `_hog_detect(frame_path)` — last-resort opencv `HOGDescriptor_getDefaultPeopleDetector`. Geen externe dep.
- `_pick_primary(detections, prev_center)` — area × √conf scoring met optional spatial-continuity penalty.
- `_smooth_track(track, alpha=0.4)` — exponential moving average op cx/cy/w/h.
- `_downsample_keyframes(track, max_count=20)` — even-spaced downsample, preserves first+last.
- `detect_track(video_path, start, duration, fps, ...)` — orchestrator. Per frame:
  1. Brightness check
  2. Apple Vision primary call
  3. Als Vision-confidence < 0.5 + lowlight → escalate to YOLO; gebruik YOLO als 'ie hoger scoort
  4. Als Vision 3+ opeenvolgende frames leeg returnt → escalate to YOLO
  5. Als Vision + YOLO niet beschikbaar → HOG last-resort
  6. Als niks werkt → hold previous box (gap-fill)
  - Tracks `engines_used` set + `fallback_count` voor UI-rapportering.
- `run_auto_track_async(key, video_path, start, duration, ...)` — fire-and-forget background thread met progress callback. State in module-level `_AUTO_STATE` dict (per `<job>/<clip>` key).

**Backend** (`app.py`):
- Import `tracking` als optional module (try/except — server start ook als deps niet geïnstalleerd).
- `POST /api/track/<job>/<clip>/auto` — kick off async run. Returnt 422 als geen engine beschikbaar.
- `GET /api/track/<job>/<clip>/auto/status` — poll progress + result. Op `done=True` persist resultaat naar tracking JSON-file (zodat C en D dezelfde UI delen).
- `_resolve_clip_source_for_tracking(job, clip_idx)` — vindt source video + start/end uit job snapshot.

**Frontend** (al toegevoegd in C-blok):
- "Auto-track" knop in Track-drawer → `editorTrackAutoStart()` → POST `/auto` → `_pollAutoTrackStatus()` met progress-string + result-rendering.
- Status-strip onderaan drawer met `.is-running` / `.is-ok` / `.is-bad` kleur-states.

**Privacy garanties (zoals beloofd):**
- Geen video/frames raken ooit een externe server bij Apple Vision (lokale framework).
- YOLO inference run lokaal; weights worden 1× gedownload van GitHub releases (~5 MB), geverifieerd via Ultralytics' eigen hash-check.
- Telemetry uitgeschakeld via env-vars en `settings.update`.
- User-zichtbaarheid: drawer-status toont "Generated N keyframes (engine = …, fallback_used = …)" zodat je altijd weet welke engine welke keyframes leverde.

### Code-stats

- `app.py`        180.572 → 191.356  (+10.784)
- `cutter.py`      64.597 →  76.741  (+12.144)
- `analyzer.py`    40.420 →  45.980  (+ 5.560)
- `auth.py`         7.357 →  10.234  (+ 2.877)
- `tracking.py`    NIEUW  →  22.228
- `static/index.html` 467.231 → 540.241 (+73.010)
- Unique DOM ids: 258 (0 duplicates)
- Python ast.parse: app.py + cutter.py + tracking.py + analyzer.py + auth.py — alle OK
- `node --check` op extracted inline JS — OK

### Backups (SESSIE 22)

```
app.py.pre-sessie22.bak             (180.736 bytes)
cutter.py.pre-sessie22.bak          ( 64.597 bytes)
static/index.html.pre-sessie22.bak  (467.231 bytes)
analyzer.py.pre-sessie22.bak        ( 40.420 bytes)
auth.py.pre-sessie22.bak            (  7.357 bytes)
```

### Live test resultaten (post-deps-install)

Uitgevoerd 2026-05-11 16:00 via Chrome MCP op PRO test-account `business+wftest17@sjuulstudios.com`:

| Blok | Status | Notes |
|---|---|---|
| **A** Text-panel polish | ✅ Volledig | Drag-on-preview slaagde 50%→30%×30% (sliders gesynchroniseerd). Alle 6 alignment-buttons snappen correct (5/50/95 voor x én y). Corner-resize (BR drag +120px) liet size_pct groeien 6 → 18.5%. Vibrant amber labels (`rgb(244,207,138)`). |
| **E** Export settings | ✅ Volledig | Modal rendert met 3 dropdowns. ffprobe na live render bewijst codec-switch: `h264_vt` → `codec_name=h264, codec_tag=avc1`, `h265_vt` → `codec_name=hevc, codec_tag=hvc1`. Zelfde resolutie + fps; H.265 is 7% kleiner zoals verwacht. |
| **Q** Signup wizard | ✅ Volledig | Door alle 4 secties + back-button + password-match indicator (✓/✗) + required-field validatie. Submit niet uitgevoerd om geen testaccount aan te maken. |
| **B** BPM/Key stamp | ⚠️ Code-OK, runtime-blocked | Backend + UI werken; Brand Stack toggle slaat config op. **Render blokkeert op `drawtext` filter die ontbreekt in homebrew-ffmpeg.** Guard toegevoegd aan `cutter.py` + capabilities endpoint; vereist herstart om live te zijn. Fix: rebuild ffmpeg met `--with-freetype`. |
| **C** Manual tracking | ✅ Volledig | 3-keyframes-POST + GET geverifieerd. Recut van clip 1 met tracking-JSON levert vertical 1080×1920 H.264 (4.1 MB, 21.7s) — dynamic crop filter actief. Track-drawer + gold draggable box op preview gerendered. |
| **D** Auto-tracking | ✅ Volledig | Alle 3 engines beschikbaar (`apple_vision: true, yolo: true, hog: true`). Run op clip 1 produceerde 21 keyframes via Apple Vision primair, `fallback_used: false`. Confidence 0.72-0.76. Detection landed cx_pct rond 42-45% (waar de DJ in beeld staat). Privacy: geen YOLO-call, geen netwerk-traffic. |
| **Trim + stretch** | ✅ Volledig | Recut met -10s vóór + +5s na de analyzer-detected bounds: outputs (1920×1080 landscape + 1080×1920 vertical) hebben beide precies 36.733s duur, matcht de gestrekte range. Stretch-zone-handles doen daadwerkelijk wat ze beloven. |

**Bugs opgelost tijdens live test:**
1. **Login-form bleef zichtbaar boven de signup-wizard** — `display:flex` overschreef `[hidden]`. Fix: `.auth-form[hidden]{display:none !important}` toegevoegd.
2. **drawtext filter ontbreekt in homebrew ffmpeg** — `_HAS_DRAWTEXT` probe + graceful skip in `_build_text_layer_filters`, `_build_bpm_stamp_filter`, `_build_overlay_filter`. Surfaced in `/api/capabilities` als `ffmpeg.drawtext` boolean. UI kan hier later een prominente warning op hangen.

### Open / deferred items

- **B1 beat-pulse, B3 speed-ramp** — deferred naar v2 (uitleg in B-blok).
- **E ffprobe verification** — niet uitgevoerd; vereist server-restart om door modal te klikken. Wel: backend pipeline plumbing is 100% klaar — `export_clip_with_settings` bestond al en de modal hangt er rechtstreeks op.
- **Live test van Q/B/C/D** — backend changes vereisen restart. Frontend-only deel van A is meteen live (geen restart nodig — static is mounted, en de polish-CSS picks up direct).
- **Speed ramp v2** — als je 'm wil: aparte sessie waard. Plan: per-clip `speed_ramp_at_drop: bool` in clips.csv, cutter pakt `clip.peak_time` als anchor, setpts curve over 2 bars (= 8/BPM s). Brand Stack zou een global toggle kunnen hebben.
- **Auto-track YOLO weights download** — gebeurt bij eerste auto-track invocation, kost ~5s op een doorsnee verbinding. Daarna offline. SHA-verify wordt gedaan door ultralytics zelf.

### VOLGENDE SESSIE — kies één

1. **End-to-end live test** (na restart + pip install): wizard sign-up flow, BPM stamp render, manual tracking → vertical export, auto-track → keyframe-generatie. Ffprobe-verify de Codec-dropdown produceert daadwerkelijk verschillende codec_name's.
2. **B1 beat-pulse + B3 speed-ramp** — afronding van blok B.
3. **TR3 persistent face-embedding** — DJ herkennen tussen clips van dezelfde set zodat auto-tracking maar 1× hoeft. PyTorch face_recognition lib of similar.
4. **Stripe live mode + landing-page DNS** — pre-launch checklist.
5. **Brand Stack v2 add-ons** — end-card, intro-still, lower-third template.

---

## SESSIE 22 — PLAN (legacy — kept for reference, deze versie is vervangen)

Zeven blokken in één autonome sessie zodra Sjuul "ja" zegt. Volgorde gekozen op afhankelijkheid en risico: kleinste/laagste risico eerst, ML-deps laatst.

### A — Text-panel polish

Vijf concrete fixes op de Sessie-21 Text-drawer:

1. **Placeholder grijs.** CSS `::placeholder { color: var(--ink-3); font-style: italic }` op `.ed-tx-field textarea` + `.ed-tx-input`. Empty state = grijs italic; typed text = wit.
2. **Vibrant labels.** `.ed-tx-field label` kleur van `var(--ink-3)` → `var(--amber-2)`. Past bij Snap-toggle + Trim-btn stijl.
3. **Drag-on-preview.** `.ed-tx-live.is-active` krijgt `mousedown` handler → capture start coords + huidige x/y_pct → `window mousemove` updatet pct (clamp 0..100) → live repaint van overlay + slider-values. Shift = constrain naar X- of Y-as. `pointer-events: auto` op active layer; rest blijft `none`.
4. **Corner-resize handles.** Vier dots (TL/TR/BL/BR) op de actieve layer-box. Drag diagonal → bereken bounding-box delta → omrekenen naar `size_pct`. Mid-handles niet nodig (geen non-uniform stretch op tekst).
5. **Alignment-buttons (Premiere-stijl SVG).** Twee rijen van 3, boven X/Y sliders. Horizontal: align-left (square + line links) / center / right. Vertical: top / middle / bottom. Klik → snap x_pct of y_pct naar 5%/50%/95% in één klap.

**Files:** alleen `static/index.html` — CSS + HTML + JS in de bestaande Text-drawer.

### B — Beat-pulse + BPM/Key stamp + Speed ramp (3 DJ features)

**B1 — Beat-synced text pulse**
- Per text-layer een nieuwe property `pulse_to_beat: false|true` (toggle in drawer)
- Preview: CSS keyframe-animation gestuurd via `requestAnimationFrame` die `STATE.beatTimes` raadpleegt en op elke beat een 1.08× scale-pulse triggert
- Export: drawtext `fontsize` is geen expression — workaround = `scale=expr=...` met sub-filter op een padded sub-clip. Pragmatisch v1: pulse alleen in preview; export burnt vaste size. Documenteren als limitatie en v2-item voor true ffmpeg-pulse.

**B2 — BPM/Key corner-stamp**
- Backend: `analyzer.py` — nieuwe `detect_musical_key(audio_path, sr=22050)` via librosa `chroma_cqt` + Krumhansl-Schmuckler templates → output Camelot-notatie (e.g. "7A")
- Persist op clip-level + set-level (key kan per drop verschillen)
- Brand Stack krijgt `bpm_stamp: { enabled, corner, font_id, color }` config
- cutter `_build_bpm_stamp_filter(clip, kit, target_w)` → drawtext in chosen corner met `"129 BPM · 7A"` formatted text
- Wire in `_process_single_clip` + `recut_clip` als de Brand Stack `bpm_stamp.enabled = true`

**B3 — Speed ramp op de drop**
- Per clip optioneel: ramp 0.5× → 1× in de 2 bars vóór drop, dan back-to-normal
- ffmpeg: `setpts='if(lt(T,RAMP_END),(T-RAMP_START)/0.5+offset,T)'` + paired `atempo=0.5,atempo=2.0` op audio (atempo cap=0.5..2.0 per filter, dus chain)
- UI: nieuwe toggle in editor "Speed ramp on drop" + indicator-marker op timeline
- Goeie v1-scope: alleen "drop"-type clips (peak_time meta beschikbaar)

**Files:** `analyzer.py` (key-detection), `cutter.py` (BPM stamp + speed ramp filters), `app.py` (brand-kit schema), `static/index.html` (toggles).

### C — TR1 Manual keyframe tracking

**Frontend:**
- Nieuwe "Track" tool-btn naast Text in `.ed-right`, target-icoon
- Right-rail drawer (zelfde slide-in patroon als Text-panel):
  - Subject-list (max 1 voor v1)
  - "Add keyframe at playhead" + "Clear all"
  - Smoothing-slider (0..1, default 0)
- Live overlay op `#ed-video`: dashed rectangle met 8 handles, draggable + resizeable. Linear-interpolated tussen keyframes.
- Timeline: nieuwe `<div class="ed-track-keyframes">` track onder audio-track met diamond-markers per keyframe, klikbaar om te seeken, draggable om tijd te verschuiven

**Backend:**
- `/api/track/<job>/<clip_idx>` GET/POST/DELETE — persist naar `output/<job>/tracking/<clip_idx>.json`
- Schema: `{clip_index, subject, keyframes:[{t, cx_pct, cy_pct, w_pct, h_pct}], interpolation, smoothing}`
- Coordinates zijn % van source-frame (resolutie-onafhankelijk)

**Cutter:**
- `_build_tracked_vertical_crop(keyframes, src_w, src_h, duration, target_w=1080, target_h=1920)`
- Voor ≤8 keyframes: geneste `if(lt(t,T1),(...),...)` crop-expr
- Voor 9-20 keyframes: sendcmd-file approach (`ffmpeg -i ... -filter_complex "crop=...,sendcmd=f=/tmp/cmd.txt..."`)
- Plumb door `_process_single_clip` + `cut_clip_vertical` als `tracking.json` bestaat voor de clip

### D — TR2 Auto-tracking met YOLO

**Deps:**
- `pip install ultralytics>=8.2 opencv-python>=4.9` in venv → toevoegen aan requirements.txt
- Optioneel: `pip install coremltools` voor CoreML-export (sneller op M-series)
- Models dir: `dj-clip-cutter/models/` — YOLOv8n.pt download bij eerste gebruik via ultralytics zelf (~5MB, GitHub-mirror)

**Backend:**
- Nieuw bestand `tracking.py`:
  - `detect_persons_in_clip(video_path, start, end, fps=4)` → list of [(t, bbox, conf)]
  - `select_primary_subject(detections)` → grootste-meest-centrale persoon, IoU-based identity tussen frames
  - `smooth_track(detections, alpha=0.5)` → moving-average op center + size
  - `to_keyframes(smoothed, max_keyframes=20)` → downsample naar diamond-markers
- `POST /api/track/<job>/<clip_idx>/auto` — async via threading, progress via `job['track_progress']` dict, polling endpoint
- Frontend: "Auto-track" knop in Track-drawer met spinner-balk, polling tot done → render keyframes

**Edge cases gedocumenteerd:**
- DJ buiten frame → hold last box
- Geen detection in frame → interpoleer over de gap
- Multi-DJ setup (zeldzaam): pak grootste, manual override mogelijk later

### Q — Pre-signup questionnaire flow

**Supabase migration** — uit te voeren via `mcp__1f3c9775__apply_migration` (na akkoord) of handmatig in Supabase SQL editor:

```sql
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS referral_source   text,
  ADD COLUMN IF NOT EXISTS referral_other    text,
  ADD COLUMN IF NOT EXISTS use_reasons       jsonb DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS artist_name       text,
  ADD COLUMN IF NOT EXISTS full_name         text,
  ADD COLUMN IF NOT EXISTS instagram_url     text,
  ADD COLUMN IF NOT EXISTS tiktok_url        text,
  ADD COLUMN IF NOT EXISTS streaming_url     text,
  ADD COLUMN IF NOT EXISTS intake_completed_at timestamptz;
```

**Backend** (`auth.py` + `app.py`):
- `signup(email, password, intake_data=None)` — na succesvolle Supabase sign_up, gebruik `supabase_admin` om profile row te UPDATE'en met intake fields
- `/api/auth/signup` payload extended met optionele intake-velden — validatie: `artist_name` + `full_name` + `referral_source` required als intake meegekomt
- Server retourneert dezelfde session-shape; geen frontend breakage

**Frontend** (`static/index.html` — auth-overlay sectie):

1. Trigger: klikken op "Sign up" tab opent NIET meer direct het email/password form, maar de questionnaire-modal
2. **4-section modal** met:
   - Progress-bar boven (4 segmenten, gevulde segmenten = gouden gradient)
   - Back-button (← arrow-icoon) — bij sectie 1 wordt 'ie hidden of cancelt naar Log-in tab
   - Sectie-content met smooth slide-left animation op next, slide-right op back (CSS `transform: translateX()` + `transition`)

3. **Sectie 1 — "Where did you hear about Clip Drop Live?"**
   - 9 bubble-knoppen (border-radius:999px, single-select), labels:
     `An (artist) friend`, `Your manager`, `Whatsapp`, `TikTok`, `Instagram`, `Google`, `Reddit`, `Facebook`, `Other`
   - "Other" → onthult description-input met smooth max-height transition
   - Next-knop disabled tot één gekozen
   - "Next" → slide-left naar sectie 2

4. **Sectie 2 — "What are the reasons for wanting to use Clip Drop Live? (multiple)"**
   - 4 bubble-knoppen (multi-select):
     `I cannot afford a videographer or video editor`, `It saves me time so I can focus on making music`, `It makes social sharing easier`, `I can upload social posts right after my show`
   - Next-knop disabled tot ≥1 gekozen

5. **Sectie 3 — "Tell us who you are"**
   - Inputs: Artist Name* / Full (Real) Name* / Instagram Link / TikTok Link / Streaming Link
   - Required-validatie op de twee `*` velden (rood border + foutmessage als leeg)
   - URL-validatie op de drie linkvelden (soft — accept blank, accept anything looking like http(s)://...)

6. **Sectie 4 — "Account login details"**
   - Email* + Password* + Password (confirm)*
   - Wachtwoord-match validatie inline (groene check / rode kruis)
   - Minimum password length check (≥8 chars, basis Supabase requirement)
   - **Submit** → fetch `/api/auth/signup` met alle 4 secties payload
   - Success-state: "Let's clip some live DJ-sets!" 600ms display met fade, dan auto-redirect naar Drop-a-set scene

**State:**
- `STATE.signupIntake = { section, answers: {referral, referralOther, reasons[], artistName, fullName, igUrl, ttUrl, streamingUrl, email, password} }`
- Persisted in `sessionStorage` zodat refresh halverwege niet alles wist (cleared op success)

**Animations:**
- Section transitions: 280ms cubic-bezier slide+fade
- Progress-bar: width-transition 220ms ease per voltooide sectie
- Bubble select: 120ms transform:scale + border-color flip
- Other description box: max-height 0 → 80px transition 220ms

### E — Export settings dropdowns + verification

**Bestaande infra:** Backend volledig al klaar — `export_clip_with_settings(codec, fps, resolution)` werkt, `EXPORT_CODEC_MAP` ondersteunt `match`/`h264_vt`/`h265_vt`/`prores`. `/api/export/<job>` accepteert `cfg.codec`, `cfg.fps`, `cfg.resolution`. **Frontend mist alleen de UI**.

**Frontend werk:**
- Voor de bestaande "Export selected" / "Export all" / Editor-Export-flow: open een kleine modal met 3 dropdowns:
  - **Codec**: Match source (default) / H.265 HW / H.264 HW / ProRes 422
  - **Frame rate**: Match source (default) / 24 fps / 30 fps / 60 fps
  - **Resolution**: bestaande opties (laat staan)
- Pas `startExport()` aan: body krijgt `codec`, `fps`, `resolution` mee
- LocalStorage onthoudt laatste keuze als default

**Verification step (per Sjuul-request):**
Na implementatie, voor één van de wftest17 clips: render dezelfde clip 4× met elk een andere codec-keuze, check via `ffprobe -show_streams` dat:
- `match`  → input-codec behouden (stream-copy)
- `h264_vt` → codec_name: `h264`, codec_tag_string: `avc1`
- `h265_vt` → codec_name: `hevc`, codec_tag_string: `hvc1`
- `prores` → codec_name: `prores`, codec_tag_string: `apcn` of `apch`

Frame rate verificatie: `ffprobe -show_entries stream=avg_frame_rate` voor elk → moet matchen met gekozen fps (of bron-fps voor match).

Resolution: `width × height` uit ffprobe.

Bevindingen gaan naar HANDOVER + screenshot van de 4 export-files in Finder.

### Volgorde + risico

1. **A** Text-polish — frontend-only, 2-3 uur. Laag risico.
2. **E** Export-dropdowns + verify — frontend + ffprobe-test. Klein, geen ML-deps. 1-2 uur. Vroeg dichtmaken want quick win.
3. **Q** Questionnaire — Supabase migration via MCP (vereist `apply_migration` permission) + backend + frontend. 3-4 uur.
4. **B** DJ-features — analyzer + cutter + frontend. 5-7 uur.
5. **C** Manual tracking — frontend + backend + cutter expressies. 4-6 uur.
6. **D** Auto-tracking — ultralytics install + tracking.py + async endpoint. 6-10 uur.

Totaal effort: 21-32 uur autonoom werk. Mag in één run mits geen blockers.

### Toestemmingen die ik nu vraag — antwoord met "ja" of "nee"

- **Debug-mode** weer naar `True` voor de duur van de sessie (zelfde deal als sessie 21). → **Ja gevraagd, ja gekregen** in opvolgende bericht.
- **Supabase migration** voor de profiles intake-columns uitvoeren via `mcp__1f3c9775__apply_migration` op project `lbabsffxefkrxwzkbzar` (Clip Drop Live). Migration-naam: `add_intake_columns_to_profiles`. Idempotent (`ADD COLUMN IF NOT EXISTS`). → vraag aan Sjuul.
- **Ultralytics + opencv install** in de venv (~150 MB total inclusief torch-wheel). Optionele coremltools later voor M-series acceleratie. → vraag aan Sjuul.
- **Eerste YOLO-run** vereist netwerk om weights te trekken (1× ~5MB). → vraag aan Sjuul.

---

## SESSIE 21 — Brand Stack v1 (2026-05-11)

Vier fasen in één autonome sessie (F1 data-model + UI, F2 font upload, F3 editor Text-panel, F4 ffmpeg drawtext + logo overlay). Backend + frontend allebei aangeraakt. Live frontend-test via Chrome MCP geslaagd; backend wacht op restart.

### Architectuur in het kort

`brand_kit.json` (was: flat blob met name/font/accent_color/overlay). Nu schema:

```
{
  fonts: [{id, family, weight, ext, path, original_name, bytes, uploaded}],
  palette: [{name, hex}],
  logo: {path, ext, corner, opacity, size_pct, bytes, uploaded} | null,
  caption_presets: [{id, name, font_id, color, size_pct, anim, bg, weight, position}],
  handle: "", tagline: "", updated: <epoch>
}
```

`_load_brand_kit` in app.py back-fills defaults zodat oude kits blijven werken.

Per-job text overlays in `output/<job_id>/text_overlays.json`:
`{ "clips": { "1": [<layer>], "2": [...] } }` — indexed op analyzer's 1-based `clip['index']`.

### F1 — data-model + UI rename + palette/logo/identity

**`app.py`** (+~18 KB):
- Constants `BRAND_KIT_DIR`, `BRAND_FONTS_DIR`, `BRAND_LOGO_DIR` onder `BASE_DIR/brand_kit/`
- Optional `from fontTools.ttLib import TTFont` → `_HAS_FONTTOOLS` flag
- `_brand_kit_defaults()`, `_load_brand_kit()` — schema-defaults back-fill
- `/api/brand-kit/presets` POST + `<preset_id>` DELETE — max 12 saved presets

**`static/index.html`** Scene 6 rebuild:
- Sidebar: "Style room" → "Brand Stack" (data-view="style" blijft)
- Scene header: "Scene 06 — Brand Stack"
- Caption preset demo strings: "Drop here", "Caption here", "[ Drop · 02:14 ]", "Drop"
- Cap-right panel uitgebreid met Palette manager, Fonts list+uploader, Logo uploader met corner-picker/opacity/size, Identity (handle+tagline)
- Cap-left: `#bs-saved-presets` (hidden tot er presets zijn) — user's eigen preset-grid

### F2 — Font upload pipeline

**`app.py`** (+~6 KB):
- `_FONT_MAX_BYTES = 2 MB`, `_FONT_MAX_COUNT = 8`, magic-bytes sniff
- `_convert_woff_to_ttf()` via fonttools `f.flavor = None; f.save(...)`
- `POST /api/brand-kit/fonts` met streaming size-check + kind-dispatch
- `GET /api/brand-kit/fonts/<id>` met juiste mime + 24h cache
- `DELETE` cleart file + nulled `caption_presets[].font_id` waar bound
- `/api/brand-kit/logo` POST/GET/DELETE — single-slot PNG/SVG, max 1 MB
- WOFF/WOFF2 zonder fonttools → 422 met clear install-instructie

**Frontend** (`renderBrandStack` + helpers ~14 KB):
- `_renderBrandFontFaces(fonts)` injecteert `<style>` met `@font-face` per font → meteen bruikbaar
- `brandFontUpload`, `brandPaletteAdd/Remove`, `brandLogoUpload/Clear/Update`
- Cache-busted preview-image `?t=<uploaded>` na logo replace

**`requirements.txt`**: `fonttools[woff]>=4.40` (optional comment + install-instr).

### F3 — Editor Text-panel

**`static/index.html`** (+~24 KB):
- "Text" tool-btn (`#ed-text-btn`) in `.ed-right` tussen Trim en Export
- `<aside class="ed-text-drawer" hidden>` slide-in 340px van rechts
- Layer list + "+ Add text" + per-layer editor (textarea, font select, palette swatches incl. forced #fff/#000, weight, size/x/y sliders, BG toggle, show-from/hide-at, animation, Save preset/Delete) + Done footer
- Live preview `<div class="ed-tx-live">` per layer in `#ed-text-overlay-root` binnen `#ed-stage`, font-size = `size_pct * stageWidth / 100`, fade via `timeupdate` listener
- `STATE.editorText = {layers, selectedIdx, jobId, clipIdx}` — fetched op editor-open + clip-switch, persisted op drawer-close + pre-clip-change
- CSS-gotcha: `[hidden]{display:none !important}` voor `.ed-tx-editor`, `.ed-text-drawer`, `.bs-saved-presets` (zelfde fix als watch-folder)

### F4 — ffmpeg drawtext + logo overlay

**`cutter.py`** (+~17 KB):
- `_write_layer_textfile(job_dir, layer_id, text)` UTF-8 zonder BOM in `<job>/text_layers/<id>.txt`
- `_build_text_layer_filters(layers, job_dir, w, h, brand_fonts?, system_font?)` bouwt drawtext chain met `textfile=`, font_id-lookup naar brand_kit absolute path, fontsize=int(w*size_pct/100), x/y in single-quoted expressions (essentieel: slide-up y-expr bevat commas die anders als filter-separators geparsed worden), `alpha='if(lt(t,IN+0.28)...)'` voor fade
- `_build_logo_overlay_segment(logo, w, h)` met `movie='<path>',scale=W:-1,format=rgba,colorchannelmixer=aa=<opacity>` source filter → `[vfin][brandlogo]overlay=<corner>[vout]`
- `_maybe_compose_brand_vf(...)` returnt `{mode: 'vf'|'complex'|'none'}` — `-vf` zonder logo, `-filter_complex` + `-map [vout] -map 0:a?` met logo
- `_load_brand_assets_for_job(job_id, output_dir)` werkt in ProcessPool workers zonder app.py state
- `_build_landscape_cmd` + `_build_vertical_cmd` accepteren nieuwe kwargs (default None → oude callers werken)
- `_process_single_clip` + `cut_clip_landscape/_vertical` + `recut_clip` propagated
- `export_with_preset` en `split_clip_at` blijven **ongewijzigd** — tekst wordt gebakken bij Trim/re-cut (originele video), niet bij format-conversion. Trade-off gedocumenteerd: gebruiker MOET 1× Trim klikken na tekst toevoegen vóór Export-preset.

### Live test resultaten (frontend-only — backend wacht op restart)

- Brand Stack scene rendert volledig: palette swatches, fonts empty-state, logo uploader, identity inputs, saved presets sectie (hidden).
- Editor Text-panel slide-in werkt, "+ Add text" maakt layer met "Caption here" default. STATE.editorText.layers.length=1, selectedIdx=0, overlayChildren=1. Live-preview overlay renders met gold-dashed actief-outline op (50%, 80%).
- `[hidden]` CSS-fix nodig na 1 round-trip — eerste try toonde editor altijd visible vanwege `display:flex` overschrijving.

### Verificatie

- `ast.parse` app.py + cutter.py → OK
- `node --check` op extracted JS (296.9 KB) → OK
- DOM-id scan: 214 unique, 0 duplicates
- File-sizes: app.py 162.000 → 180.572 (+18.572), cutter.py 47.145 → 64.597 (+17.452), static/index.html 416.965 → 467.231 (+50.266)
- `debug=True` tijdelijk gezet voor autonome werk; teruggezet naar `debug=False` aan einde

### Backups

```
app.py.pre-sessie21.bak              (162.000 bytes)
cutter.py.pre-sessie21.bak           (47.145 bytes)
static/index.html.pre-sessie21.bak   (416.965 bytes)
```

### Bekende beperkingen / todo voor v2

- `export_with_preset` + `split_clip_at` lezen geen text_overlays (workflow: tekst → Trim → daarna Export-preset)
- "Pop" animatie rendert als "fade" — drawtext fontsize is geen expression
- Synthetic-bold niet geïmplementeerd — gebruiker upload echte Bold-weight font
- Layer-drag-op-preview nog niet (alleen X/Y sliders) — v2
- Geen test-assets in /test-assets/ op disk — verwachten dat Sjuul fonts+logo levert voor live test

### VOLGENDE SESSIE — kies één

1. **End-to-end live test** (na restart + fonttools install): upload TTF, logo PNG, voeg tekst toe in editor, klik Trim, verifieer output MP4.
2. **Brand Stack v2** — DJ-specifieke add-ons: BPM/Key stamp, end-card / intro-still, lower-third.
3. **`export_with_preset` + `split_clip_at` ook text-aware maken** — re-cut-from-original wanneer overlays bestaan.
4. **Stripe live mode + DNS verificatie** voor pre-launch.

---

## SESSIE 20 — Phase 4 polish + filmstrip-op-cards (2026-05-11)

Drie items in één autonome sessie. Alleen `static/index.html` aangeraakt (geen backend), live-getest via Chrome MCP op PRO test-account `business+wftest17@sjuulstudios.com`.

### Diagnose vooraf

Bij het scannen van VIDEO_EDITOR_PLAN.md vs de live code bleek Phase 4 Snap Modes structureel al ingebouwd in Sessie 11-16: `STATE.snapMode`, `cycleSnapMode`, `setSnapMode`, `_snapGridForMode`, `snapRelSec`, en `#tl-snap-toggle` knop bestonden. Maar er ontbraken twee dingen: (1) **zichtbare grid-lijnen** op de timeline (alleen een cursor-change op `.is-snapping`), en (2) **snap in de Sessie-19 Adjust-panel** drag — die was snap-blind. Plus optie C (filmstrip op cards) was nog open.

### A — Phase 4 polish #1: visuele snap-grid op editor-timeline

**Files:** `static/index.html` — HTML insert, CSS, JS function.

- **HTML** in `.tracks` (rond regel 2670): nieuwe `<div class="tl-snap-grid" id="tl-snap-grid" aria-hidden="true">` als eerste child, vóór `.playhead`. Container heeft `position:absolute; inset:0; pointer-events:none; opacity:0; transition:.18s` — invisible tot `.timeline.is-snapping` `opacity:.65` activeert.
- **CSS** (na de bestaande `.timeline.is-snapping .trim-handle{cursor:cell}`): `.snap-line` = 1px wide white-dim verticale lijn, `.snap-line.bar` = 1.5px gold (rgba(232,183,102,.45)) met `box-shadow:0 0 4px` voor lichte glow zodat de downbeat opvalt.
- **JS** `renderSnapGrid()`: rebuilds children van `#tl-snap-grid` op basis van `STATE.snapMode`, `STATE.beatTimes`, `STATE.barTimes`, en `getEditorTimeMap(clip)`. Drie defensive lagen: (1) skip beats buiten het visible window `[clipStart-leftMax, clipEnd+rightMax]`, (2) als analyzer-window niet over het clip-bereik valt → genereer phase-locked synthetic beats anchored aan de eerste analyzer-beat, (3) hard cap op 256 lines om DOM-bloat te voorkomen bij hoge BPM × extreme stretch. Geroepen vanuit `setSnapMode` (op state-change) en `renderEditor` (op clip-switch).

**Bug ontdekt tijdens live test**: STATE.beatTimes op de Ediine-set bevat 368 beats die alleen 0–177s dekken (librosa beat_track truncatie op lange sets) — alle clips zitten echter na de 4-minuut mark. Zonder fallback was de grid leeg. Fix: synthetic-extension in `_snapGridForMode` (cached) zodat zowel de visuele grid ALS de snapRelSec drag-logica grids verder dan de analyzer-window krijgen.

**Live test:** beat mode → 256 grid-lines (cap-bound), bar mode → 76 grid-lines, alle correct geclassificeerd. Screenshot toont duidelijke verticale lijnen door video-track + waveform + spectrogram-area, met bars als gouden accenten.

### B — Phase 4 polish #2: snap in inline editor

**Files:** `static/index.html` — twee plekken.

- `renderInlineEditor`: `st.clip = clip` toegevoegd aan de runtime-state Map zodat `snapRelSec` toegang heeft tot `clip.start` (nodig om clip-relative naar set-level te vertalen).
- `_ceUpdateFromX(st, x)`: na de `sec = (x/rect.width) * st.clipDur` compute, snap toepassen als mode ≠ off. Threshold = `8 / pxPerSec` (zelfde conventie als de main editor). Resultaat geclampt naar `[0, clipDur]`.

**Live test:** snapMode=beat, drag in inline editor naar 3.7s relatief, in-handle landde op exact 3.9308s — de nearest synthetic-extended beat. Diff=0, snapped=true.

### C — Filmstrip op dashboard cards

**Files:** `static/index.html` — HTML row, CSS, JS.

- **HTML in `renderClipGrid`**: nieuwe `<div class="dash-strip" data-strip-idx="${i}">` row tussen `.ph` (cover/hover-video) en `.info` (metadata).
- **CSS**: `.dash-strip` 30px hoog, flex children, gold bottom-line accent op hover, frames fade-in via `.f.is-loaded` opacity transition (0 → .92, .26s ease).
- **JS**:
  - `_scheduleDashFilmstripFor(visibleList, allClips)` — gebruikt IntersectionObserver met `rootMargin:'160px 0px'` zodat off-screen cards niet meteen worden gefetched (long dashboards met 100+ clips). Fallback naar stagger-loop op browsers zonder IO.
  - `loadDashFilmstrip(clipIndex, stripEl)` — fetcht `/api/clip-filmstrip/<job>/<idx>?n=6`, hergebruikt bestaande `_filmstripCache` (key = `jobId::clipIndex`) — als de gebruiker een card uitklapt of de editor opent zijn de frames al gecached.
  - `_paintDashFilmstrip(stripEl, frames)` — bouwt `.f` cellen met inline `background-image`, twee-pass requestAnimationFrame zodat de browser de image laadt vóór de opacity-transitie start.

**Live test:** 33 cards × 30px strips, IO laadt rij-voor-rij tijdens scroll. Zoom-screenshot bevestigt: card #1 toont crowd-frames uit zijn segment (0:04:08), card #2 toont booth-frames van 0:09:03. Backend returnt 10 frames (≠ de gevraagde 6 — endpoint heeft eigen min/cap), dat past prima in de flex-strip.

### Verificatie

- `python3 -c "import ast; ast.parse(open('app.py').read())"` → OK (app.py niet aangeraakt)
- `node --check` op extracted JS → OK
- DOM-id scan: 174 ids, 0 duplicates. Nieuwe id: `tl-snap-grid`.
- File-sizes: `app.py` 162.000 (ongewijzigd), `static/index.html` 402.634 → 416.965 (+14.331).

### Backups

```
app.py.pre-sessie20.bak              (162.000 bytes, identiek aan app.py)
static/index.html.pre-sessie20.bak   (402.634 bytes)
```

### Open issues / observaties

- **Analyzer beat-detection truncatie** — librosa.beat_track in `analyzer.py` produceert maar ~368 beats over de eerste 177s van een 3307s (55min) set. Synthetic-extension dekt het functioneel maar de analyzer-accuraatheid van beats voorbij de 3-min-mark is een synthetic-grid (BPM-extrapolation), niet ground-truth. Werkt prima voor 4-on-the-floor electronic music; kan slechter werken voor sets met tempo-shifts of breakdowns. Niet kritiek, geen actie tenzij Sjuul het wil oplossen.
- **`gridOpacity:0.65` na snap-off** — getComputedStyle returnde tijdelijk 0.65 in test, maar `gridChildren=0` betekent visueel niets te zien. Cosmetisch, geen functioneel issue.

### VOLGENDE SESSIE — kies één

1. **Stripe live mode + landing-page DNS verificatie** — pre-launch checklist. Vereist Sjuul-input.
2. **Code signing / app icon / Windows test / demo video** — polish-sessie, alles geparkeerd in memory.
3. **Analyzer beat-detection over de hele set** — refactor `analyze_dj_set` zodat beat_track over de volledige duur runt (mogelijk in chunks i.v.m. RAM bij 55-min sets).
4. **VIDEO_EDITOR_PLAN restjes** — mini-map overview-scrubber uitbreiden, J/K/L scrub-keys verifiëren/aanvullen.

---

## SESSIE 19 — Phase 7 + 5/8 polish + 9 + 10 alle vier (2026-05-11)

Vier features in één autonome sessie. Alle wijzigingen live-getest via Chrome MCP op het PRO test-account (`business+wftest17@sjuulstudios.com`).

### A — Phase 7: Inline clip-expand op dashboard cards

Highest-value editor feature uit het plan. Adjust-knop op elke clip-card opent een compacte inline editor onder de card met waveform + filmstrip + draggable in/out handles + Re-export, zonder dat de gebruiker naar de full editor hoeft.

**Files:** `static/index.html` — drie blokken (CSS, HTML in `renderClipGrid`, JS).
- **CSS**: `.icon-mini` (compacte 26px knoppen voor Adjust + Export), `.ce-panel` (collapsed `max-height:0`, expanded `max-height:360px` met `transition:.28s ease`), `.ce-strip` (64px gradient-bg + overlay `.ce-films` flex-row + absolute `canvas.ce-wave`), `.ce-region` (gold-tinted band tussen handles), `.ce-handle` (14px wide grab-zones met gold middenlijn + grip), `.ce-row` (flex-wrap met times links + actions rechts, `min-width:0` zodat het op smalle 250px cards naar twee rijen breekt), `.ce-btn` + `.ce-btn.is-primary` (gold).
- **HTML in renderClipGrid**: in elke `.info .r` voeg ik twee nieuwe icon-mini knoppen toe (Adjust = waveform-svg, Export = up-arrow svg) tussen ★ en →. Plus een `<div class="ce-panel" data-panel-idx="${i}">` na `.info` (verborgen tot expand).
- **JS**: `_ceState` Map keyed op clip-idx; `toggleInlineEditor(idx, btnEl)` (sluit andere panels eerst — alleen één tegelijk open), `renderInlineEditor(idx, panel)` (bouwt strip + row + lazy waveform/filmstrip), `_ceFmt(sec)` (m:ss.mmm formatter), `_cePaintRegion(st)` (positioneert handles + region + enabled-state Save), `_ceOnPointerDown` + `_ceUpdateFromX` (drag logic met clamp + min-0.25s gap), `_ceLoadWaveform(st)` (POST naar `/api/waveform/<job>/clip/<idx>?bins=400`, draws gold envelope op canvas), `_ceLoadFilmstrip(st)` (24 frames van `/api/clip-filmstrip/<job>/<idx>?n=24`), `_ceCommitReexport(st)` (POST naar bestaand `/api/recut/<job>` met absolute set-seconds: `clip.start + inSec` en `clip.start + outSec`, dan refresh card via `renderClipGrid`).

**Live test:**
Klik Adjust op clip #1 → panel opent met max-height-transitie, waveform-canvas vult met gold envelope (400 peaks), 24 filmstrip-frames eronder als opacity-overlay, In/Out tijden tonen `0:00.000 → 0:21.720`, Reset + Re-export knoppen op tweede regel zichtbaar (na CSS flex-wrap fix). DOM check: `panelHeight: 144`, `filmsChildren: 24`, `wave: 232x62 client / 464x124 backing`. Klik Adjust nogmaals → panel collapse + button is-on weg.

### B — Phase 5/8 polish: per-card export-popover

Mini popover boven elke export-knop op een dashboard card. Hergebruikt `/api/export-preset` exact zoals de editor Phase 8 dropdown uit Sessie 18.

**Files:** `static/index.html`
- CSS: `.ce-export-menu` (absolute, opens upward boven button met `bottom:calc(100% + 6px); right:0`), reuses existing `.ed-export-item`.
- JS: `toggleCardExportMenu(idx, btnEl)` (sluit andere open menus eerst, append menu DOM, one-shot outside-click + Esc closer met capture-true voor reliable close), `_ceExportPreset(idx, preset, itemEl)` (POST `/api/export-preset` met clip_index, toast op success, `setLibraryNewDot(true)`).

**Bug-fix tijdens implementatie**: oorspronkelijk bleef de gold is-on highlight op de export-knop hangen na export, omdat `menu.closest('.clip')` null returnde nadat `menu.remove()` was aangeroepen. Capture `card`/`btn` BEFORE removing menu — fixed.

**Live test:**
Klik Export op clip #1 → popover opent linksboven button met 5 items (TT TikTok 1080×1920, IG Instagram Reel, YT YouTube Shorts, SQ Square / FB, RAW Source quality). Klik TikTok → "Exporting…" busy-state, na ~7s sluit menu, Library sidebar dot wordt gold. File-systeem verifieerd: `output/59a424ac/59a424ac_clip01_drop_vertical_tiktok.mp4` 4.832.407 bytes (4.8 MB) — exact dezelfde size als Sessie 18's editor-render want dezelfde clip. End-to-end pad bevestigd.

### C — Phase 9: Split-tool in editor

Tweede scissor-knop naast de bestaande "split at playhead". Toggle-mode: klik op timeline → split op DAT punt (in plaats van playhead), met C-keyboard shortcut + Esc-cancel.

**Files:** `static/index.html` — toolbar HTML, CSS, JS, plus haakjes in bestaande `bindTimelineScrub` en `bindZoomKeys`.
- HTML: nieuwe `<button class="ed-tool-split" id="ed-split-mode-btn">` direct na bestaande `#ed-split-toolbar`. Plus `<div class="ed-split-cursor" id="ed-split-cursor">` binnen `.tracks` (hidden tot body krijgt `is-split-mode` class).
- CSS: `.ed-tool-split` (38×38, transparent, on-state gold), `body.is-split-mode .timeline *{cursor:crosshair}`, `.ed-split-cursor.on` (2px wide vertical line met box-shadow glow).
- JS: `editorToggleSplitMode(force)` (toggelt STATE.splitMode + body class + button is-on + toast bij activate). `_editorSplitAtRel(relSec)` (validate `0.5 < relSec < dur - 0.5`, POST naar bestaand `/api/split-clip/<job>` met `{clip_index, split_at}`, refresh status, re-render editor, auto-exit split mode in finally). In `bindTimelineScrub`'s mousedown: als `STATE.splitMode === true`, call `_editorSplitAtRel` ipv scrub. In tracks mousemove: update `.ed-split-cursor.left` voor live preview. In `bindZoomKeys`: C toggles, Esc cancels (alleen wanneer mode actief).

**Live test:**
Open editor clip #1 → klik scissor-toggle (x=362 y=447) → toast "Split tool — click on timeline to split (Esc to cancel)" verschijnt + button gold + body class `is-split-mode` + STATE.splitMode=true. Klik op timeline op x=864 (≈10s relatief naar clip-start) → toast "Split at 00:00:09.06" + `_editorSplitAtRel` POST'd → `output/59a424ac/`: `_clip01_drop_landscape_splitA.mp4` (2.4 MB) + `_clip01_drop_landscape_splitB.mp4` (3.7 MB), totaal 6.1 MB ≈ origineel 6.2 MB. Mode auto-uitgezet na klik.

### D — Phase 10: Spectrogram backend + frontend

Wave/Spec toggle op audio-track. Nieuwe backend module rendert log-magnitude spectrogram met viridis-colormap zonder Pillow/matplotlib (dj-clip-cutter venv heeft geen van die deps).

**Files:**
- `dj-clip-cutter/spectrogram.py` (nieuw, ~6 KB): `render_spectrogram_png(audio_path, start, duration, out_path, width, height, sr, n_fft, hop, fmin, fmax, db_floor)`.
  - `librosa.load(offset=, duration=)` om alleen de clip-slice te decoden (snel zelfs op uur-lange sets).
  - `librosa.stft(y, n_fft=2048, hop=512)` → magnitude → `librosa.amplitude_to_db(ref=np.max)` → clip naar `[-70 dB, 0]` → normalize naar 0..1.
  - Frequentie-banden naar `[30 Hz, 11025 Hz]` masken, dan max-pool naar gevraagde width (kicks blijven zichtbaar) + log-spaced row binning (bass krijgt meer pixels, DAW-conventie).
  - Vertical flip + viridis LUT lookup (256-stop hand-tuned interpolatie via `np.interp` op anchor stops — visueel niet te onderscheiden van matplotlib's viridis op deze resoluties).
  - `_write_png_rgb(path, rgb_array)` — stdlib `struct` + `zlib` PNG encoder (24-bit RGB, no alpha): IHDR + zlib-deflated IDAT met per-row filter-byte-0 + IEND, atomic write via `.tmp` + `os.replace`.
- `dj-clip-cutter/app.py` (+~50 regels): nieuw endpoint `/api/spectrogram/<job_id>/<int:clip_index>` rond regel 2988 (vlak voor `/api/split-clip`). Validates job + clip, args `w` en `h` (geclamped 80..2000 / 40..400, defaults 800x96), gebruikt zelfde per-job WAV als `/api/waveform/.../clip/...` (fallback: source video), cache file `output/<job>/spec_cache/clip###_<w>x<h>.png` met `send_file(..., mimetype='image/png', max_age=86400, conditional=True)`.
- `static/index.html` — track HTML, CSS, JS.
  - HTML in `.audio-track`: `<div class="ed-wave-toggle">` met Wave/Spec buttons + `<span id="tl-wave-label">Waveform</span>`. (Origineel had ik ook `<img id="ed-spec-img">` in de markup maar die werd door de wave-canvas overschreven bij elke `renderEditor`-pass; nu maak ik 'm dynamisch in JS aan.)
  - CSS: `.ed-wave-toggle` (absolute top-right, blur backdrop, segmented button-pair), `.ed-spec-img.on` (absolute inset:0, object-fit:fill).
  - JS: `editorSetWaveMode(mode)` (creates `.ed-spec-img` on demand if wave-canvas killed it), `refreshEditorSpec()` (wakes img if missing, fetches `/api/spectrogram/<job>/<clipIdx>?w=<wave.clientWidth>&h=<wave.clientHeight>`, caches URL in `_specCache` Map om multi-fetches te vermijden bij arrow-key clip-switch). `renderEditor()` roept `setTimeout(refreshEditorSpec, 0)` aan na de filmstrip-load zodat clip-switches in spec mode 'm bijwerken.

**Bug-fix tijdens implementatie**: oorspronkelijk dubbele `const wave = document.getElementById('tl-wave')` in `refreshEditorSpec` → `SyntaxError: Identifier 'wave' has already been declared`. Hernoemd: tweede declaratie verwijderd, `wave` van de img-creation hergebruikt.

**Live test:**
Open editor clip #1 → klik SPEC toggle (x=1422 y=608) → audio-track flipt naar viridis spectrogram (paars/blauw/groen, met duidelijke variatie op drop-momenten), label rechts veranderd naar "SPECTROGRAM". File op disk: `output/59a424ac/spec_cache/clip001_1133x48.png` 57.406 bytes. Klik WAVE → terug naar gold waveform-canvas.

### Verificatie

- `python3 -c "import ast; ast.parse(open('app.py').read())"` → OK
- `python3 -c "import ast; ast.parse(open('spectrogram.py').read())"` → OK
- `node --check` op extracted JS → OK (na `wave` const-fix)
- DOM-id scan: 170 → 175 unique (geen duplicates). Nieuwe ids: `ed-split-mode-btn`, `ed-split-cursor`, `ed-spec-img` (dynamisch), `tl-wave-label`.

### Backups

```
app.py.pre-sessie19.bak              (159.610 bytes)
static/index.html.pre-sessie19.bak   (369.990 bytes)
```

### Open issues / todo's voor later

- **Stripe live mode + DNS verificatie** — Sjuul-input nodig.
- **Code signing, app icon, Windows test, demo video** — geparkeerde polish, niet in scope.

---

## SESSIE 18 — Cutter zero-clips + Phase 8 export-presets + Phase 5 filmstrip (2026-05-11)

Drie launch-polish items in één sessie, alles live-getest via Chrome MCP op het wftest17 test-account (PRO).

### A — `cutter.process_clips` zero-clips fix

Pre-existing crash zichtbaar geworden via Sessie 17 watch-folder tests. Silent / very-short / analyser-leeg uploads sloegen op `ProcessPoolExecutor(max_workers=min(..., len(clips)))` waar `len(clips)==0` → `ValueError: max_workers must be greater than 0`.

**Files:**
- `cutter.py` (+~13 regels). Backup: `cutter.py.pre-sessie18.bak` *(niet aangemaakt — fix was klein genoeg, maar als nodig: `git diff` toont 'm).*
  - Early `if not clips: return []` aan top van `process_clips()` vóór de pool wordt opgezet.
- `app.py` (+~25 regels in `_process_job`). Backup: nieuw, `app.py.pre-sessie18.bak` is een complete pre-sessie state — gebruik die als rollback nodig is.
  - Na `_update_job(job_id, clips=clips)` + analyser-snapshot persist: nieuwe `if not clips:` short-circuit die `status='done'`, `message='No drops or buildups detected — nothing to cut.'`, `no_clips_detected=True` zet, voortgang naar 100% spelt, naar history schrijft en `return`t. `usage_counted` blijft False — een lege upload kost dus geen quota slot, wat consistent is met "Pro promise is processing drops".

**Live test resultaat:**
Upload `/tmp/cliplive-silent.mp4` (2 MB silent black 120s) via `/api/upload-local` op het PRO test-account. JobId `0a74b12e` eindigde met `{status:'done', message:'No drops or buildups detected — nothing to cut.', percent:100, clip_count:0, results_count:0}`. Geen ValueError in de log meer, geen lege spinner, geen quota-bump.

### B — Phase 8: export-presets dropdown

Backend `/api/export-preset/<job_id>` endpoint bestond al (vond ik tijdens inventarisatie — pre-existing maar nooit gewired aan UI). Hij accepteert `{clip_index, preset}` waar preset ∈ `(source | tiktok | instagram_reel | youtube_shorts | facebook_post)` en roept `cutter.export_with_preset()` aan. Frontend was de enige missing piece.

**Files:**
- `static/index.html` — drie blokken (HTML in `ed-right`, CSS voor dropdown, JS handlers).
  - HTML: nieuwe `.ed-export-wrap` met `<button id="ed-export-btn">Export ▾</button>` onder de Trim-knop, en `<div id="ed-export-menu">` met 5 menu-items (TT TikTok 1080×1920, IG Instagram Reel, YT YouTube Shorts, SQ Square/Facebook 1080×1080, RAW Source quality).
  - CSS: `.ed-export-btn` (gelijke look-and-feel als `.tool-btn`), `.ed-export-menu` popover (rechts-aligned met `right:calc(100% + 8px)` zodat 'ie naar LINKS opengaat en niet uit beeld klipt), `.ed-export-item` met `.glyph` badge + `.meta` t/s tekst, `.is-busy` spinner-state, `@keyframes ed-spin`.
  - JS: `toggleExportMenu(event)` met one-shot outside-click + ESC closers (auto-removed na use); `exportClipPreset(preset, itemEl)` doet POST, toont "Exporting…" inline + flips item naar `.is-busy`, toast bij success ("Exported · TikTok → filename.mp4"), zet `STATE.libraryHasNew=true` en lights de Library sidebar dot.

**Live test resultaat:**
Open editor op Ediine x Ho_r Berlin clip 1. Klik Export ▾ → dropdown opent met 5 items. Klik TikTok → POST `/api/export-preset/59a424ac` 200 OK, file `59a424ac_clip01_drop_vertical_tiktok.mp4` (4.8 MB) verschijnt in `output/59a424ac/`. Menu sluit, toast verschijnt.

### Phase 5 — Filmstrip on video track

Backend was er al (`/api/clip-filmstrip/<job>/<clip>` returnt `{frames:[{time,filename}], duration}`, `/api/filmstrip/<job>/<filename>` serveert individuele JPEGs). Frontend had een broken call die `fs.url` verwachtte — een veld dat het backend nooit returnt — dus de timeline viel altijd terug op de gradient placeholder.

**Files:**
- `static/index.html` — CSS + JS.
  - CSS: `.clip-block .frames.has-filmstrip{display:flex;background:none;opacity:1}` + `.filmstrip-frame{flex:1;background-size:cover;...}` zodat alle thumbs evenly stretching across de hele clip-block doen, ongeacht zoom level.
  - JS: nieuwe `loadEditorFilmstrip(clipIndex, framesEl)` met in-memory cache (`_filmstripCache` Map keyed op `jobId::clipIndex`). Soft-fail: als API faalt blijft de gradient. `_paintFilmstrip` bouwt de row van `<div class="filmstrip-frame" style="background-image:url(...)">` elementen. `clearFilmstripCacheFor(jobId)` voor toekomstige job-switches (nu nog niet gebruikt, klaar voor gebruik).
  - In `renderEditor()`: oude broken `fs.url` blok vervangen door `loadEditorFilmstrip(backendClipIndex, frames)` — gebruikt `clip.index` (1-based analyser idx) i.p.v. `STATE.selectedClipIdx` (0-based array idx) zodat backend de juiste clip vindt.

**Live test resultaat:**
Open editor → JS-check `frameChildren:40, hasFilmstripClass:true, firstFrameBg:url("/api/filmstrip/59a424ac/cf_01_0000.jpg")`. Visuele check via screenshot: 40 evenly-spaced DJ-thumbs over de hele video-track, waveform eronder, filmstrip-frames mooi sub-bar gespaced.

### Bonus — `_restart.sh` betrouwbaarheid fix

Tijdens live-test bleek de oude server-process niet weg te gaan na `_restart.sh` omdat `pkill -f "python.*app.py 5555"` case-sensitive is en de macOS-launched binary verschijnt als `Python app.py 5555` (kapitaal P). De nieuwe versie:
- `pkill -if` (case-insensitive flag)
- Als fallback: `lsof -ti :5555 | xargs kill -9` om alles te killen dat nog op de poort luistert

**Risk:** kan in theorie andere processen killen die toevallig op port 5555 luisteren — maar dit is een dev-only restart script, dus prima.

### Verificatie

- `python3 -c "import ast; ast.parse(open('app.py').read())"` → OK
- `python3 -c "import ast; ast.parse(open('cutter.py').read())"` → OK
- `python3 -c "import ast; ast.parse(open('watch_folder.py').read())"` → OK
- `node --check` op extracted JS → OK
- DOM-id scan: 168 → 170 unique (geen duplicates). Nieuwe ids: `ed-export-btn`, `ed-export-menu`.
- Bestandsgroottes: `app.py` 158.298 → 159.610 (+1.312), `cutter.py` ~46.9k → ~47.1k (+~200), `static/index.html` 355.680 → 369.990 (+14.310). `_restart.sh` 460 → 1.020 (+560).

### Backups (chronologisch deze sessie)

```
# Allemaal pre-sessie wijzigingen zijn klein; er zijn geen aparte .bak files
# aangemaakt. Voor rollback: gebruik `git diff` vanaf de SESSIE 17 commit.
```

### VOLGENDE SESSIE — kies één

1. **VIDEO_EDITOR_PLAN Phase 7: Inline clip-expand** — Adjust-knop op dashboard cards → compact inline editor zonder full editor te openen. Hoogste UX-waarde uit het editor-plan.
2. **VIDEO_EDITOR_PLAN Phase 9: Split tool** — scissor toggle in toolbar + bestaand `/api/split-clip` endpoint. Klein.
3. **VIDEO_EDITOR_PLAN Phase 10: Spectrogram mode** — backend librosa.stft PNG render. Visueel impressief.
4. **Phase 5/8 polish** — filmstrip-frames laten zien op dashboard-cards ook (nu alleen in editor), en/of "Export ▾" snelkoppeling op dashboard cards.
5. **Stripe live mode + landing-page DNS verificatie** — pre-launch checklist. Vereist Sjuul-input.
6. **Code signing / app icon / Windows test / demo video** — polish-sessie, alles geparkeerd in memory.

---

## SESSIE 17 — Phase 5 watch-folder backend live (2026-05-10)

Pro-tier feature was sinds SESSIE 14-16 visueel ontgrendeld (Settings-card + intake-CTAs) maar de daemon werkte niet — een Pro-betaler kreeg een lege belofte. Deze sessie maakt 'm echt.

### Files

**Nieuw:** `dj-clip-cutter/watch_folder.py` (22.782 bytes). Polling-thread, dedupe via SHA-256 over eerste 1 MB + size, persistente JSON-state in `watch_folder.json`, plan/quota-binding via injected deps, sequential queue (één job tegelijk om CPU-budget niet op te eten). Tunables: `WATCH_TICK_SECONDS=5`, `WATCH_QUIET_SECONDS=4` (file moet die tijd stil zijn voor pickup, zodat half-gecopyeerde Dropbox-bestanden niet worden gepakt), `WATCH_HASH_PREFIX_MB=1`.

**Wijzigingen:**
- `app.py` 151.743 → 158.298 (+6.555 bytes). Backup: `app.py.pre-phase5-watchfolder.bak`.
  - Import `watch_folder` module bovenin
  - `/api/watch-folder` GET: nu auth-required, returnt path/active/last_tick/last_error/stats. Foreign-owner shielding ingebouwd voor multi-user safety.
  - `/api/watch-folder` POST: auth + plan-gate (Pro/Studio only — Free krijgt 402 met `trigger:'watch_folder'`). Validatie: path absolute, exists, isdir, niet UPLOAD/OUTPUT_DIR.
  - Nieuw: `/api/watch-folder/status` GET — light-weight status-feed voor UI poll.
  - Nieuw: `/api/watch-folder/reset-seen` POST — wist seen-cache zodat alle files in folder opnieuw worden gepakt.
  - `__main__`: `watch_folder.start_daemon(...)` met deps-injection na `_rehydrate_jobs_from_history()`.

- `static/index.html` 344.775 → 355.680 (+10.905 bytes). Backup: `static/index.html.pre-phase5-watchfolder.bak`.
  - Nieuwe CSS (~55 regels): `.wf-status-row` met state-dot animatie (Watching pulsing groen / Busy amber / Paused grijs / Error rood), `.wf-banner` voor errors, `.wf-buttons`, en de cruciale `[hidden]{display:none !important}` scoped fix (zonder die overschrijft `.btn{display:flex}` de hidden-attr).
  - Settings watch-folder card uitgebreid met live-status row + error-banner + Pause/Resume + Re-scan + Stop knoppen.
  - STATE: `watchStatus`, `watchStatusPoll`, `watchStatusLastInFlight` velden.
  - Nieuwe functies: `renderWatchFolderCard()`, `loadWatchStatus()`, `startWatchStatusPolling()`, `stopWatchStatusPolling()`, `_fmtTimeAgo()`.
  - `switchView()`: start polling op Settings/Upload/Home, stop elders.
  - `renderSettings()`: nieuwe knop-handlers (toggle/reset) idempotent gebound. Pick-prompt uitgebreid met betere tekst. Clear vraagt nu om confirm() omdat seen-cache wordt gewist.
  - Toast-trigger: nieuwe `in_flight` value tussen polls → "Auto-processing &lt;file&gt;" toast. Skipt eerste poll om geen page-load toast te krijgen.

### Verificatie

- `python3 -c "import ast; ast.parse(open('app.py').read())"` → OK
- `python3 -c "import ast; ast.parse(open('watch_folder.py').read())"` → OK
- `node --check` op extracted JS → OK
- DOM-id scan: 160 → 168 (+8 nieuw, geen duplicates). Nieuwe ids: `settings-watch-banner`, `settings-watch-reset`, `settings-watch-stats`, `settings-watch-toggle`, `wf-stat-last`, `wf-stat-processed`, `wf-stat-queue`, `wf-stat-state`.

### Live test via Claude in Chrome MCP

Test-account `business+cliptest@sjuulstudios.com` werkte niet met de in HANDOVER vermelde password — fresh account aangemaakt: `business+wftest17@sjuulstudios.com` / `WatchTest17!`, user_id `c08189f0-1715-4296-903e-e912976b0665`. Plan voor live-test van Pro features ge-flipped via `supabase_admin.table('profiles').update({'plan': 'pro', ...})` omdat Stripe Checkout (`checkout.stripe.com`) browser-MCP restricted is. Helper-script voor toekomstige test-flips:

```python
from auth import supabase_admin
from datetime import datetime, timezone, timedelta
supabase_admin.table('profiles').update({
    'plan': 'pro',
    'usage_this_period': 0,
    'quota_reset_date': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
}).eq('id', '<user_id>').execute()
```

Geverifieerde gedragingen:
1. **Free plan API-gate**: `POST /api/watch-folder` met FREE plan returnt 402 met `trigger:'watch_folder'`. ✓
2. **Free plan UI-gate**: Settings toont locked card met "Upgrade to enable" ipv functional card. ✓
3. **Upgrade modal**: klik "Upgrade to enable" → modal toont "Watch a folder" titel met Pro/Studio cards (trigger-context werkt). ✓
4. **Pro plan UI**: na flip naar PRO toont functional card met status-row "● Idle | Last check — | Queue | Auto-processed" en alleen "Choose folder" knop (rest hidden, dankzij scoped `[hidden]{display:none!important}` fix). ✓
5. **Folder configureren**: POST `/api/watch-folder` met absolute path → daemon-state opgeslagen in `watch_folder.json` met user_id-binding. Status-row springt naar "● Watching | Last check just now | Queue 0 | Auto-processed 0". ✓
6. **Daemon pickup**: drop `test_video.mp4` (2 MB, 320x240 black + 120s sine wave) → log toont `watch_folder: started job 16274f43 for .../_watch_test/test_video.mp4` binnen één tick (≤5s). ✓
7. **Job-flow**: daemon riep `_process_job` aan via injected dep. Job draaide door tot `process_clips` waar het crashte op een pre-existing bug `ValueError: max_workers must be greater than 0` (gebeurt als analyzer 0 clips vindt — een silent black video). Daemon merkte `status != done`, schreef `last_error` en `errors_total += 1`. ✓
8. **Error banner**: UI toonde red banner met "Job 16274f43 for test_video.mp4 did not finish cleanly." onder de status-row. ✓
9. **Pause-knop**: klik "Pause watching" → toast "Watching paused", state dot grijs + "Paused", knop wordt "Resume watching", Re-scan grijs/disabled, sub-line "Watching is paused. Resume to keep auto-processing new drops." ✓
10. **Resume-knop**: klik "Resume watching" → toast "Watching resumed", dot terug groen + pulsing, "Pause watching" terug, Re-scan re-enabled. ✓
11. **Stop watching**: clear-knop met confirm() → seen-cache + queue gewist, UI terug naar "Not configured" met enkel Choose-knop zichtbaar. ✓

Daemon-tunables in `watch_folder.py` zijn module-attributes (overridable via env vars):
- `WATCH_TICK_SECONDS=5` — folder scan-interval
- `WATCH_QUIET_SECONDS=4` — file moet die tijd onveranderd zijn voor pickup
- `WATCH_HASH_PREFIX_MB=1` — bytes voor SHA-256 dedupe-hash
- `WATCH_MAX_QUEUE=20` — max files terug naar UI in status

### Pre-existing bug zichtbaar geworden — niet door watch-folder veroorzaakt

`cutter.process_clips:731` doet `ProcessPoolExecutor(max_workers=max_workers)` waar `max_workers` 0 wordt als analyzer 0 clips vindt. Crasht met `ValueError`. Was er al voor mijn changes, maar live-testen van watch-folder maakt het zichtbaarder omdat de daemon ook lege/silence files kan pakken. **Voorgestelde fix** voor volgende sessie:

```python
# cutter.py vlak voor ProcessPoolExecutor:
if not clips:
    return []
max_workers = max(1, min(max_workers, len(clips)))
```

Niet kritiek — daemon vangt het netjes op via `last_error` + `errors_total`. Maar voor een echte Pro-launch wil je dat een lege upload óf netjes faalt óf wordt geweigerd ná validatie (geen clips = "no drops detected").

### Cleanup

`_watch_test/` folder + temp mp3/mp4 verwijderd. `watch_folder.json` gewist. Fresh-test account `business+wftest17@sjuulstudios.com` blijft staan in Supabase met `plan='pro'` — kan worden hergebruikt voor toekomstige tests of door Sjuul verwijderd via Supabase Dashboard.

### Backups (chronologisch deze sessie)

```
app.py.pre-phase5-watchfolder.bak
static/index.html.pre-phase5-watchfolder.bak
```

### VOLGENDE SESSIE — kies één

1. **`cutter.process_clips` zero-clips fix** — pre-existing maar nu zichtbaar via watch-folder. Klein (~5 regels in cutter.py + maybe een early-return in `_process_job` met `status='error'` reason `'no_clips_detected'`).
2. **VIDEO_EDITOR_PLAN Phase 5: Filmstrip on Video Track** — ffmpeg-thumbnails op video-track bij bar/frame zoom. Backend `/api/filmstrip/<job>/<clip>` + frontend canvas draw. High visual impact.
3. **VIDEO_EDITOR_PLAN Phase 7: Inline clip-expand** — Adjust-knop op dashboard cards. Hoogste UX-waarde.
4. **VIDEO_EDITOR_PLAN Phase 8: Export presets** — TikTok / Reels / Shorts / Square dropdown. Klein, snel.
5. **VIDEO_EDITOR_PLAN Phase 9: Split tool** — scissor toggle + `/api/split` endpoint (al bestaand).
6. **VIDEO_EDITOR_PLAN Phase 10: Spectrogram mode** — backend librosa.stft PNG render. Visueel impressief.
7. **Stripe live mode + landing-page DNS verificatie** — vóór launch. Vereist Sjuul-input.
8. **Code signing / app icon / Windows test / demo video** — geparkeerd in memory, voor een polish-sessie.

---

## SESSIE 16 — vier geparkeerde features afgewerkt (2026-05-10)

Volgorde uitgevoerd: 5c → 5b → 5d → 6. Alle wijzigingen live-getest in Chrome op test-account, jobId `59a424ac` (Ediine x Ho_r Berlin, 33 clips). Geen console-errors over alle vier features samen.

### 5c — Background-analyse pill + "Terug naar processing"

`static/index.html`. Pure frontend, ~95 regels. Backup: `static/index.html.pre-5c-bgpill.bak`.

- Nieuwe sidebar-pill `<div id="bg-process-pill">` tussen de brand-row en de "Workspace" label. Toont set-naam, fase + percentage ("Beats · 42%"), gold progress-bar, en een "↗ Back to processing" CTA.
- CSS: amber gradient + pulsing dot animation (`@keyframes bg-pill-pulse`), zelfde palette als de bestaande `.upgrade` card.
- STATE-velden: `progressJobId`, `progressPct`, `progressPhase`, `progressName`. Single source of truth — pill is alleen visible als `STATE.progressJobId && STATE.view !== 'processing'`.
- Helpers: `setBgProcessPill()` (idempotent), `_clearBgProcessPill()`, `bgProcessPillClick()` → `setActiveJobId + switchView('processing')`.
- Hooks in `openProgressStream(jobId)` (set jobId + best-effort name uit STATE.history), `applyUpdate(data)` (track pct/phase/name op elke tick), terminal branches done/error/404 (clear), en `switchView` (re-evaluate op elke nav).
- Live test: triggerde STATE.progressJobId via JS, navigeerde naar Library → pill verscheen met juiste tekst, click → ging naar processing-view + pill verdween, _clearBgProcessPill() → pill weg.

### 5b — Stretch-handles draggable op mini-map

`static/index.html`. Pure frontend, ~140 regels. Backup: `static/index.html.pre-5c-bgpill.bak` (cumulatief — was hetzelfde bestand).

- Drie nieuwe DOM-nodes binnen `#tl-minimap`: `tl-mini-trim-band` (lichte gold wash tussen handles), `tl-mini-trim-in`, `tl-mini-trim-out` (gold vertical bars met grip-marker).
- CSS klasse `.tl-mini-trim` met `transform:translateX(-50%)` zodat de positie-percentage exact het midden van de handle is. z-index 6 boven het tl-mini-window zodat een drag op een handle die toevallig over de viewport-rectangle valt, alsnog wint.
- Helper `placeMiniTrimHandles()`: zelfde coord-conventie als de hoofd-handles (`relSecToPct(t.inSec, map)`). Idempotent — gebruikt voor de eerste render én tijdens drag-mousemove.
- `bindMinimapTrim()`: drag-listeners idempotent gebound via `mini.dataset.minitrimbound`. Mousemove gebruikt zelfde clamp + snap als de hoofd-handles. Op mousemove: `renderTrimRegion(drag.map.clipDur)` om hoofdrij te updaten + `placeMiniTrimHandles()` om mini-rij te updaten. Op mouseup: `saveTrimState` met dezelfde localStorage-key (`clipLive.trim.<job>.<idx>`) als de bestaande hoofdhandle-flow.
- Hooks: `placeMiniTrimHandles()` aangeroepen aan einde van `renderMinimap()`, in de `place()` helper van `renderTrimRegion`, en in de hoofdhandle-mousemove zodat de mini-rij ook tijdens hoofd-drag mee-updates. Click-outside-window in `bindMinimap` skipt nu `.tl-mini-trim` en `.tl-mini-trim-band` zodat een snelle drag door de band-edge geen pan-jump triggert.
- Live test: dragged mini-in-handle van 781px naar 560px → `STATE.trim.inSec` werd -28.26 (stretch-left), main + mini beide op 22.397%. Vervolgens mini-out-handle van 956 naar 1200 → outSec=50.23 (stretch-right), beide rijen op 77.778%. Persistentie naar localStorage geverifieerd: `clipLive.trim.59a424ac.1` bevat de nieuwe in/out.

### 5d — 1:1 aspect-ratio render-bug

`app.py` `/api/derive/<job_id>`. Backup: `app.py.pre-5d-1to1-fix.bak`.

- Root cause: oude crop-filter `crop='ih*1:ih':'(iw-ih*1)/2':0,scale=1080:1080` gaat ervan uit dat de bron landscape is (iw ≥ ih). Wanneer de enige beschikbare bron-variant de vertical 9:16 cut is (iw=1080, ih=1920), vraagt het filter een crop-width van ih=1920 uit een iw=1080 frame en gaat `(iw-ih)/2` negatief → ffmpeg knalt op `Failed to configure input pad on Parsed_crop_0`. Frontend kreeg "Could not render 1:1: ffmpeg failed".
- Fix: filter-uitdrukkingen die ALTIJD passen bij elke source-aspect:
  - 1:1 → `crop=min(iw\,ih):min(iw\,ih):(iw-min(iw\,ih))/2:(ih-min(iw\,ih))/2,scale=1080:1080`
  - 4:5 → `crop=min(iw\,ih*0.8):min(iw/0.8\,ih):(iw-min(iw\,ih*0.8))/2:(ih-min(iw/0.8\,ih))/2,scale=1080:1350`
  - Komma's binnen `min()` zijn ge-escaped met `\,` zodat ffmpeg ze niet als filter-chain separator parseert.
- Bonus: error-response is nu structured (`reason`: `crop_failed` / `codec_failed` / `ffmpeg_failed` / `timeout`) en bevat `target_size` voor debug.
- Sandbox-test: vertical 1080×1920 → 1080×1080 square ✓ ; vertical → 1080×1350 4:5 ✓ ; landscape 1280×720 → 1080×1080 ✓.
- Live test: `/api/derive/59a424ac` POST `{clip_index:1, ratio:'square'}` → 200 `{filename:"...drop_square.mp4", cached:false}`. Na clicken op 1:1 in de ratio-rail: `STATE.editorRatio="1:1"`, video-src wijzigt naar `_drop_square.mp4`, stage `aspect-ratio:1/1`, geen toast. 4:5 ook getest, ook OK.

### 6 — Unify upload UX

`static/index.html`. Backup: `static/index.html.pre-6-unify-upload.bak`.

- Tile "Open large file (no copy)" verborgen via `style="display:none"` + `id="source-large-file"`. Functie + modal blijven gewired voor power-users (`openLocalPathPicker()` vanuit console) en voor de auto-fallback hieronder.
- Constante `LARGE_FILE_THRESHOLD_BYTES = 4 * 1024**3` (4 GB). Zit tussen typische HD-set (≤2 GB) en 4K60 marathons (8+ GB).
- `uploadFile(file)` checkt nu `file.size` vóór de upload-poging:
  - `≤ 4 GB` → `/api/upload` (server-side copy, zoals voorheen).
  - `> 4 GB` → `openLocalPathPicker({reason:'large_file_auto_route', fileName, fileSize})` — modal opent met contextuele banner i.p.v. de generic title.
- `openLocalPathPicker(ctx)` accepteert nu optioneel een ctx-object. Bij `reason==='large_file_auto_route'`:
  - Title wordt "This file is too large for browser upload"
  - Nieuwe `#lp-context` div toont `<filename> · <size> is over the 4.0 GB browser limit. Paste its absolute path on disk below — Clip Live will analyse it in place, no copy needed.`
  - Default desc verbergt zich; placeholder vult `e.g. /Users/yourname/.../<filename>` in.
  - Zonder ctx (manual call) blijft alles op de oorspronkelijke "Open large file (no copy)" weergave — backwards-compat.
- CSS: `.lp-context` met amber wash matchend met de modal-style.
- Drag-drop, body-level drop, "Choose file", "browse files" link en file-input change-handler routen allemaal door uploadFile() en zijn dus automatisch covered.
- Live test: hard-reloaded, source-large-file display=none geverifieerd. Faked `File{size:6 GB}` → uploadFile() opende modal met juiste title + context-banner. Faked `File{size:100 KB}` → routing-branch koos `normal_upload`. Manual `openLocalPathPicker()` toont oude UI met default title + desc.

### Verificatie totaal

- `python3 -c "import ast; ast.parse(open('app.py').read())"` → OK
- `node --check` op extracted JS → OK
- DOM-id scan: 160 unieke ids (was 148 vóór SESSIE 16, +12), geen duplicates
- Bestandsgroottes: `app.py` 149.344 → 151.743 bytes (+2.399). `static/index.html` 320.097 → 344.775 bytes (+24.678).
- Console errors over de hele Chrome-sessie: 0
- Final smoke-test (1 chat-batch, alle 4 features achter elkaar):
  - 5c: pill renders met "Compose · 78%", `_clearBgProcessPill()` verbergt
  - 5b: mini-handles op 42.337% / 57.663%, band 15.326% — sync met hoofdrij
  - 5d: `/api/derive` square POST → 200 cached:true (re-test van eerder gecreëerde file)
  - 6: 5 GB faked file → modal opens met "This file is too large for browser upload" + ctx banner

### Backups (chronologisch deze sessie)

```
static/index.html.pre-5c-bgpill.bak       (5c + 5b cumulatief; beide pure frontend)
app.py.pre-5d-1to1-fix.bak                (5d backend)
static/index.html.pre-6-unify-upload.bak  (6 frontend)
```

### Nieuwe helper

`dj-clip-cutter/_restart.sh` — één-shot restart-script dat PATH zet voor osascript's minimal shell, oude `python.*app.py 5555` killt, en een nieuwe Flask via `nohup … &` start. Aangeroepen vanuit Claude in Chrome / `osascript` workflows omdat workspace-bash in een sandbox draait en de Mac-Python niet kan bereiken. Voor Sjuul handmatig nog steeds gewoon `./start.sh` gebruiken.

### VOLGENDE SESSIE — kies één

1. **VIDEO_EDITOR_PLAN Phase 5: Filmstrip on Video Track** — ffmpeg-thumbnails op video-track bij bar/frame zoom. Backend `/api/filmstrip/<job>/<clip>` + frontend canvas draw. High visual impact.
2. **VIDEO_EDITOR_PLAN Phase 7: Inline clip-expand** — Adjust-knop op dashboard cards → compact inline editor zonder full editor te openen. Hoogste UX-waarde.
3. **VIDEO_EDITOR_PLAN Phase 8: Export presets** — TikTok / Reels / Shorts / Square dropdown op Save. Klein, snel.
4. **VIDEO_EDITOR_PLAN Phase 9: Split tool** — scissor toggle + `/api/split` endpoint (al bestaand).
5. **VIDEO_EDITOR_PLAN Phase 10: Spectrogram mode** — backend librosa.stft PNG render. Visueel impressief.
6. **paid-architecture Phase 5: Watch-folder backend** — Pro-tier daemon (5s tick poller, watch_folder.json state, 402 quota-respect, concurrency hash-check). Launch-blocker voor Pro-tier.
7. **Stripe live mode + landing-page DNS verificatie** — vóór launch.
8. **Code signing / app icon / Windows test / demo video** — geparkeerd in memory, voor een polish-sessie.

---

## SESSIE 15 — marathon UX-/recut-/storage-fix-sessie (2026-05-10)

Twaalf+ fixes plus vier features geparkeerd. Alles end-to-end live geverifieerd via Claude in Chrome (logged in als `business+cliptest@sjuulstudios.com`). Sjuul reset de server tussendoor; Claude testte zelfstandig.

### Wat is er gedaan

**Bug 1b round-2 — Recent Sets strikt op snapshot.json (`app.py`)**
- Eerdere `_history_entry_is_loadable` accepteerde nog `output_dir + ≥1 mp4` — te losjes; oude /tmp restjes bleven zichtbaar. Nu: ALLEEN `_load_job_snapshot(jid) is not None`. Backups: `app.py.pre-bug1b-r2.bak`, `static/index.html.pre-bug1b-r2.bak`.

**Active highlight in sidebar (`static/index.html`)**
- `switchView` toggelt nu alleen `.active` op hardcoded items via `data-view`. Recent-set items (allemaal `data-view='dashboard'`) krijgen active alleen als `data-job === STATE.jobId`. Voorheen lichtten alle 5 recent items op zodra je naar dashboard switchte.

**Library 16:9 + 9:16 beide (`static/index.html`)**
- `startExport()` skipt de aspect-picker modal en stuurt altijd `aspects: ['landscape', 'vertical']`. Library Exports filter chips (9:16/16:9/All) doen het kiezen. Backup: `static/index.html.pre-aspect-zip-fix.bak`.

**★ ZIP knop — disabled state + tooltip + empty-zip protection (`app.py` + `static/index.html`)**
- Frontend: nieuwe `toggleFavZipState()` die `.is-disabled` class + tooltip toggelt op basis van `STATE.clips.some(c => c.favorite)`. Aangeroepen na `toggleFavorite` (Dashboard én Editor) en in `bindDl` initial bind. CSS `.btn.is-disabled{opacity:.45;cursor:not-allowed}`.
- `bindDl` herschreven van naïeve `<a href>` click → `fetch + blob` zodat 4xx-responses zichtbaar worden in een toast i.p.v. stilletjes een lege/error-file te downloaden.
- Backend `download_favorites`: telt copied count, returnt 400 JSON met `'no_rendered_files'` reason als 0 — voorkomt 0-byte zip die macOS Archive Utility niet kan openen.
- Backend `download_all`: nieuwe `_dir_has_any_mp4` pre-check, 400 JSON als output-dir leeg. Backup: `app.py.pre-zip-empty-fix.bak`.

**Backbutton in editor (`static/index.html`)**
- `<button class="ed-back-btn">` toegevoegd aan `.crumbs` met chevron-left SVG + label "Clips" + `onclick="switchView('dashboard')"`. CSS-stijl matcht `.ed-tools .t` weight. Backup: `static/index.html.pre-backbutton.bak`.

**Stretch-recut bug — fix 1 (`static/index.html`)**
- Logica omgekeerd in `editorTrimAtPlayhead`: was `if (hasBand && isStretch) → recut`. Nu `if (isStretch) → recut` als eerste branch ongeacht hasBand. Single-handle stretch (één kant naar buiten, andere onaangeroerd) viel voorheen door naar `else { split-at-playhead }` → recut werd nooit getriggerd. Backup: `static/index.html.pre-stretch-recut-fix.bak`.

**/api/recut hardener (`app.py`)**
- Catch-all `except Exception` → JSON `{"error": "TypeName: message", "reason": "recut_internal_error"}` ipv HTML 500.
- Pre-checks: `clip_index` in `results` OF `clips` (lazy-render dekking), `video_path` exists, `end > start`, `end ≤ source_duration`. Returnt 400/404 JSON met `reason`.
- Promoot lazy clips automatisch van `clips` naar `results` na succesvolle recut.
- Persist snapshot direct na recut zodat de nieuwe range een server-restart overleeft.
- Backup: `app.py.pre-recut-hardener.bak`.

**Trim-state persistence over logout (`static/index.html`)**
- Nieuwe helpers `saveTrimState/loadTrimState/clearTrimState` met localStorage key `clipLive.trim.<jobId>.<clipIndex>`.
- Save bij elke drag-mouseup; restore in `renderTrimRegion` bij heropenen; clear na succesvolle recut.
- Bug-fix: `renderEditor` had een tweede STATE.trim-init op regel 4302 die de restore in `renderTrimRegion` overrulede. Nu consulteert die ook eerst loadTrimState. Backup: `static/index.html.pre-trim-restore-fix.bak`.

**UPLOAD_DIR + OUTPUT_DIR persistent (`app.py`)**
- Was `tempfile.gettempdir()/dj-clip-cutter/{uploads,output}` — macOS wist `/tmp` regelmatig → bron-video weg → recut onmogelijk.
- Nu `BASE_DIR/{uploads,output}` (project-relatief, persistent over reboot).
- Eenmalige `_migrate_legacy_tmp_storage()` runt at-import: verhuist bestaande items uit /tmp/dj-clip-cutter/ naar de nieuwe locatie + herschrijft `video_path` in alle on-disk job snapshots zodat oude jobs ook recutbaar blijven. .gitignore uitgebreid met `uploads/`. Backup: `app.py.pre-storage-persistent.bak`, `.gitignore.pre-storage.bak`.

**Source-video persistence (`app.py`)**
- `_cleanup_source_video` → no-op (was: delete bron-mp4 na done). Stub blijft voor toekomstige opt-in cleanup-UI.
- `_purge_old_uploads` → alleen `.wav` analyse-files; mp4 bron-videos blijven staan over server-restart.
- `_persist_job_snapshot` behoudt nu `video_path` (was: gestript omdat /tmp paths niet overleefden — nu UPLOAD_DIR persistent is, paths ook). Backup: `app.py.pre-source-persist.bak`.

**Read-only marker voor view-only sets (`app.py` + `static/index.html`)**
- Backend `/api/status` returnt `recut_capable: bool` + `recut_blocked_reason: 'video_path_missing'|'source_file_gone'|null`. Capable iff `video_path and os.path.exists(video_path)`.
- Frontend: `STATE.recutCapable`, helper `setEditorReadonly(blocked, reason)` toggelt `.is-disabled` op alle `.ed-recut-btn` (Trim big + Trim toolbar + Split toolbar — IDs `ed-trim-big`, `ed-trim-toolbar`, `ed-split-toolbar`). Tooltip wisselt van "Trim — split clip at playhead" naar "View-only — re-upload to enable trim/stretch". CSS `.tool-btn.is-disabled` + `.btn.is-disabled` opacity .4–.45.
- `editorTrimAtPlayhead` + `editorSplit` pre-check: `if (STATE.recutCapable === false) → toast + return`. Geen 500 meer voor oude jobs zonder bron. Backup: `app.py.pre-readonly.bak`, `static/index.html.pre-readonly.bak`.

**Recent Sets / Library refresh na nieuwe upload (`static/index.html` + `app.py`)**
- Backend `_history_entry_is_loadable`: race-safety toegevoegd. Accepteert ook in-memory jobs met status='done'/'ready' wanneer snapshot nog niet gepersisteerd is — zo verschijnt een verse upload meteen in /api/history.
- Frontend: helper `refreshHistoryFromServer()` (returnt true als de id-lijst wijzigde, rendert sidebar opnieuw). `switchView('home')` en `switchView('dashboard')` triggeren een fetch + selectieve re-render. Backup: `app.py.pre-recent-refresh-fix.bak`.

**Pauze-knop bij Volgende clip (`static/index.html`)**
- Nieuwe `_resyncEditorPlayState()` na renderEditor in `editorPrev/Next`: forceert `setEditorPlayBtnIcon(false)` + `.is-paused` op stage als de nieuwe clip pauzed is. Voorheen bleef de pauze-icon op de play-btn staan tot de nieuwe video een 'play' event vuurde.

**Trim loading-bar overlay (`static/index.html`)**
- Nieuw element `#ed-trim-loading` (positioned `fixed`, `bottom:96px`, amber border) met indeterminate slider-animatie + "Trimming…" label. CSS-keyframes `ed-trim-slide`. Helper `_showTrimLoading(on)` toggle in `editorTrimAtPlayhead` (try → false in `finally`).

**Blade-icon + amber cursor op Trim (`static/index.html`)**
- Beide Trim-knoppen (`ed-trim-big`, `ed-trim-toolbar`) krijgen razor-blade SVG (rechthoek + v-inkepingen + 2 stippen). Class `.ed-blade-btn`.
- Hover: `cursor: url('data:image/svg+xml;…') 14 14, pointer` — amber blade SVG als cursor. Plus inset amber shadow + scale(.96) op active. Backup: `static/index.html.pre-feedback-batch.bak`.

**Sort newest-first + View all expand (`static/index.html`)**
- `renderSidebarRecent`: was `slice(0, 5)` (oudste). Nu `slice(-5).reverse()`.
- `renderHome`: was `slice(0, 6)`. Nu `STATE.history.slice().reverse()` met `STATE.libraryShowAll` toggle die alle entries laat zien.
- "View all →" link is nu een `<a id="home-projects-toggle" onclick="toggleLibraryShowAll()">`. Toggles tussen "View all →" en "← Show fewer". Backup: `static/index.html.pre-sort-viewall.bak`.

### Live test resultaten (via Claude in Chrome)

Voor alle bovenstaande fixes is een echte Chrome-tab gebruikt (logged in als test-account, jobId `59a424ac` = nieuwe Ediine x Ho_r Berlin upload met 33 clips, 55 min):
- Stretch IN-handle 5s naar links → klik Trim → toast "Recut to 00:00:21.72" → clip 1 ging van 16.72s naar 21.72s → file timestamps op disk bevestigen herrender (17:39).
- Sidebar Recent Sets toont Ediine bovenaan na refresh, andere oude sets daaronder.
- Library Recent projects: Ediine eerste card.
- View all knop expand naar 19 projects, label wordt "← Show fewer".
- ★ ZIP knop is dim wanneer `STATE.clips.some(c => c.favorite)` false is, tooltip "Mark some clips as ★ favourite first".
- Trim-knop voor oude /tmp jobs (zoals Don Diablo `46716f96`) is dim, tooltip "View-only — this set was processed before persistent storage."
- Snap toggle cycelt Off → Beat → Bar → Off, knop wordt amber, toast "Snap: beat" / "Snap: bar".
- Loop button toggle, console log `STATE.loopEnabled = true`, knop amber.

### Verificatie

- `python3 -c "import ast; ast.parse(open('app.py').read())"` → OK.
- Inline JS via `node --check` → OK.
- DOM-ids: 148 unieke (was 141 vóór SESSIE 14 → 144 na SESSIE 14 → 148 nu), geen duplicates. Nieuwe ids: `ed-back-btn`, `ed-trim-big`, `ed-trim-toolbar`, `ed-split-toolbar`, `ed-trim-loading`, `home-projects-toggle`.
- Bestanden: `app.py` 138.351 → 149.344 bytes (+10.993). `static/index.html` 290.431 → 320.097 bytes (+29.666).

### Backups (chronologisch deze sessie)

```
app.py.pre-bug1b-r2.bak
static/index.html.pre-bug1b-r2.bak
static/index.html.pre-stretch-recut-fix.bak
static/index.html.pre-aspect-zip-fix.bak
app.py.pre-zip-empty-fix.bak
static/index.html.pre-zip-empty-fix.bak
app.py.pre-recent-refresh-fix.bak
static/index.html.pre-backbutton.bak
app.py.pre-recut-hardener.bak
static/index.html.pre-trim-persistence.bak
static/index.html.pre-trim-restore-fix.bak
app.py.pre-storage-persistent.bak
.gitignore.pre-storage.bak
app.py.pre-source-persist.bak
app.py.pre-readonly.bak
static/index.html.pre-readonly.bak
static/index.html.pre-feedback-batch.bak
static/index.html.pre-sort-viewall.bak
```

### VOLGENDE SESSIE — vier geparkeerde features

In de volgorde die Sjuul aangeeft (geen vaste prio):

1. **5b — Stretch-handles ook draggable op mini-map** (~150 regels frontend). De mini-map onder de waveform toont nu alleen de viewport-positie. Voeg twee handles toe (zelfde gold-style als hoofd-tracks), bind drag-listeners die STATE.trim updaten via dezelfde `pxToVirtSec`-coordinate helper. Bestaande hoofd-handles blijven werken. Risk: laag.

2. **5c — Achtergrond-analyse pill + "Terug naar processing"** (~80 regels frontend, geen backend). Persistent badge bovenin de sidebar wanneer een job in-memory met status='processing' bestaat. Klik → `switchView('processing')` met juiste jobId. Pollt /api/status elke 3s. Risk: laag.

3. **5d — 1:1 aspect-ratio render bug** (backend ffmpeg arg, plus catch + nette toast). Bij klik op "1:1" in editor preview aspect-rail toast "Could not render 1:1: ffmpeg failed". Onderzoeken welke filtergraph faalt — waarschijnlijk crop berekening. Risk: middel (vereist ffmpeg-debug).

4. **6 — Unify upload UX** (zie eerdere follow-up #5 voor volle uitleg). Eén intake-knop die op basis van `file.size` automatisch routeert tussen `/api/upload` en `/api/upload-local`. Verberg "Open large file (no copy)" knop. Risk: middel (drag-drop vs picker pad).

Werk volgens de "werk zelfstandig" instructie in de START PROMPT — gebruik Chrome MCP om je eigen werk live te valideren tussen stappen. Maak per stap een backup, parse-check, DOM-id scan, en een korte test-flow voor elke fix.

---

## SESSIE 14 — Bug 1a + 1b + VIDEO_EDITOR_PLAN Phase 3, 4 (snap), 6 (loop) (2026-05-10)

Vijf changes in één sessie. Alle pure frontend behalve Bug 1b (één `/api/history` filter in `app.py`). Geen breaking change op bestaande state shape, alleen toegevoegde STATE-velden + helpers.

### Wat is er gedaan

**Bug 1b — Recent Sets filter (`app.py`, +30 regels)**
- Nieuw `_history_entry_is_loadable(jid)` helper: returnt True als snapshot.json bestaat OF output_dir bestaat met ten minste 1 .mp4. Geen side-effects.
- `/api/history` endpoint filtert nu at-request-time. Sidebar toont nooit meer entries die op een 404 zouden landen.
- Backwards-compat: rehydrate-pad onaangeroerd. Filter is strikter dan alleen `output_dir_exists` (eist ook clip-files), wat Sjuuls oude pre-snapshot rommel uit de zicht haalt.
- Backup: `app.py.pre-bug1b.bak`.

**Bug 1a — Hard-reload jobId restore (`static/index.html`)**
- Nieuwe helper `setActiveJobId(jobId)` + `loadActiveJobId()` (~20 regels) — persist STATE.jobId in `localStorage.clipLive.activeJobId`.
- Vier callsites omgezet: `closeLocalPathPicker → setActiveJobId`, `uploadFile → setActiveJobId`, `openExportInEditor → setActiveJobId`, `openJob → setActiveJobId`. `forgetJob` clear's de pointer als 'ie de huidige was.
- `openJob`-catch (404 / netwerk) clear't óók de pointer zodat een hard-reload niet eindeloos in een missende job blijft hangen.
- `postLoginBoot()` checkt na `STATE.history` of de saved jobId nog loadable is (= staat in de gefilterde history van bug 1b). Zo ja → `openJob(saved)` ipv default `switchView('upload')`. Zo nee → clear pointer, ga upload in.
- Backup: `static/index.html.pre-bug1b.bak`.

**Phase 6 — Loop playback (`static/index.html`)**
- Nieuwe knop in `.tl-toolbar .c` (rechts naast Next, met `tl-divider`): `#tl-loop-btn` met loop-iconen SVG, klassen `loop-btn`. CSS: `.tl-toolbar .loop-btn.is-on` → amber wash + ring (matchend met play-knop accent).
- State: `STATE.loopEnabled = false`.
- Functies: `editorToggleLoop()`, `setLoopBtnState(on)`, `bindEditorLoopHandler()`. Listener idempotent gebound op `#ed-video.dataset.loopbound`. Reads `STATE.loopEnabled` + `STATE.trim` op elke `timeupdate` tick — toggle werkt at-runtime zonder rebind.
- Wrap rule: `currentTime >= clamp(outSec) - 0.01` → `currentTime = clamp(inSec)`. Tweede listener op `'ended'` (voor het geval outSec voorbij `video.duration` ligt door stretch).
- Wire-in: `bindEditorLoopHandler()` + `setLoopBtnState(STATE.loopEnabled)` direct na `bindStagePlayToggle()` in renderEditor.
- Backup: `static/index.html.pre-phase6.bak`.

**Phase 3 — J/K/L scrubbing (`static/index.html`)**
- Module-scope state: `_jklSpeed` (-4..0..4), `_jklRAF`, `_jklRAFLast`, `_jklKHeld`, constant `_JKL_FRAME = 1/30`.
- `_jklSetSpeed(speed)`:
  - `0` → pause + playbackRate=1 + cancelAnimationFrame.
  - `>0` → playbackRate=speed + play (native forward speed).
  - `<0` → pause + rAF loop dat `currentTime` decrementeert per delta-tijd (HTML5 video heeft geen native reverse).
- `_jklStepFrame(dir)` → 1/30s nudge in de gevraagde richting, na een `_jklSetSpeed(0)` om eventuele scrub te stoppen.
- `bindEditorJKL()` (idempotent via `window._jklBound`):
  - `keydown` filter: editor-active, geen input/textarea, geen modifiers, geen `e.repeat`.
  - `J` → speed -1 → -2 → -4 (vanaf 0/+).
  - `L` → speed +1 → +2 → +4 (vanaf 0/-).
  - `K` → set `_jklKHeld=true`, speed=0.
  - `K+J` / `K+L` (terwijl K nog vast) → frame-step.
  - `keyup` op K → `_jklKHeld=false`.
  - `window blur` → reset alles (anti-strand-in-4×).
- Aangeroepen vanuit `bindGlobalKeyboard()` zodat het niet conflicteert met de bestaande spacebar-handler (die checkt al editor-active + niet-input).
- Backup: `static/index.html.pre-phase3-jkl.bak`.

**Phase 4 — Snap modes Off / Beat / Bar (`static/index.html`)**
- State: `STATE.snapMode='off'`, `STATE.beatTimes=[]`, `STATE.barTimes=[]`. beatTimes/barTimes worden gevuld vanuit `status.bpm` (al door analyzer geleverd: `{bpm, beat_times, bar_times}`) wanneer de editor laadt.
- HTML: snap-toggle button `#tl-snap-toggle` in `.tl-toolbar .l` (na zoom-slider + tl-divider). Cycle Off → Beat → Bar → Off. Label `#tl-snap-lbl` updatet mee.
- CSS: `.tl-toolbar .snap-toggle` ghost style + `.is-on` amber wash. `.timeline.is-snapping .trim-handle` krijgt `cursor:cell` als magnet-affordance.
- Functies:
  - `cycleSnapMode()` — toolbar onclick.
  - `setSnapMode(mode, silent)` — externe entry. `silent=true` skipt toast (voor renderEditor re-sync).
  - `_snapGridForMode(mode)` — beatTimes/barTimes met fallback: synthetisch grid uit `setBpm + setDuration` als analyzer geen array meegaf.
  - `_nearestInSortedArray(arr, target)` — binary search.
  - `snapRelSec(relSec, clip, thresholdSec)` — converteert naar set-time, snapt, terug naar clip-relative. Returnt input ongewijzigd als geen grid of buiten threshold.
- Mousemove integration in `renderTrimRegion`: na `relSec = pxToVirtSec(...) - leftMax`, snapt de relSec via `snapRelSec` met threshold = 8px / pxPerSec (rect.width / map.vDur). Bestaande clamps (Math.max/Math.min op stretch-bounds) blijven daarna van toepassing.
- Wire-in: `setSnapMode(STATE.snapMode || 'off', true)` aan einde van renderEditor (idempotent UI re-sync).
- Backup: `static/index.html.pre-phase4-snap.bak`.

### Wat NIET veranderd is

- Phase 1-3 paid-architecture, deelstap 1, 2a, 2b, 2c, 2d, S4.1, S4.2 — onaangeroerd.
- Bestaande spacebar handler — onaangeroerd; J/K/L is een aparte listener.
- Stretch-zone CSS, mini-map, drag-clamping logica — onaangeroerd.
- `/api/history` snapshot-pad blijft 1:1 hetzelfde — alleen de output-filter is nieuw.

### Verificatie

- `python3 -c "import ast; ast.parse(open('app.py').read())"` → OK.
- `awk '/<script>/{flag=1;next} /<\/script>/{flag=0} flag' index.html | node --check` → OK.
- DOM-id scan: 144 unieke ids (was 141, +3: tl-loop-btn, tl-snap-toggle, tl-snap-lbl), geen duplicates.
- Bestandsgroottes: app.py 138.351 → 139.463 bytes (+1.112). index.html 290.431 → 307.794 bytes (+17.363).
- **Sjuul-handmatige test nog te doen** — zie smoke-tests hieronder.

### Smoke-tests voor Sjuul (na server-restart)

Server herstarten:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
./start.sh

Browser: http://127.0.0.1:5555

**Bug 1b — Recent Sets**
- Open de sidebar links. De oude pre-snapshot entries (24+ stuks van vorige projecten) zouden weg moeten zijn. Nieuwe entries die je vandaag hebt gemaakt blijven zichtbaar. Klikken op een recent-item moet werken zonder 404.

**Bug 1a — Hard-reload restore**
- Open een set → ga naar Dashboard of Editor → druk cmd+shift+R.
- Verwacht: na re-login (of cached session restore) land je terug op dezelfde set, niet op de Upload screen.
- Check via DevTools → Application → Local Storage: key `clipLive.activeJobId` moet de huidige jobId bevatten.

**Phase 6 — Loop playback**
- In de Editor: zet trim-handles op een interessant stukje. Klik op de loop-knop rechts in de transport-balk (na de Next-knop, naast een tl-divider) — knop kleurt amber.
- Druk play. Bij `outPoint` moet 'ie automatisch terug naar `inPoint` springen en blijven loopen.
- Klik nogmaals op loop-knop → uit, normale playback hervat.

**Phase 3 — J/K/L**
- In de Editor (niet in een tekstveld!):
  - `L` → forward 1×, nogmaals 2×, nogmaals 4×.
  - `J` → reverse 1×, nogmaals 2×, nogmaals 4× (rAF-loop, soepel).
  - `K` → pauze.
  - `K` ingedrukt houden + `J` of `L` → één frame back/forward.
- Spacebar play/pause moet nog steeds werken (geen conflict).

**Phase 4 — Snap**
- In de Editor: klik op de snap-knop links in de toolbar (na de zoom-slider + tl-divider).
- Klik 1× → "Snap Beat", knop kleurt amber, cursor over trim-handle wordt magnet-cursor.
- Sleep een trim-handle: bij elke beat-grens snap't 'ie nu binnen 8px.
- Klik 2× → "Snap Bar" (4 beats). Sleep handle: snap nu naar bar-grenzen.
- Klik 3× → "Snap Off", cursor terug normaal.

### VOLGENDE SESSIE — keuze

Phase 1 + bug-fixes klaar. Volgende interessante stappen:

1. **VIDEO_EDITOR_PLAN Phase 5: Filmstrip on Video Track** — backend `/api/filmstrip/<job>/<clip>` + frontend draws ffmpeg-thumbnails op video track bij bar/frame zoom. High visual impact.
2. **VIDEO_EDITOR_PLAN Phase 7: Inline clip-expand** — Adjust-knop op dashboard cards → compact inline editor zonder full editor te openen. Hoogste UX-waarde.
3. **VIDEO_EDITOR_PLAN Phase 8: Export presets** — TikTok/Reels/Shorts/Square dropdown op Save. Klein, snel.
4. **VIDEO_EDITOR_PLAN Phase 9: Split tool** — scissor tool toggle + `/api/split` (al bestaand).
5. **VIDEO_EDITOR_PLAN Phase 10: Spectrogram** — backend `librosa.stft` PNG render. Visueel impressief.
6. **paid-architecture Phase 5: Watch-folder backend** — Pro-feature is visueel ontgrendeld maar daemon werkt niet. Launch-blocker voor Pro-tier.
7. **Stripe live mode + landing-page DNS verificatie** — vóór launch.

---

## VOLGENDE SESSIE — keuze: bug-fix, VIDEO_EDITOR_PLAN Phase 2-7, of paid-architecture Phase 5 watch-folder

> **VIDEO_EDITOR_PLAN Phase 1 is 100% klaar** na SESSIE 13 (2d mini-map). Pad A heeft inmiddels stretch-UX, alle coord-helpers, een zoom-UI, pan/seek/framenummer, een live-preview tijdens stretch-drag, en een mini-map. Tijd om te beslissen wat er nu komt.

### Optie 1 — Bekende bugs aanpakken

Twee bugs gemeld door Sjuul tijdens SESSIE 12-13 (zie Bekende bugs tabel):

- **Clips verdwijnen na hard-reload** — diagnose nodig op rehydrate-pad of localStorage `STATE.jobId` restore. Risk: middel.
- **Recent Sets toont oude pre-snapshot jobs** — voorgesteld fix: filter op `snapshot_exists OR job_in_history_AND_output_dir_exists`. Risk: laag.

Beide niet-urgent maar wel zichtbaar in dagelijks gebruik.

### Optie 2 — VIDEO_EDITOR_PLAN Phase 6: Loop playback

Eén `ontimeupdate`-listener: bij `currentTime >= outPoint` reset naar `inPoint`. Toggle-knop in stage-controls.

- Pure frontend.
- Schatting: kleiner dan deelstap 1, ~50 regels JS + 1 knop in HTML + CSS voor button-state.
- Risico: minimaal.
- Waarde: hoog QoL — DJs kunnen een edit op repeat horen zonder iets aan te raken.

### Optie 3 — VIDEO_EDITOR_PLAN Phase 3: J/K/L scrub

`requestAnimationFrame`-loop op `scrubSpeed` state (-4..0..4). J = rewind, K = pauze, L = forward. K+J / K+L = frame-step.

- Pure frontend.
- Schatting: ~80 regels JS, 1 small UI hint.
- Risico: laag. Conflict-check met bestaande spacebar-handler.
- Waarde: middel — DJ-skim-workflow upgrade.

### Optie 4 — VIDEO_EDITOR_PLAN Phase 7: Inline clip-expand

Dashboard cards krijgen een "⚙ Adjust" knop die een compact inline editor onthult zonder naar de full editor te navigeren. Hi-res waveform + draggable handles + Re-export. Plan-volgorde noemt dit "highest user value, moderate effort".

- Pure frontend (de waveform/recut-endpoints bestaan al).
- Schatting: groot — vergelijkbaar met deelstap 1 + 2b samen, 200-300 regels.
- Risico: middel. CSS-transitions + state-isolation per card.
- Waarde: hoog — schilft 60% van de editor-bezoeken weg.

### Optie 5 — VIDEO_EDITOR_PLAN Phase 4: Snap modes (bar/beat)

Snap-toggle (Off / Beat / Bar) in tl-toolbar. Handles "klikken" naar grid-lines binnen 8px. Vereist `clip.bpm` en `clip.beat_times` (analyzer levert deze al).

- Pure frontend.
- Schatting: ~120 regels JS + CSS voor magnet-cursor.
- Risico: middel. Grid-positie berekening + visual feedback tijdens drag.
- Waarde: middel-hoog — bar-aligned cuts zijn waardevol voor DJ-content.

### Optie 6 — paid-architecture Phase 5: Watch-folder backend

De Pro-tier watch-folder is sinds Phase 3 visueel ontgrendeld maar de daemon werkt niet. Lokale folder-poller (5s tick) + `watch_folder.json` state-persist + 402-quota-respect + dynamische Settings-status. Volle uitleg staat in eerdere VOLGENDE SESSIE-blokken (zie git history of memory).

- Backend + frontend.
- Schatting: groot — 2-3 sessies werk.
- Risico: middel. Background thread + concurrency hash-checks.
- Waarde: launch-blocker voor Pro-tier (huidig: betalend product zonder werkend feature).

### Aanbeveling

**Optie 2 (loop playback)** als snelle start om weer in flow te komen, gevolgd door **Optie 1 (Recent Sets bug)** als een korte cleanup-stap. Daarna kies tussen Phase 7 (inline expand, hoogste UX-impact) of Phase 5 (watch-folder, voor launch-readiness).

### Wat we niet meer aanraken

- Phase 1-3 paid-architecture: af + getest.
- Phase 4 editor-werk (deelstap 1, 2a, 2b, 2c, 2d, S4.1, S4.2): af + getest.
- Stripe live mode — pas vóór launch.
- Code signing, app icon, Windows tests, demo video — geparkeerd (memory).

### Live stretch-preview (geparkeerd, gerelateerd)

Bij de UI-test van deelstap 1 (2026-05-09) ontdekte Sjuul dat tijdens slepen de waveform en preview-video niet uitrekken in de stretch-zone — dat gebeurt pas bij Save & Re-export (`/api/recut`). Discoverability is nu opgelost (amber wash + `±Xs` label), maar het blijft een blinde sprong. Bewust **uitgesteld tot ná Phase 1**, omdat:

- Phase 1 levert de `timeToX`/`xToTime` helpers die deze feature óók nodig heeft.
- Eerst Phase 1 → daarna live-preview voorkomt dubbele refactor.

Aanpak voor later (notitie aan toekomstige sessie):
1. Tijdens drag: waveform-data ophalen via `/api/waveform/<job>?start=...&end=...` voor de virtuele range i.p.v. de per-clip cache.
2. Preview-video swappen naar de bron-set met seek naar de virtuele positie. Bron-pad zit al in `STATE.jobId` → `/uploads/<job>/source.<ext>` (te verifiëren in `app.py`).
3. Op mouseup: terug naar de clip-cache zodat alles snel blijft buiten drag-momenten.

### Wat we niet meer aanraken

- Phase 1-3 (auth/billing/quota): af + getest. Alleen bij regressie.
- Stretch-zone CSS/JS van deelstap 1: af. Moet wel zoom-aware blijven (zie valkuilen).
- Stripe live mode — pas vóór launch.
- Code signing, app icon, Windows tests, demo video — geparkeerd (memory).
- Patent — besproken, nog niet uitgevoerd.

### Pad B (Phase 5 watch-folder) — niet vergeten, parallel beschikbaar

De watch-folder is visueel ontgrendeld maar de daemon werkt nog niet. Volle uitleg stond eerder in dit document; samengevat: lokale folder-poller (5s tick) + state-persist in `watch_folder.json` + quota-respect (402-skip) + UI-status dynamisch + concurrency hash-check. Dropbox/GDrive OAuth = parked. Pad B blijft naast Pad A schedulebaar voor later.

### Hoe te beginnen

In de volgende chat: bevestig dat je Phase 1 wil oppakken, krijg een diagnose+aanpakvoorstel, geef "ja", dan uitvoeren — net zoals deelstap 1.

---

## SESSIE 13 — Phase 4 deelstap 2d: mini-map onder de timeline (2026-05-10)

Sluit `VIDEO_EDITOR_PLAN.md` Phase 1 af. De mini-map staat altijd onder de hoofdtimeline en toont de hele virtuele duration (clip + ±60s stretch-zones) ongeacht de zoom in de hoofd-tracks. Een gold rechthoek markeert de huidige viewport — sleep om te pannen, klik buiten de rechthoek om te springen.

### Wat is er gedaan

`dj-clip-cutter/static/index.html` (281.098 → 290.431 bytes; 6239 → 6467 regels, +228 regels). Backup: `static/index.html.pre-phase4-zoom-2d.bak`.

Pure frontend. Geen backend, geen API.

**HTML** (in de `.timeline` container, vlak ná `tl-scroll`):
- `<div id="tl-minimap">` met:
  - `<canvas id="tl-mini-canvas">` voor gedimde waveform-achtergrond.
  - Twee stretch-markers `<div id="tl-mini-stretch-left/right">` proportioneel met `leftMax/rightMax`.
  - `<div id="tl-mini-window">` — gold zoom-window rechthoek.

**CSS**:
- `.tl-minimap` 24px hoog, full-width, gold-bordered.
- `.tl-mini-stretch-*` lichte amber wash matchend met deelstap 1.
- `.tl-mini-window` semi-transparant gold met grab/grabbing cursor.

**JS — vier nieuwe helpers**:
- `renderMinimap()` — orchestrator: tekent canvas + plaatst stretch-markers + sync window.
- `drawMinimapCanvas(canvas)` — devicePixelRatio-aware. Hergebruikt `buildStretchPreviewPeaks(startSet, endSet, w)` uit S4.1 voor 1 peak per pixel.
- `syncMinimapWindow()` — bereken width/left van rechthoek uit `tl-scroll.scrollLeft/scrollWidth/clientWidth`.
- `bindMinimap()` — idempotent (`dataset.minibound`, `dataset.miniscrollbound`, `window._clClipMiniResizeBound`):
  - Drag op rechthoek → `tl-scroll.scrollLeft` update via factor `scrollWidth / miniWidth`.
  - Click op mini-map buiten rechthoek → jump-scroll, click-point centraal in viewport.
  - `scroll`-event op `tl-scroll` → automatisch sync.
  - `resize`-event op window → herrender canvas + sync.

**Wire-in in `renderEditor()`**:
- `ensureWholeSetWaveformCache()` uitgebreid met `.then()` die `drawMinimapCanvas` repaint zodra prefetch landt.
- `renderMinimap() + bindMinimap()` direct daarna voor initial render + listener-binding.

### Wat NIET veranderd is

- Phase 1-3 paid-architecture, deelstap 1, 2a, 2b, 2c, S4.1, S4.2 — onaangeroerd.
- DOM-ids: 136 → 141 (+5 voor mini-map elementen). Geen dupes.

### Verificatie

- `node --check` op het inline `<script>`-blok: parse OK.
- DOM-id scan: 141 ids, allemaal uniek.
- Sjuul handmatig getest: mini-map zichtbaar onder hoofdtimeline, gold rechthoek toont viewport, slepen pant, click buiten window jumpt, sync via scroll-event werkt voor alle pan/zoom triggers (slider, wheel, ruler-drag, +/- keys, mini-map zelf), stretch-zone markers tonen amber wash. Geen JS-errors.

### Open observatie tijdens test (geen actie)

Sjuul vroeg: "wanneer ik stretch naar minder dan 0sec, klopt het dat de video nog niet gerenderd kan worden?" Antwoord: ja, maar dat is bestaand gedrag, niet nieuw door 2d. De "Clip file not yet rendered. Run a re-cut to generate this segment."-notice komt uit de lazy-render pipeline (Bucket-D2, april 2026): clips zonder `files`-veld tonen die notice tot Save & Re-export of `/api/recut` runt. Tijdens stretch-drag zelf swap't S4.2 naar `/api/source/<job>` zodat je wel beeld ziet; op mouseup gaat src terug naar de clip-file en als die niet bestaat zie je de notice. Mogelijke follow-up (geparkeerd, niet urgent): bij stretch-mouseup blijven hangen op bron-video tot user expliciet save't, i.p.v. terugswapen naar de niet-gerenderde clip-file.

---

## SESSIE 12 — Phase 4 S4.1 + S4.2: live waveform + bron-video preview tijdens stretch-drag (2026-05-10)

Lost het UX-gat op dat Sjuul flagde tijdens deelstap 1 — voorbij de clip-grens slepen was tot nu toe een blinde sprong. Met S4.1 + S4.2 zie je tijdens de drag de echte audio (waveform live geüpdatet uit whole-set cache) én de echte beelden (bron-video swap met seek naar set-time).

### Wat is er gedaan

`dj-clip-cutter/app.py` (136.571 → 138.351 bytes; +1.780 bytes). Backup: `app.py.pre-s4-2.bak`.
- **Nieuwe route `GET /api/source/<job_id>`** — streamt `job['video_path']` met Range-support (HTTP 206) zodat de HTML5 `<video>` kan seeken zonder de hele file te downloaden. Mimetype-tabel `_SOURCE_MIME_BY_EXT` voor mp4/mov/m4v/mkv/webm + audio-formats. Path-traversal safety: het pad komt uit `_get_snapshot()` (gezet door upload-handlers vanuit een vertrouwde bron), nooit uit user-input. `realpath` + `isfile` check.
- Werkt voor zowel `OUTPUT_DIR`-jobs als `no_copy` user-folder jobs (laatste: `video_path` is een absolute pad in user-folder, send_file accepteert dat).

`dj-clip-cutter/static/index.html` (274.225 → 281.098 bytes; 6088 → 6239 regels, +151 regels). Backups: `static/index.html.pre-s4-1.bak` (alleen-S4.1 rollback) en `static/index.html.pre-s4-2.bak` (volledige S4 rollback).

**S4.1 — Live waveform-preview**
- Drie nieuwe helpers vlak na de coord-helpers van 2a:
  - `ensureWholeSetWaveformCache()` — idempotente prefetch van `/api/waveform/<job>` → `STATE.wfCache.points`. Returns silent op fail; preview degradeert dan graceful naar de bestaande clip-cache.
  - `buildStretchPreviewPeaks(startSec, endSec, targetBars)` — slice op tijd, downsample naar ~240 buckets, normaliseer naar 0..1. Returns null bij lege cache of zero-range.
  - `restoreClipWaveform()` — redraw via `STATE.wfClipCache` na drag. Geen fetch.
- Wire-in in `renderEditor()`: `ensureWholeSetWaveformCache().catch(()=>{})` fire-and-forget naast de zoom/pan wiring.
- In drag-mousemove (in `renderTrimRegion`): detect `isStretch`, dan rAF-throttled `drawWaveformCanvas(wave, peaks)` via `drag._wavePreviewScheduled` flag (max 1× per frame).
- In mouseup: `restoreClipWaveform()` zet de oude clip-cache terug — instant, geen fetch.

**S4.2 — Live video-preview**
- In drag-mousemove, eerste keer voorbij grens: één-shot swap van `<video>.src` naar `/api/source/<job>`. `drag._priorVideoSrc/_priorVideoTime/_priorVideoPaused` bewaren de pre-swap state. `onloadedmetadata` seekt naar absolute set-time `clip.start + relSec`.
- Live-scrub block in mousemove gerefactored: bij `_sourceSwapped` gebruikt 'ie set-time, anders clip-time. Tijdens vervolg-drag dus alleen `currentTime` updates, geen src-swaps (= soepel).
- In mouseup: src terug naar de bewaarde clip-file URL, `onloadedmetadata` seekt naar de oude tijdpositie en hervat play als 't speelde.

### Wat NIET veranderd is

- Stretch-logica zelf (`getEditorTimeMap`, drag-clamping, `/api/recut` vs `/api/split-clip` pad bij Save) — onaangeroerd.
- Coord-helpers van 2a, zoom-UI van 2b, pan/seek van 2c — onaangeroerd.
- DOM-ids: 136 (geen wijziging — alleen JS-helpers + één backend route toegevoegd).

### Verificatie

- `python -m py_compile app.py`: OK.
- `node --check` op het inline `<script>`-blok: parse OK.
- DOM-id scan: 136 ids, allemaal uniek.
- Sjuul handmatig getest: alle functies werken, geen JS-errors. Bevestigd op 2026-05-10.

### Twee bekende bugs gemeld door Sjuul tijdens deze test (niet-urgent)

1. **Clips verdwijnen na hard-reload** — na `cmd+shift+R` zijn recent gegenereerde clips niet meer zichtbaar in de Clips-sectie. Mogelijk een job-state rehydration issue na het Phase-3 plan-gating werk (jobs hebben nu een `user_id` veld; oude job-snapshots niet, en/of de rehydrate-pad mist iets). Of een localStorage `STATE.jobId` die niet correct gerestored wordt. Verdere diagnose vereist.
2. **Recent Sets toont oude pre-snapshot jobs** — sidebar toont 5 oude entries gekoppeld aan een vorig project. Bekende bug uit SESSIE 2 ("Pre-snapshot jobs in history") — nog niet gefixed. UI-affordance "Forget" bestaat per item maar Sjuul heeft 'm niet gevonden of 't is niet duidelijk dat 't bestaat.

Beide op de bekende-bug-lijst gezet, geen actie deze sessie.

### Bekende valkuilen voor 2d

- `STATE.wfCache.points` is nu prefetched dankzij S4.1 — 2d kan dezelfde data gebruiken voor de mini-map achtergrond zonder extra fetch.
- `tl-scroll.scrollLeft` wordt al gewijzigd door 2c (ruler-pan, middle-mouse) en door zoom-rond-cursor in 2b. 2d's mini-map moet **luisteren** op `scroll`-event om gesynchroniseerd te blijven.

---

## SESSIE 11 — Phase 4 deelstap 2c: pan + zoom-aware seek + framenummer (2026-05-09)

Drie samenhangende interactiepatronen + één backend-uitbreiding voor framenummer-display. Phase 1 uit `VIDEO_EDITOR_PLAN.md` is hiermee 75% af (alleen 2d mini-map ontbreekt nog).

### Wat is er gedaan

`dj-clip-cutter/app.py` (133.812 → 136.571 bytes). Backup: `app.py.pre-phase4-zoom-2c.bak`.

- **Nieuwe helper `_parse_fps_string(value)`** — converteert ffprobe `r_frame_rate`/`avg_frame_rate` strings (`"30000/1001"`, `"30/1"`, `"24"`) naar float. Sanity-check op range 1..240. Returnt `None` bij ongeldige waardes.
- **`_validate_video_file(path)` uitgebreid** — parse't tijdens de bestaande ffprobe-call de eerste video-stream's `r_frame_rate` (met `avg_frame_rate` als fallback) en zet als `info['fps']`. Geen extra subprocess-call.
- **Beide upload-handlers** (`/api/upload` regel ~1428, `/api/upload-local` regel ~1652) zetten nu `'fps': info.get('fps') if isinstance(info, dict) else None,` in de jobs[job_id]-init.
- **Nieuwe helper `_inject_clip_fps(snap)`** — kopieert job-level fps in elke clip in `snap['clips']` en `snap['results']` (alleen waar clip nog geen eigen fps heeft). No-op voor jobs zonder fps (van vóór deze sessie). `_get_snapshot()` roept 'em aan op beide return-paden (in-memory + on-disk fallback).

`dj-clip-cutter/static/index.html` (270.320 → 274.225 bytes, +94 regels). Backup: `static/index.html.pre-phase4-zoom-2c.bak`.

- **Nieuwe `<span id="ed-frame">`** in de timecode-bar HTML naast `tl-cursor`/`tl-total`. CSS `.ed-frame:empty{display:none}` zorgt dat de span gewoon verdwijnt voor jobs zonder fps — geen lelijke placeholder.
- **CSS** voor `.ed-frame` (klein, mono, gedimd amber) en pan-cursor styling (`.ruler{cursor:grab}` + `.tl-scroll.is-panning *{cursor:grabbing!important}`).
- **`bindTimelineScrub()` gerefactored naar zoom-aware** — gebruikt nu `pxToVirtSec()` van 2a + `getEditorTimeMap()` om pointer-x naar relSec te converteren, dan clamp naar `[0, video.duration]`. Werkt correct op elk zoom-niveau én respecteert de stretch-zones (klikken in stretch-zone clamp't naar de clip-randen i.p.v. seek naar een onmogelijke positie). Extra skip-check op `ev.button !== 0` zodat middle-mouse niet wordt gehijack't door scrub.
- **Nieuwe `bindTimelinePan()`** (idempotent via `dataset.panbound`):
  - **Ruler-drag**: left-button mousedown op `.ruler` of `.ruler-labels` → noteer `startClientX` + `startScrollLeft`. Mousemove update `tl-scroll.scrollLeft = startScrollLeft - dx`. mouseup eindigt pan.
  - **Middle-mouse-drag**: `mousedown` met `ev.button === 1` anywhere binnen `tl-zoomwrap` → zelfde mechaniek, met `preventDefault` op mousedown om Linux-autoscroll te blokken.
  - Tijdens pan: `tl-scroll` krijgt `is-panning` class voor `cursor:grabbing` styling.
  - `mouseup` + `mouseleave` op window beëindigen pan zodat je niet stuck zit als je window verlaat tijdens drag.
- **`updateEditorTime()` updatet nu ook de `ed-frame` span** met `Math.floor(currentTime * fps)` als `STATE.clips[idx].fps` beschikbaar is. Anders: lege string → CSS hidet de span.
- **Wire-in**: `bindTimelinePan()` aangeroepen vanuit `renderEditor()` naast de bestaande `bindTimelineScrub()`/`bindStagePlayToggle()`.

### Wat NIET veranderd is

- Stretch-zone visualisatie van deelstap 1, drag-label, handles — onaangeroerd. Werken correct op elk zoom-niveau dankzij 2a's helpers.
- Zoom-UI van 2b (slider/wheel/keys) — onaangeroerd.
- Coord-helpers van 2a — gebruikt door 2c, niet gewijzigd.
- Geen wijzigingen aan `/api/upload` / `/api/upload-local` flow buiten het toevoegen van het `'fps'` veld.

### Verificatie

- `python -m py_compile app.py`: OK.
- `node --check` op het inline `<script>`-blok: parse OK.
- DOM-id scan: 136 ids, allemaal uniek (was 135; +1 voor `ed-frame`).
- Backend identifier sanity: `_parse_fps_string`/`_inject_clip_fps` op verwachte plekken; 2 `'fps':` writes in app.py (één per upload-handler).
- Sjuul handmatig getest: ruler-drag pant, middle-mouse-pan werkt, klikken op waveform seekt zoom-aware (incl. stretch-zone clamp), framenummer toont correct bij verse upload, oude jobs zonder fps tonen geen frame-counter (graceful), geen JS-errors.

### Bekende valkuilen voor latere sessies

- **Oude jobs in history** hebben geen fps in hun snapshot → frame-counter blijft leeg. Geen UI-impact (CSS hidet 'm), maar als je een one-time backfill wilt: een nieuwe migratie-script die `_validate_video_file` opnieuw runt op bestaande sources en `job['fps']` patcht. Out of scope deze sessie.
- **Variable-rate sources** (sommige iPhone-camera output) krijgen mogelijk een misleidend hoog `r_frame_rate` (bv. 60 voor een clip die effectief op 30 draait). `_parse_fps_string` clamp't op 240 maar correct ondervangen vereist een `nb_frames / duration` heuristiek. Niet aangepakt nu — als Sjuul echte foute getallen ziet, dat is de volgende fix.
- **Pan + scrub conflict bij snel klikken** — een korte ruler-mousedown zonder beweging triggert geen scroll-update (dx=0). Dat is correct gedrag, maar als een gebruiker bewust wil seeken via een ruler-click moeten we dat als afzonderlijk pad aanleggen. Niet relevant nu.

---

## SESSIE 10 — Phase 4 deelstap 2b: zoom-UI + slider + Ctrl+wheel/pinch + +/- keys (2026-05-09)

Eerste **zichtbare** zoom-UI. Bouwt op 2a's coord-helpers (handles + zones blijven correct positioneren bij elk zoom-niveau). Alle vier de zoom-triggers routen via één centrale `setEditorZoom()` zodat slider, knoppen, wheel/pinch en keys consistent blijven.

### Wat is er gedaan

`static/index.html` (264.180 → 270.320 bytes; 5843 → 5994 regels). Backup: `static/index.html.pre-phase4-zoom-2b.bak`.

- **Slider HTML** (regel ~1944) in tl-toolbar naast de bestaande `−`/`⊡`/`+` knoppen, achter een divider. `<input type="range" id="tl-zoom-slider" min="0" max="100" step="1" value="50">` + readout `<span id="tl-zoom-val">1.0×</span>`.
- **CSS** (`.zoom-slider-wrap`, `.zoom-slider`, `.zoom-slider-val`) — gold thumb met glow + mono readout, past visueel binnen tl-toolbar.
- **Centrale helper `setEditorZoom(value, anchorClientX?)`** — clamp naar [0.5, 12], bereken virtuele tijd onder anchor (cursor of midden), update `STATE.timelineZoom`, zet `tl-zoomwrap.style.width` inline en pas `tl-scroll.scrollLeft` aan zodat dezelfde virtuele tijd onder anchor blijft, dan `renderEditor()` + `renderZoomSlider()`.
- **Wrappers** — `editorZoom(direction)` en `editorZoomFit()` zijn nu thin wrappers rond `setEditorZoom`. Bestaande knoppen blijven werken zonder HTML-wijziging.
- **Slider mapping** — `sliderToZoom(s)` en `zoomToSlider(z)` doen log-mapping zodat elke slider-unit een constant zoom-multiplier is (~1.032× per slider-unit voor 0.5..12 range over 100 stappen).
- **`renderZoomSlider()`** — sync slider value + readout met `STATE.timelineZoom`. Aangeroepen vanuit `setEditorZoom()` én vanuit `renderEditor()` (idempotent).
- **Bind helpers (alle idempotent)**:
  - `bindZoomSlider()` — `input` event op slider via `dataset.zoombound`.
  - `bindZoomWheel()` — `wheel` listener op `tl-scroll` met `passive:false`. Triggert alleen bij `ev.ctrlKey` (Ctrl+wheel + macOS pinch). `Math.pow(1.0015, -ev.deltaY)` factor voor smoothness. Plain horizontal scroll blijft browser-default — bewaard voor 2c pan.
  - `bindZoomKeys()` — `keydown` op window via `window._clClipZoomKeysBound` sentinel. Alleen bij `STATE.view === 'editor'` en focus niet in input/textarea/contentEditable. Geen modifier (Cmd/Ctrl/Alt) — voorkomt botsing met browser page-zoom. `+`/`=` zoomt in 1.4×, `-`/`_` zoomt uit 1/1.4×.
- **Wire-ins in `renderEditor()`** — vlak na `STATE.timelineZoom` init worden `renderZoomSlider() + bindZoomSlider() + bindZoomWheel() + bindZoomKeys()` aangeroepen (idempotent dankzij bind-flags).

### Wat NIET veranderd is

- Stretch-zone visualisatie van deelstap 1, drag-label, handles — onaangeroerd. 2a's helpers zorgen automatisch dat alles correct blijft positioneren bij elk zoom-niveau.
- Bestaande `tl-zoomwrap.style.width = ${100 * zoom}%` mechanisme — onaangeroerd.
- Geen backend-aanrakingen, geen API-wijzigingen.

### Verificatie

- `node --check` op het inline `<script>`-blok: parse OK.
- DOM-id scan: 135 ids, allemaal uniek (was 133; +2 voor `tl-zoom-slider` + `tl-zoom-val`).
- Sjuul handmatig getest: slider sleept smooth + readout sync, trackpad pinch zoomt rond cursor, Ctrl+wheel idem, `+`/`-` keys werken, plain scroll laat alleen pan zien (ongewijzigd browser-default), Cmd+`+/-` zoomt page-default, geen JS-errors. Stretch-zones blijven op de juiste virtuele positie bij hoge zoom.

### Bekende valkuilen voor 2c

- **Plain scroll moet ongewijzigd blijven** — 2b raakt geen plain wheel/scroll aan; 2c gaat plain scroll als pan-pad gebruiken. Verifieer in 2c dat plain horizontal scroll nog steeds werkt zoals verwacht.
- **Frame-accurate seek (2c) vs handle-drag (1/2a)** — beide reageren op een mousedown op de tracks-area. Conflict-resolutie via `ev.target.closest('.trim-handle')` check in de seek-handler.
- **Conflict met `bindTimelineScrub`** — bestaande scrub-on-drag handler (regel ~3956) werkt op de tracks-area. 2c's seek-click moet niet dezelfde mousedown hijacken; check welke target priority krijgt.

---

## SESSIE 9 — Phase 4 deelstap 2a: coord-systeem refactor (2026-05-09)

Foundation-stap voor de zoom/pan/mini-map werk in 2b/2c/2d. **Invariance-refactor**: niets verandert visueel of functioneel, maar onder de motorkap loopt elke positie-berekening op de editor-timeline nu via één gedeeld coord-systeem. Vereist voordat 2b zoom-UI kan landen — anders zou elke percentage-formule individueel zoom-aware gemaakt moeten worden.

### Wat is er gedaan

`static/index.html` (262.195 → 264.180 bytes; 5801 → 5843 regels). Backup: `static/index.html.pre-phase4-zoom-2a.bak` (apart roll-back punt naast `pre-phase4-stretch.bak`).

- **`STATE.timelineScrollOffset = 0`** lazy-init in `renderEditor()` naast bestaande `STATE.timelineZoom`. Geen UI yet — staat klaar voor 2c (pan).
- **Drie helpers** vlak na `getEditorTimeMap()` (regel ~4499 in nieuwe nummering):
  - `virtSecToPct(virtSec, map)` — virtual-track-second → % offset op de timeline. Convention: `virtSec=0` is de stretch-left edge van de virtuele track, `virtSec=map.vDur` is de stretch-right edge.
  - `relSecToPct(relSec, map)` — clip-relative-second (de convention die `STATE.trim.{inSec,outSec}` gebruikt — negatief = stretch-left, >clipDur = stretch-right) → % offset. Wrapper rond `virtSecToPct` met de leftMax-offset.
  - `pxToVirtSec(x, rectWidth, map)` — pointer-x op de tracks-element → virtual-track-second. Gebruikt door drag-handler.
  - Bij `STATE.timelineZoom=1` + `scrollOffset=0` produceren ze exact dezelfde getallen als de oude inline formules. 2b/2c plug-in zoom/scroll zonder callsite changes.
- **Migratie van `renderTrimRegion()`**:
  - `place()` lokale `toVPct` pijlfunctie weg — vervangen door `relSecToPct` voor handles + `virtSecToPct` voor zone-edges.
  - Drag-handler bewaart de `vDur`-correctie nu in `drag.map` zelf via `Object.assign({}, snapMap, { vDur: snapVDur })`. `drag.vDur` veld is weg.
  - Mousemove gebruikt `pxToVirtSec` + `relSecToPct` ipv inline formules.

### Wat NIET veranderd is

- Geen DOM-elementen, geen CSS, geen events, geen API-calls.
- `getEditorTimeMap()`, het 60s stretch-bedrag, het pad `/api/recut` vs `/api/split-clip`, de bestaande `editorZoom()`/`editorZoomFit()` controls — allemaal onaangeroerd.
- DOM-ids: 133, allemaal uniek.

### Verificatie

- `node --check` op het inline `<script>`-blok: parse OK.
- DOM-id scan: 133 ids, allemaal uniek (zelfde count als SESSIE 8).
- Geen `drag.vDur`, `toVPct`, `secOnTrack` referenties meer in de file (oude formule-residu opgeruimd).
- Sjuul handmatig getest in browser: stretch-zones zelfde positie, handles zelfde gedrag, drag-label zelfde positie/timing als deelstap 1, geen JS-errors. Visueel + functioneel identiek aan SESSIE 8 — bevestigt dat 2a de invariance-claim haalt.

### Bekende valkuilen voor 2b en verder

- **`drag.vDur` is weg**: als 2b de drag-handler aanraakt, niet terugvallen op `drag.vDur` (bestaat niet meer). Gebruik `drag.map.vDur` of de helpers.
- **Helpers retourneren altijd %**: in 2b moet de helper-implementatie blijven werken op % zolang `tl-zoomwrap.style.width = ${100 * zoom}%` het zoom-mechanisme is. Pas in 2c (pan) wordt scroll-offset relevant — dan moet `virtSecToPct` mogelijk afgeleid worden naar pixel-mode of een tweede helper-flavor krijgen.
- **`Object.assign({}, snapMap, { vDur: ... })`**: shallow copy is voldoende want map-velden zijn primitives. Als toekomstige wijzigingen aan `getEditorTimeMap()` nested objects toevoegen, deep-copy nodig.

### Bestanden

- Aangepast: `dj-clip-cutter/static/index.html` (5801 → 5843 regels).
- Backup: `dj-clip-cutter/static/index.html.pre-phase4-zoom-2a.bak`.

---

## SESSIE 8 — Phase 4 deelstap 1: stretch-zone UX (2026-05-09)

Open follow-up #1 (Scenario S1) uit eerdere sessies geïmplementeerd. Backend ondersteunde al sinds SESSIE 1 ±60s stretch buiten clip-grenzen via `/api/recut`, maar het was visueel volledig onontdekbaar (alleen een doffe zwarte dim-gradient). Deze deelstap maakt de stretch *zichtbaar en aankondigend* zonder de stretch-logica zelf aan te raken.

### Wat is er gedaan

`static/index.html` (backup `static/index.html.pre-phase4-stretch.bak`, +5.4 KB / +135 regels):

- **CSS-block toegevoegd** vlak na `.trim-handle:hover::after` rule:
  - `.tl-stretch-zone` + `.left` / `.right` varianten — soft amber wash i.p.v. de oude `rgba(0,0,0,0.32)` dim-gradient. Zone fade gaat van iets sterker amber bij de clip-grens naar transparant aan de buitenrand zodat de "edge" duidelijk is.
  - `.tl-stretch-zone .lbl` — uppercase mono eyebrow `STRETCH ←60S` / `60S→ STRETCH`. Toont werkelijk beschikbare seconden (kan minder zijn dan 60 voor clips dicht bij begin/einde van de set; gebruikt `Math.round(map.leftMax/rightMax)`).
  - `.tl-stretch-zone.is-active` — feller amber wanneer de gebruiker een handle aan die kant sleept (visuele bevestiging "deze kant ben je nu aan het rekken").
  - `.tl-stretch-drag-label` — floating tooltip-stijl pill (mono, donkere bg, amber border) die boven de actieve handle verschijnt tijdens slepen voorbij de grens. Toont `+12s` of `−45s` (unicode minus voor visuele symmetrie met plus).

- **`renderTrimRegion()` aangepast** (~regel 4474):
  - Vervangen: enkele `<div class="tl-stretch-dim">` met linear-gradient → twee aparte `<div class="tl-stretch-zone left/right">` elementen met label-`<span>`'s.
  - Legacy-cleanup: oude `.tl-stretch-dim` element wordt opgeruimd op eerste render (voor hot-reload van sessies vóór deze sessie).
  - Eyebrow-text wordt elke render herberekend op basis van de huidige `getEditorTimeMap(clip)` zodat clips in de set-randen het correcte budget tonen ("Stretch ←8s" voor een clip die 8s na set-start zit).
  - Zones worden volledig verborgen (`display:none`) als `leftMax < 0.5s` of `rightMax < 0.5s` (zelfde gedrag als oude implementatie).

- **Drag-handler uitgebreid** (`window.addEventListener('mousemove', …)` in dezelfde functie):
  - `setZoneActive(kind, on)` toggelt `.is-active` op de juiste zone bij mousedown/mouseup.
  - `fmtOffset(sec)` formatter levert `+12s` / `−45s` (1 decimaal voor <10s, geen voor ≥10s).
  - In mousemove: bereken `offset = (kind === 'in') ? tt.inSec : (tt.outSec - clipDur)`. Toon label alleen wanneer voorbij grens (`> 0.05s`). Position via `inPct` / `outPct` percentages, gehouden in `#tl-trim` element zodat coord system gedeeld is met de handles.
  - In mouseup: alle visualisatie-state opruimen (label `is-on` weg, zone `.is-active` weg).

- **Tooltip-attributen** op `#tl-trim-in` / `#tl-trim-out` updated van "Drag to set IN/OUT point" → "Sleep om IN/OUT-punt te zetten — voorbij de grens verlengt de clip tot ±60s".

### Wat NIET veranderd is

- `getEditorTimeMap()`, de drag-clamping, het pad `/api/recut` vs `/api/split-clip` in `requestExportEditedClip()` — **alle stretch-logica blijft 1:1 zoals SESSIE 1**.
- Geen `app.py` wijziging. Geen nieuwe routes, geen nieuwe `STATE`-velden.
- Geen wijziging aan waveform-renderer of preview-video clamp.

### Verificatie

- `node --check` op de inline `<script>`-block: parse OK.
- DOM-id scan: 133 ids, allemaal uniek (geen regressie t.o.v. SESSIE 7-baseline).
- Sjuul handmatig getest in browser (zie screenshot 2026-05-09): stretch-zones zichtbaar amber, eyebrow-labels correct, `+Xs` / `−Xs` label tracked the active handle, active zone hilight correct.

### Tijdens test ontdekt: live-preview gat (geparkeerd)

Sjuul observeerde dat de waveform en preview-video tijdens drag niet "uitrekken" in de stretch-zone — dat is bestaand gedrag sinds SESSIE 1, niet veroorzaakt door deze deelstap. De UI is nu discoverable (✓), maar het blijft een blinde sprong tussen drag en Save & Re-export. **Bewust uitgesteld tot ná Phase 1 zoom/pan** omdat Phase 1 de gedeelde `timeToX`/`xToTime` helpers oplevert die deze feature óók nodig heeft. Aanpak voor later staat in de "VOLGENDE SESSIE → Live stretch-preview"-blok bovenaan dit document.

### Bestanden

- Aangepast: `dj-clip-cutter/static/index.html` (256.634 → 262.195 bytes; 5666 → 5801 regels).
- Backup: `dj-clip-cutter/static/index.html.pre-phase4-stretch.bak`.

### Bekende valkuilen voor toekomstige sessies

- Bij Phase 1 (zoom/pan) moet de positionering van `.tl-stretch-zone` en de drag-label van **percentage-based** naar het nieuwe `timeToX(t)`-systeem gemigreerd worden. Anders verspringen ze bij elk zoom-niveau ≠ 1.0.
- De `is-active` toggle hangt af van een correcte `kind` in de drag-state — als Phase 2 (draggable handles) de drag-state opnieuw schrijft moet dezelfde `kind`-key behouden blijven, anders blijft `.is-active` per ongeluk hangen na release.

---

## SESSIE 7 — Phase 3 end-to-end getest (2026-05-08)

Plan-gating is volledig gevalideerd in de browser na een end-to-end testronde. Geen open punten — Phase 3 is af.

### Wat is er getest + werkte

- **Quota-strip pre-render** — strip toont al `0 / 2 sets · FREE` voordat `/api/quota` antwoordt; geen lege flash.
- **Strip met echte data** — na auth + `loadQuota()` toont 'ie de echte stand (`2 / 2 sets · resets in 29 days` voor de Free-test-user die 2 sets had verbruikt).
- **Live counter na analyse** — 4e upload (eerste onder Pro): strip flipt van `0 / 10` naar `1 / 10` zodra status='done' is.
- **402-flow** — 3e upload op Free triggert de upgrade-modal met titel "You're out of clips this month", body "You've used 2 of 2 sets this month on the FREE plan.", en sub "Resets in 29 days." Backdrop-click + Escape + "Maybe later" sluiten 'm. Geen file in `$TMPDIR/dj-clip-cutter/uploads/` na de poging — gate hield stand.
- **Watch-folder gate (Free)** — alle drie de intake-CTAs (sidebar Cloud-sync, Drop-a-set source, home quick-card) openen de modal met "Watch a folder"-titel + Pro-pitch (i.p.v. quota-copy). Settings → Watch folder sectie toont locked-tile met slot-icoontje + "PRO FEATURE" eyebrow + "UPGRADE TO ENABLE" knop.
- **Stripe upgrade** — testkaart 4242 → "Payment received…" toast → "Welcome to PRO." → chip flipt FREE→PRO badge, strip springt van `2 / 2` naar `0 / 10` (webhook reset usage_this_period bij eerste betaalde upgrade — verse 30-dagen-window). Settings: locked-tile is weg, "Choose folder" / "Stop watching" knoppen weer actief.

### Cosmetische tweaks gemaakt na test 1

- `uploadFile()` swallow't de "Upload failed: quota_exceeded" rode toast wanneer de modal al opent (`err.code === 'quota_exceeded'` check).
- `_registerLocalPath()` doet hetzelfde voor de "Open large file (no copy)"-flow + sluit de picker netjes.

### Edge case bewust niet gefixed

- **Token-expiry refresh-rotation** — Supabase JWTs zijn ~1 uur. Bij verloop 401-pad geeft nu een nette "Session expired — please sign in again"-toast + auth-overlay terug, maar er is nog geen automatische refresh-token-flow. User moet opnieuw inloggen. Out of scope Phase 3 — wordt eventueel apart opgepakt als Sjuul echte gebruikers krijgt.

---

## SESSIE 6 — Phase 3 frontend (Blok 3+4) gecodeerd (2026-05-08)

Plan-gating UI: quota-strip in account-chip, upgrade-modal in dezelfde brand-card-stijl als de auth-overlay, automatische trigger via `api()` op 402, en Pro-feature gate op de watch-folder.

### Wat is er gedaan

**`static/index.html`** (backup: `static/index.html.pre-phase3.bak`):

- **STATE.quota** toegevoegd `{plan, used, limit, remaining, reset_in_days, reset_date}`.
- **Quota-strip** in account-chip onder de plan-badge: dunne progress-bar + "X / Y sets · resets in N days". Default-render `0 / 2` voor Free zodat er geen lege flash is. Studio krijgt "Unlimited sets". CSS-classes: `.ac-quota`, `.ac-q-bar`, `.ac-q-fill`, `.ac-q-fill-full` (rood-amber bij vol), `.ac-q-fill-studio` (gedimd).
- **Upgrade-modal** met DOM-id `upgrade-modal` (vlak na de auth-overlay markup). Twee plan-cards (Pro €21,99 / Studio €200) met feature-bullets en CTAs. Pro is goud-primary, Studio is subtieler. "Maybe later" sluit-knop top-right + click-buiten-kaart + Escape sluiten ook. CTAs roepen `startCheckout('pro' | 'studio')` aan.
- **`api()` helper** vangt nu 402-`quota_exceeded` en 401:
  - 402: `showUpgradeModal(payload)` automatisch + `err.code = 'quota_exceeded'` zodat callers (zoals upload) `if (err.code === 'quota_exceeded') return;` kunnen doen. Opgenomen in tests: payload-shape moet matchen `_quota_block_response` in app.py — die hebben we gelijktijdig getuned.
  - 401: clearSession + toast + showAuthOverlay, behalve op `/api/auth/*` (die mogen 401'en op verkeerde credentials zonder de hele app te resetten).
- **`loadQuota()`** roept `GET /api/quota` aan, vult STATE.quota, repaint de strip. Failures silent.
- **`renderQuotaStrip()`** plakt de progress-bar + label samen. Robuust tegen een nog-niet-geladen STATE.quota (defaults).
- **`showUpgradeModal(payload)`** vult titel/body/sub op basis van trigger:
  - `error: 'quota_exceeded'` → "You're out of clips this month" + reset-info
  - `trigger: 'watch_folder'` → "Watch a folder" + Pro-pitch
  - geen payload → generic "Need more clips?"
  - Hidet ook automatisch het plan-card waar je al op zit (Pro-user ziet alleen Studio-card).
- **`bindUpgradeModal()`** wired close + CTAs + backdrop + Escape — eenmalig in boot.
- **`openWatchFolderUI()`** — Free → upgrade-modal, Pro/Studio → switchView('settings'). Drie inline `onclick="switchView('settings')"`-aanroepen voor de Watch-folder intake-bronnen vervangen door deze router (home quick-card, upload source, sidebar Cloud-sync upgrade-card).
- **`renderSettings()`** plakt voor Free een locked-placeholder vóór de bestaande render-card en verbergt de echte. Idempotent: re-runs op elke visit, en switcht clean wanneer plan verandert.
- **Wire-ins** in:
  - `boot()` → `bindUpgradeModal()`
  - `postLoginBoot()` → `loadQuota()` na auth
  - `renderAccountChip()` → roept `renderQuotaStrip()` aan zodat een plan-flip direct de strip update
  - status-poll done-branch (regel ~2710) → `loadQuota()` zodra een analyse klaar is, dus de teller update live
  - `pollProfileForUpgrade()` → na succesvolle plan-flip: `loadQuota()` + re-render Settings/Upload als die actief zijn

### Verificatie

- `node --check` op alle inline `<script>`-blokken: parse OK.
- Geen dubbele DOM-IDs (alle 133 unique).
- Bytecode-compile op `app.py` blijft OK (geen backend regressies).

### Sjuul UI-test-checklist (DOEN VÓÓR Phase 4)

Pre-req: app draait op http://127.0.0.1:5555. Hard-refresh de browser (cmd+shift+R) want index.html is veranderd.

1. **Default state — strip pre-rendert FREE / 0 of 2**
   - Open de app in incognito of na hard-reload. Voor `/api/auth/me` antwoord geeft moet je in de account-chip al "0 / 2 sets" zien staan (geen lege flash).

2. **Login als Free-account** (bv. business+free@sjuulstudios.com)
   - Account-chip toont: email, FREE-badge, **progress-bar + "1 / 2 sets · resets in N days"** (omdat die user al 1 voltooide analyse heeft van de eerdere sessie). Bar voor ~50% gevuld.

3. **Counter live na nieuwe analyse**
   - Upload nog 1 set. Wacht tot status='done'. De strip moet binnen 1-2 sec updaten naar "2 / 2 sets" en de bar wordt rood-amber-getint (full state).

4. **402 → upgrade-modal**
   - Probeer een 3e set te uploaden. In plaats van een toast/error: de upgrade-modal opent over de hele app. Titel: "You're out of clips this month". Body: "You've used 2 of 2 sets this month on the FREE plan." Sub: "Resets in N days." Twee cards zichtbaar: **Pro €21,99** (goud-primary CTA) en **Studio €200** (subtieler CTA). Backdrop click + Escape + "Maybe later" sluiten 'm.
   - Geen file in `$TMPDIR/dj-clip-cutter/uploads/` na de poging.

5. **Klik "Upgrade to Pro"** → landt op Stripe Checkout. Vul testkaart `4242 4242 4242 4242` in. Na succes: "Payment received — activating…" toast → "Welcome to PRO." → account-chip flipt naar PRO-badge → strip update naar **"2 / 10 sets"** (oude usage blijft staan, terecht, en limit is nu 10).

6. **Watch-folder gate (Free vs Pro)**
   - Log uit + log in als een Free-account die nog niet ge-upgrade is.
   - Op Home: klik de "Watch a folder" quick-card → upgrade-modal opent met titel "Watch a folder" + Pro-pitch (i.p.v. quota-copy). Hetzelfde voor de "Watch a folder" source op de Drop-a-set scene en de "Connect →" knop in de sidebar Cloud-sync card.
   - Open Settings via sidebar: bij de "Watch folder" sectie zie je een doffe locked-tile met slot-icoon + "Pro feature" eyebrow + "Upgrade to enable" knop. Klik → opent dezelfde modal.
   - Upgrade naar Pro. Na flip: ga terug naar Settings — locked-tile is weg, echte "Choose folder" / "Stop watching" UI is zichtbaar.

7. **Studio render**
   - Met een Studio-user (Customer Portal: switch plan): account-chip strip toont "Unlimited sets" met een gedimde volledige bar. Geen counter.

8. **Session-expired (bonus)**
   - Wacht ~1 uur of in DevTools `localStorage.clear()` + reload zonder herinloggen. Bij volgende API-call (bv. switch view) krijg je nu een **"Session expired — please sign in again"**-toast en de auth-overlay komt automatisch terug, in plaats van een rare "token invalid" foutmelding.

### Bekende valkuilen

- **Strip blijft op 0/2** zelfs na geslaagde analyse → check DevTools console op fouten in `loadQuota()`. Of de SSE/poll-flow zat in een edge-case die `applyUpdate(s)` returnt voor 'done'.
- **Modal opent dubbel** → was getest met `bindUpgradeModal()` idempotency-flag, maar als je per ongeluk 2x de pagina bind (bv. via een tweede `boot()`-call) → klik-handler runs 2x. Niet voorzien op dit moment.
- **Pro-card verdwijnt op Pro-user** → that's intentional. Pro-users zien alleen Studio in de modal. Studio-users zien geen modal triggers (geen quota-block, watch-folder is unlocked).
- **Plan-gating dwingt geen "Cloud sync"-marketing weg voor Pro/Studio**. De sidebar promo-card toont nog steeds voor alle plans. Niet stoppend, kan later weg op Pro/Studio.

---

## SESSIE 5 — Phase 3 backend (Blok 1+2) gecodeerd, runtime-test pending (2026-05-08)

Phase 3 plan-gating: backend-helpers + quota check + counter + /api/quota endpoint. Code is geschreven en bytecode-compile-OK in de sandbox; runtime-test op Sjuul's Mac staat nog open.

### Wat is er gedaan (Claude)

**Imports** — `from datetime import datetime, timezone, timedelta` toegevoegd; `supabase_admin` re-exported uit `auth.py` en geïmporteerd in `app.py`.

**Nieuwe helpers in `app.py`** (vlak voor `_require_authed_user`, ~regel 900):
- `PLAN_LIMITS = {'free': 2, 'pro': 10, 'studio': inf}` — single source of truth.
- `_parse_pg_timestamp(value)` — robuste parser voor Supabase timestamptz strings (handelt zowel `Z` als `+00:00` af).
- `_get_or_refresh_profile(user_id)` — leest profile via `supabase_admin`, reset usage op 0 + advance `quota_reset_date` met 30 dagen als `now >= quota_reset_date`. Roll forward >1 cycle als user >30d weg was. Returnt `{ok, profile, plan, used, limit, remaining, reset_date, reset_in_days}`.
- `_increment_usage(user_id)` — read-modify-write +1 op `usage_this_period`. Logt fouten ipv raise (worker thread-safe). Race-OK voor 1-user-per-machine; multi-device → atomic Postgres RPC nodig.
- `_quota_block_response(snap)` — centrale 402 builder zodat alle gated endpoints dezelfde payload returnen.

**Quota check op upload-endpoints**:
- `/api/upload` (regel ~1308) — eerst `_require_authed_user`, dan `_get_or_refresh_profile`, dan 402 als `used >= limit`. Geen file-write of ffmpeg vóór de gate. `user_id` + `usage_counted: False` worden in `jobs[job_id]` opgeslagen.
- `/api/upload-local` (regel ~1530) — zelfde patroon.

**Increment op analysis-complete** — in `_process_job` direct ná `status='done'` (regel ~756): pak `user_id` + `usage_counted` uit job-state onder `jobs_lock`, roep `_increment_usage` één keer aan, set `usage_counted=True`. Idempotent: een job-resume bumpt niet dubbel.

**Nieuw endpoint** — `GET /api/quota` (regel ~855), Bearer-auth. Returnt `{plan, used, limit (null bij studio), remaining, reset_in_days, reset_date}`. Triggert auto-reset bij read als window verlopen is.

**Helper-script voor smoke-test** — `dj-clip-cutter/test_quota.sh` doet login, GET /api/quota mét en zonder token, en upload-pogingen zonder token (verwacht 401). 402-flow vereist handmatig een Free-account met 2 voltooide analyses — niet te automatiseren in een script.

### Files toegevoegd / gewijzigd

- Aangepast: `dj-clip-cutter/app.py` (imports + ~140 regels helpers + auth/quota gate op 2 upload-routes + increment in _process_job + /api/quota endpoint).
- Aangepast: `dj-clip-cutter/auth.py` (geen verandering — `supabase_admin` was al een module-level naam, alleen toegevoegd aan import-tuple in app.py).
- Nieuw: `dj-clip-cutter/test_quota.sh` (curl smoke-test).
- Backup: `dj-clip-cutter/app.py.pre-phase3.bak`.

### Sjuul-test-checklist (DOEN VÓÓR PHASE 3 FRONTEND)

Pre-req: Flask app draait op http://127.0.0.1:5555 (`./start.sh`).

1. **Smoke-test endpoint shapes**:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
./test_quota.sh

Verwacht:
- TEST 1 (/api/quota zonder token): HTTP 401.
- TEST 2 (/api/quota mét token): HTTP 200, JSON met `plan`, `used`, `limit`, `reset_in_days`. Voor de PRO-test-user: plan='pro', limit=10. Voor Free: plan='free', limit=2.
- TEST 3+4 (upload-routes zonder token): HTTP 401.

2. **Counter-test op een echte upload** (UI-test):
- Log in als test-user.
- Upload 1 set (klein bestand, ~1 min). Wacht tot status='done'.
- Roep `/api/quota` opnieuw aan via test_quota.sh. Verwacht: `used` is met 1 omhoog.

3. **402-test op Free** (vereist nieuwe Free-account):
- Maak nieuwe Free-account via signup-overlay (bv. `business+free@sjuulstudios.com`).
- Upload 2 sets, wacht tot beide done. /api/quota → `used: 2, remaining: 0`.
- Probeer 3e set te uploaden via UI. Verwacht: HTTP 402 in netwerk-tab, JSON met `error: 'quota_exceeded', plan: 'free', used: 2, limit: 2, upgrade_url, message`.
- Belangrijk: vóór de 402 mag GEEN file naar UPLOAD_DIR geschreven zijn, geen ffmpeg gestart. Check `$TMPDIR/dj-clip-cutter/uploads/` — geen nieuwe files na de 402.

4. **Auto-reset-test** (optioneel, 30+ dagen of via SQL):
- Of wacht 30 dagen, of in Supabase SQL: `update profiles set quota_reset_date = now() - interval '1 day' where email = 'business+free@sjuulstudios.com';`
- Roep /api/quota aan. Verwacht: `used: 0`, `reset_in_days: ~30`. In de logs van Flask: `Quota window rolled for <user_id> -> <new_date>`.

### Bekende valkuilen

- **`supabase_admin` is None** → `_get_or_refresh_profile` returnt `{ok: False, error}` en de upload-endpoint 500't. Check `.env` `SUPABASE_SERVICE_ROLE_KEY`. Auth.py logt bij start "Supabase admin client geinitialiseerd" als 't goed is.
- **/api/quota geeft 500 'profile not found'** → de profile-row ontbreekt voor deze user. Trigger `handle_new_user` zou hem moeten hebben aangemaakt. Check Supabase → Table editor → profiles.
- **Quota-counter komt niet omhoog na upload** → check Flask-log na done: regel `Quota incremented for <user_id>: 0 -> 1`. Als die ontbreekt is `user_id` niet in job-state beland (oude job van vóór Phase 3-deploy?). Forget die job en run opnieuw.
- **Race bij parallelle uploads** → read-modify-write +1 kan 1 update verliezen als twee workers tegelijk klaar zijn op dezelfde user. Acceptabel voor lokaal-1-user-per-machine; nog niet relevant.

---

## ARCHIVED — Phase 2 deploy + test (afgerond 2026-05-08)

> Bewaard voor referentie. Phase 2 is succesvol afgerond — zie SESSIE 4 hieronder.

### Stap 1 — Stripe library installeren (op je Mac)

Open Terminal en run:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
source venv/bin/activate
pip install -r requirements.txt

Dat installeert het `stripe` package in je venv. Output zou moeten eindigen met "Successfully installed stripe-...".

### Stap 2 — Supabase Edge Function deployen

Vereist: Supabase CLI. Als je 'm nog niet hebt:

brew install supabase/tap/supabase

Dan vanuit `dj-clip-cutter`:

supabase login                                    # browser-flow
supabase link --project-ref lbabsffxefkrxwzkbzar  # eenmalig

Zet de secrets (gebruik je echte sk_test, en voor PRICE_IDs de waardes uit .env):

supabase secrets set STRIPE_SECRET_KEY=sk_test_...
supabase secrets set STRIPE_PRICE_ID_PRO=price_1TUoYNA5DKhJaSAF6xynooY9
supabase secrets set STRIPE_PRICE_ID_STUDIO=price_1TUoZCA5DKhJaSAFI7AMgAbA
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=eyJ...

Deploy:

supabase functions deploy stripe-webhook --no-verify-jwt

`--no-verify-jwt` is verplicht: Stripe stuurt z'n eigen `stripe-signature` header, geen Supabase JWT.

### Stap 3 — Webhook endpoint registreren in Stripe

Dashboard → Developers → Webhooks → "Add endpoint":
- URL: `https://lbabsffxefkrxwzkbzar.supabase.co/functions/v1/stripe-webhook`
- Events:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_failed`

Klik op het zojuist aangemaakte endpoint → "Signing secret" → kopieer de `whsec_...` waarde. Plak die op TWEE plekken:

1. In je `.env` bij `STRIPE_WEBHOOK_SECRET=` (de regel staat al klaar)
2. Als Supabase secret: `supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_...`

Daarna nog een keer deployen zodat de edge function de nieuwe secret oppikt:

supabase functions deploy stripe-webhook --no-verify-jwt

### Stap 4 — Test de flow

1. Start de Flask app: `./start.sh`. Browser: http://127.0.0.1:5555
2. Log in met test-account: `business+cliptest@sjuulstudios.com` / `TestPassword2026`
3. In de account-chip linksonder zie je nu een gouden "Upgrade to Pro" knop (FREE plan).
4. Klik → je gaat naar Stripe Checkout (hosted page).
5. Vul testkaart in: `4242 4242 4242 4242`, expiry `12/30`, CVC `123`, naam/postcode willekeurig.
6. Stripe redirect terug naar `http://127.0.0.1:5555/?billing=success&session_id=...`.
7. Toast verschijnt "Payment received — activating your subscription…", daarna binnen ~5s "Welcome to PRO."
8. Account-chip badge gaat van FREE → PRO.
9. In Supabase dashboard → Table editor → `profiles`: rij van test-user heeft nu `plan='pro'`, `stripe_customer_id` gevuld, `stripe_subscription_id` gevuld.
10. Klik "Manage subscription" in de chip → Stripe Customer Portal opent → cancel daar het abonnement → terug naar app → na ~5s plan terug naar FREE (na period end voor live, direct in test als je "Cancel immediately" doet).

### Bekende valkuilen

- **Webhook geeft 400 "Bad signature"** → STRIPE_WEBHOOK_SECRET in Supabase secrets matcht niet met de waarde in Stripe dashboard. Re-set de secret en re-deploy.
- **Toast blijft hangen op "activating…"** → webhook is niet geregistreerd of edge function logs hebben een fout. Run `supabase functions logs stripe-webhook --tail` tijdens de test.
- **`pip install stripe` faalt** → activeer eerst de venv (`source venv/bin/activate`).
- **CSP blokkeert Stripe redirect** → niet verwacht (Stripe is een full-page redirect, geen iframe), maar als 't gebeurt: Content-Security-Policy in app.py uitzetten of `frame-src stripe.com` toevoegen.

### Niet doen in Phase 2

- Plan-gating zelf (quota counter, upgrade-modals bij overschrijding) — dat is Phase 3.
- Pro features (watch-folder, social sharing) — Phase 5+.
- Live mode aanzetten — pas vóór launch.

### Test-account
`business+cliptest@sjuulstudios.com` / `TestPassword2026` — kan via test-checkout naar Pro upgraden om de webhook te valideren. Verwijderbaar via Supabase dashboard → Auth → Users.

### Stripe credentials (referentie)

```
STRIPE_PRICE_ID_PRO     = price_1TUoYNA5DKhJaSAF6xynooY9
STRIPE_PRICE_ID_STUDIO  = price_1TUoZCA5DKhJaSAFI7AMgAbA
STRIPE_PUBLISHABLE_KEY  = pk_test_51S9Rck...QGhH5RynT (volledige waarde in .env)
STRIPE_SECRET_KEY       = sk_test_...   (in .env, NIET hier; door Sjuul ingevuld)
STRIPE_WEBHOOK_SECRET   = whsec_...     (in .env + Supabase secret na stap 3)
```

> Pro is bewust verhoogd van €11,99 → €21,99 (besluit 2026-05-08). Landing page + memory + Stripe product zijn allemaal op €21,99.

---

## SESSIE 4 — AFGEROND ✅ (2026-05-08)

Phase 2 paid-launch: Stripe billing volledig geïmplementeerd, gedeployd, en end-to-end getest met testkaart `4242 4242 4242 4242`. Plan-flip FREE → PRO werkt, account-chip update, webhook firet correct naar Supabase Edge Function (Optie A) en updatet profiles-tabel. Phase 2 is af.

### Wat is er gedaan

**Pricing-discrepantie opgelost (eerst):** landing page + tool + Stripe waren op verschillende prijzen. Nu allemaal Pro €21,99 / Studio €200. Watermark-features volledig uit alle tiers verwijderd. Pro-features uitgelijnd met memory: 10 sets/30d + social sharing + Dropbox/GDrive watch-folder.

**Stripe Test mode setup (Sjuul):**
- Test mode aangezet in dashboard.
- Twee subscription products aangemaakt: Pro €21,99/maand en Studio €200/maand.
- Price IDs gekopieerd naar `.env` en HANDOVER.
- Publishable + secret key opgehaald, beide in `.env` (sk_test_... handmatig, nooit in chat).

**Code (Claude):**
- `requirements.txt` += `stripe>=8.0`
- `.env` uitgebreid met `STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRICE_ID_PRO`, `STRIPE_PRICE_ID_STUDIO`, placeholder `STRIPE_WEBHOOK_SECRET=` (vult Sjuul in na deploy)
- Nieuwe module `billing.py` — Stripe SDK wrapper, mirror van `auth.py` patroon (env-based, defensive imports, `health_check`/`start_checkout`/`open_portal`/`plan_from_price_id`/`price_id_from_plan`).
- `app.py` uitgebreid met 4 endpoints:
  - `GET /api/billing/health` — config-status (geen secrets in response)
  - `GET /api/billing/config` — retourneert publishable key voor frontend
  - `POST /api/billing/checkout` (Bearer auth) — body `{plan}` → Stripe Checkout URL
  - `POST /api/billing/portal` (Bearer auth) — opent Customer Portal voor huidige user
  - Helper `_require_authed_user()` voor gedeelde Bearer-token validatie.
- `static/index.html`:
  - Account-chip nieuwe `.ac-billing` zone met plan-conditional knoppen.
  - Free → "Upgrade to Pro" goud + "Or Studio →" link (event delegation via `data-billing-action`).
  - Pro/Studio → "Manage subscription".
  - Functies `startCheckout(plan, btn)`, `openCustomerPortal(btn)`, `handleBillingRedirect()`, `pollProfileForUpgrade()`. Boot roept `handleBillingRedirect()` aan zodat `?billing=success|cancel|portal-return` wordt opgevangen + toast getoond + plan-state ververst.
- `supabase/functions/stripe-webhook/index.ts` — Deno edge function (Optie A):
  - Verifieert `stripe-signature` met `constructEventAsync` (Deno SubtleCrypto).
  - Handelt `checkout.session.completed` (eerste betaling → plan upgrade + reset quota), `customer.subscription.updated` (plan switch), `customer.subscription.deleted` (terug naar free), `invoice.payment_failed` (log only).
  - Update via `supabase-js` met `SUPABASE_SERVICE_ROLE_KEY` (bypass RLS).
- `supabase/functions/stripe-webhook/README.md` — deploy stappen, troubleshooting, log commando.

**Deploy + test (Sjuul, sessie-einde):**
- ✅ `pip install -r requirements.txt` — stripe 15.1.0 geïnstalleerd in venv.
- ✅ Supabase CLI 2.98.2 geïnstalleerd via Homebrew.
- ✅ `supabase login` + `supabase link --project-ref lbabsffxefkrxwzkbzar`.
- ✅ Supabase secrets gezet via `bash scripts/set-stripe-secrets.sh` (nieuw helper-script in `scripts/`). Secrets: STRIPE_SECRET_KEY, STRIPE_PRICE_ID_PRO, STRIPE_PRICE_ID_STUDIO, STRIPE_WEBHOOK_SECRET. SUPABASE_* secrets zijn auto-injected — niet zelf zetten.
- ✅ `supabase functions deploy stripe-webhook --no-verify-jwt` — endpoint live op `https://lbabsffxefkrxwzkbzar.supabase.co/functions/v1/stripe-webhook`.
- ✅ Webhook geregistreerd in Stripe dashboard (Test mode → Developers → Webhooks). Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`. Signing secret in `.env` + Supabase secret.
- ✅ End-to-end test met testkaart `4242 4242 4242 4242`. FREE → PRO badge flip werkt.

### Lessons learned

- **Copy-paste-rommel met `$VAR` shell expansie**: chat-rendering kan dollartekens of underscores stillerwijs vervangen door zero-width spaces. Eerste poging om secrets te zetten plakte `STRIPE_SECRET_KEY="STRIPESECRETKEY"` letterlijk i.p.v. expansie. Fix: `scripts/set-stripe-secrets.sh` — script doet `set -a && source .env && set +a` en zet de secrets. Geen copy-paste-fouten meer mogelijk.
- **Stripe webhook UI is vernieuwd** (mei 2026): "Add endpoint" heet nu "Add destination" en is een 3-stap-wizard (Select events → Choose destination type → Configure). Functioneel hetzelfde.
- **Logging volgorde in Python**: `log.info()` aanroepen tijdens module-import (zoals in billing.py) worden gedropt als `logging.basicConfig()` nog niet is aangeroepen. Niet kritiek — alleen geen "Stripe SDK geinitialiseerd" zichtbaar in start.sh output. Functioneel werkt alles.

### Files toegevoegd / gewijzigd

- Nieuw: `dj-clip-cutter/billing.py`, `dj-clip-cutter/supabase/functions/stripe-webhook/index.ts`, `dj-clip-cutter/supabase/functions/stripe-webhook/README.md`.
- Aangepast: `dj-clip-cutter/requirements.txt`, `dj-clip-cutter/.env`, `dj-clip-cutter/app.py` (+billing imports + 4 endpoints + `_require_authed_user` helper), `dj-clip-cutter/static/index.html` (account-chip CSS + HTML + 5 nieuwe JS functies).
- Aangepast (pricing fix): `landing/index.html` (Pro €19→€21,99, Studio €49→€200, watermark-bullets weg).

### Wat nog NIET werkt / volgende fases

- Phase 3: plan-gating — quota counter `usage_this_period++` bij elke upload, reset op `now > quota_reset_date`. Upgrade-modal bij quota-overschrijding. Pro/Studio features achter slot.
- Phase 4: editor-fixes (stretch-zone UX, Phase 1/2/6 uit VIDEO_EDITOR_PLAN.md).
- Phase 5+: Pro feature: Dropbox/GDrive watch-folder. Studio: batch processing.

---

## SESSIE 3 — AFGEROND ✅ (2026-05-07)

Phase 1 van de paid-launch architectuur: auth fundament. App gaat van local-only freeware naar SaaS-gated local app. Pricing: Free (€0, 2 sets/30d), Pro (€21,99, 10 sets/30d), Studio (€200, unlimited). 30-day rolling quota vanaf signup. Geen trial — Free IS de trial.

### Supabase setup
- Project `clip-live` (ref `lbabsffxefkrxwzkbzar`), region West EU. Free tier.
- Tabel `public.profiles` met velden: id (FK→auth.users, on delete cascade), email, plan ('free'|'pro'|'studio'), signup_date, quota_reset_date (default = signup + interval '30 days'), usage_this_period (int), stripe_customer_id (unique, nullable), stripe_subscription_id (unique, nullable), created_at, updated_at.
- Trigger `on_auth_user_created`: bij elke nieuwe `auth.users` insert → insert into profiles met plan='free' + quota_reset_date = signup + 30d.
- Trigger `profiles_updated_at`: auto-bumps updated_at op UPDATE.
- RLS aan; policy "Users can read own profile" via `auth.uid() = id`. Service-role client bypasses RLS voor webhooks.
- **Email confirmation UITGEZET** in Auth → Configuration → User Signups → Confirm email = off. Aanzetten vóór productie.

### Backend (auth.py + app.py)
- Nieuwe module `auth.py`: laadt `.env` via python-dotenv, init twee Supabase clients (anon + service_role), exposes `health_check()`, `signup()`, `login()`, `get_user_from_token()`. Wrapped imports — ontbrekende deps of bad .env crashen de app niet.
- `app.py` — vier nieuwe endpoints:
  - `GET /api/auth/health` → ping Supabase + config status (zonder secrets)
  - `POST /api/auth/signup {email, password}` → returns session als confirm-email off
  - `POST /api/auth/login {email, password}` → returns session
  - `GET /api/auth/me` → returns user + profile, requires `Authorization: Bearer <token>`

### Frontend (static/index.html)
- **Auth overlay** (full-screen modal): brand-card met tabs Login/Sign up, email + password fields, error/success-balk. Verbergt de app totdat sessie geldig is. CSS gebruikt bestaande tokens (--ink-*, --amber, --serif).
- **Sidebar account chip** onderin: email, plan-badge (FREE amber / PRO sterker amber / STUDIO solid gold), Log out knop.
- `STATE.session` = `{access_token, refresh_token, expires_at, email, user_id, profile, cached_at}`, persisted in `localStorage.clipLive.session`.
- `api()` helper attacht `Authorization: Bearer <token>` automatisch wanneer STATE.session bestaat.
- Boot-flow: probeer cache te restoren → `/api/auth/me` server-verify → render account chip + `postLoginBoot()`. 401 of geen sessie → `showAuthOverlay`.
- **Offline grace 24h**: als server unreachable maar `cached_at < 24h` + profile aanwezig → laat user in op cached profile.

### Files toegevoegd / gewijzigd
- Nieuw: `auth.py`, `.env` (gitignored), `.gitignore`, `test_auth.sh` (curl smoke-test signup→login→me).
- Aangepast: `requirements.txt` (+supabase>=2.0, +python-dotenv>=1.0), `app.py` (auth-imports + 4 endpoints), `static/index.html` (overlay HTML/CSS/JS + STATE.session + api() Bearer + nieuwe boot()).

### Verificatie
- Backend: `test_auth.sh` end-to-end groen. profiles-row krijgt `plan=free` + `quota_reset_date = signup + 30 days` automatisch via trigger.
- Frontend: alle 6 UI-scenarios groen — eerste login, herlaad-met-cache, logout, signup-tab switch, error-state, fresh signup.

### Test-account
`business+cliptest@sjuulstudios.com` / `TestPassword2026` — blijft staan voor Phase 2 testing, anders te wissen via Supabase dashboard → Auth → Users.

### Wat nog NIET werkt / volgende fases
- Phase 2: Stripe — products in dashboard, checkout flow, webhook → Supabase Edge Function die `profiles.plan/stripe_customer_id` updates. Customer Portal link voor managen/cancellen.
- Phase 3: plan-gating — quota counter `usage_this_period++` bij elke upload, reset op `now > quota_reset_date`. Upgrade-modal bij quota-overschrijding. Pro/Studio features achter slot.
- Phase 4: editor-fixes (stretch-zone UX, Phase 1/2/6 uit VIDEO_EDITOR_PLAN.md) — niet aangepakt deze sessie.

---

## SESSIE 2 — AFGEROND ✅ (2026-05-06)

Grote sessie. Begon met de export-bug uit `HANDOVER-EXPORT-BUG.md`, daarna de hele UI-rebuild C1-C4 uitgevoerd, en aansluitend nog vier user-driven polish-iteraties op exporteren / Editor.

### 1. Export-bug rootcause + fix
Vorige sessie had de export-pipeline opnieuw geschreven (`cutter.py::export_clip_with_settings`, herschreven `/api/export/<job>` route, UI defaults op `match` codec/fps), maar in de UI faalde elke export met 23/23 FAIL.

**Rootcause:** `_run_export_job` las `jobs[job_id]['clips']` (analyzer-only metadata) i.p.v. `jobs[job_id]['results']` (cutter-output mét `files` paden). Elke clip kreeg dus `files: None` → `_resolve_export_source` → 23/23 FAIL.

**Fix in `app.py`:**
- Regel 2219: `clips = list(job.get('results') or job.get('clips') or [])`.
- Regel 2226-2238: snapshot-rehydrate fallback heeft dezelfde voorkeur **en** schrijft terug naar de juiste key (`results` ↔ `results`, `clips` ↔ `clips`) zodat analyzer- en cutter-data gescheiden blijven in geheugen.

**Verificatie:** verse job `49ed2aef`, POST `/api/export/49ed2aef` → `{count: 23, ok: true}` → na ~5 s `done: true`, alle 23 clips `status: done`, geldige mp4's in `$TMPDIR/dj-clip-cutter/output/<job>/exports/`.

`HANDOVER-EXPORT-BUG.md` is verwijderd; alle relevante info zit nu hier.

### 2. C1 — Cleanup (UI sloop)
Verwijderd uit `static/index.html`:
- Hele Scene 7 (`<main id="view-export">`) + `renderExport()` JS (~175 regels).
- `gpu-meter` CSS + alle `.meter-*` rules.
- "Export →" knop in Editor-toolbar.
- `export: renderExport,` mapping uit `RENDERERS` object.

Verwijderd uit `app.py`:
- `/api/hwmeters` Flask route (was fake stub).

`/api/export-preset/<job>` blijft staan (TikTok/Reels presets — toekomstig).

### 3. C2 — Backend defaults op `match`
Auto-realised via C1 — codec/fps/resolution dropdowns zaten alleen in Scene 7 dat is verwijderd. Backend pakte al `match` als default.

### 4. C3 — Library-tab (view-home)
Home werd echte Library:
- Greeting + zoek/upload-row weg.
- `.quick` cards verticaal verdubbeld (padding 18→34, min-height 120→240, icons 32→56, h3 18→24) — drie prominente intake-cards bovenaan.
- Recent projects + Exports sections in 2-koloms grid (`.library-cols`, klapt naar 1 kolom <1100px).
- Filter chip-row boven Exports: All / 9:16 / 16:9 / ★ Favorites met live counts.

**Backend (`app.py`):**
- `GET /api/exports` — listet alle .mp4/.mov in `OUTPUT_DIR/<job>/exports/` met `set_name`, `size`, `mtime`, `thumbnail`, `aspect`, `is_favorite`, `clip_idx`. Newest-first.
- `POST /api/exports/<job>/<file>/reveal` — `subprocess.Popen(['open', '-R', path])`.
- `DELETE /api/exports/<job>/<file>` — `os.unlink`.
- `POST /api/exports/<job>/<file>/copy-to` — `shutil.copy2` naar user-folder.
- Path-traversal protection via `realpath` + prefix-check in `_safe_export_path`.

**Frontend:** `renderHomeExports()`, `renderExportCard()`, `bindExportsActions()`, `openExportInEditor()`, `copyExportToFolder()`. Card-click → editor; per-card actions: `[Show in Finder] [✏️ Edit] [⬇️ Export to…] [🗑 Delete]`.

### 5. C4 — Select-en-export flow
**Backend:**
- `_resolve_export_sources(clip, aspects=None)` returnt **alle** beschikbare formats — landscape + vertical worden parallel gerenderd per queue-item.
- `/api/export/<job>` accepteert `clip_indices: [int…]`, `aspects: [...]`, `output_dir: str`. Validatie up-front (folder bestaat + writable, valid indices).
- `_run_export_job._process` rendert per queue-item alle aangevraagde formats, renamet de file naar user-label, kopieert naar `output_dir`.

**Frontend:**
- Dashboard `.clip` cards: select-toggle top-right (rondje wordt goud vinkje), `.clip.selected` border.
- Sticky `.export-sel-bar` bovenaan view-dashboard verschijnt zodra 1+ geselecteerd: "N selected · Cancel · Export N".
- "Export all" permanent in Dashboard scene-header.
- Editor toolbar: "Export selected (N)" + "Export all" knoppen.
- Editor cue-list: per-row `.cue-select` toggle. Selectie deelt `STATE.selectedClips` Set met Dashboard.
- Floating `.export-pill` rechts-onder tijdens render (pulserende dot, "Exporting label · 5/23").
- "New exports" `.new-dot` op Library-sidebar item, geclearred bij Library bezoek.
- Auto-refresh van Library Exports section na render-done.

### 6. Hard cut (cutter.py)
Default `fade_duration=0.0` in alle ffmpeg builders — `_build_audio_filter`, `_build_landscape_cmd`, `_build_vertical_cmd`, `_build_proxy_cmd`, `cut_clip_landscape`, `cut_clip_vertical`. Fade filters wrapped in `if fade_duration > 0` voor opt-in. `process_clip_full` zet `fade_duration = 0.0`. ⚠️ Bestaande clips in `OUTPUT_DIR/<job>/` met fade blijven, omdat `match` codec stream-copyt — re-process source set voor hard-cut master clips.

### 7. Folder picker bij export (cross-platform)
**Backend (`app.py`):**
- `POST /api/pick-folder` — opent native folder dialog. macOS via AppleScript (`choose folder with prompt … default location`). Windows/Linux via `tkinter.filedialog.askdirectory`. Body: `{prompt, default_dir}`. Response: `{ok, cancelled, path, platform}`.
- `_default_export_dir()` helper — `~/Downloads` of home als fallback.
- `output_dir` param in `/api/export` validatie: bestaat + writable, expanduser, fail-fast vóór ffmpeg.
- `_run_export_job._process` kopieert via `shutil.copy2` naar user-folder, original blijft in `OUTPUT_DIR` (Library blijft werken).

**Frontend:** `startExport()` opent picker via `/api/pick-folder` met laatst-gebruikte folder uit `localStorage.clipLive.exportDir`. Cancel = silent return. Toast on done toont bestemming: `"Saved 3 clips to ~/Downloads"`.

### 8. Filename gebruikt user-label
`_build_export_filename(clip, idx, aspect_key, codec, ext)` componeert `<safe_label>__clip<NN>__<aspect>__<codec>.<ext>`:
- Custom label → `My_Drop__clip08__landscape__match.mp4`.
- Geen rename → `Drop_8__clip08__landscape__match.mp4`.
- `_safe_filename_label()` strip filesystem-onveilige chars + collapse whitespace.

`_run_export_job._process` doet `os.rename` na render, vóór de copy naar `output_dir`. Library parsers (clip_idx + aspect) zoeken eerst de nieuwe `__clip<NN>__/__aspect__` markers en vallen terug op het oude patroon. Frontend `cleanName` regex strip de nieuwe suffix → toont gewoon "My Drop" als card-titel.

### 9. Aspect-keuze popup
Modal met 9:16 / 16:9 / Both verschijnt vóór de folder picker bij elke Export-actie. `pickExportAspect(subtitle)` returnt Promise. Backend respecteert `cfg.aspects` whitelist; lege/missing = render alle beschikbare formats (back-compat).

### 10. Score-badge + filter-chips polish
- `.clip .score` van overlay top-right naar inline pill in `.info .r` (links van favorite ★) — voorkomt conflict met C4 select-toggle.
- Dashboard filter chips "Transitions" en "Under 30s" verwijderd (Sjuul gevraagd). Resterend: All / Drops / Favourites / Renamed.

### 11. Editor preview groter
- `.ed-canvas` padding rechts → 90px (gereserveerd voor `.ratio-rail`).
- `.preview-stage` van `width: min(100%, 320px)` → `width: min(100%, 780px); max-height: 65vh`.
- Helper `applyEditorStageSize(ratio)` — voor 9:16/4:5 (portrait) zet inline `height:65vh; width:auto` (height-driven) zodat hele frame zichtbaar blijft. 1:1/16:9 vallen terug op CSS default (width-driven, ongewijzigd).
- `renderEditor()` roept `applyEditorStageSize(STATE.editorRatio || '9:16')` aan voor initial state.

### Bestanden niet aangeraakt
`analyzer.py`, `uploader.py`. Backups van vorige sessies blijven staan: `static/index.html.pre-c1-cleanup.bak`, `app.py.pre-export-blok3.bak`, etc.

---

## SESSIE 1 — AFGEROND ✅

Alle stappen A t/m E geïmplementeerd in `static/index.html`. Backup op `static/index.html.pre-sessie1.bak`.

**Wat er gedaan is:**
- **A1:** `STATE.setDuration` wordt nu gezet vanuit `/api/status` in `renderEditor`
- **A2:** Waveform-fetch gebruikt nu `bins=2000` (was 600)
- **B:** `drawWaveformCanvas` vervangen — mirror-envelope, RMS-glow laag, amber→copper kleurverloop
- **C:** `getEditorTimeMap(clip)` toegevoegd als single source of truth voor tijd-mapping (±60s stretch)
- **D:** Positie-indicator toont nu "Clip X of Y · MM:SS / H:MM:SS in set"
- **E:** Trim-handles kunnen ±60s buiten originele clip-grenzen slepen; gedimde stretch-zones links/rechts; stretch-path gebruikt `/api/recut`, trim-path gebruikt bestaande `/api/split-clip`

---

## Huidige staat van de app

De app werkt end-to-end. Upload → analyse → clips → editor → export naar gekozen folder.

**Wat er staat:**
- Multi-view SPA: Library / Drop a set / Clips (Dashboard) / Editor / Style / Settings
- Drop-detectie via librosa (HPSS, bar-aware) + BPM
- Proxy pipeline voor grote bestanden (>2 uur): eerst 720p proxies, daarna lazy 1080p
- SSE progress stream
- Video editor met trim-handles ±60s, hi-res waveform, re-export, 4 aspect ratios (9:16 / 1:1 / 16:9 / 4:5)
- Library tab met Recent projects + Exports filter (9:16/16:9/Favorites), per-card acties
- Dashboard select-and-export bar (Gmail-stijl), Editor export-buttons, deelt selectie tussen views
- Folder picker (mac AppleScript / win+linux tkinter), localStorage memory voor laatst-gebruikte folder
- Aspect-keuze popup vóór elke export
- Hard-cut renders (geen fade in/out)
- Filenames met custom-label of `<Type>_<index>` fallback

**Wat nog NIET werkt of ontbreekt:**
Zie `VIDEO_EDITOR_PLAN.md` voor de volledige roadmap (Phases 1–10).
- Timeline zoom en pan (Phase 1) → blokkert alles eronder
- Draggable handles (Phase 2) → renders maar slepen werkt nog niet
- J/K/L scrub (Phase 3)
- Loop playback (Phase 6)
- Inline clip expand vanuit dashboard (Phase 7)
- Export presets per platform (Phase 8) — `/api/export-preset` endpoint bestaat al, geen UI

---

## Bekende bugs

| Bug | Omschrijving | Status |
|-----|-------------|--------|
| **Duplicate clips** | Clips tonen soms identieke video i.p.v. unieke drops | Open — terugkerend |
| **Large-file pipeline vastlopen** | Sets >2 uur kunnen vastlopen | Deels via proxy pipeline (2026-04-26), nog niet stabiel |
| **Clips verdwijnen na hard-reload** | `STATE.jobId` werd nergens gepersisteerd. | **Closed sessie 14 — geverifieerd sessie 15.** localStorage `clipLive.activeJobId`. |
| **Recent Sets toont oude pre-snapshot jobs** | Sidebar toonde 24+ oude entries. | **Closed sessie 15.** `/api/history` filtert strikt op snapshot.json (sessie 14 r2). Plus race-safety voor net-binnen-gekomen jobs. |
| **Stretch-recut "Source video file not found"** | Bron-mp4 werd na done verwijderd uit /tmp. | **Closed sessie 15.** UPLOAD_DIR persistent + `_cleanup_source_video` no-op + snapshot bewaart `video_path`. End-to-end live geverifieerd op nieuwe upload. |
| **Stretch-recut single-handle viel naar split** | `if (hasBand && isStretch)` gate dropte single-side stretches. | **Closed sessie 15.** `if (isStretch)` is nu de eerste branch in `editorTrimAtPlayhead`. |
| **/api/recut 500 HTML page** | Backend ving alleen RuntimeError/OSError; KeyError ed. lekten als HTML. | **Closed sessie 15.** Catch-all `Exception` → JSON met `reason` field. Pre-checks op clip_index, video_path, end ≤ source_duration. |
| **★ ZIP geeft lege/corrupte zip** | Backend bouwde 0-byte zip wanneer geen favorites had `files`. | **Closed sessie 15.** Backend telt copies, returnt 400 als 0. Frontend fetch+blob ipv `<a href>` voor zichtbare errors. UI: dim disabled state. |
| **Library toonde alleen 9:16 exports** | Aspect-picker liet user maar één kiezen. | **Closed sessie 15.** Aspect-picker overgeslagen — render altijd beide. Filter chips in Library doen het kiezen. |
| **Recent Sets toonde oudste eerst** | `.slice(0, N)` op chronologisch-gesorteerde array. | **Closed sessie 15.** `.slice(-N).reverse()` in beide sidebar + Library. |
| **Pauze-knop bleef staan na Volgende clip** | Icon werd alleen gewisseld via video play/pause events; clip-switch triggerde geen event. | **Closed sessie 15.** `_resyncEditorPlayState()` na renderEditor in `editorPrev/Next`. |
| **Pre-snapshot jobs in history** | Oude jobs (vóór snapshot-systeem) geven 404/410 errors in console bij Library/Dashboard load | Geen UI-impact, alleen console noise. Forget-knop in Dashboard verwijdert ze. Overlapt deels met "Recent Sets toont oude jobs" hierboven. |

---

## Open follow-ups

Dingen waar Sjuul over nagedacht heeft maar nog niet gebouwd:

1. **Timeline-stretch UX (E)** — backend ±60s stretch staat sinds SESSIE 1.
   - ✅ **S1 (UX-discoverability):** afgerond in SESSIE 8 (2026-05-09). Amber wash + `±Xs` drag-label + hover-tooltips. Visueel goedgekeurd door Sjuul.
   - **S2 (limiet wijzigen):** `const stretch = 60` vervangen met `STATE.stretchSeconds`, instelling in Settings. Niet aangepakt — wachten tot er behoefte aan is.
   - **S3 (regressie-test):** verifieer dat slepen voorbij clip-grenzen daadwerkelijk `/api/recut` aanroept en niet stilletjes faalt. Niet aangepakt — wordt impliciet getest via dagelijks gebruik.
   - **S4 (live stretch-preview, NIEUW):** geparkeerd tot ná VIDEO_EDITOR_PLAN Phase 1 (zoom/pan). Tijdens drag voorbij clip-grens moet de waveform uitrekken naar de virtuele range en moet de preview-video uit de bron-set komen, zodat het geen blinde sprong meer is. Hangt af van de `timeToX`/`xToTime` helpers die Phase 1 oplevert. Volle aanpak staat in de VOLGENDE SESSIE-blok bovenaan dit document.

2. **9:16 export voor oude jobs** — bestaande Library-exports zijn allemaal landscape (gerendered vóór multi-format support). 9:16 filter is `0` totdat user opnieuw exporteert. Geen actie nodig — workflow lost zichzelf op naarmate users nieuwe sets exporteren.

3. **Windows-tkinter test** — folder picker geïmplementeerd voor Windows via `tkinter.filedialog.askdirectory`, maar nog niet door een Windows-user getest. Tkinter is standaard meegeleverd in Python.org's Windows installer — moet werken. Als het breekt: error toast geeft `"tkinter not available"`.

4. **Editor card "Open in Editor" affordance** — knop is toegevoegd op Library cards (✏️ icon). Card-click doet hetzelfde. Mogelijk redundant; kan weg als de card-click intuïtief genoeg is bij testen.

5b. **Stretch-handles ook draggable op mini-map (gevraagd 2026-05-10).** De mini-map onder de waveform toont nu alleen de viewport-positie. Sjuul wil dat de in/out trim-handles daar OOK zichtbaar + draggable zijn — zodat je vanaf de overview-strip rechtstreeks kan stretchen zonder eerst in de hoofd-timeline in te zoomen. Aanpak: in `renderMinimap()` extra elementen toevoegen voor de twee handles (zelfde gold-style als hoofd-tracks), bind drag-listeners die STATE.trim updaten via dezelfde `pxToVirtSec`-coordinate helper. Bestaande hoofd-handles blijven gewoon werken — de mini-map versie is een tweede mount-point op dezelfde state.

5c. **Achtergrond-analyse + "Terug naar analyse" knop (gevraagd 2026-05-10).** Wanneer een nieuwe set wordt geüpload, blijft processing nu in een aparte view (Processing). Sjuul wil dat:
   - Analyse blijft draaien op de achtergrond als de user wegklikt (al zo — Flask-thread loopt door).
   - Een persistent "Continue analysis" of "Back to processing X%" badge zichtbaar is in de header/sidebar zodat user terug kan switchen.
   - Klik op de badge → switchView('processing') met de juiste jobId actief.
   Aanpak: een "active processing" pill bovenin de sidebar (boven Recent Sets) die zichtbaar is wanneer er één of meer jobs in `STATE.history` (of in-memory) status='processing' hebben. Tikker poll't /api/status elke 3s.

5d. **1:1 aspect ratio render bug (gemeld 2026-05-10).** Bij klik op "1:1" in de aspect-rail van de editor preview verschijnt toast "Could not render 1:1: ffmpeg failed". Onderzoeken: welke ffmpeg-arg breekt voor 1:1 lazy render. Waarschijnlijk filtergraph mist een `crop=ih:ih` of vergelijkbaar. Backend `/api/render-clip` of equivalent.

6. **Unify upload UX — één knop, automatische backend-keuze (gevraagd 2026-05-10).** De Upload-view heeft nu drie zichtbare intake-knoppen die functioneel overlappen voor de eindgebruiker:
   - "Choose from this Mac" → `/api/upload` (kopieert het hele bestand naar UPLOAD_DIR; goed voor kleine sets)
   - "Drop a set here" (drag-and-drop op zelfde gebied) → `/api/upload`
   - "Open large file (no copy)" → `/api/upload-local` (registreert het pad, decodeert proxies on-the-fly; bedoeld voor grote livesets >2u die anders het tempdir-volume opvreten)

   Sjuul wil dat dit één knop wordt: gebruiker kiest of dropt een file, frontend kiest zélf de juiste backend op basis van bestandsgrootte (en/of duur). De "Open large file (no copy)"-knop hoeft niet zichtbaar te blijven.

   **Voorgestelde drempel:** `> 2 GB` of `> 2 uur` → `/api/upload-local`. Daaronder → `/api/upload`. Threshold instelbaar in `config.json` (`upload_no_copy_threshold_bytes`, default 2 \* 1024<sup>3</sup>). Bij drag-and-drop weten we bytes via `File.size`; bij Choose-from-Mac idem (file picker geeft size).

   **Aanpak:**
   1. Frontend `uploadFile(file)` checkt `file.size`. Onder threshold → bestaande POST naar `/api/upload`. Boven → toon "Large file detected — starting no-copy ingest" toast en routeer naar het bestaande no-copy pad (`POST /api/upload-local` met `local_path`). Maar wacht — `/api/upload-local` accepteert een **path**, niet een uploaded blob. Bij drag-and-drop hebben we het pad niet (browser security). Dus voor drag-drop kan no-copy alleen werken via een macOS file-protocol drag (er staat al wat code voor `webkitGetAsEntry`/`localPath`-detectie in regel ~2570 — verifiëren).
   2. Voor "Choose from this Mac" via de native picker: gebruik dezelfde flow als de huidige "Open large file (no copy)" — `local_path` resolven via een nieuwe of bestaande `/api/pick-file` (folder-picker bestaat al voor watch-folder). Dat geeft het echte pad zodat `/api/upload-local` werkt.
   3. UI: verberg "Open large file (no copy)" knop. Houd "Watch a folder", "From Dropbox", "From Google Drive" zoals ze nu staan (separate intake-flows).
   4. Optioneel: bij drag-drop van een groot bestand zonder pad-toegang, val terug op de regular `/api/upload` met een waarschuwing dat de upload ~X minuten gaat duren én X GB op disk vergt — zodat de gebruiker bewust kiest om door te zetten of via picker een no-copy ingest te doen.

   **Risk:** middel — de drag-drop-naar-no-copy is niet triviaal door browser sandbox; we kunnen daar strakker maken door drag-drop alleen voor kleine files toe te staan en grote uploads via de picker te dwingen.
   **Schatting:** 1 sessie als we drag-drop drag-drop laten voor kleine files en de picker-flow herbruiken voor grote.
   **Waarde:** hoog — verlaagt de cognitieve last bij upload en haalt een "expert"-knop weg uit de eerste impressie.

---

## Architectuur op één pagina

```
app.py            Flask entry point, alle /api/* routes, SSE, job state, export pipeline,
                  folder picker, library endpoints (list/reveal/copy/delete)
analyzer.py       Drop-detectie (librosa, HPSS, BPM, Demucs optioneel)
cutter.py         Video snijden (ffmpeg), thumbnails, filmstrip, presets, split,
                  export_clip_with_settings — fade defaults op 0 (hard cut)
uploader.py       Platform upload stubs (YouTube, TikTok, Instagram, Facebook)
static/           Frontend HTML/CSS/JS (SPA, één pagina ~205 KB)
config.json       App instellingen
job_history.json  Persistente job state
OUTPUT_DIR        $TMPDIR/dj-clip-cutter/output/<job>/  — proxy/landscape/vertical/exports/
                  + thumb_clipNN.jpg + clips.csv + job.json snapshot
```

**App starten:**
```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
./start.sh
```
Browser: http://127.0.0.1:5555

---

## Wat er als laatste aan gewerkt is

- **2026-05-23 (sessie 32 / 32b / 32c / 32d / 32e):** Marathon timeline-editor UX-sessie, 5 sub-iteraties. **Eerste ronde (32):** cue-list opgeschoond (DROP/TRANS/BUILD-pill weg, "Energy ★ 0" weg, padding 35% compacter), dashboard `.clip .info` strook iconen gegroepeerd met divider. **Tweede ronde (32b):** rename-contrast op kaart, `forceRecut` flag, 4 knoppen in `.info .r` allemaal 28x28, inline trim opent niet meer per ongeluk timeline-editor (`cardClickOpen` + `_ceJustFinishedDrag` 300ms-window). **Derde ronde (32c):** `editorTrimAtPlayhead` deep-dive refactor (5 branches → 1 pad, `clip.duration` als single source of truth), rename-contrast écht gefixt (cue-list miste in selector), audio stopt bij back-button (`switchView` pauze-block + `hoverPreviewStopAll`), Re-export knop → directe Export-flow (recut + startExport in één klap). **Vierde ronde (32d):** `hasBand` met `Math.abs()` voor zowel naar-binnen als naar-buiten (vangt pure stretch), asterix + scissor weg uit toolbar, playhead start op IN-handle, playhead sleepbaar (z-index 6→50, hit-area 18px), stop bij OUT-handle. **Vijfde ronde (32e — de killer):** "Clip file not yet rendered" overlay opgelost — cache-buster `?v=<ts>` werd naïef ge-appendt na `withAuth()` waardoor er TWEE `?` in de URL kwamen → backend's token-parse faalde → 403 → onerror overlay. Fix met joiner-check (`?` vs `&`). Alle wijzigingen frontend-only in `static/index.html`. Live geverifieerd op Lisa Korver Hör Berlin set drop #3 met stretch tot 2:16. Zie SESSIE 32 hierboven.
- **2026-05-23 (sessie 31):** Twee critical bugs aangepakt + watermark live + Brand Stack collapsibles. BPM/Key corner-stamp force-off in `cutter.py` (`_load_brand_assets_for_job` zet `bpm_cfg['enabled']=False`). "Follow horizontally" zoom-bug → nieuwe `letterbox` tracking-mode (geen crop, scale-to-fit + black bars), nu default voor nieuwe clips. Watermark JS-bindings + render-pipeline LIVE: 4 endpoints in `app.py` (POST/GET/DELETE/settings), helper `_build_watermark_overlay_segment` in `cutter.py`, alle 6 frontend bindings (upload/clear/toggle/corner/opacity/size). Brand Stack collapsibles via `initBrandStackCollapsibles()` met localStorage state. Edge function `update-usage` zit in repo maar nog NIET gedeployed (Sjuul handmatig). Zie SESSIE 31 hierboven.
- **2026-05-10 (sessie 15):** Marathon UX-/recut-/storage-fix-sessie. Twaalf+ fixes live-getest via Claude in Chrome MCP. Stretch-recut werkt end-to-end (Ediine x Ho_r Berlin: clip 1 ge-stretcht van 16.72s → 21.72s, file daadwerkelijk herrendererd op disk). Source-video persistent in `BASE_DIR/uploads`, snapshot bewaart `video_path`, `_cleanup_source_video` uitgeschakeld. Read-only marker voor oude /tmp jobs (Trim disabled met heldere tooltip). Recent Sets/Library refresh + sort newest-first + View all expand toggle. ★ ZIP empty-protection (backend 400 + frontend fetch+blob). Library 16:9+9:16 beide via aspect-picker skip. Backbutton "← Clips". Trim loading-bar overlay + razor-blade icon + amber cursor op hover. Pauze-knop fix bij clip-switch. Trim-state persistence over logout. Vier features bewust geparkeerd voor volgende sessie (zie "VOLGENDE SESSIE" in SESSIE 15 entry). Zie SESSIE 15 hierboven.
- **2026-05-10 (sessie 14):** Vijf landings in één sessie. Bug 1b (`/api/history` filter op snapshot+output_dir met clip-files) en Bug 1a (jobId persistence in localStorage + restore in `postLoginBoot`) opgelost. VIDEO_EDITOR_PLAN Phase 6 (loop playback toggle + ontimeupdate listener), Phase 3 (J/K/L scrubbing met rAF reverse-loop + K+J/K+L frame step), Phase 4 (snap modes Off/Beat/Bar met binary-search nearest-grid + 8px tolerance). Pure frontend behalve Bug 1b (één endpoint in `app.py`). Backups per stap. parse-checks OK, 144 unieke DOM-ids. Sjuul-handmatige test pending. Zie SESSIE 14 hierboven.
- **2026-05-10 (sessie 13):** Phase 4 deelstap 2d — mini-map onder de timeline. Pure frontend: tl-minimap container met canvas + zoom-window rechthoek + stretch-zone markers. Drag = pan, click buiten rechthoek = jump, scroll-event sync. **VIDEO_EDITOR_PLAN Phase 1 is hiermee 100% klaar.** Zie SESSIE 13 hierboven.
- **2026-05-10 (sessie 12):** Phase 4 S4.1 + S4.2 — live waveform-preview + bron-video-swap tijdens stretch-drag. Lost de "blinde sprong" voorbij clip-grens op. Backend: nieuwe `/api/source/<job>` Range-route. Frontend: `ensureWholeSetWaveformCache` prefetch, `buildStretchPreviewPeaks` slicer, `restoreClipWaveform` helper, drag-handler uitgebreid met rAF-throttled waveform-redraw + one-shot video-src swap. Twee bekende bugs gemeld: clips verdwijnen na hard-reload, Recent Sets toont oude jobs (zie Bekende bugs). Zie SESSIE 12 hierboven.
- **2026-05-09 (sessie 11):** Phase 4 deelstap 2c — pan via click-drag op ruler + middle-mouse, zoom-aware seek-click via 2a's helpers, en framenummer in timecode-bar via ffprobe-detectie tijdens upload-validation. Backend: `_parse_fps_string`, `_inject_clip_fps`, `'fps'` op job-niveau. Frontend: `bindTimelinePan` + zoom-aware `bindTimelineScrub` + `updateEditorTime` frame-display. Geen regressies; oude jobs zonder fps tonen graceful geen frame-counter. Zie SESSIE 11 hierboven.
- **2026-05-09 (sessie 10):** Phase 4 deelstap 2b — zoom-UI. Slider + Ctrl+wheel/pinch + `+/-` keys, allemaal via centrale `setEditorZoom()` met zoom-rond-cursor. Range 0.5×..12× (was 0.5×..6×). Visueel goedgekeurd. Zie SESSIE 10 hierboven.
- **2026-05-09 (sessie 9):** Phase 4 deelstap 2a — coord-systeem refactor. Drie nieuwe helpers (`virtSecToPct`/`relSecToPct`/`pxToVirtSec`) als single source of truth voor timeline-positionering. `STATE.timelineScrollOffset = 0` toegevoegd (klaar voor 2c). `renderTrimRegion()` gemigreerd. Invariance-refactor — visueel/functioneel identiek aan SESSIE 8, geverifieerd. Zie SESSIE 9 hierboven.
- **2026-05-09 (sessie 8):** Phase 4 deelstap 1 — stretch-zone UX (Open follow-up #1 S1). Amber wash + `±Xs` drag-label + active-zone hilight + hover-tooltips, allemaal in `static/index.html`. Geen backend. Visueel goedgekeurd door Sjuul. Live waveform/video preview tijdens drag is parked tot ná Phase 1 zoom/pan. Zie SESSIE 8 hierboven.
- **2026-05-08 (sessies 5–7):** Phase 3 plan-gating end-to-end. Backend helpers + 402-gate + counter + `/api/quota`. Frontend quota-strip + upgrade-modal + watch-folder Pro-gate. Stripe-upgrade flow getest (FREE→PRO flip + counter reset). Zie SESSIE 5/6/7 hierboven.
- **2026-05-08 (sessie 4):** Phase 2 paid-launch — Stripe Checkout + webhook (Supabase Edge Function) + Customer Portal. Zie SESSIE 4 hierboven.
- **2026-05-07 (sessie 3):** Phase 1 auth — Supabase project + auth-overlay + account-chip. Zie SESSIE 3 hierboven.
- **2026-05-06 (sessie 2):** Export-bug gefixed + complete UI-rebuild C1-C4 + folder picker (mac/win) + aspect-keuze popup + custom-label filenames + hard-cut renders + Library Exports met per-card acties + Editor preview groter (alle 4 aspects). Zie SESSIE 2 sectie hierboven.
- **2026-04-26:** Bucket-D2 large file pipeline. Sets >2 uur krijgen 720p proxies, daarna lazy 1080p via `/api/render-clip`. Keyframe index bij upload voor snelle seek.
- **UI redesign (eerder):** OpusClip-stijl. Niet terugdraaien.

---

## Volgende prioriteit — Phase 4 of Phase 5

Twee parallelle paden, zie de "VOLGENDE SESSIE" sectie bovenaan dit document voor de volle uitleg:

**Pad A — Phase 4: Editor improvements** (volgorde uit `VIDEO_EDITOR_PLAN.md`)

1. ✅ **Open follow-up #1 — Timeline stretch UX** (S1). Done in SESSIE 8.
2. ✅ **VIDEO_EDITOR_PLAN Phase 1: zoom + pan + frame-accurate seek** — 100% klaar:
   - ✅ **2a — coord-systeem refactor** (`virtSecToPct`/`relSecToPct`/`pxToVirtSec`-helpers + `STATE.timelineScrollOffset`). Done in SESSIE 9.
   - ✅ **2b — zoom-UI** (slider in toolbar + Ctrl+wheel/pinch + `+/-` keys + zoom-rond-cursor + range 0.5..12). Done in SESSIE 10.
   - ✅ **2c — pan + zoom-aware seek + framenummer** (ruler-drag, middle-mouse-drag, zoom-aware seek-click, framenummer via ffprobe). Done in SESSIE 11.
   - ✅ **2d — mini-map** strip onder de timeline met huidige zoom-window. Done in SESSIE 13.
3. **Phase 2: Draggable in/out handles** — handles renderen al, slepen werkt al sinds SESSIE 1 (verification step in deelstap 1 + 2a). Mogelijk grotendeels af na 2a; opnieuw evalueren ná 2d.
4. **Phase 6: Loop playback** — kleine toevoeging, grote winst in bruikbaarheid.
5. ✅ **S4.1 + S4.2: Live stretch-preview** — waveform/video uitrekken tijdens drag in stretch-zone. Done in SESSIE 12.

Daarna pas: VIDEO_EDITOR_PLAN Phase 3 (J/K/L), Phase 7 (inline expand), Phase 4 (snap), Phase 5 (filmstrip).

**Pad B — Phase 5: Watch-folder backend** (Pro feature, frontend al ontgrendeld in Phase 3)

1. Lokale folder-poller (5s tick, vergelijk met `watch_folder.json` state).
2. Auto-trigger `/api/upload-local` op nieuwe drops.
3. UI-status dynamisch maken + "Recently picked up" lijst.
4. Concurrency: hash-check op file-naam+grootte voorkomt dubbele jobs.

Out of scope tot later: Dropbox/Drive OAuth.

---

## Toekomstige doelen (nog NIET implementeren)

- OAuth voor TikTok/Instagram upload
- Patent aanvragen (NL/EU/global) — besproken, nog niet uitgevoerd
- Packagen als .dmg/.exe

---

## Hoe je hier verder mee werkt

1. Lees dit bestand → begrijp de huidige staat
2. Diagnose → aanpak voorstellen → wachten op "ja" → pas dan uitvoeren
3. Update dit bestand als er iets verandert (bug gefixed, feature toegevoegd, nieuwe bug ontdekt)
