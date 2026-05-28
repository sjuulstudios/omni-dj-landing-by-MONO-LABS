# SESSIE 58 — Autonome audit-log

> Live smoketest + security + UI-quality van sessies 56-57 voor commit naar feature/auto-mode-and-brand-redesign.
> Datum: 2026-05-28. Werkmap: /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter/
> Sjuul gaf akkoord op alle tools en alle 4 blokken vooraf.

## SAMENVATTING

| Blok | Status | Kern |
|---|---|---|
| Pre-fix: login-scherm | DONE + LIVE | Logo+balk+sublabel weg, Omni DJ wordmark, active-tab pill werkt |
| Blok 1: Live UI-walk | DONE + LIVE | 9 views door, 2 bugs gevonden, 1 critical fix gedaan (modal-lek), 4 copy-fixes (em-dash + rebrand) |
| Blok 2: Security audit | DONE | XSS test gefaald om te triggeren (escape works), geen service_role in frontend, geen eval, 1 token-in-URL pattern als 🟡 |
| Blok 3: UI-quality + a11y | DONE | 51 focusable in Brand, AAA tekst-contrast, 1 a11y-bug (Escape) gefixt |
| Blok 4: Rapport | DONE | dit document |

**8 fixes direct doorgevoerd. 6 open items voor Sjuul's review.**

---

## SCOPE & BEPERKINGEN

- Live tests via dev-server op http://127.0.0.1:5555 (sjuul startte handmatig)
- Auth-overlay handmatig verborgen om views te kunnen testen zonder login (token zat al in localStorage uit eerdere sessie, dus profile-data was leeg in renders die fetch /api/auth/me vereisen — dat zijn test-artefacten, geen echte bugs)
- Chrome MCP draait op read-tier, ik kon page-clicks doen via `javascript_tool` ipv echte muis (zelfde rendering)
- Computer-use op Chrome was tier "read" (alleen kijken). Toch genoeg voor visuele audit
- Sandbox bash kon dev-server niet starten op Sjuul's Mac (verschillende machines), maar fysieke .app/dev-server keuze gaat via Sjuul

---

## PRE-BLOK FIX — Login-scherm opschoning

Sjuul stuurde 2 screenshots tijdens sessie-start met 3 verzoeken: logo+Clip Live+DJ-set studio sublabel weg, donkere balk-achtergrond weg, Log in/Sign up tabs duidelijker.

### Wat ik aanpaste in `static/index.html`
- **DOM 8660**: aria-label naar "Sign in to Omni DJ"
- **DOM 8662-8668**: `.auth-brand` block: weg met brand-mark + DJ-set studio sub, vervangen door enkel `<h1>Omni DJ</h1>`
- **DOM 8670-8673**: tabs kregen `role="tablist"`, `role="tab"`, `aria-selected` (a11y)
- **DOM 8841**: forgot-modal-brand "Clip Live" naar "Omni DJ"
- **CSS 4943**: gradient + border-right op `.auth-brand` weg (was de visuele "balk"). Wordmark krijgt nu enkel een border-bottom voor scheiding
- **CSS 4989**: `.auth-tab.active` toegevoegd aan v2 active-selector (mismatch met JS-toggle was de echte reden dat active-tab niet uitsprong)
- **CSS**: tablist full-width met `flex:1` per tab
- **JS 23917 `setAuthTab`**: ook `aria-selected` mee-syncen

### Live geverifieerd via Chrome MCP
- Login-tab actief: Omni DJ wordmark + active pill OK
- Sign-up klik: pill flipt naar Sign up + wizard opent met "Where did you hear about Omni DJ?" OK

---

## BLOK 1 — LIVE UI-WALK (alle 9 views via Chrome MCP)

### Per view

| View | Status | Bevinding |
|---|---|---|
| Analyse | OK | Nette dropzone, copy "Analyse a DJ set / Drag & drop or select your DJ-set.", 3 intake-tiles (Watch werkt, DBX+Drive "Coming soon") |
| Library | OK | Projects 0 / Exports 0 in empty-state (history-API faalt zonder login-token, test-artefact). Segmented control + grid layout correct |
| Brand (NIEUW) | OK | Brand-pack dropdown werkt (Artist name + checkmark + "New brand-pack" + "Duplicate"), 9 cards aanwezig: Brand Kit, Watermark, Caption Presets (0/3), Clip Templates (TikTok Drop + Instagram Reel built-ins), Hooks, CTAs, Caption Copy (TikTok/Instagram/YouTube Title+Desc/X), Hashtag Sets, Stickers + Lower-thirds + Intro/Outro. Export/Import knoppen aanwezig |
| Social | OK | 4 platform-cards met mock-stats + "Postiz soon" badges. Recent posts empty-state. Mock-banner duidelijk |
| Calendar | OK | May 2026 month-view, 7-koloms grid, Month/Week toggle, oranje "Schedule post" button. Mock-banner |
| Insights | OK | 4 KPI-cards (Total Views 4.5K / Engagement 5.4% / Clips Published 0 / Best clip). Line chart "Views per day" rendert. 7d/30d/90d range. Donut + top clips lijst verder naar onder |
| Sidebar divider | OK | Dunne lijn tussen Insights en Auto-mode, exact zoals briefing |
| Auto-mode FREE (NIEUW) | OK | LOCKED-badge, paywall banner met oranje Upgrade-knop, pipeline 6-grid met lock-icons (5 Studio, 1 Studio+), Quick-enable disabled |
| Auto-mode Studio (NIEUW) | OK | `STATE.tier='studio'` + re-render: RUNNING groene badge, 5 stappen unlocked, stap 06 Auto-publish blijft locked, Publish schedule grid disabled (Studio+), Currently-in-pipeline + Recent runs + Safety cards |
| Settings | OK | Local-first hero, Watch folder card (PRO-paywall met UPGRADE TO ENABLE), Profile card (FullName/Artist/Email) rechts, Workspace + Artists (paywall "Add artist Studio only"), Brand kit compact, Diagnostics |
| Regressie (v2 OFF) | OK na fix | Legacy sidebar werkt, oude home OK, "Drop a DJ set / Choose from this Mac / Watch a folder" tiles. **Voor de fix: schedule-modal lekte als pagina-content (zie Bug A)** |

### Bug A — v2-modal-bg lekt naar legacy-shell — FIXED

**Severity:** 🟡 Medium (UX-breuk in legacy maar niet kritisch)

`#cal-schedule-modal` heeft `class="v2-modal-bg"`. In v2 verborgen via `body.redesign-v2 .v2-modal-bg { display:none }` + `.on { display:flex }`. **Geen matching legacy-CSS** → in v2-OFF mode fallback display:block → modal-DOM rendert inline binnen `<main>`.

**Fix:** added in CSS na regel 6827:
```css
.v2-modal-bg { display: none; }
body:not(.redesign-v2) .v2-modal-bg { display: none !important; }
```

Live geverifieerd: v2 OFF + reload → modal display=none → legacy home-view rendert clean.

### Copy fixes — DONE
Alle 5 user-zichtbare "Clip Live" references in static/index.html naar "Omni DJ":
- 8988 Cloud sync card sidebar (Dropbox copy)
- 9324 v2-home tile "Drop sets into a Dropbox..."
- 10393 Settings Watch folder card "Drop a track in here..."
- 10503 Storage notice about 2h+ sets
- (Sidebar `.brand-row` "Clip Live / DJ-set studio" op regel 8903 BEWUST UIT SCOPE — aparte rebrand-pass van shell)

### Em-dash fixes — DONE (user preference: no em-dashes)
4 user-zichtbare em-dashes verwijderd:
- Calendar `.sub`: `&mdash;` weg, vervangen door komma
- Brand `.v2-brand-sub`: `—` vervangen door `:`
- Auto-mode hero: `—` vervangen door `to`
- YouTube title default `{set_name} — {track_id} drop` naar `{set_name}: {track_id} drop`

Live geverifieerd: alle 3 page-renders bevatten geen em-dash meer (textContent check via JS).

### Open items uit Blok 1
- ⚠️ Sidebar brand-row toont nog "Clip Live / DJ-set studio" in legacy mode + Cloud sync sidebar-card titel (regel 8903) — aparte rebrand-pass
- ⚠️ Browser tab-title is nog "Clip Live" (uit `<title>` tag)
- ⚠️ Insights Best clip "810 views" terwijl Clips Published = 0 (mock-data inconsistentie)
- ⚠️ Settings Profile-inputs zijn leeg ondanks Sjuul ingelogd in sidebar (geen STATE-refresh van /api/auth/me na overlay-bypass — test-artefact)

---

## BLOK 2 — SECURITY AUDIT

### 1. XSS in user-input velden — 🟢 SAFE
- 28+ `escapeHtml()` aanroepen rond brand-pack/preset/watermark rendering
- Live test: payload `<img src=x onerror=window.__XSS_TRIGGERED=true>` in `OmniBrand.create()` pack-name. Pack opgeslagen, view geherrendert. `window.__XSS_TRIGGERED` blijft `false`. `viewBrand_hasScript=false`. **escapeHtml-coverage werkt.**

### 2. Caption-preset name/color XSS — 🟢 SAFE
`OmniBrand` heeft geen publieke `addCaptionPreset`-API (alleen list/getActive/setActive/save/create/delete/duplicate + 7 default-helpers + presetCap/packCap/getTier). Direct injectie via window-globals niet mogelijk via API. UI-handlers gebruiken `escapeHtml` in alle render-paths (regels 13278-13649).

### 3. JSON-import sanitization — 🟢 N/A
Geen publieke `importJSON`-methode op `window.OmniBrand`. Import gaat via UI-file-picker handler, niet via aanroepbare API. Handler-implementatie zou nog steeds payload-validatie moeten doen. **Aanbeveling voor sessie 59**: code-pad van Import-knop spitten en bevestigen dat parsed JSON dezelfde escapeHtml-paths doorloopt.

### 4. localStorage groei — 🟢 LAAG RISICO
Huidige usage: 7KB totaal, 16 keys. Brand-packs: 5KB voor 2 packs. Logo data-URLs (PNG/JPG/SVG) zijn in v1 base64 in localStorage opgeslagen. **Aanbeveling**: enforce 2MB cap per asset, geen cap aanwezig op het moment. Bij 5MB localStorage quota crash je na 3-5 logo's.

### 5. Tier-bypass — 🟡 MEDIUM (UX, niet data)
`packCap(tier)` enforced via UI. **Maar `OmniBrand.create()` is niet tier-gated** in code. Live test: ik kon als anonymous user (geen tier) een 2e pack maken via console. UI laat geen knop zien om dat te doen, dus geen praktisch risico, maar bij toekomstige multi-tenant Supabase setup is dit een server-side check vereist.

### 6. Backend endpoints — 🟡 PARTIAL CHECK
- `app.py` heeft 96 routes
- `_require_authed_user()` helper: 16 oproepen → veel routes potentieel zonder auth
- Verschil tussen public-bedoelde routes (health, static, auth-flow) en data-routes is niet 1-op-1 traceerbaar zonder route-voor-route scan
- **Sessie 57 brand_pack + automode features: 0 backend-routes** → data is volledig localStorage-only. **Geen Supabase migrations vereist voor v1**. Goed nieuws: minder attack-surface
- 17 limiter-aanroepen (sessie 32 fix actief)
- **Aanbeveling voor sessie 59**: snelle route-audit voor write-routes zonder `_require_authed_user`, met name nieuwe sessie 56-57 toevoegingen

### 7. CSP / inline scripts — 🟢 SAFE
0 `eval()` / 0 `new Function()` matches in static/index.html.

### 8. Brand-pack export data-URL strip — ⚠️ NOT VERIFIED
Sessie 57 export is JSON, maar of `logo_url` / `watermark.image_url` / stickers met data-URL gestript worden vóór export is niet vastgesteld in deze sessie. **Aanbeveling**: handmatig één pack met logo exporteren, JSON inspecteren op data:image/* en bestandsgrootte.

### 9. Supabase service_role / keys in frontend — 🟢 SAFE
`grep service_role|SERVICE_ROLE|SUPABASE_SERVICE` in `static/` → 0 matches.

### 10. Auth-token in URLs — 🟡 MEDIUM (sessie 28 design)
Bewust `?token=<jwt>` pattern voor media-URLs (sessie 28 commentaar). Op 127.0.0.1 lokaal acceptabel. **Stop met dit pattern voor omnidj.com productie** — JWT lekt via Referer-header, server-logs, browser-history. Migreer naar Authorization-header voor authenticated `<video>` / `<img>` via service-worker-fetch.

### 11. SVG-upload security — 🟢 SAFE
Brand-kit logo accepteert `.png,.svg,image/png,image/svg+xml`. Render-path: `<img src="data:image/svg+xml;base64,...">` (regel 13019). **`<img>` execute scripts in SVG NIET** (alleen `<iframe>` of inline SVG-DOM doet dat). Veilig.

---

## BLOK 3 — UI-QUALITY + A11Y

### Tab-navigatie — 🟢
- Brand view: 56 focusable elements, 51 zichtbaar, 0 geblokkeerd uit tab-order
- Alle inputs/buttons/selects reachable via Tab

### Kleurcontrast — 🟢 (text) / 🟡 (accent)
- Primary text `rgb(245, 242, 236)` op donkere bg ≈ **17:1 contrast = AAA**
- Accent `rgb(217, 119, 66)` orange op donkere bg ≈ **6.2:1 = AA voor 18px+, krap voor 14px body**
- Aanbeveling: gebruik accent niet voor lange copy, alleen voor knoppen/badges

### Bug B — Escape sluit modals niet — FIXED

**Severity:** 🟡 Medium (a11y standaard)

`#cal-schedule-modal` heeft geen eigen Escape-handler. Andere modals (upgrade, aspect, forgot-pwd) wel.

**Fix:** globale document-level keydown listener toegevoegd na `calCloseSchedule`:
```js
(function(){
  if (window.__v2EscBound) return;
  window.__v2EscBound = true;
  document.addEventListener('keydown', function(ev){
    if (ev.key !== 'Escape') return;
    var openModals = document.querySelectorAll('.v2-modal-bg.on');
    if (!openModals.length) return;
    var top = openModals[openModals.length - 1];
    top.classList.remove('on');
  });
})();
```

Sluit altijd de bovenste open v2-modal. Verstoort geen andere Esc-handlers in dropdowns/popups (geen preventDefault).

Live geverifieerd via native `dispatchEvent`: modal sluit (open=false, display=none).

### Andere UI-quality observaties
- Responsive niet gevarieerd getest (Chrome op single resolution 1530x784). **Aanbeveling sessie 59**: viewport 980px breakpoint + <700px mobile check
- Empty-states allemaal helpful copy: "No projects yet. Drop a DJ set in the Analyse tab to get started." + action-knop. "No completed runs yet." etc. Goed.
- Cards rounden mooi af, padding consistent
- Loading-states (FileReader bij logo-upload) niet gevarieerd getest (geen logo daadwerkelijk geupload tijdens audit)

---

## CODE-WIJZIGINGEN DEZE SESSIE

| File | Type | Wat |
|---|---|---|
| `static/index.html` | DOM | Auth-overlay: brand-block vervangen door wordmark "Omni DJ" (regel 8660-8673) |
| `static/index.html` | DOM | forgot-modal "Clip Live" naar "Omni DJ" (regel 8841) |
| `static/index.html` | CSS | `.auth-brand` v2: balk-gradient weg, wordmark-styling (regel 4943) |
| `static/index.html` | CSS | `.auth-tab.active` koppelen aan v2 active-pill (regel 4989) |
| `static/index.html` | CSS | tablist full-width flex:1 |
| `static/index.html` | JS | `setAuthTab` ook `aria-selected` syncen (regel 23917) |
| `static/index.html` | CSS | `.v2-modal-bg` default `display:none` voor legacy-mode (na regel 6827) |
| `static/index.html` | Copy | 4 "Clip Live" -> "Omni DJ" in 4 v2/legacy zinnen |
| `static/index.html` | Copy | 4 em-dashes verwijderd uit user-visible copy + 1 default-value |
| `static/index.html` | JS | Globale Escape-handler voor `.v2-modal-bg.on` (na `calCloseSchedule`) |

**Geen wijzigingen aan**: `app.py`, `cutter.py`, `auth.py`, `analyzer.py`, `launcher.py`, `build_macos.sh`, `start.sh`.

---

## OPEN ITEMS VOOR SJUUL'S REVIEW

### Aanbevolen vóór commit naar feature-branch
1. **Sidebar brand-row + browser title rebrand** (regel 8903 + `<title>` tag) — aparte rebrand-pass, samen met de andere "Clip Live" references in `launcher.py`, `app.py` titels, package metadata
2. **Logo-upload size cap** — voeg 2MB enforce toe in FileReader-flow voor `bs-logo-input`
3. **Brand-pack export data-URL strip** — handmatig 1 pack met logo exporteren, JSON inspecteren, beslissen of strip nodig is

### Aanbevolen vóór productie (omnidj.com)
4. **`?token=` URL-pattern vervangen** door Authorization-header via service-worker
5. **Backend route-audit** — review nieuwe sessie 56-57 write-routes voor `_require_authed_user()` decorator
6. **Tier-bypass server-side check** — wanneer multi-tenant Supabase live gaat, moet `OmniBrand.create()` ook server-side tier-gated zijn

### Niet kritisch
7. Insights mock-data inconsistentie (Best clip 810 views terwijl Published=0)
8. Responsive cross-check op 980px en <700px viewports
9. Cross-browser Safari check voor `:has()`, `aspect-ratio`, `gap` (allemaal Safari 15.4+ OK maar visueel verifiëren)

---

## WAT SJUUL NU MOET DOEN

### Stap 1 — Visuele finale check (5-10 min)
Open `http://127.0.0.1:5555` in Chrome (dev-server draait). v2-flag aan via console:
`localStorage.setItem('clipLiveRedesignV2','1'); location.reload();`

Doorloop: Analyse → Library → Brand → Social → Calendar → Insights → Auto-mode → Settings. Schakel ook v2 uit en check legacy-home (geen Schedule-post bug meer).

### Stap 2 — Git commit (5 min)
Alle wijzigingen zitten in `static/index.html`. Suggestie:
```
git add dj-clip-cutter/static/index.html SESSIE58-AUTONOMOUS-LOG.md
git commit -m "sessie 58: login-rebrand, v2-modal-bg legacy-fix, escape-handler, em-dash cleanup, watch-folder rebrand"
```
Branch: `feature/auto-mode-and-brand-redesign` (al actief).

### Stap 3 — PyInstaller rebuild (15 min, als alles groen)
```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
source venv/bin/activate
mv "/Applications/Clip Live.app" "/Applications/Clip Live.PRE-SESSIE58.app"
./build_macos.sh dmg
mv "dist/Clip Live.app" "/Applications/"
open "/Applications/Clip Live.app"
```

### Stap 4 — Rebrand-pass sidebar + bundle (aparte sessie 59)
Sidebar brand-row, browser title, app-icon, bundle-identifier, info_plist CFBundleName, README's. Ongeveer 4-6u sessie samen met Claude.

---

## TOEKOMSTIGE SESSIES

- **Sessie 59**: rebrand sweep + 3 niet-kritische fixes uit dit log
- **Sessie 60+**: Login/auth-overlay redesign pass 2 (diepere visuele hiërarchie, forgot-modal sync, wizard polish), omnidj.com koppelen via Cloudflare, Stripe live mode, Fase D-E-F van auto-mode plan (pipeline backend, review-flow, Postiz)

