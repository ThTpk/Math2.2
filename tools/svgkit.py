# -*- coding: utf-8 -*-
"""
svgkit — geometry + SVG builders for the math figures.

Everything is authored statically: each figure is a complete, labelled SVG that
carries its full meaning with JavaScript disabled.  viz.js then attaches
interaction to known element ids.

Colours are CSS classes (see the SVG stylesheet in assets/css/site.css) so the
figures follow light/dark themes automatically.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from html import escape


# --------------------------------------------------------------- geometry ---
@dataclass(frozen=True)
class P:
    x: float
    y: float

    def __add__(self, o): return P(self.x + o.x, self.y + o.y)
    def __sub__(self, o): return P(self.x - o.x, self.y - o.y)
    def __mul__(self, k): return P(self.x * k, self.y * k)
    __rmul__ = __mul__

    def __iter__(self): return iter((self.x, self.y))

    @property
    def n(self):
        """unit vector"""
        d = math.hypot(self.x, self.y) or 1.0
        return P(self.x / d, self.y / d)

    @property
    def perp(self): return P(-self.y, self.x)

    def len(self): return math.hypot(self.x, self.y)

    def rot(self, deg, about=None):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        o = about or P(0, 0)
        dx, dy = self.x - o.x, self.y - o.y
        return P(o.x + dx * c - dy * s, o.y + dx * s + dy * c)

    def r(self, nd=2): return P(round(self.x, nd), round(self.y, nd))


def lerp(a: P, b: P, t: float) -> P:
    return P(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)


def dist(a: P, b: P) -> float:
    return math.hypot(b.x - a.x, b.y - a.y)


def mid(a: P, b: P) -> P:
    return lerp(a, b, 0.5)


def polar(c: P, r: float, deg: float) -> P:
    """Point on a circle. Angles are mathematical (CCW) but y is flipped for SVG."""
    a = math.radians(deg)
    return P(c.x + r * math.cos(a), c.y - r * math.sin(a))


def ang_of(c: P, p: P) -> float:
    """Mathematical angle (deg, CCW, y-flipped) of p seen from c."""
    return math.degrees(math.atan2(c.y - p.y, p.x - c.x)) % 360


def line_inter(a: P, b: P, c: P, d: P):
    """Intersection of line ab and line cd (None if parallel)."""
    x1, y1, x2, y2 = a.x, a.y, b.x, b.y
    x3, y3, x4, y4 = c.x, c.y, d.x, d.y
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return P(x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def foot(p: P, a: P, b: P) -> P:
    """Foot of the perpendicular from p to line ab."""
    ab = b - a
    t = ((p - a).x * ab.x + (p - a).y * ab.y) / (ab.x ** 2 + ab.y ** 2)
    return lerp(a, b, t)


def circumcenter(a: P, b: P, c: P) -> P:
    d = 2 * (a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y))
    ux = ((a.x ** 2 + a.y ** 2) * (b.y - c.y) + (b.x ** 2 + b.y ** 2) * (c.y - a.y)
          + (c.x ** 2 + c.y ** 2) * (a.y - b.y)) / d
    uy = ((a.x ** 2 + a.y ** 2) * (c.x - b.x) + (b.x ** 2 + b.y ** 2) * (a.x - c.x)
          + (c.x ** 2 + c.y ** 2) * (b.x - a.x)) / d
    return P(ux, uy)


def incenter(a: P, b: P, c: P):
    la, lb, lc = dist(b, c), dist(a, c), dist(a, b)
    s = la + lb + lc
    ctr = P((la * a.x + lb * b.x + lc * c.x) / s, (la * a.y + lb * b.y + lc * c.y) / s)
    area = abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2
    return ctr, 2 * area / s


def centroid(a: P, b: P, c: P) -> P:
    return P((a.x + b.x + c.x) / 3, (a.y + b.y + c.y) / 3)


def f(v: float) -> str:
    """Format a coordinate: trim trailing zeros."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


# ----------------------------------------------------------------- shapes ---
# ---------------------------------------------------------- path "d" strings ---
def dseg_d(*pts: P, close: bool = False) -> str:
    return "M " + " L ".join(f"{f(p.x)} {f(p.y)}" for p in pts) + (" Z" if close else "")


def arc_d(c: P, r: float, a0: float, a1: float) -> str:
    """`d` attribute of an arc from mathematical angle a0 to a1 (CCW)."""
    p0, p1 = polar(c, r, a0), polar(c, r, a1)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M {f(p0.x)} {f(p0.y)} A {f(r)} {f(r)} 0 {large} 0 {f(p1.x)} {f(p1.y)}"


def angle_d(v: P, a: P, b: P, r: float) -> str:
    """`d` attribute of the arc marking angle a-v-b."""
    a0, a1 = ang_of(v, a), ang_of(v, b)
    if (a1 - a0) % 360 > 180:
        a0, a1 = a1, a0
    return arc_d(v, r, a0, a1)


def path(d: str, cls: str = "s-ink", **kw) -> str:
    return _el("path", d=d, **{"class": cls}, **kw)


def line(a: P, b: P, cls: str = "s-ink", **kw) -> str:
    return _el("line", x1=f(a.x), y1=f(a.y), x2=f(b.x), y2=f(b.y), **{"class": cls}, **kw)


def seg(*pts: P, cls: str = "s-ink", close: bool = False, **kw) -> str:
    d = "M " + " L ".join(f"{f(p.x)} {f(p.y)}" for p in pts) + (" Z" if close else "")
    return path(d, cls, **kw)


def poly(*pts: P, cls: str = "s-ink", **kw) -> str:
    pt = " ".join(f"{f(p.x)},{f(p.y)}" for p in pts)
    return _el("polygon", points=pt, **{"class": cls}, **kw)


def circ(c: P, r: float, cls: str = "s-ink", **kw) -> str:
    return _el("circle", cx=f(c.x), cy=f(c.y), r=f(r), **{"class": cls}, **kw)


def dot(p: P, r: float = 3.4, cls: str = "f-ink", **kw) -> str:
    return _el("circle", cx=f(p.x), cy=f(p.y), r=f(r), **{"class": cls}, **kw)


def rect(x, y, w, h, cls="s-ink", rx=0, **kw) -> str:
    a = dict(x=f(x), y=f(y), width=f(w), height=f(h))
    if rx:
        a["rx"] = f(rx)
    return _el("rect", **a, **{"class": cls}, **kw)


def arc(c: P, r: float, a0: float, a1: float, cls: str = "s-muted", **kw) -> str:
    """Arc from mathematical angle a0 to a1 (CCW positive)."""
    p0, p1 = polar(c, r, a0), polar(c, r, a1)
    sweep = (a1 - a0) % 360
    large = 1 if sweep > 180 else 0
    d = f"M {f(p0.x)} {f(p0.y)} A {f(r)} {f(r)} 0 {large} 0 {f(p1.x)} {f(p1.y)}"
    return path(d, cls, **kw)


def angle_mark(v: P, a: P, b: P, r: float = 22, cls: str = "s-muted",
               arcs: int = 1, gap: float = 4, **kw) -> str:
    """One or more concentric arcs marking angle ∠avb at vertex v."""
    a0, a1 = ang_of(v, a), ang_of(v, b)
    if (a1 - a0) % 360 > 180:
        a0, a1 = a1, a0
    out = []
    for i in range(arcs):
        out.append(arc(v, r + i * gap, a0, a1, cls, **kw))
    return "".join(out)


def right_mark(v: P, a: P, b: P, s: float = 11, cls: str = "s-muted") -> str:
    u, w = (a - v).n * s, (b - v).n * s
    return seg(v + u, v + u + w, v + w, cls=cls)


def ticks(a: P, b: P, n: int = 1, s: float = 7, cls: str = "s-muted", gap: float = 4) -> str:
    """Congruence tick marks across segment ab."""
    m = mid(a, b)
    u = (b - a).n
    pp = u.perp * s
    out = []
    start = -(n - 1) * gap / 2
    for i in range(n):
        c = m + u * (start + i * gap)
        out.append(line(c - pp, c + pp, cls))
    return "".join(out)


def arrowdefs(ids=("ar", "ar-a", "ar-l", "ar-t")) -> str:
    """Arrow markers: muted / accent / link / teal."""
    css = {"ar": "f-muted", "ar-a": "f-accent", "ar-l": "f-link", "ar-t": "f-teal"}
    out = []
    for i in ids:
        out.append(
            f'<marker id="{i}" markerWidth="8" markerHeight="6" refX="7" refY="3" '
            f'orient="auto"><polygon points="0 0, 8 3, 0 6" class="{css[i]}"/></marker>'
        )
    return "<defs>" + "".join(out) + "</defs>"


def arrow(a: P, b: P, cls: str = "s-muted", m: str = "ar", **kw) -> str:
    return line(a, b, cls, **{"marker-end": f"url(#{m})"}, **kw)


# ------------------------------------------------------------------- text ---
def txt(p: P, s: str, cls: str = "t-name", anchor: str = "middle",
        dy: float = 0, **kw) -> str:
    a = dict(x=f(p.x), y=f(p.y + dy))
    if anchor != "start":
        a["text-anchor"] = anchor
    return _el("text", **a, **{"class": cls}, **kw, _body=escape(s))


def label(p: P, s: str, cls: str = "t-name", anchor: str = "middle",
          dy: float = 0, pad: float = 4, w: float | None = None,
          h: float = 15, mask: bool = True, **kw) -> str:
    """Text with an opaque mask behind it so lines don't bleed through."""
    out = []
    if mask:
        ww = w if w is not None else max(14, len(s) * 7.6 + pad * 2)
        if anchor == "middle":
            mx = p.x - ww / 2
        elif anchor == "end":
            mx = p.x - ww
        else:
            mx = p.x - pad
        out.append(rect(mx, p.y + dy - h + 4, ww, h, cls="mask", rx=2))
    out.append(txt(p, s, cls, anchor, dy, **kw))
    return "".join(out)


def tag(p: P, s: str, cls: str = "t-tag", anchor: str = "start") -> str:
    return txt(p, s, cls, anchor)


def vertex(p: P, name: str, out_dir: P, cls: str = "f-ink",
           tcls: str = "t-name", d: float = 16, r: float = 3.4) -> str:
    """A labelled point: dot + name pushed out along out_dir."""
    q = p + out_dir.n * d
    return dot(p, r, cls) + txt(q, name, tcls, "middle", 4.5)


# ------------------------------------------------------------------ frame ---
def svg(view_w: int, view_h: int, body: str, slug: str, title: str, desc: str,
        cls: str = "", extra: str = "") -> str:
    """Accessible SVG figure frame (title first child, prefixed ids)."""
    return (
        f'<svg viewBox="0 0 {view_w} {view_h}" role="img" '
        f'aria-labelledby="{slug}-t {slug}-d"'
        + (f' class="{cls}"' if cls else "")
        + (f" {extra}" if extra else "")
        + ">"
        f'<title id="{slug}-t">{escape(title)}</title>'
        f'<desc id="{slug}-d">{escape(desc)}</desc>'
        f'<rect width="100%" height="100%" fill="var(--paper-2)"/>'
        f"{body}</svg>"
    )


def grid(x0, y0, x1, y1, step=20, cls="s-rule") -> str:
    """Faint cartesian grid."""
    out = []
    v = x0
    while v <= x1 + 0.1:
        out.append(line(P(v, y0), P(v, y1), cls))
        v += step
    v = y0
    while v <= y1 + 0.1:
        out.append(line(P(x0, v), P(x1, v), cls))
        v += step
    return "".join(out)


def axes(o: P, x1: float, y1: float, step: float = 20, nx: int = 5, ny: int = 5,
         labels: bool = True) -> str:
    """x/y axes with arrowheads and unit ticks, origin at o."""
    out = [arrow(P(o.x - step * nx - 8, o.y), P(o.x + x1, o.y), "s-soft"),
           arrow(P(o.x, o.y + step * ny + 8), P(o.x, o.y - y1), "s-soft")]
    if labels:
        out.append(txt(P(o.x + x1 + 2, o.y + 4), "x", "t-mono", "start"))
        out.append(txt(P(o.x - 10, o.y - y1 + 2), "y", "t-mono", "middle"))
    for i in range(-nx, nx + 1):
        if i == 0:
            continue
        p = P(o.x + i * step, o.y)
        out.append(line(P(p.x, p.y - 3), P(p.x, p.y + 3), "s-soft"))
    for i in range(-ny, ny + 1):
        if i == 0:
            continue
        p = P(o.x, o.y - i * step)
        out.append(line(P(p.x - 3, p.y), P(p.x + 3, p.y), "s-soft"))
    return "".join(out)


def legend(y: float, w: float, items: list[tuple[str, str]], x0: float = 24) -> str:
    """Horizontal legend strip at the bottom of a figure.

    items: list of (css class for the swatch line, label text)
    """
    out = [line(P(x0, y - 10), P(w - x0, y - 10), "s-rule"),
           txt(P(x0, y + 8), "LEGEND", "t-tag", "start")]
    x = x0 + 64
    for cls, text in items:
        out.append(line(P(x, y + 4), P(x + 20, y + 4), cls))
        out.append(txt(P(x + 26, y + 8), text, "t-mono", "start"))
        x += 30 + max(60, len(text) * 6.4)
    return "".join(out)


# ------------------------------------------------------------------ utils ---
def _el(name: str, _body: str | None = None, **attrs) -> str:
    parts = []
    for k, v in attrs.items():
        if v is None:
            continue
        parts.append(f'{k.replace("_", "-")}="{v}"')
    a = (" " + " ".join(parts)) if parts else ""
    if _body is None:
        return f"<{name}{a}/>"
    return f"<{name}{a}>{_body}</{name}>"


def g(body: str, **attrs) -> str:
    return _el("g", _body=body, **attrs)
