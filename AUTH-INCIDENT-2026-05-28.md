# Auth-incident 2026-05-28: "Library toont sets van ander account"

## Bevinding

Sjuul meldde dat Library sets toonde die van een ander account waren. Dit gebeurde tijdens de huidige dev-server sessie (28 mei middag).

## Backend audit: GOED NIEUWS

De backend is solide. Geen RLS-bypass.

### Routes gecheckt
- `/api/history` (regel 3588): filtert op `user_id == h.user_id`. Anonymous → `[]`. Sessie 28 fix actief.
- `/api/clip/<job_id>/<filename>` (regel 4954): `_require_job_access`. 404 als job niet van jou.
- `/api/source/<job_id>` (regel 4982): idem.
- `/api/thumbnail/<job_id>/<filename>` (regel 5003): idem.
- `/api/filmstrip/<job_id>/<filename>` (regel 5013): idem.
- `/api/download-all/<job_id>` (regel 5023): idem.

### `_require_job_access` flow (regel 1791-1826)
1. Valid-job-id check
2. `_require_authed_user` (Bearer of query-token)
3. In-memory of disk-snapshot lookup
4. **Ownership check**: `job.user_id == user_info.user_id`, anders 404
5. 404-by-default voor onbekend job (geen info-leak)

Dit is een gezond patroon. Geen path-traversal, geen RLS-bypass, geen mogelijk lek op deze laag.

## Hypothesen voor wat Sjuul zag

Aangezien backend solide is, moet de leak elders zitten. Drie hypothesen:

### Hypothese A: frontend cache pollutie (meest waarschijnlijk)

`STATE.history` of localStorage-keys (`clipLive.activeJobId`, `clipLive.trim.<jobid>.<idx>`) bevatten residue van vorige test-sessies. De Library-view leest deze uit en toont entries die in werkelijkheid niet meer accessible zijn voor de huidige user (server geeft 404 op klik).

**Indicators in huidige localStorage:**
- `clipLive.activeJobId = "650d9b55"` (verwijst naar onbekende job)
- 8 `clipLive.trim.<jobid>.<idx>` keys met 6 verschillende job-ids: `46716f96, 59a424ac, 6378cdeb, ac7373ae, e63f06a6` plus de active

Deze trim-state staat los van wie de eigenaar is. Het zou kunnen dat de UI deze als "library entries" toont zelfs als de bijbehorende job-ids van een ander account zijn (en dus 404 retourneren bij echte click-through).

### Hypothese B: multi-account residue

Sjuul gebruikt 2 accounts op dezelfde Mac (testing + productie). localStorage van account A blijft persistent. Bij login als account B leest UI nog wat van account A. Bij click → backend 404 (correct).

### Hypothese C: stale Bearer-token

Een refresh-token van een ander account in `clipLive.session` localStorage, auto-verlengd. Onwaarschijnlijk maar testbaar.

## Diagnostische acties voor Sjuul

### Direct in browser console (paste line-by-line, geen markdown fence):

(function(){var t = JSON.parse(localStorage.getItem('clipLive.session') || '{}'); console.log('USER ID hint:', String(t.user && t.user.id || '').slice(0,8) + '...'); console.log('EMAIL:', t.user && t.user.email); console.log('EXPIRES:', t.expires_at ? new Date(t.expires_at*1000).toISOString() : 'no exp'); return 'see console';})()

Verwacht: Sjuul's eigen email (sjuul@monohq-labs.com of business@sjuulstudios.com). Als 't iemand anders is → echte cross-account leak.

### Library-test:

fetch('/api/history', {headers: {Authorization: 'Bearer ' + JSON.parse(localStorage.getItem('clipLive.session')).access_token}}).then(r=>r.json()).then(h=>console.log('history count:', h.length, 'first id:', h[0] && h[0].id, 'user_id:', h[0] && h[0].user_id))

Verwacht: alle entries hebben `user_id === Sjuul's id`. Als 't anders is, log de afwijkende.

### Trim-keys op andere user:

(function(){return Object.keys(localStorage).filter(k=>k.startsWith('clipLive.trim.')).map(k=>{var jid=k.split('.')[2]; return {jobId:jid, val_len:(localStorage.getItem(k)||'').length};});})()

Verwacht: alle job-ids moeten van Sjuul zijn. Eentje van een ander account = residue van een test-flow.

## Fix-strategie

Afhankelijk van wat de diagnose oplevert:

### Als Hypothese A bevestigd: localStorage cleanup op login
- Bij login of token-refresh: wis `clipLive.activeJobId`, `clipLive.trim.*` als de job niet meer toegankelijk is
- Hook: in `postLoginBoot()` na auth → fetch `/api/history`, dan voor elke trim-key check of `<jobid>` in history zit, anders verwijder

### Als Hypothese B bevestigd: per-user localStorage namespacing
- localStorage-keys prefixen met user-id-hash: `clipLive.<userhash>.activeJobId` etc.
- Geen migration nodig — nieuwe keys, oude verlopen vanzelf na 30 dagen retention

### Als Hypothese C bevestigd: token-refresh-flow audit
- Check `_refresh_token` flow in `auth.py`
- Check of access_token van vorige user nog gebruikt wordt (mismatch met refresh_token user_id)

## Aanbevolen volgorde

1. Sjuul draait de 3 diagnose-snippets en stuurt screenshots of plakt output hier
2. Op basis daarvan kies ik fix-strategie A, B of C
3. Implementeer + test
4. Document in HANDOVER.md
