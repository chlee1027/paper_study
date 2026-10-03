# -*- coding: utf-8 -*-
"""Wide ResNet 노트(Zagoruyko & Komodakis, BMVC 2016)의 그림 열여섯을 만든다.

색과 글꼴은 앞선 노트들(퍼셉트론부터 ResNet 까지)의 그림과 맞췄다 — 저장소의 노트들이 한 벌로 읽히게
하려는 것이다. 결과 그림의 계열 색은 셋을 고정해 쓴다(가는 망 · 넓은 망 · 드롭아웃).
바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

이 파일이 직접 계산하는 것: CIFAR 용 WRN-n-k 의 파라미터 수와 합성곱 곱-덧셈 수(표 2 · 3 · 4 · 5 의 모든 행),
사전 활성 병목 ResNet-164 · 1001 의 파라미터 · 곱-덧셈, ImageNet 기본 블록 망(WRN-18 · 34, 폭 1.0~3.0)의
파라미터, 병목 망(ResNet-50 · 101 · 152 · 200, WRN-50-2)의 파라미터 · 곱-덧셈 · 단계별 크기.
논문 그림 2 · 3 의 곡선 값은 300~400 dpi 로 눈금을 읽은 값을 상수로 적었다. 그림 4 의 막대 값은 막대 위에
적힌 숫자 그대로다. 계산한 값은 돌릴 때 화면에도 찍는다.
"""
import io, os, math, random


OUT = os.path.dirname(os.path.abspath(__file__))
random.seed(0)

BG        = "#ECEFEC"   # 그림 상자 배경
NODE      = "#F6F7F5"   # 노드 안쪽
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 입력 쪽, 정해져 있는 것
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 학습되는 층
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 지름길(항등)
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"   # 초록 — 된다
NO        = "#C0392B"   # 빨강 — 안 된다
# 결과 그림 계열 색 — 평범한 망 · 잔차 망 · VGG. 이 순서로 고정한다.
S_PLAIN   = "#2A78D6"
S_RES     = "#EB6834"
S_VGG     = "#1BAF7A"
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

# 결과 그림 계열 색 — 가는 망 · 넓은 망 · 드롭아웃. 이 순서로 고정한다(앞 노트의 평범 · 잔차 · VGG 자리를 그대로 쓴다).
S_THIN = S_PLAIN
S_WIDE = S_RES
S_DROP = S_VGG


def axis_y(b, x0, x1, y_of, ticks, label_fmt="%g", size=10):
    for v in ticks:
        b += line(x0, y_of(v), x1, y_of(v), LINE, 1)
        b += txt(x0 - 6, y_of(v) + 4, label_fmt % v, size, anchor="end", fill=MUTED)
    return b


def dot(x, y, col, r=4.5):
    return circ(x, y, r, col, col)


# ── 세는 도구 — 파라미터 수와 곱-덧셈 수 ─────────────────────────────────────
def wrn_cifar(N, k, block=(3, 3), ncls=10):
    """CIFAR 용 WRN (사전 활성). BN 은 합성곱 앞에서 입력 채널마다 γ · β 둘을 센다.
    단계마다 블록 N 개, 폭 16k · 32k · 64k, 출력 32 · 16 · 8. 채널 수가 바뀌는 첫 블록에만 1x1 사영 지름길."""
    P = 3 * 16 * 9
    M = 3 * 16 * 9 * 32 * 32
    cin = 16
    for g, (c, s) in enumerate(((16 * k, 32), (32 * k, 16), (64 * k, 8))):
        for bi in range(N):
            ch = cin
            for ks in block:
                P += 2 * ch + ch * c * ks * ks
                M += ch * c * ks * ks * s * s
                ch = c
            if cin != c:
                P += cin * c
                M += cin * c * s * s
            cin = c
    P += 2 * cin + cin * ncls + ncls
    M += cin * ncls
    return P, M


def depth_of(N, block=(3, 3)):
    """논문의 이름 붙이기 n = 3 · l · N + 4 (합성곱 1 + 블록 안 3lN + 사영 3)."""
    return 3 * len(block) * N + 4


def preact_bottleneck(N, ncls=10):
    """사전 활성 병목 ResNet (CIFAR). 깊이 = 9N + 2. 안쪽 폭 16 · 32 · 64, 출력 4 배."""
    P = 3 * 16 * 9
    M = 3 * 16 * 9 * 32 * 32
    cin = 16
    for c, s in ((16, 32), (32, 16), (64, 8)):
        out = 4 * c
        for bi in range(N):
            P += 2 * cin + cin * c + 2 * c + 9 * c * c + 2 * c + c * out
            M += (cin * c + 9 * c * c + c * out) * s * s
            if cin != out:
                P += cin * out
                M += cin * out * s * s
            cin = out
    P += 2 * cin + cin * ncls + ncls
    M += cin * ncls
    return P, M


def imagenet(blocks, bottleneck, width=1.0, inner=1):
    """ImageNet 224 입력. 기본 블록은 모든 폭에 width 를 곱하고(표 7), 병목은 안쪽 폭에만 inner 를 곱한다(표 8).
    BN 은 채널마다 둘. 보폭 2 는 3x3 에 둔다(torchvision 과 같다)."""
    base = int(64 * width) if not bottleneck else 64
    P = 3 * base * 49 + 2 * base
    M = 3 * base * 49 * 112 * 112
    cin, h = base, 56
    stages = []
    for si, n in enumerate(blocks):
        c = base * 2 ** si
        out = 4 * c if bottleneck else c
        mid = c * inner
        sp = 0
        for bi in range(n):
            ho = h // 2 if (si > 0 and bi == 0) else h
            if bottleneck:
                p = cin * mid + 2 * mid + 9 * mid * mid + 2 * mid + mid * out + 2 * out
                m = cin * mid * h * h + 9 * mid * mid * ho * ho + mid * out * ho * ho
            else:
                p = 9 * cin * c + 2 * c + 9 * c * c + 2 * c
                m = (9 * cin * c + 9 * c * c) * ho * ho
            if cin != out or ho != h:
                p += cin * out + 2 * out
                m += cin * out * ho * ho
            sp += p; M += m
            cin, h = out, ho
        P += sp
        stages.append((mid if bottleneck else c, out, h, n, sp))
    P += cin * 1000 + 1000
    M += cin * 1000
    return P, M, stages


# 표 4 — CIFAR, ZCA 전처리. (깊이, k, 논문 파라미터 M, CIFAR-10, CIFAR-100)
T4 = [(40, 1, 0.6, 6.85, 30.89), (40, 2, 2.2, 5.33, 26.04), (40, 4, 8.9, 4.97, 22.89), (40, 8, 35.7, 4.66, None),
      (28, 10, 36.5, 4.17, 20.50), (28, 12, 52.5, 4.33, 20.43), (22, 8, 17.2, 4.38, 21.22), (22, 10, 26.8, 4.44, 20.75),
      (16, 8, 11.0, 4.81, 22.07), (16, 10, 17.1, 4.56, 21.59)]
print("  [표 4] WRN-n-k 파라미터 (CIFAR-10 / CIFAR-100 머리)")
p4 = {}
for d, k, pp, e10, e100 in T4:
    N = (d - 4) // 6
    P10, M10 = wrn_cifar(N, k)
    P100, _ = wrn_cifar(N, k, ncls=100)
    p4[(d, k)] = (P10, M10)
    print("      WRN-%d-%-2d N=%d  %s / %s  (논문 %.1fM)  곱-덧셈 %.3f G" % (d, k, N, fmt(P10), fmt(P100), pp, M10 / 1e9))

# 표 2 — 블록 종류. 논문의 '깊이' 칸과 내가 맞춘 블록 수 N
T2 = [("B(1,3,1)", (1, 3, 1), 40, 1.4, 85.8, 6.06), ("B(3,1)", (3, 1), 40, 1.2, 67.5, 5.78),
      ("B(1,3)", (1, 3), 40, 1.3, 72.2, 6.42), ("B(3,1,1)", (3, 1, 1), 40, 1.3, 82.2, 5.86),
      ("B(3,3)", (3, 3), 28, 1.5, 67.5, 5.73), ("B(3,1,3)", (3, 1, 3), 22, 1.1, 59.9, 5.78)]
print("  [표 2] 블록 종류 — 깊이 칸을 '합성곱 수'로 읽을 때와 'B(3,3) 와 같은 N'으로 읽을 때")
t2 = []
for name, blk, d, pp, tm, err in T2:
    l = len(blk)
    N_conv = (d - 4) / (3.0 * l)
    N_same = (d - 4) // 6
    Pa = wrn_cifar(int(round(N_conv)), 2, blk)[0] if abs(N_conv - round(N_conv)) < 1e-9 else None
    Pb = wrn_cifar(N_same, 2, blk)[0]
    t2.append((name, blk, d, pp, tm, err, N_conv, Pa, N_same, Pb))
    print("      %-9s 깊이 %d  합성곱 수로 읽으면 N=%s 파라미터 %s | N=%d 로 읽으면 %s (실제 합성곱 %d) | 논문 %.1fM"
          % (name, d, ("%g" % N_conv), fmt(Pa) if Pa else "-", N_same, fmt(Pb), depth_of(N_same, blk), pp))

# 표 3 — 블록 안 합성곱 수 l, WRN-40-2
T3 = [(1, 6.69), (2, 5.43), (3, 5.65), (4, 5.93)]
print("  [표 3] WRN-40-2, l = 1..4")
t3 = []
for l, err in T3:
    N = 36 // (3 * l)
    P, _ = wrn_cifar(N, 2, (3,) * l)
    t3.append((l, N, P, err))
    print("      l=%d N=%d 파라미터 %s 지름길 %d 개" % (l, N, fmt(P), 3 * N))

# 표 5 — 가는 망
R164 = preact_bottleneck(18)
R1001 = preact_bottleneck(111)
print("  [표 5] 사전 활성 병목 ResNet-164 %s (논문 1.7M) 곱-덧셈 %.3f G / ResNet-1001 %s (논문 10.2M) 곱-덧셈 %.3f G"
      % (fmt(R164[0]), R164[1] / 1e9, fmt(R1001[0]), R1001[1] / 1e9))
P4010, _ = wrn_cifar(6, 10)
print("      WRN-40-10 %s (본문 56M)  WRN-16-4 %s  WRN-52-1 %s" % (fmt(P4010), fmt(wrn_cifar(2, 4)[0]), fmt(wrn_cifar(8, 1)[0])))
print("      배수: 28-10 / 1001 = %.2f, 40-10 / 1001 = %.2f (본문 3.6 과 5)" % (p4[(28, 10)][0] / R1001[0], P4010 / R1001[0]))

# 표 7 · 8 — ImageNet
T7 = {18: [(1.0, 30.4, 10.93, 11.7), (1.5, 27.06, 9.0, 25.9), (2.0, 25.58, 8.06, 45.6), (3.0, 24.06, 7.33, 101.8)],
      34: [(1.0, 26.77, 8.67, 21.8), (1.5, 24.5, 7.58, 48.6), (2.0, 23.39, 7.00, 86.0)]}
print("  [표 7] 기본 블록 ImageNet 망")
t7 = {}
for d, rows in T7.items():
    bl = [2, 2, 2, 2] if d == 18 else [3, 4, 6, 3]
    t7[d] = []
    for w, e1, e5, pp in rows:
        P, M, _ = imagenet(bl, False, width=w)
        t7[d].append((w, e1, e5, pp, P, M))
        print("      WRN-%d 폭 %.1f  %s (논문 %.1fM, 차 %+.2fM)  곱-덧셈 %.2f G" % (d, w, fmt(P), pp, P / 1e6 - pp, M / 1e9))
T8 = [("ResNet-50", [3, 4, 6, 3], 1, 24.01, 7.02, 25.6, 49), ("ResNet-101", [3, 4, 23, 3], 1, 22.44, 6.21, 44.5, 82),
      ("ResNet-152", [3, 8, 36, 3], 1, 22.16, 6.16, 60.2, 115), ("WRN-50-2", [3, 4, 6, 3], 2, 21.9, 6.03, 68.9, 93),
      ("pre-ResNet-200", [3, 24, 36, 3], 1, 21.66, 5.79, 64.7, 154)]
print("  [표 8] 병목 ImageNet 망")
t8 = []
for name, bl, inner, e1, e5, pp, tm in T8:
    P, M, st = imagenet(bl, True, inner=inner)
    t8.append((name, e1, e5, pp, tm, P, M, st))
    print("      %-15s %s (논문 %.1fM)  곱-덧셈 %.2f G  시간 %d ms" % (name, fmt(P), pp, M / 1e9, tm))
R50 = t8[0]
W50 = t8[3]
print("  [단계] ResNet-50 대 WRN-50-2 (안쪽 폭, 출력 채널, 224 입력의 출력 크기, 블록, 파라미터)")
for a, c in zip(R50[7], W50[7]):
    print("      안쪽 %4d 대 %4d  출력 %4d  %2dx%-2d  블록 %d  %s 대 %s (%.2f 배)" % (a[0], c[0], a[1], a[2], a[2], a[3], fmt(a[4]), fmt(c[4]), c[4] / a[4]))


# ── 그림 1. 논문 그림 1 의 네 블록 ───────────────────────────────────────────
W, H = 820, 470
b = defs()
b += txt(20, 30, "블록 넷 (논문 그림 1) — 합성곱마다 앞에 BN · ReLU 가 붙는다(사전 활성). 넓은 블록은 같은 모양에 채널만 k 배", 14, anchor="start", weight="bold")
panels = [("(a) 기본", ["3x3, C", "3x3, C"], 16, "가는 망의 블록 (k = 1)"),
          ("(b) 병목", ["1x1, C", "3x3, C", "1x1, 4C"], 16, "이 논문이 CIFAR 에서 안 쓴다"),
          ("(c) 넓은 기본", ["3x3, kC", "3x3, kC"], 16, "이 논문의 블록 B(3,3)"),
          ("(d) 넓은 + 드롭아웃", ["3x3, kC", "드롭아웃", "3x3, kC"], 16, "합성곱 사이에 드롭아웃")]
for i, (title, layers, _, note) in enumerate(panels):
    x0 = 25 + 198 * i
    b += box(x0, 50, 185, 360, fill="none", stroke=LINE)
    b += txt(x0 + 92, 74, title, 13, weight="bold")
    trunk = x0 + 35
    b += line(trunk, 92, trunk, 352, CODE, 5)
    b += txt(trunk, 88, "x_l", 12, fill=INK2)
    n = len(layers)
    top = 120
    step = 200.0 / n
    b += path("M%d,100 L%d,100 L%d,%d" % (trunk, x0 + 120, x0 + 120, top - 4), INK2, sw=1.2, marker="ai")
    for j, lab in enumerate(layers):
        y = top + j * step
        wide = "k" in lab
        isdrop = lab == "드롭아웃"
        bw = 120 if wide else (80 if not isdrop else 110)
        bx = x0 + 120 - bw / 2
        if not isdrop:
            b += txt(x0 + 120, y + 10, "BN · ReLU", 10, fill=MUTED)
            b += box(bx, y + 15, bw, 22, fill=REV_SOFT, stroke=REV)
            b += txt(x0 + 120, y + 31, lab, 11)
        else:
            b += box(bx, y + 8, bw, 22, fill="#F6D5D2", stroke=NO)
            b += txt(x0 + 120, y + 24, lab, 11, fill=NO)
        if j < n - 1:
            b += line(x0 + 120, y + (37 if not isdrop else 30), x0 + 120, top + (j + 1) * step + (2 if layers[j + 1] != "드롭아웃" else 6), INK2, 1.1, marker="ai")
    b += path("M%d,%d L%d,330 L%d,330" % (x0 + 120, top + (n - 1) * step + 37, x0 + 120, trunk + 12), INK2, sw=1.2, marker="ai")
    b += circ(trunk, 330, 10, NODE, INK)
    b += txt(trunk, 335, "+", 15, weight="bold")
    b += txt(trunk, 372, "x_l+1", 12, fill=INK2)
    b += txt(x0 + 92, 398, note, 11, fill=INK2)
b += txt(410, 432, "덧셈 기호는 논문 그림에서 원 안의 곱셈 기호(⊗)로 그려져 있다. 식 (1) 과 본문은 덧셈이라 여기서는 + 로 그렸다", 11, fill=MUTED)
b += txt(410, 452, "C 는 단계의 기본 채널 수(16 · 32 · 64). 노랑 굵은 줄 = 항등 지름길", 11, fill=MUTED)
svg("fig01_blocks", W, H, b, "논문 그림 1 의 네 가지 잔차 블록")


# ── 그림 2. 망의 모양 (표 1) 과 이름 붙이기 ──────────────────────────────────
W, H = 820, 420
b = defs()
b += txt(20, 30, "WRN-n-k 의 모양 (표 1) — 단계 셋, 단계마다 블록 N 개, 폭은 16k · 32k · 64k", 15, anchor="start", weight="bold")
stg = [("conv1", "32x32", "3x3, 16", "1 층", FWD_SOFT, FWD),
       ("conv2", "32x32", "[3x3, 16k] x2", "x N", REV_SOFT, REV),
       ("conv3", "16x16", "[3x3, 32k] x2", "x N", REV_SOFT, REV),
       ("conv4", "8x8", "[3x3, 64k] x2", "x N", REV_SOFT, REV),
       ("평균 풀링 · fc", "1x1", "[8x8] → 부류", "", NODE, INK2)]
for i, (nm, sz, ly, rep, f, s) in enumerate(stg):
    x = 25 + 157 * i
    hgt = 70 if i in (0, 4) else 70 + 0
    b += box(x, 60, 140, 110, fill=f, stroke=s, sw=1.4)
    b += txt(x + 70, 84, nm, 13, weight="bold", fill=s)
    b += txt(x + 70, 108, ly, 12)
    b += txt(x + 70, 130, "출력 " + sz, 11, fill=INK2)
    b += txt(x + 70, 154, rep, 12, weight="bold", fill=s)
    if i < 4:
        b += line(x + 140, 115, x + 155, 115, INK2, 1.2, marker="ai")
b += txt(25, 205, "이름 붙이기 — n 은 합성곱 층 수다 (논문 2.3절). 블록이 B(3,3) 일 때:", 13, anchor="start", weight="bold")
b += txt(45, 232, "n = 1 (conv1)  +  3 단계 x N 블록 x 2 층  +  3 (단계 첫 블록의 1x1 사영 지름길)  =  6N + 4", 13, anchor="start")
ex = [(16, 2), (22, 3), (28, 4), (40, 6)]
for i, (d, N) in enumerate(ex):
    x = 45 + 190 * i
    b += box(x, 250, 175, 54, fill=NODE, stroke=LINE)
    b += txt(x + 87, 272, "WRN-%d-k" % d, 13, weight="bold")
    b += txt(x + 87, 293, "N = %d  (6 x %d + 4 = %d)" % (N, N, d), 11, fill=INK2)
b += txt(25, 336, "작은 예시 — WRN-28-10: N = 4, 폭 160 · 320 · 640, 이 파일이 센 파라미터 %s (논문 36.5M)" % fmt(p4[(28, 10)][0]), 12, anchor="start")
b += txt(25, 360, "주의 하나. k = 1 이면 conv2 첫 블록에 사영이 필요 없어 실제 합성곱은 6N + 3 이다(WRN-40-1 은 39 층). 이름은 그대로 40 이다", 11, anchor="start", fill=NO)
b += txt(25, 382, "주의 둘. 표 5 의 가는 망 ResNet-164 · 1001 은 다른 규칙(9N + 2, fc 를 세고 사영은 안 센다)으로 이름이 붙어 있다", 11, anchor="start", fill=NO)
b += txt(25, 404, "드롭아웃 위치 · BN 순서는 그림 1. 이 그림의 값은 논문 표 1 을 그대로 옮기고 n 의 셈만 내가 풀어 적었다", 11, anchor="start", fill=MUTED)
svg("fig02_structure", W, H, b, "WRN-n-k 의 구조와 이름 붙이기")


# ── 그림 3. 파라미터는 k 의 제곱 · 깊이의 1 차 ──────────────────────────────
W, H = 820, 440
b = defs()
b += txt(20, 30, "파라미터는 폭 k 의 제곱으로, 깊이에는 1 차로 늘어난다 — 선은 이 파일이 센 값, 점은 표 4 의 값", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 80, 530, 380, 60
def X(k):
    return PX0 + (k - 1) / 11.0 * (PX1 - PX0)
def Y(v):
    return PY0 - v / 60.0 * (PY0 - PY1)
b = axis_y(b, PX0, PX1, Y, (0, 10, 20, 30, 40, 50, 60), "%gM")
for k in (1, 2, 4, 6, 8, 10, 12):
    b += txt(X(k), PY0 + 18, "k=%d" % k, 10, fill=MUTED)
cols = {16: "#8BB8E8", 22: "#5A92D6", 28: "#E59866", 40: "#B4552B"}
for d in (16, 22, 28, 40):
    N = (d - 4) // 6
    pts = []
    for k10 in range(10, (101 if d == 40 else 121), 2):
        k = k10 / 10.0
        pts.append((X(k), Y(wrn_cifar(N, k)[0] / 1e6)))
    b += polyline(pts, cols[d], 2.2)
    b += txt(X(12) + 6, Y(wrn_cifar(N, 12)[0] / 1e6) + 4, "깊이 %d" % d, 11, anchor="start", fill=cols[d], weight="bold") if d != 40 else txt(X(10) + 8, Y(wrn_cifar(6, 10)[0] / 1e6) + 4, "깊이 40", 11, anchor="start", fill=cols[d], weight="bold")
for d, k, pp, e10, e100 in T4:
    b += circ(X(k), Y(pp), 5, "none", INK, 1.6)
b += line(PX0, Y(10.2), PX1, Y(10.2), S_THIN, 1.4, dash="5,4")
b += txt(PX0 + 6, Y(10.2) - 6, "가는 ResNet-1001 (10.2M)", 11, anchor="start", fill=S_THIN, weight="bold")
b += box(615, 60, 190, 320, fill=NODE, stroke=LINE)
lines_ = ["블록 하나의 3x3 두 층:", " 2 x 9 x (16k)² = 4,608 k²", "k = 1 →  4,608", "k = 10 → 460,800 (100 배)", "",
          "깊이를 두 배로 하면", "블록 수 N 이 두 배 → 2 배", "폭을 두 배로 하면 → 4 배", "", "곱-덧셈도 같은 모양이다",
          "(합성곱 계산 = 파라미터 x", " 출력 칸 수)"]
for j, l in enumerate(lines_):
    b += txt(625, 86 + 22 * j, l, 12 if j not in (0, 5, 9) else 12, anchor="start", fill=INK if j in (0, 5, 9) else INK2,
             weight="bold" if j in (0, 5, 9) else None)
b += txt(410, 420, "점(속 빈 원) 열 개가 모두 선 위에 놓인다 — 표 4 의 파라미터 칸 열 행을 모두 소수 첫째 자리까지 맞게 셌다", 11, fill=MUTED)
svg("fig03_params_quadratic", W, H, b, "폭과 깊이에 따른 파라미터 수")


# ── 그림 4. 블록 종류 (표 2) ─────────────────────────────────────────────
W, H = 820, 470
b = defs()
b += txt(20, 30, "블록 종류 여섯 (표 2, CIFAR-10, k = 2, 다섯 번의 중앙값) — 차이는 0.69 백분율 점 안", 15, anchor="start", weight="bold")
LX0, LX1 = 200, 440
def EX(v):
    return LX0 + (v - 5.5) / 1.0 * (LX1 - LX0)
TX0, TX1 = 470, 640
def TX(v):
    return TX0 + v / 90.0 * (TX1 - TX0)
b += txt((LX0 + LX1) / 2, 62, "시험 오차 % (축이 5.5 에서 시작)", 12, weight="bold")
b += txt((TX0 + TX1) / 2, 62, "한 바퀴 학습 시간, 초", 12, weight="bold")
b += txt(730, 62, "파라미터 (논문 / 셈)", 12, weight="bold")
for v in (5.5, 5.75, 6.0, 6.25, 6.5):
    b += line(EX(v), 75, EX(v), 395, LINE, 1)
    b += txt(EX(v), 412, "%g" % v, 10, fill=MUTED)
for v in (0, 30, 60, 90):
    b += line(TX(v), 75, TX(v), 395, LINE, 1)
    b += txt(TX(v), 412, "%d" % v, 10, fill=MUTED)
for i, (name, blk, d, pp, tm, err, Nc, Pa, Ns, Pb) in enumerate(t2):
    y = 92 + 50 * i
    best = name == "B(3,3)"
    b += txt(25, y + 6, name, 13, anchor="start", weight="bold", fill=S_WIDE if best else INK)
    b += txt(25, y + 24, "깊이 칸 %d · N=%d" % (d, Ns), 10, anchor="start", fill=MUTED)
    b += '<rect x="%s" y="%s" width="%s" height="22" rx="3" fill="%s"/>' % (LX0, y - 6, EX(err) - LX0, S_WIDE if best else S_THIN)
    b += txt(EX(err) + 6, y + 9, "%.2f" % err, 11, anchor="start", weight="bold")
    b += '<rect x="%s" y="%s" width="%s" height="22" rx="3" fill="%s"/>' % (TX0, y - 6, TX(tm) - TX0, MUTED)
    b += txt(TX(tm) + 6, y + 9, "%.1f" % tm, 11, anchor="start")
    b += txt(730, y + 9, "%.1fM / %.2fM" % (pp, Pb / 1e6), 11, fill=INK2)
b += txt(410, 436, "파라미터 셈: 논문의 '깊이' 칸을 합성곱 수로 읽으면 B(1,3,1) · B(3,1,1) · B(3,1,3) 셋이 안 맞고(0.95 · 0.87 · 0.74M),", 11, fill=NO)
b += txt(410, 456, "'B(3,3) 와 같은 블록 수 N = (깊이 − 4) / 6' 으로 읽으면 여섯이 모두 맞는다 — 오른쪽 칸은 그렇게 센 값이다(내 셈)", 11, fill=NO)
svg("fig04_block_types", W, H, b, "블록 종류별 오차와 시간")


# ── 그림 5. 블록 안 합성곱 수 l (표 3) ───────────────────────────────────────
W, H = 820, 400
b = defs()
b += txt(20, 30, "블록 안 합성곱 수 l (표 3, WRN-40-2, 파라미터 2.2M 로 같게) — 둘이 가장 낫다", 15, anchor="start", weight="bold")
for i, (l, N, P, err) in enumerate(t3):
    x0 = 25 + 197 * i
    b += box(x0, 50, 185, 210, fill="none", stroke=LINE)
    b += txt(x0 + 92, 74, "l = %d   B(%s)" % (l, ",".join(["3"] * l)), 13, weight="bold", fill=S_WIDE if l == 2 else INK)
    for j in range(l):
        b += box(x0 + 60, 90 + 26 * j, 90, 20, fill=REV_SOFT, stroke=REV)
        b += txt(x0 + 105, 104 + 26 * j, "3x3", 10)
    b += line(x0 + 40, 86, x0 + 40, 90 + 26 * l, CODE, 4)
    b += txt(x0 + 92, 210, "단계마다 블록 N = %d" % N, 12)
    b += txt(x0 + 92, 230, "지름길 %d 개 · 파라미터 %s" % (3 * N, fmt(P)), 10, fill=INK2)
    b += txt(x0 + 92, 250, "합성곱 3lN = %d" % (3 * l * N), 10, fill=MUTED)
BX0, BX1 = 120, 700
def EX(v):
    return BX0 + (v - 5.0) / 2.0 * (BX1 - BX0)
for v in (5.0, 5.5, 6.0, 6.5, 7.0):
    b += line(EX(v), 275, EX(v), 345, LINE, 1)
    b += txt(EX(v), 360, "%g" % v, 10, fill=MUTED)
for i, (l, N, P, err) in enumerate(t3):
    y = 280 + 16 * i
    b += txt(BX0 - 10, y + 11, "l=%d" % l, 11, anchor="end")
    b += '<rect x="%s" y="%s" width="%s" height="12" rx="2" fill="%s"/>' % (BX0, y + 1, EX(err) - BX0, S_WIDE if l == 2 else S_THIN)
    b += txt(EX(err) + 6, y + 11, "%.2f" % err, 11, anchor="start", weight="bold")
b += txt(410, 382, "시험 오차 % (CIFAR-10, 축이 5.0 에서 시작). 같은 WRN-40-2 가 표 4 에서는 5.33 이다 — 0.10 차이의 까닭은 본문에 없다", 11, fill=MUTED)
svg("fig05_deepening", W, H, b, "블록 안 합성곱 수에 따른 오차")


# ── 그림 6. 깊이 x 폭 격자 (표 4) ─────────────────────────────────────────
W, H = 820, 420
b = defs()
b += txt(20, 30, "깊이 x 폭 격자 (표 4, ZCA 전처리) — 칸의 위 숫자가 시험 오차 %, 아래가 파라미터", 15, anchor="start", weight="bold")
ks = [1, 2, 4, 8, 10, 12]
ds = [40, 28, 22, 16]
T4d = {(d, k): (pp, e10, e100) for d, k, pp, e10, e100 in T4}
def shade(v, lo, hi):
    t = max(0.0, min(1.0, (v - lo) / (hi - lo)))
    r = int(235 - t * (235 - 180)); g = int(242 - t * (242 - 85)); bl = int(250 - t * (250 - 43))
    return "#%02X%02X%02X" % (r, g, bl)
for pi, (title, idx, lo, hi) in enumerate([("CIFAR-10", 1, 4.0, 7.0), ("CIFAR-100", 2, 19.0, 31.0)]):
    x0 = 30 + 395 * pi
    b += txt(x0 + 185, 62, title, 13, weight="bold")
    for j, k in enumerate(ks):
        b += txt(x0 + 75 + 52 * j, 84, "k=%d" % k, 11, fill=MUTED)
    for i, d in enumerate(ds):
        b += txt(x0 + 30, 122 + 62 * i, "깊이 %d" % d, 11, fill=MUTED)
        for j, k in enumerate(ks):
            cx = x0 + 52 + 52 * j
            cy = 94 + 62 * i
            v = T4d.get((d, k))
            if v is None or v[idx] is None:
                b += box(cx, cy, 48, 56, fill=BG, stroke=LINE, rx=3, dash="3,3")
                b += txt(cx + 24, cy + 32, "-", 12, fill=MUTED)
                continue
            b += box(cx, cy, 48, 56, fill=shade(v[idx], lo, hi), stroke=LINE, rx=3)
            b += txt(cx + 24, cy + 26, "%.2f" % v[idx], 12, weight="bold")
            b += txt(cx + 24, cy + 44, "%.1fM" % v[0], 9, fill=INK2)
    # 폭을 늘렸는데 나빠진 칸
    if pi == 0:
        for (d, k) in ((22, 10), (28, 12)):
            i = ds.index(d); j = ks.index(k)
            b += box(x0 + 52 + 52 * j - 2, 94 + 62 * i - 2, 52, 60, fill="none", stroke=NO, sw=2.2, rx=4)
b += txt(30, 360, "빨간 테두리 둘 — 같은 깊이에서 폭을 늘렸는데 CIFAR-10 오차가 올랐다: 22-8 → 22-10 은 4.38 → 4.44, 28-10 → 28-12 는 4.17 → 4.33.", 11, anchor="start", fill=NO)
b += txt(30, 380, "본문은 '40 · 22 · 16 층 모두 폭을 늘리면 꾸준히 낫다'고 적는다. CIFAR-100 에서는 두 자리 모두 내려갔다(21.22 → 20.75, 20.50 → 20.43).", 11, anchor="start", fill=NO)
b += txt(30, 400, "점선 칸은 표에 없는 조합이다. 표 4 의 행에는 몇 번 돌린 값인지 적혀 있지 않다(표 2 · 3 · 5 · 6 은 다섯 번의 중앙값이라고 적는다).", 11, anchor="start", fill=MUTED)
svg("fig06_depth_width_grid", W, H, b, "깊이와 폭 격자의 오차")


# ── 그림 7. 파라미터 대 오차 — 가는 망과 넓은 망 (표 5) ─────────────────────────
T5 = [("ResNet-110", 1.7, 6.43, 25.16, "orig"), ("ResNet-1202", 10.2, 7.93, 27.82, "orig"),
      ("확률 깊이-110", 1.7, 5.23, 24.58, "sd"), ("확률 깊이-1202", 10.2, 4.91, None, "sd"),
      ("사전 활성-164", 1.7, 5.46, 24.33, "pre"), ("사전 활성-1001", 10.2, 4.92, 22.71, "pre"),
      ("WRN-40-4", 8.9, 4.53, 21.18, "wrn"), ("WRN-16-8", 11.0, 4.27, 20.43, "wrn"), ("WRN-28-10", 36.5, 4.00, 19.25, "wrn")]
W, H = 820, 440
b = defs()
b += txt(20, 30, "파라미터 대 시험 오차 (표 5, 평균/표준편차 전처리, 드롭아웃 없음) — 가로축은 로그", 15, anchor="start", weight="bold")
for pi, (title, idx, lo, hi, ticks) in enumerate([("CIFAR-10", 2, 3.5, 8.5, (4, 5, 6, 7, 8)), ("CIFAR-100", 3, 18, 29, (18, 20, 22, 24, 26, 28))]):
    x0 = 70 + 395 * pi
    PX0_, PX1_, PY0_, PY1_ = x0, x0 + 320, 360, 70
    def X(v):
        return PX0_ + (math.log10(v) - math.log10(1.0)) / (math.log10(50) - math.log10(1.0)) * (PX1_ - PX0_)
    def Y(v):
        return PY0_ - (v - lo) / (hi - lo) * (PY0_ - PY1_)
    b += txt(x0 + 160, 58, title, 13, weight="bold")
    b = axis_y(b, PX0_, PX1_, Y, ticks)
    for v in (1, 2, 5, 10, 20, 50):
        b += txt(X(v), PY0_ + 18, "%gM" % v, 10, fill=MUTED)
    for name, pp, e10, e100, fam in T5:
        v = (e10, e100)[idx - 2]
        if v is None:
            continue
        col = {"orig": "#8BB8E8", "sd": "#5A92D6", "pre": S_THIN, "wrn": S_WIDE}[fam]
        b += dot(X(pp), Y(v), col, 5)
        off = {"ResNet-1202": (8, 4), "사전 활성-1001": (8, 14), "확률 깊이-1202": (8, -6), "WRN-40-4": (-8, -8),
               "WRN-16-8": (8, -8), "ResNet-110": (8, 4), "확률 깊이-110": (8, 4), "사전 활성-164": (8, 4), "WRN-28-10": (-8, -10)}[name]
        if idx == 3:
            off = {"ResNet-110": (8, -12), "확률 깊이-110": (8, 2), "사전 활성-164": (8, 16)}.get(name, off)
        b += txt(X(pp) + off[0], Y(v) + off[1], name, 10, anchor="start" if off[0] > 0 else "end", fill=col)
b += txt(410, 400, "같은 10M 근방에서 WRN-40-4(8.9M) 4.53 대 사전 활성 ResNet-1001(10.2M) 4.92 — 층 수는 40 대 1001", 11, fill=INK2)
b += txt(410, 420, "ResNet-1001 은 배치 64 로 돌리면 4.64 다(표 5 괄호). 넓은 망 셋은 다섯 번의 중앙값, 나머지는 각 원 논문의 값", 11, fill=MUTED)
svg("fig07_params_vs_error", W, H, b, "파라미터 대 시험 오차, 가는 망과 넓은 망")


# ── 그림 8. 학습 곡선 (논문 그림 2) 다시 그리기 ────────────────────────────────
# 300 · 400 dpi 로 눈금을 읽은 값. CIFAR-10 읽기 ±0.5, CIFAR-100 읽기 ±1. 첫 60 바퀴의 들쭉날쭉은 가운데를 지나는 선으로 줄였다.
C10 = {"thin_test": [(0, 20), (10, 18), (30, 17), (58, 16), (60, 8.6), (65, 8.6), (75, 9.5), (90, 10.5), (100, 10), (110, 9.6), (119, 10), (120, 5.9), (130, 5.8), (150, 6.1), (158, 5.8), (165, 5.4), (200, 5.2)],
       "wide_test": [(0, 19), (10, 16), (30, 14.5), (58, 13.5), (60, 5.7), (65, 6.0), (75, 7.5), (85, 7.8), (95, 8.2), (100, 7.6), (110, 7.8), (119, 7.2), (120, 4.6), (130, 4.3), (150, 4.2), (200, 4.0)],
       "thin_train": [(5, 20), (20, 16.5), (40, 14), (58, 13), (60, 5.6), (70, 5.3), (100, 5.1), (119, 4.8), (121, 1.2), (130, 0.6), (158, 0.4), (162, 0.05), (200, 0)],
       "wide_train": [(3, 19), (10, 13), (20, 10), (40, 8.8), (58, 8.5), (60, 2.5), (65, 1.4), (75, 2.0), (100, 2.0), (119, 1.8), (121, 0.2), (200, 0)]}
C100 = {"thin_test": [(0, 50), (20, 46), (40, 43), (58, 41), (60, 27.5), (70, 29.5), (90, 31), (110, 31), (119, 32), (120, 23.5), (150, 24), (160, 23.2), (200, 23.3)],
        "wide_test": [(0, 48), (20, 40), (40, 38), (58, 36), (60, 22), (70, 24), (90, 27.5), (105, 29), (110, 30), (119, 27.5), (120, 20.5), (140, 19.5), (200, 19.0)],
        "thin_train": [(10, 48), (20, 41), (40, 36), (58, 35), (60, 21), (65, 17), (80, 16), (119, 13), (121, 2), (140, 1), (160, 0.3), (200, 0)],
        "wide_train": [(5, 45), (10, 37), (20, 30), (40, 25), (58, 23), (60, 8), (65, 3), (70, 2.8), (80, 4.5), (100, 4), (119, 3.5), (121, 0.4), (200, 0)]}
W, H = 820, 440
b = defs()
b += txt(20, 30, "학습 곡선 (논문 그림 2 를 눈금으로 읽어 다시 그림) — 실선 시험 오차, 점선 학습 쪽 곡선, 회색 세로선 = 학습률 x 0.2", 14, anchor="start", weight="bold")
for pi, (title, data, ymax, fin) in enumerate([("CIFAR-10", C10, 20, ("5.46", "4.00")), ("CIFAR-100", C100, 50, ("24.33", "19.25"))]):
    x0 = 60 + 395 * pi
    PX0_, PX1_, PY0_, PY1_ = x0, x0 + 330, 360, 70
    def X(e):
        return PX0_ + e / 200.0 * (PX1_ - PX0_)
    def Y(v):
        return PY0_ - v / float(ymax) * (PY0_ - PY1_)
    b += txt(x0 + 165, 58, title, 13, weight="bold")
    b = axis_y(b, PX0_, PX1_, Y, range(0, ymax + 1, 5 if ymax == 20 else 10))
    for e in (0, 50, 100, 150, 200):
        b += txt(X(e), PY0_ + 18, "%d" % e, 10, fill=MUTED)
    for e in (60, 120, 160):
        b += line(X(e), PY1_, X(e), PY0_, MUTED, 1, dash="2,3")
    b += '<rect x="%s" y="%s" width="%s" height="%s" fill="%s" opacity="0.35"/>' % (X(60), PY1_, X(120) - X(60), PY0_ - PY1_, "#F6D5D2")
    for key, col, dash in (("thin_test", S_THIN, None), ("wide_test", S_WIDE, None), ("thin_train", S_THIN, "6,4"), ("wide_train", S_WIDE, "6,4")):
        b += polyline([(X(e), Y(v)) for e, v in data[key]], col, 2.0 if dash is None else 1.6, dash)
    b += txt(X(90), PY1_ + 16, "60 → 120 바퀴: 시험 오차가 다시 오른다", 10, fill=NO)
    b += txt(PX1_ - 4, PY1_ + 36, "ResNet-164 최종 %s%%" % fin[0], 11, anchor="end", fill=S_THIN, weight="bold")
    b += txt(PX1_ - 4, PY1_ + 54, "WRN-28-10 최종 %s%%" % fin[1], 11, anchor="end", fill=S_WIDE, weight="bold")
    b += txt(x0 + 165, PY0_ + 36, "바퀴 (epoch)", 10, fill=MUTED)
b += txt(410, 418, "점선의 이름이 캡션은 '학습 손실', 왼쪽 축은 'train error (%)' 로 서로 다르다. 축 눈금이 %라 학습 오차로 읽었다(읽기 ±0.5 / ±1)", 11, fill=MUTED)
b += txt(410, 436, "논문은 오르는 구간의 원인을 가중치 감쇠로 들고 '드롭아웃이 일부 없앤다, 그림 2 · 3 을 보라'고 적지만 그림 2 에는 드롭아웃 곡선이 없다", 11, fill=NO)
svg("fig08_cifar_curves", W, H + 10, b, "CIFAR 학습 곡선 다시 그리기")


# ── 그림 9. 드롭아웃의 몫 (표 6) ────────────────────────────────────────────
T6 = [("WRN-16-4", (5.02, 5.24), (24.03, 23.91), (1.85, 1.64)),
      ("WRN-28-10", (4.00, 3.89), (19.25, 18.85), None),
      ("WRN-52-1 (가는 망)", (6.43, 6.28), (29.89, 29.78), (2.08, 1.70))]
W, H = 820, 400
b = defs()
b += txt(20, 30, "드롭아웃을 넣었을 때의 차이 (표 6) — 넣은 값 − 뺀 값, 백분율 점. 왼쪽으로 갈수록 좋아짐", 15, anchor="start", weight="bold")
ZX = 520
def DX(v):
    return ZX + v / 0.45 * 230
for v in (-0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3):
    b += line(DX(v), 60, DX(v), 310, LINE if v else INK2, 1)
    b += txt(DX(v), 326, "%+.1f" % v if v else "0", 10, fill=MUTED)
row = 0
for name, c10, c100, sv in T6:
    b += txt(25, 78 + 84 * row, name, 13, anchor="start", weight="bold")
    if row == 0:
        b += txt(700, 58, "뺀 값 → 넣은 값", 10, anchor="start", fill=MUTED)
    for j, (ds_, v) in enumerate((("CIFAR-10", c10), ("CIFAR-100", c100), ("SVHN", sv))):
        y = 72 + 84 * row + 22 * j
        b += txt(250, y + 12, ds_, 11, anchor="end", fill=INK2)
        if v is None:
            b += txt(ZX + 10, y + 12, "(표에 없음)", 10, anchor="start", fill=MUTED)
            continue
        dlt = v[1] - v[0]
        x1 = DX(dlt)
        col = S_DROP if dlt < 0 else NO
        b += '<rect x="%s" y="%s" width="%s" height="16" rx="2" fill="%s"/>' % (min(ZX, x1), y, abs(x1 - ZX), col)
        b += txt(x1 + (-6 if dlt < 0 else 6), y + 12, "%+.2f" % dlt, 11, anchor="end" if dlt < 0 else "start", weight="bold")
        b += txt(700, y + 12, "%.2f → %.2f" % v, 10, anchor="start", fill=MUTED)
    row += 1
b += txt(410, 352, "아홉 칸 중 여덟이 내려갔고, WRN-16-4 의 CIFAR-10 하나가 +0.22 로 올랐다(본문: '파라미터가 적어서일 것'이라는 추측)", 11, fill=INK2)
b += txt(410, 372, "CIFAR 는 다섯 번의 중앙값이지만 흩어짐이 적혀 있지 않아, −0.11 같은 차이가 실행마다 흔들리는 폭 밖인지 알 수 없다", 11, fill=NO)
b += txt(410, 392, "SVHN 칸은 몇 번 돌린 값인지 캡션에 없다. 드롭아웃 확률은 교차 검증으로 CIFAR 0.3, SVHN 0.4", 11, fill=MUTED)
svg("fig09_dropout", W, H + 10, b, "드롭아웃의 효과")


# ── 그림 10. SVHN 곡선 (논문 그림 3 오른쪽) ──────────────────────────────────
SV = {"nodrop": [(0, 5), (5, 3.2), (20, 2.7), (40, 2.6), (60, 2.6), (79, 2.5), (82, 1.85), (100, 1.8), (119, 1.78), (121, 3.4), (123, 1.95), (140, 1.9), (160, 1.87)],
      "drop": [(0, 5), (5, 3.1), (20, 2.7), (40, 2.5), (60, 2.5), (79, 2.5), (82, 1.75), (100, 1.75), (119, 1.8), (121, 2.0), (123, 1.7), (140, 1.66), (160, 1.65)]}
W, H = 820, 420
b = defs()
b += txt(20, 30, "SVHN, WRN-16-4 드롭아웃 유무 (논문 그림 3 오른쪽을 눈금으로 읽어 다시 그림, 읽기 ±0.1)", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 70, 520, 340, 70
def X(e):
    return PX0 + e / 160.0 * (PX1 - PX0)
def Y(v):
    return PY0 - v / 5.0 * (PY0 - PY1)
b = axis_y(b, PX0, PX1, Y, (0, 1, 2, 3, 4, 5))
for e in (0, 40, 80, 120, 160):
    b += txt(X(e), PY0 + 18, "%d" % e, 10, fill=MUTED)
for e in (80, 120):
    b += line(X(e), PY1, X(e), PY0, MUTED, 1, dash="2,3")
b += '<rect x="%s" y="%s" width="%s" height="%s" fill="#FFF3C4" opacity="0.6"/>' % (X(82), PY1, X(119) - X(82), PY0 - PY1)
b += polyline([(X(e), Y(v)) for e, v in SV["nodrop"]], S_WIDE, 2.0)
b += polyline([(X(e), Y(v)) for e, v in SV["drop"]], S_DROP, 2.0)
b += txt(X(100), PY1 + 16, "82~119 바퀴: 두 선이 겹친다", 10, fill=CODE)
b += txt(X(121) + 6, Y(3.4), "드롭아웃 없는 쪽이 튄다", 10, anchor="start", fill=S_WIDE)
b += txt(PX0 + 6, PY0 + 36, "바퀴 (epoch). 학습률은 80 · 120 에서 x 0.1. 세로축은 시험 오차 %", 10, anchor="start", fill=MUTED)
b += box(545, 70, 255, 270, fill=NODE, stroke=LINE)
notes_ = [("최종", True), ("드롭아웃 없음 1.85%", False), ("드롭아웃 0.4 1.64%", False), ("", False),
          ("곡선에서 읽은 것 (내 읽기)", True), ("차이 0.21 은 120 바퀴 뒤", False), ("마지막 40 바퀴에서 생긴다.", False),
          ("그 전 40 바퀴 동안은 두 선이", False), ("0.1 안에서 겹친다.", False), ("", False),
          ("곡선은 한 번의 실행이다", True), ("(캡션에 중앙값이라는 말이 없다)", False)]
for j, (t, bold) in enumerate(notes_):
    b += txt(560, 94 + 20 * j, t, 12 if bold else 11, anchor="start", weight="bold" if bold else None, fill=INK if bold else INK2)
b += txt(410, 408, "학습 손실 점선은 왼쪽 로그 축(10~100)인데 단위가 적혀 있지 않아 다시 그리지 않았다. 드롭아웃 없는 쪽이 120 바퀴 뒤 0 쪽으로 내려간다", 11, fill=MUTED)
svg("fig10_svhn_curves", W, H, b, "SVHN 학습 곡선 다시 그리기")


# ── 그림 11. 속도 — 시간 대 계산량 (논문 그림 4) ────────────────────────────────
F4 = [("ResNet-164", 85, 5.46, R164[1], "thin", 5.46), ("ResNet-1001", 512, 4.64, R1001[1], "thin", 4.92),
      ("WRN-40-4", 68, 4.66, p4[(40, 4)][1], "wide", 4.53), ("WRN-16-10", 164, 4.56, p4[(16, 10)][1], "wide", 4.56),
      ("WRN-28-10", 312, 4.38, p4[(28, 10)][1], "wide", 4.00)]
print("  [그림 4] 시간 / 곱-덧셈")
for n, t, e, m, f, e5 in F4:
    print("      %-12s %3d ms  %.3f G  → %.0f ms / G" % (n, t, m / 1e9, t / (m / 1e9)))
W, H = 820, 480
b = defs()
b += txt(20, 30, "속도 (논문 그림 4, Titan X, 배치 32, 앞+뒤 한 번) — 시간은 계산량을 따르지 않는다", 15, anchor="start", weight="bold")
# 왼쪽: 막대
PY0, PY1 = 330, 80
def Yt(v):
    return PY0 - v / 550.0 * (PY0 - PY1)
b = axis_y(b, 70, 380, Yt, (0, 100, 200, 300, 400, 500))
b += txt(225, 62, "시간 (ms)", 12, weight="bold")
for i, (n, t, e, m, f, e5) in enumerate(F4):
    x = 85 + 60 * i
    col = S_THIN if f == "thin" else S_WIDE
    b += '<rect x="%s" y="%s" width="40" height="%s" rx="3" fill="%s"/>' % (x, Yt(t), PY0 - Yt(t), col)
    b += txt(x + 20, Yt(t) - 6, "%d" % t, 11, weight="bold")
    b += txt(x + 20, PY0 + 16, n.replace("ResNet-", "R-").replace("WRN-", ""), 10, fill=INK2)
    b += txt(x + 20, PY0 + 32, "%.2f G" % (m / 1e9), 10, fill=MUTED)
b += txt(225, PY0 + 50, "아래 줄 = 이 파일이 센 합성곱 곱-덧셈 (32x32 한 장)", 10, fill=MUTED)
# 오른쪽: 산점도
QX0, QX1, QY0, QY1 = 460, 790, 330, 80
def QX(v):
    return QX0 + v / 6.0 * (QX1 - QX0)
def QY(v):
    return QY0 - v / 550.0 * (QY0 - QY1)
b = axis_y(b, QX0, QX1, QY, (0, 100, 200, 300, 400, 500))
for v in (0, 1, 2, 3, 4, 5, 6):
    b += txt(QX(v), QY0 + 16, "%d G" % v, 10, fill=MUTED)
b += txt(625, 62, "시간 대 곱-덧셈", 12, weight="bold")
for n, t, e, m, f, e5 in F4:
    col = S_THIN if f == "thin" else S_WIDE
    b += dot(QX(m / 1e9), QY(t), col, 6)
    right = n in ("WRN-28-10",)
    b += txt(QX(m / 1e9) + (-9 if right else 9), QY(t) + (4 if n != "ResNet-164" else -8), "%s  %.0f ms/G" % (n, t / (m / 1e9)), 10, anchor="end" if right else "start", fill=col)
b += txt(410, 412, "가는 망은 1 G 곱-덧셈에 약 345 ms, 넓은 망은 52~68 ms — 같은 계산을 5~7 배 빨리 한다", 11, fill=INK2)
b += txt(410, 430, "WRN-40-4 는 ResNet-1001 과 계산이 0.87 배인데 시간이 0.13 배다", 11, fill=INK2)
b += txt(410, 450, "'8 배 빠르다'는 512 / 68 = 7.5 배다. 막대 옆 오차 라벨(4.66 · 4.38)은 표 5 의 같은 망 값(4.53 · 4.00)과 다르다 — 노트 22절", 11, fill=NO)
b += txt(410, 470, "곱-덧셈은 합성곱 · fc 만 센 내 셈이고 논문에 없는 값이다. BN · ReLU · 덧셈은 넣지 않았다", 11, fill=MUTED)
svg("fig11_speed", W, H, b, "시간과 계산량")


# ── 그림 12. ImageNet 기본 블록 망의 폭 (표 7) ─────────────────────────────────
W, H = 820, 430
b = defs()
b += txt(20, 30, "ImageNet, 병목 없는 망의 폭 (표 7, top-1 검증 오차, 한 조각) — 파라미터가 비슷하면 깊은 쪽이 0.3~1.1 낮다", 14, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 80, 560, 360, 70
def X(v):
    return PX0 + (math.log10(v) - 1.0) / (math.log10(120) - 1.0) * (PX1 - PX0)
def Y(v):
    return PY0 - (v - 22.5) / 8.5 * (PY0 - PY1)
b = axis_y(b, PX0, PX1, Y, (23, 24, 25, 26, 27, 28, 29, 30, 31))
for v in (10, 20, 50, 100):
    b += txt(X(v), PY0 + 18, "%dM" % v, 10, fill=MUTED)
for d, col in ((18, S_THIN), (34, S_WIDE)):
    pts = [(X(r[3]), Y(r[1])) for r in t7[d]]
    b += polyline(pts, col, 2.2)
    for r in t7[d]:
        b += dot(X(r[3]), Y(r[1]), col, 5)
        last = d == 18 and r[0] == 3.0
        dx = (-10 if last else 10) if d == 18 else -10
        dy = -10 if d == 18 else 18
        b += txt(X(r[3]) + dx, Y(r[1]) + dy, "폭 %.1f  %.2f" % (r[0], r[1]), 10,
                 anchor="end" if (d == 34 or last) else "start", fill=col)
b += txt(X(11.7) + 4, Y(30.4) + 24, "WRN-18 (기본 블록 8 개)", 11, anchor="start", fill=S_THIN, weight="bold")
b += txt(X(21.8) - 30, Y(26.77) + 40, "WRN-34 (기본 블록 16 개)", 11, anchor="start", fill=S_WIDE, weight="bold")
b += box(585, 70, 215, 290, fill=NODE, stroke=LINE)
pairs = [("18-1.5 대 34-1.0", 25.9, 21.8, 27.06, 26.77), ("18-2.0 대 34-1.5", 45.6, 48.6, 25.58, 24.5), ("18-3.0 대 34-2.0", 101.8, 86.0, 24.06, 23.39)]
b += txt(600, 94, "파라미터가 비슷한 짝", 12, anchor="start", weight="bold")
for j, (lab, pa, pb, ea, eb) in enumerate(pairs):
    y = 124 + 64 * j
    b += txt(600, y, lab, 12, anchor="start", weight="bold")
    b += txt(600, y + 20, "%.1fM 대 %.1fM" % (pa, pb), 11, anchor="start", fill=INK2)
    b += txt(600, y + 38, "%.2f 대 %.2f → 깊은 쪽 %.2f 낮음" % (ea, eb, ea - eb), 11, anchor="start", fill=S_WIDE)
b += txt(600, 330, "캡션: '비슷한 정확도'", 11, anchor="start", fill=MUTED)
b += txt(410, 400, "파라미터는 이 파일이 센 값과 표가 0.0~0.2M 안에서 맞는다(폭 1.0 은 torchvision 의 ResNet-18 · 34 와 같다). 한 번의 실행인지는 적혀 있지 않다", 11, fill=MUTED)
b += txt(410, 420, "가로축은 로그. 이 표의 망은 사전 활성이 아니라 원래 ResNet 블록이다(본문 3절: 100 층 아래에서는 차이가 없었다)", 11, fill=MUTED)
svg("fig12_imagenet_width", W, H, b, "ImageNet 기본 블록 망의 폭")


# ── 그림 13. ImageNet 병목 망 (표 8) ─────────────────────────────────────────
W, H = 820, 470
b = defs()
b += txt(20, 30, "ImageNet 병목 망 (표 8, 한 조각 top-1) — WRN-50-2 는 ResNet-152 와 곱-덧셈이 0.99 배, 시간이 0.81 배", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 80, 520, 360, 70
def X(v):
    return PX0 + (v - 40) / 125.0 * (PX1 - PX0)
def Y(v):
    return PY0 - (v - 21.4) / 2.9 * (PY0 - PY1)
b = axis_y(b, PX0, PX1, Y, (21.5, 22.0, 22.5, 23.0, 23.5, 24.0), "%.1f")
for v in (50, 75, 100, 125, 150):
    b += txt(X(v), PY0 + 18, "%d ms" % v, 10, fill=MUTED)
b += txt(300, PY0 + 38, "배치 16 의 시간 (표 8 의 time/batch 16 칸)", 10, fill=MUTED)
for name, e1, e5, pp, tm, P, M, st in t8:
    col = S_WIDE if name.startswith("WRN") else S_THIN
    r = 4 + pp / 10.0
    b += circ(X(tm), Y(e1), r, col, col, op=0.85)
    dx = {"ResNet-50": 14, "ResNet-101": 14, "ResNet-152": 14, "WRN-50-2": -14, "pre-ResNet-200": -14}[name]
    b += txt(X(tm) + dx, Y(e1) + 4, "%s %.2f" % (name, e1), 11, anchor="start" if dx > 0 else "end", fill=col, weight="bold")
b += box(545, 60, 255, 300, fill=NODE, stroke=LINE)
b += txt(560, 84, "파라미터 · 곱-덧셈 (내 셈)", 12, anchor="start", weight="bold")
for j, (name, e1, e5, pp, tm, P, M, st) in enumerate(t8):
    y = 112 + 46 * j
    b += txt(560, y, name, 12, anchor="start", weight="bold", fill=S_WIDE if name.startswith("WRN") else S_THIN)
    b += txt(560, y + 18, "%.1fM (표 %.1fM) · %.2f G" % (P / 1e6, pp, M / 1e9), 11, anchor="start", fill=INK2)
b += txt(560, 350, "원 크기 = 파라미터", 10, anchor="start", fill=MUTED)
b += txt(410, 424, "WRN-50-2 대 ResNet-152: top-1 0.26 낮고 시간 93 대 115 ms. 대 pre-ResNet-200: 0.24 높고 시간 0.60 배('거의 2 배 빠르다')", 11, fill=INK2)
b += txt(410, 444, "pre-ResNet-200 의 파라미터를 원래 블록으로 세면 표의 64.7M 과 같다. 각 값은 한 번의 실행이다(흩어짐 없음)", 11, fill=MUTED)
b += txt(410, 462, "표 9 는 WRN-50-2 의 top-5 를 5.79 로 적는데 표 8 에서 5.79 는 pre-ResNet-200 의 값이고 WRN-50-2 는 6.03 이다", 11, fill=NO)
svg("fig13_imagenet_bottleneck", W, H, b, "ImageNet 병목 망 비교")


# ── 그림 14. WRN-50-2 는 병목의 어디를 넓혔나 ────────────────────────────────
W, H = 820, 450
b = defs()
b += txt(20, 30, "WRN-50-2 — 병목의 안쪽 두 층(1x1 줄이기의 출력 · 3x3)만 두 배, 블록의 입출력 채널은 ResNet-50 과 같다", 14, anchor="start", weight="bold")
def bott(b, x0, title, mid, col):
    b += txt(x0 + 160, 66, title, 13, weight="bold", fill=col)
    specs = [("1x1", 256, mid), ("3x3", mid, mid), ("1x1", mid, 256)]
    for j, (kk, ci, co) in enumerate(specs):
        y = 84 + 58 * j
        wbox = 60 + co / 256.0 * 150 if j < 2 else 210
        b += box(x0 + 160 - wbox / 2, y, wbox, 36, fill=REV_SOFT if j == 1 else FWD_SOFT, stroke=REV if j == 1 else FWD)
        b += txt(x0 + 160, y + 23, "%s, %d → %d" % (kk, ci, co), 12)
        if j < 2:
            b += line(x0 + 160, y + 36, x0 + 160, y + 56, INK2, 1.1, marker="ai")
    b += txt(x0 + 160, 268, "layer1 의 블록 (입력 256 채널, 56x56)", 11, fill=INK2)
    p = 256 * mid + 9 * mid * mid + mid * 256
    b += txt(x0 + 160, 290, "합성곱 파라미터 %s" % fmt(p), 12, weight="bold")
    return b
b = bott(b, 30, "ResNet-50 — 안쪽 64", 64, S_THIN)
b = bott(b, 420, "WRN-50-2 — 안쪽 128", 128, S_WIDE)
b += txt(410, 325, "단계별 파라미터 (이 파일이 센 값, BN · 사영 포함)", 12, weight="bold")
for j, (a, c) in enumerate(zip(R50[7], W50[7])):
    x = 40 + 190 * j
    b += box(x, 340, 175, 64, fill=NODE, stroke=LINE)
    b += txt(x + 87, 360, "layer%d · 출력 %d" % (j + 1, a[1]), 11, weight="bold")
    b += txt(x + 87, 378, "%.2fM → %.2fM" % (a[4] / 1e6, c[4] / 1e6), 11, fill=INK2)
    b += txt(x + 87, 396, "%.2f 배" % (c[4] / a[4]), 11, fill=S_WIDE, weight="bold")
b += txt(410, 428, "전체 %s 대 %s (2.70 배) — torchvision 의 resnet50 · wide_resnet50_2 와 한 자리까지 같다. 곱-덧셈 %.2f G 대 %.2f G" % (fmt(R50[5]), fmt(W50[5]), R50[6] / 1e9, W50[6] / 1e9), 11, fill=MUTED)
b += txt(410, 446, "논문 문장은 '안쪽 3x3 층의 폭을 늘렸다'. 3x3 의 입력 폭도 늘어야 하므로 앞 1x1 의 출력까지 함께 두 배가 된다(내 풀이)", 11, fill=MUTED)
svg("fig14_wrn50_bottleneck", W, H + 10, b, "WRN-50-2 병목 블록의 폭")


# ── 그림 15. PatchCore 가 쓰는 자리 ──────────────────────────────────────────
W, H = 820, 440
b = defs()
b += txt(20, 30, "PatchCore 가 쓰는 자리 — layer2 · layer3 의 출력 (224 입력). 넓혀도 특징의 차원은 ResNet-50 과 같다", 14, anchor="start", weight="bold")
shapes = [("layer1", 256, 56, False), ("layer2", 512, 28, True), ("layer3", 1024, 14, True), ("layer4", 2048, 7, False)]
for j, (nm, c, s, used) in enumerate(shapes):
    x = 30 + 195 * j
    side = 30 + s * 1.6
    col = S_WIDE if used else MUTED
    b += box(x + 90 - side / 2, 150 - side / 2, side, side, fill=REV_SOFT if used else NODE, stroke=col, sw=2 if used else 1)
    b += txt(x + 90, 60, nm, 13, weight="bold", fill=col)
    b += txt(x + 90, 250, "%d 채널 x %dx%d" % (c, s, s), 12, fill=INK)
    b += txt(x + 90, 270, "보폭 누적 %d" % (224 // s), 11, fill=INK2)
    st_r = R50[7][j][4]; st_w = W50[7][j][4]
    b += txt(x + 90, 290, "파라미터 %.1fM (R50 %.1fM)" % (st_w / 1e6, st_r / 1e6), 10, fill=MUTED)
b += box(30, 310, 370, 110, fill=NODE, stroke=S_WIDE)
for j, t in enumerate(["논문이 말한 것", "ImageNet 에서는 같은 깊이에서 폭이 더 있어야 같은 정확도에", "닿는다(표 7 · 8). WRN-50-2 가 ResNet-152 보다 top-1 0.26 낮다.", "특징 추출 · 이상 탐지에 대해서는 아무 말도 하지 않는다"]):
    b += txt(45, 334 + 22 * j, t, 12 if j == 0 else 11, anchor="start", weight="bold" if j == 0 else None, fill=INK if j == 0 else INK2)
b += box(420, 310, 380, 110, fill=NODE, stroke=MUTED, dash="5,4")
for j, t in enumerate(["내 추측 (재지 않았다)", "출력 채널(512 + 1,024 = 1,536)은 그대로이고 안쪽 폭만", "두 배라, 기억 뱅크 크기는 그대로 둔 채 같은 차원에 더 많은", "필터를 거친 특징을 얻는 쪽이다. 몫은 ResNet-50 과 바꿔 재야 안다"]):
    b += txt(435, 334 + 22 * j, t, 12 if j == 0 else 11, anchor="start", weight="bold" if j == 0 else None, fill=INK if j == 0 else INK2)
svg("fig15_patchcore", W, H, b, "PatchCore 가 쓰는 WRN-50-2 의 단계")


# ── 그림 16. 계보 ────────────────────────────────────────────────────────
W, H = 820, 380
b = defs()
b += txt(20, 30, "계보 — 깊이를 늘리던 흐름에서 폭으로 돌아선 자리", 15, anchor="start", weight="bold")
nodes = [(40, 70, "Highway (2015-05)", "게이트 지름길 · 특징 재사용 감소라는 말", INK2),
         (40, 150, "ResNet (2015-12)", "항등 지름길, 병목으로 가늘게", S_THIN),
         (40, 230, "사전 활성 ResNet (2016-03)", "BN-ReLU-합성곱, 1001 층", S_THIN),
         (40, 310, "확률 깊이 (2016-03)", "학습 중 블록을 통째로 끈다", S_THIN),
         (430, 190, "Wide ResNet (2016-05, 이 논문)", "깊이 대신 폭, 블록 안 드롭아웃", S_WIDE),
         (430, 300, "PatchCore (2022) — 이 논문 뒤", "WRN-50-2 를 얼려 특징 추출기로", S_DROP)]
for x, y, t, s, col in nodes:
    b += box(x, y - 26, 330, 52, fill=NODE, stroke=col, sw=1.6)
    b += txt(x + 165, y - 5, t, 13, weight="bold", fill=col)
    b += txt(x + 165, y + 15, s, 11, fill=INK2)
for y in (70, 150, 230, 310):
    b += path("M370,%d C400,%d 400,190 428,190" % (y, y), INK2, sw=1.2, marker="ai")
b += line(595, 216, 595, 272, INK2, 1.2, marker="ai")
b += txt(20, 365, "날짜는 arXiv 첫 판. PatchCore 는 이 논문의 참고 문헌에 없다(뒤에 나온 편이다)", 11, anchor="start", fill=MUTED)
svg("fig16_lineage", W, H, b, "Wide ResNet 의 계보")
