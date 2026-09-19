# -*- coding: utf-8 -*-
"""역전파 노트(Nature 1986)의 그림 열네 개를 만든다.

색과 글꼴은 퍼셉트론 노트 · DDPM 노트의 그림과 맞췄다 — 저장소의 노트들이 한 벌로
읽히게 하려는 것이다. 그림을 고치려면 이 파일을 고쳐 다시 돌린다.
바깥 데이터를 읽지 않으므로 어디서나 돈다.

  python make_figures.py

그림 8 · 9 에 들어가는 수는 논문 그림 1 의 가중치를 식 (1)(2) 에 넣어 이 파일이
직접 계산한 것이다. 계산한 값은 돌릴 때 화면에도 찍는다.
"""
import io, os, math

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"   # 그림 상자 배경
NODE      = "#F6F7F5"   # 노드 안쪽
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 순방향, 정해져 있는 것
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 역방향, 학습으로 바뀌는 것
REV_SOFT  = "#F2DED2"
OK        = "#1E8449"   # 초록 — 된다
NO        = "#C0392B"   # 빨강 — 안 된다 · 금지
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


def txt(x, y, t, size=12, fill=None, anchor="middle", weight=None, style=None):
    a = 'x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s"' % (x, y, size, fill or INK, anchor)
    if weight:
        a += ' font-weight="%s"' % weight
    if style:
        a += ' font-style="%s"' % style
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


def path(d, stroke=None, fill="none", sw=1.6, dash=None, marker=None, op=None):
    a = '<path d="%s" fill="%s" stroke="%s" stroke-width="%s"' % (d, fill, stroke or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if marker:
        a += ' marker-end="url(#%s)"' % marker
    if op:
        a += ' opacity="%s"' % op
    return a + "/>"


def E(s, size=12):
    """'∂E/∂y_j' 처럼 밑줄로 적은 첨자를 괄호 표기로 바꾼다 — y_j 는 y(j), w_ji 는 w(j,i) 가 된다.

    아래첨자를 tspan 으로 내리지 않는 이유가 있다. SVG 뷰어마다 tspan 의 세로 이동을
    다르게 처리해 글자가 겹치는 일이 있어서, 어디서 열어도 같게 보이는 괄호 표기로 적는다.
    노트 본문의 수식은 LaTeX 로 적으므로 거기서는 제대로 된 아래첨자로 보인다.
    """
    out, i = "", 0
    while i < len(s):
        if s[i] == "_" and i + 1 < len(s) and (s[i + 1].isalnum()):
            j = i + 1
            while j < len(s) and s[j].isalnum():
                j += 1
            sub = s[i + 1:j]
            out += "(" + (",".join(sub) if len(sub) > 1 else sub) + ")"
            i = j
        else:
            out += s[i]
            i += 1
    return out


def sigmoid(v):
    return 1.0 / (1.0 + math.exp(-v))


print("그림을 만든다 ->", OUT)


# ── 1. 퍼셉트론이 남긴 빈칸 ────────────────────────────────────────────────
b = '<defs>%s%s%s</defs>' % (arrow("g1", FWD), arrow("g2", REV), arrow("g3", NO))
b += txt(390, 28, "퍼셉트론이 남긴 빈칸 — 은닉 유닛에는 정답이 없다", 14, INK, weight=600)

b += box(24, 46, 352, 232, "#F4F6F4", LINE, 1.2, 10)
b += txt(200, 70, "층이 하나일 때", 12.5, FWD, weight=600)
for y in [120, 165, 210]:
    b += circ(80, y, 15, FWD_SOFT, FWD, 1.2)
    b += line(95, y, 240, 165, MUTED, 1.0, marker="g1", op="0.75")
b += circ(258, 165, 20, REV_SOFT, REV, 1.6)
b += txt(258, 170, "y", 13, REV, weight=600)
b += box(300, 148, 56, 34, "#FFFFFF", REV, 1.2, 6)
b += txt(328, 170, "d", 13, REV, weight=600)
b += txt(328, 128, "정답", 11.5, REV)
b += line(282, 165, 296, 165, REV, 1.4)
b += txt(200, 250, "오차를 바로 안다 (y − d)", 12.5, INK, weight=600)
b += txt(200, 268, "그래서 가중치를 어디로 옮길지 나온다", 11.5, MUTED)

b += box(404, 46, 352, 232, "#F4F6F4", LINE, 1.2, 10)
b += txt(580, 70, "층을 하나 더 쌓으면", 12.5, FWD, weight=600)
for y in [120, 165, 210]:
    b += circ(450, y, 15, FWD_SOFT, FWD, 1.2)
    for yh in [140, 195]:
        b += line(465, y, 552, yh, MUTED, 0.9, op="0.6")
for yh in [140, 195]:
    b += circ(570, yh, 18, "#FFFFFF", NO, 1.8)
    b += txt(570, yh + 5, "?", 15, NO, weight=700)
    b += line(588, yh, 660, 165, MUTED, 1.0, marker="g1", op="0.75")
b += circ(678, 165, 20, REV_SOFT, REV, 1.6)
b += txt(678, 170, "y", 13, REV, weight=600)
b += box(712, 148, 40, 34, "#FFFFFF", REV, 1.2, 6)
b += txt(732, 170, "d", 13, REV, weight=600)
b += txt(570, 108, "은닉 유닛", 11.5, NO, weight=600)
b += txt(580, 250, "이 자리의 정답이 주어지지 않는다", 12.5, NO, weight=600)
b += txt(580, 268, "1958년의 규칙 (y − d) 를 쓸 수가 없다", 11.5, MUTED)

b += txt(390, 298, "1986년 논문이 채운 것이 바로 이 물음표다 — 오차를 뒤로 보내 층마다 몫을 나눈다", 12.5, REV, weight=600)
svg("fig01_gap", 780, 316, b,
    "층이 하나일 때는 출력에 정답이 있어 오차를 바로 알지만 은닉 유닛에는 정답이 주어지지 않는다")


# ── 2. 소자 하나가 하는 계산 (식 1, 2) ─────────────────────────────────────
b = '<defs>%s</defs>' % arrow("u1", INK2)
b += txt(390, 28, "소자 하나 — 선형으로 더하고 매끄러운 함수를 통과시킨다", 14, INK, weight=600)
ys = [86, 128, 170]
names = ["y_1", "y_2", "y_3"]
ws = ["w_j1", "w_j2", "w_j3"]
for y, n, w_ in zip(ys, names, ws):
    b += box(38, y - 16, 54, 32, NODE, FWD, 1.1, 5)
    b += txt(65, y + 5, E(n, 12.5), 12.5, FWD)
    b += line(92, y, 226, 140, INK2, 1.3, marker="u1", op="0.8")
    b += txt(150, y - 8 if y < 140 else y + 16, E(w_, 11.5), 11.5, MUTED)
b += box(38, 212 - 16, 54, 32, "#FFFFFF", MUTED, 1.1, 5)
b += txt(65, 217, "1", 12.5, MUTED)
b += line(92, 212, 226, 152, MUTED, 1.3, dash="4 3", marker="u1", op="0.8")
b += txt(200, 192, "편향", 11.5, MUTED)
b += txt(65, 244, "항상 1 인 입력", 11, MUTED)

b += box(228, 112, 96, 64, "#FFFFFF", INK, 1.4, 8)
b += txt(276, 140, "Σ", 20, INK, weight=600)
b += txt(276, 162, "선형 합", 11, MUTED)
b += line(324, 144, 372, 144, INK2, 1.4, marker="u1")
b += txt(348, 130, E("x_j", 12), 12, INK, weight=600)

b += box(374, 112, 96, 64, "#FFFFFF", REV, 1.4, 8)
b += path("M 392 166 C 412 166 420 122 448 122", REV, "none", 2.0)
b += txt(422, 162, "로지스틱", 10.5, REV)
b += line(470, 144, 518, 144, INK2, 1.4, marker="u1")

b += circ(544, 144, 24, REV_SOFT, REV, 1.6)
b += txt(544, 149, E("y_j", 13), 13, REV, weight=600)
b += txt(520, 188, "이 유닛의 출력", 11.5, MUTED)

b += box(568, 66, 200, 108, "#F4F6F4", LINE, 1.2, 8)
b += txt(660, 100, E("x_j = Σ_i y_i w_ji", 12.5), 12.5, INK)
b += txt(758, 100, "(1)", 11, MUTED, anchor="end")
b += txt(660, 142, E("y_j = 1 / (1 + exp(−x_j))", 12.5), 12.5, INK)
b += txt(758, 162, "(2)", 11, MUTED, anchor="end")
b += txt(668, 196, "첨자는 괄호로 적었다", 10.5, MUTED)
b += txt(668, 212, "y(j) 는 유닛 j 의 출력이다", 10.5, MUTED)

b += txt(390, 232, "편향은 따로 다루지 않는다 — 값이 늘 1 인 입력을 하나 더 두면 그 가중치가 편향이고,", 12, INK2)
b += txt(390, 250, "부호만 뒤집으면 퍼셉트론의 문턱과 같은 것이다. 나머지 가중치와 똑같이 학습된다.", 12, INK2)
b += txt(390, 276, "논문의 말: 식 (1)(2) 를 꼭 써야 하는 것은 아니고 미분이 유계인 함수면 된다.", 12, MUTED, style="italic")
svg("fig02_unit", 780, 292, b,
    "소자 하나는 입력에 가중치를 곱해 선형으로 더한 뒤 로지스틱 함수를 통과시킨다. 편향은 값이 늘 1인 입력의 가중치다")


# ── 3. 계단 함수 대신 로지스틱 — 기울기가 살아난다 ─────────────────────────
def axes(ox, oy, w, h, xlab, ylab, ymax):
    s = line(ox, oy, ox + w, oy, MUTED, 1.1)
    s += line(ox, oy, ox, oy - h, MUTED, 1.1)
    s += txt(ox + w + 6, oy + 4, xlab, 11, MUTED, anchor="start")
    s += txt(ox - 6, oy - h - 6, ylab, 11, MUTED, anchor="end")
    return s


b = '<defs></defs>'
b += txt(390, 28, "퍼셉트론의 계단을 로지스틱으로 바꾼 이유 — 기울기가 0 이 아니어야 한다", 14, INK, weight=600)

OX, OY, W, H = 70, 210, 260, 130
b += box(36, 46, 320, 232, "#F4F6F4", LINE, 1.2, 10)
b += txt(196, 70, "출력", 12.5, INK, weight=600)
b += axes(OX, OY, W, H, "x", "y", 1.0)
b += line(OX, OY - H, OX + W, OY - H, LINE, 0.9, dash="3 3")
b += txt(OX - 6, OY - H + 4, "1", 10.5, MUTED, anchor="end")
b += txt(OX - 6, OY + 4, "0", 10.5, MUTED, anchor="end")
b += txt(OX + W / 2, OY + 18, "0", 10.5, MUTED)
# 계단
b += path("M %d %d L %d %d L %d %d L %d %d" % (OX, OY, OX + W / 2, OY, OX + W / 2, OY - H, OX + W, OY - H),
          NO, "none", 2.0, dash="6 4")
# 로지스틱
pts = []
for i in range(0, 121):
    xv = -6.0 + 12.0 * i / 120.0
    pts.append("%.1f,%.1f" % (OX + W * (xv + 6) / 12.0, OY - H * sigmoid(xv)))
b += '<polyline points="%s" fill="none" stroke="%s" stroke-width="2.4"/>' % (" ".join(pts), REV)
b += txt(316, 108, "계단", 11.5, NO, anchor="end")
b += txt(316, 126, "로지스틱", 11.5, REV, anchor="end", weight=600)

OX2 = 450
b += box(416, 46, 320, 232, "#F4F6F4", LINE, 1.2, 10)
b += txt(576, 70, "그 기울기", 12.5, INK, weight=600)
b += axes(OX2, OY, W, H, "x", "dy/dx", 0.25)
b += txt(OX2 - 6, OY + 4, "0", 10.5, MUTED, anchor="end")
b += line(OX2, OY - H, OX2 + W, OY - H, LINE, 0.9, dash="3 3")
b += txt(OX2 - 6, OY - H + 4, "0.25", 10.5, MUTED, anchor="end")
b += line(OX2, OY, OX2 + W / 2, OY, NO, 2.0, dash="6 4")
b += line(OX2 + W / 2, OY, OX2 + W, OY, NO, 2.0, dash="6 4")
b += line(OX2 + W / 2, OY, OX2 + W / 2, OY - H + 4, NO, 1.2, dash="2 4")
pts = []
for i in range(0, 121):
    xv = -6.0 + 12.0 * i / 120.0
    s_ = sigmoid(xv)
    pts.append("%.1f,%.1f" % (OX2 + W * (xv + 6) / 12.0, OY - H * (s_ * (1 - s_)) / 0.25))
b += '<polyline points="%s" fill="none" stroke="%s" stroke-width="2.4"/>' % (" ".join(pts), REV)
b += txt(OX2 + W / 2 + 8, 104, "계단은 여기서만 정의되지 않고", 11, NO, anchor="start")
b += txt(OX2 + W / 2 + 8, 120, "나머지 자리에서는 0 이다", 11, NO, anchor="start")
b += txt(OX2 + W / 2 - 10, 150, E("y_j(1 − y_j)", 12), 12, REV, weight=600, anchor="end")

b += txt(390, 300, "기울기가 어디서나 0 이면 오차가 뒤로 흐르지 못한다. 로지스틱의 미분은 출력만으로 "
         + E("y_j(1 − y_j)", 12) + " 로 나와,", 12, INK2)
b += txt(390, 318, "역방향에서 따로 계산할 것이 없다 — 식 (5) 가 짧은 이유다.", 12, INK2)
svg("fig03_sigmoid", 780, 334, b,
    "계단 함수는 기울기가 0이거나 정의되지 않지만 로지스틱은 미분이 y(1-y)로 살아 있다")


# ── 4. 순방향 통과와 허용되는 연결 ─────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("f1", FWD), arrow("f2", NO))
b += txt(410, 28, "순방향 통과 — 아래 층부터 한 층씩, 층 안은 한꺼번에", 14, INK, weight=600)
cols = [(90, 3, "입력층", FWD), (270, 4, "은닉층 1", INK), (450, 3, "은닉층 2", INK), (630, 2, "출력층", REV)]
pos = {}
for ci, (cx, n, lab, col) in enumerate(cols):
    ys_ = [170 + (i - (n - 1) / 2.0) * 46 for i in range(n)]
    pos[ci] = (cx, ys_)
    for y in ys_:
        fill = FWD_SOFT if ci == 0 else (REV_SOFT if ci == 3 else NODE)
        b += circ(cx, y, 16, fill, col, 1.3)
    b += txt(cx, 282, lab, 12.5, col, weight=600)
for ci in range(3):
    cx, ys_ = pos[ci]
    nx, nys = pos[ci + 1]
    for y in ys_:
        for y2 in nys:
            b += line(cx + 16, y, nx - 18, y2, MUTED, 0.85, marker="f1", op="0.55")
b += path("M 90 106 C 200 64 340 64 450 106", FWD, "none", 1.8, dash="6 4", marker="f1")
b += txt(270, 56, "층을 건너뛰는 연결은 된다", 11.5, FWD)

b += box(28, 306, 372, 74, "#F4F6F4", NO, 1.3, 8)
b += txt(214, 332, "금지된 연결 둘", 12.5, NO, weight=600)
b += txt(214, 356, "같은 층 안의 연결 · 위 층에서 아래 층으로 가는 연결", 12, INK2)
b += box(420, 306, 372, 74, "#F4F6F4", LINE, 1.3, 8)
b += txt(606, 332, "그래서 방향이 한쪽이다", 12.5, INK, weight=600)
b += txt(606, 356, "한 번 훑는 것만으로 모든 유닛의 상태가 정해진다", 12, INK2)
b += txt(410, 404, "논문은 입력을 아래, 출력을 위에 두고 그렸다. 여기서는 왼쪽에서 오른쪽으로 옮겨 그렸다.", 11.5, MUTED)
svg("fig04_forward", 820, 420, b,
    "층을 건너뛰는 연결은 허용되지만 같은 층 안의 연결과 위 층에서 아래 층으로 가는 연결은 금지된다")


# ── 5. 역방향 통과 — 네 걸음 (식 4~7) ──────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("b1", REV), arrow("b2", INK2))
b += txt(430, 28, "역방향 통과 — 오차의 기울기를 위에서 아래로 넘긴다", 14, INK, weight=600)

steps = [
    (48, "① 출력에서 시작", "∂E/∂y_j = y_j − d_j", "(4)", "낸 답과 정답의 차이다"),
    (48 + 205, "② 활성 함수를 지난다", "∂E/∂x_j = ∂E/∂y_j · y_j(1 − y_j)", "(5)", "그림 3 의 기울기가 여기 들어간다"),
    (48 + 410, "③ 가중치의 몫을 뗀다", "∂E/∂w_ji = ∂E/∂x_j · y_i", "(6)", "아래 유닛의 출력을 곱하면 끝이다"),
    (48 + 615, "④ 한 층 아래로 넘긴다", "∂E/∂y_i = Σ_j ∂E/∂x_j · w_ji", "(7)", "가중치를 곱해 거꾸로 모은다"),
]
for x, title, eq, num, note in steps:
    b += box(x, 56, 185, 128, "#FFFFFF", REV, 1.4, 8)
    b += txt(x + 92, 80, title, 12.5, REV, weight=600)
    b += txt(x + 92, 116, E(eq, 12.5), 12.5, INK)
    b += txt(x + 176, 80, num, 11, MUTED, anchor="end")
    b += txt(x + 92, 146, note, 11, MUTED)
    b += txt(x + 92, 166, "", 11, MUTED)
for x in [48 + 185, 48 + 390, 48 + 595]:
    b += line(x, 120, x + 18, 120, REV, 1.8, marker="b1")

b += path("M 140 190 C 140 232 700 232 740 232", INK2, "none", 1.6, dash="6 4")
b += path("M 740 232 C 780 232 782 200 760 192", INK2, "none", 1.6, marker="b2")
b += txt(430, 250, "④ 로 얻은 " + E("∂E/∂y_i", 12) + " 가 한 층 아래에서 다시 ① 의 자리에 들어간다 — 층마다 같은 네 걸음을 되풀이한다", 12, INK2)

b += box(48, 272, 800, 74, "#F4F6F4", LINE, 1.2, 8)
b += txt(448, 296, "여기서 곱해지는 것은 모두 그 유닛 옆에 이미 있는 값이다 — " + E("y_j", 12) + ", " + E("y_i", 12) + ", " + E("w_ji", 12) + " 뿐이다.", 12.5, INK, weight=600)
b += txt(448, 320, "그래서 논문은 이 절차를 병렬 하드웨어의 국소 계산으로 구현할 수 있다고 적었다.", 12, INK2)
svg("fig05_backward", 880, 362, b,
    "역방향 통과는 출력의 오차에서 시작해 활성 함수를 지나 가중치의 몫을 떼고 한 층 아래로 넘기는 네 걸음을 되풀이한다")


# ── 6. 두 통과가 만나는 자리 — 무엇을 들고 있어야 하는가 ───────────────────
b = '<defs>%s%s</defs>' % (arrow("t1", FWD), arrow("t2", REV))
b += txt(400, 28, "순방향이 남긴 것을 역방향이 쓴다", 14, INK, weight=600)

b += box(32, 50, 352, 200, "#F4F6F4", LINE, 1.2, 10)
b += txt(208, 74, "순방향 — 아래에서 위로", 12.5, FWD, weight=600)
b += circ(96, 150, 20, FWD_SOFT, FWD, 1.3)
b += txt(96, 155, E("y_i", 13), 13, FWD)
b += line(116, 150, 176, 150, FWD, 1.6, marker="t1")
b += txt(146, 138, E("w_ji", 11), 11, MUTED)
b += circ(200, 150, 22, NODE, INK, 1.5)
b += txt(200, 155, "j", 13, INK, weight=600)
b += line(222, 150, 282, 150, FWD, 1.6, marker="t1")
b += circ(306, 150, 20, FWD_SOFT, FWD, 1.3)
b += txt(306, 155, E("y_j", 13), 13, FWD)
b += txt(208, 208, "유닛 j 의 출력 " + E("y_j", 12) + " 가 정해진다", 12, INK2)
b += txt(208, 228, "이 값을 버리지 않고 들고 있어야 한다", 11.5, MUTED)

b += box(416, 50, 352, 200, "#F4F6F4", LINE, 1.2, 10)
b += txt(592, 74, "역방향 — 위에서 아래로", 12.5, REV, weight=600)
b += circ(690, 150, 27, REV_SOFT, REV, 1.3)
b += txt(690, 155, E("∂E/∂y_j", 10), 10, REV)
b += line(663, 150, 610, 150, REV, 1.6, marker="t2")
b += circ(586, 150, 22, NODE, INK, 1.5)
b += txt(586, 155, "j", 13, INK, weight=600)
b += line(562, 150, 505, 150, REV, 1.6, marker="t2")
b += circ(478, 150, 27, REV_SOFT, REV, 1.3)
b += txt(478, 155, E("∂E/∂y_i", 10), 10, REV)
b += txt(586, 112, "여기서 " + E("y_j(1−y_j)", 11) + " 가 필요하다", 11.5, REV)
b += txt(592, 208, "가중치의 몫 " + E("∂E/∂w_ji", 12) + " 에는 " + E("y_i", 12) + " 가 필요하다", 12, INK2)
b += txt(592, 228, "둘 다 순방향에서 나온 값이다", 11.5, MUTED)

b += box(32, 268, 736, 76, "#FFFFFF", INK, 1.3, 8)
b += txt(400, 294, "그래서 순방향의 출력 상태를 모두 저장해 두어야 역방향을 돌릴 수 있다.", 12.5, INK, weight=600)
b += txt(400, 318, "논문이 순환망(그림 13)에서 '각 유닛의 출력 상태의 이력을 저장해야 한다'고 적은 이유가 이것이다.", 12, INK2)
svg("fig06_two_passes", 800, 360, b,
    "역방향 통과는 순방향에서 나온 출력값을 다시 쓰므로 순방향의 상태를 저장해 두어야 한다")


# ── 7. 언제 가중치를 바꾸는가 (식 8, 9) ────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("w1", INK2), arrow("w2", REV))
b += txt(410, 28, "기울기를 모았다가 한 번에 바꾼다, 그리고 가속 항을 붙인다", 14, INK, weight=600)

b += box(28, 48, 360, 224, "#F4F6F4", LINE, 1.2, 10)
b += txt(208, 72, "한 번 훑기 (sweep) 안에서", 12.5, INK, weight=600)
for i, y in enumerate([104, 134, 164]):
    b += box(56, y - 12, 96, 24, "#FFFFFF", MUTED, 1.0, 4)
    b += txt(104, y + 4, "예 %d" % (i + 1), 11, INK2)
    b += line(152, y, 210, 140, MUTED, 1.0, marker="w1", op="0.7")
b += txt(104, 192, "…", 13, MUTED)
b += box(56, 214 - 12, 96, 24, "#FFFFFF", MUTED, 1.0, 4)
b += txt(104, 218, "예 C", 11, INK2)
b += line(152, 214, 210, 152, MUTED, 1.0, marker="w1", op="0.7")
b += box(212, 116, 68, 56, "#FFFFFF", INK, 1.4, 8)
b += txt(246, 142, "Σ", 18, INK, weight=600)
b += txt(246, 160, "누적", 10.5, MUTED)
b += line(280, 144, 312, 144, REV, 1.8, marker="w2")
b += box(314, 118, 58, 52, REV_SOFT, REV, 1.4, 8)
b += txt(343, 140, "Δw", 13, REV, weight=600)
b += txt(343, 158, "한 번", 10.5, REV)
b += txt(208, 244, "논문이 쓴 방식이다. 예마다 바꾸는 방식도 된다고 적었다.", 11.5, MUTED)

b += box(404, 48, 388, 224, "#F4F6F4", LINE, 1.2, 10)
b += txt(598, 72, "가속 항 α 가 하는 일", 12.5, REV, weight=600)
cx, cy = 598, 168
for rx, ry in [(150, 34), (112, 25), (74, 17), (36, 8)]:
    b += '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s" stroke-width="1"/>' % (cx, cy, rx, ry, LINE)
b += circ(cx, cy, 3.5, INK, INK, 0)
zz = "M 462 118 L 486 152 L 500 122 L 520 154 L 536 126 L 556 156 L 572 132 L 588 160"
b += path(zz, NO, "none", 1.8)
b += txt(470, 104, "α = 0 — 골짜기를 가로질러 튄다", 11, NO, anchor="start")
b += path("M 462 200 C 500 208 540 196 566 184 C 582 178 592 174 598 170", OK, "none", 2.2)
b += txt(470, 218, "α > 0 — 이전 걸음의 방향이 남아 골짜기를 따라 간다", 11, OK, anchor="start")
b += txt(598, 240, "타원은 오차의 등고선이고 안쪽으로 갈수록 낮다 — 가운데 점이 가장 낮은 자리다.", 11.5, MUTED)
b += txt(598, 258, "이 그림은 α 의 뜻을 그린 것이고 논문의 측정 결과가 아니다.", 11.5, MUTED)

b += box(28, 290, 764, 130, "#FFFFFF", INK, 1.3, 8)
b += txt(410, 320, E("Δw = −ε · ∂E/∂w", 14) + "          (8)", 14, INK)
b += txt(410, 350, E("Δw(t) = −ε · ∂E/∂w(t) + α · Δw(t−1)", 14) + "          (9)", 14, INK)
b += txt(410, 380, "t 는 훑기 한 번마다 1 씩 늘어난다. α 는 0 과 1 사이의 값으로, 지금의 기울기와 앞선 기울기들이 "
         "각각 얼마나 들어갈지를 정한다.", 12, INK2)
b += txt(410, 404, "논문의 설정값: 대칭 과제 ε = 0.1, α = 0.9 · 가족 트리 과제 처음 20 훑기 ε = 0.005, α = 0.5, 그 뒤 ε = 0.01, α = 0.9", 11.5, MUTED)
svg("fig07_update", 820, 436, b,
    "기울기를 한 훑기 동안 누적했다가 한 번에 가중치를 바꾸고, 식 9의 가속 항으로 이전 걸음의 방향을 이어 간다")


# ── 8. 논문 그림 1 — 대칭 검출 망 ──────────────────────────────────────────
WL = [14.2, -3.6, 7.2, -7.2, 3.6, -14.2]        # 왼쪽 은닉 유닛으로 가는 가중치
WR = [-14.2, 3.6, -7.1, 7.1, -3.6, 14.2]        # 오른쪽 은닉 유닛으로 가는 가중치
BH, WHO, BO = -1.1, -8.8, 6.4

b = '<defs>%s</defs>' % arrow("s1", INK2)
b += txt(420, 28, "논문 그림 1 — 대칭을 알아내는 망 (입력 6, 은닉 2, 출력 1)", 14, INK, weight=600)

b += circ(420, 96, 25, REV_SOFT, REV, 1.8)
b += txt(420, 101, "6.4", 12, REV, weight=600)
b += txt(420, 58, "출력 유닛", 12, REV, weight=600)

HY = 268
b += path("M 196 242 C 196 130 300 96 394 96", REV, "none", 2.2)
b += path("M 644 242 C 644 130 540 96 446 96", REV, "none", 2.2)
b += txt(182, 180, "−8.8", 11.5, REV, anchor="end")
b += txt(658, 180, "−8.8", 11.5, REV, anchor="start")

IY = [156, 200, 244, 292, 336, 380]
for k, y in enumerate(IY):
    b += circ(420, y, 17, FWD_SOFT, FWD, 1.3)
    b += txt(420, y + 5, "%d" % (k + 1), 11.5, FWD)
    b += line(403, y, 222, HY, INK2, 1.0, op="0.55")
    b += line(437, y, 618, HY, INK2, 1.0, op="0.55")
    b += txt(312, y - 8 if y < HY else y + 18, "%+.1f" % WL[k], 11.5, INK2)
    b += txt(528, y - 8 if y < HY else y + 18, "%+.1f" % WR[k], 11.5, INK2)
b += line(386, HY, 454, HY, MUTED, 1.4, dash="7 5")
b += txt(462, HY + 4, "가운데", 10.5, MUTED, anchor="start")

b += circ(196, HY, 26, NODE, INK, 1.6)
b += txt(196, HY + 5, "−1.1", 11.5, INK)
b += txt(196, HY + 46, "은닉 유닛 L", 12, INK, weight=600)
b += circ(644, HY, 26, NODE, INK, 1.6)
b += txt(644, HY + 5, "−1.1", 11.5, INK)
b += txt(644, HY + 46, "은닉 유닛 R", 12, INK, weight=600)

b += box(28, 420, 784, 110, "#F4F6F4", LINE, 1.2, 8)
b += txt(420, 444, "동그라미 안의 수는 편향, 선 위의 수는 가중치다. 가운데를 기준으로 마주 보는 두 가중치는 "
         "크기가 같고 부호가 반대다.", 12.5, INK, weight=600)
b += txt(420, 466, "한쪽의 세 크기는 3.6 : 7.2 : 14.2 로 1 : 2 : 4 다 — 위쪽 절반이 만들 수 있는 여덟 가지 합이 서로 달라진다.", 12, INK2)
b += txt(420, 488, "출력 유닛의 편향은 +6.4 로 양수다 — 은닉 유닛이 누르지 않으면 켜져 있다. 두 은닉 유닛의 가중치 모양은 같고 부호만 반대다.", 12, INK2)
b += txt(420, 512, "학습 설정: 64 가지 입력을 1,425 번 훑었고 ε = 0.1, α = 0.9, 처음 가중치는 −0.3 과 0.3 사이의 난수다.", 12, MUTED)
svg("fig08_symmetry_net", 840, 548, b,
    "논문 그림 1의 대칭 검출 망. 입력 6개, 은닉 2개, 출력 1개이며 가운데를 기준으로 가중치가 부호 대칭이다")


# ── 9. 왜 되는가 — 네 가지 입력을 넣어 본다 ────────────────────────────────
cases = [
    ([1, 0, 0, 0, 0, 1], "대칭"),
    ([1, 1, 0, 0, 1, 1], "대칭"),
    ([1, 0, 0, 0, 0, 0], "비대칭"),
    ([1, 1, 0, 0, 0, 0], "비대칭"),
]
rows = []
for pat, kind in cases:
    xl = sum(w * v for w, v in zip(WL, pat)) + BH
    xr = sum(w * v for w, v in zip(WR, pat)) + BH
    yl, yr = sigmoid(xl), sigmoid(xr)
    xo = WHO * yl + WHO * yr + BO
    yo = sigmoid(xo)
    rows.append((pat, kind, xl, yl, xr, yr, yo))
    print("    %s  %s  x_L=%+7.2f y_L=%.4f  x_R=%+7.2f y_R=%.4f  y_out=%.4f"
          % ("".join(str(v) for v in pat), kind, xl, yl, xr, yr, yo))

b = '<defs></defs>'
b += txt(410, 28, "그림 8 의 가중치에 입력 넷을 넣어 본 것", 14, INK, weight=600)
hx = [90, 300, 420, 540, 690]
b += txt(hx[0], 62, "입력 패턴", 12, INK, weight=600)
b += txt(hx[1], 62, "은닉 L 의 총 입력", 12, INK, weight=600)
b += txt(hx[2], 62, "은닉 L 출력", 12, INK, weight=600)
b += txt(hx[3], 62, "은닉 R 출력", 12, INK, weight=600)
b += txt(hx[4], 62, "출력 유닛", 12, INK, weight=600)
b += line(28, 74, 792, 74, LINE, 1.2)
for r, (pat, kind, xl, yl, xr, yr, yo) in enumerate(rows):
    y = 108 + r * 56
    col = OK if kind == "대칭" else NO
    for k, v in enumerate(pat):
        px = hx[0] - 66 + k * 22
        b += box(px, y - 11, 18, 22, "#FFFFFF" if v == 0 else INK, INK, 1.0, 3)
    b += line(hx[0] - 66 + 3 * 22 - 2, y - 18, hx[0] - 66 + 3 * 22 - 2, y + 18, MUTED, 1.0, dash="3 3")
    b += txt(hx[0] + 86, y + 4, kind, 11.5, col, weight=600)
    b += txt(hx[1], y + 4, "%+.1f" % xl, 12, INK2)
    b += txt(hx[2], y + 4, "%.3f" % yl, 12, INK2)
    b += txt(hx[3], y + 4, "%.3f" % yr, 12, INK2)
    b += box(hx[4] - 40, y - 15, 80, 30, "#FFFFFF", col, 1.4, 5)
    b += txt(hx[4], y + 5, "%.3f" % yo, 12.5, col, weight=600)
    if r < 3:
        b += line(28, y + 28, 792, y + 28, LINE, 0.8)

b += box(28, 336, 764, 92, "#F4F6F4", LINE, 1.2, 8)
b += txt(410, 360, "대칭이면 위쪽 절반과 아래쪽 절반의 합이 정확히 상쇄되어 총 입력이 편향 −1.1 만 남는다. "
         "두 은닉 유닛이 함께 낮아지고,", 12.5, INK, weight=600)
b += txt(410, 382, "편향 +6.4 를 가진 출력 유닛이 켜진다. 비대칭이면 두 은닉 유닛 중 한쪽이 켜져 −8.8 로 출력을 누른다.", 12.5, INK, weight=600)
b += txt(410, 408, "표의 수는 논문에 없다 — 그림 1 의 가중치를 식 (1)(2) 에 넣어 이 저장소의 make_figures.py 가 계산한 것이다.", 11.5, MUTED)
svg("fig09_symmetry_why", 820, 444, b,
    "대칭 입력에서는 두 은닉 유닛의 총 입력이 상쇄되어 출력이 켜지고 비대칭 입력에서는 한쪽 은닉 유닛이 켜져 출력을 누른다")


# ── 10. 가족 트리 과제 ─────────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("k1", REV)
b += txt(430, 28, "논문 그림 2 — 가족 트리를 세 낱말짜리 사실로 바꾼다", 14, INK, weight=600)


def person(x, y, name, hl=None):
    w = 8.2 * len(name) + 18
    s = box(x - w / 2.0, y - 15, w, 30, REV_SOFT if hl == "a" else (FWD_SOFT if hl == "q" else "#FFFFFF"),
            REV if hl == "a" else (FWD if hl == "q" else INK2), 1.6 if hl else 1.1, 6)
    s += txt(x, y + 5, name, 12, REV if hl == "a" else (FWD if hl == "q" else INK))
    return s


b += person(150, 78, "Christopher") + txt(212, 83, "=", 13, MUTED) + person(276, 78, "Penelope")
b += person(566, 78, "Andrew") + txt(618, 83, "=", 13, MUTED) + person(676, 78, "Christine")
b += person(96, 156, "Margaret", "a") + txt(150, 161, "=", 13, MUTED) + person(196, 156, "Arthur")
b += person(384, 156, "Victoria") + txt(436, 161, "=", 13, MUTED) + person(480, 156, "James")
b += person(660, 156, "Jennifer", "a") + txt(714, 161, "=", 13, MUTED) + person(762, 156, "Charles")
b += person(404, 234, "Colin", "q") + person(492, 234, "Charlotte")

b += line(213, 93, 213, 118, MUTED, 1.2)
b += line(196, 118, 384, 118, MUTED, 1.2)
b += line(196, 118, 196, 141, MUTED, 1.2)
b += line(384, 118, 384, 141, MUTED, 1.2)
b += line(619, 93, 619, 118, MUTED, 1.2)
b += line(480, 118, 660, 118, MUTED, 1.2)
b += line(480, 118, 480, 141, MUTED, 1.2)
b += line(660, 118, 660, 141, MUTED, 1.2)
b += line(437, 171, 437, 196, MUTED, 1.2)
b += line(404, 196, 492, 196, MUTED, 1.2)
b += line(404, 196, 404, 219, MUTED, 1.2)
b += line(492, 196, 492, 219, MUTED, 1.2)

b += box(28, 272, 380, 86, "#F4F6F4", LINE, 1.2, 8)
b += txt(218, 296, "사실 하나 = ⟨사람 1⟩ ⟨관계⟩ ⟨사람 2⟩", 12.5, INK, weight=600)
b += txt(218, 318, "앞의 둘을 입력으로 넣고 셋째를 맞히게 한다", 12, INK2)
b += txt(218, 340, "관계는 열두 가지: 아버지 · 어머니 · 남편 · 아내 · 아들 · 딸 ·", 11.5, MUTED)
b += txt(218, 356, "삼촌 · 고모 · 형제 · 자매 · 조카(남) · 조카(여)", 11.5, MUTED)

b += box(424, 272, 412, 86, "#FFFFFF", REV, 1.4, 8)
b += txt(630, 296, "⟨Colin⟩ ⟨has-aunt⟩ ⟨ ? ⟩", 13.5, INK, weight=600)
b += txt(630, 320, "정답이 둘이다 — Margaret 과 Jennifer", 12.5, REV, weight=600)
b += txt(630, 344, "Margaret 은 어머니 쪽 삼촌의 아내, Jennifer 는 아버지의 자매다", 11.5, MUTED)

b += txt(430, 384, "여기 그린 것은 영국 쪽 트리 열두 명이다. 논문은 이름만 다르고 모양이 똑같은 이탈리아 쪽 트리 열두 명을 함께 쓴다 — 사람은 모두 24 명이다.", 11.5, MUTED)
svg("fig10_family_task", 860, 400, b,
    "가족 트리를 사람1 관계 사람2 세 낱말짜리 사실로 바꾸고 앞의 둘로 셋째를 맞히게 한다. Colin의 고모는 Margaret과 Jennifer 둘이다")


# ── 11. 가족 트리 망의 다섯 층 ─────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("n1", FWD)
b += txt(430, 28, "논문 그림 3 — 다섯 층, 가운데가 좁다", 14, INK, weight=600)

b += box(40, 70, 118, 78, FWD_SOFT, FWD, 1.4, 8)
b += txt(99, 100, "사람 1", 12.5, FWD, weight=600)
b += txt(99, 122, "입력 24", 12, INK)
b += box(40, 168, 118, 78, FWD_SOFT, FWD, 1.4, 8)
b += txt(99, 198, "관계", 12.5, FWD, weight=600)
b += txt(99, 220, "입력 12", 12, INK)
b += txt(99, 268, "사람마다 · 관계마다", 11, MUTED)
b += txt(99, 284, "유닛 하나씩 (국소 표현)", 11, MUTED)

b += box(206, 70, 104, 78, NODE, INK, 1.4, 8)
b += txt(258, 100, "6 유닛", 12.5, INK, weight=600)
b += txt(258, 122, "사람의 표현", 11.5, INK2)
b += box(206, 168, 104, 78, NODE, INK, 1.4, 8)
b += txt(258, 198, "6 유닛", 12.5, INK, weight=600)
b += txt(258, 220, "관계의 표현", 11.5, INK2)
b += txt(258, 268, "여기서 분산 표현이 만들어진다", 11, REV, weight=600)
b += txt(258, 284, "그림 12 가 이 여섯 유닛의 가중치다", 11, MUTED)

b += box(358, 108, 104, 100, NODE, INK, 1.4, 8)
b += txt(410, 150, "12 유닛", 12.5, INK, weight=600)
b += txt(410, 172, "가운데 층", 11.5, INK2)
b += box(510, 118, 104, 80, NODE, INK, 1.4, 8)
b += txt(562, 152, "6 유닛", 12.5, INK, weight=600)
b += txt(562, 174, "끝에서 둘째", 11.5, INK2)
b += box(662, 90, 118, 136, REV_SOFT, REV, 1.4, 8)
b += txt(721, 146, "출력 24", 12.5, REV, weight=600)
b += txt(721, 168, "사람 2", 11.5, REV)

for y0, y1 in [(109, 109), (207, 207)]:
    b += line(158, y0, 200, y1, FWD, 1.6, marker="n1")
b += line(310, 109, 352, 140, FWD, 1.6, marker="n1")
b += line(310, 207, 352, 176, FWD, 1.6, marker="n1")
b += line(462, 158, 504, 158, FWD, 1.6, marker="n1")
b += line(614, 158, 656, 158, FWD, 1.6, marker="n1")

b += txt(179, 60, "따로", 11, MUTED)
b += txt(331, 60, "합쳐진다", 11, MUTED)

b += box(28, 306, 804, 92, "#F4F6F4", LINE, 1.2, 8)
b += txt(430, 330, "입력과 출력은 사람 한 명에 유닛 하나를 쓴다 — 이름 사이에 아무 관계도 심어 두지 않았다는 뜻이다.", 12.5, INK, weight=600)
b += txt(430, 352, "104 개 사실 중 100 개로 학습했고 남은 4 개를 맞혔다. 1,500 번 훑었다.", 12, INK2)
b += txt(430, 376, "가중치 감쇠: 가중치를 바꿀 때마다 모든 가중치를 0.2% 줄였다. 출력이 0.8 위 · 0.2 아래면 오차를 0 으로 쳤다.", 11.5, MUTED)
svg("fig11_family_net", 860, 414, b,
    "가족 트리 망은 다섯 층이고 사람 24개와 관계 12개의 입력이 각각 6유닛으로 줄어든 뒤 12, 6을 거쳐 출력 24로 간다")


# ── 12. 은닉 유닛이 스스로 만든 특징 ───────────────────────────────────────
b = '<defs></defs>'
b += txt(410, 28, "논문 그림 4 가 보여 준 것 — 아무도 알려 주지 않은 특징이 생겼다", 14, INK, weight=600)
b += txt(410, 52, "2 층의 여섯 유닛이 24 명에게 준 가중치를 보면 세 유닛의 뜻이 읽힌다", 12, MUTED)

units = [
    ("유닛 1", "국적을 나눈다", ["영국 12명", "이탈리아 12명"], [1, -1]),
    ("유닛 2", "세대를 나눈다", ["1세대", "2세대", "3세대"], [1, 0, -1]),
    ("유닛 6", "집안의 어느 갈래인지를 나눈다", ["왼쪽 갈래", "오른쪽 갈래"], [1, -1]),
]
for i, (name, mean, labs, signs) in enumerate(units):
    x = 34 + i * 262
    b += box(x, 76, 244, 168, "#FFFFFF", INK, 1.3, 8)
    b += txt(x + 122, 102, name, 13, INK, weight=600)
    b += txt(x + 122, 124, mean, 12, REV, weight=600)
    for k, (lab, sg) in enumerate(zip(labs, signs)):
        y = 156 + k * 30
        b += txt(x + 92, y + 4, lab, 11.5, INK2, anchor="end")
        for m in range(5):
            sz = 16 if sg != 0 else 5
            fill = "#FFFFFF" if sg > 0 else (INK if sg < 0 else MUTED)
            b += box(x + 108 + m * 22, y - sz / 2.0, sz, sz, fill, INK2, 1.0, 2)
b += txt(410, 262, "흰 칸은 키우는 가중치, 검은 칸은 누르는 가중치다 (논문은 칸의 넓이로 크기를 나타냈다).", 11.5, MUTED)

b += box(28, 284, 764, 96, "#F4F6F4", LINE, 1.2, 8)
b += txt(410, 308, "국적 · 세대 · 갈래는 입력에도 출력에도 적혀 있지 않다. 사람마다 유닛 하나씩이었을 뿐이다.", 12.5, INK, weight=600)
b += txt(410, 332, "그런데도 이런 축이 생겼고, 유닛 1 을 빼면 영국 사람과 그에 대응하는 이탈리아 사람의 표현이 서로 닮았다.", 12, INK2)
b += txt(410, 356, "그래서 한쪽 트리에서 배운 것이 다른 쪽으로 넘어간다 — 논문이 제목에 'representations' 를 넣은 자리다.", 12, REV, weight=600)
svg("fig12_hidden_features", 820, 396, b,
    "2층의 여섯 유닛 중 하나는 국적을, 하나는 세대를, 하나는 집안의 갈래를 나누게 되었다. 입력에는 없던 축이다")


# ── 13. 순환망을 층으로 펼친다 ─────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("r1", INK2)
b += txt(410, 28, "논문 그림 5 — 되먹임이 있는 망은 층으로 펼치면 같은 절차가 돈다", 14, INK, weight=600)

b += box(28, 50, 300, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(178, 74, "되먹임이 있는 망", 12.5, INK, weight=600)
b += circ(96, 180, 20, NODE, INK, 1.4)
b += circ(178, 180, 20, NODE, INK, 1.4)
b += circ(260, 180, 20, NODE, INK, 1.4)
b += path("M 112 168 C 132 148 142 148 162 168", INK2, "none", 1.5, marker="r1")
b += path("M 162 192 C 142 212 132 212 112 192", INK2, "none", 1.5, marker="r1")
b += path("M 194 168 C 214 148 224 148 244 168", INK2, "none", 1.5, marker="r1")
b += path("M 244 192 C 224 212 214 212 194 192", INK2, "none", 1.5, marker="r1")
b += txt(137, 142, E("w_2", 11.5), 11.5, INK2)
b += txt(137, 228, E("w_1", 11.5), 11.5, INK2)
b += txt(219, 142, E("w_4", 11.5), 11.5, INK2)
b += txt(219, 228, E("w_3", 11.5), 11.5, INK2)
b += txt(178, 268, "시간이 흐르며 같은 가중치가", 11.5, MUTED)
b += txt(178, 286, "몇 번이고 다시 쓰인다", 11.5, MUTED)

b += box(348, 50, 444, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(570, 74, "세 번 돌린 것과 같은 층 구조", 12.5, INK, weight=600)
COLX = [430, 530, 630, 730]
ROWY = [252, 200, 148, 96]
for ri, y in enumerate(ROWY):
    for ci, x in enumerate(COLX[:3]):
        b += circ(x, y, 15, NODE, INK, 1.2)
    b += circ(COLX[3], y, 15, NODE, INK, 1.2)
for ri in range(3):
    y0, y1 = ROWY[ri], ROWY[ri + 1]
    for ci in range(3):
        b += line(COLX[ci] + 12, y0 - 6, COLX[ci + 1] - 12, y1 + 6, INK2, 1.0, marker="r1", op="0.7")
        b += line(COLX[ci + 1] - 12, y0 - 6, COLX[ci] + 12, y1 + 6, INK2, 1.0, marker="r1", op="0.7")
    for ci, lab in enumerate(["w_1", "w_2", "w_3", "w_4"]):
        b += txt(COLX[ci] + 12, (y0 + y1) / 2.0 + 4, E(lab, 10.5), 10.5, REV)
b += txt(570, 288, "한 시간 걸음이 한 층이 된다", 11.5, MUTED)

b += box(28, 318, 764, 108, "#FFFFFF", INK, 1.3, 8)
b += txt(410, 344, "펼쳐 놓으면 층마다 같은 이름의 가중치가 다시 나타난다. 두 가지를 맞춰 주어야 원래 망과 같아진다.", 12.5, INK, weight=600)
b += txt(410, 370, "하나. 각 유닛의 출력 상태를 시간마다 저장해 둔다 — 역방향에 그 값이 필요하다 (그림 6).", 12, INK2)
b += txt(410, 392, "둘. 같은 이름의 가중치들이 받은 " + E("∂E/∂w", 12) + " 를 평균 내고, 그 평균에 비례해 묶음 전체를 함께 바꾼다.", 12, INK2)
b += txt(410, 414, "이 두 가지를 지키면 되먹임 있는 망에도 같은 절차가 그대로 적용된다.", 12, REV, weight=600)
svg("fig13_recurrent", 820, 442, b,
    "되먹임이 있는 망은 시간 걸음마다 한 층으로 펼치면 층 구조와 같아지고 같은 이름의 가중치는 기울기를 평균 내어 함께 바꾼다")


# ── 14. 논문이 스스로 적은 한계 — 국소 최소 ────────────────────────────────
b = '<defs>%s</defs>' % arrow("m1", NO)
b += txt(400, 28, "논문이 스스로 적은 가장 뚜렷한 한계 — 오차면에 국소 최소가 있을 수 있다", 14, INK, weight=600)

b += box(28, 50, 356, 212, "#F4F6F4", LINE, 1.2, 10)
b += txt(206, 74, "연결이 과제에 딱 맞을 때", 12.5, NO, weight=600)
b += path("M 70 130 C 110 118 118 186 156 186 C 186 186 186 122 216 122 C 256 122 268 214 316 214 C 336 214 346 206 352 200",
          INK2, "none", 2.0)
b += circ(156, 186, 5, NO, NO, 0)
b += txt(156, 210, "여기서 멈춘다", 11, NO)
b += circ(316, 214, 5, OK, OK, 0)
b += txt(316, 238, "가장 낮은 자리", 11, OK)
b += txt(206, 252, "내려가기만 해서는 가운데 둔덕을 넘지 못한다", 11.5, MUTED)

b += box(404, 50, 388, 212, "#F4F6F4", LINE, 1.2, 10)
b += txt(598, 74, "연결을 몇 개 더 두면", 12.5, OK, weight=600)
b += '<ellipse cx="598" cy="166" rx="150" ry="74" fill="none" stroke="%s" stroke-width="1.1"/>' % LINE
b += path("M 598 96 L 598 200", MUTED, "none", 14.0, op="0.35")
b += txt(598, 92, "둔덕", 11, MUTED)
b += circ(478, 178, 5, NO, NO, 0)
b += txt(470, 200, "지금 자리", 11, NO, anchor="middle")
b += circ(718, 178, 5, OK, OK, 0)
b += txt(722, 200, "가장 낮은 자리", 11, OK)
b += path("M 484 176 C 520 176 560 176 590 172", NO, "none", 1.8, dash="5 4", marker="m1")
b += path("M 484 172 C 520 128 560 118 598 118 C 640 118 690 140 712 172", OK, "none", 2.2)
b += txt(598, 236, "차원이 늘면 둔덕을 돌아가는 길이 생긴다", 11.5, MUTED)

b += box(28, 282, 764, 112, "#FFFFFF", INK, 1.3, 8)
b += txt(400, 306, "논문의 말: 오차면에 국소 최소가 있을 수 있어 기울기 하강이 전역 최소를 찾는다는 보장이 없다.", 12.5, INK, weight=600)
b += txt(400, 330, "이어서 적기를, 여러 과제에서 겪어 보니 나쁜 국소 최소에 갇히는 일은 드물었고, 갇힌 것은 "
         "과제를 수행할 만큼만 연결이 있는 망뿐이었다.", 12, INK2)
b += txt(400, 354, "연결을 몇 개 더 두면 가중치 공간에 차원이 늘고, 그 차원이 낮은 차원에서 벽이던 곳을 돌아가는 길이 된다.", 12, INK2)
b += txt(400, 380, "이 문단에는 숫자가 붙어 있지 않다 — 얼마나 드물었는지, 몇 개를 더 두었는지는 논문에 적혀 있지 않다.", 11.5, NO, weight=600)
svg("fig14_local_minima", 820, 410, b,
    "논문은 오차면의 국소 최소를 한계로 적었고 연결을 더 두면 차원이 늘어 우회로가 생긴다고 서술했다. 수치는 붙어 있지 않다")

print("끝났다.")
