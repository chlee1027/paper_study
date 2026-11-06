# -*- coding: utf-8 -*-
r"""UniAD 노트(You 외, NeurIPS 2022)의 그림 열넷을 만든다.

색과 글꼴은 저장소의 앞선 노트 그림과 맞췄다. 바깥 데이터를 읽지 않으므로 어디서나 돌아간다.

  python make_figures.py

원문 표의 수는 T1 · T2 · T3 · T4 · T5A ~ T5F · S2 · S3 · S4 · S6 · S7 상수에 옮겨 적었고,
돌릴 때 평균 · 차이 · 칸 세기를 다시 내어 화면에 찍는다. 노트의 「내가 센 것」 은 이 출력이다.

원문 그림 2a · 4 의 값은 PDF 안의 래스터(734x556, 870x675 등)를 색으로 읽어 CURVES 상수에 옮겼다.
그림 2a 는 1 픽셀이 AUROC 0.00068, 그림 4 는 0.00055 다. 평가가 10 에폭마다라 곡선의 꺾임은 그 간격 안의 값이다.
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


# ── 공통 도구 ────────────────────────────────────────────────────────────────
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
CLASSES = ["Bottle", "Cable", "Capsule", "Hazelnut", "Metal Nut", "Pill", "Screw", "Toothbrush", "Transistor",
           "Zipper", "Carpet", "Grid", "Leather", "Tile", "Wood"]

# 표 1: 방법 -> (통합, 부류별) 15 칸. Ours 통합의 ± 는 T1_PM
T1 = {
    "US": ([84.0, 60.0, 57.6, 95.8, 62.7, 56.1, 66.9, 57.8, 61.0, 78.6, 86.6, 69.2, 97.2, 93.7, 90.6],
           [99.0, 86.2, 86.1, 93.1, 82.0, 87.9, 54.9, 95.3, 81.8, 91.9, 91.6, 81.0, 88.2, 99.1, 97.7]),
    "PSVDD": ([85.5, 64.4, 61.3, 83.9, 80.9, 89.4, 80.9, 99.4, 77.5, 77.8, 63.3, 66.0, 60.8, 88.3, 72.1],
              [98.6, 90.3, 76.7, 92.0, 94.0, 86.1, 81.3, 100, 91.5, 97.9, 92.9, 94.6, 90.9, 97.8, 96.5]),
    "PaDiM": ([97.9, 70.9, 73.4, 85.5, 88.0, 68.8, 56.9, 95.3, 86.6, 79.7, 93.8, 73.9, 99.9, 93.3, 98.4],
              [99.9, 92.7, 91.3, 92.0, 98.7, 93.3, 85.8, 96.1, 97.4, 90.3, 99.8, 96.7, 100, 98.1, 99.2]),
    "CutPaste": ([67.9, 69.2, 63.0, 80.9, 60.0, 71.4, 85.2, 63.9, 57.9, 93.5, 93.6, 93.2, 93.4, 88.6, 80.4],
                 [98.2, 81.2, 98.2, 98.3, 99.9, 94.9, 88.7, 99.4, 96.1, 99.9, 93.9, 100, 100, 94.6, 99.1]),
    "MKD": ([98.7, 78.2, 68.3, 97.1, 64.9, 79.7, 75.6, 75.3, 73.4, 87.4, 69.8, 83.8, 93.6, 89.5, 93.4],
            [99.4, 89.2, 80.5, 98.4, 73.6, 82.7, 83.3, 92.2, 85.6, 93.2, 79.3, 78.0, 95.1, 91.6, 94.3]),
    "DRAEM": ([97.5, 57.8, 65.3, 93.7, 72.8, 82.2, 92.0, 90.6, 74.8, 98.8, 98.0, 99.3, 98.7, 99.8, 99.8],
              [99.2, 91.8, 98.5, 100, 98.7, 98.9, 93.9, 100, 93.1, 100, 97.0, 99.9, 100, 99.6, 99.1]),
    "Ours": ([99.7, 95.2, 86.9, 99.8, 99.2, 93.7, 87.5, 94.2, 99.8, 95.8, 99.8, 98.2, 100, 99.3, 98.6],
             [100, 97.6, 85.3, 99.9, 99.0, 88.3, 91.9, 95.0, 100, 96.7, 99.9, 98.5, 100, 99.0, 97.9]),
}
T1_MEAN = {"US": (74.5, 87.7), "PSVDD": (76.8, 92.1), "PaDiM": (84.2, 95.5), "CutPaste": (77.5, 96.1),
           "MKD": (81.9, 87.8), "DRAEM": (88.1, 98.0), "Ours": (96.5, 96.6)}
T1_PM = [0.04, 0.84, 0.73, 0.10, 0.09, 0.65, 0.57, 0.20, 0.09, 0.51, 0.02, 0.26, 0.00, 0.14, 0.08]

# 표 2
T2 = {
    "US": ([67.9, 78.3, 85.5, 93.7, 76.6, 80.3, 90.8, 86.9, 68.3, 84.2, 88.7, 64.5, 95.4, 82.7, 83.3],
           [97.8, 91.9, 96.8, 98.2, 97.2, 96.5, 97.4, 97.9, 73.7, 95.6, 93.5, 89.9, 97.8, 92.5, 92.1]),
    "PSVDD": ([86.7, 62.2, 83.1, 97.4, 96.0, 96.5, 74.3, 98.0, 78.5, 95.1, 78.6, 70.8, 93.5, 92.1, 80.7],
              [98.1, 96.8, 95.8, 97.5, 98.0, 95.1, 95.7, 98.1, 97.0, 95.1, 92.6, 96.2, 97.4, 91.4, 90.8]),
    "PaDiM": ([96.1, 81.0, 96.9, 96.3, 84.8, 87.7, 94.1, 95.6, 92.3, 94.8, 97.6, 71.0, 84.8, 80.5, 89.1],
              [98.2, 96.7, 98.6, 98.1, 97.3, 95.7, 98.4, 98.8, 97.6, 98.4, 99.0, 97.1, 99.0, 94.1, 94.1]),
    "FCDD": ([56.0, 64.1, 67.6, 79.3, 57.5, 65.9, 67.2, 60.8, 54.2, 63.0, 68.6, 65.8, 66.3, 59.3, 53.3],
             [97, 90, 93, 95, 94, 81, 86, 94, 88, 92, 96, 91, 98, 91, 88]),
    "MKD": ([91.8, 89.3, 88.3, 91.2, 64.2, 69.7, 92.1, 88.9, 71.7, 86.1, 95.5, 82.3, 96.7, 85.3, 80.5],
            [96.3, 82.4, 95.9, 94.6, 86.4, 89.6, 96.0, 96.1, 76.5, 93.9, 95.6, 91.8, 98.1, 82.8, 84.8]),
    "DRAEM": ([87.6, 71.3, 50.5, 96.9, 62.2, 94.4, 95.5, 97.7, 64.5, 98.3, 98.6, 98.7, 97.3, 98.0, 96.0],
              [99.1, 94.7, 94.3, 99.7, 99.5, 97.6, 97.6, 98.1, 90.9, 98.8, 95.5, 99.7, 98.6, 99.2, 96.4]),
    "Ours": ([98.1, 97.3, 98.5, 98.1, 94.8, 95.0, 98.3, 98.4, 97.9, 96.8, 98.5, 96.5, 98.8, 91.8, 93.2],
             [98.1, 96.8, 97.9, 98.8, 95.7, 95.1, 97.4, 97.8, 98.7, 96.0, 98.0, 94.6, 98.3, 91.8, 93.4]),
}
T2_MEAN = {"US": (81.8, 93.9), "PSVDD": (85.6, 95.7), "PaDiM": (89.5, 97.4), "FCDD": (63.3, 92),
           "MKD": (84.9, 90.7), "DRAEM": (87.2, 97.3), "Ours": (96.8, 96.6)}
T2_PM = [0.04, 0.10, 0.01, 0.10, 0.09, 0.16, 0.08, 0.03, 0.19, 0.24, 0.01, 0.04, 0.03, 0.10, 0.08]

# 표 3 (CIFAR-10): 조합 넷과 평균
T3 = {"US": [51.3, 51.3, 63.9, 56.8, 55.9], "FCDD": [55.0, 50.3, 59.2, 58.5, 55.8],
      "FCDD+OE": [71.8, 73.7, 85.3, 85.0, 78.9], "PANDA": [66.6, 73.2, 77.1, 72.9, 72.4],
      "MKD": [64.2, 69.3, 76.4, 78.7, 72.1], "Ours": [84.4, 80.9, 93.0, 90.6, 87.2]}

# 표 4: (검출 통합, 검출 부류별, 위치 통합, 위치 부류별)
T4 = [("InTra", 65.3, 95.0, 70.6, 96.6), ("VT-ADL", 55.4, 78.7, 64.4, 82.0), ("AnoVit", 69.6, 78, 68.4, 83),
      ("Ours (baseline)", 87.6, 94.7, 92.8, 95.8), ("Ours", 96.5, 96.6, 96.8, 96.6)]

# 표 S2 (표 5a 의 여섯 행을 포함): (질의, NMA, FJ, 검출, 위치)
S2 = [("없음", 0, 0, 69.5, 79.4), ("1", 0, 0, 87.6, 92.8), ("1", 1, 0, 96.1, 96.3), ("1", 0, 1, 95.0, 95.8),
      ("1", 1, 1, 96.2, 96.6), ("층별", 0, 0, 95.0, 96.5), ("층별", 1, 0, 95.8, 96.5), ("층별", 0, 1, 94.9, 96.2),
      ("층별", 1, 1, 96.5, 96.8)]

# 표 5b: (enc, dec, vanilla 검출, vanilla 위치, ours 검출, ours 위치)
T5B = [(4, 0, 69.8, 79.2, 94.9, 96.0), (0, 4, 80.5, 88.3, 96.1, 96.3), (2, 2, 84.7, 90.6, 95.1, 96.0),
       (4, 4, 87.6, 92.8, 96.5, 96.8), (6, 6, 86.1, 91.9, 96.5, 96.7)]
T5C = [("1x1", 94.6, 96.3), ("5x5", 96.4, 96.8), ("7x7", 96.5, 96.8), ("9x9", 96.3, 96.7)]
T5D = [("Enc", 95.8, 96.3), ("Enc+Dec1", 96.4, 96.8), ("Enc+Dec2", 96.5, 96.7), ("All", 96.5, 96.8)]
T5E = [("5", 96.1, 96.7), ("10", 96.4, 96.7), ("20", 96.5, 96.8), ("30", 95.7, 96.6)]
T5F = [("0.25", 95.6, 96.5), ("0.50", 95.8, 96.7), ("0.75", 96.3, 96.7), ("1", 96.5, 96.8)]
# 표 S3: 설계 -> (NMA · FJ 없이), (NMA · FJ 함께)
S3 = {"Vanilla": ((87.6, 92.8), None), "(a)": ((95.0, 96.5), (96.5, 96.8)), "(b)": ((94.4, 96.3), (96.3, 96.7)),
      "(c)": ((78.4, 87.0), None), "(d)": ((77.9, 87.0), None), "(e)": ((78.2, 89.9), None),
      "(f)": ((89.8, 94.0), (96.0, 96.6))}
S4 = [("MSE", 96.5, 96.8), ("Norm MSE", 96.4, 96.9), ("Cosine", 96.6, 96.8)]
S5 = [("학습", 65.9, 65.5), ("얼림", 96.5, 96.8)]
# 표 S6: (이름, 표의 파라미터 M, 검출, 위치, torchvision 으로 내가 센 전체 파라미터)
S6 = [("Res-18", 11.4, 92.4, 95.8, 11689512), ("Res-34", 21.5, 93.0, 96.2, 21797672),
      ("Res-50", 25.6, 92.4, 96.0, 25557032), ("Res-101", 44.5, 92.2, 95.9, 44549160),
      ("Eff-b0", 5.3, 96.1, 96.4, 5288548), ("Eff-b2", 9.2, 96.2, 97.0, 9109994),
      ("Eff-b4", 19, 96.5, 96.8, 19341616), ("Eff-b6", 43, 96.0, 96.7, 43040704)]
S7 = [("US", 60.32, 9.55), ("PSVDD", 149.74, 0.41), ("PaDiM", 23.25, 950.36), ("CutPaste", 3.65, 13.61),
      ("FCDD", 13.16, 4.51), ("MKD", 32.11, 0.34), ("DRAEM", 245.15, 69.05), ("Ours", 6.46, 7.48)]

# 그림 2a · 4 에서 읽은 값: 에폭 -> (픽셀, 이미지, 손실)
CURVES = {
    "uni": {0: (.753, .725, 22.887), 10: (.817, .748, 7.777), 20: (.841, .762, 2.906), 30: (.860, .761, 1.356),
            50: (.881, .772, .664), 67: (.890, .787, .443), 100: (.897, .815, .277), 120: (.899, .821, .221),
            150: (.898, .825, .166), 200: (.893, .819, .166), 300: (.880, .801, .138), 400: (.871, .788, .138),
            500: (.862, .777, .111), 600: (.854, .770, .111), 700: (.838, .751, .111), 800: (.842, .757, .111),
            900: (.831, .737, .111), 1000: (.828, .733, .111)},
    "sep": {0: (.754, .725, 29.307), 50: (.848, .778, 16.039), 100: (.885, .811, 10.803), 200: (.921, .862, 5.873),
            300: (.938, .892, 3.657), 400: (.947, .912, 2.548), 500: (.953, .925, 1.911), 600: (.958, .935, 1.496),
            700: (.960, .944, 1.247), 800: (.963, .952, 1.053), 900: (.963, .953, 1.025), 1000: (.963, .953, .997)},
}
# 그림 2a: 이름 -> (픽셀 최고, 에폭, 이미지 최고, 에폭, 픽셀 끝, 이미지 끝, 손실 끝)
FIG2A = [("MLP", .899, 122, .826, 151, .829, .733, .135), ("CNN", .948, 120, .911, 120, .897, .787, .135),
         ("Transformer", .937, 142, .914, 162, .906, .847, 1.185), ("Ours", .969, 794, .968, 960, .969, .967, 3.772)]
N_TRAIN = 3629    # MVTec AD 학습 이미지 수. 이 편에는 없고 MVTec AD 논문의 값이다
BATCH = 64


def mean(v):
    return sum(v) / float(len(v))


# ── 그림 ──────────────────────────────────────────────────────────────────
def fig01():
    W, H = 880, 330
    s = txt(W / 2, 28, "부류별 설정과 통합 설정 — 무엇이 같고 무엇이 달라지나", 14, weight="600")
    s += box(20, 48, 410, 216, NODE, INK2)
    s += txt(225, 70, "부류별 설정 (separate case)", 13, weight="600")
    for i, (a, b) in enumerate((("병 학습 이미지", "모델 1"), ("나사 학습 이미지", "모델 2"), ("... 15 부류", "모델 15"))):
        y = 84 + i * 54
        s += node(38, y, 130, 40, a, None, FWD_SOFT, FWD, 11)
        s += line(168, y + 20, 206, y + 20, INK2, 1.3, marker="ai")
        s += node(206, y, 90, 40, b, None, OK_SOFT, OK, 11)
        s += line(296, y + 20, 322, y + 20, INK2, 1.3, marker="ai")
        s += txt(372, y + 25, "그 부류만 판정", 10, INK2)
    s += box(450, 48, 410, 216, NODE, INK2)
    s += txt(655, 70, "통합 설정 (unified case)", 13, weight="600")
    for i, a in enumerate(("병 학습 이미지", "나사 학습 이미지", "... 15 부류")):
        y = 84 + i * 54
        s += node(468, y, 130, 40, a, None, FWD_SOFT, FWD, 11)
        s += line(598, y + 20, 640, 158, INK2, 1.3, marker="ai")
    s += node(640, 130, 90, 56, "모델 하나", "부류 라벨 없음", OK_SOFT, OK, 11)
    s += line(730, 158, 762, 158, INK2, 1.3, marker="ai")
    s += txt(812, 150, "15 부류 시험", 10, INK2)
    s += txt(812, 166, "미세조정 없음", 10, INK2)
    s += txt(W / 2, H - 46, "표 1 · 2 의 성적표는 두 설정 모두 부류마다 AUROC 를 내어 15 칸을 평균한다", 12, NO, weight="600")
    s += txt(W / 2, H - 24, "부류를 섞어 문턱 하나로 가르는 값은 이 편의 표에 없다(내가 표를 훑은 범위)", 11, INK2)
    svg("fig01_two_settings", W, H, s, "부류별 설정과 통합 설정")


def fig02():
    W, H = 880, 310
    s = txt(W / 2, 28, "이웃 가림 주의 — 14 x 14 토큰에서 가리는 몫 (내가 센 것)", 14, weight="600")
    sizes = [(1, 94.6, 96.3), (5, 96.4, 96.8), (7, 96.5, 96.8), (9, 96.3, 96.7)]
    cell = 11
    for k, (sz, det, loc) in enumerate(sizes):
        x0 = 38 + k * 212
        y0 = 54
        r = sz // 2
        for i in range(14):
            for j in range(14):
                m = abs(i - 6) <= r and abs(j - 6) <= r
                c = "#D7DDD9" if m else FWD_SOFT
                s += '<rect x="%.1f" y="%.1f" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="0.5"/>' % (
                    x0 + j * cell, y0 + i * cell, cell, cell, c, LINE)
        s += circ(x0 + 6.5 * cell, y0 + 6.5 * cell, 3, REV, REV)
        tot = 0
        for i in range(14):
            for j in range(14):
                tot += (min(13, i + r) - max(0, i - r) + 1) * (min(13, j + r) - max(0, j - r) + 1)
        share = 100.0 * sz * sz / 196
        s += txt(x0 + 77, y0 + 172, "%d x %d" % (sz, sz), 13, weight="600")
        s += txt(x0 + 77, y0 + 190, "가운데 토큰 %d / 196 = %.1f%%" % (sz * sz, share), 10, INK2)
        s += txt(x0 + 77, y0 + 205, "토큰 평균 %.1f%%, 이미지 변 %d 픽셀" % (100.0 * tot / 196 / 196, sz * 16), 10, INK2)
        s += txt(x0 + 77, y0 + 222, "표 5c 검출 %.1f · 위치 %.1f" % (det, loc), 11, FWD)
    s += txt(W / 2, H - 12, "토큰 하나의 간격을 16 픽셀로 셈(224 / 14). 파란 칸은 주의가 볼 수 있는 토큰, 회색은 가린 토큰", 11, INK2)
    svg("fig02_nma_share", W, H, s, "이웃 가림의 몫")


def fig03():
    W, H = 840, 320
    data = [(5, 96.1, 96.7), (10, 96.4, 96.7), (20, 96.5, 96.8), (30, 95.7, 96.6)]
    s = txt(W / 2, 28, "특징 흔들기 — 잡음 노름은 특징 노름의 몇 배인가 (식 3, 내가 계산)", 14, weight="600")
    x0, x1, y0, y1 = 80, 800, 56, 250
    fy = lambda v: y1 - (y1 - y0) * v / 2.0
    s += frame(x0, y0, x1, y1, [], [0, 0.5, 1, 1.5, 2], lambda t: t, fy, None, "E||D|| / ||f||")
    s += line(x0, fy(1), x1, fy(1), NO, 1.2, "5,4")
    s += txt(x0 + 6, fy(1) - 6, "잡음 노름 = 특징 노름", 10, NO, "start")
    for i, (a, det, loc) in enumerate(data):
        r = a / math.sqrt(256)
        x = 150 + i * 160
        s += bar(x, fy(r), 80, y1 - fy(r), FWD if a == 20 else FWD_SOFT)
        s += txt(x + 40, fy(r) - 6, "%.3f 배" % r, 12, FWD, weight="600")
        s += txt(x + 40, y1 + 18, "α = %d" % a, 12, weight="600")
        s += txt(x + 40, y1 + 36, "검출 %.1f · 위치 %.1f" % (det, loc), 10, INK2)
    s += txt(W / 2, H - 8, "σ = α ||f|| / C 이므로 C 차원 잡음의 노름 기댓값은 σ√C = α ||f|| / √C. C = 256 으로 셈(C = 272 면 1.213 배)", 11, INK2)
    svg("fig03_jitter_ratio", W, H, s, "특징 흔들기 잡음의 크기")


def fig04():
    W, H = 860, 350
    s = txt(W / 2, 28, "그림 2a 를 픽셀로 읽은 값 — 최고와 끝 (에폭 1000)", 14, weight="600")
    x0, x1, y0, y1 = 70, 820, 56, 268
    fy = lambda v: y1 - (y1 - y0) * (v - 0.70) / 0.30
    s += frame(x0, y0, x1, y1, [], [0.70, 0.80, 0.90, 1.00], lambda t: t, fy, None, "AUROC", yfmt=lambda t: "%.2f" % t)
    for i, (n, pp, pe, ip, ie, pz, iz, l) in enumerate(FIG2A):
        cx = 150 + i * 188
        for dx, peak, end, col, lab in ((-34, pp, pz, REV, "픽셀"), (34, ip, iz, OK, "이미지")):
            s += line(cx + dx, fy(peak), cx + dx, fy(end), col, 3)
            s += circ(cx + dx, fy(peak), 5, col, col)
            s += circ(cx + dx, fy(end), 5, BG, col, 2)
            s += txt(cx + dx + 10, fy(peak) - 6, "%.3f" % peak, 10, col, "start")
            s += txt(cx + dx + 10, fy(end) + 14, "%.3f" % end, 10, col, "start")
        s += txt(cx, y1 + 18, n, 12, weight="600")
        s += txt(cx, y1 + 34, "끝 손실 %.3f" % l, 10, INK2)
    s += txt(W / 2, H - 10, "찬 점 = 곡선 최고, 빈 점 = 끝. 읽기 오차 1 픽셀 = 0.00068. 평가는 10 에폭마다이고 시험 이상 이미지를 쓴다(원문이 실제로는 못 쓴다고 적음)", 10.5, INK2)
    svg("fig04_fig2a_peak_end", W, H, s, "그림 2a 의 최고와 끝")


def _curve(key, idx, f):
    return [(f(e), CURVES[key][e][idx]) for e in sorted(CURVES[key])]


def fig05():
    W, H = 900, 400
    s = txt(W / 2, 28, "그림 4 를 같은 갱신 횟수로 다시 놓으면 (내가 읽고 옮긴 것)", 14, weight="600")
    x0, x1, y0, y1 = 70, 860, 56, 300
    un_iter = N_TRAIN / float(BATCH)
    se_iter = un_iter / 15.0
    xmax = 12000.0
    fx = lambda u: x0 + (x1 - x0) * min(u, xmax) / xmax
    fy = lambda v: y1 - (y1 - y0) * (v - 0.70) / 0.30
    s += frame(x0, y0, x1, y1, [0, 2000, 4000, 6000, 8000, 10000, 12000], [0.70, 0.80, 0.90, 1.00], fx, fy,
               "갱신 횟수 (통합 56.7 회/에폭, 부류별 평균 3.78 회/에폭 가정)", "AUROC", yfmt=lambda t: "%.2f" % t)
    for key, it, dash in (("uni", un_iter, None), ("sep", se_iter, "6,4")):
        for idx, col in ((0, REV), (1, OK)):
            pts = [(fx(e * it), fy(CURVES[key][e][idx])) for e in sorted(CURVES[key]) if e * it <= xmax]
            s += poly(pts, col, 2.2, dash)
    end = 1000 * se_iter
    s += line(fx(end), y0, fx(end), y1, INK2, 1.2, "3,3")
    s += txt(fx(end) + 6, y0 + 14, "부류별 끝 = 평균 %d 회 = 통합 %.1f 에폭" % (round(end), end / un_iter), 11, INK2, "start")
    s += circ(fx(119 * un_iter), fy(.899), 4, REV, REV) + txt(fx(119 * un_iter) + 8, fy(.899) - 8, "통합 픽셀 최고 0.899 (에폭 119)", 10, REV, "start")
    s += circ(fx(149 * un_iter), fy(.825), 4, OK, OK) + txt(fx(149 * un_iter) + 8, fy(.825) - 8, "통합 이미지 최고 0.825 (에폭 149)", 10, OK, "start")
    s += txt(x1 - 6, fy(.72), "실선 통합 · 점선 부류별 · 빨강 픽셀 · 초록 이미지. 가로축은 12,000 회에서 자름(통합은 56,703 회까지 간다)", 10, INK2, "end")
    s += txt(W / 2, H - 28, "부류별 곡선은 통합 곡선이 꺾이기 전에 끝난다 — 이 그림으로는 부류별이 나중에 꺾이는지 알 수 없다", 12, NO, weight="600")
    s += txt(W / 2, H - 8, "가정: 부류별도 배치 64 · 1000 에폭, 학습 3,629 장 / 15 부류. 부류별 배치 크기는 본문에 없다", 10.5, INK2)
    svg("fig05_fig4_updates", W, H, s, "그림 4 를 갱신 횟수로")


def fig06():
    W, H = 880, 420
    s = txt(W / 2, 28, "표 1 · 2 평균 — 부류별(옮긴 값)에서 통합(직접 돌린 값)으로", 14, weight="600")
    x0, x1, y0, y1 = 90, 750, 60, 170
    rows = [("검출 (표 1)", T1_MEAN, 56), ("위치 (표 2)", T2_MEAN, 226)]
    for title, tab, top in rows:
        y0, y1 = top + 20, top + 136
        fx = lambda v: x0 + (x1 - x0) * (v - 60) / 40.0
        n = len(tab)
        s += txt(x0, top + 10, title, 12, weight="600", anchor="start")
        for t in (60, 70, 80, 90, 100):
            s += line(fx(t), y0, fx(t), y1, LINE, 1) + txt(fx(t), y1 + 14, "%d" % t, 10, MUTED)
        for i, (k, (u, se)) in enumerate(tab.items()):
            y = y0 + 8 + i * (y1 - y0 - 8) / float(n)
            col = OK if k == "Ours" else FWD
            s += txt(x0 - 8, y + 4, k, 11, col if k == "Ours" else INK2, "end", "600" if k == "Ours" else None)
            s += line(fx(u), y, fx(se), y, col, 2.4)
            s += circ(fx(u), y, 4.5, col, col) + circ(fx(se), y, 4.5, BG, col, 2)
            s += txt(fx(max(u, se)) + 8, y + 4, "%.1f / %.1f (%+.1f)" % (u, se, u - se), 10, INK2, "start")
    s += txt(W / 2, H - 10, "찬 점 = 통합, 빈 점 = 부류별. Ours 만 두 값이 모두 저자의 실행이고, 나머지 부류별 값은 그 논문에서 옮겼다(US 는 DRAEM 논문에서)", 10.5, INK2)
    svg("fig06_means_drop", W, H, s, "통합과 부류별의 평균")


def fig07():
    W, H = 900, 400
    s = txt(W / 2, 28, "통합 설정 부류별 칸 — Ours 빼기 다른 여섯 중 최고 (내가 뺀 값)", 14, weight="600")
    x0, x1, y0, y1 = 70, 870, 56, 300
    fy = lambda v: y1 - (y1 - y0) * (v + 10) / 30.0
    s += frame(x0, y0, x1, y1, [], [-10, 0, 10, 20], lambda t: t, fy, None, "점 차")
    s += line(x0, fy(0), x1, fy(0), INK2, 1.4)
    w = (x1 - x0) / 15.0
    for i, c in enumerate(CLASSES):
        bd = T1["Ours"][0][i] - max(T1[k][0][i] for k in T1 if k != "Ours")
        bl = T2["Ours"][0][i] - max(T2[k][0][i] for k in T2 if k != "Ours")
        x = x0 + i * w + 6
        for dx, v, col in ((0, bd, FWD), (w / 2 - 6, bl, REV)):
            top = fy(max(v, 0))
            s += bar(x + dx, top, w / 2 - 8, abs(fy(0) - fy(v)), col)
            s += txt(x + dx + (w / 2 - 8) / 2, (fy(v) - 4) if v >= 0 else (fy(v) + 12), "%+.1f" % v, 8.5, col)
        s += ('<text x="%.1f" y="%.1f" font-size="10" fill="%s" text-anchor="end" transform="rotate(-35 %.1f %.1f)">%s</text>'
              % (x + w / 2, y1 + 16, INK2, x + w / 2, y1 + 16, esc(c)))
    s += txt(W / 2, H - 8, "파랑 검출(표 1) · 빨강 위치(표 2). 0 위가 Ours 가 이긴 칸이다. 두 표의 상대 여섯은 CutPaste 와 FCDD 한 자리가 다르다", 11, INK2)
    svg("fig07_per_class_margin", W, H, s, "부류별 차이")


def fig08():
    W, H = 880, 400
    s = txt(W / 2, 28, "표 S2 — 질의 · 이웃 가림 · 흔들기의 조합 아홉", 14, weight="600")
    x0, x1, y0, y1 = 250, 800, 52, 330
    fx = lambda v: x0 + (x1 - x0) * (v - 65) / 35.0
    for t in (70, 80, 90, 100):
        s += line(fx(t), y0, fx(t), y1, LINE, 1) + txt(fx(t), y1 + 14, "%d" % t, 10, MUTED)
    n = len(S2)
    for i, (q, a, b, d, l) in enumerate(S2):
        y = y0 + 10 + i * (y1 - y0 - 8) / float(n)
        lab = "질의 %s · NMA %s · FJ %s" % (q, "O" if a else "-", "O" if b else "-")
        s += txt(x0 - 10, y + 8, lab, 11, INK2, "end", "600" if (q, a, b) == ("층별", 1, 1) else None)
        s += bar(x0, y, fx(d) - x0, 10, FWD) + bar(x0, y + 11, fx(l) - x0, 10, REV)
        s += txt(fx(d) + 5, y + 9, "%.1f" % d, 10, FWD, "start") + txt(fx(l) + 5, y + 20, "%.1f" % l, 10, REV, "start")
    s += txt(W / 2, H - 28, "하나 넣기 몫 합 7.4 + 8.5 + 7.4 = 23.3 점인데 셋 다 넣은 몫은 8.9 점이다(1 질의 기준, 검출)", 12, NO, weight="600")
    s += txt(W / 2, H - 8, "이미 NMA + FJ 를 둔 1 질의(96.2 / 96.6)에 층별 질의를 더한 몫은 +0.3 / +0.2 점. 표 5a 는 이 행을 싣지 않았다", 11, INK2)
    svg("fig08_s2_combinations", W, H, s, "표 S2 조합")


def fig09():
    W, H = 860, 350
    s = txt(W / 2, 28, "표 5b — 디코더가 없는 줄 (4, 0) 에는 질의 임베딩이 없다", 14, weight="600")
    x0, x1, y0, y1 = 70, 820, 56, 276
    fy = lambda v: y1 - (y1 - y0) * (v - 60) / 40.0
    s += frame(x0, y0, x1, y1, [], [60, 70, 80, 90, 100], lambda t: t, fy, None, "검출 AUROC")
    for i, (e, d, vd, vl, od, ol) in enumerate(T5B):
        cx = 120 + i * 150
        for dx, v, col in ((-26, vd, MUTED), (26, od, FWD)):
            s += bar(cx + dx - 22, fy(v), 44, y1 - fy(v), col)
            s += txt(cx + dx, fy(v) - 5, "%.1f" % v, 11, col)
        s += txt(cx, y1 + 18, "%d, %d" % (e, d), 12, weight="600")
    s += txt(120, y1 + 31, "질의 없음", 11, NO, weight="600")
    s += txt(W / 2, H - 24, "회색 = Vanilla, 파랑 = Ours. 줄 (4, 0) 의 Ours 94.9 / 96.0 은 질의 없이 NMA + FJ 만 넣은 값이다(내 해석)", 12, NO, weight="600")
    s += txt(W / 2, H - 6, "가로축은 (인코더 층, 디코더 층). 그림 3 에서 질의 임베딩은 디코더 층 안에만 있다", 11, INK2)
    svg("fig09_tab5b_no_query", W, H, s, "표 5b")


def fig10():
    W, H = 880, 370
    groups = [("이웃 크기 5c", T5C), ("NMA 자리 5d", T5D), ("α 5e", T5E), ("p 5f", T5F),
              ("손실 S4", S4), ("백본 S6", [(a, c, d) for a, b, c, d, e in S6])]
    s = txt(W / 2, 28, "하이퍼파라미터 줄의 검출 값 — 기본값 96.5 에서의 차이와 ±0.08", 14, weight="600")
    x0, x1, y0, y1 = 70, 860, 56, 290
    fy = lambda v: y1 - (y1 - y0) * (v + 4.5) / 5.0
    s += frame(x0, y0, x1, y1, [], [-4, -3, -2, -1, 0], lambda t: t, fy, None, "96.5 대비 점 차")
    s += bar(x0, fy(0.08), x1 - x0, fy(-0.08) - fy(0.08), CODE_SOFT)
    s += txt(x0 + 6, fy(0.08) - 6, "띠 = 기본 설정의 ±0.08 (5 seed, 표 1 평균)", 10, CODE, "start")
    w = (x1 - x0) / float(len(groups))
    for i, (g, rows) in enumerate(groups):
        cx = x0 + w * (i + 0.5)
        s += txt(cx, y1 + 18, g, 11, weight="600")
        s += line(x0 + w * (i + 1), y0, x0 + w * (i + 1), y1, LINE, 1)
        n = len(rows)
        for j, (lab, d, l) in enumerate(rows):
            x = cx + (j - (n - 1) / 2.0) * (w - 20) / max(n, 1)
            v = d - 96.5
            col = OK if abs(v) < 1e-9 else FWD
            s += circ(x, fy(v), 4, col, col)
    s += txt(W / 2, H - 28, "기본값이 그 표의 검출 최고이거나 공동 최고인 표가 다섯이고, 예외는 S4 의 Cosine 96.6 하나다", 12, NO, weight="600")
    s += txt(W / 2, H - 8, "모두 시험 이미지 값이고 검증 집합은 적혀 있지 않다. 이 줄들의 반복 수도 적혀 있지 않다", 11, INK2)
    svg("fig10_hparam_spread", W, H, s, "하이퍼파라미터 줄")


def fig11():
    W, H = 880, 340
    s = txt(W / 2, 28, "표 3 — CIFAR-10 다섯 대 다섯 (검출 AUROC)", 14, weight="600")
    x0, x1, y0, y1 = 70, 860, 56, 266
    fy = lambda v: y1 - (y1 - y0) * (v - 40) / 60.0
    s += frame(x0, y0, x1, y1, [], [40, 60, 80, 100], lambda t: t, fy, None, "AUROC")
    names = ["{01234}", "{56789}", "{02468}", "{13579}", "평균"]
    cols = {"US": MUTED, "FCDD": INK2, "FCDD+OE": PURP, "PANDA": CODE, "MKD": REV, "Ours": FWD}
    for i, n in enumerate(names):
        cx = x0 + 80 + i * 156
        for j, k in enumerate(cols):
            v = T3[k][i]
            x = cx - 60 + j * 20
            s += bar(x, fy(v), 18, y1 - fy(v), cols[k])
            if k in ("Ours", "FCDD+OE"):
                s += txt(x + 9, fy(v) - 4, "%.1f" % v, 10, cols[k])
        s += txt(cx, y1 + 18, n, 12, weight="600")
    for j, k in enumerate(cols):
        s += bar(120 + j * 112, H - 34, 12, 12, cols[k]) + txt(136 + j * 112, H - 24, k, 11, INK2, "start")
    s += txt(W / 2, H - 6, "모델 쪽 설정이 MVTec 과 다르다: 단계 1 ~ 5, 720 채널, 배치 128. FCDD+OE 만 CIFAR-100 1 만 장을 더 쓴다", 11, INK2)
    svg("fig11_tab3_cifar", W, H, s, "표 3")


def fig12():
    W, H = 880, 350
    s = txt(W / 2, 28, "표 4 — 「질의 하나로 앞선다」 의 비교에 함께 바뀐 것", 14, weight="600")
    x0, x1, y0, y1 = 70, 860, 56, 250
    fy = lambda v: y1 - (y1 - y0) * (v - 40) / 60.0
    s += frame(x0, y0, x1, y1, [], [40, 60, 80, 100], lambda t: t, fy, None, "검출 AUROC")
    rows = [("InTra", 65.3, "이미지 재구성"), ("VT-ADL", 55.4, "이미지 재구성"), ("AnoVit", 69.6, "이미지 재구성"),
            ("질의 없음 (표 5a)", 69.5, "특징 재구성"), ("1 질의 (표 4 · 5a)", 87.6, "특징 재구성"), ("Ours", 96.5, "특징 재구성")]
    for i, (n, v, kind) in enumerate(rows):
        cx = x0 + 70 + i * 128
        col = REV if kind.startswith("이미지") else FWD
        s += bar(cx - 28, fy(v), 56, y1 - fy(v), col)
        s += txt(cx, fy(v) - 5, "%.1f" % v, 12, col, weight="600")
        s += txt(cx, y1 + 18, n, 10.5, weight="600")
        s += txt(cx, y1 + 34, kind, 10, INK2)
    s += txt(W / 2, H - 28, "같은 조건에서 질의의 몫이 보이는 쌍은 표 5a 의 69.5 대 87.6 하나다(+18.1 점)", 12, NO, weight="600")
    s += txt(W / 2, H - 8, "앞 셋의 재구성 대상은 2 절의 설명을 따랐다. 그 셋의 통합 값을 누가 돌렸는지는 4.5 절에 적혀 있지 않다", 11, INK2)
    svg("fig12_tab4_confound", W, H, s, "표 4")


def fig13():
    W, H = 880, 360
    s = txt(W / 2, 28, "표 S7 — 재구성 망의 크기 (로그 눈금)", 14, weight="600")
    x0, x1, y0, y1 = 70, 860, 56, 270
    fy = lambda v: y1 - (y1 - y0) * (math.log10(v) + 1) / 4.0
    s += frame(x0, y0, x1, y1, [], [0.1, 1, 10, 100, 1000], lambda t: t, fy, None, "값 (로그)")
    for i, (n, fl, p) in enumerate(S7):
        cx = x0 + 52 + i * 98
        col = OK if n == "Ours" else FWD
        s += bar(cx - 30, fy(fl), 28, y1 - fy(fl), MUTED) + bar(cx + 2, fy(p), 28, y1 - fy(p), col)
        s += txt(cx - 16, fy(fl) - 4, "%g" % fl, 9.5, INK2) + txt(cx + 16, fy(p) - 4, "%g" % p, 9.5, col)
        s += txt(cx, y1 + 18, n, 11, weight="600")
    s += txt(W / 2, H - 42, "회색 = FLOPs(G), 파랑 = 「학습 파라미터」(M). Ours 는 작은 쪽에서 파라미터 넷째, FLOPs 둘째다", 12, INK2)
    s += txt(W / 2, H - 24, "PaDiM 950.36M = 56 x 56 칸 x (550 + 550^2). 경사로 배우는 값이 아니라 통계량이고 WRN-50 · 550 차원과 맞는다(내 셈)", 11, NO)
    s += txt(W / 2, H - 8, "얼린 백본은 세지 않은 듯하다: Ours 7.48M 에 EfficientNet-b4 가 없다. 부류별이면 곱해질 저장량은 이 표에 없다", 11, INK2)
    svg("fig13_s7_complexity", W, H, s, "표 S7")


def fig14():
    W, H = 900, 372
    s = txt(W / 2, 28, "값이 어디서 왔나 — 표의 칸마다", 14, weight="600")
    head = ["표", "상대의 통합 값", "상대의 부류별 값", "Ours 설정", "Ours 흩어짐"]
    xs = [20, 150, 370, 590, 770]
    ws = [130, 220, 220, 180, 110]
    rows = [
        ("표 1 검출", "공개 구현을 저자가 돌림", "그 논문의 값 (US 는 DRAEM 논문)", "224, b4 단계 1 ~ 4, 272", "통합 5 seed"),
        ("표 2 위치", "공개 구현을 저자가 돌림", "그 논문의 값 (FCDD 포함)", "표 1 과 같음", "통합 5 seed"),
        ("표 3 CIFAR", "공개 구현을 저자가 돌림", "해당 없음", "224, b4 단계 1 ~ 5, 720", "5 seed"),
        ("표 4 Transformer 꼴", "누가 돌렸는지 적혀 있지 않음", "적혀 있지 않음", "표 1 과 같음", "표에 없음"),
        ("표 5 · S2 ~ S6", "상대 없음 (자기 변형)", "해당 없음", "한 항목씩 바꿈", "표에 없음"),
        ("표 S7", "입력 224 로 저자가 잼", "해당 없음", "224", "해당 없음"),
    ]
    y = 50
    for j, h in enumerate(head):
        s += box(xs[j], y, ws[j], 28, FWD_SOFT, FWD, rx=2) + txt(xs[j] + ws[j] / 2, y + 19, h, 11, weight="600")
    for i, r in enumerate(rows):
        yy = y + 30 + i * 38
        for j, c in enumerate(r):
            fill = NODE
            if j == 2 and c.startswith("그 논문"):
                fill = REV_SOFT
            if "적혀 있지" in c or c == "표에 없음":
                fill = NO_SOFT
            s += box(xs[j], yy, ws[j], 36, fill, LINE, rx=2)
            s += txt(xs[j] + ws[j] / 2, yy + 23, c, 10 if len(c) > 20 else 10.5, INK if j == 0 else INK2)
    s += txt(W / 2, H - 28, "표 1 · 2 의 「떨어졌다」 는 다른 논문의 값(주황 칸)과 저자가 돌린 값의 차이이고, 상대의 입력 크기 · 백본 · 체크포인트는 적혀 있지 않다", 11, NO, weight="600")
    s += txt(W / 2, H - 8, "PatchCore · SPADE 는 어느 표에도 없다(본문 · 보충 자료 전체 글자 찾기, 참고 문헌 포함)", 11, INK2)
    svg("fig14_value_sources", W, H, s, "값의 출처")


# ── 다시 계산해 찍기 ──────────────────────────────────────────────────────
def checks():
    print("\n[표 1 · 2 평균 재계산: 인쇄 값과 부류 칸 평균]")
    for name, T, M in (("표 1", T1, T1_MEAN), ("표 2", T2, T2_MEAN)):
        for k in T:
            u, se = T[k]
            print("  %s %-9s 통합 %.3f (인쇄 %.1f, 차 %+.3f) | 부류별 %.3f (인쇄 %.1f, 차 %+.3f) | 통합-부류별 인쇄 %+.1f" % (
                name, k, mean(u), M[k][0], mean(u) - M[k][0], mean(se), M[k][1], mean(se) - M[k][1], M[k][0] - M[k][1]))
    print("\n[통합 칸에서 Ours 가 최고인 부류 수 (동률 포함)]")
    for name, T in (("표 1", T1), ("표 2", T2)):
        wins = [c for i, c in enumerate(CLASSES) if all(T["Ours"][0][i] >= T[k][0][i] for k in T)]
        lose = [(c, max((T[k][0][i], k) for k in T if k != "Ours"), T["Ours"][0][i]) for i, c in enumerate(CLASSES)
                if not all(T["Ours"][0][i] >= T[k][0][i] for k in T)]
        print("  %s 이김 %d / 15: %s" % (name, len(wins), wins))
        print("     진 칸: %s" % lose)
        ms = [(c, round(T["Ours"][0][i] - max(T[k][0][i] for k in T if k != "Ours"), 1)) for i, c in enumerate(CLASSES)]
        print("     차이: %s" % ms)
    print("\n[통합 칸의 물체 10 · 질감 5 평균]")
    for name, T in (("표 1", T1), ("표 2", T2)):
        for k in T:
            print("  %s %-9s 물체 %.2f 질감 %.2f" % (name, k, mean(T[k][0][:10]), mean(T[k][0][10:])))
    print("\n[통합 값이 부류별 값 이상인 칸 수 (같으면 ≥ 로 셈)]")
    for name, T in (("표 1", T1), ("표 2", T2)):
        for k in T:
            cells = [(c, T[k][0][i], T[k][1][i]) for i, c in enumerate(CLASSES) if T[k][0][i] >= T[k][1][i]]
            print("  %s %-9s %d 칸: %s" % (name, k, len(cells), cells))
    print("\n[부류별 설정 평균 순위]")
    for name, M in (("표 1", T1_MEAN), ("표 2", T2_MEAN)):
        print("  %s %s" % (name, sorted(((v[1], k) for k, v in M.items()), reverse=True)))
    print("\n[Ours 통합 ± 를 독립으로 합치면 (표준편차로 읽을 때 평균의 값)]")
    for name, P, pr in (("표 1", T1_PM, 0.08), ("표 2", T2_PM, 0.02)):
        print("  %s sqrt(sum s^2)/15 = %.3f, 인쇄 %.2f, 부류 칸 최대 %.2f" % (name, math.sqrt(sum(x * x for x in P)) / 15, pr, max(P)))
    print("\n[본문이 적은 차이]")
    print("  DRAEM 검출 낙폭 %.1f, CutPaste %.1f, 1위와 차 %.1f" % (98.0 - 88.1, 96.1 - 77.5, 96.5 - 88.1))
    print("  US 위치 낙폭 %.1f, FCDD %.1f, PaDiM 과 차 %.1f" % (93.9 - 81.8, 92 - 63.3, 96.8 - 89.5))
    print("  FCDD+OE 와 차 %.1f" % (87.2 - 78.9))
    print("\n[표 3 평균]")
    for k, v in T3.items():
        print("  %-8s 네 칸 평균 %.3f, 인쇄 %.1f" % (k, mean(v[:4]), v[4]))
    print("\n[표 5a / S2 몫: 1 질의 기준]")
    d = {(q, a, b): (dd, l) for q, a, b, dd, l in S2}
    base = d[("1", 0, 0)]
    for lab, key in (("1 질의 - 없음", None), ("층별", ("층별", 0, 0)), ("NMA", ("1", 1, 0)), ("FJ", ("1", 0, 1)), ("NMA+FJ", ("1", 1, 1)), ("셋", ("층별", 1, 1))):
        if key is None:
            print("  %s: %+.1f / %+.1f" % (lab, base[0] - d[("없음", 0, 0)][0], base[1] - d[("없음", 0, 0)][1]))
        else:
            print("  %s: %+.1f / %+.1f" % (lab, d[key][0] - base[0], d[key][1] - base[1]))
    print("  세 몫의 합 검출 %.1f, 위치 %.1f" % (7.4 + 8.5 + 7.4, 3.7 + 3.5 + 3.0))
    print("  층별 기준 NMA %+.1f / %+.1f, FJ %+.1f / %+.1f, 둘 %+.1f / %+.1f" % (
        95.8 - 95.0, 96.5 - 96.5, 94.9 - 95.0, 96.2 - 96.5, 96.5 - 95.0, 96.8 - 96.5))
    print("  NMA+FJ 위에 층별 질의: %+.1f / %+.1f" % (96.5 - 96.2, 96.8 - 96.6))
    print("  표 5b (4,0) Ours - Vanilla: %+.1f / %+.1f, Ours (4,4) 와 차 %+.1f / %+.1f" % (94.9 - 69.8, 96.0 - 79.2, 94.9 - 96.5, 96.0 - 96.8))
    print("\n[표 4 부류별에서 통합으로 (Ours baseline)] 검출 %+.1f, 위치 %+.1f" % (87.6 - 94.7, 92.8 - 95.8))
    print("\n[표 S6 파라미터: 인쇄 대 torchvision 전체]")
    for n, p, dd, l, tv in S6:
        print("  %-8s 인쇄 %5.1fM, torchvision %.2fM, 차 %+.2fM" % (n, p, tv / 1e6, p - tv / 1e6))
    print("\n[표 S7 학습 파라미터 순위] %s" % sorted((p, n) for n, f, p in S7))
    print("[표 S7 FLOPs 순위] %s" % sorted((f, n) for n, f, p in S7))
    print("\n[갱신 횟수] 통합 %.1f 회/에폭, 부류별 평균 %.2f 회/에폭, 부류별 1000 에폭 = %.0f 회 = 통합 %.1f 에폭" % (
        N_TRAIN / float(BATCH), N_TRAIN / 15.0 / BATCH, N_TRAIN / 15.0 / BATCH * 1000, 1000 / 15.0))
    print("  같은 갱신 수에서 통합(에폭 67) 픽셀 %.3f 이미지 %.3f 손실 %.3f | 부류별(에폭 1000) 픽셀 %.3f 이미지 %.3f 손실 %.3f" % (
        CURVES["uni"][67] + CURVES["sep"][1000]))
    print("  같은 에폭 1000 손실 비 %.1f 배, 같은 갱신 수 손실 비 %.2f 배 (분모 통합)" % (.997 / .111, .997 / .443))
    print("  같은 손실에 닿는 에폭 비 (부류별 / 통합): 10 -> %.1f, 5 -> %.1f, 3 -> %.1f, 2 -> %.1f, 1.5 -> %.1f, 1.2 -> %.1f" % (
        112 / 9.0, 232 / 15.0, 351 / 20.0, 482 / 24.0, 600 / 29.0, 722 / 33.0))
    print("\n[그림 2a 낙폭: 최고 - 끝]")
    for n, pp, pe, ip, ie, pz, iz, l in FIG2A:
        print("  %-12s 픽셀 %.3f, 이미지 %.3f" % (n, pp - pz, ip - iz))
    print("  표 5a 1 질의 87.6 / 92.8 대 곡선 끝 %.1f / %.1f, 곡선 최고 %.1f / %.1f" % (84.7, 90.6, 91.4, 93.7))


if __name__ == "__main__":
    print("그림을 만든다")
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10, fig11, fig12, fig13, fig14):
        f()
    checks()
