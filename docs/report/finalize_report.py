# -*- coding: utf-8 -*-
"""Обновление полей (оглавление, номера страниц) и экспорт PDF через Word."""
import os
import sys

import win32com.client

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.join(HERE, "Курсовая_работа.docx")
PDF = os.path.join(HERE, "Курсовая_работа.pdf")

word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    doc = word.Documents.Open(DOCX, ReadOnly=False)
    doc.Fields.Update()
    for toc in doc.TablesOfContents:
        toc.Update()
    doc.Repaginate()
    pages = doc.ComputeStatistics(2)  # wdStatisticPages
    words = doc.ComputeStatistics(0)
    doc.Save()
    doc.ExportAsFixedFormat(PDF, 17)  # wdExportFormatPDF
    print(f"pages={pages} words={words}")
    doc.Close(SaveChanges=0)
finally:
    word.Quit()
print("pdf:", PDF, os.path.getsize(PDF))
