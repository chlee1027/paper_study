# -*- coding: utf-8 -*-
"""Faster R-CNN NIPS 판의 그림 1 · 2 를 원문 PDF 에서 잘라 png 로 둔다. pymupdf 가 필요하다.

그림 2 는 PDF 안에 벡터로 들어 있어 곡선 값은 좌표에서 꺼냈고 make_figures.py 의 상수에 있다.
"""
import os

import pymupdf

H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "..", "papers", "NIPS15_FasterRCNN_Towards_Real_Time_Object_Detection_with_Region_Proposal_Networks.pdf")
d = pymupdf.open(P)
for name, pno, cap, top in [("paper_fig1_rpn.png", 2, "Figure 1:", 60), ("paper_fig2_recall.png", 7, "Figure 2:", 70)]:
    pg = d[pno]
    r = pg.search_for(cap)[0]
    clip = pymupdf.Rect(70, top, pg.rect.width - 70, r.y0 - 2)
    pg.get_pixmap(matrix=pymupdf.Matrix(2.5, 2.5), clip=clip).save(os.path.join(H, name))
    print(name, clip)
