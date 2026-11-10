# -*- coding: utf-8 -*-
"""RD 원문(CVF 게재판)에서 그림 2 · 3 · 4 · 5 · 6 을 잘라 PNG 로 둔다. PyMuPDF 가 필요하다.

자르는 칸은 쪽의 그림 상자와 캡션 상자를 합친 것이다(pt, 쪽 크기 612 x 792).
"""
import os

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "..", "papers",
                   "CVPR22_RD_Anomaly_Detection_via_Reverse_Distillation_from_One_Class_Embedding.pdf")
CROPS = [  # (이름, 쪽 번호(1부터), x0, y0, x1, y1)
    ("paper_fig2_kd_vs_rd.png", 2, 46, 68, 290, 212),
    ("paper_fig3_overview.png", 4, 46, 68, 549, 406),
    ("paper_fig4_ocbe.png", 5, 305, 68, 549, 280),
    ("paper_fig5_histogram.png", 7, 46, 322, 290, 486),
    ("paper_fig6_large_defects.png", 8, 46, 68, 290, 262),
]

doc = pymupdf.open(PDF)
for name, page, x0, y0, x1, y1 in CROPS:
    pix = doc[page - 1].get_pixmap(dpi=220, clip=pymupdf.Rect(x0, y0, x1, y1))
    pix.save(os.path.join(HERE, name))
    print(name, pix.width, "x", pix.height)
