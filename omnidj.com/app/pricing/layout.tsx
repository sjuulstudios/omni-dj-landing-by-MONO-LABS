import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Pricing — Omni DJ',
  description: 'Free, Pro, Studio and Studio+. Local-first DJ-set clipping. EUR and USD.'
};

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
