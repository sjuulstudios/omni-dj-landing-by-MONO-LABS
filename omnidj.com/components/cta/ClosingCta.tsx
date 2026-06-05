'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import Reveal from '@/components/ui/Reveal';
import { DOWNLOAD_URL } from '@/lib/config';

export default function ClosingCta() {
  const ref = useRef<HTMLElement>(null);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (reduce.matches) return;

    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const el = ref.current;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        // -10% drift: glow moves opposite to scroll as the section passes.
        const centered = (window.innerHeight / 2 - (rect.top + rect.height / 2)) / window.innerHeight;
        setOffset(centered * -60);
      });
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
    };
  }, []);

  return (
    <section ref={ref} className="section section-creme relative overflow-hidden">
      {/* Parallax orange glow drifting across the section on scroll */}
      <div
        aria-hidden="true"
        className="absolute pointer-events-none"
        style={{
          top: '50%',
          left: '50%',
          width: 720,
          height: 360,
          marginLeft: -360,
          marginTop: -180,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255,106,26,0.16) 0%, transparent 70%)',
          filter: 'blur(40px)',
          transform: `translateX(${offset}px)`,
          transition: 'transform 120ms linear'
        }}
      />
      <div className="page-shell text-center relative">
        <Reveal>
          <h2 className="headline-section">Stop Editing, Start posting.</h2>
        </Reveal>
        <Reveal delay={120}>
          <p className="mt-5 body-lg max-w-[640px] mx-auto">
            Turn your next DJ-set into a month of content.
          </p>
        </Reveal>
        <Reveal delay={200}>
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            <a href={DOWNLOAD_URL} className="btn btn-orange">Download Omni DJ</a>
            <Link href="/contact" className="btn btn-outline-dark">Talk to sales</Link>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
