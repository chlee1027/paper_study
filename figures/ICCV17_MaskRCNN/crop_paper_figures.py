# -*- coding: utf-8 -*-
"""Mask R-CNN ICCV 판의 그림 1 · 3 · 5 · 6 을 원문 PDF 에서 잘라 png 로 둔다. pymupdf 가 필요하다.

그림 2 · 4 는 전 쪽을 덮는 결과 예시이고 값이 없어 잘라 두지 않았다.
"""
import os

import pymupdf

H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "..", "papers", "ICCV17_MaskRCNN_Mask_R_CNN.pdf")
d = pymupdf.open(P)
# (이름, 쪽, 캡션 문자열, x0, x1, 위 여백). x 는 단 경계로 고른다.
for name, pno, cap, x0, x1, top in [("paper_fig1_framework.png", 0, "Figure 1.", 300, 560, 206),
                                    ("paper_fig3_heads.png", 3, "Figure 3.", 300, 560, 60),
                                    ("paper_fig5_fcis.png", 5, "Figure 5.", 40, 570, 60),
                                    ("paper_fig6_keypoint.png", 7, "Figure 6.", 40, 570, 60)]:
    pg = d[pno]
    r = [q for q in pg.search_for(cap) if q.x0 >= x0][0]
    clip = pymupdf.Rect(x0, top, x1, r.y0 - 2)
    pg.get_pixmap(matrix=pymupdf.Matrix(2.2, 2.2), clip=clip).save(os.path.join(H, name))
    print(name, clip)
