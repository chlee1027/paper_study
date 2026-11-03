# -*- coding: utf-8 -*-
"""seq2seq 노트(Sutskever, Vinyals, Le, arXiv:1409.3215v3)의 그림 열넷을 만든다.

색과 글꼴은 저장소의 앞선 노트 그림과 맞췄다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

계산으로 원문을 확인하는 그림이 여럿이다 — 2(입력 뒤집기가 짝 낱말 사이 거리를 어떻게 바꾸는가),
3(파라미터 384M 을 층 · 폭 · 어휘로 다시 세기), 4(학습률 일정의 두 읽기), 5(「열흘 남짓」 을 처리 속도로
다시 세기), 7(표 1 의 차이를 단계로 가르기), 8(표 2 의 차이), 9(빔 탐색 작은 예). 계산한 값은 돌릴 때
화면에도 찍는다.

그림 10 · 11 · 12 의 값은 원문 그림 3 · 2 가 PDF 안에 벡터(선과 점)로 들어 있어, PyMuPDF 의 get_drawings 로
꺼낸 PDF 좌표(pt)를 아래 RAW_* 상수에 그대로 적어 두고 이 파일이 눈금으로 바꾼 것이다 — 이 파일은 PDF 를
읽지 않는다. 원문 그림 1 은 crop_paper_figures.py 가 잘라 png 로 둔다.
"""
import io, os, math

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"
NODE      = "#F6F7F5"
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 인코더 · LSTM 쪽
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 디코더 · 비교 상대(SMT) 쪽
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 고정 길이 벡터 v
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"
OK_SOFT   = "#D6EEDD"
NO        = "#C0392B"
NO_SOFT   = "#F6D9D5"
PURP      = "#8E44AD"
PURP_SOFT = "#EADCF0"
FONT = "IBM Plex Sans KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"


# ── 공통 도구 ──────────────────────────────────────────────────────────────
def svg(name, w, h, body, label):
    s = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="%s" role="img" aria-label="%s">' % (w, h, w, h, FONT, label))
    s += '<rect x="0" y="0" width="100%%" height="100%%" fill="%s"/>' % BG
    s += body + "</svg>\n"
    io.open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8").write(s)
    print("  " + name + ".svg  %dx%d" % (w, h))


def arrow(idd, color):
    return ('<marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>' % (idd, color))


def defs():
    return ("<defs>" + arrow("af", FWD) + arrow("ar", REV) + arrow("ai", INK2) + arrow("ao", OK)
            + arrow("an", NO) + arrow("ac", CODE) + "</defs>")


def txt(x, y, t, size=12, fill=None, anchor="middle", weight=None, style=None):
    a = 'x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s"' % (x, y, size, fill or INK, anchor)
    if weight:
        a += ' font-weight="%s"' % weight
    if style:
        a += ' font-style="%s"' % style
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return "<text %s>%s</text>" % (a, t)


def box(x, y, w, h, fill=None, stroke=None, sw=1.2, rx=6, dash=None):
    a = ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-width="%s"'
         % (x, y, w, h, rx, fill or NODE, stroke or INK, sw))
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    return a + "/>"


def line(x1, y1, x2, y2, color=None, sw=1.2, dash=None, marker=None, op=None):
    a = '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"' % (
        x1, y1, x2, y2, color or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if marker:
        a += ' marker-end="url(#%s)"' % marker
    if op:
        a += ' opacity="%s"' % op
    return a + "/>"


def circ(cx, cy, r, fill=None, stroke=None, sw=1.2):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (
        cx, cy, r, fill or NODE, stroke or INK, sw)


def path(d, stroke=None, fill="none", sw=1.6, dash=None, marker=None):
    a = '<path d="%s" fill="%s" stroke="%s" stroke-width="%s"' % (d, fill, stroke or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if marker:
        a += ' marker-end="url(#%s)"' % marker
    return a + "/>"


def polyline(pts, stroke, sw=2, dash=None):
    d = "M" + " L".join("%.1f,%.1f" % p for p in pts)
    return path(d, stroke, sw=sw, dash=dash)


def axes(x0, y0, x1, y1, xt, yt, fx, fy, xl=None, yl=None, xfmt="%g", yfmt="%g"):
    s = line(x0, y1, x1, y1, INK2, 1.2) + line(x0, y0, x0, y1, INK2, 1.2)
    for t in xt:
        s += line(fx(t), y1, fx(t), y1 + 4, INK2, 1) + txt(fx(t), y1 + 17, xfmt % t, 10, fill=MUTED)
    for t in yt:
        s += line(x0 - 4, fy(t), x0, fy(t), INK2, 1) + txt(x0 - 7, fy(t) + 4, yfmt % t, 10, fill=MUTED, anchor="end")
        s += line(x0, fy(t), x1, fy(t), LINE, 0.8, dash="2 3")
    if xl:
        s += txt((x0 + x1) / 2, y1 + 34, xl, 11, fill=INK2)
    if yl:
        s += txt(x0, y0 - 10, yl, 11, fill=INK2, anchor="start")
    return s


def lines_at(x, y, rows, size=12, gap=21, anchor="start"):
    s = ""
    for j, r in enumerate(rows):
        if isinstance(r, tuple):
            t, c = r[0], r[1]
            w = r[2] if len(r) > 2 else None
        else:
            t, c, w = r, INK2, None
        s += txt(x, y + gap * j, t, size, fill=c, anchor=anchor, weight=w)
    return s


def table_cols(x, y, head, rows, size=11, gap=20, xs=(0, 70, 140, 210)):
    s = ""
    for k, hcell in enumerate(head):
        s += txt(x + xs[k] + 50, y, hcell, size, fill=INK, anchor="end", weight="bold")
    for j, r in enumerate(rows):
        for k in range(4):
            s += txt(x + xs[k] + 50, y + gap * (j + 1), r[k], size, fill=r[4], anchor="end")
    return s


print("그림을 만든다 ->", OUT)

# ── 원문의 수 ───────────────────────────────────────────────────────────────
LAYERS, CELLS, EMB = 4, 1000, 1000
V_SRC, V_TGT = 160000, 80000
SENT, FR_WORDS, EN_WORDS = 12_000_000, 348_000_000, 304_000_000
BATCH, EPOCHS = 128, 7.5
WPS_1GPU, WPS_8GPU = 1700, 6300

# 표 1 · 표 2 (원문 6 쪽, 시험셋 ntst14)
T1 = [("Bahdanau 외 [2]", 28.45, "other"),
      ("기준 SMT [29]", 33.30, "smt"),
      ("단일 · 정방향 · 빔 12", 26.17, "single"),
      ("단일 · 뒤집음 · 빔 12", 30.59, "single"),
      ("앙상블 5 · 뒤집음 · 빔 1", 33.00, "ens"),
      ("앙상블 2 · 뒤집음 · 빔 12", 33.27, "ens"),
      ("앙상블 5 · 뒤집음 · 빔 2", 34.50, "ens"),
      ("앙상블 5 · 뒤집음 · 빔 12", 34.81, "ens")]
T2 = [("기준 SMT [29]", 33.30, "smt"),
      ("Cho 외 [5]", 34.54, "other"),
      ("WMT'14 최고 [9]", 37.0, "other"),
      ("다시 매김 · 단일 · 정방향", 35.61, "single"),
      ("다시 매김 · 단일 · 뒤집음", 35.85, "single"),
      ("다시 매김 · 앙상블 5 · 뒤집음", 36.5, "ens"),
      ("오라클 다시 매김 (~45)", 45.0, "other")]

# ── 원문 그림 3 · 그림 2 의 PDF 좌표 (pt). PyMuPDF get_drawings 로 꺼낸 값 ───────────
# 그림 3: 두 칸 모두 y 눈금 20 이 540.161, 40 이 401.470 (5 BLEU 마다 34.673 pt).
# 오른쪽 칸 x 눈금 0 이 324.907, 3500 이 464.457. 왼쪽 칸의 x 눈금 글자(4 7 8 12 17 22 28 35 79)는
# 점 자리 157.85 161.43 165.42 177.38 197.32 217.25 237.19 257.12 277.18 에 붙어 있다.
F3_Y20, F3_Y40 = 540.161, 401.470
F3R_X0, F3R_X3500 = 324.907, 464.457
F3L_X0 = 157.446                     # 왼쪽 칸 축 상자의 왼쪽 끝
RAW_F3L_LSTM = [(159.82, 559.59), (161.43, 462.63), (165.42, 513.32), (177.38, 444.53), (197.32, 448.56),
                (217.25, 438.22), (237.19, 430.87), (257.12, 426.37), (277.18, 441.34)]
RAW_F3L_SMT = [(160.07, 559.59), (161.43, 486.70), (165.42, 516.38), (177.38, 463.05), (197.32, 462.49),
               (217.25, 448.49), (237.19, 443.49), (257.12, 446.20), (277.18, 442.31)]
F3L_LABELS = [4, 7, 8, 12, 17, 22, 28, 35, 79]
F3L_TICKX = [157.85, 161.43, 165.42, 177.38, 197.32, 217.25, 237.19, 257.12, 277.18]
RAW_F3R_LSTM = [(325.31, 514.09), (328.89, 398.63), (332.88, 407.43), (344.84, 411.18), (364.78, 422.90),
                (384.71, 426.57), (404.65, 435.73), (424.59, 453.41), (444.64, 479.00)]
RAW_F3R_SMT = [(325.31, 497.44), (328.89, 422.69), (332.88, 434.27), (344.84, 438.08), (364.78, 443.98),
               (384.71, 444.39), (404.65, 441.48), (424.59, 455.28), (444.64, 470.12)]
# 그림 2: 점(파란 동그라미)의 가운데. 왼쪽 칸 x 눈금 -8 이 142.48, 10 이 283.59 / y 눈금 -6 이 621.43, 4 가 515.37.
# 오른쪽 칸 x 눈금 -15 가 334.72, 20 이 475.83 / y 눈금 -20 이 621.43, 15 가 510.09.
RAW_F2L = [("John respects Mary", 154.94, 609.50, "J>M"), ("Mary respects John", 240.61, 560.02, "M>J"),
           ("John admires Mary", 149.52, 565.61, "J>M"), ("Mary admires John", 209.95, 526.31, "M>J"),
           ("Mary is in love with John", 221.88, 536.98, "M>J"), ("John is in love with Mary", 158.13, 578.99, "J>M")]
RAW_F2R = [("I gave her a card in the garden", 413.78, 608.18, "I>her"),
           ("In the garden , I gave her a card", 344.37, 582.44, "I>her"),
           ("She was given a card by me in the garden", 379.77, 574.31, "I>her"),
           ("She gave me a card in the garden", 403.99, 531.87, "she>me"),
           ("In the garden , she gave me a card", 375.74, 526.11, "she>me"),
           ("I was given a card by her in the garden", 387.12, 513.24, "she>me")]


def f3_bleu(y):
    return 20 + (F3_Y20 - y) / ((F3_Y20 - F3_Y40) / 20)


def f3_index(x):
    return (x - F3R_X0) / ((F3R_X3500 - F3R_X0) / 3500)


def f2_conv(pts, xa, xb, ya, yb):
    (vx0, px0), (vx1, px1) = xa, xb
    (vy0, py0), (vy1, py1) = ya, yb
    out = []
    for name, px, py, g in pts:
        out.append((name, vx0 + (px - px0) * (vx1 - vx0) / (px1 - px0), vy0 + (py - py0) * (vy1 - vy0) / (py1 - py0), g))
    return out


# ── 그림 1. 모델 ────────────────────────────────────────────────────────────
W, H = 900, 520
b = defs()
b += txt(20, 30, "실제 모델 — 인코더 LSTM 4층이 뒤집은 원문을 읽고, 마지막 상태(8,000 개 수)를 디코더 LSTM 4층의 첫 상태로 넘긴다", 14, anchor="start", weight="bold")
src = ["C", "B", "A", "<EOS>"]
tgt_in = ["<EOS>", "W", "X", "Y", "Z"]
tgt_out = ["W", "X", "Y", "Z", "<EOS>"]
cx0, dx, top = 60, 82, 130
lh = 46
for li in range(4):
    yy = top + (3 - li) * lh
    for i in range(4):
        b += box(cx0 + i * dx, yy, 56, 26, FWD_SOFT, FWD, 1.0, 4)
        if i < 3:
            b += line(cx0 + i * dx + 56, yy + 13, cx0 + (i + 1) * dx - 2, yy + 13, FWD, 1.2, marker="af")
        if li < 3:
            b += line(cx0 + i * dx + 28, yy, cx0 + i * dx + 28, yy - lh + 28, FWD, 1.0, marker="af")
    b += txt(cx0 - 10, yy + 18, "%d층" % (li + 1), 10, fill=MUTED, anchor="end")
for i, w in enumerate(src):
    b += txt(cx0 + i * dx + 28, top + 4 * lh + 20, w, 12, fill=FWD, weight="bold")
    b += line(cx0 + i * dx + 28, top + 4 * lh + 6, cx0 + i * dx + 28, top + 3 * lh + 28, FWD, 1.0, marker="af")
b += txt(cx0 + 1.5 * dx + 28, top + 4 * lh + 42, "인코더 입력 — 원문 A B C 를 뒤집어 C B A 로 읽는다", 11, fill=FWD)
b += txt(cx0 + 1.5 * dx + 28, top + 4 * lh + 60, "어휘 160,000 · 낱말 벡터 1,000", 11, fill=MUTED)
# v
vx = cx0 + 4 * dx + 8
b += box(vx, top - 4, 70, 4 * lh + 2, CODE_SOFT, CODE, 1.4, 6)
b += txt(vx + 35, top + 40, "v", 18, fill=CODE, weight="bold")
b += txt(vx + 35, top + 70, "층마다", 10, fill=CODE)
b += txt(vx + 35, top + 84, "h 1,000", 10, fill=CODE)
b += txt(vx + 35, top + 98, "c 1,000", 10, fill=CODE)
b += txt(vx + 35, top + 122, "4 x 2,000", 10, fill=CODE)
b += txt(vx + 35, top + 136, "= 8,000", 11, fill=CODE, weight="bold")
for li in range(4):
    yy = top + (3 - li) * lh
    b += line(cx0 + 3 * dx + 56, yy + 13, vx, yy + 13, CODE, 1.0, dash="3 2")
    b += line(vx + 70, yy + 13, vx + 92, yy + 13, CODE, 1.2, marker="ac")
dx0 = vx + 94
for li in range(4):
    yy = top + (3 - li) * lh
    for i in range(5):
        b += box(dx0 + i * dx, yy, 56, 26, REV_SOFT, REV, 1.0, 4)
        if i < 4:
            b += line(dx0 + i * dx + 56, yy + 13, dx0 + (i + 1) * dx - 2, yy + 13, REV, 1.2, marker="ar")
        if li < 3:
            b += line(dx0 + i * dx + 28, yy, dx0 + i * dx + 28, yy - lh + 28, REV, 1.0, marker="ar")
for i in range(5):
    b += txt(dx0 + i * dx + 28, top + 4 * lh + 20, tgt_in[i], 12, fill=REV, weight="bold")
    b += line(dx0 + i * dx + 28, top + 4 * lh + 6, dx0 + i * dx + 28, top + 3 * lh + 28, REV, 1.0, marker="ar")
    b += box(dx0 + i * dx + 4, top - 44, 48, 22, NODE, INK2, 1.0, 4)
    b += txt(dx0 + i * dx + 28, top - 29, "소프트", 9, fill=INK2)
    b += line(dx0 + i * dx + 28, top, dx0 + i * dx + 28, top - 20, INK2, 1.0, marker="ai")
    b += txt(dx0 + i * dx + 28, top - 52, tgt_out[i], 12, fill=INK, weight="bold")
b += txt(dx0 + 2 * dx + 28, top + 4 * lh + 42, "디코더 입력 — 앞에서 낸 낱말을 다음 칸에 넣는다", 11, fill=REV)
b += txt(dx0 + 2 * dx + 28, top + 4 * lh + 60, "어휘 80,000 · 소프트맥스 80,000 갈래", 11, fill=MUTED)
b += txt(20, H - 46, "원문 식 (1): p(y1..yT' | x1..xT) = Π p(yt | v, y1..yt-1). 인코더와 디코더는 서로 다른 LSTM 이다(파라미터를 나누지 않는다).", 11, fill=INK2, anchor="start")
b += txt(20, H - 26, "v 를 층마다의 h · c 로 읽은 것은 내 해석이다 — 원문은 「문장을 나타내는 데 8,000 개의 실수를 쓴다」 고만 적는다(3.4절).", 11, fill=MUTED, anchor="start")
svg("fig01_model", W, H, b, "인코더 디코더 LSTM 구조")

# ── 그림 2. 입력 뒤집기와 짝 낱말 사이 거리 ───────────────────────────────────────
T = 5
fwd_d = [T + 1 for i in range(1, T + 1)]      # 원문 i 자리 i, 번역 i 자리 T+1+i (사이에 <EOS> 하나)
rev_d = [2 * i for i in range(1, T + 1)]      # 원문 i 가 T+1-i 자리로 간다
print("  [그림 2] T=%d 정방향 거리 %s 평균 %.2f 최소 %d / 뒤집음 %s 평균 %.2f 최소 %d"
      % (T, fwd_d, sum(fwd_d) / T, min(fwd_d), rev_d, sum(rev_d) / T, min(rev_d)))
for TT in (10, 25, 30):
    fd = [TT + 1] * TT
    rd = [2 * i for i in range(1, TT + 1)]
    print("  [그림 2] T=%d 평균 %.1f -> %.1f, 최소 %d -> %d, 거리 10 이하인 짝 %d -> %d"
          % (TT, sum(fd) / TT, sum(rd) / TT, min(fd), min(rd), sum(d <= 10 for d in fd), sum(d <= 10 for d in rd)))
W, H = 900, 500
b = defs()
b += txt(20, 30, "입력 뒤집기 — 짝 낱말 사이 거리의 평균은 그대로이고, 가장 짧은 거리(최소 시간 지연)만 6 에서 2 로 준다", 14, anchor="start", weight="bold")
b += txt(20, 52, "가정: 원문 다섯 낱말이 번역 다섯 낱말과 같은 순서로 하나씩 짝을 이룬다(단조 1 대 1 정렬). 원문은 이 가정을 적지 않는다", 11, fill=MUTED, anchor="start")


def seqrow(y, words, colors, title):
    s = txt(20, y + 18, title, 12, fill=INK, anchor="start", weight="bold")
    for k, (w, c) in enumerate(zip(words, colors)):
        x = 150 + k * 66
        s += box(x, y, 56, 28, c[1], c[0], 1.0, 4)
        s += txt(x + 28, y + 19, w, 12, fill=c[0], weight="bold")
        s += txt(x + 28, y + 44, str(k + 1), 9, fill=MUTED)
    return s


S = [(FWD, FWD_SOFT)]
E = [(INK2, NODE)]
Tg = [(REV, REV_SOFT)]
b += seqrow(130, ["a1", "a2", "a3", "a4", "a5", "EOS", "b1", "b2", "b3", "b4", "b5"], S * 5 + E + Tg * 5, "정방향")
for i in range(1, 6):
    x1 = 150 + (i - 1) * 66 + 28
    x2 = 150 + (5 + i) * 66 + 28
    hgt = 18 + 6 * i
    b += path("M%d,%d C%d,%d %d,%d %d,%d" % (x1, 130, x1, 130 - hgt, x2, 130 - hgt, x2, 130), FWD, sw=1.0)
b += txt(150, 196, "짝 (a_i, b_i) 거리: 6 6 6 6 6 — 평균 6 · 최소 6", 12, fill=FWD, anchor="start", weight="bold")
b += seqrow(290, ["a5", "a4", "a3", "a2", "a1", "EOS", "b1", "b2", "b3", "b4", "b5"], S * 5 + E + Tg * 5, "원문 뒤집음")
for i in range(1, 6):
    x1 = 150 + (5 - i) * 66 + 28
    x2 = 150 + (5 + i) * 66 + 28
    hgt = 10 + 12 * i
    b += path("M%d,%d C%d,%d %d,%d %d,%d" % (x1, 290, x1, 290 - hgt, x2, 290 - hgt, x2, 290), OK, sw=1.0)
b += txt(150, 356, "짝 (a_i, b_i) 거리: 2 4 6 8 10 — 평균 6 · 최소 2", 12, fill=OK, anchor="start", weight="bold")
b += lines_at(20, 400, [
    ("일반식(내가 센 것): 원문 길이 T, 짝 i 의 거리는 정방향 T + 1, 뒤집으면 2i. 평균은 둘 다 T + 1 이다 — 원문 3.3절 「평균 거리는 바뀌지 않는다」 와 맞는다.", INK2),
    ("T = 25(학습 데이터 영어 문장의 평균 낱말 수 25.3) 이면 거리 10 이하인 짝이 정방향 0 개, 뒤집으면 5 개다. 최소 지연은 26 에서 2.", INK2),
    ("이 그림은 정렬이 단조일 때의 셈이다. 어순이 다른 짝(영어 형용사 대 프랑스어 형용사 위치)은 이 셈 밖이다.", MUTED),
], 11, 22)
svg("fig02_reversal_lag", W, H, b, "입력 뒤집기와 짝 거리")

# ── 그림 3. 파라미터 384M 다시 세기 ─────────────────────────────────────────────
lstm_layer = 4 * (CELLS * (EMB if True else CELLS) + CELLS * CELLS + CELLS)   # 첫 층 입력 = 낱말 벡터 1,000, 위층 입력 = 아래층 h 1,000
lstm_stack = LAYERS * lstm_layer
peep = LAYERS * 3 * CELLS
emb_src = V_SRC * EMB
emb_tgt = V_TGT * EMB
soft = V_TGT * CELLS + V_TGT
total = emb_src + emb_tgt + 2 * lstm_stack + soft
parts = [("원문 낱말 벡터 160,000 x 1,000", emb_src, FWD), ("번역 낱말 벡터 80,000 x 1,000", emb_tgt, REV),
         ("인코더 LSTM 4층", lstm_stack, FWD), ("디코더 LSTM 4층", lstm_stack, REV),
         ("소프트맥스 1,000 x 80,000 + 치우침", soft, INK2)]
print("  [그림 3] LSTM 한 층 %d, 4층 %d, 두 묶음 %d" % (lstm_layer, lstm_stack, 2 * lstm_stack))
print("  [그림 3] 합계 %d (= %.1fM). 엿보기 연결을 넣으면 +%d x 2 = %d" % (total, total / 1e6, peep, total + 2 * peep))
for n, v, c in parts:
    print("  [그림 3]   %-34s %12d  %.1f%%" % (n, v, 100 * v / total))
W, H = 900, 400
b = defs()
b += txt(20, 30, "파라미터 384M 을 층 · 폭 · 어휘로 다시 세면 384,112,000 — 그 가운데 83.3% 가 낱말 표와 소프트맥스다", 14, anchor="start", weight="bold")
X0, X1, Y = 40, 860, 80
x = X0
for n, v, c in parts:
    wdt = (X1 - X0) * v / total
    soft_c = {FWD: FWD_SOFT, REV: REV_SOFT, INK2: NODE}[c]
    b += box(x, Y, wdt, 46, soft_c, c, 1.2, 0)
    if wdt > 70:
        b += txt(x + wdt / 2, Y + 20, "%.1fM" % (v / 1e6), 12, fill=c, weight="bold")
        b += txt(x + wdt / 2, Y + 36, "%.1f%%" % (100 * v / total), 10, fill=c)
    x += wdt
y = 160
for n, v, c in parts:
    b += box(40, y - 11, 12, 12, {FWD: FWD_SOFT, REV: REV_SOFT, INK2: NODE}[c], c, 1, 2)
    b += txt(60, y, n, 12, fill=INK, anchor="start")
    b += txt(470, y, "{:,}".format(v), 12, fill=INK, anchor="end")
    y += 24
b += line(40, y - 8, 470, y - 8, INK2, 1)
b += txt(60, y + 10, "합계", 12, fill=INK, anchor="start", weight="bold")
b += txt(470, y + 10, "{:,}".format(total), 12, fill=INK, anchor="end", weight="bold")
b += lines_at(500, 160, [
    ("LSTM 한 층 = 문 넷 x (입력 1,000 + 되먹임 1,000) x 1,000", INK2),
    ("              + 치우침 4 x 1,000 = 8,004,000", INK2),
    ("4층 = 32,016,000 — 원문 「인코더 32M, 디코더 32M」 과 같다", OK, "bold"),
    ("원문의 「순수 되먹임 연결 64M」 은 h -> h 만이 아니라", INK2),
    ("입력 -> 문 무게까지 넣은 LSTM 전체다(h -> h 만이면 16M)", INK2),
    ("Graves 꼴의 엿보기 연결(층마다 3,000)을 넣어도 +24,000 (8층)", MUTED),
    ("번역 낱말 벡터나 소프트맥스 중 하나를 빼면 304M 이 된다 —", MUTED),
    ("384M 은 둘을 따로 센 값이다", MUTED),
], 11, 20)
svg("fig03_param_count", W, H, b, "파라미터 다시 세기")

# ── 그림 4. 학습률 일정 — 두 읽기 ─────────────────────────────────────────────
def lr_at(ep, first_halving):
    if ep < first_halving:
        return 0.7
    k = int((ep - first_halving) / 0.5 + 1e-9) + 1
    return 0.7 / 2 ** k


steps_per_epoch = SENT / BATCH
print("  [그림 4] 한 바퀴 갱신 %.0f 번, 7.5 바퀴 %.0f 번" % (steps_per_epoch, steps_per_epoch * EPOCHS))
for fh in (5.0, 5.5):
    print("  [그림 4] 첫 반감 %.1f 바퀴 -> 마지막 학습률 %.5f" % (fh, lr_at(7.49, fh)))
W, H = 900, 380
b = defs()
b += txt(20, 30, "학습률 일정 — 「5 바퀴 뒤부터 반 바퀴마다 반으로」 의 두 읽기. 마지막 값이 0.0219 또는 0.0438 로 두 배 갈린다", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 560, 70, 300
fx = lambda e: X0 + e / 7.5 * (X1 - X0)
fy = lambda v: Y1 - v / 0.8 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [0, 1, 2, 3, 4, 5, 6, 7, 7.5], [0, 0.2, 0.4, 0.6, 0.8], fx, fy, "바퀴(epoch)", "학습률")
for fh, c, lab in ((5.0, FWD, "읽기 가: 5.0 에서 첫 반감"), (5.5, REV, "읽기 나: 5.5 에서 첫 반감")):
    pts = []
    e = 0.0
    while e <= 7.5 + 1e-9:
        pts.append((fx(e), fy(lr_at(min(e, 7.4999), fh))))
        e += 0.01
    b += polyline(pts, c, 2, dash=None if fh == 5.0 else "5 3")
b += lines_at(590, 90, [
    ("읽기 가 — 5.0 · 5.5 · 6.0 · 6.5 · 7.0 에서 반감,", FWD, "bold"),
    ("다섯 번, 마지막 0.7 / 32 = 0.0219", FWD),
    ("읽기 나 — 5.5 · 6.0 · 6.5 · 7.0 에서 반감,", REV, "bold"),
    ("네 번, 마지막 0.7 / 16 = 0.0438", REV),
    ("", INK2),
    ("갱신 수(내가 센 것): 12,000,000 / 128", INK2),
    ("= 한 바퀴 93,750 번, 7.5 바퀴 703,125 번", INK2),
    ("첫 5 바퀴(468,750 번)는 학습률 0.7 고정", INK2),
    ("", INK2),
    ("모멘텀 없음 · 기울기 노름 5 에서 자름", MUTED),
    ("검증셋으로 일정을 골랐다는 말은 본문에 없다", MUTED),
], 11, 20)
svg("fig04_lr_schedule", W, H, b, "학습률 일정")

# ── 그림 5. 「열흘 남짓」 을 처리 속도로 다시 세기 ──────────────────────────────────
words_epoch = FR_WORDS + EN_WORDS
words_total = words_epoch * EPOCHS
days8 = words_total / WPS_8GPU / 86400
days1 = words_total / WPS_1GPU / 86400
print("  [그림 5] 한 바퀴 낱말 %d, 7.5 바퀴 %d, 8 GPU %.2f 일, 1 GPU %.1f 일, 속도비 %.2f 배, GPU 당 효율 %.0f%%"
      % (words_epoch, words_total, days8, days1, WPS_8GPU / WPS_1GPU, 100 * WPS_8GPU / WPS_1GPU / 8))
W, H = 900, 330
b = defs()
b += txt(20, 30, "학습 시간 다시 세기 — (3억 4,800만 + 3억 400만) 낱말 x 7.5 바퀴 / 초당 6,300 낱말 = 8.98 일. 원문 「열흘 남짓(about a ten days)」", 14, anchor="start", weight="bold")
X0, X1 = 320, 820
fx = lambda d: X0 + d / 36 * (X1 - X0)
rows = [("GPU 8 장 (층마다 GPU 하나 + 소프트맥스 넷)", days8, FWD), ("GPU 1 장 (같은 속도로 셈)", days1, REV)]
for k, (n, d, c) in enumerate(rows):
    y = 80 + k * 60
    b += txt(X0 - 10, y + 20, n, 11, fill=INK, anchor="end")
    b += box(X0, y, fx(d) - X0, 30, {FWD: FWD_SOFT, REV: REV_SOFT}[c], c, 1.2, 3)
    b += txt(fx(d) + 8, y + 20, "%.2f 일" % d, 12, fill=c, anchor="start", weight="bold")
b += line(fx(10), 70, fx(10), 200, OK, 1.4, dash="4 3")
b += txt(fx(10), 215, "원문의 열흘", 11, fill=OK)
for t in (0, 10, 20, 30):
    b += txt(fx(t), 240, "%d 일" % t, 10, fill=MUTED)
b += lines_at(20, 270, [
    ("속도는 원문 3.5절: 단일 GPU 초당 1,700 낱말, 8 GPU 초당 6,300 낱말(영어와 프랑스어를 함께 셈). 8 장으로 3.71 배, GPU 한 장당 46% (내가 센 것).", INK2),
    ("앙상블 다섯은 학습 시간이 적혀 있지 않다. 같은 설정이라고 두면 8 GPU 기계로 44.9 일 몫이다(8.98 x 5, 내가 센 것 — 원문은 이 값을 적지 않는다).", MUTED),
], 11, 22)
svg("fig05_training_time", W, H, b, "학습 시간 다시 세기")

# ── 그림 6. 표 1 ────────────────────────────────────────────────────────────
COLS = {"single": (FWD, FWD_SOFT), "ens": (PURP, PURP_SOFT), "smt": (REV, REV_SOFT), "other": (INK2, NODE)}
W, H = 900, 420
b = defs()
b += txt(20, 30, "표 1 (직접 번역, ntst14) — 기준 SMT 33.30 을 넘는 줄은 앙상블 다섯뿐이다. 단일 모델 최고는 30.59", 14, anchor="start", weight="bold")
X0, X1 = 260, 760
fx = lambda v: X0 + (v - 20) / 20 * (X1 - X0)
for t in (20, 25, 30, 35, 40):
    b += line(fx(t), 56, fx(t), 56 + 8 * 34, LINE, 0.8, dash="2 3")
    b += txt(fx(t), 56 + 8 * 34 + 16, "%d" % t, 10, fill=MUTED)
b += line(fx(33.30), 52, fx(33.30), 56 + 8 * 34, REV, 1.4, dash="5 3")
for k, (n, v, kind) in enumerate(T1):
    y = 60 + k * 34
    c, cs = COLS[kind]
    b += txt(X0 - 10, y + 17, n, 11, fill=INK, anchor="end")
    b += box(X0, y, fx(v) - X0, 22, cs, c, 1.1, 2)
    b += txt(fx(v) + 6, y + 16, "%.2f" % v, 11, fill=c, anchor="start", weight="bold")
b += lines_at(20, 362, [
    ("파랑 단일 모델 · 보라 앙상블(시작값과 미니배치 순서만 다른 모델) · 주황 기준 SMT · 회색 다른 논문의 값. 막대는 20 에서 시작한다.", INK2),
    ("Bahdanau 외 28.45 는 이 표에서 학습 데이터 · 어휘 · 모델 크기가 적혀 있지 않은 값이다 — 같은 조건의 비교가 아니다.", MUTED),
], 11, 22)
svg("fig06_table1", W, H, b, "표 1 막대")

# ── 그림 7. 표 1 의 차이를 단계로 ───────────────────────────────────────────────
steps = [("단일 정방향 빔 12", 26.17), ("뒤집기", 30.59), ("앙상블 2", 33.27), ("앙상블 5", 34.81)]
print("  [그림 7] 뒤집기 +%.2f, 앙상블 1->2 +%.2f, 2->5 +%.2f, 합 +%.2f"
      % (30.59 - 26.17, 33.27 - 30.59, 34.81 - 33.27, 34.81 - 26.17))
print("  [그림 7] 앙상블 5 에서 빔 1->2 +%.2f, 2->12 +%.2f, 빔 2 몫 %.1f%%"
      % (34.50 - 33.00, 34.81 - 34.50, 100 * (34.50 - 33.00) / (34.81 - 33.00)))
print("  [그림 7] 비용(모델 수 x 빔): 앙상블5 빔2 = %d, 단일 빔12 = %d" % (5 * 2, 1 * 12))
W, H = 900, 400
b = defs()
b += txt(20, 30, "표 1 을 단계로 — 26.17 에서 34.81 까지 +8.64 가운데 뒤집기 +4.42, 앙상블 +4.22. 빔 효과는 앙상블 5 에서만 쟀다", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 70, 520, 60, 300
fy = lambda v: Y1 - (v - 24) / 12 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [], [24, 26, 28, 30, 32, 34, 36], (lambda t: 0), fy, None, "BLEU")
prev = None
for k, (n, v) in enumerate(steps):
    x = X0 + 20 + k * 110
    if prev is None:
        b += box(x, fy(v), 70, Y1 - fy(v), FWD_SOFT, FWD, 1.1, 0)
    else:
        b += box(x, fy(v), 70, fy(prev) - fy(v), OK_SOFT if k == 1 else PURP_SOFT, OK if k == 1 else PURP, 1.1, 0)
        b += txt(x + 35, fy(v) + (fy(prev) - fy(v)) / 2 + 4, "+%.2f" % (v - prev), 12, fill=OK if k == 1 else PURP, weight="bold")
        b += line(x - 40, fy(prev), x, fy(prev), MUTED, 0.8, dash="2 2")
    b += txt(x + 35, fy(v) - 6, "%.2f" % v, 11, fill=INK)
    b += txt(x + 35, Y1 + 18, n, 11, fill=INK2)
    prev = v
b += line(X0, fy(33.30), X1, fy(33.30), REV, 1.2, dash="5 3")
b += txt(X0 + 6, fy(33.30) - 5, "기준 SMT 33.30", 10, fill=REV, anchor="start")
b += lines_at(560, 70, [
    ("빔 크기 (앙상블 5 · 뒤집음에서만)", INK, "bold"),
    ("빔 1  33.00", INK2),
    ("빔 2  34.50  (+1.50)", INK2),
    ("빔 12 34.81  (+0.31)", INK2),
    ("빔 1 -> 12 의 +1.81 가운데 빔 2 가 82.9%", OK, "bold"),
    ("", INK2),
    ("원문 「빔 1 에서도 잘한다」 는 앙상블 5 의 값", INK2),
    ("33.00 이다. 단일 모델의 빔 1 값은 표에 없다", INK2),
    ("", INK2),
    ("캡션 「앙상블 5 빔 2 가 단일 빔 12 보다 싸다」:", INK2),
    ("모델 x 빔 = 10 대 12 로 맞다(내가 센 것)", INK2),
    ("", INK2),
    ("모든 값이 실행 하나다. 흩어짐이 없다", NO, "bold"),
], 11, 20)
svg("fig07_table1_steps", W, H, b, "표 1 차이 분해")

# ── 그림 8. 표 2 ────────────────────────────────────────────────────────────
print("  [그림 8] 다시 매김 이득: 정방향 +%.2f, 뒤집음 +%.2f, 앙상블 +%.2f; 정방향-뒤집음 차이 %.2f (직접 번역에서는 %.2f)"
      % (35.61 - 33.30, 35.85 - 33.30, 36.5 - 33.30, 35.85 - 35.61, 30.59 - 26.17))
W, H = 900, 420
b = defs()
b += txt(20, 30, "표 2 (SMT 의 1000 후보를 다시 매김) — 뒤집기의 몫이 직접 번역에서 +4.42, 다시 매김에서 +0.24", 14, anchor="start", weight="bold")
X0, X1 = 260, 760
fx = lambda v: X0 + (v - 30) / 16 * (X1 - X0)
for t in (30, 34, 38, 42, 46):
    b += line(fx(t), 56, fx(t), 56 + 7 * 34, LINE, 0.8, dash="2 3")
    b += txt(fx(t), 56 + 7 * 34 + 16, "%d" % t, 10, fill=MUTED)
b += line(fx(33.30), 52, fx(33.30), 56 + 7 * 34, REV, 1.4, dash="5 3")
for k, (n, v, kind) in enumerate(T2):
    y = 60 + k * 34
    c, cs = COLS[kind]
    b += txt(X0 - 10, y + 17, n, 11, fill=INK, anchor="end")
    b += box(X0, y, fx(v) - X0, 22, cs, c, 1.1, 2, dash="4 2" if "오라클" in n else None)
    b += txt(fx(v) + 6, y + 16, ("%.2f" % v) if v < 44 else "~45", 11, fill=c, anchor="start", weight="bold")
b += lines_at(20, 330, [
    ("다시 매김 점수 = SMT 점수와 LSTM 로그 확률의 단순 평균(원문 「even average」). 무게를 고르지 않았다.", INK2),
    ("37.0 은 저자들이 같은 스크립트로 다시 낸 값이다(statmt.org 공지 값은 35.8). 같은 시스템의 점수가 셈 방식으로 1.2 갈린다.", INK2),
    ("오라클 ~45 는 1000 후보 안의 가장 좋은 후보를 골랐을 때의 값이다 — 다시 매김이 닿을 수 있는 천장.", MUTED),
], 11, 22)
svg("fig08_table2", W, H, b, "표 2 막대")

# ── 그림 9. 빔 탐색 작은 예 ──────────────────────────────────────────────────
P1 = {"a": 0.5, "b": 0.4, "E": 0.1}
P2 = {"a": {"a": 0.3, "b": 0.3, "E": 0.4}, "b": {"a": 0.05, "b": 0.05, "E": 0.9}}
greedy = ("a", "E", P1["a"] * P2["a"]["E"])
ext = {(x, y): P1[x] * P2[x][y] for x in ("a", "b") for y in ("a", "b", "E")}
best = max(ext.items(), key=lambda kv: kv[1])
print("  [그림 9] 탐욕(빔 1) a,EOS = %.2f / 빔 2 의 확장 %s / 가장 높은 완결 %s = %.2f"
      % (greedy[2], {k: round(v, 3) for k, v in ext.items()}, best[0], best[1]))
W, H = 900, 400
b = defs()
b += txt(20, 30, "빔 탐색 작은 예 (어휘 a · b · EOS) — 빔 1 은 a EOS (0.20), 빔 2 는 b EOS (0.36) 를 찾는다", 14, anchor="start", weight="bold")
root = (80, 200)
b += circ(root[0], root[1], 16, NODE, INK2)
b += txt(root[0], root[1] + 4, "시작", 10, fill=INK2)
lv1 = {"a": 120, "b": 250, "E": 340}
for w, y in lv1.items():
    kept = w in ("a", "b")
    c = FWD if kept else MUTED
    b += line(root[0] + 16, root[1], 240, y, c, 1.2)
    b += box(240, y - 16, 90, 32, FWD_SOFT if kept else NODE, c, 1.2, 5)
    b += txt(285, y + 4, "%s  %.2f" % ("EOS" if w == "E" else w, P1[w]), 12, fill=c, weight="bold" if kept else None)
b += txt(285, 72, "1 걸음 — 빔 2 는 a · b 를 남긴다", 11, fill=FWD)
lv2y = {("a", "a"): 70, ("a", "b"): 110, ("a", "E"): 150, ("b", "a"): 220, ("b", "b"): 260, ("b", "E"): 300}
top2 = sorted(ext.items(), key=lambda kv: -kv[1])[:2]
for (x1, y1w), y in lv2y.items():
    v = ext[(x1, y1w)]
    win = (x1, y1w) in [k for k, _ in top2]
    c = OK if win else MUTED
    b += line(330, lv1[x1], 470, y, c, 1.0)
    b += box(470, y - 14, 150, 28, OK_SOFT if win else NODE, c, 1.1, 5)
    lab = "%s %s" % (x1, "EOS" if y1w == "E" else y1w)
    b += txt(545, y + 5, "%s  %.2f x %.2f = %.2f" % (lab, P1[x1], P2[x1][y1w], v), 11, fill=c, weight="bold" if win else None)
b += lines_at(650, 80, [
    ("2 걸음 — 확장 여섯 가운데 위 둘", OK, "bold"),
    ("b EOS 0.36, a EOS 0.20 이 남고", INK2),
    ("둘 다 EOS 로 끝나 완결 후보가 된다", INK2),
    ("가장 높은 완결: b EOS 0.36", OK, "bold"),
    ("", INK2),
    ("빔 1(탐욕)은 1 걸음에 a 를 고르고", INK2),
    ("a 다음에서 가장 높은 EOS(0.4)를 골라", INK2),
    ("a EOS 0.20 에서 멈춘다", NO),
    ("", INK2),
    ("원문 크기로는 한 걸음에 빔 12 x 어휘", MUTED),
    ("80,000 = 960,000 개 확장을 매긴다", MUTED),
], 11, 20)
svg("fig09_beam_search", W, H, b, "빔 탐색 예")


# ── 그림 10 · 11. 원문 그림 3 을 벡터 좌표에서 옮겨 그리기 ─────────────────────────────
def f3_values(raw):
    return [(f3_index(x), f3_bleu(y)) for x, y in raw]


L_lstm, L_smt = f3_values(RAW_F3L_LSTM), f3_values(RAW_F3L_SMT)
R_lstm, R_smt = f3_values(RAW_F3R_LSTM), f3_values(RAW_F3R_SMT)


def extrap_first(raw, x_target):
    (x0, y0), (x1, y1) = raw[0], raw[1]
    yt = y1 + (y0 - y1) * (x_target - x1) / (x0 - x1)
    return f3_bleu(yt)


lstm_first = extrap_first(RAW_F3L_LSTM, F3L_TICKX[0])
smt_first = extrap_first(RAW_F3L_SMT, F3L_TICKX[0])
print("  [그림 10] 왼쪽 칸 점의 x 를 오른쪽 칸 눈금으로 읽은 자리:", [round((x - F3L_X0) / ((F3R_X3500 - F3R_X0) / 3500)) for x in F3L_TICKX])
print("  [그림 10] 첫 점(길이 4)은 축 밖 — 잘린 선분을 늘려 읽으면 LSTM %.1f, SMT %.1f" % (lstm_first, smt_first))
for lab, (_, a), (_, c) in zip(F3L_LABELS[1:], L_lstm[1:], L_smt[1:]):
    print("  [그림 10] 길이 %2d  LSTM %.2f  SMT %.2f  차 %+.2f" % (lab, a, c, a - c))
for (i, a), (_, c) in zip(R_lstm, R_smt):
    print("  [그림 11] 순위 자리 %4.0f  LSTM %.2f  SMT %.2f  차 %+.2f" % (i, a, c, a - c))

W, H = 900, 450
b = defs()
b += txt(20, 30, "원문 그림 3 왼쪽 — 문장 길이별 BLEU. 가장 긴 칸(35 ~ 79 낱말)에서 LSTM 앙상블이 2.16 내려가 SMT 와의 차이가 +0.14 로 준다", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 560, 60, 330
idx = [10, 100, 200, 500, 1000, 1500, 2000, 2500, 3000]
fxi = lambda k: X0 + k / 8 * (X1 - X0)
fy = lambda v: Y1 - (v - 20) / 20 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [], [20, 25, 30, 35, 40], fxi, fy, None, "BLEU")
for k, lab in enumerate(F3L_LABELS):
    b += txt(fxi(k), Y1 + 17, str(lab), 10, fill=MUTED)
b += txt((X0 + X1) / 2, Y1 + 36, "길이 순으로 놓은 시험 문장 — 눈금 글자는 그 자리 문장의 낱말 수(원문 그대로, 칸 사이를 같게 폈다)", 10, fill=INK2)
b += polyline([(fxi(k), fy(v)) for k, (_, v) in enumerate(L_lstm) if k > 0], FWD, 2)
b += polyline([(fxi(k), fy(v)) for k, (_, v) in enumerate(L_smt) if k > 0], REV, 2, dash="5 3")
for k in range(1, 9):
    b += circ(fxi(k), fy(L_lstm[k][1]), 3, FWD, FWD)
    b += circ(fxi(k), fy(L_smt[k][1]), 3, REV, REV)
b += txt(fxi(0) + 4, Y1 - 30, "길이 4 칸: 축 밖", 10, fill=MUTED, anchor="start")
b += txt(fxi(0) + 4, Y1 - 16, "(늘려 읽으면 0.1 · 0.0)", 10, fill=MUTED, anchor="start")
b += txt(fxi(8) + 6, fy(L_lstm[8][1]) - 10, "%.2f" % L_lstm[8][1], 11, fill=FWD, anchor="start", weight="bold")
b += txt(fxi(8) + 6, fy(L_smt[8][1]) + 14, "%.2f" % L_smt[8][1], 11, fill=REV, anchor="start", weight="bold")
b += txt(fxi(7), fy(L_lstm[7][1]) - 10, "%.2f" % L_lstm[7][1], 11, fill=FWD, weight="bold")
b += txt(fxi(7), fy(L_smt[7][1]) + 18, "%.2f" % L_smt[7][1], 11, fill=REV, weight="bold")
b += table_cols(600, 70, ["길이", "LSTM", "SMT", "차"],
                [(str(F3L_LABELS[k]), "%.2f" % L_lstm[k][1], "%.2f" % L_smt[k][1], "%+.2f" % (L_lstm[k][1] - L_smt[k][1]), INK2) for k in range(1, 9)])
b += lines_at(600, 270, [
    ("LSTM = 앙상블 5 (범례 34.8). 정방향 모델의", MUTED),
    ("곡선은 이 그림에 없다", MUTED),
], 11, 18)
b += lines_at(20, 392, [
    ("값은 원문 PDF 안 벡터 선의 꼭짓점 좌표를 눈금으로 바꾼 것이다(내가 읽은 것, 눈금 기준 오차 0.02 BLEU 안). 칸마다 문장이 몇 개인지와 칸을 어떻게 나눴는지는 원문에 없다.", INK2),
    ("가장 짧은 칸은 두 곡선 모두 축 아래로 나가 원문에서 읽히지 않는다. 잘린 선분을 같은 직선으로 늘리면 LSTM 0.1 · SMT 0.0 이다.", MUTED),
], 10.5, 20)
svg("fig10_fig3_length", W, H, b, "원문 그림 3 왼쪽 옮김")

W, H = 900, 450
b = defs()
b += txt(20, 30, "원문 그림 3 오른쪽 — 드문 낱말이 많은 쪽 끝 칸에서 LSTM 앙상블(28.82)이 SMT(30.10)보다 1.28 낮다", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 560, 60, 330
fx = lambda i: X0 + i / 3500 * (X1 - X0)
b += axes(X0, Y0, X1, Y1, [0, 500, 1000, 1500, 2000, 2500, 3000, 3500], [20, 25, 30, 35, 40, 45], fx,
          lambda v: Y1 - (v - 20) / 25 * (Y1 - Y0), "낱말 빈도 순위의 평균으로 놓은 시험 문장 (오른쪽일수록 드문 낱말이 많다)", "BLEU")
fy = lambda v: Y1 - (v - 20) / 25 * (Y1 - Y0)
b += polyline([(fx(i), fy(v)) for i, v in R_lstm], FWD, 2)
b += polyline([(fx(i), fy(v)) for i, v in R_smt], REV, 2, dash="5 3")
for (i, v), (_, w) in zip(R_lstm, R_smt):
    b += circ(fx(i), fy(v), 3, FWD, FWD)
    b += circ(fx(i), fy(w), 3, REV, REV)
b += table_cols(600, 70, ["자리", "LSTM", "SMT", "차"],
                [("%.0f" % i, "%.2f" % v, "%.2f" % w, "%+.2f" % (v - w), NO if v < w else INK2) for (i, v), (_, w) in zip(R_lstm, R_smt)])
b += lines_at(20, 392, [
    ("LSTM 이 SMT 아래인 칸 둘(빨강): 맨 앞 자리 10 과 맨 끝 자리 3003. 원문 캡션은 그림만 풀이하고 이 두 칸을 말하지 않는다.", INK2),
    ("점의 x 자리 10 · 100 · 200 · 500 · 1000 ... 2500 · 3003 은 왼쪽 칸 점의 x 자리와 같다(PDF 좌표가 소수 둘째 자리까지 같다, 내가 읽은 것).", MUTED),
], 10.5, 20)
svg("fig11_fig3_rarity", W, H, b, "원문 그림 3 오른쪽 옮김")

# ── 그림 12. 원문 그림 2 를 같은 눈금으로 ──────────────────────────────────────
F2L = f2_conv(RAW_F2L, (-8, 142.48), (10, 283.59), (-6, 621.43), (4, 515.37))
F2R = f2_conv(RAW_F2R, (-15, 334.72), (20, 475.83), (-20, 621.43), (15, 510.09))


def dists(pts):
    within, between = [], []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = math.hypot(pts[i][1] - pts[j][1], pts[i][2] - pts[j][2])
            (within if pts[i][3] == pts[j][3] else between).append(d)
    return within, between


for nm, pts in (("왼쪽", F2L), ("오른쪽", F2R)):
    for p in pts:
        print("  [그림 12] %s %-42s (%6.2f, %6.2f) %s" % (nm, p[0], p[1], p[2], p[3]))
    wi, be = dists(pts)
    print("  [그림 12] %s 같은 뜻 쌍 거리 최대 %.2f / 다른 뜻 쌍 거리 최소 %.2f" % (nm, max(wi), min(be)))
W, H = 900, 470
b = defs()
b += txt(20, 30, "원문 그림 2 를 같은 눈금으로 — 오른쪽 칸은 같은 뜻끼리 거리(최대 19.0)가 다른 뜻 사이 거리(최소 14.6)보다 크다", 14, anchor="start", weight="bold")


def pca_panel(x0, y0, w, h, pts, xr, yr, title, groups):
    s = txt(x0, y0 - 12, title, 12, fill=INK, anchor="start", weight="bold")
    sc = min(w / (xr[1] - xr[0]), h / (yr[1] - yr[0]))
    fx = lambda v: x0 + (v - xr[0]) * sc
    fy = lambda v: y0 + h - (v - yr[0]) * sc
    s += box(x0, y0, (xr[1] - xr[0]) * sc, (yr[1] - yr[0]) * sc, NODE, LINE, 1, 0)
    for t in range(int(xr[0]), int(xr[1]) + 1, 5):
        s += txt(fx(t), y0 + (yr[1] - yr[0]) * sc + 14, str(t), 9, fill=MUTED)
    for t in range(int(yr[0]), int(yr[1]) + 1, 5):
        s += txt(x0 - 5, fy(t) + 3, str(t), 9, fill=MUTED, anchor="end")
    for name, vx, vy, g in pts:
        c = FWD if g == groups[0] else REV
        s += circ(fx(vx), fy(vy), 4, c, c)
        s += txt(fx(vx) + 6, fy(vy) + 4, name, 9, fill=c, anchor="start")
    return s


b += pca_panel(60, 70, 300, 300, F2L, (-10, 10), (-10, 10), "왼쪽 칸 (축 비 1:1 로 다시 폄)", ("J>M", "M>J"))
b += pca_panel(470, 70, 300, 300, F2R, (-15, 20), (-20, 15), "오른쪽 칸 (축 비 1:1)", ("I>her", "she>me"))
b += lines_at(20, 410, [
    ("파랑 · 주황 = 원문 캡션의 「뜻이 같은」 묶음(누가 누구에게). 좌표는 원문 PDF 안 점의 가운데를 눈금으로 바꾼 것이다(내가 읽은 것).", INK2),
    ("원문 그림은 가로 · 세로 눈금 간격이 달라(왼쪽 칸 가로 1 = 7.84 pt, 세로 1 = 10.61 pt) 눈으로 본 거리가 실제 거리와 다르다. 여기는 1:1 로 폈다.", MUTED),
], 10.5, 20)
svg("fig12_fig2_pca", W, H, b, "원문 그림 2 옮김")

# ── 그림 13. 입력 뒤집기를 두고 한 말의 세기 ─────────────────────────────────────
W, H = 900, 470
b = defs()
b += txt(20, 30, "입력 뒤집기를 두고 한 말 — 잰 것은 단일 모델의 두 수(혼잡도 · BLEU)이고, 「왜」 는 3.3절 스스로 가설이라 적는다", 14, anchor="start", weight="bold")
rows = [
    ("초록 상자", "잰 것", OK, OK_SOFT, [
        "3.3절: 시험 혼잡도 5.8 -> 4.7, 시험 BLEU 25.9 -> 30.6 (단일 모델)",
        "표 1: 단일 빔 12 정방향 26.17 -> 뒤집음 30.59 / 표 2: 다시 매김 35.61 -> 35.85",
    ]),
    ("노랑 상자", "가설이라고 적은 것", CODE, CODE_SOFT, [
        "3.3절: 「완전한 설명은 없지만 ... 짧은 의존이 많아져서라고 믿는다」",
        "3.3절: 「긴 문장에서 훨씬 낫다 (3.7절 참고) — 기억을 더 잘 쓰는 것으로 보인다(suggests)」",
        "5절: 「보통 RNN 도 뒤집으면 쉽게 배워질 것이라 믿는다 (실험으로 확인하지 않았다)」",
    ]),
    ("빨강 상자", "원인으로 적었지만 잰 것이 없는 것", NO, NO_SOFT, [
        "Abstract: 「짧은 의존을 많이 들여왔기 때문에(because) 성능이 크게 나아졌다」",
        "1절: 「긴 문장을 잘한 것은 뒤집었기 때문이다(because)」 — 정방향 모델의 길이별 곡선은 어디에도 없다",
        "5절: 「짧은 의존이 가장 많은 부호화를 찾는 것이 중요하다고 결론짓는다」",
    ]),
]
y = 60
for _, head, c, cs, items in rows:
    hh = 30 + 22 * len(items)
    b += box(20, y, 860, hh, cs, c, 1.3, 6)
    b += txt(36, y + 22, head, 12.5, fill=c, anchor="start", weight="bold")
    for j, it in enumerate(items):
        b += txt(52, y + 46 + 22 * j, it, 11, fill=INK, anchor="start")
    y += hh + 14
b += txt(20, y + 12, "같은 현상(뒤집기 이득)에 대한 말이 Abstract · 1절에서는 원인으로, 3.3절에서는 가설로 적혀 있다. 원인 쪽 문장의 근거는 3.3절의 그 가설이다.", 11, fill=INK2, anchor="start")
svg("fig13_reversal_claims", W, H, b, "뒤집기 주장의 세기")

# ── 그림 14. 계보 ───────────────────────────────────────────────────────────
W, H = 900, 400
b = defs()
b += txt(20, 30, "계보 — 문장 전체를 고정 길이 벡터 하나에 담는 틀. 이 편이 그 틀로 기준 SMT 를 넘었고(앙상블 5), 다음 칸이 그 벡터를 푼다", 14, anchor="start", weight="bold")
nodes = [
    (40, 70, "LSTM", "Hochreiter · Schmidhuber 1997", "긴 지연을 배우는 기억 칸", INK2, NODE),
    (40, 170, "Kalchbrenner · Blunsom", "EMNLP 2013", "문장 -> 벡터 -> 문장 첫 시도 (합성곱 인코더)", INK2, NODE),
    (40, 270, "Cho 외", "EMNLP 2014", "RNN 인코더-디코더, SMT 의 구 점수로", INK2, NODE),
    (330, 170, "이 편", "Sutskever · Vinyals · Le 2014", "깊은 LSTM 둘 · 뒤집기 · 직접 번역", FWD, FWD_SOFT),
    (630, 120, "Bahdanau 외", "ICLR 2015", "벡터 하나 대신 원문 자리마다 무게", OK, OK_SOFT),
    (630, 240, "Pouget-Abadie 외", "2014", "긴 문장을 조각내 번역", INK2, NODE),
]
for x, y, t1, t2, t3, c, cs in nodes:
    b += box(x, y, 250, 72, cs, c, 1.3, 6)
    b += txt(x + 12, y + 22, t1, 13, fill=c, anchor="start", weight="bold")
    b += txt(x + 12, y + 42, t2, 10.5, fill=MUTED, anchor="start")
    b += txt(x + 12, y + 61, t3, 10.5, fill=INK2, anchor="start")
for (x1, y1), (x2, y2) in (((290, 106), (330, 196)), ((290, 206), (330, 206)), ((290, 306), (330, 216))):
    b += line(x1, y1, x2, y2, INK2, 1.2, marker="ai")
b += line(580, 196, 630, 156, OK, 1.4, marker="ao")
b += line(290, 320, 630, 290, INK2, 1.2, marker="ai", dash="4 3")
b += txt(470, 334, "원문 4절: Cho 외의 「기억 문제」 를 풀려 한 편", 10, fill=MUTED)
b += txt(598, 160, "로드맵 다음 칸", 10, fill=OK, anchor="end")
b += lines_at(20, 362, [
    ("화살표는 원문 2 · 4절의 인용을 따른다. Bahdanau 외는 이 편보다 먼저 arXiv 에 나왔고 이 편 표 1 에 28.45 로 들어 있다 — 「이 편 다음」 은 로드맵의 순서다.", MUTED),
], 10.5, 20)
svg("fig14_lineage", W, H, b, "계보")

print("끝.")
