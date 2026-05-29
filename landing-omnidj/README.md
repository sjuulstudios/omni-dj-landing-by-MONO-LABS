# Omni DJ Landing v1

Premium dark/grey/cream landing page for omnidj.com beta launch.

## Files

- `index.html` — Main landing
- `privacy.html` — GDPR-compliant Privacy Policy
- `terms.html` — Terms of Service
- `styles.css` — All styling (CSS variables for theme)
- `script.js` — Mobile nav, smooth-scroll, beta form handler, reveal-on-scroll
- `favicon.svg` — SVG favicon
- `og-image.svg` — Open Graph preview image (1200x630)

## Before deploy: replace placeholders

Search and replace these tokens before publishing:

1. **`REPLACE_ME`** in `index.html` — Formspree form action URL.
   - Get from https://formspree.io (free tier 50/month).
   - Or replace with your Supabase Edge Function URL.
   - Or any email-capture endpoint that accepts POST.

2. **`REPLACE_DMG_URL`** in `index.html` — Cloudflare R2 DMG download link.
   - Pattern: `https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg`
   - Created during `PLAN-APPLE-DEVELOPER-2026-05-28.md` Stap 8.

## Optional improvements before public launch

- Replace `og-image.svg` with a real screenshot once the app is rebranded
- Add a real product demo video as `assets/demo.webm` (referenced from a hero "Watch demo" button)
- Add 3-4 real product screenshots as `assets/screen-*.png`
- Add Cloudflare Web Analytics snippet (privacy-preserving)
- Wire up the FAQ open-state to URL hash for shareable deep-links

## Deploy

### Option A — Cloudflare Pages direct upload
1. Zip the whole `landing-omnidj/` folder
2. Cloudflare dashboard → Workers & Pages → Create → Pages → Direct upload
3. Name: `omnidj-landing`
4. Upload the zip
5. Connect custom domain `omnidj.com` and `www.omnidj.com`

### Option B — Git-connect (recommended for updates)
1. Push this folder to a GitHub repo `omnidj-landing`
2. Cloudflare Pages → Create → Connect to Git → select repo
3. Build settings: framework = None, build command = empty, output dir = `/`
4. Connect custom domain

## Local preview

```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/landing-omnidj"
python3 -m http.server 8080
```

Open http://localhost:8080 to preview.

## Brand tokens

The CSS uses these custom properties (top of `styles.css`):

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0A0A0A` | Page background |
| `--bg-1` | `#111112` | Alt section bg |
| `--surface` | `#1F1F22` | Cards, modals |
| `--text` | `#F2E8D3` | Cream text |
| `--accent` | `#FF6F2D` | Brand orange |
| `--font-display` | Fraunces | Headlines |
| `--font-sans` | Inter | Body |

Change these to retheme the entire landing instantly.

## What I deliberately did not add

- Actual screenshots (need to wait for rebrand)
- Real product demo video (need to record on the rebranded app)
- Cookie banner (analytics is cookieless; no banner required under GDPR)
- A blog or changelog (out of scope for beta)
- Auth/login flow (the app handles that, not the landing)
