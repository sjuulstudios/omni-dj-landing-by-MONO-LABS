# Native File Picker — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the "file too large, please type the path manually" browser-limit dialog with a proper native file picker, so loading any DJ set (including >4 GB) is a single click — no path typing required.

**Architecture:** The backend already has `/api/pick-folder` (native AppleScript / tkinter). We add a sibling `/api/pick-file` endpoint that opens a native *file* picker and returns the absolute path. The frontend's `openFilePicker()` is then replaced by a flow that calls `/api/pick-file`, gets the absolute path back, and sends it straight to `/api/upload-local` — bypassing the browser `<input type="file">` and the 4 GB limit entirely.

**Tech Stack:** Python 3 · Flask · AppleScript (macOS) · tkinter (Windows/Linux) · vanilla JS (frontend)

---

## Why two problems, one plan

| Problem | Root cause | Fix |
|---|---|---|
| 4 GB browser-upload dialog | `uploadFile()` checks `file.size > 4 GB` and opens a manual path-entry modal | Replace browser picker with native picker that returns the absolute path |
| `/api/upload-local` unreachable via normal UI | Tile is hidden; auto-route only triggers for >4 GB files via the typing modal | Native picker always returns a path → always use `/api/upload-local` |

After this fix: *every* set load (small or large) goes through `/api/upload-local` via a single click. The browser `<input type="file">` and the 4 GB check become dead code and can be removed later.

---

## Files to change

| File | Change |
|---|---|
| `dj-clip-cutter/app.py` | Add `/api/pick-file` endpoint (new, ~40 lines) — sibling to existing `/api/pick-folder` |
| `dj-clip-cutter/static/index.html` | Replace `openFilePicker()` body with native-picker flow; update `uploadFile()` to use the path route; remove the >4 GB auto-route branch |

No new files. No changes to `analyzer.py`, `cutter.py`, `requirements.txt`, or any other file.

---

## Task 1 — Add `/api/pick-file` to app.py

**Files:**
- Modify: `dj-clip-cutter/app.py` — add after the `api_pick_folder` function (around line 5753)

### What it does
Opens a native file picker dialog (AppleScript `choose file` on macOS, `tkinter.filedialog.askopenfilename` on Windows/Linux). Returns `{ ok, cancelled, path, platform }` — same shape as `/api/pick-folder`.

### Step-by-step

- [ ] **Stap 1: Lees de huidige `_pick_folder_macos` en `api_pick_folder` functies** (regels ~5635–5753 in app.py) zodat je de bestaande patronen kent.

- [ ] **Stap 2: Voeg `_pick_file_macos` toe** — direct boven `api_pick_folder` (voor de definitie op ~regel 5712):

```python
def _pick_file_macos(prompt, default_dir=None):
    """Open a native file-picker on macOS via AppleScript.
    Returns (absolute_path_or_None, error_or_None)."""
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
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=300
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, f'osascript failed: {e}'
    if result.returncode != 0:
        return None, (result.stderr or 'osascript returned non-zero').strip()
    path = (result.stdout or '').strip()
    return (path or None), None


def _pick_file_tk(prompt, default_dir=None):
    """Windows / Linux fallback for native file picker."""
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
```

- [ ] **Stap 3: Voeg het Flask endpoint `/api/pick-file` toe** — direct na de `api_pick_folder` functie (~regel 5753):

```python
@app.route('/api/pick-file', methods=['POST'])
def api_pick_file():
    """Open a native file-picker dialog. Returns the absolute path of the
    chosen file, or null when the user cancels.
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
```

- [ ] **Stap 4: Test het endpoint handmatig** — start de server (`./start.sh`) en stuur een curl request:

```bash
curl -s -X POST http://127.0.0.1:5555/api/pick-file \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Kies een testbestand"}'
```

Verwacht: een native bestandspicker opent in macOS. Kies een bestand → response is `{"ok": true, "cancelled": false, "path": "/Users/...", "platform": "darwin"}`. Klik Cancel → `{"ok": true, "cancelled": true, "path": null, "platform": "darwin"}`.

- [ ] **Stap 5: Commit**

```bash
cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
git add app.py
git commit -m "feat: add /api/pick-file native file picker endpoint (macOS + Windows/Linux)"
```

---

## Task 2 — Vervang `openFilePicker()` in de frontend

**Files:**
- Modify: `dj-clip-cutter/static/index.html` — functie `openFilePicker` (~regel 5138) en `uploadFile` (~regel 5324)

### Wat er nu gebeurt
1. Gebruiker klikt "Drop a set" of dropzone
2. `openFilePicker()` wordt aangeroepen → klikt op een verborgen `<input type="file">`
3. Browser file picker opent → browser geeft een `File` object terug (geen pad)
4. `uploadFile(file)` checkt: groter dan 4 GB? → open de "type je pad hier" modal
5. Kleiner dan 4 GB → upload via `/api/upload` (kopie over HTTP)

### Wat het moet worden
1. Gebruiker klikt "Drop a set" of dropzone
2. `openFilePicker()` roept `/api/pick-file` aan → native macOS/Windows dialog opent
3. Gebruiker kiest een bestand → server geeft het absolute pad terug
4. Frontend roept `/api/upload-local` aan met dat pad → server analyseert in-place, geen kopie, geen limiet

### Step-by-step

- [ ] **Stap 1: Vervang de body van `openFilePicker()`** (zoek naar `function openFilePicker()` op ~regel 5138):

Vervang dit:
```javascript
function openFilePicker() {
  setTimeout(() => {
    const fi = document.getElementById('global-file-input');
    if (fi) fi.click();
  }, 120);
}
```

Door dit:
```javascript
async function openFilePicker() {
  // Native file picker via Flask backend — geeft absoluut pad terug,
  // geen browser-limiet, werkt voor elke bestandsgrootte.
  let pick;
  try {
    pick = await api('/api/pick-file', {
      method: 'POST',
      body: { prompt: 'Kies een DJ set om te analyseren' },
    });
  } catch (e) {
    // Fallback naar browser picker als het endpoint faalt
    // (bijv. dev-omgeving zonder Flask server).
    console.warn('Native picker niet beschikbaar, val terug op browser picker:', e);
    setTimeout(() => {
      const fi = document.getElementById('global-file-input');
      if (fi) fi.click();
    }, 120);
    return;
  }
  if (!pick || pick.cancelled || !pick.path) return; // gebruiker heeft geannuleerd
  await _startLocalJob(pick.path);
}
```

- [ ] **Stap 2: Voeg de helper `_startLocalJob(path)` toe** — direct ná de nieuwe `openFilePicker` functie:

```javascript
// Helper: registreer een lokaal bestandspad als job via /api/upload-local.
// Gedeeld door de native picker flow en de handmatige pad-modal (submitLocalPath).
async function _startLocalJob(filePath) {
  if (!filePath) return;
  try {
    toast('Bestand registreren…');
    const res = await api('/api/upload-local', {
      method: 'POST',
      body: { path: filePath },
    });
    const jobId = res && (res.job_id || res.id || res.jobId);
    if (jobId) {
      setActiveJobId(jobId);
      switchView('processing');
    } else {
      console.warn('upload-local response mist job id:', res);
      toast('Bestand geregistreerd maar geen job id ontvangen', 'bad');
    }
  } catch (err) {
    console.error(err);
    if (err && err.code === 'quota_exceeded') return;
    toast('Bestand laden mislukt: ' + (err.message || ''), 'bad');
  }
}
```

- [ ] **Stap 3: Update `submitLocalPath()`** zodat die ook `_startLocalJob` gebruikt (zoek de regel `await api('/api/upload-local'` in `submitLocalPath` en vervang die aanroep door):

Zoek in `submitLocalPath` de huidige upload-local aanroep (rond regel 5300–5320). Die ziet er ongeveer zo uit:
```javascript
  const res = await api('/api/upload-local', { method:'POST', body: params });
  const jobId = res && (res.job_id || res.id || res.jobId);
  if (jobId) { closeLocalPathPicker(); setActiveJobId(jobId); switchView('processing'); }
```

Vervang die sectie door:
```javascript
  closeLocalPathPicker();
  await _startLocalJob(path);
```

Zodat er geen dubbele logica is. (De params zoals `clip_duration` e.d. worden al door `_startLocalJob` → `/api/upload-local` via de body meegegeven; als `submitLocalPath` extra params meestuurde, voeg die dan toe aan `_startLocalJob`'s body).

> **Let op:** als `submitLocalPath` extra settings meestuurt (clip_duration, sensitivity etc.), pas dan `_startLocalJob` aan zodat die een optioneel `extraParams` argument accepteert:
> ```javascript
> async function _startLocalJob(filePath, extraParams = {}) {
>   ...
>   body: { path: filePath, ...extraParams },
>   ...
> }
> ```

- [ ] **Stap 4: Verwijder de 4 GB check uit `uploadFile()`** — de browser file input is nu alleen nog een fallback. Verwijder het blok:

```javascript
  if (file && Number(file.size) > LARGE_FILE_THRESHOLD_BYTES) {
    openLocalPathPicker({
      reason: 'large_file_auto_route',
      fileName: file.name,
      fileSize: file.size,
    });
    return;
  }
```

En verwijder de `const LARGE_FILE_THRESHOLD_BYTES = 4 * 1024 * 1024 * 1024;` constante op ~regel 5322 (niet meer nodig).

- [ ] **Stap 5: Test in de draaiende app**

Start de server:
```bash
cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
./start.sh
```

Open http://127.0.0.1:5555 in de browser. Klik "Drop a set" of de dropzone. Verwacht: een native macOS bestandspicker opent direct. Kies een kleine testset (bijv. één van de Don Diablo of Lisa Korver bestanden in CLIP DROP DJ-SETS). Verwacht: de app gaat direct naar de processing view, zonder enige upload-progress bar.

Klik Cancel in de native picker. Verwacht: niets gebeurt, de app blijft op de huidige view.

- [ ] **Stap 6: Test met een grote set (Franky Rizardo 7.8 GB)**

Klik "Drop a set". Kies `Franky Rizardo Peru Set.mp4`. Verwacht: de app gaat direct naar processing, géén "4 GB limit" dialog.

- [ ] **Stap 7: Commit**

```bash
cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
git add static/index.html
git commit -m "feat: replace browser file picker with native /api/pick-file flow — no 4GB limit"
```

---

## Task 3 — Rebuild de .app (optioneel, na testen)

De dev server (`./start.sh`) pikt de wijzigingen automatisch op na een herstart. De `.app` build heeft een aparte stap nodig.

- [ ] **Stap 1: Rebuild**

```bash
cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
python3 build.py
```

Of via het build-script dat in de vorige sessie werd gebruikt.

- [ ] **Stap 2: Verifieer dat de native picker ook in de .app werkt** — open `dist/Clip Live.app`, klik "Drop a set", controleer of de native picker opent.

---

## Wat dit oplost

| Scenario | Vóór | Na |
|---|---|---|
| Kleine set (< 4 GB) laden | Browser picker → HTTP upload (kopie) | Native picker → upload-local (in-place, geen kopie) |
| Grote set (> 4 GB) laden | Browser picker → "4 GB limit" dialog → handmatig pad typen | Native picker → upload-local (in-place, één klik) |
| Smoketest door Claude | Kan bestanden niet uploaden via Chrome extensie | Claude roept `/api/pick-file` aan via JS → native picker opent op Sjuul's scherm |
| Franky Rizardo 7.8 GB set | Geblokkeerd door browser limiet | Gewoon werkt |

---

## Risico's / aandachtspunten

- **macOS Gatekeeper:** `osascript` werkt in de dev server (`./start.sh`) altijd. In de `.app` build werkt het ook, maar als de app in de toekomst sandboxed wordt (App Store), moeten we over naar `NSOpenPanel` via Objective-C/Swift bridge.
- **Fallback:** Als `/api/pick-file` faalt (bijv. oudere build), valt `openFilePicker()` terug op de browser file input. De gebruiker merkt dan het oude gedrag.
- **`submitLocalPath()` blijft werken:** De handmatige pad-modal blijft beschikbaar (voor power users die een pad willen intypen of plakken). Die wordt nu ook gevoed door `_startLocalJob`.
