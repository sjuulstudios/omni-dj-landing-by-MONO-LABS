# Clip Live — Redesign Migration Plan
**Datum:** 2026-05-26
**Bron-design:** `clip-live-redesign-v2.html` (akkoord van Sjuul gekregen)
**Bron-design-systeem:** `PLAN-REDESIGN-2026-05-26.md`
**Target:** `dj-clip-cutter/static/index.html` (16.096 regels) + uiteindelijk .app/.dmg rebuild

---

## 1. Eerlijke complexiteit-check

| Metriek | Waarde |
|---|---|
| Regels in `static/index.html` | 16.096 |
| Bytes | 728.985 |
| Unieke DOM-IDs in HTML | 336 |
| `getElementById`-calls in JS | 240 unieke targets |
| Top-level functies | 236 |
| `onclick=` attributen | 79 |
| `addEventListener`-calls | 208 |
| Unieke `/api/*`-endpoints aangeroepen | 40+ |
| Backups van eerdere sessies aanwezig | 7 (pre-sessie40 t/m pre-sessie44) |

**Conclusie:** een full rewrite-in-één-sessie is technisch niet haalbaar zonder bestaande flows te breken (auth, upload, processing-polling, recut, /api/slice, /api/export, brand stack, fonts, watermark, queue, selectie-balk). De redesign **moet** in fases.

**Status sessies 43+44 (gedubbelcheckt 2026-05-26):**
- ✓ `/api/slice` endpoint live (`app.py:4405`)
- ✓ `_run_export_job` doet auto-bake via `text_overlays.json` (`app.py:5719+`)
- ✓ `/api/rename/<job>` endpoint live (gerefereerd in `index.html:8671`)
- ✓ `#exs-rename` input in modal (`index.html:5196`)
- ✓ Ratio-tiles CSS+HTML (`index.html:402+`)
- ✓ Folder-whitelist actief met 4 paden ~/Desktop, ~/Documents, ~/Downloads, ~/Movies (`app.py:6098`)
- ✓ Frontend folder-picker (`index.html:5271`)
- ✓ Selectie-balk `#selection-preview-bar` + `_renderSelectionBar` (`index.html:544`)
- ✓ Backups bestaan: `app.py.pre-sessie43-autobake.bak`, `cutter.py.pre-sessie43-autobake.bak`, `static/index.html.pre-sessie44.bak`
- 🟡 **Smoketests (Sjuul, ~45min) staan nog open** — Sjuul kiest expliciet om dit te skippen en door te gaan op eigen risico

---

## 2. Strategie: 5 fases, elk afzonderlijk testbaar

Elk fase eindigt met een werkende app. Geen fase is afhankelijk van een opvolgende. Tussen de fases zit een testpunt waar je in `./start.sh` kunt controleren of bestaande flows nog werken.

### Fase 1 — Design tokens + app shell *(deze sessie)*
**Tijd:** ~3-4u
**Risico:** Laag (alleen CSS + nieuwe wrapper-DOM, géén bestaande IDs aangeraakt)

**Wat verandert:**
- Top in `<style>`: design tokens (kleuren/typografie/spacing/radii uit v2)
- Nieuwe `<aside class="sidebar-v2">` met workspace-switcher, 5 nav-items (Clips/Brand/Social/Calendar/Insights), settings-footer
- Nieuwe `<header class="topbar-v2">` (52px, breadcrumb + search + new-clip-CTA)
- Body krijgt class `redesign-v2` als feature-flag
- Alle bestaande views (dashboard, editor, modals) worden gewrapped in `<main class="content-v2">` maar **behouden hun originele DOM-IDs en JS-handlers**
- Sidebar-nav-items doen wat de bestaande tab-switcher doet (show/hide van bestaande view-divs)

**Wat NIET verandert:**
- Geen bestaande IDs hernoemd
- Geen JS-functies herschreven
- Geen API-calls aangepast
- Geen Python-code aangeraakt

**Testpunten na Fase 1:**
1. Login + signup werken
2. Upload-flow werkt
3. Processing polling werkt
4. Dashboard toont clips
5. Editor opent, trim werkt
6. Export-modal opent met ratio-tiles + folder-picker
7. Selectie-balk verschijnt onderin bij selectie
8. Brand Stack opent (oude modal, nieuwe sidebar-link)

### Fase 2 — Dashboard / Clips-grid herschilderen
**Tijd:** ~3-4u
**Risico:** Middel — clip-cards krijgen nieuwe HTML, JS render-functies moeten meebewegen

**Wat verandert:**
- `renderDashboard()` produceert v2-style clip-cards (9:16-thumb, BPM-badge, type-pill, hover-select)
- Filter-chips boven grid in v2-stijl (All/Drops/Build-ups/Vocals)
- Aspect-ratio toggle (9:16 / 16:9) als pill-group

**Risico-punten:**
- Bestaande `data-*` attributen die hover-scrub aansturen moeten blijven
- Selectie-toggle koppeling (`toggleClipSelect`) moet identiek functioneren

### Fase 3 — Editor / Timeline polish
**Tijd:** ~4-5u
**Risico:** Hoog — de editor is de complexste view (timeline, waveform, BPM, text-layers, brand stack)

**Wat verandert:**
- Editor-shell, niet de canvas-logic
- Drawers (track / text / brand) krijgen v2-styling
- Knoppen-toolbar consistent met v2-buttons

**Wat NIET verandert:**
- Waveform-rendering
- BPM-detectie UI
- Trim-handles (kritiek pad sessie 43a)
- `/api/recut`, `/api/slice`, `/api/text-overlay`-flows

### Fase 4 — Modals + overige schermen
**Tijd:** ~3-4u
**Risico:** Middel

- Auth-modals (login/signup/forgot/reset) → v2-stijl
- Upgrade-modal → v2-stijl
- Onboarding-wizard → v2-stijl
- Brand Stack modal → v2-stijl (binnen nieuwe Brand-sidebar-tab)

### Fase 5 — Calendar + Social + Insights (lege placeholders → echte schermen)
**Tijd:** afhankelijk van features
**Risico:** Laag voor placeholders, hoog voor echte features

Placeholders direct meeleveren in Fase 1 (zoals in v2-mockup). Echte invulling = nieuwe sessies.

---

## 3. Per-fase rebuild-strategie naar .app

| Na fase | Rebuild .app? | Reden |
|---|---|---|
| Fase 1 | Optioneel — pas als design-tokens + shell goed voelen | Cosmetic + sidebar werkt |
| Fase 2 | Aanrader | Dashboard is hoofdscherm, premium-gevoel daar is meeste impact |
| Fase 3 | Aanrader | Editor is langste interactie |
| Fase 4 | Aanrader | Auth + onboarding zien nieuwe users |
| Fase 5 | Pas bij echte features |

Per rebuild: `LESSONS-LEARNED.md` raadplegen voor de PyInstaller-procedure + Gatekeeper-stappen.

---

## 4. Backups & versiebeheer

**Vóór Fase 1 (gedaan vandaag):**
- `static/index.html.pre-redesign-v2.bak` (728.985 bytes, identiek aan huidige stand)

**Vóór elke volgende fase:**
- `static/index.html.pre-redesign-fase{N}.bak`

**Rollback-procedure:**
```
cd dj-clip-cutter
cp static/index.html.pre-redesign-v2.bak static/index.html
./start.sh
```

---

## 5. Wat we **niet** doen in dit migratiepad

- Geen wijzigingen aan `app.py`, `analyzer.py`, `cutter.py` (puur frontend)
- Geen nieuwe API-endpoints (alles loopt op bestaande backend)
- Geen light-mode (komt later, na launch)
- Geen feature-flag-frameworks (alleen één body-class `redesign-v2`)
- Geen wijzigingen aan PyInstaller-spec (UI verandert, niet de packaging)

---

## 6. Acceptatiecriteria per fase

Fase is "klaar" als:
1. Bestand parseert (geen JS-errors in DevTools console)
2. App start zonder errors via `./start.sh`
3. Alle testpunten van die fase groen
4. Backup is gemaakt en gedocumenteerd in HANDOVER.md
5. Geen regressie op functionaliteit van vorige fase

---

## 7. Wat ik NU ga doen (deze sessie)

1. ✓ Inventory (gedaan — 336 IDs, 240 JS-targets, 40+ endpoints geïdentificeerd)
2. ✓ Backup `static/index.html.pre-redesign-v2.bak` (gedaan)
3. ✓ Dit migratieplan (deze file)
4. → **Fase 1 bouwen**: design tokens + sidebar + topbar + content-wrapper
5. → Verificatie: parse-check, geen brekende JS-errors
6. → HANDOVER.md update met status

**Tijd-schatting Fase 1 vanaf nu:** 2-3u puur uitvoeren.

**Niet vandaag (op basis van scope):**
- Fase 2-5 — die komen in volgende sessies
- PyInstaller-rebuild naar .app/.dmg — die volgt **na** Fase 2 als je het echt premium wilt voelen in de gebouwde app

---

## 8. Beslissing rebuild naar .app/.dmg

Een .app bouwen op alléén Fase 1 = sidebar + topbar premium, content nog oude stijl. Dat is een halfslachtig product om aan testers te geven.

**Mijn aanbeveling:** wacht met .app-rebuild tot minimaal **na Fase 2** (dashboard/clips-grid). Pas dan voelt de tool écht "nieuwe stijl" bij eerste indruk.

Als je hier anders over denkt — bv. "ik wil nu een .app om door collega's te laten zien, ook al is editor nog oude stijl" — dan kan dat, maar zeg het zodat ik daar de rebuild-stappen aan toevoeg.
