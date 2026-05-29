import Link from 'next/link';

export default function NotFound() {
  return (
    <section className="pt-40 pb-24 bg-black min-h-screen flex items-center">
      <div className="page-shell text-center">
        <div className="text-[120px] font-bold tracking-tight text-creme leading-none">404</div>
        <h1 className="mt-6 headline-h3 text-creme">This page is off the deck.</h1>
        <p className="mt-4 text-creme-mute max-w-[480px] mx-auto">
          The link you followed does not exist. Drop the needle back on the home page.
        </p>
        <div className="mt-10 flex justify-center gap-3 flex-wrap">
          <Link href="/" className="btn btn-orange">Back to home</Link>
          <Link href="/contact" className="btn btn-outline">Tell us what was missing</Link>
        </div>
      </div>
    </section>
  );
}
