# -*- coding: utf-8 -*-
"""PatchCore 노트(Roth 외, CVPR 2022)의 그림 열여섯을 만든다.

색과 글꼴은 앞선 노트들(퍼셉트론부터 Wide ResNet 까지)의 그림과 맞췄다 — 저장소의 노트들이 한 벌로 읽히게
하려는 것이다. 결과 그림의 계열 색은 셋을 고정해 쓴다(PatchCore · 앞선 방법 · 셋째 계열).
바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

이 파일이 직접 계산하는 것:
  - WRN-50-2 (torchvision 꼴, 보폭이 3x3 에 있는 병목) 의 단계별 출력 크기와 입력 크기별 조각 수
  - 부류별 기억 뱅크 크기(학습 이미지 수 x 조각 수)와 코어셋 25 · 10 · 1% 의 크기, 탐욕 뽑기의 거리 계산 횟수
  - 부록 표 S1 ~ S4 의 부류별 값의 평균과 인쇄된 평균의 차이, 만점(100) 부류 수
  - 표 5 의 추론 시간에 '고정 몫 + 뱅크 비례 몫' 직선을 최소제곱으로 맞춘 값
  - 식 (7) 의 재가중 w 가 움직이는 범위(내가 유도한 것)
  - 그림 3 과 같은 모양의 2 차원 장난감 자료에서 탐욕 코어셋과 무작위 뽑기의 덮는 반지름
  - 표 S5 의 '남긴 비율' 칸을 부류당 평균 학습 이미지 수로 다시 낸 값
논문 그림 4 · 5 · S4 · S5 · S6 의 값은 원 그림 이미지(PDF 에 든 래스터)에서 눈금선과 표식 중심을 픽셀로 찾아
읽은 값을 상수로 적었다. 읽기 오차는 각 상수 옆에 적었다.
MVTec AD 의 부류별 학습 · 시험 이미지 수는 이 논문에 없고 MVTec AD 데이터 논문(Bergmann 외 2019)의 값이다 —
합이 이 논문의 3,629 · 1,725 와 같은지를 이 파일이 확인한다.
"""
import io, os, math, random


OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"   # 그림 상자 배경
NODE      = "#F6F7F5"   # 노드 안쪽
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 입력 쪽, 정해져 있는 것
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 고르는 것, 학습되는 것
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 기억 뱅크
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"   # 초록
NO        = "#C0392B"   # 빨강
# 결과 그림 계열 색 — PatchCore · 앞선 방법 · 셋째 계열. 이 순서로 고정한다.
S_PC      = "#EB6834"
S_PREV    = "#2A78D6"
S_THIRD   = "#1BAF7A"
S_GRAY    = "#8A939B"
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


def rect(x, y, w, h, fill, op=None):
    a = '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"' % (x, y, max(w, 0), max(h, 0), fill)
    if op:
        a += ' opacity="%s"' % op
    return a + "/>"


def line(x1, y1, x2, y2, color=None, sw=1.2, dash=None, marker=None, op=None):
    a = '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"' % (
        x1, y1, x2, y2, color or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if marker:
        a += ' marker-end="url(#%s)"' % marker
    if op:
        a += ' opacity="%s"' % op
    return a + "/>"


def circ(cx, cy, r, fill=None, stroke=None, sw=1.2, op=None):
    a = '<circle cx="%.1f" cy="%.1f" r="%s" fill="%s" stroke="%s" stroke-width="%s"' % (
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
    d = "M" + " L".join("%.1f,%.1f" % p for p in pts)
    return path(d, stroke, sw=sw, dash=dash)


def dot(x, y, col, r=4.5):
    return circ(x, y, r, col, col)


def fmt(n):
    return "{:,}".format(int(round(n)))


def axis_y(b, x0, x1, y_of, ticks, label_fmt="%g", size=10):
    for v in ticks:
        b += line(x0, y_of(v), x1, y_of(v), LINE, 1)
        b += txt(x0 - 6, y_of(v) + 4, label_fmt % v, size, anchor="end", fill=MUTED)
    return b


def mean(v):
    return sum(v) / float(len(v))


print("그림을 만든다 ->", OUT)


# ── 자료 — 논문 표 (글자 층에서 옮겼다) ─────────────────────────────────────
CLASSES = ["Bottle", "Cable", "Capsule", "Carpet", "Grid", "Hazelnut", "Leather", "Metal Nut",
           "Pill", "Screw", "Tile", "Toothbrush", "Transistor", "Wood", "Zipper"]
# MVTec AD 부류별 학습 · 시험 이미지 수 — 이 논문에 없다. MVTec AD 데이터 논문(Bergmann 외 2019)의 값.
N_TRAIN = [209, 224, 219, 280, 264, 391, 245, 220, 267, 320, 230, 60, 213, 247, 240]
N_TEST  = [83, 150, 132, 117, 78, 110, 124, 115, 167, 160, 117, 42, 100, 79, 151]

# 표 S1 · S2 · S3 · S4 (부류 순서는 CLASSES)
S1 = {
    "PatchCore-25": (99.1, [100, 99.5, 98.1, 98.7, 98.2, 100, 100, 100, 96.6, 98.1, 98.7, 100, 100, 99.2, 99.4]),
    "PatchCore-10": (99.0, [100, 99.4, 97.8, 98.7, 97.9, 100, 100, 100, 96.0, 97.0, 98.9, 99.7, 100, 99.0, 99.5]),
    "PatchCore-1":  (99.0, [100, 99.3, 98.0, 98.0, 98.6, 100, 100, 99.7, 97.0, 96.4, 99.4, 100, 99.9, 99.2, 99.2]),
    "PatchSVDD":    (92.1, [98.6, 90.3, 76.7, 92.9, 94.6, 92.0, 90.9, 94.0, 86.1, 81.3, 97.8, 100, 91.5, 96.5, 97.9]),
    "DifferNet":    (94.9, [99.0, 95.9, 86.9, 92.9, 84.0, 99.3, 97.1, 96.1, 88.8, 96.3, 99.4, 98.6, 91.1, 99.8, 95.1]),
    "MahalanobisAD": (95.8, [100, 95.0, 95.1, 100, 89.7, 99.1, 100, 94.7, 88.7, 85.2, 99.8, 96.9, 95.5, 99.6, 97.9]),
}
S2 = {
    "PatchCore-25": (98.1, [98.6, 98.4, 98.8, 99.0, 98.7, 98.7, 99.3, 98.4, 97.4, 99.4, 95.6, 98.7, 96.3, 95.0, 98.8]),
    "PatchCore-10": (98.1, [98.6, 98.5, 98.9, 99.1, 98.7, 98.7, 99.3, 98.4, 97.6, 99.4, 95.9, 98.7, 96.4, 95.1, 98.9]),
    "PatchCore-1":  (98.0, [98.5, 98.2, 98.8, 98.9, 98.6, 98.6, 99.3, 98.4, 97.1, 99.2, 96.1, 98.5, 94.9, 95.1, 98.8]),
    "SPADE":        (96.0, [98.4, 97.2, 99.0, 97.5, 93.7, 99.1, 97.6, 98.1, 96.5, 98.9, 87.4, 97.9, 94.1, 88.5, 96.5]),
    "PaDiM":        (97.5, [98.3, 96.7, 98.5, 99.1, 97.3, 98.2, 99.2, 97.2, 95.7, 98.5, 94.1, 98.8, 98.5, 94.9, 98.5]),
}
S3 = {
    "PatchCore-25": (93.4, [96.2, 92.5, 95.5, 96.6, 96.0, 93.8, 98.9, 91.4, 93.2, 97.9, 87.3, 91.5, 83.7, 89.4, 97.1]),
    "PatchCore-10": (93.5, [96.1, 92.6, 95.5, 96.6, 95.9, 93.9, 98.9, 91.3, 94.1, 97.9, 87.4, 91.4, 83.5, 89.6, 97.1]),
    "PatchCore-1":  (93.1, [95.9, 91.6, 95.5, 96.5, 96.1, 93.8, 98.9, 91.2, 92.9, 97.1, 88.3, 90.2, 81.2, 89.5, 97.0]),
    "SPADE":        (91.7, [95.5, 90.9, 93.7, 94.7, 86.7, 95.4, 97.2, 94.4, 94.6, 96.0, 75.6, 93.5, 87.4, 87.4, 92.6]),
    "PaDiM":        (92.1, [94.8, 88.8, 93.5, 96.2, 94.6, 92.6, 97.8, 85.6, 92.7, 94.4, 86.0, 93.1, 84.5, 91.1, 95.9]),
}
S4 = {
    "(2,3) AUROC":   (99.4, [100, 99.6, 98.2, 98.4, 99.8, 100, 100, 100, 97.2, 98.9, 98.9, 100, 100, 99.5, 99.9]),
    "(2,3) pwAUROC": (98.2, [98.6, 98.4, 99.1, 98.7, 98.7, 98.8, 99.3, 98.8, 97.8, 99.3, 96.1, 98.8, 96.4, 95.1, 98.9]),
    "(2,3) PRO":     (94.4, [96.6, 93.8, 96.0, 97.4, 96.8, 91.2, 99.1, 94.8, 94.0, 97.5, 89.5, 95.5, 84.8, 91.7, 97.8]),
    "(1,2,3) AUROC": (99.2, [100, 99.7, 98.1, 98.2, 98.3, 100, 100, 100, 97.1, 99.0, 98.9, 98.9, 99.7, 99.9, 99.7]),
    "(1,2,3) pwAUROC": (98.4, [98.6, 98.7, 99.1, 98.7, 98.8, 98.8, 99.3, 99.0, 98.6, 99.5, 96.3, 98.9, 97.1, 95.2, 99.0]),
    "(1,2,3) PRO":   (95.0, [96.6, 94.6, 96.3, 97.5, 97.0, 91.5, 99.1, 95.4, 96.0, 98.1, 90.0, 95.8, 85.9, 92.0, 98.0]),
}
# 표 1 (이미지 AUROC) · 표 2 (픽셀 AUROC) · 표 3 (PRO)
T1 = [("SPADE", 85.5), ("PatchSVDD", 92.1), ("DifferNet", 94.9), ("PaDiM", 95.3), ("Mah.AD", 95.8),
      ("PaDiM*", 97.9), ("PatchCore-25%", 99.1), ("PatchCore-10%", 99.0), ("PatchCore-1%", 99.0)]
T1_MIS = {"PatchCore-25%": 42, "PatchCore-10%": 47, "PatchCore-1%": 49}
T2 = [("AESSIM", 87), ("γ-VAE+grad", 88.8), ("CAVGA-Rw", 89), ("PatchSVDD", 95.7), ("SPADE", 96.0),
      ("PaDiM", 97.5), ("PatchCore-25%", 98.1), ("PatchCore-10%", 98.1), ("PatchCore-1%", 98.0)]
T3 = [("AESSIM", 69.4), ("Student", 85.7), ("SPADE", 91.7), ("PaDiM", 92.1),
      ("PatchCore-25%", 93.4), ("PatchCore-10%", 93.5), ("PatchCore-1%", 93.1)]
# 표 5 — (이름, 뱅크 비율, (이미지, 픽셀, PRO), 초)
T5 = [("PatchCore-100%", 1.00, (99.1, 98.0, 93.3), 0.60), ("PatchCore-10%", 0.10, (99.0, 98.1, 93.5), 0.22),
      ("PatchCore-1%", 0.01, (99.0, 98.0, 93.1), 0.17), ("PatchCore-100% + IVFPQ", None, (98.0, 97.9, 93.0), 0.20),
      ("SPADE (다시 구현)", None, (85.3, 96.6, 91.5), 0.66), ("PaDiM (다시 구현)", None, (95.4, 97.3, 91.8), 0.19)]
# 표 S5 — 적은 표본. 평균과 ± (몇 번 돌렸는지는 적혀 있지 않다)
SHOTS = [1, 2, 5, 10, 16, 20, 50]
RETAINED = [0.4, 0.8, 2.1, 4.1, 6.6, 8.3, 21]
S5_IMG = {"SPADE": [(71.6, .7), (73.4, 1.3), (75.2, 1.5), (77.5, 1.1), (78.9, .9), (79.6, .8), (81.1, .4)],
          "PaDiM": [(76.1, .4), (78.9, .6), (81.0, .2), (83.2, .7), (85.5, .6), (86.5, .3), (90.1, .3)],
          "PatchCore-10": [(83.4, .6), (86.4, .9), (90.8, .8), (93.6, .6), (95.4, .7), (95.8, .6), (97.5, .3)],
          "PatchCore-25": [(84.1, .7), (87.2, 1.0), (91.0, .9), (93.8, .5), (95.5, .6), (95.9, .6), (97.7, .4)]}
S5_PIX = {"SPADE": [91.9, 93.1, 94.5, 95.4, 95.7, 95.7, 96.2], "PaDiM": [88.2, 90.5, 92.5, 93.9, 94.8, 95.1, 96.3],
          "PatchCore-10": [92.0, 93.1, 94.8, 96.2, 96.8, 96.9, 97.8], "PatchCore-25": [92.4, 93.3, 94.8, 96.1, 96.8, 96.9, 97.7]}
S5_PRO = {"SPADE": [83.5, 85.8, 88.3, 89.6, 90.1, 90.1, 90.8], "PaDiM": [72.4, 77.8, 82.7, 85.9, 87.5, 88.2, 90.4],
          "PatchCore-10": [82.4, 85.1, 88.7, 90.9, 91.8, 92.0, 93.0], "PatchCore-25": [83.7, 86.0, 88.8, 90.9, 91.7, 91.9, 92.8]}
# 표 S6 — 백본. (이름, 뱅크 %, 이미지, 픽셀, PRO)
S6 = [("ResNet50", 10, 99.0, 98.1, 93.3), ("ResNet50", 1, 98.7, 97.8, 93.3),
      ("WideResNet50", 10, 98.9, 98.1, 93.5), ("WideResNet50", 1, 99.0, 98.0, 93.1),
      ("ResNet101", 10, 98.6, 97.9, 92.5), ("ResNet101", 1, 98.7, 97.8, 92.2),
      ("WideResNet101", 10, 99.1, 98.2, 93.4), ("WideResNet101", 1, 99.0, 98.1, 93.0),
      ("ResNeXt101", 10, 98.9, 98.0, 92.8), ("ResNeXt101", 1, 98.7, 97.8, 92.6)]

# ── 자료 — 원 그림에서 눈금을 읽은 값 ──────────────────────────────────────
# 그림 4 위 (= 그림 S5 위). 이웃 크기 p = 1..7. 표식 중심을 픽셀로 찾았다.
#   이미지 AUROC 축은 1 점이 53.75 px, 픽셀 AUROC 축은 1 점이 117.5 px, PRO 축은 1 점이 32.5 px.
#   중심 찾기 오차를 ±1 px 로 잡으면 읽기 오차는 ±0.02 · ±0.01 · ±0.03 점이다.
#   다른 표식에 가려 중심을 못 찾은 칸은 None 으로 두고 본문에 눈으로 읽은 값을 따로 적었다.
P_NB = [1, 2, 3, 4, 5, 6, 7]
F4_DET_CORE = [96.29, 98.80, 98.89, 98.40, 97.60, 96.00, 94.29]
F4_DET_FULL = [95.37, 98.48, 99.11, None, None, None, None]     # 4~7 은 주황 표식 아래에 겹쳐 있다
F4_SEG_CORE = [97.20, 97.90, 98.10, 98.00, 97.60, 96.80, 96.00]
F4_SEG_FULL = [96.50, 97.60, 97.99, None, None, 96.69, 95.90]
F4_PRO_CORE = [92.60, 92.89, 93.50, 92.39, 90.88, 87.90, 85.29]
F4_PRO_FULL = [91.68, None, None, None, None, None, 84.93]
# 그림 4 아래 (= 그림 S5 아래). 단계 조합별 막대 윗변. 1 px 이 0.025 · 0.009 · 0.026 점.
HIER = ["1", "2", "3", "1+2", "2+3", "1+2+3"]
F4_HIER_DET = [93.30, 98.98, 97.60, 97.31, 98.98, 97.89]
F4_HIER_SEG = [96.40, 97.49, 96.90, 97.40, 98.09, 98.09]
F4_HIER_PRO = [91.49, 93.49, 87.96, 93.28, 93.49, 94.20]
# 그림 5 (= 그림 S6). 가로축은 로그 눈금이고 10^0 과 10^-2 사이가 246 px 다.
#   표식 가로 위치를 로그로 되돌리면 50 · 25 · 10 · 5 · 1 · 0.3 · 0.1 % 가 나온다(0.3 은 10^-2.52).
#   세로 1 px 이 이미지 0.048 · 픽셀 0.010 · PRO 0.029 점.
SUB_X = [100, 50, 25, 10, 5, 1, 0.3, 0.1]
F5_DET = {"코어셋": [99.1, None, 99.19, 98.97, 98.88, 98.97, 98.06, 95.58],
          "무작위": [99.1, 98.97, 98.59, 97.97, 97.39, 93.28, 86.15, None],
          "학습한 대리점": [99.1, 97.97, 97.29, 96.19, 94.57, 90.70, None, None]}
F5_SEG = {"코어셋": [98.0, None, 98.10, 98.10, 98.10, 97.99, 97.40, 96.00],
          "무작위": [98.0, 97.99, 97.90, 97.80, 97.60, 96.99, 96.20, None],
          "학습한 대리점": [98.0, 97.40, 97.10, 97.10, 96.90, 96.30, 95.30, None]}
F5_PRO = {"코어셋": [93.3, None, 93.39, 93.51, 93.59, 93.10, 91.38, 87.52],
          "무작위": [93.3, 93.10, 92.99, 92.79, 92.39, 90.89, 88.28, None],
          "학습한 대리점": [93.3, 92.19, 91.99, 91.49, 90.90, 88.89, 86.11, None]}
# 그림 S4. 막대 오른쪽 끝. 1 px 이 이미지 0.006 · 픽셀 0.0016 · PRO 0.007 점. 점선(기준) 위치도 같은 방식.
S4_ROWS = [("S 448, p 9", 96.69, 97.79, 92.22), ("S 448, p 7", 98.51, 98.29, 93.44),
           ("S 360, p 7", 97.34, 97.71, 91.43), ("S 448, p 5", 99.22, 98.27, 94.91),
           ("S 360, p 5", 99.09, 98.30, 94.37), ("S 448, p 3", 98.69, 97.84, 93.89),
           ("S 360, p 3", 99.04, 97.86, 94.80), ("S 288, p 3", 98.75, 97.96, 94.57)]
S4_BASE = (99.13, 98.12, 93.50)
# 그림 S3 상자 안의 숫자 (단위가 적혀 있지 않다)
S3_ERR = [("PatchCore-1", 6.93, 2.44), ("PatchCore-10", 5.72, 2.52), ("SPADE", 21.62, 15.10), ("PaDiM", 9.45, 6.03)]


# ── 셈 1. 단계별 출력 크기와 조각 수 ────────────────────────────────────────
def conv_out(n, k, s, p):
    return (n + 2 * p - k) // s + 1


def stages(n):
    c1 = conv_out(n, 7, 2, 3)
    mp = conv_out(c1, 3, 2, 1)
    l2 = conv_out(mp, 3, 2, 1)
    l3 = conv_out(l2, 3, 2, 1)
    l4 = conv_out(l3, 3, 2, 1)
    return c1, mp, l2, l3, l4


print("\n[셈 1] 입력 크기별 단계 출력과 조각 수 (WRN-50-2, torchvision 꼴 — 보폭이 3x3 에 있다)")
SIZES = [224, 256, 280, 288, 320, 360, 448, 576]
SHAPE = {}
for n in SIZES:
    c1, l1, l2, l3, l4 = stages(n)
    SHAPE[n] = (l1, l2, l3, l4)
    print("  입력 %3d: layer1 %3dx%-3d layer2 %3dx%-3d layer3 %2dx%-2d layer4 %2dx%-2d -> 조각 %s"
          % (n, l1, l1, l2, l2, l3, l3, l4, l4, fmt(l2 * l2)))
PATCH224 = SHAPE[224][1] ** 2


# ── 셈 2. 기억 뱅크 크기 ────────────────────────────────────────────────────
print("\n[셈 2] 부류별 기억 뱅크 (224 입력, 이미지당 %d 조각)" % PATCH224)
assert sum(N_TRAIN) == 3629 and sum(N_TEST) == 1725, "MVTec 수의 합이 논문과 다르다"
print("  학습 이미지 합 %d (= 5354 - 1725), 시험 합 %d — 논문의 총계와 같다" % (sum(N_TRAIN), sum(N_TEST)))
BANK = [n * PATCH224 for n in N_TRAIN]
for c, n, m in zip(CLASSES, N_TRAIN, BANK):
    print("  %-11s 학습 %3d  뱅크 %9s  25%% %8s  10%% %7s  1%% %6s" % (c, n, fmt(m), fmt(m * .25), fmt(m * .1), fmt(m * .01)))
AVG_TRAIN = sum(N_TRAIN) / 15.0
AVG_BANK = AVG_TRAIN * PATCH224
print("  부류 평균 학습 %.2f 장 -> 뱅크 %s, 15 부류 합 %s" % (AVG_TRAIN, fmt(AVG_BANK), fmt(sum(BANK))))
for d in (1536, 1024):
    print("  차원 %d · float32 이면 평균 뱅크 %.2f GB (10^9 바이트), 1%% 코어셋 %.1f MB"
          % (d, AVG_BANK * d * 4 / 1e9, AVG_BANK * .01 * d * 4 / 1e6))
for frac in (0.25, 0.10, 0.01):
    l = AVG_BANK * frac
    print("  탐욕 뽑기 %2d%%: 반복 l = %s, 거리 계산 l x |M| = %.2e 번 (투영 차원 d* 짜리)" % (frac * 100, fmt(l), l * AVG_BANK))
print("  시험 이미지 하나의 거리 계산 (전수 탐색): 100%% %.2e · 10%% %.2e · 1%% %.2e"
      % (PATCH224 * AVG_BANK, PATCH224 * AVG_BANK * .1, PATCH224 * AVG_BANK * .01))


# ── 셈 3. 부록 표의 평균 맞춰 보기 ──────────────────────────────────────────
print("\n[셈 3] 부록 표의 부류별 값 평균 대 인쇄된 평균 (반올림 허용 폭 ±0.10: 부류 값 ±0.05 + 평균 ±0.05)")
for tname, T in (("S1", S1), ("S2", S2), ("S3", S3), ("S4", S4)):
    for k, (avg, v) in T.items():
        m = mean(v)
        flag = "  <- 허용 폭 밖" if abs(m - avg) > 0.10 + 1e-9 else ""
        print("  %s %-16s 인쇄 %5.1f  평균 %7.3f  차이 %+.3f  100 인 부류 %d%s" % (tname, k, avg, m, m - avg, sum(1 for x in v if x == 100), flag))


# ── 셈 4. 추론 시간 직선 ────────────────────────────────────────────────────
pts = [(f, t) for _, f, _, t in T5 if f is not None]
n = len(pts); sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
sxx = sum(p[0] ** 2 for p in pts); sxy = sum(p[0] * p[1] for p in pts)
TB = (n * sxy - sx * sy) / (n * sxx - sx * sx)
TA = (sy - TB * sx) / n
print("\n[셈 4] 표 5 의 세 점에 '시간 = a + b x 뱅크 비율' 을 맞춤: a = %.3f 초, b = %.3f 초" % (TA, TB))
for f, t in pts:
    print("  비율 %.2f: 표 %.2f 초, 직선 %.3f 초, 고정 몫이 차지하는 비율 %.0f%%" % (f, t, TA + TB * f, 100 * TA / t))


# ── 셈 5. 식 (7) 의 재가중 범위 (내가 유도한 것) ─────────────────────────────
def w_of(b, delta):
    # m* 가 N_b(m*) 안에 들고, 나머지 b-1 개가 시험 조각에서 d* + delta 거리에 같이 놓인 경우
    return 1.0 - 1.0 / (1.0 + (b - 1) * math.exp(delta))


print("\n[셈 5] 식 (7) 의 w = 1 - exp(d*) / sum exp(d_m). 모든 d_m >= d* 이므로 w 는 [1 - 1/b, 1) 안이다")
for b in (2, 3, 5, 9):
    print("  b = %d: 최소 %.3f, delta=1 에서 %.3f, delta=3 에서 %.4f, 최대/최소 배수 %.3f"
          % (b, 1 - 1.0 / b, w_of(b, 1), w_of(b, 3), 1 / (1 - 1.0 / b)))


# ── 셈 6. 장난감 코어셋 ─────────────────────────────────────────────────────
rng = random.Random(7)
TOY = []
for cx, cy, sd, cnt in ((0.25, 0.30, 0.05, 330), (0.70, 0.25, 0.04, 200), (0.55, 0.75, 0.06, 60), (0.15, 0.80, 0.02, 10)):
    for _ in range(cnt):
        TOY.append((min(max(rng.gauss(cx, sd), 0.01), 0.99), min(max(rng.gauss(cy, sd), 0.01), 0.99)))


def d2(a, b_):
    return (a[0] - b_[0]) ** 2 + (a[1] - b_[1]) ** 2


def greedy(points, l, start):
    chosen = [start]
    mind = [d2(p, points[start]) for p in points]
    for _ in range(l - 1):
        i = max(range(len(points)), key=lambda j: mind[j])
        chosen.append(i)
        for j, p in enumerate(points):
            dd = d2(p, points[i])
            if dd < mind[j]:
                mind[j] = dd
    return chosen


def cover_radius(points, idx):
    return math.sqrt(max(min(d2(p, points[i]) for i in idx) for p in points))


L_TOY = 30
G_IDX = greedy(TOY, L_TOY, rng.randrange(len(TOY)))
R_IDX = rng.sample(range(len(TOY)), L_TOY)
RG, RR = cover_radius(TOY, G_IDX), cover_radius(TOY, R_IDX)


def in_cluster4(idx):
    return sum(1 for i in idx if i >= 590)


print("\n[셈 6] 장난감 2 차원 자료 %d 점에서 %d 점(%.0f%%)을 뽑음" % (len(TOY), L_TOY, 100.0 * L_TOY / len(TOY)))
print("  덮는 반지름(식 (5) 의 max-min): 탐욕 %.3f, 무작위 %.3f (%.1f 배)" % (RG, RR, RR / RG))
print("  점 10 개짜리 작은 무리에서 뽑힌 수: 탐욕 %d, 무작위 %d" % (in_cluster4(G_IDX), in_cluster4(R_IDX)))


# ── 셈 7. 표 S5 의 남긴 비율 ────────────────────────────────────────────────
print("\n[셈 7] 표 S5 '남긴 %%' = 표본 수 / 부류 평균 학습 이미지 %.2f" % AVG_TRAIN)
for s, r in zip(SHOTS, RETAINED):
    print("  %2d 장: 셈 %.2f%% · 표 %.1f%% · 칫솔(학습 60 장) 기준 %.1f%%" % (s, 100.0 * s / AVG_TRAIN, r, 100.0 * s / 60))
print("  MTD: 결함 없는 925 장의 20%% = %d 장이 시험, %d 장이 학습 (논문은 개수를 적지 않았다)" % (round(925 * .2), 925 - round(925 * .2)))
print("  표 1 오분류율: 42 / 1725 = %.2f%%, 47 / 1725 = %.2f%%, 49 / 1725 = %.2f%%" % (4200 / 1725., 4700 / 1725., 4900 / 1725.))


# ── 셈 8. 부류별로 PatchCore-25 가 지는 자리 ────────────────────────────────
print("\n[셈 8] 부류별로 PatchCore-25% 보다 높은 칸 (표 S2 · S3)")
for tname, T in (("픽셀 AUROC", S2), ("PRO", S3)):
    pc = T["PatchCore-25"][1]
    for other in ("SPADE", "PaDiM"):
        ov = T[other][1]
        lose = [(c, a, o) for c, a, o in zip(CLASSES, pc, ov) if o > a]
        print("  %s %-5s 가 높은 부류 %d: %s" % (tname, other, len(lose), ", ".join("%s %.1f>%.1f" % (c, o, a) for c, a, o in lose)))
# 보폭 s 로 줄인 뱅크 비율 (위치 0, s, 2s, ... 를 남긴다고 보고 센 것)
for s_ in (2, 3):
    k = len(range(0, SHAPE[224][1], s_))
    print("  보폭 %d: 한 변 %d -> %d, 뱅크 %.1f%%" % (s_, SHAPE[224][1], k, 100.0 * k * k / PATCH224))
# 집계 창이 이미지 한 변에서 차지하는 비율 — 창 한 변 = p x 8 px (layer2 격자 간격으로 센 것이고 수용장이 아니다)
for n, p in ((224, 3), (288, 3), (360, 3), (448, 3), (360, 5), (448, 5), (360, 7), (448, 7), (448, 9)):
    print("  입력 %d, p %d: 집계 창 한 변 %d px (격자 간격 기준) = 이미지 한 변의 %.1f%%" % (n, p, p * 8, 100.0 * p / SHAPE[n][1]))
print()


# ── 그림 1. 흐름 ────────────────────────────────────────────────────────────
W, H = 840, 440
b = defs()
b += txt(20, 30, "PatchCore 의 흐름 — 학습은 '배우기'가 아니라 '모으고 줄이기'다", 15, anchor="start", weight="bold")
b += box(20, 50, 520, 230, fill="none", stroke=FWD, dash="5,4")
b += txt(30, 70, "학습 쪽 (정상 이미지만, 역전파 없음)", 12, anchor="start", fill=FWD, weight="bold")
steps = [(40, "정상 이미지 N 장", "224x224 로 자름"), (160, "ImageNet 으로 배운", "WRN-50-2 (얼림)"),
         (280, "layer2 · layer3", "3x3 이웃 평균 · 합침"), (400, "기억 뱅크 M", "784 x N 개 조각 특징")]
for x, t1, t2 in steps:
    b += box(x, 95, 110, 62, fill=CODE_SOFT if "뱅크" in t1 else NODE, stroke=CODE if "뱅크" in t1 else INK2)
    b += txt(x + 55, 121, t1, 11, weight="bold")
    b += txt(x + 55, 139, t2, 10, fill=INK2)
for x in (150, 270, 390):
    b += line(x, 126, x + 10, 126, INK2, 1.4, marker="ai")
b += line(455, 157, 455, 190, CODE, 1.6, marker="ac")
b += box(360, 192, 170, 70, fill=CODE_SOFT, stroke=CODE, sw=1.6)
b += txt(445, 214, "탐욕 코어셋 뽑기", 12, weight="bold", fill=CODE)
b += txt(445, 232, "무작위 사영 뒤 max-min 으로", 10, fill=INK2)
b += txt(445, 248, "25 · 10 · 1 % 만 남김", 10, fill=INK2)
b += txt(40, 214, "학습되는 파라미터가 없다.", 11, anchor="start", fill=INK2)
b += txt(40, 232, "부류마다 뱅크 하나 (15 부류 = 15 개).", 11, anchor="start", fill=INK2)
b += txt(40, 250, "평균 부류 뱅크 189,676 개 (내 셈).", 11, anchor="start", fill=INK2)
b += box(560, 50, 260, 360, fill="none", stroke=REV, dash="5,4")
b += txt(570, 70, "시험 쪽", 12, anchor="start", fill=REV, weight="bold")
tsteps = [(95, "시험 이미지 → 같은 추출", "조각 784 개"), (170, "조각마다 M 에서", "가장 가까운 거리 (식 6)"),
          (245, "가장 먼 조각 하나", "+ 이웃 재가중 (식 7) → 이미지 점수"), (320, "조각 거리를 제자리에", "→ 224 로 늘리고 σ=4 흐림 → 분할 지도")]
for y, t1, t2 in tsteps:
    b += box(580, y, 220, 55, fill=REV_SOFT if y in (245, 320) else NODE, stroke=REV if y in (245, 320) else INK2)
    b += txt(690, y + 22, t1, 11, weight="bold")
    b += txt(690, y + 40, t2, 10, fill=INK2)
for y in (150, 225, 300):
    b += line(690, y, 690, y + 18, INK2, 1.4, marker="ai")
b += path("M530,227 C548,227 548,197 578,197", CODE, sw=1.6, marker="ac")
for k, t in enumerate(["새로 만든 것 셋: (1) 중간 단계 특징을 3x3 이웃 평균으로 묶은", "조각 특징, (2) 그 조각을 다 모은 뱅크를 탐욕 코어셋으로 줄이기,",
                       "(3) 최근접 거리에 이웃 밀도를 곱하는 재가중."]):
    b += txt(20, 306 + 19 * k, t, 12, anchor="start")
for k, t in enumerate(["SPADE 는 이미지 전체 특징으로 먼저 후보를 고른 뒤 픽셀을 봤고,", "PaDiM 은 위치마다 가우스 하나를 뒀다. PatchCore 는 위치를 묻지",
                       "않는 뱅크 하나에 모든 조각을 넣고 시험 조각마다 그 전체를 찾는다."]):
    b += txt(20, 370 + 17 * k, t, 11, anchor="start", fill=INK2)
b += txt(20, 424, "784 · 189,676 은 내가 센 값이다(224 입력 · WRN-50-2). 논문 본문에는 조각 수와 뱅크 크기가 없다.", 10, anchor="start", fill=MUTED)
svg("fig01_pipeline", W, H, b, "PatchCore 의 학습과 시험 흐름")


# ── 그림 2. 단계별 크기와 조각 수 ────────────────────────────────────────────
W, H = 840, 420
b = defs()
b += txt(20, 30, "224 입력에서 WRN-50-2 의 단계 출력 — 쓰는 것은 layer2 와 layer3 (내 셈)", 15, anchor="start", weight="bold")
sts = [("layer1", 256, SHAPE[224][0], False), ("layer2", 512, SHAPE[224][1], True),
       ("layer3", 1024, SHAPE[224][2], True), ("layer4", 2048, SHAPE[224][3], False)]
for j, (nm, c, s, used) in enumerate(sts):
    x = 30 + 200 * j
    side = 24 + s * 2.2
    col = S_PC if used else MUTED
    b += box(x + 90 - side / 2, 175 - side / 2, side, side, fill=REV_SOFT if used else NODE, stroke=col, sw=2 if used else 1)
    b += txt(x + 90, 62, nm, 13, weight="bold", fill=col)
    b += txt(x + 90, 315, "%s 채널 x %dx%d" % (fmt(c), s, s), 12)
    b += txt(x + 90, 335, "보폭 누적 %d px" % (224 // s), 11, fill=INK2)
b += line(490, 175, 368, 175, S_PC, 1.6, marker="ar")
b += txt(429, 166, "양선형으로 28x28 로 늘림", 10, fill=S_PC)
b += txt(30, 365, "조각 수 = layer2 격자 = 28 x 28 = 784.  이어 붙이면 512 + 1,024 = 1,536 차원 — 논문은 이 숫자를 적지 않고 '미리 정한 차원 d' 라고만 적는다.", 11, anchor="start")
row = "입력 크기별 조각 수 (layer2 격자):  " + " · ".join("%d → %s" % (n, fmt(SHAPE[n][1] ** 2)) for n in (224, 280, 320, 360, 448, 576))
b += txt(30, 390, row, 11, anchor="start", fill=INK2)
b += txt(30, 410, "layer1 · layer4 는 그림 4 의 단계 실험에서만 쓴다. 단계 번호 1 ~ 4 는 논문의 j 와 같다(공간 해상도가 바뀌는 블록 묶음의 끝 출력).", 10, anchor="start", fill=MUTED)
svg("fig02_feature_shapes", W, H, b, "WRN-50-2 단계별 출력 크기와 조각 수")


# ── 그림 3. 국소 이웃 집계 ──────────────────────────────────────────────────
W, H = 840, 380
b = defs()
b += txt(20, 30, "국소 이웃 집계 — 해상도를 그대로 두고 3x3 이웃의 특징을 평균한다 (식 1 · 2 · 3)", 15, anchor="start", weight="bold")
G0x, G0y, C = 40, 60, 36
for i in range(7):
    for j in range(7):
        inn = 2 <= i <= 4 and 2 <= j <= 4
        b += box(G0x + C * j, G0y + C * i, C - 2, C - 2, fill=REV_SOFT if inn else NODE, stroke=S_PC if inn else LINE, rx=2)
b += box(G0x + C * 3 + 6, G0y + C * 3 + 6, C - 14, C - 14, fill=S_PC, stroke=S_PC, rx=2)
b += txt(G0x + C * 3.5 - 1, G0y + 7 * C + 22, "특징 지도 φ(i, j): 칸마다 c* 차원 벡터", 11, fill=INK2)
b += line(310, 186, 380, 186, INK2, 1.6, marker="ai")
b += txt(345, 176, "f_agg", 11, fill=INK2, style="italic")
b += txt(345, 206, "= 평균", 10, fill=INK2)
b += box(395, 150, 70, 70, fill=S_PC, stroke=S_PC)
b += txt(430, 190, "(h, w)", 11, fill="#FFFFFF", weight="bold")
b += txt(430, 240, "같은 (h, w) 에 놓는다", 10, fill=INK2)
b += box(500, 60, 320, 240, fill=NODE, stroke=LINE)
lines_ = [("식 (1): N_p(h,w) = {(a,b): |a−h| ≤ ⌊p/2⌋, |b−w| ≤ ⌊p/2⌋}", INK),
          ("p = 3 이면 9 칸, p = 5 이면 25 칸.", INK2),
          ("식 (3): 모든 (h, w) 에서 만들고 보폭 s = 1 이라", INK),
          ("격자 크기가 그대로다 (28x28 → 28x28).", INK2),
          ("", INK),
          ("왜: 수용장을 넓히되 더 깊은 단계로 가지 않는다.", INK),
          ("깊이 가면 ImageNet 쪽으로 치우치고 해상도가 준다.", INK2),
          ("", INK),
          ("읽을 때 걸리는 자리: 식 (1) 은 홀수 p 를 전제한다", NO),
          ("('uneven patchsizes'). 그런데 그림 4 는 p = 2 · 4 · 6", NO),
          ("값도 그린다. 식 (1) 대로면 p = 2 와 3 이 같은 9 칸인데", NO),
          ("그림 4 의 값은 98.48 대 99.11 로 다르다.", NO)]
for k, (t, col) in enumerate(lines_):
    b += txt(512, 84 + 18 * k, t, 11, anchor="start", fill=col)
b += txt(20, 350, "작은 예시: 28x28 지도의 가장자리 칸 (1, 1) 은 이웃이 지도 밖으로 나간다. 논문은 가장자리 처리(채우기)를 적지 않았다.", 11, anchor="start", fill=MUTED)
b += txt(20, 370, "'적응 평균 풀링(adaptive average pooling)' 이 공간 이웃 평균인지 채널 쪽 차원 맞추기인지도 문장 하나로는 갈리지 않는다(24절).", 11, anchor="start", fill=MUTED)
svg("fig03_neighbourhood", W, H, b, "국소 이웃 집계")


# ── 그림 4. 부류별 뱅크 크기 ────────────────────────────────────────────────
W, H = 840, 470
b = defs()
b += txt(20, 30, "부류별 기억 뱅크 크기 = 학습 이미지 수 x 784 (224 입력) — 내 셈", 15, anchor="start", weight="bold")
BX0, BX1 = 150, 640
mx = max(BANK)
def BX(v):
    return BX0 + v / 320000.0 * (BX1 - BX0)
for v in (0, 100000, 200000, 300000):
    b += line(BX(v), 50, BX(v), 425, LINE, 1)
    b += txt(BX(v), 442, fmt(v), 10, fill=MUTED)
for i, (c, n, m) in enumerate(zip(CLASSES, N_TRAIN, BANK)):
    y = 56 + 24.5 * i
    b += txt(140, y + 12, "%s (%d)" % (c, n), 11, anchor="end")
    b += rect(BX0, y, BX(m) - BX0, 16, CODE_SOFT)
    b += rect(BX0, y, BX(m * .25) - BX0, 16, CODE)
    b += txt(BX(m) + 6, y + 12, fmt(m), 10, anchor="start", fill=INK2)
b += box(700, 60, 130, 200, fill=NODE, stroke=LINE)
for k, t in enumerate(["옅은 막대 = 100 %", "진한 막대 = 25 %", "", "부류 평균", fmt(AVG_BANK) + " 개", "", "1 % 코어셋", "평균 " + fmt(AVG_BANK * .01) + " 개",
                       "칫솔 470 · 개암 3,065"]):
    b += txt(708, 84 + 20 * k, t, 10, anchor="start", fill=INK if k in (3, 6) else INK2, weight="bold" if k in (3, 6) else None)
b += txt(20, 462, "괄호 안 학습 이미지 수는 MVTec AD 데이터 논문의 값이다(이 논문에는 합 3,629 만 있다). 막대 길이는 차원과 무관한 '벡터 개수'다.", 11, anchor="start", fill=MUTED)
svg("fig04_bank_sizes", W, H, b, "부류별 기억 뱅크 크기")


# ── 그림 5. 장난감 코어셋 ───────────────────────────────────────────────────
W, H = 840, 470
b = defs()
b += txt(20, 30, "탐욕 코어셋 대 무작위 — 그림 3 과 같은 모양의 장난감 자료 600 점에서 30 점(5%)", 15, anchor="start", weight="bold")
for k, (title, idx, rr, col) in enumerate((("탐욕 코어셋 (알고리즘 1, 사영 없음)", G_IDX, RG, S_PC),
                                           ("무작위 뽑기", R_IDX, RR, S_PREV))):
    x0, y0, S = 30 + 410 * k, 60, 300
    b += box(x0, y0, S + 60, S + 20, fill=NODE, stroke=LINE)
    b += txt(x0 + (S + 60) / 2, y0 - 6, title, 12, weight="bold", fill=col)
    for p in TOY:
        b += circ(x0 + 30 + p[0] * S, y0 + 10 + p[1] * S, 1.6, "#9FB3C0", "none", 0)
    for i in idx:
        p = TOY[i]
        b += circ(x0 + 30 + p[0] * S, y0 + 10 + p[1] * S, 4.2, col, INK, 0.8)
    b += txt(x0 + (S + 60) / 2, y0 + S + 44, "덮는 반지름 %.3f · 작은 무리(10 점)에서 %d 점" % (rr, in_cluster4(idx)), 12, fill=INK)
b += txt(20, 446, "덮는 반지름 = 식 (5) 의 max_m min_n ||m − n|| (모든 점이 가장 가까운 뽑힌 점까지 가는 거리 중 최댓값). 탐욕 쪽이 %.1f 배 작다." % (RR / RG), 11, anchor="start", fill=INK2)
b += txt(20, 462, "이 그림은 내가 만든 장난감 자료(무리 넷, 330 · 200 · 60 · 10 점, 씨앗 7)다. 논문 그림 3 의 자료와 같은 것이 아니다.", 10, anchor="start", fill=MUTED)
svg("fig05_coreset_toy", W, H, b, "탐욕 코어셋과 무작위 뽑기의 덮는 범위")


# ── 그림 6. 식 (7) 의 재가중 ────────────────────────────────────────────────
W, H = 840, 440
b = defs()
b += txt(20, 30, "식 (7) 의 재가중 w — 늘 [1 − 1/b, 1) 안에서 움직인다 (내가 유도한 것)", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 70, 470, 360, 60
def X(dl):
    return PX0 + dl / 5.0 * (PX1 - PX0)
def Y(v):
    return PY0 - (v - 0.4) / 0.6 * (PY0 - PY1)
b = axis_y(b, PX0, PX1, Y, (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0), "%.1f")
for dl in range(6):
    b += txt(X(dl), PY0 + 18, str(dl), 10, fill=MUTED)
b += txt((PX0 + PX1) / 2, PY0 + 38, "Δ = (m* 의 다른 이웃까지 시험 조각의 거리) − d*   (특징 공간의 L2 거리 그대로)", 11, fill=INK2)
cols = {2: S_PREV, 3: S_PC, 5: S_THIRD, 9: S_GRAY}
for bb in (2, 3, 5, 9):
    pts = [(X(i / 20.0), Y(w_of(bb, i / 20.0))) for i in range(101)]
    b += polyline(pts, cols[bb], 2.2)
    b += txt(X(0) + 6, Y(1 - 1.0 / bb) + (14 if bb == 2 else -6), "b = %d (최소 %.3f)" % (bb, 1 - 1.0 / bb), 10, anchor="start", fill=cols[bb], weight="bold")
b += box(500, 60, 320, 300, fill=NODE, stroke=LINE)
lines_ = [("식 (7):  s = (1 − e^{d*} / Σ_{m∈N_b(m*)} e^{d_m}) · s*", INK),
          ("d_m = ||m_test,* − m||,  d* = 가장 가까운 거리", INK2),
          ("", INK),
          ("m* 가 시험 조각에 가장 가까우므로 모든 d_m ≥ d*.", INK),
          ("그래서 분수는 1/b 이하이고 w ≥ 1 − 1/b.", INK),
          ("", INK),
          ("뜻: 재가중은 s* 를 많아야 b/(b−1) 배까지만", INK),
          ("갈라 놓는다. b = 3 이면 1.5 배.", INK2),
          ("", INK),
          ("지수가 거리 그 자체라 축척을 탄다.", NO),
          ("거리 차이 Δ 가 3 이면 b = 3 에서 w = 0.976.", NO),
          ("논문은 b 의 값을 적지 않았다.", NO)]
for k, (t, col) in enumerate(lines_):
    b += txt(512, 84 + 21 * k, t, 11, anchor="start", fill=col)
b += txt(20, 428, "곡선은 'm* 가 N_b(m*) 안에 들고 나머지 b−1 개가 모두 d* + Δ 에 있는' 경우다. 이웃이 제각각이면 곡선 사이 어딘가에 놓인다.", 10, anchor="start", fill=MUTED)
svg("fig06_reweight", W, H, b, "식 7 재가중의 범위")


# ── 그림 7. MVTec 이미지 수준 — 표 1 ─────────────────────────────────────────
W, H = 840, 430
b = defs()
b += txt(20, 30, "MVTec AD 이미지 수준 — 오차(100 − AUROC) 로 보면 (표 1)", 15, anchor="start", weight="bold")
EX0, EX1 = 190, 640
def EX(v):
    return EX0 + v / 15.0 * (EX1 - EX0)
for v in (0, 2.5, 5, 7.5, 10, 12.5, 15):
    b += line(EX(v), 50, EX(v), 355, LINE, 1)
    b += txt(EX(v), 372, "%g" % v, 10, fill=MUTED)
for i, (nm, au) in enumerate(T1):
    y = 58 + 33 * i
    pc = nm.startswith("PatchCore")
    b += txt(180, y + 14, nm, 12, anchor="end", weight="bold" if pc else None, fill=S_PC if pc else INK)
    b += rect(EX0, y, EX(100 - au) - EX0, 20, S_PC if pc else (S_GRAY if nm == "PaDiM*" else S_PREV))
    extra = ("  오분류 %d / 1,725" % T1_MIS[nm]) if nm in T1_MIS else ""
    b += txt(EX(100 - au) + 6, y + 15, "%.1f%s" % (100 - au, extra), 11, anchor="start")
b += txt((EX0 + EX1) / 2, 392, "부류 평균 이미지 AUROC 의 오차, %", 11, fill=INK2)
b += box(655, 60, 170, 230, fill=NODE, stroke=LINE)
for k, t in enumerate(["회색 PaDiM* 는", "부류에 맞춰 백본을", "고른 값이고, 부록 표 S1", "캡션이 '다시 내지", "못했다' 고 적는다.", "",
                       "'오차 57% 감소' 는", "2.1 → 0.9 로 이 값과의", "비교다. 다시 낸 PaDiM", "(표 5, 95.4) 과 비교하면", "4.6 → 0.9."]):
    b += txt(665, 82 + 19 * k, t, 11, anchor="start", fill=INK2)
b += txt(20, 418, "오분류 수는 F1 이 가장 큰 문턱에서 센 거짓 양성 + 거짓 음성. 그 문턱을 무엇으로 정했는지(시험 라벨인지)는 적혀 있지 않다.", 10, anchor="start", fill=MUTED)
svg("fig07_table1", W, H, b, "MVTec AD 이미지 수준 오차")


# ── 그림 8. 부류별 — 표 S1 · S2 · S3 ─────────────────────────────────────────
W, H = 840, 500
b = defs()
b += txt(20, 30, "부류별 PatchCore-25% (표 S1 · S2 · S3) — 이미지 AUROC 만점이 여섯 부류", 15, anchor="start", weight="bold")
cols3 = [("이미지 AUROC", S1["PatchCore-25"][1], 95, 100, S_PC),
         ("픽셀 AUROC", S2["PatchCore-25"][1], 94, 100, S_PREV),
         ("PRO", S3["PatchCore-25"][1], 80, 100, S_THIRD)]
for k, (nm, vals, lo, hi, col) in enumerate(cols3):
    x0, x1 = 150 + 225 * k, 350 + 225 * k
    def VX(v, x0=x0, x1=x1, lo=lo, hi=hi):
        return x0 + (v - lo) / float(hi - lo) * (x1 - x0)
    b += txt((x0 + x1) / 2, 56, nm + " (축 %d ~ %d)" % (lo, hi), 12, weight="bold", fill=col)
    for t in range(lo, hi + 1, (1 if hi - lo <= 6 else 5)):
        b += line(VX(t), 66, VX(t), 438, LINE, 1)
        b += txt(VX(t), 452, str(t), 9, fill=MUTED)
    for i, v in enumerate(vals):
        y = 72 + 24.5 * i
        b += line(x0, y + 8, VX(v), y + 8, col, 2)
        b += dot(VX(v), y + 8, col if v < 100 else INK, 4)
        if v < hi - 0.6:
            b += txt(VX(v) + 7, y + 12, "%g" % v, 9, anchor="start", fill=INK2)
        else:
            b += txt(VX(v) - 7, y + 3, "%g" % v, 9, anchor="end", fill=INK2)
for i, c in enumerate(CLASSES):
    b += txt(140, 84 + 24.5 * i, c, 11, anchor="end")
b += txt(20, 476, "가장 낮은 칸: 이미지 Pill 96.6 · 픽셀 Wood 95.0 · PRO Transistor 83.7. 본문은 '1/3 이 완벽' 이라 적고 부록은 '15 중 6' 이라 적는다(6/15 = 40%).", 11, anchor="start", fill=INK2)
b += txt(20, 494, "검은 점 = 100. 표의 100 은 소수 첫째 자리 반올림이라 99.95 이상을 뜻한다.", 10, anchor="start", fill=MUTED)
svg("fig08_per_class", W, H, b, "부류별 PatchCore-25 성적")


# ── 그림 9. 추론 시간 — 표 5 ────────────────────────────────────────────────
W, H = 840, 420
b = defs()
b += txt(20, 30, "추론 시간 (표 5) — 뱅크를 100 배 줄여도 시간은 3.5 배만 준다", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 80, 470, 350, 60
def X(f):
    return PX0 + f * (PX1 - PX0)
def Y(t):
    return PY0 - t / 0.7 * (PY0 - PY1)
b = axis_y(b, PX0, PX1, Y, (0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7), "%.1f")
for f in (0, 0.25, 0.5, 0.75, 1.0):
    b += txt(X(f), PY0 + 18, "%d%%" % (f * 100), 10, fill=MUTED)
b += txt((PX0 + PX1) / 2, PY0 + 38, "남긴 뱅크 비율", 11, fill=INK2)
b += txt(PX0 - 46, 50, "초 / 이미지", 10, fill=INK2, anchor="start")
b += line(X(0), Y(TA), X(1), Y(TA + TB), S_PC, 1.6, dash="6,4")
b += line(X(0), Y(TA), X(1), Y(TA), MUTED, 1, dash="2,3")
b += txt(X(0.55), Y(TA) + 16, "고정 몫 a = %.3f 초 (내 셈)" % TA, 10, fill=MUTED)
for nm, f, sc, t in T5:
    if f is not None:
        b += dot(X(f), Y(t), S_PC, 5)
        b += txt(X(f) + 8, Y(t) - 8, "%s %.2f" % (nm.replace("PatchCore-", ""), t), 10, anchor="start", fill=S_PC)
for nm, t, col, dy in (("SPADE 0.66", 0.66, S_PREV, 4), ("PaDiM 0.19", 0.19, S_PREV, 14), ("100% + IVFPQ 0.20", 0.20, S_GRAY, -4)):
    b += line(PX1 + 6, Y(t), PX1 + 22, Y(t), col, 3)
    b += txt(PX1 + 26, Y(t) + dy, nm, 10, anchor="start", fill=col)
b += box(600, 60, 225, 290, fill=NODE, stroke=LINE)
lines_ = ["세 점에 시간 = a + b x 비율", "을 맞추면 a = %.3f, b = %.3f." % (TA, TB), "",
          "1% 의 0.17 초가 고정 몫과", "같은 값이다. 백본 앞 계산 ·", "늘리기 · 흐림 같은 몫이", "줄지 않는 것으로 읽힌다", "(논문은 나누어 적지 않았다).", "", "장치는 부록 A 의 'Tesla V4'", "뿐 — 그런 이름의 GPU 가", "따로 있는지 나는 확인하지", "못했다. 배치 크기 · 시간", "재는 범위도 적혀 있지 않다."]
for k, t in enumerate(lines_):
    b += txt(610, 82 + 19 * k, t, 11, anchor="start", fill=INK2)
b += txt(20, 410, "점수 칸: 100% (99.1, 98.0, 93.3) · 10% (99.0, 98.1, 93.5) · 1% (99.0, 98.0, 93.1) · IVFPQ (98.0, 97.9, 93.0) — 근사 탐색은 이미지 AUROC 를 1.1 점 잃는다.", 10, anchor="start", fill=MUTED)
svg("fig09_inference_time", W, H, b, "뱅크 비율과 추론 시간")


# ── 그림 10. 이웃 크기 — 그림 4 위 · S5 위 ───────────────────────────────────
W, H = 840, 400
b = defs()
b += txt(20, 30, "이웃 크기 p (그림 4 위 · S5 위, 눈금 읽음) — 코어셋 있음 곡선은 세 지표 모두 p = 3 에서 가장 높다", 15, anchor="start", weight="bold")
panels = [("이미지 AUROC", F4_DET_CORE, F4_DET_FULL, 94, 99.5, 1.0), ("픽셀 AUROC", F4_SEG_CORE, F4_SEG_FULL, 95.5, 98.5, 0.5),
          ("PRO", F4_PRO_CORE, F4_PRO_FULL, 84, 94, 2.0)]
for k, (nm, core, full, lo, hi, step) in enumerate(panels):
    x0, x1, y0, y1 = 60 + 270 * k, 270 + 270 * k, 320, 70
    def X(p, x0=x0, x1=x1):
        return x0 + (p - 1) / 6.0 * (x1 - x0)
    def Y(v, lo=lo, hi=hi, y0=y0, y1=y1):
        return y0 - (v - lo) / (hi - lo) * (y0 - y1)
    t = lo
    while t <= hi + 1e-9:
        b += line(x0, Y(t), x1, Y(t), LINE, 1)
        b += txt(x0 - 5, Y(t) + 4, "%g" % t, 9, anchor="end", fill=MUTED)
        t += step
    for p in P_NB:
        b += txt(X(p), y0 + 16, str(p), 10, fill=MUTED if p % 2 else NO)
    b += txt((x0 + x1) / 2, 56, nm, 12, weight="bold")
    b += polyline([(X(p), Y(v)) for p, v in zip(P_NB, core)], S_PC, 2)
    for p, v in zip(P_NB, core):
        b += dot(X(p), Y(v), S_PC, 3.5)
    fp = [(p, v) for p, v in zip(P_NB, full) if v is not None]
    for p, v in fp:
        b += circ(X(p), Y(v), 4.5, "none", S_PREV, 1.8)
b += dot(70, 362, S_PC, 4)
b += txt(80, 366, "코어셋 있음 (비율 적혀 있지 않음)", 11, anchor="start", fill=S_PC)
b += circ(330, 362, 4.5, "none", S_PREV, 1.8)
b += txt(342, 366, "코어셋 없음 — 주황에 가려 중심을 못 찾은 칸은 비웠다", 11, anchor="start", fill=S_PREV)
b += txt(20, 390, "빨간 숫자 2 · 4 · 6 은 식 (1) 이 전제하는 홀수가 아닌 값. 코어셋 없음의 이미지 AUROC 는 p=2 98.48 · p=3 99.11 로 0.63 차이, 코어셋 있음은 98.80 · 98.89 로 0.09 차이.", 10, anchor="start", fill=MUTED)
svg("fig10_neighbourhood", W, H, b, "이웃 크기에 따른 성능")


# ── 그림 11. 단계 조합 — 그림 4 아래 · S5 아래 ───────────────────────────────
W, H = 840, 400
b = defs()
b += txt(20, 30, "어느 단계를 쓸까 (그림 4 아래 · S5 아래, 눈금 읽음) — 픽셀은 2+3 과 1+2+3 이 같고, PRO 는 1+2+3 이 높다", 14, anchor="start", weight="bold")
panels = [("이미지 AUROC", F4_HIER_DET, 92, 100, 2), ("픽셀 AUROC", F4_HIER_SEG, 96, 98.5, 0.5), ("PRO", F4_HIER_PRO, 86, 95, 2)]
for k, (nm, vals, lo, hi, step) in enumerate(panels):
    x0, x1, y0, y1 = 60 + 270 * k, 270 + 270 * k, 320, 70
    def Y(v, lo=lo, hi=hi, y0=y0, y1=y1):
        return y0 - (v - lo) / (hi - lo) * (y0 - y1)
    t = lo
    while t <= hi + 1e-9:
        b += line(x0, Y(t), x1, Y(t), LINE, 1)
        b += txt(x0 - 5, Y(t) + 4, "%g" % t, 9, anchor="end", fill=MUTED)
        t += step
    b += txt((x0 + x1) / 2, 56, nm, 12, weight="bold")
    bw = (x1 - x0) / 6.0
    best = max(vals)
    for i, (h, v) in enumerate(zip(HIER, vals)):
        col = S_PC if h == "2+3" else S_GRAY
        b += rect(x0 + bw * i + 4, Y(v), bw - 8, y0 - Y(v), col)
        b += txt(x0 + bw * i + bw / 2, Y(v) - 4, "%.1f" % v, 9, fill=INK if v == best else INK2, weight="bold" if v == best else None)
        b += txt(x0 + bw * i + bw / 2, y0 + 16, h, 9, fill=MUTED)
b += txt(20, 362, "이미지 AUROC 는 2 만 쓴 것과 2+3 이 같은 값(98.98)으로 읽힌다 — 2+3 을 고른 이득은 픽셀 AUROC 의 +0.6 점(97.49 → 98.09)에 있다.", 11, anchor="start", fill=INK2)
b += txt(20, 382, "막대 윗변을 픽셀로 읽었고 1 px 이 0.025 · 0.009 · 0.026 점이다. 백본은 WRN-50 하나, 반복 수 · 흩어짐은 적혀 있지 않다.", 10, anchor="start", fill=MUTED)
svg("fig11_hierarchies", W, H, b, "특징 단계 조합에 따른 성능")


# ── 그림 12. 뽑기 방법 — 그림 5 · S6 ────────────────────────────────────────
W, H = 840, 420
b = defs()
b += txt(20, 30, "뱅크를 줄이는 세 방법 (그림 5 · S6, 눈금 읽음) — 코어셋은 1% 까지 이미지 AUROC 99.0 을 지킨다", 14, anchor="start", weight="bold")
panels = [("이미지 AUROC", F5_DET, 85, 100, 2.5), ("픽셀 AUROC", F5_SEG, 95, 98.5, 0.5), ("PRO", F5_PRO, 85, 94, 1.5)]
scol = {"코어셋": S_PC, "무작위": S_THIRD, "학습한 대리점": S_GRAY}
for k, (nm, data, lo, hi, step) in enumerate(panels):
    x0, x1, y0, y1 = 60 + 270 * k, 270 + 270 * k, 320, 70
    def X(pct, x0=x0, x1=x1):
        return x0 + (2 - math.log10(pct)) / 3.0 * (x1 - x0)
    def Y(v, lo=lo, hi=hi, y0=y0, y1=y1):
        return y0 - (min(max(v, lo), hi) - lo) / (hi - lo) * (y0 - y1)
    t = lo
    while t <= hi + 1e-9:
        b += line(x0, Y(t), x1, Y(t), LINE, 1)
        b += txt(x0 - 5, Y(t) + 4, "%g" % t, 9, anchor="end", fill=MUTED)
        t += step
    for pct in (100, 10, 1, 0.1):
        b += txt(X(pct), y0 + 16, "%g%%" % pct, 9, fill=MUTED)
    b += txt((x0 + x1) / 2, 56, nm, 12, weight="bold")
    for s, vals in data.items():
        pts = [(X(p), Y(v)) for p, v in zip(SUB_X, vals) if v is not None]
        b += polyline(pts, scol[s], 2)
        for x, y in pts:
            b += dot(x, y, scol[s], 3.2)
for j, (s, col) in enumerate(scol.items()):
    b += dot(70 + 200 * j, 362, col, 4)
    b += txt(80 + 200 * j, 366, s, 11, anchor="start", fill=col)
b += txt(20, 390, "가로축은 남긴 비율(로그). 50% 칸의 코어셋 표식은 무작위 표식에 가려 비웠다. 축 아래로 나간 점(이미지 85 · 픽셀 95 · PRO 85 미만)은 그리지 않았다.", 10, anchor="start", fill=MUTED)
b += txt(20, 406, "보폭으로 줄이면: s = 2 에서 이미지 AUROC 97.6, s = 3 에서 96.8 (4.4.2 절 끝, 뱅크는 각각 1/4 · 1/9 로 줄어든다 — 내 셈).", 10, anchor="start", fill=MUTED)
svg("fig12_subsampling", W, H, b, "뱅크를 줄이는 방법별 성능")


# ── 그림 13. 적은 표본 — 표 S5 ──────────────────────────────────────────────
W, H = 840, 420
b = defs()
b += txt(20, 30, "적은 표본 (표 S5) — 부류당 정상 이미지 1 ~ 50 장, 같은 WRN-50 백본", 15, anchor="start", weight="bold")
PX0, PX1, PY0, PY1 = 70, 500, 350, 60
def X(s):
    return PX0 + math.log(s) / math.log(50) * (PX1 - PX0)
def Y(v):
    return PY0 - (v - 70) / 30.0 * (PY0 - PY1)
b = axis_y(b, PX0, PX1, Y, (70, 75, 80, 85, 90, 95, 100), "%g")
for s, r in zip(SHOTS, RETAINED):
    b += txt(X(s), PY0 + 18, str(s), 10, fill=MUTED)
    b += txt(X(s), PY0 + 32, "%g%%" % r, 8, fill=MUTED)
b += txt((PX0 + PX1) / 2, PY0 + 50, "부류당 학습 이미지 수 (아래 줄: 표의 '남긴 %')", 11, fill=INK2)
mcol = {"SPADE": S_GRAY, "PaDiM": S_PREV, "PatchCore-10": S_PC, "PatchCore-25": "#9C3D12"}
for m, vals in S5_IMG.items():
    b += polyline([(X(s), Y(v)) for s, (v, e) in zip(SHOTS, vals)], mcol[m], 2)
    for s, (v, e) in zip(SHOTS, vals):
        b += line(X(s), Y(v - e), X(s), Y(v + e), mcol[m], 1.4)
        b += dot(X(s), Y(v), mcol[m], 3)
b += circ(X(16), Y(87.3), 5, "none", S_THIRD, 2)
b += txt(X(16) + 8, Y(87.3) + 14, "DifferNet 16 장 87.3", 10, anchor="start", fill=S_THIRD)
for m, col in mcol.items():
    v = S5_IMG[m][-1][0]
    b += txt(PX1 + 8, Y(v) + (4 if m != "PatchCore-25" else -6), m, 10, anchor="start", fill=col, weight="bold")
b += box(620, 60, 205, 290, fill=NODE, stroke=LINE)
lines_ = ["이미지 AUROC, ± 는 표 그대로", "(몇 번 돌렸는지 적혀 있지 않다)", "", "PatchCore-10 의 50 장 97.5 는", "전체 학습의 PaDiM 95.3 보다", "높고 PaDiM* 97.9 보다 낮다.", "",
          "1 장에서 PatchCore-10 83.4", "> SPADE 50 장 81.1.", "", "'남긴 %' 는 15 부류 평균", "241.9 장에 대한 비율이다", "(내가 다시 냄). 칫솔은 학습이", "60 장이라 50 장이 83%."]
for k, t in enumerate(lines_):
    b += txt(630, 82 + 19 * k, t, 11, anchor="start", fill=INK2)
svg("fig13_low_shot", W, H, b, "적은 표본에서의 이미지 AUROC")


# ── 그림 14. 백본 — 표 S6 ───────────────────────────────────────────────────
W, H = 840, 400
b = defs()
b += txt(20, 30, "백본을 바꾸면 (표 S6) — 다섯 백본의 이미지 AUROC 가 98.6 ~ 99.1 안", 15, anchor="start", weight="bold")
metrics = [("이미지 AUROC", 2, 98.4, 99.2), ("픽셀 AUROC", 3, 97.6, 98.3), ("PRO", 4, 92.0, 93.6)]
bbs = ["ResNet50", "WideResNet50", "ResNet101", "WideResNet101", "ResNeXt101"]
for k, (nm, ci, lo, hi) in enumerate(metrics):
    x0, x1 = 170 + 225 * k, 365 + 225 * k
    def VX(v, x0=x0, x1=x1, lo=lo, hi=hi):
        return x0 + (v - lo) / (hi - lo) * (x1 - x0)
    b += txt((x0 + x1) / 2, 58, nm, 12, weight="bold")
    t = lo
    while t <= hi + 1e-9:
        b += line(VX(t), 68, VX(t), 330, LINE, 1)
        b += txt(VX(t), 346, "%.1f" % t, 9, fill=MUTED)
        t += 0.2
    for i, bbn in enumerate(bbs):
        y = 90 + 52 * i
        r10 = [r for r in S6 if r[0] == bbn and r[1] == 10][0]
        r1 = [r for r in S6 if r[0] == bbn and r[1] == 1][0]
        b += line(VX(r10[ci]), y, VX(r1[ci]), y + 16, LINE, 1)
        b += dot(VX(r10[ci]), y, S_PC, 4.5)
        b += circ(VX(r1[ci]), y + 16, 4.5, "none", S_PC, 1.8)
        b += txt(VX(r10[ci]) + 8, y + 4, "%.1f" % r10[ci], 9, anchor="start", fill=INK2)
        b += txt(VX(r1[ci]) + 8, y + 20, "%.1f" % r1[ci], 9, anchor="start", fill=INK2)
for i, bbn in enumerate(bbs):
    b += txt(160, 98 + 52 * i, bbn, 11, anchor="end", weight="bold" if bbn == "WideResNet50" else None, fill=S_PC if bbn == "WideResNet50" else INK)
b += dot(30, 368, S_PC, 4)
b += txt(40, 372, "뱅크 10%", 11, anchor="start")
b += circ(120, 368, 4.5, "none", S_PC, 1.8)
b += txt(130, 372, "뱅크 1%", 11, anchor="start")
b += txt(210, 372, "WideResNet50 − ResNet50: 10% 에서 −0.1 · 0.0 · +0.2, 1% 에서 +0.3 · +0.2 · −0.2 (이미지 · 픽셀 · PRO). 부호가 갈린다.", 10, anchor="start", fill=INK2)
b += txt(20, 392, "WideResNet50 10% 의 이미지 AUROC 가 이 표는 98.9, 표 1 은 99.0. 반복 수 · 흩어짐 · 단계 선택은 이 표에 적혀 있지 않다.", 10, anchor="start", fill=MUTED)
svg("fig14_backbones", W, H, b, "백본별 성능")


# ── 그림 15. 이미지 크기 · 이웃 — 그림 S4 ────────────────────────────────────
W, H = 840, 420
b = defs()
b += txt(20, 26, "이미지 크기 S 와 이웃 p (그림 S4, 눈금 읽음) — p = 3 에서는 키워도 픽셀 AUROC 가 기준 아래", 14, anchor="start", weight="bold")
metrics = [("이미지 AUROC", 1, 96.0, 99.6, 0.5, S4_BASE[0]), ("픽셀 AUROC", 2, 97.5, 98.5, 0.25, S4_BASE[1]),
           ("PRO", 3, 91.0, 95.5, 1.0, S4_BASE[2])]
for k, (nm, ci, lo, hi, step, base) in enumerate(metrics):
    x0, x1 = 120 + 240 * k, 330 + 240 * k
    def VX(v, x0=x0, x1=x1, lo=lo, hi=hi):
        return x0 + (v - lo) / (hi - lo) * (x1 - x0)
    b += txt((x0 + x1) / 2, 50, nm, 12, weight="bold")
    t = lo
    while t <= hi + 1e-9:
        b += line(VX(t), 68, VX(t), 345, LINE, 1)
        b += txt(VX(t), 360, "%g" % t, 9, fill=MUTED)
        t += step
    for i, row in enumerate(S4_ROWS):
        y = 74 + 34 * i
        v = row[ci]
        b += rect(x0, y, VX(v) - x0, 22, S_PC if v > base else S_GRAY)
        b += txt(VX(v) + 4, y + 15, "%.2f" % v, 9, anchor="start", fill=INK2)
    b += line(VX(base), 68, VX(base), 345, INK, 1.6, dash="5,4")
    b += txt(VX(base), 65, "기준 %.2f" % base, 9, fill=INK, anchor="start")
for i, row in enumerate(S4_ROWS):
    b += txt(110, 89 + 34 * i, row[0], 11, anchor="end")
b += txt(20, 386, "주황 = 점선(224, p = 3 기준)보다 높음. p = 3 의 288 · 360 · 448 은 픽셀 AUROC 가 97.96 · 97.86 · 97.84 로 기준 98.12 보다 낮다 —", 10, anchor="start", fill=INK2)
b += txt(20, 402, "부록 C.3 의 '분할은 꾸준히 오른다' 는 p 를 5 · 7 로 함께 키운 행에서만 보인다. 픽셀 AUROC 축은 원 그림대로 97.5 에서 시작한다.", 10, anchor="start", fill=INK2)
svg("fig15_resolution", W, H, b, "이미지 크기와 이웃 크기")


# ── 그림 16. 계보 ────────────────────────────────────────────────────────
W, H = 840, 400
b = defs()
b += txt(20, 30, "계보 — 사전학습 특징 + 정상 모음 + 최근접 거리", 15, anchor="start", weight="bold")
nodes = [(30, 70, "ResNet (2015) · WRN (2016)", "얼려 쓰는 특징 추출기 (WRN-50-2)", INK2),
         (30, 150, "DN2 (Bergman 외, 2020)", "이미지 전체 특징의 kNN — 마지막 단계", S_PREV),
         (30, 230, "SPADE (Cohen & Hoshen, 2020)", "여러 단계 뱅크, 이미지 kNN 으로 먼저 고름", S_PREV),
         (30, 310, "PaDiM (Defard 외, 2020)", "위치마다 가우스 하나, 마할라노비스", S_PREV),
         (440, 150, "코어셋 (Agarwal 외 2004 ·", "Sener & Savarese 2018 · Sinha 외 2020)", CODE),
         (440, 270, "PatchCore (2021-06 arXiv, 2022 CVPR)", "조각 뱅크 하나 + 탐욕 코어셋 + 재가중", S_PC)]
for x, y, t, s, col in nodes:
    b += box(x, y - 26, 360, 52, fill=NODE, stroke=col, sw=1.6)
    b += txt(x + 180, y - 5, t, 12, weight="bold", fill=col)
    b += txt(x + 180, y + 15, s, 11, fill=INK2)
for y in (70, 150, 230, 310):
    b += path("M390,%d C415,%d 415,270 438,270" % (y, y), INK2, sw=1.2, marker="ai")
b += line(620, 176, 620, 242, CODE, 1.4, marker="ac")
b += txt(20, 372, "왼쪽 넷과 코어셋 셋은 이 논문의 참고 문헌 [4] [10] [14] [23] [57] [1] [48] [49]. 탐욕 max-min 뽑기의 원 출처(Gonzalez 1985)는", 10, anchor="start", fill=MUTED)
b += txt(20, 388, "이 논문의 참고 문헌에 없다 — 노트 참고 문헌 절에 따로 적었다. 이 저장소의 노트로는 ResNet · Wide ResNet 이 앞자리다.", 10, anchor="start", fill=MUTED)
svg("fig16_lineage", W, H, b, "PatchCore 의 계보")

print("\n끝.")
