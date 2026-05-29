'use client';

import React, { useRef, useState } from 'react';

/**
 * SetTimeline — the signature motif of the site.
 *
 * A thin horizontal timeline representing a synthesised ~3-hour DJ set, with an
 * energy waveform and three orange "drops" pulsing at fixed positions. Hovering
 * the strip scrubs a playhead that tracks the cursor; the energy bars near the
 * playhead lift, and crossing a drop fires a scale-pulse.
 *
 * Pure SVG/CSS, no assets. Reduced-motion: drops sit static, no playhead motion.
 *
 * Reused later by the roadmap timeline and the auto-mode pipeline indicator.
 */

const VIEW_W = 1000;
const VIEW_H = 96;

// Drop positions as fractions of the set length (intro build, peak, closer).
const DROPS = [0.28, 0.58, 0.83];

// Synthesised energy curve: more bars = denser waveform. Deterministic so SSR
// and client render identically (no Math.random()).
const BAR_COUNT = 120;

// Snap each drop to its nearest bar index so the orange cluster, the energy
// spike and the round marker all sit on exactly the same x.
const DROP_BARS = DROPS.map(d => Math.round(d * (BAR_COUNT - 1)));
const barCenterX = (i: number) => (i + 0.5) * (VIEW_W / BAR_COUNT);

// Round geometry to a fixed precision so the server-rendered and client-rendered
// SVG attribute strings match exactly (avoids React hydration warnings from
// floating-point drift in the Math.sin/Math.exp energy curve).
const r3 = (n: number) => Math.round(n * 1000) / 1000;

function energyAt(i: number): number {
  const x = i / (BAR_COUNT - 1);
  // Base swell across the set + local spikes centred on the snapped drop bars.
  let e = 0.25 + 0.35 * Math.sin(x * Math.PI); // gentle arch
  for (const db of DROP_BARS) {
    const dist = (i - db) / (BAR_COUNT - 1);
    e += 0.55 * Math.exp(-(dist * dist) / 0.0009); // sharp spike at drop
  }
  // Fine texture so it reads as audio, not a smooth curve.
  e += 0.06 * Math.sin(i * 1.7) + 0.04 * Math.sin(i * 0.6);
  return Math.max(0.06, Math.min(1, e));
}

export default function SetTimeline() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [scrub, setScrub] = useState<number | null>(null); // 0..1 or null when idle

  const onMove = (e: React.MouseEvent) => {
    const el = wrapRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    setScrub(Math.max(0, Math.min(1, x)));
  };

  const bars = Array.from({ length: BAR_COUNT }, (_, i) => i);
  const barW = VIEW_W / BAR_COUNT;

  return (
    <div
      ref={wrapRef}
      className="set-timeline"
      onMouseMove={onMove}
      onMouseLeave={() => setScrub(null)}
      role="img"
      aria-label="A three-hour DJ set with three drops detected"
      style={{ position: 'relative', width: '100%', cursor: 'crosshair' }}
    >
      <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} width="100%" height="100%" preserveAspectRatio="none" aria-hidden="true">
        {/* baseline */}
        <line x1="0" y1={VIEW_H / 2} x2={VIEW_W} y2={VIEW_H / 2} stroke="rgba(245,239,227,0.12)" strokeWidth="1" />

        {/* energy bars */}
        {bars.map(i => {
          const e = energyAt(i);
          const h = e * (VIEW_H * 0.42);
          const x = i * barW + barW * 0.5;
          // bars near the scrub playhead lift slightly
          let lift = 1;
          if (scrub !== null) {
            const dist = Math.abs(i / (BAR_COUNT - 1) - scrub);
            lift = 1 + Math.max(0, 0.6 - dist * 8) * 0.6;
          }
          const hh = h * lift;
          // colour: bars within 2 indices of a snapped drop bar are orange
          const nearDrop = DROP_BARS.some(db => Math.abs(i - db) <= 2);
          return (
            <rect
              key={i}
              x={r3(x - barW * 0.28)}
              y={r3(VIEW_H / 2 - hh)}
              width={r3(barW * 0.56)}
              height={r3(hh * 2)}
              rx={r3(barW * 0.28)}
              fill={nearDrop ? 'var(--orange)' : 'rgba(245,239,227,0.34)'}
              style={{ transition: 'height 160ms var(--ease-drop), y 160ms var(--ease-drop)' }}
            />
          );
        })}

        {/* drop markers — fixed cx/cy on the snapped drop bar; pulse animates
            r + opacity only (never transform), so position stays locked. */}
        {DROP_BARS.map((db, i) => (
          <g key={i}>
            <circle cx={barCenterX(db)} cy={VIEW_H / 2} r="6" fill="var(--orange)" className="set-timeline-drop" style={{ animationDelay: `${i * 0.5}s` }} />
            <circle cx={barCenterX(db)} cy={VIEW_H / 2} r="10" fill="none" stroke="var(--orange)" strokeWidth="1" className="set-timeline-drop-ring" style={{ animationDelay: `${i * 0.5}s` }} />
          </g>
        ))}

        {/* scrub playhead */}
        {scrub !== null && (
          <line
            x1={scrub * VIEW_W}
            y1="6"
            x2={scrub * VIEW_W}
            y2={VIEW_H - 6}
            stroke="var(--creme)"
            strokeWidth="1.5"
            opacity="0.8"
          />
        )}
      </svg>

      {/* time labels (mono) */}
      <div className="flex justify-between mt-2 px-0.5">
        <span className="mono-label">00:00</span>
        <span className="mono-label">drops detected: {DROPS.length}</span>
        <span className="mono-label">03:00:00</span>
      </div>

      <style jsx>{`
        /* Animate opacity only (universally animatable) — cx/cy/r stay fixed,
           so markers never drift from their drop bar. */
        .set-timeline-drop {
          animation: stDot 2.4s var(--ease-drop) infinite;
        }
        .set-timeline-drop-ring {
          animation: stRing 2.4s var(--ease-drop) infinite;
        }
        @keyframes stDot {
          0%, 100% { opacity: 0.85; }
          50%      { opacity: 1; }
        }
        @keyframes stRing {
          0%, 100% { opacity: 0.5; }
          50%      { opacity: 0.12; }
        }
        @media (prefers-reduced-motion: reduce) {
          .set-timeline-drop,
          .set-timeline-drop-ring {
            animation: none;
          }
        }
      `}</style>
    </div>
  );
}
