# Omni DJ Website — Premium Pass Proposal

> **Status:** DRAFT for Sjuul to approve. No code written yet.
> **Goal:** push the site from "well-built marketing site" to "premium product reference" — the kind of site DJs send to each other in DMs because the craft itself is the proof.
> **Reference quality targets:** Linear, Vercel, Cobrand, Rauno Freiberg's site, Loops, Cron, Granola, Cursor.

---

## 0. The honest baseline assessment

What the site already does well (keep):
- Type scale, color discipline (creme on black is rare and right for music)
- Hero is restrained, headline carries the page
- Mega-menus, audience tabs, accordion patterns are solid
- Remotion-backed hero / auto-mode / tool-overview is the right architecture
- Roadmap scroll-pin is the strongest moment on the page

What is still keeping it at "Tier-2 startup site" rather than Tier-1:
- **No proof-of-craft above the fold.** The hero ends in CTAs but the visitor never sees the product working. Opus shows a video reel within 800px of scroll. Linear shows a literal app screenshot animating.
- **Section transitions are abrupt.** Each section reads as a separate slide. There is no spatial continuity, no shared element between sections.
- **The waveform / tool-overview / auto-mode animations are illustrative, not the product.** Premium sites use the real product UI as the animation. Linear renders the real linear app. We render an abstraction.
- **No motion personality.** All easings are the same `cubic-bezier(0.22, 1, 0.36, 1)`. Premium brands have one signature motion (Apple's snap, Linear's gentle drift, Stripe's measured slide). Ours is generic.
- **No sound, no haptics, no "moment".** A DJ tool that never makes the page feel rhythmic is a missed opportunity. Subtle pulses on drop-detection, beat-locked stagger on roadmap reveal, a single bass-thump when the hero lands.
- **Type pairing is one font.** Helvetica everywhere reads serious but flat. Premium DJ brands pair display Helvetica with a mono numeric for stats / timestamps / track IDs (think Akkurat Mono, JetBrains Mono, or the numerals from Inter Display Mono).
- **No dark-light contrast play.** The site is dark, then creme, then dark, then creme. Linear and Loops use *layered darks* (#000 → #0A0A0A → #141414 with subtle gradients between sections) to give depth without flipping palettes.
- **CTAs read as buttons, not commitments.** "Drop your DJ-set" should *feel* like a decision the moment your cursor enters the dashed border. Magnetic hover, micro-tilt on drag-over, file-name animation on drop.

This proposal addresses each.

---

## 1. Section-by-section deep dive

Each section has: current state → specific upgrade → questions for you to answer before I implement.

### 1.1 Hero

**Current state.** Centered mark + wordmark eyebrow → headline → subline → drop field + download + beta email.

**Tier-1 upgrade options.**
- **Option A: Quiet hero with embedded waveform.** Below the headline, replace the static drop-field with a 480-wide animated waveform that runs continuously (synthesized, not real audio). When you hover the headline or drop-field, the waveform "responds" — orange highlights cascade across the bars in sync with a slow 100 BPM. Adds proof-of-craft instantly.
- **Option B: Hero with cinematic product video on the right.** Drop the central layout, go 60/40 left-right. Left: headline + CTAs. Right: a 16:9 video frame autoplay-looping a screen recording of you opening Omni DJ, dropping a set, and seeing drops detected (5 seconds, no audio, loops). This is the Linear/Loops pattern.
- **Option C: Stay centered but add the "set timeline" strip.** Above the headline, render a thin horizontal timeline (10vw tall) showing a synthesized 3-hour set with three orange "drops" pulsing at fixed positions. Hovering the strip scrubs through. The drops sync with a 100ms haptic-style scale-pulse animation. Sets the tonal vocabulary immediately.

**My recommendation: Option C.** Cheap to ship, distinctive, doesn't require real product video assets (which you don't have yet), and the strip becomes a motif that returns later (it can BE the roadmap timeline, the auto-mode pipeline indicator, etc.).

**Beta form refinement.** Current pill works but the placeholder text "your@email.com to sign up for beta access" reads as a single long sentence and the button label "Join beta" feels weak compared to the orange CTA above it. Proposal:
- Placeholder: `Drop your email for beta access`
- Button: replace text with a single chevron arrow, button stays creme-on-orange
- On submit, the row animates: input slides 100% off to the left, success badge slides in from the right ("You are #247 on the waitlist")

**Questions for you:**
1. Option A, B, or C for the hero centerpiece? (If A or C, no asset work needed. If B, you need a 5s screen recording of Omni DJ in use — I can use placeholder until you record it.)
2. Drop the "OMNI DJ · BY MONO LABS" eyebrow entirely, or keep it? (My take: keep, but shrink to 10px / 0.18em tracking and place above the mark, not beside it.)
3. Show a real or fake "247 on waitlist" counter on the beta submit? Real-ish (faked from a static seed + a small daily increment, no backend) is fine for marketing-trust, but it's a tiny lie. Your call.
4. Headline final choice — current is "Turn your hours long DJ-sets into 20-second viral clips." Of the 8 alternatives in PLAN-website.md sec 3.2, do you want me to keep current or swap?
5. Add a thin scroll-cue at the bottom of the hero (animated arrow + "scroll" microcopy)? Premium sites have stopped doing this; modern users scroll instinctively. But if you target older DJs / festival organisers it might still help.

### 1.2 Artist carousel

**Current state.** 16 placeholder tiles, continuous slow auto-scroll, hover pauses. Functional but visually empty.

**Tier-1 upgrade options.**
- **Layered velocity:** instead of one row, render TWO rows scrolling in opposite directions at different speeds (top row left-to-right 60s, bottom row right-to-left 90s). Gives the impression of a *crowd* of clips, not a list. The Apple AirPods page uses this.
- **Per-tile metadata overlay on hover:** when you hover a tile, the tile expands slightly (1.03 scale, 200ms ease-out), the artist name + venue + a "47K views" stat fade in over the bottom 30% of the tile.
- **Edge fade is currently 6%.** Push to 12% so the seam feels softer.

**Questions for you:**
1. One row or two-row layered scroll?
2. What metadata do you want on hover? Options: (a) artist + handle, (b) artist + venue/festival, (c) artist + view count, (d) all three.
3. Real artist count target: 8 / 12 / 16 / 24 tiles before we start duplicating? More tiles = longer loop = feels more "deep roster" but costs more video assets.
4. Audio on hover? A 2-second 30dB preview of the clip would be unforgettable. But it requires real video files with audio tracks and might annoy people. Toggleable in the section header? ("Tap to enable preview audio")

### 1.3 Enterprise / audience tabs (Built for the teams behind the music)

**Current state.** Creme section, 5 tabs, each with 5 features. Clean but the tabs feel like an org chart.

**Tier-1 upgrade options.**
- **Replace the static 3-card grid per tab with a stacked-card animation.** When you click a tab, the new tab's 5 feature cards stagger-fade in from below (80ms per card, 24px translateY each). Currently it's a key-based remount with animation; tighten the easing and the stagger feels intentional.
- **Add a stat ticker per tab.** "Used by 47 artist teams. 2.1M clips shipped." Sets the social proof. Real or aspirational, your call.
- **Bigger left-column treatment.** Replace plain headline + body with a quote-style block. For DJs tab: "Three sets in. Sixty clips out. One Sunday afternoon." attributed to a DJ name. Each tab gets a different quote.

**Questions for you:**
1. Quote-style headlines per tab? If yes, I need 5 quotes (or I draft them, you approve).
2. Add the stat ticker? Real or aspirational?
3. The tabs are currently in scroll-x on mobile. Keep that, or collapse to a dropdown select on mobile?
4. Should each tab also link to its dedicated solutions page anchor (already wired, but no visible "see more" CTA in-card)?

### 1.4 Tool overview ("From three-hour set to scroll-stopping shorts")

**Current state.** Three cards (waveform / reframe / shorts) connected by SVG curves. Animated as one Remotion MP4.

**Tier-1 upgrade options.**
- **Make it scroll-driven, not loop.** As you scroll into the section, the playhead in the waveform actually moves left-to-right driven by scroll position. The orange drops pulse when the playhead crosses them. The reframe-fan animates open. The shorts stack populates one by one. This is what Apple's iPhone page does with the spatial-photo demo. It is the single highest-impact change in this whole plan.
- **Real waveform from a real set.** I can analyse a ~10-min audio sample (you provide a wav/mp3 of any open-source DJ set) and bake the actual energy curve into the SVG. Removes the "fake" feel.

**Questions for you:**
1. Scroll-driven instead of looping Remotion MP4? (My take: yes, this changes the whole feel.)
2. Provide a 10-min real DJ-set sample so the waveform is authentic? (Even a slice of one of your own sets is fine; I synthesise the rest if shorter.)
3. Keep the connector SVG curves between cards or drop them in favour of inline "→" markers? Curves are softer; markers are more product-spec.

### 1.5 Workflow ("Three steps. Hands-off.")

**Current state.** Three columns (Analyse / Edit / Auto-schedule) with placeholder screenshots and pill tags.

**Tier-1 upgrade options.**
- **Make the screenshots real.** This is the biggest blocker. Until you screenshot the actual Omni DJ app, the section reads as "coming soon." Placeholder grey blocks hurt premium feel more than any animation.
- **Add a video frame on hover for each column.** When you hover the Analyse column, the screenshot crossfades into a 4-second loop of the analyse view in action (small, no audio).
- **Numbered steps could be sequenced.** Currently all three appear at once. Stagger them: step 1 appears at scroll-in, step 2 80ms later, step 3 160ms later, with the orange "1 / 2 / 3" badges scaling in from 0.

**Questions for you:**
1. Can you provide the 3 screenshots (Analyse / Editor / Auto-mode) in 1280×720 PNG within this week? If yes, I bake them in.
2. Hover-video toggle on each column? Requires you to record three 4-second screen captures.
3. Pill tags ("Drop detection", "Energy mapping", "Auto-cut") read as feature lists. Replace with sentences like "Marks 47 drops in this 2h 14m set."? More concrete, more dramatic, but I'd need representative numbers per step.

### 1.6 Auto-mode

**Current state.** Creme section, Remotion-rendered looping pipeline animation (file → AI → 3 posts), 4 bullets below.

**Tier-1 upgrade options.**
- **The animation is already strong.** The improvement here is making the bullets *do* something. Currently they sit static below the animation. Proposal: each bullet's icon pulses orange in time with the corresponding stage of the looping animation above. So when the "AI" tile pulses in the animation, the "Fully automatic workflow" bullet's icon pulses too. Creates a single visual heartbeat across the whole section.
- **Move the section between the workflow and features sections.** Currently it's after Auto-mode → before Features accordion. The flow reads better as: Tool overview → Workflow → Auto-mode → Features → Roadmap. Already correct.

**Questions for you:**
1. Sync the bullet icons with the animation heartbeat? (Yes/no.)
2. The subline "Add customisation with brand presets, caption presets and auto-tracking." is currently a flat line. Want it as a third smaller animated row showing the customisation tokens stacking on top of the pipeline? (Premium pattern, more dev time.)

### 1.7 Features accordion

**Current state.** 6 rows (Analyse / Library / Brand / Social / Calendar / Insights), multi-open, compact.

**Tier-1 upgrade options.**
- **Replace the right-column placeholder boxes with looping micro-screencasts.** Each row, when opened, shows a 6-second silent loop of the actual feature in use. Linear does this on their features page. It's the single highest perceived-quality lift per dev hour.
- **Add a hover-preview on the row title.** Before you even click to open, hovering the row title shows a tooltip-style preview thumbnail to the right. Gives a peek without committing.

**Questions for you:**
1. Six 6-second screencasts of each feature. Can you record them in one afternoon? If yes, the section becomes the centerpiece of the page.
2. Replace "Screenshot — [feature name]" placeholders with diagrammatic icons instead, if screencasts aren't feasible yet?

### 1.8 Roadmap

**Current state.** Pinned scroll-driven horizontal reveal, 12 milestones alternating above/below the line. This is the strongest moment on the page.

**Tier-1 upgrade options.**
- **Status colour-coding.** Currently all dots fill orange. Use three states: green (shipped), orange (in progress), creme-outline (planned). The first dot (Beta feedback) is the only one currently "shipping," so the orange-fill-as-progress story breaks. Make it: NO.01 green ✓, NO.02 orange-pulse, NO.03-12 creme-outline.
- **Card sub-line for shipped items.** "Shipped Apr 2026" appears under the title on green-status cards, in 10px creme-mute.
- **Click-to-expand cards.** When you click a roadmap card, it expands to a 480-wide pop-out with a screenshot or 3-second loop showing what shipped (for green items) or what's coming (for orange/planned items as concept art).
- **Add a "subscribe to roadmap updates" CTA at the end.** When the scroll-pin releases at NO.12, the last card has a small "Get notified when these ship" button that drops into an email input.

**Questions for you:**
1. Three-state colour-coding (green / orange / creme-outline)? Need you to tell me which items are actually shipped / in progress / planned.
2. Click-to-expand card detail? (Adds dev time but huge for "this is a real product roadmap" credibility.)
3. Email subscribe at the end of the roadmap?
4. The card width is 240px. Some titles overflow ("Beta feedback & new feature implementation"). Widen to 280px or tighten the copy?

### 1.9 Closing CTA + Footer

**Current state.** Creme section "Stop editing. Start releasing." with two CTAs, then standard footer.

**Tier-1 upgrade options.**
- **Replace the static closing CTA with a parallax block.** As you scroll through the closing section, the background subtly shifts (a faint blurred orange glow drifts left-to-right at -10% scroll speed). Cobrand and Linear use this.
- **Footer micro-detail.** Add the current weather / time in Amsterdam to the footer (small, creme-mute, like "07:42 CET · Amsterdam"). A signature of where the company actually is, the kind of detail that says "real humans." Optional, removable later.
- **"Made by humans in Amsterdam" line above the copyright row.** Plus the same Omni Mark, slowly rotating, very small.

**Questions for you:**
1. Parallax background drift in closing CTA?
2. Live local time in footer? (Static "Amsterdam" is fine too if a live clock feels gimmicky.)
3. The current `support@omnidj.com` and `sjuul@monohq-labs.com` emails — keep both in contact footer? Or consolidate?

### 1.10 Navigation polish

**Current state.** Mega-menus work but the open/close feels fast and the borders feel hard.

**Tier-1 upgrade options.**
- **Soften the mega-menu shadow.** Currently `shadow-2xl`. Switch to a custom multi-layer shadow: a soft 24px / 32px / 64px blur stack at 8% / 4% / 2% opacity. Reads more crafted.
- **Animate the chevron rotation in sync with the menu reveal.** Currently chevron rotates 180° on hover with no spring. Add a slight overshoot (0.34, 1.56, 0.64, 1 easing) so it has a personality.
- **Underline the active nav item.** Currently no visual indicator when you're on `/pricing`. Add a 1px creme underline that animates in with `scaleX`.
- **Sticky nav transition.** Currently it gets a blur + border at scrollY > 80. Smoother: gradient mask from solid-black to blur over a 40px scroll range, not a hard threshold.

**Questions for you:**
1. All four of these tweaks (shadow / chevron spring / active-nav underline / smooth-sticky-transition) — yes to all, or which to skip?
2. Add a "Beta" pill next to the Omni DJ wordmark in the nav while we're pre-launch? Subtle creme-on-creme-line, fades after launch.

---

## 2. Cross-cutting upgrades

### 2.1 Typography pairing

**Add a monospaced numeric font** for stats, timestamps, version numbers, file names, track IDs. Premium options:
- **Geist Mono** (free, Vercel, premium feel)
- **Berkeley Mono** (paid, $75 personal license, the "Linear" choice)
- **JetBrains Mono** (free, slightly more tech-leaning)
- **System mono fallback** (SF Mono on Mac, Consolas on Windows — free, no extra request)

**My recommendation: Geist Mono.** Free, loads small, pairs perfectly with Helvetica.

**Where it lands:**
- All timestamps and dates (footer time, roadmap "Shipped Apr 2026")
- All numerals in stats (BPM displays, file sizes, view counts)
- File names ("live_set_amsterdam_2024.wav")
- Pricing numbers (the €75 / €200 stays Helvetica for hero impact, but unit labels like "/ month" go mono)

**Question:** Geist Mono OK?

### 2.2 Motion language

**Define ONE signature easing** and apply it everywhere. Current state mixes `0.22, 1, 0.36, 1` (smooth out) and Tailwind defaults.

**Three candidate signatures:**
- **The Glide** (Linear-style): `cubic-bezier(0.32, 0.72, 0, 1)` — slow start, gentle slide, instant stop. Reads thoughtful.
- **The Drop** (Apple-style): `cubic-bezier(0.16, 1, 0.3, 1)` — fast acceleration, hard decel. Reads decisive. *Most appropriate for a DJ tool.*
- **The Pulse** (custom): `cubic-bezier(0.34, 1.56, 0.64, 1)` — overshoot at the end. Reads playful. Risk: too cute for enterprise audiences.

**My recommendation: The Drop.** Decisive easing matches "drop detection" as the core verb of the product.

**Question:** The Drop, The Glide, or The Pulse?

### 2.3 Section transitions

Currently sections sit hard-edge against each other. Premium sites use subtle bridges:
- **Hairline divider with 50% creme-line opacity** instead of hard edge
- **Soft 1% creme-to-transparent gradient** over the first 80px of each dark section (makes the section "fade up from below")
- **Background lighten on hero only.** Currently `#000000`. Lift to `#0A0A0A` (ink-900) for the hero specifically so the dropped CTAs feel "above" rather than "on" the page. Then back to `#000000` for subsequent sections.

**Question:** Apply all three section-transition refinements, or pick subset?

### 2.4 Sound design (optional)

A tiny, tasteful audio layer:
- **One muted "click" sound** (10ms, low-freq) when the hero CTAs are clicked
- **One subtle "thump" sound** (50ms, 60Hz) when a drop is detected in the scroll-driven tool overview (only fires if user has scrolled past a "Enable sound" prompt — opt-in)
- **No music, ever.** Sound is the verb of the product but it can't autoplay.

**Question:** Sound design at all (yes/no)? If yes, opt-in or default-off-with-prompt?

### 2.5 Loading state

When the page first paints, the Remotion MP4s may flash white before they kick in. Currently the wrapper uses opacity-transition. Tighten:
- Pre-bake the first frame of each MP4 as an inline base64 poster image
- Reserve the exact aspect-ratio before video metadata loads (already done for logo, missing for auto-mode + tool-flow on slow connections)

**Question:** Worth the 30 min to nail? My take: yes, but ship the rest first.

### 2.6 Accessibility (already at AA, push to AAA on color)

Current state: WCAG 2.1 AA on all text. The creme-mute (`rgba(245,239,227,0.6)`) on black is **4.5:1 contrast ratio** — passes AA but fails AAA. For body text targeting older festival organisers this matters.

**Question:** Bump creme-mute to `0.72` (lifts to ~6.3:1, AAA on small text)? Slightly reduces hierarchy but improves readability.

### 2.7 Performance budget

Current home page = 154 kB First Load JS. Premium sites target <120 kB. Where we can cut:
- **GSAP is ~50 kB.** Only used by Roadmap. Lazy-load it only when the roadmap section enters viewport (intersection-observer-triggered dynamic import).
- **Drop `framer-motion` from deps entirely.** Not used anywhere; Reveal uses raw IntersectionObserver.
- **Drop `@studio-freight/lenis`** from deps. Not used.

This gets us to ~95 kB First Load. Premium territory.

**Question:** Do the dep cleanup now (1 hour work)?

---

## 3. Specific layout improvements per section

### 3.1 Hero — column width and rhythm
- Max-width of hero copy column is currently 760px. Tighten to 640px so the headline reaches a stronger 2-line break point on desktop.
- Vertical rhythm between eyebrow / headline / subline / CTAs is currently 32/24/40. Tighten to 24/20/32 for denser hierarchy.

### 3.2 Pricing — make the most-popular tier earn it
- Currently the orange "Most popular" pill sits on the Pro card. Visually it gets lost.
- Lift the Pro card 8px above the other 3 cards with a soft drop-shadow (24px/8% black). Read like a recommendation, not a label.
- Add a 1px orange ring around the Pro card with a slow 4s breathing pulse (opacity 0.4 → 0.6 → 0.4).

### 3.3 Contact — make the form not feel like an enterprise lead-cap
- The form currently has 5 fields. Most premium contact forms are 3 fields max.
- Proposal: collapse to (1) email, (2) "what are you working on?" textarea. Show name/role only after they start typing the message.
- Replace "Send message" with "Send →" (button shrinks to icon-arrow).

### 3.4 Collective — replace card grid with a horizontal scroll runway
- Same pattern as the home artist carousel. Reuses the runway component, less code, more consistent feel.

---

## 4. Asset asks (the bottleneck)

Things only you can produce that block the premium tier:
1. **3 product screenshots** (1280×720 PNG): Analyse view, Editor view, Auto-mode view
2. **3 short screencasts** (4-6s silent loops): same three views, recorded with QuickTime or Cleanshot at 30fps
3. **6 feature screencasts** (6s each): Analyse, Library, Brand, Social, Calendar, Insights — for the features accordion
4. **8-12 real artist vertical clips** (9:16 mp4, 6-12s, muted): for the artist carousel
5. **One audio sample** (10-min mp3 of any DJ set, ideally yours): so the tool-overview waveform is real
6. **Exact orange + creme hex codes** from the Omni DJ tool (currently placeholders)
7. **Hero headline final pick** out of the 8 in PLAN-website.md

**Without these, premium tier is capped.** With them, the site becomes a showpiece.

---

## 5. Order of execution (proposed)

I'd ship in this order, each phase independently shippable:

**Phase A — Motion + type personality (no asset asks)**
1. Pick + apply signature easing (The Drop)
2. Add Geist Mono for stats / timestamps / file names
3. Section transitions (hairlines + gradient + ink-900 hero bg)
4. Nav polish (shadow / chevron spring / active underline / smooth sticky)
5. Pricing tier elevation + breathing ring
6. Contact form collapse
7. Performance: drop framer-motion + lenis, lazy-load GSAP

**Phase B — Hero centerpiece (your asset call: A/B/C)**
8. Whichever hero option you pick
9. Beta form refinement (chevron button, waitlist counter, success animation)

**Phase C — Roadmap polish**
10. Three-state colour-coding
11. Click-to-expand cards with concept art
12. Email subscribe at end of pin

**Phase D — Tool overview scroll-drive** (the single biggest perceived-quality lift)
13. Convert from Remotion loop to scroll-driven scrub
14. Bake real waveform (needs your audio sample)

**Phase E — Features accordion screencasts** (needs your assets)
15. Replace placeholders with 6 real 6-sec loops

**Phase F — Artist carousel polish**
16. Two-row layered scroll
17. Hover metadata overlay
18. Real artist clips (needs your assets)

**Phase G — Audio + accessibility + final pass**
19. Optional sound design opt-in
20. Bump creme-mute to AAA
21. Footer details + parallax closing CTA

Phases A, C are pure code. B, D, E, F need assets. G is polish.

---

## 6. Smoketest protocol (after each phase)

1. **TS clean:** `npx tsc --noEmit` returns 0
2. **Dev:** `npm run dev`, full page Chrome MCP screenshot + console-error check
3. **Mobile:** Chrome DevTools 390px viewport, all sections render
4. **Reduced-motion:** DevTools → Rendering → Emulate `prefers-reduced-motion: reduce` — all loops stop, scroll-driven animations short-circuit to end state
5. **Keyboard nav:** Tab through entire home page, mega-menus open on focus, Esc closes
6. **Lighthouse:** desktop home page should stay ≥92 perf, ≥95 accessibility, ≥95 best practices, ≥95 SEO
7. **Production:** `npm run build` succeeds, `npx serve out` renders cleanly

---

## 7. Approval gate

Before any code is written, please answer the questions below. You can answer in any format (numbered list, screenshot annotations, voice note transcribed). I will turn your answers into a concrete tasklist.

### Section questions (compact list)
1. Hero centerpiece: A (live waveform), B (product video), or C (set-timeline strip)?
2. Eyebrow above mark, or shrink + keep where it is?
3. Real-ish waitlist counter on beta submit?
4. Headline final choice (keep current or swap)?
5. Artist carousel: one row or two-row layered?
6. Artist hover metadata: a/b/c/d?
7. Artist count target: 8 / 12 / 16 / 24?
8. Audio-on-hover preview for artist tiles?
9. Quote-style audience tab headlines (yes + I draft them, or no)?
10. Stat ticker per audience tab (real or aspirational)?
11. Mobile tabs: scroll-x or dropdown?
12. Tool overview: scroll-driven instead of looping MP4?
13. Real DJ-set audio sample for waveform?
14. Tool overview connectors: curves or → markers?
15. Workflow section: provide 3 screenshots this week, yes/no?
16. Workflow hover-video on columns?
17. Workflow pill tags as sentences with numbers?
18. Auto-mode bullet icons sync with animation heartbeat?
19. Auto-mode subline as third animated row?
20. Features: provide 6 screencasts, yes/no?
21. Features placeholder fallback: diagrammatic icons or stay placeholder?
22. Roadmap three-state colour-coding (need your shipped/in-progress/planned list)?
23. Roadmap click-to-expand cards?
24. Roadmap email subscribe at end of pin?
25. Roadmap card width: keep 240 or 280?
26. Closing CTA parallax background?
27. Footer live local time?
28. Footer emails: keep both or consolidate?

### Cross-cutting questions
29. Geist Mono for numerals / timestamps / file names: OK?
30. Signature easing: The Drop, The Glide, or The Pulse?
31. Section transitions: all three (hairlines + gradient + ink-900 hero), or pick?
32. Sound design: yes opt-in, yes default-off-with-prompt, or no?
33. Loading state polish: now or after the rest?
34. AAA creme-mute bump: yes/no?
35. Dep cleanup (drop framer-motion + lenis + lazy-load GSAP): yes/no?

### Asset commitments
36. Can you deliver the 6 asset asks within 7 days? Which ones blocking?

### Phase order
37. Proposed phase order A → G OK, or reshuffle?

---

## 8. Out of scope this round

- Stripe / Supabase / backend
- Cloudflare DNS / deploy
- Real artist video files (your asset call)
- Real product screencasts (your asset call)
- Studio+ feature list (still open from original plan)
- Knowledge Center destination URL

These remain on the original BUILD-LOG punch list.

---

Reply with answers to the 37 questions (or a subset — I can start Phase A immediately even without answers to asset-dependent ones). I will turn your answers into a concrete tasklist and start shipping.
