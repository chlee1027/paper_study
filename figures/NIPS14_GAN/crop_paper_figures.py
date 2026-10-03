# -*- coding: utf-8 -*-
"""원 GAN 논문(NIPS 2014)의 그림 2 · 3 을 원문 PDF 에서 잘라 png 로 둔다.

이 둘은 생성기가 낸 표본 사진이라 다시 그릴 수 없다. 잘라 넣은 것이라는 사실을 노트 캡션에 밝힌다.
make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers", "NIPS14_GAN_Generative_Adversarial_Nets.pdf")
doc = pymupdf.open(PDF)
page = doc[6]   # 7 쪽
# 사각형은 pt 단위다. 그림 안 이미지 상자(get_image_info)에 a) ~ d) 글자와 여백을 붙였다.
crops = {
    "paper_fig2_samples.png": pymupdf.Rect(110, 78, 504, 362),
    "paper_fig3_interpolation.png": pymupdf.Rect(130, 471, 482, 497),
}
for name, r in crops.items():
    pix = page.get_pixmap(dpi=200, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
