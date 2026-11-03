# -*- coding: utf-8 -*-
"""RNN 인코더-디코더 노트(Cho 외, EMNLP 2014)의 그림 열여섯을 만든다.

색과 글꼴은 저장소의 앞선 노트 그림들과 맞췄다. 표준 라이브러리만 쓴다.

  python make_figures.py

계산으로 원문을 확인하거나 원문에 없는 수를 내는 그림이 여럿이다 — 3(게이트 네 모서리의 값),
4(갱신 게이트 값에 따른 반감 걸음 수), 5 · 6(파라미터 세기), 7(재설정 게이트를 곱하는 자리 두 가지),
9(표 1 의 차이), 10(말뭉치 단어 수 더하기), 11(그림 3 의 점 5,000 개로 낸 상관), 12(미등록 단어 비율),
13(표 2 의 낱말 수), 14(표 3 의 표본 수). 계산한 값은 돌릴 때 화면에도 찍는다.

그림 11 만 바깥 파일을 읽는다 — 같은 폴더의 paper_fig3_points.csv(crop_paper_figures.py 가 원문 PDF 의
벡터 그림에서 읽어 만든 점 5,000 개). 표 2 · 3 의 구문은 원문 표를 손으로 옮겨 아래 상수에 적었다.
"""
import io, os, math, csv, statistics as st

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"
NODE      = "#F6F7F5"
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 인코더 · 원문 쪽
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 디코더 · RNN 인코더-디코더 쪽
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 요약 벡터 c, 게이트
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"
OK_SOFT   = "#D6EEDD"
NO        = "#C0392B"
NO_SOFT   = "#F6D9D5"
VIO       = "#8E44AD"
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
    return ("<defs>" + arrow("af", FWD) + arrow("ar", REV) + arrow("ai", INK2) + arrow("ac", CODE)
            + arrow("ao", OK) + arrow("an", NO) + "</defs>")


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


def circ(cx, cy, r, fill=None, stroke=None, sw=1.2, op=None):
    a = '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s"' % (
        cx, cy, r, fill or NODE, stroke or INK, sw)
    if op:
        a += ' opacity="%s"' % op
    return a + "/>"


def path(d, stroke=None, fill="none", sw=1.6, dash=None, marker=None, op=None):
    a = '<path d="%s" fill="%s" stroke="%s" stroke-width="%s"' % (d, fill, stroke or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if marker:
        a += ' marker-end="url(#%s)"' % marker
    if op:
        a += ' opacity="%s"' % op
    return a + "/>"


def polyline(pts, stroke, sw=2, dash=None, op=None):
    d = "M" + " L".join("%.1f,%.1f" % p for p in pts)
    return path(d, stroke, sw=sw, dash=dash, op=op)


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


def sig(v):
    return 1.0 / (1.0 + math.exp(-v))


print("그림을 만든다 ->", OUT)

# ── 그림 1. RNN 인코더-디코더 (원문 그림 1 을 식과 함께 다시 그림) ─────────────────
W, H = 900, 400
b = defs()
b += txt(20, 30, "RNN 인코더-디코더 (2.2절) — 인코더가 입력 전체를 길이가 정해진 벡터 c 하나로 줄이고, 디코더는 매 걸음 c 를 다시 받는다", 14, anchor="start", weight="bold")
ex = [90, 190, 330]
labels = ["x1", "x2", "xT"]
for i, (x, lab) in enumerate(zip(ex, labels)):
    b += box(x - 30, 200, 60, 44, FWD_SOFT, FWD)
    b += txt(x, 227, "h<%s>" % ("1", "2", "T")[i], 12, fill=FWD)
    b += line(x, 300, x, 247, FWD, 1.4, marker="af")
    b += txt(x, 318, lab, 13, fill=INK, weight="bold")
b += line(120, 222, 157, 222, FWD, 1.4, marker="af")
b += txt(260, 227, "…", 16, fill=FWD)
b += line(222, 222, 237, 222, FWD, 1.4)
b += line(282, 222, 297, 222, FWD, 1.4, marker="af")
b += txt(210, 362, "인코더: h<t> = f(h<t-1>, x_t)  — 식 (1). 끝 기호를 읽은 뒤의 상태가 요약 c", 11, fill=INK2)
# c
b += circ(450, 140, 30, CODE_SOFT, CODE, 1.8)
b += txt(450, 146, "c", 18, fill=CODE, weight="bold")
b += path("M360,222 C400,222 410,170 424,158", CODE, sw=1.6, marker="ac")
b += txt(450, 92, "1,000 차원 (4.4절)", 11, fill=CODE)
# 디코더
dx = [570, 680, 820]
for i, x in enumerate(dx):
    b += box(x - 30, 200, 60, 44, REV_SOFT, REV)
    b += txt(x, 227, "h<%s>" % ("1", "2", "T'")[i], 12, fill=REV)
    b += line(x, 197, x, 155, REV, 1.4, marker="ar")
    b += txt(x, 145, ("y1", "y2", "yT'")[i], 13, fill=INK, weight="bold")
    b += path("M478,%d C%d,%d %d,190 %d,200" % (148 + 4 * i, x - 60, 170 + 4 * i, x - 10, x - 6), CODE, sw=1.1, dash="4 3", marker="ac")
b += line(600, 222, 647, 222, REV, 1.4, marker="ar")
b += txt(750, 227, "…", 16, fill=REV)
b += line(710, 222, 725, 222, REV, 1.4)
b += line(772, 222, 787, 222, REV, 1.4, marker="ar")
# y_{t-1} 되먹임
b += path("M584,140 C640,150 620,285 668,250", INK2, sw=1.1, marker="ai")
b += txt(640, 300, "y1 이 다음 걸음 입력", 10, fill=INK2)
b += txt(690, 340, "디코더: h<t> = f(h<t-1>, y_{t-1}, c),  P(y_t | y_{<t}, c) = g(h<t>, y_{t-1}, c)", 11, fill=INK2)
b += txt(690, 362, "점선 = c 가 모든 걸음에 들어간다 (원문 그림 1 의 화살표)", 11, fill=CODE)
b += txt(450, 388, "길이 T 와 T' 는 달라도 된다. 학습은 식 (4): 짝 N 개의 조건부 로그 가능도 평균을 최대화", 11, fill=MUTED)
svg("fig01_encoder_decoder", W, H, b, "RNN 인코더-디코더 구조")

# ── 그림 2. 게이트 은닉 유닛 (식 5-8) ────────────────────────────────────────────
W, H = 900, 380
b = defs()
b += txt(20, 30, "제안한 은닉 유닛 (2.3절, 식 5-8) — 게이트 둘. 원문은 이 유닛에 이름을 붙이지 않는다(나중 이름: GRU)", 14, anchor="start", weight="bold")
b += box(40, 150, 90, 50, FWD_SOFT, FWD)
b += txt(85, 180, "h<t-1>", 13, fill=FWD, weight="bold")
b += box(40, 280, 90, 44, NODE, INK2)
b += txt(85, 307, "x", 13, weight="bold")
# 게이트
b += box(220, 70, 150, 50, CODE_SOFT, CODE)
b += txt(295, 92, "재설정 r = σ(W_r x + U_r h)", 11, fill=CODE)
b += txt(295, 110, "식 (5)", 10, fill=MUTED)
b += box(220, 235, 150, 50, CODE_SOFT, CODE)
b += txt(295, 257, "갱신 z = σ(W_z x + U_z h)", 11, fill=CODE)
b += txt(295, 275, "식 (6)", 10, fill=MUTED)
b += box(450, 70, 190, 50, REV_SOFT, REV)
b += txt(545, 92, "후보 h~ = tanh(W x + U(r⊙h))", 11, fill=REV)
b += txt(545, 110, "식 (8). φ 는 4.1.1절에서 tanh", 10, fill=MUTED)
b += box(690, 170, 180, 60, OK_SOFT, OK)
b += txt(780, 195, "h<t> = z·h<t-1> + (1-z)·h~", 12, fill=OK, weight="bold")
b += txt(780, 215, "식 (7)", 10, fill=MUTED)
for (x1, y1, x2, y2, c, m) in [(130, 168, 218, 100, INK2, "ai"), (130, 182, 218, 255, INK2, "ai"),
                               (130, 296, 218, 270, INK2, "ai"), (130, 290, 218, 108, INK2, "ai"),
                               (370, 95, 448, 95, CODE, "ac"), (640, 95, 720, 168, REV, "ar"),
                               (370, 260, 688, 210, CODE, "ac"), (130, 160, 448, 82, FWD, "af")]:
    b += line(x1, y1, x2, y2, c, 1.2, marker=m)
b += path("M85,150 L85,52 L780,52 L780,168", FWD, sw=1.2, dash="5 4", marker="af")
b += txt(780, 252, "점선: z 가 1 이면 h<t-1> 이 그대로 건너간다", 11, fill=FWD)
b += txt(780, 270, "(이 길에는 곱하는 행렬도 tanh 도 없다)", 11, fill=FWD)
b += txt(450, 350, "표기: 원문 식은 유닛 j 하나의 값([·]_j)으로 적고, 바이어스 항이 없다. 유닛 하나에 재설정 · 갱신 게이트가 따로 있다", 11, fill=INK2)
svg("fig02_gated_unit", W, H, b, "게이트 은닉 유닛의 계산 흐름")

# ── 그림 3. 게이트 네 모서리 — 1 차원 작은 예 ─────────────────────────────────────
HP, WX, UU = 0.8, 0.3, 1.2      # 내가 고른 수: 이전 상태, 입력 몫 Wx, 순환 무게 U
cases = []
for r, z in [(0, 0), (1, 0), (0, 1), (1, 1), (0.5, 0.5)]:
    ht = math.tanh(WX + UU * r * HP)
    h = z * HP + (1 - z) * ht
    cases.append((r, z, ht, h))
print("  [그림 3] 게이트 모서리 (h_prev=0.8, Wx=0.3, U=1.2):", [(r, z, round(ht, 3), round(h, 3)) for r, z, ht, h in cases])
W, H = 900, 330
b = txt(20, 30, "게이트 네 모서리 — 유닛 하나, 내가 고른 수: 이전 상태 h<t-1> = 0.8, 입력 몫 Wx = 0.3, 순환 무게 U = 1.2", 14, anchor="start", weight="bold")
heads = ["r", "z", "후보 h~ = tanh(0.3 + 1.2·r·0.8)", "새 상태 h<t>", "읽는 법"]
xs = [40, 100, 160, 470, 600]
for x, t in zip(xs, heads):
    b += txt(x, 70, t, 12, fill=INK2, anchor="start", weight="bold")
b += line(30, 80, 880, 80, LINE, 1)
reads = ["이전 상태를 버리고 지금 입력만으로 새로 쓴다", "옛 상태를 본 후보로 통째로 바꾼다 (tanh 유닛과 같다)",
         "이전 상태를 그대로 넘긴다 (r 은 상관없다)", "이전 상태를 그대로 넘긴다", "반씩 섞는다"]
for j, (r, z, ht, h) in enumerate(cases):
    y = 108 + 40 * j
    col = OK if z == 1 else (REV if z == 0 else INK)
    b += txt(40, y, "%g" % r, 13, anchor="start")
    b += txt(100, y, "%g" % z, 13, anchor="start")
    b += txt(160, y, "%.3f" % ht, 13, anchor="start", fill=REV)
    b += txt(470, y, "%.3f" % h, 13, anchor="start", fill=col, weight="bold")
    b += txt(600, y, reads[j], 11, anchor="start", fill=INK2)
b += txt(450, 318, "r = 1, z = 0 줄의 0.851 이 게이트 없는 tanh 유닛 tanh(Wx + U·h) 의 값과 같다 — 게이트 유닛은 그 유닛을 한 모서리로 품는다", 11, fill=MUTED)
svg("fig03_gate_corners", W, H, b, "게이트 값 네 모서리에서 새 상태")

# ── 그림 4. 갱신 게이트와 기억의 길이 ──────────────────────────────────────────
W, H = 900, 400
b = txt(20, 30, "갱신 게이트 z 를 걸음마다 같은 값으로 둘 때 — k 걸음 뒤 남는 몫 z^k (원문이 말한 「새는 적분 유닛」 의 꼴)", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 600, 70, 330
fx = lambda k: X0 + k / 100 * (X1 - X0)
fy = lambda v: Y1 - v * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [0, 20, 40, 60, 80, 100], [0, 0.25, 0.5, 0.75, 1.0], fx, fy, "걸음 수 k", "남는 몫")
cols = {0.5: VIO, 0.9: REV, 0.99: OK}
half = {}
for z, c in cols.items():
    b += polyline([(fx(k), fy(z ** k)) for k in range(0, 101)], c, 2.2)
    half[z] = math.log(0.5) / math.log(z)
b += polyline([(fx(k), fy(0.9 ** k)) for k in range(0, 101)], REV, 2.2)
b += line(X0, fy(0.5), X1, fy(0.5), INK2, 1, dash="4 3")
print("  [그림 4] 반감 걸음 수:", {z: round(v, 2) for z, v in half.items()}, " 0.99^100 =", round(0.99 ** 100, 4))
b += lines_at(630, 90, [("z = 0.5  반감 %.2f 걸음" % half[0.5], VIO, "bold"),
                         ("z = 0.9  반감 %.2f 걸음" % half[0.9], REV, "bold"),
                         ("z = 0.99 반감 %.2f 걸음" % half[0.99], OK, "bold"),
                         ("", INK2),
                         ("0.99^100 = %.3f" % (0.99 ** 100), OK),
                         ("0.9^100 = %.1e" % (0.9 ** 100), REV),
                         ("", INK2),
                         ("원문 식 (7) 은 z 를 걸음마다", INK2),
                         ("입력과 상태로 다시 정한다", INK2),
                         ("(그래서 「적응형」).", INK2),
                         ("이 그림은 z 를 고정한 경우만이다", MUTED)], 12, 22)
b += txt(340, 385, "반감 걸음 수 = ln 0.5 / ln z (내가 계산한 값). 원문은 유닛별 z 의 분포나 시간 척도를 재지 않는다", 11, fill=MUTED)
svg("fig04_memory_halflife", W, H, b, "갱신 게이트 값에 따른 기억의 반감")

# ── 그림 5. 실험 모델의 파라미터 세기 (가정 표기) ─────────────────────────────────
V, E, N, MO = 15000, 100, 1000, 500    # 어휘, 임베딩(낮은 계수), 은닉, maxout 단위
parts = [
    ("인코더 입력 임베딩 100x15,000", E * V, FWD, "본문"),
    ("인코더 W · W_r · W_z (1,000x100 셋)", 3 * N * E, FWD, "본문"),
    ("인코더 U · U_r · U_z (1,000x1,000 셋)", 3 * N * N, FWD, "본문"),
    ("c = tanh(V h<T>) 의 V", N * N, CODE, "가정"),
    ("디코더 입력 임베딩 100x15,000", E * V, REV, "본문"),
    ("디코더 W · W_r · W_z", 3 * N * E, REV, "본문"),
    ("디코더 U · U_r · U_z", 3 * N * N, REV, "본문"),
    ("디코더가 c 를 받는 C · C_r · C_z", 3 * N * N, CODE, "가정"),
    ("디코더 첫 상태 h<0> = tanh(V' c) 의 V'", N * N, CODE, "가정"),
    ("maxout 층 입력 (h, y_{t-1}, c) -> 1,000", 2 * MO * (N + E + N), REV, "본문"),
    ("출력 낮은 계수 500x100 + 100x15,000", MO * E + E * V, REV, "본문"),
]
tot = sum(p[1] for p in parts)
assumed = sum(p[1] for p in parts if p[3] == "가정")
full_in = 3 * N * V          # 한쪽 입력을 낮은 계수로 줄이지 않았다면
low_in = E * V + 3 * N * E
full_out = MO * V
low_out = MO * E + E * V
print("  [그림 5] 합계 %d, 가정 몫 %d, 가정 빼면 %d" % (tot, assumed, tot - assumed))
print("  [그림 5] 입력 한쪽: 전 계수 %d 대 낮은 계수 %d (%.1f 배)" % (full_in, low_in, full_in / low_in))
print("  [그림 5] 출력: 전 계수 %d 대 낮은 계수 %d (%.2f 배)" % (full_out, low_out, full_out / low_out))
W, H = 900, 470
b = txt(20, 30, "실험 모델의 파라미터 수 — 내가 센 것. 바이어스는 원문 식에 없어 넣지 않았다. 「가정」 줄은 학회판 본문만으로 정해지지 않는 자리", 13, anchor="start", weight="bold")
sx = lambda v: 360 + v / 3.2e6 * 380
for j, (name, v, c, kind) in enumerate(parts):
    y = 62 + 28 * j
    b += txt(350, y + 14, name, 11, anchor="end", fill=INK2)
    b += box(360, y, sx(v) - 360, 18, CODE_SOFT if kind == "가정" else (FWD_SOFT if c == FWD else REV_SOFT), c, 1, rx=2,
             dash="4 2" if kind == "가정" else None)
    b += txt(sx(v) + 6, y + 14, "{:,}".format(v) + ("  (가정)" if kind == "가정" else ""), 11, anchor="start", fill=c)
y = 62 + 28 * len(parts) + 18
b += txt(40, y, "합계 {:,} ({:.2f}백만). 가정 셋을 모두 빼면 {:,}. 곧 이 모델은 {:.2f} ~ {:.2f}백만 사이다".format(
    tot, tot / 1e6, tot - assumed, (tot - assumed) / 1e6, tot / 1e6), 12, anchor="start", weight="bold")
b += txt(40, y + 24, "낮은 계수의 몫: 입력 한쪽을 전 계수(1,000x15,000 셋)로 두면 {:,} — 지금의 {:,} 의 {:.0f} 배. 출력은 {:,} 대 {:,} ({:.2f} 배)".format(
    full_in, low_in, full_in / low_in, full_out, low_out, full_out / low_out), 11, anchor="start", fill=INK2)
b += txt(40, y + 46, "원문: 「입력 행렬과 출력 행렬을 계수 100 행렬 둘로 근사했다 — 단어마다 100 차원 임베딩을 배우는 것과 같다」(4.1.1절). 나머지 구조는 보충 자료로 미룬다", 11, anchor="start", fill=MUTED)
svg("fig05_param_count", W, H, b, "실험 모델 파라미터 세기")

# ── 그림 6. 층 하나의 파라미터 — tanh · 게이트 유닛 · LSTM ───────────────────────
n_in, n_h = 100, 1000
one = n_in * n_h + n_h * n_h
units = [("게이트 없는 tanh", 1, INK2), ("제안 유닛 (게이트 둘)", 3, REV), ("LSTM (게이트 셋 + 셀 입력)", 4, FWD)]
print("  [그림 6] 무게 행렬 묶음 하나 = %d, tanh %d / 제안 %d / LSTM %d" % (one, one, 3 * one, 4 * one))
W, H = 900, 300
b = txt(20, 30, "층 하나(입력 100, 은닉 1,000)의 무게 수 — 내가 센 것. 무게 묶음 (W, U) 하나 = 100x1,000 + 1,000x1,000 = 1,100,000", 13, anchor="start", weight="bold")
for j, (name, k, c) in enumerate(units):
    y = 70 + 55 * j
    b += txt(250, y + 22, name, 12, anchor="end", fill=c, weight="bold")
    b += box(260, y, k * one / 4.4e6 * 520, 32, NODE, c, 1.4, rx=3)
    b += txt(260 + k * one / 4.4e6 * 520 + 8, y + 22, "{} 묶음 = {:,}".format(k, k * one), 12, anchor="start", fill=c)
b += txt(40, 255, "제안 유닛 / LSTM = 3/4 = 0.75. 바이어스 둘씩을 넣는 PyTorch 의 nn.GRU(100, 1000) 는 3,306,000, nn.LSTM(100, 1000) 은 4,408,000 (내가 세어 맞춘 값)", 11, anchor="start", fill=INK2)
b += txt(40, 278, "원문 각주 1 은 LSTM 을 「기억 셀과 게이트 넷」, 제안 유닛을 「게이트 둘」 로 센다 — LSTM 의 넷은 게이트 셋에 셀 입력을 더한 셈으로 읽힌다", 11, anchor="start", fill=MUTED)
svg("fig06_unit_param_compare", W, H, b, "층 하나의 무게 수 비교")

# ── 그림 7. 재설정 게이트를 곱하는 자리 — 원문 식 (8) 대 PyTorch ──────────────────
U2 = [[1.0, 1.0], [0.0, 1.0]]
h2 = [1.0, 1.0]
r2 = [0.0, 1.0]
mv = lambda M, v: [sum(M[i][j] * v[j] for j in range(2)) for i in range(2)]
paper = mv(U2, [r2[i] * h2[i] for i in range(2)])
torch_ = [r2[i] * mv(U2, h2)[i] for i in range(2)]
print("  [그림 7] 원문 U(r⊙h) =", paper, " PyTorch r⊙(Uh) =", torch_)
W, H = 900, 300
b = txt(20, 30, "재설정 게이트를 어디서 곱하나 — 원문 식 (8) 은 행렬 곱 전에, PyTorch nn.GRU 는 행렬 곱 뒤에 곱한다 (내가 고른 2 차원 예)", 13, anchor="start", weight="bold")
b += lines_at(40, 75, [("U = [[1, 1], [0, 1]],  h<t-1> = (1, 1),  r = (0, 1)", INK, "bold"), ("", INK2),
                        ("원문 식 (8):   U (r ⊙ h) = U (0, 1) = (%g, %g)" % tuple(paper), REV, "bold"),
                        ("    유닛 1 의 재설정(r1 = 0)이 유닛 1 의 옛 값만 지운다. 유닛 2 의 옛 값은 U 를 거쳐 유닛 1 에 들어온다", INK2),
                        ("", INK2),
                        ("PyTorch:       r ⊙ (U h) = (0, 1) ⊙ (2, 1) = (%g, %g)" % tuple(torch_), FWD, "bold"),
                        ("    유닛 1 이 받는 순환 입력 전체가 지워진다", INK2),
                        ("", INK2),
                        ("유닛이 하나면(U 가 수 하나) 두 꼴이 같다. 둘 이상이고 U 가 유닛끼리 섞을 때만 갈린다", MUTED),
                        ("원문 꼴은 r 을 먼저 구해야 U 를 곱할 수 있다. PyTorch 꼴은 U_r h · U_z h · U h 를 한 번의 행렬 곱으로 묶을 수 있다 (내 정리, 원문에 없다)", MUTED)], 12, 22)
svg("fig07_reset_placement", W, H, b, "재설정 게이트 곱하는 자리 두 꼴")

# ── 그림 8. 실험이 RNN 을 쓰는 자리 — 구문 기반 SMT 의 로그 선형 모형 ─────────────────
W, H = 900, 380
b = defs()
b += txt(20, 30, "실험에서 RNN 인코더-디코더가 하는 일 (3 · 3.1 · 4.2절) — 번역을 만들지 않는다. 구문표의 짝마다 점수 한 칸을 더한다", 14, anchor="start", weight="bold")
b += box(40, 70, 300, 150, FWD_SOFT, FWD)
b += txt(190, 92, "구문표 (348M 단어에서 만든 것)", 12, fill=FWD, weight="bold")
b += lines_at(55, 118, [("영어 구문  |  프랑스어 구문  |  기존 점수들 ...", INK2),
                         ("at the end of the | à la fin de la | ...", INK2),
                         ("for the first time | pour la première fois | ...", INK2)], 11, 22)
b += box(240, 175, 90, 36, REV_SOFT, REV)
b += txt(285, 198, "+ RNN 점수", 11, fill=REV, weight="bold")
b += box(40, 260, 300, 70, REV_SOFT, REV)
b += txt(190, 285, "RNN 인코더-디코더", 12, fill=REV, weight="bold")
b += txt(190, 307, "구문 짝을 빈도 없이 고르게 뽑아 학습, 64 짝씩", 11, fill=INK2)
b += line(285, 257, 285, 214, REV, 1.4, marker="ar")
b += box(400, 70, 250, 110, NODE, INK2)
b += txt(525, 95, "로그 선형 모형 식 (9)", 12, weight="bold")
b += txt(525, 120, "log p(f|e) = Σ w_n f_n(f, e) + log Z(e)", 11, fill=INK2)
b += txt(525, 145, "w_n 은 개발 셋 BLEU 로 MERT 가 맞춘다", 11, fill=INK2)
b += txt(525, 166, "(newstest2012 · 2013)", 10, fill=MUTED)
b += line(342, 130, 397, 130, INK2, 1.4, marker="ai")
b += box(400, 210, 250, 60, CODE_SOFT, CODE)
b += txt(525, 235, "CSLM (목표어 신경망 언어 모형)", 11, fill=CODE, weight="bold")
b += txt(525, 255, "디코딩 중 부분 번역에 점수", 10, fill=INK2)
b += line(525, 207, 525, 183, CODE, 1.2, marker="ac")
b += box(400, 290, 250, 44, NODE, INK2, dash="4 3")
b += txt(525, 317, "단어 벌점 WP = 미등록 단어 수 (각주 3)", 11, fill=INK2)
b += line(652, 310, 700, 160, INK2, 1, dash="4 3", marker="ai")
b += box(700, 100, 170, 80, OK_SOFT, OK)
b += txt(785, 128, "Moses 디코더", 12, fill=OK, weight="bold")
b += txt(785, 150, "-> 시험 셋 BLEU", 11, fill=INK2)
b += txt(785, 168, "(newstest2014, 참조 하나)", 10, fill=MUTED)
b += line(652, 130, 697, 130, INK2, 1.4, marker="ai")
b += txt(450, 365, "그래서 표 1 의 BLEU 는 「RNN 인코더-디코더의 번역 품질」 이 아니라 「기존 SMT 에 점수 한 칸을 더한 결과」 다", 12, fill=REV, weight="bold")
svg("fig08_smt_pipeline", W, H, b, "SMT 안에서 RNN 점수가 들어가는 자리")

# ── 그림 9. 표 1 — BLEU 와 차이 ────────────────────────────────────────────────
T1 = [("Baseline", 30.64, 33.30), ("RNN", 31.20, 33.87), ("CSLM + RNN", 31.48, 34.64), ("CSLM + RNN + WP", 31.50, 34.54)]
for i in range(1, len(T1)):
    print("  [그림 9] %s - %s: dev %+.2f, test %+.2f" % (T1[i][0], T1[i - 1][0], T1[i][1] - T1[i - 1][1], T1[i][2] - T1[i - 1][2]))
print("  [그림 9] CSLM+RNN - Baseline: dev %+.2f, test %+.2f" % (T1[2][1] - T1[0][1], T1[2][2] - T1[0][2]))
W, H = 900, 430
b = txt(20, 30, "표 1 다시 그림 — 줄마다 한 번 돌린 값. 맨 아래 칸 「Baseline + CSLM」 은 원문에 없다", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 90, 560, 60, 340
fy = lambda v: Y1 - (v - 30) / 5.0 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [], [30, 31, 32, 33, 34, 35], lambda v: 0, fy, None, "BLEU (축은 30 에서 시작)")
rows = T1 + [("Baseline + CSLM", None, None)]
for i, (name, dv, ts) in enumerate(rows):
    cx = X0 + 50 + i * 95
    if dv is None:
        b += box(cx - 30, Y0 + 40, 60, Y1 - Y0 - 40, NODE, NO, 1.4, rx=2, dash="5 4")
        b += txt(cx, Y0 + 140, "없다", 13, fill=NO, weight="bold")
    else:
        b += box(cx - 30, fy(dv), 28, Y1 - fy(dv), FWD_SOFT, FWD, 1, rx=1)
        b += box(cx + 2, fy(ts), 28, Y1 - fy(ts), REV_SOFT, REV, 1, rx=1)
        b += txt(cx - 16, fy(dv) - 5, "%.2f" % dv, 10, fill=FWD)
        b += txt(cx + 16, fy(ts) - 5, "%.2f" % ts, 10, fill=REV)
    b += txt(cx, Y1 + 18, name, 10, fill=INK2)
b += lines_at(590, 80, [("파랑 = 개발(dev), 주황 = 시험(test)", INK2, "bold"), ("", INK2),
                         ("차이 (내가 뺀 값)", INK, "bold"),
                         ("RNN - Baseline:  dev +0.56, test +0.57", INK2),
                         ("CSLM+RNN - RNN:  dev +0.28, test +0.77", INK2),
                         ("+WP - CSLM+RNN:  dev +0.02, test -0.10", INK2),
                         ("CSLM+RNN - Baseline: dev +0.84, test +1.34", INK2), ("", INK2),
                         ("CSLM 혼자의 줄이 없어서", NO, "bold"),
                         ("「두 몫이 서로 겹치지 않는다」 를", NO),
                         ("이 표로는 셈할 수 없다", NO), ("", INK2),
                         ("반복 · 흩어짐 · 유의성 검정: 적혀 있지 않다", MUTED),
                         ("개발 셋은 MERT 가 무게를 맞춘 셋이다", MUTED)], 12, 21)
svg("fig09_table1_bleu", W, H, b, "표 1 BLEU 와 빠진 칸")

# ── 그림 10. 데이터 — 말뭉치 단어 수 더하기 ───────────────────────────────────────
corp = [("Europarl", 61), ("news commentary", 5.5), ("UN", 421), ("크롤 1", 90), ("크롤 2", 780)]
bitext = sum(v for _, v in corp)
lm_pool = 712 + bitext
print("  [그림 10] 양국어 말뭉치 합 %.1fM, 언어 모형 풀 %.1fM, 418/풀 = %.3f, 348/850 = %.3f" % (bitext, lm_pool, 418 / lm_pool, 348 / 850))
print("  [그림 10] UN 과 크롤 1 을 빼면 %.1fM" % (bitext - 421 - 90))
W, H = 900, 380
b = txt(20, 30, "4.1절의 단어 수를 더해 본 것 — 단위는 백만 단어(M), 토큰화 뒤 프랑스어 단어 수 (원문)", 14, anchor="start", weight="bold")
sx = lambda v: 60 + v / 2100 * 620
x = 60
for name, v in corp:
    b += box(x, 70, sx(v) - 60, 34, FWD_SOFT, FWD, 1, rx=0)
    if v > 200:
        b += txt(x + (sx(v) - 60) / 2, 92, "%s %gM" % (name, v), 10, fill=FWD)
    x += sx(v) - 60
b += txt(x + 8, 92, "합 %.1fM" % bitext, 12, anchor="start", fill=FWD, weight="bold")
b += txt(60, 124, "막대 왼쪽 끝의 좁은 셋은 차례로 Europarl 61M · news commentary 5.5M, UN 뒤의 좁은 칸이 크롤 1 90M", 10, anchor="start", fill=MUTED)
b += box(60, 150, sx(850) - 60, 30, NODE, REV, 1.4, rx=0, dash="5 3")
b += box(60, 150, sx(348) - 60, 30, REV_SOFT, REV, 1.2, rx=0)
b += txt(sx(850) + 8, 170, "RNN 학습: 「850M 가운데 348M」 = %.1f%%" % (100 * 348 / 850), 11, anchor="start", fill=REV, weight="bold")
b += txt(60, 200, "원문의 850M 은 위 다섯의 합 %.1fM 과 다르다. 원문은 무엇을 뺐는지 적지 않는다 (UN 과 크롤 1 을 빼면 %.1fM — 내가 맞춰 본 조합일 뿐)" % (bitext, bitext - 421 - 90), 11, anchor="start", fill=NO)
b += box(60, 230, sx(lm_pool) - 60, 30, NODE, CODE, 1.4, rx=0, dash="5 3")
b += box(60, 230, sx(418) - 60, 30, CODE_SOFT, CODE, 1.2, rx=0)
b += txt(sx(418) + 6, 250, "언어 모형: 「2G 넘는 것 가운데 418M」", 11, anchor="start", fill=CODE, weight="bold")
b += txt(60, 280, "신문 712M + 양국어 목표 쪽 %.1fM = %.1fM — 「2G 넘는다」 와 맞는다. 418M 은 그 %.1f%%" % (bitext, lm_pool, 100 * 418 / lm_pool), 11, anchor="start", fill=INK2)
b += txt(60, 320, "어휘: 두 언어 모두 가장 잦은 15,000 단어 (데이터의 93% 를 덮는다 — 원문은 approximately). 나머지는 [UNK] 하나로", 11, anchor="start", fill=INK2)
b += txt(60, 344, "개발 · 시험 셋: 각각 7만 단어 넘음, 참조 번역 하나 (원문)", 11, anchor="start", fill=INK2)
svg("fig10_data_budget", W, H, b, "말뭉치 단어 수 더하기")

# ── 그림 11. 원문 그림 3 — 점 5,000 개를 다시 그리고 상관을 낸다 ───────────────────
pts = []
with open(os.path.join(OUT, "paper_fig3_points.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        pts.append((float(row["rnn_log_score"]), float(row["tm_log_score"])))
xs = [p[0] for p in pts]
ys = [p[1] for p in pts]


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2.0
        i = j + 1
    return r


def pear(a, c):
    ma, mc = st.mean(a), st.mean(c)
    return sum((x - ma) * (y - mc) for x, y in zip(a, c)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mc) ** 2 for y in c))


rp = pear(xs, ys)
rs = pear(rank(xs), rank(ys))
levels = {0: 0, 1: 0, 2: 0, 3: 0}
for y in ys:
    for k in levels:
        if abs(y - math.log(1.0 / (k + 1))) < 0.02:
            levels[k] += 1
on_levels = sum(levels.values())
qx = st.quantiles(xs, n=4)
qy = st.quantiles(ys, n=4)
print("  [그림 11] 점 %d, 피어슨 %.3f, 스피어먼 %.3f" % (len(pts), rp, rs))
print("  [그림 11] 구문표 점수 log1·log1/2·log1/3·log1/4 위 점:", levels, "합", on_levels)
print("  [그림 11] RNN 사분위", [round(v, 2) for v in qx], " 구문표 사분위", [round(v, 2) for v in qy])
print("  [그림 11] RNN 범위 %.2f ~ %.2f, 구문표 범위 %.2f ~ %.2f" % (min(xs), max(xs), min(ys), max(ys)))
W, H = 900, 470
b = txt(20, 30, "원문 그림 3 의 점 5,000 개를 PDF 벡터 그림에서 읽어 다시 그린 것 — 상관은 내가 낸 값", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 560, 60, 400
fx = lambda v: X0 + (v + 60) / 60 * (X1 - X0)
fy = lambda v: Y1 - (v + 14) / 14 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [-60, -50, -40, -30, -20, -10, 0], [-14, -12, -10, -8, -6, -4, -2, 0], fx, fy,
          "RNN 점수 (로그 확률, 목표 구문 전체)", "구문표 점수 p(f|e) 의 로그")
dots = "".join('<circle cx="%.1f" cy="%.1f" r="1.1"/>' % (fx(x), fy(y)) for x, y in pts)
b += '<g fill="%s" opacity="0.35">%s</g>' % (INK, dots)
for k, lab in enumerate(["log 1", "log 1/2", "log 1/3", "log 1/4"]):
    yy = fy(math.log(1.0 / (k + 1)))
    ly = Y0 + 4 + 15 * k
    b += path("M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f" % (X1 + 2, yy, X1 + 10, ly, X1 + 16, ly), REV, sw=1)
    b += txt(X1 + 20, ly + 4, "%s: %d 점" % (lab, levels[k]), 10, anchor="start", fill=REV)
b += lines_at(640, 150, [("점 수: %d (원문 캡션에 없음)" % len(pts), INK, "bold"),
                          ("피어슨 상관: %.3f" % rp, NO, "bold"),
                          ("스피어먼 순위 상관: %.3f" % rs, NO, "bold"), ("", INK2),
                          ("구문표 점수가 1 · 1/2 · 1/3 · 1/4", REV),
                          ("네 값에 놓인 점: %d (%.1f%%)" % (on_levels, 100.0 * on_levels / len(pts)), REV), ("", INK2),
                          ("RNN 점수 중앙값 %.2f" % qx[1], INK2),
                          ("구문표 점수 중앙값 %.2f" % qy[1], INK2), ("", INK2),
                          ("두 축의 범위가 다르다:", MUTED),
                          ("RNN %.1f ~ %.1f, 구문표 %.1f ~ 0" % (min(xs), max(xs), min(ys)), MUTED)], 12, 21)
b += txt(450, 455, "읽기 오차: 축 틀 좌표로 옮긴 값이라 표시 하나의 반 폭(가로 0.36, 세로 0.11 로그 단위) 안. 겹친 표시는 하나로 보인다 (서로 다른 자리 4,534 곳)", 10, fill=MUTED)
svg("fig11_fig3_scatter", W, H, b, "원문 그림 3 점 다시 그리기와 상관")

# ── 그림 12. 미등록 단어 — 구문 길이별 [UNK] 이 하나라도 들 몫 ─────────────────────
cover = 0.93
W, H = 900, 360
b = txt(20, 30, "어휘 15,000 이 단어의 93% 를 덮을 때 — 구문에 [UNK] 이 하나라도 들 몫 (단어마다 따로라고 둔 내 계산)", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 560, 60, 300
fx = lambda n: X0 + (n - 1) / 9 * (X1 - X0)
fy = lambda v: Y1 - v / 0.6 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, list(range(1, 11)), [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], fx, fy, "구문 길이 (단어)", "1 - 0.93^n")
vals = [(n, 1 - cover ** n) for n in range(1, 11)]
b += polyline([(fx(n), fy(v)) for n, v in vals], NO, 2.2)
for n, v in vals:
    b += circ(fx(n), fy(v), 3.5, NO_SOFT, NO, 1.2)
    if n in (1, 4, 7, 10):
        b += txt(fx(n), fy(v) - 9, "%.1f%%" % (100 * v), 10, fill=NO)
print("  [그림 12]", [(n, round(v, 3)) for n, v in vals])
b += lines_at(600, 90, [("단어 하나: 7.0%", INK2), ("네 단어: %.1f%%" % (100 * (1 - cover ** 4)), INK2),
                         ("일곱 단어: %.1f%%" % (100 * (1 - cover ** 7)), INK2), ("", INK2),
                         ("각주 3: [UNK] 의 확률은 어휘 밖", INK2),
                         ("단어 전부의 합이라 늘 크게 잡힌다", INK2),
                         ("-> 단어 벌점(WP)으로 맞서려 했고", INK2),
                         ("   시험 셋에서는 -0.10", NO, "bold"), ("", INK2),
                         ("단어마다 따로라는 가정은 내 것.", MUTED), ("실제 미등록 단어는 몰려 나온다", MUTED)], 12, 21)
svg("fig12_unk_rate", W, H, b, "구문 길이별 미등록 단어 몫")

# ── 그림 13. 표 2 — 원문 표를 옮겨 낱말 수를 센다 ────────────────────────────────
# (영어 구문, [구문표 상위], [RNN 상위]). 깨진 글자는 원문 그대로 '?' · '©' · 'r' 로 두었다.
T2 = [
    ("a", "at the end of the", ["a la fin de la", "f la fin des années", "être supprimés à la fin de la"],
     ["à la fin du", "à la fin des", "à la fin de la"]),
    ("a", "for the first time", ["r © pour la premirëre fois", "été donnés pour la première fois", "été commémorée pour la première fois"],
     ["pour la première fois", "pour la première fois ,", "pour la première fois que"]),
    ("a", "in the United States and", ["? aux ?tats-Unis et", "été ouvertes aux États-Unis et", "été constatées aux États-Unis et"],
     ["aux Etats-Unis et", "des Etats-Unis et", "des États-Unis et"]),
    ("a", ", as well as", ["?s , qu'", "?s , ainsi que", "?re aussi bien que"], [", ainsi qu'", ", ainsi que", ", ainsi que les"]),
    ("a", "one of the most", ["?t ?l' un des plus", "?l' un des plus", "être retenue comme un de ses plus"], ["l' un des", "le", "un des"]),
    ("b", ", Minister of Communications and Transport", ["Secrétaire aux communications et aux transports :", "Secrétaire aux communications et aux transports"],
     ["Secrétaire aux communications et aux transports", "Secrétaire aux communications et aux transports :"]),
    ("b", "did not comply with the", ["vestimentaire , ne correspondaient pas à des", "susmentionnée n' était pas conforme aux", "présentées n' étaient pas conformes à la"],
     ["n' ont pas respecté les", "n' était pas conforme aux", "n' ont pas respecté la"]),
    ("b", "parts of the world .", ["© gions du monde .", "régions du monde considérées .", "région du monde considérée ."],
     ["parties du monde .", "les parties du monde .", "des parties du monde ."]),
    ("b", "the past few days .", ["le petit texte .", "cours des tout derniers jours .", "les tout derniers jours ."],
     ["ces derniers jours .", "les derniers jours .", "cours des derniers jours ."]),
    ("b", "on Friday and Saturday", ["vendredi et samedi à la", "vendredi et samedi à", "se déroulera vendredi et samedi ,"],
     ["le vendredi et le samedi", "le vendredi et samedi", "vendredi et samedi"]),
]
nw = lambda s: len(s.split())
broken = lambda s: any(c in s for c in "?©") or s.startswith("r ") or s.startswith("f ")
src_len = [nw(r[1]) for r in T2]
tm_all = [nw(p) for r in T2 for p in r[2]]
rnn_all = [nw(p) for r in T2 for p in r[3]]
tm_broken = sum(broken(p) for r in T2 for p in r[2])
rnn_broken = sum(broken(p) for r in T2 for p in r[3])
shorter = sum(1 for r in T2 if st.mean(nw(p) for p in r[3]) < st.mean(nw(p) for p in r[2]))
print("  [그림 13] 영어 구문 길이:", src_len, " 최소", min(src_len))
print("  [그림 13] 구문표 상위 %d 개 평균 %.2f 단어, RNN 상위 %d 개 평균 %.2f 단어" % (len(tm_all), st.mean(tm_all), len(rnn_all), st.mean(rnn_all)))
print("  [그림 13] RNN 평균이 더 짧은 줄 %d / %d, 깨진 글자 든 구문: 구문표 %d, RNN %d" % (shorter, len(T2), tm_broken, rnn_broken))
W, H = 900, 470
b = txt(20, 30, "표 2 를 옮겨 센 것 — 줄마다 상위 구문의 평균 낱말 수 (띄어쓰기로 셈, 문장 부호도 한 낱말)", 14, anchor="start", weight="bold")
X0, X1 = 300, 640
sx = lambda v: X0 + v / 8 * (X1 - X0)
for t in range(0, 9, 2):
    b += line(sx(t), 60, sx(t), 420, LINE, 0.8, dash="2 3") + txt(sx(t), 435, "%d" % t, 10, fill=MUTED)
for j, (grp, src, tm, rn) in enumerate(T2):
    y = 70 + 35 * j + (14 if grp == "b" else 0)
    b += txt(290, y + 12, "%s (%d)" % (src, nw(src)), 11, anchor="end", fill=INK2)
    mt, mr = st.mean(nw(p) for p in tm), st.mean(nw(p) for p in rn)
    b += box(X0, y, sx(mt) - X0, 11, FWD_SOFT, FWD, 1, rx=1)
    b += box(X0, y + 13, sx(mr) - X0, 11, REV_SOFT, REV, 1, rx=1)
    b += txt(sx(mt) + 4, y + 10, "%.2f%s" % (mt, "  (깨진 글자 %d)" % sum(broken(p) for p in tm) if any(broken(p) for p in tm) else ""), 9, anchor="start", fill=FWD)
    b += txt(sx(mr) + 4, y + 23, "%.2f" % mr, 9, anchor="start", fill=REV)
b += txt(20, 66, "(a) 잦은", 11, anchor="start", fill=MUTED, weight="bold")
b += txt(20, 66 + 35 * 5 + 14, "(b) 드문", 11, anchor="start", fill=MUTED, weight="bold")
b += lines_at(670, 90, [("파랑 = 구문표 상위", FWD, "bold"), ("주황 = RNN 상위", REV, "bold"), ("", INK2),
                         ("평균 (구문 %d 개씩):" % len(tm_all), INK, "bold"),
                         ("구문표 %.2f 낱말" % st.mean(tm_all), FWD),
                         ("RNN    %.2f 낱말" % st.mean(rnn_all), REV),
                         ("RNN 이 짧은 줄: %d / %d" % (shorter, len(T2)), INK2), ("", INK2),
                         ("깨진 글자 든 구문:", INK, "bold"),
                         ("구문표 %d / %d, RNN %d / %d" % (tm_broken, len(tm_all), rnn_broken, len(rnn_all)), INK2), ("", INK2),
                         ("영어 구문 길이 최소 %d" % min(src_len), INK2),
                         ("-> 캡션 「4 낱말 이상」 과 맞고", INK2),
                         ("본문 「4 나 5 낱말 넘는」 과 어긋남", NO),
                         ("", INK2), ("「상위 셋」 인데 Minister 줄은 둘", NO)], 11, 20)
svg("fig13_table2_lengths", W, H, b, "표 2 낱말 수와 깨진 글자 세기")

# ── 그림 14. 표 3 — 표본 50 개 가운데 보인 것 ─────────────────────────────────────
T3 = [("a", "at the end of the", [("à la fin de la", 11)]),
      ("a", "for the first time", [("pour la première fois", 24), ("pour la première fois que", 2)]),
      ("a", "in the United States and", [("aux États-Unis et", 6), ("dans les États-Unis et", 4)]),
      ("a", ", as well as", [(", ainsi que", 1), (",", 1), ("ainsi que", 1), (", ainsi qu'", 1), ("et UNK", 1)]),
      ("a", "one of the most", [("l' un des plus", 9), ("l' un des", 5), ("l' une des plus", 2)]),
      ("b", ", Minister of Communications and Transport", [(", ministre des communications et le transport", 13)]),
      ("b", "did not comply with the", [("n' tait pas conforme aux", 1), ("n' a pas respect l'", 2), ("n' a pas respect la", 3)]),
      ("b", "parts of the world .", [("arts du monde .", 11), ("des arts du monde .", 7)]),
      ("b", "the past few days .", [("quelques jours .", 5), ("les derniers jours .", 5), ("ces derniers jours .", 2)]),
      ("b", "on Friday and Saturday", [("vendredi et samedi", 5), ("le vendredi et samedi", 7), ("le vendredi et le samedi", 4)])]
shown = [sum(c for _, c in r[2]) for r in T3]
print("  [그림 14] 줄마다 보인 표본 수 (50 개 중):", shown, " 보인 서로 다른 구문 수:", [len(r[2]) for r in T3])
W, H = 900, 450
b = txt(20, 30, "표 3 을 옮겨 센 것 — 영어 구문마다 표본 50 개. 원문이 보인 구문의 횟수 합이 50 가운데 얼마인가", 14, anchor="start", weight="bold")
X0, X1 = 300, 640
sx = lambda v: X0 + v / 50 * (X1 - X0)
for t in range(0, 51, 10):
    b += line(sx(t), 60, sx(t), 410, LINE, 0.8, dash="2 3") + txt(sx(t), 425, "%d" % t, 10, fill=MUTED)
for j, (grp, src, items) in enumerate(T3):
    y = 66 + 33 * j + (14 if grp == "b" else 0)
    b += txt(290, y + 13, src, 11, anchor="end", fill=INK2)
    x = X0
    for k, (ph, c) in enumerate(items):
        bad = ph.startswith("arts") or ph.startswith("des arts")
        b += box(x, y, sx(c) - X0, 18, NO_SOFT if bad else REV_SOFT, NO if bad else REV, 1, rx=0)
        x += sx(c) - X0
    b += line(x, y, sx(50), y + 18, LINE, 0)
    b += box(x, y, sx(50) - x, 18, NODE, LINE, 1, rx=0, dash="3 3")
    b += txt(sx(50) + 6, y + 13, "%d / 50 (구문 %d)" % (shown[j], len(items)), 10, anchor="start", fill=INK2)
b += txt(20, 62, "(a) 잦은", 11, anchor="start", fill=MUTED, weight="bold")
b += txt(20, 62 + 33 * 5 + 14, "(b) 드문", 11, anchor="start", fill=MUTED, weight="bold")
b += txt(450, 444, "빨강 = parts 를 arts 로 옮긴 표본 (11 + 7 = 18 / 50). 점선 = 원문이 보이지 않은 표본. 캡션은 「상위 다섯 구문」 인데 보인 구문은 1 ~ 5 개", 11, fill=NO)
svg("fig14_table3_samples", W, H, b, "표 3 표본 수 세기")

# ── 그림 15. 주장과 근거의 세기 ────────────────────────────────────────────────
claims = [
    ("제안 유닛이 꼭 필요했다 (2.3절)", "예비 실험, 수 없음. 「게이트 없는 tanh 로는 의미 있는 결과를 못 얻었다」 한 문장", NO),
    ("유닛마다 다른 시간 척도를 배운다 (2.3절)", "재지 않았다. 게이트 값의 분포 · 그림 없음", NO),
    ("RNN 점수가 번역 성능을 올린다 (4.2절)", "시험 BLEU +0.57, 실행 하나, 시험 셋 하나, 흩어짐 · 검정 없음", CODE),
    ("CSLM 과 RNN 의 몫이 「너무 상관되지는 않는다」 (4.2절)", "CSLM 혼자의 줄이 없다. 더하기 꼴을 셈할 수 없다", NO),
    ("-> 결론: 「rather orthogonal」 (5절)", "같은 표 1 하나. 4.2절의 「시사한다」 가 결론에서 단정이 된다", NO),
    ("RNN 이 고른 구문이 문자 그대로의 번역에 더 가깝다 (4.3절)", "영어 구문 10 개, 세 개씩. 판정 기준 없음. [le] 같은 반례가 표 안에 있다", CODE),
    ("의미 · 문법 구조를 둘 다 잡는다 (요약 · 4.4절)", "t-SNE 그림 둘. 무리를 수로 잰 값 없음", CODE),
]
W, H = 900, 400
b = txt(20, 30, "주장과 그 근거 — 근거 칸은 원문에서 그 주장을 받치는 것 전부 (내가 정리한 것)", 14, anchor="start", weight="bold")
for j, (c, e, col) in enumerate(claims):
    y = 60 + 46 * j
    b += box(30, y, 350, 36, NODE, col, 1.4)
    b += txt(40, y + 23, c, 11, anchor="start", fill=INK)
    b += line(382, y + 18, 405, y + 18, INK2, 1)
    b += txt(412, y + 23, e, 11, anchor="start", fill=col)
b += txt(450, 390, "빨강 = 근거가 수로 없음 또는 주장을 셈할 칸이 빠짐. 노랑 = 수는 있으나 반복 · 기준이 없음", 11, fill=MUTED)
svg("fig15_claim_strength", W, H, b, "주장과 근거의 세기")

# ── 그림 16. 계보 ─────────────────────────────────────────────────────────────
W, H = 900, 360
b = defs()
b += txt(20, 30, "계보 — 이 편의 두 몫(인코더-디코더 틀, 게이트 둘 유닛)이 어디서 와서 어디로 가나", 14, anchor="start", weight="bold")
nodes = [
    (40, 70, "Elman 1990 · 단순 순환망", FWD_SOFT, FWD),
    (40, 140, "LSTM 1997 (게이트 + 셀)", FWD_SOFT, FWD),
    (40, 210, "Schwenk 2012 (앞먹임 구문 점수, 7 단어 고정)", FWD_SOFT, FWD),
    (40, 280, "Kalchbrenner · Blunsom 2013 (합성곱 인코더)", FWD_SOFT, FWD),
    (350, 160, "이 편 · EMNLP 2014", REV_SOFT, REV),
    (620, 70, "seq2seq · Sutskever 외 NIPS 2014", OK_SOFT, OK),
    (620, 160, "Bahdanau 외 ICLR 2015 (주의)", OK_SOFT, OK),
    (620, 250, "Chung 외 2014 (「GRU」 이름, 견주기)", CODE_SOFT, CODE),
]
for x, y, t, f, c in nodes:
    b += box(x, y, 250, 40, f, c, 1.4)
    b += txt(x + 125, y + 25, t, 11, fill=c, weight="bold")
for (x1, y1, x2, y2) in [(290, 90, 348, 170), (290, 160, 348, 176), (290, 230, 348, 186), (290, 300, 348, 194)]:
    b += line(x1, y1, x2, y2, INK2, 1.2, marker="ai")
for (x2, y2) in [(618, 90), (618, 180), (618, 270)]:
    b += line(600, 180, x2, y2, REV, 1.2, marker="ar")
b += txt(475, 225, "벡터 c 하나에 입력 전체", 10, fill=REV)
b += txt(745, 125, "같은 틀, LSTM, 번역을 직접 만든다", 10, fill=OK)
b += txt(745, 215, "c 하나의 병목을 푼다 (같은 연구실)", 10, fill=OK)
b += txt(450, 340, "오른쪽 칸 셋은 이 노트에서 읽지 않았다. 「GRU」 라는 이름이 Chung 외 2014 에서 붙었다는 것은 내가 아는 것이다", 11, fill=MUTED)
svg("fig16_lineage", W, H, b, "계보")

print("끝")
