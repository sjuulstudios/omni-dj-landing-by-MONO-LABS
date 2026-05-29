"""
Watch-folder daemon for DJ Clip Cutter.

Background polling thread that auto-processes new audio/video files
dropped into a configured local folder. Pro-tier feature.

Architecture:
  • Single daemon thread started by `start_daemon()`. Idempotent — calling
    it twice is a no-op.
  • Polls the configured folder every WATCH_TICK_SECONDS (default 5 s).
  • Tracks seen files by (path, size, mtime, sha256 of first 1 MB).
    A file is "new" iff its (size, mtime, partial-hash) tuple is not yet
    in `seen_files`. SHA over the first 1 MB is enough to catch most
    re-encodes without paying the cost of hashing a 4-hour set.
  • Skips files whose mtime delta over two consecutive ticks is non-zero
    (still being copied / written by Dropbox sync) and files whose
    `.processing` sibling marker is present (already claimed by another
    worker).
  • Before kicking off a job: re-checks the user's plan (must be pro
    or studio) and quota. Quota exhausted → log + status flag, no job
    started, no retry until the next file lands.
  • Hands the file off to the *same* `_process_job` pipeline that
    /api/upload-local uses (in-place register, no copy), so behaviour
    is identical to a manual no-copy upload.

Persistence (`watch_folder.json`):
    {
      "path":        "/Users/.../Dropbox/DJ-Sets",  // configured folder
      "active":      true,
      "user_id":     "<uuid>",                       // owner of this watch
      "seen":        { "<rel-path>": {size, mtime, sha, started_at, job_id} },
      "stats":       { "processed_total": 12,
                       "skipped_quota":   3,
                       "errors_total":    0 },
      "last_tick":   1715318400.0,
      "last_error":  null,                           // {msg, ts} | null
      "queue":       ["pending-file-1.mp4", ...],    // upcoming
      "in_flight":   "current-file.mp4" | null
    }

Public API (called from app.py):
    start_daemon(deps)         — start the background thread (idempotent).
    get_config()               — read the JSON blob.
    save_config(path, active,  — atomically update path/active/user_id.
                user_id)
    get_status()               — light-weight status feed for the UI.
    reset_seen()               — wipe the seen-files cache (rare; debug only).

`deps` is a dict injected by app.py at startup so this module stays free
of import-time dependencies on Flask/Supabase:
    {
      'jobs':                       # the global jobs dict
      'jobs_lock':                  # threading.Lock guarding it
      'process_job':                # _process_job callable
      'load_settings':              # _load_settings callable
      'validate_video':             # _validate_video_file callable
      'safe_filename':              # _safe_filename callable
      'check_disk_space':           # _check_disk_space callable
      'get_profile':                # _get_or_refresh_profile callable
      'append_history':             # _append_to_history callable
      'log':                        # logger
      'UPLOAD_DIR':                 # path str (uploads dir)
      'OUTPUT_DIR':                 # path str (output dir)
      'WATCH_FOLDER_PATH':          # path to the JSON blob
      'VIDEO_EXTS_ALLOWED':         # tuple of extensions to pick up
      'LARGE_FILE_PIPELINE':        # bool flag
    }
"""

from __future__ import annotations

import os
import json
import time
import uuid
import hashlib
import threading

# ---------------------------------------------------------------------------
# Tunables — kept as module-level so they can be tweaked at runtime via
# `watch_folder.WATCH_TICK_SECONDS = 10`, useful for tests / debug.
# ---------------------------------------------------------------------------
WATCH_TICK_SECONDS    = float(os.environ.get('WATCH_TICK_SECONDS', '5'))
WATCH_QUIET_SECONDS   = float(os.environ.get('WATCH_QUIET_SECONDS', '4'))  # file must be still that long
WATCH_HASH_PREFIX_MB  = float(os.environ.get('WATCH_HASH_PREFIX_MB', '1'))
WATCH_MAX_QUEUE       = int(os.environ.get('WATCH_MAX_QUEUE', '20'))
PAID_PLANS            = ('pro', 'studio')

# ---------------------------------------------------------------------------
# Module-level state. Guarded by `_lock`.
# ---------------------------------------------------------------------------
_lock         = threading.Lock()
_deps         = None        # injected via start_daemon()
_thread       = None        # the polling thread
_stop_event   = threading.Event()


def _now() -> float:
    return time.time()


def _atomic_write_json(path: str, data: dict) -> None:
    """Write JSON atomically — temp file + rename — so a crashed write
    doesn't corrupt the blob."""
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, path)
    except OSError:
        # Best-effort: leave the previous blob in place.
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        raise


def _default_blob() -> dict:
    return {
        'path':       None,
        'active':     False,
        'user_id':    None,
        'seen':       {},
        'stats':      {
            'processed_total': 0,
            'skipped_quota':   0,
            'errors_total':    0,
        },
        'last_tick':  None,
        'last_error': None,
        'queue':      [],
        'in_flight':  None,
        'updated':    None,
    }


def _load_blob() -> dict:
    """Read the JSON blob with defaults filled in. Read-modify-write callers
    should hold `_lock` for the full duration so two ticks don't clobber
    each other."""
    path = _deps['WATCH_FOLDER_PATH']
    if not os.path.exists(path):
        return _default_blob()
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        _deps['log'].warning("watch_folder: failed to read %s: %s", path, e)
        return _default_blob()
    # Merge with defaults so older blobs from the stub endpoint don't crash us.
    base = _default_blob()
    if isinstance(data, dict):
        for k, v in data.items():
            base[k] = v
    return base


def _save_blob(blob: dict) -> None:
    path = _deps['WATCH_FOLDER_PATH']
    blob['updated'] = _now()
    _atomic_write_json(path, blob)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_config() -> dict:
    """Return the watch-folder config (path / active / user_id / stats).
    Safe to call from any thread."""
    with _lock:
        return _load_blob()


def save_config(path, active, user_id):
    """Atomically update the watch-folder config. Called by the
    /api/watch-folder POST endpoint after the auth + plan check passes.

    `path`     — absolute folder path or None to clear.
    `active`   — bool, whether the daemon should poll this path.
    `user_id`  — Supabase user_id of the owner (used for quota).

    Resets `seen_files` whenever the path changes so a new folder gets
    a clean slate. Preserves stats and seen-cache when only `active`
    flips.
    """
    with _lock:
        blob = _load_blob()
        old_path = blob.get('path')
        new_path = (path or None)
        if new_path != old_path:
            blob['seen'] = {}
            blob['queue'] = []
            blob['in_flight'] = None
            blob['last_error'] = None
        blob['path']    = new_path
        blob['active']  = bool(active) and bool(new_path)
        blob['user_id'] = user_id or None
        _save_blob(blob)
        return blob


def get_status() -> dict:
    """Light-weight status feed for the UI poll (~ every 5 s)."""
    with _lock:
        blob = _load_blob()
    return {
        'path':         blob.get('path'),
        'active':       bool(blob.get('active')),
        'user_id':      blob.get('user_id'),
        'last_tick':    blob.get('last_tick'),
        'last_error':   blob.get('last_error'),
        'queue':        list(blob.get('queue') or [])[:WATCH_MAX_QUEUE],
        'queue_count':  len(blob.get('queue') or []),
        'in_flight':    blob.get('in_flight'),
        'stats':        dict(blob.get('stats') or {}),
        'tick_seconds': WATCH_TICK_SECONDS,
    }


def reset_seen():
    """Wipe the seen-files cache. Lets the user "re-process everything in
    the folder" without manually re-dropping files. Stats are preserved."""
    with _lock:
        blob = _load_blob()
        blob['seen'] = {}
        blob['queue'] = []
        blob['in_flight'] = None
        blob['last_error'] = None
        _save_blob(blob)
        return blob


# ---------------------------------------------------------------------------
# Polling loop
# ---------------------------------------------------------------------------

def _hash_prefix(path: str, mb: float = WATCH_HASH_PREFIX_MB) -> str | None:
    """SHA-256 of the first N MB of `path`. Returns None on read failure."""
    n = int(mb * 1024 * 1024)
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            buf = f.read(n)
            h.update(buf)
        return h.hexdigest()
    except OSError:
        return None


def _scan_folder(folder: str):
    """Yield (abs_path, basename, size, mtime) for every allowed media file
    directly inside `folder`. Recursion is intentionally avoided — Dropbox /
    Drive folders nest deeply and the user expects "drop into this folder
    and Clip Live picks it up", not "find files anywhere underneath"."""
    if not folder or not os.path.isdir(folder):
        return
    allowed = _deps['VIDEO_EXTS_ALLOWED']
    try:
        names = os.listdir(folder)
    except OSError as e:
        _deps['log'].warning("watch_folder: cannot list %s: %s", folder, e)
        return
    for name in names:
        if name.startswith('.'):
            continue                                 # hide dotfiles, .DS_Store
        if name.endswith('.processing') or name.endswith('.tmp'):
            continue
        p = os.path.join(folder, name)
        if not os.path.isfile(p):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext not in allowed:
            continue
        try:
            st = os.stat(p)
        except OSError:
            continue
        yield (p, name, int(st.st_size), float(st.st_mtime))


def _record_seen(blob: dict, name: str, size: int, mtime: float,
                 sha: str | None, job_id: str | None) -> None:
    seen = blob.setdefault('seen', {})
    seen[name] = {
        'size':       size,
        'mtime':      mtime,
        'sha':        sha,
        'started_at': _now(),
        'job_id':     job_id,
    }


def _is_seen(blob: dict, name: str, size: int, mtime: float, sha: str | None) -> bool:
    rec = (blob.get('seen') or {}).get(name)
    if not rec:
        return False
    # Same name + same size + same hash → assume same file. mtime alone is
    # unreliable on macOS (Spotlight, Dropbox, etc. touch mtime).
    if rec.get('size') != size:
        return False
    if sha and rec.get('sha') and sha != rec.get('sha'):
        return False
    return True


def _start_job_for(path: str, blob: dict) -> str | None:
    """Build the in-memory job record + kick off `_process_job` in its own
    thread, exactly as /api/upload-local does. Returns the new job_id, or
    None if the source couldn't be validated."""
    log = _deps['log']
    settings = _deps['load_settings']()
    valid, info = _deps['validate_video'](path)
    if not valid:
        log.warning("watch_folder: invalid file %s: %s", path, info)
        return None

    duration = float(info.get('duration', 0)) if isinstance(info, dict) else 0.0
    est_gb = max(2.0, (duration * 1.0 * 1024 * 1024) / (1024 ** 3) * 1.5)
    disk_ok, _free = _deps['check_disk_space'](_deps['OUTPUT_DIR'], required_gb=est_gb)
    if not disk_ok:
        log.warning("watch_folder: not enough disk for %s (est %.1f GB)", path, est_gb)
        return None

    job_id = str(uuid.uuid4())[:8]
    safe_name = _deps['safe_filename'](os.path.basename(path))

    clip_duration   = max(5,  min(300, int(settings.get('clip_duration', 30))))
    min_gap         = max(5,  min(300, int(settings.get('min_gap', 30))))
    bars_before     = max(1,  min(32,  int(settings.get('bars_before', 4))))
    bars_after      = max(1,  min(32,  int(settings.get('bars_after', 4))))
    sensitivity     = max(0.0, min(1.0, float(settings.get('sensitivity', 0.5))))
    formats         = settings.get('formats') or ['landscape', 'vertical']
    formats         = [f for f in formats if f in ('landscape', 'vertical')] or ['landscape', 'vertical']
    use_demucs      = bool(settings.get('use_demucs', False))
    normalize_audio = bool(settings.get('normalize_audio', False))
    overlay_text    = settings.get('overlay_text', None)

    jobs      = _deps['jobs']
    jobs_lock = _deps['jobs_lock']
    user_id   = blob.get('user_id')

    with jobs_lock:
        jobs[job_id] = {
            'id': job_id,
            'filename': safe_name,
            'video_path': path,              # in-place, no copy
            'no_copy': True,
            'watched': True,                 # marker so UI can show "auto"
            'user_id': user_id,
            'usage_counted': False,
            'status': 'queued',
            'message': 'Auto-picked up by watch folder — analysing...',
            'clips': [], 'results': [], 'waveform': [], 'filmstrip': [],
            'duration': duration,
            'video_info': info if isinstance(info, dict) else {},
            'fps': info.get('fps') if isinstance(info, dict) else None,
            'bpm': {}, 'favorites': [],
            'settings': {
                'clip_duration': clip_duration, 'min_gap': min_gap,
                'sensitivity': sensitivity, 'formats': formats,
                'use_demucs': use_demucs, 'normalize_audio': normalize_audio,
                'overlay_text': overlay_text,
                'bars_before': bars_before, 'bars_after': bars_after,
            },
        }

    th = threading.Thread(
        target=_deps['process_job'],
        args=(job_id, path, clip_duration, min_gap, formats,
              sensitivity, use_demucs, normalize_audio, overlay_text,
              bars_before, bars_after),
        daemon=True,
    )
    th.start()
    log.info("watch_folder: started job %s for %s", job_id, path)
    return job_id


def _wait_for_inflight_to_finish(job_id: str, max_wait: float = 60 * 60) -> bool:
    """Block (in the daemon thread) until the given job is no longer in
    a pre-terminal status. Returns True if it ended in done/ready, False
    on timeout/error. Sleeps in 2-second ticks. Allows the daemon to be
    naturally serial — only one watched job runs at a time, so a Pro user
    cycling through their CPU budget never sees three sets crunching at once.
    """
    jobs      = _deps['jobs']
    jobs_lock = _deps['jobs_lock']
    deadline = _now() + max_wait
    while _now() < deadline:
        if _stop_event.is_set():
            return False
        with jobs_lock:
            j = jobs.get(job_id) or {}
            status = str(j.get('status', '')).lower()
        if status in ('done', 'ready', 'complete', 'completed'):
            return True
        if status in ('error', 'failed'):
            return False
        time.sleep(2)
    return False


def _tick():
    """Run one polling iteration. Idempotent and exception-safe — anything
    that goes wrong is logged + recorded on `last_error` so the UI can
    surface it, but never raises out of the daemon thread."""
    log = _deps['log']
    try:
        with _lock:
            blob = _load_blob()

        if not blob.get('active') or not blob.get('path'):
            return
        folder = blob['path']
        if not os.path.isdir(folder):
            with _lock:
                blob = _load_blob()
                blob['last_error'] = {
                    'msg': f'Watch folder is missing on disk: {folder}',
                    'ts':  _now(),
                }
                blob['last_tick'] = _now()
                _save_blob(blob)
            return

        # Plan + quota — bail fast on Free.
        user_id = blob.get('user_id')
        if not user_id:
            return
        snap = _deps['get_profile'](user_id)
        if not snap.get('ok'):
            log.warning("watch_folder: profile read failed for %s: %s",
                        user_id, snap.get('error'))
            return
        plan = (snap.get('plan') or 'free').lower()
        if plan not in PAID_PLANS:
            # Plan downgraded since the daemon was activated.
            with _lock:
                blob = _load_blob()
                blob['active'] = False
                blob['last_error'] = {
                    'msg': 'Watch folder paused — plan no longer includes this feature.',
                    'ts':  _now(),
                }
                _save_blob(blob)
            return

        # Scan folder, pick the FIRST file that's:
        #   • not in seen{}
        #   • mtime > WATCH_QUIET_SECONDS ago (i.e. still settling)
        #   • not currently in_flight elsewhere
        candidates = list(_scan_folder(folder))
        now = _now()

        # Refresh blob so seen{} is fresh inside the loop.
        with _lock:
            blob = _load_blob()

        # Re-scan with fresh seen{}.
        skipped_quota = False
        picked = None
        for (abs_path, name, size, mtime) in candidates:
            if (now - mtime) < WATCH_QUIET_SECONDS:
                continue                                # still being written
            # Cheap pre-check before hashing.
            rec = (blob.get('seen') or {}).get(name)
            if rec and rec.get('size') == size and abs(rec.get('mtime', 0) - mtime) < 0.5:
                continue
            sha = _hash_prefix(abs_path)
            if _is_seen(blob, name, size, mtime, sha):
                continue
            # Found a new file — but check quota first.
            used  = snap.get('used', 0)
            limit = snap.get('limit', 0)
            if isinstance(limit, (int, float)) and limit != float('inf') and used >= limit:
                skipped_quota = True
                break
            picked = (abs_path, name, size, mtime, sha)
            break

        with _lock:
            blob = _load_blob()
            blob['last_tick'] = now
            if skipped_quota:
                blob['stats']['skipped_quota'] = int(blob['stats'].get('skipped_quota', 0)) + 1
                blob['last_error'] = {
                    'msg': 'Quota exhausted — auto-processing paused until reset.',
                    'ts':  now,
                }
            elif picked is None:
                # Clear the error from previous tick if we had one but now folder is healthy.
                err = blob.get('last_error')
                if err and ('missing on disk' in (err.get('msg') or '')
                            or 'Quota exhausted' in (err.get('msg') or '')):
                    blob['last_error'] = None
            else:
                blob['in_flight'] = picked[1]
            _save_blob(blob)

        if picked is None:
            return

        abs_path, name, size, mtime, sha = picked
        job_id = _start_job_for(abs_path, blob)
        with _lock:
            blob = _load_blob()
            _record_seen(blob, name, size, mtime, sha, job_id)
            if job_id is None:
                blob['stats']['errors_total'] = int(blob['stats'].get('errors_total', 0)) + 1
                blob['last_error'] = {
                    'msg': f'Could not start job for {name} — invalid file or low disk.',
                    'ts':  _now(),
                }
                blob['in_flight'] = None
            _save_blob(blob)

        if job_id:
            # Block until done so we never start a second one in parallel.
            ok = _wait_for_inflight_to_finish(job_id)
            with _lock:
                blob = _load_blob()
                blob['in_flight'] = None
                if ok:
                    blob['stats']['processed_total'] = int(blob['stats'].get('processed_total', 0)) + 1
                    blob['last_error'] = None
                else:
                    blob['stats']['errors_total'] = int(blob['stats'].get('errors_total', 0)) + 1
                    blob['last_error'] = {
                        'msg': f'Job {job_id} for {name} did not finish cleanly.',
                        'ts':  _now(),
                    }
                _save_blob(blob)

    except Exception as e:                            # never let the loop die
        try:
            _deps['log'].exception("watch_folder tick crashed: %s", e)
        except Exception:
            pass
        try:
            with _lock:
                blob = _load_blob()
                blob['last_error'] = {
                    'msg': f'Internal error: {type(e).__name__}: {e}',
                    'ts':  _now(),
                }
                blob['last_tick'] = _now()
                _save_blob(blob)
        except Exception:
            pass


def _loop():
    """Top-level thread body. Polls on a fixed cadence; sleeping is broken
    up so a stop_event can interrupt without waiting the full tick."""
    _deps['log'].info("watch_folder: daemon started (tick=%.1fs)", WATCH_TICK_SECONDS)
    while not _stop_event.is_set():
        _tick()
        # Sleep in 0.5 s slices so stop is responsive
        slept = 0.0
        while slept < WATCH_TICK_SECONDS and not _stop_event.is_set():
            time.sleep(0.5)
            slept += 0.5
    _deps['log'].info("watch_folder: daemon stopped")


def start_daemon(deps: dict) -> None:
    """Start the polling thread. Safe to call multiple times — only the
    first call wires `deps` and spins the thread. Subsequent calls re-use
    the same singleton."""
    global _deps, _thread
    with _lock:
        if _thread is not None and _thread.is_alive():
            return                                    # already running
        _deps = deps
        _stop_event.clear()
        _thread = threading.Thread(target=_loop, daemon=True, name='watch-folder')
        _thread.start()


def stop_daemon() -> None:
    """Signal the daemon to exit and wait briefly for it. Used by tests
    and graceful-shutdown hooks; the app itself relies on daemon=True
    threads dying when the process exits."""
    global _thread
    _stop_event.set()
    th = _thread
    if th is not None:
        th.join(timeout=5)
        _thread = None
