# -*- coding: utf-8 -*-
"""Elman 노트(Finding Structure in Time, Cognitive Science 14(2):179-211, 1990)의 그림 열다섯을 만든다.

색과 글꼴은 저장소의 앞선 노트들 그림과 맞췄다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

계산으로 원문을 확인하는 그림이 여럿이다 — 3(시간을 자리로 펼친 벡터 둘의 거리), 4 · 5(시간 XOR 에서 어떤
예측기도 넘을 수 없는 아래 한계와 원문 그림 3 의 값), 6(표 1 의 비트 중복과 자음 자리의 아래 한계),
9(표 2 의 글자 부호가 알파벳 순번의 이진수인가), 10(문장 말뭉치 길이 셋과 틀을 고르게 뽑았을 때의 기댓값),
14(망 넷의 파라미터 수와 학습 걸음 수). 계산한 값은 돌릴 때 화면에도 찍는다.

원문 그림 3 · 4 · 5 · 6 · 7 · 8 의 값은 스캔 쪽 이미지(300 dpi)에서 축 상자와 눈금 자리를 픽셀로 찾고
꺾이는 점의 높이를 읽은 것이다. 읽은 값을 아래 READ_* 상수에 그대로 적어 두었다 — 이 파일은 PDF 를 읽지 않는다.
원문 그림 자체는 crop_paper_figures.py 가 잘라 png 로 둔다.
"""
import io, os, math

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"
NODE      = "#F6F7F5"
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 학습되는 연결, 순방향
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 고정된 복사 연결, 기억
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 원문 그림에서 읽은 값
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"   # 초록 — 맞다 / 예측 가능
OK_SOFT   = "#D6EEDD"
NO        = "#C0392B"   # 빨강 — 어긋난다 / 넘을 수 없다
NO_SOFT   = "#F6D9D5"
FONT = "IBM Plex Sans KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"
MONO = "Consolas, D2Coding, monospace"


# ── 공통 도구 ──────────────────────────────────────────────────────────────
def svg(name, w, h, body, label):
    s = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="%s" role="img" aria-label="%s">' % (w, h, w, h, FONT, label))
    s += '<rect x="0" y="0" width="100%%" height="100%%" fill="%s"/>' % BG
    s += defs() + body + "</svg>\n"
    io.open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8").write(s)
    print("  " + name + ".svg  %dx%d" % (w, h))


def arrow(idd, color):
    return ('<marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>' % (idd, color))


def defs():
    return ("<defs>" + arrow("af", FWD) + arrow("ar", REV) + arrow("ai", INK2) + arrow("ao", OK)
            + arrow("an", NO) + "</defs>")


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, t, size=12, fill=None, anchor="middle", weight=None, style=None, family=None):
    a = 'x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s"' % (x, y, size, fill or INK, anchor)
    if weight:
        a += ' font-weight="%s"' % weight
    if style:
        a += ' font-style="%s"' % style
    if family:
        a += ' font-family="%s"' % family
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


def lines_at(x, y, rows, size=12, gap=20, anchor="start"):
    s = ""
    for j, r in enumerate(rows):
        if isinstance(r, tuple):
            t, c = r[0], r[1]
            w = r[2] if len(r) > 2 else None
        else:
            t, c, w = r, INK2, None
        s += txt(x, y + gap * j, t, size, fill=c, anchor=anchor, weight=w)
    return s


def yaxis(x0, x1, fy, ticks, fmt="%.2f"):
    s = ""
    for t in ticks:
        s += line(x0, fy(t), x1, fy(t), LINE, 0.8, dash="2 3")
        s += txt(x0 - 6, fy(t) + 4, fmt % t, 10, fill=MUTED, anchor="end")
    s += line(x0, fy(ticks[0]), x0, fy(ticks[-1]), INK2, 1.2)
    return s


print("그림을 만든다 ->", OUT)

# ── 원문 그림에서 읽은 값 ────────────────────────────────────────────────────
# 그림 3: 가로 1 ~ 12 의 꺾이는 점. 세로축은 0.00 ~ 0.50 눈금이 찍혀 있다. 읽기 오차 ±0.01.
READ_FIG3 = [0.33, 0.17, 0.31, 0.29, 0.18, 0.34, 0.32, 0.17, 0.32, 0.32, 0.16, 0.28]
# 그림 4 · 5(a) · 5(b): 세로축은 「0 -y- 1」 만 적혀 있다. 점 20 개, 괄호 안 글자는 맞혀야 할 다음 글자.
TARGETS = list("adiiguuubaguuudiidii")
READ_FIG4 = [0.13, 0.60, 0.20, 0.21, 0.77, 0.07, 0.05, 0.25, 0.43, 0.12,
             0.61, 0.02, 0.04, 0.20, 0.66, 0.06, 0.16, None, 0.07, 0.36]      # 읽기 오차 ±0.02, 18 번째 점은 그려져 있지 않다
READ_FIG5A = [0.01, 0.02, 0.00, 0.00, 0.12, 0.00, 0.02, 0.06, 0.01, 0.02,
              0.03, 0.00, 0.02, 0.05, 0.01, 0.00, 0.03, 0.03, 0.00, 0.08]     # 읽기 오차 ±0.01
READ_FIG5B = [0.01, 0.37, 0.19, 0.19, 0.18, 0.06, 0.03, 0.02, 0.04, 0.04,
              0.37, 0.02, 0.03, 0.02, 0.08, 0.02, 0.09, 0.67, 0.02, 0.09]     # 읽기 오차 ±0.02
# 그림 6: 세로축 「0 -y- 3.5」, 점 54 개. 꼭짓점을 눈으로 읽었다. 읽기 오차 ±0.1.
FIG6_TEXT = "many years ago a boy and girl lived by the sea they played happily m"
READ_FIG6 = [2.43, 2.01, 1.05, 0.50, 3.00, 1.81, 0.97, 0.87, 0.18, 2.89, 2.53, 1.00, 2.78, 1.79, 1.00, 0.25,
             2.24, 1.29, 1.49, 2.49, 1.81, 1.45, 0.85, 1.86, 1.65, 0.90, 0.52, 0.25, 1.92, 0.85, 2.15, 1.67,
             0.86, 2.92, 0.70, 0.86, 1.83, 1.40, 0.79, 1.29, 1.83, 1.56, 0.86, 0.48, 0.25, 0.14, 2.58, 1.88,
             0.86, 0.75, 0.27, 0.18, 0.02, 1.83]
# 그림 7 · 8: 눈금 다섯의 간격이 같은데 라벨은 「2.0 1.5 1.0 0.0 -0.5」 다. 잎 선이 「0.0」 눈금 좌우에서 끝나므로
# 뒤 둘을 살리고 앞 셋을 0.5 씩 내려 「1.5 1.0 0.5 0.0 -0.5」 로 읽은 합쳐지는 거리(읽기 B). 읽기 오차 ±0.02.
# 앞 셋을 살리는 읽기(A, 「2.0 1.5 1.0 0.5 0.0」)는 모든 값에 0.5 를 더한 것이다.
READ_FIG7 = {"woman-girl": 0.13, "+man": 0.21, "+boy": 0.29, "사람+동물": 0.63,
             "mouse-cat": 0.09, "+dog": 0.21, "작은+큰 동물": 0.39, "생물+무생물": 1.00, "동사+명사": 1.58}
READ_FIG8 = {"woman-girl": 0.28, "+boy": 0.36, "+zog": 0.70, "(사람+zog)+동물": 0.78,
             "mouse-cat": 0.27, "+dog": 0.35, "작은+큰 동물": 0.57, "생물+무생물": 1.15, "동사+명사": 1.58}
# 그림 7 · 8 의 눈금 자리(300 dpi 픽셀, 왼쪽부터 「2.0 1.5 1.0 0.0 -0.5」 라고 찍힌 다섯)
TICKS_FIG7 = [449.5, 634.5, 820.5, 1003.5, 1186.5]
TICKS_FIG8 = [506.5, 706.5, 908.5, 1108.5, 1308.5]


# ── 그림 1. 두 구조 ───────────────────────────────────────────────────────────
def fig01():
    b = txt(20, 28, "그림 1. 되먹임을 어디서 받는가 — Jordan(1986) 은 출력에서, Elman(1990) 은 은닉층에서", 15, anchor="start", weight="bold")
    # 왼쪽: Jordan
    ox = 40
    b += box(ox, 50, 380, 330, fill="#F4F6F4", stroke=LINE, rx=10)
    b += txt(ox + 190, 74, "Jordan (1986) — 원문 그림 1", 13, weight="bold")
    b += box(ox + 120, 100, 140, 34, fill=FWD_SOFT, stroke=FWD) + txt(ox + 190, 122, "출력", 12)
    b += box(ox + 120, 190, 140, 34, fill=NODE) + txt(ox + 190, 212, "은닉", 12)
    b += box(ox + 30, 290, 130, 34, fill=NODE) + txt(ox + 95, 312, "입력 (계획)", 12)
    b += box(ox + 220, 290, 130, 34, fill=REV_SOFT, stroke=REV) + txt(ox + 285, 312, "상태 (state)", 12)
    b += line(ox + 95, 290, ox + 160, 226, FWD, 1.6, marker="af")
    b += line(ox + 285, 290, ox + 220, 226, FWD, 1.6, marker="af")
    b += line(ox + 190, 190, ox + 190, 136, FWD, 1.6, marker="af")
    b += path("M%d,117 C%d,117 %d,300 %d,300" % (ox + 262, ox + 370, ox + 370, ox + 352), REV, sw=1.8, dash="6 4", marker="ar")
    b += box(ox + 296, 186, 56, 18, fill="#F4F6F4", stroke="none", rx=3) + txt(ox + 324, 199, "복사 1.0", 11, fill=REV)
    b += path("M%d,326 C%d,350 %d,350 %d,326" % (ox + 265, ox + 265, ox + 305, ox + 305), REV, sw=1.4, dash="4 3", marker="ar")
    b += txt(ox + 285, 362, "상태 유닛의 자기 되먹임", 11, fill=REV)
    # 오른쪽: Elman
    ox = 460
    b += box(ox, 50, 380, 330, fill="#F4F6F4", stroke=LINE, rx=10)
    b += txt(ox + 190, 74, "Elman (1990) 단순 순환망 — 원문 그림 2", 13, weight="bold")
    b += box(ox + 120, 100, 140, 34, fill=FWD_SOFT, stroke=FWD) + txt(ox + 190, 122, "출력", 12)
    b += box(ox + 120, 190, 140, 34, fill=NODE) + txt(ox + 190, 212, "은닉 h(t)", 12)
    b += box(ox + 30, 290, 130, 34, fill=NODE) + txt(ox + 95, 312, "입력 x(t)", 12)
    b += box(ox + 220, 290, 130, 34, fill=REV_SOFT, stroke=REV) + txt(ox + 285, 312, "문맥 c(t) = h(t-1)", 12)
    b += line(ox + 95, 290, ox + 160, 226, FWD, 1.6, marker="af")
    b += line(ox + 285, 290, ox + 220, 226, FWD, 1.6, marker="af")
    b += line(ox + 190, 190, ox + 190, 136, FWD, 1.6, marker="af")
    b += path("M%d,207 C%d,207 %d,290 %d,290" % (ox + 262, ox + 360, ox + 340, ox + 330), REV, sw=1.8, dash="6 4", marker="ar")
    b += box(ox + 284, 238, 56, 18, fill="#F4F6F4", stroke="none", rx=3) + txt(ox + 312, 251, "복사 1.0", 11, fill=REV)
    b += txt(ox + 190, 352, "은닉 유닛 수 = 문맥 유닛 수 (각주 3)", 11, fill=INK2)
    b += txt(ox + 190, 370, "문맥의 첫 값 0.5 (182 쪽)", 11, fill=INK2)
    b += line(60, 410, 100, 410, FWD, 1.8) + txt(108, 414, "학습되는 연결 (원문 그림 2 의 점선)", 11, fill=INK2, anchor="start")
    b += line(400, 410, 440, 410, REV, 1.8, dash="6 4") + txt(448, 414, "무게 1.0 으로 고정된 한 대 한 복사 — 학습하지 않는다", 11, fill=INK2, anchor="start")
    svg("fig01_jordan_vs_elman", 880, 432, b, "Jordan 망과 Elman 단순 순환망의 구조")


# ── 그림 2. 한 걸음 역전파 대 펼친 역전파 ─────────────────────────────────────
def fig02():
    b = txt(20, 28, "그림 2. 오차가 어디까지 거슬러 가는가 — 원문의 서술(위)과 1986 년 역전파 논문 9절의 펼치기(아래)", 15, anchor="start", weight="bold")
    def row(y0, title, through):
        s = txt(30, y0 - 12, title, 12, anchor="start", weight="bold", fill=INK)
        for k, t in enumerate(["t-2", "t-1", "t"]):
            x = 150 + 240 * k
            s += box(x, y0 + 60, 90, 30, fill=NODE) + txt(x + 45, y0 + 80, "h(%s)" % t, 12)
            s += box(x, y0 + 120, 90, 26, fill=NODE) + txt(x + 45, y0 + 138, "x(%s)" % t, 11)
            s += box(x, y0 + 8, 90, 26, fill=FWD_SOFT, stroke=FWD) + txt(x + 45, y0 + 26, "y(%s)" % t, 11)
            s += line(x + 45, y0 + 120, x + 45, y0 + 92, FWD, 1.3, marker="af")
            s += line(x + 45, y0 + 60, x + 45, y0 + 36, FWD, 1.3, marker="af")
            if k < 2:
                s += line(x + 92, y0 + 75, x + 238, y0 + 75, REV, 1.4, dash="6 4", marker="ar")
        # 오차 흐름 (빨강, 거꾸로)
        s += path("M%d,%d C%d,%d %d,%d %d,%d" % (690, y0 + 30, 730, y0 + 50, 730, y0 + 60, 692, y0 + 70), NO, sw=2, marker="an")
        if through:
            for k in [2, 1]:
                x = 150 + 240 * k
                s += path("M%d,%d C%d,%d %d,%d %d,%d" % (x - 2, y0 + 82, x - 60, y0 + 104, x - 90, y0 + 104, x - 148, y0 + 84), NO, sw=2, marker="an")
            s += txt(780, y0 + 74, "h(t-1), h(t-2) 까지 기울기가 간다", 11, fill=NO, anchor="start")
            s += txt(780, y0 + 92, "펼친 층마다 저장 · 무게 묶기", 11, fill=INK2, anchor="start")
        else:
            x = 150 + 240 * 2
            s += line(x - 120, y0 + 96, x - 100, y0 + 116, NO, 2.2) + line(x - 120, y0 + 116, x - 100, y0 + 96, NO, 2.2)
            s += txt(780, y0 + 74, "c(t) 를 입력처럼 두면", 11, fill=NO, anchor="start")
            s += txt(780, y0 + 92, "오차는 이 걸음 안에서 멈춘다", 11, fill=NO, anchor="start")
        return s
    b += row(70, "원문 2 절이 적은 것: 문맥 유닛은 고정 무게 1.0 의 복사, 걸음마다 역전파로 연결을 고친다", False)
    b += row(270, "역전파 논문(1986) 9 절: 되먹임 망을 시간으로 펼쳐 층처럼 다룬다", True)
    b += txt(20, 468, "위 그림은 내 해석이다. 원문은 오차를 앞 시간 걸음으로 넘기는지 넘기지 않는지 적지 않는다. 문맥을 입력 쪽에 덧붙인 유닛으로 두고", 11, fill=INK2, anchor="start")
    b += txt(20, 486, "역전파(Rumelhart 외 1986)를 인용한 서술은 한 걸음 안의 역전파로 읽힌다. 204 쪽의 「오차를 늦게 넣으면 성능이 나빴다」 와도 맞는다.", 11, fill=INK2, anchor="start")
    svg("fig02_one_step_vs_unrolled", 960, 500, b, "한 걸음 역전파와 시간으로 펼친 역전파")


# ── 그림 3. 시간을 자리로 펼친 벡터 ───────────────────────────────────────────
def fig03():
    v1 = [0, 1, 1, 1, 0, 0, 0, 0, 0, 1]
    v2 = [0, 0, 0, 1, 1, 1, 0, 0, 0, 1]
    ham = sum(a != c for a, c in zip(v1, v2))
    euc = math.sqrt(ham)
    dot = sum(a * c for a, c in zip(v1, v2))
    cos = dot / math.sqrt(sum(v1) * sum(v2))
    print("    그림 3: 해밍 %d, 유클리드 %.3f, 내적 %d, 코사인 %.3f" % (ham, euc, dot, cos))
    b = txt(20, 28, "그림 3. 시간을 벡터의 자리로 펼치면 — 원문 3 절의 두 벡터", 15, anchor="start", weight="bold")
    for r, (v, name) in enumerate([(v1, "벡터 A"), (v2, "벡터 B (A 의 111 을 두 칸 민 것)")]):
        y = 70 + 52 * r
        b += txt(30, y + 22, name, 12, anchor="start")
        for k, bit in enumerate(v):
            x = 250 + 40 * k
            fill = FWD_SOFT if bit else NODE
            if v1[k] != v2[k]:
                fill = NO_SOFT if bit else NODE
            b += box(x, y, 36, 34, fill=fill, stroke=INK2, rx=3) + txt(x + 18, y + 23, str(bit), 14, family=MONO)
    for k in range(10):
        if v1[k] != v2[k]:
            b += txt(250 + 40 * k + 18, 186, "다름", 10, fill=NO)
    b += lines_at(30, 222, [
        ("내가 센 것: 다른 자리 %d 개 → 유클리드 거리 %.2f, 겹치는 1 은 %d 개 → 코사인 %.2f" % (ham, euc, dot, cos), INK, "bold"),
        "같은 모양 「111」 이 두 칸 옮겨졌을 뿐인데, 자리 하나하나를 독립된 차원으로 두는 표현에서는 반만 겹친다.",
        "원문 각주 1 의 세 벡터 [1 0 0] · [0 1 0] · [0 0 1] 은 서로 직교한다(거리 1.41, 코사인 0) — 「같은 사건이 한 칸씩 늦게 온 것」 이 서로 가장 먼 점이 된다.",
        "원문이 드는 단점 셋: (1) 입력을 한꺼번에 내놓을 버퍼가 필요하다 (2) 가장 긴 패턴에 입력층 크기를 맞춰야 한다 (3) 상대 위치와 절대 위치를 가르지 못한다.",
    ], 12, gap=22)
    svg("fig03_shift_register", 880, 320, b, "시간을 자리로 펼친 두 벡터의 거리")


# ── 그림 4. 시간 XOR 의 예측 일정 ─────────────────────────────────────────────
def fig04():
    seq = [1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1]
    ok = all(seq[i + 2] == (seq[i] ^ seq[i + 1]) for i in range(0, len(seq) - 2, 3))
    print("    그림 4: 원문 예시 열이 세 자리마다 XOR 인가 —", ok)
    b = txt(20, 28, "그림 4. 시간 XOR — 다음 비트를 맞힐 수 있는 자리는 셋 중 하나", 15, anchor="start", weight="bold")
    b += txt(30, 82, "입력", 12, anchor="start") + txt(30, 132, "맞혀야 할 것", 12, anchor="start")
    for k in range(15):
        x = 140 + 46 * k
        b += box(x, 60, 40, 34, fill=NODE, stroke=INK2, rx=3) + txt(x + 20, 83, str(seq[k]), 14, family=MONO)
        if k < 14:
            pred = (k % 3) == 1   # 입력이 둘째 비트일 때 다음(셋째)은 XOR
            fill = OK_SOFT if pred else NODE
            b += box(x, 110, 40, 34, fill=fill, stroke=OK if pred else INK2, rx=3) + txt(x + 20, 133, str(seq[k + 1]), 14, family=MONO)
            b += txt(x + 20, 162, "정해짐" if pred else "우연", 10, fill=OK if pred else MUTED)
        else:
            b += box(x, 110, 40, 34, fill=NODE, stroke=INK2, rx=3) + txt(x + 20, 133, "?", 14)
    b += txt(140, 196, "아래 한계 — 어떤 예측기도 기대값으로 이보다 낮출 수 없다 (내가 센 것, 출력 o 는 0 과 1 사이)", 12, anchor="start", weight="bold")
    rows = [("", "우연인 자리 (2/3)", "맞힐 수 있는 자리 (1/3)"),
            ("제곱 오차 (o - t)²", "0.25 (o = 0.5 로 걸 때)", "0"),
            ("제곱근 (RMS)", "0.50", "0"),
            ("늘 XOR 을 0/1 로 내면", "제곱 오차 0.50", "0")]
    for r, row in enumerate(rows):
        y = 214 + 26 * r
        for c, t in enumerate(row):
            x = [140, 380, 600][c]
            b += txt(x, y + 16, t, 12, anchor="start", fill=INK if r == 0 else INK2, weight="bold" if r == 0 else None)
        b += line(140, y + 22, 820, y + 22, LINE, 0.8)
    b += txt(140, 338, "원문 설정: 3,000 비트 열, 입력 1 · 은닉 2 · 문맥 2 · 출력 1, 열을 600 번 통과", 11, fill=MUTED, anchor="start")
    svg("fig04_xor_schedule", 880, 356, b, "시간 XOR 의 예측 가능한 자리")


# ── 그림 5. 원문 그림 3 의 값과 아래 한계 ─────────────────────────────────────
def fig05():
    x0, x1, y0, y1 = 110, 640, 60, 330
    fx = lambda c: x0 + (c - 0.5) * (x1 - x0) / 12.5
    fy = lambda v: y1 - v * (y1 - y0) / 0.6
    b = txt(20, 28, "그림 5. 원문 그림 3 을 읽은 값 — 캡션의 「RMS」 로는 나올 수 없는 높이", 15, anchor="start", weight="bold")
    b += yaxis(x0, x1, fy, [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    for c in range(1, 13):
        b += txt(fx(c), y1 + 18, str(c), 10, fill=MUTED)
        if c % 3 == 2:
            b += box(fx(c) - 14, y0, 28, y1 - y0, fill=OK_SOFT, stroke="none", rx=0)
    b += txt((x0 + x1) / 2, y1 + 38, "원문 가로축 「Cycle」 (12 개 입력 창 안의 자리)", 11, fill=INK2)
    b += line(x0, fy(0.5), x1, fy(0.5), NO, 1.8, dash="7 4")
    b += txt(x1 + 8, fy(0.5) + 4, "RMS 로 읽을 때 우연 자리의 아래 한계 0.50", 11, fill=NO, anchor="start")
    b += line(x0, fy(0.25), x1, fy(0.25), FWD, 1.8, dash="7 4")
    b += txt(x1 + 8, fy(0.25) + 4, "제곱 오차로 읽을 때 우연 자리의 아래 한계 0.25", 11, fill=FWD, anchor="start")
    pts = [(fx(c + 1), fy(v)) for c, v in enumerate(READ_FIG3)]
    b += polyline(pts, CODE, 2.2)
    for (x, y), v in zip(pts, READ_FIG3):
        b += circ(x, y, 3.5, fill=CODE_SOFT, stroke=CODE)
        b += txt(x, y - 9, "%.2f" % v, 10, fill=CODE)
    pred = [v for c, v in enumerate(READ_FIG3) if (c + 1) % 3 == 2]
    rnd = [v for c, v in enumerate(READ_FIG3) if (c + 1) % 3 != 2]
    print("    그림 5: 맞힐 자리 %.2f~%.2f (평균 %.3f), 우연 자리 %.2f~%.2f (평균 %.3f)" % (
        min(pred), max(pred), sum(pred) / len(pred), min(rnd), max(rnd), sum(rnd) / len(rnd)))
    b += lines_at(x1 + 8, 252, [
        ("초록 띠 = 맞힐 수 있는 자리 (2 · 5 · 8 · 11)", OK),
        ("그 자리 값 %.2f ~ %.2f" % (min(pred), max(pred)), INK2),
        ("우연 자리 값 %.2f ~ %.2f" % (min(rnd), max(rnd)), INK2),
        ("우연 자리 8 점이 모두 0.50 아래다.", NO, "bold"),
        ("제곱 오차(근 없음)로 읽어야", INK2),
        ("0.25 위에 놓여 말이 된다.", INK2),
    ], 11, gap=19)
    b += txt(20, 388, "값은 300 dpi 스캔 쪽에서 축 상자(0.00 · 0.50 눈금)를 찾아 꺾이는 점의 높이를 픽셀로 읽었다. 읽기 오차 ±0.01. 본문은 같은 그림을 「sum squared error」 라고 부른다.", 11, fill=MUTED, anchor="start")
    svg("fig05_fig3_readings", 960, 404, b, "원문 그림 3 의 읽은 값과 아래 한계")


# ── 그림 6. 표 1 의 비트 ──────────────────────────────────────────────────────
TABLE1 = {"b": [1, 0, 1, 0, 0, 1], "d": [1, 0, 1, 1, 0, 1], "g": [1, 0, 1, 0, 1, 1],
          "a": [0, 1, 0, 0, 1, 1], "i": [0, 1, 0, 1, 0, 1], "u": [0, 1, 0, 1, 1, 1]}
FEAT = ["자음", "모음", "막힘", "높음", "뒤", "유성"]


def fig06():
    cons = ["b", "d", "g"]
    p = [sum(TABLE1[c][k] for c in cons) / 3.0 for k in range(6)]
    var = [q * (1 - q) for q in p]
    sse = sum(var)
    per_target = {c: sum((TABLE1[c][k] - p[k]) ** 2 for k in range(6)) for c in cons}
    print("    그림 6: 자음 자리 비트별 확률", ["%.3f" % q for q in p], "기대 제곱 오차 합 %.3f (근 %.3f)" % (sse, math.sqrt(sse)))
    print("            과녁별 제곱 오차 합", {c: round(v, 3) for c, v in per_target.items()},
          "근", {c: round(math.sqrt(v), 3) for c, v in per_target.items()})
    b = txt(20, 28, "그림 6. 원문 표 1 — 여섯 비트 가운데 정보를 나르는 것은 셋", 15, anchor="start", weight="bold")
    for k, f in enumerate(FEAT):
        b += txt(160 + 70 * k, 70, "%d %s" % (k + 1, f), 12, weight="bold")
    for r, c in enumerate(["b", "d", "g", "a", "i", "u"]):
        y = 82 + 34 * r
        b += txt(100, y + 22, c, 15, family=MONO, weight="bold")
        for k in range(6):
            x = 130 + 70 * k
            red = k in (1, 2, 5)
            fill = (NO_SOFT if red else FWD_SOFT) if TABLE1[c][k] else NODE
            b += box(x, y, 60, 30, fill=fill, stroke=INK2, rx=3) + txt(x + 30, y + 21, str(TABLE1[c][k]), 14, family=MONO)
    b += txt(130, 312, "빨간 칸: 2 = 1 - (1 번), 3 = 1 번, 6 = 늘 1 — 1 번 비트만 알면 정해진다", 11, fill=NO, anchor="start")
    b += txt(130, 330, "파란 칸 셋(1 · 4 · 5)이 여섯 글자를 가른다: (자음, 높음, 뒤)", 11, fill=FWD, anchor="start")
    # 오른쪽: 자음 자리
    X = 580
    b += txt(X, 70, "자음을 맞혀야 하는 자리 (자음은 무작위)", 12, anchor="start", weight="bold")
    b += txt(X, 92, "비트", 11, anchor="start", fill=INK2) + txt(X + 70, 92, "1 일 확률", 11, anchor="start", fill=INK2) + txt(X + 160, 92, "기대 제곱 오차", 11, anchor="start", fill=INK2)
    for k in range(6):
        y = 116 + 24 * k
        b += txt(X, y, "%d %s" % (k + 1, FEAT[k]), 12, anchor="start")
        b += txt(X + 70, y, "%.3f" % p[k], 12, anchor="start", family=MONO)
        b += txt(X + 160, y, "%.3f" % var[k], 12, anchor="start", family=MONO, fill=NO if var[k] > 0 else INK2)
    b += line(X, 262, X + 270, 262, INK2, 1)
    b += txt(X, 282, "합 %.3f (제곱근 %.3f) — 완벽한 학습자의 기대값" % (sse, math.sqrt(sse)), 12, anchor="start", weight="bold")
    b += txt(X, 304, "과녁이 b 면 %.3f, d · g 면 %.3f (각 제곱근 %.2f · %.2f)" % (
        per_target["b"], per_target["d"], math.sqrt(per_target["b"]), math.sqrt(per_target["d"])), 11, anchor="start", fill=INK2)
    b += txt(X, 324, "모음 자리는 자음이 정해 주므로 아래 한계 0", 11, anchor="start", fill=INK2)
    svg("fig06_table1_bits", 900, 346, b, "표 1 의 비트 중복과 자음 자리의 아래 한계")


# ── 그림 7. 원문 그림 4 · 5 를 읽은 값 ────────────────────────────────────────
def fig07():
    b = txt(20, 28, "그림 7. 원문 그림 4 · 5(a) · 5(b) 를 읽은 값 — 같은 시험 열 20 점", 15, anchor="start", weight="bold")
    x0, x1 = 120, 860
    fx = lambda i: x0 + (i + 0.5) * (x1 - x0) / 20
    panels = [("그림 4 — 출력 6 비트 전체", READ_FIG4, 1.0, 74),
              ("그림 5(a) — 1 번 비트 (자음)", READ_FIG5A, 0.8, 266),
              ("그림 5(b) — 4 번 비트 (높음)", READ_FIG5B, 0.8, 420)]
    for title, vals, vmax, top in panels:
        h = 150 if vmax == 1.0 else 120
        fy = lambda v, top=top, h=h, vmax=vmax: top + h - v * h / vmax
        b += txt(x0, top - 6, title, 12, anchor="start", weight="bold")
        ticks = [0, 0.5, 1.0] if vmax == 1.0 else [0, 0.4, 0.8]
        b += yaxis(x0, x1, fy, ticks, "%.1f")
        for i, t in enumerate(TARGETS):
            if t in "bdg":
                b += box(fx(i) - 15, top, 30, h, fill=REV_SOFT, stroke="none", rx=0)
        pts = []
        for i, v in enumerate(vals):
            if v is None:
                if pts:
                    b += polyline(pts, CODE, 2)
                pts = []
                b += txt(fx(i), top + h - 8, "빈 점", 10, fill=NO)
                continue
            pts.append((fx(i), fy(v)))
        b += polyline(pts, CODE, 2)
        for i, v in enumerate(vals):
            if v is not None:
                c = NO if (title.startswith("그림 5(a)") and i in (7, 13)) else CODE
                b += circ(fx(i), fy(v), 3.2, fill=CODE_SOFT, stroke=c)
                if v >= 0.15 or c == NO:
                    b += txt(fx(i), fy(v) - 7, "%.2f" % v, 9, fill=c)
    for i, t in enumerate(TARGETS):
        b += txt(fx(i), 566, t, 13, family=MONO, weight="bold" if t in "bdg" else None, fill=REV if t in "bdg" else INK)
    b += txt(x0 - 10, 566, "과녁", 11, anchor="end", fill=INK2)
    b += lines_at(20, 594, [
        ("주황 띠 = 자음을 맞혀야 하는 자리. 그림 4 에서 자음 자리 다섯의 값 0.43 ~ 0.77, 모음 자리 열넷의 값 0.02 ~ 0.36 — 둘이 겹치지 않는다.", INK2),
        ("빨간 테 = 8 · 14 번 점(셋째 u). 1 번 비트 오차 0.06 · 0.05 가 4 번 비트 오차 0.02 · 0.02 보다 크다 — 원문의 「모든 시점에서 1 번이 4 번보다 낮다」 와 어긋나는 두 점.", NO),
        ("그림 4 의 18 번 점(과녁 d)은 선이 끊겨 있다. 그림 5 의 두 칸에는 있다. 세로축 단위는 세 칸 모두 「0 -y- 1」 뿐이다.", INK2),
        ("읽기 오차: 그림 4 ±0.02, 그림 5 ±0.01 ~ 0.02. 300 dpi 스캔에서 축 상자를 픽셀로 찾고 꼭짓점 높이를 읽었다.", MUTED),
    ], 11, gap=19)
    svg("fig07_fig4_fig5_readings", 900, 676, b, "원문 그림 4 와 5 의 읽은 값")


# ── 그림 8. 원문 그림 6 — 낱말 경계 ──────────────────────────────────────────
def fig08():
    letters = [c for c in FIG6_TEXT if c != " "]
    assert len(letters) == len(READ_FIG6) == 54, len(letters)
    onset = []
    k = 0
    for w in FIG6_TEXT.split(" "):
        onset.append(k)
        k += len(w)
    x0, x1, y0, y1 = 70, 1060, 60, 330
    fx = lambda i: x0 + (i + 0.5) * (x1 - x0) / 54
    fy = lambda v: y1 - v * (y1 - y0) / 3.5
    b = txt(20, 28, "그림 8. 원문 그림 6 을 읽은 값 — 낱말 첫 글자에서 오르는가", 15, anchor="start", weight="bold")
    b += yaxis(x0, x1, fy, [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], "%.1f")
    b += line(x0, fy(math.sqrt(5)), x1, fy(math.sqrt(5)), NO, 1.6, dash="7 4")
    b += txt(x1 - 4, fy(math.sqrt(5)) - 9, "√5 = 2.24: 출력 5 비트 오차의 제곱근이 넘을 수 없는 선", 11, fill=NO, anchor="end")
    for o in onset:
        b += line(fx(o) - 9, y0, fx(o) - 9, y1, LINE, 1)
    b += polyline([(fx(i), fy(v)) for i, v in enumerate(READ_FIG6)], CODE, 1.8)
    hits, miss, false_up = 0, [], []
    for i, v in enumerate(READ_FIG6):
        up = i > 0 and v > READ_FIG6[i - 1]
        if i in onset and i > 0:
            if up:
                hits += 1
            else:
                miss.append(i)
        elif i > 0 and up:
            false_up.append(i)
        col = OK if (i in onset) else CODE
        b += circ(fx(i), fy(v), 3, fill=CODE_SOFT if i not in onset else OK_SOFT, stroke=col)
        b += txt(fx(i), y1 + 16, letters[i], 11, family=MONO, fill=OK if i in onset else INK, weight="bold" if i in onset else None)
    for i in miss:
        b += circ(fx(i), fy(READ_FIG6[i]), 7, fill="none", stroke=NO, sw=1.8)
    for i in false_up:
        b += circ(fx(i), fy(READ_FIG6[i]), 7, fill="none", stroke=REV, sw=1.8)
    n_on = len(onset) - 1
    print("    그림 8: 낱말 첫 글자 %d 자리 중 앞 점보다 오른 것 %d, 안 오른 자리 %s, 낱말 안에서 오른 자리 %s" % (
        n_on, hits, [letters[i] for i in miss], [(i, letters[i], round(READ_FIG6[i] - READ_FIG6[i - 1], 2)) for i in false_up]))
    print("            가장 높은 값 %.2f > √5 = %.3f" % (max(READ_FIG6), math.sqrt(5)))
    b += lines_at(20, 372, [
        ("초록 글자 = 낱말 첫 글자 (원문 그림의 글자 라벨은 맞혀야 할 글자다). 첫 점(m)을 빼면 첫 글자 자리가 %d 개다." % n_on, OK),
        ("내가 센 것: 앞 점보다 오른 첫 글자 자리 %d / %d. 안 오른 하나(빨간 원)는 한 글자 낱말 a 뒤의 b." % (hits, n_on), INK2),
        ("낱말 안에서 오른 자리(주황 원) %d 개: %s. they 의 y 는 원문도 짚었다. 나머지 둘의 오름은 0.2 아래라 읽기 오차 ±0.1 에 걸린다." % (
            len(false_up), ", ".join("%s(+%.2f)" % (letters[i], READ_FIG6[i] - READ_FIG6[i - 1]) for i in false_up)), REV),
        ("가장 높은 점 %.2f 가 √5 = 2.24 를 넘는다 — 캡션의 「root mean squared」 로는 나올 수 없고, 제곱 오차의 합(최대 5)이면 들어간다." % max(READ_FIG6), NO),
        ("이 열은 원문 표 2(학습 열의 한 토막)와 같은 글월이다 — 그림 6 은 학습 열 위의 오차다.", INK2),
    ], 11, gap=19)
    svg("fig08_fig6_word_onsets", 1100, 474, b, "원문 그림 6 의 읽은 값과 낱말 경계")


# ── 그림 9. 표 2 의 글자 부호 ─────────────────────────────────────────────────
TABLE2 = {"m": "01101", "a": "00001", "n": "01110", "y": "11001", "e": "00101", "r": "10010",
          "s": "10011", "g": "00111", "o": "01111", "b": "00010", "d": "00100", "i": "01001", "l": "01100"}


def fig09():
    rows = sorted(TABLE2.items(), key=lambda kv: ord(kv[0]))
    same = 0
    b = txt(20, 28, "그림 9. 원문 표 2 의 글자 부호 — 「무작위 5 비트」 가 아니라 알파벳 순번의 이진수", 15, anchor="start", weight="bold")
    heads = ["글자", "표 2 의 부호", "알파벳 순번", "순번의 5 비트 이진수", "같은가"]
    xs = [60, 160, 320, 460, 680]
    for x, h in zip(xs, heads):
        b += txt(x, 64, h, 12, anchor="start", weight="bold")
    for r, (c, code) in enumerate(rows):
        y = 84 + 24 * r
        pos = ord(c) - ord("a") + 1
        bn = format(pos, "05b")
        eq = (bn == code)
        same += eq
        b += txt(xs[0], y + 4, c, 13, anchor="start", family=MONO, weight="bold")
        b += txt(xs[1], y + 4, code, 13, anchor="start", family=MONO)
        b += txt(xs[2], y + 4, str(pos), 13, anchor="start", family=MONO)
        b += txt(xs[3], y + 4, bn, 13, anchor="start", family=MONO)
        b += txt(xs[4], y + 4, "같다" if eq else "다르다", 12, anchor="start", fill=OK if eq else NO)
    print("    그림 9: 표 2 의 글자 %d 개 중 알파벳 순번 이진수와 같은 것 %d" % (len(rows), same))
    y = 84 + 24 * len(rows) + 14
    b += lines_at(60, y, [
        ("내가 센 것: %d 글자 중 %d 글자가 같다. 원문 본문은 「each letter ... was converted into a 5-bit random vector」 라고 적는다." % (len(rows), same), INK, "bold"),
        "알파벳 순번 부호라면 비슷한 순번끼리 비트를 나눈다 — 예: a(00001) 와 e(00101) 는 한 비트만 다르다. 그림 6 의 오차는 이 겹침 위에서 잰 것이다.",
        "표 2 의 마지막 입력 줄은 「11001 (i)」 로 찍혀 있다 — 11001 은 y 의 부호이고 i 는 01001 이다. 출력 칸은 그 줄이 없어 한 줄 짧다.",
    ], 11, gap=20)
    svg("fig09_table2_codes", 900, y + 66, b, "표 2 의 글자 부호와 알파벳 순번")


# ── 그림 10. 문장 말뭉치의 수 ─────────────────────────────────────────────────
def fig10():
    n_tmpl, n_two, n_sent = 16, 4, 10000
    mean = (n_two * 2 + (n_tmpl - n_two) * 3) / float(n_tmpl)
    p2 = n_two / float(n_tmpl)
    sd = math.sqrt(n_sent * p2 * (1 - p2))
    exp = n_sent * mean
    nums = [(27354, 2, "196 · 199 쪽"), (27454, 3, "204 · 205 쪽"), (27534, 3, "195 · 197 쪽")]
    print("    그림 10: 틀 %d 개를 고르게 뽑으면 문장당 %.3f 낱말, 10,000 문장의 기댓값 %.0f, 표준편차 %.1f" % (n_tmpl, mean, exp, sd))
    for n, c, where in nums:
        print("            %d (%d 번, %s): z = %+.2f" % (n, c, where, (n - exp) / sd))
    x0, x1 = 120, 820
    lo, hi = 27300, 27600
    fx = lambda v: x0 + (v - lo) * (x1 - x0) / float(hi - lo)
    b = txt(20, 28, "그림 10. 문장 말뭉치의 길이가 원문에 세 가지로 적혀 있다", 15, anchor="start", weight="bold")
    b += box(fx(exp - 2 * sd), 70, fx(exp + 2 * sd) - fx(exp - 2 * sd), 70, fill=FWD_SOFT, stroke="none", rx=0)
    b += box(fx(exp - sd), 70, fx(exp + sd) - fx(exp - sd), 70, fill="#B9D3E0", stroke="none", rx=0)
    b += line(fx(exp), 64, fx(exp), 146, FWD, 1.6, dash="5 3")
    b += txt(fx(exp), 58, "기댓값 %s (틀 16 개를 고르게 뽑는다고 둘 때)" % format(int(exp), ","), 11, fill=FWD)
    b += line(x0, 140, x1, 140, INK2, 1.2)
    for v in range(lo, hi + 1, 50):
        b += line(fx(v), 140, fx(v), 145, INK2, 1) + txt(fx(v), 160, format(v, ","), 10, fill=MUTED)
    for n, c, where in nums:
        b += line(fx(n), 80, fx(n), 140, NO if abs(n - exp) / sd > 2 else CODE, 2.4)
        b += txt(fx(n), 186, "%s" % format(n, ","), 12, weight="bold", fill=NO if abs(n - exp) / sd > 2 else CODE)
        b += txt(fx(n), 204, "%d 번 · %s" % (c, where), 10, fill=INK2)
        b += txt(fx(n), 220, "z = %+.1f" % ((n - exp) / sd), 10, fill=INK2)
    b += txt(fx(exp + sd) + 4, 132, "±1 표준편차 %.0f" % sd, 10, fill=FWD, anchor="start")
    b += lines_at(30, 256, [
        ("같은 말뭉치(10,000 문장)의 낱말 수가 27,534 (세 번) · 27,354 (두 번) · 27,454 (세 번) 으로 적혀 있다. 앞 둘은 두 자리가 뒤바뀐 꼴이다.", INK),
        ("표 4 의 틀은 16 개이고 그중 두 낱말 틀이 4 개다(본문은 「15 개」). 틀을 고르게 뽑는다는 것은 원문에 없는 가정이다 — 그 가정 아래서", INK2),
        ("27,534 는 +0.8, 27,454 는 −1.1, 27,354 는 −3.4 표준편차 자리다. 어느 것이 맞는지는 이것으로 정하지 않는다.", INK2),
        ("표 3 의 범주는 12 줄인데 본문은 「Thirteen classes」 라고 적는다. 표 3 의 NOUN-FOOD 예시 「cookie, break」 의 break 는 그림 7 의 bread 로 읽힌다.", INK2),
    ], 11, gap=20)
    svg("fig10_corpus_counts", 880, 346, b, "문장 말뭉치 길이 셋과 기댓값")


# ── 그림 11. zog 는 man 의 자리에 들어갔는가 ─────────────────────────────────
def fig11():
    b = txt(20, 28, "그림 11. 사람 갈래가 합쳐지는 거리 — 원문 그림 7(학습 말뭉치) 과 그림 8(man 을 zog 로 바꾼 새 말뭉치)", 15, anchor="start", weight="bold")
    x0, x1 = 120, 820
    fx = lambda v: x1 - v * (x1 - x0) / 1.7
    def axis(y):
        s = line(x0, y, x1, y, INK2, 1.2)
        for v in [0, 0.5, 1.0, 1.5]:
            s += line(fx(v), y, fx(v), y + 5, INK2, 1) + txt(fx(v), y + 19, "%.1f" % v, 10, fill=MUTED)
        return s
    def tree(y, leaves, joins, title, hl):
        s = txt(x0, y - 8, title, 12, anchor="start", weight="bold")
        ly = [y + 14 + 22 * k for k in range(len(leaves))]
        for k, n in enumerate(leaves):
            col = NO if n == hl else INK
            s += txt(x1 + 10, ly[k] + 4, n, 12, anchor="start", fill=col, weight="bold" if n == hl else None)
        cur_x, cur_y = fx(0), ly[0]
        s += line(fx(0), ly[0], x1, ly[0], INK2, 1.6)
        for d, k in joins:
            nx = fx(d)
            s += line(nx, cur_y, cur_x, cur_y, INK2, 1.6)
            s += line(nx, ly[k], x1, ly[k], NO if leaves[k] == hl else INK2, 1.6)
            s += line(nx, cur_y, nx, ly[k], INK2, 1.6)
            s += box(nx - 34, ly[k] - 17, 30, 14, fill=BG, stroke="none", rx=2)
            s += txt(nx - 5, ly[k] - 6, "%.2f" % d, 10, fill=CODE, anchor="end")
            cur_x, cur_y = nx, (cur_y + ly[k]) / 2
        return s
    f7, f8 = READ_FIG7, READ_FIG8
    b += tree(70, ["woman", "girl", "man", "boy", "동물 갈래"],
              [(f7["woman-girl"], 1), (f7["+man"], 2), (f7["+boy"], 3), (f7["사람+동물"], 4)],
              "그림 7 — man 은 사람 셋 사이(%.2f)에서 합쳐진다" % f7["+man"], "man")
    b += axis(196)
    b += tree(260, ["woman", "girl", "boy", "zog", "동물 갈래"],
              [(f8["woman-girl"], 1), (f8["+boy"], 2), (f8["+zog"], 3), (f8["(사람+zog)+동물"], 4)],
              "그림 8 — zog 는 사람 셋이 다 모인 뒤(%.2f)에 붙는다" % f8["+zog"], "zog")
    b += axis(386)
    rB7, rB8 = f7["+man"] / f7["사람+동물"], f8["+zog"] / f8["(사람+zog)+동물"]
    rA7, rA8 = (f7["+man"] + 0.5) / (f7["사람+동물"] + 0.5), (f8["+zog"] + 0.5) / (f8["(사람+zog)+동물"] + 0.5)
    print("    그림 11: 읽기 B  man 합류/사람-동물 합류 = %.2f, zog = %.2f" % (rB7, rB8))
    print("            읽기 A  man = %.2f, zog = %.2f" % (rA7, rA8))
    b += lines_at(30, 432, [
        ("거리는 그림 12 의 읽기 B(잎이 0 에 오는 읽기)로 적었다. 읽기 오차 ±0.02.", MUTED),
        ("내가 센 비: man 이 붙는 거리 / 사람 갈래가 동물 갈래와 합쳐지는 거리 = %.2f, 같은 비가 zog 는 %.2f (읽기 A 로는 %.2f 대 %.2f)." % (rB7, rB8, rA7, rA8), INK, "bold"),
        ("zog 는 생물 · 사람 쪽 가지에 들어간다(원문의 말과 같다). 다만 사람 셋과의 거리로는 man 이 있던 자리보다 동물 갈래와의 합류점에 가깝게 붙는다.", INK2),
        ("두 그림은 말뭉치가 다르고(그림 8 은 새 10,000 문장을 한 번 통과) 거리의 크기도 다르다(woman-girl %.2f 대 %.2f) — 그래서 비로 견줬다." % (f7["woman-girl"], f8["woman-girl"]), INK2),
    ], 11, gap=20)
    svg("fig11_zog_vs_man", 960, 520, b, "그림 7 과 그림 8 의 사람 갈래 합류 거리")


# ── 그림 12. 계통수 가로축의 눈금 ─────────────────────────────────────────────
def fig12():
    b = txt(20, 28, "그림 12. 원문 그림 7 · 8 의 가로축 — 간격이 같은 눈금 다섯에 「2.0 1.5 1.0 0.0 -0.5」", 15, anchor="start", weight="bold")
    printed = ["2.0", "1.5", "1.0", "0.0", "-0.5"]
    readA = ["2.0", "1.5", "1.0", "0.5", "0.0"]
    readB = ["1.5", "1.0", "0.5", "0.0", "-0.5"]
    for r, (name, ticks) in enumerate([("그림 7", TICKS_FIG7), ("그림 8", TICKS_FIG8)]):
        y = 92 + 130 * r
        gaps = [ticks[k + 1] - ticks[k] for k in range(4)]
        print("    그림 12: %s 눈금 간격(300 dpi 픽셀)" % name, gaps)
        x0 = 140
        sc = 520.0 / (ticks[-1] - ticks[0])
        b += txt(40, y + 4, name, 13, anchor="start", weight="bold")
        b += line(x0, y, x0 + 520, y, INK2, 1.4)
        if r == 0:
            # 잎 선 끝이 놓인 범위(눈으로 읽음): 「0.0」 눈금 기준 -20 ~ +41 px
            xa, xb = x0 + (ticks[3] - 20 - ticks[0]) * sc, x0 + (ticks[3] + 41 - ticks[0]) * sc
            b += box(xa, y - 30, xb - xa, 60, fill=OK_SOFT, stroke="none", rx=2)
            b += txt((xa + xb) / 2, y - 34, "잎 선 끝", 10, fill=OK)
        for k, t in enumerate(ticks):
            x = x0 + (t - ticks[0]) * sc
            b += line(x, y - 6, x, y + 6, INK2, 1.4)
            b += txt(x, y - 12, printed[k], 12, fill=INK)
            b += txt(x, y + 22, readA[k], 11, fill=MUTED)
            b += txt(x, y + 38, readB[k], 11, fill=FWD, weight="bold")
            if k < 4:
                b += txt(x + (ticks[k + 1] - t) * sc / 2, y + 58, "%.0f px" % gaps[k], 10, fill=MUTED)
        b += txt(x0 + 540, y - 12, "원문 라벨", 11, fill=INK, anchor="start")
        b += txt(x0 + 540, y + 22, "읽기 A: 뒤 둘을 고침", 11, fill=MUTED, anchor="start")
        b += txt(x0 + 540, y + 38, "읽기 B: 앞 셋을 고침", 11, fill=FWD, anchor="start")
    b += lines_at(40, 360, [
        ("눈금 간격이 그림 7 에서 183 ~ 186 픽셀, 그림 8 에서 200 ~ 202 픽셀로 고르다. 찍힌 라벨대로면 1.0 → 0.0 한 칸만 1.0 이고 나머지 칸은 0.5 다.", INK2),
        ("라벨 다섯이 한 간격으로 맞으려면 앞 셋(읽기 B)이나 뒤 둘(읽기 A) 가운데 한쪽이 틀렸다. 원문은 축이 무슨 거리인지도 적지 않는다.", INK2),
        ("그림 7 의 잎 선 끝은 「0.0」 눈금 왼쪽 20 픽셀 ~ 오른쪽 41 픽셀에 놓인다(눈으로 읽음). 잎이 거리 0 이라면 읽기 B 가 맞는다 — 이 노트는 B 를 쓴다.", FWD),
    ], 11, gap=20)
    svg("fig12_dendrogram_axis", 900, 430, b, "계통수 가로축 눈금 라벨")


# ── 그림 13. 그림 9 의 boy 출현 ───────────────────────────────────────────────
def fig13():
    blocks = [("위 덩어리", 9, 4), ("가운데 덩어리", 0, 32), ("아래 덩어리", 6, 1)]
    tot_f = sum(f for _, f, _ in blocks)
    tot_i = sum(i for _, _, i in blocks)
    print("    그림 13: BOY 출현 %d (문장 끝 %d, 문장 첫머리 %d), 첫머리가 끝 쪽 덩어리에 들어간 것 %d" % (
        tot_f + tot_i, tot_f, tot_i, blocks[0][2] + blocks[2][2]))
    b = txt(20, 28, "그림 13. 원문 그림 9 의 BOY 출현 — 잎 순서로 센 위치별 덩어리", 15, anchor="start", weight="bold")
    x0 = 200
    for r, (name, f, i) in enumerate(blocks):
        y = 70 + 52 * r
        b += txt(x0 - 14, y + 20, name, 12, anchor="end")
        b += box(x0, y, f * 12, 30, fill=FWD_SOFT, stroke=FWD, rx=2) if f else ""
        b += box(x0 + f * 12, y, i * 12, 30, fill=REV_SOFT, stroke=REV, rx=2) if i else ""
        b += txt(x0 + (f + i) * 12 + 10, y + 20, "문장 끝 %d · 첫머리 %d" % (f, i), 11, anchor="start", fill=INK2)
    b += box(x0, 238, 20, 14, fill=FWD_SOFT, stroke=FWD, rx=2) + txt(x0 + 28, 250, "BOY 가 문장 끝 (예: woman smell BOY)", 11, anchor="start", fill=INK2)
    b += box(x0 + 320, 238, 20, 14, fill=REV_SOFT, stroke=REV, rx=2) + txt(x0 + 348, 250, "BOY 가 문장 첫머리 (예: BOY see rock)", 11, anchor="start", fill=INK2)
    b += lines_at(30, 290, [
        ("내가 센 것: 잎 %d 개 = 문장 끝 %d + 첫머리 %d. 첫머리 %d 개 중 %d 개는 끝 쪽 덩어리에 섞였다 — 원문의 「(with some exceptions)」." % (
            tot_f + tot_i, tot_f, tot_i, tot_i, blocks[0][2] + blocks[2][2]), INK, "bold"),
        ("글자가 겹쳐 찍힌 잎이 있어 개수에 ±2 를 둔다. 원문은 출현 수 · 섞인 수를 적지 않는다.", MUTED),
        ("첫머리 출현의 라벨은 BOY 뒤에 올 낱말을 보여 준다(BOY see rock). 그 시점의 은닉 상태는 뒤 낱말을 보지 못했다 — 라벨이 문맥이 아니라 문장 이름이다.", INK2),
        ("라벨 가운데 woman eat BOY · man eat BOY · BOY eat woman 은 표 4 의 틀(사람 eat 음식, 공격자 eat 사람 · 동물 · 음식)로 만들 수 없다.", NO),
    ], 11, gap=20)
    svg("fig13_fig9_tokens", 900, 380, b, "그림 9 의 BOY 출현 위치별 덩어리")


# ── 그림 14. 망 넷의 크기 ─────────────────────────────────────────────────────
NETS = [  # 이름, 입력, 은닉(=문맥), 출력, 열 길이, 통과 수, 길이 주석
    ("시간 XOR", 1, 2, 1, 3000, 600, "3,000 비트"),
    ("글자 열 (ba · dii · guuu)", 6, 20, 6, 3000, 200, "자음 1,000 개 → 약 3,000 글자"),
    ("낱말 찾기", 5, 20, 5, 4963, 10, "4,963 글자"),
    ("문장 → 품사", 31, 150, 31, 27534, 6, "27,534 낱말"),
]


def params(i, h, o):
    w = i * h + h * h + h * o
    return w, w + h + o, h * h


def fig14():
    b = txt(20, 28, "그림 14. 망 넷의 크기와 학습 걸음 수 — 내가 센 것", 15, anchor="start", weight="bold")
    heads = ["과제", "입력-은닉(=문맥)-출력", "연결 무게", "편향 넣으면", "문맥→은닉 몫", "열 길이 × 통과", "학습 걸음"]
    xs = [30, 230, 410, 510, 620, 730, 900]
    for x, hd in zip(xs, heads):
        b += txt(x, 64, hd, 12, anchor="start", weight="bold")
    for r, (name, i, h, o, L, P, note) in enumerate(NETS):
        y = 92 + 30 * r
        w, wb, hh = params(i, h, o)
        steps = L * P
        print("    그림 14: %s  무게 %d (편향 넣으면 %d), 문맥->은닉 %d (%.1f%%), 걸음 %d" % (name, w, wb, hh, 100.0 * hh / w, steps))
        cells = [name, "%d-%d-%d" % (i, h, o), format(w, ","), format(wb, ","), "%.1f%%" % (100.0 * hh / w),
                 "%s × %d" % (format(L, ","), P), format(steps, ",")]
        for x, c in zip(xs, cells):
            b += txt(x, y, c, 12, anchor="start", fill=INK if x == 30 else INK2)
        b += line(30, y + 10, 1010, y + 10, LINE, 0.8)
    b += lines_at(30, 236, [
        "원문은 편향(bias)을 쓰는지 적지 않는다. 그래서 둘을 다 적었다. 글자 열 과제의 길이는 자음 1,000 개에 모음이 1 · 2 · 3 개씩 붙는 규칙에서 낸 기댓값이다.",
        "문맥→은닉 무게가 은닉 유닛 수의 제곱이라, 은닉 150 인 문장 망에서는 연결 무게의 70.8% 가 기억을 읽는 자리다.",
        "학습률 · 모멘텀 · 처음 무게 범위 · 무작위 씨앗 수는 넷 다 적혀 있지 않다.",
    ], 11, gap=20)
    svg("fig14_net_sizes", 1060, 306, b, "망 넷의 파라미터 수와 학습 걸음")


# ── 그림 15. 계보 ─────────────────────────────────────────────────────────────
def fig15():
    b = txt(20, 28, "그림 15. 순차 데이터 갈래의 첫 칸 — 앞에서 받은 것과 뒤로 넘긴 것", 15, anchor="start", weight="bold")
    nodes = [
        (40, 70, "퍼셉트론 1958", "읽음", OK),
        (40, 150, "역전파 1986", "읽음 — 9 절 되먹임 망 펼치기", OK),
        (40, 230, "Jordan 1986", "안 읽음 — 출력을 상태로 되먹임", MUTED),
        (330, 150, "Elman 1990", "이 노트 — 은닉을 문맥으로 복사", FWD),
        (620, 70, "기울기 소실 1991 · 1994", "안 읽음 — Hochreiter · Bengio 외", MUTED),
        (620, 150, "LSTM 1997", "다음 칸 — 원문 받아 둠", REV),
        (620, 230, "GRU · seq2seq 2014", "그다음 — 원문 받아 둠", REV),
        (620, 310, "Attention 2015 · Transformer 2017", "로드맵 끝 두 칸", MUTED),
    ]
    for x, y, t, s, c in nodes:
        b += box(x, y, 250, 56, fill=NODE, stroke=c, sw=1.6)
        b += txt(x + 125, y + 24, t, 13, weight="bold", fill=INK)
        b += txt(x + 125, y + 44, s, 11, fill=c)
    b += line(165, 126, 165, 148, INK2, 1.4, marker="ai")
    b += line(292, 178, 328, 178, INK2, 1.4, marker="ai")
    b += line(292, 258, 328, 190, INK2, 1.4, marker="ai")
    b += line(582, 178, 618, 178, REV, 1.6, marker="ar")
    b += line(582, 166, 618, 104, MUTED, 1.4, marker="ai")
    b += line(745, 206, 745, 228, INK2, 1.4, marker="ai")
    b += line(745, 286, 745, 308, INK2, 1.4, marker="ai")
    b += lines_at(40, 396, [
        ("넘긴 자리: 원문 204 쪽 — 「활성 함수가 기억에 거듭 걸려 지수로 줄어든다」 · 「오차를 늦게 넣는 과제에서 성능이 나빴다」.", REV),
        ("그 두 문장을 기울기 쪽에서 정리한 것이 1991 · 1994 의 소실 분석이고, 기억을 곱셈이 아니라 덧셈으로 잇는 칸을 둔 것이 LSTM 이다(다음 노트에서 확인).", INK2),
    ], 11, gap=20)
    svg("fig15_lineage", 900, 450, b, "Elman 1990 의 계보")


for f in [fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10, fig11, fig12, fig13, fig14, fig15]:
    f()
