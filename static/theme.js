/**
 * TriggersAPI Theme Manager
 * Light/dark toggle. Persists to localStorage.
 * Dark mode works via Tailwind's `dark:` class strategy —
 * only pages with dark: variants in their markup respond to it.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'triggersapi_theme';

  function getStored() {
    return localStorage.getItem(STORAGE_KEY) || 'light';
  }

  function apply(theme) {
    var html = document.documentElement;
    html.classList.toggle('dark', theme === 'dark');
    html.classList.toggle('light', theme !== 'dark');
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
    apply(document.documentElement.classList.contains('dark') ? 'light' : 'dark');
  }

  function injectToggle() {
    if (document.querySelector('.tapi-theme-toggle')) return;

    var header = document.querySelector('header');
    if (!header) return;

    var btn = document.createElement('button');
    btn.className = 'tapi-theme-toggle';
    btn.title = 'Toggle light/dark mode';
    btn.style.cssText =
      'padding:7px;border-radius:9999px;background:transparent;border:none;' +
      'cursor:pointer;display:inline-flex;align-items:center;justify-content:center;' +
      'transition:background .2s;margin:0 2px;vertical-align:middle;';
    btn.innerHTML =
      '<span class="material-symbols-outlined tapi-sun" style="font-size:20px;color:#f59e0b;">light_mode</span>' +
      '<span class="material-symbols-outlined tapi-moon" style="font-size:20px;color:#6366f1;">dark_mode</span>';
    btn.onmouseenter = function () { this.style.background = 'rgba(128,128,128,.12)'; };
    btn.onmouseleave = function () { this.style.background = 'transparent'; };
    btn.onclick = function (e) { e.preventDefault(); toggle(); };

    // Place next to avatar (right side of header)
    var avatar = header.querySelector('img[class*="rounded-full"], div[class*="rounded-full"]');
    if (avatar) {
      var target = avatar.closest('a') || avatar;
      target.parentElement.insertBefore(btn, target);
    } else {
      var containers = header.querySelectorAll('.flex.items-center');
      var rightmost = containers[containers.length - 1];
      if (rightmost) rightmost.appendChild(btn);
    }
    updateIcons(getStored());
  }

  // Apply stored theme immediately (prevent flash)
  apply(getStored());

  // Inject toggle when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectToggle);
  } else {
    injectToggle();
  }
})();
