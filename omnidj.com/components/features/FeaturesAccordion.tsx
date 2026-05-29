'use client';

import React, { useState } from 'react';
import Reveal from '@/components/ui/Reveal';
import FeatureWireframe from '@/components/features/FeatureWireframe';
import { featuresContent } from '@/lib/content/features';

/**
 * Compact features section — fits in one viewport (~900px).
 * Multi-open accordion: any rows can be open simultaneously.
 */
export default function FeaturesAccordion() {
  // Single-open accordion: opening one row auto-closes the previous one.
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggle = (i: number) => {
    setOpenIndex(prev => (prev === i ? null : i));
  };

  return (
    <section className="bg-black" style={{ padding: '80px 0' }}>
      <div className="page-shell">
        <Reveal>
          <h2
            className="text-creme font-bold tracking-tight"
            style={{
              fontSize: 'clamp(28px, 3.4vw, 48px)',
              lineHeight: 1.05,
              letterSpacing: '-0.025em',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            {featuresContent.headline}
          </h2>
        </Reveal>

        <div className="mt-8 border-t border-creme-line">
          {featuresContent.items.map((item, i) => {
            const isOpen = openIndex === i;
            return (
              <div key={item.title} className="border-b border-creme-line">
                <button
                  onClick={() => toggle(i)}
                  className="w-full flex items-center justify-between gap-6 py-4 text-left transition-colors hover:bg-white/[0.02]"
                  aria-expanded={isOpen}
                >
                  <span
                    className="text-creme tracking-tight font-medium"
                    style={{ fontSize: 'clamp(20px, 2.2vw, 28px)' }}
                  >
                    {item.title}
                  </span>
                  <span
                    aria-hidden="true"
                    className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center border border-creme-line transition-transform"
                    style={{
                      transform: isOpen ? 'rotate(45deg)' : 'rotate(0)',
                      color: 'var(--creme)'
                    }}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12h14" /></svg>
                  </span>
                </button>

                <div
                  className="overflow-hidden transition-all"
                  style={{
                    maxHeight: isOpen ? 300 : 0,
                    opacity: isOpen ? 1 : 0,
                    transitionDuration: '420ms',
                    transitionTimingFunction: 'var(--ease-drop)'
                  }}
                >
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pb-5">
                    <p className="lg:col-span-7 text-[14px] leading-[1.55] text-creme-mute max-w-[600px]">{item.body}</p>
                    <div className="lg:col-span-5 lg:col-start-8">
                      <FeatureWireframe kind={item.title} active={isOpen} />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
