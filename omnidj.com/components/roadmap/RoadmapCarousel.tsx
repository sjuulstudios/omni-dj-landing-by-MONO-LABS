'use client';

import React, { useEffect, useRef, useState } from 'react';
import { roadmapContent } from '@/lib/content/roadmap';

/**
 * Roadmap — scroll-driven horizontal reveal with alternating branches.
 *
 * GSAP + ScrollTrigger are lazy-loaded only when the section nears the viewport
 * (dynamic import inside an IntersectionObserver), keeping ~50kB out of the
 * initial bundle.
 *
 * Cards are click-to-expand: clicking opens a 480px pop-out with concept detail.
 * After the pinned reveal, a "get notified" email row is shown.
 *
 * Mobile (<768px) / reduced-motion: vertical stack, everything visible, no pin.
 */
export default function RoadmapCarousel() {
  const sectionRef = useRef<HTMLElement>(null);
  const lineRef = useRef<HTMLDivElement>(null);
  const cardsRef = useRef<Array<HTMLDivElement | null>>([]);
  const dotsRef = useRef<Array<HTMLDivElement | null>>([]);
  const branchesRef = useRef<Array<HTMLDivElement | null>>([]);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mq = window.matchMedia('(max-width: 767px)');
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

    const showAll = () => {
      cardsRef.current.forEach(el => { if (el) { el.style.opacity = '1'; el.style.transform = 'translateY(0)'; } });
      dotsRef.current.forEach(el => { if (el) el.style.background = 'var(--orange)'; });
      branchesRef.current.forEach(el => { if (el) el.style.transform = 'translateX(-50%) scaleY(1)'; });
      if (lineRef.current) lineRef.current.style.transform = 'scaleX(1)';
    };

    if (mq.matches || reduce.matches) {
      showAll();
      return;
    }

    let cleanup: (() => void) | undefined;
    let cancelled = false;

    // Lazy-load GSAP only when the section is about to enter the viewport.
    const io = new IntersectionObserver((entries) => {
      if (!entries[0].isIntersecting) return;
      io.disconnect();
      Promise.all([import('gsap'), import('gsap/dist/ScrollTrigger')]).then(([gsapMod, stMod]) => {
        if (cancelled) return;
        const gsap = gsapMod.gsap ?? gsapMod.default;
        const ScrollTrigger = stMod.ScrollTrigger ?? stMod.default;
        gsap.registerPlugin(ScrollTrigger);

        const ctx = gsap.context(() => {
          const N = roadmapContent.items.length;
          const tl = gsap.timeline({
            scrollTrigger: {
              trigger: sectionRef.current,
              // Pin 80px below the viewport top so the sticky nav (72px) never
              // covers the "Roadmap." title while the section is pinned.
              start: 'top top+=80',
              end: () => `+=${N * 240}`,
              pin: true,
              pinSpacing: true,
              scrub: 0.6,
              anticipatePin: 1,
              invalidateOnRefresh: true
            }
          });

          tl.fromTo(lineRef.current, { scaleX: 0 }, { scaleX: 1, duration: N, ease: 'none' }, 0);

          roadmapContent.items.forEach((_, i) => {
            const t = i;
            const dot = dotsRef.current[i];
            const branch = branchesRef.current[i];
            const card = cardsRef.current[i];
            if (!dot || !branch || !card) return;
            tl.to(dot, { background: 'var(--orange)', duration: 0.1 }, t + 0.1)
              .fromTo(branch, { scaleY: 0 }, { scaleY: 1, duration: 0.25, ease: 'power2.out' }, t + 0.1)
              .fromTo(card, { opacity: 0, y: i % 2 === 0 ? -16 : 16 }, { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out' }, t + 0.18);
          });
        }, sectionRef);

        cleanup = () => ctx.revert();
      });
    }, { rootMargin: '200px' });

    if (sectionRef.current) io.observe(sectionRef.current);

    return () => {
      cancelled = true;
      io.disconnect();
      cleanup?.();
    };
  }, []);

  // Esc closes the expanded card
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setExpanded(null); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <section ref={sectionRef} className="bg-black relative overflow-hidden section-bridge" style={{ minHeight: '100vh' }}>
      <div className="page-shell pt-24 pb-24">
        <h2 className="headline-section text-creme">{roadmapContent.headline}</h2>
        <p className="mt-4 body-lg text-creme-mute max-w-[520px]">{roadmapContent.subline}</p>

        {/* Mobile stacked fallback */}
        <div className="md:hidden mt-12 space-y-4">
          {roadmapContent.items.map((it, i) => (
            <button
              key={i}
              onClick={() => setExpanded(i)}
              className="w-full text-left p-5 rounded-2xl border border-creme-line"
              style={{ background: 'var(--ink-900)' }}
            >
              <div className="mono-label mb-2">NO.{String(i + 1).padStart(2, '0')}</div>
              <h3 className="text-creme font-medium text-[16px]">{it.title}</h3>
              <p className="mt-2 text-creme-mute text-[13px]">{it.body}</p>
            </button>
          ))}
        </div>

        {/* Desktop timeline canvas */}
        <div className="hidden md:block relative mt-20" style={{ height: 540 }}>
          <div aria-hidden="true" className="absolute" style={{ top: '50%', left: 0, right: 0, height: 1, background: 'rgba(245,239,227,0.18)' }} />
          <div
            ref={lineRef}
            aria-hidden="true"
            className="absolute"
            style={{ top: '50%', left: 0, right: 0, height: 1, background: 'var(--orange)', transformOrigin: 'left center', transform: 'scaleX(0)' }}
          />

          {roadmapContent.items.map((it, i) => {
            const above = i % 2 === 0;
            const N = roadmapContent.items.length;
            const pct = (i / (N - 1)) * 92;
            return (
              <React.Fragment key={i}>
                <div
                  ref={el => { dotsRef.current[i] = el; }}
                  aria-hidden="true"
                  className="absolute"
                  style={{ top: '50%', left: `${pct}%`, width: 12, height: 12, borderRadius: 6, background: 'var(--ink-800)', border: '2px solid rgba(245,239,227,0.4)', transform: 'translate(-50%, -50%)', zIndex: 2 }}
                />
                <div
                  ref={el => { branchesRef.current[i] = el; }}
                  aria-hidden="true"
                  className="absolute"
                  style={{ top: above ? 'calc(50% - 80px)' : '50%', left: `${pct}%`, width: 1, height: 80, background: 'rgba(245,239,227,0.32)', transform: 'translateX(-50%) scaleY(0)', transformOrigin: above ? 'bottom' : 'top', zIndex: 1 }}
                />
                <div
                  ref={el => { cardsRef.current[i] = el; }}
                  className="absolute"
                  style={{ [above ? 'bottom' : 'top']: 'calc(50% + 80px)', left: `${pct}%`, width: 240, transform: 'translateX(-50%)', opacity: 0, zIndex: 3 }}
                >
                  <button
                    onClick={() => setExpanded(i)}
                    className="w-full text-left p-4 rounded-xl roadmap-card"
                    style={{ background: 'var(--ink-900)', border: '1px solid var(--creme-line)' }}
                  >
                    <div className="mono-label mb-1.5" style={{ fontSize: 10 }}>NO.{String(i + 1).padStart(2, '0')}</div>
                    <h3 className="text-creme font-medium text-[14px] leading-tight">{it.title}</h3>
                    <p className="mt-1.5 text-creme-mute text-[12px] leading-[1.5]">{it.body}</p>
                    <span className="mt-2 inline-flex items-center gap-1 text-[11px]" style={{ color: 'var(--orange)' }}>
                      Details
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M9 6l6 6-6 6" /></svg>
                    </span>
                  </button>
                </div>
              </React.Fragment>
            );
          })}
        </div>

        {/* Subscribe row — shown after the pin releases */}
        <RoadmapSubscribe />
      </div>

      {/* Click-to-expand pop-out */}
      {expanded !== null && (
        <RoadmapPopout index={expanded} onClose={() => setExpanded(null)} />
      )}

      <style jsx>{`
        .roadmap-card { transition: transform 240ms var(--ease-drop), border-color 240ms var(--ease-drop); }
        .roadmap-card:hover { transform: translateY(-3px); border-color: rgba(245,239,227,0.28); }
      `}</style>
    </section>
  );
}

function RoadmapPopout({ index, onClose }: { index: number; onClose: () => void }) {
  const it = roadmapContent.items[index];
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={it.title}
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(0,0,0,0.6)',
        backdropFilter: 'blur(4px)',
        padding: 20
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        className="roadmap-popout"
        style={{
          width: 'min(480px, 100%)',
          background: 'var(--ink-900)',
          border: '1px solid var(--creme-line)',
          borderRadius: 20,
          padding: 28,
          boxShadow: '0 24px 48px rgba(0,0,0,0.4), 0 2px 8px rgba(0,0,0,0.3)'
        }}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="mono-label" style={{ color: 'var(--orange)' }}>NO.{String(index + 1).padStart(2, '0')}</div>
          <button onClick={onClose} aria-label="Close" className="text-creme-mute hover:text-creme transition-colors">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
          </button>
        </div>
        {/* concept-art placeholder (real screenshot for shipped items later) */}
        <div className="placeholder-box rounded-xl mt-4" style={{ aspectRatio: '16 / 9' }}>
          <span style={{ fontSize: 10 }}>Concept — {it.title}</span>
        </div>
        <h3 className="headline-h3 text-creme mt-5">{it.title}</h3>
        <p className="mt-3 text-creme-mute text-[14px] leading-[1.6]">{(it as { detail?: string }).detail ?? it.body}</p>
      </div>

      <style jsx>{`
        .roadmap-popout { animation: popIn 320ms var(--ease-drop); }
        @keyframes popIn { from { opacity: 0; transform: translateY(12px) scale(0.98); } to { opacity: 1; transform: none; } }
        @media (prefers-reduced-motion: reduce) { .roadmap-popout { animation: none; } }
      `}</style>
    </div>
  );
}

function RoadmapSubscribe() {
  const [email, setEmail] = useState('');
  const [done, setDone] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes('@')) return;
    await fetch('/api/beta-signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, source: 'roadmap' })
    }).catch(() => null);
    setDone(true);
  };
  return (
    <div className="mt-16 md:mt-24 flex flex-col items-start gap-3">
      <p className="text-creme-mute text-[14px]">Get notified when these ship.</p>
      {done ? (
        <div className="px-5 py-3 rounded-full border border-creme-line text-creme text-[14px]">
          Thanks. We will let you know.
        </div>
      ) : (
        <form onSubmit={submit} className="flex items-center gap-2 pl-5 pr-2 py-2 rounded-full border border-creme-line bg-ink-900" style={{ maxWidth: 360, width: '100%' }}>
          <input
            type="email"
            required
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@email.com"
            aria-label="Email for roadmap updates"
            className="flex-1 bg-transparent border-0 outline-none py-2 text-creme placeholder:text-creme-mute text-[14px] min-w-0"
          />
          <button type="submit" aria-label="Subscribe" className="flex-shrink-0 h-9 w-9 rounded-full flex items-center justify-center" style={{ background: 'var(--orange)', color: 'var(--ink)' }}>
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
          </button>
        </form>
      )}
    </div>
  );
}
