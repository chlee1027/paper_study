# -*- coding: utf-8 -*-
"""배치 정규화 노트(Ioffe & Szegedy, ICML 2015)의 그림 열여섯을 만든다.

색과 글꼴은 앞선 노트들(퍼셉트론부터 GAN 까지)의 그림과 맞췄다 — 저장소의 노트들이 한 벌로 읽히게
하려는 것이다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다). 무작위는 seed 0.

  python make_figures.py

그림 1 의 분포 이동, 2 의 시그모이드 포화 비율, 3 의 치우침 발산, 4 의 공분산 계수, 5 의 알고리즘 1 손계산,
6 의 역전파 식과 유한 차분 비교, 7 의 m/(m-1) 보정, 8 의 미니배치 의존, 9 의 합성곱 유효 미니배치,
10 의 척도 불변, 13 의 걸음 수 배수는 이 파일이 직접 계산한다. 12 · 13 · 15 의 논문 값은 본문 표와
300 dpi 로 읽은 눈금이다. 계산한 값은 돌릴 때 화면에도 찍는다.
"""
import io, os, math, random
from statistics import NormalDist

OUT = os.path.dirname(os.path.abspath(__file__))
random.seed(0)

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
CODE      = "#9A7B00"   # 노랑 — 정규화된 값
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"   # 초록 — 된다
NO        = "#C0392B"   # 빨강 — 안 된다
# 결과 그림 계열 색 — 배치 정규화 없음 · 있음. 이 순서로 고정한다.
S_BASE    = "#2A78D6"
S_BN      = "#EB6834"
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


def sig(x):
    return 1.0 / (1.0 + math.exp(-x))


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q
    f = int(math.floor(k))
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def mstd(v):
    m = sum(v) / len(v)
    return m, math.sqrt(sum((a - m) ** 2 for a in v) / len(v))


def bn(v, eps=1e-5):
    m, s = mstd(v)
    return [(a - m) / math.sqrt(s * s + eps) for a in v]


def hist(b, x0, y0, w, h, vals, lo, hi, nb, col, title, sub):
    cnt = [0] * nb
    for a in vals:
        k = int((a - lo) / (hi - lo) * nb)
        if 0 <= k < nb:
            cnt[k] += 1
    mx = max(cnt)
    b += box(x0, y0, w, h, fill="none", stroke=LINE)
    b += txt(x0 + w / 2, y0 + 20, title, 12, weight="bold")
    base = y0 + h - 40
    bw = (w - 30) / float(nb)
    for i, c in enumerate(cnt):
        hh = (h - 90) * c / float(mx)
        b += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x0 + 15 + i * bw, base - hh, bw - 1, hh, col)
    b += line(x0 + 15, base, x0 + w - 15, base, INK2, 1)
    for t in range(int(math.ceil(lo)), int(hi) + 1, 2):
        xx = x0 + 15 + (t - lo) / (hi - lo) * (w - 30)
        b += txt(xx, base + 14, "%d" % t, 9, fill=MUTED)
    b += txt(x0 + w / 2, y0 + h - 8, sub, 11, fill=INK2)
    return b


# ── 그림 1. 앞 층의 파라미터가 바뀌면 이 층의 입력 분포가 바뀐다 ─────────────────────
N1 = 3000
u = [random.gauss(0, 1) for _ in range(N1)]
w2, b2 = 4.0, -2.0                      # 이 층 앞의 선형 변환(고정)
def layer_in(w1, b1):
    return [w2 * sig(w1 * a + b1) + b2 for a in u]
xA = layer_in(1.0, 0.0)
xB = layer_in(3.0, 1.0)
for nm, v in (("앞 층 w1=1, b1=0", xA), ("앞 층 w1=3, b1=1", xB)):
    m, s = mstd(v)
    print("  [1] %s: 이 층 입력 평균 %.3f, 표준편차 %.3f, 15/50/85 백분위 %.3f / %.3f / %.3f"
          % (nm, m, s, pct(v, .15), pct(v, .5), pct(v, .85)))
for nm, v in (("A", bn(xA)), ("B", bn(xB))):
    m, s = mstd(v)
    print("      BN 뒤 %s: 평균 %.4f, 표준편차 %.4f, 15/50/85 %.3f / %.3f / %.3f" % (nm, m, s, pct(v, .15), pct(v, .5), pct(v, .85)))
mA, sA = mstd(xA); mB, sB = mstd(xB)
W, H = 820, 470
b = defs()
b += txt(20, 30, "내부 공변량 이동을 가장 작게 — 앞 층 파라미터만 바꿨는데 이 층이 보는 입력 분포가 바뀐다 (내가 붙인 예)", 14, anchor="start", weight="bold")
b = hist(b, 20, 50, 385, 190, xA, -3, 3, 30, S_BASE, "앞 층 w1=1, b1=0", "평균 %.2f, 표준편차 %.2f" % (mA, sA))
b = hist(b, 415, 50, 385, 190, xB, -3, 3, 30, S_BASE, "앞 층 w1=3, b1=1 로 바뀐 뒤", "평균 %.2f, 표준편차 %.2f — 모양도 두 봉우리로" % (mB, sB))
b = hist(b, 20, 250, 385, 190, bn(xA), -3, 3, 30, S_BN, "같은 입력에 BN (평균 0, 분산 1)", "평균과 분산은 고정 — 모양은 그대로")
b = hist(b, 415, 250, 385, 190, bn(xB), -3, 3, 30, S_BN, "바뀐 뒤에도 BN", "평균과 분산은 같다. 두 봉우리 모양은 남는다")
b += txt(410, 462, "u ~ N(0,1) 3,000 점, 이 층 입력 x = 4·σ(w1·u + b1) − 2. BN 은 1·2차 적률만 고정한다 — 분포 전체를 고정하는 것이 아니다", 11, fill=MUTED)
svg("fig01_covariate_shift", W, H, b, "앞 층 파라미터 변화에 따른 입력 분포 이동")


# ── 그림 2. 시그모이드 포화 — 입력 분포가 밀리면 기울기가 사라진다 ──────────────────
def dsig(x):
    s = sig(x)
    return s * (1 - s)
def expect(mu, sd, f, n=4000):
    lo, hi = mu - 8 * sd, mu + 8 * sd
    h = (hi - lo) / n
    nd_ = NormalDist(mu, sd)
    return sum(f(lo + (i + 0.5) * h) * nd_.pdf(lo + (i + 0.5) * h) for i in range(n)) * h
cases2 = [("N(0, 1) — BN 뒤", 0.0, 1.0), ("N(2, 1)", 2.0, 1.0), ("N(0, 3²)", 0.0, 3.0), ("N(2, 3²)", 2.0, 3.0)]
res2 = []
for nm, mu, sd in cases2:
    nd_ = NormalDist(mu, sd)
    frac = nd_.cdf(-4) + 1 - nd_.cdf(4)
    ed = expect(mu, sd, dsig)
    res2.append((nm, mu, sd, frac, ed))
    print("  [2] 입력 %s: |x|>4 비율 %.4f, 평균 σ'(x) %.4f (최댓값 0.25 의 %.0f%%)" % (nm, frac, ed, 100 * ed / 0.25))
print("      σ'(4) = %.4f" % dsig(4))
W, H = 820, 380
b = defs()
b += txt(20, 30, "시그모이드 입력의 분포에 따라 역으로 흐르는 기울기 σ'(x) 의 평균이 달라진다 (내가 계산한 것)", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 60, 460, 300, 70
def px(v):
    return PX0 + (v + 8) / 16.0 * (PX1 - PX0)
def py(v):
    return PY0 - v / 0.27 * (PY0 - PY1)
b += line(PX0, PY0, PX1, PY0, INK2, 1)
for t in (-8, -4, 0, 4, 8):
    b += txt(px(t), PY0 + 16, "%d" % t, 10, fill=MUTED)
for t in (-4, 4):
    b += '<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s" opacity="0.25"/>' % (
        PX0 if t < 0 else px(4), PY1, px(-4) - PX0, PY0 - PY1, NO)
b += polyline([(px(-8 + i * 0.1), py(dsig(-8 + i * 0.1))) for i in range(161)], INK, 2.4)
b += txt(px(0), py(0.25) - 8, "σ'(x), 최댓값 0.25", 12, weight="bold")
for (nm, mu, sd, frac, ed), colr in zip(res2, (S_BN, S_BASE, S_THIRD, NO)):
    nd_ = NormalDist(mu, sd)
    peak = nd_.pdf(mu)
    b += polyline([(px(-8 + i * 0.1), PY0 - 0.9 * (PY0 - PY1) * nd_.pdf(-8 + i * 0.1) / peak * (0.4 if sd > 2 else 0.8)) for i in range(161)], colr, 1.4, dash="4 3")
b += txt(px(-6), PY1 + 16, "포화 |x| > 4", 11, fill=NO)
b += txt(px(6), PY1 + 16, "σ'(4) = %.4f" % dsig(4), 11, fill=NO)
b += box(480, 60, 320, 250, fill=NODE, stroke=LINE)
b += txt(495, 84, "입력 분포", 12, anchor="start", weight="bold")
b += txt(640, 84, "|x|>4", 12, anchor="start", weight="bold")
b += txt(710, 84, "평균 σ'", 12, anchor="start", weight="bold")
for k, ((nm, mu, sd, frac, ed), colr) in enumerate(zip(res2, (S_BN, S_BASE, S_THIRD, NO))):
    y = 116 + 36 * k
    b += txt(495, y, nm, 12, anchor="start", fill=colr, weight="bold")
    b += txt(640, y, "%.4f" % frac, 12, anchor="start")
    b += txt(710, y, "%.4f" % ed, 12, anchor="start")
b += txt(495, 268, "점선 = 네 입력 분포의 모양(높이는 맞추지 않았다).", 11, anchor="start", fill=INK2)
b += txt(495, 288, "N(2, 3²) 이면 평균 σ' 가 N(0,1) 의 절반 아래다", 11, anchor="start", fill=INK2)
b += txt(410, 360, "논문 1절: 입력 x 의 많은 차원이 포화 영역으로 밀리면 u 로 내려가는 기울기가 사라지고, 깊을수록 커진다. 숫자는 이 논문에 없다", 11, fill=MUTED)
svg("fig02_saturation", W, H, b, "시그모이드 포화와 입력 분포")


# ── 그림 3. 정규화를 기울기 밖에서 하면 치우침이 끝없이 자란다 (논문 2절) ──────────────
xs3 = [0.5, -1.0, 2.0, 0.3, -0.8]
ts3 = [1.8, 0.2, 2.5, 1.0, 0.6]             # 목표의 평균이 0 이 아니다(=1.22)
eta3 = 0.05
def loss3(bias, xs):
    xx = [a + bias for a in xs]
    mu = sum(xx) / len(xx)
    return sum(((a - mu) - t) ** 2 for a, t in zip(xx, ts3)) / 2.0
naive_b, tr_b, naive_l = [0.0], [0.0], []
for _ in range(40):
    bb = naive_b[-1]
    xx = [a + bb for a in xs3]; mu = sum(xx) / len(xx)
    g = sum(((a - mu) - t) for a, t in zip(xx, ts3))     # E[x] 의 b 의존을 무시한 기울기
    naive_b.append(bb - eta3 * g)
    naive_l.append(loss3(bb, xs3))
    tr_b.append(tr_b[-1] - eta3 * 0.0)                   # 평균을 통과시키면 ∂ℓ/∂b = Σ ∂ℓ/∂x̂ · (1 − 1) = 0
print("  [3] 목표 평균 %.2f: 무시한 기울기로 40 걸음 → b %.3f (걸음마다 +%.4f), 손실 %.4f → %.4f (변화 %.1e)"
      % (sum(ts3) / 5, naive_b[-1], naive_b[1] - naive_b[0], naive_l[0], naive_l[-1], naive_l[-1] - naive_l[0]))
W, H = 820, 360
b = defs()
b += txt(20, 30, "논문 2절의 예를 숫자로 — 정규화의 b 의존을 기울기에서 빼면 b 는 자라고 손실은 그대로다 (값은 내가 고른 것)", 14, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 70, 470, 300, 70
def px(k):
    return PX0 + k / 40.0 * (PX1 - PX0)
def py(v):
    return PY0 - v / 12.0 * (PY0 - PY1)
b += line(PX0, PY0, PX1, PY0, INK2, 1); b += line(PX0, PY0, PX0, PY1, INK2, 1)
for t in (0, 4, 8, 12):
    b += txt(PX0 - 6, py(t) + 4, "%d" % t, 10, anchor="end", fill=MUTED)
for t in (0, 10, 20, 30, 40):
    b += txt(px(t), PY0 + 16, "%d" % t, 10, fill=MUTED)
b += txt((PX0 + PX1) / 2, PY0 + 36, "기울기 걸음", 12, fill=INK2)
b += polyline([(px(k), py(v)) for k, v in enumerate(naive_b)], NO, 2.4)
b += polyline([(px(k), py(v)) for k, v in enumerate(tr_b)], OK, 2.4)
b += polyline([(px(k), py(v)) for k, v in enumerate(naive_l)], INK2, 1.6, dash="5 3")
b += txt(px(38), py(naive_b[38]) - 10, "b (평균을 무시)", 12, anchor="end", fill=NO, weight="bold")
b += txt(px(38), py(0) - 8, "b (평균을 통과시킴) — 안 움직인다", 12, anchor="end", fill=OK, weight="bold")
b += txt(px(20), py(naive_l[20]) - 8, "손실 %.3f — 40 걸음 내내 같다" % naive_l[0], 11, fill=INK2)
b += box(500, 60, 300, 250, fill=NODE, stroke=LINE)
for j, l in enumerate(["x = u + b,  x̂ = x − E[x]",
                       "기울기가 E[x] 가 b 에 달린 것을 모르면",
                       "Δb ∝ −∂ℓ/∂x̂ 만큼 b 를 옮긴다.",
                       "그런데 b 가 옮긴 만큼 E[x] 도 옮겨",
                       "x̂ 는 그대로 — 손실도 그대로다.",
                       "",
                       "이 예: 걸음마다 b 가 +%.3f" % (naive_b[1] - naive_b[0]),
                       "40 걸음 뒤 b = %.2f" % naive_b[-1],
                       "",
                       "논문: 척도까지 맞추면 더 나빠지고,",
                       "초기 실험에서 모델이 터졌다"]):
    b += txt(515, 84 + 21 * j, l, 11, anchor="start", fill=INK if j < 5 else INK2)
svg("fig03_bias_blowup", W, H, b, "기울기 밖 정규화에서 치우침 발산")


# ── 그림 4. 전체 백색화 대신 차원별 정규화 — 비용과 특이 공분산 ───────────────────────
def rank(mat, tol=1e-9):
    a = [row[:] for row in mat]
    n, mcol = len(a), len(a[0])
    r = 0
    for c in range(mcol):
        piv = max(range(r, n), key=lambda i: abs(a[i][c])) if r < n else None
        if piv is None or abs(a[piv][c]) < tol:
            continue
        a[r], a[piv] = a[piv], a[r]
        for i in range(n):
            if i != r:
                f = a[i][c] / a[r][c]
                a[i] = [x - f * y for x, y in zip(a[i], a[r])]
        r += 1
        if r == n:
            break
    return r
d4, m4 = 100, 60
X4 = [[random.gauss(0, 1) for _ in range(d4)] for _ in range(m4)]
mu4 = [sum(X4[i][j] for i in range(m4)) / m4 for j in range(d4)]
C4 = [[sum((X4[i][p] - mu4[p]) * (X4[i][q] - mu4[q]) for i in range(m4)) / m4 for q in range(d4)] for p in range(d4)]
rk = rank(C4)
print("  [4] d=%d, m=%d: 공분산 성분 %s 개 대 차원별 통계 %d 개, 표본 공분산 계수 %d (m−1 = %d) → 역행렬이 없다"
      % (d4, m4, fmt(d4 * (d4 + 1) // 2), 2 * d4, rk, m4 - 1))
W, H = 820, 330
b = defs()
b += txt(20, 30, "전체 백색화 대신 차원마다 따로 — 논문 3절의 첫째 단순화 (d, m 은 논문 MNIST 실험의 값)", 15, anchor="start", weight="bold")
b += box(20, 50, 385, 250, fill=REV_SOFT, stroke=REV, sw=1.4)
b += txt(212, 76, "전체 백색화  Cov[x]^(−1/2) (x − E[x])", 13, weight="bold", fill=REV)
for j, l in enumerate(["통계: 공분산 d(d+1)/2 = %s 개" % fmt(d4 * (d4 + 1) // 2),
                       "역제곱근과 그 미분이 필요하다",
                       "",
                       "미니배치 m = %d 로 추정하면" % m4,
                       "표본 공분산의 계수가 %d (= m − 1)" % rk,
                       "d = %d 보다 작아 역행렬이 없다" % d4,
                       "(그림 코드가 소거법으로 센 계수)"]):
    b += txt(212, 110 + 24 * j, l, 12, fill=INK if j not in (4, 5) else NO)
b += box(415, 50, 385, 250, fill=FWD_SOFT, stroke=FWD, sw=1.4)
b += txt(607, 76, "차원별 정규화  (x⁽ᵏ⁾ − E[x⁽ᵏ⁾]) / √Var[x⁽ᵏ⁾]", 13, weight="bold", fill=FWD)
for j, l in enumerate(["통계: 평균과 분산 2d = %d 개" % (2 * d4),
                       "m ≥ 2 면 어느 차원이든 계산된다",
                       "",
                       "대신 차원 사이의 상관은 그대로 둔다",
                       "",
                       "LeCun 외(1998b): 상관을 안 없애도",
                       "이 정규화만으로 수렴이 빨라진다"]):
    b += txt(607, 110 + 24 * j, l, 12, fill=INK)
b += txt(410, 322, "논문: 「결합 공분산이면 미니배치가 백색화할 활성 수보다 작을 가능성이 커서 공분산이 특이해지고 정규화가 필요하다」", 11, fill=MUTED)
svg("fig04_whitening_vs_perdim", W, H, b, "전체 백색화와 차원별 정규화 비교")


# ── 그림 5. 알고리즘 1 을 손으로 ──────────────────────────────────────────────
x5 = [1.0, 2.0, 4.0, 9.0]
g5, b5, eps5 = 2.0, 0.5, 1e-5
mu5 = sum(x5) / 4
var5 = sum((a - mu5) ** 2 for a in x5) / 4
xh5 = [(a - mu5) / math.sqrt(var5 + eps5) for a in x5]
y5 = [g5 * a + b5 for a in xh5]
yid = [math.sqrt(var5 + eps5) * a + mu5 for a in xh5]
print("  [5] x=%s: μ=%.3f, σ²=%.4f, x̂=%s, y=%s (γ=2, β=0.5); γ=√(σ²+ε), β=μ 이면 y=%s"
      % (x5, mu5, var5, ["%.4f" % a for a in xh5], ["%.4f" % a for a in y5], ["%.4f" % a for a in yid]))
W, H = 820, 380
b = defs()
b += txt(20, 30, "알고리즘 1 을 손으로 — 미니배치 넷, γ = 2, β = 0.5, ε = 10⁻⁵ (값은 내가 고른 것)", 15, anchor="start", weight="bold")
cols5 = ["xᵢ", "xᵢ − μ", "x̂ᵢ", "yᵢ = γx̂ᵢ + β", "γ=√(σ²+ε), β=μ 이면"]
cw = [120, 140, 150, 180, 190]
x0, y0 = 20, 60
b += box(x0, y0, sum(cw), 34, fill="#DDE3E0", stroke=LINE, rx=4)
for k, t in enumerate(cols5):
    b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y0 + 22, t, 12, weight="bold")
for r in range(4):
    y = y0 + 34 + 36 * r
    b += box(x0, y, sum(cw), 36, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    vals = ["%.0f" % x5[r], "%+.0f" % (x5[r] - mu5), "%+.4f" % xh5[r], "%+.4f" % y5[r], "%.4f" % yid[r]]
    for k, t in enumerate(vals):
        b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y + 23, t, 12, fill=OK if k == 4 else INK)
yb = y0 + 34 + 36 * 4 + 20
steps5 = ["1. μ_B = (1 + 2 + 4 + 9) / 4 = %.1f" % mu5,
          "2. σ²_B = (9 + 4 + 0 + 25) / 4 = %.2f   (m 으로 나눈다 — 추론에서는 m/(m−1) 로 고친다, 그림 7)" % var5,
          "3. x̂ = (x − μ) / √(σ² + ε):  합 %.1e, 제곱 평균 %.6f — 평균 0, 분산 1 (ε 만큼 1 에 못 미친다)" % (sum(xh5), sum(a * a for a in xh5) / 4),
          "4. y = γx̂ + β:  평균 %.2f (= β), 표준편차 %.4f (≈ γ) — 다음 층이 받는 값" % (sum(y5) / 4, mstd(y5)[1]),
          "오른쪽 끝 열: γ, β 를 그렇게 두면 원래 x 로 돌아온다 — 논문이 말하는 「항등 변환도 나타낼 수 있다」"]
for j, l in enumerate(steps5):
    b += txt(30, yb + 22 * j, l, 12, anchor="start", fill=OK if j == 4 else INK)
svg("fig05_algorithm1", W, H, b, "알고리즘 1 손계산")


# ── 그림 6. 역전파 식 — 논문의 연쇄 법칙과 유한 차분 ────────────────────────────────
gy6 = [0.3, -1.2, 0.5, 0.8]           # ∂ℓ/∂yᵢ (ℓ = Σ gᵢ yᵢ 로 둔다)
def fwd(xs, gam=g5, bet=b5):
    m = sum(xs) / len(xs)
    v = sum((a - m) ** 2 for a in xs) / len(xs)
    return [gam * (a - m) / math.sqrt(v + eps5) + bet for a in xs]
def loss6(xs, gam=g5, bet=b5):
    return sum(g * y for g, y in zip(gy6, fwd(xs, gam, bet)))
m6 = len(x5)
dxh = [g * g5 for g in gy6]
dvar = sum(d * (a - mu5) for d, a in zip(dxh, x5)) * -0.5 * (var5 + eps5) ** -1.5
dmu = sum(d * -1 / math.sqrt(var5 + eps5) for d in dxh)
dx = [d / math.sqrt(var5 + eps5) + dvar * 2 * (a - mu5) / m6 + dmu / m6 for d, a in zip(dxh, x5)]
dgam = sum(g * a for g, a in zip(gy6, xh5))
dbet = sum(gy6)
hh = 1e-6
num = []
for i in range(4):
    xp = x5[:]; xm = x5[:]
    xp[i] += hh; xm[i] -= hh
    num.append((loss6(xp) - loss6(xm)) / (2 * hh))
ngam = (loss6(x5, g5 + hh) - loss6(x5, g5 - hh)) / (2 * hh)
nbet = (loss6(x5, g5, b5 + hh) - loss6(x5, g5, b5 - hh)) / (2 * hh)
err6 = max(abs(a - c) for a, c in zip(dx + [dgam, dbet], num + [ngam, nbet]))
print("  [6] ∂ℓ/∂x 식 %s / 유한 차분 %s, ∂ℓ/∂γ %.5f/%.5f, ∂ℓ/∂β %.5f/%.5f, 최대 차이 %.1e"
      % (["%.5f" % a for a in dx], ["%.5f" % a for a in num], dgam, ngam, dbet, nbet, err6))
print("      Σ ∂ℓ/∂xᵢ = %.2e,  Σ ∂ℓ/∂xᵢ · x̂ᵢ = %.2e" % (sum(dx), sum(a * c for a, c in zip(dx, xh5))))
W, H = 820, 400
b = defs()
b += txt(20, 30, "논문 3절의 역전파 식 여섯을 그림 5 의 미니배치에 — 식과 유한 차분이 맞는가 (∂ℓ/∂y 는 내가 고른 값)", 14, anchor="start", weight="bold")
cw = [170, 150, 150, 150, 150]
x0, y0 = 20, 55
heads = ["", "i = 1", "i = 2", "i = 3", "i = 4"]
rows6 = [("∂ℓ/∂yᵢ (주어짐)", ["%+.2f" % a for a in gy6], INK),
         ("∂ℓ/∂x̂ᵢ = ∂ℓ/∂yᵢ · γ", ["%+.2f" % a for a in dxh], INK),
         ("∂ℓ/∂xᵢ — 논문 식", ["%+.5f" % a for a in dx], S_BN),
         ("∂ℓ/∂xᵢ — 유한 차분", ["%+.5f" % a for a in num], S_BASE)]
b += box(x0, y0, sum(cw), 32, fill="#DDE3E0", stroke=LINE, rx=4)
for k, t in enumerate(heads):
    b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y0 + 21, t, 12, weight="bold")
for r, (nm, vals, colr) in enumerate(rows6):
    y = y0 + 32 + 34 * r
    b += box(x0, y, sum(cw), 34, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    b += txt(x0 + 10, y + 22, nm, 12, anchor="start", weight="bold", fill=colr)
    for k, t in enumerate(vals):
        b += txt(x0 + sum(cw[:k + 1]) + cw[k + 1] / 2, y + 22, t, 12, fill=colr)
yb = y0 + 32 + 34 * 4 + 26
for j, l in enumerate(["∂ℓ/∂σ²_B = %.5f,  ∂ℓ/∂μ_B = %.5f   (중간 값)" % (dvar, dmu),
                       "∂ℓ/∂γ = Σ ∂ℓ/∂yᵢ · x̂ᵢ = %.5f (유한 차분 %.5f),  ∂ℓ/∂β = Σ ∂ℓ/∂yᵢ = %.2f (유한 차분 %.5f)" % (dgam, ngam, dbet, nbet),
                       "식과 유한 차분의 최대 차이 %.1e — 여섯 식이 맞다" % err6,
                       "",
                       "눈여겨볼 것: Σ ∂ℓ/∂xᵢ = %.1e,  Σ ∂ℓ/∂xᵢ · x̂ᵢ = %.1e" % (sum(dx), sum(a * c for a, c in zip(dx, xh5))),
                       "→ x 로 가는 기울기에는 미니배치 전체를 한꺼번에 옮기는 성분이 없고, 한꺼번에 늘이는 성분은 ε 때문에 10⁻⁶ 만큼만 남는다.",
                       "   정규화가 어차피 지울 방향으로는 기울기가 가지 않는다 — 그림 3 의 발산을 막는 것이 이것이다 (내가 붙인 읽기)"]):
    b += txt(30, yb + 22 * j, l, 12, anchor="start", fill=OK if j == 2 else (INK2 if j > 3 else INK))
svg("fig06_backward_check", W, H, b, "역전파 식과 유한 차분 비교")


# ── 그림 7. 추론 — 모집단 통계와 m/(m−1) ─────────────────────────────────────────
popm, pops = 3.0, 2.0
res7 = []
for m7 in (2, 4, 32, 60):
    K = 4000
    vs, ms = [], []
    for _ in range(K):
        bt = [random.gauss(popm, pops) for _ in range(m7)]
        mm, ss = mstd(bt)
        ms.append(mm); vs.append(ss * ss)
    ev = sum(vs) / K
    res7.append((m7, sum(ms) / K, ev, ev * m7 / (m7 - 1.0)))
    print("  [7] m=%d: E_B[μ_B]=%.3f, E_B[σ²_B]=%.3f (참 분산 4 의 %.0f%%), × m/(m−1) = %.3f"
          % (m7, sum(ms) / K, ev, 100 * ev / 4, ev * m7 / (m7 - 1.0)))
gam7, bet7 = 1.5, 0.5
a7 = gam7 / math.sqrt(4 + eps5)
c7 = bet7 - gam7 * popm / math.sqrt(4 + eps5)
print("      합친 선형 변환 (γ=1.5, β=0.5, E=3, Var=4): y = %.4f·x + (%.4f)" % (a7, c7))
W, H = 820, 380
b = defs()
b += txt(20, 30, "추론은 모집단 통계로 — 분산은 m/(m−1) 로 고친다 (모집단 N(3, 2²), 미니배치 4,000 개씩, 내가 계산)", 14, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 80, 470, 300, 70
def py(v):
    return PY0 - v / 4.6 * (PY0 - PY1)
b += line(PX0, PY0, PX1, PY0, INK2, 1)
for t in (0, 1, 2, 3, 4):
    b += line(PX0, py(t), PX1, py(t), LINE, 1)
    b += txt(PX0 - 6, py(t) + 4, "%d" % t, 10, anchor="end", fill=MUTED)
b += line(PX0, py(4), PX1, py(4), OK, 1.4, dash="5 3")
b += txt(PX0 + 4, py(4) + 14, "참 분산 4", 11, anchor="start", fill=OK)
for k, (m7, em, ev, cv) in enumerate(res7):
    x = PX0 + 30 + 95 * k
    b += '<rect x="%d" y="%.1f" width="28" height="%.1f" fill="%s"/>' % (x, py(ev), PY0 - py(ev), S_BASE)
    b += '<rect x="%d" y="%.1f" width="28" height="%.1f" fill="%s"/>' % (x + 32, py(cv), PY0 - py(cv), S_BN)
    b += txt(x + 30, PY0 + 16, "m = %d" % m7, 11)
    b += txt(x + 14, py(ev) - 4, "%.2f" % ev, 9, fill=S_BASE)
    b += txt(x + 46, py(cv) - 4, "%.2f" % cv, 9, fill=S_BN)
b += '<rect x="%d" y="332" width="12" height="12" fill="%s"/>' % (90, S_BASE)
b += txt(108, 343, "E_B[σ²_B] (m 으로 나눈 미니배치 분산의 평균)", 11, anchor="start")
b += '<rect x="%d" y="352" width="12" height="12" fill="%s"/>' % (90, S_BN)
b += txt(108, 363, "× m/(m−1) — 알고리즘 2 의 10 행", 11, anchor="start")
b += box(500, 60, 300, 260, fill=NODE, stroke=LINE)
for j, l in enumerate(["m = 2 이면 미니배치 분산이 참 분산의",
                       "%.0f%% 다. m = 60 이면 %.0f%%." % (100 * res7[0][2] / 4, 100 * res7[3][2] / 4),
                       "",
                       "알고리즘 2 의 11 행: 통계를 얼리면",
                       "BN 은 선형 변환 하나로 합쳐진다.",
                       "y = γ/√(Var+ε) · x + (β − γE/√(Var+ε))",
                       "",
                       "예: γ=1.5, β=0.5, E=3, Var=4 이면",
                       "y = %.4f · x %+.4f" % (a7, c7),
                       "",
                       "앞의 합성곱 가중치에 곱해 넣을 수 있어",
                       "추론 비용이 사실상 0 이 된다 (내 읽기)"]):
    b += txt(515, 84 + 20 * j, l, 11, anchor="start", fill=INK if j < 9 else INK2)
svg("fig07_inference", W, H, b, "추론용 모집단 통계와 분산 보정")


# ── 그림 8. 같은 예시도 미니배치에 따라 다른 값 — 정규화가 곧 잡음 ─────────────────────
bA = [2.0, 1.0, 4.0, 9.0]
bB = [2.0, 2.5, 3.0, 1.5]
bC = [2.0, 0.0, 0.5, 1.0]
outs8 = []
for nm, bt in (("미니배치 A", bA), ("미니배치 B", bB), ("미니배치 C", bC)):
    outs8.append((nm, bt, bn(bt)[0]))
    print("  [8] x=2 가 %s %s 안에 있으면 x̂ = %.4f" % (nm, bt, bn(bt)[0]))
W, H = 820, 300
b = defs()
b += txt(20, 30, "같은 예시 x = 2 가 어느 미니배치에 들어가느냐에 따라 다른 값으로 정규화된다 (값은 내가 고른 것)", 15, anchor="start", weight="bold")
for k, (nm, bt, v) in enumerate(outs8):
    y = 70 + 60 * k
    b += txt(30, y + 5, nm, 13, anchor="start", weight="bold")
    for j, a in enumerate(bt):
        b += box(140 + 50 * j, y - 16, 44, 30, fill=CODE_SOFT if j == 0 else NODE, stroke=CODE if j == 0 else LINE)
        b += txt(162 + 50 * j, y + 4, "%g" % a, 12, weight="bold" if j == 0 else None)
    b += line(345, y, 395, y, INK2, 1.4, marker="ai")
    b += txt(405, y + 5, "x̂ = %+.3f" % v, 14, anchor="start", weight="bold", fill=S_BN)
b += box(560, 50, 240, 190, fill=NODE, stroke=LINE)
for j, l in enumerate(["논문 4.2.1: 한 예시의 활성이", "같은 미니배치에 무작위로 뽑힌", "다른 예시들에 영향을 받으므로", "드롭아웃과 비슷한 정규화 효과를", "낼 것이라고 추측한다(conjecture).", "", "섞기를 철저히 해 같은 예시끼리", "늘 같이 묶이지 않게 하자 검증", "정확도가 약 1% 올랐다고 적는다"]):
    b += txt(575, 74 + 19 * j, l, 11, anchor="start", fill=INK if j < 5 else INK2)
b += txt(410, 282, "그래서 학습 중의 BN 출력은 입력 하나만의 함수가 아니다 — 추론에서 모집단 통계로 바꾸는 이유가 이것이다(그림 7)", 11, fill=MUTED)
svg("fig08_batch_dependence", W, H, b, "미니배치에 따른 정규화 값 차이")


# ── 그림 9. 합성곱 층의 BN — 특징 지도마다 하나 ─────────────────────────────────────
m9 = 32
rows9 = []
for p in (56, 28, 14, 7):
    rows9.append((p, m9 * p * p))
C9, p9 = 64, 28
print("  [9] m=%d 에서 유효 미니배치 m'=m·p·q: %s" % (m9, ", ".join("%dx%d → %s" % (p, p, fmt(v)) for p, v in rows9)))
print("      C=%d, %dx%d 에서 γ,β 수: 특징 지도마다 %d 개 대 활성마다 %s 개" % (C9, p9, p9, 2 * C9, fmt(2 * C9 * p9 * p9)))
W, H = 820, 360
b = defs()
b += txt(20, 30, "합성곱 층에서는 한 특징 지도의 모든 자리를 한 묶음으로 — 유효 미니배치 m' = m · p · q (논문 3.2절)", 15, anchor="start", weight="bold")
for k in range(4):
    x, y = 60 + 18 * k, 64 + 14 * k
    b += box(x, y, 130, 130, fill=CODE_SOFT if k == 3 else NODE, stroke=CODE if k == 3 else INK2, rx=2)
b += txt(190, 290, "미니배치 m 장 × 한 특징 지도(p × q)", 12, weight="bold")
b += txt(190, 308, "이 모두가 알고리즘 1 의 B 하나", 12, fill=CODE)
b += txt(190, 326, "γ⁽ᵏ⁾, β⁽ᵏ⁾ 도 특징 지도 k 마다 한 쌍", 12, fill=INK2)
b += box(380, 60, 420, 150, fill=NODE, stroke=LINE)
b += txt(395, 84, "m = %d (논문 ImageNet 실험의 미니배치)" % m9, 12, anchor="start", weight="bold")
for j, (p, v) in enumerate(rows9):
    b += txt(395, 110 + 22 * j, "특징 지도 %d × %d  →  m' = %s" % (p, p, fmt(v)), 12, anchor="start")
b += box(380, 220, 420, 110, fill=NODE, stroke=LINE)
b += txt(395, 244, "학습되는 γ, β 의 수 (C = %d 지도, %d × %d)" % (C9, p9, p9), 12, anchor="start", weight="bold")
b += txt(395, 268, "특징 지도마다:  2 × %d = %d 개" % (C9, 2 * C9), 12, anchor="start", fill=OK)
b += txt(395, 290, "활성마다였다면:  2 × %d × %d × %d = %s 개" % (C9, p9, p9, fmt(2 * C9 * p9 * p9)), 12, anchor="start", fill=NO)
b += txt(395, 314, "같은 지도의 다른 자리를 같은 방식으로 정규화 — 합성곱의 성질", 11, anchor="start", fill=INK2)
svg("fig09_conv_bn", W, H, b, "합성곱 층 BN 의 유효 미니배치")


# ── 그림 10. 척도 불변 — BN(Wu) = BN((aW)u), 기울기는 1/a ───────────────────────────
U10 = [[0.2, -1.0, 0.5], [1.1, 0.3, -0.4], [-0.6, 0.8, 1.2], [0.9, -0.2, 0.1]]
W10 = [0.7, -0.3, 0.5]
def bnlin(Wv, gam=1.0, bet=0.0):
    xs = [sum(w * u_ for w, u_ in zip(Wv, row)) for row in U10]
    return [gam * a + bet for a in bn(xs, eps=0.0)]
def l10(Wv):
    return sum(g * y for g, y in zip(gy6, bnlin(Wv)))
def gradW(Wv):
    out = []
    for j in range(3):
        wp = Wv[:]; wm = Wv[:]
        wp[j] += 1e-6; wm[j] -= 1e-6
        out.append((l10(wp) - l10(wm)) / 2e-6)
    return out
a10 = 10.0
y1 = bnlin(W10); y10 = bnlin([a10 * w for w in W10])
g1 = gradW(W10); g10 = gradW([a10 * w for w in W10])
print("  [10] BN(Wu) %s / BN(10·W u) %s,  ∂ℓ/∂W %s / ∂ℓ/∂(10W) %s (비 %s)"
      % (["%.4f" % a for a in y1], ["%.4f" % a for a in y10], ["%.4f" % a for a in g1], ["%.4f" % a for a in g10],
         ["%.3f" % (c / a) for a, c in zip(g1, g10)]))
W, H = 820, 330
b = defs()
b += txt(20, 30, "가중치를 a 배 해도 BN 출력은 같고, 그 가중치의 기울기는 1/a 배 (논문 3.3절, 수는 내가 고른 예, a = 10)", 15, anchor="start", weight="bold")
cw = [220, 140, 140, 140, 140]
x0, y0 = 20, 60
heads = ["", "1", "2", "3", "4"]
b += box(x0, y0, sum(cw), 32, fill="#DDE3E0", stroke=LINE, rx=4)
for k, t in enumerate(heads):
    b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y0 + 21, ("예시 " + t) if t else "", 12, weight="bold")
for r, (nm, vals, colr) in enumerate([("BN(Wu)", y1, S_BASE), ("BN((10W)u)", y10, S_BN)]):
    y = y0 + 32 + 34 * r
    b += box(x0, y, sum(cw), 34, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    b += txt(x0 + 10, y + 22, nm, 12, anchor="start", weight="bold", fill=colr)
    for k, t in enumerate(vals):
        b += txt(x0 + sum(cw[:k + 1]) + cw[k + 1] / 2, y + 22, "%+.4f" % t, 12, fill=colr)
y = y0 + 32 + 34 * 2 + 30
b += txt(30, y, "가중치 기울기 (유한 차분, 가중치 셋):", 12, anchor="start", weight="bold")
b += txt(30, y + 24, "∂ℓ/∂W = (%s)" % ", ".join("%+.4f" % a for a in g1), 12, anchor="start", fill=S_BASE)
b += txt(30, y + 46, "∂ℓ/∂(10W) = (%s)  — 정확히 1/10" % ", ".join("%+.4f" % a for a in g10), 12, anchor="start", fill=S_BN)
b += txt(30, y + 78, "논문의 읽기: 학습률이 커서 가중치가 자라면 그 기울기가 줄어 성장이 스스로 잦아든다. 그리고 u 로 가는 야코비안은 척도와 무관하다", 12, anchor="start", fill=INK2)
b += txt(30, y + 100, "이 예는 ε = 0 으로 계산했다. ε 이 있으면 척도가 아주 작을 때 등식이 조금 어긋난다", 11, anchor="start", fill=MUTED)
svg("fig10_scale_invariance", W, H, b, "BN 의 가중치 척도 불변")


# ── 그림 11. 어디에 넣는가 — 비선형 앞, 치우침은 뺀다 ────────────────────────────────
W, H = 820, 330
b = defs()
b += txt(20, 30, "BN 을 넣는 자리 — z = g(Wu + b) 를 z = g(BN(Wu)) 로 (논문 3.2절)", 15, anchor="start", weight="bold")
def chain(b, y, items, note, colr):
    x = 40
    for k, (t, f, s) in enumerate(items):
        w = 18 + 12 * len(t)
        b += box(x, y - 22, w, 44, fill=f, stroke=s, sw=1.5)
        b += txt(x + w / 2, y + 5, t, 13, weight="bold")
        if k < len(items) - 1:
            b += line(x + w + 2, y, x + w + 30, y, INK2, 1.4, marker="ai")
        x += w + 32
    b += txt(x, y + 5, note, 12, anchor="start", fill=colr)
    return b
b = chain(b, 90, [("u", NODE, INK2), ("W u + b", FWD_SOFT, FWD), ("g(·)", NODE, INK2), ("z", NODE, INK2)], "원래 층", INK2)
b = chain(b, 170, [("u", NODE, INK2), ("W u", FWD_SOFT, FWD), ("BN: γ, β", CODE_SOFT, CODE), ("g(·)", NODE, INK2), ("z", NODE, INK2)], "BN 층 — b 는 β 가 맡는다", OK)
b += box(40, 220, 760, 90, fill=NODE, stroke=LINE)
for j, l in enumerate(["왜 u 가 아니라 Wu 인가 — u 는 앞 비선형의 출력이라 분포 모양이 학습 중에 바뀌기 쉬워 1 · 2차 적률만 맞춰서는 이동을 못 없앤다.",
                       "Wu + b 는 대칭이고 희소하지 않은, 「더 가우스 같은」 분포일 가능성이 크다(논문의 말).",
                       "b 를 빼는 이유 — 평균을 빼는 순간 b 의 효과가 지워진다. 작은 예: b = 3 을 더해도 μ_B 도 3 커져 x̂ 는 그대로다."]):
    b += txt(55, 244 + 24 * j, l, 11, anchor="start")
svg("fig11_placement", W, H, b, "BN 삽입 위치")


# ── 그림 12. MNIST 실험 (논문 그림 1) — 300 dpi 로 읽은 값 ──────────────────────────
W, H = 820, 390
b = defs()
b += txt(20, 30, "논문 그림 1 — MNIST, 시그모이드 은닉 100 × 3 층, 미니배치 60, 50,000 걸음 (눈금을 읽은 값)", 15, anchor="start", weight="bold")
acc = [("5K", 0.91, 0.965), ("10K", 0.93, 0.97), ("20K", 0.96, 0.975), ("50K", 0.97, 0.98)]
b += box(20, 50, 300, 300, fill="none", stroke=LINE)
b += txt(170, 72, "(a) 시험 정확도 (읽기 ±0.01)", 12, weight="bold")
b += txt(80, 100, "걸음", 11, weight="bold"); b += txt(170, 100, "BN 없음", 11, weight="bold", fill=S_BASE); b += txt(260, 100, "BN 있음", 11, weight="bold", fill=S_BN)
for j, (s, a, c) in enumerate(acc):
    y = 130 + 30 * j
    b += txt(80, y, s, 12); b += txt(170, y, "%.2f" % a, 12, fill=S_BASE); b += txt(260, y, "%.3f" % c, 12, fill=S_BN)
b += txt(170, 270, "첫 점: BN 없음 약 0.70,", 11, fill=INK2)
b += txt(170, 288, "BN 있음 약 0.95", 11, fill=INK2)
b += txt(170, 318, "끝의 차이는 0.01 — 읽기 오차 폭", 11, fill=NO)
def pctpanel(b, x0, title, series, colr):
    b += box(x0, 50, 235, 300, fill="none", stroke=LINE)
    b += txt(x0 + 117, 72, title, 12, weight="bold", fill=colr)
    b += txt(x0 + 60, 100, "백분위", 11, weight="bold"); b += txt(x0 + 130, 100, "처음", 11, weight="bold"); b += txt(x0 + 190, 100, "끝", 11, weight="bold")
    for j, (q, s0, s1) in enumerate(series):
        y = 130 + 30 * j
        b += txt(x0 + 60, y, q, 12); b += txt(x0 + 130, y, "%+.1f" % s0, 12); b += txt(x0 + 190, y, "%+.1f" % s1, 12)
    return b
b = pctpanel(b, 330, "(b) BN 없음: 시그모이드 입력", [("85%", 0.8, 1.7), ("50%", 0.8, 0.0), ("15%", 0.8, -1.8)], S_BASE)
b = pctpanel(b, 575, "(c) BN 있음: 시그모이드 입력", [("85%", 1.4, 2.0), ("50%", 0.0, 0.0), ("15%", -1.1, -1.9)], S_BN)
b += txt(447, 250, "초반 요동: 85% 가 약 2.0 까지", 11, fill=INK2)
b += txt(447, 268, "치솟았다 0.9 로 떨어진 뒤 오른다", 11, fill=INK2)
b += txt(692, 250, "중앙값은 0 에 붙어 있다.", 11, fill=INK2)
b += txt(692, 268, "85−15 폭은 2.5 → 3.9 로 넓어진다", 11, fill=NO)
b += txt(447, 300, "(b)(c) 는 가로축 눈금이 없다 — 읽기 ±0.2", 11, fill=MUTED)
b += txt(410, 376, "(c) 의 값은 γ, β 를 거친 뒤의 시그모이드 입력이다. 평균은 고정되지만 폭은 학습 중에 바뀐다 — 「분포가 더 안정적」은 이 두 줄의 비교다", 11, fill=MUTED)
svg("fig12_mnist", W, H, b, "논문 그림 1 의 눈금 읽기")


# ── 그림 13. ImageNet — 72.2% 까지의 걸음 수 (논문 그림 3 의 표) ───────────────────────
tbl = [("Inception", 31.0, 72.2, 0.0015, S_BASE),
       ("BN-Baseline", 13.3, 72.7, 0.0015, S_THIRD),
       ("BN-x5", 2.1, 73.0, 0.0075, S_BN),
       ("BN-x30", 2.7, 74.8, 0.045, NO),
       ("BN-x5-Sigmoid", None, 69.8, 0.0075, CODE)]
print("  [13] 72.2% 까지 걸음 배수:", ", ".join("%s %.2f 배(%.1f%%)" % (n, 31.0 / s, 100 * s / 31.0) for n, s, *_ in tbl if s))
print("       BN-x30 이 74.8%% 에 닿은 6·10⁶ 걸음은 Inception 31·10⁶ 의 1/%.2f" % (31.0 / 6))
W, H = 820, 400
b = defs()
b += txt(20, 30, "논문 그림 3 의 표 — Inception 의 최고 정확도 72.2% 에 닿기까지의 걸음 수 (배수는 내가 나눈 값)", 15, anchor="start", weight="bold")
X0, X1 = 180, 560
def bx(v):
    return X0 + v / 32.0 * (X1 - X0)
for t in (0, 10, 20, 30):
    b += line(bx(t), 60, bx(t), 300, LINE, 1)
    b += txt(bx(t), 316, "%d M" % t, 10, fill=MUTED)
for k, (nm, st, mx, lr, colr) in enumerate(tbl):
    y = 80 + 46 * k
    b += txt(170, y + 5, nm, 12, anchor="end", weight="bold", fill=colr)
    if st:
        b += '<rect x="%d" y="%d" width="%.1f" height="22" rx="3" fill="%s"/>' % (X0, y - 11, bx(st) - X0, colr)
        if nm == "Inception":
            b += txt(bx(st) - 6, y + 5, "31.0 M (기준)", 11, anchor="end", fill="#FFFFFF", weight="bold")
        else:
            b += txt(bx(st) + 6, y + 5, "%.1f M  (%.1f 배)" % (st, 31.0 / st), 11, anchor="start")
    else:
        b += txt(X0 + 6, y + 5, "72.2% 에 닿지 못함", 11, anchor="start", fill=NO)
b += box(590, 60, 210, 250, fill=NODE, stroke=LINE)
b += txt(605, 82, "최고 정확도 · 첫 학습률", 12, anchor="start", weight="bold")
for k, (nm, st, mx, lr, colr) in enumerate(tbl):
    b += txt(605, 110 + 30 * k, "%s" % nm, 11, anchor="start", fill=colr, weight="bold")
    b += txt(785, 110 + 30 * k, "%.1f%% · %g" % (mx, lr), 11, anchor="end")
b += txt(605, 268, "BN 없는 Inception 을 시그모이드로", 10, anchor="start", fill=INK2)
b += txt(605, 284, "배우면 1/1000(우연 수준)에 머문다", 10, anchor="start", fill=INK2)
b += txt(410, 344, "「14 배」는 31.0 / 2.1 = %.1f. 「7%% 의 걸음」은 2.1 / 31.0 = %.1f%%. BN 만 넣은 것(BN-Baseline)은 %.2f 배다" % (31.0 / 2.1, 100 * 2.1 / 31.0, 31.0 / 13.3), 12, fill=INK)
b += txt(410, 366, "BN-x5 · BN-x30 은 BN 에 일곱 가지 변경을 더한 것이다(그림 14) — 14 배는 BN 하나의 몫이 아니다", 12, fill=NO)
b += txt(410, 388, "BN-x30 은 처음엔 BN-x5 보다 느리지만 더 높이 간다 — 논문: 「직관에 어긋나고 더 조사해야 한다」", 11, fill=MUTED)
svg("fig13_imagenet_steps", W, H, b, "ImageNet 걸음 수 비교")


# ── 그림 14. BN-x5 에 함께 들어간 일곱 가지 ──────────────────────────────────────
mods = [("학습률 올리기", "×5 (BN-x5), ×30 (BN-x30)", "그림 3 의 표로 BN-x5 대 BN-Baseline"),
        ("드롭아웃 빼기", "40% → 0", "「검증 정확도가 더 높았다」 — 수치 없음"),
        ("더 철저히 섞기", "샤드 안에서 섞기", "「약 1% 향상」 — 표 없음"),
        ("L2 가중치 벌점 줄이기", "1/5 로", "「검증 정확도가 좋아졌다」 — 수치 없음"),
        ("학습률 감쇠 빠르게", "6 배 빠르게", "따로 재지 않음"),
        ("LRN 빼기", "국소 응답 정규화 제거", "「필요 없었다」 — 수치 없음"),
        ("사진 왜곡 줄이기", "밝기·색 왜곡을 덜", "따로 재지 않음")]
W, H = 820, 400
b = defs()
b += txt(20, 30, "논문 4.2.1 — BN-x5 · BN-x30 은 BN 에 일곱 가지를 함께 바꾼 모델이다. 하나씩 뺀 표는 없다", 15, anchor="start", weight="bold")
cw = [200, 220, 360]
x0, y0 = 20, 55
b += box(x0, y0, sum(cw), 32, fill="#DDE3E0", stroke=LINE, rx=4)
for k, t in enumerate(["바꾼 것", "얼마나", "논문이 보인 근거"]):
    b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y0 + 21, t, 12, weight="bold")
for r, row in enumerate(mods):
    y = y0 + 32 + 36 * r
    b += box(x0, y, sum(cw), 36, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    for k, t in enumerate(row):
        colr = INK if k < 2 else (OK if "표로" in t else (NO if "없" in t else INK2))
        b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y + 23, t, 12, weight="bold" if k == 0 else None, fill=colr)
b += txt(410, 372, "초록의 「14 배 적은 걸음」과 「드롭아웃이 필요 없어질 때가 있다」는 이 묶음 전체의 결과다. 어느 줄이 얼마를 냈는지는 이 논문에서 가를 수 없다", 11, fill=INK2)
b += txt(410, 392, "색: 초록 = 표로 확인 가능, 빨강 = 문장만 있다, 회색 = 따로 재지 않았다 (내가 가른 것)", 11, fill=MUTED)
svg("fig14_modifications", W, H, b, "BN-x5 에 함께 들어간 변경 목록")


# ── 그림 15. 논문 그림 4 의 표 — ImageNet top-5 오차 ──────────────────────────────
tb15 = [("GoogLeNet 앙상블", "224", "144", "7", 6.67, "검증"),
        ("Deep Image 저해상도", "256", "-", "1", 7.96, "검증"),
        ("Deep Image 고해상도", "512", "-", "1", 7.42, "검증"),
        ("Deep Image 앙상블", "≤512", "-", "-", 5.98, "검증"),
        ("MSRA 다중 자르기", "≤480", "-", "-", 5.71, "검증"),
        ("MSRA 앙상블", "≤480", "-", "-", 4.94, "시험 서버"),
        ("BN-Inception 한 번 자르기", "224", "1", "1", 7.82, "검증"),
        ("BN-Inception 다중 자르기", "224", "144", "1", 5.82, "검증"),
        ("BN-Inception 앙상블", "224", "144", "6", 4.82, "시험 서버")]
print("  [15] BN 앙상블 4.82 대 MSRA 앙상블 4.94: 차이 %.2f 백분율 점 (둘 다 시험 서버)" % (4.94 - 4.82))
W, H = 820, 450
b = defs()
b += txt(20, 30, "논문 그림 4 — ImageNet top-5 오차. 해상도 · 자르기 · 모델 수가 줄마다 다르다", 15, anchor="start", weight="bold")
X0, X1 = 430, 790
def ex(v):
    return X0 + (v - 4.5) / 4.0 * (X1 - X0)
for t in (5, 6, 7, 8):
    b += line(ex(t), 55, ex(t), 380, LINE, 1)
    b += txt(ex(t), 396, "%d%%" % t, 10, fill=MUTED)
b += txt(30, 62, "모델", 11, anchor="start", weight="bold"); b += txt(230, 62, "해상도", 11, weight="bold")
b += txt(290, 62, "자르기", 11, weight="bold"); b += txt(345, 62, "모델 수", 11, weight="bold"); b += txt(400, 62, "평가", 11, weight="bold")
for k, (nm, res, cr, mdl, e, ev) in enumerate(tb15):
    y = 90 + 33 * k
    colr = S_BN if nm.startswith("BN") else S_BASE
    b += txt(30, y + 4, nm, 11, anchor="start", fill=colr, weight="bold" if nm.startswith("BN") else None)
    b += txt(230, y + 4, res, 11); b += txt(290, y + 4, cr, 11); b += txt(345, y + 4, mdl, 11)
    b += txt(400, y + 4, ev, 10, fill=NO if ev != "검증" else INK2)
    b += circ(ex(e), y, 6, colr if ev == "검증" else BG, colr, 2)
    b += txt(ex(e) + 10, y + 4, "%.2f" % e, 10, anchor="start")
b += txt(410, 420, "속 빈 점 = 시험 서버 값. BN 앙상블은 검증 50,000 장에서 4.9%% 라고 캡션이 적는다. 4.82 대 4.94 는 %.2f 백분율 점 차이, 변동 폭은 없다" % (4.94 - 4.82), 11, fill=INK2)
b += txt(410, 440, "top-1: BN-Inception 한 번 자르기 25.2%, 다중 자르기 21.99%, 앙상블 20.1% — 다른 줄은 top-1 이 대부분 비어 있다", 11, fill=MUTED)
svg("fig15_ensemble", W, H, b, "ImageNet top-5 오차 표")


# ── 그림 16. 계보 ────────────────────────────────────────────────────────────
W, H = 820, 400
b = defs()
b += txt(20, 30, "계보 — 앞 편의 한계를 받아 다음 편에 넘긴다", 15, anchor="start", weight="bold")
chainL = [("LeCun 외 1998", "입력을 백색화하면 빠르다", NODE, INK2),
          ("AlexNet 2012 (읽음)", "LRN · 드롭아웃 · ReLU", FWD_SOFT, FWD),
          ("BN 2015", "층 입력을 미니배치로 정규화", CODE_SOFT, CODE),
          ("ResNet 2015", "잔차 연결 + 층마다 BN", REV_SOFT, REV)]
for k, (t, d, f, s) in enumerate(chainL):
    x = 25 + 200 * k
    b += box(x, 60, 170, 60, fill=f, stroke=s, sw=1.6)
    b += txt(x + 85, 85, t, 13, weight="bold", fill=s)
    b += txt(x + 85, 105, d, 11, fill=INK2)
    if k < 3:
        b += line(x + 172, 90, x + 198, 90, INK2, 1.5, marker="ai")
hand = [(125, "받은 것: 입력에만 하던 정규화를", "모든 층 안으로"),
        (325, "받은 것: LRN 을 빼고", "드롭아웃을 줄여도 된다"),
        (525, "넘긴 것: 미니배치에 기대는 통계", "(m 이 작으면? RNN 은?)")]
for x, l1, l2 in hand:
    b += txt(x + 100, 148, l1, 11, fill=INK)
    b += txt(x + 100, 164, l2, 11, fill=INK)
b += box(25, 200, 770, 180, fill=NODE, stroke=LINE)
b += txt(45, 226, "곁가지 — 이상 탐지로 가는 길 (논문은 이 쓰임을 적지 않는다. 내가 잇는 자리다)", 13, anchor="start", weight="bold", fill=REV)
b += txt(45, 252, "PatchCore 같은 방법은 ImageNet 으로 미리 배운 합성곱 망(BN 포함)을 얼려 두고 중간 층 특징만 뽑는다", 12, anchor="start")
b += txt(45, 276, "그때 BN 은 추론 모드 — 알고리즘 2 의 선형 변환이고, 통계는 ImageNet 의 E[x], Var[x] 로 고정되어 있다", 12, anchor="start")
b += txt(45, 300, "그래서 특징의 척도가 「ImageNet 기준」으로 맞춰진다. 산업 이미지의 분포는 ImageNet 과 다르므로 정규화 뒤 평균이 0 이 아닐 수 있다", 12, anchor="start")
b += txt(45, 324, "논문 결론의 「모집단 평균 · 분산만 다시 계산해 새 분포에 적응」이 이 자리의 물음이다 — 정상 이미지로 통계만 다시 재면?", 12, anchor="start", fill=INK2)
b += txt(45, 348, "그리고 학습 모드로 특징을 뽑으면 한 이미지의 특징이 같은 묶음의 다른 이미지에 달린다(그림 8) — 점수가 묶음에 따라 바뀐다", 12, anchor="start", fill=INK2)
b += txt(45, 372, "잴 방법은 이 노트의 돌려 볼 것 D 에 적었다", 11, anchor="start", fill=MUTED)
svg("fig16_lineage", W, H, b, "계보와 이상 탐지로 가는 곁가지")

print("끝.")
