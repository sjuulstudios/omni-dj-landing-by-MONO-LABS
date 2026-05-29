'use client';

import React, { useRef, useState } from 'react';
import Reveal from '@/components/ui/Reveal';
import { artists, type Artist } from '@/lib/content/artists';

/**
 * Artist carousel — single-row continuous runway, 8 tiles.
 * Hover: plays the (muted) clip and reveals artist + view count. A small
 * unmute button sits top-center of the card. Hover pauses the scroll.
 * prefers-reduced-motion stops the loop and disables autoplay.
 */

function PlatformBadge({ kind }: { kind: 'instagram' | 'tiktok' }) {
  const common = { width: 12, height: 12, viewBox: '0 0 24 24', fill: 'none' as const, stroke: '#0A0A0A', strokeWidth: 2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  return (
    <div className="absolute top-2 left-2 w-6 h-6 rounded-full flex items-center justify-center z-20" style={{ background: 'var(--creme)' }} aria-label={kind}>
      {kind === 'instagram'
        ? <svg {...common}><rect x="3" y="3" width="18" height="18" rx="5" /><circle cx="12" cy="12" r="4" /></svg>
        : <svg {...common}><path d="M14 4v9a4 4 0 1 1-4-4" /><path d="M14 4c0 2.2 1.8 4 4 4" /></svg>}
    </div>
  );
}

function ArtistTile({ artist, index }: { artist: Artist; index: number }) {
  const [hover, setHover] = useState(false);
  const [muted, setMuted] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  const onEnter = () => {
    setHover(true);
    const v = videoRef.current;
    if (v) v.play().catch(() => {});
  };
  const onLeave = () => {
    setHover(false);
    setMuted(true);
    const v = videoRef.current;
    if (v) { v.pause(); v.currentTime = 0; }
  };

  const toggleMute = (e: React.MouseEvent) => {
    e.stopPropagation();
    const v = videoRef.current;
    const next = !muted;
    setMuted(next);
    if (v) v.muted = next;
  };

  return (
    <div
      className="flex-shrink-0 rounded-2xl overflow-hidden relative placeholder-box"
      style={{ width: 210, aspectRatio: '9 / 16' }}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
    >
      <PlatformBadge kind={artist.platform} />

      {/* Unmute control — top center, only meaningful while a clip is playing */}
      {artist.video && (
        <button
          onClick={toggleMute}
          aria-label={muted ? 'Unmute preview' : 'Mute preview'}
          className="absolute z-20 flex items-center justify-center rounded-full"
          style={{
            top: 8,
            left: '50%',
            transform: 'translateX(-50%)',
            width: 28,
            height: 28,
            background: 'rgba(10,10,10,0.6)',
            backdropFilter: 'blur(4px)',
            color: 'var(--creme)',
            opacity: hover ? 1 : 0,
            transition: 'opacity 200ms var(--ease-drop)'
          }}
        >
          {muted
            ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 5L6 9H2v6h4l5 4V5z" /><path d="M23 9l-6 6M17 9l6 6" /></svg>
            : <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 5L6 9H2v6h4l5 4V5z" /><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a9 9 0 0 1 0 14" /></svg>}
        </button>
      )}

      {/* Clip video (muted loop) — only when a real clip is provided */}
      {artist.video && (
        <video
          ref={videoRef}
          src={artist.video}
          muted={muted}
          loop
          playsInline
          preload="none"
          className="absolute inset-0 w-full h-full object-cover z-0"
          style={{ opacity: hover ? 1 : 0, transition: 'opacity 300ms var(--ease-drop)' }}
        />
      )}

      {/* placeholder texture (behind video) */}
      <div aria-hidden="true" className="absolute inset-0" style={{ backgroundImage: 'repeating-linear-gradient(135deg, rgba(245,239,227,0.025) 0 2px, transparent 2px 16px)' }} />
      {!artist.video && <span className="relative z-10 text-[10px]">Artist clip {index + 1}</span>}

      {/* Metadata overlay — artist + views, fades in on hover */}
      <div
        className="absolute bottom-0 left-0 right-0 z-10 p-3"
        style={{
          background: 'linear-gradient(0deg, rgba(10,10,10,0.85) 0%, transparent 100%)',
          opacity: hover ? 1 : 0,
          transform: hover ? 'translateY(0)' : 'translateY(6px)',
          transition: 'opacity 240ms var(--ease-drop), transform 240ms var(--ease-drop)'
        }}
      >
        <div className="text-creme text-[13px] font-medium">{artist.name}</div>
        <div className="mono-label" style={{ color: 'var(--creme)' }}>{artist.views} views</div>
      </div>
    </div>
  );
}

export default function ArtistCarousel() {
  return (
    <section className="section bg-black overflow-hidden section-bridge">
      <div className="page-shell">
        <Reveal>
          <h2 className="headline-section text-creme max-w-[680px]">
            Built for the artists shaping nightlife.
          </h2>
        </Reveal>
      </div>

      <div
        className="mt-16 relative overflow-hidden artist-runway"
        style={{
          maskImage: 'linear-gradient(to right, transparent 0%, #000 12%, #000 88%, transparent 100%)',
          WebkitMaskImage: 'linear-gradient(to right, transparent 0%, #000 12%, #000 88%, transparent 100%)'
        }}
      >
        <div className="flex gap-4 artist-runway-track" style={{ width: 'max-content', animation: 'artistRunway 70s linear infinite' }}>
          {[0, 1, 2].map(cycle => (
            <div key={cycle} className="flex gap-4 flex-shrink-0">
              {artists.map((a, i) => (
                <ArtistTile key={`${cycle}-${i}`} artist={a} index={i} />
              ))}
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        @keyframes artistRunway {
          0%   { transform: translateX(0); }
          100% { transform: translateX(calc(-100% / 3)); }
        }
        .artist-runway:hover .artist-runway-track { animation-play-state: paused; }
        @media (prefers-reduced-motion: reduce) {
          .artist-runway-track { animation: none !important; }
        }
      `}</style>
    </section>
  );
}
