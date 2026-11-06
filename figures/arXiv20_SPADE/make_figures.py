# -*- coding: utf-8 -*-
r"""SPADE 노트(Cohen · Hoshen, arXiv v3, 2021)의 책상 확인과 그림 여덟을 만든다.

표준 라이브러리만 쓴다. 바깥 데이터를 읽지 않으므로 어디서나 돌아간다.

  python make_figures.py

앞부분(recount)은 원문 표 2 · 3 · 6 · 7 의 수로 평균 · 부류별 순위 · 차이를 다시 내어 찍는다.
비용 칸은 원문에 없는 내 셈이고 가정을 함께 찍는다: 세 단계를 56 x 56 격자 하나에 이어 붙인다,
WRN-50-2 의 블록 출력 채널 256 · 512 · 1024, 부동소수 4 바이트, 평균 학습 장수 3,629 / 15.
3,629 는 MVTec AD 쪽 값이고 이 논문에는 적혀 있지 않다.

MS 상수(Uninformed Students 원문 표 3 의 여러 수용장 묶음 열)만 이 논문 밖의 값이다.
"""
import io
import os
import sys

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
FONT = "IBM Plex Sans KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"

CLASSES = ["Carpet", "Grid", "Leather", "Tile", "Wood", "Bottle", "Cable", "Capsule",
           "Hazelnut", "Metal nut", "Pill", "Screw", "Toothbrush", "Transistor", "Zipper"]
TEXTURES = CLASSES[:5]
OBJECTS = CLASSES[5:]

# 표 2 (픽셀 ROCAUC). None 은 원문의 「-」 또는 빈칸(Toothbrush 의 TI 칸은 원문이 비어 있다).
T2_COLS = ["AESSIM", "AEL2", "AnoGAN", "CNN Dict", "TI", "VM", "CAVGA-Ru", "SPADE"]
T2 = {
    "Carpet":     [87, 59, 54, 72, 88, None, None, 97.5],
    "Grid":       [94, 90, 58, 59, 72, None, None, 93.7],
    "Leather":    [78, 75, 64, 87, 97, None, None, 97.6],
    "Tile":       [59, 51, 50, 93, 41, None, None, 87.4],
    "Wood":       [73, 73, 62, 91, 78, None, None, 88.5],
    "Bottle":     [93, 86, 86, 78, None, 82, None, 98.4],
    "Cable":      [82, 86, 78, 79, None, None, None, 97.2],
    "Capsule":    [94, 88, 84, 84, None, 76, None, 99.0],
    "Hazelnut":   [97, 95, 87, 72, None, None, None, 99.1],
    "Metal nut":  [89, 86, 76, 82, None, 60, None, 98.1],
    "Pill":       [91, 85, 87, 68, None, 83, None, 96.5],
    "Screw":      [96, 96, 80, 87, None, 94, None, 98.9],
    "Toothbrush": [92, 93, 90, 77, None, 68, None, 97.9],
    "Transistor": [90, 86, 80, 66, None, None, None, 94.1],
    "Zipper":     [88, 77, 78, 76, None, None, None, 96.5],
}
T2_AVG = [87, 82, 74, 78, 75, 77, 89, 96.0]

# 표 3 (PRO)
T3_COLS = ["Student", "1-NN", "OC-SVM", "l2-AE", "VAE", "SSIM-AE", "CNN-Dict", "SPADE"]
T3 = {
    "Carpet":     [69.5, 51.2, 35.5, 45.6, 50.1, 64.7, 46.9, 94.7],
    "Grid":       [81.9, 22.8, 12.5, 58.2, 22.4, 84.9, 18.3, 86.7],
    "Leather":    [81.9, 44.6, 30.6, 81.9, 63.5, 56.1, 64.1, 97.2],
    "Tile":       [91.2, 82.2, 72.2, 89.7, 87.0, 17.5, 79.7, 75.9],
    "Wood":       [72.5, 50.2, 33.6, 72.7, 62.8, 60.5, 62.1, 87.4],
    "Bottle":     [91.8, 89.8, 85.0, 91.0, 89.7, 83.4, 74.2, 95.5],
    "Cable":      [86.5, 80.6, 43.1, 82.5, 65.4, 47.8, 55.8, 90.9],
    "Capsule":    [91.6, 63.1, 55.4, 86.2, 52.6, 86.0, 30.6, 93.7],
    "Hazelnut":   [93.7, 86.1, 61.6, 91.7, 87.8, 91.6, 84.4, 95.4],
    "Metal nut":  [89.5, 70.5, 31.9, 83.0, 57.6, 60.3, 35.8, 94.4],
    "Pill":       [93.5, 72.5, 54.4, 89.3, 76.9, 83.0, 46.0, 94.6],
    "Screw":      [92.8, 60.4, 64.4, 75.4, 55.9, 88.7, 27.7, 96.0],
    "Toothbrush": [86.3, 67.5, 53.8, 82.2, 69.3, 78.4, 15.1, 93.5],
    "Transistor": [70.1, 68.0, 49.6, 72.8, 62.6, 72.5, 62.8, 87.4],
    "Zipper":     [93.3, 51.2, 35.5, 83.9, 54.9, 66.5, 70.3, 92.6],
}
T3_AVG = [85.7, 64, 47.9, 79, 63.9, 69.4, 51.5, 91.7]

# Uninformed Students 원문 표 3 의 Multiscale 열 (이 논문 밖의 값). 인쇄 평균 0.914.
MS = {
    "Carpet": 87.9, "Grid": 95.2, "Leather": 94.5, "Tile": 94.6, "Wood": 91.1,
    "Bottle": 93.1, "Cable": 81.8, "Capsule": 96.8, "Hazelnut": 96.5, "Metal nut": 94.2,
    "Pill": 96.1, "Screw": 94.2, "Toothbrush": 93.3, "Transistor": 66.6, "Zipper": 95.1,
}

# PatchCore 원문 표 S3 의 SPADE 행과 표 S2 의 SPADE 행 (부류 순서를 이 편에 맞춰 옮김)
PC_S3 = {"Bottle": 95.5, "Cable": 90.9, "Capsule": 93.7, "Carpet": 94.7, "Grid": 86.7, "Hazelnut": 95.4,
         "Leather": 97.2, "Metal nut": 94.4, "Pill": 94.6, "Screw": 96.0, "Tile": 75.6, "Toothbrush": 93.5,
         "Transistor": 87.4, "Wood": 87.4, "Zipper": 92.6}
PC_S2 = {"Bottle": 98.4, "Cable": 97.2, "Capsule": 99.0, "Carpet": 97.5, "Grid": 93.7, "Hazelnut": 99.1,
         "Leather": 97.6, "Metal nut": 98.1, "Pill": 96.5, "Screw": 98.9, "Tile": 87.4, "Toothbrush": 97.9,
         "Transistor": 94.1, "Wood": 88.5, "Zipper": 96.5}

# 표 6 (PRO): 14 · 28 · 56 · SPADE
T6 = {
    "Carpet":     [93.5, 93.4, 91.0, 94.7],
    "Grid":       [80.9, 88.0, 89.1, 86.7],
    "Leather":    [96.6, 97.5, 97.3, 97.2],
    "Tile":       [74.5, 65.9, 73.8, 75.9],
    "Wood":       [84.7, 87.7, 87.5, 87.4],
    "Bottle":     [93.7, 94.7, 88.3, 95.5],
    "Cable":      [89.3, 87.3, 73.5, 90.9],
    "Capsule":    [90.5, 92.8, 91.4, 93.7],
    "Hazelnut":   [92.7, 95.8, 96.2, 95.4],
    "Metal nut":  [91.3, 93.1, 86.1, 94.4],
    "Pill":       [89.2, 94.4, 96.3, 94.6],
    "Screw":      [90.7, 95.9, 96.1, 96.0],
    "Toothbrush": [90.9, 93.5, 94.5, 93.5],
    "Transistor": [91.3, 72.1, 62.5, 87.4],
    "Zipper":     [90.9, 92.4, 92.5, 92.6],
}
T6_AVG = [89.38, 89.6, 87.74, 91.7]

CELLS = 56 * 56
DIM = 256 + 512 + 1024
MEAN_TRAIN = 3629 / 15


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


# ── 책상 확인 ──────────────────────────────────────────────
def recount():
    print("== 표 2 평균 다시 내기 ==")
    for i, c in enumerate(T2_COLS):
        v = [T2[k][i] for k in CLASSES if T2[k][i] is not None]
        print("%-10s 칸 %2d  평균 %s  인쇄 %s" % (c, len(v), ("%.3f" % mean(v)) if v else "칸 없음", T2_AVG[i]))

    print("\n== 표 2 부류별: SPADE 보다 높은 비교 칸 ==")
    n = 0
    for k in CLASSES:
        r = T2[k]
        hi = [(T2_COLS[i], r[i]) for i in range(7) if r[i] is not None and r[i] > r[7]]
        best = max(x for x in r[:7] if x is not None)
        n += 1 if hi else 0
        print("%-11s SPADE %5.1f  최고 상대 %5.1f  차 %+5.1f  위 %s" % (k, r[7], best, r[7] - best, hi))
    print("SPADE 가 최고가 아닌 부류 수", n, "/ 15")
    tex = [T2[k][7] for k in TEXTURES]
    obj6 = [k for k in CLASSES if T2[k][5] is not None]
    print("TI 칸 있는 질감 5 부류의 SPADE 평균 %.2f  대 TI %.2f" % (mean(tex), mean(T2[k][4] for k in TEXTURES)))
    print("VM 칸 있는 6 부류 %s 의 SPADE 평균 %.2f  대 VM %.2f" % (obj6, mean(T2[k][7] for k in obj6), mean(T2[k][5] for k in obj6)))
    print("물체 10 부류의 SPADE 평균 %.2f" % mean(T2[k][7] for k in OBJECTS))

    print("\n== 표 3 평균 다시 내기 ==")
    for i, c in enumerate(T3_COLS):
        print("%-10s 평균 %7.3f  인쇄 %s" % (c, mean(T3[k][i] for k in CLASSES), T3_AVG[i]))

    print("\n== 표 3 부류별: SPADE 보다 높은 비교 칸 ==")
    n = 0
    for k in CLASSES:
        r = T3[k]
        hi = [(T3_COLS[i], r[i]) for i in range(7) if r[i] > r[7]]
        n += 1 if hi else 0
        print("%-11s SPADE %5.1f  Student %5.1f  차 %+5.1f  위 %s" % (k, r[7], r[0], r[7] - r[0], hi))
    print("SPADE 가 최고가 아닌 부류 수", n, "/ 15")
    d = [T3[k][7] - T3[k][0] for k in CLASSES]
    print("SPADE-Student 평균 차 %.3f  최소 %.1f  최대 %.1f" % (mean(d), min(d), max(d)))
    m = mean(T3[k][7] for k in CLASSES)
    print("SPADE 부류 사이 표본 표준편차 %.2f, 최소 %.1f, 최대 %.1f" % (
        (sum((T3[k][7] - m) ** 2 for k in CLASSES) / 14) ** 0.5,
        min(T3[k][7] for k in CLASSES), max(T3[k][7] for k in CLASSES)))
    print("Carpet 과 Zipper 의 1-NN · OC-SVM:", T3["Carpet"][1:3], T3["Zipper"][1:3])

    print("\n== 표 3 SPADE 대 Uninformed Students 묶음(표 3 원문 Multiscale) ==")
    print("묶음 평균 %.3f (인쇄 91.4)" % mean(MS.values()))
    dm = {k: T3[k][7] - MS[k] for k in CLASSES}
    w = [k for k in CLASSES if dm[k] > 0]
    print("SPADE 가 높은 부류", len(w), w)
    print("묶음이 높은 부류", 15 - len(w), [k for k in CLASSES if dm[k] < 0])
    for k in CLASSES:
        print("  %-11s %+5.1f" % (k, dm[k]))
    rest = [k for k in CLASSES if k != "Transistor"]
    print("Transistor 뺀 14 부류 평균: SPADE %.2f  묶음 %.2f  차 %+.2f" % (
        mean(T3[k][7] for k in rest), mean(MS[k] for k in rest), mean(dm[k] for k in rest)))

    print("\n== PatchCore 표 S2 · S3 의 SPADE 행과 대조 ==")
    print("표 S2 다른 칸:", [(k, T2[k][7], PC_S2[k]) for k in CLASSES if T2[k][7] != PC_S2[k]])
    print("표 S3 다른 칸:", [(k, T3[k][7], PC_S3[k]) for k in CLASSES if T3[k][7] != PC_S3[k]])

    print("\n== 표 6 평균 다시 내기 ==")
    names = ["14", "28", "56", "SPADE"]
    for i, c in enumerate(names):
        print("%-6s 평균 %7.3f  인쇄 %s" % (c, mean(T6[k][i] for k in CLASSES), T6_AVG[i]))
    print("표 6 SPADE 열과 표 3 SPADE 열이 같은가:", all(T6[k][3] == T3[k][7] for k in CLASSES))

    print("\n== 표 6: 단일 단계 대 SPADE ==")
    cnt = [0, 0, 0]
    anyhi = 0
    best_single = []
    for k in CLASSES:
        r = T6[k]
        for i in range(3):
            cnt[i] += 1 if r[i] > r[3] else 0
        anyhi += 1 if any(r[i] > r[3] for i in range(3)) else 0
        best_single.append(max(r[:3]))
        print("%-11s %s  최고 단일-SPADE %+.1f" % (k, r, max(r[:3]) - r[3]))
    print("SPADE 보다 높은 부류 수 14/28/56:", cnt, " 하나라도 높은 부류:", anyhi)
    print("부류마다 가장 좋은 단일 단계를 고른 평균 %.3f 대 SPADE %.3f" % (mean(best_single), mean(T6[k][3] for k in CLASSES)))
    ex = [k for k in CLASSES if k not in ("Transistor", "Cable")]
    print("Transistor · Cable 뺀 13 부류 평균 14/28/56/SPADE:", [round(mean(T6[k][i] for k in ex), 2) for i in range(4)])
    tot = sum(T6[k][3] - T6[k][2] for k in CLASSES)
    two = (T6["Transistor"][3] - T6["Transistor"][2]) + (T6["Cable"][3] - T6["Cable"][2])
    print("SPADE-56 차의 합 %.1f 중 Transistor+Cable %.1f = %.1f%%" % (tot, two, two / tot * 100))
    print("질감 5 평균 14/28/56/SPADE:", [round(mean(T6[k][i] for k in TEXTURES), 2) for i in range(4)])
    print("물체 10 평균 14/28/56/SPADE:", [round(mean(T6[k][i] for k in OBJECTS), 2) for i in range(4)])

    print("\n== 표 7 ==")
    print("Average 차 %.1f  Grid 차 %.1f" % (91.4 - 89.2, 86.3 - 73.2))
    tot7 = (91.4 - 89.2) * 15
    print("15 부류 차의 합(평균이 부류 평균이라 할 때) %.1f  Grid 몫 %.1f%%  Grid 뺀 14 부류 차 평균 %.2f" % (
        tot7, 13.1 / tot7 * 100, (tot7 - 13.1) / 14))
    print("K 50 대 10: Average %.1f  Grid %.1f" % (91.7 - 91.4, 86.7 - 86.3))

    print("\n== 비용 (내 셈, 원문에 없음) ==")
    print("56x56 칸 수", CELLS, " 잇는 차원", DIM, " 평균 학습 장수 %.2f" % MEAN_TRAIN)
    for label, k in (("K=1", 1), ("K=10", 10), ("K=50", 50), ("전체 평균", MEAN_TRAIN)):
        g = k * CELLS
        print("%-8s 갤러리 %12.0f 벡터  쌍 거리 %15.0f  저장 %7.2f GB  K=50 대비 %6.3f 배" % (
            label, g, CELLS * g, g * DIM * 4 / 1e9, k / 50))
    print("이미지 단계 거리 수 %.1f, 픽셀 단계 K=50 쌍 / 이미지 단계 거리 = %.0f" % (MEAN_TRAIN, CELLS * 50 * CELLS / MEAN_TRAIN))
    print("K 50 은 평균 학습 장수의 %.1f%%, K 10 은 %.1f%%" % (50 / MEAN_TRAIN * 100, 10 / MEAN_TRAIN * 100))
    sep = sum((s * s) * (50 * s * s) for s in (56, 28, 14))
    print("단계별로 따로 맞대면 쌍 수 %d, 56 칸 몫 %.1f%%" % (sep, CELLS * 50 * CELLS / sep * 100))
    print("224 자르기로 남는 넓이 %.1f%%" % ((224 / 256) ** 2 * 100))
    print("전체 학습 3,629 장 조각 저장 %.1f GB" % (3629 * CELLS * DIM * 4 / 1e9))

    print("\n== 표끼리 차 ==")
    print("표 1 SPADE-ITAE %.1f  표 4 SPADE-ITAE %.1f  표 5 SPADE-CAVGA %.1f" % (85.5 - 83.9, 71.9 - 72.5, 89.9 - 85))
    print("표 2 SPADE-CAVGA %.1f  표 3 SPADE-Student %.1f  표 3 SPADE-묶음 %.1f" % (96.0 - 89, 91.7 - 85.7, 91.7 - 91.4))
    print("PatchCore 재구현 - 이 편: 이미지 %+.1f 픽셀 %+.1f PRO %+.1f" % (85.3 - 85.5, 96.6 - 96.0, 91.5 - 91.7))
    print("픽셀 - 이미지 간격: MVTec %.1f  STC %.1f" % (96.0 - 85.5, 89.9 - 71.9))


# ── 그림 도구 ──────────────────────────────────────────────
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def arrow(idd, color):
    return ('<marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>' % (idd, color))


def defs():
    return "<defs>" + arrow("af", FWD) + arrow("ar", REV) + arrow("ai", INK2) + "</defs>"


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


# ── 그림 ──────────────────────────────────────────────────
def fig01_pipeline():
    b = txt(470, 28, "SPADE 의 두 단계 — 얼린 WRN-50-2 하나를 두 번 읽는다", 15, weight="bold")
    # 위 줄 이미지 단계
    b += txt(24, 62, "1 단계: 이미지", 13, FWD, "start", "bold")
    b += box(24, 74, 150, 62, FWD_SOFT, FWD)
    b += txt(99, 98, "시험 이미지 y", 12) + txt(99, 118, "224 x 224", 11, INK2)
    b += line(174, 105, 212, 105, FWD, 1.6, marker="af")
    b += box(214, 74, 180, 62, FWD_SOFT, FWD)
    b += txt(304, 98, "마지막 합성곱 전역 평균", 12) + txt(304, 118, "2,048 차원 f_y (식 1)", 11, INK2)
    b += line(394, 105, 432, 105, FWD, 1.6, marker="af")
    b += box(434, 74, 210, 62, FWD_SOFT, FWD)
    b += txt(539, 98, "학습 이미지 전부와 거리", 12) + txt(539, 118, "가까운 K 장의 평균 = d(y) (식 2)", 11, INK2)
    b += line(644, 105, 682, 105, FWD, 1.6, marker="af")
    b += box(684, 74, 232, 62, CODE_SOFT, CODE, dash="5,3")
    b += txt(800, 98, "d(y) 가 문턱 τ 보다 크면 이상", 12)
    b += txt(800, 118, "τ 값은 원문에 없다, 표는 AUROC 만", 11, INK2)
    # 아래로
    b += line(539, 136, 539, 186, INK2, 1.4, marker="ai")
    b += txt(549, 166, "가까운 K 장 (MVTec 50 · STC 1)", 11, INK2, "start")
    # 아래 줄 픽셀 단계
    b += txt(24, 176, "2 단계: 픽셀", 13, REV, "start", "bold")
    b += box(434, 188, 210, 66, REV_SOFT, REV)
    b += txt(539, 212, "K 장의 모든 칸 특징 = 갤러리 G", 12) + txt(539, 232, "블록 1 · 2 · 3 (56 · 28 · 14)", 11, INK2)
    b += line(434, 221, 396, 221, REV, 1.6, marker="ar")
    b += box(214, 188, 180, 66, REV_SOFT, REV)
    b += txt(304, 212, "칸마다 G 안 최근접 κ 개 평균", 12) + txt(304, 232, "d(y, p), κ = 1 (식 3)", 11, INK2)
    b += line(214, 221, 176, 221, REV, 1.6, marker="ar")
    b += box(24, 188, 150, 66, REV_SOFT, REV)
    b += txt(99, 212, "가우스 σ = 4", 12) + txt(99, 232, "문턱 θ 로 분할", 11, INK2)
    # 아래 설명
    b += box(24, 276, 892, 58, NODE, LINE)
    b += txt(40, 299, "이 그림의 점선 칸(문턱 τ)은 설계의 문이지만, 원문은 표마다 어떤 τ 로 이미지를 걸렀는지 적지 않는다.", 12, INK, "start")
    b += txt(40, 320, "표 2 · 3 의 픽셀 값이 τ 로 거른 뒤의 값인지, 시험 이미지 전부의 값인지 원문에 적혀 있지 않다.", 12, INK2, "start")
    svg("fig01_pipeline", 940, 352, b, "SPADE 의 두 단계 흐름")


def _diverge(name, title, rows, label, unit, lo, hi, w=900, color_pos=OK, color_neg=NO, note=None, right_txt=None):
    rh = 24
    top = 62
    x0, x1 = 170, w - 150
    zero = x0 + (0 - lo) / (hi - lo) * (x1 - x0)
    h = top + rh * len(rows) + 58 + (24 if note else 0)
    b = txt(w / 2, 28, title, 15, weight="bold")
    for t in range(int(lo), int(hi) + 1, unit):
        x = x0 + (t - lo) / (hi - lo) * (x1 - x0)
        b += line(x, top - 6, x, top + rh * len(rows), LINE, 1)
        b += txt(x, top - 12, ("%+d" % t) if t else "0", 11, INK2)
    b += line(zero, top - 6, zero, top + rh * len(rows), INK, 1.4)
    for i, (k, v, tail) in enumerate(rows):
        y = top + i * rh
        b += txt(x0 - 10, y + 16, k, 12, INK, "end")
        x = x0 + (v - lo) / (hi - lo) * (x1 - x0)
        if v >= 0:
            b += bar(zero, y + 4, x - zero, rh - 8, color_pos)
        else:
            b += bar(x, y + 4, zero - x, rh - 8, color_neg)
        b += txt(x1 + 8, y + 16, tail, 11, INK2, "start")
    yb = top + rh * len(rows) + 26
    b += txt(w / 2, yb, label, 12, INK2)
    if note:
        b += txt(w / 2, yb + 22, note, 12, INK)
    svg(name, w, h, b, title)


def fig02_t2():
    rows = []
    for k in CLASSES:
        r = T2[k]
        best = max(x for x in r[:7] if x is not None)
        who = [T2_COLS[i] for i in range(7) if r[i] == best]
        rows.append((k, r[7] - best, "%.1f 대 %d (%s)" % (r[7], best, " · ".join(who))))
    _diverge("fig02_t2_best_rival", "표 2 픽셀 ROCAUC — SPADE 빼기 그 부류 최고 상대", rows,
             "초록은 SPADE 가 높은 부류, 빨강은 낮은 부류. 상대 값은 정수로 인쇄되어 있다", 5, -10, 25,
             note="평균 96.0 대 CAVGA-Ru 89 는 차이 7.0. CAVGA-Ru 는 부류별 칸이 비어 이 그림에 없다")


def fig03_t3():
    # 두 상대: 단일 수용장 Student (표 3) · 묶음 (원문 Uninformed Students 표 3)
    w, rh, top = 940, 26, 74
    x0, x1 = 150, w - 60
    lo, hi = -25, 30
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    h = top + rh * len(CLASSES) + 74
    b = txt(w / 2, 26, "표 3 PRO — SPADE 빼기 Student(단일 수용장) · 빼기 묶음(여러 수용장)", 15, weight="bold")
    b += bar(250, 40, 14, 10, FWD) + txt(270, 50, "SPADE - Student (평균 차 +6.0)", 12, INK, "start")
    b += bar(520, 40, 14, 10, REV) + txt(540, 50, "SPADE - 묶음 (평균 차 +0.3, 묶음은 원문 Uninformed Students 표 3)", 12, INK, "start")
    for t in range(-25, 31, 5):
        b += line(X(t), top - 4, X(t), top + rh * len(CLASSES), LINE, 1)
        b += txt(X(t), top - 8, ("%+d" % t) if t else "0", 11, INK2)
    b += line(X(0), top - 4, X(0), top + rh * len(CLASSES), INK, 1.4)
    for i, k in enumerate(CLASSES):
        y = top + i * rh
        a = T3[k][7] - T3[k][0]
        m = T3[k][7] - MS[k]
        b += txt(x0 - 10, y + 17, k, 12, INK, "end")
        for v, c, dy in ((a, FWD, 3), (m, REV, 13)):
            if v >= 0:
                b += bar(X(0), y + dy, X(v) - X(0), 9, c)
            else:
                b += bar(X(v), y + dy, X(0) - X(v), 9, c)
            xt = X(v) + 5 if v >= 0 else X(v) - 5
            b += txt(xt, y + dy + 8, "%+.1f" % v, 10, INK2, "start" if v >= 0 else "end")
    yb = top + rh * len(CLASSES) + 24
    b += txt(w / 2, yb, "묶음과의 평균 차 +0.3 은 Transistor 하나(+20.8)가 만든다. Transistor 를 뺀 14 부류 평균은 92.04 대 93.17 로 묶음이 1.14 높다(내가 센 것)", 12, INK)
    b += txt(w / 2, yb + 22, "SPADE 가 높은 부류 8, 묶음이 높은 부류 7. 흩어짐은 어느 쪽 표에도 없다", 12, INK2)
    svg("fig03_t3_student_and_ensemble", w, h, b, "표 3 PRO 부류별 차이")


def fig04_t6():
    w, rh, top = 760, 26, 78
    cols = ["14 x 14", "28 x 28", "56 x 56"]
    xs = [230, 330, 430]
    h = top + rh * (len(CLASSES) + 1) + 64
    b = txt(w / 2, 26, "표 6 PRO — 단일 단계 빼기 세 단계 잇기(SPADE)", 15, weight="bold")
    b += txt(w / 2, 48, "양수면 단일 단계가 더 높다. 셀 안 수는 차이, 오른쪽 수는 SPADE 값", 12, INK2)
    for x, c in zip(xs, cols):
        b += txt(x + 45, top - 6, c, 12, INK, weight="bold")
    b += txt(590, top - 6, "SPADE", 12, INK, weight="bold")
    for i, k in enumerate(CLASSES + ["평균"]):
        y = top + i * rh
        b += txt(214, y + 17, k, 12, INK, "end", "bold" if k == "평균" else None)
        if k == "평균":
            vals = [mean(T6[c][j] - T6[c][3] for c in CLASSES) for j in range(3)]
            sp = mean(T6[c][3] for c in CLASSES)
        else:
            vals = [T6[k][j] - T6[k][3] for j in range(3)]
            sp = T6[k][3]
        for x, v in zip(xs, vals):
            if v > 0.05:
                f = OK_SOFT
            elif v < -8:
                f = NO
            elif v < -3:
                f = NO_SOFT
            else:
                f = NODE
            b += box(x, y + 2, 90, rh - 4, f, LINE, 1, 3)
            b += txt(x + 45, y + 17, "%+.1f" % v, 12, "#FFFFFF" if v < -8 else INK)
        b += txt(590, y + 17, "%.1f" % sp, 12, INK)
    yb = top + rh * (len(CLASSES) + 1) + 24
    b += txt(w / 2, yb, "초록 칸이 15 x 3 = 45 칸 중 12 칸. 그중 56 x 56 단독이 7 칸(내가 센 것)", 12, INK)
    b += txt(w / 2, yb + 22, "56 x 56 과 SPADE 의 부류별 차를 더한 59.8 중 Transistor · Cable 두 부류가 42.3 (70.7%)", 12, INK2)
    svg("fig04_t6_levels", w, h, b, "표 6 단계별 PRO 차이")


def fig05_t7():
    w, h = 880, 430
    b = txt(w / 2, 28, "이미지를 먼저 고르는 단계의 몫 — 원문이 잰 칸과 안 잰 칸", 15, weight="bold")
    rows = [
        ("무작위 10 장", 89.2, 73.2, REV, "표 7"),
        ("kNN 10 장", 91.4, 86.3, FWD, "표 7"),
        ("kNN 50 장", 91.7, 86.7, OK, "표 3 · 표 6"),
    ]
    x0, x1 = 210, 800
    lo, hi = 70.0, 100.0
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    for t in range(70, 101, 5):
        b += line(X(t), 68, X(t), 346, LINE, 1)
        b += txt(X(t), 62, str(t), 11, INK2)
    y = 76
    for name, av, gr, c, src in rows:
        b += txt(x0 - 12, y + 20, name, 13, INK, "end", "bold")
        b += txt(x0 - 12, y + 38, src, 11, INK2, "end")
        b += bar(x0, y + 6, X(av) - x0, 16, c)
        b += txt(X(av) + 6, y + 19, "평균 %.1f" % av, 12, INK, "start")
        b += bar(x0, y + 26, X(gr) - x0, 16, c)
        b += txt(X(gr) + 6, y + 39, "Grid %.1f" % gr, 12, INK, "start")
        y += 66
    b += txt(x0 - 12, y + 20, "학습 전체", 13, INK, "end", "bold")
    b += txt(x0 - 12, y + 38, "원문에 없음", 11, NO, "end")
    b += box(x0, y + 4, x1 - x0, 40, NO_SOFT, NO, dash="5,3")
    b += txt((x0 + x1) / 2, y + 29, "먼저 고르지 않은 칸은 표가 없다 — 고르는 단계가 잃는 값은 이 편에서 뽑히지 않는다", 12, INK)
    b += txt(w / 2, 374, "눈금은 70 에서 시작한다. 표 7 의 캡션은 지표 이름을 적지 않았고, 값이 PRO 열과 같은 범위라 PRO 로 읽었다(내 판단)", 12, INK2)
    b += txt(w / 2, 396, "무작위 대 kNN 차 2.2 중 Grid 13.1 이 15 부류 차의 합의 39.7% (평균이 부류 평균이라 할 때, 내가 센 것)", 12, INK2)
    b += txt(w / 2, 418, "무작위 추첨을 몇 번 돌렸는지 적혀 있지 않다", 12, INK2)
    svg("fig05_t7_selection", w, h, b, "표 7 과 먼저 고르는 단계")


def fig06_cost():
    import math
    w, h = 880, 356
    b = txt(w / 2, 28, "시험 이미지 한 장의 픽셀 단계 거리 계산 수 — 내가 센 것, 원문에 없음", 15, weight="bold")
    rows = [("K = 1", 1), ("K = 10 (표 7)", 10), ("K = 50 (MVTec)", 50), ("학습 전체 (평균 241.9 장)", MEAN_TRAIN)]
    x0, x1 = 230, 790
    lo, hi = 6.0, 10.0
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    for t in range(6, 11):
        b += line(X(t), 56, X(t), 226, LINE, 1)
        b += txt(X(t), 50, "10^%d" % t, 11, INK2)
    y = 64
    for name, k in rows:
        pairs = CELLS * k * CELLS
        b += txt(x0 - 12, y + 20, name, 12, INK, "end")
        b += bar(x0, y + 6, X(math.log10(pairs)) - x0, 22, FWD if k <= 50 else NO)
        b += txt(X(math.log10(pairs)) + 6, y + 22, "{:,.0f}".format(pairs), 12, INK, "start")
        y += 40
    b += box(24, 240, 832, 102, NODE, LINE)
    b += txt(40, 262, "가정: 세 단계를 56 x 56 격자 하나에 이어 붙이면 칸 3,136 · 차원 256 + 512 + 1,024 = 1,792. 원문은 이을 때 키우는 법을 적지 않는다.", 12, INK, "start")
    b += txt(40, 284, "K = 50 갤러리는 156,800 벡터이고 부동소수 4 바이트면 1.12 GB. 이미지 단계는 평균 241.9 번(2,048 차원)이라 쌍 수의 비가 2,032,481 배다.", 12, INK2, "start")
    b += txt(40, 306, "표 7 에서 K 를 50 에서 10 으로 줄이면 쌍 수는 5 분의 1 이고 평균 값 차는 0.3, Grid 차는 0.4 다.", 12, INK2, "start")
    b += txt(40, 328, "원문이 적은 시간 값은 없다. 0.66 초는 PatchCore 편이 다시 구현해 잰 값이다. STC 는 입력이 256 이라 칸 수가 이 셈과 다르다.", 12, INK2, "start")
    svg("fig06_cost", w, h, b, "K 별 거리 계산 수")


def fig07_margins():
    w, h = 880, 330
    b = txt(w / 2, 28, "표마다 SPADE 빼기 가장 가까운 상대 — 차이는 전부 흩어짐 없는 한 값끼리다", 15, weight="bold")
    rows = [
        ("표 1 MVTec 이미지", 85.5, 83.9, "ITAE"),
        ("표 2 MVTec 픽셀 ROCAUC", 96.0, 89, "CAVGA-Ru"),
        ("표 3 MVTec PRO", 91.7, 85.7, "Student 단일"),
        ("표 3 본문의 묶음 (값 없음)", 91.7, 91.4, "Uninformed Students 원문 표 3"),
        ("표 4 STC 이미지", 71.9, 72.5, "ITAE"),
        ("표 5 STC 픽셀 ROCAUC", 89.9, 85, "CAVGA-Ru"),
    ]
    x0, x1 = 240, 620
    lo, hi = -2.0, 8.0
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    for t in range(-2, 9, 2):
        b += line(X(t), 58, X(t), 58 + 38 * len(rows), LINE, 1)
        b += txt(X(t), 52, ("%+d" % t) if t else "0", 11, INK2)
    b += line(X(0), 58, X(0), 58 + 38 * len(rows), INK, 1.4)
    y = 62
    for name, s, r, who in rows:
        d = s - r
        b += txt(x0 - 12, y + 19, name, 12, INK, "end")
        if d >= 0:
            b += bar(X(0), y + 6, X(d) - X(0), 18, OK)
        else:
            b += bar(X(d), y + 6, X(0) - X(d), 18, NO)
        b += txt(max(X(d), X(0)) + 6, y + 20, "%+.1f" % d, 12, INK, "start")
        b += txt(x1 + 8, y + 20, "%s %s" % (who, r), 11, INK2, "start")
        y += 38
    svg("fig07_margins", w, h, b, "표마다 SPADE 와 상대의 차이")


def fig08_lineage():
    w, h = 900, 272
    b = txt(w / 2, 28, "최근접 이웃으로 이상을 재는 줄기 — 뱅크에 무엇을 넣는가", 15, weight="bold")
    items = [
        ("DN2 (Bergman 외 2020)", "이미지 전역 특징만", "kNN 거리 = 이미지 점수", "위치 찾기 없음", FWD_SOFT, FWD),
        ("SPADE (이 편)", "전역 특징으로 K 장 고른 뒤", "K 장의 칸 특징과 맞대기", "이미지 85.5 · 픽셀 96.0", REV_SOFT, REV),
        ("PaDiM", "칸마다 가우스 하나", "먼저 고르는 단계 없음", "자리에 기댄다", CODE_SOFT, CODE),
        ("PatchCore", "조각 특징 뱅크 하나", "먼저 고르는 단계 없음, 코어셋", "99.1 · 98.1", OK_SOFT, OK),
    ]
    bw, gap = 200, 18
    x = 24
    for i, (n, a, c, d, f, s) in enumerate(items):
        b += box(x, 58, bw, 138, f, s)
        b += txt(x + bw / 2, 84, n, 13, INK, weight="bold")
        b += txt(x + bw / 2, 116, a, 12, INK)
        b += txt(x + bw / 2, 140, c, 12, INK)
        b += txt(x + bw / 2, 170, d, 12, INK2)
        if i < 3:
            b += line(x + bw, 127, x + bw + gap - 2, 127, INK2, 1.4, marker="ai")
        x += bw + gap
    b += txt(w / 2, 226, "PaDiM · PatchCore 칸의 값과 설명은 PatchCore 노트가 옮긴 값이고 이 편의 말이 아니다. 화살표는 읽는 순서이지 인용 관계 전부가 아니다", 12, INK2)
    b += txt(w / 2, 250, "SPADE 값은 이 편의 표 1 · 2, PatchCore 값은 코어셋 25% 의 이미지 · 픽셀 AUROC", 12, INK2)
    svg("fig08_lineage", w, h, b, "최근접 이웃 줄기")


if __name__ == "__main__":
    recount()
    print("\n== 그림 ==")
    fig01_pipeline()
    fig02_t2()
    fig03_t3()
    fig04_t6()
    fig05_t7()
    fig06_cost()
    fig07_margins()
    fig08_lineage()
