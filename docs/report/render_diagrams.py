# -*- coding: utf-8 -*-
"""Рендер Mermaid-схем в PNG локально через Edge + mermaid.js.

Печатает натуральный размер схемы и расчётный кегль подписей при вставке
в документ, чтобы контролировать читаемость рисунков.
"""
import glob
import os

import requests
from playwright.sync_api import sync_playwright

SRC = os.path.join("docs", "report", "diagrams")
OUT = os.path.join("docs", "report", "img")
CACHE = os.path.join(os.environ["TEMP"], "opencode", "mermaid.min.js")
os.makedirs(os.path.dirname(CACHE), exist_ok=True)

if not os.path.exists(CACHE):
    r = requests.get("https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js", timeout=120)
    r.raise_for_status()
    open(CACHE, "wb").write(r.content)
js = open(CACHE, encoding="utf-8").read()

FONT_PX = 16
HTML = """<!doctype html><html><head><meta charset="utf-8">
<style>
  body { margin: 0; background: #ffffff; }
  #c { display: inline-block; padding: 24px; background: #ffffff; }
  #c svg { max-width: none !important; height: auto !important; }
</style></head><body><div id="c"></div></body></html>"""

files = sorted(glob.glob(os.path.join(SRC, "*.mmd")))
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 2400, "height": 1600}, device_scale_factor=2)
    page = ctx.new_page()
    page.set_content(HTML)
    page.add_script_tag(content=js)
    page.evaluate(
        """(fontPx) => {
            mermaid.initialize({
                startOnLoad: false,
                securityLevel: 'loose',
                theme: 'neutral',
                themeVariables: {
                    fontFamily: 'Times New Roman, serif',
                    fontSize: fontPx + 'px',
                    primaryColor: '#f4f1fb',
                    primaryBorderColor: '#5b4b8a',
                    primaryTextColor: '#1b1b1b',
                    lineColor: '#4a4a4a',
                    secondaryColor: '#eef3fb',
                    tertiaryColor: '#faf7ef'
                },
                flowchart: { curve: 'basis', nodeSpacing: 30, rankSpacing: 45 },
                sequence: { actorFontSize: fontPx, messageFontSize: fontPx, noteFontSize: fontPx },
                er: { entityPadding: 14, minEntityWidth: 90, fontSize: fontPx }
            });
        }""",
        FONT_PX,
    )

    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        text = open(path, encoding="utf-8").read()
        page.evaluate(
            """async (src) => {
                const box = document.getElementById('c');
                box.innerHTML = '';
                const { svg } = await mermaid.render('d_' + Date.now(), src);
                box.innerHTML = svg;
                const el = box.querySelector('svg');
                const vb = el.viewBox.baseVal;
                el.setAttribute('width', vb.width);
                el.setAttribute('height', vb.height);
                el.style.maxWidth = 'none';
                await document.fonts.ready;
            }""",
            text,
        )
        page.wait_for_timeout(400)
        target = os.path.join(OUT, f"diagram-{name}.png")
        page.locator("#c").screenshot(path=target)
        box = page.locator("#c").bounding_box()
        natural = box["width"] - 48
        print(f"saved {target} natural={natural:.0f}px h={box['height'] - 48:.0f} "
              f"font={FONT_PX}px -> text at 15cm = {FONT_PX / natural * 425.2:.1f}pt")

    browser.close()
