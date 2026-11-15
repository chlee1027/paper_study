# -*- coding: utf-8 -*-
"""SimpleNet 원문(arXiv v2)에서 그림 2 · 3 · 4 · 5 · 6 · 7 을 잘라 PNG 로 둔다. PyMuPDF 가 필요하다.

자르는 칸은 쪽의 그림 상자와 캡션 상자를 합친 것이다(pt, 쪽 크기 612 x 792).
"""
import os

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "..", "papers",
                   "CVPR23_SimpleNet_A_Simple_Network_for_Image_Anomaly_Detection_and_Localization.pdf")
CROPS = [  # (이름, 쪽 번호(1부터), x0, y0, x1, y1)
    ("paper_fig2_fps.png", 1, 305, 222, 549, 432),
    ("paper_fig3_overview.png", 3, 46, 68, 549, 276),
    ("paper_fig4_feature_std.png", 4, 46, 68, 290, 253),
    ("paper_fig5_sigma.png", 7, 46, 68, 549, 287),
    ("paper_fig6_patch_size.png", 7, 46, 300, 290, 406),
    ("paper_fig7_loss.png", 7, 46, 415, 290, 546),
]

doc = pymupdf.open(PDF)
for name, page, x0, y0, x1, y1 in CROPS:
    pix = doc[page - 1].get_pixmap(dpi=220, clip=pymupdf.Rect(x0, y0, x1, y1))
    pix.save(os.path.join(HERE, name))
    print(name, pix.width, "x", pix.height)
