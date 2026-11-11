# -*- coding: utf-8 -*-
"""Схемы ER-модели: ручная раскладка в SVG и рендер в PNG через Edge.

Mermaid/dagre раскладывает 10 сущностей в широкую строку, из-за чего подписи
при вставке в документ становятся нечитаемыми (4 pt). Поэтому схема разбита
на два фрагмента с фиксированными координатами: масштаб известен заранее,
кегль подписей при вставке на 16,5 см составляет около 8 pt.
"""
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "img")

FONT = "Times New Roman, serif"
HEADER_H = 34
LINE_H = 23
PAD_B = 10
HEADER_FILL = "#ece7f7"
BODY_FILL = "#fdfcff"
STROKE = "#5b4b8a"
TEXT = "#1b1b1b"
KEY = "#6b5aa0"


def box_height(fields):
    return HEADER_H + LINE_H * len(fields) + PAD_B


def entity(name, x, y, w, fields):
    h = box_height(fields)
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" '
        f'fill="{BODY_FILL}" stroke="{STROKE}" stroke-width="1.4"/>',
        f'<path d="M{x + 5},{y} h{w - 10} a5,5 0 0 1 5,5 v{HEADER_H - 5} h{-w} '
        f'v{-(HEADER_H - 5)} a5,5 0 0 1 5,-5 z" fill="{HEADER_FILL}" '
        f'stroke="{STROKE}" stroke-width="1.4"/>',
        f'<text x="{x + w / 2}" y="{y + 22}" font-family="{FONT}" font-size="17" '
        f'font-weight="bold" fill="{TEXT}" text-anchor="middle">{name}</text>',
    ]
    for i, (field, key) in enumerate(fields):
        fy = y + HEADER_H + 17 + i * LINE_H
        out.append(
            f'<text x="{x + 12}" y="{fy}" font-family="{FONT}" font-size="16" '
            f'fill="{TEXT}">{field}</text>'
        )
        if key:
            out.append(
                f'<text x="{x + w - 10}" y="{fy}" font-family="{FONT}" font-size="14" '
                f'font-weight="bold" fill="{KEY}" text-anchor="end">{key}</text>'
            )
    return "\n".join(out), h


def edge(points, one=None, many=None):
    d = " ".join(f"{px},{py}" for px, py in points)
    out = [
        f'<polyline points="{d}" fill="none" stroke="#4a4a4a" stroke-width="1.3"/>'
    ]
    if one:
        out.append(_label("1", *one))
    if many:
        out.append(_label("M", *many))
    return "\n".join(out)


def _label(text, x, y):
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="15" fill="#333" '
        f'stroke="#ffffff" stroke-width="3" paint-order="stroke" '
        f'text-anchor="middle">{text}</text>'
    )


def svg(width, height, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>{body}</svg>'
    )


# ---------------------------------------------------------------------------
# Фрагмент 1: пользователи, классы, ученики, расписание, посещаемость, оценки
# ---------------------------------------------------------------------------
W1, H1 = 950, 680
parts = []

parts.append(entity("USERS", 15, 20, 215, [
    ("id", "PK"), ("username", ""), ("role", ""),
])[0])
parts.append(entity("SCHOOL_CLASSES", 365, 20, 220, [
    ("id", "PK"), ("name", ""), ("teacher_id", "FK"),
])[0])
parts.append(entity("STUDENTS", 720, 20, 215, [
    ("id", "PK"), ("full_name", ""), ("class_id", "FK"), ("parent_id", "FK"),
])[0])
parts.append(entity("SCHEDULE", 365, 210, 220, [
    ("id", "PK"), ("class_id", "FK"), ("teacher_id", "FK"),
    ("day_of_week", ""), ("lesson_number", ""),
])[0])
parts.append(entity("GRADES", 720, 250, 215, [
    ("id", "PK"), ("student_id", "FK"), ("schedule_id", "FK"), ("value", ""),
])[0])
parts.append(entity("ATTENDANCE", 720, 470, 215, [
    ("id", "PK"), ("student_id", "FK"), ("schedule_id", "FK"), ("status", ""),
])[0])

parts.append(edge([(230, 76), (365, 76)], one=(244, 68), many=(351, 68)))
parts.append(edge([(585, 76), (720, 76)], one=(599, 68), many=(706, 68)))
parts.append(edge([(122, 133), (122, 172), (320, 172), (320, 289), (365, 289)],
                  one=(112, 150), many=(352, 281)))
parts.append(edge([(475, 133), (475, 210)], one=(461, 150), many=(461, 203)))
parts.append(edge([(45, 133), (45, 645), (690, 645), (690, 110), (720, 110)],
                  one=(35, 150), many=(707, 103)))
parts.append(edge([(585, 289), (720, 289)], one=(599, 281), many=(706, 281)))
parts.append(edge([(827, 156), (827, 250)], one=(813, 173), many=(813, 243)))
parts.append(edge([(720, 140), (660, 140), (660, 530), (720, 530)],
                  one=(707, 133), many=(707, 523)))
parts.append(edge([(450, 369), (450, 430), (800, 430), (800, 470)],
                  one=(436, 386), many=(788, 463)))

svg1 = svg(W1, H1, "\n".join(parts))

# ---------------------------------------------------------------------------
# Фрагмент 2: учебные сущности — репертуар, материалы, мероприятия, конспекты
# ---------------------------------------------------------------------------
W2, H2 = 950, 380
parts = []
parts.append(entity("SCHOOL_CLASSES", 365, 20, 220, [
    ("id", "PK"), ("name", ""), ("year", ""),
])[0])
parts.append(entity("REPERTOIRE", 15, 210, 215, [
    ("id", "PK"), ("title", ""), ("class_id", "FK"),
])[0])
parts.append(entity("MATERIALS", 250, 210, 215, [
    ("id", "PK"), ("title", ""), ("class_id", "FK"),
])[0])
parts.append(entity("EVENTS", 485, 210, 215, [
    ("id", "PK"), ("title", ""), ("class_id", "FK"),
])[0])
parts.append(entity("LESSON_PLANS", 720, 210, 215, [
    ("id", "PK"), ("title", ""), ("class_id", "FK"), ("teacher_id", "FK"),
])[0])

parts.append(edge([(475, 133), (475, 165), (122, 165), (122, 210)],
                  one=(461, 150), many=(109, 203)))
parts.append(edge([(475, 133), (475, 178), (357, 178), (357, 210)],
                  one=(461, 150), many=(344, 203)))
parts.append(edge([(475, 133), (475, 191), (592, 191), (592, 210)],
                  one=(461, 150), many=(579, 203)))
parts.append(edge([(475, 133), (475, 198), (827, 198), (827, 210)],
                  one=(461, 150), many=(814, 203)))

svg2 = svg(W2, H2, "\n".join(parts))

HTML = "<!doctype html><html><head><meta charset='utf-8'></head><body></body></html>"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 1000},
                              device_scale_factor=2)
    page = ctx.new_page()
    page.set_content(HTML)
    for name, markup, w, h in (("er-core", svg1, W1, H1),
                               ("er-study", svg2, W2, H2)):
        page.evaluate(
            """(svg) => { document.body.innerHTML = svg;
                          document.body.style.margin = '0'; }""",
            markup,
        )
        page.wait_for_timeout(200)
        target = os.path.join(OUT, f"diagram-{name}.png")
        page.locator("svg").screenshot(path=target)
        print(f"saved {target} {w}x{h} -> text at 16.5cm = {16 / w * 467.6:.1f}pt, "
              f"height = {16.5 * h / w:.1f}cm")
    browser.close()
