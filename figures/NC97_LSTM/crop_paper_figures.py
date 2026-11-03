# -*- coding: utf-8 -*-
"""LSTM 논문(Hochreiter & Schmidhuber 1997, 저자 배포본 32 쪽)의 그림 1 · 2 · 3 · 4 를 원문 PDF 에서 잘라 png 로 둔다.

이 PDF 는 글자 층이 깨져 있어(Ghostscript 로 다시 만든 파일) 그림 안의 글자를 다시 옮겨 그리면 틀리기 쉽다.
그래서 원문 그림은 잘라 넣고, 노트 캡션에 잘라 넣은 것이라고 밝힌다. 다시 그린 셀 그림은 make_figures.py 의 그림 4 다.
make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers", "NC97_LSTM_Long_Short_Term_Memory.pdf")
doc = pymupdf.open(PDF)
# (쪽 번호(1 부터), 사각형 pt). 쪽 크기는 595 x 842 pt. 사각형은 쪽을 110 dpi 로 띄워 눈으로 잡은 그림 상자다.
crops = {
    "paper_fig1_memory_cell.png": (7, pymupdf.Rect(100, 418, 500, 585)),
    "paper_fig2_network.png": (9, pymupdf.Rect(110, 98, 500, 346)),
    "paper_fig3_4_reber.png": (11, pymupdf.Rect(88, 535, 520, 668)),
}
for name, (pno, r) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=200, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
