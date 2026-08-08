/**
 * NidaanPath AI — language.js
 * English/Tamil language switching
 */
'use strict';

const TRANSLATIONS = {
  en: {
    'Possible Stagnation': 'Possible Stagnation',
    'Active Progress': 'Active Progress',
    'Awaiting Evidence': 'Awaiting Evidence',
    'Clinician Review Required': 'Clinician Review Required',
    'Load Reports': 'Load Reports 01–08',
    'Add Specialist': 'Add Specialist Evidence',
  },
  ta: {
    'Possible Stagnation': 'சாத்தியமான தேக்கம்',
    'Active Progress': 'செயலில் முன்னேற்றம்',
    'Awaiting Evidence': 'சான்று எதிர்பார்க்கிறது',
    'Clinician Review Required': 'மருத்துவர் ஆய்வு தேவை',
    'Load Reports': 'அறிக்கைகள் 01–08 ஏற்றவும்',
    'Add Specialist': 'நிபுணர் சான்று சேர்க்கவும்',
  }
};

function applyTranslations(lang) {
  const t = TRANSLATIONS[lang] || TRANSLATIONS.en;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) el.textContent = t[key];
  });
}

// Apply language from cookie on load
(function() {
  const lang = document.cookie.split(';')
    .find(c => c.trim().startsWith('nidaan_lang='))
    ?.split('=')[1] || 'en';
  applyTranslations(lang);
})();
