# -*- coding: utf-8 -*-
r"""Latent Diffusion 노트(Rombach 외, CVPR 2022, arXiv v2)의 그림 열여덟을 만든다.

색과 글꼴은 저장소의 앞선 노트 그림과 맞췄다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

계산으로 원문을 확인하는 그림이 여럿이다 — 2 · 3 · 4(잠재 수의 개수), 5(식 13 ~ 15 의 가중치), 7(UNet 파라미터를 표의 설정으로 다시 세기),
8 · 9(그림 6 과 그림 17 을 맞대어 걸음당 V100-일과 본 이미지 수 내기), 10(그림 7 로 초당 UNet 평가 수 내기),
13(표 6 의 비), 15(표 5 · 11 의 참조 집합 차이), 17(첫 단계 비용 더하기). 계산한 값은 돌릴 때 화면에도 찍는다.

원문 표의 수는 T2 · T6 · T7 · T8 · T18IN · SR · SHAPES · BATCH13 상수에 옮겨 적었다.
원문 그림 6 · 7 · 17 의 값은 PDF 안의 **래스터(562x301 픽셀 등)에서 픽셀로 읽은 값**이다. 눈금 선 픽셀로 축을 맞추고 곡선 색으로
열마다 픽셀을 모아 평균했다. 1 픽셀이 그림 6 FID 에서 0.82, 그림 7 왼쪽 log FID 에서 0.0093 이다. 원문 그림 1 · 2 · 3 · 6 · 7 · 17 은
crop_paper_figures.py 가 잘라 png 로 둔다.
"""
import io, os, math, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"
NODE      = "#F6F7F5"
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"
OK_SOFT   = "#D6EEDD"
NO        = "#C0392B"
NO_SOFT   = "#F6D9D5"
PURP      = "#8E44AD"
PURP_SOFT = "#EADCF0"
FONT = "IBM Plex Sans KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"


# ── 공통 도구 ──────────────────────────────────────────────────────────────
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def arrow(idd, color):
    return ('<marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>' % (idd, color))


def defs():
    return ("<defs>" + arrow("af", FWD) + arrow("ar", REV) + arrow("ai", INK2) + arrow("ao", OK)
            + arrow("an", NO) + arrow("ac", CODE) + arrow("ap", PURP) + "</defs>")


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
    a = ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s" stroke="%s" stroke-width="%s"'
         % (x, y, w, h, rx, fill or NODE, stroke or INK, sw))
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    return a + "/>"


def bar(x, y, w, h, fill):
    return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x, y, w, h, fill)


def line(x1, y1, x2, y2, color=None, sw=1.2, dash=None, marker=None):
    a = '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"' % (
        x1, y1, x2, y2, color or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if marker:
        a += ' marker-end="url(#%s)"' % marker
    return a + "/>"


def circ(cx, cy, r, fill=None, stroke=None, sw=1.2):
    return '<circle cx="%.1f" cy="%.1f" r="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (
        cx, cy, r, fill or NODE, stroke or INK, sw)


def poly(pts, stroke, sw=2, dash=None):
    d = "M" + " L".join("%.1f,%.1f" % p for p in pts)
    a = '<path d="%s" fill="none" stroke="%s" stroke-width="%s"' % (d, stroke, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    return a + "/>"


def node(x, y, w, h, title, sub=None, fill=None, stroke=None, size=12):
    s = box(x, y, w, h, fill, stroke)
    if sub:
        s += txt(x + w / 2, y + h / 2 - 4, title, size, weight="600")
        s += txt(x + w / 2, y + h / 2 + 13, sub, size - 2, fill=INK2)
    else:
        s += txt(x + w / 2, y + h / 2 + 4, title, size, weight="600")
    return s


def frame(x0, y0, x1, y1, xt, yt, fx, fy, xl=None, yl=None, xfmt=None, yfmt=None):
    s = ""
    for t in yt:
        s += line(x0, fy(t), x1, fy(t), LINE, 1)
        s += txt(x0 - 7, fy(t) + 4, yfmt(t) if yfmt else "%g" % t, 10, fill=MUTED, anchor="end")
    for t in xt:
        s += line(fx(t), y0, fx(t), y1, LINE, 1)
        s += txt(fx(t), y1 + 16, xfmt(t) if xfmt else "%g" % t, 10, fill=MUTED)
    s += line(x0, y1, x1, y1, INK2) + line(x0, y0, x0, y1, INK2)
    if xl:
        s += txt((x0 + x1) / 2, y1 + 34, xl, 11, fill=INK2)
    if yl:
        s += ('<text x="%.1f" y="%.1f" font-size="11" fill="%s" text-anchor="middle" transform="rotate(-90 %.1f %.1f)">%s</text>'
              % (x0 - 44, (y0 + y1) / 2, INK2, x0 - 44, (y0 + y1) / 2, esc(yl)))
    return s


# ── 원문 수 ────────────────────────────────────────────────────────────────
# 표 8 (21 쪽): (f, 정칙화, c, |Z|, R-FID, PSNR). VQGAN · DALL-E · 주의 없는 행은 빼 두었다.
T8 = [
    (32, "VQ", 16, 16384, 31.83, 17.45), (16, "VQ", 8, 16384, 5.15, 20.83),
    (8, "VQ", 4, 16384, 1.14, 23.07), (8, "VQ", 4, 256, 1.49, 22.35),
    (4, "VQ", 3, 8192, 0.58, 27.43), (4, "VQ", 3, 256, 0.47, 26.43),
    (2, "VQ", 2, 2048, 0.16, 30.85), (2, "VQ", 2, 64, 0.40, 29.13),
    (32, "KL", 64, 0, 2.04, 22.27), (32, "KL", 16, 0, 7.3, 20.38),
    (16, "KL", 16, 0, 0.87, 24.08), (16, "KL", 8, 0, 2.63, 21.94),
    (8, "KL", 4, 0, 0.90, 24.19), (4, "KL", 3, 0, 0.27, 27.53), (2, "KL", 2, 0, 0.086, 32.47),
]
# 표 13 z-shape (24 쪽). LDM-32 칸은 원문이 「88 x 8 x 32」 로 적었고 8 x 8 x 32 로 읽었다.
SHAPES = [("LDM-1", 256, 3), ("LDM-2", 128, 2), ("LDM-4", 64, 3), ("LDM-8", 32, 4), ("LDM-16", 16, 8), ("LDM-32", 8, 32)]
BATCH13 = {"LDM-1": 7, "LDM-2": 9, "LDM-4": 40, "LDM-8": 64, "LDM-16": 112, "LDM-32": 112}

# 그림 6 · 17 에서 읽은 값. FID_2M = 2M 걸음 FID(그림 6), FID_35 = 35 V100-일 FID(그림 17),
# DAYS = 그림 17 을 그림 6 에 겹치는 가로 비(V100-일 / 1M 걸음). 맞댄 오차는 RMSE 0.18 ~ 0.28 FID.
# LDM-4 의 35 일 값은 빨강 · 보라에 가려 잘 안 뽑혀서 그림 6 의 1.35M 자리와 함께 보고 적었고 오차가 1 FID 까지 더 크다.
FID_2M = {"LDM-1": 68.5, "LDM-2": 55.7, "LDM-4": 34.4, "LDM-8": 31.1, "LDM-16": 36.1, "LDM-32": 86.5}
FID_35 = {"LDM-1": 68.4, "LDM-2": 55.4, "LDM-4": 37.0, "LDM-8": 36.9, "LDM-16": 38.1, "LDM-32": 87.5}
IS_2M = {"LDM-1": 18.0, "LDM-2": 23.5, "LDM-4": 38.0, "LDM-8": 41.7, "LDM-16": 36.0, "LDM-32": 13.5}
IS_35 = {"LDM-1": 18.0, "LDM-2": 23.6, "LDM-4": 35.4, "LDM-8": 34.9, "LDM-16": 33.9, "LDM-32": 13.1}
DAYS = {"LDM-1": 17.5, "LDM-2": 17.25, "LDM-4": 26.0, "LDM-8": 27.0, "LDM-16": 26.0, "LDM-32": 23.25}

# 그림 7 왼쪽(CelebA-HQ)에서 읽은 표식: 걸음 수 -> (초당 표본, log FID). 표식이 겹친 자리는 넣지 않았다.
F7L = {
    "LDM-1": {10: (3.5, 3.85), 20: (1.8, 3.49)},
    "LDM-2": {10: (6.9, 3.24), 20: (4.0, 2.76)},
    "LDM-4": {10: (14.3, 3.07), 20: (8.7, 2.44)},
    "LDM-8": {10: (26.3, 3.02), 20: (17.3, 2.53), 50: (8.4, 2.18), 100: (4.5, 2.11), 200: (2.5, 2.07)},
    "LDM-16": {10: (62.7, 2.73), 20: (48.5, 2.29), 50: (28.7, 2.12), 100: (17.1, 2.10), 200: (9.7, 2.02)},
    "LDM-32": {10: (75.3, 2.65), 20: (64.5, 2.32), 50: (45.1, 2.16), 100: (29.8, 2.18), 200: (18.0, 2.16)},
}

# 표 18 (28 쪽): 이름, V100-일, FID
T18IN = [("ADM", 916, 10.94), ("ADM-G 250", 962, 4.59), ("ADM-G 25", 962, 5.58), ("ADM-G,U", 349, 3.85),
         ("LDM-8", 79, 17.41), ("LDM-8-G", 91, 8.11), ("LDM-4", 271, 10.56), ("LDM-4-G 1.25", 271, 3.95), ("LDM-4-G 1.5", 271, 3.60)]

# 표 6 (8 쪽): 학습 처리량, 표본 @256, 표본 @512, 시간/에폭, FID@2k
T6 = {"LDM-1": (0.11, 0.26, 0.07, 20.66, 24.74), "KL attn": (0.32, 0.97, 0.34, 7.66, 15.21),
      "VQ attn": (0.33, 0.97, 0.34, 7.04, 14.99), "VQ no attn": (0.35, 0.99, 0.36, 6.66, 15.95)}

# 표 7 (9 쪽) 40 ~ 50% 가림 FID. o = 이 편이 잰 값, r = 이 편의 시험 집합에서 다시 잰 값, l = 다른 논문에서 옮긴 값
T7 = [("LDM-4 big, w/ ft", 9.39, "o"), ("CoModGAN", 10.4, "l"), ("LDM-4 w/ attn", 11.87, "o"), ("LaMa 원 논문 값", 12.0, "l"),
      ("LaMa 다시 잼", 12.31, "r"), ("LDM-4 w/o attn", 12.60, "o"), ("LDM-4 big, w/o ft", 12.89, "o"),
      ("RegionWise", 21.3, "l"), ("DeepFill v2", 22.1, "l"), ("EdgeConnect", 30.5, "l")]

# 표 5 · 11 (8 · 23 쪽): 검증 참조, 학습 참조
SR = [("LDM-4 big, 100 걸음", 2.4, 4.3), ("LDM-4 100 걸음 +15 에폭", 2.6, 4.6), ("LDM-4 100 걸음", 2.8, 4.8),
      ("LDM-4 50 걸음 안내", 4.4, 6.4), ("Pixel-DM 100 걸음 +15 에폭", 5.1, 7.1)]

# 표 2 (6 쪽): 이름, FID, 파라미터(M)
T2 = [("CogView", 27.10, 4000), ("LAFITE", 26.94, 75), ("GLIDE", 12.24, 6000), ("Make-A-Scene", 11.84, 4000),
      ("LDM-KL-8", 23.31, 1450), ("LDM-KL-8-G", 12.63, 1450)]


# ── UNet 다시 세기 (내가 센 것) ───────────────────────────────────────────────
# 짜임은 원문 표 12 ~ 16 의 값에, 원문이 말한 「ablated UNet」(ADM) 의 일반 꼴을 얹은 **가정**이다.
def gn(c):
    return 2 * c


def conv(i, o, k=3):
    return i * o * k * k + o


def lin(i, o):
    return i * o + o


def res(i, o, emb, ss=False):
    p = gn(i) + conv(i, o) + lin(emb, 2 * o if ss else o) + gn(o) + conv(o, o)
    return p + (conv(i, o, 1) if i != o else 0)


def attn(c):
    return gn(c) + (3 * c * c + 3 * c) + (c * c + c)


def stblock(c, inner, depth, ctx, gated=True):
    b = gn(c) + conv(c, inner, 1) + conv(inner, c, 1)
    blk = 3 * inner * inner + lin(inner, inner)
    blk += inner * inner + 2 * ctx * inner + lin(inner, inner)
    blk += (lin(inner, 8 * inner) if gated else lin(inner, 4 * inner)) + lin(4 * inner, inner)
    blk += 3 * 2 * inner
    return b + depth * blk


def unet(r, cin, cout, ch, mu, nres, att, af, updown=False, ss=False):
    emb = 4 * ch
    tot = lin(ch, emb) + lin(emb, emb) + conv(cin, ch)
    chs = [ch]
    cur = ch
    for li, m in enumerate(mu):
        for _ in range(nres):
            tot += res(cur, m * ch, emb, ss)
            cur = m * ch
            if r in att:
                tot += af(cur)
            chs.append(cur)
        if li != len(mu) - 1:
            tot += res(cur, cur, emb, ss) if updown else conv(cur, cur)
            chs.append(cur)
            r //= 2
    tot += 2 * res(cur, cur, emb, ss) + af(cur)
    for li, m in list(enumerate(mu))[::-1]:
        for i in range(nres + 1):
            ich = chs.pop()
            tot += res(cur + ich, m * ch, emb, ss)
            cur = m * ch
            if r in att:
                tot += af(cur)
            if li and i == nres:
                tot += res(cur, cur, emb, ss) if updown else conv(cur, cur)
                r *= 2
    return tot + gn(cur) + conv(cur, cout)


def ca1(d):
    return lambda c: stblock(c, c, d, 512)


def tau(dim, depth, seq, vocab, inner):
    block = 4 * dim + 3 * dim * inner + lin(inner, dim) + lin(dim, 4 * dim) + lin(4 * dim, dim)
    return vocab * dim + seq * dim + depth * block + 2 * dim


CE = 1000 * 512  # 부류 표 1,000 x 512
RECOUNT = [
    ("표 14 LDM-1", unet(256, 3, 3, 192, (1, 1, 2, 2, 4, 4), 2, (32, 16, 8), attn), 270),
    ("표 14 LDM-2", unet(128, 2, 2, 192, (1, 2, 2, 4, 4), 2, (32, 16, 8), attn), 265),
    ("표 14 LDM-4", unet(64, 3, 3, 224, (1, 2, 3, 4), 2, (32, 16, 8), attn), 274),
    ("표 14 LDM-8", unet(32, 4, 4, 256, (1, 2, 4), 2, (32, 16, 8), attn), 258),
    ("표 14 LDM-16", unet(16, 8, 8, 256, (1, 2, 4), 2, (16, 8, 4), attn), 260),
    ("표 14 LDM-32", unet(8, 32, 32, 256, (1, 2, 4), 2, (8, 4, 2), attn), 258),
    ("표 12 교회", unet(32, 4, 4, 192, (1, 2, 2, 4, 4), 2, (32, 16, 8, 4), attn), 294),
    ("표 18 교회", unet(32, 4, 4, 192, (1, 2, 2, 4, 4), 2, (32, 16, 8, 4), attn), 256),
    ("표 13 LDM-1", unet(256, 3, 3, 192, (1, 1, 2, 2, 4, 4), 2, (32, 16, 8), ca1(1)) + CE, 396),
    ("표 13 LDM-2", unet(128, 2, 2, 192, (1, 2, 2, 4, 4), 2, (32, 16, 8), ca1(1)) + CE, 391),
    ("표 13 LDM-4", unet(64, 3, 3, 192, (1, 2, 3, 5), 2, (32, 16, 8), ca1(1)) + CE, 391),
    ("표 3 LDM-4", unet(64, 3, 3, 192, (1, 2, 3, 5), 2, (32, 16, 8), ca1(1)) + CE, 400),
    ("표 13 LDM-8", unet(32, 4, 4, 256, (1, 2, 4), 2, (32, 16, 8), ca1(1)) + CE, 395),
    ("표 13 LDM-16", unet(16, 8, 8, 256, (1, 2, 4), 2, (16, 8, 4), ca1(1)) + CE, 395),
    ("표 13 LDM-32", unet(8, 32, 32, 256, (1, 2, 4), 2, (8, 4, 2), ca1(1)) + CE, 395),
    ("표 15 메우기", unet(64, 7, 3, 128, (1, 4, 8), 2, (), attn), 215),
    ("표 15 초해상도", unet(64, 6, 3, 160, (1, 2, 2, 4), 2, (), attn), 169),
    ("표 15 글 (UNet 만)", unet(32, 4, 4, 320, (1, 2, 4, 4), 2, (32, 16, 8), lambda c: stblock(c, c, 1, 1280)), 1450),
]


# ── 그림 ───────────────────────────────────────────────────────────────────
def fig01():
    s = txt(470, 26, "두 단계: 오토인코더를 먼저 배워 얼리고, 그 잠재 공간에서 확산을 배운다", 14, weight="600")
    s += box(20, 44, 196, 300, FWD_SOFT, FWD, dash="5,4") + txt(118, 64, "1 단계 — 픽셀 공간", 12, FWD, weight="600")
    s += node(40, 84, 66, 48, "x", "256x256x3", NODE, FWD, 11)
    s += node(136, 84, 62, 48, "E", "부호기", NODE, FWD, 11)
    s += line(106, 108, 136, 108, FWD, 1.4, marker="af")
    s += node(136, 240, 62, 48, "D", "복호기", NODE, FWD, 11)
    s += node(40, 240, 66, 48, "x 복원", "256x256x3", NODE, FWD, 11)
    s += line(136, 264, 106, 264, FWD, 1.4, marker="af")
    s += txt(118, 165, "지각 손실 + 조각 판별기", 11, INK2)
    s += txt(118, 183, "+ KL(무게 10^-6 자리)", 11, INK2) + txt(118, 201, "또는 VQ", 11, INK2)
    s += txt(118, 318, "배운 뒤 얼린다", 11, NO, weight="600")

    s += box(236, 44, 470, 300, CODE_SOFT, CODE, dash="5,4") + txt(471, 64, "2 단계 — 잠재 공간 (f = 4 면 64x64x3)", 12, CODE, weight="600")
    s += node(256, 84, 62, 48, "z", "z = E(x)", NODE, CODE, 11)
    s += line(198, 108, 256, 108, FWD, 1.4, marker="af")
    s += node(420, 84, 62, 48, "z_t", "닫힌 꼴", NODE, CODE, 11)
    s += line(318, 108, 420, 108, CODE, 1.4, marker="ac") + txt(369, 100, "잡음 더하기", 10, INK2)
    s += node(584, 84, 100, 48, "eps 맞히기", "식 (2) · (3)", NODE, CODE, 11)
    s += line(482, 108, 584, 108, CODE, 1.4, marker="ac")
    s += box(290, 170, 300, 92, NODE, INK2) + txt(440, 190, "시간 조건 UNet", 12, weight="600")
    s += txt(440, 208, "합성곱 + 교차 주의(질의 = UNet 특징)", 11, INK2)
    s += txt(440, 226, "키 · 값 = tau(y) · 표 16 블록", 11, INK2)
    s += txt(440, 248, "표본 뽑기: z_T 에서 걸음마다 eps 를 뺀다", 10, MUTED)
    s += line(451, 132, 451, 170, CODE, 1.4, marker="ac")
    s += line(290, 264, 198, 264, CODE, 1.4, marker="ac") + txt(248, 256, "z_0", 10, INK2)

    s += box(726, 44, 194, 300, PURP_SOFT, PURP, dash="5,4") + txt(823, 64, "조건 y", 12, PURP, weight="600")
    s += node(746, 84, 154, 42, "글 · 부류 · 상자", "tau 가 M x d_tau 로", NODE, PURP, 11)
    s += line(746, 110, 590, 195, PURP, 1.4, marker="ap") + txt(632, 192, "교차 주의", 10, PURP)
    s += node(746, 214, 154, 42, "낮은 해상도 · 지도 · 가림", "z_t 에 이어 붙임", NODE, PURP, 10)
    s += line(746, 235, 590, 235, PURP, 1.4, marker="ap") + txt(668, 228, "concat", 10, PURP)
    s += txt(823, 300, "tau 와 eps_theta 는", 11, INK2) + txt(823, 318, "함께 배운다(식 3)", 11, INK2)
    svg("fig01_two_stages", 940, 364, s, "두 단계 파이프라인")


def fig02():
    W, H = 860, 340
    x0, x1 = 150, 800
    ys = [62 + i * 40 for i in range(6)]
    full = 256 * 256 * 3
    fx = lambda v: x0 + (x1 - x0) * (math.log10(v) - 2.8) / (math.log10(full) - 2.8)
    s = txt(W / 2, 28, "표 13 의 z-shape 를 수의 개수로 — 256x256x3 = 196,608 개 기준", 14, weight="600")
    for i, (lab, r, c) in enumerate(SHAPES):
        n = r * r * c
        s += txt(x0 - 10, ys[i] + 15, lab, 12, anchor="end", weight="600")
        s += bar(x0, ys[i], fx(n) - x0, 22, FWD if lab != "LDM-1" else REV)
        inside = fx(n) > 640
        s += txt(fx(n) - 8 if inside else fx(n) + 8, ys[i] + 15, "%dx%dx%d = %s 개 · %.0f 분의 1" % (r, r, c, format(n, ","), full / n), 11,
                 anchor="end" if inside else "start", fill="#FFFFFF" if inside else INK)
    n32 = 8 * 8 * 16
    s += bar(x0, ys[5] + 24, fx(n32) - x0, 7, NO)
    s += txt(fx(n32) + 8, ys[5] + 32, "표 8 의 f = 32 는 c = 16 이라 1,024 개(표 13 과 어긋남)", 10, NO, anchor="start")
    s += txt(W / 2, H - 14, "가로는 로그. LDM-16 과 LDM-32 는 수의 개수가 같다(2,048). 자리 수는 256 과 64 로 네 배 다르다. 내가 센 것", 11, INK2)
    svg("fig02_latent_sizes", W, H, s, "잠재 수의 개수")


def _t8(kind):
    W, H = 760, 430
    x0, x1, y0, y1 = 80, 720, 60, 372
    fx = lambda n: x0 + (x1 - x0) * (math.log2(n) - 9.6) / (15.4 - 9.6)
    xt = [1024, 2048, 4096, 12288, 32768]
    if kind == "psnr":
        fy = lambda v: y1 - (y1 - y0) * (v - 16) / (34 - 16)
        yt = [16, 20, 24, 28, 32]
        yl = "PSNR (dB, 위가 좋다)"
        title = "표 8 — 복원 PSNR 은 f 보다 잠재 수의 개수를 따른다"
    else:
        fy = lambda v: y1 - (y1 - y0) * (math.log10(v) + 1.2) / (1.7 + 1.2)
        yt = [0.1, 0.3, 1, 3, 10, 30]
        yl = "R-FID (로그, 아래가 좋다)"
        title = "표 8 — 복원 R-FID. 같은 4,096 개에서 KL f = 8 · 16 은 0.03 차이"
    s = txt(W / 2, 28, title, 14, weight="600")
    s += frame(x0, y0, x1, y1, xt, yt, fx, fy, "잠재 수의 개수 (256x256 입력으로 계산, 로그) — 내가 센 것", yl, xfmt=lambda t: format(t, ","))
    s += line(fx(4096), y0, fx(4096), y1, CODE, 1.4, dash="4,4")
    for f, reg, c, z, rf, ps in T8:
        n = (256 // f) ** 2 * c
        v = ps if kind == "psnr" else rf
        col = FWD if reg == "KL" else REV
        s += circ(fx(n), fy(v), 5, col, "#FFFFFF", 1)
        lab = "f%d" % f + ("" if reg == "KL" or z in (16384, 8192, 2048) else " |Z|%d" % z)
        dx = 9 if reg == "KL" else -9
        dy = 4
        if reg == "KL" and f == 16 and c == 16:
            dy = -6 if kind == "rfid" else 13
        if reg == "KL" and f == 8:
            dy = 14 if kind == "rfid" else -4
        s += txt(fx(n) + dx, fy(v) + dy, lab, 10, col, anchor="start" if reg == "KL" else "end")
    lx = x0 + 24 if kind == "psnr" else x1 - 100
    s += circ(lx, y0 + 12, 5, FWD, "#FFFFFF", 1) + txt(lx + 10, y0 + 16, "KL 정칙화", 11, anchor="start")
    s += circ(lx, y0 + 32, 5, REV, "#FFFFFF", 1) + txt(lx + 10, y0 + 36, "VQ 정칙화", 11, anchor="start")
    return W, H, s


def fig03():
    W, H, s = _t8("psnr")
    svg("fig03_tab8_psnr", W, H, s, "표 8 PSNR")


def fig04():
    W, H, s = _t8("rfid")
    svg("fig04_tab8_rfid", W, H, s, "표 8 R-FID")


def fig05():
    T = 1000
    b = [1e-4 + (0.02 - 1e-4) * i / (T - 1) for i in range(T)]
    ab = []
    p = 1.0
    for x in b:
        p *= 1 - x
        ab.append(p)
    snr = [a / (1 - a) for a in ab]
    w = {}
    dd = {}
    for t in range(2, T + 1):
        i = t - 1
        w[t] = 0.5 * (snr[i - 1] - snr[i]) * (1 - ab[i]) / ab[i]
        post = (1 - ab[i - 1]) / (1 - ab[i]) * b[i]
        dd[t] = b[i] ** 2 / (2 * post * (1 - b[i]) * (1 - ab[i]))
    mx = max(abs(w[t] / dd[t] - 1) for t in w)
    tot = sum(w.values())
    m = min(w, key=lambda t: w[t])
    print("    식 13-15 가중치 대 DDPM 식 12 계수 최대 상대 차이 %.1e, w(2)/w(1000) = %.1f, w(2)/최소 = %.1f(t=%d), t<=50 의 몫 %.1f%%" % (
        mx, w[2] / w[T], w[2] / w[m], m, 100 * sum(w[t] for t in range(2, 51)) / tot))
    W, H = 760, 400
    x0, x1, y0, y1 = 84, 720, 56, 340
    fx = lambda t: x0 + (x1 - x0) * t / 1000.0
    fy = lambda v: y1 - (y1 - y0) * (math.log10(v) + 2.6) / 2.6
    s = txt(W / 2, 28, "식 (13) ~ (15) 를 eps 꼴로 — 균등 가중으로 바꾸며 버리는 몫 (t = 1 은 SNR(0) 이 무한이라 뺐다)", 13, weight="600")
    s += frame(x0, y0, x1, y1, [2, 200, 400, 600, 800, 1000], [0.003, 0.01, 0.03, 0.1, 0.3, 1], fx, fy,
               "t (선형 일정 beta 1e-4 ~ 0.02, 이 값은 DDPM 의 것이다)", "1/2 (SNR(t-1) / SNR(t) - 1), 로그")
    s += poly([(fx(t), fy(w[t])) for t in range(2, T + 1, 2)], FWD, 2.2)
    s += circ(fx(2), fy(w[2]), 4, REV, "#FFFFFF") + txt(fx(2) + 10, fy(w[2]) + 4, "t = 2: %.3f" % w[2], 11, REV, anchor="start")
    s += circ(fx(m), fy(w[m]), 4, REV, "#FFFFFF") + txt(fx(m), fy(w[m]) + 20, "가장 작은 자리 t = %d: %.5f" % (m, w[m]), 11, REV)
    s += circ(fx(T), fy(w[T]), 4, REV, "#FFFFFF") + txt(fx(T) - 8, fy(w[T]) - 10, "t = 1000: %.4f" % w[T], 11, REV, anchor="end")
    s += txt(W / 2, H - 12, "이 곡선이 DDPM 식 (12) 의 계수와 전 구간에서 같다(상대 차이 %.0e, sigma^2 = 사후 분산일 때). 내가 센 것" % mx, 11, INK2)
    svg("fig05_dropped_weight", W, H, s, "버리는 가중치")


def fig06():
    W, H = 900, 372
    s = txt(W / 2, 28, "교차 주의의 모양 — 글 모델의 32x32 층에서 작은 예 (N = 1,024, d_eps = 320, M = 77, d_tau = 1,280, d = 320)", 13, weight="600")
    s += box(30, 50, 240, 120, FWD_SOFT, FWD) + txt(150, 72, "UNet 특징 phi(z_t)", 12, FWD, weight="600")
    s += txt(150, 94, "N x d_eps = 1,024 x 320", 12) + txt(150, 118, "질의를 만든다", 11, INK2) + txt(150, 140, "W_Q: 320 -> 320", 11)
    s += box(30, 190, 240, 120, PURP_SOFT, PURP) + txt(150, 212, "조건 tau(y)", 12, PURP, weight="600")
    s += txt(150, 234, "M x d_tau = 77 x 1,280", 12) + txt(150, 258, "키와 값을 만든다", 11, INK2) + txt(150, 280, "W_K, W_V: 1,280 -> 320", 11)
    s += line(270, 110, 350, 110, FWD, 1.4, marker="af") + line(270, 250, 350, 150, PURP, 1.4, marker="ap")
    s += node(350, 90, 190, 60, "softmax(Q K^T / sqrt d)", "1,024 x 77", NODE, INK, 12)
    s += line(540, 120, 610, 120, INK2, 1.4, marker="ai")
    s += node(610, 90, 110, 60, "곱하기 V", "1,024 x 320", NODE, INK, 12)
    s += txt(445, 176, "자리마다 낱말 77 개에 무게를 나눠 준다", 11, INK2)
    s += box(380, 214, 490, 96, NO_SOFT, NO)
    s += txt(625, 236, "원문 4 · 5 쪽의 차원 표기", 12, NO, weight="600")
    s += txt(625, 258, "W_V ∈ R^(d x d_eps), W_Q ∈ R^(d x d_tau), W_K ∈ R^(d x d_tau)", 12)
    s += txt(625, 282, "그런데 Q = W_Q · phi, V = W_V · tau 다. W_Q 와 W_V 의 모양이 뒤바뀌어 있다", 11, NO)
    s += txt(W / 2, H - 22, "N · d_eps 는 표 15(채널 320, 곱 1 단) 에서, M · d_tau 는 표 17 에서 왔다. 머리 8 개를 합친 폭으로 적었다", 11, INK2)
    svg("fig06_cross_attention", W, H, s, "교차 주의 모양")


def fig07():
    rows = RECOUNT
    W, H = 860, 62 + 24 * len(rows) + 56
    x0, x1 = 190, 730
    fx = lambda r: x0 + (x1 - x0) * (r - 0.55) / (1.05 - 0.55)
    s = txt(W / 2, 28, "UNet 파라미터를 표의 설정으로 다시 세기 — 다시 센 값 / 원문 값", 14, weight="600")
    y0 = 50
    y1 = y0 + 24 * len(rows)
    for t in [0.6, 0.7, 0.8, 0.9, 1.0]:
        s += line(fx(t), y0, fx(t), y1, LINE if t != 1.0 else INK2, 1)
        s += txt(fx(t), y1 + 16, "%.1f" % t, 10, MUTED)
    for i, (n, c, rep) in enumerate(rows):
        y = y0 + 12 + i * 24
        r = c / 1e6 / rep
        ok = abs(r - 1) <= 0.012
        col = OK if ok else NO
        s += txt(x0 - 10, y + 4, n, 11, anchor="end")
        s += circ(fx(r), y, 5, col, "#FFFFFF", 1)
        s += txt(795, y + 4, "%.2fM / %sM" % (c / 1e6, format(rep, ",")), 10, col if not ok else INK2)
        print("    %-20s %8.2fM  원문 %5dM  비 %.3f" % (n, c / 1e6, rep, r))
    s += txt(W / 2, H - 16, "초록 = 1.2% 안. 가정: 원문이 말한 ablated UNet 의 일반 꼴, 교차 주의 블록의 MLP 는 게이트 꼴(원문에 없다). 내가 센 것", 11, INK2)
    svg("fig07_param_recount", W, H, s, "파라미터 다시 세기")


def fig08():
    W, H = 880, 366
    x0, x1, y0, y1 = 110, 620, 58, 296
    fx = lambda v: x0 + (x1 - x0) * (v - 20) / (95 - 20)
    names = [q[0] for q in SHAPES]
    s = txt(W / 2, 28, "그림 6(같은 걸음) 과 그림 17(같은 비용) 의 끝 값 — 같은 곡선을 다른 자리에서 자른다", 14, weight="600")
    for t in [20, 40, 60, 80]:
        s += line(fx(t), y0, fx(t), y1, LINE, 1) + txt(fx(t), y1 + 16, "%d" % t, 10, MUTED)
    s += txt((x0 + x1) / 2, y1 + 34, "FID (5,000 표본, 아래가 좋다, 픽셀로 읽은 값)", 11, INK2)
    s += txt(640, 44, "2M 걸음에 든 V100-일", 11, INK2, anchor="start") + txt(640, 58, "35 일에 간 걸음", 11, INK2, anchor="start")
    for i, n in enumerate(names):
        y = y0 + 22 + i * 40
        s += txt(x0 - 12, y + 4, n, 12, anchor="end", weight="600")
        s += line(fx(FID_2M[n]), y, fx(FID_35[n]), y, INK2, 1.4)
        s += circ(fx(FID_2M[n]), y, 6, REV, "#FFFFFF") + circ(fx(FID_35[n]), y, 6, FWD, "#FFFFFF")
        lo, hi = min(FID_2M[n], FID_35[n]), max(FID_2M[n], FID_35[n])
        s += txt(fx(lo) - 10, y + 4, "%.1f" % lo, 10, REV if FID_2M[n] <= FID_35[n] else FWD, anchor="end")
        s += txt(fx(hi) + 10, y + 4, "%.1f" % hi, 10, FWD if FID_2M[n] <= FID_35[n] else REV, anchor="start")
        s += txt(640, y + 4, "%.1f 일 · %.2fM 걸음" % (2 * DAYS[n], min(2.0, 35.0 / DAYS[n])), 11, anchor="start")
    s += circ(x0 + 20, H - 18, 6, REV, "#FFFFFF") + txt(x0 + 32, H - 14, "2M 걸음(그림 6)", 11, anchor="start")
    s += circ(x0 + 170, H - 18, 6, FWD, "#FFFFFF") + txt(x0 + 182, H - 14, "35 V100-일(그림 17)", 11, anchor="start")
    s += txt(x0 + 350, H - 14, "LDM-1 빼기 LDM-8: %.1f 에서 %.1f 로" % (FID_2M["LDM-1"] - FID_2M["LDM-8"], FID_35["LDM-1"] - FID_35["LDM-8"]), 12, NO, anchor="start", weight="600")
    svg("fig08_fig6_vs_fig17", W, H, s, "그림 6 대 그림 17")


def fig09():
    W, H = 860, 350
    names = [q[0] for q in SHAPES]
    x0, x1, y0, y1 = 90, 820, 54, 280
    bw = 40
    fy = lambda v: y1 - (y1 - y0) * v / 240.0
    s = txt(W / 2, 28, "본 이미지 수 — 표 13 의 배치 x 걸음", 14, weight="600")
    s += frame(x0, y0, x1, y1, [], [0, 60, 120, 180, 240], lambda t: t, fy, None, "본 이미지 수 (백만 장)")
    for i, n in enumerate(names):
        cx = x0 + 70 + i * 118
        a = BATCH13[n] * 2.0
        b = BATCH13[n] * min(2.0, 35.0 / DAYS[n])
        s += bar(cx - bw - 2, fy(a), bw, y1 - fy(a), REV) + bar(cx + 2, fy(b), bw, y1 - fy(b), FWD)
        s += txt(cx - bw / 2 - 2, fy(a) - 5, "%.0fM" % a, 10, REV) + txt(cx + bw / 2 + 2, fy(b) - 5, "%.0fM" % b, 10, FWD)
        s += txt(cx, y1 + 16, n, 11, weight="600") + txt(cx, y1 + 32, "배치 %d" % BATCH13[n], 10, MUTED)
        print("    %-7s 2M 걸음 %6.1fM 장, 35 일 %6.1fM 장, 초당 %.1f 장(A100 15.9 일)" % (n, a, b, b * 1e6 / (35 / 2.2 * 86400)))
    s += bar(x0 + 10, H - 20, 14, 10, REV) + txt(x0 + 30, H - 11, "2M 걸음(그림 6)", 11, anchor="start")
    s += bar(x0 + 150, H - 20, 14, 10, FWD) + txt(x0 + 170, H - 11, "35 V100-일(그림 17)", 11, anchor="start")
    s += txt(x0 + 330, H - 11, "LDM-1 은 14M 장, LDM-8 은 128M 장을 보고 그림 6 의 끝에 닿는다", 11, NO, anchor="start")
    svg("fig09_images_seen", W, H, s, "본 이미지 수")


def eval_rates():
    out = {}
    for n in F7L:
        ks = sorted(F7L[n])
        a, b = ks[0], ks[-1]
        slope = (1.0 / F7L[n][b][0] - 1.0 / F7L[n][a][0]) / (b - a)
        fixed = 1.0 / F7L[n][a][0] - slope * a
        out[n] = (1.0 / slope, fixed)
    return out


def fig10():
    R = eval_rates()
    W, H = 780, 430
    x0, x1, y0, y1 = 90, 740, 56, 366
    pos = {"LDM-1": 65536, "LDM-2": 16384, "LDM-4": 4096, "LDM-8": 1024, "LDM-16": 256, "LDM-32": 64}
    fx = lambda v: x0 + (x1 - x0) * (math.log2(v) - 5) / (17 - 5)
    fy = lambda v: y1 - (y1 - y0) * (math.log10(v) - 1) / (4 - 1)
    s = txt(W / 2, 28, "초당 UNet 평가 수 — 그림 7 왼쪽에서 걸음 수를 빼고 낸 값", 14, weight="600")
    s += frame(x0, y0, x1, y1, [64, 256, 1024, 4096, 16384, 65536], [10, 30, 100, 300, 1000, 3000, 10000], fx, fy,
               "잠재 자리 수 (h x w, 로그)", "UNet 평가 / 초 (로그)", xfmt=lambda t: format(t, ","), yfmt=lambda t: format(t, ","))
    s += poly([(fx(pos[n]), fy(R[n][0])) for n in pos], FWD, 2)
    for n in pos:
        s += circ(fx(pos[n]), fy(R[n][0]), 6, FWD, "#FFFFFF")
        s += txt(fx(pos[n]) + 9, fy(R[n][0]) - 8, "%s %s" % (n, format(int(round(R[n][0])), ",")), 11, FWD, anchor="start")
        print("    %-7s 평가/초 %7.1f, 걸음과 무관한 몫 %.1f ms" % (n, R[n][0], R[n][1] * 1000))
    s += circ(fx(4096), fy(214), 5, CODE, "#FFFFFF") + txt(fx(4096) - 9, fy(214) + 18, "표 18 LDM-4 214 (0.43 x 500 · 1.07 x 200)", 10, CODE, anchor="end")
    s += circ(fx(65536), fy(30), 5, REV, "#FFFFFF") + txt(fx(65536) - 9, fy(30) + 4, "표 18 ADM 30 (0.03 x 1000 · 0.12 x 250)", 10, REV, anchor="end")
    s += txt(W / 2, H - 12, "자리 수가 1,024 배 줄 때 평가 수는 %.0f 배 는다. 파라미터는 표 14 의 258 ~ 274M. 내가 센 것, 왼쪽 셋(LDM-1 · 2 · 4)은 표식 둘로 냈다" % (R["LDM-32"][0] / R["LDM-1"][0]), 11, INK2)
    svg("fig10_eval_rate", W, H, s, "초당 UNet 평가")


def fig11():
    W, H = 840, 350
    data = [("CelebA-HQ", 5.11, ("UDM", 7.16), ("PGGAN", 8.0)), ("FFHQ", 4.98, ("UDM", 5.54), ("ProjectedGAN", 3.08)),
            ("LSUN 교회", 4.02, ("DDPM", 7.89), ("ProjectedGAN", 1.59)), ("LSUN 침실", 2.95, ("ADM", 1.90), ("ProjectedGAN", 1.52))]
    x0, x1, y0, y1 = 70, 810, 56, 284
    fy = lambda v: y1 - (y1 - y0) * v / 9.0
    s = txt(W / 2, 28, "표 1 — 칸마다 LDM 과 표 안의 가장 낮은 확산 · GAN (FID, 아래가 좋다)", 14, weight="600")
    s += frame(x0, y0, x1, y1, [], [0, 3, 6, 9], lambda t: t, fy, None, "FID")
    for i, (n, l, d, g) in enumerate(data):
        cx = x0 + 96 + i * 186
        for j, (lab, v, col) in enumerate([("LDM", l, FWD), (d[0], d[1], PURP), (g[0], g[1], REV)]):
            x = cx - 72 + j * 50
            s += bar(x, fy(v), 44, y1 - fy(v), col) + txt(x + 22, fy(v) - 5, "%.2f" % v, 11, col)
            s += txt(x + 22, y1 + 14, lab if len(lab) < 8 else "Proj.GAN", 9, INK2)
        s += txt(cx, y1 + 32, n, 12, weight="600")
    s += txt(W / 2, H - 12, "FID 표본 수는 50,000(E.3.1). 비교 상대 값은 그 편들에서 옮긴 값이고 같은 실행이 아니다(표 1 각주)", 11, INK2)
    svg("fig11_tab1_fid", W, H, s, "표 1 FID")


def fig12():
    W, H = 800, 430
    x0, x1, y0, y1 = 80, 760, 56, 368
    fx = lambda v: x0 + (x1 - x0) * (math.log10(v) - 1.7) / (3.1 - 1.7)
    fy = lambda v: y1 - (y1 - y0) * (v - 2) / (18.5 - 2)
    s = txt(W / 2, 28, "표 18 ImageNet — 학습 비용과 FID (첫 단계 비용은 뺀 값)", 14, weight="600")
    s += frame(x0, y0, x1, y1, [50, 100, 200, 400, 800], [3, 6, 9, 12, 15, 18], fx, fy, "학습 비용 V100-일 (로그)", "FID (50,000 표본, 아래가 좋다)")
    off = {"ADM-G 250": (-8, 15, "end"), "ADM-G 25": (-8, -8, "end"), "LDM-4-G 1.25": (-9, -4, "end"), "LDM-4-G 1.5": (-9, 12, "end"), "ADM-G,U": (8, 4, "start"), "ADM": (-9, 4, "end")}
    for n, c, f in T18IN:
        col = FWD if n.startswith("LDM") else REV
        s += circ(fx(c), fy(f), 6, col, "#FFFFFF")
        dx, dy, an = off.get(n, (9, 4, "start"))
        s += txt(fx(c) + dx, fy(f) + dy, "%s %.2f" % (n, f), 11, col, anchor=an)
    s += line(fx(128), fy(6.95), fx(256), fy(6.95), REV, 3) + txt(fx(180), fy(6.95) + 18, "BigGAN-deep 128 ~ 256 일, 6.95", 11, REV)
    s += txt(W / 2, H - 12, "A100 일을 2.2 배 해 V100 일로 바꿨다(원문 부록 F). ADM 쪽은 그 편의 V100 값을 옮긴 것", 11, INK2)
    svg("fig12_imagenet_cost", W, H, s, "ImageNet 비용")


def fig13():
    W, H = 820, 356
    cols = ["학습 처리량", "표본 @256", "표본 @512", "시간/에폭", "FID"]
    x0, x1, y0, y1 = 70, 790, 62, 280
    fy = lambda v: y1 - (y1 - y0) * v / 6.0
    s = txt(W / 2, 28, "표 6 — LDM-1 대비 배수. 원문: 「속도 적어도 2.7 배, FID 적어도 1.6 배」", 14, weight="600")
    s += frame(x0, y0, x1, y1, [], [0, 1, 2, 3, 4, 5, 6], lambda t: t, fy, None, "LDM-1 대비 배수")
    base = T6["LDM-1"]
    names = ["KL attn", "VQ attn", "VQ no attn"]
    for j, c in enumerate(cols):
        cx = x0 + 78 + j * 144
        for k, n in enumerate(names):
            v = T6[n][j]
            r = v / base[j] if j < 3 else base[j] / v
            x = cx - 54 + k * 36
            low = j == 4 and r < 1.6
            s += bar(x, fy(r), 32, y1 - fy(r), NO if low else [FWD, PURP, OK][k]) + txt(x + 16, fy(r) - 5, "%.2f" % r, 10, NO if low else INK)
        s += txt(cx, y1 + 16, c, 11, weight="600")
    s += line(x0 + 576, fy(1.6), x1, fy(1.6), NO, 1.2, dash="4,3")
    for k, n in enumerate(names):
        s += bar(x0 + 40 + k * 110, H - 26, 14, 10, [FWD, PURP, OK][k]) + txt(x0 + 60 + k * 110, H - 17, n, 11, anchor="start")
    s += txt(W - 14, H - 17, "빨강: 15.95 는 24.74 의 1.55 배로 1.6 아래. 파라미터 수는 고정. 내가 센 비", 10, NO, anchor="end")
    svg("fig13_tab6_ratios", W, H, s, "표 6 배수")


def fig14():
    rows = T7
    W, H = 800, 62 + 30 * len(rows) + 44
    x0, x1 = 190, 760
    fx = lambda v: x0 + (x1 - x0) * v / 32.0
    y0 = 52
    s = txt(W / 2, 28, "표 7 — 40 ~ 50% 가림 FID. 무엇이 같은 시험 집합에서 잰 값인가", 14, weight="600")
    for i, (n, v, k) in enumerate(rows):
        y = y0 + i * 30
        col = {"o": FWD, "r": CODE, "l": MUTED}[k]
        s += txt(x0 - 10, y + 15, n, 12, anchor="end")
        s += bar(x0, y + 3, fx(v) - x0, 18, col) + txt(fx(v) + 8, y + 16, "%.2f" % v, 11, col, anchor="start")
    y = H - 30
    s += bar(x0 - 150, y, 14, 10, FWD) + txt(x0 - 130, y + 9, "이 편이 잰 값", 11, anchor="start")
    s += bar(x0 - 40, y, 14, 10, CODE) + txt(x0 - 20, y + 9, "이 편의 시험 집합에서 다시 잰 LaMa", 11, anchor="start")
    s += bar(x0 + 220, y, 14, 10, MUTED) + txt(x0 + 240, y + 9, "다른 논문에서 옮긴 값(다른 시험 집합)", 11, anchor="start")
    svg("fig14_tab7_inpainting", W, H, s, "표 7")


def fig15():
    W, H = 800, 330
    x0, x1 = 230, 760
    fx = lambda v: x0 + (x1 - x0) * v / 8.0
    y0 = 62
    s = txt(W / 2, 26, "표 5 · 11 — 참조 통계를 검증과 학습 어디서 냈는가에 따라 FID 가 1.9 ~ 2.0 움직인다", 14, weight="600")
    for t in range(0, 9, 2):
        s += line(fx(t), y0 - 8, fx(t), y0 + 36 * len(SR), LINE, 1) + txt(fx(t), y0 + 36 * len(SR) + 16, "%d" % t, 10, MUTED)
    s += line(fx(5.2), y0 - 8, fx(5.2), y0 + 36 * len(SR), REV, 1.6, dash="5,4") + txt(fx(5.2), y0 - 14, "SR3 5.2 (참조 표시 없음)", 11, REV)
    for i, (n, a, b) in enumerate(SR):
        y = y0 + 18 + i * 36
        s += txt(x0 - 10, y + 4, n, 11, anchor="end")
        s += line(fx(a), y, fx(b), y, INK2, 1.4)
        s += circ(fx(a), y, 6, FWD, "#FFFFFF") + circ(fx(b), y, 6, CODE, "#FFFFFF")
        s += txt(fx(a), y - 10, "%.1f" % a, 10, FWD) + txt(fx(b), y - 10, "%.1f" % b, 10, CODE)
        print("    %-26s 차 %.1f" % (n, b - a))
    s += circ(x0, H - 18, 6, FWD, "#FFFFFF") + txt(x0 + 12, H - 14, "검증 분할 참조", 11, anchor="start")
    s += circ(x0 + 150, H - 18, 6, CODE, "#FFFFFF") + txt(x0 + 162, H - 14, "학습 분할 참조", 11, anchor="start")
    svg("fig15_sr_reference", W, H, s, "초해상도 참조")


def fig16():
    W, H = 780, 400
    x0, x1, y0, y1 = 80, 740, 56, 340
    fx = lambda v: x0 + (x1 - x0) * (math.log10(v) - 1.6) / (4 - 1.6)
    fy = lambda v: y1 - (y1 - y0) * (v - 8) / (30 - 8)
    s = txt(W / 2, 28, "표 2 — 글에서 이미지. 파라미터와 COCO FID (값은 표에 있는 그대로)", 14, weight="600")
    s += frame(x0, y0, x1, y1, [100, 300, 1000, 3000, 10000], [10, 15, 20, 25, 30], fx, fy, "파라미터 (백만, 로그)", "FID (30,000 표본, 아래가 좋다)", xfmt=lambda t: format(t, ","))
    off = {"GLIDE": (9, 4, "start"), "Make-A-Scene": (-9, 14, "end"), "CogView": (-9, -6, "end"), "LDM-KL-8-G": (-9, 4, "end")}
    for n, f, p in T2:
        col = FWD if n.startswith("LDM") else REV
        s += circ(fx(p), fy(f), 6, col, "#FFFFFF")
        dx, dy, an = off.get(n, (9, 4, "start"))
        s += txt(fx(p) + dx, fy(f) + dy, "%s %.2f" % (n, f), 11, col, anchor=an)
    s += line(fx(1450), fy(23.31) + 7, fx(1450), fy(12.63) - 8, FWD, 1.4, dash="4,3", marker="af")
    s += txt(fx(1450) + 9, fy(18), "안내 s = 1.5: 차 %.2f" % (23.31 - 12.63), 11, FWD, anchor="start")
    s += txt(W / 2, H - 12, "LDM 의 1.45B 중 UNet 은 872M(60.2%) 로 세어진다(내 셈, 가정 있음). 다른 편의 파라미터 구성은 이 표로 모른다", 11, INK2)
    svg("fig16_tab2_text", W, H, s, "표 2")


def fig17():
    W, H = 820, 360
    rows = [("LSUN 침실 LDM-4", 60, 29, ("ADM", 232)), ("CelebA-HQ LDM-4", 14.4, 29, None), ("FFHQ LDM-4", 26, 29, ("StyleGAN2", 32.13)),
            ("ImageNet LDM-4", 271, 29, ("ADM", 916)), ("ImageNet LDM-8", 79, 66, ("ADM", 916))]
    x0, x1 = 170, 700
    fx = lambda v: x0 + (x1 - x0) * v / 950.0
    y0 = 58
    s = txt(W / 2, 28, "표 18 — 첫 단계(VQGAN-f-4 29 · f-8 66 V100-일) 를 더하면", 14, weight="600")
    for i, (n, g, f, c) in enumerate(rows):
        y = y0 + i * 52
        s += txt(x0 - 10, y + 16, n, 12, anchor="end")
        s += bar(x0, y, fx(g) - x0, 14, FWD) + bar(fx(g), y, fx(g + f) - fx(g), 14, CODE)
        s += txt(fx(g + f) + 7, y + 11, "%g + %g = %g" % (g, f, g + f), 10, anchor="start")
        if c:
            s += bar(x0, y + 17, fx(c[1]) - x0, 14, REV)
            lab = "%s %g · 배수 %.2f -> %.2f" % (c[0], c[1], c[1] / g, c[1] / (g + f))
            if fx(c[1]) > 560:
                s += txt(fx(c[1]) - 6, y + 28, lab, 10, "#FFFFFF", anchor="end")
            else:
                s += txt(fx(c[1]) + 7, y + 28, lab, 10, REV, anchor="start")
    y = H - 24
    s += bar(x0, y, 14, 10, FWD) + txt(x0 + 20, y + 9, "LDM 생성 단계", 11, anchor="start")
    s += bar(x0 + 130, y, 14, 10, CODE) + txt(x0 + 150, y + 9, "첫 단계(여러 LDM 이 나눠 쓸 수 있다)", 11, anchor="start")
    s += bar(x0 + 400, y, 14, 10, REV) + txt(x0 + 420, y + 9, "비교 상대", 11, anchor="start")
    svg("fig17_compute_first_stage", W, H, s, "첫 단계 비용")


def fig18():
    W, H = 900, 372
    s = txt(W / 2, 28, "계보 — 이 편으로 모인 줄기와 남는 자리", 14, weight="600")

    def n(x, y, w, t, sub=None, f=NODE, st=INK2):
        return node(x, y, w, 46, t, sub, f, st, 11)

    s += n(250, 54, 190, "Transformer", "교차 주의, 인코더", PURP_SOFT, PURP)
    s += n(250, 122, 190, "VAE · VQ-VAE · VQGAN", "KL · 코드북 · 판별기", FWD_SOFT, FWD)
    s += n(250, 190, 190, "DDPM · ADM", "eps 예측 · UNet", CODE_SOFT, CODE)
    s += n(250, 258, 190, "DDIM · 분류기 없는 안내", "뽑는 걸음 · 안내", CODE_SOFT, CODE)
    s += n(20, 122, 190, "오토인코더", "좁은 층", FWD_SOFT, FWD)
    s += n(20, 190, 190, "LeNet · ResNet", "합성곱, 잔차 블록", NODE)
    s += line(210, 145, 250, 145, INK2, 1.3, marker="ai") + line(210, 213, 250, 213, INK2, 1.3, marker="ai")
    s += node(480, 118, 170, 80, "Latent Diffusion", "CVPR 2022", OK_SOFT, OK, 13)
    for y, ty in ((77, 132), (145, 150), (213, 166), (281, 184)):
        s += line(440, y, 480, ty, INK2, 1.3, marker="ai")
    s += n(690, 54, 190, "한계: 뽑기 속도", "5절, GAN 보다 느리다", NO_SOFT, NO)
    s += n(690, 122, 190, "한계: 픽셀 정밀도", "5절, f = 4 의 복원 상한", NO_SOFT, NO)
    s += n(690, 190, 190, "물음: 첫 단계의 몫", "5절 끝, 적대 + 가능도", NO_SOFT, NO)
    s += n(690, 258, 190, "이상 탐지 쪽", "재구성 오차(내 해석)", NODE)
    for y in (77, 145, 213, 281):
        s += line(650, 158, 690, y, INK2, 1.1, marker="ai")
    s += txt(W / 2, H - 16, "화살표는 원문이 인용한 관계다. VQ-VAE · VQGAN · ADM · 분류기 없는 안내는 이 저장소에 노트가 없다", 11, INK2)
    svg("fig18_lineage", W, H, s, "계보")


if __name__ == "__main__":
    print("그림을 만든다")
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10, fig11, fig12, fig13, fig14, fig15, fig16, fig17, fig18):
        f()
    un = unet(32, 4, 4, 320, (1, 2, 4, 4), 2, (32, 16, 8), lambda c: stblock(c, c, 1, 1280))
    for inner in (512, 1280):
        t = tau(1280, 32, 77, 30522, inner)
        print("    글 모델: UNet %.1fM + tau(내부 %d, 어휘 30,522 가정) %.1fM = %.1fM" % (un / 1e6, inner, t / 1e6, (un + t) / 1e6))
    plain = unet(32, 4, 4, 256, (1, 2, 4), 2, (32, 16, 8), lambda c: stblock(c, c, 1, 512, gated=False)) + CE
    print("    표 13 LDM-8, 보통 MLP 라면 %.2fM (원문 395M)" % (plain / 1e6))
    print("    표 15 초해상도, 채널 192 + 32 · 16 · 8 주의면 %.2fM (원문 169M)" % (unet(64, 6, 3, 192, (1, 2, 2, 4), 2, (32, 16, 8), attn) / 1e6))
    print("    4.5절 big, 채널 256 · 곱 1,2,3,4 · 3 층 주의 · BigGAN 블록이면 %.1fM (원문 387M)" % (unet(64, 7, 3, 256, (1, 2, 3, 4), 2, (32, 16, 8), attn, updown=True) / 1e6))
    print("    ADM 무조건 256(채널 256, 곱 1,1,2,2,4,4, 주의 32 16 8, 출력 6) %.2fM (표 18 552M)" % (unet(256, 3, 6, 256, (1, 1, 2, 2, 4, 4), 2, (32, 16, 8), attn, updown=True, ss=True) / 1e6))
    # 표 18 로 낸 학습 속도
    for n, v, it, b in [("침실", 60, 1.9e6, 48), ("CelebA", 14.4, 410e3, 48), ("FFHQ", 26, 635e3, 42), ("ImageNet LDM-8", 79, 2.9e6, 64), ("ImageNet LDM-4", 271, 178e3, 1200)]:
        d = v / 2.2
        print("    표 18 %-16s V100 %g = A100 %.1f 일, 걸음/초 %.3f, 장/초 %.1f, 본 장수 %.1fM" % (n, v, d, it / (d * 86400), it * b / (d * 86400), it * b / 1e6))
    # 표 6 의 곱
    for n, r in T6.items():
        print("    표 6 %-11s 처리량 x 시간/에폭 = %.0f" % (n, r[0] * r[3] * 3600))
