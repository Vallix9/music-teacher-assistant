# -*- coding: utf-8 -*-
"""Рендер страниц PDF в PNG для визуальной проверки вёрстки."""
import os
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "Курсовая_работа.pdf")
OUT = os.path.join(os.environ["TEMP"], "opencode", "report_pages")
os.makedirs(OUT, exist_ok=True)

doc = pymupdf.open(PDF)
print("pages:", doc.page_count)
zoom = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
for i, page in enumerate(doc, start=1):
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    pix.save(os.path.join(OUT, f"p{i:02d}.png"))
print("rendered to", OUT)
