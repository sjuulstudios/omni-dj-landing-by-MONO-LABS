'use client';

import React from 'react';
import LogoReveal from '@/components/hero/LogoReveal';
import DropField from '@/components/hero/DropField';
import JoinBetaForm from '@/components/hero/JoinBetaForm';
import PillarCards from '@/components/hero/PillarCards';
import SetTimeline from '@/components/hero/SetTimeline';
import Reveal from '@/components/ui/Reveal';
import { heroContent } from '@/lib/content/hero';

export default function HomeHero() {
  return (
    <section className="relative pt-32 pb-20 bg-ink-900 overflow-hidden">
      {/* subtle background grain */}
      <div
        aria-hidden="true"
        className="absolute inset-0 opacity-[0.04] pointer-events-none"
        style={{
          backgroundImage:
            'radial-gradient(circle at 50% 0%, rgba(245,239,227,0.6) 0%, transparent 60%)'
        }}
      />
      <div className="page-shell relative">
        <div className="max-w-[820px] mx-auto text-center">
          {/* Eyebrow: small mark + wordmark + by MONO LABS */}
          <Reveal>
            <div className="inline-flex items-center gap-3 mb-8">
              <LogoReveal size={36} />
              <div className="flex items-baseline gap-2">
                <span className="text-creme font-medium text-[14px] tracking-tight">Omni DJ</span>
                <span className="text-[10px] tracking-[0.16em] uppercase text-creme-mute font-medium">
                  by MONO LABS
                </span>
              </div>
            </div>
          </Reveal>

          {/* Set-timeline strip — signature motif, sits above the headline */}
          <Reveal delay={60}>
            <div className="max-w-[680px] mx-auto mb-10" style={{ height: 96 }}>
              <SetTimeline />
            </div>
          </Reveal>

          {/* Headline */}
          <Reveal delay={120}>
            <h1 className="headline-hero text-creme">{heroContent.headline}</h1>
          </Reveal>

          {/* Subline — kept on a single line on desktop */}
          <Reveal delay={160}>
            <p className="mt-6 body-lg text-creme-mute mx-auto md:whitespace-nowrap">
              {heroContent.subline}
            </p>
          </Reveal>

          {/* CTAs: Download (solid, left) + Drop your DJ-set (transparent, right), beta below */}
          <Reveal delay={240}>
            <div className="mt-10 max-w-[560px] mx-auto" id="download">
              <div className="flex flex-col sm:flex-row gap-3">
                <a
                  href={heroContent.ctas.download.href}
                  className="btn btn-creme flex-1"
                >
                  {heroContent.ctas.download.label}
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M12 3v12M5 10l7 7 7-7M5 21h14" />
                  </svg>
                </a>
                <div className="flex-1">
                  <DropField label={heroContent.ctas.drop.label} hint={heroContent.ctas.drop.hint} />
                </div>
              </div>
              <div id="beta" className="mt-3">
                <JoinBetaForm placeholder={heroContent.ctas.beta.placeholder} label={heroContent.ctas.beta.label} />
              </div>
            </div>
          </Reveal>
        </div>

        {/* Pillar cards */}
        <div className="mt-24">
          <PillarCards />
        </div>
      </div>
    </section>
  );
}
