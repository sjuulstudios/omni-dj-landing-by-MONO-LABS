# Omni DJ Website Premium Pass — Sjuul's antwoorden op de 37 vragen

> Beslissingen vastgelegd 2026-05-29. Hoort bij `PLAN-website-premium-pass-2026-05-29.md`.
> Uitvoeringsmodus: **begin meteen alles** (niet gefaseerd A to G, alle code-fases tegelijk).
> Assets: Sjuul levert alle 7 asset-asks binnen 7 dagen, dus niets blokkeert.

## Cross-cutting fundamenten

- **Signature easing:** The Drop, `cubic-bezier(0.16, 1, 0.3, 1)`. Overal toepassen.
- **Mono-font:** Geist Mono voor cijfers, timestamps, bestandsnamen, track-IDs. Helvetica blijft voor de rest.
- **Sectie-overgangen:** alle drie. Hairline-dividers (50% creme) + zachte creme-naar-transparant gradient over eerste 80px van elke dark-sectie + hero op #0A0A0A i.p.v. puur zwart, daarna terug naar #000000.
- **Performance:** nu opruimen. framer-motion + lenis volledig uit deps, GSAP lazy-load bij roadmap-viewport. Doel ~95 kB First Load JS.
- **Geluidsdesign:** NEE. Geen audio-laag.
- **Contrast:** creme-mute ophogen van 0.6 naar 0.72 opacity (AAA, ~6.3:1).
- **Loading-state:** NU meenemen. Eerste frame van elke Remotion-MP4 als inline base64 poster pre-baken, exacte aspect-ratio reserveren voor auto-mode + tool-flow.

## Hero

- **Centerpiece:** Optie C, set-timeline strip. Dunne horizontale tijdlijn boven de headline, 3-uurs set met 3 pulserende oranje drops, hover scrubt. Wordt motief dat terugkomt in roadmap + auto-mode.
- **Eyebrow:** ongewijzigd laten ("OMNI DJ · BY MONO LABS" zoals nu).
- **Waitlist-teller:** NEE. Bij submit alleen nette success-badge zonder nummer.
- **Headline:** huidige behouden — "Turn your hours long DJ-sets into 20-second viral clips."
- Beta-form refinement (chevron-button + success-animatie) mag, alleen GEEN teller.

## Artist carousel

- **Layout:** EEN rij (geen twee-rij gelaagd). Alleen polish op de bestaande rij.
- **Hover-metadata:** artiest + view count (optie c). View-getallen voor nu STATISCH/handmatig invulbaar. Later (veel later) komt directe koppeling die de view-data live uit de post haalt en laat meegroeien. Niet nu bouwen.
- **Aantal tiles:** 8 voor de loop herhaalt.
- **Hover-audio:** video speelt on hover met audio GEMUTE, plus kleine unmute-knop boven-midden in de card/frame. Geen sectie-brede toggle.

## Audience tabs

- **Koppen:** gewone headline + body (GEEN quote-stijl).
- **Stat-ticker:** JA, maar in de card zelf onder de description (niet als losse ticker bovenaan de sectie). Cijfers aspirational tenzij Sjuul echte aanlevert — bevestigen bij asset-levering.
- **Mobiel:** scroll-x behouden.
- **See-more CTA:** JA, kleine "see more"-link per tab naar het solutions-anker.

## Tool overview

- **Scroll-driven:** JA. Van loopende Remotion-MP4 naar scroll-driven scrub. Playhead beweegt op scroll-positie, drops pulseren bij kruising, reframe-fan opent, shorts-stack vult een voor een. Grootste perceived-quality lift.
- **Connectoren:** strakke "→" markers (geen gebogen SVG-curves).
- **Echte waveform:** Sjuul levert 10-min audio-sample binnen 7 dagen, dan echte energie-curve inbakken.

## Workflow ("Three steps. Hands-off.")

- **Visuals:** BEIDE — nu diagrammatische placeholders zodat het af is, later vervangen door Sjuul's echte 1280x720 screenshots.
- **Pill-tags:** behouden (GEEN concrete zinnen met cijfers).
- **Hover-video op kolommen:** JA inbouwen. Vereist 3 korte (4-sec) screen-captures van Sjuul.

## Auto-mode

- **Bullet-sync:** JA. Elk bullet-icoon pulseert oranje in ritme met de bijbehorende stage van de loop-animatie (een heartbeat over de sectie). EXTRA: haal het "AI"-tekstje weg uit de 2e card.
- **Subline:** JA als derde geanimeerde rij die customisation-tokens op de pipeline laat stapelen.

## Features accordion

- **Aanpak:** wireframe-achtige animaties per rij (CSS/SVG), screencasts later vervangbaar. Richting goedgekeurd:
  - Analyse — waveform-lijn die zich van links naar rechts tekent, 2-3 oranje drop-markers poppen in (sluit aan op hero-timeline-motief).
  - Library — 4-koloms grid van lege 9:16 frames die staggered infaden (clips stromen binnen).
  - Brand — logo-vierkant + accent-swatch, lijn trekt van logo naar clip-frame, frame krijgt accentrand.
  - Social — drie platform-iconen (TikTok/IG/YT), clip-thumbnail schuift langs lijntje naar elk, een voor een.
  - Calendar — mini maand-grid, oranje stipjes poppen in op een paar dagen (geplande posts).
  - Insights — lijn-grafiek bouwt op van links naar rechts met oplopende curve + KPI-getal dat omhoog telt (Geist Mono).
  - Elke rij speelt af bij openen accordion, loopt subtiel door zolang open, reduced-motion stopt naar eindstaat.

## Roadmap

- **Kleurcodering:** alles oranje (GEEN drie-staten groen/oranje/creme).
- **Klikbare cards:** JA, klik-to-expand naar 480px pop-out (screenshot/loop voor shipped, concept-art voor planned).
- **Email-subscribe:** JA, aan het eind van de scroll-pin bij item NO.12 ("Get notified when these ship" + email-input).
- **Card-breedte:** 240px behouden, lange titels INKORTEN (bijv. "Beta feedback & new feature implementation").

## Closing CTA + footer

- **Parallax:** JA, subtiele oranje glow drift op scroll.
- **Copy-wijziging:** headline wordt "Stop Editing, Start posting." en description daaronder "Turn your next DJ-set into a month of content."
- **Footer-email:** vervang beide huidige adressen door **omnidj@monohq-labs.com**.
- Footer live-klok / "Made by humans in Amsterdam": niet expliciet gekozen — alleen parallax + copy. Niet bouwen tenzij Sjuul later vraagt.

## Navigation polish

- **Doorvoeren:** chevron-spring (overshoot easing) + zachtere mega-menu schaduw (multi-layer blur-stack).
- **NIET doen:** active-nav underline, smooth sticky-transitie.
- **Beta-pill in nav:** geen voorkeur uitgesproken — voorlopig WEGLATEN, makkelijk later toe te voegen.

## Asset-asks (Sjuul levert binnen 7 dagen)

1. 3 product screenshots (1280x720 PNG): Analyse / Editor / Auto-mode
2. 3 screencasts (4-6s silent loops): zelfde drie views, voor workflow-hover
3. 6 feature screencasts (6s): Analyse / Library / Brand / Social / Calendar / Insights — vervangen wireframes
4. 8-12 artist verticale clips (9:16 mp4, muted) — voor de 8-tile carousel
5. 1 audio-sample (10-min mp3 DJ-set) — voor echte tool-overview waveform
6. Exacte oranje + creme hex-codes uit de Omni DJ tool
7. Hero-headline: AL GEKOZEN (huidige behouden), geen actie nodig

## Eerder open, nu beslist (2026-05-29)

- **Stat-ticker cijfers audience-tabs:** aspirational (streefcijfers) voor nu. Later vervangen door echte data.
- **Carousel-tiles:** 8 tiles, genummerd 1 t/m 8. Statische view-getallen per tile, handmatig invulbaar tot de latere live-koppeling.
- **Lange roadmap-titels:** Sjuul akkoord dat Claude de lange titels inkort.

## UITGEVOERD — build-sessie 2026-05-29 (alles tegelijk)

Alle 17 taken code-side klaar. Build groen (18/18 static pages, exit 0). tsc 0 errors. Homepage First Load JS: 154 kB -> 117 kB (framer-motion + lenis verwijderd, GSAP lazy-loaded).

**Sign-up knop:** oranje -> creme + zwarte tekst (btn-creme class), desktop + mobiel. Log in ongemoeid.

**Nieuwe bestanden:** components/hero/SetTimeline.tsx, components/features/FeatureWireframe.tsx, lib/content/artists.ts.
**Verwijderd:** lib/motion.ts (was niet geimporteerd), deps framer-motion + @studio-freight/lenis.
**Toegevoegd:** geist@1.7.1 (Geist Mono, self-hosted woff2 in out/_next/static/media/).

### Asset-hooks klaargezet (vullen wanneer Sjuul levert)
- Workflow hover-video: `HOVER_VIDEOS` map in WorkflowGrid.tsx (paden naar /videos/workflow/*.mp4).
- Artist clips: `video` veld per artist in lib/content/artists.ts (paden naar /videos/artists/*.mp4). Zonder video toont tile de wireframe-placeholder.
- Features screencasts: vervangen FeatureWireframe per rij zodra screencasts er zijn.
- Roadmap concept-art: placeholder-box in pop-out, vervangen door screenshot/loop.
- Hex-codes: nog placeholder #FF6A1A oranje + #F5EFE3 creme in globals.css + tailwind.config.ts. 1x find-replace zodra Sjuul de echte codes uit de tool geeft.

### Twee scope-aantekeningen voor Sjuul
1. **Footer-email:** alleen het contact-blok op /contact is naar omnidj@monohq-labs.com gezet (verving support@omnidj.com + sjuul@monohq-labs.com). In lib/content/legal.ts staan nog support@omnidj.com (3x) en security@omnidj.com (1x) — bewust niet aangeraakt want dat zijn functionele juridische/security-adressen, geen footer. Zeg het als die ook moeten wijzigen.
2. **Performance:** 117 kB i.p.v. het ~95 kB streefgetal uit het plan; verschil is de extra scroll-driven logica (tool-overview, closing parallax, roadmap). Nog steeds ruim onder de oude 154 kB en onder de 120 kB premium-grens.

### Live review gedaan (2026-05-29, samen via Chrome op Sjuul's Mac)
Volledige pagina doorgelopen op localhost:3000. Alle secties live geverifieerd. Console: 0 errors na fixes. Twee bugs gevonden + gefixt tijdens review:
1. **Set-timeline drop-markers vielen niet op hun oranje cluster.** Oorzaak: `<g transform=translate>` + CSS `transform: scale()` in de pulse-animatie overschreven elkaar, marker sprong naar oorsprong. Fix: markers met vaste `cx`/`cy` op gesnapte bar-index (`DROP_BARS` + `barCenterX`), pulse animeert alleen opacity (nooit transform). Energie-spike + oranje kleur + marker delen nu exact dezelfde bar-index.
2. **Hydration-warning in SetTimeline** (`y did not match`, floating-point drift server vs client). Fix: `r3()` helper rondt alle rect-geometrie af op 3 decimalen.

## Ronde 2 — feedback-fixes (2026-05-29, samen via Chrome)

Naar aanleiding van Sjuul's review-feedback:
1. **Scroll-offset**: `.section` krijgt `scroll-margin-top: 96px`; roadmap GSAP pin start nu op `top top+=80` zodat de "Roadmap." titel niet meer onder de sticky nav valt.
2. **Features-accordion single-open**: van Set naar enkele `openIndex`. Klik op nieuwe rij vouwt vorige dicht. Lost ook de Social/Insights-overlap met de gepinde roadmap op (voorspelbare sectiehoogte).
3. **Hero CTA's**: Download solide crème (links) + Drop your DJ-set transparant met dashed oranje rand (rechts), naast elkaar. Beta-balk eronder. DropField herontworpen naar transparante knop. Subline op 1 regel (`md:whitespace-nowrap`).
4. **Animaties premium (echte Remotion-MP4's, Sjuul's keuze)**:
   - `ToolOverviewFlow.tsx` herbouwd: step-rail (Analyse/Reframe/Publish), playhead met DROP-labels die pulsen, spring-pop shorts, → arrows. ToolOverview-component terug naar RemotionMp4 (was scroll-driven).
   - `AutoModePipeline.tsx` herbouwd: AI-tekstlabel weg, processing-tile met checkmarks (Cut/Brand/Caption), spring-pop posts, minHeight 380->240 (minder dode ruimte).
   - colors.ts creme-mute gesynct naar 0.72.
5. **Witruimte auto-mode**: animatie-marge mt-14->mt-10, bullets mt-16->mt-8, aspectRatio 16/6->16/5.

**Render nog te doen op Sjuul's Mac** (sandbox kan geen Chromium downloaden):
```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/omnidj.com/remotion"
npm run render:all
```
Dit rendert tool-flow.mp4 + auto-mode.mp4 + logo-reveal.mp4 naar ../public/remotion/. Tot dan tonen de secties de CSS-fallback.

**Git**: commit `dbe8240` op branch `feature/auto-mode-and-brand-redesign` (89 files, geen node_modules/tmp/build). Niet gepusht.

**Let op — dev-server moet herstart**: na de vele snelle edits raakte de draaiende `npm run dev` in een staat waarin Tailwind-CSS niet meer laadde (kale pagina). De productie-build is groen (18/18, CSS 23KB met alle classes). Herstart `npm run dev` (Ctrl+C + opnieuw) en de styling is terug.

## Ronde 2 — live review afgerond (2026-05-29)

Alle feedback-fixes live geverifieerd via Chrome op Sjuul's Mac. MP4's gerenderd (logo-reveal 1.4MB, auto-mode 410kB, tool-flow 581kB). Bevestigd werkend:
- Roadmap-titel blijft onder de nav tijdens de pin.
- Single-open accordion.
- Premium tool-overview (step-rail + DROP-labels) + auto-mode (checkmarks, geen AI-tekst).
- Hero CTA's Download solide / Drop transparant, subline 1 regel.
- Styling terug na dev-server-herstart.

## ⏭️ VOLGENDE SESSIE — Sjuul's prioriteit (in volgorde)

1. **`git push`** van de landing-page-commit `dbe8240` (branch `feature/auto-mode-and-brand-redesign`). Eerst doen. Check of er een remote is en naar welke branch.
2. **Tool-overview + auto-mode sectie-ruimte verkleinen.** De animatie staat hoog in de sectie met te veel verticale leegte eronder voor de volgende sectie. Strakker maken (sectie-padding of animatie-positionering). Akkoord, nog niet uitgevoerd.

### Nog te doen door Sjuul (lager geprioriteerd)
- Assets leveren (zie hooks hierboven) binnen 7 dagen.
- Echte hex-codes voor find-replace.
- Eventueel: legal.ts emails (support@/security@omnidj.com) wijzigen indien gewenst.
