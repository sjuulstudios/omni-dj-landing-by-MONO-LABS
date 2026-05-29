import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Resources — Omni DJ',
  description: 'Knowledge center, changelog and roadmap for Omni DJ.'
};

const tiles = [
  {
    title: 'Knowledge Center',
    body: 'How-tos, troubleshooting and product walkthroughs.',
    href: '#',
    badge: 'soon'
  },
  {
    title: 'Roadmap',
    body: "What's shipped, what's next, what we are building.",
    href: '/#roadmap'
  },
  {
    title: 'For business',
    body: 'Multi-artist, batch and Auto-mode for talent teams and labels.',
    href: '/for-business'
  },
  {
    title: 'Contact sales',
    body: 'Book a 20-minute call. Bring your release schedule.',
    href: '/contact'
  }
];

export default function ResourcesPage() {
  return (
    <section className="pt-40 pb-24 bg-black">
      <div className="page-shell">
        <div className="max-w-[760px]">
          <div className="eyebrow text-creme-mute mb-5">Resources</div>
          <h1 className="headline-section text-creme">Everything around Omni DJ.</h1>
          <p className="mt-6 body-lg text-creme-mute">
            Reference docs, the roadmap, and a direct line to the team.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-5">
          {tiles.map(t => (
            <Link
              key={t.title}
              href={t.href}
              className="p-7 rounded-3xl block group transition-colors"
              style={{ background: 'var(--ink-900)', border: '1px solid var(--creme-line)' }}
            >
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-creme font-medium text-[22px] tracking-tight">{t.title}</h2>
                    {t.badge && (
                      <span
                        className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                        style={{ background: 'rgba(255,106,26,0.16)', color: 'var(--orange)' }}
                      >
                        {t.badge}
                      </span>
                    )}
                  </div>
                  <p className="mt-3 text-creme-mute text-[14px]">{t.body}</p>
                </div>
                <span
                  className="flex-shrink-0 w-10 h-10 rounded-full border border-creme-line flex items-center justify-center text-creme transition-all group-hover:border-creme group-hover:translate-x-1"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M13 5l7 7-7 7" /></svg>
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
