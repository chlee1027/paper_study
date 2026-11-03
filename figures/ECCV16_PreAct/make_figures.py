# -*- coding: utf-8 -*-
"""사전 활성 ResNet 노트(He 외, Identity Mappings in Deep Residual Networks, ECCV 2016)의 그림 열여섯을 만든다.

색과 글꼴은 앞선 노트들(퍼셉트론부터 Wide ResNet 까지)의 그림과 맞췄다. 결과 그림의 계열 색은 셋을 고정한다 —
원래 블록 · 사전 활성 블록 · 지름길을 바꾼 변형.

  python make_figures.py

곡선 그림(논문 그림 1 오른쪽 · 그림 3 · 그림 6)의 값은 눈금을 눈으로 읽지 않았다. 세 그림이 PDF 안의 벡터 선이라
extract_curves.py 가 선 좌표를 꺼내 curves_data.py 로 적었고(그 파일만 pymupdf 가 필요하다), 이 파일은 그것을 읽는다.
이 파일은 표준 라이브러리만 쓴다.

이 파일이 직접 계산하는 것: CIFAR 망(ResNet-110 · 164 · 1001 · 1202)의 파라미터 수를 BN 을 넣고 / 빼고 센 값과
곱-덧셈 수, ImageNet 병목 망(ResNet-101 · 152 · 200)의 파라미터, 식 (7) 의 곱 항(상수 배 · 게이트 · 드롭아웃),
게이트 치우침 초기값별 1 - g 와 그 54 제곱, 1 차원 선형 예(식 (5) 의 '1 +' 항), 곡선에서 읽은 값(20% 아래로 들어오는 반복,
1 만 반복의 학습 손실, 끝 값). 계산한 값은 돌릴 때 화면에도 찍는다.
"""
import io, os, math

from curves_data import GRID, CURVES, SPAN

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"   # 그림 상자 배경
NODE      = "#F6F7F5"   # 노드 안쪽
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 지름길(항등)
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"
NO        = "#C0392B"
# 결과 그림 계열 색 — 원래 블록 · 사전 활성 블록 · 지름길 변형. 이 순서로 고정한다.
S_ORIG    = "#2A78D6"
S_PRE     = "#EB6834"
S_VAR     = "#1BAF7A"
BAND      = "#E9DFA8"   # 깨끗한 길(논문 그림의 회색 화살표 자리)
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
    return "<text %s>%s</text>" % (a, t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


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
    if len(pts) < 2:
        return ""
    d = "M" + " L".join("%.1f,%.1f" % p for p in pts)
    return path(d, stroke, sw=sw, dash=dash)


def fmt(n):
    return "{:,}".format(n)


def dot(x, y, col, r=4.5):
    return circ(x, y, r, col, col)


print("그림을 만든다 ->", OUT)


# ── 세는 도구 — 파라미터 수와 곱-덧셈 수 ─────────────────────────────────────
def cifar_basic(N, pre, opt="A", bn=True, ncls=10):
    """CIFAR 기본 블록 망(깊이 6N + 2). 폭 16 · 32 · 64, 출력 32 · 16 · 8.
    원래 블록: 합성곱 뒤 BN(출력 채널). 사전 활성: 합성곱 앞 BN(입력 채널) + 마지막 덧셈 뒤 BN 하나.
    opt A = 채널이 늘 때 0 을 채운 항등(파라미터 없음), B = 1x1 사영."""
    bnp = (lambda c: 2 * c) if bn else (lambda c: 0)
    P = 27 * 16 + (0 if pre else bnp(16))
    M = 27 * 16 * 1024
    cin = 16
    for c, s in ((16, 32), (32, 16), (64, 8)):
        for _ in range(N):
            P += 9 * cin * c + 9 * c * c + ((bnp(cin) + bnp(c)) if pre else 2 * bnp(c))
            M += (9 * cin * c + 9 * c * c) * s * s
            if cin != c and opt == "B":
                P += cin * c + (0 if pre else bnp(c))
                M += cin * c * s * s
            cin = c
    if pre:
        P += bnp(cin)
    P += cin * ncls + ncls
    M += cin * ncls
    return P, M


def cifar_bottleneck(N, pre, bn=True, ncls=10):
    """CIFAR 병목 망(깊이 9N + 2). 안쪽 폭 16 · 32 · 64, 출력 4 배. 채널이 바뀌는 첫 블록에 1x1 사영(부록)."""
    bnp = (lambda c: 2 * c) if bn else (lambda c: 0)
    P = 27 * 16 + (0 if pre else bnp(16))
    M = 27 * 16 * 1024
    cin = 16
    for c, s in ((16, 32), (32, 16), (64, 8)):
        o = 4 * c
        for _ in range(N):
            P += cin * c + 9 * c * c + c * o
            P += (bnp(cin) + bnp(c) + bnp(c)) if pre else (bnp(c) + bnp(c) + bnp(o))
            M += (cin * c + 9 * c * c + c * o) * s * s
            if cin != o:
                P += cin * o + (0 if pre else bnp(o))
                M += cin * o * s * s
            cin = o
    if pre:
        P += bnp(cin)
    P += cin * ncls + ncls
    M += cin * ncls
    return P, M


def imagenet_bottleneck(blocks):
    """ImageNet 원래 병목 망(torchvision 과 같은 셈). 사영 지름길 4 개(conv2 첫 블록 포함)."""
    P = 3 * 64 * 49 + 2 * 64
    cin, n_proj = 64, 0
    for si, n in enumerate(blocks):
        c = 64 * 2 ** si
        o = 4 * c
        for bi in range(n):
            P += cin * c + 2 * c + 9 * c * c + 2 * c + c * o + 2 * o
            if cin != o or (si > 0 and bi == 0):
                P += cin * o + 2 * o
                n_proj += 1
            cin = o
    P += cin * 1000 + 1000
    return P, n_proj


print("  [파라미터] CIFAR 망 — BN 을 넣고 / 빼고, 곱-덧셈")
NETS = [("ResNet-110", "basic", 18, 1.7), ("ResNet-164", "bott", 18, 1.7),
        ("ResNet-1001", "bott", 111, 10.2), ("ResNet-1202", "basic", 200, 19.4)]
pcount = {}
for name, kind, N, paper in NETS:
    f = (lambda **k: cifar_basic(N, **k)) if kind == "basic" else (lambda **k: cifar_bottleneck(N, **k))
    Po, Mo = f(pre=False)
    Pp, _ = f(pre=True)
    Pn, _ = f(pre=True, bn=False)
    P100, _ = f(pre=True, ncls=100)
    depth = (6 if kind == "basic" else 9) * N + 2
    units = 3 * N
    pcount[name] = (depth, units, Po, Pp, Pn, Mo, paper, P100)
    print("      %-12s 깊이 %4d 블록 %3d | 원래 %s | 사전 활성 %s | BN 빼고 %s | CIFAR-100 머리 %s | 곱-덧셈 %.3f G | 논문 %.1fM"
          % (name, depth, units, fmt(Po), fmt(Pp), fmt(Pn), fmt(P100), Mo / 1e9, paper))
m110 = pcount["ResNet-110"][5]
print("      곱-덧셈 배수: 1001 / 110 = %.2f, 1001 / 164 = %.2f, 164 / 110 = %.3f, 1202 / 110 = %.2f  (깊이 배수 1001/110 = %.2f)"
      % (pcount["ResNet-1001"][5] / m110, pcount["ResNet-1001"][5] / pcount["ResNet-164"][5],
         pcount["ResNet-164"][5] / m110, pcount["ResNet-1202"][5] / m110, 1001 / 110.0))
print("      ResNet-110 사영(B) 으로 세면 %s" % fmt(cifar_basic(18, False, "B")[0]))
for name, bl in (("ResNet-101", [3, 4, 23, 3]), ("ResNet-152", [3, 8, 36, 3]), ("ResNet-200", [3, 24, 36, 3])):
    P, npj = imagenet_bottleneck(bl)
    print("  [ImageNet] %s %s  사영 지름길 %d 개" % (name, fmt(P), npj))

# ── 식 (7) · (8) 의 곱 항 ────────────────────────────────────────────────
sig = lambda v: 1.0 / (1.0 + math.exp(-v))
print("  [곱 항] 54 블록(ResNet-110) · 18 블록(한 단계) · 333 블록(ResNet-1001)")
for lam in (0.5, 0.9, 0.99, 1 - sig(-6), 1.0):
    print("      lambda=%.5f  ^18 %.4g  ^54 %.4g  ^333 %.4g" % (lam, lam ** 18, lam ** 54, lam ** 333))
GATE = []
for bg in range(0, -11, -1):
    g = sig(bg)
    GATE.append((bg, g, 1 - g, (1 - g) ** 54))
    print("      b_g=%3d  g=%.5f  1-g=%.5f  (1-g)^54=%.4g" % (bg, g, 1 - g, (1 - g) ** 54))
print("  [1 차원 선형 예] F_i(x) = w x, 54 블록: 잔차 (1+w)^54, 평범 w^54")
for w in (0.01, -0.01, 0.1):
    print("      w=%+.2f  잔차 %.4g  평범 %.4g" % (w, (1 + w) ** 54, abs(w) ** 54))

# ── 곡선에서 읽은 값 ────────────────────────────────────────────────────────
def val(key, it):
    return CURVES[key][GRID.index(it)]


def last(key):
    v = [x for x in CURVES[key] if x is not None]
    return v[-1]


print("  [곡선] 시험 오차가 그림의 20% 아래로 들어오는 반복 · 1 만 반복의 손실 · 64k 의 값 · 선의 끝")
for k in sorted(CURVES):
    if k.endswith("_err"):
        base = k[:-4]
        print("      %-14s 20%% 아래로 %6d | 손실 1만 %.3f | 오차 64k %.3f 끝 %.3f | 손실 64k %.4g"
              % (base, SPAN[k][0], val(base + "_loss", 10000), val(k, 64000), last(k), val(base + "_loss", 64000)))
for k in ("r1001_pre_loss", "r164_orig_loss", "r110_base_loss", "r1001_orig_loss", "r164_pre_loss"):
    seg = [v for t, v in zip(GRID, CURVES[k]) if t >= 48000 and v is not None]
    print("      %-16s 48k 뒤 손실이 축 바닥(0.002)에 붙은 점 %d / %d" % (k, sum(1 for v in seg if v < 0.00199), len(seg)))
for k in ("r164_orig_loss", "r164_pre_loss"):
    seg = [v for t, v in zip(GRID, CURVES[k]) if t >= 60000 and v is not None]
    print("      %-16s 60k 뒤 손실의 기하평균 %.5f (%d 점)" % (k, math.exp(sum(math.log(v) for v in seg) / len(seg)), len(seg)))


def gmean(key, start=60000):
    seg = [v for t, v in zip(GRID, CURVES[key]) if t >= start and v is not None]
    return math.exp(sum(math.log(v) for v in seg) / len(seg))


# ── 블록 그리기 도구 ────────────────────────────────────────────────────────
KIND = {"weight": (NODE, INK2), "BN": (CODE_SOFT, CODE), "ReLU": (FWD_SOFT, FWD), "act.": (CODE_SOFT, CODE),
        "addition": ("#FFFFFF", INK), "1x1 conv": (FWD_SOFT, FWD), "dropout": (REV_SOFT, REV),
        "3x3 conv": (NODE, INK2), "x 0.5": ("#FFFFFF", NO), "x (1-g)": ("#FFFFFF", NO), "x g": ("#FFFFFF", INK2)}


def kind_of(lab):
    return KIND.get(lab, (NODE, INK2))


def unit(b, x0, y0, title, branch, post=(), short=(), w=150, step=30, bw=78, foot=None, foot_col=None):
    """세로로 선 잔차 블록 하나. 왼쪽 줄기(깨끗한 길) 위에 short(지름길 위 연산) · 덧셈 · post(덧셈 뒤 연산)."""
    trunk = x0 + 24
    bx = x0 + w - bw / 2 - 6
    top = y0 + 34
    n = len(branch)
    yadd = top + 18 + n * step
    yend = yadd + 22 + max(1, len(post)) * step + 6
    blocked = bool(short) or bool(post)
    b += '<rect x="%s" y="%s" width="18" height="%s" fill="%s" opacity="0.9"/>' % (trunk - 9, y0 + 8, yend - y0 - 8, BAND)
    b += txt(x0 + w / 2, y0, title, 12, weight="bold")
    b += txt(trunk, y0 + 22, "x_l", 11, fill=INK2)
    b += line(trunk, y0 + 26, trunk, yadd - 9, INK2, 1.2)
    b += circ(trunk, top - 4, 2.5, INK, INK)
    b += path("M%s,%s L%s,%s L%s,%s" % (trunk, top - 4, bx, top - 4, bx, top + 4), INK2, sw=1.1, marker="ai")
    for j, lab in enumerate(branch):
        y = top + 6 + j * step
        fill, st = kind_of(lab)
        b += box(bx - bw / 2, y, bw, 20, fill=fill, stroke=st, sw=1.0, rx=3)
        b += txt(bx, y + 14, lab, 10.5)
        if j < n - 1:
            b += line(bx, y + 20, bx, y + step, INK2, 1.0, marker="ai")
    b += path("M%s,%s L%s,%s L%s,%s" % (bx, top + 6 + (n - 1) * step + 20, bx, yadd - 4, trunk + 32, yadd - 4), INK2, sw=1.1, marker="ai")
    for j, lab in enumerate(short):
        y = top + 30 + j * 30
        fill, st = kind_of(lab)
        b += box(trunk - 30, y, 60, 20, fill=fill, stroke=NO, sw=1.6, rx=3)
        b += txt(trunk, y + 14, lab, 10.5)
    b += box(trunk - 30, yadd - 12, 60, 18, fill="#FFFFFF", stroke=INK, sw=1.0, rx=3)
    b += txt(trunk, yadd + 1, "addition", 10)
    y = yadd + 6
    for j, lab in enumerate(post):
        y = yadd + 14 + j * step
        fill, st = kind_of(lab)
        b += box(trunk - 30, y, 60, 20, fill=fill, stroke=NO, sw=1.6, rx=3)
        b += txt(trunk, y + 14, lab, 10.5)
        y += 20
    b += line(trunk, y, trunk, yend - 6, INK2, 1.2, marker="ai")
    b += txt(trunk + 22, yend - 6, "x_l+1", 11, fill=INK2, anchor="start")
    if foot:
        b += txt(x0 + w / 2, yend + 18, foot, 11.5, fill=foot_col or INK, weight="bold")
    return b, yend


# ── 그림 1. 원래 블록과 사전 활성 블록 (논문 그림 1 왼쪽) ─────────────────────────
W, H = 820, 470
b = defs()
b += txt(20, 30, "원래 블록과 사전 활성 블록 (논문 그림 1 왼쪽) — 노란 띠 = 연산 없이 이어지는 길, 빨간 테 = 그 길 위에 놓인 연산", 13.5, anchor="start", weight="bold")
b, _ = unit(b, 40, 60, "(a) 원래 (ResNet 2015)", ["weight", "BN", "ReLU", "weight", "BN"], post=["ReLU"], w=230, step=34, bw=90,
            foot="f = ReLU 가 길 위에 있다", foot_col=NO)
b, _ = unit(b, 300, 60, "(b) 사전 활성 (이 논문)", ["BN", "ReLU", "weight", "BN", "ReLU", "weight"], post=[], w=230, step=34, bw=90,
            foot="덧셈 뒤가 비어 있다: f = 항등", foot_col=OK)
tx = 560
for i, (t, c) in enumerate([("같은 부품(가중치 둘 · BN 둘 · ReLU 둘)의", INK),
                            ("순서만 바꿨다.", INK),
                            ("", INK),
                            ("(a) 다음 블록의 입력 x_l+1 = ReLU(y_l)", S_ORIG),
                            ("   - 늘 0 이상이고, 덧셈 결과가 음수인", S_ORIG),
                            ("     자리는 다음 블록으로 가지 않는다", S_ORIG),
                            ("", INK),
                            ("(b) x_l+1 = y_l = x_l + F(x_l)", S_PRE),
                            ("   - 식 (3) 이 근사 없이 성립한다", S_PRE),
                            ("   - 모든 가중치 층의 입력이 BN 을", S_PRE),
                            ("     거친 값이다 (4.2절, 정칙화 설명)", S_PRE),
                            ("", INK),
                            ("표 3 · CIFAR-10 · 다섯 번의 중앙값", INK2),
                            ("  ResNet-164  5.93 -> 5.46", INK2),
                            ("  ResNet-1001 7.61 -> 4.92", INK2)]):
    b += txt(tx, 92 + i * 22, t, 11.5, anchor="start", fill=c)
svg("fig01_units", W, H, b, "원래 블록과 사전 활성 블록")


# ── 곡선 판 그리기 도구 ──────────────────────────────────────────────────────
def curve_panel(b, x0, y0, w, h, series, title, err_max=20.0, notes=()):
    """논문 그림과 같은 두 축: 오른쪽 시험 오차 0~20 % (실선), 왼쪽 학습 손실 0.002~2 로그 (점선)."""
    X = lambda t: x0 + t / 68000.0 * w
    YE = lambda v: y0 + h - min(v, err_max) / err_max * h
    YL = lambda v: y0 + h - (math.log10(min(max(v, 0.002), 2.0)) - math.log10(0.002)) / 3.0 * h
    b += box(x0, y0, w, h, fill="#FFFFFF", stroke=LINE, sw=1, rx=0)
    for v in (5, 10, 15):
        b += line(x0, YE(v), x0 + w, YE(v), LINE, 0.8)
    for v in (0, 5, 10, 15, 20):
        b += txt(x0 + w + 5, YE(v) + 4, "%d" % v, 9.5, anchor="start", fill=MUTED)
    for v in (0.002, 0.02, 0.2, 2):
        b += txt(x0 - 5, YL(v) + 4, "%g" % v, 9.5, anchor="end", fill=MUTED)
    for t in (0, 20000, 40000, 60000):
        b += txt(X(t), y0 + h + 14, "%dk" % (t // 1000), 9.5, fill=MUTED)
    for t in (32000, 48000):
        b += line(X(t), y0, X(t), y0 + h, MUTED, 0.8, dash="2,3")
    b += txt(x0 + w / 2, y0 - 8, title, 11.5, weight="bold")
    for key, col in series:
        e = [(X(t), YE(v)) for t, v in zip(GRID, CURVES[key + "_err"]) if v is not None]
        l = [(X(t), YL(v)) for t, v in zip(GRID, CURVES[key + "_loss"]) if v is not None]
        b += polyline(l, col, 1.2, dash="4,3")
        b += polyline(e, col, 2.0)
    for i, (t, c) in enumerate(notes):
        b += txt(x0 + w - 6, y0 + 16 + 15 * i, t, 10, anchor="end", fill=c)
    return b


# ── 그림 2. ResNet-1001 학습 곡선 (논문 그림 1 오른쪽) ─────────────────────────
W, H = 820, 430
b = defs()
b += txt(20, 30, "ResNet-1001 학습 곡선 (논문 그림 1 오른쪽, PDF 의 벡터 선에서 꺼낸 값) — 실선 시험 오차(오른쪽 축), 점선 학습 손실(왼쪽 로그 축)", 13, anchor="start", weight="bold")
b = curve_panel(b, 70, 70, 470, 290, [("r1001_orig", S_ORIG), ("r1001_pre", S_PRE)], "CIFAR-10, 1001 층 병목 망",
                notes=[("원래 블록 끝 %.2f%%" % last("r1001_orig_err"), S_ORIG), ("사전 활성 끝 %.2f%%" % last("r1001_pre_err"), S_PRE)])
b += txt(305, 395, "반복 (회색 점선 = 학습률 / 10 자리, 32k · 48k)", 10, fill=MUTED)
tx = 590
rows = [("읽은 값 (500 반복 간격)", INK, "bold"),
        ("시험 오차가 20% 아래로", INK2, None),
        ("  원래 %s 반복, 사전 활성 %s 반복" % (fmt(SPAN["r1001_orig_err"][0]), fmt(SPAN["r1001_pre_err"][0])), INK, None),
        ("1 만 반복의 학습 손실", INK2, None),
        ("  원래 %.2f, 사전 활성 %.2f" % (val("r1001_orig_loss", 10000), val("r1001_pre_loss", 10000)), INK, None),
        ("64k 의 학습 손실", INK2, None),
        ("  원래 %.4f" % val("r1001_orig_loss", 64000), S_ORIG, None),
        ("  사전 활성 0.002 아래 (축 바닥에 붙음)", S_PRE, None),
        ("", INK, None),
        ("축 밖은 그림에서 잘려 있다", MUTED, None),
        ("(오차 20% 위 · 손실 2 위 · 0.002 아래)", MUTED, None),
        ("선은 틀 오른쪽 끝(6.8만)까지 간다.", MUTED, None),
        ("끝나는 반복은 본문에 없다.", MUTED, None)]
for i, (t, c, wgt) in enumerate(rows):
    b += txt(tx, 84 + i * 22, t, 11, anchor="start", fill=c, weight=wgt)
svg("fig02_resnet1001_curves", W, H, b, "ResNet-1001 학습 곡선")


# ── 그림 3. 식 (4) · (5) — 앞으로 더하고, 뒤로 '1 +' ──────────────────────────
W, H = 820, 420
b = defs()
b += txt(20, 30, "식 (4) · (5) — 덧셈 뒤가 항등이면 깊은 블록 L 의 특징은 얕은 블록 l 의 특징에 잔차를 더한 합이다", 13.5, anchor="start", weight="bold")
xs = [90 + 130 * i for i in range(5)]
yt = 120
b += '<rect x="%s" y="%s" width="%s" height="14" fill="%s"/>' % (xs[0] - 20, yt - 7, xs[-1] - xs[0] + 60, BAND)
labels = ["x_l", "x_l+1", "x_l+2", "...", "x_L"]
for i, x in enumerate(xs):
    b += circ(x, yt, 15, NODE, INK)
    b += txt(x, yt + 4, labels[i], 10.5)
    if i < len(xs) - 1:
        b += line(x + 15, yt, xs[i + 1] - 17, yt, CODE, 2.2, marker="ac")
        mx = (x + xs[i + 1]) / 2
        b += box(mx - 22, yt + 34, 44, 24, fill=REV_SOFT, stroke=REV, sw=1.2, rx=4)
        b += txt(mx, yt + 50, "F_%s" % ("l" if i == 0 else ("l+%d" % i if i < 3 else "L-1")), 10.5)
        b += path("M%s,%s Q%s,%s %s,%s" % (x + 8, yt + 13, x + 20, yt + 46, mx - 22, yt + 46), REV, sw=1.1, marker="ar")
        b += path("M%s,%s Q%s,%s %s,%s" % (mx + 22, yt + 46, xs[i + 1] - 20, yt + 46, xs[i + 1] - 8, yt + 13), REV, sw=1.1, marker="ar")
b += txt(xs[2], yt - 26, "노란 길: 가중치를 하나도 거치지 않고 x_l 이 x_L 로 간다", 11, fill=CODE)
b += txt(40, 230, "앞으로 (식 4)   x_L = x_l + Σ_{i=l}^{L-1} F(x_i, W_i)", 13, anchor="start", fill=FWD, weight="bold")
b += txt(40, 256, "뒤로 (식 5)     ∂E/∂x_l = ∂E/∂x_L · ( 1 + ∂/∂x_l Σ F )   — 다차원이면 1 은 단위 행렬 I", 13, anchor="start", fill=REV, weight="bold")
b += txt(40, 282, "평범한 망은 곱 (식 4 아래 문장)   x_L = W_{L-1} ··· W_l x_l   (BN · ReLU 를 무시하면)", 12, anchor="start", fill=INK2)
b += box(40, 300, 740, 96, fill=NODE, stroke=LINE, rx=6)
b += txt(56, 324, "내가 붙인 1 차원 예 (논문에 없다) — F_i(x) = w x, 블록 54 개 (ResNet-110 의 블록 수)", 12, anchor="start", weight="bold")
b += txt(56, 348, "잔차: ∂x_L/∂x_l = (1 + w)^54  ·  w = 0.01 이면 %.3f, w = -0.01 이면 %.3f" % (1.01 ** 54, 0.99 ** 54), 12, anchor="start", fill=S_PRE)
b += txt(56, 370, "평범: ∂x_L/∂x_l = w^54  ·  w = 0.01 이면 %.0e" % (0.01 ** 54), 12, anchor="start", fill=S_ORIG)
b += txt(56, 390, "논문의 '가중치가 아무리 작아도 기울기가 사라지지 않는다' 는 이 자리 — 대신 (1+w) 가 1 에서 멀면 곱이 커지거나 작아진다", 11, anchor="start", fill=MUTED)
svg("fig03_propagation", W, H, b, "식 4 와 5 의 전파")


# ── 그림 4. 식 (7) 의 곱 항 ∏λ ───────────────────────────────────────────────
W, H = 820, 430
b = defs()
b += txt(20, 30, "식 (7) · (8) — 지름길에 λ 를 곱하면 첫 항이 λ 의 곱이 된다 (블록 수에 대해 지수)", 13.5, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 90, 560, 370, 70
LMIN, LMAX = -18, 1
X = lambda n: PX0 + n / 340.0 * (PX1 - PX0)
Y = lambda v: PY0 - (max(math.log10(v), LMIN) - LMIN) / float(LMAX - LMIN) * (PY0 - PY1) if v > 0 else PY0
for e in range(LMIN, LMAX + 1, 3):
    b += line(PX0, Y(10 ** e), PX1, Y(10 ** e), LINE, 0.8)
    b += txt(PX0 - 6, Y(10 ** e) + 4, "1e%d" % e, 9.5, anchor="end", fill=MUTED)
for n in (0, 54, 100, 200, 333):
    b += txt(X(n), PY0 + 16, "%d" % n, 9.5, fill=MUTED)
for n, lab in ((54, "ResNet-110 (54)"), (333, "ResNet-1001 (333)")):
    b += line(X(n), PY1, X(n), PY0, MUTED, 1, dash="3,3")
    b += txt(X(n) + 4, PY1 + 12, lab, 10, anchor="start", fill=MUTED)
b += txt((PX0 + PX1) / 2, PY0 + 34, "지나는 블록 수 L - l", 10.5, fill=MUTED)
lams = [(0.5, NO, "λ = 0.5 (상수 배 · 드롭아웃 기대값)"), (0.9, S_ORIG, "λ = 0.9"), (0.99, S_VAR, "λ = 0.99"),
        (1 - sig(-6), CODE, "λ = 1 - σ(-6) = 0.9975 (게이트 초기값)"), (1.0, S_PRE, "λ = 1 (항등)")]
for lam, col, lab in lams:
    pts = []
    for n in range(0, 341, 2):
        v = lam ** n
        if v <= 0 or math.log10(v) < LMIN:
            break
        pts.append((X(n), Y(v)))
    b += polyline(pts, col, 2.0)
for i, (lam, col, lab) in enumerate(lams):
    b += line(590, 86 + i * 24, 616, 86 + i * 24, col, 2.4)
    b += txt(622, 90 + i * 24, lab, 10.5, anchor="start", fill=col)
rows = ["블록 54 개를 지나면", "  0.5^54 = %.2e" % (0.5 ** 54), "  0.9^54 = %.4f" % (0.9 ** 54),
        "  0.99^54 = %.3f" % (0.99 ** 54), "  0.9975^54 = %.3f" % ((1 - sig(-6)) ** 54),
        "블록 333 개를 지나면", "  0.99^333 = %.3f" % (0.99 ** 333), "  0.9975^333 = %.3f" % ((1 - sig(-6)) ** 333)]
for i, t in enumerate(rows):
    b += txt(590, 222 + i * 20, t, 10.5, anchor="start", fill=INK2 if not t.startswith(" ") else INK)
b += txt(20, 424, "논문은 λ > 1 이면 지수로 커지고 λ < 1 이면 지수로 작아진다고만 적는다. 위 수는 내가 센 것이다. 이 식은 f = 항등을 가정한다 — 표 1 의 실험은 f = ReLU 다", 10.5, anchor="start", fill=MUTED)
svg("fig04_shortcut_product", W, H + 8, b, "지름길 곱 항")


# ── 그림 5. 지름길 여섯 (논문 그림 2) ──────────────────────────────────────────
W, H = 820, 560
b = defs()
b += txt(20, 30, "지름길 여섯 (논문 그림 2) — ResNet-110, f = ReLU, BN 은 그림에서 뺐다(가중치 층 바로 뒤에 있다). 아래 수는 표 1 시험 오차", 13, anchor="start", weight="bold")
br = ["3x3 conv", "ReLU", "3x3 conv"]
V = [("(a) 원래", br, [], "6.61", S_PRE), ("(b) 상수 배 0.5 / 0.5", br + ["x 0.5"], ["x 0.5"], "12.35", NO),
     ("(c) 배타 게이트", br + ["x g"], ["x (1-g)"], "8.70 (b_g=-6)", NO),
     ("(d) 지름길만 게이트", br, ["x (1-g)"], "6.91 (b_g=-6) / 12.86 (0)", NO),
     ("(e) 1x1 합성곱 지름길", br, ["1x1 conv"], "12.22", NO), ("(f) 드롭아웃 지름길", br, ["dropout"], "fail (> 20)", NO)]
for i, (t, brr, sh, err, col) in enumerate(V):
    x0 = 20 + (i % 3) * 265
    y0 = 62 + (i // 3) * 250
    b, _ = unit(b, x0, y0, t, brr, post=["ReLU"], short=sh, w=230, step=27, bw=74, foot=err, foot_col=col)
b += txt(410, 548, "(c) (d) 의 g(x) = σ(1x1 conv(x) + b_g). 빨간 테 = 지름길 위에 놓인 연산. 덧셈 뒤 ReLU 는 여섯 모두 같다", 11, fill=MUTED)
svg("fig05_shortcut_types", W, H, b, "지름길 여섯")


# ── 그림 6. 표 1 ──────────────────────────────────────────────────────────
T1 = [("원래", "1", "1", 6.61, ""), ("상수 배", "0", "1", None, "평범한 망"), ("상수 배", "0.5", "1", None, ""),
      ("상수 배", "0.5", "0.5", 12.35, "얼린 게이트"), ("배타 게이트", "1-g", "g", None, "b_g = 0 ~ -5"),
      ("배타 게이트", "1-g", "g", 8.70, "b_g = -6"), ("배타 게이트", "1-g", "g", 9.81, "b_g = -7"),
      ("지름길만 게이트", "1-g", "1", 12.86, "b_g = 0"), ("지름길만 게이트", "1-g", "1", 6.91, "b_g = -6"),
      ("1x1 합성곱", "1x1", "1", 12.22, ""), ("드롭아웃", "0.5", "1", None, "")]
W, H = 820, 500
b = defs()
b += txt(20, 30, "표 1 — ResNet-110 · CIFAR-10 시험 오차 (%). fail = 20% 를 넘은 것 (논문의 정의). 세로 점선 = 원래 6.61", 13.5, anchor="start", weight="bold")
PX0, PX1 = 330, 760
X = lambda v: PX0 + v / 22.0 * (PX1 - PX0)
b += txt(40, 66, "지름길 · 지름길 위 · F 위 · 비고", 10.5, anchor="start", fill=MUTED)
for i, (case, onS, onF, err, rem) in enumerate(T1):
    y = 80 + i * 32
    b += txt(40, y + 15, case, 11.5, anchor="start")
    b += txt(160, y + 15, onS, 11, fill=NO if onS != "1" else INK2)
    b += txt(205, y + 15, onF, 11, fill=INK2)
    b += txt(240, y + 15, rem, 10, anchor="start", fill=MUTED)
    if err is None:
        b += '<rect x="%s" y="%s" width="%s" height="20" fill="%s" opacity="0.35"/>' % (PX0, y, X(20) - PX0, NO)
        b += line(X(20), y, X(22), y + 20, NO, 1.2, dash="3,2")
        b += txt(X(20) - 6, y + 15, "fail (> 20)", 10.5, anchor="end", fill=NO, weight="bold")
    else:
        col = S_PRE if case == "원래" else S_VAR
        b += box(PX0, y, X(err) - PX0, 20, fill=col, stroke=col, rx=2)
        b += txt(X(err) + 6, y + 15, "%.2f" % err, 11, anchor="start", weight="bold")
b += line(X(6.61), 72, X(6.61), 80 + 11 * 32, INK2, 1.2, dash="3,3")
for v in (0, 5, 10, 15, 20):
    b += txt(X(v), 80 + 11 * 32 + 16, "%d" % v, 9.5, fill=MUTED)
b += txt(20, 470, "변형 열 행 중 원래(6.61)보다 낮은 행은 없다. 가장 가까운 것은 지름길만 게이트(b_g=-6)의 +0.30 이다", 10.5, anchor="start", fill=MUTED)
b += txt(20, 488, "이 논문의 CIFAR 표에서 흩어짐이 적힌 것은 1001 층 행뿐이라 +0.30 이 흔들림 밖인지 판정하지 않는다", 10.5, anchor="start", fill=MUTED)
svg("fig06_table1", W, H, b, "표 1 지름길 실험")


# ── 그림 7. 지름길 변형의 학습 곡선 (논문 그림 3) ───────────────────────────────
W, H = 820, 620
b = defs()
b += txt(20, 30, "지름길 변형의 학습 곡선 (논문 그림 3, 벡터 선에서 꺼낸 값) — 파랑 = ResNet-110 원래(네 판에 같은 선), 초록 = 변형", 13, anchor="start", weight="bold")
P3 = [("r110_scale", "(a) 상수 배 (0.5, 0.5)"), ("r110_exgate", "(b) 배타 게이트 b_g = -6"),
      ("r110_scgate", "(c) 지름길만 게이트 b_g = 0"), ("r110_conv", "(d) 1x1 합성곱 지름길")]
for i, (k, t) in enumerate(P3):
    x0 = 70 + (i % 2) * 390
    y0 = 72 + (i // 2) * 270
    b = curve_panel(b, x0, y0, 300, 200, [("r110_base", S_ORIG), (k, S_VAR)], t,
                    notes=[("20%% 아래로 %s / %s" % (fmt(SPAN["r110_base_err"][0]), fmt(SPAN[k + "_err"][0])), INK2),
                           ("64k 손실 %.4f / %.4f" % (val("r110_base_loss", 64000), val(k + "_loss", 64000)), INK2),
                           ("끝 오차 %.2f / %.2f" % (last("r110_base_err"), last(k + "_err")), INK2)])
b += txt(410, 600, "판 안의 수 = 원래 / 변형. 넷 모두 변형의 학습 손실이 끝까지 원래보다 높다 — 논문의 '최적화가 어려워졌다' 는 이 자리", 11, fill=MUTED)
b += txt(410, 616, "판마다 범례 글자와 선의 끝 값을 표 1 과 맞춰 어느 변형인지 확인했다 (끝 값 차이 0.00 ~ 0.22)", 10, fill=MUTED)
svg("fig07_shortcut_curves", W, H + 6, b, "지름길 변형 학습 곡선")


# ── 그림 8. 게이트 치우침 b_g ────────────────────────────────────────────────
W, H = 820, 430
b = defs()
b += txt(20, 30, "게이트 치우침 b_g — 처음 값만으로 지름길이 얼마나 열려 있나 (1x1 합성곱 출력을 0 으로 두고 내가 센 것)", 13.5, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 70, 370, 350, 80
X = lambda bg: PX0 + (-bg) / 10.0 * (PX1 - PX0)
Y = lambda v: PY0 - v * (PY0 - PY1)
for v in (0, 0.25, 0.5, 0.75, 1.0):
    b += line(PX0, Y(v), PX1, Y(v), LINE, 0.8)
    b += txt(PX0 - 6, Y(v) + 4, "%g" % v, 9.5, anchor="end", fill=MUTED)
for bg in range(0, -11, -2):
    b += txt(X(bg), PY0 + 16, "%d" % bg, 9.5, fill=MUTED)
b += txt((PX0 + PX1) / 2, PY0 + 34, "b_g 처음 값", 10.5, fill=MUTED)
b += polyline([(X(bg), Y(1 - g)) for bg, g, _, _ in GATE], CODE, 2.2)
b += polyline([(X(bg), Y(p)) for bg, _, _, p in GATE], NO, 2.2)
b += polyline([(X(bg), Y(g)) for bg, g, _, _ in GATE], REV, 1.6, dash="4,3")
b += txt(PX1 - 2, Y(1 - GATE[-1][1]) - 8, "1 - g (블록 하나의 지름길)", 10.5, anchor="end", fill=CODE)
b += txt(X(-3.2), Y(0.12), "(1 - g)^54 (110 층 전체)", 10.5, anchor="start", fill=NO)
b += txt(X(-1.4), Y(0.30), "g (F 쪽, 배타 게이트)", 10.5, anchor="start", fill=REV)
tx = 420
b += txt(tx, 84, "표 1 의 결과 (시험 오차 %)", 12, anchor="start", weight="bold")
rows = [("b_g", "1 - g", "(1-g)^54", "배타", "지름길만")]
res = {0: ("fail", "12.86"), -1: ("fail", ""), -2: ("fail", ""), -3: ("fail", ""), -4: ("fail", ""), -5: ("fail", ""),
       -6: ("8.70", "6.91"), -7: ("9.81", "")}
for bg, g, og, p in GATE[:8]:
    e = res.get(bg, ("", ""))
    rows.append(("%d" % bg, "%.4f" % og, "%.3g" % p, e[0], e[1] or "-"))
for i, r in enumerate(rows):
    y = 110 + i * 24
    for j, (c, xx) in enumerate(zip(r, (0, 52, 130, 220, 290))):
        col = INK if i else INK2
        if j >= 3 and c == "fail":
            col = NO
        b += txt(tx + xx, y, c, 11, anchor="start", fill=col, weight="bold" if i == 0 else None)
b += txt(tx, 110 + 9 * 24 + 6, "b_g 는 0 ~ -10 을 학습 집합 교차 검증으로 골랐다(본문).", 10.5, anchor="start", fill=MUTED)
b += txt(tx, 110 + 9 * 24 + 26, "표에 적힌 것은 위 여덟 행뿐이다.", 10.5, anchor="start", fill=MUTED)
b += txt(20, 418, "배타 게이트는 1 - g 가 1 에 가까울수록 F 쪽 g 가 0 에 가까워진다 — 지름길을 열면 잔차 가지가 닫힌다. 그래서 논문은 지름길만 게이트로 따로 쟀다", 10.5, anchor="start", fill=MUTED)
svg("fig08_gate_bias", W, H, b, "게이트 치우침")


# ── 그림 9. 활성 위치 다섯 (논문 그림 4) ────────────────────────────────────────
W, H = 820, 470
b = defs()
b += txt(20, 30, "활성 위치 다섯 (논문 그림 4) — 부품은 같고 순서만 다르다. 아래 수 = 표 2 의 ResNet-110 / ResNet-164", 13.5, anchor="start", weight="bold")
A = [("(a) 원래", ["weight", "BN", "ReLU", "weight", "BN"], ["ReLU"], "6.61 / 5.93", INK),
     ("(b) 덧셈 뒤 BN", ["weight", "BN", "ReLU", "weight"], ["BN", "ReLU"], "8.17 / 6.50", NO),
     ("(c) 덧셈 앞 ReLU", ["weight", "BN", "ReLU", "weight", "BN", "ReLU"], [], "7.84 / 6.14", NO),
     ("(d) ReLU 만 앞으로", ["ReLU", "weight", "BN", "ReLU", "weight", "BN"], [], "6.71 / 5.91", INK),
     ("(e) 완전 사전 활성", ["BN", "ReLU", "weight", "BN", "ReLU", "weight"], [], "6.37 / 5.46", S_PRE)]
for i, (t, brr, post, err, col) in enumerate(A):
    b, _ = unit(b, 14 + i * 161, 62, t, brr, post=post, w=152, step=30, bw=64, foot=err, foot_col=col)
b += txt(410, 440, "(c) 는 덧셈 뒤가 비었지만 F 가 ReLU 로 끝나 늘 0 이상이다 — 앞으로 가는 신호가 블록마다 커지기만 한다(본문)", 11, fill=MUTED)
b += txt(410, 460, "(d) 와 (e) 는 F 가 BN 이나 가중치로 끝나 음수도 낸다. 둘 중 BN 을 ReLU 와 함께 앞으로 옮긴 (e) 만 나아졌다", 11, fill=MUTED)
svg("fig09_activation_orders", W, H + 8, b, "활성 위치 다섯")


# ── 그림 10. 표 2 ─────────────────────────────────────────────────────────
T2 = [("(a) 원래", 6.61, 5.93), ("(b) 덧셈 뒤 BN", 8.17, 6.50), ("(c) 덧셈 앞 ReLU", 7.84, 6.14),
      ("(d) ReLU 만 사전 활성", 6.71, 5.91), ("(e) 완전 사전 활성", 6.37, 5.46)]
W, H = 820, 400
b = defs()
b += txt(20, 30, "표 2 — 활성 위치별 CIFAR-10 시험 오차 (%), 원래 (a) 와의 차이를 함께", 13.5, anchor="start", weight="bold")
PX0, PX1 = 230, 700
X = lambda v: PX0 + (v - 5.0) / 3.5 * (PX1 - PX0)
for v in (5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5):
    b += line(X(v), 62, X(v), 340, LINE, 0.8)
    b += txt(X(v), 356, "%.1f" % v, 9.5, fill=MUTED)
for i, (t, a, c) in enumerate(T2):
    y = 74 + i * 54
    b += txt(40, y + 22, t, 12, anchor="start")
    for j, (v, base, col, lab) in enumerate(((a, 6.61, S_ORIG, "110"), (c, 5.93, S_PRE, "164"))):
        yy = y + j * 20
        b += box(PX0, yy, X(v) - PX0, 16, fill=col, stroke=col, rx=2, sw=0.5)
        d = v - base
        b += txt(X(v) + 6, yy + 13, "%s  %.2f%s" % (lab, v, "" if i == 0 else "  (%+.2f)" % d), 10.5, anchor="start")
b += line(X(6.61), 66, X(6.61), 340, S_ORIG, 1, dash="3,3")
b += line(X(5.93), 66, X(5.93), 340, S_PRE, 1, dash="3,3")
b += txt(20, 384, "막대는 5.0 에서 시작한다. (d) 의 +0.10 / -0.02 를 논문은 '원래와 매우 비슷하다' 고 읽는다. 다섯 번의 흩어짐은 이 표에 없다", 10.5, anchor="start", fill=MUTED)
svg("fig10_table2", W, H, b, "표 2 활성 위치")


# ── 그림 11. 덧셈 뒤 활성을 다음 블록의 앞으로 (논문 그림 5) ──────────────────────
W, H = 820, 470
b = defs()
b += txt(20, 30, "식 (9) · 그림 5 — 덧셈 뒤 활성을 잔차 가지에만 걸면, 그것은 다음 블록의 사전 활성과 같은 망이다", 13.5, anchor="start", weight="bold")


def chain(b, y, acts_on_trunk, groups, title, col):
    """가로로 놓은 블록 둘. acts_on_trunk=True 면 덧셈 뒤 act 가 줄기 위, False 면 가지 시작에.
    블록 u 의 시작점 sx = 60 + 370 u. 가지 상자 폭 54, 간격 60."""
    b += txt(20, y - 74, title, 12, anchor="start", weight="bold", fill=col)
    b += line(30, y, 790, y, INK2, 1.2)
    for u in range(2):
        sx = 60 + u * 370
        b += circ(sx, y, 3, INK, INK)
        ops = (["weight", "act.", "weight"] if acts_on_trunk else ["act.", "weight", "act.", "weight"])
        for j, op in enumerate(ops):
            fill, st = kind_of(op)
            ox = sx + 24 + j * 60
            moved = (op == "act." and j == 0 and not acts_on_trunk)
            b += box(ox, y - 46, 54, 20, fill=fill, stroke=(NO if moved else st), sw=1.6 if moved else 1.0, rx=3)
            b += txt(ox + 27, y - 32, op, 10)
        ex = sx + 24 + len(ops) * 60
        b += path("M%s,%s L%s,%s L%s,%s" % (sx, y, sx, y - 36, sx + 22, y - 36), INK2, sw=1, marker="ai")
        b += path("M%s,%s L%s,%s" % (ex - 4, y - 36, ex + 12, y - 9), INK2, sw=1, marker="ai")
        b += circ(ex + 16, y, 8, "#FFFFFF", INK)
        b += txt(ex + 16, y + 4, "+", 11)
        if acts_on_trunk:
            b += box(ex + 34, y - 10, 46, 20, fill=CODE_SOFT, stroke=NO, sw=1.6, rx=3)
            b += txt(ex + 57, y + 4, "act.", 10)
    for (gx0, gx1, lab) in groups:
        b += box(gx0, y - 56, gx1 - gx0, 72, fill="none", stroke=col, sw=1.4, dash="5,4", rx=8)
        b += txt((gx0 + gx1) / 2, y + 32, lab, 10.5, fill=col)
    return b


# (a) 가지 끝 = 60+24+180 = 264, 덧셈 280, 줄기 act 298~344
b = chain(b, 128, True, [(48, 350, "원래 블록 = [가지 · 덧셈 · 덧셈 뒤 act]")],
          "(a) 원래: 덧셈 뒤 act 가 줄기 위에 있다 — 다음 블록의 두 길(줄기와 가지) 모두에 걸린다", S_ORIG)
# (b) 가지 끝 = 60+24+240 = 324, 덧셈 340. 다음 블록 첫 act = 430+24 ~ 508
b = chain(b, 268, False, [(326, 514, "비대칭 출력 활성 = [덧셈 · 다음 가지의 첫 act]")],
          "(b) 그 act 를 다음 블록의 가지에만 건다 — 줄기 위에는 덧셈 말고 아무것도 없다 (f = 항등)", INK2)
b = chain(b, 408, False, [(420, 790, "사전 활성 블록 = [첫 act · 가지 · 덧셈]")],
          "(c) 같은 망을 경계만 옮겨 읽으면 사전 활성 블록이 된다 (식 9)", S_PRE)
b += txt(20, 462, "빨간 테 = 옮긴 act. 망 맨 앞(conv1 뒤)과 맨 끝(마지막 덧셈 뒤)에는 act 가 하나씩 따로 남는다 (부록)", 11, anchor="start", fill=MUTED)
svg("fig11_asymmetric", W, H + 6, b, "비대칭 출력 활성과 사전 활성")


# ── 그림 12. 표 3 — 원래 대 사전 활성 ─────────────────────────────────────────
T3 = [("CIFAR-10", "ResNet-110 (한 층 지름길)", 9.90, 8.91, None), ("CIFAR-10", "ResNet-110", 6.61, 6.37, None),
      ("CIFAR-10", "ResNet-164", 5.93, 5.46, None), ("CIFAR-10", "ResNet-1001", 7.61, 4.92, (4.89, 0.14)),
      ("CIFAR-100", "ResNet-164", 25.16, 24.33, None), ("CIFAR-100", "ResNet-1001", 27.82, 22.71, (22.68, 0.22))]
W, H = 820, 420
b = defs()
b += txt(20, 30, "표 3 — 원래 블록에서 사전 활성 블록으로 바꾼 차이 (백분율 점, 다섯 번의 중앙값끼리)", 13.5, anchor="start", weight="bold")
PX0, PX1 = 330, 740
X = lambda v: PX0 + v / 7.0 * (PX1 - PX0)
for v in range(0, 8):
    b += line(X(v), 60, X(v), 330, LINE, 0.8)
    b += txt(X(v), 346, "%d" % v, 9.5, fill=MUTED)
for i, (ds, net, a, p, sd) in enumerate(T3):
    y = 66 + i * 44
    b += txt(40, y + 14, ds, 11, anchor="start", fill=MUTED)
    b += txt(120, y + 14, net, 12, anchor="start")
    b += txt(120, y + 32, "%.2f -> %.2f" % (a, p), 10.5, anchor="start", fill=INK2)
    d = a - p
    b += box(PX0, y + 6, X(d) - PX0, 20, fill=S_PRE, stroke=S_PRE, rx=2)
    b += txt(X(d) + 6, y + 21, "%.2f" % d, 11, anchor="start", weight="bold")
    if sd:
        b += txt(X(d) + 46, y + 21, "(평균 %.2f ± %.2f)" % sd, 10, anchor="start", fill=MUTED)
b += txt((PX0 + PX1) / 2, 364, "원래 - 사전 활성 (양수면 사전 활성이 낮다)", 10.5, fill=MUTED)
b += txt(20, 392, "여섯 행 모두 양수다. 흩어짐이 적힌 것은 사전 활성 1001 층 둘뿐이고, 원래 블록 쪽 흩어짐은 어느 행에도 없다", 10.5, anchor="start", fill=MUTED)
b += txt(20, 410, "가장 작은 차이 0.24 (ResNet-110) 는 원 ResNet 논문이 적은 ResNet-110 다섯 번의 표준편차 0.16 과 같은 크기 대다 — 빌린 수라 판정하지 않는다", 10.5, anchor="start", fill=MUTED)
svg("fig12_table3", W, H + 6, b, "표 3 원래 대 사전 활성")


# ── 그림 13. 논문 그림 6 ────────────────────────────────────────────────────
W, H = 820, 400
b = defs()
b += txt(20, 30, "논문 그림 6 (벡터 선에서 꺼낸 값) — 왼쪽: 덧셈 뒤 BN (ResNet-110), 오른쪽: 사전 활성 (ResNet-164)", 13.5, anchor="start", weight="bold")
b = curve_panel(b, 70, 70, 300, 230, [("r110_base", S_ORIG), ("r110_bnafter", S_VAR)], "ResNet-110: 원래(파랑) 대 덧셈 뒤 BN(초록)",
                notes=[("1만 손실 %.3f / %.3f" % (val("r110_base_loss", 10000), val("r110_bnafter_loss", 10000)), INK2),
                       ("끝 오차 %.2f / %.2f" % (last("r110_base_err"), last("r110_bnafter_err")), INK2)])
b = curve_panel(b, 460, 70, 300, 230, [("r164_orig", S_ORIG), ("r164_pre", S_PRE)], "ResNet-164: 원래(파랑) 대 사전 활성(주황)",
                notes=[("60k 뒤 손실 기하평균 %.4f / %.4f" % (gmean("r164_orig_loss"), gmean("r164_pre_loss")), INK2),
                       ("끝 오차 %.2f / %.2f" % (last("r164_orig_err"), last("r164_pre_err")), INK2)])
b += txt(410, 340, "왼쪽: 1 만 반복의 손실이 덧셈 뒤 BN 쪽 %.2f 배 (본문 '처음에 손실을 줄이기 어렵다')" % (val("r110_bnafter_loss", 10000) / val("r110_base_loss", 10000)), 11, fill=MUTED)
b += txt(410, 360, "오른쪽: 끝 무렵 사전 활성의 손실이 더 높고 시험 오차는 더 낮다 — 논문이 정칙화로 읽는 자리", 11, fill=MUTED)
b += txt(410, 380, "본문은 그림 6 을 'Fib. 6' 으로 한 번 잘못 적었다. 판 안의 수 = 파랑 / 다른 색", 10.5, fill=MUTED)
svg("fig13_figure6_curves", W, H + 4, b, "그림 6 곡선")


# ── 그림 14. ImageNet (표 5) ───────────────────────────────────────────────
T5 = [("ResNet-152 원래", "scale", "224", 23.0, 6.7, S_ORIG), ("ResNet-152 원래", "scale", "320", 21.3, 5.5, S_ORIG),
      ("ResNet-152 사전 활성", "scale", "320", 21.1, 5.5, S_PRE), ("ResNet-200 원래", "scale", "320", 21.8, 6.0, S_ORIG),
      ("ResNet-200 사전 활성", "scale", "320", 20.7, 5.3, S_PRE), ("ResNet-200 사전 활성 †", "scale+asp", "320", 20.1, 4.8, S_PRE),
      ("Inception v3", "scale+asp", "299", 21.2, 5.6, MUTED)]
W, H = 820, 430
b = defs()
b += txt(20, 30, "표 5 — ImageNet 검증 집합 한 조각 top-1 / top-5 오차 (%). 학습 조각은 모두 224 (Inception v3 만 299)", 13.5, anchor="start", weight="bold")
PX0, PX1 = 330, 700
X = lambda v: PX0 + (v - 18.0) / 6.0 * (PX1 - PX0)
for v in range(18, 25):
    b += line(X(v), 58, X(v), 344, LINE, 0.8)
    b += txt(X(v), 360, "%d" % v, 9.5, fill=MUTED)
for i, (t, aug, crop, e1, e5, col) in enumerate(T5):
    y = 62 + i * 40
    b += txt(40, y + 15, t, 12, anchor="start")
    b += txt(220, y + 15, "%s · 시험 %s" % (aug, crop), 10, anchor="start", fill=MUTED)
    b += box(PX0, y + 2, X(e1) - PX0, 20, fill=col, stroke=col, rx=2)
    b += txt(X(e1) + 6, y + 17, "%.1f / %.1f" % (e1, e5), 11, anchor="start", weight="bold")
b += txt((PX0 + PX1) / 2, 378, "top-1 오차 (막대는 18 에서 시작)", 10.5, fill=MUTED)
b += txt(20, 400, "원래 ResNet-200 은 ResNet-152 보다 나쁘고(21.8 대 21.3) 학습 오차는 더 낮았다고 적는다(수치 없음) — 과적합으로 읽는다", 10.5, anchor="start", fill=MUTED)
b += txt(20, 418, "† 는 다른 구현(fb.resnet.torch)의 공개 모델이고 늘리기도 다르다. 같은 칸의 비교는 위 다섯 행(scale · 320)이다", 10.5, anchor="start", fill=MUTED)
svg("fig14_imagenet", W, H + 4, b, "표 5 ImageNet")


# ── 그림 15. 파라미터 · 곱-덧셈을 세어 맞춰 보기 ─────────────────────────────────
W, H = 820, 430
b = defs()
b += txt(20, 30, "내가 센 파라미터와 곱-덧셈 — 논문의 10.2M 은 BN 을 빼고 셀 때 맞는다", 13.5, anchor="start", weight="bold")
hdr = ["망", "깊이", "블록", "BN 넣고 (사전 활성)", "BN 빼고", "논문", "곱-덧셈"]
xs_ = [40, 160, 215, 270, 440, 560, 640]
for x, h_ in zip(xs_, hdr):
    b += txt(x, 70, h_, 11, anchor="start", fill=INK2, weight="bold")
for i, name in enumerate(["ResNet-110", "ResNet-164", "ResNet-1001", "ResNet-1202"]):
    d, u, Po, Pp, Pn, M, paper, _ = pcount[name]
    y = 100 + i * 32
    match_bn = round(Pp / 1e5) / 10.0 == paper
    match_nb = round(Pn / 1e5) / 10.0 == paper
    cells = [name, "%d" % d, "%d" % u, fmt(Pp), fmt(Pn), "%.1fM" % paper, "%.3f G" % (M / 1e9)]
    for j, (x, c) in enumerate(zip(xs_, cells)):
        col = INK
        if j == 3:
            col = OK if match_bn else NO
        if j == 4:
            col = OK if match_nb else NO
        b += txt(x, y, c, 11.5, anchor="start", fill=col)
b += txt(40, 238, "초록 = 반올림하면 논문 값과 같다, 빨강 = 다르다. 1202 층의 19.4M 은 원 ResNet 논문의 값이고, 내 셈은 기본 블록 · 0 채움 지름길이다", 10.5, anchor="start", fill=MUTED)
b += txt(40, 256, "ResNet-1001 은 BN 을 빼야 10.2M 이고, ResNet-1202 는 BN 을 넣어야 19.4M 이다 — 두 수가 같은 셈법이 아니다 (내 추정)", 10.5, anchor="start", fill=NO)
PX0, PX1, PY0 = 120, 700, 400
X = lambda v: PX0 + v / 3.0 * (PX1 - PX0)
for i, name in enumerate(["ResNet-110", "ResNet-164", "ResNet-1001", "ResNet-1202"]):
    M = pcount[name][5] / 1e9
    y = 284 + i * 28
    col = S_ORIG if name in ("ResNet-110", "ResNet-1202") else S_PRE
    b += txt(PX0 - 8, y + 14, name, 11, anchor="end")
    b += box(PX0, y, X(M) - PX0, 18, fill=col, stroke=col, rx=2)
    b += txt(X(M) + 6, y + 14, "%.3f G  (110 의 %.2f 배)" % (M, M * 1e9 / m110), 10.5, anchor="start")
b += txt(410, 412, "본문 '1001 층은 100 층의 10 배쯤 복잡하다' — 곱-덧셈으로 세면 ResNet-110 의 %.1f 배, ResNet-164 의 %.1f 배"
         % (pcount["ResNet-1001"][5] / m110, pcount["ResNet-1001"][5] / pcount["ResNet-164"][5]), 10.5, fill=MUTED)
svg("fig15_params", W, H + 4, b, "파라미터와 곱-덧셈")


# ── 그림 16. 계보 ────────────────────────────────────────────────────────
W, H = 820, 420
b = defs()
b += txt(20, 30, "계보 — 지름길을 깨끗하게 둔다는 생각이 어디서 와서 어디로 갔나", 15, anchor="start", weight="bold")
nodes = [(40, 80, "Highway (2015-05)", "게이트 지름길, 처음 치우침 음수", INK2),
         (40, 165, "ResNet (2015-12)", "항등 지름길, 덧셈 뒤 ReLU", S_ORIG),
         (40, 250, "Inception-v4 (2016-02)", "잔차를 0.1 ~ 0.3 배로 줄여 더한다", INK2),
         (430, 165, "사전 활성 ResNet (2016-03, 이 논문)", "지름길 · 덧셈 뒤를 둘 다 항등으로", S_PRE),
         (40, 335, "확률 깊이 (2016-03)", "학습 중 블록을 통째로 끈다", INK2),
         (430, 270, "Wide ResNet (2016-05)", "이 블록(CIFAR)을 넓히고 층을 줄인다", S_VAR),
         (430, 360, "PatchCore (2022)", "WRN-50-2 는 원래 블록(덧셈 뒤 ReLU)", MUTED)]
for x, y, t, s_, col in nodes:
    b += box(x, y - 26, 340, 50, fill=NODE, stroke=col, sw=1.6)
    b += txt(x + 170, y - 5, t, 12.5, weight="bold", fill=col)
    b += txt(x + 170, y + 14, s_, 11, fill=INK2)
for y in (80, 165, 250):
    b += path("M380,%d C405,%d 405,165 428,165" % (y, y), INK2, sw=1.2, marker="ai")
b += line(600, 191, 600, 242, INK2, 1.2, marker="ai")
b += path("M380,335 C405,335 405,270 428,270", INK2, sw=1.2, marker="ai")
b += line(600, 296, 600, 332, INK2, 1.2, marker="ai")
b += txt(20, 412, "날짜는 arXiv 첫 판. 확률 깊이 · Inception-v4 는 이 논문과 같은 시기의 편이다(뒤의 것은 이 논문이 '동시 연구' 로 적었다). PatchCore 는 이 논문 뒤다", 10.5, anchor="start", fill=MUTED)
svg("fig16_lineage", W, H, b, "계보")
