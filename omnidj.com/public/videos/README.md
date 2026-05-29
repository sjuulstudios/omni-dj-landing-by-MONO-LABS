# Video placeholders

The home-page artist carousel and the `/collective` page render placeholder cards until you drop real artist clips here.

Recommended naming:

- `/public/videos/artists/artist-01.mp4` … `artist-16.mp4`
- 9:16, h264, 6–12 seconds, looped, no audio (or muted on autoplay)
- Each under ~3 MB so the bar stays snappy

After you add files, update `components/artists/ArtistCarousel.tsx` to read from a manifest or use a fixed list of filenames.
