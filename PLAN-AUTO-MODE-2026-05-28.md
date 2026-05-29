# PLAN — Auto-mode & Brand-page redesign (Omni DJ)

> **Status:** Concept, wachtend op Sjuul's akkoord.
> **Datum:** 2026-05-28
> **Auteur:** Claude in sessie 57
> **Scope:** Brand-page herontwerp + nieuwe Auto-mode (Autopilot) sidebar-sectie + Brand-pack data-model + tier-uitbreiding.
> **Buiten scope:** Postiz publishing-integratie (komt later), Dropbox/Drive backend (alleen UI), echte Stripe-billing wijzigingen (alleen tier-namen reserveren).

---

## 0. Samenvatting in 10 regels

1. **Profile-velden** (Full Name / Email) verhuizen van Brand → Settings.
2. **Brand-page** wordt de plek voor Brand Kit, Watermark, Caption-presets, Clip-templates, Hashtag-sets, Hook/CTA-templates, Lower-thirds, Intro/outro-frames en Stickers.
3. **Alles op Brand is per artist** (Studio = max 3 artists, dus max 3 brand-packs per workspace).
4. **Nieuwe sidebar-sectie "Auto-mode"** verschijnt onder Insights, gescheiden door een crème divider-lijntje.
5. **Auto-mode = pipeline-automation** met per-stap toggles (Intake → Analyse → Clip-gen → Brand → Calendar → Publish).
6. **Tiers:** Free niets, Pro = Watch-folder, Studio = Watch-folder + Auto-mode (review verplicht), Studio+ later = Auto-publish zonder review.
7. **Auto-mode default UIT** bij nieuwe gebruikers — moet expliciet aangezet worden per stap.
8. **Watch-folder backend** alleen lokaal in v1. Dropbox + Google Drive zichtbaar in UI maar disabled.
9. **Postiz-publishing** is uit scope — Publish-stap toont placeholder "Coming via Postiz".
10. **Schatting:** 8-10 weken dev, opgedeeld in 6 fasen, te releasen in 3 zichtbare drops naar gebruikers.

---

## 1. Tier-matrix (definitief)

| Feature | Free | Pro | Studio | Studio+ (toekomst) |
|---|---|---|---|---|
| Manual upload + analyse | ✓ | ✓ | ✓ | ✓ |
| Library + Brand-page basis | ✓ | ✓ | ✓ | ✓ |
| Brand Kit (logo, color, watermark) | ✓ | ✓ | ✓ | ✓ |
| Caption-presets (max aantal) | 3 | 25 | ∞ | ∞ |
| Multi-artist (brand-packs) | 1 | 1 | 3 | ∞ |
| Watch-folder (lokaal) | — | 1 folder | 3 folders | ∞ folders |
| Watch-folder (Dropbox / Drive) | — | — | — | ✓ |
| Auto-mode (pipeline-automation) | — | — | ✓ | ✓ |
| Auto-publish zonder review | — | — | — | ✓ |
| Postiz publishing (later) | — | ✓ (manual) | ✓ (auto-queue) | ✓ (auto-fire) |

**Stripe-implicatie:** Bestaande Pro + Studio prijzen blijven. Studio+ is een toekomstige price-ID — voorlopig alleen feature-flag `tier === 'studio_plus'` in code reserveren, geen Stripe-product aanmaken.

**Paywall-UX:**
- Free user opent Brand: ziet beperkte UI met "Upgrade for unlimited" pills op de geblokte secties.
- Free/Pro user opent Auto-mode: ziet de volledige UI in read-only mode met een overlay "Upgrade to Studio to enable Auto-mode" en een grote Upgrade-knop. Toggles zijn disabled.
- Pro user op Brand: ziet Watch-folder card als enabled (max 1 folder). Studio-only velden (multi-artist, 3 folders) tonen lock-icon.

---

## 2. Brand-page herontwerp

### 2.1 Wat eraf gaat

| Element | Nieuwe plek |
|---|---|
| Profile-card (Full Name / Artist Name / Email) | Settings → Account-sectie |
| Workspace-card | Settings (staat er al) |
| Watch-folder-card | **Blijft** op Brand maar wordt onderdeel van Auto-mode-config (zie 2.2.7) |

Reden Watch-folder blijft: het is per-artist een brand-keuze (welke folder hoort bij welke artist's brand-pack), niet een account-niveau setting.

### 2.2 Wat erop komt — 10 secties

#### 2.2.1 Active Brand-pack selector (top, sticky)

- Dropdown bovenaan de Brand-page: "Brand-pack: Artist name ▼"
- Studio-plan: 3 brand-packs beschikbaar (1 per artist). Pro/Free: 1.
- Bij wisselen herlaadt alle secties hieronder met de data van die brand-pack.
- "+ Create brand-pack" knop met paywall voor Free/Pro (multi-artist = Studio).
- Optioneel: "Duplicate from Artist X" snelknop.

#### 2.2.2 Brand Identity card

- Logo upload (PNG met transparency, max 2MB) + preview
- Logo-positie default voor clips: 4 hoeken + center, opacity slider 20-100%
- Logo-size default: 5-20% van clip-hoogte
- Brand accent-color (color wheel uit sessie 42)
- Brand secondary colors (max 3, voor multi-color captions)

#### 2.2.3 Watermark card

- Apart van logo — bedoeld voor altijd-aan tag (bv "@smyler.dj")
- Text-watermark (string + font + color + size)
- Of image-watermark (klein PNG)
- Positie + opacity
- "Apply to all new exports by default" toggle

#### 2.2.4 Caption-presets library

- Grid van saved presets, elk een kaart met preview (1-frame thumbnail)
- Per preset opslag:
  - Font (uit de 11 built-in of system-fonts)
  - Size, color, stroke, shadow, background-pill
  - Position (X/Y in %)
  - Animation (none / fade / pop / slide-up)
  - Duration / appear-at-second
- "+ New preset" → opens editor in preset-mode
- "Save current as preset" verschijnt ook in de Editor / text-drawer (sessie 47)
- Default-preset selector: welke wordt automatisch toegepast bij Auto-mode
- Free: max 3 presets. Pro: 25. Studio: onbeperkt.

#### 2.2.5 Clip Templates / Aspect-presets

- Library van complete export-presets, elk combineert:
  - Aspect-ratio (9:16 / 1:1 / 16:9)
  - Caption-preset reference
  - Watermark on/off
  - Logo position
  - Export quality (bitrate, fps)
- Built-in templates:
  - "TikTok Drop" (9:16, caption-preset "Bold drop", watermark on)
  - "Instagram Reel" (9:16, andere caption-positie hoger ivm IG-UI)
  - "YouTube Shorts" (9:16, geen watermark — YT detecteert dat als spam)
  - "Twitter/X" (16:9 of 1:1)
- "+ Custom template"
- Default-template per platform selector → gebruikt door Auto-mode

#### 2.2.6 Hook templates (social media)

- Library van openings-overlays (eerste 0-2s van een clip)
- Voorbeelden:
  - "Wait for the drop"
  - "Track ID 👀"
  - "POV: you're at {venue}"
  - "Best moment of the set"
- Variabele-syntax: `{venue}`, `{set_name}`, `{bpm}`, `{drop_time}`, `{date}`
- Auto-mode kiest random uit een pool, of vaste rotation, of "always this one"

#### 2.2.7 CTA templates (social media)

- Library van afsluit-overlays (laatste 1-2s)
- Voorbeelden:
  - "Follow for more"
  - "Track in bio"
  - "Full set on YouTube"
  - "Next gig: {next_event}"
- Default-CTA per platform (X-platform "Reply track ID", IG "Save for later")

#### 2.2.8 Caption-copy templates (post-text, niet overlay)

- Dit is de tekst die naast de video staat op social
- Per platform een template:
  - TikTok: max 2200 char, hashtag-rijk
  - Instagram: max 2200 char, emoji-vriendelijk
  - YouTube Shorts: titel (100 char) + description (5000 char)
  - X: max 280 char
- Variabelen `{track_id}`, `{bpm}`, `{set_name}`, `{drop_time}`
- Voorbeeld template TikTok: `🔥 {track_id} dropping at {drop_time} from my {set_name} set\n\n{hashtags}`

#### 2.2.9 Hashtag-sets per platform

- Sets van hashtags per platform, herbruikbaar
- "TikTok core" — `#dj #electronicmusic #festival #drop`
- "Instagram core" — andere mix
- Variant-sets voor genre: "Techno set", "House set", "Drum & Bass set"
- Auto-injection in caption-copy via `{hashtags}` token

#### 2.2.10 Stickers + Lower-thirds + Intro/outro

- **Sticker library:** kleine PNG-overlays draggable in editor. Default: pijl, "NEW", flame, signature. User-uploaded.
- **Lower-third templates:** artist-name + track-info bar onderaan tijdens hele clip. Vier built-in styles (clean, gradient, neon, retro), customizable color.
- **Intro/outro frames:** 0.5-1s logo-card aan begin/eind. Toggle per clip-template.

### 2.3 Brand-pack als geheel

- Brand-pack = JSON-bundel van bovenstaande velden, gekoppeld aan `artist_id`.
- "Export brand-pack" knop bovenaan: download `.omnidj-brandpack.json`.
- "Import brand-pack" knop: upload .json, merge of overwrite.
- Use-case export/import: backup, delen tussen Studio-artists, agency presets.

### 2.4 Pagina-layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Brand                          [Brand-pack: SMYLER ▼]   [Export]│
├─────────────────────────────────────────────────────────────────┤
│ Brand Kit                                                       │
│  ┌──────────┐ Accent: ●●●●                                      │
│  │ logo.png │ Secondary: ●●●                                    │
│  └──────────┘                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Watermark                                                       │
│  Text: @smyler.dj    Position: bottom-right    Opacity: 60%     │
├─────────────────────────────────────────────────────────────────┤
│ Caption Presets                          [+ New preset]         │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐                                    │
│  │ p1 │ │ p2 │ │ p3 │ │ +  │                                    │
│  └────┘ └────┘ └────┘ └────┘                                    │
│  Default for Auto-mode: ▼ Bold Drop                             │
├─────────────────────────────────────────────────────────────────┤
│ Clip Templates                           [+ New template]       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                            │
│  │ TikTok  │ │ IG Reel │ │ YT Short│                            │
│  └─────────┘ └─────────┘ └─────────┘                            │
├─────────────────────────────────────────────────────────────────┤
│ Social Templates                                                │
│  Hooks  [+ Add]    "Wait for the drop"     "Track ID 👀"       │
│  CTAs   [+ Add]    "Follow for more"       "Track in bio"      │
├─────────────────────────────────────────────────────────────────┤
│ Caption Copy (post-text)                                        │
│  TikTok template ▼   Instagram ▼   YouTube ▼   X ▼              │
├─────────────────────────────────────────────────────────────────┤
│ Hashtag Sets                                                    │
│  TikTok core   IG core   Techno   House    [+ New set]          │
├─────────────────────────────────────────────────────────────────┤
│ Stickers, Lower-thirds, Intro/Outro                             │
│  ┌──┐┌──┐┌──┐┌──┐  [+]    LT: Clean ▼    Intro/Outro: ON       │
│  └──┘└──┘└──┘└──┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Auto-mode (Autopilot) — volledige spec

### 3.1 Sidebar-positie

```
- Analyse
- Library
- Brand
- Social
- Calendar
- Insights
──────────────  ← dunne crème divider, geen label
- Auto-mode
```

Crème = `var(--v2-text-subtle)` of nieuw `--v2-divider-cream: #d4c8b8` at 30% opacity.

### 3.2 Pipeline-stappen + per-stap toggle

Auto-mode is een 6-staps pipeline. Elke stap heeft een ON/OFF toggle. Als een stap OFF staat, pauzeert de pipeline daar en wacht op manual approval. Free/Pro = alle toggles disabled met paywall.

```
Step 1: INTAKE          [ON / OFF]
Step 2: ANALYSE         [ON / OFF]
Step 3: CLIP-GEN        [ON / OFF]
Step 4: BRAND-APPLY     [ON / OFF]
Step 5: CALENDAR-QUEUE  [ON / OFF]  ← Sjuul's keuze: default ON
Step 6: AUTO-PUBLISH    [ON / OFF]  ← default OFF, Studio+ only
```

**Default-config nieuwe Studio-user:**
- Alles OFF bij eerste open van Auto-mode.
- "Quick-enable: Review mode" knop → zet Intake/Analyse/Clip-gen/Brand/Calendar op ON, Publish op OFF. Veiligste preset.
- "Quick-enable: Full Auto" knop → alleen Studio+ klikbaar.

### 3.3 Per stap — wat doet het, wat is configureerbaar

#### Step 1 — INTAKE

**Wat:** Watch-folder triggert pipeline bij nieuw bestand.

**Config in UI:**
- Folder-lijst (max N afhankelijk van tier)
- Per folder: type (Local / Dropbox-disabled / Drive-disabled), pad, bound to artist
- File-filters: extensies (.mp3, .wav, .m4a, .mp4, .aiff), min-duur (default 15min — sets korter dan dat skippen)
- Trigger-delay (debounce): default 2 min na laatste write, om incomplete uploads te vermijden

**Backend:**
- `watchdog` Python lib voor local FS-events (mac + linux). Bestaat al in `analyzer.py` context.
- Voor v1 alleen local. Dropbox/Drive UI staat klaar maar geeft `Toast: "Coming in Studio+ — not yet available"`.

#### Step 2 — ANALYSE

**Wat:** Upload bestand naar analyzer pipeline, detecteer drops.

**Config:**
- Sensitivity slider (zelfde als manual)
- Min-clip-duration / max-clip-duration
- Skip-tracks waar geen drop detected? (default ja, zou anders lege clip queue zijn)

**Backend:** roept bestaande `analyzer.py` aan via job-queue. Geen nieuwe code nodig.

#### Step 3 — CLIP-GEN

**Wat:** Genereer top-N clips.

**Config:**
- N clips per set (default 5, max 30 — bestaande limiet)
- Aspect-ratio's (multi-select: 9:16, 1:1, 16:9 — kruisproduct met clips)
- Clip-template selector (uit Brand-page 2.2.5) — kan platform-specifieke template kiezen
- Skip-if-already-processed (idempotency, hash-check op input-file)

**Backend:** roept bestaande `cutter.py` aan. Geen nieuwe code.

#### Step 4 — BRAND-APPLY

**Wat:** Pas brand-pack toe op clips.

**Config:**
- Brand-pack selector (default: artist's active pack)
- Caption-preset (default: brand-pack default)
- Hook-template strategie: none / random uit pool / fixed
- CTA-template strategie: zelfde drie opties
- Watermark on/off override
- Intro/outro on/off override

**Backend:**
- Caption-overlays JSON wordt automatisch geschreven met variabelen ingevuld:
  - `{bpm}` ← uit analyzer.py output
  - `{drop_time}` ← clip timestamp
  - `{set_name}` ← original filename minus ext
  - `{venue}` ← uit folder-naam pattern? Of leeg laten?
  - `{track_id}` ← LEEG ingevuld → trigger voor review-stap (user must fill)
- Captions worden ge-baked in MP4 zoals sessie 50+51.

#### Step 5 — CALENDAR-QUEUE

**Wat:** Clips toevoegen aan Content Calendar als "Pending review".

**Config:**
- Welke clips uit de N gerenderde gaan naar calendar? Opties:
  - "All N"
  - "Top X uit N" (slider 1-N)
  - "Best 1" (alleen sterkste drop)
- Spread-strategie:
  - "All same day" (bv release-day)
  - "Spread over N days" (bv 5 clips over 5 dagen)
  - "Use my schedule" (uit publish-schedule, zie 3.4)
- Per platform welke clip → instagram krijgt 9:16, X krijgt 16:9, etc. Auto-routing op aspect-ratio.

**Backend:**
- Calendar-events worden geschreven naar `localStorage.omnidj.calendar.v1` (sessie 56) of toekomstige Supabase `scheduled_posts` tabel.
- Status = `pending_review` bij CALENDAR-QUEUE ON + PUBLISH OFF.

#### Step 6 — AUTO-PUBLISH

**Wat:** Daadwerkelijk live zetten op socials.

**Config:**
- Per platform aan/uit (TikTok / IG / YT / X)
- Review-window: 0 / 1u / 6u / 24u / 48u — tijd dat user heeft om in te grijpen voordat post live gaat
- Safety-pause: "Stop alle auto-publish" emergency-toggle
- Studio+ alleen. Studio = greyed-out met "Upgrade to Studio+ to enable auto-publish".

**Backend:**
- Postiz API calls (later — voor nu placeholder met "Postiz coming soon")
- Wel: status-management in calendar (pending_review → scheduled → published / failed)

### 3.4 Publish-schedule (apart card binnen Auto-mode)

- Per platform een weekly schedule grid (7 dagen × 24 uur cells)
- User kan time-slots aanklikken: "Post here"
- Auto-mode pakt scheduled posts uit calendar en wijst ze toe aan eerstvolgende slot per platform
- Bv: "TikTok: Mon/Wed/Fri 18:00 + Sat 12:00" → 4 slots/week
- Default-presets: "Conservative" (3 posts/week), "Aggressive" (7/week), "Off"

### 3.5 Active queue card

Toont real-time wat de pipeline op dat moment doet:

```
┌─ Currently in pipeline ───────────────────────────────────┐
│ ⏳ Housy Goodvibes Mix.wav   → analysing  (45%)           │
│ ⏳ Boiler Room set.mp3       → clip-gen   (clip 3/5)      │
│ 👀 Lisa Korver x HöR Berlin  → in review  (24h left)      │
│ ✅ Best of April set         → published  (2 posts live)  │
└──────────────────────────────────────────────────────────┘
```

Sorteer: in-flight bovenaan, review-needed in het midden, recent-completed onderaan. Max 10 items, "View all" → Library.

### 3.6 Recent runs card

Laatste 20 pipeline-runs met:
- Set-naam, datum, status (success / partial / error)
- N clips gegenereerd, M gepublished
- Click → details-modal met logs

### 3.7 Safety controls (sticky footer of top-right)

- **Pause All** — bevriest pipeline, niets in flight gaat verder.
- **Stop Next Publish** — eerstvolgende auto-publish wordt geskipt.
- **Notify me** — emails bij elke stap (configureerbaar).

### 3.8 Review-flow (de UX voor de mens-in-de-lus)

Wanneer een clip in `pending_review` zit, gebeurt het volgende:

1. **In-app notification badge** op Auto-mode sidebar-item (rode dot met aantal pending)
2. **Calendar view** toont de scheduled post als oranje "needs review"
3. **Click op de calendar-event** opent review-modal met:
   - Video-preview
   - Caption-overlay preview
   - Post-text (caption-copy template ingevuld)
   - Hashtags
   - Platform
   - Schedule-time
   - Buttons: ✓ Approve, ✏️ Edit, ✗ Reject
4. **Edit** opent inline editor (sessie 47) op die clip
5. **Approve** → status → `scheduled`
6. **Reject** → status → `rejected`, niet gepubliceerd

Als de review-window verstrijkt zonder actie:
- Studio: post blijft staan, never auto-publishes (mens moet bewust kiezen)
- Studio+: post wordt automatisch geapproved (configureerbaar per platform)

### 3.9 Auto-mode view layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Auto-mode                                            [Status: ON]│
├──────────────────────────────────────────────────────────────────┤
│ Pipeline                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │1.INTAKE  │ │2.ANALYSE │ │3.CLIP-GEN│ │4.BRAND   │             │
│  │   [ON]   │ │   [ON]   │ │   [ON]   │ │   [ON]   │             │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │
│  ┌──────────┐ ┌──────────┐                                       │
│  │5.CALENDAR│ │6.PUBLISH │                                       │
│  │   [ON]   │ │   [OFF]🔒│ ← Studio+ only                       │
│  └──────────┘ └──────────┘                                       │
│                                                                   │
│  [Quick-enable: Review mode]  [Quick-enable: Full Auto 🔒]       │
├──────────────────────────────────────────────────────────────────┤
│ Watch-folders                                  [+ Add folder]    │
│  📁 ~/Music/DJ Sets     → SMYLER          [Local]    [Edit][×]  │
│  📁 Dropbox/Sets        → SMYLER          [Dropbox]  🔒 soon    │
│  📁 Drive/Sets          → -               [Drive]    🔒 soon    │
├──────────────────────────────────────────────────────────────────┤
│ Brand & defaults                                                  │
│  Active brand-pack: ▼ SMYLER                                     │
│  Clips per set: [5] ▼     Aspect: ☑ 9:16 ☑ 1:1 ☐ 16:9            │
│  Caption preset: ▼ Bold Drop      Hook: ▼ Random pool            │
│  CTA: ▼ Follow for more            Watermark: ☑                  │
├──────────────────────────────────────────────────────────────────┤
│ Publish schedule                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ TikTok   M T W T F S S   18:00 ●   12:00 ●                │ │
│  │ Instagram                 12:00 ●   18:00 ●                │ │
│  │ YouTube                  19:00 ●                            │ │
│  │ X                        09:00 ●                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│  Presets: [Conservative] [Aggressive] [Custom]                   │
├──────────────────────────────────────────────────────────────────┤
│ Currently in pipeline                                             │
│  ⏳ Housy Goodvibes Mix.wav   → analysing  (45%)                 │
│  👀 Lisa Korver set            → in review  (24h left)           │
│  ✅ Best of April set          → published  (2 posts live)       │
├──────────────────────────────────────────────────────────────────┤
│ Recent runs                                                       │
│  ...                                                              │
├──────────────────────────────────────────────────────────────────┤
│ Safety                                                            │
│  [Pause all]  [Stop next publish]  ☑ Email me at each step       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Data-model

### 4.1 Nieuwe Supabase tabellen

```sql
-- brand_packs: 1 per artist
create table brand_packs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id),
  artist_id uuid not null references artists(id),
  name text not null,
  brand_kit jsonb not null default '{}', -- logo_url, accent, secondary[]
  watermark jsonb not null default '{}',
  caption_presets jsonb not null default '[]',
  clip_templates jsonb not null default '[]',
  hooks jsonb not null default '[]',
  ctas jsonb not null default '[]',
  caption_copy jsonb not null default '{}',
  hashtag_sets jsonb not null default '[]',
  stickers jsonb not null default '[]',
  lower_thirds jsonb not null default '[]',
  intro_outro jsonb not null default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- auto_mode_configs: 1 per workspace
create table auto_mode_configs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) unique,
  enabled boolean default false,
  intake_on boolean default false,
  analyse_on boolean default false,
  clip_gen_on boolean default false,
  brand_apply_on boolean default false,
  calendar_queue_on boolean default true,
  publish_on boolean default false,
  watch_folders jsonb not null default '[]',
  brand_defaults jsonb not null default '{}',
  publish_schedule jsonb not null default '{}',
  review_window_hours int default 24,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- pipeline_runs: log van elke pipeline-execution
create table pipeline_runs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id),
  artist_id uuid references artists(id),
  source_file text,
  source_type text, -- 'local' | 'dropbox' | 'drive' | 'manual'
  status text not null, -- 'queued' | 'analysing' | 'clip_gen' | 'brand_apply' | 'in_review' | 'publishing' | 'done' | 'error'
  step text, -- current step
  progress_pct int default 0,
  clips_generated int default 0,
  clips_published int default 0,
  error_message text,
  metadata jsonb default '{}', -- bpm, set_duration, drop_count, etc.
  started_at timestamptz default now(),
  completed_at timestamptz
);
```

### 4.2 RLS-policies

Zelfde structuur als bestaande tabellen (sessie 32). Workspace-scoped reads + writes via `workspace_members`.

### 4.3 Local-state fallback

In v1 zonder backend voor brand-packs en auto-mode-config, gebruik dezelfde localStorage-aanpak als sessie 56 (calendar):

```js
localStorage.omnidj.brand_packs.v1
localStorage.omnidj.auto_mode_config.v1
localStorage.omnidj.pipeline_runs.v1
```

Dat geeft de UI iets om mee te werken terwijl backend langzaam aan groeit. Sync naar Supabase komt in Fase 5b van de bestaande plannen.

---

## 5. Frontend-architectuur

### 5.1 Nieuwe of gewijzigde files

| File | Wijziging |
|---|---|
| `static/index.html` | Brand-view CSS+DOM+JS uitgebreid. Nieuwe `#view-automode` met CSS+DOM+JS. Sidebar nav uitgebreid met divider + auto-mode entry. |
| `static/index.html` | `renderBrand()` herschrijven van placeholder naar volledige view met 10 secties. |
| `static/index.html` | `renderAutoMode()` nieuw — alle 6 stappen + watch-folders + schedule + queue. |
| `static/index.html` | `brandPackStore.js`-equivalent als IIFE binnen index.html — CRUD voor localStorage. |
| `static/index.html` | `autoModeStore.js`-equivalent — same. |
| `static/index.html` | Settings: nieuwe Account-sectie met Profile-velden die van Brand verhuizen. |

Geen backend-wijzigingen in v1 (lokaal-only). PyInstaller-rebuild nodig om de UI in de bundle te krijgen.

### 5.2 CSS-namespacing

Alles onder `body.redesign-v2` + nieuwe `.v2-brand`, `.v2-automode` prefixes. Geen regressie op legacy-UI. Backup-bestand maken voor en na elke fase.

### 5.3 Routing

NAV_MAP-uitbreiding:

```js
NAV_MAP['brand']    = { id: 'view-brand',    render: 'renderBrand'    };
NAV_MAP['automode'] = { id: 'view-automode', render: 'renderAutoMode' };
```

Sidebar HTML:

```html
<nav class="v2-side-nav">
  <a data-v2nav="analyse">Analyse</a>
  <a data-v2nav="library">Library</a>
  <a data-v2nav="brand">Brand</a>
  <a data-v2nav="social">Social</a>
  <a data-v2nav="calendar">Calendar</a>
  <a data-v2nav="insights">Insights</a>
  <div class="v2-nav-divider"></div> <!-- crème lijntje -->
  <a data-v2nav="automode">Auto-mode</a>
</nav>
```

CSS divider:

```css
.v2-nav-divider {
  height: 1px;
  background: rgba(220, 200, 170, 0.25); /* crème, 25% */
  margin: 12px 16px;
}
```

---

## 6. Fase-opdeling — 6 fases, 8-10 weken

### Fase A — Brand-page redesign (2 weken)

**Doel:** Brand-page volledig herontwerp, Profile-fields verhuizen, Brand Kit + Watermark + Caption-presets werkend.

**Deliverables:**
- Profile-card uit Brand verwijderd, in Settings als nieuwe "Account"-card
- Brand-pack selector top
- Brand Kit card (logo + colors)
- Watermark card
- Caption-presets library + Editor-integratie (Save-as-preset knop in text-drawer)
- Default-preset selector

**Niet in deze fase:** Clip-templates, Hooks/CTAs, Hashtag-sets, Stickers/Lower-thirds/Intro-outro. Die komen in Fase B.

**Smoketest:**
1. Open Brand → Profile-card weg, in Settings staat 'ie
2. Upload logo → preview update
3. Wijzig accent-color → preview update
4. Open editor op een clip → text-drawer → "Save as preset" → preset verschijnt op Brand
5. Default-preset wijzigen → bij nieuwe text-layer komt die default eruit
6. Refresh → alles persist via localStorage

### Fase B — Brand-page deel 2 (1.5 weken)

**Deliverables:**
- Clip-templates library + built-in 4 templates
- Hook-templates + CTA-templates
- Caption-copy templates (post-text)
- Hashtag-sets
- Stickers / Lower-thirds / Intro-outro

**Smoketest:** alle 10 secties zichtbaar en werkend.

### Fase C — Auto-mode UI shell (1.5 weken)

**Deliverables:**
- Sidebar-divider + Auto-mode entry
- `#view-automode` shell met alle cards (Pipeline / Watch-folders / Brand-defaults / Schedule / Queue / Recent runs / Safety)
- Per-stap toggles werkend (UI-only, geen pipeline-execution)
- Quick-enable presets
- Mock-data in alle cards (zelfde aanpak als sessie 56 Insights)
- Paywall-overlay voor Free/Pro
- Default-config nieuwe user = alles OFF

**Smoketest:**
1. Free user: ziet upgrade-overlay, toggles disabled
2. Pro user: ziet upgrade-overlay, toggles disabled
3. Studio user: ziet alle toggles, kan ze togglen, persist via localStorage
4. Quick-enable "Review mode" → 5 toggles ON, Publish OFF
5. Add watch-folder local → entry verschijnt in lijst
6. Add Dropbox-folder → "Coming in Studio+"-toast

### Fase D — Pipeline backend (2-2.5 weken)

**Doel:** Echte pipeline-execution voor lokale watch-folders.

**Deliverables:**
- `watchdog`-based folder-monitor in `app.py` of nieuwe `autopilot.py`
- Job-queue voor multi-step processing (gebruikt bestaande `analyzer.py` + `cutter.py`)
- Status-updates via SocketIO naar frontend (Currently in pipeline card)
- Pipeline_runs table-equivalent in localStorage v1
- Caption-overlays JSON automatisch geschreven met variabele-substitutie
- Stop-bij-OFF logica per stap

**Smoketest:**
1. Studio user zet INTAKE+ANALYSE+CLIP-GEN ON, rest OFF
2. Drop een DJ-set in watch-folder
3. Pipeline triggert binnen 2 min (debounce)
4. Analyse-progress zichtbaar in Currently in pipeline
5. Clips verschijnen in Library na clip-gen
6. Pipeline stopt voor Brand-apply (OFF), wacht op manual approval

### Fase E — Calendar-integratie + Review-flow (1 week)

**Deliverables:**
- Auto-mode → Calendar-queue stap schrijft echte events
- Status `pending_review` zichtbaar als oranje in calendar
- Review-modal met video-preview + Approve/Edit/Reject
- Notification badge op Auto-mode sidebar
- Email-notifications (basis — voor Postiz uitgesteld)

**Smoketest:**
1. Pipeline rendert 5 clips → 5 calendar-events met status pending_review
2. Klik calendar-event → review-modal opent met video + caption + post-text
3. Approve → status scheduled
4. Reject → status rejected
5. Badge op sidebar = aantal pending

### Fase F — Postiz publishing-hookup (uit scope deze planning)

**Deliverables:** Real auto-publish via Postiz cloud API.

Komt in een latere ronde. Zonder deze fase blijft Step 6 PUBLISH een placeholder met "Coming via Postiz".

---

## 7. Risico's & open vragen

| Risico | Impact | Mitigatie |
|---|---|---|
| Brand-pack data overlapt met Stripe-tier-checks | High | Tier-validatie in helper-functie `canUsePremiumPreset(tier, count)`, niet in render-code |
| Pipeline-execution kan vastlopen op grote bestanden (zie CLAUDE.md known issue) | High | Timeouts + chunked processing + crash-recovery via pipeline_runs table |
| localStorage size limits bij veel pipeline_runs | Medium | Cap op laatste 50 runs in localStorage, oudere alleen in Supabase later |
| Watch-folder kan race-conditions hebben (file half geschreven) | Medium | Debounce van 2 min na laatste write, plus file-lock check |
| User configureert Auto-mode verkeerd en mist publishes | Medium | Dry-run mode: "Show me wat de pipeline zou doen voor de laatste 3 sets" |
| Multi-artist + Auto-mode conflicten (welke folder hoort bij welke artist) | High | Verplichte artist-binding per watch-folder bij aanmaken |
| Postiz-API niet beschikbaar bij launch | Low | Fase F is sowieso uitgesteld, dependency duidelijk gedocumenteerd |
| Brand-pack export/import opens veiligheidsrisico (XSS via JSON) | Medium | Sanitize bij import, schema-validation, geen `<script>` of `<iframe>` in tekstvelden |

**Open vragen voor Sjuul:**

1. **Studio+ als nieuwe tier:** Nu reserveren in code (feature-flag), of pas later toevoegen? Mijn voorstel: feature-flag nu, geen Stripe-product.
2. **Default-folder-naam voor Watch-folders:** `~/Music/DJ Sets` of `~/Documents/Omni DJ/Watch`? Mac-conventie?
3. **Email-notifications gebruiken huidige SMTP (sessie 32) of via Postiz?** Mijn voorstel: huidige SMTP voor pipeline-events, Postiz alleen voor social.
4. **Brand-pack delen tussen workspaces:** out-of-scope of must-have voor Studio?
5. **Hooks/CTAs library-grootte limieten:** Free 3? Pro 25? Studio onbeperkt? Same als caption-presets?
6. **Pipeline-run retention:** hoe lang bewaren we logs van runs? 30 dagen? Onbeperkt?

---

## 8. Releasestrategie

3 zichtbare drops naar gebruikers:

**Drop 1 — Brand redesign (na Fase A+B, ~3.5 wkn)**
- Communicatie: "Brand-page is now your full creative toolkit"
- Migration-banner voor bestaande users: "We've moved Profile to Settings"
- Geen breaking change — alle bestaande brand-data blijft werken

**Drop 2 — Auto-mode UI preview (na Fase C, +1.5 wkn = 5 wkn)**
- Communicatie: "Auto-mode is here — preview now, Studio only"
- Free/Pro zien upgrade-prompt
- Studio kan configureren maar pipeline doet nog niets (UI-only)
- Sjuul kan zelf eerste feedback verzamelen voordat backend live gaat

**Drop 3 — Auto-mode live (na Fase D+E, +3.5 wkn = 8.5 wkn)**
- Communicatie: "Auto-mode is now executing your pipeline"
- Studio users krijgen email: "Your watch-folders are now active"
- Postiz-publishing nog steeds placeholder — duidelijk gecommuniceerd

---

## 9. Wat NIET in dit plan zit (expliciet)

- Postiz-publishing live (Fase F, apart)
- Dropbox / Google Drive backend (alleen UI in v1)
- Stripe Studio+ product (alleen feature-flag reserveren)
- Multi-tenant Supabase-laag (zit in bestaande PLAN-CONTENT-CALENDAR Fase 5b)
- Reset-password.html standalone polish (open punt sessie 48)
- Code-rebrand Omni DJ → Omni DJ (aparte sessie volgens HANDOVER)
- App-icon / bundle-identifier rebrand (idem)
- omnidj.com DNS koppelen (idem)
- App Store / DMG distributie

---

## 10. Aanbevolen volgorde voor implementatie

1. **Eerst** dit plan akkoord van Sjuul.
2. **Daarna** PyInstaller rebuild om sessie 56 in de bundle te krijgen (uit HANDOVER Stap 2 — al klaar gepland).
3. **Daarna** Fase A starten — Brand-page redesign deel 1.
4. Per fase: backup vóór wijzigingen, smoketest na wijzigingen, commit + HANDOVER-update.
5. Fase F (Postiz) opnieuw plannen wanneer Postiz cloud-account er is.

---

## 11. Schatting in uren (developer-time, niet kalender)

| Fase | Uren |
|---|---|
| A | 40-50 |
| B | 30-40 |
| C | 30-40 |
| D | 50-60 |
| E | 20-25 |
| F (later) | 40-50 |
| **Totaal v1 (zonder F)** | **170-215 uur** |

Bij 20 uur per week dev = 8.5-11 weken. Plus 10-20% buffer voor smoketest-bevindingen + rebuilds = **10-13 weken kalender**.

---

## 12. Diensten / kosten check

| Service | Nu? | Voor dit plan? |
|---|---|---|
| Supabase (Free tier) | Ja | Reikt voorlopig — nieuwe tabellen passen erin |
| Stripe test mode | Ja | Geen prijs-wijziging in deze planning |
| Cloudflare Pages | Nee (in HANDOVER nog te koppelen) | Niet vereist voor dit plan |
| Postiz Cloud | Nee | Voor Fase F nodig — apart aanvragen |
| watchdog (Python lib) | Nee | `pip install watchdog` in venv, geen kosten |

---

## 13. Checklist voor Sjuul vóór implementatie

- [ ] Akkoord op tier-matrix (sectie 1)
- [ ] Akkoord op Brand-page 10 secties (sectie 2)
- [ ] Akkoord op Auto-mode 6-stappen pipeline (sectie 3)
- [ ] Akkoord op data-model + localStorage v1 approach (sectie 4)
- [ ] Akkoord op fasering A → E (sectie 6)
- [ ] Antwoorden op open vragen sectie 7
- [ ] Bevestiging: Postiz uit scope deze planning
- [ ] Bevestiging: Dropbox/Drive UI-only

---

## 14. Bestanden die door dit plan worden geraakt

- `dj-clip-cutter/static/index.html` — CSS, DOM, JS uitbreiding
- `dj-clip-cutter/app.py` — Fase D: watch-folder monitor + job-queue endpoints
- `dj-clip-cutter/autopilot.py` — NIEUW Fase D: pipeline-orchestrator
- `supabase/migrations/00X_brand_packs.sql` — NIEUW Fase A
- `supabase/migrations/00Y_auto_mode.sql` — NIEUW Fase D
- `HANDOVER.md` — update per fase
- `requirements.txt` — `watchdog` toevoegen Fase D

---

**Einde plan.** Wachtend op Sjuul's akkoord per sectie of `ga maar`.
