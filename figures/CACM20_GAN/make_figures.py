# -*- coding: utf-8 -*-
"""GAN 노트(Goodfellow 외, Communications of the ACM 2020)의 그림 열넷을 만든다.

색과 글꼴은 앞선 노트들(퍼셉트론부터 VAE 까지)의 그림과 맞췄다 — 저장소의 노트들이 한 벌로 읽히게
하려는 것이다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

이 논문 파일에는 식이 거의 없다(표시된 식 하나와 그림 4 캡션의 둘). 그래서 그림 5 · 6 · 7 · 8 의 수는
노트가 유도한 식으로 이 파일이 직접 계산한다 — 최적 판별기, 게임의 값과 젠슨-섀넌 발산, 두 생성기
비용의 기울기, 동시 갱신과 번갈아 갱신의 궤적. 그림 2 · 4 · 12 의 수도 계산한다. 계산한 값은 돌릴 때
화면에도 찍는다.
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
FWD       = "#2E6B8A"   # 파랑 — 판별기, 진짜 데이터 쪽
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 생성기, 가짜 데이터 쪽
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 잡음 z
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"   # 초록 — 된다
NO        = "#C0392B"   # 빨강 — 안 된다
# 분포 그림 계열 색 — 데이터 · 모델 · 판별기. 논문 그림 4 의 검정 · 초록 · 파랑 점선과 역할을 맞췄다.
S_DATA    = "#1C232C"
S_MODEL   = "#1E8449"
S_DISC    = "#2A78D6"
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


# ── 그림 1. 생성 모델의 세 갈래 — 논문 2절 ─────────────────────────────────────
W, H = 820, 390
b = defs()
b += txt(20, 30, "밀도를 계산할 수 없을 때의 세 갈래 (논문 2절의 분류를 그림으로 옮긴 것)", 15, anchor="start", weight="bold")
cols3 = [("1. 밀도가 계산되게 모델을 짠다", "명시적 · 계산 가능한 밀도", FWD_SOFT, FWD,
          ["예: 완전 가시 믿음망", "(논문이 Frey 1998 · WaveNet 을 든다)", "", "p(x) 를 바로 계산한다", "대신 모델 모양이 묶인다"]),
         ("2. 밀도의 근사로 배운다", "명시적 · 근사한 밀도", CODE_SOFT, CODE,
          ["예: VAE (Kingma & Welling)", "앞 노트에서 읽은 편", "", "log p(x) 의 하한을 올린다", "하한과 참값 사이에 틈이 남는다"]),
         ("3. 밀도를 적지 않는다", "암묵적 · 표본만 뽑는다", REV_SOFT, REV,
          ["GAN 이전: 생성 확률망 (마르코프 사슬)", "GAN: 한 번에 표본 하나", "", "p(x) 를 계산하지 않아도 된다", "대신 p(x) 를 물을 수 없다"])]
for k, (t, sub, f, s, lines_) in enumerate(cols3):
    x = 20 + 263 * k
    b += box(x, 50, 250, 290, fill=f, stroke=s, sw=1.6)
    b += txt(x + 125, 78, t, 13, weight="bold", fill=s)
    b += txt(x + 125, 100, sub, 12, fill=INK2)
    for j, l in enumerate(lines_):
        b += txt(x + 125, 150 + 26 * j, l, 12, fill=INK if j < 2 else INK2)
b += txt(410, 368, "논문 2절은 1 · 2 둘 다 「고해상도 이미지를 만드는 데서 연구자들이 아직 만족하지 못한다」고 적고, 그래서 셋째 길이 쓸모 있을 수 있다고 적는다", 11, fill=MUTED)
svg("fig01_three_paths", W, H, b, "생성 모델의 세 갈래")


# ── 그림 2. 논문 그림 1 — 밀도 추정(최대가능도로 가우스 맞추기) ───────────────────
pts = [-1.3, -0.7, -0.4, 0.1, 0.3, 0.8, 1.2, 1.9]          # 내가 고른 관측 8 개
mu_hat = sum(pts) / len(pts)
sd_hat = math.sqrt(sum((p - mu_hat) ** 2 for p in pts) / len(pts))
ll = sum(math.log(NormalDist(mu_hat, sd_hat).pdf(p)) for p in pts)
ll_off = sum(math.log(NormalDist(mu_hat + 1.0, sd_hat).pdf(p)) for p in pts)
print("  [2] 관측 8 개 최대가능도: 평균 %.4f, 표준편차 %.4f, 로그 가능도 %.3f (평균을 1 옮기면 %.3f)"
      % (mu_hat, sd_hat, ll, ll_off))
W, H = 820, 330
b = defs()
b += txt(20, 30, "논문 그림 1 의 생각 — 관측 몇 개로 밀도 함수 p(x) 를 맞춘다 (점 8 개는 내가 고른 것)", 15, anchor="start", weight="bold")
X0, X1, Y0 = 60, 520, 260
def gx(v):
    return X0 + (v + 3.0) / 6.0 * (X1 - X0)
def gy(p):
    return Y0 - p * 380
b += line(X0, Y0, X1, Y0, INK2, 1.2)
for t in range(-3, 4):
    b += txt(gx(t), Y0 + 18, "%d" % t, 11, fill=MUTED)
b += txt(X1 + 10, Y0 + 4, "x", 13, anchor="start", style="italic")
b += polyline([(gx(-3 + i * 0.05), gy(NormalDist(mu_hat, sd_hat).pdf(-3 + i * 0.05))) for i in range(121)], S_MODEL, 2.4)
b += polyline([(gx(-3 + i * 0.05), gy(NormalDist(mu_hat + 1, sd_hat).pdf(-3 + i * 0.05))) for i in range(121)], MUTED, 1.4, dash="5 4")
for p in pts:
    b += circ(gx(p), Y0, 5, S_DATA, S_DATA)
b += txt(gx(mu_hat), gy(NormalDist(mu_hat, sd_hat).pdf(mu_hat)) - 10, "최대가능도 가우스", 12, fill=S_MODEL, weight="bold")
b += box(550, 55, 250, 230, fill=NODE, stroke=LINE)
b += txt(565, 80, "계산한 값", 13, anchor="start", weight="bold")
for j, l in enumerate(["평균 = 관측의 평균 = %.4f" % mu_hat,
                       "표준편차 = %.4f" % sd_hat,
                       "로그 가능도 = %.3f nat" % ll,
                       "",
                       "평균을 1 옮기면(점선) %.3f" % ll_off,
                       "— 이 모델은 어느 x 에나",
                       "  밀도 값을 줄 수 있다.",
                       "GAN 은 이 값을 주지 않는다."]):
    b += txt(565, 108 + 22 * j, l, 12, anchor="start", fill=INK if j < 3 else INK2)
svg("fig02_density_estimation", W, H, b, "최대가능도로 가우스를 맞추는 예")


# ── 그림 3. 논문 그림 3 — 학습의 두 길 ───────────────────────────────────────
W, H = 820, 400
b = defs()
b += txt(20, 30, "논문 그림 3 — 판별기는 두 길에서 입력을 받고, 생성기는 판별기를 거쳐 온 기울기로 배운다", 15, anchor="start", weight="bold")
def col(x, items, color, soft):
    s = ""
    for j, (t, sub) in enumerate(items):
        y = 320 - 80 * j
        s += box(x, y - 26, 200, 52, fill=soft, stroke=color, sw=1.5)
        s += txt(x + 100, y + (-2 if sub else 5), t, 13, weight="bold")
        if sub:
            s += txt(x + 100, y + 16, sub, 11, fill=INK2)
        if j < 3:
            s += line(x + 100, y - 28, x + 100, y - 52, INK2, 1.4, marker="ai")
    return s
b += col(60, [("데이터셋에서 무작위 번호", None), ("데이터셋", None), ("진짜 데이터 x", None), ("판별기 D(x)", "목표: 1 (진짜)")], FWD, FWD_SOFT)
b += col(430, [("잠재 변수 z ~ p(z)", "가우스나 초입방체 균등"), ("생성기 G(z)", "신경망"), ("가짜 데이터 G(z)", None), ("판별기 D(G(z))", "판별기 목표: 0 / 생성기 목표: 1")], REV, REV_SOFT)
b += path("M640,86 C690,90 690,250 640,240", OK, sw=2, dash="6 4", marker="ao")
b += txt(700, 170, "역전파:", 12, fill=OK, anchor="start", weight="bold")
b += txt(700, 188, "D 의 입력에 대한", 11, fill=OK, anchor="start")
b += txt(700, 204, "기울기가 G 로", 11, fill=OK, anchor="start")
b += txt(160, 372, "두 판별기는 같은 망 하나다 — 두 길의 입력을 번갈아 받는다", 11, fill=MUTED)
b += txt(530, 372, "「가짜」 부류의 분포가 G 가 배울수록 계속 바뀐다", 11, fill=MUTED)
svg("fig03_two_paths", W, H, b, "판별기와 생성기의 학습 경로")


# ── 그림 4. 생성기는 z 의 분포를 x 로 옮기는 함수다 (논문 그림 4 의 화살표) ────────
mu_d, sd_d = 1.0, 0.6
nd = NormalDist()
nz = 12
zs = [(k + 0.5) / nz for k in range(nz)]
xs = [mu_d + sd_d * nd.inv_cdf(z) for z in zs]
gaps = [b_ - a_ for a_, b_ in zip(xs[:-1], xs[1:])]
print("  [4] G(z) = %.1f + %.1f·Φ⁻¹(z): z 간격 %.4f → x 간격 가운데 %.4f, 끝 %.4f (%.2f 배)"
      % (mu_d, sd_d, 1.0 / nz, min(gaps), max(gaps), max(gaps) / min(gaps)))
W, H = 820, 350
b = defs()
b += txt(20, 30, "x = G(z): 고른 간격의 z 를 옮겨 밀도가 높은 곳에 모은다 (논문 그림 4 의 화살표, 수는 내가 고른 예)", 15, anchor="start", weight="bold")
ZX0, ZX1 = 90, 730
def zx(z):
    return ZX0 + z * (ZX1 - ZX0)
def xx(v):
    return ZX0 + (v + 0.8) / 3.6 * (ZX1 - ZX0)
b += line(ZX0, 270, ZX1, 270, INK2, 1.4)
b += txt(ZX0 - 12, 274, "z", 14, anchor="end", style="italic")
b += txt(ZX0, 292, "0", 11, fill=MUTED); b += txt(ZX1, 292, "1", 11, fill=MUTED)
b += line(ZX0, 130, ZX1, 130, INK2, 1.4)
b += txt(ZX0 - 12, 134, "x", 14, anchor="end", style="italic")
for t in (-0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5):
    b += txt(xx(t), 116, "%.1f" % t, 10, fill=MUTED)
for z, x in zip(zs, xs):
    b += line(zx(z), 265, xx(x), 136, CODE, 1.2, marker="ac", op=0.8)
    b += circ(zx(z), 270, 4, CODE, CODE)
    b += circ(xx(x), 130, 4, S_MODEL, S_MODEL)
dens = [(xx(-0.8 + i * 0.03), 130 - 55 * NormalDist(mu_d, sd_d).pdf(-0.8 + i * 0.03) / NormalDist(mu_d, sd_d).pdf(mu_d)) for i in range(121)]
b += polyline(dens, S_MODEL, 2, dash="4 3")
b += txt(410, 318, "z 는 1/%d = %.3f 간격으로 고르다. x 쪽 간격은 가운데 %.3f, 끝 %.3f 로 %.1f 배 차이 — G 가 가운데를 줄이고(모으고) 끝을 늘린다"
         % (nz, 1.0 / nz, min(gaps), max(gaps), max(gaps) / min(gaps)), 12, fill=INK2)
b += txt(410, 338, "논문은 이 예의 G 를 「데이터 분포 역누적분포의 단순한 척도 조정」이라 적는다", 11, fill=MUTED)
svg("fig04_pushforward", W, H, b, "생성기가 균등 잡음을 옮기는 모습")


# ── 그림 5. 최적 판별기 D* = p_data / (p_data + p_model) ─────────────────────────
pd_ = NormalDist(1.5, 0.5)
pm_ = NormalDist(0.0, 1.0)
def dstar(x):
    a, c = pd_.pdf(x), pm_.pdf(x)
    return a / (a + c)
# D* = 0.5 인 자리(두 밀도가 같은 자리)를 이분법으로 찾는다
lo_, hi_ = 0.0, 1.5
for _ in range(60):
    mid = (lo_ + hi_) / 2
    if pd_.pdf(mid) > pm_.pdf(mid):
        hi_ = mid
    else:
        lo_ = mid
cross = (lo_ + hi_) / 2
print("  [5] p_data=N(1.5,0.5²), p_model=N(0,1): D*(0)=%.4f, D*(1.5)=%.4f, D*(3)=%.4f, D*=0.5 인 x=%.4f"
      % (dstar(0), dstar(1.5), dstar(3.0), cross))
W, H = 820, 380
b = defs()
b += txt(20, 30, "G 를 고정하면 판별기의 최선은 D*(x) = p_data(x) / (p_data(x) + p_model(x)) — 논문 그림 4(b)(d)", 15, anchor="start", weight="bold")
def panel(b, x0, title, pdat, pmod, note):
    PX0, PX1, PY0, PY1 = x0 + 30, x0 + 360, 300, 80
    def X(v):
        return PX0 + (v + 3) / 7.0 * (PX1 - PX0)
    def Yp(p):
        return PY0 - p / 0.85 * (PY0 - PY1)
    def Yd(d):
        return PY0 - d * (PY0 - PY1)
    b += box(x0, 50, 380, 300, fill="none", stroke=LINE)
    b += txt(x0 + 190, 72, title, 13, weight="bold")
    b += line(PX0, PY0, PX1, PY0, INK2, 1)
    for t in range(-3, 5):
        b += txt(X(t), PY0 + 16, "%d" % t, 10, fill=MUTED)
    b += line(PX0, Yd(0.5), PX1, Yd(0.5), LINE, 1, dash="2 3")
    b += txt(PX1 + 4, Yd(0.5) + 4, "½", 11, anchor="start", fill=MUTED)
    b += txt(PX1 + 4, Yd(1.0) + 4, "1", 11, anchor="start", fill=MUTED)
    grid = [-3 + i * 0.05 for i in range(141)]
    b += polyline([(X(v), Yp(pdat.pdf(v))) for v in grid], S_DATA, 1.8, dash="2 3")
    b += polyline([(X(v), Yp(pmod.pdf(v))) for v in grid], S_MODEL, 2.2)
    b += polyline([(X(v), Yd(pdat.pdf(v) / (pdat.pdf(v) + pmod.pdf(v)))) for v in grid], S_DISC, 2.2, dash="7 4")
    b += txt(x0 + 190, 338, note, 11, fill=INK2)
    return b
b = panel(b, 20, "(b) G 가 아직 멀 때", pd_, pm_, "D*(0) = %.2f,  D*(1.5) = %.2f,  두 밀도가 같은 x = %.2f 에서 ½" % (dstar(0), dstar(1.5), cross))
b = panel(b, 420, "(d) p_model = p_data 일 때", pd_, pd_, "모든 x 에서 D* = ½ — 판별기가 가를 것이 없다")
lx = 40
for lab, colr, dash in (("p_data (검정 점선)", S_DATA, "2 3"), ("p_model (초록 실선)", S_MODEL, None), ("D* (파랑 점선)", S_DISC, "7 4")):
    b += line(lx, 368, lx + 26, 368, colr, 2, dash=dash)
    b += txt(lx + 32, 372, lab, 11, anchor="start")
    lx += 200
svg("fig05_optimal_D", W, H, b, "최적 판별기의 모양")


# ── 그림 6. 게임의 값 = −log 4 + 2·JSD (D 가 최적일 때) ──────────────────────────
def integrate(f, a=-12.0, c=16.0, n=28000):
    h = (c - a) / n
    s = 0.5 * (f(a) + f(c))
    for i in range(1, n):
        s += f(a + i * h)
    return s * h
def kl(p, q):
    return integrate(lambda x: p(x) * math.log(max(p(x), 1e-300) / max(q(x), 1e-300)) if p(x) > 1e-300 else 0.0)
def game_parts(m):
    P = NormalDist(0, 1).pdf
    Q = NormalDist(m, 1).pdf
    M = lambda x: 0.5 * (P(x) + Q(x))
    jsd = 0.5 * kl(P, M) + 0.5 * kl(Q, M)
    V = integrate(lambda x: P(x) * math.log(max(P(x) / (P(x) + Q(x)), 1e-300))
                  + Q(x) * math.log(max(Q(x) / (P(x) + Q(x)), 1e-300)))
    return jsd, V
ms = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
gv = {}
for m in ms:
    jsd, V = game_parts(m)
    gv[m] = (jsd, V)
    print("  [6] p_model=N(%.1f,1): JSD %.4f nat,  V(D*,G) 직접 %.4f,  −log4+2·JSD %.4f" % (m, jsd, V, -math.log(4) + 2 * jsd))
W, H = 820, 380
b = defs()
b += txt(20, 30, "D 가 최적일 때 게임의 값 V = −log 4 + 2·JSD — p_data=N(0,1), p_model=N(m,1) (내가 유도하고 계산한 것)", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 80, 520, 320, 70
def px(m):
    return PX0 + m / 5.0 * (PX1 - PX0)
def py(v):
    return PY0 - (v + 1.5) / 1.6 * (PY0 - PY1)
for v in (-1.5, -1.0, -0.5, 0.0):
    b += line(PX0, py(v), PX1, py(v), LINE, 1)
    b += txt(PX0 - 8, py(v) + 4, "%.1f" % v, 11, anchor="end", fill=MUTED)
for m in range(0, 6):
    b += txt(px(m), PY0 + 18, "%d" % m, 11, fill=MUTED)
b += txt((PX0 + PX1) / 2, PY0 + 40, "m (모델 평균이 데이터 평균에서 떨어진 거리)", 12, fill=INK2)
b += line(PX0, py(-math.log(4)), PX1, py(-math.log(4)), OK, 1.2, dash="4 3")
b += txt(PX1 - 4, py(-math.log(4)) + 16, "−log 4 = %.3f (p_model = p_data)" % -math.log(4), 11, anchor="end", fill=OK)
b += line(PX0, py(0), PX1, py(0), NO, 1.2, dash="4 3")
b += txt(PX1 - 4, py(0) - 6, "0 = −log 4 + 2·log 2 (겹침이 없을 때의 끝)", 11, anchor="end", fill=NO)
b += polyline([(px(m), py(gv[m][1])) for m in ms], S_DISC, 2.4)
for m in ms:
    b += circ(px(m), py(gv[m][1]), 4, S_DISC, S_DISC)
b += box(550, 70, 250, 250, fill=NODE, stroke=LINE)
b += txt(565, 94, "m 별 JSD (nat) 와 V", 12, anchor="start", weight="bold")
for j, m in enumerate([0.0, 1.0, 2.0, 3.0, 5.0]):
    b += txt(565, 122 + 24 * j, "m = %.0f:  JSD %.3f,  V %.3f" % (m, gv[m][0], gv[m][1]), 12, anchor="start")
b += txt(565, 256, "JSD 의 위 끝은 log 2 = %.3f." % math.log(2), 11, anchor="start", fill=INK2)
b += txt(565, 276, "m 이 5 이면 이미 그 %.0f%% 다 —" % (100 * gv[5.0][0] / math.log(2)), 11, anchor="start", fill=INK2)
b += txt(565, 296, "더 멀어져도 V 가 거의 안 바뀐다", 11, anchor="start", fill=INK2)
svg("fig06_value_jsd", W, H, b, "게임의 값과 젠슨-섀넌 발산")


# ── 그림 7. 생성기 비용 둘 — 미니맥스(M-GAN) 대 포화하지 않는(NS-GAN) ─────────────
d_ex = 0.01
print("  [7] D(G(z)) = %.2f 에서 로짓에 대한 기울기 크기: M-GAN %.2f, NS-GAN %.2f (%.0f 배)"
      % (d_ex, d_ex, 1 - d_ex, (1 - d_ex) / d_ex))
W, H = 820, 380
b = defs()
b += txt(20, 30, "생성기 비용 둘 — 판별기가 가짜를 쉽게 알아볼 때(D(G(z)) 가 0 쪽) 기울기가 어떻게 되나 (내가 유도한 것)", 14, anchor="start", weight="bold")
for p, (title, ylab) in enumerate([("생성기 비용 (줄이는 쪽)", "비용"), ("판별기 로짓 a 에 대한 기울기 크기", "|∂비용/∂a|")]):
    x0 = 20 + 395 * p
    PX0, PX1, PY0, PY1 = x0 + 50, x0 + 370, 300, 80
    b += box(x0, 50, 385, 290, fill="none", stroke=LINE)
    b += txt(x0 + 192, 72, title, 13, weight="bold")
    b += line(PX0, PY0, PX1, PY0, INK2, 1)
    b += line(PX0, PY0, PX0, PY1, INK2, 1)
    for t in (0, 0.5, 1):
        b += txt(PX0 + t * (PX1 - PX0), PY0 + 16, "%g" % t, 10, fill=MUTED)
    b += txt((PX0 + PX1) / 2, PY0 + 34, "D(G(z)) — 판별기가 가짜를 진짜라 볼 확률", 11, fill=INK2)
    grid = [0.005 + i * 0.005 for i in range(198)]
    if p == 0:
        def Y(v):
            return PY0 - (v + 4.5) / 9.0 * (PY0 - PY1)
        for t in (-4, 0, 4):
            b += txt(PX0 - 6, Y(t) + 4, "%d" % t, 10, anchor="end", fill=MUTED)
        b += line(PX0, Y(0), PX1, Y(0), LINE, 1)
        b += polyline([(PX0 + d * (PX1 - PX0), Y(math.log(1 - d))) for d in grid if math.log(1 - d) > -4.5], NO, 2.4)
        b += polyline([(PX0 + d * (PX1 - PX0), Y(-math.log(d))) for d in grid if -math.log(d) < 4.5], OK, 2.4)
        b += txt(PX0 + 20, Y(-0.9), "M-GAN: log(1 − D)", 12, anchor="start", fill=NO, weight="bold")
        b += txt(PX0 + 30, Y(3.6), "NS-GAN: −log D", 12, anchor="start", fill=OK, weight="bold")
        b += txt(PX0 + 22, Y(-1.9), "왼쪽 끝이 평평하다", 11, anchor="start", fill=NO)
    else:
        def Y(v):
            return PY0 - v * (PY0 - PY1)
        for t in (0, 0.5, 1):
            b += txt(PX0 - 6, Y(t) + 4, "%g" % t, 10, anchor="end", fill=MUTED)
        b += polyline([(PX0 + d * (PX1 - PX0), Y(d)) for d in grid], NO, 2.4)
        b += polyline([(PX0 + d * (PX1 - PX0), Y(1 - d)) for d in grid], OK, 2.4)
        b += txt(PX1 - 10, Y(0.9), "M-GAN: D", 12, anchor="end", fill=NO, weight="bold")
        b += txt(PX0 + 0.3 * (PX1 - PX0), Y(0.82), "NS-GAN: 1 − D", 12, anchor="start", fill=OK, weight="bold")
        b += circ(PX0 + d_ex * (PX1 - PX0), Y(d_ex), 5, NO, NO)
        b += circ(PX0 + d_ex * (PX1 - PX0), Y(1 - d_ex), 5, OK, OK)
        b += txt((PX0 + PX1) / 2, Y(0.1), "D = %.2f 에서 %.2f 대 %.2f (%.0f 배)" % (d_ex, d_ex, 1 - d_ex, (1 - d_ex) / d_ex), 11, fill=INK2)
b += txt(410, 366, "D = σ(a) 로 두면 ∂ log(1−σ(a))/∂a = −σ(a),  ∂(−log σ(a))/∂a = −(1 − σ(a)). 학습 초기에는 판별기가 쉽게 이겨 D(G(z)) 가 0 쪽에 있다", 11, fill=MUTED)
svg("fig07_saturation", W, H, b, "생성기 비용 둘의 기울기 비교")


# ── 그림 8. 동시 갱신은 돌면서 멀어진다 — 가장 작은 게임 V(x, y) = x·y ─────────────
eta, steps = 0.1, 100
sim = [(1.0, 0.0)]
alt = [(1.0, 0.0)]
for _ in range(steps):
    x, y = sim[-1]
    sim.append((x - eta * y, y + eta * x))           # x 는 줄이고 y 는 올린다, 둘이 같은 순간의 값을 본다
    x, y = alt[-1]
    x2 = x - eta * y
    alt.append((x2, y + eta * x2))                   # y 는 x 가 움직인 뒤의 값을 본다
r_sim = math.hypot(*sim[-1])
r_alt_max = max(math.hypot(*p) for p in alt)
print("  [8] η=%.1f, %d 걸음: 동시 갱신 반지름 1 → %.4f (식 (1+η²)^%d = %.4f),  번갈아 갱신 최대 반지름 %.4f"
      % (eta, steps, r_sim, steps // 2, (1 + eta ** 2) ** (steps / 2.0), r_alt_max))
W, H = 820, 400
b = defs()
b += txt(20, 30, "x 는 x·y 를 줄이고 y 는 올린다 — 내시 평형은 (0, 0) 하나인데 동시 기울기 걸음은 거기 가지 않는다 (내가 붙인 예)", 14, anchor="start", weight="bold")
for p, (title, traj, colr) in enumerate([("동시 갱신 (논문이 「가장 흔하다」고 적는 것)", sim, NO), ("번갈아 갱신", alt, OK)]):
    x0 = 20 + 395 * p
    cx, cy, sc = x0 + 192, 215, 85
    b += box(x0, 50, 385, 300, fill="none", stroke=LINE)
    b += txt(x0 + 192, 72, title, 13, weight="bold", fill=colr)
    b += line(cx - 170, cy, cx + 170, cy, LINE, 1); b += line(cx, cy - 135, cx, cy + 135, LINE, 1)
    b += ell(cx, cy, sc, sc, stroke=MUTED, dash="3 3")
    b += polyline([(cx + sc * a, cy - sc * c) for a, c in traj], colr, 1.8)
    b += circ(cx + sc, cy, 4, INK, INK)
    b += circ(cx, cy, 4, OK, OK)
    b += txt(cx + 8, cy + 16, "평형", 10, anchor="start", fill=OK)
b += txt(212, 342, "반지름 1 → %.3f (한 걸음마다 √(1+η²) = %.4f 배)" % (r_sim, math.sqrt(1 + eta ** 2)), 12, fill=NO)
b += txt(607, 342, "최대 반지름 %.3f — 돌기만 하고 커지지 않는다" % r_alt_max, 12, fill=OK)
b += txt(410, 372, "η = %.1f, %d 걸음, 시작 (1, 0), 점선 원 = 반지름 1. 어느 쪽도 평형에 닿지 않는다 — 기울기 걸음만으로는 게임의 평형을 찾는다는 보장이 없다" % (eta, steps), 11, fill=MUTED)
b += txt(410, 390, "이 예는 이 논문에 없다. 논문 4절이 「실제로 자주 수렴에 실패한다」고 적는 자리를 가장 작은 꼴로 옮긴 것이다", 11, fill=MUTED)
svg("fig08_simultaneous", W, H, b, "동시 갱신과 번갈아 갱신의 궤적")


# ── 그림 9. 이론이 가정한 학습 대 실제로 쓰는 학습 ─────────────────────────────
W, H = 820, 380
b = defs()
b += txt(20, 30, "논문 4절의 두 결과가 성립하는 자리와 실제로 학습하는 자리 사이의 거리", 15, anchor="start", weight="bold")
rows = [("움직이는 것", "밀도 함수 p_model 자체", "생성기 신경망의 파라미터 θ(G)"),
        ("함수의 범위", "모든 밀도 함수 · 모든 판별기", "유한한 수의 파라미터, 유한한 비트"),
        ("판별기", "안쪽 고리에서 수렴할 때까지", "한 걸음씩, 최적이 아니다"),
        ("생성기 비용", "M-GAN (J(G) = −J(D))", "대개 NS-GAN (라벨을 뒤집는다)"),
        ("갱신", "D 를 끝까지, 그다음 G 한 걸음", "두 쪽을 동시에 한 걸음씩"),
        ("결과", "평형은 p_model = p_data 하나, 수렴한다", "논문: 「자주 수렴에 실패한다」")]
cw = [150, 310, 320]
x0, y0 = 20, 55
b += box(x0, y0, sum(cw), 36, fill="#DDE3E0", stroke=LINE, rx=4)
for k, t in enumerate(["", "이론 (원 논문의 두 결과)", "실제"]):
    b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y0 + 23, t, 13, weight="bold", fill=[INK, OK, NO][k])
for r, row in enumerate(rows):
    y = y0 + 36 + 42 * r
    b += box(x0, y, sum(cw), 42, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    for k, t in enumerate(row):
        b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y + 26, t, 12, weight="bold" if k == 0 else None)
b += txt(410, 360, "첫 두 줄의 거리는 논문이 스스로 적는다. 셋째 · 넷째 줄은 논문 3절의 설명을 4절의 결과 옆에 놓아 내가 맞춘 것이다", 11, fill=MUTED)
svg("fig09_theory_vs_practice", W, H, b, "이론의 가정과 실제 학습의 비교")


# ── 그림 10. 오차의 출처 — 논문이 「근사가 적다」고 말하는 근거 ─────────────────
W, H = 820, 350
b = defs()
b += txt(20, 30, "논문 3절 — GAN 에 남는 오차는 둘뿐이고 다른 방법들은 그 위에 근사를 더한다고 적는다", 15, anchor="start", weight="bold")
srcs = ["통계 오차 (유한한 학습 데이터)", "학습이 최적 파라미터에 못 닿음", "마르코프 사슬 근사", "참 비용 대신 하한을 최적화"]
methods = [("GAN", [1, 1, 0, 0]), ("마르코프 사슬 쓰는 모델", [1, 1, 1, 0]), ("하한을 쓰는 모델", [1, 1, 0, 1])]
cw = [300, 160, 160, 160]
x0, y0 = 20, 55
b += box(x0, y0, sum(cw), 36, fill="#DDE3E0", stroke=LINE, rx=4)
for k, (m, _) in enumerate(methods):
    b += txt(x0 + cw[0] + 160 * k + 80, y0 + 23, m, 12, weight="bold")
for r, s in enumerate(srcs):
    y = y0 + 36 + 44 * r
    b += box(x0, y, sum(cw), 44, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    b += txt(x0 + 12, y + 27, s, 12, anchor="start")
    for k, (m, v) in enumerate(methods):
        cx = x0 + cw[0] + 160 * k + 80
        b += txt(cx, y + 27, "있다" if v[r] else "—", 12, fill=NO if v[r] else MUTED, weight="bold" if v[r] else None)
b += txt(410, 292, "논문은 셋째 · 넷째 열의 방법 이름을 적지 않는다. 앞 노트의 VAE 가 넷째 열(하한), GAN 앞의 생성 확률망이 셋째 열에 든다고 내가 맞췄다", 11, fill=MUTED)
b += txt(410, 314, "그리고 「GAN 의 두 오차」 가운데 둘째가 실제로는 가장 크다 — 4절이 「자주 수렴에 실패한다」고 적는 것이 그 칸이다", 11, fill=INK2)
b += txt(410, 336, "이 표는 논문의 문장을 옮긴 것이다. 오차의 크기를 잰 값은 논문에 없다", 11, fill=MUTED)
svg("fig10_error_sources", W, H, b, "생성 모델별 오차 출처 표")


# ── 그림 11. 논문 그림 6 — 네 해의 진척과 캡션의 순서 ─────────────────────────
W, H = 820, 330
b = defs()
b += txt(20, 30, "논문 그림 6 — 2014 · 2015 · 2016 · 2017 의 얼굴 표본 넷. 캡션의 「respectively」 순서가 해의 순서와 다르다", 15, anchor="start", weight="bold")
years = [("2014", "Goodfellow 외", "참고 문헌 13, NIPS 2014", "원 GAN"),
         ("2015", "Radford 외", "참고 문헌 27, arXiv 2015", "DCGAN"),
         ("2016", "Liu & Tuzel", "참고 문헌 17, NIPS 2016", "CoGAN"),
         ("2017", "Karras 외", "참고 문헌 14, 2017", "Progressive GAN")]
for k, (yr, who, ref, nm) in enumerate(years):
    x = 30 + 195 * k
    b += box(x, 60, 170, 150, fill=NODE, stroke=INK2)
    b += txt(x + 85, 110, yr, 24, weight="bold", fill=REV)
    b += txt(x + 85, 140, nm, 13, weight="bold")
    b += txt(x + 85, 165, who, 12, fill=INK2)
    b += txt(x + 85, 185, ref, 10, fill=MUTED)
    if k < 3:
        b += line(x + 172, 135, x + 193, 135, INK2, 1.4, marker="ai")
b += box(30, 230, 760, 80, fill=NODE, stroke=LINE)
b += txt(50, 254, "캡션: 「결과는 각각(respectively) Goodfellow, Karras 외, Liu and Tuzel, Radford 외에서 왔다」 — 이름의 알파벳 순서다", 12, anchor="start")
b += txt(50, 276, "참고 문헌의 연도로 맞추면 2014 = Goodfellow, 2015 = Radford, 2016 = Liu & Tuzel, 2017 = Karras 다 (위 칸은 이 순서로 놓았다)", 12, anchor="start")
b += txt(50, 298, "캡션을 글자 그대로 읽으면 2015 가 Karras(2017 논문)가 되어 어긋난다. 연도로 맞춘 것은 내 읽기다", 12, anchor="start", fill=INK2)
svg("fig11_progress", W, H, b, "논문 그림 6 의 연도와 출처 맞추기")


# ── 그림 12. 얇은 다양체 위의 모델 — 데이터에 가능도 0 을 줄 수 있다 ───────────────
n12 = 60
data12 = []
for _ in range(n12):
    t = random.uniform(0, 2 * math.pi)
    r = 1.0 + random.gauss(0, 0.06)
    data12.append((r * math.cos(t), r * math.sin(t)))
dists = [abs(math.hypot(*p) - 1.0) for p in data12]
on_curve = sum(1 for d in dists if d == 0.0)
print("  [12] 데이터 %d 점(반지름 1 ± 가우스 0.06): 원까지 거리 평균 %.4f, 최대 %.4f, 원 위에 정확히 놓인 점 %d 개"
      % (n12, sum(dists) / n12, max(dists), on_curve))
W, H = 820, 375
b = defs()
b += txt(20, 30, "p_model 의 받침이 얇은 곡선 하나일 때 (논문 5절의 「특이한 점」, 수는 내가 고른 예)", 15, anchor="start", weight="bold")
cx, cy, sc = 200, 200, 120
b += box(20, 50, 360, 310, fill="none", stroke=LINE)
b += ell(cx, cy, sc, sc, stroke=S_MODEL, sw=2.4)
for p in data12:
    b += circ(cx + sc * p[0], cy - sc * p[1], 3, S_DATA, S_DATA, op=0.8)
b += txt(200, 350, "초록 원 = 생성기가 낼 수 있는 모든 점 (2 차원 안의 1 차원)", 11, fill=S_MODEL)
b += box(400, 50, 400, 310, fill=NODE, stroke=LINE)
lines12 = ["2 차원 평면에서 원 위의 넓이는 0 이다.",
           "그래서 p_model 을 2 차원 밀도로 보면",
           "원 밖 어디서나 0 이고, 원 위에서는 정의되지 않는다.",
           "",
           "데이터 %d 점 중 원 위에 정확히 놓인 점: %d 개" % (n12, on_curve),
           "원까지 거리: 평균 %.3f, 최대 %.3f" % (sum(dists) / n12, max(dists)),
           "→ 학습 데이터의 로그 가능도는 −∞",
           "",
           "그래도 표본은 데이터에 %.3f 만큼 가깝다." % (sum(dists) / n12),
           "최대가능도는 이 모델을 배울 수 없지만",
           "판별기는 가짜와 진짜를 가르는 신호를 준다."]
for j, l in enumerate(lines12):
    b += txt(420, 80 + 23 * j, l, 12, anchor="start", fill=NO if "−∞" in l else INK)
svg("fig12_thin_manifold", W, H, b, "얇은 다양체 위 모델의 가능도")


# ── 그림 13. VAE(2014) 대 GAN ───────────────────────────────────────────────
W, H = 820, 470
b = defs()
b += txt(20, 30, "VAE(2014) 와 GAN — 둘 다 z ~ 단순한 분포 → 신경망 → x 인데, 배우는 방법이 다르다", 15, anchor="start", weight="bold")
rows = [("모델이 주는 것", "p(x) 의 하한 L(x), 표본", "표본만"),
        ("p(x|z) 를 정하나", "정한다 (픽셀별 베르누이 · 가우스)", "정하지 않는다 (G 는 결정적 함수)"),
        ("x → z 부호기", "있다 (q(z|x))", "원 GAN 에는 없다"),
        ("학습 목표", "하한 L 을 최대화 (최적화)", "두 사람 게임의 평형 (게임)"),
        ("「비슷하다」를 정하는 것", "사람이 고른 가능도", "배우는 판별기"),
        ("남는 근사", "하한과 log p(x) 의 틈", "통계 오차 + 수렴 실패"),
        ("평가", "하한 · 추정 주변 가능도", "가능도를 못 잰다 — 평가가 따로 연구 주제"),
        ("이산 데이터", "복호기는 이산도 된다", "어렵다 (G 출력을 거쳐 기울기를 보내야 한다)"),
        ("얇은 다양체 모델", "가능도가 −∞ 라 못 배운다", "배울 수 있다")]
cw = [200, 290, 290]
x0, y0 = 20, 55
b += box(x0, y0, sum(cw), 36, fill="#DDE3E0", stroke=LINE, rx=4)
for k, t in enumerate(["", "VAE (Kingma & Welling 2014)", "GAN (이 논문)"]):
    b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y0 + 23, t, 13, weight="bold", fill=[INK, CODE, REV][k])
for r, row in enumerate(rows):
    y = y0 + 36 + 38 * r
    b += box(x0, y, sum(cw), 38, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    for k, t in enumerate(row):
        b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y + 24, t, 12, weight="bold" if k == 0 else None)
b += txt(410, 458, "VAE 칸은 앞 노트에서 읽은 VAE 논문, GAN 칸은 이 논문의 문장에서 옮겼다. 두 논문 모두 서로를 같은 표본 품질 지표로 재지 않는다", 11, fill=MUTED)
svg("fig13_vae_vs_gan", W, H, b, "VAE 와 GAN 비교 표")


# ── 그림 14. 계보 — 어디서 받아 어디로 넘기는가 ─────────────────────────────
W, H = 820, 380
b = defs()
b += txt(20, 30, "계보 — 앞 편의 한계를 받아 다음 편에 넘긴다", 15, anchor="start", weight="bold")
chainL = [("VAE 2014 (읽음)", "가능도를 정해야 한다", CODE_SOFT, CODE),
          ("GAN 2014 / 2020", "가능도 없이 게임으로", REV_SOFT, REV),
          ("DDPM 2020 (읽음)", "다시 하한, 층을 많이", FWD_SOFT, FWD),
          ("RNN (로드맵 다음)", "순서가 있는 데이터", NODE, INK2)]
for k, (t, d, f, s) in enumerate(chainL):
    x = 25 + 200 * k
    b += box(x, 60, 170, 60, fill=f, stroke=s, sw=1.6)
    b += txt(x + 85, 85, t, 13, weight="bold", fill=s)
    b += txt(x + 85, 105, d, 11, fill=INK2)
    if k < 3:
        b += line(x + 172, 90, x + 198, 90, INK2, 1.5, marker="ai")
hand = [(125, "받은 것: 복호기의 픽셀별", "가능도가 「비슷함」을 정한다"),
        (325, "넘긴 것: 학습이 수렴하지 않고", "가능도로 평가할 수 없다"),
        (525, "로드맵의 생성 모델 칸이", "여기서 끝난다")]
for x, l1, l2 in hand:
    b += txt(x + 100, 148, l1, 11, fill=INK)
    b += txt(x + 100, 164, l2, 11, fill=INK)
b += box(25, 200, 770, 160, fill=NODE, stroke=LINE)
b += txt(45, 226, "곁가지 — 이상 탐지로 가는 길 (논문은 이 쓰임을 적지 않는다. 내가 잇는 자리다)", 13, anchor="start", weight="bold", fill=REV)
b += txt(45, 252, "GAN 은 p(x) 도, x 를 z 로 돌리는 부호기도 주지 않는다. 그래서 「이 입력이 얼마나 정상다운가」를 바로 물을 수 없다", 12, anchor="start")
b += txt(45, 276, "남는 길 둘: 학습이 끝난 판별기의 출력 D(x) 를 점수로 쓰거나, G(z) 가 x 에 가장 가까워지는 z 를 찾아 그 거리를 점수로 쓴다", 12, anchor="start")
b += txt(45, 300, "첫째는 조심할 것이 있다 — 평형에서는 D 가 어디서나 ½ 이 되는 것이 목표라서, 잘 배운 D 일수록 점수로 쓸 신호가 줄 수 있다", 12, anchor="start")
b += txt(45, 324, "둘째는 입력마다 최적화를 한 번 돌려야 한다 — VAE 의 부호기가 한 번의 계산으로 하던 일이다", 12, anchor="start", fill=INK2)
b += txt(45, 348, "잴 방법은 이 노트 23절 D 에 적었다", 11, anchor="start", fill=MUTED)
svg("fig14_lineage", W, H, b, "계보와 이상 탐지로 가는 곁가지")

print("끝.")
