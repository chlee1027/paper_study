# -*- coding: utf-8 -*-
"""사전학습 노트(Erhan 외, AISTATS 2010)의 그림 열둘을 만든다.

색과 글꼴은 DBN · Wide ResNet 노트의 그림과 맞췄다 — 저장소의 노트들이 한 벌로
읽히게 하려는 것이다. 그림을 고치려면 이 파일을 고쳐 다시 돌린다.
바깥 데이터를 읽지 않으므로 어디서나 돈다.

  python make_figures.py

논문은 수치를 본문에 적지 않고 그림으로만 낸다. 아래 READ_* 상수가 원 그림을 키워
픽셀로 눈금을 읽은 값이고, 노트의 표와 같은 값이다. 읽는 방법과 읽기 오차는 노트 6절에 있다.
차이 · 비 · 파라미터 수는 이 파일이 직접 계산하고 돌릴 때 화면에도 찍는다.
"""
import io, os, math

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"
NODE      = "#F6F7F5"
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 사전학습 없음 쪽
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 사전학습 쪽
REV_SOFT  = "#F2DED2"
OK        = "#1E8449"
NO        = "#C0392B"
PURPLE    = "#7D4E9C"
FONT = "IBM Plex Sans KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"

# ── 원 그림에서 읽은 값 ────────────────────────────────────────────────────
# 그림 1: MNIST 시험 오차(%) — 은닉 유닛 25 · 50 · 100 · 200 · 400 · 800. 읽기 오차 ±0.1
UNITS = [25, 50, 100, 200, 400, 800]
READ_F1 = {
    1: {"none": [3.61, 2.68, 2.03, 1.92, 1.90, 1.80], "RBM": [6.28, 4.40, 3.10, 1.97, 1.54, 1.31],
        "DAE": [5.73, 4.38, 2.74, 2.10, 1.65, 1.42]},
    2: {"none": [3.84, 2.68, 2.12, 1.75, 1.70, 1.74], "RBM": [6.20, 4.00, 2.29, 1.62, 1.38, 1.26],
        "DAE": [5.47, 4.09, 2.47, 1.66, 1.51, 1.38]},
    3: {"none": [4.25, 3.16, 2.38, 1.88, 1.70, 1.85], "RBM": [5.85, 3.80, 2.20, 1.62, 1.42, 1.33],
        "DAE": [5.24, 3.86, 2.12, 1.63, 1.41, 1.33]},
}
# 그림 2 위: 아래 k 층만 RBM 사전학습, 3 층 망, MNIST. 마지막 에폭의 (학습 NLL, 시험 NLL)
READ_F2T = [(0, 4.9e-5, 0.123), (1, 1.0e-4, 0.081), (2, 5.7e-4, 0.064), (3, 1.8e-3, 0.047)]
# 그림 2 아래: 맨 위 층 20 유닛, 3 층 망. 사전학습은 잡음 제거 오토인코더
READ_F2B = [("사전학습 없음", 3.0e-5, 0.103), ("DAE 사전학습", 8.5e-5, 0.084)]
# 그림 3: InfiniteMNIST 온라인 오차(%). 창 4.5–5.5 · 6.5–7.5 · 8.5–9.5 · 9.5–9.9 (백만) 의 기하평균
WIN = [5.0, 7.0, 9.0, 9.7]
READ_F3 = {
    "3층 · 없음":  [0.41, 0.28, 0.20, 0.17],
    "1층 · 없음":  [0.33, 0.18, 0.11, 0.096],
    "RBM 1·3층":  [0.27, 0.11, 0.047, 0.032],
    "DAE 1층":    [0.34, 0.13, 0.055, 0.040],
    "DAE 3층":    [0.11, 0.032, 0.0093, 0.0062],
}
# 그림 7: InfiniteMNIST 3 층 망, 아래 k 층만 DAE 사전학습. 같은 창
READ_F7 = {0: [0.49, 0.35, 0.25, 0.24], 1: [0.68, 0.37, 0.24, 0.18],
           2: [0.32, 0.17, 0.099, 0.060], 3: [0.097, 0.027, 0.0080, 0.0051]}
# 그림 4: 바꾼 구간의 시작 위치(전체 1 천만 중 비율)와 출력 분산(세로축 이름 그대로). 읽기 오차 ±0.05
F4X = [0.0, 0.1, 0.25, 0.3, 0.4, 0.5, 0.6, 0.75, 0.8, 0.9]
READ_F4 = {"none": [7.60, 3.88, 3.08, 3.10, 2.82, 2.66, 2.68, 2.45, 2.28, 3.32],
           "RBM":  [6.30, 4.20, 2.48, 1.68, 1.15, 0.93, 0.84, 0.76, 0.77, 1.36]}
# 그림 5: 학습 집합 오차(%) — 처음 0.75 천만 구간에 점들이 놓인 띠와 맨 끝 점
READ_F5 = {"none": (0.18, 0.23, 0.125), "RBM": (0.10, 0.135, 0.040)}
# 내 DBN 실험(2026-09-20) E 칸: 은닉 256 x 2 층, 라벨 수, 사전학습 오차(seed 5 중앙값), 무작위 오차
MY_DBN = [(100, 0.2410, 0.7560), (1000, 0.0880, 0.1290), (10000, 0.0370, 0.0565)]


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
    a = '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"' % (
        x1, y1, x2, y2, color or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if marker:
        a += ' marker-end="url(#%s)"' % marker
    if op:
        a += ' opacity="%s"' % op
    return a + "/>"


def circ(cx, cy, r, fill=None, stroke=None, sw=1.2):
    return '<circle cx="%.1f" cy="%.1f" r="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (
        cx, cy, r, fill or NODE, stroke or INK, sw)


def polyline(pts, stroke, sw=2, dash=None):
    a = '<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"' % (
        " ".join("%.1f,%.1f" % p for p in pts), stroke, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    return a + "/>"


class Axes:
    """눈금 있는 판 하나. 가로 · 세로 모두 선형 또는 로그."""

    def __init__(self, x0, y0, w, h, xr, yr, xlog=False, ylog=False):
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.xr, self.yr, self.xlog, self.ylog = xr, yr, xlog, ylog

    def _t(self, v, r, log):
        if log:
            return (math.log10(v) - math.log10(r[0])) / (math.log10(r[1]) - math.log10(r[0]))
        return (v - r[0]) / (r[1] - r[0])

    def X(self, v):
        return self.x0 + self._t(v, self.xr, self.xlog) * self.w

    def Y(self, v):
        return self.y0 + self.h - self._t(v, self.yr, self.ylog) * self.h

    def frame(self, xticks, yticks, xlabel="", ylabel="", xfmt=str, yfmt=str):
        b = box(self.x0, self.y0, self.w, self.h, "#FFFFFF", LINE, 1, 2)
        for v in xticks:
            x = self.X(v)
            b += line(x, self.y0, x, self.y0 + self.h, LINE, 0.8, "2,3")
            b += txt(x, self.y0 + self.h + 15, xfmt(v), 10.5, MUTED)
        for v in yticks:
            y = self.Y(v)
            b += line(self.x0, y, self.x0 + self.w, y, LINE, 0.8, "2,3")
            b += txt(self.x0 - 6, y + 4, yfmt(v), 10.5, MUTED, anchor="end")
        if xlabel:
            b += txt(self.x0 + self.w / 2, self.y0 + self.h + 33, xlabel, 11, INK2)
        if ylabel:
            b += ('<text x="%s" y="%s" font-size="11" fill="%s" text-anchor="middle" '
                  'transform="rotate(-90 %s %s)">%s</text>' % (
                      self.x0 - 44, self.y0 + self.h / 2, INK2, self.x0 - 44, self.y0 + self.h / 2, ylabel))
        return b

    def series(self, xs, ys, color, sw=2.0, dash=None, r=3.2, fill=None):
        pts = [(self.X(x), self.Y(y)) for x, y in zip(xs, ys)]
        b = polyline(pts, color, sw, dash)
        for p in pts:
            b += circ(p[0], p[1], r, fill or color, color, 1)
        return b


def pct(v):
    return ("%g" % v)


def sci(v):
    e = int(round(math.log10(v)))
    return "1e%d" % e


def legend(x, y, items, size=11):
    b = ""
    for i, (label, color, dash) in enumerate(items):
        yy = y + i * 18
        b += line(x, yy - 4, x + 22, yy - 4, color, 2.2, dash)
        b += txt(x + 28, yy, label, size, INK2, anchor="start")
    return b


print("그림을 만든다 ->", OUT)

# ── 그림 1. 두 가설과 각 가설의 예측 ─────────────────────────────────────────
b = txt(410, 30, "사전학습이 돕는 까닭 — 논문이 맞세우는 두 설명", 14, INK, weight=600)
cols = [(40, FWD, FWD_SOFT, "최적화 가설", "Bengio 외 2007", "학습 기준을 더 잘 내리게 해 준다"),
        (430, REV, REV_SOFT, "정규화 가설", "Erhan 외 2009b", "갈 수 있는 매개변수 구역을 좁힌다")]
for x, c, soft, name, src, one in cols:
    b += box(x, 48, 350, 74, soft, c, 1.3, 8)
    b += txt(x + 175, 72, name, 13.5, c, weight=600)
    b += txt(x + 175, 92, src, 11, MUTED)
    b += txt(x + 175, 111, one, 11.5, INK2)
rows = [("사전학습한 망의 학습 오차", "더 낮다", "더 높다 (시험 오차는 낮다)"),
        ("층을 아주 작게 만들면", "그래도 돕는다", "오히려 해롭다"),
        ("데이터가 끝없이 늘면", "남는다", "흔한 정규화라면 사라진다")]
for i, (q, a1, a2) in enumerate(rows):
    y = 150 + i * 46
    b += txt(410, y, q, 11.5, INK, weight=600)
    b += box(40, y + 8, 350, 26, "#FFFFFF", LINE, 1, 5)
    b += txt(215, y + 26, a1, 11.5, FWD)
    b += box(430, y + 8, 350, 26, "#FFFFFF", LINE, 1, 5)
    b += txt(605, y + 26, a2, 11.5, REV)
b += box(40, 296, 740, 56, "#FFFFFF", INK, 1.2, 8)
b += txt(410, 318, "MNIST (논문 5절) 는 위 두 줄에서 정규화 쪽 예측과 맞는다.", 11.5, INK2)
b += txt(410, 340, "InfiniteMNIST (논문 6절) 에서는 셋째 줄이 「남는다」로 나와, 논문은 둘을 엮는 설명(논문 7절)으로 간다.", 11.5, INK, weight=600)
svg("fig01_two_hypotheses", 820, 368, b,
    "최적화 가설과 정규화 가설, 그리고 세 물음에 대한 각 가설의 예측")

# ── 그림 2. 식 (2) 의 구역 사전분포 ─────────────────────────────────────────
vol = [1.0, 2.0, 1.0, 3.0, 1.0]
pi_ = [0.05, 0.10, 0.70, 0.05, 0.10]
r_ = [0.30, 0.25, 0.05, 0.30, 0.10]
b = txt(410, 28, "식 (2) · (3) — 매개변수 공간을 끌림 구역으로 나누고, 구역마다 밀도를 고르게 둔다", 13, INK, weight=600)
X0, W = 70, 680
tot = sum(vol)
xs = [X0]
for v in vol:
    xs.append(xs[-1] + v / tot * W)
maxd = max(max(p / v for p, v in zip(pi_, vol)), max(q / v for q, v in zip(r_, vol)))
for row, (probs, color, name, y0) in enumerate([(pi_, REV, "사전학습  π(k) / v(k)", 70),
                                                 (r_, FWD, "무작위 초기화  r(k) / v(k)", 220)]):
    b += txt(X0, y0 - 8, name, 12, color, anchor="start", weight=600)
    base = y0 + 110
    b += line(X0, base, X0 + W, base, INK2, 1.2)
    for k in range(5):
        d = probs[k] / vol[k]
        hgt = d / maxd * 100
        b += box(xs[k] + 2, base - hgt, xs[k + 1] - xs[k] - 4, hgt, REV_SOFT if row == 0 else FWD_SOFT, color, 1.2, 2)
        b += txt((xs[k] + xs[k + 1]) / 2, base - hgt - 6, "%.3g" % d, 10.5, color)
        b += txt((xs[k] + xs[k + 1]) / 2, base + 15, "R%d (v=%g, %s=%g)" % (k + 1, vol[k], "π" if row == 0 else "r", probs[k]), 10, MUTED)
        if k:
            b += line(xs[k], y0, xs[k], base + 4, LINE, 1, "3,3")
b += txt(410, 375, "작은 예시: R3 는 부피 1 에 확률 0.70 이라 밀도 0.70, R4 는 부피 3 에 확률 0.05 라 밀도 0.0167 — 42 배 차이다.", 11.5, INK2)
b += txt(410, 395, "정규화 항은 −log P(θ) 이므로 확률 0 인 구역 바깥은 벌점이 무한대다. 「무한 벌점」 이라는 말이 이 뜻이다.", 11.5, INK2)
b += txt(410, 415, "숫자는 내가 고른 예시다 — 논문은 π(k) 와 r(k) 의 값을 하나도 재지 않는다.", 11, NO)
svg("fig02_basins", 820, 430, b, "식 2와 3의 구역별 균일 사전분포를 다섯 구역 예시로 그린 것")

# ── 그림 3. 실험 설정과 갱신 예산 ───────────────────────────────────────────
b = txt(410, 28, "InfiniteMNIST 의 갱신 예산 — 모두 1 천만 번인데 지도 학습 몫이 다르다", 13.5, INK, weight=600)
A = Axes(170, 60, 600, 0, (0, 10), (0, 1))
for i, (name, parts) in enumerate([("사전학습 없음", [(0, 10, FWD_SOFT, FWD, "지도 1 천만")]),
                                    ("사전학습 있음", [(0, 2.5, REV_SOFT, REV, "비지도 250 만"),
                                                       (2.5, 10, FWD_SOFT, FWD, "지도 750 만")])]):
    y = 66 + i * 50
    b += txt(160, y + 22, name, 12, INK, anchor="end", weight=600)
    for a0, a1, f, s, lab in parts:
        b += box(A.X(a0), y, A.X(a1) - A.X(a0), 34, f, s, 1.2, 3)
        b += txt((A.X(a0) + A.X(a1)) / 2, y + 22, lab, 11.5, s, weight=600)
for v in range(0, 11):
    b += txt(A.X(v), 166, "%d" % v, 10.5, MUTED)
b += txt(470, 184, "본 예시 수 (백만) — 그림 3 · 7 의 가로축이 이 눈금이다. 사전학습 곡선은 250 만에서 시작한다", 11, INK2)
b += box(40, 202, 740, 130, "#FFFFFF", LINE, 1, 8)
p1 = 784 * 2500 + 2500 * 10 + 2500 + 10
p3 = {u: 784 * u + 2 * u * u + u * 10 + 3 * u + 10 for u in (800, 1000, 1200)}
b += txt(60, 226, "망의 크기 (논문 4 · 6.1절). 가중치와 치우침을 내가 센 값:", 11.5, INK, anchor="start", weight=600)
b += txt(60, 250, "1 층 망 — 은닉 2500: %s 개" % format(p1, ","), 11.5, INK2, anchor="start")
b += txt(60, 272, "3 층 망 — 층마다 800 · 1000 · 1200: %s · %s · %s 개" % tuple(format(p3[u], ",") for u in (800, 1000, 1200)), 11.5, INK2, anchor="start")
b += txt(60, 294, "3 층 / 1 층 = %.2f ~ %.2f 배 — 「깊은 망이 더 크다」도 「같은 크기다」도 아니고, 층 폭에 따라 1 배를 사이에 둔다" % (p3[800] / p1, p3[1200] / p1), 11.5, INK, anchor="start")
b += txt(60, 318, "비지도 250 만 번이 층 셋에 어떻게 나뉘는지는 본문에 적혀 있지 않다", 11, NO, anchor="start")
svg("fig03_budget", 820, 346, b, "사전학습 없는 망과 있는 망의 갱신 예산 비교, 그리고 망 크기를 센 값")
print("    파라미터 1층 %d, 3층 %s, 비 %.3f ~ %.3f" % (p1, p3, p3[800] / p1, p3[1200] / p1))

# ── 그림 4. 층 크기 (원 그림 1) ────────────────────────────────────────────
b = txt(410, 26, "원 그림 1 을 다시 그림 — MNIST 시험 오차(%) 대 층마다의 은닉 유닛 수", 13.5, INK, weight=600)
cross = {1: "200 ~ 400", 2: "100 ~ 200", 3: "50 ~ 100"}
for p in (1, 2, 3):
    A = Axes(64 + (p - 1) * 252, 52, 210, 230, (20, 1000), (1, 7), xlog=True)
    b += A.frame([25, 100, 400], [1, 2, 3, 4, 5, 6, 7], "유닛 수" if p == 2 else "",
                 "시험 오차 (%)" if p == 1 else "")
    b += txt(A.x0 + A.w / 2, 46, "%d 층" % p, 12.5, INK, weight=600)
    b += A.series(UNITS, READ_F1[p]["none"], INK2, 2.0)
    b += A.series(UNITS, READ_F1[p]["RBM"], FWD, 1.8, "5,3")
    b += A.series(UNITS, READ_F1[p]["DAE"], REV, 1.8)
    b += txt(A.x0 + A.w / 2, 350, "역전되는 자리: %s" % cross[p], 11.5, REV, weight=600)
b += legend(80, 380, [("사전학습 없음", INK2, None), ("RBM (DBN)", FWD, "5,3"), ("잡음 제거 오토인코더", REV, None)])
b += txt(470, 386, "유닛이 작으면 사전학습이 해롭고(25 유닛에서 +1.0 ~ +2.7 %p),", 11.5, INK2)
b += txt(470, 404, "깊을수록 사전학습이 이기기 시작하는 크기가 작아진다.", 11.5, INK, weight=600)
b += txt(470, 424, "값은 원 그림을 키워 읽은 것이다(읽기 오차 ±0.1). 오차 막대는 다시 그리지 않았다.", 10.5, MUTED)
svg("fig04_layer_size", 820, 442, b, "층 수별로 은닉 유닛 수에 따른 시험 오차. 사전학습이 이기기 시작하는 크기가 깊이에 따라 작아진다")

# ── 그림 5. 아래 k 층만 사전학습 (원 그림 2 위) ─────────────────────────────
b = txt(410, 26, "원 그림 2 위 — 아래 k 층만 RBM 으로 사전학습한 3 층 망의 마지막 에폭 (MNIST)", 13.5, INK, weight=600)
A = Axes(90, 50, 400, 290, (1e-5, 1e-2), (0.03, 0.2), xlog=True, ylog=True)
b += A.frame([1e-5, 1e-4, 1e-3, 1e-2], [0.04, 0.06, 0.08, 0.1, 0.15, 0.2], "학습 NLL (로그 눈금)", "시험 NLL (로그 눈금)", sci, pct)
colk = [INK2, FWD, REV, PURPLE]
prev = None
for (k, tr, te), c in zip(READ_F2T, colk):
    x, y = A.X(tr), A.Y(te)
    if prev:
        b += line(prev[0], prev[1], x, y, MUTED, 1, "3,3")
    b += circ(x, y, 6, c, c)
    b += txt(x + 10, y - 8, "k=%d" % k, 11.5, c, anchor="start", weight=600)
    prev = (x, y)
b += box(520, 50, 270, 290, "#FFFFFF", LINE, 1, 8)
b += txt(655, 74, "층을 하나 더 사전학습할 때", 12, INK, weight=600)
b += txt(655, 92, "시험 NLL 이 줄어드는 몫", 12, INK, weight=600)
for i in range(1, 4):
    a0, a1 = READ_F2T[i - 1][2], READ_F2T[i][2]
    y = 124 + (i - 1) * 46
    b += txt(540, y, "k = %d → %d" % (i - 1, i), 11.5, colk[i], anchor="start", weight=600)
    b += txt(540, y + 20, "%.3f → %.3f  (차 %.3f, 비 %.2f)" % (a0, a1, a0 - a1, a0 / a1), 11, INK2, anchor="start")
b += txt(655, 280, "첫 층의 몫이 가장 크다.", 11.5, REV, weight=600)
b += txt(655, 300, "본문은 「첫 층에서는 아니다」라고 적는다", 11, NO)
b += txt(655, 320, "(논문 5절)", 11, MUTED)
b += txt(410, 398, "학습 NLL 은 k 를 따라 4.9e-5 → 1.8e-3 으로 37 배 올라가고 시험 NLL 은 내려간다 — 정규화 쪽 예측과 맞는다", 11, INK2)
svg("fig05_selective_mnist", 820, 414, b, "아래 k 층만 사전학습했을 때 마지막 에폭의 학습 NLL과 시험 NLL")
for i in range(1, 4):
    print("    그림2위 k=%d: 차 %.3f 비 %.2f" % (i, READ_F2T[i - 1][2] - READ_F2T[i][2], READ_F2T[i - 1][2] / READ_F2T[i][2]))

# ── 그림 6. 맨 위 층 20 유닛 (원 그림 2 아래) ───────────────────────────────
b = txt(410, 26, "원 그림 2 아래 — 맨 위 층을 20 유닛으로 묶고 조기 종료 없이 끝까지 (MNIST)", 13.5, INK, weight=600)
A = Axes(90, 50, 380, 250, (1e-5, 1e-3), (0.06, 0.15), xlog=True, ylog=True)
b += A.frame([1e-5, 1e-4, 1e-3], [0.06, 0.08, 0.1, 0.12, 0.15], "학습 NLL", "시험 NLL", sci, pct)
for (name, tr, te), c in zip(READ_F2B, [INK2, REV]):
    b += circ(A.X(tr), A.Y(te), 7, c, c)
    b += txt(A.X(tr) + 12, A.Y(te) + 4, "%s (%.1e, %.3f)" % (name, tr, te), 11, c, anchor="start", weight=600)
b += box(500, 50, 290, 250, "#FFFFFF", LINE, 1, 8)
b += txt(645, 76, "읽는 법", 12.5, INK, weight=600)
lines6 = ["사전학습 쪽 학습 NLL 이 %.1f 배 높고" % (READ_F2B[1][1] / READ_F2B[0][1]),
          "시험 NLL 은 %.2f 배다." % (READ_F2B[1][2] / READ_F2B[0][2]),
          "Bengio 외(2007)의 「최적화」 결론을",
          "조기 종료를 빼고 다시 잰 것이다.",
          "",
          "각주 1 은 이 판과 위 판(k=3)을",
          "맞대어 「20 유닛이 학습 오차를",
          "낮춘다」고 적는데, 위 판은 RBM,",
          "이 판은 DAE 다 — 두 가지가 함께 바뀐다."]
for i, t in enumerate(lines6):
    b += txt(516, 104 + i * 21, t, 11.5, NO if i >= 7 else INK2, anchor="start")
svg("fig06_top20", 820, 352, b, "맨 위 층을 20 유닛으로 묶었을 때 사전학습 유무에 따른 학습 NLL과 시험 NLL")

# ── 그림 7. 온라인 오차 (원 그림 3) ─────────────────────────────────────────
b = txt(410, 26, "원 그림 3 — InfiniteMNIST 온라인 분류 오차(%), 구간마다 곡선을 기하평균한 값", 13.5, INK, weight=600)
A = Axes(90, 50, 430, 300, (4, 10), (0.004, 0.6), ylog=True)
b += A.frame([4, 5, 6, 7, 8, 9, 10], [0.01, 0.03, 0.1, 0.3], "본 예시 수 (백만)", "온라인 오차 (%, 로그 눈금)", str, pct)
sty = {"3층 · 없음": (INK, None), "1층 · 없음": (INK2, "6,3"), "RBM 1·3층": (FWD, None),
       "DAE 1층": (REV, "6,3"), "DAE 3층": (REV, None)}
for k, v in READ_F3.items():
    b += A.series(WIN, v, sty[k][0], 2.0, sty[k][1])
b += legend(548, 64, [(k, sty[k][0], sty[k][1]) for k in READ_F3])
b += box(540, 168, 250, 182, "#FFFFFF", LINE, 1, 8)
notes7 = ["RBM 1 층과 3 층은 원 그림에서", "서로 겹쳐 한 줄로 그렸다.", "",
          "깊이가 값을 내는 것은 DAE 뿐이다:", "8.5~9.5 백만에서 DAE 3 층 0.0093,",
          "RBM 3 층 0.047 — 5 배.", "", "곡선 하나가 실행 하나다. seed 를", "바꾼 흩어짐은 그려져 있지 않다."]
for i, t in enumerate(notes7):
    b += txt(554, 190 + i * 18, t, 11, INK2, anchor="start")
svg("fig07_online", 820, 392, b, "InfiniteMNIST에서 다섯 망의 온라인 분류 오차를 구간별로 다시 그린 것")

# ── 그림 8. 차이로 보는가, 비로 보는가 ──────────────────────────────────────
b = txt(410, 26, "「사전학습의 이득이 사라지지 않는다」 — 무엇으로 재느냐에 따라 답이 갈린다", 13.5, INK, weight=600)
none3, dae3 = READ_F3["3층 · 없음"], READ_F3["DAE 3층"]
diff = [a - c for a, c in zip(none3, dae3)]
ratio = [a / c for a, c in zip(none3, dae3)]
A = Axes(80, 66, 300, 180, (4.5, 10), (0, 0.35))
b += txt(230, 54, "이 논문 · 3 층 망: 차이 (%p)", 12, INK, weight=600)
b += A.frame([5, 7, 9], [0, 0.1, 0.2, 0.3], "본 예시 수 (백만)", "", str, pct)
b += A.series(WIN, diff, REV, 2.2)
for x, v in zip(WIN, diff):
    b += txt(A.X(x), A.Y(v) - 9, "%.2f" % v, 10.5, REV)
B = Axes(470, 66, 300, 180, (4.5, 10), (1, 40), ylog=True)
b += txt(620, 54, "이 논문 · 3 층 망: 비 (없음 / DAE)", 12, INK, weight=600)
b += B.frame([5, 7, 9], [1, 3, 10, 30], "본 예시 수 (백만)", "", str, pct)
b += B.series(WIN, ratio, FWD, 2.2)
for x, v in zip(WIN, ratio):
    b += txt(B.X(x), B.Y(v) - 9, "%.1f" % v, 10.5, FWD)
labs = [100, 1000, 10000]
dd = [r - p for _, p, r in MY_DBN]
rr = [r / p for _, p, r in MY_DBN]
C = Axes(80, 316, 300, 150, (60, 16000), (0, 0.55), xlog=True)
b += txt(230, 304, "내 DBN 실험 · 2 층: 차이 (오차율)", 12, INK, weight=600)
b += C.frame(labs, [0, 0.2, 0.4], "라벨 수", "", str, pct)
b += C.series(labs, dd, REV, 2.2)
for x, v in zip(labs, dd):
    b += txt(C.X(x), C.Y(v) - 9, "%.4f" % v, 10.5, REV)
D = Axes(470, 316, 300, 150, (60, 16000), (1, 4), xlog=True)
b += txt(620, 304, "내 DBN 실험 · 2 층: 비 (무작위 / 사전학습)", 12, INK, weight=600)
b += D.frame(labs, [1, 2, 3, 4], "라벨 수", "", str, pct)
b += D.series(labs, rr, FWD, 2.2)
for x, v in zip(labs, rr):
    b += txt(D.X(x), D.Y(v) - 9, "%.2f" % v, 10.5, FWD)
b += txt(410, 548, "왼쪽 줄: 차이는 데이터가 늘수록 줄어든다.  오른쪽 줄: 비는 커지거나(논문) 1,000 장부터 1.47 ~ 1.53 배에 머문다(내 실험).", 11.5, INK)
b += txt(410, 568, "논문의 그림 3 은 세로축이 로그라 눈에 보이는 간격이 곧 비다 — 「오히려 커진다」는 비로 읽은 말이다.", 11.5, INK2)
svg("fig08_diff_vs_ratio", 820, 584, b,
    "사전학습 이득을 차이와 비로 나눠 본 것. 논문의 InfiniteMNIST 3층 망과 내 DBN 실험 모두 차이는 줄고 비는 줄지 않는다")
print("    그림3 3층 차이 %s 비 %s" % (["%.3f" % v for v in diff], ["%.1f" % v for v in ratio]))
print("    내 DBN 차이 %s 비 %s" % (["%.4f" % v for v in dd], ["%.2f" % v for v in rr]))

# ── 그림 9. 앞 예시의 영향 (원 그림 4) ──────────────────────────────────────
b = txt(410, 26, "원 그림 4 — 1 천만 개 중 백만 개 구간 하나만 바꿔 10 번 배웠을 때 출력의 흩어짐 (1 층 망)", 13.5, INK, weight=600)
A = Axes(90, 50, 470, 280, (0, 0.9), (0, 8))
b += A.frame([0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9], [0, 2, 4, 6, 8], "바꾼 구간이 시작하는 자리 (전체 중 비율)", "출력 분산 (원 그림 세로축)", pct, pct)
b += line(A.X(0.25), A.y0, A.X(0.25), A.y0 + A.h, REV, 1.2, "4,3")
b += txt(A.X(0.25) + 4, A.y0 + 14, "지도 학습 시작 (사전학습 망)", 10.5, REV, anchor="start")
b += A.series(F4X, READ_F4["none"], FWD, 2.0, "6,3")
b += A.series(F4X, READ_F4["RBM"], REV, 2.0)
b += legend(590, 64, [("사전학습 없음", FWD, "6,3"), ("RBM 사전학습", REV, None)])
b += box(580, 110, 210, 220, "#FFFFFF", LINE, 1, 8)
n9 = ["0.0 에서 0.5 로 가면", "없음 %.1f 배 · 사전학습 %.1f 배 준다" % (READ_F4["none"][0] / READ_F4["none"][5], READ_F4["RBM"][0] / READ_F4["RBM"][5]),
      "", "0.1 에서만 사전학습 쪽이 높다", "(%.2f 대 %.2f)" % (READ_F4["RBM"][1], READ_F4["none"][1]), "",
      "가로축 점이 0.2 · 0.7 이 아니라", "0.25 · 0.75 다 — 본문의 「열 구간」", "과 점 자리가 맞지 않는다"]
for i, t in enumerate(n9):
    b += txt(594, 132 + i * 20, t, 11, NO if i in (3, 4) else INK2, anchor="start")
svg("fig09_early_variance", 820, 372, b, "어느 구간의 학습 예시를 바꿨는지에 따른 출력 분산")

# ── 그림 10. 학습 집합 오차와 온라인 오차가 맞지 않는다 ────────────────────
b = txt(410, 26, "원 그림 5 와 그림 3 을 맞대기 — 같은 1 층 망이라면 두 값이 비슷해야 한다", 13.5, INK, weight=600)
A = Axes(120, 52, 400, 250, (0, 4), (0, 0.25))
b += A.frame([], [0, 0.05, 0.1, 0.15, 0.2, 0.25], "", "오차 (%)", str, pct)
bars = [("그림 5 · 앞쪽 예시", READ_F5["none"], READ_F5["RBM"]),
        ("그림 3 · 끝 온라인 오차", (READ_F3["1층 · 없음"][3],) * 2, (READ_F3["RBM 1·3층"][3],) * 2)]
for i, (lab, nn, rb) in enumerate(bars):
    for j, (rng, c, soft) in enumerate([(nn, FWD, FWD_SOFT), (rb, REV, REV_SOFT)]):
        x = A.x0 + 40 + i * 190 + j * 70
        lo, hi = rng[0], rng[1]
        mid = (lo + hi) / 2
        b += box(x, A.Y(mid), 56, A.Y(0) - A.Y(mid), soft, c, 1.2, 2)
        if hi > lo:
            b += line(x + 28, A.Y(lo), x + 28, A.Y(hi), c, 2)
        b += txt(x + 28, A.Y(hi) - 6, ("%.2f ~ %.2f" % (lo, hi)) if hi > lo else "%.3f" % lo, 10.5, c)
    b += txt(A.x0 + 103 + i * 190, A.y0 + A.h + 18, lab, 11, INK2)
b += legend(140, 340, [("사전학습 없음", FWD, None), ("RBM 사전학습", REV, None)])
b += box(550, 52, 240, 250, "#FFFFFF", LINE, 1, 8)
n10 = ["본문: 앞쪽 예시는 두 망 모두", "「사실상 시험 예시와 같다」.", "",
       "그렇다면 그림 5 의 앞쪽 값이", "그림 3 의 끝 온라인 오차와", "비슷해야 하는데",
       "없음 %.1f 배, 사전학습 %.1f 배" % ((READ_F5["none"][0] + READ_F5["none"][1]) / 2 / READ_F3["1층 · 없음"][3],
                                     (READ_F5["RBM"][0] + READ_F5["RBM"][1]) / 2 / READ_F3["RBM 1·3층"][3]),
       "높다.", "", "두 그림의 1 층 망이 같은 망인지", "본문에 적혀 있지 않다."]
for i, t in enumerate(n10):
    b += txt(566, 76 + i * 20, t, 11, NO if i in (6, 7) else INK2, anchor="start")
svg("fig10_train_vs_online", 820, 378, b, "학습 집합 오차 그림과 온라인 오차 그림의 값을 맞대 본 것")

# ── 그림 11. 선택 사전학습, 온라인 (원 그림 7) ────────────────────────────
b = txt(410, 26, "원 그림 7 — 아래 k 층만 DAE 로 사전학습한 3 층 망 (InfiniteMNIST, 온라인 오차 %)", 13.5, INK, weight=600)
A = Axes(90, 50, 400, 280, (4, 10), (0.003, 1.0), ylog=True)
b += A.frame([4, 5, 6, 7, 8, 9, 10], [0.01, 0.03, 0.1, 0.3, 1.0], "본 예시 수 (백만)", "온라인 오차 (%)", str, pct)
for k, c in zip(range(4), colk):
    b += A.series(WIN, READ_F7[k], c, 2.0)
b += legend(110, 392, [("k=%d" % k, c, None) for k, c in zip(range(2), colk[:2])])
b += legend(220, 392, [("k=%d" % k, c, None) for k, c in zip(range(2, 4), colk[2:])])
b += box(520, 50, 270, 280, "#FFFFFF", LINE, 1, 8)
b += txt(655, 74, "층을 하나 더할 때의 비 (8.5~9.5 백만)", 12, INK, weight=600)
for i in range(1, 4):
    a0, a1 = READ_F7[i - 1][2], READ_F7[i][2]
    b += txt(540, 104 + (i - 1) * 24, "k = %d → %d :  %.3g → %.3g  (비 %.1f)" % (i - 1, i, a0, a1, a0 / a1), 11, colk[i], anchor="start")
b += txt(655, 196, "MNIST (그림 2 위) 와 모양이 반대다", 12, INK, weight=600)
b += txt(540, 220, "MNIST: 첫 층 비 %.2f 이 가장 크다" % (READ_F2T[0][2] / READ_F2T[1][2]), 11, INK2, anchor="start")
b += txt(540, 240, "Infinite: 첫 층 비 %.1f, 셋째 층 %.1f" % (READ_F7[0][2] / READ_F7[1][2], READ_F7[2][2] / READ_F7[3][2]), 11, INK2, anchor="start")
b += txt(540, 268, "논문 6.5절은 「2절과 견줄 만하다」고", 11, NO, anchor="start")
b += txt(540, 286, "한 줄 적는다. 2절에는 이 실험이 없다", 11, NO, anchor="start")
b += txt(540, 312, "k=0 은 그림 3 의 「3층 · 없음」보다 1.2 배 높다", 10.5, MUTED, anchor="start")
svg("fig11_selective_online", 820, 430, b, "InfiniteMNIST에서 아래 k층만 사전학습한 3층 망의 온라인 오차")
for i in range(1, 4):
    print("    그림7 k=%d 비 %.2f" % (i, READ_F7[i - 1][2] / READ_F7[i][2]))

# ── 그림 12. 계보 ─────────────────────────────────────────────────────────
b = "<defs>%s</defs>" % arrow("a12", INK2)
b += txt(410, 28, "이 논문이 서 있는 자리와 여는 다음 자리", 14, INK, weight=600)
nodes = [(30, 60, "DBN (2006)", "층별 사전학습을 낸다", FWD),
         (30, 130, "오토인코더 (2006)", "같은 쌓기를 차원 축소에", FWD),
         (30, 200, "탐욕 층별 학습 (2007)", "최적화 가설 · 20 유닛 실험", FWD),
         (30, 270, "Erhan 외 (2009b)", "정규화 가설 · 400 초기화", REV)]
for x, y, t1, t2, c in nodes:
    b += box(x, y, 210, 52, "#FFFFFF", c, 1.3, 8)
    b += txt(x + 105, y + 22, t1, 12, c, weight=600)
    b += txt(x + 105, y + 41, t2, 10.5, INK2)
    b += line(x + 212, y + 26, 300, 196, INK2, 1.2, marker="a12")
b += box(304, 150, 220, 92, REV_SOFT, REV, 1.6, 10)
b += txt(414, 176, "이 노트 (AISTATS 2010)", 12.5, REV, weight=600)
b += txt(414, 198, "MNIST: 정규화와 맞는다", 11, INK2)
b += txt(414, 216, "온라인: 이득이 남는다", 11, INK2)
b += txt(414, 234, "→ 앞 예시가 구역을 정한다", 11, INK, weight=600)
nexts = [(580, 52, "JMLR 2010 저널판", "같은 물음의 긴 판"),
         (580, 116, "Glorot · Bengio (AISTATS 2010)", "같은 학회 · 초기화로 대신"),
         (580, 180, "Hessian-free (ICML 2010)", "「더 센 최적화」의 실제 예"),
         (580, 244, "Curriculum learning (2009)", "앞 예시의 순서를 고른다"),
         (580, 308, "Stacked DAE (JMLR 2010)", "3 층에서 DAE 가 앞선 까닭")]
for x, y, t1, t2 in nexts:
    b += box(x, y, 220, 50, "#FFFFFF", INK2, 1.1, 8, "4,3")
    b += txt(x + 110, y + 21, t1, 11.5, INK, weight=600)
    b += txt(x + 110, y + 39, t2, 10.5, INK2)
    b += line(526, 196, x - 2, y + 25, MUTED, 1.1, marker="a12")
svg("fig12_lineage", 820, 372, b, "앞선 논문 넷에서 이 논문으로, 그리고 다음에 읽을 다섯 편으로 이어지는 계보")

print("끝났다.")
