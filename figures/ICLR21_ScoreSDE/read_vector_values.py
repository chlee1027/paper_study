# -*- coding: utf-8 -*-
"""원문 PDF 안의 벡터 좌표에서 그림 3 · 7 · 8 · 10 · 13 의 값을 읽어 paper_vector_values.json 으로 둔다.

축은 눈금 선 · 눈금 글자의 PDF 좌표로 맞춘다. pymupdf 가 있어야 돈다(make_figures.py 는 결과 json 만 읽는다).
"""
import json, math, os
import pymupdf

here = os.path.dirname(os.path.abspath(__file__))
doc = pymupdf.open(os.path.join(here, "..", "..", "papers",
    "ICLR21_ScoreSDE_Score_Based_Generative_Modeling_through_Stochastic_Differential_Equations.pdf"))


def col(x):
    return tuple(round(v, 2) for v in (x.get("color") or ()))


def fil(x):
    return tuple(round(v, 2) for v in (x.get("fill") or ()))


def centre(x):
    r = x["rect"]
    return (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2


out = {}
# 그림 3 왼쪽 (8 쪽). 가로 10^0 = 131.1, 10^1 = 151.3. 세로 0 = 168.8, 1 = 98.4. 범례 표식(각 줄 끝)은 뺀다.
dr = doc[7].get_drawings()
out["fig3"] = {}
for name, c in (("1e-1", (0.12, 0.47, 0.71)), ("1e-3", (1.0, 0.5, 0.05)), ("1e-5", (0.17, 0.63, 0.17))):
    m = [centre(x) for x in dr if x["type"] == "fs" and col(x) == c and len(x["items"]) == 8][:-1]
    out["fig3"][name] = [[round(10 ** ((p[0] - 131.1) / 20.2), 2), round((168.8 - p[1]) / 70.4, 4)] for p in m]

# 그림 7 (21 쪽). 가로 3.6 pt = 한 차원. 세로 눈금 글자 가운데 93.2 = 100, 117.8 = 0, 142.35 = -100.
dr = doc[20].get_drawings()
for key, c in (("A", (0.89, 0.1, 0.11)), ("B", (0.22, 0.49, 0.72))):
    m = [centre(x) for x in dr if x["type"] == "fs" and col(x) == c and len(x["items"]) == 12][:-1]
    out.setdefault("fig7", {})[key] = [round((117.8 - p[1]) * 100 / 24.6, 2) for p in m]

# 그림 8 왼쪽. 0 = 197.55, 300 = 291.94. 상자 · 중앙값 · 수염 · 이상점.
sc = (291.94 - 197.55) / 300
fl = [x for x in dr if x["type"] == "fs" and col(x) == (0.28, 0.28, 0.28) and len(x["items"]) == 4]
out["fig8_box"] = {}
for key, y, vals in (("A vs B", 229.5, (199.19, 201.14, 204.13, 211.53)),
                     ("shuffled", 276.3, (204.48, 212.29, 222.96, 250.68))):
    xs = [centre(x)[0] for x in fl if abs(centre(x)[1] - y) < 0.2]
    out["fig8_box"][key] = {"q1_med_q3_whisker": [round((v - 197.55) / sc, 1) for v in vals],
                            "fliers": len(xs), "flier_max": round((max(xs) - 197.55) / sc, 1)}
# 그림 8 오른쪽. 가로 0 = 354.04, 1 = 477.23. 세로 200 눈금 = 26.26 pt.
bars = [x for x in dr if x["type"] == "fs" and fil(x) == (0.89, 0.1, 0.11) and col(x) == (1, 1, 1)]
out["fig8_hist"] = [[round((b["rect"].x0 - 354.04) / 123.19, 4), round((b["rect"].x1 - 354.04) / 123.19, 4),
                     round((b["rect"].y1 - b["rect"].y0) * 200 / 26.26, 1)] for b in bars]
dots = [centre(x) for x in dr if x["type"] == "fs" and col(x) == (0.89, 0.1, 0.11) and len(x["items"]) == 8]
out["fig8_inset_dots"] = [[round(a, 2), round(-b, 2)] for a, b in dots]

# 그림 13 (30 쪽). 가로 log10: 0 = 386.14, 간격 32.29. 세로 0.2 = 615.82, 0.8 = 559.5.
dr = doc[29].get_drawings()
c = [x for x in dr if x["type"] == "s" and len(x["items"]) > 50][0]
pts = [(it[1].x, it[1].y) for it in c["items"]] + [(c["items"][-1][2].x, c["items"][-1][2].y)]
out["fig13"] = sorted([round(10 ** ((a - 386.14) / 32.29), 4), round(0.2 + (615.82 - b) * 0.6 / 56.32, 4)] for a, b in pts)

# 그림 10 (25 쪽): 앞 네 칸의 중앙값 · 수염. 세로 3.5 = 365.6, 37.73 pt = 1 (아래 줄 칸은 3.5 = 474.6, 37.8 pt = 1).
dr = doc[24].get_drawings()
L = [x["rect"] for x in dr if x["type"] == "s" and len(x["items"]) == 1 and 300 < x["rect"].y0 < 680
     and x["rect"].height < 0.01 and col(x) != (0.8, 0.8, 0.8)]
panels = {"FIR": ((137.5, 158.0), (158.5, 179.1), (190.0, 210.6), (211.0, 231.6)),
          "skip_rescale": ((266.7, 287.3), (287.7, 308.3), (319.2, 339.8), (340.2, 360.8)),
          "resblock_type": ((395.9, 416.5), (416.9, 437.5), (448.4, 469.0), (469.4, 490.0)),
          "num_res_blocks": ((150.6, 171.2), (171.6, 192.2), (203.1, 223.7), (224.1, 244.7))}
out["fig10"] = {}
for k, bs in panels.items():
    f = (lambda y: 3.5 - (y - 474.6) / 37.8) if k == "num_res_blocks" else (lambda y: 3.5 - (y - 365.6) / 37.73)
    row = []
    for a, b in bs:
        med = [l for l in L if abs(l.x0 - a) < 0.2 and abs(l.x1 - b) < 0.2][0]
        wh = sorted(l.y0 for l in L if l.x0 > a + 3 and l.x1 < b - 3 and abs((l.x0 + l.x1) / 2 - (a + b) / 2) < 0.5)
        row.append({"median": round(f(med.y0), 2), "low": round(f(wh[-1]), 2), "high": round(f(wh[0]), 2)})
    out["fig10"][k] = row

json.dump(out, open(os.path.join(here, "paper_vector_values.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("ok", {k: (len(v) if hasattr(v, "__len__") else v) for k, v in out.items()})
