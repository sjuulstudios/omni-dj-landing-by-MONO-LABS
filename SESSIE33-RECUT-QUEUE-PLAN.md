# Sessie 33 — Plan: `/api/recut` background-queue

> Geschreven aan eind sessie 33 (2026-05-23) als voorbereiding voor sessie 34.
> Code is NIET geschreven — Sjuul moet eerst plan reviewen voor we beginnen.

## Waarom

Na auto-track triggert `_applyTrackingToClipAndRecut` synchroon `/api/recut`.
ffmpeg blokkeert de request 5–30s afhankelijk van clip-lengte (Lisa Korver
stretch tot 2:16 = ~25s). Browser ziet alleen een spinner, geen progress,
geen "cancel". Slecht voor lange stretches.

Andere callers (split-clip, add-marker, editor Trim-knop) hebben hetzelfde
patroon maar minder pijn omdat clips daar korter zijn.

## Doel

`/api/recut/<job_id>` kan optioneel async draaien via `?async=1`. Frontend
pollt `/api/recut-status/<recut_id>` voor progress. Backwards compatible:
zonder `?async=1` blijft synchroon werkend zoals nu.

## Scope

**In scope (sessie 34):**
- Backend infrastructuur (_RECUT_QUEUE + worker thread + 2 endpoints)
- Frontend in `_applyTrackingToClipAndRecut` switchen naar async

**Out of scope (eventueel later):**
- Andere recut-callsites (Trim-knop, split-clip, add-marker) switchen
- Cancel-endpoint
- ETA-berekening

## Architectuur

### Backend — `app.py`

```python
# Bij de andere job-state dicts (regel ~120):
_RECUT_QUEUE_LOCK = threading.Lock()
_RECUT_QUEUE = {}  # recut_id (str uuid) -> {
                   #   'status': 'queued'|'running'|'done'|'failed'|'cancelled',
                   #   'user_id': str,
                   #   'job_id': str,
                   #   'clip_index': int,
                   #   'progress': float (0..1),
                   #   'started_at': float (epoch),
                   #   'finished_at': float|None,
                   #   'files': dict|None,
                   #   'error': str|None,
                   # }
_RECUT_TTL = 600  # 10 min — purge old entries
```

**Refactor `/api/recut/<job_id>`:**

```python
@app.route('/api/recut/<job_id>', methods=['POST'])
@limiter.limit("60 per hour", key_func=_rate_limit_key)
def recut(job_id):
    u, j, err = _require_job_access(job_id)
    if err: return err
    
    data = request.json or {}
    is_async = (request.args.get('async') == '1') or bool(data.get('async'))
    
    # ... all the existing validation (start, end, clip_index, video_path, etc.)
    
    if not is_async:
        # EXISTING synchronous flow — unchanged, returns {success, files}
        return _do_recut_synchronous(...)
    
    # ASYNC flow — spawn worker, return recut_id immediately
    recut_id = uuid.uuid4().hex[:16]
    with _RECUT_QUEUE_LOCK:
        _purge_old_recut_entries()  # houd queue klein
        _RECUT_QUEUE[recut_id] = {
            'status': 'queued',
            'user_id': u['id'],
            'job_id': job_id,
            'clip_index': clip_index,
            'progress': 0.0,
            'started_at': time.time(),
            'finished_at': None,
            'files': None,
            'error': None,
        }
    
    worker = threading.Thread(
        target=_recut_worker,
        args=(recut_id, video_path, start, end, job_output_dir, clip_index,
              clip_type, formats, overlay_text, normalize_audio, job_id),
        daemon=True,
    )
    worker.start()
    
    return jsonify({'recut_id': recut_id, 'status': 'queued'}), 202


def _recut_worker(recut_id, *args, **kwargs):
    """Run in background thread; updates _RECUT_QUEUE[recut_id] as it progresses."""
    try:
        with _RECUT_QUEUE_LOCK:
            _RECUT_QUEUE[recut_id]['status'] = 'running'
        
        files = recut_clip(*args, **kwargs)
        
        # Same in-job-state update as synchronous path
        with jobs_lock:
            # ... promote/update clip in job['results'] ...
            _persist_job_snapshot(...)
        
        with _RECUT_QUEUE_LOCK:
            entry = _RECUT_QUEUE.get(recut_id)
            if entry:
                entry['status'] = 'done'
                entry['progress'] = 1.0
                entry['files'] = files
                entry['finished_at'] = time.time()
    except Exception as e:
        log.exception("Background recut failed for %s", recut_id)
        with _RECUT_QUEUE_LOCK:
            entry = _RECUT_QUEUE.get(recut_id)
            if entry:
                entry['status'] = 'failed'
                entry['error'] = f"{type(e).__name__}: {e}"
                entry['finished_at'] = time.time()


@app.route('/api/recut-status/<recut_id>', methods=['GET'])
@limiter.limit("600 per hour", key_func=_rate_limit_key)
def recut_status(recut_id):
    u = _require_authed_user(allow_query_token=True)
    if not u: return jsonify({'error': 'unauthenticated'}), 401
    
    with _RECUT_QUEUE_LOCK:
        entry = _RECUT_QUEUE.get(recut_id)
        if not entry:
            return jsonify({'error': 'recut_id not found'}), 404
        # Ownership check — even bij correct recut_id mag alleen owner zien
        if entry['user_id'] != u['id']:
            return jsonify({'error': 'not found'}), 404
        snapshot = dict(entry)
    
    return jsonify(snapshot)
```

**Edge cases:**

1. **Browser sluit tijdens recut**: worker draait gewoon door, entry blijft
   10 min in queue. Frontend kan bij re-open job opnieuw status fetchen.
2. **Memory leak**: `_purge_old_recut_entries()` verwijdert entries ouder
   dan `_RECUT_TTL` (10 min na finished_at). Bij elke nieuwe enqueue.
3. **Race tussen worker en main thread**: alle state-updates in
   `_RECUT_QUEUE` zitten onder `_RECUT_QUEUE_LOCK`. `jobs_lock` blijft
   de single source of truth voor `jobs[job_id]`.
4. **Te veel parallelle workers**: voor v1 geen rate-limit op aantal
   workers. Bij beta-feedback evt. een max-2-per-user toevoegen.
5. **`recut_clip` heeft geen progress callback**: progress blijft 0.0
   tot 1.0 — geen tussentijdse update mogelijk zonder ffmpeg-progress
   parsen. Eerste versie: alleen status (`queued`/`running`/`done`/`failed`).

### Frontend — `static/index.html`

```javascript
// SESSIE 33+ — async recut helper. Returns final files dict or throws.
async function _recutAsync(jobId, body){
  // Enqueue
  const enq = await api(`/api/recut/${jobId}?async=1`, {
    method: 'POST', body
  });
  const recutId = enq.recut_id;
  if (!recutId) throw new Error('no recut_id returned');
  
  // Poll every 750ms with single-flight + 60s timeout
  const startedAt = Date.now();
  while (Date.now() - startedAt < 60000) {
    await new Promise(r => setTimeout(r, 750));
    const st = await api(`/api/recut-status/${recutId}`);
    if (st.status === 'done')   return st.files;
    if (st.status === 'failed') throw new Error(st.error || 'recut failed');
    if (st.status === 'cancelled') throw new Error('recut cancelled');
    // queued/running → keep polling
  }
  throw new Error('recut timeout after 60s');
}
```

In `_applyTrackingToClipAndRecut`: vervang het synchronous-recut blok door
`await _recutAsync(jobId, {start, end, clip_index, clip_type})`. Toon een
progress-toast met "Recutting clip..." totdat het klaar is.

## Risico's

- **Lock ordering**: pas op dat `_RECUT_QUEUE_LOCK` nooit binnen `jobs_lock`
  wordt gepakt of v.v. — anders deadlock. Patroon: pak queue-lock alleen
  in worker bij state-update, en altijd LAATSTE.
- **Sessions / Flask context**: worker thread heeft geen Flask app context.
  Alles wat Flask-specifiek is (`current_app`, `g`, `session`) NIET aanroepen
  vanuit `_recut_worker` — geef alles als args mee.
- **Recut van clip die nog niet bestaat in `results`** (lazy-render case):
  bestaande synchrone flow heeft logica om vanuit `clips` te promoten naar
  `results`. Die logica moet 1-op-1 mee in `_recut_worker`.

## Test-flow voor Sjuul (sessie 34)

1. Start dev-server zoals normaal
2. Open een job met >30s clip
3. Open editor → Track → Auto-track DJ
4. Verwacht: snelle response (<1s), geen UI-blok. Progress-toast "Recutting clip..."
5. Na ~25s: clip refresht, video toont nieuwe versie
6. Test edge cases:
   - Browser refresh tijdens recut → job blijft draaien, polling pakt het op
   - 2x snel achter elkaar auto-track triggeren → 2e wint (cancellation)
7. Verifieer in server logs: `_purge_old_recut_entries` werkt na 10 min

## Inschatting

- Backend: ~180 regels in `app.py` (helper + worker + 2 endpoints + purge)
- Frontend: ~50 regels (helper + 1 callsite refactor)
- Test: 30 min

Totaal sessie: ~2-3 uur voor schrijven + verifiëren + integration test.

## Beslispunten voor sessie 34

Vooraf met Sjuul afstemmen:

1. **Default async of opt-in?** Mijn voorstel: opt-in via `?async=1` voor v1,
   alleen `_applyTrackingToClipAndRecut` callsite. Andere recut-paths
   (Trim-knop, split-clip, add-marker) blijven synchroon.
2. **Concurrency cap?** Geen voor v1. Pas instellen bij beta-feedback.
3. **Polling-interval?** 750ms — sweet spot tussen snel feedback en
   niet-spammen. Te overwegen: exponential backoff (start 500ms → 2000ms).
4. **Progress%?** Niet beschikbaar zonder ffmpeg-progress parsen. Voor v1
   alleen status. Voor v2 evt. parse ffmpeg's `-progress` flag.

---

*Plan geschreven omdat sessie 33 autonoom was — Sjuul reviewt eerst voor implementatie.*
