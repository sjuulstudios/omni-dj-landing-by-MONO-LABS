# Omni DJ — Remotion animations

Three compositions render the heavier animations on the marketing site:

- **LogoReveal** — hero ring entry + slow rotation (800×800, 12s, 30fps)
- **AutoModePipeline** — file → AI → 3 posts looping (1600×600, 8s, 30fps, creme bg)
- **ToolOverviewFlow** — waveform → reframe fan → shorts stack (1600×600, 10s, 30fps, ink bg)

## First time setup (one-shot)

```
cd remotion
npm install
```

That installs Remotion + React + TS only inside this folder.

## Preview in Remotion Studio

```
cd remotion
npm run studio
```

Then http://localhost:3000 (Remotion's own preview app) — pick a composition from the sidebar.

## Render the three MP4s

```
cd remotion
npm run render:all
```

That drops three files into `../public/remotion/`:

- `logo-reveal.mp4`
- `auto-mode.mp4`
- `tool-flow.mp4`

Remotion will download a headless Chrome shell the first time you render (~70MB, one-time).

## How the site uses them

The site imports a `RemotionMp4` wrapper component (`components/ui/RemotionMp4.tsx`). If the MP4 exists the wrapper plays it as a looping muted autoplay `<video>`; if not it renders the static CSS fallback you had before. Means the site still works pre-render.

To re-render after editing a composition: tweak code under `remotion/src/compositions/` and re-run `npm run render:all`.

## Where each video is used in the Next.js site

| MP4 | Used in component |
| --- | --- |
| `logo-reveal.mp4` | `components/hero/LogoReveal.tsx` |
| `auto-mode.mp4` | `components/automode/AutoModeSection.tsx` |
| `tool-flow.mp4` | `components/overview/ToolOverview.tsx` |
