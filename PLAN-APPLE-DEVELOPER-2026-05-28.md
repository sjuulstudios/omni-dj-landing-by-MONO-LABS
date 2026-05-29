# Apple Developer + Codesign + Notarize Plan

> **Sessie 60 (2026-05-28). Onderdeel van `PLAN-BETA-LAUNCH-2026-05-28.md` Track B.**
>
> Doel: een signed + notarized Omni DJ DMG die beta-testers kunnen openen zonder Gatekeeper-waarschuwing.
>
> Verwachte tijd: 1u admin actief + 24 tot 48u Apple review-wachttijd + 1-2u technische implementatie.
>
> **Kritieke noot.** Start dag 1 met de admin (Stappen 1-3) omdat de wachttijd niet beïnvloedbaar is. De technische stappen (5-7) doe je pas als de certificaten beschikbaar zijn.

---

## 0. Wat is signing en notarization, in 30 seconden

- **Codesign.** Je bundle krijgt een digitale handtekening met je Developer ID. macOS kan zien dat hij van jou komt en niet onderweg gemodificeerd is.
- **Notarize.** Je stuurt de signed bundle naar Apple. Apple scant op malware en geeft een "ticket" terug. Dat ticket "staple" je op de DMG.
- **Resultaat.** Gebruikers krijgen geen "unidentified developer"-popup meer. Ze openen je app zoals elke App Store-app.
- **Zonder.** Gebruikers moeten elke installatie rechts-klik-Open doen + bevestigen via System Settings → Privacy & Security. Te veel friction voor beta.

---

## 1. Account beslissingen vooraf

Twee keuzes om vooraf te maken:

### 1a. Individual versus Organization

- **Individual** ($99/jaar). Snelste registratie, koppelt aan jouw Apple ID. Apps tonen "Sjuul Smits" als developer-naam.
- **Organization** ($99/jaar). Vereist D-U-N-S-nummer (gratis aan te vragen via Apple's portal, duurt 1-5 werkdagen). Apps tonen "MONO LABS" als developer-naam.

**Aanbeveling voor beta.** Begin als Individual (snel live), wissel later naar Organization als MONO LABS-rebrand definitief is. Of nu direct Organization als je bereid bent 5 werkdagen extra te wachten op D-U-N-S.

### 1b. Apple ID

- Gebruik bij voorkeur `omnidj@monohq-labs.com` voor consistentie met je brand-emails.
- Maak desnoods nieuwe Apple ID op die email aan voordat je Developer registreert.
- Alternatief: bestaande persoonlijke Apple ID (sneller, minder clean).

---

## 2. Stap 1 — Apple Developer Program registratie (dag 1, 15-30 min)

1. Ga naar https://developer.apple.com/programs/enroll/
2. Log in met je Apple ID (zie 1b).
3. Kies entiteit (zie 1a).
4. **Als Organization:**
   - Vul bedrijfsnaam in: MONO LABS
   - Vul D-U-N-S-nummer (vraag aan via https://developer.apple.com/enroll/duns-lookup/ als je nog niet hebt; gratis, 1-5 dagen)
   - Bevestig je rol als signing-authority of geef Apple een legal-contact
5. Betaal $99 (creditcard, eenmalig per jaar).
6. Apple stuurt bevestigingsmail.
7. **Wacht op review.**
   - Individual: meestal 24-48u
   - Organization: 1-2 weken (D-U-N-S verificatie + identity-check)

**Tussentijds.** Kun je niks builden, wel landingspagina + DNS + rebrand doen.

---

## 3. Stap 2 — Xcode + Command Line Tools installeren (dag 1, 30 min)

Sla over als je al Xcode hebt.

1. **Xcode** via App Store (ongeveer 8GB download).
2. Open Xcode 1x, accepteer license.
3. Command Line Tools:
   ```
   xcode-select --install
   ```
4. Verifieer:
   ```
   xcodebuild -version
   xcrun notarytool --version
   xcrun stapler --version
   ```
   Alle drie moeten output geven zonder error.

---

## 4. Stap 3 — Developer ID certificaten genereren (na review, 15 min)

**Voorwaarde.** Apple bevestigde je enrollment per email.

1. Open Xcode → Settings → Accounts.
2. Klik **+** → Add Apple ID → log in met je Developer Apple ID.
3. Selecteer je team (Individual of MONO LABS).
4. Klik **Manage Certificates**.
5. Klik **+** linksonder → **Developer ID Application**.
   - Dit is het certificaat dat je `.app` ondertekent.
6. (Optioneel) Klik **+** → **Developer ID Installer** voor `.pkg`-installers. Voor DMG niet nodig.
7. Klik **Done**.

Xcode genereert het certificaat en plaatst het automatisch in Keychain Access.

**Verifieer in terminal:**
```
security find-identity -p codesigning -v
```
Output moet bevatten:
```
1) <hash> "Developer ID Application: <Naam> (<TeamID>)"
```

Noteer je **Team ID** (de 10-tekens code tussen haakjes). Heb je later nodig.

---

## 5. Stap 4 — App-specific password voor notarytool (10 min)

`notarytool` heeft een App-specific password nodig (geen normaal Apple ID wachtwoord).

1. Ga naar https://appleid.apple.com → Sign in.
2. Onder **Security → App-Specific Passwords** → **Generate**.
3. Label: `notarytool-omnidj`.
4. Apple toont een password zoals `abcd-efgh-ijkl-mnop`. **Noteer dit, je kunt 'm niet later terugzien.**
5. Sla op in Keychain via terminal voor secure use:
   ```
   xcrun notarytool store-credentials "omnidj-notary" \
     --apple-id "omnidj@monohq-labs.com" \
     --team-id "<jouw-team-id>" \
     --password "abcd-efgh-ijkl-mnop"
   ```
6. Verifieer:
   ```
   xcrun notarytool history --keychain-profile "omnidj-notary"
   ```
   Moet leeg list teruggeven zonder error.

---

## 6. Stap 5 — `entitlements.plist` aanpassen (15 min)

Notarize-checks vereisen specifieke entitlements voor PyInstaller-apps. De bestaande `entitlements.plist` in je repo (sessie context) heeft mogelijk al iets, maar check + update voor Omni DJ.

**Locatie.** `Omni DJ/dj-clip-cutter/entitlements.plist` (of de gerebrandedde locatie na sessie 60b).

**Verplichte entitlements voor een Python/Flask + ffmpeg + librosa app:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.cs.disable-executable-page-protection</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.network.server</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.files.downloads.read-write</key>
    <true/>
</dict>
</plist>
```

**Toelichting per entitlement.**

| Entitlement | Reden |
|---|---|
| `allow-jit` | Python en numpy genereren runtime code |
| `allow-unsigned-executable-memory` | PyInstaller-runtime |
| `disable-library-validation` | librosa en ffmpeg laden dylibs die niet signed zijn |
| `disable-executable-page-protection` | Sommige numpy operaties |
| `network.client` | HTTP requests naar Supabase, Stripe |
| `network.server` | Flask lokale server op 5555 |
| `files.user-selected.read-write` | DJ-sets uit Finder kiezen |
| `files.downloads.read-write` | Clips naar Downloads schrijven |

---

## 7. Stap 6 — `build_macos.sh` uitbreiden voor codesign + notarize (30-45 min)

Vervang of vul aan je huidige `build_macos.sh`. Plaats deze versie naast de originele als `build_macos_signed.sh` (zodat unsigned-build nog werkt voor lokale testing).

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Omni DJ — Signed + Notarized macOS Build
# ============================================================
# Usage:
#   ./build_macos_signed.sh        # builds .app only
#   ./build_macos_signed.sh dmg    # builds .app + DMG
#
# Pre-reqs:
#   - Apple Developer ID Application certificate in Keychain
#   - Notarytool credentials stored as "omnidj-notary"
#   - Set TEAM_ID env var or hardcode below
# ============================================================

APP_NAME="Omni DJ"
BUNDLE_ID="com.monolabs.omnidj"
TEAM_ID="${TEAM_ID:-XXXXXXXXXX}"  # vervang door jouw 10-char Team ID
NOTARY_PROFILE="omnidj-notary"
ENTITLEMENTS="entitlements.plist"
SPEC_FILE="OmniDJ.spec"
VERSION="${VERSION:-1.0.0}"

# 1. Activeer venv
source venv/bin/activate

# 2. Clean
rm -rf build dist

# 3. PyInstaller build
echo "==> PyInstaller build..."
pyinstaller "$SPEC_FILE" --clean --noconfirm

APP_PATH="dist/$APP_NAME.app"

if [[ ! -d "$APP_PATH" ]]; then
    echo "ERROR: $APP_PATH niet gevonden na PyInstaller"
    exit 1
fi

# 4. Codesign deep
echo "==> Codesigning..."
SIGN_ID="Developer ID Application: ${SIGN_NAME:-MONO LABS} ($TEAM_ID)"

# Sign embedded frameworks/dylibs eerst
find "$APP_PATH" -name "*.dylib" -o -name "*.so" | while read f; do
    codesign --force --options runtime --timestamp \
        --entitlements "$ENTITLEMENTS" \
        --sign "$SIGN_ID" "$f"
done

# Sign main app last
codesign --force --options runtime --timestamp \
    --entitlements "$ENTITLEMENTS" \
    --sign "$SIGN_ID" "$APP_PATH"

# Verifieer
echo "==> Verify signing..."
codesign --verify --deep --strict --verbose=2 "$APP_PATH"
spctl -a -t exec -vv "$APP_PATH" || echo "(spctl pre-notarize fail is expected)"

# 5. Notarize
echo "==> Notarizing..."
ZIP_PATH="dist/$APP_NAME-notarize.zip"
ditto -c -k --keepParent "$APP_PATH" "$ZIP_PATH"

xcrun notarytool submit "$ZIP_PATH" \
    --keychain-profile "$NOTARY_PROFILE" \
    --wait

rm "$ZIP_PATH"

# 6. Staple ticket op .app
echo "==> Stapling .app..."
xcrun stapler staple "$APP_PATH"
xcrun stapler validate "$APP_PATH"

# 7. DMG (optioneel)
if [[ "${1:-}" == "dmg" ]]; then
    echo "==> Creating DMG..."
    DMG_PATH="dist/$APP_NAME-$VERSION.dmg"

    # Verwijder oude
    rm -f "$DMG_PATH"

    hdiutil create -volname "$APP_NAME" \
        -srcfolder "$APP_PATH" \
        -ov -format UDZO \
        "$DMG_PATH"

    # Sign DMG
    codesign --force --sign "$SIGN_ID" --timestamp "$DMG_PATH"

    # Notarize DMG
    echo "==> Notarizing DMG..."
    xcrun notarytool submit "$DMG_PATH" \
        --keychain-profile "$NOTARY_PROFILE" \
        --wait

    # Staple DMG
    xcrun stapler staple "$DMG_PATH"
    xcrun stapler validate "$DMG_PATH"

    # Final verify
    spctl -a -t open --context context:primary-signature -vv "$DMG_PATH"

    echo ""
    echo "==> Done: $DMG_PATH"
    ls -lh "$DMG_PATH"
else
    echo ""
    echo "==> Done: $APP_PATH"
fi
```

**Belangrijk.** Vervang in script:
- `TEAM_ID` met jouw echte 10-char Team ID
- `SIGN_NAME` met "MONO LABS" of "Sjuul Smits" afhankelijk van Individual/Organization

Maak executable:
```
chmod +x build_macos_signed.sh
```

---

## 8. Stap 7 — Eerste signed build draaien (1-2u inclusief Apple-wachttijd)

1. **Eerste keer:** test eerst zonder DMG:
   ```
   cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
   ./build_macos_signed.sh
   ```
2. **Watch output.** Codesigning duurt 1-5 min. Notarize-submit 5-30 min (Apple servers).
3. **Als notarize faalt:** check log:
   ```
   xcrun notarytool log <submission-id> --keychain-profile omnidj-notary
   ```
   Meest voorkomende fails:
   - Niet alle dylibs gesigned (script doet dit, controleer)
   - Verkeerde entitlements (zie Stap 6)
   - Apple ID niet membership-actief
4. **Als success:** build met DMG:
   ```
   ./build_macos_signed.sh dmg
   ```
5. **Test gatekeeper-acceptance:**
   ```
   spctl -a -t open --context context:primary-signature -vv "dist/Omni DJ-1.0.0.dmg"
   ```
   Output moet eindigen op:
   ```
   source=Notarized Developer ID
   origin=Developer ID Application: MONO LABS (XXXXXXXXXX)
   ```

---

## 9. Stap 8 — Upload DMG naar Cloudflare R2 (zie DNS-plan)

Volg `PLAN-DNS-TRANSIP-CLOUDFLARE-2026-05-28.md` Stap 7. Resultaat: `https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg`.

---

## 10. Verificatie + smoke-test

Voordat je naar beta-testers stuurt:

1. **Op een tweede Mac** (vriend, of via een freshly-created macOS user-account):
   - Download de DMG van `https://downloads.omnidj.com/...`
   - Open. Moet `Omni DJ.app` icoon tonen + Applications-shortcut.
   - Drag naar Applications.
   - Open app. **Mag geen Gatekeeper-popup zijn.** Hooguit "Omni DJ is an app downloaded from internet. Are you sure you want to open it?" (eenmalig OK).
   - App start, browser opent localhost:5555.
   - Login werkt.

2. **Als er wel een Gatekeeper-popup is** met "unidentified developer":
   - Bundle is niet correct gestapeld.
   - Check `xcrun stapler validate "Omni DJ.app"` → moet OK zijn.
   - Check notarytool log voor errors.

---

## 11. Veel voorkomende fails + fixes

| Fout | Oorzaak | Fix |
|---|---|---|
| `errSecInternalComponent` bij codesign | Keychain locked of cert niet geinstalleerd | `security unlock-keychain` + cert opnieuw genereren in Xcode |
| Notarize: "The binary uses an SDK older than the 10.9 SDK" | Oude PyInstaller of Python | Update naar Python 3.11+ + PyInstaller 6+ |
| Notarize: "code object is not signed at all" | dylib zonder signature | Script vergroot scope: ook `.so` files signen (zit erin) |
| Notarize: "The signature does not include a secure timestamp" | `--timestamp` flag mist | Toegevoegd in script (controleer) |
| `spctl: source=Unnotarized Developer ID` | Stapler stap vergeten of fout | `xcrun stapler staple "Omni DJ.app"` opnieuw |
| App crasht direct na openen | Entitlements ontbreken | Voeg entitlement toe + re-build (zie Stap 6) |

---

## 12. Kosten + verlenging

- **Eenmalig.** $99 per jaar Developer Program.
- **Auto-renewal.** Apple verlengt automatisch, zorgt dat je het niet vergeet (anders blokkeert distributie).
- **Notarize-submissions.** Onbeperkt, gratis. Geen rate limit voor normale ontwikkeling.

---

## 13. Open items + later

- **Sparkle.framework** voor in-app auto-updates (na beta, voor v1.x).
- **Universal binary** (Intel + ARM). PyInstaller doet single-arch by default; voor universal moet je beide builden en mergen met `lipo`.
- **App Store-distributie.** Andere flow (App Store Connect, sandboxing, In-App Purchase). Voor beta NIET nodig.

---

## 14. Volgende actie

**Sjuul nu:**
1. Beslis Individual vs Organization (Stap 1a).
2. Apple Developer enrollment indienen (Stap 2).
3. Begin parallel met DNS-plan + landingspagina.
4. Zodra enrollment bevestigd: Stap 3-7 doorlopen.
5. Test signed DMG op vreemde Mac voor je beta-link deelt.

**Bestand bij Claude open houden:**
- `entitlements.plist` (Stap 6 inhoud)
- `build_macos_signed.sh` (Stap 7 script)

Update `HANDOVER.md` met sessie-status zodra je certificaten hebt.
