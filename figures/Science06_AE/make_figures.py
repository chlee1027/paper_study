# -*- coding: utf-8 -*-
"""오토인코더 노트(Science 2006)의 그림 열넷을 만든다.

색과 글꼴은 앞선 노트들(퍼셉트론 · 역전파 · DBN · LeNet)의 그림과 맞췄다 — 저장소의 노트들이
한 벌로 읽히게 하려는 것이다. 막대그래프 두 장(그림 10 · 12)만 계열 색 셋을 따로 쓴다.
그 셋은 배경색 위에서 색각 이상 분리도를 검사해 통과한 조합이다.
바깥 데이터를 읽지 않으므로 어디서나 돈다.

  python make_figures.py

그림 1 의 주성분 재구성 오차, 그림 3 의 기울기 곱, 그림 9 의 파라미터 수, 그림 10 의 배수와
픽셀당 오차, 그림 13 의 층 폭 판정은 이 파일이 직접 계산한다. 계산한 값은 돌릴 때 화면에도 찍는다.
"""
import io, os, math

OUT = os.path.dirname(os.path.abspath(__file__))

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
OK        = "#1E8449"   # 초록 — 된다
NO        = "#C0392B"   # 빨강 — 안 된다
# 막대그래프 계열 색 — 오토인코더 · 주성분 분석 · 로지스틱 주성분 분석. 이 순서로 고정한다.
S_AE      = "#EB6834"
S_PCA     = "#2A78D6"
S_LPCA    = "#1BAF7A"
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
            + arrow("an", NO) + "</defs>")


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


def bar(x, y0, w, h, color):
    """바닥(y0)에 붙은 막대. 위쪽 두 모서리만 4px 둥글린다."""
    r = min(4, h / 2.0, w / 2.0)
    y = y0 - h
    d = "M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s L%s,%s z" % (
        x, y0, x, y + r, x, y, x + r, y, x + w - r, y, x + w, y, x + w, y + r, x + w, y0)
    return '<path d="%s" fill="%s"/>' % (d, color)


def fmt(n):
    return "{:,}".format(n)


print("그림을 만든다 ->", OUT)


# ── 그림 1. 주성분 분석은 직선, 데이터는 곡선 ───────────────────────────────
# 반원 위의 점 15 개. 주성분 하나로 재구성하면 얼마가 남는지 직접 계산한다.
N1 = 15
pts = [(math.cos(math.pi * k / (N1 - 1)), math.sin(math.pi * k / (N1 - 1))) for k in range(N1)]
mx = sum(p[0] for p in pts) / N1
my = sum(p[1] for p in pts) / N1
sxx = sum((p[0] - mx) ** 2 for p in pts) / N1
syy = sum((p[1] - my) ** 2 for p in pts) / N1
sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / N1
th = 0.5 * math.atan2(2 * sxy, sxx - syy)              # 가장 큰 분산 방향
ux, uy = math.cos(th), math.sin(th)
proj = []
err = 0.0
for p in pts:
    t = (p[0] - mx) * ux + (p[1] - my) * uy
    q = (mx + t * ux, my + t * uy)
    proj.append(q)
    err += (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
err /= N1
tot = sxx + syy
print("  [1] 반원 15 점: 주성분 1 개 재구성 제곱 오차 평균 %.4f (전체 분산 %.4f 의 %.1f%%)"
      % (err, tot, 100 * err / tot))

W, H = 820, 360
b = defs()
b += txt(20, 30, "한 숫자로 줄이기 — 직선 위 좌표(주성분 분석) 대 곡선 위 좌표(비선형)", 15, anchor="start", weight="bold")

def P(p, ox, oy, s=150):
    return ox + p[0] * s, oy - p[1] * s

# 왼쪽: 주성분
ox, oy = 205, 250
b += box(20, 50, 380, 285, fill="none", stroke=LINE)
b += txt(210, 74, "주성분 분석: 가장 퍼진 직선 하나에 떨어뜨린다", 13, weight="bold", fill=FWD)
a0 = P((mx - 1.2 * ux, my - 1.2 * uy), ox, oy); a1 = P((mx + 1.2 * ux, my + 1.2 * uy), ox, oy)
b += line(a0[0], a0[1], a1[0], a1[1], FWD, 2)
for p, q in zip(pts, proj):
    x0, y0 = P(p, ox, oy); x1, y1 = P(q, ox, oy)
    b += line(x0, y0, x1, y1, NO, 1, dash="3 2")
    b += circ(x1, y1, 3.5, FWD, FWD)
    b += circ(x0, y0, 4.5, NODE, INK)
b += txt(210, 305, "빨간 점선 = 버려진 몫. 평균 제곱 오차 %.3f" % err, 12, fill=INK2)
b += txt(210, 323, "(전체 분산 %.3f 의 %.0f%% 가 남는다)" % (tot, 100 * err / tot), 12, fill=INK2)

# 오른쪽: 곡선 좌표
ox, oy = 610, 250
b += box(420, 50, 380, 285, fill="none", stroke=LINE)
b += txt(610, 74, "비선형: 곡선을 따라 잰 각도 하나", 13, weight="bold", fill=REV)
arc = "M%s,%s A150,150 0 0 0 %s,%s" % (ox + 150, oy, ox - 150, oy)
b += path(arc, REV, sw=2)
for k, p in enumerate(pts):
    x0, y0 = P(p, ox, oy)
    b += circ(x0, y0, 4.5, NODE, INK)
    if k in (0, 7, 14):
        lab = ["0", "π/2", "π"][[0, 7, 14].index(k)]
        b += txt(x0 + (14 if k == 0 else (-14 if k == 14 else 0)), y0 + (18 if k != 7 else -12), lab, 11, fill=REV)
b += txt(610, 305, "점마다 각도 하나면 원래 자리로 정확히 돌아간다", 12, fill=INK2)
b += txt(610, 323, "재구성 오차 0 — 다만 이 곡선을 알아야 한다", 12, fill=INK2)
svg("fig01_pca_line_vs_curve", W, H, b, "주성분 분석의 직선 사영과 곡선 좌표 비교")


# ── 그림 2. 오토인코더의 모양 ────────────────────────────────────────────
W, H = 820, 355
b = defs()
b += txt(20, 30, "오토인코더 — 입력을 좁은 코드로 누르고 다시 펴서, 원래 입력과 맞춘다", 15, anchor="start", weight="bold")
sizes = [784, 1000, 500, 250, 30, 250, 500, 1000, 784]
xs = [60 + i * 88 for i in range(9)]
cy = 170
def hgt(n):
    return 30 + 150 * math.sqrt(n / 1000.0)
for i, (x, n) in enumerate(zip(xs, sizes)):
    h = hgt(n)
    col = FWD_SOFT if i < 4 else (REV_SOFT if i > 4 else "#FFF3C4")
    stroke = FWD if i < 4 else (REV if i > 4 else "#9A7B00")
    b += box(x - 18, cy - h / 2, 36, h, fill=col, stroke=stroke)
    b += txt(x, cy + h / 2 + 18, fmt(n), 12, weight="bold" if i == 4 else None)
    if i < 8:
        b += line(x + 20, cy, xs[i + 1] - 22, cy, FWD if i < 4 else REV, 1.6, marker="af" if i < 4 else "ar")
b += txt((xs[0] + xs[3]) / 2, 62, "부호기 (encoder)", 13, weight="bold", fill=FWD)
b += txt((xs[5] + xs[8]) / 2, 62, "복호기 (decoder)", 13, weight="bold", fill=REV)
b += txt(xs[4], 62, "코드", 13, weight="bold", fill="#9A7B00")
b += txt(xs[0], 290, "입력 x", 12, fill=INK2)
b += txt(xs[8], 290, "재구성 x̂", 12, fill=INK2)
b += path("M%s,300 Q%s,322 %s,300" % (xs[0], (xs[0] + xs[8]) / 2, xs[8]), NO, sw=1.4, dash="4 3")
b += txt((xs[0] + xs[8]) / 2, 342, "학습 목표: x 와 x̂ 의 차이(재구성 오차)를 줄인다 — 라벨이 필요 없다", 12, fill=NO)
svg("fig02_autoencoder", W, H, b, "784-1000-500-250-30 오토인코더와 대칭 복호기")


# ── 그림 3. 초기 가중치의 딜레마 ─────────────────────────────────────────
# 곡선 오토인코더(784-400-200-100-50-25-6 + 대칭)에서 맨 아래 가중치까지 기울기가 지나는
# 로지스틱 층 수를 센다. 출력층은 교차 엔트로피와 로지스틱이 만나 σ' 이 약분되고,
# 코드층 6 은 선형이라 곱해지는 것이 없다. 남는 것은 은닉 로지스틱 층 열 개다.
enc_hidden = [400, 200, 100, 50, 25]
n_logistic = 2 * len(enc_hidden)
bound = 0.25 ** n_logistic
print("  [3] 곡선 오토인코더: 맨 아래 가중치까지 로지스틱 층 %d 개, σ' 최댓값 곱 %.3g" % (n_logistic, bound))

W, H = 820, 330
b = defs()
b += txt(20, 30, "처음 가중치를 어디에 두는가 — 세 경우", 15, anchor="start", weight="bold")
cols = [(20, "큰 초기 가중치", NO, ["나쁜 국소 최소에 갇힌다", "", "", "논문: 대개(typically) 나쁜", "국소 최소를 찾는다"]),
        (290, "작은 초기 가중치", NO, ["앞쪽 층의 기울기가 아주 작다", "은닉층 여럿이면 학습이 안 된다", "", "곡선 망에서 로지스틱 층 %d 개:" % n_logistic,
                                     "0.25^%d = %.2g (가장 잘 받을 때)" % (n_logistic, bound)]),
        (560, "좋은 해에 가까운 초기 가중치", OK, ["경사 하강이 잘 된다", "", "그 자리를 찾는 것이", "이 논문의 사전학습이다", "(한 층씩 배우는 전혀 다른 알고리즘)"])]
for x, title, c, lines in cols:
    b += box(x, 50, 240, 250, fill=NODE, stroke=c, sw=1.6)
    b += txt(x + 120, 76, title, 14, weight="bold", fill=c)
    for k, s in enumerate(lines):
        b += txt(x + 120, 110 + 22 * k, s, 12, fill=INK if k < 2 else INK2)
    # 작은 손실 곡면 그림
    yb = 270
    if c == OK:
        b += path("M%s,%s Q%s,%s %s,%s" % (x + 40, yb - 40, x + 120, yb + 30, x + 200, yb - 40), INK2)
        b += circ(x + 100, yb - 8, 5, OK, OK)
    else:
        b += path("M%s,%s C%s,%s %s,%s %s,%s S%s,%s %s,%s" % (x + 30, yb - 40, x + 60, yb + 10, x + 90, yb - 30,
                   x + 120, yb - 10, x + 170, yb + 25, x + 210, yb - 40), INK2)
        b += circ(x + 83 if x == 20 else x + 185, yb - 18 if x == 20 else yb - 28, 5, NO, NO)
b += txt(410, 322, "0.25 는 로지스틱 기울기 σ'(z) 의 최댓값. 이 곱은 내가 층 수를 세어 붙인 상한이고 논문의 계산이 아니다", 11, fill=MUTED)
svg("fig03_init_dilemma", W, H, b, "큰 초기 가중치, 작은 초기 가중치, 좋은 초기 가중치")


# ── 그림 4. RBM ───────────────────────────────────────────────────────
W, H = 820, 330
b = defs()
b += txt(20, 30, "제한 볼츠만 기계(RBM) — 두 층, 층 사이만 잇고 층 안은 잇지 않는다", 15, anchor="start", weight="bold")
vx = [120 + 70 * i for i in range(7)]
hx = [155 + 70 * i for i in range(6)]
for i, x in enumerate(vx):
    for j, y in enumerate(hx):
        b += line(x, 230, y, 110, LINE, 1)
b += line(vx[2], 230, hx[3], 110, REV, 2.2)
b += txt((vx[2] + hx[3]) / 2 + 22, 176, "w(i,j)", 12, fill=REV, weight="bold")
for x in vx:
    b += circ(x, 230, 16, FWD_SOFT, FWD)
for y in hx:
    b += circ(y, 110, 16, REV_SOFT, REV)
b += txt(80, 115, "숨은 h", 13, anchor="end", fill=REV, weight="bold")
b += txt(80, 235, "보이는 v", 13, anchor="end", fill=FWD, weight="bold")
b += txt(80, 252, "(픽셀)", 11, anchor="end", fill=INK2)
b += txt(80, 132, "(특징 검출기)", 11, anchor="end", fill=INK2)
b += txt(345, 285, "층 안 연결이 없으므로 v 를 알면 h 의 유닛들이 서로 독립이다(반대도 같다)", 12, fill=INK2)
b += box(610, 70, 195, 205, fill=NODE, stroke=LINE)
b += txt(707, 94, "식 (1) 에너지", 13, weight="bold")
b += txt(707, 120, "E(v,h) = − Σ b(i) v(i)", 12)
b += txt(707, 140, "− Σ b(j) h(j)", 12)
b += txt(707, 160, "− Σ v(i) h(j) w(i,j)", 12)
b += txt(707, 190, "에너지가 낮은 (v,h) 가", 12, fill=INK2)
b += txt(707, 208, "높은 확률을 받는다", 12, fill=INK2)
b += txt(707, 238, "p(h(j)=1 | v)", 12, fill=REV)
b += txt(707, 256, "= σ(b(j) + Σ v(i) w(i,j))", 12, fill=REV)
svg("fig04_rbm", W, H, b, "RBM 의 두 층과 에너지 식")


# ── 그림 5. 한 걸음 대조 발산 ─────────────────────────────────────────────
W, H = 820, 300
b = defs()
b += txt(20, 30, "식 (2) 의 한 번 갱신 — 데이터에서 한 번, 지어낸 것(confabulation)에서 한 번", 15, anchor="start", weight="bold")
steps = [(90, 210, "v", "학습 이미지", FWD_SOFT, FWD), (270, 100, "h", "σ(b(j)+Σv w) 로 0/1 뽑기", REV_SOFT, REV),
         (450, 210, "v′", "σ(b(i)+Σh w) 로 지어낸 이미지", FWD_SOFT, FWD), (630, 100, "h′", "다시 한 번 올린다", REV_SOFT, REV)]
for k, (x, y, lab, desc, f, s) in enumerate(steps):
    b += box(x - 55, y - 24, 110, 48, fill=f, stroke=s, sw=1.5)
    b += txt(x, y + 6, lab, 18, weight="bold", fill=s)
    b += txt(x, y + 44 if y > 150 else y - 34, desc, 11, fill=INK2)
    if k < 3:
        nx, ny = steps[k + 1][0], steps[k + 1][1]
        b += line(x + 55, y - (12 if y > 150 else -12), nx - 58, ny + (12 if y > 150 else -12), INK2, 1.5, marker="ai")
b += path("M90,160 Q180,150 270,130", OK, sw=0, fill="none")
b += box(140, 150, 150, 26, fill="#DDEFE3", stroke=OK)
b += txt(215, 168, "⟨v h⟩ data", 12, fill=OK, weight="bold")
b += box(500, 150, 150, 26, fill="#F6DAD6", stroke=NO)
b += txt(575, 168, "⟨v h⟩ recon", 12, fill=NO, weight="bold")
b += txt(410, 282, "Δw(i,j) = ε ( ⟨v(i) h(j)⟩data − ⟨v(i) h(j)⟩recon ) — 데이터의 에너지를 낮추고 지어낸 것의 에너지를 올린다", 12, fill=INK)
svg("fig05_cd1", W, H, b, "대조 발산 한 걸음")


# ── 그림 6. 사전학습 — RBM 쌓기 ──────────────────────────────────────────
W, H = 820, 380
b = defs()
b += txt(20, 30, "사전학습 — RBM 넷을 아래에서부터 하나씩 배운다 (논문 그림 1 의 얼굴 망)", 15, anchor="start", weight="bold")
rbms = [(625, 2000, "W1", "RBM 1"), (2000, 1000, "W2", "RBM 2"), (1000, 500, "W3", "RBM 3"), (500, 30, "W4", "RBM 4 (맨 위)")]
for k, (lo, hi, w, name) in enumerate(rbms):
    x = 40 + 195 * k
    b += box(x, 60, 170, 250, fill="none", stroke=LINE, dash="4 3")
    b += txt(x + 85, 82, name, 13, weight="bold")
    b += box(x + 25, 250, 120, 30, fill=FWD_SOFT, stroke=FWD)
    b += txt(x + 85, 270, fmt(lo), 13, weight="bold", fill=FWD)
    b += box(x + 25, 120, 120, 30, fill=REV_SOFT, stroke=REV)
    b += txt(x + 85, 140, fmt(hi), 13, weight="bold", fill=REV)
    b += line(x + 85, 245, x + 85, 156, INK2, 1.5)
    b += txt(x + 97, 205, w, 13, anchor="start", weight="bold")
    b += txt(x + 85, 300, "보이는 층" if k else "보이는 층 = 픽셀", 11, fill=INK2)
    b += txt(x + 85, 112, "숨은 층", 11, fill=INK2)
    if k < 3:
        b += path("M%s,135 C%s,135 %s,265 %s,265" % (x + 147, x + 175, x + 190, x + 218), OK, sw=1.6, marker="ao")
b += txt(410, 338, "초록 화살표: 아래 RBM 을 다 배우고 얼린 뒤, 데이터를 넣어 얻은 숨은 층 활성을 다음 RBM 의 「데이터」로 쓴다", 12, fill=OK)
b += txt(410, 360, "RBM 하나에는 숨은 층이 하나뿐이다. 깊이는 쌓아서 얻는다", 12, fill=INK2)
svg("fig06_pretrain_stack", W, H, b, "RBM 넷을 쌓는 사전학습")


# ── 그림 7. 펼치기와 미세조정 ─────────────────────────────────────────────
W, H = 820, 420
b = defs()
b += txt(20, 30, "펼치기(unrolling)와 미세조정(fine-tuning)", 15, anchor="start", weight="bold")
layers = [625, 2000, 1000, 500, 30, 500, 1000, 2000, 625]
wl = ["W1", "W2", "W3", "W4", "W4ᵀ", "W3ᵀ", "W2ᵀ", "W1ᵀ"]
for panel, x0 in ((0, 60), (1, 460)):
    b += txt(x0 + 150, 62, "펼친 직후 — 부호기와 복호기가 같은 가중치" if panel == 0 else "미세조정 뒤 — 여덟 벌이 따로 움직인다", 13,
             weight="bold", fill=FWD if panel == 0 else REV)
    for i, n in enumerate(layers):
        y = 380 - 36 * i
        wbox = 60 + 170 * math.sqrt(n / 2000.0)
        col = FWD_SOFT if i < 4 else (REV_SOFT if i > 4 else "#FFF3C4")
        b += box(x0 + 150 - wbox / 2, y - 12, wbox, 22, fill=col, stroke=INK2, sw=1)
        b += txt(x0 + 150, y + 4, fmt(n) + (" 코드" if i == 4 else ""), 11, weight="bold" if i == 4 else None)
        if i < 8:
            lab = wl[i] if panel == 0 else wl[i] + " + ε%d" % (i + 1)
            b += txt(x0 + 150 + wbox / 2 + 8 if i != 3 else x0 + 245, y - 16, lab, 11, anchor="start", fill=REV if panel else INK2)
b += line(385, 220, 440, 220, INK2, 1.6, marker="ai")
b += txt(412, 208, "역전파", 11, fill=INK2)
svg("fig07_unroll_finetune", W, H, b, "펼친 오토인코더와 미세조정")


# ── 그림 8. 유닛의 종류 — 단계마다 다르다 ───────────────────────────────────
W, H = 820, 335
b = defs()
b += txt(20, 30, "어느 유닛이 어떤 값을 갖는가 — 논문이 한 문단에 몰아 적은 것을 풀어 놓는다", 15, anchor="start", weight="bold")
rows = [("", "사전학습 (RBM)", "미세조정 (펼친 망)"),
        ("맨 아래 보이는 층", "[0,1] 실수값(로지스틱). 얼굴은 선형 + 가우스 잡음", "입력 그대로"),
        ("중간 층 (RBM 의 보이는 쪽)", "아래 RBM 숨은 유닛의 활성 확률(실수)", "—"),
        ("중간 층 (RBM 의 숨은 쪽)", "확률적 이진값 0/1", "결정적 실수 확률 σ(·)"),
        ("맨 위 RBM 의 숨은 층 = 코드", "분산 1 가우스, 평균은 입력으로 정해짐", "선형 유닛"),
        ("출력 층", "—", "로지스틱 + 교차 엔트로피 (곡선·MNIST)")]
cw = [220, 300, 260]
for r, row in enumerate(rows):
    x = 20
    y = 50 + 42 * r
    for c, cell in enumerate(row):
        f = BG if r == 0 else (NODE if c else "#E3E8E5")
        b += box(x, y, cw[c], 38, fill=f, stroke=LINE, rx=0)
        b += txt(x + cw[c] / 2, y + 24, cell, 12, weight="bold" if r == 0 or c == 0 else None,
                 fill=(REV if (c == 2 and r == 3) else INK))
        x += cw[c]
b += txt(410, 322, "주황 칸: 사전학습의 확률적 이진 상태가 미세조정에서 결정적 실수로 바뀐다", 12, fill=REV)
svg("fig08_unit_types", W, H, b, "단계별 유닛 종류 표")


# ── 그림 9. 망 다섯과 파라미터 수 ─────────────────────────────────────────
def n_params(sizes, symmetric):
    """가중치 수와 치우침 수를 센다. symmetric 이면 거울상 복호기를 붙이고, 미세조정 뒤처럼 따로 센다."""
    full = sizes + sizes[-2::-1] if symmetric else sizes
    w = sum(a * c for a, c in zip(full[:-1], full[1:]))
    bb = sum(full[1:])
    return w, bb, full

nets = [("곡선 (6 차원 코드)", [784, 400, 200, 100, 50, 25, 6], True),
        ("MNIST (30 차원 코드)", [784, 1000, 500, 250, 30], True),
        ("MNIST 시각화 (2 차원)", [784, 1000, 500, 250, 2], True),
        ("얼굴 조각 (30 차원)", [625, 2000, 1000, 500, 30], True),
        ("문서 (10 차원)", [2000, 500, 250, 125, 10], True),
        ("분류 (라벨 10)", [784, 500, 500, 2000, 10], False)]
print("  [9] 파라미터 수 (가중치 + 치우침, 복호기 따로):")
W, H = 820, 420
b = defs()
b += txt(20, 30, "논문의 망 여섯 — 층 폭과 파라미터 수(이 파일이 센 값)", 15, anchor="start", weight="bold")
for k, (name, s, sym) in enumerate(nets):
    w, bb, full = n_params(s, sym)
    pca = s[0] * s[-1] + s[0] if sym else None
    print("      %-18s %s  가중치 %s + 치우침 %s = %s%s" % (
        name, "-".join(map(str, s)), fmt(w), fmt(bb), fmt(w + bb),
        ("   같은 차원 주성분 %s (%.0f 배)" % (fmt(pca), (w + bb) / float(pca))) if pca else ""))
    y = 60 + 58 * k
    b += txt(20, y + 12, name, 12, anchor="start", weight="bold")
    b += txt(20, y + 30, "-".join(map(str, s)) + (" + 거울상" if sym else ""), 11, anchor="start", fill=INK2)
    x = 245
    for i, n in enumerate(full):
        hh = 6 + 38 * math.sqrt(n / 2000.0)
        col = FWD if (not sym or i < len(s) - 1) else (REV if i > len(s) - 1 else "#9A7B00")
        b += '<rect x="%s" y="%s" width="9" height="%s" rx="2" fill="%s"/>' % (x, y + 20 - hh / 2, hh, col)
        x += 13
    b += txt(800, y + 12, fmt(w + bb), 13, anchor="end", weight="bold")
    if pca:
        b += txt(800, y + 30, "같은 차원 주성분 %s 의 %.0f 배" % (fmt(pca), (w + bb) / float(pca)), 11, anchor="end", fill=INK2)
b += txt(410, 408, "막대 높이는 층 폭의 제곱근. 파랑 = 부호기, 노랑 = 코드, 주황 = 복호기. 주성분 수 = 입력 차원 x 코드 차원 + 평균", 11, fill=MUTED)
svg("fig09_architectures", W, H, b, "여섯 망의 층 폭과 파라미터 수")


# ── 그림 10. 재구성 오차 — 그림 2 의 캡션 숫자 ─────────────────────────────
panels = [("곡선", 784, [("오토인코더 6", 1.44, S_AE), ("로지스틱 주성분 6", 7.64, S_LPCA),
                                        ("로지스틱 주성분 18", 2.45, S_LPCA), ("주성분 18", 5.90, S_PCA)]),
          ("MNIST", 784, [("오토인코더 30", 3.00, S_AE), ("로지스틱 주성분 30", 8.01, S_LPCA),
                                          ("주성분 30", 13.87, S_PCA)]),
          ("얼굴 조각", 625, [("오토인코더 30", 126.0, S_AE), ("주성분 30", 135.0, S_PCA)])]
print("  [10] 이미지당 제곱 오차 -> 픽셀당, 오토인코더 대비 배수:")
W, H = 820, 380
b = defs()
b += txt(20, 30, "이미지 한 장당 평균 제곱 오차 — 논문 그림 2 캡션의 숫자 (낮을수록 좋다, 판마다 세로 눈금이 다르다)", 14, anchor="start", weight="bold")
for p, (title, npx, items) in enumerate(panels):
    x0 = 30 + 265 * p
    b += txt(x0 + 118, 64, title, 13, weight="bold")
    base = 290
    top = max(v for _, v, _ in items)
    ae = items[0][1]
    bw = 34 if len(items) == 4 else 44
    gap = (236 - bw * len(items)) / (len(items) + 1)
    b += line(x0, base, x0 + 236, base, INK2, 1)
    for i, (lab, v, col) in enumerate(items):
        hh = 190 * v / top
        x = x0 + gap + i * (bw + gap)
        b += bar(x, base, bw, hh, col)
        b += txt(x + bw / 2, base - hh - 8, ("%.2f" % v) if v < 100 else "%d" % v, 12, weight="bold")
        words = lab.rsplit(" ", 1)
        b += txt(x + bw / 2, base + 16, words[0] if len(words[0]) < 7 else words[0][:-3], 10, fill=INK2)
        b += txt(x + bw / 2, base + 29, (words[0][-3:] + " " if len(words[0]) >= 7 else "") + words[1], 10, fill=INK2)
        if i:
            b += txt(x + bw / 2, base + 45, "%.2f 배" % (v / ae), 10, fill=MUTED)
        print("      %-22s %-18s %7.2f  픽셀당 %.5f  (%.2f 배)" % (title, lab, v, v / npx, v / ae))
b += txt(410, 366, "배수 = 그 방법의 오차 / 같은 판 오토인코더의 오차. 얼굴 조각은 입력이 선형 유닛이라 값의 크기를 다른 두 판과 견주지 않는다", 11, fill=MUTED)
svg("fig10_recon_errors", W, H, b, "세 데이터셋의 재구성 오차 막대그래프")


# ── 그림 11. 문서 검색 ───────────────────────────────────────────────────
n_docs = 804414
print("  [11] 문서 %s 편의 절반 = %s (논문의 질의 수 402,207 과 같은가: %s)" % (fmt(n_docs), fmt(n_docs // 2), n_docs // 2 == 402207))
W, H = 820, 320
b = defs()
b += txt(20, 30, "문서 검색 — 기사 하나를 10 개의 수로 줄이고, 코드끼리의 코사인으로 찾는다", 15, anchor="start", weight="bold")
chain = [("기사 한 편", "뉴스 기사 804,414 편", FWD_SOFT, FWD),
         ("단어 2000 개 확률", "가장 흔한 어간 2000 개의\n기사 안 비율", FWD_SOFT, FWD),
         ("10 차원 코드", "2000-500-250-125-10\n오토인코더", "#FFF3C4", "#9A7B00"),
         ("코사인 유사도", "질의 코드와 각도가\n가까운 순서로 꺼낸다", REV_SOFT, REV)]
for k, (t, d, f, s) in enumerate(chain):
    x = 30 + 200 * k
    b += box(x, 70, 160, 52, fill=f, stroke=s, sw=1.5)
    b += txt(x + 80, 101, t, 13, weight="bold", fill=s)
    for j, dl in enumerate(d.split("\n")):
        b += txt(x + 80, 145 + 16 * j, dl, 11, fill=INK2)
    if k < 3:
        b += line(x + 162, 96, x + 196, 96, INK2, 1.5, marker="ai")
b += box(30, 200, 760, 100, fill=NODE, stroke=LINE)
b += txt(50, 224, "학습: 절반(402,207 편). 미세조정 손실은 여러 부류 교차 엔트로피 −Σ p(i) log p̂(i)", 12, anchor="start")
b += txt(50, 246, "평가: 나머지 절반의 기사 하나하나를 질의로 삼아 같은 부류 기사가 몇 % 나오는지 — 질의 402,207 개의 평균", 12, anchor="start")
b += txt(50, 268, "비교: 잠재 의미 분석(LSA, 주성분 분석과 같은 뿌리) 10 차원 · 50 차원", 12, anchor="start")
b += txt(50, 290, "804,414 / 2 = %s — 질의 수와 정확히 맞는다(이 파일이 나눠 본 값)" % fmt(n_docs // 2), 12, anchor="start", fill=OK)
svg("fig11_retrieval", W, H, b, "문서 검색 절차")


# ── 그림 12. 분류 오차 ──────────────────────────────────────────────────
W, H = 820, 330
b = defs()
b += txt(20, 30, "MNIST 분류 시험 오차 (%) — 논문이 적은 셋과, 같은 해 DBN 논문의 값 하나", 15, anchor="start", weight="bold")
items = [("무작위 초기화 역전파", 1.6, S_PCA, "논문이 인용한 최고 보고값"),
         ("서포트 벡터 머신", 1.4, S_LPCA, "논문이 인용한 최고 보고값"),
         ("사전학습 + 역전파", 1.2, S_AE, "784-500-500-2000-10, 이 논문"),
         ("DBN 위-아래 미세조정", 1.25, MUTED, "같은 해 다른 논문(참고로만)")]
base = 270
for i, (lab, v, col, note) in enumerate(items):
    x = 70 + 180 * i
    hh = 180 * v / 1.6
    b += bar(x, base, 70, hh, col)
    b += txt(x + 35, base - hh - 8, "%.2f" % v if v == 1.25 else "%.1f" % v, 13, weight="bold")
    b += txt(x + 35, base + 18, lab, 11, fill=INK)
    b += txt(x + 35, base + 34, note, 10, fill=MUTED)
b += line(50, base, 790, base, INK2, 1)
b += txt(790, 60, "논문에 seed 수 · 변동 폭이 없다 — 1.2 와 1.25 의 순서를 매기지 않는다", 11, anchor="end", fill=MUTED)
svg("fig12_classification", W, H, b, "MNIST 분류 오차 막대그래프")


# ── 그림 13. 하한 보장이 닿는 자리 ─────────────────────────────────────────
# 논문: 층을 더하면 하한이 좋아진다 — 층의 유닛 수가 줄지 않을 때만. 층마다 판정한다.
W, H = 820, 330
b = defs()
b += txt(20, 30, "「층을 더하면 하한이 좋아진다」는 층 폭이 줄지 않을 때만 — 이 논문의 오토인코더는 대부분 줄어든다", 14, anchor="start", weight="bold")
chk = [("곡선", [784, 400, 200, 100, 50, 25, 6]), ("MNIST", [784, 1000, 500, 250, 30]),
       ("얼굴 조각", [625, 2000, 1000, 500, 30]), ("문서", [2000, 500, 250, 125, 10]),
       ("분류", [784, 500, 500, 2000])]
print("  [13] RBM 쌓기에서 폭이 줄지 않는 단계 / 전체 단계:")
for k, (name, s) in enumerate(chk):
    y = 70 + 48 * k
    b += txt(20, y + 5, name, 13, anchor="start", weight="bold")
    x = 120
    okn = 0
    for i, n in enumerate(s):
        b += box(x, y - 13, 56, 26, fill=NODE, stroke=INK2, sw=1)
        b += txt(x + 28, y + 5, fmt(n), 11)
        if i + 1 < len(s):
            good = s[i + 1] >= n
            okn += good
            b += line(x + 58, y, x + 82, y, OK if good else NO, 2, marker="ao" if good else "an")
        x += 86
    print("      %-8s %d / %d" % (name, okn, len(s) - 1))
    b += txt(800, y + 5, "%d / %d 단계" % (okn, len(s) - 1), 12, anchor="end", fill=OK if okn else NO, weight="bold")
b += txt(410, 318, "초록 = 다음 층이 같거나 넓다(하한 보장 조건 충족), 빨강 = 좁아진다. 논문도 「이 경우 하한은 적용되지 않는다」고 적는다", 11, fill=MUTED)
svg("fig13_bound_scope", W, H, b, "층 폭 조건 판정")


# ── 그림 14. 계보 — 어디서 받아 어디로 넘기는가 ─────────────────────────────
W, H = 820, 360
b = defs()
b += txt(20, 30, "계보 — 앞 편의 한계를 받아 다음 편에 넘긴다", 15, anchor="start", weight="bold")
chainL = [("역전파 1986", "은닉층에 몫을 나눈다", FWD_SOFT, FWD),
          ("DBN 2006", "한 층씩 RBM 으로 쌓는다", FWD_SOFT, FWD),
          ("오토인코더 2006", "펼쳐서 역전파로 다듬는다", "#FFF3C4", "#9A7B00"),
          ("VAE (다음)", "코드에 확률 분포를 준다", REV_SOFT, REV)]
for k, (t, d, f, s) in enumerate(chainL):
    x = 25 + 200 * k
    b += box(x, 60, 170, 60, fill=f, stroke=s, sw=1.6)
    b += txt(x + 85, 85, t, 13, weight="bold", fill=s)
    b += txt(x + 85, 105, d, 11, fill=INK2)
    if k < 3:
        b += line(x + 172, 90, x + 198, 90, INK2, 1.5, marker="ai")
hand = [(125, "넘긴 것: 깊은 망은", "초기값에 따라 안 배워진다"),
        (325, "넘긴 것: 쌓은 층을", "차원 줄이기에 쓰지 않았다"),
        (525, "남긴 것: 코드의 분포를 정하지 않아", "코드를 뽑아 새 이미지를 만들 길이 없다")]
for x, l1, l2 in hand:
    b += txt(x + 100, 148, l1, 11, fill=INK)
    b += txt(x + 100, 164, l2, 11, fill=INK)
b += box(25, 200, 770, 140, fill=NODE, stroke=LINE)
b += txt(45, 226, "곁가지 — 재구성 오차를 이상 점수로 쓰는 길 (논문은 이 쓰임을 적지 않는다. 내가 잇는 자리다)", 13, anchor="start", weight="bold", fill=REV)
b += txt(45, 252, "정상 데이터만으로 오토인코더를 배우고, 재구성이 잘 안 되는 입력을 이상으로 본다", 12, anchor="start")
b += txt(45, 276, "이 논문의 목표는 반대 방향이다 — 처음 보는 시험 이미지도 잘 재구성하는 것이 성공이다", 12, anchor="start")
b += txt(45, 300, "그래서 「잘 일반화하는 오토인코더」는 이상도 잘 재구성해 버릴 수 있다. 이상 탐지에 가져가려면 이 긴장부터 잰다", 12, anchor="start")
b += txt(45, 324, "사전학습이 없을 때 「평균만 재구성한다」는 논문의 관찰은, 반대로 모든 입력의 점수를 같게 만든다", 12, anchor="start", fill=INK2)
svg("fig14_lineage", W, H, b, "계보와 이상 탐지로 가는 곁가지")

print("끝.")
