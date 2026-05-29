"""
SESSIE 22 — Auto-tracking (TR2).

Hybrid subject-detection for the editor's Track tool. Privacy-first:

1. **Primary engine — Apple Vision Framework** (via PyObjC).
   - 100% on-device, no network, no telemetry.
   - VNDetectHumanRectanglesRequest returns bounding boxes for visible
     people in a frame, with confidence scores per detection.
   - Fast on Apple Silicon — typically 20-40 ms / frame at native res.

2. **Fallback engine — Ultralytics YOLOv8n** (only when:
      a. Apple Vision returns 0 detections on >=3 consecutive sampled frames, OR
      b. The frame is "lowlight" (mean luminance < 60/255) AND Apple Vision
         confidence < 0.5
   - Telemetry hard-killed via env vars (see `_disable_ultralytics_telemetry`).
   - Weights downloaded once (~5 MB) from GitHub releases; cached locally.

3. **Last-resort fallback — OpenCV HOG person detector.**
   - Built into opencv-python, no extra weights to download.
   - Lower accuracy but works without ML deps.

All three are guarded with try/except so the app starts cleanly even if
none of pyobjc-framework-Vision / ultralytics / opencv-python is installed.
The /api/track/<job>/<clip>/auto endpoint returns a 422 with an install hint
when nothing is available.

Output schema (single subject — for v1):
    [
      {t, cx_pct, cy_pct, w_pct, h_pct, source, confidence},
      ...
    ]
percentages relative to source-frame dimensions. `source` is one of
'apple_vision', 'yolo', 'hog'; `confidence` is 0..1.
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import threading
import time
from typing import List, Dict, Optional, Tuple

# --- Optional-import gauntlet ----------------------------------------------
# Each engine is import-once-and-cache. Module-import never fails — the
# absence of a particular engine just disables that branch.

_HAS_OPENCV = False
_cv2 = None
try:
    import cv2 as _cv2  # type: ignore
    _HAS_OPENCV = True
except Exception:
    pass

_HAS_VISION = False
_vn_request = None  # cached VNDetectHumanRectanglesRequest instance
try:
    # PyObjC bridge — only available on macOS with `pyobjc-framework-Vision`.
    from Vision import VNImageRequestHandler, VNDetectHumanRectanglesRequest  # type: ignore
    from CoreFoundation import CFURLCreateFromFileSystemRepresentation, kCFAllocatorDefault  # type: ignore
    _HAS_VISION = True
except Exception:
    pass

_HAS_YOLO = False
_yolo_model = None  # cached YOLO model
try:
    # SESSIE 22 — disable telemetry BEFORE importing ultralytics so the
    # sync=False setting is in effect for any first-run hub call.
    os.environ.setdefault('YOLO_OFFLINE', 'True')
    os.environ.setdefault('NO_ALBUMENTATIONS_UPDATE', '1')
    from ultralytics import YOLO  # type: ignore
    try:
        from ultralytics import settings as _yolo_settings  # type: ignore
        try:
            _yolo_settings.update({'sync': False, 'api_key': ''})
        except Exception:
            pass
    except Exception:
        pass
    _HAS_YOLO = True
except Exception:
    pass

# Optional numpy (already a hard dep elsewhere).
try:
    import numpy as _np  # type: ignore
except Exception:
    _np = None  # extremely unlikely


# Path to the local YOLO weights — bundled-or-downloaded under models/.
_HERE = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR = os.path.join(_HERE, 'models')
_YOLO_WEIGHTS = os.path.join(_MODELS_DIR, 'yolov8n.pt')


def engines_available() -> Dict[str, bool]:
    """Report which engines this install supports. The /api/track endpoint
    surfaces this so the UI can render an accurate disabled-state."""
    return {
        'apple_vision': _HAS_VISION,
        'yolo':         _HAS_YOLO,
        'hog':          _HAS_OPENCV,
        'any':          _HAS_VISION or _HAS_YOLO or _HAS_OPENCV,
    }


# --- Frame extraction ------------------------------------------------------
# We use ffmpeg to pull frames at the requested sample rate. Significantly
# more portable than asking each engine to open the video; also lets us reuse
# the same frame for brightness check + detection.

def _extract_frames(video_path: str, start: float, duration: float,
                    fps: float, out_dir: str) -> List[Tuple[float, str]]:
    """Extract frames at `fps` per second from a [start, start+duration]
    window of the video. Returns list of (t_relative, frame_path).
    `t_relative` is seconds from clip start (i.e. start at 0 not `start`)."""
    os.makedirs(out_dir, exist_ok=True)
    # Use ffmpeg's fast keyframe seek BEFORE the input for speed.
    pattern = os.path.join(out_dir, 'f_%06d.jpg')
    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-ss', f'{start:.3f}',
        '-i', video_path,
        '-t', f'{duration:.3f}',
        '-vf', f'fps={fps}',
        '-q:v', '4',
        pattern,
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=300, check=True)
    except subprocess.CalledProcessError as e:
        # Don't bubble up — return empty so the caller can degrade.
        sys.stderr.write(f'[tracking] ffmpeg frame-extract failed: {e}\n')
        return []
    out = []
    files = sorted(f for f in os.listdir(out_dir) if f.startswith('f_') and f.endswith('.jpg'))
    for f in files:
        # frame index → time relative to clip start
        try:
            idx = int(f[2:].split('.')[0])
        except (ValueError, IndexError):
            continue
        t = (idx - 1) / max(0.01, fps)   # 1-based pattern
        out.append((t, os.path.join(out_dir, f)))
    return out


# --- Brightness check ------------------------------------------------------
# Mean luminance of a frame — used to route lowlight frames to YOLO. We
# downsize to 64×64 first so the read is essentially free.

def _frame_brightness(path: str) -> float:
    if not _HAS_OPENCV:
        return 128.0   # assume mid-bright if we can't read
    try:
        img = _cv2.imread(path)
        if img is None:
            return 128.0
        small = _cv2.resize(img, (64, 64))
        gray = _cv2.cvtColor(small, _cv2.COLOR_BGR2GRAY)
        return float(gray.mean())
    except Exception:
        return 128.0


# --- Apple Vision detector -------------------------------------------------
# Synchronous per-file. We re-use the same VNRequest instance across calls
# because constructing it is non-trivial (Cocoa bridging).

def _vision_detect(frame_path: str) -> Optional[List[Dict]]:
    """Returns list of {x, y, w, h, conf} normalized 0..1 (Apple Vision
    returns boxes in normalized coords). None if Vision call fails."""
    if not _HAS_VISION:
        return None
    global _vn_request
    try:
        # Build URL from path.
        path_b = frame_path.encode('utf-8')
        url = CFURLCreateFromFileSystemRepresentation(
            kCFAllocatorDefault, path_b, len(path_b), False
        )
        if url is None:
            return None
        handler = VNImageRequestHandler.alloc().initWithURL_options_(url, {})
        if _vn_request is None:
            _vn_request = VNDetectHumanRectanglesRequest.alloc().init()
        ok, _err = handler.performRequests_error_([_vn_request], None)
        if not ok:
            return None
        results = _vn_request.results() or []
        out = []
        for obs in results:
            try:
                bb = obs.boundingBox()
                # Apple's bbox origin is BOTTOM-left. We convert to top-left
                # convention (matches the rest of the pipeline).
                x = float(bb.origin.x)
                y_bottom = float(bb.origin.y)
                w = float(bb.size.width)
                h = float(bb.size.height)
                y = max(0.0, 1.0 - y_bottom - h)
                conf = float(getattr(obs, 'confidence', lambda: 0.5)())
                out.append({'x': x, 'y': y, 'w': w, 'h': h, 'conf': conf})
            except Exception:
                continue
        return out
    except Exception:
        return None


# --- YOLO detector ---------------------------------------------------------
# Lazy-init: loaded on first call. Uses MPS (Apple Silicon GPU) when
# available — falls back to CPU silently.

def _yolo_load():
    global _yolo_model
    if _yolo_model is not None or not _HAS_YOLO:
        return _yolo_model
    try:
        # Local-only weights if present; let ultralytics download on first run.
        weights = _YOLO_WEIGHTS if os.path.exists(_YOLO_WEIGHTS) else 'yolov8n.pt'
        _yolo_model = YOLO(weights)
        # On macOS Apple Silicon, pin to MPS for speed.
        try:
            import torch  # type: ignore
            if hasattr(torch, 'backends') and torch.backends.mps.is_available():
                _yolo_model.to('mps')
        except Exception:
            pass
        return _yolo_model
    except Exception as e:
        sys.stderr.write(f'[tracking] YOLO load failed: {e}\n')
        return None


def _yolo_detect(frame_path: str) -> Optional[List[Dict]]:
    """Person-class (COCO id 0) detections, normalized 0..1 (top-left)."""
    if not _HAS_YOLO:
        return None
    model = _yolo_load()
    if model is None:
        return None
    try:
        # YOLO returns Results object — we want xyxy normalized + conf.
        results = model.predict(source=frame_path, classes=[0], verbose=False)
        if not results:
            return None
        r = results[0]
        if not hasattr(r, 'boxes') or r.boxes is None:
            return None
        h_img, w_img = r.orig_shape  # (h, w)
        out = []
        for b in r.boxes:
            xy = b.xyxy[0].tolist()  # x1,y1,x2,y2 in pixels
            conf = float(b.conf[0]) if hasattr(b, 'conf') else 0.5
            if w_img and h_img:
                out.append({
                    'x': max(0.0, xy[0] / w_img),
                    'y': max(0.0, xy[1] / h_img),
                    'w': max(0.0, (xy[2] - xy[0]) / w_img),
                    'h': max(0.0, (xy[3] - xy[1]) / h_img),
                    'conf': conf,
                })
        return out
    except Exception as e:
        sys.stderr.write(f'[tracking] YOLO predict failed: {e}\n')
        return None


# --- HOG last-resort detector ----------------------------------------------

_hog = None
def _hog_detect(frame_path: str) -> Optional[List[Dict]]:
    if not _HAS_OPENCV:
        return None
    global _hog
    try:
        if _hog is None:
            _hog = _cv2.HOGDescriptor()
            _hog.setSVMDetector(_cv2.HOGDescriptor_getDefaultPeopleDetector())
        img = _cv2.imread(frame_path)
        if img is None: return None
        # HOG works better on a downscaled image — 480p is plenty for DJ shots.
        h, w = img.shape[:2]
        scale = 1.0
        if w > 720:
            scale = 720.0 / w
            img = _cv2.resize(img, (int(w*scale), int(h*scale)))
            h, w = img.shape[:2]
        rects, weights = _hog.detectMultiScale(img, winStride=(8, 8), padding=(8, 8), scale=1.05)
        out = []
        for (x, y, ww, hh), conf in zip(rects, weights):
            out.append({
                'x': max(0.0, x / w),
                'y': max(0.0, y / h),
                'w': max(0.0, ww / w),
                'h': max(0.0, hh / h),
                'conf': float(conf),
            })
        return out
    except Exception:
        return None


# --- Subject selection + smoothing ----------------------------------------

def _pick_primary(detections: List[Dict],
                  prev_center: Optional[Tuple[float, float]] = None,
                  prior_signature: Optional[Dict] = None) -> Optional[Dict]:
    """Pick the best 'primary' detection from a list.

    Base heuristic: max(area * sqrt(conf)) — bigger + more confident.

    `prev_center` (when given) is a normalized (cx, cy) in 0..1 from the
    previously-picked detection in this clip. Lightly prefers detections near
    it for in-clip identity continuity.

    SESSIE 24 — `prior_signature` is a job-level signature persisted from an
    earlier clip's auto-track. Shape: {'cx', 'cy', 'w', 'h'} all in 0..1.
    When given:
      - On the FIRST frame of a clip (prev_center is None), bias scoring
        toward detections matching the signature in position+size. This is
        what stops auto-track from latching onto a crowd-member on clip-N
        when the DJ has been the saved subject since clip-1.
      - On subsequent frames, apply a milder size-similarity bias so the
        tracker doesn't drift to a big "wrong person" mid-clip when prev
        loses track briefly.
    """
    if not detections:
        return None

    def _det_center(d):
        return (d['x'] + d['w'] / 2, d['y'] + d['h'] / 2)

    def _size_similarity(d):
        # Compare candidate box-width to the signature's. Ratio in (0,1].
        if not prior_signature: return 1.0
        pw = max(0.02, float(prior_signature.get('w', 0)))
        cw = max(0.02, float(d['w']))
        return min(pw, cw) / max(pw, cw)

    def score(d):
        area = max(1e-6, d['w'] * d['h'])
        s = area * (max(0.05, d.get('conf', 0.5)) ** 0.5)
        cx, cy = _det_center(d)
        if prev_center is not None:
            dx = cx - prev_center[0]; dy = cy - prev_center[1]
            dist = (dx * dx + dy * dy) ** 0.5
            s *= max(0.5, 1.0 - dist)
        elif prior_signature is not None:
            # First-frame seeding from job-level signature (SESSIE 24 B3).
            # Strong bias here — prevents drift to the wrong person on clip-1
            # of a new clip when there's no prev_center to anchor identity.
            px = float(prior_signature.get('cx', 0.5))
            py = float(prior_signature.get('cy', 0.5))
            dx = cx - px; dy = cy - py
            dist = (dx * dx + dy * dy) ** 0.5
            # Position penalty up to 0.4×, multiplied with size-similarity.
            s *= max(0.4, 1.0 - dist) * (0.5 + 0.5 * _size_similarity(d))
        if prior_signature is not None:
            # Mild size-bias even when prev_center exists — keeps the tracker
            # from latching onto someone twice the DJ's size mid-clip.
            s *= (0.8 + 0.2 * _size_similarity(d))
        return s

    return max(detections, key=score)


def _smooth_track(track: List[Dict], alpha: float = 0.4) -> List[Dict]:
    """Simple exponential-moving-average smoothing on cx/cy/w/h.
    `alpha` is the smoothing factor — higher = more responsive, lower = smoother.
    Operates in-place semantics but returns a new list."""
    if not track:
        return []
    smoothed = [dict(track[0])]
    for i in range(1, len(track)):
        prev = smoothed[-1]
        cur  = track[i]
        merged = dict(cur)
        for k in ('cx_pct', 'cy_pct', 'w_pct', 'h_pct'):
            merged[k] = (alpha * cur[k]) + ((1 - alpha) * prev[k])
        smoothed.append(merged)
    return smoothed


def _downsample_keyframes(track: List[Dict], max_count: int = 20) -> List[Dict]:
    """Reduce a per-frame track to <= max_count keyframes by skipping evenly.
    Always preserves first + last keyframe so interpolation works at edges."""
    if not track or len(track) <= max_count:
        return track[:]
    step = len(track) / max_count
    out = []
    last_idx = -1
    for i in range(max_count):
        idx = int(round(i * step))
        idx = max(0, min(len(track) - 1, idx))
        if idx == last_idx:
            continue
        out.append(track[idx])
        last_idx = idx
    # Ensure the last keyframe is in.
    if out[-1] is not track[-1]:
        out.append(track[-1])
    return out


# --- Orchestration ---------------------------------------------------------

def detect_track(video_path: str,
                 start: float,
                 duration: float,
                 fps: float = 4.0,
                 lowlight_threshold: float = 60.0,
                 vision_confidence_floor: float = 0.5,
                 max_keyframes: int = 20,
                 smoothing: float = 0.4,
                 yolo_fallback: bool = True,
                 subject_signature: Optional[Dict] = None,
                 progress_cb=None) -> Dict:
    """Run the hybrid track over the requested clip range.

    Returns:
        {
          'ok': bool,
          'engine': 'apple_vision' | 'yolo' | 'hog' | 'mixed',
          'fallback_used': bool,
          'keyframes': [...],
          'frames_total': int,
          'frames_done': int,
          'error': str|None,
        }
    `progress_cb(done, total)` is called between frames; the auto-track
    endpoint uses it to update the in-memory progress dict.
    """
    eng = engines_available()
    if not eng['any']:
        return {
            'ok': False,
            'engine': None, 'fallback_used': False, 'keyframes': [],
            'frames_total': 0, 'frames_done': 0,
            'error': 'No detection engine available. Install one: '
                     'pip install "pyobjc-framework-Vision" (macOS, recommended), '
                     'or "ultralytics", or "opencv-python".',
        }

    # 1) Extract frames via ffmpeg.
    with tempfile.TemporaryDirectory(prefix='omnidj-track-') as tmpdir:
        frames = _extract_frames(video_path, start, duration, fps, tmpdir)
        total = len(frames)
        if total == 0:
            return {
                'ok': False, 'engine': None, 'fallback_used': False,
                'keyframes': [], 'frames_total': 0, 'frames_done': 0,
                'error': 'No frames extracted from clip range — bad timestamps?',
            }

        # 2) Per-frame detection. Source-tagged so the UI can show which
        #    engine produced each keyframe.
        track = []   # per-frame: {t, cx_pct, cy_pct, w_pct, h_pct, source, confidence}
        prev_center = None
        engines_used = set()
        fallback_count = 0
        vision_empty_streak = 0
        for i, (t_rel, frame_path) in enumerate(frames):
            best = None
            source = None
            brightness = _frame_brightness(frame_path) if eng['hog'] else 128.0

            # Try Apple Vision first (when available).
            if _HAS_VISION:
                dets = _vision_detect(frame_path)
                if dets:
                    best = _pick_primary(dets, prev_center, subject_signature)
                    if best:
                        vision_empty_streak = 0
                        # Lowlight + low-confidence → escalate to YOLO.
                        if yolo_fallback and _HAS_YOLO and brightness < lowlight_threshold and best['conf'] < vision_confidence_floor:
                            ydets = _yolo_detect(frame_path)
                            ybest = _pick_primary(ydets or [], prev_center, subject_signature)
                            if ybest and ybest.get('conf', 0) > best['conf']:
                                best = ybest; source = 'yolo'; fallback_count += 1
                            else:
                                source = 'apple_vision'
                        else:
                            source = 'apple_vision'
                    else:
                        vision_empty_streak += 1
                else:
                    vision_empty_streak += 1

            # Vision returned nothing for >=3 frames in a row → try YOLO.
            if best is None and yolo_fallback and _HAS_YOLO and vision_empty_streak >= 3:
                ydets = _yolo_detect(frame_path)
                best = _pick_primary(ydets or [], prev_center, subject_signature)
                if best:
                    source = 'yolo'; fallback_count += 1

            # Vision unavailable + (no YOLO or YOLO returned nothing) → HOG.
            if best is None and _HAS_OPENCV:
                hdets = _hog_detect(frame_path)
                best = _pick_primary(hdets or [], prev_center, subject_signature)
                if best:
                    source = 'hog'

            # No detection at all → hold previous box (interpolation gap-fill).
            if best is None:
                if track:
                    last = track[-1]
                    track.append({**last, 't': t_rel, 'source': 'hold'})
                if progress_cb:
                    try: progress_cb(i + 1, total)
                    except Exception: pass
                continue

            engines_used.add(source)
            # Convert normalised box → percentage center/width/height
            cx = (best['x'] + best['w'] / 2) * 100
            cy = (best['y'] + best['h'] / 2) * 100
            w  = best['w'] * 100
            h  = best['h'] * 100
            track.append({
                't': round(t_rel, 3),
                'cx_pct': round(cx, 2),
                'cy_pct': round(cy, 2),
                'w_pct':  round(w,  2),
                'h_pct':  round(h,  2),
                'source': source,
                'confidence': round(best.get('conf', 0.5), 3),
            })
            prev_center = (best['x'] + best['w'] / 2, best['y'] + best['h'] / 2)
            if progress_cb:
                try: progress_cb(i + 1, total)
                except Exception: pass

        if not track:
            return {
                'ok': False, 'engine': None, 'fallback_used': False,
                'keyframes': [], 'frames_total': total, 'frames_done': total,
                'error': 'No subject detected in this clip range.',
            }

        # 3) Smooth + downsample.
        smoothed = _smooth_track(track, alpha=smoothing) if smoothing > 0 else track
        # Re-tag smoothed entries' source so the UI knows.
        for kf in smoothed:
            kf['source'] = 'smoothed' if smoothing > 0 else kf.get('source', 'auto')
        keyframes = _downsample_keyframes(smoothed, max_keyframes)

        engine_label = (
            'mixed' if len(engines_used) > 1
            else next(iter(engines_used)) if engines_used
            else 'unknown'
        )
        return {
            'ok': True,
            'engine': engine_label,
            'fallback_used': fallback_count > 0,
            'fallback_count': fallback_count,
            'keyframes': keyframes,
            'frames_total': total,
            'frames_done': total,
            'error': None,
        }


# --- In-memory progress table for the API ---------------------------------
# Auto-track is fired in a background thread by the endpoint; the table
# below lets a status-poll endpoint read progress without sharing a lock
# with the worker. Single-process; survives only until server restart.

_AUTO_LOCK = threading.Lock()
_AUTO_STATE: Dict[str, Dict] = {}   # key = f"{job_id}/{clip_idx}"


def _set_progress(key, **kw):
    with _AUTO_LOCK:
        _AUTO_STATE.setdefault(key, {})
        _AUTO_STATE[key].update(kw)


def get_auto_state(key) -> Dict:
    with _AUTO_LOCK:
        return dict(_AUTO_STATE.get(key, {}))


def clear_auto_state(key):
    with _AUTO_LOCK:
        _AUTO_STATE.pop(key, None)


def run_auto_track_async(key: str,
                         video_path: str,
                         start: float,
                         duration: float,
                         fps: float = 4.0,
                         max_keyframes: int = 20,
                         smoothing: float = 0.4,
                         yolo_fallback: bool = True,
                         subject_signature: Optional[Dict] = None):
    """Fire-and-forget background runner. Updates _AUTO_STATE[key] with
    progress; final result lands in the same dict under 'result'.
    The /auto/status endpoint reads from there.

    SESSIE 24 B3 — `subject_signature` is a job-level prior produced from an
    earlier clip's auto-track. When given, `_pick_primary` biases detection
    selection toward boxes matching it in position+size, so the tracker
    locks onto the same subject (the DJ) across clips instead of latching
    onto whoever's biggest in each frame.
    """
    def _worker():
        _set_progress(key, done=False, frames_done=0, frames_total=0)
        def cb(done, total):
            _set_progress(key, frames_done=done, frames_total=total)
        try:
            result = detect_track(
                video_path, start, duration,
                fps=fps, max_keyframes=max_keyframes,
                smoothing=smoothing, yolo_fallback=yolo_fallback,
                subject_signature=subject_signature,
                progress_cb=cb,
            )
            _set_progress(key, done=True, result=result)
        except Exception as e:
            _set_progress(key, done=True, result={
                'ok': False, 'error': f'{type(e).__name__}: {e}',
                'keyframes': [],
            })
    t = threading.Thread(target=_worker, daemon=True, name=f'auto-track-{key}')
    t.start()
    return t


# SESSIE 24 B3 — Subject-signature helper. Computes a job-level "this is the
# DJ" signature from a clip's tracked keyframes. The signature is just the
# mean cx/cy/w/h converted to 0..1 — small enough to stash on job.json and
# fast enough to compute on every successful auto-track.
def compute_subject_signature(keyframes: List[Dict]) -> Optional[Dict]:
    """Return {'cx', 'cy', 'w', 'h'} all in 0..1, averaged over keyframes,
    or None if too few keyframes to be meaningful."""
    if not keyframes or len(keyframes) < 2:
        return None
    cx = cy = w = h = 0.0
    n = 0
    for k in keyframes:
        try:
            cx += float(k.get('cx_pct', 50)) / 100.0
            cy += float(k.get('cy_pct', 50)) / 100.0
            w  += float(k.get('w_pct',  30)) / 100.0
            h  += float(k.get('h_pct',  50)) / 100.0
            n += 1
        except (TypeError, ValueError):
            continue
    if n == 0:
        return None
    return {
        'cx': round(cx / n, 4),
        'cy': round(cy / n, 4),
        'w':  round(w  / n, 4),
        'h':  round(h  / n, 4),
        'samples': n,
    }
