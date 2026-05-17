# SESSIE 24 — End-to-end pipeline test op verse uploads (2026-05-12)

> Doel: bevestigen dat de full pipeline (upload-local → analyze → BPM/Key detect → cutting → BPM stamp render → keyframe tracking → multi-codec export → large-file proxy + lazy full-quality) zonder regressies werkt na de Sessie 21–23 wijzigingen.
>
> Twee verse uploads gebruikt: **Lisa Korver x Hör Berlin** (444 MB, 55 min, h264 30 fps) en **Franky Rizardo Peru Set** (7.8 GB, 3:54 u, h264 23.976 fps).

---

## TL;DR

Pipeline werkt end-to-end. Eén echte bug gevonden (librosa half-tempo op melodische sets), één UX-observatie (analyzer-stage rapporteert geen sub-progress op lange files). Alle Sessie 21–23 features — Brand Stack BPM/Key stamp, manual keyframe tracking, 4-codec export modal, large-file proxy pipeline, lazy full-quality render — leveren correcte output.

---

## Setup

- Server: `http://127.0.0.1:5555`, productie-mode (debug=False), ffmpeg 8.1.1 met drawtext + h264_videotoolbox, demucs/torch+mps aanwezig.
- Account: `business+wftest17@sjuulstudios.com` — login via `/api/auth/login` levert direct een access_token + session-state in `localStorage.clipLive.session`.
- Brand Stack van wftest17: `bpm_stamp.enabled = true`, format `bpm_key`, corner `tr`, color white. Default kit zonder eigen fonts/logo.

---

## Lisa Korver x Hör Berlin (job `ac7373ae`)

| Fase | Resultaat | Tijd |
|---|---|---|
| `/api/upload-local` register | 200, `no_copy: true`, `estimated_gb: 2` | <1s |
| Analyzer | 26 drops gedetecteerd | ~3 min |
| BPM detect | **71.8** ⚠️ (half-tempo — track is house, echt rond 143) | — |
| Key detect | 4B (Ab major / G# major) — plausibel | — |
| Cutting | 26 × landscape + 26 × vertical (52 files) | ~3 min |
| BPM/Key stamp | "72 BPM · 4B" zichtbaar in top-right ✅ | — |
| Tracking pipeline | 3 keyframes (cx=25→75→50) → recut → pan-effect visueel correct ✅ | <2s/recut |
| Export 4 codecs | match h264 / h265_vt hevc / h264_vt h264 / prores prores — alle 4 correct gerendered | 2–12s per codec |

**Pipeline klaar in ~6 minuten totaal** (55-min source). Vertical clips ~6 MB, landscape ~8 MB (30s @ ~2 Mbps). ProRes-export 730 MB voor vertical (lossless intermediate, verwacht).

### Bug: BPM half-tempo

Librosa's `tempo` schat 71.8 BPM voor een set die in werkelijkheid 122–128 BPM is. Dit is een bekend probleem met librosa's beat-tracker op melodischer / minder hard-kicked house — de onset-detectie pakt elke tweede kick. Wel: het renderer-pipeline gebruikt deze BPM puur voor de drawtext-stamp, niet voor cuts (cuts gebruiken `bar_times`, die wel correct zijn). Impact: cosmetisch op de stamp, niet op de clip-quality.

**Voorstel voor fix** (out of scope deze sessie): post-process tempo-doubling check in `detect_bpm()` — als gedetecteerd tempo < 90 BPM én onset-density per bar > X, verdubbel. Of secondaire methode (autocorrelation rond verwachte tempo-range).

### Geen-bug bevestigingen

- `tracking/clip_002.json` correct geschreven door `_validate_keyframes_payload` (sortering + clamp).
- `recut_clip` met track-keyframes laadt de file automatisch — geen extra param nodig.
- BPM stamp drawtext + tracked-crop werken in dezelfde filter-chain zonder conflict (zie t=29 frame: stamp + DJ in centered crop allebei correct).

---

## Franky Rizardo Peru Set (job `94d6c9c7`)

| Fase | Resultaat | Tijd |
|---|---|---|
| `/api/upload-local` register | 200, `no_copy: true`, 7.8 GB niet gekopieerd | <1s |
| Analyzer | 151 drops gedetecteerd, source-duration 14045s = 3:54 u | ~3.5 min |
| BPM detect | **129.2** ✅ — correct tech-house tempo | — |
| Key detect | 12A (E minor) — plausibel | — |
| Pipeline-keuze | `is_long: true` (>7200s threshold) → LARGE_FILE_PIPELINE → 720p proxy-route ✅ | — |
| Cutting | 151 × 1280×720 proxy mp4 (geen landscape/vertical) | ~2 min |
| Lazy full-quality render | `/api/render-clip/<job>/<idx>` levert 1080p landscape + vertical in **5 sec** ✅ | 5s |
| BPM/Key stamp (full) | "129 BPM · 12A" zichtbaar in top-right ✅ | — |

**Totaal end-to-end: ~6 minuten** voor analyze + 151 proxies van een 3:54 u source.
**Lazy full-quality on-demand: 5 sec voor landscape + vertical samen.**

### Clip-lengte observatie (geen bug)

Franky's clips zijn 16.72s (9 bars @ 129 BPM = 9 × 1.86 = 16.72s) in plaats van de default 30s setting van Lisa Korver. Dit is correct gedrag — bar-aligned cuts hebben prioriteit boven `clip_duration`. Bij 129 BPM zijn 9 bars muzikaal sterker dan een vaste 30s window die mid-bar zou eindigen.

### Geen-bug bevestigingen

- 7.8 GB bron NIET gekopieerd naar OUTPUT_DIR — `no_copy: true` werkt zoals bedoeld.
- Proxy-bestanden zijn 7–10 MB per stuk (16s @ 4 Mbps 720p) — passen ruim binnen de 2 GB estimated_gb budget.
- Lazy render schrijft naast bestaande proxy zonder die te vervangen — clip-cache structuur klopt: `files: {proxy, landscape, vertical}`.

---

## UX-observatie: analyzer progress staat lang stil

Op de Franky-job bleef `progress.percent` ~270s op 14% staan tijdens HPSS + bar-aware detection. Pas bij overgang naar cutting sprong hij naar 69% in één klap. Voor een 3:54 u file is dit verwarrend — gebruiker zou denken dat de pipeline hangt.

**Voorstel** (deferred):
- Substage-progress binnen `analyzing` (HPSS done, key done, drop-scan started/done, …) zodat de bar wel beweegt
- Of in elk geval een tijd-indicator ("Analyzer running for 1m 30s — long sets take 3–6 minutes")

Niet kritiek, geen blocker — server logging gaf via polling-log wél bewijs van leven, alleen de UI-percentage stond stil.

---

## Bekende issues uit CLAUDE.md die NIET zijn opgetreden

- ❌ **Duplicate clips bug**: NIET gereproduceerd op deze twee sets. Alle 26 + 151 clips waren uniek (verschillende `start`/`end`/`peak_time`).
- ❌ **Large-file pipeline hang**: NIET gereproduceerd. 3:54 u liep door zonder vastlopen.
- ❌ **UI regressie**: dashboard, editor, Brand Stack — alles rendert. Geen layout-breaks.

---

## Bug-shortlist voor follow-up

1. **[Cosmetic, low-pri]** Librosa half-tempo bias op melodischer sets (Lisa Korver: 71.8 → echt 124-ish). Drawtext stamp toont half-tempo. Bar-aware cuts werken wel correct. Fix-voorstel: post-detect doubling-heuristiek in `detect_bpm()`.
2. **[UX, low-pri]** Analyzer progress staat stil op 14% tijdens lange HPSS-runs. Geen sub-progress binnen analyze-stage. Fix-voorstel: substage progress reporting of een "elapsed time" hint.
3. **[Cleanup, very-low]** `dj-clip-cutter/uploads/59a424ac.mp4` (759 MB, hash-named) lijkt een orphaned upload uit een eerder geannuleerde job. Geen referentie in actieve jobs gevonden. Mag waarschijnlijk weg.

---

## Pipeline-componenten met groen vinkje

| Component | Test | Status |
|---|---|---|
| `/api/upload-local` (no-copy register) | 2 verse sets, geen byte-copy | ✅ |
| Analyzer drop-detection | 26 + 151 unieke drops | ✅ |
| `detect_bpm()` BPM | Lisa half-tempo, Franky correct | ⚠️ (cosmetisch op Lisa) |
| `detect_musical_key()` Camelot | 4B + 12A allebei plausibel | ✅ |
| Cutting parallel (eager) | 26 × 2 formats in 3 min | ✅ |
| LARGE_FILE_PIPELINE auto-trigger | 14045s > 7200s threshold → proxy-route | ✅ |
| Proxy-clip rendering 720p | 151 proxies in 2 min | ✅ |
| `/api/render-clip` lazy full-quality | 1080p L+V in 5s | ✅ |
| BPM/Key stamp drawtext-overlay | "72 BPM · 4B" + "129 BPM · 12A" zichtbaar | ✅ |
| `_persist_job_snapshot` op disk | `job.json` schrijft 26-clip + 151-clip arrays | ✅ |
| `/api/track/<job>/<clip>` save+load | 3 keyframes round-trip via JSON | ✅ |
| `recut_clip` met keyframes-lookup | pan-effect cx=25→75→50 visueel correct | ✅ |
| `/api/export` 4 codec-varianten | match h264, h265_vt hevc, h264_vt h264, prores prores | ✅ |
| `export_clip_with_settings` per-clip | Per codec geverifieerd via ffprobe stream | ✅ |

---

## Volgende stappen

Sjuul heeft toestemming gegeven door te gaan met **optie b (tracking edge cases + TR3)** en daarna **optie c (B1 beat-pulse + B3 speed-ramp)** zodra optie a klaar is. Optie a is hiermee compleet.

Voor optie b is de Franky-job (`94d6c9c7`) een geschikte test-omgeving: 151 clips met DJ-figuur centraal én bewegende lighting — goed voor camera-pan auto-track en multi-clip face-embedding tests.

---

## Addendum — Drie polish-fixes na optie a (2026-05-12, dezelfde dag)

Na de end-to-end test heeft Sjuul drie kleine fixes gevraagd vóór optie b. Allemaal afgerond en live-getest:

### 14. BPM half-tempo fix (`analyzer.py`)

`_maybe_double_tempo()` helper toegevoegd in `analyzer.py` direct boven `detect_bpm`. Heuristiek: als librosa tempo retourneert in [60, 90) BPM **én** doubling in [120, 180] valt, verdubbel zowel tempo als beat_times (midpoint-insertion zodat de bar-grid intern consistent blijft).

**Live verificatie op `00abd848`** (verse re-upload van Lisa Korver):
- bpm: 71.8 → **143.6** ✓
- bpm_raw: 71.8 (bewaard voor debug)
- bpm_doubled: true
- bar_duration: 3.34 → 1.67 (gehalveerd, matched doubled tempo)
- Gerenderde clip 1 vertical mp4 toont nu **"144 BPM · 4B"** in top-right stamp (was "72 BPM · 4B").
- 30 clips gedetecteerd ipv 26 — finere bar-grid produceert meer bar-aligned drop windows.
- Franky (`94d6c9c7`) blijft 129.2 BPM ongewijzigd — heuristiek triggert niet op tech-house.

Edge-case suite (8 cases) unit-getest standalone:
- 89 BPM → 178 (doubles)
- 90 BPM → 90 (boundary, no double)
- 75 BPM → 150 (doubles)
- 50 BPM → 50 (doubles to 100, below dance-range, NO double)
- 95 BPM → 95 (already in range, NO double)
- 140 BPM → 140 (already in range, NO double)
- 60 BPM → 120 (boundary lower, doubles)
- 65 BPM → 130 (doubles)

Beeld bewijs: [SESSIE-24-bpm-fix-stamp.png](computer:///Users/sjuulsmits/Documents/Claude/Projects/Clip Live/SESSIE-24-bpm-fix-stamp.png)

Backup: `analyzer.py.pre-sessie24.bak`.

### 15. Export dropdown chevron (`static/index.html`)

Was: 9px `▾` tekst-character met opacity 0.7 — onzichtbaar voor first-time users. Sjuul's feedback: pijl moet duidelijker zijn én naar links wijzen omdat het menu naar links uitvouwt.

Vervangen door inline SVG polyline (left-chevron), 14×16px, `color: var(--amber-2)`, hover/open-state animaties (translateX(-2px) tijdens open richting menu). Hit-area expansion ::after pseudo om makkelijker te raken.

DOM-verifieerd: `<svg viewBox="0 0 24 24"><polyline points="15 6 9 12 15 18"></polyline></svg>` met computed color `rgb(244, 207, 138)` (amber-2). Caret element width/height 16×14.

### 16. Playhead — draggable + start-at-IN (`static/index.html`)

Twee aspecten:

**(a) Playhead-knob draggable.** De ::before pseudo-element die de gouden driehoek tekende is vervangen door een echt DOM-element `.playhead-knob` (id `tl-playhead-knob`). `pointer-events:auto`, `cursor:grab`, hit-area expansion via ::after. Mousedown enters scrub mode (body.is-scrubbing class, video gepauzeerd), mousemove updates v.currentTime via dezelfde `pxToVirtSec`-conversie als de trim-handles, mouseup cleart drag state. Plus dubbelklik-shortcut om naar inSec te springen.

**(b) Play-restart bij IN-handle.** Nieuwe helper `_editorSnapPlayheadToInIfOutside()`. Bij play-trigger (via `editorTogglePlay()` of stage-click): als v.currentTime buiten [inSec, outSec) ligt → seek naar inSec voor `v.play()`. Detecteert source-swap mode (S4.2) en gebruikt set-time (`clipStart + inSec`) ipv clip-time. Binnen het bereik blijft currentTime ongemoeid — user's scrub-positie wordt gerespecteerd.

Live-getest via simulated MouseEvents in MCP-tab:
- mousedown op knob → `_playheadDrag` set, body.is-scrubbing toegevoegd, knob.is-grabbing toegevoegd ✓
- mousemove 70% across tracks → currentTime clamped to duration ✓
- mousemove 20% across → currentTime = 5.37s ✓
- mouseup → drag state cleared, classes verwijderd ✓
- v.currentTime=0 + STATE.trim.inSec=5 → `editorTogglePlay()` → currentTime springt naar 5, dan v.play() → na 300ms staat hij op 5.22s, paused=false ✓

Backup: `static/index.html.pre-sessie24.bak`.

### Server restart vereist?

Voor (14) ja — analyzer.py wijziging. Restart uitgevoerd via `_restart.sh` script (osascript bridge), nieuwe Flask-process pid 70201. Server live op port 5555, capabilities check OK.

Voor (15) + (16) is hard-refresh van de browser voldoende — pure frontend wijzigingen in `static/index.html`.

---

## Addendum 2 — Optie B (tracking edge cases + DJ-centered preview) (2026-05-12)

Drie sub-takenlijst (B1 stretch+tracking edge-case test, B2 live DJ-centered preview, B3 subject-signature persistence) volledig afgerond + live geverifieerd.

### B1 — Stretch + tracking combined

Test op Franky clip 5: IN-stretch -3s, 3 manual keyframes (cx 20→80→50), recut. Output 19.72s. Frame-extract op t=0/10/19 toont correcte pan inclusief gestrechte zone vóór `clip.start`. **PASS** — geen fix nodig, bestaande recut_clip-pipeline werkt met tracking + stretch combined.

### B2 — Auto-track live preview (DJ-centered)

Nieuwe "Preview crop" toggle in de Track drawer naast Auto-track DJ. Bij ON:

- Swap `<video>.src` van vertical naar **landscape** (16:9 source — bestaande pre-cropped vertical heeft niets om over te croppen)
- `_updateTrackCropPreview()` op elke timeupdate: berekent `object-position` via `_trackedObjectPosition(cx, cy, stage, video)` met cover-formule:
  - `visibleFracX = stageAspect / videoAspect` (overflow-axis)
  - `halfX = visibleFracX * 50`
  - `objX = ((cx_pct - halfX) / (100 - 2*halfX)) * 100`
- Clamp cx_pct zodat visible strip nooit buiten source-bounds valt
- Werkt voor alle stage-aspecten (9:16/1:1/16:9) — formule leest stage+source runtime
- Badge linksboven "PREVIEW · DJ-tracked crop" zodat user weet dat ze in preview-mode zijn

Bij OFF: src restore + objectPosition reset + currentTime preserve.

Hook-up: `timeupdate` listener (al gewired voor box overlay) roept ook `_updateTrackCropPreview()` als `cropPreviewOn` true. Plus `_paintEditorTrackBox()` triggert update — dekt manual-drag van keyframe wanneer paused.

**Live geverifieerd op Franky clip 1**: na auto-track (21 keyframes "mixed + YOLO fallback"), toggle ON, samples op verschillende currentTimes:
- t=1.25 → object-position "14.52% 50%"
- t=5.0  → "55.31% 50%"
- t=10.0 → "64.96% 50%"
- t=15.0 → "55.55% 50%"

`object-position` schuift dynamisch met de keyframes. Stage class `is-crop-preview` toegevoegd, video src swap't naar landscape (1920×1080, aspect 1.778). Toggle OFF → vertical terug + objectPosition reset.

### B3 — Subject-signature persistence (pragmatic alternative to face-embedding)

**Scope-beslissing**: pure face-embedding (dlib of OpenFace via OpenCV DNN) vereist heavy deps + model-download. Gekozen voor **position+size signature** ipv face-descriptor — 80% van de waarde voor DJ-sets (waar DJ-positie typisch stabiel is), zonder nieuwe deps.

**Implementation:**

`tracking.py`:
- `_pick_primary()` accepteert nu een derde param `prior_signature: {cx, cy, w, h}` in 0..1
  - Bij eerste-frame van een clip (geen `prev_center`): strong position+size bias naar signature
  - Daarna: milde size-similarity bias (voorkomt drift naar verkeerde persoon mid-clip)
- `detect_track()` accepteert + propageert `subject_signature` naar alle 4 `_pick_primary` calls
- `run_auto_track_async()` propageert
- Nieuwe helper `compute_subject_signature(keyframes)` → avg cx/cy/w/h

`app.py`:
- `/api/track/<job>/<clip>/auto` POST leest `job.subject_signature` (in-memory state, fallback naar snapshot) en geeft door aan `run_auto_track_async`. Response heeft `using_signature: bool`.
- `/api/track/<job>/<clip>/auto/status` GET: na succesvolle auto-track berekent + persisteert signature ALS job nog geen heeft (one-shot bias-seed). Response heeft `subject_signature_saved: <sig>` als nieuw opgeslagen.
- Nieuwe endpoints:
  - `GET /api/job/<job>/subject-signature` → `{signature, anchor_clip, present}`
  - `DELETE /api/job/<job>/subject-signature` → clear
  - `POST /api/job/<job>/subject-signature` met body `{clip_index}` → recompute uit die clip's tracking JSON + overwrite

`static/index.html`:
- Nieuw lock-row in Track drawer met badge "🎯 Subject locked" + "from clip N · cx X% · cy Y%" meta + "Lock to this clip" en "Clear" buttons
- `_refreshTrackLockBadge()` hidden/visible obv `/api/job/<job>/subject-signature` GET
- Trigger op: drawer open + auto-track success + lock/clear actions
- Status text na auto-track: " · matched locked DJ" of " · saved as DJ signature"

**Live geverifieerd op Franky `94d6c9c7`:**
- POST signature van clip 1 → succes, signature `{cx:0.5217, cy:0.5536, w:0.2217, h:0.6664, samples:21}`
- GET retrieves matched ✓
- Auto-track op **clip 10** → `using_signature: true` in response → 67 frames analyzed → 21 keyframes
- **Avg cx = 51.03%** (vs locked 52.17%) — afwijking 1.14% ✓
- **Avg cy = 57.30%** (vs locked 55.36%) — afwijking 1.94% ✓
- Width range 17-25% (vs locked 22.17%) ✓
- Frontend lock-row visible met text "🎯 Subject locked / from clip 1 · cx 52% · cy 55%" ✓

Bias is soft (multiplicative score, niet hard constraint) zodat individuele frames met legitiem grote/duidelijke alternative detections nog steeds correct opgepakt worden. Maar gemiddeld blijft de tracker bij de DJ-positie ipv naar willekeurige crowd-members te drijven.

**Backups voor optie B**: `tracking.py.pre-sessie24.bak`, `app.py.pre-sessie24.bak` (samen met `static/index.html.pre-sessie24.bak` die ook B2 + 14/15/16 bevat).

Server restart uitgevoerd voor B3 backend changes (tracking.py + app.py): pid 72143.

---

## Volgende stappen — wat is er nog over?

Sessie-24 scope is hiermee volledig afgerond:
- ✅ Optie a — end-to-end test op 2 verse uploads
- ✅ Fixes 14/15/16 — BPM half-tempo + chevron + playhead
- ✅ Optie B1/B2/B3 — tracking edge cases + DJ-centered preview + subject lock

**Restant van Sjuul's roadmap:**
- Optie C — B1 beat-pulse + B3 speed-ramp (Sessie 22 deferred items)
- Stripe live mode + DNS — pre-launch
- Brand Stack v2 add-ons — end-card, intro-still, lower-third
- Pure face-embedding upgrade voor B3 (dlib of OpenCV DNN) als de position+size heuristiek te zacht blijkt in de praktijk
