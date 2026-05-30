# PLAN - Native app-venster (pywebview) i.p.v. Chrome-tab

> Datum: 2026-05-30 (sessie 65)
> Doel: Omni DJ opent als eigen venster (zoals Photoshop), niet als tab in Chrome.
> Voor: betalende klanten, macOS + Windows. Aanpak: pywebview (geen gebundelde Chromium).
> Status: PLAN - nog niet uitgevoerd. Wacht op "ja".

---

## Probleem (huidige situatie)

`launcher.py` start Flask, wacht op de poort, en roept dan `subprocess.run(["open", url])`
(`_open_url_native`) of `webbrowser.open(url)` aan. Dat geeft de URL door aan de
default browser (Chrome) -> de UI verschijnt als tab. Daardoor voelt het als een
website, niet als een app.

De hele "open een venster"-beslissing zit in 1 functie:
`launcher.py` -> `_open_browser_when_ready()` -> `_open_url_native()`. Dat is het enige
punt dat we hoeven te vervangen.

---

## Gekozen aanpak: pywebview

pywebview opent een echt OS-venster met de ingebouwde web-engine:
- macOS: WebKit (zit in het systeem, niets te bundelen)
- Windows: WebView2 (Edge-runtime, vrijwel overal aanwezig op Win10/11)

De Flask-server blijft 100% hetzelfde. pywebview wijst alleen een venster naar
`http://127.0.0.1:5555`. Geen URL-balk, geen tabs, eigen icoon in de Dock/taakbalk,
eigen titel. Bundle groeit met enkele MB's, niet honderden.

**Waarom niet de alternatieven:**
- Gebundelde Chromium (Qt/CEF/Electron): identieke rendering overal, maar +100-200 MB
  en veel meer build-complexiteit. Alleen nodig als WebKit/WebView2 iets niet rendert.
- Chrome `--app=`-modus: snel, maar hangt af van Chrome + toont Chrome's icoon, niet
  het jouwe. Afgevallen want jij wilt een echt native venster voor klanten.

---

## De structurele wijziging (belangrijk)

Op macOS MOET de GUI op de hoofd-thread draaien. Nu draait Flask op de hoofd-thread
(`app.run(...)` blokkeert). Dus de rolverdeling draait om:

- NIEUW: Flask draait op een achtergrond-thread.
- NIEUW: pywebview (`webview.start()`) draait op de hoofd-thread en blokkeert daar.
- Als het venster sluit -> proces stopt netjes (incl. Flask-thread).

Dit raakt alleen `launcher.py`. `app.py` blijft ongemoeid (we starten Flask via de
bestaande runpy-aanroep, maar in een thread).

---

## Concrete stappen

### 1. Dependency
- `pip install pywebview` (macOS: trekt `pyobjc` aan; Windows: `pythonnet`/WebView2-loader).
- Toevoegen aan `requirements.txt`.

### 2. launcher.py aanpassen
- Flask-start verplaatsen naar een `threading.Thread(daemon=True)`.
- `_open_browser_when_ready()` vervangen door: wacht op poort -> `webview.create_window(
  "Omni DJ", "http://127.0.0.1:5555", width=1400, height=900, min_size=(1024,700))`
  -> `webview.start()`.
- Fallback behouden: als `import webview` faalt OF het venster niet opent, val terug op
  de oude browser-open. Zo blijft de app altijd bruikbaar (defensief).
- Env-var ontsnapping: `OMNI_DJ_NO_WEBVIEW=1` forceert de oude browser-modus (handig
  voor debuggen / als een klant problemen heeft met WebView2).

### 3. OmniDJ.spec aanpassen
- `hiddenimports += collect_submodules("webview")`.
- macOS: `pyobjc`-submodules die pywebview lazy-importeert expliciet toevoegen indien
  PyInstaller ze mist (blijkt pas bij de testbuild).
- Windows (later): WebView2Loader.dll meebundelen indien nodig.

### 4. Bouwen + testen (jij, op je Mac)
- `./build_macos.sh dmg` -> open `dist/Omni DJ.app`.
- TEST-CHECKLIST in het eigen venster (dit zijn de risico-plekken):
  1. App opent als EIGEN venster, geen Chrome-tab, eigen icoon in Dock.
  2. Inloggen werkt.
  3. Bestand kiezen via de upload-knop (`<input type=file>`) opent een NATIVE
     bestandskiezer en de file komt binnen. (3x checken: audio/video-upload,
     font-upload, logo/watermark-upload in Brand.)
  4. Drag-drop een audiobestand op de dropzone -> wordt opgepakt.
  5. Volledige analyse draait.
  6. Editor + timeline + video-preview (`<video>`) speelt af en scrubt.
  7. Export met captions -> MP4 op schijf.
  8. "Reveal in Finder" (`open -R`) werkt nog vanuit het venster.
- Wat in WebKit breekt -> noteren; meestal op te lossen met een kleine polyfill of
  een pywebview-API-call (bv. native dialog hook). Pas als iets fundamenteel niet kan,
  overwegen we Option B (gebundelde Chromium) voor dat ene onderdeel.

### 5. Windows (aparte ronde, later)
- WebView2-runtime-check bij startup; zo niet aanwezig, gebruiker naar de
  Microsoft-installer sturen (1 klik, gratis). Meestal al aanwezig op Win10/11.
- Eigen `.spec`/build voor Windows. Niet deze sessie.

---

## Risico's / eerlijk

- **WebKit-rendering verschilt licht van Chrome.** Jouw editor is HTML/CSS/JS +
  standaard `<video>`, dus kans op problemen is klein, maar pas na de testbuild zeker.
- **File-input + drag-drop** zijn de meest waarschijnlijke snags. Daarom staan ze
  bovenaan de checklist.
- **macOS code-signing**: een venster-app voelt klanten "echter", wat de noodzaak van
  een Apple Developer-signature (geen "unidentified developer"-waarschuwing) groter
  maakt. Los van dit plan, zie PLAN-APPLE-DEVELOPER-2026-05-28.md.
- **Rollback**: launcher.py wordt geback-upt (`launcher.py.pre-webview.bak`). De
  fallback + env-var zorgen dat de oude browser-modus altijd binnen handbereik is.

---

## Wat NIET in scope is
- app.py-logica, Flask-routes, UI-code (op kleine WebKit-fixes na).
- Gebundelde Chromium (alleen als WebKit iets echt niet kan).
- Windows-build (apart, later).
- Code-signing/notarization.

---

## Beslissing aan Sjuul
1. Akkoord met pywebview-aanpak (geen gebundelde Chromium)?
2. Mag ik launcher.py + spec aanpassen (met backup + fallback), zodat jij daarna 1x
   `./build_macos.sh dmg` draait en de checklist afloopt?
