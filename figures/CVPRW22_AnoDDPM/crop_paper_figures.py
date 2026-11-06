# -*- coding: utf-8 -*-
"""AnoDDPM 논문(CVF 게재판)의 그림 1 ~ 6 을 원문 PDF 에서 잘라 png 로 둔다.

그림 4 · 6 은 PDF 안에 벡터로 들어 있어 곡선 값은 좌표에서 꺼냈고 make_figures.py 의 상수에 있다.
그림 2(a) 는 칸마다 190 x 190 픽셀 이미지가 들어 있다. make_figures.py 와 달리 pymupdf 가 필요하다.

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers",
                   "CVPRW22_AnoDDPM_Anomaly_Detection_with_Denoising_Diffusion_Probabilistic_Models_using_Simplex_Noise.pdf")
doc = pymupdf.open(PDF)
crops = {
    "paper_fig1_process.png": (1, pymupdf.Rect(308, 242, 550, 438), 170),
    "paper_fig2_simplex.png": (3, pymupdf.Rect(50, 72, 290, 202), 200),
    "paper_fig3_qualitative.png": (4, pymupdf.Rect(308, 72, 550, 500), 150),
    "paper_fig4_sweep.png": (5, pymupdf.Rect(50, 72, 552, 206), 170),
    "paper_fig5_mvtec_leather.png": (5, pymupdf.Rect(50, 250, 276, 404), 200),
    "paper_fig6_roc.png": (5, pymupdf.Rect(326, 248, 530, 404), 170),
}
for name, (pno, r, dpi) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=dpi, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
