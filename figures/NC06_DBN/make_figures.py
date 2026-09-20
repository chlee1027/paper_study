# -*- coding: utf-8 -*-
"""DBN 노트(Neural Computation 2006)의 그림 열넷을 만든다.

색과 글꼴은 퍼셉트론 · 역전파 · DDPM 노트의 그림과 맞췄다 — 저장소의 노트들이 한 벌로
읽히게 하려는 것이다. 그림을 고치려면 이 파일을 고쳐 다시 돌린다.
바깥 데이터를 읽지 않으므로 어디서나 돈다.

  python make_figures.py

그림 1 의 기울기 곱, 그림 3 의 확률, 그림 8 의 막대 길이는 이 파일이 직접 계산한다.
계산한 값은 돌릴 때 화면에도 찍는다.
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


# ── 1. 역전파가 남긴 빈칸 — 깊어지면 기울기가 곱해져 줄어든다 ──────────────
b = '<defs>%s%s</defs>' % (arrow("a1", FWD), arrow("a2", REV))
b += txt(410, 28, "역전파가 남긴 빈칸 — 층을 쌓으면 아래층까지 기울기가 안 내려온다", 14, INK, weight=600)

b += box(24, 46, 380, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(214, 70, "로지스틱의 기울기는 최대가 0.25 다", 12.5, FWD, weight=600)
ax0, ay0, aw, ah = 60, 96, 300, 130
b += line(ax0, ay0 + ah, ax0 + aw, ay0 + ah, INK2, 1.2)
b += line(ax0 + aw / 2, ay0, ax0 + aw / 2, ay0 + ah, LINE, 1.0)
pts = []
for i in range(0, 121):
    x = -6 + 12.0 * i / 120.0
    g = sigmoid(x) * (1 - sigmoid(x))
    pts.append("%.1f,%.1f" % (ax0 + aw * (x + 6) / 12.0, ay0 + ah - ah * (g / 0.25) * 0.88))
b += '<polyline points="%s" fill="none" stroke="%s" stroke-width="2.2"/>' % (" ".join(pts), REV)
b += line(ax0, ay0 + ah - ah * 0.88, ax0 + aw, ay0 + ah - ah * 0.88, MUTED, 1.0, dash="4 4")
b += txt(ax0 + 30, ay0 + ah - ah * 0.88 - 8, "0.25", 11.5, REV, weight=600)
b += txt(ax0 + aw / 2, ay0 + ah + 18, "유닛이 받는 총입력", 11.5, MUTED)
b += txt(214, 268, "가장 잘 받아도 한 층을 지날 때마다 4분의 1 이하로 줄어든다", 11.5, INK2)

b += box(418, 46, 380, 250, "#F4F6F4", LINE, 1.2, 10)
b += txt(608, 70, "층마다 곱하면", 12.5, REV, weight=600)
vals = [(1, 0.25), (2, 0.0625), (3, 0.015625), (4, 0.00390625), (5, 0.0009765625)]
for n, v in enumerate(vals):
    y = 100 + n * 36
    L = 300 * (v[1] / 0.25) ** 0.34
    b += txt(452, y + 4, str(v[0]) + "층", 12, INK2, anchor="end")
    b += box(462, y - 9, max(2.0, L), 18, REV_SOFT, REV, 1.0, 3)
    b += txt(470 + max(2.0, L), y + 4, format(v[1], ".7f").rstrip("0"), 11.5, INK2, anchor="start")
print("  기울기 곱:", ["%.7f" % v for _n, v in vals])
b += txt(608, 276, "다섯 층이면 0.00098 — 아래층 가중치가 사실상 안 움직인다", 11.5, INK2)

b += box(28, 306, 770, 92, "#FFFFFF", INK, 1.3, 8)
b += txt(413, 330, "역전파(1986)는 은닉 유닛에 몫을 나누는 길을 열었지만, 그 몫은 위층에서 곱해져 내려온다.", 12.5, INK, weight=600)
b += txt(413, 354, "이 논문은 기울기를 더 잘 흘리는 대신, 아래층을 위층과 따로 · 정답 없이 먼저 배우는 길을 낸다.", 12, INK2)
b += txt(413, 380, "곧 「깊은 망을 한 번에 배우지 않는다」가 이 논문의 출발점이다.", 12, REV, weight=600)
svg("fig01_gap", 820, 414, b,
    "로지스틱의 기울기는 최대 0.25 이고 층마다 곱해져 다섯 층이면 0.00098 이 된다. 이 논문은 층을 따로 배우는 길을 낸다")


# ── 2. 방향이 있는 망과 없는 망 ───────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("b1", FWD), arrow("b2", REV))
b += txt(410, 28, "방향이 있는 믿음망과 방향이 없는 망 — 무엇이 쉬운가", 14, INK, weight=600)

b += box(24, 46, 372, 300, "#F4F6F4", LINE, 1.2, 10)
b += txt(210, 70, "방향 있는 믿음망 (directed belief net)", 12.5, FWD, weight=600)
for i, x in enumerate([110, 175, 240, 305]):
    b += circ(x, 120, 16, FWD_SOFT, FWD, 1.2)
for i, x in enumerate([142, 207, 272]):
    b += circ(x, 230, 16, NODE, INK, 1.2)
for x in [110, 175, 240, 305]:
    for x2 in [142, 207, 272]:
        b += line(x, 136, x2, 214, MUTED, 0.9, marker="b1", op="0.5")
b += txt(210, 100, "숨은 층", 11.5, MUTED)
b += txt(210, 262, "보이는 층", 11.5, MUTED)
b += box(44, 282, 332, 50, "#FFFFFF", FWD, 1.2, 6)
b += txt(210, 302, "생성은 쉽다 — 위에서 아래로 한 번 내려오면 된다", 11.5, INK2)
b += txt(210, 322, "추론은 어렵다 — 데이터를 보면 숨은 원인들이 얽힌다", 11.5, NO, weight=600)

b += box(412, 46, 384, 300, "#F4F6F4", LINE, 1.2, 10)
b += txt(604, 70, "방향 없는 망 · 제한 볼츠만 기계 (RBM)", 12.5, REV, weight=600)
for x in [500, 565, 630, 695]:
    b += circ(x, 120, 16, REV_SOFT, REV, 1.2)
for x in [532, 597, 662]:
    b += circ(x, 230, 16, NODE, INK, 1.2)
for x in [500, 565, 630, 695]:
    for x2 in [532, 597, 662]:
        b += line(x, 136, x2, 214, MUTED, 0.9, op="0.5")
b += txt(604, 100, "숨은 층 (층 안 연결 없음)", 11.5, MUTED)
b += txt(604, 262, "보이는 층 (층 안 연결 없음)", 11.5, MUTED)
b += box(432, 282, 344, 50, "#FFFFFF", REV, 1.2, 6)
b += txt(604, 302, "추론은 쉽다 — 한 층을 보면 다른 층이 서로 독립이다", 11.5, OK, weight=600)
b += txt(604, 322, "학습은 어렵다 — 평형 분포에서 표본을 뽑아야 한다", 11.5, NO, weight=600)

b += box(28, 356, 768, 62, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 380, "이 논문은 둘을 잇는다 — 방향 있는 망의 한 층을 방향 없는 망 하나로 바꿔 배우고, 그것을 층마다 되풀이한다.", 12.5, INK, weight=600)
b += txt(412, 404, "잇는 자리를 만드는 것이 「상보 사전분포」다(그림 5).", 12, INK2)
svg("fig02_directed_vs_undirected", 820, 434, b,
    "방향 있는 믿음망은 생성이 쉽고 추론이 어렵다. RBM 은 추론이 쉽고 학습이 어렵다. 이 논문은 둘을 잇는다")


# ── 3. 설명해치우기 (논문 그림 2) ─────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("c1", INK2)
b += txt(410, 28, "설명해치우기 (explaining away) — 논문 그림 2 를 숫자로 따라가 보면", 14, INK, weight=600)

b += circ(240, 100, 34, FWD_SOFT, FWD, 1.4)
b += txt(240, 96, "지진", 12.5, INK, weight=600)
b += txt(240, 113, "치우침 -10", 10.5, MUTED)
b += circ(580, 100, 34, FWD_SOFT, FWD, 1.4)
b += txt(580, 96, "트럭", 12.5, INK, weight=600)
b += txt(580, 113, "치우침 -10", 10.5, MUTED)
b += circ(410, 232, 36, NODE, INK, 1.6)
b += txt(410, 228, "집이", 12.5, INK, weight=600)
b += txt(410, 245, "흔들림", 12.5, INK, weight=600)
b += line(262, 128, 386, 204, INK2, 1.6, marker="c1")
b += line(558, 128, 434, 204, INK2, 1.6, marker="c1")
b += txt(304, 178, "+20", 12, REV, weight=600)
b += txt(516, 178, "+20", 12, REV, weight=600)
b += txt(410, 288, "치우침 -20", 11, MUTED)

b += box(28, 316, 768, 156, "#FFFFFF", INK, 1.3, 8)
b += txt(52, 340, "집이 흔들린 것을 보았다. 무엇이 켜졌다고 볼 것인가.", 12.5, INK, weight=600, anchor="start")
rows = [("둘 다 꺼짐", "총입력 -20", "흔들릴 확률이 e^-20 배로 낮다 — 관찰과 안 맞는다", NO),
        ("지진만 켜짐", "총입력 -20 + 20 = 0", "흔들릴 확률이 반반 — 관찰을 잘 설명한다", OK),
        ("트럭만 켜짐", "총입력 -20 + 20 = 0", "마찬가지로 잘 설명한다", OK),
        ("둘 다 켜짐", "총입력 +20", "설명은 되지만 둘이 함께 일어날 확률이 e^-10 x e^-10 = e^-20", NO)]
for i, (a, c, d, col) in enumerate(rows):
    y = 366 + i * 26
    b += txt(60, y, a, 11.5, INK, anchor="start", weight=600)
    b += txt(178, y, c, 11.5, INK2, anchor="start")
    b += txt(330, y, d, 11.5, col, anchor="start")
print("  설명해치우기: 둘 다 켜질 확률 e^-20 = %.3e" % math.exp(-20))

b += box(28, 484, 768, 76, "#F4F6F4", REV, 1.3, 8)
b += txt(412, 508, "그래서 지진이 켜지면 트럭은 꺼지는 쪽으로 기운다 — 원래 서로 무관하던 둘이 관찰 뒤에 반대로 묶인다.", 12.5, INK, weight=600)
b += txt(412, 532, "이것이 설명해치우기다. 숨은 변수들이 얽히므로 사후분포를 변수마다 따로 적을 수 없고, 그래서 추론이 어렵다.", 12, INK2)
svg("fig03_explaining_away", 820, 576, b,
    "지진과 트럭은 원래 무관하지만 집이 흔들린 것을 관찰하면 반대로 묶인다. 이것이 설명해치우기이고 추론을 어렵게 만든다")


# ── 4. 사후분포가 곱으로 안 쪼개진다 ──────────────────────────────────────
b = txt(410, 28, "곱꼴 사후분포 (factorial posterior) — 되면 쉽고 안 되면 어렵다", 14, INK, weight=600)

b += box(24, 46, 372, 224, "#F4F6F4", OK, 1.3, 10)
b += txt(210, 70, "곱꼴이면", 12.5, OK, weight=600)
b += txt(210, 104, E("P(h_1, h_2, h_3 | v)"), 14, INK)
b += txt(210, 130, "=", 13, MUTED)
b += txt(210, 158, E("P(h_1|v) x P(h_2|v) x P(h_3|v)"), 14, OK, weight=600)
for i, x in enumerate([110, 175, 240, 305]):
    b += circ(x, 206, 13, NODE, LINE, 1.0)
b += txt(210, 246, "숨은 유닛마다 따로 정하면 된다 — 한 번 훑으면 끝난다", 11.5, INK2)

b += box(412, 46, 384, 224, "#F4F6F4", NO, 1.3, 10)
b += txt(604, 70, "안 되면", 12.5, NO, weight=600)
b += txt(604, 104, E("P(h_1, h_2, h_3 | v)"), 14, INK)
b += txt(604, 130, "!=", 13, MUTED)
b += txt(604, 158, "따로따로의 곱", 14, NO, weight=600)
for i, x in enumerate([500, 565, 630, 695]):
    b += circ(x, 206, 13, NODE, LINE, 1.0)
for a2, c2 in [(500, 565), (565, 630), (630, 695), (500, 630)]:
    b += path("M %d 193 Q %d 172 %d 193" % (a2, (a2 + c2) / 2, c2), NO, "none", 1.4)
b += txt(604, 246, "조합을 통째로 봐야 한다 — 유닛 n 개면 경우가 2^n 가지다", 11.5, NO)

b += box(28, 284, 768, 108, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 308, "지금까지의 길 둘, 그리고 이 논문의 길 하나.", 12.5, INK, weight=600)
b += txt(52, 334, "MCMC — 사후분포에서 표본을 뽑는다. 맞지만 오래 걸린다.", 12, INK2, anchor="start")
b += txt(52, 356, "변분법 — 곱꼴인 가짜 분포로 대신한다. 빠르지만 근사가 나쁠 수 있고, 특히 가장 깊은 층에서 나쁘다.", 12, INK2, anchor="start")
b += txt(52, 380, "이 논문 — 사후분포가 애초에 곱꼴이 되도록 모델을 짓는다. 근사가 아니라 정확해진다.", 12, REV, anchor="start", weight=600)
svg("fig04_posterior_not_factorial", 820, 406, b,
    "사후분포가 곱꼴이면 유닛마다 따로 정할 수 있고 아니면 조합을 통째로 봐야 한다. 이 논문은 곱꼴이 되도록 모델을 짓는다")


# ── 5. 상보 사전분포 ──────────────────────────────────────────────────────
b = txt(410, 28, "상보 사전분포 (complementary prior) — 이 논문의 알맹이", 14, INK, weight=600)
b += txt(410, 52, "가능도가 만드는 상관을 사전분포가 정확히 반대로 만들면, 곱한 사후분포가 곱꼴이 된다", 12, INK2)

cx = [150, 410, 670]
b += box(58, 76, 184, 150, "#F4F6F4", NO, 1.3, 10)
b += txt(cx[0], 100, "가능도가 만드는 상관", 12, NO, weight=600)
b += txt(cx[0], 122, E("P(v|h)"), 13, INK)
b += circ(116, 168, 14, NODE, LINE, 1.0)
b += circ(184, 168, 14, NODE, LINE, 1.0)
b += path("M 116 154 Q 150 128 184 154", NO, "none", 2.0)
b += txt(cx[0], 208, "얽힌다 (설명해치우기)", 11, NO)

b += txt(268, 156, "x", 18, MUTED)

b += box(318, 76, 184, 150, "#F4F6F4", FWD, 1.3, 10)
b += txt(cx[1], 100, "사전분포가 만드는 상관", 12, FWD, weight=600)
b += txt(cx[1], 122, E("P(h)"), 13, INK)
b += circ(376, 168, 14, NODE, LINE, 1.0)
b += circ(444, 168, 14, NODE, LINE, 1.0)
b += path("M 376 182 Q 410 208 444 182", FWD, "none", 2.0)
b += txt(cx[1], 208, "정확히 반대로 얽는다", 11, FWD)

b += txt(528, 156, "=", 18, MUTED)

b += box(578, 76, 184, 150, "#F4F6F4", OK, 1.3, 10)
b += txt(cx[2], 100, "사후분포", 12, OK, weight=600)
b += txt(cx[2], 122, E("P(h|v)"), 13, INK)
b += circ(636, 168, 14, NODE, LINE, 1.0)
b += circ(704, 168, 14, NODE, LINE, 1.0)
b += txt(cx[2], 208, "상관이 지워져 곱꼴이 된다", 11, OK, weight=600)

b += box(28, 244, 768, 124, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 268, "그런 사전분포가 정말 있는가 — 논문이 답한 방식", 12.5, INK, weight=600)
b += txt(52, 294, "1. 있다고 주장하지 않고 하나를 짓는다 — 같은 가중치를 무한히 쌓은 망이 층마다 상보 사전분포를 만든다(그림 6).", 12, INK2, anchor="start")
b += txt(52, 316, "2. 부록 A 가 어떤 가능도가 상보 사전분포를 가질 수 있는지를 식 11~13 으로 가른다.", 12, INK2, anchor="start")
b += txt(52, 340, "3. 이 짓기가 곧 방향 없는 망(RBM)과 같아진다 — 그래서 빠르게 배울 수 있다(그림 7).", 12, REV, anchor="start", weight=600)
b += txt(412, 362, "논문의 말: 이것이 가능하다는 것 자체가 널리 불가능하다고 여겨지던 것이었다.", 11.5, MUTED)
svg("fig05_complementary_prior", 820, 382, b,
    "가능도가 만드는 상관을 사전분포가 정확히 반대로 만들면 사후분포의 상관이 지워져 곱꼴이 된다")


# ── 6. 무한 스택 (논문 그림 3) ────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("d1", FWD), arrow("d2", REV))
b += txt(410, 28, "가중치를 묶어 무한히 쌓은 망 — 논문 그림 3", 14, INK, weight=600)

layers = [("V2", 92), ("H1", 152), ("V1", 212), ("H0", 272), ("V0", 332)]
for name, y in layers:
    b += box(300, y - 18, 220, 36, NODE, INK, 1.2, 6)
    b += txt(410, y + 5, name, 12.5, INK, weight=600)
b += txt(410, 62, "더 위로 끝없이", 11.5, MUTED)
b += path("M 410 46 L 410 70", MUTED, "none", 1.2, dash="4 4")
for i in range(len(layers) - 1):
    y1 = layers[i][1] + 18
    y2 = layers[i + 1][1] - 18
    b += line(370, y1, 370, y2, FWD, 1.8, marker="d1")
    b += line(450, y2, 450, y1, REV, 1.6, dash="5 4", marker="d2")
b += txt(268, 212, "W", 13, FWD, weight=600, anchor="end")
b += txt(556, 212, "W 의 전치", 12.5, REV, anchor="start")

b += box(28, 372, 768, 128, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 396, "화살표 둘의 뜻이 다르다", 12.5, INK, weight=600)
b += txt(52, 422, "아래로 (파랑, 실선) — 이것이 모델이다. 위층 상태에서 아래층을 만들어 낸다.", 12, FWD, anchor="start")
b += txt(52, 444, "위로 (주황, 점선) — 모델의 일부가 아니다. 데이터를 V0 에 고정했을 때 사후분포에서 표본을 뽑는 데 쓴다.", 12, REV, anchor="start")
b += txt(52, 470, "모든 층이 같은 W 를 쓴다(묶여 있다). 그래서 위로 올라가며 전치 행렬만 곱하면 참 사후분포에서 표본이 나온다.", 12, INK, anchor="start", weight=600)
b += txt(52, 492, "곧 이 망에서는 추론이 어렵지 않다 — 상보 사전분포가 층마다 서 있기 때문이다.", 11.5, OK, anchor="start", weight=600)
svg("fig06_infinite_stack", 820, 514, b,
    "가중치를 묶어 무한히 쌓은 방향 있는 망. 아래 화살표가 모델이고 위 화살표는 추론에만 쓴다")


# ── 7. 무한 스택 = RBM ────────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("e1", FWD), arrow("e2", REV))
b += txt(410, 28, "무한 스택은 RBM 과 같다 — 기브스 한 걸음이 한 층이다", 14, INK, weight=600)

b += box(24, 48, 372, 300, "#F4F6F4", LINE, 1.2, 10)
b += txt(210, 72, "무한 스택 (방향 있음)", 12.5, FWD, weight=600)
for i, (nm, y) in enumerate([("V2", 110), ("H1", 158), ("V1", 206), ("H0", 254), ("V0", 302)]):
    b += box(130, y - 15, 160, 30, NODE, INK, 1.1, 5)
    b += txt(210, y + 4, nm, 11.5, INK, weight=600)
    if i:
        b += line(210, y - 33, 210, y - 17, FWD, 1.5, marker="e1")
b += txt(210, 332, "층을 하나 올라간다", 11.5, MUTED)

b += txt(410, 200, "=", 22, MUTED, weight=600)

b += box(424, 48, 372, 300, "#F4F6F4", LINE, 1.2, 10)
b += txt(610, 72, "RBM (방향 없음)", 12.5, REV, weight=600)
for x in [540, 590, 640, 690]:
    b += circ(x, 140, 15, REV_SOFT, REV, 1.2)
for x in [565, 615, 665]:
    b += circ(x, 236, 15, NODE, INK, 1.2)
for x in [540, 590, 640, 690]:
    for x2 in [565, 615, 665]:
        b += line(x, 155, x2, 221, MUTED, 0.9, op="0.5")
b += txt(610, 112, "숨은 층 h", 11.5, MUTED)
b += txt(610, 268, "보이는 층 v", 11.5, MUTED)
b += path("M 730 140 C 766 160 766 216 730 236", REV, "none", 1.8, marker="e2")
b += txt(752, 190, "번갈아", 11, REV, anchor="start")
b += txt(610, 332, "기브스를 한 걸음 돈다", 11.5, MUTED)

b += box(28, 358, 768, 128, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 382, "같은 것이라는 근거 — 미분이 맞아떨어진다 (식 4, 5)", 12.5, INK, weight=600)
b += txt(52, 408, E("무한 스택의 미분 = <h_0(v_0 - v_1)> + <v_1(h_0 - h_1)> + <h_1(v_1 - v_2)> + ..."), 12, INK2, anchor="start")
b += txt(52, 432, "세로로 줄지은 항들이 서로 지워지고 남는 것이 RBM 의 학습 규칙이다.", 12, INK2, anchor="start")
b += txt(52, 458, E("남는 것: d log p(v_0) / d w_ij = <v_0 h_0> - <v_inf h_inf>"), 12.5, REV, anchor="start", weight=600)
b += txt(52, 480, "왼쪽은 데이터를 고정했을 때의 상관, 오른쪽은 평형에 이르렀을 때의 상관이다.", 11.5, MUTED, anchor="start")
svg("fig07_rbm_equiv", 820, 500, b,
    "무한 스택의 미분에서 세로로 줄지은 항이 지워지고 RBM 의 학습 규칙만 남는다. 기브스 한 걸음이 한 층에 해당한다")


# ── 8. 대조 발산 ──────────────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("f1", REV)
b += txt(410, 28, "대조 발산 (contrastive divergence) — 평형까지 안 가고 n 걸음에서 끊는다", 14, INK, weight=600)

ys = 110
for i, (lab, x) in enumerate([("v0", 90), ("h0", 190), ("v1", 290), ("h1", 390), ("v-inf", 640), ("h-inf", 730)]):
    b += circ(x, ys, 22, (FWD_SOFT if i < 4 else "#EDEDED"), (FWD if i < 4 else MUTED), 1.3)
    b += txt(x, ys + 5, E(lab.replace("-inf", "_inf")), 11.5, INK if i < 4 else MUTED, weight=600)
for a2, c2 in [(90, 190), (190, 290), (290, 390)]:
    b += line(a2 + 22, ys, c2 - 22, ys, INK2, 1.3, marker="f1")
b += path("M 412 110 L 612 110", MUTED, "none", 1.3, dash="6 5", marker="f1")
b += txt(512, 98, "평형까지 아주 많이", 11.5, MUTED)
b += txt(90, ys + 44, "데이터", 11.5, FWD, weight=600)
b += txt(685, ys + 44, "평형 분포", 11.5, MUTED)

b += box(56, 168, 300, 64, "#F4F6F4", OK, 1.3, 8)
b += txt(206, 192, "여기서 끊는다 (n 걸음)", 12, OK, weight=600)
b += txt(206, 214, "논문의 MNIST 실험은 n = 1 로 시작한다", 11.5, INK2)
b += box(504, 168, 262, 64, "#F4F6F4", NO, 1.3, 8)
b += txt(635, 192, "여기까지 가면 정확하지만", 12, NO, weight=600)
b += txt(635, 214, "깊은 망에서는 시간이 감당 안 된다", 11.5, INK2)

b += box(28, 250, 768, 130, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 274, "무엇을 얻고 무엇을 잃는가", 12.5, INK, weight=600)
b += txt(52, 300, "얻는 것 — 평형 표본을 안 뽑아도 되므로 훨씬 빠르다. RBM 하나를 실제로 배울 수 있게 된다.", 12, OK, anchor="start")
b += txt(52, 322, "잃는 것 — 정확한 최대가능도 학습이 아니다. 논문이 「효율을 비싼 값에 샀다」고 적는다.", 12, NO, anchor="start")
b += txt(52, 348, "그리고 이것을 그대로 깊은 망에 쓰면 안 된다 — 층마다 가중치가 다르면 데이터를 고정한 조건부 평형에 이르는 데도 너무 오래 걸린다.", 12, INK, anchor="start", weight=600)
b += txt(52, 370, "그 막힌 자리를 푸는 것이 다음 그림의 탐욕 학습이다.", 11.5, REV, anchor="start", weight=600)
svg("fig08_cd", 820, 396, b,
    "대조 발산은 평형까지 가지 않고 n 걸음에서 끊는다. 빠르지만 최대가능도가 아니고 깊은 망에 바로 쓸 수 없다")


# ── 9. 탐욕 층별 학습 ─────────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("g1", FWD), arrow("g2", REV))
b += txt(410, 28, "탐욕 층별 학습 (greedy layer-wise learning) — 한 층씩 배우고 얼린다", 14, INK, weight=600)

steps = [
    ("1. 모든 가중치가 묶여 있다고 보고", "W0 를 RBM 으로 배운다", 24),
    ("2. W0 를 얼리고, 전치로 올려", "첫 은닉층의 「데이터」를 만든다", 290),
    ("3. 위층끼리는 묶은 채 W0 와는 풀어", "그 「데이터」의 RBM 을 배운다", 556),
]
for title, sub, x in steps:
    b += box(x, 50, 240, 232, "#F4F6F4", LINE, 1.2, 10)
    b += txt(x + 120, 74, title, 11.5, INK, weight=600)
    b += txt(x + 120, 94, sub, 11.5, INK2)
for i, x in enumerate([24, 290, 556]):
    for j, (nm, y) in enumerate([("h2", 130), ("h1", 182), ("v", 234)]):
        on = (i == 0 and j >= 1) or (i == 1 and j >= 1) or (i == 2)
        col = REV if (i == 2 and j <= 1) else (FWD if j >= 1 else INK)
        fill = REV_SOFT if (i == 2 and j <= 1) else (FWD_SOFT if j >= 1 else NODE)
        if i == 1 and j == 2:
            fill, col = "#E4E7E4", MUTED
        b += box(x + 60, y - 16, 120, 32, fill, col, 1.2, 5)
        b += txt(x + 120, y + 5, nm, 11.5, INK if fill != "#E4E7E4" else MUTED, weight=600)
    if i == 0:
        b += txt(x + 120, 262, "W0 를 배운다", 11, REV, weight=600)
        b += line(x + 120, 218, x + 120, 198, REV, 1.6, marker="g2")
    if i == 1:
        b += txt(x + 120, 262, "W0 는 얼었다", 11, MUTED, weight=600)
        b += line(x + 120, 218, x + 120, 198, MUTED, 1.6, marker="g1", dash="4 3")
    if i == 2:
        b += txt(x + 120, 262, "위층을 배운다", 11, REV, weight=600)
        b += line(x + 120, 166, x + 120, 146, REV, 1.6, marker="g2")

b += box(28, 296, 768, 132, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 320, "왜 이것이 되는가 — 부스팅과 닮았지만 다른 점 하나", 12.5, INK, weight=600)
b += txt(52, 346, "부스팅은 같은 약한 학습기를 되풀이하되 데이터에 가중치를 다시 매겨 다음이 새것을 배우게 한다.", 12, INK2, anchor="start")
b += txt(52, 368, "이 알고리즘은 가중치를 다시 매기는 대신 데이터를 다시 표현한다 — 위층은 아래층이 만든 표현을 본다.", 12, REV, anchor="start", weight=600)
b += txt(52, 394, "그리고 약한 학습기 자체가 방향 없는 그래프 모델(RBM)이다.", 12, INK2, anchor="start")
b += txt(52, 418, "논문의 MNIST 실험은 층마다 30 바퀴를 돌렸고 층당 몇 시간이 걸렸다(3GHz Xeon, Matlab).", 11.5, MUTED, anchor="start")
svg("fig09_greedy", 820, 444, b,
    "탐욕 층별 학습은 W0 를 RBM 으로 배워 얼리고 그 표현 위에서 다음 층을 배운다. 데이터에 가중치를 매기는 대신 다시 표현한다")


# ── 10. 변분 하한이 보장하는 것 ───────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("h1", OK)
b += txt(410, 28, "층을 더해도 나빠지지 않는다는 보장 (식 8, 9)", 14, INK, weight=600)

gx, gy, gw, gh = 70, 60, 420, 220
b += line(gx, gy + gh, gx + gw, gy + gh, INK2, 1.2)
b += line(gx, gy, gx, gy + gh, INK2, 1.2)
b += txt(gx - 12, gy + 10, "높다", 11, MUTED, anchor="end")
b += txt(gx + gw / 2, gy + gh + 22, "학습 단계", 11.5, MUTED)
b += line(gx + 20, gy + 150, gx + gw - 20, gy + 150, FWD, 2.0, dash="6 4")
b += txt(gx + gw - 24, gy + 142, "참 로그가능도", 11.5, FWD, anchor="end")
b += path("M %d %d L %d %d L %d %d" % (gx + 20, gy + 150, gx + 180, gy + 150, gx + gw - 20, gy + 84),
          OK, "none", 2.4, marker="h1")
b += circ(gx + 20, gy + 150, 6, OK, OK, 0)
b += txt(gx + 30, gy + 176, "2단계: 하한이 참값과 딱 맞는다", 11.5, OK, anchor="start", weight=600)
b += txt(gx + 200, gy + 108, "3단계: 하한이 올라간다", 11.5, OK, anchor="start", weight=600)
b += txt(gx + 200, gy + 130, "그래서 참값이 2단계 아래로 못 내려간다", 11, INK2, anchor="start")

b += box(516, 60, 280, 220, "#F4F6F4", LINE, 1.2, 10)
b += txt(656, 84, "왜 딱 맞는가", 12.5, INK, weight=600)
b += txt(656, 112, "가중치가 전부 묶여 있으면", 11.5, INK2)
b += txt(656, 132, "전치를 곱해 얻은 곱꼴 분포가", 11.5, INK2)
b += txt(656, 152, "참 사후분포와 같다", 11.5, OK, weight=600)
b += txt(656, 180, "하한이 등호가 되는 조건이", 11.5, INK2)
b += txt(656, 200, "「Q 가 참 사후분포일 때」이므로", 11.5, INK2)
b += txt(656, 220, "그 자리에서 하한 = 참값", 11.5, OK, weight=600)
b += txt(656, 252, "그 뒤 위층을 배우면 하한만 올라간다", 11, MUTED)

b += box(28, 300, 768, 128, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 324, "보장의 범위를 정확히 적는다", 12.5, INK, weight=600)
b += txt(52, 350, "보장되는 것 — 각 층을 최대가능도 볼츠만 기계 학습으로 배우면 로그가능도가 내려가지 않는다(기댓값 기준).", 12, OK, anchor="start")
b += txt(52, 372, "실제로 한 것 — 대조 발산으로 바꿔 썼다. 논문의 말로 「대조 발산을 쓰면 그 보장이 무효가 된다」.", 12, NO, anchor="start", weight=600)
b += txt(52, 398, "논문이 이어 적기를, 그래도 층을 충분히 참을성 있게 배우면 불완전한 모델이 나아진다는 것은 안심이 된다고 했다.", 12, INK2, anchor="start")
b += txt(52, 420, "그리고 하한이 조여들면 참값이 내려가는 일도 있을 수 있다고 적는다 — 2단계 값 아래로는 안 내려간다.", 11.5, MUTED, anchor="start")
svg("fig10_bound", 820, 444, b,
    "가중치가 묶인 자리에서 변분 하한이 참값과 같아지고 위층을 배우면 하한이 올라간다. 대조 발산을 쓰면 이 보장은 무효가 된다")


# ── 12. 논문 그림 1 의 망 ─────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("i1", FWD), arrow("i2", REV))
b += txt(410, 28, "MNIST 에 쓴 망 — 논문 그림 1", 14, INK, weight=600)

b += box(230, 56, 360, 44, REV_SOFT, REV, 1.6, 6)
b += txt(410, 83, "2000 units (연상 기억의 위쪽)", 12.5, INK, weight=600)
b += box(150, 132, 200, 40, REV_SOFT, REV, 1.6, 6)
b += txt(250, 157, "500 units", 12.5, INK, weight=600)
b += box(430, 132, 160, 40, REV_SOFT, REV, 1.6, 6)
b += txt(510, 157, "10 label units", 12.5, INK, weight=600)
b += box(150, 212, 200, 40, FWD_SOFT, FWD, 1.4, 6)
b += txt(250, 237, "500 units", 12.5, INK, weight=600)
b += box(150, 292, 200, 44, NODE, INK, 1.4, 6)
b += txt(250, 312, "28 x 28 pixel image", 12, INK, weight=600)
b += txt(250, 329, "784", 11, MUTED)

b += path("M 250 132 L 250 104 M 240 112 L 250 100 L 260 112", REV, "none", 1.8)
b += path("M 250 100 L 250 128 M 240 120 L 250 132 L 260 120", REV, "none", 1.8)
b += path("M 510 132 L 510 104 M 500 112 L 510 100 L 520 112", REV, "none", 1.8)
b += path("M 510 100 L 510 128 M 500 120 L 510 132 L 520 120", REV, "none", 1.8)
b += line(250, 212, 250, 178, FWD, 1.8, marker="i1")
b += line(250, 292, 250, 258, FWD, 1.8, marker="i1")

b += txt(620, 154, "방향 없음 — 연상 기억", 11.5, REV, anchor="start", weight=600)
b += txt(620, 232, "방향 있음 — 생성 연결", 11.5, FWD, anchor="start", weight=600)
b += txt(620, 252, "(반대 방향에 인식 연결)", 11, MUTED, anchor="start")
b += box(600, 292, 196, 44, "#F4F6F4", MUTED, 1.2, 6)
b += txt(698, 312, "라벨 자리는 다른 감각 경로의", 10.5, MUTED)
b += txt(698, 328, "위층으로 바꿔도 된다고 적는다", 10.5, MUTED)

b += box(28, 356, 768, 106, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 380, "숫자로 적어 두는 설정", 12.5, INK, weight=600)
b += txt(52, 406, "가중치 약 170만 개. 학습 이미지 60,000 · 시험 이미지 10,000.", 12, INK2, anchor="start")
b += txt(52, 428, "탐욕 학습은 44,000 장을 10 개씩 균형 잡은 440 묶음으로 나눠 층마다 30 바퀴. 끝났을 때 시험 오차 2.49%.", 12, INK2, anchor="start")
b += txt(52, 452, "그 뒤 위-아래 알고리즘으로 300 바퀴. 학습 전체가 약 일주일 걸렸다.", 12, INK2, anchor="start")
svg("fig12_network", 820, 478, b,
    "MNIST 망은 784 픽셀에서 500, 500 을 거쳐 위 두 층 2000 과 라벨 10 이 방향 없는 연상 기억을 이룬다")


# ── 11. 위-아래 알고리즘 ──────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("j1", FWD), arrow("j2", REV))
b += txt(410, 28, "위-아래 알고리즘 (up-down) — 먼저 배운 아래층을 나중에 다시 맞춘다", 14, INK, weight=600)

for idx, (title, col, x) in enumerate([("올라가는 패스", REV, 24), ("연상 기억에서 기브스", MUTED, 290), ("내려가는 패스", FWD, 556)]):
    b += box(x, 50, 240, 250, "#F4F6F4", LINE, 1.2, 10)
    b += txt(x + 120, 74, title, 12.5, col, weight=600)
    for j, y in enumerate([110, 160, 210, 260]):
        b += box(x + 60, y - 15, 120, 30, NODE, INK, 1.1, 5)
    if idx == 0:
        for y in [160, 210, 260]:
            b += line(x + 120, y - 15, x + 120, y - 35, REV, 1.6, marker="j2")
        b += txt(x + 120, 288, "인식 가중치로 상태를 뽑는다", 10.5, MUTED)
    if idx == 1:
        b += path("M %d 110 C %d 128 %d 142 %d 160" % (x + 190, x + 216, x + 216, x + 190), MUTED, "none", 1.6, marker="j1")
        b += path("M %d 160 C %d 142 %d 128 %d 110" % (x + 50, x + 24, x + 24, x + 50), MUTED, "none", 1.6, marker="j1")
        b += txt(x + 120, 288, "위 두 층만 몇 번 번갈아 돈다", 10.5, MUTED)
    if idx == 2:
        for y in [110, 160, 210]:
            b += line(x + 120, y + 15, x + 120, y + 35, FWD, 1.6, marker="j1")
        b += txt(x + 120, 288, "생성 가중치로 내려가며 만든다", 10.5, MUTED)

b += box(28, 314, 768, 148, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 338, "무엇이 바뀌고 무엇이 안 바뀌는가 — 이 구분이 알고리즘의 전부다", 12.5, INK, weight=600)
b += txt(52, 364, "올라갈 때 — 생성 가중치(아래로 가는 것)를 고친다.", 12, REV, anchor="start")
b += txt(52, 386, "내려갈 때 — 인식 가중치(위로 가는 것)만 고친다. 위 두 층과 생성 가중치는 안 건드린다.", 12, FWD, anchor="start")
b += txt(52, 412, "원래 깨어-잠 알고리즘과 다른 점 — 잠 단계를 평형에서 시작하지 않고 올라가는 패스로 초기화한 뒤 몇 번만 돌린다.", 12, INK, anchor="start", weight=600)
b += txt(52, 434, "그래서 인식 가중치가 실제 데이터에서 나오는 표현 위에서 배워지고, 최빈값 평균내기 문제가 줄어든다.", 12, INK2, anchor="start")
b += txt(52, 456, "논문의 설정: 처음 100 바퀴는 기브스 3 번, 다음 100 바퀴는 6 번, 마지막 100 바퀴는 10 번. 늘릴 때마다 검증 오차가 내려갔다.", 11.5, MUTED, anchor="start")
svg("fig11_updown", 820, 478, b,
    "위-아래 알고리즘은 올라갈 때 생성 가중치를, 내려갈 때 인식 가중치를 고친다. 잠 단계를 올라가는 패스로 초기화하는 것이 원래와 다르다")


# ── 13. MNIST 오차율 ──────────────────────────────────────────────────────
b = txt(410, 28, "MNIST 오차율 — 논문 표 1 에서 순열 불변 조건만 뽑았다", 14, INK, weight=600)
b += txt(410, 50, "순열 불변 (permutation-invariant) = 픽셀 순서를 모르는 조건. 기하 지식도 전처리도 쓰지 않는다", 11.5, MUTED)

bars = [("이 논문의 생성 모델", 1.25, REV, "784-500-500-2000-10"),
        ("서포트 벡터 머신", 1.40, FWD, "9차 다항 커널"),
        ("역전파 784-500-300-10", 1.51, FWD, "교차 엔트로피 + 가중치 감쇠"),
        ("역전파 784-800-10", 1.53, FWD, "교차 엔트로피 + 조기 종료"),
        ("최근접 이웃", 2.80, MUTED, "60,000 전부, L3 노름"),
        ("역전파 784-500-150-10", 2.95, MUTED, "제곱 오차 + 온라인 갱신"),
        ("최근접 이웃", 3.10, MUTED, "60,000 전부, L2 노름")]
x0, w0 = 250, 430
for i, (nm, v, col, sub) in enumerate(bars):
    y = 88 + i * 44
    b += txt(238, y + 5, nm, 11.5, INK, anchor="end", weight=(600 if i == 0 else None))
    L = w0 * v / 3.4
    b += box(x0, y - 11, L, 22, (REV_SOFT if i == 0 else ("#E8EEF1" if col == FWD else "#EAEAEA")), col, 1.2, 3)
    b += txt(x0 + L + 10, y + 5, format(v, ".2f") + "%", 12, col, anchor="start", weight=600)
    b += txt(x0 + L + 66, y + 5, sub, 10.5, MUTED, anchor="start")
print("  오차율 막대:", [v for _n, v, _c, _s in bars])

b += box(28, 402, 768, 132, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 426, "읽을 때 조심할 것 셋", 12.5, INK, weight=600)
b += txt(52, 452, "1. 이 표는 순열 불변 조건이다. 픽셀 순서를 쓰는 합성곱 망은 0.4~0.95% 로 더 낮다 — 같은 칸에 놓지 않는다.", 12, INK2, anchor="start")
b += txt(52, 474, "2. 1.25% 는 60,000 장 전부로 다시 배운 뒤의 값이다. 44,000 장으로 고른 망의 값은 1.39% 다.", 12, INK2, anchor="start")
b += txt(52, 498, "3. 탐욕 학습만 끝냈을 때가 2.49% 이고, 위-아래 미세조정이 1.25% 로 내렸다 — 두 단계의 몫이 갈린다.", 12, REV, anchor="start", weight=600)
b += txt(52, 522, "논문 각주: 아주 작은 학습률로 6 주 더 돌리자 시험 오차가 1.12~1.31% 사이에서 흔들렸다.", 11.5, MUTED, anchor="start")
svg("fig13_mnist", 820, 550, b,
    "순열 불변 MNIST 에서 이 논문이 1.25%, SVM 이 1.4%, 역전파가 1.51% 다. 탐욕 학습만으로는 2.49% 였다")


# ── 14. 한계와 다음 ───────────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("k1", REV)
b += txt(410, 28, "논문이 스스로 적은 한계, 그리고 다음 자리", 14, INK, weight=600)

b += box(24, 52, 380, 266, "#F4F6F4", NO, 1.3, 10)
b += txt(214, 76, "논문이 한계라고 적은 것", 12.5, NO, weight=600)
lims = ["이진값이 아닌 값을 확률로 다룰 수 있는",
        "이미지를 전제한다 — 자연 이미지는 아니다",
        "지각할 때의 위에서 아래로의 되먹임이",
        "위 두 층의 연상 기억에 갇혀 있다",
        "지각 불변성을 다루는 방법이 없다",
        "분할이 이미 끝났다고 가정한다",
        "어려울 때 정보가 많은 부분을 차례로",
        "살펴보는 것을 배우지 않는다"]
for i, t in enumerate(lims):
    b += txt(44, 106 + i * 26, ("- " if i in (0, 2, 4, 5, 6) else "  ") + t, 11.5, INK2, anchor="start")
b += txt(214, 302, "그리고 미세조정이 느리다 — 일그러뜨린 데이터를 못 써 봤다고 적는다", 11, MUTED)

b += box(416, 52, 380, 266, "#F4F6F4", REV, 1.3, 10)
b += txt(606, 76, "이 한계가 여는 다음 자리", 12.5, REV, weight=600)
nexts = [("자연 이미지로", "이진 · 확률 가정을 벗는 쪽"),
         ("불변성을 배우게", "가중치 공유와 부분 표본 뽑기"),
         ("미세조정을 빠르게", "또는 아예 없애는 쪽"),
         ("생성 대신 판별로", "층별 사전학습이 정말 필요했는가")]
for i, (a2, c2) in enumerate(nexts):
    y = 116 + i * 50
    b += box(436, y - 20, 340, 40, "#FFFFFF", LINE, 1.1, 6)
    b += txt(452, y - 3, a2, 11.5, REV, anchor="start", weight=600)
    b += txt(452, y + 15, c2, 11, INK2, anchor="start")
b += txt(606, 302, "논문의 마지막 문단: 판별 학습이 앞서는 영역은 좋은 생성 모델을 못 배우는 영역뿐이다", 10.5, MUTED)

b += box(28, 334, 768, 108, "#FFFFFF", INK, 1.3, 8)
b += txt(412, 358, "이 노트를 쓰며 내가 짚은 자리 — 논문의 말이 아니다", 12.5, INK, weight=600)
b += txt(52, 384, "탐욕 학습이 2.49% 이고 미세조정이 1.25% 다. 층별 사전학습이 낸 몫과 미세조정이 낸 몫이 갈려 있지 않다.", 12, INK2, anchor="start")
b += txt(52, 406, "같은 미세조정을 무작위 초기화 위에 얹으면 얼마가 나오는지가 이 논문 안에 없다.", 12, NO, anchor="start", weight=600)
b += txt(52, 430, "곧 「깊은 망에 사전학습이 필요한가」는 이 논문이 답하지 않은 채로 남아 있고, 그것이 다음 몇 해의 주제가 된다.", 12, INK2, anchor="start")
svg("fig14_limits", 820, 458, b,
    "논문이 적은 한계 여섯과 그것이 여는 다음 자리. 탐욕 학습과 미세조정의 몫이 갈려 있지 않다는 점은 내가 짚은 것이다")

print("끝났다.")
