# -*- coding: utf-8 -*-
"""EfficientAD 원문(arXiv v3)에서 그림 1 · 2 · 3 · 4 · 5 를 잘라 PNG 로 둔다. PyMuPDF 가 필요하다.

자르는 칸은 쪽의 그림 상자와 캡션 상자를 합친 것이다(pt, 쪽 크기 612 x 792).
"""
import os

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "..", "papers",
                   "WACV24_EfficientAD_Accurate_Visual_Anomaly_Detection_at_Millisecond_Level_Latencies.pdf")
CROPS = [  # (이름, 쪽 번호(1부터), x0, y0, x1, y1)
    ("paper_fig1_latency.png", 1, 305, 214, 549, 418),
    ("paper_fig2_pdn.png", 3, 305, 68, 549, 179),
    ("paper_fig3_receptive.png", 4, 46, 68, 290, 277),
    ("paper_fig4_hard_mask.png", 4, 305, 68, 549, 212),
    ("paper_fig5_overview.png", 5, 46, 68, 549, 289),
]

doc = pymupdf.open(PDF)
for name, page, x0, y0, x1, y1 in CROPS:
    pix = doc[page - 1].get_pixmap(dpi=220, clip=pymupdf.Rect(x0, y0, x1, y1))
    pix.save(os.path.join(HERE, name))
    print(name, pix.width, "x", pix.height)
