#!/usr/bin/env bash
#
# Omni DJ — macOS build script
#
# Bouwt een Omni DJ.app + Omni DJ.dmg vanuit de huidige source.
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
echo "=== Omni DJ build ==="
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
rm -rf build/ "dist/Omni DJ" "dist/Omni DJ.app" "dist/Omni DJ.dmg"

# --------------------------------------------------------------------------- #
# 2. PyInstaller
# --------------------------------------------------------------------------- #
echo "→ PyInstaller draaien (kan 3–8 minuten duren)..."
pyinstaller --noconfirm OmniDJ.spec

APP_PATH="dist/Omni DJ.app"
if [[ ! -d "$APP_PATH" ]]; then
    echo "FOUT: dist/Omni DJ.app is niet gebouwd. Check de PyInstaller-output."
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

# SESSIE 30 - defensieve secret-scan: .env / .env.* / *.pem / *_secret* /
# *_service_role* mogen nooit in de bundle landen. Als pyinstaller of een
# dev per ongeluk zoiets oppakt, faalt de build hier ipv stil te shippen.
echo "→ Secret-scan op de bundle..."
# NB: cacert.pem (Mozilla CA bundle bij certifi) is geen secret; vandaar
# dat we niet op alle *.pem files matchen.
SECRET_HITS=$(find "$APP_PATH" \
    \( -name ".env" -o -name ".env.*" \
       -o -iname "*service_role*" -o -iname "*_secret*" \
       -o -iname "*.private.pem" -o -iname "id_rsa*" \) 2>/dev/null || true)
if [[ -n "$SECRET_HITS" ]]; then
    echo "FOUT: secret-bestanden gevonden in de bundle:"
    echo "$SECRET_HITS"
    echo "Verwijder ze uit de source of pas OmniDJ.spec datas/excludes aan, en bouw opnieuw."
    exit 1
fi

# Daarnaast: grep door alle Python-bytecode files op hard-coded secrets.
# Dit pakt het zeldzame geval waarin iemand een sk_test_ of service_role
# token in een module heeft gezet ipv via env. Voor pyinstaller-bundles
# liggen .pyc bestanden in Contents/Resources/lib/python*/site-packages of
# in Contents/MacOS na archive-extract; we scannen breed maar non-fataal
# (alleen waarschuwen) zodat een legitieme test_data file de build niet
# breekt.
SUSPECT=$(grep -rEl "sk_(test|live)_[A-Za-z0-9]{20,}|whsec_[A-Za-z0-9]{20,}|service_role.{0,5}eyJ[A-Za-z0-9_\-\.]{40,}" \
    "$APP_PATH" 2>/dev/null | head -5 || true)
if [[ -n "$SUSPECT" ]]; then
    echo "WAARSCHUWING: mogelijke hard-coded secrets gedetecteerd in:"
    echo "$SUSPECT"
    echo "Controleer voor je deze .app distribueert."
fi

# --------------------------------------------------------------------------- #
# 4. ffmpeg + ffprobe bundlen
# --------------------------------------------------------------------------- #
echo "→ ffmpeg + ffprobe in de bundle kopiëren..."
RESOURCES="$APP_PATH/Contents/Resources"
mkdir -p "$RESOURCES/bin"

# SESSIE 66 — we gebruiken VENDORED STATIC binaries i.p.v. de Homebrew-ffmpeg.
# Reden: Homebrew-ffmpeg laadt zijn dylibs uit /opt/homebrew/Cellar/... Onder
# de hardened runtime (vereist voor notarization) weigert macOS die dylibs
# (different Team IDs) → ffprobe abort → elke upload faalt in de gesignde .app,
# en faalt sowieso bij testers zonder Homebrew. Static binaries hebben geen
# externe dylibs en werken overal. Leg ze in vendor/ffmpeg/ (zie
# PLAN-FFMPEG-BUNDLE-FIX-2026-05-31.md voor download-bron).
VENDOR_FFMPEG="vendor/ffmpeg/ffmpeg"
VENDOR_FFPROBE="vendor/ffmpeg/ffprobe"

if [[ ! -f "$VENDOR_FFMPEG" || ! -f "$VENDOR_FFPROBE" ]]; then
    echo "FOUT: static ffmpeg/ffprobe niet gevonden in vendor/ffmpeg/."
    echo "Download arm64 static builds (bv. https://ffmpeg.martin-riedl.de/) en"
    echo "plaats ze als vendor/ffmpeg/ffmpeg en vendor/ffmpeg/ffprobe."
    echo "Zie PLAN-FFMPEG-BUNDLE-FIX-2026-05-31.md."
    exit 1
fi

cp "$VENDOR_FFMPEG"  "$RESOURCES/bin/ffmpeg"
cp "$VENDOR_FFPROBE" "$RESOURCES/bin/ffprobe"
chmod +x "$RESOURCES/bin/ffmpeg" "$RESOURCES/bin/ffprobe"

# Vangrail: faal de build als de binaries tóch externe (Homebrew/Cellar)
# dylibs nodig hebben — dat is precies wat notarization later zou breken.
for b in "$RESOURCES/bin/ffmpeg" "$RESOURCES/bin/ffprobe"; do
    if otool -L "$b" 2>/dev/null | grep -qE "/opt/homebrew|/usr/local/Cellar|@rpath"; then
        echo "FOUT: $b heeft externe dylib-afhankelijkheden (geen static build):"
        otool -L "$b" | grep -E "/opt/homebrew|/usr/local/Cellar|@rpath"
        echo "Gebruik een écht static binary. Zie PLAN-FFMPEG-BUNDLE-FIX-2026-05-31.md."
        exit 1
    fi
done
echo "  • static ffmpeg/ffprobe geverifieerd (geen externe dylibs)"

# Belangrijk: in app.py / cutter.py wordt ffmpeg via PATH gezocht. Een
# kleine launcher-wrapper zet PATH zodat de gebundelde binaries gevonden
# worden voordat de Python-code start. We doen dat met een runtime hook
# alternatief: env-var in Info.plist. Eenvoudigste pad: een launchscript.
LAUNCH="$APP_PATH/Contents/MacOS/clip-live-launch.sh"
ORIGINAL_BIN="$APP_PATH/Contents/MacOS/Omni DJ"
mv "$ORIGINAL_BIN" "$APP_PATH/Contents/MacOS/Omni DJ.bin"
cat > "$LAUNCH" <<'EOF'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$DIR/Resources/bin:$PATH"
exec "$DIR/MacOS/Omni DJ.bin" "$@"
EOF
chmod +x "$LAUNCH"
# Info.plist verwijst naar CFBundleExecutable=Omni DJ; we hernoemen het
# wrapper-script daarheen.
mv "$LAUNCH" "$ORIGINAL_BIN"

# --------------------------------------------------------------------------- #
# 4. Optioneel: signen
# --------------------------------------------------------------------------- #
if [[ "$MODE_SIGN" == "yes" ]]; then
    if [[ -z "${APPLE_DEVELOPER_ID:-}" ]]; then
        echo "FOUT: zet APPLE_DEVELOPER_ID environment variable, bv.:"
        echo "  export APPLE_DEVELOPER_ID=\"Developer ID Application: MONO LABS (TEAMID)\""
        exit 1
    fi
    echo "→ Signen met identiteit: $APPLE_DEVELOPER_ID"

    # Apple raadt --deep af voor notarization. We signen daarom van binnen
    # naar buiten: eerst alle ingebedde dylibs/.so's (elk met een secure
    # --timestamp), daarna de gebundelde ffmpeg/ffprobe, en als laatste de
    # .app zelf. Zonder --timestamp weigert notarization ("signature does
    # not include a secure timestamp").
    echo "  • embedded .dylib / .so files signen..."
    find "$APP_PATH" \( -name "*.dylib" -o -name "*.so" \) -print0 \
        | while IFS= read -r -d '' lib; do
            codesign --force --options runtime --timestamp \
                --sign "$APPLE_DEVELOPER_ID" "$lib"
        done

    # Ingebedde frameworks (bv. Python.framework) bevatten een uitvoerbaar
    # binary zónder .dylib/.so-extensie (bv. .../Python.framework/Versions/
    # 3.14/Python). Die werd door de zoekstap hierboven overgeslagen en hield
    # zijn ongeldige, timestamp-loze handtekening — precies wat Apple's
    # notarization afkeurde. We signen elk .framework hier expliciet (het
    # versie-binnenste eerst, dan het framework als geheel).
    echo "  • embedded .framework bundles signen..."
    find "$APP_PATH" -name "*.framework" -type d -print0 \
        | while IFS= read -r -d '' fw; do
            # Sign het binary in elke Versions/<x>/ map (het echte
            # uitvoerbare bestand binnen het framework).
            find "$fw/Versions" -maxdepth 2 -type f -perm -u+x 2>/dev/null \
                | while IFS= read -r fwbin; do
                    codesign --force --options runtime --timestamp \
                        --sign "$APPLE_DEVELOPER_ID" "$fwbin" || true
                done
            # Sign het framework als geheel.
            codesign --force --options runtime --timestamp \
                --sign "$APPLE_DEVELOPER_ID" "$fw"
        done

    echo "  • gebundelde ffmpeg / ffprobe signen..."
    for bin in "$RESOURCES/bin/ffmpeg" "$RESOURCES/bin/ffprobe"; do
        [[ -f "$bin" ]] && codesign --force --options runtime --timestamp \
            --sign "$APPLE_DEVELOPER_ID" "$bin"
    done

    # De launcher-wrapper-stap hierboven hernoemde het echte PyInstaller-
    # binary naar "Omni DJ.bin" en zette er een bash-launcher voor in de
    # plaats. Door dat verplaatsen werd de PyInstaller-signature van .bin
    # ongeldig. We her-signen het hier expliciet (met entitlements, want het
    # is de daadwerkelijke Python-executable die JIT/dyld nodig heeft),
    # vóór we de .app-bundle als geheel signen.
    echo "  • hernoemd PyInstaller-binary (Omni DJ.bin) her-signen..."
    if [[ -f "$APP_PATH/Contents/MacOS/Omni DJ.bin" ]]; then
        codesign --force --options runtime --timestamp \
            --entitlements entitlements.plist \
            --sign "$APPLE_DEVELOPER_ID" \
            "$APP_PATH/Contents/MacOS/Omni DJ.bin"
    fi

    echo "  • hoofd-app signen (met entitlements)..."
    codesign --force --options runtime --timestamp \
        --entitlements entitlements.plist \
        --sign "$APPLE_DEVELOPER_ID" \
        "$APP_PATH"

    echo "  • signing verifiëren..."
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
        echo "  xcrun notarytool store-credentials omnidj-notary \\"
        echo "    --apple-id omnidj@monohq-labs.com \\"
        echo "    --team-id  TEAMID \\"
        echo "    --password APP-SPECIFIC-PASSWORD"
        echo "  export APPLE_NOTARY_PROFILE=omnidj-notary"
        exit 1
    fi
    ZIPFILE="dist/Omni DJ.zip"
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
    cat > /tmp/omnidj_dmg_settings.py <<'EOF'
import os
APP = os.path.join(os.getcwd(), "dist", "Omni DJ.app")
files = [APP]
symlinks = {"Applications": "/Applications"}
icon_locations = {"Omni DJ.app": (140, 120), "Applications": (500, 120)}
window_rect = ((100, 100), (640, 360))
background = None
icon_size = 128
text_size = 16
EOF
    dmgbuild -s /tmp/omnidj_dmg_settings.py "Omni DJ" "dist/Omni DJ.dmg"
    rm -f /tmp/omnidj_dmg_settings.py

    # De app in de DMG is al genotariseerd, maar de DMG-verpakking zelf is
    # nog ongesigned (spctl op de .dmg geeft anders "no usable signature").
    # Als we ook signen+notarizen, dan geeft Gatekeeper geen enkele melding,
    # ook niet bij het openen van de DMG. Alleen zinvol als sign+notarize aan.
    if [[ "$MODE_SIGN" == "yes" && "$MODE_NOTARIZE" == "yes" ]]; then
        DMG_PATH="dist/Omni DJ.dmg"
        echo "→ DMG signen..."
        codesign --force --timestamp \
            --sign "$APPLE_DEVELOPER_ID" "$DMG_PATH"

        echo "→ DMG notarizen (kan 1–15 min duren)..."
        xcrun notarytool submit "$DMG_PATH" \
            --keychain-profile "$APPLE_NOTARY_PROFILE" \
            --wait

        echo "→ DMG staplen..."
        xcrun stapler staple "$DMG_PATH"
        xcrun stapler validate "$DMG_PATH"
    fi
fi

echo ""
echo "=== Klaar ==="
echo "App        : $APP_PATH"
[[ "$MODE_DMG" == "yes" ]] && echo "DMG        : dist/Omni DJ.dmg"
echo ""
echo "Test met   : open \"$APP_PATH\""
