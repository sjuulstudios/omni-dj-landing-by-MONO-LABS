// Mobile nav toggle
(function () {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.nav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => nav.classList.toggle('is-open'));
  }

  // Close mobile nav when a link is clicked
  document.querySelectorAll('.nav-links a').forEach((a) => {
    a.addEventListener('click', () => nav && nav.classList.remove('is-open'));
  });

  // Smooth scroll for in-page anchors
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (id.length <= 1) return;
      const target = document.querySelector(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // "Drop DJ-set Live" button — for now, scroll to email capture.
  // When the app is downloadable, swap this for the download link.
  const dropBtn = document.getElementById('droplive-btn');
  if (dropBtn) {
    dropBtn.addEventListener('click', (e) => {
      const form = document.getElementById('early-access-form');
      if (form) {
        e.preventDefault();
        form.scrollIntoView({ behavior: 'smooth', block: 'center' });
        const input = form.querySelector('input');
        if (input) setTimeout(() => input.focus(), 400);
      }
    });
  }

  /* ───────────── Cookie consent ───────────── */
  // Stores choice in localStorage under "cdl-cookie-consent": "all" | "essential"
  // Banner re-appears only if no choice has been made yet.
  const COOKIE_KEY = 'cdl-cookie-consent';
  const banner = document.getElementById('cookie-banner');

  function showBanner() {
    if (banner) banner.classList.add('is-visible');
  }
  function hideBanner() {
    if (banner) banner.classList.remove('is-visible');
  }
  function setConsent(choice) {
    try { localStorage.setItem(COOKIE_KEY, choice); } catch (_) {}
    hideBanner();
    // Hook for future analytics: only enable when "all" is chosen.
    // if (choice === 'all') initAnalytics();
  }

  if (banner) {
    let stored = null;
    try { stored = localStorage.getItem(COOKIE_KEY); } catch (_) {}
    if (!stored) showBanner();

    const acceptBtn = document.getElementById('cookie-accept');
    const rejectBtn = document.getElementById('cookie-reject');
    if (acceptBtn) acceptBtn.addEventListener('click', () => setConsent('all'));
    if (rejectBtn) rejectBtn.addEventListener('click', () => setConsent('essential'));
  }

  // Footer "Cookie settings" link — re-opens the banner.
  document.querySelectorAll('#cookie-settings-link').forEach((link) => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      showBanner();
    });
  });

  /* ───────────── FAQ accordion ───────────── */
  // Uses native <details> elements; this just makes sure only one is open
  // at a time, which feels cleaner on the landing page.
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach((item) => {
    item.addEventListener('toggle', () => {
      if (item.open) {
        faqItems.forEach((other) => {
          if (other !== item) other.open = false;
        });
      }
    });
  });

  /* ───────────── Onboarding wizard ───────────── */
  // 4-step modal: hear-about → reasons → identity → account.
  // Submit writes to localStorage AND fires a hidden Formspree POST so
  // Sjuul receives every signup as email until Supabase is wired up.
  // Replace WIZARD_FORMSPREE_ENDPOINT below with your real Formspree URL.

  const WIZARD_FORMSPREE_ENDPOINT = 'https://formspree.io/f/REPLACE_ME';
  const WIZARD_STORAGE_KEY = 'cdl-onboarding';

  const overlay = document.getElementById('wizard-overlay');
  const wizardEl = document.getElementById('wizard');
  if (overlay && wizardEl) {
    const steps = wizardEl.querySelectorAll('.wizard-step');
    const segs = wizardEl.querySelectorAll('.wizard-progress-seg');
    const backBtn = document.getElementById('wizard-back');
    const closeBtn = document.getElementById('wizard-close');

    // State container — flushed on submit
    const wState = {
      hear_about: null,
      hear_about_other: '',
      reasons: [],
      artist_name: '',
      real_name: '',
      instagram_url: '',
      tiktok_url: '',
      streaming_url: '',
      email: '',
      password: '',
      plan_intent: 'free',
      started_at: null,
    };
    let currentStep = 1;

    function openWizard(plan) {
      wState.plan_intent = plan || 'free';
      wState.started_at = new Date().toISOString();
      currentStep = 1;
      goToStep(1, /*animate*/ false);
      overlay.hidden = false;
      overlay.classList.add('is-open');
      document.body.style.overflow = 'hidden';
      // focus first interactive element after slide-in
      setTimeout(() => {
        const firstBubble = wizardEl.querySelector('.wizard-step.is-active .wizard-bubble');
        if (firstBubble) firstBubble.focus();
      }, 250);
    }

    function closeWizard() {
      overlay.classList.remove('is-open');
      overlay.hidden = true;
      document.body.style.overflow = '';
    }

    function goToStep(n, animate = true) {
      currentStep = n;
      steps.forEach((stepEl) => {
        const idx = parseInt(stepEl.dataset.step, 10);
        stepEl.classList.remove('is-active', 'is-prev');
        if (idx === n) stepEl.classList.add('is-active');
        else if (idx < n) stepEl.classList.add('is-prev');
      });
      // Progress: 1..4 visible, 5 = success (all bars filled)
      const fillUpTo = n === 5 ? 4 : n;
      segs.forEach((seg, i) => {
        seg.classList.remove('is-active', 'is-done');
        if (i + 1 < fillUpTo) seg.classList.add('is-done');
        else if (i + 1 === fillUpTo) seg.classList.add('is-active');
      });
      // Back button visible from step 2 onwards, hidden on success
      backBtn.hidden = (n <= 1 || n === 5);
      if (!animate) {
        // Skip the slide-in transition on first open
        steps.forEach((stepEl) => {
          stepEl.style.transition = 'none';
          requestAnimationFrame(() => { stepEl.style.transition = ''; });
        });
      }
    }

    /* ── Bubbles (single + multi select) ── */
    wizardEl.querySelectorAll('.wizard-bubbles').forEach((group) => {
      const field = group.dataset.field;
      const mode = group.dataset.mode; // 'single' or 'multi'
      group.querySelectorAll('.wizard-bubble').forEach((bubble) => {
        bubble.addEventListener('click', () => {
          const value = bubble.dataset.value;
          if (mode === 'single') {
            group.querySelectorAll('.wizard-bubble').forEach((b) => b.classList.remove('is-selected'));
            bubble.classList.add('is-selected');
            wState[field] = value;
            // Show "Other" description box if Other is selected
            if (field === 'hear_about') {
              const otherWrap = document.getElementById('hear-about-other-wrap');
              if (otherWrap) {
                if (bubble.dataset.other === 'true') {
                  otherWrap.classList.add('is-visible');
                  setTimeout(() => {
                    const inp = document.getElementById('hear-about-other');
                    if (inp) inp.focus();
                  }, 200);
                } else {
                  otherWrap.classList.remove('is-visible');
                  wState.hear_about_other = '';
                  const inp = document.getElementById('hear-about-other');
                  if (inp) inp.value = '';
                }
              }
            }
            updateNextEnabled();
          } else {
            // multi
            bubble.classList.toggle('is-selected');
            const list = wState[field];
            const idx = list.indexOf(value);
            if (bubble.classList.contains('is-selected')) {
              if (idx === -1) list.push(value);
            } else {
              if (idx !== -1) list.splice(idx, 1);
            }
            updateNextEnabled();
          }
        });
      });
    });

    // Track the "Other" description text
    const otherInput = document.getElementById('hear-about-other');
    if (otherInput) {
      otherInput.addEventListener('input', () => {
        wState.hear_about_other = otherInput.value.trim();
      });
    }

    /* ── Continue button enable/disable per step ── */
    function updateNextEnabled() {
      const next1 = document.getElementById('wizard-next-1');
      const next2 = document.getElementById('wizard-next-2');
      if (next1) next1.disabled = !wState.hear_about;
      if (next2) next2.disabled = !(wState.reasons && wState.reasons.length > 0);
    }
    updateNextEnabled();

    /* ── Navigation ── */
    document.getElementById('wizard-next-1').addEventListener('click', () => {
      if (!wState.hear_about) return;
      goToStep(2);
    });
    document.getElementById('wizard-next-2').addEventListener('click', () => {
      if (!wState.reasons.length) return;
      goToStep(3);
    });
    document.getElementById('wizard-next-3').addEventListener('click', () => {
      if (!validateStep3()) return;
      goToStep(4);
    });
    document.getElementById('wizard-submit').addEventListener('click', () => {
      if (!validateStep4()) return;
      submitWizard();
    });

    backBtn.addEventListener('click', () => {
      if (currentStep > 1) goToStep(currentStep - 1);
    });
    closeBtn.addEventListener('click', closeWizard);

    // Close on overlay click (but not when clicking inside the modal)
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeWizard();
    });
    // Esc to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && overlay.classList.contains('is-open')) closeWizard();
    });

    /* ── Step 3 / 4 validation ── */
    function setError(inputId, visible) {
      const inp = document.getElementById(inputId);
      const err = wizardEl.querySelector(`[data-error-for="${inputId}"]`);
      if (inp) inp.classList.toggle('has-error', visible);
      if (err) err.classList.toggle('is-visible', visible);
    }
    function validateStep3() {
      const artist = document.getElementById('onb-artist').value.trim();
      const real = document.getElementById('onb-real').value.trim();
      let ok = true;
      setError('onb-artist', !artist); if (!artist) ok = false;
      setError('onb-real', !real); if (!real) ok = false;
      if (ok) {
        wState.artist_name = artist;
        wState.real_name = real;
        wState.instagram_url = document.getElementById('onb-instagram').value.trim();
        wState.tiktok_url = document.getElementById('onb-tiktok').value.trim();
        wState.streaming_url = document.getElementById('onb-streaming').value.trim();
      }
      return ok;
    }
    function validateStep4() {
      const email = document.getElementById('onb-email').value.trim();
      const pass = document.getElementById('onb-pass').value;
      const pass2 = document.getElementById('onb-pass2').value;
      const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      const passOk = pass.length >= 8;
      const matchOk = pass === pass2 && pass.length > 0;
      setError('onb-email', !emailOk);
      setError('onb-pass', !passOk);
      setError('onb-pass2', !matchOk);
      const ok = emailOk && passOk && matchOk;
      if (ok) {
        wState.email = email;
        wState.password = pass; // we DO NOT store this in plain text below
      }
      return ok;
    }

    /* ── Submit ── */
    function submitWizard() {
      // Build a sanitised payload — never persist the raw password locally
      // or send it to Formspree. Supabase will hash + store it later.
      const payload = {
        hear_about: wState.hear_about,
        hear_about_other: wState.hear_about_other,
        reasons: wState.reasons,
        artist_name: wState.artist_name,
        real_name: wState.real_name,
        instagram_url: wState.instagram_url,
        tiktok_url: wState.tiktok_url,
        streaming_url: wState.streaming_url,
        email: wState.email,
        plan_intent: wState.plan_intent,
        started_at: wState.started_at,
        submitted_at: new Date().toISOString(),
        password_set: true, // signal only — actual value never stored
      };

      // 1. Local storage (no password)
      try { localStorage.setItem(WIZARD_STORAGE_KEY, JSON.stringify(payload)); } catch (_) {}

      // 2. Formspree fallback so Sjuul gets an email until Supabase is live.
      // Skipped if endpoint placeholder hasn't been replaced.
      if (WIZARD_FORMSPREE_ENDPOINT && WIZARD_FORMSPREE_ENDPOINT.indexOf('REPLACE_ME') === -1) {
        try {
          fetch(WIZARD_FORMSPREE_ENDPOINT, {
            method: 'POST',
            headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
            body: JSON.stringify({
              ...payload,
              _subject: 'Omni DJ — new account signup',
              _replyto: payload.email,
            }),
          }).catch(() => { /* silent — UI moves on regardless */ });
        } catch (_) { /* ignore */ }
      }

      // 3. UI: success state
      goToStep(5);

      // 4. TODO when Supabase is connected: replace this whole block with
      //    supabase.auth.signUp({ email, password }) + insert into 'profiles'
      //    table. The wState already has every field you'll need.
    }

    /* ── Open triggers ── */
    document.querySelectorAll('[data-open-wizard]').forEach((trigger) => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        const plan = trigger.dataset.plan || 'free';
        openWizard(plan);
      });
    });
  }
})();
