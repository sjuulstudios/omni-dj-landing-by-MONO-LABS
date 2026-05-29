export type EnterpriseFeature = {
  icon: string;
  title: string;
  body: string;
  soon?: boolean;
};

export type EnterpriseTab = {
  id: string;
  label: string;
  headline: string;
  body: string;
  /** Aspirational social-proof line shown under the description (not real yet). */
  stat: string;
  /** Anchor on /solutions for the "see more" link. */
  anchor: string;
  features: EnterpriseFeature[];
};

export const enterpriseContent: {
  headline: string;
  subline: string;
  tabs: EnterpriseTab[];
} = {
  headline: 'Built for the teams behind the music.',
  subline: 'Whatever your role, Omni DJ scales with you.',
  tabs: [
    {
      id: 'djs',
      label: 'DJs',
      headline: 'Ship a month of content from one set.',
      body: 'Play the set you would play anyway. Omni DJ pulls the drops, frames every clip for every feed, and queues them on a release rhythm so the algorithm sees you all month.',
      stat: 'One set in. Sixty clips out.',
      anchor: '#djs',
      features: [
        { icon: 'wave', title: 'Drop detection', body: 'Every drop in your set, marked automatically with the cleanest cut in and out.' },
        { icon: 'rail', title: 'Aspect-ratio rail', body: '9:16 for TikTok and Reels, 1:1 for grid, 16:9 for YouTube — one pass.' },
        { icon: 'caption', title: 'Animated captions', body: 'Bouncing captions locked to the beat. Your hook lands before the scroll.' },
        { icon: 'calendar', title: 'Calendar', body: 'Plan the release rhythm. Drag clips onto dates. Never run dry.' },
        { icon: 'shield', title: 'Local-first', body: 'Your unreleased ID stays on your machine. No upload, no leak.' }
      ]
    },
    {
      id: 'videographers',
      label: 'Videographers',
      headline: 'Cut a month of edits in an afternoon.',
      body: 'Stop scrubbing three-hour recordings looking for the drop. Omni DJ marks every cue, exports vertical and landscape variants in one pass, and remembers your brand presets across artists.',
      stat: 'Hours of scrubbing, gone.',
      anchor: '#videographers',
      features: [
        { icon: 'wave', title: 'Drop detection', body: 'Save the hour of scrubbing. Every drop pre-marked the second you open the file.' },
        { icon: 'camera', title: 'Multi-cam', body: 'Align angles to the same set. Pick the best frame per drop.', soon: true },
        { icon: 'batch', title: 'Batch processing', body: 'Queue a whole festival night. Slate ready in the morning.' },
        { icon: 'palette', title: 'Brand kits per artist', body: 'Logos, captions, watermarks scoped to the artist or label.' },
        { icon: 'rail', title: 'Aspect-ratio rail', body: 'Every platform delivered in one export pass.' }
      ]
    },
    {
      id: 'managers',
      label: 'Talent managers',
      headline: 'Every artist on your roster, always posting.',
      body: 'One workspace per artist. Auto-mode posts approved clips on a schedule you set. You stay on top of the calendar instead of inside it.',
      stat: 'A whole roster, one grid.',
      anchor: '#managers',
      features: [
        { icon: 'workspaces', title: 'Multi-artist workspaces', body: 'Isolated brand kit, calendar and history per artist.' },
        { icon: 'palette', title: 'Brand kits per artist', body: 'Each artist keeps their own voice. Switch identities in one click.' },
        { icon: 'calendar', title: 'Calendar', body: 'Roster-wide release planning. See every artist on one grid.' },
        { icon: 'auto', title: 'Auto-mode', body: 'From recording to scheduled post, optionally gated by your approval.', soon: true },
        { icon: 'chart', title: 'Insights', body: 'Which artist is pulling weight. Which clip moved the needle.', soon: true }
      ]
    },
    {
      id: 'organisers',
      label: 'Event organisers',
      headline: 'Recap your event before the bar closes.',
      body: 'Drop the room recording, pick the act, and have shorts ready while the headliner is still on. Real-time recaps for socials, partners, sponsors.',
      stat: 'Recap live before last call.',
      anchor: '#organisers',
      features: [
        { icon: 'watch', title: 'Watch-folder', body: 'Drop the room recording. Clips appear next morning.' },
        { icon: 'batch', title: 'Batch processing', body: 'Run a whole night through the pipeline. Walk away.' },
        { icon: 'rail', title: 'Aspect-ratio rail', body: 'Recap reels and stage stills, ready for every feed.' },
        { icon: 'shield', title: 'Local-first', body: 'Unreleased festival recordings stay on your machine until you decide.' },
        { icon: 'auto', title: 'Auto-mode', body: 'Recap shipped before the last act leaves the stage.', soon: true }
      ]
    },
    {
      id: 'labels',
      label: 'Record labels',
      headline: 'Turn every signed set into shareable proof.',
      body: 'Roster-wide brand kits, batch processing across releases, and insights that show you which drop actually moved the needle.',
      stat: 'The whole catalogue, on cadence.',
      anchor: '#labels',
      features: [
        { icon: 'workspaces', title: 'Multi-artist workspaces', body: 'Whole roster under one account. Each artist sandboxed.' },
        { icon: 'batch', title: 'Batch processing', body: 'Release-week pushes across the whole catalogue.' },
        { icon: 'chart', title: 'Insights', body: 'Per-clip retention by artist, by platform, by release.', soon: true },
        { icon: 'palette', title: 'Brand kits per release', body: 'Pre-save campaigns. Album lockups. Release-specific captions.' },
        { icon: 'auto', title: 'Auto-mode', body: 'Set the release cadence once. Ship continuously.', soon: true }
      ]
    }
  ]
};
