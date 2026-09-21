# -*- coding: utf-8 -*-
"""LeNet 노트(Proceedings of the IEEE 1998)의 그림 열다섯을 만든다.

색과 글꼴은 퍼셉트론 · 역전파 · DDPM · DBN 노트의 그림과 맞췄다 — 저장소의 노트들이
한 벌로 읽히게 하려는 것이다. 그림을 고치려면 이 파일을 고쳐 다시 돌린다.
바깥 데이터를 읽지 않으므로 어디서나 돈다.

  python make_figures.py

그림 4 의 파라미터 수, 그림 6 의 누름 함수 값, 그림 7 의 표 I 연결 수, 그림 5 의 층별
합계는 이 파일이 직접 계산한다. 계산한 값은 돌릴 때 화면에도 찍는다 — 노트 본문에 적은
수와 맞는지 눈으로 보려는 것이다.
"""
import io, os, math

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"   # 그림 상자 배경
NODE      = "#F6F7F5"   # 노드 안쪽
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 구조로 정해 놓은 것
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 학습으로 바뀌는 것
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


def txt(x, y, t, size=12, fill=None, anchor="middle", weight=None, style=None, mono=False):
    a = 'x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s"' % (x, y, size, fill or INK, anchor)
    if weight:
        a += ' font-weight="%s"' % weight
    if style:
        a += ' font-style="%s"' % style
    if mono:
        a += ' font-family="Consolas, DejaVu Sans Mono, monospace"'
    return "<text %s>%s</text>" % (a, t)


def box(x, y, w, h, fill=None, stroke=None, sw=1.2, rx=6, dash=None, op=None):
    a = ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-width="%s"'
         % (x, y, w, h, rx, fill or NODE, stroke or INK, sw))
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if op:
        a += ' opacity="%s"' % op
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


def grid(x, y, cell, cols, rows, stroke=None, sw=0.5, op=None):
    """격자 하나. 픽셀판과 특징 지도를 그리는 데 쓴다."""
    s = ""
    for c in range(cols + 1):
        s += line(x + c * cell, y, x + c * cell, y + rows * cell, stroke or LINE, sw, op=op)
    for r in range(rows + 1):
        s += line(x, y + r * cell, x + cols * cell, y + r * cell, stroke or LINE, sw, op=op)
    return s


def squash(a, A=1.7159, S=2.0 / 3.0):
    """논문 부록 A 의 누름 함수. 그림 6 의 숫자 예시를 여기서 낸다."""
    return A * math.tanh(S * a)


def bar_h(x, y, h, val, vmax, color, soft, label, unit="", size=11.5, wide=300):
    """가로 막대 하나. 그림 10 · 11 · 12 가 쓴다. h 는 막대 높이, wide 는 vmax 일 때의 길이."""
    L = max(2.0, wide * (float(val) / vmax))
    s = txt(x - 8, y + h * 0.72, label, size, INK2, anchor="end")
    s += box(x, y, L, h, soft, color, 1.0, 3)
    s += txt(x + L + 7, y + h * 0.72, ("%s%s" % (val, unit)), size, INK2, anchor="start")
    return s


print("그림을 만든다 ->", OUT)

# ── 노트 본문과 맞춰 볼 수 있게, 층별 수치를 여기서 한 번 센다 ─────────────
LAYERS = [
    # 이름, 설명, 특징 지도 수, 크기, 학습되는 값, 연결
    ("C1", "합성곱 5x5",      6,  28, 156,     122304),
    ("S2", "부분 표본 2x2",   6,  14, 12,      5880),
    ("C3", "합성곱 5x5 (표I)", 16, 10, 1516,    151600),
    ("S4", "부분 표본 2x2",   16, 5,  32,      2000),
    ("C5", "합성곱 5x5",      120, 1, 48120,   48120),
    ("F6", "완전연결",        84, 0,  10164,   10164),
]
PARAM_SUM = sum(l[4] for l in LAYERS)
CONN_SUM = sum(l[5] for l in LAYERS)
RBF_CONN = 84 * 10
print("  학습되는 값 합계 %d · 연결 합계 %d · RBF 연결 %d · 둘을 더하면 %d"
      % (PARAM_SUM, CONN_SUM, RBF_CONN, CONN_SUM + RBF_CONN))


# ── 1. 완전연결이 남긴 빈칸 ────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("a1", FWD), arrow("a2", NO))
b += txt(430, 28, "완전연결 망이 이미지 앞에서 막히는 자리 셋", 14.5, INK, weight=600)

# (가) 크기
b += box(24, 46, 266, 262, "#F4F6F4", LINE, 1.2, 10)
b += txt(157, 70, "(가) 파라미터가 먼저 터진다", 12.5, NO, weight=600)
b += grid(60, 86, 6, 12, 12, LINE, 0.5)
b += txt(96, 168, "28 x 28", 11, MUTED)
for i, yy in enumerate([100, 124, 148]):
    b += circ(212, yy, 9, FWD_SOFT, FWD, 1.0)
b += txt(212, 176, "은닉 100", 11, MUTED)
for yy in (100, 124, 148):
    b += line(132, 120, 202, yy, MUTED, 0.6, op="0.5")
FC1 = 784 * 100
b += box(48, 190, 218, 58, "#FFFFFF", NO, 1.2, 6)
b += txt(157, 212, "784 x 100 = %s 개" % format(FC1, ","), 13, NO, weight=600)
b += txt(157, 232, "첫 층 하나에서 가중치가 이만큼", 11, INK2)
b += txt(157, 272, "파라미터가 늘면 용량이 늘고,", 11.5, INK2)
b += txt(157, 290, "용량이 늘면 더 큰 학습 집합이 든다", 11.5, INK2)

# (나) 위상
b += box(300, 46, 266, 262, "#F4F6F4", LINE, 1.2, 10)
b += txt(433, 70, "(나) 입력의 위상을 버린다", 12.5, NO, weight=600)
b += grid(336, 88, 9, 8, 8, LINE, 0.6)
on = [(2, 1), (3, 1), (4, 1), (4, 2), (3, 3), (2, 4), (2, 5), (3, 5), (4, 5)]
for (cx, cy) in on:
    b += box(336 + cx * 9, 88 + cy * 9, 9, 9, INK, INK, 0, 0)
b += txt(376, 178, "원래 배치", 11, MUTED)
b += txt(433, 130, "→", 15, MUTED)
b += grid(456, 88, 9, 8, 8, LINE, 0.6)
sh = [(0, 0), (5, 1), (2, 3), (7, 2), (1, 6), (6, 5), (3, 7), (7, 7), (4, 4)]
for (cx, cy) in sh:
    b += box(456 + cx * 9, 88 + cy * 9, 9, 9, INK, INK, 0, 0)
b += txt(492, 178, "픽셀을 고정 순열로 섞은 것", 10.5, MUTED)
b += box(322, 192, 222, 56, "#FFFFFF", NO, 1.2, 6)
b += txt(433, 214, "완전연결에는 둘이 같은 문제다", 12.5, NO, weight=600)
b += txt(433, 234, "학습 결과가 달라지지 않는다", 11, INK2)
b += txt(433, 272, "이미지는 가까운 픽셀끼리 상관이 센데,", 11.5, INK2)
b += txt(433, 290, "그 정보를 쓸 수 없는 자리에서 시작한다", 11.5, INK2)

# (다) 불변성
b += box(576, 46, 266, 262, "#F4F6F4", LINE, 1.2, 10)
b += txt(709, 70, "(다) 옮기면 다른 입력이 된다", 12.5, NO, weight=600)
b += grid(612, 88, 9, 8, 8, LINE, 0.6)
for (cx, cy) in on:
    b += box(612 + cx * 9, 88 + cy * 9, 9, 9, INK, INK, 0, 0)
b += grid(732, 88, 9, 8, 8, LINE, 0.6)
for (cx, cy) in on:
    b += box(732 + (cx + 2) * 9, 88 + cy * 9, 9, 9, REV, REV, 0, 0)
b += txt(652, 178, "원본", 11, MUTED)
b += txt(772, 178, "오른쪽으로 2 픽셀", 10.5, REV)
b += box(598, 192, 222, 56, "#FFFFFF", NO, 1.2, 6)
b += txt(709, 214, "입력 벡터가 통째로 달라진다", 12.5, NO, weight=600)
b += txt(709, 234, "자리마다 가중치 무늬를 따로 배워야 한다", 10.5, INK2)
b += txt(709, 272, "손글씨는 낱말 단위로 정규화되는 일이 많아", 11, INK2)
b += txt(709, 290, "낱글자의 크기 · 기울기 · 자리가 흔들린다", 11, INK2)

b += box(28, 320, 814, 86, "#FFFFFF", INK, 1.3, 8)
b += txt(435, 346, "이 논문의 답은 기울기를 더 잘 흘리는 것이 아니라, 가중치에 제약을 걸어 배울 것을 줄이는 것이다.",
         13, INK, weight=600)
b += txt(435, 370, "국소 수용장으로 (나)를, 가중치 공유로 (가)와 (다)를, 부분 표본 뽑기로 남은 자리 흔들림을 다룬다.", 12, INK2)
b += txt(435, 394, "LeNet-5 의 자유 파라미터는 %s 개다 — 위 (가) 의 한 층짜리 %s 개보다 적다."
         % (format(PARAM_SUM, ","), format(FC1, ",")), 12, FWD, weight=600)
svg("fig01_gap", 870, 420, b,
    "완전연결 망이 이미지 앞에서 막히는 자리 셋 — 파라미터 폭발, 위상 무시, 불변성 없음")


# ── 2. 세 가지 생각 ───────────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("b1", FWD)
b += txt(430, 28, "합성곱 망을 이루는 생각 셋 — 논문 II-A", 14.5, INK, weight=600)

# 국소 수용장
b += box(24, 46, 266, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(157, 70, "하나. 국소 수용장", 13, FWD, weight=600)
b += grid(70, 86, 10, 10, 10, LINE, 0.6)
b += box(70 + 2 * 10, 86 + 2 * 10, 50, 50, "none", FWD, 2.0, 2)
b += line(170, 111, 214, 111, FWD, 1.2, marker="b1")
b += circ(228, 111, 11, FWD_SOFT, FWD, 1.2)
b += txt(157, 206, "유닛 하나가 앞 층의 5 x 5 = 25 개만 본다", 11.5, INK2)
b += txt(157, 226, "모서리 · 끝점 · 모퉁이 같은 기초 특징이", 11.5, INK2)
b += txt(157, 244, "국소 연결에서 나온다", 11.5, INK2)
b += txt(157, 272, "근거: Hubel 과 Wiesel 의 고양이 시각계", 11, MUTED)

# 가중치 공유
b += box(300, 46, 266, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(433, 70, "둘. 가중치 공유", 13, REV, weight=600)
for k, xx in enumerate([340, 390, 440]):
    b += box(xx, 92, 40, 40, REV_SOFT, REV, 1.2, 3)
    b += txt(xx + 20, 117, "w", 13, REV, weight=600, style="italic")
b += txt(433, 150, "자리가 달라도 값이 같은 가중치 한 벌", 11, MUTED)
b += box(340, 164, 186, 46, "#FFFFFF", REV, 1.2, 6)
b += txt(433, 184, "유닛 784 개 · 학습되는 값 26 개", 12, REV, weight=600)
b += txt(433, 202, "(5 x 5 = 25 에 바이어스 1)", 10.5, INK2)
b += txt(433, 230, "같은 특징을 모든 자리에서 찾고,", 11.5, INK2)
b += txt(433, 248, "자유 파라미터가 줄어", 11.5, INK2)
b += txt(433, 266, "학습 오차와 시험 오차의 간격이 준다", 11.5, INK2)

# 부분 표본
b += box(576, 46, 266, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(709, 70, "셋. 부분 표본 뽑기", 13, OK, weight=600)
b += grid(630, 90, 11, 8, 4, LINE, 0.6)
for c in range(0, 8, 2):
    b += box(630 + c * 11, 90, 22, 22, "none", OK, 1.4, 2)
    b += box(630 + c * 11, 112, 22, 22, "none", OK, 1.4, 2)
b += line(718, 146, 718, 166, OK, 1.2, marker="b1")
b += grid(652, 170, 11, 4, 2, LINE, 0.6)
b += txt(709, 212, "2 x 2 를 한 칸으로 — 해상도가 반이 된다", 11.5, INK2)
b += txt(709, 234, "특징이 한 번 잡히면 정확한 자리는", 11.5, INK2)
b += txt(709, 252, "덜 중요하고, 오히려 해로울 수 있다", 11.5, INK2)
b += txt(709, 278, "논문의 예시: 왼쪽 위 가로획 끝점 + 오른쪽 위", 10.5, MUTED)

b += box(28, 308, 814, 74, "#FFFFFF", INK, 1.3, 8)
b += txt(435, 332, "셋을 번갈아 쌓으면 「두 겹 피라미드」가 된다 — 층마다 해상도는 내려가고 특징 지도 수는 는다.",
         12.5, INK, weight=600)
b += txt(435, 356, "LeNet-5 에서 28x28 여섯 장 → 14x14 여섯 장 → 10x10 열여섯 장 → 5x5 열여섯 장 으로 간다.", 12, INK2)
b += txt(435, 374, "모퉁이 + 아래 세로획 끝점 이면 그 입력은 7 이다. 셋이 정확히 어디였는지는 필요 없다.", 11, MUTED)
svg("fig02_three_ideas", 870, 396, b,
    "국소 수용장 · 가중치 공유 · 부분 표본 뽑기 셋과 각각의 작은 예시")


# ── 3. 수용장과 겹침 ──────────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("c1", FWD), arrow("c2", REV))
b += txt(420, 28, "수용장 5 x 5 와 이웃한 두 유닛의 겹침 — 32 에서 28 이 나오는 셈", 14.5, INK, weight=600)

CELL = 11
GX, GY = 40, 60
b += grid(GX, GY, CELL, 32, 20, LINE, 0.45)
b += txt(GX + 16 * CELL, GY - 10, "입력 32 x 32 (세로는 20 행까지만 그렸다)", 11, MUTED)
# 두 수용장
b += box(GX + 3 * CELL, GY + 4 * CELL, 5 * CELL, 5 * CELL, "none", FWD, 2.2, 2)
b += box(GX + 4 * CELL, GY + 4 * CELL, 5 * CELL, 5 * CELL, "none", REV, 2.2, 2, dash="4 3")
# 겹치는 4 열
for c in range(4, 8):
    b += box(GX + c * CELL, GY + 4 * CELL, CELL, 5 * CELL, OK, "none", 0, 0, op="0.22")
b += txt(GX + 6 * CELL, GY + 10.6 * CELL, "겹치는 4 열", 11, OK, weight=600)
b += line(GX + 3 * CELL, GY + 3 * CELL - 6, GX + 8 * CELL, GY + 3 * CELL - 6, FWD, 1.2)
b += txt(GX + 5.5 * CELL, GY + 3 * CELL - 12, "5", 11, FWD, weight=600)

b += line(GX + 8.4 * CELL, GY + 6.5 * CELL, GX + 13 * CELL, GY + 6.5 * CELL, INK2, 1.2, marker="c1")
OX = GX + 14 * CELL
b += grid(OX, GY + 3 * CELL, CELL, 14, 8, LINE, 0.45)
b += box(OX + 3 * CELL, GY + 6 * CELL, CELL, CELL, FWD, FWD, 0, 0)
b += box(OX + 4 * CELL, GY + 6 * CELL, CELL, CELL, REV, REV, 0, 0)
b += txt(OX + 7 * CELL, GY + 2 * CELL, "특징 지도 28 x 28 (일부)", 11, MUTED)
b += txt(OX + 4 * CELL, GY + 12.2 * CELL, "이웃한 두 출력", 11, INK2)

b += box(40, 300, 390, 104, "#FFFFFF", INK, 1.2, 8)
b += txt(60, 324, "32 - 5 + 1 = 28", 13.5, FWD, weight=600, anchor="start")
b += txt(60, 346, "가로로 이웃한 두 수용장은 4 열이 겹친다", 12, INK2, anchor="start")
b += txt(60, 366, "세로로 이웃한 두 수용장은 5 행이 겹친다", 12, INK2, anchor="start")
b += txt(60, 390, "한 장의 유닛 28 x 28 = 784 개에 가중치는 26 개", 11.5, REV, anchor="start", weight=600)

b += box(446, 300, 394, 104, "#FFFFFF", INK, 1.2, 8)
b += txt(466, 324, "입력을 32 로 잡은 이유", 12.5, INK, anchor="start", weight=600)
b += txt(466, 346, "가장 큰 글자가 28x28 안의 20x20 을 안 넘는데도 32 다.", 11.5, INK2, anchor="start")
b += txt(466, 366, "획의 끝점이나 모퉁이가 가장 높은 층 수용장의", 11.5, INK2, anchor="start")
b += txt(466, 386, "가운데에 올 수 있게 하려는 것이다.", 11.5, INK2, anchor="start")
svg("fig03_receptive_field", 880, 420, b,
    "5x5 수용장 둘이 4 열 겹치고 32 에서 28 이 나온다")


# ── 4. 가중치 공유가 줄이는 것 ────────────────────────────────────────────
b = txt(420, 28, "가중치 공유는 연결을 줄이지 않는다 — 학습되는 값을 줄인다", 14.5, INK, weight=600)

b += box(24, 46, 400, 210, "#F4F6F4", LINE, 1.2, 10)
b += txt(224, 70, "C1 한 층을 두 방식으로 세면", 12.5, INK, weight=600)
C1_UNITS = 6 * 28 * 28
C1_CONN = C1_UNITS * 26
C1_PARAM = 6 * 26
rows4 = [
    ("유닛 수", "6 장 x 28 x 28", C1_UNITS),
    ("연결 수 (유닛마다 25 + 바이어스)", "%s x 26" % format(C1_UNITS, ","), C1_CONN),
    ("공유하지 않으면 학습되는 값", "연결마다 하나", C1_CONN),
    ("공유하면 학습되는 값", "6 x (25 + 1)", C1_PARAM),
]
for i, (name, how, v) in enumerate(rows4):
    yy = 96 + i * 36
    col = REV if i == 3 else INK2
    b += txt(44, yy, name, 11.5, col, anchor="start", weight=(600 if i == 3 else None))
    b += txt(268, yy, how, 11, MUTED, anchor="start")
    b += txt(404, yy, format(v, ","), 12.5, col, anchor="end", weight=600)
b += txt(224, 240, "연결은 그대로인데 배워야 할 값이 %s 배로 줄어든다"
         % format(int(round(C1_CONN / float(C1_PARAM))), ","), 12, REV, weight=600)
print("  C1 연결 %d · 공유 시 학습되는 값 %d · 비 %.0f 배"
      % (C1_CONN, C1_PARAM, C1_CONN / float(C1_PARAM)))

b += box(434, 46, 406, 210, "#F4F6F4", LINE, 1.2, 10)
b += txt(637, 70, "망 전체 — 논문이 적는 두 수", 12.5, INK, weight=600)
b += bar_h(560, 96, 22, 340908, 360000, FWD, FWD_SOFT, "연결", "", 11.5, 210)
b += bar_h(560, 132, 22, 60000, 360000, REV, REV_SOFT, "학습되는 값", "", 11.5, 210)
b += txt(637, 184, "차이는 가중치 공유와 고정된 RBF 파라미터에서 온다", 11, INK2)
b += txt(637, 206, "%s + %s(RBF 연결) = %s"
         % (format(CONN_SUM, ","), RBF_CONN, format(CONN_SUM + RBF_CONN, ",")), 11.5, FWD, weight=600)
b += txt(637, 226, "층별 학습되는 값을 더하면 정확히 %s" % format(PARAM_SUM, ","), 11.5, REV, weight=600)
b += txt(637, 244, "(두 덧셈은 이 그림을 만들며 맞춰 본 것이다)", 10.5, MUTED)

b += box(28, 270, 812, 68, "#FFFFFF", INK, 1.3, 8)
b += txt(434, 294, "그래서 「가중치 공유가 계산을 줄인다」가 아니다 — 계산은 연결 수를 따라간다.", 12.5, INK, weight=600)
b += txt(434, 318, "줄어드는 것은 용량이고, 논문이 드는 효과도 학습 오차와 시험 오차의 간격이다.", 12, INK2)
svg("fig04_weight_sharing", 870, 352, b,
    "가중치 공유는 연결이 아니라 학습되는 값을 줄인다. C1 에서 122,304 대 156")


# ── 5. LeNet-5 의 층 일곱 ─────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("e1", INK2)
b += txt(470, 28, "LeNet-5 — 입력을 빼고 층 일곱", 15, INK, weight=600)

X0, Y0 = 34, 66
COLW = 118
stages = [
    ("입력", "32 x 32", "픽셀 값 -0.1 ~ 1.175", None, None, FWD_SOFT, FWD),
    ("C1", "6 장 @ 28x28", "합성곱 5x5", 156, 122304, REV_SOFT, REV),
    ("S2", "6 장 @ 14x14", "부분 표본 2x2", 12, 5880, "#E4EFE4", OK),
    ("C3", "16 장 @ 10x10", "합성곱 5x5 · 표 I", 1516, 151600, REV_SOFT, REV),
    ("S4", "16 장 @ 5x5", "부분 표본 2x2", 32, 2000, "#E4EFE4", OK),
    ("C5", "120 장 @ 1x1", "합성곱 5x5", 48120, 48120, REV_SOFT, REV),
    ("F6", "84", "완전연결", 10164, 10164, REV_SOFT, REV),
    ("출력", "10", "유클리드 RBF", None, 840, FWD_SOFT, FWD),
]
for i, (name, size, kind, par, con, soft, col) in enumerate(stages):
    x = X0 + i * COLW
    b += box(x, Y0, 104, 162, soft, col, 1.4, 8)
    b += txt(x + 52, Y0 + 24, name, 14, col, weight=600)
    b += txt(x + 52, Y0 + 44, size, 11.5, INK)
    b += txt(x + 52, Y0 + 62, kind, 10.5, INK2)
    # 작은 모양
    if name in ("입력",):
        b += grid(x + 32, Y0 + 74, 3.0, 13, 13, col, 0.4)
    elif name.startswith("C") or name.startswith("S"):
        n = 3
        for k in range(n):
            b += box(x + 26 + k * 8, Y0 + 74 + (n - 1 - k) * 6, 40, 32, "#FFFFFF", col, 0.9, 2, op="0.9")
    else:
        for k in range(5):
            b += circ(x + 26 + k * 13, Y0 + 92, 5, "#FFFFFF", col, 0.9)
    yy = Y0 + 132
    if par is not None:
        b += txt(x + 52, yy, "학습 %s" % format(par, ","), 10.5, REV, weight=600)
    else:
        b += txt(x + 52, yy, "고정" if name == "출력" else "", 10.5, MUTED)
    if con is not None:
        b += txt(x + 52, yy + 14, "연결 %s" % format(con, ","), 10.5, INK2)
    if i < len(stages) - 1:
        b += line(x + 104, Y0 + 75, x + COLW, Y0 + 75, INK2, 1.2, marker="e1")

b += box(34, 232, 512, 112, "#FFFFFF", INK, 1.2, 8)
b += txt(52, 256, "층별 학습되는 값을 더하면", 12, INK2, anchor="start")
b += txt(52, 280, "156 + 12 + 1,516 + 32 + 48,120 + 10,164 = %s" % format(PARAM_SUM, ","),
         13, REV, anchor="start", weight=600)
b += txt(52, 306, "연결을 더하고 RBF 의 84 x 10 = 840 을 넣으면", 12, INK2, anchor="start")
b += txt(52, 330, "%s" % format(CONN_SUM + RBF_CONN, ","), 13, FWD, anchor="start", weight=600)
b += txt(190, 330, "— 논문이 적는 340,908 과 같다", 11.5, INK2, anchor="start")

b += box(560, 232, 392, 112, "#FFFFFF", INK, 1.2, 8)
b += txt(578, 256, "C5 를 완전연결층이라 부르지 않는 이유", 12, INK, anchor="start", weight=600)
b += txt(578, 278, "S4 가 5x5 이고 커널도 5x5 라 지금은 1x1 이 되지만,", 11.5, INK2, anchor="start")
b += txt(578, 298, "입력을 키우면 C5 의 특징 지도가 1x1 보다 커진다.", 11.5, INK2, anchor="start")
b += txt(578, 322, "이 성질이 VII절의 SDNN 으로 이어진다.", 11.5, FWD, anchor="start", weight=600)
svg("fig05_lenet5", 986, 360, b,
    "LeNet-5 의 층 일곱과 층마다의 크기 · 학습되는 값 · 연결 수")


# ── 6. 부분 표본 뽑기 한 칸 ───────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("f1", OK)
b += txt(420, 28, "부분 표본 뽑기 한 칸 — 오늘날의 최댓값 풀링이 아니다", 14.5, INK, weight=600)

vals = [0.2, 0.4, 0.1, 0.3]
A_COEF, B_BIAS = 0.8, -0.2
s_sum = sum(vals)
s_mul = s_sum * A_COEF
s_add = s_mul + B_BIAS
s_out = squash(s_add)
print("  부분 표본 예시: 합 %.1f -> x%.1f = %.2f -> %+.1f = %.2f -> 누름 %.4f"
      % (s_sum, A_COEF, s_mul, B_BIAS, s_add, s_out))

b += grid(60, 70, 34, 2, 2, INK, 1.0)
for k, v in enumerate(vals):
    cx, cy = 60 + (k % 2) * 34 + 17, 70 + (k // 2) * 34 + 22
    b += txt(cx, cy, "%.1f" % v, 12.5, INK)
b += txt(94, 156, "2 x 2 이웃 넷", 11, MUTED)

steps = [
    ("① 더한다", "0.2+0.4+0.1+0.3", "%.1f" % s_sum, INK2),
    ("② 학습되는 계수를 곱한다", "x %.1f" % A_COEF, "%.2f" % s_mul, REV),
    ("③ 학습되는 바이어스를 더한다", "%+.1f" % B_BIAS, "%.2f" % s_add, REV),
    ("④ 누름 함수를 지난다", "1.7159 tanh(2/3 a)", "%.3f" % s_out, FWD),
]
for i, (name, how, out, col) in enumerate(steps):
    yy = 78 + i * 50
    b += box(196, yy - 22, 300, 40, "#F4F6F4", LINE, 1.0, 6)
    b += txt(210, yy - 2, name, 11.5, col, anchor="start", weight=600)
    b += txt(484, yy - 2, how, 11, MUTED, anchor="end")
    b += box(512, yy - 22, 74, 40, "#FFFFFF", col, 1.2, 6)
    b += txt(549, yy - 2, out, 13, col, weight=600)
    if i < 3:
        b += line(549, yy + 18, 549, yy + 28, INK2, 1.0, marker="f1")

b += box(612, 56, 228, 200, "#F4F6F4", LINE, 1.2, 10)
b += txt(726, 80, "그래서 층마다 학습되는 값이", 12, INK, weight=600)
b += txt(726, 102, "지도 수의 두 배다", 12, INK, weight=600)
b += box(636, 118, 180, 40, "#FFFFFF", OK, 1.2, 6)
b += txt(726, 143, "S2: 6 x 2 = 12", 13, OK, weight=600)
b += box(636, 166, 180, 40, "#FFFFFF", OK, 1.2, 6)
b += txt(726, 191, "S4: 16 x 2 = 32", 13, OK, weight=600)
b += txt(726, 226, "최댓값 풀링에는 학습되는 값이 없다.", 10.8, INK2)
b += txt(726, 244, "그래서 같은 것으로 부르지 않는다.", 10.8, INK2)

b += box(28, 286, 812, 68, "#FFFFFF", INK, 1.3, 8)
b += txt(434, 310, "논문은 계수가 작으면 준선형으로 흐려지고, 크면 「잡음 섞인 OR」 이나 「잡음 섞인 AND」 처럼 된다고 적는다.",
         12, INK, weight=600)
b += txt(434, 334, "곧 이 층은 해상도를 깎는 동시에 무엇을 통과시킬지도 배운다.", 12, INK2)
svg("fig06_subsampling", 870, 368, b,
    "부분 표본 뽑기의 네 단계와 숫자 예시, 학습되는 값이 지도 수의 두 배인 이유")


# ── 7. 표 I 의 연결 ───────────────────────────────────────────────────────
TABLE1 = [
    [0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5], [0, 4, 5], [0, 1, 5],
    [0, 1, 2, 3], [1, 2, 3, 4], [2, 3, 4, 5], [0, 3, 4, 5], [0, 1, 4, 5], [0, 1, 2, 5],
    [0, 1, 3, 4], [1, 2, 4, 5], [0, 2, 3, 5],
    [0, 1, 2, 3, 4, 5],
]
n_pairs = sum(len(c) for c in TABLE1)
c3_param = n_pairs * 25 + 16
c3_conn = c3_param * 100
c3_full_param = 16 * 6 * 25 + 16
print("  표 I: 이어진 쌍 %d · 학습되는 값 %d · 연결 %d · 전부 연결이면 %d"
      % (n_pairs, c3_param, c3_conn, c3_full_param))

b = txt(430, 28, "표 I — C3 의 특징 지도 열여섯이 S2 의 어느 장을 받는가", 14.5, INK, weight=600)
CW, CH = 34, 26
TX, TY = 120, 76
for c in range(16):
    b += txt(TX + c * CW + CW / 2, TY - 10, str(c), 11, MUTED)
for r in range(6):
    b += txt(TX - 14, TY + r * CH + 18, "S2 %d" % r, 11, MUTED, anchor="end")
b += grid(TX, TY, 0, 0, 0)
for r in range(6):
    for c in range(16):
        on_ = r in TABLE1[c]
        b += box(TX + c * CW, TY + r * CH, CW, CH, (REV_SOFT if on_ else "#FFFFFF"),
                 LINE, 0.8, 0)
        if on_:
            b += txt(TX + c * CW + CW / 2, TY + r * CH + 18, "X", 12.5, REV, weight=600)
# 묶음 표시
groups = [(0, 6, "이어진 3 장씩", FWD), (6, 12, "이어진 4 장씩", OK),
          (12, 15, "이어지지 않은 4 장씩", REV), (15, 16, "6 장 전부", INK)]
for (a0, a1, name, col) in groups:
    x0 = TX + a0 * CW
    w = (a1 - a0) * CW
    drop = 18 if a0 >= 12 else 0
    b += line(x0 + 2, TY + 6 * CH + 8, x0 + w - 2, TY + 6 * CH + 8, col, 2.0)
    b += txt(x0 + w / 2 + (30 if a0 == 15 else 0), TY + 6 * CH + 26 + drop, name, 10.5, col, weight=600)

b += box(40, 268, 380, 116, "#FFFFFF", INK, 1.2, 8)
b += txt(60, 292, "이어진 쌍 %d 개 x 25 + 바이어스 16 = %s"
         % (n_pairs, format(c3_param, ",")), 12.5, REV, anchor="start", weight=600)
b += txt(60, 314, "x 10 x 10 자리 = 연결 %s" % format(c3_conn, ","), 12, INK2, anchor="start")
b += txt(60, 342, "전부 연결이면 16 x 6 x 25 + 16 = %s" % format(c3_full_param, ","),
         12.5, NO, anchor="start", weight=600)
b += txt(60, 364, "곧 %s 개가 는다 (이 그림에서 센 값이다)"
         % format(c3_full_param - c3_param, ","), 11.5, INK2, anchor="start")

b += box(436, 268, 404, 116, "#FFFFFF", INK, 1.2, 8)
b += txt(456, 292, "논문이 대는 이유 둘", 12.5, INK, anchor="start", weight=600)
b += txt(456, 314, "(가) 연결 수를 다스릴 만한 범위로 묶는다", 11.5, INK2, anchor="start")
b += txt(456, 334, "(나) 망의 대칭을 깬다 — 입력 묶음이 다르면", 11.5, INK2, anchor="start")
b += txt(456, 352, "      특징 지도들이 서로 다른 특징을 뽑는다", 11.5, INK2, anchor="start")
b += txt(456, 376, "둘 다 전부 연결과 견준 숫자가 없다.", 11.5, NO, anchor="start", weight=600)
svg("fig07_c3_table", 870, 400, b,
    "표 I 의 6x16 연결표와 이어진 쌍 60 개에서 나오는 학습되는 값 1,516")


# ── 8. 출력층 RBF 와 손실 ─────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("g1", FWD), arrow("g2", REV))
b += txt(430, 28, "출력층은 소프트맥스가 아니라 유클리드 RBF 다", 14.5, INK, weight=600)

b += box(24, 46, 250, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(149, 70, "F6 의 84 = 7 x 12 — 부류 3 의 파라미터 벡터", 11.5, INK, weight=600)
# '3' 모양 7x12 비트맵
bitmap3 = [
    "0111100", "1100110", "0000110", "0000110", "0001100", "0011000",
    "0001100", "0000110", "0000110", "1100110", "0111100", "0000000",
]
CB = 13
for r, rowstr in enumerate(bitmap3):
    for c, ch in enumerate(rowstr):
        on_ = ch == "1"
        b += box(105 + c * CB, 90 + r * CB, CB, CB,
                 (INK if on_ else "#FFFFFF"), LINE, 0.5, 0)
b += txt(149, 268, "+1 은 검은 칸 · -1 은 흰 칸", 11, MUTED)
b += txt(149, 286, "사람이 그려 고정해 둔다", 11, REV, weight=600)

b += box(286, 46, 264, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(418, 70, "부류마다 RBF 하나", 12.5, INK, weight=600)
for k in range(5):
    b += circ(330, 104 + k * 34, 12, FWD_SOFT, FWD, 1.1)
    b += txt(330, 108 + k * 34, str(k), 11, FWD)
b += txt(330, 282, "…10 개", 10.5, MUTED)
b += box(378, 96, 150, 96, "#FFFFFF", INK, 1.2, 6)
b += txt(453, 124, "y(i) = Σ (x(j) - w(i,j))²", 12.5, INK, weight=600)
b += txt(453, 148, "입력 84 개와 자기 파라미터", 11, INK2)
b += txt(453, 166, "벡터의 제곱 거리", 11, INK2)
b += txt(453, 186, "작을수록 그 부류다", 11, OK, weight=600)
b += txt(418, 222, "-1 과 +1 은 F6 의 누름 함수가", 11, INK2)
b += txt(418, 240, "가장 많이 휘는 자리라", 11, INK2)
b += txt(418, 258, "F6 이 포화되지 않는다", 11, INK2)

b += box(562, 46, 278, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(701, 70, "손실 둘", 12.5, INK, weight=600)
b += box(580, 86, 242, 74, "#FFFFFF", INK2, 1.2, 6)
b += txt(701, 110, "식 8 — 정답 RBF 출력의 평균", 11.5, INK2, weight=600)
b += txt(701, 132, "부족한 점 셋을 논문이 스스로 적는다", 10.8, NO)
b += txt(701, 150, "주저앉기 · 경쟁 없음 · 그래서 식 9", 10.8, NO)
b += box(580, 170, 242, 106, "#FFFFFF", REV, 1.3, 6)
b += txt(701, 194, "식 9 — 판별 기준", 11.5, REV, weight=600)
b += txt(701, 216, "y(D) + log( e^-j + Σ e^-y(i) )", 12, INK, weight=600)
b += txt(701, 238, "둘째 항이 경쟁을 맡는다 —", 10.8, INK2)
b += txt(701, 256, "오답 부류의 벌점을 밀어 올린다", 10.8, INK2)

b += box(28, 308, 812, 68, "#FFFFFF", INK, 1.3, 8)
b += txt(434, 332, "가중치 공유가 있을 때의 역전파는 한 줄로 끝난다 — 연결마다 편미분을 구하고, 같은 값을 나눠 쓰는 연결들의 것을 더한다.",
         12, INK, weight=600)
b += txt(434, 356, "이 비트맵 표현은 숫자 열 개에는 값을 덜 하고, 인쇄 가능한 ASCII 전체처럼 헷갈리는 글자가 많을 때 값을 한다고 적는다.", 11.5, INK2)
svg("fig08_rbf_output", 870, 390, b,
    "7x12 비트맵으로 고정한 RBF 파라미터와 식 7 · 8 · 9")


# ── 9. 옮기면 같이 옮겨진다 ───────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("h1", FWD), arrow("h2", REV))
b += txt(420, 28, "가중치 공유가 주는 성질 — 입력이 옮겨지면 특징 지도도 같이 옮겨진다", 14.5, INK, weight=600)

def small_digit(x, y, cell, dx=0, color=INK):
    pts = [(2, 1), (3, 1), (4, 1), (4, 2), (3, 3), (2, 4), (2, 5), (3, 5), (4, 5)]
    s = grid(x, y, cell, 8, 7, LINE, 0.5)
    for (cx, cy) in pts:
        s += box(x + (cx + dx) * cell, y + cy * cell, cell, cell, color, color, 0, 0)
    return s

b += txt(130, 66, "입력", 12, MUTED)
b += small_digit(70, 78, 14, 0, INK)
b += txt(130, 208, "원본", 11.5, INK2)
b += small_digit(70, 232, 14, 2, REV)
b += txt(130, 362, "오른쪽으로 2 픽셀", 11.5, REV, weight=600)

b += line(202, 130, 246, 130, INK2, 1.2, marker="h1")
b += line(202, 284, 246, 284, REV, 1.2, marker="h2")

b += txt(320, 66, "특징 지도", 12, MUTED)
b += small_digit(260, 78, 14, 0, FWD)
b += small_digit(260, 232, 14, 2, REV)
b += txt(320, 208, "같은 자리", 11.5, INK2)
b += txt(320, 362, "2 픽셀만큼만 옮겨졌다", 11.5, REV, weight=600)

b += line(392, 130, 436, 130, INK2, 1.2, marker="h1")
b += line(392, 284, 436, 284, REV, 1.2, marker="h2")

b += txt(500, 66, "부분 표본 뒤", 12, MUTED)
b += small_digit(450, 78, 14, 0, OK)
b += small_digit(450, 232, 14, 1, OK)
b += txt(500, 208, "같은 자리", 11.5, INK2)
b += txt(500, 362, "이동이 1 칸으로 줄었다", 11.5, OK, weight=600)

b += box(596, 66, 250, 290, "#F4F6F4", LINE, 1.2, 10)
b += txt(721, 92, "그래서 무엇이 되는가", 12.5, INK, weight=600)
b += txt(721, 118, "특징 지도는 이동에 대해", 11.5, INK2)
b += txt(721, 136, "불변이 아니라 등변이다 —", 11.5, FWD, weight=600)
b += txt(721, 154, "같은 양만큼 따라 옮겨진다.", 11.5, INK2)
b += txt(721, 182, "부분 표본이 그 이동을 반으로", 11.5, INK2)
b += txt(721, 200, "깎아, 층을 쌓을수록 자리 정밀도가", 11.5, INK2)
b += txt(721, 218, "떨어지고 견디는 폭이 는다.", 11.5, INK2)
b += box(614, 236, 214, 104, "#FFFFFF", NO, 1.2, 6)
b += txt(721, 258, "논문이 적는 견디는 범위 셋", 11.5, NO, weight=600)
b += txt(721, 280, "크기 약 2 배까지", 11, INK2)
b += txt(721, 298, "세로 이동 글자 높이의 절반쯤", 11, INK2)
b += txt(721, 316, "회전 위아래 30 도까지", 11, INK2)
b += txt(721, 334, "셋 다 「추정된다」로만 적혀 있다", 10.5, NO, weight=600)
svg("fig09_shift", 870, 380, b,
    "입력을 2 픽셀 옮기면 특징 지도도 2 픽셀 옮겨지고 부분 표본 뒤에는 1 칸이 된다")


# ── 10. 그림 9 의 오차율 ──────────────────────────────────────────────────
b = txt(450, 28, "시험 10,000 장 위의 오차율 (%) — 논문 그림 9 에서 옮긴 값", 14.5, INK, weight=600)
rows10 = [
    ("선형", 12.0, MUTED, "#E8E8E8"),
    ("쌍별 선형", 7.6, MUTED, "#E8E8E8"),
    ("K-NN 유클리드", 5.0, MUTED, "#E8E8E8"),
    ("완전연결 28x28-300-10", 4.7, FWD, FWD_SOFT),
    ("완전연결 28x28-1000-10", 4.5, FWD, FWD_SOFT),
    ("완전연결 28x28-300-100-10", 3.05, FWD, FWD_SOFT),
    ("완전연결 28x28-500-150-10", 2.95, FWD, FWD_SOFT),
    ("[기울기 편] 20x20-300-10", 1.6, FWD, FWD_SOFT),
    ("접선 거리 [16x16]", 1.1, MUTED, "#E8E8E8"),
    ("SVM 다항 4차", 1.1, MUTED, "#E8E8E8"),
    ("축소집합 SVM 5차", 1.0, MUTED, "#E8E8E8"),
    ("[왜곡] V-SVM 9차", 0.8, MUTED, "#E8E8E8"),
    ("LeNet-1 [16x16]", 1.7, REV, REV_SOFT),
    ("LeNet-4", 1.1, REV, REV_SOFT),
    ("LeNet-5", 0.95, REV, REV_SOFT),
    ("[왜곡] LeNet-5", 0.8, REV, REV_SOFT),
    ("[왜곡] Boosted LeNet-4", 0.7, REV, REV_SOFT),
]
X10, Y10, W10 = 250, 58, 520
for i, (name, v, col, soft) in enumerate(rows10):
    yy = Y10 + i * 24
    b += bar_h(X10, yy, 17, v, 12.0, col, soft, name, "", 11.5, W10)
# 축
b += line(X10, Y10 - 6, X10, Y10 + len(rows10) * 24 - 4, LINE, 1.0)
for gv in (1, 2, 4, 6, 8, 10, 12):
    gx = X10 + W10 * gv / 12.0
    b += line(gx, Y10 - 6, gx, Y10 + len(rows10) * 24 - 4, LINE, 0.8, dash="3 4")
    b += txt(gx, Y10 - 12, str(gv), 10, MUTED)

yb = Y10 + len(rows10) * 24 + 12
b += box(40, yb, 880, 86, "#FFFFFF", INK, 1.3, 8)
b += txt(480, yb + 26, "논문 캡션이 적는 오차율의 불확실성이 0.1 백분율 점이다.", 12.5, NO, weight=600)
b += txt(480, yb + 48, "0.7 · 0.8 · 0.95 사이의 간격이 0.1 과 0.15 라, 이 셋에 순서를 매기는 문장은 그 불확실성을 함께 적어야 한다.", 12, INK2)
b += txt(480, yb + 70, "[왜곡] 은 왜곡으로 불린 학습 집합, [기울기 편] 과 [16x16] 은 입력이 다른 행이다.", 11.5, MUTED)
svg("fig10_results", 960, yb + 106, b,
    "그림 9 의 오차율 막대. LeNet-5 0.95, 왜곡 학습 0.8, Boosted LeNet-4 0.7")


# ── 11. 네 축 ─────────────────────────────────────────────────────────────
b = txt(430, 28, "오차만 보지 않는다 — 논문이 따로 그린 네 축", 14.5, INK, weight=600)
panels = [
    ("오차율 (%)", "그림 9", [("LeNet-5", 0.95, REV), ("[왜곡] LeNet-5", 0.8, REV),
                            ("28x28-1000-10", 4.5, FWD), ("K-NN", 5.0, MUTED)], 5.0, ""),
    ("기각률 (%)", "그림 10 · 오차 0.5% 를 맞추려면", [("LeNet-4", 1.8, REV), ("LeNet-4/Local", 1.4, REV),
                                                ("[왜곡] Boosted LeNet-4", 0.5, REV),
                                                ("[기울기 편] 20x20-300-10", 3.2, FWD)], 3.2, ""),
    ("곱셈-누적", "그림 11 · 단위가 캡션에 없다", [("LeNet-5", 401, REV), ("28x28-1000-10", 795, FWD),
                                          ("축소집합 SVM", 650, MUTED), ("K-NN", 24000, MUTED)], 900, ""),
    ("메모리 (변수 개수)", "그림 12 · 단위는 천 개", [("LeNet-5", 60, REV), ("28x28-1000-10", 795, FWD),
                                             ("축소집합 SVM", 650, MUTED), ("K-NN", 24000, MUTED)], 900, ""),
]
for pi, (title, sub, rows, vmax, unit) in enumerate(panels):
    px = 24 + (pi % 2) * 428
    py = 50 + (pi // 2) * 196
    b += box(px, py, 412, 180, "#F4F6F4", LINE, 1.2, 10)
    b += txt(px + 206, py + 24, title, 12.5, INK, weight=600)
    b += txt(px + 206, py + 42, sub, 10.5, MUTED)
    for ri, (name, v, col) in enumerate(rows):
        yy = py + 56 + ri * 28
        over = v > vmax
        soft = {REV: REV_SOFT, FWD: FWD_SOFT, MUTED: "#E4E4E4"}[col]
        if over:
            b += txt(px + 186, yy + 13, name, 10.8, INK2, anchor="end")
            b += box(px + 192, yy, 130, 17, soft, col, 1.0, 3, dash="4 3")
            b += txt(px + 328, yy + 13, "%s (축 밖)" % format(v, ","), 10.8, NO, anchor="start")
        else:
            b += txt(px + 186, yy + 13, name, 10.8, INK2, anchor="end")
            L = max(2.0, 130 * (v / float(vmax)))
            b += box(px + 192, yy, L, 17, soft, col, 1.0, 3)
            b += txt(px + 196 + L, yy + 13, format(v, ","), 10.8, INK2, anchor="start")

b += box(28, 448, 808, 66, "#FFFFFF", INK, 1.3, 8)
b += txt(432, 472, "그림 12 의 LeNet-5 값 60 이 자유 파라미터 60,000 과 맞아, 이 그림의 단위가 천 개로 읽힌다.", 12, INK, weight=600)
b += txt(432, 496, "그림 11 에는 같은 실마리가 없다. 그래서 노트는 그림 11 에서 배수만 옮긴다.", 12, INK2)
svg("fig11_four_axes", 866, 530, b,
    "오차율 · 기각률 · 곱셈-누적 · 메모리 네 축에서 LeNet-5 와 견줄 값들")


# ── 12. 왜곡과 학습 집합 크기 ─────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("j1", REV)
b += txt(420, 28, "데이터를 불리면 — 왜곡 540,000 장을 더한 결과", 14.5, INK, weight=600)

b += box(24, 50, 400, 210, "#F4F6F4", LINE, 1.2, 10)
b += txt(224, 76, "학습 집합", 12.5, INK, weight=600)
b += box(60, 96, 150, 44, FWD_SOFT, FWD, 1.2, 6)
b += txt(135, 124, "원본 60,000", 12.5, FWD, weight=600)
b += txt(224, 124, "+", 14, MUTED)
b += box(238, 96, 150, 44, REV_SOFT, REV, 1.2, 6)
b += txt(313, 124, "왜곡 540,000", 12.5, REV, weight=600)
b += txt(224, 164, "평면 아핀 변환 — 가로세로 이동 · 크기 ·", 11.5, INK2)
b += txt(224, 182, "눌림(가로 압축과 세로 신장) · 가로 밀림", 11.5, INK2)
b += box(60, 196, 328, 48, "#FFFFFF", INK, 1.2, 6)
b += txt(224, 216, "학습 길이는 그대로 60,000 장 x 20 바퀴", 12, INK, weight=600)
b += txt(224, 236, "= 갱신 1,200,000 번 / 600,000 장 = 한 장을 2 번씩", 11.5, REV, weight=600)
print("  왜곡: 600,000 장을 1,200,000 번 = 한 장당 %.1f 번" % (1200000 / 600000.0))

b += box(436, 50, 404, 210, "#F4F6F4", LINE, 1.2, 10)
b += txt(638, 76, "시험 오차", 12.5, INK, weight=600)
b += bar_h(600, 100, 26, 0.95, 1.1, FWD, FWD_SOFT, "왜곡 없이", " %", 12, 190)
b += bar_h(600, 144, 26, 0.8, 1.1, REV, REV_SOFT, "왜곡 학습", " %", 12, 190)
b += txt(638, 196, "0.15 백분율 점이 내려갔다", 12, INK2)
b += txt(638, 218, "다만 논문이 적는 불확실성이 0.1 백분율 점이다", 11.5, NO, weight=600)
b += txt(638, 240, "완전연결 쪽 [왜곡] 이 같은 집합인지는 본문에 없다", 11, MUTED)

b += box(28, 274, 812, 66, "#FFFFFF", INK, 1.3, 8)
b += txt(434, 298, "그림 6 이 학습 집합 15,000 · 30,000 · 60,000 장을 견주고, 더 큰 학습 집합이 LeNet-5 를 더 낫게 할 것이라고 적는다.",
         12, INK, weight=600)
b += txt(434, 322, "그리고 그림 5 에서 시험 오차가 10 바퀴 언저리에서 가라앉고 다시 오르지 않는다 — 논문은 그 까닭을 추측으로 적는다.", 12, INK2)
svg("fig12_distortion", 870, 354, b,
    "원본 60,000 에 왜곡 540,000 을 더해 0.95% 에서 0.8% 로 내려간 결과")


# ── 13. 휴리스틱 과분할과 GTN ─────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("k1", INK2), arrow("k2", REV))
b += txt(450, 28, "길 하나 — 자를 자리를 많이 만들고 벌점으로 고른다", 14.5, INK, weight=600)

stack = [
    ("입력 이미지", "\"34\" 한 장", FWD_SOFT, FWD),
    ("분할 그래프 G(seg)", "자를 자리를 필요한 것보다 많이", "#EFEFEF", INK2),
    ("인식 변환기 T(rec)", "간선마다 인식기를 돌려 부류별 벌점", REV_SOFT, REV),
    ("해석 그래프 G(int)", "간선 하나가 부류 하나 — 라벨과 벌점", "#EFEFEF", INK2),
    ("경로 선택기", "정답 라벨 열과 맞는 경로만 남긴다", "#E4EFE4", OK),
    ("비터비 변환기", "누적 벌점이 가장 작은 경로 하나", "#EFEFEF", INK2),
    ("벌점", "이것이 손실이 된다", FWD_SOFT, FWD),
]
SX, SY, SH = 40, 58, 52
for i, (name, sub, soft, col) in enumerate(stack):
    yy = SY + i * (SH + 10)
    b += box(SX, yy, 300, SH, soft, col, 1.3, 7)
    b += txt(SX + 150, yy + 22, name, 12.5, col, weight=600)
    b += txt(SX + 150, yy + 40, sub, 10.8, INK2)
    if i < len(stack) - 1:
        b += line(SX + 150, yy + SH, SX + 150, yy + SH + 10, INK2, 1.2, marker="k1")

# 오른쪽 — 분할 그래프 예시
b += box(370, 58, 300, 176, "#F4F6F4", LINE, 1.2, 10)
b += txt(520, 82, "분할 그래프의 경로 둘", 12.5, INK, weight=600)
nodes = [(400, 120), (460, 120), (520, 120), (580, 120), (640, 120)]
for (nx, ny) in nodes:
    b += circ(nx, ny, 7, "#FFFFFF", INK, 1.2)
labels = ["3", "4", "1", "2"]
for i in range(4):
    b += line(nodes[i][0] + 7, 120, nodes[i + 1][0] - 7, 120, INK2, 1.2, marker="k1")
    b += txt((nodes[i][0] + nodes[i + 1][0]) / 2, 112, labels[i], 11.5, INK2)
b += path("M 400 128 Q 460 168 520 128", REV, "none", 1.6, marker="k2")
b += txt(460, 176, "34 로 한 덩이", 11, REV)
b += path("M 520 128 Q 580 168 640 128", REV, "none", 1.6, marker="k2")
b += txt(580, 176, "12 로 한 덩이", 11, REV)
b += txt(520, 208, "경로 하나가 해석 하나다 — 잉크 조각을 한 번씩만 쓴다", 10.8, MUTED)

# 오른쪽 아래 — 손실 셋
b += box(370, 246, 300, 262, "#F4F6F4", LINE, 1.2, 10)
b += txt(520, 270, "손실을 셋으로 고쳐 간다", 12.5, INK, weight=600)
losses = [
    ("비터비 학습 (식 11)", "정답 경로의 벌점", "주저앉기 — 입력을 무시하면 최소가 된다", NO),
    ("판별 비터비 (식 12)", "정답 경로 − 최선 경로", "여유를 안 만든다 — 같아지면 기울기 0", NO),
    ("판별 앞방향 (식 17)", "logadd 로 모든 경로를 모은다", "경로 하나가 아니라 해석 전체를 본다", OK),
]
for i, (name, what, why, col) in enumerate(losses):
    yy = 286 + i * 74
    b += box(388, yy, 264, 62, "#FFFFFF", col, 1.2, 6)
    b += txt(520, yy + 20, name, 11.8, col, weight=600)
    b += txt(520, yy + 38, what, 10.8, INK)
    b += txt(520, yy + 54, why, 10.2, INK2)

BAND = 520
b += box(44, BAND, 626, 62, "#FFFFFF", INK, 1.3, 8)
b += txt(357, BAND + 26, "감독자가 주는 것은 바라는 글자 라벨의 열뿐이다 — 어디서 잘렸는지는 주지 않는다.",
         12.5, INK, weight=600)
b += txt(357, BAND + 48, "잘못 잘린 글자에 사람이 라벨을 붙이는 일을 없애는 것이 이 얼개의 값이다.", 12, INK2)
svg("fig13_gtn", 700, BAND + 80, b,
    "분할 그래프에서 비터비까지의 흐름과 손실을 셋으로 고쳐 간 과정")


# ── 14. SDNN ──────────────────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("m1", FWD), arrow("m2", REV))
b += txt(420, 28, "길 둘 — 자르지 않고 쓸어본다 (SDNN)", 14.5, INK, weight=600)

b += box(24, 50, 400, 216, "#F4F6F4", LINE, 1.2, 10)
b += txt(224, 74, "인식기를 자리마다 하나씩 대면", 12.5, NO, weight=600)
b += box(60, 92, 328, 52, "#FFFFFF", LINE, 1.0, 4)
b += txt(224, 124, "2 3 4 5", 22, INK, weight=600)
for k, xx in enumerate([70, 130, 190, 250]):
    b += box(xx, 88, 60, 60, "none", REV, 1.4, 3, dash="4 3")
b += txt(224, 172, "겹치는 자리를 다시 계산한다", 11.5, INK2)
b += txt(224, 194, "논문은 이 방식이 일반적으로 비싸다고 적는다", 11.5, INK2)
b += txt(224, 228, "그리고 가운데 글자 옆에 이웃 글자가 닿아 있어도", 11, MUTED)
b += txt(224, 246, "가운데 것을 맞게 읽어야 한다", 11, MUTED)

b += box(436, 50, 404, 216, "#F4F6F4", LINE, 1.2, 10)
b += txt(638, 74, "합성곱이면 한 번에 된다", 12.5, OK, weight=600)
for k in range(4):
    b += box(470 + k * 10, 96 + (3 - k) * 8, 240, 44, "#FFFFFF", FWD, 1.0, 3, op="0.95")
b += txt(600, 128, "입력 폭을 넓힌 같은 망", 11.5, FWD, weight=600)
b += line(600, 152, 600, 172, OK, 1.2, marker="m1")
for k in range(6):
    b += box(500 + k * 34, 176, 30, 26, ("#E4EFE4" if k % 2 == 0 else "#FFFFFF"), OK, 1.0, 3)
b += txt(638, 218, "출력층도 합성곱층이 되어 자리마다 증거가 나온다", 11.5, INK2)
b += txt(638, 240, "새로 계산할 것은 얇은 「조각」뿐이다", 11.5, OK, weight=600)

b += box(24, 280, 400, 120, "#FFFFFF", INK, 1.2, 8)
b += txt(224, 304, "실험 설정", 12.5, INK, weight=600)
b += txt(44, 328, "가운데 글자 양옆에 다른 글자를 붙였다", 11.5, INK2, anchor="start")
b += txt(44, 348, "경계 상자 사이 간격은 -1 에서 4 픽셀 사이 무작위", 11.5, INK2, anchor="start")
b += txt(44, 368, "픽셀마다 10% 소금후추 잡음", 11.5, INK2, anchor="start")
b += txt(44, 390, "가운데가 비면 빈칸 부류를 내게 했다", 11.5, INK2, anchor="start")

b += box(436, 280, 404, 120, "#FFFFFF", NO, 1.3, 8)
b += txt(638, 306, "그런데 논문이 성적을 낮춰 적는다", 12.5, NO, weight=600)
b += txt(638, 332, "SDNN 은 OCR 에 유망하고 매력적인 방법이지만,", 11.5, INK2)
b += txt(638, 352, "지금까지 휴리스틱 과분할보다 나은 결과를", 11.5, INK2)
b += txt(638, 372, "내지는 못했다 (VII-C).", 11.5, INK2)
b += txt(638, 392, "곧 둘은 이어지는 단계가 아니라 경쟁하는 두 길이다.", 11, MUTED)
svg("fig14_sdnn", 870, 416, b,
    "인식기를 자리마다 대는 대신 입력 폭을 넓히는 SDNN 과 그 한계")


# ── 15. 한계와 다음 ───────────────────────────────────────────────────────
b = txt(440, 28, "이 논문이 스스로 적은 한계와, 내가 재 보려는 자리", 14.5, INK, weight=600)

b += box(24, 48, 426, 350, "#F4F6F4", LINE, 1.2, 10)
b += txt(237, 72, "논문이 적은 한계", 13, NO, weight=600)
lim = [
    "온전한 불변 인식은 아직 손에 잡히지 않은 목표다",
    "파라미터 많은 망이 왜 되는지가 수수께끼로 남는다",
    "극소점이 왜 문제가 안 되는지도 이론적으로 비었다",
    "SDNN 이 휴리스틱 과분할을 아직 못 이겼다",
    "비터비 학습은 주저앉고, 판별 비터비는 여유가 없다",
    "수표 읽기에서 전역 학습의 몫이 작았다",
    "더 큰 구조가 반드시 더 낫지는 않았다",
    "특화 하드웨어의 앞날이 불확실하다",
    "출력 그래프의 구조를 배우는 일은 조합 문제로 보인다",
]
for i, t in enumerate(lim):
    yy = 98 + i * 32
    b += txt(46, yy, "%d." % (i + 1), 11.5, NO, anchor="start", weight=600)
    b += txt(70, yy, t, 11.5, INK2, anchor="start")
b += txt(237, 386, "다섯째는 논문이 스스로 답(앞방향 학습)까지 낸다", 10.8, MUTED)

b += box(462, 48, 384, 350, "#F4F6F4", LINE, 1.2, 10)
b += txt(654, 72, "내가 짚은 자리에서 잴 것 다섯", 13, REV, weight=600)
mine = [
    ("A", "세운 LeNet-5 의 자유 파라미터가 60,000 인가"),
    ("B", "픽셀을 고정 순열로 섞으면 둘이 각각 얼마나 무너지는가"),
    ("C", "옮기면 오차가 어떤 모양으로 오르는가"),
    ("D", "가중치 공유만 끄면 파라미터와 오차가 얼마가 되는가"),
    ("E", "표 I 대신 전부 연결하면 무엇이 달라지는가"),
]
for i, (k, t) in enumerate(mine):
    yy = 104 + i * 54
    b += box(482, yy - 22, 344, 44, "#FFFFFF", REV, 1.1, 6)
    b += txt(502, yy + 4, k, 14, REV, weight=600)
    b += txt(522, yy + 4, t, 11.2, INK2, anchor="start")
b += txt(654, 386, "B 와 C 는 논문이 문장으로만 적고 재지 않은 자리다", 10.8, MUTED)
svg("fig15_limits", 876, 418, b,
    "논문이 적은 한계 아홉과 실험으로 잴 다섯 자리")


print("끝났다.")
