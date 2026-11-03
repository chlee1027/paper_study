# -*- coding: utf-8 -*-
"""WGAN 논문(arXiv:1701.07875v3)의 그림 3 · 4 · 5 · 6 · 7 을 원문 PDF 에서 잘라 png 로 둔다.

이 그림들은 학습 곡선 위에 생성 표본 사진을 얹었거나(3 · 4) 표본 사진만 있어(5 · 6 · 7) 다시 그릴 수 없다.
잘라 넣은 것이라는 사실을 노트 캡션에 밝힌다. 곡선 값은 make_figures.py 의 그림 9 · 10 이 따로 옮겨 그린다.
make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers", "ICML17_WGAN_Wasserstein_GAN.pdf")
doc = pymupdf.open(PDF)
# (쪽 번호(1 부터), 사각형 pt). 사각형은 쪽 안 그림 이미지 상자(get_image_info)에 여백 몇 pt 를 붙인 것이다.
crops = {
    "paper_fig3_wgan_curves.png": (10, pymupdf.Rect(128, 122, 484, 352)),
    "paper_fig4_gan_js_curves.png": (11, pymupdf.Rect(128, 122, 484, 346)),
    "paper_fig5_dcgan_samples.png": (13, pymupdf.Rect(134, 123, 478, 170)),
    "paper_fig6_nobn_samples.png": (13, pymupdf.Rect(134, 209, 478, 256)),
    "paper_fig7_mlp_samples.png": (13, pymupdf.Rect(134, 339, 478, 386)),
}
for name, (pno, r) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=200, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
