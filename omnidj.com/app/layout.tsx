import type { Metadata } from 'next';
import { GeistMono } from 'geist/font/mono';
import './globals.css';
import StickyNav from '@/components/nav/StickyNav';
import Footer from '@/components/footer/Footer';

export const metadata: Metadata = {
  title: {
    default: 'Omni DJ — Turn your DJ-sets into viral clips',
    template: '%s'
  },
  description: 'Local-first. Drops detected automatically. Three-hour set in, thirty-second clip out. By MONO LABS.',
  metadataBase: new URL('https://omnidj.com'),
  applicationName: 'Omni DJ',
  authors: [{ name: 'MONO LABS' }],
  keywords: ['DJ', 'DJ-set', 'clip generator', 'social media', 'TikTok', 'Instagram', 'auto-cut', 'drop detection', 'local-first'],
  openGraph: {
    title: 'Omni DJ — Turn your DJ-sets into viral clips',
    description: 'Local-first. Drops detected automatically. By MONO LABS.',
    url: 'https://omnidj.com',
    siteName: 'Omni DJ',
    type: 'website',
    locale: 'en_US'
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Omni DJ',
    description: 'Turn your hours-long DJ-sets into 20-second viral clips.'
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true }
  }
};

export const viewport = {
  themeColor: '#000000',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={GeistMono.variable}>
      <body>
        <a href="#main-content" className="skip-link">Skip to content</a>
        <StickyNav />
        <main id="main-content">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
