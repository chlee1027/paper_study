# -*- coding: utf-8 -*-
"""ViT 노트(Dosovitskiy 외, An Image is Worth 16x16 Words, ICLR 2021)의 그림 열여덟을 만든다.

색과 글꼴은 저장소의 앞선 노트 그림과 맞췄다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

계산으로 원문을 확인하는 그림이 여럿이다 — 3(표 1 의 파라미터를 짜임에서 다시 세기), 4 · 5(입력 크기 · 조각 크기별
조각 수와 블록 곱셈-덧셈의 n² 몫), 6(표 2 의 차), 9(데이터 크기마다 갱신 횟수), 12(표 6 으로 잰 「같은 성능의 계산 배수」),
16(균일 주의의 거리). 계산한 값은 돌릴 때 화면에도 찍는다.

원문 표의 수는 T2 · T5 · T6 · T7 · T8 · T9 상수에 옮겨 적었다(6 · 15 · 16 · 17 · 20 쪽). 원문 그림 2 · 3 · 4 · 8 · 10 ·
11 · 12 의 값은 **PDF 안의 벡터 좌표에서 읽은 값**이고 FIG2 · FIG3 · FIG4 · FIG8 · FIG10 · FIG11 · FIG12 상수에 있다.
읽는 방법은 눈금 선 좌표로 축을 맞춘 뒤 표식 상자의 가운데를 값으로 바꾼 것이다. 그림 3 의 점 12 개가 표 5 와 소수 둘째
자리까지 맞아 읽기 오차는 0.01 안이다. 원문 그림 1 · 6 · 7 은 crop_paper_figures.py 가 잘라 png 로 둔다.
"""
import io, os, math

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
# 표 1 (5 쪽): 이름 -> (층 L, 폭 D, MLP 폭 M, 머리 수, 원문 Params 백만)
T1 = {"B": (12, 768, 3072, 12, 86), "L": (24, 1024, 4096, 16, 307), "H": (32, 1280, 5120, 16, 632)}

# 표 2 (6 쪽): 행 -> H/14 JFT, L/16 JFT, L/16 I21k, BiT-L (값, ±). BiT ReaL 은 ± 없음, Noisy Student 는 ImageNet 88.4/88.5 · ReaL 90.55 만
T2 = [("ImageNet",      (88.55, 0.04), (87.76, 0.03), (85.30, 0.02), (87.54, 0.02)),
      ("ImageNet ReaL", (90.72, 0.05), (90.54, 0.03), (88.62, 0.05), (90.54, None)),
      ("CIFAR-10",      (99.50, 0.06), (99.42, 0.03), (99.15, 0.03), (99.37, 0.06)),
      ("CIFAR-100",     (94.55, 0.04), (93.90, 0.05), (93.25, 0.05), (93.51, 0.08)),
      ("Pets",          (97.56, 0.03), (97.32, 0.11), (94.67, 0.15), (96.62, 0.23)),
      ("Flowers-102",   (99.68, 0.02), (99.74, 0.00), (99.61, 0.02), (99.63, 0.03)),
      ("VTAB (19)",     (77.63, 0.23), (76.28, 0.46), (72.72, 0.21), (76.29, 1.70))]
T2_COST = {"H/14 JFT": 2500, "L/16 JFT": 680, "L/16 I21k": 230, "BiT-L": 9900, "Noisy Student": 12300}

# 표 5 (15 쪽) 의 ImageNet 행만 (그림 3 과 맞대는 데 쓴다): 사전학습 -> 모델 -> 값
T5_IN = {"ImageNet":     {"B/16": 77.91, "B/32": 73.38, "L/16": 76.53, "L/32": 71.16, "H/14": None},
         "ImageNet-21k": {"B/16": 83.97, "B/32": 81.28, "L/16": 85.15, "L/32": 80.99, "H/14": 85.13},
         "JFT-300M":     {"B/16": 84.15, "B/32": 80.73, "L/16": 87.12, "L/32": 84.37, "H/14": 88.04}}

# 표 6 (15 쪽): 이름, 에폭, ImageNet, ReaL, CIFAR-10, CIFAR-100, Pets, Flowers, exaFLOPs
T6 = [("ViT-B/32", 7, 80.73, 86.27, 98.61, 90.49, 93.40, 99.27, 164),
      ("ViT-B/16", 7, 84.15, 88.85, 99.00, 91.87, 95.80, 99.56, 743),
      ("ViT-L/32", 7, 84.37, 88.28, 99.19, 92.52, 95.83, 99.45, 574),
      ("ViT-L/16", 7, 86.30, 89.43, 99.38, 93.46, 96.81, 99.66, 2586),
      ("ViT-L/16", 14, 87.12, 89.99, 99.38, 94.04, 97.11, 99.56, 5172),
      ("ViT-H/14", 14, 88.08, 90.36, 99.50, 94.71, 97.11, 99.71, 12826),
      ("R50x1", 7, 77.54, 84.56, 97.67, 86.07, 91.11, 94.26, 150),
      ("R50x2", 7, 82.12, 87.94, 98.29, 89.20, 93.43, 97.02, 592),
      ("R101x1", 7, 80.67, 87.07, 98.48, 89.17, 94.08, 95.95, 285),
      ("R152x1", 7, 81.88, 87.96, 98.82, 90.22, 94.17, 96.94, 427),
      ("R152x2", 7, 84.97, 89.69, 99.06, 92.05, 95.37, 98.62, 1681),
      ("R152x2", 14, 85.56, 89.89, 99.24, 91.92, 95.75, 98.75, 3362),
      ("R200x3", 14, 87.22, 90.15, 99.34, 93.53, 96.32, 99.04, 10212),
      ("R50+B/32", 7, 84.90, 89.15, 99.01, 92.24, 95.75, 99.46, 315),
      ("R50+B/16", 7, 85.58, 89.65, 99.14, 92.63, 96.65, 99.40, 855),
      ("R50+L/32", 7, 85.68, 89.04, 99.24, 92.93, 96.97, 99.43, 725),
      ("R50+L/16", 7, 86.60, 89.72, 99.18, 93.64, 97.03, 99.40, 2704),
      ("R50+L/16", 14, 87.12, 89.76, 99.31, 93.89, 97.36, 99.11, 5165)]

# 표 8 (17 쪽): ViT-B/16, ImageNet 5-shot 선형. 행 -> (입력에 한 번, 층마다, 층마다 공유)
T8 = [("없음", 0.61382, None, None), ("1-D", 0.64206, 0.63964, 0.64292),
      ("2-D", 0.64001, 0.64046, 0.64022), ("상대", 0.64032, None, None)]

# 표 9 (20 쪽). 앞 7 칸 Natural, 다음 4 칸 Specialized, 다음 8 칸 Structured, 끝 칸 평균
T9 = {"H/14 JFT":  [95.3, 85.5, 75.2, 99.7, 97.2, 65.0, 88.9, 83.3, 96.7, 91.4, 76.6, 91.7, 63.8, 53.1, 79.4, 63.3, 84.5, 33.2, 51.2, 77.6],
      "L/16 JFT":  [95.4, 81.9, 74.3, 99.7, 96.7, 63.5, 87.4, 83.6, 96.5, 89.7, 77.1, 86.4, 63.1, 49.7, 74.5, 60.5, 82.2, 36.2, 51.1, 76.3],
      "L/16 I21k": [90.8, 84.1, 74.1, 99.3, 92.7, 61.0, 80.9, 82.5, 95.6, 85.2, 75.3, 70.3, 56.1, 41.9, 74.7, 64.9, 79.9, 30.5, 41.7, 72.7]}

# ── 벡터 좌표에서 읽은 값 ────────────────────────────────────────────────────
# 그림 2 (6 쪽): 묶음 -> H/14, BiT-L, VIVI, S4L
FIG2 = {"VTAB (19)": (77.63, 76.21, 70.40, 67.50), "Natural (7)": (86.67, 85.53, 72.20, 73.09),
        "Specialized (4)": (87.01, 86.85, 83.70, 83.25), "Structured (8)": (65.02, 62.72, 62.30, 54.83)}
# 그림 3 (7 쪽). 점은 표 5 와 같고 H/14 JFT 만 88.28(표 5 는 88.04). BiT 띠의 위 · 아래 끝
FIG3_H14 = 88.28
FIG3_BIT = {"low": (76.81, 80.03, 79.02), "high": (81.30, 85.39, 87.76)}
# 그림 4 (7 쪽): 9M, 30M, 90M, 300M
FIG4 = {"L/16": (41.90, 57.84, 70.03, 71.56), "L/32": (36.16, 53.64, 64.04, 65.37), "B/32": (37.96, 52.91, 54.65, 55.24),
        "b/32": (37.37, 40.72, 41.17, 41.95), "R50x1": (47.83, 50.77, 51.88, 52.03), "R152x2": (52.69, 66.87, 68.93, 69.32)}
# 그림 8 왼쪽 (16 쪽): (상대 계산, ImageNet 5-shot)
FIG8 = {"전부": [(0.16, 0.229), (1.0, 0.436), (8.89, 0.619)],
        "깊이": [(0.27, 0.139), (0.51, 0.303), (1.0, 0.436), (1.97, 0.532), (3.06, 0.576), (6.09, 0.611)],
        "조각 크기": [(0.27, 0.294), (0.51, 0.360), (1.0, 0.436), (2.0, 0.485), (4.1, 0.531)],
        "MLP 폭": [(1.0, 0.436), (1.53, 0.484), (3.03, 0.527)],
        "폭": [(0.26, 0.326), (0.57, 0.396), (1.0, 0.436), (1.74, 0.468), (3.06, 0.490)]}
# 그림 10 (18 쪽): 층 0~23 의 (최소, 중앙, 최대), 층마다 머리 16 개
FIG10 = {"ViT-L/16": [(8.0, 51.6, 110.0), (18.9, 71.9, 111.6), (17.2, 69.3, 112.0), (24.1, 59.4, 115.7), (30.2, 65.0, 124.7), (41.1, 72.8, 117.2),
                      (59.7, 86.1, 111.1), (59.1, 84.1, 127.2), (64.1, 90.7, 113.6), (81.1, 98.1, 111.3), (87.8, 98.2, 114.8), (92.3, 104.3, 114.6),
                      (108.5, 111.4, 115.2), (103.7, 111.1, 113.6), (109.0, 111.2, 117.2), (107.1, 109.5, 114.0), (108.6, 110.1, 112.1), (108.8, 110.0, 111.7),
                      (109.3, 110.1, 111.9), (99.0, 111.0, 111.9), (105.2, 111.1, 111.8), (109.5, 112.8, 113.3), (111.8, 115.0, 117.7), (114.4, 115.8, 120.3)],
         "R50x1 + ViT-L/16": [(36.5, 73.2, 104.1), (47.5, 75.3, 113.2), (40.2, 83.8, 113.0), (55.2, 86.9, 112.9), (53.2, 95.5, 114.8), (63.4, 96.7, 115.4),
                              (69.9, 92.0, 131.2), (76.3, 93.0, 118.8), (83.0, 102.8, 119.1), (93.2, 113.0, 115.9), (105.4, 112.2, 116.7), (110.1, 112.1, 116.4),
                              (90.4, 111.2, 114.4), (109.9, 111.2, 115.0), (109.0, 110.5, 112.2), (109.8, 111.5, 114.1), (110.4, 111.2, 114.1), (110.5, 111.8, 115.2),
                              (111.1, 112.8, 114.7), (108.5, 112.8, 115.4), (107.6, 113.2, 115.3), (100.6, 113.4, 114.4), (111.3, 114.4, 116.5), (114.5, 116.8, 118.2)]}
# 그림 11 왼쪽 (19 쪽): 입력 64 · 128 · 224 · 384 · 512 의 최고 추론 속도(이미지/초/코어). H/14 의 입력은 70 · 126 · 224 · 378 · 518
FIG11 = {"R50x1": (21087, 6320, 2163, 766, 436.5), "R50x2": (8890, 2567, 884.7, 317.1, 178.0),
         "B/32": (18085, 6539, 2860, 982.6, 497.0), "L/32": (6326, 2232, 909.5, 307.8, 163.3),
         "B/16": (6737, 2229, 861.2, 244.6, 95.6), "L/16": (2265, 750.1, 279.8, 79.5, 32.2),
         "H/14": (877.6, 346.0, 87.3, 34.8, 14.8), "R152x4": (1097, 317.1, 110.7, 40.4, 22.5)}
FIG11_X = (64, 128, 224, 384, 512)
FIG11_XH = (70, 126, 224, 378, 518)


# ── 계산 ──────────────────────────────────────────────────────────────────
def parts(D, M, L, P, res, head=0):
    """조각 투영(바이어스 포함) · 분류 토큰 · 자리 임베딩 · 블록 L 개 · 끝 LN · 머리. 식 (1)~(8) 에서 센다."""
    n = (res // P) ** 2
    emb = P * P * 3 * D + D
    cls = D
    pos = (n + 1) * D
    msa = 4 * D * D + 4 * D            # q, k, v, 출력 투영 넷, 바이어스 포함
    mlp = 2 * D * M + M + D
    ln = 2 * 2 * D                     # LN 둘, 각각 스케일 + 이동
    block = msa + mlp + ln
    final = 2 * D
    h = D * head + head if head else 0
    return dict(n=n, emb=emb, cls=cls, pos=pos, block=block, blocks=block * L, final=final, head=h,
                total=emb + cls + pos + block * L + final + h)


def macs(n, D, M):
    """블록 하나의 곱셈-덧셈: 주의 2n²D, 투영 4nD², MLP 2nDM."""
    return 2 * n * n * D, 4 * n * D * D, 2 * n * D * M


def model_macs(L, D, M, P, res):
    n0 = (res // P) ** 2
    a, b, c = macs(n0 + 1, D, M)
    return L * (a + b + c) + n0 * P * P * 3 * D


print("\n[표 1] 파라미터 다시 세기(224 입력)")
ROWS1 = []
for name, v, P in (("B/16", "B", 16), ("B/32", "B", 32), ("L/16", "L", 16), ("L/32", "L", 32), ("H/14", "H", 14)):
    L, D, M, _, t1 = T1[v]
    a, b = parts(D, M, L, P, 224), parts(D, M, L, P, 224, 1000)
    ROWS1.append((name, a, b, t1))
    print("  %-5s 머리 없음 %11d  머리 1000 %11d  표 1 %dM" % (name, a["total"], b["total"], t1))

print("\n[n 과 n² 몫] 몫 = n / (n + 2D + M)")
for name, L, D, M, P, res in (("B/16", 12, 768, 3072, 16, 224), ("B/32", 12, 768, 3072, 32, 224), ("B/16", 12, 768, 3072, 16, 384),
                              ("L/16", 24, 1024, 4096, 16, 224), ("L/16", 24, 1024, 4096, 16, 384), ("L/16", 24, 1024, 4096, 16, 512),
                              ("H/14", 32, 1280, 5120, 14, 224), ("H/14", 32, 1280, 5120, 14, 378), ("H/14", 32, 1280, 5120, 14, 518)):
    n = (res // P) ** 2 + 1
    a, b, c = macs(n, D, M)
    print("  %-5s %3d  n=%5d  주의 %8.1fM 투영 %8.1fM MLP %8.1fM  n² 몫 %5.1f%%  모델 %6.1fG" % (
        name, res, n, a / 1e6, b / 1e6, c / 1e6, 100.0 * a / (a + b + c), model_macs(L, D, M, P, res) / 1e9))

print("\n[표 6 exaFLOPs 를 이미지당으로] 303M 장 x 에폭")
for name, L, D, M, P, ep, ex in (("B/32", 12, 768, 3072, 32, 7, 164), ("B/16", 12, 768, 3072, 16, 7, 743), ("L/32", 24, 1024, 4096, 32, 7, 574),
                                 ("L/16", 24, 1024, 4096, 16, 7, 2586), ("L/16", 24, 1024, 4096, 16, 14, 5172), ("H/14", 32, 1280, 5120, 14, 14, 12826)):
    per = ex * 1e18 / (303e6 * ep)
    m = model_macs(L, D, M, P, 224)
    print("  %-5s 에폭 %2d  이미지당 %7.1fG  내 앞먹임 곱셈-덧셈 %6.1fG  배수 %.1f" % (name, ep, per / 1e9, m / 1e9, per / m))

print("\n[표 2 차] ViT - BiT-L")
DIFF2 = []
for r in T2:
    d_l = r[2][0] - r[4][0]
    d_h = r[1][0] - r[4][0]
    DIFF2.append((r[0], d_h, d_l, r[1][1], r[2][1], r[4][1]))
    print("  %-14s H/14 %+.2f  L/16 %+.2f  (± %s, %s, %s)" % (r[0], d_h, d_l, r[1][1], r[2][1], r[4][1]))

print("\n[표 9 묶음 평균]")
for k, v in T9.items():
    nat, spe, stc = sum(v[:7]) / 7, sum(v[7:11]) / 4, sum(v[11:19]) / 8
    print("  %-10s Natural %.2f  Specialized %.2f  Structured %.2f  19 평균 %.2f (표 %.1f)" % (k, nat, spe, stc, sum(v[:19]) / 19, v[19]))
print("  그림 2 BiT 막대로 낸 19 평균 %.2f (표 2 는 76.29)" % ((7 * 85.53 + 4 * 86.85 + 8 * 62.72) / 19))

print("\n[갱신 횟수] 배치 4096")
STEPS = []
for ds, N, ep in (("ImageNet", 1.3e6, 300), ("ImageNet-21k", 14e6, 30), ("ImageNet-21k", 14e6, 90), ("JFT-300M", 303e6, 7), ("JFT-300M", 303e6, 14)):
    STEPS.append((ds, N, ep, N * ep / 4096, N * ep))
    print("  %-13s %5.1fM 장 x %3d 에폭 = %7.0f 걸음, 본 이미지 %6.2f 억 장" % (ds, N / 1e6, ep, N * ep / 4096, N * ep / 1e8))
for sub in (9e6, 30e6, 90e6, 303e6):
    print("  JFT 부분 %4.0fM x 7 에폭 = %7.0f 걸음 (예열 1 만 걸음의 몫 %.0f%%)" % (sub / 1e6, sub * 7 / 4096, 100 * 1e4 / (sub * 7 / 4096)))

print("\n[표 6 Average-5 와 같은 성능의 계산 배수]")


def avg5(r):
    return (r[2] + r[4] + r[5] + r[6] + r[7]) / 5.0


def frontier(rows, f):
    pts = sorted((r[8], f(r)) for r in rows)
    out = []
    best = -1
    for c, a in pts:
        if a > best:
            out.append((c, a))
            best = a
    return out


def needed(front, a):
    if a <= front[0][1]:
        return None, "아래"
    for (c0, a0), (c1, a1) in zip(front, front[1:]):
        if a0 <= a <= a1:
            t = (a - a0) / (a1 - a0)
            return 10 ** (math.log10(c0) + t * (math.log10(c1) - math.log10(c0))), "안"
    return None, "위"


VITS = [r for r in T6 if r[0].startswith("ViT")]
RES = [r for r in T6 if r[0].startswith("R") and "+" not in r[0]]
HYB = [r for r in T6 if "+" in r[0]]
RATIO = {"avg": [], "in": []}
for key, f in (("avg", avg5), ("in", lambda r: r[2])):
    fr = frontier(RES, f)
    print("  [%s] ResNet 앞줄 %s" % (key, [(c, round(a, 2)) for c, a in fr]))
    for r in VITS:
        c, where = needed(fr, f(r))
        val = None if c is None else c / r[8]
        RATIO[key].append((r[0] + "-" + str(r[1]), r[8], f(r), val, where))
        print("    %-12s 계산 %6d 값 %.2f  ResNet 필요 %s  배수 %s" % (
            r[0] + "-" + str(r[1]), r[8], f(r), "%.0f" % c if c else where, "%.2f" % val if val else "-"))

print("\n[균일 주의의 거리] 조각 가운데 사이 평균 거리")


def grid_mean(g, step):
    pts = [(i * step, j * step) for i in range(g) for j in range(g)]
    s = 0.0
    for a in pts:
        for b in pts:
            s += math.hypot(a[0] - b[0], a[1] - b[1])
    return s / len(pts) ** 2


UNIF = grid_mean(14, 16)
print("  14x14 x 16px = %.2f, 연속 정사각형 0.5214 x 224 = %.2f" % (UNIF, 0.5214054 * 224))
late = sorted(v[1] for v in FIG10["ViT-L/16"][12:])
print("  ViT-L/16 층 12~23 의 층별 중앙값 범위 %.1f ~ %.1f" % (late[0], late[-1]))

print("\n[그림 8 기준 모델] 8 층, D 1024, M 2048, 패치 32, 224 입력")
BASE = model_macs(8, 1024, 2048, 32, 224)
print("  곱셈-덧셈 %.3fG" % (BASE / 1e9))
for L_ in (2, 4, 8, 16, 24, 32, 48, 64):
    print("  %2d 층: 상대 계산 %.2f" % (L_, model_macs(L_, 1024, 2048, 32, 224) / float(BASE)))
pa, pb = parts(1024, 2048, 8, 32, 224), parts(1024, 2048, 8, 16, 224)
print("  파라미터 패치 32 %d, 패치 16 %d, 차 %d (%.1f%%)" % (pa["total"], pb["total"], pb["total"] - pa["total"], 100.0 * (pb["total"] - pa["total"]) / pa["total"]))

print("\n[그림 11 기울기] log(속도) / log(입력), 384->512")
SLOPE = {}
for k, v in FIG11.items():
    xs = FIG11_XH if k == "H/14" else FIG11_X
    SLOPE[k] = (math.log(v[3] / v[4]) / math.log(float(xs[4]) / xs[3]), math.log(v[2] / v[4]) / math.log(float(xs[4]) / xs[2]))
    print("  %-7s 384->512 %.2f   224->512 %.2f" % (k, SLOPE[k][0], SLOPE[k][1]))


# ── 그림 1: 입력에서 표현까지 ───────────────────────────────────────────────
def fig01():
    W, H = 980, 370
    s = defs() + txt(W / 2, 26, "그림 1. ViT-B/16 에 224 x 224 x 3 이 들어가면 — 모양을 따라간다 (식 1 ~ 4)", 15, weight="700")
    # 이미지 격자
    x0, y0, cell = 34, 66, 11
    for i in range(14):
        for j in range(14):
            shade = FWD_SOFT if (i + j) % 2 else NODE
            s += '<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="0.6"/>' % (x0 + j * cell, y0 + i * cell, cell, cell, shade, LINE)
    s += '<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="1.4"/>' % (x0 + 5 * cell, y0 + 5 * cell, cell, cell, CODE_SOFT, CODE)
    s += lines_at(x0, y0 + 14 * cell + 20, [("입력 224 x 224 x 3", INK, "700"), "P = 16 조각 14 x 14", "N = HW / P² = 196"], 11.5, 17)
    s += line(200, 140, 232, 140, INK2, 1.4, marker="ai")
    # 평탄화
    s += box(236, 104, 124, 72, CODE_SOFT, CODE)
    s += lines_at(298, 128, [("조각을 펴기", INK, "700"), "16 x 16 x 3 = 768", "x_p: 196 x 768"], 11.5, 18, "middle")
    s += line(360, 140, 392, 140, INK2, 1.4, marker="ai")
    # E
    s += box(396, 104, 116, 72, FWD_SOFT, FWD)
    s += lines_at(454, 128, [("학습되는 E", INK, "700"), "768 -> D = 768", "590,592 개"], 11.5, 18, "middle")
    s += line(512, 140, 544, 140, INK2, 1.4, marker="ai")
    # cls + pos
    s += box(548, 104, 128, 72, PURP_SOFT, PURP)
    s += lines_at(612, 122, [("[class] 앞에 + E_pos", INK, "700"), "z_0: 197 x 768", "분류 토큰 768 개", "자리 151,296 개"], 11, 16, "middle")
    s += line(676, 140, 708, 140, INK2, 1.4, marker="ai")
    # encoder
    s += box(712, 92, 112, 96, REV_SOFT, REV)
    s += lines_at(768, 118, [("블록 x 12", INK, "700"), "식 (2), (3)", "모양 그대로", "197 x 768"], 11.5, 18, "middle")
    s += line(824, 140, 852, 140, INK2, 1.4, marker="ai")
    s += box(856, 104, 100, 72, OK_SOFT, OK)
    s += lines_at(906, 128, [("LN(z_L^0)", INK, "700"), "y: 768", "자리 0 하나만"], 11.5, 18, "middle")
    # 아래 설명
    s += box(236, 214, 720, 132, NODE, LINE)
    s += lines_at(252, 238, [
        ("머리는 단계마다 다르다", INK, "700"),
        "사전학습: y -> 은닉층 하나짜리 MLP -> 부류 (본문 3.1절, 부록 B.1.1 은 「선형 층 둘」).",
        "미세조정: 그 머리를 통째로 버리고 0 으로 시작하는 D x K 선형 층 하나.",
        ("합성곱 없이 간다고 적지만, 조각마다 같은 E 를 쓰는 것은 커널 = 보폭 = 16 인 합성곱 한 번과 계산이 같다(내 해석).", INK2),
        ("2 차원 정보를 사람이 넣는 자리는 원문이 꼽은 둘 — 조각 자르기와 미세조정 때 자리 임베딩 보간 — 뿐이다.", INK2)], 12, 21)
    svg("fig01_patch_pipeline", W, H, s, "ViT-B/16 의 입력에서 표현까지 모양 변화")


# ── 그림 2: 블록 ───────────────────────────────────────────────────────────
def fig02():
    W, H = 900, 400
    s = defs() + txt(W / 2, 26, "그림 2. 블록 — 정규화 자리가 원 Transformer 와 다르다", 15, weight="700")

    def stack(x, title, sub, items, fill, stroke):
        o = txt(x + 130, 56, title, 13, weight="700") + txt(x + 130, 74, sub, 11, fill=MUTED)
        y = 340
        o += txt(x + 130, 390, "입력", 11, fill=MUTED)
        last = 378
        for t, kind in items:
            if kind == "add":
                o += circ(x + 130, y, 12, NODE, INK) + txt(x + 130, y + 4, "+", 13)
                o += line(x + 130, last, x + 130, y + 12, INK2, 1.2, marker="ai")
                last = y - 12
                y -= 40
            else:
                o += box(x + 60, y - 14, 140, 28, fill if kind == "n" else NODE, stroke if kind == "n" else INK)
                o += txt(x + 130, y + 4, t, 12)
                o += line(x + 130, last, x + 130, y + 14, INK2, 1.2, marker="ai")
                last = y - 14
                y -= 42
        return o
    s += stack(50, "ViT 인코더 블록 (식 2, 3)", "정규화 먼저, 지름길은 정규화 밖", [
        ("LN", "n"), ("다중 머리 주의", "o"), ("", "add"), ("LN", "n"), ("MLP (GELU)", "o"), ("", "add")], CODE_SOFT, CODE)
    s += stack(470, "원 Transformer 인코더 층", "더한 뒤 정규화, 지름길이 정규화를 지난다", [
        ("다중 머리 주의", "o"), ("", "add"), ("LN", "n"), ("앞먹임 (ReLU)", "o"), ("", "add"), ("LN", "n")], CODE_SOFT, CODE)
    s += lines_at(322, 130, [("ViT 의 길", INK, "700"), "z' = MSA(LN(z)) + z", "z = MLP(LN(z')) + z'", "", ("Transformer 의 길", INK, "700"), "z' = LN(z + MSA(z))", "z = LN(z' + FF(z'))"], 11.5, 20)
    svg("fig02_block_compare", W, H, s, "ViT 블록과 원 Transformer 층의 정규화 자리 비교")


# ── 그림 3: 표 1 다시 세기 ─────────────────────────────────────────────────
def fig03():
    W, H = 980, 318
    s = txt(W / 2, 26, "그림 3. 표 1 의 Params 를 짜임에서 다시 세기 (224 입력, 내가 센 것, 단위 백만)", 15, weight="700")
    rows = [["모델", "E", "분류+자리", "블록 L 개", "끝 LN", "머리 없음", "머리 1000", "표 1", "맞는가"]]
    verdict = {"B/16": ("머리 없음이면 86", OK), "B/32": ("안 맞는다", NO), "L/16": ("안 맞는다 (3.0~3.7 모자람)", NO),
               "L/32": ("머리 1000 이면 307", OK), "H/14": ("머리 1000 이면 632", OK)}
    for name, a, b, t1 in ROWS1:
        v, c = verdict[name]
        rows.append([name, "%.3f" % (a["emb"] / 1e6), "%.3f" % ((a["cls"] + a["pos"]) / 1e6), "%.3f" % (a["blocks"] / 1e6), "%.3f" % (a["final"] / 1e6),
                     "%.3f" % (a["total"] / 1e6), "%.3f" % (b["total"] / 1e6), (str(t1), CODE, "700", CODE_SOFT), (v, c, "700", None)])
    s += table(20, 48, [64, 70, 90, 92, 62, 94, 94, 60, 314], rows, 28, 12)
    s += lines_at(24, 238, [
        ("한 줄 안에서는 패치 크기가 파라미터를 바꾼다. 표 1 은 패치 크기와 머리를 적지 않아 줄마다 어느 모델인지 정해지지 않는다.", INK2),
        ("시험한 조합(패치 14 · 16 · 32, 입력 224 · 384, 머리 없음 · 1,000 · 18k · 21k, 은닉층 유무, 투영 바이어스 유무) 안에서 307 은 패치 32 에서만 ±1 안에 든다.", INK2),
        ("머리 1000 칸의 다섯 수는 torchvision 0.26 의 같은 이름 모델을 만들어 센 값과 정수까지 같다.", OK, "700")], 11.5, 22)
    svg("fig03_param_parts", W, H, s, "표 1 파라미터 수를 부분별로 다시 센 표")


# ── 그림 4: 조각 수 ────────────────────────────────────────────────────────
def fig04():
    W, H = 760, 290
    s = txt(W / 2, 26, "그림 4. 입력 크기와 패치 크기가 조각 수 N 을 정한다 (N = HW / P²)", 15, weight="700")
    sizes = [224, 384, 512, 518]
    rows = [["입력 / 패치"] + ["P = %d" % p for p in (14, 16, 32)]]
    for r in sizes:
        row = [("%d" % r, INK, "700", None)]
        for p in (14, 16, 32):
            if r % p:
                row.append(("%.2f² = 안 나뉜다" % (float(r) / p), NO, None, NO_SOFT))
            else:
                g = r // p
                row.append(("%d² = %s" % (g, format(g * g, ",")), INK2, None, None))
        rows.append(row)
    s += table(60, 48, [130, 180, 180, 150], rows, 30, 12.5)
    s += lines_at(60, 228, [
        ("표 2 의 미세조정은 L/16 이 512, H/14 가 518 이다. 표 5 는 「384」 라 적는데 384 는 14 로 나뉘지 않는다.", INK2),
        ("그림 11 의 H/14 선은 입력 70 · 126 · 224 · 378 · 518 에 찍혀 있다(벡터 좌표로 읽음). 378 = 27 x 14.", CODE, "700"),
        ("픽셀 하나를 자리 하나로 두면 N = 50,176. 16 조각으로 묶어 n 은 1/256, n² 은 1/65,536 이 된다.", INK2)], 12, 22)
    svg("fig04_seq_len", W, H, s, "입력 크기와 패치 크기별 조각 수")


# ── 그림 5: n² 몫 ──────────────────────────────────────────────────────────
def fig05():
    W, H = 900, 400
    x0, y0, x1, y1 = 76, 58, 560, 340
    lo, hi = 1.0, 5.0
    fx = lambda v: x0 + (math.log10(v) - lo) / (hi - lo) * (x1 - x0)
    fy = lambda v: y1 - v / 100.0 * (y1 - y0)
    s = txt(W / 2, 26, "그림 5. 블록 곱셈-덧셈에서 n² 항의 몫 — 원문 표현 「bi-quadratic」 이 어디서 시작하나 (내가 센 것)", 14.5, weight="700")
    s += axes(x0, y0, x1, y1, [10, 100, 1000, 10000, 100000], [0, 25, 50, 75, 100], fx, fy, "조각 수 n (분류 토큰 포함, 로그)", "n² 항의 몫 (%)", xfmt=lambda v: format(int(v), ","))
    for name, D, c in (("B (D = 768)", 768, FWD), ("L (D = 1024)", 1024, REV), ("H (D = 1280)", 1280, PURP)):
        pts = []
        for k in range(0, 81):
            n = 10 ** (lo + (hi - lo) * k / 80.0)
            pts.append((fx(n), fy(100.0 * n / (n + 6 * D))))
        s += polyline(pts, c, 2)
    marks = [("B/32 224", 50, 768, FWD), ("B/16 224", 197, 768, FWD), ("L/16 384", 577, 1024, REV), ("L/16 512", 1025, 1024, REV), ("H/14 518", 1370, 1280, PURP)]
    for t, n, D, c in marks:
        v = 100.0 * n / (n + 6 * D)
        s += circ(round(fx(n), 1), round(fy(v), 1), 4, c, c)
    s += box(580, 62, 300, 276, NODE, LINE)
    s += lines_at(594, 86, [
        ("블록 하나의 셈 (M = 4D)", INK, "700"),
        "주의      2n²D",
        "투영      4nD²  (q, k, v, 출력)",
        "MLP       2nDM = 8nD²",
        "몫 = n / (n + 2D + M) = n / (n + 6D)",
        "",
        ("찍힌 점의 몫", INK, "700")] + [
        "%s  n = %s  %.1f%%" % (t, format(n, ","), 100.0 * n / (n + 6 * D)) for t, n, D, c in marks] + [
        "",
        ("같아지는 n = 6D: B 4,608, L 6,144, H 7,680", NO, "700")], 11.5, 19)
    svg("fig05_mac_share", W, H, s, "조각 수에 따른 n 제곱 항의 몫")


# ── 그림 6: 표 2 의 차 ─────────────────────────────────────────────────────
def fig06():
    W, H = 900, 430
    x0, x1 = 170, 650
    lo, hi = -2.0, 3.0
    fx = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    s = txt(W / 2, 26, "그림 6. 표 2 — ViT 값에서 BiT-L 값을 뺀 차 (백분율 점)", 15, weight="700")
    s += txt(W / 2, 46, "가로 막대는 ViT 쪽 표준편차와 BiT 쪽 표준편차의 제곱합 제곱근 (세 번의 미세조정이므로 사전학습의 흩어짐은 들어 있지 않다)", 10.5, fill=MUTED)
    ytop = 76
    rowh = 44
    for t in (-2, -1, 0, 1, 2, 3):
        s += line(fx(t), ytop - 10, fx(t), ytop + rowh * 7, LINE if t else INK2, 0.8 if t else 1.3, dash="2 3" if t else None)
        s += txt(fx(t), ytop + rowh * 7 + 16, "%+d" % t if t else "0", 10, fill=MUTED)
    for i, (name, dh, dl, sh, sl, sb) in enumerate(DIFF2):
        y = ytop + rowh * i + 14
        s += txt(x0 - 12, y + 8, name, 12, anchor="end")

        def err(a, b):
            if b is None:
                return None
            return math.sqrt(a * a + b * b)
        el, eh = err(sl, sb), err(sh, sb)
        for yy, d, e, c in ((y, dl, el, REV), (y + 16, dh, eh, FWD)):
            if e is not None:
                s += line(round(fx(d - e), 1), yy, round(fx(d + e), 1), yy, c, 1.6, op=0.6)
            s += circ(round(fx(d), 1), yy, 4, c, c)
        s += txt(668, y + 4, "L/16 %+.2f" % dl, 11, fill=(NO if dl <= 0 else REV), anchor="start", weight=("700" if dl <= 0 else None))
        s += txt(668, y + 20, "H/14 %+.2f" % dh, 11, fill=FWD, anchor="start")
        s += txt(762, y + 4, "BiT ± %s" % ("없음" if sb is None else "%.2f" % sb), 10.5, fill=MUTED, anchor="start")
    s += txt(450, ytop + rowh * 7 + 36, "원문: L/16 JFT 가 BiT-L 을 「모든 과제에서」 넘는다 (5 쪽, 표 2 캡션 「모든 데이터셋」). ReaL 은 같고 VTAB 은 0.01 아래다.", 12, fill=NO, weight="700")
    svg("fig06_table2_delta", W, H, s, "표 2 의 ViT 와 BiT-L 차이")


# ── 그림 7: 비용 ──────────────────────────────────────────────────────────
def fig07():
    W, H = 940, 370
    s = txt(W / 2, 26, "그림 7. 표 2 의 TPUv3-코어-일 — 에폭이 칸마다 다르고 표에 적혀 있지 않다", 15, weight="700")
    x0, x1 = 170, 560
    fx = lambda v: x0 + v / 13000.0 * (x1 - x0)
    rows = [("H/14 JFT", 2500, FWD, "표 3: 14 에폭"), ("L/16 JFT", 680, FWD, "표 3: 7 또는 14 에폭"), ("L/16 I21k", 230, FWD, "표 3: 30 또는 90 에폭"),
            ("BiT-L R152x4", 9900, REV, "D.1 이 BiT 논문을 두고 적은 값: 30 에폭"), ("Noisy Student", 12300, REV, "이 편에 적혀 있지 않다")]
    for i, (n, v, c, e) in enumerate(rows):
        y = 60 + i * 38
        s += txt(x0 - 10, y + 15, n, 12, anchor="end")
        s += box(x0, y, round(fx(v) - x0, 1), 22, c, c, rx=3)
        s += txt(round(fx(v), 1) + 8, y + 16, format(v, ","), 11.5, anchor="start")
        s += txt(650, y + 16, e, 11.5, fill=INK2, anchor="start")
    s += box(40, 258, 860, 92, NODE, LINE)
    s += lines_at(56, 280, [
        ("BiT-L / H/14 = 9,900 / 2,500 = 3.96 배. BiT-L 이 30 에폭이라면 에폭당 1.85 배 (내가 센 것, 표 2 의 BiT-L 에폭은 적혀 있지 않다).", INK, "700"),
        "같은 편 그림 11 의 224 입력 추론 속도는 H/14 87.3 · R152x4 110.7 이미지/초/코어로 H/14 가 R152x4 의 0.79 배다(벡터 좌표로 읽음).",
        "원문도 「스케줄 · 최적화기 · 가중치 감쇠에도 달렸다」 고 적고 통제된 비교를 4.4절로 넘긴다(6 쪽). 그 4.4절에 R152x4 와 Noisy Student 는 없다."], 11.5, 21)
    svg("fig07_cost_units", W, H, s, "표 2 사전학습 비용과 에폭")


# ── 그림 8: VTAB ──────────────────────────────────────────────────────────
def fig08():
    W, H = 900, 340
    s = txt(W / 2, 26, "그림 8. 원문 그림 2 를 벡터 좌표로 읽은 값 — VTAB 묶음별", 15, weight="700")
    cols = (FWD, REV, OK, CODE)
    names = ("ViT-H/14", "BiT-L (R152x4)", "VIVI-Ex-100% (R50x3)", "S4L (R50x1)")
    y0, y1 = 70, 262
    fy = lambda v: y1 - (v - 50) / 50.0 * (y1 - y0)
    x = 70
    for g, vals in FIG2.items():
        s += txt(x + 80, y1 + 22, g, 11.5)
        s += line(x - 8, y1, x + 168, y1, INK2, 1)
        for i, v in enumerate(vals):
            bx = x + i * 40
            s += box(bx, round(fy(v), 1), 34, round(y1 - fy(v), 1), cols[i], cols[i], rx=2)
            s += txt(bx + 17, round(fy(v), 1) - 5, "%.1f" % v, 10.5)
        x += 200
    for i, n in enumerate(names):
        s += box(90 + i * 190, 296, 12, 12, cols[i], cols[i], rx=2) + txt(108 + i * 190, 306, n, 11, anchor="start", fill=INK2)
    s += txt(W / 2, 330, "세로 축은 50 부터 그렸다. H/14 와 BiT-L 차: 19 과제 +1.42 · Natural +1.14 · Specialized +0.16 · Structured +2.30", 11.5, fill=INK2)
    svg("fig08_vtab", W, H, s, "VTAB 묶음별 네 방법의 값")


# ── 그림 9: 데이터 크기와 함께 바뀌는 것 ────────────────────────────────────
def fig09():
    W, H = 900, 300
    s = txt(W / 2, 26, "그림 9. 그림 3 의 가로축 「사전학습 데이터」 와 함께 바뀌는 것 (표 3, 걸음 수는 내가 센 것)", 14.5, weight="700")
    rows = [["데이터", "부류", "장 수", "에폭", "갱신 걸음", "본 이미지", "학습률 감쇠", "가중치 감쇠", "드롭아웃", "기울기 자르기"]]
    meta = {"ImageNet": ("1k", "cosine", "0.3", "0.1", "1"), "ImageNet-21k": ("21k", "linear", "0.03", "0.1", "-"), "JFT-300M": ("18k", "linear", "0.1", "0.0", "-")}
    for ds, N, ep, st, seen in STEPS:
        m = meta[ds]
        rows.append([(ds, INK, "700", None), m[0], "%gM" % (N / 1e6), str(ep), format(int(round(st)), ","), "%.2f 억" % (seen / 1e8), m[1], m[2], m[3], m[4]])
    s += table(20, 48, [120, 54, 66, 54, 96, 96, 102, 102, 84, 86], rows, 27, 12)
    s += lines_at(24, 234, [
        ("부류 수 · 갱신 걸음 · 정칙화 셋 · 감쇠 꼴이 데이터와 함께 움직인다. 원문은 「작은 데이터의 성능을 올리려고 정칙화 셋을 최적화했다」 고 적는다(6 쪽).", INK2),
        ("둘째 실험(그림 4)은 설정을 하나로 묶었지만 부분 데이터에서 에폭을 묶었는지 걸음을 묶었는지 적혀 있지 않다.", INK2),
        ("7 에폭으로 묶었다면 9M 은 15,381 걸음이고 그중 65% 가 예열 1 만 걸음이다(내 셈).", NO, "700")], 11.5, 22)
    svg("fig09_train_confounds", W, H, s, "데이터 크기와 함께 바뀌는 학습 설정 표")


# ── 그림 10: 그림 3 다시 그리기 ─────────────────────────────────────────────
def fig10():
    W, H = 900, 420
    x0, y0, x1, y1 = 70, 56, 560, 360
    fy = lambda v: y1 - (v - 70) / 20.0 * (y1 - y0)
    xs = [130, 315, 500]
    s = txt(W / 2, 26, "그림 10. 원문 그림 3 다시 그리기 — 표 5 의 값과 BiT 띠 (벡터 좌표로 읽음)", 15, weight="700")
    s += line(x0, y1, x1, y1, INK2, 1.2) + line(x0, y0, x0, y1, INK2, 1.2)
    for t in (70, 75, 80, 85, 90):
        s += line(x0, fy(t), x1, fy(t), LINE, 0.8, dash="2 3") + txt(x0 - 7, fy(t) + 4, str(t), 10, fill=MUTED, anchor="end")
    labs = ["ImageNet", "ImageNet-21k", "JFT-300M"]
    for x, l in zip(xs, labs):
        s += txt(x, y1 + 20, l, 12)
    hi, lo = FIG3_BIT["high"], FIG3_BIT["low"]
    pts = ["%.1f,%.1f" % (x, fy(v)) for x, v in zip(xs, hi)] + ["%.1f,%.1f" % (x, fy(v)) for x, v in zip(xs[::-1], lo[::-1])]
    s += '<polygon points="%s" fill="%s" opacity="0.55"/>' % (" ".join(pts), REV_SOFT)
    s += polyline([(x, fy(v)) for x, v in zip(xs, hi)], REV, 1.6) + polyline([(x, fy(v)) for x, v in zip(xs, lo)], REV, 1.6)
    for x, v in zip(xs, hi):
        s += txt(x + 10, fy(v) - 8, "%.2f" % v, 10.5, fill=REV, anchor="start")
    for x, v in zip(xs, lo):
        s += txt(x + 10, fy(v) + 15, "%.2f" % v, 10.5, fill=REV, anchor="start")
    cols = {"B/32": "#7FB2CF", "B/16": PURP, "L/32": OK, "L/16": FWD, "H/14": NO}
    offs = {"B/32": -26, "B/16": -13, "L/32": 0, "L/16": 13, "H/14": 26}
    for x, l in zip(xs, labs):
        for k, v in T5_IN[l].items():
            if v is None:
                continue
            if l == "ImageNet-21k" and k == "H/14":
                s += circ(x + offs[k], round(fy(v), 1), 5, NODE, cols[k], 1.6)
            else:
                s += circ(x + offs[k], round(fy(v), 1), 5, cols[k], cols[k])
    s += circ(xs[2] + offs["H/14"], round(fy(FIG3_H14), 1), 3, NODE, NO, 1.4)
    for i, k in enumerate(("B/32", "B/16", "L/32", "L/16", "H/14")):
        s += circ(600, 72 + i * 22, 5, cols[k], cols[k]) + txt(614, 76 + i * 22, "ViT-" + k, 11.5, anchor="start", fill=INK2)
    s += box(590, 190, 290, 170, NODE, LINE)
    s += lines_at(602, 212, [
        ("읽은 것", INK, "700"),
        "21k 의 ViT 최고 85.15 < BiT 위 끝 85.39",
        "JFT 에서 BiT 위 끝 87.76 을 넘는 것은",
        "H/14 하나(표 5 88.04, +0.28)",
        "빈 원: H/14 21k 85.13 은 표 5 에만 있고",
        "원문 그림 3 에 찍혀 있지 않다",
        "작은 원: 원문 그림 3 의 H/14 는 88.28"], 11.5, 22)
    svg("fig10_fig3_redraw", W, H, s, "원문 그림 3 을 표 5 값과 BiT 띠로 다시 그린 것")


# ── 그림 11: 그림 4 다시 그리기 ─────────────────────────────────────────────
def fig11():
    W, H = 920, 420
    x0, y0, x1, y1 = 70, 56, 520, 360
    xv = (9, 30, 90, 300)
    fx = lambda v: x0 + 20 + (math.log10(v) - math.log10(9)) / (math.log10(300) - math.log10(9)) * (x1 - x0 - 40)
    fy = lambda v: y1 - (v - 30) / 45.0 * (y1 - y0)
    s = txt(W / 2, 26, "그림 11. 원문 그림 4 다시 그리기 — JFT 부분집합 크기와 ImageNet 5-shot 선형 (벡터 좌표로 읽음)", 14.5, weight="700")
    s += axes(x0, y0, x1, y1, xv, [30, 40, 50, 60, 70], fx, fy, "사전학습 장 수 (백만, 점은 9 · 30 · 90 · 300)", "top-1 (%)")
    style = {"L/16": (FWD, None), "L/32": (OK, None), "B/32": (PURP, None), "b/32": (CODE, None), "R50x1": (MUTED, "5 4"), "R152x2": (REV, "5 4")}
    for k, v in FIG4.items():
        c, d = style[k]
        s += polyline([(round(fx(a), 1), round(fy(b), 1)) for a, b in zip(xv, v)], c, 2, d)
        for a, b in zip(xv, v):
            s += circ(round(fx(a), 1), round(fy(b), 1), 3, c, c)
        s += txt(round(fx(300), 1) + 6, round(fy(v[3]), 1) + (4 if k != "R152x2" else 12), k, 10.5, fill=c, anchor="start")
    rows = [["장 수", "B/32 - R50x1", "L/16 - R152x2"]]
    for i, a in enumerate(xv):
        d1, d2 = FIG4["B/32"][i] - FIG4["R50x1"][i], FIG4["L/16"][i] - FIG4["R152x2"][i]
        rows.append(["%dM" % a, ("%+.2f" % d1, NO if d1 < 0 else OK, "700", None), ("%+.2f" % d2, NO if d2 < 0 else OK, "700", None)])
    s += table(570, 66, [70, 120, 130], rows, 28, 12)
    s += lines_at(570, 232, [
        ("원문이 「비슷한 계산」 으로 묶은 두 쌍", INK, "700"),
        "표 6 의 exaFLOPs: B/32 164 대 R50x1 150 = 1.09 배",
        "L/16 2,586 대 R152x2 1,681 = 1.54 배",
        ("90M -> 300M 에서 오른 양", INK, "700"),
        "L/16 +1.53, L/32 +1.33, B/32 +0.59",
        "R152x2 +0.39, R50x1 +0.15",
        ("하이브리드는 이 실험에 없다. 흩어짐도 없다.", NO, "700")], 11.5, 21)
    svg("fig11_fig4_redraw", W, H, s, "원문 그림 4 를 벡터 좌표 값으로 다시 그린 것")


# ── 그림 12: 그림 5 와 배수 ─────────────────────────────────────────────────
def fig12():
    W, H = 960, 440
    x0, y0, x1, y1 = 70, 58, 540, 370
    lo, hi = 2.0, 4.3
    fx = lambda v: x0 + (math.log10(v) - lo) / (hi - lo) * (x1 - x0)
    fy = lambda v: y1 - (v - 88) / 9.0 * (y1 - y0)
    s = txt(W / 2, 26, "그림 12. 표 6 으로 다시 그린 원문 그림 5 (Average-5) 와 「같은 성능에 드는 계산 배수」", 15, weight="700")
    s += axes(x0, y0, x1, y1, [100, 1000, 10000], [88, 90, 92, 94, 96], fx, fy, "사전학습 계산 (exaFLOPs, 로그)", "Average-5 (%)", xfmt=lambda v: format(int(v), ","))
    for rows, c in ((RES, REV), (VITS, FWD), (HYB, OK)):
        for r in rows:
            xx, yy = round(fx(r[8]), 1), round(fy(avg5(r)), 1)
            if rows is RES:
                s += '<rect x="%.1f" y="%.1f" width="9" height="9" fill="%s"/>' % (xx - 4.5, yy - 4.5, c)
            elif rows is HYB:
                s += line(xx - 5, yy, xx + 5, yy, c, 2.2) + line(xx, yy - 5, xx, yy + 5, c, 2.2)
            else:
                s += circ(xx, yy, 5, c, c)
    s += circ(88, 74, 5, FWD, FWD) + txt(98, 78, "ViT", 11, anchor="start", fill=INK2)
    s += '<rect x="134" y="70" width="9" height="9" fill="%s"/>' % REV + txt(148, 78, "ResNet", 11, anchor="start", fill=INK2)
    s += line(200, 74, 210, 74, OK, 2.2) + line(205, 69, 205, 79, OK, 2.2) + txt(216, 78, "하이브리드", 11, anchor="start", fill=INK2)
    rows = [["ViT", "Average-5 배수", "ImageNet 배수"]]
    for a, b in zip(RATIO["avg"], RATIO["in"]):
        def cell(v):
            if v[3] is not None:
                return ("%.2f" % v[3], INK, "700", None)
            return ("ResNet 앞줄 " + v[4], MUTED, None, None)
        rows.append([a[0], cell(a), cell(b)])
    s += table(566, 66, [116, 130, 130], rows, 28, 11.5)
    s += lines_at(566, 276, [
        ("배수 = ResNet 앞줄이 같은 값에 닿는 계산 / ViT 계산", INK, "700"),
        "(로그 계산에서 직선 보간, 내가 센 것)",
        "원문: 2 ~ 4 배 적은 계산 (Average-5).",
        "Average-5 안에는 Flowers · Pets 가 있고",
        "R50x1 의 Flowers 는 94.26, ViT-B/32 는 99.27.",
        ("표 6 은 실행 수와 흩어짐을 적지 않는다.", NO, "700")], 11.5, 21)
    svg("fig12_fig5_ratio", W, H, s, "표 6 으로 다시 그린 그림 5 와 계산 배수")


# ── 그림 13: 같은 값이 넷 ──────────────────────────────────────────────────
def fig13():
    W, H = 900, 300
    s = txt(W / 2, 26, "그림 13. ViT-H/14 (JFT) 의 같은 칸이 표마다 다르다", 15, weight="700")
    rows = [["칸", "표 2 (세 번 평균)", "표 5", "표 6", "원문 그림 3 · 5"],
            ["ImageNet", "88.55 (518, Polyak)", ("88.04", NO, "700", None), ("88.08", NO, "700", None), ("그림 3: 88.28 · 그림 5: 88.08", NO, "700", None)],
            ["ImageNet ReaL", "90.72 (518, Polyak)", "90.33", "90.36", "-"],
            ["CIFAR-10", "99.50", "99.50", "99.50", "-"],
            ["CIFAR-100", "94.55", "94.55", ("94.71", NO, "700", None), "-"],
            ["Pets", "97.56", "97.56", ("97.11", NO, "700", None), "-"],
            ["Flowers-102", "99.68", "99.68", ("99.71", NO, "700", None), "-"]]
    s += table(30, 48, [130, 180, 90, 90, 350], rows, 26, 12)
    s += lines_at(30, 248, [
        ("표 2 와 표 5 는 ImageNet 을 빼고 같고 표 6 만 다섯 칸이 다르다. 표 6 의 Pets 97.11 은 윗줄 L/16 14 에폭의 값과 같다.", INK2),
        ("표 5 의 다른 줄(B/16 · B/32 · L/16 · L/32) JFT 값은 표 6 과 모두 같다. 어느 값이 어느 실행인지 원문에 적혀 있지 않다.", INK2)], 11.5, 22)
    svg("fig13_h14_values", W, H, s, "ViT-H/14 값을 표마다 대조한 표")


# ── 그림 14: 자리 임베딩 보간과 표 8 ────────────────────────────────────────
def fig14():
    W, H = 920, 370
    s = defs() + txt(W / 2, 26, "그림 14. 미세조정에서 입력을 키울 때의 자리 임베딩 (왼쪽) 과 표 8 (오른쪽)", 15, weight="700")

    def grid(x, y, g, size, title, sub):
        o = ""
        c = float(size) / g
        for i in range(g):
            for j in range(g):
                o += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="%s" stroke-width="0.5"/>' % (
                    x + j * c, y + i * c, c, c, FWD_SOFT if (i + j) % 2 else NODE, LINE)
        o += txt(x + size / 2.0, y + size + 20, title, 12, weight="700") + txt(x + size / 2.0, y + size + 38, sub, 10.5, fill=MUTED)
        return o
    s += grid(40, 70, 14, 140, "224 입력: 14 x 14", "E_pos 197 x D")
    s += line(190, 140, 232, 140, INK2, 1.4, marker="ai") + txt(211, 128, "2-D", 10.5, fill=INK2) + txt(211, 158, "보간", 10.5, fill=INK2)
    s += grid(240, 70, 24, 140, "384 입력: 24 x 24", "E_pos 577 x D")
    s += lines_at(40, 270, [
        "분류 토큰 자리 0 은 격자가 아니다. 보간을 어떤 방법으로",
        "(쌍선형 · 쌍삼차) 했는지, 자리 0 을 어떻게 뒀는지 원문에",
        "적혀 있지 않다. 보간만의 몫을 잰 행도 없다."], 11.5, 19)
    x0, x1 = 610, 880
    lo, hi = 0.60, 0.65
    fx = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    y = 70
    for name, a, b, c in T8:
        for lab, v, col in (("입력에 한 번", a, FWD), ("층마다", b, REV), ("층마다 공유", c, OK)):
            if v is None:
                continue
            s += txt(x0 - 74, y + 11, name if lab == "입력에 한 번" else "", 11.5, anchor="end", weight="700")
            s += txt(x0 - 6, y + 11, lab, 10, anchor="end", fill=MUTED)
            s += box(x0, y, round(fx(v) - x0, 1), 14, col, col, rx=2)
            s += txt(round(fx(v), 1) + 5, y + 11, "%.5f" % v, 10.5, anchor="start")
            y += 19
        y += 8
    s += txt(745, y + 14, "가로 축 0.60 부터. 흩어짐이 적혀 있지 않다.", 11, fill=NO, weight="700")
    svg("fig14_pos_interp", W, H, s, "자리 임베딩 보간과 표 8")


# ── 그림 15: 그림 8 ────────────────────────────────────────────────────────
def fig15():
    W, H = 920, 400
    x0, y0, x1, y1 = 70, 56, 560, 340
    lo, hi = -0.85, 1.05
    fx = lambda v: x0 + (math.log10(v) - lo) / (hi - lo) * (x1 - x0)
    fy = lambda v: y1 - (v - 0.1) / 0.55 * (y1 - y0)
    s = txt(W / 2, 26, "그림 15. 원문 그림 8 왼쪽 다시 그리기 — 어느 차원을 키울까 (벡터 좌표로 읽음)", 15, weight="700")
    s += axes(x0, y0, x1, y1, [0.2, 0.5, 1, 2, 5, 10], [0.1, 0.2, 0.3, 0.4, 0.5, 0.6], fx, fy, "상대 계산 (기준 = 8 층, D 1024, M 2048, 패치 32)", "ImageNet 5-shot")
    cols = {"전부": INK, "깊이": REV, "조각 크기": OK, "MLP 폭": CODE, "폭": PURP}
    for k, v in FIG8.items():
        c = cols[k]
        s += polyline([(round(fx(a), 1), round(fy(b), 1)) for a, b in v], c, 2)
        for a, b in v:
            s += circ(round(fx(a), 1), round(fy(b), 1), 3, c, c)
    xm = round(fx(7.70), 1)
    s += line(xm, y0, xm, y1, NO, 1.2, dash="4 3") + txt(xm, y0 - 6, "64 층이면 7.70", 10.5, fill=NO)
    for i, k in enumerate(cols):
        s += circ(590, 70 + i * 21, 4, cols[k], cols[k]) + txt(602, 74 + i * 21, k, 11.5, anchor="start", fill=INK2)
    s += box(586, 186, 310, 154, NODE, LINE)
    s += lines_at(598, 208, [
        ("내가 센 것", INK, "700"),
        "기준 모델의 곱셈-덧셈으로 층 수를 재면",
        "2 층 0.28 · 4 층 0.52 · 16 층 1.96 으로",
        "그림의 0.27 · 0.51 · 1.97 과 맞는다.",
        "64 층은 7.70 인데 깊이 선의 끝 점은 6.09.",
        ("본문 「64 층까지 뚜렷하다」 의 점이 그림에", NO, "700"),
        ("보이지 않는다.", NO, "700")], 11.5, 20)
    svg("fig15_fig8_shape", W, H, s, "원문 그림 8 왼쪽을 다시 그린 것")


# ── 그림 16: 주의 거리 ─────────────────────────────────────────────────────
def fig16():
    W, H = 940, 400
    s = txt(W / 2, 26, "그림 16. 원문 그림 10 다시 그리기 — 층마다 머리 16 개의 평균 주의 거리 (벡터 좌표로 읽음)", 14.5, weight="700")

    def panel(x0, name, c):
        y0, y1 = 66, 330
        x1 = x0 + 380
        fx = lambda v: x0 + v / 23.0 * (x1 - x0)
        fy = lambda v: y1 - v / 135.0 * (y1 - y0)
        o = axes(x0, y0, x1, y1, [0, 5, 10, 15, 20], [0, 20, 40, 60, 80, 100, 120], fx, fy, "층", None)
        o += txt((x0 + x1) / 2.0, y0 - 8, name, 12.5, weight="700")
        data = FIG10[name]
        up = ["%.1f,%.1f" % (fx(i), fy(v[2])) for i, v in enumerate(data)]
        dn = ["%.1f,%.1f" % (fx(i), fy(v[0])) for i, v in reversed(list(enumerate(data)))]
        o += '<polygon points="%s" fill="%s" opacity="0.8"/>' % (" ".join(up + dn), FWD_SOFT if c == FWD else REV_SOFT)
        o += polyline([(fx(i), fy(v[1])) for i, v in enumerate(data)], c, 2.2)
        o += line(x0, round(fy(UNIF), 1), x1, round(fy(UNIF), 1), NO, 1.3, dash="5 4")
        return o
    s += panel(70, "ViT-L/16", FWD) + panel(520, "R50x1 + ViT-L/16", REV)
    s += txt(W / 2, 378, "띠 = 최소 ~ 최대, 선 = 중앙값. 빨간 점선 116.49 = 14 x 14 조각에 무게를 똑같이 줄 때의 거리(내가 센 것). ViT-L/16 층 12 이후 중앙값은 그 값의 94~99%.", 11.5, fill=INK2)
    svg("fig16_attention_distance", W, H, s, "층별 평균 주의 거리와 균일 주의의 값")


# ── 그림 17: 속도 ──────────────────────────────────────────────────────────
def fig17():
    W, H = 920, 420
    x0, y0, x1, y1 = 70, 56, 520, 360
    fx = lambda v: x0 + 16 + (math.log10(v) - math.log10(64)) / (math.log10(518) - math.log10(64)) * (x1 - x0 - 32)
    fy = lambda v: y1 - (math.log10(v) - 1) / 3.5 * (y1 - y0)
    s = txt(W / 2, 26, "그림 17. 원문 그림 11 왼쪽 다시 그리기 — 입력 크기와 최고 추론 속도 (벡터 좌표로 읽음)", 14.5, weight="700")
    s += axes(x0, y0, x1, y1, FIG11_X, [10, 100, 1000, 10000], fx, fy, "입력 변 (픽셀, 로그)", "이미지 / 초 / 코어 (로그)", yfmt=lambda v: format(int(v), ","))
    style = {"R50x1": (REV, None), "R50x2": (REV, "5 4"), "R152x4": (MUTED, None), "B/32": ("#7FB2CF", None), "L/32": ("#7FB2CF", "5 4"),
             "B/16": (FWD, None), "L/16": (FWD, "5 4"), "H/14": (PURP, None)}
    for k, v in FIG11.items():
        xs = FIG11_XH if k == "H/14" else FIG11_X
        c, d = style[k]
        s += polyline([(round(fx(a), 1), round(fy(b), 1)) for a, b in zip(xs, v)], c, 2, d)
    rows = [["모델", "224 속도", "224->512 기울기", "384->512 기울기"]]
    for k in ("R50x1", "R50x2", "R152x4", "B/32", "L/32", "B/16", "L/16", "H/14"):
        rows.append([(k, style[k][0], "700", None), "%.1f" % FIG11[k][2], "%.2f" % SLOPE[k][1], "%.2f" % SLOPE[k][0]])
    s += table(548, 60, [70, 76, 102, 102], rows, 25, 11)
    s += lines_at(548, 306, [
        "기울기 2 = 조각 수 비례, 4 = 조각 수 제곱(원문의 bi-quadratic).",
        "n² 몫(그림 5) 으로 내가 낸 512 의 기울기는 2.3 안팎인데",
        ("B/16 · L/16 의 실측은 3.1~3.3. 곱셈-덧셈 셈만으로는", NO, "700"),
        ("설명되지 않는다 (D.4 도 FLOPs 와 다르다고 적는다).", NO, "700")], 11.5, 20)
    svg("fig17_speed_slope", W, H, s, "입력 크기와 추론 속도의 기울기")


# ── 그림 18: 계보 ──────────────────────────────────────────────────────────
def fig18():
    W, H = 900, 300
    s = defs() + txt(W / 2, 26, "그림 18. 이 편이 앞 칸에서 받은 것", 15, weight="700")

    def node(x, y, w, h, title, sub, fill, st):
        return box(x, y, w, h, fill, st) + txt(x + w / 2, y + 20, title, 12, weight="700") + txt(x + w / 2, y + 38, sub, 10.5, fill=INK2)
    s += node(30, 60, 210, 52, "Transformer (2017)", "인코더, 다중 머리, 자리 합", NODE, INK)
    s += node(30, 136, 210, 52, "BERT (2019)", "[class], 사전학습 후 미세조정", NODE, INK)
    s += node(30, 212, 210, 52, "ResNet · BN · GN + WS (BiT)", "비교 상대, 하이브리드의 앞단", NODE, INK)
    s += node(350, 124, 200, 76, "ViT (2021)", "조각 = 낱말, 표준 인코더", FWD_SOFT, FWD)
    for y in (86, 162, 238):
        s += line(240, y, 348, 162, INK2, 1.3, marker="ai")
    s += node(660, 60, 214, 52, "원문이 꼽은 남은 일 하나", "검출 · 분할 등 다른 과제", NODE, LINE)
    s += node(660, 136, 214, 52, "원문이 꼽은 남은 일 둘", "자기 지도 사전학습 (79.9%)", NODE, LINE)
    s += node(660, 212, 214, 52, "원문이 꼽은 남은 일 셋", "더 키우기 (포화를 못 봄)", NODE, LINE)
    for y in (86, 162, 238):
        s += line(550, 162, 658, y, INK2, 1.3, marker="ai")
    svg("fig18_lineage", W, H, s, "ViT 의 앞 칸과 남은 일")


print("")
for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10, fig11, fig12, fig13, fig14, fig15, fig16, fig17, fig18):
    f()
print("끝")
