import type { Metadata } from 'next';
import Link from 'next/link';
import Reveal from '@/components/ui/Reveal';
import { featuresContent } from '@/lib/content/features';
import { DOWNLOAD_URL } from '@/lib/config';

export const metadata: Metadata = {
  title: 'Features — Omni DJ',
  description: 'Analyse, Library, Brand, Social, Calendar, Insights. Everything inside Omni DJ.'
};

export default function FeaturesPage() {
  return (
    <>
      <section className="pt-40 pb-16 bg-black">
        <div className="page-shell">
          <div className="max-w-[760px]">
            <div className="eyebrow text-creme-mute mb-5">Features</div>
            <h1 className="headline-section text-creme">{featuresContent.headline}</h1>
            <p className="mt-6 body-lg text-creme-mute">
              Six modules, all locally on your machine. Click any one to jump in.
            </p>
          </div>
        </div>
      </section>

      <section className="pb-24 bg-black">
        <div className="page-shell space-y-4">
          {featuresContent.items.map((it, i) => (
            <Reveal key={it.title} delay={i * 60}>
              <div
                className="grid grid-cols-1 lg:grid-cols-12 gap-8 p-8 rounded-3xl"
                style={{ background: 'var(--ink-900)', border: '1px solid var(--creme-line)' }}
              >
                <div className="lg:col-span-5">
                  <div className="flex items-baseline gap-3">
                    <span
                      className="text-[12px] tracking-[0.16em] uppercase font-medium"
                      style={{ color: 'var(--orange)' }}
                    >
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <h2 className="text-creme font-medium text-[28px] tracking-tight">{it.title}</h2>
                  </div>
                  <p className="mt-4 body-default text-creme-mute">{it.body}</p>
                </div>
                <div className="lg:col-span-7">
                  <div className="placeholder-box rounded-2xl" style={{ aspectRatio: '16 / 9' }}>
                    <span>Screenshot — {it.title}</span>
                  </div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="section section-creme">
        <div className="page-shell text-center">
          <h2 className="headline-section">Try every feature, free.</h2>
          <div className="mt-8 flex justify-center gap-3 flex-wrap">
            <a href={DOWNLOAD_URL} className="btn btn-orange">Download Omni DJ</a>
            <Link href="/pricing" className="btn btn-outline-dark">See pricing</Link>
          </div>
        </div>
      </section>
    </>
  );
}
