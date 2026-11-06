/* ============================================================
   site.js — theme, TOC, solution toggles, difficulty filter
   No dependencies. Everything degrades to plain HTML without JS.
   ============================================================ */
(function () {
  'use strict';

  /* ---------------------------------------------------- theme ---------- */
  var KEY = 'mjmath-theme';
  var root = document.documentElement;

  function applyTheme(t) {
    root.setAttribute('data-theme', t);
    var b = document.querySelector('.theme-btn');
    if (b) {
      b.textContent = t === 'dark' ? '☀' : '☾';
      b.setAttribute('aria-label', t === 'dark' ? 'สลับเป็นโหมดสว่าง' : 'สลับเป็นโหมดมืด');
    }
  }

  try {
    var saved = localStorage.getItem(KEY);
    applyTheme(saved || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  } catch (e) { applyTheme('light'); }

  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest('.theme-btn');
    if (!btn) return;
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    try { localStorage.setItem(KEY, next); } catch (e) {}
    window.dispatchEvent(new CustomEvent('themechange', { detail: next }));
  });

  /* --------------------------------------------- solution toggles ------ */
  document.addEventListener('click', function (ev) {
    var t = ev.target.closest('.sol-toggle');
    if (!t) return;
    var sol = document.getElementById(t.getAttribute('aria-controls'));
    if (!sol) return;
    var open = sol.hasAttribute('hidden');
    if (open) { sol.removeAttribute('hidden'); } else { sol.setAttribute('hidden', ''); }
    t.setAttribute('aria-expanded', open ? 'true' : 'false');
    t.textContent = open ? 'ซ่อนเฉลย' : 'ดูเฉลย';
    if (open && window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise([sol]);
    }
  });

  /* reveal-all / hide-all */
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-sol-all]');
    if (!b) return;
    var scope = b.closest('.drill') || document;
    var want = b.getAttribute('data-sol-all') === 'show';
    scope.querySelectorAll('.qsol').forEach(function (s) {
      if (want) s.removeAttribute('hidden'); else s.setAttribute('hidden', '');
    });
    scope.querySelectorAll('.sol-toggle').forEach(function (t) {
      t.setAttribute('aria-expanded', want ? 'true' : 'false');
      t.textContent = want ? 'ซ่อนเฉลย' : 'ดูเฉลย';
    });
    if (want && window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise([scope]);
    }
  });

  /* ------------------------------------------- difficulty filter ------- */
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-filter]');
    if (!b) return;
    var scope = b.closest('.drill');
    if (!scope) return;
    var want = b.getAttribute('data-filter');
    scope.querySelectorAll('[data-filter]').forEach(function (o) {
      o.setAttribute('aria-pressed', o === b ? 'true' : 'false');
    });
    var shown = 0;
    scope.querySelectorAll('.q').forEach(function (q) {
      var lv = q.getAttribute('data-lvl');
      var ok = (want === 'all') || (lv === want);
      if (ok) { q.removeAttribute('hidden'); shown++; } else { q.setAttribute('hidden', ''); }
    });
    var stat = scope.querySelector('.drill-stat');
    if (stat) stat.textContent = 'แสดง ' + shown + ' / ' + scope.querySelectorAll('.q').length + ' ข้อ';
  });

  /* -------------------------------------------------- TOC active ------- */
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll('.toc a[href^="#"]'));
  if (tocLinks.length) {
    var targets = tocLinks.map(function (a) {
      return document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1)));
    });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var i = targets.indexOf(e.target);
        if (i < 0) return;
        tocLinks.forEach(function (a) { a.classList.remove('is-active'); });
        tocLinks[i].classList.add('is-active');
      });
    }, { rootMargin: '-72px 0px -70% 0px', threshold: 0 });
    targets.forEach(function (t) { if (t) obs.observe(t); });
  }
})();
