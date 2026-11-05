# -*- coding: utf-8 -*-
"""DDIM 논문(arXiv v4)의 그림 3 · 5 · 6 을 원문 PDF 에서 잘라 png 로 둔다.

세 그림은 표본 이미지(래스터)라 다시 그리지 않는다. 표와 그림 4 의 수는 make_figures.py 가 옮겨 그린다.
make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers", "ICLR21_DDIM_Denoising_Diffusion_Implicit_Models.pdf")
doc = pymupdf.open(PDF)
# (쪽 번호(1 부터), 사각형 pt). 쪽 그림을 110 dpi 로 띄워 눈으로 잡은 상자에 여백을 붙였다.
crops = {
    "paper_fig3_samples.png": (7, pymupdf.Rect(108, 222, 504, 305)),
    "paper_fig5_consistency.png": (8, pymupdf.Rect(108, 190, 504, 416)),
    "paper_fig6_interpolation.png": (8, pymupdf.Rect(104, 512, 508, 678)),
}
for name, (pno, r) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=170, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
