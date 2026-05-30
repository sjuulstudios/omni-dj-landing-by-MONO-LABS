export type MegaItem = {
  title: string;
  body: string;
  href: string;
  soon?: boolean;
  icon?: string;
};

export type MegaGroup = {
  title?: string;
  items: MegaItem[];
};

export const featuresMega: { columns: MegaGroup[] } = {
  columns: [
    {
      title: 'Analyse & cut',
      items: [
        {
          title: 'Drop detection',
          body: 'Drop detection, BPM and key, full energy map across the whole set.',
          href: '/features#analyse',
          icon: 'wave'
        },
        {
          title: 'Auto-cut',
          body: '30 to 60 second clip windows proposed automatically from every drop.',
          href: '/features#analyse',
          icon: 'scissors'
        },
        {
          title: 'Multi-cam',
          body: 'Align multiple camera angles to the same set. Pick the best frame per drop.',
          href: '/features#multicam',
          icon: 'camera',
          soon: true
        }
      ]
    },
    {
      title: 'Brand & edit',
      items: [
        {
          title: 'Brand kits',
          body: 'Logos, captions, watermarks per artist or label. Saved once, applied everywhere.',
          href: '/features#brand',
          icon: 'palette'
        },
        {
          title: 'Animated captions',
          body: 'Per-platform caption presets with timing locked to the beat.',
          href: '/features#captions',
          icon: 'caption'
        },
        {
          title: 'Auto-track',
          body: 'Keep the subject framed across every aspect ratio automatically.',
          href: '/features#track',
          icon: 'target',
          soon: true
        }
      ]
    },
    {
      title: 'Ship',
      items: [
        {
          title: 'Aspect-ratio rail',
          body: '9:16, 1:1, 4:5, 16:9 in one pass. Same edit, every platform.',
          href: '/features#ratio',
          icon: 'rail'
        },
        {
          title: 'Social',
          body: 'Direct publish to TikTok, Instagram, YouTube and X from inside Omni DJ.',
          href: '/features#social',
          icon: 'share',
          soon: true
        },
        {
          title: 'Calendar',
          body: 'Drag clips onto dates. See gaps before your audience does.',
          href: '/features#calendar',
          icon: 'calendar'
        },
        {
          title: 'Insights',
          body: 'Per-clip retention and account growth across every platform.',
          href: '/features#insights',
          icon: 'chart',
          soon: true
        }
      ]
    }
  ]
};

export const solutionsMega: { columns: MegaGroup[] } = {
  columns: [
    {
      items: [
        {
          title: 'DJs',
          body: 'Ship a month of content from one set.',
          href: '/solutions#djs',
          icon: 'dj'
        },
        {
          title: 'Videographers',
          body: 'Cut a month of edits in an afternoon.',
          href: '/solutions#videographers',
          icon: 'film'
        },
        {
          title: 'Talent managers',
          body: 'Every artist on your roster, always posting.',
          href: '/solutions#managers',
          icon: 'users'
        }
      ]
    },
    {
      items: [
        {
          title: 'Event organisers',
          body: 'Recap your event before the bar closes.',
          href: '/solutions#organisers',
          icon: 'event'
        },
        {
          title: 'Festival organisers',
          body: 'Aftermovie-grade shorts from every stage.',
          href: '/solutions#festivals',
          icon: 'flag'
        },
        {
          title: 'Record labels',
          body: 'Roster-wide brand kits and insights that move the needle.',
          href: '/solutions#labels',
          icon: 'disc'
        }
      ]
    }
  ]
};
