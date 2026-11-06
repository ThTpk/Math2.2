# -*- coding: utf-8 -*-
"""build — generate the whole static site into the repository root.

    python tools/build.py

Writes:
    index.html
    <course>/index.html
    <course>/<lesson>.html
Everything else (assets/, .nojekyll) is committed by hand and left alone.
"""
from __future__ import annotations

import importlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# The build summary contains Thai text; force UTF-8 so it prints on a
# Windows console whose default code page is cp874.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover - very old Python
    pass

import layout  # noqa: E402

# --------------------------------------------------------------- course map ---
COURSES = [
    dict(
        slug="c22122",
        name="คณิตศาสตร์ 4",
        short="เลขยกกำลัง · พื้นที่ผิวและปริมาตร · เส้นขนาน · "
               "การแปลงทางเรขาคณิต · ความเท่ากันทุกประการ · การให้เหตุผลทางเรขาคณิต",
        modules=["c22122_u1", "c22122_u2", "c22122_u3",
                 "c22122_u4", "c22122_u5", "c22122_u6"],
        subs=["นิยาม สมบัติ สัญกรณ์วิทยาศาสตร์ และสมการเลขยกกำลัง",
              "ปริซึม ทรงกระบอก รูปทรงประกอบ และรูปทรงที่ถูกเจาะ",
              "คู่มุมจากเส้นตัด มุมในรูปสามเหลี่ยม และรูปหลายเหลี่ยม",
              "เลื่อนขนาน สะท้อน หมุน สมมาตร และเทเซเลชัน",
              "เงื่อนไข ด.ด.ด. · ด.ม.ด. · ม.ด.ม. · ม.ม.ด. · ฉ.ด.ด.",
              "การพิสูจน์สองคอลัมน์ สมบัติรูปสี่เหลี่ยม และทฤษฎีบทเส้นกึ่งกลาง"],
    ),
    dict(
        slug="c22292",
        name="คณิตศาสตร์พัฒนาศักยภาพ 4",
        short="สัจพจน์ยุคลิดและการพิสูจน์ · ทฤษฎีบทเมเนลอสและเซวา · "
              "อัตราส่วนพื้นที่ · ทฤษฎีวงกลม · เซนทรอยด์และวงกลมแนบใน",
        modules=["c22292_u1", "c22292_u2"],
        subs=["สัจพจน์ การพิสูจน์ เมเนลอส เซวา และอัตราส่วนของพื้นที่",
              "คอร์ด ส่วนโค้ง มุมในส่วนโค้ง เส้นสัมผัส และจุดสำคัญของสามเหลี่ยม"],
    ),
    dict(
        slug="c22294",
        name="เทคโนโลยีเพื่อการศึกษาทางคณิตศาสตร์",
        short="การสร้างด้วยวงเวียนและสันตรง · รูปเรขาคณิตและพื้นที่ · "
              "วงกลมแนบในและล้อมรอบ · การแปลงและเทเซเลชัน · สถิติ · กราฟฟังก์ชัน",
        modules=["c22294_u1", "c22294_u2", "c22294_u3",
                 "c22294_u4", "c22294_u5", "c22294_u6"],
        subs=["การสร้างพื้นฐานห้าแบบ และความต่างระหว่างการสร้างกับการวาด",
              "สี่เหลี่ยมด้านขนาน พื้นที่จากการตัด–เลื่อน และการสำรวจวงกลม",
              "วงกลมแนบใน วงกลมล้อมรอบ และการสำรวจอย่างเป็นระบบ",
              "สะท้อน หมุน เลื่อน การประกอบการแปลง และเทเซเลชัน",
              "ค่ากลาง การกระจาย แผนภาพ และการอ่านกราฟอย่างมีวิจารณญาณ",
              "กราฟเส้นตรงและพาราโบลา ตัวเลื่อน และการแก้สมการด้วยกราฟ"],
    ),
]


def write(rel_path: str, html: str) -> int:
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    return len(html)


def main() -> int:
    total_bytes = 0
    n_pages = 0
    built = []

    for c in COURSES:
        units = []
        for mod_name in c["modules"]:
            mod = importlib.import_module(f"content.{mod_name}")
            units.append(mod.UNIT)

        # prev / next links within the course
        for i, u in enumerate(units):
            if i > 0:
                u["prev"] = (f'{units[i - 1]["slug"]}.html', units[i - 1]["title"])
            if i < len(units) - 1:
                u["next"] = (f'{units[i + 1]["slug"]}.html', units[i + 1]["title"])

        for u in units:
            html = layout.unit_page(u)
            total_bytes += write(f'{c["slug"]}/{u["slug"]}.html', html)
            n_pages += 1
            built.append((f'{c["slug"]}/{u["slug"]}.html', len(u["exercises"])))

        c["units"] = [
            dict(href=f'{u["slug"]}.html', title=u["title"], sub=sub,
                 n=len(u["exercises"]))
            for u, sub in zip(units, c["subs"])
        ]
        total_bytes += write(f'{c["slug"]}/index.html', layout.course_index(c))
        n_pages += 1

    total_bytes += write("index.html", layout.home(COURSES))
    n_pages += 1

    print(f"built {n_pages} pages · {total_bytes / 1024:.0f} KB")
    for c in COURSES:
        tot = sum(u["n"] for u in c["units"])
        print(f'  {c["slug"]:8s} {len(c["units"])} lessons · {tot:3d} exercises'
              f'  — {c["name"]}')
    print(f'  TOTAL    {sum(len(c["units"]) for c in COURSES)} lessons · '
          f'{sum(sum(u["n"] for u in c["units"]) for c in COURSES)} exercises')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
