# PLAN — Redesign Fase 5 + Analyse/Library herstructurering + Multi-artist workspace

**Datum:** 2026-05-27 (v3 — Sjuul's antwoorden op beslispunten + concrete content-wijzigingen verwerkt)
**Sessie:** 54 (volgend op sessie 53)
**Product:** Omni DJ (codebase nog Omni DJ)
**Status:** voorstel, wacht op akkoord Sjuul

---

## 0. Doel in één zin

Alle nog niet-geraakte views naar v2 brengen, de sidebar herstructureren naar **Analyse** (alle intake-routes op één plek) + **Library** (Projects-overzicht, vervangt Clips als top-level), en bovenin de sidebar een **Supabase-stijl workspace+artist switcher** introduceren waarmee Studio-plan gebruikers tussen meerdere artiesten kunnen schakelen.

---

## 1. Wat verandert t.o.v. v2 van dit plan (jouw 9 wijzigingen)

| # | v2 | v3 (huidig) |
|---|---|---|
| 1 | Artist-chip placeholder "Omni DJ" | **"Artist name"** (placeholder, alle "Omni DJ"-refs weg) |
| 2 | Analyse-page sub "Drop, open, or auto-watch — we find the drops..." | **"Drag & drop or select your DJ-set."** |
| 3 | Dropzone met "— up to 4 hours" + `[Choose file]`-knop | Dropzone strak: alleen "Drop a set here" + formats (geen knop, geen "up to 4 hours") |
| 4 | "Or use:" label + 4 tiles incl. "Choose file / Local picker" | Geen "Or use:"-label; "Choose file" tile **weg** (duplicaat). Tiles overgebleven: Watch folder + Dropbox + Drive |
| 5 | BPM-meter / "144 BPM" zichtbaar in UI | **weg** (uit headers/tiles) |
| 6 | Capabilities-sectie in Settings (ffmpeg/Demucs/VideoToolbox/MPS) | **Capabilities weg uit Settings** (front-end). Backend-detection blijft. |
| 7 | Storage & large files-sectie in Settings | **Storage & large files weg uit Settings** (front-end). Proxy-cleanup-functie blijft beschikbaar via console/dev. |
| 8 | Artist-dropdown header "Artists in this workspace" | **"Artists"** |
| 9 | Studio = onbeperkt artists | **Studio = max 3 artists**. Stripe price-ID hergebruiken (bestaat al). |

---

## 2. Aanleiding

Sessies 45-48 hebben sidebar, dashboard/clips-grid, editor/timeline en 5 modals naar v2 gebracht. 0 regressies, premium dark-mode look. Maar **6 views + 2 UI-fragmenten** zijn nog in oude warm-amber Playfair-stijl:

| # | Element | Locatie | Stijl nu |
|---|---|---|---|
| 1 | `#view-home` | regel 6060 | Playfair eyebrow + warm-amber chips + "View all →" links |
| 2 | `#view-upload` | regel 6107 | Eyebrow "Drop a set" + Playfair italic + warm dropzone |
| 3 | `#view-processing` | regel 6175 | Eyebrow "Working on your set" + Playfair italic |
| 4 | `#view-style` (Brand Stack) | regel 6849 | Playfair section-titles |
| 5 | `#view-publish` | regel 7090 | Playfair section-titles |
| 6 | `#view-settings` | regel 7136 | Playfair eyebrow + italic op "Local-first and yours.", "Watch folder", "Brand kit" |
| 7 | "CLIP PICKER · Pick the keepers" hero | boven dashboard | Playfair italic + uppercase eyebrow |
| 8 | Workspace-knop linksboven sidebar | huidige sidebar | "MONO LABS · Pro plan" statisch label, niet klikbaar, geen artist-laag |

`reset-password.html` blijft bewust uit scope (standalone landingspagina).

---

## 3. Informatie-architectuur — nieuwe indeling

### Sidebar (nieuwe volgorde)

```
┌─────────────────────────────────────┐
│ ⚡ MONO LABS   [FREE] ▾          │   ← workspace + plan chip (klikbaar)
│ ⏵ Omni DJ ▾                   │   ← artist-picker (klikbaar)
├─────────────────────────────────────┤
│                                       │
│ ▤  Analyse        ← NIEUW (top-level) │
│ ▦  Library         ← vervangt Clips   │
│ 🎨  Brand                              │
│ 📤  Social                              │
│ 🗓️  Calendar                            │
│ 📊  Insights                            │
│                                       │
├─────────────────────────────────────┤
│ ⚙  Settings                           │
│ 👤  omnidj@monohq-labs.com         │
└─────────────────────────────────────┘
```

**Logica:**
- **Analyse** = alle intake-routes op één scherm. Drop, kies van Mac, watch folder, Dropbox, Google Drive. Plus de in-progress upload/processing states binnen dezelfde view.
- **Library** = Projects-overzicht. Vervangt "Clips" als sidebar-item. Bevat alle geanalyseerde sets/projecten. Klik op een project → Clips-view (de huidige `#view-dashboard`).
- **Clips-view** = nog steeds bereikbaar via een project, maar niet meer rechtstreeks vanuit de sidebar. De huidige `body.redesign-v2 #view-dashboard` styling blijft 1:1.
- **Brand / Social / Calendar / Insights** = onveranderd

### Routing-gedrag

| Trigger | Resultaat |
|---|---|
| App start | Analyse view (drop-screen prominent, of "Continue editing: [setnaam]" CTA als er een active set is) |
| Klik sidebar "Analyse" | switchView('analyse') |
| Klik sidebar "Library" | switchView('library') — toont Projects-tiles |
| Klik op project in Library | switchView('dashboard') + load set (= Clips-view van dat project) |
| Upload klaar | Analyse view → upload-state → processing-state (zonder view-switch) |
| Analyse klaar (analyzer.py done) | Auto switchView('dashboard') (=Clips van dat zojuist gecreëerde project) |
| Klik op breadcrumb "Library" vanuit Clips | terug naar Library Projects-tiles |

### Sidebar workspace+artist switcher — Supabase-stijl

**Twee onafhankelijke chips, gestapeld:**

```
┌─────────────────────────────────────┐
│ ⚡  MONO LABS       [FREE] ▾     │ ← chip 1: workspace
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ ⏵  Omni DJ          ▾         │ ← chip 2: actieve artist
└─────────────────────────────────────┘
```

**Chip 1 (workspace + plan):**
- Toont: workspace-naam + plan-badge (FREE / PRO / STUDIO)
- Klik → dropdown met:
  - Lijst workspaces (Fase 5 hardcoded 1 entry, Fase 5b multi-tenant)
  - "Manage workspace" link → Settings → Workspace section
  - "Upgrade plan" link bij FREE/PRO → opent upgrade-modal
- Plan-badge kleur:
  - FREE = `--v2-text-tertiary` op transparent
  - PRO = `--v2-accent-muted` op `--v2-accent`
  - STUDIO = `--v2-text-primary` op `--v2-accent` (vol oranje, premium feel)

**Chip 2 (artist):**
- Toont: huidige artist (uit onboarding default = `artist_name` veld uit Profile)
- Klik → dropdown met:
  - Lijst artiesten in deze workspace
  - **Bij FREE/PRO:** alleen 1 artist (de default uit onboarding). Andere artiesten in dropdown zijn locked → klik triggert upgrade-modal "Multi-artist is a Studio plan feature"
  - **Bij STUDIO:** vrij switchen + "+ Add artist" link → Settings → Workspace → Add artist
  - "Manage artists" link altijd zichtbaar → Settings

**State binding:**
- Active artist staat in `localStorage.clipLiveActiveArtist` (Fase 5)
- Library en Analyse filteren projecten/exports per active artist (Fase 5b — data hangt aan artist_id in Supabase). Fase 5: filter werkt frontend-only op een hardcoded `artist_id` veld.

### Multi-artist als Studio-plan feature — paywall-strategie

| Touchpoint | Gedrag bij FREE/PRO | Gedrag bij STUDIO |
|---|---|---|
| Artist-chip in sidebar | Klik opent dropdown, alleen 1 artist (default) zichtbaar als vrij. Demo-tweede-artist erin als locked-item met 🔒 icoon | Volledige lijst klikbaar |
| Klik op locked artist | Upgrade-modal opent: "Multi-artist workspace — Studio plan only" | n.v.t. |
| Settings → Workspace → Add artist | Disabled-knop met lock-icoon. Klik → upgrade-modal | Werkende form |
| Onboarding | Vraagt alleen 1 artist-naam (= default) | Vraagt alleen 1 artist-naam (= default), extra artists later via Settings |

**Bij upgrade FREE → STUDIO** of **PRO → STUDIO**: locked-states verdwijnen, dropdown wordt volledig functioneel.

---

## 4. View-voor-view scope

### 4.1 Analyse view (vervangt + integreert #view-home, #view-upload, #view-processing)

**Huidige situatie:** 3 losse views met view-switches.

**Nieuw:** 1 view `#view-analyse` met 3 sub-states.

**Layout (idle-state, app net opgestart of na "Analyse" klik):**

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Breadcrumb: Analyse                                          [Quota 6/10]│
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Analyse a DJ set                                                         │
│  Drag & drop or select your DJ-set.                                       │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │           ⬇                                                       │   │
│  │      Drop a set here                                              │   │
│  │      MP4 · MOV · WAV · MP3 · FLAC                                 │   │
│  │                                                                    │   │
│  │      (klik = openFilePicker, geen aparte knop nodig)              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                │
│  │ 👀              │ │ ☁              │ │ ☁              │                │
│  │ Watch a folder  │ │ Dropbox        │ │ Google Drive   │                │
│  │ Auto-process    │ │ Coming soon    │ │ Coming soon    │                │
│  └────────────────┘ └────────────────┘ └────────────────┘                │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Continue editing: Lisa Korver x Ho_r Berlin                       │   │
│  │ 30 clips · last opened 2 days ago        [Open in Library →]      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

**Wijzigingen t.o.v. v2:**
- Sub-copy: "Drag & drop or select your DJ-set."
- Dropzone: geen "— up to 4 hours" text, geen `[Choose file]`-knop (de hele card is klikbaar = file-picker)
- Geen "Or use:"-label boven de tiles
- "Choose file / Local picker"-tile **weg** (was duplicaat van dropzone-klik)
- 3 tiles ipv 4: Watch folder + Dropbox + Drive

**Uploading-state:**
- Dropzone-card transformeert tot upload-progress card: filename, MB, ETA, percent-bar, cancel-knop
- 4 intake-tiles eronder grayed out (no double-upload)
- "Continue editing"-card blijft

**Processing-state:**
- Dropzone-card wordt "Analyzing **[setnaam]** · 38%"
- Sub-progress steps: waveform → drop detection → stems → done
- Cancel-knop
- Bij klaar: card animeert naar "Done! [Open clips →]" knop, of auto-redirect na 2s naar `dashboard`

**Drie sub-states binnen dezelfde view = 0 view-switches** = premium, compact, intuïtief.

**Watch folder UI:**
- Klik tile "Watch a folder" → opent dezelfde `openWatchFolderUI()` call die nu al bestaat
- Watch-status-strook verschijnt in een 5e tile-positie of als info-banner onder de 4 tiles als er een folder actief is

**Dropbox / Google Drive:**
- Beide tiles zichtbaar maar `disabled` class + tooltip "Coming soon"
- Hetzelfde patroon als view-upload nu

### 4.2 Library view (NIEUW — vervangt Clips als sidebar-entry)

**Doel:** Projects-overzicht. Klik op project → Clips-view van dat project.

**Layout (Projects-tab default):**

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Breadcrumb: Library                                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Library                                  [⌕ Search]   [Filter ▾]         │
│  All your projects, ready to revisit.                                     │
│                                                                           │
│  Tabs: ╭─ Projects (12) ─╮  Exports (47)                                  │
│        ╰────────────────╯                                                  │
│                                                                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ [thumb]    ★ │ │ [thumb]      │ │ [thumb]    ★ │ │ [thumb]      │   │
│  │              │ │              │ │              │ │              │   │
│  │ Lisa Korver  │ │ Housy Good   │ │ Ediine x...  │ │ Set 04       │   │
│  │ x Ho_r Berlin│ │ Vibes 30m    │ │ Ho_r Berlin  │ │              │   │
│  │ 30 clips     │ │ 23 clips     │ │ 33 clips     │ │ 12 clips     │   │
│  │ 55 min       │ │ 30 min       │ │ 45 min       │ │ 22 min       │   │
│  │ 2 days ago   │ │ 5 days ago   │ │ 1 week ago   │ │ 3 wk ago     │   │
│  │              │ │              │ │              │ │ ▸ Open       │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│                                                                           │
│  + 8 more — scroll                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Tile-interactie:**
- Hover: lift -1px + border-strong
- Klik op tile: `switchView('dashboard')` + `loadJob(jobId)` → Clips-view van dat project
- Klik op ★: toggle favourite
- Right-click of `⋯` menu: Rename, Duplicate, Delete project, Show in Finder

**Exports-tab:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Tabs: Projects (12)  ╭─ Exports (47) ─╮                                  │
│                       ╰─────────────────╯                                  │
│                                                                           │
│  Filter: [All] [9:16] [16:9] [★ Favorites] [Last 7 days]                  │
│                                                                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │
│  │ thumb  │ │ thumb  │ │ thumb  │ │ thumb  │ │ thumb  │ │ thumb  │      │
│  │ Drop_3 │ │ Drop_5 │ │ Drop_1 │ │ Drop_8 │ │ Drop_2 │ │ Drop_4 │      │
│  │ 9:16   │ │ 9:16   │ │ 16:9   │ │ 9:16   │ │ 9:16   │ │ 9:16   │      │
│  │ Lisa K │ │ Lisa K │ │ Housy  │ │ Ediine │ │ Ediine │ │ Ediine │      │
│  │ 2d ago │ │ 2d ago │ │ 5d ago │ │ 1w ago │ │ 1w ago │ │ 1w ago │      │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘      │
│                                                                           │
│  Klik export → "Reveal in Finder" / "Re-export" / "Delete"               │
└─────────────────────────────────────────────────────────────────────────┘
```

**Sub-tabs (Projects / Exports):** segmented control in v2-stijl (zelfde patroon als Fase 2 ratio-toggle).

**Active-artist filter:**
- Library toont alleen projecten/exports die bij de actieve artist horen
- Fase 5: frontend filter op een hardcoded artist_id veld
- Fase 5b: backend-filter via Supabase RLS

### 4.3 Clips view (huidige #view-dashboard)

Geen styling-wijzigingen — Fase 2 heeft 'm al gedaan. Wel **3 polish-aanpassingen:**

1. **"CLIP PICKER · Pick the keepers"-hero VERWIJDEREN**. Vervangen door subtle v2 breadcrumb-stijl:
   ```
   Library › Lisa Korver x Ho_r Berlin · 30 clips
   ```
   (geen BPM in breadcrumb — die was visuele clutter)
2. **"Back to Library" link** linksbovenaan: chevron-left + "Library" — clickable, switchView('library')
3. **Project-context-pill** rechtsbovenaan: kleine kaartje met de active project-naam + ★ toggle. Klik op naam = inline rename

### 4.4 Settings view

**Probleem nu:** mengt Playfair italic met v2-cards. Visueel inconsistent.

**Nieuw:**
- Alle Playfair-titels weghalen
- Hero: `Settings` (Inter 600 22px) + sub "Local-first. Everything stays on this Mac." (text-secondary 14px)
- 2-koloms layout op desktop (>1100px), 1-koloms op smaller schermen
- Cards groeperen:
  - **Profile** (naam, artist-name, email) — staat er al, v2-restyle
  - **Workspace** (NIEUW — multi-artist) — workspace-naam, plan, leden, **"Artists" sub-sectie**:
    - Lijst van artists in workspace (max 3 op Studio-plan)
    - Default-artist (uit onboarding, placeholder `Artist name`) gemarkeerd
    - "+ Add artist"-knop:
      - FREE/PRO: disabled + lock-icoon, tooltip "Studio plan only", klik → upgrade-modal
      - STUDIO + minder dan 3 artists: enabled, opent inline form (naam + accent-kleur + brand kit-koppeling)
      - STUDIO + 3 artists: disabled met tooltip "Max 3 artists in Studio plan"
  - **Watch folder** — folder-keuze, on/off toggle
  - **Brand kit** — quick view + "Open style room" knop. **Per artist** in STUDIO-plan, gedeeld in FREE/PRO
  - **Account & plan** — plan-badge groot, quota, billing, upgrade-knop, "Sign out"

**Weg uit Settings (v3 — front-end weghalen, backend blijft):**
- ~~Capabilities~~ (ffmpeg/Demucs/VideoToolbox/MPS) — backend-detection blijft draaien voor processing-keuzes, gewoon niet meer in UI
- ~~Storage & large files~~ — proxy-cleanup blijft als functie beschikbaar maar niet in UI

### 4.5 Brand Stack (`view-style`)

- Playfair-titels weg
- Sectie-headers in v2 (Inter 600 17px primary)
- **Artist-pill linksboven** (read-only): toont voor welke artist deze Brand Stack is. Klik = switch via sidebar-artist-chip
- "Save preset" / "Reset" buttons in v2 accent-fill + v2-secondary
- Op STUDIO-plan: brand-kit is per-artist; switchen van artist via sidebar laadt andere brand-kit

### 4.6 Publish (`view-publish`)

Voorlopig grotendeels placeholder (Postiz-integratie staat in Fase 5c uit content-calendar plan). Wel v2-restyle van skeleton:
- Playfair titels weg
- Cards voor: Connected accounts, Scheduled posts, Recent posts
- Empty-state v2 (dashed border, secondary text, accent CTA)
- **Per-artist account-koppeling** in STUDIO-plan

### 4.7 Workspace + artist switcher (sidebar bovenin)

**Nu:** statische tekst "MONO LABS · Pro plan" op één regel.

**Nieuw — 2 gestapelde chips:**

```html
<div class="v2-ws-stack">
  <button class="v2-ws-chip" data-role="workspace">
    <span class="v2-ws-icon">⚡</span>
    <span class="v2-ws-name">MONO LABS</span>
    <span class="v2-ws-plan v2-plan-free">FREE</span>
    <span class="v2-ws-chev">▾</span>
  </button>
  <button class="v2-ws-chip v2-ws-artist" data-role="artist">
    <span class="v2-ws-icon">⏵</span>
    <span class="v2-ws-name" data-placeholder="Artist name">Artist name</span>
    <span class="v2-ws-chev">▾</span>
  </button>
</div>
```

**Workspace-chip dropdown:**
- Workspaces (Fase 5: hardcoded 1, Fase 5b: multi-tenant)
- "Manage workspace" → Settings → Workspace
- "Upgrade plan" als plan ≠ STUDIO → opent upgrade-modal

**Artist-chip dropdown:**
- Header: "Artists" (kort)
- Lijst artists. Active gemarkeerd met checkmark
- Locked artists (alleen voor FREE/PRO): `🔒` + grayed out, klik → upgrade-modal
- "+ Add artist" (STUDIO, indien < 3 artists) of "Add more artists with Studio →" (FREE/PRO) of niets (STUDIO + 3 artists bereikt)
- "Manage artists" → Settings

**Visuele referentie van jouw screenshot:** dezelfde compacte chip-stijl als Supabase ("MONO LABS FREE" / "Omni DJ"), met:
- Kleine icoon-glyph links
- Naam-tekst middenin
- Plan-badge of weglaten (alleen op workspace-chip)
- Chevron rechts
- Hover-state: subtle bg-elevated-2 fill
- Active-state (open dropdown): accent-border

---

## 5. Design-principes voor Fase 5 — compacter / premium / intuïtiever

| Principe | Wat | Waar |
|---|---|---|
| **Geen Playfair italic in tool-views** | Inter 600 ipv Playfair. | Analyse, Library, Settings, Brand Stack, Publish |
| **Eyebrows weg** | Vervangen door JetBrains Mono 11px breadcrumb. | Alle scene-headers |
| **1 H1 per view, geen sub-display** | "Pick the *keepers.*" + dash-set-title was 2 niveaus. | Clips, Analyse, Library |
| **2-koloms grids waar mogelijk** | Settings: Profile+Workspace links, Capabilities+Brand+Storage rechts. | Settings, Brand Stack |
| **Iconen + tekst** | Capabilities ✓ icoon ipv "Available ✓"-tekst. | Settings → Capabilities |
| **Cards consistent** | Alles op `--v2-radius-card: 14px` + `--v2-shadow-drawer`. | Settings, Library-tiles |
| **Sticky workspace+artist chips** | Altijd zichtbaar, ook tijdens scroll. | Sidebar |
| **Empty-states v2** | Dashed border + tertiary text + accent CTA. | Library, Analyse continue-card, Exports |
| **Loading-skeletons** | bg-elevated-2 + animated-shimmer. | Analyse, Library, Clips |
| **Plan-badge consistent** | FREE/PRO/STUDIO chip-styling identiek door hele app. | Sidebar, Settings, Upgrade-modal, paywalled features |

---

## 6. Technische uitvoering

### 6.1 Aanpak per onderdeel

| Item | Aanpak | Risico |
|---|---|---|
| Settings restyle | CSS-only + nieuwe Workspace-card markup | Laag |
| Brand Stack restyle | CSS-only + artist-pill toevoegen | Laag |
| Publish restyle | CSS-only | 0% |
| Processing-state restyle | CSS-only (binnen Analyse view) | Laag |
| **Analyse view NIEUW** | DOM-herschrijving `#view-home` → `#view-analyse` + integratie van upload/processing als sub-states | Middel — JS-call-sites updaten |
| **Library NIEUW** | Nieuwe `#view-library` DOM + sidebar-link, vervangt "Clips"-positie | Middel — sidebar-routing + data uit `/api/jobs` |
| **Workspace+artist switcher** | Nieuwe sidebar-DOM + 2 dropdowns + CSS + plan-badge | Middel — frontend-only data Fase 5 |
| **Paywall-states multi-artist** | Locked-items in dropdown + upgrade-modal trigger | Laag — patroon bestaat al (`upgrade-modal`) |
| "Pick the keepers" weg | DOM-edit | 0% |
| Project-context-pill in Clips | Nieuwe markup in `#view-dashboard` header | Laag |

### 6.2 Sub-fases binnen Fase 5 (uitvoerings-volgorde)

Eén sessie, met deze checkpoints:

1. **5.0 — Discovery + backup** (20 min)
   - Backup `static/index.html.pre-redesign-fase5.bak`
   - Grep alle Playfair-refs + alle `switchView('home'|'upload'|'processing')` call-sites
   - Bepaal data-shape: `/api/jobs`, `/api/recent-exports` (check of die endpoint bestaat)
   - Bepaal exacte JS-state-vars die multi-state Analyse aansturen

2. **5.1 — Sidebar rebuild: workspace + artist chips** (1.5u)
   - DOM-edit in sidebar-header
   - CSS voor 2 chips + plan-badge varianten (FREE/PRO/STUDIO)
   - JS: 2 dropdowns met hardcoded data + click-handlers
   - Active-artist in localStorage
   - Plan-check (uit bestaand auth-state) bepaalt locked-states
   - Sidebar-nav: "Clips" → "Library", "Home" → "Analyse" (volgorde + iconen aanpassen)

3. **5.2 — CSS-only restyles** (1.5u)
   - Settings, Brand Stack, Publish (Playfair weg, v2-cards, 2-koloms)
   - Settings → nieuwe Workspace-card incl. artists-sectie + paywall
   - "Pick the keepers" hero verwijderen
   - Project-context-pill in Clips-view header

4. **5.3 — Analyse view rebuild** (2u)
   - Nieuwe `#view-analyse` view (kopie van `#view-home` skeleton, gerename'd)
   - 4 intake-tiles (Drop / Choose file / Watch folder / Dropbox / Drive — laatste 2 disabled)
   - 3 sub-states (idle / uploading / processing) via class-toggle op view-container
   - "Continue editing"-card onderaan
   - JS: switchView('upload') en switchView('processing') redirect naar switchView('analyse') met state-flag
   - Oude `#view-upload` en `#view-processing` behouden in DOM (display:none) als fallback

5. **5.4 — Library view NIEUW** (2u)
   - Nieuw `<main id="view-library" data-scene="X">` element
   - Tabs (Projects / Exports) segmented control
   - Reuse clip-grid CSS voor tiles (zelfde aspect, andere data)
   - `renderLibraryProjects()` + `renderLibraryExports()` functies
   - Data uit `/api/jobs` + `/api/recent-exports` (laatstgenoemde check/maak)
   - Sidebar-link "Library" routet hier
   - Klik op tile → `loadJob(id)` + switchView('dashboard')
   - Active-artist filter (frontend voor Fase 5)

6. **5.5 — Polish + verificatie** (45 min)
   - Tag-balance, JS-syntax, live test via Chrome MCP
   - Alle 8 onderdelen + paywall-flow getest
   - Flag UIT 100% intact controleren

**Totaal:** ~8 uur dev-sessie. Met buffer = 1 hele werkdag.

### 6.3 Files die wijzigen

- `dj-clip-cutter/static/index.html` (+~900 regels CSS, +~350 regels nieuwe DOM, ~50 regels DOM-edits)
- Geen wijzigingen aan `app.py`, `cutter.py`, `analyzer.py`, `auth.py` — tenzij `/api/recent-exports` ontbreekt, dan ~20 regels extra

### 6.4 Backup-strategie

- `static/index.html.pre-redesign-fase5.bak` (volledige snapshot vóór sessie 54)
- Tussentijdse backups na elke sub-fase: `.pre-fase5-checkpoint-{0..5}.bak`
- Rollback: `cp static/index.html.pre-redesign-fase5.bak static/index.html && ./start.sh`

### 6.5 Verificatie

**Statisch:**
- `python3 -c 'import ast; ast.parse(open("app.py").read())'` (alleen als app.py geraakt)
- `node --check` op JS-blok
- Python `html.parser` over hele file = 0 errors
- Tag-balance delta vs backup = 0
- Grep: alle nieuwe selectors aanwezig (`v2-ws-chip`, `v2-plan-free|pro|studio`, `#view-analyse`, `#view-library`, etc.)
- Grep: 0 matches voor "Pick the keepers" en oude eyebrows in v2-scope
- Grep: oude "Clips"-sidebar-link is vervangen door "Library"

**Live (Chrome MCP):**

*Flag UIT:* oude UI 100% intact

*Flag AAN:*
- Sidebar: 2-chip stack bovenaan (workspace + artist)
- Sidebar-nav: Analyse + Library + Brand + Social + Calendar + Insights (geen Clips!)
- Workspace-chip dropdown opent, sluit op klik buiten
- Artist-chip dropdown: bij FREE-plan toont 1 actieve + 1 locked artist
- Klik op locked artist → upgrade-modal opent
- Analyse view: 4 intake-tiles + dropzone + "Continue editing"
- Drop file → upload-state binnen Analyse (geen view-switch)
- Analyse klaar → Clips-view (= dashboard)
- Library: Projects/Exports tabs werken, project-klik → Clips van dat project, breadcrumb klopt
- Clips-view: geen "Pick the keepers" meer, wel project-context-pill rechts + Library-back-link
- Settings: 2-koloms, Workspace-card met Artists-sectie, "+ Add artist" disabled met lock bij FREE
- Klik lock → upgrade-modal
- Brand Stack: artist-pill linksboven
- Geen JS-errors, geen layout-shift

---

## 7. Risico's en mitigaties

| Risico | Kans | Impact | Mitigatie |
|---|---|---|---|
| Sidebar "Clips" → "Library" verwart bestaande gebruikers | Middel | Laag | Bij eerste open van "Library" tonen we 1x een toast: "Clips zitten nu in een project — klik op een project om ze te zien". 7 dagen dismissable. |
| Upload-flow breekt door view-merge | Laag | Hoog | view-upload + view-processing behouden als fallback (display:none). Bij eerste failure flag-toggle om alleen Analyse-merge te disablen. |
| Active-artist niet meegestuurd naar Supabase | Hoog | Laag (Fase 5) / Hoog (Fase 5b) | Fase 5: alleen frontend-filter, geen Supabase-call met artist_id. Fase 5b: RLS-policy + migration. |
| Paywall te aggressief, irriteert FREE-users | Middel | Middel | Locked artist alleen demo (= 1 dummy). Geen pop-up bij sidebar-open, alleen bij klik op locked item. |
| Workspace+artist chips nemen te veel verticale ruimte | Laag | Laag | Total height ~80px voor 2 chips + 8px gap. Sidebar is min 700px hoog, ruim genoeg. |
| Dropdown z-index conflict | Laag | Laag | z-index 9998 (zelfde als sessie 49 export-modal fix). |
| `/api/recent-exports` ontbreekt | Hoog | Middel | Sub-fase 5.4 checkt eerst — als endpoint niet bestaat, toevoegen (~20 regels) of filesystem-scan. |
| Multi-artist Brand Stack-data niet beschikbaar | Hoog | Laag | Fase 5: 1 gedeelde Brand Stack voor alle artists. Fase 5b: per-artist brand-kit met Supabase. |

---

## 8. Wat NIET in deze fase zit

- **Echte multi-tenant data-werk** — workspace + artist switcher is UI-only. Supabase RLS op `workspace_id` + `artist_id` = Fase 5b.
- **Per-artist Brand Stack data** — Fase 5b.
- **Per-artist Social-accounts (Postiz)** — Fase 5c.
- **reset-password.html** — eigen sessie.
- **App-icon vervangen** — rebrand-werk, aparte sessie.
- **Folder rename `dj-clip-cutter/` → `omnidj/`** — hoge risico, aparte sessie.
- **Bundle-identifier wijzigen** — code-rebrand sessie.
- **Echte Stripe-koppeling Studio plan** — pricing-pagina + Stripe price-IDs voor Studio bestaan nog niet. Voor Fase 5 doen we de paywall maar de upgrade-knop opent dezelfde upgrade-modal als nu (Pro). **Aanbeveling:** Studio plan-pricing definiëren vóór sessie 54.
- **Onboarding-flow uitbreiden voor multi-artist** — Onboarding vraagt nog steeds 1 artist-naam (default). Multi-artist add via Settings.

---

## 9. Beslispunten — beantwoord door Sjuul (v3)

1. **Studio Stripe price-ID:** ✅ bestaat al, hergebruiken.
2. **Max artists in Studio:** ✅ **3** (UI-copy: "Add up to 3 artists" / "Max 3 artists in Studio plan").
3. **Default-artist placeholder:** ✅ "Artist name" (uit `artist_name` veld onboarding, of als leeg dan letterlijk "Artist name" als placeholder-tekst).
4. **Library-tile-density:** ✅ **4 per rij** desktop-default.

---

## 10. Volgorde t.o.v. andere plannen

```
SESSIE 53 (klaar) ──► visuele verificatie (5 min, Sjuul)
                          │
                          ├──► SESSIE 54 = dit plan (Fase 5 — UI only)
                          │        │
                          │        └──► Sessie 55 = rebuild .app/.dmg
                          │                  │
                          │                  └──► Code-rebrand Omni DJ → Omni DJ
                          │                            │
                          │                            └──► omnidj.com koppelen
                          │                                      │
                          │                                      └──► Stripe live mode + Studio price
                          │
                          ├──► (parallel) Fase 5b multi-tenant data (workspace+artist in Supabase)
                          │
                          └──► (parallel) Fase 5c Postiz publishing
```

---

## 11. Wat Sjuul moet doen om dit plan goed te keuren

1. Lees dit plan door
2. Bevestig de sidebar-structuur: **Analyse + Library + Brand + Social + Calendar + Insights** (Clips weg uit sidebar)
3. Bevestig de 2-chip workspace+artist switcher Supabase-stijl
4. Bevestig dat multi-artist = Studio-plan-only feature (locked op FREE/PRO)
5. Geef antwoord op de 4 open beslispunten in sectie 9 (of zeg "doe je voorkeur", dan ga ik met aanbevelingen)
6. Schrijf "ja, ga ervoor" of geef terugkoppeling per sectie

Pas na "ja" begin ik aan sessie 54.

---

**Einde plan v2. Wacht op akkoord.**
