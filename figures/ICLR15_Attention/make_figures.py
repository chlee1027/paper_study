# -*- coding: utf-8 -*-
"""Attention 노트(Bahdanau · Cho · Bengio, ICLR 2015, arXiv:1409.0473v6)의 그림 열다섯을 만든다.

색과 글꼴은 저장소의 앞선 노트 그림과 맞췄다. 표준 라이브러리만 쓴다.

  python make_figures.py

계산으로 원문을 확인하는 그림이 여럿이다 — 2(맥락 벡터 한 걸음의 작은 예), 4(부록 A.2 의 크기로 파라미터
다시 세기), 5(Tx x Ty 비용의 몫), 6(표 1 의 차), 8 · 9(그림 2 곡선끼리의 차와 남는 몫), 12(그림 3 의 줄),
13(표 2 의 학습 통계에서 바퀴당 문장 수 · 시간당 갱신 수). 계산한 값은 돌릴 때 화면에도 찍는다.

그림 7 · 8 · 9 의 값은 원문 그림 2 의 PDF 벡터 좌표를, 그림 10 · 11 · 12 의 값은 원문 그림 3 의 회색조 이미지
화소 값을 crop_paper_figures.py 가 꺼내 둔 CSV 둘(paper_fig2_curves.csv · paper_fig3_alpha.csv)에서 읽는다.
이 파일은 PDF 를 읽지 않는다.
"""
import io, os, math, csv
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


def heat(a):
    """무게 0 -> 밝은 바탕, 1 -> 짙은 파랑. 원문(0 검정 · 1 흰색)과 밝기가 반대다."""
    c0 = (0xF6, 0xF7, 0xF5)
    c1 = (0x1F, 0x4E, 0x66)
    a = max(0.0, min(1.0, a))
    return "#%02X%02X%02X" % tuple(int(round(c0[k] + (c1[k] - c0[k]) * a)) for k in range(3))


# ── 원문의 수 ───────────────────────────────────────────────────────────────
N, M, L, NP = 1000, 620, 500, 1000          # 부록 A.2.3: 은닉 n, 낱말 벡터 m, maxout l, 정렬 모델 n'
K = 30000                                   # 4.1절: 언어마다 가장 잦은 30,000 낱말 (UNK · 끝 기호는 넣지 않고 셈)
BATCH = 80

# 표 1 (원문 7 쪽): (모델, 전체, UNK 없는 문장)
T1 = [("RNNencdec-30", 13.93, 24.19), ("RNNsearch-30", 21.50, 31.44),
      ("RNNencdec-50", 17.82, 26.71), ("RNNsearch-50", 26.75, 34.16),
      ("RNNsearch-50*", 28.45, 36.15), ("Moses", 33.30, 35.63)]
# 표 2 (원문 14 쪽): (모델, 갱신 x1e5, 바퀴, 시간, GPU, 학습 NLL, 개발 NLL)
T2 = [("RNNencdec-30", 8.46, 6.4, 109, "TITAN BLACK", 28.1, 53.0),
      ("RNNencdec-50", 6.00, 4.5, 108, "Quadro K-6000", 44.0, 43.6),
      ("RNNsearch-30", 4.71, 3.6, 113, "TITAN BLACK", 26.7, 47.2),
      ("RNNsearch-50", 2.88, 2.2, 111, "Quadro K-6000", 40.7, 38.1),
      ("RNNsearch-50*", 6.67, 5.0, 252, "Quadro K-6000", 36.7, 35.2)]

# ── CSV 둘 읽기 ─────────────────────────────────────────────────────────────
CURVES = {}
with io.open(os.path.join(OUT, "paper_fig2_curves.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        CURVES.setdefault(r["model"], []).append((float(r["x_tick"]), float(r["bleu"])))
ALPHA = {}
with io.open(os.path.join(OUT, "paper_fig3_alpha.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        p = ALPHA.setdefault(r["panel"], {"src": {}, "tgt": {}, "a": {}})
        i, j = int(r["i_target"]), int(r["j_source"])
        p["src"][j] = r["source_word"]
        p["tgt"][i] = r["target_word"]
        p["a"][(i, j)] = float(r["alpha"])
for k, p in ALPHA.items():
    p["S"] = [p["src"][j] for j in range(len(p["src"]))]
    p["T"] = [p["tgt"][i] for i in range(len(p["tgt"]))]
    p["M"] = [[p["a"][(i, j)] for j in range(len(p["S"]))] for i in range(len(p["T"]))]

# ── 그림 1. 고정 길이 벡터 하나 대 낱말마다 맥락 벡터 ──────────────────────────────
W, H = 940, 470
b = defs()
b += txt(20, 30, "고정 길이 벡터 하나(RNNencdec) 대 번역 낱말마다 다른 맥락 벡터(RNNsearch)", 15, anchor="start", weight="bold")
# 왼쪽
b += txt(230, 62, "RNNencdec — 인코더 끝 상태 하나를 디코더가 매 걸음 받는다", 12, fill=INK2)
xs = [60, 130, 200, 270]
for k, x in enumerate(xs):
    b += box(x, 300, 52, 36, FWD_SOFT, FWD) + txt(x + 26, 323, "h%d" % (k + 1) if k < 3 else "hT", 12, fill=FWD)
    b += txt(x + 26, 365, "x%d" % (k + 1) if k < 3 else "xT", 12, fill=INK2)
    if k:
        b += line(xs[k - 1] + 52, 318, x, 318, FWD, 1.2, marker="af")
b += box(340, 220, 60, 36, CODE_SOFT, CODE) + txt(370, 243, "c", 14, fill=CODE, weight="bold")
b += path("M322,318 C350,318 365,290 370,258", CODE, sw=1.5, marker="ac")
for k, x in enumerate([60, 150, 240, 330]):
    b += box(x, 120, 56, 36, REV_SOFT, REV) + txt(x + 28, 143, "s%d" % (k + 1), 12, fill=REV)
    b += txt(x + 28, 104, "y%d" % (k + 1), 12, fill=INK2)
    b += line(370, 220, x + 28, 158, CODE, 1.0, marker="ac", op=0.8)
    if k:
        b += line(x - 34, 138, x, 138, REV, 1.2, marker="ar")
b += lines_at(40, 400, [("원문 길이가 5 낱말이든 50 낱말이든 c 는 같은 크기", INK2),
                       ("(이 편의 RNNencdec 은 1,000 개의 수, 부록 A.2.2 끝 문장)", MUTED)], 11.5, 19)
# 오른쪽
ox = 480
b += line(ox - 10, 50, ox - 10, 440, LINE, 1)
b += txt(ox + 225, 62, "RNNsearch — 걸음 i 마다 주석 h1..hT 의 무게 합 ci 를 새로 만든다", 12, fill=INK2)
xs2 = [ox + 30, ox + 110, ox + 190, ox + 270]
for k, x in enumerate(xs2):
    b += box(x, 300, 60, 44, FWD_SOFT, FWD) + txt(x + 30, 319, "h%d" % (k + 1) if k < 3 else "hT", 12, fill=FWD)
    b += txt(x + 30, 336, "앞 · 뒤 이음", 9, fill=MUTED)
    b += txt(x + 30, 365, "x%d" % (k + 1) if k < 3 else "xT", 12, fill=INK2)
b += circ(ox + 190, 230, 14, CODE_SOFT, CODE) + txt(ox + 190, 235, "+", 15, fill=CODE, weight="bold")
for k, x in enumerate(xs2):
    b += line(x + 30, 300, ox + 190, 244, CODE, 1.2, marker="ac")
    b += txt((x + 30 + ox + 190) / 2 - 8, 278 - (k == 2) * 4, "a(i,%s)" % (str(k + 1) if k < 3 else "T"), 11, fill=CODE)
b += txt(ox + 214, 216, "ci", 13, fill=CODE, anchor="start", weight="bold")
b += box(ox + 100, 120, 64, 36, REV_SOFT, REV) + txt(ox + 132, 143, "s(i-1)", 12, fill=REV)
b += box(ox + 230, 120, 56, 36, REV_SOFT, REV) + txt(ox + 258, 143, "si", 12, fill=REV)
b += line(ox + 164, 138, ox + 230, 138, REV, 1.2, marker="ar")
b += path("M%d,216 C%d,190 %d,175 %d,158" % (ox + 190, ox + 195, ox + 235, ox + 250), CODE, sw=1.5, marker="ac")
b += path("M%d,156 C%d,200 %d,230 %d,232" % (ox + 132, ox + 120, ox + 150, ox + 175), INK2, sw=1.0, dash="3 3", marker="ai")
b += txt(ox + 100, 196, "점수 eij 에", 10, fill=MUTED, anchor="end") + txt(ox + 100, 210, "s(i-1) 이 들어간다", 10, fill=MUTED, anchor="end")
b += txt(ox + 258, 104, "yi", 12, fill=INK2)
b += lines_at(ox + 10, 400, [("ci 는 원문 길이 T 만큼의 주석에서 다시 고른다", INK2),
                            ("(주석 하나 2,000 개의 수, 무게 a 는 합이 1)", MUTED)], 11.5, 19)
svg("fig01_encdec_vs_search", W, H, b, "RNNencdec 과 RNNsearch 의 차이")

# ── 그림 2. 맥락 벡터 한 걸음의 작은 예 ────────────────────────────────────────
E_EX = [1.2, 2.5, 0.3]
H_EX = [0.2, 0.9, -0.4]
Z = sum(math.exp(e) for e in E_EX)
A_EX = [math.exp(e) / Z for e in E_EX]
C_EX = sum(a * h for a, h in zip(A_EX, H_EX))
print("  [작은 예] e =", E_EX, "-> alpha =", ["%.3f" % a for a in A_EX], " c =", "%.3f" % C_EX)
W, H = 900, 350
b = defs()
b += txt(20, 30, "한 걸음의 셈 — 점수 e -> 소프트맥스 -> 무게 alpha -> 주석의 무게 합 c (원문 식 5 · 6, 수는 내가 고른 것)", 14, anchor="start", weight="bold")
cols = [("원문 자리 j", ["1", "2", "3"]),
        ("점수 eij = a(s(i-1), hj)", ["%.1f" % e for e in E_EX]),
        ("exp(eij)", ["%.3f" % math.exp(e) for e in E_EX]),
        ("alpha ij = exp / 합", ["%.3f" % a for a in A_EX]),
        ("주석 hj (한 칸만)", ["%+.1f" % h for h in H_EX]),
        ("alpha ij x hj", ["%+.3f" % (a * h) for a, h in zip(A_EX, H_EX)])]
for k, (hd, vals) in enumerate(cols):
    x = 30 + k * 145
    b += txt(x + 60, 72, hd, 11, fill=INK, weight="bold")
    for r, v in enumerate(vals):
        fill = CODE_SOFT if k == 3 else NODE
        b += box(x + 15, 88 + r * 44, 90, 32, fill, LINE, 1) + txt(x + 60, 109 + r * 44, v, 12.5, fill=INK2)
b += txt(30 + 2 * 145 + 60, 236, "합 %.3f" % Z, 11, fill=MUTED)
b += txt(30 + 3 * 145 + 60, 236, "합 %.3f" % sum(A_EX), 11, fill=CODE)
b += txt(30 + 5 * 145 + 60, 236, "c = %+.3f" % C_EX, 12.5, fill=CODE, weight="bold")
b += lines_at(30, 270, [("점수가 가장 큰 자리 2 가 무게 %.3f 를 받는다. 점수 차 1.3 이 무게 비 %.2f 배가 된다(exp(1.3))." % (A_EX[1], A_EX[1] / A_EX[0]), INK2),
                       ("무게는 모든 자리에 0 보다 크게 남는다 — 원문이 「부드러운(soft) 정렬」 이라 부르는 까닭.", INK2),
                       ("실제 모델의 주석은 2,000 개의 수이고 c 도 2,000 개다. 무게 alpha 는 같은 값을 2,000 칸 모두에 곱한다.", MUTED)], 11, 21)
svg("fig02_attention_step", W, H, b, "맥락 벡터 한 걸음의 작은 예")

# ── 그림 3. 양방향 RNN 으로 만드는 주석 ──────────────────────────────────────
W, H = 900, 330
b = defs()
b += txt(20, 30, "주석 hj — 앞에서 읽은 상태와 뒤에서 읽은 상태를 잇는다 (원문 3.2절 · 식 7)", 15, anchor="start", weight="bold")
words = ["The", "agreement", "on", "the", "European"]
for k, w_ in enumerate(words):
    x = 60 + k * 160
    b += box(x, 90, 90, 34, FWD_SOFT, FWD) + txt(x + 45, 112, "앞 h%d" % (k + 1), 11.5, fill=FWD)
    b += box(x, 140, 90, 34, PURP_SOFT, PURP) + txt(x + 45, 162, "뒤 h%d" % (k + 1), 11.5, fill=PURP)
    b += txt(x + 45, 205, w_, 12, fill=INK2)
    b += box(x + 10, 230, 70, 30, CODE_SOFT, CODE) + txt(x + 45, 250, "h%d" % (k + 1), 12, fill=CODE)
    if k:
        b += line(x - 70, 107, x, 107, FWD, 1.2, marker="af")
        b += line(x, 157, x - 70, 157, PURP, 1.2, marker="ai")
b += lines_at(60, 290, [("앞 상태 1,000 + 뒤 상태 1,000 = 주석 2,000 개의 수. 낱말 벡터 표 E 는 두 방향이 함께 쓰고, 무게 행렬은 따로다(부록 A.2.1).", INK2),
                       ("원문의 주장: 「RNN 은 최근 입력을 더 잘 나타내므로 hj 가 xj 주변에 모인다」 — 이 편 안에서 잰 것은 없다.", MUTED)], 11, 20)
svg("fig03_birnn", W, H, b, "양방향 RNN 주석")

# ── 그림 4. 파라미터 다시 세기 ──────────────────────────────────────────────
def gru(inp, n, ctx):
    return 3 * n * inp + 3 * n * n + 3 * n * ctx

P_SEARCH = [
    ("원문 낱말 표 E (m x Kx)", M * K, "emb"),
    ("앞 RNN (게이트 둘 유닛)", gru(M, N, 0), "rnn"),
    ("뒤 RNN", gru(M, N, 0), "rnn"),
    ("번역 낱말 표 (m x Ky)", M * K, "emb"),
    ("디코더 RNN (C 는 n x 2n)", gru(M, N, 2 * N), "rnn"),
    ("첫 상태 Ws", N * N, "rnn"),
    ("정렬 모델 Wa · Ua · va", NP * N + NP * 2 * N + NP, "att"),
    ("깊은 출력 Uo · Vo · Co", 2 * L * N + 2 * L * M + 2 * L * 2 * N, "out"),
    ("소프트맥스 Wo (Ky x l)", K * L, "emb"),
]
P_ENC = [
    ("원문 낱말 표", M * K, "emb"),
    ("인코더 RNN", gru(M, N, 0), "rnn"),
    ("번역 낱말 표", M * K, "emb"),
    ("디코더 RNN (C 는 n x n, 가정)", gru(M, N, N), "rnn"),
    ("첫 상태 (가정)", N * N, "rnn"),
    ("깊은 출력 (Co 는 2l x n, 가정)", 2 * L * N + 2 * L * M + 2 * L * N, "out"),
    ("소프트맥스", K * L, "emb"),
]
SUM_S = sum(v for _, v, _ in P_SEARCH)
SUM_E = sum(v for _, v, _ in P_ENC)
EMB_S = sum(v for _, v, c in P_SEARCH if c == "emb")
BIAS_S = 3 * N * 3 + N + NP + 2 * L + K
print("  [파라미터] RNNsearch 무게 %s (치우침 더하면 %s), 낱말 표 둘+소프트맥스 %s = %.1f%%" % (
    format(SUM_S, ","), format(SUM_S + BIAS_S, ","), format(EMB_S, ","), 100.0 * EMB_S / SUM_S))
print("  [파라미터] RNNencdec(가정) %s, 차 %s, 비 %.3f" % (format(SUM_E, ","), format(SUM_S - SUM_E, ","), SUM_S / SUM_E))
for n_, v, _ in P_SEARCH:
    print("     %-26s %s" % (n_, format(v, ",")))
W, H = 920, 440
b = defs()
b += txt(20, 30, "파라미터 다시 세기 — 부록 A.2.3 의 크기(n 1,000 · m 620 · l 500 · n' 1,000)와 어휘 30,000 으로 (내가 센 것)", 14, anchor="start", weight="bold")
colors = {"emb": (MUTED, LINE), "rnn": (FWD, FWD_SOFT), "att": (CODE, CODE_SOFT), "out": (REV, REV_SOFT)}
scale = 660.0 / 82e6
for row, (title, parts, tot) in enumerate([("RNNsearch", P_SEARCH, SUM_S), ("RNNencdec (가정 셋)", P_ENC, SUM_E)]):
    y = 80 + row * 130
    b += txt(20, y + 24, title, 12.5, fill=INK, anchor="start", weight="bold")
    x = 150
    for n_, v, c in parts:
        wdt = v * scale
        b += '<rect x="%.1f" y="%d" width="%.1f" height="36" fill="%s" stroke="%s" stroke-width="0.8"/>' % (x, y, wdt, colors[c][1], colors[c][0])
        if wdt > 50:
            b += txt(x + wdt / 2, y + 22, "%.1fM" % (v / 1e6), 10.5, fill=colors[c][0])
        x += wdt
    b += txt(x + 6, y + 23, "%.2fM" % (tot / 1e6), 12, fill=INK, anchor="start", weight="bold")
legend = [("낱말 표 둘 · 소프트맥스", "emb"), ("RNN · 첫 상태", "rnn"), ("정렬 모델", "att"), ("깊은 출력(maxout)", "out")]
for k, (t, c) in enumerate(legend):
    b += box(150 + k * 180, 300, 14, 14, colors[c][1], colors[c][0], 1, 2) + txt(170 + k * 180, 312, t, 11, fill=INK2, anchor="start")
b += lines_at(20, 345, [("RNNsearch 80.40M 가운데 %.1f%% 가 낱말 표 둘과 소프트맥스다." % (100.0 * EMB_S / SUM_S), INK2),
                       ("RNNencdec 은 원문이 「은닉 1,000」 밖에 적지 않아, 같은 m · l 을 쓰고 c 를 인코더 끝 상태(1,000)로 둔다는 가정으로 셌다.", INK2),
                       ("두 모델의 차 %.2fM (RNNsearch 가 %.1f%% 크다) = 뒤 RNN 4.86M + 정렬 모델 3.00M + 디코더 C 의 늘어난 몫 3.00M + Co 의 늘어난 몫 1.00M." % ((SUM_S - SUM_E) / 1e6, 100.0 * (SUM_S / SUM_E - 1)), MUTED),
                       ("원문은 두 모델의 파라미터 수를 적지 않는다.", MUTED)], 11, 21)
svg("fig04_param_count", W, H, b, "파라미터 다시 세기")

# ── 그림 5. Tx x Ty 비용의 몫 ───────────────────────────────────────────────
LIN_S = 2 * gru(M, N, 0) + NP * 2 * N + gru(M, N, 2 * N) + NP * N + (2 * L * N + 2 * L * M + 2 * L * 2 * N) + K * L
PAIR = NP + 2 * N
LIN_E = gru(M, N, 0) + gru(M, N, N) + (2 * L * N + 2 * L * M + 2 * L * N) + K * L
def share(T):
    return PAIR * T * T / (LIN_S * T + PAIR * T * T)
CROSS = LIN_S / PAIR
print("  [비용] 낱말 걸음당 선형 몫 RNNsearch %.2fM, RNNencdec %.2fM, 짝당 %d. 이차 몫이 선형 몫과 같아지는 T = %.0f" % (LIN_S / 1e6, LIN_E / 1e6, PAIR, CROSS))
for T in (15, 30, 40, 50, 100, 1000):
    print("     T=%5d  이차 몫 %.3f%%   RNNsearch/RNNencdec 곱셈 비 %.3f" % (T, 100 * share(T), (LIN_S * T + PAIR * T * T) / (LIN_E * T)))
W, H = 900, 430
b = defs()
b += txt(20, 30, "Tx x Ty 비용 — 문장 하나를 번역할 때 곱셈-덧셈 가운데 정렬 점수 · 무게 합이 차지하는 몫 (Tx = Ty = T, 내가 센 것)", 14, anchor="start", weight="bold")
x0, y0, x1, y1 = 90, 70, 860, 300
lo, hi = math.log10(10), math.log10(100000)
fx = lambda T: x0 + (math.log10(T) - lo) / (hi - lo) * (x1 - x0)
fy = lambda p: y1 - p / 100.0 * (y1 - y0)
b += axes(x0, y0, x1, y1, [10, 100, 1000, 10000, 100000], [0, 25, 50, 75, 100], fx, fy, "문장 길이 T (낱말, 로그 눈금)", "몫 (%)", xfmt="%g")
pts = [(fx(10 ** (lo + (hi - lo) * k / 200.0)), fy(100 * share(10 ** (lo + (hi - lo) * k / 200.0)))) for k in range(201)]
b += polyline(pts, CODE, 2.2)
for T, lab in ((15, "15"), (40, "40"), (CROSS, "%.0f" % CROSS)):
    b += circ(fx(T), fy(100 * share(T)), 4, CODE_SOFT, CODE)
    b += txt(fx(T) + 8, fy(100 * share(T)) - 8, "T=%s: %.2f%%" % (lab, 100 * share(T)), 10.5, fill=CODE, anchor="start")
b += lines_at(20, 356, [("원문 6.1절의 「번역 문장은 대개 15 ~ 40 낱말이라 이 단점이 심하지 않다」 는 곱셈 수로는 맞다 — T = 40 에서 %.2f%%." % (100 * share(40)), INK2),
                       ("걸음마다의 몫(RNN · 깊은 출력 · 소프트맥스, 낱말 걸음 하나에 %.1fM)이 크기 때문이다." % (LIN_S / 1e6), INK2),
                       ("셈에 넣은 것: 짝마다 v_a 내적 1,000 과 무게 합 2,000. Ua hj 는 문장마다 한 번(원문 A.1.2). 메모리와 병렬화는 넣지 않았다.", MUTED)], 11, 20)
svg("fig05_cost_share", W, H, b, "정렬 비용의 몫")

# ── 그림 6. 표 1 ────────────────────────────────────────────────────────────
W, H = 900, 420
b = defs()
b += txt(20, 30, "표 1 — 시험셋 BLEU. 전체(3,003 문장) 와 UNK 없는 문장 (원문 7 쪽)", 15, anchor="start", weight="bold")
x0, y0, x1, y1 = 70, 60, 860, 300
fy = lambda v: y1 - v / 40.0 * (y1 - y0)
b += axes(x0, y0, x1, y1, [], [0, 10, 20, 30, 40], lambda t: x0, fy, None, "BLEU")
gw = (x1 - x0) / len(T1)
for k, (nm, a, u) in enumerate(T1):
    cx = x0 + gw * (k + 0.5)
    ca, cu = (REV, REV_SOFT) if nm == "Moses" else ((OK, OK_SOFT) if "search" in nm else (FWD, FWD_SOFT))
    b += '<rect x="%.1f" y="%.1f" width="34" height="%.1f" fill="%s" stroke="%s"/>' % (cx - 36, fy(a), y1 - fy(a), cu, ca)
    b += '<rect x="%.1f" y="%.1f" width="34" height="%.1f" fill="%s" stroke="%s" stroke-dasharray="3 2"/>' % (cx + 2, fy(u), y1 - fy(u), NODE, ca)
    b += txt(cx - 19, fy(a) - 5, "%.2f" % a, 10, fill=ca) + txt(cx + 19, fy(u) - 5, "%.2f" % u, 10, fill=ca)
    b += txt(cx, y1 + 18, nm, 11, fill=INK2)
b += line(x0, fy(33.30), x1, fy(33.30), REV, 1, dash="5 4", op=0.7)
b += line(x0, fy(35.63), x1, fy(35.63), REV, 1, dash="1 3", op=0.9)
b += lines_at(20, 344, [("왼쪽 막대 = 전체, 오른쪽(점선 테) = 원문 낱말과 정답 번역에 UNK 가 없는 문장만. 오른쪽 열에서는 모델이 UNK 를 내지 못하게 했다(캡션). 그 문장 수는 적혀 있지 않다.", INK2),
                       ("UNK 없는 열에서 Moses(35.63) 를 넘는 줄은 RNNsearch-50*(36.15, +0.52) 하나다. RNNsearch-50 은 34.16 으로 1.47 아래.", MUTED),
                       ("전체 열에서는 가장 높은 28.45 가 Moses 아래 4.85 다.", MUTED)], 11, 20)
svg("fig06_table1", W, H, b, "표 1")
d = {nm: (a, u) for nm, a, u in T1}
print("  [표 1] search30-enc30 %+.2f / %+.2f, search50-enc50 %+.2f / %+.2f, search30-enc50 %+.2f / %+.2f, search50*-search50 %+.2f / %+.2f, search50*-Moses %+.2f / %+.2f, search50-Moses %+.2f / %+.2f" % (
    d["RNNsearch-30"][0] - d["RNNencdec-30"][0], d["RNNsearch-30"][1] - d["RNNencdec-30"][1],
    d["RNNsearch-50"][0] - d["RNNencdec-50"][0], d["RNNsearch-50"][1] - d["RNNencdec-50"][1],
    d["RNNsearch-30"][0] - d["RNNencdec-50"][0], d["RNNsearch-30"][1] - d["RNNencdec-50"][1],
    d["RNNsearch-50*"][0] - d["RNNsearch-50"][0], d["RNNsearch-50*"][1] - d["RNNsearch-50"][1],
    d["RNNsearch-50*"][0] - d["Moses"][0], d["RNNsearch-50*"][1] - d["Moses"][1],
    d["RNNsearch-50"][0] - d["Moses"][0], d["RNNsearch-50"][1] - d["Moses"][1]))
for nm, a, u in T1:
    print("     %-14s UNK 없는 열 - 전체 열 = %+.2f" % (nm, u - a))

# ── 그림 7. 원문 그림 2 옮겨 그리기 ──────────────────────────────────────────
STY = {"RNNsearch-50": (OK, None, 2.4), "RNNsearch-30": (OK, "2 3", 2.0),
       "RNNencdec-50": (FWD, "7 4", 2.0), "RNNencdec-30": (FWD, "8 3 2 3", 1.8)}
W, H = 900, 450
b = defs()
b += txt(20, 30, "원문 그림 2 — 문장 길이별 시험 BLEU. PDF 안 곡선 꼭짓점 60 개씩을 눈금으로 바꿔 다시 그렸다", 14, anchor="start", weight="bold")
x0, y0, x1, y1 = 70, 60, 700, 330
fx = lambda v: x0 + v / 60.0 * (x1 - x0)
fy = lambda v: y1 - v / 30.0 * (y1 - y0)
b += axes(x0, y0, x1, y1, [0, 10, 20, 30, 40, 50, 60], [0, 5, 10, 15, 20, 25, 30], fx, fy, "원문 가로축 「Sentence length」", "BLEU")
for nm in ["RNNsearch-50", "RNNsearch-30", "RNNencdec-50", "RNNencdec-30"]:
    c, dash, sw = STY[nm]
    b += polyline([(fx(x), fy(v)) for x, v in CURVES[nm]], c, sw, dash)
for k, nm in enumerate(["RNNsearch-50", "RNNsearch-30", "RNNencdec-50", "RNNencdec-30"]):
    c, dash, sw = STY[nm]
    y = 90 + k * 40
    b += line(720, y, 760, y, c, sw, dash=dash) + txt(768, y + 4, nm, 11.5, fill=c, anchor="start")
    v = [p[1] for p in CURVES[nm]]
    b += txt(768, y + 18, "끝 %.2f / 꼭대기 %.2f" % (v[-1], max(v)), 9.5, fill=MUTED, anchor="start")
b += lines_at(20, 392, [("곡선마다 꼭짓점이 가로 0, 1, 2, ..., 59 의 정수 자리에 60 개 있다. 원문은 칸을 어떻게 나눴는지(가로 0 이 무슨 문장인지, 칸마다 문장 몇 개인지) 적지 않는다.", INK2),
                       ("원문 그림의 범례 이름은 RNNenc-50 · RNNenc-30 이다. 표 1 의 RNNencdec 과 같은 모델로 읽었다.", MUTED)], 11, 20)
svg("fig07_fig2_redraw", W, H, b, "원문 그림 2 옮김")

def cv(nm):
    return [p[1] for p in CURVES[nm]]
S50, S30, E50, E30 = cv("RNNsearch-50"), cv("RNNsearch-30"), cv("RNNencdec-50"), cv("RNNencdec-30")
for nm, v in (("RNNsearch-50", S50), ("RNNsearch-30", S30), ("RNNencdec-50", E50), ("RNNencdec-30", E30)):
    pk = max(v)
    print("  [그림 2] %-13s 꼭대기 %.2f (가로 %d), 가로 59 %.2f, 남는 몫 %.3f, 내림 %.2f, 가로 50~59 평균 %.2f" % (
        nm, pk, v.index(pk), v[59], v[59] / pk, pk - v[59], sum(v[50:]) / 10))
for a_, b_, an, bn in ((S50, E50, "S50", "E50"), (S30, E30, "S30", "E30"), (S30, E50, "S30", "E50"), (S50, S30, "S50", "S30")):
    g = [a_[i] - b_[i] for i in range(60)]
    print("  [그림 2] %s-%s 가장 작은 차 %.2f (가로 %d), 가장 큰 차 %.2f (가로 %d), 음수인 가로 %s" % (
        an, bn, min(g), g.index(min(g)), max(g), g.index(max(g)), [i for i in range(60) if g[i] < 0]))

# ── 그림 8. 곡선끼리의 차 ───────────────────────────────────────────────────
W, H = 900, 450
b = defs()
b += txt(20, 30, "그림 2 의 곡선끼리 뺀 값 (내가 센 것) — 0 아래로 내려가는 자리가 있다", 15, anchor="start", weight="bold")
x0, y0, x1, y1 = 70, 60, 700, 330
fx = lambda v: x0 + v / 60.0 * (x1 - x0)
fy = lambda v: y1 - (v + 6) / 32.0 * (y1 - y0)
b += axes(x0, y0, x1, y1, [0, 10, 20, 30, 40, 50, 60], [-5, 0, 5, 10, 15, 20, 25], fx, fy, "원문 가로축", "BLEU 차")
b += line(x0, fy(0), x1, fy(0), INK, 1.2)
pairs = [("search-50 - encdec-50", S50, E50, OK, None), ("search-30 - encdec-30", S30, E30, FWD, "5 3"),
         ("search-30 - encdec-50", S30, E50, PURP, "2 3"), ("search-50 - search-30", S50, S30, REV, "8 3 2 3")]
for k, (nm, a_, b_, c, dash) in enumerate(pairs):
    b += polyline([(fx(i), fy(a_[i] - b_[i])) for i in range(60)], c, 2, dash)
    y = 90 + k * 26
    b += line(715, y, 755, y, c, 2, dash=dash) + txt(762, y + 4, nm, 11, fill=c, anchor="start")
b += circ(fx(0), fy(S50[0] - E50[0]), 4, NO_SOFT, NO) + txt(fx(0) + 8, fy(S50[0] - E50[0]) + 4, "%.2f" % (S50[0] - E50[0]), 10, fill=NO, anchor="start")
b += circ(fx(55), fy(S30[55] - E50[55]), 4, PURP_SOFT, PURP) + txt(fx(55), fy(S30[55] - E50[55]) - 9, "%.2f" % (S30[55] - E50[55]), 10, fill=PURP)
b += lines_at(20, 386, [("search-50 은 가로 0 · 1 에서 encdec-50 보다 낮다(%.2f · %.2f). 가로 0 ~ 20 에서는 search-30 이 search-50 보다 높다." % (S50[0] - E50[0], S50[1] - E50[1]), INK2),
                       ("원문 1절은 「어느 길이에서나 나아짐을 볼 수 있다」 고 적는다.", INK2),
                       ("search-30 이 encdec-50 을 앞선 몫은 가로 25 에서 %.2f 로 가장 크고 가로 55 에서 %.2f 로 가장 작다. 흩어짐이 없어 1 BLEU 아래의 차를 가를 근거가 없다." % (max(S30[i] - E50[i] for i in range(60)), S30[55] - E50[55]), MUTED)], 11, 20)
svg("fig08_fig2_gaps", W, H, b, "그림 2 곡선 차")

# ── 그림 9. 꼭대기 대비 끝 자리 ───────────────────────────────────────────────
W, H = 900, 380
b = defs()
b += txt(20, 30, "그림 2 — 곡선마다 가로 59 의 값이 자기 꼭대기의 몇 % 인가 (내가 센 것)", 15, anchor="start", weight="bold")
rows = [("RNNsearch-50", S50, OK), ("RNNsearch-30", S30, OK), ("RNNencdec-50", E50, FWD), ("RNNencdec-30", E30, FWD)]
for k, (nm, v, c) in enumerate(rows):
    y = 70 + k * 56
    pk = max(v)
    r = v[59] / pk
    b += txt(150, y + 22, nm, 12, fill=c, anchor="end", weight="bold")
    b += box(165, y, 400, 32, NODE, LINE, 1, 3)
    b += '<rect x="165" y="%d" width="%.1f" height="32" fill="%s" stroke="%s"/>' % (y, 400 * r, FWD_SOFT if c == FWD else OK_SOFT, c)
    b += txt(575, y + 21, "%.1f%%  (꼭대기 %.2f 가로 %d -> 가로 59 %.2f, %.2f 내려감)" % (100 * r, pk, v.index(pk), v[59], pk - v[59]), 10.5, fill=INK2, anchor="start")
b += lines_at(20, 304, [("원문 5.1절: 「RNNsearch-30 과 RNNsearch-50 둘 다 길이에 더 강하다(more robust)」.", INK2),
                       ("RNNsearch-30 의 남는 몫 28.3% 는 같은 길이로 배운 RNNencdec-30(7.2%)보다 크지만 RNNencdec-50(28.8%)과 0.5 백분율 점 차다.", INK2),
                       ("내려간 폭으로는 RNNsearch-30 (19.36) 이 RNNencdec-50 (16.00) 보다 크다. 「더 강하다」 가 어느 모델과 견준 말인지 원문은 가르지 않는다.", MUTED)], 10.5, 20)
svg("fig09_fig2_retention", W, H, b, "그림 2 남는 몫")

# ── 그림 3 의 무게 읽기 ──────────────────────────────────────────────────────
STATS = {}
for k in "abcd":
    p = ALPHA[k]
    Mx = p["M"]
    am = [max(range(len(r)), key=lambda j: r[j]) for r in Mx]
    mx = [max(r) for r in Mx]
    sums = [sum(r) for r in Mx]
    disc = sum(1 for i in range(len(am)) for j in range(i + 1, len(am)) if am[j] < am[i])
    tot = len(am) * (len(am) - 1) // 2
    weak = sum(1 for m_ in mx if m_ < 0.5)
    STATS[k] = (am, mx, sums, disc, tot, weak)
    print("  [그림 3 %s] %d x %d, 줄 합 %.3f ~ %.3f, 가장 큰 무게 평균 %.3f, 0.5 아래 줄 %d, 순서 뒤집힌 짝 %d / %d" % (
        k, len(p["T"]), len(p["S"]), min(sums), max(sums), sum(mx) / len(mx), weak, disc, tot))


def heat_panel(x0, y0, k, cell, title):
    p = ALPHA[k]
    S, T, Mx = p["S"], p["T"], p["M"]
    s = txt(x0, y0 - 92, title, 12, fill=INK, anchor="start", weight="bold")
    lw = 92
    for j, w_ in enumerate(S):
        cx = x0 + lw + j * cell + cell / 2
        s += '<text x="%.1f" y="%.1f" font-size="9.5" fill="%s" text-anchor="start" transform="rotate(-60 %.1f %.1f)">%s</text>' % (
            cx, y0 - 4, INK2, cx, y0 - 4, w_.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    for i, t_ in enumerate(T):
        s += txt(x0 + lw - 4, y0 + i * cell + cell / 2 + 3.5, t_, 9.5, fill=INK2, anchor="end")
        for j in range(len(S)):
            a = Mx[i][j]
            s += '<rect x="%.1f" y="%.1f" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="0.4"/>' % (
                x0 + lw + j * cell, y0 + i * cell, cell, cell, heat(a), LINE)
            if a >= 0.2:
                s += txt(x0 + lw + j * cell + cell / 2, y0 + i * cell + cell / 2 + 3, ("%.2f" % a)[1:] if a < 1 else "1", 7.5,
                         fill="#FFFFFF" if a > 0.5 else INK)
    return s


for name, pa, pb, ta, tb in (("fig10_fig3_ab", "a", "b", "(a) 원문 「임의로 고른 문장」", "(b) 「무작위로 고른」 셋 가운데 하나"),
                             ("fig11_fig3_cd", "c", "d", "(c) 「무작위로 고른」 셋 가운데 하나", "(d) 「무작위로 고른」 셋 가운데 하나")):
    W, H = 920, 520
    b = defs()
    b += txt(20, 30, "원문 그림 3 의 무게를 화소 값으로 읽어 다시 그림 — 짙을수록 큰 무게, 0.2 이상만 수를 적었다 (원문과 밝기가 반대)", 13.5, anchor="start", weight="bold")
    b += heat_panel(20, 150, pa, 19, ta)
    b += heat_panel(470, 150, pb, 19, tb)
    svg(name, W, H, b, "원문 그림 3 무게")

# ── 그림 12. 원문이 말한 줄과 말하지 않은 줄 ────────────────────────────────────
def row_of(k, word, nth=0):
    p = ALPHA[k]
    idx = [i for i, t in enumerate(p["T"]) if t == word][nth]
    r = p["M"][idx]
    top = sorted(range(len(r)), key=lambda j: -r[j])[:3]
    return [(p["S"][j], r[j]) for j in top]

SEL = [("(a) zone", row_of("a", "zone"), "원문: Area 로 두 낱말을 건너뛴다"),
       ("(a) économique", row_of("a", "économique"), "원문: 한 낱말씩 뒤로"),
       ("(a) européenne", row_of("a", "européenne"), ""),
       ("(d) l'", row_of("d", "l'"), "원문: the 와 man 을 함께 본다"),
       ("(c) la", row_of("c", "la"), "말하지 않음: 관사가 뒤 명사를 본다"),
       ("(b) que", row_of("b", "que"), "말하지 않음: that 대신 It 이 가장 크다"),
       ("(d) .", row_of("d", "."), "말하지 않음: 원문 . 대신 said"),
       ("(c) peut", row_of("c", "peut"), "말하지 않음: can 과 produce 가 반씩")]
W, H = 920, 500
b = defs()
b += txt(20, 30, "번역 낱말 하나의 무게 위 셋 — 원문 5.2.1절이 말한 줄과 말하지 않은 줄 (내가 읽은 값)", 14, anchor="start", weight="bold")
for k, (lab, top, note) in enumerate(SEL):
    y = 62 + k * 50
    b += txt(120, y + 20, lab, 12, fill=INK, anchor="end", weight="bold")
    x = 135
    for w_, a in top:
        wdt = 330 * a
        b += '<rect x="%.1f" y="%d" width="%.1f" height="28" fill="%s" stroke="%s" stroke-width="0.8"/>' % (x, y, max(wdt, 1), heat(a), FWD)
        if wdt > 44:
            b += txt(x + wdt / 2, y + 18, "%s %.2f" % (w_, a), 10, fill="#FFFFFF" if a > 0.5 else INK)
        x += max(wdt, 1)
    small = ", ".join("%s %.2f" % (w_, a) for w_, a in top if 330 * a <= 44)
    if small:
        b += txt(x + 6, y + 18, small, 9.5, fill=MUTED, anchor="start")
    b += txt(905, y + 18, note, 10.5, fill=INK2 if note.startswith("원문") else REV, anchor="end")
b += lines_at(20, 474, [("막대 길이 = 무게(줄 합 1). 회색조 화소 값 / 255 로 읽었고, 줄 합이 0.957 ~ 1.032 라 칸마다 읽기 오차를 0.04 까지로 본다.", MUTED)], 10.5, 20)
svg("fig12_fig3_rows", W, H, b, "그림 3 의 줄")

# ── 그림 13. 표 2 학습 통계 ─────────────────────────────────────────────────
print("  [표 2]")
T2c = []
for nm, upd, ep, hrs, gpu, trn, dev in T2:
    sents = upd * 1e5 * BATCH / ep
    lo_ = upd * 1e5 * BATCH / (ep + 0.05)
    hi_ = upd * 1e5 * BATCH / (ep - 0.05)
    uph = upd * 1e5 / hrs
    T2c.append((nm, sents, lo_, hi_, uph, hrs, gpu, dev))
    print("     %-14s 바퀴당 문장 %.2fM (반올림 범위 %.2f ~ %.2fM), 시간당 갱신 %.0f, %.1f 일, 개발 NLL %.1f" % (
        nm, sents / 1e6, lo_ / 1e6, hi_ / 1e6, uph, hrs / 24.0, dev))
W, H = 920, 430
b = defs()
b += txt(20, 30, "표 2 로 다시 센 것 — 바퀴당 문장 수(갱신 x 80 / 바퀴)와 시간당 갱신 수 (내가 센 것)", 14, anchor="start", weight="bold")
b += txt(250, 66, "바퀴당 문장 (백만, 가는 선 = 바퀴 수 반올림 범위)", 11, fill=INK2)
b += txt(700, 66, "시간당 갱신", 11, fill=INK2)
for k, (nm, sents, lo_, hi_, uph, hrs, gpu, dev) in enumerate(T2c):
    y = 86 + k * 52
    c = OK if "search" in nm else FWD
    b += txt(120, y + 20, nm, 11.5, fill=c, anchor="end", weight="bold")
    b += txt(120, y + 36, gpu, 9, fill=MUTED, anchor="end")
    fxs = lambda v: 140 + (v - 10.0e6) / 1.0e6 * 300
    b += line(fxs(lo_), y + 14, fxs(hi_), y + 14, c, 1.2)
    b += circ(fxs(sents), y + 14, 5, OK_SOFT if c == OK else FWD_SOFT, c)
    b += txt(fxs(sents), y + 34, "%.2f" % (sents / 1e6), 10, fill=c)
    b += '<rect x="560" y="%d" width="%.1f" height="24" fill="%s" stroke="%s"/>' % (y + 2, uph / 8000.0 * 210, OK_SOFT if c == OK else FWD_SOFT, c)
    b += txt(560 + uph / 8000.0 * 210 + 6, y + 19, "%s / 시간 · %d 시간" % (format(int(round(uph)), ","), hrs), 10, fill=INK2, anchor="start")
for v in (10.0e6, 10.5e6, 11.0e6):
    b += txt(140 + (v - 10.0e6) / 1.0e6 * 300, 356, "%.1f" % (v / 1e6), 9.5, fill=MUTED)
b += lines_at(20, 380, [("-30 과 -50 의 바퀴당 문장 수가 10.47M ~ 10.67M 로 겹친다. 「30 낱말 이하 문장으로 학습」 이 긴 문장을 빼는 것이라면 -30 쪽 바퀴가 그만큼 작아야 한다.", INK2),
                       ("같은 GPU 에서 RNNsearch 의 시간당 갱신이 RNNencdec 의 0.47 ~ 0.54 배다.", INK2)], 10.5, 20)
svg("fig13_table2_training", W, H, b, "표 2 다시 세기")

# ── 그림 14. 「Moses 와 견줄 만하다」 를 두고 한 말 ─────────────────────────────
W, H = 920, 430
b = defs()
b += txt(20, 30, "같은 비교를 두고 한 말의 세기 — RNNsearch 대 기준 구문 기반 시스템(Moses)", 15, anchor="start", weight="bold")
claims = [
    ("잰 것", "표 1 전체 열", "RNNsearch-50* 28.45 대 Moses 33.30 (-4.85). RNNsearch-50 26.75 (-6.55)", OK),
    ("잰 것", "표 1 UNK 없는 열", "RNNsearch-50* 36.15 대 35.63 (+0.52). RNNsearch-50 34.16 (-1.47)", OK),
    ("말", "요약", "「the existing state-of-the-art phrase-based system 과 견줄 만한(comparable) 번역 성능」", REV),
    ("말", "1절", "「단일 모델로 기존 구문 기반 시스템과 견줄 만하거나 가까운(comparable, or close) 성능」", REV),
    ("말", "5.1절", "「알려진 낱말로 된 문장만 보면 Moses 만큼 높다(as high as)」 — 50* 만 넘고 50 은 1.47 아래", REV),
    ("말", "7절", "「기존 구문 기반 통계 번역과 견줄 만한 성능을 냈다 ... 놀라운(striking) 결과」", REV),
    ("조건", "각주 1 · 5.1절", "「state-of-the-art」 = 신경망 부품이 없는 구문 기반 시스템. Moses 는 단일어 418M 낱말을 더 쓴다", MUTED),
]
for k, (kind, where, what, c) in enumerate(claims):
    y = 62 + k * 46
    b += box(20, y, 70, 30, NODE, c, 1.2, 4) + txt(55, y + 20, kind, 11.5, fill=c, weight="bold")
    b += txt(100, y + 20, where, 11, fill=INK2, anchor="start", weight="bold")
    b += txt(215, y + 20, what, 11, fill=INK2, anchor="start")
b += lines_at(20, 400, [("「견줄 만하다」 를 받치는 수는 UNK 없는 열의 RNNsearch-50* 한 줄이다. 그 열은 모델의 어휘 30,000 으로 문장을 고른 부분집합이고, 문장 수와 흩어짐이 없다.", INK2)], 11, 20)
svg("fig14_comparable_claims", W, H, b, "견줄 만하다는 말의 세기")

# ── 그림 15. 계보 ───────────────────────────────────────────────────────────
W, H = 920, 400
b = defs()
b += txt(20, 30, "계보 — 고정 길이 벡터 하나를 원문 자리마다의 주석과 그 무게 합으로 바꾼 자리", 15, anchor="start", weight="bold")
nodes = [
    (30, 70, "Cho 외", "EMNLP 2014", "RNN 인코더-디코더 · 게이트 둘 유닛", INK2, NODE),
    (30, 170, "Sutskever 외", "NIPS 2014", "깊은 LSTM 둘 · 입력 뒤집기 · 직접 번역", INK2, NODE),
    (30, 270, "Graves", "arXiv 2013", "필기 생성: 가우스 창, 한 방향으로만 움직임", INK2, NODE),
    (330, 170, "이 편", "Bahdanau · Cho · Bengio, ICLR 2015", "낱말마다 맥락 벡터 ci = 주석의 무게 합", OK, OK_SOFT),
    (630, 120, "Vaswani 외", "NIPS 2017", "되먹임 없이 주의(attention) 만", FWD, FWD_SOFT),
    (630, 240, "Luong 외 · Jean 외", "2015", "주의 꼴 비교 · 큰 어휘 (원문 뒤의 편)", INK2, NODE),
]
for x, y, t1, t2, t3, c, cs in nodes:
    b += box(x, y, 260, 72, cs, c, 1.3, 6)
    b += txt(x + 12, y + 22, t1, 13, fill=c, anchor="start", weight="bold")
    b += txt(x + 12, y + 42, t2, 10.5, fill=MUTED, anchor="start")
    b += txt(x + 12, y + 61, t3, 10.5, fill=INK2, anchor="start")
for (x1, y1), (x2, y2) in (((290, 106), (330, 196)), ((290, 206), (330, 206)), ((290, 306), (330, 216))):
    b += line(x1, y1, x2, y2, INK2, 1.2, marker="ai")
b += line(590, 196, 630, 156, FWD, 1.4, marker="af")
b += line(590, 216, 630, 266, INK2, 1.2, marker="ai", dash="4 3")
b += txt(612, 150, "로드맵 다음 칸", 10, fill=FWD, anchor="end")
b += lines_at(20, 362, [("화살표는 원문 2 · 6.1절의 인용을 따른다(Graves 2013 은 원문이 가장 가까운 편으로 꼽은 것). 오른쪽 아래 상자는 이 편 뒤에 나와 원문 참고 문헌에 없다.", MUTED)], 10.5, 20)
svg("fig15_lineage", W, H, b, "계보")

print("끝.")
