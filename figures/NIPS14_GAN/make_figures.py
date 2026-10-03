# -*- coding: utf-8 -*-
"""원 GAN 노트(Goodfellow 외, NIPS 2014)의 그림 열여섯을 만든다.

색과 글꼴은 앞선 노트들(특히 CACM 2020 개관판 GAN 노트)의 그림과 맞췄다 — 저장소의 노트들이 한 벌로
읽히게 하려는 것이다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

원문의 식 (1)~(6) 을 수로 확인하는 그림이 여럿이다 — 그림 2(논문 그림 1 을 계산으로 다시 그림),
4(명제 1 의 점별 최대), 5(정리 1 의 KL 둘), 7(명제 2 의 볼록성: 섞기 방향 대 파라미터 방향),
8(포화), 10 · 11(Parzen 창 추정의 σ 와 차원). 계산한 값은 돌릴 때 화면에도 찍는다.
참값은 기댓값이 아니라 같은 시험 점에서 참 밀도로 잰 평균 로그 가능도다(시험 표본의 흔들림을 지운다).
논문 그림 2 · 3 의 표본 사진은 다시 그릴 수 없어 crop_paper_figures.py 가 원문에서 잘라 png 로 둔다.
"""
import io, os, math, random
from statistics import NormalDist

OUT = os.path.dirname(os.path.abspath(__file__))
random.seed(0)

BG        = "#ECEFEC"   # 그림 상자 배경
NODE      = "#F6F7F5"   # 노드 안쪽
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 판별기, 진짜 데이터 쪽
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 생성기, 가짜 데이터 쪽
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 잡음 z
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"   # 초록 — 된다
NO        = "#C0392B"   # 빨강 — 안 된다
# 분포 그림 계열 색 — 데이터 · 모델 · 판별기. 논문 그림 4 의 검정 · 초록 · 파랑 점선과 역할을 맞췄다.
S_DATA    = "#1C232C"
S_MODEL   = "#1E8449"
S_DISC    = "#2A78D6"
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
    return "<text %s>%s</text>" % (a, t.replace("&", "&amp;"))


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


def ell(cx, cy, rx, ry, fill="none", stroke=None, sw=1.2, dash=None, op=None):
    a = '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="%s"' % (
        cx, cy, rx, ry, fill, stroke or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
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


def polyline(pts, stroke, sw=2, dash=None):
    d = "M" + " L".join("%.1f,%.1f" % p for p in pts)
    return path(d, stroke, sw=sw, dash=dash)


def fmt(n):
    return "{:,}".format(n)


print("그림을 만든다 ->", OUT)

LN4 = math.log(4.0)
LN2 = math.log(2.0)


def npdf(x, m, s):
    return math.exp(-0.5 * ((x - m) / s) ** 2) / (s * math.sqrt(2 * math.pi))


GRID = [-12 + i * 0.005 for i in range(int(30 / 0.005) + 1)]   # -12 ~ 18, 수치 적분 격자
DX = 0.005


def kl(p, q):
    s = 0.0
    for x in GRID:
        a = p(x)
        if a > 1e-300:
            s += a * math.log(a / max(q(x), 1e-300))
    return s * DX


def jsd(p, q):
    m = lambda x: 0.5 * (p(x) + q(x))
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def v_direct(p, q):
    """V(D*, G) 를 식 (4) 의 넷째 줄 그대로 적분한다."""
    s = 0.0
    for x in GRID:
        a, c = p(x), q(x)
        if a > 1e-300:
            s += a * math.log(a / (a + c))
        if c > 1e-300:
            s += c * math.log(c / (a + c))
    return s * DX


def axes(x0, y0, x1, y1, xt, yt, fx, fy, xl=None, yl=None, xfmt="%g", yfmt="%g"):
    """눈금이 있는 축. fx, fy 는 값 -> 화면 좌표."""
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


# ── 그림 1. 가치 함수 식 (1) 의 두 항과 두 사람 ───────────────────────────────────
W, H = 860, 380
b = defs()
b += txt(20, 30, "식 (1) 의 가치 함수 V(D, G) — 판별기는 두 항을 함께 올리고, 생성기는 둘째 항만 움직여 내린다", 15, anchor="start", weight="bold")
b += txt(430, 72, "min_G  max_D  V(D, G)  =  E_{x~p_data}[ log D(x) ]  +  E_{z~p_z}[ log(1 − D(G(z))) ]", 15, weight="bold")
b += box(130, 92, 290, 96, fill=FWD_SOFT, stroke=FWD, sw=1.6)
b += txt(275, 118, "첫째 항: 진짜에 매긴 log D", 13, weight="bold", fill=FWD)
b += txt(275, 140, "진짜 x 에 D(x) → 1 이면 0 으로 올라간다", 12, fill=INK2)
b += txt(275, 160, "G 와 상관없다", 12, fill=INK2)
b += txt(275, 178, "(G 에 대한 기울기가 0)", 11, fill=MUTED)
b += box(450, 92, 300, 96, fill=REV_SOFT, stroke=REV, sw=1.6)
b += txt(600, 118, "둘째 항: 가짜에 매긴 log(1 − D)", 13, weight="bold", fill=REV)
b += txt(600, 140, "D 는 D(G(z)) → 0 으로 올리고", 12, fill=INK2)
b += txt(600, 160, "G 는 D(G(z)) → 1 로 내린다", 12, fill=INK2)
b += txt(600, 178, "두 사람이 함께 움직이는 유일한 자리", 11, fill=MUTED)
b += box(40, 214, 380, 140, fill=NODE, stroke=LINE)
b += txt(55, 238, "작은 예시 (내가 고른 수)", 13, anchor="start", weight="bold")
ex_v = math.log(0.9) + math.log(1 - 0.2)
for j, l in enumerate(["진짜 한 장에 D = 0.9, 가짜 한 장에 D = 0.2",
                       "V = ln 0.9 + ln 0.8 = %.3f" % ex_v,
                       "판별기가 완벽하면(1 과 0) V = 0 — 위 끝",
                       "평형(어디서나 D = 1/2) V = −log 4 = %.3f" % (-LN4)]):
    b += txt(55, 264 + 24 * j, l, 12, anchor="start", fill=INK if j < 2 else INK2)
b += box(450, 214, 370, 140, fill=NODE, stroke=LINE)
b += txt(465, 238, "읽는 법", 13, anchor="start", weight="bold")
for j, l in enumerate(["V 는 D 가 진짜/가짜 라벨에 매긴",
                       "로그 가능도다 (논문 4.1 의 해석)",
                       "판별기: 이진 분류기의 로그 가능도 최대화",
                       "생성기: 그 분류기가 틀리게 만든다",
                       "식 (1) 에는 무게 1/2 이 없다"]):
    b += txt(465, 262 + 21 * j, l, 12, anchor="start", fill=INK2)
svg("fig01_value_function", W, H, b, "가치 함수의 두 항")
print("  [1] 예시 V = %.4f, -log4 = %.4f" % (ex_v, -LN4))


# ── 그림 2. 논문 그림 1 을 계산으로 다시 그림 ─────────────────────────────────────
nd = NormalDist()
PD = (0.0, 0.5)
panels = [("(a) 수렴 근처, D 는 부분만 맞다", (1.0, 0.7), "wiggle"),
          ("(b) 안쪽 고리: D → D*", (1.0, 0.7), "star"),
          ("(c) G 갱신: G(z) 가 D 큰 쪽으로", (0.45, 0.6), "star"),
          ("(d) p_g = p_data, D = 1/2", PD, "half")]
W, H = 900, 420
b = defs()
b += txt(20, 30, "논문 그림 1 을 다시 그림 — p_data = N(0, 0.5²), p_g 는 가우스(수는 내가 고른 것), D 는 식 (2) 로 계산", 15, anchor="start", weight="bold")
PW = 200
for k, (title, (mg, sg), mode) in enumerate(panels):
    ox = 30 + k * 220
    def fx(v, ox=ox):
        return ox + (v + 2.0) / 4.5 * PW
    def fy(p):
        return 250 - p * 150
    b += box(ox - 8, 46, PW + 16, 340, fill=NODE, stroke=LINE)
    b += txt(ox + PW / 2, 68, title, 12, weight="bold")
    xsamp = [-2.0 + i * 0.02 for i in range(226)]
    b += polyline([(fx(x), fy(npdf(x, *PD) * 0.62)) for x in xsamp], S_DATA, 2, dash="2 3")
    b += polyline([(fx(x), fy(npdf(x, mg, sg) * 0.62)) for x in xsamp], S_MODEL, 2)
    def dval(x, mg=mg, sg=sg, mode=mode):
        a, c = npdf(x, *PD), npdf(x, mg, sg)
        ds = a / (a + c)
        if mode == "wiggle":
            return min(0.98, max(0.02, ds + 0.18 * math.sin(7 * x)))
        if mode == "half":
            return 0.5
        return ds
    b += polyline([(fx(x), fy(dval(x))) for x in xsamp], S_DISC, 1.8, dash="5 3")
    b += line(ox, 252, ox + PW, 252, INK2, 1.2)
    b += line(ox, 330, ox + PW, 330, INK2, 1.2)
    b += txt(ox - 2, 256, "x", 11, anchor="end", style="italic")
    b += txt(ox - 2, 334, "z", 11, anchor="end", style="italic")
    for j in range(9):
        z = (j + 0.5) / 9
        xz = mg + sg * nd.inv_cdf(z)
        b += line(ox + z * PW, 328, fx(xz), 257, CODE, 1, marker="ac", op=0.8)
    J = jsd(lambda x: npdf(x, *PD), lambda x, mg=mg, sg=sg: npdf(x, mg, sg))
    d0 = dval(0.0)
    b += txt(ox + PW / 2, 356, "JSD = %.3f nat" % J, 11, fill=INK2)
    b += txt(ox + PW / 2, 374, "D(0) = %.3f" % d0, 11, fill=INK2)
    print("  [2] %s: p_g=N(%.2f,%.2f) JSD=%.4f D(0)=%.4f" % (title, mg, sg, J, d0))
b += txt(450, 408, "검정 점선 p_data · 초록 실선 p_g · 파랑 파선 D (논문과 같은 색 역할). (a) 의 D 는 D* 에 사인 물결을 얹어 「부분만 맞다」를 흉내 냈다", 11, fill=MUTED)
svg("fig02_figure1_redraw", W, H, b, "논문 그림 1 을 계산으로 다시 그린 것")


# ── 그림 3. 알고리즘 1 ────────────────────────────────────────────────────────
W, H = 880, 470
b = defs()
b += txt(20, 30, "알고리즘 1 — 판별기 k 걸음, 생성기 한 걸음을 번갈아 (논문은 k = 1 · 모멘텀을 썼다)", 15, anchor="start", weight="bold")
b += box(30, 50, 540, 400, fill="none", stroke=INK2, sw=1.2, dash="6 4")
b += txt(45, 72, "학습 반복마다", 12, anchor="start", fill=INK2, weight="bold")
b += box(55, 85, 490, 205, fill="none", stroke=FWD, sw=1.2, dash="4 3")
b += txt(70, 106, "k 걸음 되풀이 (판별기)", 12, anchor="start", fill=FWD, weight="bold")
steps = [(120, "잡음 m 개를 뽑는다 (원문 「p_g(z)」 는 p_z(z) 의 오기)", CODE_SOFT, CODE),
         (170, "데이터 m 개를 p_data 에서 뽑는다", FWD_SOFT, FWD),
         (220, "θ_d 를 올린다: ∇ (1/m) Σ [ log D(x) + log(1 − D(G(z))) ]", FWD_SOFT, FWD)]
for y, t, f, s in steps:
    b += box(75, y, 440, 38, fill=f, stroke=s)
    b += txt(295, y + 24, t, 12)
for y in (158, 208):
    b += line(295, y, 295, y + 12, INK2, 1.2, marker="ai")
b += path("M515,239 C548,239 548,139 515,139", FWD, sw=1.4, dash="4 3", marker="af")
b += txt(552, 194, "k 번", 11, fill=FWD, anchor="start")
b += line(295, 290, 295, 315, INK2, 1.2, marker="ai")
b += box(75, 318, 440, 38, fill=CODE_SOFT, stroke=CODE)
b += txt(295, 342, "잡음 m 개를 새로 뽑는다", 12)
b += line(295, 356, 295, 372, INK2, 1.2, marker="ai")
b += box(75, 375, 440, 38, fill=REV_SOFT, stroke=REV)
b += txt(295, 399, "θ_g 를 내린다: ∇ (1/m) Σ log(1 − D(G(z)))", 12)
b += box(590, 50, 270, 400, fill=NODE, stroke=LINE)
b += txt(605, 74, "원문에서 확인한 것", 13, anchor="start", weight="bold")
notes3 = [("k 는 초매개변수, 실험은 k = 1", INK),
          ("「가장 싼 선택」이라고 적는다", INK2),
          ("갱신 규칙은 아무 기울기 규칙,", INK),
          ("실험은 모멘텀", INK2),
          ("", INK),
          ("인쇄된 생성기 갱신은 log(1 − D)", NO),
          ("— 3절 끝이 권한 log D 최대화", INK2),
          ("(포화 안 하는 쪽)가 아니다", INK2),
          ("실험에 어느 쪽을 썼는지는", INK2),
          ("본문에 없다 (코드 주소만 있다)", INK2),
          ("", INK),
          ("D 를 끝까지 배우지 않는 이유 둘:", INK),
          ("계산이 너무 비싸고,", INK2),
          ("유한 데이터에서 과적합한다 (3절)", INK2)]
for j, (l, c) in enumerate(notes3):
    b += txt(605, 102 + 24 * j, l, 12, anchor="start", fill=c)
svg("fig03_algorithm1", W, H, b, "알고리즘 1 흐름")


# ── 그림 4. 명제 1 — 점마다 a log y + b log(1−y) 의 최대 ──────────────────────────
W, H = 880, 380
b = defs()
b += txt(20, 30, "명제 1 의 증명 — x 마다 따로: a = p_data(x), b = p_g(x) 일 때 a log y + b log(1 − y) 는 y = a/(a+b) 에서 최대", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 70, 520, 60, 320
fx = lambda y: X0 + y * (X1 - X0)
fy = lambda v: Y0 + (0.0 - v) / 3.0 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [0, 0.25, 0.5, 0.75, 1.0], [0, -1, -2, -3], fx, fy, "y = D(x)", "a log y + b log(1−y)")
pairs = [(0.8, 0.2, S_DISC), (0.5, 0.5, INK2), (0.15, 0.45, REV)]
rows4 = []
for a, c, col_ in pairs:
    pts_ = []
    for i in range(1, 200):
        y = i / 200
        v = a * math.log(y) + c * math.log(1 - y)
        if v >= -3:
            pts_.append((fx(y), fy(v)))
    b += polyline(pts_, col_, 2.2)
    ys = a / (a + c)
    vs = a * math.log(ys) + c * math.log(1 - ys)
    # 격자에서 최대를 찾아 식과 맞춘다
    yg = max((i / 10000 for i in range(1, 10000)), key=lambda y: a * math.log(y) + c * math.log(1 - y))
    rows4.append((a, c, ys, yg, vs))
    b += circ(fx(ys), fy(vs), 5, col_, col_)
    b += line(fx(ys), fy(vs), fx(ys), Y1, col_, 1, dash="3 3")
    print("  [4] a=%.2f b=%.2f: a/(a+b)=%.4f, 격자 최대=%.4f, 최대값=%.4f" % (a, c, ys, yg, vs))
b += box(560, 60, 300, 280, fill=NODE, stroke=LINE)
b += txt(575, 84, "계산한 값", 13, anchor="start", weight="bold")
yy = 110
for (a, c, ys, yg, vs), (_, _, col_) in zip(rows4, pairs):
    b += txt(575, yy, "a = %.2f, b = %.2f" % (a, c), 12, anchor="start", fill=col_, weight="bold")
    b += txt(575, yy + 19, "a/(a+b) = %.3f · 격자 최대 %.3f" % (ys, yg), 12, anchor="start", fill=INK2)
    b += txt(575, yy + 38, "최대값 %.3f" % vs, 12, anchor="start", fill=INK2)
    yy += 66
b += txt(575, yy + 2, "a, b 는 밀도라 0 이상이다 — 원문은", 11, anchor="start", fill=MUTED)
b += txt(575, yy + 18, "「R² 에서 (0, 0) 을 뺀 곳」으로 적는다", 11, anchor="start", fill=MUTED)
svg("fig04_prop1_pointwise", W, H, b, "명제 1 의 점별 최대")


# ── 그림 5. 정리 1 — C(G) = −log 4 + KL(p_data‖M) + KL(p_g‖M) ───────────────────
pdat = lambda x: npdf(x, 0.0, 1.0)
ms5 = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0]
rows5 = []
for m in ms5:
    pg = lambda x, m=m: npdf(x, m, 1.5)
    M = lambda x, pg=pg: 0.5 * (pdat(x) + pg(x))
    k1, k2 = kl(pdat, M), kl(pg, M)
    vd = v_direct(pdat, pg)
    rows5.append((m, k1, k2, vd))
    print("  [5] m=%.1f: KL(pd||M)=%.4f KL(pg||M)=%.4f  -log4+합=%.4f  직접 적분 V=%.4f"
          % (m, k1, k2, -LN4 + k1 + k2, vd))
W, H = 880, 400
b = defs()
b += txt(20, 30, "정리 1 의 식 (5) — p_data = N(0, 1), p_g = N(m, 1.5²) 일 때 C(G) 를 KL 두 조각으로 나눈다", 15, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 520, 60, 330
fy = lambda v: Y1 - v / 1.4 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [], [0, 0.35, 0.7, 1.05, 1.4], lambda t: 0, fy, None, "KL 두 조각의 합 = 2·JSD (nat)", yfmt="%.2f")
bw = 44
for i, (m, k1, k2, vd) in enumerate(rows5):
    x = X0 + 25 + i * 72
    b += '<rect x="%.1f" y="%.1f" width="%d" height="%.1f" fill="%s"/>' % (x, fy(k1), bw, Y1 - fy(k1), FWD)
    b += '<rect x="%.1f" y="%.1f" width="%d" height="%.1f" fill="%s"/>' % (x, fy(k1 + k2), bw, fy(k1) - fy(k1 + k2), REV)
    b += txt(x + bw / 2, Y1 + 17, "m = %g" % m, 11, fill=INK2)
    b += txt(x + bw / 2, fy(k1 + k2) - 6, "%.3f" % (k1 + k2), 11, fill=INK)
b += line(X0, fy(2 * LN2), X1, fy(2 * LN2), NO, 1.2, dash="5 4")
b += txt(X1, fy(2 * LN2) - 6, "위 끝 2·log 2 = %.3f" % (2 * LN2), 11, fill=NO, anchor="end")
b += box(550, 60, 310, 300, fill=NODE, stroke=LINE)
b += txt(565, 84, "직접 적분한 V 와 맞추기", 13, anchor="start", weight="bold")
for cx, hd in [(575, "m"), (655, "KL(p_data||M)"), (745, "KL(p_g||M)"), (820, "V")]:
    b += txt(cx, 106, hd, 11, fill=MUTED)
for j, (m, k1, k2, vd) in enumerate(rows5):
    for cx, v in [(575, "%g" % m), (655, "%.4f" % k1), (745, "%.4f" % k2), (820, "%.4f" % vd)]:
        b += txt(cx, 130 + 22 * j, v, 12)
maxdiff5 = max(abs(-LN4 + k1 + k2 - vd) for m, k1, k2, vd in rows5)
b += txt(565, 278, "−log 4 + 두 KL 과 직접 적분한 V 의", 12, anchor="start", fill=INK2)
b += txt(565, 298, "차이 최대 %.1e" % maxdiff5, 12, anchor="start", fill=INK2)
b += '<rect x="565" y="318" width="12" height="12" fill="%s"/>' % FWD
b += txt(583, 329, "KL(p_data||M)", 11, anchor="start")
b += '<rect x="690" y="318" width="12" height="12" fill="%s"/>' % REV
b += txt(708, 329, "KL(p_g||M)", 11, anchor="start")
b += txt(440, 384, "분산이 달라(1 과 1.5²) m = 0 에서도 두 조각이 0 이 아니다. 두 조각이 함께 0 이 되는 것은 p_g = p_data 일 때뿐", 11, fill=MUTED)
svg("fig05_theorem1_kl", W, H, b, "정리 1 의 KL 분해")
print("  [5] 최대 차이 %.2e" % maxdiff5)


# ── 그림 6. 증명의 사슬과 가정 ───────────────────────────────────────────────────
W, H = 880, 430
b = defs()
b += txt(20, 30, "4절 증명의 사슬 — 무엇이 어디서 가정되는가", 15, anchor="start", weight="bold")
chain = [("식 (1)", "min_G max_D V(D, G)", NODE, INK2),
         ("명제 1 · 식 (2)", "D* = p_data / (p_data + p_g)", FWD_SOFT, FWD),
         ("식 (4)", "C(G) = max_D V(G, D)", NODE, INK2),
         ("정리 1 · 식 (5)(6)", "C(G) = −log 4 + 2·JSD", FWD_SOFT, FWD),
         ("명제 2", "p_g → p_data", "#DDEFE3", OK)]
for i, (t, s, f, c) in enumerate(chain):
    x = 20 + i * 172
    b += box(x, 60, 158, 70, fill=f, stroke=c, sw=1.5)
    b += txt(x + 79, 88, t, 13, weight="bold", fill=c)
    b += txt(x + 79, 110, s, 11)
    if i < 4:
        b += line(x + 158, 95, x + 170, 95, INK2, 1.4, marker="ai")
assume = [(20 + 172, ["D 는 아무 함수나 된다", "두 받침의 합집합 밖은", "정의하지 않아도 된다"]),
          (20 + 3 * 172, ["밀도 함수 공간에서", "(비모수 설정, 무한 용량)", "JSD ≥ 0, 같을 때만 0"]),
          (20 + 4 * 172, ["G, D 가 충분한 용량", "매 걸음 D 가 최적에 닿는다", "p_g 를 직접, 작게 갱신"])]
for x, ls in assume:
    b += line(x + 79, 132, x + 79, 156, CODE, 1.2, dash="3 3")
    b += box(x, 158, 158, 78, fill=CODE_SOFT, stroke=CODE)
    for j, l in enumerate(ls):
        b += txt(x + 79, 180 + 21 * j, l, 11)
b += txt(20, 270, "가정 (노랑) 은 원문 명제 · 정리 · 증명에 적힌 것을 옮겼다", 11, anchor="start", fill=MUTED)
b += box(20, 290, 840, 120, fill=REV_SOFT, stroke=NO, sw=1.5)
b += txt(40, 316, "실제 학습과의 거리 — 논문 4.2 끝이 스스로 적는다", 13, anchor="start", weight="bold", fill=NO)
for j, l in enumerate(["「실제로는 G(z; θ_g) 가 나타내는 제한된 p_g 가족을 쓰고, p_g 자체가 아니라 θ_g 를 최적화하므로 증명이 적용되지 않는다」",
                       "그리고 알고리즘 1 은 k = 1 — 판별기가 매 걸음 최적에 닿는다는 명제 2 의 가정과도 다르다 (이 줄은 내가 맞춘 것)",
                       "논문이 대신 드는 근거: 「실제로 다층 퍼셉트론의 성능이 뛰어나다」 — 잰 값이 붙은 문장이 아니다"]):
    b += txt(40, 344 + 24 * j, l, 12, anchor="start", fill=INK2 if j else INK)
svg("fig06_proof_chain", W, H, b, "4절 증명의 사슬과 가정")


# ── 그림 7. 명제 2 의 볼록성 — 섞기 방향은 볼록, 파라미터 방향은 아니다 ───────────
lam = [i / 20 for i in range(21)]
cl = []
for l_ in lam:
    pg = lambda x, l_=l_: (1 - l_) * npdf(x, 4.0, 1.0) + l_ * npdf(x, 0.0, 1.0)
    cl.append(-LN4 + 2 * jsd(pdat, pg))
d2l = [cl[i - 1] - 2 * cl[i] + cl[i + 1] for i in range(1, 20)]
ms7 = [i * 0.25 for i in range(25)]
cm = [-LN4 + 2 * jsd(pdat, lambda x, m=m: npdf(x, m, 1.0)) for m in ms7]
d2m = [cm[i - 1] - 2 * cm[i] + cm[i + 1] for i in range(1, 24)]   # d2m[i] 은 ms7[i+1] 자리
infl = None
for i in range(1, len(d2m)):
    if d2m[i - 1] > 0 >= d2m[i]:
        infl = (ms7[i] + ms7[i + 1]) / 2
        break
print("  [7] 섞기 방향 이계 차분 최소 %.6f (모두 0 이상이면 볼록)" % min(d2l))
print("  [7] 이동 방향: 이계 차분이 양에서 음으로 바뀌는 자리 m ≈ %.3f, C(0)=%.4f C(6)=%.4f" % (infl, cm[0], cm[-1]))
W, H = 880, 410
b = defs()
b += txt(20, 30, "명제 2 는 p_g 공간의 볼록성에 기댄다 — 같은 C 가 파라미터 방향으로는 볼록하지 않다 (내가 계산한 예)", 15, anchor="start", weight="bold")
for k in range(2):
    X0 = 70 + k * 430
    X1 = X0 + 340
    Y0, Y1 = 80, 320
    fy = lambda v: Y1 - (v + LN4) / LN4 * (Y1 - Y0)
    if k == 0:
        fx = lambda t, X0=X0, X1=X1: X0 + t * (X1 - X0)
        b += axes(X0, Y0, X1, Y1, [0, 0.25, 0.5, 0.75, 1], [-LN4, -0.693, 0], fx, fy, "λ   (p_g = (1−λ)·N(4,1) + λ·N(0,1))", "C(G)", yfmt="%.2f")
        b += polyline([(fx(l_), fy(v)) for l_, v in zip(lam, cl)], S_MODEL, 2.4)
        b += txt((X0 + X1) / 2, 54, "섞기 방향 — p_g 를 직접 움직인다", 13, weight="bold", fill=OK)
        b += txt(X1 - 6, Y0 + 20, "이계 차분 최소 %.4f ≥ 0 : 볼록" % min(d2l), 11, anchor="end", fill=OK)
    else:
        fx = lambda t, X0=X0, X1=X1: X0 + t / 6.0 * (X1 - X0)
        b += axes(X0, Y0, X1, Y1, [0, 1, 2, 3, 4, 5, 6], [-LN4, -0.693, 0], fx, fy, "m   (p_g = N(m, 1), 생성기 파라미터 하나)", "C(G)", yfmt="%.2f")
        b += polyline([(fx(m), fy(v)) for m, v in zip(ms7, cm)], REV, 2.4)
        b += line(fx(infl), Y0, fx(infl), Y1, NO, 1.2, dash="4 3")
        b += txt(fx(infl) + 6, Y1 - 12, "m ≈ %.2f 에서 굽는 방향이 바뀐다" % infl, 11, anchor="start", fill=NO)
        b += txt((X0 + X1) / 2, 54, "파라미터 방향 — θ_g 를 움직인다", 13, weight="bold", fill=NO)
b += txt(440, 374, "왼쪽: C 는 p_g 에 대해 볼록하다 — 원문 증명이 쓰는 성질(두 분포 섞기로 확인). 오른쪽: 같은 C 를 평균 m 으로 재면 오목한 구간이 생긴다", 11, fill=MUTED)
b += txt(440, 394, "평균 이동 한 축만으로도 볼록성이 깨진다 — 논문이 「θ_g 를 최적화하므로 증명이 적용되지 않는다」고 적는 자리를 수로 옮긴 것", 11, fill=MUTED)
svg("fig07_convex_vs_param", W, H, b, "섞기 방향과 파라미터 방향의 볼록성")


# ── 그림 8. 포화 — log(1−D) 와 −log D ────────────────────────────────────────────
W, H = 880, 400
b = defs()
b += txt(20, 30, "3절 끝 — 학습 초기 D(G(z)) 가 0 쪽이면 log(1 − D) 가 포화한다. 그래서 log D 를 올리게 바꾼다", 15, anchor="start", weight="bold")
ds8 = [i / 200 for i in range(1, 200)]
for k in range(2):
    X0 = 70 + k * 430
    X1 = X0 + 340
    Y0, Y1 = 70, 310
    fx = lambda t, X0=X0, X1=X1: X0 + t * (X1 - X0)
    if k == 0:
        fy = lambda v: Y0 + (3.0 - v) / 8.0 * (Y1 - Y0)
        b += axes(X0, Y0, X1, Y1, [0, 0.25, 0.5, 0.75, 1], [3, 0, -2, -5], fx, fy, "D(G(z))", "생성기가 줄이는 값")
        b += polyline([(fx(d), fy(math.log(1 - d))) for d in ds8 if math.log(1 - d) >= -5], REV, 2.4)
        b += polyline([(fx(d), fy(-math.log(d))) for d in ds8 if -math.log(d) <= 3.0], S_DISC, 2.4)
        b += txt(fx(0.05), fy(-1.3), "log(1 − D)  (식 1 그대로)", 11, fill=REV, anchor="start")
        b += txt(fx(0.22), fy(-math.log(0.22)) - 10, "−log D  (3절 끝의 대안)", 11, fill=S_DISC, anchor="start")
    else:
        fy = lambda v: Y1 - v * (Y1 - Y0)
        b += axes(X0, Y0, X1, Y1, [0, 0.25, 0.5, 0.75, 1], [0, 0.5, 1], fx, fy, "D(G(z))", "로짓 a 에 대한 기울기 크기 (D = σ(a))")
        b += polyline([(fx(d), fy(d)) for d in ds8], REV, 2.4)
        b += polyline([(fx(d), fy(1 - d)) for d in ds8], S_DISC, 2.4)
        b += circ(fx(0.01), fy(0.01), 5, REV, REV)
        b += circ(fx(0.01), fy(0.99), 5, S_DISC, S_DISC)
        b += txt(fx(0.12), fy(0.97), "D = 0.01 에서 대안 0.99", 11, anchor="start", fill=S_DISC)
        b += txt(fx(0.25), fy(0.08), "D = 0.01 에서 식 1 은 0.01 (99 배 작다)", 11, anchor="start", fill=REV)
b += txt(440, 364, "원문은 식 없이 문장 셋: 「log(1−D(G(z))) 가 포화한다」 · 「log D(G(z)) 를 최대화하게 할 수 있다」 · 「같은 고정점, 초기에 훨씬 센 기울기」", 11, fill=MUTED)
b += txt(440, 384, "기울기 식(식 1: σ(a), 대안: 1 − σ(a))과 99 배는 내가 붙인 것 — CACM 개관판 노트 10절과 같은 계산", 11, fill=MUTED)
svg("fig08_saturation", W, H, b, "포화하는 생성기 비용과 대안")


# ── 그림 9. 표 1 — Parzen 창 로그 가능도 ──────────────────────────────────────────
T1 = {"MNIST": [("DBN", 138, 2), ("Stacked CAE", 121, 1.6), ("Deep GSN", 214, 1.1), ("Adversarial nets", 225, 2)],
      "TFD": [("DBN", 1909, 66), ("Stacked CAE", 2110, 50), ("Deep GSN", 1890, 29), ("Adversarial nets", 2057, 26)]}
W, H = 880, 400
b = defs()
b += txt(20, 30, "표 1 — Parzen 창으로 추정한 시험 집합 로그 가능도 (높을수록 좋다). 굵은 선 끝 막대는 ± 표준오차", 15, anchor="start", weight="bold")
rng = {"MNIST": (100, 240), "TFD": (1750, 2200)}
for k, ds_ in enumerate(["MNIST", "TFD"]):
    X0 = 160 + k * 440
    X1 = X0 + 250
    lo, hi = rng[ds_]
    fx = lambda v, X0=X0, X1=X1, lo=lo, hi=hi: X0 + (v - lo) / (hi - lo) * (X1 - X0)
    b += txt(X0 + 125, 62, ds_, 14, weight="bold")
    ticks = [100, 140, 180, 220] if ds_ == "MNIST" else [1800, 1900, 2000, 2100, 2200]
    b += line(X0, 280, X1, 280, INK2, 1.2)
    for t in ticks:
        b += line(fx(t), 280, fx(t), 284, INK2, 1) + txt(fx(t), 298, "%d" % t, 10, fill=MUTED)
        b += line(fx(t), 80, fx(t), 280, LINE, 0.8, dash="2 3")
    for j, (name, v, se) in enumerate(T1[ds_]):
        y = 100 + j * 48
        c = REV if name.startswith("Adv") else FWD
        b += txt(X0 - 10, y + 4, name, 12, anchor="end", fill=c, weight="bold" if c == REV else None)
        b += line(fx(lo), y, fx(v), y, c, 10, op=0.35)
        b += line(fx(v - se), y, fx(v + se), y, c, 2.2)
        b += line(fx(v - se), y - 6, fx(v - se), y + 6, c, 1.6) + line(fx(v + se), y - 6, fx(v + se), y + 6, c, 1.6)
        b += txt(fx(v), y - 10, "%d ± %g" % (v, se), 11, anchor="middle", fill=c)
d_mn = 225 - 214
se_mn = math.sqrt(2 ** 2 + 1.1 ** 2)
d_tf = 2110 - 2057
se_tf = math.sqrt(50 ** 2 + 26 ** 2)
print("  [9] MNIST GAN-GSN %d, 표준오차 제곱합 %.2f / TFD CAE-GAN %d, 제곱합 %.1f" % (d_mn, se_mn, d_tf, se_tf))
b += txt(30, 330, "MNIST: GAN 이 넷 중 가장 높다 — 둘째(Deep GSN)와 차이 %d, 두 표준오차의 제곱합 제곱근 %.1f." % (d_mn, se_mn), 11, anchor="start", fill=INK2)
b += txt(30, 348, "이쪽 ± 는 시험 예시 사이의 표준오차라 학습 seed 의 흔들림은 들어 있지 않다", 11, anchor="start", fill=INK2)
b += txt(30, 366, "TFD: GAN 은 둘째 — 첫째(Stacked CAE)보다 %d 낮고, 같은 방식으로 합친 표준오차 %.1f 보다 차이가 작다. 이쪽 ± 는 묶음(fold) 사이의 표준오차" % (d_tf, se_tf), 11, anchor="start", fill=INK2)
b += txt(30, 384, "본문은 이 표에 「결과는 표 1 에 있다」만 적고 순위를 말하지 않는다. CIFAR-10 은 표에 없다. 제곱합은 두 값이 독립이라고 친 내 계산", 11, anchor="start", fill=MUTED)
svg("fig09_table1", W, H, b, "표 1 Parzen 창 로그 가능도")


# ── 그림 10. Parzen 창 추정 — 1 차원, σ 를 바꾸면 ────────────────────────────────
random.seed(1)
gen = [random.gauss(0, 1) for _ in range(20)]
test = [random.gauss(0, 1) for _ in range(500)]
true_ll = sum(math.log(npdf(t, 0, 1)) for t in test) / len(test)   # 같은 시험 점에서 참 밀도로


def parzen_ll(samples, tests, s):
    tot = 0.0
    for t in tests:
        tot += math.log(sum(npdf(t, g, s) for g in samples) / len(samples) + 1e-300)
    return tot / len(tests)


sig = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5]
lls = [parzen_ll(gen, test, s) for s in sig]
best = max(zip(lls, sig))
print("  [10] σ 별 Parzen LL:", ", ".join("%.2f:%.3f" % (s, v) for s, v in zip(sig, lls)), " 참값 %.4f" % true_ll)
W, H = 880, 400
b = defs()
b += txt(20, 30, "Parzen 창 추정 — 생성 표본 20 개에 가우스를 하나씩 얹어 밀도로 쓴다. σ 가 결과를 정한다 (1 차원, 내가 만든 예)", 15, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 60, 420, 90, 300
fx = lambda v: X0 + (v + 3.5) / 7.0 * (X1 - X0)
fy = lambda p: Y1 - p / 1.0 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [-3, -2, -1, 0, 1, 2, 3], [0, 0.5, 1.0], fx, fy, "x", "밀도")
xs10 = [-3.5 + i * 0.02 for i in range(351)]
b += polyline([(fx(x), fy(npdf(x, 0, 1))) for x in xs10], S_DATA, 2, dash="2 3")
for s, c in [(0.05, NO), (best[1], S_MODEL), (1.0, S_DISC)]:
    b += polyline([(fx(x), fy(min(1.0, sum(npdf(x, g, s) for g in gen) / len(gen)))) for x in xs10], c, 1.6)
for g in gen:
    b += line(fx(g), Y1, fx(g), Y1 - 8, REV, 2)
b += txt(X0, 50, "σ = 0.05 (빨강) · σ = %.1f (초록, 가장 높음) · σ = 1.0 (파랑)" % best[1], 11, anchor="start", fill=INK2)
b += txt(X0, 66, "검정 점선 = 참 분포 N(0, 1) · 주황 눈금 = 생성 표본 20 개", 11, anchor="start", fill=INK2)
X0b, X1b = 510, 850
fxb = lambda s: X0b + math.log(s / 0.05) / math.log(1.5 / 0.05) * (X1b - X0b)
fyb = lambda v: Y1 - (v + 4.0) / 3.0 * (Y1 - Y0)
b += axes(X0b, Y0, X1b, Y1, [0.05, 0.1, 0.3, 1.0, 1.5], [-4, -3, -2, -1], fxb, fyb, "σ (로그 눈금)", "시험 500 점의 평균 로그 가능도", xfmt="%g")
b += polyline([(fxb(s), fyb(max(v, -4))) for s, v in zip(sig, lls)], S_MODEL, 2.2)
for s, v in zip(sig, lls):
    b += circ(fxb(s), fyb(max(v, -4)), 3.5, S_MODEL, S_MODEL)
b += line(X0b, fyb(true_ll), X1b, fyb(true_ll), S_DATA, 1.2, dash="5 4")
b += txt(X1b, fyb(true_ll) - 6, "같은 시험 점의 참 밀도 %.3f" % true_ll, 11, anchor="end")
b += txt(fxb(best[1]), fyb(best[0]) + 20, "σ = %.1f: %.3f" % (best[1], best[0]), 11, fill=S_MODEL)
b += txt(440, 364, "σ 가 작으면 시험 점이 표본 사이에 떨어질 때 로그 가능도가 크게 떨어지고(σ = 0.05 에서 %.2f, 그림은 −4 에서 자름), 크면 밀도가 퍼진다" % lls[0], 11, fill=MUTED)
b += txt(440, 384, "같은 표본 20 개인데 σ 하나로 %.2f 에서 %.2f 까지 움직인다 — 표 1 의 수는 모델과 σ 고르기를 함께 잰 것이다 (논문은 σ 를 검증 집합으로 골랐다)" % (min(lls), max(lls)), 11, fill=MUTED)
svg("fig10_parzen_1d", W, H, b, "Parzen 창 추정과 σ")


# ── 그림 11. Parzen 창 추정 — 차원이 오르면 ──────────────────────────────────────
random.seed(2)
dims = [1, 2, 5, 10, 20, 50]
NS, NT = 1000, 200
sig11 = [0.05 * 1.25 ** i for i in range(25)]
rows11 = []
for d in dims:
    S = [[random.gauss(0, 1) for _ in range(d)] for _ in range(NS)]
    T = [[random.gauss(0, 1) for _ in range(d)] for _ in range(NT)]
    D2 = [[sum((a - c) ** 2 for a, c in zip(t, s_)) for s_ in S] for t in T]
    bestv, bests = -1e18, None
    for s in sig11:
        c0 = -0.5 * d * math.log(2 * math.pi * s * s) - math.log(NS)
        tot = 0.0
        for row in D2:
            e = [-r / (2 * s * s) for r in row]
            mx = max(e)
            tot += c0 + mx + math.log(sum(math.exp(v - mx) for v in e))
        v = tot / NT
        if v > bestv:
            bestv, bests = v, s
    tr = sum(-0.5 * d * math.log(2 * math.pi) - 0.5 * sum(a * a for a in t) for t in T) / NT   # 같은 시험 점의 참 밀도
    rows11.append((d, bestv, tr, bests))
    print("  [11] d=%d: Parzen 최고 %.3f (σ=%.3f), 참값 %.3f, 차이 %.3f (차원당 %.3f)" % (d, bestv, bests, tr, tr - bestv, (tr - bestv) / d))
W, H = 880, 400
b = defs()
b += txt(20, 30, "차원이 오르면 Parzen 추정이 참값에서 멀어진다 — N(0, I_d) 표본 1,000 개, 시험 200 개 (내가 만든 예)", 15, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 460, 70, 300
fx = lambda d: X0 + math.log(d) / math.log(50) * (X1 - X0)
gmax = max(r[2] - r[1] for r in rows11)
fy = lambda v: Y1 - v / (gmax * 1.1) * (Y1 - Y0)
yt = [0, round(gmax / 2), round(gmax)]
b += axes(X0, Y0, X1, Y1, dims, yt, fx, fy, "차원 d (로그 눈금)", "참값 − Parzen 최고값 (nat, 시험 점 하나당)")
b += polyline([(fx(d), fy(tr - bv)) for d, bv, tr, s in rows11], NO, 2.2)
for d, bv, tr, s in rows11:
    b += circ(fx(d), fy(tr - bv), 4, NO, NO)
b += box(510, 60, 350, 250, fill=NODE, stroke=LINE)
for cx, hd in [(540, "d"), (610, "Parzen 최고"), (690, "참값"), (760, "차이"), (825, "σ")]:
    b += txt(cx, 84, hd, 11, fill=MUTED)
for j, (d, bv, tr, s) in enumerate(rows11):
    for cx, v in [(540, "%d" % d), (610, "%.2f" % bv), (690, "%.2f" % tr), (760, "%.2f" % (tr - bv)), (825, "%.2f" % s)]:
        b += txt(cx, 110 + 26 * j, v, 12)
b += txt(525, 290, "σ 는 1.25 배 간격 25 개 중 시험 점에서 가장 좋은 것", 10, anchor="start", fill=MUTED)
b += txt(440, 350, "차이는 d = 1 에서 %.2f, d = 50 에서 %.2f nat. σ 를 시험 점에서 골라 추정 쪽에 유리한데도 그렇다. MNIST 는 d = 784, TFD 는 48 × 48 이면 d = 2,304" % (rows11[0][2] - rows11[0][1], rows11[-1][2] - rows11[-1][1]), 11, fill=MUTED)
b += txt(440, 370, "논문 5절: 「이 추정은 분산이 꽤 크고 고차원 공간에서 잘 동작하지 않지만 우리가 아는 가장 나은 방법이다」 — 그 문장의 크기를 작은 예로 잰 것", 11, fill=MUTED)
svg("fig11_parzen_dim", W, H, b, "차원과 Parzen 추정의 차이")


# ── 그림 12. 헬베티카 시나리오 ─────────────────────────────────────────────────
W, H = 880, 380
b = defs()
b += txt(20, 30, "6절의 「헬베티카 시나리오」 — G 를 D 갱신 없이 너무 많이 배우면 많은 z 를 같은 x 로 보낸다", 15, anchor="start", weight="bold")
mix = lambda x: 0.5 * npdf(x, -1.2, 0.4) + 0.5 * npdf(x, 1.2, 0.4)
for k in range(2):
    ox = 40 + k * 430
    PW2 = 380
    fx = lambda v, ox=ox: ox + (v + 2.5) / 5.0 * PW2
    b += box(ox - 10, 48, PW2 + 20, 280, fill=NODE, stroke=LINE)
    b += txt(ox + PW2 / 2, 72, "건강한 G — 두 봉우리를 덮는다" if k == 0 else "무너진 G — z 대부분이 한 점으로", 13, weight="bold", fill=OK if k == 0 else NO)
    xs12 = [-2.5 + i * 0.02 for i in range(251)]
    b += polyline([(fx(x), 190 - 80 * mix(x) / 0.5) for x in xs12], S_DATA, 2, dash="2 3")
    b += line(ox, 195, ox + PW2, 195, INK2, 1.2)
    b += line(ox, 290, ox + PW2, 290, INK2, 1.2)
    b += txt(ox - 2, 199, "x", 11, anchor="end", style="italic")
    b += txt(ox - 2, 294, "z", 11, anchor="end", style="italic")
    for j in range(14):
        z = (j + 0.5) / 14
        if k == 0:
            xz = (-1.2 if z < 0.5 else 1.2) + 0.4 * nd.inv_cdf((z * 2) % 1)
        else:
            xz = -1.1 if j == 3 else 1.15 + 0.03 * (j - 7) / 7
        b += line(ox + z * PW2, 288, fx(xz), 200, CODE, 1, marker="ac", op=0.8)
    b += txt(ox + PW2 / 2, 316, "z 14 개가 두 봉우리에 7 개씩" if k == 0 else "z 13 개가 x ≈ 1.15 한 점, 1 개만 왼쪽", 11, fill=INK2)
b += txt(440, 350, "원문: G 가 「p_data 를 나타낼 만큼의 다양성을 갖지 못하게」 된다 — 볼츠만 기계의 음의 사슬을 학습 걸음 사이에 갱신해 둬야 하는 것과 같다고 적는다", 11, fill=MUTED)
b += txt(440, 370, "오늘 흔히 「모드 붕괴」라 부르는 현상의 첫 이름이다 (이 연결은 내가 이은 것). 원문은 이 일이 얼마나 자주 나는지 재지 않는다. 그림의 수는 내가 고른 것", 11, fill=MUTED)
svg("fig12_helvetica", W, H, b, "헬베티카 시나리오")


# ── 그림 13. 표 2 — 생성 모델 네 갈래의 어려움 ─────────────────────────────────
W, H = 900, 470
b = defs()
b += txt(20, 30, "표 2 — 생성 모델 네 갈래가 각 연산에서 만나는 어려움 (원문 표를 옮긴 것. 빨강은 걸림이 적힌 칸으로 내가 칠한 것)", 14, anchor="start", weight="bold")
cols13 = ["깊은 유향 그래프 모델", "깊은 무향 그래프 모델", "생성 오토인코더", "적대 모델 (GAN)"]
rows13 = [("학습", [(["학습 중 추론이 필요"], 1), (["학습 중 추론이 필요", "분배 함수 기울기를", "MCMC 로 근사"], 1), (["섞임과 재구성 능력", "사이의 맞교환이 강제됨"], 1), (["판별기를 생성기와", "맞춰 가기", "헬베티카"], 1)]),
          ("추론", [(["배운 근사 추론"], 0), (["변분 추론"], 0), (["MCMC 기반 추론"], 0), (["배운 근사 추론"], 0)]),
          ("표본 뽑기", [(["어려움 없음"], 0), (["마르코프 사슬 필요"], 1), (["마르코프 사슬 필요"], 1), (["어려움 없음"], 0)]),
          ("p(x) 평가", [(["계산 불가,", "AIS 로 근사할 수 있다"], 1), (["계산 불가,", "AIS 로 근사할 수 있다"], 1), (["명시적으로 없음,", "Parzen 으로 근사"], 1), (["명시적으로 없음,", "Parzen 으로 근사"], 1)]),
          ("모델 설계", [(["원하는 추론 방식에", "맞게 설계해야 한다"], 1), (["여러 성질을 갖추게", "조심스러운 설계"], 1), (["미분 가능한 함수는", "이론상 무엇이든"], 0), (["미분 가능한 함수는", "이론상 무엇이든"], 0)])]
CW, RX = 185, 110
b += box(20, 46, 860, 400, fill=NODE, stroke=LINE)
for i, c in enumerate(cols13):
    x = RX + i * CW
    b += box(x + 4, 52, CW - 8, 34, fill=REV_SOFT if i == 3 else FWD_SOFT, stroke=REV if i == 3 else FWD)
    b += txt(x + CW / 2, 74, c, 12, weight="bold")
for r, (name, cells) in enumerate(rows13):
    y = 96 + r * 70
    b += txt(32, y + 38, name, 13, anchor="start", weight="bold")
    b += line(30, y + 68, 870, y + 68, LINE, 0.8)
    for i, (ls, hard) in enumerate(cells):
        x = RX + i * CW
        for j, l in enumerate(ls):
            b += txt(x + CW / 2, y + 38 - 9 * (len(ls) - 1) + 18 * j, l, 11, fill=NO if hard else INK)
b += txt(450, 462, "원문 표는 칸을 글로만 적는다. 「생성 오토인코더」 열은 GSN 계열처럼 마르코프 사슬로 표본을 뽑는 오토인코더를 말한다", 11, fill=MUTED)
svg("fig13_table2", W, H, b, "표 2 생성 모델 비교")


# ── 그림 14. 2절 관련 연구 — GAN 과 무엇이 다른가 ────────────────────────────────
W, H = 900, 460
b = defs()
b += txt(20, 30, "2절 — 원문이 견주는 여섯과 GAN 과의 차이 (원문 문장을 줄여 옮겼다)", 15, anchor="start", weight="bold")
rel = [("깊은 볼츠만 기계", ["가능도를 식으로 적는다", "기울기에 근사가 많이 든다"], ["가능도를 적지 않는다"]),
       ("생성 확률망 (GSN)", ["가능도 없이 표본을 내는 「생성 기계」", "정확한 역전파로 학습"], ["마르코프 사슬까지 없앴다"]),
       ("VAE (Kingma · Rezende)", ["미분되는 생성망 + 둘째 망", "둘째 망은 인식 모델(근사 추론)"], ["둘째 망이 판별기다", "GAN 은 이산 데이터 불가 / VAE 는 이산 잠재 불가"]),
       ("잡음 대조 추정 (NCE)", ["고정된 잡음 분포와 데이터를 가르며 학습", "판별 기준이 두 밀도의 비"], ["두 밀도를 계산하고", "미분할 필요가 없다"]),
       ("예측 가능성 최소화", ["은닉 유닛이 다른 망의 예측과 다르게", "다른 과제에 붙는 정칙화 항"], ["경쟁이 유일한 기준 · 고차원 벡터 입력", "최적화가 아니라 최소최대 게임"]),
       ("적대적 예시", ["분류기 입력을 기울기로 바꿔", "틀리게 만드는 분석 도구"], ["생성 모델 학습 장치가 아니다", "(GAN 학습이 비효율일 수 있음을 시사)"])]
b += txt(42, 62, "편", 12, anchor="start", fill=MUTED, weight="bold")
b += txt(250, 62, "그 방법", 12, anchor="start", fill=MUTED, weight="bold")
b += txt(580, 62, "GAN 이 다른 점", 12, anchor="start", fill=MUTED, weight="bold")
for j, (a, c, d) in enumerate(rel):
    y = 74 + j * 60
    b += box(30, y, 840, 52, fill=NODE, stroke=LINE)
    b += txt(42, y + 31, a, 12, anchor="start", weight="bold")
    for i, l in enumerate(c):
        b += txt(250, y + 22 + 18 * i, l, 11, anchor="start", fill=INK2)
    for i, l in enumerate(d):
        b += txt(580, y + (31 if len(d) == 1 else 22 + 18 * i), l, 11, anchor="start", fill=REV)
b += txt(450, 446, "VAE 문단은 「이 일을 할 때 Kingma · Welling 과 Rezende 외의 규칙을 몰랐다」로 시작한다 — 두 편이 같은 시기에 나왔다는 것을 원문이 밝힌다", 11, fill=MUTED)
svg("fig14_related_work", W, H, b, "관련 연구와의 차이")


# ── 그림 15. CACM 개관판 노트의 유도를 원문과 대조 ──────────────────────────────
W, H = 900, 470
b = defs()
b += txt(20, 30, "CACM 2020 개관판 노트에서 내가 유도한 것 · 옮긴 것을 원문과 맞춘 결과", 15, anchor="start", weight="bold")
chk = [("가치 함수 (개관판 노트 식 b)", "원문 식 (1) 과 같다 — 무게 1/2 없음. z 의 분포를 원문은 p_z(z) 로 적는다", "같다", OK),
       ("최적 판별기 D* (식 c)", "원문 명제 1 · 식 (2) 와 같다. 원문은 미분 대신 최대 자리를 바로 적고 받침 밖을 뺀다", "같다", OK),
       ("−log 4 + 2·JSD (식 d)", "원문 정리 1 · 식 (5)(6) 과 같다. 원문은 KL 둘을 먼저 적고 JSD 로 묶는다", "같다", OK),
       ("포화 기울기 (10절 표)", "원문은 식 없이 문장뿐. 방향(초기 D 가 확신 있게 거부 → 포화)은 같다", "식은 내 것", CODE),
       ("「NS-GAN 의 이론이 없다」", "원문 3절이 「같은 고정점」이라고 한 문장 적는다 — 증명은 없다", "고쳐 적을 것", NO),
       ("그림 4 (a) 의 설명", "원문 그림 1 (a) 는 「수렴 근처의 쌍」, 개관판은 「초기화 때」로 바꿨다", "두 판이 다르다", NO),
       ("물음: NS-GAN 을 이론 절에서?", "다루지 않는다. 4절은 식 (1) 의 최소최대 게임만 다룬다", "답", INK2),
       ("물음: 2014 얼굴의 데이터셋", "원문의 얼굴 표본은 TFD (그림 2b) 뿐 — 개관판 그림 6 의 출처라고 적지는 않는다", "추정", INK2)]
for j, (a, c, v, col_) in enumerate(chk):
    y = 50 + j * 50
    b += box(20, y, 860, 44, fill=NODE, stroke=LINE)
    b += txt(32, y + 27, a, 12, anchor="start", weight="bold")
    b += txt(262, y + 27, c, 11, anchor="start", fill=INK2)
    b += box(770, y + 9, 100, 26, fill="#FFFFFF", stroke=col_)
    b += txt(820, y + 27, v, 11, fill=col_, weight="bold")
svg("fig15_cacm_check", W, H, b, "개관판 노트 유도와 원문 대조")


# ── 그림 16. 계보 ─────────────────────────────────────────────────────────────
W, H = 900, 430
b = defs()
b += txt(20, 30, "계보 — 원문 2절이 든 앞선 편과, 7절 결론의 다섯 확장이 이어진 자리 (오른쪽 칸 둘째 줄은 내가 이은 것, 읽지 않았다)", 14, anchor="start", weight="bold")
left = ["깊은 볼츠만 기계 (2009)", "잡음 대조 추정 (2010)", "예측 가능성 최소화 (1992)", "생성 확률망 (2014)", "VAE (2014, 같은 시기)"]
for j, l in enumerate(left):
    y = 60 + j * 66
    b += box(20, y, 210, 44, fill=FWD_SOFT, stroke=FWD)
    b += txt(125, y + 27, l, 12)
    b += line(230, y + 22, 330, 205, INK2, 1, marker="ai", op=0.6)
b += box(335, 170, 170, 70, fill=REV_SOFT, stroke=REV, sw=2)
b += txt(420, 200, "GAN", 16, weight="bold", fill=REV)
b += txt(420, 222, "NIPS 2014 (이 노트)", 11)
right = [("1. 조건부 p(x | c)", "Conditional GAN (Mirza · Osindero 2014)"),
         ("2. 배운 근사 추론 (x → z)", "BiGAN / ALI (2016)"),
         ("3. 모든 조건부 p(x_S | 나머지)", "(이을 편을 아직 못 골랐다)"),
         ("4. 준지도 학습", "Improved Techniques (Salimans 외 2016)"),
         ("5. G 와 D 맞추기 · 효율", "WGAN (2017), 수렴 분석 편들 (2017)")]
for j, (a, c) in enumerate(right):
    y = 56 + j * 66
    b += line(505, 205, 555, y + 26, INK2, 1, marker="ai", op=0.6)
    b += box(560, y, 320, 54, fill=NODE, stroke=LINE)
    b += txt(574, y + 22, a, 12, anchor="start", weight="bold")
    b += txt(574, y + 42, c, 11, anchor="start", fill=INK2)
b += box(335, 290, 170, 60, fill=NODE, stroke=LINE)
b += txt(420, 315, "CACM 2020 개관판", 12, weight="bold")
b += txt(420, 335, "(앞서 읽은 노트)", 11, fill=INK2)
b += line(420, 240, 420, 288, INK2, 1.2, marker="ai")
b += txt(450, 410, "왼쪽 다섯은 원문 2절이 직접 견준 편. 오른쪽 칸의 첫 줄은 원문 7절, 둘째 줄(뒤에 나온 편)은 내가 이은 것이다", 11, fill=MUTED)
svg("fig16_lineage", W, H, b, "GAN 계보")

print("끝")
