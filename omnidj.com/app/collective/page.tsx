import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Collective — Omni DJ',
  description: 'The artists shaping Omni DJ.'
};

const slots = Array.from({ length: 8 }, (_, i) => ({
  name: `Artist ${i + 1}`,
  handle: `@artist${i + 1}`,
  credit: ['Resident · TBC', 'Festival main stage', 'Label · TBC', 'Touring'][i % 4]
}));

export default function CollectivePage() {
  return (
    <section className="pt-40 pb-24 bg-black">
      <div className="page-shell">
        <div className="max-w-[760px]">
          <h1 className="headline-section text-creme">The artists shaping Omni DJ.</h1>
          <p className="mt-5 body-lg text-creme-mute">
            We build Omni DJ next to the DJs who actually use it. These are the artists shaping the product.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {slots.map((s, i) => (
            <div key={i} className="space-y-3">
              <div
                className="placeholder-box rounded-2xl"
                style={{ aspectRatio: '9 / 16' }}
              >
                <span>Vertical clip placeholder</span>
              </div>
              <div>
                <div className="text-creme font-medium">{s.name}</div>
                <a href="#" className="text-[13px] text-creme-mute hover:text-creme transition-colors">{s.handle}</a>
                <div className="text-[12px] text-creme-mute mt-1">{s.credit}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
