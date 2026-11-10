# -*- coding: utf-8 -*-
"""DRAEM ICCV 판의 그림 2 · 3 · 4 · 10 · 11 을 원문 PDF 에서 잘라 png 로 둔다. pymupdf 가 필요하다."""
import os

import pymupdf

H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "..", "papers", "ICCV21_DRAEM_A_Discriminatively_Trained_Reconstruction_Embedding_for_Surface_Anomaly_Detection.pdf")
d = pymupdf.open(P)
# (이름, 쪽, 캡션 앞머리, x0, x1, 위 끝)
for name, pno, cap, x0, x1, top in [("paper_fig2_concept.png", 1, "Figure 2. Autoencoders", 45, 292, 62),
                                    ("paper_fig3_architecture.png", 3, "Figure 3. The anomaly", 45, 552, 62),
                                    ("paper_fig4_simulation.png", 3, "Figure 4. Simulated", 305, 552, 262),
                                    ("paper_fig10_variants.png", 7, "Figure 10. Anomalies", 45, 292, 268),
                                    ("paper_fig11_dagm.png", 7, "Figure 11. Supervised", 305, 552, 196)]:
    pg = d[pno]
    r = pg.search_for(cap)[0]
    clip = pymupdf.Rect(x0, top, x1, r.y0 - 2)
    pg.get_pixmap(matrix=pymupdf.Matrix(2.2, 2.2), clip=clip).save(os.path.join(H, name))
    print(name, clip)
