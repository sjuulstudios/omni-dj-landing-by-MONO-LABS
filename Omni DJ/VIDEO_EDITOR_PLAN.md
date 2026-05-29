# OmniDJ Video Editor — Feature Expansion Plan

## What exists today

The current editor has a solid skeleton:
- Left panel: video `<video>` preview with landscape/vertical format tabs
- Playback controls: play/pause, frame step (±1), in/out point buttons
- Right panel: ruler canvas, video track + waveform track with in/out handles and playhead
- Timecode bar: editable in-point, out-point, read-only duration inputs
- Save & Re-export button that sends new in/out to the backend

What it's missing is interactivity: the timeline can't be zoomed, dragged, or clicked to seek; the handles can't be dragged; and there's no way to expand a clip from the dashboard without entering the full editor.

---

## Phase 1 — Timeline Zoom, Pan & Frame Accuracy

This is the prerequisite for everything else. Without zoom there's no way to cut precisely.

### 1.1 Zoom levels

Three meaningful levels mapped to a `zoomLevel` state (0.0 – 1.0 on a log scale):

| Level | px per second | Use case |
|-------|--------------|----------|
| Overview | ~20 px/s | See entire clip at once |
| Bar | ~80 px/s | Musical bar grid visible |
| Frame | ~400+ px/s | Individual video frames visible |

Controls:
- **Scroll wheel / trackpad pinch** on the timeline zooms in/out around the cursor position
- **`+` / `-` keyboard shortcuts** while editor is focused
- **Zoom slider** widget at the top-right of the timeline panel

Implementation: store `zoomLevel` and `scrollOffset` (seconds) in `state`. All canvas draw calls and handle positions read from these two values. A `timeToX(t)` / `xToTime(x)` helper pair converts between seconds and pixels, making every other piece zoom-aware automatically.

### 1.2 Pan / scroll

When zoomed in, the timeline is wider than the panel. The user pans by:
- **Click-drag on the ruler** (the top time-bar) — a standard DAW convention
- **Middle-mouse drag** anywhere on the timeline
- **Horizontal scroll** on a trackpad

The playhead auto-scrolls when playback reaches the right edge (follows playhead mode, toggleable).

### 1.3 Frame-accurate seeking

At frame-level zoom, click anywhere on the video track to seek to that frame. The `<video>` element's `currentTime` is set to `xToTime(clickX)`, which at 400 px/s gives sub-frame click accuracy. Display the current frame number in the timecode bar alongside the timestamp.

### 1.4 Mini-map (overview scrubber)

A 100%-wide, 18 px-tall strip below the main timeline always shows the full clip. A shaded rectangle shows the current zoom window. Drag the rectangle to pan. This is the standard "you are here" map used in Premiere, DaVinci, and Ableton.

---

## Phase 2 — Draggable In/Out Handles

The handles already render on the canvas; they just aren't draggable yet.

### 2.1 Drag behavior

- Mouse down on the green in-handle or red out-handle → enter drag mode
- Mouse move → update `state.inPoint` / `state.outPoint` in real time, redraw canvas, seek video to current handle position so the DJ sees exactly where the cut will land
- Mouse up → commit; update timecode inputs; enable Save button if changed
- Handles snap to bar/beat boundaries when snap mode is active (see Phase 3)

### 2.2 Selection region highlight

The existing `.selection-region` div fills the space between in and out handles with a semi-transparent accent colour. This already exists in CSS — it just needs to be wired to the drag positions.

### 2.3 Keyboard shortcuts for in/out

| Key | Action |
|-----|--------|
| `I` | Set in point at current playhead position |
| `O` | Set out point at current playhead position |
| `Shift+I` | Jump playhead to in point |
| `Shift+O` | Jump playhead to out point |

These are the industry-standard shortcuts (Premiere, Final Cut, DaVinci).

---

## Phase 3 — J/K/L Scrubbing

The most requested pro editing shortcut. Lets the DJ skim through a set quickly without touching the mouse.

| Key | Action |
|-----|--------|
| `J` | Rewind (press again to go 2×, 4×) |
| `K` | Pause |
| `L` | Fast forward (press again to go 2×, 4×) |
| `K + J` | Step back one frame |
| `K + L` | Step forward one frame |

Implementation: track a `scrubSpeed` state (-4, -2, -1, 0, 1, 2, 4). `requestAnimationFrame` loop advances `video.currentTime` by `scrubSpeed × frameDuration` each frame when speed ≠ 0. The visual playhead follows in real time. This is purely frontend — no backend changes needed.

---

## Phase 4 — Snap Modes

A snap toggle group in the timeline toolbar with three modes:

**Off** — free movement, sub-frame precision  
**Beat** — handles and seeks snap to the beat grid (requires BPM data in `state.editorClip.bpm` and beat_times, which the analyzer already outputs)  
**Bar** — snaps to bar boundaries (every 4 beats)

When snap is active, the cursor changes to a magnet icon and handles visually "pop" to grid lines as you drag near them (within 8 px). This makes bar-aligned re-cuts effortless for DJ content.

---

## Phase 5 — Filmstrip on Video Track

At bar-level or frame-level zoom, the video track canvas draws actual frame thumbnails extracted from the source clip. This is the most visually useful feature — you can see the drop moment, crowd reaction, and lighting changes directly on the timeline.

Backend: a new `/api/filmstrip/<job_id>/<clip_index>` endpoint calls ffmpeg to extract N evenly-spaced JPEG frames from the clip's source segment and returns them as a JSON array of base64 images (or serves them as individual files). Cache on disk per job.

Frontend: when zoom level crosses the bar threshold, request the filmstrip if not cached, then draw frames on the video track canvas at the correct x positions. At overview zoom, show a solid colour fill instead to keep it fast.

---

## Phase 6 — Loop Playback

A loop button in the video controls (between the frame-step buttons) toggles in/out loop mode. When active, playback wraps from `outPoint` back to `inPoint` automatically. This is essential for checking an edit — the DJ can hear the cut on repeat without touching anything.

Implementation: `video.ontimeupdate` checks if `video.currentTime >= state.outPoint` and resets to `state.inPoint` when loop is enabled.

---

## Phase 7 — Inline Clip Expand from Dashboard (the "big" feature)

Instead of requiring the user to open the full editor for every clip, each dashboard card gets an **Expand** button that reveals a compact inline editor directly inside the card row. This is the fastest path for quick cut adjustments.

### What the inline editor shows

```
┌──────────────────────────────────────────────────────────────────────┐
│ [▶ Preview]   [🖼 Thumbnail]   In: 0:32.400   Out: 1:16.800   Dur: 44.4s │
│ ━━━━━━━━━━━━━━━━━[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│           ↑ in handle                ↑ out handle                    │
│                                                          [💾 Re-export] │
└──────────────────────────────────────────────────────────────────────┘
```

The waveform strip uses the same `get_waveform_data` API that the processing view already calls. The handles are draggable in the same way as the full editor. The clip card expands vertically with a smooth CSS transition. Only one card can be expanded at a time (expanding a second one collapses the first).

### Interaction

1. User clicks **⚙ Adjust** button on any dashboard card
2. Card expands with 300 ms CSS transition to show the inline timeline strip
3. A small `<audio>` element loads the source clip for preview playback
4. User drags in/out handles on the strip or types timecodes directly
5. **💾 Re-export** sends the adjusted in/out to `/api/reexport` (endpoint already exists)
6. After re-export completes, thumbnail refreshes and card collapses

This removes the need to visit the full editor for the vast majority of cuts.

---

## Phase 8 — Export Presets

A dropdown on the Save button with platform presets:

| Preset | Resolution | Format | Notes |
|--------|-----------|--------|-------|
| Source quality | original | landscape or vertical | Current default |
| TikTok / Reels | 1080×1920 | vertical | Max 60 fps, H.264 |
| YouTube Shorts | 1080×1920 | vertical | Same as TikTok |
| Instagram Post | 1080×1080 | square crop | Centre crop |
| Twitter/X | 1280×720 | landscape | 2-minute limit |

The selected preset overrides the job-level format setting only for this clip's re-export.

---

## Phase 9 — Split Tool ~~(in scope)~~ — VERWIJDERD IN SESSIE 33

> **Update sessie 33 (2026-05-23):** Sjuul's workflow is trim/stretch, niet split-in-twee. UI-knoppen (scissor + asterix) zijn verwijderd in sessie 32d, en de bijbehorende JS-functies + `C` keyboard-shortcut + `STATE.splitMode` flag + CSS zijn opgeruimd in sessie 33. Backend `/api/split-clip` endpoint blijft draaien voor het geval het ooit weer nodig is, maar wordt op dit moment nergens vanuit de UI aangeroepen. Het oorspronkelijke design hieronder blijft staan als historische referentie.

A secondary toolbar tool (alongside the existing Select tool): the **Split** tool (scissor icon, keyboard shortcut `C` matching Premiere) lets the user click anywhere on the timeline to split the clip at that point and immediately export both halves as separate clips. Useful when a drop moment contains two distinct sections the user wants as separate clips.

This requires:
- Frontend: detecting which tool is active when the user clicks the timeline, and calling a new `/api/split` endpoint
- Backend: calling ffmpeg twice — once for 0 to split point, once for split point to end

---

## Phase 10 — Waveform Zoom Sync & Spectrogram Mode

When the user zooms into the timeline, the waveform track redraws at higher resolution by requesting more sample points from the `/api/waveform` endpoint (increasing `num_points` proportionally). This gives the user a detailed transient view at the frame level — they can see the exact kick drum hit as a spike in the waveform.

A toggle on the audio track row switches between:
- **Waveform** — RMS amplitude over time (current)
- **Spectrogram** — colour-coded frequency content (orange/red = sub-bass, green = mids, blue = high-freq). This is generated on the backend using `librosa.stft` and returned as a PNG image drawn onto the canvas. This view is the most musically useful one for a DJ — they can see where the bass drops, where the breakdown starts, and where the build peaks.

---

## Implementation priority order

1. **Phase 1** (Zoom + pan + frame-seek) — everything depends on this
2. **Phase 2** (Draggable handles) — immediately useful, pairs with zoom
3. **Phase 6** (Loop playback) — one listener, huge quality-of-life win
4. **Phase 3** (J/K/L scrub) — pure frontend, fast to add
5. **Phase 7** (Inline expand) — highest user value, moderate effort
6. **Phase 4** (Snap modes) — pairs with draggable handles
7. **Phase 5** (Filmstrip) — needs backend endpoint, high visual impact
8. **Phase 8** (Export presets) — dropdown UI + backend switch
9. **Phase 9** (Split tool) — new endpoint + frontend tool mode
10. **Phase 10** (Spectrogram) — backend computation, visually impressive

Phases 1–4 are all pure frontend changes. No new API endpoints, no backend changes. They can be shipped as a single HTML/JS update. Phases 5–10 each require at least one new backend endpoint.
