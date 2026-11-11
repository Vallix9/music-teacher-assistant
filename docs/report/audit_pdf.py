# -*- coding: utf-8 -*-
"""Текстовый аудит PDF: пустые страницы, переполнение, оглавление, колонтитулы."""
import os
import re
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "Курсовая_работа.pdf")
OUT = os.path.join(os.environ["TEMP"], "opencode", "report_audit.txt")

doc = pymupdf.open(PDF)
W, H = doc[0].rect.width, doc[0].rect.height
# поля: левое 3 см, правое 1 см, верх/низ 2 см
CM = 72 / 2.54
LEFT, RIGHT = 3 * CM, W - 1 * CM
TOP, BOTTOM = 2 * CM, H - 2 * CM

lines = [f"pages={doc.page_count} size={W:.0f}x{H:.0f} text_area x=[{LEFT:.1f},{RIGHT:.1f}] y=[{TOP:.1f},{BOTTOM:.1f}]"]

blank = []
overflow = []
no_footer = []
for i, page in enumerate(doc, start=1):
    text = page.get_text("text").strip()
    words = page.get_text("words")
    images = page.get_images(full=True)
    footer_words = [w for w in words if w[3] > BOTTOM]
    max_x = max((w[2] for w in words), default=0)
    min_x = min((w[0] for w in words), default=0)
    max_y = max((w[3] for w in words), default=0)
    if not text and not images:
        blank.append(i)
    if max_x > RIGHT + 6:
        overflow.append((i, round(max_x, 1)))
    if not footer_words:
        no_footer.append(i)
    first = text.split("\n")[0][:70] if text else "(нет текста)"
    last = text.split("\n")[-1][:70] if text else ""
    lines.append(
        f"p{i:02d} imgs={len(images)} words={len(words)} x=[{min_x:.0f},{max_x:.0f}] y_max={max_y:.0f} "
        f"footer={[w[4] for w in footer_words][:3]} | {first!r} ... {last!r}"
    )

lines.append("")
lines.append(f"BLANK PAGES: {blank}")
lines.append(f"OVERFLOW PAGES: {overflow}")
lines.append(f"NO FOOTER: {no_footer}")

# оглавление: страницы 2-4
lines.append("\n=== TOC TEXT ===")
for i in range(1, min(4, doc.page_count)):
    lines.append(f"--- page {i + 1} ---")
    lines.append(doc[i].get_text("text").strip())

# ищем ссылки оглавления (текст + номер)
lines.append("\n=== HEADINGS DETECTED (font >= 13.5, bold) ===")
for i, page in enumerate(doc, start=1):
    d = page.get_text("dict")
    for block in d["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            if all(s["size"] >= 13.5 and ("Bold" in s["font"] or s["flags"] & 16) for s in spans):
                txt = "".join(s["text"] for s in spans).strip()
                if len(txt) > 3:
                    lines.append(f"p{i:02d} {txt[:95]!r}")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("\n".join(lines[:6]))
print("...")
print(f"BLANK: {blank}")
print(f"OVERFLOW: {overflow}")
print(f"NO FOOTER: {no_footer}")
print("audit:", OUT)
