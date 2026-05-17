# Sessie 1 — Editor verbeteringen (waveform, alignment, positie, trim-stretch)

> **Voor de nieuwe sessie: lees ook HANDOVER.md en .claude/CLAUDE.md eerst.**
> Dit document bevat het volledige plan en de exacte code-locaties voor sessie 1.
> Plan is in vorige sessie afgestemd met Sjuul. Begin met stap A en werk door.

---

## Wat sessie 1 oplevert

Vier samenhangende wijzigingen in de Editor view:

1. Waveform per clip in hoge resolutie (Premiere-Pro-stijl mirror)
2. Filmstrip + waveform exact uitgelijnd op dezelfde tijdas
3. Positie-indicator boven timeline ("Clip 3 of 12 · 47:23 / 2:15:08 in set")
4. Trim-handles die ±60s buiten de huidige clipgrenzen kunnen stretchen

**Buiten scope deze sessie** (komt in latere sessies):
- Export-popup met codec/fps dropdowns (sessie 2)
- Supabase auth + onboarding flow (sessie 3)
- .dmg / .exe installer (sessie 4)

---

## Eerste stap: backup maken

Voordat je 1 regel aanpast, kopieer:
```
/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter/static/index.html
```
naar:
```
/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter/static/index.html.pre-sessie1.bak
```

Er staan al twee oudere `.bak` bestanden in dezelfde folder — consistent met hoe Sjuul het eerder deed.

---

## Werkvolgorde (A → E) met testmomenten

### Stap A — Backend voorbereiding

Twee minimale dingen, geen grote backend-rewrite:

**A1. Set-duur beschikbaar in editor.**
De positie-indicator heeft de totale set-duur nodig (`snap['duration']` in app.py). Check of een bestaand endpoint dit al teruggeeft naar de frontend. Zo niet: voeg het toe aan het endpoint dat de clip-lijst voor de editor laadt. Geen nieuw endpoint maken als het via een bestaand veld kan.

**A2. Waveform endpoint check.**
`GET /api/waveform/<job_id>/clip/<idx>?bins=N` accepteert al `bins` 60–2000. Geen backend-wijziging nodig — de frontend gaat gewoon `bins=2000` aanvragen.

**Test na A:** start de app, open editor, log in browser console of `bins=2000` daadwerkelijk werkt en of `set_duration` in de clip-state zit.

### Stap B — Frontend waveform renderer

Bestand: `dj-clip-cutter/static/index.html`
Functie: `drawWaveformCanvas(wave, peaks)` — **regels 2885–2927**

Vervang de bar-loop door:

- 2000 peaks ipv 600 (frontend-fetch op regel 2697 wijzigen naar `?bins=2000`)
- **Mirror-stijl:** bovenste helft positief, onderste helft gespiegeld om centerline `cy = h / 2`
- Geen losse rechthoekjes meer; gebruik `ctx.beginPath() + ctx.lineTo()` om één continue gevulde envelope te tekenen — geeft Premiere-look
- **RMS-glow approximatie:** smooth de peaks via moving average (window van 12) en teken die als doffere glow onder de scherpe peaks. Geen extra backend call nodig.
- Kleurverloop: amber-2 (#f4cf8a) bovenaan → copper (#c2864a) onderaan. Drops blijven helder omdat ze hoger reiken in het verloop.

**Test na B:** open een clip in de editor, kijk of de waveform er gedetailleerd uitziet en of de drops als duidelijke pieken zichtbaar zijn. Vergelijk visueel met huidige 600-bar render.

### Stap C — Filmstrip + waveform alignment

Beide tracks zitten al in `.tl-zoomwrap` met `width:100%` en delen dus dezelfde fysieke breedte. Echte alignment-issue: ze moeten ook **dezelfde virtuele tijd-mapping** krijgen wanneer trim-handles in stap E kunnen uitsteken.

Voeg toe in JS (boven `renderTrimRegion`, rond regel 3100):

```js
// Single source of truth voor tijd-naar-pixel mapping in editor.
// Wordt gebruikt door waveform, filmstrip, trim-handles en playhead.
function getEditorTimeMap(clip){
  const stretch = 60; // max seconden uitstrekken aan elke kant
  const setDur  = (STATE.set && STATE.set.duration) || 0;
  const leftMax  = Math.min(stretch, clip.start || 0);
  const rightMax = Math.min(stretch, Math.max(0, setDur - (clip.end || 0)));
  return {
    clipStart:  clip.start,
    clipEnd:    clip.end,
    clipDur:    (clip.end - clip.start),
    leftMax, rightMax,
    vDur:       (clip.end - clip.start) + leftMax + rightMax,
  };
}
```

Filmstrip + waveform blijven 0..clipDur tonen. De `vDur`-mapping wordt alleen door de trim-handles gebruikt om hun positie buiten de clip-grenzen te bepalen.

**Test na C:** geen visueel verschil verwacht (mapping wordt pas in stap E gebruikt). Wel checken dat `getEditorTimeMap` correct rekent in console: `getEditorTimeMap(STATE.clips[STATE.selectedClipIdx])`.

### Stap D — Positie-indicator

Bestand: `static/index.html`, **regel 2745**

Huidig:
```js
if (frameLabel) frameLabel.textContent = `${setTitle} · clip ${idx+1}`;
```

Wordt:
```js
if (frameLabel) {
  const total   = STATE.clips.length;
  const setDur  = (STATE.set && STATE.set.duration) || 0;
  const fmt = (s) => {
    s = Math.max(0, Math.floor(s));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return h > 0
      ? `${h}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
      : `${m}:${String(sec).padStart(2,'0')}`;
  };
  frameLabel.textContent =
    `Clip ${idx+1} of ${total} · ${fmt(clip.start)} / ${fmt(setDur)} in set`;
}
```

**Test na D:** open editor, label moet "Clip 3 of 12 · 47:23 / 2:15:08 in set" tonen ipv "set · clip 3".

### Stap E — Trim-handles ±60s stretch

Bestand: `static/index.html`
Functie: `renderTrimRegion(dur)` — **regels 3106–3169**

Wijzigingen:

1. **Mapping van % naar seconden gaat via `getEditorTimeMap`**, niet meer puur op `dur`:
   - `vDur = leftMax + clipDur + rightMax`
   - Handle-positie in % = `((value + leftMax) / vDur) * 100` waarbij `value` de seconden vanaf clip-start is (kan negatief zijn).

2. **Drag-clamp wordt:**
   ```js
   const map = getEditorTimeMap(currentClip);
   // sec is nu vanaf 0 tot map.vDur (over de hele track)
   const valueFromStart = sec - map.leftMax; // kan negatief zijn
   if (drag.kind === 'in') {
     tt.inSec = Math.max(-map.leftMax, Math.min(valueFromStart, tt.outSec - 0.25));
   } else {
     tt.outSec = Math.max(tt.inSec + 0.25, Math.min(valueFromStart, map.clipDur + map.rightMax));
   }
   ```
   `tt.inSec` en `tt.outSec` worden seconden **vanaf clip-start** (negatief = links van originele start, positief = binnen of na de clip).

3. **Visueel: gedimde stretch-zones links/rechts van originele clip.**
   Voeg in HTML twee dim-overlays toe binnen `.trim-region` (regel 1197), of teken ze met CSS `linear-gradient` op `.tracks` zelf:
   - `0%..(leftMax/vDur*100)%`: gedimd, gestreepte achtergrond
   - `((leftMax+clipDur)/vDur*100)%..100%`: idem rechts
   Originele clip-zone blijft normaal.

4. **Bij Apply / Recut:**
   `start = clip.start + tt.inSec` (kan dus eerder zijn dan originele `clip.start`)
   `end   = clip.start + tt.outSec`
   Bestaande `/api/recut` endpoint accepteert al arbitrary start/end — geen backend-wijziging.
   Na succesvolle recut: refresh clip-data (filmstrip + waveform worden via bestaande flow opnieuw geladen).

**Test na E (dit is de echte end-to-end test):**
- Open een clip in editor
- Sleep linker handle 30s naar links (buiten originele clip-start) → gold band groeit, gedimde zone links wordt kleiner
- Sleep rechter handle 45s naar rechts (na originele clip-end)
- Klik "Apply" / "Recut" → controleer dat de uitgevoerde clip langer is dan origineel, met de juiste audio/video voor en na
- Edge cases: clip dicht bij begin van set (links < 60s mogelijk), clip dicht bij einde (rechts < 60s mogelijk) — de `Math.min(stretch, ...)` clamp regelt dit

---

## Code-locaties (kaart van vorige sessie)

### `static/index.html`
| Wat | Regels |
|---|---|
| Editor template HTML | 1117–1218 |
| Trim region elements | 1197–1201 (`#tl-trim-in`, `#tl-trim-band`, `#tl-trim-out`) |
| Filmstrip element | 1206 (`#tl-frames`) |
| Waveform element | 1211 (`#tl-wave`) |
| Editor CSS | 601–690 (timeline, tracks, trim-handle, wave) |
| `drawWaveformCanvas` | 2885–2927 |
| Waveform fetch + cache | 2682–2734 (fetch op 2697) |
| Filmstrip fetch | 2747–2756 |
| Frame label (clip-positie) | 2745 |
| `renderTrimRegion` | 3106–3169 |
| `bindTimelineScrub` | 3230–3256 |

### `cutter.py`
| Wat | Regels |
|---|---|
| `get_per_clip_waveform(audio_path, start, end, bins=600, sr=22050)` | 407–442 |
| `recut_clip(...)` — accepteert arbitrary start/end | 848–876 |
| `extract_clip_filmstrip(...)` | 946–983 |

### `app.py`
| Endpoint | Regels |
|---|---|
| `GET /api/waveform/<job>/clip/<idx>?bins=...` | 1428–1481 |
| `GET /api/waveform/<job>` (legacy fallback) | 1484–1491 |
| `POST /api/recut/<job>` | 1494–1542 |
| `GET /api/clip-filmstrip/<job>/<idx>?n=...` | 1996–2027 |

---

## Kritisch: niet kapot maken

De volgende dingen werken nu en moeten blijven werken:
- Split clip (`/api/split-clip`, ergens rond regel 3007–3086 in index.html)
- Recut bestaande flow (alleen uitbreiden, niet vervangen)
- Aspect-ratio swap (9:16 / 16:9 / 1:1 / 4:5)
- Stage click-to-play (`bindStagePlayToggle`)
- Timeline scrub op andere posities dan trim-handles (`bindTimelineScrub` op regel 3230 zorgt dat trim-handle drags genegeerd worden — die check moet blijven)

Bekende terugkerende bugs (zie HANDOVER.md):
- **Duplicate clips bug** — clips tonen soms identieke video. Niet veroorzaakt door deze sessie maar wees alert tijdens testen.
- **Large-file pipeline** — kan vastlopen bij sets > 2u. Test daarom bij voorkeur met een set van 30–60 min.

---

## Tussenstops voor Sjuul

Stop na elke stap die visueel te checken is, geef Sjuul een **letterlijk** terminal-commando om de app te herstarten als nodig (geen markdown fences om commando's), en wacht op feedback voor je verder gaat. Volgens project-rules: "Diagnose → aanpak voorstellen → wachten op 'ja' → pas dan uitvoeren" en "Minimale impact: doe alleen wat gevraagd is".

App starten:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
./start.sh

Browser: http://127.0.0.1:5555

---

## Acceptatie-criteria sessie 1

- [ ] Waveform toont duidelijk gedetailleerde vorm, drops zijn herkenbaar als pieken
- [ ] Filmstrip en waveform-detail vallen visueel samen op tijdas (geen offset)
- [ ] Label boven timeline toont "Clip X of Y · MM:SS / HH:MM:SS in set"
- [ ] Linker trim-handle kan tot 60s voor originele clip-start gesleept worden (of tot 0 als clip dichter bij begin zit)
- [ ] Rechter trim-handle kan tot 60s na originele clip-end gesleept worden (of tot set-eind)
- [ ] Stretched zones tonen gedimd voor de Apply/Recut
- [ ] Na Apply: nieuwe clip is fysiek langer, nieuwe filmstrip + waveform worden geladen
- [ ] Split-clip, ratio-swap, stage-play-toggle werken nog
- [ ] Geen errors in browser console tijdens normaal gebruik
