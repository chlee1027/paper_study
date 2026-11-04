# -*- coding: utf-8 -*-
"""BERT 논문(NAACL 2019 발표집 판)의 그림 1 ~ 5 를 원문 PDF 에서 잘라 png 로 둔다.

사각형은 쪽을 120 dpi 로 띄워 눈으로 잡은 값에 여백 몇 pt 를 붙인 것이다. 표는 글자로 들어 있어
make_figures.py 가 수를 옮겨 그린다. make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers",
                   "NAACL19_BERT_Pre_training_of_Deep_Bidirectional_Transformers_for_Language_Understanding.pdf")
doc = pymupdf.open(PDF)
# (쪽 번호(1 부터), 사각형 pt)
crops = {
    "paper_fig1_pretrain_finetune.png": (3, pymupdf.Rect(70, 60, 528, 246)),
    "paper_fig2_input.png": (5, pymupdf.Rect(112, 58, 476, 172)),
    "paper_fig3_architectures.png": (13, pymupdf.Rect(74, 60, 530, 168)),
    "paper_fig4_finetune_tasks.png": (15, pymupdf.Rect(106, 62, 488, 438)),
    "paper_fig5_steps.png": (16, pymupdf.Rect(70, 565, 276, 704)),
}
for name, (pno, r) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=200, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))
