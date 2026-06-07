#!/usr/bin/env bash
# SESSIE 78 - B2: bouw de Omni DJ desktop (Electron) met de PyInstaller-backend
# als HEADLESS sidecar. Draai dit OP DE MAC (vereist Node + npm + de Python-venv
# met pyinstaller). Dit levert een lokaal te draaien .app + .dmg. Het tekent
# NIET (dat is B3): de mac.identity in package.json staat op null.
#
# Stappen:
#   1. PyInstaller-backend bouwen via de bestaande, beproefde build_macos.sh
#      (zonder sign/dmg -> alleen de onverskende dist/Omni DJ.app).
#   2. Die .app stagen in electron/resources/backend/ (electron-builder bundelt
#      'm als extraResource "backend"; main.js draait 'm headless).
#   3. icon klaarzetten in electron/build/.
#   4. electron-builder draaien -> electron/dist-electron/.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"          # .../Omni DJ/Omni DJ/electron
APP_DIR="$(cd "$HERE/.." && pwd)"              # .../Omni DJ/Omni DJ

echo "==> 1/4 PyInstaller-backend bouwen (build_macos.sh, geen sign/dmg)"
( cd "$APP_DIR" && ./build_macos.sh )

BACKEND_APP="$APP_DIR/dist/Omni DJ.app"
if [[ ! -d "$BACKEND_APP" ]]; then
  echo "FOUT: $BACKEND_APP niet gevonden. Check de PyInstaller-output."
  exit 1
fi

echo "==> 2/4 Backend stagen in electron/resources/backend/"
rm -rf "$HERE/resources/backend"
mkdir -p "$HERE/resources/backend"
/usr/bin/ditto "$BACKEND_APP" "$HERE/resources/backend/Omni DJ.app"

echo "==> 3/4 Build-resources (icon) klaarzetten"
mkdir -p "$HERE/build"
if [[ -f "$APP_DIR/static/icon.icns" ]]; then
  cp -f "$APP_DIR/static/icon.icns" "$HERE/build/icon.icns"
else
  echo "    (geen static/icon.icns - electron-builder gebruikt het default-icoon)"
fi

echo "==> 4/4 electron-builder draaien (npm install + dist:mac)"
( cd "$HERE" && npm install && npm run dist:mac )

echo ""
echo "KLAAR. Output staat in: $HERE/dist-electron/"
echo "Smoke-test: open de .app, controleer dat login/analyse/export werken en"
echo "dat na afsluiten geen 'Omni DJ'-backendproces blijft draaien (ps aux | grep -i 'omni dj')."
