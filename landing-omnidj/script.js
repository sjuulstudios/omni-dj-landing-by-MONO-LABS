/* =========================================
   Omni DJ — Landing v1
   Minimal vanilla JS
   ========================================= */

(function () {
  'use strict';

  // ---- Mobile nav toggle ----
  var burger = document.getElementById('navBurger');
  var navLinks = document.querySelector('.nav-links');
  var navOpen = false;

  if (burger) {
    burger.addEventListener('click', function () {
      navOpen = !navOpen;
      burger.setAttribute('aria-expanded', String(navOpen));
      if (navOpen) {
        navLinks.style.display = 'flex';
        navLinks.style.position = 'fixed';
        navLinks.style.top = '64px';
        navLinks.style.left = '0';
        navLinks.style.right = '0';
        navLinks.style.flexDirection = 'column';
        navLinks.style.background = 'rgba(10,10,10,0.95)';
        navLinks.style.backdropFilter = 'blur(20px)';
        navLinks.style.padding = '24px';
        navLinks.style.gap = '20px';
        navLinks.style.borderBottom = '1px solid rgba(242,232,211,0.08)';
      } else {
        navLinks.removeAttribute('style');
      }
    });
  }

  // Close nav on link click (mobile)
  document.querySelectorAll('.nav-links a').forEach(function (a) {
    a.addEventListener('click', function () {
      if (window.innerWidth <= 1000 && navOpen) {
        navOpen = false;
        burger.setAttribute('aria-expanded', 'false');
        navLinks.removeAttribute('style');
      }
    });
  });

  // ---- Sticky nav shadow on scroll ----
  var nav = document.getElementById('nav');
  function updateNavShadow() {
    if (window.scrollY > 8) {
      nav.style.boxShadow = '0 6px 24px -12px rgba(0,0,0,0.5)';
    } else {
      nav.style.boxShadow = '';
    }
  }
  if (nav) {
    window.addEventListener('scroll', updateNavShadow, { passive: true });
    updateNavShadow();
  }

  // ---- Beta form handler ----
  var betaForm = document.getElementById('betaForm');
  if (betaForm) {
    betaForm.addEventListener('submit', function (e) {
      // Replace this with your real Formspree (or other) endpoint.
      var action = betaForm.getAttribute('action') || '';
      if (action.indexOf('REPLACE_ME') !== -1) {
        e.preventDefault();
        var input = document.getElementById('betaEmail');
        if (input && input.value) {
          alert('Thanks. Replace the Formspree endpoint in script.js to actually receive ' + input.value);
        }
        return;
      }

      // Default: let the browser submit to Formspree (Ajax can be added later).
      var btn = betaForm.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Sending…';
      }
    });
  }

  // ---- Smooth-scroll for #anchors (older browsers fallback) ----
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var href = a.getAttribute('href');
      if (!href || href === '#') return;
      var target = document.querySelector(href);
      if (!target) return;
      e.preventDefault();
      var top = target.getBoundingClientRect().top + window.scrollY - 72;
      window.scrollTo({ top: top, behavior: 'smooth' });
    });
  });

  // ---- Reveal-on-scroll for cards (subtle) ----
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    document.querySelectorAll(
      '.how-card, .feat, .wf-step, .price-card, .faq-item'
    ).forEach(function (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(16px)';
      el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
      io.observe(el);
    });
  }
})();
