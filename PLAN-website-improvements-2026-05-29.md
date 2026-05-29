# Omni DJ Website — Animation & UX Improvements Plan

> **Status:** DRAFT for Sjuul to approve. No code written yet.
> **Triggered by:** screenshot review on the live `npx serve out` build, sessie 60 vervolg.
> **Files this will touch (preview):** ~12 components + 3 content files + globals.css. No new pages.

---

## 0. Approach and order

We tackle this in five chunks, each independently shippable. After each chunk a smoketest pass in Chrome before moving on. Total estimated work: 6-8 hours dev + 1 hour review.

1. Hero polish (smaller logo + sub-line copy + beta-form copy)
2. Mega-menus (Features and Solutions hover pop-outs)
3. Audience tabs rework (add DJs, retune feature relevance per audience)
4. Features accordion shrink (one-page, single-line headline)
5. Animations rework
   - Roadmap scroll-reveal with alternating branches
   - Artist carousel slow-motion auto-scroll

---

## 1. Hero polish

### 1.1 Logo size

Currently the 8-circle mark renders at 320×320 inside a 5/12 column → ~28% of viewport width on desktop. Visually heavy, fights with the headline.

OpusClip reference (your screenshot): no logo in hero. They lean entirely on headline + "#1 AI VIDEO CLIPPING TOOL" eyebrow + drop-input. Clean, but we lose our brand mark which is core identity.

**Proposal:** keep the logo, drop to **~120px** and move it to a tighter "eyebrow + mark" cluster above the headline, left-aligned with the headline column. So the hero collapses from 2 columns to 1 column, headline-first.

```
[120px mark]  OMNI DJ  ·  BY MONO LABS
Turn your hours long DJ-sets
into 20-second viral clips.
Local analysis on your machine. Drops detected automatically. Ready to post.

[ Drop your DJ-set ............................. ]
[ Download Omni DJ                                ]
[ your@email.com to sign up for beta access  → ]

[ pillar card ]  [ pillar card ]  [ pillar card ]
```

The ring still slowly rotates (Remotion or CSS, whichever stays sharp at 120px). Entry rotation kept but tightened to 900ms.

### 1.2 Copy changes

- Sub-line: `Local-first analysis. Drops detected automatically. Ready to post.`
  → `Local analysis on your machine. Drops detected automatically. Ready to post.`
- Beta form placeholder: `your@email.com`
  → `your@email.com to sign up for beta access`
- Submit button becomes `Join beta` (replaces the plain → arrow button) so the action is unambiguous

### 1.3 Pillar card (first one)

Currently reads `Local-first. Secure. Fast.` Sjuul confirmed in screenshot — keep this card title as is. The hero sub-line is the only place that changes from "Local-first" to "Local analysis on your machine".

### 1.4 Files touched

- `lib/content/hero.ts` (copy)
- `components/hero/HomeHero.tsx` (layout collapse to 1-col)
- `components/hero/LogoReveal.tsx` (size + alignment)
- `components/hero/JoinBetaForm.tsx` (placeholder + button label)

---

## 2. Mega-menu pop-outs for Features and Solutions

Reference patterns: OpusClip dropdowns (your screenshot). Three-column grid. Title + 1-line description per item. Soft fade-in on hover. Closes on mouse-leave with 150ms delay so users can move down without losing it.

### 2.1 Features mega-menu

Three columns of feature cards. Each card has a small icon, a title, and a 1-2 line description. Items not yet shipped get a `soon` chip and 60% opacity (matches OpusClip's grey-out pattern).

**Column 1 — Analyse & cut**
- ClipDrop (currently called Analyse) — Drop detection, BPM, energy across the whole set
- Auto-cut — 30-60s windows proposed automatically
- Multi-cam (soon) — Align angles, pick the best frame per drop

**Column 2 — Brand & edit**
- Brand kits — Logo, captions, watermarks per artist or label
- Animated captions — Per-platform caption presets
- Auto-track (soon) — Keep the subject framed across crops

**Column 3 — Ship**
- Aspect-ratio rail — 9:16, 1:1, 4:5, 16:9 in one pass
- Social (soon) — TikTok, Instagram, YouTube, X direct publish
- Calendar — Drag-and-drop release rhythm
- Insights (soon) — Per-clip retention and account growth

### 2.2 Solutions mega-menu

Two columns (5 audiences, so 3 + 2 or 2 + 3). Each item: audience name + 1-line value proposition.

- DJs — Ship a month of content from one set
- Videographers — Cut a month of edits in an afternoon
- Event organisers — Recap your event before the bar closes
- Festival organisers — Aftermovie-grade shorts from every stage
- Record labels — Roster-wide brand kits and insights

Clicking goes to `/solutions#<audience>` (we anchor-scroll into a specific card on the solutions page).

### 2.3 Interaction spec

- Hover on nav-item: pop-out fades in (200ms ease-out), translateY from -4px to 0
- Hover on pop-out content: stays open
- Mouse leaves both nav-item AND pop-out: 150ms grace period then fades out (200ms ease-in)
- Keyboard: nav-item Tab focus opens pop-out, Esc closes, arrow keys navigate items
- Mobile: pop-outs replaced by expandable accordion under each top-level nav-item in the slide-down menu

### 2.4 Files touched

- `components/nav/StickyNav.tsx` (add hover state + pop-out anchor)
- `components/nav/MegaMenuFeatures.tsx` (new)
- `components/nav/MegaMenuSolutions.tsx` (new)
- `lib/content/megamenu.ts` (new — both menus' data)
- `lib/content/nav.ts` (mark which nav-items have a mega-menu)

---

## 3. Audience tabs rework

The home page Enterprise tabs currently has 4 audiences and 5 shared features. Sjuul wants:
- Add **DJs** as a 5th tab
- Verify each audience gets the features that genuinely matter to them, not a one-size-fits-all set

### 3.1 New tab order

DJs → Videographers → Talent managers → Event organisers → Record labels

### 3.2 Per-audience feature curation (5 items each, varies per audience)

**DJs**
- Drop detection (hero feature)
- Aspect-ratio rail (9:16 for TikTok/IG Reels, 1:1 for grid)
- Animated captions
- Calendar (release rhythm)
- Local-first (no cloud queue, no waiting)

**Videographers**
- Drop detection (saves scrubbing)
- Multi-cam (soon)
- Batch processing
- Brand kits per artist
- Aspect-ratio rail (all platforms in one pass)

**Talent managers**
- Multi-artist workspaces
- Brand kits per artist
- Calendar (roster-wide)
- Auto-mode (soon — set it once per artist)
- Insights (soon — which artist is pulling weight)

**Event organisers**
- Watch-folder (drop the room recording, walk away)
- Batch processing (whole night through pipeline)
- Aspect-ratio rail
- Local-first (privacy of unreleased recordings)
- Auto-mode (soon — recap shipped before closing time)

**Record labels**
- Multi-artist workspaces (roster)
- Batch processing
- Insights (soon)
- Brand kits per release
- Auto-mode (soon)

Features marked `soon` get the chip + 60% opacity, matching the mega-menu convention.

### 3.3 Headlines per tab (already in `enterprise.ts`)

Keep current headlines for the 4 existing tabs. Add DJs:
- "Ship a month of content from one set."

### 3.4 Files touched

- `lib/content/enterprise.ts` (DJs tab + per-audience feature lists)
- `components/enterprise/EnterpriseTabs.tsx` (render per-tab feature list instead of shared list)
- `app/solutions/page.tsx` (sync with same data, add DJs card)

---

## 4. Features accordion → one-page overview

Currently 6 large rows that take 6 viewports of scroll. Sjuul wants the whole section to fit in **one viewport** with the same design language, just smaller.

### 4.1 Headline on one line

Current: `Everything inside Omni DJ.` — wraps to 2 lines around 18-20 chars per line on the 6vw clamp.

Fix: reduce hero clamp to `clamp(28px, 4vw, 56px)` for this specific section (still bold, still tracking-tight). One-line at ≥1100px viewport, gracefully wraps below.

### 4.2 Compact accordion layout

Drop row height from ~96px (closed) to ~60px. Reduce open-state body padding from 40px to 20px. Screenshot side reduces from 4:3 to 3:2 to take less vertical room when open.

Allow **multiple open at once** (current is single-open). Users can scan the whole list without losing context. Open all by default the first time the section enters viewport, then close individually.

Total target height: ≤900px including section padding. Fits 1280×900 viewport with hero + footer visible above/below.

### 4.3 Files touched

- `components/features/FeaturesAccordion.tsx` (sizing + multi-open behavior)
- `app/globals.css` (one new utility class for this section's headline clamp)

---

## 5. Animation rebuilds

### 5.1 Roadmap — scroll-driven horizontal reveal with alternating branches

**Current:** static horizontal carousel, all cards visible at once, drag-scroll only.

**Target:** scroll-driven reveal where the horizontal timeline draws itself as the user scrolls down. Cards appear one by one, alternating above/below the track. Pattern: above, below, above, below…

```
Roadmap.
What's shipped. What's next. What we're building.

      ┌─NO.01─┐         ┌─NO.03─┐         ┌─NO.05─┐
      │ card  │         │ card  │         │ card  │
      └───┬───┘         └───┬───┘         └───┬───┘
          │                 │                 │
●─────────●─────────●─────────●─────────●─────────●─→
                    │                 │                 │
                ┌───┴───┐         ┌───┴───┐         ┌───┴───┐
                │ NO.02 │         │ NO.04 │         │ NO.06 │
                └───────┘         └───────┘         └───────┘
```

**Mechanism:**

The roadmap section becomes a **pinned scroll section**. While the user scrolls vertically through ~1.5x viewport, the pinned content animates: the horizontal line draws left-to-right, and each milestone dot + card fades in at the matching x-position. The first card's **left edge aligns horizontally with the left edge of "Roadmap." text** (so the headline anchors the timeline).

After the last card is revealed, the pin releases and the page continues scrolling normally.

**Implementation:**

- Use a vertical scroll-driven approach with CSS `scroll-driven animations` (modern Chrome/Safari) with GSAP ScrollTrigger fallback for Firefox
- Library: **GSAP ScrollTrigger** (already a planned dep, not yet installed) — `pin: true`, scrub: 0.5
- Total scroll distance = N cards × 250px = 3000px for 12 cards (≈ 3 viewports)
- Each card's reveal range: `(i / N, (i + 1) / N)` of total progress
- Card fade-up: opacity 0 → 1 + translateY ±20px (sign alternates by index parity)
- Track line: drawn via `stroke-dashoffset` keyframe from `length` to `0`
- Dot fill: each dot animates from outline to orange-filled when its card reveals

**Mobile fallback:** scroll-driven pinning feels wrong on touch. On <768px, fall back to vertical stack (no horizontal scroll, no pinning) — cards listed top-to-bottom with the timeline running vertically through them.

### 5.2 Artist carousel — slow continuous auto-scroll

**Current:** static cards, manual arrow scroll, scroll-snap.

**Target:** **continuous slow-motion infinite scroll** — like a runway. ~30px/second so a viewer reads it as deliberate motion, not a screen-saver.

**Mechanism:**

- Duplicate the artist list 3× in the DOM
- Wrap in a flex row, then animate `transform: translateX(-33.33%)` over **60 seconds, linear, infinite**
- On hover: animation-play-state pauses
- Manual arrow buttons still work — when pressed, they `scrollBy` and the auto-scroll resumes from the new position
- Respect `prefers-reduced-motion`: animation pauses entirely, manual scroll only

This is the same pattern as Apple's product video reels and Stripe's customer logos — feels premium because it never stops, never jerks.

### 5.3 Remotion compositions — kept as-is

The 3 Remotion MP4s (hero logo, auto-mode pipeline, tool-overview flow) already render well. We don't touch them in this round.

### 5.4 Files touched

- `components/roadmap/RoadmapCarousel.tsx` → renamed to `RoadmapScrollReveal.tsx`, mostly new
- `components/artists/ArtistCarousel.tsx` (add auto-scroll loop)
- `app/page.tsx` (rename import if RoadmapCarousel changed)
- `package.json` (add `gsap` dependency — already in plan, install now)

---

## 6. Smoketest checklist (after each chunk)

After each numbered chunk, in Chrome at `http://localhost:3000`:

1. **Console errors** — must stay clean
2. **TypeScript** — `npx tsc --noEmit` returns 0
3. **Mobile (Chrome DevTools 390px)** — layout doesn't break
4. **Keyboard nav** — Tab through nav, mega-menu opens on focus, Esc closes
5. **prefers-reduced-motion** — DevTools "Emulate CSS prefers-reduced-motion: reduce" → all loops stop, scroll-driven animations short-circuit to end state
6. **Lighthouse perf score** — should stay ≥90 on desktop home page

Final: full `npm run build` + `npx serve out` pass.

---

## 7. Out of scope this round

- Real artist videos / screenshots (still placeholder)
- Stripe / Supabase / DNS
- Backend SMTP wire-up
- Cloudflare deploy
- Hex color confirmation (still placeholder orange + creme)
- Knowledge Center URL
- Studio+ feature list

These remain on the original BUILD-LOG punch list for after the visual polish lands.

---

## 8. Approval gate

Before any code is written, please confirm:

- [ ] Hero collapses from 2-col (logo left, copy right) to 1-col (small mark + headline + CTAs) — OK?
- [ ] Mega-menu structure (3-col Features, 2-col Solutions) and item lists — OK?
- [ ] DJs added as a 5th audience tab, audience-specific feature lists — OK?
- [ ] Features accordion shrinks to one viewport, multiple open at once allowed — OK?
- [ ] Roadmap becomes pinned scroll-reveal with alternating-side cards — OK?
- [ ] Artist carousel becomes slow continuous auto-scroll — OK?
- [ ] GSAP added as a dependency for scroll-pinning — OK?
- [ ] Copy changes: hero sub-line, beta-form placeholder, beta button label — OK?
- [ ] Order of execution (Hero → Mega-menu → Audience tabs → Features accordion → Animations) — OK?

Reply with "approve" or with specific tweaks per bullet. After your sign-off I start implementing chunk 1 immediately and ship one chunk at a time with a smoketest in between.
