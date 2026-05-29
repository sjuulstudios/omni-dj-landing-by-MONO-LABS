import { ImageResponse } from 'next/og';

export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';
export const alt = 'Omni DJ — Turn your DJ-sets into viral clips';

export default function OG() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          background: '#000000',
          display: 'flex',
          flexDirection: 'column',
          padding: 80,
          fontFamily: 'Helvetica, Arial, sans-serif'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <svg viewBox="0 0 100 100" width="80" height="80" xmlns="http://www.w3.org/2000/svg">
            {Array.from({ length: 8 }).map((_, i) => {
              const angle = (i / 8) * Math.PI * 2 - Math.PI / 2;
              const cx = 50 + Math.cos(angle) * 38;
              const cy = 50 + Math.sin(angle) * 38;
              return <circle key={i} cx={cx} cy={cy} r="9" fill="#F5EFE3" />;
            })}
          </svg>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: '#F5EFE3', fontSize: 36, fontWeight: 500, letterSpacing: '-0.02em' }}>
              Omni DJ
            </span>
            <span style={{ color: 'rgba(245,239,227,0.6)', fontSize: 14, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
              by MONO LABS
            </span>
          </div>
        </div>

        <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
          <div
            style={{
              color: '#F5EFE3',
              fontSize: 84,
              lineHeight: 1.05,
              letterSpacing: '-0.03em',
              fontWeight: 700,
              maxWidth: 960
            }}
          >
            Turn your hours-long DJ-sets into 20-second viral clips.
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 16, height: 16, borderRadius: 8, background: '#FF6A1A' }} />
          <span style={{ color: 'rgba(245,239,227,0.7)', fontSize: 22, letterSpacing: '-0.005em' }}>
            Local-first. Drops detected automatically. Ready to post.
          </span>
        </div>
      </div>
    ),
    size
  );
}
