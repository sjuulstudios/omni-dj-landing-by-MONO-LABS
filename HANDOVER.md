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
  - `REPLACE_ME` in de landing = Formspree endpoint voor het beta-formulier (gratis via formspree.io)
  - `REPLACE_DMG_URL` = R2-link naar de DMG (`https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg`)
  - Google Workspace domein-verificatie voor `monohq-labs.com` nog niet afgerond
- **Oude landing:** `landing-omnidj/` map is de vorige simpele 1-page versie, niet meer actief

> **GECOMMIT + GEPUSHT (2026-06-04):** commit `9176c8a` op `main` bevat sessie 69+71+72+73+74 (22 bestanden). De "NIET gecommit"-vermeldingen verderop zijn historisch. NOG OPEN voor Sjuul: E2E-export-check fase 2b (nu met per-workspace logo), clips-metadata (007, bewust uitgesteld), migratie 010 (review), test-infra (pytest/Playwright), gesignde rebuild + DMG->R2.

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
