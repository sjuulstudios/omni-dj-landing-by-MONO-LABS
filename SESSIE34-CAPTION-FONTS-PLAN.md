# SESSIE 34 — Caption Fonts + Color Wheel Plan

> Datum: 2026-05-23
> Status: Plan-document — niets geïmplementeerd
> Author: Claude (sessie 34) op basis van Sjuul's verzoek

---

## Doel

Sjuul wil dat eindgebruikers in het tekstpaneel ("Text on this clip") veel meer keuze hebben:

1. **Een uitgebreide lijst captionfonts** — niet alleen System sans + brand-stack
2. **Live hover-preview** in de font-dropdown (font-naam getoond IN dat font)
3. **Vrije text-kleur** via een color wheel (geen 5-swatch palette)
4. **Vrije achtergrond-kleur** via een color wheel (nu alleen on/off met vaste zwart-tint)

## Wat is er al (sessie 21, brand-stack v1)

- `STATE.brandKit.fonts` is een array met user-uploaded TTF/OTF/WOFF fonts
- `_renderBrandFontFaces()` injecteert `@font-face` op de pagina
- `editorTextRenderControls()` bouwt de `#ed-tx-font` dropdown van Brand Stack fonts + "System sans"
- `cutter.py / _build_text_layer_filters` resolved `font_id` → `brand_kit/fonts/<file>` op disk, valt anders terug op `_get_system_font()` (Helvetica/Arial/DejaVu)
- Kleur: 5 swatches uit `STATE.brandKit.palette` + altijd geforceerd #fff/#000
- Background: één boolean toggle `L.bg` → ffmpeg `box=1:boxcolor=0x000000@0.55`

## Wat dit plan toevoegt

### Fase A — Ingebakken font-library (~3 uur)

**Beslissing:** we bakken een set Google Fonts mee in de app zelf. Dat geeft:
- Geen extra upload-stap voor eindgebruikers
- Bekende, gelicensieerde fonts (OFL/Apache 2.0 — gratis voor commercieel gebruik)
- Werkt offline (cruciaal voor de dmg-distributie)
- FFmpeg krijgt hetzelfde fontfile-pad → preview en burn-in matchen 1-op-1

**Font-selectie — 12 fonts, gekozen op DJ/event/social-context:**

| Category | Font | Waarom |
|---|---|---|
| Sans neutraal | Inter | UI-standaard, neutraal |
| Sans display | Bebas Neue | Allcaps, "festival poster" |
| Sans heavy | Anton | Heel zwaar, TikTok-stijl |
| Sans rounded | Nunito | Vriendelijk, IG Reels |
| Sans condensed | Oswald | Compact, drop-stamps |
| Serif klassiek | Playfair Display | Editorial, premium |
| Serif modern | Fraunces | Past bij huidige brand |
| Display retro | Bungee | Geometrisch, club-vibe |
| Mono | JetBrains Mono | Time-codes, drop-marks |
| Script | Caveat | Handwritten, persoonlijk |
| Display | Permanent Marker | Sharpie-stijl, hand-drawn |
| Display | Press Start 2P | 8-bit retro, gaming |

Bundle-grootte: ~12 × 50-200 KB = **~1-2 MB extra** in de dmg. Te overzien.

**Implementatie:**

1. Maak `dj-clip-cutter/static/fonts/` met de 12 `.ttf`/`.woff2` files + een `licenses/` submap
2. Eén `static/fonts/manifest.json`:
   ```json
   [
     {"id":"inter",      "family":"Inter",            "file":"Inter-Regular.woff2",      "ffmpeg":"Inter-Regular.ttf",      "category":"sans"},
     {"id":"bebas",      "family":"Bebas Neue",       "file":"BebasNeue-Regular.woff2",  "ffmpeg":"BebasNeue-Regular.ttf",  "category":"display"},
     ...
   ]
   ```
   We bundelen **dubbel**: `.woff2` voor browser (`@font-face`) en `.ttf` voor ffmpeg (`fontfile=`). Anders moet ffmpeg woff2 lezen → niet altijd ondersteund.
3. Nieuw Flask-endpoint `GET /api/builtin-fonts` returnt het manifest + statische serving van `/static/fonts/*` (Flask doet dat al via `static_url_path`)
4. Bij app-load: fetch `/api/builtin-fonts`, injecteer `@font-face` net als brand-kit fonts, store in `STATE.builtinFonts`
5. `editorTextRenderControls()` bouwt de dropdown nu als drie secties:
   ```
   ─ System ─
     System sans
   ─ Built-in ─
     Inter
     Bebas Neue
     ...
   ─ Brand Stack ─
     <user uploads>
   ```
6. `cutter.py` `_build_text_layer_filters` krijgt extra dispatch:
   - `font_id` matcht builtin → resolve naar `static/fonts/<file>.ttf` (absoluut pad)
   - Anders → brand-kit, anders → system

**Risico:** PyInstaller bundle moet `static/fonts/` meenemen. Check `ClipLive.spec` — die heeft al `datas=[('static', 'static')]` (verwachting), dus inclusief.

### Fase B — Hover-preview in font-dropdown (~2 uur)

`<select>` is OS-native en kan niet gestyled worden per-option. Oplossing: vervang met een custom dropdown widget.

**Approach (zelfde idee als het export-popover-menu uit sessie 34a):**

```html
<div class="ed-tx-fontpicker">
  <button class="ed-tx-fontpicker-btn">
    <span class="font-name" style="font-family: 'Bebas Neue'">Bebas Neue</span>
    <span class="caret">▾</span>
  </button>
  <div class="ed-tx-fontpicker-menu" hidden>
    <div class="ed-tx-fontpicker-section">SYSTEM</div>
    <div class="ed-tx-fontpicker-opt" data-id="" style="font-family: -apple-system">System sans</div>
    <div class="ed-tx-fontpicker-section">BUILT-IN</div>
    <div class="ed-tx-fontpicker-opt" data-id="inter" style="font-family: 'Inter'">Inter</div>
    <div class="ed-tx-fontpicker-opt" data-id="bebas" style="font-family: 'Bebas Neue'">Bebas Neue</div>
    ...
  </div>
</div>
```

- Elke `.ed-tx-fontpicker-opt` rendert zijn **eigen naam in zijn eigen font** → instant visuele preview zonder hover
- Hover toont een extra preview-tooltip met de letters "Aa 1234 — Drop here" in dat font, ~3× zo groot, naast de optie
- Click → sluit menu, update layer + live-preview
- Keyboard: pijltjes + Enter werken (focus-trap binnen menu)

**Trade-off:** custom dropdown is meer code dan native `<select>` maar de hover-preview is fundamenteel onmogelijk met native select. Niet onderhandelbaar.

### Fase C — Color wheel voor text-kleur (~2 uur)

Vervang de 5-swatches grid door een full color picker. Twee opties:

**Optie 1 — `<input type="color">`** (native, 0 KB JS, lelijk maar werkt)

```html
<input type="color" id="ed-tx-color" value="#ffffff">
```

Wel: 100% browser-native, geen library, accessibility gratis.
Niet: OS-native widget die afwijkt van onze brand styling. Op macOS opent het de macOS color picker — dat is feitelijk een full color wheel. Op Windows ander widget.

**Optie 2 — Bundeled JS color picker** (custom, mooi, ~6 KB)

Libraries:
- [Pickr](https://github.com/Simonwep/pickr) — 6 KB, hue ring + saturation square + alpha + hex
- [iro.js](https://iro.js.org/) — 8 KB, configurable wheel + saturation
- [Coloris](https://coloris.js.org/) — 4 KB, simpel, fits dark themes

**Aanbeveling:** **Pickr** of **Coloris**, beide inline gebundeld (download .min.js naar `static/vendor/`). Geen CDN want offline-distributie.

**Layout:**

```
COLOUR
[white swatch][black swatch][amber swatch] [+ open picker]
                                            ↓ klikt opent inline picker
                                            ┌──────────┐
                                            │ wheel    │
                                            │ + hex    │
                                            │ #f4cf8a  │
                                            └──────────┘
```

- Keep 3 quick-swatches (wit/zwart/brand-amber) voor 1-click toegang
- Plus-knop opent de picker
- Custom hex blijft persistent als 4e swatch tot je opnieuw kiest

**Data-impact:** `L.color` is nu al een hex-string, dus zero schema-change. `_hex_to_ffmpeg_color()` in cutter.py werkt al voor any hex.

### Fase D — Color wheel voor background-kleur (~1.5 uur)

Background is nu een boolean `L.bg` → hardcoded zwart 55% opaak.

**Nieuw schema:**

```js
L.bg = null                  // geen achtergrond
L.bg = {
  color: '#000000',
  opacity: 0.55              // 0..1
}
```

Back-compat: bestaande `L.bg === true` blijft `box=1:boxcolor=0x000000@0.55` (de huidige hardcoded fallback in cutter.py).

**UI:**

Vervang de huidige `Off / On` toggle met:

```
BACKGROUND
[ Off ] [ ◐ ]   ← klik op cirkel opent picker
              ┌──────────┐
              │ wheel    │
              │ hex      │
              │ opacity  │  ← extra slider 0-100%
              │ ━━━━━━●━ │
              └──────────┘
```

`cutter.py` `_build_text_layer_filters` regel ~338-339:

```python
if L.get('bg'):
    bg = L['bg']
    if bg is True:
        bg_color, bg_alpha = '#000000', 0.55
    else:
        bg_color = bg.get('color', '#000000')
        bg_alpha = float(bg.get('opacity', 0.55))
    color_hex = _hex_to_ffmpeg_color(bg_color)  # nieuwe helper
    box_part = f':box=1:boxcolor={color_hex}@{bg_alpha:.2f}:boxborderw=12'
```

### Fase E — Verificatie & test (~1 uur)

1. Unit-check: lokaal `python3 -c "from cutter import _build_text_layer_filters"` import-test
2. Functional: open editor, kies elk nieuw built-in font, kies vrije kleur, kies vrije bg-kleur, klik Trim, verifieer met `ffprobe` dat output mp4 bestaat + kijk met VLC
3. Cross-browser: Chrome + Safari hard-refresh
4. Backups: `static/index.html.pre-sessie34b.bak`, idem app.py + cutter.py

---

## Totaal scope

| Fase | Wat | Effort |
|---|---|---|
| A | Bundle 12 fonts + manifest + Flask endpoint + dropdown sections | 3 u |
| B | Custom font-picker met hover-preview | 2 u |
| C | Color wheel voor text | 2 u |
| D | Color wheel voor background + opacity | 1.5 u |
| E | Verificatie + backups + smoketest | 1 u |
| | **Totaal** | **~9.5 u** |

Praktisch: doe A+B in één sessie, C+D in een tweede, E aan het eind.

---

## Beslispunten voor Sjuul

**B1.** Akkoord met 12 ingebakken fonts (~1-2 MB bundle-overhead)? Of liever minder/meer?

**B2.** Color picker library — voorkeur **Coloris** (4 KB, donker-thema vriendelijk) of **Pickr** (6 KB, meer features)?

**B3.** Doen we tegelijk de back-compat voor `L.bg === true` of mag elke oude clip-tekst gemigreerd worden naar het nieuwe schema?

**B4.** Volgorde: A+B eerst (fonts) of C+D eerst (kleuren)?

---

## Risico's / open einden

- **PyInstaller**: `ClipLive.spec` moet `static/fonts/**` includeren. Verificatie: na build `ls -R "dist/Clip Live.app/Contents/Resources/static/fonts"`.
- **Drawtext-render**: sommige display fonts hebben rare metrics (Bebas Neue heeft hoge x-height). De `size_pct → fontsize` formule kan visueel afwijken tussen fonts. Acceptabel — gebruiker stelt size_pct in op het oog.
- **Press Start 2P (8-bit)** geeft soms ffmpeg-glyph-warnings als pixels niet exact passen. Niet kritisch — geeft alleen log-noise.
- **Caveat (script)**: cursive fonts hebben overlappende glyphs in drawtext (geen ligaturen). Resultaat ziet er soms "verkleind" uit. Documenteren.
- **Hex met alpha** (8-digit hex zoals `#ff000080`) — ffmpeg drawtext snapt dat niet native. Daarom apart `color@opacity` in box_part. Voor fontcolor: niet ondersteund → opacity-slider is alléén voor background, niet voor text.
