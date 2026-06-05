import { DOWNLOAD_URL } from '@/lib/config';

export const footerColumns = [
  {
    title: 'Get Started',
    links: [
      { label: 'Download', href: DOWNLOAD_URL },
      { label: 'Request demo', href: '/contact' },
      { label: 'Pricing', href: '/pricing' },
      { label: 'For business', href: '/for-business' }
    ]
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '#' },
      { label: 'Trust', href: '/legal/trust' },
      { label: 'Terms', href: '/legal/terms' },
      { label: 'Privacy', href: '/legal/privacy' }
    ]
  },
  {
    title: 'Connect',
    links: [{ label: 'Collective', href: '/collective' }]
  },
  {
    title: 'Resources',
    links: [{ label: 'Knowledge Center', href: '#' }]
  }
];

export const footerSocials = [
  { label: 'Instagram', href: '#', icon: 'instagram' },
  { label: 'TikTok', href: '#', icon: 'tiktok' },
  { label: 'YouTube', href: '#', icon: 'youtube' },
  { label: 'LinkedIn', href: '#', icon: 'linkedin' },
  { label: 'Facebook', href: '#', icon: 'facebook' }
];
