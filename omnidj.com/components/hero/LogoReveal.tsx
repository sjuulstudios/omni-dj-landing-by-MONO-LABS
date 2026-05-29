'use client';

import React, { useEffect, useState } from 'react';
import OmniMark from '@/components/logo/OmniMark';
import RemotionMp4 from '@/components/ui/RemotionMp4';

/**
 * Hero logo reveal — compact eyebrow version.
 * Renders inline at small size (default 56px) next to a wordmark + tagline.
 *
 * Falls back to OmniMark CSS spin if /remotion/logo-reveal.mp4 missing.
 */
export default function LogoReveal({ size = 56 }: { size?: number }) {
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setRevealed(true), 60);
    return () => clearTimeout(t);
  }, []);

  const fallback = (
    <div className="absolute inset-0 flex items-center justify-center">
      <div
        className="transition-all flex items-center justify-center w-full h-full"
        style={{
          opacity: revealed ? 1 : 0,
          transform: revealed ? 'translateX(0)' : 'translateX(-12px)',
          transition:
            'opacity 700ms cubic-bezier(0.22, 1, 0.36, 1), transform 700ms cubic-bezier(0.22, 1, 0.36, 1)'
        }}
      >
        <div
          style={{
            animation: revealed
              ? 'logoEntryRotate 900ms cubic-bezier(0.22, 1, 0.36, 1) 0ms 1 forwards, spinSlow 12s linear 900ms infinite'
              : undefined,
            transformOrigin: 'center center'
          }}
        >
          <OmniMark size={size} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <RemotionMp4
        src="/remotion/logo-reveal.mp4"
        fallback={fallback}
        aspectRatio="1 / 1"
        style={{ width: '100%', height: '100%' }}
      />
      <style jsx>{`
        @keyframes logoEntryRotate {
          0%   { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
