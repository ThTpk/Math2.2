# -*- coding: utf-8 -*-
"""layout — HTML page templates shared by every generated page.

Scope rule for this site: pages carry the subject name and the mathematics
only.  No syllabus apparatus (course description, learning outcomes, weekly
schedule, teaching methods, score weighting) and no teacher information.
"""
from __future__ import annotations

from html import escape

SITE = "คณิตศาสตร์ ม.2"

COURSES = [
    ("c22122", "คณิตศาสตร์ 4"),
    ("c22292", "คณิตศาสตร์พัฒนาศักยภาพ 4"),
    ("c22294", "เทคโนโลยีเพื่อการศึกษาทางคณิตศาสตร์"),
]

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    "family=IBM+Plex+Sans+Thai:wght@400;500;600&"
    "family=IBM+Plex+Mono:wght@400;500;600&"
    "family=Noto+Serif+Thai:wght@400;600;700&"
    'display=swap" rel="stylesheet">'
)

# CHTML output, not SVG: the SVG renderer has no Thai glyphs and breaks
# combining vowels/tone marks inside \text{...}.  mtextInheritFont makes
# \text{} fall back to the page's Thai font instead.
MATHJAX = """<script>
window.MathJax = {
  tex: { inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']],
         processEscapes: true },
  options: { skipHtmlTags: ['script','noscript','style','textarea','pre','code'] },
  chtml: { mtextInheritFont: true, scale: 1.0 },
  startup: { typeset: true }
};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js"></script>"""

NAV_SHORT = {
    "c22122": "คณิตศาสตร์ 4",
    "c22292": "พัฒนาศักยภาพ 4",
    "c22294": "เทคโนโลยีคณิตศาสตร์",
}


# ----------------------------------------------------------------- helpers ---
def _nav(depth: int, active: str | None) -> str:
    r = "../" * depth
    cur_home = ' aria-current="page"' if active == "home" else ""
    links = [f'<a href="{r}index.html"{cur_home}>หน้าแรก</a>']
    for slug, name in COURSES:
        cur = ' aria-current="page"' if active == slug else ""
        links.append(
            f'<a href="{r}{slug}/index.html"{cur} title="{escape(name)}">'
            f"{escape(NAV_SHORT[slug])}</a>"
        )
    return (
        '<nav class="nav">'
        f'<a class="nav-brand" href="{r}index.html">คณิต<span>ศาสตร์</span> ม.2</a>'
        f'<div class="nav-links">{"".join(links)}'
        '<button class="theme-btn" type="button" aria-label="สลับโหมดสี">☾</button>'
        "</div></nav>"
    )


def _head(title: str, desc: str, depth: int, extra_head: str = "") -> str:
    r = "../" * depth
    return (
        "<!DOCTYPE html>\n"
        '<html lang="th" data-theme="light">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(title)}</title>\n"
        f'<meta name="description" content="{escape(desc)}">\n'
        f"{FONTS}\n"
        f'<link rel="stylesheet" href="{r}assets/css/site.css">\n'
        f"{MATHJAX}\n{extra_head}\n</head>\n<body>\n"
    )


def _foot(depth: int, scripts: list[str] | None = None) -> str:
    r = "../" * depth
    s = [f'<script src="{r}assets/js/site.js"></script>']
    for x in scripts or []:
        s.append(f'<script src="{r}assets/js/{x}"></script>')
    return (
        '<footer class="site"><div class="wrap">'
        f"{escape(SITE)} · สื่อการเรียนรู้แบบอินเทอร์แอกทีฟ"
        "</div></footer>\n" + "\n".join(s) + "\n</body>\n</html>\n"
    )


# -------------------------------------------------------------- unit page ---
def unit_page(u: dict) -> str:
    """Render a lesson page: subject name, the mathematics, worked examples,
    interactive figures and the end-of-lesson drill."""
    depth = 1
    body_html, toc = _sections(u["sections"])
    toc += '<li><a href="#drill">แบบฝึกหัดท้ายบท</a></li>'

    pager = []
    if u.get("prev"):
        pager.append(f'<a class="pl" href="{u["prev"][0]}">{escape(u["prev"][1])}</a>')
    else:
        pager.append("<span></span>")
    if u.get("next"):
        pager.append(f'<a class="pr" href="{u["next"][0]}">{escape(u["next"][1])}</a>')
    else:
        pager.append("<span></span>")

    scripts = ["viz.js"]
    extra = ""
    if u.get("needs3d"):
        scripts.append("viz3d.js")
        extra = ('<script defer src="https://cdn.jsdelivr.net/npm/three@0.160.0/'
                 'build/three.min.js"></script>')

    n_ex = len(u["exercises"])
    return (
        _head(f'{u["title"]} · {u["course_name"]}', _plain(u["lead"])[:150], depth, extra)
        + _nav(depth, u["course_slug"])
        + '<div class="wrap"><div class="page">'
        + f'<aside class="toc"><div class="toc-label">หัวข้อในบทนี้</div><ol>{toc}</ol></aside>'
        + "<main>"
        + f'<p class="eyebrow">{escape(u["course_name"])}</p>'
        + f'<h1>{escape(u["title"])}</h1>'
        + f'<p class="lead">{u["lead"]}</p>'
        + '<div class="badges">'
        + "".join(f'<span class="badge">{escape(b)}</span>' for b in u.get("badges", []))
        + f'<span class="badge on">แบบฝึกหัด {n_ex} ข้อ</span>'
        + "</div>"
        + body_html
        + _drill(u)
        + f'<div class="pager">{"".join(pager)}</div>'
        + "</main></div></div>"
        + _foot(depth, scripts)
    )


def _plain(s: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", s)


def _sections(sections: list[dict]) -> tuple[str, str]:
    out, toc = [], []
    for s in sections:
        toc.append(f'<li><a href="#{s["id"]}">{escape(s["title"])}</a></li>')
        out.append(f'<section id="{s["id"]}"><h2>{escape(s["title"])}</h2>')
        out.append(render_blocks(s["blocks"]))
        out.append("</section>")
    return "".join(out), "".join(toc)


def render_blocks(blocks) -> str:
    out = []
    for b in blocks:
        kind = b[0]
        if kind == "p":
            out.append(f"<p>{b[1]}</p>")
        elif kind == "h3":
            out.append(f"<h3>{escape(b[1])}</h3>")
        elif kind == "h4":
            out.append(f"<h4>{escape(b[1])}</h4>")
        elif kind == "html":
            out.append(b[1])
        elif kind == "ul":
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in b[1]) + "</ul>")
        elif kind == "ol":
            out.append("<ol>" + "".join(f"<li>{x}</li>" for x in b[1]) + "</ol>")
        elif kind == "box":
            _, cls, lab, inner = b
            inner = inner if isinstance(inner, str) else render_blocks(inner)
            out.append(
                f'<div class="box {cls}"><span class="box-label">{escape(lab)}</span>{inner}</div>'
            )
        elif kind == "fig":
            out.append(b[1])
        elif kind == "ex":
            out.append(worked(b[1]))
        elif kind == "table":
            out.append(table(b[1], b[2]))
        else:  # pragma: no cover
            raise ValueError(f"unknown block kind: {kind}")
    return "".join(out)


LVL = {"med": ("ปานกลาง", ""), "hard": ("ยาก", "hard"), "apply": ("ประยุกต์", "apply")}


def worked(e: dict) -> str:
    lab, cls = LVL[e.get("lvl", "med")]
    steps = "".join(f"<li>{s}</li>" for s in e["steps"])
    ans = f'<p class="ans">{e["ans"]}</p>' if e.get("ans") else ""
    return (
        '<div class="ex"><div class="ex-head">'
        f'<span class="ex-tag">ตัวอย่าง {e["n"]}</span>'
        f'<span class="ex-lvl {cls}">{lab}</span>'
        + (f'<span class="ex-lvl">{escape(e["topic"])}</span>' if e.get("topic") else "")
        + "</div>"
        f'<div class="ex-body">{e["q"]}</div>'
        '<div class="ex-sol"><p class="sol-label">แนวคิดและวิธีทำ</p>'
        f'<ol class="steps">{steps}</ol>{ans}</div></div>'
    )


def table(headers: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="tbl"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def _drill(u: dict) -> str:
    qs = u["exercises"]
    rows = []
    for i, q in enumerate(qs, 1):
        lvl = q.get("lvl", "med")
        lab, cls = LVL[lvl]
        sid = f'{u["slug"]}-s{i}'
        sol = q.get("sol", "")
        rows.append(
            f'<div class="q" data-lvl="{lvl}">'
            f'<div class="qn">{i}.</div>'
            f'<div class="qbody">{q["q"]}</div>'
            '<div class="qmeta">'
            f'<span class="ex-lvl {cls}">{lab}</span>'
            + (f'<span class="ex-lvl">{escape(q["tag"])}</span>' if q.get("tag") else "")
            + (f'<button class="sol-toggle" type="button" aria-expanded="false" '
               f'aria-controls="{sid}">ดูเฉลย</button>' if sol else "")
            + "</div>"
            + (f'<div class="qsol" id="{sid}" hidden>{sol}</div>' if sol else "")
            + "</div>"
        )
    counts = {k: sum(1 for q in qs if q.get("lvl", "med") == k) for k in LVL}
    return (
        '<section id="drill" class="drill"><div class="drill-head">'
        "<h3>แบบฝึกหัดท้ายบท</h3>"
        f'<span class="drill-stat">แสดง {len(qs)} / {len(qs)} ข้อ</span></div>'
        "<p>โจทย์เรียงจากปานกลางไปยาก และปิดท้ายด้วยโจทย์ประยุกต์ "
        "ลองทำด้วยตัวเองให้ครบก่อนเปิดเฉลย</p>"
        '<div class="drill-filter">'
        f'<button class="btn" type="button" data-filter="all" aria-pressed="true">ทั้งหมด ({len(qs)})</button>'
        f'<button class="btn" type="button" data-filter="med" aria-pressed="false">ปานกลาง ({counts["med"]})</button>'
        f'<button class="btn" type="button" data-filter="hard" aria-pressed="false">ยาก ({counts["hard"]})</button>'
        f'<button class="btn" type="button" data-filter="apply" aria-pressed="false">ประยุกต์ ({counts["apply"]})</button>'
        '<button class="btn" type="button" data-sol-all="show">เปิดเฉลยทั้งหมด</button>'
        '<button class="btn" type="button" data-sol-all="hide">ปิดเฉลยทั้งหมด</button>'
        "</div>" + "".join(rows) + "</section>"
    )


# -------------------------------------------------------------- figure box ---
def figure(svg_markup: str, caption: str, controls: str = "",
           viz: str | None = None, fid: str | None = None,
           data: dict | None = None) -> str:
    attrs = ' class="fig"'
    if viz:
        attrs += f' data-viz="{viz}"'
    if fid:
        attrs += f' id="{fid}"'
    for k, v in (data or {}).items():
        attrs += f' data-{k}="{v}"'
    return (
        f"<figure{attrs}>"
        f'<div class="fig-body">{svg_markup}</div>'
        + (f'<div class="fig-ctrl">{controls}</div>' if controls else "")
        + f"<figcaption>{caption}</figcaption></figure>"
    )


def ctrl_btns(*items, group: str = "") -> str:
    """items: (value, label, pressed)"""
    out = []
    for v, lab, pressed in items:
        out.append(
            f'<button type="button" data-act="{v}"'
            + (f' data-group="{group}"' if group else "")
            + f' aria-pressed="{"true" if pressed else "false"}">{escape(lab)}</button>'
        )
    return "".join(out)


def ctrl_range(name: str, lo, hi, step, val, label: str) -> str:
    return (
        f'<label for="r-{name}">{escape(label)}</label>'
        f'<input type="range" id="r-{name}" data-input="{name}" '
        f'min="{lo}" max="{hi}" step="{step}" value="{val}">'
    )


def readout(text: str = "") -> str:
    return f'<span class="fig-readout" data-readout>{text}</span>'


# ------------------------------------------------------------- index pages ---
def course_index(c: dict) -> str:
    """Subject name + the list of lessons.  Nothing else."""
    depth = 1
    rows = []
    for i, un in enumerate(c["units"], 1):
        rows.append(
            f'<a class="unit-row" href="{un["href"]}">'
            f'<span class="num">{i}</span>'
            f'<span><span class="title">{escape(un["title"])}</span><br>'
            f'<span class="sub">{escape(un["sub"])}</span></span>'
            f'<span class="count">{un["n"]} ข้อ</span></a>'
        )
    return (
        _head(f'{c["name"]} · {SITE}', c["short"], depth)
        + _nav(depth, c["slug"])
        + '<div class="wrap"><main>'
        + f'<p class="eyebrow">{escape(SITE)}</p>'
        + f'<h1>{escape(c["name"])}</h1>'
        + f'<p class="lead">{c["short"]}</p>'
        + "<h2>บทเรียน</h2>"
        + f'<div class="unit-list">{"".join(rows)}</div>'
        + "</main></div>"
        + _foot(depth)
    )


def home(courses: list[dict]) -> str:
    cards = []
    for c in courses:
        topics = " · ".join(u["title"] for u in c["units"][:4])
        if len(c["units"]) > 4:
            topics += " · …"
        cards.append(
            f'<a class="course-card" href="{c["slug"]}/index.html">'
            f'<span class="code">{len(c["units"])} บทเรียน</span>'
            f'<h3>{escape(c["name"])}</h3>'
            f"<p>{escape(topics)}</p>"
            f'<span class="meta">{sum(u["n"] for u in c["units"])} โจทย์ฝึก</span></a>'
        )
    return (
        _head(SITE,
              "เนื้อหาคณิตศาสตร์ ม.2 ทฤษฎี ภาพอธิบายแบบอินเทอร์แอกทีฟ "
              "และโจทย์ระดับปานกลางถึงยากพร้อมเฉลยละเอียด", 0)
        + _nav(0, "home")
        + '<div class="wrap"><main>'
        + "<h1>คณิตศาสตร์ ชั้นมัธยมศึกษาปีที่ 2</h1>"
        + '<p class="lead">ทฤษฎีอธิบายทีละขั้น ภาพประกอบที่ขยับและลากได้ '
          "ตัวอย่างแสดงวิธีทำเต็มรูปแบบ และแบบฝึกหัดระดับปานกลางถึงยาก "
          "พร้อมโจทย์ประยุกต์ท้ายทุกบท</p>"
        + f'<div class="course-grid">{"".join(cards)}</div>'
        + "</main></div>"
        + _foot(0)
    )
