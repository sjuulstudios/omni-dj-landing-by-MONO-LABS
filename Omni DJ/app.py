"""
Flask web server for DJ Clip Cutter.
Handles file upload, analysis, cutting, and serving clips.

Enhanced with:
- Multi-view SPA frontend (Home → Parameters → Processing → Dashboard → Editor)
- Full 20 Hz–20 kHz audio spectrum in all output clips (44.1 kHz AAC 320k)
- Chunked audio analysis for 3–4 hour / 7–10 GB DJ sets
- SSE (Server-Sent Events) progress stream for real-time updates
- Lazy filmstrip: frames generated on-demand, not all upfront
- Disk space pre-check (scales with upload size) before processing starts
- ffprobe file validation at upload time
- Input sanitisation and secure filename handling
- Job history persisted to disk
- Thread-safe job-state access via jobs_lock
- Uploaded source videos cleaned up after processing + on new upload
- Binds to 127.0.0.1 by default (no LAN exposure without an auth layer)
"""

import os
import sys
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, send_file, Response, stream_with_context, g

from analyzer import analyze_dj_set, get_waveform_data, detect_bpm, create_manual_clip
from cutter import (
    extract_audio, get_video_info, process_clips, recut_clip,
    generate_thumbnail, export_clips_csv, snap_to_beat,
    export_with_preset, extract_clip_filmstrip, split_clip_at,
    process_proxy_clips, process_clip_full, build_keyframe_index,
    get_per_clip_waveform, export_clip_with_settings,
    _ffmpeg_has_drawtext,
    # SESSIE 43a — slice_clip = trim zonder layers; gebruikt door /api/slice
    slice_clip,
    # SESSIE 78 - D5: crowd-inmix stream-count guard (alleen actief bij synced 2-track bron).
    _count_audio_streams,
)
from uploader import get_platform_status, upload_to_youtube, upload_to_tiktok, upload_to_instagram, upload_to_facebook
# SESSIE 66 — centrale resolver voor de gebundelde ffmpeg/ffprobe binaries.
# Voorkomt "ffprobe failed" in de gesignde .app (kale naam → PATH-afhankelijk).
import media_tools

from auth import (
    health_check as auth_health_check,
    signup as auth_signup,
    login as auth_login,
    get_user_from_token as auth_get_user_from_token,
    refresh_session as auth_refresh_session,
    forgot_password as auth_forgot_password,
    reset_password as auth_reset_password,
    log_action as auth_log_action,
    require_role,
    supabase_admin,
)

from billing import (
    health_check as billing_health_check,
    start_checkout as billing_start_checkout,
    open_portal as billing_open_portal,
    STRIPE_PUBLISHABLE_KEY,
)

from analyzer import analyze_with_demucs

# Watch-folder daemon (Pro-tier feature). Imported as a module so its
# polling thread can be started after all helpers/jobs/locks are defined.
# See watch_folder.py for the architecture overview.
import watch_folder

try:
    import torch
    import demucs
    HAS_DEMUCS = True
except ImportError:
    HAS_DEMUCS = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('clip-live')

app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024 * 1024  # 20 GB

# ---------------------------------------------------------------------------
# SESSIE 32 - Rate limiting (flask-limiter).
# ---------------------------------------------------------------------------
# Defensieve laag bovenop Supabase's eigen auth-rate-limiting en de quota
# gate. Beschermt tegen:
#   - bots die /api/auth/signup of /api/auth/login spammen
#   - misbruik van /api/billing/checkout (kosten bij abuse)
#   - bulk-upload door 1 account
#
# Backend: in-memory (geen Redis). Limieten resetten bij dev-server-restart;
# voor een lokaal-draaiende tool prima. Default per-IP; voor authed routes
# zetten we de key op het access_token-prefix zodat 1 user via IP-rotation
# niet om de limiet kan.
#
# Geen default_limits — alleen routes met @limiter.limit decorator worden
# beperkt. 429 response wordt als JSON gerendered zodat de frontend hem
# nicely kan tonen ipv de standaard HTML page.
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    def _rate_limit_key():
        """Per-user rate limit key voor authed routes; valt terug op IP
        als er geen token is. Voorkomt dat 1 user via IP-rotation om de
        per-user limiet kan."""
        auth_header = request.headers.get('Authorization', '')
        if auth_header.lower().startswith('bearer '):
            token = auth_header[7:].strip()
            if token:
                # Eerste 32 chars van het JWT zijn ruim genoeg om uniek te
                # zijn per user, en logt het volledige token niet.
                return f'user:{token[:32]}'
        return f'ip:{get_remote_address()}'

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri='memory://',
        default_limits=[],
        headers_enabled=True,
    )

    @app.errorhandler(429)
    def _rate_limit_response(e):
        retry = getattr(e, 'retry_after', None)
        return jsonify({
            'ok': False,
            'error': 'Te veel verzoeken - probeer het over een paar minuten opnieuw.',
            'retry_after_seconds': retry,
        }), 429
    log.info('Rate limiter geinitialiseerd (in-memory)')
except ImportError:
    # flask-limiter niet geinstalleerd - dev kan doorgaan zonder rate
    # limiting. Vervang door no-op decorator zodat @limiter.limit(...) niet
    # crasht.
    log.warning('flask-limiter niet geinstalleerd - rate limiting UIT. '
                'Run: pip install "flask-limiter>=3.5"')

    class _NoLimiter:
        def limit(self, *_a, **_kw):
            def _decorator(fn):
                return fn
            return _decorator
    limiter = _NoLimiter()

    def _rate_limit_key():
        return 'noop'

# ---------------------------------------------------------------------------
# SESSIE 67 — Lokale-server hardening (S1 + S4)
# ---------------------------------------------------------------------------
# De app draait op 127.0.0.1:5555. Dat is bereikbaar vanuit de browser, dus
# een kwaadaardige website die je open hebt staan kan in theorie requests naar
# de loopback-poort sturen (CSRF), of via DNS-rebinding een eigen hostname laten
# resolven naar 127.0.0.1 en zo de same-origin-policy omzeilen.
#
# Twee verdedigingslagen:
#   S1a Host-header check  — blokkeert DNS-rebinding. Een rebinding-aanval komt
#       binnen met de hostname van de aanvaller in de Host-header; wij accepteren
#       alleen localhost/127.0.0.1. (De browser kan de Host-header niet vervalsen.)
#   S1b Origin/Sec-Fetch check op state-changing requests — blokkeert cross-site
#       POST/PUT/DELETE (CSRF). Same-origin en directe navigatie blijven werken.
#   S4  Security headers op elke response (nosniff, X-Frame-Options, CSP, etc.).
#
# Bewust GEEN CSRF-token-systeem: de echte API-acties vereisen al een Bearer
# token in de Authorization-header, en een cross-site pagina kan dat token niet
# uit onze localStorage lezen (same-origin policy). De Host+Origin-checks dekken
# de resterende vector af zonder de single-page-app te breken.

# Toegestane Host-waarden. OMNI_DJ_PORT laat een afwijkende poort toe.
_ALLOWED_PORT = os.environ.get('OMNI_DJ_PORT', '5555')
_ALLOWED_HOSTS = {
    f'127.0.0.1:{_ALLOWED_PORT}', f'localhost:{_ALLOWED_PORT}',
    '127.0.0.1', 'localhost',
}
# Als de gebruiker bewust op het LAN bindt (OMNI_DJ_BIND=0.0.0.0) zetten we de
# Host-check uit — dan weet hij wat hij doet en bepaalt zijn eigen netwerk wie
# erbij kan. Loopback (default) blijft streng.
_HOST_CHECK_ON = os.environ.get('OMNI_DJ_BIND', '127.0.0.1') in ('127.0.0.1', 'localhost')

# Methodes die state veranderen → Origin moet kloppen (of afwezig zijn bij een
# directe, niet-cross-site request).
_STATE_CHANGING = {'POST', 'PUT', 'PATCH', 'DELETE'}


@app.before_request
def _security_gate():
    """S1 — weer DNS-rebinding en cross-site state-changing requests af."""
    # S1a — Host-header allowlist (alleen bij loopback-bind).
    if _HOST_CHECK_ON:
        host = (request.host or '').lower()
        if host and host not in _ALLOWED_HOSTS:
            log.warning('Geweigerd: onverwachte Host-header %r', host)
            return jsonify({'ok': False, 'error': 'Invalid host'}), 421

    # S1b — CSRF: cross-site state-changing requests blokkeren. We leunen op
    # Sec-Fetch-Site (moderne browsers) met een Origin-fallback. 'same-origin'
    # en 'none' (directe navigatie / adresbalk) zijn oké; 'cross-site' niet.
    if request.method in _STATE_CHANGING:
        sec_site = request.headers.get('Sec-Fetch-Site')
        if sec_site is not None:
            if sec_site not in ('same-origin', 'none'):
                log.warning('Geweigerd: cross-site %s (Sec-Fetch-Site=%s)',
                            request.method, sec_site)
                return jsonify({'ok': False, 'error': 'Cross-site request geweigerd'}), 403
        else:
            # Oudere browser zonder Sec-Fetch-Site: val terug op Origin-header.
            origin = request.headers.get('Origin')
            if origin:
                allowed_origins = {f'http://{h}' for h in _ALLOWED_HOSTS} | \
                                  {f'https://{h}' for h in _ALLOWED_HOSTS}
                if origin.lower() not in allowed_origins:
                    log.warning('Geweigerd: cross-site Origin %r', origin)
                    return jsonify({'ok': False, 'error': 'Cross-site request geweigerd'}), 403
            # Geen Origin én geen Sec-Fetch-Site: same-origin form-post of een
            # niet-browser-client (curl). Doorlaten — de Bearer-token-gate op de
            # API-routes is dan de feitelijke bescherming.
    return None


# S4 — Content Security Policy. 'self' + de externe origins die de SPA echt
# gebruikt (Google Fonts). Inline script/style zijn nodig omdat de hele app
# één groot inline-bestand is; 'unsafe-inline' is hier acceptabel want alle
# content is door ons gegenereerd en wordt lokaal geserveerd (geen user-HTML).
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: blob:; "
    "media-src 'self' blob: data:; "
    "connect-src 'self' https://lbabsffxefkrxwzkbzar.supabase.co; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self' https://checkout.stripe.com https://billing.stripe.com"
)


@app.after_request
def _security_headers(resp):
    """S4 — defensieve HTTP-headers op elke response."""
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resp.headers.setdefault('X-Frame-Options', 'DENY')
    resp.headers.setdefault('Referrer-Policy', 'no-referrer')
    resp.headers.setdefault('Content-Security-Policy', _CSP)
    resp.headers.setdefault(
        'Permissions-Policy',
        'geolocation=(), camera=(), microphone=(), payment=()',
    )
    resp.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
    # HSTS: alleen zinvol/geldig over HTTPS. De lokale app draait over http op
    # loopback, dus we zetten 'm alleen als de request echt over TLS binnenkwam
    # (bv. achter een reverse proxy op omnidj.com). Op http://127.0.0.1 negeren
    # browsers HSTS toch, maar we sturen 'm dan ook niet mee.
    if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https':
        resp.headers.setdefault(
            'Strict-Transport-Security',
            'max-age=31536000; includeSubDomains',
        )
    return resp


def _path_within_home(path):
    """SESSIE 67 (S2) — True als `path` binnen de home-map van de gebruiker valt.
    realpath'd zodat symlinks geen uitweg buiten home bieden. Gebruikt door de
    input-pad-validatie van /api/upload-local (zelfde regel als de export-map)."""
    try:
        real_target = os.path.realpath(os.path.expanduser(path))
        real_home = os.path.realpath(os.path.expanduser('~'))
        return real_target == real_home or real_target.startswith(real_home + os.sep)
    except OSError:
        return False

# ---------------------------------------------------------------------------
# Bucket-D2 large-file pipeline flag (2026-04-26)
# ---------------------------------------------------------------------------
# When ON:
#   • /api/upload-local registers an existing path on disk WITHOUT copying.
#   • Long sets (> LARGE_DURATION_THRESHOLD seconds) skip the eager
#     full-quality cut step. The analyser runs as usual; clips are produced
#     as 720p PROXIES first so the editor is interactive in minutes. The
#     full 1080p landscape + vertical cuts are encoded lazily — when the
#     user opens or exports a clip — via /api/render-clip.
#   • A keyframe index is built once at upload time so each clip's `-ss`
#     lands on a real keyframe (essentially free seek even on 10-hour files).
#
# Default OFF — flip via the env var below or via /api/settings → large_file.
LARGE_FILE_PIPELINE       = os.environ.get('LARGE_FILE_PIPELINE', '1') in ('1', 'true', 'yes')
LARGE_DURATION_THRESHOLD  = int(os.environ.get('LARGE_DURATION_THRESHOLD', '7200'))   # 2 h
PROXY_BITS_PER_SEC        = 1.0 * 1024 * 1024  # ~1 MB/s — used by disk-estimate
FULL_BITS_PER_SEC         = 5.0 * 1024 * 1024  # ~5 MB/s — landscape+vertical combined

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR      = os.path.dirname(__file__)
# SESSIE 40 (2026-05-26) — In een gebundelde .app is BASE_DIR Contents/Frameworks
# en daar mag een unsigned app NIET schrijven (macOS PermissionError errno 1 op
# os.makedirs). launcher.py zet OMNI_DJ_USER_DATA naar een schrijfbare locatie
# (~/Library/Application Support/Omni DJ/ op macOS, %APPDATA%\Omni DJ\ op
# Windows). In dev-server is die env-var NIET gezet → DATA_DIR valt terug op
# BASE_DIR en alles blijft werken zoals voorheen. Backwards-compatibel.
DATA_DIR      = os.environ.get("OMNI_DJ_USER_DATA", BASE_DIR)
# 2026-05-10 — moved out of tempfile.gettempdir() (which is /var/folders/.../T
# on macOS and gets aggressively cleaned by the OS, including across reboots).
# Living in /tmp wiped the source video for any job whose UPLOAD_DIR file was
# evicted, which then broke every recut/stretch with "Source video file not
# found on disk". Persistent paths under DATA_DIR solve that, at the cost
# of disk space (managed manually for now). Snapshots in OUTPUT_DIR/<job>/job.json
# now likewise survive reboots, so /api/history reflects real state.
UPLOAD_DIR    = os.path.join(DATA_DIR, 'uploads')
OUTPUT_DIR    = os.path.join(DATA_DIR, 'output')
SETTINGS_PATH     = os.path.join(DATA_DIR, 'user_settings.json')
HISTORY_PATH      = os.path.join(DATA_DIR, 'job_history.json')
WATCH_FOLDER_PATH = os.path.join(DATA_DIR, 'watch_folder.json')
BRAND_KIT_PATH    = os.path.join(DATA_DIR, 'brand_kit.json')
# SESSIE 21 — Brand Stack: per-asset folders under DATA_DIR/brand_kit/.
# Fonts live alongside the JSON kit, plus a per-job text_overlays.json under
# output/<job>/ for editor text layers (added in F3).
BRAND_KIT_DIR     = os.path.join(DATA_DIR, 'brand_kit')
BRAND_FONTS_DIR   = os.path.join(BRAND_KIT_DIR, 'fonts')
BRAND_LOGO_DIR    = os.path.join(BRAND_KIT_DIR, 'logo')
# SESSIE 31 — separate folder for the user's watermark image. A watermark
# is conceptually different from a logo: typically larger, semi-transparent,
# tiled or repeated. Keeping them apart avoids overwriting either.
BRAND_WATERMARK_DIR = os.path.join(BRAND_KIT_DIR, 'watermark')

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BRAND_FONTS_DIR, exist_ok=True)
os.makedirs(BRAND_LOGO_DIR, exist_ok=True)
os.makedirs(BRAND_WATERMARK_DIR, exist_ok=True)

# SESSIE 21 — fonttools is optional. When present we can accept WOFF2 uploads
# and convert them to TTF on the fly (ffmpeg's drawtext only reads TTF/OTF).
# When absent the UI rejects WOFF2 with a clear "install fonttools" error.
try:
    from fontTools.ttLib import TTFont as _FT_TTFont  # noqa: F401
    _HAS_FONTTOOLS = True
except Exception:
    _HAS_FONTTOOLS = False


def _migrate_legacy_tmp_storage():
    """One-time migration from the legacy /tmp/dj-clip-cutter/* paths into
    BASE_DIR/{uploads,output}. Runs at import. If the legacy paths are
    already gone (macOS cleaned them) this is a no-op. Anything we move
    out is also patched up in the on-disk job snapshots so `video_path`
    points at the new persistent location and recut keeps working without
    a manual re-upload."""
    legacy_root = os.path.join(tempfile.gettempdir(), 'dj-clip-cutter')
    if not os.path.isdir(legacy_root):
        return
    moved = 0
    for sub, dest in (('uploads', UPLOAD_DIR), ('output', OUTPUT_DIR)):
        src_dir = os.path.join(legacy_root, sub)
        if not os.path.isdir(src_dir):
            continue
        os.makedirs(dest, exist_ok=True)
        try:
            entries = os.listdir(src_dir)
        except OSError as e:
            log.warning("legacy migration: cannot list %s: %s", src_dir, e)
            continue
        for name in entries:
            src_path  = os.path.join(src_dir, name)
            dest_path = os.path.join(dest, name)
            if os.path.exists(dest_path):
                continue  # never overwrite something already in the new location
            try:
                shutil.move(src_path, dest_path)
                moved += 1
            except OSError as e:
                log.warning("legacy migration: %s -> %s failed: %s",
                            src_path, dest_path, e)
    # Rewrite snapshot video_path entries so they point at the new
    # persistent UPLOAD_DIR. Without this, every existing job would still
    # hold a stale "/private/var/folders/.../T/dj-clip-cutter/uploads/<id>"
    # path and recut would 404 with "Source video file not found".
    if os.path.isdir(OUTPUT_DIR):
        try:
            for jid in os.listdir(OUTPUT_DIR):
                snap_path = os.path.join(OUTPUT_DIR, jid, 'job.json')
                if not os.path.isfile(snap_path):
                    continue
                try:
                    with open(snap_path) as f:
                        snap_obj = json.load(f)
                    vp = snap_obj.get('video_path')
                    if vp and not os.path.exists(vp):
                        bn = os.path.basename(str(vp))
                        new_vp = os.path.join(UPLOAD_DIR, bn)
                        if os.path.exists(new_vp):
                            snap_obj['video_path'] = new_vp
                            with open(snap_path, 'w') as f:
                                json.dump(snap_obj, f, default=str, indent=2)
                except (OSError, ValueError) as e:
                    log.warning("legacy migration: snapshot rewrite %s failed: %s",
                                snap_path, e)
        except OSError as e:
            log.warning("legacy migration: scan OUTPUT_DIR failed: %s", e)
    if moved:
        log.info("Storage migration: moved %d items from /tmp/dj-clip-cutter -> %s",
                 moved, BASE_DIR)


_migrate_legacy_tmp_storage()

# Job IDs are 8-char UUID slices; validate on every file-serving route.
JOB_ID_RE = re.compile(r'^[a-f0-9]{8}$')

# In-memory job state + lock for thread-safe access
jobs = {}
jobs_lock = threading.RLock()  # RLock so callers inside locked sections can re-lock


# ---------------------------------------------------------------------------
# Helpers that manipulate the shared `jobs` dict — always take the lock
# ---------------------------------------------------------------------------
def _get_job(job_id):
    """Return a shallow copy of the job dict under the lock, or None."""
    with jobs_lock:
        job = jobs.get(job_id)
        return dict(job) if job else None


def _job_exists(job_id):
    with jobs_lock:
        return job_id in jobs


def _update_job(job_id, **updates):
    """Apply updates to a job under the lock. Returns True if job exists."""
    with jobs_lock:
        if job_id not in jobs:
            return False
        jobs[job_id].update(updates)
        return True


def _update_progress(job_id, **kwargs):
    """Merge kwargs into jobs[job_id]['progress'] under the lock."""
    with jobs_lock:
        if job_id not in jobs:
            return
        jobs[job_id].setdefault('progress', {}).update(kwargs)


def _inject_clip_fps(snap):
    """Phase-4 deelstap 2c: copy job-level fps into every clip dict so the
    editor frontend can read STATE.clips[idx].fps uniformly. Doesn't touch
    clips that already declare their own fps. No-op if job has no fps yet
    (older snapshots from before SESSIE 11)."""
    if not isinstance(snap, dict):
        return snap
    job_fps = snap.get('fps')
    if job_fps is None:
        return snap
    for key in ('clips', 'results'):
        items = snap.get(key)
        if not isinstance(items, list):
            continue
        for c in items:
            if isinstance(c, dict) and c.get('fps') is None:
                c['fps'] = job_fps
    return snap


def _get_snapshot(job_id):
    """Thread-safe deep copy of a job for read-only use in a handler.
    Falls back to a persisted on-disk snapshot if the job is no longer
    in the in-memory dict (e.g. after a server restart)."""
    with jobs_lock:
        job = jobs.get(job_id)
        if job:
            # json round-trip gives us a true deep copy safe to return
            try:
                snap = json.loads(json.dumps(job, default=str))
            except (TypeError, ValueError):
                # Fallback if something non-serialisable sneaks in
                snap = dict(job)
            return _inject_clip_fps(snap)
    # Not in memory — try disk
    snap = _load_job_snapshot(job_id)
    if snap:
        # Re-populate in-memory cache so subsequent reads are fast
        with jobs_lock:
            jobs[job_id] = snap
        return _inject_clip_fps(snap)
    return None


# ---------------------------------------------------------------------------
# Settings & history (file-backed; lightweight file locks via OS-level rename)
# ---------------------------------------------------------------------------
def _load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            log.warning("Could not read settings: %s", e)
    return {}


def _save_settings(settings):
    try:
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
    except OSError as e:
        log.warning("Could not save settings: %s", e)


def _load_json_blob(path, default):
    """Load a JSON file, returning `default` on missing/invalid."""
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            log.warning("Could not read %s: %s", path, e)
    return default


def _save_json_blob(path, data):
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        log.warning("Could not save %s: %s", path, e)


def _load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            log.warning("Could not read job history: %s", e)
    return []


def _save_history(history):
    try:
        with open(HISTORY_PATH, 'w') as f:
            json.dump(history[-50:], f, indent=2)  # keep last 50
    except OSError as e:
        log.warning("Could not save job history: %s", e)


def _append_to_history(job_data):
    history = _load_history()
    entry = {
        'id': job_data['id'],
        'filename': job_data.get('filename', ''),
        'clipCount': len(job_data.get('results', [])),
        'date': time.strftime('%Y-%m-%d'),
        'thumb': None,
        # SESSIE 28 — user_id stamp so /api/history can filter per signed-in
        # account. Without this, every user on the same local install saw the
        # full library across accounts (see SESSIE 28 bug report).
        'user_id': job_data.get('user_id'),
    }
    results = job_data.get('results', [])
    if results and results[0].get('thumbnail'):
        entry['thumb'] = f"/api/thumbnail/{job_data['id']}/{results[0]['thumbnail']}"
    history = [h for h in history if h['id'] != entry['id']]
    history.append(entry)
    _save_history(history)
    # Also persist the full job snapshot so we can rehydrate after a restart.
    _persist_job_snapshot(job_data)


def _persist_job_snapshot(job_data):
    """Write a JSON snapshot of a finished job into its OUTPUT_DIR so it
    survives server restarts and can be re-loaded by /api/status.

    2026-05-10 — `video_path` IS now persisted. Previously it was stripped
    because UPLOAD_DIR lived in /tmp and absolute paths didn't survive a
    reboot, but UPLOAD_DIR is now project-relative + persistent (see paths
    setup near the top of this file), so the path stays valid across
    restarts. Keeping video_path in the snapshot means recut_capable
    correctly returns true after a restart whenever the source still
    exists on disk.
    """
    job_id = job_data.get('id')
    if not job_id:
        return
    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    try:
        os.makedirs(job_output_dir, exist_ok=True)
        snap_path = os.path.join(job_output_dir, 'job.json')
        # SESSIE 22 — preserve-fields merge for `bpm`. Legacy jobs (analysed
        # before detect_musical_key was added) carry `bpm={bpm, beat_times,
        # bar_times, bar_duration}` in memory. If a power-user has patched
        # `bpm.key` into the on-disk snap manually (or a later upgrade adds
        # new keys), we don't want this write to wipe them just because the
        # in-memory dict is missing those keys. Merge: any field that the
        # in-memory state has as None or missing AND the on-disk state has
        # a non-empty value → keep the on-disk value.
        try:
            if os.path.exists(snap_path):
                with open(snap_path) as _rf:
                    on_disk = json.load(_rf) or {}
                if isinstance(on_disk.get('bpm'), dict) and isinstance(job_data.get('bpm'), dict):
                    for k, v in on_disk['bpm'].items():
                        if v not in (None, '', [], {}) and job_data['bpm'].get(k) in (None, '', [], {}):
                            job_data['bpm'][k] = v
        except (OSError, json.JSONDecodeError):
            pass
        # SESSIE 30 - never persist the user's access_token to disk.
        # It is kept on the in-memory job dict only so background quota
        # callbacks can route through the update-usage edge function.
        # Strip on a shallow copy so the live in-memory state stays intact.
        if isinstance(job_data, dict) and 'access_token' in job_data:
            sanitised = {k: v for k, v in job_data.items() if k != 'access_token'}
        else:
            sanitised = job_data
        with open(snap_path, 'w') as f:
            json.dump(sanitised, f, default=str, indent=2)
    except (OSError, TypeError, ValueError) as e:
        log.warning("Could not persist job snapshot for %s: %s", job_id, e)


def _load_job_snapshot(job_id):
    """Load a previously-persisted job snapshot from disk, or None."""
    if not _valid_job_id(job_id):
        return None
    snap_path = os.path.join(OUTPUT_DIR, job_id, 'job.json')
    if not os.path.exists(snap_path):
        return None
    try:
        with open(snap_path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        log.warning("Could not load job snapshot for %s: %s", job_id, e)
        return None


def _rehydrate_jobs_from_history():
    """At server startup, walk job_history.json and re-populate jobs[] for
    every entry that still has a job.json snapshot on disk. Prune entries
    that have neither in-memory state nor an on-disk snapshot."""
    history = _load_history()
    kept = []
    rehydrated = 0
    pruned = 0
    for entry in history:
        jid = entry.get('id')
        if not jid:
            continue
        snap = _load_job_snapshot(jid)
        if snap:
            with jobs_lock:
                jobs[jid] = snap
            rehydrated += 1
            kept.append(entry)
        else:
            # No snapshot AND not in memory — orphan entry. Drop it.
            # (Do NOT delete the OUTPUT_DIR — clips may still be there
            # for a job that simply predates the snapshot system.)
            output_dir = os.path.join(OUTPUT_DIR, jid)
            if os.path.isdir(output_dir):
                # Keep entry; we may be able to reconstruct from CSV later
                kept.append(entry)
            else:
                pruned += 1
    if pruned:
        _save_history(kept)
    if rehydrated or pruned:
        log.info("Job rehydrate: %d restored, %d orphan history entries pruned",
                 rehydrated, pruned)


# ---------------------------------------------------------------------------
# Security: safe filename
# ---------------------------------------------------------------------------
def _safe_filename(filename):
    """Strip path components and sanitise filename."""
    filename = os.path.basename(filename)
    # Allow only alphanumeric, dash, underscore, dot, space
    filename = re.sub(r'[^\w\s\-\.]', '_', filename)
    filename = filename.strip().strip('.')
    return filename[:200] or 'upload'


def _valid_job_id(job_id):
    return isinstance(job_id, str) and bool(JOB_ID_RE.match(job_id))


# ---------------------------------------------------------------------------
# Security: validate that uploaded file is actually a video
# ---------------------------------------------------------------------------
def _parse_fps_string(value):
    """
    Convert ffprobe r_frame_rate / avg_frame_rate strings (e.g. '30000/1001'
    or '30/1' or '24') to a float fps. Returns None if the value is missing,
    malformed, or implausible (out of 1..240 range).
    Used by Phase-4 deelstap 2c so the editor can display a frame counter.
    """
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            v = float(value)
        else:
            s = str(value).strip()
            if not s:
                return None
            if '/' in s:
                num, den = s.split('/', 1)
                num = float(num)
                den = float(den)
                if den == 0:
                    return None
                v = num / den
            else:
                v = float(s)
    except (TypeError, ValueError):
        return None
    if not (1.0 <= v <= 240.0):
        return None
    return round(v, 3)


def _validate_video_file(path):
    """
    Run ffprobe to confirm the file contains at least one video stream.
    Returns (True, info_dict) or (False, error_string).

    Phase-4 deelstap 2c: also parses the first video stream's r_frame_rate
    (with avg_frame_rate as fallback) into info['fps'] so the editor can
    show a frame counter without an extra ffprobe call.
    """
    cmd = [
        media_tools.ffprobe(), '-v', 'quiet', '-print_format', 'json',
        '-show_streams', '-show_format', path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return False, 'ffprobe failed — not a valid video file'
        info = json.loads(result.stdout)
        streams = info.get('streams', [])
        video_stream = next((s for s in streams if s.get('codec_type') == 'video'), None)
        if video_stream is None:
            return False, 'No video stream found in file'
        duration = float(info.get('format', {}).get('duration', 0))
        if duration <= 0:
            return False, 'Could not determine video duration'
        # Phase-4 deelstap 2c — fps detection (best-effort, never fails the
        # validation). r_frame_rate is the "real" base rate; avg_frame_rate
        # is the fallback for variable-rate sources.
        fps = _parse_fps_string(video_stream.get('r_frame_rate'))
        if fps is None:
            fps = _parse_fps_string(video_stream.get('avg_frame_rate'))
        if fps is not None:
            info['fps'] = fps
        return True, info
    except subprocess.TimeoutExpired:
        return False, 'ffprobe timed out — file may be corrupt'
    except (OSError, ValueError, json.JSONDecodeError) as e:
        return False, f'Validation error: {e}'


# ---------------------------------------------------------------------------
# Security: check available disk space
# ---------------------------------------------------------------------------
def _check_disk_space(path, required_gb):
    """
    Check that there is at least required_gb of free space at path.
    Returns (True, free_gb) or (False, free_gb).
    """
    try:
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024 ** 3)
        return free_gb >= required_gb, round(free_gb, 1)
    except OSError:
        return True, 0  # if check fails, don't block


# ---------------------------------------------------------------------------
# Cleanup helpers
# ---------------------------------------------------------------------------
def _cleanup_source_video(job_id):
    """Was: delete the uploaded source video after processing finished.

    DISABLED 2026-05-10 — Sjuul needs the source video to remain on disk
    so /api/recut (stretch + edit-in-editor flow) can keep working after
    the initial cut. Without the source, every recut returns "Source
    video file not found on disk" and the user can't extend a clip past
    its original boundaries.

    The function is kept as a no-op (rather than removing all callers)
    so future cleanup logic — e.g. a Settings → "Delete sources older
    than 30 days" UI — can hook back in here without re-introducing the
    bug for already-shipped builds. The .wav cleanup in _process_job's
    `finally` block is unaffected and still runs.
    """
    with jobs_lock:
        job = jobs.get(job_id) or {}
        video_path = job.get('video_path')
    log.info("Source-video cleanup is disabled — keeping %s for future recut/stretch.",
             video_path)


def _purge_old_uploads():
    """Was: nuke UPLOAD_DIR at server startup. Disabled 2026-05-10 because
    that wiped every source video — including ones the user still needs
    for recut. Now we only sweep stray .wav analysis files, which are
    rebuilt on demand and have no edit value."""
    if not os.path.isdir(UPLOAD_DIR):
        return
    for name in os.listdir(UPLOAD_DIR):
        if not name.lower().endswith('.wav'):
            continue
        p = os.path.join(UPLOAD_DIR, name)
        try:
            if os.path.isfile(p):
                os.remove(p)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Lazy filmstrip: generate frames on demand, or in small batches
# ---------------------------------------------------------------------------
def _generate_filmstrip_lazy(video_path, output_dir, num_frames=60, height=80,
                             batch_size=10, progress_callback=None):
    """
    Extract evenly-spaced thumbnail frames in small parallel batches.
    Using lazy/batched extraction avoids spawning 60 ffmpeg processes at once
    for a 4-hour video, which can saturate I/O on slow disks.

    Returns list of {time, filename}.
    """
    from cutter import get_video_info
    info = get_video_info(video_path)
    duration = info['duration']
    interval = duration / num_frames if num_frames else 0

    filmstrip_dir = os.path.join(output_dir, 'filmstrip')
    os.makedirs(filmstrip_dir, exist_ok=True)

    def _extract_frame(i):
        t = i * interval
        fname = f"frame_{i:04d}.jpg"
        fpath = os.path.join(filmstrip_dir, fname)
        if os.path.exists(fpath):
            return (i, t, fname, True)
        cmd = [
            media_tools.ffmpeg(), '-y',
            '-ss', str(t),
            '-i', video_path,
            '-frames:v', '1',
            '-vf', f'scale=-1:{height}',
            '-q:v', '8',
            fpath
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                log.debug("Filmstrip frame %d ffmpeg returned %d: %s", i, result.returncode, result.stderr[:200])
        except subprocess.TimeoutExpired:
            log.warning("Filmstrip frame %d timed out at t=%.1f", i, t)
        return (i, t, fname, os.path.exists(fpath))

    frames_map = {}
    indices = list(range(num_frames))

    for batch_start in range(0, num_frames, batch_size):
        batch = indices[batch_start:batch_start + batch_size]
        with ThreadPoolExecutor(max_workers=min(batch_size, 8)) as pool:
            futs = {pool.submit(_extract_frame, i): i for i in batch}
            for fut in as_completed(futs):
                try:
                    i, t, fname, exists = fut.result()
                    if exists:
                        frames_map[i] = {'time': round(t, 2), 'filename': fname}
                except Exception as e:
                    log.warning("Filmstrip frame failed: %s", e)
        if progress_callback:
            progress_callback(batch_start + len(batch), num_frames)

    frames = [frames_map[i] for i in range(num_frames) if i in frames_map]
    log.info("Filmstrip: %d frames extracted", len(frames))
    return frames


# ---------------------------------------------------------------------------
# SSE progress endpoint
# ---------------------------------------------------------------------------
@app.route('/api/progress/<job_id>')
def job_progress_stream(job_id):
    """
    Server-Sent Events stream for real-time job progress.
    SESSIE 28 — accepts ?token=... query param (EventSource cannot set
    custom headers).
    """
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err

    def generate():
        last_sent = None
        # Long DJ sets (~60+ min) routinely take 12–20 min to fully process —
        # filmstrip + chunked HPSS + 48 parallel ffmpeg cuts. The previous
        # 10-minute cap closed the SSE stream mid-job and the UI froze on the
        # last percentage it saw. Allow up to an hour. The stream still exits
        # immediately when status hits 'done' or 'error'.
        timeout = 3600  # max 60 min stream
        start = time.time()
        while time.time() - start < timeout:
            snap = _get_snapshot(job_id)
            if snap is None:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            payload = {
                'status': snap.get('status'),
                'message': snap.get('message'),
                'progress': snap.get('progress', {}),
            }
            serialised = json.dumps(payload)
            if serialised != last_sent:
                yield f"data: {serialised}\n\n"
                last_sent = serialised
            if snap.get('status') in ('done', 'error'):
                break
            time.sleep(0.5)

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


# ---------------------------------------------------------------------------
# Background processing
# ---------------------------------------------------------------------------
def _process_job(job_id, video_path, clip_duration, min_gap, formats,
                 sensitivity, use_demucs, normalize_audio, overlay_text,
                 bars_before, bars_after):
    """Background processing with granular progress tracking."""
    audio_path = os.path.join(UPLOAD_DIR, f"{job_id}.wav")

    try:
        _update_job(job_id, status='extracting_audio',
                    message='Reading your live DJ set...')
        _update_progress(job_id, stage='extracting_audio', stage_index=0, percent=2,
                         total_clips=0, clips_done=0, completed_indices=[],
                         workers=[], total_thumbs=0, thumbs_done=0)

        extract_audio(video_path, audio_path)

        video_info = get_video_info(video_path)
        _update_job(job_id, video_info=video_info)
        _update_progress(job_id, percent=8)

        # --- Stage 2: Detect BPM (8–12%) ---
        _update_job(job_id, status='detecting_bpm',
                    message='Analysing the waveform and beats')
        _update_progress(job_id, stage='detecting_bpm', stage_index=1, percent=9)
        bpm_info = detect_bpm(audio_path, sr=11025)
        _update_job(job_id, bpm=bpm_info)
        _update_progress(job_id, percent=12)

        # --- Stage 3: Analyze drops/buildups (12–40%) ---
        _update_job(job_id, status='analyzing')
        if use_demucs and HAS_DEMUCS:
            _update_job(job_id, message='Listening for the drops...')
            _update_progress(job_id, stage='analyzing_demucs', stage_index=2, percent=14)
            clips = analyze_with_demucs(
                audio_path, clip_duration=clip_duration, min_gap=min_gap,
                sensitivity=sensitivity, bars_before=bars_before, bars_after=bars_after,
            )
        else:
            _update_job(job_id, message='Listening for the drops...')
            _update_progress(job_id, stage='analyzing', stage_index=2, percent=14)
            clips = analyze_dj_set(
                audio_path, clip_duration=clip_duration, min_gap=min_gap,
                sensitivity=sensitivity, bars_before=bars_before, bars_after=bars_after,
                bpm_info=bpm_info,
            )

        _update_job(job_id, clips=clips)
        _update_progress(job_id, percent=50)

        # SAFETY (2026-04-28): persist the analyser output to disk *before*
        # the cut step. If anything later in the pipeline crashes (e.g. a
        # bad cmd-builder call), the user can resume / re-cut without paying
        # the 5–10 minute HPSS pass on a 4-hour set again.
        try:
            snap_now = _get_snapshot(job_id)
            if snap_now:
                _persist_job_snapshot(snap_now)
        except Exception as _e:
            log.warning("post-analysis snapshot persist failed: %s", _e)

        # SESSIE 18 — short-circuit on empty analyses. Silent / low-energy
        # / very-short uploads (and any source that genuinely has no drops)
        # would previously sail into `process_clips` and crash on a
        # `max_workers=0` ProcessPoolExecutor. Now we stop early with a
        # clean status so the dashboard, the watch-folder daemon and the
        # quota-counter all see a coherent terminal state. We deliberately
        # mark status='done' (not 'error') because the analysis itself
        # succeeded; there just isn't anything to cut. usage_counted stays
        # False so an empty set doesn't burn a quota slot.
        if not clips:
            log.info("Job %s: analyser found 0 clips — skipping cut/encode.", job_id)
            _update_job(
                job_id,
                status='done',
                message='No drops or buildups detected — nothing to cut.',
                no_clips_detected=True,
            )
            _update_progress(job_id, stage='done', stage_index=8, percent=100)
            snap = _get_snapshot(job_id)
            if snap:
                try:
                    _append_to_history(snap)
                except Exception as _e:
                    log.warning("history append on empty job failed: %s", _e)
            return

        # --- Stage 5: Waveform + filmstrip (50–58%) ---
        _update_job(job_id, status='waveform', message='Generating waveform...')
        _update_progress(job_id, stage='waveform', stage_index=4, percent=51)
        waveform, duration = get_waveform_data(audio_path)
        _update_job(job_id, waveform=waveform, duration=duration)
        _update_progress(job_id, percent=54)

        # Lazy filmstrip in small batches
        _update_job(job_id, message='Extracting video preview frames...')
        job_output_dir = os.path.join(OUTPUT_DIR, job_id)
        os.makedirs(job_output_dir, exist_ok=True)

        def filmstrip_progress(done, total):
            pct = int(54 + (done / total) * 4) if total else 58
            _update_progress(job_id, percent=pct)

        filmstrip = _generate_filmstrip_lazy(
            video_path, job_output_dir, num_frames=60, height=80,
            batch_size=10, progress_callback=filmstrip_progress
        )
        _update_job(job_id, filmstrip=filmstrip)
        _update_progress(job_id, percent=58)

        # --- Stage 5b: keyframe index (large-file pipeline only) ---
        # Built ONCE at upload time. Subsequent `-ss` values snap to a real
        # keyframe so seek on the source is free even for a 10-hour file.
        keyframes = None
        long_set = LARGE_FILE_PIPELINE and (duration or 0) >= LARGE_DURATION_THRESHOLD
        if long_set:
            _update_job(job_id, message='Building keyframe index for fast seek...')
            try:
                keyframes = build_keyframe_index(video_path)
                if keyframes:
                    log.info("Keyframe index built: %d keyframes for %d-second source",
                             len(keyframes), int(duration or 0))
                    _update_job(job_id, keyframe_count=len(keyframes))
            except Exception as e:
                log.warning("Keyframe index build failed: %s", e)

        # --- Stage 6: Cut clips in parallel (58–88%) ---
        _update_job(job_id, status='cutting')
        total_clips = len(clips)
        if long_set:
            _update_job(job_id,
                        message=f'Cutting your {total_clips} clips...')
        else:
            _update_job(job_id, message=f'Cutting your {total_clips} clips...')
        _update_progress(job_id, stage='cutting', stage_index=5, percent=58,
                         total_clips=total_clips, clips_done=0, workers=[])

        def on_clip_progress(clip_index, clip_info, worker_id, event):
            """Thread-safe progress callback invoked by cutter.process_clips."""
            with jobs_lock:
                if job_id not in jobs:
                    return
                progress = jobs[job_id].setdefault('progress', {})
                workers = progress.setdefault('workers', [])
                if event == 'start':
                    found = False
                    for w in workers:
                        if w['id'] == worker_id:
                            w.update({'clip_index': clip_index,
                                      'clip_type': clip_info.get('type', 'clip'),
                                      'clip_time': clip_info.get('start', 0),
                                      'status': 'active'})
                            found = True
                            break
                    if not found:
                        workers.append({
                            'id': worker_id,
                            'clip_index': clip_index,
                            'clip_type': clip_info.get('type', 'clip'),
                            'clip_time': clip_info.get('start', 0),
                            'status': 'active',
                        })
                elif event == 'done':
                    completed = progress.setdefault('completed_indices', [])
                    if clip_index not in completed:
                        completed.append(clip_index)
                    progress['clips_done'] = len(completed)
                    for w in workers:
                        if w['id'] == worker_id:
                            w['status'] = 'idle'
                            break
                    clips_done = len(completed)
                    cutting_pct = (clips_done / total_clips) * 30 if total_clips else 30
                    progress['percent'] = int(58 + cutting_pct)
                    jobs[job_id]['message'] = f'Cut {clips_done} of {total_clips} clips...'

        # SESSIE 74 - fase 2b: zet de per-workspace brand in de job-map zodat de
        # cutter (die output_dir eerst leest) de juiste brand bakt. No-op zonder
        # workspace/cache -> globale fallback (geen regressie).
        _materialize_job_brand(job_id, job_output_dir)

        if long_set:
            # Two-tier — fast 720p proxies for every clip; landscape/vertical
            # full-quality cuts are produced on-demand via /api/render-clip.
            results = process_proxy_clips(
                video_path, clips, job_output_dir, keyframes=keyframes,
                normalize_audio=normalize_audio,
                progress_callback=on_clip_progress
            )
            _update_job(job_id, results=results, keyframes=keyframes,
                        large_file_pipeline=True)
        else:
            results = process_clips(
                video_path, clips, job_output_dir, formats,
                overlay_text=overlay_text if overlay_text else None,
                normalize_audio=normalize_audio,
                parallel=True,
                progress_callback=on_clip_progress
            )
            _update_job(job_id, results=results)
        _update_progress(job_id, percent=88, workers=[])

        # --- Stage 7: Thumbnails (88–95%) ---
        _update_job(job_id, status='thumbnails', message='Verifying thumbnails...')
        total_thumbs = len(results)
        _update_progress(job_id, stage='thumbnails', stage_index=6, percent=89,
                         total_thumbs=total_thumbs, thumbs_done=0)

        missing_thumbs = 0
        for ti, result in enumerate(results):
            thumb_fname = result.get('thumbnail')
            if thumb_fname:
                thumb_path = os.path.join(job_output_dir, thumb_fname)
                if not os.path.exists(thumb_path):
                    thumb_fname = None

            if not thumb_fname:
                missing_thumbs += 1
                clip_idx = result.get('index', ti)
                thumb_fname = f"thumb_clip{clip_idx:02d}.jpg"
                thumb_path = os.path.join(job_output_dir, thumb_fname)
                peak = result.get('peak_time') or result.get('start', 0)
                try:
                    generate_thumbnail(video_path, peak, thumb_path)
                    result['thumbnail'] = thumb_fname
                except Exception as e:
                    # TimeoutExpired, RuntimeError, OSError — skip gracefully
                    log.warning("Thumbnail failed for clip %s: %s", clip_idx, e)
                    result['thumbnail'] = None
            else:
                result['thumbnail'] = thumb_fname

            _update_progress(
                job_id,
                thumbs_done=ti + 1,
                percent=int(89 + ((ti + 1) / total_thumbs) * 6) if total_thumbs else 95
            )

        if missing_thumbs:
            log.info("Generated %d missing thumbnails as fallback", missing_thumbs)

        # Flush updated thumbnail fields back into the job dict so /api/status
        # reflects the correct thumbnail paths after the loop finishes.
        _update_job(job_id, results=results)

        # --- Stage 8: Finalize (95–100%) ---
        _update_job(job_id, status='finalizing', message='Exporting CSV and cleaning up...')
        _update_progress(job_id, stage='finalizing', stage_index=7, percent=96)

        csv_path = os.path.join(job_output_dir, 'clips.csv')
        export_clips_csv(results, csv_path)
        _update_job(job_id, csv_path=csv_path)

        _update_progress(job_id, stage='done', stage_index=8, percent=100)
        _update_job(job_id, status='done', message=f'Done! {len(results)} clips ready.')

        # Phase 3: increment quota counter exactly once per successfully
        # completed analysis. The `usage_counted` flag keeps this idempotent
        # if _process_job ever runs twice for the same job (resume path).
        with jobs_lock:
            j = jobs.get(job_id) or {}
            already_counted = bool(j.get('usage_counted'))
            user_id_for_quota = j.get('user_id')
            access_token_for_quota = j.get('access_token')
        if user_id_for_quota and not already_counted:
            new_count = _increment_usage(user_id_for_quota, access_token=access_token_for_quota)
            if new_count is not None:
                _update_job(job_id, usage_counted=True)

        # Persist to history (lock-free helper — reads a snapshot)
        snap = _get_snapshot(job_id)
        if snap:
            _append_to_history(snap)

    except Exception as e:
        log.exception("Error processing job %s", job_id)
        # SESSIE 68 — capture the full traceback into job state. In the packaged
        # .app stdout is swallowed (runw), so log.exception is invisible; storing
        # the traceback here lets /api/status surface the real failing line for
        # debugging (e.g. the zlib "incorrect header check" analysis crash).
        import traceback as _tb
        tb_text = _tb.format_exc()
        with jobs_lock:
            if job_id in jobs:
                jobs[job_id]['status'] = 'error'
                jobs[job_id]['message'] = str(e)
                jobs[job_id]['traceback'] = tb_text
                jobs[job_id].setdefault('progress', {})['stage'] = 'error'

    finally:
        # Always remove the analysis-only audio file
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                log.info("Cleaned up temp audio: %s", audio_path)
            except OSError:
                pass
        # Remove the uploaded source video — keep output clips
        _cleanup_source_video(job_id)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/auth/health', methods=['GET'])
def api_auth_health():
    """Verify Supabase connection. Used tijdens setup + debugging.
    Returns ok=true als URL/key/netwerk allemaal valid zijn."""
    return jsonify(auth_health_check())


@app.route('/api/auth/signup', methods=['POST'])
@limiter.limit("5 per hour")
def api_auth_signup():
    """Register a new user. Body: {email, password, intake?}.
    The handle_new_user trigger creates their profiles row automatically;
    SESSIE 22 added the `intake` payload — pre-signup questionnaire answers
    that get patched onto the profile via service_role after auth.sign_up.
    Intake schema: see auth.signup() docstring."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    intake = data.get('intake') if isinstance(data.get('intake'), dict) else None
    if not email or '@' not in email:
        return jsonify({'ok': False, 'error': 'Geldig email-adres is verplicht'}), 400
    if not password or len(password) < 8:
        return jsonify({'ok': False, 'error': 'Wachtwoord moet minstens 8 tekens zijn'}), 400
    # Validate the *required* intake fields when intake is supplied.
    if intake is not None:
        missing = []
        for req in ('artist_name', 'full_name', 'referral_source'):
            v = intake.get(req)
            if not isinstance(v, str) or not v.strip():
                missing.append(req)
        if missing:
            return jsonify({
                'ok': False,
                'error': 'Missing required intake fields: ' + ', '.join(missing),
            }), 400
    result = auth_signup(email, password, intake=intake)
    # SESSIE 35 — audit log
    _audit(
        'auth.signup',
        user_id=result.get('user_id'),
        metadata={'ok': result.get('ok'), 'email': email},
    )
    return jsonify(result), (200 if result.get('ok') else 400)


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per 5 minutes")
def api_auth_login():
    """Sign in existing user. Body: {email, password}.
    Returns access_token + refresh_token on success."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'ok': False, 'error': 'Email en wachtwoord zijn verplicht'}), 400
    result = auth_login(email, password)
    # SESSIE 35 — audit log. user_id is None bij mislukking (onbekende user).
    _audit(
        'auth.login' if result.get('ok') else 'auth.login_failed',
        user_id=result.get('user_id'),
        metadata={'ok': result.get('ok'), 'email': email},
    )
    return jsonify(result), (200 if result.get('ok') else 401)


@app.route('/api/auth/refresh', methods=['POST'])
@limiter.limit("30 per hour")
def api_auth_refresh():
    """SESSIE 30b - exchange a refresh_token for a new access_token + a
    rotated refresh_token. Lets the frontend keep going indefinitely
    without forcing the user to log in again. The refresh_token MUST be
    sent in the JSON body (never in a query-string, never logged).

    Body: { refresh_token: "..." }
    Returns: { ok, access_token, refresh_token, expires_at, user_id, email }
    """
    data = request.get_json(silent=True) or {}
    rt = (data.get('refresh_token') or '').strip()
    if not rt:
        return jsonify({'ok': False, 'error': 'refresh_token ontbreekt'}), 400
    result = auth_refresh_session(rt)
    return jsonify(result), (200 if result.get('ok') else 401)


# ---------------------------------------------------------------------------
# SESSIE 40 (2026-05-26) — Password Reset endpoints
# ---------------------------------------------------------------------------
# Twee endpoints werken samen volgens SESSIE34-PASSWORD-RESET-PLAN.md:
#   POST /api/auth/forgot-password — stuurt reset-mail (altijd ok=True om
#                                    account-enumeration te voorkomen)
#   POST /api/auth/reset-password  — wijzigt password met tokens uit mail
#
# Rate-limiting per-IP via flask-limiter's default get_remote_address.
# De forgot-endpoint heeft een tweede limiet per-email om gerichte mail-bombing
# tegen te gaan: als IP roteert, dan vangt de per-email cap het op.

def _forgot_email_key():
    """flask-limiter key_func dat key=email gebruikt zodat we per-email kunnen
    rate-limiten naast per-IP. Leeg email-veld → key 'no-email' (wordt nooit
    gehit want forgot_password() rejecten lege emails meteen)."""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        return f'forgot-email:{email}' if email else 'forgot-email:none'
    except Exception:
        return 'forgot-email:err'


@app.route('/api/auth/forgot-password', methods=['POST'])
@limiter.limit("3 per hour")              # per-IP cap
@limiter.limit("5 per hour", key_func=_forgot_email_key)  # per-email cap
def api_auth_forgot_password():
    """SESSIE 40 — vraag een reset-mail aan.
    Body: { email: "user@example.com" }
    Returns ALTIJD { ok: true } — ongeacht of de email bestaat. Dit voorkomt
    dat een aanvaller via response-verschillen kan ontdekken welke emails
    een account hebben (account-enumeration). De rate-limit zit dus deels
    op de endpoint zelf, en deels in de fail-silent logica in auth.py.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    # forgot_password() returnt altijd {ok: True} — geen branching op result
    auth_forgot_password(email)
    # Audit: log dat een reset werd aangevraagd. user_id kennen we niet
    # (zou enumeration mogelijk maken om die op te zoeken), dus alleen email.
    _audit(
        'auth.password_reset_requested',
        user_id=None,
        metadata={'email': email},
    )
    return jsonify({'ok': True}), 200


@app.route('/api/auth/reset-password', methods=['POST'])
@limiter.limit("5 per 10 minutes")
def api_auth_reset_password():
    """SESSIE 40 — pas een nieuw wachtwoord toe na klik op reset-link.
    Body: { access_token, refresh_token, new_password }
    De tokens komen uit het URL-fragment van Supabase's reset-redirect.
    De frontend (static/reset-password.html) extraheert ze, valideert
    password-confirmation, en POST't hier.
    """
    data = request.get_json(silent=True) or {}
    access_token  = (data.get('access_token')  or '').strip()
    refresh_token = (data.get('refresh_token') or '').strip()
    new_password  = data.get('new_password') or ''

    result = auth_reset_password(access_token, refresh_token, new_password)

    # Audit: log of reset slaagde of niet. Bij success kennen we de user_id;
    # bij failure niet (token kan ongeldig zijn).
    _audit(
        'auth.password_reset' if result.get('ok') else 'auth.password_reset_failed',
        user_id=result.get('user_id'),
        metadata={'ok': result.get('ok')},
    )

    return jsonify(result), (200 if result.get('ok') else 400)


@app.route('/api/auth/me', methods=['GET'])
def api_auth_me():
    """Return current user's info + profile (plan, usage).
    Requires Authorization: Bearer <access_token> header."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.lower().startswith('bearer '):
        return jsonify({'ok': False, 'error': 'Geen Authorization header'}), 401
    token = auth_header[7:].strip()
    user_info = auth_get_user_from_token(token)
    if not user_info:
        return jsonify({'ok': False, 'error': 'Ongeldig of verlopen token'}), 401
    return jsonify({'ok': True, **user_info})


@app.route('/api/profile', methods=['POST'])
def api_profile_update():
    """SESSIE 30 - update the caller's profile (full_name, artist_name).
    Sidebar header reads full_name to render "Workstation of: NAME".

    Strategy:
      1. Prefer supabase_admin when configured (dev) - bypasses RLS.
      2. Otherwise fall back to the anon client with the caller's JWT,
         which respects the "users update own row" RLS policy. This is
         the path taken by the bundled .app where no service_role key
         is present.

    Whitelisted fields only - never trust the client to set plan, quota,
    stripe_customer_id, or any other column.
    """
    user_info, err = _require_authed_user()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    full_name   = (body.get('full_name')   or '').strip()
    artist_name = (body.get('artist_name') or '').strip()
    if not full_name or not artist_name:
        return jsonify({'ok': False, 'error': 'full_name en artist_name zijn beide verplicht'}), 400
    payload = {
        'full_name':   full_name[:120],
        'artist_name': artist_name[:80],
    }
    user_id = user_info['user_id']
    token   = user_info.get('access_token')

    # Path 1: admin client (dev/server). Bypasses RLS.
    if supabase_admin is not None:
        try:
            supabase_admin.table('profiles').update(payload).eq('id', user_id).execute()
            return jsonify({'ok': True, 'profile': payload})
        except Exception as e:
            log.warning('Profile update via admin failed for %s: %s', user_id, e)
            return jsonify({'ok': False, 'error': f'profile update failed: {e}'}), 500

    # Path 2: bundled .app fallback - per-call anon client with the
    # caller's own JWT, relying on a Supabase RLS policy that lets users
    # update their own profile row. If the policy is missing this will
    # 401/403 - we surface that so the user can ask support to enable it.
    try:
        from supabase import create_client as _create_anon_client
        from auth import SUPABASE_URL as _SUP_URL, SUPABASE_ANON_KEY as _SUP_ANON
        anon = _create_anon_client(_SUP_URL, _SUP_ANON)
        # Inject the user's JWT so RLS sees them as the authenticated caller.
        anon.postgrest.auth(token)
        anon.table('profiles').update(payload).eq('id', user_id).execute()
        return jsonify({'ok': True, 'profile': payload})
    except Exception as e:
        log.warning('Profile update via anon client failed for %s: %s', user_id, e)
        return jsonify({
            'ok': False,
            'error': f'profile update failed: {e}. If this persists, '
                     f'support needs to enable the "users update own profile" '
                     f'RLS policy on the profiles table.',
        }), 500


# ---------------------------------------------------------------------------
# SESSIE 29 — Debug log bundle endpoint for beta testers.
# Reads launcher.log + recent app state and returns a single ZIP that a
# tester can attach to a support email. PII-sensitive paths (uploads/output
# file contents) are NEVER included — only diagnostic metadata.
# ---------------------------------------------------------------------------
@app.route('/api/debug/logs', methods=['GET'])
@require_role('admin')  # SESSIE 35 — alleen admins (Sjuul) mogen debug-logs downloaden
def api_debug_logs():
    """Return a ZIP archive containing:
      - launcher.log (from OMNI_DJ_USER_DATA or fallback)
      - tail of system info (platform, python, ffmpeg version)
      - job_history.json (filtered to caller's jobs only)
      - a summary.txt with the caller's user_id, plan, and timestamps

    Query params:
      ?format=text  →  returns plain text instead of ZIP (for copy-paste
                       on machines without download support).

    Auth: required. Only returns the caller's own data — never shows other
    users' jobs or tokens.
    """
    import io as _io
    import platform as _platform
    import zipfile
    from datetime import datetime, timezone

    # SESSIE 35 — access-check gebeurt al via @require_role('admin') decorator.
    # Tweede call hier alleen om user_info te hebben voor de audit log.
    user_info, _ = _require_authed_user()
    _audit('debug.logs_downloaded', user_id=user_info['user_id'] if user_info else None)

    fmt = (request.args.get('format') or 'zip').strip().lower()

    # Locate the launcher.log written by launcher.py — it lives in the
    # per-OS user data dir set by OMNI_DJ_USER_DATA. Falls back to common
    # locations for dev mode (where launcher.py was not the entry point).
    log_candidates = []
    env_dir = os.environ.get('OMNI_DJ_USER_DATA')
    if env_dir:
        log_candidates.append(os.path.join(env_dir, 'launcher.log'))
    home = os.path.expanduser('~')
    if sys.platform == 'darwin':
        log_candidates.append(os.path.join(home, 'Library', 'Application Support', 'Omni DJ', 'launcher.log'))
    elif sys.platform == 'win32':
        appdata = os.environ.get('APPDATA', home)
        log_candidates.append(os.path.join(appdata, 'Omni DJ', 'launcher.log'))
    else:
        log_candidates.append(os.path.join(home, '.clip-live', 'launcher.log'))

    launcher_log_text = ''
    launcher_log_path = ''
    for cand in log_candidates:
        try:
            if cand and os.path.isfile(cand):
                with open(cand, 'r', encoding='utf-8', errors='replace') as fh:
                    # Tail last 200 KB only — long-running installs can grow huge.
                    fh.seek(0, 2)
                    size = fh.tell()
                    fh.seek(max(0, size - 200 * 1024))
                    launcher_log_text = fh.read()
                launcher_log_path = cand
                break
        except Exception as e:
            launcher_log_text = f'(could not read {cand}: {e!r})'

    # System info — no PII, just versions.
    try:
        ffmpeg_version = subprocess.run(
            [media_tools.ffmpeg(), '-version'],
            capture_output=True, text=True, timeout=5
        ).stdout.splitlines()[0] if subprocess else 'subprocess not available'
    except Exception as e:
        ffmpeg_version = f'(ffmpeg not found: {e!r})'

    summary_lines = [
        f'Omni DJ — diagnostic bundle',
        f'Generated: {datetime.now(timezone.utc).isoformat()}',
        f'',
        f'User:     {user_info.get("user_id", "?")}',
        f'Email:    {user_info.get("email", "?")}',
        f'Plan:     {(user_info.get("profile") or {}).get("plan") or "free (no profile data — supabase_admin not configured in this bundle)"}',
        f'',
        f'Platform: {_platform.platform()}',
        f'Python:   {sys.version.split()[0]}',
        f'ffmpeg:   {ffmpeg_version}',
        f'',
        f'Launcher log path: {launcher_log_path or "(not found)"}',
        f'BASE_DIR:          {BASE_DIR}',
        f'OUTPUT_DIR:        {OUTPUT_DIR}',
    ]
    summary_text = '\n'.join(summary_lines)

    # Filter job_history.json to caller's jobs only — never leak others.
    own_history = []
    try:
        if os.path.isfile(HISTORY_PATH):
            with open(HISTORY_PATH, 'r', encoding='utf-8') as fh:
                full = json.load(fh) or []
            caller_id = user_info.get('user_id')
            for entry in full:
                if isinstance(entry, dict) and entry.get('user_id') == caller_id:
                    # Strip filename to just the basename for privacy.
                    redacted = dict(entry)
                    if 'filename' in redacted:
                        redacted['filename'] = os.path.basename(str(redacted['filename']))
                    own_history.append(redacted)
    except Exception as e:
        own_history = [{'_error': f'could not read history: {e!r}'}]

    history_text = json.dumps(own_history, indent=2, ensure_ascii=False)

    if fmt == 'text':
        # Plain-text combined view for copy-paste support workflows.
        combined = (
            f'=== summary.txt ===\n{summary_text}\n\n'
            f'=== launcher.log (last 200 KB) ===\n{launcher_log_text or "(empty)"}\n\n'
            f'=== your jobs (job_history.json filtered) ===\n{history_text}\n'
        )
        return combined, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    # ZIP path — single file, no temp on disk.
    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('summary.txt', summary_text)
        zf.writestr('launcher.log', launcher_log_text or '(empty)')
        zf.writestr('job_history_yours.json', history_text)
    buf.seek(0)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    fname = f'clip-live-diagnostics-{ts}.zip'
    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=fname,
    )


@app.route('/api/quota', methods=['GET'])
def api_quota():
    """Phase 3: report the caller's plan limit + current usage in the
    rolling 30-day window. Triggers an auto-reset if the window has expired,
    so the frontend gets a fresh number without needing a separate /reset
    call.

    Auth: Authorization: Bearer <access_token>

    Response:
      { ok: true,
        plan: 'free' | 'pro' | 'studio',
        used: int,
        limit: int | null,        // null means unlimited (Studio)
        remaining: int | null,
        reset_in_days: int | null,
        reset_date: ISO string | null }
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.lower().startswith('bearer '):
        return jsonify({'ok': False, 'error': 'Geen Authorization header'}), 401
    token = auth_header[7:].strip()
    user_info = auth_get_user_from_token(token)
    if not user_info:
        return jsonify({'ok': False, 'error': 'Ongeldig of verlopen token'}), 401

    snap = _get_or_refresh_profile(user_info['user_id'], access_token=token)
    if not snap.get('ok'):
        return jsonify({'ok': False, 'error': snap.get('error', 'profile read failed')}), 500

    limit = snap['limit']
    remaining = snap['remaining']
    return jsonify({
        'ok': True,
        'plan': snap['plan'],
        'used': snap['used'],
        'limit': (None if limit == float('inf') else int(limit)),
        'remaining': (None if remaining == float('inf') else int(remaining)),
        'reset_in_days': snap['reset_in_days'],
        'reset_date': snap['reset_date'],
    })


# ---------------------------------------------------------------------------
# Plan-gating (Phase 3) — quota counter + tier limits.
# Single source of truth for "how many sets per 30-day window per plan".
# Used by upload endpoints (gate), _process_job (increment), /api/quota (read).
# ---------------------------------------------------------------------------

PLAN_LIMITS = {
    'free':   2,
    'pro':    10,
    'studio': float('inf'),
}


def _parse_pg_timestamp(value):
    """Best-effort parse of a Supabase timestamptz string into a tz-aware
    datetime. Returns None on empty / unparseable input. Handles both the
    'Z' suffix and the '+00:00' suffix that supabase-py can return."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        s = str(value)
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _get_or_refresh_profile(user_id, access_token=None):
    """Read a user's profile via supabase_admin (bypasses RLS), and reset
    the rolling 30-day quota window if it has expired.

    SESSIE 30 - if supabase_admin is None (bundled .app: no service_role key)
    and an access_token is provided, route through the update-usage edge
    function with the caller's JWT instead. Same shape on success/failure.

    Returns:
      {ok: True, profile, plan, used, limit, remaining, reset_date, reset_in_days}
      {ok: False, error: '...'}
    """
    if supabase_admin is None:
        if access_token:
            try:
                from auth import call_update_usage_edge_function
                edge = call_update_usage_edge_function(access_token, 'get')
            except Exception as e:
                return {'ok': False, 'error': f'edge function call failed: {e}'}
            if not edge.get('ok'):
                return {'ok': False, 'error': edge.get('error') or 'edge function failure'}
            # Normalise limit (edge returns null for studio, we use float inf locally)
            limit_val = edge.get('limit')
            if limit_val is None:
                limit_val = float('inf')
            remaining_val = edge.get('remaining')
            if remaining_val is None:
                remaining_val = float('inf')
            return {
                'ok': True,
                'profile': edge.get('profile') or {},
                'plan': edge.get('plan') or 'free',
                'used': int(edge.get('used') or 0),
                'limit': limit_val,
                'remaining': remaining_val,
                'reset_date': edge.get('reset_date'),
                'reset_in_days': edge.get('reset_in_days'),
            }
        return {'ok': False, 'error': 'supabase_admin niet geconfigureerd'}
    if not user_id:
        return {'ok': False, 'error': 'user_id ontbreekt'}

    try:
        resp = supabase_admin.table('profiles').select('*').eq('id', user_id).single().execute()
        profile = getattr(resp, 'data', None)
    except Exception as e:
        return {'ok': False, 'error': f'profile read failed: {type(e).__name__}: {e}'}

    if not profile:
        return {'ok': False, 'error': 'profile not found'}

    plan = (profile.get('plan') or 'free').strip().lower()
    if plan not in PLAN_LIMITS:
        plan = 'free'
    limit = PLAN_LIMITS[plan]

    used = int(profile.get('usage_this_period') or 0)
    reset_date = _parse_pg_timestamp(profile.get('quota_reset_date'))
    now = datetime.now(timezone.utc)

    if reset_date is not None and now >= reset_date:
        new_reset = reset_date + timedelta(days=30)
        # Roll forward more than one cycle if the user has been away for >30d
        # so we don't end up with a reset_date still in the past.
        while new_reset <= now:
            new_reset = new_reset + timedelta(days=30)
        try:
            supabase_admin.table('profiles').update({
                'usage_this_period': 0,
                'quota_reset_date': new_reset.isoformat(),
            }).eq('id', user_id).execute()
            profile['usage_this_period'] = 0
            profile['quota_reset_date']  = new_reset.isoformat()
            used = 0
            reset_date = new_reset
            log.info('Quota window rolled for %s -> %s', user_id, new_reset.isoformat())
        except Exception as e:
            log.warning('Quota reset failed for %s: %s', user_id, e)

    if limit == float('inf'):
        remaining = float('inf')
    else:
        remaining = max(0, limit - used)

    if reset_date is not None:
        reset_in_days = max(0, (reset_date - now).days)
    else:
        reset_in_days = None

    return {
        'ok': True,
        'profile': profile,
        'plan': plan,
        'used': used,
        'limit': limit,
        'remaining': remaining,
        'reset_date': profile.get('quota_reset_date'),
        'reset_in_days': reset_in_days,
    }


def _increment_usage(user_id, access_token=None):
    """Bump usage_this_period by 1. Called once per successfully completed
    analysis from inside _process_job. Bypasses RLS via supabase_admin.
    Logs and swallows errors  never raises into the worker thread.
    Returns the new usage count, or None on failure.

    SESSIE 30 - if supabase_admin is None (bundled .app) and access_token is
    given, increment via the update-usage edge function instead.
    """
    if not user_id:
        return None
    if supabase_admin is None:
        if not access_token:
            return None
        try:
            from auth import call_update_usage_edge_function
            edge = call_update_usage_edge_function(access_token, 'increment')
        except Exception as e:
            log.warning('Quota increment edge call raised for %s: %s', user_id, e)
            return None
        if not edge.get('ok'):
            log.warning('Quota increment edge function failed for %s: %s', user_id, edge.get('error'))
            return None
        new_val = int(edge.get('used') or 0)
        log.info('Quota incremented via edge function for %s -> %d', user_id, new_val)
        return new_val
    try:
        # Read-modify-write. Acceptable race profile for a one-user-per-machine
        # local app. If we go multi-device for a single account, swap this for
        # an atomic Postgres RPC (UPDATE ... SET usage = usage + 1 RETURNING).
        resp = supabase_admin.table('profiles').select('usage_this_period').eq('id', user_id).single().execute()
        cur = int((getattr(resp, 'data', None) or {}).get('usage_this_period') or 0)
        new_val = cur + 1
        supabase_admin.table('profiles').update({
            'usage_this_period': new_val,
        }).eq('id', user_id).execute()
        log.info('Quota incremented for %s: %d -> %d', user_id, cur, new_val)
        return new_val
    except Exception as e:
        log.warning('Quota increment failed for %s: %s', user_id, e)
        return None


def _quota_block_response(snap):
    """Build the 402 Payment Required body from a _get_or_refresh_profile
    result. Centralised so all gated endpoints return identical shape."""
    used  = snap.get('used', 0)
    limit = snap.get('limit', 0)
    plan  = snap.get('plan', 'free')
    return jsonify({
        'ok': False,
        'error': 'quota_exceeded',
        'message': (
            f"You've used {used} of {limit} sets this month. "
            f"Upgrade to keep going."
        ),
        'plan': plan,
        'used': used,
        'limit': (None if limit == float('inf') else limit),
        'reset_in_days': snap.get('reset_in_days'),
        'reset_date': snap.get('reset_date'),
        'upgrade_url': '/api/billing/checkout',
    }), 402


# ---------------------------------------------------------------------------
# Billing — Stripe Checkout + Customer Portal.
# Webhook lives in supabase/functions/stripe-webhook/index.ts (Optie A).
# Flask only initiates redirects; Stripe and the edge function do the rest.
# ---------------------------------------------------------------------------

# SESSIE 72 — TTL-cache op token-validatie. /api/status wordt elke ~1.5s
# gepolld tijdens analyse; zonder cache deed elke poll een Supabase
# auth/v1/user round-trip (netwerk-chatter + latency die met de CPU-zware
# analyse-thread concurreert). Met een 30s-cache valideren we 1x per 30s
# i.p.v. ~20x. Veilig voor een lokaal single-user tool: het token heeft een
# eigen exp (~1u) en revocatie binnen 30s is verwaarloosbaar. Per-token
# gekeyd, dus geen cross-user lek. Alleen geldige validaties worden gecachet.
_TOKEN_USER_CACHE = {}            # token -> (user_info_base, expiry_ts)
_TOKEN_USER_CACHE_TTL = 30.0
_TOKEN_USER_CACHE_LOCK = threading.Lock()


def _cached_auth_user(token):
    """Wrap auth_get_user_from_token met een korte TTL-cache (zie boven)."""
    now = time.time()
    with _TOKEN_USER_CACHE_LOCK:
        hit = _TOKEN_USER_CACHE.get(token)
        if hit and hit[1] > now:
            return dict(hit[0])
    info = auth_get_user_from_token(token)
    if info:
        with _TOKEN_USER_CACHE_LOCK:
            if len(_TOKEN_USER_CACHE) > 256:
                stale = [k for k, (_v, exp) in list(_TOKEN_USER_CACHE.items()) if exp <= now]
                for k in stale[:200]:
                    _TOKEN_USER_CACHE.pop(k, None)
            _TOKEN_USER_CACHE[token] = (dict(info), now + _TOKEN_USER_CACHE_TTL)
        return dict(info)
    return None


def _require_authed_user(allow_query_token=False):
    """Helper: extract Bearer token, validate, return user_info dict.
    On failure returns (None, (json_response, status_code)).
    On success returns (user_info, None).

    SESSIE 28 — when `allow_query_token=True` the helper ALSO accepts a
    ?token=<jwt> query-string parameter. Needed for media endpoints that
    are loaded via <img>/<video>/EventSource where the browser cannot set
    custom headers.

    Usage in route:
        user_info, err = _require_authed_user()
        if err: return err
    """
    token = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.lower().startswith('bearer '):
        token = auth_header[7:].strip()
    elif allow_query_token:
        token = (request.args.get('token') or '').strip()
    if not token:
        return None, (jsonify({'ok': False, 'error': 'Geen Authorization header'}), 401)
    user_info = _cached_auth_user(token)
    if not user_info:
        return None, (jsonify({'ok': False, 'error': 'Ongeldig of verlopen token'}), 401)
    # SESSIE 30 - keep the raw access token on the user_info so quota
    # callers can route through the update-usage edge function when no
    # service_role key is configured (i.e. the bundled .app).
    user_info['access_token'] = token
    return user_info, None


# ---------------------------------------------------------------------------
# SESSIE 73 - A1 multi-tenant backend (Spoor A, PLAN-COMBINED v1.3 Correctie 6)
#
# De backend draait vandaag alle DB-queries via supabase_admin (service_role),
# wat RLS VOLLEDIG omzeilt. Voor de nieuwe content-tabellen (workspaces,
# workspace_members, clips, dj_profiles, dj_templates, scheduled_posts) is dat
# onveilig: dan is RLS decoratief en kan data tussen artists lekken. Daarom een
# aparte anon-client die de USER-JWT meedraagt, zodat PostgREST queries als rol
# 'authenticated' draaien en auth.uid() klopt -> RLS is de echte isolatie-grens.
#
# supabase_admin BLIJFT voor profiel/role/billing/audit (vertrouwde server-acties
# die juist boven RLS moeten staan). Deze helpers zijn ADDITIEF: geen bestaand
# endpoint (analyse/export/auth) verandert; alleen nieuwe content-routes (vanaf
# /api/workspaces) gebruiken ze.
# ---------------------------------------------------------------------------
def _user_supabase(access_token):
    """Anon Supabase client gebonden aan de end-user-JWT (RLS-scoped).

    Maakt een VERSE client per call zodat er geen gedeelde, muteerbare
    auth-state tussen requests/threads ontstaat (postgrest.auth muteert de
    client). Retourneert None als Supabase niet is geconfigureerd of de JWT
    ontbreekt -> additieve callers kunnen dan netjes no-op'en.
    """
    if not access_token:
        return None
    try:
        from auth import SUPABASE_URL as _URL, SUPABASE_ANON_KEY as _ANON
    except Exception:
        return None
    if not _URL or not _ANON:
        return None
    try:
        from supabase import create_client
        ClientOptions = None
        try:
            from supabase import ClientOptions as _CO
            ClientOptions = _CO
        except Exception:
            try:
                from supabase.lib.client_options import ClientOptions as _CO2
                ClientOptions = _CO2
            except Exception:
                ClientOptions = None
        if ClientOptions is not None:
            client = create_client(_URL, _ANON, options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False,
                headers={'Authorization': f'Bearer {access_token}'},
            ))
        else:
            client = create_client(_URL, _ANON)
        # Belt + suspenders: zet de PostgREST-bearer expliciet zodat table()-
        # calls de user-JWT sturen ongeacht client-interne details.
        try:
            client.postgrest.auth(access_token)
        except Exception:
            pass
        return client
    except Exception as e:
        log.warning("_user_supabase init mislukt: %s", e)
        return None


def current_workspace_id(user_info, required=False):
    """Resolve de actieve workspace voor dit request, RLS-scoped.

    Leest de 'X-Omni-Workspace' header. Is die aanwezig, dan een expliciete
    membership-check via de user-client (defence-in-depth BOVENOP RLS: RLS
    blokkeert reads/writes al, dit faalt alleen sneller met een nette 403 bij
    een niet-lid). Ontbreekt de header, dan de primaire workspace van de caller
    (eerste membership).

    Returnt (workspace_id, None) bij succes of (None, (resp, code)) bij een
    fout. Met required=False en geen oplosbare workspace -> (None, None) zodat
    additieve callers kunnen no-op'en.
    """
    token = (user_info or {}).get('access_token')
    uid = (user_info or {}).get('user_id')
    sb = _user_supabase(token)
    if sb is None or not uid:
        if required:
            return None, (jsonify({'ok': False, 'error': 'Supabase niet geconfigureerd'}), 503)
        return None, None
    hdr = (request.headers.get('X-Omni-Workspace') or '').strip()
    try:
        if hdr:
            res = (sb.table('workspace_members')
                     .select('workspace_id')
                     .eq('workspace_id', hdr)
                     .eq('user_id', uid)
                     .limit(1).execute())
            rows = getattr(res, 'data', None) or []
            if not rows:
                return None, (jsonify({'ok': False, 'error': 'Geen lid van deze workspace'}), 403)
            return hdr, None
        # Geen header -> primaire (eerste) membership van de caller.
        res = (sb.table('workspace_members')
                 .select('workspace_id')
                 .eq('user_id', uid)
                 .limit(1).execute())
        rows = getattr(res, 'data', None) or []
        if rows:
            return rows[0].get('workspace_id'), None
    except Exception as e:
        log.warning("current_workspace_id mislukt: %s", e)
        if required:
            return None, (jsonify({'ok': False, 'error': 'workspace-resolutie mislukt'}), 500)
        return None, None
    if required:
        return None, (jsonify({'ok': False, 'error': 'Geen workspace'}), 404)
    return None, None


def _audit(action, user_id=None, metadata=None):
    """SESSIE 35 — Convenience wrapper rond auth_log_action().
    Plukt ip_address en user_agent automatisch uit het actieve Flask-request.
    Fire-and-forget: nooit blocking, nooit raising."""
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
        # X-Forwarded-For kan een komma-lijst zijn (proxies); neem het eerste adres
        ip = ip.split(',')[0].strip() if ip else None
        ua = request.headers.get('User-Agent', '')[:512] or None
    except Exception:
        ip, ua = None, None
    auth_log_action(action, user_id=user_id, ip_address=ip, user_agent=ua, metadata=metadata)


def _require_job_access(job_id, allow_query_token=False):
    """SESSIE 28 — authenticate caller AND verify they own the job_id.

    Returns:
      (user_info, job, None)        on success
      (None, None, (response, code)) on auth or ownership failure

    Ownership is determined by:
      - in-memory job dict: jobs[job_id]['user_id']
      - falling back to the on-disk job snapshot if not in memory.

    Legacy jobs without a user_id field are inaccessible (private by
    default — no leak). An admin can re-bind them via the snapshot if
    needed.

    NB: returns 404 for "not yours" instead of 403, so an attacker
    cannot probe existence of other users' job IDs.
    """
    if not _valid_job_id(job_id):
        return None, None, (jsonify({'ok': False, 'error': 'Invalid job id'}), 400)
    user_info, err = _require_authed_user(allow_query_token=allow_query_token)
    if err:
        return None, None, err
    # Try in-memory first (fast path) then on-disk snapshot (cold path).
    job = None
    with jobs_lock:
        job = jobs.get(job_id)
    if job is None:
        job = _load_job_snapshot(job_id)
    if job is None:
        return None, None, (jsonify({'ok': False, 'error': 'Job not found'}), 404)
    owner = job.get('user_id')
    if owner != user_info['user_id']:
        # Don't reveal existence to other users.
        return None, None, (jsonify({'ok': False, 'error': 'Job not found'}), 404)
    return user_info, job, None


@app.route('/api/workspaces', methods=['GET'])
def api_list_workspaces():
    """SESSIE 73 - A1: lijst de workspaces (artists) van de caller, RLS-scoped.

    Read-only. Loopt via de anon+JWT-client zodat RLS de isolatie-grens is
    (NIET service_role). Returnt [] als Supabase niet is geconfigureerd zodat
    de frontend netjes degradeert. Eerste echte consument van _user_supabase();
    content-writes komen met A2/A3. ADDITIEF: raakt analyse/export/auth niet.
    """
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    if sb is None:
        return jsonify({'ok': True, 'workspaces': []})
    try:
        res = (sb.table('workspaces')
                 .select('id,name,slug,artist_name,avatar_url,owner_id,created_at')
                 .order('created_at')
                 .execute())
        rows = getattr(res, 'data', None) or []
    except Exception as e:
        log.warning("api_list_workspaces mislukt: %s", e)
        return jsonify({'ok': False, 'error': 'Kon workspaces niet laden'}), 502
    uid = user_info.get('user_id')
    for w in rows:
        try:
            w['is_owner'] = (w.get('owner_id') == uid)
        except Exception:
            pass
    return jsonify({'ok': True, 'workspaces': rows})


@app.route('/api/billing/health', methods=['GET'])
def api_billing_health():
    """Report whether Stripe is configured. Used during setup + debugging.
    Never returns secret keys — only whether each env var is set."""
    return jsonify(billing_health_check())


@app.route('/api/billing/config', methods=['GET'])
def api_billing_config():
    """Public Stripe config the frontend needs (publishable key only).
    Safe to call without auth — pk_test_/pk_live_ is not secret."""
    return jsonify({
        'ok': True,
        'publishable_key': STRIPE_PUBLISHABLE_KEY,
    })


@app.route('/api/billing/checkout', methods=['POST'])
@limiter.limit("10 per hour", key_func=_rate_limit_key)
def api_billing_checkout():
    """Start a Stripe Checkout Session for a paid-plan upgrade.

    Body: {plan: 'pro' | 'studio'}
    Auth: Authorization: Bearer <access_token>

    Returns {ok: True, url} — frontend should window.location = url.
    The Supabase Edge Function handles the rest once payment completes.
    """
    user_info, err = _require_authed_user()
    if err:
        return err

    body = request.json or {}
    plan = (body.get('plan') or '').strip().lower()
    if plan not in ('pro', 'studio'):
        return jsonify({'ok': False, 'error': "plan moet 'pro' of 'studio' zijn"}), 400

    profile = user_info.get('profile') or {}
    stripe_customer_id = profile.get('stripe_customer_id') or None

    # Build redirect URLs from the request host so this works whether the
    # user is on localhost, a LAN IP, or eventually a packaged build with a
    # custom protocol. host_url ends with a slash already.
    base = request.host_url.rstrip('/')
    success_url = f"{base}/?billing=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base}/?billing=cancel"

    # Bij edge-function-modus heeft billing.py de JWT van de user nodig om
    # de Supabase Edge Function te autoriseren. In dev (lokale Stripe SDK)
    # wordt deze parameter genegeerd.
    _auth_header = request.headers.get('Authorization', '')
    access_token = _auth_header[7:].strip() if _auth_header.lower().startswith('bearer ') else None

    result = billing_start_checkout(
        user_id=user_info['user_id'],
        email=user_info['email'],
        plan=plan,
        success_url=success_url,
        cancel_url=cancel_url,
        stripe_customer_id=stripe_customer_id,
        access_token=access_token,
    )
    # SESSIE 35 — audit log
    _audit(
        'plan.checkout_started',
        user_id=user_info['user_id'],
        metadata={'plan': plan, 'ok': result.get('ok')},
    )
    return jsonify(result), (200 if result.get('ok') else 400)


@app.route('/api/billing/portal', methods=['POST'])
@limiter.limit("10 per hour", key_func=_rate_limit_key)
def api_billing_portal():
    """Open the Stripe Customer Portal so a paying user can manage their
    subscription (cancel, swap plan, update card, view invoices).

    Auth: Authorization: Bearer <access_token>
    No body required.

    Returns {ok: True, url} — frontend redirects there.
    """
    user_info, err = _require_authed_user()
    if err:
        return err

    profile = user_info.get('profile') or {}
    stripe_customer_id = profile.get('stripe_customer_id')
    if not stripe_customer_id:
        return jsonify({
            'ok': False,
            'error': 'Geen actief Stripe-abonnement gekoppeld aan deze account.'
        }), 400

    base = request.host_url.rstrip('/')
    return_url = f"{base}/?billing=portal-return"

    _auth_header = request.headers.get('Authorization', '')
    access_token = _auth_header[7:].strip() if _auth_header.lower().startswith('bearer ') else None

    result = billing_open_portal(
        stripe_customer_id=stripe_customer_id,
        return_url=return_url,
        access_token=access_token,
    )
    # SESSIE 35 — audit log
    _audit(
        'plan.portal_opened',
        user_id=user_info['user_id'],
        metadata={'ok': result.get('ok')},
    )
    return jsonify(result), (200 if result.get('ok') else 400)


@app.route('/api/billing/metrics', methods=['GET'])
def api_billing_metrics():
    """Fetch comprehensive Stripe metrics for dashboard display.

    Returns: {
        ok: bool,
        data: {
            mrr: float (in EUR),
            mrr_by_tier: {pro: float, studio: float},
            active_subscriptions: int,
            total_revenue: float (lifetime, in EUR),
            available_balance: float (in EUR cents, per Stripe),
            outstanding_invoices: int,
            churn_rate_30d: float (0–1),
            ltv_by_tier: {pro: float, studio: float},
            customer_count: int,
            subscription_stats: {
                pro_active: int,
                studio_active: int,
                pro_inactive: int,
                studio_inactive: int
            },
            last_updated: ISO 8601 timestamp
        }
    }

    Note: Stripe SDK must be configured. Returns error if not.
    This endpoint is read-only and can be called without auth for dashboard.
    """
    from billing import stripe as stripe_sdk, STRIPE_PRICE_ID_PRO, STRIPE_PRICE_ID_STUDIO

    if not stripe_sdk:
        return jsonify({
            'ok': False,
            'error': 'Stripe not configured. Check STRIPE_SECRET_KEY in .env'
        }), 503

    try:
        # Fetch all subscriptions
        subscriptions = []
        sub_cursor = None
        while True:
            sub_batch = stripe_sdk.Subscription.list(
                limit=100,
                starting_after=sub_cursor,
                expand=['data.customer']
            )
            subscriptions.extend(sub_batch['data'])
            if not sub_batch.get('has_more'):
                break
            sub_cursor = sub_batch['data'][-1]['id']

        # Calculate MRR and subscription stats
        mrr = 0.0
        mrr_by_tier = {'pro': 0.0, 'studio': 0.0}
        active_subs_count = 0
        subscription_stats = {
            'pro_active': 0,
            'studio_active': 0,
            'pro_inactive': 0,
            'studio_inactive': 0
        }

        for sub in subscriptions:
            price_id = None
            if sub.get('items') and sub['items'].get('data'):
                price_id = sub['items']['data'][0].get('price', {}).get('id')

            # Determine tier and status
            tier = None
            if price_id == STRIPE_PRICE_ID_PRO:
                tier = 'pro'
            elif price_id == STRIPE_PRICE_ID_STUDIO:
                tier = 'studio'
            else:
                continue  # Unknown tier, skip

            is_active = sub['status'] in ('active', 'trialing')

            if is_active:
                active_subs_count += 1
                subscription_stats[f'{tier}_active'] += 1

                # Add to MRR (assuming monthly billing; adjust if needed)
                amount = sub['items']['data'][0].get('price', {}).get('unit_amount', 0)
                if amount:
                    mrr += (amount / 100.0)  # Convert cents to EUR
                    mrr_by_tier[tier] += (amount / 100.0)
            else:
                subscription_stats[f'{tier}_inactive'] += 1

        # Fetch all charges for total revenue
        total_revenue = 0.0
        charges_list = []
        charge_cursor = None
        while True:
            charge_batch = stripe_sdk.Charge.list(
                limit=100,
                starting_after=charge_cursor
            )
            charges_list.extend(charge_batch['data'])
            if not charge_batch.get('has_more'):
                break
            charge_cursor = charge_batch['data'][-1]['id']

        for charge in charges_list:
            if charge.get('paid') and not charge.get('refunded'):
                total_revenue += (charge.get('amount', 0) / 100.0)  # Convert to EUR

        # Fetch account balance for available payout
        account = stripe_sdk.Balance.retrieve()
        available_balance = 0.0
        if account.get('available'):
            for bal in account['available']:
                if bal.get('currency') == 'eur':
                    available_balance += (bal.get('amount', 0) / 100.0)

        # Fetch outstanding invoices
        outstanding_invoices = 0
        invoice_cursor = None
        while True:
            invoice_batch = stripe_sdk.Invoice.list(
                limit=100,
                status='open',
                starting_after=invoice_cursor
            )
            outstanding_invoices += len(invoice_batch['data'])
            if not invoice_batch.get('has_more'):
                break
            invoice_cursor = invoice_batch['data'][-1]['id']

        # Calculate 30-day churn (simplified: inactive / (active + inactive))
        total_subs = (subscription_stats['pro_active'] + subscription_stats['studio_active'] +
                      subscription_stats['pro_inactive'] + subscription_stats['studio_inactive'])
        total_inactive = subscription_stats['pro_inactive'] + subscription_stats['studio_inactive']
        churn_rate = (total_inactive / total_subs) if total_subs > 0 else 0.0

        # Estimate LTV by tier (simplified: assumes 5-month average lifetime at current churn)
        # LTV = (monthly_price) * (1 / churn_rate) if churn_rate > 0, else 12 months
        pro_ltv = 21.99 * (1 / churn_rate) if churn_rate > 0 else 21.99 * 12
        studio_ltv = 200.0 * (1 / churn_rate) if churn_rate > 0 else 200.0 * 12
        ltv_by_tier = {'pro': round(pro_ltv, 2), 'studio': round(studio_ltv, 2)}

        # Fetch total customer count
        customers = stripe_sdk.Customer.list(limit=1)
        customer_count = customers['total_count']

        return jsonify({
            'ok': True,
            'data': {
                'mrr': round(mrr, 2),
                'mrr_by_tier': {
                    'pro': round(mrr_by_tier['pro'], 2),
                    'studio': round(mrr_by_tier['studio'], 2)
                },
                'active_subscriptions': active_subs_count,
                'total_revenue': round(total_revenue, 2),
                'available_balance': round(available_balance, 2),
                'outstanding_invoices': outstanding_invoices,
                'churn_rate_30d': round(churn_rate, 4),
                'ltv_by_tier': ltv_by_tier,
                'customer_count': customer_count,
                'subscription_stats': subscription_stats,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
        }), 200

    except Exception as e:
        log.error(f'Error fetching Stripe metrics: {e}')
        return jsonify({
            'ok': False,
            'error': f'Failed to fetch Stripe metrics: {str(e)}'
        }), 500


@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(_load_settings())


@app.route('/api/settings', methods=['POST'])
def save_settings():
    data = request.json or {}
    _save_settings(data)
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Watch folder — Pro-tier feature, end-to-end wired in SESSIE 17 (2026-05-10).
#
# Auth required on every endpoint. POST also enforces the plan-gate
# (only `pro` and `studio` may activate a watch folder) and persists the
# owner's user_id, which the background daemon uses to look up plan/quota
# at every tick.
#
# The actual polling lives in watch_folder.py — see that file for the
# state-blob shape, dedupe strategy, and concurrency model.
# ---------------------------------------------------------------------------

_WATCH_PAID_PLANS = ('pro', 'studio')


@app.route('/api/watch-folder', methods=['GET'])
def get_watch_folder():
    """Return the watch-folder config. Auth required so we never leak
    the configured path back to an unauthenticated session.

    Backwards-compat: pre-SESSIE-17 callers expect `{path, ...}`; this
    shape is preserved (with the daemon-specific fields layered on top)."""
    user_info, err = _require_authed_user()
    if err:
        return err
    cfg = watch_folder.get_config()
    # Only expose the path/active to the user that owns it. Different user
    # on the same machine → return as if unconfigured. (One-per-machine in
    # practice, but defensive against multi-account use.)
    if cfg.get('user_id') and cfg.get('user_id') != user_info['user_id']:
        return jsonify({'path': None, 'active': False, 'foreign_owner': True})
    return jsonify({
        'path':       cfg.get('path'),
        'active':     bool(cfg.get('active')),
        'last_tick':  cfg.get('last_tick'),
        'last_error': cfg.get('last_error'),
        'stats':      cfg.get('stats') or {},
        'updated':    cfg.get('updated'),
    })


@app.route('/api/watch-folder', methods=['POST'])
def save_watch_folder():
    """Configure or clear the watch folder.

    Body: { path: "<absolute folder>" | "", active: bool }
    Auth: Bearer token. Plan: pro | studio (Free returns 402).

    `active=true` + non-empty `path` starts the daemon polling that path.
    `active=false` (or empty path) pauses the daemon but keeps the seen
    cache so re-activating doesn't reprocess existing files.
    """
    user_info, err = _require_authed_user()
    if err:
        return err

    # Plan-gate — same shape as the upload quota gate so the frontend
    # can re-use its 402 handling to surface the upgrade modal.
    snap = _get_or_refresh_profile(user_info['user_id'], access_token=user_info.get('access_token'))
    if not snap.get('ok'):
        return jsonify({'ok': False, 'error': snap.get('error', 'profile read failed')}), 500
    if (snap.get('plan') or 'free').lower() not in _WATCH_PAID_PLANS:
        return _quota_block_response({
            **snap,
            'error':   'quota_exceeded',
            'trigger': 'watch_folder',
        })

    data = request.get_json(silent=True) or {}
    raw_path = (data.get('path') or '').strip()
    active   = bool(data.get('active', True)) if raw_path else False

    if raw_path:
        if not os.path.isabs(raw_path):
            return jsonify({'ok': False, 'error': 'Path must be absolute (start with /).'}), 400
        if not os.path.exists(raw_path):
            return jsonify({'ok': False, 'error': f'Folder does not exist: {raw_path}'}), 404
        if not os.path.isdir(raw_path):
            return jsonify({'ok': False, 'error': f'Path is not a folder: {raw_path}'}), 400
        # Sanity: don't watch UPLOAD_DIR / OUTPUT_DIR — that'd loop on our own files.
        for forbidden in (UPLOAD_DIR, OUTPUT_DIR):
            try:
                if os.path.samefile(raw_path, forbidden):
                    return jsonify({
                        'ok': False,
                        'error': "Pick a different folder — that's where Omni DJ writes its own output.",
                    }), 400
            except OSError:
                pass

    cfg = watch_folder.save_config(
        path=raw_path or None,
        active=active,
        user_id=user_info['user_id'],
    )
    log.info("Watch folder configured by %s: path=%s active=%s",
             user_info['user_id'], cfg.get('path'), cfg.get('active'))
    return jsonify({
        'success':    True,
        'path':       cfg.get('path'),
        'active':     bool(cfg.get('active')),
        'last_tick':  cfg.get('last_tick'),
        'last_error': cfg.get('last_error'),
        'stats':      cfg.get('stats') or {},
        'updated':    cfg.get('updated'),
    })


@app.route('/api/watch-folder/status', methods=['GET'])
def watch_folder_status():
    """Light-weight status feed for the Settings panel's polling UI.
    Returns last-tick timestamp, in-flight filename, queue length,
    counters, and the most recent error (if any). Auth required."""
    user_info, err = _require_authed_user()
    if err:
        return err
    status = watch_folder.get_status()
    # Hide foreign owner's stats so we don't leak across users.
    if status.get('user_id') and status.get('user_id') != user_info['user_id']:
        return jsonify({
            'path': None, 'active': False, 'foreign_owner': True,
            'stats': {}, 'queue': [], 'queue_count': 0,
            'in_flight': None, 'last_tick': None, 'last_error': None,
            'tick_seconds': status.get('tick_seconds'),
        })
    return jsonify(status)


@app.route('/api/watch-folder/reset-seen', methods=['POST'])
def watch_folder_reset_seen():
    """Clear the seen-files cache so the daemon will re-process every
    file currently in the watched folder. Auth + plan gate (Pro/Studio)."""
    user_info, err = _require_authed_user()
    if err:
        return err
    snap = _get_or_refresh_profile(user_info['user_id'], access_token=user_info.get('access_token'))
    if not snap.get('ok'):
        return jsonify({'ok': False, 'error': snap.get('error', 'profile read failed')}), 500
    if (snap.get('plan') or 'free').lower() not in _WATCH_PAID_PLANS:
        return _quota_block_response({**snap, 'error': 'quota_exceeded',
                                      'trigger': 'watch_folder'})
    cfg = watch_folder.reset_seen()
    return jsonify({'ok': True, 'stats': cfg.get('stats') or {}})


# SESSIE 21 — Brand Stack v1
# ==========================
# The brand_kit.json blob is the source of truth for an artist's persistent
# visual identity. Schema (all keys optional, additive over time):
#   fonts:           [{id, family, weight, ext, path, uploaded}]
#   palette:         [{name, hex}]               (3-5 brand colours)
#   logo:            {path, ext, corner, opacity, size_pct}
#   caption_presets: [{id, name, font_id, color, size, anim, bg, position}]
#   handle:          string                       (e.g. "@sjuulsmits")
#   tagline:         string                       (closer line)
#   bpm_stamp:       {enabled, corner, font_id}   (v2 — DJ BPM/Key overlay)
#   end_card:        {enabled, duration_s, text}  (v2 — branded outro)
#   updated:         epoch seconds
def _brand_kit_defaults():
    """Return the seed fields a fresh brand_kit gets when first touched.
    Keys mirror the schema comment above. We don't write this to disk
    eagerly — it's merged in on first read so old kits keep working."""
    return {
        'fonts': [],
        'palette': [
            {'name': 'Amber',   'hex': '#e8b766'},
            {'name': 'Copper',  'hex': '#cf6b58'},
            {'name': 'Sage',    'hex': '#7fb685'},
            {'name': 'Sky',     'hex': '#7aa6e0'},
            {'name': 'Paper',   'hex': '#f6efe2'},
        ],
        'logo': None,
        'caption_presets': [],
        'handle': '',
        'tagline': '',
        # SESSIE 22 — BPM/Key corner stamp config. Disabled by default;
        # turn on via Brand Stack toggle.
        'bpm_stamp': {
            'enabled': False,
            'corner':  'bl',       # tl / tr / bl / br
            'font_id': None,       # falls back to system sans
            'color':   '#ffffff',
            'format':  'bpm_key',  # 'bpm' | 'key' | 'bpm_key'
        },
    }


# ---------------------------------------------------------------------------
# SESSIE 74 - Slice 2 FASE 4: brand-kit + assets per workspace.
# `_active_brand_ws()` bepaalt (per-request gecached) de actieve workspace voor
# de huidige brand-request; daarmee laden/schrijven de brand-kit-endpoints een
# per-workspace bestand i.p.v. het globale. Logo/watermark gaan naar per-workspace
# mappen (lost de vaste-bestandsnaam-clobber op). Zonder workspace -> globaal
# gedrag (geen regressie). De cutter blijft globaal/job-map lezen (fase 2b).
# ---------------------------------------------------------------------------
def _active_brand_ws():
    """De actieve workspace voor de huidige brand-request (per-request gecached op
    flask.g). None bij geen auth/workspace/Supabase -> globale fallback. Faalt stil."""
    try:
        if getattr(g, '_brand_ws_resolved', False):
            return getattr(g, '_brand_ws_id', None)
    except Exception:
        return None
    ws = None
    try:
        user_info, err = _require_authed_user()
        if not err and user_info:
            sb = _user_supabase(user_info.get('access_token'))
            if sb is not None:
                ws, _w = current_workspace_id(user_info, required=False)
    except Exception:
        ws = None
    try:
        g._brand_ws_resolved = True
        g._brand_ws_id = ws
    except Exception:
        pass
    return ws


def _ws_brand_kit_path(ws):
    return os.path.join(DATA_DIR, 'workspaces', str(ws), 'brand_kit.json') if ws else BRAND_KIT_PATH


def _brand_asset_dirs(ws):
    """Dict met logo/fonts/watermark-mappen voor deze workspace (of globaal als ws
    None). Maakt de mappen aan. NB: fonts blijven praktisch globaal-compatibel via
    uuid-namen; logo/watermark zijn juist per-workspace om clobber te voorkomen."""
    if ws:
        base = os.path.join(DATA_DIR, 'workspaces', str(ws), 'brand_kit')
        d = {'logo': os.path.join(base, 'logo'),
             'fonts': os.path.join(base, 'fonts'),
             'watermark': os.path.join(base, 'watermark')}
    else:
        d = {'logo': BRAND_LOGO_DIR, 'fonts': BRAND_FONTS_DIR, 'watermark': BRAND_WATERMARK_DIR}
    for p in d.values():
        try:
            os.makedirs(p, exist_ok=True)
        except Exception:
            pass
    return d


def _load_brand_kit():
    """Read + back-fill defaults so callers can rely on the schema. SESSIE 74 fase 4:
    per-workspace wanneer de brand-request een workspace heeft (eigen cache, eenmalig
    geseed uit het globale bestand); anders globaal (geen regressie)."""
    ws = _active_brand_ws()
    path = _ws_brand_kit_path(ws)
    if ws and not os.path.exists(path):
        kit = _load_json_blob(BRAND_KIT_PATH, {})   # seed uit globaal
    else:
        kit = _load_json_blob(path, {})
    base = _brand_kit_defaults()
    for k, v in base.items():
        if k not in kit:
            kit[k] = v
    return kit


@app.route('/api/brand-kit', methods=['GET'])
def get_brand_kit():
    # SESSIE 74 - Slice 2 fase 2a: geef de per-workspace brand-kit uit dj_profiles
    # terug als die er is; anders het globale bestand (backward compatible voor
    # unauth/boot-callers). De cutter blijft het globale bestand lezen (fase 2b).
    sb, ws_id = _brand_ws_ctx()
    if sb is not None and ws_id:
        try:
            res = (sb.table('dj_profiles').select('profile')
                     .eq('workspace_id', ws_id).limit(1).execute())
            rows = getattr(res, 'data', None) or []
            bk = ((rows[0].get('profile') if rows else None) or {}).get('brand_kit')
            if isinstance(bk, dict) and bk:
                base = _brand_kit_defaults()
                for k, v in base.items():
                    bk.setdefault(k, v)
                return jsonify(bk)
        except Exception as e:
            log.warning("get_brand_kit workspace-read mislukt: %s", e)
    return jsonify(_load_brand_kit())


@app.route('/api/brand-kit', methods=['POST'])
def save_brand_kit():
    data = request.json or {}
    # Merge into existing kit so partial saves don't blow away other fields
    kit = _load_brand_kit()
    kit.update({k: v for k, v in data.items() if v is not None})
    kit['updated'] = time.time()
    _save_brand_kit(kit)
    log.info("Brand kit updated: keys=%s", list(data.keys()))
    return jsonify({'success': True, **kit})


# ---------------------------------------------------------------------------
# SESSIE 74 - Slice 2 (Brand bron-migratie), FASE 1: per-workspace brand-profiel.
# Additief en niet-destructief: nieuwe routes NAAST de bestaande /api/brand-kit*.
# dj_profiles (Supabase) wordt de bron van waarheid per workspace, gelezen/
# geschreven via de anon+user-JWT-client (_user_supabase) zodat RLS de grens is.
# brand_kit.json + alle /api/brand-kit* blijven in fase 1 ONGEMOEID. Het canonieke
# profiel embed het bestaande brand_kit-blok onder de sleutel 'brand_kit' zodat de
# render-shape verliesvrij meegaat naar fase 2. Zie PLAN-SLICE2-BRAND-MIGRATION.
# ---------------------------------------------------------------------------
_BRAND_PROFILE_SCHEMA_VERSION = 1


def _brand_profile_defaults():
    """Lege canonieke profiel-structuur (moat-schema + ingebed brand_kit)."""
    return {
        'schema_version': _BRAND_PROFILE_SCHEMA_VERSION,
        'artist_name': '',
        'alias': '',
        'visual': {
            'logo': None, 'logo_position': 'bottom_right', 'logo_size': '8%',
            'primary_color': '', 'secondary_color': '', 'accent_color': '',
        },
        'typography': {'title_font': '', 'caption_font': '', 'caption_style': 'two_word_punch'},
        'lower_third': {'enabled': False, 'template': 'name_below_logo', 'duration': 3.0},
        'cta': {'style': 'out_now', 'spotify_link': '', 'beatport_link': '', 'show_in_last_seconds': 2.5},
        'hashtags': {'tiktok': [], 'instagram': [], 'youtube_shorts': []},
        'caption_voice': {'tone': 'hyped', 'use_emojis': True, 'max_length_chars': 80},
        'brand_kit': {},
    }


def _seed_brand_profile_from_kit():
    """Bouw een canoniek profiel uit het bestaande globale brand_kit.json.
    Best-effort mapping van overlappende velden; het volledige brand_kit-blok gaat
    verliesvrij onder 'brand_kit'. Nul-impact als er nog geen kit is."""
    prof = _brand_profile_defaults()
    try:
        kit = _load_brand_kit() or {}
    except Exception:
        kit = {}
    prof['brand_kit'] = kit
    try:
        if kit.get('handle'):
            prof['alias'] = kit.get('handle') or ''
        pal = kit.get('palette') or []
        if len(pal) >= 1 and (pal[0] or {}).get('hex'):
            prof['visual']['primary_color'] = pal[0]['hex']
        if len(pal) >= 2 and (pal[1] or {}).get('hex'):
            prof['visual']['secondary_color'] = pal[1]['hex']
        if len(pal) >= 3 and (pal[2] or {}).get('hex'):
            prof['visual']['accent_color'] = pal[2]['hex']
        logo = kit.get('logo')
        if isinstance(logo, dict):
            prof['visual']['logo'] = logo.get('path')
        elif logo:
            prof['visual']['logo'] = logo
        fonts = kit.get('fonts') or []
        if fonts and fonts[0].get('family'):
            prof['typography']['title_font'] = fonts[0]['family']
            prof['typography']['caption_font'] = fonts[0]['family']
    except Exception:
        pass
    return prof


def _merge_brand_profile(base, incoming):
    """Merge incoming op base. Bekende sub-objecten worden 1 niveau diep gemerged;
    None-waarden worden genegeerd zodat partiele saves niets wegvegen."""
    out = dict(base or {})
    for k, v in (incoming or {}).items():
        if v is None:
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            merged = dict(out[k])
            merged.update({kk: vv for kk, vv in v.items() if vv is not None})
            out[k] = merged
        else:
            out[k] = v
    out['schema_version'] = _BRAND_PROFILE_SCHEMA_VERSION
    return out


@app.route('/api/brand/profile', methods=['GET'])
def get_brand_profile():
    """Lees het brand-profiel van de actieve workspace (RLS-scoped). Bestaat er nog
    geen dj_profiles-rij, dan eenmalig SEEDEN uit het globale brand_kit.json en
    upserten. Degradeert (legacy) naar het globale brand_kit als er geen workspace/
    Supabase is, zodat de frontend altijd iets bruikbaars krijgt."""
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    ws_id, _werr = current_workspace_id(user_info, required=False)
    if sb is None or not ws_id:
        prof = _seed_brand_profile_from_kit()
        return jsonify({'ok': True, 'workspace_id': ws_id, 'source': 'legacy', 'profile': prof})
    try:
        res = (sb.table('dj_profiles').select('id,profile,updated_at')
                 .eq('workspace_id', ws_id).limit(1).execute())
        rows = getattr(res, 'data', None) or []
        if rows:
            prof = rows[0].get('profile') or _brand_profile_defaults()
            return jsonify({'ok': True, 'workspace_id': ws_id, 'source': 'supabase', 'profile': prof})
        seeded = _seed_brand_profile_from_kit()
        try:
            sb.table('dj_profiles').upsert(
                {'workspace_id': ws_id, 'profile': seeded},
                on_conflict='workspace_id').execute()
        except Exception as e:
            log.warning("brand-profile seed-upsert mislukt: %s", e)
        return jsonify({'ok': True, 'workspace_id': ws_id, 'source': 'seeded', 'profile': seeded})
    except Exception as e:
        log.warning("get_brand_profile mislukt: %s", e)
        return jsonify({'ok': False, 'error': 'Kon brand-profiel niet laden'}), 502


@app.route('/api/brand/profile', methods=['PUT'])
def put_brand_profile():
    """Schrijf (merge) het brand-profiel van de actieve workspace via de user-JWT
    (RLS is de grens). Niet-destructief t.o.v. brand_kit.json in fase 1."""
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    ws_id, werr = current_workspace_id(user_info, required=True)
    if werr:
        return werr
    if sb is None:
        return jsonify({'ok': False, 'error': 'Supabase niet geconfigureerd'}), 503
    body = request.get_json(silent=True) or {}
    incoming = body.get('profile')
    if not isinstance(incoming, dict):
        return jsonify({'ok': False, 'error': 'profile-object ontbreekt'}), 400
    try:
        res = (sb.table('dj_profiles').select('profile')
                 .eq('workspace_id', ws_id).limit(1).execute())
        rows = getattr(res, 'data', None) or []
        base = (rows[0].get('profile') if rows else None) or _seed_brand_profile_from_kit()
    except Exception:
        base = _seed_brand_profile_from_kit()
    merged = _merge_brand_profile(base, incoming)
    try:
        sb.table('dj_profiles').upsert(
            {'workspace_id': ws_id, 'profile': merged},
            on_conflict='workspace_id').execute()
    except Exception as e:
        log.warning("put_brand_profile upsert mislukt: %s", e)
        return jsonify({'ok': False, 'error': 'Kon brand-profiel niet opslaan'}), 502
    return jsonify({'ok': True, 'workspace_id': ws_id, 'profile': merged})


# ---------------------------------------------------------------------------
# SESSIE 78 - per-workspace settings (editor/export-defaults + crowd-inmix).
#
# Opslag: dj_profiles.profile.settings (een JSONB sub-sleutel NAAST brand_kit/
# artist_name). Bewust GEEN aparte tabel/migratie: dj_profiles + zijn RLS
# (008/010) zijn al live op main en workspace==dj_profile is hier 1-op-1, dus
# een sub-sleutel landt meteen autonoom zonder schema-checkpoint. Een dedicated
# `workspace_settings`-tabel blijft een optie als settings later zwaarder worden.
#
# De settings-PUT raakt ALLEEN de 'settings'-sleutel en behoudt de rest van het
# profiel; de brand-PUT (_merge_brand_profile) behoudt op zijn beurt 'settings'
# (hij merget per bekende sub-sleutel), dus ze leven naast elkaar zonder clobber.
# Uitgelogd / geen workspace -> de frontend blijft op localStorage draaien.
# ---------------------------------------------------------------------------
def _merge_workspace_settings(base, incoming):
    """Merge incoming op base, 2 niveaus diep (editor/export -> hun sub-objecten
    zoals inmix). None-waarden negeren zodat partiele saves niets wegvegen."""
    out = dict(base or {})
    for k, v in (incoming or {}).items():
        if v is None:
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            merged = dict(out[k])
            for kk, vv in v.items():
                if vv is None:
                    continue
                if isinstance(vv, dict) and isinstance(merged.get(kk), dict):
                    inner = dict(merged[kk])
                    inner.update({a: b for a, b in vv.items() if b is not None})
                    merged[kk] = inner
                else:
                    merged[kk] = vv
            out[k] = merged
        else:
            out[k] = v
    return out


@app.route('/api/workspace/settings', methods=['GET'])
def get_workspace_settings():
    """Lees de per-workspace settings (RLS-scoped). Leeg object als er nog niets
    is opgeslagen of als er (nog) geen workspace/Supabase is -> frontend valt dan
    terug op zijn localStorage-defaults."""
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    ws_id, _werr = current_workspace_id(user_info, required=False)
    if sb is None or not ws_id:
        return jsonify({'ok': True, 'workspace_id': ws_id, 'source': 'none', 'settings': {}})
    try:
        res = (sb.table('dj_profiles').select('profile')
                 .eq('workspace_id', ws_id).limit(1).execute())
        rows = getattr(res, 'data', None) or []
        prof = (rows[0].get('profile') if rows else None) or {}
        settings = prof.get('settings') if isinstance(prof, dict) else None
        return jsonify({'ok': True, 'workspace_id': ws_id, 'source': 'supabase',
                        'settings': settings or {}})
    except Exception as e:
        log.warning("get_workspace_settings mislukt: %s", e)
        return jsonify({'ok': False, 'error': 'Kon settings niet laden'}), 502


@app.route('/api/workspace/settings', methods=['PUT'])
def put_workspace_settings():
    """Schrijf (merge) de per-workspace settings via de user-JWT (RLS = grens).
    Raakt alleen profile.settings; brand-velden blijven intact."""
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    ws_id, werr = current_workspace_id(user_info, required=True)
    if werr:
        return werr
    if sb is None:
        return jsonify({'ok': False, 'error': 'Supabase niet geconfigureerd'}), 503
    body = request.get_json(silent=True) or {}
    incoming = body.get('settings')
    if not isinstance(incoming, dict):
        return jsonify({'ok': False, 'error': 'settings-object ontbreekt'}), 400
    try:
        res = (sb.table('dj_profiles').select('profile')
                 .eq('workspace_id', ws_id).limit(1).execute())
        rows = getattr(res, 'data', None) or []
        base_profile = (rows[0].get('profile') if rows else None) or _seed_brand_profile_from_kit()
    except Exception:
        base_profile = _seed_brand_profile_from_kit()
    if not isinstance(base_profile, dict):
        base_profile = {}
    base_settings = base_profile.get('settings') or {}
    merged_settings = _merge_workspace_settings(base_settings, incoming)
    new_profile = dict(base_profile)
    new_profile['settings'] = merged_settings
    try:
        sb.table('dj_profiles').upsert(
            {'workspace_id': ws_id, 'profile': new_profile},
            on_conflict='workspace_id').execute()
    except Exception as e:
        log.warning("put_workspace_settings upsert mislukt: %s", e)
        return jsonify({'ok': False, 'error': 'Kon settings niet opslaan'}), 502
    return jsonify({'ok': True, 'workspace_id': ws_id, 'settings': merged_settings})


# ---------------------------------------------------------------------------
# SESSIE 74 - Slice 2 FASE 2a: brand-kit metadata per workspace (mirror).
# De cutter (cutter.py `_load_brand_assets_for_job`) leest het GLOBALE
# brand_kit.json ZELF van schijf. Daarom blijft dat bestand in fase 2a exact
# zoals het is (nul export-regressie). Wat fase 2a wel doet: elke brand-kit-save
# mirrort de metadata naar `dj_profiles.profile.brand_kit` van de actieve
# workspace, en GET /api/brand-kit geeft die per-workspace versie terug als die
# bestaat. Het per-workspace LOKALE cache-bestand + de cutter workspace-bewust
# maken horen bij elkaar en schuiven naar fase 2b (raakt de render). Zie
# PLAN-SLICE2-BRAND-MIGRATION.
# ---------------------------------------------------------------------------
def _brand_ws_ctx():
    """(sb, ws_id) voor de huidige brand-request, of (None, None) als er geen
    auth/workspace/Supabase is. Soft: faalt nooit, degradeert naar het globale
    gedrag zodat unauth-callers (boot vóór login) blijven werken."""
    try:
        user_info, err = _require_authed_user()
        if err or not user_info:
            return None, None
        sb = _user_supabase(user_info.get('access_token'))
        ws_id, _werr = current_workspace_id(user_info, required=False)
        if sb is None or not ws_id:
            return None, None
        return sb, ws_id
    except Exception:
        return None, None


def _mirror_kit_to_workspace(kit):
    """Best-effort: schrijf de brand-kit metadata naar dj_profiles.profile.brand_kit
    van de actieve workspace (RLS via user-JWT). Raakt het globale bestand niet."""
    sb, ws_id = _brand_ws_ctx()
    if sb is None or not ws_id:
        return
    # SESSIE 74 - fase 2b: schrijf ook een lokale per-workspace cache zodat de
    # render-thread (geen auth/JWT) de juiste brand kan materialiseren in de
    # job-map. Onafhankelijk van de Supabase-mirror.
    try:
        cp = _workspace_brand_cache_path(ws_id)
        if cp:
            os.makedirs(os.path.dirname(cp), exist_ok=True)
            _save_json_blob(cp, kit)
    except Exception as e:
        log.warning("brand-kit lokale workspace-cache schrijven mislukt: %s", e)
    try:
        res = (sb.table('dj_profiles').select('profile')
                 .eq('workspace_id', ws_id).limit(1).execute())
        rows = getattr(res, 'data', None) or []
        prof = (rows[0].get('profile') if rows else None) or _seed_brand_profile_from_kit()
        prof = dict(prof)
        prof['brand_kit'] = kit
        sb.table('dj_profiles').upsert(
            {'workspace_id': ws_id, 'profile': prof},
            on_conflict='workspace_id').execute()
    except Exception as e:
        log.warning("brand-kit mirror naar workspace mislukt: %s", e)


def _save_brand_kit(kit):
    """Sla de brand-kit op. SESSIE 74 fase 4: met actieve workspace schrijven we
    ALLEEN de per-workspace cache + Supabase-mirror (via _mirror_kit_to_workspace);
    het globale bestand blijft een stabiele default/fallback voor de cutter (oude/
    ongetagde jobs). Zonder workspace schrijven we het globale bestand."""
    if not _active_brand_ws():
        _save_json_blob(BRAND_KIT_PATH, kit)
    _mirror_kit_to_workspace(kit)


# SESSIE 74 - Slice 2 fase 2b: per-workspace brand in de render.
def _workspace_brand_cache_path(ws_id):
    """Lokaal per-workspace brand_kit cache-pad (door de render-thread leesbaar
    zonder Supabase/JWT). None als ws_id leeg."""
    if not ws_id:
        return None
    return os.path.join(DATA_DIR, 'workspaces', str(ws_id), 'brand_kit.json')


def _materialize_job_brand(job_id, target_dir):
    """Kopieer de per-workspace brand-cache van de job naar target_dir/brand_kit.json
    zodat de cutter (die output_dir eerst leest) de juiste brand bakt. Best-effort
    en no-op zonder workspace/cache -> de cutter valt terug op het globale bestand
    (geen regressie)."""
    try:
        if not target_dir:
            return
        job = None
        with jobs_lock:
            job = jobs.get(job_id)
        if job is None:
            job = _load_job_snapshot(job_id)
        ws_id = (job or {}).get('workspace_id')
        src = _workspace_brand_cache_path(ws_id)
        if not src or not os.path.exists(src):
            return
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy2(src, os.path.join(target_dir, 'brand_kit.json'))
    except Exception as e:
        log.warning("job-brand materialiseren mislukt voor %s: %s", job_id, e)


# ---------------------------------------------------------------------------
# SESSIE 74 - Slice 4 (Content Calendar / A3), FASE 4a: scheduled_posts per
# workspace via _user_supabase + current_workspace_id (RLS is de grens).
# Draft-store: publisht NIETS (status blijft draft/scheduled tot de latere
# Postiz-fase, buiten dit plan). Additief; raakt analyse/export/brand niet.
# ---------------------------------------------------------------------------
_CAL_STATUS = {'draft', 'scheduled', 'published', 'failed'}
_CAL_COLS = 'id,clip_id,caption,platforms,scheduled_for,status,created_at,updated_at'
_UUID_RE = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')


def _cal_clean_platforms(v):
    """Witte-lijst-vrije maar veilige normalisatie: strings, getrimd, gecapt."""
    if not isinstance(v, list):
        return []
    out = []
    for p in v:
        if isinstance(p, str) and p.strip():
            out.append(p.strip()[:32])
    return out[:10]


@app.route('/api/calendar/list', methods=['GET'])
def api_calendar_list():
    """Lijst geplande posts van de actieve workspace, RLS-scoped. Optioneel
    filteren op ?from=ISO&to=ISO (op scheduled_for)."""
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    ws_id, werr = current_workspace_id(user_info, required=True)
    if werr:
        return werr
    if sb is None:
        return jsonify({'ok': True, 'posts': []})
    try:
        q = sb.table('scheduled_posts').select(_CAL_COLS).eq('workspace_id', ws_id)
        frm = (request.args.get('from') or '').strip()
        to = (request.args.get('to') or '').strip()
        if frm:
            q = q.gte('scheduled_for', frm)
        if to:
            q = q.lte('scheduled_for', to)
        res = q.order('scheduled_for').execute()
        rows = getattr(res, 'data', None) or []
    except Exception as e:
        log.warning("api_calendar_list mislukt: %s", e)
        return jsonify({'ok': False, 'error': 'Kon calendar niet laden'}), 502
    return jsonify({'ok': True, 'workspace_id': ws_id, 'posts': rows})


@app.route('/api/calendar/schedule', methods=['POST'])
def api_calendar_schedule():
    """Maak een geplande post (draft) voor de actieve workspace via RLS."""
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    ws_id, werr = current_workspace_id(user_info, required=True)
    if werr:
        return werr
    if sb is None:
        return jsonify({'ok': False, 'error': 'Supabase niet geconfigureerd'}), 503
    body = request.get_json(silent=True) or {}
    scheduled_for = (body.get('scheduled_for') or '').strip()
    if not scheduled_for:
        return jsonify({'ok': False, 'error': 'scheduled_for ontbreekt'}), 400
    status = body.get('status') if body.get('status') in _CAL_STATUS else 'draft'
    row = {
        'workspace_id': ws_id,
        'caption': ((body.get('caption') or '')[:2000] or None),
        'platforms': _cal_clean_platforms(body.get('platforms')),
        'scheduled_for': scheduled_for,
        'status': status,
        'created_by': user_info.get('user_id'),
    }
    cid = body.get('clip_id')
    if isinstance(cid, str) and _UUID_RE.match(cid):
        row['clip_id'] = cid   # clips-tabel is nog leeg; meestal afwezig
    try:
        res = sb.table('scheduled_posts').insert(row).execute()
        rows = getattr(res, 'data', None) or []
    except Exception as e:
        log.warning("api_calendar_schedule mislukt: %s", e)
        return jsonify({'ok': False, 'error': 'Kon post niet plannen'}), 502
    return jsonify({'ok': True, 'post': (rows[0] if rows else None)})


@app.route('/api/calendar/update', methods=['PUT', 'POST'])
def api_calendar_update():
    """Wijzig een geplande post (caption/platforms/scheduled_for/status). RLS +
    expliciete workspace-filter zodat een vreemde id netjes 404 geeft."""
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    ws_id, werr = current_workspace_id(user_info, required=True)
    if werr:
        return werr
    if sb is None:
        return jsonify({'ok': False, 'error': 'Supabase niet geconfigureerd'}), 503
    body = request.get_json(silent=True) or {}
    pid = (body.get('id') or '').strip()
    if not pid:
        return jsonify({'ok': False, 'error': 'id ontbreekt'}), 400
    patch = {}
    if 'caption' in body:
        patch['caption'] = ((body.get('caption') or '')[:2000] or None)
    if 'platforms' in body:
        patch['platforms'] = _cal_clean_platforms(body.get('platforms'))
    if body.get('scheduled_for'):
        patch['scheduled_for'] = str(body.get('scheduled_for')).strip()
    if body.get('status') in _CAL_STATUS:
        patch['status'] = body.get('status')
    if not patch:
        return jsonify({'ok': False, 'error': 'niets te wijzigen'}), 400
    try:
        res = (sb.table('scheduled_posts').update(patch)
                 .eq('id', pid).eq('workspace_id', ws_id).execute())
        rows = getattr(res, 'data', None) or []
    except Exception as e:
        log.warning("api_calendar_update mislukt: %s", e)
        return jsonify({'ok': False, 'error': 'Kon post niet bijwerken'}), 502
    if not rows:
        return jsonify({'ok': False, 'error': 'Post niet gevonden'}), 404
    return jsonify({'ok': True, 'post': rows[0]})


@app.route('/api/calendar/delete', methods=['POST', 'DELETE'])
def api_calendar_delete():
    """Verwijder een geplande post (RLS + workspace-filter)."""
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    ws_id, werr = current_workspace_id(user_info, required=True)
    if werr:
        return werr
    if sb is None:
        return jsonify({'ok': False, 'error': 'Supabase niet geconfigureerd'}), 503
    body = request.get_json(silent=True) or {}
    pid = (body.get('id') or '').strip()
    if not pid:
        return jsonify({'ok': False, 'error': 'id ontbreekt'}), 400
    try:
        sb.table('scheduled_posts').delete().eq('id', pid).eq('workspace_id', ws_id).execute()
    except Exception as e:
        log.warning("api_calendar_delete mislukt: %s", e)
        return jsonify({'ok': False, 'error': 'Kon post niet verwijderen'}), 502
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# SESSIE 77 - Clip-metadata sync (A1/A3). Schrijft lichte clip-verwijzingen van
# een job naar de live clips-tabel zodat de Content Calendar een echte clip kan
# kiezen (clip_id-koppeling). ADDITIEF: raakt de analyse/cut/export-pipeline
# NIET aan. De media blijft lokaal; alleen metadata (een local_path-referentie,
# label, duur, set-naam) gaat naar Supabase, RLS-scoped via _user_supabase.
# Dedupe op (workspace_id, local_path) zodat herhaald syncen geen duplicaten
# geeft en bestaande clip_id-koppelingen intact blijven (geen delete/herinsert).
# ---------------------------------------------------------------------------
_CLIP_COLS = 'id,label,duration_s,source_set,kind,local_path,created_at'


def _clip_label_for(job, r, idx):
    """Beste leesbare naam voor een clip: per-job hernoeming eerst, dan
    custom_label/caption, anders 'Clip N'."""
    try:
        labels = job.get('clip_labels') or {}
        v = labels.get(str(idx))
        if v is None and idx is not None:
            v = labels.get(idx)
        if isinstance(v, str) and v.strip():
            return v.strip()[:200]
    except Exception:
        pass
    for k in ('custom_label', 'caption'):
        v = r.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()[:200]
    return ("Clip %s" % idx) if idx is not None else "Clip"


def _clip_rows_from_job(job):
    """Bouw lichte clips-tabel-rijen uit een job. local_path = '<job_id>/<bestand>'
    (stabiele, unieke dedupe-sleutel; verwijst naar de lokale cut). Geen media,
    alleen een referentie + metadata. Slaat clips zonder bestand over."""
    if not isinstance(job, dict):
        return []
    job_id = job.get('id')
    if not job_id:
        return []
    results = job.get('results') or job.get('clips') or []
    set_name = os.path.splitext(str(job.get('filename') or 'set'))[0][:200]
    kind = 'import' if job.get('imported') else 'clip'
    rows = []
    for r in results:
        if not isinstance(r, dict):
            continue
        files = r.get('files') or {}
        primary = (files.get('vertical') or files.get('landscape')
                   or files.get('square') or files.get('portrait45'))
        if not primary:
            continue
        idx = r.get('index')
        try:
            dur = float(r.get('duration') or 0.0)
            if dur <= 0:
                dur = max(0.0, float(r.get('end') or 0) - float(r.get('start') or 0))
        except Exception:
            dur = 0.0
        rows.append({
            'local_path': ("%s/%s" % (job_id, primary))[:500],
            'label': _clip_label_for(job, r, idx),
            'duration_s': round(dur, 3) if dur else None,
            'source_set': set_name,
            'kind': kind,
        })
    return rows


def _load_job_for_caller(job_id, user_id):
    """Haal een job (memory of snapshot) op en verifieer eigenaarschap. None als
    onbekend of niet van de caller -> de sync slaat 'm dan stil over."""
    job = None
    try:
        with jobs_lock:
            job = jobs.get(job_id)
    except Exception:
        job = None
    if job is None:
        try:
            job = _load_job_snapshot(job_id)
        except Exception:
            job = None
    if not isinstance(job, dict):
        return None
    owner = job.get('user_id')
    if owner and user_id and owner != user_id:
        return None
    return job


@app.route('/api/clips', methods=['GET'])
def api_clips_list():
    """Lijst clips van de actieve workspace (RLS-scoped) voor de Calendar-picker."""
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    ws_id, werr = current_workspace_id(user_info, required=True)
    if werr:
        return werr
    if sb is None:
        return jsonify({'ok': True, 'clips': []})
    try:
        res = (sb.table('clips').select(_CLIP_COLS)
                 .eq('workspace_id', ws_id)
                 .order('created_at', desc=True).limit(200).execute())
        rows = getattr(res, 'data', None) or []
    except Exception as e:
        log.warning("api_clips_list mislukt: %s", e)
        return jsonify({'ok': False, 'error': 'Kon clips niet laden'}), 502
    return jsonify({'ok': True, 'workspace_id': ws_id, 'clips': rows})


@app.route('/api/clips/sync', methods=['POST'])
def api_clips_sync():
    """Registreer de clips van een of meer jobs in de clips-tabel van de actieve
    workspace (dedupe op local_path). Retourneert de actuele workspace-cliplijst.
    ADDITIEF en best-effort: verstoort de pipeline nooit; alleen metadata."""
    user_info, err = _require_authed_user()
    if err:
        return err
    sb = _user_supabase(user_info.get('access_token'))
    ws_id, werr = current_workspace_id(user_info, required=True)
    if werr:
        return werr
    if sb is None:
        return jsonify({'ok': True, 'clips': [], 'inserted': 0})
    body = request.get_json(silent=True) or {}
    ids = body.get('job_ids')
    if not isinstance(ids, list):
        ids = []
    one = body.get('job_id')
    if isinstance(one, str) and one:
        ids = ids + [one]
    # Veilige, gecapte, unieke lijst van job-id-strings.
    seen_ids = []
    for j in ids:
        if isinstance(j, str) and j and j not in seen_ids:
            seen_ids.append(j)
        if len(seen_ids) >= 20:
            break
    uid = user_info.get('user_id')
    want = []
    for jid in seen_ids:
        job = _load_job_for_caller(jid, uid)
        if job is None:
            continue
        want.extend(_clip_rows_from_job(job))
    inserted = 0
    try:
        # Bestaande local_paths in deze workspace ophalen -> alleen nieuwe invoegen.
        existing = set()
        try:
            ex = (sb.table('clips').select('local_path')
                    .eq('workspace_id', ws_id).limit(1000).execute())
            for row in (getattr(ex, 'data', None) or []):
                lp = row.get('local_path')
                if lp:
                    existing.add(lp)
        except Exception as e:
            log.warning("clips dedupe-read mislukt: %s", e)
        to_insert = []
        seen_lp = set()
        for row in want:
            lp = row.get('local_path')
            if not lp or lp in existing or lp in seen_lp:
                continue
            seen_lp.add(lp)
            r = dict(row)
            r['workspace_id'] = ws_id
            to_insert.append(r)
        if to_insert:
            sb.table('clips').insert(to_insert).execute()
            inserted = len(to_insert)
    except Exception as e:
        log.warning("api_clips_sync insert mislukt: %s", e)
        # Niet fataal: probeer alsnog de huidige lijst terug te geven.
    try:
        res = (sb.table('clips').select(_CLIP_COLS)
                 .eq('workspace_id', ws_id)
                 .order('created_at', desc=True).limit(200).execute())
        rows = getattr(res, 'data', None) or []
    except Exception as e:
        log.warning("api_clips_sync list mislukt: %s", e)
        rows = []
    return jsonify({'ok': True, 'workspace_id': ws_id, 'clips': rows, 'inserted': inserted})


# ---------------------------------------------------------------------------
# SESSIE 77 - Spoor D: video + audio sync. Additieve, optionele tweede ingang op
# de Analyse-page. Matcht een losse camera-video tegen een schone audio-opname
# (audio_sync.py), muxt de schone audio onder het beeld (camera-audio blijft als
# 2e spoor) en levert EEN gewoon videobestand op dat daarna de BESTAANDE analyse-
# pipeline in kan. Raakt analyzer.py/cutter.py NIET aan. Lokaal + workspace-
# scoped; inputs gevalideerd met _path_within_home (S2), net als upload-local.
# ---------------------------------------------------------------------------
_SYNC_VIDEO_EXT = {'.mp4', '.mov', '.m4v', '.webm', '.mkv'}
_SYNC_AUDIO_EXT = {'.wav', '.mp3', '.m4a', '.aac', '.flac', '.aif', '.aiff'}


@app.route('/api/sync-import', methods=['POST'])
def api_sync_import():
    """Sync een losse camera-video met een schone audio-opname en mux ze.
    Retourneert metrics (offset/drift/confidence/warnings) + het lokale pad van
    het gemuxede bestand; de frontend voert dat pad daarna in de bestaande
    /api/upload-local-flow voor de normale drop-analyse."""
    user_info, err = _require_authed_user()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    video_path = (body.get('video_path') or '').strip()
    audio_path = (body.get('audio_path') or '').strip()
    if not video_path or not audio_path:
        return jsonify({'ok': False, 'error': 'video_path and audio_path are required'}), 400
    # S2: beide inputs moeten binnen de home-map vallen (zelfde regel als upload-local).
    if not _path_within_home(video_path) or not _path_within_home(audio_path):
        return jsonify({'ok': False, 'error': 'File outside your home folder is not allowed'}), 403
    vp = os.path.realpath(os.path.expanduser(video_path))
    ap = os.path.realpath(os.path.expanduser(audio_path))
    if not os.path.isfile(vp):
        return jsonify({'ok': False, 'error': 'video does not exist'}), 404
    if not os.path.isfile(ap):
        return jsonify({'ok': False, 'error': 'audio does not exist'}), 404
    if os.path.splitext(vp)[1].lower() not in _SYNC_VIDEO_EXT:
        return jsonify({'ok': False, 'error': 'video format not supported'}), 415
    if os.path.splitext(ap)[1].lower() not in _SYNC_AUDIO_EXT:
        return jsonify({'ok': False, 'error': 'audio format not supported'}), 415

    # Output landt lokaal in de workspace-map (sync/), of globaal als er (nog)
    # geen workspace is. Geen cloud-opslag (local-first, consistent met C2).
    ws_id, _werr = current_workspace_id(user_info, required=False)
    if ws_id:
        out_dir = os.path.join(DATA_DIR, 'workspaces', str(ws_id), 'sync')
    else:
        out_dir = os.path.join(OUTPUT_DIR, '_sync')
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as e:
        return jsonify({'ok': False, 'error': 'could not create sync folder: %s' % e}), 500

    base = _safe_filename(os.path.splitext(os.path.basename(vp))[0]) or 'set'
    out_path = _dedupe_output_path(os.path.join(out_dir, base + '_synced.mp4'))

    try:
        import audio_sync
        _ff = media_tools.ffmpeg()
        _fp = media_tools.ffprobe()
        manual = body.get('manual_offset_s')
        if manual is not None:
            # D4 - handmatige bevestiging: mux met de door de gebruiker gekozen offset.
            res = audio_sync.mux_with_offset(
                vp, ap, out_path, ffmpeg_bin=_ff, ffprobe_bin=_fp, offset_s=float(manual))
        else:
            # Eerst analyseren (geen mux). Hoge confidence -> automatisch muxen
            # (live-bewezen sync_and_mux). Lage confidence -> NIET stil een slechte
            # sync bakken, maar de handmatige-uitlijn-UI vragen (D4).
            info = audio_sync.analyze(vp, ap, ffmpeg_bin=_ff, ffprobe_bin=_fp)
            if float(info.get('confidence') or 0.0) >= 0.15:
                res = audio_sync.sync_and_mux(
                    vp, ap, out_path, ffmpeg_bin=_ff, ffprobe_bin=_fp)
            else:
                info['ok'] = True
                info['status'] = 'needs_manual'
                return jsonify(info)
    except Exception as e:
        log.warning("sync-import mislukt: %s", e)
        return jsonify({'ok': False, 'error': str(e)}), 422
    try:
        _audit('sync.import', user_id=user_info.get('user_id'),
               metadata={'video': os.path.basename(vp), 'confidence': res.get('confidence')})
    except Exception:
        pass
    return jsonify(res)


# --- Font upload + serving --------------------------------------------------
# Accepts TTF / OTF / WOFF2 (if fonttools is installed). WOFF2 gets converted
# to TTF on upload because ffmpeg's drawtext filter only reads native font
# files. Max 2 MB per font, max 8 fonts per brand kit. Storage: stable UUID
# filename under BRAND_FONTS_DIR. Metadata lives in brand_kit.json so the
# frontend can render an @font-face block on boot.
_FONT_MAX_BYTES   = 2 * 1024 * 1024
_FONT_MAX_COUNT   = 8
_FONT_ALLOWED_EXT = {'.ttf', '.otf', '.woff', '.woff2'}


def _sniff_font_kind(head_bytes):
    """Magic-bytes sniff. Returns one of 'ttf' / 'otf' / 'woff' / 'woff2' or None.
    Cheap defence against arbitrary file-as-font uploads."""
    if not head_bytes or len(head_bytes) < 4:
        return None
    sig = head_bytes[:4]
    if sig == b'\x00\x01\x00\x00' or sig == b'true' or sig == b'typ1':
        return 'ttf'
    if sig == b'OTTO':
        return 'otf'
    if sig == b'wOFF':
        return 'woff'
    if sig == b'wOF2':
        return 'woff2'
    return None


def _convert_woff_to_ttf(src_path, dst_path):
    """Decompress a WOFF/WOFF2 font into a native TTF/OTF using fonttools.
    Caller must check _HAS_FONTTOOLS first. Returns the resolved ext ('ttf' or 'otf')."""
    from fontTools.ttLib import TTFont
    f = TTFont(src_path)
    # WOFF/WOFF2 wrap a TTF or OTF table — sfntVersion tells us which.
    sfnt = getattr(f, 'sfntVersion', None)
    ext = 'otf' if sfnt == 'OTTO' else 'ttf'
    f.flavor = None  # strip WOFF compression so the saved file is a raw sfnt
    final = dst_path if dst_path.lower().endswith('.' + ext) else dst_path + '.' + ext
    f.save(final)
    return ext, final


@app.route('/api/brand-kit/fonts', methods=['POST'])
def upload_brand_font():
    """multipart/form-data with 'file' + optional 'family' + 'weight'.
    Returns the new font entry (and the whole fonts array for client refresh)."""
    if 'file' not in request.files:
        return jsonify({'error': 'no file'}), 400
    f = request.files['file']
    filename = (f.filename or '').strip()
    if not filename:
        return jsonify({'error': 'empty filename'}), 400
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _FONT_ALLOWED_EXT:
        return jsonify({'error': f'extension {ext} not allowed (use ttf/otf/woff/woff2)'}), 400

    head = f.stream.read(8)
    f.stream.seek(0)
    kind = _sniff_font_kind(head)
    if kind is None:
        return jsonify({'error': 'file does not look like a font (magic bytes mismatch)'}), 400

    kit = _load_brand_kit()
    if len(kit.get('fonts', [])) >= _FONT_MAX_COUNT:
        return jsonify({'error': f'brand kit already has {_FONT_MAX_COUNT} fonts — remove one first'}), 422

    # Buffer to a temp file so we can (a) size-check before commit, (b) hand off to fonttools.
    font_id = uuid.uuid4().hex[:12]
    tmp_path = os.path.join(BRAND_FONTS_DIR, font_id + '.' + kind + '.tmp')
    written = 0
    with open(tmp_path, 'wb') as out:
        while True:
            chunk = f.stream.read(64 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > _FONT_MAX_BYTES:
                out.close()
                try: os.remove(tmp_path)
                except Exception: pass
                return jsonify({'error': f'file exceeds {_FONT_MAX_BYTES // 1024 // 1024}MB limit'}), 413
            out.write(chunk)

    final_ext = 'ttf' if kind == 'ttf' else 'otf' if kind == 'otf' else None
    final_path = None
    if kind in ('woff', 'woff2'):
        if not _HAS_FONTTOOLS:
            try: os.remove(tmp_path)
            except Exception: pass
            return jsonify({
                'error': 'WOFF/WOFF2 conversion needs fonttools — run: pip install "fonttools[woff]" in the venv, then upload again'
            }), 422
        try:
            final_path = os.path.join(BRAND_FONTS_DIR, font_id)
            final_ext, final_path = _convert_woff_to_ttf(tmp_path, final_path)
        except Exception as e:
            try: os.remove(tmp_path)
            except Exception: pass
            return jsonify({'error': f'WOFF conversion failed: {e}'}), 500
        try: os.remove(tmp_path)
        except Exception: pass
    else:
        final_path = os.path.join(BRAND_FONTS_DIR, font_id + '.' + final_ext)
        os.replace(tmp_path, final_path)

    # Family name — caller can pass one explicitly; otherwise derive from filename.
    family = (request.form.get('family') or '').strip()
    if not family:
        family = os.path.splitext(filename)[0]
        # Strip common suffixes that turn into ugly labels in the picker.
        for suf in ('-Regular', '-Bold', '-Black', '-Italic', '-Medium', '-Light'):
            if family.endswith(suf):
                family = family[:-len(suf)]
    weight = (request.form.get('weight') or 'normal').strip()

    entry = {
        'id': font_id,
        'family': family,
        'weight': weight,
        'ext': final_ext,
        'path': final_path,            # absolute — used by ffmpeg drawtext
        'original_name': filename,
        'bytes': os.path.getsize(final_path),
        'uploaded': time.time(),
    }
    kit.setdefault('fonts', []).append(entry)
    kit['updated'] = time.time()
    _save_brand_kit(kit)
    log.info("Brand font uploaded: %s (%s, %d bytes)", family, final_ext, entry['bytes'])
    return jsonify({'success': True, 'font': entry, 'fonts': kit['fonts']})


@app.route('/api/brand-kit/fonts/<font_id>', methods=['GET'])
def serve_brand_font(font_id):
    """Serve the font binary so the browser can register it via @font-face."""
    if not re.fullmatch(r'[a-f0-9]{6,32}', font_id or ''):
        return jsonify({'error': 'bad font id'}), 400
    kit = _load_brand_kit()
    entry = next((e for e in kit.get('fonts', []) if e.get('id') == font_id), None)
    if not entry or not entry.get('path') or not os.path.exists(entry['path']):
        return jsonify({'error': 'font not found'}), 404
    mime = 'font/otf' if entry.get('ext') == 'otf' else 'font/ttf'
    return send_file(entry['path'], mimetype=mime, max_age=86400, conditional=True)


@app.route('/api/brand-kit/fonts/<font_id>', methods=['DELETE'])
def delete_brand_font(font_id):
    if not re.fullmatch(r'[a-f0-9]{6,32}', font_id or ''):
        return jsonify({'error': 'bad font id'}), 400
    kit = _load_brand_kit()
    fonts = kit.get('fonts', [])
    entry = next((e for e in fonts if e.get('id') == font_id), None)
    if not entry:
        return jsonify({'error': 'not found'}), 404
    # Best-effort file removal; we don't fail the API on disk errors.
    try:
        if entry.get('path') and os.path.exists(entry['path']):
            os.remove(entry['path'])
    except Exception as e:
        log.warning("Could not remove font file %s: %s", entry.get('path'), e)
    kit['fonts'] = [e for e in fonts if e.get('id') != font_id]
    # If the deleted font was bound to a caption preset, null its font_id so the
    # preset falls back to the system fonts instead of erroring on render.
    for p in kit.get('caption_presets', []):
        if p.get('font_id') == font_id:
            p['font_id'] = None
    kit['updated'] = time.time()
    _save_brand_kit(kit)
    return jsonify({'success': True, 'fonts': kit['fonts']})


# --- SESSIE 42 — Built-in fonts library + system-font auto-scan -------------
# Three read-only endpoints (no auth gate needed — fonts are public OS assets):
#   GET /api/builtin-fonts        → returns the 11-font manifest (from disk)
#   GET /api/system-fonts         → scans OS font directories, returns family list
#                                   ?refresh=1 forces a rescan; otherwise cached ~30s
#   GET /api/system-fonts/file/<id> → serves the .ttf/.otf to the browser so
#                                     @font-face can register it for live preview.
#
# Privacy: we read ONLY filenames from system font dirs. The font bytes never
# leave the user's machine — Flask serves them from localhost to the same
# browser tab. ffmpeg reads font paths directly from disk during render.

import platform
import hashlib
import threading

# Builtin-fonts directory is shipped with the app (bundled by PyInstaller).
# BASE_DIR is read-only in .app builds, but static/ is bundled inside the
# Resources folder — readable everywhere.
BUILTIN_FONTS_DIR = os.path.join(BASE_DIR, 'static', 'fonts', 'builtin')

# System-font scan cache. We rescan every 30s by default OR when the client
# passes ?refresh=1. The lock guards concurrent scans from spam.
_SYSTEM_FONT_CACHE = {'ts': 0.0, 'data': None}
_SYSTEM_FONT_LOCK = threading.Lock()
_SYSTEM_FONT_TTL = 30.0  # seconds


def _system_font_dirs():
    """Return the list of OS-specific directories to scan for fonts."""
    sys = platform.system()
    home = os.path.expanduser('~')
    if sys == 'Darwin':
        return [
            '/System/Library/Fonts',
            '/Library/Fonts',
            os.path.join(home, 'Library/Fonts'),
        ]
    if sys == 'Windows':
        win_root = os.environ.get('WINDIR', r'C:\Windows')
        local = os.environ.get('LOCALAPPDATA', '')
        out = [os.path.join(win_root, 'Fonts')]
        if local:
            out.append(os.path.join(local, 'Microsoft', 'Windows', 'Fonts'))
        return out
    # Linux + everything else
    return [
        '/usr/share/fonts',
        '/usr/local/share/fonts',
        os.path.join(home, '.fonts'),
        os.path.join(home, '.local/share/fonts'),
    ]


# Persisted scan-cache so cutter.py (different code path, same process)
# can resolve system-font IDs to absolute paths without re-scanning.
SYSTEM_FONTS_CACHE_PATH = os.path.join(DATA_DIR, 'system_fonts_cache.json')


def _persist_system_fonts_cache(data):
    """Write the scanned system-fonts to a JSON cache for cutter.py to read."""
    try:
        with open(SYSTEM_FONTS_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump({'ts': time.time(), 'fonts': data}, f)
    except Exception as e:
        log.warning("system-fonts cache write failed: %s", e)


def _scan_system_fonts():
    """Walk OS font dirs and build a flat list of available font files.

    Returns a list of dicts: {id, family, file, path, ext, source}.
    Each font gets a stable id = md5(absolute path)[:16] so the same file
    keeps the same id across rescans.
    ffmpeg can only render .ttf/.otf, so we filter on those extensions.
    .woff/.woff2 are valid for the browser preview but not the burned-in
    render — for simplicity we skip them entirely (no half-broken UX).
    """
    out = []
    seen_paths = set()
    seen_families = {}  # family lower → first entry (dedupe by family)
    for d in _system_font_dirs():
        if not d or not os.path.isdir(d):
            continue
        try:
            for root, _dirs, files in os.walk(d):
                for fn in files:
                    ext = os.path.splitext(fn)[1].lower()
                    # SESSIE 42 — accept .ttc (TrueType Collection) too:
                    # ffmpeg drawtext can read those via fontfile= and macOS
                    # ships Helvetica, Times, Geneva, Courier as .ttc bundles.
                    if ext not in ('.ttf', '.otf', '.ttc'):
                        continue
                    full = os.path.join(root, fn)
                    if full in seen_paths:
                        continue
                    seen_paths.add(full)
                    # Derive a human-readable family from the filename:
                    # "HelveticaNeue-Bold.ttf" → "Helvetica Neue Bold"
                    stem = os.path.splitext(fn)[0]
                    # Strip leading dot (e.g. ".SFNS-Regular" on macOS)
                    stem = stem.lstrip('.')
                    if not stem:
                        continue
                    # Build family by replacing - and _ with spaces, then
                    # splitting CamelCase. We do the camelcase split with a
                    # simple regex so "BebasNeue-Regular" → "Bebas Neue Regular".
                    family = re.sub(r'([a-z])([A-Z])', r'\1 \2', stem)
                    family = family.replace('-', ' ').replace('_', ' ')
                    family = re.sub(r'\s+', ' ', family).strip()
                    if not family:
                        continue
                    fid = hashlib.md5(full.encode('utf-8')).hexdigest()[:16]
                    entry = {
                        'id':     fid,
                        'family': family,
                        'file':   fn,
                        'path':   full,
                        'ext':    ext.lstrip('.'),
                        'source': 'system',
                    }
                    out.append(entry)
        except (PermissionError, OSError) as e:
            log.debug("system-font scan: skip %s (%s)", d, e)
            continue
    # Sort case-insensitively by family for predictable UX.
    out.sort(key=lambda e: (e['family'].lower(), e['file'].lower()))
    return out


@app.route('/api/builtin-fonts', methods=['GET'])
def list_builtin_fonts():
    """Return the bundled font manifest. Falls back to empty list if missing."""
    manifest_path = os.path.join(BUILTIN_FONTS_DIR, 'manifest.json')
    if not os.path.isfile(manifest_path):
        return jsonify({'fonts': []})
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Only return entries whose file actually exists on disk.
        out = []
        for entry in (data or []):
            fp = os.path.join(BUILTIN_FONTS_DIR, entry.get('file') or '')
            if os.path.isfile(fp):
                out.append(entry)
        return jsonify({'fonts': out})
    except Exception as e:
        log.warning("builtin-fonts manifest read failed: %s", e)
        return jsonify({'fonts': []})


@app.route('/api/system-fonts', methods=['GET'])
def list_system_fonts():
    """Return scanned system fonts. Cached per _SYSTEM_FONT_TTL seconds.

    Client passes ?refresh=1 to force a rescan (e.g. when the user clicks
    the ↻ refresh icon next to the Font label).
    """
    refresh = request.args.get('refresh') in ('1', 'true', 'yes')
    now = time.time()
    with _SYSTEM_FONT_LOCK:
        cache = _SYSTEM_FONT_CACHE
        stale = (cache['data'] is None) or ((now - cache['ts']) > _SYSTEM_FONT_TTL)
        if refresh or stale:
            cache['data'] = _scan_system_fonts()
            cache['ts'] = now
            _persist_system_fonts_cache(cache['data'])
        data = cache['data']
    # The path field is for internal use (cutter.py needs it for ffmpeg);
    # the browser only needs {id, family, file, ext, source}, but exposing
    # the path here is harmless since this endpoint runs locally only.
    return jsonify({
        'fonts': data,
        'count': len(data),
        'scanned_at': cache['ts'],
        'platform': platform.system(),
    })


@app.route('/api/system-fonts/file/<font_id>', methods=['GET'])
def serve_system_font(font_id):
    """Serve a system font file to the browser so @font-face can load it.

    We resolve the font_id against the cache (built up by /api/system-fonts).
    Only paths in the scanned cache are served — no arbitrary path traversal.
    """
    if not re.fullmatch(r'[a-f0-9]{8,32}', font_id or ''):
        return jsonify({'error': 'bad font id'}), 400
    with _SYSTEM_FONT_LOCK:
        data = _SYSTEM_FONT_CACHE.get('data') or []
    entry = next((e for e in data if e.get('id') == font_id), None)
    if not entry:
        # Cold cache — do a one-shot scan, then retry.
        with _SYSTEM_FONT_LOCK:
            _SYSTEM_FONT_CACHE['data'] = _scan_system_fonts()
            _SYSTEM_FONT_CACHE['ts'] = time.time()
            _persist_system_fonts_cache(_SYSTEM_FONT_CACHE['data'])
            data = _SYSTEM_FONT_CACHE['data']
        entry = next((e for e in data if e.get('id') == font_id), None)
    if not entry or not entry.get('path') or not os.path.isfile(entry['path']):
        return jsonify({'error': 'font not found'}), 404
    # SESSIE 42 — mime by ext. .ttc reports as font/collection (RFC 8081)
    # but browsers also accept font/ttf for it.
    ext = (entry.get('ext') or 'ttf').lower()
    mime = {'otf': 'font/otf', 'ttc': 'font/collection'}.get(ext, 'font/ttf')
    return send_file(entry['path'], mimetype=mime, max_age=86400, conditional=True)


# --- Logo upload + serving --------------------------------------------------
# Single logo slot per brand kit. PNG / SVG only. Max 1 MB. Stored at
# BRAND_LOGO_DIR/logo.<ext> so older logos get overwritten on upload.
_LOGO_MAX_BYTES = 1 * 1024 * 1024
_LOGO_ALLOWED_EXT = {'.png', '.svg'}


@app.route('/api/brand-kit/logo', methods=['POST'])
def upload_brand_logo():
    if 'file' not in request.files:
        return jsonify({'error': 'no file'}), 400
    f = request.files['file']
    filename = (f.filename or '').strip()
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _LOGO_ALLOWED_EXT:
        return jsonify({'error': f'extension {ext} not allowed (use png/svg)'}), 400
    # Sniff: PNG starts with \x89PNG, SVG starts with <?xml or <svg
    head = f.stream.read(8)
    f.stream.seek(0)
    if ext == '.png' and head[:4] != b'\x89PNG':
        return jsonify({'error': 'PNG magic bytes mismatch'}), 400
    if ext == '.svg' and not (head.lstrip().startswith(b'<?xml') or head.lstrip().startswith(b'<svg')):
        return jsonify({'error': 'SVG does not start with <?xml or <svg'}), 400

    # SESSIE 74 fase 4: per-workspace logo-map (lost vaste-bestandsnaam-clobber op).
    _logo_dir = _brand_asset_dirs(_active_brand_ws())['logo']
    # Wipe any previous logo files so we don't accumulate.
    for old in os.listdir(_logo_dir):
        try: os.remove(os.path.join(_logo_dir, old))
        except Exception: pass

    final_path = os.path.join(_logo_dir, 'logo' + ext)
    written = 0
    with open(final_path, 'wb') as out:
        while True:
            chunk = f.stream.read(64 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > _LOGO_MAX_BYTES:
                out.close()
                try: os.remove(final_path)
                except Exception: pass
                return jsonify({'error': f'file exceeds {_LOGO_MAX_BYTES // 1024 // 1024}MB limit'}), 413
            out.write(chunk)

    kit = _load_brand_kit()
    kit['logo'] = {
        'path': final_path,
        'ext': ext.lstrip('.'),
        'corner': (kit.get('logo') or {}).get('corner') or 'tr',
        'opacity': (kit.get('logo') or {}).get('opacity') or 0.9,
        'size_pct': (kit.get('logo') or {}).get('size_pct') or 12,
        'uploaded': time.time(),
        'bytes': written,
    }
    kit['updated'] = time.time()
    _save_brand_kit(kit)
    log.info("Brand logo uploaded: %s (%d bytes)", filename, written)
    return jsonify({'success': True, 'logo': kit['logo']})


@app.route('/api/brand-kit/logo', methods=['GET'])
def serve_brand_logo():
    kit = _load_brand_kit()
    logo = kit.get('logo') or {}
    p = logo.get('path')
    if not p or not os.path.exists(p):
        return jsonify({'error': 'no logo set'}), 404
    mime = 'image/png' if logo.get('ext') == 'png' else 'image/svg+xml'
    return send_file(p, mimetype=mime, max_age=3600, conditional=True)


@app.route('/api/brand-kit/logo', methods=['DELETE'])
def delete_brand_logo():
    kit = _load_brand_kit()
    logo = kit.get('logo') or {}
    p = logo.get('path')
    try:
        if p and os.path.exists(p):
            os.remove(p)
    except Exception as e:
        log.warning("Could not remove logo file %s: %s", p, e)
    kit['logo'] = None
    kit['updated'] = time.time()
    _save_brand_kit(kit)
    return jsonify({'success': True})


# --- Brand watermark (SESSIE 31) -------------------------------------------
# Watermark is a per-export overlay that sits on top of every rendered clip.
# Stored alongside brand_kit.json under BRAND_WATERMARK_DIR/watermark.<ext>.
# Settings (corner, opacity, size_pct, enabled) live in brand_kit.json so
# cutter.py picks them up via _load_brand_assets_for_job.
_WATERMARK_MAX_BYTES = 2 * 1024 * 1024   # 2 MB
_WATERMARK_ALLOWED_EXT = {'.png', '.jpg', '.jpeg'}


@app.route('/api/brand-kit/watermark', methods=['POST'])
def upload_brand_watermark():
    """Twee upload-modes:
       1. Multipart-upload (file=...) — legacy, gebruikt door brand-kit panel
       2. SESSIE 43b — JSON met {path: '/abs/path/to.png'} — gebruikt door
          de inline upload-flow in de export-modal die eerst /api/pick-file
          aanroept. Backend leest dan lokaal het bestand en kopieert het
          naar BRAND_WATERMARK_DIR.
    """
    content_type = (request.content_type or '').lower()

    # ---- Mode 2: JSON path-based ----
    if 'application/json' in content_type:
        body = request.get_json(silent=True) or {}
        src_path = body.get('path')
        if not src_path or not isinstance(src_path, str):
            return jsonify({'error': 'JSON body must include "path"'}), 400
        if not os.path.isfile(src_path):
            return jsonify({'error': f'file not found: {src_path}'}), 404
        ext = os.path.splitext(src_path)[1].lower()
        if ext not in _WATERMARK_ALLOWED_EXT:
            return jsonify({'error': f'extension {ext} not allowed (use png/jpg)'}), 400
        try:
            file_size = os.path.getsize(src_path)
        except OSError as e:
            return jsonify({'error': f'cannot stat file: {e}'}), 400
        if file_size > _WATERMARK_MAX_BYTES:
            return jsonify({'error': f'file exceeds {_WATERMARK_MAX_BYTES // 1024 // 1024}MB limit'}), 413
        # Magic-byte check
        try:
            with open(src_path, 'rb') as fh:
                head = fh.read(8)
        except OSError as e:
            return jsonify({'error': f'cannot read file: {e}'}), 400
        if ext == '.png' and head[:4] != b'\x89PNG':
            return jsonify({'error': 'PNG magic bytes mismatch'}), 400
        if ext in ('.jpg', '.jpeg') and head[:3] != b'\xff\xd8\xff':
            return jsonify({'error': 'JPG magic bytes mismatch'}), 400

        # SESSIE 74 fase 4: per-workspace watermark-map (clobber-fix).
        _wm_dir = _brand_asset_dirs(_active_brand_ws())['watermark']
        # Wipe previous watermark files so the folder doesn't accumulate.
        for old in os.listdir(_wm_dir):
            try: os.remove(os.path.join(_wm_dir, old))
            except Exception: pass

        save_ext = ext if ext != '.jpeg' else '.jpg'
        final_path = os.path.join(_wm_dir, 'watermark' + save_ext)
        try:
            shutil.copy2(src_path, final_path)
        except (OSError, shutil.Error) as e:
            return jsonify({'error': f'copy failed: {e}'}), 500

        kit = _load_brand_kit()
        prev = kit.get('watermark') or {}
        kit['watermark'] = {
            'path': final_path,
            'ext': save_ext.lstrip('.'),
            'corner':  prev.get('corner') or 'br',
            'opacity': prev.get('opacity') if isinstance(prev.get('opacity'), (int,float)) else 0.6,
            'size_pct': prev.get('size_pct') if isinstance(prev.get('size_pct'), (int,float)) else 18,
            'enabled': True,
            'uploaded': time.time(),
            'bytes': file_size,
            'file': os.path.basename(final_path),
        }
        kit['updated'] = time.time()
        _save_brand_kit(kit)
        log.info("Brand watermark imported from %s (%d bytes)", src_path, file_size)
        return jsonify({
            'success': True,
            'watermark': kit['watermark'],
            'url': '/api/brand-kit/watermark',
        })

    # ---- Mode 1: multipart upload (legacy) ----
    if 'file' not in request.files:
        return jsonify({'error': 'no file'}), 400
    f = request.files['file']
    filename = (f.filename or '').strip()
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _WATERMARK_ALLOWED_EXT:
        return jsonify({'error': f'extension {ext} not allowed (use png/jpg)'}), 400
    head = f.stream.read(8)
    f.stream.seek(0)
    if ext == '.png' and head[:4] != b'\x89PNG':
        return jsonify({'error': 'PNG magic bytes mismatch'}), 400
    if ext in ('.jpg', '.jpeg') and head[:3] != b'\xff\xd8\xff':
        return jsonify({'error': 'JPG magic bytes mismatch'}), 400

    # SESSIE 74 fase 4: per-workspace watermark-map (clobber-fix).
    _wm_dir = _brand_asset_dirs(_active_brand_ws())['watermark']
    # Wipe previous watermark files so the folder doesn't accumulate.
    for old in os.listdir(_wm_dir):
        try: os.remove(os.path.join(_wm_dir, old))
        except Exception: pass

    save_ext = ext if ext != '.jpeg' else '.jpg'
    final_path = os.path.join(_wm_dir, 'watermark' + save_ext)
    written = 0
    with open(final_path, 'wb') as out:
        while True:
            chunk = f.stream.read(64 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > _WATERMARK_MAX_BYTES:
                out.close()
                try: os.remove(final_path)
                except Exception: pass
                return jsonify({'error': f'file exceeds {_WATERMARK_MAX_BYTES // 1024 // 1024}MB limit'}), 413
            out.write(chunk)

    kit = _load_brand_kit()
    prev = kit.get('watermark') or {}
    kit['watermark'] = {
        'path': final_path,
        'ext': save_ext.lstrip('.'),
        'corner':  prev.get('corner') or 'br',
        'opacity': prev.get('opacity') if isinstance(prev.get('opacity'), (int,float)) else 0.6,
        'size_pct': prev.get('size_pct') if isinstance(prev.get('size_pct'), (int,float)) else 18,
        'enabled': True,
        'uploaded': time.time(),
        'bytes': written,
        'file': os.path.basename(final_path),
    }
    kit['updated'] = time.time()
    _save_brand_kit(kit)
    log.info("Brand watermark uploaded: %s (%d bytes)", filename, written)
    return jsonify({'success': True, 'watermark': kit['watermark']})


@app.route('/api/brand-kit/watermark', methods=['GET'])
def serve_brand_watermark():
    kit = _load_brand_kit()
    wm = kit.get('watermark') or {}
    p = wm.get('path')
    if not p or not os.path.exists(p):
        return jsonify({'error': 'no watermark set'}), 404
    ext = (wm.get('ext') or '').lower()
    mime = 'image/png' if ext == 'png' else 'image/jpeg'
    return send_file(p, mimetype=mime, max_age=3600, conditional=True)


@app.route('/api/brand-kit/watermark', methods=['DELETE'])
def delete_brand_watermark():
    kit = _load_brand_kit()
    wm = kit.get('watermark') or {}
    p = wm.get('path')
    try:
        if p and os.path.exists(p):
            os.remove(p)
    except Exception as e:
        log.warning("Could not remove watermark file %s: %s", p, e)
    kit['watermark'] = None
    kit['updated'] = time.time()
    _save_brand_kit(kit)
    return jsonify({'success': True})


@app.route('/api/brand-kit/watermark/settings', methods=['POST'])
def update_brand_watermark_settings():
    """PATCH-like endpoint to flip corner/opacity/size/enabled without
    re-uploading the image."""
    body = request.json or {}
    kit = _load_brand_kit()
    wm = dict(kit.get('watermark') or {})
    if not wm.get('path'):
        return jsonify({'error': 'no watermark uploaded yet'}), 400
    if 'corner' in body and body['corner'] in ('tl','tr','bl','br','center'):
        wm['corner'] = body['corner']
    if 'opacity' in body:
        try:
            wm['opacity'] = max(0.0, min(1.0, float(body['opacity'])))
        except (TypeError, ValueError): pass
    if 'size_pct' in body:
        try:
            wm['size_pct'] = max(5.0, min(60.0, float(body['size_pct'])))
        except (TypeError, ValueError): pass
    if 'enabled' in body:
        wm['enabled'] = bool(body['enabled'])
    kit['watermark'] = wm
    kit['updated'] = time.time()
    _save_brand_kit(kit)
    return jsonify({'success': True, 'watermark': wm})


# --- Per-clip text overlays (used by the editor Text panel) -----------------
# Stored at output/<job_id>/text_overlays.json. Shape:
#   { "clips": { "<clip_idx>": [ {id, text, font_id, color, size_pct,
#                                  x_pct, y_pct, align, in_sec, out_sec,
#                                  anim, bg, weight}, ... ] } }
# Indexed by analyzer's 1-based clip['index']. Re-export paths in cutter.py
# read this file and apply drawtext filters per layer.
def _job_overlays_path(job_id):
    return os.path.join(OUTPUT_DIR, job_id, 'text_overlays.json')


@app.route('/api/clip-overlays/<job_id>', methods=['GET'])
def get_clip_overlays(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    data = _load_json_blob(_job_overlays_path(job_id), {'clips': {}})
    if 'clips' not in data:
        data['clips'] = {}
    return jsonify(data)


# --- SESSIE 22 — TR1 manual keyframe tracking -----------------------------
# Per-clip tracking data lives at output/<job>/tracking/<clip_idx>.json:
#   {
#     "clip_index": 1,
#     "subject": "primary",
#     "keyframes": [{t, cx_pct, cy_pct, w_pct, h_pct, source}],  source=manual|auto|smoothed
#     "interpolation": "linear" | "smoothed",
#     "smoothing": 0.0..1.0
#   }
# All coordinates are percentages of the source frame so they remain
# resolution-independent. The cutter reads this file and builds dynamic
# crop expressions for vertical export. Auto-tracking (block D) writes the
# same schema — same UI displays + edits both.
def _job_tracking_dir(job_id):
    return os.path.join(OUTPUT_DIR, job_id, 'tracking')


def _job_tracking_path(job_id, clip_idx):
    return os.path.join(_job_tracking_dir(job_id), f'clip_{int(clip_idx):03d}.json')


def _validate_keyframes_payload(raw):
    """Sanitise an incoming keyframes-list. Drops malformed entries, clamps
    ranges, sorts by time. Returns a clean list."""
    if not isinstance(raw, list):
        return []
    out = []
    for kf in raw:
        if not isinstance(kf, dict):
            continue
        try:
            t = float(kf.get('t') or 0)
            cx = float(kf.get('cx_pct') if kf.get('cx_pct') is not None else 50)
            cy = float(kf.get('cy_pct') if kf.get('cy_pct') is not None else 50)
            w  = float(kf.get('w_pct')  if kf.get('w_pct')  is not None else 40)
            h  = float(kf.get('h_pct')  if kf.get('h_pct')  is not None else 70)
        except (TypeError, ValueError):
            continue
        out.append({
            't':       max(0.0, t),
            'cx_pct':  max(0.0, min(100.0, cx)),
            'cy_pct':  max(0.0, min(100.0, cy)),
            'w_pct':   max(5.0,  min(100.0, w)),
            'h_pct':   max(5.0,  min(100.0, h)),
            'source':  kf.get('source') if kf.get('source') in ('manual','auto','smoothed') else 'manual',
        })
    # Sort by time so the cutter doesn't need to.
    out.sort(key=lambda k: k['t'])
    # Cap at 50 keyframes total — anything more and the user should rely on
    # the auto-tracker's smoothing instead of manual placement.
    return out[:50]


@app.route('/api/track/<job_id>/<int:clip_idx>', methods=['GET'])
def get_track(job_id, clip_idx):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    p = _job_tracking_path(job_id, clip_idx)
    data = _load_json_blob(p, None)
    if data is None:
        return jsonify({
            'clip_index': clip_idx,
            'subject': 'primary',
            'keyframes': [],
            'interpolation': 'linear',
            'smoothing': 0.0,
        })
    return jsonify(data)


@app.route('/api/track/<job_id>/<int:clip_idx>', methods=['POST'])
def save_track(job_id, clip_idx):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    if not os.path.isdir(job_dir):
        return jsonify({'error': 'unknown job'}), 404
    body = request.json or {}
    keyframes = _validate_keyframes_payload(body.get('keyframes') or [])
    interp = body.get('interpolation') if body.get('interpolation') in ('linear','smoothed') else 'linear'
    try:
        smoothing = max(0.0, min(1.0, float(body.get('smoothing') or 0)))
    except (TypeError, ValueError):
        smoothing = 0.0
    # SESSIE 30c - crop_mode: 'pan' (default - full height, horizontal
    # pan only, preserves the whole scene) or 'zoom' (legacy - tightens
    # around the DJ). Whitelisted so a client can't sneak in other modes.
    # SESSIE 31 — 'letterbox' added: no crop at all, scale-to-fit with
    # black bars. Sjuul's "follow horizontally" expectation maps best to
    # this mode for landscape sources.
    crop_mode = body.get('crop_mode') if body.get('crop_mode') in ('pan', 'zoom', 'letterbox') else 'pan'
    data = {
        'clip_index':    int(clip_idx),
        'subject':       body.get('subject') or 'primary',
        'keyframes':     keyframes,
        'interpolation': interp,
        'smoothing':     smoothing,
        'crop_mode':     crop_mode,
        'updated':       time.time(),
    }
    os.makedirs(_job_tracking_dir(job_id), exist_ok=True)
    _save_json_blob(_job_tracking_path(job_id, clip_idx), data)
    return jsonify({'success': True, **data})


# SESSIE 22 D — optional tracking module. Wrapped so the app starts even
# when none of pyobjc-framework-Vision / ultralytics / opencv-python is
# installed in the venv.
try:
    import tracking as _tracking_mod
except Exception as e:
    log.warning(f"tracking module not available: {e}")
    _tracking_mod = None


def _resolve_clip_source_for_tracking(job, clip_idx):
    """Find the source video path + clip start/end seconds for an auto-track
    run. Tracking analyses the ORIGINAL video (not the already-cut clip)
    because the keyframes drive the vertical-crop pipeline which also
    operates on the original."""
    if not job:
        return None, None, None
    video_path = job.get('video_path') or job.get('source_path')
    if not video_path or not os.path.exists(video_path):
        return None, None, None
    clips = job.get('clips') or []
    # Match on analyzer 1-based clip['index']; fall back to 0-based offset.
    target = None
    for c in clips:
        if int(c.get('index') or -1) == int(clip_idx):
            target = c; break
    if target is None and 0 <= int(clip_idx) - 1 < len(clips):
        target = clips[int(clip_idx) - 1]
    if target is None:
        return None, None, None
    start = float(target.get('start') or 0)
    end   = float(target.get('end')   or (start + 10))
    return video_path, start, max(0.5, end - start)


@app.route('/api/track/<job_id>/<int:clip_idx>/auto', methods=['POST'])
def api_track_auto_start(job_id, clip_idx):
    """Kick off auto-tracking on the given clip. Returns immediately with
    async=True; clients poll /api/track/<job>/<clip>/auto/status until done."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    if _tracking_mod is None:
        return jsonify({
            'ok': False,
            'error': 'Tracking module failed to import — see server log.',
        }), 500
    engines = _tracking_mod.engines_available()
    if not engines.get('any'):
        return jsonify({
            'ok': False,
            'error': 'No detection engine installed. Run in venv: '
                     'pip install "pyobjc-framework-Vision" opencv-python ultralytics',
            'engines': engines,
        }), 422

    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        snap = _load_job_snapshot(job_id)
        if snap: job = snap
    if not job:
        return jsonify({'ok': False, 'error': 'unknown job'}), 404

    video_path, start, duration = _resolve_clip_source_for_tracking(job, clip_idx)
    if not video_path:
        return jsonify({'ok': False, 'error': 'Could not resolve clip source video'}), 404

    body = request.get_json(silent=True) or {}
    fps = float(body.get('fps') or 4)
    max_kf = int(body.get('max_keyframes') or 20)
    smoothing = float(body.get('smoothing') or 0.4)
    yolo_fb = bool(body.get('yolo_fallback', True))

    # SESSIE 24 B3 — read the job-level subject signature so the per-clip
    # tracker can bias its picks toward "the DJ we already locked onto".
    # Body can opt OUT with use_signature=false (e.g. user wants a clean
    # re-detect on this clip).
    subject_sig = None
    if body.get('use_signature', True):
        subject_sig = (job.get('subject_signature') or None)

    key = f'{job_id}/{int(clip_idx)}'
    _tracking_mod.clear_auto_state(key)
    _tracking_mod.run_auto_track_async(
        key, video_path, start, duration,
        fps=fps, max_keyframes=max_kf, smoothing=smoothing,
        yolo_fallback=yolo_fb,
        subject_signature=subject_sig,
    )
    return jsonify({
        'ok': True, 'async': True, 'engines': engines,
        'using_signature': bool(subject_sig),
    })


@app.route('/api/track/<job_id>/<int:clip_idx>/auto/status', methods=['GET'])
def api_track_auto_status(job_id, clip_idx):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    if _tracking_mod is None:
        return jsonify({'done': True, 'error': 'tracking module not loaded'}), 500
    key = f'{job_id}/{int(clip_idx)}'
    state = _tracking_mod.get_auto_state(key)
    if not state:
        return jsonify({'done': False, 'frames_done': 0, 'frames_total': 0})
    out = {
        'done':         bool(state.get('done')),
        'frames_done':  int(state.get('frames_done') or 0),
        'frames_total': int(state.get('frames_total') or 0),
    }
    if state.get('done'):
        result = state.get('result') or {}
        if result.get('ok'):
            out.update({
                'ok': True,
                'engine': result.get('engine'),
                'fallback_used': result.get('fallback_used'),
                'keyframes': result.get('keyframes', []),
            })
            # Persist to disk so the manual-tracking endpoints see it next load.
            # SESSIE 30c - preserve the existing crop_mode if the file
            # already had one; otherwise default to 'pan' (full height,
            # horizontal pan only - the new default).
            try:
                existing = {}
                p_existing = _job_tracking_path(job_id, clip_idx)
                if os.path.exists(p_existing):
                    try:
                        with open(p_existing, 'r') as _f:
                            existing = json.load(_f) or {}
                    except Exception:
                        existing = {}
                existing_mode = existing.get('crop_mode')
                if existing_mode not in ('pan', 'zoom', 'letterbox'):
                    existing_mode = 'pan'
                _save_json_blob(_job_tracking_path(job_id, clip_idx), {
                    'clip_index':    int(clip_idx),
                    'subject':       'primary',
                    'keyframes':     result.get('keyframes', []),
                    'interpolation': 'linear',
                    'smoothing':     0.4,
                    'crop_mode':     existing_mode,
                    'updated':       time.time(),
                    'auto':          True,
                    'engine':        result.get('engine'),
                })
            except Exception as e:
                log.warning(f"tracking persist failed for {key}: {e}")
            # SESSIE 24 B3 — compute + persist the job-level subject signature
            # from this clip's keyframes IF the job doesn't have one yet. We
            # don't overwrite an existing signature on every auto-track,
            # because clip-N may have detected the wrong person if the prior
            # was missing. Manual /subject-signature POST/DELETE handles
            # explicit overrides.
            try:
                kfs = result.get('keyframes', []) or []
                sig = _tracking_mod.compute_subject_signature(kfs)
                if sig:
                    snapshot_target = None
                    with jobs_lock:
                        j = jobs.get(job_id)
                        if j is not None and not j.get('subject_signature'):
                            j['subject_signature'] = sig
                            j['subject_signature_clip'] = int(clip_idx)
                            out['subject_signature_saved'] = sig
                            snapshot_target = j
                    if snapshot_target is not None:
                        try:
                            _persist_job_snapshot(snapshot_target)
                        except Exception:
                            pass
            except Exception as e:
                log.warning(f"subject signature compute failed for {key}: {e}")
        else:
            out['ok'] = False
            out['error'] = result.get('error') or 'auto-track failed'
        # Clean up state so a re-run starts fresh.
        _tracking_mod.clear_auto_state(key)
    return jsonify(out)


@app.route('/api/track/<job_id>/<int:clip_idx>', methods=['DELETE'])
def delete_track(job_id, clip_idx):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    p = _job_tracking_path(job_id, clip_idx)
    try:
        if os.path.exists(p):
            os.remove(p)
    except Exception:
        pass
    return jsonify({'success': True})


# SESSIE 24 B3 — Subject-signature endpoints. The signature is a job-level
# (cx, cy, w, h) in 0..1 that locks auto-track onto "the DJ" across clips.
# GET inspects it, DELETE clears it, POST overrides it manually (e.g. user
# happy with clip-N's tracking and wants THAT to be the canonical signature).
@app.route('/api/job/<job_id>/subject-signature', methods=['GET'])
def api_subject_signature_get(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    with jobs_lock:
        job = jobs.get(job_id) or {}
        sig = job.get('subject_signature')
        anchor_clip = job.get('subject_signature_clip')
    if not sig:
        snap = _load_job_snapshot(job_id)
        if snap:
            sig = snap.get('subject_signature')
            anchor_clip = snap.get('subject_signature_clip')
    return jsonify({
        'signature': sig,
        'anchor_clip': anchor_clip,
        'present': bool(sig),
    })


@app.route('/api/job/<job_id>/subject-signature', methods=['DELETE'])
def api_subject_signature_clear(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    snapshot_target = None
    with jobs_lock:
        j = jobs.get(job_id)
        if j is not None:
            j.pop('subject_signature', None)
            j.pop('subject_signature_clip', None)
            snapshot_target = j
    if snapshot_target is not None:
        try:
            _persist_job_snapshot(snapshot_target)
        except Exception:
            pass
    return jsonify({'success': True, 'present': False})


@app.route('/api/job/<job_id>/subject-signature', methods=['POST'])
def api_subject_signature_set(job_id):
    """Override the auto-saved signature with one computed from a specific
    clip's keyframes. Body: { clip_index } — we look up that clip's tracking
    JSON and recompute the signature."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    body = request.get_json(silent=True) or {}
    try:
        clip_idx = int(body['clip_index'])
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'clip_index required'}), 400
    if _tracking_mod is None:
        return jsonify({'error': 'tracking module unavailable'}), 500
    trk = _load_json_blob(_job_tracking_path(job_id, clip_idx), None)
    if not trk or not trk.get('keyframes'):
        return jsonify({'error': 'No tracking keyframes for that clip'}), 404
    sig = _tracking_mod.compute_subject_signature(trk['keyframes'])
    if not sig:
        return jsonify({'error': 'Could not compute signature (too few keyframes)'}), 422
    snapshot_target = None
    with jobs_lock:
        j = jobs.get(job_id)
        if j is not None:
            j['subject_signature'] = sig
            j['subject_signature_clip'] = clip_idx
            snapshot_target = j
    if snapshot_target is not None:
        try:
            _persist_job_snapshot(snapshot_target)
        except Exception:
            pass
    return jsonify({'success': True, 'signature': sig, 'anchor_clip': clip_idx})


@app.route('/api/clip-overlays/<job_id>', methods=['POST'])
def save_clip_overlays(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    if not os.path.isdir(job_dir):
        return jsonify({'error': 'unknown job'}), 404
    body = request.json or {}
    clip_idx = body.get('clip_index')
    layers   = body.get('layers')
    if not isinstance(clip_idx, int) or not isinstance(layers, list):
        return jsonify({'error': 'expected {clip_index:int, layers:list}'}), 400
    if len(layers) > 8:
        return jsonify({'error': 'max 8 text layers per clip'}), 422

    data = _load_json_blob(_job_overlays_path(job_id), {'clips': {}})
    if 'clips' not in data:
        data['clips'] = {}

    # Sanitise every layer — drop unknown keys, coerce types, clamp ranges.
    sanitised = []
    for raw in layers:
        if not isinstance(raw, dict): continue
        txt = (raw.get('text') or '').strip()
        if not txt: continue
        sanitised.append({
            'id':      str(raw.get('id') or uuid.uuid4().hex[:10]),
            'text':    txt[:240],
            'font_id': raw.get('font_id') if isinstance(raw.get('font_id'), str) else None,
            'color':   (raw.get('color') if re.fullmatch(r'#?[0-9a-fA-F]{3,8}', str(raw.get('color') or '')) else '#ffffff'),
            'size_pct': max(2, min(40, float(raw.get('size_pct') or 6))),
            'x_pct':   max(0, min(100, float(raw.get('x_pct') if raw.get('x_pct') is not None else 50))),
            'y_pct':   max(0, min(100, float(raw.get('y_pct') if raw.get('y_pct') is not None else 80))),
            'align':   raw.get('align') if raw.get('align') in ('left','center','right') else 'center',
            'in_sec':  max(0, float(raw.get('in_sec') or 0)),
            'out_sec': max(0.1, float(raw.get('out_sec') or 9999)),
            'anim':    raw.get('anim') if raw.get('anim') in ('none','fade','slide-up','pop') else 'fade',
            'bg':      bool(raw.get('bg')),
            'weight':  raw.get('weight') if raw.get('weight') in ('normal','bold') else 'normal',
        })

    data['clips'][str(clip_idx)] = sanitised
    _save_json_blob(_job_overlays_path(job_id), data)
    return jsonify({'success': True, 'clip_index': clip_idx, 'layers': sanitised})


# --- Brand caption preset CRUD ----------------------------------------------
# Stored under brand_kit.caption_presets (saved presets, not the 4 hardcoded
# Style Room demos). Up to 12 user-saved presets per kit.
@app.route('/api/brand-kit/presets', methods=['POST'])
def save_brand_preset():
    body = request.json or {}
    name = (body.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400
    kit = _load_brand_kit()
    if len(kit.get('caption_presets', [])) >= 12:
        return jsonify({'error': 'max 12 saved presets — remove one first'}), 422
    preset = {
        'id':       uuid.uuid4().hex[:10],
        'name':     name[:60],
        'font_id':  body.get('font_id') if isinstance(body.get('font_id'), str) else None,
        'color':    body.get('color') if re.fullmatch(r'#?[0-9a-fA-F]{3,8}', str(body.get('color') or '')) else '#ffffff',
        'size_pct': max(2, min(40, float(body.get('size_pct') or 6))),
        'anim':     body.get('anim') if body.get('anim') in ('none','fade','slide-up','pop') else 'fade',
        'bg':       bool(body.get('bg')),
        'weight':   body.get('weight') if body.get('weight') in ('normal','bold') else 'normal',
        'position': body.get('position') if body.get('position') in ('top','center','bottom') else 'bottom',
        'created':  time.time(),
    }
    kit.setdefault('caption_presets', []).append(preset)
    kit['updated'] = time.time()
    _save_brand_kit(kit)
    return jsonify({'success': True, 'preset': preset, 'presets': kit['caption_presets']})


@app.route('/api/brand-kit/presets/<preset_id>', methods=['DELETE'])
def delete_brand_preset(preset_id):
    if not re.fullmatch(r'[a-f0-9]{6,32}', preset_id or ''):
        return jsonify({'error': 'bad preset id'}), 400
    kit = _load_brand_kit()
    kit['caption_presets'] = [p for p in kit.get('caption_presets', []) if p.get('id') != preset_id]
    kit['updated'] = time.time()
    _save_brand_kit(kit)
    return jsonify({'success': True, 'presets': kit['caption_presets']})


@app.route('/api/capabilities')
def capabilities():
    """Probe local hardware/encoder capabilities so the UI can surface them.

    Reports: ffmpeg presence + version, h264_videotoolbox encoder availability
    (Apple Silicon hardware H.264), Apple Metal Performance Shaders (mps)
    availability via PyTorch, plus the existing demucs + social-platform info.
    """
    platforms = get_platform_status()

    # ffmpeg presence + version + videotoolbox encoder probe
    # SESSIE 66 — via media_tools zodat het rapport de daadwerkelijk gebruikte
    # (gebundelde) binary toont, niet alleen de PATH-versie.
    ffmpeg_path = media_tools.ffmpeg()
    if not os.path.isabs(ffmpeg_path):
        ffmpeg_path = shutil.which(ffmpeg_path)
    ffmpeg_version = None
    has_videotoolbox = False
    if ffmpeg_path:
        try:
            v_out = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True, text=True, timeout=5,
            )
            first_line = (v_out.stdout or '').splitlines()[:1]
            if first_line:
                ffmpeg_version = first_line[0].strip()
        except Exception as e:
            log.warning("ffmpeg -version probe failed: %s", e)
        try:
            enc_out = subprocess.run(
                [ffmpeg_path, '-hide_banner', '-encoders'],
                capture_output=True, text=True, timeout=8,
            )
            has_videotoolbox = 'h264_videotoolbox' in (enc_out.stdout or '')
        except Exception as e:
            log.warning("ffmpeg -encoders probe failed: %s", e)

    # PyTorch MPS (Metal) probe — soft-fail if torch isn't installed.
    has_mps = False
    torch_version = None
    try:
        import torch  # noqa: WPS433 — optional dependency
        torch_version = getattr(torch, '__version__', None)
        has_mps = bool(
            getattr(torch.backends, 'mps', None)
            and torch.backends.mps.is_available()
        )
    except Exception:
        pass

    return jsonify({
        'demucs': HAS_DEMUCS,
        'platforms': platforms,
        'ffmpeg': {
            'present': bool(ffmpeg_path),
            'path': ffmpeg_path,
            'version': ffmpeg_version,
            'h264_videotoolbox': has_videotoolbox,
            # SESSIE 22 — drawtext requires libfreetype at ffmpeg compile time.
            # Surfaced so the UI can warn the user; without it our text-overlay
            # and BPM-stamp pipelines silently skip the burn-in step.
            'drawtext': _ffmpeg_has_drawtext(),
        },
        'torch': {
            'present': torch_version is not None,
            'version': torch_version,
            'mps': has_mps,
        },
    })


def _history_entry_is_loadable(jid):
    """Bug-fix 1b + race-safety — a history entry is "loadable" if either:
      • a job.json snapshot exists on disk (rehydrate path, authoritative), OR
      • the job is still only in-memory but already finished — `_process_job`
        flips status to 'done' BEFORE `_append_to_history` writes the
        snapshot, so a frontend that polls /api/history immediately after
        seeing status='done' would briefly miss the brand-new upload.
        Accepting in-memory done/ready jobs closes that race.
    Pure helper — no side-effects, no pruning. Used by /api/history
    so the sidebar never shows entries that would 404 on click, while
    still surfacing freshly-uploaded sets without a hard reload."""
    if not jid:
        return False
    if _load_job_snapshot(jid) is not None:
        return True
    with jobs_lock:
        job = jobs.get(jid)
        if job and str(job.get('status', '')).lower() in (
                'done', 'ready', 'complete', 'completed'):
            return True
    return False


@app.route('/api/history')
def job_history():
    # SESSIE 28 — auth + user-scoped filter. Before, this returned every job
    # on disk to every caller, so a second account on the same local install
    # saw the first account's library. Anonymous callers now get an empty
    # list; signed-in callers see only their own jobs.
    #
    # Backfill heuristic: entries without user_id are treated as legacy /
    # pre-multi-user state. They're invisible to all accounts going forward
    # (private by default — no leak). They're left on disk so an admin can
    # still rescue them.
    auth_header = request.headers.get('Authorization', '')
    user_id = None
    if auth_header.lower().startswith('bearer '):
        token = auth_header[7:].strip()
        user_info = auth_get_user_from_token(token)
        if user_info:
            user_id = user_info['user_id']
    if not user_id:
        return jsonify([])
    return jsonify([h for h in _load_history()
                    if h.get('user_id') == user_id
                    and _history_entry_is_loadable(h.get('id'))])


@app.route('/api/history/<job_id>', methods=['DELETE'])
def job_history_delete(job_id):
    """Remove a single entry from job history (and any orphan output dir).
    SESSIE 28 — auth + ownership check. Only the user who owns the entry
    can delete it."""
    if not _valid_job_id(job_id):
        return jsonify({'error': 'Invalid job id'}), 400
    user_info, err = _require_authed_user()
    if err:
        return err
    history = _load_history()
    # Find target entry first so we can check ownership before mutating.
    target = next((h for h in history if h.get('id') == job_id), None)
    if target is None:
        return jsonify({'error': 'Not in history'}), 404
    if target.get('user_id') != user_info['user_id']:
        # Don't reveal existence to other users — return same 404 as missing.
        return jsonify({'error': 'Not in history'}), 404
    new_history = [h for h in history if h.get('id') != job_id]
    _save_history(new_history)
    # Best-effort cleanup of output dir if it exists
    out_dir = os.path.join(OUTPUT_DIR, job_id)
    if os.path.isdir(out_dir):
        try:
            shutil.rmtree(out_dir)
        except OSError as e:
            log.warning("Could not remove output dir for %s: %s", job_id, e)
    with jobs_lock:
        jobs.pop(job_id, None)
    return jsonify({'ok': True, 'remaining': len(new_history)})


@app.route('/api/upload', methods=['POST'])
@limiter.limit("20 per hour", key_func=_rate_limit_key)
def upload():
    # Phase 3: auth + quota gate runs BEFORE file save. Anonymous calls or
    # expired tokens get 401, plan limit reached gets 402 — neither writes
    # bytes to disk or starts ffmpeg.
    user_info, err = _require_authed_user()
    if err:
        return err
    user_id = user_info['user_id']
    snap = _get_or_refresh_profile(user_id, access_token=user_info.get('access_token'))
    if not snap.get('ok'):
        return jsonify({'ok': False, 'error': snap.get('error', 'profile read failed')}), 500
    if snap['used'] >= snap['limit']:
        return _quota_block_response(snap)

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    safe_name = _safe_filename(file.filename)
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ('.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.flv'):
        return jsonify({'error': f'Unsupported file type: {ext}. Use MP4, MOV, AVI, MKV.'}), 400

    # Form parsing helpers with targeted exception handling
    def form_int(key, default):
        try:
            return int(request.form.get(key, default))
        except (TypeError, ValueError):
            return default

    def form_float(key, default):
        try:
            return float(request.form.get(key, default))
        except (TypeError, ValueError):
            return default

    clip_duration   = max(5,  min(300, form_int('clip_duration', 30)))
    min_gap         = max(5,  min(300, form_int('min_gap', 30)))
    bars_before     = max(1,  min(32,  form_int('bars_before', 4)))
    bars_after      = max(1,  min(32,  form_int('bars_after', 4)))
    sensitivity     = max(0.0, min(1.0, form_float('sensitivity', 0.5)))
    formats         = request.form.getlist('formats') or ['landscape', 'vertical']
    use_demucs      = request.form.get('use_demucs', 'false').lower() == 'true'
    normalize_audio = request.form.get('normalize_audio', 'false').lower() == 'true'

    formats = [f for f in formats if f in ('landscape', 'vertical')]
    if not formats:
        formats = ['landscape', 'vertical']

    # Text overlay — sanitise to prevent ffmpeg filter injection
    overlay_text = None
    overlay_text_raw = request.form.get('overlay_text', '').strip()
    if overlay_text_raw:
        safe_text = re.sub(r"['\\\[\]{}=]", '', overlay_text_raw)[:120]
        overlay_text = {
            'text': safe_text,
            'position': request.form.get('overlay_position', 'bottom'),
            'font_size': form_int('overlay_font_size', 0),
        }

    # Save upload (stream to disk, 16 MB chunks)
    job_id = str(uuid.uuid4())[:8]
    video_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")
    CHUNK = 16 * 1024 * 1024
    written = 0
    try:
        with open(video_path, 'wb') as out_f:
            while True:
                chunk = file.stream.read(CHUNK)
                if not chunk:
                    break
                out_f.write(chunk)
                written += len(chunk)
    except OSError as e:
        # Try to clean up partial upload
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except OSError:
            pass
        return jsonify({'error': f'Could not save upload: {e}'}), 500

    log.info("Upload complete: %s → %s (%.0f MB)", safe_name, video_path, written / 1e6)

    # Scaled disk-space check: require roughly 2× the upload size (min 2 GB)
    upload_gb = written / (1024 ** 3)
    required_gb = max(2.0, upload_gb * 2)
    ok, free_gb = _check_disk_space(OUTPUT_DIR, required_gb=required_gb)
    if not ok:
        try:
            os.remove(video_path)
        except OSError:
            pass
        return jsonify({
            'error': f'Not enough disk space ({free_gb} GB free, need ~{required_gb:.1f} GB).'
        }), 507

    # Validate file with ffprobe (detects corrupt/non-video files)
    valid, info = _validate_video_file(video_path)
    if not valid:
        try:
            os.remove(video_path)
        except OSError:
            pass
        return jsonify({'error': f'Invalid video file: {info}'}), 422

    # Persist settings
    _save_settings({
        'clip_duration': clip_duration, 'min_gap': min_gap,
        'sensitivity': sensitivity, 'formats': formats,
        'use_demucs': use_demucs, 'normalize_audio': normalize_audio,
        'bars_before': bars_before, 'bars_after': bars_after,
    })

    # Create job (lock protects the shared jobs dict)
    # Phase-4 deelstap 2c — `fps` captured during ffprobe validation is kept
    # at job-level. _get_snapshot() injects it into every clip below so the
    # editor can display a frame counter without an extra round-trip.
    with jobs_lock:
        jobs[job_id] = {
            'id': job_id,
            'filename': safe_name,
            'video_path': video_path,
            'user_id': user_id,                # Phase 3: who to bill for this set
            'access_token': user_info.get('access_token'),  # SESSIE 30: routed through update-usage edge function when no service_role
            'workspace_id': current_workspace_id(user_info, required=False)[0],  # SESSIE 74 fase 2b: brand-scope van de job
            'usage_counted': False,            # Phase 3: idempotency for increment
            'status': 'queued',
            'message': 'Upload complete, starting analysis...',
            'clips': [], 'results': [], 'waveform': [], 'filmstrip': [],
            'duration': 0, 'video_info': {}, 'bpm': {},
            'fps': info.get('fps') if isinstance(info, dict) else None,
            'favorites': [],
            'settings': {
                'clip_duration': clip_duration, 'min_gap': min_gap,
                'sensitivity': sensitivity, 'formats': formats,
                'use_demucs': use_demucs, 'normalize_audio': normalize_audio,
                'overlay_text': overlay_text,
                'bars_before': bars_before, 'bars_after': bars_after,
            }
        }

    thread = threading.Thread(
        target=_process_job,
        args=(job_id, video_path, clip_duration, min_gap, formats,
              sensitivity, use_demucs, normalize_audio, overlay_text,
              bars_before, bars_after)
    )
    thread.daemon = True
    thread.start()

    # SESSIE 35 — audit log
    _audit(
        'file.upload',
        user_id=user_id,
        metadata={'job_id': job_id, 'filename': safe_name},
    )

    return jsonify({'job_id': job_id})


# ---------------------------------------------------------------------------
# Bucket-D2: no-copy local-path upload + on-demand render endpoints
# ---------------------------------------------------------------------------
VIDEO_EXTS_ALLOWED = ('.mp4', '.mov', '.m4v', '.mkv', '.wav', '.mp3', '.flac', '.aac', '.aif', '.aiff')


def _scan_folder_for_videos(folder, max_results=20):
    """Return a list of video/audio files inside `folder`, sorted largest-first.
    Used by /api/upload-local when the user paths to a directory."""
    out = []
    try:
        for name in os.listdir(folder):
            p = os.path.join(folder, name)
            if not os.path.isfile(p):
                continue
            if not name.lower().endswith(VIDEO_EXTS_ALLOWED):
                continue
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            out.append({'path': p, 'name': name, 'size': sz})
    except OSError:
        return []
    out.sort(key=lambda x: x['size'], reverse=True)
    return out[:max_results]


@app.route('/api/upload-local/scan', methods=['POST'])
def upload_local_scan():
    """Light-weight folder probe — used by the modal when the user pasted a
    folder path. Returns the up-to-20 largest media files inside, so the
    front-end can render a picker."""
    if not LARGE_FILE_PIPELINE:
        return jsonify({'error': 'Large-file pipeline disabled. Set LARGE_FILE_PIPELINE=1.'}), 403
    data = request.get_json(silent=True) or {}
    raw = (data.get('path') or '').strip()
    if not raw or not os.path.isabs(raw):
        return jsonify({'error': 'Path must be absolute'}), 400
    if not os.path.exists(raw):
        return jsonify({'error': 'Path does not exist'}), 404
    if not os.path.isdir(raw):
        return jsonify({'error': 'Path is not a folder'}), 400
    # SESSIE 67 (S2) — zelfde home-whitelist als upload-local. Voorkomt dat dit
    # endpoint mapinhoud buiten de gebruikersmap lekt (info-disclosure).
    if not _path_within_home(raw):
        return jsonify({'error': 'Map moet binnen je gebruikersmap liggen.',
                        'reason': 'scan_path_outside_home'}), 403
    files = _scan_folder_for_videos(raw)
    return jsonify({'folder': raw, 'count': len(files),
                    'files': files,
                    'allowed_extensions': list(VIDEO_EXTS_ALLOWED)})


@app.route('/api/upload-local', methods=['POST'])
@limiter.limit("20 per hour", key_func=_rate_limit_key)
def upload_local():
    """Register an existing on-disk video path as a job WITHOUT copying.
    Designed for huge sets (10h 4K60 ≈ 250–470 GB) where streaming the bytes
    over the file picker is wasteful and fragile.

    Accepts either a file path OR a folder path. When a folder is given,
    the LARGEST matching media file inside is auto-picked (the typical
    "I dropped my whole sets folder in there" case). Front-end can also
    call /api/upload-local/scan to render a picker first.

    Body (JSON):
      { path: "/Users/.../big-set.mp4",  // required, absolute
        clip_duration?, min_gap?, sensitivity?, formats?,
        use_demucs?, normalize_audio?, overlay_text?,
        bars_before?, bars_after? }
    """
    if not LARGE_FILE_PIPELINE:
        return jsonify({'error': 'Large-file pipeline disabled. Set LARGE_FILE_PIPELINE=1.'}), 403

    # Phase 3: auth + quota gate. Same logic as /api/upload — must run before
    # any file validation / proxy work so a quota-blocked user sees the
    # upgrade modal instantly.
    user_info, err = _require_authed_user()
    if err:
        return err
    user_id = user_info['user_id']
    snap = _get_or_refresh_profile(user_id, access_token=user_info.get('access_token'))
    if not snap.get('ok'):
        return jsonify({'ok': False, 'error': snap.get('error', 'profile read failed')}), 500
    if snap['used'] >= snap['limit']:
        return _quota_block_response(snap)

    data = request.get_json(silent=True) or {}
    raw_path = (data.get('path') or '').strip()
    if not raw_path:
        return jsonify({'error': 'Missing "path"'}), 400
    # Defensive: reject relative paths and traversal — must be absolute.
    if not os.path.isabs(raw_path):
        return jsonify({'error': 'Path must be absolute (start with /)'}), 400
    if not os.path.exists(raw_path):
        return jsonify({'error': f'Path does not exist: {raw_path}'}), 404

    # Folder shorthand — pick the largest media file inside.
    if os.path.isdir(raw_path):
        candidates = _scan_folder_for_videos(raw_path)
        if not candidates:
            return jsonify({
                'error': f'No video/audio files found in folder. '
                         f'Looking for: {", ".join(VIDEO_EXTS_ALLOWED)}'
            }), 404
        raw_path = candidates[0]['path']
        log.info("upload-local: folder shorthand — picked largest file: %s", raw_path)

    if not os.path.isfile(raw_path):
        return jsonify({'error': f'Path is not a file: {raw_path}'}), 400

    # SESSIE 67 (S2) — home-whitelist. De export-map was al beperkt tot de
    # gebruikersmap; we doen hetzelfde voor het INPUT-pad. Voorkomt dat (via een
    # CSRF/DNS-rebinding-poging, of een rogue client) een willekeurig systeembestand
    # buiten de home-map als "DJ-set" geregistreerd en geserveerd wordt
    # (bv. /etc/passwd, ~/.ssh/...). realpath dekt symlink-uitwegen af.
    if not _path_within_home(raw_path):
        return jsonify({
            'error': 'Voor de veiligheid mag het bronbestand alleen binnen je '
                     'gebruikersmap liggen (~/Desktop, ~/Documents, ~/Downloads, '
                     '~/Movies of subfolders daarvan).',
            'reason': 'input_path_outside_home',
        }), 403

    # Reject extensions we can't actually read with ffmpeg
    ext = os.path.splitext(raw_path)[1].lower()
    if ext and ext not in VIDEO_EXTS_ALLOWED:
        return jsonify({
            'error': f'Unsupported file type "{ext}". '
                     f'Allowed: {", ".join(VIDEO_EXTS_ALLOWED)}'
        }), 415

    valid, info = _validate_video_file(raw_path)
    if not valid:
        return jsonify({'error': f'Invalid video file: {info}'}), 422

    # Disk-space pre-flight: rough estimate scales with duration, not file size,
    # because the OUTPUT_DIR holds the cut clips not the source video.
    duration = float(info.get('duration', 0)) if isinstance(info, dict) else 0.0
    est_gb = max(2.0, (duration * PROXY_BITS_PER_SEC) / (1024 ** 3) * 1.5)
    ok, free_gb = _check_disk_space(OUTPUT_DIR, required_gb=est_gb)
    if not ok:
        return jsonify({'error': f'Not enough output disk space ({free_gb} GB free, '
                                  f'~{est_gb:.1f} GB needed for proxies)'}), 507

    job_id = str(uuid.uuid4())[:8]
    safe_name = _safe_filename(os.path.basename(raw_path))
    settings = _load_settings()
    def _g(k, dflt):
        v = data.get(k, settings.get(k, dflt))
        return v
    clip_duration   = max(5,  min(300, int(_g('clip_duration', 30))))
    min_gap         = max(5,  min(300, int(_g('min_gap', 30))))
    bars_before     = max(1,  min(32,  int(_g('bars_before', 4))))
    bars_after      = max(1,  min(32,  int(_g('bars_after', 4))))
    sensitivity     = max(0.0, min(1.0, float(_g('sensitivity', 0.5))))
    formats         = data.get('formats') or settings.get('formats') or ['landscape', 'vertical']
    formats         = [f for f in formats if f in ('landscape', 'vertical')] or ['landscape', 'vertical']
    use_demucs      = bool(_g('use_demucs', False))
    normalize_audio = bool(_g('normalize_audio', False))
    overlay_text    = _g('overlay_text', None)

    with jobs_lock:
        jobs[job_id] = {
            'id': job_id,
            'filename': safe_name,
            'video_path': raw_path,           # SOURCE LIVES IN PLACE — do not delete on cleanup
            'no_copy': True,
            'user_id': user_id,                # Phase 3: who to bill for this set
            'access_token': user_info.get('access_token'),  # SESSIE 30: routed through update-usage edge function when no service_role
            'workspace_id': current_workspace_id(user_info, required=False)[0],  # SESSIE 74 fase 2b: brand-scope van de job
            'usage_counted': False,            # Phase 3: idempotency for increment
            'status': 'queued',
            'message': 'Local source registered — starting analysis...',
            'clips': [], 'results': [], 'waveform': [], 'filmstrip': [],
            'duration': duration, 'video_info': info if isinstance(info, dict) else {},
            'fps': info.get('fps') if isinstance(info, dict) else None,  # Phase 4 deelstap 2c
            'bpm': {}, 'favorites': [],
            'settings': {
                'clip_duration': clip_duration, 'min_gap': min_gap,
                'sensitivity': sensitivity, 'formats': formats,
                'use_demucs': use_demucs, 'normalize_audio': normalize_audio,
                'overlay_text': overlay_text,
                'bars_before': bars_before, 'bars_after': bars_after,
            },
        }

    thread = threading.Thread(
        target=_process_job,
        args=(job_id, raw_path, clip_duration, min_gap, formats,
              sensitivity, use_demucs, normalize_audio, overlay_text,
              bars_before, bars_after)
    )
    thread.daemon = True
    thread.start()
    return jsonify({'job_id': job_id, 'no_copy': True, 'estimated_gb': round(est_gb, 1)})


# ---------------------------------------------------------------------------
# SESSIE 71 — C2: Import a finished short straight into the editor.
# ADDITIVE endpoint. It does NOT touch the analyse/cut pipeline. It saves the
# uploaded video into a fresh job folder, probes it, makes a thumbnail, and
# registers it as a single-clip "done" job so it opens in the editor for
# trim / captions / brand / export. No drop-analysis runs (no quota cost).
# Local-first: the file lives under OUTPUT_DIR/<job_id>/ (DATA_DIR), exactly
# like every other job, and is private to the caller via job['user_id'].
# When the multi-tenant data-layer (A1) lands this becomes workspace-scoped.
# ---------------------------------------------------------------------------
_IMPORT_VIDEO_EXT = {'.mp4', '.mov', '.m4v', '.webm'}


@app.route('/api/import-clip', methods=['POST'])
def api_import_clip():
    user_info, err = _require_authed_user()
    if err:
        return err
    user_id = user_info['user_id']

    file = request.files.get('file')
    if file is None or not file.filename:
        return jsonify({'ok': False, 'error': 'No file provided'}), 400
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in _IMPORT_VIDEO_EXT:
        return jsonify({'ok': False,
                        'error': 'Unsupported file type. Import a video (mp4, mov, m4v, webm).'}), 415

    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    try:
        os.makedirs(job_dir, exist_ok=True)
    except OSError as e:
        return jsonify({'ok': False, 'error': f'Could not create job folder: {e}'}), 500

    safe_name = _safe_filename(os.path.basename(file.filename)) or ('import' + ext)
    if not os.path.splitext(safe_name)[1]:
        safe_name += ext
    dest = os.path.join(job_dir, safe_name)
    try:
        file.save(dest)
    except OSError as e:
        return jsonify({'ok': False, 'error': f'Could not save file: {e}'}), 500

    # Probe duration / dimensions (best-effort; ffprobe via cutter.get_video_info).
    info = {}
    duration = 0.0
    try:
        info = get_video_info(dest) or {}
        duration = float(info.get('duration') or 0.0)
    except Exception as e:
        log.warning("import-clip: probe failed for %s: %s", dest, e)
    if duration < 0:
        duration = 0.0

    # Thumbnail near the start (midpoint for very short clips).
    thumb_name = 'thumb_clip01.jpg'
    try:
        ts = min(1.0, duration / 2.0) if duration > 0 else 0.0
        generate_thumbnail(dest, ts, os.path.join(job_dir, thumb_name))
    except Exception as e:
        log.warning("import-clip: thumbnail failed: %s", e)
        thumb_name = None

    base_label = os.path.splitext(safe_name)[0]
    # Single clip that spans the whole file. Same object in clips[] and
    # results[] so both the editor (reads clips) and the Clips view (reads
    # results) find the playable `files`. All ratios point at the imported
    # file; the export pipeline reframes per-ratio from video_path as usual.
    clip = {
        'index': 1,
        'type': 'import',
        'start': 0.0,
        'end': duration,
        'duration': duration,
        'peak_time': 0.0,
        'score': 1.0,
        'caption': base_label,
        'files': {
            'landscape': safe_name,
            'vertical': safe_name,
            'square': safe_name,
            'portrait45': safe_name,
        },
    }
    if thumb_name:
        clip['thumbnail'] = thumb_name

    job = {
        'id': job_id,
        'filename': safe_name,
        'video_path': dest,            # source == the imported file (recut/export read this)
        'no_copy': False,
        'user_id': user_id,
        'usage_counted': True,         # imports don't consume analysis quota
        'imported': True,
        'status': 'done',
        'message': 'Imported clip ready.',
        'clips': [clip],
        'results': [clip],
        'waveform': [], 'filmstrip': [],
        'duration': duration,
        'video_info': info if isinstance(info, dict) else {},
        'fps': info.get('fps') if isinstance(info, dict) else None,
        'bpm': {}, 'favorites': [],
        'settings': {},
    }
    with jobs_lock:
        jobs[job_id] = job
    try:
        _append_to_history(job)   # writes history entry + persists snapshot
    except Exception as e:
        log.warning("import-clip: history/snapshot persist failed: %s", e)
    try:
        _audit('import_clip', user_id=user_id, metadata={'job_id': job_id, 'ext': ext})
    except Exception:
        pass

    return jsonify({'ok': True, 'job_id': job_id, 'clip_index': 0, 'duration': duration})


@app.route('/api/storage', methods=['GET'])
def api_storage_summary():
    """Storage panel feed — output-dir size + free disk + pipeline flag.
    Used by Settings → Storage section."""
    total = 0
    job_count = 0
    try:
        for name in os.listdir(OUTPUT_DIR):
            p = os.path.join(OUTPUT_DIR, name)
            if os.path.isdir(p):
                job_count += 1
                for root, _dirs, files in os.walk(p):
                    for fn in files:
                        try:
                            total += os.path.getsize(os.path.join(root, fn))
                        except OSError:
                            pass
    except FileNotFoundError:
        pass
    free_gb = 0
    try:
        usage = shutil.disk_usage(OUTPUT_DIR)
        free_gb = usage.free / (1024 ** 3)
    except OSError:
        pass
    return jsonify({
        'output_dir': OUTPUT_DIR,
        'output_size_bytes': total,
        'job_count': job_count,
        'free_gb': round(free_gb, 1),
        'large_file_pipeline': LARGE_FILE_PIPELINE,
        'large_threshold_seconds': LARGE_DURATION_THRESHOLD,
    })


@app.route('/api/storage/cleanup-proxies', methods=['POST'])
def api_storage_cleanup_proxies():
    """Remove proxy clip files (`*_proxy.mp4`) across all jobs. Full-quality
    cuts, thumbnails, filmstrips and waveform caches are preserved."""
    removed = 0
    bytes_freed = 0
    try:
        for name in os.listdir(OUTPUT_DIR):
            jdir = os.path.join(OUTPUT_DIR, name)
            if not os.path.isdir(jdir):
                continue
            for fn in os.listdir(jdir):
                if fn.endswith('_proxy.mp4'):
                    fp = os.path.join(jdir, fn)
                    try:
                        sz = os.path.getsize(fp)
                        os.remove(fp)
                        removed += 1
                        bytes_freed += sz
                    except OSError as e:
                        log.warning("could not remove proxy %s: %s", fp, e)
    except FileNotFoundError:
        pass
    # Drop proxy paths from in-memory job state too
    with jobs_lock:
        for j in jobs.values():
            for coll in (j.get('results'), j.get('clips')):
                for r in coll or []:
                    files = r.get('files') or {}
                    files.pop('proxy', None)
    return jsonify({'success': True, 'removed': removed, 'bytes_freed': bytes_freed})


@app.route('/api/disk-estimate', methods=['POST'])
def disk_estimate():
    """Return a rough disk-space estimate for the upload the user is about
    to start. Used to gate huge sets before bytes get copied.
    Body: { duration_seconds?, file_size_bytes? }
    """
    data = request.get_json(silent=True) or {}
    dur  = float(data.get('duration_seconds') or 0)
    size = float(data.get('file_size_bytes') or 0)
    proxy_gb = (dur * PROXY_BITS_PER_SEC) / (1024 ** 3)
    full_gb  = (dur * FULL_BITS_PER_SEC)  / (1024 ** 3)
    upload_gb = size / (1024 ** 3)
    free_gb_ok, free_gb = _check_disk_space(OUTPUT_DIR, required_gb=max(2.0, proxy_gb * 1.2))
    return jsonify({
        'upload_gb':       round(upload_gb, 2),
        'proxy_gb':        round(proxy_gb, 2),
        'full_quality_gb': round(full_gb, 2),
        'free_gb':         round(free_gb, 1),
        'fits_proxies':    bool(free_gb_ok),
        'recommend_local_path': bool(upload_gb > 8 or dur > LARGE_DURATION_THRESHOLD),
    })


@app.route('/api/render-clip/<job_id>', methods=['POST'])
def api_render_clip(job_id):
    """On-demand full-quality cut of ONE clip from the source video. Used
    by the editor when the user opens a clip that only has a proxy file, or
    by the export flow before publishing. Returns when the file is ready.

    Body: { clip_index, formats?: ['vertical','landscape'] }
    """
    _user, _job, err = _require_job_access(job_id)
    if err:
        return err
    data = request.json or {}
    try:
        clip_index = int(data.get('clip_index', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid clip_index'}), 400
    formats = data.get('formats') or ['vertical', 'landscape']
    formats = [f for f in formats if f in ('landscape', 'vertical')] or ['vertical']

    snap = _get_snapshot(job_id)
    if not snap:
        return jsonify({'error': 'Job not found'}), 404
    video_path = snap.get('video_path')
    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': 'Source video missing — cannot re-render'}), 410
    target = next((r for r in (snap.get('results') or snap.get('clips') or [])
                   if r.get('index') == clip_index), None)
    if not target:
        return jsonify({'error': 'clip not found'}), 404
    have = (target.get('files') or {})
    needed = [f for f in formats if not have.get(f)]
    if not needed:
        return jsonify({'success': True, 'cached': True,
                        'files': {k: os.path.basename(v) for k, v in have.items()}})

    # Run the full-quality encode (synchronous — typically 5–20 s per clip).
    try:
        result = process_clip_full(
            video_path, target,
            os.path.join(OUTPUT_DIR, job_id),
            formats=needed,
            overlay_text=(snap.get('settings') or {}).get('overlay_text'),
            normalize_audio=(snap.get('settings') or {}).get('normalize_audio', False),
        )
    except Exception as e:
        return jsonify({'error': f'Render failed: {e}'}), 500

    # Merge new variant paths back onto the job's results
    new_files = (result.get('files') or {})
    with jobs_lock:
        for coll_name in ('results', 'clips'):
            for r in jobs[job_id].get(coll_name, []) or []:
                if r.get('index') == clip_index:
                    files = r.setdefault('files', {})
                    files.update(new_files)
                    if result.get('thumbnail') and not r.get('thumbnail'):
                        r['thumbnail'] = result['thumbnail']
    try:
        latest = _get_snapshot(job_id)
        if latest:
            _persist_job_snapshot(latest)
    except Exception as e:
        log.warning("render-clip persist failed: %s", e)
    return jsonify({
        'success': True,
        'cached':  False,
        'files':   {k: os.path.basename(v) for k, v in new_files.items()},
    })


@app.route('/api/status/<job_id>')
def job_status(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if snap is None:
        return jsonify({'error': 'Job not found'}), 404

    # Hydrate per-clip favorite + custom_label flags onto each result so the
    # frontend doesn't have to cross-reference favorites[] and clip_labels{}
    # separately. This makes the Clips view + Editor render correctly on a
    # cold reload (the renderer reads c.favorite / c.custom_label directly).
    favorites_set = set(snap.get('favorites', []) or [])
    labels = (snap.get('clip_labels') or {}) if isinstance(snap.get('clip_labels'), dict) else {}
    def _enrich(items):
        out = []
        for r in (items or []):
            if not isinstance(r, dict):
                out.append(r)
                continue
            r = dict(r)
            ci = r.get('index')
            r['favorite']    = ci in favorites_set
            r['is_favorite'] = r['favorite']
            lbl = labels.get(str(ci)) if ci is not None else None
            if lbl:
                r['custom_label'] = lbl
                r['renamed']      = True
            out.append(r)
        return out

    # Recut-capability flag — true only when the source upload still
    # exists on disk. Pre-existing jobs whose /tmp upload was wiped will
    # have recut_capable=False; the editor uses this to disable the Trim
    # button with a clear tooltip instead of returning a 500/404 on click.
    vp = snap.get('video_path')
    recut_capable = bool(vp and os.path.exists(vp))
    return jsonify({
        'id': snap['id'],
        'filename': snap['filename'],
        'status': snap['status'],
        'message': snap['message'],
        'clips':   _enrich(snap.get('clips', [])),
        'results': _enrich(snap.get('results', [])),
        'duration': snap.get('duration', 0),
        'video_info': snap.get('video_info', {}),
        'bpm': snap.get('bpm', {}),
        'favorites': snap.get('favorites', []),
        'clip_labels': labels,
        'settings': snap.get('settings', {}),
        'progress': snap.get('progress', {}),
        'filmstrip': snap.get('filmstrip', []),
        'recut_capable': recut_capable,
        'recut_blocked_reason': None if recut_capable else (
            'video_path_missing' if not vp else 'source_file_gone'
        ),
        # SESSIE 68 — surface the captured traceback on error jobs so the real
        # failing line is visible even in the stdout-swallowed packaged app.
        'traceback': snap.get('traceback'),
    })


@app.route('/api/waveform/<job_id>/clip/<int:clip_index>')
def job_waveform_clip(job_id, clip_index):
    """High-resolution per-clip waveform — used by the editor's canvas
    waveform renderer (Task #7). Cached on disk under <job>/wave_cache/.
    Query params: bins (default 600).
    """
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if snap is None:
        return jsonify({'error': 'Job not found'}), 404
    try:
        bins = max(60, min(2000, int(request.args.get('bins', 600))))
    except (TypeError, ValueError):
        bins = 600

    target = next((r for r in (snap.get('results') or snap.get('clips') or [])
                   if r.get('index') == clip_index), None)
    if not target:
        return jsonify({'error': 'clip not found'}), 404

    start = float(target.get('start', 0))
    end   = float(target.get('end', start + 15))
    cache_dir = os.path.join(OUTPUT_DIR, job_id, 'wave_cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f'clip{clip_index:03d}_{bins}.json')
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return jsonify(json.load(f))
        except (OSError, ValueError):
            pass

    # Source = the same WAV used for analysis (faster than re-decoding the
    # source video from scratch each time).
    audio_path = os.path.join(UPLOAD_DIR, f"{job_id}.wav")
    if not os.path.exists(audio_path):
        # Fallback: derive from the source video (slower, but still works
        # for jobs whose UPLOAD_DIR was purged after a restart).
        audio_path = snap.get('video_path')
    if not audio_path or not os.path.exists(audio_path):
        return jsonify({'error': 'audio source unavailable for waveform'}), 410

    peaks = get_per_clip_waveform(audio_path, start, end, bins=bins)
    if peaks is None:
        return jsonify({'error': 'waveform compute failed'}), 500
    payload = {'peaks': peaks, 'bins': len(peaks),
               'start': start, 'end': end, 'cached': False}
    try:
        with open(cache_path, 'w') as f:
            json.dump(payload, f)
    except OSError as e:
        log.warning("waveform cache write failed: %s", e)
    return jsonify(payload)


@app.route('/api/waveform/<job_id>')
def job_waveform(job_id):
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if snap is None:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify({'waveform': snap.get('waveform', [])})


@app.route('/api/recut/<job_id>', methods=['POST'])
def recut(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err

    data = request.json or {}
    try:
        start = float(data['start'])
        end   = float(data['end'])
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'start and end are required floats'}), 400

    if not (end > start):
        return jsonify({'error': f'end ({end}) must be greater than start ({start})'}), 400

    try:
        clip_index = int(data.get('clip_index', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'clip_index must be an integer'}), 400
    clip_type = str(data.get('clip_type', 'drop'))[:20]

    # ---- Resolve job + target clip with full pre-flight validation. ----
    # Older code only checked `results` and assumed `video_path`/settings
    # were present, then any KeyError leaked out as an HTML 500 page that
    # the frontend could only show as raw markup. We now look in both
    # `results` and `clips` (analyzer output that hasn't been cut yet —
    # the lazy-render case the editor reaches when stretching a clip
    # marked "not yet rendered") and return a clean JSON error if any
    # required field is missing, so the user sees an actionable message.
    with jobs_lock:
        job = jobs.get(job_id) or {}
        results_list = list(job.get('results') or [])
        clips_list   = list(job.get('clips') or [])
        target = next((r for r in results_list if r.get('index') == clip_index), None)
        if target is None:
            target = next((r for r in clips_list if r.get('index') == clip_index), None)
        settings  = job.get('settings') or {}
        video_path = job.get('video_path')
        formats         = data.get('formats', settings.get('formats') or ['landscape', 'vertical'])
        overlay_text    = data.get('overlay_text', settings.get('overlay_text'))
        normalize_audio = data.get('normalize_audio', settings.get('normalize_audio', False))

    if target is None:
        return jsonify({
            'error': f'Clip index {clip_index} not found in this job.',
            'reason': 'clip_not_found',
            'available_results': [r.get('index') for r in results_list],
            'available_clips':   [c.get('index') for c in clips_list],
        }), 404
    if not video_path:
        return jsonify({
            'error': 'Source video path is missing on this job — cannot re-cut.',
            'reason': 'video_path_missing',
        }), 400
    if not os.path.exists(video_path):
        return jsonify({
            'error': f'Source video file not found on disk: {os.path.basename(str(video_path))}. '
                     f'It may have been moved or /tmp was cleaned.',
            'reason': 'video_path_not_on_disk',
            'video_path': video_path,
        }), 404
    # Sanity-check that the requested range fits inside the source video
    # so we don't ask ffmpeg to cut past EOF (which silently produces a
    # zero-byte clip and the user would then see an empty preview).
    src_duration = float(job.get('duration') or 0)
    if src_duration > 0 and end > src_duration + 0.5:
        return jsonify({
            'error': f'End time ({end:.2f}s) is past the source video duration ({src_duration:.2f}s).',
            'reason': 'end_past_source',
            'source_duration': src_duration,
        }), 400

    job_output_dir = os.path.join(OUTPUT_DIR, job_id)

    try:
        files = recut_clip(
            video_path, start, end, job_output_dir,
            clip_index, clip_type, formats,
            overlay_text=overlay_text, normalize_audio=normalize_audio
        )
        # Update the target result under the lock. Promote the clip from
        # `clips` to `results` if it didn't exist there yet (lazy-render
        # case) so subsequent edits + exports find it.
        with jobs_lock:
            j = jobs.get(job_id) or {}
            results = j.setdefault('results', [])
            existing = next((r for r in results if r.get('index') == clip_index), None)
            if existing is None:
                # Promote analyzer-only clip into results with the new range.
                promoted = dict(target)
                promoted.update({
                    'index': clip_index,
                    'start': start,
                    'end': end,
                    'duration': round(end - start, 2),
                    'files': files,
                })
                results.append(promoted)
                results.sort(key=lambda r: float(r.get('start', 0)))
            else:
                existing['start']    = start
                existing['end']      = end
                existing['duration'] = round(end - start, 2)
                existing['files']    = files
            # Persist so the new range survives a restart — the previous
            # code only updated in-memory state, which Sjuul also asked to
            # fix ("aanpassingen moeten behouden blijven na uitloggen").
            try:
                snap_after = _get_snapshot(job_id)
                if snap_after:
                    _persist_job_snapshot(snap_after)
            except Exception as _e:
                log.warning("recut: snapshot persist failed: %s", _e)
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        # Catch-all so we never leak an HTML 500 page to the frontend.
        # Include the exception type in the message so failure-mode
        # debugging is fast even without server logs.
        log.exception("Recut failed for job %s clip %s", job_id, clip_index)
        return jsonify({
            'error': f"{type(e).__name__}: {e}",
            'reason': 'recut_internal_error',
        }), 500


@app.route('/api/slice/<job_id>', methods=['POST'])
def slice_endpoint(job_id):
    """SESSIE 43a — Trim-only endpoint, gebruikt door de editor's Trim-knop.

    Verschil met /api/recut: doet GEEN drawtext/logo/watermark/pan-keyframes
    inbakken. Alleen ffmpeg trim op (start, end). Editor toont overlays nog
    steeds als live WYSIWYG laag bovenop het video-element — pre-bake gebeurt
    pas in de export-pipeline.

    De track-mode + keyframes (pan/zoom/letterbox) komen wel mee omdat dat
    een geometrische crop is, geen overlay — zonder die crop wijkt de vertical
    output zichtbaar af van wat de editor toont.

    Payload, body en preflight-validation matchen /api/recut zodat de
    frontend simpel kan omschakelen: alleen URL hoeft te wijzigen.
    """
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err

    data = request.json or {}
    try:
        start = float(data['start'])
        end   = float(data['end'])
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'start and end are required floats'}), 400

    if not (end > start):
        return jsonify({'error': f'end ({end}) must be greater than start ({start})'}), 400

    try:
        clip_index = int(data.get('clip_index', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'clip_index must be an integer'}), 400
    clip_type = str(data.get('clip_type', 'drop'))[:20]

    with jobs_lock:
        job = jobs.get(job_id) or {}
        results_list = list(job.get('results') or [])
        clips_list   = list(job.get('clips') or [])
        target = next((r for r in results_list if r.get('index') == clip_index), None)
        if target is None:
            target = next((r for r in clips_list if r.get('index') == clip_index), None)
        settings  = job.get('settings') or {}
        video_path = job.get('video_path')
        formats         = data.get('formats', settings.get('formats') or ['landscape', 'vertical'])
        normalize_audio = data.get('normalize_audio', settings.get('normalize_audio', False))

    if target is None:
        return jsonify({
            'error': f'Clip index {clip_index} not found in this job.',
            'reason': 'clip_not_found',
            'available_results': [r.get('index') for r in results_list],
            'available_clips':   [c.get('index') for c in clips_list],
        }), 404
    if not video_path:
        return jsonify({
            'error': 'Source video path is missing on this job — cannot slice.',
            'reason': 'video_path_missing',
        }), 400
    if not os.path.exists(video_path):
        return jsonify({
            'error': f'Source video file not found on disk: {os.path.basename(str(video_path))}.',
            'reason': 'video_path_not_on_disk',
            'video_path': video_path,
        }), 404
    src_duration = float(job.get('duration') or 0)
    if src_duration > 0 and end > src_duration + 0.5:
        return jsonify({
            'error': f'End time ({end:.2f}s) is past the source video duration ({src_duration:.2f}s).',
            'reason': 'end_past_source',
            'source_duration': src_duration,
        }), 400

    job_output_dir = os.path.join(OUTPUT_DIR, job_id)

    try:
        files = slice_clip(
            video_path, start, end, job_output_dir,
            clip_index, clip_type, formats,
            normalize_audio=normalize_audio,
        )
        # Dezelfde results/clips promotion-logica als /api/recut zodat
        # subsequent edits + exports de nieuwe range vinden.
        with jobs_lock:
            j = jobs.get(job_id) or {}
            results = j.setdefault('results', [])
            existing = next((r for r in results if r.get('index') == clip_index), None)
            if existing is None:
                promoted = dict(target)
                promoted.update({
                    'index': clip_index,
                    'start': start,
                    'end': end,
                    'duration': round(end - start, 2),
                    'files': files,
                })
                results.append(promoted)
                results.sort(key=lambda r: float(r.get('start', 0)))
            else:
                existing['start']    = start
                existing['end']      = end
                existing['duration'] = round(end - start, 2)
                existing['files']    = files
            try:
                snap_after = _get_snapshot(job_id)
                if snap_after:
                    _persist_job_snapshot(snap_after)
            except Exception as _e:
                log.warning("slice: snapshot persist failed: %s", _e)
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        log.exception("Slice failed for job %s clip %s", job_id, clip_index)
        return jsonify({
            'error': f"{type(e).__name__}: {e}",
            'reason': 'slice_internal_error',
        }), 500


@app.route('/api/add-marker/<job_id>', methods=['POST'])
def add_marker(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err

    data = request.json or {}
    try:
        peak_time = float(data.get('time', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid time'}), 400

    with jobs_lock:
        job = jobs[job_id]
        clip_duration = int(data.get('clip_duration', job['settings']['clip_duration']))
        total_duration = job.get('duration', 0)
        video_path     = job['video_path']
        formats        = job['settings']['formats']
        overlay_text   = job['settings'].get('overlay_text')
        normalize_audio = job['settings'].get('normalize_audio', False)
        bpm_info = job.get('bpm', {})

    clip = create_manual_clip(peak_time, clip_duration, total_duration)
    if bpm_info.get('bpm'):
        clip['bpm'] = bpm_info['bpm']

    # Insert + re-index under the lock
    with jobs_lock:
        existing = jobs[job_id].get('clips', [])
        clip['index'] = len(existing) + 1
        clip['rank']  = clip['index']
        existing.append(clip)
        existing.sort(key=lambda c: c['start'])
        for i, c in enumerate(existing):
            c['index'] = i + 1
        jobs[job_id]['clips'] = existing

    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    try:
        files = recut_clip(
            video_path, clip['start'], clip['end'],
            job_output_dir, clip['index'], 'manual', formats,
            overlay_text=overlay_text, normalize_audio=normalize_audio
        )
        clip['files'] = files
        with jobs_lock:
            results = jobs[job_id].get('results', [])
            results.append({**clip})
            results.sort(key=lambda c: c['start'])
            for i, r in enumerate(results):
                r['index'] = i + 1
            jobs[job_id]['results'] = results
        return jsonify({'success': True, 'clip': clip})
    except (RuntimeError, OSError, subprocess.SubprocessError) as e:
        log.exception("Add-marker cut failed for job %s", job_id)
        return jsonify({'error': str(e)}), 500


@app.route('/api/favorite/<job_id>', methods=['POST'])
def toggle_favorite(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    data = request.json or {}
    try:
        clip_index = int(data.get('clip_index', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid clip_index'}), 400
    # Optional explicit flag — front-end sends `favorite: true|false` so we
    # don't accidentally double-toggle on rapid double-clicks.
    explicit = data.get('favorite')

    with jobs_lock:
        favorites = jobs[job_id].setdefault('favorites', [])
        already = clip_index in favorites
        if explicit is True and not already:
            favorites.append(clip_index)
        elif explicit is False and already:
            favorites.remove(clip_index)
        elif explicit is None:
            # Legacy toggle path
            if already:
                favorites.remove(clip_index)
            else:
                favorites.append(clip_index)

    # Persist so the favourite survives a server restart (uses the same
    # snapshot path as the rest of job state).
    try:
        snap = _get_snapshot(job_id)
        if snap:
            snap['favorites'] = list(favorites)
            _persist_job_snapshot(snap)
    except Exception as e:
        log.warning("favorite persist failed: %s", e)
    return jsonify({'success': True, 'favorites': list(favorites)})


@app.route('/api/rename/<job_id>', methods=['POST'])
def api_rename_clip(job_id):
    """Rename a single clip's display label.

    Stored as `clip_labels: { "<clip_index>": "<label>" }` on the job
    snapshot. Returned via /api/status as `clip.custom_label` after enrichment.
    SPEC (2026-04-26): right-click any clip name → inline edit → POST here.
    """
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    data = request.json or {}
    try:
        clip_index = int(data.get('clip_index', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid clip_index'}), 400
    raw_label = (data.get('label') or '').strip()
    # Sanitise: strip control chars, length-cap. The label is never used as a
    # filesystem path — but treat it defensively anyway.
    safe = re.sub(r'[\x00-\x1f\x7f]', '', raw_label)[:80]

    with jobs_lock:
        labels = jobs[job_id].setdefault('clip_labels', {})
        if safe:
            labels[str(clip_index)] = safe
        else:
            labels.pop(str(clip_index), None)

    try:
        snap = _get_snapshot(job_id)
        if snap:
            snap['clip_labels'] = dict(jobs[job_id].get('clip_labels', {}))
            _persist_job_snapshot(snap)
    except Exception as e:
        log.warning("rename persist failed: %s", e)
    return jsonify({'success': True, 'clip_index': clip_index, 'label': safe})


def _derive_with_tracking(job_id, target, ratio, source_video_path, tracking_path,
                          job_output_dir):
    """SESSIE 30c - render a 1:1 or 4:5 variant FROM THE ORIGINAL SOURCE
    with the tracked crop applied. Used when the clip has tracking
    keyframes so the DJ stays in frame (instead of getting their head
    centre-cropped off).
    """
    from cutter import _build_tracked_vertical_crop, get_video_info, detect_hw_encoder
    # Load tracking data.
    with open(tracking_path, 'r') as f:
        track = json.load(f) or {}
    keyframes = track.get('keyframes') or []
    crop_mode = track.get('crop_mode') or 'pan'
    if crop_mode not in ('pan', 'zoom', 'letterbox'):
        crop_mode = 'pan'
    # SESSIE 31 — letterbox doesn't need keyframes; pan/zoom still do.
    if crop_mode != 'letterbox' and not keyframes:
        raise RuntimeError('tracking file present but has no keyframes')

    # Resolve source dimensions + clip start/end.
    video_info = get_video_info(source_video_path)
    src_w = video_info.get('width')  or 0
    src_h = video_info.get('height') or 0
    if src_w <= 0 or src_h <= 0:
        raise RuntimeError('could not read source video dimensions')
    start = float(target.get('start') or 0)
    end   = float(target.get('end')   or (start + (target.get('duration') or 10)))
    duration = max(0.5, end - start)

    if ratio == 'square':
        out_w, out_h = 1080, 1080
        target_ratio = 1.0   # w / h
    elif ratio == 'portrait45':
        out_w, out_h = 1080, 1350
        target_ratio = 4.0 / 5.0   # 0.8
    else:
        raise RuntimeError(f'unsupported ratio {ratio}')

    # The pan/zoom helper outputs a crop sized to the keyframe metrics;
    # we then scale+pad to the target out_w x out_h. Pass a custom
    # target_ratio so the pan-mode pre-builds a window of the right
    # aspect for this output.
    crop_expr = _build_tracked_vertical_crop(
        keyframes, src_w, src_h, crop_mode=crop_mode, target_aspect=target_ratio,
    )
    if not crop_expr:
        raise RuntimeError('tracking crop expression empty')

    # SESSIE 31 — letterbox: no crop, just scale-to-fit + pad with black bars.
    if crop_expr == '__LETTERBOX__':
        vf = (
            f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,"
            f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:black"
        )
    else:
        vf = (
            crop_expr + ","
            f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,"
            f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2"
        )

    encoder, quality_args = detect_hw_encoder()
    base = os.path.splitext(os.path.basename(source_video_path))[0]
    out_name = f"{base}_clip{int(target.get('index') or 0):02d}_{target.get('type') or 'drop'}_{ratio}.mp4"
    out_path = os.path.join(job_output_dir, out_name)

    cmd = [
        media_tools.ffmpeg(), '-y',
        '-ss', str(start),
        '-i', source_video_path,
        '-t', str(duration),
        '-vf', vf,
        '-c:v', encoder, *quality_args,
        '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart',
        out_path,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        if proc.returncode != 0:
            # Retry with libx264 in case VideoToolbox is unavailable.
            log.warning('Tracked derive %s primary encoder failed, retrying with libx264. stderr=%s',
                        ratio, (proc.stderr or '')[-300:])
            cmd2 = list(cmd)
            for i, a in enumerate(cmd2):
                if a == '-c:v':
                    cmd2[i+1] = 'libx264'
                    break
            proc = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'tracked derivation timed out', 'reason': 'timeout'}), 504
    if proc.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError(f'ffmpeg failed: {(proc.stderr or "")[-300:]}')

    # Persist onto the job + snapshot.
    clip_index = int(target.get('index') or 0)
    with jobs_lock:
        for coll_name in ('results', 'clips'):
            for r in jobs[job_id].get(coll_name, []) or []:
                if r.get('index') == clip_index:
                    r.setdefault('files', {})[ratio] = out_path
    try:
        snap = _get_snapshot(job_id)
        if snap:
            _persist_job_snapshot(snap)
    except Exception as e:
        log.warning('tracked derive persist failed: %s', e)
    return jsonify({
        'success': True,
        'filename': out_name,
        'cached': False,
        'tracked': True,
        'crop_mode': crop_mode,
    })


@app.route('/api/derive/<job_id>', methods=['POST'])
def api_derive_ratio(job_id):
    """Derive a 1:1 (square) or 4:5 (portrait) variant of a clip from the
    existing vertical or landscape cut.  Center-crop only — does NOT re-decode
    the source DJ set.  Synchronous response: returns when the file is ready.

    Body: { clip_index, ratio: 'square'|'portrait45' }
    SPEC (2026-04-26): generated lazily when the user clicks 1:1 / 4:5 in
    the editor's ratio rail.
    """
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    data = request.json or {}
    try:
        clip_index = int(data.get('clip_index', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid clip_index'}), 400
    ratio = data.get('ratio', 'square')
    if ratio not in ('square', 'portrait45'):
        return jsonify({'error': 'unsupported ratio'}), 400

    with jobs_lock:
        job_blob = jobs.get(job_id) or {}
        results = list(job_blob.get('results') or job_blob.get('clips') or [])
        source_video_path = job_blob.get('video_path') or job_blob.get('source_path')
    target = next((r for r in results if r.get('index') == clip_index), None)
    if not target:
        return jsonify({'error': 'clip not found'}), 404

    files = target.get('files') or {}
    # Force rebuild parameter so a re-track can refresh the 1:1/4:5 variants.
    force_rebuild = bool(data.get('force'))
    if files.get(ratio) and not force_rebuild:
        return jsonify({'success': True, 'filename': os.path.basename(files[ratio]), 'cached': True})

    # SESSIE 30c - if this clip has tracking, derive the new ratio FROM
    # THE ORIGINAL SOURCE with the tracked crop applied. The legacy
    # behaviour center-cropped from the already-cut vertical/landscape,
    # which sliced the DJ's head off whenever the tracked area was not
    # in the centre. We only fall back to the centre-crop path when
    # there is no tracking file or the source video is missing.
    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    tracking_path = os.path.join(job_output_dir, 'tracking', f'clip_{int(clip_index):03d}.json')
    has_tracking = os.path.exists(tracking_path)
    if has_tracking and source_video_path and os.path.exists(source_video_path):
        try:
            return _derive_with_tracking(
                job_id, target, ratio, source_video_path, tracking_path,
                job_output_dir,
            )
        except Exception as e:
            log.warning('Tracked derive failed for %s clip %s ratio %s: %s; '
                        'falling back to centre-crop', job_id, clip_index, ratio, e)

    # Source = vertical for portrait45 (narrow crop), landscape for square (center crop).
    src = files.get('vertical') if ratio == 'portrait45' else files.get('landscape')
    src = src or files.get('landscape') or files.get('vertical')
    if not src or not os.path.exists(src):
        return jsonify({'error': 'no source variant available - re-cut the clip first'}), 409

    base = os.path.splitext(os.path.basename(src))[0]
    # Strip any existing _vertical/_landscape suffix so the new file lands
    # cleanly: ..._clip07_drop_square.mp4
    for suffix in ('_vertical', '_landscape', '_square', '_portrait45'):
        if base.endswith(suffix):
            base = base[:-len(suffix)]
    out_name = f"{base}_{ratio}.mp4"
    out_path = os.path.join(job_output_dir, out_name)

    # SESSIE 16 — 5d: center-crop filter that picks the LARGEST region of the
    # target aspect ratio that fits inside the source, regardless of whether
    # the source is landscape or portrait.
    #
    # Old (broken) filter: `crop='ih*1:ih':'(iw-ih*1)/2':0,...` — assumed source
    # was landscape (iw >= ih). When the only available source variant was the
    # vertical 9:16 cut (iw=1080, ih=1920), the requested crop width=ih=1920
    # exceeded iw=1080 and `(iw-ih)/2` went negative, so ffmpeg errored with
    # "Failed to configure input pad on Parsed_crop_0". The frontend then
    # surfaced "Could not render 1:1: ffmpeg failed".
    #
    # New filter (R = target aspect = w/h):
    #   w = min(iw, ih*R)         → take target-aspect width, capped by source
    #   h = w / R = min(iw/R, ih) → derive height from target aspect, capped
    #   x = (iw - w) / 2          → centre horizontally
    #   y = (ih - h) / 2          → centre vertically
    # Commas inside min(...) are escaped with `\,` so ffmpeg's filtergraph
    # parser doesn't treat them as filter-chain separators.
    if ratio == 'square':
        # R = 1 → w = h = min(iw, ih)
        crop_filter = (
            "crop=min(iw\\,ih):min(iw\\,ih):"
            "(iw-min(iw\\,ih))/2:(ih-min(iw\\,ih))/2,"
            "scale=1080:1080"
        )
        out_w, out_h = 1080, 1080
    else:  # portrait45 → R = 0.8
        crop_filter = (
            "crop=min(iw\\,ih*0.8):min(iw/0.8\\,ih):"
            "(iw-min(iw\\,ih*0.8))/2:(ih-min(iw/0.8\\,ih))/2,"
            "scale=1080:1350"
        )
        out_w, out_h = 1080, 1350

    cmd = [
        media_tools.ffmpeg(), '-y', '-i', src,
        '-vf', crop_filter,
        '-c:v', 'h264_videotoolbox' if sys.platform == 'darwin' else 'libx264',
        '-b:v', '8M', '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart',
        out_path,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if proc.returncode != 0:
            log.warning("derive ffmpeg returncode=%s stderr=%s",
                        proc.returncode, (proc.stderr or '')[-300:])
            # Retry with libx264 in case VideoToolbox is unavailable
            cmd[cmd.index('-c:v') + 1] = 'libx264'
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'derivation timed out',
                        'reason': 'timeout'}), 504
    if proc.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        # SESSIE 16 — 5d: return a structured error so the frontend can show a
        # useful toast instead of the bare "ffmpeg failed" string.
        stderr_tail = (proc.stderr or '')[-400:]
        reason = 'crop_failed' if 'Parsed_crop' in stderr_tail else (
            'codec_failed' if 'codec' in stderr_tail.lower() else 'ffmpeg_failed'
        )
        return jsonify({
            'error': f'Could not render {ratio} (reason: {reason})',
            'reason': reason,
            'stderr': stderr_tail,
            'target_size': f'{out_w}x{out_h}',
        }), 500

    # Persist the new variant onto the job
    with jobs_lock:
        for coll_name in ('results', 'clips'):
            for r in jobs[job_id].get(coll_name, []) or []:
                if r.get('index') == clip_index:
                    r.setdefault('files', {})[ratio] = out_path
        # Re-snapshot so a restart doesn't lose the derivative path
    try:
        snap = _get_snapshot(job_id)
        if snap:
            _persist_job_snapshot(snap)
    except Exception as e:
        log.warning("derive persist failed: %s", e)
    return jsonify({'success': True, 'filename': out_name, 'cached': False})


@app.route('/api/reorder/<job_id>', methods=['POST'])
def reorder_clips(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    data = request.json or {}
    new_order = data.get('order', [])

    with jobs_lock:
        results = jobs[job_id].get('results', [])
        result_map = {r['index']: r for r in results}
        reordered = []
        for i, idx in enumerate(new_order):
            if idx in result_map:
                r = result_map[idx]
                r['index'] = i + 1
                reordered.append(r)
        jobs[job_id]['results'] = reordered
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# File serving — all use validated job_id + basename-stripped filename
# ---------------------------------------------------------------------------

@app.route('/api/clip/<job_id>/<filename>')
def serve_clip(job_id, filename):
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    filename = os.path.basename(filename)
    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    return send_from_directory(job_output_dir, filename)


# Phase-4 S4.2 — serve the original source video so the editor can show a
# live preview while the user drags handles past the clip boundary into
# the ±60s stretch zones. Range-aware (HTTP 206) so the HTML5 <video>
# element can seek within the file.
#
# Path-traversal safety: we only ever return the path stored in
# job['video_path'] — that string is set by the upload handlers from a
# trusted origin (uploaded file in UPLOAD_DIR or user-confirmed local
# path for `no_copy` jobs). The path is never reconstructed from the
# request, so there's no untrusted segment to traverse.
_SOURCE_MIME_BY_EXT = {
    '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.m4v': 'video/mp4',
    '.mkv': 'video/x-matroska', '.webm': 'video/webm',
    '.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.flac': 'audio/flac',
    '.aac': 'audio/aac', '.aif': 'audio/aiff', '.aiff': 'audio/aiff',
}


@app.route('/api/source/<job_id>')
def serve_source(job_id):
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if snap is None:
        return jsonify({'error': 'Job not found'}), 404
    video_path = snap.get('video_path')
    if not video_path or not isinstance(video_path, str):
        return jsonify({'error': 'Source video not registered for this job'}), 404
    real = os.path.realpath(video_path)
    if not os.path.isfile(real):
        return jsonify({'error': 'Source video not accessible'}), 404
    ext = os.path.splitext(real)[1].lower()
    mime = _SOURCE_MIME_BY_EXT.get(ext, 'application/octet-stream')
    # conditional=True turns on If-Modified-Since + Range support so the
    # browser can seek without re-downloading the whole file.
    return send_file(real, mimetype=mime, conditional=True)


@app.route('/api/thumbnail/<job_id>/<filename>')
def serve_thumbnail(job_id, filename):
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    filename = os.path.basename(filename)
    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    return send_from_directory(job_output_dir, filename)


@app.route('/api/filmstrip/<job_id>/<filename>')
def serve_filmstrip(job_id, filename):
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    filename = os.path.basename(filename)
    filmstrip_dir = os.path.join(OUTPUT_DIR, job_id, 'filmstrip')
    return send_from_directory(filmstrip_dir, filename)


@app.route('/api/download-all/<job_id>')
def download_all(job_id):
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if snap is None:
        return jsonify({'error': 'Job not found'}), 404
    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    # Mirror the favorites-zip safety: never ship an empty/0-byte archive.
    # macOS Archive Utility can't open one and shows a useless error.
    if not os.path.isdir(job_output_dir) or not _dir_has_any_mp4(job_output_dir):
        return jsonify({
            'error': "No rendered clip files for this set yet. "
                     "Process or re-cut a clip first, then try again.",
            'reason': 'no_rendered_files',
        }), 400
    zip_base = os.path.join(OUTPUT_DIR, f"{job_id}_clips")
    shutil.make_archive(zip_base, 'zip', job_output_dir)
    safe_dl = re.sub(r'[^\w\-.]', '_', os.path.splitext(snap['filename'])[0])
    return send_file(
        f"{zip_base}.zip", mimetype='application/zip',
        as_attachment=True, download_name=f"{safe_dl}_clips.zip"
    )


def _dir_has_any_mp4(root):
    """Recursive walk — return True as soon as we find a .mp4. Used by the
    download-all guard so we never build a zip that contains only stub
    folders (and macOS Archive Utility refuses to open afterwards)."""
    try:
        for _r, _dirs, files in os.walk(root):
            if any(f.lower().endswith('.mp4') for f in files):
                return True
    except OSError:
        pass
    return False


@app.route('/api/download-favorites/<job_id>')
def download_favorites(job_id):
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if snap is None:
        return jsonify({'error': 'Job not found'}), 404
    favorites = snap.get('favorites', [])
    if not favorites:
        return jsonify({'error': 'No favourites selected'}), 400

    fav_dir = os.path.join(OUTPUT_DIR, f"{job_id}_favorites")
    zip_base = os.path.join(OUTPUT_DIR, f"{job_id}_favorites")

    # Clean up any stale residue from a previous call
    if os.path.isdir(fav_dir):
        shutil.rmtree(fav_dir, ignore_errors=True)
    if os.path.exists(f"{zip_base}.zip"):
        try:
            os.remove(f"{zip_base}.zip")
        except OSError:
            pass

    os.makedirs(fav_dir, exist_ok=True)
    copied = 0
    missing_clips = []
    try:
        for result in snap.get('results', []):
            if result['index'] in favorites:
                clip_had_file = False
                for _fmt, filepath in result.get('files', {}).items():
                    fname = os.path.basename(filepath)
                    if os.path.exists(filepath):
                        shutil.copy2(filepath, os.path.join(fav_dir, fname))
                        copied += 1
                        clip_had_file = True
                if not clip_had_file:
                    missing_clips.append(result['index'])
        # Refuse to build an empty zip — Archive Utility on macOS can't open
        # a 0-byte archive and shows a confusing truncated error to the user.
        # Return a clean 400 so the frontend can toast the real reason.
        if copied == 0:
            return jsonify({
                'error': "Favourite clips don't have rendered files yet. "
                         "Open each one in the editor (or wait for processing "
                         "to finish) and try again.",
                'reason': 'no_rendered_files',
                'favorites': len(favorites),
                'missing_clips': missing_clips,
            }), 400
        shutil.make_archive(zip_base, 'zip', fav_dir)
    finally:
        shutil.rmtree(fav_dir, ignore_errors=True)

    safe_dl = re.sub(r'[^\w\-.]', '_', os.path.splitext(snap['filename'])[0])
    return send_file(
        f"{zip_base}.zip", mimetype='application/zip',
        as_attachment=True, download_name=f"{safe_dl}_favorites.zip"
    )


@app.route('/api/csv/<job_id>')
def download_csv(job_id):
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if snap is None:
        return jsonify({'error': 'Job not found'}), 404
    csv_path = snap.get('csv_path')
    if not csv_path or not os.path.exists(csv_path):
        return jsonify({'error': 'CSV not available'}), 404
    safe_dl = re.sub(r'[^\w\-.]', '_', os.path.splitext(snap['filename'])[0])
    return send_file(
        csv_path, mimetype='text/csv',
        as_attachment=True, download_name=f"{safe_dl}_clips.csv"
    )


@app.route('/api/upload-social/<job_id>', methods=['POST'])
def upload_social(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if snap is None:
        return jsonify({'error': 'Job not found'}), 404

    data = request.json or {}
    try:
        clip_index = int(data.get('clip_index', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid clip_index'}), 400
    platform = str(data.get('platform', ''))
    title    = str(data.get('title', f'DJ Set Clip #{clip_index}'))[:255]
    fmt      = data.get('format', 'vertical')
    if fmt not in ('landscape', 'vertical'):
        fmt = 'vertical'

    clip_file = None
    for result in snap.get('results', []):
        if result['index'] == clip_index:
            clip_file = result.get('files', {}).get(fmt)
            break

    if not clip_file or not os.path.exists(clip_file):
        return jsonify({'error': 'Clip file not found'}), 404

    upload_fns = {
        'youtube': upload_to_youtube,
        'tiktok':  upload_to_tiktok,
        'instagram': upload_to_instagram,
        'facebook': upload_to_facebook,
    }
    if platform not in upload_fns:
        return jsonify({'error': f'Unknown platform: {platform}'}), 400

    result = upload_fns[platform](clip_file, title)
    return jsonify(result)


@app.route('/api/export-preset/<job_id>', methods=['POST'])
def api_export_preset(job_id):
    """Apply an export preset (tiktok/instagram_reel/youtube_shorts/facebook_post/source)."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if not snap:
        return jsonify({'error': 'Job not found'}), 404

    data = request.json or {}
    try:
        clip_index = int(data['clip_index'])
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'clip_index required'}), 400

    preset = str(data.get('preset', 'source'))
    valid_presets = ('source', 'tiktok', 'instagram_reel', 'youtube_shorts', 'facebook_post')
    if preset not in valid_presets:
        return jsonify({'error': f'Unknown preset: {preset}'}), 400

    result = next((r for r in snap.get('results', []) if r['index'] == clip_index), None)
    if not result:
        return jsonify({'error': 'Clip not found'}), 404

    # Prefer vertical source for 9:16 presets, landscape for square
    if preset in ('tiktok', 'instagram_reel', 'youtube_shorts'):
        source = (result.get('files', {}).get('vertical')
                  or result.get('files', {}).get('landscape'))
    else:
        source = (result.get('files', {}).get('landscape')
                  or result.get('files', {}).get('vertical'))

    if not source or not os.path.exists(source):
        return jsonify({'error': 'Source clip file not found on disk'}), 404

    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    # SESSIE 73 - honor de hernoemde clip-naam in de gedownloade filename.
    # Deze per-card quick-export-popover (frontend _ceExportPreset) raakte de
    # custom_label nooit aan: de output kreeg "<bron-basename>_<preset>.mp4",
    # dus een rename ging bij download verloren (WENS sessie 71/72). Spiegelt nu
    # /api/export: prefer een expliciet 'label' uit de request, anders het
    # persistente clip_labels uit het snapshot, anders de oude bron-naam (geen
    # regressie). _dedupe_output_path voorkomt stil overschrijven bij gelijke
    # labels.
    labels = snap.get('clip_labels') if isinstance(snap.get('clip_labels'), dict) else {}
    custom = None
    req_label = data.get('label')
    if isinstance(req_label, str) and req_label.strip():
        custom = req_label.strip()
    else:
        lv = labels.get(str(clip_index)) if isinstance(labels, dict) else None
        if isinstance(lv, str) and lv.strip():
            custom = lv.strip()
    label_part = _safe_filename_label(custom)
    if not label_part:
        label_part = _safe_filename_label(os.path.splitext(os.path.basename(source))[0]) or 'clip'
    out_path = _dedupe_output_path(os.path.join(job_output_dir, f"{label_part}_{preset}.mp4"))

    try:
        export_with_preset(source, preset, out_path)
        fname = os.path.basename(out_path)
        return jsonify({'success': True, 'filename': fname,
                        'url': f'/api/clip/{job_id}/{fname}'})
    except Exception as e:
        log.exception("Export preset failed job=%s clip=%s", job_id, clip_index)
        return jsonify({'error': str(e)}), 500


@app.route('/api/clip-filmstrip/<job_id>/<int:clip_index>')
def clip_filmstrip(job_id, clip_index):
    """Generate/return filmstrip frames for a specific cut clip (editor timeline)."""
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if not snap:
        return jsonify({'error': 'Job not found'}), 404

    result = next((r for r in snap.get('results', []) if r['index'] == clip_index), None)
    if not result:
        return jsonify({'error': 'Clip not found'}), 404

    clip_file = (result.get('files', {}).get('landscape')
                 or result.get('files', {}).get('vertical'))
    if not clip_file or not os.path.exists(clip_file):
        return jsonify({'error': 'Clip file not on disk'}), 404

    try:
        n = max(10, min(80, int(request.args.get('n', 40))))
    except (TypeError, ValueError):
        n = 40

    filmstrip_dir = os.path.join(OUTPUT_DIR, job_id, 'filmstrip')
    try:
        frames = extract_clip_filmstrip(clip_file, filmstrip_dir, clip_index, n)
        return jsonify({'frames': frames,
                        'duration': result.get('duration', 0)})
    except Exception as e:
        log.exception("Clip filmstrip failed job=%s clip=%s", job_id, clip_index)
        return jsonify({'error': str(e)}), 500


# SESSIE 19 — Phase 10: spectrogram PNG for the editor's audio track.
# Loads only the requested time slice from the per-job WAV (same source
# the waveform endpoint uses), STFTs it, log-maps to viridis, encodes a
# tiny PNG with stdlib zlib + struct, and caches it on disk so subsequent
# opens are instant.
@app.route('/api/spectrogram/<job_id>/<int:clip_index>')
def clip_spectrogram(job_id, clip_index):
    _u, _j, err = _require_job_access(job_id, allow_query_token=True)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if not snap:
        return jsonify({'error': 'Job not found'}), 404

    target = next((r for r in (snap.get('results') or snap.get('clips') or [])
                   if r.get('index') == clip_index), None)
    if not target:
        return jsonify({'error': 'clip not found'}), 404

    try:
        width  = max(80, min(2000, int(request.args.get('w', 800))))
        height = max(40, min(400,  int(request.args.get('h', 96))))
    except (TypeError, ValueError):
        width, height = 800, 96

    start = float(target.get('start', 0))
    end   = float(target.get('end', start + 15))
    dur   = max(0.05, end - start)

    # Reuse the per-job WAV the waveform endpoint already populates. Falls
    # back to the source video when the WAV is gone (post-restart cleanup).
    audio_path = os.path.join(UPLOAD_DIR, f"{job_id}.wav")
    if not os.path.exists(audio_path):
        audio_path = snap.get('video_path')
    if not audio_path or not os.path.exists(audio_path):
        return jsonify({'error': 'audio source unavailable'}), 410

    cache_dir = os.path.join(OUTPUT_DIR, job_id, 'spec_cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f'clip{clip_index:03d}_{width}x{height}.png')
    if os.path.exists(cache_path):
        return send_file(cache_path, mimetype='image/png',
                         max_age=86400, conditional=True)

    try:
        from spectrogram import render_spectrogram_png
        render_spectrogram_png(audio_path, start, dur, cache_path,
                               width=width, height=height)
        return send_file(cache_path, mimetype='image/png',
                         max_age=86400, conditional=True)
    except Exception as e:
        log.exception("Spectrogram failed job=%s clip=%s", job_id, clip_index)
        return jsonify({'error': str(e)}), 500


@app.route('/api/split-clip/<job_id>', methods=['POST'])
def api_split_clip(job_id):
    """Split an existing clip at a given time into two new clips."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err

    data = request.json or {}
    try:
        clip_index = int(data['clip_index'])
        split_at   = float(data['split_at'])   # seconds relative to clip start
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'clip_index and split_at required'}), 400

    with jobs_lock:
        job = jobs[job_id]
        target = next((r for r in job.get('results', []) if r['index'] == clip_index), None)
        if not target:
            return jsonify({'error': f'Clip {clip_index} not found'}), 404

        clip_file = (target.get('files', {}).get('landscape')
                     or target.get('files', {}).get('vertical'))
        clip_dur  = target.get('duration', 0)

    if not clip_file or not os.path.exists(clip_file):
        return jsonify({'error': 'Clip file not on disk'}), 404

    if not (0.5 < split_at < clip_dur - 0.5):
        return jsonify({'error': 'split_at must be > 0.5 s from each end'}), 400

    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    try:
        clip_type = target.get('type', 'manual')
        path_a, path_b = split_clip_at(clip_file, split_at, job_output_dir,
                                       clip_index, clip_type)
        fname_a = os.path.basename(path_a)
        fname_b = os.path.basename(path_b)
        return jsonify({
            'success': True,
            'part_a': {'filename': fname_a, 'url': f'/api/clip/{job_id}/{fname_a}',
                       'duration': round(split_at, 3)},
            'part_b': {'filename': fname_b, 'url': f'/api/clip/{job_id}/{fname_b}',
                       'duration': round(clip_dur - split_at, 3)},
        })
    except Exception as e:
        log.exception("Split clip failed job=%s clip=%s", job_id, clip_index)
        return jsonify({'error': str(e)}), 500


@app.route('/api/snap-to-beat/<job_id>', methods=['POST'])
def snap_beat(job_id):
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    snap = _get_snapshot(job_id)
    if snap is None:
        return jsonify({'error': 'Job not found'}), 404
    data = request.json or {}
    try:
        start = float(data['start'])
        end   = float(data['end'])
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'start and end required'}), 400
    bpm_info = snap.get('bpm', {})
    bpm = bpm_info.get('bpm', 0)
    if bpm <= 0:
        return jsonify({'error': 'BPM not detected'}), 400
    beat_times = bpm_info.get('beat_times', [])
    offset = beat_times[0] if beat_times else 0
    snapped_start, snapped_end = snap_to_beat(start, end, bpm, offset)
    return jsonify({'start': snapped_start, 'end': snapped_end})


# ---------------------------------------------------------------------------
# UI-driven stubs (Style / Export / Publish / Schedule / Hardware meters)
# These accept the payloads the new UI sends and return success envelopes so
# the front end can complete its flows. Replace internals with real engines
# as they come online.
# ---------------------------------------------------------------------------

# Persisted scheduled batches — simple JSON file
SCHEDULES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheduled_batches.json')

def _load_schedules():
    try:
        with open(SCHEDULES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return []

def _save_schedules(items):
    try:
        with open(SCHEDULES_FILE, 'w') as f:
            json.dump(items, f, indent=2)
    except OSError:
        pass


@app.route('/api/style/<job_id>', methods=['POST'])
def api_apply_style(job_id):
    """Persist a per-job style preset (caption preset, accent, overlays).
    Stub: stores into the job dict and returns ok. Real renderer should
    consume this when burning captions."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    body = request.get_json(silent=True) or {}
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            return jsonify({'error': 'job not found'}), 404
        job['style'] = body
    return jsonify({'ok': True, 'style': body})


@app.route('/api/brand-kit/logo', methods=['POST'])
def api_brand_logo():
    """Accept a logo image upload for the brand kit."""
    f = request.files.get('logo')
    if not f or not f.filename:
        return jsonify({'error': 'logo file required'}), 400
    safe = secure_filename(f.filename) if 'secure_filename' in globals() else f.filename
    target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brand_kit')
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, 'logo_' + safe)
    f.save(path)
    # Update brand_kit.json if it exists
    bk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brand_kit.json')
    bk = {}
    try:
        with open(bk_path, 'r') as fh:
            bk = json.load(fh)
    except (FileNotFoundError, ValueError):
        pass
    bk['logo_path'] = path
    try:
        with open(bk_path, 'w') as fh:
            json.dump(bk, fh, indent=2)
    except OSError:
        pass
    return jsonify({'ok': True, 'logo_path': path})


@app.route('/api/brand-kit/overlay', methods=['POST'])
def api_brand_overlay():
    """Accept a custom overlay video/image upload for music-visual overlays."""
    f = request.files.get('overlay')
    if not f or not f.filename:
        return jsonify({'error': 'overlay file required'}), 400
    safe = secure_filename(f.filename) if 'secure_filename' in globals() else f.filename
    target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brand_kit', 'overlays')
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, safe)
    f.save(path)
    return jsonify({'ok': True, 'overlay_path': path})


def _format_dur(seconds):
    try:
        s = int(round(float(seconds)))
        return f"{s//60}:{s%60:02d}"
    except (TypeError, ValueError):
        return '–'


# Concurrency cap for export ffmpegs. 2 is conservative — VideoToolbox handles
# 2 simultaneous encodes well on M-series chips without thermal throttling.
EXPORT_MAX_PARALLEL = 2


def _resolve_export_source(clip):
    """Pick the best single source file for this clip (legacy single-format
    callers). Prefers landscape (higher quality master)."""
    files = clip.get('files') or {}
    return files.get('landscape') or files.get('vertical')


# SESSIE 75 — center-crop helper voor de echte 1:1 (1080x1080) en 4:5 (1080x1350)
# formaten. Hergebruikt exact de crop-filters van /api/derive (api_derive_ratio).
# Crop't een BESTAANDE cut (landscape/vertical); geen aparte brand-overlay-stap
# (brand komt mee als de bron-cut 'm al had).
def _derive_ratio_file(src, ratio, out_path):
    if ratio == 'square':
        crop_filter = ("crop=min(iw\\,ih):min(iw\\,ih):"
                       "(iw-min(iw\\,ih))/2:(ih-min(iw\\,ih))/2,scale=1080:1080")
    elif ratio == 'portrait45':
        crop_filter = ("crop=min(iw\\,ih*0.8):min(iw/0.8\\,ih):"
                       "(iw-min(iw\\,ih*0.8))/2:(ih-min(iw/0.8\\,ih))/2,scale=1080:1350")
    else:
        raise ValueError(f'unsupported ratio {ratio}')
    cmd = [media_tools.ffmpeg(), '-y', '-i', src, '-vf', crop_filter,
           '-c:v', 'h264_videotoolbox' if sys.platform == 'darwin' else 'libx264',
           '-b:v', '8M', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
           out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    if proc.returncode != 0:
        cmd[cmd.index('-c:v') + 1] = 'libx264'   # fallback als VideoToolbox faalt
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError(f'derive {ratio} rc={proc.returncode}')
    return out_path


def _resolve_export_sources(clip, aspects=None, job_id=None, job_output_dir=None):
    """Return every wanted format source for this clip as a list of
    (aspect_key, path) tuples. Used by the export worker.

    SESSIE 68 — ontbrekende landscape/vertical worden on-demand uit de bron
    gesneden. SESSIE 75 — square (1:1) en portrait45 (4:5) worden afgeleid
    (center-crop) uit de bijbehorende basis-cut (square<-landscape,
    portrait45<-vertical); de basis-cut wordt zo nodig eerst gemaakt. Alleen
    de WANTED formaten komen terug (een basis-cut die enkel als crop-bron
    diende, wordt niet meegeleverd)."""
    files = clip.get('files') or {}
    BASE = ('landscape', 'vertical')
    DERIVED = ('square', 'portrait45')
    if aspects:
        wanted = [a for a in aspects if a in BASE + DERIVED]
    else:
        wanted = list(BASE)
    base_wanted = [a for a in wanted if a in BASE]
    derived_wanted = [a for a in wanted if a in DERIVED]

    # Welke basis-cuts hebben we nodig (gevraagd OF als crop-bron voor derived)?
    need_base = set(base_wanted)
    for d in derived_wanted:
        need_base.add('vertical' if d == 'portrait45' else 'landscape')

    resolved_base = {}      # key -> path
    missing = []
    for key in need_base:
        src = files.get(key)
        if src and os.path.exists(src):
            resolved_base[key] = src
        else:
            missing.append(key)

    # On-demand cut for any needed-but-missing base format.
    if missing and job_id and job_output_dir:
        start = clip.get('start')
        end = clip.get('end')
        clip_index = clip.get('index')
        clip_type = clip.get('type') or clip.get('kind') or 'drop'
        if start is not None and end is not None and clip_index is not None and end > start:
            with jobs_lock:
                j = jobs.get(job_id) or {}
                video_path_job = j.get('video_path')
            if not (video_path_job and os.path.exists(video_path_job)):
                snap = _load_job_snapshot(job_id)
                if snap:
                    video_path_job = snap.get('video_path')
            if video_path_job and os.path.exists(video_path_job):
                try:
                    cut = slice_clip(
                        video_path_job, float(start), float(end),
                        job_output_dir, int(clip_index), str(clip_type),
                        formats=list(missing),
                    )
                    for key in missing:
                        p = (cut or {}).get(key)
                        if p and os.path.exists(p):
                            resolved_base[key] = p
                            files[key] = p
                except Exception as e:
                    log.warning("export: on-demand cut of %s failed for clip %s: %s",
                                missing, clip_index, e)

    out = [(k, p) for (k, p) in resolved_base.items() if k in base_wanted]

    # Derived (1:1 / 4:5) afleiden uit de basis-cut.
    for d in derived_wanted:
        if files.get(d) and os.path.exists(files[d]):
            out.append((d, files[d]))
            continue
        base_key = 'vertical' if d == 'portrait45' else 'landscape'
        base_src = (resolved_base.get(base_key)
                    or resolved_base.get('landscape') or resolved_base.get('vertical'))
        if not (base_src and os.path.exists(base_src)) or not job_output_dir:
            log.warning("export: geen bron voor %s (clip %s)", d, clip.get('index'))
            continue
        try:
            base_name = os.path.splitext(os.path.basename(base_src))[0]
            for suffix in ('_vertical', '_landscape', '_square', '_portrait45'):
                if base_name.endswith(suffix):
                    base_name = base_name[:-len(suffix)]
                    break
            out_path = os.path.join(job_output_dir, f"{base_name}_{d}.mp4")
            _derive_ratio_file(base_src, d, out_path)
            out.append((d, out_path))
            files[d] = out_path
        except Exception as e:
            log.warning("export: derive %s failed for clip %s: %s", d, clip.get('index'), e)

    order = {'landscape': 0, 'vertical': 1, 'square': 2, 'portrait45': 3}
    out.sort(key=lambda kv: order.get(kv[0], 9))
    return out


def _dedupe_output_path(path):
    """SESSIE 73 - voorkom stil overschrijven bij label-gebaseerde namen.
    Label-namen kunnen botsen (twee clips met dezelfde naam, of een re-export
    van dezelfde clip). Bestaat het pad al, voeg dan _2/_3/... toe vóór de
    extensie i.p.v. data te overschrijven.
    """
    try:
        if not os.path.exists(path):
            return path
        root, ext = os.path.splitext(path)
        i = 2
        while i < 1000:
            cand = f"{root}_{i}{ext}"
            if not os.path.exists(cand):
                return cand
            i += 1
    except Exception:
        pass
    return path


def _safe_filename_label(label, max_len=80):
    """Make a filesystem-safe filename component from a user-facing label.
    Strips path separators and characters that confuse Finder/Explorer,
    collapses whitespace to underscores. Returns '' on empty input."""
    if not label:
        return ''
    safe = re.sub(r'[\\/:*?"<>|]+', '', str(label))
    safe = re.sub(r'\s+', '_', safe).strip('_')
    return safe[:max_len]


# SESSIE 75 — aspect-key -> filesystem-veilig ratio-label. Geen ':' (Finder toont
# die als '/', Windows weigert 'm), dus "9x16"-stijl. Gebruikt in de export-naam.
_ASPECT_RATIO_LABEL = {
    'vertical':   '9x16',
    'landscape':  '16x9',
    'square':     '1x1',
    'portrait45': '4x5',
}


def _safe_filename_label_keep_spaces(label, max_len=80):
    """Als _safe_filename_label maar behoudt spaties (collapse naar 1 spatie).
    Strip alleen filesystem-illegale tekens (\\ / : * ? " < > |). Zo blijft een
    rename als "House set" leesbaar als "House set" i.p.v. "House_set"."""
    if not label:
        return ''
    safe = re.sub(r'[\\/:*?"<>|]+', '', str(label))
    safe = re.sub(r'\s+', ' ', safe).strip()
    return safe[:max_len]


def _build_export_filename(clip, idx, aspect_key, codec, ext='.mp4'):
    """Compose the user-visible export filename.

    SESSIE 75 — elke ratio krijgt " - <ratio>" achter de rename-basis (ook 9:16),
    met filesystem-veilige ratio-tokens. Voorbeeld rename "House set":
      "House set - 9x16.mp4", "House set - 16x9.mp4", "House set - 1x1.mp4",
      "House set - 4x5.mp4". Codec (bij non-match) komt er als " - h265" achteraan.

    Metadata (clip_index, aspect, codec) blijft naar de sidecar .meta.json gaan
    (zie _write_export_sidecar), dus /api/exports leest de aspect uit de sidecar
    en de Library blijft op alle (oude + nieuwe) namen werken.
    """
    custom = clip.get('custom_label')
    fallback_type = (clip.get('type') or clip.get('kind') or 'Clip')
    fallback_type = str(fallback_type).strip().capitalize() or 'Clip'
    fallback_idx = clip.get('index') if clip.get('index') is not None else (idx + 1)
    fallback = f"{fallback_type}_{fallback_idx}"
    label = (_safe_filename_label_keep_spaces(custom)
             or _safe_filename_label_keep_spaces(fallback)
             or f"clip_{idx+1:02d}")

    parts = [label]
    ratio = _ASPECT_RATIO_LABEL.get(aspect_key)
    if ratio:
        parts.append(ratio)
    elif aspect_key and aspect_key != 'vertical':
        parts.append(aspect_key)  # fallback voor onbekende aspect-keys
    if codec and codec != 'match':
        # Strip _vt suffix voor leesbaarheid: h265_vt → h265, h264_vt → h264
        parts.append(codec.replace('_vt', ''))
    return ' - '.join(parts) + ext


def _build_export_filename_legacy(clip, idx, aspect_key, codec, ext='.mp4'):
    """Het pre-sessie43 patroon — alleen aangeroepen door de
    backward-compat fallback parser in /api/exports."""
    custom = clip.get('custom_label')
    fallback_type = (clip.get('type') or clip.get('kind') or 'Clip')
    fallback_type = str(fallback_type).strip().capitalize() or 'Clip'
    fallback_idx = clip.get('index') if clip.get('index') is not None else (idx + 1)
    fallback = f"{fallback_type}_{fallback_idx}"
    label = _safe_filename_label(custom) or _safe_filename_label(fallback) or f"clip_{idx+1:02d}"
    clip_num = clip.get('index') if clip.get('index') is not None else (idx + 1)
    return f"{label}__clip{int(clip_num):02d}__{aspect_key}__{codec}{ext}"


def _write_export_sidecar(out_path, clip, idx, aspect_key, codec):
    """SESSIE 43a — sidecar .meta.json naast elke export.

    Bevat de metadata die voorheen in de filename zat: clip_index, aspect,
    codec, originele user-label, mtime van schrijven. /api/exports leest dit
    als de filename geen __clip__-token bevat (= nieuwe schone naam).

    Best-effort: een mislukte sidecar-write logt een warning maar laat de
    export niet falen. Backward-compat parser in /api/exports valt terug op
    bestandsnaam-regex als sidecar ontbreekt.
    """
    try:
        meta = {
            'clip_index': clip.get('index') if clip.get('index') is not None else (idx + 1),
            'aspect': aspect_key,
            'codec': codec,
            'label': clip.get('custom_label') or None,
            'written_at': time.time(),
            'schema': 1,
        }
        sidecar_path = out_path + '.meta.json'
        with open(sidecar_path, 'w') as f:
            json.dump(meta, f, indent=2)
    except (OSError, TypeError) as e:
        log.warning("Could not write export sidecar for %s: %s", out_path, e)


def _detect_layers_for_clip(job_id, output_dir, clip_index):
    """SESSIE 43a — check of er voor deze clip iets bake-baar is.

    Snelle pre-bake skip-check: als er geen text-overlays voor deze clip
    bestaan EN brand_kit geen logo/watermark heeft, kan de export gewoon
    via de bestaande snelle `clip['files']` route. Anders moeten we de
    layers eerst in een tmp-bestand bakken vóór de codec-conversie.

    Returnt een dict: {
      'has_text_layers': bool,
      'has_logo': bool,
      'has_watermark': bool,
      'has_tracking': bool,   # pan/zoom/letterbox keyframes
    }
    """
    info = {
        'has_text_layers': False,
        'has_logo': False,
        'has_watermark': False,
        'has_tracking': False,
    }
    # Text overlays voor deze specifieke clip
    try:
        ov_path = os.path.join(output_dir, 'text_overlays.json')
        if os.path.exists(ov_path):
            with open(ov_path, 'r') as f:
                raw = json.load(f) or {}
            clips_map = raw.get('clips') or {}
            layers = clips_map.get(str(int(clip_index))) or []
            if layers:
                info['has_text_layers'] = True
    except Exception as e:
        log.warning("layer-detect: text_overlays read failed for %s: %s", job_id, e)
    # Brand-kit logo + watermark
    try:
        # SESSIE 74 - fase 2b: verkies de per-workspace brand uit de job-map als
        # die gematerialiseerd is; anders het globale bestand (geen regressie).
        _kit_path = os.path.join(output_dir, 'brand_kit.json') if output_dir else BRAND_KIT_PATH
        if not os.path.exists(_kit_path):
            _kit_path = BRAND_KIT_PATH
        if os.path.exists(_kit_path):
            with open(_kit_path, 'r') as f:
                kit = json.load(f) or {}
            logo = kit.get('logo')
            if isinstance(logo, dict) and (logo.get('path') or logo.get('file')) and logo.get('enabled', True):
                info['has_logo'] = True
            wm = kit.get('watermark')
            if isinstance(wm, dict) and wm.get('file') and wm.get('enabled', True):
                info['has_watermark'] = True
    except Exception as e:
        log.warning("layer-detect: brand_kit read failed: %s", e)
    # Tracking keyframes (pan/zoom/letterbox) — alleen relevant voor vertical
    try:
        kf_dir = os.path.join(output_dir, 'keyframes')
        kf_path = os.path.join(kf_dir, f'clip_{int(clip_index):02d}.json')
        if os.path.exists(kf_path):
            with open(kf_path, 'r') as f:
                kf = json.load(f) or {}
            if kf.get('keyframes') or kf.get('crop_mode') in ('pan', 'zoom', 'letterbox'):
                info['has_tracking'] = True
    except Exception:
        pass
    return info


def _prebake_clip_for_export(clip, idx, job_id, job_output_dir, aspect_filter,
                              cfg_overlays, inmix=None):
    """SESSIE 43a — bake text/logo/watermark in vóór de codec-conversie.

    SESSIE 78 - D5: `inmix` (default None) wordt doorgegeven aan recut_clip zodat
    een synced bron (2e camera/crowd-audiospoor) de crowd onder de schone mix
    bakt. No-op als de bron maar 1 audiospoor heeft (recut guardt op de stream-
    telling), dus geen impact op gewone sets.

    Wordt alleen aangeroepen als _detect_layers_for_clip iets vond én de
    user-toggles (cfg_overlays) niet alles uitschakelen. Roept recut_clip
    aan met de huidige clip-grenzen, schrijft naar tmp-paden binnen het
    job-dir (zelfde dir als de gewone clip-files, met `_baked` suffix zodat
    ze niet de live editor-preview overschrijven).

    cfg_overlays = {
      'captions': bool,   # default True
      'watermark': bool,  # default True (als brand-kit watermark heeft)
      'logo': bool,       # default True (als brand-kit logo heeft)
    }

    Returns dict {aspect_key: baked_path} — dezelfde shape als clip['files']
    zodat de caller transparant kan switchen.
    """
    video_path_job = None
    clip_type = clip.get('type') or clip.get('kind') or 'drop'
    start = clip.get('start')
    end = clip.get('end')
    clip_index = clip.get('index')
    if start is None or end is None or clip_index is None:
        return None
    # Source video van de set ophalen uit de in-memory job (of snapshot).
    with jobs_lock:
        j = jobs.get(job_id) or {}
        video_path_job = j.get('video_path')
    if not video_path_job or not os.path.exists(video_path_job):
        snap = _load_job_snapshot(job_id)
        if snap:
            video_path_job = snap.get('video_path')
    if not video_path_job or not os.path.exists(video_path_job):
        log.warning("prebake: source video missing for job %s", job_id)
        return None

    # Aspect-filter respecteren: we baken alleen de aspects die we straks
    # ook gaan exporteren. recut_clip accepteert 'formats' = lijst van
    # ['landscape', 'vertical'].
    if aspect_filter:
        formats = list(aspect_filter)
    else:
        formats = ['landscape', 'vertical']

    # Tmp-output-dir binnen job-dir zodat brand-kit/text-overlay paden
    # (die relatief vanuit job-dir worden geresolved) blijven werken.
    # `_baked` prefix in filename voorkomt clobber van editor-files.
    baked_dir = os.path.join(job_output_dir, '_baked_for_export')
    os.makedirs(baked_dir, exist_ok=True)

    # We schrijven baked-versies via een truc: kopieer text_overlays.json
    # tijdelijk naar baked_dir zodat recut_clip ze daar vindt, maar pas
    # 'm aan als user-toggles bepaalde lagen uitzetten.
    try:
        src_overlays = os.path.join(job_output_dir, 'text_overlays.json')
        baked_overlays = os.path.join(baked_dir, 'text_overlays.json')
        if cfg_overlays.get('captions', True) and os.path.exists(src_overlays):
            shutil.copy2(src_overlays, baked_overlays)
        else:
            # Captions uit → schrijf lege overlays zodat recut_clip ze skipt
            with open(baked_overlays, 'w') as f:
                json.dump({'clips': {}}, f)
        # Keyframes dir spiegelen zodat pan/zoom in baked variant blijft
        src_kf = os.path.join(job_output_dir, 'keyframes')
        baked_kf = os.path.join(baked_dir, 'keyframes')
        if os.path.isdir(src_kf):
            if os.path.isdir(baked_kf):
                shutil.rmtree(baked_kf)
            shutil.copytree(src_kf, baked_kf)
        # set-level BPM info (job.json) — recut_clip leest 'm voor BPM-stamp
        # (die nu force-disabled is, maar we kopiëren 'm voor consistentie)
        src_job_json = os.path.join(job_output_dir, 'job.json')
        if os.path.exists(src_job_json):
            shutil.copy2(src_job_json, os.path.join(baked_dir, 'job.json'))
    except (OSError, json.JSONDecodeError) as e:
        log.warning("prebake: setup failed for clip %s: %s", clip_index, e)
        return None

    # SESSIE 74 - fase 2b: per-workspace brand in de baked-map zodat recut_clip
    # (leest output_dir eerst) de juiste brand bakt. No-op -> globale fallback.
    _materialize_job_brand(job_id, baked_dir)

    # Watermark/logo uitzetten gebeurt NIET via brand_kit.json edit
    # (dat is een globale file — race conditions tussen parallel exports).
    # In plaats daarvan: na de recut, als toggles uit staan, opnieuw recut
    # met aangepaste brand_kit kopie. Voor MVP simpel houden — we leveren
    # captions-toggle nu (Onderdeel 1), watermark/logo-toggle komt in
    # Onderdeel 5 met een uitgebreidere pre-bake.

    try:
        files = recut_clip(
            video_path_job,
            float(start), float(end),
            baked_dir,
            int(clip_index),
            str(clip_type)[:20],
            formats=formats,
            overlay_text=None,
            normalize_audio=False,
            inmix=inmix,
        )
        return files or None
    except Exception as e:
        log.exception("prebake: recut_clip failed for clip %s: %s", clip_index, e)
        return None


def _run_export_job(job_id, cfg):
    """Worker thread: re-encode every clip in the job using user's settings.
    Updates job['export_queue'] in-place under jobs_lock so the status endpoint
    can report real progress. Runs up to EXPORT_MAX_PARALLEL ffmpegs at once."""
    from concurrent.futures import ThreadPoolExecutor

    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return
        # Cutter-output (`results`) carries the actual `files` paths needed to
        # re-encode. `clips` is analyzer-only metadata (start/end/bpm/...) and
        # has no file paths. Prefer results; fall back to clips so older
        # pre-cutter jobs still produce a clean "source missing" error per item
        # rather than a silent no-op.
        clips = list(job.get('results') or job.get('clips') or [])
        job_output_dir = os.path.join(OUTPUT_DIR, job_id)

    # If clip list is empty in memory, try to recover from on-disk snapshot.
    # Older jobs (pre-snapshot system) may need reconstruction via clips.csv.
    if not clips:
        snap = _load_job_snapshot(job_id)
        if snap and (snap.get('results') or snap.get('clips')):
            clips = list(snap.get('results') or snap['clips'])
            with jobs_lock:
                if job_id in jobs:
                    # Restore to whichever key the snapshot used so other code
                    # paths that distinguish results (cutter-output, has files)
                    # vs clips (analyzer-only) keep working consistently. Prior
                    # behaviour wrote everything to ['clips'], which silently
                    # mixed the two and could mask future bugs.
                    if snap.get('results'):
                        jobs[job_id]['results'] = clips
                    else:
                        jobs[job_id]['clips'] = clips

    if not clips:
        with jobs_lock:
            job['export_done'] = True
        return

    # Apply Dashboard selection (C4) — when the caller asked for a subset,
    # restrict the worker to those indices so the queue and the work loop
    # stay in lock-step.
    sel = cfg.get('_selected_indices')
    if isinstance(sel, list) and sel:
        clips = [clips[i] for i in sel if 0 <= i < len(clips)]

    codec = cfg.get('codec', 'match')
    fps = cfg.get('fps', 'match')
    resolution = cfg.get('res', 'source')

    def _set_item(idx, **fields):
        with jobs_lock:
            j = jobs.get(job_id)
            if not j:
                return
            q = j.get('export_queue') or []
            if 0 <= idx < len(q):
                q[idx].update(fields)
                j['export_queue'] = q

    user_dir = cfg.get('output_dir')
    # Optional aspect whitelist from the Dashboard/Editor aspect-picker
    # ('vertical', 'landscape', or both). When omitted, render every
    # available format (back-compat with API callers).
    raw_aspects = cfg.get('aspects')
    aspect_filter = None
    if isinstance(raw_aspects, list) and raw_aspects:
        aspect_filter = [a for a in raw_aspects
                         if a in ('landscape', 'vertical', 'square', 'portrait45')]
        if not aspect_filter:
            aspect_filter = None

    # SESSIE 43a — overlay-toggles uit de export-modal. Default ALLES AAN
    # zodat clips met captions/branding niet ineens kaal exporteren bij
    # API-callers die de keys niet meegeven. Onderdeel 5 (sessie 43b) zet
    # deze keys vanuit de frontend modal.
    raw_overlays = cfg.get('overlays') or {}
    overlays_cfg = {
        'captions':  bool(raw_overlays.get('captions',  True)),
        'watermark': bool(raw_overlays.get('watermark', True)),
        'logo':      bool(raw_overlays.get('logo',      True)),
    }

    # SESSIE 78 - D5: crowd (camera) audio inmix. Default OFF. Alleen effectief
    # als de export-modal het vraagt EN de bronset echt een 2e audiospoor heeft
    # (een via Spoor D gesynced camera+schone-audio-bestand). Dan forceren we de
    # recut/prebake zodat de crowd onder de schone mix wordt gebakken. Gewone
    # 1-spoor-sets raken dit niet (identieke output als voorheen). De stream-
    # telling gebeurt 1x per export-job op de bron, niet per clip.
    raw_inmix = cfg.get('inmix') or {}
    inmix_cfg = None
    inmix_source_ok = False
    if isinstance(raw_inmix, dict) and raw_inmix.get('enabled'):
        inmix_cfg = {
            'enabled': True,
            'volume': raw_inmix.get('volume', 0.25),
            'highpass': raw_inmix.get('highpass', 200),
        }
        try:
            src_v = (job or {}).get('video_path')
            if src_v and os.path.exists(src_v):
                inmix_source_ok = _count_audio_streams(src_v) >= 2
        except Exception:
            inmix_source_ok = False

    # SESSIE 43a — custom labels per clip-index meegeven via cfg['labels'].
    # Shape: {"<clip_index>": "Naam"}. Wordt door /api/export gevuld vanuit
    # de modal-rename (Onderdeel 2). Niet-meegegeven clips behouden hun
    # bestaande custom_label / fallback.
    labels_map = cfg.get('labels') or {}

    def _process(idx, clip):
        _set_item(idx, status='running', pct=5)

        # Per-clip rename uit modal toepassen (Onderdeel 2). We muteren een
        # kopie zodat we het in-memory job-snapshot niet aanpassen voordat
        # de export geslaagd is. /api/rename blijft de canonieke route voor
        # persistente naamswijziging.
        clip_for_export = dict(clip)
        clip_key = str(clip.get('index')) if clip.get('index') is not None else str(idx + 1)
        if clip_key in labels_map and isinstance(labels_map[clip_key], str):
            new_label = labels_map[clip_key].strip()
            if new_label:
                clip_for_export['custom_label'] = new_label

        # SESSIE 43a — pre-bake check. Heeft deze clip layers die in de
        # output móeten? Zo ja en de user wil ze (toggles aan), bake ze in
        # naar tmp-paden vóór de codec-conversie. Anders gebruiken we de
        # bestaande clip['files'] direct = sneller pad.
        layer_info = _detect_layers_for_clip(
            job_id, job_output_dir,
            clip.get('index') if clip.get('index') is not None else (idx + 1),
        )
        want_captions  = overlays_cfg['captions']  and layer_info['has_text_layers']
        want_watermark = overlays_cfg['watermark'] and layer_info['has_watermark']
        want_logo      = overlays_cfg['logo']      and layer_info['has_logo']
        # Tracking (pan/zoom/letterbox) is een geometrische crop, geen
        # overlay — die nemen we ALTIJD mee in de pre-bake als 'm bestaat,
        # ongeacht overlay-toggles. Anders wijkt de vertical export af van
        # wat de editor liet zien.
        needs_prebake = want_captions or want_watermark or want_logo or layer_info['has_tracking']

        # SESSIE 78 - D5: een crowd-inmix moet vanaf de BRON herrenderd worden
        # (de bestaande clipfiles hebben het 2e camera-spoor mogelijk al laten
        # vallen), dus forceer de prebake-recut als inmix gevraagd is en de bron
        # 2 audiosporen heeft. Bij gewone sets is use_inmix None -> niets verandert.
        use_inmix = inmix_cfg if (inmix_cfg and inmix_source_ok) else None
        if use_inmix:
            needs_prebake = True

        sources = _resolve_export_sources(
            clip, aspects=aspect_filter,
            job_id=job_id, job_output_dir=job_output_dir,
        )
        if needs_prebake:
            _set_item(idx, status='running', pct=15)
            baked = _prebake_clip_for_export(
                clip_for_export, idx, job_id, job_output_dir,
                aspect_filter, overlays_cfg, inmix=use_inmix,
            )
            if baked:
                # Swap baked-files in als source voor de codec-conversie.
                baked_sources = []
                wanted_aspects = (aspect_filter or ['landscape', 'vertical'])
                for key in wanted_aspects:
                    p = baked.get(key)
                    if p and os.path.exists(p):
                        baked_sources.append((key, p))
                if baked_sources:
                    # SESSIE 75 — merge: vervang alleen de gebakte aspecten
                    # (landscape/vertical) door hun baked-versie; behoud andere
                    # (square/portrait45 uit _resolve_export_sources) zodat 1:1/4:5
                    # niet wegvallen als de prebake draait.
                    baked_keys = {k for k, _ in baked_sources}
                    sources = baked_sources + [(k, p) for (k, p) in sources
                                               if k not in baked_keys]
                else:
                    log.warning("prebake produced no usable files for clip %s — falling back to live files", idx)
            else:
                log.warning("prebake skipped for clip %s — using live files (export may miss layers)", idx)

        if not sources:
            _set_item(idx, status='fail', pct=0,
                      error=f'source clip missing for clip {idx+1}')
            return

        # Render every requested format so the Library filter shows both
        # 16:9 and 9:16. Queue still tracks one item per clip — selecting
        # 3 clips produces up to 6 files but the progress reads "3/3".
        primary_path = None
        primary_size = 0
        total_duration = 0.0
        last_error = None
        rendered_count = 0
        copy_warning = None

        for aspect_key, src in sources:
            result = export_clip_with_settings(
                source_clip=src,
                output_dir=job_output_dir,
                clip_index=idx,
                codec=codec,
                fps=fps,
                resolution=resolution,
            )
            if not result['ok']:
                last_error = result['error']
                continue

            out_path = result['path']
            out_size = result['size_bytes']
            total_duration = max(total_duration, result.get('duration_s', 0))

            # SESSIE 43a — schone filename ('Drop_3.mp4' i.p.v. 'Drop_3__clip03__
            # vertical__match.mp4') + sidecar .meta.json met clip_index/aspect/codec.
            try:
                ext = os.path.splitext(out_path)[1] or '.mp4'
                new_basename = _build_export_filename(clip_for_export, idx, aspect_key, codec, ext)
                renamed_path = os.path.join(os.path.dirname(out_path), new_basename)
                # Avoid clobber if a previous clip rendered to the same name
                if renamed_path != out_path and os.path.exists(renamed_path):
                    os.unlink(renamed_path)
                if renamed_path != out_path:
                    os.rename(out_path, renamed_path)
                    out_path = renamed_path
                # Sidecar JSON náást het bestand (best-effort, faalt niet hard)
                _write_export_sidecar(out_path, clip_for_export, idx, aspect_key, codec)
            except OSError as e:
                log.warning("Could not rename export %s -> %s: %s",
                            out_path, new_basename, e)

            # Copy to user's folder if they picked one. Original stays in
            # OUTPUT_DIR so the Library still finds it.
            if user_dir:
                try:
                    target = os.path.join(user_dir, os.path.basename(out_path))
                    shutil.copy2(out_path, target)
                    # SESSIE 75 — de .meta.json sidecar NIET meekopieren naar de
                    # door de gebruiker gekozen map; die is alleen intern nodig
                    # (Library leest 'm uit de job-map). Eindgebruiker krijgt enkel
                    # de schone .mp4-bestanden.
                    out_path = target
                    try:
                        out_size = os.path.getsize(target)
                    except OSError:
                        pass
                except (OSError, shutil.Error) as e:
                    log.warning("Could not copy %s -> %s: %s", out_path, user_dir, e)
                    copy_warning = str(e)

            rendered_count += 1
            # First successful render becomes the "primary" reported path.
            # Landscape is yielded first by _resolve_export_sources so that's
            # what wins — keeps Show-in-Finder predictable.
            if primary_path is None:
                primary_path = out_path
                primary_size = out_size

        # SESSIE 43a — opruimen van baked-tmp na succesvolle export.
        # Behouden bij failure zodat we kunnen debuggen. Loopt expres NA
        # de copy-to-user-dir zodat die copy nog kan slagen.
        if needs_prebake and rendered_count > 0:
            try:
                baked_dir = os.path.join(job_output_dir, '_baked_for_export')
                if os.path.isdir(baked_dir):
                    shutil.rmtree(baked_dir, ignore_errors=True)
            except Exception as e:
                log.warning("Could not clean baked tmp for clip %s: %s", idx, e)

        if rendered_count == 0:
            _set_item(idx, status='fail', pct=0,
                      error=last_error or f'all renders failed for clip {idx+1}')
            return

        fields = {
            'status': 'done',
            'pct': 100,
            'export_path': primary_path,
            'export_size': primary_size,
            'export_duration': round(total_duration, 2),
            'aspects_rendered': rendered_count,
        }
        if copy_warning:
            fields['copy_warning'] = copy_warning
        _set_item(idx, **fields)

    try:
        with ThreadPoolExecutor(max_workers=EXPORT_MAX_PARALLEL) as ex:
            futures = [ex.submit(_process, i, c) for i, c in enumerate(clips)]
            for f in futures:
                try:
                    f.result()
                except Exception as e:
                    log.exception("export worker crashed: %s", e)
    finally:
        with jobs_lock:
            j = jobs.get(job_id)
            if j:
                j['export_done'] = True


@app.route('/api/default-export-dir', methods=['GET'])
def api_default_export_dir():
    """SESSIE 75 — default export-map (Downloads) zodat de export-modal die
    vooraf kan selecteren. ~/Downloads ligt binnen home -> voldoet aan de
    bestaande home-whitelist op /api/export."""
    user_info, err = _require_authed_user()
    if err:
        return err
    dl = os.path.expanduser('~/Downloads')
    return jsonify({'ok': True, 'path': dl, 'label': 'Downloads',
                    'exists': os.path.isdir(dl)})


@app.route('/api/export/<job_id>', methods=['POST'])
def api_export_start(job_id):
    """Start a real render queue for all clips in this job.
    Spawns a background thread that ffmpegs each clip with the requested
    codec/fps/resolution. Status is polled via /api/export/<job_id>/status."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    with jobs_lock:
        job = jobs.get(job_id)

    # Fallback: rehydrate from on-disk snapshot if not in memory.
    # Happens for jobs created before the rehydrate system, or after a
    # cold start when only some history entries restored cleanly.
    if not job:
        snap = _load_job_snapshot(job_id)
        if snap:
            with jobs_lock:
                jobs[job_id] = snap
                job = snap

    if not job:
        # Pre-snapshot jobs (verwerkt vóór deze sessie) kunnen niet worden
        # gerehydrateerd. Geef de UI een nuttige melding zodat we niet
        # eindigen met 23x FAIL en 0 idee waarom.
        return jsonify({
            'error': 'This set was processed before exports were supported. Re-process the source file to enable export.',
            'reason': 'pre_snapshot_job',
        }), 410  # 410 Gone — semantically correct: resource bestond ooit

    cfg = request.get_json(silent=True) or {}
    # For the queue we want analyzer metadata (caption/score/duration), which
    # lives on `clips`. The actual file paths live on `results` and are
    # resolved later in _run_export_job. Keep them aligned by index.
    clips = job.get('clips', []) or []
    if not clips:
        return jsonify({
            'error': 'No clips found for this job. Re-process the source set to enable export.',
            'reason': 'no_clips',
        }), 400

    # Optional: caller can ask for renders to be copied into a user-chosen
    # folder (Library/Editor "Export" buttons pick this via /api/pick-folder).
    # We validate up-front so a bad path fails fast — not after a 30 s render.
    output_dir = cfg.get('output_dir')
    # SESSIE 75 — default doel = ~/Downloads (i.p.v. de Library) als de caller
    # geen map meegeeft. De frontend stuurt normaal de gekozen/Downloads-map mee;
    # dit is het vangnet zodat exports niet stilletjes in de Library belanden.
    if not output_dir:
        _dl = os.path.expanduser('~/Downloads')
        if os.path.isdir(_dl):
            output_dir = _dl
    if output_dir:
        if not isinstance(output_dir, str) or not output_dir.strip():
            return jsonify({'error': 'Invalid output folder.', 'reason': 'bad_output_dir'}), 400
        output_dir = os.path.expanduser(output_dir)
        if not os.path.isdir(output_dir):
            return jsonify({
                'error': "That folder doesn't exist anymore.",
                'reason': 'output_dir_missing',
            }), 400
        if not os.access(output_dir, os.W_OK):
            return jsonify({
                'error': "Cannot write to that folder (permission denied).",
                'reason': 'output_dir_readonly',
            }), 400
        # SESSIE 43b — whitelist: alleen subfolders van de home-dir. Voorkomt
        # dat de export per ongeluk in /etc, /System of /Library belandt.
        # ~/, ~/Desktop, ~/Documents, ~/Downloads, ~/Movies en hun kinderen
        # zijn toegestaan. Volledig pad realpath'en zodat symlinks geen
        # uitweg bieden buiten home.
        try:
            real_target = os.path.realpath(output_dir)
            real_home = os.path.realpath(os.path.expanduser('~'))
            if not (real_target == real_home or real_target.startswith(real_home + os.sep)):
                return jsonify({
                    'error': "Voor de veiligheid mag de export-map alleen binnen je gebruikersmap liggen "
                             "(~/Desktop, ~/Documents, ~/Downloads, ~/Movies of subfolders).",
                    'reason': 'output_dir_outside_home',
                }), 400
        except OSError as e:
            return jsonify({
                'error': f'Could not resolve output folder: {e}',
                'reason': 'output_dir_resolve_failed',
            }), 400
        cfg['output_dir'] = output_dir   # normalised back into cfg

    # SESSIE 43a — overlay-toggles validatie. Frontend stuurt
    # {captions: bool, watermark: bool, logo: bool}. Onbekende keys negeren,
    # niet-bool waardes coercen via bool(). Default = alles aan (zie
    # _run_export_job._process voor toepassing).
    raw_overlays = cfg.get('overlays')
    if raw_overlays is not None:
        if not isinstance(raw_overlays, dict):
            return jsonify({
                'error': 'overlays must be an object',
                'reason': 'bad_overlays',
            }), 400
        cfg['overlays'] = {
            'captions':  bool(raw_overlays.get('captions',  True)),
            'watermark': bool(raw_overlays.get('watermark', True)),
            'logo':      bool(raw_overlays.get('logo',      True)),
        }

    # SESSIE 43a — labels-map voor per-clip rename via modal.
    # Shape: {"<clip_index_1based>": "Nieuwe naam"}.
    raw_labels = cfg.get('labels')
    if raw_labels is not None:
        if not isinstance(raw_labels, dict):
            return jsonify({
                'error': 'labels must be an object',
                'reason': 'bad_labels',
            }), 400
        clean_labels = {}
        for k, v in raw_labels.items():
            if isinstance(v, str):
                clean_labels[str(k)] = v[:200]  # cap, _safe_filename_label strippt verder
        cfg['labels'] = clean_labels

    # Refuse to start a second export while one is already running for this job.
    if job.get('export_queue') and not job.get('export_done', True):
        return jsonify({'error': 'export already in progress'}), 409

    # Optional: caller can request a subset by passing `clip_indices`
    # (positions in the clips/results list — 0-based). Used by the
    # Dashboard select-and-export flow (C4). When omitted, export all.
    raw_sel = cfg.get('clip_indices')
    selected_idx = None
    if isinstance(raw_sel, list) and raw_sel:
        try:
            selected_idx = sorted({int(i) for i in raw_sel
                                   if isinstance(i, (int, float)) and 0 <= int(i) < len(clips)})
        except (TypeError, ValueError):
            selected_idx = None
        if not selected_idx:
            return jsonify({
                'error': 'No valid clip indices in selection.',
                'reason': 'empty_selection',
            }), 400

    queue = []
    iter_indices = selected_idx if selected_idx is not None else list(range(len(clips)))
    for q_pos, i in enumerate(iter_indices):
        c = clips[i]
        queue.append({
            'idx': q_pos,             # position in queue (used for UI updates)
            'clip_idx': i,            # original clip index in the set
            'title': c.get('caption') or c.get('title') or f'Clip {i+1}',
            'score': int(round(c.get('score', 0))) if c.get('score') is not None else None,
            'duration': _format_dur(c.get('duration', 0)),
            'codec': cfg.get('codec', 'match'),
            'status': 'queued',
            'pct': 0,
        })

    # Stash the resolved indices on cfg so the worker thread can apply the
    # same filter to results/clips when it re-reads them.
    cfg['_selected_indices'] = iter_indices

    with jobs_lock:
        job['export_cfg'] = cfg
        job['export_queue'] = queue
        job['export_started_at'] = time.time()
        job['export_done'] = False

    # Fire-and-forget worker thread — Flask returns immediately so the UI
    # can start polling.
    t = threading.Thread(target=_run_export_job, args=(job_id, cfg), daemon=True)
    t.start()

    # SESSIE 35 — audit log
    _u_info, _ = _require_authed_user()
    _audit(
        'clip.export_started',
        user_id=_u_info['user_id'] if _u_info else None,
        metadata={'job_id': job_id, 'clip_count': len(queue), 'codec': cfg.get('codec', 'match')},
    )

    return jsonify({'ok': True, 'count': len(queue), 'cfg': cfg})


@app.route('/api/export/<job_id>/status', methods=['GET'])
def api_export_status(job_id):
    """Report the real render-queue progress, mutated by _run_export_job."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    with jobs_lock:
        job = jobs.get(job_id)

    if not job:
        # Same rehydrate fallback as the start endpoint
        snap = _load_job_snapshot(job_id)
        if snap:
            with jobs_lock:
                jobs[job_id] = snap
                job = snap

    if not job:
        return jsonify({'error': 'job not found'}), 404

    with jobs_lock:
        queue = list(job.get('export_queue') or [])
        done_flag = bool(job.get('export_done'))
    return jsonify({'items': queue, 'total': len(queue), 'done': done_flag})


@app.route('/api/publish/<job_id>', methods=['POST'])
def api_publish(job_id):
    """Publish a job's clips to the requested destinations.
    Stub: validates and acknowledges. Real implementation should hand off
    to per-platform connectors."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    body = request.get_json(silent=True) or {}
    destinations = body.get('destinations') or []
    if not destinations:
        return jsonify({'error': 'destinations required'}), 400
    return jsonify({
        'ok': True,
        'job_id': job_id,
        'destinations': destinations,
        'queued_at': time.time(),
        'note': 'Stub — real publish handlers not yet wired'
    })


@app.route('/api/schedule-batch', methods=['POST'])
def api_schedule_batch():
    """Save a scheduled batch drop for a job to local JSON."""
    body = request.get_json(silent=True) or {}
    job_id = body.get('jobId')
    destinations = body.get('destinations') or []
    schedule = body.get('schedule') or {}
    if not job_id:
        return jsonify({'error': 'jobId required'}), 400
    if not destinations:
        return jsonify({'error': 'destinations required'}), 400
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    items = _load_schedules()
    entry = {
        'id': f'sched_{int(time.time()*1000)}',
        'jobId': job_id,
        'destinations': destinations,
        'schedule': schedule,
        'created_at': time.time(),
    }
    items.append(entry)
    _save_schedules(items)
    return jsonify({'ok': True, 'entry': entry, 'total': len(items)})


# /api/hwmeters route removed in C1 cleanup. The fake hardware utilisation
# meters were retired along with Scene 7. No frontend caller remains.


# ---------------------------------------------------------------------------
# Library / Exports endpoints (added in C3)
# Lists rendered export files across all jobs, with reveal-in-Finder and
# delete actions. Backs the new "Exports" section in the Library tab.
# ---------------------------------------------------------------------------

@app.route('/api/exports', methods=['GET'])
def api_list_exports():
    """List every rendered export across all jobs, newest first.
    Walks OUTPUT_DIR/<job>/exports/ and returns mp4/mov files annotated
    with size, mtime, source set name (from snapshot), and a thumbnail
    derived from the clip-index in the filename when available.

    SESSIE 28 — user-scoped: only jobs owned by the signed-in user are
    enumerated. Anonymous callers get an empty list."""
    user_info, err = _require_authed_user()
    if err:
        return err
    caller_id = user_info['user_id']
    items = []
    if not os.path.isdir(OUTPUT_DIR):
        return jsonify({'exports': []})
    try:
        job_ids = os.listdir(OUTPUT_DIR)
    except OSError:
        return jsonify({'exports': []})
    for job_id in job_ids:
        if not _valid_job_id(job_id):
            continue
        exports_dir = os.path.join(OUTPUT_DIR, job_id, 'exports')
        if not os.path.isdir(exports_dir):
            continue
        # Best-effort source-set name + favorites set + ownership check
        # from snapshot (falls back to id / empty set).
        set_name = job_id
        favorites_set = set()
        try:
            snap = _load_job_snapshot(job_id)
            if snap:
                # Ownership filter — skip jobs that aren't this user's.
                if snap.get('user_id') != caller_id:
                    continue
                if snap.get('filename'):
                    set_name = snap['filename']
                favorites_set = set(snap.get('favorites', []) or [])
            else:
                # No snapshot → cannot verify ownership → skip.
                continue
        except Exception:
            continue
        try:
            entries = os.listdir(exports_dir)
        except OSError:
            continue
        for fn in entries:
            if not fn.lower().endswith(('.mp4', '.mov')):
                continue
            fp = os.path.join(exports_dir, fn)
            try:
                st = os.stat(fp)
            except OSError:
                continue
            # SESSIE 43a — filenames volgen nu één van drie patronen:
            #   1. Nieuw (schoon, met sidecar): <label>.mp4 / <label>_landscape.mp4
            #      Metadata komt uit <filename>.meta.json
            #   2. Tussen (sessie 22+): <label>__clip<NN>__<aspect>__<codec>.mp4
            #   3. Oud (pre-sessie 22): export_<NN>_<jobid>_clip<NN>_<type>_<aspect>_<codec>.mp4
            #
            # We proberen eerst de sidecar (meest betrouwbaar — staat los van
            # de filename), dan de patronen #2 en #3 als fallback. Library blijft
            # zo werken op alle bestaande exports.
            thumbnail = None
            clip_idx = None
            aspect = '16:9'

            # Strategie 1: sidecar .meta.json
            sidecar_path = fp + '.meta.json'
            sidecar_used = False
            if os.path.exists(sidecar_path):
                try:
                    with open(sidecar_path, 'r') as f:
                        meta = json.load(f) or {}
                    if isinstance(meta.get('clip_index'), int):
                        clip_idx = meta['clip_index']
                    sidecar_aspect_key = meta.get('aspect')
                    if sidecar_aspect_key:
                        aspect = {
                            'landscape':  '16:9',
                            'vertical':   '9:16',
                            'square':     '1:1',
                            'portrait':   '4:5',
                            'portrait45': '4:5',
                        }.get(sidecar_aspect_key, '16:9')
                    sidecar_used = True
                except (OSError, json.JSONDecodeError, TypeError):
                    sidecar_used = False

            # Strategie 2 + 3: regex-fallback voor pre-sessie43 exports of
            # bestanden waar de sidecar weg is (best-effort delete-cleanup).
            if not sidecar_used:
                m = re.search(r'__clip(\d+)__', fn)
                if not m:
                    m = re.search(r'_clip(\d+)_', fn)
                if m:
                    clip_idx = int(m.group(1))
                asp_match = re.search(r'__(landscape|vertical|square|portrait)__', fn)
                if not asp_match:
                    asp_match = re.search(r'_(landscape|vertical|square|portrait)_', fn)
                if asp_match:
                    fmt = asp_match.group(1)
                    aspect = {
                        'landscape': '16:9',
                        'vertical':  '9:16',
                        'square':    '1:1',
                        'portrait':  '4:5',
                    }.get(fmt, '16:9')
                else:
                    # SESSIE 43a — schone naam zonder aspect-suffix = default 9:16
                    # (zo bouwt _build_export_filename 'm op: vertical wordt
                    # weggelaten als suffix om de meest gangbare case schoon
                    # te houden). Alleen relevant als sidecar ontbreekt.
                    if re.search(r'_landscape\b', fn, re.IGNORECASE):
                        aspect = '16:9'
                    elif re.search(r'_square\b', fn, re.IGNORECASE):
                        aspect = '1:1'
                    elif re.search(r'_portrait\b', fn, re.IGNORECASE):
                        aspect = '4:5'
                    else:
                        aspect = '9:16'

            # Thumbnail-pad o.b.v. clip_idx (uit sidecar of regex).
            if clip_idx is not None:
                thumb_fname = f"thumb_clip{clip_idx:02d}.jpg"
                if os.path.exists(os.path.join(OUTPUT_DIR, job_id, thumb_fname)):
                    thumbnail = thumb_fname

            items.append({
                'job_id': job_id,
                'filename': fn,
                'set_name': set_name,
                'size': st.st_size,
                'mtime': st.st_mtime,
                'thumbnail': thumbnail,
                'aspect': aspect,
                'is_favorite': clip_idx is not None and clip_idx in favorites_set,
                'clip_idx': clip_idx,
            })
    items.sort(key=lambda x: x['mtime'], reverse=True)
    return jsonify({'exports': items})


def _safe_export_path(job_id, filename):
    """Resolve user-supplied <job>/<filename> into a path inside
    OUTPUT_DIR/<job>/exports/. Returns None if the resolved path would
    escape that directory or the file doesn't exist."""
    if not _valid_job_id(job_id):
        return None
    if not filename or '/' in filename or '\\' in filename or '..' in filename:
        return None
    exports_dir = os.path.realpath(os.path.join(OUTPUT_DIR, job_id, 'exports'))
    fp = os.path.realpath(os.path.join(exports_dir, filename))
    # Prefix check — defends against symlinks pointing outside the dir.
    if not fp.startswith(exports_dir + os.sep):
        return None
    if not os.path.isfile(fp):
        return None
    return fp


@app.route('/api/exports/<job_id>/<path:filename>/reveal', methods=['POST'])
def api_reveal_export(job_id, filename):
    """Open Finder with this export selected (macOS-only).
    Quietly no-ops on platforms without `open`."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    fp = _safe_export_path(job_id, filename)
    if not fp:
        return jsonify({'error': 'file not found'}), 404
    try:
        subprocess.Popen(['open', '-R', fp])
        return jsonify({'ok': True})
    except OSError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/exports/<job_id>/<path:filename>/copy-to', methods=['POST'])
def api_copy_export(job_id, filename):
    """Copy an existing export file to a user-chosen folder.
    Used by the per-card "Export to…" button so the user doesn't need to
    re-render — the mp4 already exists in OUTPUT_DIR. Body: {output_dir}."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    fp = _safe_export_path(job_id, filename)
    if not fp:
        return jsonify({'error': 'file not found'}), 404
    body = request.get_json(silent=True) or {}
    target_dir = body.get('output_dir')
    if not isinstance(target_dir, str) or not target_dir.strip():
        return jsonify({'error': 'output_dir is required.'}), 400
    target_dir = os.path.expanduser(target_dir)
    if not os.path.isdir(target_dir):
        return jsonify({'error': "That folder doesn't exist."}), 400
    if not os.access(target_dir, os.W_OK):
        return jsonify({'error': "Cannot write to that folder."}), 400
    try:
        target = os.path.join(target_dir, os.path.basename(fp))
        shutil.copy2(fp, target)
        return jsonify({'ok': True, 'target_path': target})
    except (OSError, shutil.Error) as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/exports/<job_id>/<path:filename>', methods=['DELETE'])
def api_delete_export(job_id, filename):
    """Permanently delete an exported file. UI confirms before calling.

    SESSIE 43a — ook de sidecar .meta.json verwijderen als die bestaat,
    anders blijven er weeskinderen achter die /api/exports laat parsen
    maar waar geen mp4 meer bij hoort."""
    _u, _j, err = _require_job_access(job_id)
    if err:
        return err
    fp = _safe_export_path(job_id, filename)
    if not fp:
        return jsonify({'error': 'file not found'}), 404
    try:
        os.unlink(fp)
        # Best-effort: sidecar mee. Faalt stil als die niet bestaat (oude exports).
        sidecar = fp + '.meta.json'
        if os.path.exists(sidecar):
            try:
                os.unlink(sidecar)
            except OSError:
                pass
        return jsonify({'ok': True})
    except OSError as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Native folder picker — used by the export flow so users can pick where
# rendered clips should land (Downloads, an external drive, etc.).
# macOS uses AppleScript; Windows / Linux fall back to tkinter so we don't
# need any extra dependencies. Both run in the Flask request thread, which
# is fine for a one-shot modal.
# ---------------------------------------------------------------------------

def _default_export_dir():
    """Pick a sensible starting folder when the caller has no preference.
    Prefers ~/Downloads, falls back to the home directory."""
    home = os.path.expanduser('~')
    downloads = os.path.join(home, 'Downloads')
    return downloads if os.path.isdir(downloads) else home


# ---------------------------------------------------------------------------
# SESSIE 69 — native picker via NSOpenPanel (geen Apple-Event).
#
# De osascript-route ('choose file'/'choose folder') is een Apple-Event en
# wordt in de hardened-runtime bundle geblokkeerd zonder het entitlement
# com.apple.security.automation.apple-events. Resultaat: het dialog opent
# nergens en /api/pick-file keert nooit terug → de UI "hangt".
#
# NSOpenPanel draait in-proces (Cocoa/AppKit, via PyObjC dat al binnenkomt
# met pyobjc-framework-Vision) en heeft GEEN Apple-Event nodig. Het werkt
# dus ook onder de hardened runtime. We proberen dit eerst; de osascript-
# variant blijft als fallback (bv. als AppKit ontbreekt in dev).
#
# NSOpenPanel moet op de main thread draaien. Flask-requests draaien op
# worker-threads, dus we marshallen via een __NSObject-helper +
# performSelectorOnMainThread en wachten op het resultaat.
# ---------------------------------------------------------------------------

# Cache zodat we de import-poging niet bij elke klik herhalen.
_NSOPENPANEL_AVAILABLE = None


def _nsopenpanel_supported():
    global _NSOPENPANEL_AVAILABLE
    if _NSOPENPANEL_AVAILABLE is not None:
        return _NSOPENPANEL_AVAILABLE
    if sys.platform != 'darwin':
        _NSOPENPANEL_AVAILABLE = False
        return False
    try:
        import AppKit  # noqa: F401  (pyobjc-framework-Cocoa)
        import objc  # noqa: F401
        _NSOPENPANEL_AVAILABLE = True
    except Exception:
        _NSOPENPANEL_AVAILABLE = False
    return _NSOPENPANEL_AVAILABLE


# SESSIE 75 — _PanelRunner ObjC-class EEN keer op moduleniveau registreren.
# Voorheen stond `class _PanelRunner(NSObject)` BINNEN _pick_with_nsopenpanel,
# waardoor een 2e pick (bv. eerst een set-bestand kiezen, dan de export-map)
# de ObjC-class opnieuw probeerde te registreren -> "_PanelRunner is overriding
# existing Objective-C class" in de gesignde bundle. Nu lazy-once geregistreerd
# + gedeelde state; picks zijn geserialiseerd via _PANEL_LOCK + waitUntilDone,
# dus de gedeelde state is veilig.
_PANEL_RUNNER_CLS = None
_PANEL_LOCK = threading.Lock()
_PANEL_STATE = {}


def _get_panel_runner_cls():
    """Registreer (eenmalig) de NSObject-subclass die het NSOpenPanel op de
    main thread opent, en geef de gecachte class terug. Volgende calls
    her-registreren de ObjC-class NIET."""
    global _PANEL_RUNNER_CLS
    if _PANEL_RUNNER_CLS is not None:
        return _PANEL_RUNNER_CLS
    import AppKit
    from Foundation import NSObject, NSURL

    class _PanelRunner(NSObject):
        def run_(self, _arg):
            st = _PANEL_STATE
            try:
                panel = AppKit.NSOpenPanel.openPanel()
                panel.setCanChooseFiles_(not st['choose_dirs'])
                panel.setCanChooseDirectories_(st['choose_dirs'])
                panel.setAllowsMultipleSelection_(False)
                panel.setResolvesAliases_(True)
                if st.get('prompt'):
                    try:
                        panel.setMessage_(str(st['prompt']))
                    except Exception:
                        pass
                if st.get('default_dir') and os.path.isdir(st['default_dir']):
                    try:
                        panel.setDirectoryURL_(
                            NSURL.fileURLWithPath_(str(st['default_dir'])))
                    except Exception:
                        pass
                # Breng het panel naar de voorgrond (de Flask-app heeft geen
                # echt app-venster, dus zonder dit kan het achter Chrome vallen).
                try:
                    AppKit.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
                except Exception:
                    pass
                rc = panel.runModal()
                if rc == AppKit.NSModalResponseOK or rc == 1:
                    urls = panel.URLs()
                    if urls and len(urls) > 0:
                        st['path'] = urls[0].path()
                # else: cancel → path blijft None
            except Exception as exc:
                st['err'] = str(exc)
            finally:
                st['done'] = True

    _PANEL_RUNNER_CLS = _PanelRunner
    return _PanelRunner


def _pick_with_nsopenpanel(prompt, default_dir, choose_dirs):
    """Open an NSOpenPanel on the main thread and return (path|None, err|None).

    choose_dirs=True → folder picker; False → file picker.
    Returns (None, None) on user-cancel, (path, None) on success,
    (None, err_string) on a real error so the caller can fall back."""
    try:
        import objc
        Runner = _get_panel_runner_cls()
    except Exception as e:  # AppKit niet beschikbaar → laat caller terugvallen
        return None, f'AppKit unavailable: {e}'

    # Picks serialiseren: gedeelde _PANEL_STATE + één modaal dialoog tegelijk.
    with _PANEL_LOCK:
        _PANEL_STATE.clear()
        _PANEL_STATE.update({
            'path': None, 'err': None, 'done': False,
            'choose_dirs': bool(choose_dirs),
            'prompt': prompt, 'default_dir': default_dir,
        })
        try:
            runner = Runner.alloc().init()
            # waitUntilDone=True blokkeert deze worker-thread tot de main thread
            # het panel heeft afgehandeld.
            runner.performSelectorOnMainThread_withObject_waitUntilDone_(
                objc.selector(runner.run_, signature=b'v@:@'), None, True)
        except Exception as e:
            return None, f'NSOpenPanel dispatch failed: {e}'

        if not _PANEL_STATE['done']:
            return None, 'NSOpenPanel did not complete'
        if _PANEL_STATE['err']:
            return None, _PANEL_STATE['err']
        return _PANEL_STATE['path'], None


def _pick_folder_macos(prompt, default_dir):
    # SESSIE 71 — NSOpenPanel ALLEEN in de gepackagede bundle (sys.frozen). Op de
    # dev-server draait de main thread Flask's serve-loop (geen Cocoa run-loop),
    # dus performSelectorOnMainThread hangt, en de in-functie ObjC-class-definitie
    # crasht bij de 2e aanroep -> 500. De osascript-route is een los subprocess
    # (thread-safe) en werkt prima op dev. In de bundle blokkeert hardened runtime
    # Apple-Events, daar is NSOpenPanel nodig.
    # SESSIE 75 — osascript EERST. Een los subprocess heeft een eigen run-loop en
    # toont het dialog betrouwbaar (ook in de bundle: het apple-events entitlement
    # zit er sinds sessie 69 in). NSOpenPanel was in de Flask-bundle main-thread-
    # afhankelijk en toonde het paneel pas bij de 2e klik. Bij een osascript-fout
    # vallen we terug op NSOpenPanel (alleen in de frozen bundle).
    safe_prompt = (prompt or 'Choose a folder').replace('"', '')
    if default_dir and os.path.isdir(default_dir):
        # POSIX path → AppleScript "POSIX file" alias.
        safe_default = default_dir.replace('"', '')
        default_clause = f' default location (POSIX file "{safe_default}")'
    else:
        default_clause = ''
    script = (
        'try\n'
        f'  set chosen to choose folder with prompt "{safe_prompt}"{default_clause}\n'
        '  return POSIX path of chosen\n'
        'on error number -128\n'
        '  return ""\n'
        'end try'
    )
    osa_err = None
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            path = (result.stdout or '').strip()
            return (path or None), None   # success, of nette cancel (path='')
        osa_err = (result.stderr or 'osascript returned non-zero').strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        osa_err = f'osascript failed: {e}'

    if getattr(sys, 'frozen', False) and _nsopenpanel_supported():
        print(f'[pick-folder] osascript faalde, fallback NSOpenPanel: {osa_err}', flush=True)
        return _pick_with_nsopenpanel(prompt, default_dir, choose_dirs=True)
    return None, osa_err


def _pick_folder_tk(prompt, default_dir):
    """Windows / Linux fallback. tkinter ships with the stdlib on every
    desktop CPython build we care about. Runs the dialog in this thread —
    safe for one-shot askdirectory."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as e:
        return None, f'tkinter not available: {e}'
    initial = default_dir if (default_dir and os.path.isdir(default_dir)) else _default_export_dir()
    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        # Bring the dialog to the front so it's not hidden behind the browser.
        try:
            root.attributes('-topmost', True)
        except tk.TclError:
            pass
        path = filedialog.askdirectory(
            title=prompt or 'Choose a folder',
            initialdir=initial,
            mustexist=True,
        )
    except Exception as e:
        return None, str(e)
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass
    return (path or None), None


@app.route('/api/pick-folder', methods=['POST'])
def api_pick_folder():
    """Open a native folder-picker. Returns the chosen absolute path,
    or null when the user cancels. Cross-platform: macOS uses AppleScript,
    Windows / Linux use tkinter.askdirectory."""
    body = request.get_json(silent=True) or {}
    prompt = body.get('prompt') or 'Choose where to save your exports'
    default_dir = body.get('default_dir')

    # SESSIE 71 — vang elke onverwachte fout op zodat de UI altijd JSON krijgt
    # i.p.v. een rauwe HTML 500 (de oude NSOpenPanel-crash gaf precies dat).
    try:
        if sys.platform == 'darwin':
            path, err = _pick_folder_macos(prompt, default_dir)
        else:
            path, err = _pick_folder_tk(prompt, default_dir)
    except Exception as e:
        log.warning("pick-folder crashed: %s", e)
        return jsonify({'ok': False, 'cancelled': False, 'path': None,
                        'error': f'Folder picker failed: {e}', 'platform': sys.platform}), 500

    if err and path is None:
        # Surface the underlying error so the UI can show something useful.
        return jsonify({
            'ok': False,
            'cancelled': False,
            'path': None,
            'error': err,
            'platform': sys.platform,
        }), 500

    if not path:
        return jsonify({
            'ok': True, 'cancelled': True, 'path': None,
            'platform': sys.platform,
        })

    if not os.path.isdir(path):
        return jsonify({
            'ok': False, 'cancelled': False, 'path': path,
            'error': 'Picked path is not a directory.',
            'platform': sys.platform,
        }), 400

    return jsonify({
        'ok': True, 'cancelled': False, 'path': path,
        'platform': sys.platform,
    })


def _pick_file_macos(prompt, default_dir=None):
    """Open a native file-picker on macOS via AppleScript.
    Returns (absolute_path_or_None, error_or_None).
    Works for any file size — no bytes are read, just the path is returned."""
    # SESSIE 71 — NSOpenPanel ALLEEN in de gepackagede bundle (sys.frozen); op de
    # dev-server crasht het (main thread draait Flask, niet de Cocoa run-loop, en
    # de in-functie ObjC-class-def botst bij de 2e aanroep). osascript is een los
    # subprocess en werkt op dev. In de bundle is NSOpenPanel nodig (hardened runtime).
    # SESSIE 75 — osascript EERST (zie _pick_folder_macos). NSOpenPanel als
    # terugval in de frozen bundle.
    safe_prompt = (prompt or 'Choose a DJ set to analyse').replace('"', '')
    if default_dir and os.path.isdir(default_dir):
        safe_default = default_dir.replace('"', '')
        default_clause = f' default location (POSIX file "{safe_default}")'
    else:
        default_clause = ''
    script = (
        'try\n'
        f'  set chosen to choose file with prompt "{safe_prompt}"{default_clause}\n'
        '  return POSIX path of chosen\n'
        'on error number -128\n'
        '  return ""\n'
        'end try'
    )
    osa_err = None
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            path = (result.stdout or '').strip()
            return (path or None), None
        osa_err = (result.stderr or 'osascript returned non-zero').strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        osa_err = f'osascript failed: {e}'

    if getattr(sys, 'frozen', False) and _nsopenpanel_supported():
        print(f'[pick-file] osascript faalde, fallback NSOpenPanel: {osa_err}', flush=True)
        return _pick_with_nsopenpanel(prompt, default_dir, choose_dirs=False)
    return None, osa_err


def _pick_file_tk(prompt, default_dir=None):
    """Windows / Linux fallback for native file picker.
    Uses tkinter.filedialog.askopenfilename — ships with stdlib CPython."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as e:
        return None, f'tkinter not available: {e}'
    initial = default_dir if (default_dir and os.path.isdir(default_dir)) else os.path.expanduser('~')
    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes('-topmost', True)
        except Exception:
            pass
        path = filedialog.askopenfilename(
            title=prompt or 'Choose a DJ set',
            initialdir=initial,
            filetypes=[
                ('Video / Audio files',
                 '*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.flv *.wmv *.mp3 *.aac *.wav *.flac *.ogg *.m4a'),
                ('All files', '*.*'),
            ],
        )
    except Exception as e:
        return None, str(e)
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass
    return (path or None), None


@app.route('/api/pick-file', methods=['POST'])
def api_pick_file():
    """Open a native file-picker dialog and return the absolute path of the
    chosen file. Works for any file size — no bytes are read or copied,
    the path is simply returned to the frontend which then calls
    /api/upload-local to register it in-place.

    Body (JSON, all optional):
      { prompt: str, default_dir: str }
    Response: { ok, cancelled, path, platform }
    """
    body = request.get_json(silent=True) or {}
    prompt = body.get('prompt') or 'Choose a DJ set to analyse'
    default_dir = body.get('default_dir')

    if sys.platform == 'darwin':
        path, err = _pick_file_macos(prompt, default_dir)
    else:
        path, err = _pick_file_tk(prompt, default_dir)

    if err and path is None:
        return jsonify({
            'ok': False,
            'cancelled': False,
            'path': None,
            'error': err,
            'platform': sys.platform,
        }), 500

    if not path:
        return jsonify({
            'ok': True, 'cancelled': True, 'path': None,
            'platform': sys.platform,
        })

    if not os.path.isfile(path):
        return jsonify({
            'ok': False, 'cancelled': False, 'path': path,
            'error': 'Picked path is not a file.',
            'platform': sys.platform,
        }), 400

    return jsonify({
        'ok': True, 'cancelled': False, 'path': path,
        'platform': sys.platform,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5555
    # Bind to loopback by default. Set OMNI_DJ_BIND=0.0.0.0 to allow LAN
    # (don't do this without adding authentication).
    bind_host = os.environ.get('OMNI_DJ_BIND', '127.0.0.1')

    _purge_old_uploads()
    _rehydrate_jobs_from_history()

    # SESSIE 17 — start the watch-folder daemon. Deps are injected here so
    # watch_folder.py stays decoupled from Flask/Supabase imports. The
    # thread is daemon=True, so it dies cleanly when the process exits.
    try:
        watch_folder.start_daemon({
            'jobs':                 jobs,
            'jobs_lock':            jobs_lock,
            'process_job':          _process_job,
            'load_settings':        _load_settings,
            'validate_video':       _validate_video_file,
            'safe_filename':        _safe_filename,
            'check_disk_space':     _check_disk_space,
            'get_profile':          _get_or_refresh_profile,
            'append_history':       _append_to_history,
            'log':                  log,
            'UPLOAD_DIR':           UPLOAD_DIR,
            'OUTPUT_DIR':           OUTPUT_DIR,
            'WATCH_FOLDER_PATH':    WATCH_FOLDER_PATH,
            'VIDEO_EXTS_ALLOWED':   VIDEO_EXTS_ALLOWED,
            'LARGE_FILE_PIPELINE':  LARGE_FILE_PIPELINE,
        })
    except Exception as e:
        log.warning("Watch-folder daemon failed to start: %s", e)

    print(f"\n{'='*52}")
    print(f"  Omni DJ — DJ Set Clip Cutter")
    print(f"  Open: http://{bind_host}:{port}")
    print(f"  Demucs AI : {'Available ✓' if HAS_DEMUCS else 'Not installed (pip install torch demucs)'}")
    print(f"  Audio out : 44.1 kHz AAC 320k — full 20 Hz–20 kHz spectrum ✓")
    print(f"{'='*52}\n")
    app.run(host=bind_host, port=port, debug=False)
