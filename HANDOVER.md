# Omni DJ (voorheen Clip Live) — HANDOVER

> **Lees dit altijd als eerste.** Update dit bestand na elke significante stap.

---

## START HIER — sessie 64 (2026-05-30) — EDITOR-CLEANUP + ICOON + RUNBOOK

> **Status:** code-side klaar en gepusht (commit `9f76839` op `main`). De .app-rebuild en de externe services (Supabase/Stripe/Cloudflare) staan nog open — die moet Sjuul zelf doen. Volledige stap-voor-stap in **`SESSIE64-REBUILD+SERVICES-RUNBOOK.md`**.

**Wat is gedaan deze sessie (allemaal gepusht in `9f76839`):**

1. **Git rebrand (stap 1) bevestigd klaar** — commit `f1211ff` "Rebrand: Clip Live -> Omni DJ" stond al op `main`, branch ge-merged, working tree schoon. Geverifieerd, niets meer te doen.

2. **Rebuild + services runbook opgeleverd** — `SESSIE64-REBUILD+SERVICES-RUNBOOK.md` met letterlijke terminal-stappen voor stap 2 (.app rebuild via `./build_macos.sh dmg`) en stap 3 (Supabase/Stripe/Cloudflare rebrand naar omnidj.com). Registrar = **TransIP** (bevestigd door Sjuul).

3. **App-icoon** — zwarte bolletjes op witte afgeronde achtergrond (uit Sjuul's `omni-dj_black.svg`). Assets in `Omni DJ/static/`: `icon.svg`, `icon_1024.png`, `Omni DJ.iconset/` (10 maten), `make_icns.sh`. **De `.icns` moet Sjuul nog 1× maken** op zijn Mac: `cd "Omni DJ/static" && ./make_icns.sh` (iconutil is Mac-only). OmniDJ.spec pikt `static/icon.icns` automatisch op bij de build.

4. **Editor-cleanup (FEATURE-CLEANUP plan)** in `Omni DJ/static/index.html`:
   - ITEM 4 — Edit/Style/Brand tabs weg uit editor-header.
   - ITEM 5 — "Cue points" header weg; `#ed-cue-meta` (cues · BPM) verplaatst naar de filter-row.
   - ITEM 2 — Drops-filter weg uit het dashboard (All toont toch alles).
   - ITEM 7 — "Sorted by energy score" tekst weg uit subtitel + set-meta.

5. **Twee gele lekken in V2 gefixt** (echte CSS-bugs):
   - **Cue/drops-lijst links:** de v2-overrides matchten `.cue-row`, maar de code rendert `.cue`. Daardoor viel de hele lijst terug op de oude AMBER (gele) styling. Nu dekken de overrides beide classes; cue-time/fav/select volgen de oranje `--v2-accent`.
   - **Export-`<`-knop:** open-state toggelt een `.is-open` class, maar v2 luisterde alleen naar `[aria-expanded]`; de caret-pijl was hardcoded amber. Beide nu `--v2-accent`.
   - Bevinding: de rest van de V2-editor was al volledig oranje; dashboard-chips/ratio zijn neutraal grijs (geen geel).

6. **Landing-fix** — mega-menu item "ClipDrop" → "Drop detection" in `omnidj.com/lib/content/megamenu.ts`. Actieve site verder schoon (domeinen + meta op omnidj.com).

**⏭️ Eerste taken volgende sessie (Sjuul's kant):**

1. **Editor live checken** — dev-server draait al op je Mac (`http://127.0.0.1:5555`). Refresh en bevestig dat de gele randjes in de cue-lijst + export-knop weg zijn.
2. **Icoon afmaken** — `cd "Omni DJ/static" && ./make_icns.sh` → maakt `icon.icns`.
3. **.app rebuild** — runbook stap 2: `./build_macos.sh dmg`. (pyinstaller zit nog NIET in venv → eerst `pip install pyinstaller dmgbuild`; ffmpeg via brew.)
4. **Externe services** — runbook stap 3: Supabase/Stripe/Cloudflare rebrand. Open vraag: welke admin-emails moeten unlimited in Supabase (nu default `omnidj@`/`sjuul@monohq-labs.com`).

**Bewust NIET gedaan (wacht op OK):**
- FEATURE-CLEANUP **ITEM 6** — Library ratio-filter uitbreiden van 2 (9:16/16:9) naar 4 (+1:1, +4:5). Verandert filter-gedrag; aparte beslissing.

**Sandbox-beperkingen die terugkomen:** committen/pushen kan NIET vanuit de tool-sandbox (git-lock-cleanup geblokkeerd + geen GitHub-token). Sjuul plakt het commando zelf in Terminal. Dev-server draait ook niet in de sandbox (venv is macOS-build).

---

## sessie 63 (2026-05-30) — CODE-SIDE REBRAND UITGEVOERD ✅

> **Status:** de volledige code-side rebrand Clip Live → Omni DJ is uitgevoerd en geverifieerd. Externe services (Supabase/Stripe/Cloudflare/Workspace) en de .app-rebuild staan nog open — die moet Sjuul zelf doen (dashboards + lokale build). Domein gekozen = **omnidj.com** (niet omni.com uit het oude plan).

**Wat is gedaan (code + docs):**
- Merknaam-sweep over 75 bestanden: `Clip Live` / `Clipdrop` / `Clip Drop` / `Clipdrop Live` → **Omni DJ**.
- Domein: `clipdroplive.com` / `djclips.nl` / `clipdrop.com` → **omnidj.com**. STRIPE-DNS-RUNBOOK `cliplive.app` → omnidj.com.
- Bundle-ID `com.sjuulstudios.cliplive` → **`com.monolabs.omnidj`**.
- Env-vars `CLIP_LIVE_USER_DATA/PORT/BIND` → **`OMNI_DJ_*`** (launcher.py zet, app.py + cutter.py lezen — geverifieerd consistent).
- localStorage/sessionStorage keys `clipLive.*` + `clipLivePlanOverride/clipLiveActiveArtist/clipLiveArtists/clipLiveRedesignV2` → **`omniDj.*`** (14 keys, incl. template-literals).
- Wachtwoord-blacklist + email-adressen (`business@sjuulstudios.com` → `omnidj@monohq-labs.com`, plan-conform).
- `Sjuul Studios` → **MONO LABS** in copyright-context.
- File-renames: `ClipLive.spec` → `OmniDJ.spec`, 3 mockup-HTMLs in root, 2 business-model docs (binary — interne inhoud nog handmatig).
- launcher.py Linux-pad `~/.clip-live` → `~/.omni-dj`.

**Verificatie (geen git nodig):** alle .py compileren schoon, alle JSON valide, 0 achtergebleven `CLIP_LIVE_` in code, HTML `<title>Omni DJ</title>`, spec CFBundleName = Omni DJ. **Niet** getest: live dev-server run (kan ik niet vanuit sandbox), .app-build.

**Backups vóór rebrand:** git-branch `backup/pre-rebrand-20260529-1545` + `.backups/omni-dj-CODE-backup-20260529-1547.tar.gz`. Pre-rebrand git-commit `71d1aed`.

### ⚠️ Git is NIET gecommit door Claude (sandbox-mount blokkeert git lock-cleanup)
De rebrand-wijzigingen staan **uncommitted** in de working tree. Claude kon niet betrouwbaar committen omdat de sandbox git's lock-files niet kan opruimen. **Sjuul moet zelf committen + mergen + pushen** (Fix 1):
```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ"
git add -A
git commit -m "Rebrand: Clip Live -> Omni DJ (code, env-vars, localStorage, bundle-ID, docs)"
git checkout main && git merge --ff-only feature/auto-mode-and-brand-redesign
git push origin main
```
(Of eerst reviewen met `git diff HEAD` / `git status` voor je commit.)

### ⏭️ Wat nog open is (Sjuul's kant)
1. **Git commit + merge naar main + push** (zie hierboven) — Fix 1.
2. **Dev-server smoketest:** `cd "Omni DJ" && ./start.sh` → check titel "Omni DJ", login zet `omniDj.session`, upload/export werkt.
3. **Externe services** (PLAN-REBRAND sectie 5): Supabase rename + email-templates + SMTP + admin-whitelist SQL, Stripe products/branding, Cloudflare omnidj.com + DNS + Pages.
4. **.app rebuild** met OmniDJ.spec (PLAN-REBRAND sectie 6) + oude `/Applications/Clip Live.app` weggooien.
5. **Niet-kritieke resten** (bewust gelaten): `@sjuulstudios` mock social-handles in demo-data + plannen; sommige historische log-regels in HANDOVER-ARCHIVE.md; binary docx/xlsx interne inhoud; `dist/Clip Live/` oude build (regenereert bij rebuild).

---

## 🌐 sessie 62 (2026-05-29) — LANDING GEPUSHT NAAR GITHUB ✅

> **Status:** landing-page-werk staat nu op GitHub. Remote gekoppeld (HTTPS), 2 commits gepusht naar branch `feature/auto-mode-and-brand-redesign`. Premium-pass-details in `PLAN-website-premium-pass-DECISIONS-2026-05-29.md`.

**Locatie:** `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/omnidj.com/`
**Remote:** `origin` = `https://github.com/sjuulstudios/omni-dj-landing-by-MONO-LABS.git` (HTTPS, repo public, hernoemd vanaf omnidj.com-by-MONO-LABS).
**Branch:** `feature/auto-mode-and-brand-redesign` → gepusht, tracking `origin/feature/auto-mode-and-brand-redesign`.
**Remote state:** `feature/auto-mode-and-brand-redesign` @ `ef89022` · `main` @ `d98cf78` (oude losse landing, ongemoeid). **Nog NIET gemerged naar main.**
**Gepushte commits:** `dbe8240` (omnidj.com site + premium pass) + `ef89022` (folder-rename dj-clip-cutter → Omni DJ + docs/landing/MP4-sync).
**Dev-server:** `cd omnidj.com && npm run dev` → localhost:3000. **Remotion render:** `cd omnidj.com/remotion && npm run render:all`.

> **Auth-noot:** HTTPS-push vereist GitHub Personal Access Token (PAT) als wachtwoord. Sjuul pusht zelf vanuit Terminal; creds zitten in zijn macOS keychain. Geen token in repo/bestanden opgeslagen.

> **.gitignore-uitbreiding (sessie 62, `Omni DJ/.gitignore`):** `OMNI DJ - TEST DJ-SETS/` (12GB), `yolov8n.pt` + `*.pt`, `zibQMEOQ` toegevoegd — anders zou de 39GB-app-map met testvideo's mee-committen. Al genegeerd: output/ uploads/ venv/ dist/ build/ __pycache__/.

### ⏭️ EERSTE TAKEN VOLGENDE SESSIE (Sjuul's prioriteit, in volgorde)

1. ✅ **`git push`** — GEDAAN sessie 62. Remote gekoppeld + 2 commits gepusht. Branch nog niet gemerged naar `main` (bewust; aparte beslissing).
2. **Tool-overview + auto-mode sectie-ruimte verkleinen.** De animatie staat hoog in de sectie met te veel verticale leegte eronder vóór de volgende sectie. Strakker maken (sectie-padding / animatie-positie). Bekend en akkoord; nog niet uitgevoerd. **= nu de eerstvolgende code-taak.**

### Wat deze sessie is gedaan (premium pass, alles live geverifieerd)

**Ronde 1 — 17 premium-pass taken** (zie DECISIONS-doc voor 37 keuzes):
- Motion-fundament: The Drop easing (`--ease-drop` cubic-bezier(0.16,1,0.3,1), `--ease-smooth` is alias), Geist Mono (`geist@1.7.1`, self-hosted) voor cijfers/timestamps, creme-mute 0.6→0.72 (AAA).
- Sectie-overgangen: hairline DarkSeam tussen dark-secties, `.section-bridge` gradient, hero op `bg-ink-900`.
- Dep-cleanup: framer-motion + @studio-freight/lenis verwijderd, `lib/motion.ts` weg, GSAP lazy-loaded in roadmap → **154kB → 117kB First Load JS**.
- Nav: chevron overshoot-spring + multi-layer mega-menu schaduw.
- Pricing: Pro-card elevatie (translateY -8 + shadow) + ademende oranje ring (`.pricing-pro-ring`), mono unit-labels.
- Contact: 2 velden + progressive disclosure (naam/rol verschijnen bij typen), "Send →".
- Hero: set-timeline strip (`components/hero/SetTimeline.tsx`, signature motief), beta-form oranje chevron + slide-in success (geen teller).
- Tool-overview, workflow, auto-mode, features, roadmap, carousel, audience-tabs, closing — zie DECISIONS-doc.
- Sign-up knop: oranje → creme + zwarte tekst (`.btn-creme`).
- Loading-state: RemotionMp4 fade pas op `onPlaying`.

**Ronde 2 — feedback-fixes:**
- Scroll-offset: `.section { scroll-margin-top: 96px }` + roadmap GSAP pin `start: 'top top+=80'` → "Roadmap." titel valt niet meer onder de nav.
- Features-accordion single-open (`openIndex` i.p.v. Set) → lost Social/Insights-overlap met gepinde roadmap op.
- Hero CTA's: Download solide creme (links) + Drop your DJ-set transparant dashed (rechts), subline 1 regel (`md:whitespace-nowrap`). DropField herontworpen naar transparante knop.
- **Echte Remotion-MP4's** (Sjuul's keuze i.p.v. live CSS):
  - `ToolOverviewFlow.tsx` herbouwd: step-rail (Analyse/Reframe/Publish), playhead + pulserende DROP-labels, spring-pop shorts, → arrows. ToolOverview-component terug naar RemotionMp4.
  - `AutoModePipeline.tsx` herbouwd: AI-tekst weg, processing-tile met checkmarks (Cut/Brand/Caption), spring-pop posts, minHeight 380→240.
  - colors.ts creme-mute → 0.72.
- Witruimte auto-mode verkleind (mt-14→mt-10, mt-16→mt-8, 16/6→16/5).
- 3 MP4's gerenderd op Sjuul's Mac (logo-reveal 1.4MB, auto-mode 410kB, tool-flow 581kB) → zitten in `public/remotion/` + commit.

**Twee bugs gevonden + gefixt tijdens live review:**
1. Set-timeline drop-markers vielen niet op hun cluster (transform-conflict) → vaste cx/cy op gesnapte bar-index, pulse animeert alleen opacity.
2. Hydration-warning in SetTimeline (float-drift) → `r3()` rondt geometrie af op 3 decimalen.

**Verificatie:** app tsc 0 errors, remotion tsc 0 errors, `next build` groen (18/18), console 0 errors. Volledige pagina live doorgelopen via Chrome MCP op localhost:3000.

### Asset-hooks klaargezet (Sjuul levert binnen 7 dagen)
- Workflow hover-video: `HOVER_VIDEOS` map in `WorkflowGrid.tsx`.
- Artist clips: `video` veld per artist in `lib/content/artists.ts` (8 tiles, statische views).
- Features screencasts: vervangen `FeatureWireframe` per rij later.
- Hex-codes: nog placeholder `#FF6A1A` + `#F5EFE3`; 1× find-replace zodra Sjuul de echte uit de tool geeft.

### Bekende dev-quirk
Na veel snelle edits kan de draaiende `npm run dev` de Tailwind-CSS stoppen met serveren (kale pagina). Productie-build blijft groen. Fix = dev-server herstarten (Ctrl+C + `npm run dev`).

### Toestemmingen gebruikt deze sessie
✅ Bash, File-access op omnidj.com, Computer-use (Terminal click-tier + Chrome read-tier), Chrome MCP, git commit (lokaal).
❌ git push, DNS, Stripe, Supabase, echte assets, hex-codes.

---

## 🌐 sessie 60 (2026-05-29 nacht-build) — WEBSITE UITGEVOERD

> **Status:** complete autonome nacht-build van omnidj.com marketing-site afgerond. Alle 4 fases uit `PLAN-website.md` opgeleverd. Volledig logboek in `BUILD-LOG-website-2026-05-29.md`.

**Locatie:** `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/omnidj.com/`

**Stack:** Next.js 14.2.18 + TypeScript + Tailwind 3.4 + App Router + static export. Helvetica Neue system stack. Framer-motion + GSAP + Lenis dependencies geinstalleerd (huidige animaties zijn CSS-keyframe + IntersectionObserver, geen runtime dependency op die libs nodig tot een complexere section dat vraagt).

**Wat live klaar staat:**
- 1 home page met 9 secties (Hero met 8-circle logo reveal + 3 CTAs + pillars, Artist carousel, Enterprise tabs, Tool overview SVG flow, Workflow 3-col, Auto-mode looping animation, Features accordion, Roadmap 12-item carousel, Closing CTA)
- 8 andere pages (`/pricing` met EUR+USD side-by-side + matrix, `/contact` met form + Flask stub, `/collective`, `/for-business`, `/features`, `/solutions`, `/resources`, `/legal/terms|privacy|trust`)
- 404 not-found page
- StickyNav (logo + by MONO LABS + 5 nav-items + login/signup + mobile burger)
- Footer (4 link-columns + 5 social icons + copyright)
- Backend Flask skeleton (`backend/` met routes/contact.py + routes/beta.py + .env.example + README) — **NIET draaiend**
- SEO complete: metadata, sitemap.ts, robots.ts + .txt, dynamic favicon, dynamic OG-image
- A11y: skip-link, ARIA labels, focus-visible, prefers-reduced-motion

**Verificatie:** `npx tsc --noEmit` = 0 errors over alle 4 fases. Sandbox `next build` hangt door cross-mount SWC binary issue — werkt native op je Mac.

### Status na 29 mei build + improvements pass

**Site is volledig functioneel** in zowel dev (`localhost:3000`) als productie (`out/` static export, getest via `npx serve out`).

**Wat draait:**
- Dev server: `npm run dev` op port 3000
- Production preview: `npx serve out` op port 62575 (poort 5000 in use)
- Remotion: 3 MP4s gerendered in `public/remotion/` (logo-reveal, auto-mode, tool-flow)
- Production build: 18/18 static pages, home = 56.8 kB / 154 kB First Load JS

**Wat is afgerond in deze sessie (60 vervolg, ochtend):**

1. Initial scaffold + 4 phases (zie BUILD-LOG)
2. Remotion compositions toegevoegd voor 3 hero-animaties
3. 5 improvement chunks doorgevoerd na live smoketest:
   - Hero polish (kleiner logo, 1-col layout, copy fixes, "Join beta" pill button)
   - Mega-menu pop-outs (Features 3-col, Solutions 2-col, soon-chips)
   - DJs audience tab toegevoegd (1e tab), per-audience feature curatie
   - Features accordion shrink (1 viewport, multi-open, headline op 1 regel)
   - Roadmap scroll-driven horizontal reveal met alternating branches (GSAP ScrollTrigger)
   - Artist carousel continuous slow auto-scroll (90s loop, hover-pause, reduced-motion-safe)

**Bestanden voor referentie:**
- [`PLAN-website.md`](PLAN-website.md) — originele build plan
- [`PLAN-website-improvements-2026-05-29.md`](PLAN-website-improvements-2026-05-29.md) — improvement pass plan
- [`PLAN-website-premium-pass-2026-05-29.md`](PLAN-website-premium-pass-2026-05-29.md) — NEW: deep premium upgrade proposal
- [`BUILD-LOG-website-2026-05-29.md`](BUILD-LOG-website-2026-05-29.md) — per-fase decision log

### Volgende stap (in volgorde)

**Voor je verder gaat met premium-pass:**
1. **Smoketest** alle nieuwe elementen via `http://localhost:62575` (productie versie):
   - Hover Features + Solutions in nav → mega-menus
   - Klik door alle 5 audience tabs (DJs default)
   - Scroll naar Roadmap → pinned scroll-reveal animation
   - Scroll naar artist carousel → continuous loop
   - Open features accordion (multi-open)
   - Mobile (DevTools 390px) → mega-menus collapsed naar accordion, roadmap vertical stack
   - Reduced-motion (DevTools → Rendering → Emulate prefers-reduced-motion) → loops stoppen

2. **Lees PLAN-website-premium-pass-2026-05-29.md** voor de volgende ronde upgrades — deep proposal met specifieke vragen per section.

**Voor productie deploy** (later):
- Render-stap voor Remotion (al gedaan)
- Hex codes confirmeren (orange + creme) uit Omni DJ tool
- Real artist videos in `public/videos/artists/`
- Real UI screenshots in `public/images/`
- Studio+ feature lijst invullen
- Flask backend wire'n + deployen (Fly.io/Railway)
- Cloudflare Pages deploy

### Original setup commands

```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/omnidj.com"
npm run dev
```

2. **Production build** verifieren:
   ```
   npm run build
   ```
   Output gaat naar `out/`. Test met `npx serve out -p 5000`.

3. **10 open items voor jou** — alle in `BUILD-LOG-website-2026-05-29.md` sectie "Wat Sjuul morgen moet doen". Belangrijkste:
   - Exacte hex codes voor orange + creme vervangen in `tailwind.config.ts` + `app/globals.css`
   - Hero headline finaliseren uit 8 alternatieven (PLAN-website.md sectie 3.2)
   - Studio+ feature-lijst invullen in `lib/content/pricing.ts`
   - Real artist videos in `/public/videos/artists/`
   - Real UI screenshots in `/public/images/`
   - Flask backend wire'n + deployen (Fly.io/Railway)
   - Cloudflare Pages deploy + DNS

**Wat Claude bewust NIET deed:**
- `git init` / commits / pushes
- DNS / Cloudflare / Supabase / Stripe / Apple notary
- Geen real assets gedrop't (placeholders met clear labels)
- Geen `npm run build` success-bevestiging (sandbox-limitatie)

**Volledige decision log + per-fase samenvatting:** [`BUILD-LOG-website-2026-05-29.md`](BUILD-LOG-website-2026-05-29.md)

### Toestemmingen die deze sessie zijn gebruikt
✅ Bash (npm install + tsc + sandbox dev-server poging)
✅ File-access op `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/omnidj.com/`
✅ Computer-use (Terminal/Chrome/Finder — granted, niet effectief gebruikt want sandbox-server niet bereikbaar van host-Chrome)

### Toestemmingen NIET gebruikt
❌ Stripe / Supabase / DNS / Email / Git push

---

## 🌐 WEBSITE-PLAN — sessie 28-05-2026 — NIET UITGEVOERD

> **Status:** plan geschreven, ligt klaar voor een aparte build-sessie. Verwijst naar [`PLAN-website.md`](PLAN-website.md). Geen code geschreven deze sessie, alleen planning.

**Aanleiding.** Sjuul wil de omnidj.com marketing-website bouwen, gebaseerd op visuele referenties van Weave.figma.com, Sana Labs, Cobrand, Opus.pro en Opus.pro/agent. Premium look met focus op zwart-dominante backgrounds, creme tekst en spaarzaam oranje (kleuren matchen de Omni DJ tool zelf). Geen "glow" effects.

**Beslissingen vastgelegd in PLAN-website.md.**

- **Stack:** Next.js 14 (static export via `output: 'export'`) + Tailwind + Framer Motion + GSAP + Lenis voor smooth scroll. Flask backend voor forms (provider-agnostisch via SMTP env vars).
- **Hosting:** Cloudflare Pages voor frontend (geen Vercel), Fly.io of Railway voor Flask backend op subdomein `api.omnidj.com`. Domein omnidj.com is van Sjuul via TransIP, DNS via Cloudflare.
- **Locatie:** `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/omnidj.com/` (apart subfolder naast de app code).
- **Logo:** 8-circle ring (8 witte cirkels in een rondvorm). PNG referenties geleverd door Sjuul (wit-op-zwart + zwart-op-transparant). Hero animatie: wordmark glijdt vanaf rechts, ring fadet in vanaf links + roteert 360°, daarna loop slow 360° rotatie elke 10s.
- **Typografie:** Helvetica Neue system stack (Bold, Medium, Light, fallback Arial). Geen Inter/Geist.
- **Kleuren:** Background `#000000`, creme `#F5EFE3` (placeholder — exact hex moet Sjuul bevestigen vanuit de tool), oranje TBD (placeholder `#FF6A1A` — exact hex moet uit de Omni DJ tool komen).
- **Hero copy (working final):** "Turn your hours long DJ-sets into 20-second viral clips." Met 8 alternatieven in plan-sectie 3.2 voor finale pick.
- **Hero CTAs:** drie elementen — Drop your DJ-set field + Download Omni DJ button + Join the beta email field.
- **Pricing:** 4 tiers — Free €0 (analyse 2 sets + library only) / Pro €75 (4 sets/maand + Editor + Brand + Captions + Social + Calendar) / Studio €200 (alles uit Pro + Multi-artist + Batch + Auto-mode + Watch-folder + Insights) / Studio+ Custom (TBD). 15% off yearly. EUR + USD beide ondersteund via toggle.
- **Roadmap:** horizontale carousel, 12 items in Sjuul's eigen volgorde (geen datums).
- **Andere secties:** sticky nav (Features / Solutions / Resources / Pricing / For business) met "by MONO LABS" tagline naast logo, artiest-carousel (9:16 verticale video frames met TikTok/Instagram badge), enterprise tabs (4 audiences), tool overview met Weave-style SVG connector flow, workflow 3-column, Auto-mode big looping animation, features accordion (Analyse/Library/Brand/Social/Calendar/Insights), closing CTA, footer (Get Started / Company / Connect / Resources + 5 social icons: Instagram/TikTok/YouTube/LinkedIn/Facebook).
- **Forms:** Flask backend op port 5556 (5555 blijft voor app). Endpoints `/api/contact` (role-routed dropdown) en `/api/beta-signup` (SQLite). SMTP-agnostisch.

**Wat het plan NIET dekt (out of scope).**

- Login/signup flow (alleen placeholder nav-links)
- User dashboard
- Stripe payment integratie (komt later)
- Knowledge Center content (footer-link is `#` placeholder)
- Blog/changelog content

**Nog open vóór code-sessie (sectie 9b van plan).**

1. Exacte hex codes voor creme + oranje uit Omni DJ tool
2. Finale hero headline kiezen uit 8 alternatieven
3. Currency switcher: side-by-side vs toggle
4. Studio+ feature-lijst definieren
5. Screenshots van Analyse/Editor/Auto-mode schermen voor placeholders

**Kickoff-prompt voor volgende sessie** (paste in nieuwe chat in Omni DJ folder):

> Read PLAN-website.md and start Phase 1 of the build. Scaffold the Next.js project in /omnidj.com/, set up Tailwind + global styles + Helvetica stack, then build StickyNav and Footer components. Stop after Phase 1 for review.

**Verband met REBRAND-PLAN.** De website is een afzonderlijk traject. Rebrand-sessie gaat over de app + Supabase + Stripe + Cloudflare DNS voor omni.com / monolabs. De website-build gebruikt het al bestaande omnidj.com domein op Cloudflare en raakt geen app-code. Beide trajecten kunnen onafhankelijk worden uitgevoerd.

**Bestand:** [`PLAN-website.md`](PLAN-website.md) — staat in project-root: `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/PLAN-website.md`.

---

## 🏷️ REBRAND-PLAN — sessie post-52 (2026-05-27) — NIET UITGEVOERD

> **Status:** plan geschreven, ligt klaar voor een aparte big-bang rebrand-sessie. Pas uitvoeren als de 8 OPEN VRAGEN in sectie 14 van het plan beantwoord zijn. Verwijst naar [`PLAN-REBRAND-OMNI-DJ-2026-05-27.md`](PLAN-REBRAND-OMNI-DJ-2026-05-27.md).

**Aanleiding.** Sjuul wil de volledige rebrand Omni DJ / Omni DJ / Omni DJ / DJClips → **Omni DJ (by MONO LABS)** in één big-bang sessie afronden: code, externe services (Stripe + Supabase + Cloudflare + Gmail/Workspace), .app-bundle, domein omni.com, alle docs. Geen users, dus Stripe customers + Supabase auth blijven behouden (alleen rename). Sjuul zelf geeft als input: `omnidj@monohq-labs.com` + `sjuul@monohq-labs.com` whitelisten als admin-accounts.

**Scope-scan-resultaten (deze sessie, vóór folder-rename van sessie 59).** Ik heb een volledige grep gedraaid over de toenmalige `/Omni DJ/`-folder en vond **±900 occurrences in 71 files**, verspreid over **5 verschillende oude merknamen** die door elkaar in de codebase staan:

> **Historische naam-archeologie (oude merknamen vóór rebrand sessie 63) — bewust niet mee-gerebrand, documenteert wat er WAS:**
- `Clip Live` (app-titel, env-vars `CLIP_LIVE_*`, Bundle ID `com.sjuulstudios.cliplive`, localStorage `clipLive.*`, feature-flag `clipLiveRedesignV2`) — ±500 hits
- `Clipdrop` / `Clip Drop` (Supabase migrations comments, oude `CLIP DROP DJ-SETS`-folder, Supabase project display-name = "Clip Drop Live") — ±50 hits
- `Clipdrop Live` / `clipdroplive.com` (landing-pagina title, og:url, canonical) — ±30 hits
- `DJClips` / `djclips.nl` (beoogd productie-domein, GitHub-repo `sjuulstudios/djclips.nl-by-MONO-LABS`, reset-password footer, wachtwoord-blacklist in auth.py:418) — ±75 hits
- `Sjuul Studios` / `sjuulstudios` (copyright PyInstaller spec, Apple Notary, KvK/VAT context in Stripe webhook) — ±40 hits

**Wat het plan dekt.** File-by-file breakdown (sectie 3), definitieve naamgebruiks-tabel per context (sectie 2), exacte sed-commando's voor de code-rebrand (sectie 7), stap-voor-stap dashboard-instructies voor Supabase (project rename + email-templates + custom SMTP + URL-allowlist + admin-whitelisting via SQL), Stripe (account-branding + products renamen — IDs blijven gelijk), Cloudflare (nameservers + DNS-records + Pages-deploy), Gmail/Workspace (App Password voor SMTP, DKIM/SPF/DMARC, email-aliassen via Cloudflare Email Routing), .app-rebuild met nieuwe Bundle ID `com.monolabs.omnidj` + nieuwe paths in launcher.py, verificatie-checklist (sectie 10), risico's + rollback-procedure (sectie 12). Big-bang volgorde-overzicht in sectie 13. Verwachte sessie-tijd: 4-6u actief + 1-24u DNS-propagatie passief.

**Email-whitelist mechanisme.** Code heeft géén email-allowlist. Whitelisting loopt via Supabase `profiles.role='admin'` + `plan='studio'`. SQL-snippet zit in plan sectie 5.1 stap 5. Sjuul moet eerst beide accounts via normale signup-flow registreren (anders bestaat de profiles-rij niet), dan SQL draaien.

**Belangrijkste vondsten die in plan-uitvoering aandacht vereisen.**
1. **Supabase project heet "Omni DJ"** in dashboard — vierde brand-variant die in geen enkele code-string voorkomt, alleen in `supabase/.temp/linked-project.json`. Moet handmatig in dashboard hernoemd worden naar "Omni DJ".
2. **`.env` met live secrets staat in repo-folder** (`dj-clip-cutter/.env`) — bestaand security-issue uit audit 2026-05-12. OPEN VRAAG (5 in plan) of we secrets roteren tijdens rebrand-sessie.
3. **Wachtwoord-blacklist in `auth.py:418`** bevat `'omnidj1', 'omnidj123', 'omni1', 'omni123'` — moet mee in sed-replace.
4. **9 localStorage-keys** met `clipLive.*` prefix (session/activeJobId/trim/exportDir/exportSettings/lastExportDir/wizardState/brandstack-collapsed/RedesignV2) — bestaande user-sessies worden gewist bij rename. Geen users dus geen probleem.
5. **`~/Library/Application Support/Omni DJ/`** macOS user-data folder wordt door launcher.py hernoemd naar `Omni DJ` — bestaande job_history.json gaat verloren bij upgrade. Geen users.
6. **Landing-pagina hardcoded canonical = `omnidj.com`** (niet omnidj.com) — multiple oude domeinen ooit gebruikt.

**8 OPEN VRAGEN in sectie 14 van het plan** die Sjuul moet beantwoorden vóór uitvoering: registrar van omni.com, GitHub-org `monolabs` bestaat, Apple Developer-account migratie, Stripe-entity juridische naam, `.env` secret-rotatie scope, workspace-folder rename via Finder of git, status oude `clipdrop-landing-deploy/`-folder, visual-identity placeholder vs nieuwe assets.

**Wat dit plan NIET doet** (sectie 15): Stripe LIVE-mode activeren (eerst stabiel onder Omni DJ in TEST), marketing-launch / beta-uitnodiging-mails (per [[feedback_beta_flyer_skip]]), nieuw logo/visual identity-refresh (Sjuul werkt hier nog aan), Apple Developer migratie, Stripe entity wijzigen, `.env`-secrets roteren, git-history rewriten, `.bak`-backups rebranden.

**Update na sessie 59.** Sjuul heeft op 28 mei alvast de folder-renames in Finder uitgevoerd ([[project-folder-renames-2026-05-28]]). De live code-paden zijn in sessie 59 gepatcht voor de folder-rename, maar alle andere rebrand-werk (sed-replace code + UI strings + .app-bundle + externe services + DNS + email-templates) wacht nog op de big-bang sessie volgens dit plan.

**Bestand:** [`PLAN-REBRAND-OMNI-DJ-2026-05-27.md`](PLAN-REBRAND-OMNI-DJ-2026-05-27.md) — staat in project-root (op nieuwe pad: `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/PLAN-REBRAND-OMNI-DJ-2026-05-27.md`).

---

## 📁 FOLDER-RENAMES — sessie 59 (2026-05-28)

Sjuul heeft handmatig in Finder drie folders hernoemd. De nieuwe namen zijn:

| Was | Is nu |
|---|---|
| `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/` | `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/` |
| `Omni DJ/dj-clip-cutter/` | `Omni DJ/Omni DJ/` |
| `Omni DJ/Omni DJ/CLIP DROP DJ - SETS/` | `Omni DJ/Omni DJ/OMNI DJ - TEST DJ-SETS/` |

**Claude heeft toegang** tot `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/` via cowork-mount. Alle Read/Write/Edit/Grep/Glob werkt direct op die nieuwe pad-structuur.

### Code-impact-check (uitgevoerd sessie 59)

Scan gedaan met `Omni DJ/dj-clip-cutter` + `CLIP DROP DJ - SETS` + `CLIP DROP DJ-SETS` patterns. Resultaat:

**A. Gepatcht (echt break-risico):**
- `Omni DJ/build_sess53.sh` regel 3 — executable cd-commando
- `Omni DJ/test_export_settings.py` regel 11 — docstring instructie
- `Omni DJ/scripts/cleanup_legacy_jobs.py` regels 14 + 25 — docstring instructies
- `Omni DJ/supabase/functions/update-usage/index.ts` regel 29 — deploy-header
- `Omni DJ/supabase/functions/create-portal-session/index.ts` regel 19 — deploy-header
- `Omni DJ/supabase/functions/stripe-webhook/index.ts` regel 25 — deploy-header
- `Omni DJ/supabase/functions/create-checkout-session/index.ts` regel 24 — deploy-header
- `Omni DJ/supabase/functions/stripe-webhook/README.md` regels 10 + 49 — deploy-instructies
- `Omni DJ/static/index.html` regels 11566 + 11610 — UI placeholder voor large-file path picker (was "CLIP DROP DJ-SETS", nu "OMNI DJ - TEST DJ-SETS")

**B. BEWUST NIET aangeraakt (geen scope deze sessie):**
- `launcher.py` regel 58/60/65 — gebruikt `~/Library/Application Support/Omni DJ/` als macOS user-data folder. Hernoemen zou alle bestaande user-data orphaned maken. Per memory `project_omni_dj_rebrand.md`: aparte rebrand-sessie.
- `OMNI_DJ_USER_DATA` env-var in `app.py`, `runtime_config.py` — zelfde reden.
- `OmniDJ.spec`, `build_macos.sh`, `entitlements.plist`, `CFBundleName=Omni DJ` — bundle/app-naam. Aparte rebrand-sessie.
- Alle `.md` history-files (PLAN-*, SESSIE-*, archives) — historisch correct dat ze "Omni DJ" zeggen.
- Alle `*.bak` backups.

### Verificatie
```
grep -r "Omni DJ/dj-clip-cutter\|CLIP DROP DJ - SETS\|CLIP DROP DJ-SETS" \
  /Users/sjuulsmits/Documents/Claude/Projects/Omni\ DJ \
  --include="*.py" --include="*.sh" --include="*.ts" \
  --include="*.html" --include="*.plist" --include="*.spec" \
  --include="*.json" --include="*.css"
```
→ 0 hits. Alle live code clean.

### Update voor jezelf in toekomstige sessies
Wanneer je `cd` doet, gebruik nu: `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"` (twee keer Omni DJ, want subfolder).

---

## ⚡ START HIER — sessie 59 vervolg (28 mei middag/avond)

**Project:** Omni DJ — DJ-set → vertical/landscape clip generator
**Eigenaar:** MONO LABS
**Branch actief:** `feature/auto-mode-and-brand-redesign` (sessies 57+58 wel committed, sessie 59-werk nog niet)
**Bundle:** `/Applications/Omni DJ.app` (sessie 56 versie, sessies 57+58+59 alleen op disk)
**Dev-server:** `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ" && ./start.sh` → http://127.0.0.1:5555

### Status na vervolg-sessie 59

Sessie 58 was sluitend (zie hieronder). Sessie 59 vervolg deed:

**1. Pre-fix login UI (op verzoek tijdens sessie-start):**
- Login-scherm balk-achtergrond + logo + "DJ-set studio" sublabel weg, "Omni DJ" wordmark, active-tab pill werkt nu.
- Live geverifieerd via Chrome MCP.

**2. Selection-tray verhuisd naar top-overlay balk (`#export-sel-bar`):**
- Nieuwe inline `.est-tile` met 9:16 vertical thumbnails, dun text-balkje (naam + tijdstamp), kruisje exact in rechterbovenhoek met fade-in op hover.
- Hover-video: muted-loop start meteen, audio gaat aan zodra video playable is. Mouseleave pauseert + cleant src voor RAM.
- Legacy bottom-tray `#selection-preview-bar` wordt in v2 verborgen via CSS-override.
- **NIET live geverifieerd in browser** (mount viel weg, code-side wel klaar). Sjuul moet visueel testen.

**3. Auth-incident diagnose — VEILIG (geen leak):**
- Sjuul meldde "Library toont sets van ander account".
- Diagnose: 7 sets in Library, ALLEMAAL onder user_id `d86a3a54...` = `omnidj@monohq-labs.com`.
- Backend (`/api/history`, `/api/clip/`, `_require_job_access`) doet correcte ownership-check + 404-by-default — geen RLS-bypass.
- Conclusie afgewacht (Sjuul moet bevestigen): zijn de 4× Lisa Korver + 2× Ediine + 1× Franky inderdaad allemaal van zijn business@ account, of zit er een set tussen van ander account?
- Preventief: localStorage cache-residue fix klaar voor implementatie (oude trim/activeJobId keys uit vorige sessies).
- Volledig rapport in `AUTH-INCIDENT-2026-05-28.md`.

**4. Feature-lijst van 28 mei vastgelegd (14 items):**
- Quick wins: Drops-filter weg, Edit/Style/Brand-buttons editor-header weg, Cue points header weg, layout-shift filters omhoog, Sorted-by-energy weg, "+ New set" weg, 4 aspect-ratio filters in Library (9:16, 1:1, 4:5, 16:9), Calendar zondag-fix + scrollbar styling.
- Grote items met plannen vereist: Brand-page visueel/compact, Social-page persoonlijker (profielfoto's), Insights uitbreiding (account-growth + per-post detail).
- Volledige plan in `PLAN-2026-05-28-FEATURE-CLEANUP.md`.

### Volgende stap voor Sjuul (in volgorde)

1. **Antwoord op auth-vraag** (zie `AUTH-INCIDENT-2026-05-28.md` einde): zijn de 7 zichtbare projects allemaal van omnidj@monohq-labs.com of zat er iets tussen van een ander account?
2. **Selection-tray visueel testen** in dev-server v2 op http://127.0.0.1:5555: selecteer 2-3 clips in Library Clips-view, check de tray bovenaan met 9:16 thumbs + hover-audio + kruisje-op-hoek.
3. **Plannen-batch goedkeuren of bijsturen** (`PLAN-2026-05-28-FEATURE-CLEANUP.md`): per quick win OK/skip, per groot plan A/B/C OK voor implementatie of redesign.
4. **Daarna**: commit sessie 59 wijzigingen + rebuild.

### Open items uit sessie 58 (niet kritisch, voor latere sessies)

- Logo-upload size cap (2MB enforce in FileReader-flow)
- Brand-pack export data-URL strip (handmatig verifiëren)
- Auth `?token=` URL-pattern vervangen voor omnidj.com productie
- Backend route-audit sessie 56-57 write-routes
- Tier-bypass server-side check voor multi-tenant Supabase
- Insights mock-data inconsistentie (Best clip vs Published count)
- Responsive cross-check op 980px + <700px
- Cross-browser Safari check

### Open items uit sessie 59 vervolg (28 mei middag)

- Cache-residue fix nog te implementeren: hook in `postLoginBoot` die stale `clipLive.trim.<jobid>.*` en `clipLive.activeJobId` weghaalt als jobid niet in `/api/history` zit
- 14 feature-cleanup items wachten op Sjuul's go/no-go per item
- 3 grote plannen (Brand-visueel, Social-persoonlijker, Insights-uitbreiding) wachten op Sjuul's OK

### Toestemmingen al doorgegeven (lopen door)
✅ Computer-use voor app management
✅ Bash terminal voor dev-server, builds, tests
✅ File-access op heel `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/`
✅ Supabase migration-files schrijven (geen `db push`)
✅ `pip install watchdog` in venv
✅ Git commits + branch werk

### Toestemmingen NIET doorgegeven
❌ Stripe live-mode toggle
❌ Supabase `db push` of dashboard-mutaties
❌ DNS / Cloudflare wijzigingen
❌ Email versturen via SMTP
❌ `git push` naar remote
❌ App-Store / DMG distributie

---

## ⚡ ARCHIVED — sessie 58 briefing (oorspronkelijke opdracht)

**Project:** Omni DJ — DJ-set → vertical/landscape clip generator
**Eigenaar:** MONO LABS
**Branch actief:** `feature/auto-mode-and-brand-redesign` (afgesplitst van main in sessie 57, nog niet gemerged)
**Bundle:** `/Applications/Omni DJ.app` (sessie 56 versie — sessie 57 wijzigingen NIET in bundle, alleen in `static/index.html` op disk)
**Dev-server:** `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ" && ./start.sh` → http://127.0.0.1:5555

### EERSTE TAAK SESSIE 58 — VOLLEDIGE AUTONOME SMOKETEST + SECURITY + UI

> **Claude moet deze taak ZELFSTANDIG uitvoeren bij sessie-start. Niet eerst aan Sjuul vragen wat te doen. Niet wachten op input. Pas stoppen om te overleggen als er een blocker is die alleen Sjuul kan oplossen (bijv. niet-werkende auth, ontbrekende env-vars, productie-data wijzigingen).**

**Sessie 57 leverde 3 nieuwe fases code-side op (zie hieronder) maar zonder live verificatie. Sessie 58 moet die verificatie alsnog doen, plus een brede security + UI audit, voordat Sjuul kan committen en rebuilden.**

#### Vereiste tools

Laad via ToolSearch wat nodig is:
- `chrome` keyword → alle `mcp__Claude_in_Chrome__*` tools
- `computer-use` keyword → alle `mcp__computer-use__*` tools (alleen voor zien wat er op scherm staat, niet voor klikken — Chrome zit op read-tier)
- `TaskCreate`, `TaskUpdate`, `TaskList`

#### Plan in 4 blokken — werk ze in volgorde af

##### BLOK 1 — Dev-server starten + live UI-check (Chrome MCP) [60-90 min]

1. Check of `/Applications/Omni DJ.app` draait → quit 'm met `mcp__computer-use__open_application` + `osascript -e 'tell application "Omni DJ" to quit'` of via bash
2. Start dev-server via bash: `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter" && nohup ./start.sh > /tmp/devserver.log 2>&1 &` — wacht ~5s tot Flask listening op 5555
3. Verifieer met `curl -s http://127.0.0.1:5555/ | head -50` dat de page laadt
4. Navigeer via Chrome MCP naar `http://127.0.0.1:5555`
5. **Login indien nodig** — Sjuul's account is `omnidj@monohq-labs.com` (testen via Profile-card). Als auth-overlay verschijnt, log Sjuul in (vraag wachtwoord als nodig). Of test als anonymous user — voor UI-check is auth niet vereist.
6. Console: `localStorage.setItem('omniDjRedesignV2','1'); location.reload();` via Chrome MCP `javascript_tool`
7. **Loop alle views door en maak screenshot/text-dump van elke view:**

| View | Check |
|---|---|
| Analyse | Drop-zone, "Continue editing" als history aanwezig, 3 intake-tiles (Watch/Dropbox/Drive) |
| Library | Projects-tab (4-koloms grid), Exports-tab — klik project → opent Clips-view |
| **Brand** (NIEUW) | Sticky top met "Brand-pack: Artist name ▼" dropdown, dan 9 cards: Brand Kit / Watermark / Caption Presets / Clip Templates (met 4 built-ins) / Hooks / CTAs / Caption Copy (5 platform-velden) / Hashtag Sets / Stickers + extras. Klik dropdown — menu opent. Klik "+ New preset" — modal opent. Sluit modal. Upload een logo (kan dummy data-URL zijn). Check accent-color picker werkt. |
| Social | 4 account-cards met "Postiz soon" badges, recent-posts feed |
| Calendar | Month-view, klik dag → schedule-modal opent. Sluit modal. Klik week-toggle. |
| Insights | KPI-cards, line-chart, top-clips, donut. Klik 7d/30d/90d range. |
| **Sidebar divider + Auto-mode** (NIEUW) | Direct onder Insights moet een dun crème lijntje zijn (rgba 220,200,170 @ 22%). Daaronder Auto-mode entry met klok-icoon. |
| **Auto-mode** (NIEUW) | Free user → paywall-overlay met grote Upgrade-knop. Set tier via console: `STATE.tier='studio'` + reload. Dan: pipeline 6-staps grid (Publish heeft lock-ico voor Studio+), watch-folders card, brand-defaults card, publish-schedule grid, queue+recent, safety. Klik "Quick-enable: Review mode" → 5 stappen worden ON. Klik "+ Add folder" → modal opent. Set tier `studio_plus` + reload → schedule-grid wordt klikbaar. Klik conservative-preset → 3 tiktok-slots active. |
| Settings | Local-first hero, Watch folder card, Profile card (Sjuul wilde Profile hier laten), Workspace card, Diagnostics. **Profile MOET hier nog staan** — niet verhuisd. |

8. **Regressie-check:** zet v2-flag UIT (`localStorage.setItem('omniDjRedesignV2','0')` + reload) — oude UI moet 100% intact zijn, geen layout-breuk.
9. **Console-errors monitoren tijdens hele check** via Chrome MCP `read_console_messages`. Alle echte errors loggen in `SESSIE58-AUTONOMOUS-LOG.md`.

**Output van Blok 1:** lijst van bevindingen per view (✅ werkt / ⚠️ werkt maar issue / ❌ kapot). Screenshots optioneel maar handig voor lange-termijn referentie.

##### BLOK 2 — Security audit [60-90 min]

Doel: voordat sessie 57's nieuwe Brand + Auto-mode flow productie raakt, scannen op de gebruikelijke web-app-issues.

1. **XSS in user-input velden** — alle plekken waar `innerHTML` met user-data wordt gevuld:
   - Brand-pack name (gebruikt in dropdown + selector)
   - Caption-preset name + tekst-content
   - Hook + CTA tekstvelden
   - Hashtag-set naam + tags
   - Watch-folder pad
   - Sticker label
   - Test: zet `<img src=x onerror=alert(1)>` in elk veld, sla op, render opnieuw → mag GEEN alert tonen
   - Fix gebruikt `escapeHtml()` — controleer dat ALLE user-input-injecties dat helper doorlopen
2. **Brand-pack JSON import sanitization** — test of import met `{"name":"<script>alert(1)</script>"}` wordt afgewezen (we regex-checken op `<script`, `<iframe`, `javascript:` — verifieer dat dat werkt)
3. **localStorage data-URL groei** — kijk hoeveel MB localStorage gebruikt na 5 logo-uploads. Cap moet 5-10MB blijven; bij overshoot oudere assets purgen of waarschuwing tonen.
4. **Tier-bypass check** — zet `STATE.tier='free'` maar probeer via console direct `OmniBrand.create('hack')` aan te roepen. De helper `packCap(tier)` moet de paywall enforcen in de UI; maar in code is `create()` zelf niet tier-gated. Beslissing: of `create()` ook tier-checken, of accepteren dat dat alleen UX is (vergt OK van Sjuul).
5. **Backend endpoints scan** — `grep` `app.py` voor recent toegevoegde endpoints (sessie 56-57). Check op:
   - `@require_auth` decorator op alle data-routes
   - Rate-limiting op write-routes (sessie 32 fix-pattern)
   - RLS-policy bestaan voor nieuwe tables in `supabase/migrations/` (zijn die er al voor brand_packs / auto_mode_configs? Of zit alles in localStorage v1?)
6. **CSP / inline scripts** — check of inline `<script>` blocks geen `eval()` of `Function()` gebruiken (snel `grep`)
7. **Brand-pack export** — bevestig dat data-URLs gestript worden (logo, watermark image, stickers) — anders kunnen exports >25MB gigantisch zijn
8. **Supabase keys in frontend** — `grep` op `service_role` of `SUPABASE_SERVICE_KEY` in static/ — mag niet voorkomen. Anon key is OK want public.
9. **Auth-token in URLs** — check dat geen auth-tokens in query-params worden gezet (alleen in headers of cookies)
10. **File-upload validation** — Brand Kit logo accepteert PNG/JPG/WebP/SVG. SVG kan XSS bevatten. Beslissing: of SVG strippen aan client, of accepteer met `dangerouslySetInnerHTML`-vermijding (SVG wordt nu via `<img src>` getoond, dus geen execute-context — OK).

**Output van Blok 2:** security-rapport in `SESSIE58-AUTONOMOUS-LOG.md` met severity-levels (🔴 critical / 🟡 medium / 🟢 low / ✅ no issue). Fixes voor 🔴 direct doorvoeren met code-edit + commit-instructie. 🟡 + 🟢 alleen documenteren voor Sjuul's review.

##### BLOK 3 — UI-quality check [60 min]

Diepere UX-pass op de 3 nieuwe fases:

1. **Brand-page interactie-pass:**
   - Tab-volgorde door alle form-velden (a11y) — alle inputs reachable met Tab?
   - Color-pickers responsive op kleine viewports (980px breakpoint)?
   - Cards padden mooi af op mobile (<700px viewport)?
   - Modal-editor sluit met Escape-toets?
   - Empty-states tonen helpful copy (geen "No data" maar "Save your first preset from the editor")?
   - Loading-states bij upload (logo, sticker)? Of toont 'ie freezed UI tijdens FileReader?
2. **Auto-mode interactie-pass:**
   - Pipeline-stappen ON/OFF visueel duidelijk (kleur + tekst)?
   - Quick-enable knoppen geven feedback (toast)?
   - Watch-folder modal sluit netjes?
   - Schedule-grid scrollt horizontaal op mobile?
   - Paywall-overlay (Free/Pro) — knop "Upgrade" leidt naar correcte upgrade-modal?
   - Status-pill kleur klopt met state (Off=grey, Running=green, Paused=grey, Locked=grey)?
3. **Cross-browser snel-check** — als computer-use beschikbaar: test ook in Safari (op de Mac). v2-CSS gebruikt veel `:has()`, `aspect-ratio`, `gap` — die werken in Safari ≥15.4, maar verifieer.
4. **Accessibility** — color-contrast op v2-cards (Brand Kit titel `var(--v2-text)` op `var(--v2-bg-elevated-1)`) — moet WCAG AA halen
5. **Dark-mode consistency** — alle nieuwe sections gebruiken v2-CSS-variabelen, geen hardcoded colors die in light-mode broken zijn (we hebben geen light-mode maar voor de toekomst)
6. **Empty-state per view bij verse install:** wis localStorage `omnidj.*` keys + brand_packs, reload — moet auto-seed werken zonder errors

**Output Blok 3:** UI-bevindingen in `SESSIE58-AUTONOMOUS-LOG.md` als ✅ / ⚠️ / ❌. Quick-wins direct fixen (≤30 min werk).

##### BLOK 4 — Rapport + aanbevelingen voor Sjuul [30 min]

1. `SESSIE58-AUTONOMOUS-LOG.md` aanmaken met:
   - Samenvatting per blok (Blok 1 / 2 / 3)
   - Alle bevindingen gesorteerd op severity
   - Lijst van fixes die Claude direct heeft doorgevoerd
   - Lijst van open items voor Sjuul's review
2. `HANDOVER.md` updaten met sessie 58 status (deze sessie wordt dan ARCHIVED, nieuwe START HIER voor sessie 59)
3. **NIET doen zonder Sjuul's OK:**
   - PyInstaller rebuild
   - Git commits/merges (alleen documenteren wat moet gebeuren)
   - Supabase migraties uitvoeren (alleen SQL-files schrijven)
   - Productie-toggles wijzigen

#### Toestemmingen die al doorgegeven zijn (sessie 57)

✅ Computer-use voor app management
✅ Bash terminal voor dev-server, builds, tests
✅ File-access op heel `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/`
✅ Supabase migration-files schrijven (geen `db push`)
✅ `pip install watchdog` in venv
✅ Git commits + branch werk

#### Toestemmingen NIET doorgegeven

❌ Stripe live-mode toggle
❌ Supabase `db push` of dashboard-mutaties
❌ DNS / Cloudflare wijzigingen
❌ Email versturen via SMTP
❌ `git push` naar remote
❌ App-Store / DMG distributie

#### Sessie 57 context (KORT — voor details lees `SESSIE57-AUTONOMOUS-LOG.md`)

Sjuul gaf akkoord op `PLAN-AUTO-MODE-2026-05-28.md`. Claude bouwde **autonoom** terwijl Sjuul sportte:

- **Fase A** — Brand-page herontwerp deel 1 (Brand Kit, Watermark, Caption-presets met modal-editor). Brand mapt nu naar eigen `#view-brand` ipv Settings-fallback. Profile blijft in Settings.
- **Fase B** — Brand-page deel 2 (Clip Templates + 4 built-ins, Hooks/CTAs, Caption-copy per platform, Hashtag-sets, Stickers + Lower-thirds + Intro/Outro, Export/Import als JSON)
- **Fase C** — Auto-mode (sidebar divider + entry, 6-staps pipeline, watch-folders lokaal + DBX/Drive UI-only, brand-defaults, publish-schedule, queue + runs, safety controls, paywall Free/Pro, Studio+ feature-flag voor publish)

Verificatie (jsdom):
- Fase A: 20/20 OK
- Fase B: 22/22 OK
- Fase C: 25/25 OK
- Regressie: 28/28 OK

Bestand: `dj-clip-cutter/static/index.html` 1.083.979 bytes (+133K vs backup). Backup: `static/index.html.pre-sessie57-faseA.bak` (950K).

**Live verificatie NIET gedaan in sessie 57** — sandbox-Flask kon niet bij host-Chrome. Dat is precies wat Blok 1 hierboven moet doen.

**Commit + rebuild NIET gedaan in sessie 57** — sandbox kon niet schrijven naar .git/objects + kan geen Mac-bundle bouwen. Sessie 58 documenteert wat Sjuul moet doen, voert dat niet uit.

---

## ⚡ ARCHIVED — sessie 57 follow-up (autonoom werk 2026-05-28)

### Wat Claude gedaan heeft in sessie 57 (autonoom terwijl Sjuul sportte)

Sjuul gaf akkoord op `PLAN-AUTO-MODE-2026-05-28.md` + akkoord op:
- Aparte feature-branch + per-fase merge naar main
- Toestemmingen 5, 6, 9 (Supabase migraties schrijven, pip install watchdog, git commits)
- Studio+ feature-flag in code reserveren (geen Stripe-product)
- Default watch-folder `~/Documents/Omni DJ/Watch`
- Hooks/CTAs onbeperkt op alle tiers
- Pipeline-run retention 30 dagen in localStorage v1

**Code-side klaar:**

- **Fase A** — Brand-page volledig herontwerp deel 1 (Brand Kit, Watermark, Caption-presets met modal-editor)
- **Fase B** — Brand-page deel 2 (Clip Templates + 4 built-ins, Hooks/CTAs onbeperkt, Caption-copy per platform met char-limits, Hashtag-sets, Stickers + Lower-thirds + Intro/Outro, Export/Import als JSON)
- **Fase C** — Auto-mode (sidebar divider + entry, 6-staps pipeline met per-stap ON/OFF toggles, watch-folders lokaal werkend + Dropbox/Drive UI-only, brand-defaults, publish-schedule, queue + recent runs, safety controls, paywall Free/Pro)

**Resultaat:** 70/70 jsdom-smoketest checks groen + 28/28 regressie groen. Bestand 1.083.979 bytes (+133K vs backup). Backup: `dj-clip-cutter/static/index.html.pre-sessie57-faseA.bak`.

**Profile-card:** is NIET verhuisd — staat nog steeds in Settings (sessie 30 plek). Wat is gewijzigd is dat Brand-tab nu zijn eigen `#view-brand` heeft (was Settings-fallback sinds sessie 55), waardoor Profile alleen in Settings zichtbaar is. Dat was Sjuul's bedoeling op het screenshot.

**Nog NIET gedaan (Sjuul moet zelf):**
1. Live visuele test op dev-server (15 min) — wordt sessie 58 Blok 1
2. Git commits (sandbox kon niet schrijven naar .git/objects)
3. PyInstaller rebuild (sandbox kan geen mac-bundle bouwen)
4. Fase D-E-F (pipeline backend, review-flow, Postiz) — staat in plan, niet code-side

**Lees `SESSIE57-AUTONOMOUS-LOG.md` voor:**
- Exacte verificatie-resultaten
- Bestand-changes log
- Open punten/bekende beperkingen
- Stap-voor-stap commando's voor live-test, commit, rebuild
- Tier-matrix per feature

---

## ⚡ ARCHIVED — sessie 57 briefing (na sessie 56 — autonome nacht)

**Project:** Omni DJ — DJ-set → vertical/landscape clip generator
**Eigenaar:** MONO LABS
**Domein:** `www.omnidj.com` (nog niet gekoppeld). `omnidj.com` vervalt volledig.
**Werkmap (code):** `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter/`
**Bundle:** `/Applications/Omni DJ.app` (oude sessie 53 versie — sessies 54+55+56 NIET in bundle)
**Dev-server:** `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ" && ./start.sh` → http://127.0.0.1:5555

### Wat Claude vannacht autonoom heeft gedaan

Sjuul gaf 4 groene lichten: rebuild OK, volledige Omni DJ rebrand OK, Social/Calendar/Insights met volledige functionaliteit, en "maak conservatieve keuze + log" bij twijfel. Claude heeft 4 van de oorspronkelijke 8 doelen volledig opgeleverd en 4 bewust niet gedaan met expliciete reden. Zie hieronder per onderdeel.

#### ✅ Wel afgerond — code-side klaar

1. **Sessie 56 Fase 5 — Social view** (`#view-social`)
   - 4 account-cards (TikTok, Instagram, YouTube, X) met platform-gradient iconen, mock followers/engagement-stats, "Connect"-knop disabled met "Postiz soon" badge.
   - Recent-posts feed (max 8 mock-posts) gegenereerd uit `STATE.history` met deterministic seed (stabiel tussen renders). Per post: platform-naam, datum, view-count, status-pill (Published/Scheduled/Failed).
   - Mock-banner bovenaan ("Preview — account-connecties komen via Postiz in een latere release").

2. **Sessie 56 Fase 5 — Content Calendar view** (`#view-calendar`)
   - Month-view 7×6 grid met dag-tegels, today-highlight, vorige/huidige/volgende-maand klikbaar.
   - Week-view toggle (6 tijd-rijen: 09/12/15/18/21/23).
   - Prev/Next/Today nav-knoppen.
   - "Schedule post"-button rechtsboven opent een modal.
   - Schedule-modal: clip-picker (4-koloms grid uit STATE.history), caption-textarea, platform-chips (TikTok/IG/YT/X), datetime-picker. Submit → persist in `localStorage.omnidj.calendar.v1`. Drafts overleven page-refresh. Posts verschijnen direct in calendar-grid als gekleurde events (per platform een border-kleur).
   - Auto-seed 5 mock-events als history aanwezig + calendar nog leeg.

3. **Sessie 56 Fase 5 — Insights view** (`#view-insights`)
   - 4 KPI-cards: Total views / Engagement rate / Clips published / Best clip. Met up/down delta vs previous period.
   - Line-chart "Views per day" via custom Canvas-rendering (geen Chart.js dependency — werkt ook in `.app`-bundle zonder externe CDN).
   - Top 5 clips tabel met rank/thumb/name/platform-badge/views.
   - Donut-chart "By platform" met legend (TikTok 48% / IG 32% / YT 14% / X 6%).
   - Range-switch 7d/30d/90d (re-renderen line-chart).

4. **Sessie 56 Analyse-progress-hookup** (taak uit sessie 55 prio 3)
   - `setProcUI(pct, eta, phase)` roept nu óók `window.analyseSetState('processing', {pct, step})` aan in v2-modus → progress-bar binnen Analyse update echt mee tijdens analyse.
   - `uploadFile()` herschreven van `fetch()` naar `XMLHttpRequest` met `xhr.upload.onprogress` → progress-bar update tijdens upload (was 0% blijven).
   - Beide niet-destructief: legacy-modus blijft 1-op-1.

#### ⛔ Bewust NIET gedaan — met expliciete reden

5. **Volledige Omni DJ rebrand** (Sjuul gaf groen licht, Claude koos conservatief)
   - PLAN-REBRAND-OMNI-DJ-2026-05-27.md beschrijft 7+ externe-service-handelingen (Supabase email-templates renamen, Cloudflare nameservers omzetten, Stripe products renamen, Apple notary-keychain rebinden, GitHub repo's renamen, Google Workspace App-Passwords) plus folder-renames die alle hardcoded paden breken.
   - Als ik tussen die stappen vastloop ben jij je hele werkende dev-omgeving + Stripe-test-mode kwijt. Te risicovol zonder Sjuul.
   - **Aparte sessie wanneer Sjuul wakker is + 2-3u blok beschikbaar.** Plan staat klaar.

6. **omnidj.com koppelen + Stripe live mode** (zelfde reden — vereist Cloudflare-DNS toegang + Stripe-toggle die ik niet alleen mag doen).

7. **PyInstaller rebuild** (sandbox kan niet)
   - Claude's sandbox heeft geen toegang tot Sjuul's host venv, PyInstaller, macOS-frameworks.
   - Rebuild is een 1-commando-stap voor Sjuul, zie "Wat Sjuul morgen moet doen" hieronder.

8. **Fase 5b multi-tenant Supabase data** (uit scope — vereist 3-4 weken dev volgens PLAN-CONTENT-CALENDAR §8 Fase 1)
   - Workspaces + workspace_members tabellen, RLS-policies, data-migratie. Niet één nacht.

### Wat Sjuul morgen moet doen (volgorde)

**Stap 1 — Visuele check op dev-server (10 min)**

Open Terminal en plak (één voor één):

osascript -e 'tell application "Omni DJ" to quit' 2>/dev/null

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"

./start.sh

Open dan in Chrome: http://127.0.0.1:5555

In browser:
- v2-flag aan (klik linksonder of console: `localStorage.setItem('omniDjRedesignV2','1')` + reload)
- Klik **Social** in sidebar → 4 account-cards + Recent-posts feed
- Klik **Calendar** → month-view, klik op een dag → schedule-modal opent → vul iets in → opslaan → event verschijnt in calendar-grid
- Refresh pagina → draft is er nog (localStorage)
- Klik **Insights** → KPI-cards + line-chart + top clips + donut-chart
- Klik op range-knop 7d/30d/90d → chart re-rendered
- Klik **Analyse** → drop een file → upload-progress bar moet echt naar 100% lopen (niet meer op 0% blijven)
- Klik **Library** + **Settings** → moeten nog steeds werken zoals voor sessie 56

**Stap 2 — PyInstaller rebuild (5-15 min)**

Stop dev-server (Ctrl+C in dezelfde terminal), dan:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"

source venv/bin/activate

mv "/Applications/Omni DJ.app" "/Applications/Omni DJ.PRE-SESSIE56.app"

./build_macos.sh dmg

mv "dist/Omni DJ.app" "/Applications/"

open "/Applications/Omni DJ.app"

Rollback bij issue:

rm -rf "/Applications/Omni DJ.app"

mv "/Applications/Omni DJ.PRE-SESSIE56.app" "/Applications/Omni DJ.app"

**Stap 3 — Code-rebrand Omni DJ (aparte sessie 57+ samen met Claude)**
- Plan staat klaar (PLAN-REBRAND-OMNI-DJ-2026-05-27.md)
- Reken op 4-6u sessie waar je beschikbaar bent voor Supabase/Cloudflare/Stripe acties

### Bestandsstatistieken

- `static/index.html`: 882.154 → 948.383 bytes (+66.229 sessie 56)
- 20.259 → 21.719 regels (+1.460)
- Backup: `static/index.html.pre-sessie56.bak` (887.446 bytes, vóór sessie 56 wijzigingen)
- Wijzigingen alleen in `static/index.html`. Geen backend-wijzigingen.
- Geen wijzigingen aan: `app.py`, `cutter.py`, `auth.py`, `analyzer.py`, `launcher.py`, `build_macos.sh`, `start.sh`.

### Verificatie status

| Check | Status |
|---|---|
| `html.parser` parse | OK 0 errors |
| `node --check` op JS-blok (533KB) | OK groen |
| Tag-balance vs backup | OK identiek (alleen verwachte SVG self-close delta) |
| Selector presence (9 nieuwe IDs) | OK alle 9 aanwezig |
| Renderers exposed op window | OK renderSocial/renderCalendar/renderInsights |
| NAV_MAP routes | OK social/calendar/insights → echte views |
| Backward-compat `redesign-v2` class | OK 775 occurrences, ongewijzigd |
| Backward-compat `omniDjRedesignV2` key | OK 3 occurrences, ongewijzigd |
| Runtime smoketest (jsdom) | OK 3 renderers slagen, modal open/close/save OK, localStorage write OK |
| Live verificatie via Chrome MCP | SKIPPED — vereist dev-server op host, zie limitatie hieronder |

**Over de live-verificatie:** Claude's sandbox draait Flask op `127.0.0.1:5556` in eigen omgeving, maar Chrome MCP zit op de host en kan daar niet bij. Statische + jsdom-runtime checks zijn sluitend genoeg voor de 3 nieuwe views. Bij Stap 1 hierboven doe je de echte live-test in 10 min.

### Bekende open punten (gold-state na sessie 56)

- **Brand-tab mapt nog naar Settings** in NAV_MAP — overgenomen uit sessie 55. Niet gewijzigd.

- **Analyse-progress-hookup is one-way** — server `setProcUI` → Analyse-state werkt nu. Maar als gebruiker mid-upload op andere tab klikt en terug komt, blijft de pct in geheugen (geen polling re-sync). Acceptabel voor v1.

- **Calendar drafts zijn lokaal** (localStorage) — niet gesynchroniseerd naar Supabase. Per design (PLAN-CONTENT-CALENDAR §4 Laag 2 vereist eerst multi-tenant tabel `scheduled_posts` + RLS). Drafts overleven page-refresh maar niet OS-reinstall of nieuwe machine.

- **Insights data is mock** — gegenereerd uit STATE.history met deterministic seed. Toont reële UI maar getallen zijn fictief tot Postiz publish-events terugkomen + analytics-API gebouwd is.

- **Social account-connect-knoppen zijn disabled** — duidelijk gemarkeerd met "Postiz soon" badge. Echte OAuth-flow komt in Fase 3 (3-4 wkn dev volgens PLAN-CONTENT-CALENDAR).

- **Bug 1 selectie-balk** uit sessie 53 — niet reproduceerbaar in lab, blijft open tot Sjuul exact reproduce-stappen heeft.

### Recente sessies — één-regelers (sessie 55 en eerder in detail hieronder)

- **Sessie 56** (vandaag, autonoom 's nachts) — Social/Calendar/Insights v2-shells met werkende frontend-state + Analyse-progress-hookup. Code-side klaar, bundle nog niet rebuilt. Rebrand bewust overgeslagen — te risicovol zonder Sjuul.
- **Sessie 55** — Smoketest Fase 5: 8 bugs gefixt + 3 polish-fixes. Live geverifieerd via Chrome MCP.
- **Sessie 54** — Redesign Fase 5: sidebar workspace+artist, Analyse view, Library view, Settings polish, Capabilities/Storage verborgen. Code-side klaar.
- **Sessie 53** — Rebrand-noot + 2× rebuild + 5 fixes. Captions in productie groen verifieerd.
- **Sessie 52** — E2E export-test groen via inline editor (sessies 50+51 keten bewezen).
- **Sessie 51** — Bug 1 (off-by-one) frontend-fix + 3 UI-fixes export-modal.
- **Sessie 50** — Caption-bake bug opgelost: `import re` ontbrak in cutter.py.

---

## STATUS NA SESSIE 56 — AUTONOMOUS NIGHT-RUN (2026-05-27)

> **Sjuul ging slapen en gaf Claude vier groene lichten: rebuild OK, full rebrand OK, full functionality Social/Calendar/Insights, conservatieve keuze + log bij twijfel.**
>
> **Claude leverde 4 van 8 doelen volledig, en 4 bewust niet — met log waarom. Onder de "skip"-bestanden: full rebrand, omni.com DNS, Stripe live mode, multi-tenant Supabase. Reden steeds: te veel onomkeerbare externe-service handelingen.**
>
> ### Aanpak
>
> Claude bouwde de 3 nieuwe views (Social / Calendar / Insights) als visuele shells met werkende frontend-state in plaats van placeholder-content. Mock-data komt uit `STATE.history` met deterministic seed zodat repeats stabiel zijn. Echte Postiz/analytics-koppeling staat gepland in latere fasen (zie PLAN-CONTENT-CALENDAR-2026-05-26.md). Plus: een kleine kwaliteitsverbetering — de Analyse-progress-bar update nu écht mee, was sinds sessie 54 op 0% blijven hangen.
>
> ### Bestand-wijzigingen
>
> 1. **CSS-blok** (~750 regels, +25 KB) vóór `/* /REDESIGN v2 — Fase 5 */` marker
> 2. **DOM** (~250 regels nieuwe markup) direct ná `#view-library` — 3 nieuwe `<main>` + 1 schedule-modal
> 3. **JS** (~600 regels) direct na `analyseSetState` definitie — 3 renderers, custom Canvas-charts, calendar-state-machine
> 4. **RENDERERS map** in router — social/calendar/insights toegevoegd
> 5. **NAV_MAP** sidebar-routes — placeholders vervangen door echte views
> 6. **Defensive STATE.history reads** in 4 plekken — robuust tegen lexical vs window-binding
> 7. **Analyse-progress-hookup** in `setProcUI()` — forward pct naar v2-card
> 8. **Upload-progress** in `uploadFile()` — switched van fetch() naar XHR met onprogress
>
> ### Verificatie
>
> Zie tabel bovenaan. Live verificatie via Chrome MCP **niet uitgevoerd** — sandbox-Flask draait op 127.0.0.1:5556 maar host-Chrome kan daar niet bij. jsdom-runtime smoketest dekt: alle 3 renderers callable + DOM gevuld + modal open/save/close + localStorage write. Sjuul doet 10-min live test op dev-server in Stap 1 hierboven.
>
> ### Bewust niet gedaan
>
> Zie hoofd-blok: rebrand (4-6u externe-service handelingen), omnidj.com koppelen (Cloudflare-DNS), Stripe live mode (productie-toggle), PyInstaller rebuild (sandbox kan niet), Fase 5b multi-tenant (3-4 wkn dev).
>
> ### Volgende sessie 57
>
> 1. Sjuul live-test (10 min) — Stap 1 hierboven
> 2. Sjuul rebuild (5-15 min) — Stap 2 hierboven
> 3. Volledige Omni DJ rebrand (4-6u sessie samen) — Stap 3
> 4. Daarna: omnidj.com koppelen via Cloudflare + Stripe live mode
> 5. Later: Postiz cloud-account + Fase 3 Social publishing-laag

---

## ⚡ ARCHIVED — sessie 56 briefing (na sessie 55 smoketest + 8 bugs gefixt)

**Project:** Omni DJ — DJ-set → vertical/landscape clip generator
**Eigenaar:** MONO LABS
**Domein:** `www.omnidj.com` (nog niet gekoppeld). `omnidj.com` vervalt volledig.
**Werkmap (code):** `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter/`
**Bundle:** `/Applications/Omni DJ.app` (oude versie, sessie 53 fixes erin — Fase 5 NIET in bundle)
**Dev-server:** `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ" && ./start.sh` → http://127.0.0.1:5555

### Status na sessie 55 — Fase 5 live geverifieerd + alle bugs gefixt

Volledige smoketest doorlopen via Chrome MCP + dev-server. **8 bugs gevonden en allemaal opgelost.**

#### Bugs gefixt deze sessie

| # | Bug | Locatie | Fix |
|---|---|---|---|
| 1 | Library + Analyse zichtbaar tegelijk (gestapeld onder elkaar) | CSS `.v2-only { display: block }` overruled `.view { display: none }` | `.v2-only.view` respecteert nu `.active`-toggle; non-view-elementen blijven `block` |
| 2 | Page-load opende dashboard ipv Analyse | `postLoginBoot()` deed `openJob(savedJobId)` of `switchView('upload')` | Toegevoegd: `if (v2On) switchView('analyse'); return;` vóór de auto-resume-logica |
| 3 | Library Projects toonde 0 ondanks 7 in history | shape mismatch: `clipCount` ipv `clips.length`, `date` ipv `created_at`, `thumb` is al full-path | `renderLibraryProjects` gebruikt nu correcte keys + accepteert `h.thumb` als path |
| 4 | Library Exports datums = 21/01/1970 | mtime is Unix-seconden, `formatWhen` interpreteerde als ms | `toMs()` helper detecteert s vs ms (>1e12 = ms, anders *1000) |
| 5 | Settings titels nog Playfair italic | CSS-selector `h1`+`.eyebrow`, maar Settings heeft `h2.scene-title`+`.scene-num` | Selectors aangepast naar beide vormen + `!important` |
| 6 | Workspace-input had witte bg + blauwe browser-default | Geen v2-input-styling voor `#view-settings input` | v2-input-styling toegevoegd (bg-elevated-2, accent-border on focus) |
| 7 | BPM in dash-set-meta in Clips-view | Sjuul wilde BPM weg in v2 | Wrap BPM/Key push in `if (!v2On)` |
| 8 | `STATE.history` shape gebruikt `clipCount`/`thumb`/`date` ipv generieke fields | Library + Analyse continue-card faalden | Beide functies accepteren nu meerdere shape-varianten |

#### Plus polish-fixes

- Brand kit / panel-h labels strakker (Inter 600, niet meer Fraunces)
- Save-knop in Profile = accent fill
- "Choose folder"-knop v2-ghost-stijl
- Watch-folder card v2

#### Live geverifieerd (alle groen via Chrome MCP)

- ✅ Sidebar: 2-chip workspace+artist, plan-badge FREE, dropdowns werken, locked-state opent upgrade-modal
- ✅ Nav-volgorde: **Analyse → Library → Brand → Social → Calendar → Insights → Settings**
- ✅ Analyse view: idle/uploading/processing sub-states + correct copy ("Analyse a DJ set" / "Drag & drop or select your DJ-set.")
- ✅ Dropzone strak (geen "up to 4 hours", geen [Choose file]-knop)
- ✅ 3 tiles: Watch folder + Dropbox (disabled) + Drive (disabled)
- ✅ Library Projects: 7 tiles met thumbnails, dates, clip-counts (4-koloms grid)
- ✅ Library Exports: 11 tiles met thumbnails, dates, aspect+set-name
- ✅ Klik project → Clips-view, sidebar highlight blijft "Library"
- ✅ Settings: 2-koloms, Workspace+Artists-card, paywall "🔒 + Add artist (Studio only)", Capabilities+Storage verborgen
- ✅ Brand/Social/Calendar/Insights placeholders (Brand mapt naar settings — acceptabel)
- ✅ Clips view: geen "Pick the keepers" hero, geen BPM in meta
- ✅ Flag UIT: oude UI 100% intact (v2-shell display:none, oude sidebar terug, "Pick the keepers" terug)
- ✅ Page-load in v2 → Analyse landing (geen auto-resume in project)
- ✅ Geen JS console errors
- ✅ Geen HTML parse errors
- ✅ Node syntax check JS-blok groen

#### Bestandsstatistieken

- `static/index.html`: 817.654 → 882.154 bytes (+64.500 sessie 54+55)
- Backup: `static/index.html.pre-redesign-fase5.bak` (817.654 bytes)
- Geen wijzigingen aan: `app.py`, `cutter.py`, `auth.py`, `analyzer.py`

### Volgende sessie 56 — prio's

1. **🔵 Visuele finale check** (5 min, Sjuul): hard refresh in Chrome (cmd+shift+R), doorklikken: Analyse → Library → klik project → Clips → terug Library → Settings → drop een file om upload-state te zien. Als alles soepel = klaar voor rebuild.
2. **🟢 PyInstaller rebuild** → `./build_macos.sh dmg` om Fase 5 in productie-`.app` te krijgen. Volg INSTALLER-RUNBOOK.md.
3. **🟢 Analyse-view progress hookup** — `analyseSetState()` helper staat klaar maar bestaande upload/processing-code roept 'm niet aan. Voor échte progress-doorvoer moet de bestaande progress-handler in app.py/socketio worden hergebruikt om `analyseSetState('processing', {pct, step})` aan te roepen. Werkt nu basaal maar progress-bar blijft op 0%.
4. **🟢 Code-rebrand "Omni DJ" → "Omni DJ"** (~4-6u aparte sessie). Sweep door static/index.html, launcher.py, app.py, auth.py, build_macos.sh, alle README's. App-icon, bundle-identifier (`com.monolabs.omnidj` → `com.monolabs.omnidj`?), info_plist `CFBundleName`. Folder rename (`dj-clip-cutter/` → ?) is hoge-risico — apart plannen.
5. **🟢 omnidj.com koppelen** via Cloudflare. Nieuwe Cloudflare Pages-project + DNS-records.
6. **🟢 Stripe live mode** — pas na omnidj.com live. Runbook STRIPE-DNS-RUNBOOK.md updaten.
7. **🟢 Fase 5b multi-tenant data** — workspace_id + artist_id in Supabase RLS (UI staat al klaar, alleen data-laag mist)

### Bekende open punten (geen blockers)

⚠️ **Brand-tab mapt naar Settings** in NAV_MAP. Acceptabel maar Sjuul gaat verwarrend vinden. Voor latere sessie: aparte `#view-style` route maken of NAV_MAP aanpassen.

⚠️ **Brand-tab + Settings beide tonen Workspace-card** — Workspace-card is in #view-settings DOM, dus klikken op Brand toont 'm ook. Niet kritisch.

⚠️ **`exportSelected` zeldzame zijroute** — comment regel 10351 stale, was nog niet gefixt.

⚠️ **Bug 1 selectie-balk** uit sessie 53 — niet reproduceerbaar in lab, blijft open tot Sjuul exact reproduce-stappen heeft.

### Active email-aliases

- `omnidj@monohq-labs.com` — support, algemene vragen
- `sjuul@monohq-labs.com` — Sjuul's eigen account, whitelist/testing

### Recente sessies — één-regelers (alles boven sessie 55 staat in detail in status-blokken hieronder)

- **Sessie 55** (vandaag) — Smoketest Fase 5: 8 bugs gefixt + 3 polish-fixes. Live geverifieerd via Chrome MCP.
- **Sessie 54** — Redesign Fase 5: sidebar workspace+artist, Analyse view, Library view, Settings polish, Capabilities/Storage verborgen. Code-side klaar.
- **Sessie 53** — Rebrand-noot + 2× rebuild + 5 fixes. Captions in productie groen verifieerd.
- **Sessie 52** — E2E export-test groen via inline editor (sessies 50+51 keten bewezen).
- **Sessie 51** — Bug 1 (off-by-one) frontend-fix + 3 UI-fixes export-modal.
- **Sessie 50** — Caption-bake bug opgelost: `import re` ontbrak in cutter.py.

---

## STATUS NA SESSIE 55 — SMOKETEST + 8 BUGS GEFIXT (2026-05-27)

> **Volledige smoketest van Fase 5 via Chrome MCP + dev-server. 8 bugs gevonden en allemaal opgelost. Sjuul kan nu productie-rebuild doen.**
>
> ### Aanpak
>
> Sjuul vroeg om volledige smoketest om errors eruit te halen vóór hij zelf opnieuw doorliep. Strategie: dev-server starten, alle views in v2-modus + legacy doorlopen, console errors monitoren, bevindingen direct fixen, daarna re-test.
>
> Dev-server start vereiste eerst `osascript -e 'tell application "Omni DJ" to quit'` + `kill -9 <PID>` voor het oude .app-Python-proces dat poort 5555 vasthield (bekend PyInstaller-issue, ook sessie 50).
>
> ### Bug 1 — Library + Analyse stack-bug (CSS-conflict)
>
> **Locatie:** `static/index.html` ~regel 6237, `.v2-only { display: block }`
>
> **Probleem:** Mijn regel forceerde `display: block` voor alle `.v2-only` elementen, óók wanneer de basis-CSS `.view { display: none }` hen zou moeten verbergen. Resultaat: `#view-library` (`.view.v2-only`) bleef altijd zichtbaar als `block` en stapelde onder `#view-analyse` als die ook actief was.
>
> **Fix:**
> ```css
> .v2-only { display: none; }
> body.redesign-v2 .v2-only.view { display: none; }
> body.redesign-v2 .v2-only.view.active { display: block; }
> body.redesign-v2 .v2-only:not(.view) { display: block; }
> ```
>
> ### Bug 2 — Page-load opende dashboard ipv Analyse
>
> **Locatie:** `static/index.html` `postLoginBoot()` regel ~19418
>
> **Probleem:** Na page-refresh roept `postLoginBoot()` `openJob(savedJobId)` aan als er een gepersisteerde job is. In v2 mismatch: sidebar highlightte "Analyse" maar content was Dashboard.
>
> **Fix:**
> ```js
> const v2On = (function(){ try { return localStorage.getItem('omniDjRedesignV2') === '1'; } catch(_){ return false; }})();
> if (v2On) { switchView('analyse'); return; }
> // ...legacy auto-resume flow blijft hieronder
> ```
>
> ### Bug 3 — Library Projects toonde 0 ondanks 7 in history
>
> **Locatie:** `static/index.html` `renderLibraryProjects()` regel ~9061
>
> **Probleem:** Ik nam aan dat history-items shape `{clips:[], created_at, thumbnail, original_filename}` hadden. Echte shape uit `/api/history`:
> ```json
> {"id":"e63f06a6","filename":"Lisa Korver x Ho_r Berlin.mp4","clipCount":30,"date":"2026-05-23","thumb":"/api/thumbnail/e63f06a6/thumb_clip01.jpg","user_id":"d86a3a54..."}
> ```
>
> **Fix:** `renderLibraryProjects` accepteert nu beide shapes:
> ```js
> var name = (h.filename || h.original_filename || 'Untitled').replace(/\.[^.]+$/, '');
> var clipCount = h.clipCount || (h.clips && h.clips.length) || h.clip_count || 0;
> var dateVal = h.date || h.created_at || h.mtime || null;
> // thumb is al full-path
> if (h.thumb && h.thumb.startsWith('/')) thumbSrc = withAuth(h.thumb);
> else if (h.thumbnail) thumbSrc = withAuth('/api/thumbnail/' + h.id + '/' + ...);
> ```
>
> ### Bug 4 — Library Exports datums = 21/01/1970
>
> **Locatie:** `renderLibraryExports()` regel ~9133
>
> **Probleem:** `ex.mtime = 1779882578.832528` is Unix-seconden (float). `new Date(1779882578)` interpreteert als ms = ~21 dagen na epoch = 21/01/1970.
>
> **Fix:** detecteer s vs ms:
> ```js
> function toMs(v){
>   if (v == null) return 0;
>   if (typeof v === 'number') return (v > 1e12) ? v : v * 1000;
>   var n = +new Date(v); return isNaN(n) ? 0 : n;
> }
> ```
>
> ### Bug 5 — Settings titels nog Playfair italic
>
> **Locatie:** CSS regel ~5797
>
> **Probleem:** Settings gebruikt `<h2 class="scene-title">` (niet `h1`) en `<div class="scene-num">` (niet `.eyebrow`). Mijn CSS-selectors matchten niet.
>
> **Fix:** selectors uitgebreid + `!important`:
> ```css
> body.redesign-v2 #view-settings .scene-header .scene-num,
> body.redesign-v2 #view-settings .scene-header .eyebrow { display: none !important; }
> body.redesign-v2 #view-settings .scene-header h1,
> body.redesign-v2 #view-settings .scene-header h2.scene-title,
> body.redesign-v2 #view-settings .cap-left h2 {
>   font-family: var(--v2-font-sans) !important;
>   font-style: normal !important;
> }
> ```
>
> ### Bug 6 — Workspace-input browser-default
>
> **Fix:** v2-input-styling toegevoegd voor `#view-settings input[type="text"|"email"]` met bg-elevated-2, border-subtle, accent-focus.
>
> ### Bug 7 — BPM in dash-set-meta in v2
>
> **Locatie:** `renderDashboard()` regel ~10049
>
> **Fix:** wrap BPM/Key in `if (!v2On)` check.
>
> ### Bug 8 — STATE.history shape-mismatch (zelfde als #3, andere call-site)
>
> **Fix:** `renderAnalyse()` continue-card accepteert nu ook nieuwe shape.
>
> ### Files gewijzigd deze sessie
>
> - `dj-clip-cutter/static/index.html`: 873.503 → 882.154 bytes (+8.651 sessie 55 bugfixes)
> - Geen backend-wijzigingen
>
> ### Sjuul moet doen
>
> 1. Hard refresh in Chrome (cmd+shift+R), v2 actief, doorklikken alle views
> 2. Drop een file in Analyse om upload-state te zien
> 3. Klik op project in Library → Clips-view → terug
> 4. Bevestig dat alles soepel werkt
> 5. Daarna: `./build_macos.sh dmg` voor productie-`.app`
>
> ### Volgende sessie
>
> 1. Sjuul's visuele finale check
> 2. PyInstaller rebuild
> 3. `analyseSetState()` progress-hookup vanuit upload/processing code
> 4. Code-rebrand Omni DJ → Omni DJ
> 5. omnidj.com koppelen
> 6. Stripe live mode
> 7. Fase 5b multi-tenant data (Supabase RLS)

---

### Status na sessie 54 — Fase 5 code-side klaar, bundle NIET ge-rebuild

Sjuul heeft akkoord gegeven op PLAN-REDESIGN-FASE5-2026-05-27.md v3. Alle 5 sub-fases doorlopen:

- ✅ **5.0 Discovery + backup** — `static/index.html.pre-redesign-fase5.bak` (817.654 bytes)
- ✅ **5.1 Sidebar rebuild** — 2-chip workspace+artist Supabase-stijl + NAV_MAP aangepast: `analyse` + `library` zijn nu top-level entries, Clips weg uit sidebar (alleen bereikbaar via project-klik). Plan-badges FREE/PRO/STUDIO. Workspace + Artist dropdowns met locked-states voor FREE/PRO.
- ✅ **5.2 CSS-restyles + content-strip** — Settings 2-koloms voorbereid, Workspace+Artists-card toegevoegd aan Settings (max 3 artists Studio, paywall FREE/PRO). Capabilities-sectie en Storage & large files-sectie **verborgen in v2** (wrap in `.v2-hide-in-v2`, DOM blijft voor backend-detection). "Pick the keepers" hero + eyebrow CSS-verborgen in v2-dashboard. Brand Stack + Publish display-titels v2.
- ✅ **5.3 Analyse view rebuild** — Nieuwe `#view-analyse` met copy "Analyse a DJ set" / "Drag & drop or select your DJ-set." 3 sub-states (idle / uploading / processing) via class-toggle. Dropzone strak (geen [Choose file]-knop, geen "up to 4 hours"). 3 intake-tiles (Watch / Dropbox / Drive — laatste 2 disabled). `switchView('home'|'upload'|'processing')` redirect in v2 naar `analyse` met juiste sub-state.
- ✅ **5.4 Library view NIEUW** — `#view-library` met Projects/Exports tabs (segmented control), 4-koloms grid. Projects-tab gebruikt `STATE.history`. Exports-tab fetcht `/api/exports`. Tile-klik op project → `openJob()` → switchView('dashboard') = Clips-view van dat project.
- ✅ **5.5 Statische verificatie groen** — `html.parser` 0 errors, `node --check` groen, tag-balance check 0 mismatches (alleen `<input>`-delta verwacht want self-closing), alle nieuwe selectors aanwezig, "Omni DJ" = 0 matches.

**Code-statistieken:**
- `static/index.html`: 817.654 → 875.442 bytes (+57.788)
- 19.834 regels (was 18.429)
- Backup: `static/index.html.pre-redesign-fase5.bak`
- Geen wijzigingen aan app.py, cutter.py, auth.py, analyzer.py

### Bekende open punten

⚠️ **Live verificatie NIET gedaan.** Chrome MCP verbond met `http://127.0.0.1:5555` maar die port draaide de oude `/Applications/Omni DJ.app`-bundle (815.821 bytes, vóór sessie 54). De nieuwe code zit alleen in de dev-server-folder, niet in de bundle.

⚠️ **"Omni DJ"-strings vervangen door "Omni DJ"** in 2 onboarding-wizard secties (regels ~6451 + ~6476). Bewuste sweep: jouw verzoek "geen Omni DJ meer ivm rebrand". Beperkt tot UI-strings die de user ziet; codebase-rebrand `Omni DJ` → `Omni DJ` blijft voor aparte sessie.

⚠️ **Sub-state polling Analyse-view** — `window.analyseSetState()` helper-functie staat klaar, maar de bestaande upload/processing-code roept 'm nog niet aan. Voor nu: in v2 redirect `switchView('upload')` direct naar `analyse`, en `switchView('processing')` zet `is-processing` class. Voor échte progress-doorvoer moet de bestaande progress-handler in `app.py`/socketio worden hergebruikt om `analyseSetState('processing', {pct, step})` aan te roepen. Werkt nu basaal maar progress-bar blijft op 0%.

### Volgende sessie — prio's

1. **🔴 LIVE-TEST CRUCIAAL** (Sjuul, 10 min): stop `/Applications/Omni DJ.app`, start dev-server via `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter" && ./start.sh`. Open `http://127.0.0.1:5555` in Chrome. Zet v2 aan (klik v2-toggle linksonder of `localStorage.setItem('omniDjRedesignV2','1')`). Verifieer:
   - Sidebar: 2-chip workspace+artist stack bovenaan (MONO LABS FREE + Artist name)
   - Sidebar nav: **Analyse → Library → Brand → Social → Calendar → Insights → Settings** (geen "Clips"-entry!)
   - Klik Analyse → drop-card + 3 tiles (Watch/Dropbox/Drive) + Continue editing (als history aanwezig)
   - Klik Library → Projects-tab tiles in 4-koloms grid. Klik project → Clips-view van die set
   - Klik Library → Exports-tab → exports tiles
   - Klik workspace-chip → dropdown opent met MONO LABS + Manage workspace + Upgrade plan
   - Klik artist-chip → dropdown met Artist (default actief) + locked "+ Second artist" + "Add more with Studio"
   - Klik locked artist → upgrade-modal opent
   - Klik Settings → 2-koloms layout, **Capabilities + Storage & large files NIET zichtbaar**, Workspace+Artists-card wel zichtbaar met "+ Add artist" lock-button
   - Klik "+ Add artist" → upgrade-modal opent (FREE)
   - Klik Clips-view (via project-klik in Library) → geen "Pick the keepers" hero meer
2. **🟢 PyInstaller rebuild** als alles groen is → `./build_macos.sh dmg` om Fase 5 in productie-`.app` te krijgen
3. **🟢 Analyse-view progress hookup** — `analyseSetState()` aanroepen vanuit bestaande upload/processing-handlers zodat de progress-bar binnen Analyse echt updatet (nu nog op 0%)
4. **🟢 Bug 1 (selectie-balk)** — als Sjuul reproduce-stappen heeft
5. **🟢 Code-rebrand Omni DJ → Omni DJ** (~4-6u, aparte sessie)
6. **🟢 omnidj.com koppelen + Stripe live mode** (Fase 3-4 launch)

---

## STATUS NA SESSIE 54 — REDESIGN FASE 5 (2026-05-27)

> **Sidebar workspace+artist switcher, Analyse-view (vervangt home+upload+processing), Library-view (vervangt Clips als top-level), Capabilities+Storage uit Settings, multi-artist Studio-plan paywall (max 3). CSS+DOM+JS-only, geen backend-wijzigingen.**
>
> ### Sjuul's wijzigingsverzoeken (allemaal verwerkt)
>
> 1. Sidebar 2-chip Supabase-stijl: workspace + artist gestapeld
> 2. Library vervangt Clips top-level; Clips alleen via project-klik
> 3. Multi-artist = Studio-plan feature, **max 3 artists**, Stripe price-ID hergebruiken
> 4. Default artist-naam = `Artist name` (placeholder), uit onboarding-`artist_name` veld
> 5. Analyse-page copy: `Analyse a DJ set` + `Drag & drop or select your DJ-set.`
> 6. Dropzone strak: geen "— up to 4 hours", geen [Choose file]-knop, geen "Or use:"-label, geen duplicate "Choose file / Local picker"-tile
> 7. BPM-meter / "144 BPM" weg uit headers (CSS-restyle dash-set-meta)
> 8. Capabilities-sectie en Storage & large files-sectie verborgen in v2-Settings (DOM blijft staan)
> 9. Artist-dropdown header: `Artists` (kort)
> 10. Library-tile-density: **4 per rij** desktop-default
>
> ### Files gewijzigd deze sessie
>
> - `dj-clip-cutter/static/index.html`: +57.788 bytes (875.442 totaal). +~1.400 regels CSS (Fase 5 blok ~5634-6000), +~250 regels nieuwe DOM (Analyse + Library views), +~400 regels JS (Workspace+Artist dropdowns + renderAnalyse + renderLibrary + analyseSetState + v2RenderArtistsList).
> - `PLAN-REDESIGN-FASE5-2026-05-27.md`: nieuw plan v3 met alle 9 wijzigingen.
> - `HANDOVER.md`: dit blok.
> - Backup: `static/index.html.pre-redesign-fase5.bak` (817.654 bytes).
>
> ### Geen wijzigingen aan
>
> `app.py`, `cutter.py`, `analyzer.py`, `auth.py`, `start.sh`, `build_macos.sh`.
>
> ### Verificatie statisch (allemaal groen)
>
> - ✅ `html.parser`: 0 parse-errors
> - ✅ `node --check` op JS-blok (490 KB): groen
> - ✅ Tag-balance delta vs backup: 0 mismatches (alleen `<input>` self-closing delta)
> - ✅ Alle nieuwe selectors aanwezig (1× #view-analyse, 1× #view-library, 1× .v2-ws-stack, 1× #v2WsChip, 1× #v2ArtistChip, 1× data-v2nav="analyse", 1× data-v2nav="library", 1× #settings-workspace)
> - ✅ 0 matches voor "Omni DJ" (2 onboarding-strings vervangen door "Omni DJ")
> - ✅ "Pick the keepers" hero blijft in legacy-DOM maar CSS-verborgen in v2-dashboard
>
> ### Verificatie live — NIET DOORGELOPEN
>
> Chrome MCP connectie met `http://127.0.0.1:5555` haalde 815.821 bytes binnen — dat is de oude `/Applications/Omni DJ.app`-bundle, niet onze dev-server. Live-test vereist dat Sjuul de bundle stopt en `./start.sh` in de project-folder draait.
>
> ### Wat Sjuul nu moet doen
>
> ```
> # 1. Stop de oude bundle
> osascript -e 'tell application "Omni DJ" to quit'
> # of: pkill -f "Omni DJ.app"
>
> # 2. Start dev-server
> cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"
> ./start.sh
>
> # 3. Open in Chrome
> open "http://127.0.0.1:5555"
> ```
>
> Daarna in browser:
> - Console: `localStorage.setItem('omniDjRedesignV2','1')` + reload
> - Verifieer de checklist hierboven onder "🔴 LIVE-TEST CRUCIAAL"
>
> ### Bewust uit scope sessie 54
>
> - Analyse-view progress-hookup: `analyseSetState()` helper staat klaar maar bestaande upload/processing-code roept 'm niet aan
> - PyInstaller rebuild (Sjuul doet handmatig na groene live-test)
> - Multi-tenant Supabase-werk (Fase 5b — workspace_id + artist_id RLS)
> - Per-artist Brand Stack data
> - Code-rebrand `Omni DJ` → `Omni DJ` strings overal (apart sessie)
> - reset-password.html standalone polish
>
> ### Volgende sessie
>
> 1. Sjuul live-test (zie checklist hierboven)
> 2. Eventuele restbugs fixen
> 3. PyInstaller rebuild → bundle in /Applications
> 4. Optioneel: Analyse-view progress-hookup
> 5. Daarna: code-rebrand of Fase 5b multi-tenant

---

## ⚡ START HIER — sessie 54 briefing (2026-05-28+, NU AFGEROND)

**Project:** Omni DJ (rebrand sessie 53, was Omni DJ) — DJ-set → vertical/landscape clip generator
**Eigenaar:** MONO LABS (de tools-divisie van Sjuul's bedrijf MONO)
**Domein:** `www.omnidj.com` (nog niet gekoppeld). `omnidj.com` vervalt volledig.
**Werkmap (code):** `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter/`
**Bundle:** `/Applications/Omni DJ.app` (intern nog "Omni DJ" genaamd — code-rebrand staat los gepland)
**App starten:** `open "/Applications/Omni DJ.app"` (poort 5555). Of dev-server via `./start.sh`.

### Status na sessie 53 — alles GROEN voor productie-bundle

✅ Captions worden ge-baked in MP4 (sessies 50+51 fixes in bundle, E2E groen in productie via "SESSIE 53 TEST"-tekst test)
✅ Single-clip-rename werkt voor zowel inline editor als 'Export selected' route (sessie 53 fix 4)
✅ Multi-clip & multi-ratio export pipeline werkt
✅ Brand-kit, watermark, logo, fonts, color wheels (sessies 41-48)
✅ v2-redesign volledig live: shell + dashboard + editor + 5 modals
✅ Auth + Supabase + Stripe (test mode) + rate limiting + RBAC + audit log
✅ Bug 4 (`.duration` stretch in v2) opgelost — timestamp-pill staat correct rechtsonder
✅ Eerste 8 thumbnails laden direct (`loading=eager`) — geen wazige first paint meer
✅ Animation-default nieuwe text-layer = "None" ipv "Fade in"
✅ Captions-info-tekst onder Export-modal toggle als geen overlays op selectie zitten

### Bekende open punten (geen blockers)

⚠️ **Bug 1** — Selectie-balk leek bij 2 clips niet zichtbaar in Sjuul's screenshot, maar NIET reproduceerbaar in Chrome MCP-lab. Mogelijk transition-race (`.22s ease-out` slide-in). Pas oppakken als Sjuul exact kan reproduceren met stappen.
⚠️ **Rebrand code-side** — `static/index.html` + `launcher.py` + `app.py` + `auth.py` + `build_macos.sh` + README's bevatten nog "Omni DJ"-strings. App-icon ongewijzigd. Map-namen ongewijzigd. ~4-6u dev voor volledige sweep (zie sessie 54 prio's).
⚠️ **`exportSelected` zeldzame zijroute** — STATE.clips lookup match nu correct (sessie 53 fix 4), maar comment op regel 10351 zegt nog "1-based" — moet "0-based" worden (sessie 52 mini-bevinding 1).
⚠️ **Multi-clip + multi-ratio E2E in productie** niet getest. Single-clip-route is bewezen, andere routes verwacht groen maar niet sluitend.

### Volgende sessie — prio's in volgorde

1. **🔵 Visuele sanity check** (5 min, Sjuul) — alle 5 sessie-53 fixes verifiëren in productie-`.app`:
   - Dashboard: eerste rij thumbnails direct geladen (niet wazig)
   - Dashboard: timestamp-pill rechtsonder in thumb (klein, ~10px), niet stretching
   - Export selected (1 clip) → rename-veld prefilled met `Drop_N`
   - Editor → Text-drawer → "+ Add text" → Animation dropdown = "None"
   - Selecteer clip zonder caption → Export → info-tekst "Geen captions aanwezig op deze clips" onder toggle
2. ✅ **Code-rebrand Clip Live → Omni DJ** — UITGEVOERD sessie 63 (2026-05-30): string-sweep door static/index.html, launcher.py, app.py, auth.py, build_macos.sh, docs. Bundle-identifier `com.sjuulstudios.cliplive` → `com.monolabs.omnidj`, env-vars `CLIP_LIVE_*` → `OMNI_DJ_*`, localStorage `clipLive.*` → `omniDj.*`, spec hernoemd. App-icon nog ongewijzigd. Folder-rename al gedaan sessie 59.
3. **🟢 omnidj.com koppelen** via Cloudflare (was Fase 3 voor omnidj.com). Nieuwe Cloudflare Pages-project + DNS-records. Oude `djclips-nl-by-mono-labs` Pages-project mag verwijderd; GitHub-repo `sjuulstudios/djclips.nl-by-MONO-LABS` kan archive.
4. **🟢 Stripe live mode** — pas na omnidj.com live. Runbook STRIPE-DNS-RUNBOOK.md moet inhoudelijk worden geupdate.
5. **🟢 Multi-clip E2E in productie verifiëren** — 2+ clips selecteren waar beide caption-overlays op zitten, exporteren met multi-ratio (9:16 + 16:9), check of alle MP4's captions bevatten.
6. **🟢 Fase 5 Content Calendar + Multi-artist** (zie `PLAN-CONTENT-CALENDAR-2026-05-26.md` v1.1) — 5a multi-tenant fundament, 5b calendar UI, 5c Postiz publishing, etc. 13-15 weken dev verspreid over fases.
7. **Optioneel** — Sessie 52 mini-bevinding 1 (comment regel 10351 stale 1-based → 0-based), sessie 40 hardening (`admin.sign_out(scope='others')`), SMTP-provider als eigen email nodig.

### Rebrand-noot

**Product heet voortaan Omni DJ.** Eigenaar = **MONO LABS** (tools-divisie). Naar buiten toe alleen Omni DJ + MONO LABS. Intern (codebase + map-namen) nog "Omni DJ" totdat sessie 54+ de code-rebrand doet.

**Active email-aliases:**
- `omnidj@monohq-labs.com` — support, algemene vragen
- `sjuul@monohq-labs.com` — Sjuul's eigen account, whitelist/testing

Memory: `project_omni_dj_rebrand.md` heeft de volledige rebrand-info.

### Recente sessies — één-regelers (alles boven sessie 53 staat in detail in status-blokken hieronder)

- **Sessie 53** (vandaag) — Rebrand-noot + 2× rebuild + 5 fixes. Captions in productie groen verifieerd.
- **Sessie 52** — E2E export-test groen via inline editor (sessies 50+51 keten bewezen).
- **Sessie 51** — Bug 1 (off-by-one) frontend-fix + 3 UI-fixes export-modal.
- **Sessie 50** — Caption-bake bug opgelost: `import re` ontbrak in cutter.py.
- **Sessie 49** — Rebuild groen sessies 41-48 + z-index fix aspect-modal + caption-bake bug geconfirmeerd.
- **Sessie 48** — Redesign Fase 4 modals (auth/wizard/forgot/upgrade/aspect/export).
- **Sessie 47** — Redesign Fase 3 editor/timeline.
- **Sessie 46** — Redesign Fase 2 dashboard/clips-grid.
- **Sessie 45** — Redesign Fase 1 shell (sidebar + workspace-switcher).
- **Sessies 44, 43a+b** — Selectie-balk + 7 export-pipeline onderdelen.

---

## STATUS NA SESSIE 53 — REBRAND NAAR OMNI DJ + REBUILD #1 + BUG-ONDERZOEK + FIXES + REBUILD #2 (2026-05-27)

> **Product hernoemd naar Omni DJ. Documentatie + memory bijgewerkt.
> Rebuild #1 (sessies 50+51 fixes) groen. Captions-export E2E geverifieerd
> in productie-`.app`. Smoketests deden 4 bugs aan het licht — 4
> onderzocht, 1 echte CSS-bug + 1 img-loading-tweak + 1 rename-bug + 1
> animation-default + 1 captions-UX. Rebuild #2 met alle 5 fixes
> geïnstalleerd in /Applications.**
>
> ### Sessie-flow (chronologisch)
>
> 1. **Memory + HANDOVER** — Omni DJ rebrand-info vastgelegd
>    (`project_omni_dj_rebrand.md`), HANDOVER hoofd-blok aangepast
> 2. **Rebuild #1** — `./build_macos.sh dmg` op Sjuul's Mac. Bundle in
>    `/Applications` geüpdatet (`Omni DJ.PRE-SESSIE53.app` rollback bewaard).
>    Sessies 50 + 51 fixes nu in productie.
> 3. **Captions E2E test productie** — Housy Good vibes set 30min (487MB)
>    geüpload via .app, geanalyseerd → 23 clips. Caption "SESSIE 53 TEST"
>    toegevoegd op clip 3 via full-page editor → text-drawer. Export 9:16
>    + captions ON → `Drop_3.mp4` (8.9MB) bevat de caption-tekst in de
>    pixels (visueel geverifieerd via QuickTime preview). **Sluitend bewijs
>    sessies 50+51 werken in productie.**
> 4. **Smoketests sessies 43 + 44** — 4 issues gerapporteerd door Sjuul:
>    - Selectie-balk bij 2 clips niet zichtbaar (1 of 3 wel)
>    - Multi-clip-export geen captions ondanks toggle aan
>    - Geen export-selected-overzicht in modal
>    - Rare blurred-overlays met timestamps op clip-cards
> 5. **Bug-onderzoek via Chrome MCP + osascript** (taak 8)
> 6. **Fixes doorgevoerd** (taken 6, 7, 9, 10, 11)
> 7. **Rebuild #2** met fixes → in /Applications
>
> ### Bug-onderzoek bevindingen
>
> **Bug 1 — Selectie-balk bij 2 clips niet zichtbaar:**
> ⚠️ **niet reproduceerbaar in lab**. Via Chrome MCP getest met
> `toggleClipSelect(0)` → `(1)` → `(2)` op dezelfde set (PID 11409,
> Housy 23 clips): bij 1, 2 én 3 selecties krijgt
> `#selection-preview-bar` `.on` class + `transform: translateY(0)` +
> correct aantal tiles. Mogelijke verklaring van wat Sjuul zag:
> race-condition tijdens de `.22s` CSS-transition (screenshot gemaakt
> tijdens slide-in animatie), of een `clearSelection`-call tussendoor.
> Géén code-fix gedaan zonder reproduce-stappen.
>
> **Bug 2 — Captions in multi-clip-export ontbreken:**
> ✅ **geen bug, gewoon geen content.** API-call op `/api/clip-overlays/116f7d0a`
> toonde dat alleen clip **3** een text-layer had (de manuele "SESSIE 53
> TEST"). Clips 1 en 2 hadden geen overlays. Bij export wordt er dus
> niks gebakt voor 1 en 2 — terecht. Sjuul verwachtte captions omdat de
> toggle aanstond, maar er waren simpelweg geen captions aanwezig.
> **UX-fix doorgevoerd** (fix 5 hieronder) om dit te voorkomen.
>
> **Bug 3 — Geen export-selected-overzicht in modal:**
> ✅ **geen bug, design-keuze.** Modal toont alleen "Render 2 clips" als
> korte beschrijving. Geen lijst van wélke clips. Feature-uitbreiding voor
> later, niet kritisch.
>
> **Bug 4 — Blurred timestamp-overlays op clip-cards:**
> 🔴 **echte CSS-bug + img-loading-vertraging gecombineerd.**
> - **CSS root cause (static/index.html regel 4053-4064):**
>   `body.redesign-v2 .clip-grid .clip .ph .duration` zette
>   `right: 10px; bottom: 10px` maar liet de legacy `top: 10px; left: 10px`
>   (regel 1086-1088) niet uitschakelen → alle 4 inset-properties gezet →
>   `.duration` werd opgerekt over de hele `.ph` (247×454px) → leek op
>   een wazige overlay van de hele card.
> - **Img-loading separate:** alle thumbnails op `loading="lazy"` (sessie
>   28+) + de img zit binnen aspect-ratio container → intersection
>   observer triggert pas na scroll → eerste paint heeft `naturalSize 0x0`
>   thumbnails → wazig.
> - **Beide fixes doorgevoerd** (zie hieronder).
>
> ### Fixes doorgevoerd
>
> 1. **Fix 1 — Bug 4 CSS (`top: auto; left: auto;`)** in
>    `static/index.html` regel ~4055. Sessie 53-comment toegevoegd.
>    Duration-pill staat nu correct rechtsonder ipv stretching.
> 2. **Fix 2 — Eager loading eerste 8 thumbnails** in `renderClipGrid()`
>    regel ~9082: `loading="${i < 8 ? 'eager' : 'lazy'}"`. Eerste rij is
>    direct geladen bij dashboard-open, rest blijft lazy om netwerk-storm
>    bij 50+ clips te voorkomen.
> 3. **Fix 3 — Captions-info-tekst** in export-modal: nieuw HTML element
>    `#exs-captions-empty` ("Geen captions aanwezig op deze clips —
>    voeg ze toe via de editor.") + async-fetch in `pickExportSettings`
>    die `/api/clip-overlays/<job>` checkt voor de geselecteerde indices.
>    Tekst verschijnt onder Captions-toggle alleen als géén overlays op
>    de te exporteren clips zitten. Voorkomt Bug 2's "toggle aan maar
>    geen output"-verwarring.
> 4. **Fix 4 — Rename-bug `exportSelected`** regel 10000: `c.index === idx`
>    → `c.index === idx + 1`. Sessie 52 mini-bevinding 2 was dus geen
>    zeldzame zijroute — het was de hele "Export selected met 1 clip"
>    route die single-clip rename brak.
> 5. **Fix 5 — Animation-default op "None"** (taak 6, Sjuul's verzoek):
>    `defaultLayer` factory `anim: 'fade'` → `'none'`, plus
>    `<option value="none" selected>` in de dropdown (was fade).
>
> ### Files gewijzigd deze sessie
>
> - `dj-clip-cutter/static/index.html`: +1502 bytes (5 fixes + 2
>   sessie-53-comments). Backup: `static/index.html.pre-sessie53-fixes.bak`
>   (796KB, vóór alle fixes).
> - **GEEN backend-wijzigingen** — `app.py`, `cutter.py`, `auth.py`
>   ongewijzigd.
> - Memory: `project_omni_dj_rebrand.md` aangemaakt + MEMORY.md index
>   bijgewerkt.
>
> ### Bundle-status
>
> - `/Applications/Omni DJ.app` — Rebuild #2 (sessie 53 fixes) ✅
> - `/Applications/Omni DJ.PRE-SESSIE53.app` — verwijderd (was rebuild
>   #1, vervangen door de oudere)
> - `/Applications/Omni DJ.PRE-SESSIE53b.app` — rebuild #1 als
>   rollback bewaard
> - `dist/Omni DJ.app` + `dist/Omni DJ.dmg` — verse bouw
>
> ### Wat Sjuul nog moet (visuele verificatie)
>
> Een korte check in de productie-`.app`:
> 1. Dashboard openen → bevestigen dat **eerste rij thumbnails meteen
>    zichtbaar** is (niet wazig)
> 2. Bevestigen dat **timestamp-pill rechtsonder** in elke thumb staat
>    (klein, ~10px font, niet stretching)
> 3. Selecteer 1 clip → "Export selected" → bevestig dat **rename-veld
>    prefilled** is met `Drop_N` (was `null` voor sessie 53)
> 4. In editor → Text-drawer → "+ Add text" → bevestig dat
>    **Animation dropdown standaard op "None"** staat
> 5. Selecteer een clip waar **geen** caption op zit → Export → bevestig
>    dat onder Captions-toggle de info-tekst "Geen captions aanwezig op
>    deze clips" verschijnt
>
> ### Bewust niet gedaan deze sessie
>
> - Code-side rebrand "Omni DJ" → "Omni DJ" in
>   index.html/launcher.py/app.py/build_macos.sh/auth.py + alle README's.
>   Aparte rebrand-sessie waard (~4-6u dev).
> - Folder renames `dj-clip-cutter/` + `Omni DJ/`. Hoge risico,
>   raakt alle build-paden.
> - App-icon vervangen.
> - omnidj.com koppelen (Fase 3 van launch-plan; runbook moet eerst
>   omschreven van omnidj.com → omnidj.com).
> - Stripe live mode (Fase 4).
> - Bug 1 (selectie-balk) — pas oppakken als Sjuul kan reproduceren met
>   stappen.
>
> ### Volgende sessie
>
> 1. Visuele verificatie (5 checks hierboven) en eventuele restbugs
> 2. Code-side rebrand "Omni DJ" → "Omni DJ" (aparte sessie ~4-6u)
> 3. omnidj.com koppelen via Cloudflare (was djclips.nl)
> 4. Daarna Stripe live mode

---

## STATUS NA SESSIE 52 — E2E EXPORT-TEST GROEN (2026-05-27)

> **Sluitend bewijs dat sessies 50 + 51 samen werken. Caption-export via UI
> levert een MP4 op met de tekst in de pixels. Geen code-wijzigingen, alleen
> verificatie. Sjuul kan nu PyInstaller rebuilden.**
>
> ### Doel
>
> Sessie 51 sloot af met de E2E-test expliciet "uit scope — sessie 52".
> Sessie 50's fix (`cutter.py` regel 20: `import re`) en sessie 51's fix
> (`static/index.html` regel 9548-9550: `exportIdx = backendIdx - 1`) waren
> elk geverifieerd, maar niet samen via de échte UI-route. Sessie 52 sluit
> dat gat.
>
> ### Aanpak
>
> Geen code-wijzigingen. Dev-server (PID 3264, system Python 3.9, 1u05min
> oud, draait vanuit project-cwd op poort 5555) lag al klaar. Strategie:
> - Code-marker-check: `cutter.py` regel 20 = `import re` ✅, `static/index.html`
>   regel 9542 = `SESSIE 51 fix — Bug 1` ✅. Geladen JS in browser bevat
>   beide markers.
> - UI-route: inline editor (NIET full-page editor) → Save→Export-knop in
>   drawer onder dashboard-card → `_ceCommitReexport` → `startExport` →
>   `POST /api/export`. Dit is de route die sessie 51's frontend-fix raakt.
> - Bewijs-laag 1: monkey-patch `window.fetch` om de outgoing POST body op
>   te vangen → kijken of `clip_indices` 0-based is.
> - Bewijs-laag 2: ffmpeg frame-extract uit output-MP4 op t=3s → visueel
>   inspecteren of "CAPTION"-tekst in de pixels zit.
>
> ### Stappen
>
> 1. Server-check via `lsof -nP -iTCP:5555 -sTCP:LISTEN`: PID 3264 luistert,
>    cwd via `lsof -p 3264 -a -d cwd` = `dj-clip-cutter/`. `curl HTTP 200`
>    op `/`.
> 2. Code-markers op disk geverifieerd via grep + in geladen pagina via
>    `document.documentElement.outerHTML.includes(...)`. Beide groen.
> 3. Setup-status in Chrome MCP: Sjuul al ingelogd via Supabase
>    session-restore, redesign-v2 flag aan, dashboard toont Lisa Korver-set
>    `e63f06a6` met 30 clips. Belangrijk: `window.STATE === undefined` maar
>    `typeof STATE === 'object'` werkt vanuit eval (STATE zit in module-scope
>    IIFE). Direct refereren met `STATE.clips[2].index` werkt wel.
> 4. `text_overlays.json` op disk bevestigt clip 3 heeft nog steeds layer
>    "CAPTION" (bold 14% wit op 80% Y, fade, in_sec=0/out_sec=63.29). Sessie
>    50's `Drop_3.mp4` (15.028.117 bytes) hernoemd naar
>    `Drop_3.SESSIE50.mp4` zodat verse export niet verward wordt met de
>    oude.
> 5. Klik op `.ph` van clip 3 (data-idx=2) opende per ongeluk de full-page
>    editor, niet de inline drawer. Code-inspectie regel 9224 + 9551
>    bevestigt: `toggleInlineEditor(idx, btnEl)` opent de drawer, en `_ceCommitReexport`
>    in die drawer raakt de sessie 51-fix. Inline drawer geopend met
>    `toggleInlineEditor(2, card.querySelector('.ce-adjust-btn'))`. Drawer
>    toont knoppen "Reset" + "Export".
> 6. Monkey-patch:
>    ```js
>    window.__sess52 = { exportCalls: [] };
>    var origFetch = window.fetch;
>    window.fetch = function(u, opts){
>      if(typeof u === 'string' && u.indexOf('/api/export/') !== -1 && opts && opts.method === 'POST'){
>        var b = (typeof opts.body === 'string') ? JSON.parse(opts.body) : opts.body;
>        window.__sess52.exportCalls.push({url: u, body: b, time: Date.now()});
>      }
>      return origFetch.apply(this, arguments);
>    };
>    ```
> 7. Klik Export-knop in drawer → export-settings-modal opent
>    (`#export-settings-modal.aspect-back.on`). Modal-velden:
>    - `#exs-rename` = "Drop_3" (sessie 43 prefilled rename werkt)
>    - 9:16 standaard aan
>    - `#exs-captions-input` = false
>    - `#exs-watermark-input` = false
>    - Submit-knop = `#exs-continue` "Exporteren"
>    Rename gezet naar `Drop_3_SESSIE52_TEST`, captions-toggle aangeklikt via
>    `#exs-toggle-captions.click()` → checked=true.
> 8. Klik `#exs-continue` → monkey-patch ving op:
>    ```json
>    {
>      "url": "/api/export/e63f06a6",
>      "body": {
>        "aspects": ["vertical"],
>        "codec": "match",
>        "fps": "match",
>        "resolution": "source",
>        "overlays": {"captions": true, "watermark": false, "logo": true},
>        "labels": {"3": "Drop_3_SESSIE52_TEST"},
>        "output_dir": "/Users/sjuulsmits/Downloads/",
>        "clip_indices": [2]
>      }
>    }
>    ```
>    **`clip_indices: [2]` is 0-based, exact wat sessie 51's fix oplevert.**
>    `backendIdx=3` (clip.index, 1-based) → `exportIdx=2` (sessie 51 conversie)
>    → backend `clips[2]` = clip met `index=3` = clip mét overlay ✅.
>    `labels` map gebruikt 1-based key "3" (matched text_overlays.json keys).
> 9. Output landt in `~/Downloads/Drop_3_SESSIE52_TEST.mp4` (15.028.117 bytes,
>    identiek aan sessie 50's baked-MP4 — `_baked_for_export` cache hit) +
>    sidecar `Drop_3_SESSIE52_TEST.mp4.meta.json` met `clip_index: 3`
>    (1-based naar gebruiker).
> 10. Visuele verificatie:
>     ```
>     ffmpeg -y -ss 3 -i ~/Downloads/Drop_3_SESSIE52_TEST.mp4 \
>            -frames:v 1 -q:v 2 -update 1 /tmp/sess52_frame_t3.jpg
>     ```
>     Frame op t=3s toont scherp witte "CAPTION"-tekst gecentreerd op ~80% Y
>     bold, exact zoals `text_overlays.json` specificeert. Lisa Korver (DJ)
>     herkenbaar in beeld — juiste clip. Frame visueel geïnspecteerd via Read
>     tool op de jpg.
>
> ### Bewezen keten
>
> ```
> cutter.py:20 `import re` (sessie 50)
>   → _write_layer_textfile faalt niet meer
>     → recut_clip lukt
>       → _prebake_clip_for_export returnt baked-path (i.p.v. None)
>         → _run_export_job gebruikt baked-MP4
>           → captions in pixels
>             → ffmpeg frame-extract bevestigt visueel
> ```
>
> Werkt voor de **single-clip-editor-export** route na sessie 51's
> frontend-fix.
>
> ### Niet getest deze sessie (uit scope)
>
> - Multi-clip select-and-export via `exportSelected` (al 0-based
>   pre-sessie51, geen regressie verwacht — maar niet expliciet geverifieerd)
> - Export All (`exportAll` → `startExport(null, ...)`)
> - Editor full-page export-route (de Export-knop in de full-page editor
>   tool-rail) — onbekend of die ook `_ceCommitReexport` hergebruikt of een
>   eigen call-site heeft
> - Watermark-bake
> - Multi-ratio export (9:16 + 16:9 tegelijk)
> - Queue-bar UX bij ≥2 jobs
>
> ### Mini-bevindingen voor later (NIET kritisch, niet sessie 52-werk)
>
> 1. `static/index.html` regel 10351: comment op `startExport` zegt
>    "indices = array of 1-based clip-indices". Sinds sessie 51 is dat
>    **0-based**. Comment-update is 1 regel; valt onder
>    documentatie-hygiene.
> 2. `static/index.html` regel 10000 in `exportSelected`:
>    `const clip = (STATE.clips || []).find(c => (c.index ?? null) === idx);`
>    met `idx` 0-based vs `clip.index` 1-based → matched **nooit**. `clip`
>    blijft `undefined`, `opts.singleClip` wordt nooit gezet. Komt enkel
>    voor in zeldzame zijroute (multi-select met precies 1 item geselecteerd
>    → de rename-prefill in modal mist dan). Geen kritisch pad, geen
>    beta-blocker.
>
> ### Files gewijzigd deze sessie
>
> Geen code wijzigingen. Alleen:
> - `~/Downloads/Drop_3.SESSIE50.mp4` ← hernoemd van Drop_3.mp4 (was sessie 50's
>   bewijs-MP4 binnen `dj-clip-cutter/output/e63f06a6/exports/`, dus
>   technisch verkeerd genoteerd in eerste lijst — staat **NIET** in
>   Downloads maar in de project-output folder)
> - `~/Downloads/Drop_3_SESSIE52_TEST.mp4` + `.meta.json` (verse export, mag
>   weggegooid worden)
>
> Correctie: de rename gebeurde op:
> `dj-clip-cutter/output/e63f06a6/exports/Drop_3.SESSIE50.mp4` (van
> `Drop_3.mp4`). De **nieuwe** export landde in `~/Downloads/` omdat dat de
> default `output_dir` in de export-modal was.
>
> ### Wat Sjuul nu kan doen
>
> 1. **PyInstaller rebuild** — `./build_macos.sh dmg`. Sessies 50 + 51 fixes
>    gaan dan mee in de productie-.app. Geen blockers meer voor de bundle.
> 2. **Test-artefact weggooien** — `~/Downloads/Drop_3_SESSIE52_TEST.mp4`
>    (+ meta.json) mag in de prullenbak. Sessie 50's bewijs-MP4 in
>    `dj-clip-cutter/output/e63f06a6/exports/Drop_3.SESSIE50.mp4` blijft als
>    referentie.
> 3. **Optioneel** — Visuele controle in echte browser dat de v2
>    export-modal toggle-bolletjes in ON-state oranje pill met witte cirkel
>    rechts zijn (sessie 51's CSS-fix, was via MCP-screenshot al groen).
>
> ### Dev-server status
>
> Draait nog op poort 5555 (PID 3264, system Python 3.9). Cmd+Tab Terminal
> → Ctrl+C als je 'm wil stoppen. Belangrijk om te weten: deze instance
> draait met **system Python**, niet venv. Werkt voor de export-keten
> (librosa+demucs zitten kennelijk ook in system-Python op deze Mac), maar
> als je opnieuw start gebruik dan `./start.sh` voor de venv-Python.
>
> ### Volgende sessie
>
> 1. PyInstaller rebuild als Sjuul nog niet gedaan heeft → captions in
>    .app verifiëren via UI
> 2. Optioneel: mini-bevinding 1 + 2 fixen (comment-update regel 10351 +
>    `exportSelected` find-by-index) als tech-debt opruim-batch
> 3. Optioneel: andere export-routes (Export All, multi-clip, full-page
>    editor) bevestigen om 100% dekking te krijgen
> 4. Anders: vooruit met Fase 5 redesign (Social/Calendar/Insights echte
>    features) of nieuwe features uit moat-plan (PLAN-MOAT-FEATURES.md)

---

## STATUS NA SESSIE 50 — CAPTION-BAKE BUG OPGELOST (2026-05-27)

> **Bug 2 (root cause) gefixt met 1-regel-edit. Bug 1 (off-by-one) gevonden,
> bewust nog OPEN voor sessie 51. Caption-export werkt nu in dev-server.**
>
> ### Aanleiding
>
> Sessie 49 confirmde: caption-bake pipeline (sessie 43a/43b) werkt niet in
> de bundle. Diagnose-log werd niet zichtbaar door PyInstaller `runw`
> stdout-redirect, dus blocker werd doorgeschoven naar sessie 50 met aanpak
> "dev-server gebruiken waar stdout wel zichtbaar is".
>
> ### Diagnose-aanpak
>
> 1. Hangende Omni DJ `.app` proces (PID 93126) op poort 5555 gekild via
>    `osascript do shell script "kill 93126"` (Cmd+Q sloot UI maar liet
>    Python-backend draaien — bekend PyInstaller-patroon op Mac).
> 2. Dev-server gestart in achtergrond:
>    ```
>    cat > /tmp/clip-live-launch.sh << 'EOF'
>    #!/bin/bash
>    export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin
>    cd '/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter'
>    source venv/bin/activate
>    exec python app.py 5555
>    EOF
>    chmod +x /tmp/clip-live-launch.sh
>    nohup /tmp/clip-live-launch.sh > /tmp/clip-live-dev.log 2>&1 &
>    ```
>    Werkt omdat `osascript do shell script` PATH minimaal heeft → ffmpeg
>    moet expliciet in PATH. Venv-activate zorgt dat de juiste Python +
>    dependencies (librosa, demucs, etc.) geladen worden.
> 3. 4 SESSIE50_DIAG-prints in `_run_export_job._process` op exacte regels:
>    5854 (raw_overlays + overlays_cfg), 5892 (clip_index + layer_info +
>    want_captions + needs_prebake), 5901 (prebake-result), 5917 (final
>    sources vóór ffmpeg).
> 4. Sjuul ingelogd in Chrome (account `business+dmgtest1@sjuulstudios.com`,
>    user_id `d86a3a54-aa47-472e-875f-e17347e406df`). Job `e63f06a6` (Lisa
>    Korver x Ho_r Berlin, 30 clips, 144 BPM) had al een
>    `text_overlays.json` met overlay "CAPTION" op clip 3 (bold 14% wit op
>    80% Y, fade-anim).
> 5. Export-call via JS (gebruikt jouw auth-token, exact zoals frontend):
>    ```js
>    fetch('/api/export/e63f06a6', { method:'POST', headers:{...auth},
>      body: JSON.stringify({
>        aspects:['vertical'], codec:'match', fps:'match',
>        resolution:'source',
>        overlays:{captions:true, watermark:false, logo:false},
>        clip_indices:[3]
>      })
>    })
>    ```
>    Test 1 (`clip_indices:[3]`) → backend pakte `clip_index=4`
>    (= `clips[3]` 0-based) → `has_text_layers=False` → **off-by-one
>    bug ontdekt (Bug 1)**.
>    Test 2 (`clip_indices:[2]`) → backend pakte `clip_index=3` correct →
>    `has_text_layers=True, needs_prebake=True, baked=None` → log toonde
>    `ERROR prebake: recut_clip failed for clip 3: name 're' is not defined`
>    → **Bug 2 (root cause) gevonden**.
>
> ### Root cause Bug 2
>
> `dj-clip-cutter/cutter.py` regel 274 in `_write_layer_textfile`:
> ```python
> safe_id = re.sub(r'[^A-Za-z0-9_-]', '', str(layer_id or 'layer'))[:32] or 'layer'
> ```
> `re`-module nooit geïmporteerd in cutter.py. Stacktrace volledig in log:
> ```
> recut_clip (cutter.py:1862)
>   → cut_clip_vertical (1721)
>     → _build_vertical_cmd (1135)
>       → _maybe_compose_brand_vf (753)
>         → _build_text_layer_filters (310)
>           → _write_layer_textfile (274) ← NameError here
> ```
> `_prebake_clip_for_export` (app.py:5754-5768) heeft een blanket
> `except Exception` die de NameError opvangt en `None` returnt. Caller
> (`_run_export_job._process` regel 5915) logt alleen een `log.warning`
> en valt terug op live-files. Daarom was de bug stil voor de gebruiker —
> export voltooit "succesvol" maar zonder captions.
>
> Waarschijnlijke oorzaak: import-regel per ongeluk verwijderd tijdens
> sessie 41/42 (Fase 5 fonts + color wheels), waar `cutter.py` flink
> herstructureerd is. Geen regressie-test ving 'm omdat de meeste flows
> die `_write_layer_textfile` raken via een ander pad lopen of er waren
> geen E2E export-tests met overlays in CI.
>
> ### De fix (Bug 2)
>
> **Bestand:** `dj-clip-cutter/cutter.py`
> Regel 20 toegevoegd, alfabetisch tussen `platform` en `shutil`:
> ```python
> import subprocess
> import os
> import json
> import csv
> import platform
> import re          ← NIEUW
> import shutil
> from concurrent.futures import ProcessPoolExecutor, as_completed
> from pathlib import Path
> ```
>
> Eén regel. Eén bestand. Zero functionele risico's. Geen tests gebroken
> want `re` is stdlib — geen extra dependency.
>
> ### Verificatie sessie 50
>
> Statisch:
> - ✅ `python3 -c 'import ast; ast.parse(open("cutter.py").read())'` → SYNTAX OK
> - ✅ `python3 -c 'import ast; ast.parse(open("app.py").read())'` → SYNTAX OK (na cleanup DIAG-prints)
> - ✅ `grep -n '^import re' cutter.py` → regel 20
> - ✅ `grep SESSIE50_DIAG app.py` → 0 matches (DIAG-prints schoon weg)
>
> Runtime (post-fix dev-server herstart):
> - ✅ Server start zonder errors/tracebacks (log: `Running on http://127.0.0.1:5555`)
> - ✅ Export-call `clip_indices:[2]` produceert `baked={'vertical': '.../e63f06a6/_baked_for_export/e63f06a6_clip03_drop_vertical.mp4'}` — niet meer `None`
> - ✅ Definitieve MP4 `output/e63f06a6/exports/Drop_3.mp4` (15.028.117 bytes, met sidecar `.meta.json`)
> - ✅ Frame-extract (`ffmpeg -ss 3 -frames:v 1`) toont scherpe witte "CAPTION"-tekst op 80% Y zoals gespecificeerd
> - ✅ `_baked_for_export/` opgeruimd na succesvolle export (cleanup-stap app.py:5994-6002 werkt)
>
> ### Bug 1 — OPEN voor sessie 51
>
> **Locatie:** mismatch tussen frontend en `app.py` regel 6160-6165.
> Frontend (`static/index.html` regel 9488): `startExport([st.backendIdx],
> ...)` waar `backendIdx = clip.index` (1-based, matched `text_overlays.json`-keys).
> Backend interpreteert `clip_indices` als 0-based array-positie:
> ```python
> selected_idx = sorted({int(i) for i in raw_sel
>                        if isinstance(i, (int, float)) and 0 <= int(i) < len(clips)})
> ```
> Comment op regel 6158 zegt expliciet "0-based" — maar frontend doet
> nergens `-1`. Bug zit dus in semantiek-afspraak, niet in code-defect.
>
> **Impact:** UI-selectie "clip 3" → backend exporteert clip 4. Voor de
> meeste gebruikers onzichtbaar omdat naburige clips lijken (zelfde set).
> Werd zichtbaar bij overlays omdat alleen specifieke clip-indices captions
> hebben (van de Lisa Korver-set: clips 1, 2, 3 — met off-by-one pakte
> backend clips 2, 3, 4 → clip 4 mist altijd captions). Dit maskeerde
> sessie 49's diagnose: de DIAG-output had moeten zien dat een clip met
> overlays `has_text_layers=True` had, maar door off-by-one zag 'ie steeds
> de "next" clip die geen overlays had.
>
> **Fix-opties:**
> - **Optie A (aanbevolen):** in `app.py` regel 6164:
>   ```python
>   selected_idx = sorted({int(i) - 1 for i in raw_sel
>                          if isinstance(i, (int, float)) and 1 <= int(i) <= len(clips)})
>   ```
>   Plus comment-update regel 6157-6159 ("1-based, matches clip.index in UI").
>   Eén regel codewijziging, één commentaarwijziging. Sluit aan op
>   `text_overlays.json` keys + UI-display.
>
> - **Optie B:** in `static/index.html` regel 9488, stuur `st.backendIdx - 1`.
>   Risico: andere `startExport` call-sites (regels 9940 + 9948) moeten
>   óók aangepast, plus toekomstige call-sites kunnen het vergeten.
>
> Optie A is concentratie-fix, Optie B is verdeel-fix. Aanbeveling = Optie A.
>
> ### Bestanden gewijzigd deze sessie
>
> - `dj-clip-cutter/cutter.py`: +1 regel (`import re` op regel 20).
> - `dj-clip-cutter/app.py`: DIAG-prints toegevoegd op regels ~5854/5892/5901/5917, dan weer verwijderd. Netto 0 wijziging.
>
> ### Wat Sjuul nog moet doen
>
> 1. **PyInstaller rebuild** zodra je captions in de productie-`.app` wil
>    hebben. De fix zit in dev-server-code; bundle in `/Applications` heeft
>    'm nog niet. Procedure: zie `INSTALLER-RUNBOOK.md` of
>    `LESSONS-LEARNED.md`. Command: `./build_macos.sh dmg`.
> 2. **Sessie 51 plannen** voor:
>    - Bug 1 fixen (Optie A aanbevolen)
>    - UI-fixes export-modal: toggle-bolletjes (oranje fill + checkmark als
>      aan), label "CAPTIONS INBAKKEN" → "CAPTIONS", description-tekst
>      weghalen
>    - Rebuild .app/.dmg na fix
> 3. **Dev-server draait nog** (PID 2562, op poort 5555). Cmd+Tab → Terminal
>    → Ctrl+C als je 'm wil stoppen. Of laat 'm draaien tot je een nieuwe
>    sessie begint.
>
> ### Bewust uit scope sessie 50
>
> - Bug 1 fixen (afgesproken: alleen Bug 2 nu om regressie-oppervlak klein
>   te houden)
> - UI-fixes export-modal toggles + labels (sessie 51)
> - PyInstaller rebuild (Sjuul doet dat zelf)
> - Andere export-paden (multi-clip, Export All, Editor-export) — alleen
>   single-clip-export getest. Bug 2 (NameError) raakt alle paden die
>   `_write_layer_textfile` triggeren, dus is gefixt voor alle paden. Bug 1
>   raakt alleen single-clip-select-and-export, niet "alle clips".
>
> ### Volgende sessie
>
> 1. Bug 1 fixen via Optie A in `app.py` regel 6164 + comment-update
> 2. UI-fixes export-modal (toggle-bolletjes + label + description)
> 3. Verificatie via dev-server + Chrome-MCP zoals sessie 50
> 4. PyInstaller rebuild → .app → .dmg

---

## STATUS NA SESSIE 48 — REDESIGN FASE 4 (2026-05-26)

> **Modals in v2-stijl. CSS-only. Geen JS/backend wijzigingen.**
>
> ### Aanpak gekozen na inventarisatie
>
> Net als bij sessies 45/46/47: alle 5 modals in `static/index.html` hebben
> heldere DOM-structuur (één scrim-element met klasse + één direct-child
> "card"-div). Pure CSS-restyle volstaat — geen JS aanrakingen,
> geen DOM-IDs hernoemen. Resultaat: **0% risico op functionele regressie**
> op login/signup/forgot/upgrade/aspect/export-flows.
>
> ### Beslissingen
>
> 1. **Volledige scope** — alle 5 modals tegelijk in v2-stijl (Sjuul akkoord).
> 2. **Reset-password.html bewust UIT scope** — standalone landingspagina,
>    geen onderdeel van SPA, geen flag-aware logica. Krijgt eigen polish
>    later als Sjuul dat wil.
> 3. **Generieke scrim-tokens** — alle 5 modals delen scrim `rgba(8,8,10,0.78)`
>    + `backdrop-filter: blur(14px) saturate(140%)`. Eén plek wijzigen = alle
>    modals updaten.
> 4. **Accent spaarzaam** — alleen submit-buttons en active-states krijgen
>    `#D97742` fill. Geen oranje vlakken op cards/scrim.
> 5. **Upgrade-modal premium-detail** — subtiele 2px accent-gradient bovenaan
>    de kaart (`linear-gradient(90deg, transparent, accent, transparent)` met
>    opacity 0.6) als enige sierelement. Premium-feel zonder zwaar te zijn.
>
> ### Wat is gewijzigd
>
> **Bestand:** `dj-clip-cutter/static/index.html`
> - Bytes 786.023 → 810.655 (+24.632)
> - Nieuw CSS-blok ingeprikt vóór `</style>` op regel ~4906
> - Blok-marker in code: `/* REDESIGN v2 — Fase 4 (Modals, 2026-05-26) */`
> - 185 nieuwe `body.redesign-v2` modal-selectors verdeeld over 5 modals:
>   - 49 op `.auth-overlay`
>   - 28 op `.auth-wizard`
>   - 15 op `.forgot-modal`
>   - 37 op `.upgrade-modal`
>   - 27 op `#aspect-modal`
>   - 29 op `#export-settings-modal`
>
> ### Selectors toegevoegd (clusters, alle scoped onder `body.redesign-v2`)
>
> ```
> # GENERIEK
> .auth-overlay / .forgot-modal / .upgrade-modal / #aspect-modal / #export-settings-modal
>   → scrim rgba(8,8,10,0.78) + backdrop-filter blur(14px) saturate(140%)
>
> # AUTH OVERLAY (login + signup)
> .auth-card                        → bg-elevated + border-subtle + radius 16 + drawer-shadow
> .auth-brand / .auth-left / .auth-hero → linear-gradient #0E0E0F→#15151A→#1A1A22
> h1/h2/h3                          → text-primary + Inter 600
> p / label / .auth-sub             → text-secondary
> .auth-tabs / [role=tablist]       → segmented control (bg-elevated-2 + padding 3px)
> .auth-tab[aria-selected=true]     → bg-hover + inset border-strong
> input[email|password|text]        → v2-input (bg-elevated-2 + radius 8)
> input:focus                       → accent border
> button[type=submit] / .btn-primary → accent fill + #0E0E0F text
> a / .auth-link                    → accent
> .auth-error                       → soft red bg/border
> .auth-success                     → soft green bg/border
>
> # AUTH WIZARD (onboarding)
> .wiz-step / .wiz-card             → bg-elevated-2 + radius 12
> .wiz-dot                          → border-strong default, accent + scale(1.2) bij active
> .wiz-nav button                   → v2-iconbutton stijl
> .wiz-nav button.primary           → accent fill
> .wiz-skip                         → transparent + tertiary text + underline
> .wiz-option / .wiz-tile           → bg-elevated + radius 10 + border-subtle
> .wiz-option.is-selected           → accent-muted + accent border + accent text
>
> # FORGOT MODAL
> .forgot-modal-card                → bg-elevated + radius 14 + drawer-shadow + max-width 420
> #forgot-modal-title               → Inter 600 17px primary
> #forgot-modal-email               → v2-input
> #forgot-modal-submit              → accent fill
> #forgot-modal-close               → v2-iconbutton 28×28
> #forgot-modal-success             → soft green bg/border
>
> # UPGRADE MODAL
> .upgrade-card                     → bg-elevated + radius 16 + drawer-shadow + max-width 540
> .upgrade-card::before             → 2px accent-gradient lijn bovenaan (opacity 0.6)
> #upgrade-title                    → Inter 600 22px primary
> .upgrade-price / .price           → accent 26px Inter 700
> .upgrade-features li / .feat      → border-subtle dividers
> .upgrade-cta / #upgrade-cta       → accent fill
> .upgrade-cancel / button.secondary → bg-elevated-2 + border-subtle + secondary text
> .quota-line / .upgrade-quota      → bg-elevated-2 + JetBrains Mono 12px tertiary
>
> # ASPECT MODAL + EXPORT SETTINGS MODAL (delen .aspect-back scrim)
> .aspect-card                      → bg-elevated + radius 14 + drawer-shadow + max-width 480
> #aspect-modal-title / #exs-title  → Inter 600 16px primary
> #aspect-modal-sub                 → text-secondary 13px
> #aspect-modal-opts                → grid auto-fit minmax(120px, 1fr) gap 8
> #aspect-modal-opts button         → kaartje bg-elevated-2 + radius 10 + hover lift -1
> #aspect-modal-opts button.on      → accent-muted + accent border + accent text
> #aspect-modal-cancel / .aspect-cancel → bg-elevated-2 + border-subtle
> .modal-confirm / button.primary   → accent fill
> #export-settings-modal label      → uppercase tertiary 11px
> #export-settings-modal input/select/textarea → v2-input
> #export-settings-modal input[type=checkbox] → accent-color: accent
> #export-settings-modal .toggle-row → bg-elevated-2 + border-subtle + flex space-between
>
> # GENERIEKE MODAL-CLOSE in alle 5 modals
> .modal-close                      → v2-iconbutton 28×28
> ```
>
> ### Backup sessie 48
>
> - `static/index.html.pre-redesign-fase4.bak` (786.023 bytes, identiek aan
>   stand na sessie 47).
>   Rollback: `cp static/index.html.pre-redesign-fase4.bak static/index.html && ./start.sh`
>
> ### Verificatie sessie 48
>
> Statisch:
> - ✅ JS-blok bytes-identiek aan sessie 47 (467.780 → 467.780, delta = 0)
> - ✅ `node --check` op het JS-blok: exit 0 (groen)
> - ✅ Python `html.parser` over hele file: 0 parse errors (bak + new)
> - ✅ Tag-balance delta vs backup: 0 voor html/body/head/div/span/aside/main/section/style/script/button/input/form/select/textarea
> - ✅ `<style>` / `</style>` count ongewijzigd (2/1)
> - ✅ Marker open + close = 1
> - ✅ 185 nieuwe `body.redesign-v2` modal-selectors aanwezig (49+28+15+37+27+29)
>
> Live geverifieerd via Chrome MCP op Sjuul's dev-server (localhost:5555):
>
> Met flag AAN (`localStorage.omniDjRedesignV2='1'`):
> - ✅ Alle 5 modals krijgen scrim `rgba(8, 8, 10, 0.78)`
> - ✅ Auth-card: bg `rgb(22,22,24)` = `#161618`, border subtle 1px, radius 16px, drawer-shadow
> - ✅ Forgot-card: bg `#161618`, border subtle, radius 14px, drawer-shadow
> - ✅ Forgot-email input: bg `rgb(26,26,29)` = bg-elevated-2, border subtle, radius 8px
> - ✅ Forgot-submit button: bg `rgb(217,119,66)` = `#D97742` accent, color `rgb(14,14,15)`, radius 8px, border 0
> - ✅ Upgrade-card, aspect-card, expset-card allemaal in nieuwe stijl
> - ✅ CSS-vars actief: `--v2-accent=#D97742`, `--v2-bg-elevated=#161618`, `--v2-text-primary=#F5F2EC`
>
> Met flag UIT (`localStorage.omniDjRedesignV2='0'`):
> - ✅ `body.className = ""` (geen `redesign-v2`)
> - ✅ auth-card radius 28px (oude waarde, niet 16)
> - ✅ forgot-card radius 20px (oude waarde, niet 14)
> - ✅ forgot-input radius 14px (oude waarde, niet 8)
> - ✅ forgot-submit bg `rgb(232,183,102)` = oude warm-amber `#E8B766` (niet `#D97742`)
> - ✅ scrim `rgb(10,8,5)` (oude warm-dark, niet `rgba(8,8,10,0.78)`)
> - ✅ Oude UI 100% intact, geen residu
>
> ### Bestanden gewijzigd deze sessie
>
> - `dj-clip-cutter/static/index.html`:
>   - +~425 regels CSS (Fase 4 modals) vóór `</style>`
>   - Geen JS-aanrakingen
>   - Geen DOM-IDs hernoemd of toegevoegd
>   - Reset-password.html niet aangeraakt
>
> ### Wat Sjuul nog moet doen (runtime-tests die niet via Chrome MCP gedekt zijn)
>
> 1. **Interactietest auth-overlay (flag AAN):**
>    - Log uit (Settings → Sign out) → auth-overlay verschijnt in v2-stijl
>    - Tabs Sign in / Sign up switchen → segmented control on-state pakt
>    - Verkeerd password → error-bg verschijnt in soft red
>    - "Forgot password?" klikken → forgot-modal opent in v2
>    - Email invoeren + Submit → success-bg verschijnt in soft green
>    - Sign up flow → auth-wizard (als die actief is) → dots + tiles in v2
> 2. **Interactietest upgrade-modal (flag AAN):**
>    - Quota opgebruiken (of /api endpoint forceren) → upgrade-modal opent
>    - Lijst features, price-tag in accent, CTA-knop in accent
>    - Cancel → modal sluit
> 3. **Interactietest aspect-modal + export-settings-modal:**
>    - Export single clip → aspect-modal opent, kies 9:16 → optie krijgt accent-state
>    - Export multi-clip met settings → export-settings-modal opent
>    - Captions/watermark toggles, output-folder input, Submit
> 4. **Smoketests sessies 43+44+47 nog open** (komen vanzelf bij volgende interactie-test)
>
> ### Bewust uit scope sessie 48
>
> - `reset-password.html` → standalone pagina, krijgt eigen polish-sessie indien gewenst
> - Brand Stack modal (Sjuul gebruikt momenteel een view, geen modal — geen aanpassing nodig)
> - Lichte aanpassing aan oude warm-amber tokens in legacy-modus (we raken alleen v2 aan)
> - PyInstaller rebuild → **volgende stap** als alle interactietests groen zijn
>
> ### Volgende sessie

> 1. Interactietests sessie 48 draaien (auth/upgrade/aspect/export-flows)
> 2. Smoketests sessies 43/44/47 afronden
> 3. Als alles groen: **PyInstaller rebuild** → .app → .dmg
>    (procedure: zie `LESSONS-LEARNED.md` + `INSTALLER-RUNBOOK.md`)
> 4. Optioneel daarna: **Fase 5 — Social/Calendar/Insights echte features**
>    (placeholder-cards vervangen door werkende screens)

---

## STATUS NA SESSIE 47 — REDESIGN FASE 3 (2026-05-26)

> **Editor / Timeline polish in v2-stijl. CSS-only. Geen JS/backend wijzigingen.**
>
> ### Aanpak gekozen na inventarisatie
>
> Net als bij sessies 45/46 was het bestaande DOM-skelet rijk genoeg om
> met pure CSS naar de v2-look te brengen. De editor-shell (`#view-editor`)
> heeft heldere klassen (`.editor`, `.ed-top`, `.ed-tools`, `.ed-body`,
> `.ed-left`, `.ed-canvas`, `.ed-right`, `.timeline`, `.tl-toolbar`,
> `.tl-scroll`, `.tl-minimap`, `.ed-text-drawer`, `.ed-track-drawer`)
> waardoor de hele restyle in één CSS-blok kan, zonder JS aanrakingen
> en zonder DOM-IDs hernoemen. Resultaat: **0% risico op functionele
> regressie** op trim/recut/slice, BPM/snap/loop, text-layer rendering,
> font-pickers, track-keyframes, waveform/spec toggle, mini-map.
>
> ### Beslissingen
>
> 1. **Volledige editor-restyle** (niet alleen drawers) — match aanbevolen
>    scope: ed-shell + toolbar + waveform-frame + timeline + cue-rows +
>    trim-handles + alle drawers.
> 2. **Toolbar-stijl = dashboard-stijl uit Fase 2** — subtle border, bg-elevated,
>    radius 8, accent oranje alleen op de primary play-button + trim-handles +
>    accent-toggles (Snap/Loop on-state) + de actieve cue-row + time-cursor.
> 3. **Trim als primary action gemarkeerd** met border-strong (i.p.v. border-subtle),
>    krijgt op hover de accent-kleur — visuele hint dat dit de hoofd-actie is
>    zonder zwaar oranje vlak te plaatsen.
> 4. **Geen wijziging aan track-drawer DOM-classes** — track-drawer is een
>    minder vaak gebruikt panel, krijgt dezelfde basis-styling (bg/border/
>    drawer-shadow) + accent op de primary button. Volledige content-restyle
>    komt zodra Sjuul aangeeft dat hij Track-flow doorloopt en daar bugs/
>    styling-gaps tegenkomt.
>
> ### Wat is gewijzigd
>
> **Bestand:** `dj-clip-cutter/static/index.html`
> - Bytes 762.228 → 786.023 (+23.795)
> - Nieuw CSS-blok ingeprikt vóór `</style>` op regel ~4226
> - Blok-marker in code: `/* REDESIGN v2 — Fase 3 (Editor / Timeline polish, 2026-05-26) */`
> - 145 nieuwe `body.redesign-v2 #view-editor`-selectors
>
> ### Selectors toegevoegd (alle scoped onder `body.redesign-v2 #view-editor`)
>
> ```
> # SHELL
> .canvas                      → bg-base + padding 16px
> .editor                      → bg-elevated + border-subtle + radius 14
> .ed-top                      → border-bottom + padding 12/16
> .ed-top .crumbs + b          → typografie v2 (sans 13px primary/secondary)
> .ed-back-btn                 → v2-iconbutton stijl
>
> # TOOLS-TABS
> .ed-tools .t                 → pill (bg-elevated-2 + border-subtle + radius 8)
> .ed-tools .t:hover           → bg-hover + border-strong
> .ed-tools .t.on              → accent-muted + accent-border + accent-text
>
> # CUE PANEL (left)
> .ed-left                     → bg-elevated + border-right
> .ed-left .panel-h .ti/.ct    → primary + mono-tertiary
> .ed-left .filter-row .chip   → radius-16 pill (mockup-stijl)
> .cue-list .cue-row           → kaartje (bg-elevated-2 + border-subtle)
> .cue-list .cue-row.is-active → accent-muted + accent-border
>
> # PREVIEW (center)
> .ratio-rail                  → segmented (bg-elevated + padding 3px)
> .ratio-rail button.on        → bg-hover + text-primary
> .preview-stage               → border-subtle + radius 12 + #050505
>
> # TOOLS-RAIL (right)
> .ed-right                    → bg-elevated + border-left + padding 12/10
> .ed-right .tool-btn          → kaartje + radius 10 + hover lift -1
> .ed-right .tool-btn.on       → accent-muted + accent-border + accent-text
> .ed-right .tool-btn.ed-blade-btn → primary-hint (border-strong, hover=accent)
> .ed-export-wrap              → margin-top auto (sticky-bottom)
> .ed-export-btn               → kaartje + aria-expanded=true → accent-muted
> .ed-export-menu              → bg-elevated + radius 12 + shadow
> .ed-export-menu .ed-export-item → radius 8 hover-row
>
> # TIMELINE
> .timeline                    → bg-elevated + border-top
> .tl-toolbar                  → padding 10/14 + border-bottom
> .tl-toolbar .btn             → v2-iconbutton
> .tl-toolbar .btn.play        → accent fill (#0E0E0F text)
> .tl-toolbar .tl-divider      → border-subtle
> .tl-toolbar .time b          → accent (cursor)
> .tl-toolbar .snap-toggle/.loop-toggle → pill, on-state=accent-muted
> .tl-zoomwrap .ruler          → bg-elevated + border-bottom
> .tl-zoomwrap .tracks .track  → bg-elevated + border-bottom
> .tl-zoomwrap .clip-block     → bg-elevated-2 + border-subtle + radius 6
> .trim-region .trim-band      → accent-muted (10% oranje) + accent borders
> .trim-region .trim-handle    → accent fill
> .trim-band-label             → accent border + accent text + mono
> .playhead/.playhead-knob     → text-primary
> .tl-analyzer-mark            → border-strong + mono-tertiary label
> .ed-wave-toggle              → segmented mini (bg-elevated)
> .tl-minimap                  → bg-elevated + border-top
> .tl-mini-window              → accent border + accent-muted
> .tl-mini-trim                → accent fill
> .ed-trim-loading             → bg-base/75 + backdrop-blur
> .ed-trim-loading-bar         → accent fill
>
> # DRAWERS (text + track)
> .ed-text-drawer              → bg-elevated + border-left + shadow
> .ed-tx-head + .ed-tx-title   → border-bottom + 13px primary
> .ed-tx-close                 → v2-iconbutton 24×24
> .ed-tx-layers .ed-tx-layer   → kaartje (bg-elevated-2)
> .ed-tx-layers .ed-tx-layer.on → accent-muted + accent-border
> .ed-tx-add                   → dashed border, hover=accent
> .ed-tx-editor                → border-top + bg-base + padding 12
> .ed-tx-field label           → uppercase tertiary 11px
> .ed-tx-field textarea/input/select → v2-input (bg-elevated + border-subtle + radius 6)
> .ed-tx-field *:focus         → accent border
> .ed-tx-align button.on       → accent-muted + accent
> .ed-tx-bg-controls .bg-btn.on → accent-muted + accent
> .ed-tx-font-refresh          → v2-iconbutton mini 22×22
> .ed-track-drawer             → bg-elevated + border-left + shadow
> .ed-track-drawer button.primary → accent fill
> .ed-frame                    → pill mono 10.5px
> .ed-left-scroll scrollbar    → border-subtle thumb 10px
> ```
>
> ### Backup sessie 47
>
> - `static/index.html.pre-redesign-fase3.bak` (762.228 bytes, identiek aan
>   stand na sessie 46).
>   Rollback: `cp static/index.html.pre-redesign-fase3.bak static/index.html && ./start.sh`
>
> ### Verificatie sessie 47
>
> Statisch:
> - ✅ `node --check` op het 467.780 byte JS-blok: groen (JS-blok bytes-identiek aan sessie 46)
> - ✅ Python `html.parser` over hele file: 0 parse errors
> - ✅ Tag-balance delta vs backup: 0 voor div/span/aside/main/section/style/script/button/input
> - ✅ `<style>` / `</style>` count ongewijzigd (2/1)
> - ✅ 145 nieuwe `body.redesign-v2 #view-editor` selectors aanwezig
> - ✅ Alle 21 sub-component-clusters bevestigd via grep-count (.ed-top, .ed-tools .t, .cue-list .cue-row, .ratio-rail, .ed-right .tool-btn, .ed-export-menu, .tl-toolbar, .trim-region, .ed-text-drawer, .ed-track-drawer, etc.)
>
> Live geverifieerd via Chrome MCP (Sjuul's dev-server, set "Ediine x Ho_r Berlin", 33 clips):
>
> Met flag UIT:
> - ✅ Oude Omni DJ shell volledig terug (Omni DJ logo + Drop a set / Library / Clips 33 / Brand Stack / Settings / Cloud sync / PRO 6/10)
> - ✅ Dashboard in oude styling, geen residu
> - ✅ v2 OFF rechtsonder
>
> Met flag AAN:
> - ✅ V2-sidebar (MONO LABS · Pro plan / Clips / Brand / Social / Calendar / Insights + Settings + account-footer)
> - ✅ Dashboard in Fase 2 v2-stijl
> - ✅ Editor opent in v2-stijl:
>   - Crumbs "Clips › Ediine x Ho_r Berlin › Clip 01 · drop @ 00:04:13" + v2 back-button
>   - ed-tools-strip: Edit (accent-active), Style, Brand, Export selected (disabled), Export all
>   - Cue-points-panel: titel + meta "33 cues · 129 BPM (clip)", filter-chips als radius-16 pills, cue-rows als kaartjes met actieve-rij in accent-border
>   - Ratio-rail segmented control 9:16/1:1/16:9/4:5 (9:16 active)
>   - Tool-rail rechts: Trim/Text/Track + Export-pill onderaan
>   - Klik op Text → drawer opent rechts: header + close-btn + empty-state + dashed "+ Add text" knop
>   - Klik op "+ Add text" → per-layer editor verschijnt: layer-tegel in accent-border, TEXT/FONT/COLOUR/WEIGHT velden met uppercase tertiary labels en v2-inputs, swatches, SIZE-slider, BACKGROUND Off/On-toggle (Off in accent), X/Y-sliders, ALIGN-grid
>   - Caption-overlay zichtbaar op preview-video ("Caption here")
> - ✅ Timeline:
>   - Tl-toolbar: zoom −/fit/+, snap-toggle, prev/play(accent)/next, loop-toggle, time "00:00:00.00 / 00:00:16.73 · frame 0 · 129 BPM" met accent-cursor en frame-pill
>   - Ruler met seconden-labels in mono secondary
>   - Trim-region: accent-handles + duration-pill "16.7s" (accent border + tekst), EXTEND-knoppen aan beide kanten
>   - Waveform-band met WAVE/SPEC-segmented control rechtsboven
>   - Filmstrip onderaan
>
> ### Bestanden gewijzigd deze sessie
>
> - `dj-clip-cutter/static/index.html`:
>   - +~440 regels CSS (Fase 3 editor/timeline/drawers) vóór `</style>`
>   - Geen JS-aanrakingen
>   - Geen DOM-IDs hernoemd of toegevoegd
>
> ### Wat Sjuul nog moet doen (runtime-tests die niet via Chrome MCP gedekt zijn)
>
> 1. **Interactietest editor — flag AAN:**
>    - Klik Trim-knop → /api/slice draait, clip wordt opnieuw gerendered (geen styling-regressie op handles/playhead)
>    - Sleep IN-handle naar binnen → trim-band krimpt, label updatet
>    - Sleep OUT-handle voorbij rand → EXTEND-knop laadt extra audio
>    - Snap-toggle aan → grid verschijnt; sleep handle → snap werkt
>    - Loop-toggle aan → play loopt binnen in/out
>    - Wave/Spec toggle → schakelt naar spectrogram
>    - Mini-map: drag window om te pannen, klik buiten = jump
>    - Track-drawer: open via Track-knop, voeg keyframe toe, export vertical → kijk of accent-knoppen werken
>    - Brand-knop → Settings/Brand-Stack-view opent (krijgt zijn eigen Fase 4-restyle)
> 2. **Smoketests sessies 43+44 nog open:**
>    - Export single met rename → MP4 bevat captions + heet exact zoals getypt
>    - Export multi-clip × multi-ratio → queue-bar verschijnt
>    - Selectie-preview-balk onderaan editor werkt nog
>
> ### Bewust uit scope sessie 47
>
> - Modals (auth/upgrade/onboarding/Brand Stack) → **Fase 4**
> - Echte Social/Calendar/Insights features → **Fase 5**
> - PyInstaller rebuild naar .app/.dmg → **na Fase 4** (auth-modals zijn first-impression voor nieuwe users)
> - Track-drawer content-restyle (alleen shell + primary-button gestyled, panel-content krijgt aandacht zodra Sjuul de Track-flow gebruikt)
> - Lichte aanpassing aan oude amber-tokens in legacy-modus (we raken alleen v2 aan)
>
> ### Volgende sessie

> 1. Smoketests interactie editor + sessies 43/44 draaien
> 2. Als alles groen: starten met **Fase 4 — Modals + overige schermen**
>    - Auth-modals (login/signup/forgot/reset) → v2-stijl
>    - Upgrade-modal → v2-stijl
>    - Onboarding-wizard → v2-stijl
>    - Brand Stack modal → v2-stijl
> 3. Na akkoord Fase 4: PyInstaller rebuild → .app → .dmg
>    (procedure: zie `LESSONS-LEARNED.md` + `INSTALLER-RUNBOOK.md`)

---

## STATUS NA SESSIE 46 — REDESIGN FASE 2 (2026-05-26)

> **Dashboard / clips-grid in v2-stijl. CSS-only. Geen JS/backend wijzigingen.**
>
> ### Aanpak gekozen na inventarisatie
>
> Tijdens discovery bleek dat het bestaande markup-skelet uit
> `renderClipGrid()` (regel 7270) rijk genoeg is om met pure CSS naar de
> v2-look te brengen. Geen JS-aanrakingen nodig → **0% risico op functionele
> regressie** op hover-scrub, selectie, filmstrip-loader, inline editor,
> rename, export-menu, favourite-toggle.
>
> ### Beslissingen
>
> 1. **Type-pill boven thumbnail NIET toegevoegd** — backend kent buildup,
>    niet alleen drop, maar UI laat zien dat we historisch "Drops" als
>    label gebruiken; geen visuele toevoeging die verwarring kan geven.
> 2. **Filter-set blijft op huidige 4** (All / Drops / Favourites / Renamed).
>    Mockup-set (All/Drops/Build-ups/Vocals) is schijn-feature; "Build-ups"
>    en "Vocals" bestaan niet als classificatie in onze backend.
>    Alleen visuele restyle van de chips.
>
> ### Wat is gewijzigd
>
> **Bestand:** `dj-clip-cutter/static/index.html`
> - Regels 16.595 → 16.943 (+348)
> - Bytes 750.144 → 761.556 (+11.412)
> - Nieuw CSS-blok ingeprikt vóór `</style>` op regel ~3868
> - Blok-marker in code: `/* REDESIGN v2 — Fase 2 (2026-05-26) */`
>
> ### Selectors toegevoegd (alle scoped onder `body.redesign-v2`)
>
> ```
> .clip-pick .pick-head      → flex header met border-bottom
> #dash-subhead              → titel + meta links
> #dash-set-title / #dash-set-meta → typografie (Inter 15px + mono 11px)
> #dash-filters .chip        → mockup .filter-chip (radius 16, subtle border)
> #dash-filters .chip.on     → active state (bg-hover + border-strong)
> #dash-ratio-toggle         → segmented control (bg-elevated, radius 6)
> #dash-ratio-toggle .chip   → naadloze pill, .on krijgt bg-hover
> .clip-grid                 → grid auto-fill minmax(260px, 1fr) + gap 16px
> .clip-grid .clip           → kaart bg-elevated + border-subtle + radius 14
> .clip-grid .clip:hover     → border-strong + translateY(-1px)
> .clip-grid .clip.selected  → accent-border (oranje rand)
> .clip-grid .clip.fav       → zachte gouden accent-rand
> .clip-grid .clip .ph       → aspect-ratio 9/16, gradient #1A1A1D→#0F0F11
> .clip-grid.ratio-landscape .clip .ph → 16/9
> .clip-grid .clip .ph::before → decorative orange-halo + bottom-shadow
> .clip-grid .clip .ph .thumb-img / .hover-vid → cover-fit + z-index ordering
> .clip-grid .clip .select-toggle → rond top-left, opacity 0 → 1 op hover,
>                                  accent-fill bij selected
> .clip-grid .clip .ph .duration → bottom-right mono pill met backdrop-blur
> .clip-grid .clip .ph .cap → bottom-left caption-strip met backdrop-blur
> .clip-grid .clip .ph .unmute-pip → consistent gestyled
> .clip-grid .clip .dash-strip → 28px filmstrip, opacity 0.85
> .clip-grid .clip .info → padding + border-top + flex space-between
> .clip-grid .clip .info .l/.r/.mini-btn/.icon-mini/.info-div → consistente icon-buttons
> #export-sel-bar → bg-elevated + border-subtle + accent CTA
> #dash-clips-root .empty-state → dashed border + secondary text
> .dashboard .head .actions .btn → consistent met v2-tokens
> .clip-grid .clip .ce-panel → bg-elevated-2 + border-top
> ```
>
> ### Backup
>
> - `static/index.html.pre-redesign-fase2.bak` (750.144 bytes, identiek aan
>   stand na sessie 45).
>   Rollback: `cp static/index.html.pre-redesign-fase2.bak static/index.html && ./start.sh`
>
> ### Verificatie sessie 46
>
> - ✅ `node --check` op het 467.780 byte JS-blok: groen (JS-blok 218 bytes
>   groter dan sessie 45 door 1 micro-edit beneden)
> - ✅ Python `html.parser` over hele file: 0 parse errors
> - ✅ `<div>` open/close delta vs backup = 0
> - ✅ `<style>` / `</style>` count ongewijzigd
> - ✅ 30 nieuwe `body.redesign-v2 .clip-grid .clip` selectors aanwezig
> - ✅ 3 nieuwe `body.redesign-v2 #dash-filters .chip` selectors aanwezig
> - ✅ 4 nieuwe `body.redesign-v2 #dash-ratio-toggle` selectors aanwezig
> - ✅ v2-tokens-referenties verdubbeld
>
> ### Live geverifieerd via Chrome MCP (Sjuul's dev-server, set "Ediine x Ho_r Berlin", 33 clips)
>
> Tijdens de runtime-smoketest kwamen 2 bugs aan het licht die ik meteen
> heb gefixt — beide carry-over uit sessie 45:
>
> **Bug 1 — Mount-selector mist klasse `.app`** (sessie 45 carry-over)
> - `v2Mount()` (regel ~16814) gebruikte
>   `body > .view, body > #app, body > main` als selector. De oude Omni DJ
>   shell heeft echter klasse `.app` (geen ID). Resultaat: `v2-content-wrap`
>   bleef leeg, oude `.app` (5452px hoog) bleef body-level onder de v2-shell
>   prikken — de v2-sidebar overlapte met de oude sidebar.
> - **Fix:** selector aangevuld naar
>   `body > .view, body > #app, body > .app, body > main`. Inline comment
>   toegevoegd. Eén-regel-edit.
>
> **Bug 2 — Dubbele sidebar** (gevolg van bug 1 na fix)
> - Na het mounten van `.app` binnen `v2-content-wrap` werd de oude
>   `<aside id="sidebar" class="sidebar">` opnieuw zichtbaar in de
>   2-koloms grid van `.app`.
> - **Fix:** twee CSS-regels toegevoegd onder `body.redesign-v2`:
>   ```
>   body.redesign-v2 .v2-content-wrap > .app { grid-template-columns: 1fr !important; }
>   body.redesign-v2 .v2-content-wrap > .app > aside.sidebar { display: none !important; }
>   ```
>
> ### Smoketest-resultaten (alle groen)
>
> Met flag UIT:
> - ✅ Oude UI 100% intact (sidebar links: Omni DJ / Drop a set / Library /
>   Clips 33 / Brand Stack / Settings / Cloud sync / PRO 6/10 sets)
> - ✅ Pick-head, header, filter-chips, ratio-toggle in oude oranje-pill-stijl
> - ✅ Clip-cards in oude stijl, hover-preview werkt
>
> Met flag AAN:
> - ✅ V2-sidebar (MONO LABS · Pro plan / Clips actief / Brand / Social /
>   Calendar / Insights / Settings + account-footer)
> - ✅ Topbar met breadcrumb "Clips"
> - ✅ Pick-head + 33-clips-titel + meta (129 BPM · 55 min set)
> - ✅ Filter-chips als v2 radius-16 pills (All 33 / Drops (33) / Favourites (0)
>   / Renamed (0)), click op "Drops" → `activeFilter: drops` + chip krijgt
>   on-state
> - ✅ Ratio-toggle segmented control (9:16 actief), click op 16:9 →
>   `gridCls: clip-grid ratio-landscape`, cards switchen naar 16:9
> - ✅ Hover op clip-card → `is-hovering` class + select-toggle opacity 0→1
>   (rond cirkeltje links-boven)
> - ✅ Klik select-toggle → card krijgt `selected` class + accent-border +
>   checkmark-fill. `export-sel-bar` verschijnt bovenaan ("1 selected" + Cancel
>   + oranje Export 1). **Sessie 44 selectie-preview-balk** verschijnt
>   onderaan met tile-thumb + label + Clear-knop.
> - ✅ Klik op een clip-card body → oude Editor-view opent (heeft nog oude
>   styling, dat is correct — Fase 3 is voor Editor)
> - ✅ Cap-tekst (`drop · #1 · 00:04:13`) leesbaar binnen thumb, mono-font,
>   backdrop-blur pill
> - ✅ Duration-pill linksboven (`00:00:16`) met backdrop-blur
> - ✅ Filmstrip onder thumb in 16:9-modus (sessie 20 IntersectionObserver
>   lazy-load werkt)
> - ✅ Info-row onder card met start-time + ★ + Adjust + Download + → buttons
>   in v2-icon-button-stijl
> - ✅ Flag terug uit → oude UI weer compleet, geen residu
>
> ### Bestanden gewijzigd deze sessie
>
> - `dj-clip-cutter/static/index.html`:
>   - +348 regels CSS (Fase 2 grid + filters + ratio-toggle + cards) vóór `</style>`
>   - +4 regels JS-comment + 1-regel-fix in `v2Mount()` selector
>   - +5 regels CSS aan einde Fase 2-blok voor de oude-sidebar-suppressie
>
> ### Wat Sjuul nog moet doen (runtime-tests)
>
> 1. `./start.sh` — dev-server starten
> 2. **Smoketest Fase 2 — flag UIT:**
>    - Open http://127.0.0.1:5555
>    - App opent zoals altijd (oude UI) ✓
>    - Upload set → dashboard toont oude-stijl clip-cards ongewijzigd
>    - Hover-preview, selectie, favourite, Adjust-drawer, Export-menu,
>      Rename — alles werkt zoals voor sessie 46
> 3. **Smoketest Fase 2 — flag AAN:**
>    - Klik linksonder `v2 shell`-knopje (of in DevTools:
>      `localStorage.setItem('omniDjRedesignV2','1')` + reload)
>    - Sidebar verschijnt + clip-grid wordt automatisch v2-stijl
>    - Filter-chips (All/Drops/Favourites/Renamed) zijn nu radius-16 pills
>    - Ratio-toggle (9:16/16:9) is nu segmented control
>    - Clip-cards: donkere bg, subtle border, hover lift, ronde select-toggle
>      verschijnt op hover, duration-pill en caption rechtsonder/linksonder
>    - Selecteer een clip → border wordt oranje + select-toggle fill oranje
>    - Hover-scrub video werkt nog
>    - Adjust-knop opent inline editor onder de kaart
>    - Export-menu opent nog
>    - Klik op clip → editor opent
>    - Rename via rechtermuisknop op label werkt nog
> 4. **Switchen tussen flag aan/uit:**
>    - Klik nogmaals op `v2 shell` → terug naar oude UI, alles intact
>
> ### Bewust uit scope sessie 46
>
> - Editor / timeline polish → **Fase 3**
> - Modals herstijlen (auth, upgrade, onboarding) → **Fase 4**
> - Echte Social/Calendar/Insights features → **Fase 5**
> - PyInstaller rebuild naar .app/.dmg → **pas na Fase 3** (Editor is
>   langste interactie, daar maakt het visuele verschil het meeste uit)
> - Type-pill boven thumbnail (besloten weg te laten — geen Build-ups/Vocals)
>
> ### Volgende sessie

> 1. Smoketests draaien (v2-shell uit sessie 45 + v2-grid uit sessie 46 +
>    nog open 43+44 smoketests)
> 2. Als alles groen: starten met **Fase 3 — Editor / Timeline polish**
>    - Editor-shell + drawers (track/text/brand) krijgen v2-styling
>    - Knoppen-toolbar consistent met v2-buttons
>    - Waveform-rendering, BPM-detectie, trim-handles, /api/recut+/api/slice
>      blijven onaangeraakt
> 3. Na akkoord Fase 3: PyInstaller rebuild → .app → .dmg

---

---

## 📂 Bestandsstructuur van deze handover

Deze handover is op 2026-05-26 opgesplitst in drie bestanden om snel laadbaar te blijven:

- **`HANDOVER.md`** (dit bestand) — actieve handover: huidige status (sessie 40), recente sessies 27–39 ingedikt, openstaande prioriteiten, werkwijze
- **`HANDOVER-ARCHIVE.md`** — chronologisch archief van sessies 1–26 (lossless). Alleen raadplegen voor historische context
- **`LESSONS-LEARNED.md`** — terugkerende bugs, werkmanieren die werken, vaakgestelde vragen + canonieke antwoorden

**Backups van het origineel (322 KB, 80K tokens):** `HANDOVER.md.backup-2026-05-26` (naast origineel) en `.backups/HANDOVER-pre-compact-2026-05-26.md`.

---

## STATUS NA SESSIE 45 — REDESIGN FASE 1 (2026-05-26)

> **Premium dark-mode shell live achter feature-flag. Volledig non-destructief.**
> Geen backend wijzigingen. Sessie 43 + 44 code-side onveranderd.
>
> ### Aanleiding
>
> Sjuul wil de tool een premium look-and-feel geven (referenties: Supabase dark
> dashboard, Linear, Notion sidebar, opus.pro). Eerst is een
> mockup gebouwd (`clip-live-redesign-v2.html` in projectroot) — akkoord
> gekregen. Daarna split in 5 fases (`PLAN-REDESIGN-MIGRATION-2026-05-26.md`).
> Sessie 45 = Fase 1.
>
> ### Design-richting (vastgelegd, niet meer ter discussie)
>
> - **Dark-mode first** (light komt later)
> - **Warm cream tekst** (#F5F2EC) op near-black (#0E0E0F)
> - **Oranje accent** (#D97742) heel spaarzaam — géén glow, géén gradient
> - **Sidebar:** Supabase-stijl shell met workspace-switcher boven,
>   TIMA-stijl categorie-groepen in het midden, settings-footer onderin
> - **Sidebar-namen:** Clips · Brand · Social · Calendar · Insights
> - **Toekomst-ready voor:** multi-artist (workspace-switcher), Content
>   Calendar (Postiz), Ads (Intellijend model), Brand Stack uitbreiden
>
> ### ✅ Fase 1 — App shell (sidebar + topbar + design tokens)
>
> **Strategie:** non-destructief feature-flag. Alle v2-CSS/HTML/JS is
> volledig gescoped onder `body.redesign-v2`. Standaard staat de flag uit
> en is de tool 100% identiek aan vóór sessie 45. Bij activeren mount de
> JS de bestaande `.view`-containers in de nieuwe `.v2-content-wrap` —
> géén DOM-IDs hernoemd, géén handlers vervangen.
>
> **Feature-flag aan/uit:**
> - Toggle linksonder in de UI: knop `v2 shell` (klein, met label "ON"/"OFF")
> - Of via DevTools: `localStorage.setItem('omniDjRedesignV2','1')` + reload
> - Of uitzetten: `localStorage.setItem('omniDjRedesignV2','0')` + reload
>
> **CSS toegevoegd (`static/index.html` ~regel 3624, vóór `</style>`):**
> - 16 v2-tokens (`--v2-bg-base`, `--v2-text-primary`, `--v2-accent` etc.),
>   allemaal alleen actief onder `body.redesign-v2`
> - `.v2-app` grid (sidebar 240px / main 1fr, fixed `inset:0` over de hele
>   viewport)
> - `.v2-sidebar` met `.v2-workspace`, `.v2-nav`, `.v2-sidebar-footer`
> - `.v2-nav-item` met active-state (oranje 2px linker-rand + oranje tekst
>   + `--v2-accent-muted` background)
> - `.v2-main` met `.v2-topbar` (52px, breadcrumb links) + `.v2-content-wrap`
> - `.v2-placeholder` voor Social/Calendar/Insights (nog geen feature)
> - `.v2-hide-when-on` helper voor oude chrome
> - Responsive: ≤768px collapse de sidebar naar 64px
>
> **HTML toegevoegd (direct na `<body>`, vóór auth-overlay):**
> - `<div class="v2-app" id="v2App" style="display:none">` — root shell
> - Sidebar met workspace-button ("MONO LABS · Pro plan"), 5 nav-items
>   (Clips/Brand/Social/Calendar/Insights), settings-footer (Settings-knop
>   + account-tegel met initialen/naam/email)
> - Topbar met breadcrumb (`#v2Breadcrumb`)
> - Content-wrap (`#v2ContentWrap`) — leeg bij mount, JS verplaatst views
>
> **JS toegevoegd (vóór `</script>`, IIFE `v2Init`):**
> - `isV2On()` / `setV2(on)` — flag-state via localStorage
> - `v2Mount()` — verplaatst eenmalig alle `body > .view, body > #app,
>   body > main` (behalve `#auth-overlay`, de v2-app zelf, en de flag-knop)
>   in `.v2-content-wrap`. Markeert via `dataset.mounted='1'`. Voegt
>   `body.redesign-v2` toe. Roept `v2HydrateAccount()` aan voor
>   footer-tegel. Synct active-nav via `v2SyncActiveNav()`.
> - `v2Unmount()` — verplaatst views terug naar body, verwijdert
>   `body.redesign-v2`, verbergt de v2-app. Volledig reversibel.
> - `v2SyncActiveNav()` — mapt `STATE.view` (`dashboard`/`settings`/etc.)
>   naar bijbehorende nav-item, kleurt die als active.
> - `v2ShowPlaceholder(key)` — toont een placeholder-card voor schermen die
>   nog niet bestaan (Social, Calendar, Insights).
> - `v2HydrateAccount()` — leest `window.AUTH` of `STATE.user`, vult
>   naam/email/initialen in de footer-tegel.
> - Click-handler op `[data-v2nav]` — roept `window.switchView(targetView)`
>   aan voor bestaande screens, of `v2ShowPlaceholder()` voor nieuwe.
> - Toggle-handler op `#v2FlagToggle` — flipt flag + paint knop.
> - Boot-hook op `DOMContentLoaded` — als flag aan, mount automatisch.
>
> **Sidebar-naar-view mapping (`NAV_MAP` in JS):**
> ```
> clips    → switchView('dashboard')
> brand    → switchView('settings')   (Brand Stack zit in settings)
> social   → placeholder
> calendar → placeholder
> insights → placeholder
> settings → switchView('settings')   (footer-knop)
> ```
>
> ### Bestanden gewijzigd
>
> - `static/index.html` — 16.096 → 16.595 regels (+499). Bytes 728.985 → 750.144.
>
> ### Backup sessie 45
>
> - `static/index.html.pre-redesign-v2.bak` (728.985 bytes, identiek aan
>   stand na sessie 44). Rollback: `cp static/index.html.pre-redesign-v2.bak
>   static/index.html && ./start.sh`.
>
> ### Verificatie sessie 45
>
> - ✅ `node --check` op het hele 467KB JS-blok: groen
> - ✅ Python `html.parser` over hele file: 0 parse errors
> - ✅ Tag-balance check: géén nieuwe onbalans toegevoegd (de bestaande
>   +1 `<div>` delta zat al in het origineel, vermoedelijk in een
>   commentaar of template-literal)
> - ✅ Geen Jinja-tokens in `static/index.html` (wordt direct geserveerd
>   via `send_from_directory`, geen render_template — `app.py:1121`)
> - ✅ Alle v2-DOM-IDs aanwezig: `#v2App`, `#v2ContentWrap`,
>   `#v2Breadcrumb`, `#v2FlagToggle`, `#v2AccountName/Email/Avatar`
> - ✅ 5 nav-buttons in sidebar + 1 settings-knop + 1 account-knop in
>   footer, allemaal met `data-v2nav` attribuut
>
> ### Wat Sjuul nog moet doen (runtime-tests)
>
> 1. `./start.sh` — dev-server starten
> 2. **Smoketest v2-shell:**
>    - App opent zoals altijd (flag uit, oude UI) ✓
>    - Klik linksonder op `v2 shell`-knopje → sidebar verschijnt, oude
>      content zit nu rechts in de wrap
>    - Klik Clips in sidebar → dashboard zichtbaar (active nav-item oranje)
>    - Klik Brand → Brand Stack / settings view
>    - Klik Social/Calendar/Insights → placeholder-cards
>    - Klik Settings (footer) → settings-view
>    - Klik nogmaals op `v2 shell` → terug naar oude UI, alles werkt nog
> 3. **Smoketests sessie 43 + 44** (gecombineerd, ~45min) — staan nog
>    open uit vorige sessies. Doe deze nu in v2-mode, dat scheelt later
>    dubbel werk:
>    - Upload nieuwe set → Processing → Dashboard met clips ✓
>    - Editor opent, trim werkt, text-layer toevoegen ✓
>    - Export single clip met rename → MP4 bevat captions ✓
>    - Export multi-clip met meerdere ratios → folder-picker werkt ✓
>    - Selectie-preview-balk verschijnt onderaan met thumbs + hover-scrub ✓
>
> ### Bewust uit scope sessie 45
>
> - Dashboard/clips-grid herstijlen → **Fase 2**
> - Editor/timeline polish → **Fase 3**
> - Modals herstijlen → **Fase 4**
> - Echte Social/Calendar/Insights features → **Fase 5**
> - PyInstaller rebuild naar .app/.dmg → **pas na Fase 2** (anders ziet
>   een tester nieuwe sidebar maar oude content binnen = halfslachtig)
>
> ### Volgende sessie

> 1. Smoketests draaien (v2-shell + 43 + 44 gecombineerd)
> 2. Als alles groen: starten met **Fase 2 — Dashboard/Clips-grid in v2-stijl**
>    - `renderDashboard()` produceert v2-style clip-cards
>    - Filter-chips boven grid in v2-stijl
>    - Aspect-ratio toggle (9:16 / 16:9)
>    - Mockup-referentie: zie clips-grid in `clip-live-redesign-v2.html`
> 3. Na akkoord Fase 2: PyInstaller rebuild → .app → .dmg
>    (procedure: zie `LESSONS-LEARNED.md` + `INSTALLER-RUNBOOK.md`)

---

## STATUS NA SESSIE 44 (2026-05-26)

> **Onderdeel 8 uit `SESSIE43-EXPORT-PIPELINE-PLAN.md` code-side klaar.**
> Volledig frontend-only — geen backend wijzigingen.
>
> ### ✅ Onderdeel 8 — Selectie-preview-balk in timeline-editor
>
> **Wat:** Horizontale balk onderaan scherm die verschijnt zodra ≥1 clip is
> aangevinkt (vinkje in dashboard-card of cue-row in editor). Verdwijnt
> zacht via CSS transform-animatie zodra de selectie leeg is.
>
> **HTML (`static/index.html` ~regel 5210):**
> ```
> #selection-preview-bar
>   .selbar-inner
>     .selbar-meta (count + "selected" label)
>     .selbar-tiles (horizontaal scrollbaar)
>     .selbar-actions (Clear-knop)
> ```
>
> **CSS (~regel 539):**
> - `position:fixed; bottom:0`; `transform:translateY(100%)` → off-screen.
> - `.on` class → `translateY(0)` met 0.22s ease-out transitie.
> - `body.has-export-queue #selection-preview-bar.on` → `translateY(-72px)`
>   zodat de export-queue-bar (eigen z:9000) niet overlapt. `body`-class wordt
>   gezet door `showExportQueueBar/hideExportQueueBar`.
> - Tile-grid horizontal-scroll met amber thin scrollbar.
> - Hover op tile → ×-knop verschijnt (`opacity 0 → 1`).
> - `is-scrubbing` class fade't de scrub-video over de poster heen.
>
> **JS (~regel 7600 e.v.):**
> - `_renderSelectionBar()` — idempotent: bouwt/diff't tiles op basis van
>   `STATE.selectedClips`. Hergebruikt bestaande tiles via een Map-cache
>   zodat hover-scrub state niet flikkert tussen renders.
> - `_buildSelbarTile(idx, clip)` — bouwt één tile DOM element:
>   - 120×75 thumbnail wrap (16:10 aspect-ratio, `object-fit:cover`)
>   - Thumb via `/api/thumbnail/<job>/<file>` met `withAuth` (cross-account
>     security uit sessie 28). Fallback: label-tekst tegen donker vlak.
>   - ×-knop top-right, klik → `toggleClipSelect(idx, null)`.
>   - Meta-rij: label (`custom_label` of `${kind} · #${index}`) + tijdmarker
>     `@ MM:SS` (of `H:MM:SS` voor sets ≥1u via `_fmtSelbarTime`).
>   - Tile-click (buiten ×) → `selectClipInEditor/setSelectedClipIdx` als die
>     bestaat. Pure visuele hint nu — geen backend call.
> - Hook: `updateExportSelBar()` (al de single source of truth voor selectie-
>   UI updates) roept aan het eind `_renderSelectionBar()` aan. Alle paden
>   die de selectie wijzigen (toggleClipSelect / clearSelection / cue-row
>   buttons / dashboard select-toggle) gaan hierdoor.
>
> **Hover-scrub:**
> - `_attachSelbarScrub(tile, clip)` registreert mouseenter/leave listeners
>   en stasht `scrubSrc` op `tile.dataset`. Video element wordt pas op
>   eerste hover gecreëerd (lazy).
> - `_selbarScrubStart` maakt `<video.selbar-scrub>` met `preload="metadata"`
>   + `playsInline + muted + disablePictureInPicture`. Bij `loadedmetadata`
>   doet hij 4 `currentTime` seeks gespreid over 1.2s — geeft een mini-
>   teaser zonder de hele clip te streamen.
> - `_selbarScrubStop` cleared de interval, pauseert de video en doet
>   `video.removeAttribute('src')` + `.load()` om de decoder vrij te geven
>   (memory cleanup voor sets met 20+ geselecteerde clips).
> - Bij selectie wegnemen (×, Clear, of leeg na export): `_detachSelbarScrub`
>   verwijdert listeners en cleart de video.
>
> **setActiveJobId fix:** bij job-wissel wordt nu `clearSelection()` aangeroepen
> zodat een oude set z'n stale selectie niet meeneemt naar een nieuwe set.
> Voorkomt dat de balk tiles toont uit een job-id die niet meer in
> `STATE.clips` zit.
>
> **Bewust uit scope deze sessie:**
> - Drag-to-reorder tiles (zou volgorde van export-queue beïnvloeden — apart
>   traject met backend `clip_indices` reorder logica).
> - Persistente selectie tussen page-reloads (selectie is sessie-lokaal in
>   `STATE.selectedClips`, niet in localStorage).
> - Hover-scrub volume / unmute knop (tile-thumb is intentioneel muted).
>
> ### Verificatie sessie 44
>
> ✅ `node --check` op het 460.8KB JS-blok in `static/index.html` OK
> ✅ Alle 4 nieuwe DOM-IDs aanwezig (`#selection-preview-bar`, `#selbar-clear`,
>    `#selbar-count`, `#selbar-tiles`)
> ✅ 7 nieuwe JS-functies geëxporteerd op `window` (`_renderSelectionBar`,
>    `_buildSelbarTile`, `_attachSelbarScrub`, `_detachSelbarScrub`,
>    `_selbarScrubStart`, `_selbarScrubStop`, `_fmtSelbarTime`)
>
> Wat Sjuul nog moet doen (combineer met smoketests sessie 43):
> 1. Dev-server herstarten (`./start.sh`)
> 2. Smoketests sessie 44:
>    - 0 selectie → bar onzichtbaar
>    - 1 clip aanvinken (dashboard óf cue-row) → bar slidet omhoog met 1 tile
>    - Deselect via × op tile → tile weg, dashboard checkmark ook weg
>    - Selecteer 5 clips → bar toont 5 tiles, count = 5
>    - 20+ clips → balk scrollt horizontaal, geen layout-overflow
>    - Hover op tile → ×-knop verschijnt + thumb scrubt 3-4 frames door clip
>    - Clear-knop → bar slidet weg
>    - Tijdens actieve queue-bar export → selectie-balk schuift ~72px omhoog
>    - Wissel naar andere set → selectie wordt vanzelf gecleared
>
> ### Backup sessie 44
>
> - `static/index.html.pre-sessie44.bak` (712.5KB)

---

## STATUS NA SESSIE 43a + 43b (2026-05-26)

> **Alle 7 onderdelen uit `SESSIE43-EXPORT-PIPELINE-PLAN.md` code-side klaar.**
> Sessie 44 (selectie-balk) bewust uitgesteld op verzoek van Sjuul.
>
> ### ✅ Onderdeel 1 — Auto-bake captions in export (BLOCKER opgelost)
>
> Root cause: `_run_export_job` gebruikte bestaande `clip['files']` zonder
> text_overlays.json of brand-assets te lezen, dus exports van clips met
> captions kwamen kaal uit. Trim deed wel layer-injection via `/api/recut`,
> maar Export sloeg dat over.
>
> **Backend fix:**
> - Nieuwe `slice_clip()` in `cutter.py` ~regel 1875: lichtgewicht trim-only
>   variant van `recut_clip` zonder text/logo/watermark inbakken (track-mode
>   keyframes wel meegenomen — geometrische crop, geen overlay).
> - Nieuwe `/api/slice/<job_id>` endpoint in `app.py` ~regel 4329: zelfde
>   signature als `/api/recut` zodat frontend simpel kan switchen.
> - `_detect_layers_for_clip()` (`app.py`) check per clip of er text_overlays,
>   logo, watermark of tracking aanwezig zijn (skip-fast-path voor kale clips).
> - `_prebake_clip_for_export()` (`app.py`) bakt overlays + branding in naar
>   tmp-paden onder `output/<job>/_baked_for_export/` vóór de codec-conversie.
>   Roept `recut_clip` aan met huidige clip-grenzen, respecteert caption-toggle
>   uit modal (kopieert `text_overlays.json` óf schrijft lege overlays als
>   captions=off). Tmp-dir wordt na succesvolle export opgeruimd.
> - `_run_export_job._process` integreert pre-bake: als `needs_prebake`, swap
>   baked-sources in als source voor `export_clip_with_settings`. Anders snelle
>   pad via bestaande `clip['files']`.
>
> **Frontend fix:**
> - `editorTrimAtPlayhead()` (`static/index.html` ~regel 9269): `/api/recut` →
>   `/api/slice`. Trim doet vanaf nu écht alleen slicen, overlays blijven als
>   WYSIWYG live-laag in de editor, worden pas bij Export ingebakken.
>
> ### ✅ Onderdeel 2 — Rename-veld in export-modal
>
> - Nieuwe `<input id="exs-rename">` boven codec-select. Alleen zichtbaar bij
>   single-clip flow (via `opts.singleClip` in `pickExportSettings(label, opts)`).
> - Multi-clip + Export-all: rename-row verborgen.
> - Bij OK: `settings.renameTo` wordt als `labels: {"<index>": "Naam"}` mee
>   gestuurd naar `/api/export`.
> - Backend `_run_export_job._process` past per-clip `custom_label` aan op een
>   kopie van het clip-object (`clip_for_export = dict(clip)`) — origineel
>   blijft in jobs-snapshot tot user op /api/rename de naam permanent maakt.
> - Editor "Export"-knop + Dashboard "Export selected" met N=1 sturen nu
>   `{ singleClip: clip }` mee.
>
> ### ✅ Onderdeel 3 — Schonere filenames + sidecar JSON
>
> - `_build_export_filename` levert nu schone namen op: `Drop_3.mp4` (9:16 +
>   match-source), `Drop_3_landscape.mp4` (16:9), `Drop_3_h265.mp4` (codec
>   override). Geen `__clip{NN}__{aspect}__{codec}` ruis meer in Finder.
> - `_write_export_sidecar` schrijft `<filename>.meta.json` náást elk export-
>   bestand met `{clip_index, aspect, codec, label, written_at, schema}`.
> - `/api/exports` parser (app.py ~regel 5826): probeert eerst sidecar JSON,
>   valt terug op `__clip<NN>__` regex (sessie 22+ exports) en daarna op
>   `_clip<NN>_` regex (pre-sessie 22). Schone namen zonder suffix worden
>   gemapped op 9:16 (de default-aspect) of via `_landscape`/`_square`/`_portrait`
>   detectie. Library blijft dus zichtbaar voor álle bestaande exports.
> - `/api/exports/<job_id>/<filename>` DELETE ruimt nu ook de sidecar JSON op.
> - `_build_export_filename_legacy` blijft beschikbaar als fallback maar wordt
>   niet aangeroepen — alleen voor documentatie van het oude patroon.
>
> ### ✅ Onderdeel 4 — Visuele ratio-tiles (multi-select)
>
> - 4 tegels (9:16 / 16:9 / 1:1 / 4:5) met inline SVG rechthoek-iconen in
>   `#exs-ratio-grid`. Multi-select via `<input type="checkbox">` met visuele
>   `is-checked` class (amber border + checkmark dot).
> - Backend mapping: `9:16 + 4:5` → `vertical`, `16:9` → `landscape`, `1:1` →
>   `vertical` (square als post-crop op vertical — backend kent in v1 alleen
>   landscape/vertical formats; 1:1 en 4:5 worden in een follow-up sessie
>   echt aparte aspect_filter keys).
> - Default = 9:16, last-used persist in `localStorage['omniDj.exportSettings'].ratios`.
> - 0 tiles aangevinkt → OK-knop disabled + tooltip "Selecteer minstens één formaat".
>
> ### ✅ Onderdeel 5 — Caption + watermark toggles met inline upload
>
> - Twee iOS-stijl switches in `#exs-toggle-captions` + `#exs-toggle-watermark`.
> - Caption-toggle default **aan** (sluit aan bij Onderdeel 1 auto-bake).
> - Watermark-toggle default **aan** als `STATE.brandKit.watermark.file`
>   bestaat, anders **uit**.
> - **Inline upload-flow:** als watermark-toggle aan staat én er nog geen
>   watermark in brand-kit is, verschijnt `#exs-watermark-upload` panel. Klik
>   op "Watermark kiezen…" → `/api/pick-file` (native picker) → POST naar
>   `/api/brand-kit/watermark` met JSON `{path: "/abs/path.png"}`.
> - **Backend (`app.py` regel 2819):** `upload_brand_watermark` accepteert nu
>   twee modes — multipart-upload (legacy, brand-kit panel) én JSON `{path}`
>   (sessie 43b inline flow). JSON-mode doet magic-byte check, size-cap, en
>   `shutil.copy2` naar `BRAND_WATERMARK_DIR`.
>
> ### ✅ Onderdeel 6 — Direct-to-folder met user-home whitelist
>
> - `#exs-folder-row` met truncated pad-display + "Kies map…" knop + "Reset"
>   knop. `~`-prefix replace voor leesbaarheid.
> - localStorage `clipLive.lastExportDir` voor sticky keuze tussen sessies.
> - `/api/pick-folder` bestond al uit sessie 39 — bewust hergebruikt.
> - **Backend security (`app.py` ~regel 6018):** nieuwe whitelist check op
>   `output_dir`. `os.path.realpath` van target vergelijken met realpath van
>   `os.path.expanduser('~')`. Target moet `== home OR startswith(home + sep)`.
>   Voorkomt dat exports in `/etc`, `/System`, `/Library` belanden. Geeft een
>   duidelijke 400 error "Voor de veiligheid mag de export-map alleen binnen
>   je gebruikersmap liggen".
>
> ### ✅ Onderdeel 7 — Export-queue + globale loading bar
>
> - `#export-queue-bar` fixed onderaan scherm, `display:none` bij 0 jobs.
> - Verschijnt automatisch als `totalJobs > 1` OR `aspects.length > 1` (multi-
>   clip × multi-ratio). Single-clip + single-ratio gebruikt nog de bestaande
>   `#export-pill`.
> - Toont "Exporting X/Y · Z%" + horizontale progress bar + Cancel-knop.
> - `updateExportQueueBar(done, total, failed, label)` wordt door
>   `pollExportStatus` aangeroepen elke 1.5s.
> - Cancel-knop stopt alleen het pollen (soft-cancel — geen abort-endpoint
>   in MVP; lopende ffmpeg-jobs ronden achtergrond af).
> - **Backend keuze:** Optie A (sequentieel via bestaande `EXPORT_MAX_PARALLEL`
>   ThreadPoolExecutor — `_run_export_job` is unchanged). Optie B (parallelle
>   workers met semafoor) uitgesteld naar follow-up sessie zoals afgesproken.
>
> ### Backend cfg-validatie uitgebreid
>
> `/api/export` accepteert nu 3 nieuwe velden:
> - `overlays: {captions, watermark, logo}` — alle bool. Default = alles aan.
>   Onbekende keys negeren. Non-dict → 400 `bad_overlays`.
> - `labels: {"<index>": "Naam"}` — values gecapt op 200 chars, niet-strings
>   genegeerd. Non-dict → 400 `bad_labels`.
> - `output_dir` — nu mét user-home whitelist (zie Onderdeel 6).
>
> Geen wijziging aan SSE/status-endpoint nodig — frontend leest dezelfde
> `items[]` shape, queue-bar berekent done/total client-side.
>
> ### Verificatie sessie 43a + 43b
>
> ✅ `python3 -m py_compile app.py` OK
> ✅ `python3 -m py_compile cutter.py` OK
> ✅ `python3 -c "import cutter; assert hasattr(cutter, 'slice_clip')"` OK
> ✅ `node --check` op het 449.7KB JS-blok in `static/index.html` OK
> ✅ Alle nieuwe modal-IDs aanwezig in DOM (23 exs-* + 4 exqb-* IDs).
>
> Wat Sjuul nog moet doen:
> 1. Dev-server herstarten (`./start.sh`)
> 2. Smoketests (zie `LESSONS-LEARNED.md` voor patronen):
>    - Clip met text-layer → Trim → mp4 ververst MAAR ZONDER tekst (alleen geslicet)
>    - Clip met text-layer → Export → mp4 op disk HEEFT tekst
>    - Rename in modal → mp4 op disk heet exact zoals getypt
>    - Bestandsnaam in Finder = "Drop_3.mp4" (zonder __clip__ ruis)
>    - Watermark toggle in modal werkt zonder brand-kit (inline upload-flow)
>    - Folder buiten `~` → 400 error in toast
>    - 2 clips × 2 ratios = 4 jobs → globale queue bar verschijnt
> 3. Pas bij groen alles → rebuild .app via `bash build_macos.sh dmg`
>
> ### Backups sessie 43a + 43b
>
> - `app.py.pre-sessie43-autobake.bak` (255.7KB)
> - `cutter.py.pre-sessie43-autobake.bak` (89.6KB)
> - `static/index.html.pre-sessie43-autobake.bak` (688.6KB)
>
> ### Bewust uit scope deze sessie
>
> - **Sessie 44 — Selectie-preview-balk** in timeline-editor (Onderdeel 8).
>   Verschoven naar aparte sessie zoals Sjuul aangaf bij start.
> - **1:1 en 4:5 als echte aspect-keys** in backend. Nu mapped op
>   vertical/landscape. Volgende sessie: aparte aspect-filter waarden +
>   crop-logica in `cutter.cut_clip_vertical` / `cut_clip_landscape`.
> - **Optie B parallel export-queue** (apart traject, zie plan).
> - **Export-queue Cancel = hard abort** (vereist subprocess-handle bijhouden,
>   complexer dan MVP toelaat).

---

## STATUS NA CONTENT CALENDAR PLAN (2026-05-26)

> **Planning-only sessie, geen code aangeraakt.** Sjuul vroeg om uitwerking
> van Content Calendar + Multi-artist workspaces + Ads-management in Omni DJ.
> Plan-document `PLAN-CONTENT-CALENDAR-2026-05-26.md` opgesteld na onderzoek
> naar Postiz (publishing-laag), DJ-tool businessmodellen en Meta/TikTok/Google
> Ads API-vereisten.
>
> ### Wat het plan voorstelt — 6 fasen + research-fase
>
> **Fase 1 — Multi-tenant fundament (3–4 wkn dev):**
> - Migratie 004+005+006: `workspaces` + `workspace_members` + `workspace_id`
>   op alle resource-tabellen
> - Data-migratie: voor elke bestaande user 1 default workspace aanmaken
> - Backend + frontend workspace-switcher (zoals Slack)
> - `profiles.max_workspaces` voor tier-grenzen
>
> **Fase 2 — Content Calendar UI (2–3 wkn dev):**
> - Migratie 007: `scheduled_posts` tabel
> - Maand/week-view kalender, drag-to-reschedule
> - "Plan in Calendar"-knop in sessie 43b export-modal
> - Drafts-systeem (publishen pas in Fase 3)
>
> **Fase 3 — Postiz publishing (3–4 wkn dev):**
> - Migratie 008: `social_accounts` tabel
> - Postiz Cloud + Public API + OAuth2 Developer App
> - Per workspace 1 Postiz-org (multi-tenant workaround voor open issue #975)
> - Upload + schedule via Postiz, autopublish + safety-cap
>
> **Fase 4 — Polish + Mobile companion (4+ wkn):**
> - Approval-flow, watch-folder + auto-draft, Ollama-captions
> - Mobile push voor approve-flow
>
> **Fase 4a — Ads research (2–3 wkn research, geen dev):**
> - Geld-flow-vraag: Model A (agency) vs. B (PSP-vergunning) vs. C (Stripe Connect)
> - NL-jurist + fiscalist (~€500–€1.500)
> - Meta + TikTok reseller-policy onderzoek
> - **Dan pas** Meta Business Verification + TikTok For Business starten
>
> **Fase 5+6+7 — Ads-platform (was prioriteit in v1.0, verschoven naar einde):**
> - Meta Ads orchestrator + TikTok Ads + later Google
> - Mix-en-matchen-budget voor managers (per Sjuul-wens)
>
> ### Beslissingen vastgelegd in plan v1.1
>
> 1. **Postiz Cloud akkoord** — geen self-host in v1
>    - Tool blijft 100% lokaal tot user op "Connect TikTok/IG" of "Plan in
>      Calendar" klikt — pas dan online
>    - MP4 + caption gaan naar Postiz Cloud op moment van plannen (anders kan
>      Postiz niet om 19:00 publishen als laptop dicht is)
>    - Studio-tier krijgt opt-out: manual export only, geen Postiz-koppeling
> 2. **Ads-systeem allerlaatst bouwen** — vereist meer research
>    - Sjuul wil geld via Omni DJ (mix-en-matchen budget tussen klant-accounts)
>    - Dat raakt PSP-vergunning of agency-of-record-constructie — apart traject
>    - Meta/TikTok verificaties NIET nu starten (kan wachten tot Fase 4a)
> 3. **Pricing geparkeerd** — Sjuul wil nog niet vastleggen
>    - Onderzoek-data (Soundcharts/Chartmetric/Beatchain) blijft in plan als ref
>    - Geen Stripe-products aanmaken, geen pricing-page updaten
>
> ### Totale werk-schatting (v1.1)
>
> - **v1 (Fase 1–4, zonder ads):** 13–15 weken dev = 3–3,5 maand
> - **v2 (Fase 1–7, inclusief ads):** 28–35 weken dev = 7–9 maanden + reviews
>
> Aanbeveling: launch v1 eerst als paid product. Ads erbij in v2 zodra
> research klaar is.
>
> ### Niets gebouwd, geen migraties uitgevoerd
>
> Deze sessie was puur planning. Beslissing-uitvoering pas na sessie 43 +
> omnidj.com + Stripe live. **Volgorde blijft:** 43a → 43b → 44 → Cloudflare
> DNS → Stripe live → DAN Fase 1 (multi-tenant).
>
> ### Memory-entries toegevoegd
>
> - `project_content_calendar_plan.md` — pointer naar plan v1.1
> - MEMORY.md index bijgewerkt

---

## STATUS NA SESSIE 43 VOORBEREIDING (2026-05-26)

> **Planning-only sessie, geen code aangeraakt.** Sjuul vroeg om twee nieuwe
> features bovenop het bestaande sessie 43 plan:
>
> 1. **Selectie-preview-balk in timeline-editor** — horizontale balk onderaan
>    die verschijnt bij ≥1 geselecteerde clip. Per clip: mini-thumb, naam,
>    tijdmarker (`@ 12:34`), hover-scrub (3-4 frames), hover-`×` om uit
>    export-batch te halen.
> 2. **Visuele resolutie-tiles in export-modal** — aanvinkbare iconen
>    (9:16 / 16:9 / 1:1 / 4:5) i.p.v. dropdown, multi-select.
>
> Aanvullend tijdens gesprek geadopteerd:
> - **Caption-toggle** + **Watermark-toggle** in export-modal (los van Brand Kit).
>   Watermark-toggle heeft inline upload-flow als nog geen watermark ingesteld.
> - **Direct-to-folder** met whitelist (user-home subfolders only).
> - **Export-queue + horizontale loading bar** onderaan scherm bij multi-clip
>   × multi-ratio exports. **Optie A (sequentieel) gekozen voor MVP**; Optie B
>   (parallelle workers) uitgesteld naar latere sessie.
>
> ### Plan-document uitgebreid 3 → 8 onderdelen, en gesplitst
>
> `SESSIE43-EXPORT-PIPELINE-PLAN.md` heeft nu:
>
> **Sessie 43a (~4-4,5u) — beta-blocker fix, MUST DO FIRST:**
> - Onderdeel 1: auto-bake captions in `_run_export_job` via nieuwe `/api/slice`
>   endpoint + bestaande `_recut_with_layers` als pre-bake step
> - Onderdeel 2: rename-veld in `pickExportSettings` modal (single-clip only)
> - Onderdeel 3: sidecar `.meta.json` per export, schone bestandsnamen op disk
>   (weg met `__clip__` token), backward-compat regex blijft werken
>
> **Sessie 43b (~5,5-6u) — modal-redesign, NA 43a:**
> - Onderdeel 4: visuele ratio-tiles (9:16/16:9/1:1/4:5) multi-select
> - Onderdeel 5: caption-toggle + watermark-toggle met inline upload-flow
>   (hergebruikt bestaande `/api/brand-kit/watermark` endpoint uit sessie 31)
> - Onderdeel 6: direct-to-folder, `/api/pick-file?type=folder` uitbreiding,
>   whitelist `~/`, `~/Desktop`, `~/Documents`, `~/Downloads`, `~/Movies` + children
> - Onderdeel 7: export-queue + globale loading bar (Optie A sequentieel)
>
> **Sessie 44 (~3-4u) — frontend-only, NA 43b:**
> - Onderdeel 8: selectie-preview-balk in timeline-editor
>
> ### Beslissingen vastgelegd in plan
>
> - **Optie A (sequentieel) voor MVP** export-queue; Optie B parallel later
> - **Whitelist user-home** voor folder-picker (geen system-folders)
> - **Caption-toggle default aan** (sluit aan bij auto-bake fix)
> - **Watermark inline upload** = modal blijft open, file-picker via bestaande
>   `/api/pick-file`, POST naar bestaande `/api/brand-kit/watermark`
> - **Rename-veld alleen single-clip flow** (multi-clip krijgt geen veld)
>
> ### Niets gebouwd, geen backups gemaakt
>
> Deze sessie was puur planning + plan-document. Code-aanrakingen pas in
> sessie 43a in nieuwe chat. Start daar met `LESSONS-LEARNED.md` raadplegen
> en bestaande backups archiveren als routine.
>
> ### Memory-entries toegevoegd
>
> - `project_sessie43_split_plan.md` — split-rationale + sessie-volgorde
> - MEMORY.md index bijgewerkt

---

## STATUS NA SESSIE 42 (2026-05-26)

> **Wat gedaan deze sessie — Fase 5 grotendeels klaar + UI cleanup:**
>
> ### ✅ Color wheels voor text + background (Fase 5 / C+D)
>
> Eigen mini-picker `OmniDJPicker` ingebouwd, **geen externe library** (Sjuul wilde geen Coloris dependency in frontend). HSV-canvas + hue-strip + hex-input + optionele opacity-slider. ~280 regels JS/CSS inline in `static/index.html`.
>
> - **Text-kleur:** `+`-knop met regenboog-icoon naast bestaande quick-swatches (`#ed-tx-color-picker`). Bestaande swatches blijven werken.
> - **Background:** `Off`/`On` toggle + swatch-tile (opent picker) + opacity-slider 0-100%. Schema: `L.bg = null` OR `L.bg = true` (legacy) OR `L.bg = {color, opacity}`.
> - **Cutter (`cutter.py` regel 335-355):** nieuwe dispatch leest dict-schema `{color, opacity}`, valt terug op legacy `bg=true` voor backward-compat.
> - **Live preview:** rgba-styling toegepast via inline style op `.ed-tx-live` nodes.
>
> ### ✅ Built-in fonts library (11 fonts, 3,7 MB)
>
> Fonts in `dj-clip-cutter/static/fonts/builtin/` met OFL-licenties:
> Alfa Slab One, Anton, Archivo Black, Bebas Neue, Inter, Montserrat, Open Sans, Oswald, Roboto, Roboto Condensed, Roboto Mono. Manifest in `manifest.json`.
>
> - **Backend (`app.py` ~regel 2510-2680):** `GET /api/builtin-fonts` returnt manifest. Static files via Flask's `static_url_path`. PyInstaller bundelt automatisch (datas=[('static','static')]).
> - **Frontend:** `loadFontLibraries()` parallel met auth-boot, `_renderBuiltinFontFaces()` injecteert @font-face eager (alle 11), `STATE.builtinFonts`.
>
> ### ✅ System-font auto-scan (438 fonts op test-Mac)
>
> Lokale scan via Python `os.walk`, **geen netwerk**. macOS scant `/System/Library/Fonts`, `/Library/Fonts`, `~/Library/Fonts`. Windows + Linux paths ook geconfigureerd.
>
> - **Backend (`app.py`):** `_scan_system_fonts()` filtert op `.ttf` / `.otf` / `.ttc` (inclusief Mac TrueType Collections — Helvetica, Times, etc.). 30s in-memory cache + persisted naar `DATA_DIR/system_fonts_cache.json` zodat cutter.py de paden kan lezen.
> - **Endpoints:** `GET /api/system-fonts` (met `?refresh=1`), `GET /api/system-fonts/file/<id>` voor browser @font-face load.
> - **Frontend:** lazy `@font-face` — pas geladen bij selectie van een system-font (anders 438× HTTP-requests).
> - **Cutter (`cutter.py` ~regel 320-380):** `_load_system_fonts_cache()` + `_load_builtin_fonts()` worden gemerged in `brand_fonts` lijst. `_build_text_layer_filters` resolved alles via één pad.
>
> ### ✅ Font picker UI: 4 secties + search + refresh-knop
>
> Font-dropdown (`#ed-tx-font`) wordt nu gerendert met 4 optgroups: System sans / Built-in / System fonts (438) / Brand Stack. Live filter via `#ed-tx-font-search` input boven de dropdown. Refresh-knop `↻` (12×12 SVG) naast Font-label triggert `/api/system-fonts?refresh=1` met spinner-animatie.
>
> Empty-state placeholder: "Geen fonts gevonden voor X" bij 0 hits.
>
> **Belangrijke fix tijdens sessie:** `_paintEditorTextLive` (regel ~11151) keek aanvankelijk alleen in `STATE.brandKit.fonts`. Uitgebreid naar alle 3 bronnen + lazy `_ensureSystemFontFaceLoaded()` zodat live preview werkelijk in de gekozen font rendert.
>
> ### ✅ PREVIEW-badge weg uit video editor
>
> `<div class="stage-tag">● Preview</div>` (regel 3980) + bijbehorende CSS (regel 1014-1018) verwijderd. Sjuul vond hem niets toevoegen — video stage is nu schoon.
>
> ### 🔴 ONTDEKT BUG (BLOCKER voor sessie 43): Captions niet in export
>
> Sjuul testte: clip met text-layer → "Done" geklikt → Export → mp4-bestand op disk bevat **geen tekst**. Root cause: `_run_export_job` (app.py regel 5355) gebruikt bestaande `clip['files']` paths zonder text_overlays.json te lezen. Trim doet wel layer-injection (via `/api/recut`), maar Export skipt dat.
>
> **Plan voor sessie 43 staat in `SESSIE43-EXPORT-PIPELINE-PLAN.md`** met 3 onderdelen:
> 1. Auto-bake captions in export (kritiek, ~2,5u, raakt brand-pipeline)
> 2. Rename-veld in `pickExportSettings` modal (~30-45min)
> 3. Filename op disk schoner — sidecar JSON ipv `__clip__` token in filename (~1u)
>
> Trim-knop moet ENKEL slicen (in/out) na sessie 43 — geen text/branding meer. Editorrechts-paneel knoppen `ed-trim-big` + `ed-trim-toolbar` blijven, maar `editorTrimAtPlayhead()` switcht van `/api/recut` naar nieuwe `/api/slice` endpoint.
>
> ### Backups sessie 42
>
> - `static/index.html.pre-sessie41.bak` (646K) — vóór color wheels
> - `static/index.html.pre-sessie42.bak` (663K) — vóór fonts
> - `static/index.html.pre-sessie42-rename.bak` (673K) — na PREVIEW-badge, vóór rename-werk (nog ongebruikt voor sessie 43)
> - `cutter.py.pre-sessie41.bak` (85K) + `cutter.py.pre-sessie42.bak` (85K)
> - `app.py.pre-sessie42.bak` (241K) + `app.py.pre-sessie42-rename.bak` (250K)
>
> ### Verificatie sessie 42
>
> Alle wijzigingen live geverifieerd via Chrome MCP connector — Sjuul's eigen dev-server:
> - Color wheels werken voor text + bg + opacity
> - Built-in fonts (Bebas Neue + Helvetica) renderen visueel zichtbaar in canvas
> - Search-input filtert correct, refresh-knop triggert nieuwe scan
> - PREVIEW-badge afwezig in DOM na hard refresh
> - Smoketest 5/5 groen op font picker (search → select → empty-state → clear → built-in)

---

## STATUS NA SESSIE 40 (2026-05-26)

> **Wat gedaan deze sessie — twee grote wins:**
>
> ### ✅ Fase 1 — Clip-render bug in .app gefixt
>
> **Root cause:** `BASE_DIR = os.path.dirname(__file__)` in `app.py` regel 176 wijst in een PyInstaller bundle naar `Contents/Frameworks/` — dat is **read-only** voor unsigned .apps op macOS. `os.makedirs(UPLOAD_DIR, exist_ok=True)` op regel 201 gooide `PermissionError(1, 'Operation not permitted')` op startup. Dev-server had geen probleem omdat `BASE_DIR` daar `dj-clip-cutter/` was (schrijfbaar). `launcher.py` had de oplossing al voorbereid (`USER_DATA_DIR` op regel 58, `os.environ.setdefault("OMNI_DJ_USER_DATA", ...)` op regel 65), maar `app.py` las die env-var nooit.
>
> **Fix in `app.py` regel 176-205:**
> - Nieuwe regel 183: `DATA_DIR = os.environ.get("OMNI_DJ_USER_DATA", BASE_DIR)` — leest env-var, valt anders terug op `BASE_DIR` (dev-server gedrag onveranderd).
> - 7 paden gewijzigd: `UPLOAD_DIR`, `OUTPUT_DIR`, `SETTINGS_PATH`, `HISTORY_PATH`, `WATCH_FOLDER_PATH`, `BRAND_KIT_PATH`, `BRAND_KIT_DIR` (`BRAND_FONTS_DIR`/`BRAND_LOGO_DIR`/`BRAND_WATERMARK_DIR` zijn child-paths van `BRAND_KIT_DIR`).
>
> **Verificatie:** rebuild via `build_macos.sh dmg`, smoketest met Housy Good vibes set (30min) — 200/206 responses op `/api/clip/...mp4`, geen PermissionError meer in `launcher.log`, clips renderen + spelen af in editor.
>
> **Backup:** `app.py.pre-sessie40.bak` (237K).
>
> ### ✅ Fase 2 — Password-reset flow volledig end-to-end
>
> **Backend (`auth.py` ~regel 442 + verder):**
> - `_EMAIL_RE`, `_COMMON_PASSWORDS` blacklist (20 entries — uitbreidbaar post-launch)
> - `_is_valid_email(email)` — lengte-cap 254 + regex
> - `_is_strong_password(pw)` — NIST-conform: 8-128 chars + niet in blacklist + letter + cijfer/symbool. Géén verplichte hoofdletter/symbool (NIST 2017 onderzoek: dat verzwakt wachtwoorden)
> - `_reset_redirect_url()` — env-var `RESET_REDIRECT_URL`, default `http://127.0.0.1:5555/static/reset-password.html`
> - `forgot_password(email)` — fail-silent, returnt ALTIJD `{ok: true}` (account-enumeration protection)
> - `reset_password(access_token, refresh_token, new_password)` — `set_session()` → `update_user()` → tokens terug. **Bug tijdens test gevonden:** `set_session()` in supabase-py 2.30 returnt `AuthResponse` met `.session.access_token`, niet `.access_token` direct. `update_user()` returnt `UserResponse` zonder `.session`. Fix: leest tokens uit `sess.session.access_token` met fallback naar input-tokens (die zijn nog steeds geldig).
>
> **Backend endpoints (`app.py` regel 1185 e.v.):**
> - `POST /api/auth/forgot-password` met dubbele rate-limit: 3/u per IP + 5/u per email (via `_forgot_email_key`). Audit-log `auth.password_reset_requested`.
> - `POST /api/auth/reset-password` met 5 per 10 min per IP. Audit-log `auth.password_reset` of `auth.password_reset_failed`.
>
> **Frontend nieuw bestand `static/reset-password.html`:**
> - Standalone pagina, brand-tokens inline (Inter + Fraunces), invalid-state als hash leeg is, hash-clearing binnen 100ms na load (security), tokens uit `#access_token=...&refresh_token=...&type=recovery`, password+confirm check, fetch `/api/auth/reset-password`, schrijft success naar `localStorage['omniDj.session']` (zelfde shape als `saveSessionToStorage()` in index.html → auto-login na redirect naar `/`).
>
> **Frontend `static/index.html`:**
> - "Wachtwoord vergeten?" link onder Log in-knop, alleen zichtbaar in login-mode (CSS `data-auth-mode="signup"` verbergt 'm)
> - Forgot-modal HTML rond regel 3447: email-input + "Stuur reset-link" + success-melding "Check je inbox" (altijd zelfde melding ongeacht response)
> - CSS regel 2486-2585: `.auth-forgot-link`, `.forgot-modal`, `.forgot-modal-card`, etc.
> - JS rond regel 14033: `openForgotModal()`, `closeForgotModal()`, `handleForgotSubmit()`, `bindForgotModal()`. Pre-fill email uit login-form, autofocus, Escape sluit, overlay-click sluit, `dataset.bound` guards
>
> **Supabase config (door Sjuul in dashboard gedaan):**
> - URL Configuration → Site URL: `https://omnidj.com`. Redirect URLs allowlist: `http://127.0.0.1:5555/static/reset-password.html` + `https://omnidj.com/reset-password`
> - Sign In / Providers → Email → Email OTP expiration 3600s (1u), Min password length 8
> - Emails → Reset Password template Nederlandstalig in Omni DJ brand-kleur `#e8b766`, subject "Wachtwoord resetten - omnidj.com"
>
> **End-to-end test geslaagd** met test-account `sjuulsmitslolol@gmail.com`: signup → forgot via modal → mail kwam binnen (Supabase default SMTP, 0 min) → klik link → reset-form geopend → nieuw wachtwoord opgegeven → auto-login → redirect naar `/`.
>
> **Backups:** `auth.py.pre-sessie40.bak` (18K), `app.py.pre-sessie40-reset.bak` (238K), `static/index.html.pre-sessie40.bak` (636K).
>
> **TODO voor sessie 41:** `supabase_admin.auth.admin.sign_out(user_id, scope='others')` faalt in supabase-py 2.30 met "invalid JWT: token is malformed" — onze try/except vangt het op (password wijziging slaagt), maar hardening werkt niet. Volgende sessie de juiste signature vinden (mogelijk via REST call ipv Python SDK). Niet beta-blocker.
>
> **Curl-tests bewezen security:**
> - Onbestaande email → `{ok:true}` ✅ (geen enumeration)
> - Leeg email-veld → `{ok:true}` ✅ (geen 500)
> - XSS in email → `{ok:true}` ✅ (geen reflectie)
> - 4× snel achter elkaar → poging 4 → HTTP 429 ✅ (rate-limit)
> - Zwak wachtwoord ("abc") → `{ok:false}` met duidelijke error ✅ (vóór Supabase aanroep)

---

## 🎯 Openstaand voor volgende sessie — in prioriteitsvolgorde

> NB — Voor de **snelste briefing** zie het ⚡ START HIER blok bovenaan dit
> document; de lijst hieronder is de uitgebreide planning-met-context.

1. ✅ ~~**🔴 PyInstaller rebuild**~~ — **klaar in sessie 53** (2x gedaan: rebuild #1 sessies 50+51, rebuild #2 sessie 53 fixes). Bundle in `/Applications` is up-to-date.
2. ✅ ~~**🟡 E2E real-export-test**~~ — **klaar in sessie 53.** "SESSIE 53 TEST"-tekst in `Drop_3.mp4` op disk geverifieerd via QuickTime → captions worden ge-baked in productie-.app.
3. **🟡 Smoketests sessie 43+44 — deels gedaan in sessie 53.** Captions-flow + rename + sidecar + folder-whitelist + multi-clip-flow (UI) bewezen. Niet gedaan: 9 selectie-balk-smoketests (Bug 1 niet reproduceerbaar → laagste prio).
4. **🔵 Code-rebrand "Omni DJ" → "Omni DJ"** (~4-6u) — string-sweep door static/index.html, launcher.py, app.py, auth.py, build_macos.sh, alle .md files. Plus app-icon, bundle-identifier, `CFBundleName`, in-app teksten. Folder-renames (`dj-clip-cutter/` → ?) hoge-risico — apart plannen. **Doe dit vóór Fase 3 omdat omnidj.com landing onder Omni DJ-branding hoort.**
5. **Sessie 43 follow-up — 1:1 + 4:5 als echte aspect-keys** (~2-3u). Nu mapped op vertical/landscape in startExport. Backend `_resolve_export_sources` + `cutter.cut_clip_*` moeten aparte `square` + `portrait` formats kennen met eigen crop-strategie.
6. **Fase 3 — omnidj.com koppelen** via Cloudflare (nameservers van registrar → Cloudflare, DNS records, Pages custom domain). Vóór Stripe live mode. **Was omnidj.com, vervalt — sessie 53 rebrand.** Landing-repo + Pages-project moeten opnieuw onder Omni DJ-naam (oude repo `sjuulstudios/djclips.nl-by-MONO-LABS` blijft als archive bestaan).
7. **Fase 4 — Stripe live mode** — pas na omnidj.com live. Runbook: `STRIPE-DNS-RUNBOOK.md` moet inhoudelijk worden geupdate van omnidj.com → omnidj.com.
7. **🆕 Fase 5 — Content Calendar + Multi-artist (zie `PLAN-CONTENT-CALENDAR-2026-05-26.md`)** — pas na sessie 44 + omnidj.com + Stripe live:
   - **5a Multi-tenant fundament** (3-4 wkn dev): migraties 004/005/006 voor workspaces + workspace_members + workspace_id op resource-tabellen
   - **5b Calendar UI + datamodel** (2-3 wkn dev): migratie 007 (scheduled_posts) + maand/week-view + "Plan in Calendar" knop in export-modal
   - **5c Postiz publishing** (3-4 wkn dev): migratie 008 (social_accounts) + Postiz Cloud OAuth + per-workspace social-connect
   - **5d Polish + mobile** (4+ wkn): approval-flow, watch-folder, Ollama-captions, mobile push
   - **5e Ads research** (2-3 wkn, geen dev): geld-flow Model A/B/C beslissen + NL-jurist/fiscalist
   - **5f+ Ads-platform** (Fase 5/6/7 in plan): Meta + TikTok + later Google. Allerlaatst.
8. **Sessie 40 hardening TODO** — `admin.sign_out(scope='others')` signature voor supabase-py 2.30 fixen, zodat password-change ook alle andere sessies invalideert.
9. **Sessie 43 follow-up — Export-queue Optie B (parallel)** — pas overstappen als gebruikers in praktijk klagen over snelheid bij grote queues. N parallelle workers (cap 3), met semafoor voor disk I/O. Aparte sessie waardig.
10. **SMTP-provider** (Postmark of Resend, ~$15-20/mo) — pas relevant bij betalende gebruikers. Voor beta is Supabase default OK.

### Klaar — Fase 5 (sessie 41+42)

- ✅ Color wheels voor text + background (sessie 41)
- ✅ Built-in fonts library (sessie 42)
- ✅ System-font auto-scan + .ttc support (sessie 42)
- ✅ Font picker UI met 4 secties + search + refresh (sessie 42)
- ✅ Live-preview rendering voor alle font-bronnen (sessie 42)
- ✅ PREVIEW-badge verwijderd uit editor (sessie 42)

---

## Recente sessies — ingedikt (27–39)

> Volledige beschrijvingen staan in `HANDOVER-ARCHIVE.md` voor sessies 1–26. Sessies 27 en later staan compacter hieronder. Per sessie: wat + waarom + relevante files/commits + eventuele gotchas. Sessie 40 staat als hoofdstatus boven.

### Sessie 41 — Color wheels (Fase 5 / C+D, 2026-05-26)

- **Wat:** Mini color picker `OmniDJPicker` ingebouwd (eigen build, geen externe library zoals Coloris — Sjuul wilde geen frontend-dependency). HSV-vlak + hue-strip + hex-input + opacity-slider. Herbruikt voor text-kleur én bg-kleur.
- **Text-kleur:** `+`-knop met regenboog-icoon náást bestaande swatches in `#ed-tx-swatches`. Bij elke `renderEditorTextLayers` opnieuw geappend want `swWrap.innerHTML = ...` wist 'm anders.
- **Background:** Off/On toggle + swatch + opacity-slider. Nieuw schema `L.bg = {color, opacity}` of `null`. Back-compat `L.bg === true` blijft werken (cutter resolved fallback).
- **Cutter (`cutter.py` regel 335-355):** dispatch leest isinstance(bg, dict), else legacy bool defaults.
- **Verificatie:** 5/5 smoketests groen via Chrome MCP. Geen visuele regressie.
- **Backups:** `static/index.html.pre-sessie41.bak` (646K), `cutter.py.pre-sessie41.bak` (85K).

### Sessie 39 — Native file picker + editor drawer fixes (2026-05-25, avond)

- **Wat:** (1) Native file picker (commits `0ef2232` + `7ab31e5`): `/api/pick-file` endpoint met AppleScript voor macOS + tk fallback voor Win/Linux, `openFilePicker()` in `static/index.html` vervangen — geen 4GB browser-limiet meer. (2) Editor drawer fixes (commit `7ab31e5`): `.ed-body` `position:relative`, `.ed-text-drawer top:62px`, sluitende `</div>` van `.editor` naar ná `<aside>` drawers verplaatst, `--ink-0..4` overschreven in donkere drawer. (3) Timeline editor smoketest met Franky Rizardo 7.8GB set: trim handles, scrubbing, ratio switching werken zonder JS errors.
- **🔴 Open bug bij afsluiten:** clips renderen niet in .app build (PermissionError op writes naar `Contents/Frameworks`). **→ Opgelost in sessie 40, zie hoofdstatus boven.**
- **Commits:** `7ab31e5`, `0ef2232`, `b000a57` (baseline)

### Sessie 38 + 37 — DMG Fase 4 klaar (2026-05-25)

- **Wat:** Fase 4 afgerond: venv, flask-limiter, smoketest, migrations 002 (audit_logs) + 003 (RBAC role) deployed, admin role gezet voor omnidj@monohq-labs.com, edge function `update-usage` deployed, DMG gebouwd.
- **Post-build bugfixes** (in `static/index.html` + `launcher.py` + `app.py`):
  - Upload error "supabase_admin niet geconfigureerd" → fixed door `access_token` door te geven aan `_get_or_refresh_profile()`
  - File picker 2 clicks nodig → fixed met 120ms `setTimeout` (pywebview race condition)
  - Set stopt bij 14% / process pool crash → fixed door `multiprocessing.freeze_support()` ALLEREERST in `launcher.py` te zetten
  - Meerdere browsertabs spawnen → zelfde fix
  - Preview ratio black bars → `applyEditorStageSize()` set nu `object-fit` op video; `maxHeight:'none'` bij 16:9 en 1:1
- **Testsets beschikbaar:** `dj-clip-cutter/CLIP DROP DJ-SETS/` bevat 5 MP4 sets voor debugging (Don Diablo, Ediine x Hör Berlin, Franky Rizardo, Housy Good vibes, Lisa Korver x Hör Berlin)
- **DMG bouwen:** `bash build_macos.sh dmg` in `dj-clip-cutter/` met actieve venv. Output: `dist/Omni DJ.app` + `dist/Omni DJ.dmg`
- **Belangrijke regel:** na elke code-change herbouwen — PyInstaller bakt `index.html` in de bundle, dev-server serveert altijd de oude versie

### Sessie 36 — Infrastructuur (2026-05-24)

- **Wat:** externe diensten gekoppeld, geen code-changes. Aparte landing-werkmap `~/Documents/Claude/Projects/clipdrop-landing-deploy/` (los van Omni DJ git-repo), GitHub repo `sjuulstudios/djclips.nl-by-MONO-LABS` aangemaakt + initial push (commit `d98cf78`), Cloudflare Pages project `djclips-nl-by-mono-labs` live op https://djclips-nl-by-mono-labs.pages.dev, oud `clipdroplive` Pages-project verwijderd
- **🟡 Open:** omnidj.com koppelen aan Cloudflare (nameservers TransIP → Cloudflare, DNS-records, custom domain in Pages)
- **Gotcha:** `index.html` heeft `https://omnidj.com/` HARDCODED op meerdere plekken (canonical/og:image/og:url). Search-replace naar `https://omnidj.com/` pas doen samen met de DNS-cutover
- **Beslissingen vastgelegd:** Google Workspace ($6/mo) voor email, Cloudflare Pages (i.p.v. Vercel — onbeperkte bandwidth + commercieel toegestaan)
- **Drie werkmappen om te onthouden:** hoofd-app in `~/Documents/Claude/Projects/Omni DJ/`, deploy-map in `~/Documents/Claude/Projects/clipdrop-landing-deploy/`, source-of-truth landing in `Omni DJ/landing/`

### Sessie 35 — Security Foundation (2026-05-24, autonoom)

- **Wat:** drie security-onderdelen gebouwd: (1) audit-log met `supabase/migrations/002_audit_logs.sql` + `log_action()` in `auth.py` + `_audit()` in `app.py`, aanroepen op 7 endpoints (signup, login, login_failed, plan.checkout_started, plan.portal_opened, clip.export_started, file.upload, debug.logs_downloaded). (2) Data-isolatie review: alle Supabase-queries in `app.py` + `auth.py` gechekt → 6 admin-queries met expliciete `.eq('id', user_id)`, 3 anon-queries via RLS — isolatie correct. (3) RBAC: `supabase/migrations/003_rbac_role_column.sql` (role kolom user/beta/admin met check constraint), `get_user_role()` + `require_role()` decorator in `auth.py`. `/api/debug/logs` nu beveiligd met `@require_role('admin')`
- **Sjuul handmatig vereist:** migraties 002+003 deployen in Supabase SQL Editor + zichzelf admin maken via UPDATE-query + dev-server herstarten

### Sessie 34 — UI polish + plan-documenten (2026-05-23 + 24)

- **Wat:** Tekstpaneel input-contrast (`color:var(--paper)` op `.ed-tx-field textarea/input/select`), platform-logo's (TikTok/Instagram/YouTube/Facebook) als gekleurde SVGs i.p.v. text-glyphs in export-popover + dashboard menu, compactere layout (`.meta` flex space-between)
- **Plan-documenten opgesteld (niet geïmplementeerd):**
  - `SESSIE34-CAPTION-FONTS-PLAN.md` — caption-fonts library + color-wheel, ~9.5u, 4 beslispunten
  - `SESSIE34-PASSWORD-RESET-PLAN.md` — security-critical, ontbreekt volledig in `auth.py`, leunt op Supabase Auth reset-flow, dekt 16 OWASP-aanvallen, ~5.5u, 4 beslispunten. **Aanbeveling: bouwen vóór beta-launch**
- **Backup:** `static/index.html.pre-sessie34.bak` (642 KB)

### Sessie 33 — Autonoom (2026-05-23)

- **Wat:** Beta-flyer definitief uit scope (verwijderd uit alle carry-overs), split-feature volledig opgeruimd uit frontend (UI + JS + CSS — backend `/api/split-clip` endpoint blijft), loop-mode toggle prominenter (tekst-label "Loop On/Off" + pulserende amber-dot + glow-lijn onder trim-band in timeline)
- **Cleanup-script:** `python3 scripts/cleanup_legacy_jobs.py` dry-run → 0 kandidaten (al opgeruimd). 13GB output/ over 28 folders, allemaal owned
- **Plan-document:** `SESSIE33-RECUT-QUEUE-PLAN.md` — background recut-queue (`_RECUT_QUEUE` dict + worker thread + `/api/recut-status/<recut_id>`, opt-in via `?async=1`), edge cases, 4 beslispunten
- **Backup:** `static/index.html.pre-sessie33.bak`

### Sessie 32 — Security ronde + timeline UX (2026-05-23)

- **Security fixes:**
  - **Fix 1 — Rate limiting (live):** `flask-limiter>=3.5` in `requirements.txt`, limiter-init in `app.py` (~84-149), 7 endpoints met `@limiter.limit`: signup 5/h-IP, login 10/5min-IP, refresh 30/h-IP, billing/checkout 10/h-user, billing/portal 10/h-user, upload 20/h-user, upload-local 20/h-user. Storage `memory://`, per-user key = eerste 32 chars JWT
  - **Fix 2 — RLS policies in version control:** `supabase/migrations/001_rls_policies.sql` met SELECT (`auth.uid()=id`) + UPDATE met kolom-bescherming (`plan`, `usage_this_period`, `quota_reset_date`, `stripe_customer_id`, `stripe_subscription_id` zijn protected). INSERT/DELETE expliciet REVOKED van authenticated role. Live geverifieerd in Supabase
- **Bewust geparkeerd:** concurrency limit, database indexing, webhook IP allowlist
- **Timeline-editor UX (frontend-only, alleen hard-refresh):**
  - **Killer bug (32e):** cache-buster `?v=<timestamp>` werd ná `withAuth()` (`?token=...`) toegevoegd → dubbele `?` in URL → backend `_require_job_access(..., allow_query_token=True)` faalt → 403 → "Clip file not yet rendered" overlay. **Fix:** check op bestaand `?` en gebruik `&` als joiner
  - Stretch-bug definitief gefixt: `hasBand = (Math.abs(t.inSec) > 0.05) || (Math.abs(t.outSec - dur) > 0.05)` — vangt nu ook pure stretch (beide handles naar buiten)
  - `editorTrimAtPlayhead` refactor: 5 branches → 1 pad, single source of truth = `clip.duration`. `if (hasBand) → /api/recut` else `→ /api/split-clip`
  - Playhead: start op IN-handle, sleepbaar (z-index 6→50, hit-area 18/14px), stopt automatisch bij `cur >= outSec - 0.02s`
  - Asterix + scissor weg uit toolbar — alleen Trim als primaire actie
  - Audio stopt bij back-button via `switchView()` detect
- **Backups:** `app.py.pre-ratelimit.bak`, `requirements.txt.pre-ratelimit.bak`, `static/index.html.pre-sessie32{,b,c,d}.bak`
- **Memory:** `project_clip_live_security.md` aangemaakt

### Sessie 31 — Bugs + watermark + Brand Stack collapsibles (2026-05-23)

- **Wat:** (1) Bug #1 BPM/Key corner-stamp force-off in `cutter.py: _load_brand_assets_for_job` (zet `bpm_cfg['enabled']=False` bij laden). (2) Bug #2 "Follow horizontally" — vondst: Lisa Korver source is **1920×1080 LANDSCAPE 16:9**, niet vertical. Pan-mode op landscape source IS wiskundig altijd zoom. Fix: nieuwe derde mode `letterbox` (geen crop, scale-to-fit + pad met zwarte balken) — nu **default voor nieuwe clips**. (3) Watermark JS-bindings + render-pipeline LIVE: backend endpoints POST/GET/DELETE `/api/brand-kit/watermark`, `cutter.py` nieuwe `_build_watermark_overlay_segment` analoog aan logo maar met aparte labels zodat watermark NA logo komt. (4) Brand Stack collapsibles met chevron `▾` + localStorage persistence
- **Verificatie:** `python3 -m py_compile app.py cutter.py` OK, `node --check` op 398KB JS-block OK
- **Backups:** `app.py.pre-sessie31.bak`, `cutter.py.pre-sessie31.bak`, `static/index.html.pre-sessie31.bak`
- **Runbook:** `SESSIE31-REBUILD-RUNBOOK.md`

### Sessie 30 — Pan/letterbox tracking + JWT refresh (2026-05-22)

- **Wat:** Pan-modus + 1:1/4:5 tracking + auto-refresh JWT live geverifieerd. 11 punten van Sjuul afgewerkt + beta-blocker code-side klaar
- **Runbook:** `SESSIE30-REBUILD-RUNBOOK.md`
- **Sjuul handmatig:** edge function `update-usage` deployen, rebuild, retest

### Sessie 29 — Vier kleine bèta-verbeteringen (2026-05-22)

- **Wat:** (1) Landing site Vercel-ready (`vercel.json`, `favicon.svg`, `og-image.svg` 1200×630, `robots.txt`, `sitemap.xml`, og/twitter/canonical meta tags in 4 HTML-pagina's). (2) In-app Send-logs knop: `/api/debug/logs` endpoint in `app.py`, ZIP of `?format=text`, bundelt summary + launcher.log tail 200KB + caller's job_history. Settings-view kreeg "Diagnostics" sectie. (3) NaN BPM display fix in `static/index.html` regel ~5471 (safe extraction met typeof check). (4) Cleanup-script `dj-clip-cutter/scripts/cleanup_legacy_jobs.py` (dry-run default, `--apply` verplaatst owner-less jobs naar `.quarantine-YYYYMMDD/`)
- **Backups:** `app.py.pre-sessie29.bak`, `static/index.html.pre-sessie29.bak`

### Sessie 28 — Library-scoping bug + 20/20 security tests (2026-05-22)

- **Wat:** Kritieke library-scoping bug opgelost — tweede account zag andermans sets. (1) Backend Strategie B: nieuwe helper `_require_job_access(job_id, allow_query_token=False)` in `app.py` trekt JWT uit Bearer-header óf `?token=` query param, valideert, matched `job['user_id']` met caller. Returns 404 bij mismatch (geen probe-leak). Toegepast op ~30 job-routes. `_append_to_history` stamps user_id, `/api/history` filtert. (2) Frontend `withAuth(url)` helper in `static/index.html`: voegt `?token=<JWT>` aan media-URLs die geen Bearer-header kunnen meesturen. 10+ call-sites: thumbnail, filmstrip, clip src, source src, spectrogram, progress SSE. Download-knoppen kregen Bearer in fetch-init. (3) End-to-end smoketest op Lisa Korver x Hör Berlin (424MB, 55 min, 30 clips) — Account A + Account B in nieuwe tab → library leeg, badge FREE, quota 0/2. **20/20 cross-account security tests groen**
- **Supabase-vondst:** `.test` en `.example` TLDs worden geweigerd. Free email rate limit 2/uur blokt 3e signup. Beide opgelost door **Email Confirmation UIT te zetten** in Supabase dashboard → Auth → Sign In/Up. **Voor v1.0 (paid launch) weer aanzetten** zodra eigen SMTP (SendGrid/Postmark/Resend) is gekoppeld
- **Backups:** `app.py.pre-sessie28.bak`

### Sessie 27 — Installer pipeline + Stripe via edge functions + legal (2026-05-17)

- **Wat:** (1) Installer pipeline werkend: PyInstaller-spec + `launcher.py` + `entitlements.plist` + `build_macos.sh` in `dj-clip-cutter/`. ffmpeg/ffprobe in bundle gekopieerd, .bak files defensief gestript. **Browser-fix:** `subprocess.run(['open', url])` i.p.v. `webbrowser.open` (laatste werkt niet in gebundelde .app op macOS). Logging naar `~/Library/Application Support/Omni DJ/launcher.log`. Apple Developer + Windows BEWUST UITGESTELD tot na macOS-beta. (2) Stripe via edge functions: `runtime_config.py` hardcodet alleen publieke keys, geen secrets in bundle. Twee nieuwe edge functions met JWT-verificatie: `create-checkout-session` + `create-portal-session`. `billing.py` heeft fallback (zonder lokale `STRIPE_SECRET_KEY` → edge function call met Bearer). Deploy zonder `--no-verify-jwt`; webhook blijft mét `--no-verify-jwt`. (3) Legal hardening: `landing/privacy.html` + `landing/terms.html` aangevuld met sub-processors, AVG-rechten (15/16/17/18/20/21), retention per type (7 jaar invoices), CCPA, force majeure, export controls, beta-disclaimer. Plus 64 .bak files opgeruimd naar `_bak-archive-2026-05-17.tar.gz`, git repo geïnitialiseerd (commit `b000a57`, branch `main`)

---

## App starten (dev-server)

```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"
./start.sh
```

Browser opent op http://127.0.0.1:5555.

Voor `.app` build: `bash build_macos.sh dmg` in `dj-clip-cutter/` met actieve venv. Output: `dist/Omni DJ.app` + `dist/Omni DJ.dmg`.

---

## Toekomstige doelen (nog NIET implementeren)

- OAuth voor TikTok/Instagram upload
- Patent aanvragen (NL/EU/global) — besproken, nog niet uitgevoerd
- Apple Developer signing + notarization
- Windows .exe build

**📄 Strategisch + technisch plan voor moat-features (2026-05-26):** zie `PLAN-MOAT-FEATURES-2026-05-26.md` in de project-root. Dat document beschrijft features 5 (multicam), 7 (branding profielen), 8 (auto-draft pipeline + content calendar + direct publish naar TikTok/Instagram/YouTube), 9 (lokaal/privacy als premium tier) plus de ad-spend-as-a-service laag (Intellijend-model). Inclusief volgorde, werk-schattingen, wat Sjuul moet aanleveren en pricing-voorstel. Raadplegen voor langetermijn-richting; eerst de open .app-build bug fixen voor we hieraan beginnen.

---

## Hoe je hier verder mee werkt

1. Lees dit bestand → begrijp de huidige staat
2. Raadpleeg `LESSONS-LEARNED.md` voor terugkerende patronen vóór je iets aanraakt dat al eens gefixt is
3. Diagnose → aanpak voorstellen → wachten op "ja" → pas dan uitvoeren
4. Minimale impact: doe alleen wat gevraagd is, meld als scope groter is dan verwacht
5. Update dit bestand als er iets verandert (bug gefixed, feature toegevoegd, nieuwe bug ontdekt)

**Voor Sjuul:** terminal-commando's letterlijk zonder markdown fences, één commando per regel met pad-quotes. Hij kopieert direct vanuit chat.

---

## Veiligheid

- Nooit API keys of wachtwoorden in bestanden opslaan
- Altijd bevestiging vragen voor bestandsverwijdering
- Backup vóór elke risky change (`bestand.pre-sessieNN.bak` patroon)
