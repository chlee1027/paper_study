# -*- coding: utf-8 -*-
"""WinCLIP 원문(CVF 공개판, 11 쪽)에서 그림 2 · 3 · 4 · 5 를 잘라 PNG 로 둔다. PyMuPDF 가 필요하다.

자르는 칸은 쪽의 그림 상자와 캡션 상자를 합친 것이다(pt, 쪽 크기 612 x 792).
"""
import os

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "..", "papers",
                   "CVPR23_WinCLIP_Zero_Few_Shot_Anomaly_Classification_and_Segmentation.pdf")
CROPS = [  # (이름, 쪽 번호(1부터), x0, y0, x1, y1)
    ("paper_fig2_motivation.png", 2, 48, 68, 548, 204),
    ("paper_fig3_window_features.png", 4, 306, 68, 549, 253),
    ("paper_fig4_workflow.png", 5, 48, 68, 548, 359),
    ("paper_fig5_qualitative.png", 8, 50, 68, 545, 212),
]

doc = pymupdf.open(PDF)
for name, page, x0, y0, x1, y1 in CROPS:
    pix = doc[page - 1].get_pixmap(dpi=220, clip=pymupdf.Rect(x0, y0, x1, y1))
    pix.save(os.path.join(HERE, name))
    print(name, pix.width, "x", pix.height)
