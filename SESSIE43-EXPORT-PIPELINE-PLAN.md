# SESSIE 43 — Plan: Export-pipeline fix + modal-redesign (7 onderdelen)

> Datum: 2026-05-26 — uitgebreid in sessie 43 voorbereiding (Sjuul vroeg om visuele
> ratio-tiles, caption-toggle, watermark-toggle met inline upload, direct-to-folder,
> export-queue). Plus aparte sessie 44 voor selectie-balk in timeline.
> Status: Plan-document — nog niets geïmplementeerd
> Auteur: Claude (sessie 42 + uitbreiding sessie 43 voorbereiding)
>
> Aanleiding: drie originele blocker-onderwerpen + vier UX-uitbreidingen die
> dezelfde export-modal raken (alles in één refactor i.p.v. modal twee keer
> openbreken):
>
> 1. **Captions worden niet meegenomen in export** (KRITIEK, blocker voor users)
>    Sjuul testte: clip met text-layer → "Done" geklikt → Export → resulterende
>    mp4 bevat geen tekst. `_run_export_job` gebruikt bestaande `clip['files']`
>    paths zonder text_overlays.json te lezen.
>
> 2. **Rename-veld in export-modal** — gebruiker wil naam aanpassen op het
>    moment van exporten, niet vooraf via right-click rename.
>
> 3. **Filename op disk matcht UI-naam** — exports heten nu
>    `Drop_3__clip03__vertical__match.mp4` op disk. UI strippt dat al voor de
>    Library-card, maar in Finder/Explorer ziet de gebruiker de volle ruis.
>
> 4. **Visuele resolutie-tiles** — vervang ratio-dropdown door aanvinkbare
>    iconen (9:16 smal vertical, 16:9 breed horizontaal, 1:1 vierkant, 4:5).
>    Multi-select = exporteert per aangevinkte ratio één bestand.
>
> 5. **Caption + Watermark toggles** — losse switches in modal. Watermark-toggle
>    moet ook werken als gebruiker nog geen watermark in Brand Kit heeft —
>    inline upload-flow zonder modal te sluiten.
>
> 6. **Direct-to-folder** — kies output folder per export (default OUTPUT_DIR).
>
> 7. **Export-queue + loading bar** — bij meerdere clips × meerdere ratio's één
>    queue met simpele horizontale loading-bar onderaan scherm (X/Y clips · Z%).
>
> En parallel/erna: **Sessie 44 — Selectie-preview-balk** in timeline-editor.
> Zie onderdeel 8 onderaan dit document.

---

## Onderdeel 1 — Auto-bake captions in export (KRITIEK)

---

## Doel

- **Trim-knop** (`ed-trim-big` + `ed-trim-toolbar`, beide `editorTrimAtPlayhead()`)
  doet ENKEL het slicen van de video op de huidige in/out-tijden in de timeline.
  Geen layers, geen branding, geen text inbakken — alleen `ffmpeg -ss / -t`.
- **Export-knop** (`ed-export-btn` + `ed-export-selected` + `ed-export-all`)
  bakt automatisch alle layers in (text_overlays + brand_logo + watermark)
  vóór de uiteindelijke encode.

## Huidige situatie

`editorTrimAtPlayhead()` (frontend) → `/api/recut` (backend)
- Doet trim (in/out)
- Doet text_layers ffmpeg drawtext
- Doet brand_logo overlay
- Doet brand_watermark
- Doet pan/track keyframes
- Slaat resultaat op als `clip['files'][aspect]`

`/api/export` → `_run_export_job` (worker thread)
- Pakt `clip['files']` uit memory/snapshot
- Doet **geen** layer-injection — gebruikt de bestaande bestanden
- Re-encodet alleen met user-codec/fps/resolution

→ Gevolg: zonder Trim heeft de export-mp4 geen tekst.

## Stappen

### 1. Backend: nieuwe lichte recut-helper `_slice_only`

Splits de huidige recut-pipeline in twee functies:
- `_slice_only(clip, in_sec, out_sec)` — alleen `ffmpeg -ss / -t -c copy`
- `_recut_with_layers(...)` — de huidige volledige pipeline (blijft beschikbaar)

### 2. Backend: `/api/recut` → routeer op basis van caller-intent

Of nieuwe endpoint `/api/slice` voor trim-only. Frontend Trim-knop noemt
deze nieuwe endpoint.

### 3. Backend: `_run_export_job` voert pre-bake uit

Voor elke clip in de queue:
- Lees `text_overlays.json` van die job
- Lees `brand_kit.json` (logo, watermark, fonts)
- Als één van die niet-leeg is: roep `_recut_with_layers` aan vóór de
  reguliere export-encode. Schrijf naar tmp-pad, gebruik die als
  source voor de export.
- Anders: gewoon de bestaande `clip['files']` gebruiken (sneller pad).

### 4. Frontend: Trim-knop wisselt naar `/api/slice`

`editorTrimAtPlayhead()` aanpassen: roep een nieuwe `/api/slice` endpoint
aan ipv `/api/recut`. Hou bestaande recut-call beschikbaar voor de track-mode
preview ("Save & re-render" flow van Track-paneel).

### 5. Verificatie

- `python3 -m py_compile cutter.py app.py`
- Live test in Chrome:
  - Voeg tekst toe → Klik Trim → mp4 ververst MAAR ZONDER tekst (alleen geslicet)
  - Klik Export → output-mp4 HEEFT WEL tekst ingebakken
- Edge cases:
  - Clip zonder tekst → Export werkt zoals voorheen (geen extra recut)
  - Clip met tekst + brand-logo → beide aanwezig in export
  - Trim na text-toevoegen → tekst blijft als overlay zichtbaar in preview
    (huidige WYSIWYG-laag)
- Quota: één export-actie = één quota-tik (pre-bake is sub-stap, geen aparte tik)

## Geschatte effort

- Backend split: 1u
- Backend pre-bake in export-worker: 1u
- Frontend route-switch: 30m
- Smoketest + edge cases: 1u
- **Totaal: ~3,5u**

## Risico's

- **Track-mode** gebruikt nu ook `/api/recut` voor pan/keyframe-preview.
  Niet aanraken, alleen Trim-knop hoeft te switchen.
- **Brand watermark/logo** moet in de pre-bake mee. Bestaande recut-code
  heeft die al; we hergebruiken volledig.
- **Performance** voor power-users die 30 clips ineens exporteren met
  tekst-layers: 30× extra ffmpeg-pass = 1-2 minuten extra. Acceptabel
  (vs. nu Trim → wachten → Export = vergelijkbaar).

## Backups voor onderdeel 1

Vóór implementatie:
- `app.py.pre-sessie43-autobake.bak`
- `cutter.py.pre-sessie43-autobake.bak`
- `static/index.html.pre-sessie43-autobake.bak`

---

## Onderdeel 2 — Rename-veld in export-modal

### Doel
Bij klik op Export (toolbar of header-knop) toont de modal `pickExportSettings`
een tekstveld bovenaan: **"Bestandsnaam"**, vooringevuld met de huidige naam
(custom_label of fallback `Drop_3`). Gebruiker kan aanpassen of laten staan.

### Frontend wijzigingen (`static/index.html`)

1. HTML in `#export-settings-modal` rond regel 4930: nieuwe `<input type="text"
   id="exs-rename">` boven het codec-select.
2. `pickExportSettings(label, clip)` krijgt een tweede argument met de huidige
   clip-data zodat we de naam kunnen prefilllen.
3. Bij OK: als de input afwijkt van de oorspronkelijke naam, eerst
   `POST /api/rename/<job_id>` met `{clip_index, label}`, dan pas
   `/api/export/<job_id>` triggeren.
4. Voor multi-clip export (Export selected / Export all): rename-veld
   **verbergen** — alleen single-clip flow heeft het zinnig.

### Verificatie
- Single clip: rename via modal → export → mp4 op disk en in Library heet
  zoals de gebruiker tikte.
- Multi-clip: modal toont geen rename-veld.
- Cancel: rename-input niet gesubmit, geen `/api/rename` call.

### Effort: ~30-45 min

---

## Onderdeel 3 — Filename op disk schoner (zonder `__clip__...` ruis)

### Probleem
`_build_export_filename` produceert nu:
`{label}__clip{NN}__{aspect}__{codec}.mp4`

Het `__clip{NN}__` token is nodig voor de parser in `/api/exports`
(regel 5806) en in `renderExportCard` (frontend regel 5844). Die strippen
het wel voor de UI maar de echte filename op disk blijft `Drop_3__clip03__
vertical__match.mp4`.

### Voorgestelde aanpak
Sidecar-JSON: bij elke export ook een `<filename>.meta.json` schrijven met
`{clip_index, aspect, codec}`. De `_build_export_filename` produceert dan
schone namen `Drop_3_vertical.mp4` of `Drop_3.mp4` (codec en aspect alleen
in filename als er meerdere zijn).

### Backend wijzigingen
- `_build_export_filename` nieuwe signature die "minimale" naam genereert
- `_run_export_job` schrijft de sidecar mee na succesvolle encode
- `/api/exports` leest meta.json voor parse ipv regex op filename
- Backward-compat: filename met `__clip__` blijft parseerbaar (regex fallback)

### Verificatie
- Nieuwe export → bestandsnaam `Drop_3_vertical.mp4` (of `My Best Drop.mp4`
  bij rename)
- Library-card toont nog steeds correct
- Oude exports (pre-sessie43) blijven werken via fallback parser

### Effort: ~1u

---

---

## Onderdeel 4 — Visuele resolutie-tiles in export-modal

### Doel
Vervang de huidige ratio-dropdown door een rij aanvinkbare tiles met SVG-iconen.
Multi-select: elke aangevinkte ratio levert één export-bestand op (komt samen
met Onderdeel 7 — Export-queue).

### Tiles + iconen
- **9:16** — smal verticaal rechthoek-icoon (TikTok/Reels/Shorts)
- **16:9** — breed horizontaal rechthoek-icoon (YouTube landscape, LinkedIn video)
- **1:1** — vierkant icoon (Instagram feed)
- **4:5** — bijna-vierkant verticaal (Instagram feed portrait — meer real-estate
  in de feed dan 1:1)

Iconen zijn inline SVG (geen externe deps), monochroom met `currentColor`,
aangevinkte staat = accent-fill `#e8b766` (brand-amber).

### Frontend wijzigingen (`static/index.html`)
- HTML in `#export-settings-modal` (regel ~4930): nieuwe `<div class="exs-ratio-grid">`
  met 4 `<label class="exs-ratio-tile">` met `<input type="checkbox">` + inline SVG.
- CSS: grid-layout, hover-state, checked-state met amber-border + amber-fill.
- JS: `STATE.exportSettings.ratios = Set<string>` met `["9:16"]` als default.
  Toggle voegt/verwijdert uit Set. Bij OK: maak één export-job per ratio
  (queue handelt dit verder af).
- Backward-compat: oude `STATE.exportSettings.ratio` (string) blijft lezen,
  bij eerste open migreert naar Set.

### Verificatie
- 0 tiles aangevinkt → OK-knop disabled met tooltip "Selecteer minstens één formaat"
- 1 tile aangevinkt → werkt zoals nu (1 export-job)
- 3 tiles aangevinkt → 3 jobs in queue, bestanden krijgen aspect-suffix in naam
- Tile-clicks zijn pure toggles, geen radio-gedrag

### Effort: ~1u

---

## Onderdeel 5 — Caption + Watermark toggles in export-modal

### Doel
Twee losse switches in de export-modal die gebruiker per export-actie kan
bepalen, los van wat in Brand Kit is ingesteld.

### Caption-toggle
- Label: "Burn captions in"
- Default: **aan** (sluit aan bij Onderdeel 1 — auto-bake)
- Sub-select (alleen actief bij toggle on): "Style: TikTok / Subtitle / None"
  - Sluit aan bij bestaande caption-style logica in `cutter.py` text-layer renderer
- Off-state: text_overlays.json wordt door pre-bake in `_run_export_job` overgeslagen
  voor deze ene export

### Watermark-toggle
- Label: "Watermark"
- Default: **aan als watermark in Brand Kit aanwezig**, anders **uit**
- Drie scenario's:

**Scenario A — watermark al ingesteld in Brand Kit:**
Simpele toggle. Off = `_run_export_job` skipt `_build_watermark_overlay_segment`
voor deze export.

**Scenario B — toggle wordt aangezet maar nog géén watermark in Brand Kit:**
Modal toont inline panel: "Upload watermark (PNG met transparantie)" met
file-picker knop. Klik → bestaande native picker (`/api/pick-file` uit sessie 39)
→ POST naar bestaande `/api/brand-kit/watermark` endpoint (sessie 31).
Modal **blijft open**, toont kleine preview van geüploade watermark + position
controls (TR/TL/BR/BL, zelfde als Brand Kit). Toggle blijft on.

**Scenario C — toggle off:**
Geen verandering aan Brand Kit, alleen deze ene export krijgt geen watermark.

### Frontend wijzigingen (`static/index.html`)
- HTML in `#export-settings-modal`: nieuwe `<section class="exs-overlays">` met
  twee `<label class="exs-toggle-row">` (caption + watermark) + sub-panels
  die conditioneel verschijnen (`hidden` attribute toggling).
- Watermark sub-panel: file-picker knop + preview-img + position-radio-group.
  Hergebruik bestaande `_renderWatermarkPanel()` logica uit Brand Kit (extraheren
  naar shared helper).
- JS: `STATE.exportSettings.captions = {on: true, style: 'tiktok'}`,
  `STATE.exportSettings.watermark = {on: bool, justUploaded: bool}`.

### Backend
- `_run_export_job` leest beide flags uit job payload, geeft door aan
  `_recut_with_layers` als skip-flags. Geen nieuwe endpoints nodig
  — `/api/brand-kit/watermark` is herbruikt voor inline upload.

### Verificatie
- Toggle caption off → export-mp4 heeft geen tekst (zelfs als text_overlays.json bestaat)
- Toggle watermark off bij ingestelde Brand Kit → export-mp4 zonder watermark
- Geen Brand Kit watermark + toggle on → upload-flow opent inline → na upload
  preview zichtbaar → OK → export bevat watermark én Brand Kit heeft 'm nu staan

### Effort: ~1,5u (waarvan 45min inline upload-flow)

---

## Onderdeel 6 — Direct-to-folder optie

### Doel
Gebruiker kiest per export waar het bestand belandt, in plaats van altijd
`OUTPUT_DIR`. Default blijft `OUTPUT_DIR` zodat bestaand gedrag onveranderd is.

### Frontend wijzigingen (`static/index.html`)
- HTML: nieuwe rij in modal: "Save to: [pad-string-truncated] [Change…]"
- JS: `STATE.exportSettings.outputDir` (string of null voor default).
- Klik op "Change…" → POST `/api/pick-file?type=folder` (uitgebreid, zie backend).
- Klik op "Reset to default" (verschijnt als custom dir actief) → terug naar null.
- localStorage persist `clipLive.lastExportDir` zodat keuze sticky is per browser-sessie.

### Backend (`app.py`)
- Bestaande `/api/pick-file` endpoint (sessie 39, regel ~3200) uitbreiden:
  - Query param `?type=folder` → AppleScript `choose folder` ipv `choose file`
  - Tk-fallback: `filedialog.askdirectory()` ipv `askopenfilename()`
  - Returnt JSON `{ok: true, path: "/Users/..."}`
- `_run_export_job` payload accepteert `output_dir` (optioneel). Default = `OUTPUT_DIR`.
- Validatie: path moet bestaan en schrijfbaar zijn. Anders 400 met clear error.
- Veiligheid: path mag **niet** buiten user-home liggen (geen `/System/`, `/etc/`, etc.).
  Whitelist: `~/`, `~/Desktop`, `~/Documents`, `~/Downloads`, `~/Movies` of children daarvan.

### Verificatie
- Default-flow: niet kiezen → export landt in `OUTPUT_DIR` (zoals altijd)
- Custom folder → export landt daar, Library-card toont nog steeds correct
- localStorage sticky: tweede export onthoudt vorige keuze, toont 'm in modal
- Veiligheid: probeer `/etc/passwd` → 400 error in UI

### Effort: ~1u

---

## Onderdeel 7 — Export-queue + loading bar

### Doel
Bij export van meerdere clips × meerdere ratio's: één queue, één globale
progress bar onderaan scherm. User klikt OK in modal → queue start → kan
verder werken in de UI terwijl renders lopen.

### Frontend wijzigingen (`static/index.html`)
- Bestaande per-clip SSE-progress (regel ~5700) blijft werken voor individuele
  card-updates.
- Nieuwe globale `<div id="export-queue-bar">` fixed onderaan scherm:
  - Horizontale balk + tekst "Exporting 3/8 · 42%"
  - Cancel-knop rechts (stopt huidige worker, queue blijft daarop staan)
  - Bij 0 jobs in queue: `display:none`
- JS: `STATE.exportQueue = []` array van `{jobId, clipId, ratio, status, progress}`.
  Update via SSE-events per job, totaal-progress = avg van alle `progress` values.
- Bij OK in modal: pak alle aangevinkte clips × aangevinkte ratio's, push naar queue.
  Backend werkt sequentieel of parallel (zie backend-keuze hieronder).

### Backend — keuze gemaakt: Optie A (sequentieel) voor MVP

**Optie A — sequentiële worker (KIES DEZE voor sessie 43b):**
`_export_worker` pakt 1 job tegelijk uit de queue. Frontend ziet één bar met
sequentieel oplopende progress (1/6, 2/6, …). Simpel, stabiel, voorspelbaar
CPU-gebruik. ffmpeg is al multi-threaded dus single-worker benut alle cores.

**Optie B — parallelle workers (UITGESTELD naar latere sessie):**
N parallelle workers (N = CPU-cores - 1, cap op 3). Sneller bij veel kleine
clips. Risico: ffmpeg is al multi-threaded, parallellisme kan systeem
overbelasten (RAM-spikes, fan op max, mogelijk thermal throttling op MacBooks).
Vereist ook semafoor voor disk I/O en bredere SSE-aggregatie aan frontend-kant.

**Beslissing Sjuul (2026-05-26):** Begin met Optie A. Pas overstappen naar B
als gebruikers in praktijk klagen over export-snelheid bij grote queues. Aparte
sessie waardig — niet vermengen met sessie 43b.

- Cancel: nieuwe `/api/export/cancel/<job_id>` endpoint, kill subprocess, mark job failed.

### Verificatie
- 1 clip × 1 ratio → queue invisible (single export, geen bar nodig)
- 3 clips × 2 ratios = 6 jobs → bar verschijnt, telt af, verdwijnt bij 0 remaining
- Cancel mid-queue → huidige job stopt, rest blijft pending (user kan resume? — out of scope MVP, gewoon hele queue cancellen voor nu)
- Bar zichtbaar tijdens navigatie tussen views (Library / Settings) — staat
  echt fixed bottom

### Effort: ~1,5u

---

## Totale scope sessie 43

| Onderdeel | Tijd | Risico |
|---|---|---|
| 1. Auto-bake captions | 2-2,5u | Medium — raakt brand-pipeline |
| 2. Rename-veld modal | 30-45min | Laag |
| 3. Filename op disk | 1u | Medium — backward-compat moet kloppen |
| 4. Visuele ratio-tiles | 1u | Laag |
| 5. Caption + watermark toggles + inline upload | 1,5u | Medium — inline upload-flow nieuwe interactie |
| 6. Direct-to-folder | 1u | Laag — bestaande pick-file uitbreiden |
| 7. Export-queue + loading bar | 1,5u | Medium — meerdere SSE-streams aggregeren |
| Verificatie + smoketest | 1u | Laag |
| **Totaal** | **~10-10,5u** | |

Verdeling over meerdere sessies aanbevolen. Voorstel:
- **Sessie 43a:** onderdelen 1+2+3 (backend-fix + rename + filename, ~4-4,5u)
- **Sessie 43b:** onderdelen 4+5+6+7 (modal-redesign + queue, ~5,5-6u)

---

## Onderdeel 8 (Sessie 44) — Selectie-preview-balk in timeline-editor

### Doel
Horizontale balk onderaan de timeline-editor die verschijnt zodra ≥1 clip
geselecteerd is, en de geselecteerde batch visueel toont. Verdwijnt zacht
als selectie leeg is.

### Per clip-tile in de balk
- **Mini-thumbnail** (~80×60 px, hergebruik bestaande `clip.thumbnail_url`)
- **Naam-label** onder thumb: `Drop #3` of custom-label
- **Tijdmarker** rechts of onder thumb: `@ 12:34` (positie in originele set,
  format `MM:SS` of `H:MM:SS` voor sets >1u)
- **Hover-scrub:** mouse-over op thumb scrubt 3-4 frames van die clip
  (preload kleine sprite-sheet of poll bestaande clip via `<video>` element
  met seekable thumbnail-segment — onderzoeken in implementatie-fase)
- **Hover-×:** klein kruisje rechtsboven verschijnt op thumb-hover. Klik →
  deselecteer die clip uit batch (clip blijft in Library, alleen niet in batch).

### Frontend wijzigingen (`static/index.html`)
- HTML: nieuwe `<div id="selection-preview-bar">` fixed onderaan editor-view
  (boven `#export-queue-bar` als die ook actief is).
- CSS: slide-up animatie bij verschijnen, slide-down bij leeg worden.
  Donker-thema (passend bij editor), max-height 120px.
- JS: bestaande `STATE.selectedClips` (Set<string>) is single source of truth.
  Nieuwe `_renderSelectionBar()` luistert op selectie-mutaties (centraal
  via bestaande `_onSelectionChange()` hook of nieuwe `Proxy`).
- Hover-scrub: lazy load `<video preload="metadata" src=clip.url>` per thumb,
  alleen actief tijdens hover. Cleanup op mouseleave om geheugen te sparen.

### Geen backend-wijzigingen nodig
Alle data al beschikbaar in bestaande clip-objects.

### Verificatie
- 0 selectie → bar onzichtbaar
- 1 selectie → bar verschijnt met 1 tile
- Deselect via × → bar update, clip verdwijnt uit batch
- Selecteer alles (20+ clips) → bar scrollt horizontaal
- Hover-scrub werkt zonder lag op test-set Lisa Korver (1080p source)
- Geen geheugenlek bij veel hover-events (devtools memory snapshot)

### Effort: ~3-4u (waarvan 1u hover-scrub research/implementatie)

### Backups voor sessie 44
- `static/index.html.pre-sessie44.bak`

---

## Volgorde-aanbeveling

1. **Sessie 43a** (4-4,5u): onderdelen 1+2+3 — backend-fix + rename + filename
2. **Sessie 43b** (5,5-6u): onderdelen 4+5+6+7 — modal-redesign + queue
3. **Sessie 44** (3-4u): onderdeel 8 — selectie-balk

Totale tijdsinvestering: ~13-14u verspreid over 3 sessies.

Na elke sessie: HANDOVER.md update + backups archiveren.
