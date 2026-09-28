# -*- coding: utf-8 -*-
"""VAE 노트(Kingma & Welling, ICLR 2014)의 그림 열넷을 만든다.

색과 글꼴은 앞선 노트들(퍼셉트론 · 역전파 · DBN · LeNet · AlexNet · 오토인코더)의 그림과 맞췄다 —
저장소의 노트들이 한 벌로 읽히게 하려는 것이다. 결과 그림 둘(그림 10 · 11)만 계열 색 셋을 따로 쓴다.
바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

그림 3 의 변분 하한 분해, 그림 4 의 두 기울기 추정량의 분산, 그림 6 의 역누적분포 예시, 그림 7 의
파라미터 수, 그림 8 의 KL 값, 그림 9 의 계산 시간, 그림 10 의 학습-시험 간격, 그림 12 의 격자 좌표는
이 파일이 직접 계산한다. 계산한 값은 돌릴 때 화면에도 찍는다. 몬테카를로 확인은 seed 0 으로 고정했다.
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
FWD       = "#2E6B8A"   # 파랑 — 생성 쪽(θ), 정해져 있는 것
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 추론 쪽(φ), 근사하는 것
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 코드(잠재 변수)
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"   # 초록 — 된다
NO        = "#C0392B"   # 빨강 — 안 된다
# 결과 그림 계열 색 — AEVB · 깨어남-잠 · 몬테카를로 EM. 이 순서로 고정한다.
S_AEVB    = "#EB6834"
S_WS      = "#2A78D6"
S_MCEM    = "#1BAF7A"
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


# ── 그림 1. 앞 노트가 남긴 빈칸 — 코드 공간에 분포가 없다 ──────────────────────
W, H = 820, 400
b = defs()
b += txt(20, 30, "오토인코더의 코드 공간 대 VAE 의 코드 공간 (개념도 — 점의 자리는 내가 그린 것이다)", 15, anchor="start", weight="bold")
arms = [(0.3, FWD), (1.9, REV), (3.5, OK), (5.0, CODE)]
# 왼쪽: 오토인코더 — 점이 팔 모양으로 뻗고 팔 사이가 빈다
ox, oy = 210, 195
b += box(20, 50, 380, 335, fill="none", stroke=LINE)
b += txt(210, 74, "오토인코더(2006): 입력마다 점 하나", 13, weight="bold", fill=INK)
for ang, col in arms:
    for k in range(14):
        r = 10 + 7 * k + random.uniform(-3, 3)
        a = ang + random.uniform(-0.12, 0.12)
        b += circ(ox + r * math.cos(a), oy - r * math.sin(a), 3.2, col, col, op=0.85)
qx, qy = ox + 62 * math.cos(1.1), oy - 62 * math.sin(1.1)
b += txt(qx, qy + 5, "?", 22, weight="bold", fill=NO)
b += txt(210, 348, "팔 사이에서 점을 골라 복호기에 넣으면", 12, fill=INK2)
b += txt(210, 366, "무엇이 나올지 정한 것이 없다", 12, fill=NO)
# 오른쪽: VAE — 입력마다 작은 가우스, 전체는 N(0, I) 안에 모인다
ox, oy = 610, 195
b += box(420, 50, 380, 335, fill="none", stroke=LINE)
b += txt(610, 74, "VAE(2014): 입력마다 분포 하나", 13, weight="bold", fill=INK)
b += ell(ox, oy, 52, 52, stroke=MUTED, dash="4 3")
b += ell(ox, oy, 104, 104, stroke=MUTED, dash="4 3")
b += txt(ox + 40, oy - 40, "1σ", 10, fill=MUTED, anchor="start")
b += txt(ox + 76, oy - 78, "2σ", 10, fill=MUTED, anchor="start")
for ang, col in arms:
    for k in range(4):
        r = 18 + 20 * k + random.uniform(-4, 4)
        a = ang + random.uniform(-0.25, 0.25)
        b += ell(ox + r * math.cos(a), oy - r * math.sin(a), 13, 9, fill=col, stroke=col, op=0.35)
b += circ(ox + 45 * math.cos(1.1), oy - 45 * math.sin(1.1), 4, NO, NO)
b += txt(610, 348, "사전분포 N(0, I) 에서 점을 뽑으면 복호기가", 12, fill=INK2)
b += txt(610, 366, "학습 중에 본 자리다 — 학습 목표가 그렇게 만든다", 12, fill=OK)
svg("fig01_gap", W, H, b, "오토인코더와 VAE 의 코드 공간 비교")


# ── 그림 2. 논문 그림 1 — 다루는 방향 그래프 모델 ───────────────────────────────
W, H = 820, 340
b = defs()
b += txt(20, 30, "논문 그림 1 — 실선은 생성 모델 pθ(z)pθ(x|z), 점선은 근사 추론 qφ(z|x)", 15, anchor="start", weight="bold")
b += box(250, 60, 260, 250, fill="none", stroke=INK2, sw=1.4)
b += txt(495, 298, "N", 14, weight="bold", fill=INK2)
zx, zy, xx, xy = 380, 115, 380, 245
b += circ(zx, zy, 30, CODE_SOFT, CODE, 1.8)
b += txt(zx, zy + 6, "z", 18, weight="bold", style="italic")
b += circ(xx, xy, 30, "#C9D2D6", INK, 1.8)
b += txt(xx, xy + 6, "x", 18, weight="bold", style="italic")
b += line(zx - 6, zy + 31, xx - 6, xy - 33, FWD, 2, marker="af")
b += path("M%s,%s Q%s,%s %s,%s" % (xx + 22, xy - 22, xx + 70, 180, zx + 24, zy + 20), REV, sw=2, dash="6 4", marker="ar")
b += circ(130, 180, 26, FWD_SOFT, FWD, 1.6)
b += txt(130, 187, "θ", 18, weight="bold", fill=FWD)
b += line(155, 170, zx - 32, zy + 6, FWD, 1.6, marker="af")
b += line(155, 190, xx - 32, xy - 8, FWD, 1.6, marker="af")
b += circ(640, 180, 26, REV_SOFT, REV, 1.6)
b += txt(640, 187, "φ", 18, weight="bold", fill=REV)
b += line(615, 170, zx + 34, zy + 10, REV, 1.6, dash="6 4", marker="ar")
b += txt(130, 230, "생성 파라미터", 12, fill=FWD)
b += txt(130, 247, "(복호기)", 12, fill=FWD)
b += txt(640, 230, "변분 파라미터", 12, fill=REV)
b += txt(640, 247, "(부호기 = 인식 모델)", 12, fill=REV)
b += txt(410, 330, "사각형(판) = 데이터 점 N 개마다 되풀이된다. θ 와 φ 는 판 밖에 있어 모든 데이터 점이 함께 쓴다", 11, fill=MUTED)
svg("fig02_graphical_model", W, H, b, "방향 그래프 모델과 근사 추론")


# ── 그림 3. 식 (1)(3) — log p(x) = KL + L, 그리고 L = 재구성 - KL ────────────────
# 사후분포를 닫힌 꼴로 아는 1 차원 선형 가우스 모델로 식 (1) 을 숫자로 맞춰 본다(내가 붙인 예시).
# p(z) = N(0, 1),  p(x|z) = N(w z, s^2),  관측 x = 3
w_, s_, x_ = 2.0, 1.0, 3.0
logpx = -0.5 * math.log(2 * math.pi * (w_ ** 2 + s_ ** 2)) - x_ ** 2 / (2 * (w_ ** 2 + s_ ** 2))
post_v = 1.0 / (1 + w_ ** 2 / s_ ** 2)
post_m = post_v * w_ * x_ / s_ ** 2


def elbo_parts(m, v):
    rec = -0.5 * math.log(2 * math.pi * s_ ** 2) - ((x_ - w_ * m) ** 2 + w_ ** 2 * v) / (2 * s_ ** 2)
    klp = 0.5 * (m ** 2 + v - 1 - math.log(v))                      # KL(q || p(z))
    klpost = 0.5 * (v / post_v + (m - post_m) ** 2 / post_v - 1 + math.log(post_v / v))  # KL(q || p(z|x))
    return rec, klp, rec - klp, klpost


qs = [("q 가 사후분포와 다를 때: q = N(0.5, 0.6²)", 0.5, 0.36),
      ("q 를 사후분포로 둘 때: q = N(%.1f, %.3f)" % (post_m, post_v), post_m, post_v)]
print("  [3] 선형 가우스 예시: log p(x=3) = %.4f,  사후분포 N(%.3f, %.3f)" % (logpx, post_m, post_v))
rows = []
for name, m, v in qs:
    rec, klp, L, klpost = elbo_parts(m, v)
    rows.append((name, rec, klp, L, klpost))
    print("      %s  재구성 %.4f  KL(q||p(z)) %.4f  L %.4f  KL(q||p(z|x)) %.4f  L+KL = %.4f"
          % (name, rec, klp, L, klpost, L + klpost))

W, H = 820, 400
b = defs()
b += txt(20, 30, "식 (1) 을 숫자로 — 사후분포를 아는 1 차원 예시 (p(z)=N(0,1), p(x|z)=N(2z,1), x=3)", 15, anchor="start", weight="bold")
lo, hi = -4.2, -2.3
X0, X1 = 80, 760
def sx(v):
    return X0 + (v - lo) / (hi - lo) * (X1 - X0)
for t in [-4.0, -3.5, -3.0, -2.5]:
    b += line(sx(t), 70, sx(t), 330, LINE, 1)
    b += txt(sx(t), 350, "%.1f" % t, 11, fill=MUTED)
b += txt(420, 372, "로그 확률 (nat)", 12, fill=INK2)
b += line(sx(logpx), 62, sx(logpx), 335, INK, 2, dash="5 3")
b += txt(sx(logpx) + 6, 56, "log p(x) = %.3f" % logpx, 12, anchor="start", weight="bold")
b += txt(sx(logpx) + 6, 74, "(q 와 상관없이 하나)", 11, anchor="start", fill=INK2)
for k, (name, rec, klp, L, klpost) in enumerate(rows):
    y = 100 + 120 * k
    b += txt(X0, y - 8, name, 13, anchor="start", weight="bold", fill=REV if k == 0 else OK)
    b += '<rect x="%s" y="%s" width="%s" height="26" rx="4" fill="%s"/>' % (X0, y, sx(L) - X0, FWD_SOFT)
    b += txt(X0 + 8, y + 18, "L = %.3f" % L, 12, anchor="start", fill=FWD, weight="bold")
    if klpost > 1e-9:
        b += '<rect x="%s" y="%s" width="%s" height="26" rx="4" fill="%s"/>' % (sx(L), y, sx(logpx) - sx(L), REV_SOFT)
        b += txt((sx(L) + sx(logpx)) / 2, y + 18, "KL(q‖p(z|x)) = %.3f" % klpost, 12, fill=REV, weight="bold")
    else:
        b += txt(sx(logpx) - 8, y + 18, "KL(q‖p(z|x)) = 0 → L 이 log p(x) 에 닿는다", 12, anchor="end", fill=OK, weight="bold")
    b += txt(X0, y + 50, "L 을 식 (3) 으로 가르면: 재구성 E[log p(x|z)] = %.3f,  KL(q‖p(z)) = %.3f,  %.3f − %.3f = %.3f"
             % (rec, klp, rec, klp, L), 12, anchor="start", fill=INK2)
b += txt(420, 392, "q 를 바꿔도 log p(x) 는 그대로다 — 그래서 L 을 올리는 일이 곧 KL(q‖사후분포) 를 줄이는 일이다", 11, fill=MUTED)
svg("fig03_elbo", W, H, b, "변분 하한 분해의 숫자 예시")


# ── 그림 4. 소박한 추정량 대 재매개변수화 추정량의 분산 ─────────────────────────
# q = N(μ, 1), f(z) = z²,  참 기울기 d/dμ E[f] = 2μ.
# 점수 함수(소박한) 추정량 g = f(z)(z-μ),  분산 = μ⁴ + 14μ² + 15  (정규분포 적률로 계산)
# 재매개변수화 추정량  g = f'(μ+ε) = 2(μ+ε),  분산 = 4
def var_score(mu):
    return mu ** 4 + 14 * mu ** 2 + 15
VAR_RP = 4.0
n_mc = 200000
for mu in (0.0, 1.0, 3.0):
    s1 = s2 = r1 = r2 = 0.0
    for _ in range(n_mc):
        e = random.gauss(0, 1)
        g = (mu + e) ** 2 * e
        r = 2 * (mu + e)
        s1 += g; s2 += g * g; r1 += r; r2 += r * r
    vs = s2 / n_mc - (s1 / n_mc) ** 2
    vr = r2 / n_mc - (r1 / n_mc) ** 2
    print("  [4] μ=%.0f  점수 추정량 분산 식 %.1f / 몬테카를로 %.1f,  재매개변수화 식 %.1f / 몬테카를로 %.2f,  배수 %.1f"
          % (mu, var_score(mu), vs, VAR_RP, vr, var_score(mu) / VAR_RP))

W, H = 820, 380
b = defs()
b += txt(20, 30, "같은 기울기를 두 방법으로 추정할 때 표본 하나의 분산 (q=N(μ,1), f(z)=z², 내가 붙인 예시)", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 90, 520, 310, 60
ylo, yhi = 0, 3          # log10 분산
def px(mu):
    return PX0 + mu / 3.0 * (PX1 - PX0)
def py(v):
    return PY0 - (math.log10(v) - ylo) / (yhi - ylo) * (PY0 - PY1)
for e in range(0, 4):
    b += line(PX0, py(10 ** e), PX1, py(10 ** e), LINE, 1)
    b += txt(PX0 - 8, py(10 ** e) + 4, fmt(10 ** e), 11, anchor="end", fill=MUTED)
for m in range(0, 4):
    b += txt(px(m), PY0 + 18, "%d" % m, 11, fill=MUTED)
b += txt((PX0 + PX1) / 2, PY0 + 38, "μ (q 의 평균)", 12, fill=INK2)
b += txt(PX0 + 8, 50, "분산 (로그 눈금)", 12, fill=INK2, anchor="start")
b += polyline([(px(m / 20.0), py(var_score(m / 20.0))) for m in range(61)], NO, 2.4)
b += polyline([(px(0), py(VAR_RP)), (px(3), py(VAR_RP))], OK, 2.4)
b += txt(px(2.2), py(var_score(2.2)) - 10, "소박한 추정량 μ⁴+14μ²+15", 12, fill=NO, anchor="end", weight="bold")
b += txt(px(3), py(VAR_RP) - 8, "재매개변수화 4", 12, fill=OK, anchor="end", weight="bold")
for m in (0, 1, 3):
    b += circ(px(m), py(var_score(m)), 4, NO, NO)
b += box(550, 60, 250, 250, fill=NODE, stroke=LINE)
b += txt(565, 86, "배수 (소박한 / 재매개변수화)", 12, anchor="start", weight="bold")
for k, m in enumerate((0, 1, 3)):
    b += txt(565, 120 + 34 * k, "μ = %d:  %d / 4 = %.2f 배" % (m, var_score(m), var_score(m) / VAR_RP), 12, anchor="start")
b += txt(565, 238, "두 추정량의 평균은 둘 다 2μ 다.", 11, anchor="start", fill=INK2)
b += txt(565, 256, "다른 것은 흔들림뿐이다.", 11, anchor="start", fill=INK2)
b += txt(565, 284, "몬테카를로 20 만 번으로 확인", 11, anchor="start", fill=MUTED)
svg("fig04_estimator_variance", W, H, b, "두 기울기 추정량의 분산 비교")


# ── 그림 5. 재매개변수화 — 무작위를 바깥으로 빼낸다 ────────────────────────────
W, H = 820, 360
b = defs()
b += txt(20, 30, "재매개변수화 — 뽑기를 φ 밖으로 옮기면 기울기가 μ, σ 까지 내려간다", 15, anchor="start", weight="bold")
for side, ox in ((0, 20), (1, 420)):
    b += box(ox, 50, 380, 290, fill="none", stroke=LINE)
b += txt(210, 74, "원래 꼴: z ~ N(μ, σ²)", 13, weight="bold", fill=NO)
b += box(60, 250, 120, 40, fill=FWD_SOFT, stroke=FWD); b += txt(120, 275, "x", 14, style="italic")
b += box(60, 170, 120, 40, fill=REV_SOFT, stroke=REV); b += txt(120, 195, "μ, σ = 부호기_φ(x)", 12)
b += line(120, 248, 120, 212, INK2, 1.4, marker="ai")
b += '<polygon points="120,100 160,125 120,150 80,125" fill="%s" stroke="%s" stroke-width="1.6"/>' % (CODE_SOFT, NO)
b += txt(120, 130, "z 뽑기", 12, fill=NO, weight="bold")
b += line(120, 168, 120, 152, INK2, 1.4, marker="ai")
b += txt(250, 110, "뽑기 마디는 미분이 안 된다", 12, fill=NO, anchor="start")
b += txt(250, 128, "∂z/∂μ 가 정의되지 않는다", 12, fill=NO, anchor="start")
b += line(240, 160, 180, 160, NO, 1.6, dash="4 3", marker="an")
b += txt(250, 165, "기울기가 여기서 끊긴다", 12, fill=NO, anchor="start")
# 오른쪽
b += txt(610, 74, "재매개변수화: z = μ + σ ⊙ ε,  ε ~ N(0, I)", 13, weight="bold", fill=OK)
b += box(450, 250, 120, 40, fill=FWD_SOFT, stroke=FWD); b += txt(510, 275, "x", 14, style="italic")
b += box(450, 170, 120, 40, fill=REV_SOFT, stroke=REV); b += txt(510, 195, "μ, σ = 부호기_φ(x)", 12)
b += line(510, 248, 510, 212, INK2, 1.4, marker="ai")
b += '<polygon points="690,165 730,190 690,215 650,190" fill="%s" stroke="%s" stroke-width="1.6"/>' % (NODE, INK2)
b += txt(690, 195, "ε 뽑기", 12, fill=INK2, weight="bold")
b += box(560, 100, 110, 40, fill=CODE_SOFT, stroke=CODE); b += txt(615, 125, "z = μ + σ ε", 12, weight="bold")
b += line(520, 168, 580, 142, INK2, 1.4, marker="ai")
b += line(680, 166, 650, 142, INK2, 1.4, marker="ai")
b += path("M600,98 Q560,70 525,168", OK, sw=1.8, dash="5 3", marker="ao")
b += txt(560, 238, "∂z/∂μ = 1,  ∂z/∂σ = ε", 12, fill=OK, weight="bold")
b += txt(610, 312, "무작위는 φ 와 상관없는 ε 에만 남는다", 12, fill=INK2)
b += txt(610, 330, "예: μ=2, σ=0.5, ε=1.2 이면 z=2.6,  ∂z/∂σ=1.2", 12, fill=INK2)
svg("fig05_reparam", W, H, b, "재매개변수화 전후의 계산 그래프")


# ── 그림 6. 어떤 분포에 쓸 수 있는가 — 세 갈래 ─────────────────────────────────
# 첫째 갈래의 예시: 지수분포(λ=1)의 역누적분포 z = -ln(1-ε), ε ~ U(0,1)
eps_ex = [0.1, 0.5, 0.9]
print("  [6] 지수분포 역누적분포: " + ", ".join("ε=%.1f → z=%.3f" % (e, -math.log(1 - e)) for e in eps_ex))
W, H = 820, 360
b = defs()
b += txt(20, 30, "g_φ(ε) 를 고르는 세 갈래 (논문 2.4절)", 15, anchor="start", weight="bold")
# 1. 역누적분포 그림
b += box(20, 50, 260, 290, fill="none", stroke=LINE)
b += txt(150, 74, "1. 역누적분포가 닫힌 꼴", 13, weight="bold", fill=FWD)
GX0, GX1, GY0, GY1 = 55, 260, 270, 100
def gx(z):
    return GX0 + z / 3.0 * (GX1 - GX0)
def gy(p):
    return GY0 - p * (GY0 - GY1)
b += line(GX0, GY0, GX1, GY0, INK2, 1); b += line(GX0, GY0, GX0, GY1 - 5, INK2, 1)
b += polyline([(gx(z / 20.0), gy(1 - math.exp(-z / 20.0))) for z in range(61)], FWD, 2)
for e in eps_ex:
    z = -math.log(1 - e)
    b += line(GX0, gy(e), gx(z), gy(e), REV, 1, dash="3 2")
    b += line(gx(z), gy(e), gx(z), GY0, REV, 1, dash="3 2", marker="ar")
    b += txt(GX0 - 4, gy(e) + 4, "%.1f" % e, 10, anchor="end", fill=REV)
    b += txt(gx(z), GY0 + 14, "%.2f" % z, 10, fill=REV)
b += txt(150, 305, "지수분포: ε~U(0,1) → z = −ln(1−ε)", 11, fill=INK2)
b += txt(150, 322, "세로축 ε 에서 가로축 z 로 옮긴다", 11, fill=INK2)
# 2. 위치-척도
b += box(290, 50, 250, 290, fill="none", stroke=LINE)
b += txt(415, 74, "2. 위치-척도 족", 13, weight="bold", fill=REV)
b += txt(415, 110, "z = 위치 + 척도 · ε", 14, weight="bold")
b += txt(415, 135, "ε 는 위치 0 · 척도 1 인 표준형", 12, fill=INK2)
for k, nm in enumerate(["가우스 (이 논문이 쓰는 것)", "라플라스", "스튜던트 t", "로지스틱", "균등", "삼각"]):
    b += txt(415, 170 + 24 * k, nm, 12, fill=OK if k == 0 else INK)
# 3. 합성
b += box(550, 50, 250, 290, fill="none", stroke=LINE)
b += txt(675, 74, "3. 합성", 13, weight="bold", fill=CODE)
comp = [("로그 정규", "정규 변수의 exp"), ("감마", "지수 변수의 합"), ("디리클레", "감마 변수의 가중 합"),
        ("베타 · 카이제곱 · F", "같은 식으로")]
for k, (a, c) in enumerate(comp):
    b += txt(675, 115 + 48 * k, a, 13, weight="bold")
    b += txt(675, 133 + 48 * k, c, 11, fill=INK2)
b += txt(675, 322, "셋 다 안 되면 역누적분포 근사", 11, fill=MUTED)
svg("fig06_three_families", W, H, b, "재매개변수화가 가능한 분포 세 갈래")


# ── 그림 7. 논문 3절의 VAE — MNIST, 은닉 500, 잠재 20 ─────────────────────────
def vae_params(D, Hh, J):
    """부록 C 의 식 (11)(12) 대로 센다. 부호기: 가우스 MLP, 복호기: 베르누이 MLP, 은닉층 하나."""
    enc = D * Hh + Hh + 2 * (Hh * J + J)          # W3,b3 / W4,b4 / W5,b5
    dec = J * Hh + Hh + Hh * D + D                # W1,b1 / W2,b2
    return enc, dec


def ae_params(sizes):
    full = sizes + sizes[-2::-1]
    return sum(a * c for a, c in zip(full[:-1], full[1:])) + sum(full[1:])


print("  [7] VAE 파라미터 수 (MNIST 784 픽셀, 은닉 500):")
for J in (3, 5, 10, 20, 200):
    e, d = vae_params(784, 500, J)
    print("      Nz=%-3d 부호기 %s + 복호기 %s = %s" % (J, fmt(e), fmt(d), fmt(e + d)))
e20, d20 = vae_params(784, 500, 20)
ae30 = ae_params([784, 1000, 500, 250, 30])
print("      비교: 2006 오토인코더 MNIST 784-1000-500-250-30 = %s  (VAE Nz=20 의 %.2f 배)"
      % (fmt(ae30), ae30 / float(e20 + d20)))

W, H = 820, 400
b = defs()
b += txt(20, 30, "논문 3절의 VAE (MNIST, 은닉 500, 잠재 Nz=20) — 층 하나짜리 부호기와 복호기", 15, anchor="start", weight="bold")
cy = 190
def slab(x, n, col, stroke, lab, sub=None, hmax=180):
    h = 20 + hmax * math.sqrt(n / 784.0)
    s = box(x - 16, cy - h / 2, 32, h, fill=col, stroke=stroke)
    s += txt(x, cy + h / 2 + 18, lab, 12, weight="bold")
    if sub:
        s += txt(x, cy + h / 2 + 34, sub, 11, fill=INK2)
    return s
b += slab(60, 784, "#C9D2D6", INK, "x", "784")
b += slab(170, 500, REV_SOFT, REV, "h", "500 tanh")
b += box(254, 105, 32, 45, fill=REV_SOFT, stroke=REV); b += txt(270, 98, "μ", 13, weight="bold", fill=REV)
b += box(254, 230, 32, 45, fill=REV_SOFT, stroke=REV); b += txt(270, 295, "log σ²", 12, weight="bold", fill=REV)
b += txt(270, 132, "20", 11); b += txt(270, 257, "20", 11)
b += line(78, cy, 152, cy, REV, 1.6, marker="ar")
b += line(188, cy - 20, 252, 130, REV, 1.6, marker="ar")
b += line(188, cy + 20, 252, 250, REV, 1.6, marker="ar")
b += circ(390, 60, 18, NODE, INK2); b += txt(390, 65, "ε", 14, style="italic")
b += txt(420, 64, "~ N(0, I)", 11, anchor="start", fill=INK2)
b += box(370, cy - 40, 40, 80, fill=CODE_SOFT, stroke=CODE, sw=1.8)
b += txt(390, cy + 5, "z", 16, weight="bold", style="italic")
b += txt(390, cy + 60, "20", 12, weight="bold")
b += txt(390, cy + 76, "μ + σ ⊙ ε", 11, fill=INK2)
b += line(288, 128, 368, cy - 15, INK2, 1.4, marker="ai")
b += line(288, 252, 368, cy + 15, INK2, 1.4, marker="ai")
b += line(390, 80, 390, cy - 42, INK2, 1.4, marker="ai")
b += slab(520, 500, FWD_SOFT, FWD, "h", "500 tanh")
b += slab(640, 784, FWD_SOFT, FWD, "y", "784 sigmoid")
b += line(412, cy, 502, cy, FWD, 1.6, marker="af")
b += line(538, cy, 622, cy, FWD, 1.6, marker="af")
b += txt(165, 60, "부호기 qφ(z|x) — 가우스 MLP, 식 (12)", 12, weight="bold", fill=REV)
b += txt(625, 60, "복호기 pθ(x|z) — 베르누이 MLP, 식 (11)", 12, weight="bold", fill=FWD)
b += box(690, 110, 115, 160, fill=NODE, stroke=LINE)
b += txt(748, 132, "파라미터", 12, weight="bold")
b += txt(748, 156, "부호기", 11, fill=REV); b += txt(748, 173, fmt(e20), 12, weight="bold")
b += txt(748, 197, "복호기", 11, fill=FWD); b += txt(748, 214, fmt(d20), 12, weight="bold")
b += txt(748, 238, "합계", 11); b += txt(748, 255, fmt(e20 + d20), 12, weight="bold")
b += txt(410, 360, "목표 = 재구성 Σ xᵢ log yᵢ + (1−xᵢ) log(1−yᵢ)  −  KL(q(z|x) ‖ N(0, I))   … 식 (10)", 12, fill=INK)
b += txt(410, 384, "2006 오토인코더(784-1000-500-250-30)는 %s 개 — 이 VAE 의 %.1f 배다" % (fmt(ae30), ae30 / float(e20 + d20)), 11, fill=MUTED)
svg("fig07_vae_arch", W, H, b, "VAE 구조와 파라미터 수")


# ── 그림 8. KL 항 — 부록 B 의 닫힌 꼴 ──────────────────────────────────────────
def kl1(mu, sd):
    return 0.5 * (mu ** 2 + sd ** 2 - 1 - math.log(sd ** 2))
ex_mu, ex_sd = 1.0, 0.5
mc = sum(math.log(NormalDist(ex_mu, ex_sd).pdf(z)) - math.log(NormalDist(0, 1).pdf(z))
         for z in (random.gauss(ex_mu, ex_sd) for _ in range(n_mc))) / n_mc
print("  [8] KL(N(1, 0.5²) || N(0,1)) 닫힌 꼴 %.4f,  몬테카를로 %.4f" % (kl1(ex_mu, ex_sd), mc))
W, H = 820, 380
b = defs()
b += txt(20, 30, "차원 하나의 KL(N(μ, σ²) ‖ N(0, 1)) = ½(μ² + σ² − 1 − log σ²)   (부록 B)", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 80, 520, 320, 70
def kx(s):
    return PX0 + s / 2.0 * (PX1 - PX0)
def ky(v):
    return PY0 - v / 3.0 * (PY0 - PY1)
for v in range(0, 4):
    b += line(PX0, ky(v), PX1, ky(v), LINE, 1)
    b += txt(PX0 - 8, ky(v) + 4, "%d" % v, 11, anchor="end", fill=MUTED)
for s in (0.5, 1.0, 1.5, 2.0):
    b += txt(kx(s), PY0 + 18, "%.1f" % s, 11, fill=MUTED)
b += txt((PX0 + PX1) / 2, PY0 + 40, "σ (부호기가 낸 표준편차)", 12, fill=INK2)
b += txt(PX0 - 45, (PY0 + PY1) / 2, "nat", 12, fill=INK2)
for mu, col in ((0, OK), (1, FWD), (2, REV)):
    pts = [(kx(s), ky(kl1(mu, s))) for s in [0.12 + i * 0.02 for i in range(95)] if kl1(mu, s) <= 3.05]
    b += polyline(pts, col, 2.4)
    b += txt(kx(1.93), ky(kl1(mu, 1.93)) - 8, "μ = %d" % mu, 12, fill=col, anchor="end", weight="bold")
b += circ(kx(ex_sd), ky(kl1(ex_mu, ex_sd)), 5, FWD, FWD)
b += txt(kx(ex_sd) + 10, ky(kl1(ex_mu, ex_sd)) + 4, "μ=1, σ=0.5 → %.3f" % kl1(ex_mu, ex_sd), 11, anchor="start", fill=FWD, weight="bold")
b += circ(kx(1.0), ky(0), 5, OK, OK)
b += box(550, 70, 250, 250, fill=NODE, stroke=LINE)
b += txt(565, 96, "읽는 법", 13, anchor="start", weight="bold")
lines_ = ["0 이 되는 자리는 μ=0, σ=1 하나 —",
          "곧 부호기가 사전분포를 그대로 낼 때다.",
          "",
          "σ 를 0 쪽으로 줄이면(점 하나로",
          "누르면) −log σ² 때문에 끝없이 커진다.",
          "오토인코더처럼 점을 내면 벌점이 무한이다.",
          "",
          "μ 를 멀리 두면 ½μ² 만큼 붙는다.",
          "코드를 원점 가까이 모으는 힘이다."]
for k, t in enumerate(lines_):
    b += txt(565, 124 + 20 * k, t, 11, anchor="start", fill=INK2)
svg("fig08_kl_term", W, H, b, "KL 항의 모양")


# ── 그림 9. 알고리즘 1 — 미니배치 AEVB ─────────────────────────────────────────
M_, L_ = 100, 1
N_ex = 50000
per_million = (20, 40)
samples = 1e8
hrs = [samples / 1e6 * m / 60.0 for m in per_million]
print("  [9] 표본 10^8 개를 보는 데 %.0f ~ %.0f 시간 (백만 개당 %d~%d 분),  N=%s 이면 %.0f 바퀴"
      % (hrs[0], hrs[1], per_million[0], per_million[1], fmt(N_ex), samples / N_ex))
W, H = 820, 360
b = defs()
b += txt(20, 30, "알고리즘 1 — 미니배치 하나로 하한 전체의 기울기를 추정해 θ 와 φ 를 함께 올린다", 15, anchor="start", weight="bold")
steps = [("1", "미니배치 X_M 뽑기", "M = %d 장" % M_, FWD_SOFT, FWD),
         ("2", "잡음 ε 뽑기", "데이터 점마다 L = %d 개" % L_, NODE, INK2),
         ("3", "L̃ 의 기울기 g", "(N/M)·Σ L̃(θ,φ;x⁽ⁱ⁾), 식 (8)", CODE_SOFT, CODE),
         ("4", "θ, φ 갱신", "Adagrad (+ 작은 가중치 감쇠)", REV_SOFT, REV)]
for k, (n, t, d, f, s) in enumerate(steps):
    x = 30 + 195 * k
    b += box(x, 80, 170, 90, fill=f, stroke=s, sw=1.6)
    b += txt(x + 18, 104, n, 14, weight="bold", fill=s)
    b += txt(x + 85, 124, t, 13, weight="bold")
    b += txt(x + 85, 148, d, 11, fill=INK2)
    if k < 3:
        b += line(x + 172, 125, x + 193, 125, INK2, 1.6, marker="ai")
b += path("M%s,172 Q%s,225 %s,172" % (30 + 195 * 3 + 85, 420, 115), INK2, sw=1.6, dash="5 3", marker="ai")
b += txt(420, 222, "θ, φ 가 수렴할 때까지 되풀이", 12, fill=INK2)
b += box(30, 250, 760, 90, fill=NODE, stroke=LINE)
b += txt(50, 274, "N/M 을 곱하는 이유: 미니배치 100 장의 평균을 데이터 전체의 합으로 키운다. 예: N=50,000 이면 500 을 곱한다", 12, anchor="start")
b += txt(50, 298, "L = 1 로 충분했다는 것은 논문이 적은 관찰이다 — 조건은 「M 이 충분히 크면(예: 100)」", 12, anchor="start")
b += txt(50, 322, "계산량: 논문 그림 2 캡션이 백만 개당 20~40 분이라 적는다. 10⁸ 개면 %.0f~%.0f 시간이다 (40 GFLOPS Xeon CPU)" % (hrs[0], hrs[1]), 12, anchor="start", fill=INK2)
svg("fig09_algorithm", W, H, b, "미니배치 AEVB 알고리즘 흐름")


# ── 그림 10. 결과 1 — 논문 그림 2 의 끝 값(300 dpi 로 눈금을 읽은 값) ─────────────
# 각 판의 오른쪽 끝에서 읽었다. MNIST 는 눈금 10 이라 ±2, Frey Face 는 눈금 200 이라 ±30 으로 읽는다.
# (Nz, AEVB 학습, AEVB 시험, 깨어남-잠 학습, 깨어남-잠 시험)
MNIST_END = [(3, -128, -133.5, -139, -137.5), (5, -114.5, -118.5, -121, -120.5),
             (10, -99, -103, -105.5, -106), (20, -99, -101, -103, -103.5), (200, -98.5, -100, -103, -102.5)]
FREY_END = [(2, 930, 870, 580, 570), (5, 1230, 1110, 580, 570), (10, 1460, 1310, 580, 570), (20, 1490, 1310, 580, 570)]
print("  [10] 학습 - 시험 간격 (AEVB, 눈금 읽기):")
print("       MNIST " + ", ".join("Nz=%d: %.1f" % (r[0], r[1] - r[2]) for r in MNIST_END))
print("       Frey  " + ", ".join("Nz=%d: %d" % (r[0], r[1] - r[2]) for r in FREY_END))
W, H = 820, 470
b = defs()
b += txt(20, 30, "논문 그림 2 의 오른쪽 끝 값 — 데이터 점당 하한 L (높을수록 좋다, 눈금을 읽은 값)", 15, anchor="start", weight="bold")
def dotpanel(b, x0, y0, w, h, rows, lo, hi, step, title, unit_note, dz_label):
    b += box(x0, y0, w, h, fill="none", stroke=LINE)
    b += txt(x0 + 12, y0 + 22, title, 13, anchor="start", weight="bold")
    b += txt(x0 + w - 12, y0 + 22, unit_note, 11, anchor="end", fill=MUTED)
    ax0, ax1 = x0 + 80, x0 + w - 20
    def X(v):
        return ax0 + (v - lo) / float(hi - lo) * (ax1 - ax0)
    v = lo
    while v <= hi + 1e-9:
        b += line(X(v), y0 + 38, X(v), y0 + h - 30, LINE, 1)
        b += txt(X(v), y0 + h - 12, "%g" % v, 10, fill=MUTED)
        v += step
    rh = (h - 80) / float(len(rows))
    for k, r in enumerate(rows):
        y = y0 + 50 + rh * k + rh / 2
        b += txt(x0 + 12, y + 4, "%s=%d" % (dz_label, r[0]), 12, anchor="start")
        b += line(X(min(r[1:])), y, X(max(r[1:])), y, LINE, 3)
        for val, col, filled, dy in ((r[1], S_AEVB, True, -5), (r[2], S_AEVB, False, 5),
                                     (r[3], S_WS, True, -5), (r[4], S_WS, False, 5)):
            b += circ(X(val), y + dy, 5, col if filled else BG, col, 2)
    return b
b = dotpanel(b, 20, 50, 385, 360, MNIST_END, -145, -95, 10, "MNIST (은닉 500)", "읽기 ±2", "Nz")
b = dotpanel(b, 415, 50, 385, 360, FREY_END, 400, 1600, 200, "Frey Face (은닉 200)", "읽기 ±30", "Nz")
lx = 40
for lab, col, filled in (("AEVB 학습", S_AEVB, True), ("AEVB 시험", S_AEVB, False),
                         ("깨어남-잠 학습", S_WS, True), ("깨어남-잠 시험", S_WS, False)):
    b += circ(lx, 433, 5, col if filled else BG, col, 2)
    b += txt(lx + 10, 437, lab, 11, anchor="start")
    lx += 130
b += txt(20, 460, "학습-시험 간격(AEVB): MNIST 는 Nz 가 3→200 으로 커질 때 %.1f→%.1f 로 준다. Frey Face 는 Nz 2→20 에서 %d→%d 로 는다"
         % (MNIST_END[0][1] - MNIST_END[0][2], MNIST_END[-1][1] - MNIST_END[-1][2],
            FREY_END[0][1] - FREY_END[0][2], FREY_END[-1][1] - FREY_END[-1][2]), 11, anchor="start", fill=INK2)
svg("fig10_lower_bound", W, H, b, "논문 그림 2 끝 값의 점 그림")


# ── 그림 11. 결과 2 — 논문 그림 3 의 끝 값(추정 주변 로그 가능도, Nz=3, 은닉 100) ─────
# 왼쪽 판(N=1000) 눈금 10 → ±2, 오른쪽 판(N=50000) 눈금 5 → ±1
# (방법, 학습, 시험)
F3 = {1000: [("AEVB", -109, -143.5), ("깨어남-잠", -125.5, -145), ("몬테카를로 EM", -109, -141.5)],
      50000: [("AEVB", -131, -138), ("깨어남-잠", -136.8, -141), ("몬테카를로 EM", -147, -148.5)]}
W, H = 820, 360
b = defs()
b += txt(20, 30, "논문 그림 3 의 오른쪽 끝 값 — 추정 주변 로그 가능도 (Nz=3, 은닉 100, 눈금을 읽은 값)", 15, anchor="start", weight="bold")
cols = {"AEVB": S_AEVB, "깨어남-잠": S_WS, "몬테카를로 EM": S_MCEM}
for p, (nt, rows) in enumerate(sorted(F3.items())):
    x0 = 20 + 395 * p
    b += box(x0, 50, 385, 250, fill="none", stroke=LINE)
    b += txt(x0 + 12, 72, "학습 데이터 N = %s" % fmt(nt), 13, anchor="start", weight="bold")
    b += txt(x0 + 373, 72, "읽기 ±%d" % (2 if nt == 1000 else 1), 11, anchor="end", fill=MUTED)
    lo, hi = -150, -105
    ax0, ax1 = x0 + 110, x0 + 365
    def X(v):
        return ax0 + (v - lo) / float(hi - lo) * (ax1 - ax0)
    for v in range(lo, hi + 1, 10):
        b += line(X(v), 88, X(v), 262, LINE, 1)
        b += txt(X(v), 280, "%d" % v, 10, fill=MUTED)
    for k, (m, tr, te) in enumerate(rows):
        y = 115 + 55 * k
        b += txt(x0 + 12, y + 4, m, 12, anchor="start", fill=cols[m], weight="bold")
        b += line(X(te), y, X(tr), y, LINE, 3)
        b += circ(X(tr), y, 5, cols[m], cols[m], 2)
        b += circ(X(te), y, 5, BG, cols[m], 2)
b += circ(40, 322, 5, INK2, INK2, 2); b += txt(50, 326, "학습", 11, anchor="start")
b += circ(110, 322, 5, BG, INK2, 2); b += txt(120, 326, "시험", 11, anchor="start")
b += txt(180, 326, "N=1000 의 시험은 몬테카를로 EM(−141.5) 이 AEVB(−143.5) 위에 있다. 논문은 이 칸을 말하지 않는다", 11, anchor="start", fill=INK2)
b += txt(180, 346, "N=50000 의 몬테카를로 EM 은 오른쪽 끝에서도 오르는 중이다(도달한 값이 아니다)", 11, anchor="start", fill=INK2)
svg("fig11_marginal_ll", W, H, b, "논문 그림 3 끝 값의 점 그림")


# ── 그림 12. 논문 그림 4 를 만드는 법 — 단위 정사각형 격자를 가우스 역누적분포로 ─────
nd = NormalDist()
n_grid = 10
us = [(k + 0.5) / n_grid for k in range(n_grid)]
zs = [nd.inv_cdf(u) for u in us]
print("  [12] 격자 %d 칸: u=%.2f..%.2f → z=%.3f..%.3f,  가운데 칸 간격 %.3f,  끝 칸 간격 %.3f"
      % (n_grid, us[0], us[-1], zs[0], zs[-1], zs[5] - zs[4], zs[1] - zs[0]))
W, H = 820, 330
b = defs()
b += txt(20, 30, "논문 그림 4 의 좌표 — (0,1) 의 고른 간격을 Φ⁻¹ 로 z 에 옮긴다 (한 축, %d 칸은 내가 고른 예)" % n_grid, 15, anchor="start", weight="bold")
UX0, UX1 = 80, 740
def ux(u):
    return UX0 + u * (UX1 - UX0)
def zx(z):
    return UX0 + (z + 2.0) / 4.0 * (UX1 - UX0)
b += line(UX0, 90, UX1, 90, INK2, 1.4)
b += txt(UX0 - 10, 94, "u", 14, anchor="end", style="italic")
b += txt(UX0, 76, "0", 11, fill=MUTED); b += txt(UX1, 76, "1", 11, fill=MUTED)
b += line(UX0, 230, UX1, 230, INK2, 1.4)
b += txt(UX0 - 10, 234, "z", 14, anchor="end", style="italic")
for zt in (-2, -1, 0, 1, 2):
    b += txt(zx(zt), 255, "%d" % zt, 11, fill=MUTED)
for u, z in zip(us, zs):
    b += line(ux(u), 95, zx(z), 225, FWD, 1, op=0.6)
    b += circ(ux(u), 90, 4, REV, REV)
    b += circ(zx(z), 230, 4, CODE, CODE)
b += txt(410, 285, "위: 고른 간격 %.2f.  아래: 가운데 칸 사이 %.3f, 끝 칸 사이 %.3f — 사전분포의 밀도가 높은 가운데를 촘촘히 훑는다"
         % (us[1] - us[0], zs[5] - zs[4], zs[1] - zs[0]), 12, fill=INK2)
b += txt(410, 308, "두 축을 이렇게 옮긴 격자의 칸마다 복호기의 pθ(x|z) 를 그린 것이 논문 그림 4 다", 12, fill=INK2)
svg("fig12_manifold_grid", W, H, b, "격자 좌표를 가우스 역누적분포로 옮기기")


# ── 그림 13. 오토인코더(2006) 대 VAE(2014) ─────────────────────────────────────
W, H = 820, 470
b = defs()
b += txt(20, 30, "오토인코더(2006) 와 VAE(2014) — 같은 모양, 다른 목표", 15, anchor="start", weight="bold")
rows = [("부호기가 내는 것", "점 z", "분포 N(μ, σ²) 의 μ, σ"),
        ("코드 공간", "정한 것이 없다", "사전분포 N(0, I)"),
        ("학습 목표", "재구성 오차", "변분 하한 = 재구성 − KL"),
        ("코드의 벌점", "없다", "KL(q(z|x) ‖ N(0, I))"),
        ("망 깊이 (MNIST)", "784-1000-500-250-30 거울상", "784-500-Nz 와 Nz-500-784"),
        ("파라미터 (MNIST)", "%s" % fmt(ae30), "%s (Nz=20)" % fmt(e20 + d20)),
        ("초기화", "RBM 을 쌓아 사전학습", "N(0, 0.01) 무작위"),
        ("새 데이터 만들기", "길이 없다", "z ~ N(0, I) 를 복호기에"),
        ("보고한 지표", "재구성 제곱 오차", "하한 L, 추정 주변 가능도")]
cw = [220, 270, 290]
x0, y0 = 20, 55
b += box(x0, y0, sum(cw), 36, fill="#DDE3E0", stroke=LINE, rx=4)
for k, t in enumerate(["", "오토인코더 2006", "VAE 2014"]):
    b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y0 + 23, t, 13, weight="bold", fill=[INK, FWD, REV][k])
for r, row in enumerate(rows):
    y = y0 + 36 + 38 * r
    b += box(x0, y, sum(cw), 38, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    for k, t in enumerate(row):
        b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y + 24, t, 12, weight="bold" if k == 0 else None)
b += txt(410, 458, "망 깊이가 다른 것은 두 논문이 고른 설정이다. VAE 가 깊은 망을 못 쓴다는 뜻이 아니다(논문 7절이 깊은 망을 다음 일로 꼽는다)", 11, fill=MUTED)
svg("fig13_ae_vs_vae", W, H, b, "오토인코더와 VAE 비교 표")


# ── 그림 14. 계보 — 어디서 받아 어디로 넘기는가 ─────────────────────────────
W, H = 820, 380
b = defs()
b += txt(20, 30, "계보 — 앞 편의 한계를 받아 다음 편에 넘긴다", 15, anchor="start", weight="bold")
chainL = [("오토인코더 2006", "코드에 분포가 없다", FWD_SOFT, FWD),
          ("VAE 2014", "코드에 분포를 준다", CODE_SOFT, CODE),
          ("GAN (다음)", "가능도 없이 배운다", REV_SOFT, REV),
          ("DDPM 2020 (읽음)", "같은 하한, 많은 층", REV_SOFT, REV)]
for k, (t, d, f, s) in enumerate(chainL):
    x = 25 + 200 * k
    b += box(x, 60, 170, 60, fill=f, stroke=s, sw=1.6)
    b += txt(x + 85, 85, t, 13, weight="bold", fill=s)
    b += txt(x + 85, 105, d, 11, fill=INK2)
    if k < 3:
        b += line(x + 172, 90, x + 198, 90, INK2, 1.5, marker="ai")
hand = [(125, "받은 것: 코드 공간에서", "점을 골라 만들 길이 없다"),
        (325, "넘긴 것: 픽셀별 가능도를", "정해야 한다(베르누이·가우스)"),
        (525, "넘긴 것: q 가 대각 가우스", "하나 — 하한과의 틈")]
for x, l1, l2 in hand:
    b += txt(x + 100, 148, l1, 11, fill=INK)
    b += txt(x + 100, 164, l2, 11, fill=INK)
b += box(25, 200, 770, 160, fill=NODE, stroke=LINE)
b += txt(45, 226, "곁가지 — 이상 탐지로 가는 길 (논문은 이 쓰임을 적지 않는다. 내가 잇는 자리다)", 13, anchor="start", weight="bold", fill=REV)
b += txt(45, 252, "정상 데이터만으로 VAE 를 배우면 입력마다 하한 L(x) 가 나온다. 이것은 재구성 오차와 달리 「이 입력이 얼마나 그럴듯한가」의 하한이다", 12, anchor="start")
b += txt(45, 276, "점수가 둘로 갈린다 — 재구성 항(픽셀을 얼마나 되살리나) 과 KL 항(코드가 사전분포에서 얼마나 벗어났나)", 12, anchor="start")
b += txt(45, 300, "재구성 기반 이상 탐지의 긴장(잘 일반화하면 이상도 되살린다)은 그대로 남는다 — 목표가 여전히 시험 데이터의 L 을 올리는 것이다", 12, anchor="start")
b += txt(45, 324, "그리고 하한 L 은 log p(x) 보다 KL(q‖사후분포) 만큼 낮다. 그 틈이 입력마다 다르면 점수 순서가 틈 때문에 바뀔 수 있다", 12, anchor="start", fill=INK2)
b += txt(45, 348, "잴 방법은 이 노트 24절 D 에 적었다", 11, anchor="start", fill=MUTED)
svg("fig14_lineage", W, H, b, "계보와 이상 탐지로 가는 곁가지")

print("끝.")
