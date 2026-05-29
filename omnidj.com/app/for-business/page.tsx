import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'For business — Omni DJ',
  description: 'Omni DJ at the roster level. Multi-artist workspaces, batch processing, Auto-mode and SSO.'
};

const valueProps = [
  {
    title: 'Multi-artist workspaces',
    body: 'Isolate brand kits, captions and history per artist or release. Switch identities in one click.'
  },
  {
    title: 'Batch processing',
    body: 'Queue a whole festival night and walk away. Find the slate ready in the morning.'
  },
  {
    title: 'Auto-mode pipeline',
    body: 'Six stages from watch-folder drop to scheduled post, with optional review gates per artist.'
  },
  {
    title: 'Insights at the roster level',
    body: 'See which clip and which drop pulled the engagement. Per artist, per platform.'
  },
  {
    title: 'SSO and SLA',
    body: 'Custom single sign-on, dedicated success manager and SLA-backed support on Studio+.'
  },
  {
    title: 'Local-first by default',
    body: 'Your sets, your file system. No upload queue, no cloud quota, no third-party processing.'
  }
];

export default function ForBusinessPage() {
  return (
    <>
      <section className="pt-40 pb-24 bg-black">
        <div className="page-shell">
          <div className="max-w-[760px]">
            <div className="eyebrow text-creme-mute mb-5">For business</div>
            <h1 className="headline-section text-creme">Built for the teams behind the music.</h1>
            <p className="mt-6 body-lg text-creme-mute">
              Talent managers, record labels, event organisers and festival teams use Omni DJ to keep every artist on the roster posting, without growing the headcount that has to make it happen.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link href="/contact" className="btn btn-orange">Talk to sales</Link>
              <Link href="/pricing" className="btn btn-outline">See pricing</Link>
            </div>
          </div>
        </div>
      </section>

      <section className="pb-24 bg-black">
        <div className="page-shell">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {valueProps.map(v => (
              <div
                key={v.title}
                className="p-7 rounded-2xl"
                style={{ background: 'var(--ink-900)', border: '1px solid var(--creme-line)' }}
              >
                <div className="text-creme font-medium text-[18px] tracking-tight">{v.title}</div>
                <p className="mt-3 text-creme-mute text-[14px] leading-[1.55]">{v.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section section-creme">
        <div className="page-shell text-center">
          <h2 className="headline-section">Ready to roll your roster out?</h2>
          <p className="mt-4 body-lg max-w-[640px] mx-auto">
            Book a 20-minute call. Bring your release schedule and we will show you how it would look inside Omni DJ.
          </p>
          <div className="mt-8 flex justify-center gap-3 flex-wrap">
            <Link href="/contact" className="btn btn-orange">Book a call</Link>
            <Link href="/pricing" className="btn btn-outline-dark">Compare tiers</Link>
          </div>
        </div>
      </section>
    </>
  );
}
