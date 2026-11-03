# -*- coding: utf-8 -*-
"""Bahdanau 외(ICLR 2015, arXiv:1409.0473v6) 원문에서 그림 둘을 잘라 내고, 그림 2 · 3 의 수를 CSV 로 꺼낸다.

PyMuPDF 가 필요하다. 저장소 맨 위에서

  python figures/ICLR15_Attention/crop_paper_figures.py

로 돌린다. 만드는 것:

  paper_fig1_model.png        원문 그림 1 (3 쪽, 모델 그림)
  paper_fig3_alignments.png   원문 그림 3 (6 쪽, 정렬 무게 넷)
  paper_fig2_curves.csv       원문 그림 2 (5 쪽) 곡선 넷의 꼭짓점. PDF 좌표(pt)와 눈금으로 바꾼 값
  paper_fig3_alpha.csv        원문 그림 3 의 칸마다 무게. 그림 안 회색조 이미지의 칸 가운데 화소 값 / 255

그림 2 는 PDF 안에 선(벡터)으로 들어 있고, 그림 3 의 네 칸은 칸 하나가 16 x 16 또는 14 x 14 화소인
회색조 이미지(0 = 검정 = 무게 0, 255 = 흰색 = 무게 1, 원문 캡션)로 들어 있다. 그래서 눈으로 읽지 않고
좌표와 화소 값을 그대로 꺼낸다.
"""
import csv, io, os, sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "..", "papers",
                   "ICLR15_Attention_Neural_Machine_Translation_by_Jointly_Learning_to_Align_and_Translate.pdf")


def crop(doc, page, rect, name, dpi):
    pix = doc[page].get_pixmap(dpi=dpi, clip=pymupdf.Rect(*rect))
    pix.save(os.path.join(HERE, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))


# 그림 2: 곡선 넷의 그리기 순서와 범례(실선 · 점선 · 파선 · 일점쇄선)가 같다는 것을 범례 글자 자리로 확인했다.
FIG2_CURVES = [(3, "RNNsearch-50"), (4, "RNNsearch-30"), (5, "RNNencdec-50"), (6, "RNNencdec-30")]
FIG2_X0, FIG2_X1 = 136.07, 364.51   # 눈금 0 과 60 의 x 자리(pt)
FIG2_Y0, FIG2_Y1 = 204.91, 87.01    # 눈금 0 과 30 의 y 자리(pt)

# 그림 3: 이미지 번호(xref), 칸 자리, 원문 낱말(가로), 번역 낱말(세로). 낱말은 원문 그림의 눈금 글자 그대로.
FIG3 = [
    ("a", 338, "The agreement on the European Economic Area was signed in August 1992 . <end>",
     "L' accord sur la zone économique européenne a été signé en août 1992 . <end>"),
    ("b", 377, "It should be noted that the marine environment is the least known of environments . <end>",
     "Il convient de noter que l' environnement marin est le moins connu de l' environnement . <end>"),
    ("c", 409, "Destruction of the equipment means that Syria can no longer produce new chemical weapons . <end>",
     "La destruction de l' équipement signifie que la Syrie ne peut plus produire de nouvelles armes chimiques . <end>"),
    ("d", 445, '" This will change my future with my family , " the man said . <end>',
     '" Cela va changer mon avenir avec ma famille " , a dit l\' homme . <end>'),
]


def fig2(doc):
    dr = doc[4].get_drawings()
    rows = []
    for k, name in FIG2_CURVES:
        items = dr[k]["items"]
        pts = [(items[0][1].x, items[0][1].y)] + [(it[2].x, it[2].y) for it in items]
        for (x, y) in pts:
            xv = (x - FIG2_X0) / (FIG2_X1 - FIG2_X0) * 60
            yv = (FIG2_Y0 - y) / (FIG2_Y0 - FIG2_Y1) * 30
            rows.append([name, "%.2f" % xv, "%.3f" % yv, "%.2f" % x, "%.2f" % y])
    with io.open(os.path.join(HERE, "paper_fig2_curves.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "x_tick", "bleu", "pdf_x_pt", "pdf_y_pt"])
        w.writerows(rows)
    print("  paper_fig2_curves.csv  %d rows" % len(rows))


def fig3(doc):
    rows = []
    for panel, xref, src, tgt in FIG3:
        src, tgt = src.split(), tgt.split()
        pm = pymupdf.Pixmap(doc, xref)
        W, H = pm.width, pm.height
        cw, ch = W // len(src), H // len(tgt)
        assert cw * len(src) == W and ch * len(tgt) == H, (panel, W, H)
        s = pm.samples
        spread = 0
        for i in range(len(tgt)):
            for j in range(len(src)):
                vals = [s[(i * ch + yy) * W + j * cw + xx] for yy in range(ch) for xx in range(cw)]
                spread = max(spread, max(vals) - min(vals))
                rows.append([panel, i, tgt[i], j, src[j], "%.4f" % (vals[len(vals) // 2] / 255.0)])
        print("  panel %s: %d x %d cells of %d px, largest spread inside a cell = %d" % (
            panel, len(tgt), len(src), cw, spread))
    with io.open(os.path.join(HERE, "paper_fig3_alpha.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["panel", "i_target", "target_word", "j_source", "source_word", "alpha"])
        w.writerows(rows)
    print("  paper_fig3_alpha.csv  %d rows" % len(rows))


def main():
    doc = pymupdf.open(PDF)
    crop(doc, 2, (380, 350, 508, 512), "paper_fig1_model.png", 300)
    crop(doc, 5, (104, 78, 508, 523), "paper_fig3_alignments.png", 200)
    fig2(doc)
    fig3(doc)


if __name__ == "__main__":
    main()
