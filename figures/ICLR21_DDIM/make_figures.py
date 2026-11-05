# -*- coding: utf-8 -*-
"""DDIM 노트(Song · Meng · Ermon, Denoising Diffusion Implicit Models, ICLR 2021)의 그림 열여덟을 만든다.

색과 글꼴은 저장소의 앞선 노트 그림과 맞췄다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

계산으로 원문을 확인하는 그림이 여럿이다 — 3 · 4 · 5(식 12 · 16 의 계수, DDPM 선형 일정), 6 · 7(정리 1 의 계수를 다시 풀기),
8(부분열 규칙), 11(1000 걸음 기준 대비 배수), 13(그림 4 의 걸음당 시간), 14(재구성 오차의 RMSE), 15 · 16(식 13 · 15 의 계수 비와
sigma(t)), 17(1 차원 가우시안에서 닫힌 분산). 계산한 값은 돌릴 때 화면에도 찍는다.

원문 표의 수는 T1_C · T1_A · T2_S · T2_E · T3 상수에 옮겨 적었다(7 · 9 · 18 쪽). 원문 그림 4 의 값은 **PDF 안의 벡터 좌표에서
읽은 값**이고 F4_S · F4_C · F4_B 상수에 있다. 읽는 방법은 눈금 선 좌표로 축을 맞춘 뒤 표식 상자의 가운데를 값으로 바꾼 것이다.
가로축이 10, 20, 50, 100, 200, 500, 1000 으로 소수 첫째까지 떨어진다. 원문 그림 3 · 5 · 6 은 crop_paper_figures.py 가 잘라
png 로 둔다.
"""
import io, os, math, random

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"
NODE      = "#F6F7F5"
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — ViT · 이 논문 쪽
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — ResNet · 비교 상대 쪽
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 원문 표에 적힌 값
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"
OK_SOFT   = "#D6EEDD"
NO        = "#C0392B"
NO_SOFT   = "#F6D9D5"
PURP      = "#8E44AD"
PURP_SOFT = "#EADCF0"
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


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, t, size=12, fill=None, anchor="middle", weight=None, style=None):
    a = 'x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s"' % (x, y, size, fill or INK, anchor)
    if weight:
        a += ' font-weight="%s"' % weight
    if style:
        a += ' font-style="%s"' % style
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


def axes(x0, y0, x1, y1, xt, yt, fx, fy, xl=None, yl=None, xfmt="%g", yfmt="%g"):
    s = line(x0, y1, x1, y1, INK2, 1.2) + line(x0, y0, x0, y1, INK2, 1.2)
    for t in xt:
        lab = xfmt(t) if callable(xfmt) else xfmt % t
        s += line(fx(t), y1, fx(t), y1 + 4, INK2, 1) + txt(fx(t), y1 + 17, lab, 10, fill=MUTED)
    for t in yt:
        lab = yfmt(t) if callable(yfmt) else yfmt % t
        s += line(x0 - 4, fy(t), x0, fy(t), INK2, 1) + txt(x0 - 7, fy(t) + 4, lab, 10, fill=MUTED, anchor="end")
        s += line(x0, fy(t), x1, fy(t), LINE, 0.8, dash="2 3")
    if xl:
        s += txt((x0 + x1) / 2, y1 + 34, xl, 11, fill=INK2)
    if yl:
        s += txt(x0, y0 - 10, yl, 11, fill=INK2, anchor="start")
    return s


def lines_at(x, y, rows, size=12, gap=21, anchor="start"):
    s = ""
    for j, r in enumerate(rows):
        if isinstance(r, tuple):
            t, c = r[0], r[1]
            w = r[2] if len(r) > 2 else None
        else:
            t, c, w = r, INK2, None
        s += txt(x, y + gap * j, t, size, fill=c, anchor=anchor, weight=w)
    return s


def table(x, y, widths, rows, rowh=24, size=11.5, head_fill=None):
    """rows: 칸 문자열 또는 (문자열, 글자색, 굵기, 바탕색). 첫 줄은 머리."""
    s = ""
    total = sum(widths)
    for i, r in enumerate(rows):
        cx = x
        for j, c in enumerate(r):
            t, col, w, bg = c if isinstance(c, tuple) else (c, None, None, None)
            if i == 0 and bg is None:
                bg = head_fill or "#DDE3E0"
            if bg:
                s += '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (cx, y + i * rowh, widths[j], rowh, bg)
            s += txt(cx + widths[j] / 2, y + i * rowh + rowh / 2 + size * 0.36, t, size,
                     fill=col or (INK if i == 0 else INK2), weight=w or ("700" if i == 0 else None))
            cx += widths[j]
        s += line(x, y + (i + 1) * rowh, x + total, y + (i + 1) * rowh, LINE, 0.8)
    s += line(x, y, x + total, y, INK2, 1)
    return s


print("그림을 만든다 ->", OUT)

# ── 원문의 수 ───────────────────────────────────────────────────────────────
STEPS = [10, 20, 50, 100, 1000]
# 표 1 (7 쪽). 원문 기호: eta = 0, 0.2, 0.5, 1 과 sigma-hat
T1_C = {"0.0": [13.36, 6.84, 4.67, 4.16, 4.04], "0.2": [14.04, 7.11, 4.77, 4.25, 4.09],
        "0.5": [16.66, 8.35, 5.25, 4.46, 4.29], "1.0": [41.07, 18.36, 8.01, 5.78, 4.73],
        "hat": [367.43, 133.37, 32.72, 9.99, 3.17]}
T1_A = {"0.0": [17.33, 13.73, 9.17, 6.53, 3.51], "0.2": [17.66, 14.11, 9.51, 6.79, 3.64],
        "0.5": [19.86, 16.06, 11.01, 8.09, 4.28], "1.0": [33.12, 26.03, 18.48, 13.93, 5.98],
        "hat": [299.71, 183.83, 71.71, 45.20, 3.26]}
# 표 3 (18 쪽). 캡션: 1000 걸음 DDPM 은 Bedroom 6.36, Church 7.89
T3 = {"Bedroom": ([16.95, 8.89, 6.75, 6.62], [42.78, 22.77, 10.81, 6.81], 6.36),
      "Church": ([19.45, 12.47, 10.84, 10.58], [51.56, 23.37, 11.16, 8.27], 7.89)}
# 표 2 (9 쪽). 픽셀 [0, 1] 눈금의 차원당 제곱 오차, 캡션 「10^-4 로 반올림」
T2_S = [10, 20, 50, 100, 200, 500, 1000]
T2_E = [0.014, 0.0065, 0.0023, 0.0009, 0.0004, 0.0001, 0.0001]

# 그림 4 (8 쪽). **PDF 안의 벡터 좌표에서 읽은 값.** 표식 상자의 가운데를 눈금 선 좌표로 바꿨다.
# 가로축 값은 10, 20, 50, 100, 200, 500, 1000 으로 소수 첫째까지 떨어진다. 원문이 숫자로 적지 않은 값이다.
F4_S = [10, 20, 50, 100, 200, 500, 1000]
F4_C = [0.197, 0.386, 0.949, 1.978, 3.833, 9.437, 18.825]
F4_B = [10.156, 21.076, 47.118, 82.847, 165.694, 414.235, 828.469]


# ── 계산 ──────────────────────────────────────────────────────────────────
T = 1000
beta = [None] + [1e-4 + (0.02 - 1e-4) * (t - 1) / (T - 1) for t in range(1, T + 1)]
AB = [1.0]                      # 원문의 alpha_t (DDPM 의 alpha-bar_t), AB[0] = 1 은 원문 정의
for t in range(1, T + 1):
    AB.append(AB[-1] * (1 - beta[t]))


def lin(S):
    c = T / S
    return [int(math.floor(c * i + 1e-9)) for i in range(1, S + 1)]


def quad(S):
    c = T / S ** 2
    return [int(math.floor(c * i * i + 1e-9)) for i in range(1, S + 1)]


def walk(seq):
    """(t, 다음 자리 p) 를 큰 t 부터. 마지막은 p = 0."""
    out = []
    for i in range(len(seq) - 1, -1, -1):
        out.append((seq[i], seq[i - 1] if i > 0 else 0))
    return out


def s1(t, p):
    "eta = 1 의 sigma^2 (식 16)"
    return (1 - AB[p]) / (1 - AB[t]) * (1 - AB[t] / AB[p])


def shat(t, p):
    "sigma-hat^2"
    return 1 - AB[t] / AB[p]


def ve(t):
    "식 38 의 sigma(t)"
    return math.sqrt((1 - AB[t]) / AB[t])


def gamma_eq66(t):
    "부록 식 66 의 계수, sigma^2 = beta-tilde"
    bt = (1 - AB[t - 1]) / (1 - AB[t]) * beta[t]
    return beta[t] ** 2 / (2 * bt * (1 - beta[t]) * (1 - AB[t]))


def gamma_mine(t, s2):
    "식 30 을 바로 계산한 계수: c^2 (1 - a_t) / (2 s2 a_t)"
    c = math.sqrt(AB[t - 1]) - math.sqrt(1 - AB[t - 1] - s2) * math.sqrt(AB[t] / (1 - AB[t]))
    return c * c * (1 - AB[t]) / (2 * s2 * AB[t]), c


def gamma_printed(t, s2, d=3072):
    "식 32 · 35 에 인쇄된 계수, d = 3 x 32 x 32"
    return 1 / (2 * d * s2 * AB[t])


def toy(seq, eta, s2=0.25, hat=False, lastnoise=True):
    """데이터가 1 차원 N(0, s2) 이면 최적 epsilon 이 x 에 선형이라 표본 없이 분산이 닫힌다.
    시작 분산 1 에서 식 12 를 따라 내려가 끝 분산을 돌려준다."""
    v = 1.0
    for t, p in walk(seq):
        vt = AB[t] * s2 + 1 - AB[t]
        k = math.sqrt(1 - AB[t]) / vt
        g = s1(t, p)
        coef = g if hat else eta * eta * g
        A = math.sqrt(AB[p] / AB[t]) * (1 - math.sqrt(1 - AB[t]) * k) + math.sqrt(max(0, 1 - AB[p] - coef)) * k
        noise = shat(t, p) if hat else eta * eta * g
        if p == 0 and hat and not lastnoise:
            noise = 0
        v = A * A * v + noise
    return v


print("\n[일정] alpha_t:", [(t, round(AB[t], 6)) for t in (1, 100, 300, 500, 700, 900, 1000)])
print("[식 38] sigma(t):", [(t, round(ve(t), 4)) for t in (1, 100, 500, 900, 1000)])
print("\n[식 12 = DDPM] eta = 1 의 epsilon 계수 대 DDPM mu 의 계수")
for t in (2, 100, 500, 1000):
    bt = s1(t, t - 1)
    a = -math.sqrt(AB[t - 1] * (1 - AB[t]) / AB[t]) + math.sqrt(1 - AB[t - 1] - bt)
    b = -beta[t] / math.sqrt((1 - beta[t]) * (1 - AB[t]))
    print("  t=%4d  %.10f  %.10f" % (t, a, b))
print("\n[정리 1 의 계수] t, 식 66, 내 계산, c, 인쇄(d=3072), 인쇄/식 66")
GT = [2, 10, 100, 300, 500, 700, 900, 1000]
for t in GT:
    bt = s1(t, t - 1)
    m, c = gamma_mine(t, bt)
    print("  t=%4d  %.5f  %.5f  %.5f  %.4e  %.3e" % (t, gamma_eq66(t), m, c, gamma_printed(t, bt), gamma_printed(t, bt) / gamma_eq66(t)))
ge = [(gamma_eq66(t), t) for t in range(2, T + 1)]
print("  식 66 최솟값 자리:", min(ge), " 인쇄 최솟값 자리:", min((gamma_printed(t, s1(t, t - 1)), t) for t in range(2, T + 1)))
print("\n[이차 규칙] S, 앞 자리, 서로 다른 값 수, 0 의 수")
for S in (10, 20, 50, 100, 1000):
    q = quad(S)
    print("  S=%4d  %s  %d  %d" % (S, q[:8], len(set(q)), q.count(0)))
print("\n[새 잡음 몫] sigma(1)^2 / (1 - alpha_p), 첫 걸음과 t=500 근처")
for S in (10, 20, 50, 100, 1000):
    w = walk(lin(S))
    tt = [x for x in w if x[0] == 500]
    print("  S=%4d  첫 %.4f  t=500 %.4f" % (S, s1(*w[0]) / (1 - AB[w[0][1]]), s1(*tt[0]) / (1 - AB[tt[0][1]])))
print("\n[sigma-hat^2 / sigma(1)^2] 끝에서 둘째 걸음")
for S in (10, 100, 1000):
    w = walk(lin(S))
    print("  S=%4d  %s  %.3f  / 마지막 걸음 sigma-hat = %.4f" % (S, w[-2], shat(*w[-2]) / s1(*w[-2]), math.sqrt(shat(*w[-1]))))
print("\n[식 15 / 식 13] (1 + sigma'/sigma) / 2")
for S in (10, 100, 1000):
    w = walk(lin(S))
    r = [(1 + ve(p) / ve(t)) / 2 if p > 0 else 0.5 for t, p in w]
    print("  S=%4d  첫 %.4f  끝에서 둘째 %.4f  끝 %.4f" % (S, r[0], r[-2], r[-1]))
print("\n[표 2] S, 제곱 오차, 255 눈금 RMSE")
for S, e in zip(T2_S, T2_E):
    print("  %4d  %.4f  %.2f" % (S, e, 255 * math.sqrt(e)))
print("  0.0001 의 반올림 구간 RMSE: %.2f ~ %.2f" % (255 * math.sqrt(0.00005), 255 * math.sqrt(0.00015)))
print("  기울기 S 10->100: %.3f, 20->50: %.3f" % (math.log10(0.014 / 0.0009), math.log10(.0065 / .0023) / math.log10(2.5)))
print("\n[그림 4] 걸음당 시간(시간), 이미지 하나 · 걸음 하나의 밀리초")
for nm, F in (("CIFAR10", F4_C), ("Bedroom", F4_B)):
    print(" ", nm, [round(h / s, 5) for h, s in zip(F, F4_S)], [round(h / s * 3600 / 50000 * 1000, 2) for h, s in zip(F, F4_S)])
print("\n[1 차원 가우시안] 끝 표준편차 (목표 s)")
for s2 in (0.25, 0.04, 0.0025, 0.0004):
    print("  s =", math.sqrt(s2))
    for nm, kw in (("eta=0", dict(eta=0)), ("eta=0.5", dict(eta=.5)), ("eta=1", dict(eta=1)), ("hat", dict(eta=1, hat=True)), ("hat, 끝 잡음 없음", dict(eta=1, hat=True, lastnoise=False))):
        print("   ", nm, [round(math.sqrt(toy(lin(S) if S < 1000 else list(range(1, 1001)), s2=s2, **kw)), 4) for S in STEPS])
print("\n[1000 걸음 대비] 표 1 eta=0 / 같은 줄 1000, 표 3 DDIM / DDPM 1000")
print("  CIFAR10", [round(v / T1_C["0.0"][4], 3) for v in T1_C["0.0"][:4]], " / 3.17:", [round(v / 3.17, 3) for v in T1_C["0.0"][:4]])
print("  CelebA ", [round(v / T1_A["0.0"][4], 3) for v in T1_A["0.0"][:4]], " / 3.26:", [round(v / 3.26, 3) for v in T1_A["0.0"][:4]])
print("  Bedroom", [round(v / 6.36, 3) for v in T3["Bedroom"][0]])
print("  Church ", [round(v / 7.89, 3) for v in T3["Church"][0]])
print()


def logx(v, lo, hi, x0, x1):
    return x0 + (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (x1 - x0)


def logy(v, lo, hi, y0, y1):
    "y0 위, y1 아래"
    return y1 - (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (y1 - y0)


def legend(x, y, items, size=11, gap=18):
    s = ""
    for j, (lab, col, dash) in enumerate(items):
        s += line(x, y + gap * j - 4, x + 24, y + gap * j - 4, col, 2.2, dash=dash)
        s += txt(x + 30, y + gap * j, lab, size, fill=INK2, anchor="start")
    return s


# ── 그림 1: 앞방향 두 꼴 ───────────────────────────────────────────────────
def fig01():
    W, H = 860, 310
    s = defs() + txt(W / 2, 26, "x_T 쪽으로 가는 앞방향의 두 꼴 (원문 그림 1 을 다시 그림, T = 3)", 15, weight="700")

    def node(x, y, name, fill=None):
        return circ(x, y, 22, fill or NODE, INK) + txt(x, y + 5, name, 13, weight="700")
    ys = 128
    xs = [360, 270, 180, 90]
    s += txt(225, 58, "왼쪽: DDPM (식 3, 마르코프)", 13, fill=FWD, weight="700")
    for i in range(4):
        s += node(xs[i], ys, "x%d" % i)
    for i in range(3):
        s += line(xs[i] - 24, ys, xs[i + 1] + 25, ys, FWD, 2, marker="af")
    s += lines_at(70, 190, [("다음 자리는 바로 앞 자리에만 기댄다.", INK2), ("q(x_t | x_{t-1})", FWD, "700"),
                            ("x_t 하나를 만드는 데 드는 표본 잡음은 t 개.", INK2)], size=12)
    xr = [790, 700, 610, 520]
    s += txt(655, 58, "오른쪽: 이 편 (식 6, 7, 비마르코프)", 13, fill=REV, weight="700")
    for i in range(4):
        s += node(xr[i], ys, "x%d" % i)
    s += path("M %d %d C 700 208, 610 208, %d %d" % (790, 150, 520, 150), REV, sw=2, marker="ar")
    s += txt(655, 208, "q(x_3 | x_0)", 11.5, fill=REV)
    s += line(xr[3] + 25, ys, xr[2] - 25, ys, REV, 2, marker="ar")
    s += line(xr[2] + 25, ys, xr[1] - 25, ys, REV, 2, marker="ar")
    s += path("M 790 106 C 760 72, 640 72, 612 104", REV, sw=1.5, dash="4 3", marker="ar")
    s += path("M 790 106 C 770 80, 725 80, 702 104", REV, sw=1.5, dash="4 3", marker="ar")
    s += lines_at(490, 238, [("x_{t-1} 은 x_t 와 x_0 둘에 기댄다(점선이 x_0 쪽 의존).", INK2),
                             ("q_sigma(x_{t-1} | x_t, x_0). 인수 분해 방향이 위에서 아래다.", REV, "700"),
                             ("q(x_t | x_0) 는 왼쪽과 같다(보조 정리 1).", INK2)], size=12)
    svg("fig01_two_forward", W, H, s, "DDPM 의 마르코프 앞방향과 이 편의 비마르코프 앞방향")


# ── 그림 2: 같은 주변 분포, 다른 경로 ───────────────────────────────────────
def fig02():
    W, H = 860, 370
    random.seed(0)
    s = defs() + txt(W / 2, 26, "x_0 = 1 에서 나간 경로 여섯: 곁에서 보면 같은 띠, 경로는 다르다 (내가 그린 것)", 15, weight="700")

    def panel(x0, x1, title, col, paths):
        y0, y1 = 70, 290
        fx = lambda t: x0 + t / T * (x1 - x0)
        fy = lambda v: (y0 + y1) / 2 - v / 3.0 * (y1 - y0) / 2
        o = axes(x0, y0, x1, y1, [0, 250, 500, 750, 1000], [-3, -1, 0, 1, 3], fx, fy, xl="t", yl="x_t")
        ts = list(range(0, T + 1, 10))
        for sgn in (1, -1):
            o += polyline([(fx(t), fy(math.sqrt(AB[t]) + sgn * math.sqrt(1 - AB[t]))) for t in ts], INK2, sw=1.4, dash="5 4")
        for p in paths:
            o += polyline([(fx(t), fy(p[t])) for t in ts], col, sw=1.3)
        o += txt((x0 + x1) / 2, 56, title, 12.5, fill=col, weight="700")
        return o
    eps = [-1.7, -1.0, -0.35, 0.3, 0.95, 1.6]
    a = [[math.sqrt(AB[t]) + math.sqrt(1 - AB[t]) * e for t in range(T + 1)] for e in eps]
    b = []
    for _ in eps:
        x, p = 1.0, [1.0]
        for t in range(1, T + 1):
            x = math.sqrt(1 - beta[t]) * x + math.sqrt(beta[t]) * random.gauss(0, 1)
            p.append(x)
        b.append(p)
    s += panel(60, 410, "sigma = 0: 경로마다 epsilon 하나를 끝까지 쓴다", REV, a)
    s += panel(490, 840, "DDPM: 걸음마다 새 잡음을 더한다", FWD, b)
    s += txt(W / 2, 355, "점선 = 평균 ± 표준편차 = sqrt(alpha_t) ± sqrt(1 - alpha_t). 두 칸의 점선은 같은 값이다.", 12, fill=INK2)
    svg("fig02_same_marginal", W, H, s, "주변 분포가 같고 경로가 다른 두 앞방향")


# ── 그림 3: 식 12 의 세 조각 ───────────────────────────────────────────────
def fig03():
    W, H = 860, 340
    t, p = 500, 400
    g = s1(t, p)
    s = defs() + txt(W / 2, 26, "식 12 의 한 걸음: 셋의 합이 x_{t-1} 이다", 15, weight="700")
    s += box(30, 70, 120, 50, FWD_SOFT, FWD) + txt(90, 92, "x_t", 13, weight="700") + txt(90, 110, "지금 자리", 11, fill=INK2)
    s += box(30, 150, 120, 50, CODE_SOFT, CODE) + txt(90, 172, "epsilon_theta", 12.5, weight="700") + txt(90, 190, "망의 출력 1 번", 11, fill=INK2)
    s += line(90, 122, 90, 148, INK2, 1.4, marker="ai")
    bx = [(220, 200, "예측한 x_0", "× sqrt(alpha_{t-1})", "식 9 의 f 를 다음 눈금으로", FWD_SOFT, FWD),
          (440, 200, "x_t 쪽 방향", "× sqrt(1 - alpha_{t-1} - sigma^2)", "같은 epsilon 을 다시 쓴다", CODE_SOFT, CODE),
          (660, 170, "새 잡음", "× sigma", "sigma = 0 이면 사라진다", REV_SOFT, REV)]
    for x, w, a, a2, b, f, c in bx:
        s += box(x, 78, w, 82, f, c) + txt(x + w / 2, 100, a, 11.8, weight="700") + txt(x + w / 2, 120, a2, 11.2, weight="700") + txt(x + w / 2, 144, b, 11, fill=INK2)
    s += line(152, 95, 218, 110, INK2, 1.4, marker="ai") + line(152, 175, 218, 135, INK2, 1.4, marker="ai")
    s += txt(430, 126, "+", 18, weight="700") + txt(650, 126, "+", 18, weight="700")
    rows = [["같은 x_t, 같은 망, t = 500 -> 400 (S = 10 선형)", "x_0 쪽 계수", "방향 계수", "잡음 표준편차", "새 잡음의 분산 몫"]]
    for nm, e in (("eta = 0 (DDIM)", 0.0), ("eta = 0.5", 0.5), ("eta = 1 (DDPM)", 1.0)):
        sg = e * e * g
        rows.append([nm, "%.4f" % math.sqrt(AB[p]), "%.4f" % math.sqrt(1 - AB[p] - sg), "%.4f" % math.sqrt(sg), "%.1f%%" % (100 * sg / (1 - AB[p]))])
    s += table(40, 200, [320, 110, 110, 120, 130], rows, rowh=27)
    s += txt(W / 2, 325, "표의 값은 DDPM 선형 일정(T = 1000)에서 내가 계산한 것이다. 분산 몫의 분모는 1 - alpha_{t-1}.", 11.5, fill=MUTED)
    svg("fig03_update_parts", W, H, s, "식 12 의 세 조각과 eta 별 계수")


# ── 그림 4: 새 잡음 몫 ─────────────────────────────────────────────────────
def fig04():
    W, H = 820, 370
    x0, x1, y0, y1 = 80, 620, 60, 310
    fx = lambda t: x0 + t / T * (x1 - x0)
    fy = lambda v: y1 - v * (y1 - y0)
    s = defs() + txt(W / 2, 28, "eta = 1 에서 다음 자리 잡음 분산 가운데 새로 뽑는 몫 (내가 계산한 것)", 15, weight="700")
    s += axes(x0, y0, x1, y1, [0, 200, 400, 600, 800, 1000], [0, .25, .5, .75, 1], fx, fy, xl="걸음의 출발 자리 t", yl="sigma^2 / (1 - alpha_{t-1})")
    cols = {10: NO, 20: REV, 50: PURP, 100: CODE, 1000: FWD}
    items = []
    for S in (10, 20, 50, 100, 1000):
        w = walk(lin(S) if S < 1000 else list(range(1, 1001)))
        pts = [(fx(t), fy(s1(t, p) / (1 - AB[p]))) for t, p in w if p > 0]
        if S == 1000:
            pts = pts[::5]
        s += polyline(pts, cols[S], sw=2)
        if S < 100:
            for q in pts:
                s += circ(q[0], q[1], 2.6, cols[S], cols[S])
        items.append(("S = %d" % S, cols[S], None))
    s += legend(650, 90, items)
    s += lines_at(640, 210, [("첫 걸음의 몫", INK2, "700"), "S = 10: 85.3%", "S = 100: 18.2%", "S = 1000: 2.0%"], size=11.5, gap=19)
    svg("fig04_fresh_share", W, H, s, "걸음 수별 새 잡음 분산 몫")


# ── 그림 5: sigma-hat ─────────────────────────────────────────────────────
def fig05():
    W, H = 820, 370
    x0, x1, y0, y1 = 80, 620, 60, 310
    fx = lambda t: logx(t, 1, 1000, x0, x1)
    fy = lambda v: logy(v, 1, 1000, y0, y1)
    s = defs() + txt(W / 2, 28, "sigma-hat^2 / sigma(1)^2: 큰 잡음은 어디서 더 큰가 (내가 계산한 것)", 15, weight="700")
    s += axes(x0, y0, x1, y1, [1, 10, 100, 1000], [1, 10, 100, 1000], fx, fy, xl="걸음의 출발 자리 t (로그)", yl="분산의 배수 (로그)")
    cols = {10: NO, 100: CODE, 1000: FWD}
    items = []
    for S in (10, 100, 1000):
        w = walk(lin(S) if S < 1000 else list(range(1, 1001)))
        pts = [(fx(t), fy(shat(t, p) / s1(t, p))) for t, p in w if p > 0]
        s += polyline(pts, cols[S], sw=2)
        items.append(("S = %d" % S, cols[S], None))
    s += legend(650, 90, items)
    s += lines_at(640, 190, [("끝 걸음(자리 0 으로)", INK2, "700"), "sigma(1) = 0", "식대로면 sigma-hat 은", "S = 10: 0.3209", "S = 100: 0.0435", "S = 1000: 0.0100"], size=11.5, gap=19)
    svg("fig05_sigma_hat_ratio", W, H, s, "sigma hat 대 sigma(1) 의 분산 배수")


# ── 그림 6: 정리 1 의 계수 ─────────────────────────────────────────────────
def fig06():
    W, H = 820, 380
    x0, x1, y0, y1 = 80, 610, 60, 320
    fx = lambda t: logx(t, 2, 1000, x0, x1)
    fy = lambda v: logy(v, 1e-3, 1e3, y0, y1)
    s = defs() + txt(W / 2, 28, "정리 1 의 계수 gamma_t: 식 66 대 식 35 (sigma^2 = beta-tilde, 내가 계산한 것)", 15, weight="700")
    s += axes(x0, y0, x1, y1, [2, 10, 100, 1000], [1e-3, 1e-2, 1e-1, 1, 10, 100, 1000], fx, fy, xl="t (로그)", yl="gamma_t (로그)")
    ts = sorted(set([2, 3, 4, 5, 7, 10, 15, 20, 30, 50, 70] + list(range(100, 1001, 25))))
    s += polyline([(fx(t), fy(gamma_eq66(t))) for t in ts], FWD, sw=2.4)
    s += polyline([(fx(t), fy(gamma_printed(t, s1(t, t - 1)))) for t in ts], REV, sw=2.4)
    for t in (2, 1000):
        s += circ(fx(t), fy(gamma_eq66(t)), 3.5, FWD, FWD) + circ(fx(t), fy(gamma_printed(t, s1(t, t - 1))), 3.5, REV, REV)
    s += legend(630, 90, [("식 66 = 식 30 을 바로 푼 값", FWD, None), ("식 35 에 인쇄된 값 (d = 3072)", REV, None)], size=11)
    s += lines_at(630, 170, [("gamma_2 / gamma_1000", INK2, "700"), "식 66: %.1f 배" % (gamma_eq66(2) / gamma_eq66(1000)),
                             "식 35: %.4f 배" % (gamma_printed(2, s1(2, 1)) / gamma_printed(1000, s1(1000, 999))), "",
                             ("곡선 모양이 다르다.", NO, "700"), "다만 정리의 말(양수 gamma", "가 있다)은 그대로 선다."], size=11.5, gap=19)
    svg("fig06_gamma", W, H, s, "식 66 과 식 35 의 계수 비교")


# ── 그림 7: 증명의 세 자리 ─────────────────────────────────────────────────
def fig07():
    W, H = 860, 290
    s = defs() + txt(W / 2, 26, "부록 B 정리 1 의 증명에서 바뀌어야 하는 세 자리 (내가 유도한 것)", 15, weight="700")
    rows = [["자리", "원문", "바로 계산하면", "까닭"],
            ["식 30", "||x_0 - f||^2 / (2 sigma_t^2)", "c_t^2 ||x_0 - f||^2 / (2 sigma_t^2)", "두 평균의 차에 x_0 의 계수 c_t 가 곱해진다"],
            ["식 31 -> 32", "(1 - alpha_t) 가 없다", "(1 - alpha_t) / alpha_t 가 곱해진다", "epsilon 앞의 sqrt(1 - alpha_t) 제곱"],
            ["식 32 · 34 · 35", "분모에 d", "d 없음", "식 5 의 노름은 차원으로 나누지 않는다"],
            [("결과 gamma_t", None, "700", None), ("1 / (2 d sigma_t^2 alpha_t)", NO, "700", None), ("c_t^2 (1 - alpha_t) / (2 sigma_t^2 alpha_t)", OK, "700", None), "sigma^2 = beta-tilde 이면 식 66 과 같다"]]
    s += table(30, 50, [110, 210, 250, 230], rows, rowh=34, size=11)
    s += txt(W / 2, 245, "c_t = sqrt(alpha_{t-1}) - sqrt(1 - alpha_{t-1} - sigma_t^2) · sqrt(alpha_t / (1 - alpha_t))", 12.5, fill=INK, weight="700")
    s += txt(W / 2, 270, "sigma = beta-tilde 에서 c_2 = 0.5453 · c_500 = 0.00307 · c_1000 = 0.00013. 「≡」 는 상수 차만 허용하므로 c_t^2 은 뺄 수 없다.", 11.5, fill=INK2)
    svg("fig07_proof_chain", W, H, s, "정리 1 증명에서 바뀌는 세 자리")


# ── 그림 8: 부분열 ─────────────────────────────────────────────────────────
def fig08():
    W, H = 840, 370
    x0, x1, y0, y1 = 80, 610, 60, 290
    fx = lambda t: x0 + t / T * (x1 - x0)
    fy = lambda v: y1 - v * (y1 - y0)
    s = defs() + txt(W / 2, 28, "S = 10 의 부분열이 어느 자리를 밟나 (DDPM 선형 일정, 내가 계산한 것)", 15, weight="700")
    s += axes(x0, y0, x1, y1, [0, 200, 400, 600, 800, 1000], [0, .25, .5, .75, 1], fx, fy, xl="t", yl="sqrt(alpha_t)")
    s += polyline([(fx(t), fy(math.sqrt(AB[t]))) for t in range(0, T + 1, 5)], INK2, sw=1.6)
    L, Q = lin(10), quad(10)
    for t in L:
        s += circ(fx(t), fy(math.sqrt(AB[t])) - 9, 4, FWD, FWD)
    for t in Q:
        s += circ(fx(t), fy(math.sqrt(AB[t])) + 9, 4, REV, REV)
    s += legend(640, 90, [("곡선 = sqrt(alpha_t)", INK2, None)], size=11)
    s += circ(652, 112, 4, FWD, FWD) + txt(670, 116, "선형 c i (c = 100)", 11, fill=INK2, anchor="start")
    s += circ(652, 134, 4, REV, REV) + txt(670, 138, "이차 c i^2 (c = 10)", 11, fill=INK2, anchor="start")
    s += lines_at(630, 170, [("끝 걸음이 건너는 폭", INK2, "700"), "선형: 100 -> 0", "이차: 10 -> 0", "", ("이차 규칙을 그대로 적으면", NO, "700"),
                             "S = 50: tau_1 = 0", "S = 100: 서로 다른 값 98", "S = 1000: 서로 다른 값 751"], size=11.5, gap=19)
    s += txt(W / 2, 342, "점은 겹치지 않게 곡선에서 위아래로 9 픽셀 띄웠다.", 11, fill=MUTED)
    s += txt(W / 2, 358, "원문은 CIFAR10 에 이차, 나머지에 선형을 썼다고 적는다(부록 D.2). c 는 「tau_{-1} 이 T 에 가깝게」 로만 적혀 있어 c = T / S^2 은 내가 넣었다.", 11, fill=MUTED)
    svg("fig08_tau", W, H, s, "선형과 이차 부분열")


# ── 그림 9: 표 1 ───────────────────────────────────────────────────────────
def fig09():
    W, H = 860, 400
    s = defs() + txt(W / 2, 28, "표 1 을 옮겨 그림: 걸음 수와 eta 에 따른 FID (낮을수록 좋다)", 15, weight="700")
    cols = {"0.0": FWD, "0.2": OK, "0.5": CODE, "1.0": REV, "hat": NO}
    names = {"0.0": "eta = 0 (DDIM)", "0.2": "eta = 0.2", "0.5": "eta = 0.5", "1.0": "eta = 1 (DDPM)", "hat": "sigma-hat (DDPM)"}

    def panel(x0, x1, tb, title):
        y0, y1 = 70, 320
        fx = lambda v: logx(v, 10, 1000, x0, x1)
        fy = lambda v: logy(v, 3, 400, y0, y1)
        o = axes(x0, y0, x1, y1, [10, 20, 50, 100, 1000], [3, 5, 10, 20, 50, 100, 400], fx, fy, xl="S (로그)", yl="FID (로그)")
        o += txt((x0 + x1) / 2, 58, title, 13, weight="700")
        for k in ("hat", "1.0", "0.5", "0.2", "0.0"):
            pts = [(fx(a), fy(b)) for a, b in zip(STEPS, tb[k])]
            o += polyline(pts, cols[k], sw=2.2)
            for q in pts:
                o += circ(q[0], q[1], 2.8, cols[k], cols[k])
        return o
    s += panel(70, 400, T1_C, "CIFAR10 (이차 부분열)")
    s += panel(490, 820, T1_A, "CelebA (선형 부분열)")
    lg = [(names[k], cols[k]) for k in ("0.0", "0.2", "0.5", "1.0", "hat")]
    for i, (a, c) in enumerate(lg):
        s += line(50 + i * 160, 372, 74 + i * 160, 372, c, 2.4) + txt(80 + i * 160, 376, a, 11, fill=INK2, anchor="start")
    svg("fig09_table1", W, H, s, "표 1 의 FID 를 걸음 수와 eta 로")


# ── 그림 10: 표 3 ──────────────────────────────────────────────────────────
def fig10():
    W, H = 860, 410
    s = defs() + txt(W / 2, 28, "표 3 을 옮겨 그림: 부록에만 있는 256 x 256 결과", 15, weight="700")

    def panel(x0, x1, name):
        a, b, ref = T3[name]
        y0, y1 = 70, 310
        S4 = STEPS[:4]
        fx = lambda v: logx(v, 10, 100, x0 + 15, x1 - 15)
        fy = lambda v: logy(v, 5, 60, y0, y1)
        o = axes(x0, y0, x1, y1, S4, [5, 10, 20, 40, 60], fx, fy, xl="S (로그)", yl="FID (로그)")
        o += txt((x0 + x1) / 2, 58, "LSUN " + name, 13, weight="700")
        o += line(x0, fy(ref), x1, fy(ref), INK2, 1.2, dash="5 4") + txt(x0 + 6, fy(ref) + 14, "DDPM 1000 걸음 %.2f (캡션)" % ref, 10.5, fill=INK2, anchor="start")
        for vals, c, dy in ((a, FWD, -10), (b, REV, 16)):
            pts = [(fx(u), fy(v)) for u, v in zip(S4, vals)]
            o += polyline(pts, c, sw=2.2)
            for q, v in zip(pts, vals):
                up = dy
                if name == "Bedroom" and v in (6.62, 6.81):
                    up = 16 if v == 6.62 else -10
                if name == "Church" and v in (8.27, 10.58):
                    up = 16 if v == 8.27 else -10
                o += circ(q[0], q[1], 3, c, c) + txt(q[0], q[1] + up, "%.2f" % v, 10, fill=c)
        return o
    s += panel(70, 410, "Bedroom") + panel(490, 830, "Church")
    s += line(320, 368, 344, 368, FWD, 2.4) + txt(350, 372, "DDIM (eta = 0)", 11, fill=INK2, anchor="start")
    s += line(470, 368, 494, 368, REV, 2.4) + txt(500, 372, "DDPM (eta = 1)", 11, fill=INK2, anchor="start")
    s += txt(W / 2, 398, "Church S = 100 에서 DDPM 8.27 이 DDIM 10.58 보다 2.31 낮다. 원문 표도 이 칸을 DDPM 쪽에 굵게 적는다.", 12, fill=NO, weight="700")
    svg("fig10_table3", W, H, s, "표 3 의 FID")


# ── 그림 11: 1000 걸음과 비슷한가 ──────────────────────────────────────────
def fig11():
    W, H = 860, 380
    x0, x1, y0, y1 = 80, 830, 70, 300
    fy = lambda v: y1 - (v - 1) / 4.2 * (y1 - y0)
    s = defs() + txt(W / 2, 28, "DDIM 의 FID 가 1000 걸음 기준의 몇 배인가 (표 1 · 표 3 에서 내가 나눈 것)", 15, weight="700")
    s += axes(x0, y0, x1, y1, [], [1, 2, 3, 4, 5], lambda v: v, fy, yl="FID / 기준 FID")
    data = [("CIFAR10\n기준: eta = 0, 4.04", [v / 4.04 for v in T1_C["0.0"][:4]]),
            ("CelebA\n기준: eta = 0, 3.51", [v / 3.51 for v in T1_A["0.0"][:4]]),
            ("Bedroom\n기준: DDPM 6.36", [v / 6.36 for v in T3["Bedroom"][0]]),
            ("Church\n기준: DDPM 7.89", [v / 7.89 for v in T3["Church"][0]])]
    cols = [NO, REV, CODE, FWD]
    gw = (x1 - x0) / 4
    for i, (nm, vals) in enumerate(data):
        gx = x0 + i * gw + 18
        for j, v in enumerate(vals):
            bx = gx + j * 36
            s += '<rect x="%.1f" y="%.1f" width="30" height="%.1f" fill="%s"/>' % (bx, fy(v), y1 - fy(v), cols[j])
            s += txt(bx + 15, fy(v) - 5, "%.2f" % v, 10.5, fill=INK2)
        a, b = nm.split("\n")
        s += txt(x0 + i * gw + gw / 2, y1 + 18, a, 12, weight="700") + txt(x0 + i * gw + gw / 2, y1 + 34, b, 10.5, fill=MUTED)
    for j, lab in enumerate(("S = 10", "S = 20", "S = 50", "S = 100")):
        s += '<rect x="%d" y="358" width="14" height="10" fill="%s"/>' % (250 + j * 95, cols[j]) + txt(270 + j * 95, 367, lab, 11, fill=INK2, anchor="start")
    svg("fig11_comparable", W, H, s, "1000 걸음 기준 대비 FID 배수")


# ── 그림 12: 그림 4 다시 그리기 ────────────────────────────────────────────
def fig12():
    W, H = 860, 370
    s = defs() + txt(W / 2, 28, "원문 그림 4 를 벡터 좌표로 읽어 다시 그림: 50k 장을 뽑는 시간 (2080 Ti 한 장)", 15, weight="700")

    def panel(x0, x1, F, lo, hi, yt, c, title):
        y0, y1 = 70, 300
        fx = lambda v: logx(v, 10, 1000, x0, x1)
        fy = lambda v: logy(v, lo, hi, y0, y1)
        o = axes(x0, y0, x1, y1, [10, 30, 100, 300, 1000], yt, fx, fy, xl="걸음 수 (로그)", yl="시간 (로그)")
        o += txt((x0 + x1) / 2, 58, title, 13, weight="700")
        pts = [(fx(a), fy(b)) for a, b in zip(F4_S, F)]
        o += polyline(pts, c, sw=2.2)
        for q, v in zip(pts, F):
            o += circ(q[0], q[1], 3, c, c) + txt(q[0] - 6, q[1] - 8, ("%.2f" % v) if v < 10 else ("%.1f" % v), 10, fill=c, anchor="end")
        return o
    s += panel(80, 410, F4_C, 0.15, 25, [0.2, 0.5, 2, 5, 20], FWD, "CIFAR10")
    s += panel(500, 830, F4_B, 8, 1200, [10, 30, 100, 300, 1000], REV, "LSUN Bedroom")
    s += txt(W / 2, 358, "머리말의 「about 20 hours」 · 「nearly 1000 hours」 와 맞대면 18.8 시간 · 828 시간이다. 값은 표식 상자 가운데를 눈금 선 좌표로 바꾼 것이다.", 11.5, fill=INK2)
    svg("fig12_fig4_redraw", W, H, s, "원문 그림 4 를 다시 그림")


# ── 그림 13: 걸음당 시간 ───────────────────────────────────────────────────
def fig13():
    W, H = 860, 310
    s = defs() + txt(W / 2, 28, "그림 4 의 시간을 걸음 수로 나눈 값 (내가 나눈 것)", 15, weight="700")
    rows = [["걸음 수"] + [str(v) for v in F4_S]]
    rows.append(["CIFAR10, 시간 / 걸음"] + ["%.5f" % (h / a) for h, a in zip(F4_C, F4_S)])
    rows.append(["CIFAR10, 장 · 걸음당 ms"] + ["%.2f" % (h / a * 3600 / 50000 * 1000) for h, a in zip(F4_C, F4_S)])
    rows.append(["Bedroom, 시간 / 걸음"] + [(("%.5f" % (h / a)), (NO if a >= 100 else None), ("700" if a >= 100 else None), None) for h, a in zip(F4_B, F4_S)])
    rows.append(["Bedroom, 장 · 걸음당 ms"] + ["%.2f" % (h / a * 3600 / 50000 * 1000) for h, a in zip(F4_B, F4_S)])
    s += table(30, 55, [205] + [85] * 7, rows, rowh=30, size=11)
    s += lines_at(40, 230, [("Bedroom 의 100 ~ 1000 네 점은 걸음당 시간이 소수 다섯째까지 같다. CIFAR10 은 0.01882 ~ 0.01978 로 흔들린다.", NO, "700"),
                            "네 점을 따로 잰 값이라면 보기 어려운 일치이고, 한 번 잰 값에 걸음 수를 곱해 그렸을 수 있다. 원문에 말이 없으니 이것은 내 추정이다.",
                            "Bedroom 은 CIFAR10 의 %.1f 배(1000 걸음, 분모 CIFAR10)이고 픽셀 수는 64 배(분모 32 x 32)다." % (F4_B[-1] / F4_C[-1])], size=11.5, gap=22)
    svg("fig13_time_per_step", W, H, s, "그림 4 의 걸음당 시간")


# ── 그림 14: 표 2 ──────────────────────────────────────────────────────────
def fig14():
    W, H = 820, 370
    x0, x1, y0, y1 = 80, 590, 60, 310
    fx = lambda v: logx(v, 10, 1000, x0, x1)
    fy = lambda v: logy(v, 5e-5, 2e-2, y0, y1)
    s = defs() + txt(W / 2, 28, "표 2 를 옮겨 그림: 부호화 S 걸음 + 복호화 S 걸음의 재구성 오차", 15, weight="700")
    s += axes(x0, y0, x1, y1, [10, 20, 50, 100, 200, 500, 1000], [1e-4, 1e-3, 1e-2], fx, fy, xl="S (로그)", yl="차원당 제곱 오차, [0, 1] 눈금 (로그)", yfmt=lambda v: "%g" % v)
    pts = [(fx(a), fy(b)) for a, b in zip(T2_S, T2_E)]
    s += polyline(pts, FWD, sw=2.2)
    for q, a, e in zip(pts, T2_S, T2_E):
        s += circ(q[0], q[1], 3.2, FWD, FWD) + txt(q[0] + (2 if a < 1000 else -2), q[1] - 10, "%.2f" % (255 * math.sqrt(e)), 10.5, fill=REV, anchor=("start" if a < 1000 else "end"))
    s += lines_at(610, 90, [("주황 수", REV, "700"), "제곱 오차를 0 ~ 255 눈금", "RMSE 로 바꾼 값(내가 셈)", "", ("500 과 1000 은 가를 수 없다", NO, "700"),
                            "캡션이 10^-4 로 반올림했고", "둘 다 0.0001 이다. 그 구간은", "RMSE 1.80 ~ 3.12", "", ("S = 10 -> 100 기울기", INK2, "700"), "제곱 오차 S^-1.19"], size=11.5, gap=20)
    svg("fig14_table2", W, H, s, "표 2 의 재구성 오차")


# ── 그림 15: 식 15 / 식 13 ─────────────────────────────────────────────────
def fig15():
    W, H = 820, 370
    x0, x1, y0, y1 = 80, 610, 60, 310
    fx = lambda t: logx(t, 1, 1000, x0, x1)
    fy = lambda v: y1 - (v - 0.45) / 0.57 * (y1 - y0)
    s = defs() + txt(W / 2, 28, "같은 걸음에서 식 15 의 계수 / 식 13 의 계수 = (1 + sigma' / sigma) / 2 (내가 계산한 것)", 14.5, weight="700")
    s += axes(x0, y0, x1, y1, [1, 10, 100, 1000], [.5, .6, .7, .8, .9, 1], fx, fy, xl="걸음의 출발 자리 t (로그)", yl="계수 비", yfmt="%.1f")
    cols = {10: NO, 100: CODE, 1000: FWD}
    items = []
    for S in (10, 100, 1000):
        w = walk(lin(S) if S < 1000 else list(range(1, 1001)))
        pts = [(fx(t), fy((1 + ve(p) / ve(t)) / 2 if p > 0 else .5)) for t, p in w]
        s += polyline(pts, cols[S], sw=2)
        items.append(("S = %d" % S, cols[S], None))
    s += legend(635, 90, items)
    s += lines_at(630, 180, [("읽는 법", INK2, "700"), "1 이면 두 오일러 걸음이 같다.", "끝 걸음은 sigma' = 0 이라", "S 와 상관없이 0.5 다.", "", "S = 1000 의 끝 걸음은", "sigma 폭이 0.01 이다."], size=11.5, gap=19)
    svg("fig15_euler_ratio", W, H, s, "식 15 와 식 13 의 계수 비")


# ── 그림 16: sigma(t) ─────────────────────────────────────────────────────
def fig16():
    W, H = 820, 360
    x0, x1, y0, y1 = 80, 610, 60, 300
    fx = lambda t: x0 + t / T * (x1 - x0)
    fy = lambda v: logy(v, 0.01, 200, y0, y1)
    s = defs() + txt(W / 2, 28, "식 38 의 sigma(t): 오일러 걸음을 재는 눈금 (DDPM 선형 일정, 내가 계산한 것)", 15, weight="700")
    s += axes(x0, y0, x1, y1, [1, 200, 400, 600, 800, 1000], [0.01, 0.1, 1, 10, 100], fx, fy, xl="t", yl="sigma(t) (로그)")
    s += polyline([(fx(t), fy(ve(t))) for t in range(1, T + 1, 5)], FWD, sw=2.2)
    for t in lin(10):
        s += circ(fx(t), fy(ve(t)), 3.8, REV, REV)
    w = walk(lin(10))
    s += lines_at(630, 90, [("S = 10 선형의 sigma 폭", INK2, "700")] + ["%d -> %d: %.2f" % (t, p, ve(t) - (ve(p) if p else 0)) for t, p in w[:3]]
                  + ["..."] + ["%d -> %d: %.2f" % (t, p, ve(t) - (ve(p) if p else 0)) for t, p in w[-2:]]
                  + ["", ("t 가 고른 간격이어도", NO, "700"), "sigma 폭은 %.0f 배 차이." % ((ve(w[0][0]) - ve(w[0][1])) / (ve(w[-1][0]) - 0))], size=11.5, gap=19)
    svg("fig16_ve_sigma", W, H, s, "식 38 의 sigma(t)")


# ── 그림 17: 1 차원 가우시안 ───────────────────────────────────────────────
def fig17():
    W, H = 820, 380
    x0, x1, y0, y1 = 80, 590, 60, 320
    fx = lambda v: logx(v, 10, 1000, x0, x1)
    fy = lambda v: y1 - (v - 0.3) / 0.32 * (y1 - y0)
    s = defs() + txt(W / 2, 28, "1 차원 가우시안 데이터(s = 0.5)와 최적 epsilon 에서 끝 표준편차 (식으로 닫은 것, 표본 없음)", 14, weight="700")
    s += axes(x0, y0, x1, y1, STEPS, [.3, .4, .5, .6], fx, fy, xl="S (로그, 선형 부분열)", yl="끝 표준편차", yfmt="%.1f")
    s += line(x0, fy(.5), x1, fy(.5), INK, 1.4, dash="5 4")
    seqs = {S: (lin(S) if S < 1000 else list(range(1, 1001))) for S in STEPS}
    cases = [("eta = 0", dict(eta=0), FWD, None), ("eta = 0.5", dict(eta=.5), CODE, None), ("eta = 1", dict(eta=1), REV, None),
             ("sigma-hat", dict(eta=1, hat=True), NO, None), ("sigma-hat, 끝 걸음 잡음 없음", dict(eta=1, hat=True, lastnoise=False), NO, "4 3")]
    for nm, kw, c, d in cases:
        pts = [(fx(S), fy(math.sqrt(toy(seqs[S], **kw)))) for S in STEPS]
        s += polyline(pts, c, sw=2.1, dash=d)
        for q in pts:
            s += circ(q[0], q[1], 2.6, c, c)
    s += legend(605, 80, [(a, c, d) for a, b, c, d in cases], size=10.8)
    s += lines_at(605, 190, [("가리키는 것", INK2, "700"), "eta = 0 과 1 은 분산이", "목표보다 작고, sigma-hat 은", "S = 10 에서 크다.", "", ("가리키지 않는 것", NO, "700"), "FID 367 의 크기.", "이 셈은 둘째 모멘트 하나다."], size=11.2, gap=18)
    svg("fig17_toy", W, H, s, "1 차원 가우시안에서 끝 표준편차")


# ── 그림 18: 계보 ──────────────────────────────────────────────────────────
def fig18():
    W, H = 860, 300
    s = defs() + txt(W / 2, 26, "이 편의 자리: 학습은 그대로, 뽑기만 바뀐다", 15, weight="700")
    B = [(30, 90, 190, "DDPM (2020)", "학습 L_1, 걸음 1000", "뽑기 = 앞방향의 역", FWD_SOFT, FWD),
         (260, 90, 190, "DDIM (이 편)", "같은 체크포인트", "뽑기 = sigma, tau 를 고른다", REV_SOFT, REV),
         (490, 50, 170, "Score SDE (2021)", "확률 흐름 ODE", "동시 발표, 명제 1", CODE_SOFT, CODE),
         (490, 150, 170, "고차 풀이법", "원문 7절이 제안", "이 파일에 결과 없음", NODE, INK2),
         (690, 90, 150, "Latent Diffusion", "잠재 공간에서 확산", "다음 칸", OK_SOFT, OK)]
    for x, y, w, a, b, c, f, st in B:
        s += box(x, y, w, 78, f, st) + txt(x + w / 2, y + 24, a, 12.5, weight="700") + txt(x + w / 2, y + 45, b, 11, fill=INK2) + txt(x + w / 2, y + 63, c, 11, fill=INK2)
    s += line(222, 129, 258, 129, INK2, 1.6, marker="ai") + line(452, 115, 488, 92, INK2, 1.6, marker="ai") + line(452, 143, 488, 180, INK2, 1.6, marker="ai")
    s += line(662, 100, 688, 118, INK2, 1.6, marker="ai", op=0.5)
    s += txt(W / 2, 262, "남긴 빈칸: 공유 망에서 정리 1 의 근거 · 256 x 256 Church 의 역전 · 일관성과 보간을 재는 수.", 12, fill=NO, weight="700")
    svg("fig18_lineage", W, H, s, "이 편의 계보")


for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10, fig11, fig12, fig13, fig14, fig15, fig16, fig17, fig18):
    f()
print("끝.")
