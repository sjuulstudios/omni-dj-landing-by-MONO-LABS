'use client';

import React, { useState } from 'react';
import type { Metadata } from 'next';
import PricingCards from '@/components/pricing/PricingCards';
import PricingMatrix from '@/components/pricing/PricingMatrix';
import BillingToggle from '@/components/pricing/BillingToggle';
import Reveal from '@/components/ui/Reveal';
import { pricingContent } from '@/lib/content/pricing';

export default function PricingPage() {
  const [billing, setBilling] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <>
      <section className="pt-40 pb-20 bg-black">
        <div className="page-shell text-center">
          <Reveal><h1 className="headline-section text-creme">{pricingContent.headline}</h1></Reveal>
          <Reveal delay={120}><p className="mt-4 body-lg text-creme-mute max-w-[620px] mx-auto">{pricingContent.subline}</p></Reveal>
          <Reveal delay={200}>
            <div className="mt-10 flex justify-center">
              <BillingToggle value={billing} onChange={setBilling} />
            </div>
          </Reveal>
          <Reveal delay={280}>
            <div className="mt-3 text-[12px] text-creme-mute">EUR shown first, USD shown alongside</div>
          </Reveal>
        </div>
      </section>

      <section className="pb-24 bg-black">
        <div className="page-shell">
          <PricingCards tiers={pricingContent.tiers} billing={billing} />
        </div>
      </section>

      <section className="py-24 bg-black">
        <div className="page-shell">
          <div className="mb-10">
            <h2 className="headline-h3 text-creme">Compare every feature</h2>
            <p className="mt-2 body-default text-creme-mute">All numbers reflect monthly billing unless marked yearly.</p>
          </div>
          <PricingMatrix groups={pricingContent.matrix.groups} />
        </div>
      </section>
    </>
  );
}
