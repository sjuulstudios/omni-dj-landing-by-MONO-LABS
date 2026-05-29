# Omni DJ Website — Implementation Plan

Status: DRAFT for Sjuul to approve before any code is written.
Location: `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/omnidj.com/`
Stack: Next.js 14 (App Router, static export) + Tailwind CSS + Framer Motion + GSAP for advanced scroll/SVG + Lenis for smooth scrolling. Flask backend for forms.
Hosting: Cloudflare Pages (static frontend) + Cloudflare Workers or external host for Flask backend. Domain omnidj.com owned via TransIP, DNS via Cloudflare.

## 1. Visual system

### Colors
- Background primary: `#000000` (true black from the tool)
- Background secondary: `#0A0A0A` (card surface, very slight lift from primary)
- Creme primary: `#F5EFE3` (warm off-white, text on dark, light section background) — TO BE CONFIRMED with exact hex from the Omni DJ tool
- Creme secondary: `#E8DFC9` (muted creme, dividers, secondary text)
- Orange accent: TBD — Sjuul to provide exact hex from the tool. Placeholder `#FF6A1A`. Used for CTAs, key highlights, active states only.
- Orange muted (hover): TBD — derived from confirmed orange
- Text on dark: `#F5EFE3`
- Text secondary on dark: rgba(245,239,227,0.6)
- Text on light: `#0A0A0A`

No glow effects. No gradients except very subtle (~3% opacity) creme-to-transparent washes on section transitions.

### Typography
System Helvetica Neue stack:
```
font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
```
Weights used:
- Bold (700): hero headlines, section headlines
- Medium (500): subheadings, button labels, nav
- Light (300): body, large block quotes
- Regular (400): fallback if Light unavailable

Type scale (desktop):
- Hero headline: 88px / 1.0 / Bold / -0.03em tracking
- Section headline: 64px / 1.05 / Bold / -0.025em
- H3: 32px / 1.2 / Medium
- Body large: 20px / 1.5 / Light
- Body: 17px / 1.55 / Light
- Caption / mono substitute: 12px / 1.4 / Medium / uppercase / 0.08em tracking

Mobile scales proportionally (hero 52px, section 40px).

### Motion
- Library: Framer Motion + GSAP ScrollTrigger + Lenis for smooth scroll
- Easing default: `cubic-bezier(0.22, 1, 0.36, 1)` (smooth out)
- Element entry: 24px translateY + 0 to 1 opacity, 700ms duration, staggered 80ms per item
- Parallax depth: 3 layers (background -10%, mid 0%, foreground +5%) on hero and feature sections
- Connector SVG draws: stroke-dashoffset animation, 1200ms, eased
- Hover states: 200ms ease-out on all interactive elements
- No glow, no bloom, no neon. Everything is geometric and clean.

## 2. Page structure

### Routes
- `/` Home
- `/features` Features overview
- `/solutions` Solutions (4 audience landing pages)
- `/resources` Resources hub (links to knowledge center)
- `/pricing` Pricing
- `/for-business` Enterprise page
- `/contact` Contact + role-routed form
- `/collective` Artist showcase (linked from footer)
- `/legal/terms` `/legal/privacy` `/legal/trust`

### File structure
```
omnidj.com/
├── package.json
├── next.config.mjs
├── tailwind.config.ts
├── tsconfig.json
├── public/
│   ├── fonts/                  (if we later add custom .woff2)
│   ├── logo/
│   │   ├── omni-dj-mark.svg    (the circle logo, animated)
│   │   └── omni-dj-wordmark.svg
│   ├── videos/                 (vertical artist clips placeholders)
│   ├── images/                 (screenshots, OG image, etc.)
│   └── favicon.ico
├── app/
│   ├── layout.tsx              (nav + footer wrappers, fonts)
│   ├── page.tsx                (home)
│   ├── pricing/page.tsx
│   ├── contact/page.tsx
│   ├── collective/page.tsx
│   ├── for-business/page.tsx
│   ├── features/page.tsx
│   ├── solutions/page.tsx
│   ├── resources/page.tsx
│   ├── legal/[slug]/page.tsx
│   └── globals.css
├── components/
│   ├── nav/StickyNav.tsx
│   ├── nav/LogoReveal.tsx           (hero logo animation, looping circle)
│   ├── hero/HeroSection.tsx
│   ├── hero/DropField.tsx           (Drop your DJ-set field)
│   ├── hero/DownloadButton.tsx
│   ├── hero/JoinBetaForm.tsx
│   ├── hero/PillarCards.tsx
│   ├── enterprise/EnterpriseTabs.tsx
│   ├── overview/ToolOverview.tsx    (waveform + reframe connector SVG)
│   ├── overview/WaveformNode.tsx
│   ├── overview/ReframeFan.tsx
│   ├── workflow/WorkflowGrid.tsx    (3 columns: Analyse / Edit / Auto-schedule)
│   ├── automode/AutoModeAnimation.tsx (big looping in-out animation)
│   ├── features/FeaturesAccordion.tsx
│   ├── roadmap/RoadmapCarousel.tsx
│   ├── artists/ArtistCarousel.tsx   (horizontal 9:16 vertical video bar)
│   ├── pricing/PricingCards.tsx
│   ├── pricing/PricingMatrix.tsx
│   ├── pricing/BillingToggle.tsx
│   ├── contact/ContactForm.tsx
│   ├── footer/Footer.tsx
│   └── ui/                          (Button, Tag, Section, etc.)
├── lib/
│   ├── motion.ts                    (shared variants)
│   └── content/                     (all copy + roadmap + pricing data in TS)
│       ├── nav.ts
│       ├── hero.ts
│       ├── enterprise.ts
│       ├── workflow.ts
│       ├── automode.ts
│       ├── features.ts
│       ├── roadmap.ts
│       ├── pricing.ts
│       └── footer.ts
└── backend/                         (Flask, separate venv)
    ├── app.py
    ├── routes/
    │   ├── contact.py               (POST /api/contact, role-routed)
    │   └── beta.py                  (POST /api/beta-signup)
    ├── requirements.txt
    └── .env.example                 (SMTP credentials, never committed)
```

Flask backend runs on port 5556 (5555 is taken by Clip Live). Next.js dev server on 3000.

## 3. Section-by-section spec

### 3.1 Sticky nav
- Black background, 72px tall, becomes 88% opacity blur on scroll past 100px
- Left: animated Omni DJ logo (small version of hero reveal) + "Omni DJ" wordmark + tiny creme text "by MONO LABS" beside it in 11px Medium uppercase
- Center: Features / Solutions / Resources / Pricing / For business
- Right: "Log in" (creme text link) + "Sign up" (orange button)
- Mobile: hamburger that slides full-screen menu

### 3.2 Hero
- Full viewport height, black background
- Left side (50%): logo reveal animation
  - Omni DJ logo is an 8-circle ring (eight white circles arranged evenly around a central void). Reference: white-on-black PNG provided by Sjuul.
  - Vector SVG version will be authored from the PNG reference. Two variants stored in `/public/logo/`:
    - `omni-dj-mark-white.svg` (white circles, transparent background, for dark sections)
    - `omni-dj-mark-black.svg` (black circles, transparent background, for light sections)
  - On page load: "Omni DJ" wordmark slides in from the right (700ms, eased), simultaneously the 8-circle mark fades in from the left and the whole ring rotates 360 degrees once around its center
  - After load: the ring loops a slow 360-degree rotation every 10 seconds, eased linearly. Each individual circle keeps its orientation (no spinning circles, just the whole formation rotates).
  - "by MONO LABS" displayed only in the nav (not in hero per latest decision)
- Right side (50%): copy + interactions
  - Headline (current final): "Turn your hours long DJ-sets into 20-second viral clips."
  - Headline alternatives to consider before launch:
    1. "Three-hour set in. Thirty-second clip out." (rhythm, contrast)
    2. "Your set deserves more than one play." (emotional, reframes the value)
    3. "Find every drop. Clip it. Post it." (action-led, three beats)
    4. "From decks to feed in one drop." (DJ-native vocabulary)
    5. "Every drop, automatically clipped." (shortest, most direct)
    6. "The clipping studio that lives on your machine." (positioning-led, local-first hook)
    7. "Stop scrubbing. Start posting." (problem/solution)
    8. "One set. A month of content." (ROI framing)
  - Sub-line: "Local-first analysis. Drops detected automatically. Ready to post."
  - Three CTAs stacked:
    1. "Drop your DJ-set" field (orange dashed border, file-drop affordance, accepts .wav/.mp3/.mp4 and shows filename on hover)
    2. "Download Omni DJ" button (creme background, black text, downloads .dmg/.exe based on UA detection)
    3. "Join the beta" inline email field + arrow submit button (creme outline, sends to /api/beta-signup)
- Below, 3 pillar cards in a row:
  1. Local-first. Secure. Fast.
  2. Works offline. Your set never leaves your machine.
  3. Clip from anywhere. Mac, Windows. No cloud, no wait.

### 3.3 Artist carousel
- Black background section, headline: "Built for the artists shaping nightlife."
- Horizontal scrolling bar of vertical 9:16 video frames (8 visible at once, scrolls infinitely)
- Each frame: vertical video placeholder, autoplay muted loop, 200px wide x ~355px tall, rounded 16px
- Top-left of each frame: small social icon badge (Instagram or TikTok) in 24x24 circle
- No name labels, no day counts (clean, per your spec)
- Hover: video subtly scales 1.02, social icon brightens

### 3.4 Enterprise tabs
- Creme section (background `#F5EFE3`, black text)
- Headline: "Built for the teams behind the music."
- Sub: "Whatever your role, Omni DJ scales with you."
- Tab bar (sticky on scroll within section): Videographers | Talent managers | Event organisers | Record labels
- Active tab shows orange underline animation
- Each tab content:
  - Need-driven headline (e.g. Videographers > "Cut a month of edits in an afternoon.")
  - 5 shared feature cards in a 2+3 grid:
    1. Workspaces per artist
    2. Auto-mode
    3. Watch-folder
    4. Batch processing
    5. Multi-artist
- Each card has a small icon (creme line art), title, 2-line description
- Tab switch: cards fade out 200ms then new cards stagger in 80ms per card

### 3.5 Tool overview (Weave-style flow)
- Back to black background
- Headline: "From three-hour set to scroll-stopping shorts."
- Full-bleed flow diagram with connector SVG:
  - Node 1 (left): "Your set" — animated waveform inside a rounded card, scrubber moves left-to-right showing 3:00:00 timestamp, filename label "live_set_amsterdam_2024.wav"
  - Curved orange-to-creme connector line draws to Node 2 on scroll
  - Node 2 (center): "Reframe options" — single 16:9 source frame with three connector lines fanning to 9:16, 1:1, 4:5 thumbnails (each a video placeholder you fill later)
  - Curved connector draws to Node 3
  - Node 3 (right): "Shorts ready" — small stack of three vertical clips with social platform icons
- Connector lines: 1.5px stroke, creme color with orange highlight on the active flow direction
- ScrollTrigger draws each segment as the section enters viewport

### 3.6 Workflow section (3 columns)
- Black background, headline: "Three steps. Hands-off."
- 3 columns horizontally, each gets:
  - Top: 16:9 screenshot/video placeholder of the matching tool screen
  - Title: Analyse / Edit / Auto-schedule
  - Description (2-3 sentences each)
  - Below each: 3 small feature pills
    - Analyse: Drop detection, Energy mapping, Auto-cut
    - Edit: Brand presets, Animated captions, Auto-track
    - Auto-schedule: TikTok, Instagram, Calendar
- On scroll: each column slides in 24px with 200ms stagger

### 3.7 Auto-mode showcase
- Creme background section, headline: "Auto-mode. Set it once. Ship forever."
- Big looping animation:
  - Left side: video file icon labeled "live_set.wav" with progress bar filling
  - Middle: arrow connector animating left-to-right (orange dot traveling)
  - Animated machine middle stage: small "AI" badge pulse, captions appearing, brand watermark applying
  - Arrow continues to right
  - Right side: three social posts appearing one by one (Instagram, TikTok, YouTube cards)
  - Whole sequence loops every 8 seconds
- Below animation, 4 bullet points in a 4-column grid:
  - Fully automatic workflow
  - From upload to auto-schedule
  - Approve and Live
  - Insights
- Sub-line: "Add customisation with brand presets, caption presets and auto-tracking."

### 3.8 Features accordion
- Black background, headline: "Everything inside Omni DJ."
- 6 accordion rows (one open at a time):
  - Analyse, Library, Brand, Social, Calendar, Insights
- Closed state: large 48px row title in Helvetica Medium, creme color, with a + icon right-aligned
- Open state: + becomes -, content slides down (height auto with framer-motion AnimatePresence):
  - 2-3 sentence description left
  - Small 4:3 screenshot or illustration right
- Only one open at a time; opening another closes the current

### 3.9 Roadmap horizontal carousel
- Black background, headline: "Roadmap."
- Sub: "What's shipped. What's next. What we're building."
- Horizontal scrollable timeline:
  - Single horizontal line across, with bullet dots at each milestone
  - Each milestone is a card above the line connected by a vertical tick
  - Cards in your exact order (no dates):
    1. Beta feedback & new feature implementation
    2. Out-of-beta launch
    3. Direct Social sharing (TikTok, Instagram, Facebook, Twitter)
    4. Watch-folder feature (local, Dropbox, Google Drive)
    5. Multi-cam solution
    6. Insights full launch
    7. Batch-processing
    8. Multi-artist workspace
    9. Auto-mode
    10. Social Advertising (TikTok, Instagram, Facebook, Twitter)
    11. Streaming platform analytics (Spotify, Soundcloud, Beatport)
    12. Omni DJ Mini
  - User scrolls horizontally with native drag or arrow buttons left/right
  - On scroll-into-view: dots fade in one by one, cards slide up from below
- Each card: title in Medium, 2-line description in Light

### 3.10 Closing CTA
- Creme background, full-bleed
- Headline: "Stop editing. Start releasing."
- Sub: "Download Omni DJ and turn your next set into a month of content."
- Two buttons: "Download Omni DJ" (orange) + "Talk to sales" (black outline)

### 3.11 Footer
Black background, creme text. 4 columns plus social icons row right.
- **Get Started**: Download, Request demo, Pricing, For business
- **Company**: About, Trust, Terms, Privacy
- **Connect**: Collective
- **Resources**: Knowledge Center
- Right side: social icons: Instagram, TikTok, YouTube, LinkedIn, Facebook
- Bottom row: "OMNI DJ © 2026. ALL RIGHTS RESERVED." + small "by MONO LABS" right-aligned

## 4. Pricing page

### Toggle
Monthly / Yearly with 15% off badge on yearly. Yearly prices shown as monthly equivalent.

### Currency switcher
EUR / USD toggle in the top-right of the pricing page. Defaults to EUR. USD conversion uses a fixed rate stored in `lib/content/pricing.ts` (manually maintained, not live FX). Both currencies visible on the card simultaneously is also acceptable — Sjuul to pick before build.

USD reference prices (using ~1.10 EUR/USD as starting point, Sjuul to confirm):
- Free: $0
- Pro: $79/mo monthly, $67/mo billed yearly
- Studio: $219/mo monthly, $186/mo billed yearly
- Studio+: Custom

### Cards (4 across on desktop, stacked mobile)
1. **Free** — €0
   - For: DJs, Talent managers
   - Included: Analyse 2 DJ-sets, Library
   - Excluded: Editor, Brand, Social, Calendar, Auto-mode
   - CTA: "Download free"
2. **Pro** — €75/mo (€63.75/mo billed yearly)
   - For: DJs, Talent managers, Videographers, Editors
   - Included: 4 DJ-sets/month, Editor, Brand presets, Captions, Social, Calendar
   - CTA: "Start free trial"
3. **Studio** — €200/mo (€170/mo billed yearly)
   - For: Artist teams, Talent managers, Record labels
   - Included: Everything in Pro, plus Multi-artist workspaces, Batch processing, Auto-mode, Watch-folder, Insights
   - CTA: "Start free trial"
4. **Studio+** — Custom
   - For: Event organisers, Festival organisers, Artist teams
   - Included: Tailored to your team (TBD — Sjuul to define)
   - CTA: "Contact us"

Each card has feature checklist with roadmap items showing small "soon" badge.

### Comparison matrix
Opus-style: feature rows grouped by category (Analyse, Editor, Brand, Social, Calendar, Insights, Workspace, Support). Each row shows ✓ or feature limit per tier. Roadmap items get "soon" pill.

## 5. Contact page
- Black background, headline: "Let's talk."
- Sub: "Tell us about your set, your team, your audience."
- Form fields:
  - Name
  - Email
  - Role dropdown: DJ / Talent manager / Videographer or editor / Event organiser / Record label / Other
  - Optional: Company / Artist name
  - Message
- Submit goes to `/api/contact` (Flask). Role tag included in payload. Email routed to appropriate inbox (you configure in .env).
- Success state: replace form with "Thanks. We'll be in touch within 2 business days."

## 6. Collective page
- Linked from footer
- Black background, headline: "The artists shaping Omni DJ."
- Grid of artist cards, each with:
  - 9:16 video clip placeholder
  - Artist name
  - Social handle (linked)
  - Optional 1-line credit (festival, label)
- For now: 8 placeholder cards. You add real artists later.

## 7. Backend (Flask)

### Endpoints
- `POST /api/contact` — receives form, validates, sends email via SMTP. Role-tags subject line (`[STUDIO+] New contact from...`).
- `POST /api/beta-signup` — stores email + UA in a simple SQLite db, sends welcome email.

### Tech
- Flask 3.x, Flask-CORS, python-dotenv, gunicorn for production
- SQLite for now (file-based, lives in `backend/data/omnidj.db`)
- SMTP via configurable provider (Postmark recommended, or your SMTP)
- `.env.example` provided; real `.env` never committed

### Deployment notes
- Frontend: Cloudflare Pages. Next.js exported as static (`next export` or `output: 'export'` in next.config). All animations work client-side. No SSR needed for this site.
- Backend: Flask deployed separately. Recommended: Fly.io or Railway (Cloudflare Workers can't run Flask directly without Python on Workers, which is still beta). Backend lives at `api.omnidj.com` subdomain.
- Domain: omnidj.com owned by Sjuul via TransIP. DNS managed via Cloudflare. Sjuul to set up Cloudflare Pages deployment from a git repo (GitHub recommended).
- SSL: Cloudflare handles TLS automatically for both apex and api subdomain.

## 8. Build order (chronological tasks)

Phase 1 — Foundation
1. Scaffold Next.js + Tailwind project
2. Set up global styles, color tokens, Helvetica stack
3. Build StickyNav with animated logo + nav links
4. Build Footer

Phase 2 — Home page sections (in order)
5. Hero with logo reveal animation + 3 CTAs + pillar cards
6. Artist carousel (placeholder videos)
7. Enterprise tabs
8. Tool overview with SVG connector flow
9. Workflow 3-column section
10. Auto-mode looping animation
11. Features accordion
12. Roadmap horizontal carousel
13. Closing CTA

Phase 3 — Other pages
14. Pricing page (cards + matrix + toggle)
15. Contact page + Flask backend
16. Collective page
17. For business, Features, Solutions, Resources pages (stub or minimal until content is ready)
18. Legal pages (terms, privacy, trust placeholders)

Phase 4 — Polish
19. Mobile responsive pass
20. Accessibility pass (WCAG 2.1 AA)
21. Performance pass (image optimization, lazy loading, Lighthouse)
22. SEO pass (metadata, OG images, sitemap)
23. Connect Flask backend, wire forms, test in production-like env

## 9. Resolved items (from Sjuul's answers)

1. **Logo file**: Omni DJ mark is an 8-circle ring. PNG references provided (white-on-black and black-on-transparent). To be re-authored as clean SVG with both color variants.
2. **Hero headline**: "Turn your hours long DJ-sets into 20-second viral clips." is the working final. 8 alternatives listed in section 3.2 for final pick before launch.
3. **Studio+ feature list**: still TBD, Sjuul to define before launch. Card shows "Custom" until then.
4. **Real artist video clips**: placeholders used. Sjuul drops final files into `/public/videos/artists/` when ready.
5. **Workflow / tool screenshots**: placeholders used. Sjuul provides actual UI screenshots from Omni DJ when ready.
6. **Domain + hosting**: omnidj.com owned via TransIP. DNS + frontend on Cloudflare. Static export via Cloudflare Pages. Backend on Fly.io or Railway. NOT Vercel.
7. **Brand assets**: use black + creme text colors from the Omni DJ tool, plus the same orange from the tool. Exact hex codes for creme and orange to be confirmed by Sjuul (sample from tool screenshots). Placeholders in section 1.
8. **Knowledge Center**: empty link for now.
9. **Pricing currency**: EUR + USD both supported via toggle.
10. **Email provider**: backend built provider-agnostic via SMTP env vars. Choice deferred to launch time.

## 9b. Still open for next session

Before code generation:
- Confirm exact creme + orange hex values from Omni DJ tool
- Pick final hero headline from the 8 alternatives (or keep the current one)
- Decide currency switcher: side-by-side display vs toggle
- Provide screenshots or descriptions of the Omni DJ Analyse / Editor / Auto-mode screens for placeholders to be sized correctly
8. **Knowledge Center destination**: empty link (`#`) for now. Sjuul to provide URL later.
9. **Pricing currency**: EUR + USD both supported. Toggle on pricing page. Decided.
10. **Email provider for backend**: Sjuul to decide later. Backend will be built provider-agnostic via SMTP env vars so any provider plugs in without code changes.

## 10. Out of scope for this build

- Login / signup flow (the "Sign up" and "Log in" nav links lead to placeholders or to your existing product app)
- User dashboard
- Payment processing (Stripe integration ships separately)
- Knowledge Center content
- Blog/changelog (linked but not built here)

---

## Approval gate

Before code generation starts in the next session, please confirm:
- [ ] Plan reads correctly end-to-end
- [ ] Section order matches your vision
- [ ] Pricing structure is final (€0/€75/€200/Custom, 15% yearly off, EUR+USD)
- [ ] Tech stack OK (Next.js static export + Tailwind + Flask + Cloudflare Pages)
- [ ] File location OK (`/Omni DJ/omnidj.com/`)
- [ ] 8-circle logo description matches your asset
- [ ] Item 9b "still open" list is acceptable to defer

## Next session: kickoff prompt

To pick up cleanly in a new session, open a new chat in the Omni DJ folder and paste:

> Read PLAN-website.md and start Phase 1 of the build. Scaffold the Next.js project in /omnidj.com/, set up Tailwind + global styles + Helvetica stack, then build StickyNav and Footer components. Stop after Phase 1 for review.
