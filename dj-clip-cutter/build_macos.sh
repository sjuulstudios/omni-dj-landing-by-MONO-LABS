#!/usr/bin/env bash
#
# Clip Live — macOS build script
#
# Bouwt een Clip Live.app + Clip Live.dmg vanuit de huidige source.
# Werkt op de Mac waarop je ontwikkelt. Aanroep:
#
#     ./build_macos.sh                  # alleen .app bouwen (geen signing)
#     ./build_macos.sh sign             # .app bouwen + signen met Developer ID
#     ./build_macos.sh sign notarize    # signen + notarizen (vereist Apple ID)
#     ./build_macos.sh sign notarize dmg  # alles + .dmg verpakken
#
# Vooraf: open Terminal, ga naar de dj-clip-cutter map, en draai:
#   source venv/bin/activate
#   pip install pyinstaller dmgbuild
#
# Voor signing+notarization heb je een Apple Developer account nodig
# ($99/jaar) en moet je een Developer ID Application certificaat in je
# Keychain hebben staan. Zie INSTALLER-RUNBOOK.md voor stap-voor-stap.

set -euo pipefail

cd "$(dirname "$0")"

MODE_SIGN="no"
MODE_NOTARIZE="no"
MODE_DMG="no"
for arg in "$@"; do
    case "$arg" in
        sign)     MODE_SIGN="yes" ;;
        notarize) MODE_NOTARIZE="yes" ;;
        dmg)      MODE_DMG="yes" ;;
        *)        echo "Onbekend argument: $arg"; exit 1 ;;
    esac
done

# --------------------------------------------------------------------------- #
# 0. Sanity checks
# --------------------------------------------------------------------------- #
echo ""
echo "=== Clip Live build ==="
echo ""

if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "FOUT: pyinstaller niet gevonden in PATH."
    echo "Activeer eerst je venv en draai: pip install pyinstaller dmgbuild"
    exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "FOUT: ffmpeg niet geïnstalleerd. Draai eerst: brew install ffmpeg"
    exit 1
fi

# --------------------------------------------------------------------------- #
# 1. Schoonmaken
# --------------------------------------------------------------------------- #
echo "→ Oude build/ en dist/ verwijderen..."
rm -rf build/ "dist/Clip Live" "dist/Clip Live.app" "dist/Clip Live.dmg"

# --------------------------------------------------------------------------- #
# 2. PyInstaller
# --------------------------------------------------------------------------- #
echo "→ PyInstaller draaien (kan 3–8 minuten duren)..."
pyinstaller --noconfirm ClipLive.spec

APP_PATH="dist/Clip Live.app"
if [[ ! -d "$APP_PATH" ]]; then
    echo "FOUT: dist/Clip Live.app is niet gebouwd. Check de PyInstaller-output."
    exit 1
fi

# --------------------------------------------------------------------------- #
# 3. Bundel opschonen — .bak files en backups eruit
# --------------------------------------------------------------------------- #
# Mocht je tijdens development per ongeluk een .bak of .backup in static/
# laten staan, dan zit die anders in de gedistribueerde .app. Hier defensief
# verwijderen — geen invloed op de werking, scheelt soms 50+ MB.
echo "→ .bak / .backup / .orig files uit bundle strippen..."
find "$APP_PATH" \( -name "*.bak" -o -name "*.backup" -o -name "*.orig" \) -delete 2>/dev/null || true

# --------------------------------------------------------------------------- #
# 4. ffmpeg + ffprobe bundlen
# --------------------------------------------------------------------------- #
echo "→ ffmpeg + ffprobe in de bundle kopiëren..."
RESOURCES="$APP_PATH/Contents/Resources"
mkdir -p "$RESOURCES/bin"
cp "$(command -v ffmpeg)"  "$RESOURCES/bin/ffmpeg"
cp "$(command -v ffprobe)" "$RESOURCES/bin/ffprobe"
chmod +x "$RESOURCES/bin/ffmpeg" "$RESOURCES/bin/ffprobe"

# Belangrijk: in app.py / cutter.py wordt ffmpeg via PATH gezocht. Een
# kleine launcher-wrapper zet PATH zodat de gebundelde binaries gevonden
# worden voordat de Python-code start. We doen dat met een runtime hook
# alternatief: env-var in Info.plist. Eenvoudigste pad: een launchscript.
LAUNCH="$APP_PATH/Contents/MacOS/clip-live-launch.sh"
ORIGINAL_BIN="$APP_PATH/Contents/MacOS/Clip Live"
mv "$ORIGINAL_BIN" "$APP_PATH/Contents/MacOS/Clip Live.bin"
cat > "$LAUNCH" <<'EOF'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$DIR/Resources/bin:$PATH"
exec "$DIR/MacOS/Clip Live.bin" "$@"
EOF
chmod +x "$LAUNCH"
# Info.plist verwijst naar CFBundleExecutable=Clip Live; we hernoemen het
# wrapper-script daarheen.
mv "$LAUNCH" "$ORIGINAL_BIN"

# --------------------------------------------------------------------------- #
# 4. Optioneel: signen
# --------------------------------------------------------------------------- #
if [[ "$MODE_SIGN" == "yes" ]]; then
    if [[ -z "${APPLE_DEVELOPER_ID:-}" ]]; then
        echo "FOUT: zet APPLE_DEVELOPER_ID environment variable, bv.:"
        echo "  export APPLE_DEVELOPER_ID=\"Developer ID Application: Sjuul Studios (TEAMID)\""
        exit 1
    fi
    echo "→ Signen met identiteit: $APPLE_DEVELOPER_ID"
    codesign --force --deep --options runtime \
        --entitlements entitlements.plist \
        --sign "$APPLE_DEVELOPER_ID" \
        "$APP_PATH"
    codesign --verify --strict --verbose=2 "$APP_PATH"
fi

# --------------------------------------------------------------------------- #
# 5. Optioneel: notarizen
# --------------------------------------------------------------------------- #
if [[ "$MODE_NOTARIZE" == "yes" ]]; then
    if [[ "$MODE_SIGN" != "yes" ]]; then
        echo "FOUT: notarize vereist sign. Draai opnieuw met: sign notarize"
        exit 1
    fi
    if [[ -z "${APPLE_NOTARY_PROFILE:-}" ]]; then
        echo "FOUT: stel eerst een notary-profiel in (eenmalig):"
        echo "  xcrun notarytool store-credentials cliplive-notary \\"
        echo "    --apple-id business@sjuulstudios.com \\"
        echo "    --team-id  TEAMID \\"
        echo "    --password APP-SPECIFIC-PASSWORD"
        echo "  export APPLE_NOTARY_PROFILE=cliplive-notary"
        exit 1
    fi
    ZIPFILE="dist/Clip Live.zip"
    /usr/bin/ditto -c -k --keepParent "$APP_PATH" "$ZIPFILE"
    echo "→ Notarization submit (kan 1–15 min duren)..."
    xcrun notarytool submit "$ZIPFILE" \
        --keychain-profile "$APPLE_NOTARY_PROFILE" \
        --wait
    xcrun stapler staple "$APP_PATH"
    rm -f "$ZIPFILE"
fi

# --------------------------------------------------------------------------- #
# 6. Optioneel: .dmg bouwen
# --------------------------------------------------------------------------- #
if [[ "$MODE_DMG" == "yes" ]]; then
    if ! command -v dmgbuild >/dev/null 2>&1; then
        echo "FOUT: dmgbuild niet geïnstalleerd. Draai: pip install dmgbuild"
        exit 1
    fi
    echo "→ .dmg bouwen..."
    cat > /tmp/cliplive_dmg_settings.py <<'EOF'
import os
APP = os.path.join(os.getcwd(), "dist", "Clip Live.app")
files = [APP]
symlinks = {"Applications": "/Applications"}
icon_locations = {"Clip Live.app": (140, 120), "Applications": (500, 120)}
window_rect = ((100, 100), (640, 360))
background = None
icon_size = 128
text_size = 16
EOF
    dmgbuild -s /tmp/cliplive_dmg_settings.py "Clip Live" "dist/Clip Live.dmg"
    rm -f /tmp/cliplive_dmg_settings.py
fi

echo ""
echo "=== Klaar ==="
echo "App        : $APP_PATH"
[[ "$MODE_DMG" == "yes" ]] && echo "DMG        : dist/Clip Live.dmg"
echo ""
echo "Test met   : open \"$APP_PATH\""
