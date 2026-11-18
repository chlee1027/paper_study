# -*- coding: utf-8 -*-
r"""AnomalyCLIP 원문(arXiv v8, 31 쪽)의 표 값과 그림 6 · 7 의 값을 PDF 에서 읽어 tables_anomalyclip.json 으로 둔다.

PyMuPDF 가 필요하다. 손으로 옮기지 않고 글자 층과 벡터 경로에서 읽는다.

- 표 1 \~ 5 · 7 \~ 21: 글자 층의 줄을 차례로 읽는다. 「(a, b)」 짝은 쉼표 대신 마침표가 찍힌 칸(표 8 의 「(78.6. 84.1)」)도 읽는다.
- 그림 6(레이더 넷): 색 선 다각형의 꼭짓점 반지름을 바깥 틀 반지름으로 나눠 값으로 바꾼다.
  눈금은 가운데가 75(AUPRO 는 50), 바깥 틀이 100 이다. V-V 줄 28 값이 표 1 과 모두 같은 것으로 이 읽기를 확인한다.
- 그림 7(선 그래프 여덟): 표식 사각형의 중심을 축 눈금 글자 위치로 값으로 바꾼다. 소수 둘째 자리는 읽기 오차다.

  python read_tables.py
"""
import json
import math
import os
import re

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "..", "papers",
                   "ICLR24_AnomalyCLIP_Object_Agnostic_Prompt_Learning_for_Zero_Shot_Anomaly_Detection.pdf")
doc = pymupdf.open(PDF)
PAIR = re.compile(r"\((\d+(?:\.\d+)?)\s*[,.]\s*(\d+(?:\.\d+)?)\)|\(-,\s*-\)")
METHODS = ["CLIP", "CLIP-AC", "WinCLIP", "VAND", "CoOp", "AnomalyCLIP"]


def lines(page, start=None, stop=None):
    t = doc[page - 1].get_text()
    if start:
        t = t[t.index(start):]
    if stop and stop in t:
        t = t[:t.index(stop)]
    return [s.strip() for s in t.split("\n") if s.strip()]


def pairs(s):
    out = []
    for m in PAIR.finditer(s):
        out.append(None if m.group(1) is None else [float(m.group(1)), float(m.group(2))])
    return out


def rows_by_name(ls, names, k, skip_int=False):
    """이름 줄 다음(정수 |C| 줄이 있으면 건너뛰고)의 짝 k 개를 읽는다. 같은 이름이 두 번 나오면 두 번째는 화소 쪽이다."""
    res, i = [], 0
    while i < len(ls):
        tok = ls[i]
        name = next((n for n in names if tok == n or tok.startswith(n + " (")), None)
        if name is None:
            i += 1
            continue
        j = i + 1
        rest = tok[len(name):]
        if skip_int and j < len(ls) and ls[j].isdigit():
            j += 1
        got = pairs(rest)
        while len(got) < k and j < len(ls):
            p = pairs(ls[j])
            if not p:
                break
            got += p
            j += 1
        if len(got) == k:
            res.append((name, got))
            i = j
        else:
            i += 1
    return res


def split_levels(rows):
    img, pix = {}, {}
    for name, v in rows:
        (pix if name in img else img)[name] = v
    return img, pix


J = {}

# 표 1 (산업, 7 쪽)
IND = ["MVTec AD", "VisA", "MPDD", "BTAD", "SDD", "DAGM", "DTD-Synthetic"]
img, pix = split_levels(rows_by_name(lines(7, "Table 1:", "Table 2:"), IND, 6, skip_int=True))
J["table1"] = {"methods": METHODS, "image_auroc_ap": img, "pixel_auroc_pro": pix}

# 표 2 (의료, 7 쪽)
MED_IMG = ["HeadCT", "BrainMRI", "Br35H", "COVID-19"]
MED_PIX = ["ISIC", "CVC-ColonDB", "CVC-ClinicDB", "Kvasir", "Endo", "TN3K"]
r = dict(rows_by_name(lines(7, "Table 2:", "datasets HeadCT"), MED_IMG + MED_PIX, 6, skip_int=True))
J["table2"] = {"methods": METHODS,
               "image_auroc_ap": {k: r[k] for k in MED_IMG},
               "pixel_auroc_pro": {k: r[k] for k in MED_PIX}}

# 표 3 (의료 데이터로 배운 판, 8 쪽)
r = dict(rows_by_name(lines(8, "Table 3:"), MED_IMG + [m for m in MED_PIX if m != "CVC-ColonDB"], 2))
J["table3"] = {"methods": ["VAND", "AnomalyCLIP"], "rows": r}

# 표 4 · 5 (9 쪽)
ls = lines(9, "Table 4:", "Figure 6")
mods = ["Base", "+T1", "+T2", "+T3", "+T4"]
t4, i = {}, 0
for m in mods:
    i = ls.index(m, i)
    got = []
    j = i + 1
    while len(got) < 4:
        got += pairs(ls[j])
        j += 1
    t4[m] = got
J["table4"] = {"columns": ["MVTec pixel (AUROC, PRO)", "MVTec image (AUROC, AP)",
                           "VisA pixel (AUROC, PRO)", "VisA image (AUROC, AP)"], "rows": t4}
CROSS, CHECK = chr(0x2717), chr(0x2713)  # 표 5 의 끔 · 켬 표시
ls5 = ls[ls.index("Table 5: Context optimization ablation."):]
marks = [t for t in ls5 if t in (CROSS, CHECK)]
vals = [p for t in ls5 for p in pairs(t)]
J["table5"] = {"columns": J["table4"]["columns"],
               "rows": [{"local": marks[2 * k] == CHECK, "global": marks[2 * k + 1] == CHECK,
                         "values": vals[4 * k:4 * k + 4]} for k in range(4)]}

# 표 7 (18 쪽)
img, pix = split_levels(rows_by_name(lines(18, "Table 7:", "Ablation on"), IND, 3, skip_int=True))
J["table7"] = {"methods": ["AnomalyCLIP", "PatchCore", "RD4AD"], "image_auroc_ap": img, "pixel_auroc_pro": pix}

# 표 8 · 9 (19 · 20 쪽)
WORDS = ["damaged", "anomalous", "flawed", "defective", "blemished"]
img, pix = split_levels(rows_by_name(lines(19, "Table 8:", "Figure 8"), IND, 5))
J["table8"] = {"words": WORDS, "image_auroc_ap": img, "pixel_auroc_pro": pix}
r = dict(rows_by_name(lines(20, "Table 9:", "Table 10:"), MED_IMG + MED_PIX, 5))
J["table9"] = {"words": WORDS, "image_auroc_ap": {k: r[k] for k in MED_IMG},
               "pixel_auroc_pro": {k: r[k] for k in MED_PIX}}

# 표 10 \~ 21 (부류별, 20 \~ 23 쪽)
CW = {10: (20, "MVTec AD", "pixel AUROC"), 11: (21, "MVTec AD", "PRO"), 12: (21, "MVTec AD", "image AUROC"),
      13: (21, "MVTec AD", "image AP"), 14: (21, "VisA", "pixel AUROC"), 15: (22, "VisA", "PRO"),
      16: (22, "VisA", "image AUROC"), 17: (22, "VisA", "image AP"), 18: (22, "MPDD", "pixel AUROC"),
      19: (22, "MPDD", "PRO"), 20: (23, "MPDD", "image AUROC"), 21: (23, "MPDD", "image AP")}
J["classwise"] = {"methods": METHODS}
for n, (page, data, metric) in CW.items():
    ls = lines(page, f"Table {n}:")
    i = ls.index("AnomalyCLIP") + 1
    rows = {}
    while True:
        name = ls[i]
        nums = [float(x) for x in ls[i + 1:i + 7]]
        rows[name] = nums
        i += 7
        if name == "Mean":
            break
    J["classwise"][f"table{n}"] = {"data": data, "metric": metric, "rows": rows}


# 그림 6 (9 쪽, 레이더 넷): 모서리 차례는 MVTec AD(위) 부터 반시계로 VisA · MPDD · BTAD · SDD · DAGM · DTD
def segs(x):
    return [it[1] for it in x["items"] if it[0] == "l"]


def col(x, key):
    c = x.get(key)
    return tuple(round(v, 2) for v in c) if c else None


pg = doc[8]
dr = [x for x in pg.get_drawings() if x["rect"].y0 > 140 and x["rect"].y1 < 225]
frames = sorted([x for x in dr if col(x, "color") == (0, 0, 0) and len(x["items"]) == 7], key=lambda x: x["rect"].x0)
ANG = {90: "MVTec AD", 141: "VisA", -167: "MPDD", -116: "BTAD", -64: "SDD", -13: "DAGM", 39: "DTD-Synthetic"}
PANELS = [("pixel AUROC", 75), ("PRO", 50), ("image AUROC", 75), ("image AP", 75)]
fig6 = {}
for (metric, lo), fr in zip(PANELS, frames):
    P = segs(fr)
    cx, cy = sum(p.x for p in P) / 7, sum(p.y for p in P) / 7
    R = max(math.hypot(p.x - cx, p.y - cy) for p in P)
    fig6[metric] = {}
    for c, name in [((0, 0, 1), "V-V"), ((1, 0, 0), "Q-Q"), ((0, 0.5, 0), "K-K")]:
        poly = [x for x in dr if col(x, "color") == c and len(x["items"]) == 7
                and abs((x["rect"].x0 + x["rect"].x1) / 2 - cx) < 40]
        assert len(poly) == 1
        out = {}
        for q in segs(poly[0]):
            a = round(math.degrees(math.atan2(-(q.y - cy), q.x - cx)))
            out[ANG[a]] = round(lo + math.hypot(q.x - cx, q.y - cy) / R * (100 - lo), 2)
        fig6[metric][name] = out
J["fig6"] = fig6

# 그림 7 (18 쪽, 선 그래프 여덟)
pg = doc[17]
dr = [x for x in pg.get_drawings() if x["rect"].y0 > 220 and x["rect"].y1 < 375]
words = pg.get_text("words")
axes = sorted([x["rect"] for x in dr if not x.get("color") and col(x, "fill") == (0.92, 0.92, 0.95)],
              key=lambda r: (round(r.y0), r.x0))
NAMES = ["E AUPRO", "E AP", "M AUPRO", "M AP", "L AUPRO", "L AP", "N AUPRO", "N AP"]
# 축은 위에서 아래, 왼쪽에서 오른쪽 차례다: (a) 왼 · 오, (b) 왼 · 오, 그다음 줄 (d) 왼 · 오 가 (c) 보다 위에 놓인다
order = []
for ax in axes:
    yt = [(float(w[4]), (w[1] + w[3]) / 2) for w in words
          if ax.x0 - 25 < w[2] <= ax.x0 + 1 and ax.y0 - 5 <= (w[1] + w[3]) / 2 <= ax.y1 + 5
          and w[4].replace(".", "").isdigit()]
    xt = [(float(w[4]), (w[0] + w[2]) / 2) for w in words
          if ax.y1 - 1 <= w[1] < ax.y1 + 8 and ax.x0 - 5 <= (w[0] + w[2]) / 2 <= ax.x1 + 5
          and w[4].replace(".", "").isdigit()]
    (v1, y1), (v2, y2) = yt[0], yt[-1]
    (u1, x1), (u2, x2) = xt[0], xt[-1]
    out = {}
    for x in dr:
        if x["items"][0][0] != "re" or col(x, "fill") not in ((0.3, 0.45, 0.69), (0.87, 0.52, 0.32)):
            continue
        r = x["rect"]
        mx, my = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        if not (ax.x0 - 2 <= mx <= ax.x1 + 2 and ax.y0 - 2 <= my <= ax.y1 + 2):
            continue
        xv = u1 + (mx - x1) * (u2 - u1) / (x2 - x1)
        if min(abs(xv - u) for u, _ in xt) > 0.15:
            continue  # 범례 표식
        key = "MVTec AD" if x["fill"][0] < 0.5 else "VisA"
        out.setdefault(key, {})[str(int(round(xv)))] = round(v1 + (my - y1) * (v2 - v1) / (y2 - y1), 2)
    order.append((ax.y0, ax.x0, xt[0][0], out))
# x 눈금 첫 값으로 어느 판인지 가른다: E 는 10, M 은 5, L 은 2, N 은 0 에서 시작한다
first = {10.0: "E", 5.0: "M", 2.0: "L", 0.0: "N"}
fig7 = {}
for y0, x0, start, out in order:
    p = first[start]
    side = "AUPRO" if f"{p} AUPRO" not in fig7 else "AP"
    fig7[f"{p} {side}"] = out
J["fig7"] = {k: fig7[k] for k in NAMES}

with open(os.path.join(HERE, "tables_anomalyclip.json"), "w", encoding="utf-8") as f:
    json.dump(J, f, ensure_ascii=False, indent=1)

# 확인: 그림 6 의 V-V 와 그림 7 의 기본값 자리가 표 1 과 같은가
t1i, t1p = J["table1"]["image_auroc_ap"], J["table1"]["pixel_auroc_pro"]
bad = 0
for ds in IND:
    for metric, src, k in [("pixel AUROC", t1p, 0), ("PRO", t1p, 1), ("image AUROC", t1i, 0), ("image AP", t1i, 1)]:
        got, want = fig6[metric]["V-V"][ds], src[ds][5][k]
        bad += abs(got - want) > 0.06
print("그림 6 V-V 대 표 1: 28 칸 중 어긋남", bad)
for key, x, ds_m, ds_v in [("E", "12", 1, 1), ("M", "9", 1, 1), ("L", "4", 1, 1), ("N", "4", 1, 1)]:
    print(key, x, "AUPRO", J["fig7"][f"{key} AUPRO"]["MVTec AD"][x], J["fig7"][f"{key} AUPRO"]["VisA"][x],
          "AP", J["fig7"][f"{key} AP"]["MVTec AD"][x], J["fig7"][f"{key} AP"]["VisA"][x])
print("표 1 AnomalyCLIP: MVTec PRO", t1p["MVTec AD"][5][1], "VisA PRO", t1p["VisA"][5][1],
      "MVTec AP", t1i["MVTec AD"][5][1], "VisA AP", t1i["VisA"][5][1])
print("부류별 표 행 수", {k: len(v["rows"]) for k, v in J["classwise"].items() if k != "methods"})
