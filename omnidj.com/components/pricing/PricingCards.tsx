'use client';

import React from 'react';
import Link from 'next/link';
import type { Tier } from '@/lib/content/pricing';

function priceLine(t: Tier, billing: 'monthly' | 'yearly') {
  const p = billing === 'monthly' ? t.monthly : t.yearly;
  if (p.eur === 'custom') return { eur: 'Custom', usd: '' };
  const eur = `€${typeof p.eur === 'number' ? p.eur.toFixed(p.eur % 1 === 0 ? 0 : 2) : p.eur}`;
  const usd = `$${typeof p.usd === 'number' ? p.usd.toFixed(p.usd % 1 === 0 ? 0 : 0) : p.usd}`;
  return { eur, usd };
}

export default function PricingCards({
  tiers,
  billing
}: {
  tiers: Tier[];
  billing: 'monthly' | 'yearly';
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {tiers.map(t => {
        const { eur, usd } = priceLine(t, billing);
        const isCustom = t.monthly.eur === 'custom';
        return (
          <div
            key={t.id}
            className={`flex flex-col rounded-3xl p-7 relative${t.highlight ? ' pricing-pro' : ''}`}
            style={{
              background: t.highlight ? 'var(--creme)' : 'var(--ink-900)',
              color: t.highlight ? 'var(--ink)' : 'var(--creme)',
              border: t.highlight
                ? '1px solid rgba(10,10,10,0.12)'
                : '1px solid var(--creme-line)',
              // Lift the recommended tier so it reads as a recommendation, not a label.
              transform: t.highlight ? 'translateY(-8px)' : undefined,
              boxShadow: t.highlight
                ? '0 24px 48px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04)'
                : undefined,
              zIndex: t.highlight ? 2 : 1
            }}
          >
            {t.highlight && (
              <>
                {/* Breathing orange ring around the recommended tier. */}
                <span
                  aria-hidden="true"
                  className="pricing-pro-ring"
                  style={{
                    position: 'absolute',
                    inset: -1,
                    borderRadius: 24,
                    border: '1px solid var(--orange)',
                    pointerEvents: 'none'
                  }}
                />
                <div
                  className="absolute -top-3 left-7 px-3 py-1 rounded-full text-[11px] font-medium tracking-[0.08em] uppercase"
                  style={{ background: 'var(--orange)', color: 'var(--ink)', zIndex: 1 }}
                >
                  Most popular
                </div>
              </>
            )}

            <div className="text-[24px] font-medium tracking-tight">{t.name}</div>
            <div
              className="text-[12px] mt-1"
              style={{ color: t.highlight ? 'rgba(10,10,10,0.55)' : 'var(--creme-mute)' }}
            >
              {t.forWho}
            </div>

            <div className="mt-6">
              {isCustom ? (
                <div>
                  <div className="text-[40px] font-bold leading-none tracking-tight">Custom</div>
                  <div
                    className="text-[12px] mt-2"
                    style={{ color: t.highlight ? 'rgba(10,10,10,0.55)' : 'var(--creme-mute)' }}
                  >
                    Tailored to your team
                  </div>
                </div>
              ) : (
                <div>
                  <div className="flex items-baseline gap-3 flex-wrap">
                    <div className="text-[40px] font-bold leading-none tracking-tight">{eur}</div>
                    <div className="text-[18px] opacity-60 font-mono">{usd}</div>
                  </div>
                  <div
                    className="text-[12px] mt-2 font-mono"
                    style={{ color: t.highlight ? 'rgba(10,10,10,0.55)' : 'var(--creme-mute)' }}
                  >
                    {t.monthly.eur === 0 ? 'Forever' : `per month${billing === 'yearly' ? ', billed yearly' : ''}`}
                  </div>
                </div>
              )}
            </div>

            <Link
              href={t.cta.href}
              className={`mt-6 btn ${t.highlight ? 'btn-orange' : 'btn-creme'} w-full`}
              style={{ width: '100%' }}
            >
              {t.cta.label}
            </Link>

            <ul className="mt-7 space-y-3 flex-1">
              {t.features.map((f, i) => (
                <li key={i} className="flex items-start gap-3 text-[14px]">
                  <span
                    aria-hidden="true"
                    className="mt-[3px] flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center"
                    style={{
                      background: f.included
                        ? t.highlight
                          ? 'var(--orange)'
                          : 'rgba(255,106,26,0.16)'
                        : 'rgba(245,239,227,0.06)',
                      color: f.included
                        ? t.highlight ? 'var(--ink)' : 'var(--orange)'
                        : t.highlight ? 'rgba(10,10,10,0.4)' : 'var(--creme-mute)'
                    }}
                  >
                    {f.included ? (
                      <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                    ) : (
                      <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M6 12h12" /></svg>
                    )}
                  </span>
                  <span style={{ color: f.included ? 'inherit' : t.highlight ? 'rgba(10,10,10,0.4)' : 'var(--creme-mute)' }}>
                    {f.label}
                    {f.soon && (
                      <span
                        className="ml-2 text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                        style={{
                          background: t.highlight ? 'rgba(10,10,10,0.06)' : 'rgba(245,239,227,0.06)',
                          color: t.highlight ? 'rgba(10,10,10,0.55)' : 'var(--creme-mute)'
                        }}
                      >
                        soon
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
