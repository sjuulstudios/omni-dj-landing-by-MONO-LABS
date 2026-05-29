'use client';

import React from 'react';
import Reveal from '@/components/ui/Reveal';
import { heroContent } from '@/lib/content/hero';

export default function PillarCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {heroContent.pillars.map((p, i) => (
        <Reveal key={p.title} delay={i * 80}>
          <div
            className="p-6 rounded-2xl h-full"
            style={{ background: 'var(--ink-900)', border: '1px solid var(--creme-line)' }}
          >
            <div className="flex items-center gap-3 mb-3">
              <span
                className="block rounded-full"
                style={{ width: 8, height: 8, background: 'var(--orange)' }}
                aria-hidden="true"
              />
              <h3 className="text-creme font-medium text-[16px] tracking-tight">{p.title}</h3>
            </div>
            <p className="text-creme-mute text-[14px] leading-[1.55]">{p.body}</p>
          </div>
        </Reveal>
      ))}
    </div>
  );
}
