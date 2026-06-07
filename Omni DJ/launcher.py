"""
Omni DJ — Desktop launcher

Wordt gebruikt als entry point in de PyInstaller-bundle. Doet drie dingen:

1. Zet de werkdirectory correct (bij gebundelde uitvoer wijst Python naar
   sys._MEIPASS — een tijdelijke map waar PyInstaller alle bestanden uitpakt).
2. Opent automatisch de standaardbrowser zodra Flask gereed is op
   http://127.0.0.1:5555.
3. Roept vervolgens het bestaande "if __name__ == '__main__'"-blok in app.py
   aan via runpy, zonder bestaande code te wijzigen. Dat blok start de
   watch-folder daemon, leest argv, en draait app.run().

Bij ontwikkeling (python launcher.py) gedraagt het zich identiek aan
"python app.py 5555", met als enige verschil dat de browser automatisch
opent.

Belangrijk: dit script wordt NIET geïmporteerd door app.py. Het is
puur een schil eromheen voor de gebundelde desktop-distributie.
"""

import multiprocessing
# SESSIE 37 — freeze_support() moet als ALLEREERSTE aangeroepen worden,
# nog voor enige andere import of code. PyInstaller-child-processen
# (gespawnd door ProcessPoolExecutor in cutter.py) komen hier binnen en
# moeten onmiddellijk onderschept worden — anders voeren ze de rest van
# launcher.py uit en openen ze een nieuw browsertabblad.
multiprocessing.freeze_support()

import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

# --------------------------------------------------------------------------- #
# 1. Werkdirectory bepalen
# --------------------------------------------------------------------------- #
# PyInstaller zet sys.frozen = True en sys._MEIPASS = pad-naar-uitgepakte-map
# wanneer de bundel draait. We chdir daarheen zodat alle relatieve paden in
# app.py (static/, config.json, brand_kit/) gewoon werken.
if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    BUNDLE_DIR = Path(__file__).parent

os.chdir(BUNDLE_DIR)

# --------------------------------------------------------------------------- #
# 2. Gebruikersmap voor logs en job-history
# --------------------------------------------------------------------------- #
# In een gebundelde .app is sys._MEIPASS read-only. We sturen schrijfacties
# (uploads, output, job_history.json) naar een schrijfbare locatie per OS.
# app.py leest deze env-vars op meerdere plekken.
if sys.platform == "darwin":
    USER_DATA_DIR = Path.home() / "Library" / "Application Support" / "Omni DJ"
elif sys.platform == "win32":
    USER_DATA_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "Omni DJ"
else:
    USER_DATA_DIR = Path.home() / ".omni-dj"

USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("OMNI_DJ_USER_DATA", str(USER_DATA_DIR))

# --------------------------------------------------------------------------- #
# 2b. Hardcoded publieke config laden (Supabase URL, anon key, Stripe
#     publishable, price IDs). Wordt door dotenv overruled als die toch
#     een .env naast app.py vindt — dev-flow blijft dus werken.
# --------------------------------------------------------------------------- #
try:
    import runtime_config

    runtime_config.apply_defaults()
except Exception as e:
    # Niet fataal — als de bundle stuk is en config ontbreekt, krijgt de
    # gebruiker dezelfde "niet geconfigureerd" waarschuwingen die je in
    # dev krijgt zonder .env.
    print(f"runtime_config load failed: {e}", file=sys.stderr)

# --------------------------------------------------------------------------- #
# 3. Logging — naar bestand zodat we GUI-builds kunnen debuggen
# --------------------------------------------------------------------------- #
# Bij console=False (productie .app) zijn print()-calls onzichtbaar voor de
# eindgebruiker. We schrijven launcher-events naar een logfile in de
# gebruikers-data-map zodat we achteraf kunnen zien waarom de browser bv.
# niet opent.
LOG_FILE = USER_DATA_DIR / "launcher.log"


def _log(msg: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass
    # Ook naar stdout als die er is (development of console-build).
    try:
        print(line, end="", flush=True)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# 4. Poort + browser-opener
# --------------------------------------------------------------------------- #
PORT = int(os.environ.get("OMNI_DJ_PORT", "5555"))


def _open_url_native(url: str) -> bool:
    """Open een URL via het OS-eigen commando. Veel betrouwbaarder in
    gebundelde .app dan Python's webbrowser-module (die in een bundle
    soms geen geldige default browser kan vinden)."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", url], check=False)
            return True
        if sys.platform == "win32":
            os.startfile(url)  # type: ignore[attr-defined]
            return True
        subprocess.run(["xdg-open", url], check=False)
        return True
    except Exception as e:
        _log(f"native browser open failed: {e}")
        return False


def _open_browser_when_ready() -> None:
    """Wacht tot Flask de poort open heeft, open dan de browser."""
    import socket

    _log(f"waiting for Flask on 127.0.0.1:{PORT}")
    for attempt in range(120):  # max ~60 s
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
                _log(f"Flask reachable after {attempt} attempts")
                break
        except OSError:
            time.sleep(0.5)
    else:
        _log("Flask never became reachable — giving up on auto-open")
        return

    url = f"http://127.0.0.1:{PORT}"
    if _open_url_native(url):
        _log(f"opened browser via native command: {url}")
        return
    if webbrowser.open(url):
        _log(f"opened browser via webbrowser module: {url}")
        return
    _log(f"could not open any browser — user must visit {url} manually")


# --------------------------------------------------------------------------- #
# 5. Trigger het bestaande main-block in app.py
# --------------------------------------------------------------------------- #
# We doen eerst "import app" zodat PyInstaller bij dependency-scanning alle
# imports van app.py meeneemt. Daarna roepen we het script opnieuw aan via
# runpy met __name__='__main__' — dat triggert het bestaande entry-point
# (watch-folder daemon, _purge_old_uploads, app.run) zonder dat we ook maar
# één regel in app.py hoeven te veranderen.

if __name__ == "__main__":
    _log(f"launcher starting — bundle_dir={BUNDLE_DIR}, port={PORT}, frozen={getattr(sys, 'frozen', False)}")

    # SESSIE 78 - B1b: als Electron de backend als sidecar start, laadt Electron
    # de UI zelf in zijn venster. Dan GEEN browser openen (OMNI_DJ_NO_BROWSER=1).
    # Standalone .app zet die env niet en opent de browser zoals altijd.
    if os.environ.get("OMNI_DJ_NO_BROWSER") not in ("1", "true", "True", "yes"):
        threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    else:
        _log("OMNI_DJ_NO_BROWSER set -> skip browser auto-open (Electron sidecar)")

    # Forceer dependency-scan door PyInstaller — niet werkelijk gebruikt.
    import app as _app  # noqa: F401

    import runpy

    sys.argv = ["app.py", str(PORT)]
    try:
        runpy.run_path(str(BUNDLE_DIR / "app.py"), run_name="__main__")
    except Exception as e:
        _log(f"app.py crashed: {e!r}")
        raise
