'use client';

import React from 'react';

/**
 * FeatureWireframe — lightweight CSS/SVG wireframe animation per feature row.
 * Plays when `active` (the accordion row is open); loops subtly while open.
 * Replaced by real 6s screencasts later (same slot).
 *
 * kinds (in content order): Analyse, Library, Brand, Social, Calendar, Insights.
 */
export default function FeatureWireframe({ kind, active }: { kind: string; active: boolean }) {
  return (
    <div
      className={`fw-wrap${active ? ' is-active' : ''}`}
      aria-hidden="true"
      style={{
        aspectRatio: '3 / 2',
        background: 'var(--ink-800)',
        border: '1px dashed var(--creme-line)',
        borderRadius: 12,
        overflow: 'hidden',
        position: 'relative'
      }}
    >
      <svg viewBox="0 0 300 200" width="100%" height="100%" fill="none" preserveAspectRatio="xMidYMid meet">
        {kind === 'Analyse' && <Analyse />}
        {kind === 'Library' && <Library />}
        {kind === 'Brand' && <Brand />}
        {kind === 'Social' && <Social />}
        {kind === 'Calendar' && <Calendar />}
        {kind === 'Insights' && <Insights />}
      </svg>

      <style jsx>{`
        .fw-wrap :global(.fw-anim) { animation-play-state: paused; }
        .fw-wrap.is-active :global(.fw-anim) { animation-play-state: running; }

        /* Analyse — waveform draws + drop markers pop */
        :global(.fw-wave) {
          stroke: rgba(245, 239, 227, 0.55);
          stroke-width: 2;
          fill: none;
          stroke-dasharray: 520;
          stroke-dashoffset: 520;
          animation: fwDraw 2.4s var(--ease-drop) infinite alternate;
        }
        :global(.fw-drop) {
          fill: var(--orange);
          transform-box: fill-box;
          transform-origin: center;
          opacity: 0;
          animation: fwDropIn 2.4s var(--ease-drop) infinite;
        }
        @keyframes fwDraw { to { stroke-dashoffset: 0; } }
        @keyframes fwDropIn {
          0%, 40% { opacity: 0; transform: scale(0.4); }
          55% { opacity: 1; transform: scale(1.3); }
          70%, 100% { opacity: 1; transform: scale(1); }
        }

        /* Library — grid tiles stagger in */
        :global(.fw-tile) {
          fill: rgba(245, 239, 227, 0.14);
          opacity: 0;
          animation: fwTileIn 2.8s var(--ease-drop) infinite;
        }
        @keyframes fwTileIn {
          0%, 10% { opacity: 0; transform: translateY(6px); }
          30% { opacity: 1; transform: translateY(0); }
          90% { opacity: 1; }
          100% { opacity: 0; }
        }

        /* Brand — connector line draws, frame gets accent border */
        :global(.fw-brand-line) {
          stroke: var(--orange);
          stroke-width: 2;
          stroke-dasharray: 120;
          stroke-dashoffset: 120;
          animation: fwDraw 2.6s var(--ease-drop) infinite;
        }
        :global(.fw-brand-frame) {
          stroke: rgba(245, 239, 227, 0.4);
          stroke-width: 2;
          fill: none;
          animation: fwBrandBorder 2.6s var(--ease-drop) infinite;
        }
        @keyframes fwBrandBorder {
          0%, 50% { stroke: rgba(245, 239, 227, 0.4); }
          70%, 100% { stroke: var(--orange); }
        }

        /* Social — thumb travels along line to each platform */
        :global(.fw-thumb) {
          fill: var(--orange);
          animation: fwTravel 3s var(--ease-drop) infinite;
        }
        @keyframes fwTravel {
          0% { transform: translateX(0); }
          33% { transform: translateX(70px); }
          66% { transform: translateX(140px); }
          100% { transform: translateX(0); }
        }

        /* Calendar — dots pop on a few days */
        :global(.fw-cal-dot) {
          fill: var(--orange);
          opacity: 0;
          animation: fwDropIn 2.8s var(--ease-drop) infinite;
        }

        /* Insights — line graph builds up */
        :global(.fw-graph) {
          stroke: var(--orange);
          stroke-width: 2.5;
          fill: none;
          stroke-dasharray: 300;
          stroke-dashoffset: 300;
          animation: fwDraw 2.6s var(--ease-drop) infinite;
        }

        @media (prefers-reduced-motion: reduce) {
          :global(.fw-wave), :global(.fw-drop), :global(.fw-tile),
          :global(.fw-brand-line), :global(.fw-brand-frame), :global(.fw-thumb),
          :global(.fw-cal-dot), :global(.fw-graph) {
            animation: none !important;
            opacity: 1 !important;
            stroke-dashoffset: 0 !important;
          }
        }
      `}</style>
    </div>
  );
}

function Analyse() {
  return (
    <g className="fw-anim">
      <line x1="20" y1="100" x2="280" y2="100" stroke="rgba(245,239,227,0.12)" />
      <path className="fw-wave fw-anim" d="M20 100 Q50 60 70 100 T120 100 Q140 30 160 100 T210 100 Q230 50 250 100 T280 100" />
      <circle className="fw-drop fw-anim" cx="135" cy="100" r="6" style={{ animationDelay: '0.2s' }} />
      <circle className="fw-drop fw-anim" cx="225" cy="100" r="6" style={{ animationDelay: '0.6s' }} />
    </g>
  );
}

function Library() {
  const tiles = [];
  let n = 0;
  for (let r = 0; r < 2; r++) {
    for (let c = 0; c < 4; c++) {
      tiles.push(
        <rect
          key={`${r}-${c}`}
          className="fw-tile fw-anim"
          x={28 + c * 64}
          y={44 + r * 64}
          width="48"
          height="52"
          rx="5"
          style={{ animationDelay: `${n * 0.12}s`, transformBox: 'fill-box', transformOrigin: 'center' } as React.CSSProperties}
        />
      );
      n++;
    }
  }
  return <g className="fw-anim">{tiles}</g>;
}

function Brand() {
  return (
    <g className="fw-anim">
      {/* logo swatch */}
      <rect x="30" y="80" width="40" height="40" rx="6" fill="var(--orange)" opacity="0.85" />
      {/* accent swatch */}
      <rect x="30" y="128" width="40" height="14" rx="4" fill="rgba(245,239,227,0.4)" />
      {/* connector to frame */}
      <path className="fw-brand-line fw-anim" d="M74 100 H 150" />
      {/* clip frame gaining accent border */}
      <rect className="fw-brand-frame fw-anim" x="160" y="56" width="110" height="88" rx="8" />
    </g>
  );
}

function Social() {
  return (
    <g className="fw-anim">
      <line x1="50" y1="100" x2="250" y2="100" stroke="rgba(245,239,227,0.18)" />
      {[60, 130, 200].map((x, i) => (
        <circle key={i} cx={x} cy="100" r="16" fill="none" stroke="rgba(245,239,227,0.4)" strokeWidth="2" />
      ))}
      <rect className="fw-thumb fw-anim" x="48" y="60" width="24" height="30" rx="4" />
    </g>
  );
}

function Calendar() {
  const cells = [];
  let n = 0;
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 5; c++) {
      const x = 50 + c * 42;
      const y = 48 + r * 38;
      const slot = n === 3 || n === 7 || n === 11;
      cells.push(
        <g key={n}>
          <rect x={x} y={y} width="30" height="28" rx="4" fill="none" stroke="rgba(245,239,227,0.2)" strokeWidth="1.2" />
          {slot && <circle className="fw-cal-dot fw-anim" cx={x + 15} cy={y + 14} r="5" style={{ animationDelay: `${n * 0.15}s` }} />}
        </g>
      );
      n++;
    }
  }
  return <g className="fw-anim">{cells}</g>;
}

function Insights() {
  return (
    <g className="fw-anim">
      <line x1="40" y1="160" x2="270" y2="160" stroke="rgba(245,239,227,0.18)" />
      <line x1="40" y1="40" x2="40" y2="160" stroke="rgba(245,239,227,0.18)" />
      <path className="fw-graph fw-anim" d="M40 150 L 90 130 L 140 138 L 190 90 L 240 56" />
      {[[90, 130], [140, 138], [190, 90], [240, 56]].map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="3.5" fill="var(--orange)" />
      ))}
    </g>
  );
}
