# -*- coding: utf-8 -*-
"""Transformer 논문(NIPS 2017 학회판)의 그림 1 · 2 를 원문 PDF 에서 잘라 png 로 둔다.

두 그림은 PDF 안에 래스터 이미지로 들어 있다(3 쪽에 하나, 4 쪽에 둘). 사각형은 PyMuPDF 의
get_image_info 로 잰 이미지 상자에 여백 몇 pt 를 붙인 것이다. 표 1 · 2 · 3 은 글자로 들어 있어
make_figures.py 가 수를 옮겨 그린다. make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers", "NIPS17_Transformer_Attention_Is_All_You_Need.pdf")
doc = pymupdf.open(PDF)
# (쪽 번호(1 부터), 사각형 pt)
# 3 쪽 이미지 상자 x 196.6 ~ 415.4, y 72.0 ~ 394.4 / 4 쪽 이미지 둘 x 175.0 ~ 239.0 · 346.8 ~ 467.0, y 82.7 ~ 267.3
crops = {
    "paper_fig1_architecture.png": (3, pymupdf.Rect(190, 66, 422, 400)),
    "paper_fig2_attention.png": (4, pymupdf.Rect(140, 66, 476, 272)),
}
for name, (pno, r) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=200, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
