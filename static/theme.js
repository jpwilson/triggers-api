/**
 * TriggersAPI Theme Manager
 * Handles light/dark mode toggle with localStorage persistence.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'triggersapi_theme';

  function getPreferred() {
    var stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark' || stored === 'light') return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    var html = document.documentElement;
    html.classList.toggle('dark', theme === 'dark');
    html.classList.toggle('light', theme === 'light');
    localStorage.setItem(STORAGE_KEY, theme);
    updateIcons(theme);
  }

  function updateIcons(theme) {
    document.querySelectorAll('.tapi-theme-toggle').forEach(function (btn) {
      var sun = btn.querySelector('.tapi-sun');
      var moon = btn.querySelector('.tapi-moon');
      if (sun) sun.style.display = theme === 'dark' ? 'inline' : 'none';
      if (moon) moon.style.display = theme === 'dark' ? 'none' : 'inline';
    });
  }

  function toggle() {
    applyTheme(document.documentElement.classList.contains('dark') ? 'light' : 'dark');
  }

  function injectToggle() {
    if (document.querySelector('.tapi-theme-toggle')) return;

    // Strategy: find the right-side controls area in the header
    // Look for notification bell or settings gear, and insert AFTER them (before avatar)
    var header = document.querySelector('header');
    if (!header) return;

    var btn = document.createElement('button');
    btn.className = 'tapi-theme-toggle';
    btn.title = 'Toggle light/dark mode';
    btn.setAttribute('aria-label', 'Toggle theme');
    btn.innerHTML =
      '<span class="material-symbols-outlined tapi-sun" style="font-size:20px;color:#f59e0b;">light_mode</span>' +
      '<span class="material-symbols-outlined tapi-moon" style="font-size:20px;color:#6366f1;">dark_mode</span>';
    btn.addEventListener('click', function (e) { e.preventDefault(); toggle(); });

    // Find the avatar (usually last img or div with rounded-full in header)
    var avatar = header.querySelector('img[class*="rounded-full"], div[class*="rounded-full"]');
    if (avatar) {
      // Insert before the avatar's parent container
      var target = avatar.closest('a') || avatar;
      target.parentElement.insertBefore(btn, target);
    } else {
      // Fallback: append to the last flex container in header
      var rightSide = header.querySelectorAll('.flex.items-center');
      var last = rightSide[rightSide.length - 1];
      if (last) last.appendChild(btn);
    }

    updateIcons(getPreferred());
  }

  function injectStyles() {
    if (document.getElementById('tapi-theme-css')) return;
    var s = document.createElement('style');
    s.id = 'tapi-theme-css';
    s.textContent = [
      /* Toggle button */
      '.tapi-theme-toggle{',
        'padding:7px;border-radius:9999px;background:transparent;border:none;',
        'cursor:pointer;display:inline-flex;align-items:center;justify-content:center;',
        'transition:background .2s;margin:0 2px;vertical-align:middle;',
      '}',
      '.tapi-theme-toggle:hover{background:rgba(128,128,128,.15);}',

      /* ===== DARK MODE ===== */',

      /* Page backgrounds */
      '.dark body{background:#0d0e14!important;color:#d4d4d8!important;}',
      '.dark main{background:#0d0e14!important;}',

      /* Header */
      '.dark header{background:#13141c!important;border-color:#1f2029!important;}',

      /* Sidebar */
      '.dark aside{background:#0f1018!important;border-color:#1f2029!important;color:#d4d4d8!important;}',

      /* Cards — the big fix: target ALL white/light backgrounds in dark mode */
      '.dark [class*="bg-white"]{background:#181922!important;color:#d4d4d8!important;}',
      '.dark [class*="bg-surface"]{background:#181922!important;color:#d4d4d8!important;}',
      '.dark [class*="bg-zinc-5"]{background:#14151d!important;}',  /* bg-zinc-50, bg-zinc-50/50 */
      '.dark [class*="bg-zinc-1"]{background:#1a1b24!important;}',  /* bg-zinc-100 */
      '.dark [class*="bg-gray-5"]{background:#14151d!important;}',
      '.dark [class*="bg-slate-5"]{background:#14151d!important;}',
      '.dark [class*="bg-neutral-5"]{background:#14151d!important;}',

      /* Specific overrides to keep the dark hierarchy */
      '.dark body .bg-surface,.dark [class*="surface-dim"]{background:#0d0e14!important;}',
      '.dark [class*="surface-container-lowest"]{background:#181922!important;}',
      '.dark [class*="surface-container-high"]{background:#1a1b24!important;}',
      '.dark [class*="surface-container-low"]{background:#14151d!important;}',
      '.dark [class*="surface-container "]{background:#151620!important;}',

      /* Text */
      '.dark h1,.dark h2,.dark h3,.dark h4,.dark h5{color:#f4f4f5!important;}',
      '.dark p,.dark span,.dark label,.dark td,.dark th,.dark li,.dark a:not([class*="text-primary"]):not([class*="text-emerald"]):not([class*="text-red"]):not([class*="text-blue"]):not([class*="text-yellow"]):not([class*="text-green"]){color:inherit!important;}',
      '.dark [class*="text-on-surface"]{color:#d4d4d8!important;}',
      '.dark [class*="text-zinc-9"]{color:#f4f4f5!important;}',
      '.dark [class*="text-zinc-6"],.dark [class*="text-zinc-5"],.dark [class*="text-zinc-4"]{color:#9ca3af!important;}',
      '.dark [class*="text-gray-"]{color:#9ca3af!important;}',

      /* Borders */
      '.dark [class*="border-zinc"],.dark [class*="border-outline"],.dark [class*="border-gray"]{border-color:#262733!important;}',
      '.dark [class*="divide-zinc"] > * + *,.dark [class*="divide-outline"] > * + *{border-color:#262733!important;}',
      '.dark hr{border-color:#262733!important;}',

      /* Tables */
      '.dark table thead,.dark table thead tr{background:#111219!important;}',
      '.dark table tbody tr{border-color:#1f2029!important;}',
      '.dark table tbody tr:hover{background:#1a1b24!important;}',

      /* Inputs */
      '.dark input,.dark select,.dark textarea{background:#1a1b24!important;color:#d4d4d8!important;border-color:#262733!important;}',
      '.dark input::placeholder,.dark textarea::placeholder{color:#6b7280!important;}',

      /* Shadows */
      '.dark [class*="shadow"]{box-shadow:0 2px 8px rgba(0,0,0,.4)!important;}',

      /* Semantic color badges — keep visible but darken background */
      '.dark [class*="bg-emerald-1"]{background:rgba(16,185,129,.15)!important;}',
      '.dark [class*="bg-blue-1"]{background:rgba(59,130,246,.15)!important;}',
      '.dark [class*="bg-red-1"]{background:rgba(239,68,68,.15)!important;}',
      '.dark [class*="bg-yellow-1"]{background:rgba(245,158,11,.15)!important;}',
      '.dark [class*="bg-green-1"]{background:rgba(34,197,94,.15)!important;}',

      /* Brand colors stay */
      '.dark .text-primary,.dark [class*="text-\\\\[\\\\#FF4F00\\\\]"]{color:#FF4F00!important;}',
      '.dark [class*="bg-primary"]:not([class*="bg-primary/"]):not([class*="bg-primary\\\\/"]):not(aside *){background:#a93100!important;}',

      /* Sidebar active link */
      '.dark aside [class*="bg-white"],.dark aside [class*="bg-zinc"]{background:#1e1f2a!important;}',

      /* Footer */
      '.dark footer{background:#0d0e14!important;border-color:#1f2029!important;}',

      /* Code blocks — keep dark ones dark */
      '.dark code:not([class*="bg-zinc-9"]):not([class*="bg-gray-9"]){background:#1a1b24!important;color:#f97316!important;}',

      /* Scrollbar */
      '.dark ::-webkit-scrollbar-thumb{background:#3a3b45!important;}',
      '.dark ::-webkit-scrollbar-track{background:transparent!important;}',

    ].join('');
    document.head.appendChild(s);
  }

  // Apply immediately to prevent flash
  var initial = getPreferred();
  document.documentElement.classList.toggle('dark', initial === 'dark');
  document.documentElement.classList.toggle('light', initial === 'light');
  injectStyles();

  // Inject toggle when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { injectToggle(); });
  } else {
    injectToggle();
  }
})();
