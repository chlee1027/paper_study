# -*- coding: utf-8 -*-
"""YOLO CVPR 판의 그림 1 · 2 · 3 · 5(a) · 6 을 원문 PDF 에서 잘라 png 로 둔다. pymupdf 가 필요하다."""
import os

import pymupdf

H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "..", "papers", "CVPR16_YOLO_You_Only_Look_Once_Unified_Real_Time_Object_Detection.pdf")
d = pymupdf.open(P)
# (이름, 쪽, 캡션, x0, x1, 위 여백, 캡션 x 하한)
for name, pno, cap, x0, x1, top, xmin in [("paper_fig1_system.png", 0, "Figure 1:", 300, 560, 186, 300),
                                          ("paper_fig2_model.png", 1, "Figure 2:", 300, 560, 194, 300),
                                          ("paper_fig3_architecture.png", 2, "Figure 3:", 40, 570, 62, 0),
                                          ("paper_fig5_generalization.png", 7, "Figure 5:", 40, 570, 62, 0),
                                          ("paper_fig6_qualitative.png", 7, "Figure 6:", 40, 570, 290, 0)]:
    pg = d[pno]
    r = [q for q in pg.search_for(cap) if q.x0 >= xmin][0]
    clip = pymupdf.Rect(x0, top, x1, r.y0 - 2)
    pg.get_pixmap(matrix=pymupdf.Matrix(2.2, 2.2), clip=clip).save(os.path.join(H, name))
    print(name, clip)
