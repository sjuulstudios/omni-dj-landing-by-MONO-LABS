# PLAN - Native app via Electron (Tier 3)

> Datum: 2026-05-30 (sessie 65)
> Doel: Omni DJ als een solide, native-voelende desktop-app (eigen venster, native
> menu's, notificaties, Dock-progress, geen browser-luchtje). Voor betalende klanten,
> macOS + Windows. Analyse blijft 100% lokaal.
> Aanpak: Electron-shell rond je BESTAANDE Python-backend (als sidecar).
> Status: PLAN - nog niet uitgevoerd. Wacht op "ja".

---

## Kernidee (lees dit eerst)

Electron VERVANGT je Python-backend NIET. Het wrapt 'm.

- Je Flask + analyse-code (librosa/scipy/ffmpeg/YOLO/etc.) blijft exact zoals het is.
- PyInstaller blijft die backend bouwen tot 1 executable (zoals nu in build_macos.sh).
- Electron is de "shell": het toont je web-UI in een Chromium-venster EN start de
  PyInstaller-backend als kind-proces ("sidecar") op de achtergrond.
- De UI praat met de backend via `http://127.0.0.1:<poort>` - net als nu. Lokaal,
  niets gaat het internet op (behalve login/Supabase + Stripe, zoals nu).

Visueel:

  [ Electron-venster (Chromium) ]  <-- jouw index.html, native menu's, notificaties
            |  praat met (localhost)
  [ PyInstaller Python-backend ]   <-- Flask + librosa + ffmpeg + YOLO = analyse
            |
  [ jouw bestanden op schijf ]     <-- audio/video nooit geupload

## Loopt analyse nog lokaal? JA.

Niets verandert aan waar de analyse draait. De zware Python doet nog steeds alles op
de machine van de gebruiker. Electron voegt alleen een mooier, native venster + OS-
integratie toe. Je local-first belofte (privacy / offline / geen upload-wachttijd)
blijft volledig intact en wordt een sterker verkoopargument met een echte app-shell.

---

## Wat je hiervoor terugkrijgt (waarom Tier 3)

- Chromium-rendering identiek aan Chrome overal (geen WebKit-verschillen). Veiligste
  basis als je later een zware editor/timeline/WebGL-feature bouwt.
- Turnkey native API's: echt macOS-menubalk, Cmd-shortcuts, systeem-notificaties,
  Dock-progress/badge, tray, auto-update (Squirrel/electron-updater), recent-files,
  drag-clip-naar-desktop, file-associaties.
- Eén rendering-engine om tegen te testen op Mac EN Windows.

Kosten (eerlijk):
- Bundle +100-200 MB (Chromium). Voor een desktop-creator-tool acceptabel.
- Tweede toolchain naast Python: Node + Electron + electron-builder. Meer
  build-infra om als solo-dev te onderhouden.
- Twee processen (Electron + Python-sidecar) netjes laten starten/stoppen vereist
  zorgvuldige lifecycle-code (hieronder gedekt).

---

## Architectuur-details die we goed moeten doen

### 1. Backend als sidecar
- PyInstaller bouwt de backend tot `omnidj-backend` (one-folder, niet one-file -
  one-folder start sneller en speelt beter met grote native libs als torch/llvmlite).
- Electron's main-process spawnt die executable bij app-start met een VRIJE poort
  (niet hard 5555 - we zoeken een vrije poort en geven 'm mee als argument, zodat
  twee instanties of een bezette poort niet botsen).
- Electron wacht tot de poort antwoordt (health-check op `/`), laadt dan de UI.
  Tot die tijd: splash-screen (geen wit scherm).

### 2. Lifecycle (het belangrijkste risico)
- App-quit -> Electron MOET het Python-sidecar-proces killen (anders blijft Python
  draaien als zombie). We registreren `before-quit` + `window-all-closed` + een
  process-tree-kill (taskkill op Windows, SIGTERM->SIGKILL op Mac).
- Crash van de backend -> Electron toont een nette foutmelding + "herstart", i.p.v.
  een dood venster.

### 3. ffmpeg / native deps
- ffmpeg + ffprobe blijven meegebundeld (zoals nu in build_macos.sh, regel ~115).
  In de Electron-build verhuizen ze naar de app-resources; backend zoekt ze via een
  expliciet pad i.p.v. PATH (betrouwbaarder in een gebundelde app).
- Zware optionele deps (torch/demucs, ultralytics/YOLO) blijven optioneel; de build
  kan een "lite" (zonder torch) en "full" variant kennen om de omvang te beheersen.

### 4. Auth/redirects
- Supabase password-reset + OAuth-redirects gebruiken nu `127.0.0.1:5555/...`. Met een
  dynamische poort moeten redirect-URL's mee. Optie: vaste poort behouden voor auth
  maar conflict-fallback; of een custom protocol (`omnidj://`) registreren voor
  redirects (netjes + native). Te beslissen bij implementatie.

### 5. Native polish (de "solide app"-laag)
- macOS-menubalk: Omni DJ / File / Edit / View / Window / Help + Cmd+Q, Cmd+W, About.
- Systeem-notificatie wanneer een analyse/export klaar is.
- Dock-progress tijdens analyse (taakbalk-progress op Windows).
- Splash-screen tijdens backend-opstart.
- Eigen venster-frame + jouw icoon (icon.icns is al klaar; Windows .ico nog maken).
- Later optioneel: auto-update via electron-updater.

---

## Code-signing / notarization (parallel, must-do voor klanten)

Dit is het grootste "echte app"-signaal. Zonder signing toont macOS een
"niet-geidentificeerde ontwikkelaar"-waarschuwing.

- macOS: Apple Developer account ($99/jr) -> Developer ID -> sign + notarize de
  Electron-app (electron-builder doet dit; je bestaande notarize-stappen uit
  build_macos.sh vervallen want Electron-builder neemt het over).
- Windows: code-signing-certificaat (apart; EV-cert geeft direct SmartScreen-trust,
  duurder). Kan later.
- Detail-plan: PLAN-APPLE-DEVELOPER-2026-05-28.md (macOS) - dit Electron-plan haakt
  daarop in.

---

## Bouwstructuur (nieuw)

```
Omni DJ/
├── (bestaande Python-app, ongemoeid)
├── electron/
│   ├── main.js          ← spawnt backend, maakt venster, menu's, lifecycle
│   ├── preload.js       ← veilige bridge (contextIsolation aan)
│   ├── splash.html      ← laadscherm
│   └── package.json     ← electron + electron-builder config
└── build-electron.sh    ← 1) PyInstaller backend 2) electron-builder package
```

PyInstaller bouwt de backend, electron-builder verpakt Electron + backend +
ffmpeg in 1 `.app`/`.dmg` (Mac) en `.exe`/installer (Windows).

---

## Stappenplan (fases)

**Fase 0 - prototype (bewijs dat het werkt, klein):**
- Minimale Electron main.js die de bestaande dev-backend (python app.py) start op een
  vrije poort, wacht, en de UI laadt in een venster. Geen packaging nog.
- Doel: bevestigen dat jouw UI + analyse + export volledig werken in Chromium-venster.

**Fase 1 - lifecycle + native polish:**
- Sidecar-spawn met PyInstaller-build i.p.v. losse python.
- Quit/crash-handling (geen zombie-processen).
- Menubalk, shortcuts, finish-notificatie, splash, Dock-progress.

**Fase 2 - packaging macOS:**
- electron-builder config; `.app` + `.dmg`. ffmpeg meebundelen. Test op schone map.

**Fase 3 - signing/notarization macOS:**
- Apple Developer + Developer ID via electron-builder. Geen Gatekeeper-warning meer.

**Fase 4 - Windows:**
- PyInstaller Windows-backend + electron-builder NSIS-installer. WebView2 n.v.t.
  (Electron bundelt eigen Chromium). Windows-signing later.

---

## Test-checklist (in het Electron-venster)
1. App opent als eigen venster, geen Chrome-tab, jouw icoon in Dock/taakbalk.
2. Backend start (splash -> UI), op een vrije poort.
3. Inloggen + (Supabase) redirect-flow werkt.
4. Upload via `<input type=file>` opent native bestandskiezer; file komt binnen
   (audio/video + font + logo/watermark).
5. Drag-drop op de dropzone werkt.
6. Volledige analyse draait lokaal; CPU/RAM acceptabel.
7. Editor + timeline + `<video>`-preview speelt/scrubt.
8. Export met captions -> MP4 op schijf. Finish-notificatie verschijnt.
9. "Reveal in Finder/Explorer" werkt.
10. App afsluiten -> GEEN achtergebleven Python-proces (check Activity Monitor).
11. Backend-crash -> nette foutmelding, geen dood venster.

---

## Risico's / eerlijk
- **Twee-proces-lifecycle** is de #1 valkuil (zombie Python). Expliciet gedekt in Fase 1.
- **Bundle-omvang**: Chromium + Python + ffmpeg + (optioneel torch) kan groot worden.
  Mitigatie: one-folder PyInstaller, "lite" build zonder torch, compressie in installer.
- **Twee toolchains** (Node + Python) om solo te onderhouden. Reëel, maar beheersbaar
  met 1 build-script (`build-electron.sh`).
- **Auth-redirects + dynamische poort**: vereist een keuze (vaste poort vs custom
  protocol). Niet moeilijk, wel bewust beslissen.
- **Bestaande PyInstaller-`.app`-flow** (build_macos.sh) blijft bestaan als fallback
  tijdens de overgang; we slopen 'm pas als Electron groen is.

## Rollback
- Niets aan de Python-app verandert destructief. De Electron-laag is additief in
  `electron/`. De huidige `.app`-build blijft werken tot je 'm bewust vervangt.

---

## Beslissing aan Sjuul
1. Akkoord met Electron-rond-PyInstaller-sidecar (niet Python herschrijven)?
2. Beginnen we met **Fase 0 (prototype)** deze of volgende sessie, zodat we eerst
   bewijzen dat jouw UI + analyse + export in een Electron-venster werken vóór we
   in packaging/signing investeren?
3. Akkoord dat signing/notarization (Fase 3) erbij hoort als must-do voor klanten?
