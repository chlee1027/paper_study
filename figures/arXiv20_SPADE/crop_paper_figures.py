# -*- coding: utf-8 -*-
"""SPADE 논문(arXiv v3)의 그림 1 · 2 · 3 을 원문 PDF 에서 잘라 png 로 둔다.

셋 다 정성 예시이고 수가 없어 값을 읽을 것이 없다. make_figures.py 와 달리 pymupdf 가 필요하다.

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers",
                   "arXiv20_SPADE_Sub_Image_Anomaly_Detection_with_Deep_Pyramid_Correspondences.pdf")
doc = pymupdf.open(PDF)
for name, pno in (("paper_fig1_flowers_birds.png", 7),
                  ("paper_fig2_hazelnut_metalnut.png", 11),
                  ("paper_fig3_cable_grid_stc.png", 12)):
    page = doc[pno - 1]
    rects = [r for info in page.get_images(full=True) for r in page.get_image_rects(info[0])]
    u = rects[0]
    for r in rects[1:]:
        u = u | r
    pix = page.get_pixmap(dpi=130, clip=u)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d  from %s" % (name, pix.width, pix.height, u))
