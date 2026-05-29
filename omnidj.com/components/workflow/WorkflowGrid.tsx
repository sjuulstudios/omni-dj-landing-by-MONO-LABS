'use client';

import React, { useState } from 'react';
import Reveal from '@/components/ui/Reveal';
import { workflowContent } from '@/lib/content/workflow';

/** Optional per-step hover video. Drop real 4s captures here when available. */
const HOVER_VIDEOS: Record<string, string | undefined> = {
  Analyse: undefined,      // e.g. '/videos/workflow/analyse.mp4'
  Edit: undefined,         // e.g. '/videos/workflow/edit.mp4'
  'Auto-schedule': undefined
};

export default function WorkflowGrid() {
  return (
    <section className="section bg-black section-bridge">
      <div className="page-shell">
        <Reveal><h2 className="headline-section text-creme max-w-[680px]">{workflowContent.headline}</h2></Reveal>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          {workflowContent.steps.map((s, i) => (
            <Reveal key={s.title} delay={i * 120}>
              <WorkflowCard step={s} index={i} />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function WorkflowCard({ step, index }: { step: typeof workflowContent.steps[number]; index: number }) {
  const [hover, setHover] = useState(false);
  const video = HOVER_VIDEOS[step.title];

  return (
    <div
      className="h-full rounded-3xl overflow-hidden"
      style={{ background: 'var(--ink-900)', border: '1px solid var(--creme-line)' }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {/* Visual: diagrammatic SVG now, crossfades to hover video when provided */}
      <div
        className="relative"
        style={{ aspectRatio: '16 / 9', borderBottom: '1px solid var(--creme-line)', background: 'var(--ink-800)' }}
      >
        <div style={{ position: 'absolute', inset: 0, opacity: video && hover ? 0 : 1, transition: 'opacity 400ms var(--ease-drop)' }}>
          <WorkflowDiagram kind={step.title} active={hover} />
        </div>
        {video && (
          <video
            src={video}
            muted
            loop
            playsInline
            autoPlay
            aria-hidden="true"
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              opacity: hover ? 1 : 0,
              transition: 'opacity 400ms var(--ease-drop)'
            }}
          />
        )}
      </div>

      <div className="p-7">
        <div className="flex items-center gap-3 mb-3">
          <span
            className="block w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-medium font-mono"
            style={{
              background: 'var(--orange)',
              color: 'var(--ink)',
              transform: hover ? 'scale(1.08)' : 'scale(1)',
              transition: 'transform 300ms var(--ease-overshoot)'
            }}
          >
            {index + 1}
          </span>
          <h3 className="headline-h3 text-creme">{step.title}</h3>
        </div>
        <p className="text-creme-mute text-[15px] leading-[1.55]">{step.body}</p>

        <div className="mt-5 flex flex-wrap gap-2">
          {step.pills.map(p => (
            <span
              key={p}
              className="text-[12px] font-medium px-3 py-1 rounded-full"
              style={{
                background: 'rgba(245,239,227,0.06)',
                color: 'var(--creme)',
                border: '1px solid var(--creme-line)'
              }}
            >
              {p}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

/** Diagrammatic placeholder per step — lifts on hover. Replaced by real screenshots later. */
function WorkflowDiagram({ kind, active }: { kind: string; active: boolean }) {
  const stroke = 'rgba(245,239,227,0.5)';
  const accent = 'var(--orange)';
  const t = { transition: 'all 400ms var(--ease-drop)' };

  return (
    <svg viewBox="0 0 320 180" width="100%" height="100%" fill="none" aria-hidden="true">
      {kind === 'Analyse' && (
        <>
          {/* waveform with a highlighted drop */}
          {Array.from({ length: 28 }, (_, i) => {
            const x = 24 + i * 10;
            const base = 18 + Math.abs(Math.sin(i * 0.7)) * 22 + (i === 12 || i === 20 ? 40 : 0);
            const h = active ? base * 1.12 : base;
            const hot = i === 12 || i === 20;
            return <rect key={i} x={x} y={90 - h / 2} width="4" height={h} rx="2" fill={hot ? accent : stroke} style={t} />;
          })}
          <line x1="0" y1="90" x2="320" y2="90" stroke="rgba(245,239,227,0.14)" />
        </>
      )}
      {kind === 'Edit' && (
        <>
          {/* a clip frame + aspect rail + caption bar */}
          <rect x="40" y="36" width="120" height="108" rx="8" stroke={stroke} strokeWidth="1.5" />
          <rect x="52" y="118" width="96" height="14" rx="4" fill={accent} opacity={active ? 1 : 0.7} style={t} />
          {[0, 1, 2].map(i => (
            <rect key={i} x={190} y={44 + i * 36} width={active ? 90 : 80} height="24" rx="5" stroke={i === 0 ? accent : stroke} strokeWidth="1.5" style={t} />
          ))}
        </>
      )}
      {kind === 'Auto-schedule' && (
        <>
          {/* calendar grid with active slots */}
          {Array.from({ length: 21 }, (_, i) => {
            const col = i % 7;
            const row = Math.floor(i / 7);
            const x = 40 + col * 36;
            const y = 40 + row * 36;
            const slot = i === 4 || i === 10 || i === 16;
            return <rect key={i} x={x} y={y} width="26" height="26" rx="5" fill={slot ? accent : 'none'} opacity={slot && active ? 1 : slot ? 0.7 : 1} stroke={slot ? 'none' : stroke} strokeWidth="1.2" style={t} />;
          })}
        </>
      )}
    </svg>
  );
}
