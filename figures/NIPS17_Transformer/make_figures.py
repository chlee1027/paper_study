# -*- coding: utf-8 -*-
"""Transformer 노트(Vaswani 외, Attention Is All You Need, NIPS 2017 학회판)의 그림 열다섯을 만든다.

색과 글꼴은 저장소의 앞선 노트 그림과 맞췄다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

계산으로 원문을 확인하는 그림이 여럿이다 — 2(비율 맞춘 내적 주의의 작은 예), 3(나누기 √d_k 가 소프트맥스
기울기를 어떻게 바꾸나), 5(가림 한 줄의 예), 6 · 7(자리 부호화의 파장과 회전), 8 · 9(원문 표 1 의 계산량 ·
경로 길이를 수로), 10(식 3 학습률), 11 · 12(표 3 의 파라미터 수를 층 · 폭 · 어휘로 다시 세기), 13(표 2 의
FLOPs 다시 세기). 계산한 값은 돌릴 때 화면에도 찍는다.

원문 표 2 · 표 3 의 수는 아래 T2 · T3 상수에 옮겨 적었다(원문 8 · 9 쪽). 원문 그림 1 · 2 는
crop_paper_figures.py 가 잘라 png 로 둔다.
"""
import io, os, math

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"
NODE      = "#F6F7F5"
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 인코더 · 이 논문 쪽
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 디코더 · 비교 상대 쪽
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 주의 · 원문 표에 적힌 값
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


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, t, size=12, fill=None, anchor="middle", weight=None, style=None):
    a = 'x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s"' % (x, y, size, fill or INK, anchor)
    if weight:
        a += ' font-weight="%s"' % weight
    if style:
        a += ' font-style="%s"' % style
    return "<text %s>%s</text>" % (a, esc(t))


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


def diamond(cx, cy, r, fill, stroke):
    return '<path d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f z" fill="%s" stroke="%s" stroke-width="1.2"/>' % (
        cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy, fill, stroke)


def axes(x0, y0, x1, y1, xt, yt, fx, fy, xl=None, yl=None, xfmt="%g", yfmt="%g"):
    s = line(x0, y1, x1, y1, INK2, 1.2) + line(x0, y0, x0, y1, INK2, 1.2)
    for t in xt:
        lab = xfmt(t) if callable(xfmt) else xfmt % t
        s += line(fx(t), y1, fx(t), y1 + 4, INK2, 1) + txt(fx(t), y1 + 17, lab, 10, fill=MUTED)
    for t in yt:
        lab = yfmt(t) if callable(yfmt) else yfmt % t
        s += line(x0 - 4, fy(t), x0, fy(t), INK2, 1) + txt(x0 - 7, fy(t) + 4, lab, 10, fill=MUTED, anchor="end")
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


def pow10(v):
    e = int(math.floor(math.log10(v)))
    m = v / 10 ** e
    sup = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    if abs(m - 1) < 1e-9:
        return "10" + str(e).translate(sup)
    return ("%.1f·10" % m) + str(e).translate(sup)


print("그림을 만든다 ->", OUT)

# ── 원문의 수 ───────────────────────────────────────────────────────────────
D_BASE, DFF_BASE, H_BASE, N_BASE = 512, 2048, 8, 6
V_TEXT = 37000          # 5.1절 「약 37000 토큰」 (EN-DE, 원문과 번역이 함께 쓰는 BPE 어휘)
WARMUP = 4000
TFLOPS = {"K80": 2.8, "K40": 3.7, "M40": 6.0, "P100": 9.5}   # 각주 5

# 표 2 (원문 8 쪽, newstest2014). (이름, EN-DE BLEU, EN-FR BLEU, EN-DE FLOPs, EN-FR FLOPs, 앙상블?)
T2 = [("ByteNet [15]",              23.75, None,  None,   None,   False),
      ("Deep-Att + PosUnk [32]",    None,  39.2,  None,   1.0e20, False),
      ("GNMT + RL [31]",            24.6,  39.92, 2.3e19, 1.4e20, False),
      ("ConvS2S [8]",               25.16, 40.46, 9.6e18, 1.5e20, False),
      ("MoE [26]",                  26.03, 40.56, 2.0e19, 1.2e20, False),
      ("Deep-Att + PosUnk 앙상블",   None,  40.4,  None,   8.0e20, True),
      ("GNMT + RL 앙상블",           26.30, 41.16, 1.8e20, 1.1e21, True),
      ("ConvS2S 앙상블",             26.36, 41.29, 7.7e19, 1.2e21, True),
      ("Transformer (base)",        27.3,  38.1,  3.3e18, 3.3e18, False),
      ("Transformer (big)",         28.4,  41.0,  2.3e19, 2.3e19, False)]

# 표 3 (원문 9 쪽, newstest2013 개발셋). (묶음, 이름, 바꾼 설정 dict, PPL, BLEU, params ×10⁶ 또는 None)
T3 = [("base", "base",               {},                                   4.92, 25.8, 65),
      ("A", "h=1, d_k=d_v=512",      dict(h=1, dk=512, dv=512),            5.29, 24.9, None),
      ("A", "h=4, d_k=d_v=128",      dict(h=4, dk=128, dv=128),            5.00, 25.5, None),
      ("A", "h=16, d_k=d_v=32",      dict(h=16, dk=32, dv=32),             4.91, 25.8, None),
      ("A", "h=32, d_k=d_v=16",      dict(h=32, dk=16, dv=16),             5.01, 25.4, None),
      ("B", "d_k=16",                dict(dk=16),                          5.16, 25.1, 58),
      ("B", "d_k=32",                dict(dk=32),                          5.01, 25.4, 60),
      ("C", "N=2",                   dict(N=2),                            6.11, 23.7, 36),
      ("C", "N=4",                   dict(N=4),                            5.19, 25.3, 50),
      ("C", "N=8",                   dict(N=8),                            4.88, 25.5, 80),
      ("C", "d_model=256, d_k=d_v=32", dict(d=256, dk=32, dv=32),          5.75, 24.5, 28),
      ("C", "d_model=1024, d_k=d_v=128", dict(d=1024, dk=128, dv=128),     4.66, 26.0, 168),
      ("C", "d_ff=1024",             dict(f=1024),                         5.12, 25.4, 53),
      ("C", "d_ff=4096",             dict(f=4096),                         4.75, 26.2, 90),
      ("D", "P_drop=0.0",            {},                                   5.77, 24.6, None),
      ("D", "P_drop=0.2",            {},                                   4.95, 25.5, None),
      ("D", "ε_ls=0.0",              {},                                   4.67, 25.3, None),
      ("D", "ε_ls=0.2",              {},                                   5.47, 25.7, None),
      ("E", "학습하는 자리 표현",       {},                                   4.92, 25.7, None),
      ("big", "big (300K 걸음)",      dict(d=1024, f=4096, h=16),           4.33, 26.4, 213)]


# ── 파라미터 세기 (내가 센 것) ──────────────────────────────────────────────────
def att_params(d, h, dk, dv):
    # W_Q, W_K (d × h·d_k), W_V (d × h·d_v), W_O (h·d_v × d), 치우침 넷
    return d * h * dk * 2 + d * h * dv + h * dv * d + (h * dk * 2 + h * dv + d)


def ffn_params(d, f):
    return 2 * d * f + f + d


def body_params(N=6, d=512, f=2048, h=8, dk=64, dv=64):
    enc = att_params(d, h, dk, dv) + ffn_params(d, f) + 2 * (2 * d)      # 층 정규화 둘(γ, β)
    dec = 2 * att_params(d, h, dk, dv) + ffn_params(d, f) + 3 * (2 * d)  # 층 정규화 셋
    return N * enc, N * dec


ENC_B, DEC_B = body_params()
ENC_G, DEC_G = body_params(d=1024, f=4096, h=16)
print("  [파라미터] base 인코더 %d · 디코더 %d · 몸통 %d · 낱말 표(37,000×512) %d · 합 %d"
      % (ENC_B, DEC_B, ENC_B + DEC_B, V_TEXT * 512, ENC_B + DEC_B + V_TEXT * 512))
print("  [파라미터] big  인코더 %d · 디코더 %d · 몸통 %d · 낱말 표(37,000×1024) %d · 합 %d"
      % (ENC_G, DEC_G, ENC_G + DEC_G, V_TEXT * 1024, ENC_G + DEC_G + V_TEXT * 1024))

VRANGE = []
for grp, name, cfg, ppl, bleu, prm in T3:
    if prm is None:
        continue
    e, dd = body_params(**cfg)
    d = cfg.get("d", 512)
    lo = ((prm - 0.5) * 1e6 - (e + dd)) / d
    hi = ((prm + 0.5) * 1e6 - (e + dd)) / d
    VRANGE.append((grp, name, prm, e + dd, lo, hi))
    print("  [어휘 역산] %-28s 적힌 %3dM, 몸통 %11d -> 어휘 %6.0f ~ %6.0f" % (name, prm, e + dd, lo, hi))
FAM = [r for r in VRANGE if r[0] != "big"]
FAM_LO = max(r[4] for r in FAM)
FAM_HI = min(r[5] for r in FAM)
print("  [어휘 역산] big 을 뺀 열 줄이 함께 맞는 어휘: %.0f ~ %.0f" % (FAM_LO, FAM_HI))


# ── 그림 1. 층 하나의 모양 (3.1절) ───────────────────────────────────────────────
def fig01():
    W, H = 860, 560
    s = defs()
    s += txt(W / 2, 28, "그림 1. 인코더 층 하나와 디코더 층 하나 — 덧셈 뒤 정규화, 층마다 같은 모양을 6 번 쌓는다", 15, weight="bold")

    def sub(x, y, w, title, sub_t, fill, stroke):
        r = box(x, y, w, 46, fill, stroke, 1.4)
        r += txt(x + w / 2, y + 20, title, 12.5, weight="bold")
        r += txt(x + w / 2, y + 37, sub_t, 10.5, fill=INK2)
        return r

    def addnorm(x, y, w):
        return box(x, y, w, 24, CODE_SOFT, CODE, 1.2) + txt(x + w / 2, y + 16, "LayerNorm(x + 부분층(x))", 10.5, fill=INK)

    # 인코더
    ex, ew = 80, 260
    s += box(ex - 20, 70, ew + 40, 330, "none", FWD, 1.6, rx=10, dash="6 4")
    s += txt(ex - 30, 240, "× 6", 14, fill=FWD, anchor="end", weight="bold")
    s += txt(ex + ew / 2, 62, "인코더 층 (원문 3.1절)", 13, fill=FWD, weight="bold")
    y = 360
    s += txt(ex + ew / 2, 430, "입력: 자리 n 개 × 512 (낱말 표 · √512 + 자리 부호화)", 11, fill=INK2)
    s += line(ex + ew / 2, 418, ex + ew / 2, 398, INK2, 1.4, marker="ai")
    s += sub(ex, 300, ew, "여러 머리 자기 주의", "머리 8 개 × 64, 질의 · 키 · 값 모두 아래층에서", FWD_SOFT, FWD)
    s += addnorm(ex, 262, ew)
    s += sub(ex, 170, ew, "자리별 앞먹임 (FFN)", "512 -> 2048 -> 512, ReLU, 자리마다 같은 무게", NODE, INK2)
    s += addnorm(ex, 132, ew)
    s += line(ex + ew / 2, 300, ex + ew / 2, 288, INK2, 1.2, marker="ai")
    s += line(ex + ew / 2, 262, ex + ew / 2, 218, INK2, 1.2, marker="ai")
    s += line(ex + ew / 2, 170, ex + ew / 2, 158, INK2, 1.2, marker="ai")
    s += line(ex + ew / 2, 132, ex + ew / 2, 92, INK2, 1.4, marker="ai")
    # 지름길
    s += path("M%d,%d L%d,%d L%d,%d" % (ex + ew / 2, 352, ex + ew + 12, 352, ex + ew + 12, 274), OK, sw=1.4, marker="ao")
    s += path("M%d,%d L%d,%d L%d,%d" % (ex + ew / 2, 228, ex + ew + 12, 228, ex + ew + 12, 144), OK, sw=1.4, marker="ao")
    s += txt(ex + ew + 18, 318, "지름길", 10.5, fill=OK, anchor="start")
    s += txt(ex + ew / 2, 84, "출력: n × 512  ->  디코더의 키 · 값", 11, fill=FWD)

    # 디코더
    dx, dw = 500, 290
    s += box(dx - 20, 70, dw + 40, 400, "none", REV, 1.6, rx=10, dash="6 4")
    s += txt(dx + dw + 30, 280, "× 6", 14, fill=REV, anchor="start", weight="bold")
    s += txt(dx + dw / 2, 62, "디코더 층", 13, fill=REV, weight="bold")
    s += txt(dx + dw / 2, 500, "입력: 지금까지 낸 출력을 한 자리 밀어 넣은 것 (shifted right)", 11, fill=INK2)
    s += line(dx + dw / 2, 488, dx + dw / 2, 468, INK2, 1.4, marker="ai")
    s += sub(dx, 420, dw, "가린 여러 머리 자기 주의", "자리 i 는 1 ~ i 만 본다 (뒤쪽 점수 = −∞)", REV_SOFT, REV)
    s += addnorm(dx, 382, dw)
    s += sub(dx, 296, dw, "인코더-디코더 주의", "질의 = 디코더, 키 · 값 = 인코더 마지막 층", CODE_SOFT, CODE)
    s += addnorm(dx, 258, dw)
    s += sub(dx, 172, dw, "자리별 앞먹임 (FFN)", "512 -> 2048 -> 512", NODE, INK2)
    s += addnorm(dx, 134, dw)
    for a, b in ((420, 408), (382, 344), (296, 284), (258, 220), (172, 160)):
        s += line(dx + dw / 2, a, dx + dw / 2, b, INK2, 1.2, marker="ai")
    s += line(dx + dw / 2, 134, dx + dw / 2, 96, INK2, 1.4, marker="ai")
    s += txt(dx + dw / 2, 88, "선형 (낱말 표와 같은 무게) -> 소프트맥스", 11, fill=REV)
    # 인코더 출력 -> 디코더 주의
    s += path("M%d,%d C%d,%d %d,%d %d,%d" % (ex + ew + 20, 100, 420, 100, 420, 318, dx, 318), CODE, sw=1.6, marker="ac")
    s += txt(430, 210, "키 · 값", 11, fill=CODE, anchor="start")
    s += lines_at(40, 530, [("부분층마다 출력 = LayerNorm(x + Dropout(부분층(x))). 정규화가 덧셈 「뒤」 에 있다(원문 식 그대로). "
                             "모든 부분층과 낱말 표의 출력 폭은 d_model = 512.", INK2)], 11)
    svg("fig01_layer", W, H, s, "인코더 층과 디코더 층의 부분층 구성")


# ── 그림 2. 비율 맞춘 내적 주의의 작은 예 (식 1) ─────────────────────────────────────
Q = [1, 0, 1, 0]
KS = [[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 0, 0]]
VS = [[1, 0], [0, 1], [1, 1]]


def softmax(xs):
    m = max(x for x in xs if x != -math.inf)
    es = [0.0 if x == -math.inf else math.exp(x - m) for x in xs]
    t = sum(es)
    return [e / t for e in es]


def fig02():
    dk = len(Q)
    dots = [sum(a * b for a, b in zip(Q, k)) for k in KS]
    sc = [x / math.sqrt(dk) for x in dots]
    w = softmax(sc)
    out = [sum(w[j] * VS[j][c] for j in range(3)) for c in range(2)]
    print("  [주의 예] 내적 %s · 나눈 값 %s · 무게 %s · 출력 %s" % (dots, sc, ["%.3f" % x for x in w], ["%.3f" % x for x in out]))
    W, H = 820, 360
    s = defs()
    s += txt(W / 2, 28, "그림 2. 질의 하나 · 키 셋 · 값 셋으로 식 (1) 을 손으로 한 번 (d_k = 4, 내가 고른 수)", 15, weight="bold")
    s += txt(60, 70, "질의 q = (1, 0, 1, 0)", 13, fill=FWD, anchor="start", weight="bold")
    hx = [60, 250, 360, 470, 570, 690]
    heads = ["키", "q · k", "÷ √4", "소프트맥스 무게", "", "값 v"]
    for x, t in zip(hx, heads):
        s += txt(x, 105, t, 12, fill=INK, anchor="start", weight="bold")
    for j in range(3):
        y = 140 + 52 * j
        s += txt(60, y, "k%d = (%s)" % (j + 1, ", ".join(str(v) for v in KS[j])), 12.5, fill=INK2, anchor="start")
        s += txt(250, y, "%d" % dots[j], 12.5, anchor="start")
        s += txt(360, y, "%.1f" % sc[j], 12.5, anchor="start")
        s += box(470, y - 14, 180 * w[j], 18, CODE_SOFT, CODE, 1, rx=3)
        s += txt(470 + 180 * w[j] + 8, y, "%.3f" % w[j], 12, fill=CODE, anchor="start")
        s += txt(690, y, "v%d = (%d, %d)" % (j + 1, VS[j][0], VS[j][1]), 12.5, fill=REV, anchor="start")
    s += line(60, 290, 790, 290, LINE, 1)
    s += txt(60, 318, "출력 = Σ 무게 × 값 = %.3f·(1,0) + %.3f·(0,1) + %.3f·(1,1) = (%.3f, %.3f)"
             % (w[0], w[1], w[2], out[0], out[1]), 13, fill=INK, anchor="start", weight="bold")
    s += txt(60, 342, "질의와 가장 닮은 키(k1)의 값이 가장 많이 섞이지만, 나머지 둘도 0.49 를 나눠 받는다 — 원문이 「가중 평균」 이라 부르는 것.", 11, fill=INK2, anchor="start")
    svg("fig02_attention_example", W, H, s, "비율 맞춘 내적 주의의 작은 계산 예")
    return w, out


# ── 그림 3. 나누기 √d_k 와 소프트맥스 기울기 (3.2.1절 · 각주 4) ─────────────────────────
def sig(g):
    return 1 / (1 + math.exp(-g))


def fig03():
    g_s = math.sqrt(2)          # 나눈 뒤: 내적 둘의 차의 표준편차 √2
    g_u = 8 * math.sqrt(2)      # 나누기 전(d_k = 64): 8√2
    print("  [포화] 차 %.2f -> 무게 %.4f, 기울기 %.4f · 차 %.2f -> 무게 %.6f, 기울기 %.2e"
          % (g_s, sig(g_s), sig(g_s) * (1 - sig(g_s)), g_u, sig(g_u), sig(g_u) * (1 - sig(g_u))))
    W, H = 820, 400
    s = defs()
    s += txt(W / 2, 28, "그림 3. 키 둘일 때 소프트맥스 무게 p 와 그 기울기 p(1 − p) — 점수 차 g 의 함수", 15, weight="bold")
    x0, x1, y0, y1 = 80, 560, 60, 330
    fx = lambda g: x0 + (x1 - x0) * g / 16
    fy = lambda p: y1 - (y1 - y0) * p
    s += axes(x0, y0, x1, y1, [0, 2, 4, 6, 8, 10, 12, 14, 16], [0, 0.25, 0.5, 0.75, 1.0], fx, fy,
              xl="두 점수의 차 g", yl="값")
    pts1 = [(fx(i / 20), fy(sig(i / 20))) for i in range(0, 321)]
    pts2 = [(fx(i / 20), fy(4 * sig(i / 20) * (1 - sig(i / 20)))) for i in range(0, 321)]
    s += polyline(pts1, FWD, 2.2)
    s += polyline(pts2, REV, 2.2, dash="6 3")
    s += txt(fx(6), fy(0.93), "p (큰 쪽 무게)", 11, fill=FWD)
    s += txt(fx(3.6), fy(0.55), "4·p(1 − p) (기울기, 4 배로 그림)", 11, fill=REV, anchor="start")
    for g, c, lab, yy, anc, dx in ((g_s, OK, "나눈 뒤 전형적 차 √2 = 1.41", 0.035, "start", 5), (g_u, NO, "나누기 전 전형적 차 8√2 = 11.3", 0.45, "end", -5)):
        s += line(fx(g), y0, fx(g), y1, c, 1.4, dash="4 3")
        s += txt(fx(g) + dx, fy(yy), lab, 10.5, fill=c, anchor=anc)
    s += lines_at(585, 90, [
        ("각주 4 의 가정: q · k 의 성분이", INK2), ("평균 0 · 분산 1 이고 서로 독립이면", INK2),
        ("q · k 의 분산은 d_k (= 64), 표준편차 8.", INK2), ("내적 둘의 차는 표준편차 8√2.", INK2),
        ("", INK2),
        ("g = 1.41: p = %.3f, p(1−p) = %.3f" % (sig(g_s), sig(g_s) * (1 - sig(g_s))), OK, "bold"),
        ("g = 11.3: p = %.5f," % sig(g_u), NO, "bold"),
        ("  p(1−p) = %.1e" % (sig(g_u) * (1 - sig(g_u))), NO, "bold"),
        ("", INK2),
        ("기울기 비 %s 배 (내가 센 것)." % format(round((sig(g_s) * (1 - sig(g_s))) / (sig(g_u) * (1 - sig(g_u)))), ","), INK),
        ("원문은 이 효과를 「짐작한다(suspect)」", INK2), ("고만 적고 재지 않았다.", INK2)], 11.5, gap=20)
    svg("fig03_scaling_softmax", W, H, s, "점수 차에 따른 소프트맥스 무게와 기울기")


# ── 그림 4. 여러 머리 — 계산량이 같다 (3.2.2절, 표 3 (A)) ─────────────────────────────
def fig04():
    W, H = 820, 380
    s = defs()
    s += txt(W / 2, 28, "그림 4. 512 폭을 머리 h 개로 나눠도 투영 무게 수와 QKᵀ 곱셈 수는 그대로다 (내가 센 것)", 15, weight="bold")
    # 막대: 512 를 8 칸으로
    x, y, wd = 60, 70, 640
    s += box(x, y, wd, 30, FWD_SOFT, FWD, 1.2, rx=3)
    s += txt(x + wd / 2, y + 20, "질의 하나 = 512 개의 수 (d_model)", 12, fill=FWD)
    for k in range(8):
        xx = x + k * wd / 8
        s += box(xx + 2, y + 50, wd / 8 - 4, 30, CODE_SOFT, CODE, 1, rx=3)
        s += txt(xx + wd / 16, y + 70, "머리 %d: 64" % (k + 1), 11, fill=CODE)
    s += txt(x + wd + 10, y + 70, "h = 8, d_k = 64", 11.5, fill=CODE, anchor="start")
    s += line(x + wd / 2, y + 32, x + wd / 2, y + 48, INK2, 1.2, marker="ai")
    s += txt(x + wd / 2 + 8, y + 44, "학습하는 투영 W_i^Q (512 × 64) 로 머리마다 따로", 10.5, fill=INK2, anchor="start")
    hd = ["h", "d_k = d_v", "h · d_k", "투영 무게 (W^Q,K,V,O)", "QKᵀ 곱셈 (자리 n 개)", "표 3 BLEU"]
    xs = [70, 150, 250, 350, 540, 720]
    yy = 200
    for xx, t in zip(xs, hd):
        s += txt(xx, yy, t, 11.5, fill=INK, anchor="start", weight="bold")
    rows = [(1, 512, 24.9), (4, 128, 25.5), (8, 64, 25.8), (16, 32, 25.8), (32, 16, 25.4)]
    for j, (h, dk, b) in enumerate(rows):
        yj = yy + 24 * (j + 1)
        c = INK if h == 8 else INK2
        proj = 4 * 512 * h * dk
        s += txt(70, yj, str(h), 11.5, fill=c, anchor="start")
        s += txt(150, yj, str(dk), 11.5, fill=c, anchor="start")
        s += txt(250, yj, str(h * dk), 11.5, fill=c, anchor="start")
        s += txt(350, yj, "4 × 512 × %d = %s" % (h * dk, format(proj, ",")), 11.5, fill=c, anchor="start")
        s += txt(540, yj, "%d × %d × n² = 512 · n²" % (h, dk), 11.5, fill=c, anchor="start")
        s += txt(720, yj, "%.1f" % b + ("  (base)" if h == 8 else ""), 11.5, fill=CODE, anchor="start")
    s += txt(60, 350, "같은 것: 투영 무게 1,048,576 개(치우침 빼고), QKᵀ 와 (무게)·V 의 곱셈 수. 다른 것: 소프트맥스를 h 번(자리 n × n 개씩) 한다.", 11, fill=INK2, anchor="start")
    svg("fig04_multihead", W, H, s, "여러 머리 주의에서 머리 수를 바꿔도 같은 계산량")


# ── 그림 5. 디코더의 가림 (3.2.3절) ─────────────────────────────────────────────
def fig05():
    W, H = 820, 380
    s = defs()
    s += txt(W / 2, 28, "그림 5. 디코더 자기 주의의 가림 — 점수 행렬의 위 삼각을 −∞ 로 두고 소프트맥스", 15, weight="bold")
    n = 6
    x0, y0, c = 110, 80, 40
    labs = ["y0", "y1", "y2", "y3", "y4", "y5"]
    for i in range(n):
        s += txt(x0 - 10, y0 + c * i + 25, "질의 " + labs[i], 11, fill=INK2, anchor="end")
        s += txt(x0 + c * i + c / 2, y0 - 8, labs[i], 11, fill=INK2)
        for j in range(n):
            ok = j <= i
            s += box(x0 + c * j, y0 + c * i, c - 2, c - 2, OK_SOFT if ok else NO_SOFT, OK if ok else NO, 1, rx=2)
            s += txt(x0 + c * j + c / 2 - 1, y0 + c * i + 24, "점수" if ok else "−∞", 10, fill=OK if ok else NO)
    s += txt(x0 + c * n / 2, y0 + c * n + 22, "키 (같은 디코더 층의 자리들)", 11, fill=INK2)
    row = [0.5, 1.2, -0.3, 0.9, -math.inf, -math.inf]
    w = softmax(row)
    print("  [가림 예] 질의 y3 줄 점수 %s -> 무게 %s" % (row, ["%.3f" % x for x in w]))
    xx = 450
    s += txt(xx, 90, "예: 질의 y3 의 한 줄 (점수는 내가 고른 수)", 12, fill=INK, anchor="start", weight="bold")
    for j in range(n):
        yj = 120 + 30 * j
        sc = "−∞" if row[j] == -math.inf else "%.1f" % row[j]
        s += txt(xx, yj + 13, "키 %s: 점수 %s" % (labs[j], sc), 11.5, fill=INK2, anchor="start")
        s += box(xx + 140, yj, max(1, 170 * w[j]), 18, CODE_SOFT if w[j] > 0 else NO_SOFT, CODE if w[j] > 0 else NO, 1, rx=2)
        s += txt(xx + 150 + 170 * w[j], yj + 13, "%.3f" % w[j], 11, fill=CODE if w[j] > 0 else NO, anchor="start")
    s += lines_at(xx, 318, [("e^(−∞) = 0 이라 y4 · y5 의 무게가 정확히 0.", INK2),
                            ("입력을 한 자리 미는 것과 합쳐, 자리 i 의 예측은 i 앞의 출력만 쓴다.", INK2)], 11, gap=18)
    svg("fig05_mask", W, H, s, "디코더 자기 주의의 가림 행렬과 한 줄의 무게")


# ── 그림 6. 자리 부호화 (3.5절) ───────────────────────────────────────────────
def pe(pos, i2, d=512):
    return math.sin(pos / 10000 ** (i2 / d)) if i2 % 2 == 0 else math.cos(pos / 10000 ** ((i2 - 1) / d))


def fig06():
    W, H = 860, 450
    s = defs()
    s += txt(W / 2, 28, "그림 6. 사인 · 코사인 자리 부호화 — 차원마다 파장이 다르다 (d_model = 512)", 15, weight="bold")
    x0, x1, y0, y1 = 70, 480, 60, 330
    fx = lambda p: x0 + (x1 - x0) * p / 60
    fy = lambda v: (y0 + y1) / 2 - (y1 - y0) / 2 * v
    s += axes(x0, y0, x1, y1, [0, 10, 20, 30, 40, 50, 60], [-1, -0.5, 0, 0.5, 1], fx, fy, xl="자리 pos", yl="PE(pos, 2i)")
    cols = [(0, FWD), (16, OK), (64, REV), (256, PURP)]
    for k, (i2, c) in enumerate(cols):
        pts = [(fx(p / 10), fy(pe(p / 10, i2))) for p in range(0, 601)]
        s += polyline(pts, c, 1.8)
        lam = 2 * math.pi * 10000 ** (i2 / 512)
        s += txt(x1 + 8, 80 + 20 * k, "2i = %d, 파장 %.2f" % (i2, lam), 11, fill=c, anchor="start")
    # 오른쪽: 파장의 기하수열 (로그 축)
    a0, a1, b0, b1 = 560, 820, 170, 330
    fxa = lambda i: a0 + (a1 - a0) * i / 255
    fyl = lambda lam: b1 - (b1 - b0) * (math.log10(lam) - 0) / 5
    s += line(a0, b1, a1, b1, INK2, 1.2) + line(a0, b0, a0, b1, INK2, 1.2)
    for e in range(0, 6):
        s += line(a0 - 4, fyl(10 ** e), a0, fyl(10 ** e), INK2) + txt(a0 - 7, fyl(10 ** e) + 4, pow10(10 ** e), 9.5, fill=MUTED, anchor="end")
    for t in (0, 64, 128, 192, 255):
        s += txt(fxa(t), b1 + 15, str(t), 9.5, fill=MUTED)
    s += txt((a0 + a1) / 2, b1 + 32, "차원 짝 번호 i (0 ~ 255)", 10.5, fill=INK2)
    pts = [(fxa(i), fyl(2 * math.pi * 10000 ** (2 * i / 512))) for i in range(256)]
    s += polyline(pts, CODE, 2)
    top = 2 * math.pi * 10000 ** (510 / 512)
    s += line(a0, fyl(2 * math.pi * 10000), a1, fyl(2 * math.pi * 10000), NO, 1, dash="4 3")
    s += txt(a1, fyl(2 * math.pi * 10000) - 6, "원문 「10000·2π = 62,832」", 10, fill=NO, anchor="end")
    s += txt(a0 + 6, fyl(top) + 20, "실제 끝값 2π·10000^(510/512) = %s" % format(round(top), ","), 10, fill=CODE, anchor="start")
    s += txt(a0, b0 - 12, "파장 (로그 축)", 10.5, fill=INK2, anchor="start")
    s += lines_at(70, 405, [("각 차원 짝이 다른 시계 바늘처럼 돈다. 짧은 파장(2π)은 이웃 자리를, 긴 파장은 먼 자리를 가른다.", INK2),
                            ("원문의 「2π 에서 10000·2π 까지」 는 위 끝이 닿지 않는 경계다(i 가 255 에서 끝나 지수가 510/512).", INK2)], 11, gap=19)
    svg("fig06_positional_encoding", W, H, s, "사인 코사인 자리 부호화의 곡선과 파장")
    return top


# ── 그림 7. 자리를 k 만큼 옮기기 = 회전 (3.5절의 「선형 함수」) ──────────────────────────
def fig07():
    W, H = 820, 380
    s = defs()
    s += txt(W / 2, 28, "그림 7. PE(pos + k) 는 PE(pos) 에 k 만으로 정해지는 회전 행렬을 곱한 것 (내가 유도한 것)", 15, weight="bold")
    cx, cy, r = 190, 210, 120
    s += circ(cx, cy, r, "none", LINE, 1.4)
    s += line(cx - r - 15, cy, cx + r + 15, cy, LINE, 1) + line(cx, cy - r - 15, cx, cy + r + 15, LINE, 1)
    s += txt(cx + r + 18, cy + 4, "sin", 10.5, fill=MUTED, anchor="start")
    s += txt(cx + 4, cy - r - 18, "cos", 10.5, fill=MUTED, anchor="start")
    w_, pos, k = 1.0, 2.0, 3.0
    p1 = (math.sin(w_ * pos), math.cos(w_ * pos))
    p2 = (math.sin(w_ * (pos + k)), math.cos(w_ * (pos + k)))
    M = [[math.cos(w_ * k), math.sin(w_ * k)], [-math.sin(w_ * k), math.cos(w_ * k)]]
    m2 = (M[0][0] * p1[0] + M[0][1] * p1[1], M[1][0] * p1[0] + M[1][1] * p1[1])
    print("  [회전] PE(2) = (%.3f, %.3f), M_3·PE(2) = (%.3f, %.3f), PE(5) = (%.3f, %.3f)" % (p1 + m2 + p2))
    for p, c, lab in ((p1, FWD, "PE(2)"), (p2, REV, "PE(5)")):
        X, Y = cx + r * p[0], cy - r * p[1]
        s += line(cx, cy, X, Y, c, 2, marker="af" if c == FWD else "ar")
        s += txt(X + (12 if p[0] >= 0 else -12), Y + 4, lab, 12, fill=c, anchor="start" if p[0] >= 0 else "end", weight="bold")
    s += txt(cx, cy + r + 40, "ω = 1 (i = 0 차원 짝), pos = 2, k = 3", 11, fill=INK2)
    s += lines_at(380, 80, [
        ("한 차원 짝 (sin ωpos, cos ωpos) 에 대해", INK),
        ("sin(ω(pos+k)) = sin ωpos · cos ωk + cos ωpos · sin ωk", INK2),
        ("cos(ω(pos+k)) = cos ωpos · cos ωk − sin ωpos · sin ωk", INK2),
        ("", INK2),
        ("곧  PE(pos+k) = M_k · PE(pos),", INK, "bold"),
        ("M_k = [[cos ωk, sin ωk], [−sin ωk, cos ωk]]", INK, "bold"),
        ("", INK2),
        ("예: PE(2) = (%.3f, %.3f)" % p1, FWD),
        ("     M_3 · PE(2) = (%.3f, %.3f) = PE(5)" % m2, REV),
        ("", INK2),
        ("M_k 는 pos 와 무관하다 — 원문의 「고정된 k 에 대해", INK2),
        ("PE(pos+k) 를 PE(pos) 의 선형 함수로 나타낼 수 있다」.", INK2),
        ("이것은 수의 사실이고, 모델이 이 길을 실제로 쓰는지는", INK2),
        ("원문이 재지 않았다(가설로 적었다).", INK2)], 11.5, gap=20)
    svg("fig07_pe_rotation", W, H, s, "자리 부호화에서 자리 이동이 회전이 되는 것")


# ── 그림 8. 표 1 의 층당 계산량을 수로 (4절) ──────────────────────────────────────
def fig08():
    d = 512
    W, H = 860, 430
    s = defs()
    s += txt(W / 2, 28, "그림 8. 층 하나의 곱셈-덧셈 수 (d = 512) — 원문 표 1 의 항과 투영까지 넣은 셈 (내가 센 것)", 15, weight="bold")
    x0, x1, y0, y1 = 90, 560, 60, 360
    lx0, lx1 = 1, math.log10(4000)
    ly0, ly1 = 4, 11
    fx = lambda n: x0 + (x1 - x0) * (math.log10(n) - lx0) / (lx1 - lx0)
    fy = lambda v: y1 - (y1 - y0) * (math.log10(v) - ly0) / (ly1 - ly0)
    s += axes(x0, y0, x1, y1, [10, 30, 100, 300, 1000, 3000], [1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11], fx, fy,
              xl="자리 수 n (로그 축)", yl="곱셈-덧셈 (로그 축)", xfmt="%g", yfmt=pow10)
    ns = [10 * 1.05 ** i for i in range(0, 120) if 10 * 1.05 ** i <= 4000]
    curves = [(lambda n: n * n * d, FWD, None, "표 1 자기 주의 n²·d"),
              (lambda n: n * d * d, REV, None, "표 1 되먹임 n·d²"),
              (lambda n: 4 * n * d * d + 2 * n * n * d, FWD, "6 3", "주의 부분층 전체 4n·d² + 2n²·d"),
              (lambda n: 8 * n * d * d, REV, "6 3", "LSTM 층 8n·d² (문 넷 × 입력 · 되먹임)")]
    for k, (f, c, da, lab) in enumerate(curves):
        s += polyline([(fx(n), fy(f(n))) for n in ns], c, 2, dash=da)
        s += line(585, 80 + 22 * k, 615, 80 + 22 * k, c, 2, dash=da)
        s += txt(622, 84 + 22 * k, lab, 11, fill=c, anchor="start")
    for n, lab, c, anc, dx in ((512, "n = d = 512", CODE, "end", -4), (1024, "n = 2d = 1024", OK, "start", 4)):
        s += line(fx(n), y0, fx(n), y1, c, 1.2, dash="3 3")
        s += txt(fx(n) + dx, y1 - 10, lab, 10, fill=c, anchor=anc)
    n = 50
    rows = [("n = 50 일 때 (내가 센 것)", INK, "bold"),
            ("표 1 자기 주의 n²·d = %s" % format(n * n * d, ","), FWD),
            ("표 1 되먹임 n·d² = %s" % format(n * d * d, ","), REV),
            ("주의 부분층 전체 = %s" % format(4 * n * d * d + 2 * n * n * d, ","), FWD),
            ("LSTM 층 = %s" % format(8 * n * d * d, ","), REV),
            ("FFN 부분층 2n·d·d_ff = %s" % format(2 * n * d * 2048, ","), INK2),
            ("", INK2),
            ("표 1 의 n²·d 는 Q · K · V · O 투영(4n·d²)을", INK2),
            ("뺀 값이다. 투영을 넣으면 n 이 2d 보다 작을 때", INK2),
            ("주의 부분층이 LSTM 층보다 적다. 단순 RNN", INK2),
            ("(2n·d²) 과 견주면 늘 많다.", INK2)]
    s += lines_at(585, 190, rows, 11, gap=19)
    svg("fig08_table1_cost", W, H, s, "자리 수에 따른 층당 계산량")


# ── 그림 9. 표 1 의 최대 경로 길이 ─────────────────────────────────────────────
def fig09():
    W, H = 820, 400
    s = defs()
    s += txt(W / 2, 28, "그림 9. 두 자리를 잇는 가장 긴 경로가 몇 층(걸음)을 지나나 — 원문 표 1 의 차수를 상수 1 로 그림", 15, weight="bold")
    x0, x1, y0, y1 = 80, 520, 60, 340
    fx = lambda n: x0 + (x1 - x0) * n / 100
    fy = lambda v: y1 - (y1 - y0) * v / 100
    s += axes(x0, y0, x1, y1, [0, 20, 40, 60, 80, 100], [0, 20, 40, 60, 80, 100], fx, fy, xl="자리 수 n", yl="경로 길이")
    ns = list(range(1, 101))
    curves = [(lambda n: n, REV, "되먹임 O(n)"),
              (lambda n: n / 3, PURP, "합성곱 이어진 핵 O(n/k), k = 3"),
              (lambda n: n / 10, CODE, "제한 자기 주의 O(n/r), r = 10"),
              (lambda n: math.log(n, 3) if n > 1 else 0, OK, "팽창 합성곱 O(log_k n), k = 3"),
              (lambda n: 1, FWD, "자기 주의 O(1)")]
    for k, (f, c, lab) in enumerate(curves):
        s += polyline([(fx(n), fy(f(n))) for n in ns], c, 2.2)
        s += line(545, 80 + 24 * k, 575, 80 + 24 * k, c, 2.2)
        s += txt(582, 84 + 24 * k, lab, 11, fill=c, anchor="start")
    s += lines_at(545, 220, [("n = 50 에서: 50 · 16.7 · 5 · 3.6 · 1", INK, "bold"),
                             ("", INK2),
                             ("원문 표 1 은 차수(O)만 적는다.", INK2),
                             ("상수 1 은 내가 둔 것이다. 「짧을수록", INK2),
                             ("먼 의존을 배우기 쉽다」 는 원문이 [11]", INK2),
                             ("을 인용해 세운 전제이고, 이 편 안에서", INK2),
                             ("경로 길이와 성능을 함께 잰 실험은 없다.", INK2)], 11, gap=19)
    svg("fig09_path_length", W, H, s, "층 종류별 최대 경로 길이")


# ── 그림 10. 식 3 학습률 (5.3절) ─────────────────────────────────────────────
def lr(step, d, wu=WARMUP):
    return d ** -0.5 * min(step ** -0.5, step * wu ** -1.5)


def fig10():
    W, H = 860, 440
    s = defs()
    s += txt(W / 2, 28, "그림 10. 식 (3) 의 학습률 — 4,000 걸음까지 곧게 오르고 그 뒤 1/√걸음 으로 준다 (내가 센 값)", 15, weight="bold")
    # 왼쪽: 0 ~ 20K
    for (x0, x1, smax, xt, title) in ((70, 390, 20000, [0, 4000, 8000, 12000, 16000, 20000], "처음 20,000 걸음"),
                                     (470, 800, 300000, [0, 100000, 200000, 300000], "전체 (base 100K, big 300K)")):
        y0, y1 = 70, 320
        fx = lambda st, x0=x0, x1=x1, smax=smax: x0 + (x1 - x0) * st / smax
        fy = lambda v: y1 - (y1 - y0) * v / 8e-4
        s += axes(x0, y0, x1, y1, xt, [0, 2e-4, 4e-4, 6e-4, 8e-4], fx, fy, xl="걸음", yl=title,
                  xfmt=lambda t: "%dK" % (t // 1000) if t else "0", yfmt=lambda v: "%.0e" % v if v else "0")
        stp = max(1, smax // 400)
        s += polyline([(fx(st), fy(lr(st, 512))) for st in range(1, smax + 1, stp)], FWD, 2)
        s += polyline([(fx(st), fy(lr(st, 1024))) for st in range(1, smax + 1, stp)], REV, 2, dash="6 3")
    p5, p10 = lr(4000, 512), lr(4000, 1024)
    s += txt(70 + 320 * 4000 / 20000 + 6, 70 + 250 * (1 - p5 / 8e-4) - 4, "꼭짓점 %.2e" % p5, 10.5, fill=FWD, anchor="start")
    s += txt(70 + 320 * 4000 / 20000 + 6, 70 + 250 * (1 - p10 / 8e-4) + 14, "꼭짓점 %.2e" % p10, 10.5, fill=REV, anchor="start")
    s += line(80, 380, 110, 380, FWD, 2) + txt(116, 384, "d_model = 512 (base)", 11, fill=FWD, anchor="start")
    s += line(80, 404, 110, 404, REV, 2, dash="6 3") + txt(116, 408, "d_model = 1024 (big, 식을 그대로 쓴다면)", 11, fill=REV, anchor="start")
    s += txt(470, 384, "끝값: base 100K 걸음 %.2e · big 300K 걸음 %.2e" % (lr(100000, 512), lr(300000, 1024)), 11, fill=INK2, anchor="start")
    s += txt(470, 408, "원문은 big 의 학습률 설정을 따로 적지 않았다.", 11, fill=INK2, anchor="start")
    svg("fig10_lr_schedule", W, H, s, "식 3 학습률 일정")
    print("  [학습률] 꼭짓점 512: %.4e · 1024: %.4e · base 끝 %.4e · big 끝 %.4e" % (p5, p10, lr(100000, 512), lr(300000, 1024)))


# ── 그림 11. 파라미터 내역 (3절 · 표 3) ───────────────────────────────────────
def fig11():
    W, H = 860, 400
    s = defs()
    s += txt(W / 2, 28, "그림 11. base · big 파라미터를 층 · 폭 · 어휘(37,000, 공유 1 개)로 다시 센 것 (내가 센 것)", 15, weight="bold")
    data = [("base", ENC_B, DEC_B, V_TEXT * 512, 65), ("big", ENC_G, DEC_G, V_TEXT * 1024, 213)]
    x0, x1 = 160, 700
    fx = lambda v: x0 + (x1 - x0) * v / 230e6
    for t in range(0, 230, 50):
        s += line(fx(t * 1e6), 70, fx(t * 1e6), 270, LINE, 0.8, dash="2 3") + txt(fx(t * 1e6), 285, "%dM" % t, 10, fill=MUTED)
    for j, (nm, e, dd, emb, listed) in enumerate(data):
        y = 90 + 90 * j
        s += txt(x0 - 12, y + 24, nm, 13, anchor="end", weight="bold")
        xs = x0
        for v, c, cs, lab in ((emb, CODE, CODE_SOFT, "낱말 표"), (e, FWD, FWD_SOFT, "인코더"), (dd, REV, REV_SOFT, "디코더")):
            s += box(xs, y, fx(v) - x0, 36, cs, c, 1.2, rx=2)
            xs += fx(v) - x0
        s += txt(x0, y + 54, "낱말 표 %.2fM · 인코더 %.2fM · 디코더 %.2fM" % (emb / 1e6, e / 1e6, dd / 1e6), 10.5, fill=INK2, anchor="start")
        tot = e + dd + emb
        s += txt(xs + 8, y + 15, "합 %.2fM" % (tot / 1e6), 11.5, fill=INK, anchor="start", weight="bold")
        s += txt(xs + 8, y + 32, "원문 표 3: %dM" % listed, 11.5, fill=NO, anchor="start")
        s += line(fx(listed * 1e6), y - 6, fx(listed * 1e6), y + 42, NO, 2)
    s += lines_at(60, 320, [("층 하나: 주의 = 4·d² + 치우침 4·d, FFN = 2·d·d_ff + d_ff + d, 층 정규화 2·d 씩. 디코더 층은 주의 둘 · 정규화 셋.", INK2),
                            ("낱말 표는 원문 3.4절대로 원문 쪽 · 번역 쪽 낱말 표와 소프트맥스 앞 선형이 무게 하나를 나눈다고 두었다.", INK2),
                            ("base 는 1.92M 모자라고(63.08 대 65), big 은 1.25M 넘친다(214.25 대 213). 어휘 하나로 둘 다 맞출 수 없다(그림 12).", NO)], 11, gap=20)
    svg("fig11_param_breakdown", W, H, s, "base와 big 모델의 파라미터 내역")


# ── 그림 12. 표 3 의 params 열에서 어휘 크기를 거꾸로 (내가 센 것) ───────────────────────
def fig12():
    W, H = 860, 470
    s = defs()
    s += txt(W / 2, 28, "그림 12. 표 3 의 params(반올림한 정수 M) 가 허락하는 공유 어휘 크기 — 줄마다 구간 (내가 센 것)", 15, weight="bold")
    x0, x1 = 250, 800
    lo, hi = 34000, 44000
    fx = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)
    y0 = 60
    n = len(VRANGE)
    y1 = y0 + 26 * n + 10
    for t in range(34000, 44001, 2000):
        s += line(fx(t), y0, fx(t), y1, LINE, 0.8, dash="2 3") + txt(fx(t), y1 + 16, format(t, ","), 10, fill=MUTED)
    s += box(fx(FAM_LO), y0, fx(FAM_HI) - fx(FAM_LO), y1 - y0, OK_SOFT, OK, 1, rx=0)
    s += line(fx(V_TEXT), y0 - 4, fx(V_TEXT), y1, CODE, 1.6, dash="5 3")
    s += txt(fx(V_TEXT), y0 - 8, "본문 「약 37000」", 10.5, fill=CODE)
    for j, (grp, name, prm, body, a, b) in enumerate(VRANGE):
        y = y0 + 14 + 26 * j
        c = NO if grp == "big" else FWD
        s += txt(x0 - 10, y + 4, ("%s  (%dM)" % (name, prm)) if grp in ("base", "big") else ("(%s) %s  (%dM)" % (grp, name, prm)), 10.5, fill=c, anchor="end")
        aa, bb = max(a, lo), min(b, hi)
        s += line(fx(aa), y, fx(bb), y, c, 5)
    s += lines_at(60, y1 + 44, [
        ("초록 띠: big 을 뺀 열 줄이 함께 허락하는 어휘 %s ~ %s. 본문의 37,000 은 이 띠 밖이다." % (format(round(FAM_LO), ","), format(round(FAM_HI), ",")), OK),
        ("big 줄만 35,296 ~ 36,272 를 요구해 띠와 겹치지 않는다. 치우침 · 정규화를 빼거나 낱말 표를 2 · 3 개로 세도 열한 줄 모두를 맞추는 어휘는 없었다.", NO),
        ("원문은 정확한 어휘 수와 params 를 셈한 방식을 적지 않았다 — 이 그림은 「어긋난다」 까지만 말한다.", INK2)], 11, gap=20)
    svg("fig12_vocab_intervals", W, H, s, "표 3 파라미터 수에서 역산한 어휘 크기 구간")


# ── 그림 13. 표 2 — BLEU 와 학습 비용 ──────────────────────────────────────────
def fig13():
    W, H = 900, 450
    s = defs()
    s += txt(W / 2, 28, "그림 13. 원문 표 2 — BLEU 대 학습 비용 추정(FLOPs, 로그 축). 원은 단일 모델, 네모는 앙상블", 15, weight="bold")
    panels = [(70, 420, 1, 3, "EN-DE (newstest2014)", 23, 29), (500, 850, 2, 4, "EN-FR (newstest2014)", 38, 42)]
    for (x0, x1, bi, ci, title, ylo, yhi) in panels:
        y0, y1 = 70, 340
        fx = lambda v, x0=x0, x1=x1: x0 + (x1 - x0) * (math.log10(v) - 18) / 3.3
        fy = lambda b, ylo=ylo, yhi=yhi: y1 - (y1 - y0) * (b - ylo) / (yhi - ylo)
        s += axes(x0, y0, x1, y1, [1e18, 1e19, 1e20, 1e21], list(range(ylo, yhi + 1)), fx, fy,
                  xl="학습 비용 FLOPs", yl=title, xfmt=pow10)
        for (nm, de, fr, cde, cfr, ens) in T2:
            b = (de, fr)[bi - 1]
            c = (cde, cfr)[bi - 1]
            if b is None:
                continue
            if c is None:
                s += txt(x0 + 6, fy(b) + 4, "%s %.2f (비용 칸 비어 있음)" % (nm, b), 10, fill=MUTED, anchor="start")
                continue
            X, Y = fx(c), fy(b)
            if nm.startswith("Transformer"):
                s += diamond(X, Y, 7, FWD, FWD)
                col = FWD
            elif ens:
                s += '<rect x="%.1f" y="%.1f" width="10" height="10" fill="%s" stroke="%s"/>' % (X - 5, Y - 5, REV_SOFT, REV)
                col = REV
            else:
                s += circ(X, Y, 5, REV_SOFT, REV)
                col = INK2
            place = {("ConvS2S 앙상블", 1): (-8, -9, "end"), ("GNMT + RL 앙상블", 1): (8, 16, "start"),
                     ("ConvS2S 앙상블", 2): (-8, -9, "end"), ("GNMT + RL 앙상블", 2): (-8, 16, "end"),
                     ("Deep-Att + PosUnk 앙상블", 2): (-8, 18, "end"), ("GNMT + RL [31]", 2): (-8, 4, "end"), ("MoE [26]", 2): (-8, -9, "end"),
                     ("ConvS2S [8]", 2): (-8, 4, "end"), ("GNMT + RL [31]", 1): (8, 16, "start")}
            dx, dy, anc = place.get((nm, bi), (8, -9, "start"))
            s += txt(X + dx, Y + dy, "%s %.2f" % (nm.replace(" [31]", "").replace(" [8]", "").replace(" [26]", "").replace(" [32]", ""), b),
                     9.5, fill=col, anchor=anc)
    s += lines_at(70, 392, [("Transformer 의 비용은 원문 표에서 두 언어 칸에 걸친 값 하나(base 3.3·10¹⁸, big 2.3·10¹⁹)라 두 칸에 같이 찍었다.", INK2),
                            ("FLOPs 는 연산을 센 것이 아니라 「학습 시간 × GPU 수 × GPU 의 단정밀도 능력 추정」(각주 5) 이다. 비교 상대의 BLEU 는 각 논문에서 옮긴 값이다.", INK2)], 11, gap=20)
    svg("fig13_table2", W, H, s, "표 2의 BLEU와 학습 비용 산점도")


# ── 그림 14. 표 3 — base 대비 BLEU 차 ─────────────────────────────────────────
def fig14():
    rows = [r for r in T3 if r[0] != "base"]
    W, H = 900, 120 + 24 * len(rows)
    s = defs()
    s += txt(W / 2, 28, "그림 14. 원문 표 3 — 개발셋(newstest2013) BLEU 의 base(25.8) 대비 차, 줄마다 실행 하나", 15, weight="bold")
    x0, x1 = 340, 600
    fx = lambda v: (x0 + x1) / 2 + (x1 - x0) / 2 * v / 2.4
    y0 = 60
    for t in (-2, -1, 0, 1):
        s += line(fx(t), y0, fx(t), y0 + 24 * len(rows), LINE if t else INK2, 0.8 if t else 1.2, dash="2 3" if t else None)
        s += txt(fx(t), y0 + 24 * len(rows) + 16, "%+d" % t if t else "0", 10, fill=MUTED)
    s += txt(620, 52, "BLEU (차)", 11, fill=INK2, anchor="start", weight="bold")
    s += txt(720, 52, "PPL (base 4.92)", 11, fill=INK2, anchor="start", weight="bold")
    s += txt(830, 52, "params", 11, fill=INK2, anchor="start", weight="bold")
    for j, (grp, name, cfg, ppl, bleu, prm) in enumerate(rows):
        y = y0 + 12 + 24 * j
        dlt = bleu - 25.8
        c = OK if dlt > 0 else (NO if dlt < 0 else MUTED)
        s += txt(x0 - 10, y + 4, "(%s) %s" % (grp, name) if grp != "big" else name, 10.5, fill=INK if grp == "big" else INK2, anchor="end")
        a, b = sorted((fx(0), fx(dlt)))
        s += box(a, y - 8, max(1.5, b - a), 16, OK_SOFT if dlt > 0 else NO_SOFT, c, 1, rx=2)
        s += txt(620, y + 4, "%.1f (%+.1f)" % (bleu, dlt), 10.5, fill=c, anchor="start")
        s += txt(720, y + 4, "%.2f" % ppl, 10.5, fill=INK2, anchor="start")
        s += txt(830, y + 4, "%dM" % prm if prm else "", 10.5, fill=INK2, anchor="start")
    s += txt(60, H - 18, "흩어짐(실행 사이 변동)이 적혀 있지 않아, 0.1 ~ 0.4 차이가 변동 안인지 밖인지 이 표로 가를 수 없다. big 은 걸음 수(300K)와 P_drop(0.3)도 함께 다르다.", 11, fill=INK2, anchor="start")
    svg("fig14_table3", W, H, s, "표 3 변형별 BLEU 차이")


# ── 그림 15. 계보 ───────────────────────────────────────────────────────────
def fig15():
    W, H = 900, 400
    s = defs()
    s += txt(W / 2, 28, "그림 15. 순차 데이터 갈래 — 앞 편의 한계를 다음 편이 받는다", 15, weight="bold")
    nodes = [(30, 80, "Elman 1990", "은닉을 복사해 되먹임", INK2),
             (250, 80, "LSTM 1997", "오차 배율 1.0 셀 · 곱셈 문", INK2),
             (470, 80, "Cho 외 2014", "인코더-디코더 · 문 둘 유닛", INK2),
             (690, 80, "seq2seq 2014", "4 층 LSTM · 벡터 하나", INK2),
             (690, 200, "Bahdanau 외 2015", "디코더 걸음마다 원문 자리에 무게", CODE),
             (380, 200, "이 편 2017", "되먹임 없이 주의만", FWD),
             (150, 300, "이미지로", "원문 7절 「다른 형식」", OK),
             (450, 300, "긴 입력으로", "원문 4 · 7절 「제한된 주의」", OK),
             (700, 300, "생성을 덜 순차로", "원문 7절", OK)]
    for (x, y, a, b, c) in nodes:
        s += box(x, y, 190, 54, NODE, c, 1.4)
        s += txt(x + 95, y + 22, a, 12.5, fill=c, weight="bold")
        s += txt(x + 95, y + 41, b, 10.5, fill=INK2)
    for xa in (220, 440, 660):
        s += line(xa, 107, xa + 28, 107, INK2, 1.4, marker="ai")
    s += line(785, 134, 785, 198, CODE, 1.4, marker="ac")
    s += line(690, 227, 572, 227, FWD, 1.4, marker="af")
    s += line(430, 254, 250, 298, OK, 1.2, marker="ao")
    s += line(475, 254, 540, 298, OK, 1.2, marker="ao")
    s += line(520, 254, 790, 298, OK, 1.2, marker="ao")
    s += txt(795, 170, "고정 길이 벡터 병목", 10.5, fill=CODE, anchor="start")
    s += txt(631, 218, "되먹임을 뺀다", 10.5, fill=FWD)
    s += txt(W / 2, 382, "아래 줄 셋은 원문이 스스로 적은 다음 할 일이다. 어느 편이 그 자리를 받았는지는 이 노트 「다음에 읽을 것」 에 적는다.", 11, fill=INK2)
    svg("fig15_lineage", W, H, s, "순차 데이터 갈래의 계보")


# ── FLOPs 다시 세기 (표 2, 각주 5) ─────────────────────────────────────────────
base_flops = 12 * 3600 * 8 * TFLOPS["P100"] * 1e12
big_flops = 3.5 * 86400 * 8 * TFLOPS["P100"] * 1e12
print("  [FLOPs] base 12 시간 × 8 × 9.5T = %.3e (원문 3.3e18) · big 3.5 일 × 8 × 9.5T = %.3e (원문 2.3e19)" % (base_flops, big_flops))
print("  [걸음 시간] base 100K × 0.4 초 = %.2f 시간 · big 300K × 1.0 초 = %.2f 일" % (100000 * 0.4 / 3600, 300000 * 1.0 / 86400))

fig01(); fig02(); fig03(); fig04(); fig05(); fig06(); fig07(); fig08(); fig09()
fig10(); fig11(); fig12(); fig13(); fig14(); fig15()
