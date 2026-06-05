import { DOWNLOAD_URL } from '@/lib/config';

export type Tier = {
  id: 'free' | 'pro' | 'studio' | 'studio-plus';
  name: string;
  forWho: string;
  monthly: { eur: number | 'custom'; usd: number | 'custom' };
  yearly: { eur: number | 'custom'; usd: number | 'custom' }; // shown as per-month equivalent
  yearlyBadge?: string;
  features: { label: string; included: boolean; soon?: boolean }[];
  cta: { label: string; href: string };
  highlight?: boolean;
};

export const pricingContent = {
  headline: 'Pricing.',
  subline: 'Local-first, no surprise overages, cancel any time.',
  yearlyBadge: '15% off',
  tiers: [
    {
      id: 'free',
      name: 'Free',
      forWho: 'DJs · Talent managers',
      monthly: { eur: 0, usd: 0 },
      yearly: { eur: 0, usd: 0 },
      features: [
        { label: 'Analyse 2 DJ-sets', included: true },
        { label: 'Library', included: true },
        { label: 'Editor', included: false },
        { label: 'Brand', included: false },
        { label: 'Social', included: false },
        { label: 'Calendar', included: false },
        { label: 'Auto-mode', included: false }
      ],
      cta: { label: 'Download free', href: DOWNLOAD_URL }
    },
    {
      id: 'pro',
      name: 'Pro',
      forWho: 'DJs · Videographers · Editors',
      monthly: { eur: 75, usd: 79 },
      yearly: { eur: 63.75, usd: 67 },
      yearlyBadge: '15% off',
      features: [
        { label: '4 DJ-sets / month', included: true },
        { label: 'Editor', included: true },
        { label: 'Brand presets', included: true },
        { label: 'Animated captions', included: true },
        { label: 'Social', included: true },
        { label: 'Calendar', included: true },
        { label: 'Multi-artist', included: false }
      ],
      cta: { label: 'Start free trial', href: DOWNLOAD_URL },
      highlight: true
    },
    {
      id: 'studio',
      name: 'Studio',
      forWho: 'Artist teams · Talent managers · Labels',
      monthly: { eur: 200, usd: 219 },
      yearly: { eur: 170, usd: 186 },
      yearlyBadge: '15% off',
      features: [
        { label: 'Everything in Pro', included: true },
        { label: 'Multi-artist workspaces', included: true },
        { label: 'Batch processing', included: true },
        { label: 'Auto-mode', included: true, soon: true },
        { label: 'Watch-folder', included: true, soon: true },
        { label: 'Insights', included: true, soon: true }
      ],
      cta: { label: 'Start free trial', href: DOWNLOAD_URL }
    },
    {
      id: 'studio-plus',
      name: 'Studio+',
      forWho: 'Event organisers · Festivals · Artist teams',
      monthly: { eur: 'custom', usd: 'custom' },
      yearly: { eur: 'custom', usd: 'custom' },
      features: [
        { label: 'Everything in Studio', included: true },
        { label: 'Dedicated success manager', included: true },
        { label: 'Custom SSO & SLA', included: true },
        { label: 'Custom integrations', included: true },
        { label: 'Roster onboarding', included: true }
      ],
      cta: { label: 'Contact us', href: '/contact' }
    }
  ] as Tier[],
  matrix: {
    groups: [
      {
        title: 'Analyse',
        rows: [
          ['DJ-sets per month', '2', '4', 'Unlimited', 'Unlimited'],
          ['Drop detection', '✓', '✓', '✓', '✓'],
          ['BPM & key', '✓', '✓', '✓', '✓'],
          ['Energy map', '—', '✓', '✓', '✓']
        ]
      },
      {
        title: 'Editor',
        rows: [
          ['Trim & export', '—', '✓', '✓', '✓'],
          ['Aspect-ratio rail (9:16 · 1:1 · 4:5 · 16:9)', '—', '✓', '✓', '✓'],
          ['Auto-track', '—', '✓', '✓', '✓']
        ]
      },
      {
        title: 'Brand',
        rows: [
          ['Brand kit', '—', '✓', '✓', '✓'],
          ['Caption presets', '—', '✓', '✓', '✓'],
          ['Watermark / Intro / Outro', '—', '✓', '✓', '✓']
        ]
      },
      {
        title: 'Social',
        rows: [
          ['Connect TikTok / IG / YT / X', '—', '✓', '✓', '✓'],
          ['Direct publish', '—', 'soon', 'soon', 'soon']
        ]
      },
      {
        title: 'Calendar',
        rows: [
          ['Month & week view', '—', '✓', '✓', '✓'],
          ['Drag-and-drop scheduling', '—', '✓', '✓', '✓']
        ]
      },
      {
        title: 'Workspace',
        rows: [
          ['Multi-artist', '—', '—', '✓', '✓'],
          ['Batch processing', '—', '—', '✓', '✓'],
          ['Watch-folder', '—', '—', 'soon', '✓']
        ]
      },
      {
        title: 'Support',
        rows: [
          ['Community', '✓', '✓', '✓', '✓'],
          ['Priority email', '—', '—', '✓', '✓'],
          ['Dedicated success manager', '—', '—', '—', '✓'],
          ['SLA', '—', '—', '—', '✓']
        ]
      }
    ]
  }
};
