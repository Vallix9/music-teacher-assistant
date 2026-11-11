# -*- coding: utf-8 -*-
"""Build the coursework .docx from the user's template and the report content."""
import os
import sys

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import content_part1  # noqa: E402
import content_part2  # noqa: E402

TEMPLATE = r"F:\Новая папка (2)\kursovaya_rabota_2.docx"
OUTPUT = os.path.join(HERE, "Курсовая_работа.docx")

FONT = "Times New Roman"
BLACK = RGBColor(0, 0, 0)


# ---------------------------------------------------------------------------
# low-level helpers
# ---------------------------------------------------------------------------
def set_run(run, size=14, bold=False, italic=False, name=FONT):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = BLACK
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), name)


def para(text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=1.5, size=14,
         bold=False, italic=False, before=0, after=0, line=1.5,
         keep=False, page_break=False, style="Normal", left=0):
    p = doc.add_paragraph(style=style)
    pf = p.paragraph_format
    pf.alignment = align
    pf.first_line_indent = Cm(indent)
    pf.left_indent = Cm(left)
    pf.line_spacing = line
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.keep_with_next = keep
    pf.page_break_before = page_break
    if text:
        run = p.add_run(text)
        set_run(run, size=size, bold=bold, italic=italic)
    return p


def heading1(text):
    p = doc.add_paragraph(style="Heading 1")
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0)
    pf.line_spacing = 1.5
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.keep_with_next = True
    pf.page_break_before = True
    run = p.add_run(text)
    set_run(run, size=14, bold=True)
    return p


def heading2(text):
    p = doc.add_paragraph(style="Heading 2")
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0)
    pf.line_spacing = 1.5
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.keep_with_next = True
    run = p.add_run(text)
    set_run(run, size=14, bold=True)
    return p


def setup_document_language(document):
    """Русский язык по умолчанию и автоматические переносы (как принято для работ)."""
    # язык в docDefaults
    styles = document.styles.element
    rPrDefault = styles.find(qn("w:docDefaults")).find(qn("w:rPrDefault"))
    rPr = rPrDefault.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        rPrDefault.append(rPr)
    lang = rPr.find(qn("w:lang"))
    if lang is None:
        lang = OxmlElement("w:lang")
        rPr.append(lang)
    lang.set(qn("w:val"), "ru-RU")
    lang.set(qn("w:eastAsia"), "ru-RU")
    lang.set(qn("w:bidi"), "ar-SA")

    # параметры переносов
    settings = document.settings.element
    order = [
        "w:defaultTabStop", "w:autoHyphenation", "w:consecutiveHyphenLimit",
        "w:hyphenationZone", "w:doNotHyphenateCaps", "w:hdrShapeDefaults",
        "w:footnotePr", "w:endnotePr", "w:compat",
    ]
    values = {
        "w:autoHyphenation": None,
        "w:consecutiveHyphenLimit": "2",
        "w:hyphenationZone": "360",
        "w:doNotHyphenateCaps": None,
    }
    for tag, val in values.items():
        el = settings.find(qn(tag))
        if el is not None:
            settings.remove(el)
        el = OxmlElement(tag)
        if val is not None:
            el.set(qn("w:val"), val)
        # вставляем в соответствии с порядком элементов схемы
        pos = order.index(tag)
        anchor = None
        for later in order[pos + 1:]:
            anchor = settings.find(qn(later))
            if anchor is not None:
                break
        if anchor is not None:
            anchor.addprevious(el)
        else:
            settings.append(el)


def shade_paragraph(p, fill):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def table_borders(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    layout = tblPr.find(qn("w:tblLayout"))
    if layout is not None:
        layout.addprevious(borders)
    else:
        tblPr.append(borders)

    margins = OxmlElement("w:tblCellMar")
    for edge, width in (("top", 30), ("left", 80), ("bottom", 30), ("right", 80)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(width))
        el.set(qn("w:type"), "dxa")
        margins.append(el)
    if layout is not None:
        layout.addnext(margins)
    else:
        tblPr.append(margins)


def add_table(spec):
    header = spec["header"]
    rows = spec["rows"]
    widths = spec["widths"]
    font = spec.get("font", 11)

    para(spec["caption"], align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, size=12,
         before=6, after=3, line=1.0, keep=True)

    table = doc.add_table(rows=1 + len(rows), cols=len(header))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.allow_autofit = False
    table_borders(table)

    tblW = table._tbl.tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        table._tbl.tblPr.append(tblW)
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(int(round(sum(widths) * 567))))

    for i, width in enumerate(widths):
        table.columns[i].width = Cm(width)

    for i, text in enumerate(header):
        cell = table.rows[0].cells[i]
        cell.width = Cm(widths[i])
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        pf = p.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.first_line_indent = Cm(0)
        pf.line_spacing = 1.0
        pf.space_before = Pt(1)
        pf.space_after = Pt(1)
        pf.keep_with_next = True
        run = p.add_run(text)
        set_run(run, size=font, bold=True)
        shade_cell(cell, "EDEDED")

    for r, row in enumerate(rows, start=1):
        for i, text in enumerate(row):
            cell = table.rows[r].cells[i]
            cell.width = Cm(widths[i])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            pf = p.paragraph_format
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.first_line_indent = Cm(0)
            pf.line_spacing = 1.0
            pf.space_before = Pt(1)
            pf.space_after = Pt(1)
            pf.keep_with_next = r < len(rows)
            run = p.add_run(text)
            set_run(run, size=font)

    # строки не разрываются между страницами, шапка повторяется
    for idx, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        cantSplit = OxmlElement("w:cantSplit")
        trPr.append(cantSplit)
        if idx == 0:
            tblHeader = OxmlElement("w:tblHeader")
            tblHeader.set(qn("w:val"), "true")
            trPr.append(tblHeader)

    spacer = doc.add_paragraph()
    pf = spacer.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.0
    pf.first_line_indent = Cm(0)
    run = spacer.add_run("")
    set_run(run, size=4)


def add_image(path, caption, width_cm):
    full = os.path.join(HERE, path)
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0)
    pf.space_before = Pt(6)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.0
    pf.keep_with_next = True
    p.add_run().add_picture(full, width=Cm(width_cm))

    para(caption, align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, size=12,
         before=0, after=8, line=1.0)


def add_code(code, caption):
    para(caption, align=WD_ALIGN_PARAGRAPH.LEFT, indent=0, size=12,
         before=6, after=3, line=1.0, keep=True)

    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0.4)
    pf.line_spacing = 1.0
    pf.space_before = Pt(2)
    pf.space_after = Pt(8)
    shade_paragraph(p, "F3F3F3")

    run = p.add_run()
    set_run(run, size=8.5, name="Courier New")
    for i, line in enumerate(code.split("\n")):
        if i:
            run.add_break()
        run.add_text(line)


def add_toc():
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.first_line_indent = Cm(0)
    pf.line_spacing = 1.5
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)

    run = p.add_run()
    set_run(run, size=14)
    r = run._r

    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = ' TOC \\o "1-3" \\h \\z \\u '
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "Оглавление обновляется при открытии документа (F9)."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, separate, text, end):
        r.append(el)


def add_page_field(paragraph):
    run = paragraph.add_run()
    set_run(run, size=12)
    r = run._r
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE \\* MERGEFORMAT "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "2"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, separate, text, end):
        r.append(el)


def set_page_start(section, start):
    sectPr = section._sectPr
    pgNumType = sectPr.find(qn("w:pgNumType"))
    if pgNumType is None:
        pgNumType = OxmlElement("w:pgNumType")
        sectPr.append(pgNumType)
    pgNumType.set(qn("w:start"), str(start))
    for el in sectPr.findall(qn("w:titlePg")):
        sectPr.remove(el)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
doc = Document(TEMPLATE)

# remove all body content but keep the final section properties
body = doc.element.body
for child in list(body):
    if child.tag == qn("w:sectPr"):
        continue
    body.remove(child)

core = doc.core_properties
core.title = "Система-помощник учителя музыки в школе"
core.subject = "Курсовая работа"
core.author = "Студент"
core.comments = ""

setup_document_language(doc)

# --- единственная секция: номер страницы в нижнем колонтитуле ---
section = doc.sections[0]
footer = section.footer
footer.is_linked_to_previous = False
ftr_element = footer._element
for child in list(ftr_element):
    ftr_element.remove(child)
footer_p = footer.add_paragraph()
footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
footer_p.paragraph_format.first_line_indent = Cm(0)
footer_p.paragraph_format.space_before = Pt(0)
footer_p.paragraph_format.space_after = Pt(0)
add_page_field(footer_p)
set_page_start(section, 1)

# --- table of contents ---
para("СОДЕРЖАНИЕ", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, size=14,
     bold=True, before=0, after=6, line=1.5)
add_toc()

# --- content ---
SRC_NUM = 0
for blocks in (content_part1.BLOCKS, content_part2.BLOCKS):
    for block in blocks:
        kind = block[0]
        if kind == "h1":
            heading1(block[1])
        elif kind == "h2":
            heading2(block[1])
        elif kind == "p":
            para(block[1])
        elif kind == "center":
            para(block[1], align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, size=14,
                 bold=True, before=0, after=6, line=1.5)
        elif kind == "li":
            for item in block[1]:
                para("– " + item)
        elif kind == "img":
            add_image(block[1], block[2], block[3])
        elif kind == "table":
            add_table(block[1])
        elif kind == "code":
            add_code(block[1], block[2])
        elif kind == "group":
            para(block[1], align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, size=14,
                 bold=True, italic=True, before=12, after=6, line=1.5)
        elif kind == "src":
            SRC_NUM += 1
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.left_indent = Cm(2.4)
            pf.first_line_indent = Cm(-0.65)
            pf.line_spacing = 1.5
            pf.space_before = Pt(0)
            pf.space_after = Pt(0)
            run = p.add_run(f"{SRC_NUM}. {block[1]}")
            set_run(run, size=14)
        else:
            raise ValueError(f"unknown block: {kind}")

doc.save(OUTPUT)
print("saved", OUTPUT)
