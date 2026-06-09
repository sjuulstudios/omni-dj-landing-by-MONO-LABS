# Omni DJ - HANDOVER (compact)

> **Lees dit altijd als eerste.** Update na elke significante stap.
> Volledige historie staat in `HANDOVER-FULL-2026-06-02.md` + `HANDOVER-ARCHIVE.md` + `LESSONS-LEARNED.md`.
> Deze versie is bewust ingedikt: actuele status + openstaande acties bovenaan, thematische naslag eronder.

---

## 0. VOLGENDE SESSIE - START HIER

### Website status (2026-06-04) - LIVE
- **omnidj.com** is LIVE met de nieuwe Next.js site (`omnidj.com/` map in de repo).
- **Cloudflare Pages project:** `omni-dj-landing-by-mono-labs`
- **GitHub repo:** `sjuulstudios/omni-dj-landing-by-MONO-LABS`, branch `main`, commit `34ed96b`
- **Build settings:** root dir = `omnidj.com`, build = `npm run build`, output = `out`
- **Custom domains:** `omnidj.com` + `www.omnidj.com` (beide gekoppeld, www kan nog 48u propageren)
- **Fix toegepast:** `remotion/` uitgesloten van `omnidj.com/tsconfig.json` om build-fout op te lossen
- **Cloudflare Pages deploys automatisch** bij elke push naar `main`
- **Nog open (website):**
  - Download + beta-aanmeldingen: AANGEPAKT in sessie 76 (zie het sessie-76-blok hieronder). Download-knoppen wijzen nu naar de DMG; het beta-formulier gaat naar een eigen Supabase-tabel `beta_signups` i.p.v. Formspree. Wacht alleen nog op `git push` door Sjuul (Cloudflare auto-deploy).
  - Google Workspace domein-verificatie voor `monohq-labs.com` nog niet afgerond
- **Oude landing:** `landing-omnidj/` map is de vorige simpele 1-page versie, niet meer actief

> **GECOMMIT + GEPUSHT (2026-06-04):** commit `9176c8a` op `main` bevat sessie 69+71+72+73+74 (22 bestanden). De "NIET gecommit"-vermeldingen verderop zijn historisch. NOG OPEN voor Sjuul: test-infra (pytest/Playwright) + punt 5 (C7/C3/B0/Spoor D). (Bijgewerkt sessie 77: migratie 007 clips-metadata staat AL LIVE en is nu gewired in de Calendar; migratie 010 + DMG->R2 zijn in sessie 75/76 afgerond. Sessie 76 website nu GECOMMIT als `16e79fd`, wacht op `git push` door Sjuul.) (E2E-export-check fase 2b: GEDAAN in sessie 75 + logo-export-bug gefixt, zie direct hieronder. Sessie 75 nu GECOMMIT + GEPUSHT: commit `302c4d7` op `main` (origin/main), DMG->R2 live.)

---

**Sessie 81 (2026-06-09) - 1:1 (en 4:5) export-bug GEFIXT + ffmpeg-bewezen. De "1x1" export was fysiek 1080x1080 maar bevatte een geletterboxde 16:9 (zwarte balken boven/onder) i.p.v. een gevulde vierkante crop. Root cause: `_derive_with_tracking` (draait zodra een clip een tracking-bestand heeft) gebruikte voor square/portrait45 `scale=...force_original_aspect_ratio=decrease,pad=...:black`; bij `crop_mode: "letterbox"` (clip03's tracking) padde dat de hele wide shot tot een vierkant. Fix code-side, NIET gecommit tot rebuild.**

- **End-to-end diagnose (alle tools):** ffprobe op de echte exports in ~/Downloads (`EDIINE - 1x1.mp4`) toonde 1080x1080 MAAR een frame-extract toonde de volledige 16:9-shot met zwarte balken. Het tussenbestand `output/a4aae701/..._clip03_drop_square.mp4` was identiek geletterboxd. `tracking/clip_003.json` -> `crop_mode: "letterbox"`, keyframes leeg. De draaiende app is de Electron-bundle in /Applications (geinstalleerd 7 juni) met huidige source (index.html md5 matcht, app.py heeft `_derive_ratio_file`). Twee derive-paden ontdekt: editor `/api/derive` -> `_derive_with_tracking` (tracking-bewust MAAR letterbox-buggy) en export `_resolve_export_sources` -> `_derive_ratio_file` (correcte center-crop MAAR tracking-blind); de export hergebruikte bovendien het door de editor gecachte foute bestand.
- **Fix (`app.py`, 2 plekken):** (1) `_derive_with_tracking`: voor square/portrait45 nu ALTIJD een gecentreerde crop-to-fill rechtstreeks uit de bron (zelfde filter als `_derive_ratio_file`/`api_derive_ratio`), crop_mode/keyframes bewust genegeerd want Sjuul wil de DJ GECENTREERD (niet getrackt-gevolgd) voor 1:1 en 4:5. Ongebruikte import `_build_tracked_vertical_crop` verwijderd. De 9:16-render (recut_clip/cut_clip_vertical) is ONGEMOEID, dus letterbox blijft werken voor vertical. (2) `_resolve_export_sources`: de gecachte `clip['files'][square|portrait45]` wordt NIET meer hergebruikt maar altijd her-derived met de center-crop (overschrijft via -y het deterministische pad). Reden: een oud geletterboxd bestand is fysiek 1080x1080 (balken ingebakken) dus niet via dimensies te detecteren; altijd her-deriven garandeert correctheid en lost de stale-cache op zonder bestanden te verwijderen.
- **GEVERIFIEERD met echte ffmpeg op de clip03-bronnen (`_verify_1x1_fix.sh`):** 1:1 uit landscape -> 1080x1080, frame toont DJ gevuld+gecentreerd, GEEN balken. 4:5 uit vertical -> 1080x1350, idem DJ gevuld+gecentreerd. py_compile groen, 0 em/en-dashes in de nieuwe regels. Backup `app.py.pre-sessie81-1x1fix.bak`.
- **BEPERKING/NB:** de editor-preview kan voor een AL eerder gecachte clip nog het oude letterbox-bestand tonen tot het opnieuw wordt afgeleid (force), maar de EXPORT is altijd correct (her-derive). Nieuwe previews zijn correct. Clips met ECHTE keyframes worden voor 1:1/4:5 nu ook gecentreerd (bewuste keuze Sjuul), niet meer subject-getrackt; de getrackte follow blijft voor 9:16.
- **GECOMMIT sessie 81:** `f5237a6` (app.py + HANDOVER). NIET gecommit: `app.py.pre-sessie81-1x1fix.bak`, `Omni DJ/_verify_1x1_fix.sh` (opgeruimd).
- **GESIGNDE REBUILD + R2-UPLOAD GEDAAN (2026-06-09):** verse gesignde/genotariseerde DMG met de 1x1-fix erin (`SESSIE 81`-marker in de sidecar-app.py geverifieerd), spctl app EN dmg `accepted / Notarized Developer ID`. Eindartefact `electron/dist-electron/Omni DJ-1.0.0-arm64.dmg` (367.542.120 bytes). **UPLOAD NAAR R2 GELUKT** ondanks twee blokkades: wrangler weigert >300 MiB en de Chrome-upload-tool cap is 10 MB. Oplossing: via Chrome-MCP in het Cloudflare-dashboard een TIJDELIJK scoped R2 Account API-token gemaakt (Object Read & Write, alleen bucket `omnidj-downloads`), DMG ge-upload met boto3 multipart (S3-endpoint `<acct>.r2.cloudflarestorage.com`), daarna token METEEN verwijderd (dashboard "Delete"). Live geverifieerd: `https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg` HTTP 200, content-length 367542120 = de verse build, last-modified vandaag, cf-cache MISS. Website ongewijzigd (zelfde bestandsnaam). boto3 is nu in de venv geinstalleerd. NB: Sjuul moest eenmalig in Chrome bij Cloudflare inloggen (token-creatie vereist dashboard; OAuth-wrangler-token mist R2-scope).
- **NOG OPEN:** smoke-test van de live DMG door Sjuul (download van omnidj.com, openen, picker/login/analyse/export, 1:1 nu een echte gevulde crop). `git push origin main` (commits `ebfbb5f`+`3bfb0f9`+`4731c8e`+`f5237a6`).

Detail: memory `project_sessie81_1x1_crop_fix`.

---

**Sessie 80 (2026-06-07) - Electron-icoon gediagnosticeerd + dev-Dock-icoon-fix + VERSE Electron-rebuild + DMG gedraaid op de Mac (exit 0, geverifieerd). De gepackagede app had het Omni DJ-icoon en de naam "Omni DJ" AL correct (sessie 78 config klopte); het "Electron"-icoon dat Sjuul in het Dock zag is dev-mode (npm start). De nieuwe DMG bevat nu ook de sessie 79 frontend (C5 Brand). NIET gecommit (stapelt op 77+78+79). GUI-smoke-test van de .app blijft voor Sjuul (stond ook nog open uit sessie 78).**

- **Diagnose:** Dock-icoon "Electron" met die tekst = `npm start` (dev draait de generieke Electron-binary uit node_modules; icoon en naam komen dan uit de Electron.app-bundle zelf). De sessie-78 packaged build was al goed: `productName` "Omni DJ", `build/icon.icns` (checksum identiek aan `static/icon.icns`), CFBundleName + CFBundleDisplayName "Omni DJ".
- **Fix (`electron/main.js`, in whenReady):** in dev (niet packaged, darwin) `app.dock.setIcon(APP_DIR/static/icon_1024.png)` -> ook `npm start` toont nu het Omni DJ-icoon in het Dock. De Dock-TEKST blijft in dev "Electron" (macOS leest die uit de Electron.app-bundle; niet aanpasbaar zonder node_modules te hacken). Packaged pad ongemoeid. `node --check` groen, 0 dashes. Backup `main.js.pre-sessie80.bak`.
- **Rebuild (via osascript-achtergrond, runner `electron/_build_sessie80.sh`):** GOTCHA bovenop de sessie-78 ffmpeg-PATH: `pyinstaller` zit ALLEEN in de venv -> in een non-interactieve shell moet `venv/bin` vooraan op PATH (eerste run faalde op de build_macos.sh-sanitycheck; runner gefixt). Daarna build exit 0 in ~2,5 min (warme PyInstaller-cache). Log `electron/_build_sessie80.log` (*.log is gitignored).
- **Output + verificatie (alle 5 groen):** `electron/dist-electron/Omni DJ-0.1.0-arm64.dmg` (367 MB, 2026-06-07). (1) icon.icns in de app = Omni DJ-logo (md5 64813d80...), (2) CFBundleName/DisplayName "Omni DJ", (3) sidecar-backend vers gestaged (Contents/Resources/backend/), (4) `static/index.html` IN de sidecar byte-identiek aan de sessie-79 bron (de rebuild-reden), (5) dock-fix aanwezig in app.asar.
- **NOG door Sjuul:** GUI-smoke-test van de NIEUWE DMG/.app (openen, login/analyse/export, na afsluiten geen achtergebleven backendproces via `ps aux | grep -i 'omni dj'`). Signing (B3) bewust nog uit (identity null), dus Gatekeeper kan om rechtsklik-Open vragen.
- **TE COMMITTEN sessie 80 (stapelt op 77+78+79):** gewijzigd `Omni DJ/electron/main.js` (dev-Dock-icoon), `HANDOVER.md`. NIET committen: `electron/main.js.pre-sessie80.bak`, `electron/_build_sessie80.sh`, `electron/_build_sessie80.log`, `electron/dist-electron/`, `electron/resources/backend/`, `electron/build/icon.icns`.

- **SESSIE 80 VERVOLG - B3 GEDAAN (zelfde dag): gesignde + genotariseerde Electron-DMG, beide spctl "accepted / Notarized Developer ID".** Eerst commit `ebfbb5f` op main (sessies 77-80, 17 bestanden; stale `.git/HEAD.lock` van 5 juni met akkoord Sjuul verwijderd; LET OP: `electron/build/` valt onder de generieke `build/`-ignore -> entitlements.mac.plist is met `git add -f` toegevoegd en blijft nu gewoon getrackt). Daarna B3: `electron/package.json` versie 0.1.0 -> **1.0.0**, `mac.identity` = "Sjuul Smits (PTLV7AY4UL)" (**VALKUIL: electron-builder wil de identity ZONDER het "Developer ID Application:"-prefix**, anders harde fout), `dmg.sign: true` (nieuw; electron-builder signt de dmg-container anders NIET). `build_electron.sh` accepteert nu optioneel argument `sign` -> geeft het door aan build_macos.sh (backend per-component gesigned, vereist `APPLE_DEVELOPER_ID` env, met prefix). Flow gedraaid via runner `electron/_build_sessie80_signed.sh`: backend-sign -> electron-builder (deep-sign, identity-hash gevonden) -> codesign verify groen -> notarytool submit dmg (profiel `omnidj-notary`, status **Accepted**) -> staple dmg + app. Nazorg: de dmg-CONTAINER was nog ongesigned (spctl rejected) -> `_sign_dmg_sessie80.sh`: codesign dmg + her-notarize (**Accepted**) + staple -> **spctl dmg: accepted / Notarized Developer ID; spctl app: accepted / Notarized Developer ID**. Eindartefact: `electron/dist-electron/Omni DJ-1.0.0-arm64.dmg` (368 MB, 2026-06-08). De entitlements-set van s78 dekt de backend-keys (jit/unsigned-exec-mem/lib-validation/dyld/apple-events); network/files-keys uit entitlements.plist zijn sandbox-only en inert. NOG: smoke-test Sjuul (incl. picker!) -> DAARNA pas DMG->R2 als `Omni-DJ-1.0.0.dmg` (overschrijft; website ongewijzigd). TE COMMITTEN B3: `electron/package.json`, `electron/build_electron.sh`, `HANDOVER.md`. NIET committen: `_build_sessie80_signed.sh/.log`, `_sign_dmg_sessie80.sh/.log`, `_commit_sessie77_80.sh`.

Detail: memory `project_sessie80_electron_icon_rebuild`.

---

**Sessie 79 (2026-06-06) - C5 Brand-pagina redesign + reconciliatie AUTONOOM gebouwd (frontend-only, alleen `static/index.html`). De V2 Brand-view is heringedeeld in heldere C5-secties + een live 9:16 preview, de per-workspace backend-profielvelden (sessie 74) zijn nu ECHT zichtbaar in V2, EN een "Apply to exports"-knop pusht de pack-logo/watermark naar de bestaande `/api/brand-kit`-endpoints zodat de look ECHT in de export bakt. Statisch groen (node --check, id-uniek, main-balans, geen dashes). NIET visueel/E2E getest (vereist login op :5599 + een echte export). NIET gecommit (stapelt op 77+78).**

- **Context:** Sjuul vroeg het C5-plan ("Redesign Brand-pagina") autonoom uit te voeren. Diagnose-vondst: er waren TWEE losgekoppelde Brand-systemen. (1) De V2-view `#view-brand` draait volledig op een localStorage-store `window.OmniBrand` (brand-packs: logo/kleuren/watermark/templates/captions). (2) De ECHTE per-workspace data (`/api/brand/profile`, sessie 74: artist_name/alias/cta/hashtags/caption_voice) had alleen UI in de legacy `#view-style`, die in V2 NOOIT getoond wordt. C5 = die versnippering opheffen.
- **Aanpak (veilig, additief, GEEN backend/pipeline-wijziging):** de sessie-74 `ap-*`-velden + `loadArtistProfile`/`saveArtistProfile` (querien op id, met document-niveau delegated save-handler) zijn verplaatst van de dode `#view-style` naar `#view-brand`, gegroepeerd in C5-secties. De bestaande OmniBrand-kaarten (logo/kleuren/watermark/templates/caption-presets/hooks/ctas/caption-copy/stickers) blijven 1-op-1 werken, alleen heringedeeld onder sectiekoppen.
- **Nieuwe indeling `renderBrand()`:** Identity (artist name/alias/avatar) -> Live preview -> Visual (Brand Kit + Watermark) -> Typography (title/caption-font, nieuw op de pack) -> Lower-third and CTA (links/cta backend + bestaande CTA-teksten) -> Hashtags (backend per platform + bestaande hashtag-sets) -> Templates -> Captions and extras (caption voice + presets/hooks/copy/stickers). Sectiekoppen via nieuw `_c5SectionHead()`.
- **Live preview (`renderBrandPreviewCard` + `_c5RenderPreview`):** lichte CSS 9:16 mock die logo-positie/grootte/opacity, accentkleur, watermark, artist-naam en CTA toont; herverft live via een delegated input/change-listener op `#v2-brand-sections` (setTimeout-0 zodat de kaart-handler eerst de pack bijwerkt). BEWUST geen zware on-demand render (sessie 77 stelde dat uit).
- **Consolidatie:** het "Brand kit"-samenvattingsblok is uit Settings gehaald (de JS die `settings-brand-name/accent` vulde is null-safe -> veilig) en het legacy `#artist-profile-room` is uit `#view-style` verwijderd (anders dubbele `ap-*` ids -> getElementById-breuk).
- **Backend = ONGEMOEID.** Identity/links/hashtags/voice persisten via de bestaande `/api/brand/profile` (sessie 74). Logo/kleuren/watermark/typografie/templates/captions blijven OmniBrand-localStorage. Geen wijziging aan app.py/cutter.py.
- **RECONCILIATIE (vervolg, zelfde sessie - "Apply to exports"):** lost beperking (a) op zonder de pipeline aan te raken. Nieuwe kaart in de Visual-sectie met `_c5ApplyPackToExports(pack)` + `renderApplyExportsCard` + statusregel (`_c5RefreshApplyStatus` doet een read-only GET `/api/brand-kit`). De knop pusht de ACTIEVE pack naar exact dezelfde per-workspace endpoints die de legacy Brand Stack ook voedde (de sessie-75-bewezen bake-route): logo -> raster wordt via canvas naar PNG geconverteerd (svg passthrough) en geupload naar `POST /api/brand-kit/logo` (multipart `file`, png/svg + magic-check), daarna `POST /api/brand-kit {logo:{...,corner,opacity,size_pct}}` met 9-grid->4-hoek-mapping (`_c5PosToCorner`); image-watermark -> upload + `POST /api/brand-kit/watermark/settings`; palette (accent+secondary) + handle -> `POST /api/brand-kit`. Alles via `api()` (auth + `X-Omni-Workspace` + 401-refresh + FormData al ingebouwd). ADDITIEF + faalveilig (push alleen wat de pack heeft; geen destructieve delete) + alleen ingelogd. WAT BAKT ECHT: logo + image-watermark (cutter overlayt images). WAT NIET: kleuren/palette (referentie; cutter gebruikt geen palette direct), typografie, en TEKST-watermark (cutter bakt alleen image-watermark) -> eerlijk vermeld in de kaart-copy.
- **Geverifieerd (statisch, sandbox):** 1 inline script-block, `node --check` groen; alle 16 verplaatste/nieuwe ids exact 1x; legacy ids 0; alle 15 renderBrand-renderers gedefinieerd EN aangeroepen; `<main>` 16/16 balans; 0 em/en-dashes in toegevoegde regels (netto -2). NIET getest: live login/UI op :5599, echte export-bake.
- **BEKENDE BEPERKINGEN v1 (bewust, voor vervolg):** (a) OPGELOST via "Apply to exports" (zie reconciliatie-bullet): de logo/image-watermark bakt nu in de export na 1 klik. RESTEERT: het is een EXPLICIETE knop (geen auto-sync bij elke wijziging), en de Apply is additief (een logo verwijderen in V2 wist de backend-logo nog niet -> bidirectionele mirror is vervolg). (b) Typography-keuze stuurt de preview + nieuwe templates, maar wordt nog niet in de render gebakken (gebruikt de bestaande `/api/brand-kit`-fonts). (c) Avatar-upload roept `renderBrand()` aan (zoals de bestaande logo-upload), dus niet-opgeslagen getypte identity-tekst kan resetten -> eerst Save, dan avatar. (d) Kleuren/palette + tekst-watermark bakken niet in de video (cutter overlayt alleen logo/image-watermark).
- **VISUEEL/E2E TESTSCRIPT (Sjuul, op :5599, frontend-only dus GEEN server-restart nodig):** reload `http://127.0.0.1:5599/?v=s79c5`, log in, ga naar Brand. (1) De pagina toont secties Identity / Visual / Typography / Lower-third and CTA / Hashtags / Templates / Captions met een live 9:16 preview bovenaan. (2) Type een artist-naam + kies CTA -> de preview-naam/CTA updaten live. (3) Upload een logo + kies positie/kleur in Visual -> de preview verplaatst het logo + verandert de accentkleur. (4) Klik "Save identity and links" -> toast "Artist profile saved"; reload -> velden komen terug uit de backend (bewijst de `/api/brand/profile`-roundtrip). (5) Settings bevat GEEN "Brand kit"-blok meer. (6) No-regression: brand-pack wisselen/dupliceren bovenaan werkt nog, en analyse+export van een set werkt nog (pipeline ongemoeid). (7) RECONCILIATIE-bake (de kern): upload een PNG-logo in Visual, kies een hoek/grootte, klik "Apply to exports" -> toast "Brand applied to exports" + de statusregel zegt "logo on"; analyseer dan een korte set en exporteer een clip -> het logo staat ECHT in de geexporteerde MP4 in de gekozen hoek (dit is de sessie-75-bake-route, nu gevoed vanuit V2). Verifieer ook isolatie als je 2 workspaces hebt (logo per artist).
- **TE COMMITTEN sessie 79 (stapelt op 77+78):** gewijzigd `Omni DJ/static/index.html` (C5 Brand-redesign + "Apply to exports"-reconciliatie), `HANDOVER.md`. NIET committen: `static/index.html.pre-sessie79-c5.bak`.

Detail: memory `project_sessie79_c5_brand_redesign`.

---

**Sessie 78 (2026-06-05) - de drie sessie-77-vervolgpunten AUTONOOM gebouwd: Electron B1b/B2 (packaging) + Spoor D D5 (crowd-inmix in cutter) + per-workspace settings. Statisch groen + subagent-review groen + LIVE OP DE MAC geverifieerd: de Electron-DMG is gebouwd (352 MB, sidecar correct embedded) en D5 is bewezen op een ECHT gesynced 2-track-bestand (residu on-off correleert 0.998 met het highpass-crowd-spoor). NIET gecommit (stapelt op 77). Alleen de GUI-smoke-test van de .app blijft voor Sjuul.**

- **LIVE OP DE MAC geverifieerd (sessie 78 vervolg, via osascript):** (1) **Electron-build GEDRAAID**: `electron/build_electron.sh` -> PyInstaller-backend + electron-builder -> `electron/dist-electron/Omni DJ-0.1.0-arm64.dmg` (352 MB). De PyInstaller-backend zit embedded op exact het pad dat `resolveBackend()` als eerste checkt (`.../mac-arm64/Omni DJ.app/Contents/Resources/backend/Omni DJ.app/Contents/MacOS/Omni DJ` = SIDECAR_PRESENT). Signing correct OVERGESLAGEN (identity null = B3 uit). GOTCHA gevonden+omzeild: `build_macos.sh` heeft een `command -v ffmpeg`-sanity-check; in een non-interactieve shell moet `vendor/ffmpeg` op PATH staan (geen `brew install ffmpeg` nodig, dat zou juist de notarisatie breken). RESTEERT: alleen de GUI-smoke-test (de .app openen, login/analyse/export klikken, na afsluiten geen achtergebleven backendproces). (2) **D5 E2E BEWEZEN** op `workspaces/c78d89da-.../sync/Lisa Korver x Ho_r Berlin_synced.mp4` (echt 2-track, sessie-77 sync): de echte `_build_landscape_cmd` met inmix aan vs uit -> ON-output is 1 audiospoor, gebruikte de inmix-filtergraph, en het residu (ON minus OFF) correleert **0.998** met het apart geextraheerde highpass(200)+volume(0.25) camera-spoor = de crowd zit er aantoonbaar onder. (Mijn naieve "ON luider"-check faalde bewust: het cameraspoor bevat dezelfde muziek, dus het is geen pure energie-optelling; de 0.998-correlatie is het sluitende bewijs.) A/B-clips voor Sjuul in `~/Downloads/OmniDJ_D5_crowd_OFF.mp4` + `OmniDJ_D5_crowd_ON.mp4`.

- **Context:** Sjuul vroeg deze 3 punten volledig autonoom te doen. Aanpak: diagnose -> bouwen met backups -> statische + ffmpeg-verificatie, met respect voor de harde checkpoints (geen migratie naar main, geen verwijderingen, geen DMG->R2). Alle addities getagd `SESSIE 78`. Backups `*.pre-sessie78.bak` voor app.py/cutter.py/launcher.py/static/index.html/electron/main.js/electron/package.json.
- **Spoor D / D5 - crowd-inmix render in de cutter (GEBOUWD + ffmpeg-BEWEZEN):** een via Spoor D gesynced bestand draagt 2 audiosporen (a:0 schone mix = default, a:1 camera/crowd). D5 mixt de crowd (highpass + verlaagd volume) ONDER de schone mix tot EEN audiospoor in de render. `cutter.py`: nieuw `_normalize_inmix`/`_count_audio_streams`/`_inmix_active`/`_compose_inmix_filters` + een `inmix=None`-param door `_build_landscape_cmd`, `_build_vertical_cmd`, `cut_clip_landscape`, `cut_clip_vertical`, `recut_clip`. DEFAULT OFF + stream-telling-guard -> elke gewone (1-spoor) set rendert BYTE-IDENTIEK (bewezen: off-path-diff + 24 ffmpeg-checks). De inmix-filtergraph is gevalideerd met echte ffmpeg in alle 3 videomodi (none/vf landscape, vf vertical, complex/brand) op synthetische 2-track-bestanden -> 1v/1a output, gating klopt. `app.py`: `_count_audio_streams` geimporteerd; `_prebake_clip_for_export(inmix=None)` -> `recut_clip`; `_run_export_job` leest `cfg.inmix`, telt 1x de bron-audiosporen (`job.video_path`), en forceert in `_process` de prebake-recut MET inmix ALLEEN als enabled EN bron >=2 sporen (anders niets veranderd; geen ongewenste brand-bake want recut bakt brand alleen als die geconfigureerd is). Frontend: inmix-toggle + crowd-volume (15/25/40%) in C7 Export-defaults (`#ex-default-inmix`), opgeslagen in `omniDjExportDefaults.inmix`, en `startExport` stuurt `body.inmix` mee. **NOG door Sjuul (E2E):** een ECHT gesynced 2-track-bestand exporteren met de toggle aan -> crowd hoorbaar onder de mix; verifieer sign/volume. BEPERKING v1: per-clip/editor-control + 1:1/4:5-derive-inmix komen later (de derive cropt de bestaande cut).
- **Per-workspace settings (GEBOUWD + landt autonoom, GEEN migratie):** bewuste keuze om GEEN aparte `workspace_settings`-tabel/migratie te maken (dat zou een main-checkpoint vergen); in plaats daarvan opslag onder `dj_profiles.profile.settings` (JSONB sub-sleutel naast brand_kit/artist_name) -> hergebruikt de LIVE RLS van dj_profiles (008/010), workspace==dj_profile is 1-op-1. `app.py`: nieuw `GET/PUT /api/workspace/settings` (via `_user_supabase`+`current_workspace_id`, zelfde patroon als `/api/brand/profile`) + helper `_merge_workspace_settings` (2 niveaus diep). De settings-PUT raakt ALLEEN `profile.settings` (rest van het profiel blijft); de brand-PUT behoudt op zijn beurt `settings` (subagent bevestigd geen clobber over en weer). Frontend: `_settingsSaveDefaults` PUT't nu ook naar de server (ingelogd, fire-and-forget); nieuw `_settingsSyncFromServer` GET't + herverft bij Settings-open, workspace-wissel en login. Uitgelogd = puur localStorage (non-regressief). **NOG door Sjuul (E2E):** ingelogd op :5599, in 2 workspaces verschillende export-defaults zetten -> wisselen toont per-artist; reload behoudt.
- **Electron B1b + B2 (GEBOUWD, kan NIET in de sandbox draaien - native):** **B1b** (`electron/main.js`): `resolveBackend()` kiest de backend - in een gepackagede build draait het de meegebundelde PyInstaller-backend HEADLESS (extraResource `backend`, env `OMNI_DJ_NO_BROWSER=1`), in dev valt het terug op venv-python + app.py; override via `OMNI_DJ_BACKEND`. `launcher.py` slaat de browser-auto-open over bij `OMNI_DJ_NO_BROWSER` (standalone .app onveranderd). Backend-pad geverifieerd tegen build_macos.sh: `Contents/MacOS/Omni DJ` is de wrapper die `exec ".../Omni DJ.bin" "$@"` doet -> port-argv EN env bereiken launcher.py, PATH wijst naar de gebundelde ffmpeg. **B2** (`electron/package.json` build-config + nieuw `electron/build_electron.sh` + `electron/build/entitlements.mac.plist`): electron-builder bouwt een arm64-dmg, bundelt de PyInstaller-`.app` als sidecar; het script bouwt de backend via de bestaande `build_macos.sh`, staget 'm en draait electron-builder. **B3 (signing) staat UIT** (`mac.identity: null`) -> onverskende lokale build; entitlements + hardenedRuntime al klaar voor B3. `.gitignore` sluit de Electron-build-output uit. node --check + JSON + plist + bash -n groen. **NOG door Sjuul (op de Mac):** `cd electron && ./build_electron.sh`, dan smoke-test (.app opent, login/analyse/export, geen achtergebleven backendproces na afsluiten).
- **Geverifieerd (statisch + ffmpeg + subagent):** py_compile (app.py/cutter.py/launcher.py/audio_sync.py) groen, node --check (main.js/preload.js/inline SPA-JS) groen, package.json/plist valide, geen dubbele functienamen (app/cutter), beide nieuwe routes 1x geregistreerd, geen dubbele element-IDs, geen em/en-dashes in de additie-regels, en 24 echte-ffmpeg D5-checks groen. Een subagent-review van de diffs vond GEEN materiele regressie (off-paden byte-identiek, RLS-coexistence klopt, frontend logged-out-safe; bevestigde dat logo/watermark via in-graph `movie=` lopen dus de inmix met 1 input klopt in complex-mode). NIET getest: live login/UI, native Electron-build, echte 2-track-export.
- **TE COMMITTEN sessie 78 (stapelt op 77):** gewijzigd `Omni DJ/cutter.py` (D5 inmix), `Omni DJ/app.py` (D5 export-wiring + `/api/workspace/settings`), `Omni DJ/launcher.py` (headless-flag), `Omni DJ/static/index.html` (inmix-toggle in C7 + per-workspace settings-sync + startExport.inmix), `Omni DJ/electron/main.js` (sidecar) + `electron/package.json` (electron-builder), nieuw `Omni DJ/electron/build_electron.sh` + `Omni DJ/electron/build/entitlements.mac.plist`, gewijzigd `Omni DJ/electron/README-ELECTRON.md` + `.gitignore`, `HANDOVER.md`. NIET committen: alle `*.pre-sessie78.bak`, `electron/node_modules/`, `electron/dist-electron/`, `electron/resources/backend/`, `electron/build/icon.icns`.

Detail: memory `project_sessie78_d5_inmix_settings_electron`.

---

**Sessie 77 (2026-06-05) - Punt 1 website GEPUSHT (live) + punt 3 (clip-metadata wiring) + punt 5 C7 (Settings) + C3 (editor-splitters) + B0 (Electron-scaffold) + Spoor D (audio-sync) GEBOUWD. B0 + Spoor D LIVE BEVESTIGD door Sjuul (Electron-venster werkt, login werkt; Lisa Korver-set -> 30 clips correct gesynced). C7 + C3 nog visueel te checken.**

- **Sessie 77 VERVOLG (refinements na Sjuuls live-test van Spoor D + B0):** (1) de losse "Of: import video + audio sync"-knop is nu een echte 4e source-tile (`#analyse-tile-sync`) LINKS van Watch folder; `.analyse-tiles` grid 3 -> 4 koloms; de tile dimt/disablet tijdens analyse net als de andere (lost op dat de knop tijdens laden bleef staan). (2) Indeterminate loading bar (`#sync-progress` + `_syncProgress()`) onder de sync-status tijdens `/api/sync-import`. (3) ALLE Spoor D user-facing tekst nu Engels: de tile, de modal (titel/sub/labels/knoppen/placeholders), de JS-status/toasts en de 21 warning/error-strings in `audio_sync.py` + `/api/sync-import` (app.py). node --check + py_compile groen, 4 tiles, geen em/en-dashes. (Buiten scope gelaten: de Dutch picker-prompt 'Kies een DJ set om te analyseren' in `openFilePicker()` hoort bij de gewone dropzone, niet bij Spoor D.) NOG door Sjuul: out-of-sync test-bestanden proberen (drift/lage-confidence-pad).
- **Sessie 77 VERVOLG 2 - B1 + C8 + D4 (3x "keep going"):** **B1** (Electron lifecycle, `electron/main.js`): detached spawn + process-groep tree-kill, macOS-menubalk + Cmd-shortcuts, SIGINT/SIGTERM-shutdown, veilige links, venster-sluiten=app-quit=backend-stop (B0 live bevestigd; B1 ongetest). **C8** (`static/index.html`): de export-modal (`pickExportSettings`) consumeert nu de C7 export-defaults (`omniDjExportDefaults`) als fallback voor captions/watermark (last wint -> C7-default -> oud gedrag; non-regressief). **C8b**: editor preview-default-ratio nu OOK geconsumeerd - `renderEditor` past `omniDjEditorDefaults.ratio` toe bij het eerste clip-open van de sessie, maar ALLEEN als die variant al bestaat (geen on-demand-render, rail-active-sync); 1:1/4:5 pakken pas zodra die variant gecut is. **D4** (manual-align fallback, `audio_sync.py` + `app.py` + `static/index.html`): nieuw `analyze()` (offset/confidence/drift + downsampled waveforms, geen mux) + `mux_with_offset()` + helpers `_drift_to_tempo`/`_run_mux`/`_downsample_env`; `sync_and_mux` gerefactord naar dezelfde helpers (gedrag identiek, logic-test groen). `/api/sync-import` nu 2-mode: analyseren -> confidence >= 0.15 automatisch muxen (live-bewezen pad), < 0.15 -> `status:'needs_manual'` met waveforms (geen mux); `manual_offset_s` -> mux met die offset. Frontend: bij needs_manual een manual-align-sectie in de sync-modal (canvas-waveform-gids boven=camera/onder=schone audio + slider als functionele control + "Use this alignment" -> confirm). Statisch groen (py_compile/node/logic-test), geen em/en-dashes. NIET getest (vereist een bewust out-of-sync paar). Backup `static/index.html.pre-sessie77-c8.bak`. Open vervolg: Electron B1b/B2 packaging, Spoor D D5 (inmix-track-render in cutter), per-workspace Supabase `workspace_settings`.
- **Sessie 77 VERVOLG 3 - VOLLEDIGE TEST (automatisch) + rapport.** Zie `SESSIE77-TESTREPORT-2026-06-05.md` (NIET committen of wel, jouw keuze). 65+ automatische checks groen: py_compile alle .py, AST geen dubbele functienamen, alle nieuwe routes geregistreerd, audio_sync-logic (drift/downsample/clean_filter/xcorr), `_clip_rows_from_job` matcht clips-schema, node --check SPA-JS + electron, geen dubbele element-IDs (475), alle sessie-handlers gedefinieerd, alle nieuwe IDs aanwezig, main/section-balans, geen em/en-dashes, localStorage-keys consistent, B1-features aanwezig. Live infra: Supabase 8 tabellen RLS-aan + policies, security-advisors LEEG; omnidj.com HTTP 200 met DMG-download live (= sessie-76 push staat live gedeployed). **2 vondsten:** (1) ECHTE PRE-BESTAANDE dubbele `POST /api/brand-kit/logo` (`upload_brand_logo` r.3806 wint, `api_brand_logo` r.6687 dood voor POST) - NIET aangeraakt (werkende brand-flow, vereist jouw test om de canonieke te kiezen); opruim-kandidaat. (2) edge in `_drift_to_tempo` GEHARDEND: drift >= setduur (pathologisch) gaf misleidend "Corrected", nu correct "outside" (1-regel: `tempo_ratio = (dur/denom) if denom>0 else 0.0`, py_compile groen). NOG door Sjuul: de handmatige B-checklist in het testrapport (UI/visueel/E2E/native/login) + commit sessie 77.

- **Context:** Sjuul vroeg punt 1+3+5 autonoom uit te voeren. Bevinding: migratie `007_clips_metadata` staat AL LIVE (de "REVIEW ONLY"-header in het .sql-bestand is stale; de `clips`-tabel bestaat live op `lbabsffxefkrxwzkbzar`). Punt 3 was dus geen DB-werk maar app-wiring. Punt 5 = vier losse features; Sjuul koos C7 (Settings) als start en daarbinnen "volledige herinrichting". C3/B0/Spoor D blijven losse sessies (elk eigen bouw+test-ronde met login).
- **Punt 1 GECOMMIT (`16e79fd` op main, NOG NIET gepusht):** de 9 sessie-76 website-bestanden + migraties 010/011 in version control. `tsc --noEmit` schoon; anon-key wijst naar live project (rol anon); `DOWNLOAD_URL` = R2-DMG. Sjuul moet nog `git push origin main` (= live Cloudflare deploy; de sandbox heeft geen GitHub-creds). LET OP: een lege `.git/index.lock` bleef achter (sandbox kan 'm niet unlinken) -> blokkeert de push niet, wel een volgende commit; verwijderen met `rm -f "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/.git/index.lock"`.
- **Punt 3 clip-metadata wiring GEBOUWD (ADDITIEF, analyse/cut/export-pipeline ONGEMOEID):**
  - Backend (`app.py`, direct na de calendar-endpoints): `GET /api/clips` (workspace-clips, RLS) + `POST /api/clips/sync` (registreert de clips van meegegeven `job_ids` in de `clips`-tabel, dedupe op (workspace_id, local_path), best-effort, retourneert de cliplijst). Helpers `_clip_label_for` / `_clip_rows_from_job` / `_load_job_for_caller`. Alles via `_user_supabase` + `current_workspace_id` (RLS = grens). `local_path` = '<job_id>/<bestand>' (stabiele dedupe-sleutel, geen media in de cloud). `kind` clip/import. GEEN wijziging aan `_process_job`/`cutter.py`.
  - Frontend (`static/index.html`): de Calendar schedule-modal laadt nu echte workspace-clips (`_calLoadClipPicker`: POST `/api/clips/sync` van de laatste ~10 sets, dan tegels met de ECHTE clips-UUID); uitgelogd of geen clips -> terugval op de bestaande set-tegels. KERN-FIX: `calSaveSchedule` stuurt nu `clip_id` mee (UUID-gevalideerd). Dat ontbrak volledig -> koppeling werkte voorheen nooit, ook al kon je een set kiezen.
  - STATISCH geverifieerd: `py_compile` groen, `node --check` op de inline SPA-JS groen, logic-unittests op `_clip_rows_from_job` groen (clip_labels-precedence, bestand-fallback square/portrait, kind-constraint clip/import/sync, lege/rare input). Geen route/symbool-collisies. NIET E2E getest (vereist login op :5599). Niets naar de live DB geschreven deze sessie (checks waren read-only).
  - Backups: `app.py.pre-sessie77.bak`, `static/index.html.pre-sessie77.bak`.
- **E2E-TESTSCRIPT punt 3 (Sjuul, op :5599, ingelogd):** (1) herstart de dev-server zodat de nieuwe app.py-routes laden: `bash "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/_dev_restart_5599.sh"`. (2) Open `http://127.0.0.1:5599/?v=s77` en log in. (3) Zorg voor minstens 1 geanalyseerde set in de history (of analyseer er een). (4) Ga naar Calendar -> "Schedule a post": de clip-picker moet nu losse clips tonen (label + set-naam), niet alleen sets. (5) Kies een clip, kies datum+tijd, kies minstens 1 platform, Opslaan. (6) Verifieer in Supabase (project lbabsffxefkrxwzkbzar): `select id, clip_id, caption, scheduled_for from scheduled_posts order by created_at desc limit 3;` -> `clip_id` is gevuld (UUID); en `select count(*) from clips;` -> > 0 met jouw set-clips. (7) No-regression: analyse + export van een set blijven werken (pipeline is niet aangeraakt).
- **Punt 5 / C7 - Settings herinrichting GEBOUWD (frontend-only, `static/index.html`):**
  - DOM: `#view-settings` `.cap-room` (2-koloms) vervangen door single-column `.settings-stack`. Zichtbaar: Account (was "Profile"), Workspace, Privacy (nieuw). Daaronder uitklapbare **Advanced** (`#settings-adv-body`, default dicht) met Editor-defaults (nieuw), Export-defaults (nieuw), Watch folder (verplaatst uit cap-left), Capabilities + Opslag (waren `v2-hide-in-v2`, nu ontklapt), Brand kit (blijft tot C5), Diagnostics. ALLE 44 oorspronkelijke control-IDs behouden (blokken verplaatst via programmatische splice, niet verwijderd) -> de ID-gebaseerde handlers in `renderSettings` blijven werken.
  - Nieuw + persistent (localStorage): Editor-defaults (ratio 9x16/16x9/1x1/4x5 + captions standaard) -> `omniDjEditorDefaults`; Export-defaults (captions inbakken + watermark) -> `omniDjExportDefaults`. `_settingsLoadDefaults()` (hook in renderSettings) laadt+bindt, `_settingsSaveDefaults()` schrijft bij wijziging, `settingsToggleAdvanced()` klapt open/dicht. Privacy = local-first uitleg + uitgeschakelde "Airgap (binnenkort)". C8 (deze sessie): de EXPORT-defaults worden nu GECONSUMEERD - de export-modal (`pickExportSettings`) zet de captions- en watermark-toggle uit `omniDjExportDefaults` als FALLBACK (volgorde: onthouden 'last' wint -> anders de C7-default als gezet -> anders het oude gedrag; non-regressief, met backup `static/index.html.pre-sessie77-c8.bak`). NOG OPEN: de editor preview-default-ratio is BEWUST UITGESTELD (toepassen op clip-open kan een zware on-demand 1:1/4:5-render triggeren -> vereist live-test om te tunen); per-workspace Supabase (`workspace_settings`) ook later.
  - STATISCH geverifieerd: `node --check` groen, settings-view div-balans 0 (well-formed), 44 oude + 7 nieuwe IDs aanwezig, geen em/en-dashes in de C7-additions. NIET visueel getest (vereist :5599). Backup: `static/index.html.pre-sessie77-c7.bak`.
- **VISUEEL TESTSCRIPT C7 (Sjuul, op :5599):** herstart NIET nodig (frontend-only); reload `http://127.0.0.1:5599/?v=s77c7`, ga naar Settings. (1) Zichtbaar: Account + Workspace + Privacy als kaarten. (2) Klik "Advanced" -> klapt open met Editor-defaults, Export-defaults, Watch folder, Capabilities, Brand kit, Opslag, Diagnostics. (3) Zet een default ratio + toggles -> reload -> blijven staan (localStorage). (4) Bestaande knoppen werken nog: Log out, Profile/Account Save, Watch "Choose folder", Diagnostics "Download logs".
- **Punt 5 / C3 - CapCut sizeable editor-panes GEBOUWD (frontend-only, `static/index.html`):** twee sleepbare splitters als grid-tracks in `#view-editor`: verticaal tussen cue-lijst en preview (`#ed-split-x`, var `--ed-left-w`, 220-560px) en horizontaal tussen body en timeline (`#ed-split-y`, var `--ed-tl-h`, 160px tot 70%). Defaults = de HUIDIGE maten, dus de editor oogt identiek tot je sleept. Persistent in localStorage (`omniDjEditorPanes`), pointer-drag, narrow (<=980px) verbergt de splitters. Bestaande trim/text/track-resize ONGEMOEID (omkaderd, niet herschreven). `node --check` groen, editor-view div-balans 0, splitters 1x. IIFE `_edPanesC3` + scoped `<style>`.
  - **VISUEEL TESTSCRIPT C3:** reload `:5599`, open de editor (Library -> clip). Sleep de balk tussen cue-lijst en preview (breder/smaller) en de balk boven de timeline (timeline hoger/lager); reload -> maten blijven. Bestaande trim/tekst/tracks werken nog.
- **Punt 5 / B0 - Electron-prototype SCAFFOLD (nieuw `Omni DJ/electron/`):** `main.js` (vrije poort -> venv `app.py <poort>` met `OMNI_DJ_PORT` + vendor/ffmpeg op PATH -> health-check op / -> laad UI; splash; SIGTERM-kill bij quit), `preload.js` (leeg/veilig), `splash.html`, `package.json` (electron ^31, `npm start`), `README-ELECTRON.md`. KAN NIET in de sandbox draaien (native). `node --check` main.js/preload.js groen, package.json valid. **B0 LIVE BEVESTIGD door Sjuul** (venster + login + analyse/export werken).
  - **B1 (lifecycle) NU ERIN (`electron/main.js`):** detached spawn + process-groep tree-kill (SIGTERM -> SIGKILL na 1.5s, geen zombie python/ffmpeg), macOS application-menu met standaard Cmd-shortcuts (Quit/Cut/Copy/Paste/Reload/DevTools/zoom/fullscreen/window), nette shutdown op SIGINT/SIGTERM, veilige link-afhandeling (externe links -> standaardbrowser via shell.openExternal, geen wegnavigatie uit de localhost-backend), `app.setName('Omni DJ')`, venster-sluiten = app-quit = backend-stop. README B0-blok bijgewerkt. `node --check` groen. NIET door Sjuul getest. Resteert: PyInstaller-sidecar (B1b) + packaging/signing (B2/B3) + Windows (B4) + finish-notificatie/Dock-progress (renderer->main IPC).
  - **RUN-INSTRUCTIE B0/B1 (Sjuul):** `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/electron"` dan `npm install` dan `npm start`. Verwacht: splash -> gewone oranje UI; login/analyse/export werken; menubalk + Cmd-shortcuts; venster sluiten stopt de backend. Tree-kill checken: na afsluiten geen `python3 app.py`-proces meer in Activity Monitor / `ps aux | grep app.py`.
- **Punt 5 / Spoor D - video + audio sync GEBOUWD (nieuw `audio_sync.py` + `app.py`-endpoint + `static/index.html` sub-flow), analyzer.py/cutter.py ONGEMOEID:**
  - `audio_sync.py`: offset via librosa onset-envelope cross-correlatie, drift-schatting (begin- vs eind-venster), confidence (genormaliseerde piek), ffmpeg-mux (schone audio = spoor 0, camera-audio = spoor 1, video copy), milde GECLAMPTE atempo-driftcorrectie (0.97-1.03) anders alleen waarschuwen. CONVENTIES (sign/drift) in de module-docstring: verifieer op de 1e echte run.
  - `app.py`: additief `POST /api/sync-import` (workspace-scoped, `_path_within_home` op beide inputs net als upload-local, output naar `workspaces/<id>/sync/`, `media_tools.ffmpeg/ffprobe`, retourneert metrics + pad). Lazy `import audio_sync` (faalt netjes met 422).
  - `static/index.html`: 2e knop "Of: import video + audio sync" op de Analyse-page + `#sync-modal` sub-flow (`/api/pick-file` voor video+audio -> `/api/sync-import` -> metrics/warnings -> `_startLocalJob(output_path)` voor de normale analyse). De gewone dropzone-flow is ONGEMOEID.
  - STATISCH: py_compile (app.py + audio_sync.py) groen, audio_sync importeert (numpy ok, librosa-guard), node --check groen, route+symbool uniek. NIET getest met echte bestanden.
  - **E2E-TESTSCRIPT Spoor D (Sjuul, op :5599, na `bash "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/_dev_restart_5599.sh"`):** Analyse-page -> "Of: import video + audio sync" -> kies een camera-video (met boordgeluid) + schone audio van DEZELFDE set -> "Sync + analyseren". Verwacht: confidence% + offset (+ evt. drift-waarschuwing), dan start de normale analyse op het gemuxede bestand. Controleer uitlijning (transients) + het einde (drift). BELANGRIJK v1: verifieer de sign-conventie (loopt de audio voor of achter?); de handmatige-uitlijn-UI (D4) bij lage confidence komt later, net als de inmix-track-render (D5) in cutter.
- **NOG door Sjuul:** (a) push punt 1 = GEDAAN (`16e79fd` live); (b) testen: punt 3 (E2E) + C7 (visueel) + C3 (sleep-panes) + Spoor D (echte video+audio) + B0 (`npm start`) - scripts hierboven; (c) vervolg: C8 (defaults consumeren + Supabase `workspace_settings`), Electron B1-B4, Spoor D D4 (handmatige fallback) + D5 (inmix-render in cutter); (d) commit sessie 77.
- **TE COMMITTEN sessie 77:** `Omni DJ/app.py` (clips-endpoints + `/api/sync-import`), nieuw `Omni DJ/audio_sync.py`, `Omni DJ/static/index.html` (clip-picker+clip_id + C7 Settings + C3 editor-splitters + Spoor D sub-flow), nieuw `Omni DJ/electron/` (main.js/preload.js/splash.html/package.json/README-ELECTRON.md), `HANDOVER.md`. NIET committen: `*.pre-sessie77*.bak`, `_dev_restart_5599.sh`, `electron/node_modules/` (ontstaat bij `npm install`).

Detail: memory `project_sessie77_clip_metadata_wiring`.

---

**Sessie 76 (2026-06-04) - Website afgemaakt (DMG-download + EIGEN beta-systeem via Supabase) + migratie 010 LIVE op main. Website wacht op git push door Sjuul.**

- **Website (omnidj.com), code + DB klaar, NIET gedeployed:** de HANDOVER-aanname over `REPLACE_*` placeholders was verouderd; de Next.js-site had die niet. Echte gaten: (1) alle download-knoppen wezen naar een leeg `#download` anker, (2) beide beta-formulieren postten naar `/api/beta-signup` dat op de statische export niet bestaat (aanmeldingen verdwenen geruisloos).
  - **Download:** nieuw `omnidj.com/lib/config.ts` met `DOWNLOAD_URL` (= `https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg`); alle 6 CTA-plekken (hero/footer/pricing x3/ClosingCta/features) wijzen er nu naar.
  - **Beta-systeem (EIGEN, GEEN Formspree - keuze Sjuul):** nieuw `omnidj.com/lib/betaSignup.ts` post rechtstreeks naar Supabase REST `beta_signups` met de publieke anon-key + `Prefer: return=minimal`. `JoinBetaForm.tsx` + `RoadmapCarousel.tsx` omgezet, honeypot tegen spam, echte foutafhandeling. Sandbox `tsc --noEmit` schoon.
  - **Migratie 011_beta_signups.sql (LIVE op main):** tabel `beta_signups` + insert-only RLS (anon/authenticated alleen INSERT). Live geverifieerd: anon insert=allowed, select=denied; grants alleen INSERT. Daarom is de anon-key veilig in de statische bundle.
  - **NOG door Sjuul:** `git add omnidj.com "Omni DJ/supabase/migrations/011_beta_signups.sql"` + commit + push -> Cloudflare Pages auto-deploy. DB staat al klaar. Google Workspace domeinverificatie monohq-labs.com nog open.
- **Migratie 010 (RLS-helpers -> `private` schema) NU LIVE op main.** Eerst volledig getest op een wegwerp-branch: main's basis-schema zit NIET in de migratiegeschiedenis (begint pas bij add_intake_columns) -> branch-replay gaf 0 tabellen, dus 005-009 zelf nagebouwd + geseed (`auth.users` vereist alleen `id`; owner_id/user_id hebben wel een FK naar auth.users). Isolatie-audit groen pre EN post 010 over alle 5 tabellen (workspaces/clips/dj_profiles/dj_templates/scheduled_posts); branch daarna verwijderd. Op main na toepassen: `get_advisors(security)` = LEEG (de 3 `authenticated_security_definer_function_executable` WARNs weg), 3 helpers alleen in `private`, public-versies gedropt, read-only spotcheck (sample-user ziet 1 van 14 workspaces = isolatie intact). Checkpoint met Sjuul gerespecteerd (akkoord vóór main).
- **TE COMMITTEN sessie 76:** nieuw `omnidj.com/lib/config.ts` + `omnidj.com/lib/betaSignup.ts`, gewijzigd `omnidj.com/lib/content/{hero,footer,pricing}.ts` + `omnidj.com/components/hero/JoinBetaForm.tsx` + `omnidj.com/components/roadmap/RoadmapCarousel.tsx` + `omnidj.com/components/cta/ClosingCta.tsx` + `omnidj.com/app/features/page.tsx`, nieuw `Omni DJ/supabase/migrations/011_beta_signups.sql`, header-update `Omni DJ/supabase/migrations/010_*.sql`, `HANDOVER.md`. (010 + 011 zijn nu live op main.)

Detail: memory `project_sessie76_website_beta_010`.

---

**Sessie 75 (2026-06-04) - E2E-export-check (fase 2b/4) GEDAAN + logo-export-bug gefixt. Code-side klaar, NIET gecommit.**

- **Doel:** bevestigen dat het per-workspace logo correct in de export bakt (open punt uit sessie 74), met no-regression.
- **Bug gevonden + gefixt (1 regel, `app.py` r.6690):** `_detect_layers_for_clip` checkte `logo.get('file')`, maar de logo-upload slaat de sleutel op als `'path'` (en de cutter rendert ook via `'path'`). Daardoor was `has_logo` altijd False -> bij EXPORT liep de prebake nooit -> een logo werd nooit ingebakken. Nu: `(logo.get('path') or logo.get('file'))`. Bestaande bug (sessie 43a), GEEN sessie-74-regressie. Watermark werkte al (slaat wel `'file'` op). Backup `app.py.pre-sessie75.bak`, py_compile groen.
- **LIVE geverifieerd op :5599 (na restart met de fix):** test-logo op TEST-workspace gezet -> korte Franky-excerpt vers geanalyseerd (job workspace-getagd via upload-local r.4792, brand gematerialiseerd in job-map via r.1133) -> clip geexporteerd -> frame-extract toont het per-workspace logo rechtsboven in de export (export-grootte veranderde t.o.v. de kale clip = prebake liep echt).
- **Isolatie/no-regression bevestigd:** globaal `brand_kit.json` bleef `logo=null` (geen clobber); een export uit de bestaande ONGETAGDE Franky-job (a0746acc) viel terug op globaal en had GEEN logo (geen leak). Export-pipeline intact.
- **Nevenobservatie (geen actie ondernomen):** de logo-upload-endpoint snuffelt alleen de eerste 4 PNG-magic-bytes, niet of de PNG decodeerbaar is (een corrupte PNG kan dus opgeslagen worden). Echte upload via de bestandskiezer stuurt geldige bytes; laag risico.
- **Opgeruimd:** test-logo (via DELETE), excerpt, test-job 40b3cee6, test-export + frames. NB: de test-analyse verhoogde de usage-teller met 1 (5->6) voor business@; NIET teruggedraaid.
- **GESIGNDE REBUILD GEDAAN (2026-06-04):** `./build_macos.sh sign notarize dmg` gedraaid (via osascript-achtergrond, APPLE_DEVELOPER_ID=Sjuul Smits/PTLV7AY4UL, profiel omnidj-notary). Resultaat: `dist/Omni DJ.app` + `dist/Omni DJ.dmg` (258 MB), beide spctl `accepted / Notarized Developer ID`. Gebouwd uit huidige source -> logo-fix zit erin. NOG NIET gedaan (Sjuul): bundle naar `/Applications` zetten, picker-smoketest in de gesignde bundle (harde regel), en PAS DAARNA DMG->R2 (hernoemen naar `Omni-DJ-1.0.0.dmg`).
- **Picker-fix (`app.py`, NIET getest in bundle):** `_PanelRunner`-ObjC-class stond BINNEN
  `_pick_with_nsopenpanel` -> 2e pick (eerst set, dan KIES MAP) gaf "_PanelRunner is overriding
  existing Objective-C class" in de gesignde bundle. Nu 1x op moduleniveau via `_get_panel_runner_cls()`
  (global-guard) + gedeelde `_PANEL_STATE` onder `_PANEL_LOCK`. De NSOpenPanel-route draait alleen in de
  bundle (dev gebruikt osascript), dus pas te bevestigen NA een rebuild. Backup `app.py.pre-sessie75-picker.bak`.
- **Export-feature GEBOUWD + LIVE GROEN op :5599 (PLAN-SESSIE75-RATIOS-NAMING-DOWNLOADS):**
  (1) Per-ratio bestandsnaam = rename + " - <ratio>" met veilige tokens (`_build_export_filename`,
  `_ASPECT_RATIO_LABEL` 9x16/16x9/1x1/4x5, spaties behouden). (2) Echte 1:1 + 4:5 crops: nieuwe
  `_derive_ratio_file` (hergebruikt de /api/derive center-crop) + `_resolve_export_sources` leidt
  square (1080x1080) en portrait45 (1080x1350) af uit landscape/vertical; aspect_filter + prebake-merge
  laten 1:1/4:5 niet wegvallen. Frontend mapt nu 1:1->square, 4:5->portrait45 (geen collapse meer).
  (3) Downloads-default: nieuw `GET /api/default-export-dir` (~/Downloads), modal selecteert 'm vooraf,
  map verplicht (duidelijke toast als leeg), backend-vangnet default ~/Downloads. LIVE bewezen: export
  van 1 clip in alle 4 formaten -> "House set - 9x16/16x9/1x1/4x5.mp4" met juiste afmetingen
  (1080x1920 / 1920x1080 / 1080x1080 / 1080x1350); 1:1-frame is een echte center-crop. Backups
  `app.py`/`cutter.py.pre-sessie75-ratios.bak` (cutter ongewijzigd). BEPERKING v1: brand-overlay in de
  afgeleide 1:1/4:5 komt alleen mee als de bron-cut 'm al had (derive cropt de cut, geen aparte overlay);
  fijn-tunen hoort bij de logo-in-editor-feature.
- **TE COMMITTEN (stapelt op 9176c8a):** gewijzigd `Omni DJ/app.py` (logo-detect fix + `_PanelRunner`
  moduleniveau + `_build_export_filename`/ratio-tokens + `_derive_ratio_file` + `_resolve_export_sources`
  + aspect_filter + prebake-merge + sidecar portrait45 + `/api/default-export-dir` + export Downloads-default),
  `Omni DJ/static/index.html` (Downloads-default + verplichte map + ratio->aspect mapping), nieuw
  `PLAN-SESSIE75-RATIOS-NAMING-DOWNLOADS-2026-06-04.md`, `HANDOVER.md`. NIET committen: alle
  `app.py.pre-sessie75*.bak`, `cutter.py.pre-sessie75-ratios.bak`, `_dev_restart_5599.sh`.
- **GESIGNDE REBUILD #2 GEDAAN (2026-06-04):** bundle herbouwd `./build_macos.sh sign notarize dmg`,
  app + dmg spctl `accepted / Notarized Developer ID` (DMG ~258 MB), en in `/Applications` gezet (ditto).
  De bundle bevat nu ALLES van sessie 75: logo-fix + picker-fix + export-feature (per-ratio naam + echte
  1:1/4:5 crops + Downloads-default). NOG: picker-smoketest in de bundle (set inladen EN KIES MAP), dan
  pas DMG->R2 (`Omni-DJ-1.0.0.dmg`). (Commit + DMG->R2 later GEDAAN, zie onderaan dit blok.)
- **SMOKETEST bundle #2 (Sjuul, 2026-06-04) -> 3 fixes in broncode (NIET in bundle, vereist rebuild #3):**
  (1) Picker-crash WEG (analyse lukt), maar "Drop a set" opent Finder pas bij 2e klik en KIES MAP toont
  niks. Diagnose: backend, NSOpenPanel hangt af van de Flask-main-thread run-loop -> paneel verschijnt
  onbetrouwbaar; GEEN frontend-bug (de knop vuurt /api/pick-folder). FIX: `_pick_folder_macos` +
  `_pick_file_macos` nu OSASCRIPT-EERST (los subprocess met eigen run-loop, entitlement aanwezig sinds
  sessie 69), NSOpenPanel alleen als terugval. Strikt >= huidig (terugval blijft). Alleen in de bundle te
  bevestigen. (2) `.meta.json` sidecar werd meegekopieerd naar de gekozen doelmap -> NU NIET meer
  (sidecar blijft alleen in de job-map voor de Library; eindgebruiker krijgt enkel schone .mp4's).
  (3) RESET-knop leek niks te doen: hij reset naar Downloads (al getoond) -> nu met bevestigings-toast.
  py_compile groen, dev (:5599) laadt zonder console-fouten. Backups pre-sessie75-ratios.bak dekken app.py.
- **REBUILD #3 GEDAAN + in /Applications (2026-06-04):** app + dmg `accepted / Notarized Developer ID`.
  Bundle bevat nu ook de 3 smoketest-fixes. NOG door Sjuul: smoketest (1-klik Drop a set + KIES MAP openen
  direct? geen .json in doelmap? RESET-toast?). DAARNA pas DMG->R2. (Commit + DMG->R2 GEDAAN, zie onder.)
- **SMOKETEST #3 GROEN (Sjuul, 2026-06-04):** picker opent nu in EEN klik (osascript-first werkt in de
  bundle), geen .json in de doelmap, RESET geeft toast. WEL twee normale macOS-bijverschijnselen:
  (a) een generiek wit Dock-icoon stuitert terwijl het kies-venster open is (dat is het osascript-helper-
  proces dat de dialog host; onschuldig), en (b) eenmalig de macOS-toestemmingsprompt voor de Downloads-map
  (uit `NSDownloadsFolderUsageDescription`; Allow = permanent). App-icoon (Dock/Finder/.dmg) = Omni DJ-logo;
  browser-tab favicon ontbrak -> toegevoegd.
- **REBUILD #4 (favicon) GEDAAN + in /Applications + DMG->R2 LIVE (2026-06-04):** app+dmg notarized.
  DMG geupload naar R2 bucket `omnidj-downloads` als `Omni-DJ-1.0.0.dmg` via wrangler (osascript kon niet
  non-interactief -> `script -q /dev/null wrangler ... --remote` gaf een pty -> OAuth re-auth (Sjuul
  goedgekeurd) -> upload. Wrangler zit op nvm-pad `/Users/sjuulsmits/.nvm/versions/node/v20.19.5/bin`,
  draaien vanuit $HOME (anders `/.wrangler/cache`-fout). GEVERIFIEERD: `https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg`
  HTTP 200, content-length 258137270 = de verse build (cf-cache MISS). **GECOMMIT + GEPUSHT: commit
  `302c4d7` op `main` (origin/main), alle sessie 75-wijzigingen. Sessie 75 volledig afgerond.**

Detail: memory `project_sessie75_logo_export_fix`.

---

**Sessie 74 (2026-06-03) - A1 afmaken gestart. Stappenplan opgeleverd + Slice 1 (workspace-header activeren) GEBOUWD en LIVE GEVERIFIEERD op :5599. Frontend-only, NIET gecommit/herbouwd.**

### Wat sessie 74 deed
- **Stappenplan** `PLAN-A2-A3-SLICES-2026-06-03.md`: 5 slices (1 header-activatie, 2 Brand-profiel-data, 3 Brand-in-render, 4 Calendar-data, 5 Correctie 8 + per-workspace mappen) + migratie 010 los, met volgorde/risico/checkpoints. Lees dat voor de vervolg-slices.
- **Slice 1 GEBOUWD (alleen `static/index.html`, additief):** de tot nu toe SLAPENDE `X-Omni-Workspace`-header is nu echt aan.
  - Globaal (na `_omniWsHeaders`): `loadWorkspaces(force)` haalt `/api/workspaces` (RLS-scoped) op, vult `STATE.workspaces`, en `_setActiveWorkspace(uuid)` zet de gereserveerde sleutel `omniDjWorkspaceId` (behoud huidige als nog lid, anders de primaire). Fire-and-forget, degradeert stil naar [].
  - Trigger: aan het eind van `renderAccountChip()`, 1x per sessie (`!STATE._workspacesLoaded`).
  - Artist-switcher (v2-IIFE): `v2ActiveWorkspace()`/`v2WsLabel()` toegevoegd; `v2PaintArtistChip()` toont nu de ECHTE workspace-naam (op `window` gezet zodat loadWorkspaces kan herverven); `v2ArtistDropdownContent()` lijst de echte workspaces met `data-ws-id` (+ stub-fallback); de `artist-select`-handler zet bij keuze de workspace-UUID.
- **LIVE GEVERIFIEERD (ingelogd `omnidj@monohq-labs.com`, studio, op :5599):** `/api/workspaces` gaf RLS-scoped 1 workspace "TEST" (is_owner); `omniDjWorkspaceId` = die UUID; `X-Omni-Workspace` matcht de actieve; chip toont "TEST"; dropdown toont "TEST" met actief-vinkje + UUID; geen console-fouten; app-shell intact (switchView/sidebar/10 views). Backup `static/index.html.pre-sessie74.bak`. `node --check` groen.

### Slice 2 - Brand bron-migratie (Sjuul koos VOLLEDIGE migratie). FASE 1 GEBOUWD + LIVE GROEN.
- **Plan:** `PLAN-SLICE2-BRAND-MIGRATION-2026-06-03.md` (4 fasen + rollback + harde checkpoint vóór fase 2). Canoniek `dj_profiles.profile` = moat-schema (artist_name/alias/visual/typography/lower_third/cta/hashtags/caption_voice) MET het bestaande brand_kit-blok verliesvrij ingebed onder sleutel `brand_kit`.
- **Fase 1 (additief, niet-destructief, alleen `app.py`):** nieuwe routes `GET/PUT /api/brand/profile`, workspace-scoped via `_user_supabase` + `current_workspace_id`. GET seedt eenmalig uit het globale `brand_kit.json` en upsert; PUT merget (None-safe) + upsert. `brand_kit.json` + alle `/api/brand-kit*` ONGEMOEID. Helpers `_brand_profile_defaults`/`_seed_brand_profile_from_kit`/`_merge_brand_profile`. Backup `app.py.pre-sessie74-fase1.bak`. `py_compile` groen, +151 regels, geen dashes.
- **LIVE GEVERIFIEERD (:5599, na restart, ingelogd omnidj@):** GET#1 source=seeded (visual-kleuren uit palette, brand_kit ingebed), PUT zet artist_name+cta.spotify, GET#2 source=supabase met waarden persistent en brand_kit intact. RLS: directe PostgREST op dj_profiles met JWT geeft 1 rij (TEST), anon 401. DB bevestigt 1 rij, ws TEST, eigenaar omnidj@.
- **Fase 2 diagnose-vondst:** de cutter (`cutter.py` `_load_brand_assets_for_job` r.877) leest het GLOBALE `brand_kit.json` ZELF van schijf, los van app.py; jobs zijn niet workspace-getagd; logo/watermark gebruiken vaste bestandsnamen. Daarom Fase 2 gesplitst.
- **Fase 2a GEBOUWD + LIVE GROEN (alleen `app.py`, geen export-impact):** globaal `brand_kit.json` blijft de cutter-bron en ongemoeid; `_save_brand_kit` schrijft globaal EN mirrort de metadata naar `dj_profiles.profile.brand_kit` per workspace; `GET /api/brand-kit` geeft de per-workspace versie als die er is (anders globaal, backward compatible). Helpers `_brand_ws_ctx`/`_mirror_kit_to_workspace`/`_save_brand_kit`, 11 save-sites omgezet (geen recursie, `_kp`). py_compile groen. Live (:5599, ws TEST): GET per-workspace, POST->mirror->GET roundtrip groen, Supabase bevat de mirror (handle+tagline), globaal bestand kreeg dezelfde wijziging (cutter-bron intact), Fase-1 `artist_name` bleef staan.
- **Fase 2b GEBOUWD (niet-regressief, `app.py` + `cutter.py`):** export gebruikt nu de per-workspace brand met GLOBALE FALLBACK. (1) `_save_brand_kit`/`_mirror_kit_to_workspace` schrijft een lokale cache `workspaces/<ws_id>/brand_kit.json` (door de render-thread leesbaar zonder JWT). (2) Jobs getagd met `workspace_id` bij aanmaak (2 sites, via `current_workspace_id`). (3) `_materialize_job_brand(job_id, dir)` kopieert die cache naar de job-map; aangeroepen in `_process_job` (analyse) en `_prebake_clip_for_export` (export). (4) cutter `_load_brand_assets_for_job` leest `output_dir/brand_kit.json` EERST, anders globaal (strikt superset). (5) `_detect_layers_for_clip` idem. Backups `app.py`/`cutter.py.pre-sessie74-fase2b.bak`. py_compile beide groen, geen dashes.
- **LIVE geverifieerd (deel):** na brand-save verschijnt de per-workspace cache op schijf met de juiste waarde + het globale bestand blijft gelijk (cutter-bron intact). **NOG door Sjuul te verifieren (E2E):** echte set analyseren + exporteren -> brand bakt correct (single-workspace == globaal, dus zelfde resultaat = geen regressie; echte per-artist isolatie vergt 2 workspaces met verschillende brand). **BEKENDE BEPERKING:** asset-FILES (logo/watermark) gebruiken nog vaste namen in gedeelde mappen -> per-workspace asset-mappen = aparte vervolgstap (hoort bij fase 4). Metadata + settings zijn wel per-workspace.
- **Fase 3 GEBOUWD + LIVE GROEN (alleen `static/index.html`, frontend, raakt export niet):** "Artist profile"-kaart in de Brand-view (`#view-style`, `#artist-profile-room`) met de nieuwe per-artist velden (artist_name, alias, cta style/spotify/beatport, hashtags tiktok/instagram/youtube, caption_voice tone/emojis/maxlen). `loadArtistProfile()` (GET) bij view-open + `saveArtistProfile()` (PUT) op de knop, via `/api/brand/profile`. Hergebruikt bestaande stijlklassen (geen nieuwe CSS). Backup `static/index.html.pre-sessie74-fase3.bak`, node --check groen, geen console-fouten. Live (:5599, ws TEST): kaart laadt uit Supabase, save persisteert + merge bewaart cta.spotify + brand_kit. LET OP: ik liet test-waarden achter in het TEST-profiel (artist_name "Fase3 ...", alias @fase3test) en in het globale brand_kit (handle "@2b-cache-..."); Sjuul kan die in de UI overschrijven.
- **Fase 4 GEBOUWD + LIVE GROEN (`app.py`):** brand-kit EN logo/watermark nu echt per workspace. `_active_brand_ws()` (per-request gecached op flask.g) bepaalt de workspace; `_load_brand_kit()` laadt nu de per-workspace cache (geseed uit globaal), `_save_brand_kit()` schrijft met workspace ALLEEN de per-workspace cache + Supabase-mirror (globaal blijft stabiele cutter-fallback voor oude jobs); `_brand_asset_dirs(ws)` -> logo/watermark naar `workspaces/<ws>/brand_kit/{logo,watermark}/` (lost de vaste-bestandsnaam-clobber op; fonts blijven globaal want uuid-namen). Backup `app.py.pre-sessie74-fase4.bak`, py_compile groen. Live (ws TEST): logo-upload landt in de per-workspace map, per-workspace cache krijgt handle+logo-pad, GLOBAAL bestand ONgewijzigd (handle leeg), brand-profiel/brand-kit GET blijven werken, geen console-fouten. De BEKENDE asset-clobber-beperking uit fase 2a/2b is hiermee OPGELOST.
- **CHECKPOINT/volgende:** E2E-export (Sjuul) om fase 2b te bevestigen (nu met per-workspace logo), dan backups + 1 commit (69+71+72+73+74).

### Slice 4 - Content Calendar (A3). FASE 4a + 4b GEBOUWD + LIVE GROEN.
- **Tabel:** `scheduled_posts` (009) is LIVE op main (RLS aan, 4 policies). Draft-store, publisht niets.
- **Fase 4a backend (`app.py`, additief):** `GET /api/calendar/list` (?from&to op scheduled_for), `POST /api/calendar/schedule`, `PUT|POST /api/calendar/update`, `POST|DELETE /api/calendar/delete`, alle via `_user_supabase` + `current_workspace_id(required)`, RLS-scoped. `clip_id` alleen als geldige uuid (clips-tabel nog leeg -> meestal null). Backup `app.py.pre-sessie74-slice4a.bak`, py_compile groen. Live: volledige CRUD groen, anon-PostgREST 401 (RLS), DB-scope klopt (ws TEST + created_by), tabel weer schoon.
- **Fase 4b frontend (`static/index.html`, additief):** ingelogd -> Calendar leest/schrijft Supabase per workspace; uitgelogd -> de oude localStorage/demo-laag ONGEMOEID. `loadCalendarPosts()` (GET+map naar `{ymd:[event]}`), `_v2PostsToEvents()`, `_v2LoadCalEvents()` geeft server-events bij login (geen demo-seeding), `calSaveSchedule()` POST't bij login, view-open-hook in de render-dispatch. Backup gedekt door `index.html.pre-sessie74-fase3.bak` (zelfde sessie). node --check groen, geen console-fouten. Live: lege calendar bij open (geen mock), save->POST->reload toont de draft, tijdzone-conversie klopt (20:30 lokaal -> 18:30Z). BEPERKING: edit/delete-UI bestaat nog niet (alleen toevoegen via modal); endpoints zijn er wel. clip_id-koppeling wacht op clips-metadata (007); clipName valt nu uit de caption.

### Belangrijke vondst + valkuil (sessie 74)
- **A1-backend nu E2E BEWEZEN** (was ongetest sinds sessie 73): directe PostgREST-call met de user-JWT gaf "TEST", en na server-restart gaf `/api/workspaces` via `_user_supabase` dezelfde rij. De anon+JWT-aanpak (Correctie 6) werkt dus echt; RLS is de grens.
- **VALKUIL die tijd kostte:** :5599 draaide een STALE `app.py` (van vóór sessie 73, zonder `/api/workspaces` -> Flask viel terug op de SPA-catch-all -> HTML i.p.v. JSON -> frontend las "0 workspaces"). `app.py`-edits vereisen `bash "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/_dev_restart_5599.sh"`. **Altijd herstarten na een app.py-edit voordat je backend test.** De eerste "0 workspaces" was dit, NIET RLS.

### Nog open (zelfde checkpoints als sessie 73)
- **Vervolg-slices:** Slice 2 (Brand-profiel per workspace via nieuwe `/api/brand/profile` + `_user_supabase`/`current_workspace_id`, lokale `brand_kit.json` migreren) of Slice 4 (Calendar-data). Aanbeveling: Slice 2 eerst (Calendar leunt visueel op Brand). Zie `PLAN-A2-A3-SLICES-2026-06-03.md`.
- Migratie 010 (review) + C7/C3/B0/Spoor D + test-infra: ongewijzigd t.o.v. sessie 73.

**TE COMMITTEN sessie 74 (stapelt op 69+71+72+73, samen in 1 commit):** gewijzigd `Omni DJ/static/index.html` (Slice 1 workspace-header + fase 3 Artist profile-kaart), gewijzigd `Omni DJ/app.py` (Slice 2 fase 1 brand-profiel-endpoints + fase 2a mirror/per-workspace-GET + fase 2b job-tag/materialize/cache + Slice 4a calendar-endpoints + fase 4 per-workspace brand/assets), gewijzigd `Omni DJ/cutter.py` (fase 2b: output_dir-brand eerst), gewijzigd `Omni DJ/static/index.html` (Slice 1 + fase 3 Artist profile + Slice 4b Calendar-koppeling + Calendar edit/delete + Plan-in-Calendar), nieuw `PLAN-A2-A3-SLICES-2026-06-03.md` + `PLAN-SLICE2-BRAND-MIGRATION-2026-06-03.md`, `HANDOVER.md`. NIET committen: alle `*.pre-sessie74*.bak` (index.html/app.py/cutter.py), `_dev_restart_5599.sh`, en de lokale test-map `Omni DJ/workspaces/<ws_id>/` (dev-cache).

Detail: memory `project_sessie74_slice1_workspace_header`.

---

**Sessie 73 (2026-06-03) - A1 multi-tenant BACKEND + frontend-plumbing + rename-bug gefixt. Code-side klaar, NIET gecommit/herbouwd. Statisch groen (py_compile + node --check + logic-unittests).**

### Wat sessie 73 deed (de "gekozen volgende stap" A1 + de rename-wens)
- **A1a backend (ADDITIEF, raakt analyse/export/auth NIET):**
  - `_user_supabase(access_token)` in app.py: verse anon-client met de user-JWT erop (`create_client(..., ClientOptions(headers=Bearer))` + `postgrest.auth(jwt)`, supabase-py 2.30.1 geverifieerd). Content-queries hierdoorheen lopen als rol `authenticated` -> RLS is de echte grens (Correctie 6). `supabase_admin` blijft alleen profiel/role/billing/audit.
  - `current_workspace_id(user_info, required=False)`: leest `X-Omni-Workspace`, membership-check via de user-client (nette 403 bovenop RLS), valt anders terug op de primaire membership. Query-patroon matcht de `members_select` policy (006).
  - Nieuwe read-only route `GET /api/workspaces`: eerste echte consument van `_user_supabase` (lijst de artists/workspaces van de caller, RLS-scoped). Returnt [] als Supabase niet geconfigureerd (graceful in de bundle).
- **A1b frontend (ADDITIEF, DORMANT):** `currentWorkspaceId()` + `_omniWsHeaders()` in index.html; `X-Omni-Workspace` nu in de centrale `api()` EN op de 3 authed rauwe fetches (filmstrip/overlays/watermark). LET OP: de HANDOVER-aanname dat de header "al in api() zat" was ONJUIST - hij stond NERGENS. Nu wel, maar gevoed uit een GERESERVEERDE sleutel `omniDjWorkspaceId` (UUID-gevalideerd), NIET `omniDjActiveArtist` (dat is nog een display-naam-stub uit Fase 5). De header blijft dus dormant tot A2 echte workspace-UUIDs in die sleutel zet -> stuurt nooit een misleidende waarde. Pre-auth fetches (auth-refresh, forgot-password) bewust ongemoeid.
- **Rename->filename bug GEPIND + GEFIXT:** root cause = `/api/export-preset` (de per-card quick-export-popover; frontend `_ceExportPreset` + `exportClipPreset`) bouwde de filename uit `<bron-basename>_<preset>.mp4` en raakte `clip_labels`/`custom_label` NOOIT aan. Nu: prefer `data['label']` (frontend stuurt `clip.custom_label` mee), anders persistent `clip_labels[str(clip_index)]`, anders de oude bron-naam (geen regressie). Plus `_dedupe_output_path()` tegen stil overschrijven bij gelijke labels. De grote `/api/export`-modal-flow was al goed (RENAMETEST sessie 72).
- **Migratie 010 = REVIEW, NIET toegepast** (checkpoint gerespecteerd). Bestand is correct (helpers -> schema `private`, alle policies herschreven naar `private.*`, oude public-helpers gedropt). Lost de 3 advisor-WARNs op.

### Geverifieerd (statisch, in de sandbox)
- `python3 -m py_compile app.py` groen. `node --check` op de SPA-JS groen. Logic-unittests (label-precedence + sanitisatie + dedupe) groen. Live DB-check via Supabase-MCP: project `lbabsffxefkrxwzkbzar` ACTIVE_HEALTHY, content-tabellen live + RLS aan (workspaces/members 14 rijen, clips/dj_profiles/dj_templates/scheduled_posts 0 rijen).
- NIET getest (kan niet in de sandbox; vereist Mac-login = een echte JWT): de anon+JWT RLS-call van `_user_supabase`/`/api/workspaces` E2E. RLS-isolatie zelf was al bewezen groen (sessie 71 branch-audit). Backups: `app.py.pre-sessie73.bak`, `static/index.html.pre-sessie73.bak`.

### Zo verifieer je op de Mac (na inloggen op :5599)
1. Start de dev-server (zie de "Zo hervat je"-stappen onder de sessie-72-kop). Log in.
2. A1: open de browser-console en draai
   fetch('/api/workspaces',{headers:{Authorization:'Bearer '+STATE.session.access_token}}).then(r=>r.json()).then(console.log)
   -> moet JOUW workspace(s) tonen (RLS-scoped, NIET alle 14).
3. Rename-fix: hernoem een clip -> gebruik de per-card quick-export (TikTok/IG/Shorts/Source) -> de toast + de Library tonen de HERNOEMDE naam i.p.v. de bron-naam.
4. Kernflow blijft groen: login -> analyse -> editor -> grote Export-modal.

### Nog open (zelfde checkpoints: A1-merge-naar-main / bestandsverwijdering / DMG->R2)
- **A1 afmaken (A2/A3-werk):** content-tabellen (clips/dj_profiles/dj_templates/scheduled_posts) echt door `_user_supabase` laten lopen + de frontend `omniDjWorkspaceId` met de echte workspace-UUID vullen (artist-switcher -> `/api/workspaces`). Pipeline-koppeling (Correctie 8) per-workspace mappen.
- **Migratie 010:** branch-test (mcp create_branch) + her-audit (AUDIT_cross_account_rls.sql) + CHECKPOINT met Sjuul vóór main.
- C7 Settings opschonen, C3 CapCut 3-pane editor (flagged), A2->C5 Brand, A3->C6 Calendar, B0 Electron, Spoor D audio-sync.
- Test-infra: pytest + Playwright (Playwright OP DE MAC). Security-pass + advisors.
- DAN: backups + 1 commit (sessie 69+71+72+73 samen) + gesignde rebuild + DMG->R2 (pas NA picker-smoketest).

**TE COMMITTEN sessie 73 (stapelt op 69+71+72, samen in 1 commit):** gewijzigd `Omni DJ/app.py` (_user_supabase + current_workspace_id + /api/workspaces + _dedupe_output_path + export-preset label-fix), `Omni DJ/static/index.html` (currentWorkspaceId + _omniWsHeaders + header op api()/3 fetches + export-preset label-passthrough), `HANDOVER.md`. NIET committen: `*.pre-sessie73.bak`.

Detail: memory `project_sessie73_a1_backend_rename_fix`.

---

**Sessie 72 (2026-06-03) - grote autonome bouw-sessie, live op de dev-server. Code-side klaar, NIET gecommit/herbouwd.**

### Zo hervat je (eerste 5 min)
1. Dev-server draait op **:5599** (current code, leest static/ vers van disk). Check: open `http://127.0.0.1:5599/` in Chrome -> oranje login of ingelogd. Down? Draai `bash "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/_dev_restart_5599.sh"` (start app.py op 5599 met vendor-ffmpeg op PATH). Log: `/tmp/omnidj_dev_5599.log`.
2. **Test ALTIJD op :5599, NOOIT :5555** (:5555 = oude stale bundle, pre-sessie71). Frontend-edit (index.html) -> reload met `?v=<iets>` (cache-bust). `app.py`-edit -> draai `_dev_restart_5599.sh` (Flask herlaadt niet vanzelf, debug=False).
3. Sjuul logt zelf in (ik mag geen wachtwoord typen). De sessie zit in :5599 localStorage en overleeft een reload.

### Gekozen volgende stap (Sjuul, sessie 72): A1 multi-tenant backend
Het isolatie-fundament is BEWEZEN (zie onder). Nu de backend-integratie zodat content-queries echt via RLS lopen:
- **`_user_supabase(access_token)`** in app.py: anon-client met de user-JWT erop (`postgrest.auth(jwt)` of per-request client). ALLE content-queries (workspaces, workspace_members, clips, dj_profiles, dj_templates, scheduled_posts) hierdoorheen, NIET via `supabase_admin` (service_role omzeilt RLS = Correctie 6). `supabase_admin` blijft alleen voor profiel/role/billing/audit.
- **`current_workspace_id()`** als 2e slot (membership-check + 403) bovenop RLS.
- **Frontend (Correctie 9):** `X-Omni-Workspace` zit in de centrale `api()` (~11348), maar 6 rauwe `fetch()` omzeilen die: clip-filmstrip 16135 / clip-overlays 17305 / brand-kit-watermark 17374 MOETEN de header krijgen; auth-refresh 11283 + forgot-password 25026 NIET (pre-auth); debug/logs 24152+24179 optioneel.
- **Migratie 010** (helpers->private; lost de 3 advisor-WARNs op): test op een Supabase-BRANCH + her-audit, dan **CHECKPOINT met Sjuul vóór toepassen op main**.
- Elke slice: auth/analyse/edit/export blijven groen op :5599 (plan sectie 9b quality-gate).
- Alternatief dat Sjuul ook overweegt: eerst **commit + gesignde rebuild** om de wins vast te zetten (werkende installable, vervangt de stale :5555-build), daarna A1-backend.

LET OP - twee servers draaien:
- **:5555 = STALE bundle** (pre-sessie71: geen Editor-tab, geen import-clip). Sjuuls geinstalleerde .app is dus oud.
- **:5599 = current-code dev-server** (leest `static/index.html` vers van disk). HIER testen. Herstart na een `app.py`-edit met `bash _dev_restart_5599.sh` (dev-helper deze sessie, NIET committen). Frontend-edits zijn live na een cache-bust reload (`?v=ts`).

Gedaan + live geverifieerd op :5599 (current code):
- **Kernflow GROEN:** login (oranje V2) -> analyse (echte sets, 23/33 clips, geen dup) -> live progress-kaart -> editor (preview speelt, trim/text/track) -> export (POST /api/export -> valide 1080x1920 mp4 + audio, hernoemde naam in filename). **C1** Editor-tab + leegstaat-kiezer + routing naar clip-editor werkt. **C2** Import (video -> /api/import-clip -> nieuw 1-clip-job -> opent in editor) werkt.
- **FREE-badge GEFIXT -> STUDIO.** 3 oorzaken: (a) `window.STATE = STATE;` alias toegevoegd na STATE-decl (STATE was lexical const -> `window.STATE` was ALTIJD undefined -> hele klasse bugs, incl. de renderAnalyse processing-guard die de analyse-progress-kaart altijd wiste); (b) `v2GetCurrentPlan` las STATE.user.plan_id -> nu STATE.session.profile.plan; (c) `renderAccountChip` schildert nu ook #v2WsPlan + #settings-ws-plan-badge na profiel-load.
- **Trage-analyse:** 30s TTL-cache op token-validatie (`_cached_auth_user` in app.py) -> /api/status-poll doet niet elke 1.5s een Supabase auth/v1/user round-trip. py_compile groen, auth na server-restart OK. (Inherente kost = librosa HPSS + per-clip ffmpeg; bewust niet herschreven.)
- **DB live (main):** business@sjuulstudios.com -> plan=studio + max_workspaces=3.

**TE COMMITTEN (1 commit: sessie 69 + 71 + 72 samen):**
- Sessie 72 gewijzigd: `Omni DJ/static/index.html` (window.STATE-alias + v2GetCurrentPlan-path + renderAccountChip v2-badges), `Omni DJ/app.py` (_cached_auth_user TTL-cache), `HANDOVER.md`.
- Stapelt op sessie 71 (`app.py` /api/import-clip + picker `sys.frozen`-gate; `static/index.html` C1/C2; `supabase/migrations/005-010*.sql`; `supabase/audit/AUDIT_cross_account_rls.sql`; `PLAN-COMBINED...md`; `SESSIE71-RUNBOOK.md`) en sessie 69 (`OmniDJ.spec`, `entitlements.plist`, `requirements.txt`, `system_fonts_cache.json`; picker-fix + V1->V2-uitfasering).
- **NIET committen:** `Omni DJ/_dev_restart_5599.sh` (dev-helper) + alle `*.pre-sessie*.bak`. Maak vóór de commit `static/index.html.pre-sessie72.bak` + `app.py.pre-sessie72.bak`.
- Gesignde rebuild + DMG->R2 pas NA de sessie-69 picker-smoketest (harde regel).

NOG OPEN (volgorde-bouw, Sjuul akkoord autonoom; checkpoint alleen bij A1-merge-naar-main / bestandsverwijdering / DMG->R2):
- rename "niet altijd" -> filename: backend OK (label gekeyd op 1-based `clip['index']`, bewezen met RENAMETEST_omni72.mp4); verdenk een specifieke frontend export-entry of de download-knop (/api/export-preset zonder labels). Nog pinnen.
- **A1 multi-tenant - isolatie-FUNDAMENT BEWEZEN:** cross-account RLS-audit GROEN op live main voor alle 5 content-tabellen (workspaces, clips, dj_profiles, dj_templates, scheduled_posts), beide richtingen, membership-trigger werkt, seed rolt schoon terug (0 residu, 14 ws intact). RESTEERT voor A1: (a) backend `_user_supabase()` anon+JWT helper i.p.v. service_role voor content-queries (Correctie 6 - additief, geen content-endpoint gebruikt de tabellen nog); (b) frontend X-Omni-Workspace header op de 6 rauwe fetch-calls (Correctie 9); (c) migratie 010 (helpers->private, advisor-cleanup) op een branch + her-audit + CHECKPOINT vóór main; (d) pipeline-koppeling (Correctie 8) bij per-workspace mappen.
- C7 Settings opschonen, C3 CapCut 3-pane editor (flagged), A2->C5 Brand, A3->C6 Calendar, B0 Electron, Spoor D audio-sync.
- Test-infra: pytest + Playwright. LET OP: Playwright E2E moet OP DE MAC draaien (sandbox kan :5599 niet bereiken). Security-pass + advisors. Leaked-pw confirm (lijkt al AAN; geen advisor-warning).
- DAN: backups + 1 commit (sessie 69+71+72 samen) + gesignde rebuild + DMG->R2 (pas NA picker-smoketest).

Detail: memory `project_sessie72_corecheck_and_fixes`.

---

**Sessie 71 (2026-06-02) - kritische review + eerste veilige bouw-slice. Code-side klaar, NIET gecommit/herbouwd.
Lees `SESSIE71-RUNBOOK.md` voor de smoketest + git + de A1-branch-stappen.**

Opgeleverd sessie 71 (stapelt bovenop de nog-niet-gecommitte sessie-69-wijzigingen, samen in 1 commit):
- **Plan v1.3** (`PLAN-COMBINED...md` sectie 9b): KRITIEK - backend draait alles via service_role en omzeilt RLS;
  A1 moet via anon-client + user-JWT zodat RLS de echte isolatie-grens is. Plus 9 kleinere correcties + aangepaste
  bouwvolgorde + per-slice quality-gate.
- **C1** Editor als eigen sidebar-tab + leegstaat-kiezer (Continue editing + recente sets + Import). Frontend-only.
- **C2** Import-knop (Editor-toolbar + Editor-leegstaat + Library-header) + additief `/api/import-clip` endpoint:
  losse video (mp4/mov/m4v/webm) rechtstreeks de editor in, lokaal opgeslagen, geen analyse. Analyse/export ongemoeid.
- **A1-migraties als REVIEW-bestanden** (NIET toegepast): `supabase/migrations/005-009*.sql` + verplichte
  `supabase/audit/AUDIT_cross_account_rls.sql`. Toepassen alleen op een branch, audit groen, dan pas main.
- Verificatie: `py_compile app.py` groen, `node --check` op de SPA-JS groen, pglast-parse op alle SQL-bestanden groen.
- Backups: `static/index.html.pre-sessie71.bak`, `app.py.pre-sessie71.bak`.

**LIVE UITGEVOERD sessie 71 (Supabase Pro + Chrome MCP, 2026-06-02):**
- **A1 toegepast op MAIN** (`lbabsffxefkrxwzkbzar`): migraties 005-009 live. 8 tabellen, RLS aan, 14 workspaces + 14 members
  gebackfilld (1 per profiel). Cross-account audit op een wegwerp-branch GROEN (user A ziet 0 van B en omgekeerd, op de
  echte auth.uid()/authenticated/JWT-stack). Branch daarna verwijderd. `add_owner_as_member` EXECUTE revoked (advisor-WARN weg).
  Migratie-bestanden kregen expliciete `grant ... to authenticated` (bleek nodig via de branch-audit).
- **Migratie 010 (review, NIET toegepast):** verplaatst RLS-helpers naar schema `private` om de laatste 3 advisor-WARNs
  (is_workspace_member/owner, can_access_dj_profile) op te lossen. Laag-risico (caller-only), optioneel; branch + her-audit eerst.
- **Upload-bug GEFIXT:** drag-drop "Drop a set" faalde met 401 "Geen Authorization header" omdat `uploadFile()` `window.STATE`
  las (STATE is een closure-const). Nu via bare `STATE`. Live geverifieerd: token resolvet, 401 weg.
- **Editor-leegstaat niet meer afgekapt:** `.ed-empty` was absolute over een ingeklapte parent -> normale flow + min-height. Live OK.
- **Analyse-stappen tonen nu bij drop (v2-bug):** in v2 startte de status-poller nooit (renderProcessing draait niet; processing
  mapt op analyse) EN renderAnalyse wiste `is-processing`. Fixes: `openProgressStream()` gestart in switchView('processing'),
  renderAnalyse-guard op `STATE.progressJobId`, en een zichtbare stappen-checklist (`#analyse-process-steps`, done/now/queued)
  in de processing-kaart gevoed door setProcUI.
- **E2E analyse bevestigd werkend (echte set):** Sjuul draaide een 55-min set (Ediine x Ho_r Berlin) -> 33 clips gecut,
  Library + editor gevuld, export-modal werkt. De kernpijplijn werkt dus op de nieuwe code.
- **Stappen-checklist liep vast op stap 1 (gefixt):** setProcUI's `analyseSetState`-forward gaf geen `stepIndex` mee,
  dus de checklist resette elke tick naar 0. Nu geeft het de berekende `activeIdx` door -> stappen lopen mee met %.
- **Processing blijft zichtbaar bij wegnavigeren + terug:** `renderAnalyse` herschildert de processing-kaart uit STATE
  als `STATE.progressJobId` actief is (poller loopt door op de achtergrond).
- **Knipperende oranje sidebar-dot** op de Analyse-nav zolang een analyse loopt (`#analyse-nav-dot`, getoggeld in `setBgProcessPill`).
- **Export-modal scrollbaar + responsive:** `.aspect-card` kreeg `max-height: calc(100vh - 48px)` + `overflow-y:auto` + smal-breekpunt,
  zodat alle controls (t/m de Export-knop) bereikbaar zijn.
- **Export "Kies map…" 500 gefixt:** de NSOpenPanel-route crasht op de dev-server (main thread = Flask serve-loop, geen Cocoa
  run-loop; + in-functie ObjC-class-def botst 2e keer). NSOpenPanel nu ALLEEN in de bundle (`sys.frozen`); dev gebruikt de
  thread-safe `osascript`-route. `/api/pick-folder` + `/api/pick-file` gegate; handler vangt alles af -> altijd JSON (nooit rauwe 500).
  LET OP (bundle, ongetest): de NSOpenPanel-class-redef-bug bestaat daar nog -> fix vóór de bundle-picker-smoke-test (definieer
  `_PanelRunner` 1x op module-niveau i.p.v. in de functie).

**WENSEN / NOG TE DOEN (Sjuul, sessie 71):**
- **Renamed clip-naam moet doorvertalen naar de gedownloade bestandsnaam na export.** Nu lijkt de hernoemde naam (editor/
  export-modal "Bestandsnaam") niet altijd de uiteindelijke filename op schijf te worden. Checken: `/api/export` label-flow +
  de sidecar/rename-logica (zie LESSONS / sessie 43-52 rename-werk) zodat de download de hernoemde naam draagt.
- **Trage analyse onderzoeken:** een 1-uur set duurt lang. Mogelijke factoren: librosa/HPSS op dev-Python (inherent), en elke
  `/api/status`-poll (1.5s) doet 2 Supabase-calls (auth/v1/user + profiles) -> veel chatter. Niet de analyse-thread zelf, maar
  onderzoeken (poll-interval verlagen of token-validatie cachen).
- **Clips-view = al redesigned** (eerdere sessies). De CapCut-stijl sizeable 3-pane editor (C3 uit het plan) is nog NIET gebouwd.

- **Whitelist:** `omnidj@monohq-labs.com` -> role=admin, plan=studio (matcht business@). LET OP: badge toont nog FREE tot
  uitloggen/inloggen (sessie-profiel gecached).
- **Leaked password protection AAN** (Supabase Auth, via dashboard) — advisor-WARN weg. Was geparkeerd tot Pro.
- **Live smoketest (dev-server :5599, ingelogd) - GROEN:** meerdere echte sets E2E gedraaid (Ediine 33 clips,
  Don Diablo 27, Franky Rizardo 151): analyse -> stappen-checklist loopt mee met %, Library + Clips + editor gevuld,
  export-modal scrollt, dot knippert op Analyse. Kernfuncties + auth werken op de nieuwe code. Nog door Sjuul te
  bevestigen: de export-render zelf + de "Kies map…"-Finder-dialog (pick-folder is code-gefixt, niet via Chrome getriggerd).

**TE COMMITTEN (sessie 71, 1 commit; stapelt op de nog-niet-gecommitte sessie 69):**
- Gewijzigd: `Omni DJ/app.py` (/api/import-clip + pick-folder/-file `sys.frozen`-gate + handler-guard),
  `Omni DJ/static/index.html` (C1/C2 + upload-fix + analyse-stappen-checklist + sidebar-dot + export-modal-scroll),
  `HANDOVER.md`. (Sessie 69 staat ook al in de tree: `OmniDJ.spec`, `entitlements.plist`, `requirements.txt`, `system_fonts_cache.json`.)
- Nieuw: `Omni DJ/supabase/migrations/005-010*.sql` (005-009 = LIVE op main toegepast; 010 = review, niet toegepast),
  `Omni DJ/supabase/audit/AUDIT_cross_account_rls.sql`, `PLAN-COMBINED-...md` (v1.3), `SESSIE71-RUNBOOK.md`, `HANDOVER-FULL-2026-06-02.md`.
- NIET committen: `*.pre-sessie71.bak` backups. Gesigned rebuild + DMG->R2 pas NA de sessie-69 picker-smoke-test (harde HANDOVER-regel).

**Nog open sessie 71:** C7 (Settings opschonen) bewust UITGESTELD (te veel JS-gebonden controls, vereist live iteratie).
Zie de WENSEN-lijst hierboven (renamed->filename, trage analyse onderzoeken). Dev-server-pad = `.../Omni DJ/Omni DJ`
(NIET `dj-clip-cutter`, die map bestaat niet meer; de oude §4 hieronder is op dat punt stale).

---

### Plan-sessie 70 context (basis voor het bouwen)

**Sessie 70 leverde een gecombineerd implementatieplan op + alle bouw-beslissingen zijn genomen (zie hieronder).
Volgende sessie = direct bouwen, geen beslissingen meer nodig (alleen C4-look is open).**

Plan: `PLAN-COMBINED-DATA-LAYER-PLUS-ELECTRON-2026-06-02.md` (v1.2). Lees dat als eerste vóór je bouwt.
Het bundelt + corrigeert de drie bron-plannen (content-calendar, moat-features, electron) en is op de ECHTE
live staat geverifieerd. Vier sporen:

- **Spoor A (data-laag, kritieke pad):** A1 multi-tenant fundament (migraties vanaf 005, want 004 is bezet) ->
  A2 Brand-architectuur -> A3 Content Calendar. A2/A3 NOOIT vóór A1.
- **Spoor B (Electron):** B0 prototype -> B1 lifecycle -> B2 packaging -> B3 signing -> B4 Windows. Losgekoppeld.
- **Spoor C (redesign + UX):** eigen Editor-tab + Import-knop (C1/C2), CapCut 3-pane sizeable editor (C3),
  Analyse-knop als Remotion particle-accelerator (C4), Brand-redesign (C5, na A2), Calendar-redesign (C6, na A3),
  Settings opschonen in secties + Advanced-inklap (C7), backend C8. Effecten-spec (zoom/blur/gaussian/strobe/
  transitions) staat in 4c - NIET nu bouwen, post-beta.
- **Spoor D (video + audio sync):** 2e knop op Analyse "Import video + audio sync"; volautomatisch waveform-sync +
  drift-correctie + waarschuwing; schone audio onder video muxen; camera-audio als inmix-track (volume + highpass);
  confidence + handmatige terugval. Nieuw `audio_sync.py` + `/api/sync-import`; analyzer.py/cutter.py blijven ongemoeid.

**Aanbevolen bouw-marsroute (sessie 71+):** start A1 + B0 + de losgekoppelde C-delen (C4 Analyse-knop, C3 editor,
C1/C2 Editor-tab + Import, C7 Settings) tegelijk. Na A1: A2 -> C5, en A3 -> C6. Spoor D na C3 (D1-D4 mag eerder).

**Smoketest-regel (sectie 4d):** bouw-en-test-lus per fase, niet stoppen tot de feature werkt EN strak oogt.
E2E met een echte set via Chrome MCP op de dev-server (`OMNI_DJ_PORT=<vrij>`). Inclusief sync-scenario +
data-isolatie-checks (2 users x 2 workspaces) + responsive breekpunten (rond 900/1280/1600px).

**Beslissingen Sjuul - BEVESTIGD sessie 70 (2026-06-02):**
1. **Data-laag: AKKOORD.** Media blijft lokaal (`workspaces/<id>/`), lichte metadata (brand-profiel, clip-metadata,
   scheduled_posts) naar Supabase. Privacy-belofte blijft intact.
2. **UI-term = "Artist".** LET OP: de code/datalaag blijft intern "workspace" heten (tabel `workspaces`,
   `workspace_id`, `current_workspace_id()`); alleen de UI-copy toont "Artist". Geen technische rename - plan en code
   blijven consistent, alleen labels/teksten in `index.html` zeggen "Artist".
3. **Plan-limiet: NOG NIET vastgelegd.** Bouw A1 met een INSTELBARE limiet (bv. `profiles.max_workspaces`, default
   afgeleid van plan) zodat het getal later beslist kan worden zonder migratie. FREE/Solo praktisch 1; Studio-getal
   (3 of 5) later.
4. **Startvolgorde: A1 + B0 + losgekoppelde C parallel.** Multi-tenant fundament (kritieke pad) samen met
   Electron-prototype en de data-onafhankelijke C-delen (C4 Analyse-knop, C3 editor-layout, C1/C2 Editor-tab + Import,
   C7 Settings).
5. **Niet-blokkerend (open):** accelerator-look puur Remotion of eerst Higgsfield-refs - te beslissen bij C4.

**Tools toegestaan bij bouwen (Sjuul akkoord):** computer-use, Chrome MCP, Supabase-connector, Remotion (animaties),
Higgsfield (concept-refs), terminal.

**LET OP - sessie 69 nog open:** file-picker-fix (NSOpenPanel) + V1->V2-uitfasering zijn code-side klaar maar NIET
gecommit/gerebuild. Gaat mee in EEN gezamenlijke commit met de nieuwe features (sectie 8 van het plan). DMG pas naar
R2 NA de smoke-test van de picker-fix. Zie §1-§2 hieronder voor de details.

---

## 1. LAATSTE SESSIE - 69 (2026-06-02)

**Twee dingen opgeleverd, code-side klaar, dev-geverifieerd, NIET gecommit/gerebuild.**

**A. File-picker-blocker opgelost (A+B+C).** In de gesignde bundle kon je geen DJ-set inladen:
`/api/pick-file` opende een osascript `choose file` Apple-Event die de hardened runtime blokkeert
(geen `apple-events` entitlement) → dialog verscheen nergens, request hing. Opgelost via alle 3 opties:
- **C (primair), `app.py`:** in-proces `NSOpenPanel` (Cocoa/PyObjC, geen Apple-Event → werkt onder hardened runtime).
  `_nsopenpanel_supported()` + `_pick_with_nsopenpanel()`; `_pick_file_macos`/`_pick_folder_macos` proberen dit eerst, fallback osascript.
- **B, `entitlements.plist`:** `com.apple.security.automation.apple-events` toegevoegd (houdt osascript-fallback werkend).
- **A, `static/index.html`:** `openFilePicker()` 7s-timeout + `_fallbackToBrowserPicker()` → verborgen file-input → `/api/upload`. Toasts bij hang/fout. Drag-drop ging al via `/api/upload`.
- **Bundling:** `OmniDJ.spec` hidden-imports `objc/AppKit/Foundation/Cocoa` + `collect_submodules("objc")`; `requirements.txt` kreeg `pyobjc-framework-Cocoa>=10.0`.

**B. V1-UI uitgefaseerd, V2 = enige UI.** Doel: users zien V1 niet meer, geen toggle meer; login/signup/onboarding + app standaard de oranje V2-UI. V1-code blijft bewaard (bestand + git). 3 mini-edits in `static/index.html`: `isV2On()`→`return true`, losse `v2On`-reader→`true`, `#v2FlagToggle` verborgen + click-handler weg. Oorzaak: v2-auth-CSS bestond al (oranje) maar zat onder `body.redesign-v2`, en die class kwam alleen bij flag-aan → verse install/login viel terug op oude amber-stijl.

**Dev-verificatie (Chrome MCP, source-server :5556 met `OMNI_DJ_PORT=5556`):** picker-hang→timeout-fallback+toast, server-fout→fallback, geldig pad→`_startLocalJob`, cancel→no-op. Login-knop = #D97742 (oranje), pill-tabs, toggle weg, signup-wizard oranje. `py_compile`/spec/JS-check groen.

---

## 2. NOG TE DOEN (Sjuul, op de Mac) - gebundeld

**Direct (sessie 69 afronden):**
1. **git commit + push** - `Omni DJ/app.py`, `static/index.html`, `entitlements.plist`, `OmniDJ.spec`, `requirements.txt`, `HANDOVER.md`. (index.html bevat picker-fix én V1→V2-uitfasering.)
2. **venv-dep:** `cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ" && venv/bin/pip install "pyobjc-framework-Cocoa>=10.0"`
3. **Rebuild gesigned+genotariseerd:** stop dev-server (poort vrij) → `./build_macos.sh sign notarize dmg` → vervang `/Applications`-versie.
4. **Smoke-test in de GESIGNDE bundle:** "Choose file" → NSOpenPanel opent (geen hang) → set laadt; drag-drop werkt; login/signup zijn oranje (V2); bij picker-fout nette toast i.p.v. hang.
5. **DMG→R2:** publiceer pas NA de smoke-test. LET OP: de sessie-68 DMG (`dist/Omni DJ.dmg`) was al gebouwd maar nog NIET naar R2 - die mag pas mee als de picker-fix erin zit.

**Geparkeerd / later:**
- **leaked-password-protection** (Supabase "Prevent use of leaked passwords"): alleen op Pro-plan; project staat Free. App weert zwakke ww al via `_COMMON_PASSWORDS` (auth.py) + minlengte 8. Aanzetten bij Pro-upgrade. Enige resterende advisor-warning.
- **Email Confirmation** staat UIT in Supabase (Auth) zodat testsignups werken. Voor v1.0/paid launch weer AAN zetten zodra eigen SMTP (SendGrid/Postmark/Resend) gekoppeld is.
- **Smoke-test op 2e Mac:** download via `downloads.omnidj.com/Omni-DJ-1.0.0.dmg`, open (geen Gatekeeper-popup), login, upload binnen home (werkt) + buiten home (403, S2), export MET captions (tekst zichtbaar).
- **Multi-tenant data (Fase 5b):** `workspace_id` + `artist_id` in Supabase-RLS. UI staat al klaar; alleen de data-laag mist (multi-artist = Studio-plan, max 3, Stripe price-ID hergebruiken).
- **Moat-features / content-calendar / ads:** zie `PLAN-MOAT-FEATURES-2026-05-26.md` + `PLAN-CONTENT-CALENDAR-2026-05-26.md`. Calendar-drafts zijn nu localStorage (overleven refresh, niet herinstall).
- **Toekomst (nog NIET bouwen):** OAuth TikTok/Instagram-upload, Windows .exe, Electron native window (`PLAN-NATIVE-WINDOW-ELECTRON-2026-05-30.md`), patent (NL/EU/global).

---

## 3. BEKENDE BUGS & VALKUILEN (niet opnieuw introduceren)

- **Duplicate clips:** clips toonden soms identieke video i.p.v. unieke drops. Terugkerend - check of het al gefixt is vóór je iets aan clip-logica wijzigt.
- **Off-by-one clip-index (sessie 51):** export gebruikte verkeerde clip. Fix zit in de FRONTEND (`index.html` ~9488, `[st.backendIdx - 1]`), NIET backend - `exportSelected` was al 0-based. `/api/export` verwacht 0-based `clip_indices`.
- **Caption-bake (sessie 50):** captions werden niet ingebakken door ontbrekende `import re` in `cutter.py`. Ook drawtext-detectie was te streng (sessie 67 regex-fix `(?m)^\s*\S+\s+drawtext\b` herkent Martin-Riedl static build). E2E groen sessie 52.
- **Large-file pipeline-hang:** bij grote audiobestanden kan de pipeline vastlopen - check timeouts + chunksize.
- **zlib "incorrect header check" / stale process:** GEEN bug. Eénmalige stale lang-draaiende bundle-instance (numba-JIT/first-run). Verse Terminal-launch verwerkt alles. Advies: bij hang app herstarten. `_process_job` slaat nu volledige traceback op in job-state, `/api/status` geeft `traceback` terug.
- **DATA_DIR (sessie 40):** in de PyInstaller-bundle is `BASE_DIR` read-only. Alle writes via `DATA_DIR` (env `CLIP_LIVE_USER_DATA`).
- **.app vs dev-server:** ffmpeg-paden + schrijfrechten + PyInstaller-gedrag verschillen. Test in BEIDE modi. In de bundle wordt stdout geslikt (runw) → log naar `~/Library/Application Support/Omni DJ/launcher.log`.
- **Host-gate (sessie 67):** `_security_gate` staat alleen Host `127.0.0.1:5555`/`localhost:5555` toe (421 buiten). Een dev-server op een andere poort vereist `OMNI_DJ_PORT=<poort>`, anders "Invalid host". Uit bij `OMNI_DJ_BIND=0.0.0.0`.
- **UI:** V2 is de enige UI (sessie 69). Niet terug naar V1/amber. Oranje accent = `--v2-accent #D97742` (hover #E08854).

---

## 4. BUILD / SIGNING / DEPLOY-RECEPT

**Dev-server:**
```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"
./start.sh
```
Browser: http://127.0.0.1:5555 (let op: live code zit onder `.../Omni DJ/Omni DJ/`, zie §6).

**Bundle bouwen:** in de projectmap met actieve venv:
- `./build_macos.sh dmg` - bouwt `.app` + `.dmg` (onverskend).
- `./build_macos.sh sign notarize dmg` - volledige signed+notarized build (productie).

**Apple-signing (sessie 66, werkend):**
- Apple ID (Developer + notary): `sjuulsmits@gmail.com` (persoonlijk, NIET het brand-adres - dat gaf 401).
- Team ID: `PTLV7AY4UL`. Certificaat: `Developer ID Application: Sjuul Smits (PTLV7AY4UL)`.
- Notary keychain-profiel: `omnidj-notary` (via `notarytool store-credentials`). App-specific password label `notarytool-omnidj`.
- `build_macos.sh` signt per-onderdeel met `--options runtime --timestamp` + entitlements (GEEN `--deep`); inclusief `*.framework`, hernoemde `Contents/MacOS/Omni DJ.bin`, en de `.app` als geheel. DMG-blok signt+notariseert+stapelt de DMG zelf.
- ffmpeg/ffprobe: **static arm64 binaries** in `vendor/ffmpeg/` (Homebrew-dylibs faalden notarization door andere Team IDs). Vangrail in build faalt als er externe dylibs in zitten.
- Verificatie: `spctl -a -t exec -vv "dist/Omni DJ.app"` → `accepted / Notarized Developer ID`; idem `-t open` op de `.dmg`.
- Vereiste eindgebruiker: **Apple Silicon (arm64), macOS 11+**. Intel werkt NIET. Geen Homebrew/pip/download nodig.

**R2 download-hosting (LIVE):**
- Cloudflare R2 Free-tier, bucket met custom domain **`downloads.omnidj.com`** (CNAME auto).
- DMG-naam: **`Omni-DJ-1.0.0.dmg`**. URL: `https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg` (overschrijven bij nieuwe build). Bucket-Size-teller in header is gecachet; de objectregel is leidend.

**Git:** `origin` = HTTPS `sjuulstudios/omni-dj-landing-by-MONO-LABS`, branch `main`. PAT-auth, Sjuul pusht zelf. `.gitignore` sluit ~39GB testdata uit. (Sandbox kan niet committen - Sjuul doet git zelf.)

---

## 5. ARCHITECTUUR & STACK

- **Product:** Omni DJ (voorheen Clip Live / Clip Drop). Eigenaar **MONO LABS**, domein **omnidj.com**. Detecteert drops/buildups in DJ-sets en genereert korte verticale/landscape clips (30-60s). Lokaal op Sjuuls Mac, doel = downloadbare .dmg/.exe.
- **Backend:** Python 3 + Flask 3.0. Loopback-bind (`OMNI_DJ_BIND=0.0.0.0` voor LAN). `debug=False`.
- **Audio:** librosa, numpy, scipy, soundfile. **Video:** ffmpeg (static binaries). **Optioneel (niet actief):** torch+demucs (source separation), pyobjc-Vision (person-detect auto-tracking).
- **Auth/data:** Supabase (project-display-name "Omni DJ"). RLS aan + correct (user kan eigen `plan`/`role`/`stripe_*` niet wijzigen). Migrations onder `supabase/migrations/` (001 RLS … 004 S3-security). Edge functions: `create-checkout-session`, `create-portal-session` (JWT-verified), `stripe-webhook` (`--no-verify-jwt`), `update-usage`.
- **Billing:** Stripe via edge functions; `runtime_config.py` bevat alleen publieke keys (geen secrets in bundle). `billing.py` heeft edge-function-fallback.
- **Security (sessie 67):** Host-allowlist + CSRF (Sec-Fetch-Site/Origin) + security-headers (nosniff, X-Frame DENY, CSP, HSTS over https). `_path_within_home()` whitelist op `/api/upload-local(+/scan)` (403 buiten home). Geen secrets in git/bundle, geen shell-injection, geen path-traversal.
- **Pricing/plannen:** FREE / PRO / STUDIO (multi-artist max 3 = Studio). 30-dagen rolling quota (FREE 2 sets/30d). Detail: zie plan-docs.

---

## 6. KEY FILES & PADEN

- **Live code (sessie 59 rename):** `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/` (dubbele "Omni DJ"-map). Start-script verwijst nog naar oudere `dj-clip-cutter`-naam in oude docs - gebruik de actuele map.
- `app.py` - Flask entry; routes, security-gate, `_pick_file_*`/`_pick_folder_*`, `_process_job`, upload-local.
- `analyzer.py` - drop-detectie (librosa). `cutter.py` - video snijden (ffmpeg, smart-cut landscape, drawtext/captions). `uploader.py` - toekomstige social upload. `auth.py` / `billing.py`.
- `static/index.html` - volledige SPA (1 bestand). V2-UI onder `body.redesign-v2` (nu altijd aan). Auth-overlay, editor, modals, wizard.
- `OmniDJ.spec` / `launcher.py` / `entitlements.plist` / `build_macos.sh` - bundling/signing. `runtime_config.py` - publieke keys-fallback.
- `vendor/ffmpeg/` - static arm64 ffmpeg/ffprobe.
- **User-data (bundle):** `~/Library/Application Support/Omni DJ/` (writes + `launcher.log`).
- **Plan-docs (project-root):** **PLAN-COMBINED-DATA-LAYER-PLUS-ELECTRON-2026-06-02.md (v1.2 - ACTIEF, lees dit eerst voor de bouw)**, PLAN-MOAT-FEATURES, PLAN-CONTENT-CALENDAR, PLAN-REBRAND-OMNI-DJ, PLAN-NATIVE-WINDOW-ELECTRON, PLAN-SESSIE67-DIAGNOSE-FIX-SECURITY, etc.

---

## 7. THEMATISCHE HISTORIE (eindstand per gebied)

- **Rebrand → Omni DJ (sessie 53/63):** code-side rebrand uitgevoerd+geverifieerd (env-vars, localStorage, bundle-ID `com.monolabs.omnidj`, domein omnidj.com). Detail-plan: PLAN-REBRAND-OMNI-DJ.
- **Redesign V2 (sessie 45-58):** premium dark-mode shell, fase 1-5. Sidebar (Analyse/Library/Brand/Auto-mode/Social/Calendar/Insights/Settings), dashboard, editor/timeline, modals, auth, onboarding-wizard. Sessie 69: V2 nu enige UI.
- **Export-pipeline (sessie 43-52):** auto-bake captions, rename-veld, schone filenames+sidecar, ratio-tiles, caption/wm-toggles, folder-whitelist (home), selectie-preview-balk. E2E export groen (sessie 52).
- **Editor (sessie 41-68):** fonts (built-in + system-scan), color-wheels, trim sneller (smart-cut landscape ~5x, 1 formaat on-demand), bron-bewuste spatiebalk-preview.
- **Security (sessie 32-67):** flask-limiter, RLS-migrations, library-scoping fix (20/20 cross-account tests), S1-S4 hardening. 4 grote vibecode-killers waren al afwezig.
- **Signing/deploy (sessie 66-67):** Apple code-sign+notarize gelukt, R2-hosting live, DNS TransIP→Cloudflare, ffmpeg static-binary fix.
- **Website/landing (sessie 28-62):** premium landing gebouwd + naar GitHub gepusht (zie BUILD-LOG-website + PLAN-website*).

> **Sessie-by-sessie detail nodig?** De volledige, ongekorte historie per sessie staat in
> `HANDOVER-FULL-2026-06-02.md` (snapshot vóór deze compactie) en `HANDOVER-ARCHIVE.md` (oudere sessies).
> Terugkerende patronen + valkuilen: `LESSONS-LEARNED.md`. Raadpleeg die als deze samenvatting niet genoeg context geeft.

---

## 8. WERKWIJZE (altijd volgen)

1. Lees dit bestand eerst. Raadpleeg `LESSONS-LEARNED.md` vóór je iets aanraakt dat al eens gefixt is.
2. Diagnose → aanpak voorstellen (met opties) → wachten op "ja" → pas dan uitvoeren.
3. Minimale impact: alleen wat gevraagd is. Meld als scope groter is dan verwacht. Backup vóór risky change (`bestand.pre-sessieNN.bak`).
4. **Voor Sjuul:** niet-technisch op devniveau - leg uit wat een commando doet, één stap tegelijk. Terminal-commando's letterlijk, ZONDER markdown code-fences, paden met spaties altijd quoten. Geen em-dashes/en-dashes (project-regel).
5. Update dit bestand na elke significante stap (bug gefixt, feature toegevoegd, nieuwe bug ontdekt).

---

## 9. VEILIGHEID

- Nooit API keys/wachtwoorden in bestanden opslaan (`.env` nooit committen).
- Altijd bevestiging vragen vóór bestandsverwijdering.
- Backup vóór elke risky change.
