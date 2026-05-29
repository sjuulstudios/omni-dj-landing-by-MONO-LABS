# Plan 2026-05-28: Feature cleanup + UI compact + auth-incident

> Sjuul's lijst van 28 mei middag, in 14 items. Volgorde: kritiek > quick wins > plannen.

## STATUS

- KRITIEK: auth-incident (item 14) — in onderzoek nu
- QUICK WINS: items 1-12 (UI cleanup, filters weg, lay-out shifts)
- PLANNEN VEREIST: items 11, 12, 13 (Brand visueel, Social visueel, Insights uitbreiding)

---

## ITEM 1 — Clips view: scrubbable mini-timeline per clip

**Wens:** in de bibliotheek heeft elke clip onderin een mini-timeline-strip. Bij klikken ergens op die strip moet de clip vanaf dat punt afspelen.

**Huidige staat (te verifiëren):** ik weet niet of er nu al een mini-timeline-strip onderin de clip-tiles staat in Library, of dat het filmstrip-row is in editor. Eerst inspecteren.

**Vragen open:** is het de filmstrip-row in editor of een per-tile mini-strip in library?

**Plan:** 
1. Lokaliseren huidige library-tile markup
2. Mini-timeline-canvas of `<div>` met click-handler -> `video.currentTime = (clickX / barWidth) * video.duration`
3. Visueel: dunne 4px bar, hover toont currentTime tooltip

---

## ITEM 2 — Drops-filter verwijderen

**Wens:** Drops-filter mag eruit, want All toont toch alle drops.

**Wacht-vraag voor Sjuul:** Als de set ook Buildups bevat, toont 'All' die ook? Dan is Drops niet redundant maar wel handig om alleen drops te zien. **Of bedoel je**: jouw sets bevatten alleen drops, dus All == Drops?

**Aanname tot Sjuul reageert:** ik verwijder Drops-filter zoals gevraagd. Eenvoudig: DOM-knop weg + JS-handler bestaat al voor All.

---

## ITEM 3 — 404 op gerenderde clip + auth-incident KRITIEK

Apart blok onderaan: zie ITEM 14.

---

## ITEM 4 — Edit/Style/Brand-knoppen weghalen uit editor-header

**Wens:** rechtsboven in editor zie je nu `Edit · Style · Brand` toggle. Allemaal weg:
- Edit: redundant (je bent al in edit)
- Style: zit al in Text-knop in rechter rail
- Brand: zit al als losse pagina in sidebar

**Plan:** DOM-block met deze 3 knoppen verwijderen + bijbehorende JS-handlers cleanen. Check eerst of geen andere code afhankelijk is.

---

## ITEM 5 — Cue points header + 23 cues + divider weg

**Wens:** in editor links de "Cue points 23 cues · —" header weg + de smalle divider eronder. De filters (All 23 / Favourites / Renamed) schuiven omhoog naar de top van de linker-rail.

**Plan:** DOM-cleanup links pane editor, padding-top reset.

---

## ITEM 6 — Aspect-ratio filters: 9:16, 16:9 uitbreiden met 1:1 en 4:5 in Library

**Wens:** Library view aspect-toggle moet 4 opties hebben ipv 2.

**Wacht-vraag voor Sjuul:** Is "4:4" een typo? Bedoel je 4:5 (Instagram post) of echt 4:4 (vierkant — dan = 1:1)? Ik ga uit van **1:1 (square) + 4:5 (portrait)** als nieuwe opties. Klopt dat?

**Plan:** chip-row uitbreiden + filter-logica aanpassen.

---

## ITEM 7 — "Sorted by energy score" tekst weghalen

**Wens:** weg.

**Plan:** 1-liner DOM-fix.

---

## ITEM 8 — "+ New set" knop in Library weghalen

**Wens:** weg.

**Plan:** 1-liner DOM-fix. Check of er een Analyse-CTA terugkomt in plaats van de New-set knop. Anders gebruiker kan niet snel een nieuwe set toevoegen vanuit Library — moet via Analyse-tab. Acceptabel.

---

## ITEM 9 — Edit Selected -> multi-clip Timeline Editor

**Wens:** bij ≥2 geselecteerde clips in Library, klik "Edit selected" → opent Timeline Editor met alle selected clips. Text en Brand-edits die je daar toepast moeten op alle clips landen, ook al zie je maar 1 video in viewport.

**Plan (groot item, multi-step):**
1. Edit-selected-flow: check huidige implementatie
2. State-model: STATE.selectedClips wordt overlay-edit-state
3. Text + Brand edits gebroadcast naar alle indices ipv 1 active clip
4. Visueel: thumb-strip onderaan editor toont de selected clips, klik = swap viewport
5. Export-flow: opent al per-clip, dat blijft

**Risico:** veel state-mutatie. Aparte sessie aanbevolen.

---

## ITEM 10 — Watermark position picker per aspect-ratio

**Wens:** in Brand > Watermark > Position. Geef per ratio/resolutie een aparte position-picker (zoals de huidige 16:9 grid).

**Plan:** Brand-state-model uitbreiden:
```
watermark.position_by_aspect = {
  '9:16': 'br',
  '1:1':  'br',
  '4:5':  'br',
  '16:9': 'br'
}
```
DOM: 4× position-grid ipv 1 (compacter: tabs of side-by-side).

---

## ITEM 11 — Brand-page visueel/compact (plan-vereist)

**Wens:** zie volgende sectie "PLAN-A — Brand visueel".

---

## ITEM 12 — Social-page visueel/persoonlijker (plan-vereist)

**Wens:** zie volgende sectie "PLAN-B — Social".

---

## ITEM 13 — Calendar fixes

**Wens:**
1. Zondag valt weg uit view → fix
2. Compact binnen pagina
3. Scrollbars wit/grijs → platform-stijl (donker met accent)

**Plan:** CSS-fixes. Grid-template-columns 7-eq, scrollbar-color CSS-var override.

---

## ITEM 14 — Insights uitbreiding (plan-vereist)

**Wens:** zie volgende sectie "PLAN-C — Insights".

---

# AUTH-INCIDENT — KRITIEK ONDERZOEK

**Sjuul's melding:** "Het platform is ingelogd in een ander account. Ik zie dit aan de Library met sets van een andere user. Dit MAG ABSOLUUT NIET."

**Wanneer:** zojuist, in de huidige dev-server sessie.

**Vragen die ik wil beantwoorden:**
1. Welk account is nu actief volgens Supabase JWT in localStorage?
2. Welke user_id staat in de JWT?
3. Welke sets retourneert `/api/history`? Filtert die op user_id of toont 't alles?
4. Wanneer is er ge-switched? Track-event in console?
5. Token-pollutie van vorige test-acties (mock-data, fake-job-id)?

**Verdachte momenten in deze sessie:**
- Mijn fake STATE.clips inject (in Chrome console) zou STATE kunnen polluten maar geen JWT-impact
- Auth-overlay manueel verbergen heeft een refresh-token-pad kunnen activeren
- Multiple Chrome-tabs naar 127.0.0.1:5555 met verschillende sessions

**Volgorde diagnose:**
1. Live: leesout JWT uit localStorage, decode payload
2. Live: `/api/auth/me` aanroepen, vergelijk met Sjuul's verwachte user
3. Backend: code-review op `/api/history` en `/api/clip` voor user-id filtering
4. Backend: token-validatie-flow audit

**Plan tot fix:** afhankelijk van root cause:
- A) Frontend: state-leak tussen sessies (bv. localStorage niet gecleared bij login-switch)
- B) Backend: route serveert per ongeluk andere user's data (RLS-bypass)
- C) Token-mix: oude token in cookie vs. nieuwe in localStorage
- D) Path-traversal in `/api/clip/<jobId>/...` (zou clip-files van andere users blootleggen)

Worst case is D. Pas RLS toe in de file-serving endpoints + check job-ownership voor elke clip-request.

---

# PLAN-A — Brand-page visueel compact (geen code zonder Sjuul's OK)

**Doelen Sjuul:**
- Logo's beter in beeld
- Sectie-grenzen duidelijker
- Compacter, secties naast elkaar
- Geen lange sliders

**Voorstel layout:**

```
[ Brand-pack dropdown ] [ Export ] [ Import ]   <- sticky top

╔═══════════════════════════════════════════════╗
║  HERO   "Your sound, your look."  + sub-text  ║
╚═══════════════════════════════════════════════╝

┌── BRAND KIT ──┐  ┌── WATERMARK ──┐
│ Logo preview  │  │ Watermark on/off
│ Accent color  │  │ Text input
│ Secondary     │  │ Color + size
│ Position grid │  │ Position-by-aspect (4 mini grids)
└───────────────┘  └────────────────┘

┌── CAPTION PRESETS ──────────────┐
│ [+ New preset]  [presets row 4 cols]
│ Default for Auto-mode: dropdown
└──────────────────────────────────┘

┌── CLIP TEMPLATES ─────┐ ┌── HOOKS ────┐ ┌── CTAs ──┐
│ TikTok / IG / YT etc. │ │ tags-input  │ │ tags-in  │
└───────────────────────┘ └─────────────┘ └──────────┘

┌── CAPTION COPY ────────────────────────────────────┐
│ 2x2 grid: TikTok / Instagram / YouTube T+D / X
└────────────────────────────────────────────────────┘

┌── HASHTAG SETS ──┐ ┌── STICKERS + LOWER-THIRDS + INTRO/OUTRO ──┐
│ named sets       │ │ compact card row                            │
└──────────────────┘ └─────────────────────────────────────────────┘
```

**Sliders vervangen:**
- Logo opacity (range 20-100) → 3 segmented chips: 40% / 70% / 100%
- Logo size (5-20%) → 3 chips: S / M / L (map naar 8/12/18%)
- Watermark size → idem

**Logo prominenter:**
- Brand Kit card krijgt linker-helft de logo-preview groot (240×240 dropzone), rechter-helft de accent + position + sliders-naar-chips.

**Implementatie-tijd schatting:** 4-6 uur dev. Aparte sessie aanbevolen.

---

# PLAN-B — Social visueel + profielfoto's

**Doelen Sjuul:**
- Visueler
- Persoonlijker: profielfoto's gekoppelde accounts ipv platform-icoontjes

**Voorstel:**

```
Connected accounts:
┌──────────────────┐  ┌──────────────────┐  ┌─...──┐
│  [avatar 56px]   │  │  [generic-icon]  │
│  @sjuulstudios   │  │  Connect TikTok  │
│  TikTok · 12.4K  │  │  Postiz coming   │
│  ▲ +120 last 7d  │  └──────────────────┘
└──────────────────┘
```

- Avatar = ronde 56px met platform-badge linksonder (mini-icoon)
- Niet-gekoppeld → grijze placeholder met "Connect" CTA
- Followers + engagement + delta week-over-week
- Recent posts blijft, maar tiles krijgen platform-badge linksonder ipv text

**Profielfoto-bron:** via Postiz-API zodra gekoppeld. Tot die tijd: placeholder-avatar met initials.

**Implementatie-tijd:** 2-3 uur (mock-data nu, echte API later via Postiz).

---

# PLAN-C — Insights uitgebreid

**Doelen Sjuul:**
- Detail per post: hoe goed presteert het?
- Accountgroei per platform
- Optie om platform toe te voegen als nog niet gekoppeld

**Voorstel layout:**

```
[ 7d / 30d / 90d ]   [ Account: all v ]

┌── Account growth per platform ────────────────────┐
│  Line chart, 4 lines (TT/IG/YT/X), followers over time
└────────────────────────────────────────────────────┘

┌── KPI cards ─────────────────────────────────────┐
│ Total views | Engagement | Posts | Reach
└───────────────────────────────────────────────────┘

┌── Top performing clips ──────────────────────────┐
│  Table: thumb · clip-name · platform · views · likes · shares · % engagement
│  Sortable headers
└───────────────────────────────────────────────────┘

┌── Per-post detail (drill-down) ───────────────────┐
│  Click row above → modal/sidebar met:
│    - full-size preview
│    - performance chart (hourly views)
│    - audience demographics if API levert
│    - copy-link + reschedule actions
└───────────────────────────────────────────────────┘

┌── Connect more platforms ─────────────────────────┐
│  Empty-state cards voor niet-gekoppelde platforms
│  Compact CTA "Connect Spotify / SoundCloud / etc."
└────────────────────────────────────────────────────┘
```

**Data-bron:** alles via Postiz analytics-API (post-mockup-phase). Voor v1 demo: deterministic mock-generator (zoals nu) maar uitgebreid met growth-data per platform.

**Implementatie-tijd:** 5-8 uur (vereist line-chart met 4 series, sortable table, drill-down modal).

---

# AANBEVOLEN VOLGORDE VAN UITVOERING

1. **NU — Auth-incident diagnose** (kritiek)
2. **NU — Quick wins batch** (items 2, 4, 5, 7, 8, 13 — UI cleanup wat geen plan vereist)
3. **Apart, sessie 59 — Items 1, 6, 9, 10** (kleine maar wel werk)
4. **Sessie 60+ — Plan A** (Brand visueel) na Sjuul's OK
5. **Sessie 60+ — Plan B** (Social) na Sjuul's OK
6. **Sessie 61+ — Plan C** (Insights) na Sjuul's OK + Postiz API klaar
