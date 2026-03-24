/**
 * TriggersAPI Theme Manager
 * Handles light/dark mode toggle with localStorage persistence.
 * Self-initializes on load. Include via <script src="/static/theme.js"></script>
 */
(function () {
  'use strict';

  const STORAGE_KEY = 'triggersapi_theme';

  function getPreferred() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark' || stored === 'light') return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    const html = document.documentElement;
    if (theme === 'dark') {
      html.classList.add('dark');
      html.classList.remove('light');
    } else {
      html.classList.add('light');
      html.classList.remove('dark');
    }
    localStorage.setItem(STORAGE_KEY, theme);
    updateToggleIcons(theme);
  }

  function updateToggleIcons(theme) {
    document.querySelectorAll('.theme-toggle-btn').forEach(function (btn) {
      var sun = btn.querySelector('.theme-icon-sun');
      var moon = btn.querySelector('.theme-icon-moon');
      if (sun && moon) {
        if (theme === 'dark') {
          sun.style.display = 'inline';
          moon.style.display = 'none';
        } else {
          sun.style.display = 'none';
          moon.style.display = 'inline';
        }
      }
    });
  }

  function toggle() {
    var current = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
  }

  function injectToggleButton() {
    // Find the settings gear button(s) in the top nav — look for settings icon buttons
    var settingsBtns = document.querySelectorAll(
      'button .material-symbols-outlined, span.material-symbols-outlined'
    );
    var inserted = false;

    settingsBtns.forEach(function (icon) {
      if (icon.textContent.trim() === 'settings' && !inserted) {
        var parentBtn = icon.closest('button') || icon.parentElement;
        if (!parentBtn || parentBtn.querySelector('.theme-toggle-btn')) return;

        var toggleBtn = document.createElement('button');
        toggleBtn.className = 'theme-toggle-btn';
        toggleBtn.title = 'Toggle light/dark mode';
        toggleBtn.style.cssText =
          'padding:8px;border-radius:9999px;background:transparent;border:none;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;transition:background 0.2s;margin-right:0px;vertical-align:middle;';

        toggleBtn.innerHTML =
          '<span class="material-symbols-outlined theme-icon-sun" style="font-size:22px;color:#f59e0b;display:none;">light_mode</span>' +
          '<span class="material-symbols-outlined theme-icon-moon" style="font-size:22px;color:#6366f1;display:none;">dark_mode</span>';

        toggleBtn.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          toggle();
        });

        toggleBtn.addEventListener('mouseenter', function () {
          this.style.background = document.documentElement.classList.contains('dark')
            ? 'rgba(255,255,255,0.1)'
            : 'rgba(0,0,0,0.05)';
        });
        toggleBtn.addEventListener('mouseleave', function () {
          this.style.background = 'transparent';
        });

        parentBtn.parentElement.insertBefore(toggleBtn, parentBtn);
        inserted = true;
      }
    });

    // Fallback: if no settings button found, inject into any top nav header
    if (!inserted) {
      var header =
        document.querySelector('header .flex.items-center.gap-2') ||
        document.querySelector('header .flex.items-center.gap-3') ||
        document.querySelector('header .flex.gap-2');
      if (header) {
        var toggleBtn2 = document.createElement('button');
        toggleBtn2.className = 'theme-toggle-btn';
        toggleBtn2.title = 'Toggle light/dark mode';
        toggleBtn2.style.cssText =
          'padding:8px;border-radius:9999px;background:transparent;border:none;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;transition:background 0.2s;';
        toggleBtn2.innerHTML =
          '<span class="material-symbols-outlined theme-icon-sun" style="font-size:22px;color:#f59e0b;display:none;">light_mode</span>' +
          '<span class="material-symbols-outlined theme-icon-moon" style="font-size:22px;color:#6366f1;display:none;">dark_mode</span>';
        toggleBtn2.addEventListener('click', function (e) {
          e.preventDefault();
          toggle();
        });
        header.insertBefore(toggleBtn2, header.firstChild);
      }
    }
  }

  // Inject dark mode CSS overrides
  function injectDarkStyles() {
    var style = document.createElement('style');
    style.id = 'triggersapi-dark-theme';
    style.textContent = `
      /* === Dark Mode Overrides === */
      .dark body,
      .dark main,
      .dark .bg-surface,
      .dark .bg-\\[\\#f8f9fa\\],
      .dark .bg-\\[\\#fcfcfc\\],
      .dark .bg-\\[\\#f9f9f9\\] {
        background-color: #0f1117 !important;
        color: #e4e4e7 !important;
      }

      .dark header,
      .dark .bg-white,
      .dark .bg-surface-container-lowest,
      .dark [class*="bg-white"] {
        background-color: #1a1b23 !important;
        color: #e4e4e7 !important;
      }

      .dark aside,
      .dark .bg-\\[\\#f4f4f4\\],
      .dark .bg-\\[\\#f5f5f5\\],
      .dark .bg-\\[\\#f7f7f7\\],
      .dark .bg-zinc-50 {
        background-color: #12131a !important;
        color: #e4e4e7 !important;
      }

      .dark .bg-surface-container,
      .dark .bg-surface-container-low,
      .dark .bg-surface-container-high,
      .dark .bg-zinc-100,
      .dark .bg-zinc-50\\/50,
      .dark .bg-surface-container-low\\/30 {
        background-color: #1e1f2a !important;
      }

      .dark .text-on-surface,
      .dark .text-zinc-900,
      .dark .text-\\[\\#1a1a1a\\],
      .dark .text-on-background,
      .dark h1, .dark h2, .dark h3 {
        color: #f0f0f2 !important;
      }

      .dark .text-on-surface-variant,
      .dark .text-zinc-600,
      .dark .text-zinc-500,
      .dark .text-zinc-400 {
        color: #9ca3af !important;
      }

      .dark .text-zinc-700 {
        color: #a1a1aa !important;
      }

      .dark .border-zinc-100,
      .dark .border-zinc-200,
      .dark .border-outline-variant,
      .dark [class*="border-outline-variant"],
      .dark .divide-zinc-50 > * + *,
      .dark .divide-outline-variant\\/10 > * + * {
        border-color: #2a2b35 !important;
      }

      .dark table thead,
      .dark table thead tr,
      .dark .bg-surface-container-low\\/50 {
        background-color: #14151d !important;
      }

      .dark table tbody tr:hover {
        background-color: #1e1f2a !important;
      }

      .dark input,
      .dark select,
      .dark textarea {
        background-color: #1e1f2a !important;
        color: #e4e4e7 !important;
        border-color: #2a2b35 !important;
      }

      .dark input::placeholder,
      .dark textarea::placeholder {
        color: #6b7280 !important;
      }

      .dark .shadow-soft-hover,
      .dark .shadow-card,
      .dark .soft-shadow,
      .dark .shadow-sm,
      .dark .shadow-md,
      .dark .shadow-lg,
      .dark .shadow-xl {
        box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
      }

      .dark .shadow-2xl {
        box-shadow: 0 4px 20px rgba(0,0,0,0.5) !important;
      }

      .dark code {
        background-color: #1e1f2a !important;
        color: #f97316 !important;
      }

      .dark .bg-emerald-100 { background-color: rgba(16,185,129,0.15) !important; }
      .dark .bg-blue-100 { background-color: rgba(59,130,246,0.15) !important; }
      .dark .bg-red-100 { background-color: rgba(239,68,68,0.15) !important; }
      .dark .bg-yellow-100 { background-color: rgba(245,158,11,0.15) !important; }
      .dark .bg-green-100 { background-color: rgba(34,197,94,0.15) !important; }
      .dark .bg-zinc-100 { background-color: #1e1f2a !important; }

      .dark .bg-primary\\/10 {
        background-color: rgba(255,79,0,0.15) !important;
      }

      .dark footer {
        background-color: #0f1117 !important;
        border-color: #2a2b35 !important;
      }

      .dark .glass-panel {
        background: rgba(26,27,35,0.8) !important;
      }

      /* Keep brand colors intact */
      .dark .text-primary,
      .dark .text-\\[\\#FF4F00\\] {
        color: #FF4F00 !important;
      }

      .dark .bg-primary,
      .dark .bg-primary-container {
        background-color: #a93100 !important;
      }

      /* Scrollbar */
      .dark ::-webkit-scrollbar-thumb {
        background: #3a3b45 !important;
      }

      /* Active sidebar link adjustments */
      .dark aside a[class*="bg-white"],
      .dark aside .bg-white {
        background-color: #1e1f2a !important;
      }
    `;
    document.head.appendChild(style);
  }

  // Initialize immediately (before DOM ready for flash prevention)
  var initialTheme = getPreferred();
  if (initialTheme === 'dark') {
    document.documentElement.classList.add('dark');
    document.documentElement.classList.remove('light');
  } else {
    document.documentElement.classList.add('light');
    document.documentElement.classList.remove('dark');
  }

  // Inject styles immediately
  injectDarkStyles();

  // Inject toggle button when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      injectToggleButton();
      updateToggleIcons(getPreferred());
    });
  } else {
    injectToggleButton();
    updateToggleIcons(getPreferred());
  }
})();
