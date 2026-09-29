# -*- coding: utf-8 -*-
"""VGG 노트(Simonyan & Zisserman, ICLR 2015)의 그림 열여섯을 만든다.

색과 글꼴은 앞선 노트들(퍼셉트론부터 GAN 까지)의 그림과 맞췄다 — 저장소의 노트들이 한 벌로 읽히게
하려는 것이다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

망 A~E 의 파라미터 수(논문 표 2 와 맞춰 본다), 쌓은 3x3 의 수용장과 파라미터 비, 망 D 의 층별 곱셈-덧셈
수와 활성 메모리, 층별 수용장, 조밀 평가의 점수 지도 크기, 표 3~7 · 11 의 차이는 이 파일이 직접 계산한다.
표의 숫자는 논문에서 옮긴 것이고 이 파일 안에 상수로 적었다. 계산한 값은 돌릴 때 화면에도 찍는다.
"""
import io, os, math, random

OUT = os.path.dirname(os.path.abspath(__file__))
random.seed(0)

BG        = "#ECEFEC"   # 그림 상자 배경
NODE      = "#F6F7F5"   # 노드 안쪽
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 합성곱, 논문이 고정한 것
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 완전연결, 더한 층
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 풀링, 수용장
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"   # 초록 — 좋아진다
NO        = "#C0392B"   # 빨강 — 나빠진다
# 막대 · 점 그림 계열 색 — 오차 top-1 · top-5, 방법 비교. 이 순서로 고정한다.
S_TOP1    = "#2A78D6"
S_TOP5    = "#EB6834"
S_THIRD   = "#1BAF7A"
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


# ── 망 정의 (논문 표 1) ──────────────────────────────────────────────────────
# 단계마다 (커널, 채널) 목록. 단계 뒤에 최댓값 풀링이 하나씩 온다.
CFG = {
    "A": [[(3, 64)], [(3, 128)], [(3, 256)] * 2, [(3, 512)] * 2, [(3, 512)] * 2],
    "B": [[(3, 64)] * 2, [(3, 128)] * 2, [(3, 256)] * 2, [(3, 512)] * 2, [(3, 512)] * 2],
    "C": [[(3, 64)] * 2, [(3, 128)] * 2, [(3, 256)] * 2 + [(1, 256)], [(3, 512)] * 2 + [(1, 512)], [(3, 512)] * 2 + [(1, 512)]],
    "D": [[(3, 64)] * 2, [(3, 128)] * 2, [(3, 256)] * 3, [(3, 512)] * 3, [(3, 512)] * 3],
    "E": [[(3, 64)] * 2, [(3, 128)] * 2, [(3, 256)] * 4, [(3, 512)] * 4, [(3, 512)] * 4],
}
PAPER_M = {"A": 133, "B": 133, "C": 134, "D": 138, "E": 144}
FC = [(7 * 7 * 512, 4096), (4096, 4096), (4096, 1000)]


def count(name):
    """가중치 + 치우침. 합성곱 부분과 완전연결 부분을 따로 센다. 곱셈-덧셈 수는 224x224 입력 기준."""
    cin, side = 3, 224
    conv_p = conv_mac = 0
    layers = []
    for stage in CFG[name]:
        for k, c in stage:
            p = k * k * cin * c + c
            mac = side * side * k * k * cin * c
            conv_p += p; conv_mac += mac
            layers.append(("conv%d-%d" % (k, c), side, c, p, mac))
            cin = c
        side //= 2
    fc_p = sum(a * c + c for a, c in FC)
    fc_mac = sum(a * c for a, c in FC)
    return conv_p, fc_p, conv_mac, fc_mac, layers


print("  [표 2] 파라미터 수 (가중치 + 치우침):")
PC = {}
for n in "ABCDE":
    cp, fp, cm, fm, L = count(n)
    PC[n] = (cp, fp, cm, fm, L)
    nw = sum(len(s) for s in CFG[n]) + 3
    print("      %s  가중 층 %2d  합성곱 %s + 완전연결 %s = %s  (논문 %dM, 완전연결 몫 %.1f%%)  곱셈-덧셈 %.2f G"
          % (n, nw, fmt(cp), fmt(fp), fmt(cp + fp), PAPER_M[n], 100.0 * fp / (cp + fp), (cm + fm) / 1e9))


# ── 그림 1. 앞 노트가 남긴 빈칸 — AlexNet 의 선택들 대 규칙 하나 ─────────────────
W, H = 820, 380
b = defs()
b += txt(20, 30, "AlexNet(2012) 은 층마다 다른 선택을 했다. VGG 는 규칙 하나로 고정하고 깊이만 바꾼다", 15, anchor="start", weight="bold")
b += box(20, 50, 380, 300, fill="none", stroke=LINE)
b += txt(210, 74, "AlexNet: 층마다 다르다", 13, weight="bold", fill=REV)
alex = [("합성곱 1", "11x11, 보폭 4, 96"), ("합성곱 2", "5x5, 256"), ("합성곱 3~5", "3x3, 384 · 384 · 256"),
        ("정규화", "LRN (상수 넷)"), ("풀링", "3x3, 보폭 2 (겹침)"), ("깊이", "학습되는 층 8")]
for j, (a, c) in enumerate(alex):
    b += txt(60, 110 + 36 * j, a, 12, anchor="start", weight="bold")
    b += txt(170, 110 + 36 * j, c, 12, anchor="start", fill=INK2)
b += box(420, 50, 380, 300, fill="none", stroke=LINE)
b += txt(610, 74, "VGG: 한 규칙, 깊이만 바꾼다", 13, weight="bold", fill=FWD)
vgg = [("합성곱", "모두 3x3, 보폭 1, 여백 1"), ("채널", "64 에서 풀링마다 2 배, 512 까지"), ("풀링", "2x2, 보폭 2 (겹치지 않음), 다섯 번"),
       ("정규화", "없다 (A-LRN 하나만 시험)"), ("완전연결", "4096 · 4096 · 1000, 모든 망 같다"), ("깊이", "11 · 13 · 16 · 16 · 19")]
for j, (a, c) in enumerate(vgg):
    b += txt(450, 110 + 36 * j, a, 12, anchor="start", weight="bold")
    b += txt(540, 110 + 36 * j, c, 12, anchor="start", fill=INK2)
b += txt(410, 372, "AlexNet 노트가 남긴 물음: 「층을 빼면 top-1 이 약 2% 나빠진다」가 숫자 한 개였다. 이 논문은 깊이를 다섯 단계로 체계적으로 바꾼다", 11, fill=MUTED)
svg("fig01_gap", W, H, b, "AlexNet 의 선택과 VGG 의 규칙 비교")


# ── 그림 2. 논문 표 1 — 망 A~E ──────────────────────────────────────────────
W, H = 820, 650
b = defs()
b += txt(20, 30, "논문 표 1 — 다섯 망은 단계마다 쌓는 층 수만 다르다 (굵은 테두리 = 앞 망에 더한 층)", 15, anchor="start", weight="bold")
names = ["A", "A-LRN", "B", "C", "D", "E"]
colx = [70 + 125 * i for i in range(6)]
for i, n in enumerate(names):
    key = "A" if n == "A-LRN" else n
    nw = sum(len(s) for s in CFG[key]) + 3
    b += txt(colx[i] + 50, 62, n, 14, weight="bold")
    b += txt(colx[i] + 50, 80, "가중 층 %d" % nw, 11, fill=INK2)
prev = {"A": None, "A-LRN": "A", "B": "A", "C": "B", "D": "B", "E": "D"}
y0 = 95
stage_y = []
y = y0
for s in range(5):
    maxn = max(len(CFG[k][s]) for k in "ABCDE") + (1 if s == 0 else 0)
    stage_y.append((y, maxn))
    y += maxn * 22 + 26
for i, n in enumerate(names):
    key = "A" if n == "A-LRN" else n
    for s in range(5):
        ys, _ = stage_y[s]
        items = list(CFG[key][s])
        pk = prev[n]
        pitems = list(CFG["A" if pk == "A-LRN" else pk][s]) if pk else items
        for j, (k, c) in enumerate(items):
            added = pk is not None and n != "A-LRN" and (j >= len(pitems) or pitems[j] != (k, c))
            col = FWD_SOFT if k == 3 else CODE_SOFT
            b += box(colx[i], ys + 22 * j, 100, 19, fill=col, stroke=INK if added else LINE, sw=2.2 if added else 1, rx=3)
            b += txt(colx[i] + 50, ys + 22 * j + 14, "conv%d-%d" % (k, c), 11, weight="bold" if added else None)
        if n == "A-LRN" and s == 0:
            b += box(colx[i], ys + 22, 100, 19, fill=REV_SOFT, stroke=INK, sw=2.2, rx=3)
            b += txt(colx[i] + 50, ys + 36, "LRN", 11, weight="bold")
for s in range(5):
    ys, maxn = stage_y[s]
    yp = ys + maxn * 22 + 4
    b += line(colx[0], yp + 6, colx[-1] + 100, yp + 6, CODE, 1, dash="4 3")
    b += txt(20, yp + 10, "풀링", 10, anchor="start", fill=CODE)
    b += txt(20, ys + 14, "%d" % (224 >> s), 11, anchor="start", fill=MUTED)
b += txt(410, 636, "왼쪽 숫자 = 그 단계의 가로·세로 크기(224 입력 기준). 뒤에 완전연결 4096 · 4096 · 1000 과 소프트맥스가 모든 망에 같게 붙는다", 11, fill=MUTED)
svg("fig02_configs", W, H, b, "망 A 부터 E 까지의 층 구성")


# ── 그림 3. 표 2 — 파라미터 수를 다시 세고, 합성곱과 완전연결로 가른다 ─────────────
W, H = 820, 380
b = defs()
b += txt(20, 30, "파라미터 수 — 이 파일이 센 값과 논문 표 2. 깊이가 11 → 19 로 늘어도 1.08 배다", 15, anchor="start", weight="bold")
PX0, PX1, PY0 = 90, 480, 320
def bx(v):
    return PX0 + v / 150e6 * (PX1 - PX0)
for t in range(0, 151, 25):
    b += line(bx(t * 1e6), 60, bx(t * 1e6), PY0, LINE, 1)
    b += txt(bx(t * 1e6), PY0 + 16, "%dM" % t, 10, fill=MUTED)
for j, n in enumerate("ABCDE"):
    cp, fp = PC[n][0], PC[n][1]
    y = 70 + 48 * j
    b += '<rect x="%s" y="%s" width="%s" height="26" fill="%s"/>' % (PX0, y, bx(cp) - PX0, FWD)
    b += '<rect x="%s" y="%s" width="%s" height="26" fill="%s"/>' % (bx(cp), y, bx(cp + fp) - bx(cp), REV)
    b += txt(PX0 - 10, y + 18, n, 13, anchor="end", weight="bold")
    b += txt(bx(cp + fp) + 6, y + 18, "%.1fM (논문 %dM)" % ((cp + fp) / 1e6, PAPER_M[n]), 11, anchor="start")
b += box(610, 60, 195, 250, fill=NODE, stroke=LINE)
b += txt(622, 84, "합성곱 / 완전연결", 12, anchor="start", weight="bold")
for j, n in enumerate("ABCDE"):
    cp, fp = PC[n][0], PC[n][1]
    b += txt(622, 112 + 26 * j, "%s: %.1fM / %.1fM" % (n, cp / 1e6, fp / 1e6), 11, anchor="start")
b += txt(622, 258, "완전연결 몫: E 에서도", 11, anchor="start", fill=INK2)
b += txt(622, 276, "%.0f%%, A 에서 %.0f%%" % (100 * PC["E"][1] / sum(PC["E"][:2]), 100 * PC["A"][1] / sum(PC["A"][:2])), 11, anchor="start", fill=INK2)
b += '<rect x="90" y="345" width="14" height="10" fill="%s"/>' % FWD
b += txt(110, 354, "합성곱", 11, anchor="start")
b += '<rect x="170" y="345" width="14" height="10" fill="%s"/>' % REV
b += txt(190, 354, "완전연결 (첫 층만 7·7·512·4096 = 102.8M)", 11, anchor="start")
svg("fig03_params", W, H, b, "망별 파라미터 수")


# ── 그림 4. 쌓은 3x3 의 수용장 ─────────────────────────────────────────────
def rf_stack(n, k=3):
    return 1 + n * (k - 1)
print("  [4] 3x3 을 n 층 쌓은 수용장: " + ", ".join("%d층 %dx%d" % (n, rf_stack(n), rf_stack(n)) for n in (1, 2, 3, 4)))
W, H = 820, 330
b = defs()
b += txt(20, 30, "3x3 을 쌓으면 수용장이 2 씩 넓어진다 — 한 줄 단면 (내가 그린 그림)", 15, anchor="start", weight="bold")
cx = 410
cell = 26
for lvl in range(4):
    y = 270 - 62 * lvl
    half = 3
    for i in range(-half, half + 1):
        rf = rf_stack(lvl) // 2
        inside = abs(i) <= (3 - lvl) and lvl < 3 or (lvl == 3 and i == 0)
        col = CODE_SOFT if (lvl == 0 and abs(i) <= 3) else (FWD_SOFT if inside else NODE)
        b += box(cx + i * (cell + 4) - cell / 2, y - cell / 2, cell, cell, fill=col, stroke=INK2 if inside or lvl == 0 else LINE, rx=3)
    lab = ["입력", "3x3 한 층 뒤", "두 층 뒤", "세 층 뒤"][lvl]
    b += txt(cx - 4 * (cell + 4) - 20, y + 4, lab, 12, anchor="end")
    if lvl > 0:
        b += txt(cx + 4 * (cell + 4) + 20, y + 4, "이 줄의 한 칸이 입력에서 보는 폭 = %dx%d" % (rf_stack(lvl), rf_stack(lvl)), 12, anchor="start", fill=FWD)
for lvl in range(3):
    y = 270 - 62 * lvl
    for i in range(-(2 - lvl), (2 - lvl) + 1):
        for d in (-1, 0, 1):
            b += line(cx + (i + d) * (cell + 4), y - 14, cx + i * (cell + 4), y - 48, LINE, 1)
b += txt(410, 312, "여백 1 · 보폭 1 이라 크기는 그대로이고, 층마다 가장자리가 한 칸씩 더 들어온다. 두 층 = 5x5, 세 층 = 7x7 (논문 2.3절)", 11, fill=MUTED)
svg("fig04_receptive_field", W, H, b, "쌓은 3x3 합성곱의 수용장")


# ── 그림 5. 7x7 한 층 대 3x3 세 층 — 파라미터와 비선형 ────────────────────────
C_ = 512
p7, p33 = 49 * C_ * C_, 27 * C_ * C_
p5, p32 = 25 * C_ * C_, 18 * C_ * C_
print("  [5] C=%d: 7x7 한 층 %s 대 3x3 세 층 %s (%.1f%% 더 많다),  5x5 한 층 %s 대 3x3 두 층 %s (%.1f%%)"
      % (C_, fmt(p7), fmt(p33), 100.0 * (p7 - p33) / p33, fmt(p5), fmt(p32), 100.0 * (p5 - p32) / p32))
W, H = 820, 360
b = defs()
b += txt(20, 30, "같은 7x7 수용장을 두 방법으로 — 입력·출력 채널이 C 로 같을 때 (C = 512 는 내가 넣은 값)", 15, anchor="start", weight="bold")
for p, (title, rows, total, nl, col) in enumerate([
        ("7x7 한 층", [("7x7 conv", "49C²")], p7, 1, REV),
        ("3x3 세 층", [("3x3 conv", "9C²"), ("3x3 conv", "9C²"), ("3x3 conv", "9C²")], p33, 3, FWD)]):
    x0 = 20 + 395 * p
    b += box(x0, 50, 385, 250, fill="none", stroke=LINE)
    b += txt(x0 + 192, 74, title, 14, weight="bold", fill=col)
    for j, (a, c) in enumerate(rows):
        y = 230 - 50 * j
        b += box(x0 + 60, y, 170, 36, fill=REV_SOFT if p == 0 else FWD_SOFT, stroke=col)
        b += txt(x0 + 145, y + 23, a, 12, weight="bold")
        b += txt(x0 + 250, y + 23, c, 12, anchor="start", fill=INK2)
        b += txt(x0 + 330, y + 23, "ReLU", 11, anchor="start", fill=OK)
    b += txt(x0 + 192, 286, "합계 %s = %s 개,  ReLU %d 번" % ("49C²" if p == 0 else "27C²", fmt(total), nl), 12, weight="bold")
b += txt(410, 326, "7x7 이 3x3 세 층보다 %.0f%% 많다 (49/27 = %.3f). 같은 셈으로 5x5 한 층은 3x3 두 층보다 %.0f%% 많다 (25/18)"
         % (100.0 * (p7 - p33) / p33, 49 / 27.0, 100.0 * (p5 - p32) / p32), 12, fill=INK2)
b += txt(410, 346, "논문은 이것을 「7x7 필터가 3x3 들로 분해되도록 강제하는 정규화」로 본다 — 7x7 이 낼 수 있는 모든 필터를 세 층이 낼 수 있는 것은 아니다", 11, fill=MUTED)
svg("fig05_param_compare", W, H, b, "7x7 한 층과 3x3 세 층의 파라미터 비교")


# ── 그림 6. 1x1 합성곱 — 망 C 대 망 D ─────────────────────────────────────────
W, H = 820, 360
b = defs()
b += txt(20, 30, "1x1 합성곱은 자리마다 채널을 섞는 선형 사상이다 — 망 C 는 1x1, 망 D 는 같은 자리에 3x3 을 둔다", 15, anchor="start", weight="bold")
b += box(20, 50, 380, 240, fill="none", stroke=LINE)
b += txt(210, 74, "1x1: 한 자리의 채널 벡터만 본다", 13, weight="bold", fill=CODE)
for i in range(5):
    for j in range(5):
        b += box(70 + 22 * i, 110 + 22 * j, 20, 20, fill=CODE_SOFT if (i, j) == (2, 2) else NODE, stroke=LINE, rx=2)
b += line(185, 165, 245, 165, CODE, 1.6, marker="ac")
b += box(255, 145, 110, 40, fill=CODE_SOFT, stroke=CODE)
b += txt(310, 170, "W · v (C x C)", 12, weight="bold")
b += txt(210, 250, "수용장이 넓어지지 않는다. ReLU 하나를 더할 뿐", 12, fill=INK2)
b += txt(210, 270, "3 단계 · 4 단계 · 5 단계 끝에 하나씩", 11, fill=MUTED)
b += box(420, 50, 380, 240, fill="none", stroke=LINE)
b += txt(610, 74, "같은 자리의 결과 (표 3, S = Q = 256)", 13, weight="bold")
rows = [("B (13 층)", 28.7, 9.9), ("C (16 층, 1x1 셋)", 28.1, 9.4), ("D (16 층, 3x3 셋)", 27.0, 8.8)]
for j, (n, t1, t5) in enumerate(rows):
    y = 115 + 44 * j
    b += txt(440, y, n, 12, anchor="start", weight="bold")
    b += txt(640, y, "top-1 %.1f" % t1, 12, anchor="start", fill=S_TOP1)
    b += txt(720, y, "top-5 %.1f" % t5, 12, anchor="start", fill=S_TOP5)
b += txt(610, 250, "B → C: %.1f / %.1f,  C → D: %.1f / %.1f (백분율 점)" % (28.7 - 28.1, 9.9 - 9.4, 28.1 - 27.0, 9.4 - 8.8), 12, fill=OK)
b += txt(610, 270, "논문의 해석: 비선형도 돕지만 공간 맥락이 더 돕는다", 11, fill=INK2)
b += txt(410, 322, "C 와 D 는 층 수가 같지만 파라미터가 다르다 — C %.1fM, D %.1fM. 그래서 C → D 의 차이는 「3x3 이라서」와 「파라미터가 %.1fM 많아서」가 섞여 있다"
         % (sum(PC["C"][:2]) / 1e6, sum(PC["D"][:2]) / 1e6, (sum(PC["D"][:2]) - sum(PC["C"][:2])) / 1e6), 11, fill=MUTED)
b += txt(410, 342, "(이 섞임은 내가 짚은 것이다. 논문은 두 요인을 가르지 않는다)", 11, fill=MUTED)
svg("fig06_1x1", W, H, b, "1x1 합성곱과 망 C, D 비교")


# ── 그림 7. 망 D 의 층별 비용 — 곱셈-덧셈, 활성, 파라미터 ─────────────────────────
Lyr = PC["D"][4]
fc_rows = [("fc-4096", 1, 4096, 25088 * 4096 + 4096, 25088 * 4096), ("fc-4096", 1, 4096, 4096 * 4096 + 4096, 4096 * 4096),
           ("fc-1000", 1, 1000, 4096 * 1000 + 1000, 4096 * 1000)]
allL = [(n, s, c, p, m) for n, s, c, p, m in Lyr] + fc_rows
tot_mac = sum(r[4] for r in allL)
tot_act = sum(r[1] * r[1] * r[2] for r in allL)
print("  [7] 망 D, 224 입력: 곱셈-덧셈 합 %.2f G, 활성 수 합 %s (float32 %.1f MB/장, 순방향만)"
      % (tot_mac / 1e9, fmt(tot_act), tot_act * 4 / 1e6))
first2 = sum(r[1] * r[1] * r[2] for r in allL[:2])
print("      첫 두 층 활성 %s = 전체의 %.1f%%,  완전연결 파라미터 %.1f%%,  완전연결 곱셈-덧셈 %.1f%%"
      % (fmt(first2), 100.0 * first2 / tot_act, 100.0 * sum(r[3] for r in fc_rows) / sum(r[3] for r in allL),
         100.0 * sum(r[4] for r in fc_rows) / tot_mac))
W, H = 820, 470
b = defs()
b += txt(20, 30, "망 D(16 층)의 층별 비용 — 224x224 한 장, 이 파일이 센 값", 15, anchor="start", weight="bold")
metrics = [("활성 수 (메모리)", lambda r: r[1] * r[1] * r[2], S_TOP1), ("곱셈-덧셈 (계산)", lambda r: r[4], S_TOP5), ("파라미터", lambda r: r[3], S_THIRD)]
colw = 230
for mi, (mname, f, col) in enumerate(metrics):
    x0 = 150 + 225 * mi
    b += txt(x0 + colw / 2 - 10, 60, mname, 12, weight="bold", fill=col)
    vals = [f(r) for r in allL]
    vmax = max(vals)
    tot = sum(vals)
    for j, (r, v) in enumerate(zip(allL, vals)):
        y = 72 + 20 * j
        w_ = (colw - 70) * v / vmax
        b += '<rect x="%s" y="%s" width="%.1f" height="14" rx="2" fill="%s"/>' % (x0, y, max(w_, 0.5), col)
        b += txt(x0 + w_ + 4, y + 11, "%.1f%%" % (100.0 * v / tot), 9, anchor="start", fill=INK2)
for j, r in enumerate(allL):
    b += txt(140, 72 + 20 * j + 11, "%s  %dx%d" % (r[0], r[1], r[1]), 10, anchor="end")
b += txt(410, 440, "메모리는 앞쪽(224x224, 64 채널)에, 계산은 합성곱 층 전체에 퍼져 있고, 파라미터는 첫 완전연결 층 하나에 몰린다", 11, fill=INK2)
b += txt(410, 458, "합계: 곱셈-덧셈 %.2f G, 활성 %.1f M 개, 파라미터 %.1f M — 퍼센트는 각 열의 합에 대한 몫" % (tot_mac / 1e9, tot_act / 1e6, sum(r[3] for r in allL) / 1e6), 11, fill=MUTED)
svg("fig07_cost_D", W, H, b, "망 D 의 층별 계산, 메모리, 파라미터")


# ── 그림 8. 깊이와 비용 — 파라미터는 거의 같은데 계산은 2.6 배 ───────────────────
W, H = 820, 330
b = defs()
b += txt(20, 30, "「깊이만 다르다」의 비용 — 파라미터와 곱셈-덧셈을 망 A 를 1 로 두고 (이 파일이 센 값)", 15, anchor="start", weight="bold")
pa = sum(PC["A"][:2]); ma = PC["A"][2] + PC["A"][3]
PX0, PX1 = 150, 700
def sx(v):
    return PX0 + (v - 0.9) / 1.9 * (PX1 - PX0)
for t in (1.0, 1.5, 2.0, 2.5):
    b += line(sx(t), 55, sx(t), 290, LINE, 1)
    b += txt(sx(t), 306, "%.1f 배" % t, 10, fill=MUTED)
for j, n in enumerate("ABCDE"):
    y = 75 + 44 * j
    p = sum(PC[n][:2]) / pa
    m = (PC[n][2] + PC[n][3]) / ma
    b += txt(PX0 - 12, y + 5, "%s (%d 층)" % (n, sum(len(s) for s in CFG[n]) + 3), 12, anchor="end", weight="bold")
    b += line(sx(p), y, sx(m), y, LINE, 3)
    b += circ(sx(p), y, 6, S_THIRD, S_THIRD)
    b += circ(sx(m), y, 6, S_TOP5, S_TOP5)
    b += txt(sx(m) + 10, y + 4, "%.2f G" % ((PC[n][2] + PC[n][3]) / 1e9), 11, anchor="start", fill=S_TOP5)
    print("  [8] %s: 파라미터 %.3f 배, 곱셈-덧셈 %.3f 배 (A 대비)" % (n, p, m))
b += circ(160, 322, 5, S_THIRD, S_THIRD); b += txt(170, 326, "파라미터", 11, anchor="start")
b += circ(250, 322, 5, S_TOP5, S_TOP5); b += txt(260, 326, "곱셈-덧셈 (오른쪽 수 = 224 입력 한 장)", 11, anchor="start")
svg("fig08_depth_cost", W, H, b, "망별 파라미터와 계산량 배수")


# ── 그림 9. 학습 척도 S — 고정 대 흔들기 ────────────────────────────────────────
W, H = 820, 360
b = defs()
b += txt(20, 30, "학습 척도 S = 짧은 변을 S 로 줄인 뒤 224x224 를 잘라 낸다 — S 가 클수록 자른 조각은 물체의 일부다", 15, anchor="start", weight="bold")
for j, S in enumerate((256, 384, 512)):
    x0 = [40, 210, 440][j]
    sc = 0.3
    w_, h_ = S * 4 / 3.0 * sc, S * sc
    b += box(x0, 70, w_, h_, fill=NODE, stroke=INK2, rx=2)
    b += box(x0 + (w_ - 224 * sc) / 2, 70 + (h_ - 224 * sc) / 2, 224 * sc, 224 * sc, fill=FWD_SOFT, stroke=FWD, sw=2, rx=2)
    frac = 224.0 / S
    print("  [9] S=%d: 자른 조각이 짧은 변의 %.1f%%, 넓이(4:3 가정)의 %.1f%%" % (S, 100 * frac, 100 * 224 * 224 / (S * S * 4 / 3.0)))
    b += txt(x0 + w_ / 2, 70 + h_ + 20, "S = %d" % S, 13, weight="bold")
    b += txt(x0 + w_ / 2, 70 + h_ + 38, "짧은 변의 %.0f%%, 넓이의 %.0f%%" % (100 * frac, 100 * 224 * 224 / (S * S * 4 / 3.0)), 11, fill=INK2)
b += box(30, 290, 760, 56, fill=NODE, stroke=LINE)
b += txt(50, 312, "고정: S = 256 또는 384 (384 망은 256 망에서 시작, 학습률 10⁻³).  흔들기: 그림마다 S 를 [256, 512] 에서 뽑는다 — 384 망에서 미세조정", 11, anchor="start")
b += txt(50, 332, "넓이 비율은 4:3 사진을 가정한 내 계산이다. 논문은 사진의 가로세로 비를 적지 않는다", 11, anchor="start", fill=MUTED)
svg("fig09_scale", W, H, b, "학습 척도에 따른 자르기 비율")


# ── 그림 10. 조밀 평가 — 완전연결을 합성곱으로 바꾼다 ────────────────────────────
def score_map(q):
    return q // 32 - 6
print("  [10] 정사각 입력 Q 에서 점수 지도 크기 (Q//32 - 6): " + ", ".join("Q=%d → %dx%d" % (q, score_map(q), score_map(q)) for q in (224, 256, 384, 512)))
W, H = 820, 380
b = defs()
b += txt(20, 30, "조밀 평가 — 첫 완전연결 층을 7x7 합성곱으로, 뒤 둘을 1x1 로 바꾸면 어떤 크기의 그림에도 돌릴 수 있다", 15, anchor="start", weight="bold")
flow = [("그림 Q x Q", NODE, INK2), ("합성곱 + 풀링 다섯", FWD_SOFT, FWD), ("Q/32 x Q/32 x 512", NODE, INK2),
        ("7x7 conv 4096", REV_SOFT, REV), ("1x1 conv 4096", REV_SOFT, REV), ("1x1 conv 1000", REV_SOFT, REV), ("평균 → 1000", CODE_SOFT, CODE)]
for j, (t, f, s) in enumerate(flow):
    x = 20 + 113 * j
    b += box(x, 70, 104, 50, fill=f, stroke=s, sw=1.4)
    b += txt(x + 52, 100, t, 10.5, weight="bold")
    if j < 6:
        b += line(x + 105, 95, x + 112, 95, INK2, 1.4, marker="ai")
b += txt(410, 148, "점수 지도의 크기 = Q/32 − 6 (정사각 그림을 가정한 내 계산). 한 칸이 224x224 조각 하나의 점수에 해당한다", 12, fill=INK2)
for j, q in enumerate((224, 256, 384, 512)):
    x0 = 60 + 185 * j
    m = score_map(q)
    cs = min(12, 110 // max(m, 1))
    for a in range(m):
        for c in range(m):
            b += box(x0 + a * cs, 180 + c * cs, cs - 1, cs - 1, fill=CODE_SOFT, stroke=CODE, sw=0.6, rx=1)
    b += txt(x0 + 60, 320, "Q = %d → %d x %d = %d 칸" % (q, m, m, m * m), 12, weight="bold")
b += txt(410, 352, "여러 조각을 따로 잘라 망을 다시 돌리는 대신 한 번에 모든 자리의 점수를 얻는다 (보폭은 32 픽셀). 좌우 뒤집은 그림의 결과와 평균한다", 11, fill=MUTED)
svg("fig10_dense_eval", W, H, b, "완전연결을 합성곱으로 바꾼 조밀 평가")


# ── 그림 11. 표 3 — 한 척도 평가 ─────────────────────────────────────────────
T3 = [("A", "256", 29.6, 10.4), ("A-LRN", "256", 29.7, 10.5), ("B", "256", 28.7, 9.9),
      ("C", "256", 28.1, 9.4), ("C", "384", 28.1, 9.3), ("C", "[256;512]", 27.3, 8.8),
      ("D", "256", 27.0, 8.8), ("D", "384", 26.8, 8.7), ("D", "[256;512]", 25.6, 8.1),
      ("E", "256", 27.3, 9.0), ("E", "384", 26.9, 8.7), ("E", "[256;512]", 25.5, 8.0)]
W, H = 820, 470
b = defs()
b += txt(20, 30, "논문 표 3 — 한 시험 척도에서의 검증 오차 (%). 점 = top-1, 네모 = top-5", 15, anchor="start", weight="bold")
def panel_x(v, lo, hi, x0, x1):
    return x0 + (v - lo) / (hi - lo) * (x1 - x0)
for side, (lo, hi, x0, x1, key, col, lab) in enumerate([(25, 30, 180, 470, 2, S_TOP1, "top-1"), (7.5, 11, 500, 790, 3, S_TOP5, "top-5")]):
    b += txt((x0 + x1) / 2, 58, lab, 13, weight="bold", fill=col)
    v = lo
    while v <= hi + 1e-9:
        X = panel_x(v, lo, hi, x0, x1)
        b += line(X, 66, X, 420, LINE, 1)
        b += txt(X, 436, "%g" % v, 10, fill=MUTED)
        v += 1.0 if side == 0 else 0.5
    for j, r in enumerate(T3):
        y = 82 + 28 * j
        X = panel_x(r[key], lo, hi, x0, x1)
        if side == 0:
            b += circ(X, y, 5, col, col)
        else:
            b += '<rect x="%s" y="%s" width="9" height="9" fill="%s"/>' % (X - 4.5, y - 4.5, col)
        b += txt(X + 9, y + 4, "%.1f" % r[key], 10, anchor="start", fill=INK2)
for j, r in enumerate(T3):
    y = 82 + 28 * j
    b += txt(20, y + 4, r[0], 12, anchor="start", weight="bold")
    b += txt(80, y + 4, "S = " + r[1], 11, anchor="start", fill=INK2)
    if j in (2, 3, 6, 9):
        b += line(20, y - 14, 790, y - 14, LINE, 1)
b += txt(410, 460, "시험 척도 Q 는 고정 S 이면 Q = S, 흔들기 [256;512] 이면 Q = 384. 변동 폭은 논문에 없다", 11, fill=MUTED)
svg("fig11_table3", W, H, b, "표 3 한 척도 평가 결과")


# ── 그림 12. 무엇이 얼마를 냈나 — 표 3~6 의 차이 ──────────────────────────────
steps = [("LRN 넣기 (A → A-LRN)", 29.6 - 29.7, 10.4 - 10.5),
         ("깊이 A → D (S=256)", 29.6 - 27.0, 10.4 - 8.8),
         ("D → E (S=256)", 27.0 - 27.3, 8.8 - 9.0),
         ("D → E (흔들기)", 25.6 - 25.5, 8.1 - 8.0),
         ("학습 흔들기 (D, 384 → [256;512])", 26.8 - 25.6, 8.7 - 8.1),
         ("시험 척도 셋 (D 흔들기, 표 3 → 4)", 25.6 - 24.8, 8.1 - 7.5),
         ("여러 조각 + 조밀 (D, 표 5)", 24.8 - 24.4, 7.5 - 7.2),
         ("망 둘 합치기 (D·E, 표 6 → D 표 5)", 24.4 - 23.7, 7.2 - 6.8)]
print("  [12] 개선량 (백분율 점, 양수 = 좋아짐): " + "; ".join("%s %.1f/%.1f" % (n, a, c) for n, a, c in steps))
W, H = 820, 440
b = defs()
b += txt(20, 30, "무엇이 얼마를 냈나 — 논문 표 3~6 의 두 행 차이 (양수 = 오차가 줄었다, 백분율 점, 이 파일이 뺀 값)", 14, anchor="start", weight="bold")
X0, X1 = 330, 780
def dx(v):
    return X0 + (v + 0.5) / 3.2 * (X1 - X0)
for t in (-0.5, 0, 0.5, 1.0, 1.5, 2.0, 2.5):
    b += line(dx(t), 50, dx(t), 370, LINE if t else INK2, 1)
    b += txt(dx(t), 386, "%+.1f" % t if t else "0", 10, fill=MUTED)
for j, (n, a, c) in enumerate(steps):
    y = 70 + 38 * j
    b += txt(X0 - 10, y + 8, n, 11.5, anchor="end")
    for k, (v, col) in enumerate(((a, S_TOP1), (c, S_TOP5))):
        yy = y + k * 12
        x_a, x_b = dx(0), dx(v)
        b += '<rect x="%s" y="%s" width="%s" height="10" fill="%s"/>' % (min(x_a, x_b), yy, abs(x_b - x_a) + 0.5, col)
        b += txt(max(x_a, x_b) + 4, yy + 9, "%+.1f" % v, 9.5, anchor="start", fill=INK2)
b += '<rect x="330" y="398" width="12" height="10" fill="%s"/>' % S_TOP1
b += txt(348, 407, "top-1", 11, anchor="start")
b += '<rect x="400" y="398" width="12" height="10" fill="%s"/>' % S_TOP5
b += txt(418, 407, "top-5", 11, anchor="start")
b += txt(410, 430, "LRN 과 D → E 는 0.1~0.3 점이라 변동 폭 없이 순서를 매기지 않는다", 11, fill=MUTED)
svg("fig12_deltas", W, H, b, "설계 요소별 오차 개선량")


# ── 그림 13. 표 7 — ILSVRC 분류 top-5 시험 오차 ───────────────────────────────
T7 = [("VGG, 망 2", 6.8), ("VGG, 망 1", 7.0), ("VGG 제출, 망 7", 7.3), ("GoogLeNet, 망 1", 7.9), ("GoogLeNet, 망 7", 6.7),
      ("MSRA, 망 11", 8.1), ("MSRA, 망 1", 9.1), ("Clarifai, 여러 망", 11.7), ("Clarifai, 망 1", 12.5),
      ("Zeiler & Fergus, 망 6", 14.8), ("Zeiler & Fergus, 망 1", 16.1), ("OverFeat, 망 7", 13.6),
      ("Krizhevsky 외, 망 5", 16.4)]
W, H = 820, 460
b = defs()
b += txt(20, 30, "논문 표 7 — ILSVRC 분류, top-5 시험 오차 (%) (바깥 학습 데이터 없는 결과만. 값이 없는 행은 뺐다)", 14, anchor="start", weight="bold")
X0, X1 = 200, 740
for t in range(0, 19, 3):
    b += line(X0 + t / 18.0 * (X1 - X0), 50, X0 + t / 18.0 * (X1 - X0), 420, LINE, 1)
    b += txt(X0 + t / 18.0 * (X1 - X0), 436, "%d" % t, 10, fill=MUTED)
for j, (n, v) in enumerate(T7):
    y = 58 + 28 * j
    col = S_TOP5 if n.startswith("VGG") else (S_TOP1 if n.startswith("Goog") else MUTED)
    b += '<rect x="%s" y="%s" width="%s" height="18" rx="2" fill="%s"/>' % (X0, y, v / 18.0 * (X1 - X0), col)
    b += txt(X0 - 8, y + 13, n, 11, anchor="end", weight="bold" if n.startswith("VGG") else None)
    b += txt(X0 + v / 18.0 * (X1 - X0) + 6, y + 13, "%.1f" % v, 11, anchor="start")
b += txt(410, 454, "망 하나끼리: VGG 7.0 대 GoogLeNet 7.9 (0.9 점). 여러 망: 2014 분류 1 등은 GoogLeNet 7 망 6.7, VGG 는 2 등(제출 7.3, 제출 뒤 6.8)", 11, fill=INK2)
svg("fig13_sota", W, H, b, "ILSVRC 분류 결과 비교")


# ── 그림 14. 부록 B — 다른 데이터로 옮긴 특징 ─────────────────────────────────
T11 = [("VOC-2007 mAP", 82.4, 89.3, 89.3, 89.7, "Chatfield 외"), ("VOC-2012 mAP", 83.2, 89.0, 89.0, 89.3, "Chatfield 외"),
       ("Caltech-101 재현율", 93.4, 91.8, 92.3, 92.7, "He 외 (SPP)"), ("Caltech-256 재현율", 77.6, 85.0, 85.1, 86.2, "Chatfield 외")]
for n, prev_, d, e, de, who in T11:
    print("  [14] %s: 앞선 최고(%s) %.1f → D %.1f, E %.1f, D+E %.1f (D+E 차이 %+.1f)" % (n, who, prev_, d, e, de, de - prev_))
W, H = 820, 400
b = defs()
b += txt(20, 30, "부록 B — ImageNet 으로 배운 망을 얼려 두고 특징만 뽑아 선형 SVM 을 붙였을 때 (논문 표 11)", 15, anchor="start", weight="bold")
for j, (n, prev_, d, e, de, who) in enumerate(T11):
    x0 = 30 + 195 * j
    b += box(x0, 55, 180, 280, fill="none", stroke=LINE)
    b += txt(x0 + 90, 78, n, 12, weight="bold")
    lo, hi = 70, 100
    def Y(v):
        return 310 - (v - lo) / (hi - lo) * 210
    for t in (70, 80, 90, 100):
        b += line(x0 + 10, Y(t), x0 + 170, Y(t), LINE, 1)
        b += txt(x0 + 8, Y(t) + 4, "%d" % t, 9, anchor="end", fill=MUTED)
    for k, (lab, v, col) in enumerate((("앞선 최고", prev_, MUTED), ("D", d, S_TOP1), ("E", e, S_TOP1), ("D+E", de, S_TOP5))):
        bx_ = x0 + 25 + 37 * k
        b += '<rect x="%s" y="%.1f" width="28" height="%.1f" rx="2" fill="%s"/>' % (bx_, Y(v), 310 - Y(v), col)
        b += txt(bx_ + 14, Y(v) - 4, "%.1f" % v, 9.5)
        b += txt(bx_ + 14, 326, lab, 9.5, fill=INK2)
    b += txt(x0 + 90, 352, "앞선 최고: %s" % who, 10, fill=MUTED)
    b += txt(x0 + 90, 370, "D+E 차이 %+.1f 점" % (de - prev_), 11, weight="bold", fill=OK if de > prev_ else NO)
b += txt(410, 394, "Caltech-101 만 앞선 최고보다 낮다. 본문의 「6% 넘게」는 D+E 로는 두 VOC 모두 선다(7.3 · 6.1). 망 하나로는 VOC-2012 에서 5.8 점이다", 11, fill=INK2)
svg("fig14_transfer", W, H, b, "다른 데이터셋으로의 전이 결과")


# ── 그림 15. AlexNet(2012) 대 VGG(2015) ────────────────────────────────────
def alex_count():
    conv = [(11, 3, 96), (5, 96, 256), (3, 256, 384), (3, 384, 384), (3, 384, 256)]
    p = sum(k * k * ci * co + co for k, ci, co in conv)
    fc = [(6 * 6 * 256, 4096), (4096, 4096), (4096, 1000)]
    p += sum(a * c + c for a, c in fc)
    return p
ap = alex_count()
print("  [15] AlexNet 을 두 GPU 나눔 없이 센 파라미터 %s (VGG D 의 %.1f%%)" % (fmt(ap), 100.0 * ap / sum(PC["D"][:2])))
W, H = 820, 470
b = defs()
b += txt(20, 30, "AlexNet(2012) 과 VGG(2015) — 같은 뼈대(합성곱 + 완전연결 셋), 다른 선택", 15, anchor="start", weight="bold")
rows = [("학습되는 층", "8", "11 ~ 19"),
        ("첫 합성곱", "11x11, 보폭 4", "3x3, 보폭 1"),
        ("커널 크기", "11 · 5 · 3", "모두 3 (C 만 1x1 셋)"),
        ("정규화", "LRN", "없다 (도움이 없었다)"),
        ("풀링", "3x3 보폭 2 (겹침)", "2x2 보폭 2"),
        ("파라미터", "%.1fM (GPU 나눔 없이 센 값)" % (ap / 1e6), "133 ~ 144M"),
        ("초기화", "무작위", "얕은 A 를 먼저 배워 옮긴다"),
        ("시험", "조각 10 개", "조밀 평가 + 척도 셋"),
        ("ILSVRC top-5 시험 (망 1)", "18.2 (검증, 표 7)", "7.0")]
cw = [220, 280, 280]
x0, y0 = 20, 55
b += box(x0, y0, sum(cw), 36, fill="#DDE3E0", stroke=LINE, rx=4)
for k, t in enumerate(["", "AlexNet 2012", "VGG 2015"]):
    b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y0 + 23, t, 13, weight="bold", fill=[INK, REV, FWD][k])
for r, row in enumerate(rows):
    y = y0 + 36 + 38 * r
    b += box(x0, y, sum(cw), 38, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    for k, t in enumerate(row):
        b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y + 24, t, 12, weight="bold" if k == 0 else None)
b += txt(410, 458, "AlexNet 칸은 앞 노트의 AlexNet 논문과 이 논문 표 7 에서 옮겼다. 표 7 의 AlexNet 망 1 은 top-5 시험 값이 없어 검증 값을 적었다", 11, fill=MUTED)
svg("fig15_alexnet_vs_vgg", W, H, b, "AlexNet 과 VGG 비교 표")


# ── 그림 16. 계보와 곁가지 — 층별 수용장 (이상 탐지 쪽) ──────────────────────────
def rf_layers(name):
    rf, jump, out = 1, 1, []
    for si, stage in enumerate(CFG[name]):
        for k, c in stage:
            rf += (k - 1) * jump
            out.append(("conv%d" % (si + 1), rf, jump, c))
        rf += 1 * jump
        jump *= 2
        out.append(("pool%d" % (si + 1), rf, jump, None))
    return out
rfs = rf_layers("D")
print("  [16] 망 D 수용장: " + ", ".join("%s %d(보폭 %d)" % (n, r, j) for n, r, j, _ in rfs if n.startswith("pool")))
W, H = 820, 420
b = defs()
b += txt(20, 30, "계보, 그리고 곁가지 — 망 D 의 각 풀링 뒤 한 칸이 보는 입력 크기 (이 파일이 센 수용장)", 15, anchor="start", weight="bold")
chainL = [("LeNet 1998", "작은 합성곱 망", NODE, INK2), ("AlexNet 2012", "크게, 층마다 다르게", REV_SOFT, REV),
          ("VGG 2015", "3x3 하나로, 깊게", FWD_SOFT, FWD), ("BN · ResNet (다음)", "더 깊게 배우는 법", CODE_SOFT, CODE)]
for k, (t, d, f, s) in enumerate(chainL):
    x = 25 + 200 * k
    b += box(x, 50, 170, 56, fill=f, stroke=s, sw=1.6)
    b += txt(x + 85, 74, t, 13, weight="bold", fill=s)
    b += txt(x + 85, 94, d, 11, fill=INK2)
    if k < 3:
        b += line(x + 172, 78, x + 198, 78, INK2, 1.5, marker="ai")
b += txt(410, 130, "넘긴 것: 19 층에서 오차가 멈췄고, 깊은 망은 얕은 A 에서 가중치를 옮겨 와야 시작할 수 있었다 — 다음 두 편이 받는 자리", 11, fill=INK)
pools = [(n, r, j) for n, r, j, _ in rfs if n.startswith("pool")]
X0 = 60
for k, (n, r, j) in enumerate(pools):
    x = X0 + 150 * k
    s = min(r, 224) * 0.42
    b += box(x, 160, 94, 94, fill=NODE, stroke=LINE, rx=2)
    b += box(x + 47 - s / 2 if s < 94 else x, 160 + 47 - s / 2 if s < 94 else 160, min(s, 94), min(s, 94), fill=CODE_SOFT, stroke=CODE, rx=2)
    b += txt(x + 47, 272, "%s 뒤" % n.replace("pool", "풀링 "), 12, weight="bold")
    b += txt(x + 47, 290, "%d 픽셀 (보폭 %d)" % (r, j), 11, fill=INK2)
b += txt(410, 150, "네모 = 224x224 입력, 노란 칸 = 한 자리의 수용장 (224 를 넘으면 가득 찬다)", 10, fill=MUTED)
b += box(25, 310, 770, 100, fill=NODE, stroke=LINE)
b += txt(45, 334, "곁가지 — 이상 탐지로 가는 길 (논문은 이 쓰임을 적지 않는다. 내가 잇는 자리다)", 13, anchor="start", weight="bold", fill=REV)
b += txt(45, 358, "부록 B: ImageNet 으로 배운 망을 얼려 두고 특징만 떼어 다른 과제에 붙여도 된다 — 사전학습 특징으로 이상을 찾는 방법들의 전제", 11, anchor="start")
b += txt(45, 380, "조밀 평가처럼 돌리면 중간 층 한 칸이 위 크기의 조각 하나를 요약한다. 어느 층을 쓰느냐가 「얼마나 큰 흠을 보느냐」다", 11, anchor="start")
b += txt(45, 400, "잴 방법은 이 노트의 돌려 볼 것 D 에 적었다", 11, anchor="start", fill=MUTED)
svg("fig16_lineage", W, H, b, "계보와 층별 수용장")

print("끝.")
