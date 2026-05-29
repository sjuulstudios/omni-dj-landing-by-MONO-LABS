'use client';

import React, { useEffect, useRef, useState } from 'react';

type Props = {
  src: string;                     // e.g. "/remotion/logo-reveal.mp4"
  fallback: React.ReactNode;       // shown if MP4 missing or before it loads
  className?: string;
  style?: React.CSSProperties;
  /** Lock aspect ratio (e.g. "1 / 1", "16 / 6") so layout stays stable before the file loads */
  aspectRatio?: string;
};

/**
 * RemotionMp4 — render a Remotion-rendered MP4 as a looping muted autoplay video.
 * If the MP4 is 404 (not rendered yet) or fails to load, the fallback art renders instead.
 */
export default function RemotionMp4({ src, fallback, className, style, aspectRatio }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [ok, setOk] = useState<'loading' | 'ok' | 'failed'>('loading');
  // Keep the fallback fully opaque until the video is actually painting frames,
  // not merely loaded — this removes the white/empty flash on slow connections.
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    // Probe the file via fetch HEAD; if 404, drop to fallback immediately
    let cancelled = false;
    fetch(src, { method: 'HEAD' })
      .then(r => {
        if (cancelled) return;
        if (r.ok) setOk('ok');
        else setOk('failed');
      })
      .catch(() => !cancelled && setOk('failed'));
    return () => { cancelled = true; };
  }, [src]);

  // aspectRatio is required to reserve layout space before metadata loads.
  // Falls back to 16/9 so a missing prop never causes a layout jump.
  const containerStyle: React.CSSProperties = {
    position: 'relative',
    overflow: 'hidden',
    aspectRatio: aspectRatio ?? '16 / 9',
    ...style
  };

  if (ok === 'failed') {
    return <div className={className} style={containerStyle}>{fallback}</div>;
  }

  return (
    <div className={className} style={containerStyle}>
      {/* Fallback acts as the poster: stays opaque until the first frame paints. */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: playing ? 0 : 1,
          transition: 'opacity 400ms var(--ease-drop)'
        }}
      >
        {fallback}
      </div>
      {ok === 'ok' && (
        <video
          ref={videoRef}
          src={src}
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          onPlaying={() => setPlaying(true)}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover'
          }}
          onError={() => setOk('failed')}
        />
      )}
    </div>
  );
}
