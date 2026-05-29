export type LegalPage = {
  slug: 'terms' | 'privacy' | 'trust';
  title: string;
  updated: string;
  sections: { heading: string; body: string }[];
};

export const legalPages: Record<string, LegalPage> = {
  terms: {
    slug: 'terms',
    title: 'Terms of Service',
    updated: '29 May 2026',
    sections: [
      {
        heading: 'Acceptance of terms',
        body: 'By downloading or using Omni DJ, you agree to these Terms of Service. If you do not agree, do not use the product. Omni DJ is operated by MONO LABS (the legal entity behind the product).'
      },
      {
        heading: 'Licence',
        body: 'We grant you a non-exclusive, non-transferable licence to use Omni DJ on your own machine for the duration of your subscription or trial. You may not redistribute, reverse engineer or resell the software.'
      },
      {
        heading: 'Your content',
        body: 'You retain all rights to the audio, video and other content you process through Omni DJ. We never claim ownership of your sets, your clips, your brand assets or your output.'
      },
      {
        heading: 'Local-first processing',
        body: 'Omni DJ analyses and edits your files on your own machine by default. Cloud features (where applicable) are opt-in and clearly labelled inside the product.'
      },
      {
        heading: 'Subscriptions and refunds',
        body: 'Paid plans renew monthly or yearly until you cancel. You can cancel any time inside the app or by contacting support. Refunds are evaluated case by case within 14 days of the most recent charge.'
      },
      {
        heading: 'Liability',
        body: 'Omni DJ is provided as-is. We will not be liable for indirect, incidental or consequential damages arising from your use of the product, to the maximum extent permitted by law.'
      },
      {
        heading: 'Changes',
        body: 'We may update these terms occasionally. Material changes will be announced inside the product and on this page at least 30 days before they take effect.'
      },
      {
        heading: 'Contact',
        body: 'Questions about these terms? Email support@omnidj.com.'
      }
    ]
  },
  privacy: {
    slug: 'privacy',
    title: 'Privacy Policy',
    updated: '29 May 2026',
    sections: [
      {
        heading: 'What we collect',
        body: 'When you create an account: your email address and the workspace metadata you provide. When you use the product locally: nothing leaves your machine by default. When you opt into cloud features: only the data you explicitly choose to send.'
      },
      {
        heading: 'What we do not collect',
        body: 'We do not upload, scan or transmit your audio or video files. We do not sell, rent or share your personal data. We do not use your sets to train AI models, ever.'
      },
      {
        heading: 'Analytics',
        body: 'We collect anonymous product telemetry (which features get used, crash reports) to improve Omni DJ. You can opt out in Settings → Diagnostics at any time.'
      },
      {
        heading: 'Cookies on this website',
        body: 'omnidj.com uses only the cookies strictly necessary to keep the site working. No tracking cookies, no third-party advertising pixels.'
      },
      {
        heading: 'Your rights (GDPR)',
        body: 'You can request access, correction or deletion of your personal data by emailing support@omnidj.com. We respond within 30 days.'
      },
      {
        heading: 'Data processors',
        body: 'For paid plans we use Stripe (payments) and a transactional email provider (account emails). Data shared is limited to what each provider needs to operate.'
      },
      {
        heading: 'Contact',
        body: 'Privacy questions? Email support@omnidj.com.'
      }
    ]
  },
  trust: {
    slug: 'trust',
    title: 'Trust',
    updated: '29 May 2026',
    sections: [
      {
        heading: 'Local-first by design',
        body: 'Audio and video analysis runs on your machine. Your sets never leave it unless you explicitly opt into a cloud feature. There is no upload queue, no third-party processing pipeline by default.'
      },
      {
        heading: 'Account data',
        body: 'Authentication is handled by Supabase. We store only the minimum needed to run subscriptions, workspaces and basic identity. No biometric, no payment card data on our side.'
      },
      {
        heading: 'Payments',
        body: 'Card data is handled directly by Stripe under their PCI DSS Level 1 certification. Omni DJ never sees your card number.'
      },
      {
        heading: 'Security practices',
        body: 'HTTPS everywhere. Database row-level security on every table that touches user data. Regular dependency audits. Production secrets rotated on incident.'
      },
      {
        heading: 'Reporting an issue',
        body: 'Security disclosures: security@omnidj.com. We aim to acknowledge within one business day.'
      }
    ]
  }
};
