# -*- coding: utf-8 -*-
"""ResNet 노트(He, Zhang, Ren, Sun, CVPR 2016)의 그림 열여섯을 만든다.

색과 글꼴은 앞선 노트들(퍼셉트론부터 GAN 까지)의 그림과 맞췄다 — 저장소의 노트들이 한 벌로 읽히게
하려는 것이다. 결과 그림은 계열 색 셋을 고정해 쓴다(평범한 망 · 잔차 망 · VGG).
바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

이 파일이 직접 계산하는 것: 표 1 의 다섯 망과 VGG-16/19 의 파라미터 수와 곱-덧셈 수(FLOPs),
기본 블록과 병목 블록의 파라미터, 지름길 선택지 A/B/C 가 더하는 파라미터, CIFAR-10 망(6n+2)의
파라미터, 선형 스칼라 사슬에서 평범한 곱과 잔차 곱의 크기(seed 0), WideResNet-50-2 의 단계별
크기. 논문 그림 1 · 4 · 6 · 7 의 값은 300 dpi 로 눈금을 읽은 값을 상수로 적었다.
계산한 값은 돌릴 때 화면에도 찍는다.
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


# ── 세는 도구 — 파라미터 수와 곱-덧셈 수 ─────────────────────────────────────
def conv(cin, cout, k, hout, bn=True, bias=False):
    """합성곱 하나의 (파라미터, 곱-덧셈). BN 은 채널마다 학습되는 값 둘(γ, β)을 센다."""
    p = k * k * cin * cout + (2 * cout if bn else 0) + (cout if bias else 0)
    m = k * k * cin * cout * hout * hout
    return p, m


def resnet(blocks, bottleneck, shortcut="B", stride_on="1x1", inner=1, verbose=False):
    """ImageNet 224 입력의 ResNet 을 센다. shortcut: A(영 채움) / B(차원이 바뀔 때만 사영) / C(모두 사영)."""
    P, M = conv(3, 64, 7, 112)
    cin, h = 64, 56
    stages = []
    for s, n in enumerate(blocks):
        c = 64 * 2 ** s
        out = 4 * c if bottleneck else c
        mid = c * inner
        sp = sm = 0
        for b in range(n):
            stride = 2 if (s > 0 and b == 0) else 1
            hout = h // stride
            parts = []
            if bottleneck:
                parts.append(conv(cin, mid, 1, hout if stride_on == "1x1" else h))
                parts.append(conv(mid, mid, 3, hout))
                parts.append(conv(mid, out, 1, hout))
            else:
                parts.append(conv(cin, c, 3, hout))
                parts.append(conv(c, c, 3, hout))
            need = (cin != out) or stride != 1
            if (shortcut == "B" and need) or shortcut == "C":
                parts.append(conv(cin, out, 1, hout))
            for p, m in parts:
                sp += p; sm += m
            h, cin = hout, out
        P += sp; M += sm
        stages.append((c, out, h, n, sp))
    P += cin * 1000 + 1000
    M += cin * 1000
    return P, M, stages


def vgg(cfg):
    P = M = 0
    cin, h = 3, 224
    for v in cfg:
        if v == "M":
            h //= 2
            continue
        p, m = conv(cin, v, 3, h, bn=False, bias=True)
        P += p; M += m; cin = v
    for a, c in ((512 * 7 * 7, 4096), (4096, 4096), (4096, 1000)):
        P += a * c + c; M += a * c
    return P, M


def cifar(n):
    P, _ = conv(3, 16, 3, 32)
    cin = 16
    for c in (16, 32, 64):
        for b in range(n):
            P += conv(cin, c, 3, 1)[0] + conv(c, c, 3, 1)[0]
            cin = c
    return P + 64 * 10 + 10


CFG = {18: ([2, 2, 2, 2], False), 34: ([3, 4, 6, 3], False), 50: ([3, 4, 6, 3], True),
       101: ([3, 4, 23, 3], True), 152: ([3, 8, 36, 3], True)}
PAPER_FLOPS = {18: 1.8, 34: 3.6, 50: 3.8, 101: 7.6, 152: 11.3}
REF_PARAMS = {18: 11689512, 34: 21797672, 50: 25557032, 101: 44549160, 152: 60192808}
counts = {}
print("  [표 1] 파라미터 · 곱-덧셈 (선택지 B, 병목은 보폭을 첫 1x1 에):")
for d, (bl, bot) in CFG.items():
    P, M, st = resnet(bl, bot)
    P3, M3, _ = resnet(bl, bot, stride_on="3x3")
    counts[d] = (P, M, M3)
    print("      ResNet-%-3d 파라미터 %s (torchvision 참고값 %s)  곱-덧셈 %.2f G (논문 %.1f)  보폭을 3x3 에 두면 %.2f G"
          % (d, fmt(P), fmt(REF_PARAMS[d]), M / 1e9, PAPER_FLOPS[d], M3 / 1e9))
V16 = vgg([64, 64, "M", 128, 128, "M", 256, 256, 256, "M", 512, 512, 512, "M", 512, 512, 512, "M"])
V19 = vgg([64, 64, "M", 128, 128, "M", 256, 256, 256, 256, "M", 512, 512, 512, 512, "M", 512, 512, 512, 512, "M"])
print("      VGG-16 파라미터 %s 곱-덧셈 %.2f G (논문 15.3)   VGG-19 파라미터 %s 곱-덧셈 %.2f G (논문 19.6)"
      % (fmt(V16[0]), V16[1] / 1e9, fmt(V19[0]), V19[1] / 1e9))
PA, MA, _ = resnet([3, 4, 6, 3], False, shortcut="A")
PB, MB, _ = resnet([3, 4, 6, 3], False, shortcut="B")
PC, MC, _ = resnet([3, 4, 6, 3], False, shortcut="C")
print("  [선택지] ResNet-34: A %s / B %s (+%s) / C %s (+%s 더)" % (fmt(PA), fmt(PB), fmt(PB - PA), fmt(PC), fmt(PC - PB)))
print("      ResNet-34 A 곱-덧셈 %.3f G = 평범한 34 층과 같다.  34 층 대 VGG-19: %.1f%%" % (MA / 1e9, 100 * MA / V19[1]))


# ── 그림 1. 퇴화 문제 — 깊은 평범한 망이 학습 오차부터 높다 ─────────────────────
F1 = {"train": (1.5, 6.0), "test": (9.7, 13.2)}          # CIFAR-10 평범한 20 / 56 층, 그림 1 끝 값, 읽기 ±1
T2 = {"plain": (27.94, 28.54), "res": (27.88, 25.03)}    # 표 2, top-1 %, 10-crop
W, H = 820, 430
b = defs()
b += txt(20, 30, "퇴화 문제 — 층을 더했는데 학습 오차부터 높아진다 (과적합이면 학습 오차는 낮아야 한다)", 15, anchor="start", weight="bold")
def bars(b, x0, title, groups, vmax, unit, note):
    b += box(x0, 50, 385, 335, fill="none", stroke=LINE)
    b += txt(x0 + 192, 72, title, 13, weight="bold")
    base = 300
    for gi, (gname, items) in enumerate(groups):
        gx = x0 + 40 + 175 * gi
        b += txt(gx + 70, base + 22, gname, 12, weight="bold")
        for k, (lab, v, col) in enumerate(items):
            hgt = v / vmax * 190
            x = gx + 10 + 70 * k
            b += '<rect x="%s" y="%s" width="50" height="%s" rx="3" fill="%s"/>' % (x, base - hgt, hgt, col)
            b += txt(x + 25, base - hgt - 6, ("%.2f" % v) if v % 1 else "%d" % v, 11, weight="bold")
            b += txt(x + 25, base + 40, lab, 11, fill=INK2)
    b += line(x0 + 30, base, x0 + 370, base, INK2, 1)
    b += txt(x0 + 192, 372, note, 11, fill=MUTED)
    return b
b = bars(b, 20, "CIFAR-10 평범한 망 (그림 1, 눈금 읽기 ±1)",
         [("학습 오차 %", [("20 층", F1["train"][0], S_PLAIN), ("56 층", F1["train"][1], NO)]),
          ("시험 오차 %", [("20 층", F1["test"][0], S_PLAIN), ("56 층", F1["test"][1], NO)])], 16, "%",
         "56 층이 학습 · 시험 둘 다 높다")
b = bars(b, 415, "ImageNet top-1 오차 % (표 2, 10-crop)",
         [("평범한 망", [("18 층", T2["plain"][0], S_PLAIN), ("34 층", T2["plain"][1], NO)]),
          ("잔차 망", [("18 층", T2["res"][0], S_RES), ("34 층", T2["res"][1], OK)])], 34, "%",
         "평범한 망은 +0.60, 잔차 망은 −2.85 — 방향이 뒤집힌다")
b += txt(410, 415, "왼쪽 막대의 높이는 눈금을 읽은 값이라 소수 첫째 자리까지만 적는다. 오른쪽은 표의 값 그대로다", 11, fill=MUTED)
svg("fig01_degradation", W, H, b, "퇴화 문제 막대 그림")


# ── 그림 2. 구성 논증 — 깊은 망에는 얕은 망만큼 좋은 해가 늘 있다 ─────────────────
W, H = 820, 330
b = defs()
b += txt(20, 30, "구성 논증 — 얕은 망을 베끼고 더한 층을 항등으로 두면 깊은 망도 같은 학습 오차를 낸다", 15, anchor="start", weight="bold")
def stack(b, x0, layers, title, col):
    b += txt(x0 + 60, 70, title, 13, weight="bold", fill=col)
    for k, (lab, f, s) in enumerate(layers):
        y = 90 + 30 * k
        b += box(x0, y, 120, 24, fill=f, stroke=s)
        b += txt(x0 + 60, y + 17, lab, 11)
    return b
shallow = [("층 1 (학습됨)", FWD_SOFT, FWD), ("층 2 (학습됨)", FWD_SOFT, FWD), ("층 3 (학습됨)", FWD_SOFT, FWD)]
deep = [("층 1 (베낌)", FWD_SOFT, FWD), ("층 2 (베낌)", FWD_SOFT, FWD), ("층 3 (베낌)", FWD_SOFT, FWD),
        ("더한 층 = 항등", CODE_SOFT, CODE), ("더한 층 = 항등", CODE_SOFT, CODE), ("더한 층 = 항등", CODE_SOFT, CODE)]
b = stack(b, 60, shallow, "얕은 망", FWD)
b = stack(b, 300, deep, "깊은 망 (구성한 해)", CODE)
b += line(185, 135, 295, 135, INK2, 1.4, marker="ai")
b += txt(240, 125, "그대로 베낀다", 11, fill=INK2)
b += box(470, 70, 330, 200, fill=NODE, stroke=LINE)
for j, l in enumerate(["이 해의 학습 오차 = 얕은 망의 학습 오차",
                       "→ 깊은 망의 최선은 얕은 망보다 나쁠 수 없다",
                       "",
                       "그런데 실험에서는 더 나빴다 (그림 1)",
                       "→ 해가 없는 것이 아니라 풀이기(SGD)가",
                       "   그 해를 (적당한 시간 안에) 못 찾는다",
                       "",
                       "논문의 가설: 여러 비선형 층으로",
                       "항등을 맞추는 일이 어렵다"]):
    b += txt(485, 96 + 20 * j, l, 12, anchor="start", fill=NO if j in (3,) else INK)
b += txt(410, 310, "잔차 학습은 이 가설에서 나온다 — 항등이 최선이면 잔차 F 를 0 으로 밀기만 하면 된다", 12, fill=OK, weight="bold")
svg("fig02_construction", W, H, b, "구성 논증")


# ── 그림 3. 잔차 블록 — 식 (1) 과 논문 그림 2 ─────────────────────────────────
W, H = 820, 380
b = defs()
b += txt(20, 30, "잔차 블록 — 층 둘이 H(x) 대신 F(x) = H(x) − x 를 배우고, 지름길이 x 를 더한다 (논문 그림 2)", 15, anchor="start", weight="bold")
cx = 250
b += txt(cx, 72, "x", 16, style="italic", weight="bold")
b += line(cx, 78, cx, 98, INK2, 1.4, marker="ai")
b += box(cx - 80, 100, 160, 36, fill=REV_SOFT, stroke=REV); b += txt(cx, 123, "가중치 층 (3x3 합성곱 + BN)", 11)
b += line(cx, 138, cx, 156, INK2, 1.4, marker="ai"); b += txt(cx + 12, 152, "ReLU", 11, anchor="start", fill=INK2)
b += box(cx - 80, 158, 160, 36, fill=REV_SOFT, stroke=REV); b += txt(cx, 181, "가중치 층 (3x3 합성곱 + BN)", 11)
b += line(cx, 196, cx, 226, INK2, 1.4, marker="ai"); b += txt(cx - 12, 216, "F(x)", 12, anchor="end", fill=REV, weight="bold")
b += circ(cx, 240, 14, NODE, INK); b += txt(cx, 245, "+", 16, weight="bold")
b += path("M%s,86 C%s,86 %s,100 %s,150 C%s,200 %s,240 %s,240" % (cx, cx + 150, cx + 150, cx + 150, cx + 150, cx + 150, cx + 16), CODE, sw=2.2, marker="ac")
b += txt(cx + 160, 150, "항등 지름길 x", 12, anchor="start", fill=CODE, weight="bold")
b += txt(cx + 160, 168, "파라미터 0", 11, anchor="start", fill=CODE)
b += txt(cx + 160, 184, "계산은 더하기뿐", 11, anchor="start", fill=CODE)
b += line(cx, 256, cx, 282, INK2, 1.4, marker="ai"); b += txt(cx + 12, 274, "ReLU (더한 뒤)", 11, anchor="start", fill=INK2)
b += txt(cx, 300, "y = σ(F(x) + x)", 13, weight="bold")
b += box(520, 60, 280, 280, fill=NODE, stroke=LINE)
lines3 = [("식 (1)  y = F(x, {Wᵢ}) + x", True), ("F = W₂ σ(W₁ x)  (치우침 생략)", False), ("", False),
          ("식 (2)  y = F(x, {Wᵢ}) + W_s x", True), ("x 와 F 의 차원이 다를 때만", False), ("W_s 로 맞춘다 (1x1 합성곱)", False), ("", False),
          ("작은 예시 (내가 붙인 것)", True), ("x = 2.0, F(x) = 0.1 이면 y = 2.1", False),
          ("항등이 최선이면 F → 0 이 목표다", False), ("평범한 망은 W₂σ(W₁x) = x 를", False), ("직접 맞춰야 한다", False)]
for j, (l, bold) in enumerate(lines3):
    b += txt(535, 86 + 21 * j, l, 12, anchor="start", weight="bold" if bold else None)
svg("fig03_residual_block", W, H, b, "잔차 블록 구조")


# ── 그림 4. 선형 스칼라 사슬 — 가중치가 0 근처일 때 평범한 곱과 잔차 곱 ─────────────
sigma = 0.1
trials = 2000
res4 = {}
for L in (2, 10, 34, 110):
    lp, lr = [], []
    for _ in range(trials):
        ws = [random.gauss(0, sigma) for _ in range(L)]
        lp.append(sum(math.log10(abs(w) + 1e-300) for w in ws))
        lr.append(sum(math.log10(abs(1 + w)) for w in ws))
    lp.sort(); lr.sort()
    res4[L] = (lp[trials // 2], lr[trials // 2])
    print("  [4] L=%-3d 가중치 ~ N(0, %.1f²): 평범한 곱 |Π w| 중앙값 10^%.1f,  잔차 곱 |Π(1+w)| 중앙값 10^%.3f (= %.3f)"
          % (L, sigma, res4[L][0], res4[L][1], 10 ** res4[L][1]))
W, H = 820, 380
b = defs()
b += txt(20, 30, "층마다 y = w·x (평범한 망) 대 y = x + w·x (잔차 망), w ~ N(0, 0.1²) — 입력에 대한 기울기의 크기 (내가 붙인 예)", 14, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 90, 520, 320, 70
Ls = [2, 10, 34, 110]
def px(i):
    return PX0 + i / 3.0 * (PX1 - PX0)
def py(v):
    return PY0 - (v + 140) / 142.0 * (PY0 - PY1)
for v in (0, -20, -40, -60, -80, -100, -120, -140):
    b += line(PX0, py(v), PX1, py(v), LINE, 1)
    b += txt(PX0 - 8, py(v) + 4, "10^%d" % v if v else "1", 10, anchor="end", fill=MUTED)
for i, L in enumerate(Ls):
    b += txt(px(i), PY0 + 18, "L = %d" % L, 11, fill=MUTED)
b += polyline([(px(i), py(res4[L][0])) for i, L in enumerate(Ls)], S_PLAIN, 2.4)
b += polyline([(px(i), py(res4[L][1])) for i, L in enumerate(Ls)], S_RES, 2.4)
for i, L in enumerate(Ls):
    b += circ(px(i), py(res4[L][0]), 4, S_PLAIN, S_PLAIN)
    b += circ(px(i), py(res4[L][1]), 4, S_RES, S_RES)
b += txt(px(2) + 12, py(res4[34][0]) + 4, "평범한 곱 |Π w|", 12, anchor="start", fill=S_PLAIN, weight="bold")
b += txt(px(2), py(0) - 8, "잔차 곱 |Π(1 + w)|", 12, fill=S_RES, weight="bold")
b += box(550, 70, 250, 250, fill=NODE, stroke=LINE)
b += txt(565, 94, "중앙값 (2,000 번 뽑기, seed 0)", 12, anchor="start", weight="bold")
for j, L in enumerate(Ls):
    b += txt(565, 122 + 26 * j, "L=%-3d  평범 10^%.0f,  잔차 %.3f" % (L, res4[L][0], 10 ** res4[L][1]), 12, anchor="start")
for j, l in enumerate(["가중치가 0 근처에서 시작하면", "평범한 망은 곱이 사라지고", "잔차 망은 1 근처에 남는다.", "논문의 퇴화 설명과는 다른 자리다(본문)"]):
    b += txt(565, 236 + 20 * j, l, 11, anchor="start", fill=INK2 if j < 3 else NO)
svg("fig04_scalar_chain", W, H, b, "평범한 곱과 잔차 곱의 크기")


# ── 그림 5. 지름길 선택지 A / B / C (표 3) ──────────────────────────────────
T3 = [("평범한 34", 28.54, 10.02, PA), ("ResNet-34 A", 25.03, 7.76, PA), ("ResNet-34 B", 24.52, 7.46, PB), ("ResNet-34 C", 24.19, 7.40, PC)]
W, H = 820, 380
b = defs()
b += txt(20, 30, "지름길 선택지 셋 — 차원이 늘 때 영으로 채울까(A), 사영할까(B), 모든 지름길을 사영할까(C) (표 3)", 15, anchor="start", weight="bold")
opts = [("A", "영 채움", "항등 + 늘어난 채널은 0", "추가 파라미터 0", CODE),
        ("B", "늘 때만 사영", "3 곳만 1x1 합성곱 W_s", "+%s" % fmt(PB - PA), REV),
        ("C", "모두 사영", "16 곳 모두 1x1 합성곱", "B 보다 +%s" % fmt(PC - PB), NO)]
for k, (n, t, d, extra, col) in enumerate(opts):
    x = 20 + 265 * k
    b += box(x, 50, 250, 110, fill=NODE, stroke=col, sw=1.6)
    b += txt(x + 125, 76, "%s — %s" % (n, t), 13, weight="bold", fill=col)
    b += txt(x + 125, 100, d, 12)
    b += txt(x + 125, 124, extra, 12, fill=INK2, weight="bold")
    b += txt(x + 125, 146, "(파라미터는 이 파일이 센 값)", 10, fill=MUTED)
PX0, PX1 = 200, 760
def X(v):
    return PX0 + (v - 23.5) / 5.5 * (PX1 - PX0)
for v in (24, 25, 26, 27, 28, 29):
    b += line(X(v), 180, X(v), 330, LINE, 1)
    b += txt(X(v), 348, "%d" % v, 10, fill=MUTED)
for k, (n, t1, t5, p) in enumerate(T3):
    y = 198 + 36 * k
    b += txt(PX0 - 12, y + 4, n, 12, anchor="end", weight="bold")
    col = S_PLAIN if k == 0 else S_RES
    b += '<rect x="%s" y="%s" width="%s" height="18" rx="3" fill="%s"/>' % (PX0, y - 9, X(t1) - PX0, col)
    b += txt(X(t1) + 6, y + 4, "%.2f (top-5 %.2f)" % (t1, t5), 11, anchor="start")
b += txt(480, 370, "top-1 오차 % (10-crop). A→B −0.51, B→C −0.33. 평범한 망과의 차 3.51 에 비해 작다 — 논문은 C 를 뒤에서 쓰지 않는다", 11, fill=MUTED)
svg("fig05_shortcut_options", W, H, b, "지름길 선택지 비교")


# ── 그림 6. 34 층 망의 네 단계 (논문 그림 3 과 표 1) ─────────────────────────────
W, H = 820, 380
b = defs()
b += txt(20, 30, "34 층 망의 모양 — 크기가 반이 될 때마다 필터를 두 배로 (논문 그림 3 · 표 1)", 15, anchor="start", weight="bold")
stages6 = [("conv1", "7x7, 64, /2", 112, 1, FWD_SOFT, FWD), ("conv2_x", "3x3 64 x 6", 56, 3, REV_SOFT, REV),
           ("conv3_x", "3x3 128 x 8", 28, 4, REV_SOFT, REV), ("conv4_x", "3x3 256 x 12", 14, 6, REV_SOFT, REV),
           ("conv5_x", "3x3 512 x 6", 7, 3, REV_SOFT, REV), ("풀링 + fc", "평균, 1000", 1, 0, FWD_SOFT, FWD)]
for k, (n, d, sz, nb, f, s) in enumerate(stages6):
    x = 30 + 130 * k
    side = 20 + 0.9 * sz
    b += box(x + 55 - side / 2, 190 - side / 2, side, side, fill=f, stroke=s, rx=3)
    b += txt(x + 55, 62, n, 13, weight="bold")
    b += txt(x + 55, 290, d, 11, fill=INK2)
    b += txt(x + 55, 310, "%d x %d" % (sz, sz), 12, weight="bold")
    b += txt(x + 55, 330, ("블록 %d 개" % nb) if nb else "", 11, fill=REV)
    if k < 5:
        b += line(x + 110, 190, x + 128, 190, INK2, 1.4, marker="ai")
b += txt(410, 360, "규칙 둘: (i) 같은 크기면 필터 수가 같다 (ii) 크기가 반이 되면 필터가 두 배 → 층마다 시간 복잡도가 같다. 줄이기는 보폭 2 합성곱으로", 11, fill=MUTED)
svg("fig06_stages", W, H, b, "34 층 망의 단계 구조")


# ── 그림 7. 표 1 — 다섯 깊이의 블록 수, 파라미터, 곱-덧셈 ────────────────────────
W, H = 820, 420
b = defs()
b += txt(20, 30, "표 1 의 다섯 망 — 단계별 블록 수와 곱-덧셈 (논문 값) 옆에 이 파일이 센 파라미터와 곱-덧셈", 15, anchor="start", weight="bold")
cw = [120, 70, 70, 70, 70, 110, 110, 180]
hdr = ["망", "conv2", "conv3", "conv4", "conv5", "논문 FLOPs", "센 FLOPs", "센 파라미터"]
x0, y0 = 20, 55
b += box(x0, y0, sum(cw), 34, fill="#DDE3E0", stroke=LINE, rx=4)
for k, t in enumerate(hdr):
    b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y0 + 22, t, 12, weight="bold")
rows7 = []
for d, (bl, bot) in CFG.items():
    P, M, M3 = counts[d]
    rows7.append(("ResNet-%d %s" % (d, "(병목)" if bot else "(기본)"), bl, "%.1f G" % PAPER_FLOPS[d], "%.2f G" % (M / 1e9), "%.1f M" % (P / 1e6)))
rows7.append(("VGG-16", None, "15.3 G", "%.2f G" % (V16[1] / 1e9), "%.1f M" % (V16[0] / 1e6)))
rows7.append(("VGG-19", None, "19.6 G", "%.2f G" % (V19[1] / 1e9), "%.1f M" % (V19[0] / 1e6)))
for r, (n, bl, pf, mf, pp) in enumerate(rows7):
    y = y0 + 34 + 36 * r
    b += box(x0, y, sum(cw), 36, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    cells = [n] + ([str(v) for v in bl] if bl else ["—"] * 4) + [pf, mf, pp]
    for k, t in enumerate(cells):
        b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y + 23, t, 12, weight="bold" if k == 0 else None,
                 fill=S_VGG if n.startswith("VGG") and k == 0 else None)
b += txt(410, 368, "FLOPs 는 곱-덧셈 수(논문의 정의). 파라미터는 합성곱 + BN(γ, β) + fc, 선택지 B. 50 층 이상은 보폭을 병목의 첫 1x1 에 둔 값이다", 11, fill=MUTED)
b += txt(410, 388, "보폭을 3x3 에 두면 ResNet-50 이 %.2f G 가 되어 논문의 3.8 에서 멀어진다 — 논문은 첫 1x1 에 둔 것으로 읽힌다 (내 계산)" % (counts[50][2] / 1e9), 11, fill=INK2)
b += txt(410, 408, "센 값과 논문 값의 차이는 −0.03 ~ +0.06 G 이고, 파라미터는 torchvision 의 다섯 모델과 한 자리까지 같다", 11, fill=MUTED)
svg("fig07_table1", W, H, b, "표 1 의 망 다섯 비교")


# ── 그림 8. 기본 블록 대 병목 블록 (논문 그림 5) ─────────────────────────────
basic64 = 2 * 9 * 64 * 64
bott256 = 256 * 64 + 9 * 64 * 64 + 64 * 256
basic256 = 2 * 9 * 256 * 256
proj256 = 256 * 256
print("  [8] 기본 블록(64-d) %s, 병목(256-d) %s, 기본 블록을 256-d 로 %s (%.1f 배), 병목에 사영 지름길 +%s → %.2f 배"
      % (fmt(basic64), fmt(bott256), fmt(basic256), basic256 / float(bott256), fmt(proj256), (bott256 + proj256) / float(bott256)))
W, H = 820, 400
b = defs()
b += txt(20, 30, "기본 블록 대 병목 블록 — 1x1 로 줄이고, 3x3 을 좁은 폭에서 하고, 1x1 로 되살린다 (논문 그림 5, 가중치 수는 내가 센 것)", 14, anchor="start", weight="bold")
def blk(b, x0, title, layers, total, col):
    b += txt(x0 + 120, 70, title, 13, weight="bold", fill=col)
    for k, (lab, w, n) in enumerate(layers):
        y = 90 + 56 * k
        b += box(x0 + 120 - w / 2, y, w, 36, fill=REV_SOFT, stroke=REV)
        b += txt(x0 + 120, y + 23, lab, 12)
        b += txt(x0 + 235, y + 23, fmt(n), 11, anchor="start", fill=INK2)
        if k < len(layers) - 1:
            b += line(x0 + 120, y + 38, x0 + 120, y + 54, INK2, 1.2, marker="ai")
    b += txt(x0 + 120, 90 + 56 * len(layers) + 12, "합계 %s" % fmt(total), 13, weight="bold", fill=col)
    return b
b = blk(b, 30, "기본 (ResNet-34, 64-d)", [("3x3, 64", 120, 9 * 64 * 64), ("3x3, 64", 120, 9 * 64 * 64)], basic64, S_PLAIN)
b = blk(b, 420, "병목 (ResNet-50 이상, 256-d)", [("1x1, 64", 90, 256 * 64), ("3x3, 64", 90, 9 * 64 * 64), ("1x1, 256", 200, 64 * 256)], bott256, S_RES)
b += box(30, 300, 760, 90, fill=NODE, stroke=LINE)
b += txt(50, 324, "그림 5 가 「비슷한 시간 복잡도」라 부르는 두 블록: %s 대 %s (%.1f%% 차이, 같은 56x56 위라 곱-덧셈도 같은 비율)" % (fmt(basic64), fmt(bott256), 100 * (basic64 - bott256) / float(basic64)), 12, anchor="start")
b += txt(50, 348, "256-d 입출력을 기본 블록으로 하면 %s 로 병목의 %.1f 배다 — 병목이 깊이를 싸게 만든다" % (fmt(basic256), basic256 / float(bott256)), 12, anchor="start")
b += txt(50, 372, "병목의 지름길을 사영(256x256 = %s)으로 바꾸면 %.2f 배 — 논문의 「시간과 크기가 두 배가 된다」와 맞는다" % (fmt(proj256), (bott256 + proj256) / float(bott256)), 12, anchor="start", fill=INK2)
svg("fig08_bottleneck", W, H, b, "기본 블록과 병목 블록 비교")


# ── 그림 9. ImageNet 학습 곡선의 끝 값 (논문 그림 4, 눈금 읽기 ±1) ────────────────
F4 = [("plain-18", 31.0, 31.2, S_PLAIN), ("plain-34", 32.5, 32.3, NO), ("ResNet-18", 30.5, 31.0, S_RES), ("ResNet-34", 24.7, 28.3, OK)]
W, H = 820, 340
b = defs()
b += txt(20, 30, "논문 그림 4 의 오른쪽 끝 (약 55만 반복) — 가는 선 = 학습 오차, 굵은 선 = 중앙 자르기 검증 오차 (눈금 읽기 ±1)", 14, anchor="start", weight="bold")
PX0, PX1 = 180, 760
def X(v):
    return PX0 + (v - 22) / 12.0 * (PX1 - PX0)
for v in range(22, 35, 2):
    b += line(X(v), 60, X(v), 270, LINE, 1)
    b += txt(X(v), 288, "%d" % v, 10, fill=MUTED)
for k, (n, tr, va, col) in enumerate(F4):
    y = 85 + 50 * k
    b += txt(PX0 - 14, y + 4, n, 12, anchor="end", weight="bold", fill=col)
    b += line(X(tr), y, X(va), y, LINE, 3)
    b += circ(X(tr), y, 5, BG, col, 2)
    b += circ(X(va), y, 6, col, col, 2)
b += txt(410, 310, "빈 점 = 학습, 찬 점 = 검증. 평범한 34 층은 학습 오차가 18 층보다 1.5 높다(퇴화). ResNet-34 는 학습이 18 층보다 5.8 낮다", 11, fill=INK2)
b += txt(410, 330, "학습 오차가 검증보다 높거나 비슷한 것은 학습 쪽에 데이터 늘리기가 걸려 있어서로 읽는다 (논문이 설명하지 않는다)", 11, fill=MUTED)
svg("fig09_imagenet_curves", W, H, b, "ImageNet 학습 곡선 끝 값")


# ── 그림 10. ImageNet 결과 (표 3 · 4 · 5) ──────────────────────────────────
T4 = [("VGG (v5)", 7.1, S_VGG), ("PReLU-net", 5.71, INK2), ("BN-inception", 5.81, INK2), ("ResNet-34 B", 5.71, S_RES),
      ("ResNet-34 C", 5.60, S_RES), ("ResNet-50", 5.25, S_RES), ("ResNet-101", 4.60, S_RES), ("ResNet-152", 4.49, S_RES)]
T5 = [("VGG (ILSVRC'14)", 7.32, S_VGG), ("GoogLeNet (ILSVRC'14)", 6.66, INK2), ("VGG (v5)", 6.8, S_VGG),
      ("PReLU-net", 4.94, INK2), ("BN-inception", 4.82, INK2), ("ResNet (ILSVRC'15)", 3.57, S_RES)]
W, H = 820, 420
b = defs()
b += txt(20, 30, "ImageNet top-5 오차 % — 왼쪽: 단일 모델 검증(표 4), 오른쪽: 앙상블 시험(표 5)", 15, anchor="start", weight="bold")
for p, (title, rows) in enumerate([("단일 모델 · 검증 (다중 크기)", T4), ("앙상블 · 시험 서버", T5)]):
    x0 = 20 + 395 * p
    b += box(x0, 50, 385, 330, fill="none", stroke=LINE)
    b += txt(x0 + 192, 72, title, 13, weight="bold")
    ax0, ax1 = x0 + 170, x0 + 365
    for k, (n, v, col) in enumerate(rows):
        y = 100 + 33 * k
        b += txt(ax0 - 8, y + 4, n, 11, anchor="end")
        wdt = v / 8.0 * (ax1 - ax0)
        b += '<rect x="%s" y="%s" width="%s" height="18" rx="3" fill="%s"/>' % (ax0, y - 9, wdt, col)
        b += txt(ax0 + wdt + 5, y + 4, "%.2f" % v, 11, anchor="start", weight="bold")
b += txt(410, 400, "152 층 단일 모델(4.49, 검증)이 앞선 앙상블(4.82, 시험)보다 낮다고 논문이 적는다 — 검증과 시험을 가로지른 비교다", 11, fill=INK2)
svg("fig10_imagenet_results", W, H, b, "ImageNet 결과 막대 그림")


# ── 그림 11. CIFAR-10 — 깊이에 따른 오차 (표 6, 그림 6) ───────────────────────────
T6 = [(20, 0.27, 8.75), (32, 0.46, 7.51), (44, 0.66, 7.17), (56, 0.85, 6.97), (110, 1.7, 6.43), (1202, 19.4, 7.93)]
F6P = [(20, 9.8, 1.2), (32, 10.1, 1.2), (44, 11.5, 3.3), (56, 13.2, 5.8)]      # 평범한 망 시험 / 학습, 그림 6 왼쪽 읽기 ±0.5
print("  [11] CIFAR-10 6n+2 파라미터: " + ", ".join("%d 층 %.3f M (표 %.2f M)" % (6 * n + 2, cifar(n) / 1e6, t)
      for n, t in ((3, 0.27), (5, 0.46), (7, 0.66), (9, 0.85), (18, 1.7), (200, 19.4))))
W, H = 820, 380
b = defs()
b += txt(20, 30, "CIFAR-10 시험 오차 % 와 깊이 — 잔차 망은 표 6 의 값, 평범한 망은 그림 6 의 끝 값(눈금 읽기 ±0.5)", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 90, 560, 320, 60
def lx(d):
    return PX0 + (math.log10(d) - math.log10(15)) / (math.log10(1500) - math.log10(15)) * (PX1 - PX0)
def ly(v):
    return PY0 - (v - 5) / 9.0 * (PY0 - PY1)
for v in (6, 8, 10, 12, 14):
    b += line(PX0, ly(v), PX1, ly(v), LINE, 1)
    b += txt(PX0 - 8, ly(v) + 4, "%d" % v, 10, anchor="end", fill=MUTED)
for d in (20, 56, 110, 1202):
    b += txt(lx(d), PY0 + 18, "%d" % d, 10, fill=MUTED)
b += txt((PX0 + PX1) / 2, PY0 + 38, "층 수 (로그 눈금)", 12, fill=INK2)
b += polyline([(lx(d), ly(e)) for d, _, e in T6], S_RES, 2.4)
b += polyline([(lx(d), ly(e)) for d, e, _ in F6P], S_PLAIN, 2.4)
for d, _, e in T6:
    b += circ(lx(d), ly(e), 4, S_RES, S_RES)
    b += txt(lx(d), ly(e) + 18, "%.2f" % e, 10, fill=S_RES)
for d, e, _ in F6P:
    b += circ(lx(d), ly(e), 4, S_PLAIN, S_PLAIN)
b += txt(lx(44), ly(12.6), "평범한 망", 12, fill=S_PLAIN, weight="bold")
b += txt(lx(300), ly(6.1), "잔차 망", 12, fill=S_RES, weight="bold")
b += box(585, 60, 215, 260, fill=NODE, stroke=LINE)
b += txt(598, 84, "표 6 (잔차 망)", 12, anchor="start", weight="bold")
for j, (d, p, e) in enumerate(T6):
    b += txt(598, 110 + 22 * j, "%4d 층  %5.2f M  %.2f%%" % (d, p, e), 11, anchor="start")
b += txt(598, 250, "110 층: 5 번 돌려 최고 6.43,", 11, anchor="start", fill=INK2)
b += txt(598, 268, "평균 6.61 ± 0.16", 11, anchor="start", fill=INK2)
b += txt(598, 292, "1202 층은 학습 < 0.1% 인데", 11, anchor="start", fill=NO)
b += txt(598, 310, "시험이 110 층보다 1.50 높다", 11, anchor="start", fill=NO)
svg("fig11_cifar", W, H, b, "CIFAR-10 깊이별 오차")


# ── 그림 12. 층 응답의 표준편차 (논문 그림 7, 눈금 읽기 ±0.1) ─────────────────────
F7 = [("plain-20", 1.85, S_PLAIN), ("ResNet-20", 1.55, S_RES), ("plain-56", 1.65, S_PLAIN), ("ResNet-56", 1.05, S_RES), ("ResNet-110", 0.92, OK)]
W, H = 820, 340
b = defs()
b += txt(20, 30, "층 응답 표준편차의 가운데 값 — 크기 순으로 줄 세운 그림 7 아래 판에서 가운데 순위의 값 (눈금 읽기 ±0.1)", 14, anchor="start", weight="bold")
PX0, PX1 = 160, 700
def X(v):
    return PX0 + v / 2.2 * (PX1 - PX0)
for v in (0, 0.5, 1.0, 1.5, 2.0):
    b += line(X(v), 60, X(v), 280, LINE, 1)
    b += txt(X(v), 298, "%.1f" % v, 10, fill=MUTED)
for k, (n, v, col) in enumerate(F7):
    y = 80 + 42 * k
    b += txt(PX0 - 10, y + 4, n, 12, anchor="end", weight="bold", fill=col)
    b += '<rect x="%s" y="%s" width="%s" height="20" rx="3" fill="%s"/>' % (PX0, y - 10, X(v) - PX0, col)
    b += txt(X(v) + 6, y + 4, "%.2f" % v, 11, anchor="start")
b += txt(410, 318, "응답 = 3x3 층의 출력, BN 뒤 · 비선형(ReLU/더하기) 앞. 잔차 망이 더 작고, 깊을수록 한 층이 신호를 덜 바꾼다(논문의 해석)", 11, fill=INK2)
b += txt(410, 336, "가운데 순위를 고른 것은 내 선택이다. 논문은 곡선만 보이고 요약 수를 내지 않는다", 11, fill=MUTED)
svg("fig12_layer_std", W, H, b, "층 응답 표준편차 비교")


# ── 그림 13. 검출 (표 7 · 8) ─────────────────────────────────────────────
T78 = [("VOC 07 test", 73.2, 76.4), ("VOC 12 test", 70.4, 73.8), ("COCO mAP@.5", 41.5, 48.4), ("COCO mAP@[.5,.95]", 21.2, 27.2)]
print("  [13] COCO mAP@[.5,.95] 상대 향상 %.1f%% (논문 28%%)" % (100 * (27.2 - 21.2) / 21.2))
W, H = 820, 340
b = defs()
b += txt(20, 30, "Faster R-CNN 의 바탕 망만 VGG-16 에서 ResNet-101 로 바꿨을 때 mAP % (표 7 · 8)", 15, anchor="start", weight="bold")
for k, (n, v, r) in enumerate(T78):
    x = 40 + 190 * k
    base = 270
    for j, (val, col) in enumerate(((v, S_VGG), (r, S_RES))):
        hgt = val / 80.0 * 190
        b += '<rect x="%s" y="%s" width="55" height="%s" rx="3" fill="%s"/>' % (x + 20 + 65 * j, base - hgt, hgt, col)
        b += txt(x + 47 + 65 * j, base - hgt - 6, "%.1f" % val, 11, weight="bold")
    b += txt(x + 80, base + 20, n, 12, weight="bold")
    b += txt(x + 80, base + 38, "+%.1f" % (r - v), 11, fill=OK)
b += line(30, 270, 790, 270, INK2, 1)
b += circ(560, 60, 6, S_VGG, S_VGG); b += txt(572, 64, "VGG-16", 11, anchor="start")
b += circ(650, 60, 6, S_RES, S_RES); b += txt(662, 64, "ResNet-101", 11, anchor="start")
b += txt(410, 330, "COCO 의 +6.0 은 21.2 의 %.1f%% — 논문의 「28%% 상대 향상」이다. 검출기 구현은 두 쪽이 같다고 논문이 적는다" % (100 * 6.0 / 21.2), 11, fill=MUTED)
svg("fig13_detection", W, H, b, "검출 결과 비교")


# ── 그림 14. VGG 와 ResNet ─────────────────────────────────────────────
W, H = 820, 450
b = defs()
b += txt(20, 30, "VGG-19 와 34 층 · 152 층 ResNet — 깊이는 늘고 계산은 줄었다", 15, anchor="start", weight="bold")
rows14 = [("가중치 층", "19", "34", "152"),
          ("곱-덧셈 (논문)", "19.6 G", "3.6 G", "11.3 G"),
          ("곱-덧셈 (내가 센 값)", "%.2f G" % (V19[1] / 1e9), "%.2f G" % (counts[34][1] / 1e9), "%.2f G" % (counts[152][1] / 1e9)),
          ("파라미터 (내가 센 값)", "%.1f M" % (V19[0] / 1e6), "%.1f M" % (counts[34][0] / 1e6), "%.1f M" % (counts[152][0] / 1e6)),
          ("fc 층", "4096-4096-1000", "평균 풀링 + 1000", "평균 풀링 + 1000"),
          ("줄이기", "최댓값 풀링 5 번", "보폭 2 합성곱", "보폭 2 합성곱"),
          ("정규화", "없다 (원 논문)", "BN, 합성곱마다", "BN, 합성곱마다"),
          ("지름길", "없다", "있다", "있다 (병목)")]
cw = [220, 180, 180, 180]
x0, y0 = 20, 55
b += box(x0, y0, sum(cw), 36, fill="#DDE3E0", stroke=LINE, rx=4)
for k, t in enumerate(["", "VGG-19", "ResNet-34", "ResNet-152"]):
    b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y0 + 23, t, 13, weight="bold", fill=[INK, S_VGG, S_RES, S_RES][k])
for r, row in enumerate(rows14):
    y = y0 + 36 + 38 * r
    b += box(x0, y, sum(cw), 38, fill=NODE if r % 2 == 0 else BG, stroke=LINE, rx=0)
    for k, t in enumerate(row):
        b += txt(x0 + sum(cw[:k]) + cw[k] / 2, y + 24, t, 12, weight="bold" if k == 0 else None)
b += txt(410, 418, "VGG-19 파라미터의 %.0f%% 가 fc 세 층에 있다 (내가 센 값). ResNet 은 fc 를 평균 풀링과 fc 하나로 바꿨다" % (100 * (25088 * 4096 + 4096 + 4096 * 4096 + 4096 + 4096 * 1000 + 1000) / V19[0]), 11, fill=INK2)
b += txt(410, 438, "34 층의 곱-덧셈이 VGG-19 의 18%% 라는 것은 논문의 문장이다. 내가 센 값으로는 %.1f%%" % (100 * counts[34][1] / V19[1]), 11, fill=MUTED)
svg("fig14_vgg_vs_resnet", W, H, b, "VGG 와 ResNet 비교 표")


# ── 그림 15. 단계와 공간 크기 — PatchCore 가 쓰는 자리 (내가 잇는 것) ─────────────
Pw, Mw, stw = resnet([3, 4, 6, 3], True, inner=2)
print("  [15] WideResNet-50-2 (병목 안쪽 폭 두 배) 파라미터 %s (torchvision 참고값 68,883,240), 곱-덧셈 %.2f G" % (fmt(Pw), Mw / 1e9))
for c, out, h, n, sp in stw:
    print("       단계 출력 %4d 채널 @ %2dx%-2d  블록 %d  파라미터 %s" % (out, h, h, n, fmt(sp)))
W, H = 820, 430
b = defs()
b += txt(20, 30, "224 입력에서 단계마다의 출력 — ResNet-50 과 WideResNet-50-2 (PatchCore 가 쓰는 자리는 내가 이은 것)", 15, anchor="start", weight="bold")
names = ["conv2_x (layer1)", "conv3_x (layer2)", "conv4_x (layer3)", "conv5_x (layer4)"]
for k, (c, out, h, n, sp) in enumerate(stw):
    x = 40 + 190 * k
    side = 30 + 1.9 * h
    hl = k in (1, 2)
    b += box(x + 75 - side / 2, 175 - side / 2, side, side, fill=CODE_SOFT if hl else REV_SOFT, stroke=CODE if hl else REV, sw=2 if hl else 1.2, rx=3)
    b += txt(x + 75, 62, names[k], 12, weight="bold")
    b += txt(x + 75, 262, "%d x %d" % (h, h), 13, weight="bold")
    b += txt(x + 75, 282, "출력 %s 채널" % fmt(out), 11)
    b += txt(x + 75, 300, "병목 안쪽 %d → %d (WRN)" % (c, 2 * c), 11, fill=INK2)
    b += txt(x + 75, 318, "보폭 누적 %d" % (224 // h), 11, fill=MUTED)
b += box(30, 332, 760, 88, fill=NODE, stroke=LINE)
b += txt(50, 354, "PatchCore 는 layer2 (28x28, 512 채널) 와 layer3 (14x14, 1,024 채널) 의 특징을 이어 붙여 위치마다 조각 특징을 만든다", 12, anchor="start")
b += txt(50, 376, "이어 붙인 채널은 512 + 1,024 = 1,536. 조각 위치는 layer2 격자를 따라 224 입력이면 28 x 28 = 784, 576 입력이면 72 x 72 = 5,184", 12, anchor="start")
b += txt(50, 398, "이 연결은 ResNet 논문에 없다 — PatchCore 쪽 설정을 내가 옆에 놓은 것이다", 12, anchor="start", fill=INK2)
svg("fig15_stages_patchcore", W, H, b, "단계별 출력 크기와 PatchCore 연결")


# ── 그림 16. 계보 ──────────────────────────────────────────────────
W, H = 820, 360
b = defs()
b += txt(20, 30, "계보 — 「깊으면 안 배워진다」에 대한 답들", 15, anchor="start", weight="bold")
chainL = [("역전파 1986", "층마다 기울기가 준다"), ("DBN · AE 2006", "사전학습으로 출발점"), ("AlexNet 2012", "ReLU 로 8 층"),
          ("VGG 2014", "3x3 으로 19 층"), ("BN 2015", "층 입력을 정규화"), ("ResNet 2015", "항등 지름길로 152 층")]
for k, (t, d) in enumerate(chainL):
    x = 20 + 132 * k
    last = k == 5
    b += box(x, 60, 120, 64, fill=CODE_SOFT if last else NODE, stroke=CODE if last else INK2, sw=1.6 if last else 1.2)
    b += txt(x + 60, 86, t, 12, weight="bold", fill=CODE if last else INK)
    b += txt(x + 60, 106, d, 10, fill=INK2)
    if k < 5:
        b += line(x + 121, 92, x + 131, 92, INK2, 1.3, marker="ai")
b += box(20, 150, 780, 190, fill=NODE, stroke=LINE)
b += txt(40, 176, "무엇이 달라졌나 — 문제가 옮겨 갔다", 13, anchor="start", weight="bold", fill=REV)
lines16 = ["역전파 · DBN · AE 의 문제는 기울기가 아래층까지 안 내려오는 것(사라지는 기울기)이었다",
           "ResNet 은 그 문제가 정규화된 초기화와 BN 으로 「대부분 풀렸다」고 적고 시작한다 — 그 위에서 드러난 것이 퇴화다",
           "퇴화: 기울기는 건강한데(논문이 확인했다고 적는다) 깊은 평범한 망의 학습 오차가 더 높다",
           "답은 풀이기를 바꾸는 것이 아니라 문제를 바꿔 적는 것 — H(x) 대신 F(x) = H(x) − x",
           "PatchCore 같은 이상 탐지는 ImageNet 으로 배운 이 망을 얼려 특징 추출기로 쓴다 (논문 밖, 내가 잇는 자리)"]
for j, l in enumerate(lines16):
    b += txt(40, 204 + 26 * j, l, 12, anchor="start", fill=INK if j < 4 else INK2)
svg("fig16_lineage", W, H, b, "깊이 문제의 계보")

print("끝.")
