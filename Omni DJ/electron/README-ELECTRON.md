# Omni DJ desktop - Electron prototype (B0)

Dit is het Spoor B / B0 prototype: Electron wrapt de bestaande Flask-backend als
sidecar en laadt de bestaande web-UI in een eigen venster. De analyse blijft
100% lokaal. Dit is bewust nog GEEN packaging of signing (dat is B2/B3); het doel
is bewijzen dat UI plus analyse plus export werken in een Electron-venster.

## Wat het doet
- Kiest een vrije poort.
- Start de dev-backend: venv python app.py op die poort, met OMNI_DJ_PORT gezet
  (de Host-gate eist dat voor andere poorten dan 5555) en met vendor/ffmpeg op PATH.
- Doet een health-check op / tot Flask antwoordt, met een splash zolang dat duurt.
- Laadt daarna de UI op http://127.0.0.1:<poort>/.
- Sluit de backend af bij het afsluiten van de app.

## Vereisten
- De bestaande Python-venv moet bestaan op ../venv (dezelfde die start.sh gebruikt).
- Node en npm op de Mac.

## Draaien (vanuit deze electron-map)
Stap 1, ga naar de map:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/electron"

Stap 2, installeer Electron (eenmalig, lokaal in deze map):

npm install

Stap 3, start het venster:

npm start

Als de venv ergens anders staat, kun je het pad overschrijven, bijvoorbeeld:

OMNI_DJ_PYTHON="/pad/naar/venv/bin/python3" npm start

## Wat te verwachten / smoke-test
- Een venster met de Omni DJ-splash, daarna de gewone UI (oranje V2).
- Login werkt, een set analyseren werkt, een clip exporteren werkt: dezelfde flow
  als in de browser, maar nu in een eigen venster.
- Sluit het venster: het python-proces stopt mee (in de terminal zie je "backend exited").

## B1 (lifecycle) - nu erin
- Robuuste process-tree-kill: detached spawn + groep-kill (SIGTERM, daarna
  SIGKILL) zodat er geen zombie-python of achtergebleven ffmpeg blijft draaien.
- macOS application-menu met de standaard Cmd-shortcuts (Quit, Cut/Copy/Paste,
  Reload, DevTools, zoom, fullscreen, window).
- Nette shutdown op SIGINT/SIGTERM (bv. Ctrl-C in de terminal).
- Veilige link-afhandeling: externe http(s)-links openen in de standaardbrowser;
  wegnavigeren uit de lokale backend wordt geblokkeerd.
- Venster sluiten = app afsluiten = backend stoppen.

## B1b (PyInstaller-sidecar) - nu erin
main.js kiest de backend automatisch (`resolveBackend()`):
- In een gepackagede build draait het de meegebundelde PyInstaller-backend
  HEADLESS (extraResource `backend`, env `OMNI_DJ_NO_BROWSER=1` zodat launcher.py
  geen browser opent; Electron laadt de UI zelf).
- In dev (npm start) valt het terug op de venv-python + app.py (B0/B1-gedrag).
- Override met `OMNI_DJ_BACKEND=/pad/naar/Omni DJ.app/Contents/MacOS/Omni DJ`.

## B2 (packaging) - nu erin
electron-builder-config staat in `package.json` (`build`). Bouwen OP DE MAC:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/electron"

./build_electron.sh

Dat doet: (1) de PyInstaller-backend bouwen via de bestaande `build_macos.sh`,
(2) die `.app` stagen in `resources/backend/`, (3) het icoon klaarzetten,
(4) electron-builder draaien. Resultaat: `electron/dist-electron/Omni DJ-*.dmg`.

Smoke-test na de build: open de .app, login/analyse/export werken, en na
afsluiten blijft er GEEN backendproces hangen (`ps aux | grep -i 'omni dj'`).

## Bekende beperkingen (bewust nog open)
- B3 (signing/notarization) staat UIT: `mac.identity` = null -> de build is
  onverskend (lokaal te draaien, niet distribueerbaar zonder Gatekeeper-omweg).
- Finish-notificatie + Dock-progress vereisen renderer->main IPC -> later.
- macOS/Apple Silicon, net als de bestaande tool.

## Volgende fasen (zie het hoofdplan)
- B3: signing/notarization. Zet `mac.identity` op de Developer ID
  ("Developer ID Application: Sjuul Smits (PTLV7AY4UL)"), behoud
  `hardenedRuntime` + `build/entitlements.mac.plist`, en notariseer de DMG
  (zelfde notarytool-profiel `omnidj-notary` als de standalone build). De
  embedded backend is al apart getekend; `disable-library-validation` in de
  entitlements dekt de gemengde handtekeningen.
- B4: Windows (PyInstaller-backend plus NSIS-installer via electron-builder).
- Finish-notificatie + Dock-progress via een smalle contextBridge IPC.
