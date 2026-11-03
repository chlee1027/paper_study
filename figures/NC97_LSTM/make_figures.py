# -*- coding: utf-8 -*-
"""LSTM 노트(Hochreiter & Schmidhuber, Neural Computation 9(8), 1997)의 그림 열다섯을 만든다.

색과 글꼴은 저장소의 앞선 노트 그림들과 맞췄다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

계산으로 원문을 확인하는 그림이 여럿이다 — 1(오차 배율의 q 제곱), 2(로지스틱 시그모이드에서 |f'(wy) w| 의 최댓값),
8(표 1 ~ 10 의 무게 수를 망 짜임에서 다시 세기), 11(표 3 의 「배우는 시간이 아주 천천히 는다」를 시간 걸음 수와
계산량으로 다시 세기), 12(과제 2c 의 기대 길이), 13(표 4 ~ 6 의 비율을 시험 서열 개수로 되돌리기).
계산한 값은 돌릴 때 화면에도 찍는다. 원문 표의 숫자는 아래 상수에 그대로 옮겨 적었다 — 이 파일은 PDF 를 읽지 않는다.
원문 그림 1 · 2 · 3 · 4 는 crop_paper_figures.py 가 잘라 png 로 둔다.
"""
import io, os, math

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"
NODE      = "#F6F7F5"
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 앞으로 가는 신호, LSTM
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 거꾸로 가는 오차, 견준 방법들
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 게이트
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"
OK_SOFT   = "#D6EEDD"
NO        = "#C0392B"
NO_SOFT   = "#F6D9D5"
PUR       = "#8E44AD"
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


def table(x, y, colw, rows, rowh=24, head_fill=FWD_SOFT, size=11, fills=None):
    """rows[0] 은 머리. fills 는 (행, 열) -> 색."""
    s = ""
    W = sum(colw)
    for r, row in enumerate(rows):
        yy = y + r * rowh
        s += box(x, yy, W, rowh, fill=head_fill if r == 0 else NODE, stroke=LINE, sw=0.8, rx=0)
        xx = x
        for c, cell in enumerate(row):
            if fills and (r, c) in fills:
                s += box(xx + 1, yy + 1, colw[c] - 2, rowh - 2, fill=fills[(r, c)], stroke="none", sw=0, rx=0)
            s += txt(xx + colw[c] / 2, yy + rowh / 2 + 4, str(cell), size, fill=INK if r else INK, weight="bold" if r == 0 else None)
            xx += colw[c]
    return s


print("그림을 만든다 ->", OUT)


def sig(x):
    return 1.0 / (1.0 + math.exp(-x))


def dsig(x):
    s = sig(x)
    return s * (1 - s)


# ── 그림 1. 오차 배율을 q 번 곱하면 — 식 (2) 의 한 경로 ─────────────────────────────
W, H = 900, 430
b = defs()
b += txt(20, 30, "식 (2) 의 한 경로: 걸음마다 |f'(net) w| 를 곱한다. q 걸음 뒤 배율은 그 값의 q 제곱이다 (세로축은 10 의 지수)", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 600, 60, 370
fx = lambda q: X0 + q / 100.0 * (X1 - X0)
fy = lambda e: Y0 + (6 - e) / 36.0 * (Y1 - Y0)   # e = log10, 6 ~ -30
b += axes(X0, Y0, X1, Y1, [0, 20, 40, 60, 80, 100], [6, 0, -6, -12, -18, -24, -30], fx, fy,
          xl="거꾸로 간 걸음 수 q", yl="log10(배율)", yfmt="%d")
cols = [(1.1, NO), (1.0, OK), (0.99, PUR), (0.9, FWD), (0.5, CODE), (0.25, REV)]
print("  그림 1 — q = 10 · 100 에서의 배율")
for f, c in cols:
    pts = []
    for q in range(0, 101):
        e = q * math.log10(f)
        if -30 <= e <= 6:
            pts.append((fx(q), fy(e)))
    b += polyline(pts, c, sw=2.2)
    print("    %.2f  q=10 %.3g  q=100 %.3g" % (f, f ** 10, f ** 100))
lx = 620
rows = [("배율 = |f'w|", INK, "bold")]
for f, c in cols:
    rows.append(("%.2f :  q=100 에서 %.2g" % (f, f ** 100), c))
b += lines_at(lx, 80, rows, 12, 22)
b += lines_at(lx, 250, [
    "0.25 = 로지스틱 시그모이드의 f' 최댓값",
    "(w = 1 이면 이것이 위 끝)",
    "1.0 = 3.2절의 상수 오차 회전목마(CEC):",
    "f 가 항등이고 w = 1.0",
    "0.9 도 100 걸음이면 2.7 x 10^-5 이다",
], 11, 19)
svg("fig01_decay_factor", W, H, b, "오차 배율을 q 번 곱한 값")

# ── 그림 2. 로지스틱 시그모이드에서 |f'(wy) w| 의 최댓값 ─────────────────────────────
best_v, best_x = 0.0, 0.0
for i in range(1, 100000):
    x = i / 10000.0
    v = x * dsig(x)
    if v > best_v:
        best_v, best_x = v, x
print("  그림 2 — max x f'(x) = %.4f  (x = %.4f, coth(x/2) = %.4f)" % (best_v, best_x, 1 / math.tanh(best_x / 2)))
W, H = 900, 430
b = defs()
b += txt(20, 30, "보내는 활성 y 가 고정일 때 |f'(w y) w| 는 w 를 아무리 골라도 0.224 / y 를 넘지 못한다 (내가 계산한 것)", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 590, 60, 370
fx = lambda w: X0 + w / 12.0 * (X1 - X0)
fy = lambda v: Y1 - v / 1.4 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [0, 2, 4, 6, 8, 10, 12], [0, 0.25, 0.5, 0.75, 1.0, 1.25], fx, fy,
          xl="무게 w", yl="|f'(w y) w|")
b += line(X0, fy(1.0), X1, fy(1.0), NO, 1.4, dash="6 4")
b += txt(X0 + 6, fy(1.0) - 6, "1.0 — 넘으면 오차가 커진다", 11, fill=NO, anchor="start")
for y, c in [(1.0, REV), (0.5, CODE), (0.25, FWD), (0.2, OK)]:
    pts = [(fx(w / 50.0), fy(min((w / 50.0) * dsig(w / 50.0 * y), 1.4))) for w in range(0, 601)]
    b += polyline(pts, c, sw=2.2)
    wm = best_x / y
    if wm <= 12:
        b += circ(fx(wm), fy(best_v / y), 4, fill=c, stroke=c)
        b += txt(fx(wm) + 6, fy(best_v / y) - 8, "y=%.2g: 최댓값 %.3f (w=%.2f)" % (y, best_v / y, wm), 10, fill=c, anchor="start")
b += lines_at(610, 80, [
    ("읽는 법", INK, "bold"),
    "원문 3.1절: y 가 0 이 아닌 상수면 |f'w| 는",
    "w = coth(net/2) / y 에서 가장 크고,",
    "|w| 가 4.0 보다 작으면 1.0 보다 작다.",
    "",
    ("내가 더 센 것", INK, "bold"),
    "최댓값을 직접 구하면 0.224 / y 다",
    "(x f'(x) 의 최댓값 0.2239, x = 1.543).",
    "그래서 y = 1 이면 어떤 w 에서도 0.224 이하,",
    "1.0 을 넘으려면 y < 0.224 여야 한다.",
    "그린 넷 가운데 y = 0.2 만 1.12 로 넘는다.",
], 11, 20)
svg("fig02_sigmoid_bound", W, H, b, "시그모이드에서 오차 배율의 최댓값")

# ── 그림 3. 단순한 접근 — 유닛 하나의 상수 오차 흐름 (3.2절) ──────────────────────────
W, H = 900, 360
b = defs()
b += txt(20, 30, "3.2절 — 유닛 j 하나가 자기 자신과만 이어져 있으면 오차는 걸음마다 f'(net) w_jj 배가 된다", 14, anchor="start", weight="bold")
for k, (title, fac, col, sub) in enumerate([
        ("보통 유닛: 시그모이드, w_jj = 1.0", 0.25, REV, "f' 최대 0.25 -> 10 걸음 뒤 9.5 x 10^-7"),
        ("CEC: f 가 항등, w_jj = 1.0", 1.0, OK, "f'(net) w_jj = 1.0 -> 몇 걸음이든 1.0")]):
    y = 80 + k * 135
    b += txt(40, y, title, 13, anchor="start", weight="bold", fill=col)
    for t in range(5):
        cx = 80 + t * 120
        b += circ(cx, y + 45, 20, fill=NODE, stroke=col, sw=1.6)
        b += txt(cx, y + 50, "t-%d" % t if t else "t", 11)
        if t < 4:
            b += line(cx + 22, y + 45, cx + 98, y + 45, col, 1.6, marker="ar" if col == REV else "ao")
        v = fac ** t
        b += txt(cx, y + 85, ("%.3g" % v) if v > 1e-3 else ("%.1e" % v), 11, fill=col)
    b += txt(820, y + 50, sub, 11, fill=INK2, anchor="end")
b += txt(40, 345, "화살표는 오차가 시간을 거꾸로 가는 방향. 원문: 이것을 지키려면 f 가 선형이어야 하고 j 의 활성은 그대로 머문다 — y_j(t+1) = y_j(t).", 11, fill=INK2, anchor="start")
svg("fig03_cec_single_unit", W, H, b, "유닛 하나의 상수 오차 흐름")

# ── 그림 4. 기억 셀 하나 (원문 그림 1 을 다시 그림) ────────────────────────────────
W, H = 900, 420
b = defs()
b += txt(20, 30, "기억 셀 c_j 와 게이트 둘 (원문 그림 1 · 4절의 식). 1997 원판 — 망각 게이트가 없다", 14, anchor="start", weight="bold")
b += box(150, 70, 600, 150, fill=FWD_SOFT, stroke=FWD, sw=1.6)
b += txt(160, 90, "기억 셀 c_j", 12, anchor="start", fill=FWD, weight="bold")
# 입력
for dy in (-25, 0, 25):
    b += line(40, 145 + dy, 185, 145, INK2, 1.2, marker="ai")
b += txt(40, 110, "net_c(t) = Σ w_cu y^u(t-1)", 11, anchor="start", fill=INK2)
b += circ(210, 145, 24, fill=NODE, stroke=INK)
b += txt(210, 150, "g", 14, weight="bold")
b += txt(210, 192, "[-2, 2]", 10, fill=MUTED)
b += line(234, 145, 318, 145, INK2, 1.4, marker="ai")
b += circ(330, 145, 10, fill=CODE, stroke=CODE)
b += txt(330, 125, "x", 12, fill=CODE, weight="bold")
b += line(340, 145, 418, 145, INK2, 1.4, marker="ai")
b += circ(450, 145, 28, fill=OK_SOFT, stroke=OK, sw=1.8)
b += txt(450, 150, "s_c", 14, weight="bold", fill=OK)
b += path("M 438,119 C 420,80 480,80 462,119", stroke=OK, sw=1.8, marker="ao")
b += txt(450, 82, "무게 1.0 고정 (CEC)", 11, fill=OK)
b += line(478, 145, 548, 145, INK2, 1.4, marker="ai")
b += circ(575, 145, 24, fill=NODE, stroke=INK)
b += txt(575, 150, "h", 14, weight="bold")
b += txt(575, 192, "[-1, 1]", 10, fill=MUTED)
b += line(599, 145, 668, 145, INK2, 1.4, marker="ai")
b += circ(680, 145, 10, fill=CODE, stroke=CODE)
b += txt(680, 125, "x", 12, fill=CODE, weight="bold")
for dy in (-25, 0, 25):
    b += line(690, 145, 860, 145 + dy, INK2, 1.2, marker="ai")
b += txt(860, 110, "y^c(t)", 12, anchor="end", fill=INK2)
# 게이트
for gx, name, sub in [(330, "in_j (입력 게이트)", "y^in = f(net_in) ∈ [0, 1]"), (680, "out_j (출력 게이트)", "y^out = f(net_out) ∈ [0, 1]")]:
    b += line(gx, 155, gx, 258, CODE, 1.6)
    b += circ(gx, 280, 22, fill=CODE_SOFT, stroke=CODE, sw=1.6)
    b += txt(gx, 285, "f", 13, weight="bold", fill=CODE)
    b += txt(gx + 32, 274, name, 12, fill=CODE, weight="bold", anchor="start")
    b += txt(gx + 32, 293, sub, 11, fill=INK2, anchor="start")
    for dx in (-18, 0, 18):
        b += line(gx + dx * 1.5, 350, gx + dx * 0.6, 304, INK2, 1, marker="ai")
b += txt(40, 395, "s_c(t) = s_c(t-1) + y^in(t) g(net_c(t)),  s_c(0) = 0", 12, fill=INK2, anchor="start")
b += txt(500, 395, "y^c(t) = y^out(t) h(s_c(t))", 12, fill=INK2, anchor="start")
svg("fig04_memory_cell", W, H, b, "기억 셀과 입력 게이트 출력 게이트")

# ── 그림 5. 1997 원판과 나중의 표준형 ──────────────────────────────────────────
W, H = 900, 470
b = defs()
b += txt(20, 30, "이 논문의 LSTM 과 지금 흔히 쓰는 LSTM 은 같은 식이 아니다 — 오른쪽 칸은 이 논문에 없다", 14, anchor="start", weight="bold")
b += box(20, 55, 420, 395, fill=FWD_SOFT, stroke=FWD)
b += box(460, 55, 420, 395, fill=REV_SOFT, stroke=REV)
b += txt(230, 80, "1997 원판 (이 논문)", 14, weight="bold", fill=FWD)
b += txt(670, 80, "나중 판 (Gers 외 2000 부터)", 14, weight="bold", fill=REV)
left = [
    ("상태", INK, "bold"), "s(t) = s(t-1) + y^in(t) · g(net_c(t))",
    ("출력", INK, "bold"), "y^c(t) = y^out(t) · h(s(t))",
    ("게이트", INK, "bold"), "입력 · 출력 둘. 블록 하나가 게이트를 공유",
    ("g · h", INK, "bold"), "g = 4σ - 2 ∈ [-2, 2],  h = 2σ - 1 ∈ [-1, 1]",
    "(h(x) = tanh(x/2), g(x) = 2 tanh(x/2) 와 같다)",
    ("학습", INK, "bold"), "RTRL 변형, 셀 밖으로 나가는 오차는 자른다",
    ("상태 비우기", INK, "bold"), "서열마다 활성을 0 으로 되돌린다",
    "(5절 서두: 모든 실험. 끝없이 이어지는 입력은 없다)",
]
right = [
    ("상태", INK, "bold"), "c_t = f_t ⊙ c_(t-1) + i_t ⊙ g_t",
    ("출력", INK, "bold"), "h_t = o_t ⊙ tanh(c_t)",
    ("게이트", INK, "bold"), "망각 게이트 f_t 가 더해진다 (Gers 2000)",
    "엿보기 연결 (Gers 2002) 은 고를 수 있다",
    ("g · h", INK, "bold"), "둘 다 tanh, 범위 [-1, 1]",
    ("학습", INK, "bold"), "자르지 않은 BPTT (Graves 외 2005)",
    ("상태 비우기", INK, "bold"), "망각 게이트가 스스로 비운다",
    "f_t = 1 로 두면 원판의 CEC 와 같다",
]
b += lines_at(40, 110, left, 12, 22)
b += lines_at(480, 110, right, 12, 22)
svg("fig05_original_vs_modern", W, H, b, "1997 원판과 나중 판 비교")

# ── 그림 6. 잘린 역전파 — 오차가 셀 안에서만 시간을 거슬러 간다 ──────────────────────────
W, H = 900, 400
b = defs()
b += txt(20, 30, "잘린 역전파 (4절, 부록 A.1 · A.2): 셀 안 CEC 에서만 오차가 시간을 거슬러 가고, 셀 밖으로 나가려 하면 0 으로 둔다", 14, anchor="start", weight="bold")
ts = ["t", "t-1", "t-2", "...", "t-q"]
for k, lab in enumerate(ts):
    cx = 720 - k * 150
    b += circ(cx, 170, 26, fill=OK_SOFT, stroke=OK, sw=1.6)
    b += txt(cx, 175, "s(" + lab + ")" if lab != "..." else "...", 11, fill=OK, weight="bold")
    if k < 4:
        b += line(cx - 28, 170, cx - 122, 170, OK, 2, marker="ao")
        b += txt(cx - 75, 160, "x 1.0", 11, fill=OK)
b += line(840, 90, 748, 152, REV, 2, marker="ar")
b += txt(845, 82, "오차가 y^c(t) 에 닿는다", 11, fill=REV, anchor="end")
b += txt(845, 120, "x y^out(t) h'(s(t))", 11, fill=REV, anchor="end")
b += line(120, 196, 70, 290, REV, 2, marker="ar")
b += txt(60, 310, "셀에 들어올 때 한 번 더: x g'(net_c) y^in  또는  x g(net_c) f'_in(net_in)", 11, fill=REV, anchor="start")
b += txt(60, 330, "여기서 들어오는 무게(w_cu, w_in,u)를 고치는 데만 쓰고, 그 앞 유닛으로는 넘기지 않는다", 11, fill=INK2, anchor="start")
for k in range(3):
    cx = 720 - k * 150
    b += line(cx, 200, cx, 250, NO, 1.4, dash="4 3")
    b += txt(cx, 268, "x 0 (자름)", 10, fill=NO)
b += lines_at(60, 360, [
    "원문 식 (41): 배율은 셀에 들어올 때(t)와 나갈 때(t-q) 두 번만 곱해지고 그 사이 q 걸음에서는 1.0 이다. 무게 하나당 걸음마다 O(1) 셈이다.",
], 11, 18)
svg("fig06_truncation", W, H, b, "잘린 역전파의 오차 경로")

# ── 그림 7. 입력 무게 충돌 · 출력 무게 충돌 (3.2절) ─────────────────────────────────
W, H = 900, 380
b = defs()
b += txt(20, 30, "3.2절 — 같은 무게 하나가 서로 다른 때에 반대 일을 해야 한다. 게이트는 이것을 「때」에 따라 가르려는 장치다", 14, anchor="start", weight="bold")
for k, (title, wname, jobs, gate) in enumerate([
        ("입력 무게 충돌", "w_ji (i -> j)", [("t1: 이 입력을 저장하라 (j 를 켠다)", OK), ("t2 ~ t9: 무관한 입력은 무시하라 (j 를 지킨다)", NO)], "입력 게이트 in_j: 쓰기를 연다 / 닫는다"),
        ("출력 무게 충돌", "w_kj (j -> k)", [("t10: j 의 내용을 꺼내라", OK), ("t1 ~ t9: k 를 흔들지 마라", NO)], "출력 게이트 out_j: 읽기를 연다 / 닫는다")]):
    x = 30 + k * 440
    b += box(x, 55, 420, 300, fill=NODE, stroke=LINE)
    b += txt(x + 210, 80, title, 14, weight="bold")
    b += txt(x + 210, 110, "같은 무게 " + wname, 12, fill=INK2)
    for r, (jt, c) in enumerate(jobs):
        b += box(x + 20, 130 + r * 55, 380, 40, fill=OK_SOFT if c == OK else NO_SOFT, stroke=c)
        b += txt(x + 210, 155 + r * 55, jt, 12, fill=c)
    b += txt(x + 210, 260, "두 일이 같은 무게에 반대 방향의 갱신을 보낸다", 11, fill=INK2)
    b += box(x + 20, 280, 380, 50, fill=CODE_SOFT, stroke=CODE)
    b += txt(x + 210, 310, gate, 12, fill=CODE, weight="bold")
svg("fig07_weight_conflicts", W, H, b, "입력 무게 충돌과 출력 무게 충돌")

# ── 그림 8. 무게 수 다시 세기 ───────────────────────────────────────────────────
def count(I, K, cells, gates, hid_bias, out_bias, out_from_input=False):
    hidden = cells + gates
    w = hidden * (I + hidden)            # 입력 -> 숨은 층, 숨은 층 안 완전 연결
    w += K * cells                       # 출력은 기억 셀에서만
    if out_from_input:
        w += K * I
    w += hid_bias + (K if out_bias else 0)
    return w


recount = [
    ("1 (표 1)", "입력 7 · 출력 7 · 블록 4 x 크기 1", count(7, 7, 4, 8, 8, False), 264, "게이트만 치우침"),
    ("1 (표 1)", "입력 7 · 출력 7 · 블록 3 x 크기 2", count(7, 7, 6, 6, 6, False), 276, "게이트만 치우침"),
    ("2c (표 3)", "입력 p+4 · 출력 2 · 블록 2 x 1, p = 50", count(54, 2, 2, 4, 0, False), 364, "치우침 없음"),
    ("2c (표 3)", "같은 짜임, p = 1000", count(1004, 2, 2, 4, 0, False), 6064, "6p + 64"),
    ("3a (표 4)", "입력 1 · 출력 1 · 블록 3 x 1", count(1, 1, 3, 6, 9, False), 102, "숨은 유닛만 치우침"),
    ("4 · 5 (표 7 · 8)", "입력 2 · 출력 1 · 블록 2 x 2", count(2, 1, 4, 4, 8, True), 93, "모든 비입력 유닛"),
    ("6a (표 9)", "입력 8 · 출력 4 · 블록 2 x 2", count(8, 4, 4, 4, 8, True), 156, "모든 비입력 유닛"),
    ("6b (표 9)", "입력 8 · 출력 8 · 블록 3 x 2", count(8, 8, 6, 6, 12, True), 308, "모든 비입력 유닛"),
]
# RTRL (표 2): 입력 p+1, 숨은 1 (자기 연결), 출력 p+1 은 입력 · 숨은 유닛에서
for p in (4, 10, 100):
    I = p + 1
    recount.append(("2a RTRL (표 2)", "p = %d: 입력 %d · 숨은 1 · 출력 %d" % (p, I, I), I + 1 + I * (I + 1), {4: 36, 10: 144, 100: 10404}[p], "치우침 없음"))
# LSTM 2a: 셀 · 입력 게이트가 입력에서만, 출력이 입력과 셀에서
recount.append(("2a LSTM (표 2)", "p = 100: 셀 · 게이트는 입력만 받는다고 가정", 101 * 102 + 101 + 101, 10504, "가정 하나"))
print("  그림 8 — 무게 수 다시 세기")
for r in recount:
    print("    %-16s %-40s 내가 센 것 %6d  원문 %6d  %s" % (r[0], r[1], r[2], r[3], "같다" if r[2] == r[3] else "다르다"))
W, H = 900, 60 + 26 * (len(recount) + 1) + 70
b = defs()
b += txt(20, 30, "원문 표의 「# weights」 를 4절 · 5절의 망 짜임에서 다시 셌다 (내가 센 것). 열두 칸이 모두 같다", 14, anchor="start", weight="bold")
rows = [["실험", "짜임", "내가 센 것", "원문", "치우침 무게"]]
fills = {}
for i, r in enumerate(recount):
    rows.append([r[0], r[1], "{:,}".format(r[2]), "{:,}".format(r[3]), r[4]])
    fills[(i + 1, 2)] = OK_SOFT if r[2] == r[3] else NO_SOFT
    if r[4] == "가정 하나":
        fills[(i + 1, 4)] = CODE_SOFT
b += table(20, 50, [140, 330, 110, 100, 180], rows, 26, fills=fills)
b += lines_at(20, 60 + 26 * (len(recount) + 1) + 20, [
    "세는 규칙: 숨은 층(셀 + 게이트) 의 각 유닛이 입력 전부와 숨은 층 전부를 받고, 출력은 셀에서만 받는다(원문 표 10 의 「F」).",
    "실험 4 · 5 · 6 은 출력도 치우침을 갖는다(표 10 의 「all」). 2a LSTM 의 10,504 는 셀과 입력 게이트가 입력 101 개만 받을 때 맞는다 — 원문은 이 짜임을 적지 않았다.",
], 11, 18)
svg("fig08_weight_recount", W, H, b, "무게 수 다시 세기")

# ── 그림 9. 표 1 — 내장 Reber 문법 ─────────────────────────────────────────────
T1 = [  # (방법, 숨은 유닛, 무게, 학습률, 성공 %, 성공까지 서열 수, 출처)
    ("RTRL", "3", "≈170", "0.05", "일부", 173000, "다른 논문"),
    ("RTRL", "12", "≈494", "0.1", "일부", 25000, "다른 논문"),
    ("ELM", "15", "≈435", "", "0", 200000, "다른 논문"),
    ("RCC", "7-9", "≈119-198", "", "50", 182000, "다른 논문"),
    ("LSTM", "4 블록 x 1", "264", "0.1", "100", 39740, "이 논문"),
    ("LSTM", "3 블록 x 2", "276", "0.1", "100", 21730, "이 논문"),
    ("LSTM", "3 블록 x 2", "276", "0.2", "97", 14060, "이 논문"),
    ("LSTM", "4 블록 x 1", "264", "0.5", "97", 9500, "이 논문"),
    ("LSTM", "3 블록 x 2", "276", "0.5", "100", 8440, "이 논문"),
]
W, H = 900, 440
b = defs()
b += txt(20, 30, "표 1 — 내장 Reber 문법: 성공까지 본 서열 수 (가로축 로그). 위 넷은 다른 논문에서 옮긴 값이다", 14, anchor="start", weight="bold")
X0, X1, Y0 = 300, 780, 60
fx = lambda n: X0 + (math.log10(n) - 3.5) / 2.0 * (X1 - X0)
for t in (10 ** 3.5, 1e4, 10 ** 4.5, 1e5, 10 ** 5.5):
    b += line(fx(t), Y0, fx(t), Y0 + 9 * 34, LINE, 0.8, dash="2 3")
    b += txt(fx(t), Y0 + 9 * 34 + 16, "{:,}".format(int(round(t, -2))), 10, fill=MUTED)
for i, (m, h, w, lr, pc, n, src) in enumerate(T1):
    y = Y0 + i * 34
    col = FWD if m == "LSTM" else REV
    b += txt(20, y + 20, "%s  %s  (w %s%s)" % (m, h, w, (", lr " + lr) if lr else ""), 11, anchor="start", fill=col)
    b += box(X0, y + 6, fx(n) - X0, 20, fill=FWD_SOFT if m == "LSTM" else REV_SOFT, stroke=col, rx=2)
    lab = ("> " if m == "ELM" else "") + "{:,}".format(n) + "  ·  성공 " + pc + ("%" if pc not in ("일부",) else "")
    b += txt(fx(n) + 6, y + 21, lab, 10, fill=INK2, anchor="start")
b += txt(20, 400, "LSTM 다섯 줄 = 각 30 번(학습 · 시험 짝 셋 x 초기값 10). 97% 는 30 번 중 29 번(96.7%)이고, 두 줄이 하나씩 실패해 캡션의 「150 번 중 실패 둘」 과 맞는다(내가 센 것).", 11, fill=INK2, anchor="start")
b += txt(20, 420, "ELM 은 「> 200,000」 이라 막대 끝이 하한이다. 맨 아래 줄의 30 번 범위는 3,800 ~ 24,100 (캡션). 다른 줄은 흩어짐이 없다.", 11, fill=INK2, anchor="start")
svg("fig09_table1_reber", W, H, b, "표 1 내장 Reber 문법 결과")

# ── 그림 10. 표 2 — 과제 2a ───────────────────────────────────────────────────
T2 = [("RTRL", 4, "1.0", 36, 78, "1,043,000"), ("RTRL", 4, "4.0", 36, 56, "892,000"), ("RTRL", 4, "10.0", 36, 22, "254,000"),
      ("RTRL", 10, "1.0-10.0", 144, 0, "> 5,000,000"), ("RTRL", 100, "1.0-10.0", 10404, 0, "> 5,000,000"),
      ("BPTT", 100, "1.0-10.0", 10404, 0, "> 5,000,000"), ("CH", 100, "1.0", 10506, 33, "32,400"), ("LSTM", 100, "1.0", 10504, 100, "5,040")]
W, H = 900, 420
b = defs()
b += txt(20, 30, "표 2 — 과제 2a (잡음 없는 서열, 지연 p): 성공한 실행의 비율. 각 줄 18 번의 평균", 14, anchor="start", weight="bold")
X0, X1 = 330, 640
fx = lambda v: X0 + v / 100.0 * (X1 - X0)
for t in (0, 25, 50, 75, 100):
    b += line(fx(t), 55, fx(t), 55 + 8 * 34, LINE, 0.8, dash="2 3")
    b += txt(fx(t), 55 + 8 * 34 + 16, "%d%%" % t, 10, fill=MUTED)
for i, (m, p, lr, w, pc, n) in enumerate(T2):
    y = 55 + i * 34
    col = FWD if m == "LSTM" else REV
    b += txt(20, y + 20, "%s  p=%d  lr %s  (w %s)" % (m, p, lr, "{:,}".format(w)), 11, anchor="start", fill=col)
    if pc:
        b += box(X0, y + 6, fx(pc) - X0, 20, fill=FWD_SOFT if m == "LSTM" else REV_SOFT, stroke=col, rx=2)
    k = round(pc * 18 / 100.0)
    b += txt(max(fx(pc), X0) + 6, y + 21, "%d%%  (18 번 중 %d 번)" % (pc, k), 10, fill=INK2, anchor="start")
    b += txt(880, y + 21, "성공까지 " + n, 10, fill=INK2, anchor="end")
b += txt(20, 365, "18 번 중 정수 번으로 되돌리면 14 · 10 · 4 · 6 번이 원문의 78 · 56 · 22 · 33% 와 맞는다(내가 센 것).", 11, fill=INK2, anchor="start")
b += txt(20, 385, "본문의 「p = 4 에서 전체 실행의 7/9 가 성공」 은 학습률 1.0 줄(14/18) 하나와만 맞는다. 세 학습률을 합치면 28/54 = 51.9% 다.", 11, fill=INK2, anchor="start")
b += txt(20, 405, "「성공까지」 는 성공한 실행만의 평균으로 읽힌다(캡션: 실패한 실행을 빼고 보아도). 그러면 RTRL 14 번과 LSTM 18 번은 다른 모집단이다.", 11, fill=INK2, anchor="start")
svg("fig10_table2_task2a", W, H, b, "표 2 과제 2a 결과")

# ── 그림 11. 표 3 — 「배우는 시간이 아주 천천히 는다」 를 다시 세기 ──────────────────────
T3 = [(50, 50, 30000, 364), (100, 100, 31000, 664), (200, 200, 33000, 1264), (500, 500, 38000, 3064), (1000, 1000, 49000, 6064),
      (1000, 500, 49000, 3064), (1000, 200, 75000, 1264), (1000, 100, 135000, 664), (1000, 50, 203000, 364)]
print("  그림 11 — 표 3 위 칸, q = 50 대비 배수 (서열 수 · 시간 걸음 수 · 걸음 x 무게)")
base = None
up = []
for q, p, n, w in T3[:5]:
    steps = n * (q + 13)
    ops = steps * w
    if base is None:
        base = (n, steps, ops)
    r = (n / base[0], steps / base[1], ops / base[2])
    up.append((q, r))
    print("    q=%4d  서열 %.2f  걸음 %.1f  걸음x무게 %.0f" % (q, r[0], r[1], r[2]))
W, H = 900, 450
b = defs()
b += txt(20, 30, "표 3 위 칸 — 지연 q 를 20 배로 늘렸을 때, 무엇으로 세느냐에 따라 「배우는 시간」 이 1.6 배도 되고 438 배도 된다", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 560, 60, 360
fx = lambda q: X0 + (math.log10(q) - math.log10(50)) / (math.log10(1000) - math.log10(50)) * (X1 - X0)
fy = lambda r: Y1 - math.log10(r) / 3.0 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [50, 100, 200, 500, 1000], [1, 10, 100, 1000], fx, fy,
          xl="q (= 지연 - 1), p = q", yl="q = 50 대비 배수 (로그)", yfmt=lambda t: "%dx" % t)
for k, (lab, c) in enumerate([("성공까지 본 서열 수 (원문 표의 값)", FWD), ("처리한 시간 걸음 수 (서열 수 x 기대 길이 q+13)", CODE), ("걸음 x 무게 수 (걸음마다 셈이 O(W))", REV)]):
    pts = [(fx(q), fy(r[k])) for q, r in up]
    b += polyline(pts, c, sw=2.2)
    for x, y in pts:
        b += circ(x, y, 3.5, fill=c, stroke=c)
    b += txt(pts[-1][0] + 8, pts[-1][1] + 4, "%.1fx" % up[-1][1][k] if k < 2 else "%.0fx" % up[-1][1][k], 11, fill=c, anchor="start", weight="bold")
    b += txt(600, 90 + k * 24, lab, 11, fill=c, anchor="start")
b += lines_at(600, 180, [
    ("아래 칸 (q = 1000 고정, p 를 줄임)", INK, "bold"),
    "q/p = 1 · 2 · 5 · 10 · 20 에서",
    "서열 수 49,000 · 49,000 · 75,000 ·",
    "135,000 · 203,000",
    "방해 기호가 자주 나올수록 느려진다",
    "(원문: 자주 보는 입력이 무게를 흔든다).",
    "",
    "원문 주장은 서열 수로 센 것이다.",
    "벽시계 시간은 원문에 없다.",
], 11, 20)
svg("fig11_table3_scaling", W, H, b, "표 3 지연과 학습 시간")

# ── 그림 12. 과제 2c 서열의 기대 길이 ───────────────────────────────────────────
Ek = sum(0.1 * 0.9 ** k * k for k in range(20000))
print("  그림 12 — E[k] = %.6f, 기대 길이 = q + 4 + E[k] = q + %.4f" % (Ek, 4 + Ek))
W, H = 900, 400
b = defs()
b += txt(20, 30, "과제 2c — 덧붙는 방해 기호 수 k 는 기하분포다. 원문 식을 그대로 계산하면 기대 길이는 q+14 가 아니라 q+13 이다", 14, anchor="start", weight="bold")
X0, X1, Y0, Y1 = 80, 560, 60, 330
fx = lambda k: X0 + (k + 0.5) / 41.0 * (X1 - X0)
fy = lambda v: Y1 - v / 0.11 * (Y1 - Y0)
b += axes(X0, Y0, X1, Y1, [0, 10, 20, 30, 40], [0, 0.025, 0.05, 0.075, 0.1], fx, fy, xl="k", yl="P(k) = 0.1 x 0.9^k")
bw = (X1 - X0) / 41.0 * 0.8
for k in range(41):
    v = 0.1 * 0.9 ** k
    b += box(fx(k) - bw / 2, fy(v), bw, Y1 - fy(v), fill=FWD_SOFT, stroke=FWD, sw=0.6, rx=0)
b += line(fx(9), Y0, fx(9), Y1, NO, 1.6, dash="5 3")
b += txt(fx(9) + 6, Y0 + 14, "E[k] = 0.9 / 0.1 = 9", 11, fill=NO, anchor="start")
b += lines_at(590, 80, [
    ("원문의 식", INK, "bold"),
    "4 + Σ_k (1/10)(9/10)^k (q + k) = q + 14",
    "",
    ("내가 계산한 것", INK, "bold"),
    "Σ_k (1/10)(9/10)^k = 1",
    "Σ_k k (1/10)(9/10)^k = 9",
    "-> 4 + q + 9 = q + 13",
    "",
    "서열 = b, x 또는 y, 방해 기호 q + k 개,",
    "e, 끝 기호 -> 길이 q + k + 4.",
    "같은 이유로 방해 기호 하나의 기대",
    "출현 수도 (q+10)/p 가 아니라 (q+9)/p.",
    "q = 1000 이면 차이는 0.1% 다.",
], 11, 20)
svg("fig12_task2c_length", W, H, b, "과제 2c 기대 길이")

# ── 그림 13. 표 4 ~ 6 의 비율을 개수로 되돌리기 ──────────────────────────────────
T456 = [("표 4 (3a)", "T=100, N=3", 0.000195), ("표 4 (3a)", "T=100, N=1", 0.000117), ("표 4 (3a)", "T=1000, N=3", 0.000078),
        ("표 5 (3b)", "T=100, N=3", 0.00828), ("표 5 (3b)", "T=100, N=1", 0.01500), ("표 5 (3b)", "T=1000, N=1", 0.01207),
        ("표 6 (3c)", "T=100, N=3", 0.00558), ("표 6 (3c)", "T=100, N=1", 0.00441)]
print("  그림 13 — 비율 x 2,560 x 10 번")
rows = [["표", "설정", "원문 비율", "x 25,600 (2,560 개 x 10 번)", "정수로 되돌리면"]]
fills = {}
for i, (t, s, f) in enumerate(T456):
    v = f * 25600
    k = round(v)
    rows.append([t, s, ("%.6f" % f).rstrip("0"), "%.2f" % v, "%d 개 -> %.6f" % (k, k / 25600.0)])
    nd = len(("%f" % f).rstrip("0").split(".")[1])     # 원문이 적은 소수 자리 수
    fills[(i + 1, 3)] = OK_SOFT if abs(round(k / 25600.0, nd) - f) < 1e-12 else CODE_SOFT
    print("    %s %s  %.3f" % (t, s, v))
W, H = 900, 60 + 26 * 9 + 80
b = defs()
b += txt(20, 30, "표 4 ~ 6 의 「잘못 분류한 비율」 은 시험 서열 2,560 개를 10 번 돌린 평균이다. 개수로 되돌려 본 것 (내가 센 것)", 14, anchor="start", weight="bold")
b += table(20, 50, [110, 130, 110, 250, 260], rows, 26, fills=fills)
b += lines_at(20, 60 + 26 * 9 + 20, [
    "표 4 는 10 번을 다 합쳐 25,600 개 중 5 · 3 · 2 개를 틀렸다는 뜻이다. 표 5 · 6 은 112 ~ 384 개.",
    "노란 칸 하나(표 6 첫 줄)는 142.85 라 정수가 아니다. 143 개면 0.005586 이고, 원문은 끝자리를 버린 것으로 읽힌다.",
    "표 7 · 8 은 개수로 적었다: 실험 4 는 2,560 개 중 1 · 0 · 1 개, 실험 5 는 139 · 14 개 (10 번 평균).",
], 11, 18)
svg("fig13_fraction_counts", W, H, b, "표 4 ~ 6 비율을 개수로")

# ── 그림 14. 실험마다 근거의 모양 ───────────────────────────────────────────────
EV = [  # 실험, 반복 수, 흩어짐 적힘, 견준 방법을 저자가 돌림, 다른 논문 값, 견준 방법 없음
    ("1 Reber (표 1)", "30 x 5 줄", "맨 아래 줄만 범위", "아니다", "RTRL · ELM · RCC", ""),
    ("2a (표 2)", "18", "없다", "RTRL · BPTT · CH", "", ""),
    ("2b (본문)", "18", "없다", "CH (실패만 적음)", "", ""),
    ("2c (표 3)", "20", "없다", "아니다", "", "LSTM 만"),
    ("3a · 3b · 3c (표 4 ~ 6)", "10", "없다", "아니다", "추측 비교는 다른 보고서", "LSTM 만"),
    ("4 덧셈 (표 7)", "10", "T=1000 만 범위", "아니다", "", "LSTM 만"),
    ("5 곱셈 (표 8)", "10", "없다", "아니다", "", "LSTM 만"),
    ("6a · 6b (표 9)", "20 · 10", "없다", "아니다", "", "LSTM 만"),
]
W, H = 900, 60 + 30 * 9 + 70
b = defs()
b += txt(20, 30, "실험마다 근거의 모양 — 견준 방법을 저자가 같은 조건에서 돌린 것은 실험 2a · 2b 뿐이다", 14, anchor="start", weight="bold")
rows = [["실험", "반복 수", "흩어짐", "저자가 돌린 비교", "다른 논문에서 옮김", "비교 없음"]] + [list(r) for r in EV]
fills = {}
for i, r in enumerate(EV):
    fills[(i + 1, 3)] = OK_SOFT if r[3] != "아니다" else NODE
    fills[(i + 1, 2)] = NO_SOFT if r[2] == "없다" else CODE_SOFT
    if r[5]:
        fills[(i + 1, 5)] = NO_SOFT
b += table(20, 50, [180, 90, 140, 160, 180, 110], rows, 30, size=11, fills=fills)
b += lines_at(20, 60 + 30 * 9 + 20, [
    "「다른 순환망 알고리즘으로 풀린 적 없다」(실험 2c ~ 6) 는 저자가 아는 문헌에 대한 말이고, 같은 과제에서 RTRL · BPTT 를 돌린 값은 없다.",
    "근거로 든 것은 2a 에서 RTRL · BPTT 가 지연 10 에서도 실패했다는 것 하나다.",
], 11, 18)
svg("fig14_evidence_map", W, H, b, "실험마다 근거의 모양")

# ── 그림 15. 계보 ─────────────────────────────────────────────────────────────
W, H = 900, 400
b = defs()
b += txt(20, 30, "계보 — 왼쪽 칸은 이 논문이 인용한 것, 오른쪽 칸은 이 논문 뒤에 나온 것이다 (오른쪽 칸은 이 노트에서 읽지 않았다)", 14, anchor="start", weight="bold")
nodes = [
    (110, 90, "Elman 1988 / 1990", "단순 순환망, 문맥 유닛", REV_SOFT, REV),
    (110, 170, "Hochreiter 1991 (학위논문)", "오차가 지수로 사라진다", REV_SOFT, REV),
    (110, 250, "Bengio 외 1994", "기울기로 긴 의존을 배우기 어렵다", REV_SOFT, REV),
    (110, 330, "Mozer 1992 · Schmidhuber 1992", "시간 상수 · 서열 덩이 짓기", REV_SOFT, REV),
    (450, 210, "LSTM 1997 (이 논문)", "CEC + 입력 · 출력 게이트, 잘린 기울기", FWD_SOFT, FWD),
    (780, 80, "Gers 외 2000", "망각 게이트", NODE, INK2),
    (780, 150, "Gers 외 2002", "엿보기 연결", NODE, INK2),
    (780, 220, "Graves 외 2005", "자르지 않은 BPTT", NODE, INK2),
    (780, 290, "Cho 외 2014 (GRU)", "게이트 둘로 줄인 셀", OK_SOFT, OK),
    (780, 360, "Sutskever 외 2014", "LSTM 부호기-복호기", OK_SOFT, OK),
]
for x, y, t, s, f, c in nodes:
    b += box(x - 105, y - 28, 210, 56, fill=f, stroke=c)
    b += txt(x, y - 6, t, 12, weight="bold", fill=c)
    b += txt(x, y + 14, s, 10, fill=INK2)
for y in (90, 170, 250, 330):
    b += line(215, y, 345, 210, INK2, 1.2, marker="ai")
for y in (80, 150, 220, 290, 360):
    b += line(555, 210, 675, y, INK2, 1.2, marker="ai")
svg("fig15_lineage", W, H, b, "LSTM 계보")

print("끝.")
