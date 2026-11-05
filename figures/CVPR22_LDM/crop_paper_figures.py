# -*- coding: utf-8 -*-
"""Latent Diffusion 논문(arXiv v2)의 그림 1 · 2 · 3 · 6 · 7 · 17 을 원문 PDF 에서 잘라 png 로 둔다.

그림 6 · 7 · 17 은 PDF 안에 래스터로 들어 있어(562x301, 404x301 픽셀 등) 벡터 좌표가 없다. 값은 눈금 선 픽셀로 축을 맞춰
색으로 곡선을 뽑아 읽었고 make_figures.py 의 상수에 있다. make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers",
                   "CVPR22_LDM_High_Resolution_Image_Synthesis_with_Latent_Diffusion_Models.pdf")
doc = pymupdf.open(PDF)
crops = {
    "paper_fig1_recon.png": (1, pymupdf.Rect(306, 176, 552, 322), 130),
    "paper_fig2_rate_distortion.png": (2, pymupdf.Rect(330, 70, 524, 221), 200),
    "paper_fig3_architecture.png": (4, pymupdf.Rect(308, 70, 550, 184), 220),
    "paper_fig6_training.png": (6, pymupdf.Rect(48, 303, 288, 380), 300),
    "paper_fig7_throughput.png": (6, pymupdf.Rect(48, 477, 288, 554), 300),
    "paper_fig17_v100days.png": (22, pymupdf.Rect(48, 469, 548, 629), 150),
}
for name, (pno, r, dpi) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=dpi, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
