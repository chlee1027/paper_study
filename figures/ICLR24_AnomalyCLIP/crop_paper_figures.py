# -*- coding: utf-8 -*-
"""AnomalyCLIP 원문(arXiv v8, 31 쪽)에서 그림 1 · 2 · 3 · 4 를 잘라 PNG 로 둔다. PyMuPDF 가 필요하다.

자르는 칸은 쪽의 그림 상자와 캡션 상자를 합친 것이다(pt, 쪽 크기 612 x 792).
"""
import os

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "..", "papers",
                   "ICLR24_AnomalyCLIP_Object_Agnostic_Prompt_Learning_for_Zero_Shot_Anomaly_Detection.pdf")
CROPS = [  # (이름, 쪽 번호(1부터), x0, y0, x1, y1)
    ("paper_fig1_comparison.png", 2, 106, 76, 506, 342),
    ("paper_fig2_overview.png", 4, 106, 78, 506, 392),
    ("paper_fig3_dpam.png", 6, 340, 172, 506, 309),
    ("paper_fig4_segmentation.png", 8, 106, 570, 330, 709),
]

doc = pymupdf.open(PDF)
for name, page, x0, y0, x1, y1 in CROPS:
    pix = doc[page - 1].get_pixmap(dpi=220, clip=pymupdf.Rect(x0, y0, x1, y1))
    pix.save(os.path.join(HERE, name))
    print(name, pix.width, "x", pix.height)
