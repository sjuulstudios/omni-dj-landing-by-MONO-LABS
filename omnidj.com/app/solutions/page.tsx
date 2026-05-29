import type { Metadata } from 'next';
import Link from 'next/link';
import { enterpriseContent } from '@/lib/content/enterprise';

export const metadata: Metadata = {
  title: 'Solutions — Omni DJ',
  description: 'Solutions for DJs, videographers, talent managers, event organisers, festival organisers and record labels.'
};

export default function SolutionsPage() {
  return (
    <>
      <section className="pt-40 pb-16 bg-black">
        <div className="page-shell">
          <div className="max-w-[760px]">
            <div className="eyebrow text-creme-mute mb-5">Solutions</div>
            <h1 className="headline-section text-creme">Pick your role. We will pick the workflow.</h1>
            <p className="mt-6 body-lg text-creme-mute">
              Omni DJ adapts to the team behind the music. Five audiences, five workflows, one tool.
            </p>
          </div>
        </div>
      </section>

      <section className="pb-24 bg-black">
        <div className="page-shell">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {enterpriseContent.tabs.map(t => (
              <div
                key={t.id}
                id={t.id}
                className="p-8 rounded-3xl scroll-mt-32"
                style={{ background: 'var(--ink-900)', border: '1px solid var(--creme-line)' }}
              >
                <div className="eyebrow text-creme-mute mb-3">{t.label}</div>
                <h2 className="headline-h3 text-creme">{t.headline}</h2>
                <p className="mt-4 body-default text-creme-mute">{t.body}</p>
                <div className="mt-6">
                  <Link href="/contact" className="text-[14px] font-medium" style={{ color: 'var(--orange)' }}>
                    Talk to sales →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
