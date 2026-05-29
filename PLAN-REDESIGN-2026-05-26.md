# Omni DJ — Redesign Plan v1.0
**Datum:** 2026-05-26
**Doel:** Premium dark-first redesign van de tool, schaalbaar voor toekomstige features. Resultaat van deze sessie: 1 HTML MVP met de volledige flow (upload → processing → clips → export), klaar om later 1-op-1 door te vertalen naar de landing page.

---

## 1. Design-richting (vastgesteld met Sjuul)

| Onderdeel | Keuze |
|---|---|
| Modus | Dark-mode first (light-mode later, niet nu) |
| Sfeer | Premium, monochroom, clean — referenties: Linear, Supabase, cobrand.com, Notion |
| Accent | Oranje, héél spaarzaam, géén glow, géén gradient |
| Sidebar-model | Supabase-shell (workspace-switcher boven, settings onder) met TIMA-categorieën in het midden |
| Scope MVP | Hele flow in 1 HTML: upload → processing → clips → export |
| Toekomst-ready voor | Content Calendar (Postiz), multi-artist switcher, Ads-systeem, Brand Stack |

---

## 2. Kleurpalet

Near-black achtergrond met warme tinten, géén pure zwart of pure wit — anders voelt het klinisch in plaats van premium.

```
/* Surfaces */
--bg-base:        #0E0E0F    /* hoofdachtergrond — near-black met warmte */
--bg-sidebar:     #0A0A0B    /* sidebar iets donkerder dan canvas */
--bg-elevated:    #161618    /* cards, modals, dropdowns */
--bg-hover:       #1E1E21    /* hover state op rows en buttons */
--bg-input:       #131315    /* input/textarea */

/* Borders */
--border-subtle:  rgba(255, 255, 255, 0.06)   /* card borders, dividers */
--border-default: rgba(255, 255, 255, 0.10)   /* input borders */
--border-strong:  rgba(255, 255, 255, 0.16)   /* focused, active */

/* Text (warm cream, geen pure wit) */
--text-primary:   #F5F2EC    /* headlines, body */
--text-secondary: #A8A39A    /* labels, captions */
--text-tertiary:  #6B6863    /* hints, disabled */
--text-inverse:   #0E0E0F    /* tekst op accent-bg */

/* Accent — oranje, gedempt */
--accent:         #D97742    /* hoofdoranje — gebrand, niet neon */
--accent-hover:   #E08854
--accent-muted:   rgba(217, 119, 66, 0.12)   /* achtergrond van active nav-item */
--accent-border:  rgba(217, 119, 66, 0.30)

/* Status (gedempt, niet schreeuwerig) */
--success:        #6FAE7E
--warning:        #C9A66B
--danger:         #C16A5C
```

**Belangrijke regel:** oranje wordt alleen gebruikt voor:
- Active nav-item (linker rand 2px + tekst in accent)
- Primary CTA (1 per scherm max)
- Progress indicator op processing
- Selected-state op clip-kaarten (1px border)

Géén oranje voor: hover-states (gebruik `--bg-hover`), badges (gebruik gedempt cream), of decoratie.

---

## 3. Typografie

Eén familie, drie gewichten — onnodige variatie = onrust.

```
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
```

| Rol | Size | Weight | Line-height | Letter-spacing |
|---|---|---|---|---|
| Display (page title) | 28px | 600 | 1.2 | -0.02em |
| H2 (section header) | 18px | 600 | 1.3 | -0.01em |
| H3 (card title) | 14px | 600 | 1.4 | -0.005em |
| Body | 13px | 400 | 1.5 | 0 |
| Label / nav-item | 13px | 500 | 1.4 | 0 |
| Caption / meta | 11px | 500 | 1.4 | 0.04em (uppercase voor categorie-headers) |
| Mono (timestamps, BPM) | 12px | 500 | — | `'JetBrains Mono', monospace` |

Categorie-headers in sidebar (CREATIVEOS, etc.) → 11px / 500 / uppercase / 0.08em letter-spacing / `--text-tertiary`.

---

## 4. Spacing & radii

```
--space-1: 4px
--space-2: 8px
--space-3: 12px
--space-4: 16px
--space-5: 24px
--space-6: 32px
--space-7: 48px

--radius-sm: 6px    /* buttons, inputs, nav-items */
--radius-md: 10px   /* cards, modals */
--radius-lg: 14px   /* hoofd-containers, clip-thumbs */
```

Sidebar-breedte: **240px** (collapsed: 60px). Topbar-hoogte: **52px**.

---

## 5. Sidebar-architectuur

Drie zones, van boven naar beneden:

### Zone A — Workspace-switcher (top, ~64px)
- Logo + workspace-naam ("MONO LABS") + chevron-dropdown
- Klik opent dropdown met: andere workspaces, "+ New workspace", "Workspace settings"
- Toekomstklaar voor multi-artist

### Zone B — Navigatie-blokken (scroll-area)
TIMA-stijl categorieën. Elk blok heeft een uppercase header (caption-stijl) en items eronder. Active item krijgt 2px linker rand in oranje + tekstkleur naar accent + lichte `--accent-muted` achtergrond.

```
CLIPOS                     ← huidige hoofdfunctie
  ⬆ Upload
  ✂ Clips                  (huidige clips-overzicht)
  ⏱ Queue                  (processing-queue, ook handig voor batch)
  📁 Library               (archief van eerdere sessies)

CREATIVEOS                 ← branding & customization
  🎨 Brand Stack
  Aa Fonts & captions
  🎚 Presets               (toekomstige feature)

PUBLISHOS                  ← Postiz-integratie + content cal
  📅 Calendar              (Postiz-integratie)
  📤 Publish               (queue van geplande posts)
  🔗 Channels              (verbonden socials)

INSIGHTS                   ← toekomstig: Ads + analytics
  📊 Performance           (TikTok/IG analytics per clip)
  💰 Ads                   (Intellijend-model, laatste fase)
  👥 Audience              (toekomstig)

WORKSPACE
  🔌 Integrations
  💳 Billing
  ❓ Support
```

### Zone C — Footer (bottom, ~48px, sticky)
Klein settings-menu zoals gevraagd. Twee items, low-key:
- ⚙ Settings (opent settings-modal of /settings)
- 👤 Account-avatar + email (klik = dropdown: profiel / logout / theme-switch later)

Visueel gescheiden van Zone B met een dunne `--border-subtle` divider.

---

## 6. Topbar (52px)

Minimaal. Links: huidige page-titel + breadcrumb als relevant. Rechts: ⌘K search-trigger, notificatie-bell, "+ New clip" primary button (oranje, alleen op relevante pages).

Geen tabs in de topbar — die zitten binnen de page als secondary nav indien nodig.

---

## 7. Hoofd-content patronen

### 7.1 Upload-scherm (eerste scherm)
- Grote dropzone (cream-strepen border, dashed, hover → solid + lichte `--bg-hover`)
- "Drop your set" + small caption "WAV, MP3, MP4 — tot 4GB"
- Onder dropzone: 3 quick-presets (30s drops / 60s buildups / Auto-detect) als kleine pill-buttons
- Recent uploads (laatste 3) als kleine cards links onderin

### 7.2 Processing-scherm
- Centraal: progress-circle (8px stroke, oranje accent, géén glow)
- Stage-tekst eronder: "Analyzing drops... 47%"
- Onder progress: live log (mono font, `--text-secondary`, scrollable, max 4 regels zichtbaar) — geeft het premium-tool gevoel
- Cancel-button (ghost, niet danger-rood)

### 7.3 Clips-overzicht (hart van de app)
- Grid van clip-kaarten (3-kolommen op desktop, 2 op tablet)
- Elke kaart: 9:16 thumb (of 16:9 toggle), titel, BPM-badge, drop-tijdstip, duration
- Hover: subtiele lift (translateY -1px) + border verandert naar `--border-strong`
- Selected: 1px oranje border + checkmark linksboven
- Bulk-action bar verschijnt onderin bij selectie (zoals Notion table-selection)

### 7.4 Clip-detail (modal of side-panel)
- Side-panel voorkeur (480px breed, schuift in van rechts), modal voor edit-acties
- Video preview boven, controls onder, transcript/caption-editor als tab
- Acties: Recut, Add captions, Export, Schedule (Postiz)

### 7.5 Export-modal
- Format-keuze (MP4, MOV), resolutie, captions on/off, filename-rename veld
- "Save to" picker (user-home whitelist zoals afgesproken in sessie 43)
- Primary CTA: "Export" (oranje)

---

## 8. Componenten-bibliotheek (in MVP definiëren)

| Component | Specs |
|---|---|
| Button-primary | bg `--accent`, text `--text-inverse`, 32px hoog, 12px padding, radius-sm |
| Button-ghost | transparent, border `--border-default`, hover `--bg-hover` |
| Button-secondary | bg `--bg-elevated`, hover `--bg-hover` |
| Input | bg `--bg-input`, border `--border-default`, focus border `--border-strong` (géén oranje glow) |
| Card | bg `--bg-elevated`, border `--border-subtle`, radius-md, 16px padding |
| Badge | bg `--bg-elevated`, text `--text-secondary`, 11px, radius-sm, 4px/8px padding |
| Divider | `--border-subtle`, 1px |
| Modal | bg `--bg-elevated`, backdrop `rgba(0,0,0,0.6)` blur-sm, radius-lg |
| Tooltip | bg `#1E1E21`, text `--text-primary`, 12px, radius-sm |

---

## 9. Wat verandert er t.o.v. huidige UI

| Huidig | Nieuw |
|---|---|
| OpusClip-stijl (single layout, geen sidebar?) | Linear/Supabase-shell met persistente sidebar |
| Onzeker accent-gebruik | Oranje is schaars; cream domineert |
| Geen workspace-concept | Workspace-switcher boven, klaar voor multi-artist |
| Settings ergens in topbar/menu | Settings als sidebar-footer, account-avatar erbij |
| Feature-set niet uitbreidbaar | 4 OS-blokken die meegroeien |

---

## 10. Acceptatiecriteria voor HTML MVP

De HTML is geslaagd als:
1. Alle 5 schermen (upload, processing, clips-grid, clip-detail, export) bestaan in 1 file
2. Sidebar werkt: tussen schermen wisselen via nav-items
3. Volledig dark-mode, oranje wordt nergens meer dan 4 keer per scherm gebruikt
4. Responsive: ≥1280px desktop optimaal, ≥1024px werkt netjes
5. Geen externe afhankelijkheden behalve Inter via Google Fonts + 1 SVG icon-set inline
6. Bestand heet `clip-live-redesign-v2.html` en staat naast de bestaande mockup
7. Bij elk scherm minimaal 1 echte content-state (dus geen lege placeholders) zodat je het "premium gevoel" kunt voelen

---

## 11. Wat ik **niet** ga doen in deze sessie

- Geen Python-code aanraken
- Geen light-mode variant
- Geen echte data-koppeling (alles is statisch in de HTML)
- Geen verandering aan de bestaande `static/index.html` — de nieuwe file leeft naast de oude, zodat je 1-op-1 kunt vergelijken
- Geen landing-page (komt later, op basis van dit design-systeem)

---

## 12. Vervolg na akkoord

1. Ik bouw `clip-live-redesign-v2.html` in 1 keer in `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/`
2. Jij opent 'm in je browser, klikt door de 5 schermen
3. Feedback → ik pas aan (iteratief)
4. Daarna pas: doorvertaling naar Python/Flask templates + landing page
