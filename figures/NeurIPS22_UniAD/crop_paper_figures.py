# -*- coding: utf-8 -*-
"""UniAD 논문(NeurIPS 2022 게재판과 보충 자료)의 그림을 원문 PDF 에서 잘라 png 로 둔다.

그림 2a · 4 는 PDF 안에 래스터로 들어 있어 벡터 좌표가 없다. 값은 색으로 곡선을 뽑아 읽었고
make_figures.py 의 CURVES 상수에 있다. make_figures.py 와 달리 pymupdf 가 필요하다.

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(OUT, "..", "..", "papers", "NeurIPS22_UniAD_A_Unified_Model_for_Multi_class_Anomaly_Detection")
main = pymupdf.open(BASE + ".pdf")
supp = pymupdf.open(BASE + "_Supplemental.pdf")
crops = {
    "paper_fig1_setting.png": (main, 2, pymupdf.Rect(105, 70, 508, 192), 170),
    "paper_fig2_shortcut.png": (main, 4, pymupdf.Rect(105, 68, 508, 204), 240),
    "paper_fig3_framework.png": (main, 5, pymupdf.Rect(112, 70, 502, 260), 170),
    "paper_fig4_unified_separate.png": (main, 5, pymupdf.Rect(107, 342, 306, 430), 240),
    "paper_fig5_nma.png": (main, 5, pymupdf.Rect(316, 350, 500, 472), 170),
    "paper_figS1_lqd_designs.png": (supp, 4, pymupdf.Rect(105, 70, 508, 166), 170),
}
for name, (doc, pno, r, dpi) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=dpi, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
