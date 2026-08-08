/**
 * NidaanPath AI — app.js
 * Core application JavaScript
 */
'use strict';

// ── Language Management ──────────────────────────────────────────────────────
function setLanguage(lang) {
  document.cookie = `nidaan_lang=${lang};path=/;max-age=86400`;
  // Update active button
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.id === 'lang' + lang.charAt(0).toUpperCase() + lang.slice(1));
  });
  // Apply translations
  applyTranslations(lang);
}

function applyTranslations(lang) {
  fetch(`/static/js/../translations/${lang === 'ta' ? 'ta' : 'en'}.json`)
    .catch(() => null);
  // Simple DOM translation via data-i18n attributes
  document.querySelectorAll('[data-i18n]').forEach(el => {
    // Translations applied via language.js
  });
}

// ── Notifications ────────────────────────────────────────────────────────────
function showNotification(message, type = 'info', duration = 3000) {
  const notif = document.createElement('div');
  notif.style.cssText = `
    position:fixed;bottom:2rem;right:2rem;
    background:${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--critical)' : 'var(--navy)'};
    color:white;padding:1rem 1.5rem;border-radius:var(--radius-lg);
    box-shadow:var(--shadow-lg);z-index:9999;
    animation:fadeInUp 0.3s ease-out;
    max-width:360px;font-size:0.875rem;line-height:1.4;
  `;
  notif.textContent = message;
  document.body.appendChild(notif);
  setTimeout(() => {
    notif.style.animation = 'none';
    notif.style.opacity = '0';
    notif.style.transition = 'opacity 0.3s';
    setTimeout(() => notif.remove(), 300);
  }, duration);
}

// ── API Helpers ──────────────────────────────────────────────────────────────
async function apiPost(url, data = null) {
  const opts = {method: 'POST'};
  if (data) {
    opts.headers = {'Content-Type': 'application/json'};
    opts.body = JSON.stringify(data);
  }
  const resp = await fetch(url, opts);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

// ── UI Utilities ─────────────────────────────────────────────────────────────
function setLoading(btn, loading, originalText) {
  btn.disabled = loading;
  btn.innerHTML = loading
    ? '<span class="spinner"></span> Loading...'
    : originalText;
}

// ── Auto-animate cards on scroll ─────────────────────────────────────────────
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, {threshold: 0.1});

  document.querySelectorAll('.animate-in').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';
    observer.observe(el);
  });
}

// ── Text-to-Speech (patient guidance) ────────────────────────────────────────
function speakText(text, lang = 'en') {
  if ('speechSynthesis' in window) {
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = lang === 'ta' ? 'ta-IN' : 'en-IN';
    utter.rate = 0.85;
    window.speechSynthesis.speak(utter);
  }
}

// ── Print Optimization ───────────────────────────────────────────────────────
window.addEventListener('beforeprint', () => {
  document.querySelectorAll('details').forEach(d => d.open = true);
});
