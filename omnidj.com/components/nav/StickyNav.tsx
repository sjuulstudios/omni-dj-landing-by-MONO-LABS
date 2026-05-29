'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import OmniMark from '@/components/logo/OmniMark';
import MegaMenu from '@/components/nav/MegaMenu';
import { navItems, navAuth, type NavItem } from '@/lib/content/nav';
import { featuresMega, solutionsMega } from '@/lib/content/megamenu';

export default function StickyNav() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openMega, setOpenMega] = useState<NavItem['mega'] | null>(null);
  const [mobileExpanded, setMobileExpanded] = useState<string | null>(null);
  const closeTimer = useRef<number | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpenMega(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const scheduleClose = () => {
    if (closeTimer.current) window.clearTimeout(closeTimer.current);
    closeTimer.current = window.setTimeout(() => setOpenMega(null), 150);
  };
  const cancelClose = () => {
    if (closeTimer.current) {
      window.clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
  };
  const openFor = (mega: NavItem['mega']) => {
    cancelClose();
    setOpenMega(mega ?? null);
  };

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ease-smooth ${
          scrolled ? 'bg-black/85 backdrop-blur-md' : 'bg-transparent'
        }`}
        style={{ borderBottom: scrolled ? '1px solid var(--creme-line)' : '1px solid transparent' }}
      >
        <div className="page-shell flex items-center justify-between" style={{ height: 72 }}>
          {/* Left: logo + wordmark */}
          <Link href="/" className="flex items-center gap-3 group" aria-label="Omni DJ — home">
            <OmniMark size={28} spin />
            <div className="flex items-baseline gap-2">
              <span className="text-creme font-medium tracking-tight text-[18px]">Omni DJ</span>
              <span className="hidden sm:inline text-[10px] tracking-[0.14em] uppercase text-creme-mute font-medium">
                by MONO LABS
              </span>
            </div>
          </Link>

          {/* Center: nav items with mega-menus */}
          <nav className="hidden lg:flex items-center gap-1 relative">
            {navItems.map(item => {
              const hasMega = !!item.mega;
              const isOpen = openMega === item.mega;
              return (
                <div
                  key={item.href}
                  className="relative"
                  onMouseEnter={hasMega ? () => openFor(item.mega) : undefined}
                  onMouseLeave={hasMega ? scheduleClose : undefined}
                >
                  <Link
                    href={item.href}
                    onFocus={hasMega ? () => openFor(item.mega) : undefined}
                    aria-haspopup={hasMega ? 'true' : undefined}
                    aria-expanded={hasMega ? isOpen : undefined}
                    className="flex items-center gap-1 px-3 py-2 text-[14px] font-medium text-creme hover:text-white transition-colors"
                  >
                    {item.label}
                    {hasMega && (
                      <svg
                        width="10"
                        height="10"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.4"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                        style={{
                          opacity: 0.6,
                          transform: `rotate(${isOpen ? 180 : 0}deg)`,
                          transition: 'transform 320ms var(--ease-overshoot)'
                        }}
                      >
                        <path d="M6 9l6 6 6-6" />
                      </svg>
                    )}
                  </Link>

                  {hasMega && (
                    <MegaMenu
                      open={isOpen}
                      columns={item.mega === 'features' ? featuresMega.columns : solutionsMega.columns}
                      onMouseEnter={cancelClose}
                      onMouseLeave={scheduleClose}
                      onItemClick={() => setOpenMega(null)}
                    />
                  )}
                </div>
              );
            })}
          </nav>

          {/* Right: auth */}
          <div className="hidden lg:flex items-center gap-3">
            <Link
              href={navAuth.login.href}
              className="text-[14px] font-medium text-creme hover:text-white transition-colors"
            >
              {navAuth.login.label}
            </Link>
            <Link href={navAuth.signup.href} className="btn btn-creme" style={{ height: 38, padding: '0 18px' }}>
              {navAuth.signup.label}
            </Link>
          </div>

          {/* Mobile burger */}
          <button
            className="lg:hidden flex flex-col gap-[5px] p-2"
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen(o => !o)}
          >
            <span
              className="block w-6 h-[1.5px] bg-creme transition-transform"
              style={{ transform: mobileOpen ? 'rotate(45deg) translate(5px, 4px)' : 'none' }}
            />
            <span
              className="block w-6 h-[1.5px] bg-creme transition-opacity"
              style={{ opacity: mobileOpen ? 0 : 1 }}
            />
            <span
              className="block w-6 h-[1.5px] bg-creme transition-transform"
              style={{ transform: mobileOpen ? 'rotate(-45deg) translate(5px, -4px)' : 'none' }}
            />
          </button>
        </div>
      </header>

      {/* Mobile slide-down menu */}
      <div
        className={`fixed inset-0 z-40 bg-black lg:hidden transition-opacity duration-300 ${
          mobileOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        style={{ paddingTop: 72, overflowY: 'auto' }}
      >
        <nav className="page-shell flex flex-col gap-1 pt-8 pb-12">
          {navItems.map(item => {
            const expanded = mobileExpanded === item.label;
            const cols = item.mega === 'features' ? featuresMega.columns : item.mega === 'solutions' ? solutionsMega.columns : null;
            return (
              <div key={item.href} className="border-b border-creme-line">
                {cols ? (
                  <button
                    onClick={() => setMobileExpanded(expanded ? null : item.label)}
                    aria-expanded={expanded}
                    className="w-full flex items-center justify-between py-4 text-[24px] font-medium text-creme"
                  >
                    {item.label}
                    <span style={{ transform: `rotate(${expanded ? 45 : 0}deg)`, transition: 'transform 200ms', display: 'inline-block' }}>+</span>
                  </button>
                ) : (
                  <Link
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className="block py-4 text-[24px] font-medium text-creme"
                  >
                    {item.label}
                  </Link>
                )}
                {cols && (
                  <div
                    className="overflow-hidden transition-all"
                    style={{
                      maxHeight: expanded ? 1200 : 0,
                      opacity: expanded ? 1 : 0
                    }}
                  >
                    <div className="pb-4 space-y-1">
                      {cols.flatMap(c => c.items).map((sub, i) => (
                        <Link
                          key={i}
                          href={sub.href}
                          onClick={() => setMobileOpen(false)}
                          className="block py-2 text-creme-mute text-[14px]"
                          style={{ opacity: sub.soon ? 0.55 : 1 }}
                        >
                          {sub.title}
                          {sub.soon && (
                            <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: 'rgba(255,106,26,0.16)', color: 'var(--orange)' }}>
                              soon
                            </span>
                          )}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
          <div className="mt-8 flex flex-col gap-3">
            <Link href={navAuth.login.href} onClick={() => setMobileOpen(false)} className="btn btn-outline w-full">
              {navAuth.login.label}
            </Link>
            <Link href={navAuth.signup.href} onClick={() => setMobileOpen(false)} className="btn btn-creme w-full">
              {navAuth.signup.label}
            </Link>
          </div>
        </nav>
      </div>
    </>
  );
}
