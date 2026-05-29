# Omni DJ — Local Installation Guide

A complete walkthrough for getting **dj-clip-cutter** running on your Mac, plus how to view the new `clip-live-redesign.html` mockup.

Tested on macOS 13+ (Apple Silicon and Intel). The app is a Flask server that runs locally at `http://127.0.0.1:5555`.

---

## 1. Prerequisites

You need three things on the system before the app will start: a working `python3`, Homebrew, and `ffmpeg`. The launcher script checks for `python3` and `ffmpeg` and refuses to start without them.

### 1a. Python 3.10 or newer

Check what you already have:

```bash
python3 --version
```

If the command isn't found, or the version is older than 3.10, install a current Python:

- **Recommended:** `brew install python` (after installing Homebrew below)
- **Alternative:** download the official installer from https://www.python.org/downloads/

### 1b. Homebrew

If you don't already have it, install Homebrew. It's the easiest way to get `ffmpeg`:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Verify with `brew --version`.

### 1c. FFmpeg

`ffmpeg` does all the audio/video decoding, slicing, and re-encoding. Install it once:

```bash
brew install ffmpeg
```

Verify with `ffmpeg -version`. You should see version info and a list of compiled codecs.

---

## 2. Locate the project

The project already lives at:

```
/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter
```

Open a Terminal and cd into it (the quotes matter because of the space in "Omni DJ"):

```bash
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"
```

Confirm you're in the right place — you should see `start.sh`, `app.py`, `analyzer.py`, `cutter.py`, `requirements.txt`, and a `static/` folder:

```bash
ls
```

---

## 3. First-time launch

The launcher script handles the venv and dependency install for you. From inside the project folder:

```bash
./start.sh
```

What happens on the **first** run:

1. The script verifies `python3` and `ffmpeg` are available
2. It creates a Python virtual environment in `./venv`
3. It activates the venv and runs `pip install -r requirements.txt`
4. It prints two optional add-on commands (AI detection, YouTube upload)
5. It starts the Flask server on port `5555`

This first run takes a few minutes because it pulls down the dependency tree (Flask, librosa, numpy, scipy, soundfile, ffmpeg-python, requests).

When you see something like `Running on http://127.0.0.1:5555`, open your browser to:

```
http://127.0.0.1:5555
```

That's the live tool.

### Subsequent launches

After the first run, `./start.sh` skips the install step entirely — it just activates the existing venv and starts the server. Cold start should be under 5 seconds.

---

## 4. Optional add-ons

These are not required to use the tool — `requirements.txt` covers the core experience. Add them only if you want the extra capability.

### 4a. AI drop detection (Demucs on PyTorch MPS)

This pulls a large download (~2GB for PyTorch) but unlocks Demucs stem separation, which feeds the drop classifier. On Apple Silicon it runs on the MPS backend so it's very fast.

```bash
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"
source venv/bin/activate
pip install torch demucs
```

### 4b. YouTube upload

If you want to push finished clips straight to YouTube from the app:

```bash
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"
source venv/bin/activate
pip install google-api-python-client google-auth-oauthlib
```

You'll also need to wire up Google OAuth credentials — see `uploader.py` for the expected client-secret location.

---

## 5. View the redesign mockup

The new visual prototype is a single self-contained HTML file at:

```
/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/clip-live-redesign.html
```

Open it in your default browser:

```bash
open "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/clip-live-redesign.html"
```

The sticky top nav scroll-spies through eight scenes plus the GPU plan section. No build step, no dependencies — just the file.

---

## 6. Troubleshooting

**`./start.sh: Permission denied`**
The script lost its executable bit. Fix with:
```bash
chmod +x start.sh
```

**`ERROR: FFmpeg is not installed`**
Run `brew install ffmpeg`, then retry. If `brew` isn't found, install Homebrew first (section 1b).

**`Address already in use` / port 5555 busy**
Something else is on 5555. Find it and kill it:
```bash
lsof -i :5555
kill -9 <PID>
```
Or edit the last line of `start.sh` to use a different port: `python3 app.py 5556`.

**Demucs install errors on Apple Silicon**
PyTorch wheels for Apple Silicon need a recent pip:
```bash
source venv/bin/activate
pip install --upgrade pip
pip install torch demucs
```

**Reset the venv from scratch**
If dependencies get into a weird state, nuke the venv and let `start.sh` rebuild it:
```bash
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"
rm -rf venv
./start.sh
```

**Browser shows "can't connect"**
Make sure the terminal window running `start.sh` is still open and shows the `Running on http://127.0.0.1:5555` line. Closing the terminal stops the server.

---

## 7. Stopping the app

In the terminal window where `start.sh` is running, press **Ctrl+C**. That shuts the Flask server down cleanly.

---

## Quick reference

| What | Command |
|------|---------|
| Install ffmpeg | `brew install ffmpeg` |
| Go to project | `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"` |
| Start the app | `./start.sh` |
| Open in browser | http://127.0.0.1:5555 |
| View the mockup | `open "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/clip-live-redesign.html"` |
| Stop the app | Ctrl+C in the terminal |
| Reset venv | `rm -rf venv && ./start.sh` |
