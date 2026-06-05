import { DOWNLOAD_URL } from '@/lib/config';

export const heroContent = {
  eyebrow: 'OMNI DJ · BY MONO LABS',
  headline: 'Turn your hours long DJ-sets into 20-second viral clips.',
  subline: 'Local analysis on your machine. Drops detected automatically. Ready to post.',
  ctas: {
    drop: {
      label: 'Drop your DJ-set',
      hint: '.wav .mp3 .mp4 — analysed on your machine'
    },
    download: {
      label: 'Download Omni DJ',
      href: DOWNLOAD_URL
    },
    beta: {
      label: 'Join beta',
      placeholder: 'Drop your email for beta access'
    }
  },
  pillars: [
    {
      title: 'Local-first. Secure. Fast.',
      body: 'Drops, energy and BPM detected on your own machine. No upload queues. No cloud quota.'
    },
    {
      title: 'Works offline.',
      body: 'Your set never leaves your machine. Analyse, clip and edit without a connection.'
    },
    {
      title: 'Clip from anywhere.',
      body: 'Mac or Windows. Native app, no browser tab. Open it, drop a file, ship a month of content.'
    }
  ]
};
