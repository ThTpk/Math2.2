/* ===========================================================================
   viz.js — interactive / animated math figures
   ---------------------------------------------------------------------------
   Every figure is authored as a complete static SVG on the server.  This file
   only *enhances* it: without JavaScript the figure still carries its whole
   meaning, and under prefers-reduced-motion all tweening is skipped (the end
   state is applied instantly).
   Figures opt in with  <figure class="fig" data-viz="name">.
   ========================================================================= */
(function () {
  'use strict';

  var REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var NS = 'http://www.w3.org/2000/svg';
  var R = {};            // registry: name -> init(ctx)

  /* ======================================================= tiny helpers == */
  function num(v, d) { var n = parseFloat(v); return isNaN(n) ? d : n; }
  function fmt(v, nd) {
    if (nd === undefined) nd = 2;
    var s = v.toFixed(nd);
    return s.replace(/\.?0+$/, '') || '0';
  }
  function deg(r) { return r * 180 / Math.PI; }
  function rad(d) { return d * Math.PI / 180; }
  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }

  /* vector ops on {x,y} */
  function pt(x, y) { return { x: x, y: y }; }
  function add(a, b) { return pt(a.x + b.x, a.y + b.y); }
  function sub(a, b) { return pt(a.x - b.x, a.y - b.y); }
  function mul(a, k) { return pt(a.x * k, a.y * k); }
  function len(a) { return Math.hypot(a.x, a.y); }
  function nrm(a) { var d = len(a) || 1; return pt(a.x / d, a.y / d); }
  function perp(a) { return pt(-a.y, a.x); }
  function lerp(a, b, t) { return pt(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t); }
  function mid(a, b) { return lerp(a, b, 0.5); }
  function dist(a, b) { return Math.hypot(b.x - a.x, b.y - a.y); }
  function polar(c, r, d) { return pt(c.x + r * Math.cos(rad(d)), c.y - r * Math.sin(rad(d))); }
  function angOf(c, p) { return (deg(Math.atan2(c.y - p.y, p.x - c.x)) + 360) % 360; }
  function rot(p, d, o) {
    o = o || pt(0, 0);
    var a = rad(d), c = Math.cos(a), s = Math.sin(a);
    var dx = p.x - o.x, dy = p.y - o.y;
    return pt(o.x + dx * c - dy * s, o.y + dx * s + dy * c);
  }
  function footOf(p, a, b) {
    var ab = sub(b, a), ap = sub(p, a);
    var t = (ap.x * ab.x + ap.y * ab.y) / (ab.x * ab.x + ab.y * ab.y);
    return lerp(a, b, t);
  }
  function inter(a, b, c, d) {
    var den = (a.x - b.x) * (c.y - d.y) - (a.y - b.y) * (c.x - d.x);
    if (Math.abs(den) < 1e-9) return null;
    var t = ((a.x - c.x) * (c.y - d.y) - (a.y - c.y) * (c.x - d.x)) / den;
    return pt(a.x + t * (b.x - a.x), a.y + t * (b.y - a.y));
  }
  /* signed angle ∠ a-v-b in degrees, 0..180 */
  function angle3(a, v, b) {
    var u = nrm(sub(a, v)), w = nrm(sub(b, v));
    return deg(Math.acos(clamp(u.x * w.x + u.y * w.y, -1, 1)));
  }
  function triArea(a, b, c) {
    return Math.abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2;
  }

  /* ---------------------------------------------------------- svg writes -- */
  function set(el, a) { if (el) for (var k in a) el.setAttribute(k, a[k]); }
  function txt(el, s) { if (el) el.textContent = s; }
  function lineTo(el, a, b) { set(el, { x1: a.x, y1: a.y, x2: b.x, y2: b.y }); }
  function moveC(el, p, r) { if (el) { set(el, { cx: p.x, cy: p.y }); if (r != null) set(el, { r: r }); } }
  function polyPts(el, arr) {
    set(el, { points: arr.map(function (p) { return p.x.toFixed(2) + ',' + p.y.toFixed(2); }).join(' ') });
  }
  function pathD(el, d) { set(el, { d: d }); }
  function dSeg(arr, close) {
    return 'M ' + arr.map(function (p) { return p.x.toFixed(2) + ' ' + p.y.toFixed(2); }).join(' L ') + (close ? ' Z' : '');
  }
  function dArc(c, r, a0, a1) {
    var p0 = polar(c, r, a0), p1 = polar(c, r, a1);
    var sweep = ((a1 - a0) % 360 + 360) % 360;
    return 'M ' + p0.x.toFixed(2) + ' ' + p0.y.toFixed(2) + ' A ' + r.toFixed(2) + ' ' + r.toFixed(2) +
           ' 0 ' + (sweep > 180 ? 1 : 0) + ' 0 ' + p1.x.toFixed(2) + ' ' + p1.y.toFixed(2);
  }
  /* arc marking angle a-v-b */
  function dAngle(v, a, b, r) {
    var a0 = angOf(v, a), a1 = angOf(v, b);
    if (((a1 - a0) % 360 + 360) % 360 > 180) { var t = a0; a0 = a1; a1 = t; }
    return dArc(v, r, a0, a1);
  }
  function moveText(el, p, dx, dy) {
    if (el) set(el, { x: p.x + (dx || 0), y: p.y + (dy || 0) });
  }
  function mkEl(name, attrs, parent) {
    var e = document.createElementNS(NS, name);
    set(e, attrs || {});
    if (parent) parent.appendChild(e);
    return e;
  }

  /* --------------------------------------------------------------- drag --- */
  function svgPoint(svg, ev) {
    var r = svg.getBoundingClientRect();
    var vb = svg.viewBox.baseVal;
    var cx = (ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left;
    var cy = (ev.touches ? ev.touches[0].clientY : ev.clientY) - r.top;
    return pt(vb.x + cx / r.width * vb.width, vb.y + cy / r.height * vb.height);
  }

  function draggable(svg, handle, onMove) {
    if (!handle) return;
    var active = false;
    function down(ev) { active = true; ev.preventDefault(); }
    function move(ev) { if (!active) return; ev.preventDefault(); onMove(svgPoint(svg, ev)); }
    function up() { active = false; }
    handle.addEventListener('mousedown', down);
    handle.addEventListener('touchstart', down, { passive: false });
    window.addEventListener('mousemove', move);
    window.addEventListener('touchmove', move, { passive: false });
    window.addEventListener('mouseup', up);
    window.addEventListener('touchend', up);
    /* keyboard access */
    handle.setAttribute('tabindex', '0');
    handle.addEventListener('keydown', function (ev) {
      var k = ev.key, step = ev.shiftKey ? 8 : 2, d = null;
      if (k === 'ArrowLeft') d = pt(-step, 0);
      else if (k === 'ArrowRight') d = pt(step, 0);
      else if (k === 'ArrowUp') d = pt(0, -step);
      else if (k === 'ArrowDown') d = pt(0, step);
      if (!d) return;
      ev.preventDefault();
      var c = pt(num(handle.getAttribute('cx'), 0), num(handle.getAttribute('cy'), 0));
      onMove(add(c, d));
    });
  }

  /* ------------------------------------------------------------- tween --- */
  function tween(ms, step, done) {
    if (REDUCED) { step(1); if (done) done(); return { stop: function () {} }; }
    var t0 = performance.now(), raf = null, killed = false;
    function frame(t) {
      if (killed) return;
      var k = clamp((t - t0) / ms, 0, 1);
      step(k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2);  /* easeInOutQuad */
      if (k < 1) raf = requestAnimationFrame(frame);
      else if (done) done();
    }
    raf = requestAnimationFrame(frame);
    return { stop: function () { killed = true; if (raf) cancelAnimationFrame(raf); } };
  }

  /* ------------------------------------------------------------- context -- */
  function ctxFor(fig) {
    var svg = fig.querySelector('svg');
    var ctl = fig.querySelector('.fig-ctrl');
    return {
      fig: fig, svg: svg, ctl: ctl,
      el: function (id) { return svg.querySelector('[data-id="' + id + '"]'); },
      all: function (id) { return Array.prototype.slice.call(svg.querySelectorAll('[data-id="' + id + '"]')); },
      p: function (k, d) { return num(fig.getAttribute('data-' + k), d); },
      input: function (name) { return ctl && ctl.querySelector('[data-input="' + name + '"]'); },
      out: function (s) { var o = ctl && ctl.querySelector('[data-readout]'); if (o) o.textContent = s; },
      btn: function (v) { return ctl && ctl.querySelector('[data-act="' + v + '"]'); },
      btns: function () { return ctl ? Array.prototype.slice.call(ctl.querySelectorAll('[data-act]')) : []; },
      onAct: function (fn) {
        if (!ctl) return;
        ctl.addEventListener('click', function (ev) {
          var b = ev.target.closest('[data-act]');
          if (!b || !ctl.contains(b)) return;
          fn(b.getAttribute('data-act'), b);
        });
      },
      press: function (v, group) {
        if (!ctl) return;
        ctl.querySelectorAll('[data-act]' + (group ? '[data-group="' + group + '"]' : ''))
           .forEach(function (b) {
             b.setAttribute('aria-pressed', b.getAttribute('data-act') === v ? 'true' : 'false');
           });
      },
      onInput: function (name, fn) {
        var i = this.input(name);
        if (i) i.addEventListener('input', function () { fn(parseFloat(i.value)); });
        return i;
      }
    };
  }

  /* ========================================================== 1. powers == */
  /* Visual meaning of a^n: repeated multiplication growing a strip, plus the
     reciprocal meaning of a negative exponent.                             */
  R.powers = function (c) {
    var base = c.p('base', 2);
    var cells = c.all('cell');            // 10 unit rectangles
    var x0 = c.p('x0', 60), y0 = c.p('y0', 150), unit = c.p('unit', 26);

    function render(n) {
      var val = Math.pow(base, n);
      var k = clamp(Math.abs(n), 0, cells.length);
      cells.forEach(function (el, i) {
        var on = i < k;
        el.setAttribute('opacity', on ? '1' : '0.12');
        el.setAttribute('class', on ? (n < 0 ? 'f-vt' : 'f-at') : 'f-it');
      });
      var bar = c.el('bar');
      if (bar) {
        /* log-scaled bar so 2^-3 .. 2^8 all fit */
        var w = clamp((Math.log(Math.abs(val)) / Math.log(base) + 4) / 12, 0.02, 1) * c.p('barw', 360);
        set(bar, { width: w.toFixed(1) });
      }
      txt(c.el('expr'), base + (n < 0 ? '⁻' : '') + supDigits(Math.abs(n)));
      txt(c.el('val'), n < 0 ? '1/' + fmt(Math.pow(base, -n), 0) + '  =  ' + val.toPrecision(4)
                             : fmt(val, val < 1 ? 6 : 0));
      txt(c.el('expand'), expandText(base, n));
      c.out(base + '^' + n + ' = ' + (n < 0 ? val.toPrecision(4) : fmt(val, 0)));
    }
    function supDigits(n) {
      var m = { 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹' };
      return String(n).split('').map(function (d) { return m[d]; }).join('');
    }
    function expandText(a, n) {
      if (n === 0) return 'นิยาม: a⁰ = 1  (เมื่อ a ≠ 0)';
      var k = Math.abs(n);
      var s = Array(k).fill(a).join(' × ');
      if (k > 6) s = a + ' × ' + a + ' × … × ' + a + '  (' + k + ' ตัว)';
      return n > 0 ? s : '1 / (' + s + ')';
    }
    c.onInput('n', render);
    render(num(c.input('n') && c.input('n').value, 3));
  };

  /* ================================================= 2. scientific notation */
  R.scinot = function (c) {
    var x0 = c.p('x0', 70), x1 = c.p('x1', 540), y = c.p('y', 96);
    var lo = -9, hi = 12;
    function render(e, m) {
      var t = (e - lo) / (hi - lo);
      var px = x0 + t * (x1 - x0);
      moveC(c.el('marker'), pt(px, y));
      moveC(c.el('halo'), pt(px, y));
      moveText(c.el('mlabel'), pt(px, y), 0, -22);
      var v = m * Math.pow(10, e);
      txt(c.el('mlabel'), fmt(m, 2) + '×10' + (e < 0 ? '⁻' : '') + String(Math.abs(e)).split('')
          .map(function (d) { return '⁰¹²³⁴⁵⁶⁷⁸⁹'[+d]; }).join(''));
      txt(c.el('plain'), plain(v));
      txt(c.el('note'), noteFor(e));
      c.out(fmt(m, 2) + ' × 10^' + e);
    }
    function plain(v) {
      if (v === 0) return '0';
      var a = Math.abs(v);
      if (a >= 1e15 || a < 1e-9) return v.toExponential(3);
      var s = a >= 1 ? v.toFixed(Math.max(0, 2 - Math.floor(Math.log10(a))))
                     : v.toFixed(Math.min(12, -Math.floor(Math.log10(a)) + 2));
      return s.replace(/(\.\d*?)0+$/, '$1').replace(/\.$/, '');
    }
    function noteFor(e) {
      if (e >= 11) return 'ระยะทางโลก–ดวงอาทิตย์ ≈ 1.5×10¹¹ เมตร';
      if (e >= 8) return 'ความเร็วแสง ≈ 3×10⁸ เมตร/วินาที';
      if (e >= 6) return 'ประชากรกรุงเทพฯ ≈ 5.5×10⁶ คน';
      if (e >= 3) return 'ความสูงภูเขา ≈ 2×10³ เมตร';
      if (e >= 0) return 'ขนาดของสิ่งของในชีวิตประจำวัน';
      if (e >= -3) return 'ความหนาเส้นผม ≈ 7×10⁻⁵ เมตร';
      if (e >= -7) return 'ขนาดไวรัส ≈ 1×10⁻⁷ เมตร';
      return 'รัศมีอะตอม ≈ 5×10⁻¹¹ เมตร';
    }
    var ei = c.onInput('e', function (v) { render(v, num(mi && mi.value, 1.5)); });
    var mi = c.onInput('m', function (v) { render(num(ei && ei.value, 8), v); });
    render(num(ei && ei.value, 8), num(mi && mi.value, 1.5));
  };

  /* =============================================== 3. prism net unfolding = */
  /* A rectangular prism unfolds into its net; the running total of the
     surface area is shown as each face lands.                              */
  R.prismnet = function (c) {
    var W = c.p('w', 120), H = c.p('h', 70), L = c.p('len', 170);
    var cx = c.p('cx', 300), cy = c.p('cy', 150);

    /* faces: [id, folded-corners, unfolded-corners] driven by t */
    function faceQuads(t) {
      /* closed (t=0) ~ an isometric-ish box; open (t=1) ~ flat cross net */
      var s = 0.45;                                 /* isometric squash */
      var o = pt(cx - L / 2, cy - H / 2);
      /* unfolded layout: left | front | right | back  with top above front */
      var U = {
        front: [pt(o.x, o.y), pt(o.x + L, o.y), pt(o.x + L, o.y + H), pt(o.x, o.y + H)],
        right: [pt(o.x + L, o.y), pt(o.x + L + W, o.y), pt(o.x + L + W, o.y + H), pt(o.x + L, o.y + H)],
        left:  [pt(o.x - W, o.y), pt(o.x, o.y), pt(o.x, o.y + H), pt(o.x - W, o.y + H)],
        top:   [pt(o.x, o.y - W), pt(o.x + L, o.y - W), pt(o.x + L, o.y), pt(o.x, o.y)],
        bottom:[pt(o.x, o.y + H), pt(o.x + L, o.y + H), pt(o.x + L, o.y + H + W), pt(o.x, o.y + H + W)],
        back:  [pt(o.x + L + W, o.y), pt(o.x + L + W + L, o.y), pt(o.x + L + W + L, o.y + H), pt(o.x + L + W, o.y + H)]
      };
      /* folded: project a box with depth W */
      var d = pt(W * 0.62, -W * s);
      var F = {
        front: [pt(o.x, o.y), pt(o.x + L, o.y), pt(o.x + L, o.y + H), pt(o.x, o.y + H)],
        right: [pt(o.x + L, o.y), add(pt(o.x + L, o.y), d), add(pt(o.x + L, o.y + H), d), pt(o.x + L, o.y + H)],
        left:  [add(pt(o.x, o.y), d), pt(o.x, o.y), pt(o.x, o.y + H), add(pt(o.x, o.y + H), d)],
        top:   [add(pt(o.x, o.y), d), add(pt(o.x + L, o.y), d), pt(o.x + L, o.y), pt(o.x, o.y)],
        bottom:[pt(o.x, o.y + H), pt(o.x + L, o.y + H), add(pt(o.x + L, o.y + H), d), add(pt(o.x, o.y + H), d)],
        back:  [add(pt(o.x, o.y), d), add(pt(o.x + L, o.y), d), add(pt(o.x + L, o.y + H), d), add(pt(o.x, o.y + H), d)]
      };
      var out = {};
      Object.keys(U).forEach(function (k) {
        out[k] = U[k].map(function (p, i) { return lerp(F[k][i], p, t); });
      });
      return out;
    }

    function render(t) {
      var q = faceQuads(t);
      Object.keys(q).forEach(function (k) {
        var el = c.el(k);
        if (el) {
          polyPts(el, q[k]);
          el.setAttribute('opacity', (k === 'back' && t < 0.25) ? '0' : '1');
        }
        var lb = c.el(k + '-lab');
        if (lb) {
          var m = pt((q[k][0].x + q[k][2].x) / 2, (q[k][0].y + q[k][2].y) / 2);
          moveText(lb, m, 0, 4);
          lb.setAttribute('opacity', t > 0.55 ? '1' : '0');
        }
      });
      var lat = 2 * (L + W) * H, bas = 2 * L * W;
      txt(c.el('f-lat'), 'ข้างรวม = ความยาวรอบรูปฐาน × สูง = ' + fmt(2 * (L + W) / 10, 1) + ' × ' + fmt(H / 10, 1));
      txt(c.el('f-tot'), 'พื้นที่ผิวทั้งหมด = ' + fmt((lat + bas) / 100, 1) + ' ตร.หน่วย');
      c.out(t < 0.1 ? 'รูปทรงปิด' : (t > 0.9 ? 'คลี่เต็มที่ — เห็นทั้ง 6 หน้า' : 'กำลังคลี่ ' + Math.round(t * 100) + '%'));
    }

    var anim = null;
    c.onAct(function (a) {
      if (anim) anim.stop();
      if (a === 'open') { c.press('open'); anim = tween(1100, render); }
      else if (a === 'close') { c.press('close'); anim = tween(900, function (k) { render(1 - k); }); }
    });
    var sl = c.onInput('t', function (v) { if (anim) anim.stop(); render(v); });
    render(sl ? parseFloat(sl.value) : 0);
  };

  /* ================================================ 4. cylinder unrolling = */
  R.cylnet = function (c) {
    var r = c.p('r', 42), h = c.p('h', 96);
    var cx = c.p('cx', 150), cy = c.p('cy', 120);
    var C = 2 * Math.PI * r;

    function render(t) {
      /* the lateral surface goes from a cylinder silhouette to a C × h rect */
      var w = C * t + (2 * r) * (1 - t);
      var el = c.el('lat');
      if (el) set(el, { x: cx - r, y: cy - h / 2, width: w.toFixed(1), height: h });
      /* top & bottom ellipses flatten into circles sliding aside */
      var sq = 1 - t;                           /* ellipse squash */
      var top = c.el('top'), bot = c.el('bot');
      if (top) set(top, { cx: cx - r + (t ? w + r + 14 : r), cy: cy - h / 2 + (t ? -r - 10 : 0) * 0 + (t ? 0 : 0),
                          rx: r, ry: (r * sq + r * t).toFixed(1) });
      if (top) set(top, { cx: (cx - r + (t > 0.05 ? w + r + 16 : r)).toFixed(1),
                          cy: (cy - h / 2 + (t > 0.05 ? 0 : 0)).toFixed(1),
                          rx: r, ry: (r * (0.32 + 0.68 * t)).toFixed(1) });
      if (bot) set(bot, { cx: (cx - r + (t > 0.05 ? w + r + 16 : r)).toFixed(1),
                          cy: (cy + h / 2 + (t > 0.05 ? 0 : 0)).toFixed(1),
                          rx: r, ry: (r * (0.32 + 0.68 * t)).toFixed(1) });
      var cl = c.el('circ-lab');
      if (cl) { moveText(cl, pt(cx - r + w / 2, cy - h / 2), 0, -10); cl.setAttribute('opacity', t > 0.5 ? '1' : '0'); }
      var gl = c.el('gen-lab');
      if (gl) gl.setAttribute('opacity', t > 0.5 ? '1' : '0');
      txt(c.el('f-lat'), 'ผิวข้าง = 2πr·h = ' + fmt(C * h / 100, 1));
      txt(c.el('f-tot'), 'ผิวทั้งหมด = 2πr(r + h) = ' + fmt(2 * Math.PI * r * (r + h) / 100, 1));
      c.out(t > 0.9 ? 'คลี่แล้ว: ผิวข้างคือสี่เหลี่ยมผืนผ้า 2πr × h' : 'ทรงกระบอก');
    }
    var anim = null;
    c.onAct(function (a) {
      if (anim) anim.stop();
      if (a === 'open') { c.press('open'); anim = tween(1200, render); }
      else { c.press('close'); anim = tween(900, function (k) { render(1 - k); }); }
    });
    var sl = c.onInput('t', function (v) { if (anim) anim.stop(); render(v); });
    render(sl ? parseFloat(sl.value) : 0);
  };

  /* ============================================ 6. parallel lines + angles */
  R.parallel = function (c) {
    var y1 = c.p('y1', 72), y2 = c.p('y2', 188);
    var xl = c.p('xl', 40), xr = c.p('xr', 560);
    var pivot = pt(c.p('px', 300), (y1 + y2) / 2);
    var state = { a: c.p('a0', 58), mode: 'corr' };

    var PAIRS = {
      corr:  { label: 'มุมแย้งเท่ากัน (corresponding)', ids: ['a1', 'b1'], note: 'มุมในตำแหน่งเดียวกันของจุดตัดสองจุด' },
      alt:   { label: 'มุมแย้ง (alternate interior)', ids: ['a4', 'b2'], note: 'อยู่คนละข้างของเส้นตัด และอยู่ภายในเส้นขนาน' },
      coint: { label: 'มุมภายในข้างเดียวกัน', ids: ['a3', 'b2'], note: 'รวมกันได้ 180°' },
      vert:  { label: 'มุมตรงข้าม (vertical)', ids: ['a1', 'a3'], note: 'เกิดจากเส้นตรงสองเส้นตัดกัน' }
    };

    function render() {
      var a = state.a;
      var dir = pt(Math.cos(rad(a)), -Math.sin(rad(a)));
      /* transversal through pivot, clipped generously */
      var p1 = add(pivot, mul(dir, 260)), p2 = sub(pivot, mul(dir, 260));
      lineTo(c.el('tr'), p2, p1);
      var A = inter(p2, p1, pt(xl, y1), pt(xr, y1));
      var B = inter(p2, p1, pt(xl, y2), pt(xr, y2));
      if (!A || !B) return;
      moveC(c.el('ptA'), A); moveC(c.el('ptB'), B);
      moveC(c.el('handle'), add(pivot, mul(dir, 150)));
      moveC(c.el('halo'), add(pivot, mul(dir, 150)));
      moveText(c.el('labA'), A, -14, -8);
      moveText(c.el('labB'), B, -14, 18);

      /* 4 angles at each intersection, numbered CCW from the +x direction */
      var ref = { a: A, b: B };
      ['a', 'b'].forEach(function (k) {
        var V = ref[k];
        var along = pt(1, 0);
        var arms = [add(V, mul(dir, 40)), add(V, mul(along, 40)),
                    sub(V, mul(dir, 40)), sub(V, mul(along, 40))];
        for (var i = 0; i < 4; i++) {
          var el = c.el(k + (i + 1));
          if (el) pathD(el, dAngle(V, arms[i], arms[(i + 1) % 4], 26 + (i % 2) * 4));
          var t2 = c.el(k + (i + 1) + '-t');
          if (t2) {
            var bis = nrm(add(nrm(sub(arms[i], V)), nrm(sub(arms[(i + 1) % 4], V))));
            moveText(t2, add(V, mul(bis, 44)), 0, 4);
            var v = angle3(arms[i], V, arms[(i + 1) % 4]);
            txt(t2, Math.round(v) + '°');
          }
        }
      });

      var P = PAIRS[state.mode];
      ['a1', 'a2', 'a3', 'a4', 'b1', 'b2', 'b3', 'b4'].forEach(function (id) {
        var on = P.ids.indexOf(id) >= 0;
        [c.el(id), c.el(id + '-t')].forEach(function (e) {
          if (!e) return;
          e.classList.toggle('off', !on);
          if (e.tagName === 'path') e.setAttribute('class', (on ? 's-accent' : 's-muted') + ' hl' + (on ? '' : ' off'));
        });
      });
      txt(c.el('pair-label'), P.label);
      txt(c.el('pair-note'), P.note);
      var v1 = Math.round(angleById(P.ids[0], A, B, dir));
      var v2 = Math.round(angleById(P.ids[1], A, B, dir));
      var rel = state.mode === 'coint'
        ? v1 + '° + ' + v2 + '° = ' + (v1 + v2) + '°'
        : v1 + '° = ' + v2 + '°';
      txt(c.el('pair-val'), rel);
      c.out(P.label + ' · ' + rel);
    }
    function angleById(id, A, B, dir) {
      var V = id[0] === 'a' ? A : B, i = +id[1] - 1;
      var along = pt(1, 0);
      var arms = [add(V, mul(dir, 40)), add(V, mul(along, 40)), sub(V, mul(dir, 40)), sub(V, mul(along, 40))];
      return angle3(arms[i], V, arms[(i + 1) % 4]);
    }

    draggable(c.svg, c.el('handle'), function (p) {
      var d = sub(p, pivot);
      var a = angOf(pivot, p);
      /* keep the transversal clearly oblique */
      a = clamp(((a % 180) + 180) % 180, 22, 158);
      state.a = a;
      render();
    });
    c.onAct(function (a) {
      if (PAIRS[a]) { state.mode = a; c.press(a, 'pair'); render(); }
    });
    render();
  };

  /* ============================================= 7. exterior angle of a tri */
  R.extangle = function (c) {
    var A = pt(c.p('ax', 110), c.p('ay', 190)), B = pt(c.p('bx', 300), c.p('by', 190));
    var Cv = pt(c.p('cx', 210), c.p('cy', 72));
    function render() {
      polyPts(c.el('tri'), [A, B, Cv]);
      var ext = add(B, mul(nrm(sub(B, A)), 120));
      lineTo(c.el('ext'), B, ext);
      moveC(c.el('handle'), Cv); moveC(c.el('halo'), Cv);
      moveText(c.el('labA'), A, -16, 6);
      moveText(c.el('labB'), B, 4, 20);
      moveText(c.el('labC'), Cv, 0, -12);
      moveText(c.el('labD'), ext, 10, 6);
      pathD(c.el('mA'), dAngle(A, B, Cv, 26));
      pathD(c.el('mC'), dAngle(Cv, A, B, 24));
      pathD(c.el('mExt'), dAngle(B, Cv, ext, 30));
      pathD(c.el('mInt'), dAngle(B, A, Cv, 22));
      var a = angle3(B, A, Cv), cc = angle3(A, Cv, B), bInt = angle3(A, B, Cv);
      var e = 180 - bInt;
      moveText(c.el('tA'), add(A, mul(nrm(add(nrm(sub(B, A)), nrm(sub(Cv, A)))), 42)), 0, 4);
      moveText(c.el('tC'), add(Cv, mul(nrm(add(nrm(sub(A, Cv)), nrm(sub(B, Cv)))), 40)), 0, 4);
      moveText(c.el('tExt'), add(B, mul(nrm(add(nrm(sub(Cv, B)), nrm(sub(ext, B)))), 48)), 0, 4);
      txt(c.el('tA'), Math.round(a) + '°');
      txt(c.el('tC'), Math.round(cc) + '°');
      txt(c.el('tExt'), Math.round(e) + '°');
      txt(c.el('eq'), Math.round(a) + '° + ' + Math.round(cc) + '° = ' + Math.round(a + cc) + '°  =  มุมภายนอก');
      c.out('Â + Ĉ = ' + Math.round(a + cc) + '° = มุมภายนอกที่ B');
    }
    draggable(c.svg, c.el('handle'), function (p) {
      Cv = pt(clamp(p.x, 60, 380), clamp(p.y, 36, 160));
      render();
    });
    render();
  };

  /* ==================================================== 8. transformations */
  R.transform = function (c) {
    var o = pt(c.p('ox', 300), c.p('oy', 170)), u = c.p('unit', 26);
    var base = [pt(1, 1), pt(4, 1), pt(2, 3)];          /* lattice coords */
    var state = { mode: 'translate', k: 1 };
    function toPx(q) { return pt(o.x + q.x * u, o.y - q.y * u); }

    function imageOf(mode, t) {
      return base.map(function (q) {
        if (mode === 'translate') return pt(q.x + 5 * t, q.y - 3 * t);
        if (mode === 'reflect') {
          /* reflect in the y-axis, tweened as a flip through x=0 */
          return pt(q.x * (1 - 2 * t), q.y);
        }
        /* rotate 90° CCW about the origin */
        var a = rad(90 * t);
        return pt(q.x * Math.cos(a) - q.y * Math.sin(a), q.x * Math.sin(a) + q.y * Math.cos(a));
      });
    }
    function render(t) {
      var img = imageOf(state.mode, t);
      polyPts(c.el('pre'), base.map(toPx));
      polyPts(c.el('img'), img.map(toPx));
      ['A', 'B', 'C'].forEach(function (n, i) {
        moveC(c.el('pt' + n), toPx(base[i]));
        moveC(c.el('ipt' + n), toPx(img[i]));
        moveText(c.el('lab' + n), toPx(base[i]), -12, -8);
        moveText(c.el('ilab' + n), toPx(img[i]), 12, -8);
        var tr = c.el('tr' + n);
        if (tr) {
          pathD(tr, dSeg([toPx(base[i]), toPx(img[i])]));
          tr.setAttribute('opacity', state.mode === 'translate' && t > 0.05 ? '0.9' : '0');
        }
      });
      /* mirror line / centre of rotation */
      var ml = c.el('mirror');
      if (ml) ml.setAttribute('opacity', state.mode === 'reflect' ? '1' : '0');
      var ctr = c.el('centre');
      if (ctr) ctr.setAttribute('opacity', state.mode === 'rotate' ? '1' : '0');
      var vec = c.el('vector');
      if (vec) {
        vec.setAttribute('opacity', state.mode === 'translate' ? '1' : '0');
        lineTo(vec, toPx(pt(0, 0)), toPx(pt(5, -3)));
      }
      var rule = { translate: '(x, y) → (x + 5, y − 3)', reflect: '(x, y) → (−x, y)', rotate: '(x, y) → (−y, x)' };
      txt(c.el('rule'), rule[state.mode]);
      var f = imageOf(state.mode, 1);
      txt(c.el('map'), 'A(1,1) → A′(' + fmt(f[0].x, 0) + ',' + fmt(f[0].y, 0) + ')   ' +
                       'B(4,1) → B′(' + fmt(f[1].x, 0) + ',' + fmt(f[1].y, 0) + ')   ' +
                       'C(2,3) → C′(' + fmt(f[2].x, 0) + ',' + fmt(f[2].y, 0) + ')');
      c.out(rule[state.mode] + ' · พื้นที่คงเดิม');
    }
    var anim = null;
    function play() { if (anim) anim.stop(); anim = tween(900, render); }
    c.onAct(function (a) {
      if (a === 'play') { play(); return; }
      if (a === 'reset') { if (anim) anim.stop(); render(0); return; }
      state.mode = a; c.press(a, 'mode'); render(0); play();
    });
    render(1);
  };

  /* =================================================== 9. tessellation ==== */
  R.tessel = function (c) {
    var tiles = c.all('tile');
    var anim = null;
    function render(t) {
      tiles.forEach(function (el, i) {
        var k = clamp(t * tiles.length - i, 0, 1);
        el.setAttribute('opacity', (0.15 + 0.85 * k).toFixed(2));
        var tx = num(el.getAttribute('data-tx'), 0), ty = num(el.getAttribute('data-ty'), 0);
        var rt = num(el.getAttribute('data-rot'), 0);
        var ox = num(el.getAttribute('data-ox'), 0), oy = num(el.getAttribute('data-oy'), 0);
        el.setAttribute('transform',
          'translate(' + (tx * k).toFixed(1) + ',' + (ty * k).toFixed(1) + ') ' +
          'rotate(' + (rt * k).toFixed(1) + ',' + ox + ',' + oy + ')');
      });
      c.out(t >= 1 ? 'ปูเต็มระนาบ — ไม่มีช่องว่างและไม่ทับกัน' : 'กำลังปู ' + Math.round(t * 100) + '%');
    }
    c.onAct(function (a) {
      if (anim) anim.stop();
      if (a === 'play') anim = tween(1800, render);
      else render(0);
    });
    render(1);
  };

  /* ================================================ 10. congruence overlay */
  R.congruence = function (c) {
    var T1 = [pt(c.p('ax', 76), c.p('ay', 178)), pt(c.p('bx', 196), c.p('by', 178)),
              pt(c.p('cx', 128), c.p('cy', 86))];
    var off = pt(c.p('dx', 250), c.p('dy', 0));
    /* second triangle is the first, rotated and shifted */
    var ROT = c.p('rot', -28);
    var T2 = T1.map(function (p) { return add(rot(p, ROT, T1[0]), off); });
    var state = { crit: 'sss' };
    var CRIT = {
      sss: { name: 'ด.ด.ด. (SSS)', parts: ['s1', 's2', 's3'], note: 'ด้านสามคู่ยาวเท่ากัน' },
      sas: { name: 'ด.ม.ด. (SAS)', parts: ['s1', 'a1', 's3'], note: 'ด้าน–มุมระหว่างด้าน–ด้าน' },
      asa: { name: 'ม.ด.ม. (ASA)', parts: ['a1', 's1', 'a2'], note: 'มุม–ด้านระหว่างมุม–มุม' },
      aas: { name: 'ม.ม.ด. (AAS)', parts: ['a1', 'a2', 's2'], note: 'มุมสองคู่และด้านที่ไม่อยู่ระหว่างมุม' },
      rhs: { name: 'ฉ.ด.ด. (RHS)', parts: ['a3', 's2', 's3'], note: 'มุมฉาก–ด้านตรงข้ามมุมฉาก–ด้านประกอบ' }
    };
    function render(t) {
      polyPts(c.el('t1'), T1);
      polyPts(c.el('t2'), T2);
      /* the moving copy slides from T2 back onto T1 */
      var mv = T2.map(function (p, i) { return lerp(p, T1[i], t); });
      var m = c.el('moving');
      if (m) { polyPts(m, mv); m.setAttribute('opacity', t > 0.02 ? '1' : '0'); }
      var P = CRIT[state.crit];
      ['s1', 's2', 's3', 'a1', 'a2', 'a3'].forEach(function (id) {
        var on = P.parts.indexOf(id) >= 0;
        c.all(id).forEach(function (e) {
          e.classList.toggle('off', !on);
          e.setAttribute('opacity', on ? '1' : '0.14');
        });
      });
      txt(c.el('crit-name'), P.name);
      txt(c.el('crit-note'), P.note);
      c.out(P.name + ' — ' + P.note);
    }
    var anim = null;
    c.onAct(function (a) {
      if (a === 'play') { if (anim) anim.stop(); anim = tween(1400, render); return; }
      if (a === 'reset') { if (anim) anim.stop(); render(0); return; }
      if (CRIT[a]) { state.crit = a; c.press(a, 'crit'); render(0); }
    });
    render(0);
  };

  /* ================================================ 11. stepped proof ===== */
  R.proof = function (c) {
    var steps = Array.prototype.slice.call(c.svg.querySelectorAll('[data-step]'))
      .map(function (e) { return { el: e, n: +e.getAttribute('data-step') }; });
    var rows = Array.prototype.slice.call(c.fig.querySelectorAll('[data-prow]'));
    var maxN = steps.reduce(function (m, s) { return Math.max(m, s.n); }, 0);
    maxN = Math.max(maxN, rows.reduce(function (m, r) { return Math.max(m, +r.getAttribute('data-prow')); }, 0));
    var cur = maxN;
    function render() {
      steps.forEach(function (s) { s.el.classList.toggle('pending', s.n > cur); });
      rows.forEach(function (r) {
        var on = +r.getAttribute('data-prow') <= cur;
        r.style.opacity = on ? '1' : '0.2';
      });
      c.out('ขั้นที่ ' + cur + ' / ' + maxN);
      var p = c.btn('prev'), n = c.btn('next');
      if (p) p.disabled = cur <= 0;
      if (n) n.disabled = cur >= maxN;
    }
    c.onAct(function (a) {
      if (a === 'prev') cur = Math.max(0, cur - 1);
      else if (a === 'next') cur = Math.min(maxN, cur + 1);
      else if (a === 'all') cur = maxN;
      else if (a === 'reset') cur = 0;
      render();
    });
    render();
  };

  /* ================================================= 12. Menelaus theorem */
  R.menelaus = function (c) {
    var A = pt(c.p('ax', 110), c.p('ay', 214)), B = pt(c.p('bx', 330), c.p('by', 214)),
        Cv = pt(c.p('cx', 236), c.p('cy', 70));
    var state = { s: c.p('s0', 0.34) };           /* parameter of F on AB */
    function render() {
      polyPts(c.el('tri'), [A, B, Cv]);
      /* F on AB, E on AC; D = BC ∩ FE  (transversal F–E–D) */
      var F = lerp(A, B, state.s);
      var E = lerp(A, Cv, 0.62);
      var dir = nrm(sub(E, F));
      var D = inter(F, add(F, mul(dir, 1000)), B, Cv);
      if (!D) return;
      lineTo(c.el('trans'), sub(F, mul(dir, 60)), add(F, mul(dir, dist(F, D) + 60)));
      moveC(c.el('ptD'), D); moveC(c.el('ptE'), E); moveC(c.el('ptF'), F);
      moveC(c.el('handle'), F); moveC(c.el('halo'), F);
      moveText(c.el('labA'), A, -14, 8);
      moveText(c.el('labB'), B, 8, 18);
      moveText(c.el('labC'), Cv, 0, -12);
      moveText(c.el('labD'), D, 12, 2);
      moveText(c.el('labE'), E, 14, 0);
      moveText(c.el('labF'), F, 0, 20);
      var r1 = dist(A, F) / dist(F, B), r2 = dist(B, D) / dist(D, Cv), r3 = dist(Cv, E) / dist(E, A);
      txt(c.el('r1'), 'AF/FB = ' + fmt(r1, 3));
      txt(c.el('r2'), 'BD/DC = ' + fmt(r2, 3));
      txt(c.el('r3'), 'CE/EA = ' + fmt(r3, 3));
      txt(c.el('prod'), 'ผลคูณ = ' + fmt(r1 * r2 * r3, 3));
      c.out('(AF/FB)(BD/DC)(CE/EA) = ' + fmt(r1 * r2 * r3, 3) + ' ≈ 1');
    }
    draggable(c.svg, c.el('handle'), function (p) {
      var f = footOf(p, A, B);
      state.s = clamp(dist(A, f) / dist(A, B), 0.12, 0.78);
      render();
    });
    render();
  };

  /* ================================================ 13. area ratio ======== */
  R.arearatio = function (c) {
    var A = pt(c.p('ax', 180), c.p('ay', 62)), B = pt(c.p('bx', 70), c.p('by', 214)),
        Cv = pt(c.p('cx', 330), c.p('cy', 214));
    var state = { t: 0.42 };
    function render() {
      var D = lerp(B, Cv, state.t);
      polyPts(c.el('abd'), [A, B, D]);
      polyPts(c.el('adc'), [A, D, Cv]);
      lineTo(c.el('cev'), A, D);
      var H = footOf(A, B, Cv);
      lineTo(c.el('alt'), A, H);
      moveC(c.el('handle'), D); moveC(c.el('halo'), D);
      moveText(c.el('labA'), A, 0, -12);
      moveText(c.el('labB'), B, -14, 18);
      moveText(c.el('labC'), Cv, 14, 18);
      moveText(c.el('labD'), D, 0, 22);
      moveText(c.el('labH'), H, -4, 20);
      var s1 = triArea(A, B, D), s2 = triArea(A, D, Cv);
      var bd = dist(B, D), dc = dist(D, Cv);
      txt(c.el('ratio-len'), 'BD : DC = ' + fmt(bd / 10, 2) + ' : ' + fmt(dc / 10, 2) + '  = ' + fmt(bd / dc, 3));
      txt(c.el('ratio-area'), '[ABD] : [ADC] = ' + fmt(s1 / 100, 2) + ' : ' + fmt(s2 / 100, 2) + '  = ' + fmt(s1 / s2, 3));
      c.out('ฐานต่างกัน สูงเท่ากัน ⇒ อัตราส่วนพื้นที่ = อัตราส่วนฐาน = ' + fmt(s1 / s2, 3));
    }
    draggable(c.svg, c.el('handle'), function (p) {
      var f = footOf(p, B, Cv);
      state.t = clamp(dist(B, f) / dist(B, Cv), 0.1, 0.9);
      render();
    });
    render();
  };

  /* ============================================ 14. inscribed angle ======= */
  R.inscribed = function (c) {
    var O = pt(c.p('ox', 220), c.p('oy', 150)), r = c.p('r', 96);
    var aA = c.p('aa', 212), aB = c.p('ab', 328);     /* fixed chord ends */
    var state = { p: c.p('p0', 80) };
    function render() {
      var A = polar(O, r, aA), B = polar(O, r, aB), P = polar(O, r, state.p);
      moveC(c.el('circle'), O, r);
      moveC(c.el('ptO'), O); moveC(c.el('ptA'), A); moveC(c.el('ptB'), B);
      moveC(c.el('handle'), P); moveC(c.el('halo'), P);
      lineTo(c.el('pa'), P, A); lineTo(c.el('pb'), P, B);
      lineTo(c.el('oa'), O, A); lineTo(c.el('ob'), O, B);
      lineTo(c.el('chord'), A, B);
      pathD(c.el('arcAB'), dArc(O, r, aB, aA));
      pathD(c.el('mP'), dAngle(P, A, B, 30));
      pathD(c.el('mO'), dAngle(O, A, B, 34));
      moveText(c.el('labA'), A, -14, 4);
      moveText(c.el('labB'), B, 14, 4);
      moveText(c.el('labP'), P, 0, -14);
      moveText(c.el('labO'), O, -6, -10);
      var ip = angle3(A, P, B);
      var cen = ((aA - aB) % 360 + 360) % 360;
      var bisP = nrm(add(nrm(sub(A, P)), nrm(sub(B, P))));
      moveText(c.el('tP'), add(P, mul(bisP, 48)), 0, 4);
      var bisO = nrm(add(nrm(sub(A, O)), nrm(sub(B, O))));
      moveText(c.el('tO'), add(O, mul(bisO, 52)), 0, 4);
      txt(c.el('tP'), Math.round(ip) + '°');
      txt(c.el('tO'), Math.round(cen) + '°');
      txt(c.el('eq'), 'มุมที่จุดศูนย์กลาง ' + Math.round(cen) + '° = 2 × มุมในส่วนโค้ง ' + Math.round(ip) + '°');
      c.out('ลาก P ไปไหนบนส่วนโค้งเดียวกัน มุม P ก็ยังเท่ากับ ' + Math.round(ip) + '°');
    }
    draggable(c.svg, c.el('handle'), function (p) {
      var a = angOf(O, p);
      /* keep P on the major arc (outside the arc AB that the chord cuts off) */
      var lo = aB % 360, hi = aA % 360;   /* minor arc spans aB..aA going CCW */
      if (a > lo && a < hi) a = (a - lo < hi - a) ? lo - 6 : hi + 6;
      state.p = (a + 360) % 360;
      render();
    });
    render();
  };

  /* ================================= 15. chord ⟂ from centre bisects it === */
  R.chordperp = function (c) {
    var O = pt(c.p('ox', 190), c.p('oy', 156)), r = c.p('r', 104);
    var state = { d: c.p('d0', 46) };     /* distance from O to the chord */
    function render() {
      var d = state.d;
      var half = Math.sqrt(Math.max(1, r * r - d * d));
      var M = pt(O.x, O.y - d);
      var A = pt(M.x - half, M.y), B = pt(M.x + half, M.y);
      moveC(c.el('circle'), O, r);
      lineTo(c.el('chord'), A, B);
      lineTo(c.el('perp'), O, M);
      lineTo(c.el('ra'), O, A); lineTo(c.el('rb'), O, B);
      moveC(c.el('ptA'), A); moveC(c.el('ptB'), B); moveC(c.el('ptM'), M); moveC(c.el('ptO'), O);
      moveC(c.el('handle'), M); moveC(c.el('halo'), M);
      moveText(c.el('labA'), A, -14, 4);
      moveText(c.el('labB'), B, 14, 4);
      moveText(c.el('labM'), M, 0, -10);
      moveText(c.el('labO'), O, -4, 18);
      var rm = c.el('rightmark');
      if (rm) {
        var u = mul(nrm(sub(B, M)), 12), w = mul(nrm(sub(O, M)), 12);
        pathD(rm, dSeg([add(M, u), add(add(M, u), w), add(M, w)]));
      }
      var t1 = c.el('t-half1'), t2 = c.el('t-half2');
      moveText(t1, mid(A, M), 0, -9); moveText(t2, mid(M, B), 0, -9);
      txt(t1, fmt(half / 10, 2)); txt(t2, fmt(half / 10, 2));
      moveText(c.el('t-d'), mid(O, M), 12, 4);
      txt(c.el('t-d'), 'd = ' + fmt(d / 10, 2));
      txt(c.el('eq'), 'AM = MB = √(r² − d²) = √(' + fmt(r / 10, 1) + '² − ' + fmt(d / 10, 2) + '²) = ' + fmt(half / 10, 2));
      txt(c.el('note2'), d < 14 ? 'คอร์ดผ่านจุดศูนย์กลาง → เป็นเส้นผ่านศูนย์กลาง ยาวที่สุด'
                                : 'ยิ่งคอร์ดอยู่ไกลจุดศูนย์กลาง ยิ่งสั้นลง');
      c.out('d = ' + fmt(d / 10, 2) + ' → คอร์ดยาว ' + fmt(2 * half / 10, 2));
    }
    draggable(c.svg, c.el('handle'), function (p) {
      state.d = clamp(O.y - p.y, 0, r - 8);
      render();
    });
    render();
  };

  /* ============================== 16. tangent–chord (alternate segment) === */
  R.tangentchord = function (c) {
    var O = pt(c.p('ox', 210), c.p('oy', 160)), r = c.p('r', 98);
    var aT = c.p('at', 268);                     /* tangent point */
    var state = { b: c.p('b0', 20) };            /* chord end angle */
    /* which side of line ab does p fall on? */
    function side(a, b, p) {
      return (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);
    }

    function render() {
      var T = polar(O, r, aT), B = polar(O, r, state.b);
      var tdir = perp(nrm(sub(T, O)));
      lineTo(c.el('tangent'), sub(T, mul(tdir, 130)), add(T, mul(tdir, 130)));
      lineTo(c.el('chord'), T, B);
      moveC(c.el('circle'), O, r);
      moveC(c.el('ptT'), T); moveC(c.el('ptB'), B); moveC(c.el('ptO'), O);
      moveC(c.el('handle'), B); moveC(c.el('halo'), B);
      /* P sits at the middle of one of the two arcs cut off by chord TB */
      var aP = (state.b + (((aT - state.b) % 360 + 360) % 360) / 2 + 180) % 360;
      var P = polar(O, r, aP);
      moveC(c.el('ptP'), P);
      lineTo(c.el('pt1'), P, T); lineTo(c.el('pt2'), P, B);
      /* The tangent–chord angle equal to the inscribed angle at P is the one
         on the far side of the chord from P — pick that tangent ray. */
      var sP = side(T, B, P);
      var armPlus = add(T, mul(tdir, 44));
      var tArm = (side(T, B, armPlus) * sP < 0) ? armPlus : sub(T, mul(tdir, 44));
      pathD(c.el('mTan'), dAngle(T, tArm, B, 26));
      pathD(c.el('mP'), dAngle(P, T, B, 28));
      moveText(c.el('labT'), T, 0, 22);
      moveText(c.el('labB'), B, 14, -6);
      moveText(c.el('labP'), P, -14, 4);
      moveText(c.el('labO'), O, -4, -10);
      var at1 = angle3(tArm, T, B);
      var ap = angle3(T, P, B);
      moveText(c.el('tTan'), add(T, mul(nrm(add(nrm(sub(tArm, T)), nrm(sub(B, T)))), 42)), 0, 4);
      moveText(c.el('tP'), add(P, mul(nrm(add(nrm(sub(T, P)), nrm(sub(B, P)))), 46)), 0, 4);
      txt(c.el('tTan'), Math.round(at1) + '°');
      txt(c.el('tP'), Math.round(ap) + '°');
      txt(c.el('eq'), 'มุมระหว่างเส้นสัมผัสกับคอร์ด ' + Math.round(at1) +
                      '° = มุมในส่วนโค้งสลับ ' + Math.round(ap) + '°');
      c.out('tangent–chord = ' + Math.round(at1) + '° · alternate segment = ' + Math.round(ap) + '°');
    }
    draggable(c.svg, c.el('handle'), function (p) {
      var a = angOf(O, p);
      /* keep B away from T */
      var gap = ((a - aT) % 360 + 360) % 360;
      if (gap < 28) a = aT + 28; else if (gap > 332) a = aT - 28;
      state.b = (a + 360) % 360;
      render();
    });
    render();
  };

  /* ================================================ 17. cyclic quad ====== */
  R.cyclicquad = function (c) {
    var O = pt(c.p('ox', 210), c.p('oy', 152)), r = c.p('r', 98);
    var ang = [c.p('a1', 142), c.p('a2', 222), c.p('a3', 314), c.p('a4', 48)];
    var moving = 3;
    function render() {
      var V = ang.map(function (a) { return polar(O, r, a); });
      moveC(c.el('circle'), O, r);
      polyPts(c.el('quad'), V);
      ['A', 'B', 'C', 'D'].forEach(function (n, i) {
        moveC(c.el('pt' + n), V[i]);
        var out = nrm(sub(V[i], O));
        moveText(c.el('lab' + n), add(V[i], mul(out, 18)), 0, 5);
      });
      [0, 1, 2, 3].forEach(function (i) {
        var p = V[i], a = V[(i + 3) % 4], b = V[(i + 1) % 4];
        pathD(c.el('m' + i), dAngle(p, a, b, 26));
        var bis = nrm(add(nrm(sub(a, p)), nrm(sub(b, p))));
        moveText(c.el('t' + i), add(p, mul(bis, 42)), 0, 4);
        txt(c.el('t' + i), Math.round(angle3(a, p, b)) + '°');
      });
      moveC(c.el('handle'), V[moving]); moveC(c.el('halo'), V[moving]);
      var s02 = angle3(V[3], V[0], V[1]) + angle3(V[1], V[2], V[3]);
      var s13 = angle3(V[0], V[1], V[2]) + angle3(V[2], V[3], V[0]);
      txt(c.el('sum1'), 'Â + Ĉ = ' + Math.round(s02) + '°');
      txt(c.el('sum2'), 'B̂ + D̂ = ' + Math.round(s13) + '°');
      c.out('Â + Ĉ = ' + Math.round(s02) + '° · B̂ + D̂ = ' + Math.round(s13) + '°');
    }
    draggable(c.svg, c.el('handle'), function (p) {
      var a = angOf(O, p);
      /* keep the vertex order (D between C and A going CCW) */
      var lo = ang[2] + 12, hi = ang[0] + 360 - 12;
      var aa = a < ang[2] ? a + 360 : a;
      ang[3] = clamp(aa, lo, hi) % 360;
      render();
    });
    render();
  };

  /* ==================================================== 18. centroid ===== */
  R.centroid = function (c) {
    var A = pt(c.p('ax', 196), c.p('ay', 58)), B = pt(c.p('bx', 76), c.p('by', 216)),
        Cv = pt(c.p('cx', 328), c.p('cy', 216));
    function render() {
      var Ma = mid(B, Cv), Mb = mid(A, Cv), Mc = mid(A, B);
      var G = pt((A.x + B.x + Cv.x) / 3, (A.y + B.y + Cv.y) / 3);
      polyPts(c.el('tri'), [A, B, Cv]);
      lineTo(c.el('ma'), A, Ma); lineTo(c.el('mb'), B, Mb); lineTo(c.el('mc'), Cv, Mc);
      [['A', A], ['B', B], ['C', Cv]].forEach(function (x) {
        moveC(c.el('pt' + x[0]), x[1]);
      });
      moveC(c.el('ptG'), G);
      ['Ma', 'Mb', 'Mc'].forEach(function (n, i) { moveC(c.el('pt' + n), [Ma, Mb, Mc][i]); });
      moveText(c.el('labA'), A, 0, -12);
      moveText(c.el('labB'), B, -14, 16);
      moveText(c.el('labC'), Cv, 14, 16);
      moveText(c.el('labG'), G, 14, 4);
      moveText(c.el('labMa'), Ma, 16, 4);
      moveC(c.el('handle'), A); moveC(c.el('halo'), A);
      [[B, Cv], [A, Cv], [A, B]].forEach(function (e, i) {
        var el = c.all('tick')[i];
        if (!el) return;
        var m = mid(e[0], e[1]), u = mul(nrm(perp(nrm(sub(e[1], e[0])))), 7);
        pathD(el, dSeg([sub(m, u), add(m, u)]));
      });
      var ag = dist(A, G), gm = dist(G, Ma);
      txt(c.el('ratio'), 'AG : GM = ' + fmt(ag / 10, 2) + ' : ' + fmt(gm / 10, 2) + ' = ' + fmt(ag / gm, 2) + ' : 1');
      var s1 = triArea(A, B, G), s2 = triArea(B, Cv, G), s3 = triArea(Cv, A, G);
      txt(c.el('areas'), 'พื้นที่สามส่วนย่อย = ' + fmt(s1 / 100, 1) + ', ' + fmt(s2 / 100, 1) + ', ' + fmt(s3 / 100, 1) + ' (เท่ากัน)');
      c.out('เส้นมัธยฐานตัดกันที่ G โดย AG : GMa = 2 : 1');
    }
    draggable(c.svg, c.el('handle'), function (p) {
      A = pt(clamp(p.x, 60, 356), clamp(p.y, 30, 170));
      render();
    });
    render();
  };

  /* ================================= 19. incircle / excircle ============== */
  R.incircle = function (c) {
    var A = pt(c.p('ax', 180), c.p('ay', 56)), B = pt(c.p('bx', 72), c.p('by', 214)),
        Cv = pt(c.p('cx', 318), c.p('cy', 214));
    var state = { ex: false };
    function render() {
      var a = dist(B, Cv), b = dist(A, Cv), cc = dist(A, B);
      var s = (a + b + cc) / 2, area = triArea(A, B, Cv);
      var I = pt((a * A.x + b * B.x + cc * Cv.x) / (a + b + cc),
                 (a * A.y + b * B.y + cc * Cv.y) / (a + b + cc));
      var r = area / s;
      polyPts(c.el('tri'), [A, B, Cv]);
      moveC(c.el('inc'), I, r);
      moveC(c.el('ptI'), I);
      moveText(c.el('labI'), I, 0, 16);
      ['A', 'B', 'C'].forEach(function (n, i) {
        moveC(c.el('pt' + n), [A, B, Cv][i]);
      });
      moveText(c.el('labA'), A, 0, -12);
      moveText(c.el('labB'), B, -14, 16);
      moveText(c.el('labC'), Cv, 14, 16);
      moveC(c.el('handle'), A); moveC(c.el('halo'), A);
      /* angle bisectors, drawn from each vertex to the incentre */
      lineTo(c.el('bi1'), A, I); lineTo(c.el('bi2'), B, I); lineTo(c.el('bi3'), Cv, I);
      /* touch points */
      [['tA', footOf(I, B, Cv)], ['tB', footOf(I, A, Cv)], ['tC', footOf(I, A, B)]]
        .forEach(function (x) { moveC(c.el(x[0]), x[1]); });
      /* excircle opposite A: centre on the external bisectors */
      var ra = area / (s - a);
      var Ia = pt((-a * A.x + b * B.x + cc * Cv.x) / (-a + b + cc),
                  (-a * A.y + b * B.y + cc * Cv.y) / (-a + b + cc));
      var ex = c.el('exc'), exc = c.el('ptIa'), exl = c.el('labIa');
      [ex, exc, exl].forEach(function (e) { if (e) e.setAttribute('opacity', state.ex ? '1' : '0'); });
      if (ex) moveC(ex, Ia, ra);
      if (exc) moveC(exc, Ia);
      if (exl) moveText(exl, Ia, 0, 18);
      txt(c.el('f-r'), 'r = พื้นที่ / s = ' + fmt(area / 100, 2) + ' / ' + fmt(s / 10, 2) + ' = ' + fmt(r / 10, 2));
      txt(c.el('f-ra'), 'rₐ = พื้นที่ / (s − a) = ' + fmt(ra / 10, 2));
      c.out('r = ' + fmt(r / 10, 2) + (state.ex ? ' · rₐ = ' + fmt(ra / 10, 2) : ''));
    }
    c.onAct(function (act) {
      if (act === 'excircle') {
        state.ex = !state.ex;
        var b = c.btn('excircle');
        if (b) b.setAttribute('aria-pressed', state.ex ? 'true' : 'false');
        render();
      }
    });
    draggable(c.svg, c.el('handle'), function (p) {
      A = pt(clamp(p.x, 70, 330), clamp(p.y, 26, 168));
      render();
    });
    render();
  };

  /* =========================================== 20. statistics (c22294) ==== */
  R.statviz = function (c) {
    var data = (c.fig.getAttribute('data-values') || '').split(',').map(Number).filter(function (v) { return !isNaN(v); });
    if (!data.length) return;
    var x0 = c.p('x0', 60), x1 = c.p('x1', 540), base = c.p('base', 200);
    var lo = Math.min.apply(null, data), hi = Math.max.apply(null, data);
    function sx(v) { return x0 + (v - lo) / ((hi - lo) || 1) * (x1 - x0); }
    var sorted = data.slice().sort(function (a, b) { return a - b; });
    var n = sorted.length;
    var mean = data.reduce(function (s, v) { return s + v; }, 0) / n;
    function q(p) {
      var i = (n - 1) * p, f2 = Math.floor(i);
      return sorted[f2] + (sorted[Math.min(n - 1, f2 + 1)] - sorted[f2]) * (i - f2);
    }
    var med = q(0.5), q1 = q(0.25), q3 = q(0.75);
    var sd = Math.sqrt(data.reduce(function (s, v) { return s + (v - mean) * (v - mean); }, 0) / n);
    var state = { show: 'mean' };
    function render() {
      c.all('pt').forEach(function (el, i) {
        if (i < n) { moveC(el, pt(sx(sorted[i]), base)); el.setAttribute('opacity', '1'); }
        else el.setAttribute('opacity', '0');
      });
      var S = { mean: mean, median: med, q1: q1, q3: q3 };
      var marks = { mean: 'mean', median: 'median', q1: 'q1', q3: 'q3' };
      Object.keys(marks).forEach(function (k) {
        var el = c.el('m-' + k), lb = c.el('l-' + k);
        var on = (state.show === 'all') || (state.show === k) ||
                 (state.show === 'quart' && (k === 'q1' || k === 'q3' || k === 'median'));
        if (el) { lineTo(el, pt(sx(S[k]), base - 48), pt(sx(S[k]), base + 16)); el.setAttribute('opacity', on ? '1' : '0.12'); }
        if (lb) { moveText(lb, pt(sx(S[k]), base - 54), 0, 0); lb.setAttribute('opacity', on ? '1' : '0.12'); }
      });
      var box = c.el('box');
      if (box) {
        set(box, { x: sx(q1), y: base - 30, width: Math.max(1, sx(q3) - sx(q1)), height: 60 });
        box.setAttribute('opacity', (state.show === 'quart' || state.show === 'all') ? '1' : '0');
      }
      var sdb = c.el('sdband');
      if (sdb) {
        set(sdb, { x: sx(mean - sd), y: base - 22, width: Math.max(1, sx(mean + sd) - sx(mean - sd)), height: 44 });
        sdb.setAttribute('opacity', state.show === 'sd' ? '1' : '0');
      }
      txt(c.el('stat'), 'x̄ = ' + fmt(mean, 2) + ' · มัธยฐาน = ' + fmt(med, 2) +
                        ' · Q1 = ' + fmt(q1, 2) + ' · Q3 = ' + fmt(q3, 2) + ' · s.d. = ' + fmt(sd, 2));
      c.out('n = ' + n + ' · x̄ = ' + fmt(mean, 2) + ' · s.d. = ' + fmt(sd, 2));
    }
    c.onAct(function (a) { state.show = a; c.press(a, 'stat'); render(); });
    render();
  };

  /* ======================================= 21. desmos-style function graph */
  R.graphlab = function (c) {
    var o = pt(c.p('ox', 300), c.p('oy', 150)), u = c.p('unit', 26);
    var state = { a: 1, b: 0, c: 0, kind: 'quad' };
    function px(x, y) { return pt(o.x + x * u, o.y - y * u); }
    function render() {
      var pts = [], XM = (c.p('w', 600) - 20) / 2 / u;
      for (var x = -XM; x <= XM; x += 0.08) {
        var y;
        if (state.kind === 'quad') y = state.a * x * x + state.b * x + state.c;
        else if (state.kind === 'lin') y = state.a * x + state.c;
        else y = state.a * Math.abs(x) + state.c;
        if (Math.abs(y) < 60) pts.push(px(x, y));
      }
      pathD(c.el('curve'), pts.length ? dSeg(pts) : 'M 0 0');
      var vx = state.kind === 'quad' && state.a !== 0 ? -state.b / (2 * state.a) : 0;
      var vy = state.kind === 'quad' ? state.a * vx * vx + state.b * vx + state.c : state.c;
      var vtx = c.el('vertex');
      if (vtx) { moveC(vtx, px(vx, vy)); vtx.setAttribute('opacity', state.kind === 'quad' ? '1' : '0'); }
      var eq = state.kind === 'quad'
        ? 'y = ' + fmt(state.a, 2) + 'x² + ' + fmt(state.b, 2) + 'x + ' + fmt(state.c, 2)
        : (state.kind === 'lin' ? 'y = ' + fmt(state.a, 2) + 'x + ' + fmt(state.c, 2)
                                : 'y = ' + fmt(state.a, 2) + '|x| + ' + fmt(state.c, 2));
      txt(c.el('eq'), eq);
      c.out(eq + (state.kind === 'quad' ? ' · จุดยอด (' + fmt(vx, 2) + ', ' + fmt(vy, 2) + ')' : ''));
    }
    c.onInput('a', function (v) { state.a = v; render(); });
    c.onInput('b', function (v) { state.b = v; render(); });
    c.onInput('c', function (v) { state.c = v; render(); });
    c.onAct(function (a) { state.kind = a; c.press(a, 'kind'); render(); });
    render();
  };

  /* ===================================== 22. GSP-style construction steps = */
  R.construct = R.proof;

  /* ============================================================ bootstrap */
  function boot() {
    document.querySelectorAll('figure.fig[data-viz]').forEach(function (fig) {
      var name = fig.getAttribute('data-viz');
      var fn = R[name];
      if (!fn) return;
      try { fn(ctxFor(fig)); }
      catch (e) { if (window.console) console.warn('viz "' + name + '" failed:', e); }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  window.MJViz = { register: function (n, f) { R[n] = f; }, helpers: {
    pt: pt, add: add, sub: sub, mul: mul, nrm: nrm, lerp: lerp, mid: mid, dist: dist,
    polar: polar, angOf: angOf, rot: rot, inter: inter, footOf: footOf, angle3: angle3,
    triArea: triArea, set: set, txt: txt, tween: tween, draggable: draggable, fmt: fmt,
    clamp: clamp, dSeg: dSeg, dArc: dArc, dAngle: dAngle, polyPts: polyPts, pathD: pathD,
    lineTo: lineTo, moveC: moveC, moveText: moveText, REDUCED: REDUCED
  } };
})();
