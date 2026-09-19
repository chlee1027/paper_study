# -*- coding: utf-8 -*-
"""퍼셉트론 노트의 그림 일곱 개를 만든다.

색과 글꼴은 DDPM 노트의 그림과 맞췄다 — 저장소의 노트들이 한 벌로 읽히게 하려는 것이다.
그림을 고치려면 이 파일을 고쳐 다시 돌린다. 결과 CSV 를 읽지 않으므로 어디서나 돈다.

  python make_figures.py
"""
import io, os

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"   # 그림 상자 배경
NODE      = "#F6F7F5"   # 노드 안쪽
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 정해져 있는 것, 클래스 0
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 학습하는 것, 클래스 1
REV_SOFT  = "#F2DED2"
OK        = "#1E8449"   # 초록 — 풀린다
NO        = "#C0392B"   # 빨강 — 안 풀린다
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


def txt(x, y, t, size=12, fill=None, anchor="middle", weight=None):
    a = 'x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s"' % (x, y, size, fill or INK, anchor)
    if weight:
        a += ' font-weight="%s"' % weight
    return "<text %s>%s</text>" % (a, t)


def box(x, y, w, h, fill=None, stroke=None, sw=1.2, rx=6):
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-width="%s"/>'
            % (x, y, w, h, rx, fill or NODE, stroke or INK, sw))


# ── 1. 구조 — 감각 · 연합 · 반응 ────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("a1", MUTED), arrow("a2", REV))
b += txt(380, 26, "퍼셉트론의 세 층 — 배우는 것은 마지막 한 줄뿐이다", 13.5, INK, weight=600)
for i, y in enumerate([70, 110, 150, 190]):
    b += '<circle cx="90" cy="%d" r="15" fill="%s" stroke="%s" stroke-width="1.2"/>' % (y, FWD_SOFT, FWD)
for i, y in enumerate([70, 120, 170]):
    b += '<circle cx="330" cy="%d" r="18" fill="%s" stroke="%s" stroke-width="1.2"/>' % (y, NODE, INK)
    b += txt(330, y + 5, "A%d" % (i + 1), 12)
b += '<circle cx="600" cy="120" r="24" fill="%s" stroke="%s" stroke-width="1.6"/>' % (REV_SOFT, REV)
b += txt(600, 125, "R", 14, REV, weight=600)
for y0 in [70, 110, 150, 190]:
    for y1 in [70, 120, 170]:
        b += ('<line x1="105" y1="%d" x2="312" y2="%d" stroke="%s" stroke-width="0.8" opacity="0.55"/>'
              % (y0, y1, MUTED))
for y1 in [70, 120, 170]:
    b += ('<line x1="348" y1="%d" x2="576" y2="%d" stroke="%s" stroke-width="2.2" marker-end="url(#a2)"/>'
          % (y1, 120, REV))
b += txt(90, 232, "감각 층 S", 12.5, FWD, weight=600)
b += txt(90, 250, "빛이 닿는 자리", 11.5, MUTED)
b += txt(330, 232, "연합 층 A", 12.5, INK, weight=600)
b += txt(330, 250, "S 에서 무작위로 연결", 11.5, MUTED)
b += txt(600, 232, "반응 층 R", 12.5, REV, weight=600)
b += txt(600, 250, "0 또는 1 을 낸다", 11.5, MUTED)
b += txt(210, 45, "고정 · 학습하지 않는다", 12, MUTED)
b += txt(462, 42, "학습되는 가중치 w — 이 한 줄만 바뀐다", 12.5, REV, weight=600)
svg("fig01_structure", 760, 270, b,
    "퍼셉트론은 감각 층 S, 연합 층 A, 반응 층 R 로 되어 있고 S 에서 A 로 가는 연결은 무작위로 고정이며 A 에서 R 로 가는 가중치만 학습한다")

# ── 2. 소자 하나의 계산 ────────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("a3", INK)
b += txt(380, 26, "소자 하나가 하는 일 — 더하고, 문턱을 넘었는지 본다", 13.5, INK, weight=600)
ys = [70, 110, 150, 190]
lab = ["x₁", "x₂", "x₃", "x₄"]
ws = ["w₁", "w₂", "w₃", "w₄"]
for y, l, w_ in zip(ys, lab, ws):
    b += box(40, y - 16, 56, 32, NODE, INK, 1.1, 5) + txt(68, y + 5, l, 12.5)
    b += '<line x1="96" y1="%d" x2="266" y2="130" stroke="%s" stroke-width="1.6" marker-end="url(#a3)"/>' % (y, INK2)
    mx, my = 150, y + (130 - y) * (150 - 96) / (266 - 96.0)
    b += txt(mx, my - 7, w_, 12, REV, weight=600)
b += '<circle cx="300" cy="130" r="30" fill="%s" stroke="%s" stroke-width="1.6"/>' % (FWD_SOFT, FWD)
b += txt(300, 137, "Σ", 22, FWD)
b += txt(300, 180, "가중합 z", 12, FWD, weight=600)
b += '<line x1="330" y1="130" x2="404" y2="130" stroke="%s" stroke-width="1.6" marker-end="url(#a3)"/>' % INK2
b += box(410, 96, 130, 68, NODE, REV, 1.6)
b += txt(475, 124, "계단 함수", 12.5, REV, weight=600)
b += txt(475, 146, "z ≥ θ 면 1, 아니면 0", 11.5, REV)
b += '<line x1="540" y1="130" x2="604" y2="130" stroke="%s" stroke-width="1.6" marker-end="url(#a3)"/>' % INK2
b += box(610, 108, 110, 44, REV_SOFT, REV, 1.6) + txt(665, 136, "출력 ŷ ∈ {0, 1}", 12.5, REV)
b += txt(380, 224, "z = w₁x₁ + w₂x₂ + w₃x₃ + w₄x₄ − θ", 14, INK, weight=600)
b += txt(380, 248, "작은 예시: w = (0.6, −0.2), θ = 0.3, x = (1, 1) 이면 z = 0.6 − 0.2 − 0.3 = 0.1 ≥ 0 이라 ŷ = 1", 11.5, INK2)
svg("fig02_one_neuron", 760, 264, b,
    "입력마다 가중치를 곱해 더한 값이 문턱을 넘으면 1, 넘지 못하면 0 을 낸다")

# ── 3. 계단 함수와 기울기 ──────────────────────────────────────────────────
b = txt(380, 26, "계단 함수 — 이 모양이 뒤에서 발목을 잡는다", 13.5, INK, weight=600)
b += '<line x1="80" y1="150" x2="350" y2="150" stroke="%s" stroke-width="1"/>' % INK
b += '<line x1="215" y1="60" x2="215" y2="168" stroke="%s" stroke-width="1"/>' % INK
b += '<path d="M85,150 L215,150" stroke="%s" stroke-width="2.6" fill="none"/>' % REV
b += '<path d="M215,80 L345,80" stroke="%s" stroke-width="2.6" fill="none"/>' % REV
b += '<line x1="215" y1="150" x2="215" y2="80" stroke="%s" stroke-width="2.6" stroke-dasharray="4 3"/>' % REV
b += '<circle cx="215" cy="80" r="4" fill="%s"/>' % REV
b += txt(215, 184, "문턱 θ", 12, INK)
b += txt(70, 84, "1", 12, INK) + txt(70, 154, "0", 12, INK)
b += txt(345, 184, "z", 12, INK)
b += '<line x1="430" y1="150" x2="700" y2="150" stroke="%s" stroke-width="1"/>' % INK
b += '<line x1="565" y1="60" x2="565" y2="168" stroke="%s" stroke-width="1"/>' % INK
b += '<path d="M435,150 L560,150" stroke="%s" stroke-width="2.6"/>' % MUTED
b += '<path d="M570,150 L695,150" stroke="%s" stroke-width="2.6"/>' % MUTED
b += '<line x1="565" y1="150" x2="565" y2="72" stroke="%s" stroke-width="2.6"/>' % NO
b += '<text x="565" y="66" font-size="13" fill="%s" text-anchor="middle" font-weight="600">∞</text>' % NO
b += txt(500, 136, "기울기 0", 12, MUTED)
b += txt(640, 136, "기울기 0", 12, MUTED)
b += txt(565, 184, "θ 에서만 정의되지 않는다", 11.5, NO)
b += txt(215, 210, "출력", 12.5, INK, weight=600)
b += txt(565, 210, "기울기", 12.5, INK, weight=600)
b += txt(380, 238, "어디서나 기울기가 0이라 \"얼마나 틀렸는지\"가 뒤로 흐르지 못한다. 그래서 층을 쌓아도 안쪽을 고칠 길이 없다.",
          11.8, INK2)
svg("fig03_step_and_gradient", 760, 252, b,
    "계단 함수는 문턱 앞뒤로 평평해 기울기가 0이고 문턱에서는 정의되지 않는다")

# ── 4. 결정 경계는 직선 ────────────────────────────────────────────────────
b = '<defs>%s</defs>' % arrow("a4", REV)
b += txt(380, 26, "퍼셉트론이 그을 수 있는 경계는 직선 하나뿐이다", 13.5, INK, weight=600)
b += '<line x1="120" y1="230" x2="420" y2="230" stroke="%s" stroke-width="1"/>' % INK
b += '<line x1="140" y1="60" x2="140" y2="246" stroke="%s" stroke-width="1"/>' % INK
b += txt(425, 234, "x₁", 12, INK, anchor="start") + txt(136, 54, "x₂", 12, INK, anchor="end")
b += '<line x1="160" y1="222" x2="402" y2="74" stroke="%s" stroke-width="2.4"/>' % INK
b += txt(392, 62, "w·x = θ", 12.5, INK, weight=600)
for cx, cy in [(190, 190), (230, 205), (215, 160), (170, 210), (255, 178)]:
    b += '<circle cx="%d" cy="%d" r="7" fill="%s" stroke="%s" stroke-width="1.4"/>' % (cx, cy, FWD_SOFT, FWD)
for cx, cy in [(320, 140), (360, 160), (330, 100), (380, 120), (300, 95)]:
    b += '<rect x="%d" y="%d" width="13" height="13" fill="%s" stroke="%s" stroke-width="1.4"/>' % (cx - 6, cy - 6, REV_SOFT, REV)
b += txt(196, 252, "출력 0 (경계 아래)", 12, FWD, weight=600)
b += txt(345, 78, "출력 1 (경계 위)", 12, REV, weight=600)
b += '<line x1="281" y1="148" x2="330" y2="192" stroke="%s" stroke-width="2.2" marker-start="url(#a4)"/>' % REV
b += txt(322, 214, "w 는 경계의 법선", 11.5, REV)
b += txt(600, 70, "이것이 할 수 있는 전부다", 13, INK, weight=600)
b += txt(600, 100, "· 평면을 직선 하나로 가른다", 12, INK2)
b += txt(600, 124, "· 입력이 n 개면 n 차원의", 12, INK2)
b += txt(600, 146, "  평평한 칸막이 하나", 12, INK2)
b += txt(600, 176, "· 굽은 경계는 만들 수 없다", 12, NO, weight=600)
b += txt(600, 206, "그래서 \"직선으로 갈리는 문제\"만", 11.8, INK2)
b += txt(600, 226, "풀 수 있다. 다음 그림이 그 경계다.", 11.8, INK2)
svg("fig04_decision_boundary", 760, 268, b,
    "퍼셉트론의 결정 경계는 직선 하나이고 가중치 벡터가 그 직선의 법선이다")

# ── 5. 학습 규칙 ───────────────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("a5", REV), arrow("a6", OK))
b += txt(380, 26, "학습 규칙 — 틀린 예가 있으면 그쪽으로 경계를 민다", 13.5, INK, weight=600)
for ox, title in [(30, "틀렸을 때"), (400, "고친 뒤")]:
    b += '<line x1="%d" y1="215" x2="%d" y2="215" stroke="%s" stroke-width="1"/>' % (ox + 30, ox + 300, INK)
    b += '<line x1="%d" y1="60" x2="%d" y2="228" stroke="%s" stroke-width="1"/>' % (ox + 50, ox + 50, INK)
    b += txt(ox + 165, 50, title, 13, INK, weight=600)
b += '<line x1="70" y1="200" x2="300" y2="80" stroke="%s" stroke-width="2.2"/>' % INK
b += '<circle cx="235" cy="170" r="8" fill="%s" stroke="%s" stroke-width="2"/>' % (REV_SOFT, NO)
b += txt(235, 195, "정답 1 인데 0 이라 함", 11.5, NO)
b += '<line x1="440" y1="212" x2="670" y2="74" stroke="%s" stroke-width="2.2"/>' % INK
b += '<line x1="440" y1="200" x2="670" y2="80" stroke="%s" stroke-width="1.4" stroke-dasharray="4 3" opacity="0.6"/>' % MUTED
b += '<circle cx="605" cy="170" r="8" fill="%s" stroke="%s" stroke-width="2"/>' % (REV_SOFT, OK)
b += txt(605, 195, "이제 맞는 쪽에 있다", 11.5, OK)
b += '<path d="M330,140 C360,140 370,140 395,140" fill="none" stroke="%s" stroke-width="2" marker-end="url(#a6)"/>' % OK
b += txt(363, 128, "갱신", 11.5, OK, weight=600)
b += txt(248, 254, "w ← w + η (y − ŷ) x", 14, INK, weight=600)
b += '<line x1="380" y1="238" x2="380" y2="262" stroke="%s" stroke-width="1"/>' % LINE
b += txt(512, 254, "θ ← θ − η (y − ŷ)", 14, INK, weight=600)
b += txt(380, 278, "맞히면 y − ŷ = 0 이라 아무것도 하지 않는다. 틀렸을 때만 그 입력 x 의 방향으로 w 를 옮긴다.", 11.8, INK2)
svg("fig05_learning_rule", 760, 292, b,
    "맞히면 그대로 두고 틀린 예가 나올 때만 그 입력 방향으로 가중치를 옮긴다")

# ── 6. AND · OR 는 갈리고 XOR 는 안 갈린다 (핵심) ──────────────────────────
b = txt(380, 26, "핵심 한계 — 직선 하나로 갈리지 않는 문제가 있다", 14, INK, weight=600)


def panel(ox, title, pts, line, ok):
    """pts: [(x,y,cls)] with x,y in {0,1}; line: (x1,y1,x2,y2) in 축 좌표 또는 None"""
    s = ""
    X = lambda v: ox + 40 + v * 110
    Y = lambda v: 200 - v * 110
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>' % (ox + 22, 200, ox + 190, 200, INK)
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>' % (ox + 40, 72, ox + 40, 216, INK)
    s += txt(ox + 106, 56, title, 13, OK if ok else NO, weight=600)
    if line:
        s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2.4"/>' % (
            line[0], line[1], line[2], line[3], OK)
    for px, py, cl in pts:
        if cl:
            s += ('<rect x="%d" y="%d" width="15" height="15" fill="%s" stroke="%s" stroke-width="1.8"/>'
                  % (X(px) - 7, Y(py) - 7, REV_SOFT, REV))
        else:
            s += '<circle cx="%d" cy="%d" r="8" fill="%s" stroke="%s" stroke-width="1.8"/>' % (X(px), Y(py), FWD_SOFT, FWD)
    s += txt(ox + 36, 216, "0", 11, MUTED) + txt(ox + 150, 216, "1", 11, MUTED) + txt(ox + 28, 96, "1", 11, MUTED)
    return s


AND = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)]
OR = [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1)]
XOR = [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)]
b += panel(20, "AND — 갈린다", AND, (95, 90, 200, 208), True)
b += panel(275, "OR — 갈린다", OR, (296, 136, 376, 216), True)
b += panel(530, "XOR — 갈리지 않는다", XOR, None, False)
b += ('<line x1="600" y1="180" x2="700" y2="90" stroke="%s" stroke-width="2" stroke-dasharray="5 4" opacity="0.8"/>' % NO)
b += ('<line x1="600" y1="100" x2="700" y2="190" stroke="%s" stroke-width="2" stroke-dasharray="5 4" opacity="0.8"/>' % NO)
b += txt(650, 236, "어느 직선을 그어도", 11.5, NO, weight=600)
b += txt(650, 252, "네모 둘이 같은 쪽에 안 온다", 11.5, NO)
b += txt(146, 244, "원 = 출력 0", 11.5, FWD)
b += txt(146, 260, "네모 = 출력 1", 11.5, REV)
b += txt(380, 284, "XOR 는 같은 값이면 0, 다르면 1 이다. 1 인 두 점이 대각선으로 마주 보고 있어 직선 하나로는 떼어 낼 수 없다.",
          12, INK2)
svg("fig06_and_or_xor", 760, 298, b,
    "AND 와 OR 는 직선 하나로 갈리지만 XOR 는 1 인 두 점이 대각선으로 마주 보아 직선 하나로 갈리지 않는다")

# ── 7. 한계를 넘은 자리 ────────────────────────────────────────────────────
b = '<defs>%s%s</defs>' % (arrow("a7", INK), arrow("a8", REV))
b += txt(380, 26, "층을 하나 더 쌓으면 풀린다. 그런데 안쪽 가중치를 무엇으로 고치나", 13.5, INK, weight=600)
b += box(40, 70, 300, 150, NODE, LINE, 1.2)
b += txt(190, 96, "한 층 (1958)", 13, INK, weight=600)
b += '<circle cx="100" cy="140" r="14" fill="%s" stroke="%s" stroke-width="1.2"/>' % (FWD_SOFT, FWD)
b += '<circle cx="100" cy="185" r="14" fill="%s" stroke="%s" stroke-width="1.2"/>' % (FWD_SOFT, FWD)
b += '<circle cx="250" cy="162" r="18" fill="%s" stroke="%s" stroke-width="1.6"/>' % (REV_SOFT, REV)
for y0 in [140, 185]:
    b += '<line x1="114" y1="%d" x2="230" y2="162" stroke="%s" stroke-width="2" marker-end="url(#a8)"/>' % (y0, REV)
b += txt(190, 206, "직선 하나 · XOR 못 푼다", 11.5, NO, weight=600)
b += box(420, 70, 300, 150, NODE, LINE, 1.2)
b += txt(570, 96, "두 층 (1986)", 13, INK, weight=600)
b += '<circle cx="460" cy="140" r="13" fill="%s" stroke="%s" stroke-width="1.2"/>' % (FWD_SOFT, FWD)
b += '<circle cx="460" cy="185" r="13" fill="%s" stroke="%s" stroke-width="1.2"/>' % (FWD_SOFT, FWD)
for y1 in [130, 165, 200]:
    b += '<circle cx="570" cy="%d" r="13" fill="%s" stroke="%s" stroke-width="1.2"/>' % (y1, NODE, INK)
    for y0 in [140, 185]:
        b += '<line x1="473" y1="%d" x2="556" y2="%d" stroke="%s" stroke-width="1.6"/>' % (y0, y1, MUTED)
    b += '<line x1="583" y1="%d" x2="668" y2="165" stroke="%s" stroke-width="1.8" marker-end="url(#a8)"/>' % (y1, REV)
b += '<circle cx="682" cy="165" r="16" fill="%s" stroke="%s" stroke-width="1.6"/>' % (REV_SOFT, REV)
b += txt(570, 116, "은닉층", 11.5, INK2)
b += txt(570, 234, "굽은 경계 · XOR 풀린다", 11.5, OK, weight=600)
b += txt(515, 256, "그런데 은닉층의 가중치는 정답이 없다", 12, NO, weight=600)
b += txt(190, 256, "정답이 바로 옆에 있어 규칙이 성립", 12, INK2)
b += txt(380, 290, "이 빈칸을 채운 것이 1986년 역전파다. 오차를 연쇄 법칙으로 뒤로 보내 층마다 몫을 나눈다.",
          12.5, INK, weight=600)
b += txt(380, 312, "그러려면 활성 함수의 기울기가 0이 아니어야 한다 — 그림 3이 왜 문제였는지가 여기서 이어진다.", 11.8, INK2)
svg("fig07_next_paper", 760, 326, b,
    "한 층은 직선 하나만 긋고 두 층은 굽은 경계를 만들지만 은닉층에는 정답이 없어 1958년의 규칙을 쓸 수 없다")

print("그림 일곱 개를 " + OUT + " 에 만들었다")
