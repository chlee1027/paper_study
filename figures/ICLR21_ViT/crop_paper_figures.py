# -*- coding: utf-8 -*-
"""ViT 논문(ICLR 2021 판)의 그림 1 · 6 · 7 · 9 를 원문 PDF 에서 잘라 png 로 둔다.

그림 1 은 벡터와 래스터가 섞여 있고(3 쪽), 그림 6 · 7 · 9 는 래스터 이미지가 들어 있어(8 · 9 · 17 쪽) 다시 그리지 않는다.
표와 나머지 그림의 수는 make_figures.py 가 옮겨 그린다. make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers",
                   "ICLR21_ViT_An_Image_is_Worth_16x16_Words_Transformers_for_Image_Recognition_at_Scale.pdf")
doc = pymupdf.open(PDF)
# (쪽 번호(1 부터), 사각형 pt). 쪽 그림을 130 dpi 로 띄워 눈으로 잡은 상자에 여백을 붙였다.
crops = {
    "paper_fig1_model.png": (3, pymupdf.Rect(135, 78, 480, 252)),
    "paper_fig6_attention.png": (8, pymupdf.Rect(395, 340, 502, 515)),
    "paper_fig7_inspect.png": (9, pymupdf.Rect(102, 88, 505, 212)),
    "paper_fig9_pos_hparam.png": (17, pymupdf.Rect(105, 200, 510, 335)),
}
for name, (pno, r) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=200, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
