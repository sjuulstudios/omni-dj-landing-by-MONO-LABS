import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { legalPages } from '@/lib/content/legal';

export async function generateStaticParams() {
  return Object.keys(legalPages).map(slug => ({ slug }));
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const p = legalPages[params.slug];
  if (!p) return {};
  return { title: `${p.title} — Omni DJ` };
}

export default function LegalPage({ params }: { params: { slug: string } }) {
  const page = legalPages[params.slug];
  if (!page) notFound();

  return (
    <section className="pt-40 pb-24 bg-black">
      <div className="page-shell">
        <div className="max-w-[760px] mx-auto">
          <div className="eyebrow text-creme-mute mb-5">Legal</div>
          <h1 className="headline-section text-creme">{page.title}</h1>
          <p className="mt-4 text-creme-mute text-[13px]">Last updated: {page.updated}</p>

          <div className="mt-12 space-y-10">
            {page.sections.map((s, i) => (
              <div key={i}>
                <h2 className="text-creme font-medium text-[22px] tracking-tight">{s.heading}</h2>
                <p className="mt-3 body-default text-creme-mute">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
