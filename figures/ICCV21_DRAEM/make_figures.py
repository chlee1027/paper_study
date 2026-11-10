# -*- coding: utf-8 -*-
"""DRAEM 노트의 그림을 만들고, 노트가 인용하는 다시 계산한 값을 찍는다.

표준 라이브러리만 쓰고 바깥 데이터를 읽지 않는다. 표 값은 원문 표 1 ~ 4 와 보충 자료 표 1 을 옮긴 상수다.
그림 9 의 값은 PDF 벡터 좌표(쪽 8)를 눈금선으로 맞춰 읽은 것이고, 좌표 자체를 상수로 둔다.
PaDiM 원 논문 값(WRN-50-2 · Rd550 픽셀 AUROC)은 PaDiM 원문 4.3 절 부류별 표에서 옮긴 것이다.
"""
import math
import os

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "'Malgun Gothic','Noto Sans KR',sans-serif"
INK, MUTE, LINE = "#222222", "#666666", "#cccccc"
A, B, C, D = "#2f6db3", "#c8553d", "#4a9a6a", "#8a8a8a"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(x, y, s, size=12, fill=INK, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" font-family="{FONT}">{esc(s)}</text>')


def R(x, y, w, h, fill, stroke="none"):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}"/>'


def L(x1, y1, x2, y2, stroke=LINE, width=1, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>'


def Ci(x, y, r, fill, stroke="none"):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}"/>'


def PL(pts, stroke, width=2, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{width}"{d}/>'


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


# ---------------------------------------------------------------- 원문 값
CL = ["bottle", "capsule", "grid", "leather", "pill", "tile", "transistor", "zipper",
      "cable", "carpet", "hazelnut", "metal nut", "screw", "toothbrush", "wood"]
TEX = {"grid", "leather", "tile", "carpet", "wood"}

# 표 1 (이미지 AUROC). 열 순서는 원문 그대로 [1] [26] [4] [31] [20] [11] DRAEM
M1 = ["GANomaly", "DAGAN", "US", "RIAD", "MAD", "PaDiM", "DRAEM"]
T1 = [[79.4, 98.3, 99.0, 99.9, 100, 99.9, 99.2], [72.1, 68.7, 86.1, 88.4, 92.3, 91.3, 98.5],
      [74.3, 86.7, 81.0, 99.6, 92.9, 96.7, 99.9], [80.8, 94.4, 88.2, 100, 100, 100, 100],
      [67.1, 76.8, 87.9, 83.8, 83.4, 93.3, 98.9], [72.0, 96.1, 99.1, 98.7, 97.4, 98.1, 99.6],
      [80.8, 79.4, 81.8, 90.9, 95.9, 97.4, 93.1], [74.4, 78.1, 91.9, 98.1, 97.9, 90.3, 100],
      [71.1, 66.5, 86.2, 81.9, 94.0, 92.7, 91.8], [82.1, 90.3, 91.6, 84.2, 95.5, 99.8, 97.0],
      [87.4, 100, 93.1, 83.3, 98.7, 92.0, 100.0], [69.4, 81.5, 82.0, 88.5, 93.1, 98.7, 98.7],
      [100, 100, 54.9, 84.5, 81.2, 85.8, 93.9], [70.0, 95.0, 95.3, 100, 95.8, 96.1, 100],
      [92.0, 97.9, 97.7, 93.0, 97.6, 99.2, 99.1]]
AVG1 = [78.2, 87.3, 87.7, 91.7, 94.4, 95.5, 98.0]

# 표 2 (픽셀 AUROC, AP). 열 US RIAD PaDiM DRAEM
M2 = ["US", "RIAD", "PaDiM", "DRAEM"]
T2 = [[(97.8, 74.2), (98.4, 76.4), (98.2, 77.3), (99.1, 86.5)], [(96.8, 25.9), (92.8, 38.2), (98.6, 46.7), (94.3, 49.4)],
      [(89.9, 10.1), (98.8, 36.4), (97.1, 35.7), (99.7, 65.7)], [(97.8, 40.9), (99.4, 49.1), (99.0, 53.5), (98.6, 75.3)],
      [(96.5, 62.0), (95.7, 51.6), (95.7, 61.2), (97.6, 48.5)], [(92.5, 65.3), (89.1, 52.6), (94.1, 52.4), (99.2, 92.3)],
      [(73.7, 27.1), (87.7, 39.2), (97.6, 72.0), (90.9, 50.7)], [(95.6, 36.1), (97.8, 63.4), (98.4, 58.2), (98.8, 81.5)],
      [(91.9, 48.2), (84.2, 24.4), (96.7, 45.4), (94.7, 52.4)], [(93.5, 52.2), (96.3, 61.4), (99.0, 60.7), (95.5, 53.5)],
      [(98.2, 57.8), (96.1, 33.8), (98.1, 61.1), (99.7, 92.9)], [(97.2, 83.5), (92.5, 64.3), (97.3, 77.4), (99.5, 96.3)],
      [(97.4, 7.8), (98.8, 43.9), (98.4, 21.7), (97.6, 58.2)], [(97.9, 37.7), (98.9, 50.6), (98.8, 54.7), (98.1, 44.7)],
      [(92.1, 53.3), (85.8, 38.2), (94.1, 46.3), (96.4, 77.7)]]
AVG2 = [(93.9, 45.5), (94.2, 48.2), (97.4, 55.0), (97.3, 68.4)]

# PaDiM 원 논문 4.3 절 부류별 표, WRN-50-2 · Rd550 픽셀 AUROC
PADIM_PAPER = {"carpet": 99.1, "grid": 97.3, "leather": 99.2, "tile": 94.1, "wood": 94.9, "bottle": 98.3, "cable": 96.7,
               "capsule": 98.5, "hazelnut": 98.2, "metal nut": 97.2, "pill": 95.7, "screw": 98.5, "toothbrush": 98.8,
               "transistor": 97.5, "zipper": 98.5}

# 표 3 (검출 AUROC, 픽셀 AUROC, 픽셀 AP)
T3 = [("Disc.", "재구성 망 없음", 93.9, 92.7, 62.5), ("Recon.-AE", "판별 망 없음, SSIM 지도", 83.9, 89.7, 47.5),
      ("Recon.-AE MSGMS", "판별 망 없음, MSGMS 지도", 90.7, 93.4, 50.9), ("Božič 외 [6]", "망을 지도 검출 망으로", 92.8, 93.9, 60.7),
      ("DRAEM ImageNet", "질감 출처 ImageNet", 97.9, 97.0, 67.9), ("DRAEM color", "단색 영역, 변형 없음", 96.2, 92.6, 56.5),
      ("DRAEM rect", "모양을 직사각형으로", 96.9, 96.8, 65.1), ("DRAEM no aug", "변형 · β 둘 다 없음", 97.4, 94.5, 64.3),
      ("DRAEM img aug", "변형만", 97.4, 95.0, 64.5), ("DRAEM β", "β 만", 97.9, 97.1, 68.4), ("DRAEM", "전부", 98.0, 97.3, 68.4)]
PADIM_ROW = (95.5, 97.4, 55.0)  # 표 1 · 2 의 PaDiM 평균, 가장 센 상대

# 보충 자료 표 1 (가짜 이상으로 배운 지도 방법, 검출 AUROC / 픽셀 AUROC)
S1 = [("DRAEM", 98.0, 97.3), ("Rački 외 [5]", 90.7, 84.3), ("Božič 외 [3]", 92.8, 93.9)]

# 표 4 (DAGM). AUROC TPR TNR CA
T4 = [("RIAD", 78.6, 79.2, 69.1, 70.4), ("US", 72.5, 72.6, 65.3, 66.2), ("MAD", 82.4, 78.7, 85.7, 66.2),
      ("PaDiM", 95.0, 83.3, 97.5, 95.7), ("DRAEM", 99.0, 96.5, 99.4, 98.5)]

# 그림 9: 쪽 8 의 벡터 좌표(pt). 눈금선 y = 209.30 (55) ~ 73.84 (100), x = 94.92 (10^0), 138.98 (10^1)
F9_X = [94.92, 108.18, 147.97, 174.49, 260.18]
F9_Y = {"det_aug": [83.48, 81.67, 79.86, 79.86, 79.86], "loc_aug": [87.09, 86.49, 82.57, 82.87, 81.97],
        "det_no": [143.08, 119.00, 87.09, 83.17, 81.67], "loc_no": [205.09, 164.15, 115.99, 98.83, 90.40]}


def f9_val(y):
    return 55 + (209.30 - y) * 45 / (209.30 - 73.84)


def f9_n(x):
    return 10 ** ((x - 94.92) / (138.98 - 94.92))


F9 = {k: [round(f9_val(y), 1) for y in v] for k, v in F9_Y.items()}
F9_N = [f9_n(x) for x in F9_X]


def mean(v):
    return sum(v) / len(v)


def split(col):
    t = [v for c, v in zip(CL, col) if c in TEX]
    o = [v for c, v in zip(CL, col) if c not in TEX]
    return mean(t), mean(o)


def share_range(tpr, tnr, ca, h=0.05):
    """CA = w TPR + (1 - w) TNR 이면 w = (TNR - CA) / (TNR - TPR). 각 값의 반올림 폭 ±h 를 넣은 범위."""
    vals = []
    for a in (-h, h):
        for b in (-h, h):
            for c in (-h, h):
                den = (tnr + b) - (tpr + a)
                if abs(den) > 1e-9:
                    vals.append(((tnr + b) - (ca + c)) / den)
    return (tnr - ca) / (tnr - tpr), min(vals), max(vals)


# ---------------------------------------------------------------- 그림
def fig01():
    rows = []
    for c, r in zip(CL, T1):
        o = max(r[:6])
        rows.append((c, round(r[6] - o, 1), M1[r[:6].index(o)]))
    rows.sort(key=lambda x: -x[1])
    W, H = 820, 70 + 24 * len(rows) + 40
    b = [T(20, 24, "표 1 · 이미지 AUROC: DRAEM 에서 그 부류의 가장 센 상대를 뺀 값 (내 뺄셈)", 14, weight="bold"),
         T(20, 44, "0 은 같은 값. 이긴 5 부류 + 같은 4 부류 = 원문의 「15 중 9」. 진 6 부류는 상대 이름을 적었다.", 11, MUTE)]
    x0, sc = 480, 30
    b.append(L(x0, 56, x0, 56 + 24 * len(rows), INK))
    for i, (c, d, who) in enumerate(rows):
        y = 60 + i * 24
        col = C if c in TEX else A
        w = d * sc
        b.append(R(min(x0, x0 + w), y, max(abs(w), 1.5), 16, col if d >= 0 else B))
        b.append(T(20, y + 13, c + (" (질감)" if c in TEX else ""), 11))
        lab = f"{d:+.1f}" if d > 0 else ("같음" if d == 0 else f"{d:+.1f} ({who})")
        b.append(T((x0 + w + 6) if d >= 0 else (x0 + w - 6), y + 13, lab, 11, MUTE, "start" if d >= 0 else "end"))
    b.append(T(20, H - 14, "파랑 = 물체가 이김 · 초록 = 질감이 이김 · 빨강 = 짐. 막대 축척 1 점 = 30 px.", 11, MUTE))
    save("fig01_tab1_margin.svg", W, H, b)


def fig02():
    rows = sorted([(c, round(r[3][1] - r[2][1], 1)) for c, r in zip(CL, T2)], key=lambda x: -x[1])
    W, H = 820, 70 + 24 * len(rows) + 40
    b = [T(20, 24, "표 2 · 픽셀 AP: DRAEM 에서 PaDiM 을 뺀 값 (내 뺄셈). 평균 차 13.4 점", 14, weight="bold"),
         T(20, 44, "위 다섯 부류(그중 넷이 질감)가 차이 합의 84.3% 를 낸다. 네 부류는 DRAEM 이 낮다.", 11, MUTE)]
    x0, sc = 420, 8
    b.append(L(x0, 56, x0, 56 + 24 * len(rows), INK))
    for i, (c, d) in enumerate(rows):
        y = 60 + i * 24
        w = d * sc
        b.append(R(min(x0, x0 + w), y, abs(w), 16, (C if c in TEX else A) if d > 0 else B))
        b.append(T(20, y + 13, c + (" (질감)" if c in TEX else ""), 11))
        b.append(T((x0 + w + 6) if d >= 0 else (x0 + w - 6), y + 13, f"{d:+.1f}", 11, MUTE, "start" if d >= 0 else "end"))
    b.append(T(20, H - 14, "질감 5 부류 평균 차 +23.2 점, 물체 10 부류 평균 차 +8.5 점. 막대 축척 1 점 = 8 px.", 11, MUTE))
    save("fig02_tab2_ap_gain.svg", W, H, b)


def fig03():
    steps = [("PaDiM (표 2 의 가장 센 상대)", 55.0, D), ("Božič 외, 가짜 이상으로 학습 (표 3)", 60.7, D),
             ("Disc. = 재구성 망을 뺀 DRAEM (표 3)", 62.5, A), ("DRAEM (표 2 · 3)", 68.4, B)]
    W, H = 820, 250
    b = [T(20, 24, "픽셀 AP 13.4 점을 나눠 보면 (내 뺄셈)", 14, weight="bold"),
         T(20, 44, "재구성 망 없이 가짜 이상으로 분할만 배운 Disc. 가 이미 PaDiM 보다 7.5 점(13.4 의 56%) 높다.", 11, MUTE)]
    x0, sc = 330, 6
    for i, (n, v, col) in enumerate(steps):
        y = 64 + i * 40
        b += [T(20, y + 18, n, 11), R(x0, y, v * sc, 26, col), T(x0 + v * sc + 8, y + 18, f"{v:.1f}", 12, INK)]
    b.append(L(x0 + 55.0 * sc, 56, x0 + 55.0 * sc, 224, MUTE, 1, "4 3"))
    b.append(T(20, H - 10, "같은 저자가 같은 평가로 낸 줄끼리의 차이다. 반복이 없어 흩어짐은 모른다.", 11, MUTE))
    save("fig03_ap_steps.svg", W, H, b)


def fig04():
    W, H = 900, 60 + 30 * len(T3) + 50
    cols = [("검출 AUROC", 0, 80, 100), ("픽셀 AUROC", 1, 85, 100), ("픽셀 AP", 2, 40, 75)]
    b = [T(20, 24, "표 3 의 열한 줄과 PaDiM 평균(점선). 점 하나가 표의 값 하나다(반복 수는 적혀 있지 않다)", 14, weight="bold")]
    px0, pw = 330, 170
    for j, (name, k, lo, hi) in enumerate(cols):
        x = px0 + j * (pw + 20)
        b.append(T(x + pw / 2, 48, f"{name} ({lo} ~ {hi})", 11, INK, "middle", "bold"))
        pv = PADIM_ROW[k]
        xx = x + (pv - lo) / (hi - lo) * pw
        b.append(L(xx, 56, xx, 56 + 30 * len(T3), MUTE, 1, "4 3"))
        b.append(L(x, 56, x, 56 + 30 * len(T3), LINE))
    for i, (n, desc, *v) in enumerate(T3):
        y = 70 + i * 30
        if i in (4, 7, 10):
            b.append(L(20, y - 15, W - 20, y - 15, LINE))
        b += [T(20, y + 4, n, 11, INK, weight="bold" if n == "DRAEM" else "normal"), T(150, y + 4, desc, 10, MUTE)]
        for j, (name, k, lo, hi) in enumerate(cols):
            x = px0 + j * (pw + 20)
            val = v[k]
            xx = x + (val - lo) / (hi - lo) * pw
            col = B if val < PADIM_ROW[k] else A
            b += [Ci(xx, y, 4.5, col), T(xx + 8, y + 4, f"{val:.1f}", 10, MUTE)]
    b.append(T(20, H - 14, "빨강 = PaDiM 평균보다 낮음. DRAEM color 의 픽셀 AUROC 92.6 은 표 2 의 세 상대(93.9 · 94.2 · 97.4) 모두보다 낮다.", 11, MUTE))
    save("fig04_tab3_rows.svg", W, H, b)


def fig05():
    W, H = 760, 400
    ox, oy, pw, ph = 80, 50, 520, 280
    b = [T(20, 26, "그림 9 를 벡터 좌표에서 다시 그림 (원문 눈금선으로 맞춤, 점 다섯씩)", 14, weight="bold")]
    lo, hi = 55, 100
    xmax = math.log10(F9_N[-1]) * 1.08

    def px(n):
        return ox + math.log10(n) / xmax * pw

    def py(v):
        return oy + ph - (v - lo) / (hi - lo) * ph
    for v in range(55, 101, 5):
        b += [L(ox, py(v), ox + pw, py(v), LINE), T(ox - 8, py(v) + 4, str(v), 10, MUTE, "end")]
    for e, lab in ((0, "1"), (1, "10"), (2, "100"), (3, "1,000")):
        b += [L(px(10 ** e), oy, px(10 ** e), oy + ph, LINE), T(px(10 ** e), oy + ph + 18, lab, 10, MUTE, "middle")]
    b.append(T(ox + pw / 2, oy + ph + 40, "질감 출처 이미지 수 (로그 축). 점의 위치: 1 · 2 · 16 · 64 · 약 5,634", 11, MUTE, "middle"))
    # 원문과 같은 표기: 변형 있음 = 주황 실선, 변형 없음 = 하늘 점선, 검출 = 원, 위치 = 사각(원문은 삼각)
    series = [("det_aug", "#e08a1e", "", "o", "검출, 변형 있음"), ("loc_aug", "#e08a1e", "", "s", "위치, 변형 있음"),
              ("det_no", "#2bb3d6", "6 4", "o", "검출, 변형 없음"), ("loc_no", "#2bb3d6", "6 4", "s", "위치, 변형 없음")]

    def mk(x, y, shape, col):
        return Ci(x, y, 4, col, INK) if shape == "o" else R(x - 4, y - 4, 8, 8, col, INK)
    for i, (k, col, dash, shape, lab) in enumerate(series):
        pts = [(px(n), py(v)) for n, v in zip(F9_N, F9[k])]
        b.append(PL(pts, col, 2, dash))
        for x, y in pts:
            b.append(mk(x, y, shape, col))
        ly = oy + 20 + i * 22
        b += [L(ox + pw + 20, ly, ox + pw + 50, ly, col, 2, dash), mk(ox + pw + 35, ly, shape, col), T(ox + pw + 56, ly + 4, lab, 10)]
    b.append(T(20, H - 10, "오른쪽 끝 값은 표 3 의 DRAEM(98.0 / 97.3)과 DRAEM no aug(97.4 / 94.5)와 같다. 그림에 x = 10 인 점은 없다.", 11, MUTE))
    save("fig05_fig9_redrawn.svg", W, H, b)


def fig06():
    na = T3[7][2:]
    grid = [("둘 다 없음", na), ("변형만", T3[8][2:]), ("β 만", T3[9][2:]), ("둘 다", T3[10][2:])]
    W, H = 820, 230
    b = [T(20, 24, "표 3 의 2 x 2: 질감 변형과 불투명도 β (변형 · β 둘 다 없는 줄과의 차, 내 뺄셈)", 14, weight="bold")]
    hdr = ("", "검출 AUROC", "픽셀 AUROC", "픽셀 AP")
    xs = (30, 260, 440, 620)
    for x, h in zip(xs, hdr):
        b.append(T(x, 56, h, 12, weight="bold"))
    for i, (n, v) in enumerate(grid):
        y = 70 + i * 34
        b.append(R(20, y, 780, 28, "#f4f4f4"))
        b.append(T(xs[0], y + 19, n, 12))
        for j in range(3):
            d = v[j] - na[j]
            b.append(T(xs[j + 1], y + 19, f"{v[j]:.1f}  ({d:+.1f})", 12, B if j == 2 and d > 3 else INK))
    b.append(T(20, H - 14, "β 만으로 픽셀 AP 차 4.1 이 다 난다. 변형만은 +0.2. 둘을 더한 줄은 β 만과 0.1 · 0.2 · 0.0 다르다.", 11, MUTE))
    save("fig06_low_perturbation.svg", W, H, b)


def fig07():
    W, H = 820, 290
    b = [T(20, 24, "표 4 의 TPR · TNR · CA 로 거꾸로 낸 「시험 이미지 중 결함 비율」 w (내 계산)", 14, weight="bold"),
         T(20, 44, "같은 시험 집합을 같은 문턱으로 셌다면 CA = w TPR + (1 - w) TNR 이고 w 는 줄마다 같아야 한다. 막대는 반올림 폭 ±0.05 를 넣은 범위.", 11, MUTE)]
    x0, sc = 200, 900
    for v in (0, 0.1, 0.2, 0.3, 0.4):
        b += [L(x0 + v * sc / 2, 60, x0 + v * sc / 2, 230, LINE), T(x0 + v * sc / 2, 248, f"{v:.1f}", 10, MUTE, "middle")]
    ref = 150 / 1150
    b += [L(x0 + ref * sc / 2, 58, x0 + ref * sc / 2, 232, B, 1.5, "5 3"), T(x0 + ref * sc / 2 + 4, 70, "0.130", 10, B)]
    for i, (n, au, tpr, tnr, ca) in enumerate(T4):
        y = 80 + i * 30
        b.append(T(20, y + 12, n, 12))
        if not (min(tpr, tnr) <= ca <= max(tpr, tnr)):
            b.append(T(x0, y + 12, f"CA {ca} 가 TPR {tpr} · TNR {tnr} 사이에 있지 않다 → 같은 문턱의 정확도일 수 없다", 11, B))
            continue
        w, lo, hi = share_range(tpr, tnr, ca)
        b += [R(x0 + lo * sc / 2, y + 2, (hi - lo) * sc / 2, 14, "#d9e4f2", A), Ci(x0 + w * sc / 2, y + 9, 3.5, A),
              T(x0 + hi * sc / 2 + 8, y + 13, f"{w:.3f} ({lo:.3f} ~ {hi:.3f})", 10, MUTE)]
    b.append(T(20, H - 14, "점선 0.130 = 150 / 1,150. DAGM 의 부류별 구성은 이 편에 없고 내가 아는 값이다. 세 줄은 그 값을 범위에 품고 DRAEM 줄은 품지 않는다.", 11, MUTE))
    save("fig07_tab4_share.svg", W, H, b)


def fig08():
    rows = [(c, r[2][0], PADIM_PAPER[c]) for c, r in zip(CL, T2)]
    W, H = 820, 70 + 22 * len(rows) + 40
    b = [T(20, 24, "표 2 의 PaDiM 픽셀 AUROC 와 PaDiM 원 논문(WRN-50-2 · Rd550) 값", 14, weight="bold"),
         T(20, 44, "같은 칸은 15 중 4. 다른 11 칸 중 10 칸이 ±0.2 안이고 wood 만 0.8 낮다. 출처는 적혀 있지 않다.", 11, MUTE)]
    for i, (c, a, p) in enumerate(rows):
        y = 64 + i * 22
        d = round(a - p, 1)
        b += [T(30, y + 12, c, 11), T(250, y + 12, f"{a:.1f}", 11), T(330, y + 12, f"{p:.1f}", 11),
              T(410, y + 12, f"{d:+.1f}" if d else "같음", 11, B if abs(d) >= 0.5 else MUTE)]
    b += [T(250, 60, "표 2", 10, MUTE), T(330, 60, "원 논문", 10, MUTE), T(410, 60, "차", 10, MUTE)]
    b.append(T(20, H - 14, f"평균: 표 2 는 97.4, 원 논문 부류 평균은 {mean(list(PADIM_PAPER.values())):.2f} (인쇄 97.5).", 11, MUTE))
    save("fig08_padim_two_sources.svg", W, H, b)


def fig09():
    W, H = 880, 200
    nodes = [("AE-SSIM (2018)", ["재구성 오차", "SSIM 으로 비교"]), ("RIAD (2020)", ["같은 저자", "가리고 채우기"]),
             ("DRAEM (이 편)", ["재구성 + 판별", "가짜 이상 학습"]), ("Reverse Distillation", ["다음 칸", "아직 안 읽음"]),
             ("SimpleNet · EfficientAD", ["다음 칸", "아직 안 읽음"])]
    b = [T(20, 24, "이 편의 자리: 재구성 계열에서 「차이를 배운다」 로 넘어가는 칸", 14, weight="bold")]
    for i, (a, c) in enumerate(nodes):
        x = 14 + i * 174
        b += [R(x, 50, 158, 100, "#fbe9e5" if i == 2 else "#eef2f7", LINE), T(x + 79, 80, a, 11, INK, "middle", "bold")]
        for k, l in enumerate(c):
            b.append(T(x + 79, 106 + k * 18, l, 11, MUTE, "middle"))
        if i < 4:
            b.append(L(x + 158, 100, x + 174, 100, INK, 1.5))
    b.append(T(20, H - 18, "산업 이상 탐지 2막: DRAEM → Reverse Distillation → SimpleNet → EfficientAD", 11, MUTE))
    save("fig09_lineage.svg", W, H, b)


# ---------------------------------------------------------------- 찍기
def report():
    print("== 표 1 평균 다시 내기 (부류 15 평균, 인쇄값, 질감 5, 물체 10)")
    for j, m in enumerate(M1):
        col = [r[j] for r in T1]
        t, o = split(col)
        print(f"  {m:9s} {mean(col):.2f} 인쇄 {AVG1[j]}  질감 {t:.2f} 물체 {o:.2f}")
    strict = sum(r[6] > max(r[:6]) for r in T1)
    tie = sum(r[6] == max(r[:6]) for r in T1)
    print(f"  DRAEM 단독 최고 {strict}, 같은 최고 {tie}, 합 {strict + tie}")
    print("== 표 2 평균 다시 내기 (픽셀 AUROC, AP, AP 질감, AP 물체)")
    for j, m in enumerate(M2):
        a = [r[j][0] for r in T2]
        p = [r[j][1] for r in T2]
        t, o = split(p)
        print(f"  {m:6s} {mean(a):.2f} {mean(p):.2f} 인쇄 {AVG2[j]}  AP 질감 {t:.2f} 물체 {o:.2f}")
    for k, name in ((0, "픽셀 AUROC"), (1, "AP")):
        s = sum(r[3][k] > max(x[k] for x in r[:3]) for r in T2)
        print(f"  {name}: DRAEM 단독 최고 {s} / 15")
    g = sorted([(c, r[3][1] - r[2][1]) for c, r in zip(CL, T2)], key=lambda x: -x[1])
    tot = sum(v for _, v in g)
    print(f"  AP 차 합 {tot:.1f}, 위 다섯 {[c for c, _ in g[:5]]} 몫 {sum(v for _, v in g[:5]) / tot:.3f}, 음수 {[c for c, v in g if v < 0]}")
    t, o = split([r[3][1] - r[2][1] for r in T2])
    print(f"  AP 차 평균 질감 {t:.2f} 물체 {o:.2f}")
    t, o = split([r[6] - r[5] for r in T1])
    print(f"  이미지 AUROC DRAEM - PaDiM 평균 질감 {t:.2f} 물체 {o:.2f}")
    diffs = [round(r[2][0] - PADIM_PAPER[c], 1) for c, r in zip(CL, T2)]
    print(f"  PaDiM 표 2 대 원 논문: 같은 칸 {diffs.count(0.0)}, 최대 차 {max(map(abs, diffs))}")
    print("== 표 3 (DRAEM 에서 뺀 값 / PaDiM 평균과의 차)")
    full = T3[-1][2:]
    for n, _, *v in T3:
        print(f"  {n:16s} {[round(full[i] - v[i], 1) for i in range(3)]}  PaDiM 대비 {[round(v[i] - PADIM_ROW[i], 1) for i in range(3)]}")
    print(f"  Disc. 의 AP 몫 (62.5 - 55.0) / 13.4 = {(62.5 - 55.0) / 13.4:.3f}")
    print("== 표 4 거꾸로 낸 결함 비율 w")
    for n, au, tpr, tnr, ca in T4:
        inside = min(tpr, tnr) <= ca <= max(tpr, tnr)
        if inside:
            w, lo, hi = share_range(tpr, tnr, ca)
            print(f"  {n:6s} w {w:.3f} 범위 {lo:.3f} ~ {hi:.3f}")
        else:
            print(f"  {n:6s} CA 가 TPR · TNR 사이 밖")
    print(f"  150/1150 = {150 / 1150:.4f}; DRAEM 줄에 w = 0.1304 를 넣은 CA = {0.1304 * 96.5 + 0.8696 * 99.4:.2f}")
    print("== 그림 9 (x 값, 그리고 넷)")
    print("  x", [round(n, 1) for n in F9_N])
    for k, v in F9.items():
        print(f"  {k}: {v}")
    print("== 보충 자료 표 1", S1)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for fn in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09):
        fn()
    report()
