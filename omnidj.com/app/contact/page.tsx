import type { Metadata } from 'next';
import ContactForm from '@/components/contact/ContactForm';

export const metadata: Metadata = {
  title: 'Contact — Omni DJ',
  description: 'Tell us about your set, your team, your audience.'
};

export default function ContactPage() {
  return (
    <section className="pt-40 pb-24 bg-black">
      <div className="page-shell">
        <div className="max-w-[760px] mx-auto">
          <h1 className="headline-section text-creme">Let&apos;s talk.</h1>
          <p className="mt-5 body-lg text-creme-mute">
            Tell us about your set, your team, your audience. We get back to every message within two business days.
          </p>

          <div className="mt-12">
            <ContactForm />
          </div>

          <div className="mt-10 text-creme-mute text-[14px] flex flex-wrap gap-x-8 gap-y-2">
            <a href="mailto:omnidj@monohq-labs.com" className="hover:text-creme">omnidj@monohq-labs.com</a>
          </div>
        </div>
      </div>
    </section>
  );
}
