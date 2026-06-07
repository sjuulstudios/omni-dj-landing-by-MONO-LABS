# Omni DJ - Sessie 77 testrapport (2026-06-05)

Volledige test van alles wat in sessie 77 is gebouwd. Opgesplitst in (A) wat ik
automatisch kon verifieren en (B) wat alleen jij op je Mac kunt testen (UI,
visueel, E2E, native, login). Niets is nog gecommit; dit rapport hoort bij de
diff bovenop commit `16e79fd`.

## Samenvatting

- Automatisch: 65+ checks groen. 1 echte (PRE-BESTAANDE) vondst: dubbele
  `POST /api/brand-kit/logo`. 1 edge-case in de drift-logica gehardend.
- Live infra: Supabase 8 tabellen RLS-aan met policies, security-advisors LEEG;
  omnidj.com LIVE met werkende DMG-download (jouw sessie-76 push staat live).
- Handmatig (jij): UI/visueel + E2E van C7, C3, C8/C8b, Spoor D (normaal + manual),
  Electron B0/B1. Checklist onderaan.

---

## A. Automatisch geverifieerd (door mij)

### A1. Python (backend)
- `py_compile` groen: app.py, audio_sync.py, analyzer.py, cutter.py, auth.py,
  billing.py, uploader.py, media_tools.py, runtime_config.py.
- Geen dubbele top-level functienamen (203 functies).
- Alle nieuwe routes geregistreerd: `/api/clips`, `/api/clips/sync`,
  `/api/sync-import`, `/api/calendar/list`, `/api/brand/profile`, `/api/workspaces`.
- VONDST (pre-bestaand, niet sessie 77): `POST /api/brand-kit/logo` is TWEE keer
  geregistreerd: `upload_brand_logo()` (app.py r.3806, wint) en `api_brand_logo()`
  (r.6687, dood voor POST). Deterministisch naar de eerste; geen nieuwe breuk.
  Aanbeveling: opruimen (bepaal welke canoniek is), maar pas met jouw test want het
  raakt werkende brand-logo-flow. NIET in dit sessie-werk aangeraakt.

### A2. audio_sync.py (Spoor D wiskunde)
- `_drift_to_tempo`: klein -> geen correctie; veilig -> tempo + "Corrected"-warning;
  extreem (200s) -> clamp 1.0 + "outside"-warning. EDGE GEHARDEND: drift >= duur
  (pathologisch) gaf eerst misleidend "Corrected"; nu correct "outside".
- `_clean_filter`: offset>0 -> adelay, offset<0 -> atrim, tempo!=1 -> atempo.
- `_xcorr_lag`: vindt een 5-sample shift terug (synthetische impulstreinen).
- `_downsample_env`: 600 punten, genormaliseerd 0..1.
- `_clip_rows_from_job` (app.py): bouwt geldige rij, kolommen matchen het
  `clips`-schema (workspace_id/local_path/label/duration_s/source_set/kind).

### A3. Frontend SPA (static/index.html)
- `node --check` op de inline JS: groen.
- Geen dubbele element-IDs in de statische HTML (475 unieke ids).
- Alle event-handlers van deze sessie zijn gedefinieerd (openSyncImport,
  closeSyncImport, syncPick, runSyncImport, syncConfirmManual, syncOnSlide,
  settingsToggleAdvanced, calOpenSchedule/Save, importClipPick, openFilePicker,
  openWatchFolderUI).
- Alle nieuwe IDs aanwezig: sync-modal, sync-manual, sync-wave, sync-offset-slider,
  sync-progress, analyse-tile-sync, settings-adv-body/-toggle, ed-split-x/-y,
  settings-sec-privacy.
- `<main>`/`<section>` tag-balans gelijk. Geen em/en-dashes in SESSIE 77-regels.
- localStorage-sleutels consistent gebruikt (omniDjEditorDefaults/ExportDefaults/
  EditorPanes elk read+write).

### A4. Electron (electron/)
- `node --check` main.js + preload.js groen. package.json valid (main=main.js).
- B1-features aanwezig: detached spawn, process-groep-kill, Menu.buildFromTemplate,
  setWindowOpenHandler, SIGINT/SIGTERM.

### A5. Live infrastructuur
- Supabase (`lbabsffxefkrxwzkbzar`): RLS AAN op clips(4)/scheduled_posts(4)/
  beta_signups(1, insert-only)/workspaces(4)/workspace_members(4)/dj_profiles(4)/
  dj_templates(4)/profiles(2). Security-advisors: LEEG (0 lints).
- Website omnidj.com: HTTP 200, live content; "Download Omni DJ" ->
  `https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg`. Jouw sessie-76 push is dus
  live gedeployed. Beta-formulier aanwezig.

---

## B. Handmatige smoketest-checklist (jij, op de Mac)

Dit kan ik niet doen: het vereist de draaiende dev-server `:5599` (of de Electron-
app), jouw login, echte bestanden, en visuele/native bevestiging. Werk per blok af.

### B0. Start
- [ ] Dev-server vers: `bash "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/_dev_restart_5599.sh"`
- [ ] Open `http://127.0.0.1:5599/?v=s77test`, log in.

### B1. Punt 3 - clip-metadata + Calendar
- [ ] Analyseer een set (of gebruik een bestaande in de history).
- [ ] Calendar -> "Schedule a post": de clip-picker toont ECHTE clips (label + set-naam).
- [ ] Kies clip + datum + 1 platform -> Opslaan.
- [ ] Supabase: `scheduled_posts.clip_id` is gevuld (UUID) en `clips` heeft rijen.

### B2. C7 - Settings herinrichting (visueel)
- [ ] Settings: Account + Workspace + Privacy als kaarten zichtbaar.
- [ ] "Advanced" klapt open: Editor-defaults, Export-defaults, Watch folder,
      Capabilities, Brand kit, Opslag, Diagnostics.
- [ ] Bestaande knoppen werken nog: Log out, (Account) Save, Watch "Choose folder",
      Diagnostics "Download logs".

### B3. C8 + C8b - defaults werken echt
- [ ] Zet in Settings > Advanced > Export-defaults: captions aan, watermark aan.
- [ ] Open Export op een verse clip (zonder eerdere export): toggles staan zoals
      jouw default.
- [ ] Zet Editor-default ratio op 16:9 -> reload -> open een clip -> editor opent op
      16:9 (mits die variant bestaat); rail-knop matcht. (1:1/4:5 pakken pas zodra
      die variant gecut is - dat is bewust.)

### B4. C3 - sleepbare editor-panes
- [ ] Open een clip in de editor.
- [ ] Sleep de balk tussen de cue-lijst en de preview (breder/smaller).
- [ ] Sleep de balk boven de timeline (timeline hoger/lager).
- [ ] Reload -> maten blijven. Bestaande trim/tekst/track-resize werken nog.

### B5. Spoor D - sync (NORMAAL, hoge confidence)
- [ ] Analyse-page -> tile "Video + audio sync".
- [ ] Kies een camera-video (met boordgeluid) + schone audio van DEZELFDE set.
- [ ] "Sync + analyse": loading bar, dan confidence% + offset, dan start de analyse.
- [ ] Clips zijn correct gesynced (zoals de Lisa Korver-test).

### B6. Spoor D - D4 manual-align (LAGE confidence)
- [ ] Kies een BEWUST out-of-sync paar (of een opname met stilte aan het begin),
      zodat de confidence < 15% valt.
- [ ] In plaats van auto-muxen verschijnt de manual-align-sectie: twee waveforms
      (boven camera, onder schone audio) + een slider.
- [ ] Schuif de slider tot de pieken uitlijnen -> "Use this alignment".
- [ ] Het muxt met jouw offset en start daarna de analyse. Controleer de uitlijning.

### B7. Electron B0 + B1
- [ ] `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/electron"`
- [ ] `npm start` -> splash -> de gewone UI in een venster.
- [ ] Login/analyse/export werken; menubalk + Cmd-shortcuts (Cmd+Q/C/V/R) werken.
- [ ] Sluit het venster -> backend stopt. Controleer tree-kill:
      `ps aux | grep "app.py"` toont GEEN achtergebleven proces.

### B8. Afronden
- [ ] Als bovenstaande groen is: commit sessie 77 (de TE-COMMITTEN-lijst staat in
      HANDOVER.md, sessie-77-blok). Daarna eventueel gesignde rebuild later.

---

## C. Wat NIET kon en waarom
- Geen toegang tot de draaiende `:5599`-server vanuit mijn sandbox (andere machine).
- Geen login (ik mag/heb je wachtwoord niet).
- Geen visuele render, geen native Electron-runtime, geen echte ffmpeg-mux-output.
- RLS-isolatie met een echte user-JWT (cross-account) E2E - de policies staan er
  wel en zijn eerder (sessie 71) op een branch groen geaudit.
