# Omni DJ - Gecombineerd implementatieplan: data-laag (multi-tenant + Brand + Calendar) + Electron

> **Versie:** 1.2 - 2026-06-02 (sessie 70)
> **Auteur:** Claude + Sjuul
> **Status:** PLAN. Nog niet bouwen. Eerst lezen, beslissen, dan fase voor fase.
> **Vervangt niet, maar bundelt en CORRIGEERT:** PLAN-CONTENT-CALENDAR-2026-05-26.md (multi-tenant + calendar),
> PLAN-MOAT-FEATURES-2026-05-26.md (Brand-profielen §3), PLAN-NATIVE-WINDOW-ELECTRON-2026-05-30.md (Electron).
>
> **Drie parallelle sporen:**
> - **Spoor A (data-laag):** multi-tenant fundament EERST, dan Brand-architectuur, dan Content Calendar erbovenop.
> - **Spoor B (Electron):** native window, volledig losgekoppeld, mag parallel lopen.
> - **Spoor C (redesign + UX):** Analyse/Library/Clips/Editor/Export/Brand/Calendar/Settings mooier, responsive en
>   sizeable maken; nieuwe Editor-tab + Import-knop; Analyse-knop als particle-accelerator. Losgekoppelde delen mogen
>   direct, view-redesigns landen na de bijbehorende A-fase.
> - **Spoor D (video + audio sync):** tweede knop op de Analyse-page die losse camera-video en schone audio
>   volautomatisch op waveform synct, de schone audio onder het beeld muxt en daarna de normale analyse draait;
>   camera-audio blijft als inmix-track in de editor. Mag de bestaande flow niet verstoren (aparte ingang).
>
> **Sessie 69 wordt deze sessie NIET afgerond.** De file-picker-fix + V1-naar-V2-uitfasering zijn code-side klaar
> maar nog niet gecommit/gerebuild. Sjuul rondt dat later af in EEN gezamenlijke commit samen met de nieuwe features
> uit dit plan (zie sectie 8).

---

## 0. Waarom dit plan bestaat en wat het corrigeert

De drie bron-plannen zijn strategisch sterk maar gingen uit van een data-architectuur die in de live code NIET zo is.
Voor dit plan is de echte staat geverifieerd (sessie 70, 2026-06-02). De belangrijkste correcties:

**Correctie 1 - Supabase bevat alleen auth/billing, geen content.**
Live project `lbabsffxefkrxwzkbzar` ("Clip Drop Live", ACTIVE_HEALTHY) heeft exact twee tabellen:
`profiles` (13 rijen) en `audit_logs` (33 rijen). Er is GEEN `jobs`, GEEN `brand_kits`, GEEN `clips` tabel.
Het content-calendar-plan nam aan dat die bestonden en alleen een `workspace_id`-kolom nodig hadden. Dat klopt niet.

**Correctie 2 - content leeft lokaal, niet in de cloud.**
Clips, jobs, history en de Brand Stack staan op de machine van de user onder
`~/Library/Application Support/Omni DJ/` (DATA_DIR). Brand kit = lokaal `brand_kit.json` + asset-folders
(`brand_kit/fonts`, `brand_kit/logo`, `brand_kit/watermark`). Dit is bewust: local-first is de privacy-belofte
(zie moat-plan §2). Multi-tenant betekent dus NIET "kolom toevoegen", maar een expliciete keuze per data-soort:
blijft het lokaal (per-workspace-map) of gaat het naar Supabase (per-workspace-rij). Sectie 2 maakt die keuze.

**Correctie 3 - migratie-nummering klopt niet meer.**
De plannen reserveerden 004/005/006 voor workspaces. Maar `004_sessie67_security_definer_hardening.sql`
is al gebruikt (sessie 67). Nieuwe migraties beginnen daarom bij **005**. Dit plan hernummert alles.

**Correctie 4 - de multi-artist UI bestaat al, alleen client-side.**
De V2-sidebar heeft al een workspace-chip + artist-chip + "Manage workspace"-actie
(`v2PaintWorkspaceChip`, `v2PaintArtistChip`, `v2ArtistDropdownContent`). De actieve artiest + de artiestenlijst
staan in `localStorage` (`omniDjActiveArtist`, `omniDjArtists`). Dat is puur frontend, zonder data-isolatie en
zonder server-kant. De frontend-schil staat dus klaar; alleen de laag eronder ontbreekt. Dit verlaagt het
frontend-werk in Fase A1 fors.

**Correctie 5 - calendar-drafts staan al in localStorage.**
Sessie 56 bouwde Social/Calendar/Insights als werkende shells met mock-data en localStorage-drafts
(overleven refresh, niet herinstall). De calendar-UI bestaat dus al als shell; Fase A3 vervangt de localStorage-laag
door een echte data-laag, het is geen UI-from-scratch.

---

## 1. Overzicht van de twee sporen en hun afhankelijkheden

```
SPOOR A - data-laag (strikt volgordelijk)
  A1  Multi-tenant fundament   ── moet eerst, alles hangt eraan
        │
        ├── A2  Brand-architectuur (dj_profiles + templates, scoped op workspace)
        │
        └── A3  Content Calendar (scheduled_posts, scoped op workspace)
                  (publisht nog NIETS - Postiz is een latere fase, buiten dit plan)

SPOOR B - Electron (losgekoppeld, mag op elk moment parallel)
  B0  Prototype  →  B1  Lifecycle + native polish  →  B2  Packaging macOS
                                                          →  B3  Signing  →  B4  Windows
```

**Harde dependency-regels:**
- A2 en A3 mogen NIET starten voordat A1 (workspaces + RLS + workspace-scope in backend) groen is. Anders bouw je
  brand/calendar op `user_id` en moet je later remigreren naar `workspace_id` - exact het dubbele werk dat we vermijden.
- A2 en A3 zijn onderling onafhankelijk: zodra A1 staat, mogen ze in willekeurige volgorde of zelfs parallel.
  Aanbeveling: A2 (Brand) eerst, want Calendar-previews tonen straks de brand toegepast op de clip (A3 leunt visueel op A2).
- Spoor B raakt de data-laag niet aan. Het enige raakvlak is auth-redirects bij een dynamische poort (sectie 5, punt B-auth).

---

## 2. De data-laag-keuze (de kern-beslissing voor Spoor A)

Per data-soort kiezen we waar de waarheid leeft. Leidend principe: **zware media blijft lokaal (privacy + geen
upload-wachttijd), lichte metadata + coordinatie gaat naar Supabase (zodat een workspace gedeeld en server-side
gescoped kan worden).**

| Data | Waar nu | Waar na dit plan | Reden |
|---|---|---|---|
| Audio/video bron + gerenderde clips | lokaal (DATA_DIR) | **blijft lokaal**, per-workspace-submap | privacy-belofte, bestandsgrootte |
| Brand kit (logo/fonts/kleuren/watermark) | lokaal `brand_kit.json` | **Supabase `dj_profiles` (metadata) + Supabase Storage (assets), met lokale cache** | moet per workspace scopebaar zijn + deelbaar met manager |
| Job/clip-historie (metadata) | lokaal | **Supabase `clips` (lichte metadata, geen media)** | nodig om in Calendar een clip te kunnen kiezen per workspace |
| Workspaces + members | bestaat niet | **Supabase `workspaces` + `workspace_members`** | de scope-sleutel zelf |
| Geplande posts | localStorage | **Supabase `scheduled_posts`** | moet de herinstall overleven + per workspace |
| Actieve artiest (UI-state) | localStorage | blijft localStorage (cache) + server is bron | snelle UI, server is autoritatief |

**Gevolg voor de privacy-belofte (moat-plan §2):** alleen metadata + brand-assets verlaten de machine, nooit
de bron-audio of de gerenderde clip-media. Voor het toekomstige Studio-tier (unreleased ID's) houden we de optie
om brand-assets ook lokaal-only te houden. Dit is consistent met het bestaande local-first verhaal.

**Per-workspace lokale mappen:** DATA_DIR krijgt een laag `workspaces/<workspace_id>/` waaronder clips, drafts en
de lokale brand-cache vallen. De huidige platte DATA_DIR-structuur wordt bij de data-migratie (A1, stap 4) onder
de default-workspace van de user geschoven.

---

## 3. SPOOR A - gedetailleerd

### Fase A1 - Multi-tenant fundament

> Niets anders in Spoor A mag hiervoor. Dit is het fundament.

**Database (migraties, nieuw genummerd vanaf 005):**

- **005_workspaces.sql** - tabellen `workspaces` + `workspace_members`.
  ```sql
  create table public.workspaces (
    id          uuid primary key default gen_random_uuid(),
    name        text not null,            -- "DJ Sjuul" / "Lisa Korver"
    slug        text unique,
    owner_id    uuid not null references auth.users(id) on delete cascade,
    artist_name text,
    avatar_url  text,
    created_at  timestamptz default now()
  );
  create table public.workspace_members (
    workspace_id uuid references public.workspaces(id) on delete cascade,
    user_id      uuid references auth.users(id) on delete cascade,
    role         text check (role in ('owner','editor','viewer')) default 'editor',
    invited_at   timestamptz default now(),
    primary key (workspace_id, user_id)
  );
  ```
- **006_workspaces_rls.sql** - RLS-policies. Patroon: een rij is leesbaar/schrijfbaar als de huidige user
  member is van die workspace. Owner-only voor delete + member-beheer. Dit is de hoogste-risico-stap
  (data-isolatie tussen workspaces). Test-account-matrix verplicht voor oplevering (zie sectie 7).
- **007_clips_metadata.sql** - lichte `clips`-tabel (geen media):
  ```sql
  create table public.clips (
    id           uuid primary key default gen_random_uuid(),
    workspace_id uuid not null references public.workspaces(id) on delete cascade,
    local_path   text,                    -- verwijzing naar bestand op de machine
    label        text,
    duration_s   numeric,
    source_set   text,
    created_at   timestamptz default now()
  );
  create index on public.clips (workspace_id, created_at);
  ```
  + RLS in dezelfde migratie.

**Data-migratie (eenmalig, in 005 of als los script):**
voor elke bestaande rij in `profiles` automatisch 1 workspace aanmaken op basis van `artist_name` of `full_name`,
en die user als `owner` in `workspace_members` zetten. Lokaal: bestaande platte DATA_DIR-content onder
`workspaces/<default_id>/` schuiven (idempotent script, draait bij eerste start na de update).

**Backend (`app.py`):**
- Nieuwe helper `current_workspace_id()` die uit een request-header (`X-Omni-Workspace`) of sessie de actieve
  workspace haalt en verifieert dat de user member is (anders 403). Dit hangt naast de bestaande security-gate.
- Nieuwe endpoints: `/api/workspaces` (list/create), `/api/workspaces/<id>` (get/update/delete),
  `/api/workspaces/<id>/members` (list/invite/remove).
- Alle bestaande content-endpoints (upload, jobs, brand-kit, history, export) krijgen workspace-scope:
  ze schrijven/lezen onder de actieve-workspace-map en/of filteren Supabase-queries op `workspace_id`.
- Stripe: `profiles` krijgt `max_workspaces` (afgeleid van plan). Workspace-create blokkeert bij overschrijden
  (FREE/Solo = 1, Studio = max 3 artiesten zoals in de UI-paywall sessie 54/55). Geen nieuwe Stripe-products nodig;
  alleen een plan-naar-limiet-mapping in `billing.py`.

**Frontend (`static/index.html`):**
- De bestaande workspace-/artist-chip + "Manage workspace"-actie aansluiten op de echte endpoints
  (nu localStorage-only). `omniDjActiveArtist`/`omniDjArtists` worden cache; server is autoritatief.
- Bij workspace-wissel: actieve-workspace-header meesturen in alle `/api/*` calls.
- "Manage workspace"-scherm onder Settings: rename, members, plan-limiet tonen.

**Verificatie A1:** bestaand single-user account blijft werken (krijgt automatisch zijn default-workspace).
Tweede workspace aanmaken lukt alleen op Studio-plan. Cross-account test (sectie 7) groen.

---

### Fase A2 - Brand-architectuur

> Bouwt op A1. Brand wordt per workspace gescoped.

**Database:**
- **008_dj_profiles.sql** - `dj_profiles` (1 per workspace) + `dj_templates` (N per profiel).
  ```sql
  create table public.dj_profiles (
    id           uuid primary key default gen_random_uuid(),
    workspace_id uuid unique not null references public.workspaces(id) on delete cascade,
    profile      jsonb not null,    -- visual/typography/lower_third/cta/hashtags/caption_voice
    updated_at   timestamptz default now()
  );
  create table public.dj_templates (
    id           uuid primary key default gen_random_uuid(),
    profile_id   uuid not null references public.dj_profiles(id) on delete cascade,
    name         text not null,     -- "Festival-clip" / "Studio-mix" / "Track-release"
    overrides    jsonb not null,
    created_at   timestamptz default now()
  );
  ```
  + RLS (member-scoped via de workspace van het profiel).
- De `profile` jsonb volgt het schema uit moat-plan §3 (artist_name, alias, visual, typography, lower_third,
  cta met Spotify/Beatport-links, hashtags per platform, caption_voice).

**Brand-assets:** logo/fonts/watermark gaan naar Supabase Storage in een per-workspace-bucket-pad,
met een lokale cache onder `workspaces/<id>/brand_kit/`. De bestaande lokale brand-kit-logica in `app.py`
(`_load_brand_kit`/`_save_brand_kit` + `BRAND_*_DIR`) wordt de cache-laag; de waarheid wordt het Supabase-profiel.
Migratie van de bestaande lokale `brand_kit.json` naar het default-workspace-profiel gebeurt eenmalig.

**Backend:** `/api/brand/profile` (get/save), `/api/brand/templates` (CRUD), asset-upload-endpoints
workspace-scoped. De bestaande brand-endpoints worden hierop omgelegd (niet dupliceren).

**Renderer (`cutter.py`):** uitbreiden zodat hij profiel + actief template leest en in ffmpeg-filtersyntax toepast
(drawtext voor captions/lower-third, overlay voor logo/watermark, fade voor CTA). De bestaande drawtext/caption-
pipeline (sessie 50 `import re`-fix + sessie 67 regex) is het startpunt; niet herschrijven, uitbreiden. Begin met
EEN template ("Festival-clip"), daarna 1 tot 2 dagen per extra template.

**Frontend:** de bestaande "Brand Stack"/Style-view (`data-view="style"`) wordt de profiel-editor; template-keuze
erbij. Geen nieuwe view nodig.

**Verificatie A2:** brand-profiel van workspace A is niet zichtbaar in workspace B. Export met profiel toegepast
toont logo + lower-third + CTA. Bestaande lokale brand-kit is correct gemigreerd naar het default-profiel.

---

### Fase A3 - Content Calendar

> Bouwt op A1 (scope) en leunt visueel op A2 (previews met brand). Publisht NIETS - draft-systeem.

**Database:**
- **009_scheduled_posts.sql** - `scheduled_posts` (workspace-scoped) + RLS.
  ```sql
  create table public.scheduled_posts (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    clip_id       uuid references public.clips(id),
    caption       text,
    platforms     text[] not null,            -- ['tiktok','instagram','youtube']
    scheduled_for timestamptz not null,
    status        text default 'draft',       -- draft|scheduled|published|failed
    created_by    uuid references auth.users(id),
    created_at    timestamptz default now(),
    updated_at    timestamptz default now()
  );
  create index on public.scheduled_posts (workspace_id, scheduled_for);
  ```
  (Geen `postiz_post_ids` nog; dat komt pas in de Postiz-fase, buiten dit plan.)

**Backend:** `/api/calendar/list?from=X&to=Y`, `/api/calendar/schedule`, `/api/calendar/update`,
`/api/calendar/delete`. Alles workspace-scoped.

**Frontend:** de bestaande Calendar-shell (sessie 56) omzetten van localStorage naar deze endpoints.
"Plan in Calendar"-knop in de export-modal (datum/tijd + platform-select + caption pre-filled met clip-label).
Month/Week-view, drag-to-reschedule. Behoud van het bestaande visuele werk; alleen de databron wisselt.

**Verificatie A3:** post gepland in workspace A verschijnt niet in workspace B. Draft overleeft herinstall
(staat in Supabase, niet localStorage). "Plan in Calendar" vanuit export maakt een echte rij.

---

## 4. SPOOR B - Electron (parallel, losgekoppeld)

Inhoud volgt PLAN-NATIVE-WINDOW-ELECTRON-2026-05-30.md ongewijzigd. Kernidee: Electron wrapt de bestaande
PyInstaller-backend als sidecar; analyse blijft 100% lokaal. Fasen:

- **B0 - Prototype:** minimale `electron/main.js` start de bestaande dev-backend op een VRIJE poort, health-check
  op `/`, laadt dan de UI in een Chromium-venster. Splash tijdens opstart. Doel: bewijzen dat UI + analyse + export
  werken in een Electron-venster. Geen packaging.
- **B1 - Lifecycle + native polish:** sidecar uit PyInstaller-build, quit/crash-handling (geen zombie Python via
  `before-quit` + `window-all-closed` + process-tree-kill), macOS-menubalk, Cmd-shortcuts, finish-notificatie,
  Dock-progress.
- **B2 - Packaging macOS:** electron-builder config, `.app` + `.dmg`, ffmpeg meebundelen (static arm64 binaries
  uit `vendor/ffmpeg/`).
- **B3 - Signing/notarization:** via electron-builder met de bestaande Developer ID (Team `PTLV7AY4UL`,
  Apple ID `sjuulsmits@gmail.com`). De huidige `build_macos.sh` sign/notarize-stappen vervallen want
  electron-builder neemt ze over. De huidige PyInstaller-`.app`-flow blijft als fallback tot Electron groen is.
- **B4 - Windows:** PyInstaller Windows-backend + electron-builder NSIS-installer. Windows-signing later.

**Aanbeveling start-volgorde Spoor B:** begin met B0 zodra je wilt. Het is de laagste-risico-start van alles in
dit plan en raakt de data-laag niet, dus het kan veilig naast A1 lopen.

---

## 4b. SPOOR C - Redesign + UX (bestaande features mooier, responsive, sizeable)

> Dit spoor herontwerpt de pagina's die er al zijn (Analyse, Library, Clips, Editor, Export, Brand, Calendar,
> Settings) zonder de werkende pipeline te slopen. Het is grotendeels frontend (`static/index.html`, CSS + JS),
> met enkele kleine backend-toevoegingen (Import-endpoint, panel-layout-persistentie). Spoor C mag deels parallel
> aan Spoor A, maar Brand- en Calendar-REDESIGN landen het netst NA respectievelijk A2 en A3, zodat we niet twee
> keer aan dezelfde view bouwen. Analyse-knop, Editor-layout, Import en Settings-opschoning zijn onafhankelijk van
> de data-laag en mogen direct.

### Globaal ontwerpprincipe (geldt voor alle views)

- **Eén designtaal:** V2-dark, accent `--v2-accent #D97742` (hover `#E08854`). Geen nieuwe kleurtokens tenzij nodig.
  Consistente kaart-radius, spacing-schaal en typografische hierarchie over alle views.
- **Responsive als first-class:** elke view moet bruikbaar blijven van smal (rond 900px, Electron-venster verkleind)
  tot breed (ultrawide). Sidebar collapset naar iconen onder een breekpunt. Geen horizontale scroll, geen afgekapte
  controls. Dit wordt per view in de smoketest op meerdere breedtes bewezen (sectie 7b).
- **Sizeable panels met persistentie:** waar panelen sleepbaar zijn (vooral de editor), worden splitter-posities
  opgeslagen. Nu in `localStorage`; zodra A1 staat, per workspace in Supabase (`workspace_settings` jsonb, zie C7).

### C1 - Nieuwe sidebar-structuur (Editor als eigen tab)

De V2-sidebar heeft nu 8 keys: `analyse, library, brand, social, calendar, insights, automode, settings`.
Toevoeging: een **`editor`-tab** als eigen sidebar-item, zodat je rechtstreeks de editor in kunt zonder eerst via
Library/Clips te navigeren. Voorgestelde volgorde:

```
Analyse  |  Library  |  Editor (nieuw)  |  Brand  |  Calendar  |  Social  |  Insights  |  Auto-mode  |  Settings
```

Gedrag van de Editor-tab bij openen (jouw keuze verwerkt):
1. **Herstel laatste sessie** als er een is (laatst bewerkte clip/project uit cache terugladen).
2. Anders een **kiezer eerst**: Library-projectkiezer + clip-kiezer-grid van de huidige workspace.
3. In beide gevallen staat de **Import-knop** in de toolbar (zie C2).

### C2 - Import-knop (losse short of audio in de tool trekken)

- Knop in de Editor-toolbar en in de Library-header: "Import".
- Accepteert **video en audio** (mp4/mov/wav/mp3/m4a en wat ffmpeg verder aankan binnen die twee soorten).
- Bestand landt **lokaal in de actieve-workspace-map** als een "imported clip" (`workspaces/<id>/imported/`), met een
  lichte metadata-rij in `clips` (A1) zodra de data-laag staat. Tot die tijd lokaal-only.
- Geen analyse vereist: een geimporteerde short gaat direct de editor in voor trim, captions, brand en export.
- Backend: klein nieuw endpoint `/api/import-clip` (workspace-scoped, hergebruikt de bestaande upload-validatie +
  `_path_within_home()`-whitelist). ffmpeg-probe voor duur/afmetingen, thumbnail genereren.

### C3 - Editor + preview op 1 pagina, CapCut-stijl drie sizeable panes (jouw keuze)

Layout-model:

```
┌──────────────────────────────┬───────────────────────────┐
│  PREVIEW (video, ratio-aware) │  CLIP / CUE-LIJST         │   <- bovenste rij, horizontaal splitsbaar
│                               │  (drops, selectie, props) │
├──────────────────────────────┴───────────────────────────┤
│  TIMELINE (volle breedte, tracks + trim-handles + minimap)│   <- onderste rij, verticaal splitsbaar
└───────────────────────────────────────────────────────────┘
```

- **Drie panes, twee splitters:** een horizontale splitter tussen Preview en Clip/Cue-lijst, een verticale splitter
  tussen de bovenrij en de Timeline. Beide sleepbaar met min/max-grenzen (preview niet kleiner dan bruikbaar,
  timeline niet hoger dan X% van het venster).
- **Sizeable preview:** sleep de splitters om de preview groter/kleiner te maken; de timeline wordt korter/langer.
- **Persistentie per workspace** (jouw keuze): splitter-posities opgeslagen, eerst localStorage, later
  `workspace_settings` in Supabase. Resize van het venster herschaalt vloeiend binnen de grenzen.
- **Hergebruik bestaande bouwstenen:** de huidige editor heeft al trim-handles, een minimap, text-/track-resize en
  `ew-resize`/`nwse-resize`-cursors. Die blijven; we bouwen er een splitter-grid (CSS grid + drag-resizers) omheen.
  Niet herschrijven, omkaderen.
- **Responsive fallback:** onder het smalle breekpunt stapelen de drie panes verticaal (preview boven, dan cue-lijst,
  dan timeline) met tab-knoppen om te wisselen, zodat het op een verkleind venster werkbaar blijft.

### C4 - Analyse-knop als "particle accelerator" (Remotion-gerenderde loop, jouw keuze)

- De Analyse-actie (nu de dropzone met kalme drift-particles) krijgt een **particle-accelerator-knop**: light-particles
  die in een void naar het centrum/naar binnen reizen, alsof de knop de DJ-set naar binnen zuigt.
- **Techniek (jouw keuze):** een met **Remotion** vooraf gerenderde, naadloze loop (webm/mp4, alpha of zwarte
  achtergrond passend bij V2-dark) als achtergrond van de knop/dropzone. Idle = rustige inwaartse drift; hover/drag =
  versnelde acceleratie (tweede loop of playbackRate omhoog); bij start-analyse = korte "inslag"-burst.
- **Productie:** Remotion-compositie in een losse `remotion/`-map; render naar `static/assets/analyse-accelerator/`.
  Meerdere varianten (idle, active, burst) + een statische poster-frame als fallback voor reduced-motion.
- **Reduced-motion + performance:** respecteer `prefers-reduced-motion` (toon poster-frame), pauzeer de loop als de
  view niet zichtbaar is, en houd de bestandsgrootte klein zodat het in de bundle past.
- **Responsive:** de loop schaalt mee met de knop; tekst ("Drop a DJ set" / "amount 100%"-stijl meter) blijft scherp
  als HTML-overlay bovenop de video, niet ingebakken.
- Higgsfield kan optioneel concept-frames/refs leveren voor de look; de uiteindelijke loop wordt met Remotion
  gerenderd zodat hij controleerbaar en herhaalbaar is.

### C5 - Redesign Brand-pagina

> Landt het netst NA A2 (dan is de data-laag er en tonen we het echte profiel per workspace).

- Heldere indeling: **Identiteit** (artist name, alias, avatar), **Visueel** (logo + positie/grootte, kleuren:
  primary/secondary/accent, watermark), **Typografie** (title/caption-fonts uit de bestaande font-bronnen),
  **Lower-third + CTA** (Spotify/Beatport-links, stijl), **Hashtags per platform**, **Templates** (Festival-clip,
  Studio-mix, Track-release: dupliceren/kiezen).
- **Live preview:** een mini-clip-preview die het profiel + actief template direct toont (leunt op de editor-renderer).
- Verwijdert de huidige versnippering (Brand-kit zit nu deels in Settings als "Brand kit" en "Brand-pack"); alles
  consolideert in de Brand-view.

### C6 - Redesign Calendar-pagina

> Landt het netst NA A3 (echte `scheduled_posts` ipv localStorage).

- Behoud van de bestaande Month/Week/Today + "Schedule a post" (Clip/Caption/Platforms), maar strakker:
  duidelijke maand-/weekraster, leesbare post-kaartjes met thumbnail + platform-iconen + tijd, drag-to-reschedule.
- **Lege staat** die uitnodigt ("Nog niets gepland, plan je eerste clip") ipv een leeg raster.
- Responsive: maandweergave op breed, automatische val naar agenda-lijst op smal.
- Status-badges (draft/scheduled) voorbereid op de latere Postiz-fase, maar publisht nu niets.

### C7 - Settings opschonen (gegroepeerd, minimaal, Advanced-inklap, jouw keuze)

De huidige Settings is een mix van Local-first, Watch folder, Profile, Workspace, Capabilities, Brand kit,
Output folder, Diagnostics, Brand-pack, Export/Import en Auto-mode. Voorstel:

**Zichtbaar (minimaal):**
- **Account** - artist name, email, log out.
- **Workspace** - naam, plan-badge, artiesten/leden (haakt op A1), workspace-switch.
- **Privacy** - local-first toggle/uitleg, airgap-optie (later).

**Onder "Advanced" (ingeklapt):**
- **Editor-defaults** - default ratio, caption-default aan/uit.
- **Export-defaults** - output-folder, captions inbakken default, watermark default.
- **Capabilities** - FFmpeg/VideoToolbox-status (read-only info).
- **Watch folder + Auto-mode** - folder kiezen, queue, pauzeren.
- **Opslag** - clean proxy clips, used/free disk.
- **Diagnostics** - download logs, copy as text, support email.

Brand-kit/Brand-pack verdwijnen uit Settings (verhuizen naar de Brand-view, C5). Wat feature-specifiek is en
logischer bij een pagina hoort (export-defaults) blijft onder Advanced staan zodat Settings niet leeg oogt maar wel
rustig. Geen functionaliteit verwijderen, alleen herordenen + inklappen.

### C8 - Backend-toevoeging voor Spoor C

- `/api/import-clip` (C2).
- `workspace_settings` jsonb op de `workspaces`-tabel of een losse tabel (panel-layout, editor-defaults,
  export-defaults per workspace). Komt erbij in een migratie binnen A1 of als losse migratie 010 na A1.
- Alle nieuwe endpoints workspace-scoped via `current_workspace_id()`.

---

## 4c. Editor-effecten en transitions (NIET bouwen, volledige spec voor post-beta, jouw keuze)

> Deze sectie specificeert de effecten zodat ze na beta direct bouwbaar zijn. Niets hiervan wordt nu geimplementeerd.
> Alle effecten hangen aan een clip of aan een tijdsbereik op de timeline, met een parameter-paneel rechts (de
> Clip/Cue-lijst-pane, C3). Implementatie is later via ffmpeg-filters in `cutter.py`.

Gemeenschappelijk model per effect: een effect is een entry op een timeline-track met `start`, `end`, `easing`
(linear/ease-in/ease-out/ease-in-out) en effect-specifieke parameters. UI: sleepbaar bereik op de timeline +
parameter-sliders in het rechterpaneel. Een live-preview-benadering (lichte CSS/Canvas-approximatie tijdens scrubben),
de echte render gebeurt bij export via ffmpeg.

| Effect | Parameters | UI-control | ffmpeg-richting (later) |
|---|---|---|---|
| Quick zoom-in | doel-zoom (1.0 tot 3.0x), duur (0.1 tot 2s), focuspunt (x/y), easing | slider zoom + duur, klikbaar focuspunt op preview | `zoompan` of `scale`+`crop` met geanimeerde expressie |
| Quick zoom-out | start-zoom, eind-zoom, duur, focuspunt, easing | idem | idem, omgekeerde expressie |
| Blur (box) | sterkte (0 tot 50), duur, in/out-fade | slider sterkte + duur | `boxblur` met geanimeerde sterkte |
| Gaussian blur | sigma (0 tot 30), duur, in/out-fade | slider sigma + duur | `gblur=sigma=` geanimeerd |
| Strobe | frequentie (Hz), intensiteit, kleur (wit/accent), bereik | slider Hz + intensiteit, kleurkiezer | frame-select / `geq` of overlay-flits op beat |
| Transition: cut | (geen) | klik | harde knip |
| Transition: crossfade | duur, curve | slider duur | `xfade=transition=fade` |
| Transition: zoom-punch | richting (in/uit), intensiteit, duur | slider | `xfade` + `zoompan`-combinatie |
| Transition: glitch/RGB-split | intensiteit, duur | slider | `rgbashift` + `noise` op overgangsframes |
| Beat-sync flash | aan/uit, gekoppeld aan gedetecteerde drops (analyzer.py) | toggle + intensiteit | overlay-flits op drop-timestamps |

Voorgestelde fasering voor de effecten (post-beta): eerst zoom-in/out + crossfade (hoogste impact, laagste risico),
dan blur/gaussian, dan strobe + beat-sync (raakt de analyzer), dan de zwaardere transitions (glitch/zoom-punch).

---

## 4d. Smoketest-protocol (E2E met echte set, Chrome MCP op dev-server, jouw keuze)

> Dit protocol geldt bij de BOUWFASE (na goedkeuring van dit plan). Regel: niet stoppen met aanpassen tot elke
> feature werkt EN het design strak oogt. Per fase wordt dit gedraaid; een fase is pas "groen" als alle relevante
> punten slagen, bewezen met screenshots.

**Opzet:** dev-server starten met `OMNI_DJ_PORT=<vrij>`, testen via Chrome MCP (DOM + screenshots). Eén echte DJ-set
door de volledige pipeline halen als end-to-end-bewijs.

**E2E-hoofdscenario (elke bouwfase minstens 1x volledig):**
1. Inloggen (V2-oranje), workspace kiezen/aanmaken.
2. Analyse: echte set inladen (Choose file + drag-drop), particle-accelerator-knop reageert, analyse draait lokaal,
   drops gedetecteerd.
3. Library: set verschijnt als project, clips zichtbaar, scoped op de actieve workspace.
4. Clips/Editor: clip openen in de CapCut-editor, preview speelt/scrubt, timeline trim werkt.
5. Import: een losse short importeren, opent direct in de editor, bewerkbaar.
6. Brand: profiel toepassen op de clip, preview toont logo/lower-third/CTA.
7. Export: met captions inbakken, MP4 op schijf, captions zichtbaar in het frame.
8. Calendar: "Plan in Calendar" vanuit export, draft verschijnt, overleeft refresh.

**Per-view design- en responsive-checks (sectie 7b breekpunten):** elke view getest op smal (rond 900px), midden en
breed; sidebar collapse; editor-splitters slepen en groottes onthouden; geen overflow/afgekapte controls;
reduced-motion toont poster ipv accelerator-loop.

**Data-isolatie-checks (zodra A1 staat):** alle workspace-scoped data getest met 2 users x 2 workspaces; geen enkele
rij van workspace A zichtbaar in workspace B (clips, brand, scheduled_posts, settings).

**Sync-scenario (Spoor D, zie sectie 4e):** losse video (camera/GoPro) + losse schone audio van dezelfde set
importeren via "Import video + audio sync"; tool synct volautomatisch, toont confidence; gemuxede video gaat de
normale analyse in; drops gedetecteerd op de schone audio; in de editor staat de camera-audio als losse inmix-track
met werkende volume + highpass. Falende/zwakke match valt terug op de handmatige waveform-view.

---

## 4e. SPOOR D - Import video + audio sync (losse camera + schone audio matchen)

> Nieuwe feature op verzoek van Sjuul. Doel: een DJ neemt zijn set op met camera/GoPro (beeld + troebel boordgeluid)
> en heeft daarnaast een schone audio-opname (mengtafel/recorder). De tool matcht beide op waveform/transients,
> legt de schone audio onder het beeld, en draait daarna de NORMALE drop-analyse op de schone audio.
>
> **Harde regel:** deze feature mag de bestaande flow NIET verstoren. Het is een tweede, optionele ingang op de
> Analyse-page naast de bestaande dropzone. Wie een losse set heeft, merkt er niets van. De sync-stap is een
> sub-flow die VOOR de bestaande analyse-pipeline hangt en daar een gewoon (gemuxed) videobestand aan doorgeeft,
> zodat analyzer.py/cutter.py ongewijzigd blijven.

### D1 - Plaatsing en flow (jouw keuze: tweede knop op Analyse)

- Op de Analyse-page komt naast de normale dropzone een tweede knop: **"Import video + audio sync"**.
- Klikken opent een **sync-sub-flow** (modal of inline paneel), niet een aparte sidebar-pagina, zodat de
  Analyse-page de enige ingang voor "een set analyseren" blijft.
- Stappen in de sub-flow:
  1. Video kiezen (camera/GoPro mp4/mov) + schone audio kiezen (wav/mp3/m4a). Beide lokaal, workspace-scoped.
  2. Tool extraheert het boordgeluid uit de video en cross-correlateert dat tegen de schone audio (transient/
     waveform-match) -> bepaalt offset, volautomatisch.
  3. Drift-check + automatische drift-correctie (zie D2) + confidence-score (zie D4).
  4. Schone audio wordt onder de video gemuxed met de gevonden offset; camera-audio blijft als tweede spoor bewaard.
  5. Het resulterende videobestand gaat de BESTAANDE analyse-pipeline in (drops/buildups op de schone audio).
- Vanaf stap 5 is alles identiek aan de huidige tool: Library, Clips, Editor, Export werken zoals nu.

### D2 - Sync-logica (jouw keuze: volautomatisch + automatische drift-correctie + waarschuwing)

- **Offset:** cross-correlatie van de twee audiosporen (gedownsampled envelope/onset-functie via librosa, die al in
  de stack zit) levert de begin-offset. Volautomatisch, geen verplichte handmatige stap.
- **Drift-correctie:** de tool meet of begin- en eind-offset verschillen (camera- en recorder-klok lopen uiteen over
  lange sets). Bij meetbare drift wordt de schone audio minimaal hersampled/opgerekt zodat begin EN eind kloppen.
- **Waarschuwing:** als de drift buiten een veilige marge valt of de correctie groot is, toont de tool een melding
  ("we hebben X seconden drift gecorrigeerd over de set, check het eind") in plaats van stilletjes door te gaan.
- Implementatie zit in een nieuw `audio_sync.py` (los van analyzer.py), zodat de bestaande analyse onaangeroerd blijft.

### D3 - Output (jouw keuze: schone audio onder de video muxen + camera-audio behouden als inmix-track)

- De sync produceert EEN nieuw videobestand met de schone audio als hoofdspoor (offset + drift toegepast), via
  ffmpeg (de bestaande static binaries). Downstream blijft dus "gewoon een videobestand".
- Het oorspronkelijke **camera-boordgeluid wordt behouden als tweede audiospoor** (of als sidecar-bestand met de
  offset), specifiek zodat de editor er een crowd/ambient-inmix van kan maken (zie D5). Dat is jouw doel:
  crowdnoise terugmengen voor sfeer.
- Bestandsgrootte-afweging: tweede spoor kost ruimte; we houden het bij het origineel (geen dubbele cloud-opslag,
  consistent met de local-first data-laag-keuze in sectie 2).

### D4 - Fail-gedrag (jouw keuze: confidence-score + handmatige terugval)

- De sync toont een **match-zekerheid** (confidence uit de cross-correlatie-piek).
- Bij hoge zekerheid: direct door naar mux + analyse (volautomatisch, zoals gewenst).
- Bij lage zekerheid (stilte aan het begin, te veel ruis, verkeerd bestand): val terug op een **mini-waveform-view**
  waar de gebruiker de twee sporen handmatig over elkaar schuift tot ze kloppen, daarna bevestigen. Dit voorkomt
  stille out-of-sync resultaten zonder de volautomatische ervaring in de weg te zitten bij goede opnames.

### D5 - Editor/timeline-toevoegingen (jouw keuze: sub-flow + optionele track)

- De sync zelf gebeurt in de sub-flow (D1). De editor blijft voor de gewone gebruiker gelijk.
- Voor sync-projecten krijgt de timeline een **optionele losse audio-track** met het camera-boordgeluid, met:
  - **Inmix-volume** (0 tot 100%) per clip (jouw keuze 1): hoeveel crowd/ambient je terugmengt onder de schone audio.
  - **Highpass-filter** (jouw keuze 3): een simpele hoogdoorlaat zodat je alleen de crowd/ambient eruit haalt en de
    troebele boord-kick wegfiltert. Twee controls: cutoff-frequentie + aan/uit.
- De offset is op dit punt al vastgelegd; de track is puur voor inmix, niet om opnieuw te synchroniseren. (Een
  achteraf-nudge kan later, post-beta, als de effecten-fase uit sectie 4c wordt gebouwd.)
- Keyframed inmix over tijd valt bewust in de post-beta effecten-fase (sectie 4c), niet in deze build.

### D6 - Data-laag en plaatsing in de fasering

- Sync-import landt lokaal in de workspace-map (`workspaces/<id>/sync/`), met een `clips`-metadata-rij (A1) zodra de
  data-laag staat; tot die tijd lokaal-only, net als Import (C2).
- Nieuwe backend: `/api/sync-import` (workspace-scoped, hergebruikt upload-validatie + `_path_within_home()`),
  plus `audio_sync.py` voor de matching/mux. Geen wijziging aan analyzer.py/cutter.py voor de sync zelf;
  cutter.py krijgt later alleen de inmix-track-render (volume + highpass) erbij voor export.
- Spoor D is grotendeels onafhankelijk van A, maar de inmix-track in de editor leunt op de CapCut-editor (C3).
  Aanbeveling: bouw D na C3 (editor-layout) zodat de extra audio-track een plek heeft.

### D7 - Mogelijke issues in deze build (eerlijk, vooraf benoemd)

- **Zwakke of dubbelzinnige match:** als het begin van de opname stil is, of de camera-mic vol staat met
  ruis/wind, of er repetitieve loops in de muziek zitten, kan cross-correlatie een verkeerde piek kiezen.
  Mitigatie: confidence-score + handmatige terugval (D4), en matchen op de onset-envelope ipv ruwe samples.
- **Clock drift over lange sets:** zonder drift-correctie loopt het eind uit sync. Gedekt door D2, maar de correctie
  zelf kan bij zware drift hoorbare artefacten geven; daarom de waarschuwing.
- **Variabele framerate (VFR) van GoPro/telefoon:** VFR-video geeft tijdsafwijkingen bij muxen. Mitigatie: bij import
  detecteren en eventueel naar constante framerate normaliseren voor het muxen.
- **Verschillende sample-rates** (48kHz video-audio vs 44.1kHz recorder): resamplen voor correlatie en mux, anders
  schuift de offset.
- **Lange bestanden + geheugen:** een 2-uur-set in het geheugen cross-correleren is zwaar. Mitigatie: downsample naar
  een envelope, correleer op lage resolutie, verfijn lokaal rond de piek (coarse-to-fine). Sluit aan bij de bekende
  large-file-pipeline-valkuil uit de HANDOVER.
- **A/V-codec-mismatch bij muxen:** niet elke audio past zonder re-encode in elke container. Mitigatie: ffmpeg
  re-encode naar een veilig profiel waar nodig, niet alleen stream-copy.
- **Tweede audiospoor + bestandsgrootte:** behouden boordgeluid vergroot het bestand; helder communiceren en optie
  om het weg te laten als de gebruiker geen crowd-inmix wil.
- **Verstoring van de bestaande flow:** grootste product-risico. Mitigatie: sync is een aparte ingang die een gewoon
  videobestand oplevert; de bestaande analyse/editor/export-code blijft ongewijzigd (alleen de optionele
  inmix-track-render komt erbij). De smoketest test expliciet dat de normale losse-set-flow onveranderd werkt.

---

## 5. Kruisende aandachtspunten (waar A, B, C en D elkaar of de bestaande staat raken)

- **B-auth (Electron + dynamische poort):** Supabase password-reset + OAuth-redirects gebruiken nu
  `127.0.0.1:5555`. Met een vrije poort in Electron moeten redirects mee. Keuze bij B1: vaste poort behouden met
  conflict-fallback, of een custom protocol (`omnidj://`) registreren. Te beslissen bij implementatie, niet nu.
- **Host-gate (sessie 67):** `_security_gate` staat alleen `127.0.0.1:5555`/`localhost:5555` toe. Een Electron-
  venster op een andere poort vereist `OMNI_DJ_PORT=<poort>` mee te geven aan de backend (al ondersteund). Belangrijk
  bij B0/B1 testen.
- **Workspace-scope + bestaande security:** `current_workspace_id()` komt NAAST de bestaande Host-allowlist + CSRF +
  `_path_within_home()` whitelist. Niet vervangen, aanvullen.
- **Sessie 69 nog niet gecommit:** de file-picker-fix (NSOpenPanel) en V1-naar-V2-uitfasering zitten al in
  `app.py` + `index.html` + `entitlements.plist` + `OmniDJ.spec` + `requirements.txt`. Alle nieuwe code uit dit plan
  stapelt daar bovenop. Eén gezamenlijke commit aan het eind (sectie 8).

---

## 6. Fasering, volgorde en realistische schatting

| Fase | Spoor | Dev-tijd (1 dev) | Blocker / vereist eerst |
|---|---|---|---|
| A1 - Multi-tenant fundament | A | 3 tot 4 weken | niets (start hier voor Spoor A) |
| A2 - Brand-architectuur | A | 2 weken + 1 tot 2 dagen per extra template | A1 groen |
| A3 - Content Calendar | A | 2 tot 3 weken | A1 groen (A2 aanbevolen eerst) |
| B0 - Electron prototype | B | enkele dagen | niets (mag direct, parallel aan A1) |
| B1 - Lifecycle + polish | B | 1 tot 2 weken | B0 |
| B2 - Packaging macOS | B | 1 week | B1 |
| B3 - Signing macOS | B | enkele dagen | B2 + Apple Developer (al geregeld) |
| B4 - Windows | B | 2 tot 3 weken | B2 |
| C1 - Sidebar + Editor-tab | C | enkele dagen | niets (mag direct) |
| C2 - Import-knop | C | 3 tot 5 dagen | C1; volle data-laag pas na A1 |
| C3 - CapCut sizeable editor | C | 1 tot 2 weken | niets (mag direct); layout-persistentie per workspace pas na A1 |
| C4 - Analyse-knop (Remotion accelerator) | C | 3 tot 5 dagen render + inbouw | niets (mag direct, losgekoppeld) |
| C5 - Brand-redesign | C | 1 week | A2 aanbevolen eerst |
| C6 - Calendar-redesign | C | 1 week | A3 aanbevolen eerst |
| C7 - Settings opschonen | C | 3 tot 5 dagen | niets (mag direct) |
| D1-D4 - Sync sub-flow + logica | D | 2 tot 3 weken | niets voor de kern; lokaal-only tot A1 |
| D5 - Inmix-track in editor | D | 1 week | C3 (editor-layout) aanbevolen eerst |
| D6 - Sync data-laag scope | D | enkele dagen | A1 (voor workspace-scope van sync-clips) |

**Aanbevolen marsroute:** start A1 en B0 tegelijk, en pak uit Spoor C de losgekoppelde stukken er meteen bij
(C4 Analyse-knop, C3 editor-layout, C1/C2 Editor-tab + Import, C7 Settings) want die raken de data-laag niet.
A1 is het zware kritieke pad; B0 levert snel een zichtbaar "echte app"-resultaat. Zodra A1 groen is: A2 gevolgd door
C5 (Brand-redesign), en A3 gevolgd door C6 (Calendar-redesign), zodat we elke view maar één keer aanraken.
Spoor D (sync-import) bouw je na C3 (de editor moet de inmix-track kunnen huisvesten); de sync-kern (D1-D4) mag
eerder als losse sub-flow want die levert gewoon een videobestand aan de bestaande pipeline.

**Bewust BUITEN dit plan (latere fasen, blijven in de bron-plannen staan):**
Postiz social-publishing, ads-platform/orchestrator, geld-flow-research (Model A/B/C), mobile companion,
watch-folder auto-draft (let op: `watch_folder.py` bestaat al als bouwsteen, maar de auto-draft-pipeline is geen
onderdeel van dit plan).

---

## 7. Risico's + verplichte verificatie

| Risico | Impact | Mitigatie |
|---|---|---|
| Workspace data-isolatie-bug (A ziet data van B) | Catastrofaal | RLS in version control, **verplichte cross-account test-matrix** (min. 2 users x 2 workspaces, 20-tests-stijl zoals sessie security-audit) vóór A1-oplevering |
| Data-migratie corrumpeert bestaande lokale content | Hoog | Idempotent migratie-script, DRY-RUN-modus eerst, backup van DATA_DIR + Supabase-dump vóór run |
| Brand-asset-upload lekt tussen workspaces | Hoog | per-workspace storage-pad + RLS op `dj_profiles`, test in cross-account-matrix |
| Electron zombie Python-proces | Hoog | expliciet in B1 (before-quit + tree-kill), test-checklist punt 10 uit Electron-plan |
| Migratie-nummer-botsing | Middel | dit plan start bij 005; check `list_migrations` op het live project vóór elke nieuwe migratie |
| Scope-creep (alles tegelijk) | Hoog | strikte dependency-regels sectie 1, A2/A3 niet vóór A1, Postiz/ads expliciet buiten scope |
| Sync verstoort bestaande analyse-flow | Hoog | sync is aparte ingang die een gewoon videobestand oplevert; analyzer.py/cutter.py ongewijzigd; smoketest test losse-set-flow expliciet (sectie 4e D7) |
| Sync-mismatch / drift / VFR levert out-of-sync resultaat | Middel tot Hoog | confidence-score + handmatige terugval (D4), drift-correctie + waarschuwing (D2), VFR-normalisatie + resample bij import (D7) |

**Verplichte verificatiestap per fase:** elke fase levert pas op als de cross-account/cross-workspace test groen is
EN de bestaande functionaliteit (single-user, export met captions) onveranderd werkt. Voor A1 specifiek een
security-audit-pass (data-isolatie) door een subagent, gezien de catastrofale impact-categorie.

### 7b. Responsive breekpunten (voor Spoor C smoketest)

Elke herontworpen view wordt op deze breedtes getest via Chrome MCP (window resize + screenshot):

| Breekpunt | Breedte | Verwacht gedrag |
|---|---|---|
| Smal | rond 900px (Electron-venster verkleind) | sidebar collapse naar iconen; editor-panes stapelen verticaal met tabs; geen overflow |
| Midden | rond 1280px | standaard layout, alle panes zichtbaar, comfortabel |
| Breed | 1600px en hoger / ultrawide | content begrensd op max-breedte waar nodig, geen uitgerekte controls |

Extra editor-checks: splitters slepen binnen min/max, groottes onthouden na reload (per workspace na A1), preview
groter/kleiner maakt timeline korter/langer. Reduced-motion toont de poster-frame ipv de accelerator-loop.

---

## 8. Git / commit-strategie (sessie 69 + dit plan samen)

Sjuul rondt sessie 69 niet los af maar neemt alles mee in EEN gezamenlijke commit zodra een logisch blok klaar is.
Praktisch betekent dat:

- Werk per fase op een feature-branch (`feature/multi-tenant`, `feature/brand`, `feature/calendar`,
  `feature/electron`, `feature/redesign-ux`, `feature/video-audio-sync`).
- De sessie-69-wijzigingen (`app.py`, `static/index.html`, `entitlements.plist`, `OmniDJ.spec`,
  `requirements.txt`) zitten al in de working tree en gaan mee in de eerste commit die Sjuul maakt.
- Pas een gesignde rebuild + DMG-naar-R2 NA de smoke-test van de file-picker-fix (sessie 69 stap 4-5 uit HANDOVER).
  Dat blijft een harde voorwaarde: de DMG mag niet naar R2 zonder dat "Choose file" zonder hang werkt.
- Sandbox kan niet committen; Sjuul doet git zelf (PAT-auth, `origin` = `sjuulstudios/omni-dj-landing-by-MONO-LABS`,
  branch `main`).

---

## 9. Wat ik van Sjuul nodig heb voor we Spoor A beginnen

1. **Akkoord op de data-laag-keuze (sectie 2):** brand-metadata + clip-metadata + scheduled_posts naar Supabase,
   media blijft lokaal. Dit is de fundamentele beslissing.
2. **Workspace-naam in UI-copy:** "Workspace" / "Roster" / "Artist" / "Project". De chips tonen nu "Workspace" +
   "Artist name"; bevestigen of dat de definitieve termen zijn.
3. **Bevestiging Studio-limiet = 3 workspaces** (matcht de bestaande UI-paywall). FREE/Solo = 1.
4. **Go voor start-volgorde:** A1 + B0 parallel starten?

Voor Spoor B apart is verder niets nodig dan B0 zelf (Apple Developer is al geregeld, sessie 66).

**Voor Spoor C (redesign + UX) heb ik bevestigd van je gekregen (verwerkt in dit plan):**
- Editor-layout: CapCut-stijl drie sizeable panes (C3).
- Panel-persistentie: sleepbaar + onthouden per workspace (C3/C8).
- Analyse-knop: Remotion-gerenderde particle-accelerator loop (C4).
- Editor-tab: herstel laatste sessie, anders Library-projectkiezer + clip-kiezer eerst (C1).
- Import: video + audio, lokaal in de workspace (C2).
- Settings: gegroepeerd in secties, minimaal, rest onder Advanced-inklap (C7).
- Effecten: volledige spec per effect, niet nu bouwen (sectie 4c).
- Bouwen: eerst dit plan goedkeuren, daarna de bouw-en-test-lus per fase (sectie 4d).
- Testmethode: volledige E2E met een echte set via Chrome MCP op de dev-server (sectie 4d + 7b).

**Nog 1 open keuze voor Spoor C:** de tool-keuze voor de concept-look van de accelerator (alleen Remotion, of
eerst Higgsfield-refs als inspiratie). Niet blokkerend; te beslissen bij C4.

**Voor Spoor D (video + audio sync) heb ik bevestigd van je gekregen (verwerkt in dit plan):**
- Plaatsing: tweede knop "Import video + audio sync" op de Analyse-page, als sub-flow (D1).
- Sync-logica: volautomatisch + automatische drift-correctie + waarschuwing bij grote drift (D2).
- Output: schone audio onder de video muxen; camera-audio behouden als inmix-track (D3/D5).
- Inmix-controls: volume-slider + highpass-filter per clip (D5).
- Fail-gedrag: confidence-score + handmatige waveform-terugval bij zwakke match (D4).
- Editor: sub-flow + optionele losse audio-track in de timeline (D5).

---

## 9b. KRITISCHE REVIEW v1.3 (sessie 71, 2026-06-02) - geverifieerd tegen de live code

> Deze sectie is toegevoegd na een code-grondige review (auth/security, pipeline, frontend) tegen de echte
> live staat. Het corrigeert aannames in v1.0-v1.2 die de bouw zouden laten ontsporen of de data-isolatie
> onveilig zouden maken. De fasering in sectie 1/6 blijft staan, maar A1 wordt anders gebouwd dan beschreven.
> Alles geverifieerd op `app.py` (7140 r), `auth.py` (603 r), `cutter.py` (2377 r), `static/index.html` (26075 r)
> en het live Supabase-project `lbabsffxefkrxwzkbzar`.

### CORRECTIE 6 (KRITIEK - verandert A1): RLS beschermt NIETS zoals het plan het nu beschrijft

De backend draait ALLE profiel-, quota- en data-queries via `supabase_admin` (de **service_role-key**, `auth.py:53`).
Service_role **omzeilt RLS volledig**. Vandaag is dat veilig omdat de app single-tenant is en eigendom in
app-code wordt gecheckt (`_require_job_access`, `app.py:1926`). Maar het plan (A1/A2/A3) gebruikt RLS-policies
("een rij is leesbaar als de user member is van die workspace") als DE isolatie-grens tussen workspaces. Als de
nieuwe content-tabellen ook via `supabase_admin` worden bevraagd, doet die RLS **niets** en hangt de hele
workspace-isolatie aan een handmatige `workspace_id`-check op ELK endpoint. Eén vergeten check = data-lek tussen
artists (catastrofale categorie uit sectie 7).

Bijkomend: de **gesignde bundle bevat de service_role-key niet** (bewust, `runtime_config.py:21-28`); privileged ops
lopen daar via edge functions. De nieuwe tabellen hebben geen edge functions. Dus in de bundle is er sowieso geen
service_role-pad naar de nieuwe tabellen.

**Fix (verplicht voor A1):** de nieuwe workspace-gescopete content-tabellen (`workspaces`, `workspace_members`,
`clips`, `dj_profiles`, `dj_templates`, `scheduled_posts`, `workspace_settings`) worden bevraagd via de **anon-client
gebonden aan de JWT van de request** (`Authorization: Bearer <user-jwt>` op de PostgREST-call), NIET via
`supabase_admin`. Dan is RLS de echte grens en werkt het ook in de bundle (anon-key wordt al meegeleverd).
- Nieuwe helper `_user_supabase()` in `app.py`: maakt/hergebruikt een anon-client en zet de access_token van de
  ingelogde user erop (supabase-py: `postgrest.auth(jwt)` of een per-request client). Alle workspace-content-queries
  gaan hierdoorheen.
- `supabase_admin` blijft ALLEEN voor wat RLS moet omzeilen: profiel/role/billing-writes en audit-logs.
- `current_workspace_id()` blijft als extra app-laag (membership-verificatie + 403), maar is nu een tweede slot
  bovenop RLS, niet de enige sleutel.
- Defense-in-depth: RLS-policy + `current_workspace_id()`-check + de bestaande Host/CSRF-gate.

### CORRECTIE 7: migratie-nummering en -historie kloppen niet 1-op-1

De live migratie-historie kent maar twee entries (`20260511095737`, `20260601063344`); de lokale bestanden
`001`-`004` zijn een aparte naamconventie en zitten niet (allemaal) in die historie - ze zijn out-of-band toegepast.
Conclusie: de tabellen/kolommen staan WEL live (geverifieerd via `list_tables`), de historie-tabel is alleen geen
betrouwbare bron. Daarom:
- Verifieer vóór elke nieuwe migratie de ECHTE schema-staat met `list_tables`, niet de historie-tabel.
- Houd version-controlled bestanden `005+`, maar pas ze toe via de Supabase-MCP (die timestamp't zelf); de
  lokale nummering is puur voor ons leesbaarheid.
- Test elke migratie EERST op een Supabase-branch (`create_branch`) en pas daarna op `main`. De cross-account
  audit (sectie 7) draait op de branch vóór merge.

### CORRECTIE 8: pipeline-koppelingen die stilletjes breken bij per-workspace mappen

- **cutter.py kent DATA_DIR niet.** Het lost fonts/brand op via zijn eigen `BASE_DIR`-spiegel. Zodra content naar
  `workspaces/<id>/` verhuist, faalt font/brand-resolutie STIL. Fix: geef opgeloste paden expliciet als argument mee
  aan de cutter-functies (`process_clips`, export-functies); cutter.py mag geen pad zelf raden.
- **`job_history.json`, `OUTPUT_DIR` en `/api/exports` zijn globaal, niet workspace-gescoped.** `/api/exports`
  (`app.py:6503`) loopt heel `OUTPUT_DIR` af. Vóór per-workspace mappen live gaan, moeten history + exports
  workspace-bewust worden, anders lekt/mislijst de ene workspace de clips van de andere. Dit is werk binnen A1, niet
  "erbij".
- **Data-migratie van de platte DATA_DIR** onder `workspaces/<default_id>/` is idempotent + dry-run + backup
  (zoals sectie 7 al eist); maar het verplaatst ook job-snapshots (`OUTPUT_DIR/<job>/job.json`) en de
  brand_kit-assets. Het migratiescript moet die mee verhuizen, niet alleen de top-level mappen.

### CORRECTIE 9: frontend-injectie van de workspace-header dekt 6 losse fetch-calls niet

Er is een centrale wrapper `api(path, opts)` (`index.html:11335`) - daar komt de `X-Omni-Workspace`-header in
(net vóór de `fetch` op ~11348). MAAR er zijn minstens 6 rauwe `fetch()`-calls die de wrapper omzeilen
(auth-refresh 11283, clip-filmstrip 16135, clip-overlays 17305, brand-kit/watermark 17374, debug/logs 24152+24179,
forgot-password 25026). Die moeten OF door `api()` gerouteerd worden OF handmatig de header krijgen, anders zijn die
calls niet workspace-gescoped. Auth-refresh en forgot-password hoeven geen workspace-header (pre-auth), maar
clip-filmstrip/overlays/watermark WEL.

### CORRECTIE 10 (design/logica): de editor is GEEN CapCut-layout en is niet sleepbaar

De huidige editor (`#view-editor`, `index.html:9743`) is een VAST 3-koloms grid (`340px | 1fr | 88px`,
`.ed-body` regel 1163): links cue-lijst, midden preview, rechts tool-rail. Geen sleepbare splitters, en NIET de
C3-layout (preview + cue-lijst boven, volle-breedte timeline onder). C3 is dus een echte layout-herbouw met risico
voor de werkende editor, geen tweak. Aanpak om de werkende trim/minimap-logica niet te slopen:
- Bouw de nieuwe CSS-grid + splitters als een NIEUWE laag rond de bestaande bouwstenen (trim-handles `#tl-trim-in/out`
  10030, minimap `.tl-minimap` 1480, text/track-resize). Hergebruiken, omkaderen, niet herschrijven.
- Zet de nieuwe layout achter een lichte flag of bouw hem naast de oude en wissel pas om als de E2E-editor-test
  groen is (preview speelt, trim werkt, export uit de editor werkt).
- De drift-particles (C4) zijn nu CSS (`index.html:821-861`), geen canvas. De Remotion-loop vervangt die als
  achtergrond; houd een poster-frame als `prefers-reduced-motion`-fallback en let op bundle-grootte (static/ wordt
  meegebundeld in de .app).

### Aangepaste bouwvolgorde (vervangt de "Aanbevolen marsroute" voor de uitvoering)

A1 NIET blind starten. De juiste volgorde, met de hard-quality-gate "analyse/edit/export + auth blijven groen":

0. **Plan + fundament op papier en op een branch** (deze sessie deels): deze v1.3-correcties; migraties `005-009`
   geschreven met de anon+JWT+RLS-architectuur (Correctie 6); een security-audit-harness (2 users x 2 workspaces)
   klaar; alles op een Supabase-branch, niets op `main`.
1. **Veilige, ontkoppelde slice + E2E** (raakt auth/data-laag niet): C7 (Settings opschonen), C1 (Editor-tab),
   C2 (Import + `/api/import-clip`, hergebruikt bestaande upload-validatie + `_path_within_home`), C3 (CapCut-layout
   omkaderend). Eventueel B0 (Electron-prototype, geisoleerd). Elke stap E2E groen op de dev-server.
2. **A1 met anon+JWT+RLS** + verplichte 2x2 cross-account-audit op de branch; pas merge naar `main` als de audit
   groen is. Dan pas `current_workspace_id()` op de bestaande content-endpoints aanzetten.
3. **A2 -> C5** (Brand) en **A3 -> C6** (Calendar), elke view 1x aanraken.
4. **Spoor D** na C3 (de inmix-track heeft de editor-layout nodig); D1-D4 mag als losse sub-flow eerder.

### Quality-gate per slice (operationaliseert sectie 4d voor de "main functies + auth")

Elke opgeleverde slice bewijst, vóór "groen", op de dev-server (`OMNI_DJ_PORT=<vrij>`, Chrome MCP):
- **Auth:** login (oranje V2), token-refresh na 401, logout. Niet stuk.
- **Analyse:** echte set in -> drops gedetecteerd (geen duplicate-clips-regressie).
- **Edit:** clip opent in editor, preview speelt/scrubt, trim werkt.
- **Export:** met captions ingebakken -> MP4 op schijf, captions zichtbaar, 0-based `clip_indices` (geen
  off-by-one-regressie).
- **A1-only extra:** geen enkele rij van workspace A zichtbaar in workspace B (clips, brand, scheduled_posts,
  settings) - bewezen met de 2x2-matrix.

---

## 10. Changelog

- 2026-06-02 - v1.0 - Gecombineerd plan na verificatie van de live staat (sessie 70). Corrigeert de
  data-architectuur-aannames uit de drie bron-plannen (Supabase bevat alleen profiles+audit_logs; content is
  lokaal; migraties starten bij 005; multi-artist-UI bestaat al client-side; calendar-shell bestaat al). Twee sporen:
  A (multi-tenant -> Brand -> Calendar) en B (Electron parallel). Postiz/ads/mobile bewust buiten scope. Sessie 69
  blijft open, gaat mee in de gezamenlijke commit.
- 2026-06-02 - v1.1 - Spoor C (redesign + UX) toegevoegd op verzoek van Sjuul: nieuwe sidebar met eigen Editor-tab
  (C1), Import-knop voor losse short/audio lokaal in workspace (C2), CapCut-stijl drie sizeable panes editor met
  per-workspace panel-persistentie (C3), Analyse-knop als Remotion particle-accelerator (C4), Brand-redesign (C5),
  Calendar-redesign (C6), Settings opgeschoond in secties + Advanced-inklap (C7), backend-toevoegingen (C8).
  Volledige effecten-spec voor post-beta toegevoegd (4c: zoom/blur/gaussian/strobe/transitions met parameters +
  ffmpeg-richting). E2E-smoketest-protocol met echte set via Chrome MCP (4d) + responsive breekpunten (7b).
  Fasering-tabel uitgebreid met C-fasen, branch `feature/redesign-ux` toegevoegd. Alle ontwerpkeuzes van Sjuul
  verwerkt (sectie 9).
- 2026-06-02 - v1.2 - Spoor D (video + audio sync) toegevoegd op verzoek van Sjuul: tweede knop op de Analyse-page
  voor het matchen van losse camera-video + schone audio op waveform (D1), volautomatische sync met drift-correctie +
  waarschuwing (D2), schone audio onder de video gemuxed met behoud van camera-audio (D3), confidence-score +
  handmatige waveform-terugval (D4), optionele inmix-track in de editor met volume + highpass voor crowdnoise (D5),
  data-laag/plaatsing (D6) en een eerlijke issues-paragraaf (D7: zwakke match, drift, VFR, sample-rates, geheugen bij
  lange sets, codec-mux, bestandsgrootte, flow-verstoring). Nieuw `audio_sync.py` + `/api/sync-import`, analyzer.py/
  cutter.py blijven ongemoeid. Smoketest (4d) + risico-tabel (7) + fasering + sporen-overzicht + branch
  `feature/video-audio-sync` bijgewerkt. Sync mag de bestaande losse-set-flow niet verstoren; dat wordt expliciet
  getest.
- 2026-06-02 - v1.3 - Kritische code-review tegen de live staat (sessie 71, sectie 9b). Tien correcties, waarvan
  KRITIEK: de backend draait alles via de service_role-key en omzeilt RLS, dus de workspace-isolatie uit A1/A2/A3
  moet via de anon-client + user-JWT (RLS wordt dan de echte grens; werkt ook in de bundle). Verder: migratie-historie
  is geen betrouwbare bron (verifieer schema live, test op branch), cutter.py kent DATA_DIR niet (paden expliciet
  meegeven), job_history/`/api/exports` moeten workspace-bewust worden, 6 rauwe fetch-calls omzeilen de api-wrapper,
  de editor is een vast 3-koloms grid (C3 = echte herbouw, omkaderend), en een per-slice quality-gate die
  auth/analyse/edit/export groen houdt. A1 wordt NIET blind gestart; aangepaste bouwvolgorde toegevoegd.
