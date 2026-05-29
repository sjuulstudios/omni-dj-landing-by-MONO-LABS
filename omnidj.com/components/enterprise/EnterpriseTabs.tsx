'use client';

import React, { useState } from 'react';
import Reveal from '@/components/ui/Reveal';
import { enterpriseContent } from '@/lib/content/enterprise';

function FeatureIcon({ kind }: { kind: string }) {
  const common = { width: 22, height: 22, viewBox: '0 0 24 24', fill: 'none' as const, stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  switch (kind) {
    case 'workspaces': return <svg {...common}><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>;
    case 'auto': return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>;
    case 'watch': return <svg {...common}><path d="M3 7h5l2 3h11v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" /><circle cx="14" cy="15" r="2" /></svg>;
    case 'batch': return <svg {...common}><path d="M4 5h16M4 12h16M4 19h10" /></svg>;
    case 'multi': return <svg {...common}><circle cx="9" cy="9" r="3.5" /><circle cx="16" cy="14" r="3.5" /><path d="M3 21c0-3 3-5 6-5M14 21c2 0 6-1.5 6-5" /></svg>;
    case 'wave': return <svg {...common}><path d="M3 12h2l2-7 3 14 3-10 2 7 2-5 2 3h2" /></svg>;
    case 'rail': return <svg {...common}><rect x="3" y="4" width="6" height="16" rx="1" /><rect x="11" y="6" width="6" height="12" rx="1" /><rect x="19" y="9" width="2.5" height="6" rx="0.5" /></svg>;
    case 'caption': return <svg {...common}><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M7 14h2M11 14h6M7 10h10" /></svg>;
    case 'calendar': return <svg {...common}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>;
    case 'shield': return <svg {...common}><path d="M12 3l8 4v5a9 9 0 0 1-8 9 9 9 0 0 1-8-9V7z" /><path d="M9 12l2 2 4-4" /></svg>;
    case 'palette': return <svg {...common}><path d="M12 2a10 10 0 0 0 0 20 4 4 0 0 0 4-4 2 2 0 0 1 2-2h2a4 4 0 0 0 4-4 10 10 0 0 0-12-10z" /></svg>;
    case 'camera': return <svg {...common}><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" /><circle cx="12" cy="13" r="4" /></svg>;
    case 'chart': return <svg {...common}><path d="M3 20h18" /><path d="M6 16v-4M11 16V8M16 16v-6M21 16V6" /></svg>;
    default: return null;
  }
}

export default function EnterpriseTabs() {
  const [active, setActive] = useState(enterpriseContent.tabs[0].id);
  const tab = enterpriseContent.tabs.find(t => t.id === active)!;

  return (
    <section className="section section-creme">
      <div className="page-shell">
        <Reveal><h2 className="headline-section">{enterpriseContent.headline}</h2></Reveal>
        <Reveal delay={120}><p className="mt-4 body-lg max-w-[640px]">{enterpriseContent.subline}</p></Reveal>

        {/* Tab bar */}
        <div
          className="mt-14 flex flex-wrap gap-1 border-b overflow-x-auto no-scrollbar"
          style={{ borderColor: 'rgba(10,10,10,0.12)' }}
          role="tablist"
        >
          {enterpriseContent.tabs.map(t => {
            const isActive = t.id === active;
            return (
              <button
                key={t.id}
                role="tab"
                aria-selected={isActive}
                onClick={() => setActive(t.id)}
                className="relative px-5 py-4 text-[15px] font-medium transition-colors flex-shrink-0"
                style={{ color: isActive ? '#0A0A0A' : 'rgba(10,10,10,0.55)' }}
              >
                {t.label}
                <span
                  className="absolute left-0 right-0 -bottom-px h-[2px] transition-all"
                  style={{
                    background: 'var(--orange)',
                    transform: isActive ? 'scaleX(1)' : 'scaleX(0)',
                    transformOrigin: 'left'
                  }}
                />
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        <div key={tab.id} className="mt-12 grid grid-cols-1 lg:grid-cols-12 gap-12">
          <div className="lg:col-span-5">
            <h3 className="headline-h3" style={{ color: '#0A0A0A' }}>{tab.headline}</h3>
            <p className="mt-5 body-lg">{tab.body}</p>

            {/* Aspirational stat ticker — in-card, under the description */}
            <div
              className="mt-6 inline-flex items-center gap-2 px-3.5 py-2 rounded-full"
              style={{ background: 'rgba(255,106,26,0.10)', border: '1px solid rgba(255,106,26,0.3)' }}
            >
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--orange)' }} aria-hidden="true" />
              <span className="font-mono text-[13px]" style={{ color: '#0A0A0A' }}>{tab.stat}</span>
            </div>

            <div className="mt-6">
              <a
                href={`/solutions${tab.anchor}`}
                className="inline-flex items-center gap-1.5 text-[14px] font-medium group"
                style={{ color: '#0A0A0A' }}
              >
                See more for {tab.label.toLowerCase()}
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ transition: 'transform 240ms var(--ease-drop)' }} className="group-hover:translate-x-1">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </a>
            </div>
          </div>
          <div className="lg:col-span-7">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {tab.features.map((f, i) => (
                <div
                  key={f.title}
                  className="p-5 rounded-2xl relative"
                  style={{
                    background: 'rgba(10,10,10,0.04)',
                    border: '1px solid rgba(10,10,10,0.08)',
                    animation: `fadeInUp 500ms var(--ease-drop) ${i * 70}ms both`,
                    opacity: f.soon ? 0.65 : 1
                  }}
                >
                  <div style={{ color: 'var(--orange)' }}><FeatureIcon kind={f.icon} /></div>
                  <div className="mt-4 flex items-center gap-2">
                    <div className="font-medium" style={{ color: '#0A0A0A' }}>{f.title}</div>
                    {f.soon && (
                      <span
                        className="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                        style={{ background: 'rgba(255,106,26,0.16)', color: 'var(--orange)' }}
                      >
                        soon
                      </span>
                    )}
                  </div>
                  <div className="mt-2 text-[14px]" style={{ color: 'rgba(10,10,10,0.62)' }}>{f.body}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <style jsx>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </section>
  );
}
