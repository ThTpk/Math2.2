/* ===========================================================================
   viz3d.js — 3D solids for พื้นที่ผิวและปริมาตร  (Three.js, loaded from CDN)
   ---------------------------------------------------------------------------
   Progressive enhancement: the figure ships a complete static isometric SVG.
   Only when THREE is actually available do we swap in the live canvas, so the
   page is fully usable with JavaScript off or the CDN blocked.
   ========================================================================= */
(function () {
  'use strict';

  var REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function boot() {
    if (typeof window.THREE === 'undefined') return;        /* keep the SVG */
    document.querySelectorAll('figure.fig[data-viz3d]').forEach(function (fig) {
      try { build(fig); } catch (e) { if (window.console) console.warn('viz3d:', e); }
    });
  }

  function css(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function build(fig) {
    var kind = fig.getAttribute('data-viz3d');          /* 'prism' | 'cylinder' */
    var canvas = fig.querySelector('canvas.viz3d');
    var fallback = fig.querySelector('[data-fallback]');
    if (!canvas) return;
    canvas.hidden = false;
    if (fallback) fallback.hidden = true;

    var ctl = fig.querySelector('.fig-ctrl');
    var out = ctl && ctl.querySelector('[data-readout]');
    function input(n) { return ctl && ctl.querySelector('[data-input="' + n + '"]'); }
    function val(n, d) { var i = input(n); return i ? parseFloat(i.value) : d; }

    var THREE = window.THREE;
    var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));

    var scene = new THREE.Scene();
    var cam = new THREE.PerspectiveCamera(38, 16 / 10, 0.1, 200);
    cam.position.set(9, 7, 13);
    cam.lookAt(0, 0.4, 0);

    scene.add(new THREE.HemisphereLight(0xffffff, 0x404858, 1.05));
    var key = new THREE.DirectionalLight(0xffffff, 0.75);
    key.position.set(6, 10, 8);
    scene.add(key);

    var group = new THREE.Group();
    scene.add(group);

    var state = { mode: 'solid', spin: !REDUCED, slice: 0 };

    /* ------------------------------------------------------------ colours */
    function colors() {
      return {
        face: new THREE.Color(css('--accent', '#c8552e')),
        base: new THREE.Color(css('--teal', '#18736a')),
        edge: new THREE.Color(css('--ink', '#23283a'))
      };
    }

    var meshes = [], edges = [], sliceMesh = null;

    function clear() {
      while (group.children.length) {
        var c = group.children.pop();
        if (c.geometry) c.geometry.dispose();
        if (c.material) (Array.isArray(c.material) ? c.material : [c.material]).forEach(function (m) { m.dispose(); });
      }
      meshes = []; edges = []; sliceMesh = null;
    }

    function addSolid(geo, col, op) {
      var mat = new THREE.MeshStandardMaterial({
        color: col, roughness: 0.62, metalness: 0.02,
        transparent: true, opacity: op === undefined ? 0.9 : op,
        side: THREE.DoubleSide, flatShading: true
      });
      var m = new THREE.Mesh(geo, mat);
      group.add(m); meshes.push(m);
      var eg = new THREE.LineSegments(
        new THREE.EdgesGeometry(geo, 18),
        new THREE.LineBasicMaterial({ color: colors().edge, transparent: true, opacity: 0.85 })
      );
      group.add(eg); edges.push(eg);
      return m;
    }

    /* --------------------------------------------------------- geometries */
    function rebuild() {
      clear();
      var C = colors();
      var a, b, h, r, info;

      if (kind === 'prism') {
        var shape = (fig.getAttribute('data-shape') || 'rect');
        h = val('h', 4);
        if (shape === 'tri') {
          a = val('a', 4); b = val('b', 3);          /* legs of a right triangle */
          var s = new THREE.Shape();
          s.moveTo(-a / 2, -b / 2); s.lineTo(a / 2, -b / 2); s.lineTo(-a / 2, b / 2); s.closePath();
          var geo = new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: false });
          geo.rotateX(-Math.PI / 2); geo.translate(0, -h / 2, 0);
          addSolid(geo, C.face);
          var hyp = Math.hypot(a, b), base = a * b / 2, per = a + b + hyp;
          info = {
            base: base, per: per, h: h,
            lat: per * h, tot: per * h + 2 * base, vol: base * h,
            text: 'ปริซึมสามเหลี่ยมมุมฉาก  ขา ' + a + ' × ' + b +
                  ' , สูง ' + h + ' พื้นที่ฐาน = ' + base.toFixed(2) +
                  ' , ความยาวรอบรูปฐาน = ' + per.toFixed(2)
          };
        } else {
          a = val('a', 5); b = val('b', 3);
          addSolid(new THREE.BoxGeometry(a, h, b), C.face);
          var bse = a * b, pr = 2 * (a + b);
          info = {
            base: bse, per: pr, h: h,
            lat: pr * h, tot: pr * h + 2 * bse, vol: bse * h,
            text: 'ปริซึมสี่เหลี่ยมมุมฉาก ' + a + ' × ' + b + ' × ' + h
          };
        }
      } else {
        r = val('r', 2.2); h = val('h', 5);
        addSolid(new THREE.CylinderGeometry(r, r, h, 56, 1, false), C.face);
        var bs = Math.PI * r * r, pc = 2 * Math.PI * r;
        info = {
          base: bs, per: pc, h: h,
          lat: pc * h, tot: pc * h + 2 * bs, vol: bs * h,
          text: 'ทรงกระบอก r = ' + r + ' , h = ' + h
        };
      }

      applyMode();
      report(info);
      return info;
    }

    function report(info) {
      if (out) {
        out.textContent = 'ผิวข้าง ' + info.lat.toFixed(2) +
                          '  ·  ผิวทั้งหมด ' + info.tot.toFixed(2) +
                          '  ·  ปริมาตร ' + info.vol.toFixed(2);
      }
      var sel = {
        'f-shape': info.text,
        'f-lat': 'พื้นที่ผิวข้าง = (ความยาวรอบรูปฐาน) × (สูง) = ' +
                 info.per.toFixed(2) + ' × ' + info.h.toFixed(2) + ' = ' + info.lat.toFixed(2),
        'f-tot': 'พื้นที่ผิวทั้งหมด = ผิวข้าง + 2(พื้นที่ฐาน) = ' +
                 info.lat.toFixed(2) + ' + 2(' + info.base.toFixed(2) + ') = ' + info.tot.toFixed(2),
        'f-vol': 'ปริมาตร = (พื้นที่ฐาน) × (สูง) = ' +
                 info.base.toFixed(2) + ' × ' + info.h.toFixed(2) + ' = ' + info.vol.toFixed(2)
      };
      Object.keys(sel).forEach(function (k) {
        var e = fig.querySelector('[data-out="' + k + '"]');
        if (e) e.textContent = sel[k];
      });
    }

    function applyMode() {
      meshes.forEach(function (m) {
        m.visible = state.mode !== 'wire';
        m.material.opacity = state.mode === 'xray' ? 0.26 : 0.9;
        m.material.needsUpdate = true;
      });
      edges.forEach(function (e) { e.visible = true; });
      /* cross-section: clip the solid with a moving plane */
      var plane = new THREE.Plane(new THREE.Vector3(0, -1, 0), state.slice);
      renderer.localClippingEnabled = state.mode === 'slice';
      meshes.forEach(function (m) {
        m.material.clippingPlanes = state.mode === 'slice' ? [plane] : null;
        m.material.needsUpdate = true;
      });
    }

    /* ------------------------------------------------------------ resize */
    function resize() {
      var w = canvas.clientWidth || fig.clientWidth || 600;
      var hh = Math.round(w / 1.6);
      renderer.setSize(w, hh, false);
      cam.aspect = w / hh;
      cam.updateProjectionMatrix();
    }
    window.addEventListener('resize', resize);

    /* ------------------------------------------------------------ events */
    ['a', 'b', 'h', 'r'].forEach(function (n) {
      var i = input(n);
      if (i) i.addEventListener('input', function () {
        rebuild();
        var lbl = ctl.querySelector('[data-val="' + n + '"]');
        if (lbl) lbl.textContent = i.value;
      });
    });
    var si = input('slice');
    if (si) si.addEventListener('input', function () {
      state.slice = parseFloat(si.value); applyMode();
    });

    if (ctl) ctl.addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-act]');
      if (!b || !ctl.contains(b)) return;
      var a = b.getAttribute('data-act');
      if (a === 'spin') {
        state.spin = !state.spin;
        b.setAttribute('aria-pressed', state.spin ? 'true' : 'false');
        return;
      }
      state.mode = a;
      ctl.querySelectorAll('[data-act][data-group="mode"]').forEach(function (o) {
        o.setAttribute('aria-pressed', o.getAttribute('data-act') === a ? 'true' : 'false');
      });
      applyMode();
    });

    /* drag to orbit */
    var drag = false, last = null;
    function dn(e) { drag = true; last = ptOf(e); e.preventDefault(); }
    function mv(e) {
      if (!drag) return;
      var p = ptOf(e);
      group.rotation.y += (p.x - last.x) * 0.012;
      group.rotation.x = Math.max(-0.9, Math.min(0.9, group.rotation.x + (p.y - last.y) * 0.008));
      last = p; e.preventDefault();
    }
    function up() { drag = false; }
    function ptOf(e) {
      var t = e.touches ? e.touches[0] : e;
      return { x: t.clientX, y: t.clientY };
    }
    canvas.addEventListener('mousedown', dn);
    canvas.addEventListener('touchstart', dn, { passive: false });
    window.addEventListener('mousemove', mv);
    window.addEventListener('touchmove', mv, { passive: false });
    window.addEventListener('mouseup', up);
    window.addEventListener('touchend', up);
    canvas.style.cursor = 'grab';

    window.addEventListener('themechange', function () {
      var C = colors();
      meshes.forEach(function (m) { m.material.color.copy(C.face); });
      edges.forEach(function (e) { e.material.color.copy(C.edge); });
    });

    /* --------------------------------------------------------------- loop */
    resize();
    rebuild();
    group.rotation.y = -0.5;
    group.rotation.x = 0.18;

    var visible = true;
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) { visible = es[0].isIntersecting; })
        .observe(canvas);
    }
    (function frame() {
      requestAnimationFrame(frame);
      if (!visible) return;
      if (state.spin && !drag && !REDUCED) group.rotation.y += 0.0042;
      renderer.render(scene, cam);
    })();
  }

  /* THREE arrives via a deferred CDN script, so wait for window load. */
  if (document.readyState === 'complete') boot();
  else window.addEventListener('load', boot);
})();
