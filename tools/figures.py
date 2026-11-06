# -*- coding: utf-8 -*-
"""figures — the static SVG frame of every interactive figure.

Each function returns a complete <figure> element.  The SVG it contains is the
whole diagram at its initial state, so the page is meaningful with JavaScript
disabled; `assets/js/viz.js` then re-computes the same geometry live.
Element contracts are the `data-id` attributes read by viz.js.
"""
from __future__ import annotations

import math

from svgkit import (
    P, angle_d, angle_mark, arc_d, arrowdefs, axes, circ, dist, dot, dseg_d, f,
    foot, g, grid, legend, lerp, line, line_inter, mid, path, poly, polar, rect,
    right_mark, seg, svg, ticks,
)
from svgkit import arrow, centroid, txt
from layout import figure, ctrl_btns, ctrl_range, readout


def _ang(a: P, v: P, b: P) -> float:
    u, w = (a - v).n, (b - v).n
    return math.degrees(math.acos(max(-1.0, min(1.0, u.x * w.x + u.y * w.y))))


def _tri_area(a: P, b: P, c: P) -> float:
    return abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2


def _bis(v: P, a: P, b: P, d: float) -> P:
    return v + ((a - v).n + (b - v).n).n * d


def _id(k: str) -> str:
    return f'data-id="{k}"'


# ===========================================================================
# 1 · ความหมายของเลขยกกำลัง
# ===========================================================================
def fig_powers() -> str:
    W, H = 600, 250
    x0, y0, unit, barw = 60, 160, 26, 400
    b = []
    b.append(txt(P(30, 36), "เลขยกกำลัง: การคูณซ้ำ ๆ", "t-tag", "start"))
    # ten unit cells
    for i in range(10):
        b.append(
            rect(x0 + i * (unit + 4), y0 - unit, unit, unit,
                 cls=("f-at" if i < 3 else "f-it"), rx=3, **{"data-id": "cell"})
        )
        b.append(rect(x0 + i * (unit + 4), y0 - unit, unit, unit, cls="s-soft thin", rx=3))
    b.append(txt(P(x0, y0 + 20), "แต่ละช่อง = ฐานหนึ่งตัวที่ถูกคูณเข้าไป", "t-mono", "start"))
    # log bar
    b.append(txt(P(30, 206), "ขนาดเทียบ (สเกลลอการิทึม)", "t-tag", "start"))
    b.append(rect(x0, 216, barw, 14, cls="f-it", rx=3))
    b.append(rect(x0, 216, 0.58 * barw, 14, cls="f-accent", rx=3, **{"data-id": "bar"}))
    # readouts
    b.append(txt(P(x0, 80), "2³", "t-val t-accent", "start", **{"data-id": "expr",
                                                                   "font-size": "26"}))
    b.append(txt(P(x0 + 70, 80), "8", "t-val", "start", **{"data-id": "val",
                                                              "font-size": "22"}))
    b.append(txt(P(x0, 108), "2 × 2 × 2", "t-mono", "start", **{"data-id": "expand"}))
    body = "".join(b)
    sv = svg(W, H, body, "fig-powers", "ความหมายของเลขยกกำลัง",
             "แถบช่องสี่เหลี่ยมแสดงจำนวนครั้งที่ฐานถูกคูณเข้าไป พร้อมค่าของเลขยกกำลัง "
             "และแถบเปรียบเทียบขนาดในสเกลลอการิทึม")
    ctl = ctrl_range("n", -3, 8, 1, 3, "เลขชี้กำลัง n") + readout("2^3 = 8")
    return figure(
        sv,
        "เลื่อนค่า <b>n</b> ดูว่า \\(2^n\\) โตเร็วแค่ไหน และเมื่อ \\(n&lt;0\\) "
        "ความหมายเปลี่ยนเป็นส่วนกลับ \\(2^{-n}=1/2^{n}\\)",
        ctl, viz="powers",
        data={"base": 2, "x0": x0, "y0": y0, "unit": unit, "barw": barw},
    )


# ===========================================================================
# 2 · สัญกรณ์วิทยาศาสตร์
# ===========================================================================
def fig_scinot() -> str:
    W, H = 600, 180
    x0, x1, y = 70, 540, 96
    lo, hi = -9, 12
    b = [txt(P(30, 34), "สเกลของจำนวน", "t-tag", "start")]
    b.append(line(P(x0, y), P(x1, y), "s-soft"))
    for e in range(lo, hi + 1, 3):
        t = (e - lo) / (hi - lo)
        px = x0 + t * (x1 - x0)
        b.append(line(P(px, y - 6), P(px, y + 6), "s-soft"))
        sup = "⁻" if e < 0 else ""
        sup += "".join("⁰¹²³⁴⁵⁶⁷⁸⁹"[int(d)] for d in str(abs(e)))
        b.append(txt(P(px, y + 22), "10" + sup, "t-mono"))
    t0 = (8 - lo) / (hi - lo)
    mx = x0 + t0 * (x1 - x0)
    b.append(circ(P(mx, y), 13, "f-at", **{"data-id": "halo"}))
    b.append(dot(P(mx, y), 6, "f-accent", **{"data-id": "marker"}))
    b.append(txt(P(mx, y - 22), "1.50×10⁸", "t-val t-accent", **{"data-id": "mlabel"}))
    b.append(txt(P(30, 148), "150000000", "t-val", "start", **{"data-id": "plain",
                                                                 "font-size": "18"}))
    b.append(txt(P(30, 168), "ความเร็วแสง ≈ 3×10⁸ เมตร/วินาที", "t-mono", "start",
                   **{"data-id": "note"}))
    sv = svg(W, H, "".join(b), "fig-scinot", "สัญกรณ์วิทยาศาสตร์บนสเกลลอการิทึม",
             "เส้นสเกลกำลังสิบจาก 10 ยกกำลังลบเก้าถึงสิบสอง มีเครื่องหมายชี้ตำแหน่งของจำนวน "
             "ที่เขียนในรูป a คูณสิบยกกำลัง n พร้อมค่าเต็มและตัวอย่างในชีวิตจริง")
    ctl = (ctrl_range("m", 1, 9.9, 0.1, 1.5, "สัมประสิทธิ์ a")
           + ctrl_range("e", -9, 12, 1, 8, "กำลัง n") + readout("1.5 × 10^8"))
    return figure(sv, "สัญกรณ์วิทยาศาสตร์เขียนจำนวนเป็น \\(a\\times 10^{n}\\) โดย "
                      "\\(1\\le a&lt;10\\) — เลื่อนดูว่าปรับ \\(n\\) ทีละหนึ่งแล้วค่าขยับไปทิศไหน",
                  ctl, viz="scinot", data={"x0": x0, "x1": x1, "y": y})


# ===========================================================================
# 3 · การคลี่ปริซึม
# ===========================================================================
def fig_prismnet() -> str:
    W, H = 600, 320
    Wd, Hh, L = 120, 70, 170
    cx, cy = 300, 150
    o = P(cx - L / 2, cy - Hh / 2)
    d = P(Wd * 0.62, -Wd * 0.45)
    F = {
        "front": [P(o.x, o.y), P(o.x + L, o.y), P(o.x + L, o.y + Hh), P(o.x, o.y + Hh)],
        "right": [P(o.x + L, o.y), P(o.x + L, o.y) + d, P(o.x + L, o.y + Hh) + d, P(o.x + L, o.y + Hh)],
        "left":  [P(o.x, o.y) + d, P(o.x, o.y), P(o.x, o.y + Hh), P(o.x, o.y + Hh) + d],
        "top":   [P(o.x, o.y) + d, P(o.x + L, o.y) + d, P(o.x + L, o.y), P(o.x, o.y)],
        "bottom": [P(o.x, o.y + Hh), P(o.x + L, o.y + Hh), P(o.x + L, o.y + Hh) + d, P(o.x, o.y + Hh) + d],
        "back":  [P(o.x, o.y) + d, P(o.x + L, o.y) + d, P(o.x + L, o.y + Hh) + d, P(o.x, o.y + Hh) + d],
    }
    names = {"front": "หน้า", "right": "ข้างขวา", "left": "ข้างซ้าย",
             "top": "บน", "bottom": "ล่าง", "back": "หลัง"}
    fills = {"front": "f-at", "right": "f-at", "left": "f-at", "back": "f-at",
             "top": "f-tt", "bottom": "f-tt"}
    b = [txt(P(30, 32), "คลี่ปริซึมสี่เหลี่ยม → รูปคลี่ 6 หน้า", "t-tag", "start")]
    order = ["back", "top", "bottom", "left", "right", "front"]
    for k in order:
        b.append(poly(*F[k], cls=fills[k], **{"data-id": k,
                                              "opacity": "0" if k == "back" else "1"}))
        b.append(poly(*F[k], cls="s-ink thin", **{"pointer-events": "none"}))
    for k in order:
        m = P((F[k][0].x + F[k][2].x) / 2, (F[k][0].y + F[k][2].y) / 2)
        b.append(txt(m, names[k], "t-mono", dy=4, **{"data-id": k + "-lab", "opacity": "0"}))
    b.append(txt(P(30, 268), "ข้างรวม = ความยาวรอบรูปฐาน × สูง = 29.0 × 7.0", "t-mono",
                   "start", **{"data-id": "f-lat"}))
    b.append(txt(P(30, 292), "พื้นที่ผิวทั้งหมด = 44.9 ตร.หน่วย", "t-val", "start",
                   **{"data-id": "f-tot"}))
    b.append(legend(H - 6, W, [("s-ink thin", "หน้าข้าง"), ("s-teal", "หน้าฐาน")]))
    sv = svg(W, H + 26, "".join(b), "fig-prismnet", "การคลี่ปริซึมสี่เหลี่ยมมุมฉาก",
             "ปริซึมสี่เหลี่ยมมุมฉากคลี่ออกเป็นรูปคลี่ที่มีหน้าข้างสี่หน้าเรียงต่อกัน "
             "และหน้าฐานสองหน้าอยู่บนและล่าง แสดงว่าพื้นที่ผิวข้างคือความยาวรอบรูปฐานคูณความสูง")
    ctl = (ctrl_btns(("open", "คลี่ออก", False), ("close", "พับกลับ", True))
           + ctrl_range("t", 0, 1, 0.01, 0, "ระดับการคลี่") + readout("รูปทรงปิด"))
    return figure(sv, "การคลี่ทำให้เห็นว่า <b>พื้นที่ผิวข้าง</b> ของปริซึมเป็นสี่เหลี่ยมผืนผ้า "
                      "ที่มีด้านหนึ่งเท่ากับความยาวรอบรูปฐาน และอีกด้านเท่ากับความสูง",
                  ctl, viz="prismnet",
                  data={"w": Wd, "h": Hh, "len": L, "cx": cx, "cy": cy})


# ===========================================================================
# 4 · การคลี่ทรงกระบอก
# ===========================================================================
def fig_cylnet() -> str:
    W, H = 600, 250
    r, h, cx, cy = 42, 96, 150, 120
    b = [txt(P(30, 32), "คลี่ทรงกระบอก → สี่เหลี่ยมผืนผ้า + วงกลมสองวง", "t-tag", "start")]
    b.append(rect(cx - r, cy - h / 2, 2 * r, h, cls="f-at", **{"data-id": "lat"}))
    b.append(rect(cx - r, cy - h / 2, 2 * r, h, cls="s-ink thin"))
    b.append(f'<ellipse {_id("top")} cx="{f(cx)}" cy="{f(cy - h / 2)}" rx="{f(r)}" '
             f'ry="{f(r * 0.32)}" class="f-tt"/>')
    b.append(f'<ellipse cx="{f(cx)}" cy="{f(cy - h / 2)}" rx="{f(r)}" ry="{f(r * 0.32)}" '
             f'class="s-ink thin"/>')
    b.append(f'<ellipse {_id("bot")} cx="{f(cx)}" cy="{f(cy + h / 2)}" rx="{f(r)}" '
             f'ry="{f(r * 0.32)}" class="f-tt"/>')
    b.append(f'<ellipse cx="{f(cx)}" cy="{f(cy + h / 2)}" rx="{f(r)}" ry="{f(r * 0.32)}" '
             f'class="s-ink thin dash-fine"/>')
    b.append(txt(P(cx, cy - h / 2 - 14), "เส้นรอบวง = 2πr", "t-mono",
                   **{"data-id": "circ-lab", "opacity": "0"}))
    b.append(txt(P(cx - r - 12, cy), "h", "t-mono", "end", dy=4,
                   **{"data-id": "gen-lab", "opacity": "1"}))
    b.append(txt(P(30, 200), "ผิวข้าง = 2πr·h = 25.3", "t-mono", "start",
                   **{"data-id": "f-lat"}))
    b.append(txt(P(30, 226), "ผิวทั้งหมด = 2πr(r + h) = 36.4", "t-val", "start",
                   **{"data-id": "f-tot"}))
    sv = svg(W, H, "".join(b), "fig-cylnet", "การคลี่ทรงกระบอก",
             "ทรงกระบอกคลี่ออกโดยผิวข้างกลายเป็นสี่เหลี่ยมผืนผ้ากว้างเท่ากับเส้นรอบวงฐาน "
             "และสูงเท่ากับความสูงของทรงกระบอก ส่วนฐานทั้งสองเป็นวงกลมรัศมี r")
    ctl = (ctrl_btns(("open", "คลี่ออก", False), ("close", "พับกลับ", True))
           + ctrl_range("t", 0, 1, 0.01, 0, "ระดับการคลี่") + readout("ทรงกระบอก"))
    return figure(sv, "ผิวข้างของทรงกระบอกคลี่ได้เป็นสี่เหลี่ยมผืนผ้าขนาด "
                      "\\(2\\pi r \\times h\\) — นี่คือที่มาของสูตร \\(2\\pi rh\\)",
                  ctl, viz="cylnet", data={"r": r, "h": h, "cx": cx, "cy": cy})


# ===========================================================================
# 5 · 3D solid (prism / cylinder)
# ===========================================================================
def fig_solid3d(kind: str = "prism", shape: str = "rect") -> str:
    """3D viewer with a static isometric SVG fallback."""
    W, H = 600, 300
    b = [txt(P(30, 32), "ภาพสามมิติ (ลากเพื่อหมุน)", "t-tag", "start")]
    if kind == "prism":
        o = P(190, 200)
        a, hh, dep = 150, 110, 70
        d = P(dep * 0.6, -dep * 0.48)
        base = [o, o + P(a, 0), o + P(a, 0) + d, o + d]
        topf = [p + P(0, -hh) for p in base]
        b.append(poly(*base, cls="f-tt"))
        b.append(poly(*[base[0], base[1], topf[1], topf[0]], cls="f-at"))
        b.append(poly(*[base[1], base[2], topf[2], topf[1]], cls="f-at"))
        b.append(poly(*topf, cls="f-tt"))
        for q in (base, topf):
            b.append(poly(*q, cls="s-ink thin"))
        for i in range(4):
            b.append(line(base[i], topf[i], "s-ink thin"))
        b.append(txt(mid(base[0], base[1]), "ด้านฐาน", "t-mono", dy=18))
        b.append(txt(P(base[0].x - 14, base[0].y - hh / 2), "สูง", "t-mono", "end", dy=4))
        ttl = "ปริซึมสี่เหลี่ยมมุมฉาก"
        desc = ("ภาพฉายของปริซึมสี่เหลี่ยมมุมฉาก แสดงหน้าฐานสองหน้าและหน้าข้างสี่หน้า "
                "พร้อมกำกับความยาวฐานและความสูง")
    else:
        cx, cy, r, hh = 200, 150, 60, 120
        b.append(rect(cx - r, cy - hh / 2, 2 * r, hh, cls="f-at"))
        b.append(line(P(cx - r, cy - hh / 2), P(cx - r, cy + hh / 2), "s-ink thin"))
        b.append(line(P(cx + r, cy - hh / 2), P(cx + r, cy + hh / 2), "s-ink thin"))
        b.append(f'<ellipse cx="{cx}" cy="{cy + hh / 2}" rx="{r}" ry="{r * 0.3}" class="f-tt"/>')
        b.append(f'<ellipse cx="{cx}" cy="{cy + hh / 2}" rx="{r}" ry="{r * 0.3}" class="s-ink thin"/>')
        b.append(f'<ellipse cx="{cx}" cy="{cy - hh / 2}" rx="{r}" ry="{r * 0.3}" class="f-tt"/>')
        b.append(f'<ellipse cx="{cx}" cy="{cy - hh / 2}" rx="{r}" ry="{r * 0.3}" class="s-ink thin"/>')
        b.append(line(P(cx, cy - hh / 2), P(cx + r, cy - hh / 2), "s-muted dash"))
        b.append(txt(P(cx + r / 2, cy - hh / 2 - 8), "r", "t-mono"))
        b.append(txt(P(cx + r + 16, cy), "h", "t-mono", "start", dy=4))
        ttl = "ทรงกระบอก"
        desc = "ภาพฉายของทรงกระบอก แสดงฐานวงกลมรัศมี r สองฐานและผิวข้าง พร้อมกำกับความสูง h"

    static = svg(W, H, "".join(b), f"fig-3d-{kind}-{shape}", ttl, desc,
                 extra='data-fallback="1"')
    canvas = '<canvas class="viz3d" data-3d="1" hidden></canvas>'

    if kind == "prism" and shape == "rect":
        sliders = (ctrl_range("a", 2, 8, 0.5, 5, "ฐาน a")
                   + ctrl_range("b", 1, 6, 0.5, 3, "ฐาน b")
                   + ctrl_range("h", 1, 8, 0.5, 4, "สูง h"))
    elif kind == "prism":
        sliders = (ctrl_range("a", 2, 8, 0.5, 4, "ขา a")
                   + ctrl_range("b", 2, 8, 0.5, 3, "ขา b")
                   + ctrl_range("h", 1, 8, 0.5, 4, "สูง h"))
    else:
        sliders = (ctrl_range("r", 1, 4, 0.1, 2.2, "รัศมี r")
                   + ctrl_range("h", 1, 8, 0.5, 5, "สูง h"))

    ctl = (sliders
           + ctrl_btns(("solid", "ทึบ", True), ("xray", "โปร่ง", False),
                       ("wire", "โครงลวด", False), ("slice", "ผ่าครึ่ง", False), group="mode")
           + ctrl_range("slice", -4, 4, 0.1, 0, "ระนาบตัด")
           + ctrl_btns(("spin", "หมุนอัตโนมัติ", True))
           + readout(""))
    outs = (
        '<p class="mono" data-out="f-shape"></p>'
        '<p class="mono" data-out="f-lat"></p>'
        '<p class="mono" data-out="f-tot"></p>'
        '<p class="mono" data-out="f-vol"></p>'
    )
    fig = figure(static + canvas,
                 "ลากเพื่อหมุน ปรับสไลเดอร์เพื่อดูว่าพื้นที่ผิวและปริมาตรเปลี่ยนตามมิติอย่างไร "
                 "โหมด <b>ผ่าครึ่ง</b> ช่วยให้เห็นหน้าตัดที่คงรูปทุกระดับ — "
                 "เหตุผลที่ปริมาตร = พื้นที่ฐาน × สูง" + outs,
                 ctl)
    # inject the 3D hook attributes on the <figure>
    fig = fig.replace('<figure class="fig"',
                      f'<figure class="fig" data-viz3d="{kind}" data-shape="{shape}"', 1)
    return fig


# ===========================================================================
# 6 · เส้นขนานและมุม
# ===========================================================================
def fig_parallel() -> str:
    W, H = 600, 300
    y1, y2, xl, xr = 72, 188, 40, 560
    piv = P(300, (y1 + y2) / 2)
    a0 = 58.0
    dirv = P(math.cos(math.radians(a0)), -math.sin(math.radians(a0)))
    p1, p2 = piv + dirv * 260, piv - dirv * 260
    A = line_inter(p2, p1, P(xl, y1), P(xr, y1))
    B = line_inter(p2, p1, P(xl, y2), P(xr, y2))
    b = [arrowdefs()]
    b.append(txt(P(30, 34), "เส้นขนานถูกตัดด้วยเส้นตัด", "t-tag", "start"))
    b.append(line(P(xl, y1), P(xr, y1), "s-ink"))
    b.append(line(P(xl, y2), P(xr, y2), "s-ink"))
    for yy in (y1, y2):
        for k in (-1, 1):
            cpt = P(xr - 36 + k * 6, yy)
            b.append(seg(P(cpt.x - 7, yy - 6), P(cpt.x + 2, yy), P(cpt.x - 7, yy + 6),
                         cls="s-muted thin"))
    b.append(txt(P(xl + 4, y1 - 10), "ℓ₁", "t-mono", "start"))
    b.append(txt(P(xl + 4, y2 + 20), "ℓ₂", "t-mono", "start"))
    b.append(line(p2, p1, "s-link", **{"data-id": "tr"}))
    b.append(txt(P(p1.x + 6, p1.y), "t", "t-mono t-link", "start"))
    # angle arcs at both intersections
    for key, V in (("a", A), ("b", B)):
        along = P(1, 0)
        arms = [V + dirv * 40, V + along * 40, V - dirv * 40, V - along * 40]
        for i in range(4):
            cls = "s-accent hl" if (key, i) in (("a", 0), ("b", 0)) else "s-muted hl off"
            a_from, a_to = arms[i], arms[(i + 1) % 4]
            b.append(angle_mark(V, a_from, a_to, 26 + (i % 2) * 4, cls,
                                **{"data-id": f"{key}{i + 1}"}))
            bis = _bis(V, a_from, a_to, 44)
            v = _ang(a_from, V, a_to)
            on = (key, i) in (("a", 0), ("b", 0))
            b.append(txt(bis, f"{round(v)}°", "t-mono" + (" t-accent" if on else ""), dy=4,
                           **{"data-id": f"{key}{i + 1}-t",
                              "opacity": "1" if on else "0.16"}))
        b.append(dot(V, 4.2, "f-ink", **{"data-id": f"pt{key.upper()}"}))
    b.append(txt(P(A.x - 14, A.y - 8), "P", "t-name", **{"data-id": "labA"}))
    b.append(txt(P(B.x - 14, B.y + 18), "Q", "t-name", **{"data-id": "labB"}))
    hp = piv + dirv * 150
    b.append(circ(hp, 14, "handle-halo", **{"data-id": "halo"}))
    b.append(dot(hp, 7, "handle", **{"data-id": "handle"}))
    b.append(txt(P(hp.x + 20, hp.y - 12), "ลากเพื่อหมุนเส้นตัด", "hint", "start"))
    b.append(txt(P(30, 240), "มุมแย้งเท่ากัน (corresponding)", "t-val t-accent", "start",
                   **{"data-id": "pair-label"}))
    b.append(txt(P(30, 262), "มุมในตำแหน่งเดียวกันของจุดตัดสองจุด", "t-mono", "start",
                   **{"data-id": "pair-note"}))
    b.append(txt(P(30, 284), "58° = 58°", "t-val", "start", **{"data-id": "pair-val"}))
    sv = svg(W, H, "".join(b), "fig-parallel", "มุมที่เกิดจากเส้นขนานและเส้นตัด",
             "เส้นขนานสองเส้นถูกตัดด้วยเส้นตัดหนึ่งเส้น เกิดมุมสี่มุมที่จุดตัดแต่ละจุด "
             "เน้นคู่มุมที่สัมพันธ์กัน ได้แก่ มุมแย้ง มุมภายในข้างเดียวกัน และมุมตรงข้าม")
    ctl = (ctrl_btns(("corr", "มุมแย้งเท่ากัน", True), ("alt", "มุมแย้ง", False),
                     ("coint", "ภายในข้างเดียวกัน", False), ("vert", "มุมตรงข้าม", False),
                     group="pair")
           + readout("มุมแย้งเท่ากัน · 58° = 58°"))
    return figure(sv, "ลากจุดวงกลมเพื่อหมุนเส้นตัด แล้วสังเกตว่าคู่มุมใดเท่ากันเสมอ "
                      "และคู่ใดรวมกันได้ \\(180^\\circ\\) ไม่ว่าจะหมุนไปที่มุมใด",
                  ctl, viz="parallel",
                  data={"y1": y1, "y2": y2, "xl": xl, "xr": xr, "px": piv.x, "a0": a0})


# ===========================================================================
# 7 · มุมภายนอกของรูปสามเหลี่ยม
# ===========================================================================
def fig_extangle() -> str:
    W, H = 500, 280
    A, B, C = P(110, 190), P(300, 190), P(210, 72)
    ext = B + (B - A).n * 120
    b = [arrowdefs()]
    b.append(txt(P(30, 32), "มุมภายนอก = ผลรวมมุมภายในที่ไม่ประชิด", "t-tag", "start"))
    b.append(poly(A, B, C, cls="f-it", **{"data-id": "tri"}))
    b.append(poly(A, B, C, cls="s-ink"))
    b.append(line(B, ext, "s-accent dash", **{"data-id": "ext"}))
    b.append(angle_mark(A, B, C, 26, "s-link", **{"data-id": "mA"}))
    b.append(angle_mark(C, A, B, 24, "s-teal", **{"data-id": "mC"}))
    b.append(angle_mark(B, C, ext, 30, "s-accent", **{"data-id": "mExt"}))
    b.append(angle_mark(B, A, C, 22, "s-muted dash-fine", **{"data-id": "mInt"}))
    aA, aC = _ang(B, A, C), _ang(A, C, B)
    aE = 180 - _ang(A, B, C)
    b.append(txt(_bis(A, B, C, 42), f"{round(aA)}°", "t-mono t-link", dy=4,
                   **{"data-id": "tA"}))
    b.append(txt(_bis(C, A, B, 40), f"{round(aC)}°", "t-mono t-teal", dy=4,
                   **{"data-id": "tC"}))
    b.append(txt(_bis(B, C, ext, 48), f"{round(aE)}°", "t-mono t-accent", dy=4,
                   **{"data-id": "tExt"}))
    for nm, p, dx, dy in (("A", A, -16, 6), ("B", B, 4, 20), ("C", C, 0, -12)):
        b.append(dot(p, 4))
        b.append(txt(P(p.x + dx, p.y + dy), nm, "t-name", **{"data-id": "lab" + nm}))
    b.append(txt(P(ext.x + 10, ext.y + 6), "D", "t-name t-accent", "start",
                   **{"data-id": "labD"}))
    b.append(circ(C, 14, "handle-halo", **{"data-id": "halo"}))
    b.append(dot(C, 7, "handle", **{"data-id": "handle"}))
    b.append(txt(P(30, 252), f"{round(aA)}° + {round(aC)}° = {round(aA + aC)}°  =  มุมภายนอก",
                   "t-val", "start", **{"data-id": "eq"}))
    b.append(legend(H + 18, W, [("s-link", "มุม A"), ("s-teal", "มุม C"),
                                ("s-accent", "มุมภายนอกที่ B")]))
    sv = svg(W, H + 36, "".join(b), "fig-extangle", "มุมภายนอกของรูปสามเหลี่ยม",
             "รูปสามเหลี่ยม ABC ต่อด้าน AB ออกไปถึงจุด D เกิดมุมภายนอกที่จุด B "
             "ซึ่งเท่ากับผลรวมของมุมภายในที่จุด A และจุด C")
    return figure(sv, "ลากจุด C ไปที่ไหนก็ได้ มุมภายนอกที่ B ยังเท่ากับ "
                      "\\(\\hat{A}+\\hat{C}\\) เสมอ เพราะมุมภายในทั้งสามรวมกันได้ "
                      "\\(180^\\circ\\) และมุมภายนอกเป็นมุมประชิดเส้นตรงของ \\(\\hat{B}\\)",
                  readout("Â + Ĉ = มุมภายนอกที่ B"), viz="extangle",
                  data={"ax": A.x, "ay": A.y, "bx": B.x, "by": B.y, "cx": C.x, "cy": C.y})


# ===========================================================================
# 8 · การแปลงทางเรขาคณิต
# ===========================================================================
def fig_transform() -> str:
    W, H = 600, 320
    o = P(300, 190)
    u = 26
    base = [P(1, 1), P(4, 1), P(2, 3)]

    def px(q): return P(o.x + q.x * u, o.y - q.y * u)

    img = [P(q.x + 5, q.y - 3) for q in base]   # static frame = the translation
    b = [arrowdefs()]
    b.append(grid(o.x - 10 * u, o.y - 5 * u, o.x + 10 * u, o.y + 4 * u, u))
    b.append(axes(o, 10 * u + 6, 5 * u + 6, u, 10, 4))
    b.append(line(P(o.x, o.y - 5 * u), P(o.x, o.y + 4 * u), "s-violet dash",
                  **{"data-id": "mirror", "opacity": "0"}))
    b.append(dot(o, 5, "f-violet", **{"data-id": "centre", "opacity": "0"}))
    b.append(arrow(px(P(0, 0)), px(P(5, -3)), "s-violet", "ar",
                     **{"data-id": "vector"}))
    b.append(poly(*[px(q) for q in base], cls="f-lt", **{"data-id": "pre"}))
    b.append(poly(*[px(q) for q in base], cls="s-link"))
    b.append(poly(*[px(q) for q in img], cls="f-at", **{"data-id": "img"}))
    for i, nm in enumerate("ABC"):
        b.append(path(dseg_d(px(base[i]), px(img[i])), "s-soft dash-fine",
                      **{"data-id": "tr" + nm, "opacity": "0.9"}))
    for i, nm in enumerate("ABC"):
        b.append(dot(px(base[i]), 4, "f-link", **{"data-id": "pt" + nm}))
        b.append(txt(P(px(base[i]).x - 12, px(base[i]).y - 8), nm, "t-name t-link",
                       **{"data-id": "lab" + nm}))
        b.append(dot(px(img[i]), 4, "f-accent", **{"data-id": "ipt" + nm}))
        b.append(txt(P(px(img[i]).x + 12, px(img[i]).y - 8), nm + "′", "t-name t-accent",
                       **{"data-id": "ilab" + nm}))
    b.append(txt(P(30, 282), "(x, y) → (x + 5, y − 3)", "t-val t-accent", "start",
                   **{"data-id": "rule"}))
    b.append(txt(P(30, 304), "A(1,1) → A′(6,−2)   B(4,1) → B′(9,−2)   C(2,3) → C′(7,0)",
                   "t-mono", "start", **{"data-id": "map"}))
    b.append(legend(H + 18, W, [("s-link", "รูปต้นแบบ"), ("s-accent", "ภาพที่ได้"),
                                ("s-violet dash", "เส้น/จุดอ้างอิง")]))
    sv = svg(W, H + 36, "".join(b), "fig-transform", "การแปลงทางเรขาคณิตสามแบบ",
             "ระนาบพิกัดแสดงรูปสามเหลี่ยมต้นแบบและภาพที่ได้จากการเลื่อนขนาน การสะท้อน "
             "หรือการหมุน พร้อมกฎการจับคู่พิกัดและเส้นหรือจุดอ้างอิงของการแปลงนั้น")
    ctl = (ctrl_btns(("translate", "เลื่อนขนาน", True), ("reflect", "สะท้อน", False),
                     ("rotate", "หมุน 90°", False), group="mode")
           + ctrl_btns(("play", "เล่นภาพเคลื่อนไหว", False), ("reset", "เริ่มใหม่", False))
           + readout("(x, y) → (x + 5, y − 3) · พื้นที่คงเดิม"))
    return figure(sv, "การแปลงทั้งสามแบบนี้เป็น <b>การแปลงที่รักษาระยะ</b> (isometry) "
                      "รูปที่ได้จึงเท่ากันทุกประการกับรูปต้นแบบ — ความยาวด้าน ขนาดมุม "
                      "และพื้นที่ไม่เปลี่ยน เปลี่ยนแค่ตำแหน่งหรือทิศทาง",
                  ctl, viz="transform", data={"ox": o.x, "oy": o.y, "unit": u})


# ===========================================================================
# 9 · เทเซเลชัน
# ===========================================================================
def fig_tessel() -> str:
    W, H = 600, 260
    b = [txt(P(30, 32), "เทเซเลชันจากรูปสามเหลี่ยมเดียว", "t-tag", "start")]
    # one triangle tile, repeated by translation + 180° rotation
    tw, th = 72, 62
    ox, oy = 90, 70
    idx = 0
    for row in range(3):
        for col in range(6):
            for up in (True, False):
                x = ox + col * tw + (row % 2) * (tw / 2)
                y = oy + row * th
                if x > 540:
                    continue
                if up:
                    pts = [P(x, y + th), P(x + tw, y + th), P(x + tw / 2, y)]
                    cls = "f-at"
                    rotd, tx, ty = 0, 0, 0
                else:
                    pts = [P(x + tw / 2, y), P(x + tw * 1.5, y), P(x + tw, y + th)]
                    cls = "f-tt"
                    rotd, tx, ty = 180, 0, 0
                if max(p.x for p in pts) > 552:
                    continue
                idx += 1
                inner = (poly(*pts, cls=cls) + poly(*pts, cls="s-ink thin"))
                b.append(g(inner, **{"data-id": "tile",
                                     "data-tx": f"{-(col - 2) * 14:.0f}",
                                     "data-ty": f"{-(row - 1) * 10:.0f}",
                                     "data-rot": f"{rotd * 0.12:.0f}",
                                     "data-ox": f(x + tw / 2), "data-oy": f(y + th / 2),
                                     "opacity": "1"}))
    b.append(txt(P(30, 236), "มุมที่มาชุมนุมรอบจุดเดียวรวมกันได้ 360° จึงไม่มีช่องว่าง",
                   "t-mono", "start"))
    sv = svg(W, H, "".join(b), "fig-tessel", "เทเซเลชันของรูปสามเหลี่ยม",
             "รูปสามเหลี่ยมรูปเดียวถูกเลื่อนขนานและหมุนครึ่งรอบซ้ำ ๆ จนปูเต็มระนาบ "
             "โดยไม่มีช่องว่างและไม่ทับกัน")
    ctl = (ctrl_btns(("play", "เล่นการปู", False), ("reset", "เริ่มใหม่", False))
           + readout("ปูเต็มระนาบ — ไม่มีช่องว่างและไม่ทับกัน"))
    return figure(sv, "สามเหลี่ยมทุกรูปปูระนาบได้ เพราะสำเนาที่หมุน \\(180^\\circ\\) "
                      "ประกบกันเป็นรูปสี่เหลี่ยมด้านขนาน ซึ่งเลื่อนขนานไปปูต่อได้ไม่สิ้นสุด",
                  ctl, viz="tessel")


# ===========================================================================
# 10 · ความเท่ากันทุกประการ
# ===========================================================================
def fig_congruence() -> str:
    W, H = 600, 300
    A, B, C = P(76, 198), P(196, 198), P(128, 106)
    T1 = [A, B, C]
    off = P(250, 0)
    rotd = -28.0
    T2 = [p.rot(rotd, A) + off for p in T1]
    b = [txt(P(30, 32), "เงื่อนไขที่ทำให้สามเหลี่ยมสองรูปเท่ากันทุกประการ", "t-tag", "start")]
    b.append(poly(*T1, cls="f-lt", **{"data-id": "t1"}))
    b.append(poly(*T1, cls="s-link"))
    b.append(poly(*T2, cls="f-at", **{"data-id": "t2"}))
    b.append(poly(*T2, cls="s-accent"))
    b.append(poly(*T2, cls="f-vt", **{"data-id": "moving", "opacity": "0"}))

    # side ticks: s1 = AB, s2 = BC, s3 = CA  (1/2/3 ticks so pairs are readable)
    for tri, cls in ((T1, "s-link"), (T2, "s-accent")):
        for sid, p, q, n in (("s1", tri[0], tri[1], 1), ("s2", tri[1], tri[2], 2),
                             ("s3", tri[2], tri[0], 3)):
            b.append(g(ticks(p, q, n, 7, cls, 5), **{"data-id": sid}))
    # angle marks: a1 at A, a2 at B, a3 at C
    for tri, cls in ((T1, "s-link"), (T2, "s-accent")):
        for aid, v, p, q, na in (("a1", 0, 1, 2, 1), ("a2", 1, 2, 0, 2), ("a3", 2, 0, 1, 1)):
            b.append(g(angle_mark(tri[v], tri[p], tri[q], 22, cls, arcs=na),
                       **{"data-id": aid}))
    for tri, names, cls in ((T1, "ABC", "t-link"), (T2, "DEF", "t-accent")):
        for i, nm in enumerate(names):
            out = (tri[i] - centroid(*tri)).n * 16
            b.append(dot(tri[i], 4, "f-ink"))
            b.append(txt(tri[i] + out, nm, "t-name " + cls, dy=5))
    b.append(txt(P(30, 254), "ด.ด.ด. (SSS)", "t-val t-accent", "start",
                   **{"data-id": "crit-name"}))
    b.append(txt(P(30, 278), "ด้านสามคู่ยาวเท่ากัน", "t-mono", "start",
                   **{"data-id": "crit-note"}))
    sv = svg(W, H, "".join(b), "fig-congruence", "เงื่อนไขความเท่ากันทุกประการ",
             "รูปสามเหลี่ยมสองรูปวางห่างกันและหมุนต่างกัน มีขีดกำกับด้านและส่วนโค้งกำกับมุม "
             "เพื่อเน้นว่าส่วนประกอบคู่ใดเท่ากันตามเงื่อนไขที่เลือก")
    ctl = (ctrl_btns(("sss", "ด.ด.ด.", True), ("sas", "ด.ม.ด.", False),
                     ("asa", "ม.ด.ม.", False), ("aas", "ม.ม.ด.", False),
                     ("rhs", "ฉ.ด.ด.", False), group="crit")
           + ctrl_btns(("play", "ทับรูป", False), ("reset", "แยกรูป", False))
           + readout("ด.ด.ด. (SSS) — ด้านสามคู่ยาวเท่ากัน"))
    return figure(sv, "กด <b>ทับรูป</b> เพื่อเลื่อนและหมุนรูปหนึ่งไปทับอีกรูป — "
                      "นี่คือความหมายของคำว่า “เท่ากันทุกประการ” "
                      "เลือกเงื่อนไขเพื่อดูว่าต้องรู้ส่วนประกอบใดเพียง 3 คู่ก็สรุปได้",
                  ctl, viz="congruence",
                  data={"ax": A.x, "ay": A.y, "bx": B.x, "by": B.y,
                        "cx": C.x, "cy": C.y, "dx": off.x, "dy": off.y, "rot": rotd})


# ===========================================================================
# 11 · ทฤษฎีบทเมเนลอส
# ===========================================================================
def fig_menelaus() -> str:
    W, H = 500, 300
    A, B, C = P(110, 214), P(330, 214), P(236, 70)
    s = 0.34
    F = lerp(A, B, s)
    E = lerp(A, C, 0.62)
    dirv = (E - F).n
    D = line_inter(F, F + dirv * 1000, B, C)
    b = [txt(P(30, 32), "เส้นตัดหนึ่งเส้นกับด้านทั้งสามของสามเหลี่ยม", "t-tag", "start")]
    b.append(poly(A, B, C, cls="f-it", **{"data-id": "tri"}))
    b.append(poly(A, B, C, cls="s-ink"))
    b.append(line(B, D, "s-ink dash-fine"))
    b.append(line(F - dirv * 60, F + dirv * (dist(F, D) + 60), "s-accent",
                  **{"data-id": "trans"}))
    for nm, p, dx, dy, cls in (("A", A, -14, 8, "f-ink"), ("B", B, 8, 18, "f-ink"),
                               ("C", C, 0, -12, "f-ink")):
        b.append(dot(p, 4, cls))
        b.append(txt(P(p.x + dx, p.y + dy), nm, "t-name", **{"data-id": "lab" + nm}))
    for nm, p, dx, dy in (("D", D, 12, 2), ("E", E, 14, 0), ("F", F, 0, 20)):
        b.append(dot(p, 4.2, "f-accent", **{"data-id": "pt" + nm}))
        b.append(txt(P(p.x + dx, p.y + dy), nm, "t-name t-accent",
                       **{"data-id": "lab" + nm}))
    b.append(circ(F, 14, "handle-halo", **{"data-id": "halo"}))
    b.append(dot(F, 7, "handle", **{"data-id": "handle"}))
    b.append(txt(P(F.x, F.y + 38), "ลาก F", "hint"))
    r1 = dist(A, F) / dist(F, B)
    r2 = dist(B, D) / dist(D, C)
    r3 = dist(C, E) / dist(E, A)
    b.append(txt(P(30, 252), f"AF/FB = {r1:.3f}", "t-mono", "start", **{"data-id": "r1"}))
    b.append(txt(P(170, 252), f"BD/DC = {r2:.3f}", "t-mono", "start", **{"data-id": "r2"}))
    b.append(txt(P(310, 252), f"CE/EA = {r3:.3f}", "t-mono", "start", **{"data-id": "r3"}))
    b.append(txt(P(30, 280), f"ผลคูณ = {r1 * r2 * r3:.3f}", "t-val t-accent", "start",
                   **{"data-id": "prod"}))
    sv = svg(W, H, "".join(b), "fig-menelaus", "ทฤษฎีบทของเมเนลอส",
             "รูปสามเหลี่ยม ABC ถูกตัดด้วยเส้นตรงหนึ่งเส้นที่พบด้าน AB ที่จุด F "
             "ด้าน CA ที่จุด E และส่วนต่อของด้าน BC ที่จุด D "
             "ผลคูณของอัตราส่วนสามอัตราส่วนบนด้านทั้งสามมีค่าเท่ากับหนึ่ง")
    return figure(sv, "ลากจุด F ไปตามด้าน AB แล้วสังเกตว่า <b>ผลคูณของอัตราส่วนทั้งสาม</b> "
                      "ยังเท่ากับ 1 เสมอ — นี่คือสาระของทฤษฎีบทเมเนลอส "
                      "(ค่าที่คลาดจาก 1 เล็กน้อยมาจากการปัดเศษตำแหน่งพิกเซล)",
                  readout(f"(AF/FB)(BD/DC)(CE/EA) = {r1 * r2 * r3:.3f} ≈ 1"),
                  viz="menelaus",
                  data={"ax": A.x, "ay": A.y, "bx": B.x, "by": B.y,
                        "cx": C.x, "cy": C.y, "s0": s})


# ===========================================================================
# 12 · อัตราส่วนของพื้นที่
# ===========================================================================
def fig_arearatio() -> str:
    W, H = 440, 300
    A, B, C = P(180, 62), P(70, 214), P(330, 214)
    t = 0.42
    D = lerp(B, C, t)
    Hf = foot(A, B, C)
    b = [txt(P(30, 32), "ฐานต่างกัน สูงเท่ากัน", "t-tag", "start")]
    b.append(poly(A, B, D, cls="f-lt", **{"data-id": "abd"}))
    b.append(poly(A, D, C, cls="f-at", **{"data-id": "adc"}))
    b.append(poly(A, B, C, cls="s-ink"))
    b.append(line(A, D, "s-ink", **{"data-id": "cev"}))
    b.append(line(A, Hf, "s-teal dash", **{"data-id": "alt"}))
    b.append(right_mark(Hf, A, C, 10, "s-teal"))
    for nm, p, dx, dy in (("A", A, 0, -12), ("B", B, -14, 18), ("C", C, 14, 18)):
        b.append(dot(p, 4))
        b.append(txt(P(p.x + dx, p.y + dy), nm, "t-name", **{"data-id": "lab" + nm}))
    b.append(txt(P(Hf.x - 4, Hf.y + 20), "H", "t-name t-teal", **{"data-id": "labH"}))
    b.append(dot(D, 4.2, "f-accent"))
    b.append(txt(P(D.x, D.y + 22), "D", "t-name t-accent", **{"data-id": "labD"}))
    b.append(circ(D, 14, "handle-halo", **{"data-id": "halo"}))
    b.append(dot(D, 7, "handle", **{"data-id": "handle"}))
    s1, s2 = _tri_area(A, B, D), _tri_area(A, D, C)
    bd, dc = dist(B, D), dist(D, C)
    b.append(txt(P(30, 252), f"BD : DC = {bd / 10:.2f} : {dc / 10:.2f}  = {bd / dc:.3f}",
                   "t-mono", "start", **{"data-id": "ratio-len"}))
    b.append(txt(P(30, 278),
                   f"[ABD] : [ADC] = {s1 / 100:.2f} : {s2 / 100:.2f}  = {s1 / s2:.3f}",
                   "t-val t-accent", "start", **{"data-id": "ratio-area"}))
    sv = svg(W, H, "".join(b), "fig-arearatio", "อัตราส่วนของพื้นที่สามเหลี่ยมที่สูงเท่ากัน",
             "รูปสามเหลี่ยม ABC มีจุด D บนด้าน BC ทำให้เกิดสามเหลี่ยมสองรูปที่ใช้ความสูง "
             "จากจุด A เส้นเดียวกัน อัตราส่วนพื้นที่จึงเท่ากับอัตราส่วนความยาวฐาน")
    return figure(sv, "สามเหลี่ยม ABD และ ADC ใช้ความสูง \\(AH\\) เส้นเดียวกัน "
                      "ดังนั้น \\(\\dfrac{[ABD]}{[ADC]}=\\dfrac{BD}{DC}\\) — "
                      "ลากจุด D เพื่อยืนยัน",
                  readout("อัตราส่วนพื้นที่ = อัตราส่วนฐาน"), viz="arearatio",
                  data={"ax": A.x, "ay": A.y, "bx": B.x, "by": B.y, "cx": C.x, "cy": C.y})


# ===========================================================================
# 13 · มุมในส่วนโค้งเดียวกัน
# ===========================================================================
def fig_inscribed() -> str:
    W, H = 440, 300
    O, r = P(220, 150), 96
    aA, aB, aP = 212.0, 328.0, 80.0
    A, B, Pp = polar(O, r, aA), polar(O, r, aB), polar(O, r, aP)
    b = [txt(P(30, 32), "มุมที่จุดศูนย์กลาง vs มุมในส่วนโค้ง", "t-tag", "start")]
    b.append(circ(O, r, "s-ink", **{"data-id": "circle"}))
    b.append(path(arc_d(O, r, aB, aA), "s-accent thick", **{"data-id": "arcAB"}))
    b.append(line(A, B, "s-muted dash", **{"data-id": "chord"}))
    b.append(line(O, A, "s-link", **{"data-id": "oa"}))
    b.append(line(O, B, "s-link", **{"data-id": "ob"}))
    b.append(line(Pp, A, "s-teal", **{"data-id": "pa"}))
    b.append(line(Pp, B, "s-teal", **{"data-id": "pb"}))
    b.append(angle_mark(Pp, A, B, 30, "s-teal", **{"data-id": "mP"}))
    b.append(angle_mark(O, A, B, 34, "s-link", **{"data-id": "mO"}))
    for nm, p, dx, dy, cls in (("A", A, -14, 4, "f-ink"), ("B", B, 14, 4, "f-ink"),
                               ("O", O, -6, -10, "f-ink")):
        b.append(dot(p, 4, cls, **{"data-id": "pt" + nm}))
        b.append(txt(P(p.x + dx, p.y + dy), nm, "t-name", **{"data-id": "lab" + nm}))
    b.append(txt(P(Pp.x, Pp.y - 14), "P", "t-name t-teal", **{"data-id": "labP"}))
    b.append(circ(Pp, 14, "handle-halo", **{"data-id": "halo"}))
    b.append(dot(Pp, 7, "handle", **{"data-id": "handle"}))
    ip = _ang(A, Pp, B)
    cen = (aA - aB) % 360
    b.append(txt(_bis(Pp, A, B, 48), f"{round(ip)}°", "t-mono t-teal", dy=4,
                   **{"data-id": "tP"}))
    b.append(txt(_bis(O, A, B, 52), f"{round(cen)}°", "t-mono t-link", dy=4,
                   **{"data-id": "tO"}))
    b.append(txt(P(30, 276),
                   f"มุมที่จุดศูนย์กลาง {round(cen)}° = 2 × มุมในส่วนโค้ง {round(ip)}°",
                   "t-val", "start", **{"data-id": "eq"}))
    b.append(legend(H + 18, W, [("s-link", "มุมที่จุดศูนย์กลาง"),
                                ("s-teal", "มุมในส่วนโค้ง"),
                                ("s-accent thick", "ส่วนโค้ง AB")]))
    sv = svg(W, H + 36, "".join(b), "fig-inscribed", "มุมในส่วนโค้งของวงกลม",
             "วงกลมมีจุดศูนย์กลาง O และคอร์ด AB จุด P อยู่บนส่วนโค้งใหญ่ "
             "มุม APB มีขนาดครึ่งหนึ่งของมุม AOB และคงที่เมื่อเลื่อน P ไปตามส่วนโค้งเดิม")
    return figure(sv, "ลากจุด P ไปตามส่วนโค้ง — ขนาดของ \\(\\angle APB\\) ไม่เปลี่ยน "
                      "และเท่ากับครึ่งหนึ่งของ \\(\\angle AOB\\) เสมอ",
                  readout("ลาก P แล้วมุมยังเท่าเดิม"), viz="inscribed",
                  data={"ox": O.x, "oy": O.y, "r": r, "aa": aA, "ab": aB, "p0": aP})


# ===========================================================================
# 14 · คอร์ดและเส้นตั้งฉากจากจุดศูนย์กลาง
# ===========================================================================
def fig_chordperp() -> str:
    W, H = 420, 300
    O, r = P(190, 156), 104
    d0 = 46.0
    half = math.sqrt(r * r - d0 * d0)
    M = P(O.x, O.y - d0)
    A, B = P(M.x - half, M.y), P(M.x + half, M.y)
    b = [txt(P(30, 32), "เส้นจากจุดศูนย์กลางตั้งฉากกับคอร์ด", "t-tag", "start")]
    b.append(circ(O, r, "s-ink", **{"data-id": "circle"}))
    b.append(line(A, B, "s-accent thick", **{"data-id": "chord"}))
    b.append(line(O, M, "s-link", **{"data-id": "perp"}))
    b.append(line(O, A, "s-muted dash-fine", **{"data-id": "ra"}))
    b.append(line(O, B, "s-muted dash-fine", **{"data-id": "rb"}))
    u = (B - M).n * 12
    w = (O - M).n * 12
    b.append(seg(M + u, M + u + w, M + w, cls="s-link", **{"data-id": "rightmark"}))
    for nm, p, dx, dy, cls in (("A", A, -14, 4, "f-accent"), ("B", B, 14, 4, "f-accent"),
                               ("M", M, 0, -10, "f-link"), ("O", O, -4, 18, "f-ink")):
        b.append(dot(p, 4.2, cls, **{"data-id": "pt" + nm}))
        b.append(txt(P(p.x + dx, p.y + dy), nm, "t-name", **{"data-id": "lab" + nm}))
    b.append(circ(M, 14, "handle-halo", **{"data-id": "halo"}))
    b.append(dot(M, 7, "handle", **{"data-id": "handle"}))
    b.append(txt(mid(A, M), f"{half / 10:.2f}", "t-mono t-accent", dy=-9,
                   **{"data-id": "t-half1"}))
    b.append(txt(mid(M, B), f"{half / 10:.2f}", "t-mono t-accent", dy=-9,
                   **{"data-id": "t-half2"}))
    b.append(txt(P(mid(O, M).x + 12, mid(O, M).y + 4), f"d = {d0 / 10:.2f}",
                   "t-mono t-link", "start", **{"data-id": "t-d"}))
    b.append(txt(P(30, 254),
                   f"AM = MB = √(r² − d²) = √({r / 10:.1f}² − {d0 / 10:.2f}²) = {half / 10:.2f}",
                   "t-val", "start", **{"data-id": "eq"}))
    b.append(txt(P(30, 278), "ยิ่งคอร์ดอยู่ไกลจุดศูนย์กลาง ยิ่งสั้นลง", "t-mono", "start",
                   **{"data-id": "note2"}))
    sv = svg(W, H, "".join(b), "fig-chordperp", "เส้นตั้งฉากจากจุดศูนย์กลางแบ่งครึ่งคอร์ด",
             "วงกลมรัศมี r มีคอร์ด AB และเส้นจากจุดศูนย์กลาง O ตั้งฉากกับคอร์ดที่จุด M "
             "ทำให้ AM เท่ากับ MB และความยาวครึ่งคอร์ดเท่ากับรากที่สองของ r กำลังสองลบ d กำลังสอง")
    return figure(sv, "ลากจุด M เข้าออกจากจุดศูนย์กลาง: ระยะ \\(d\\) กับความยาวคอร์ด "
                      "สัมพันธ์กันด้วย \\(\\left(\\tfrac{AB}{2}\\right)^2 + d^2 = r^2\\) "
                      "ซึ่งก็คือทฤษฎีบทพีทาโกรัสในสามเหลี่ยม \\(OMB\\)",
                  readout("d กับความยาวคอร์ดสัมพันธ์กันแบบพีทาโกรัส"), viz="chordperp",
                  data={"ox": O.x, "oy": O.y, "r": r, "d0": d0})


# ===========================================================================
# 15 · มุมระหว่างเส้นสัมผัสกับคอร์ด
# ===========================================================================
def fig_tangentchord() -> str:
    W, H = 440, 300
    O, r = P(210, 160), 98
    aT, aB = 268.0, 20.0
    T, B = polar(O, r, aT), polar(O, r, aB)
    tdir = (T - O).n.perp
    aP = (aB + ((aT - aB) % 360) / 2 + 180) % 360
    Pp = polar(O, r, aP)

    # the tangent–chord angle equal to the inscribed angle at P is the one on
    # the far side of the chord from P — pick that tangent ray
    def _side(a, bb, p):
        return (bb.x - a.x) * (p.y - a.y) - (bb.y - a.y) * (p.x - a.x)

    arm_plus = T + tdir * 44
    t_arm = arm_plus if _side(T, B, arm_plus) * _side(T, B, Pp) < 0 else T - tdir * 44

    b = [txt(P(30, 32), "มุมระหว่างเส้นสัมผัสกับคอร์ด", "t-tag", "start")]
    b.append(circ(O, r, "s-ink", **{"data-id": "circle"}))
    b.append(line(T - tdir * 130, T + tdir * 130, "s-accent thick",
                  **{"data-id": "tangent"}))
    b.append(line(T, B, "s-link", **{"data-id": "chord"}))
    b.append(line(Pp, T, "s-teal", **{"data-id": "pt1"}))
    b.append(line(Pp, B, "s-teal", **{"data-id": "pt2"}))
    b.append(angle_mark(T, t_arm, B, 26, "s-accent", **{"data-id": "mTan"}))
    b.append(angle_mark(Pp, T, B, 28, "s-teal", **{"data-id": "mP"}))
    for nm, p, dx, dy, cls in (("T", T, 0, 22, "f-accent"), ("B", B, 14, -6, "f-link"),
                               ("P", Pp, -14, 4, "f-teal"), ("O", O, -4, -10, "f-ink")):
        b.append(dot(p, 4.2, cls, **{"data-id": "pt" + nm}))
        b.append(txt(P(p.x + dx, p.y + dy), nm, "t-name", **{"data-id": "lab" + nm}))
    b.append(circ(B, 14, "handle-halo", **{"data-id": "halo"}))
    b.append(dot(B, 7, "handle", **{"data-id": "handle"}))
    at1 = _ang(t_arm, T, B)
    ap = _ang(T, Pp, B)
    b.append(txt(_bis(T, t_arm, B, 42), f"{round(at1)}°", "t-mono t-accent", dy=4,
                   **{"data-id": "tTan"}))
    b.append(txt(_bis(Pp, T, B, 46), f"{round(ap)}°", "t-mono t-teal", dy=4,
                   **{"data-id": "tP"}))
    b.append(txt(P(30, 276),
                   f"มุมระหว่างเส้นสัมผัสกับคอร์ด {round(at1)}° = มุมในส่วนโค้งสลับ {round(ap)}°",
                   "t-val", "start", **{"data-id": "eq"}))
    sv = svg(W, H, "".join(b), "fig-tangentchord", "มุมระหว่างเส้นสัมผัสกับคอร์ด",
             "เส้นสัมผัสวงกลมที่จุด T กับคอร์ด TB ทำมุมกัน ขนาดของมุมนั้นเท่ากับมุม "
             "ในส่วนโค้งสลับที่จุด P ซึ่งอยู่บนส่วนโค้งอีกข้างของคอร์ด")
    return figure(sv, "ลากจุด B เพื่อเปลี่ยนคอร์ด — มุมระหว่างเส้นสัมผัสกับคอร์ด "
                      "เท่ากับมุมในส่วนโค้งสลับเสมอ (tangent–chord angle)",
                  readout("tangent–chord = มุมในส่วนโค้งสลับ"), viz="tangentchord",
                  data={"ox": O.x, "oy": O.y, "r": r, "at": aT, "b0": aB})


# ===========================================================================
# 16 · สี่เหลี่ยมแนบในวงกลม
# ===========================================================================
def fig_cyclicquad() -> str:
    W, H = 440, 300
    O, r = P(210, 152), 98
    ang = [142.0, 222.0, 314.0, 48.0]
    V = [polar(O, r, a) for a in ang]
    b = [txt(P(30, 32), "สี่เหลี่ยมที่มีจุดยอดทั้งสี่อยู่บนวงกลม", "t-tag", "start")]
    b.append(circ(O, r, "s-ink", **{"data-id": "circle"}))
    b.append(poly(*V, cls="f-at", **{"data-id": "quad"}))
    b.append(poly(*V, cls="s-ink"))
    for i, nm in enumerate("ABCD"):
        out = (V[i] - O).n * 18
        b.append(dot(V[i], 4.2, "f-ink", **{"data-id": "pt" + nm}))
        b.append(txt(V[i] + out, nm, "t-name", dy=5, **{"data-id": "lab" + nm}))
    cols = ["s-accent", "s-link", "s-accent", "s-link"]
    tcols = ["t-accent", "t-link", "t-accent", "t-link"]
    for i in range(4):
        p, a, c2 = V[i], V[(i + 3) % 4], V[(i + 1) % 4]
        b.append(angle_mark(p, a, c2, 26, cols[i], **{"data-id": f"m{i}"}))
        b.append(txt(_bis(p, a, c2, 42), f"{round(_ang(a, p, c2))}°",
                       "t-mono " + tcols[i], dy=4, **{"data-id": f"t{i}"}))
    b.append(circ(V[3], 14, "handle-halo", **{"data-id": "halo"}))
    b.append(dot(V[3], 7, "handle", **{"data-id": "handle"}))
    s02 = _ang(V[3], V[0], V[1]) + _ang(V[1], V[2], V[3])
    s13 = _ang(V[0], V[1], V[2]) + _ang(V[2], V[3], V[0])
    b.append(txt(P(30, 258), f"Â + Ĉ = {round(s02)}°", "t-val t-accent", "start",
                   **{"data-id": "sum1"}))
    b.append(txt(P(200, 258), f"B̂ + D̂ = {round(s13)}°", "t-val t-link", "start",
                   **{"data-id": "sum2"}))
    b.append(txt(P(30, 282), "มุมตรงข้ามของสี่เหลี่ยมแนบในวงกลมรวมกันได้ 180°",
                   "t-mono", "start"))
    sv = svg(W, H, "".join(b), "fig-cyclicquad", "สี่เหลี่ยมแนบในวงกลม",
             "รูปสี่เหลี่ยม ABCD มีจุดยอดทั้งสี่อยู่บนวงกลมเดียวกัน "
             "มุมตรงข้ามคู่ A กับ C และคู่ B กับ D แต่ละคู่รวมกันได้หนึ่งร้อยแปดสิบองศา")
    return figure(sv, "ลากจุด D ไปตามวงกลม — ผลรวมของมุมตรงข้ามยังเป็น "
                      "\\(180^\\circ\\) เสมอ ตามมาจากทฤษฎีบทมุมในส่วนโค้ง",
                  readout("มุมตรงข้ามรวมกันได้ 180°"), viz="cyclicquad",
                  data={"ox": O.x, "oy": O.y, "r": r,
                        "a1": ang[0], "a2": ang[1], "a3": ang[2], "a4": ang[3]})


# ===========================================================================
# 17 · จุดเซนทรอยด์
# ===========================================================================
def fig_centroid() -> str:
    W, H = 440, 300
    A, B, C = P(196, 58), P(76, 216), P(328, 216)
    Ma, Mb, Mc = mid(B, C), mid(A, C), mid(A, B)
    G = centroid(A, B, C)
    b = [txt(P(30, 32), "เส้นมัธยฐานสามเส้นพบกันที่จุดเดียว", "t-tag", "start")]
    b.append(poly(A, B, G, cls="f-at"))
    b.append(poly(B, C, G, cls="f-lt"))
    b.append(poly(C, A, G, cls="f-tt"))
    b.append(poly(A, B, C, cls="s-ink", **{"data-id": "tri"}))
    b.append(line(A, Ma, "s-accent", **{"data-id": "ma"}))
    b.append(line(B, Mb, "s-link", **{"data-id": "mb"}))
    b.append(line(C, Mc, "s-teal", **{"data-id": "mc"}))
    for i, (p, q) in enumerate(((B, C), (A, C), (A, B))):
        b.append(g(ticks(p, mid(p, q), i + 1, 6, "s-muted", 4)
                   + ticks(mid(p, q), q, i + 1, 6, "s-muted", 4),
                   **{"data-id": "tick"}))
    for nm, p, dx, dy in (("A", A, 0, -12), ("B", B, -14, 16), ("C", C, 14, 16)):
        b.append(dot(p, 4.2, "f-ink", **{"data-id": "pt" + nm}))
        b.append(txt(P(p.x + dx, p.y + dy), nm, "t-name", **{"data-id": "lab" + nm}))
    for nm, p in (("Ma", Ma), ("Mb", Mb), ("Mc", Mc)):
        b.append(dot(p, 3.4, "f-muted", **{"data-id": "pt" + nm}))
    b.append(txt(P(Ma.x + 16, Ma.y + 4), "Mₐ", "t-mono", "start", **{"data-id": "labMa"}))
    b.append(dot(G, 5.5, "f-accent", **{"data-id": "ptG"}))
    b.append(txt(P(G.x + 14, G.y + 4), "G", "t-name t-accent", "start",
                   **{"data-id": "labG"}))
    b.append(circ(A, 14, "handle-halo", **{"data-id": "halo"}))
    b.append(dot(A, 7, "handle", **{"data-id": "handle"}))
    ag, gm = dist(A, G), dist(G, Ma)
    s1, s2, s3 = _tri_area(A, B, G), _tri_area(B, C, G), _tri_area(C, A, G)
    b.append(txt(P(30, 256), f"AG : GM = {ag / 10:.2f} : {gm / 10:.2f} = {ag / gm:.2f} : 1",
                   "t-val t-accent", "start", **{"data-id": "ratio"}))
    b.append(txt(P(30, 280),
                   f"พื้นที่สามส่วนย่อย = {s1 / 100:.1f}, {s2 / 100:.1f}, {s3 / 100:.1f} (เท่ากัน)",
                   "t-mono", "start", **{"data-id": "areas"}))
    sv = svg(W, H, "".join(b), "fig-centroid", "จุดเซนทรอยด์ของรูปสามเหลี่ยม",
             "รูปสามเหลี่ยม ABC มีเส้นมัธยฐานสามเส้นตัดกันที่จุด G "
             "ซึ่งแบ่งแต่ละเส้นมัธยฐานในอัตราส่วนสองต่อหนึ่งจากจุดยอด "
             "และแบ่งรูปสามเหลี่ยมเป็นสามส่วนที่มีพื้นที่เท่ากัน")
    return figure(sv, "ลากจุด A ไปที่ไหนก็ได้ — เส้นมัธยฐานยังพบกันที่จุดเดียว "
                      "และอัตราส่วน \\(AG:GM_a = 2:1\\) ไม่เปลี่ยน",
                  readout("AG : GMₐ = 2 : 1"), viz="centroid",
                  data={"ax": A.x, "ay": A.y, "bx": B.x, "by": B.y, "cx": C.x, "cy": C.y})


# ===========================================================================
# 18 · วงกลมแนบในและแนบนอก
# ===========================================================================
def fig_incircle() -> str:
    W, H = 440, 320
    A, B, C = P(180, 56), P(72, 214), P(318, 214)
    a, bb, c = dist(B, C), dist(A, C), dist(A, B)
    s = (a + bb + c) / 2
    area = _tri_area(A, B, C)
    I = P((a * A.x + bb * B.x + c * C.x) / (a + bb + c),
          (a * A.y + bb * B.y + c * C.y) / (a + bb + c))
    r = area / s
    ra = area / (s - a)
    Ia = P((-a * A.x + bb * B.x + c * C.x) / (-a + bb + c),
           (-a * A.y + bb * B.y + c * C.y) / (-a + bb + c))
    b = [txt(P(30, 32), "วงกลมแนบในสัมผัสด้านทั้งสาม", "t-tag", "start")]
    b.append(poly(A, B, C, cls="f-it"))
    b.append(circ(Ia, ra, "s-violet dash", **{"data-id": "exc", "opacity": "0"}))
    b.append(circ(I, r, "s-accent thick", **{"data-id": "inc"}))
    b.append(poly(A, B, C, cls="s-ink", **{"data-id": "tri"}))
    b.append(line(A, I, "s-link dash-fine", **{"data-id": "bi1"}))
    b.append(line(B, I, "s-link dash-fine", **{"data-id": "bi2"}))
    b.append(line(C, I, "s-link dash-fine", **{"data-id": "bi3"}))
    for nm, p in (("tA", foot(I, B, C)), ("tB", foot(I, A, C)), ("tC", foot(I, A, B))):
        b.append(dot(p, 3.4, "f-accent", **{"data-id": nm}))
    for nm, p, dx, dy in (("A", A, 0, -12), ("B", B, -14, 16), ("C", C, 14, 16)):
        b.append(dot(p, 4.2, "f-ink", **{"data-id": "pt" + nm}))
        b.append(txt(P(p.x + dx, p.y + dy), nm, "t-name", **{"data-id": "lab" + nm}))
    b.append(dot(I, 5, "f-accent", **{"data-id": "ptI"}))
    b.append(txt(P(I.x, I.y + 16), "I", "t-name t-accent", **{"data-id": "labI"}))
    b.append(dot(Ia, 5, "f-violet", **{"data-id": "ptIa", "opacity": "0"}))
    b.append(txt(P(Ia.x, Ia.y + 18), "Iₐ", "t-name t-violet",
                   **{"data-id": "labIa", "opacity": "0"}))
    b.append(circ(A, 14, "handle-halo", **{"data-id": "halo"}))
    b.append(dot(A, 7, "handle", **{"data-id": "handle"}))
    b.append(txt(P(30, 268), f"r = พื้นที่ / s = {area / 100:.2f} / {s / 10:.2f} = {r / 10:.2f}",
                   "t-val t-accent", "start", **{"data-id": "f-r"}))
    b.append(txt(P(30, 292), f"rₐ = พื้นที่ / (s − a) = {ra / 10:.2f}", "t-mono", "start",
                   **{"data-id": "f-ra"}))
    sv = svg(W, H, "".join(b), "fig-incircle", "วงกลมแนบในและวงกลมแนบนอกของรูปสามเหลี่ยม",
             "รูปสามเหลี่ยม ABC มีวงกลมแนบในจุดศูนย์กลาง I สัมผัสด้านทั้งสามจากภายใน "
             "โดย I คือจุดตัดของเส้นแบ่งครึ่งมุม และมีวงกลมแนบนอกตรงข้ามจุด A ที่เลือกแสดงได้")
    ctl = (ctrl_btns(("excircle", "แสดงวงกลมแนบนอก", False))
           + readout(f"r = {r / 10:.2f}"))
    return figure(sv, "จุดศูนย์กลางวงกลมแนบในคือจุดตัดของ <b>เส้นแบ่งครึ่งมุม</b> "
                      "ทั้งสาม และ \\(r=\\dfrac{\\text{พื้นที่}}{s}\\) โดย \\(s\\) "
                      "คือครึ่งหนึ่งของความยาวรอบรูป",
                  ctl, viz="incircle",
                  data={"ax": A.x, "ay": A.y, "bx": B.x, "by": B.y, "cx": C.x, "cy": C.y})


# ===========================================================================
# 19 · สถิติ
# ===========================================================================
def fig_statviz(values: list[float]) -> str:
    W, H = 600, 260
    x0, x1, base = 60, 540, 200
    lo, hi = min(values), max(values)
    srt = sorted(values)
    n = len(srt)

    def sx(v): return x0 + (v - lo) / ((hi - lo) or 1) * (x1 - x0)

    def q(p):
        i = (n - 1) * p
        fl = int(math.floor(i))
        return srt[fl] + (srt[min(n - 1, fl + 1)] - srt[fl]) * (i - fl)

    mean = sum(values) / n
    med, q1, q3 = q(0.5), q(0.25), q(0.75)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / n)
    b = [txt(P(30, 32), "ค่ากลางและการกระจายของข้อมูลชุดเดียวกัน", "t-tag", "start")]
    b.append(line(P(x0 - 10, base), P(x1 + 10, base), "s-soft"))
    for i in range(6):
        v = lo + (hi - lo) * i / 5
        b.append(line(P(sx(v), base - 5), P(sx(v), base + 5), "s-soft"))
        b.append(txt(P(sx(v), base + 22), f"{v:g}", "t-mono"))
    b.append(rect(sx(q1), base - 30, max(1, sx(q3) - sx(q1)), 60, cls="f-lt",
                  **{"data-id": "box", "opacity": "0"}))
    b.append(rect(sx(mean - sd), base - 22, max(1, sx(mean + sd) - sx(mean - sd)), 44,
                  cls="f-tt", **{"data-id": "sdband", "opacity": "0"}))
    for v in srt:
        b.append(dot(P(sx(v), base), 5, "f-ink", **{"data-id": "pt", "opacity": "0.75"}))
    marks = (("mean", mean, "s-accent", "t-accent", "x̄"),
             ("median", med, "s-link", "t-link", "มัธยฐาน"),
             ("q1", q1, "s-muted", "t-mono", "Q1"),
             ("q3", q3, "s-muted", "t-mono", "Q3"))
    for key, v, scls, tcls, lab in marks:
        on = key == "mean"
        b.append(line(P(sx(v), base - 48), P(sx(v), base + 16), scls,
                      **{"data-id": "m-" + key, "opacity": "1" if on else "0.12"}))
        b.append(txt(P(sx(v), base - 54), lab, "t-mono " + tcls,
                       **{"data-id": "l-" + key, "opacity": "1" if on else "0.12"}))
    b.append(txt(P(30, 240),
                   f"x̄ = {mean:.2f} · มัธยฐาน = {med:.2f} · Q1 = {q1:.2f} · "
                   f"Q3 = {q3:.2f} · s.d. = {sd:.2f}", "t-mono", "start",
                   **{"data-id": "stat"}))
    sv = svg(W, H, "".join(b), "fig-statviz", "ค่ากลางและการกระจายของข้อมูล",
             "เส้นจำนวนแสดงข้อมูลเป็นจุดเรียงตามค่า พร้อมเส้นกำกับค่าเฉลี่ยเลขคณิต "
             "มัธยฐาน ควอร์ไทล์ที่หนึ่งและสาม และแถบแสดงช่วงหนึ่งส่วนเบี่ยงเบนมาตรฐาน")
    ctl = (ctrl_btns(("mean", "ค่าเฉลี่ย", True), ("median", "มัธยฐาน", False),
                     ("quart", "ควอร์ไทล์", False), ("sd", "ส่วนเบี่ยงเบนมาตรฐาน", False),
                     ("all", "ทั้งหมด", False), group="stat")
           + readout(f"n = {n} · x̄ = {mean:.2f} · s.d. = {sd:.2f}"))
    return figure(sv, "ค่าเฉลี่ยถูกค่าผิดปกติดึงได้ง่าย แต่มัธยฐานไม่ — "
                      "กดสลับดูว่าค่ากลางแต่ละแบบอยู่ตำแหน่งใดในข้อมูลชุดเดียวกัน",
                  ctl, viz="statviz",
                  data={"x0": x0, "x1": x1, "base": base,
                        "values": ",".join(str(v) for v in values)})


# ===========================================================================
# 20 · กราฟฟังก์ชัน (Desmos-style)
# ===========================================================================
def fig_graphlab() -> str:
    W, H = 600, 320
    o = P(300, 170)
    u = 26
    b = [arrowdefs()]
    b.append(grid(o.x - 11 * u, o.y - 6 * u, o.x + 11 * u, o.y + 5 * u, u))
    b.append(axes(o, 11 * u + 6, 6 * u + 6, u, 11, 5))
    pts = []
    x = -7.0
    while x <= 7.0:
        y = x * x
        if abs(y) < 7:
            pts.append(P(o.x + x * u, o.y - y * u))
        x += 0.08
    b.append(seg(*pts, cls="s-accent thick", **{"data-id": "curve"}))
    b.append(dot(o, 5, "f-accent", **{"data-id": "vertex"}))
    b.append(txt(P(30, 302), "y = 1x² + 0x + 0", "t-val t-accent", "start",
                   **{"data-id": "eq"}))
    sv = svg(W, H, "".join(b), "fig-graphlab", "กราฟของฟังก์ชันที่ปรับสัมประสิทธิ์ได้",
             "ระนาบพิกัดแสดงกราฟของฟังก์ชันที่เลือกได้ระหว่างเส้นตรง พาราโบลา "
             "และค่าสัมบูรณ์ โดยปรับสัมประสิทธิ์แล้วกราฟเปลี่ยนรูปทันที")
    ctl = (ctrl_btns(("quad", "y = ax²+bx+c", True), ("lin", "y = ax+c", False),
                     ("abs", "y = a|x|+c", False), group="kind")
           + ctrl_range("a", -3, 3, 0.1, 1, "a")
           + ctrl_range("b", -4, 4, 0.1, 0, "b")
           + ctrl_range("c", -4, 4, 0.1, 0, "c")
           + readout("y = x²"))
    return figure(sv, "ปรับ \\(a\\) เพื่อดูการยืด–หดและการพลิกกราฟ ปรับ \\(b\\) "
                      "เพื่อเลื่อนจุดยอดในแนวเฉียง และปรับ \\(c\\) "
                      "เพื่อเลื่อนกราฟขึ้นลง — เหมือนที่ทำได้ใน Desmos",
                  ctl, viz="graphlab", data={"ox": o.x, "oy": o.y, "unit": u, "w": W})


# ===========================================================================
# 21 · การพิสูจน์แบบทีละขั้น (generic, data-driven)
# ===========================================================================
def fig_proof(slug: str, title: str, desc: str, w: int, h: int,
              body: str, rows: list[tuple[str, str]], caption: str) -> str:
    """A figure whose SVG groups carry data-step, paired with a reason table
    whose rows carry data-prow.  viz.js reveals them together."""
    sv = svg(w, h, body, slug, title, desc)
    table_rows = "".join(
        f'<tr data-prow="{i + 1}"><td>{a}</td><td>{b}</td></tr>'
        for i, (a, b) in enumerate(rows)
    )
    tbl = ('<table class="tbl"><thead><tr><th>ข้อความ</th><th>เหตุผล</th></tr></thead>'
           f"<tbody>{table_rows}</tbody></table>")
    ctl = (ctrl_btns(("reset", "เริ่มต้น", False), ("prev", "ย้อน", False),
                     ("next", "ขั้นต่อไป", False), ("all", "แสดงทั้งหมด", False))
           + readout(f"ขั้นที่ {len(rows)} / {len(rows)}"))
    return figure(sv + tbl, caption, ctl, viz="proof", fid=slug)
