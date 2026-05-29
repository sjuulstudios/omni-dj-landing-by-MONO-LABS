/**
 * Artist carousel data — 8 tiles.
 *
 * `views` is a static, hand-editable number for now. Later this can be wired to
 * pull live counts from the post itself so it grows as the clip grows (out of
 * scope for this round, per Sjuul). `video` is the 9:16 muted clip path; leave
 * undefined to show the wireframe placeholder until real clips are dropped in.
 */
export type Artist = {
  name: string;
  views: string;          // display string, e.g. "47K"
  platform: 'instagram' | 'tiktok';
  video?: string;         // e.g. '/videos/artists/1.mp4'
};

export const artists: Artist[] = [
  { name: 'Artist 1', views: '47K', platform: 'tiktok' },
  { name: 'Artist 2', views: '120K', platform: 'instagram' },
  { name: 'Artist 3', views: '38K', platform: 'tiktok' },
  { name: 'Artist 4', views: '210K', platform: 'instagram' },
  { name: 'Artist 5', views: '64K', platform: 'tiktok' },
  { name: 'Artist 6', views: '95K', platform: 'instagram' },
  { name: 'Artist 7', views: '52K', platform: 'tiktok' },
  { name: 'Artist 8', views: '180K', platform: 'instagram' }
];
