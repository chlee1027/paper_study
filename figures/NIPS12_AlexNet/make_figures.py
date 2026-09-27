# -*- coding: utf-8 -*-
"""AlexNet 노트(NIPS 2012)의 그림 열셋을 만든다.

색과 글꼴은 퍼셉트론 · 역전파 · DDPM · DBN · LeNet 노트의 그림과 맞췄다 — 저장소의 노트들이
한 벌로 읽히게 하려는 것이다. 그림을 고치려면 이 파일을 고쳐 다시 돌린다.
바깥 데이터를 읽지 않으므로 어디서나 돈다.

  python make_figures.py

그림 7 의 파라미터 수, 그림 11 의 뉴런 합계, 그림 3 의 층별 출력 크기는 이 파일이 직접
계산한다. 계산한 값은 돌릴 때 화면에도 찍는다 — **논문이 적은 수와 어긋나는 자리가 있어서**
(초록의 6천만 · 650,000, 그림 2 캡션의 253,440) 눈으로 맞춰 보려는 것이다.
"""
import io, os, math

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"
NODE      = "#F6F7F5"
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 구조로 정해 놓은 것
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 학습으로 바뀌는 것 · 이 논문이 새로 넣은 것
REV_SOFT  = "#F2DED2"
OK        = "#1E8449"
NO        = "#C0392B"
FONT = "IBM Plex Sans KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"


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
    s = ""
    for c in range(cols + 1):
        s += line(x + c * cell, y, x + c * cell, y + rows * cell, stroke or LINE, sw, op=op)
    for r in range(rows + 1):
        s += line(x, y + r * cell, x + cols * cell, y + r * cell, stroke or LINE, sw, op=op)
    return s


def bar_h(x, y, h, val, vmax, color, soft, label, unit="", size=11.5, wide=300, fmt="%s"):
    L = max(2.0, wide * (float(val) / vmax))
    s = txt(x - 8, y + h * 0.72, label, size, INK2, anchor="end")
    s += box(x, y, L, h, soft, color, 1.0, 3)
    shown = fmt(val) if callable(fmt) else (fmt % val)
    s += txt(x + L + 7, y + h * 0.72, shown + unit, size, INK2, anchor="start")
    return s


print("그림을 만든다 ->", OUT)

# ── 논문 수치를 여기서 한 번 센다 ─────────────────────────────────────────
# 층별 (이름, 커널 수, 커널 하나의 값 수, 출력 크기)
CONV = [
    ("conv1", 96,  11 * 11 * 3,  55, 96),
    ("conv2", 256, 5 * 5 * 48,   27, 256),
    ("conv3", 384, 3 * 3 * 256,  13, 384),
    ("conv4", 384, 3 * 3 * 192,  13, 384),
    ("conv5", 256, 3 * 3 * 192,  13, 256),
]
POOL5 = 6          # (13 - 3) / 2 + 1 = 6. 논문이 6 이라고 적지는 않는다 — 내가 센 값이다
FC = [("fc6", 4096, POOL5 * POOL5 * 256), ("fc7", 4096, 4096), ("fc8", 1000, 4096)]

params = [(n, k * s + k) for (n, k, s, _o, _c) in CONV] + [(n, o * i + o) for (n, o, i) in FC]
P_TOTAL = sum(v for _n, v in params)
NEUR_LISTED = [253440, 186624, 64896, 64896, 43264, 4096, 4096, 1000]
NEUR_FIXED = [55 * 55 * 96] + NEUR_LISTED[1:]
print("  층별 파라미터:", ["%s %s" % (n, format(v, ",")) for n, v in params])
print("  파라미터 합계 %s (논문 초록은 「6천만」)" % format(P_TOTAL, ","))
print("  fc6 이 전체의 %.1f%%" % (100.0 * dict(params)["fc6"] / P_TOTAL))
print("  뉴런: 캡션대로 더하면 %s · 첫 층을 55x55x96 으로 고치면 %s (초록은 650,000)"
      % (format(sum(NEUR_LISTED), ","), format(sum(NEUR_FIXED), ",")))
print("  첫 층 셈: (224-11)/4+1 = %.2f · (227-11)/4+1 = %.2f" % ((224 - 11) / 4.0 + 1, (227 - 11) / 4.0 + 1))


# ── 1. LeNet 이후 무엇이 달라졌는가 ───────────────────────────────────────
b = '<defs>%s</defs>' % arrow("a1", REV)
b += txt(430, 28, "1998 에서 2012 사이에 먼저 커진 것은 데이터다", 14.5, INK, weight=600)

rows1 = [
    ("학습 사례", "60,000", "1,200,000", 20),
    ("부류", "10", "1,000", 100),
    ("학습되는 값", "60,000", "60,000,000", 1000),
    ("장비", "CPU 하나", "GPU 두 장", None),
    ("학습 시간", "2~3 일", "5~6 일", None),
]
y0 = 58
b += box(24, y0 - 14, 816, 40, "#F4F6F4", LINE, 1.0, 6)
b += txt(150, y0 + 10, "무엇", 12, INK, weight=600)
b += txt(360, y0 + 10, "LeNet-5 (1998)", 12, FWD, weight=600)
b += txt(580, y0 + 10, "AlexNet (2012)", 12, REV, weight=600)
b += txt(760, y0 + 10, "배수", 12, INK2, weight=600)
for i, (name, a, c, mult) in enumerate(rows1):
    yy = y0 + 46 + i * 36
    b += txt(150, yy, name, 12, INK2)
    b += txt(360, yy, a, 12.5, FWD)
    b += txt(580, yy, c, 12.5, REV, weight=600)
    b += txt(760, yy, ("%s 배" % format(mult, ",")) if mult else "—", 12, INK2)
    if i < len(rows1) - 1:
        b += line(40, yy + 12, 824, yy + 12, LINE, 0.8)

b += box(24, 250, 400, 120, "#FFFFFF", INK, 1.2, 8)
b += txt(224, 274, "이 논문이 적는 출발점 셋", 12.5, INK, weight=600)
b += txt(44, 298, "하나. 작은 데이터로는 실제 장면의 물체를 못 배운다", 11.5, INK2, anchor="start")
b += txt(44, 320, "둘. 그러려면 용량이 큰 모델이 필요하다", 11.5, INK2, anchor="start")
b += txt(44, 342, "셋. 합성곱 망은 좋지만 큰 규모로 쓰기에 비쌌다", 11.5, INK2, anchor="start")
b += txt(224, 362, "— 그 셋째를 GPU 가 푼다", 11.5, REV, weight=600)

b += box(440, 250, 400, 120, "#FFFFFF", INK, 1.2, 8)
b += txt(640, 274, "합성곱 망이 담는 사전 지식 둘", 12.5, INK, weight=600)
b += txt(460, 298, "통계가 자리에 따라 변하지 않는다", 11.5, FWD, anchor="start", weight=600)
b += txt(460, 320, "픽셀의 의존이 가깝다", 11.5, FWD, anchor="start", weight=600)
b += txt(640, 350, "데이터가 아무리 커도 이 과제를 다 적을 수 없으니,", 11, INK2)
b += txt(640, 366, "모델이 없는 데이터를 메울 가정을 담아야 한다", 11, INK2)
svg("fig01_gap", 866, 388, b,
    "1998 과 2012 사이에 학습 사례 20배, 부류 100배, 학습되는 값 1000배가 되었다")


# ── 2. ReLU ───────────────────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("b1", REV), arrow("b2", FWD))
b += txt(430, 28, "3.1 ReLU — 저자가 가장 중요하다고 꼽은 것", 14.5, INK, weight=600)

# 함수 그림
b += box(24, 48, 392, 240, "#F4F6F4", LINE, 1.2, 10)
ax0, ay0, aw, ah = 70, 80, 300, 170
b += line(ax0, ay0 + ah / 2, ax0 + aw, ay0 + ah / 2, INK2, 1.0)
b += line(ax0 + aw / 2, ay0, ax0 + aw / 2, ay0 + ah, INK2, 1.0)
pts_t, pts_r = [], []
for i in range(0, 121):
    x = -4 + 8.0 * i / 120.0
    sx = ax0 + aw * (x + 4) / 8.0
    t = math.tanh(x)
    pts_t.append("%.1f,%.1f" % (sx, ay0 + ah / 2 - (ah / 2) * 0.8 * t))
    r = max(0.0, x)
    pts_r.append("%.1f,%.1f" % (sx, ay0 + ah / 2 - (ah / 2) * 0.8 * min(r, 1.6) / 1.6))
b += '<polyline points="%s" fill="none" stroke="%s" stroke-width="2.4"/>' % (" ".join(pts_t), FWD)
b += '<polyline points="%s" fill="none" stroke="%s" stroke-width="2.4"/>' % (" ".join(pts_r), REV)
b += txt(ax0 + 46, ay0 + 26, "tanh — 포화한다", 11.5, FWD, weight=600)
b += txt(ax0 + 250, ay0 + 26, "ReLU", 11.5, REV, weight=600)
b += txt(220, 272, "포화한 자리에서는 기울기가 0 으로 눌린다", 11.5, INK2)

# 6배
b += box(432, 48, 408, 240, "#F4F6F4", LINE, 1.2, 10)
b += txt(636, 72, "그림 1 의 값 — CIFAR-10, 네 층 망", 12.5, INK, weight=600)
b += txt(636, 94, "학습 오차 25% 에 닿기까지 걸린 바퀴 수", 11.5, MUTED)
b += bar_h(600, 112, 24, 1, 6, REV, REV_SOFT, "ReLU", " 배", 12, 190, "%.0f")
b += bar_h(600, 150, 24, 6, 6, FWD, FWD_SOFT, "tanh", " 배", 12, 190, "%.0f")
b += box(452, 190, 368, 82, "#FFFFFF", NO, 1.2, 6)
b += txt(636, 212, "그림 설명이 붙여 놓은 조건 셋", 11.5, NO, weight=600)
b += txt(470, 232, "두 망의 학습률을 각각 따로 골랐다", 11, INK2, anchor="start")
b += txt(470, 250, "정칙화를 전혀 걸지 않았다", 11, INK2, anchor="start")
b += txt(470, 268, "효과의 크기는 구조에 따라 달라진다", 11, INK2, anchor="start")

b += box(28, 302, 812, 62, "#FFFFFF", INK, 1.3, 8)
b += txt(434, 326, "그래서 「ReLU 가 6 배 빠르다」로 옮겨 적으면 안 된다 — 조건이 붙은 값이다.", 12.5, INK, weight=600)
b += txt(434, 350, "논문이 말하는 것은 「포화하지 않는 비선형이 학습 집합에 빨리 맞춰 간다」이고, 과적합을 막는 이야기와는 다른 자리다.", 11.5, INK2)
svg("fig02_relu", 866, 380, b,
    "tanh 는 포화하고 ReLU 는 포화하지 않는다. CIFAR-10 네 층 망에서 6배")


# ── 3. 전체 구조 ──────────────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("c1", INK2)
b += txt(500, 28, "AlexNet — 학습되는 층 여덟 (괄호는 GPU 하나의 몫)", 15, INK, weight=600)

stages = [
    ("입력", "224x224x3", "", FWD_SOFT, FWD, ""),
    ("conv1", "55x55x96", "11x11x3 x96, 보폭 4", REV_SOFT, REV, "LRN + 풀링"),
    ("conv2", "27x27x256", "5x5x48 x256", REV_SOFT, REV, "LRN + 풀링"),
    ("conv3", "13x13x384", "3x3x256 x384", REV_SOFT, REV, "앞 층 전부를 받는다"),
    ("conv4", "13x13x384", "3x3x192 x384", REV_SOFT, REV, ""),
    ("conv5", "13x13x256", "3x3x192 x256", REV_SOFT, REV, "풀링"),
    ("fc6", "4096 (2048x2)", "", "#E4EFE4", OK, "드롭아웃"),
    ("fc7", "4096 (2048x2)", "", "#E4EFE4", OK, "드롭아웃"),
    ("fc8", "1000", "소프트맥스", FWD_SOFT, FWD, ""),
]
X0, Y0, COLW = 30, 62, 110
for i, (name, size, kern, soft, col, after) in enumerate(stages):
    x = X0 + i * COLW
    b += box(x, Y0, 98, 132, soft, col, 1.4, 8)
    b += txt(x + 49, Y0 + 24, name, 13.5, col, weight=600)
    b += txt(x + 49, Y0 + 44, size, 10.8, INK)
    if kern:
        b += txt(x + 49, Y0 + 62, kern, 9.6, INK2)
    # 작은 모양
    if name == "입력":
        b += grid(x + 30, Y0 + 74, 3.0, 13, 13, col, 0.4)
    elif name.startswith("conv"):
        for k in range(3):
            b += box(x + 22 + k * 8, Y0 + 70 + (2 - k) * 6, 40, 28, "#FFFFFF", col, 0.9, 2, op="0.9")
    else:
        for k in range(5):
            b += circ(x + 24 + k * 13, Y0 + 92, 5, "#FFFFFF", col, 0.9)
    if after:
        b += txt(x + 49, Y0 + 122, after, 9.6, REV if "풀링" in after or "LRN" in after else OK, weight=600)
    if i < len(stages) - 1:
        b += line(x + 98, Y0 + 66, x + COLW, Y0 + 66, INK2, 1.2, marker="c1")

# GPU 띠
b += box(X0 + COLW, Y0 + 146, COLW * 5 - 12, 26, FWD_SOFT, FWD, 1.0, 5)
b += txt(X0 + COLW + (COLW * 5 - 12) / 2, Y0 + 164, "커널의 절반씩이 GPU 두 장에 나뉘어 있다", 11, FWD, weight=600)

b += box(30, 252, 470, 116, "#FFFFFF", INK, 1.2, 8)
b += txt(50, 276, "파라미터를 세면", 12.5, INK, anchor="start", weight=600)
b += txt(50, 300, "%s 개 — 초록의 「6천만」과 맞는다" % format(P_TOTAL, ","), 12.5, REV, anchor="start", weight=600)
b += txt(50, 322, "(이 그림을 만들며 층별로 더한 값이다. 논문은 층별 파라미터를 적지 않는다)", 10.8, MUTED, anchor="start")
b += txt(50, 348, "fc6 하나가 전체의 %.0f%% 다" % (100.0 * dict(params)["fc6"] / P_TOTAL),
         12, INK2, anchor="start", weight=600)

b += box(516, 252, 470, 116, "#FFFFFF", NO, 1.3, 8)
b += txt(536, 276, "맞지 않는 자리 둘", 12.5, NO, anchor="start", weight=600)
b += txt(536, 300, "(224 - 11) / 4 + 1 = 54.25 — 55 가 되려면 227 이어야 한다", 11.5, INK2, anchor="start")
b += txt(536, 322, "그림 2 캡션의 첫 층 뉴런 253,440 ≠ 55 x 55 x 96 = 290,400", 11.5, INK2, anchor="start")
b += txt(536, 348, "둘 다 내가 셈해 본 것이다. 본문에 패딩 이야기가 없다.", 10.8, MUTED, anchor="start")
svg("fig03_architecture", 1010, 388, b,
    "AlexNet 여덟 층의 출력 크기와 커널, 그리고 파라미터 합계와 맞지 않는 자리 둘")


# ── 4. 두 GPU ─────────────────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("d1", FWD), arrow("d2", REV))
b += txt(430, 28, "3.2 GPU 둘로 쪼개기 — 메모리 3GB 가 정한 구조", 14.5, INK, weight=600)

names = ["conv1", "conv2", "conv3", "conv4", "conv5"]
X0, Y0, W, GAP = 90, 70, 110, 42
for i, n in enumerate(names):
    x = X0 + i * (W + GAP)
    b += box(x, Y0, W, 48, REV_SOFT, REV, 1.3, 6)
    b += txt(x + W / 2, Y0 + 30, n, 12.5, REV, weight=600)
    b += box(x, Y0 + 112, W, 48, REV_SOFT, REV, 1.3, 6)
    b += txt(x + W / 2, Y0 + 142, n, 12.5, REV, weight=600)
b += txt(52, Y0 + 30, "GPU 1", 12, FWD, weight=600, anchor="end")
b += txt(52, Y0 + 142, "GPU 2", 12, FWD, weight=600, anchor="end")

for i in range(4):
    x1 = X0 + i * (W + GAP) + W
    x2 = X0 + (i + 1) * (W + GAP)
    b += line(x1, Y0 + 24, x2, Y0 + 24, INK2, 1.3, marker="d1")
    b += line(x1, Y0 + 136, x2, Y0 + 136, INK2, 1.3, marker="d1")
# conv3 만 넘나든다
x1 = X0 + 1 * (W + GAP) + W
x2 = X0 + 2 * (W + GAP)
b += path("M %d %d L %d %d" % (x1, Y0 + 32, x2, Y0 + 128), OK, "none", 2.0, marker="d2")
b += path("M %d %d L %d %d" % (x1, Y0 + 128, x2, Y0 + 32), OK, "none", 2.0, marker="d2")
b += txt((x1 + x2) / 2, Y0 + 88, "conv3 만 서로 넘나든다", 11.5, OK, weight=600)

b += box(30, 254, 400, 122, "#FFFFFF", INK, 1.2, 8)
b += txt(230, 278, "이득과 견준 상대", 12.5, INK, weight=600)
b += txt(50, 302, "top-1 -1.7% · top-5 -1.2%", 13, REV, anchor="start", weight=600)
b += txt(50, 326, "견준 상대는 합성곱 층마다 커널이 절반인 1-GPU 망", 11.5, INK2, anchor="start")
b += txt(50, 352, "GTX 580 한 장의 메모리가 3GB 라 크기가 거기 묶인다", 11.5, INK2, anchor="start")

b += box(446, 254, 394, 122, "#FFFFFF", NO, 1.3, 8)
b += txt(643, 278, "논문이 스스로 적는 치우침", 12.5, NO, weight=600)
b += txt(466, 302, "1-GPU 망의 마지막 합성곱 층은 절반으로 줄이지", 11.5, INK2, anchor="start")
b += txt(466, 320, "않았다(파라미터 수를 맞추려고).", 11.5, INK2, anchor="start")
b += txt(466, 346, "그래서 이 비교는 1-GPU 쪽에 유리하게 치우쳐 있다", 11.5, NO, anchor="start", weight=600)
b += txt(466, 366, "— 각주에 저자들이 직접 적는다.", 10.8, MUTED, anchor="start")
svg("fig04_two_gpus", 866, 396, b,
    "커널을 GPU 두 장에 나누고 conv3 에서만 서로 넘나든다")


# ── 5. LRN ────────────────────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("e1", REV)
b += txt(430, 28, "3.3 국소 반응 정규화 — 같은 자리에서 커널끼리 겨룬다", 14.5, INK, weight=600)

b += box(24, 50, 420, 230, "#F4F6F4", LINE, 1.2, 10)
b += txt(234, 74, "이웃한 커널 지도 n = 5 장", 12.5, INK, weight=600)
for k in range(9):
    x = 60 + k * 42
    on = 2 <= k <= 6
    b += box(x, 96, 34, 76, (REV_SOFT if on else "#FFFFFF"), (REV if on else LINE), 1.1, 3)
    b += circ(x + 17, 134, 6, (REV if k == 4 else "#FFFFFF"), (REV if on else LINE), 1.0)
    b += txt(x + 17, 186, str(k), 10, MUTED)
b += txt(234, 206, "가운데 하나(i)를 그 좌우 두 장씩과 함께 본다", 11.5, INK2)
b += txt(234, 228, "같은 자리 (x, y) 에서만 — 한 지도 안의 이웃 픽셀이 아니다", 11.5, NO, weight=600)
b += txt(234, 258, "커널 지도의 순서는 학습 전에 정해지는 임의의 것이다", 11, MUTED)

b += box(460, 50, 380, 230, "#F4F6F4", LINE, 1.2, 10)
b += txt(650, 74, "상수와 이득", 12.5, INK, weight=600)
consts = [("k", "2"), ("n", "5"), ("알파", "10^-4"), ("베타", "0.75")]
for i, (k, v) in enumerate(consts):
    x = 500 + (i % 2) * 180
    y = 104 + (i // 2) * 44
    b += box(x, y - 22, 150, 36, "#FFFFFF", INK2, 1.0, 5)
    b += txt(x + 40, y + 2, k, 12, INK2, weight=600)
    b += txt(x + 110, y + 2, v, 12.5, INK, weight=600)
b += txt(650, 206, "검증 집합으로 골랐다고만 적혀 있다 —", 11, MUTED)
b += txt(650, 222, "어느 범위에서 몇 개를 훑었는지가 없다", 11, NO, weight=600)
b += box(480, 236, 340, 34, "#FFFFFF", REV, 1.2, 5)
b += txt(650, 258, "top-1 -1.4% · top-5 -1.2%", 12.5, REV, weight=600)

b += box(28, 294, 812, 76, "#FFFFFF", INK, 1.3, 8)
b += txt(434, 318, "CIFAR-10 네 층 망에서도 확인했다고 적는다 — 정규화 없이 13%, 넣으면 11%.", 12.5, INK, weight=600)
b += txt(434, 342, "다만 그 망은 자리가 모자라 자세히 적지 못한다고 각주에 적혀 있다(코드로 대신한다).", 11.5, INK2)
b += txt(434, 362, "평균을 빼지 않으므로 「밝기 정규화」라 부르는 편이 더 맞다고 논문이 덧붙인다.", 11, MUTED)
svg("fig05_lrn", 866, 386, b,
    "LRN 은 같은 자리에서 이웃한 커널 지도 다섯과 겨룬다. 상수 넷과 이득")


# ── 6. 겹치는 풀링 ────────────────────────────────────────────────────────
b = txt(430, 28, "3.4 겹치는 풀링 — s < z", 14.5, INK, weight=600)

CELL = 26
for panel, (s_, z_, title, col, soft) in enumerate([
        (2, 2, "보통 풀링  s = 2, z = 2", FWD, FWD_SOFT),
        (2, 3, "겹치는 풀링  s = 2, z = 3", REV, REV_SOFT)]):
    px = 30 + panel * 420
    b += box(px, 50, 400, 210, "#F4F6F4", LINE, 1.2, 10)
    b += txt(px + 200, 74, title, 12.5, col, weight=600)
    gx, gy = px + 60, 96
    b += grid(gx, gy, CELL, 9, 4, LINE, 0.6)
    for i in range(4):
        x0 = gx + i * s_ * CELL
        b += box(x0, gy + (0 if i % 2 == 0 else 8), z_ * CELL, 2 * CELL, soft, col, 1.6, 3, op="0.55")
    b += txt(px + 200, 216, ("창이 서로 닿지 않는다" if s_ == z_ else "이웃한 두 창이 한 줄씩 겹친다"),
             11.5, INK2)
    b += txt(px + 200, 240, "출력 크기는 둘이 같다", 11, MUTED)

b += box(30, 274, 790, 90, "#FFFFFF", INK, 1.3, 8)
b += txt(425, 298, "이득: top-1 -0.4% · top-5 -0.3%. 견준 상대가 출력 크기가 같은 s = 2, z = 2 다.", 12.5, INK, weight=600)
b += txt(425, 322, "그리고 관찰 하나 — 겹치는 풀링을 쓴 모델이 과적합되기가 더 어렵더라고 적는다(논문의 말: slightly).", 12, INK2)
b += txt(425, 348, "LeNet 의 부분 표본 뽑기와 달리 최댓값 풀링에는 학습되는 계수와 바이어스가 없다. 그 자리를 이 논문은 따로 변호하지 않는다.",
         11, MUTED)
svg("fig06_overlapping_pool", 850, 380, b,
    "s=2, z=2 와 s=2, z=3 의 차이와 이득 -0.4 / -0.3")


# ── 7. 파라미터가 어디에 있나 ─────────────────────────────────────────────
FC_SHARE = 100.0 * sum(v for n, v in params if n.startswith("fc")) / P_TOTAL
b = txt(430, 28, "파라미터 6천만의 %.0f%%%% 가 완전연결 층 셋에 있다" % FC_SHARE, 14.5, INK, weight=600)
vmax = max(v for _n, v in params)
for i, (n, v) in enumerate(params):
    yy = 60 + i * 34
    col = OK if n.startswith("fc") else REV
    soft = "#E4EFE4" if n.startswith("fc") else REV_SOFT
    b += bar_h(180, yy, 22, v, vmax, col, soft, n, "", 12, 470, "{:,}".format)
    b += txt(830, yy + 16, "%.1f%%" % (100.0 * v / P_TOTAL), 11.5, INK2, anchor="end")
b += txt(830, 46, "전체 대비", 10.5, MUTED, anchor="end")

yb = 60 + len(params) * 34 + 8
b += box(30, yb, 810, 108, "#FFFFFF", INK, 1.3, 8)
b += txt(435, yb + 26, "합계 %s — 초록의 「6천만」과 맞는다. (층별로 더한 것은 내가 한 셈이다)"
         % format(P_TOTAL, ","), 12.5, INK, weight=600)
b += txt(435, yb + 50, "합성곱 다섯을 다 더해도 %s 로 전체의 %.1f%% 다. 그런데 논문은 "
         % (format(sum(v for n, v in params if n.startswith('conv')), ","),
            100.0 * sum(v for n, v in params if n.startswith('conv')) / P_TOTAL), 11.5, INK2)
b += txt(435, yb + 70, "「합성곱 층 하나를 빼면 top-1 이 약 2% 나빠진다」고 적는다 — 그 층 하나가 파라미터의 1% 도 안 되는데도.", 11.5, INK2)
b += txt(435, yb + 94, "드롭아웃을 fc6 · fc7 에만 건 이유도 이 그림에서 읽힌다.", 11.5, OK, weight=600)
svg("fig07_params", 866, yb + 132, b,
    "층별 파라미터 막대. fc6 하나가 전체의 62%")


# ── 8. 데이터 늘리기 ──────────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("h1", REV)
b += txt(430, 28, "4.1 데이터 늘리기 둘 — 디스크에 저장하지 않는다", 14.5, INK, weight=600)

b += box(24, 50, 420, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(234, 74, "하나. 자르기와 좌우 뒤집기", 12.5, REV, weight=600)
b += box(70, 92, 130, 130, "#FFFFFF", INK2, 1.2, 4)
b += txt(135, 232, "256 x 256", 11, MUTED)
for k, (dx, dy) in enumerate([(6, 6), (26, 26), (46, 10)]):
    b += box(70 + dx, 92 + dy, 78, 78, REV_SOFT, REV, 1.3, 3, op="0.75")
b += txt(135, 160, "224", 11, REV, weight=600)
b += txt(300, 120, "무작위 조각", 11.5, INK2)
b += txt(300, 142, "+ 좌우 뒤집기", 11.5, INK2)
b += box(250, 160, 160, 44, "#FFFFFF", REV, 1.3, 6)
b += txt(330, 188, "2048 배", 14, REV, weight=600)
b += txt(300, 222, "다만 서로 크게 의존하는", 10.8, MUTED)
b += txt(300, 238, "사례들이라고 논문이 덧붙인다", 10.8, MUTED)
b += txt(234, 268, "시험할 때는 네 모퉁이 + 가운데 다섯 조각과", 11, INK2)
b += txt(234, 286, "각각의 뒤집기, 곧 열 장의 소프트맥스를 평균한다", 11, INK2)

b += box(460, 50, 380, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(650, 74, "둘. RGB 세기 흔들기", 12.5, REV, weight=600)
b += txt(650, 100, "학습 집합 전체의 RGB 값에 주성분 분석을 돌려", 11, INK2)
b += txt(650, 118, "이미지마다 주성분 방향으로 흔들어 더한다", 11, INK2)
b += box(490, 134, 320, 40, "#FFFFFF", INK, 1.2, 5)
b += txt(650, 160, "[p1 p2 p3][a1 L1, a2 L2, a3 L3]^T", 12.5, INK, weight=600)
b += txt(650, 194, "a 는 평균 0 · 표준편차 0.1 에서 뽑고,", 11, INK2)
b += txt(650, 212, "한 이미지의 모든 픽셀에 같은 값을 쓴다", 11, INK2)
b += box(500, 226, 300, 40, "#FFFFFF", REV, 1.2, 5)
b += txt(650, 252, "top-1 이 1% 넘게 내려간다", 12.5, REV, weight=600)
b += txt(650, 286, "노리는 것: 물체는 조명의 세기와 색이 바뀌어도 그대로다", 10.8, MUTED)

b += box(28, 314, 812, 66, "#FFFFFF", INK, 1.3, 8)
b += txt(434, 338, "GPU 가 앞 묶음을 배우는 동안 CPU 가 파이썬으로 만들어내므로 사실상 계산이 공짜라고 적는다.", 12.5, INK, weight=600)
b += txt(434, 362, "열 조각 평균을 하지 않으면 각주의 값은 top-1 39.0% · top-5 18.3% 다(하면 37.5% · 17.0%).", 12, INK2)
svg("fig08_augmentation", 866, 396, b,
    "224 조각과 좌우 뒤집기로 2048배, 그리고 RGB 주성분 흔들기")


# ── 9. 드롭아웃 ───────────────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("i1", OK)
b += txt(430, 28, "4.2 드롭아웃 — fc6 과 fc7 에만", 14.5, INK, weight=600)

for panel, (title, dropped, col) in enumerate([("학습할 때", [1, 4], OK), ("시험할 때", [], FWD)]):
    px = 30 + panel * 300
    b += box(px, 52, 280, 208, "#F4F6F4", LINE, 1.2, 10)
    b += txt(px + 140, 76, title, 12.5, col, weight=600)
    for li, n in enumerate([5, 6, 5]):
        for k in range(n):
            x = px + 140 + (k - (n - 1) / 2.0) * 34
            y = 108 + li * 52
            off = (li == 1 and k in dropped)
            b += circ(x, y, 11, ("#FFFFFF" if off else (NODE if li != 1 else "#E4EFE4")),
                      (LINE if off else (col if li == 1 else INK2)), 1.1)
            if off:
                b += line(x - 8, y - 8, x + 8, y + 8, NO, 1.6)
                b += line(x - 8, y + 8, x + 8, y - 8, NO, 1.6)
    b += txt(px + 140, 240, ("확률 0.5 로 0 으로 만든다" if panel == 0 else "전부 쓰되 출력에 0.5 를 곱한다"),
             11.5, INK2)

b += box(620, 52, 220, 208, "#F4F6F4", LINE, 1.2, 10)
b += txt(730, 76, "논문이 적는 값", 12.5, INK, weight=600)
b += box(640, 92, 180, 52, "#FFFFFF", OK, 1.2, 6)
b += txt(730, 114, "수렴까지의 반복 수", 11, INK2)
b += txt(730, 134, "두 배 (논문의 말: roughly)", 12, OK, weight=600)
b += box(640, 156, 180, 52, "#FFFFFF", NO, 1.2, 6)
b += txt(730, 178, "빼면 얼마인가", 11, INK2)
b += txt(730, 198, "숫자가 없다", 13, NO, weight=600)
b += txt(730, 232, "「없으면 과적합이 상당했다」", 10.8, MUTED)
b += txt(730, 248, "까지만 적혀 있다", 10.8, MUTED)

b += box(28, 274, 812, 66, "#FFFFFF", INK, 1.3, 8)
b += txt(434, 298, "노리는 것은 유닛끼리의 복잡한 공적응을 깨는 것이다 — 특정한 다른 유닛이 있다고 기대할 수 없게 만든다.", 12.5, INK, weight=600)
b += txt(434, 322, "모델 여럿을 묶는 효과를 학습 비용 두 배로 얻는 방법이라고 적는다. 시험할 때의 0.5 곱하기는 기하 평균의 근사다.", 11.5, INK2)
svg("fig09_dropout", 866, 356, b,
    "드롭아웃의 학습과 시험 동작, 그리고 논문에 숫자가 없는 자리")


# ── 10. 결과 ──────────────────────────────────────────────────────────────
b = txt(450, 28, "결과 — 표 1(ILSVRC-2010)과 표 2(ILSVRC-2012)", 14.5, INK, weight=600)

b += txt(230, 58, "표 1 · ILSVRC-2010 시험 집합", 12.5, INK, weight=600)
rows10 = [("희소 부호화 여섯 평균", 47.1, 28.2, MUTED, "#E8E8E8"),
          ("SIFT + 피셔 벡터 둘 평균", 45.7, 25.7, MUTED, "#E8E8E8"),
          ("이 논문의 CNN", 37.5, 17.0, REV, REV_SOFT)]
for i, (n, t1, t5, col, soft) in enumerate(rows10):
    yy = 78 + i * 46
    b += bar_h(250, yy, 18, t1, 50, col, soft, n, " %", 11.5, 190, "%.1f")
    b += bar_h(250, yy + 20, 18, t5, 50, col, soft, "", " %", 11.5, 190, "%.1f")
b += txt(250, 218, "위 막대가 top-1, 아래가 top-5", 10.5, MUTED, anchor="start")

b += txt(700, 58, "표 2 · ILSVRC-2012 (top-5)", 12.5, INK, weight=600)
rows12 = [("SIFT + FV (2등, 시험)", 26.2, MUTED, "#E8E8E8"),
          ("CNN 하나 (검증)", 18.2, FWD, FWD_SOFT),
          ("CNN 다섯 평균", 16.4, FWD, FWD_SOFT),
          ("CNN 하나* (검증)", 16.6, OK, "#E4EFE4"),
          ("CNN 일곱* (시험)", 15.3, REV, REV_SOFT)]
for i, (n, v, col, soft) in enumerate(rows12):
    yy = 80 + i * 30
    b += bar_h(700, yy, 20, v, 28, col, soft, n, " %", 11.5, 180, "%.1f")
b += txt(700, 238, "* 는 ImageNet 2011 가을 판 전체(1,500만 장 · 22,000 부류)로", 10.5, MUTED, anchor="start")
b += txt(700, 254, "   먼저 배운 뒤 미세조정한 것이고, 여섯째 합성곱 층이 하나 더 있다", 10.5, MUTED, anchor="start")

b += box(30, 272, 900, 96, "#FFFFFF", INK, 1.3, 8)
b += txt(480, 296, "표 1 의 17.0% 와 표 2 의 15.3% 를 「좋아졌다」로 이어 읽으면 안 된다 — 데이터가 다르다.", 12.5, NO, weight=600)
b += txt(480, 320, "2010 은 시험 라벨이 공개된 유일한 판이고, 2012 는 시험 라벨이 없어 검증 값을 섞어 적는다(둘의 차이가 0.1% 를 넘은 적이 없다고 적는다).", 11.3, INK2)
b += txt(480, 346, "ImageNet 2009 가을 판(10,184 부류 · 890만 장)에서는 top-1 67.4% · top-5 40.9% 이고 그전 최고가 78.1% · 60.9% 였다.", 11.3, INK2)
svg("fig10_results", 950, 384, b,
    "ILSVRC-2010 에서 37.5 / 17.0, ILSVRC-2012 에서 top-5 15.3")


# ── 11. 깊이 ──────────────────────────────────────────────────────────────
b = txt(430, 28, "「깊이가 실제로 중요하다」가 얹혀 있는 숫자", 14.5, INK, weight=600)

b += box(24, 52, 400, 230, "#F4F6F4", LINE, 1.2, 10)
b += txt(224, 76, "논문이 두 번 적는 말", 12.5, INK, weight=600)
b += box(48, 94, 352, 56, "#FFFFFF", REV, 1.2, 6)
b += txt(224, 116, "합성곱 층을 아무거나 하나 빼면", 11.5, INK2)
b += txt(224, 138, "top-1 이 약 2% 나빠진다", 13, REV, weight=600)
b += box(48, 162, 352, 56, "#FFFFFF", FWD, 1.2, 6)
b += txt(224, 184, "그 층 하나가 모델 파라미터의", 11.5, INK2)
b += txt(224, 206, "1% 도 안 되는데도 그렇다", 13, FWD, weight=600)
b += txt(224, 244, "합성곱 다섯을 다 더해도 전체의 %.1f%% 다"
         % (100.0 * sum(v for n, v in params if n.startswith('conv')) / P_TOTAL), 11.5, INK2)
b += txt(224, 266, "(이 그림에서 센 값이다)", 10.5, MUTED)

b += box(440, 52, 400, 230, "#F4F6F4", LINE, 1.2, 10)
b += txt(640, 76, "그런데 없는 것", 12.5, NO, weight=600)
for i, t in enumerate(["어느 층을 뺐는지", "몇 번 돌렸는지", "파라미터 수를 맞췄는지",
                       "층을 더 뺐을 때의 곡선"]):
    b += txt(470, 108 + i * 30, "· " + t, 12, INK2, anchor="start")
b += box(460, 228, 360, 40, "#FFFFFF", NO, 1.2, 6)
b += txt(640, 254, "표가 없고 숫자 한 개뿐이다", 12.5, NO, weight=600)

b += box(28, 296, 812, 84, "#FFFFFF", INK, 1.3, 8)
b += txt(434, 320, "그림 3 의 관찰 하나 — GPU 1 쪽 커널은 대체로 색과 무관하고 GPU 2 쪽은 대체로 색에 특화된다.", 12.5, INK, weight=600)
b += txt(434, 344, "이 갈림이 실행할 때마다 나타나고 가중치 초기화와 무관하다고 적는다(GPU 번호가 바뀌는 것 빼고).", 11.5, INK2)
b += txt(434, 368, "곧 3.2 절의 끊어 놓은 연결이 만든 것이다 — 구조가 특징의 분업을 강제한 자리다.", 11.5, FWD, weight=600)
svg("fig11_depth", 866, 396, b,
    "깊이가 중요하다는 결론과 그 근거에 없는 것들, 그리고 GPU 별 필터 특화")


# ── 12. LeNet 과 맞춰 보기 ────────────────────────────────────────────────
b = txt(430, 28, "LeNet-5 (1998) 와 AlexNet (2012)", 14.5, INK, weight=600)
rows12b = [
    ("학습되는 층", "7", "8", False),
    ("학습되는 값", "60,000", "60,965,224", True),
    ("학습 사례", "60,000", "1,200,000", True),
    ("부류", "10", "1,000", True),
    ("비선형", "1.7159 tanh(2/3 a)", "ReLU", True),
    ("해상도 깎기", "부분 표본(학습되는 계수 있음)", "겹치는 최댓값 풀링(없음)", True),
    ("출력층", "유클리드 RBF (고정)", "1000-way 소프트맥스", True),
    ("층 사이 희소 연결", "표 I", "GPU 둘로 쪼개기", False),
    ("장비와 시간", "CPU 하나 · 2~3 일", "GPU 둘 · 5~6 일", False),
]
y0 = 58
b += box(24, y0 - 14, 816, 36, "#F4F6F4", LINE, 1.0, 6)
b += txt(150, y0 + 8, "자리", 12, INK, weight=600)
b += txt(400, y0 + 8, "LeNet-5 (1998)", 12, FWD, weight=600)
b += txt(660, y0 + 8, "AlexNet (2012)", 12, REV, weight=600)
for i, (name, a, c, changed) in enumerate(rows12b):
    yy = y0 + 44 + i * 30
    b += txt(150, yy, name, 11.5, INK2)
    b += txt(400, yy, a, 11.5, FWD)
    b += txt(660, yy, c, 11.5, REV, weight=(600 if changed else None))
    if i < len(rows12b) - 1:
        b += line(40, yy + 10, 824, yy + 10, LINE, 0.7)

b += box(24, 330, 400, 100, "#FFFFFF", INK, 1.2, 8)
b += txt(224, 354, "같은 동기가 이름만 바뀐 자리", 12.5, INK, weight=600)
b += txt(44, 378, "표 I 의 비완전 연결도, GPU 둘로 쪼개기도", 11.5, INK2, anchor="start")
b += txt(44, 398, "계산 예산을 지키면서 대칭을 깨는 장치다.", 11.5, INK2, anchor="start")
b += txt(44, 420, "1998 은 연결 수 때문에, 2012 는 메모리 3GB 때문에.", 11, MUTED, anchor="start")

b += box(440, 330, 400, 100, "#FFFFFF", NO, 1.2, 8)
b += txt(640, 354, "두 논문 모두 답하지 않은 자리", 12.5, NO, weight=600)
b += txt(460, 378, "최댓값 풀링이 부분 표본 뽑기를 왜 대신하는가 —", 11.5, INK2, anchor="start")
b += txt(460, 398, "AlexNet 도 겹치게 할지만 재고 그 선택은 변호하지 않는다.", 11.5, INK2, anchor="start")
b += txt(460, 420, "파라미터가 많은 망이 왜 되는가도 여전히 열려 있다.", 11, MUTED, anchor="start")
svg("fig12_lenet_vs_alexnet", 866, 448, b,
    "1998 과 2012 사이에 무엇이 그대로이고 무엇이 바뀌었는가")


# ── 13. 한계와 잴 것 ──────────────────────────────────────────────────────
b = txt(440, 28, "이 논문이 스스로 적은 한계와, 내가 재 보려는 자리", 14.5, INK, weight=600)

b += box(24, 48, 426, 330, "#F4F6F4", LINE, 1.2, 10)
b += txt(237, 72, "논문이 적은 한계", 13, NO, weight=600)
lim = [
    "망 크기가 GPU 메모리와 학습 시간에 묶여 있다",
    "비지도 사전학습을 쓰지 않았다(도움될 것으로 본다)",
    "사람의 시각 경로에 견주면 자릿수가 여러 번 남았다",
    "정지 영상만 다룬다 — 영상으로 가고 싶다",
    "두 GPU 비교가 1-GPU 쪽에 유리하게 치우쳐 있다",
    "데이터 늘리기 2048 배는 서로 크게 의존한다",
    "CIFAR-10 쪽 망은 자리가 모자라 적지 못했다",
]
for i, t in enumerate(lim):
    yy = 100 + i * 36
    b += txt(46, yy, "%d." % (i + 1), 11.5, NO, anchor="start", weight=600)
    b += txt(70, yy, t, 11.5, INK2, anchor="start")
b += txt(237, 362, "다섯째와 여섯째는 저자들이 직접 적어 둔 치우침이다", 10.8, MUTED)

b += box(462, 48, 384, 330, "#F4F6F4", LINE, 1.2, 10)
b += txt(654, 72, "CIFAR-10 에서 잴 것 다섯", 13, REV, weight=600)
mine = [
    ("A", "ReLU 가 tanh 보다 몇 배 빠른가"),
    ("B", "LRN 을 넣고 빼면 얼마인가 (13% 대 11%)"),
    ("C", "겹치는 풀링 대 안 겹치는 풀링"),
    ("D", "드롭아웃을 빼면 얼마인가 (논문에 없다)"),
    ("E", "넷을 하나씩 켜고 끈 값을 한 표에"),
]
for i, (k, t) in enumerate(mine):
    yy = 110 + i * 54
    b += box(482, yy - 22, 344, 44, "#FFFFFF", REV, 1.1, 6)
    b += txt(502, yy + 4, k, 14, REV, weight=600)
    b += txt(522, yy + 4, t, 11.2, INK2, anchor="start")
b += txt(654, 368, "A 와 B 는 논문 자신이 CIFAR-10 에서 확인한 자리다", 10.8, MUTED)
svg("fig13_limits", 876, 398, b,
    "논문이 적은 한계 일곱과 CIFAR-10 에서 잴 다섯 자리")


print("끝났다.")
