// Special metadata file: dynamic favicon generation.
// For `output: 'export'` compat, route is statically pre-rendered at build time.
import { ImageResponse } from 'next/og';

export const size = { width: 32, height: 32 };
export const contentType = 'image/png';

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          background: '#000000',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <svg viewBox="0 0 100 100" width="28" height="28" xmlns="http://www.w3.org/2000/svg">
          {Array.from({ length: 8 }).map((_, i) => {
            const angle = (i / 8) * Math.PI * 2 - Math.PI / 2;
            const cx = 50 + Math.cos(angle) * 36;
            const cy = 50 + Math.sin(angle) * 36;
            return <circle key={i} cx={cx} cy={cy} r="11" fill="#F5EFE3" />;
          })}
        </svg>
      </div>
    ),
    size
  );
}
