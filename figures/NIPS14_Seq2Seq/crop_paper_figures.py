# -*- coding: utf-8 -*-
"""seq2seq 논문(arXiv:1409.3215v3)의 그림 1 을 원문 PDF 에서 잘라 png 로 둔다.

그림 1 은 노트가 「그림과 캡션이 다르다」 고 짚는 자리라 원문 그대로 보여야 해서 잘라 넣는다.
그림 2 · 3 은 PDF 안에 벡터로 들어 있어 make_figures.py 가 좌표로 옮겨 그린다(그림 10 · 11 · 12).
make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers", "NIPS14_Seq2Seq_Sequence_to_Sequence_Learning_with_Neural_Networks.pdf")
doc = pymupdf.open(PDF)
# (쪽 번호(1 부터), 사각형 pt). 그림 1 의 선 상자(get_drawings 로 잰 x 128 ~ 484, y 327 ~ 397)에 여백 몇 pt 를 붙였다.
crops = {
    "paper_fig1_model.png": (2, pymupdf.Rect(120, 320, 492, 404)),
}
for name, (pno, r) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=200, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
