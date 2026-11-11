# -*- coding: utf-8 -*-
"""Проверка вёрстки: целостность таблиц, привязка подписей к рисункам, оглавление."""
import importlib.util
import os
import re
import sys

import pymupdf

HERE = r"D:\programmirovanie\PPnarek\docs\report"
doc = pymupdf.open(os.path.join(HERE, "Курсовая_работа.pdf"))

pages = [p.get_text("text") for p in doc]
flat = [re.sub(r"\s+", " ", t) for t in pages]

# --- таблицы: подпись и последняя строка должны быть на одной странице ---
print("=== ТАБЛИЦЫ ===")
for name in ("content_part1", "content_part2"):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for block in mod.BLOCKS:
        if block[0] != "table":
            continue
        spec_t = block[1]
        caption = re.sub(r"\s+", " ", spec_t["caption"])
        last_cell = re.sub(r"\s+", " ", spec_t["rows"][-1][0])
        cap_pages = [i + 1 for i, t in enumerate(flat) if caption[:40] in t]
        row_pages = [i + 1 for i, t in enumerate(flat) if last_cell[:35] in t]
        ok = bool(cap_pages) and bool(row_pages) and cap_pages[0] in row_pages
        print(f"{'OK ' if ok else 'BAD'} {caption[:45]!r} caption={cap_pages} last_row={row_pages}")

# --- рисунки: подпись на той же странице, что и изображение ---
print("\n=== РИСУНКИ ===")
for i, page in enumerate(doc, start=1):
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 1:
            continue
        bbox = block["bbox"]
        below = [
            line
            for b in page.get_text("dict")["blocks"] if b["type"] == 0
            for line in b["lines"]
            if line["bbox"][1] > bbox[3] - 2 and line["bbox"][1] < bbox[3] + 40
        ]
        txt = " ".join(
            "".join(s["text"] for s in line["spans"]).strip() for line in below
        ).strip()
        print(f"p{i:02d} img y=[{bbox[1]:.0f},{bbox[3]:.0f}] h={bbox[3] - bbox[1]:.0f}pt "
              f"caption={txt[:60]!r}")

# --- оглавление: строка TOC и реальная страница заголовка ---
print("\n=== ОГЛАВЛЕНИЕ ===")
toc_text = "\n".join(pages[1:2])
entries = re.findall(r"([^\n]+?)\s*\.{3,}\s*(\d+)", toc_text)
for title, num in entries:
    title = title.strip()
    key = title[:35]
    real = [
        i + 1
        for i, t in enumerate(flat)
        if i > 0 and key in t and not t.startswith("2 ") and not t.startswith("3 ")
    ]
    print(f"{'OK ' if real and int(num) in real[:3] else '?? '} {title[:45]!r} toc={num} pages={real[:4]}")
