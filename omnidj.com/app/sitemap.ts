import type { MetadataRoute } from 'next';

const BASE = 'https://omnidj.com';

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const routes = [
    '',
    '/features',
    '/solutions',
    '/resources',
    '/pricing',
    '/for-business',
    '/contact',
    '/collective',
    '/legal/terms',
    '/legal/privacy',
    '/legal/trust'
  ];
  return routes.map(r => ({
    url: `${BASE}${r}`,
    lastModified: now,
    changeFrequency: 'monthly' as const,
    priority: r === '' ? 1 : 0.7
  }));
}
