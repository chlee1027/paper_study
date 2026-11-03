# -*- coding: utf-8 -*-
"""Cho 외 EMNLP 2014 (RNN 인코더-디코더) 원문 PDF 에서 두 가지를 꺼낸다.

1. 그림 4 · 5 (Barnes-Hut-SNE 로 낮춘 단어 · 구문 표현) 를 잘라 png 로 둔다.
   이 그림들은 글자 수백 개가 겹친 산점도라 다시 그릴 수 없다. 잘라 넣은 것이라는 사실을 노트 캡션에 밝힌다.
   원 그림은 PDF 안에 1200x900 픽셀 이미지로 들어 있다(그림 4 는 둘, 그림 5 는 넷).
2. 그림 3 (RNN 점수 대 구문표 점수) 의 점 좌표를 읽어 paper_fig3_points.csv 로 둔다.
   그림 3 은 이미지가 아니라 벡터 그림이다. 표시 하나가 너비 0.219pt 의 대각선 둘(가로 · 세로 1.83pt)로 그린
   'x' 이고, 그런 짝이 정확히 5,000 개 있다. 각 'x' 의 가운데를 축 틀(가로 343.73 ~ 495.96pt 가 -60 ~ 0,
   세로 587.39 ~ 467.28pt 가 -14 ~ 0) 로 값에 옮긴다. 축 틀 끝이 눈금 글자 '0' 의 가운데와 0.1pt 안에서
   맞는 것을 확인했다. make_figures.py 의 그림 11 이 이 csv 를 읽는다.

make_figures.py 와 달리 pymupdf 가 필요하다(pip install pymupdf).

  python crop_paper_figures.py
"""
import os
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(OUT, "..", "..", "papers",
                   "EMNLP14_GRU_Learning_Phrase_Representations_using_RNN_Encoder_Decoder_for_Statistical_Machine_Translation.pdf")
doc = pymupdf.open(PDF)

# (쪽 번호(1 부터), 사각형 pt). 사각형은 쪽 안 그림 이미지 상자(get_image_info)에 여백 몇 pt 를 붙인 것이다.
crops = {
    "paper_fig4_word_embedding.png": (8, pymupdf.Rect(70, 270, 527, 440)),
    "paper_fig5_phrase_embedding.png": (9, pymupdf.Rect(70, 60, 527, 390)),
}
for name, (pno, r) in crops.items():
    pix = doc[pno - 1].get_pixmap(dpi=200, clip=r)
    pix.save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, pix.width, pix.height))

# 그림 3 의 점 좌표
X0, X1 = 343.73248291015625, 495.958251953125   # 가로 축 틀: -60, 0
Y0, Y1 = 587.3912963867188, 467.28448486328125   # 세로 축 틀: -14, 0
pts = []
for dr in doc[6 - 1].get_drawings():
    w = dr.get("width")
    if not w or abs(w - 0.21924) > 1e-3:
        continue
    it = dr["items"][0]
    if len(it) != 3 or it[0] != "l":
        continue
    a, b = it[1], it[2]
    if round(b.x - a.x, 2) == 1.83 and round(b.y - a.y, 2) == 1.83:      # 'x' 의 '\' 획 하나만 센다
        cx, cy = a.x + 0.915, a.y + 0.915
        pts.append((-60 + 60 * (cx - X0) / (X1 - X0), -14 + 14 * (Y0 - cy) / (Y0 - Y1)))
with open(os.path.join(OUT, "paper_fig3_points.csv"), "w", encoding="utf-8") as f:
    f.write("rnn_log_score,tm_log_score\n")
    for x, y in pts:
        f.write("%.4f,%.4f\n" % (x, y))
print("  paper_fig3_points.csv  %d 점" % len(pts))
