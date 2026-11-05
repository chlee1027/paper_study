# -*- coding: utf-8 -*-
"""Score SDE 노트(Song 외, ICLR 2021)의 그림 열여덟을 만든다.

표준 라이브러리만 쓴다. 원문 표의 수는 아래 상수에 옮겨 적었고(6 · 7 · 24 쪽), 원문 그림 3 · 8 · 10 · 13 의 값은
read_vector_values.py 가 PDF 벡터 좌표에서 읽어 둔 paper_vector_values.json 을 쓴다.
그림 3 · 4 는 원문 식으로 계산하고, 그림 5 는 참 점수로 궤적을 풀고, 그림 6 의 수는 toy_exact_score.py 를 돌린 값이다.

  python make_figures.py
"""
import io, json, math, os, random

OUT = os.path.dirname(os.path.abspath(__file__))
V = json.load(open(os.path.join(OUT, "paper_vector_values.json"), encoding="utf-8"))

BG, NODE, INK, INK2, MUTED, LINE = "#ECEFEC", "#F6F7F5", "#1C232C", "#4E5964", "#7A8590", "#CFD6D3"
FWD, FWD_SOFT, REV, REV_SOFT = "#2E6B8A", "#D8E7EE", "#B4552B", "#F2DED2"
CODE, CODE_SOFT, OK, OK_SOFT, NO, NO_SOFT = "#9A7B00", "#FFF3C4", "#1E8449", "#D6EEDD", "#C0392B", "#F6D9D5"
PURP, PURP_SOFT = "#8E44AD", "#EADCF0"
FONT = "IBM Plex Sans KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def defs():
    a = lambda i, c: ('<marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>' % (i, c))
    return "<defs>" + a("af", FWD) + a("ar", REV) + a("ai", INK2) + a("ao", OK) + a("ap", PURP) + "</defs>"


def svg(name, w, h, body, label):
    s = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="%s" role="img" aria-label="%s">' % (w, h, w, h, FONT, esc(label)))
    s += '<rect x="0" y="0" width="100%%" height="100%%" fill="%s"/>' % BG
    s += defs() + body + "</svg>\n"
    io.open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8").write(s)
    print("  " + name + ".svg  %dx%d" % (w, h))


def txt(x, y, t, size=12, fill=None, anchor="middle", weight=None):
    a = 'x="%.1f" y="%.1f" font-size="%s" fill="%s" text-anchor="%s"' % (x, y, size, fill or INK, anchor)
    if weight:
        a += ' font-weight="%s"' % weight
    return "<text %s>%s</text>" % (a, esc(t))


def box(x, y, w, h, fill=None, stroke=None, sw=1.2, rx=6, dash=None):
    a = 'x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s" stroke="%s" stroke-width="%s"' % (
        x, y, w, h, rx, fill or NODE, stroke or LINE, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    return "<rect %s/>" % a


def line(x1, y1, x2, y2, c=None, sw=1.2, dash=None, m=None):
    a = 'x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"' % (x1, y1, x2, y2, c or LINE, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if m:
        a += ' marker-end="url(#%s)"' % m
    return "<line %s/>" % a


def poly(pts, c, sw=1.8, dash=None, op=None):
    a = 'points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"' % (
        " ".join("%.1f,%.1f" % p for p in pts), c, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if op:
        a += ' stroke-opacity="%s"' % op
    return "<polyline %s/>" % a


def dot(x, y, c, r=4, fill=None):
    return '<circle cx="%.1f" cy="%.1f" r="%s" fill="%s" stroke="%s" stroke-width="1.2"/>' % (x, y, r, fill or c, c)


def title(w, t, sub=None):
    s = txt(w / 2, 26, t, 15, INK, weight="700")
    if sub:
        s += txt(w / 2, 46, sub, 12, INK2)
    return s


class Axes:
    """선형 또는 로그 축 하나."""

    def __init__(self, x, y, w, h, xr, yr, xlog=False, ylog=False):
        self.x, self.y, self.w, self.h, self.xr, self.yr, self.xlog, self.ylog = x, y, w, h, xr, yr, xlog, ylog

    def X(self, v):
        a, b = self.xr
        f = (math.log10(v) - math.log10(a)) / (math.log10(b) - math.log10(a)) if self.xlog else (v - a) / (b - a)
        return self.x + f * self.w

    def Y(self, v):
        a, b = self.yr
        f = (math.log10(v) - math.log10(a)) / (math.log10(b) - math.log10(a)) if self.ylog else (v - a) / (b - a)
        return self.y + self.h - f * self.h

    def frame(self, xt, yt, xl=None, yl=None, xf=None, yf=None):
        s = box(self.x, self.y, self.w, self.h, "#FFFFFF", LINE, 1, 0)
        for t in xt:
            s += line(self.X(t), self.y, self.X(t), self.y + self.h, "#E6EAE8", 1)
            s += txt(self.X(t), self.y + self.h + 16, (xf(t) if xf else t), 11, INK2)
        for t in yt:
            s += line(self.x, self.Y(t), self.x + self.w, self.Y(t), "#E6EAE8", 1)
            s += txt(self.x - 7, self.Y(t) + 4, (yf(t) if yf else t), 11, INK2, "end")
        if xl:
            s += txt(self.x + self.w / 2, self.y + self.h + 34, xl, 12, INK2)
        if yl:
            cx, cy = self.x - 46, self.y + self.h / 2
            s += '<text x="%.1f" y="%.1f" font-size="12" fill="%s" text-anchor="middle" transform="rotate(-90 %.1f %.1f)">%s</text>' % (
                cx, cy, INK2, cx, cy, esc(yl))
        return s


# ── 원문 값 ────────────────────────────────────────────────────────────────
BMIN, BMAX, N = 0.1, 20.0, 1000
SMIN, SMAX = 0.01, 50.0
B = lambda t: t * BMIN + t * t * (BMAX - BMIN) / 2
T1 = {  # (값, 표준편차) 표 1 · 표 4. P2000 은 표 1 = 선형 보간, P2000r 은 표 4 = 반올림 보간
    "VE": {"ancestral": {"P1000": (4.98, .06), "P2000": (4.88, .06), "P2000r": (4.92, .02), "PC1000": (3.62, .03)},
           "reverse": {"P1000": (4.79, .07), "P2000": (4.74, .08), "P2000r": (4.72, .07), "PC1000": (3.60, .02)},
           "flow": {"P1000": (15.41, .15), "P2000": (10.54, .08), "P2000r": (12.87, .09), "PC1000": (3.51, .04)},
           "C2000": (20.43, .07)},
    "VP": {"ancestral": {"P1000": (3.24, .02), "P2000": (3.24, .02), "P2000r": (3.11, .03), "PC1000": (3.21, .02)},
           "reverse": {"P1000": (3.21, .02), "P2000": (3.19, .02), "P2000r": (3.10, .03), "PC1000": (3.18, .01)},
           "flow": {"P1000": (3.59, .04), "P2000": (3.23, .03), "P2000r": (3.25, .04), "PC1000": (3.06, .03)},
           "C2000": (19.06, .06)},
}
T2 = [("RealNVP", 3.49, "uni"), ("iResNet", 3.45, "uni"), ("Glow", 3.35, "uni"), ("MintNet", 3.32, "uni"),
      ("Residual Flow", 3.28, "uni"), ("FFJORD", 3.40, "uni"), ("Flow++", 3.29, "uni"),
      ("DDPM (L), ELBO", 3.70, "elbo"), ("DDPM (Lsimple), ELBO", 3.75, "elbo"),
      ("DDPM", 3.28, "ours"), ("DDPM cont. (VP)", 3.21, "ours"), ("DDPM cont. (sub-VP)", 3.05, "ours"),
      ("DDPM++ cont. (VP)", 3.16, "ours"), ("DDPM++ cont. (sub-VP)", 3.02, "ours"),
      ("DDPM++ cont. (deep, VP)", 3.13, "ours"), ("DDPM++ cont. (deep, sub-VP)", 2.99, "ours")]


def fig01():
    w, h = 960, 400
    b = title(w, "SDE 하나로 놓은 전체 틀", "앞으로 가는 식에는 학습할 것이 없고, 뒤로 가는 두 식이 함께 점수 하나만 요구한다")
    b += box(40, 110, 130, 150, FWD_SOFT, FWD) + txt(105, 170, "데이터", 14, weight="700") + txt(105, 192, "x(0) ~ p0", 12, INK2)
    b += box(790, 110, 130, 150, REV_SOFT, REV) + txt(855, 170, "사전분포", 14, weight="700") + txt(855, 192, "x(T) ~ pT", 12, INK2)
    b += line(170, 130, 788, 130, FWD, 2, m="af")
    b += txt(480, 120, "식 (5) 앞으로 가는 SDE:  dx = f(x,t) dt + g(t) dw", 13, FWD)
    b += line(790, 190, 172, 190, REV, 2, m="ar")
    b += txt(480, 180, "식 (6) 거꾸로 가는 SDE:  dx = [f - g² · 점수] dt + g dw̄   (걸음마다 잡음이 더해진다)", 13, REV)
    b += line(790, 245, 172, 245, PURP, 2, m="ap")
    b += txt(480, 235, "식 (13) 확률 흐름 ODE:  dx = [f - ½ g² · 점수] dt   (같은 주변 분포, 잡음 없음)", 13, PURP)
    b += box(250, 290, 460, 74, CODE_SOFT, CODE) + txt(480, 316, "점수 모델 s(x, t) ≈ ∇x log p_t(x)", 14, weight="700")
    b += txt(480, 342, "식 (7): 시간 t 를 뽑아 잡음 제거 점수 맞추기로 배운다", 12, INK2)
    b += line(420, 288, 420, 194, CODE, 1.4, "4 3") + line(560, 288, 560, 249, CODE, 1.4, "4 3")
    svg("fig01_overview", w, h, b, "앞으로 가는 SDE, 거꾸로 가는 SDE, 확률 흐름 ODE, 점수 모델의 관계")


def fig02():
    w, h = 960, 330
    b = title(w, "이산 사슬 둘이 SDE 둘의 이산화다", "표의 이름은 이 노트의 이름이고 식 번호는 원문 번호다")
    heads = [("모델", 40, 150), ("이산 사슬", 200, 280), ("N -> 무한", 490, 240), ("t = 1 의 분포", 740, 180)]
    for t, x, wd in heads:
        b += box(x, 62, wd, 30, "#DDE3E0", LINE, 1, 3) + txt(x + wd / 2, 82, t, 12, weight="700")
    rows = [("SMLD (NCSN)", "x_i = x_{i-1} + √(σ_i² - σ_{i-1}²) z  식 (8)", ["VE:  dx = √(d[σ²]/dt) dw", "식 (9)"], "N(x(0), σmax²)", FWD_SOFT),
            ("DDPM", "x_i = √(1-β_i) x_{i-1} + √β_i z  식 (10)", ["VP:  dx = -½βx dt + √β dw", "식 (11)"], "평균 0.0066 x(0), 분산 0.99996", REV_SOFT),
            ("새로 낸 꼴", "(이산 사슬에서 오지 않는다)", ["sub-VP:  dx = -½βx dt", "+ √(β(1-e^(-2∫β))) dw  식 (12)"], "평균 0.0066 x(0), 분산 0.99991", PURP_SOFT)]
    for i, (a, c, d, e, f) in enumerate(rows):
        y = 100 + i * 66
        b += box(40, y, 150, 56, f, LINE, 1, 3) + txt(115, y + 33, a, 13, weight="700")
        b += box(200, y, 280, 56, NODE, LINE, 1, 3) + txt(340, y + 33, c, 11.5)
        b += box(490, y, 240, 56, NODE, LINE, 1, 3) + txt(610, y + 24, d[0], 11.5) + txt(610, y + 42, d[1], 11.5)
        b += box(740, y, 180, 56, NODE, LINE, 1, 3) + txt(830, y + 33, e, 10.5)
    b += txt(480, 312, "오른쪽 칸의 수는 β 0.1 ~ 20 으로 내가 센 것. VE 의 σmax 는 원문 그림 5(a) · 그림 13 에서 읽은 50.", 11.5, INK2)
    svg("fig02_unify", w, h, b, "SMLD와 DDPM이 VE와 VP SDE의 이산화라는 대응")


def fig03():
    w, h = 980, 370
    b = title(w, "세 SDE 의 섭동 핵 (식 29 · 31 · 33 · 34, 내가 계산)", "VE 는 로그 축. VP 와 sub-VP 는 평균 계수가 같고, x(0) 이 고정이면 sub-VP 분산이 VP 분산의 제곱이다")
    ts = [i / 200 for i in range(1, 201)]
    a = Axes(70, 70, 240, 230, (0, 1), (1e-4, 1e4), ylog=True)
    b += a.frame([0, .25, .5, .75, 1], [1e-4, 1e-2, 1, 1e2, 1e4], "t", "VE 분산 σ²(t)", yf=lambda v: "%g" % v)
    b += poly([(a.X(t), a.Y((SMIN * (SMAX / SMIN) ** t) ** 2)) for t in ts], FWD, 2.2)
    b += txt(a.X(.5) + 6, a.Y(.5) + 16, "t = 0.5 에서 0.5", 11, FWD, "start")
    b += txt(a.X(.62), a.Y(2500) - 4, "t = 1 에서 2,500", 11, FWD)
    c = Axes(385, 70, 240, 230, (0, 1), (0, 1))
    b += c.frame([0, .25, .5, .75, 1], [0, .25, .5, .75, 1], "t", "VP · sub-VP 평균 계수")
    b += poly([(c.X(t), c.Y(math.exp(-B(t) / 2))) for t in ts], REV, 2.2)
    b += txt(c.X(.42), c.Y(.62), "e^(-½∫β), 두 SDE 같음", 11, REV, "start")
    e = Axes(700, 70, 240, 230, (0, 1), (0, 1))
    b += e.frame([0, .25, .5, .75, 1], [0, .25, .5, .75, 1], "t", "분산")
    b += poly([(e.X(t), e.Y(1 - math.exp(-B(t)))) for t in ts], REV, 2.2)
    b += poly([(e.X(t), e.Y((1 - math.exp(-B(t))) ** 2)) for t in ts], PURP, 2.2)
    tm = 0.25896
    b += line(e.X(tm), e.Y(.5), e.X(tm), e.Y(.25), NO, 1.6) + txt(e.X(tm) + 12, e.Y(.12), "차 최대 0.25 (t = 0.259)", 11, NO, "start")
    b += txt(e.X(.12), e.Y(.62), "VP", 12, REV, "start") + txt(e.X(.4), e.Y(.5), "sub-VP", 12, PURP, "start")
    svg("fig03_kernels", w, h, b, "VE VP sub-VP 섭동 핵의 평균과 분산")


def fig04():
    w, h = 980, 360
    ab, pts_m, pts_v, pts_r = 1.0, [], [], []
    for i in range(1, N + 1):
        b_i = BMIN / N + (i - 1) / (N * (N - 1)) * (BMAX - BMIN)
        ab *= 1 - b_i
        t = i / N
        pts_m.append((i, abs(math.exp(-B(t) / 2) - math.sqrt(ab))))
        pts_v.append((i, abs((1 - math.exp(-B(t))) - (1 - ab))))
        d = (SMIN * (SMAX / SMIN) ** ((i - 1) / (N - 1))) ** 2
        cc = (SMIN * (SMAX / SMIN) ** t) ** 2
        pts_r.append((i, 100 * (cc / d - 1), abs(cc - d)))
    print("   VP 평균 최대차 %.6f (i=%d), 분산 최대차 %.6f (i=%d)" % (
        max(p[1] for p in pts_m), max(pts_m, key=lambda p: p[1])[0], max(p[1] for p in pts_v), max(pts_v, key=lambda p: p[1])[0]))
    print("   VE 상대차 최대 %.3f%%, 절대차 최대 %.3f" % (max(p[1] for p in pts_r), max(p[2] for p in pts_r)))
    b = title(w, "원문 그림 5 를 수로: 이산 사슬과 연속 핵의 차이 (N = 1000, 내가 계산)", "원문 그림은 축 전체로 그려 겹쳐 보인다. 차이를 따로 그리면 어디서 벌어지는지 보인다")
    a = Axes(90, 70, 370, 230, (0, 1000), (0, .0012))
    b += a.frame([0, 250, 500, 750, 1000], [0, .0004, .0008, .0012], "눈금 번호 i (t = i / 1000)", "VP: 절대 차")
    b += poly([(a.X(p[0]), a.Y(p[1])) for p in pts_m[::4]], REV, 2) + poly([(a.X(p[0]), a.Y(p[1])) for p in pts_v[::4]], PURP, 2)
    b += txt(a.X(450), a.Y(.00112), "평균 계수: 최대 0.00099 (i = 602)", 11, REV, "start") + txt(a.X(20), a.Y(.00093), "분산: 최대 0.00081 (i = 141)", 11, PURP, "start")
    e = Axes(570, 70, 370, 230, (0, 1000), (0, 2))
    b += e.frame([0, 250, 500, 750, 1000], [0, .5, 1, 1.5, 2], "눈금 번호 i", "VE: 분산 상대 차 (%)")
    b += poly([(e.X(p[0]), e.Y(p[1])) for p in pts_r[::4]], FWD, 2)
    b += txt(e.X(70), e.Y(1.82), "최대 1.72% (i = 1)", 11, FWD, "start") + txt(e.X(30), e.Y(.42), "절대 차 최대는 0.92 (i = 941),", 11, INK2, "start") + txt(e.X(30), e.Y(.27), "세로축 2,500 의 0.037%", 11, INK2, "start")
    svg("fig04_discretization_gap", w, h, b, "이산 사슬과 연속 핵의 차이")


def toy_score(x, t):
    a = math.exp(-B(t) / 2)
    v = .0625 * a * a + 1 - a * a
    ws = []
    for w0, m in ((.3, -2.), (.7, 2.)):
        d = x - m * a
        ws.append((w0 * math.exp(-.5 * d * d / v), -d / v))
    s = ws[0][0] + ws[1][0]
    return (ws[0][0] * ws[0][1] + ws[1][0] * ws[1][1]) / s


def fig05():
    w, h = 980, 380
    b = title(w, "참 점수를 넣은 1 차원 궤적 (내가 계산, 신경망 없음)", "p0 = 0.3 N(-2, 0.25²) + 0.7 N(2, 0.25²), VP SDE, 오일러 500 걸음, 같은 출발점 24 개")
    rng = random.Random(3)
    st = [rng.gauss(0, 1) for _ in range(24)]
    for k, (name, c, ox) in enumerate((("식 (6) 거꾸로 가는 SDE", REV, 70), ("식 (13) 확률 흐름 ODE", PURP, 540))):
        a = Axes(ox, 76, 400, 230, (1, 0), (-3.5, 3.5))
        b += a.frame([1, .75, .5, .25, 0], [-3, -2, -1, 0, 1, 2, 3], "시간 t (왼쪽이 사전분포, 오른쪽이 데이터)", "x" if k == 0 else None)
        b += txt(ox + 200, 70, name, 12.5, c, weight="700")
        for x0 in st:
            x, pts = x0, []
            M = 500
            for i in range(M):
                t = 1 - i * (1 - 1e-3) / M
                dt = (1 - 1e-3) / M
                bt = BMIN + t * (BMAX - BMIN)
                s = toy_score(x, t)
                if k == 0:
                    x += (.5 * bt * x + bt * s) * dt + math.sqrt(bt * dt) * rng.gauss(0, 1)
                else:
                    x += (.5 * bt * x + .5 * bt * s) * dt
                if i % 3 == 0:
                    pts.append((a.X(t), a.Y(max(-3.5, min(3.5, x)))))
            b += poly(pts, c, .9, op=".55")
    b += txt(w / 2, 368, "ODE 는 x(T) 하나에 x(0) 하나가 정해진다. SDE 는 같은 출발에서도 끝이 달라질 수 있다.", 11.5, INK2)
    svg("fig05_toy_paths", w, h, b, "참 점수로 푼 SDE와 ODE 궤적")


TOY = [(5, .7973, .2325), (10, .2451, .1012), (20, .0682, .0495), (50, .0256, .0227),
       (100, .0116, .0144), (200, .0083, .0103), (1000, .0064, .0075)]


def fig06():
    w, h = 720, 370
    b = title(w, "참 점수를 넣어도 걸음 수에 따른 오차가 남는다 (내가 계산)", "toy_exact_score.py, 입자 200,000 개, 앞 궤적 그림과 같은 혼합")
    a = Axes(90, 66, 580, 240, (5, 1000), (.003, 1), xlog=True, ylog=True)
    b += a.frame([5, 10, 20, 50, 100, 200, 1000], [.01, .1, 1], "오일러 걸음 수 N", "W1 (참 표본과의 거리)", yf=lambda v: "%g" % v)
    b += line(a.X(5), a.Y(.004), a.X(1000), a.Y(.004), MUTED, 1.2, "5 4") + txt(a.X(5) + 8, a.Y(.004) - 5, "표본 잡음 바닥 0.0040", 11, MUTED, "start")
    for idx, c in ((1, REV), (2, PURP)):
        b += poly([(a.X(t[0]), a.Y(t[idx])) for t in TOY], c, 2.2)
        for t in TOY:
            b += dot(a.X(t[0]), a.Y(t[idx]), c, 3.5)
    b += txt(a.X(7), a.Y(.75), "거꾸로 가는 SDE (N = 5 에서 0.797)", 11.5, REV, "start") + txt(a.X(5.5), a.Y(.03), "확률 흐름 ODE (N = 5 에서 0.232)", 11.5, PURP, "start")
    svg("fig06_toy_w1", w, h, b, "걸음 수에 따른 분포 거리")


def fig07():
    w, h = 880, 320
    b = title(w, "PC 표본기의 칸에 앞선 방법들을 놓으면 (4.2절 · 부록 G)", "칸이 뜻하는 것은 한 눈금마다의 할 일이다. 점수 평가는 P 한 걸음 1 회, C 한 걸음 1 회")
    for t, x in (("예측기 (식을 푼다)", 290), ("수정기 (주변 분포를 맞춘다)", 545), ("눈금당 점수 평가", 770)):
        b += txt(x, 82, t, 12.5, INK2, weight="700")
    rows = [("SMLD (Song · Ermon)", "항등 (아무것도 안 함)", "담금질 랑주뱅 M 걸음", "M", FWD_SOFT),
            ("DDPM (Ho 외)", "조상 표집 식 (4)", "항등", "1", REV_SOFT),
            ("표 1 PC1000", "조상 · 거꾸로 확산 · 확률 흐름", "랑주뱅 1 걸음, r 격자 탐색", "2", CODE_SOFT),
            ("표 1 C2000", "항등", "랑주뱅 2 걸음", "2", NODE)]
    for i, (a, p, c, n, f) in enumerate(rows):
        y = 96 + i * 50
        b += box(30, y, 150, 42, f, LINE, 1, 3) + txt(105, y + 26, a, 11.5, weight="700")
        b += box(190, y, 200, 42, NODE, LINE, 1, 3) + txt(290, y + 26, p, 11)
        b += box(445, y, 200, 42, NODE, LINE, 1, 3) + txt(545, y + 26, c, 11.5)
        b += box(710, y, 120, 42, NODE, LINE, 1, 3) + txt(770, y + 26, n, 13, weight="700")
    svg("fig07_pc_family", w, h, b, "PC 표본기와 앞선 방법의 대응")


def fig08():
    w, h = 980, 400
    b = title(w, "표 1 · 표 4 의 FID (CIFAR-10, 표집 다섯 번의 평균 ± 표준편차)", "VE 와 VP 는 축이 다르다. 학습 반복은 표에 없다")
    names = [("ancestral", "조상 표집"), ("reverse", "거꾸로 확산"), ("flow", "확률 흐름")]
    cols = ["P1000", "P2000", "P2000r", "PC1000"]
    cc = {"P1000": MUTED, "P2000": FWD, "P2000r": PURP, "PC1000": OK}
    lab = {"P1000": "P1000", "P2000": "P2000 선형", "P2000r": "P2000 반올림", "PC1000": "PC1000"}
    for sde, xr, ox, ticks in (("VE", (3, 16.5), 90, [3, 6, 9, 12, 15]), ("VP", (3, 3.65), 570, [3.0, 3.2, 3.4, 3.6])):
        a = Axes(ox, 84, 370, 240, xr, (0, 3))
        b += a.frame(ticks, [], "FID (낮을수록 좋음)")
        b += txt(ox + 185, 78, sde + " SDE (C2000 은 %.2f, 축 밖)" % T1[sde]["C2000"][0], 12.5, weight="700")
        for j, (r, nm) in enumerate(names):
            y0 = 84 + (j + .5) * 80
            b += txt(ox - 8, y0 + 4, nm, 11, INK2, "end")
            for m, col in enumerate(cols):
                v, s = T1[sde][r][col]
                y = y0 - 21 + m * 14
                b += line(a.X(v - s), y, a.X(v + s), y, cc[col], 2) + dot(a.X(v), y, cc[col], 3.5)
                right = a.X(v) < ox + 320
                b += txt((a.X(v + s) + 7) if right else (a.X(v - s) - 7), y + 4, "%.2f" % v, 9.5, cc[col], "start" if right else "end")
    x = 240
    for col in cols:
        b += dot(x, 372, cc[col], 4) + txt(x + 9, 376, lab[col], 11.5, INK2, "start")
        x += 130
    svg("fig08_table1", w, h, b, "표 1과 표 4의 FID")


def fig09():
    w, h = 900, 350
    b = title(w, "VP 칸: 같은 P2000 이 보간 방법에 따라 PC1000 의 위 · 아래로 간다", "표 1 은 선형 보간, 표 4 는 반올림 보간. 조상 표집 줄에서 수정기 몫 0.03 보다 보간 몫 0.13 이 크다")
    a = Axes(100, 70, 740, 230, (0, 1), (3.0, 3.3))
    names = [("ancestral", "조상 표집", .17), ("reverse", "거꾸로 확산", .5), ("flow", "확률 흐름", .83)]
    b += a.frame([], [3.0, 3.1, 3.2, 3.3], yl="FID", yf=lambda v: "%.1f" % v)
    for r, nm, cx in names:
        b += txt(a.X(cx), a.y + a.h + 20, nm, 12.5, weight="700")
        d = T1["VP"][r]
        for col, dx, c, n in (("P2000", -.09, FWD, "선형"), ("P2000r", -.03, PURP, "반올림"), ("PC1000", .05, OK, "PC1000")):
            v, s = d[col]
            x = a.X(cx + dx)
            b += line(x, a.Y(v - s), x, a.Y(v + s), c, 2.2) + dot(x, a.Y(v), c, 4.5)
            b += txt(x, a.Y(v + s) - 7, "%.2f" % v, 10.5, c)
            b += txt(x, a.y + a.h - 6, n, 9.5, c)
    svg("fig09_interp_flip", w, h, b, "보간 방법에 따른 P2000과 PC1000의 순서")


def fig10():
    w, h = 860, 300
    b = title(w, "표 5 의 신호 대 잡음비 r 과 r² (수정기 걸음 폭에 들어가는 몫, 내가 셈)", "알고리즘 4 · 5 의 걸음 폭 ε = 2 (r ‖z‖/‖g‖)² (VP 는 αi 가 더 곱해진다). 막대는 r² / 0.16²")
    rows = [("VE PC1000 조상", .17, FWD), ("VE PC1000 거꾸로 확산", .16, FWD), ("VE PC1000 확률 흐름", .17, FWD), ("VE C2000", .22, FWD),
            ("VP PC1000 조상", .01, REV), ("VP PC1000 거꾸로 확산", .01, REV), ("VP PC1000 확률 흐름", .04, REV), ("VP C2000", .27, REV)]
    for i, (n, r, c) in enumerate(rows):
        y = 64 + i * 26
        v = r * r / .16 / .16
        b += txt(190, y + 15, n, 11.5, INK2, "end")
        b += box(200, y + 2, max(v * 170, 1), 18, c, c, 0, 2)
        b += txt(206 + v * 170, y + 16, "r = %.2f,  %.4g 배" % (r, v), 11, INK, "start")
    svg("fig10_snr", w, h, b, "표 5의 r과 r 제곱 비")


def fig11():
    w, h = 900, 530
    b = title(w, "표 2 의 NLL: 평가 방식이 셋 섞여 있다", "bits/dim, 낮을수록 좋음. 표에 표준편차가 없다")
    a = Axes(250, 66, 590, 380, (2.9, 3.85), (0, len(T2)))
    b += a.frame([3.0, 3.2, 3.4, 3.6, 3.8], [], "NLL (bits/dim)")
    cm = {"uni": MUTED, "elbo": NO, "ours": FWD}
    for i, (n, v, g) in enumerate(T2):
        y = a.y + (i + .5) * a.h / len(T2)
        b += txt(242, y + 4, n, 11, INK2, "end")
        b += dot(a.X(v), y, cm[g], 4.5, None if g != "elbo" else "#FFFFFF")
        b += txt(a.X(v) + 9, y + 4, ("≤ %.2f" if g == "elbo" else "%.2f") % v, 10.5, cm[g], "start")
    x = 170
    for g, n in (("uni", "다른 논문 값(균일 역양자화)"), ("elbo", "다른 논문의 하한(이산 데이터)"), ("ours", "이 논문의 ODE 값")):
        b += dot(x, 508, cm[g], 4.5, None if g != "elbo" else "#FFFFFF") + txt(x + 9, 512, n, 11.5, INK2, "start")
        x += 225
    svg("fig11_table2_nll", w, h, b, "표 2의 NLL")


def fig12():
    w, h = 900, 350
    b = title(w, "같은 모델의 FID 두 벌: 표본기와 체크포인트가 함께 바뀐다", "왼쪽 점 = 표 3 (PC 표본기, FID 가 가장 낮은 체크포인트). 오른쪽 점 = 표 2 (RK45 ODE, 마지막 체크포인트)")
    rows = [("DDPM++ cont. (VP)", 2.55, 3.93), ("DDPM++ cont. (sub-VP)", 2.61, 3.16), ("DDPM++ cont. (deep, VP)", 2.41, 3.08), ("DDPM++ cont. (deep, sub-VP)", 2.41, 2.92)]
    a = Axes(270, 70, 570, 220, (2.2, 4.1), (0, 4))
    b += a.frame([2.4, 2.8, 3.2, 3.6, 4.0], [], "FID", xf=lambda v: "%.1f" % v)
    for i, (n, p, o) in enumerate(rows):
        y = a.y + (i + .5) * a.h / 4
        b += txt(262, y + 4, n, 11.5, INK2, "end")
        b += line(a.X(p), y, a.X(o), y, LINE, 3) + dot(a.X(p), y, OK, 5) + dot(a.X(o), y, PURP, 5)
        b += txt(a.X(p), y - 10, "%.2f" % p, 11, OK) + txt(a.X(o), y - 10, "%.2f" % o, 11, PURP)
        b += txt(a.X((p + o) / 2), y + 18, "+%.2f" % (o - p), 10.5, INK2)
    svg("fig12_fid_pairs", w, h, b, "표 2와 표 3의 FID 비교")


def fig13():
    w, h = 1000, 370
    b = title(w, "표 3 의 FID 사다리: 한 칸에 바뀐 것이 하나가 아니다 (부록 H)", "숫자는 표 3. 칸 사이 글은 부록 H.1 · H.2 에 적힌 변경을 모은 것")
    for k, (c, rows, y) in enumerate(((FWD, [("NCSN++", 2.45), ("cont.", 2.38), ("cont. (deep)", 2.20)], 70),
                                      (REV, [("DDPM++", 2.78), ("cont.", 2.55), ("cont. (deep)", 2.41)], 206))):
        x = 50
        ch = [["목적 함수 이산 -> 연속", "위치 임베딩 -> 푸리에 특징", "반복 1.3M -> 0.95M"], ["잔차 블록 두 배"]] if k == 0 else \
             [["목적 함수 이산 -> 연속", "연속 시간 조건", "예측기 -> 오일러-마루야마"], ["깊이 두 배", "반복 0.95M"]]
        for i, (n, v) in enumerate(rows):
            b += box(x, y, 150, 72, NODE, c, 1.6) + txt(x + 75, y + 28, n, 12.5, weight="700") + txt(x + 75, y + 54, "FID %.2f" % v, 14, c, weight="700")
            if i < 2:
                b += line(x + 152, y + 14, x + 348, y + 14, c, 1.6, m="af" if k == 0 else "ar")
                b += txt(x + 250, y + 10, "%.2f" % (rows[i + 1][1] - v), 12, c, weight="700")
                for q, t in enumerate(ch[i]):
                    b += txt(x + 250, y + 34 + q * 15, t, 10.5, INK2)
            x += 350
    b += txt(w / 2, 310, "VE 칸의 PC 는 눈금당 평가 2 회다. H.1 은 VP 탐색에서 수정기를 뺐다고 적고, 4.4절은 표 3 이 PC 표본기라고 적는다.", 11.5, INK2)
    b += txt(w / 2, 332, "원문 그림 10 의 VE · CIFAR-10 에서 가장 낮은 체크포인트 평균 FID 는 2.60 이고, 표 3 의 2.45 는 학습 중 가장 낮은 체크포인트 값이다.", 11.5, INK2)
    svg("fig13_table3_steps", w, h, b, "표 3의 단계별 변경")


def fig14():
    w, h = 980, 370
    b = title(w, "원문 그림 3 왼쪽을 벡터 좌표로 (내가 읽은 값)", "표식 수 13 · 85 · 547 은 라벨 14 · 86 · 548 보다 하나 적다. 로그 축 밖 평가 번호 0 하나로 읽힌다")
    a = Axes(80, 64, 470, 250, (1, 1000), (0, 1), xlog=True)
    b += a.frame([1, 10, 100, 1000], [0, .25, .5, .75, 1], "평가 번호", "평가한 시간 t")
    cm = {"1e-1": FWD, "1e-3": REV, "1e-5": OK}
    for k, c in cm.items():
        pts = V["fig3"][k]
        step = 1 if len(pts) < 200 else 3
        b += poly([(a.X(max(1, p[0])), a.Y(p[1])) for p in pts[::step]], c, 1.8)
    b += txt(a.X(15), a.Y(.08), "1e-1", 11.5, FWD, "start") + txt(a.X(90), a.Y(.08), "1e-3", 11.5, REV, "start") + txt(a.X(330), a.Y(.6), "1e-5", 11.5, OK, "start")
    x0, y0 = 610, 70
    b += txt(x0 + 165, y0, "라벨 NFE 와 줄어든 비율", 12.5, weight="700")
    rows = [("548 -> 86", "548 대비", "84.3%", "그림에서 차이가 보이지 않는다"), ("548 -> 14", "548 대비", "97.4%", "얼룩이 보인다"),
            ("1000 -> 86", "1000 대비", "91.4%", "(1000 칸은 그림에 없다)"), ("1000 -> 14", "1000 대비", "98.6%", "얼룩이 보인다")]
    for i, (p, q, r, s) in enumerate(rows):
        y = y0 + 14 + i * 44
        b += box(x0, y, 330, 38, OK_SOFT if i == 2 else NODE, LINE, 1, 3)
        b += txt(x0 + 10, y + 16, p, 12, anchor="start", weight="700") + txt(x0 + 110, y + 16, q, 11, INK2, "start") + txt(x0 + 200, y + 16, r, 13, NO, "start", "700")
        b += txt(x0 + 10, y + 32, s, 10.5, INK2, "start")
    print("   t<0.1 비율", {k: round(sum(1 for p in V["fig3"][k] if p[1] < .1) / len(V["fig3"][k]), 3) for k in cm})
    b += txt(x0, y0 + 208, "「90% 넘게 줄고 시각 품질에 영향 없음」 이 둘 다 서는 짝은", 11, INK2, "start")
    b += txt(x0, y0 + 225, "1000 -> 86 뿐이고 원문은 이 분모를 적지 않는다.", 11, INK2, "start")
    svg("fig14_ode_eval", w, h, b, "그림 3 왼쪽 재현과 NFE 감소 비율")


def fig15():
    w, h = 980, 360
    b = title(w, "원문 그림 8 을 벡터 좌표로 (내가 읽은 값)", "모델 둘(잔차 블록 4 대 8), 이미지 16 장, VE SDE, 3,072 차원. 원문 그림 7 의 100 차원은 r = 0.937")
    a = Axes(170, 80, 340, 190, (0, 400), (0, 2))
    b += a.frame([0, 100, 200, 300, 400], [], "차원별 부호화 차이")
    for i, (k, n, c) in enumerate((("A vs B", "모델 A 대 B", REV), ("shuffled", "섞은 대조", FWD))):
        d = V["fig8_box"][k]
        q1, med, q3, wh = d["q1_med_q3_whisker"]
        y = a.y + (i + .5) * a.h / 2
        b += txt(162, y + 4, n, 12, INK2, "end")
        b += line(a.X(0), y, a.X(wh), y, c, 1.6) + box(a.X(q1), y - 18, a.X(q3) - a.X(q1), 36, REV_SOFT if i == 0 else FWD_SOFT, c, 1.4, 0)
        b += line(a.X(med), y - 18, a.X(med), y + 18, c, 2.4) + line(a.X(wh), y, a.X(d["flier_max"]), y, c, 1, "2 3") + dot(a.X(d["flier_max"]), y, c, 3)
        b += txt(a.X(med) + 3, y - 24, "중앙값 %.1f" % med, 11, c, "start")
        b += txt(a.X(d["flier_max"]), y + 18, "최대 %.1f" % d["flier_max"], 11, c)
    e = Axes(590, 80, 340, 190, (0, 1), (0, 700))
    b += e.frame([0, .25, .5, .75, 1], [0, 200, 400, 600], "차원별 상관 계수 (이미지 16 장)", yf=lambda v: "%d" % v)
    tot = sum(x[2] for x in V["fig8_hist"])
    for l, r, c in V["fig8_hist"]:
        if c > .3:
            b += box(e.X(l), e.Y(c), e.X(r) - e.X(l) - .4, e.Y(0) - e.Y(c), REV, REV, 0, 0)
    mean = sum((x[0] + x[1]) / 2 * x[2] for x in V["fig8_hist"]) / tot
    ge9 = sum(x[2] for x in V["fig8_hist"] if x[1] >= .9) / tot
    print("   합 %.1f, 평균 r %.3f, 0.9 이상 %.3f" % (tot, mean, ge9))
    b += txt(e.X(.03), e.Y(620), "막대 합 3,072", 11.5, INK2, "start") + txt(e.X(.03), e.Y(530), "평균 r 0.916", 11.5, INK2, "start")
    b += txt(e.X(.03), e.Y(440), "r ≥ 0.9 인 차원 73.7%", 11.5, INK2, "start") + txt(e.X(.03), e.Y(350), "원문 삽입 그림의 차원 r = 0.96", 11.5, INK2, "start")
    b += txt(w / 2, 340, "두 독립 N(0, 50²) 의 차이는 중앙값이 47.7 이다(내가 계산). 섞은 대조 46.8 과 맞고, 모델 A 대 B 의 중앙값은 대조의 24% 다.", 11.5, INK2)
    svg("fig15_identifiable", w, h, b, "그림 8의 부호화 차이와 상관 계수")


def fig16():
    w, h = 980, 370
    b = title(w, "원문 그림 10 의 중앙값을 벡터 좌표로 (내가 읽은 값, VE SDE)", "「평균으로 늘 낫다」 는 중앙값으로 맞는다. 낮은 쪽 수염 끝은 CelebA 에서 켜고 끄는 방향이 갈린다 (붉은 글)")
    names = [("FIR", "FIR 상 · 하표본"), ("skip_rescale", "지름길 1/√2"), ("resblock_type", "BigGAN 블록"), ("num_res_blocks", "블록 4 개")]
    for k, (ds, ox, i0) in enumerate((("CIFAR-10", 150, 0), ("CelebA 64", 600, 2))):
        a = Axes(ox, 76, 340, 220, (2.4, 4.0), (0, 4))
        b += a.frame([2.5, 3.0, 3.5, 4.0], [], "FID (체크포인트 평균)", xf=lambda v: "%.1f" % v)
        b += txt(ox + 170, 70, ds, 13, weight="700")
        for j, (key, n) in enumerate(names):
            off, on = V["fig10"][key][i0], V["fig10"][key][i0 + 1]
            y = a.y + (j + .5) * a.h / 4
            b += txt(ox - 8, y + 4, n, 11, INK2, "end")
            b += line(a.X(off["median"]), y, a.X(on["median"]), y, LINE, 3)
            b += dot(a.X(off["median"]), y, MUTED, 5) + dot(a.X(on["median"]), y, OK, 5)
            b += txt(a.X(off["median"]), y - 10, "%.2f" % off["median"], 10.5, MUTED) + txt(a.X(on["median"]), y - 10, "%.2f" % on["median"], 10.5, OK)
            b += txt(a.X(2.42), y + 20, "수염 끝 끔 %.2f · 켬 %.2f" % (off["low"], on["low"]), 10, NO if on["low"] > off["low"] else INK2, "start")
    b += dot(420, 354, MUTED, 4.5) + txt(429, 358, "끔", 11.5, INK2, "start") + dot(480, 354, OK, 4.5) + txt(489, 358, "켬", 11.5, INK2, "start")
    svg("fig16_fig10_medians", w, h, b, "그림 10의 구성 요소별 중앙값")


def fig17():
    w, h = 760, 350
    b = title(w, "원문 그림 13 의 분류기 곡선을 벡터 좌표로 (내가 읽은 값)", "시간에 조건을 건 WRN-28-10 의 정확도. 학습 · 시험 어느 쪽 값인지 원문에 적혀 있지 않다")
    a = Axes(90, 66, 620, 230, (.01, 50), (0, 1), xlog=True)
    b += a.frame([.01, .1, 1, 10, 50], [0, .2, .4, .6, .8, 1], "σ", "정확도", xf=lambda v: "%g" % v)
    b += poly([(a.X(p[0]), a.Y(p[1])) for p in V["fig13"]], FWD, 2.2)
    b += line(a.X(.01), a.Y(.1), a.X(50), a.Y(.1), MUTED, 1.2, "5 4") + txt(a.X(.012), a.Y(.1) + 15, "열 부류 무작위 0.1", 11, MUTED, "start")
    for s, v in ((.01, .923), (.1, .893), (1, .479), (10, .142), (50, .107)):
        b += dot(a.X(s), a.Y(v), FWD, 4) + txt(a.X(s) + (6 if s < 50 else -6), a.Y(v) - 8, "%.3f" % v, 11, FWD, "start" if s < 50 else "end")
    svg("fig17_classifier_acc", w, h, b, "잡음 크기에 따른 분류기 정확도")


def fig18():
    w, h = 960, 340
    b = title(w, "이 편의 자리", "화살표는 원문이 인용으로 적은 연결이다")
    items = [(30, 130, "점수 맞추기", "Hyvärinen 2005 · Vincent 2011", NODE), (270, 60, "역시간 SDE", "Anderson 1982", NODE),
             (270, 130, "SMLD (NCSN)", "Song · Ermon 2019 · 2020", FWD_SOFT), (270, 200, "DDPM", "Sohl-Dickstein 2015 · Ho 2020", REV_SOFT),
             (520, 130, "Score SDE", "이 편 (ICLR 2021)", CODE_SOFT), (760, 80, "Neural ODE · FFJORD", "우도 계산 도구", NODE),
             (760, 180, "Maoutsa 외 2020", "확률 흐름의 착상", NODE)]
    for x, y, a, s, f in items:
        b += box(x, y, 180, 58, f, LINE if f != CODE_SOFT else CODE, 1.4) + txt(x + 90, y + 25, a, 13, weight="700") + txt(x + 90, y + 44, s, 10.5, INK2)
    b += line(210, 159, 268, 159, INK2, 1.3, m="ai")
    b += line(450, 89, 518, 145, INK2, 1.3, m="ai") + line(450, 159, 518, 159, INK2, 1.3, m="ai") + line(450, 229, 518, 173, INK2, 1.3, m="ai")
    b += line(760, 109, 702, 145, INK2, 1.3, m="ai") + line(760, 209, 702, 173, INK2, 1.3, m="ai")
    b += txt(480, 292, "DDPM 은 ε 예측을 점수 맞추기로 읽었고, 이 편은 그 대응을 식 (3) 으로 옮긴 뒤 시간을 연속으로 늘린다.", 11.5, INK2)
    b += txt(480, 314, "이 저장소 다음 칸의 DDIM 은 원문 본문과 참고 문헌 목록에 나오지 않는다(글자 층 검색).", 11.5, INK2)
    svg("fig18_lineage", w, h, b, "이 논문의 계보")


if __name__ == "__main__":
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10, fig11, fig12, fig13, fig14, fig15, fig16, fig17, fig18):
        f()
