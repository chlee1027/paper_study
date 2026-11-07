# -*- coding: utf-8 -*-
"""U-Net 게재판의 그림 1 ~ 4 를 원문 PDF 에서 잘라 png 로 둔다. pymupdf 가 필요하다."""
import os

import pymupdf

H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "..", "papers", "MICCAI15_UNet_Convolutional_Networks_for_Biomedical_Image_Segmentation.pdf")
d = pymupdf.open(P)
for name, pno, cap in [("paper_fig1_architecture.png", 1, "Fig. 1."), ("paper_fig2_tile.png", 2, "Fig. 2."),
                       ("paper_fig3_hela_weight.png", 4, "Fig. 3."), ("paper_fig4_results.png", 6, "Fig. 4.")]:
    pg = d[pno]
    r = pg.search_for(cap)[0]
    clip = pymupdf.Rect(30, 42, pg.rect.width - 30, r.y0 - 2)
    pg.get_pixmap(matrix=pymupdf.Matrix(2.5, 2.5), clip=clip).save(os.path.join(H, name))
    print(name, clip)
