"""
Video cutting and export pipeline.
Takes detected clip timestamps and cuts video into social-ready clips.
Outputs both landscape (original) and vertical (9:16) versions.

Speed-optimized with:
- GPU-accelerated encoding (VideoToolbox on macOS, NVENC on Linux)
- Parallel landscape + vertical encoding via subprocess.Popen (no filter_complex split)
- Fast keyframe seeking (-ss before -i)
- Thumbnail extraction after clip encode
- 4 parallel workers (each runs 2 FFmpeg simultaneously = 8 total GPU processes)
- Encoder detected once in main process and passed to workers (avoids spawn cache loss)
"""

import subprocess
import os
import json
import csv
import platform
import re
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


# ---------------------------------------------------------------------------
# Hardware encoder detection (called once in main process, passed to workers)
# ---------------------------------------------------------------------------

def detect_hw_encoder():
    """
    Detect the best available H.264 hardware encoder.
    Returns (encoder_name, quality_args_list).
    Always returns a valid encoder (falls back to libx264).
    """
    system = platform.system()

    if system == 'Darwin':
        # macOS: VideoToolbox (Apple Silicon / Intel GPU)
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True, text=True, timeout=5
            )
            if 'h264_videotoolbox' in result.stdout:
                print("  [GPU] Using h264_videotoolbox (Apple Silicon)")
                return ('h264_videotoolbox', ['-q:v', '50', '-profile:v', 'high'])
        except Exception:
            pass

    elif system == 'Linux':
        # Linux: NVENC (NVIDIA GPU)
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True, text=True, timeout=5
            )
            if 'h264_nvenc' in result.stdout:
                print("  [GPU] Using h264_nvenc (NVIDIA)")
                return ('h264_nvenc', ['-preset', 'p4', '-cq', '23', '-profile:v', 'high'])
        except Exception:
            pass

    # Fallback: software encoding
    print("  [CPU] Using libx264 software encoder")
    return ('libx264', ['-preset', 'fast', '-crf', '23'])


# ---------------------------------------------------------------------------
# System font detection
# ---------------------------------------------------------------------------

def _get_system_font():
    """Get a suitable system font path for FFmpeg drawtext overlay."""
    system = platform.system()
    if system == 'Darwin':
        candidates = [
            '/System/Library/Fonts/Helvetica.ttc',
            '/System/Library/Fonts/SFNSMono.ttf',
            '/Library/Fonts/Arial.ttf',
            '/System/Library/Fonts/Supplemental/Arial.ttf',
        ]
    elif system == 'Windows':
        candidates = [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/segoeui.ttf',
        ]
    else:
        candidates = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/TTF/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


# ---------------------------------------------------------------------------
# Audio extraction (speed: use fast codec, no video decode, 11025 Hz)
# ---------------------------------------------------------------------------

def extract_audio(video_path, output_path):
    """
    Extract audio from video file for analysis ONLY.
    Uses 11025 Hz mono — sufficient for sub-bass (20–250 Hz) + percussion detection.
    Half the data vs 22050 Hz → faster analysis, smaller temp file.

    NOTE: This file is used exclusively for beat/drop detection and is deleted
    after analysis. Output clips are cut directly from the original video source
    and preserve the full 20 Hz–20 kHz audio spectrum (see _build_landscape_cmd /
    _build_vertical_cmd which use the original video_path with 44.1 kHz AAC 320k).
    """
    print(f"  Extracting audio from video (analysis-only at 11025 Hz)...")
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '11025', '-ac', '1',
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")
    print(f"  Audio extracted to {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Video info
# ---------------------------------------------------------------------------

def get_video_info(video_path):
    """Get video dimensions and codec info."""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', '-show_format', video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    info = json.loads(result.stdout)
    video_stream = None
    for stream in info.get('streams', []):
        if stream['codec_type'] == 'video':
            video_stream = stream
            break

    if not video_stream:
        raise RuntimeError("No video stream found")

    raw_dur = info.get('format', {}).get('duration', '') or ''
    try:
        duration = float(raw_dur)
    except (ValueError, TypeError):
        duration = 0.0

    return {
        'width': int(video_stream['width']),
        'height': int(video_stream['height']),
        'duration': duration,
        'codec': video_stream['codec_name'],
    }


# ---------------------------------------------------------------------------
# Filter builders
# ---------------------------------------------------------------------------

def _build_overlay_filter(overlay_text, video_height, is_vertical=False):
    """Build FFmpeg drawtext filter for text overlay."""
    if not overlay_text or not overlay_text.get('text'):
        return None
    # SESSIE 22 — drawtext-missing guard. Silently skips rendering this
    # legacy single-text overlay on ffmpeg builds without libfreetype.
    if not _ffmpeg_has_drawtext():
        return None

    text = overlay_text['text']
    position = overlay_text.get('position', 'bottom')
    # Fix font_size=0 edge case — use sensible defaults
    font_size = overlay_text.get('font_size') or (24 if is_vertical else 32)
    text_escaped = text.replace("'", "\\'")

    if position == 'top':
        y_pos = f"{int(font_size * 0.5)}"
    else:
        y_pos = f"h-{int(font_size * 1.5)}"

    font_path = _get_system_font()
    font_param = f"fontfile='{font_path}':" if font_path else ""
    drawtext = (
        f"drawtext={font_param}"
        f"text='{text_escaped}':"
        f"fontsize={font_size}:"
        f"fontcolor=white:"
        f"x=(w-text_w)/2:"
        f"y={y_pos}:"
        f"box=1:"
        f"boxcolor=black@0.5:"
        f"boxborderw=5:"
        f"line_spacing=5"
    )
    return drawtext


# ---------------------------------------------------------------------------
# SESSIE 21 — Brand Stack F4: per-clip text layers + brand logo overlay.
# ---------------------------------------------------------------------------
# These helpers are used by every re-export path (process_clips, recut_clip,
# export_with_preset, split_clip_at, export_clip_with_settings). They are
# additive: if a job has no text_overlays.json and the brand_kit has no
# logo, every path falls back to the legacy "no extra filters" behaviour.
#
# Why textfile= over text=  --------------------------------------------------
# FFmpeg's drawtext filter has gnarly escaping rules for colons, single
# quotes, backslashes, percents and brackets. The textfile= variant reads
# the text from a UTF-8 file on disk, so we can store *exactly* what the
# user typed (including emoji, accented characters and stray quotes)
# without juggling per-character escapes that differ between ffmpeg builds.
# We dump each layer's text to a sibling file under the job dir at render
# time and clean it up after the run.

# SESSIE 22 — drawtext-availability probe. Some ffmpeg builds (notably
# the default homebrew bottle without --enable-libfreetype) ship without
# the drawtext filter, which makes our text-overlay + BPM-stamp pipeline
# blow up with "No such filter: 'drawtext'". We probe once at module-import
# and silently skip text filters when it's missing — the user sees a clear
# warning in the startup log + HANDOVER explains the homebrew workaround.
_HAS_DRAWTEXT = None  # tri-state: None=untested, True=available, False=missing


def _ffmpeg_has_drawtext():
    """Probe `ffmpeg -filters` once and cache the result. True if drawtext
    is compiled in. False otherwise (text overlays will degrade silently)."""
    global _HAS_DRAWTEXT
    if _HAS_DRAWTEXT is not None:
        return _HAS_DRAWTEXT
    try:
        r = subprocess.run(['ffmpeg', '-hide_banner', '-filters'],
                           capture_output=True, text=True, timeout=5)
        _HAS_DRAWTEXT = (' drawtext ' in r.stdout) or ('\ndrawtext ' in r.stdout) or ('T..  drawtext' in r.stdout)
        if not _HAS_DRAWTEXT:
            sys.stderr.write(
                "[cutter] WARNING: ffmpeg is built without libfreetype → drawtext filter missing. "
                "Text overlays + BPM/Key stamp will be SKIPPED on this install. "
                "Fix on macOS: `brew uninstall ffmpeg && brew install ffmpeg --with-freetype` "
                "or use `brew tap homebrew-ffmpeg/ffmpeg && brew install homebrew-ffmpeg/ffmpeg/ffmpeg --with-fdk-aac --with-libass --with-freetype`. "
                "Image-based logo overlays still work.\n"
            )
    except Exception:
        _HAS_DRAWTEXT = False
    return _HAS_DRAWTEXT


def _hex_to_ffmpeg_color(hex_str, alpha=None):
    """Translate '#rrggbb' / '#rgb' to ffmpeg's '0xRRGGBB[@a.a]' colour spec."""
    s = (hex_str or '').lstrip('#').strip()
    if len(s) == 3:
        s = ''.join(c*2 for c in s)
    if len(s) < 6:
        s = (s + '000000')[:6]
    s = s[:6]
    out = '0x' + s.upper()
    if alpha is not None:
        out += f'@{max(0.0, min(1.0, float(alpha))):.2f}'
    return out


def _write_layer_textfile(job_dir, layer_id, text):
    """Persist a single drawtext payload as UTF-8 (no BOM). Returns path."""
    d = os.path.join(job_dir, 'text_layers')
    os.makedirs(d, exist_ok=True)
    safe_id = re.sub(r'[^A-Za-z0-9_-]', '', str(layer_id or 'layer'))[:32] or 'layer'
    path = os.path.join(d, safe_id + '.txt')
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text or '')
    return path


def _escape_drawtext_path(p):
    """Drawtext expects single-quoted filter-graph values; backslash and
    apostrophe are the only escapes that matter for filenames on macOS."""
    return (p or '').replace('\\', '\\\\').replace("'", "\\'")


def _build_text_layer_filters(layers, job_dir, target_w, target_h,
                              brand_fonts=None, system_font=None):
    """Return a list of drawtext filter strings for the supplied layers.

    layers      — list of dicts (output/<job>/text_overlays.json schema)
    job_dir     — used for the textfile= sidecars
    target_w/h  — render-frame dimensions in px (vertical=1080x1920, landscape varies)
    brand_fonts — list of brand-kit font entries; we look up by `id`
    system_font — fallback font path for layers without a font_id
    """
    if not layers:
        return []
    # SESSIE 22 — silently skip when ffmpeg lacks drawtext (homebrew default).
    if not _ffmpeg_has_drawtext():
        return []
    brand_by_id = { (f.get('id') or ''): f for f in (brand_fonts or []) }

    filters = []
    for L in layers:
        text = (L.get('text') or '').strip()
        if not text:
            continue
        layer_id = L.get('id') or 'layer'
        textfile = _write_layer_textfile(job_dir, layer_id, text)
        # Resolve font: brand-kit first (must exist on disk), else system fallback.
        font_entry = brand_by_id.get(L.get('font_id') or '') if L.get('font_id') else None
        font_path = (font_entry or {}).get('path') if font_entry and os.path.exists((font_entry or {}).get('path') or '') else None
        if not font_path:
            font_path = system_font

        # Geometry: size_pct + x/y_pct are relative to the render frame width
        # (size) and frame dimensions (position). We center the anchor on the
        # text bounding box so the live HTML preview and the burned-in pixels
        # land in the same spot.
        try:
            size_pct = float(L.get('size_pct') or 6)
        except Exception:
            size_pct = 6
        fontsize = max(10, int((size_pct / 100.0) * target_w))
        # x/y_pct relative to frame center
        try:
            x_pct = float(L.get('x_pct') if L.get('x_pct') is not None else 50)
            y_pct = float(L.get('y_pct') if L.get('y_pct') is not None else 80)
        except Exception:
            x_pct, y_pct = 50, 80
        x_expr = f"(w*{x_pct:.3f}/100)-text_w/2"
        y_expr = f"(h*{y_pct:.3f}/100)-text_h/2"

        # Colour + optional background fill
        color = _hex_to_ffmpeg_color(L.get('color') or '#ffffff')
        # SESSIE 41 (Fase 5) — background schema:
        #   L['bg'] == None / falsy  → geen achtergrond
        #   L['bg'] == True          → legacy hardcoded zwart 55% (back-compat)
        #   L['bg'] == {color, opacity} → vrije kleur + opacity 0..1
        box_part = ''
        bg = L.get('bg')
        if bg:
            if isinstance(bg, dict):
                bg_color = bg.get('color') or '#000000'
                try:
                    bg_alpha = float(bg.get('opacity', 0.55))
                except Exception:
                    bg_alpha = 0.55
                bg_alpha = max(0.0, min(1.0, bg_alpha))
            else:
                # Legacy bool / truthy → defaults
                bg_color = '#000000'
                bg_alpha = 0.55
            box_color_ff = _hex_to_ffmpeg_color(bg_color)
            box_part = f':box=1:boxcolor={box_color_ff}@{bg_alpha:.2f}:boxborderw=12'

        # Time window — drawtext's `enable` accepts ffmpeg's expression syntax.
        try:
            in_sec  = max(0.0, float(L.get('in_sec') or 0))
            out_sec = max(in_sec + 0.05, float(L.get('out_sec') or 9999))
        except Exception:
            in_sec, out_sec = 0, 9999
        # NOTE: enable/alpha/y expressions live inside single-quoted parameter
        # values below, so commas inside the expressions do NOT need to be
        # escaped — ffmpeg's parser keeps them intact within '...'.
        enable_expr = f"between(t,{in_sec:.3f},{out_sec:.3f})"

        # Animation: fade in/out (alpha), slide-up (y), or none. The "pop"
        # option from the UI degrades to fade here because drawtext's
        # fontsize is a literal int, not an expression — close-enough for v1.
        anim = L.get('anim') or 'fade'
        FT = 0.28  # transition time in seconds
        alpha_expr = '1'
        if anim in ('fade', 'pop'):
            alpha_expr = (
                f"if(lt(t,{in_sec:.3f}+{FT}),(t-{in_sec:.3f})/{FT},"
                f"if(gt(t,{out_sec:.3f}-{FT}),max(({out_sec:.3f}-t)/{FT},0),1))"
            )
        if anim == 'slide-up':
            slide_amount = int(fontsize * 1.2)
            # y starts BELOW its final pos and rises into place over FT seconds.
            y_expr = (
                f"if(lt(t,{in_sec:.3f}+{FT}),"
                f"((h*{y_pct:.3f}/100)-text_h/2)+{slide_amount}*(1-(t-{in_sec:.3f})/{FT}),"
                f"(h*{y_pct:.3f}/100)-text_h/2)"
            )

        # Weight: ffmpeg has no native "bold". If the user picked Bold AND
        # the chosen font has a bold variant via the same fontfile, the
        # rendered glyph will be bold inherently. We emulate "synthetic
        # bold" by drawing the text twice with a small horizontal offset
        # — cheap but reads as bold at all sizes. Skip for now to keep
        # the filter chain compact; users can upload a bold-weight font.

        # x and y get single-quoted because the slide-up animation puts
        # commas inside the y expression — without quoting they'd be parsed
        # as filter-separator commas and the whole filtergraph would break.
        parts = [
            f"drawtext=textfile='{_escape_drawtext_path(textfile)}'",
            f"fontsize={fontsize}",
            f"fontcolor={color}",
            f"x='{x_expr}'",
            f"y='{y_expr}'",
            f"alpha='{alpha_expr}'",
            f"enable='{enable_expr}'",
            "line_spacing=4",
            "borderw=0",
        ]
        if font_path:
            parts.insert(1, f"fontfile='{_escape_drawtext_path(font_path)}'")
        if box_part:
            parts.append(box_part.lstrip(':'))
        filters.append(':'.join(parts))
    return filters


def _load_keyframes_for_clip(job_id, output_dir, clip_index):
    """SESSIE 22 — load tracking keyframes if present. Returns None when no
    tracking file exists for this clip; returns dict otherwise."""
    if not job_id or not output_dir or clip_index is None:
        return None
    p = os.path.join(output_dir, 'tracking', f'clip_{int(clip_index):03d}.json')
    if not os.path.exists(p):
        return None
    try:
        with open(p, 'r') as f:
            data = json.load(f) or {}
        if not data.get('keyframes'):
            return None
        return data
    except Exception:
        return None


def _build_tracked_vertical_crop(keyframes, src_w, src_h, crop_mode='pan',
                                 target_aspect=None):
    """SESSIE 22 / SESSIE 30c - Build an ffmpeg `crop` filter where the
    crop window follows the keyframes over time. Returns the filter string
    or None if there's nothing to track.

    `target_aspect` is the output w/h ratio. Defaults to 9/16 (vertical
    portrait). Pass 1.0 for 1:1 square or 0.8 for 4:5 portrait.

    Two modes:

    * `crop_mode='pan'` (DEFAULT, new in SESSIE 30c):
        Crop is FULL source height x (src_h * target_aspect) pixels wide.
        Only the horizontal position (x) interpolates between keyframes.
        Camera pans left-right but the full scene height stays visible.
    * `crop_mode='zoom'` (opt-in):
        Original SESSIE 22 behaviour - crop window tightens around the
        DJ and tracks both x and y. For a tight close-up.
    """
    if src_w <= 0 or src_h <= 0:
        return None
    target_ratio = float(target_aspect) if target_aspect else (9.0 / 16.0)

    # LETTERBOX mode (SESSIE 31): no crop at all. Caller is expected to
    # pass scale=W:H:force_original_aspect_ratio=decrease + pad=W:H so the
    # whole source frame is letterboxed inside the target aspect. We return
    # a sentinel string the cmd builder recognises.
    if crop_mode == 'letterbox':
        return '__LETTERBOX__'

    if not keyframes:
        return None

    # PAN mode: fixed full-height crop window, only x moves.
    if crop_mode == 'pan':
        # Pan crop is always full source height; width = h * target_ratio.
        pan_w = int(src_h * target_ratio)
        pan_w -= pan_w % 2
        if pan_w >= src_w:
            # Source is already narrower than 9:16 - nothing to pan over.
            # Fall through to a static centred crop.
            pan_w = src_w - (src_w % 2)
        pan_h = src_h - (src_h % 2)
        if pan_w <= 0 or pan_h <= 0:
            return None
        # Collect x positions per keyframe from cx_pct only.
        kfs_x = []
        for kf in keyframes:
            cx = (kf.get('cx_pct', 50) / 100.0) * src_w
            x  = max(0, min(src_w - pan_w, cx - pan_w / 2))
            kfs_x.append({'t': float(kf.get('t', 0)),
                          'x': x,
                          'y': 0,
                          'w': pan_w,
                          'h': pan_h})
        if not kfs_x:
            return None
        if len(kfs_x) == 1:
            x_expr = f"{int(kfs_x[0]['x'])}"
        elif len(kfs_x) > 8:
            print(f"  [WARN] Pan-tracking has {len(kfs_x)} keyframes, only first 8 will drive crop")
            kfs_x = kfs_x[:8]
            x_expr, _y = _build_keyframe_lerp_exprs(kfs_x)
        else:
            x_expr, _y = _build_keyframe_lerp_exprs(kfs_x)
        # y is constant (0). h is full source height. Only x animates.
        return f"crop={pan_w}:{pan_h}:x='{x_expr}':y=0"

    # ZOOM mode (legacy SESSIE 22): width/height tighten around the DJ.
    kfs = []
    for kf in keyframes:
        # Convert percentages to pixels in the source frame.
        cx = (kf.get('cx_pct', 50) / 100.0) * src_w
        cy = (kf.get('cy_pct', 50) / 100.0) * src_h
        w  = (kf.get('w_pct',  40) / 100.0) * src_w
        h  = (kf.get('h_pct',  70) / 100.0) * src_h
        # Enforce 9:16 aspect - pick the constraining dim.
        if w / max(1, h) > target_ratio:
            w = h * target_ratio
        else:
            h = w / target_ratio
        # Clamp so the box stays inside the frame.
        w = max(64, min(src_w, w))
        h = max(64, min(src_h, h))
        x = max(0, min(src_w - w, cx - w / 2))
        y = max(0, min(src_h - h, cy - h / 2))
        kfs.append({'t': float(kf.get('t', 0)), 'x': x, 'y': y, 'w': w, 'h': h})
    if not kfs:
        return None
    out_w = int(max(k['w'] for k in kfs))
    out_h = int(max(k['h'] for k in kfs))
    out_w -= out_w % 2; out_h -= out_h % 2
    if out_w <= 0 or out_h <= 0:
        return None

    if len(kfs) == 1:
        x_expr = f"{int(kfs[0]['x'])}"
        y_expr = f"{int(kfs[0]['y'])}"
    elif len(kfs) > 8:
        print(f"  [WARN] Zoom-tracking has {len(kfs)} keyframes, only first 8 will drive crop")
        kfs = kfs[:8]
        x_expr, y_expr = _build_keyframe_lerp_exprs(kfs)
    else:
        x_expr, y_expr = _build_keyframe_lerp_exprs(kfs)

    return f"crop={out_w}:{out_h}:x='{x_expr}':y='{y_expr}'"


def _build_keyframe_lerp_exprs(kfs):
    """Linear-interpolate between consecutive keyframes via nested
    if(lt(t,T_next), lerp, next-block). Returns (x_expr, y_expr)."""
    # Sort defensively.
    kfs = sorted(kfs, key=lambda k: k['t'])
    def lerp(a, b, attr):
        t0, t1 = a['t'], b['t']
        v0, v1 = a[attr], b[attr]
        # avoid divide-by-zero for ill-formed keyframes
        if abs(t1 - t0) < 1e-3:
            return f"{int(v1)}"
        return f"({int(v0)}+({int(v1)}-{int(v0)})*(t-{t0:.3f})/{t1-t0:.3f})"
    def build_axis(attr):
        # Before first KF: stick at first. After last: stick at last.
        # Between: lerp.
        expr = f"{int(kfs[-1][attr])}"
        # Build inside-out so the innermost ends with the "after last" case.
        for i in range(len(kfs) - 2, -1, -1):
            a = kfs[i]
            b = kfs[i + 1]
            interp = lerp(a, b, attr)
            expr = f"if(lt(t,{b['t']:.3f}),{interp},{expr})"
        # Before first KF: pin to first.
        expr = f"if(lt(t,{kfs[0]['t']:.3f}),{int(kfs[0][attr])},{expr})"
        return expr
    return build_axis('x'), build_axis('y')


def _build_bpm_stamp_filter(bpm_cfg, clip_data, target_w, target_h,
                             brand_fonts=None, system_font=None):
    """SESSIE 22 — build a drawtext filter that burns "129 BPM · 7A" into
    a corner of the clip. Returns a single drawtext string or None.

    bpm_cfg comes from brand_kit['bpm_stamp']: {enabled, corner, font_id, color, format}
    clip_data comes from analyzer clip metadata: must have 'bpm' (clip or set) and optional 'key'."""
    if not bpm_cfg or not bpm_cfg.get('enabled'):
        return None
    # SESSIE 22 — same drawtext-availability guard as text-overlays.
    if not _ffmpeg_has_drawtext():
        return None
    bpm = clip_data.get('bpm') or clip_data.get('set_bpm')
    key = clip_data.get('key')
    if not bpm:
        return None
    # Build the stamp text. User-chosen format ('bpm', 'bpm_key', 'key') so
    # power-users can pick what they want shown.
    fmt = bpm_cfg.get('format') or ('bpm_key' if key else 'bpm')
    if fmt == 'key' and key:
        txt = key
    elif fmt == 'bpm':
        txt = f"{int(round(bpm))} BPM"
    else:  # bpm_key
        txt = f"{int(round(bpm))} BPM" + (f" · {key}" if key else "")
    # Sanitize aggressively — this string ends up inside drawtext text=''
    # and we don't write it to a file like text-layers do (too tiny to be
    # worth the overhead). Strip the few characters that confuse drawtext.
    safe = (txt or '').replace('\\', '').replace("'", "").replace(':', '\\:')[:40]

    # Font: brand-kit override, else system fallback.
    font_path = system_font
    if bpm_cfg.get('font_id') and brand_fonts:
        f = next((e for e in brand_fonts if e.get('id') == bpm_cfg.get('font_id')), None)
        if f and os.path.exists((f or {}).get('path') or ''):
            font_path = f.get('path')

    color = _hex_to_ffmpeg_color(bpm_cfg.get('color') or '#ffffff')
    fontsize = max(14, int(target_w * 0.02))  # 2% of frame-width, sane for 1080p+
    margin = max(16, int(target_w * 0.025))

    corner = (bpm_cfg.get('corner') or 'bl').lower()
    if corner == 'tl':
        xy = f"x={margin}:y={margin}"
    elif corner == 'tr':
        xy = f"x=w-text_w-{margin}:y={margin}"
    elif corner == 'br':
        xy = f"x=w-text_w-{margin}:y=h-text_h-{margin}"
    else:  # bl default
        xy = f"x={margin}:y=h-text_h-{margin}"

    parts = [
        f"drawtext=text='{safe}'",
        f"fontsize={fontsize}",
        f"fontcolor={color}",
        xy,
        "box=1:boxcolor=0x000000@0.45:boxborderw=10",
    ]
    if font_path:
        parts.insert(1, f"fontfile='{_escape_drawtext_path(font_path)}'")
    return ':'.join(parts)


def _build_logo_overlay_segment(logo, target_w, target_h):
    """If a logo is configured, return (filter_segment_str, extra_inputs).

    The segment is what gets appended to a filter_complex string AFTER the
    text drawtext chain. It expects the previous chain to end at a labelled
    pad (e.g. [vfin]) and produces [vout]. When there's no logo, returns
    ('', []) and callers fall back to -vf.

    extra_inputs is empty here because we use movie= as a source filter
    inside the same graph — that way the existing -i video stays the
    only ffmpeg input and we don't have to renumber stream maps.
    """
    if not logo or not isinstance(logo, dict):
        return ('', [])
    p = logo.get('path')
    if not p or not os.path.exists(p):
        return ('', [])
    try:
        opacity = float(logo.get('opacity') or 0.9)
    except Exception:
        opacity = 0.9
    opacity = max(0.1, min(1.0, opacity))
    try:
        size_pct = float(logo.get('size_pct') or 12)
    except Exception:
        size_pct = 12
    size_pct = max(4, min(40, size_pct))
    logo_w = max(48, int(target_w * size_pct / 100.0))
    corner = (logo.get('corner') or 'tr').lower()
    margin = max(16, int(target_w * 0.025))
    if corner == 'tl':
        xy = f"x={margin}:y={margin}"
    elif corner == 'bl':
        xy = f"x={margin}:y=H-h-{margin}"
    elif corner == 'br':
        xy = f"x=W-w-{margin}:y=H-h-{margin}"
    else:  # tr default
        xy = f"x=W-w-{margin}:y={margin}"
    movie_src = (
        f"movie='{_escape_drawtext_path(p)}',"
        f"scale={logo_w}:-1,"
        f"format=rgba,colorchannelmixer=aa={opacity:.2f}"
        "[brandlogo]"
    )
    overlay = f"[vfin][brandlogo]overlay={xy}[vout]"
    return (f"{movie_src};{overlay}", [])


def _build_watermark_overlay_segment(watermark, target_w, target_h,
                                     in_label='vout', out_label='vwm'):
    """SESSIE 31 — Watermark overlay segment for filter_complex chains.
    Pattern is identical to `_build_logo_overlay_segment` but reads the
    `watermark` block from brand_kit.json (separate from `logo`). Returns
    (segment_str, used_bool). Caller controls labels so we can stack this
    after a logo (in=[vout], out=[vwm]) or directly on the base chain.

    watermark dict shape (from app.py):
      { path, ext, corner, opacity, size_pct, enabled, ... }
    """
    if not watermark or not isinstance(watermark, dict):
        return ('', False)
    if not watermark.get('enabled'):
        return ('', False)
    p = watermark.get('path')
    if not p or not os.path.exists(p):
        return ('', False)
    try:
        opacity = float(watermark.get('opacity'))
    except (TypeError, ValueError):
        opacity = 0.6
    opacity = max(0.05, min(1.0, opacity))
    try:
        size_pct = float(watermark.get('size_pct'))
    except (TypeError, ValueError):
        size_pct = 18.0
    size_pct = max(5.0, min(60.0, size_pct))
    wm_w = max(64, int(target_w * size_pct / 100.0))
    corner = (watermark.get('corner') or 'br').lower()
    margin = max(16, int(target_w * 0.025))
    if corner == 'tl':
        xy = f"x={margin}:y={margin}"
    elif corner == 'tr':
        xy = f"x=W-w-{margin}:y={margin}"
    elif corner == 'bl':
        xy = f"x={margin}:y=H-h-{margin}"
    elif corner == 'center':
        xy = "x=(W-w)/2:y=(H-h)/2"
    else:  # 'br' default
        xy = f"x=W-w-{margin}:y=H-h-{margin}"
    movie_src = (
        f"movie='{_escape_drawtext_path(p)}',"
        f"scale={wm_w}:-1,"
        f"format=rgba,colorchannelmixer=aa={opacity:.3f}"
        f"[brandwm]"
    )
    overlay = f"[{in_label}][brandwm]overlay={xy}[{out_label}]"
    return (f"{movie_src};{overlay}", True)


def _maybe_compose_brand_vf(base_chain, layers, logo, job_dir, target_w, target_h,
                            brand_fonts=None, bpm_cfg=None, clip_data=None,
                            watermark=None):
    """Tie together the existing base filter chain (string), the new text
    layers, optional BPM/Key stamp and an optional logo into ffmpeg flags
    ready to plug into a cmd.

    SESSIE 22 — added bpm_cfg + clip_data for the BPM/Key corner stamp.

    Returns a dict:
      {
        'mode':        'vf' | 'complex' | 'none',
        'vf':          string  (when mode == 'vf')
        'complex':     string  (when mode == 'complex')
        'map_v':       '[vout]' or None   (only set for complex)
      }
    Caller assembles the final ffmpeg argv around this.
    """
    sysfont = _get_system_font()
    drawtext_filters = _build_text_layer_filters(
        layers or [], job_dir, target_w, target_h,
        brand_fonts=brand_fonts, system_font=sysfont
    )
    bpm_filter = None
    if bpm_cfg and clip_data is not None:
        bpm_filter = _build_bpm_stamp_filter(
            bpm_cfg, clip_data, target_w, target_h,
            brand_fonts=brand_fonts, system_font=sysfont,
        )
    logo_segment, _extra = _build_logo_overlay_segment(logo, target_w, target_h)

    pieces = []
    if base_chain:
        pieces.append(base_chain)
    if drawtext_filters:
        pieces.extend(drawtext_filters)
    if bpm_filter:
        pieces.append(bpm_filter)

    # SESSIE 31 — figure out whether the watermark image is going to render.
    # It comes AFTER the logo in the chain so the watermark always sits on
    # top of the logo if both are configured.
    has_logo = bool(logo_segment)
    if has_logo:
        wm_in_label = 'vout'   # logo produces [vout] — chain watermark on top of it
    else:
        wm_in_label = 'vfin'   # no logo → watermark consumes the linear chain
    wm_segment, has_wm = _build_watermark_overlay_segment(
        watermark, target_w, target_h,
        in_label=wm_in_label, out_label='vwm',
    )

    if not pieces and not has_logo and not has_wm:
        return {'mode': 'none', 'vf': '', 'complex': '', 'map_v': None}

    if not has_logo and not has_wm:
        # Simple linear chain — fine for -vf.
        return {'mode': 'vf', 'vf': ','.join(pieces), 'complex': '', 'map_v': None}

    # filter_complex path. Wrap the linear chain into [vfin].
    linear = ','.join(pieces) if pieces else 'null'
    fc = f"[0:v]{linear}[vfin]"
    final_label = '[vfin]'
    if has_logo:
        fc += f";{logo_segment}"
        final_label = '[vout]'
    if has_wm:
        fc += f";{wm_segment}"
        final_label = '[vwm]'
    return {'mode': 'complex', 'vf': '', 'complex': fc, 'map_v': final_label}


# SESSIE 42 — Built-in & system font helpers.
# Built-ins live in static/fonts/builtin/ (shipped with the app); manifest
# describes the 11 bundled families. System-fonts are scanned by app.py
# and persisted to DATA_DIR/system_fonts_cache.json so we can resolve a
# font_id to an absolute on-disk path without re-running the scan here.

def _load_builtin_fonts():
    """Read static/fonts/builtin/manifest.json + resolve files to absolute paths.
    Returns list of {id, family, path, ext} matching brand-kit shape so the
    rest of _build_text_layer_filters can treat them identically."""
    here = os.path.dirname(os.path.abspath(__file__))
    builtin_dir = os.path.join(here, 'static', 'fonts', 'builtin')
    manifest_path = os.path.join(builtin_dir, 'manifest.json')
    if not os.path.isfile(manifest_path):
        return []
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f) or []
    except Exception:
        return []
    out = []
    for entry in data:
        fp = os.path.join(builtin_dir, entry.get('file') or '')
        if os.path.isfile(fp):
            out.append({
                'id':     entry.get('id'),
                'family': entry.get('family'),
                'path':   fp,
                'ext':    os.path.splitext(fp)[1].lstrip('.').lower() or 'ttf',
                'source': 'builtin',
            })
    return out


def _load_system_fonts_cache():
    """Read the cache file written by app.py after every system-font scan.
    Returns [] if the file doesn't exist yet (cutter then falls back to
    brand-kit + system font resolver only)."""
    # DATA_DIR isn't defined in cutter.py, mirror app.py's logic:
    data_dir = os.environ.get(
        "CLIP_LIVE_USER_DATA",
        os.path.dirname(os.path.abspath(__file__))
    )
    cache_path = os.path.join(data_dir, 'system_fonts_cache.json')
    if not os.path.isfile(cache_path):
        return []
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f) or {}
        return data.get('fonts') or []
    except Exception:
        return []


def _load_brand_assets_for_job(job_id, output_dir=None):
    """Load the brand kit + the job's text-overlays once per render call.
    Returns (brand_fonts_list, brand_logo_dict, overlays_by_clip_idx_str,
             bpm_cfg, watermark_dict).
    Safe to call when nothing has been configured — returns empties.

    SESSIE 22 — also returns bpm_cfg for the BPM/Key corner stamp.
    SESSIE 31 — also returns watermark for the brand watermark overlay."""
    overlays = {}
    if job_id and output_dir:
        ov_path = os.path.join(output_dir, 'text_overlays.json')
        if os.path.exists(ov_path):
            try:
                with open(ov_path, 'r') as f:
                    raw = json.load(f) or {}
                overlays = raw.get('clips') or {}
            except Exception:
                overlays = {}
    here = os.path.dirname(os.path.abspath(__file__))
    kit_path = os.path.join(here, 'brand_kit.json')
    brand_fonts, brand_logo, bpm_cfg, watermark = [], None, None, None
    if os.path.exists(kit_path):
        try:
            with open(kit_path, 'r') as f:
                kit = json.load(f) or {}
            brand_fonts = kit.get('fonts') or []
            brand_logo  = kit.get('logo')
            bpm_cfg     = kit.get('bpm_stamp')
            watermark   = kit.get('watermark')
        except Exception:
            pass
    # SESSIE 31 — BPM/Key corner stamp is force-disabled. Sjuul wants it
    # gone from both preview and exported clips. We keep the brand_kit
    # entry intact (for future re-enable) but never render the drawtext.
    if isinstance(bpm_cfg, dict):
        bpm_cfg = dict(bpm_cfg)
        bpm_cfg['enabled'] = False
    else:
        bpm_cfg = None
    # SESSIE 42 — merge built-in + system fonts into the same brand_fonts
    # list so _build_text_layer_filters resolves them via the same lookup.
    # Order matters for ID-collision-fallback: built-ins use kebab-case ids
    # (e.g. "bebas-neue"), brand-kit uses hex ids (e.g. "a3f2..."), and
    # system-fonts use hex too — but a different hash space so collisions
    # are vanishingly unlikely. We list brand-kit first so user uploads
    # take precedence over built-ins with the same family name.
    merged_fonts = list(brand_fonts) + _load_builtin_fonts() + _load_system_fonts_cache()
    return merged_fonts, brand_logo, overlays, bpm_cfg, watermark


def _build_clip_data_for_stamp(clip, job_bpm_info):
    """Return a minimal dict the BPM/Key stamp filter understands. Clips
    carry their own bpm/key when available; else fall back to the set-level
    detected values."""
    if not isinstance(clip, dict):
        clip = {}
    if not isinstance(job_bpm_info, dict):
        job_bpm_info = {}
    return {
        'bpm':     clip.get('bpm') or job_bpm_info.get('bpm'),
        'key':     clip.get('key') or job_bpm_info.get('key'),
        'set_bpm': job_bpm_info.get('bpm'),
        'set_key': job_bpm_info.get('key'),
    }


def _load_set_bpm_info_for_job(job_id, output_dir):
    """Read the persisted analyzer bpm dict for a job (set-level BPM + key).
    Cutter doesn't have access to app.py's `jobs` table so we rely on the
    on-disk job.json snapshot that's written when the analyzer finishes."""
    if not job_id or not output_dir:
        return {}
    snap_path = os.path.join(output_dir, 'job.json')
    if not os.path.exists(snap_path):
        return {}
    try:
        with open(snap_path, 'r') as f:
            snap = json.load(f) or {}
        bpm_info = snap.get('bpm') or {}
        return {
            'bpm': bpm_info.get('bpm'),
            'key': bpm_info.get('key'),
        }
    except Exception:
        return {}


def _layers_for_clip_index(overlays_map, clip_index):
    """Return the layer list for a given 1-based clip index, or []."""
    if not overlays_map or clip_index is None:
        return []
    return overlays_map.get(str(int(clip_index))) or []


def _build_audio_filter(normalize_audio=False, fade_duration=0.0, duration=None):
    """
    Build FFmpeg audio filter chain.

    Always resamples to 44100 Hz to guarantee the full 20 Hz–20 kHz spectrum
    is preserved in every output clip, regardless of the source sample rate.
    The codec (AAC 320k) then encodes that full bandwidth.

    `fade_duration` defaults to 0 (hard cut). Pass a positive value to opt in
    to audio fade-in / fade-out — kept for back-compat with explicit callers.
    """
    filters = []
    # Resample to 44100 Hz — ensures full 20 Hz–20 kHz spectrum in output
    filters.append("aresample=44100")
    if fade_duration > 0:
        filters.append(f"afade=t=in:st=0:d={fade_duration}")
        if duration:
            fade_out_start = max(0, duration - fade_duration)
            filters.append(f"afade=t=out:st={fade_out_start}:d={fade_duration}")
    if normalize_audio:
        filters.append("loudnorm=I=-14:TP=-1.5:LRA=11")
    return ','.join(filters)


def _get_vertical_crop(video_info):
    """Calculate 9:16 center crop parameters from source video."""
    src_w = video_info['width']
    src_h = video_info['height']
    target_ratio = 9 / 16

    if (src_w / src_h) > target_ratio:
        crop_h = src_h
        crop_w = int(src_h * target_ratio)
    else:
        crop_w = src_w
        crop_h = int(src_w / target_ratio)

    crop_w = crop_w - (crop_w % 2)
    crop_h = crop_h - (crop_h % 2)
    crop_x = (src_w - crop_w) // 2
    crop_y = (src_h - crop_h) // 2

    return crop_w, crop_h, crop_x, crop_y


# ---------------------------------------------------------------------------
# FFmpeg command builders — return command lists without running them
# ---------------------------------------------------------------------------

def _build_landscape_cmd(video_path, start, duration, output_path,
                         encoder, quality_args,
                         fade_duration=0.0, overlay_text=None, normalize_audio=False,
                         text_layers=None, brand_logo=None, brand_fonts=None,
                         job_dir=None, target_w=1920, target_h=1080,
                         bpm_cfg=None, clip_data=None, watermark=None):
    """Build FFmpeg command for landscape output. Does NOT run it.
    fade_duration defaults to 0 (hard cut). Pass >0 to opt in to fades.

    SESSIE 21 — text_layers / brand_logo / brand_fonts compose the Brand
    Stack drawtext + logo overlay on top of the existing chain. job_dir is
    needed for the textfile= sidecar files; defaults to output_path's dir
    if not supplied. target_w/h default to plausible landscape output."""
    base_filters = []
    if fade_duration > 0:
        # Guard against negative fade-out start (clips < 2×fade_duration)
        fade_out_st = max(0.0, duration - fade_duration)
        base_filters.append(f"fade=t=in:st=0:d={fade_duration}")
        base_filters.append(f"fade=t=out:st={fade_out_st}:d={fade_duration}")
    legacy_text = _build_overlay_filter(overlay_text, None, is_vertical=False)
    if legacy_text:
        base_filters.append(legacy_text)
    base_chain = ','.join(base_filters) if base_filters else ''

    if job_dir is None:
        job_dir = os.path.dirname(os.path.abspath(output_path))
    composed = _maybe_compose_brand_vf(
        base_chain, text_layers, brand_logo, job_dir, target_w, target_h,
        brand_fonts=brand_fonts, bpm_cfg=bpm_cfg, clip_data=clip_data,
        watermark=watermark,
    )

    afilter_str = _build_audio_filter(normalize_audio, fade_duration, duration)

    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start),        # Fast keyframe seek BEFORE input
        '-i', video_path,
        '-t', str(duration),
    ]
    if composed['mode'] == 'vf':
        cmd.extend(['-vf', composed['vf']])
    elif composed['mode'] == 'complex':
        cmd.extend(['-filter_complex', composed['complex'],
                    '-map', composed['map_v'], '-map', '0:a?'])
    cmd.extend([
        '-af', afilter_str,
        '-c:v', encoder, *quality_args,
        '-c:a', 'aac', '-b:a', '320k',
        '-movflags', '+faststart',
        output_path
    ])
    return cmd


def _build_vertical_cmd(video_path, start, duration, output_path,
                        video_info, encoder, quality_args,
                        fade_duration=0.0, overlay_text=None, normalize_audio=False,
                        text_layers=None, brand_logo=None, brand_fonts=None,
                        job_dir=None,
                        bpm_cfg=None, clip_data=None,
                        track_keyframes=None, track_crop_mode='pan',
                        watermark=None):
    """Build FFmpeg command for 9:16 vertical output. Does NOT run it.
    fade_duration defaults to 0 (hard cut). Pass >0 to opt in to fades.

    SESSIE 21 - see _build_landscape_cmd for the new Brand Stack params.
    SESSIE 22 - track_keyframes (optional) replaces the static centre-crop
    with a dynamic crop window that follows the keyframes over time.
    SESSIE 30c - track_crop_mode='pan'|'zoom'. Pan = full-height window
    that only pans left-right (preserves the whole scene). Zoom = the
    legacy behaviour where the window tightens around the DJ."""
    # SESSIE 22 / SESSIE 30c - if we have tracking keyframes, use the
    # dynamic crop expr instead of the static centre-crop. The scale+pad
    # steps stay the same so the output is still 1080x1920. The
    # `track_crop_mode` selects pan-only (default) vs the legacy zoom.
    tracked = None
    # SESSIE 31 — letterbox mode doesn't require keyframes; it just bypasses
    # the centre-crop and lets scale+pad handle the entire frame.
    if track_crop_mode == 'letterbox':
        try:
            tracked = _build_tracked_vertical_crop(
                track_keyframes or [],
                video_info.get('width', 0), video_info.get('height', 0),
                crop_mode='letterbox',
            )
        except Exception as e:
            print(f"  [WARN] letterbox build failed: {e}; falling back to centre-crop")
            tracked = None
    elif track_keyframes:
        try:
            tracked = _build_tracked_vertical_crop(
                track_keyframes, video_info.get('width', 0), video_info.get('height', 0),
                crop_mode=track_crop_mode,
            )
        except Exception as e:
            print(f"  [WARN] tracked crop build failed: {e}; falling back to centre-crop")
            tracked = None

    if tracked == '__LETTERBOX__':
        # SESSIE 31 — no crop, only scale-to-fit + pad. Whole source frame
        # stays visible inside a 1080x1920 black-bar letterbox.
        crop_scale = (
            f"scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"
        )
    elif tracked:
        crop_scale = (
            tracked + ","
            f"scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
        )
    else:
        crop_w, crop_h, crop_x, crop_y = _get_vertical_crop(video_info)
        crop_scale = (
            f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
            f"scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
        )

    base_filters = [crop_scale]
    if fade_duration > 0:
        fade_out_st = max(0.0, duration - fade_duration)
        base_filters.append(f"fade=t=in:st=0:d={fade_duration}")
        base_filters.append(f"fade=t=out:st={fade_out_st}:d={fade_duration}")
    legacy_text = _build_overlay_filter(overlay_text, 1920, is_vertical=True)
    if legacy_text:
        base_filters.append(legacy_text)
    base_chain = ','.join(base_filters)

    if job_dir is None:
        job_dir = os.path.dirname(os.path.abspath(output_path))
    composed = _maybe_compose_brand_vf(
        base_chain, text_layers, brand_logo, job_dir, 1080, 1920,
        brand_fonts=brand_fonts, bpm_cfg=bpm_cfg, clip_data=clip_data,
        watermark=watermark,
    )
    # Vertical always has a base chain (crop+scale+pad) so 'none' is unreachable.
    # The composed dict always returns 'vf' here unless a logo or watermark is set.

    afilter_str = _build_audio_filter(normalize_audio, fade_duration, duration)

    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start),        # Fast keyframe seek BEFORE input
        '-i', video_path,
        '-t', str(duration),
    ]
    if composed['mode'] == 'complex':
        cmd.extend(['-filter_complex', composed['complex'],
                    '-map', composed['map_v'], '-map', '0:a?'])
    else:
        cmd.extend(['-vf', composed['vf'] or base_chain])
    cmd.extend([
        '-af', afilter_str,
        '-c:v', encoder, *quality_args,
        '-c:a', 'aac', '-b:a', '320k',
        '-movflags', '+faststart',
        output_path
    ])
    return cmd


def _build_proxy_cmd(video_path, start, duration, output_path,
                     fade_duration=0.0, normalize_audio=False):
    """Build a fast, low-quality "proxy" clip — 720p H.264 with cheap encode
    settings. Used by the Bucket-D2 large-file pipeline to make the editor
    interactive within minutes of upload, while final-quality 1080p clips
    are deferred until the user opens or exports a clip.

    SPEC (2026-04-26): proxies are thumbnail-grade preview files (~1 MB each).
    All real-time editor playback can run off them; the export path swaps in
    the full-quality cut.

    fade_duration defaults to 0 (hard cut). Pass >0 to opt in to fades.
    """
    vfilters = ["scale=-2:720"]
    if fade_duration > 0:
        fade_out_st = max(0.0, duration - fade_duration)
        vfilters.append(f"fade=t=in:st=0:d={fade_duration}")
        vfilters.append(f"fade=t=out:st={fade_out_st}:d={fade_duration}")
    afilter_str = _build_audio_filter(normalize_audio, fade_duration, duration)
    return [
        'ffmpeg', '-y',
        '-ss', str(start),        # Fast keyframe seek BEFORE input
        '-i', video_path,
        '-t', str(duration),
        '-vf', ','.join(vfilters),
        '-af', afilter_str,
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        output_path,
    ]


def build_keyframe_index(video_path, max_seconds=None):
    """Probe the input for keyframe timestamps so clip cuts can snap to the
    nearest preceding keyframe — making seek essentially free even on a 10-hour
    file. Returns a sorted list of float timestamps (seconds).

    SPEC (2026-04-26 — Bucket D2): one ffprobe pass at upload time for any
    set whose duration > 30 minutes; cached on the job. None if probe fails.
    """
    cmd = [
        'ffprobe', '-v', 'error',
        '-skip_frame', 'nokey',
        '-select_streams', 'v:0',
        '-show_entries', 'frame=pts_time,key_frame',
        '-of', 'csv=print_section=0',
        video_path,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if out.returncode != 0:
            return None
        kf = []
        for line in (out.stdout or '').splitlines():
            parts = line.strip().split(',')
            if len(parts) < 2:
                continue
            try:
                t = float(parts[0])
                key = parts[1].strip() == '1'
            except (TypeError, ValueError):
                continue
            if key:
                kf.append(t)
                if max_seconds is not None and t > max_seconds:
                    break
        return sorted(set(kf)) or None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def snap_to_keyframe(t, keyframes, mode='before'):
    """Given a sorted list of keyframe timestamps, return the nearest one
    *before* (default) or *after* `t`. Falls through if `keyframes` is None
    or empty. Used by the large-file pipeline so each clip's `-ss` value sits
    on a real keyframe — eliminates wait-for-decode on big files.
    """
    if not keyframes:
        return t
    import bisect
    i = bisect.bisect_right(keyframes, t)
    if mode == 'before':
        if i == 0:
            return keyframes[0]
        return keyframes[i - 1]
    # after
    if i >= len(keyframes):
        return keyframes[-1]
    return keyframes[i]


def get_per_clip_waveform(audio_path, start, end, bins=600, sr=22050):
    """Compute a high-resolution peak envelope for a [start, end] slice of
    the source audio. Returns a list of `bins` peak values normalised to
    [0, 1]. Used by the editor's canvas waveform renderer.

    SPEC (2026-04-26 — Task #7): per-clip waveform cached on disk by the
    /api/waveform/<job> handler so subsequent requests are instant.
    """
    try:
        import librosa
        import numpy as np
    except ImportError:
        return None
    duration = max(0.1, float(end) - float(start))
    try:
        y, _sr = librosa.load(audio_path, sr=sr, mono=True,
                              offset=max(0.0, float(start)), duration=duration)
    except Exception:
        return None
    if y is None or len(y) == 0:
        return [0.0] * bins
    # Take the peak (max absolute value) per bucket — gives a true envelope
    # rather than RMS, so transients pop on the waveform.
    bucket = max(1, int(len(y) / max(1, bins)))
    peaks = []
    for i in range(0, len(y), bucket):
        chunk = y[i:i + bucket]
        if len(chunk) == 0:
            continue
        peaks.append(float(np.max(np.abs(chunk))))
        if len(peaks) >= bins:
            break
    if not peaks:
        return [0.0] * bins
    mx = max(peaks) or 1.0
    return [round(p / mx, 4) for p in peaks]


def _build_thumbnail_cmd(video_path, timestamp, output_path, width=1080):
    """Build FFmpeg command for thumbnail extraction. Does NOT run it.

    SPEC (2026-04-26): thumbnails are pulled at 1080px wide (was 480px) so
    retina cards render crisply. `-q:v 2` keeps each JPG <120KB.
    """
    return [
        'ffmpeg', '-y',
        '-ss', str(timestamp),    # Fast keyframe seek
        '-i', video_path,
        '-frames:v', '1',
        '-q:v', '2',
        '-vf', f'scale={width}:-1',
        output_path
    ]


# ---------------------------------------------------------------------------
# Single-clip worker for ProcessPoolExecutor
# Encodes landscape + vertical SIMULTANEOUSLY via subprocess.Popen
# ---------------------------------------------------------------------------

def _process_single_clip(args):
    """
    Worker function: processes one clip → landscape + vertical (in parallel) + thumbnail.

    Args tuple:
        (video_path, clip, output_dir, video_info, formats,
         overlay_text, normalize_audio, encoder, quality_args)

    Landscape and vertical are started simultaneously with Popen,
    then both waited for — so they encode in parallel within the worker.

    SESSIE 21 — also reads brand_kit.json + output/<job>/text_overlays.json
    to lay down per-clip drawtext layers and the brand logo on top of
    the existing crop+scale+pad+fade chain.
    """
    (video_path, clip, output_dir, video_info, formats,
     overlay_text, normalize_audio, encoder, quality_args) = args

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    clip_num = clip['index']
    clip_type = clip['type']
    start = clip['start']
    end = clip['end']
    duration = end - start
    # Hard cut by default — set to a positive value (e.g. 0.5) to re-enable
    # the 0.5 s in/out fades for both video and audio.
    fade_duration = 0.0

    # SESSIE 21 — Brand Stack F4: lookup the text layers for this clip and
    # the brand logo+font list. job_id is the basename of output_dir, which
    # is how app.py organises the per-job directories.
    job_id = os.path.basename(os.path.normpath(output_dir))
    brand_fonts, brand_logo, overlays_map, bpm_cfg, brand_watermark = _load_brand_assets_for_job(
        job_id, output_dir
    )
    # SESSIE 22 — set-level BPM/key for the corner stamp.
    set_bpm_info = _load_set_bpm_info_for_job(job_id, output_dir)
    text_layers = _layers_for_clip_index(overlays_map, clip_num)
    clip_data_for_stamp = _build_clip_data_for_stamp(clip, set_bpm_info)
    # SESSIE 22 TR1 / SESSIE 30c - load tracking keyframes (manual or
    # auto) AND the crop mode for this clip. Only fed into the vertical
    # export pipeline; landscape stays untouched.
    track_kfs = None
    track_mode = 'pan'
    try:
        track_info = _load_keyframes_for_clip(job_id, output_dir, clip_num)
        if track_info and track_info.get('keyframes'):
            track_kfs = track_info['keyframes']
            track_mode = track_info.get('crop_mode') or 'pan'
            if track_mode not in ('pan', 'zoom'):
                track_mode = 'pan'
    except Exception as e:
        print(f"  [WARN] tracking load failed for clip {clip_num}: {e}")
        track_kfs = None

    clip_result = {**clip, 'files': {}, 'thumbnail': None}

    landscape_path = None
    vertical_path = None
    thumb_fname = f"thumb_clip{clip_num:02d}.jpg"
    thumb_path = os.path.join(output_dir, thumb_fname)

    if 'landscape' in formats:
        landscape_path = os.path.join(
            output_dir, f"{base_name}_clip{clip_num:02d}_{clip_type}_landscape.mp4"
        )
    if 'vertical' in formats:
        vertical_path = os.path.join(
            output_dir, f"{base_name}_clip{clip_num:02d}_{clip_type}_vertical.mp4"
        )

    # --- Start both encodes simultaneously via Popen ---
    procs = []

    if landscape_path:
        cmd_l = _build_landscape_cmd(
            video_path, start, duration, landscape_path,
            encoder, quality_args, fade_duration, overlay_text, normalize_audio,
            text_layers=text_layers, brand_logo=brand_logo,
            brand_fonts=brand_fonts, job_dir=output_dir,
            target_w=video_info.get('width') or 1920,
            target_h=video_info.get('height') or 1080,
            bpm_cfg=bpm_cfg, clip_data=clip_data_for_stamp,
            watermark=brand_watermark,
        )
        proc_l = subprocess.Popen(cmd_l, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(('landscape', proc_l, landscape_path))

    if vertical_path:
        cmd_v = _build_vertical_cmd(
            video_path, start, duration, vertical_path,
            video_info, encoder, quality_args, fade_duration, overlay_text, normalize_audio,
            text_layers=text_layers, brand_logo=brand_logo,
            brand_fonts=brand_fonts, job_dir=output_dir,
            bpm_cfg=bpm_cfg, clip_data=clip_data_for_stamp,
            track_keyframes=track_kfs, track_crop_mode=track_mode,
            watermark=brand_watermark,
        )
        proc_v = subprocess.Popen(cmd_v, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(('vertical', proc_v, vertical_path))

    # --- Wait for all encodes to finish (timeout: 10 min per clip) ---
    for fmt, proc, out_path in procs:
        try:
            returncode = proc.wait(timeout=600)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            print(f"  [ERROR] Clip {clip_num} {fmt}: ffmpeg timed out after 600s, skipping")
            continue

        # Check file exists AND has non-zero size
        if returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            clip_result['files'][fmt] = out_path
        else:
            # Retry with software encoder if hardware failed
            if encoder != 'libx264':
                retry_cmd = None
                if fmt == 'landscape':
                    retry_cmd = _build_landscape_cmd(
                        video_path, start, duration, out_path,
                        'libx264', ['-preset', 'fast', '-crf', '23'],
                        fade_duration, overlay_text, normalize_audio,
                        text_layers=text_layers, brand_logo=brand_logo,
                        brand_fonts=brand_fonts, job_dir=output_dir,
                        target_w=video_info.get('width') or 1920,
                        target_h=video_info.get('height') or 1080,
                        watermark=brand_watermark,
                    )
                else:
                    retry_cmd = _build_vertical_cmd(
                        video_path, start, duration, out_path,
                        video_info, 'libx264', ['-preset', 'fast', '-crf', '23'],
                        fade_duration, overlay_text, normalize_audio,
                        text_layers=text_layers, brand_logo=brand_logo,
                        brand_fonts=brand_fonts, job_dir=output_dir,
                        watermark=brand_watermark,
                    )
                if retry_cmd:
                    result = subprocess.run(retry_cmd, capture_output=True, text=True,
                                            timeout=600)
                    if (result.returncode == 0 and os.path.exists(out_path)
                            and os.path.getsize(out_path) > 0):
                        clip_result['files'][fmt] = out_path
                        print(f"  [WARN] Clip {clip_num} {fmt}: GPU failed, re-encoded with libx264")

    # --- Generate thumbnail (fast single seek, after both encodes) ---
    peak_time = clip.get('peak_time', start + duration / 2)
    thumb_cmd = _build_thumbnail_cmd(video_path, peak_time, thumb_path)
    try:
        subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=60)
    except subprocess.TimeoutExpired:
        print(f"  [WARN] Clip {clip_num}: thumbnail generation timed out, skipping")

    if os.path.exists(thumb_path):
        clip_result['thumbnail'] = thumb_fname

    return clip_result


# ---------------------------------------------------------------------------
# Parallel clip processing (main entry point)
# ---------------------------------------------------------------------------

# 6 workers × 2 simultaneous FFmpeg each = 12 total GPU processes.
# M4-class Media Engine + 4 efficiency cores can absorb this without throttling;
# 4 workers was leaving headroom on the table during 30+-clip jobs. The
# `min(..., os.cpu_count(), len(clips))` cap below still protects smaller
# machines and short jobs from over-subscription.
MAX_PARALLEL_WORKERS = 6


def process_proxy_clips(video_path, clips, output_dir, keyframes=None,
                        normalize_audio=False, progress_callback=None):
    """Cut every clip into a fast 720p H.264 PROXY file. Used by the
    Bucket-D2 large-file pipeline to give the editor something playable in
    minutes instead of waiting for full-quality landscape+vertical encodes
    on every cue.

    Returns list of clip dicts annotated with `clip['files']['proxy']`.
    Final-quality cuts are produced lazily by `process_clips_for` (single
    clip, on-demand) when the user opens or exports a cue.
    """
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]
    out = []
    for i, clip in enumerate(clips):
        clip_num = clip.get('index', i + 1)
        clip_type = clip.get('type', 'cue')
        start = clip.get('start', 0)
        end = clip.get('end', start + 15)
        # Snap start to the nearest preceding keyframe so ffmpeg's input-side
        # `-ss` is essentially free.
        kf_start = snap_to_keyframe(start, keyframes, mode='before') if keyframes else start
        # Trim a small lead-in via output-side seek so the visible clip still
        # begins at the analyser's intended start.
        lead = max(0.0, start - kf_start)
        proxy_path = os.path.join(output_dir, f"{base}_clip{clip_num:02d}_{clip_type}_proxy.mp4")
        if progress_callback:
            progress_callback(clip_num, clip, 0, 'start')
        # BUGFIX (2026-04-28): the 4th positional arg `output_path` was
        # missing — every proxy encode failed with "TypeError: _build_proxy_cmd()
        # missing 1 required positional argument: 'output_path'" right after
        # the 5-minute analyser pass completed.
        cmd = _build_proxy_cmd(video_path, kf_start, (end - kf_start),
                               proxy_path,
                               normalize_audio=normalize_audio)
        # If we snapped to a keyframe behind the requested start, drop the
        # lead-in seconds with an output-side `-ss` placed AFTER `-i`.
        if lead > 0.05:
            try:
                ix = cmd.index(video_path)
                cmd[ix + 1: ix + 1] = ['-ss', str(lead)]
            except ValueError:
                # `video_path` not found verbatim — skip the lead trim rather
                # than corrupt the cmd. Worst case the proxy starts a frame
                # or two early relative to the analyser's intended start.
                pass
        try:
            r = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=180)
            ok = (r.returncode == 0 and os.path.exists(proxy_path)
                  and os.path.getsize(proxy_path) > 0)
        except subprocess.TimeoutExpired:
            ok = False
        merged = {**clip, 'files': dict(clip.get('files') or {})}
        if ok:
            merged['files']['proxy'] = proxy_path
        if progress_callback:
            progress_callback(clip_num, clip, 0, 'done')
        out.append(merged)
    return out


def process_clip_full(video_path, clip, output_dir, formats=None,
                      overlay_text=None, normalize_audio=False):
    """Encode a SINGLE clip at full quality (vertical + landscape). The
    Bucket-D2 large-file pipeline calls this lazily — when the user opens a
    cue in the editor or hits Export. Returns the same dict shape as
    `_process_single_clip` so the caller can merge it back into results[].
    """
    os.makedirs(output_dir, exist_ok=True)
    if formats is None:
        formats = ['landscape', 'vertical']
    video_info = get_video_info(video_path)
    encoder, quality_args = detect_hw_encoder()
    args = (video_path, clip, output_dir, video_info, formats,
            overlay_text, normalize_audio, encoder, quality_args)
    return _process_single_clip(args)


def process_clips(video_path, clips, output_dir, formats=None, overlay_text=None,
                  normalize_audio=False, parallel=True, progress_callback=None):
    """
    Process all detected clips — cut landscape + vertical + thumbnails.
    Uses parallel processing with capped workers for GPU encoding.

    Args:
        video_path: Source video file
        clips: List of clip dicts from analyzer
        output_dir: Where to save output clips
        formats: List of formats to export ('landscape', 'vertical', or both)
        overlay_text: Optional text overlay dict
        normalize_audio: If True, normalize audio
        parallel: If True, process clips in parallel
        progress_callback: Optional callable(clip_index, clip_info, worker_id, event)

    Returns:
        List of processed clip info dicts (includes thumbnail field)
    """
    if formats is None:
        formats = ['landscape', 'vertical']

    # SESSIE 18 — zero-clips guard. Previously `process_clips` called
    # `ProcessPoolExecutor(max_workers=min(..., len(clips)))` which evaluates
    # to 0 if the analyser found no drops, then raises
    # `ValueError: max_workers must be greater than 0`. That crash propagated
    # up through `_process_job`, leaving the job in an inconsistent state
    # and bubbling up to the watch-folder daemon as a cryptic "did not
    # finish cleanly". Returning early is the cheap fix; the caller is
    # responsible for reporting "no drops detected" to the user.
    if not clips:
        return []

    os.makedirs(output_dir, exist_ok=True)
    video_info = get_video_info(video_path)

    # Detect encoder ONCE in the main process before spawning workers.
    # On macOS spawn, child processes don't inherit globals — passing
    # encoder as an argument ensures every worker uses GPU encoding.
    encoder, quality_args = detect_hw_encoder()

    if not parallel or len(clips) == 1:
        results = []
        for i, clip in enumerate(clips):
            print(f"  Cutting clip {clip['index']}/{len(clips)}: {clip['type']} at {_format_time(clip['start'])} - {_format_time(clip['end'])}")
            if progress_callback:
                progress_callback(clip['index'], clip, 0, 'start')
            args = (video_path, clip, output_dir, video_info, formats,
                    overlay_text, normalize_audio, encoder, quality_args)
            result = _process_single_clip(args)
            results.append(result)
            if progress_callback:
                progress_callback(clip['index'], clip, 0, 'done')
        return results

    # Parallel processing — cap at MAX_PARALLEL_WORKERS
    max_workers = min(MAX_PARALLEL_WORKERS, os.cpu_count() or 4, len(clips))
    worker_args = [
        (video_path, clip, output_dir, video_info, formats,
         overlay_text, normalize_audio, encoder, quality_args)
        for clip in clips
    ]

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_meta = {}
        for worker_slot, args in enumerate(worker_args):
            clip_info = args[1]
            worker_id = worker_slot % max_workers
            future = executor.submit(_process_single_clip, args)
            future_meta[future] = (clip_info['index'], clip_info, worker_id)

        # Use as_completed for real-time progress — results arrive out of order.
        # Emit 'start' lazily right before we wait on each future so the UI
        # reflects actual execution, not submission order. Collect per-clip
        # errors rather than raising — one bad clip shouldn't kill the batch.
        for future in as_completed(future_meta):
            clip_idx, clip_info, worker_id = future_meta[future]
            if progress_callback:
                progress_callback(clip_idx, clip_info, worker_id, 'start')
            try:
                result = future.result()
                results.append(result)
                print(f"  Cut clip {result['index']}/{len(clips)}: {result['type']} at {_format_time(result['start'])} - {_format_time(result['end'])}")
                if progress_callback:
                    progress_callback(clip_idx, clip_info, worker_id, 'done')
            except Exception as e:
                print(f"  Error processing clip {clip_idx}: {e}")
                # Record the failure but continue with remaining clips.
                failed = {**clip_info, 'files': {}, 'thumbnail': None, 'error': str(e)}
                results.append(failed)
                if progress_callback:
                    progress_callback(clip_idx, clip_info, worker_id, 'done')

    results.sort(key=lambda x: x['index'])
    return results


# ---------------------------------------------------------------------------
# Single-format cutters (used by recut_clip)
# ---------------------------------------------------------------------------

def cut_clip_landscape(video_path, start, end, output_path, fade_duration=0.0,
                       overlay_text=None, normalize_audio=False,
                       text_layers=None, brand_logo=None, brand_fonts=None,
                       job_dir=None, target_w=None, target_h=None,
                       bpm_cfg=None, clip_data=None, watermark=None):
    """Cut a clip in landscape format. Uses GPU encoding + fast seek.
    Hard cut by default — pass fade_duration>0 to opt in to fades.

    SESSIE 21 — pass text_layers (per-clip overlays), brand_logo and
    brand_fonts to bake the Brand Stack into the cut at render time."""
    duration = end - start
    encoder, quality_args = detect_hw_encoder()
    # Default w/h from the source so drawtext size_pct lands consistently.
    if target_w is None or target_h is None:
        info = get_video_info(video_path)
        target_w = target_w or info.get('width') or 1920
        target_h = target_h or info.get('height') or 1080
    cmd = _build_landscape_cmd(
        video_path, start, duration, output_path,
        encoder, quality_args, fade_duration, overlay_text, normalize_audio,
        text_layers=text_layers, brand_logo=brand_logo,
        brand_fonts=brand_fonts,
        job_dir=job_dir or os.path.dirname(os.path.abspath(output_path)),
        target_w=target_w, target_h=target_h,
        bpm_cfg=bpm_cfg, clip_data=clip_data,
        watermark=watermark,
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Landscape cut failed: {result.stderr}")
    return output_path


def cut_clip_vertical(video_path, start, end, output_path, video_info=None,
                      fade_duration=0.0, overlay_text=None, normalize_audio=False,
                      text_layers=None, brand_logo=None, brand_fonts=None,
                      job_dir=None,
                      bpm_cfg=None, clip_data=None,
                      track_keyframes=None, track_crop_mode='pan',
                      watermark=None):
    """Cut a clip cropped to 9:16 vertical format. Uses GPU encoding + fast seek.
    Hard cut by default - pass fade_duration>0 to opt in to fades.

    SESSIE 21 - see cut_clip_landscape for the new Brand Stack params.
    SESSIE 30c - track_crop_mode='pan'|'zoom' picks the tracking style."""
    duration = end - start
    encoder, quality_args = detect_hw_encoder()
    if video_info is None:
        video_info = get_video_info(video_path)
    cmd = _build_vertical_cmd(
        video_path, start, duration, output_path,
        video_info, encoder, quality_args, fade_duration, overlay_text, normalize_audio,
        text_layers=text_layers, brand_logo=brand_logo,
        brand_fonts=brand_fonts,
        job_dir=job_dir or os.path.dirname(os.path.abspath(output_path)),
        bpm_cfg=bpm_cfg, clip_data=clip_data,
        track_keyframes=track_keyframes, track_crop_mode=track_crop_mode,
        watermark=watermark,
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Vertical cut failed: {result.stderr}")
    return output_path


# ---------------------------------------------------------------------------
# Thumbnail generation (standalone — used by recut and fallback)
# ---------------------------------------------------------------------------

def generate_thumbnail(video_path, timestamp, output_path, width=480):
    """Extract a single frame from video as a JPEG thumbnail. Uses fast seek."""
    cmd = _build_thumbnail_cmd(video_path, timestamp, output_path, width)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Thumbnail generation timed out after 60s (clip at {timestamp:.1f}s)")
    if result.returncode != 0:
        raise RuntimeError(f"Thumbnail generation failed: {result.stderr[:300]}")
    return output_path


# ---------------------------------------------------------------------------
# Beat snapping and CSV export
# ---------------------------------------------------------------------------

def snap_to_beat(start, end, bpm, offset=0):
    """Adjust start/end timestamps to the nearest beat boundary."""
    beat_duration = 60.0 / bpm
    adjusted_start = start - offset
    snapped_start = round(adjusted_start / beat_duration) * beat_duration + offset
    adjusted_end = end - offset
    snapped_end = round(adjusted_end / beat_duration) * beat_duration + offset
    return (snapped_start, snapped_end)


def export_clips_csv(clips, output_path):
    """Export clip metadata to CSV file."""
    fieldnames = ['index', 'type', 'start', 'end', 'duration', 'score', 'rank', 'bpm', 'landscape_file', 'vertical_file']
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for clip in clips:
            row = {
                'index': clip.get('index', ''),
                'type': clip.get('type', ''),
                'start': clip.get('start', ''),
                'end': clip.get('end', ''),
                'duration': round(clip.get('end', 0) - clip.get('start', 0), 3),
                'score': clip.get('score', ''),
                'rank': clip.get('rank', ''),
                'bpm': clip.get('bpm', ''),
                'landscape_file': clip.get('files', {}).get('landscape', ''),
                'vertical_file': clip.get('files', {}).get('vertical', ''),
            }
            writer.writerow(row)
    print(f"  CSV export written to {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Re-cut (UI editing)
# ---------------------------------------------------------------------------

def recut_clip(video_path, start, end, output_dir, clip_index, clip_type, formats=None,
               overlay_text=None, normalize_audio=False):
    """Re-cut a single clip with adjusted timestamps.

    SESSIE 21 — loads the Brand Stack (fonts + logo) and the per-clip
    text_overlays.json so every re-cut burns in the latest text + logo.
    output_dir is assumed to be `output/<job_id>/`, which is how app.py
    organises its per-job storage."""
    if formats is None:
        formats = ['landscape', 'vertical']

    os.makedirs(output_dir, exist_ok=True)
    video_info = get_video_info(video_path)
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # SESSIE 21 — Brand Stack assets for this job + clip.
    job_id = os.path.basename(os.path.normpath(output_dir))
    brand_fonts, brand_logo, overlays_map, bpm_cfg, brand_watermark = _load_brand_assets_for_job(
        job_id, output_dir
    )
    # SESSIE 22 — set-level BPM/key for the corner stamp. recut_clip has
    # no analyzer clip dict in scope; the set-level fallback in
    # _build_clip_data_for_stamp keeps the stamp text correct.
    set_bpm_info = _load_set_bpm_info_for_job(job_id, output_dir)
    text_layers = _layers_for_clip_index(overlays_map, clip_index)
    clip_data_for_stamp = _build_clip_data_for_stamp({}, set_bpm_info)
    # SESSIE 22 TR1 / SESSIE 30c / SESSIE 31 - load tracking keyframes +
    # crop mode for the vertical re-cut. SESSIE 31 added 'letterbox' as
    # a no-crop fit-to-frame option.
    track_kfs = None
    track_mode = 'pan'
    try:
        track_info = _load_keyframes_for_clip(job_id, output_dir, clip_index)
        if track_info:
            # Letterbox doesn't require keyframes; still honor the mode.
            saved_mode = track_info.get('crop_mode') or 'pan'
            if saved_mode in ('pan', 'zoom', 'letterbox'):
                track_mode = saved_mode
            else:
                track_mode = 'pan'
            if track_info.get('keyframes'):
                track_kfs = track_info['keyframes']
    except Exception:
        track_kfs = None

    files = {}

    if 'landscape' in formats:
        landscape_path = os.path.join(
            output_dir, f"{base_name}_clip{clip_index:02d}_{clip_type}_landscape.mp4"
        )
        cut_clip_landscape(
            video_path, start, end, landscape_path,
            overlay_text=overlay_text, normalize_audio=normalize_audio,
            text_layers=text_layers, brand_logo=brand_logo,
            brand_fonts=brand_fonts, job_dir=output_dir,
            target_w=video_info.get('width') or 1920,
            target_h=video_info.get('height') or 1080,
            bpm_cfg=bpm_cfg, clip_data=clip_data_for_stamp,
            watermark=brand_watermark,
        )
        files['landscape'] = landscape_path

    if 'vertical' in formats:
        vertical_path = os.path.join(
            output_dir, f"{base_name}_clip{clip_index:02d}_{clip_type}_vertical.mp4"
        )
        cut_clip_vertical(
            video_path, start, end, vertical_path, video_info,
            overlay_text=overlay_text, normalize_audio=normalize_audio,
            text_layers=text_layers, brand_logo=brand_logo,
            brand_fonts=brand_fonts, job_dir=output_dir,
            bpm_cfg=bpm_cfg, clip_data=clip_data_for_stamp,
            track_keyframes=track_kfs, track_crop_mode=track_mode,
            watermark=brand_watermark,
        )
        files['vertical'] = vertical_path

    return files


def slice_clip(video_path, start, end, output_dir, clip_index, clip_type,
               formats=None, normalize_audio=False):
    """SESSIE 43a — Lichtgewicht "alleen-snijden" variant van recut_clip.

    Doet ENKEL ffmpeg trim op de gegeven in/out-tijden, zonder text-overlays,
    brand-logo, watermark of pan/track-keyframes te bakken. Bedoeld voor de
    Trim-knop in de editor zodat de Trim-actie snel is en niet alvast iets
    'platbakt' wat de gebruiker later in de export-modal nog wil aan/uit
    kunnen zetten.

    Voor het inbakken van layers in de uiteindelijke export — zie de pre-bake
    in app._run_export_job die `recut_clip` aanroept met dezelfde signature.
    """
    if formats is None:
        formats = ['landscape', 'vertical']

    os.makedirs(output_dir, exist_ok=True)
    video_info = get_video_info(video_path)
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # Pan/keyframes uitlezen ZOALS recut_clip — een vertical slice die de
    # source 16:9 → 9:16 mapt heeft nog steeds een crop-strategie nodig,
    # anders wijkt het preview-frame af van wat de editor toont. We bakken
    # geen drawtext/logo/watermark in, alleen de geometrische crop.
    job_id = os.path.basename(os.path.normpath(output_dir))
    track_kfs = None
    track_mode = 'pan'
    try:
        track_info = _load_keyframes_for_clip(job_id, output_dir, clip_index)
        if track_info:
            saved_mode = track_info.get('crop_mode') or 'pan'
            if saved_mode in ('pan', 'zoom', 'letterbox'):
                track_mode = saved_mode
            if track_info.get('keyframes'):
                track_kfs = track_info['keyframes']
    except Exception:
        track_kfs = None

    files = {}

    if 'landscape' in formats:
        landscape_path = os.path.join(
            output_dir, f"{base_name}_clip{clip_index:02d}_{clip_type}_landscape.mp4"
        )
        # Geen overlays meegeven → cut_clip_landscape rendert zuiver de
        # trim. Brand-kit blijft op disk; pre-bake in export-pipeline pakt
        # 'm later op als de user de Caption/Watermark-toggles aan heeft.
        cut_clip_landscape(
            video_path, start, end, landscape_path,
            overlay_text=None, normalize_audio=normalize_audio,
            text_layers=None, brand_logo=None,
            brand_fonts=None, job_dir=output_dir,
            target_w=video_info.get('width') or 1920,
            target_h=video_info.get('height') or 1080,
            bpm_cfg=None, clip_data=None,
            watermark=None,
        )
        files['landscape'] = landscape_path

    if 'vertical' in formats:
        vertical_path = os.path.join(
            output_dir, f"{base_name}_clip{clip_index:02d}_{clip_type}_vertical.mp4"
        )
        cut_clip_vertical(
            video_path, start, end, vertical_path, video_info,
            overlay_text=None, normalize_audio=normalize_audio,
            text_layers=None, brand_logo=None,
            brand_fonts=None, job_dir=output_dir,
            bpm_cfg=None, clip_data=None,
            track_keyframes=track_kfs, track_crop_mode=track_mode,
            watermark=None,
        )
        files['vertical'] = vertical_path

    return files


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def export_with_preset(source_clip, preset, output_path):
    """
    Apply an export preset to an already-cut clip file.

    Presets:
        'source'           — copy as-is (stream copy, no re-encode)
        'tiktok'           — ensure 1080×1920 9:16
        'instagram_reel'   — same as tiktok
        'youtube_shorts'   — same as tiktok
        'facebook_post'    — 1080×1080 centre square crop
    """
    encoder, quality_args = detect_hw_encoder()

    if preset == 'source' or preset is None:
        shutil.copy2(source_clip, output_path)
        return output_path

    info = get_video_info(source_clip)
    src_w, src_h = info['width'], info['height']

    if preset in ('tiktok', 'instagram_reel', 'youtube_shorts'):
        if src_w == 1080 and src_h == 1920:
            shutil.copy2(source_clip, output_path)
            return output_path
        target_ratio = 9 / 16
        if (src_w / src_h) > target_ratio:
            crop_h = src_h
            crop_w = int(src_h * target_ratio)
        else:
            crop_w = src_w
            crop_h = int(src_w / target_ratio)
        crop_w -= crop_w % 2
        crop_h -= crop_h % 2
        crop_x = (src_w - crop_w) // 2
        crop_y = (src_h - crop_h) // 2
        vf = (f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
              f"scale=1080:1920:force_original_aspect_ratio=decrease,"
              f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2")

    elif preset == 'facebook_post':
        # 1080×1080 centre square crop
        vf = ("crop=min(iw\\,ih):min(iw\\,ih):(iw-min(iw\\,ih))/2:(ih-min(iw\\,ih))/2,"
              "scale=1080:1080")

    else:
        raise ValueError(f"Unknown preset: {preset}")

    cmd = [
        'ffmpeg', '-y',
        '-i', source_clip,
        '-vf', vf,
        '-af', 'aresample=44100',
        '-c:v', encoder, *quality_args,
        '-c:a', 'aac', '-b:a', '320k',
        '-movflags', '+faststart',
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"Export preset failed: {result.stderr[:400]}")
    return output_path


def extract_clip_filmstrip(clip_path, output_dir, clip_index, num_frames=40):
    """
    Extract evenly-spaced thumbnail frames from an already-cut clip for the
    editor timeline filmstrip.  Frames are stored as cf_{idx}_{frame}.jpg
    inside output_dir (typically the job's filmstrip/ directory).
    Returns list of {'time': float, 'filename': str}.
    """
    info = get_video_info(clip_path)
    duration = info['duration']
    if duration <= 0 or num_frames <= 0:
        return []

    os.makedirs(output_dir, exist_ok=True)
    interval = duration / num_frames
    frames = []

    for i in range(num_frames):
        t = i * interval
        fname = f"cf_{clip_index:02d}_{i:04d}.jpg"
        fpath = os.path.join(output_dir, fname)
        if not os.path.exists(fpath):
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(t),
                '-i', clip_path,
                '-frames:v', '1',
                '-vf', 'scale=-1:72',
                '-q:v', '5',
                fpath
            ]
            try:
                subprocess.run(cmd, capture_output=True, timeout=15)
            except Exception:
                continue
        if os.path.exists(fpath):
            frames.append({'time': round(t, 3), 'filename': fname})

    return frames


def split_clip_at(source_clip, split_at, output_dir, clip_index, clip_type):
    """
    Split an existing clip file at split_at seconds into two parts.
    Returns (path_part_a, path_part_b).
    """
    base = os.path.splitext(os.path.basename(source_clip))[0]
    path_a = os.path.join(output_dir, f"{base}_splitA.mp4")
    path_b = os.path.join(output_dir, f"{base}_splitB.mp4")

    encoder, quality_args = detect_hw_encoder()

    for path, extra_args in [
        (path_a, ['-t', str(split_at)]),
        (path_b, ['-ss', str(split_at)]),
    ]:
        cmd = [
            'ffmpeg', '-y',
            '-i', source_clip,
            *extra_args,
            '-c:v', encoder, *quality_args,
            '-c:a', 'aac', '-b:a', '320k',
            '-movflags', '+faststart',
            path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"Split failed ({path}): {result.stderr[:300]}")

    return path_a, path_b


def _format_time(seconds):
    """Format seconds as MM:SS or HH:MM:SS."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


# ---------------------------------------------------------------------------
# Real export pipeline (added in Blok 3)
# ---------------------------------------------------------------------------
# Re-encodes an already-cut clip to user-chosen codec/fps/resolution.
# Used by /api/export/<job_id> to produce delivery-ready files.

# Codec map: UI value -> (ffmpeg encoder, extra args, output extension)
EXPORT_CODEC_MAP = {
    # 'match' = stream copy: no re-encode at all, just remux. Fastest, lossless.
    'match':   (None,                  [],                                                          '.mp4'),
    'h265_vt': ('hevc_videotoolbox',   ['-q:v', '55', '-tag:v', 'hvc1'],                            '.mp4'),
    'h264_vt': ('h264_videotoolbox',   ['-q:v', '55', '-profile:v', 'high'],                        '.mp4'),
    'prores':  ('prores_ks',           ['-profile:v', '3', '-vendor', 'apl0', '-pix_fmt', 'yuv422p10le'], '.mov'),
}


def export_clip_with_settings(source_clip, output_dir, clip_index,
                              codec='match', fps='match', resolution='source'):
    """
    Re-encode a previously cut clip to the user's chosen codec/fps/resolution.

    Args:
        source_clip: absolute path to existing landscape or vertical clip
        output_dir:  job's output directory (we write into output_dir/exports/)
        clip_index:  numeric index, used in output filename
        codec:       'match' | 'h265_vt' | 'h264_vt' | 'prores'
        fps:         'match' | '24' | '30' | '60'
        resolution:  '1080x1920' | '2160x3840' | 'source'

    Returns dict: { 'ok': bool, 'path': str, 'size_bytes': int, 'duration_s': float, 'error': str|None }
    """
    if not source_clip or not os.path.exists(source_clip):
        return {'ok': False, 'path': None, 'size_bytes': 0, 'duration_s': 0,
                'error': f'source clip missing: {source_clip}'}

    if codec not in EXPORT_CODEC_MAP:
        return {'ok': False, 'path': None, 'size_bytes': 0, 'duration_s': 0,
                'error': f'unknown codec: {codec}'}

    encoder, extra_args, ext = EXPORT_CODEC_MAP[codec]

    # Build output path
    exports_dir = os.path.join(output_dir, 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    src_stem = os.path.splitext(os.path.basename(source_clip))[0]
    out_name = f"export_{clip_index:02d}_{src_stem}_{codec}{ext}"
    out_path = os.path.join(exports_dir, out_name)

    # Build ffmpeg command
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning', '-i', source_clip]

    if encoder is None:
        # Stream copy: no re-encode. Note: -r and -s have no effect with -c copy,
        # so for 'match' codec we always copy as-is regardless of fps/resolution
        # choice. This is the correct behaviour for "Match source" — fps and
        # resolution choice only kick in once user picks a non-match codec.
        cmd += ['-c', 'copy', '-movflags', '+faststart']
    else:
        cmd += ['-c:v', encoder, *extra_args]

        # Frame rate: only set if user picked a specific value
        if fps != 'match':
            try:
                cmd += ['-r', str(int(fps))]
            except (TypeError, ValueError):
                pass  # silently ignore invalid fps

        # Resolution: only set if user picked a specific value
        if resolution and resolution != 'source':
            # Format is 'WIDTHxHEIGHT', e.g. '1080x1920'. Use a scale filter
            # that preserves aspect inside the box (no distortion).
            try:
                w_str, h_str = resolution.lower().split('x')
                w, h = int(w_str), int(h_str)
                cmd += ['-vf', f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black']
            except (ValueError, AttributeError):
                pass  # bad resolution string -> use source size

        # Audio: re-encode to AAC for compatibility, except ProRes which
        # traditionally pairs with PCM in .mov.
        if codec == 'prores':
            cmd += ['-c:a', 'pcm_s16le']
        else:
            cmd += ['-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart']

    cmd.append(out_path)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if result.returncode != 0:
            return {'ok': False, 'path': None, 'size_bytes': 0, 'duration_s': 0,
                    'error': f'ffmpeg failed (code {result.returncode}): {result.stderr[-400:]}'}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'path': None, 'size_bytes': 0, 'duration_s': 0,
                'error': 'ffmpeg timed out after 900s'}
    except Exception as e:
        return {'ok': False, 'path': None, 'size_bytes': 0, 'duration_s': 0,
                'error': f'ffmpeg exception: {e}'}

    # Probe output for verification
    size_bytes = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    duration_s = 0.0
    try:
        probe = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', out_path],
            capture_output=True, text=True, timeout=10
        )
        duration_s = float(probe.stdout.strip() or 0)
    except Exception:
        pass

    return {
        'ok': True,
        'path': out_path,
        'size_bytes': size_bytes,
        'duration_s': duration_s,
        'error': None,
    }
