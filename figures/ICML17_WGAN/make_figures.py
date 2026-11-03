# -*- coding: utf-8 -*-
"""WGAN 노트(Arjovsky, Chintala, Bottou, arXiv:1701.07875v3)의 그림 열다섯을 만든다.

색과 글꼴은 앞선 GAN 노트 둘(CACM 2020 개관판 · NIPS 2014 원판)의 그림과 맞췄다 — 저장소의 노트들이
한 벌로 읽히게 하려는 것이다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

계산으로 원문을 확인하는 그림이 여럿이다 — 2(예 1 의 네 거리), 3(정리 2 의 부등식 셋을 가우스로),
4(가우스 이동에서 JS 와 W 와 그 기울기), 5(작은 이산 예에서 수송 계획과 쌍대 함수가 같은 값을 내는가),
7(그림 2 의 두 가우스에서 최적 판별기 · 최적 critic 과 생성기 기울기), 8(부록 D 정리 4 의 상수를
무차별 대입으로 확인), 12(MMD 비용 셈). 계산한 값은 돌릴 때 화면에도 찍는다.

그림 9 · 10 의 곡선 값은 원문 그림 3 · 4 · 8 의 PDF 안 그림 이미지(560x370 픽셀 안팎)에서 파란 픽셀의
중앙값으로 읽은 것이다. 읽은 값을 아래 READ_* 상수에 그대로 적어 두었다 — 이 파일은 PDF 를 읽지 않는다.
원문의 표본 사진(그림 3 · 4 · 5 · 6 · 7)은 crop_paper_figures.py 가 잘라 png 로 둔다.
"""
import io, os, math, itertools
from statistics import NormalDist

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"   # 그림 상자 배경
NODE      = "#F6F7F5"   # 노드 안쪽
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 판별기 · critic, 진짜 데이터 쪽
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 생성기, 가짜 데이터 쪽
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 잡음 z
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"   # 초록 — 된다
OK_SOFT   = "#D6EEDD"
NO        = "#C0392B"   # 빨강 — 안 된다
NO_SOFT   = "#F6D9D5"
# 거리 계열 색 — 넷을 한 그림에 겹칠 때만 쓴다.
C_W  = "#1E8449"   # EM(W) — 초록
C_JS = "#2A78D6"   # JS — 파랑
C_TV = "#8E44AD"   # TV — 보라
C_KL = "#B4552B"   # KL — 주황
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
            + arrow("an", NO) + arrow("ac", CODE) + arrow("aw", C_W) + "</defs>")


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


print("그림을 만든다 ->", OUT)

LN2 = math.log(2.0)
ND = NormalDist()


def npdf(x, m, s=1.0):
    return math.exp(-0.5 * ((x - m) / s) ** 2) / (s * math.sqrt(2 * math.pi))


DX = 0.002
GRID = [-14 + i * DX for i in range(int(36 / DX) + 1)]   # -14 ~ 22, 수치 적분 격자


def kl(p, q):
    s = 0.0
    for x in GRID:
        a = p(x)
        if a > 1e-300:
            s += a * math.log(a / max(q(x), 1e-300))
    return s * DX


def jsd(p, q):
    """젠슨-섀넌 발산. 1/2 무게가 붙은 꼴(위 끝 log 2) — 원문 부록 C 와 그림 1 의 꼴이다."""
    m = lambda x: 0.5 * (p(x) + q(x))
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def tv(p, q):
    """sup_A |P(A) - Q(A)| = (1/2) ∫ |p - q|. 원문 2절의 정의."""
    return 0.5 * sum(abs(p(x) - q(x)) for x in GRID) * DX


# ── 그림 1. 예 1 — 평행선 둘 ────────────────────────────────────────────────────
W, H = 880, 400
b = defs()
b += txt(20, 30, "예 1 (평행선 배우기) — P0 는 x = 0 위의 세로 선분, Pθ 는 x = θ 위의 세로 선분. 받침이 겹치지 않는다", 15, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 440, 70, 330
fx = lambda v: X0 + (v + 0.4) / 1.4 * (X1 - X0)
fy = lambda v: Y1 - v * (Y1 - Y0)
b += line(fx(-0.4), fy(0), fx(1.0), fy(0), INK2, 1.2)
b += line(fx(0), fy(-0.05), fx(0), fy(1.05), LINE, 1)
for t in (0.0, 0.6):
    b += line(fx(t), fy(0), fx(t), fy(0) + 4, INK2, 1)
b += txt(fx(0), fy(0) + 18, "0", 11, fill=MUTED)
b += txt(fx(0.6), fy(0) + 18, "θ = 0.6", 11, fill=MUTED)
b += txt(fx(-0.4) + 6, fy(1.0) + 4, "z = 1", 10, fill=MUTED, anchor="start")
b += txt(fx(-0.4) + 6, fy(0.0) - 6, "z = 0", 10, fill=MUTED, anchor="start")
b += line(fx(0), fy(0), fx(0), fy(1), FWD, 5)
b += line(fx(0.6), fy(0), fx(0.6), fy(1), REV, 5)
b += txt(fx(0) - 10, fy(0.5), "P0", 13, fill=FWD, anchor="end", weight="bold")
b += txt(fx(0.6) + 10, fy(0.5), "Pθ", 13, fill=REV, anchor="start", weight="bold")
for z in (0.1, 0.3, 0.5, 0.7, 0.9):
    b += line(fx(0) + 4, fy(z), fx(0.6) - 5, fy(z), C_W, 1.3, marker="aw", op=0.85)
b += txt((fx(0) + fx(0.6)) / 2, fy(0.98) - 10, "결합 γ: (0, z) 를 (θ, z) 로 옮긴다", 11, fill=C_W)
b += txt((X0 + X1) / 2, Y1 + 46, "Z ~ U[0, 1], gθ(z) = (θ, z). θ 하나가 선분을 가로로만 옮긴다", 11, fill=INK2)
b += box(470, 60, 390, 300, fill=NODE, stroke=LINE)
b += txt(485, 86, "원문이 적은 값 (θ ≠ 0 일 때)", 13, anchor="start", weight="bold")
rows1 = [("W(P0, Pθ) = |θ|  — 모든 질량을 가로로 |θ| 옮긴다", C_W, "bold"),
         ("JS(P0, Pθ) = log 2 = %.3f  — 받침이 따로라 위 끝" % LN2, C_JS),
         ("KL(Pθ‖P0) = KL(P0‖Pθ) = +∞", C_KL),
         ("δ(P0, Pθ) = 1  — A = P0 의 선분이면 1 − 0", C_TV),
         ("", INK2),
         ("θ = 0 이면 넷 모두 0", INK),
         ("", INK2),
         ("θt → 0 인 열은 W 로는 P0 에 수렴하고,", INK),
         ("JS · KL · 역 KL · TV 로는 수렴하지 않는다", INK),
         ("", INK2),
         ("W 로 재면 θ 에 대한 기울기가 늘 ±1 이다", INK2),
         ("나머지 셋은 θ ≠ 0 에서 상수라 기울기가 0", INK2)]
b += lines_at(485, 114, rows1, 12, 21)
svg("fig01_parallel_lines", W, H, b, "예 1 평행선 둘")


# ── 그림 2. 예 1 의 네 거리를 θ 의 함수로 ───────────────────────────────────────
W, H = 900, 400
b = defs()
b += txt(20, 30, "예 1 의 네 거리를 θ 의 함수로 — 원문 그림 1 은 왼쪽 둘(W · JS)만 그린다. KL 은 θ ≠ 0 에서 +∞ 라 그리지 않았다", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 70, 520, 60, 330
fx = lambda v: X0 + (v + 1) / 2 * (X1 - X0)
fy = lambda v: Y1 - v / 1.5 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [-1, -0.5, 0, 0.5, 1], [0, 0.5, 1.0, 1.5], fx, fy, "θ", "값")
ths = [-1 + i * 0.025 for i in range(81)]
b += polyline([(fx(t), fy(abs(t))) for t in ths], C_W, 2.4)
for seg in ((-1, -0.012), (0.012, 1)):
    b += line(fx(seg[0]), fy(LN2), fx(seg[1]), fy(LN2), C_JS, 2.4)
    b += line(fx(seg[0]), fy(1.0), fx(seg[1]), fy(1.0), C_TV, 2.0, dash="6 4")
    b += line(fx(seg[0]), fy(2 * LN2), fx(seg[1]), fy(2 * LN2), C_JS, 1.4, dash="2 3")
b += circ(fx(0), fy(0), 4, fill=INK, stroke=INK)
b += txt(fx(-0.64), fy(0.5), "W = |θ|", 12, fill=C_W, anchor="end", weight="bold")
b += txt(fx(0.05), fy(LN2) - 8, "JS = log 2 = %.3f (1/2 무게)" % LN2, 11, fill=C_JS, anchor="start")
b += txt(fx(0.05), fy(1.0) - 8, "δ (TV) = 1", 11, fill=C_TV, anchor="start")
b += txt(fx(-0.98), fy(2 * LN2) - 8, "2 log 2 = %.3f — 2절 정의(1/2 없음)대로면 이 값" % (2 * LN2), 11, fill=C_JS, anchor="start")
b += txt(fx(0) + 8, fy(0) - 8, "θ = 0: 넷 모두 0", 10, fill=INK, anchor="start")
b += box(550, 60, 330, 290, fill=NODE, stroke=LINE)
b += txt(565, 86, "원문 그림 1 의 눈금을 읽은 것", 13, anchor="start", weight="bold")
rows2 = [("왼쪽: W 가 θ = ±1 에서 1, 0 에서 0 인 V 자", INK),
         ("오른쪽: JSD 가 θ ≠ 0 에서 0.69 로 평평,", INK),
         ("θ = 0 한 점만 0", INK),
         ("", INK),
         ("오른쪽 축의 0.69 는 log 2 = %.3f 다." % LN2, INK2),
         ("곧 그림은 1/2 무게가 붙은 JS 를 그렸다", INK2),
         ("", INK),
         ("원문 2절의 정의 JS = KL(Pr‖Pm) + KL(Pg‖Pm)", NO),
         ("에는 1/2 이 없다. 그 정의를 그대로 쓰면", NO),
         ("예 1 의 값은 2 log 2 = %.3f 이 된다" % (2 * LN2), NO),
         ("부록 C (정리 2 의 증명)는 1/2 을 붙여 쓴다", INK2)]
b += lines_at(565, 112, rows2, 12, 21)
svg("fig02_four_distances", W, H, b, "예 1 의 네 거리")
print("  [2] 예 1: JS(1/2 무게) = %.4f, 2절 정의대로 = %.4f, TV = 1, W = |θ|" % (LN2, 2 * LN2))


# ── 그림 3. 정리 2 — 위상의 세기 순서와 증명의 부등식 ──────────────────────────────
gpairs = [0.25, 0.5, 1.0, 2.0]
rows3 = []
for m in gpairs:
    p = lambda x: npdf(x, 0.0)
    q = lambda x, m=m: npdf(x, m)
    d = tv(p, q)
    j = jsd(p, q)
    k = m * m / 2
    rows3.append((m, d, 2 * ND.cdf(m / 2) - 1, j, k, math.sqrt(k / 2), math.sqrt(2 * j), 2 * math.sqrt(j)))
W, H = 900, 450
b = defs()
b += txt(20, 30, "정리 2 — 위상이 센 차례: KL ⇒ (JS ⇔ TV) ⇒ (W ⇔ 분포 수렴). 왼쪽으로 수렴하면 오른쪽으로도 수렴한다", 15, anchor="start", weight="bold")
nodes = [(40, "KL(Pn‖P) → 0", "또는 KL(P‖Pn) → 0", C_KL, "가장 세다"),
         (250, "JS(Pn, P) → 0", "⇔ δ(Pn, P) → 0", C_JS, "둘이 같은 위상"),
         (460, "W(Pn, P) → 0", "⇔ Pn 이 분포로 P 에 수렴", C_W, "가장 약하다")]
for x, t1, t2, col, lab in nodes:
    b += box(x, 62, 190, 74, fill=NODE, stroke=col, sw=1.8)
    b += txt(x + 95, 90, t1, 13, fill=col, weight="bold")
    b += txt(x + 95, 112, t2, 12, fill=INK2)
    b += txt(x + 95, 154, lab, 11, fill=MUTED)
b += line(232, 99, 248, 99, INK2, 1.6, marker="ai")
b += line(442, 99, 458, 99, INK2, 1.6, marker="ai")
b += txt(240, 84, "(3)", 10, fill=MUTED)
b += txt(450, 84, "(4)", 10, fill=MUTED)
b += box(670, 62, 210, 92, fill=NODE, stroke=LINE)
b += lines_at(682, 84, [("항목 (3): 핀스커 부등식", INK),
                        ("항목 (1): 핀스커 + 삼각 부등식", INK),
                        ("항목 (2): 바깥 결과 [22] 인용", INK2),
                        ("항목 (4): 강 · 약* 위상", INK2)], 11, 18)
X0 = 40
b += txt(X0, 196, "증명이 쓰는 부등식을 P = N(0, 1), Pn = N(m, 1) 로 확인 (내 계산, 수치 적분 간격 0.002)", 13, anchor="start", weight="bold")
cols3 = ["m", "δ (적분)", "δ (닫힌 꼴)", "JS (nat)", "KL = m²/2", "√(KL/2)", "√(2·JS)", "2·√JS (원문)"]
cx = [60, 150, 250, 350, 440, 540, 640, 760]
for c, t in zip(cx, cols3):
    b += txt(c, 226, t, 12, weight="bold", fill=INK2)
b += line(X0, 234, 860, 234, LINE, 1)
for i, r in enumerate(rows3):
    y = 256 + 26 * i
    vals = ["%.2f" % r[0], "%.4f" % r[1], "%.4f" % r[2], "%.4f" % r[3], "%.4f" % r[4], "%.4f" % r[5], "%.4f" % r[6], "%.4f" % r[7]]
    for c, t in zip(cx, vals):
        b += txt(c, y, t, 12)
b += lines_at(X0, 380, [("핀스커: δ ≤ √(KL/2) — 넷 다 성립. 원문의 항목 (1) 끝은 δ ≤ 2√JS 로 적는데, 같은 줄의 앞 부등식에서 나오는 것은 √(2·JS) 이고 2√JS 는 그보다 늘 크다(느슨하지만 맞다)", INK2),
                        ("이 확인은 가우스 넷에 대한 것이고 정리의 증명이 아니다. 정리는 받침이 콤팩트한 공간을 가정한다 — 가우스는 그 가정 밖이라 부등식만 확인했다", MUTED)], 11, 20)
svg("fig03_topology_order", W, H, b, "정리 2 위상의 순서")
for r in rows3:
    print("  [3] m=%.2f  TV=%.4f(닫힌꼴 %.4f)  JS=%.4f  KL=%.4f  sqrt(KL/2)=%.4f  sqrt(2JS)=%.4f  2sqrtJS=%.4f" % r)


# ── 그림 4. 가우스 이동 — JS 는 위 끝에 붙고 W 는 곧게 큰다 ─────────────────────────
ms = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 8]
rows4 = []
for m in ms:
    p = lambda x: npdf(x, 0.0)
    jm = lambda mm: jsd(p, lambda x: npdf(x, mm))
    j = jm(m)
    h = 0.01
    dj = (jm(m + h) - jm(max(m - h, 0))) / (m + h - max(m - h, 0))
    rows4.append((m, j, j / LN2, dj, float(m), 2 * ND.cdf(m / 2) - 1))
W, H = 920, 470
b = defs()
b += txt(20, 30, "P_r = N(0, 1), Pθ = N(m, 1) — m 을 옮길 때 JS 는 log 2 에 붙어 평평해지고 W 는 m 그대로 큰다 (내 계산)", 15, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 70, 430, 70, 330
fx = lambda v: X0 + v / 8 * (X1 - X0)
fy = lambda v: Y1 - v / 1.0 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [0, 2, 4, 6, 8], [0, 0.25, 0.5, 0.75, 1.0], fx, fy, "m (평균 차이)", "위 끝으로 나눈 값")
b += polyline([(fx(r[0]), fy(r[2])) for r in rows4], C_JS, 2.4)
b += polyline([(fx(r[0]), fy(r[5])) for r in rows4], C_TV, 2.0, dash="6 4")
b += polyline([(fx(r[0]), fy(r[0] / 8)) for r in rows4], C_W, 2.4)
r5 = [r for r in rows4 if r[0] == 5][0]
b += circ(fx(5), fy(r5[2]), 4, fill=C_JS, stroke=C_JS)
b += line(fx(5), fy(r5[2]) + 4, fx(5.6), fy(0.56), C_JS, 1)
b += txt(fx(5.6), fy(0.53), "m = 5: JS 가 log 2 의 %.1f%%" % (100 * r5[2]), 11, fill=C_JS)
b += box(fx(4.6), fy(0.42), fx(8) - fx(4.6) - 4, fy(0.06) - fy(0.42), fill=NODE, stroke=LINE)
for j, (lab, col, dash) in enumerate([("JS / log 2", C_JS, None), ("δ (TV, 위 끝 1)", C_TV, "6 4"), ("W / 8 (W = m, 위 끝 없음)", C_W, None)]):
    yy = fy(0.36) + 22 * j
    b += line(fx(4.75), yy - 4, fx(5.25), yy - 4, col, 2.2, dash=dash)
    b += txt(fx(5.35), yy, lab, 11, fill=col, anchor="start")
X0b, X1b = 500, 880
fxb = lambda v: X0b + v / 8 * (X1b - X0b)
fyb = lambda v: Y1 - v / 1.2 * (Y1 - Y0)
b += axes(X0b, Y0, X1b, Y1, [0, 2, 4, 6, 8], [0, 0.4, 0.8, 1.2], fxb, fyb, "m", "m 에 대한 기울기")
b += polyline([(fxb(r[0]), fyb(r[3])) for r in rows4], C_JS, 2.4)
b += line(fxb(0), fyb(1.0), fxb(8), fyb(1.0), C_W, 2.4)
b += txt(fxb(7.9), fyb(1.0) - 8, "dW/dm = 1 (어디서나)", 11, fill=C_W, anchor="end", weight="bold")
b += txt(fxb(2.3), fyb(0.24) - 10, "dJS/dm", 11, fill=C_JS, anchor="start", weight="bold")
b += circ(fxb(5), fyb(r5[3]), 4, fill=C_JS, stroke=C_JS)
b += txt(fxb(5), fyb(r5[3]) - 12, "m = 5: %.4f" % r5[3], 11, fill=C_JS)
b += lines_at(70, 400, [("JS 는 m 이 커지면 log 2 = %.3f 로 다가가기만 하고 닿지 않는다(가우스는 받침이 겹친다). 예 1 처럼 받침이 따로면 θ ≠ 0 에서 정확히 log 2 이고 기울기가 정확히 0 이다" % LN2, INK2),
                        ("m = 5 의 %.1f%% 는 CACM 개관판 노트 9절의 계산과 같은 설정 · 같은 값이다. 둘 다 판별기가 최적이라는 가정 위의 값이고, 학습 중인 판별기가 내는 값이 아니다" % (100 * r5[2]), INK2)], 11, 20)
svg("fig04_gaussian_shift", W, H, b, "가우스 이동에서 JS 와 W")
for r in rows4:
    print("  [4] m=%.1f  JS=%.4f (log2 의 %.1f%%)  dJS/dm=%.5f  W=%.1f  TV=%.4f" % (r[0], r[1], 100 * r[2], r[3], r[4], r[5]))


# ── 그림 5. 이산 예 — 수송 계획(식 1)과 쌍대 함수(식 2)가 같은 값을 내는가 ─────────────
xs5 = [0, 1, 2]
pr5 = [0.5, 0.3, 0.2]
pg5 = [0.2, 0.3, 0.5]
step = 0.05
best_primal, best_plan = None, None
n = int(round(1 / step))
for a, bb, c, d in itertools.product(range(n + 1), repeat=4):
    g = [[None] * 3 for _ in range(3)]
    g[0][0], g[0][1], g[1][0], g[1][1] = a * step, bb * step, c * step, d * step
    g[0][2] = pr5[0] - g[0][0] - g[0][1]
    g[1][2] = pr5[1] - g[1][0] - g[1][1]
    g[2][0] = pg5[0] - g[0][0] - g[1][0]
    g[2][1] = pg5[1] - g[0][1] - g[1][1]
    g[2][2] = pr5[2] - g[2][0] - g[2][1]
    if min(min(r) for r in g) < -1e-9 or abs(g[0][2] + g[1][2] + g[2][2] - pg5[2]) > 1e-9:
        continue
    cost = sum(g[i][j] * abs(xs5[i] - xs5[j]) for i in range(3) for j in range(3))
    if best_primal is None or cost < best_primal - 1e-12:
        best_primal, best_plan = cost, [r[:] for r in g]
best_dual, best_f = None, None
fgrid = [-2 + i * 0.05 for i in range(81)]
for f0, f1 in itertools.product(fgrid, repeat=2):
    f = [f0, f1, 0.0]
    if abs(f[0] - f[1]) > 1 + 1e-9 or abs(f[1] - f[2]) > 1 + 1e-9 or abs(f[0] - f[2]) > 2 + 1e-9:
        continue
    v = sum(f[i] * (pr5[i] - pg5[i]) for i in range(3))
    if best_dual is None or v > best_dual + 1e-12:
        best_dual, best_f = v, f
cdf_gap = sum(abs(sum(pr5[:k + 1]) - sum(pg5[:k + 1])) for k in range(2))
W, H = 920, 440
b = defs()
b += txt(20, 30, "식 (1) 과 식 (2) 가 같은 값을 내는가 — 점 셋(0, 1, 2) 위의 작은 이산 예 (내가 고른 수)", 15, anchor="start", weight="bold")
fx5 = lambda v: 90 + v * 150
for i, x in enumerate(xs5):
    b += box(fx5(x) - 22, 200 - pr5[i] * 220, 20, pr5[i] * 220, fill=FWD_SOFT, stroke=FWD, rx=2)
    b += box(fx5(x) + 2, 200 - pg5[i] * 220, 20, pg5[i] * 220, fill=REV_SOFT, stroke=REV, rx=2)
    b += txt(fx5(x) - 12, 200 - pr5[i] * 220 - 6, "%.1f" % pr5[i], 10, fill=FWD)
    b += txt(fx5(x) + 12, 200 - pg5[i] * 220 - 6, "%.1f" % pg5[i], 10, fill=REV)
    b += txt(fx5(x), 218, "x = %d" % x, 11, fill=INK2)
b += line(50, 200, 430, 200, INK2, 1.2)
b += txt(60, 70, "P_r (파랑) · P_g (주황)", 12, anchor="start", fill=INK2)
b += path("M%.1f,236 C%.1f,276 %.1f,276 %.1f,236" % (fx5(0) - 12, fx5(0) + 60, fx5(2) - 60, fx5(2) + 12), C_W, sw=2, marker="aw")
b += txt(fx5(1), 290, "0.3 을 0 → 2 로 (거리 2)", 11, fill=C_W)
b += lines_at(40, 322, [("식 (1) — 수송 계획 γ 에 대해 최소화", INK, "bold"),
                        ("결합 γ 를 0.05 간격 격자로 모두 훑은 최솟값 = %.4f" % best_primal, C_W),
                        ("최적 계획의 하나: 0 에 0.2 · 1 에 0.3 은 그대로, 0 의 0.3 을 2 로", INK2),
                        ("1 차원 닫힌 꼴 Σ |F_r − F_g| = %.4f 와 같다" % cdf_gap, INK2)], 12, 21)
b += box(470, 60, 430, 360, fill=NODE, stroke=LINE)
b += txt(485, 86, "식 (2) — 1-립시츠 함수 f 에 대해 최대화", 13, anchor="start", weight="bold")
fy5 = lambda v: 250 - v * 60
for i in range(3):
    b += circ(520 + 140 * i, fy5(best_f[i]), 5, fill=C_W, stroke=C_W)
    b += txt(520 + 140 * i, fy5(best_f[i]) - 12, "f(%d) = %.2f" % (i, best_f[i]), 11, fill=C_W)
b += polyline([(520 + 140 * i, fy5(best_f[i])) for i in range(3)], C_W, 1.6, dash="4 3")
b += lines_at(485, 330, [("f 를 0.05 간격으로 훑은 최댓값 = %.4f" % best_dual, C_W, "bold"),
                         ("E_r[f] − E_g[f] 를 가장 크게 하는 f 는 기울기 −1 의 직선", INK2),
                         ("(상수를 더해도 값이 같아 f(2) = 0 으로 두었다)", MUTED),
                         ("두 값이 같다 — 칸토로비치-루빈시테인 쌍대의 한 예", INK)], 12, 21)
svg("fig05_transport_dual", W, H, b, "수송 계획과 쌍대 함수")
print("  [5] 이산 예: 식 (1) 격자 최소 = %.4f, 식 (2) 격자 최대 = %.4f, 닫힌 꼴 = %.4f, f = %s" % (best_primal, best_dual, cdf_gap, ["%.2f" % v for v in best_f]))
print("      최적 계획 = %s" % [["%.2f" % v for v in r] for r in best_plan])


# ── 그림 6. 알고리즘 1 ────────────────────────────────────────────────────────
NCRIT = 5
GEN_IT = 600000
loop_lit = NCRIT + 1
W, H = 900, 500
b = defs()
b += txt(20, 30, "알고리즘 1 (WGAN) — critic 을 n_critic 번 배우고 생성기를 한 번. 원문 기본값 α = 0.00005, c = 0.01, m = 64, n_critic = 5", 14, anchor="start", weight="bold")
b += box(30, 50, 560, 430, fill="none", stroke=INK2, sw=1.2, dash="6 4")
b += txt(45, 72, "θ 가 수렴하지 않은 동안 (1행)", 12, anchor="start", fill=INK2, weight="bold")
b += box(55, 85, 510, 250, fill="none", stroke=FWD, sw=1.2, dash="4 3")
b += txt(70, 106, "for t = 0, ..., n_critic (2행) — critic", 12, anchor="start", fill=FWD, weight="bold")
steps6 = [(118, "진짜 m 개 x 를 P_r 에서, 잡음 m 개 z 를 p(z) 에서 (3 · 4행)", CODE_SOFT, CODE),
          (166, "g_w ← ∇_w [ (1/m) Σ f_w(x) − (1/m) Σ f_w(g_θ(z)) ] (5행)", FWD_SOFT, FWD),
          (214, "w ← w + α · RMSProp(w, g_w) — 올린다 (6행)", FWD_SOFT, FWD),
          (262, "w ← clip(w, −c, c) — 무게를 상자 [−c, c] 에 (7행)", NO_SOFT, NO)]
for y, t, f, s in steps6:
    b += box(75, y, 460, 36, fill=f, stroke=s)
    b += txt(305, y + 23, t, 12)
for y in (154, 202, 250):
    b += line(305, y, 305, y + 11, INK2, 1.2, marker="ai")
b += path("M535,280 C568,280 568,136 535,136", FWD, sw=1.4, dash="4 3", marker="af")
b += txt(560, 314, "n_critic 번", 11, fill=FWD, anchor="end")
b += line(305, 335, 305, 356, INK2, 1.2, marker="ai")
b += box(75, 358, 460, 36, fill=CODE_SOFT, stroke=CODE)
b += txt(305, 381, "잡음 m 개를 새로 (9행)", 12)
b += line(305, 394, 305, 410, INK2, 1.2, marker="ai")
b += box(75, 412, 460, 50, fill=REV_SOFT, stroke=REV)
b += txt(305, 432, "g_θ ← −∇_θ (1/m) Σ f_w(g_θ(z)),  θ ← θ − α · RMSProp(θ, g_θ)", 12)
b += txt(305, 452, "(10 · 11행) — 생성기는 f_w(g_θ(z)) 를 올린다", 11, fill=INK2)
b += box(610, 50, 270, 430, fill=NODE, stroke=LINE)
b += txt(625, 74, "원문에서 확인한 것", 13, anchor="start", weight="bold")
rows6 = [("로그 · 시그모이드가 없다", INK),
         ("critic 출력이 확률이 아니다", INK2),
         ("최적화기는 RMSProp — Adam(β1 > 0)", INK),
         ("은 「가끔 불안정」해 바꿨다 (4.2절)", INK2),
         ("", INK),
         ("2행 「t = 0, ..., n_critic」 은", NO),
         ("글자 그대로 세면 %d 번이다" % loop_lit, NO),
         ("요구 조건 줄의 뜻(생성기 한 번당", INK2),
         ("critic 반복 수)은 %d 번" % NCRIT, INK2),
         ("", INK),
         ("그림 3 의 생성기 반복 %s 번이면" % "{:,}".format(GEN_IT), INK),
         ("critic 갱신 %s ~ %s 번," % ("{:,}".format(GEN_IT * NCRIT), "{:,}".format(GEN_IT * loop_lit)), INK2),
         ("critic 이 본 진짜 이미지", INK2),
         ("%s ~ %s 장 (내 셈)" % ("{:,}".format(GEN_IT * NCRIT * 64), "{:,}".format(GEN_IT * loop_lit * 64)), INK2),
         ("", INK),
         ("원문: 「모든 실험이 기본값을 썼다」", INK),
         ("그림 3 아래 칸 캡션은 「학습률이", NO),
         ("상당히 높은」 실행이라고 적는다", NO)]
b += lines_at(625, 100, rows6, 12, 21)
svg("fig06_algorithm1", W, H, b, "알고리즘 1 흐름")
print("  [6] 2행을 글자대로 세면 %d 번. 생성기 %d 번 -> critic %d ~ %d 번, 진짜 이미지 %d ~ %d 장" % (loop_lit, GEN_IT, GEN_IT * NCRIT, GEN_IT * loop_lit, GEN_IT * NCRIT * 64, GEN_IT * loop_lit * 64))


# ── 그림 7. 원문 그림 2 — 최적 판별기는 포화하고 critic 은 곧다 ─────────────────────────
# 원문 그림 2 의 두 밀도는 꼭대기 0.40 · 중심 ±5 로 읽혀 N(-5, 1)(진짜) · N(5, 1)(가짜)로 둔다.
MR, MG = -5.0, 5.0
def dstar(x):
    # p_r / (p_r + p_g). 분산이 같은 두 가우스면 로짓이 (MG - MR) * (MR + MG - 2x) / 2 = -10x
    a = -(MG - MR) * x + (MG * MG - MR * MR) / 2.0
    return 1.0 / (1.0 + math.exp(-a)) if a > -700 else 0.0
# 원문 그림 2 의 critic 을 픽셀로 읽은 값 (x, f). 세로 1 픽셀 = 0.0029, 선 굵기 2 픽셀.
READ_CRITIC = [(-7.9, -0.396), (-7, -0.359), (-6, -0.317), (-5, -0.276), (-4, -0.235), (-3, -0.193),
               (-2, -0.154), (-1, -0.110), (-0.5, -0.069), (0, -0.031), (0.5, 0.007), (1, 0.048),
               (3, 0.124), (4, 0.161), (5, 0.199), (6, 0.236), (7, 0.274), (7.9, 0.309)]
READ_DISC = [(-0.5, 0.971), (0.0, 0.027), (0.5, 0.003), (5.0, 0.003)]
sl_left = (READ_CRITIC[7][1] - READ_CRITIC[0][1]) / (READ_CRITIC[7][0] - READ_CRITIC[0][0])
sl_mid = (READ_CRITIC[11][1] - READ_CRITIC[7][1]) / (READ_CRITIC[11][0] - READ_CRITIC[7][0])
sl_right = (READ_CRITIC[-1][1] - READ_CRITIC[11][1]) / (READ_CRITIC[-1][0] - READ_CRITIC[11][0])
f_real = dict(READ_CRITIC)[-5]
f_fake = dict(READ_CRITIC)[5]
W1_true = MG - MR
Keff = (f_fake - f_real) / W1_true
d5 = dstar(MG)
grad_mgan = (MG - MR) * d5               # |d/dx log(1 - D*(x))| at x = 5 = 10 * D*
grad_ns = (MG - MR) * (1 - d5)           # |d/dx (-log D*(x))| at x = 5 = 10 * (1 - D*)
W, H = 920, 540
b = defs()
b += txt(20, 30, "원문 그림 2 를 다시 그림 — N(−5, 1) 진짜, N(5, 1) 가짜. 판별기는 원 GAN 식 (2) 의 D* 를 계산, critic 은 원문 그림에서 읽은 값", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 70, 540, 60, 380
fx = lambda v: X0 + (v + 8) / 16 * (X1 - X0)
fy = lambda v: Y1 - (v + 0.4) / 1.4 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [-8, -4, 0, 4, 8], [-0.4, 0, 0.4, 0.8, 1.0], fx, fy, "x", None)
xx = [-8 + i * 0.02 for i in range(801)]
b += polyline([(fx(x), fy(npdf(x, MR))) for x in xx], FWD, 1.8)
b += polyline([(fx(x), fy(npdf(x, MG))) for x in xx], OK, 1.8)
b += polyline([(fx(x), fy(dstar(x))) for x in xx], NO, 2.2)
b += polyline([(fx(x), fy(v)) for x, v in READ_CRITIC], "#17A2B8", 2.4)
for x, v in READ_CRITIC:
    b += circ(fx(x), fy(v), 2.5, fill="#17A2B8", stroke="#17A2B8")
b += txt(fx(-5), fy(0.44), "진짜 N(−5, 1)", 11, fill=FWD)
b += txt(fx(5), fy(0.44), "가짜 N(5, 1)", 11, fill=OK)
b += txt(fx(-1.2), fy(0.92), "D*(x) = σ(−10x)", 11, fill=NO, anchor="end", weight="bold")
b += txt(fx(-7.8), fy(-0.1), "critic (원문 그림 읽기)", 11, fill="#17A2B8", anchor="start", weight="bold")
b += box(570, 60, 330, 420, fill=NODE, stroke=LINE)
b += txt(585, 86, "계산한 것 (내 계산)", 13, anchor="start", weight="bold")
rows7 = [("가짜 중심 x = 5 에서 D* = %.1e" % d5, NO),
         ("원 GAN 꼴 log(1 − D) 의 x 기울기 크기", INK),
         ("= 10 · D* = %.1e — 사라진다" % grad_mgan, NO),
         ("−log D 꼴(NS)의 기울기 크기", INK),
         ("= 10 · (1 − D*) = %.1f — 안 사라진다" % grad_ns, OK),
         ("원문 그림 2 의 「사라지는 기울기」는", INK2),
         ("식 (1) 그대로인 최소최대 꼴의 이야기다", INK2),
         ("", INK),
         ("critic 을 읽은 값 (세로 읽기 ±0.005)", INK, "bold"),
         ("기울기: 왼쪽 %.3f · 가운데 %.3f · 오른쪽 %.3f" % (sl_left, sl_mid, sl_right), "#17A2B8"),
         ("f(−5) = %.3f, f(5) = %.3f" % (f_real, f_fake), INK2),
         ("참 W = %.0f 인데 E_r f − E_g f = %.3f" % (W1_true, f_real - f_fake), INK2),
         ("— 크기 비 %.4f 는 클리핑이 정한 K 로 읽힌다" % abs(Keff), INK2),
         ("부호가 식 (3) 의 f 와 반대다 (가짜 쪽이 높다)", NO),
         ("— 그림은 −f 를 그린 것으로 읽힌다", INK2)]
b += lines_at(585, 112, rows7, 12, 23)
b += txt(30, 504, "원문 그림 2 는 두 가우스의 평균 · 분산, 판별기 · critic 의 망 모양, 학습 걸음 수를 적지 않는다. 밀도 꼭대기 0.40 과 중심 ±5 는 눈금에서 읽었다", 11, fill=MUTED, anchor="start")
b += txt(30, 524, "D* 곡선은 원문 그림의 빨강 곡선과 모양이 같다(−0.5 에서 0.97, 0 에서 0.03 으로 읽힘) — 원문 곡선은 학습한 판별기이고 이 곡선은 원 GAN 식 (2) 의 해다", 11, fill=MUTED, anchor="start")
svg("fig07_critic_vs_discriminator", W, H, b, "최적 판별기와 critic")
print("  [7] D*(5)=%.3e  |grad log(1-D*)|=%.3e  |grad -logD*|=%.4f" % (d5, grad_mgan, grad_ns))
print("      critic 기울기 왼 %.4f 가운데 %.4f 오른 %.4f, f(-5)=%.3f f(5)=%.3f, E_r f - E_g f=%.3f, K_eff=%.4f" % (sl_left, sl_mid, sl_right, f_real, f_fake, f_real - f_fake, abs(Keff)))


# ── 그림 8. 부록 D 정리 4 — EBGAN 의 생성기 비용은 δ 에 비례, 그런데 상수가 m/2 인가 m 인가 ──────
def ebgan_check(pr, pq, mm, stepn=20):
    grid = [mm * i / stepn for i in range(stepn + 1)]
    best = None
    for D in itertools.product(grid, repeat=len(pr)):
        LD = sum(pr[i] * D[i] for i in range(len(pr))) + sum(pq[i] * max(0.0, mm - D[i]) for i in range(len(pr)))
        if best is None or LD < best[0] - 1e-12:
            best = (LD, D)
    LD, D = best
    LG = sum(pq[i] * D[i] for i in range(len(pr))) - sum(pr[i] * D[i] for i in range(len(pr)))
    delta = max(abs(sum(pr[i] for i in A) - sum(pq[i] for i in A))
                for k in range(len(pr) + 1) for A in itertools.combinations(range(len(pr)), k))
    l1 = sum(abs(pr[i] - pq[i]) for i in range(len(pr)))
    return LD, D, LG, delta, l1
cases8 = [((0.7, 0.3, 0.0), (0.2, 0.3, 0.5), 1.0),
          ((0.5, 0.5, 0.0), (0.0, 0.5, 0.5), 2.0),
          ((0.4, 0.4, 0.2), (0.1, 0.3, 0.6), 1.0),
          ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1.0)]
res8 = [ebgan_check(a, c, mm) for a, c, mm in cases8]
W, H = 920, 450
b = defs()
b += txt(20, 30, "부록 D 정리 4 를 무차별 대입으로 — 최적 판별기에서 EBGAN 생성기 비용 L_G 는 δ 에 비례한다. 상수는 m/2 가 아니라 m 으로 나왔다", 14, anchor="start", weight="bold")
heads8 = ["P_r", "P_θ", "m", "δ = sup|P_r(A)−P_θ(A)|", "Σ|p_r − p_θ|", "L_G (최적 D)", "원문 (m/2)·δ", "m·δ"]
cx8 = [80, 210, 300, 420, 560, 660, 760, 850]
for c, t in zip(cx8, heads8):
    b += txt(c, 76, t, 11, weight="bold", fill=INK2)
b += line(30, 86, 890, 86, LINE, 1)
for i, ((a, c, mm), (LD, D, LG, delta, l1)) in enumerate(zip(cases8, res8)):
    y = 112 + 30 * i
    vals = ["(%s)" % ", ".join("%.1f" % v for v in a), "(%s)" % ", ".join("%.1f" % v for v in c), "%.0f" % mm,
            "%.2f" % delta, "%.2f" % l1, "%.3f" % LG, "%.3f" % (mm / 2 * delta), "%.3f" % (mm * delta)]
    for cc, t in zip(cx8, vals):
        b += txt(cc, y, t, 12, fill=(OK if cc == 850 else (NO if cc == 760 else INK)))
b += lines_at(30, 258, [("판별기 D 를 각 점에서 [0, m] 의 21 칸 격자로 모두 훑어 L_D = E_r[D] + E_θ[[m − D]+] 를 가장 작게 하는 D 를 고르고, 그 D 에서 L_G = E_θ[D] − E_r[D] 를 쟀다", INK2),
                        ("어긋나는 자리: 원문 2절과 부록 A 는 δ 를 sup_A |P_r(A) − P_θ(A)| 로 정의한다. 식 (7) 의 증명 끝은 |μ|(X) = ‖μ‖_TV = δ 로 적는데,", INK),
                        ("두 확률 분포의 차 μ 에서 |μ|(X) = Σ|p_r − p_θ| 는 sup_A |μ(A)| 의 두 배다 (위 표의 다섯째 칸 = 넷째 칸의 2 배)", INK),
                        ("그래서 inf_{−1≤f≤1} (E_r f − E_θ f) 는 −δ 가 아니라 −2δ 이고, 정리 4 의 상수는 m 이 된다. 「δ 에 비례한다」 는 결론은 그대로 선다", OK),
                        ("같은 두 배가 5절의 「|f| ≤ 1 인 함수 모임의 IPM 은 δ 다」 와 부록 A 의 「Φ 는 등거리」 에도 걸린다 — 정의를 Σ|p − q| 쪽으로 읽으면 셋 다 맞는다", INK2),
                        ("이 확인은 내가 한 것이고, 세 이산 예에서 나온 값이다. 받침이 따로인 예(넷째 줄)는 손으로도 L_G = m 이 나온다: 진짜 쪽 D = 0, 가짜 쪽 D = m, δ = 1", MUTED)], 11, 22)
svg("fig08_ebgan_tv_constant", W, H, b, "EBGAN 정리 4 상수 확인")
for (a, c, mm), (LD, D, LG, delta, l1) in zip(cases8, res8):
    print("  [8] Pr=%s Pθ=%s m=%.0f: D*=%s L_D=%.3f L_G=%.3f δ=%.2f Σ|.|=%.2f (m/2)δ=%.3f mδ=%.3f" % (a, c, mm, ["%.2f" % v for v in D], LD, LG, delta, l1, mm / 2 * delta, mm * delta))


# ── 그림 9. 원문 그림 3 을 읽은 값 — WGAN 의 EM 추정 곡선 ────────────────────────────
# 원문 그림 3 의 PDF 안 이미지(560x373 픽셀)에서 파란 픽셀 중앙값으로 읽었다. 세로 1 픽셀 = 0.0114(위 두 칸),
# 0.059(아래 칸). 선 굵기가 2~3 픽셀이라 위 두 칸의 읽기 오차를 ±0.02 로 적는다.
READ_F3_MLP = [(2000, 1.46), (10000, 1.40), (50000, 1.18), (100000, 0.80), (200000, 0.55), (300000, 0.46),
               (400000, 0.40), (500000, 0.39), (590000, 0.38)]
READ_F3_DCGAN = [(2000, 1.35), (10000, 1.04), (50000, 0.40), (100000, 0.26), (200000, 0.19), (300000, 0.15),
                 (400000, 0.13), (500000, 0.13), (590000, 0.12)]
READ_F3_MLPMLP = [(20000, 14.7, 15.4, 15.9), (100000, 14.8, 15.4, 16.0), (300000, 14.6, 15.2, 15.8), (590000, 14.7, 15.3, 15.9)]
W, H = 920, 470
b = defs()
b += txt(20, 30, "원문 그림 3 을 픽셀로 읽은 값 — WGAN 학습 중 EM 추정(식 3). 원문 곡선은 중앙값 거르개를 거친 것이다", 15, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 70, 500, 70, 360
fx = lambda v: X0 + v / 600000 * (X1 - X0)
fy = lambda v: Y1 - v / 1.6 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [0, 200000, 400000, 600000], [0, 0.4, 0.8, 1.2, 1.6], fx, fy, "생성기 반복", "EM 추정", xfmt="%d")
b += polyline([(fx(x), fy(v)) for x, v in READ_F3_MLP], REV, 2.4)
b += polyline([(fx(x), fy(v)) for x, v in READ_F3_DCGAN], FWD, 2.4)
for x, v in READ_F3_MLP:
    b += circ(fx(x), fy(v), 3, fill=REV, stroke=REV)
for x, v in READ_F3_DCGAN:
    b += circ(fx(x), fy(v), 3, fill=FWD, stroke=FWD)
b += txt(fx(600000), fy(0.38) - 10, "MLP 생성기 %.2f" % READ_F3_MLP[-1][1], 11, fill=REV, anchor="end", weight="bold")
b += txt(fx(600000), fy(0.12) - 8, "DCGAN 생성기 %.2f" % READ_F3_DCGAN[-1][1], 11, fill=FWD, anchor="end", weight="bold")
b += box(530, 60, 370, 390, fill=NODE, stroke=LINE)
b += txt(545, 86, "읽은 값 (위 두 칸 ±0.02)", 13, anchor="start", weight="bold")
rows9 = [("위 두 칸: critic 은 둘 다 시그모이드 뺀 DCGAN", INK),
         ("— 그래서 두 곡선끼리는 견줄 수 있다 (캡션)", INK2),
         ("MLP 생성기: 1.46 → 0.80 (10만) → 0.38", REV),
         ("DCGAN 생성기: 1.35 → 0.26 (10만) → 0.12", FWD),
         ("", INK),
         ("아래 칸: 생성기 · critic 둘 다 MLP,", INK),
         ("학습률이 상당히 높아 학습 실패 (캡션)", INK2),
         ("60만 번 내내 14.6 ~ 16.0 사이 (중앙 15.2 ~ 15.4)", NO),
         ("critic 이 다르니 위 칸 값과 견주지 않는다", INK2),
         ("— 원문 4.2절이 스스로 적는 조건이다", INK2),
         ("", INK),
         ("「표본 질과 잘 맞는다」 의 근거는", INK),
         ("곡선 셋과 그 위에 얹은 표본 일곱 장씩이다", INK2),
         ("표본 질을 수로 잰 값은 원문에 없다", NO),
         ("실행 횟수(seed)도 적혀 있지 않다", NO)]
b += lines_at(545, 112, rows9, 12, 22)
b += txt(70, 420, "가로축은 생성기 반복이다. 생성기 한 번에 critic 이 5 번(2행을 글자대로 세면 6 번) 배운다", 11, fill=MUTED, anchor="start")
svg("fig09_fig3_readings", W, H, b, "원문 그림 3 읽은 값")
print("  [9] 그림 3 MLP: %s" % READ_F3_MLP)
print("      그림 3 DCGAN: %s" % READ_F3_DCGAN)


# ── 그림 10. 원문 그림 4 · 8 을 읽은 값 — 보통 GAN 의 JS 추정과 생성기 비용 ──────────────────
# 그림 4: 세로 1 픽셀 = 0.0038. 그림 8: 위 왼쪽 0.062, 위 오른쪽 0.031, 아래 0.017. 곡선이 위아래로 크게
# 흔들리는 칸(그림 4 오른쪽 · 그림 8 위 둘)은 중앙값과 함께 그 자리 픽셀의 최소 · 최대를 적는다.
READ_F4_MLP = [(5000, 0.61), (25000, 0.65), (50000, 0.665), (100000, 0.662), (200000, 0.665), (300000, 0.673), (395000, 0.675)]
READ_F4_DCGAN = [(5000, 0.56), (25000, 0.54), (50000, 0.57), (100000, 0.62), (200000, 0.62), (300000, 0.669), (395000, 0.677)]
READ_F4_DCGAN_LOW = [(25000, 0.33), (50000, 0.30), (200000, 0.42)]
READ_F4_MLPMLP = [(5000, 0.50), (25000, 0.13), (50000, 0.15), (100000, 0.18), (200000, 0.23), (270000, 0.24), (300000, 0.38), (395000, 0.47)]
READ_F8_MLP = [(5000, 5.2), (50000, 8.6), (100000, 8.0), (200000, 8.6), (300000, 9.3), (395000, 9.8)]
READ_F8_DCGAN = [(5000, 3.3), (50000, 4.4), (100000, 5.1), (200000, 6.0), (300000, 6.7), (395000, 7.3)]
READ_F8_MLPMLP = [(5000, 2.8), (25000, 1.08), (50000, 1.15), (100000, 1.23), (200000, 1.47), (270000, 1.49), (300000, 2.20), (395000, 2.93)]
W, H = 940, 490
b = defs()
b += txt(20, 30, "원문 그림 4 (왼쪽) · 그림 8 (오른쪽)을 픽셀로 읽은 값 — 보통 GAN 학습 중 JS 추정과 생성기 비용 (중앙값 거르개 뒤)", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 70, 440, 70, 330
fx = lambda v: X0 + v / 400000 * (X1 - X0)
fy = lambda v: Y1 - v / 0.8 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [0, 100000, 200000, 300000, 400000], [0, 0.2, 0.4, 0.6, 0.8], fx, fy, "생성기 반복", "JS 추정 = L/2 + log 2", xfmt="%d")
b += line(fx(0), fy(LN2), fx(400000), fy(LN2), C_JS, 1.2, dash="5 4")
b += txt(fx(400000), fy(LN2) - 6, "log 2 = %.3f" % LN2, 10, fill=C_JS, anchor="end")
b += polyline([(fx(x), fy(v)) for x, v in READ_F4_MLP], REV, 2.2)
b += polyline([(fx(x), fy(v)) for x, v in READ_F4_DCGAN], FWD, 2.2)
for x, v in READ_F4_DCGAN_LOW:
    b += line(fx(x), fy(v), fx(x), fy(dict(READ_F4_DCGAN)[x]), FWD, 1, dash="2 2")
b += polyline([(fx(x), fy(v)) for x, v in READ_F4_MLPMLP], INK2, 2.2)
X0b, X1b = 520, 900
fxb = lambda v: X0b + v / 400000 * (X1b - X0b)
fyb = lambda v: Y1 - v / 10 * (Y1 - Y0)
b += axes(X0b, Y0, X1b, Y1, [0, 100000, 200000, 300000, 400000], [0, 2, 4, 6, 8, 10], fxb, fyb, "생성기 반복", "생성기 비용 −log D", xfmt="%d")
b += polyline([(fxb(x), fyb(v)) for x, v in READ_F8_MLP], REV, 2.2)
b += polyline([(fxb(x), fyb(v)) for x, v in READ_F8_DCGAN], FWD, 2.2)
b += polyline([(fxb(x), fyb(v)) for x, v in READ_F8_MLPMLP], INK2, 2.2)
leg10 = [("MLP 생성기 · DCGAN 판별기", REV, 70), ("DCGAN 생성기 · DCGAN 판별기 (점선 = 아래쪽 흔들림)", FWD, 300), ("MLP 생성기 · MLP 판별기", INK2, 680)]
for lab, col, lx in leg10:
    b += line(lx, 382, lx + 26, 382, col, 2.4)
    b += txt(lx + 32, 386, lab, 11, fill=col, anchor="start")
b += lines_at(30, 414, [("왼쪽 위 두 칸: JS 추정이 0.61 → 0.675 · 0.56 → 0.677 (읽기 ±0.01) 로 오른다. 395,000 번에서 log 2 의 %.1f%% · %.1f%%" % (100 * 0.675 / LN2, 100 * 0.677 / LN2), INK2),
                        ("그런데 원문 캡션은 DCGAN 생성기의 표본이 「좋아진다」 고 적는다 — 평평함이 학습을 막았다는 그림이 아니라, 손실이 진척을 알려 주지 않는다는 그림이다", INK),
                        ("가로축이 그림 3 은 60만, 그림 4 · 8 은 40만이다. 그림 4 의 값은 학습 중인 판별기로 잰 하한이라 참 JS 보다 작거나 같다(4.2절)", MUTED)], 11, 21)
svg("fig10_fig4_fig8_readings", W, H, b, "원문 그림 4 · 8 읽은 값")
print("  [10] 그림 4 MLP 끝 %.3f = log2 의 %.1f%%, DCGAN 끝 %.3f = %.1f%%" % (READ_F4_MLP[-1][1], 100 * READ_F4_MLP[-1][1] / LN2, READ_F4_DCGAN[-1][1], 100 * READ_F4_DCGAN[-1][1] / LN2))


# ── 그림 11. 모드 붕괴를 두고 한 말 넷 — 세기가 다르다 ───────────────────────────────
W, H = 920, 470
b = defs()
b += txt(20, 30, "모드 붕괴를 두고 원문이 적은 문장 넷 — 같은 논문 안에서 세기가 다르다", 15, anchor="start", weight="bold")
claims = [("1절 기여 목록", "「GAN 에 흔한 모드 떨어뜨림 현상도 크게 줄어든다」", "줄어든다 — 정도를 말하지만 잰 값이 없다", CODE),
          ("3절 (알고리즘 1 뒤)", "「critic 을 최적까지 배우면 모드를 무너뜨리는 것이 불가능해진다」", "조건부 논증 — critic 이 최적일 때. 실험은 n_critic = 5", FWD),
          ("4.3절 끝", "「어느 실험에서도 WGAN 의 모드 붕괴 증거를 보지 못했다」", "관찰 — 실험 수를 적지 않는다. 표본 판은 구조마다 64 장씩", OK),
          ("6절 결론", "「모드 붕괴 같은 문제를 없앨 수 있음을 보였다」", "가장 센 말 — 근거는 위 셋이다", NO)]
for i, (where, quote, judge, col) in enumerate(claims):
    y = 62 + 92 * i
    b += box(30, y, 860, 80, fill=NODE, stroke=col, sw=1.6)
    b += txt(46, y + 26, where, 12, anchor="start", fill=col, weight="bold")
    b += txt(220, y + 26, quote, 13, anchor="start", fill=INK)
    b += txt(220, y + 54, judge, 12, anchor="start", fill=INK2)
b += txt(30, 448, "3절 논증의 바탕: 판별기가 고정되면 최적 생성기는 판별기가 가장 높게 매기는 점들 위의 델타의 합이다 — [4] (원 GAN)가 관찰하고 [11] (Unrolled GAN)가 짚었다고 적는다", 11, fill=MUTED, anchor="start")
svg("fig11_mode_collapse_claims", W, H, b, "모드 붕괴 주장 넷")


# ── 그림 12. 5절 MMD 비용 셈 ────────────────────────────────────────────────────
d_gray = 64 * 64
d_rgb = 64 * 64 * 3
gan_lin = 64
gan_sq = 64 * 64
rows12 = [("64x64, 원문이 쓴 차원", d_gray), ("64x64x3, 색 채널까지", d_rgb)]
W, H = 920, 420
b = defs()
b += txt(20, 30, "5절의 MMD 비용 셈 — 「64x64 이미지면 미니배치 4096, 반복당 4096² — 배치 64 인 GAN 반복보다 다섯 자릿수 넘게 많다」", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 260, 860, 70, 300
fx = lambda v: X0 + v / 9 * (X1 - X0)
for t in range(0, 10):
    b += line(fx(t), Y0, fx(t), Y1, LINE, 0.8, dash="2 3")
    b += txt(fx(t), Y1 + 18, "10^%d" % t, 10, fill=MUTED)
bars = [("GAN 반복, 배치 64 (선형)", gan_lin, FWD),
        ("GAN 배치 64 를 제곱으로 셀 때", gan_sq, FWD),
        ("MMD, 배치 4096 (원문)", d_gray ** 2, REV),
        ("MMD, 배치 12288 (색 채널)", d_rgb ** 2, REV)]
for i, (lab, v, col) in enumerate(bars):
    y = 86 + 52 * i
    b += box(X0, y, fx(math.log10(v)) - X0, 30, fill=col, stroke=col, rx=2)
    b += txt(X0 - 10, y + 20, lab, 12, anchor="end", fill=INK)
    b += txt(fx(math.log10(v)) + 8, y + 20, "{:,}".format(v), 11, anchor="start", fill=INK2)
b += txt(X0 + 300, Y1 + 36, "반복 하나의 계산량 (상대 단위, 로그 눈금)", 11, fill=INK2)
r_lin = d_gray ** 2 / gan_lin
r_sq = d_gray ** 2 / gan_sq
b += lines_at(30, 362, [("4096² / 64 = %s 배 = 10^%.2f — 원문의 「다섯 자릿수 넘게」 는 MMD 를 제곱으로, GAN 을 선형으로 센 비교다. 둘 다 제곱으로 세면 4096² / 64² = %s 배 = 10^%.2f" % ("{:,}".format(int(r_lin)), math.log10(r_lin), "{:,}".format(int(r_sq)), math.log10(r_sq)), INK2),
                        ("「차원만큼 표본」 의 차원을 원문은 64 x 64 = 4096 으로 셌다. 색 채널 셋을 넣으면 12,288 이다. 원문은 이 셈이 MMD 에 박할 수 있다고 스스로 적는다(경험 대 이론 표본 복잡도)", INK2)], 11, 21)
svg("fig12_mmd_cost", W, H, b, "MMD 비용 셈")
print("  [12] 4096^2/64 = %d (10^%.2f), 4096^2/64^2 = %d (10^%.2f), 12288^2 = %d" % (r_lin, math.log10(r_lin), r_sq, math.log10(r_sq), d_rgb ** 2))


# ── 그림 13. IPM — 함수 모임을 바꾸면 거리가 바뀐다 (5절) ──────────────────────────────
W, H = 920, 430
b = defs()
b += txt(20, 30, "적분 확률 거리(IPM) d_F = sup_{f∈F} E_r[f] − E_θ[f] — 함수 모임 F 를 고르면 거리가 정해진다 (5절, 식 4)", 15, anchor="start", weight="bold")
ipm = [("1-립시츠 함수 전부", "W (EM)", "약한 위상, 연속인 손실", C_W, "WGAN — 무게 자르기로 K-립시츠 모임을 흉내"),
       ("|f| ≤ 1 인 측정 가능 함수 전부", "δ (TV) — 원문 표기", "센 위상, 예 1 에서 불연속", C_TV, "EBGAN — 판별기가 [0, m] (부록 D)"),
       ("RKHS 공의 함수 (‖f‖ ≤ 1)", "MMD", "핵이 정한다 — 띠폭이 작으면 TV 쪽", C_JS, "GMMN — 망 없이 핵 공식으로 (비용 제곱)")]
for i, (F, dist, prop, col, who) in enumerate(ipm):
    y = 62 + 108 * i
    b += box(30, y, 250, 86, fill=NODE, stroke=col, sw=1.6)
    b += txt(155, y + 38, F, 13, fill=INK, weight="bold")
    b += txt(155, y + 62, "F", 11, fill=MUTED)
    b += line(282, y + 43, 330, y + 43, col, 1.8, marker="ai")
    b += box(332, y, 240, 86, fill=NODE, stroke=col, sw=1.6)
    b += txt(452, y + 34, dist, 14, fill=col, weight="bold")
    b += txt(452, y + 60, prop, 11, fill=INK2)
    b += box(592, y, 300, 86, fill=NODE, stroke=LINE)
    b += txt(742, y + 38, who, 12, fill=INK)
    b += txt(742, y + 62, "생성 모델 쪽 짝", 10, fill=MUTED)
b += txt(30, 400, "−f 도 F 안에 있으면 d_F 는 0 이상 · 대칭 · 삼각 부등식을 만족하는 의사 거리다(원문). 둘째 줄의 값은 sup_A 정의의 δ 가 아니라 그 두 배(Σ|p − q|)다 — 그림 8", 11, fill=MUTED, anchor="start")
svg("fig13_ipm_family", W, H, b, "IPM 함수 모임")


# ── 그림 14. 앞 노트 둘의 물음과 이 편의 답 ──────────────────────────────────────────
W, H = 980, 470
b = defs()
b += txt(20, 30, "앞 노트 둘(CACM 개관판 · NIPS 원판)이 이 편에 넘긴 물음과 답", 15, anchor="start", weight="bold")
qa = [("CACM 9절 · 18절 다섯", ("모델이 멀면 JS 가 log 2 에 붙어 평평", "(m = 5 에서 97.5%)"), "닫힘 — 이론", ("예 1: 받침이 따로면 정확히 log 2, 기울기 0", "정리 1 의 3 항"), OK),
      ("CACM 18절 다섯 (단서)", ("최적 D 가정 위의 계산이라", "실제 학습을 막는지는 모른다"), "일부", ("그림 4: 39.5만 번에 JS 추정이 log 2 의 97.4 ~ 97.7%", "그래도 DCGAN 표본은 좋아졌다 (캡션)"), CODE),
      ("NIPS 24절 첫째", ("다른 거리를 쓰면 멀리 있는", "모델에 어떤 신호가 가나"), "닫힘 — 이론", ("W 는 거리와 상관없이 기울기 크기 1", "(예 1 · 가우스), 정리 3"), OK),
      ("NIPS 24절 첫째 (실제)", ("학습한 critic 이", "그 신호를 주는가"), "일부", ("그림 2 하나 (1 차원, 설정 없음)", "이미지 실험의 기울기 크기는 재지 않음"), CODE),
      ("NIPS 11.1절", ("θ 공간에서 C(G) 의 볼록성이", "깨지고 멀면 평평"), "옆으로 닫힘", ("W 는 θ 에 대해 연속, 측도 0 집합 밖에서 미분", "(정리 1). 볼록성은 말하지 않는다"), CODE),
      ("NIPS 20절 다섯", ("학습 안정성 · 실패율에", "수가 없다"), "안 닫힘", ("이 편도 실행 수 · 실패 비율을 적지 않는다", "구조 셋에 표본 판 하나씩"), NO)]
heads14 = [("앞 노트 자리", 30), ("물음", 200), ("판정", 470), ("이 편의 근거", 590)]
for t, x in heads14:
    b += txt(x, 64, t, 12, anchor="start", weight="bold", fill=INK2)
b += line(30, 72, 960, 72, LINE, 1)
for i, (where, q, verdict, why, col) in enumerate(qa):
    y = 98 + 60 * i
    b += txt(30, y, where, 12, anchor="start", fill=INK)
    b += txt(200, y, q[0], 12, anchor="start", fill=INK)
    b += txt(200, y + 19, q[1], 12, anchor="start", fill=INK)
    b += box(466, y - 16, 100, 24, fill=NODE, stroke=col, sw=1.4)
    b += txt(516, y + 1, verdict, 11, fill=col, weight="bold")
    b += txt(590, y, why[0], 11, anchor="start", fill=INK2)
    b += txt(590, y + 19, why[1], 11, anchor="start", fill=INK2)
svg("fig14_prior_notes_check", W, H, b, "앞 노트 물음과 답")


# ── 그림 15. 계보 ─────────────────────────────────────────────────────────────
W, H = 940, 440
b = defs()
b += txt(20, 30, "계보 — 이 편이 받은 것과 넘긴 것 (오른쪽 칸 이름은 내가 이은 것이고 읽지 않았다)", 15, anchor="start", weight="bold")
left = [("원 GAN (NIPS 2014)", "식 (1) · 최적 D · −log D 꼴", REV),
        ("f-GAN (2016)", "모든 f-발산으로 넓힘", REV),
        ("Arjovsky · Bottou (ICLR 2017)", "포화 · 불안정의 이론 [1]", REV),
        ("최적 수송 (Villani 2009)", "칸토로비치-루빈시테인 쌍대 [22]", FWD),
        ("MMD · GMMN (2012 · 2015)", "다른 IPM 하나", FWD)]
for i, (t1, t2, col) in enumerate(left):
    y = 62 + 66 * i
    b += box(30, y, 270, 54, fill=NODE, stroke=col, sw=1.4)
    b += txt(165, y + 23, t1, 12, fill=INK, weight="bold")
    b += txt(165, y + 42, t2, 11, fill=INK2)
    b += line(302, y + 27, 368, 205, INK2, 1, marker="ai", op=0.7)
b += box(370, 160, 220, 90, fill=OK_SOFT, stroke=OK, sw=2)
b += txt(480, 192, "WGAN (2017)", 15, fill=OK, weight="bold")
b += txt(480, 214, "EM 거리 · critic · 무게 자르기", 11, fill=INK2)
b += txt(480, 232, "arXiv v3 2017-12 · ICML 2017", 10, fill=MUTED)
right = [("WGAN-GP (2017)", "무게 자르기 대신 기울기 벌점"),
         ("스펙트럼 정규화 (2018)", "층마다 스펙트럼 노름으로 나눔"),
         ("GAN 수렴 분석 (2017 ~)", "θ 공간의 국소 안정성"),
         ("생성 모델 평가", "EM 추정을 평가로 쓸 수 있나")]
for i, (t1, t2) in enumerate(right):
    y = 62 + 82 * i
    b += line(592, 205, 648, y + 27, INK2, 1, marker="ai", op=0.7)
    b += box(650, y, 260, 54, fill=NODE, stroke=LINE)
    b += txt(780, y + 23, t1, 12, fill=INK, weight="bold")
    b += txt(780, y + 42, t2, 11, fill=INK2)
b += txt(30, 404, "왼쪽 다섯은 원문 참고 문헌에 있다([4] · [17] · [1] · [22] · [5] · [10]). 오른쪽 넷은 원문 3절이 「립시츠 제약을 더 나은 방법으로」 를 권한 자리와", 11, fill=MUTED, anchor="start")
b += txt(30, 422, "4.2절이 「아직 평가 방법이라 주장하지 않는다」 고 한 자리에서 이었다", 11, fill=MUTED, anchor="start")
svg("fig15_lineage", W, H, b, "계보")

print("끝.")
