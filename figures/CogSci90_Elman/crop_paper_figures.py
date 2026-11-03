# -*- coding: utf-8 -*-
"""Elman(1990) 원문의 그림 3 · 4 · 5 · 6 · 7 · 8 · 9 를 스캔 PDF 에서 잘라 회색조 png 로 둔다.

원문은 쪽마다 300 dpi 스캔 이미지 한 장이라 그림을 따로 꺼낼 수 없다. 쪽을 150 dpi 로 그려 그림 자리만 자른다.
사각형은 300 dpi 로 그린 쪽에서 축 상자와 캡션 자리를 픽셀로 찾은 뒤 pt(1/72 인치)로 옮긴 것이다.
make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers", "CogSci90_Elman_Finding_Structure_in_Time.pdf")
doc = pymupdf.open(PDF)
# (쪽 번호(PDF 1 부터, 원문 쪽은 +178), 사각형 pt)
crops = {
    "paper_fig3_xor_error.png": (8, pymupdf.Rect(62, 82, 376, 324)),
    "paper_fig4_letter_error.png": (11, pymupdf.Rect(66, 78, 380, 390)),
    "paper_fig5_bit_error.png": (12, pymupdf.Rect(66, 68, 380, 584)),
    "paper_fig6_word_error.png": (16, pymupdf.Rect(60, 70, 380, 390)),
    "paper_fig7_cluster_tree.png": (22, pymupdf.Rect(56, 52, 380, 452)),
    "paper_fig8_zog_tree.png": (24, pymupdf.Rect(60, 58, 380, 474)),
    "paper_fig9_token_trees.png": (28, pymupdf.Rect(40, 40, 404, 626)),
}
for name, (pno, r) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=150, clip=r, colorspace=pymupdf.csGRAY)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
