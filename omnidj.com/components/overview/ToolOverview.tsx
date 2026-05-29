'use client';

import React from 'react';
import Reveal from '@/components/ui/Reveal';
import RemotionMp4 from '@/components/ui/RemotionMp4';

/**
 * Tool overview — premium Remotion MP4 (ToolOverviewFlow) showing the
 * three-hour set -> drops -> reframe -> shorts pipeline. Static CSS fallback
 * renders the end-state while the MP4 loads or if it is missing.
 */
export default function ToolOverview() {
  const fallback = (
    <div className="w-full h-full flex items-center justify-center" style={{ background: COLORS_INK }}>
      <div className="grid grid-cols-3 gap-3 w-full px-6">
        {['Your set', 'Reframe', 'Shorts ready'].map((t, i) => (
          <div key={t} className="rounded-2xl p-5" style={{ background: 'var(--ink-900)', border: '1px solid var(--creme-line)' }}>
            <div className="mono-label mb-2" style={{ color: i === 0 ? 'var(--orange)' : 'var(--creme-mute)' }}>
              {['ANALYSE', 'REFRAME', 'PUBLISH'][i]}
            </div>
            <div className="text-creme text-[14px] font-medium">{t}</div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <section className="section bg-black overflow-hidden">
      <div className="page-shell">
        <div className="max-w-[760px] mb-12">
          <Reveal>
            <h2 className="headline-section text-creme">
              From three-hour set to scroll-stopping shorts.
            </h2>
          </Reveal>
          <Reveal delay={120}>
            <p className="mt-5 body-lg text-creme-mute">
              Drop the file. Omni DJ analyses energy across the whole set, finds every drop and proposes vertical, square and landscape variants in one pass.
            </p>
          </Reveal>
        </div>

        <Reveal>
          <RemotionMp4
            src="/remotion/tool-flow.mp4"
            fallback={fallback}
            aspectRatio="16 / 6"
            className="rounded-3xl overflow-hidden"
            style={{ borderRadius: 24 }}
          />
        </Reveal>
      </div>
    </section>
  );
}

const COLORS_INK = '#000000';
