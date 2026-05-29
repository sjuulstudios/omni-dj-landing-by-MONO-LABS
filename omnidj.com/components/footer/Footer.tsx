'use client';

import React from 'react';
import Link from 'next/link';
import OmniMark from '@/components/logo/OmniMark';
import { footerColumns, footerSocials } from '@/lib/content/footer';

function SocialIcon({ name }: { name: string }) {
  const c = 'currentColor';
  const common = { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none' as const, stroke: c, strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  switch (name) {
    case 'instagram':
      return (
        <svg {...common}><rect x="3" y="3" width="18" height="18" rx="5" /><circle cx="12" cy="12" r="4" /><circle cx="17.5" cy="6.5" r="0.6" fill={c} /></svg>
      );
    case 'tiktok':
      return (
        <svg {...common}><path d="M14 4v9a4 4 0 1 1-4-4" /><path d="M14 4c0 2.2 1.8 4 4 4" /></svg>
      );
    case 'youtube':
      return (
        <svg {...common}><rect x="2.5" y="6" width="19" height="12" rx="3" /><path d="M10.5 9.5v5l4-2.5z" fill={c} stroke="none" /></svg>
      );
    case 'linkedin':
      return (
        <svg {...common}><rect x="3" y="3" width="18" height="18" rx="3" /><path d="M8 10v7" /><path d="M8 7v.01" /><path d="M12 17v-4a2 2 0 1 1 4 0v4" /><path d="M12 17v-7" /></svg>
      );
    case 'facebook':
      return (
        <svg {...common}><path d="M14 8h2V5h-2a3 3 0 0 0-3 3v2H9v3h2v6h3v-6h2.5l.5-3H14V8.5c0-.3.2-.5.5-.5z" /></svg>
      );
    default:
      return null;
  }
}

export default function Footer() {
  return (
    <footer className="bg-black pt-24 pb-10 mt-0">
      <div className="page-shell">
        {/* Top: brand mark + columns */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-12">
          {/* Brand col */}
          <div className="md:col-span-4">
            <Link href="/" className="flex items-center gap-3" aria-label="Omni DJ — home">
              <OmniMark size={36} />
              <div>
                <div className="text-creme font-medium text-[20px]">Omni DJ</div>
                <div className="text-[10px] tracking-[0.14em] uppercase text-creme-mute">by MONO LABS</div>
              </div>
            </Link>
            <p className="mt-6 text-creme-mute max-w-[280px] body-default">
              Turn your hours-long DJ-sets into scroll-stopping shorts. Locally on your machine.
            </p>
          </div>

          {/* Link columns */}
          <div className="md:col-span-6 grid grid-cols-2 md:grid-cols-4 gap-8">
            {footerColumns.map(col => (
              <div key={col.title}>
                <div className="eyebrow mb-4">{col.title}</div>
                <ul className="space-y-3">
                  {col.links.map(l => (
                    <li key={l.label}>
                      <Link
                        href={l.href}
                        className="text-creme hover:text-orange transition-colors text-[14px]"
                      >
                        {l.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Socials */}
          <div className="md:col-span-2 flex md:justify-end">
            <div>
              <div className="eyebrow mb-4">Follow</div>
              <div className="flex flex-wrap gap-3">
                {footerSocials.map(s => (
                  <Link
                    key={s.label}
                    href={s.href}
                    aria-label={s.label}
                    className="w-9 h-9 rounded-full border border-creme-line flex items-center justify-center text-creme hover:text-orange hover:border-orange transition-colors"
                  >
                    <SocialIcon name={s.icon} />
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom row */}
        <div className="mt-16 pt-8 border-t border-creme-line flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="text-[11px] tracking-[0.12em] uppercase text-creme-mute font-medium">
            OMNI DJ © {new Date().getFullYear()}. ALL RIGHTS RESERVED.
          </div>
          <div className="text-[11px] tracking-[0.12em] uppercase text-creme-mute font-medium">
            by MONO LABS
          </div>
        </div>
      </div>
    </footer>
  );
}
