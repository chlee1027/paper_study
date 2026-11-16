# -*- coding: utf-8 -*-
"""CLIP 원문(PMLR v139 게재판)에서 그림 1 · 3 · 5 · 7 을 잘라 PNG 로 둔다. PyMuPDF 가 필요하다.

자르는 칸은 쪽의 그림 상자와 캡션 상자를 합친 것이다(pt, 쪽 크기 612 x 792).
"""
import os

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "..", "papers",
                   "ICML21_CLIP_Learning_Transferable_Visual_Models_From_Natural_Language_Supervision.pdf")
CROPS = [  # (이름, 쪽 번호(1부터), x0, y0, x1, y1)
    ("paper_fig1_overview.png", 2, 50, 62, 546, 296),
    ("paper_fig3_pseudocode.png", 3, 302, 62, 548, 318),
    ("paper_fig5_fewshot.png", 6, 50, 62, 296, 318),
    ("paper_fig7_robustness.png", 8, 50, 62, 548, 322),
]

doc = pymupdf.open(PDF)
for name, page, x0, y0, x1, y1 in CROPS:
    pix = doc[page - 1].get_pixmap(dpi=220, clip=pymupdf.Rect(x0, y0, x1, y1))
    pix.save(os.path.join(HERE, name))
    print(name, pix.width, "x", pix.height)
