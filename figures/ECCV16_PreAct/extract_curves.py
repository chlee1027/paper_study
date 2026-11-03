# -*- coding: utf-8 -*-
"""원문 PDF 의 곡선 그림(그림 1 오른쪽 · 그림 3 · 그림 6)에서 곡선 값을 꺼내 curves_data.py 로 적는다.

세 그림은 그림 파일이 아니라 PDF 안의 벡터 선(MATLAB 출력)이다. 그래서 눈금을 눈으로 읽지 않고
선의 좌표를 그대로 꺼낸다. 축 맞추기는 그림 틀(흰 사각형)의 왼쪽 = 0 반복, 가로 눈금 글자 '6' 의 가운데 = 6 x 10^4 반복,
틀 아래 = 시험 오차 0% · 학습 손실 0.002, 틀 위 = 시험 오차 20% · 학습 손실 2 (손실 축은 로그)다.
실선 = 시험 오차(오른쪽 축), 점선 = 학습 손실(왼쪽 축)이라는 것은 캡션의 말이다.

꺼낸 선은 500 반복 간격으로 선형 보간해 적는다. 축 밖의 값은 그림에서 틀에 붙어 잘려 있다 —
시험 오차 20% 위, 손실 2 위, 손실 0.002 아래는 그 값으로 적히고 make_figures.py 가 '잘림'으로 다룬다.

이 파일만 pymupdf 가 필요하다. make_figures.py 는 이 파일이 쓴 curves_data.py 를 읽고 표준 라이브러리만 쓴다.

  python extract_curves.py ../../papers/ECCV16_PreAct_Identity_Mappings_in_Deep_Residual_Networks.pdf
"""
import io, math, os, sys
import pymupdf

OUT = os.path.dirname(os.path.abspath(__file__))
PDF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "..", "..", "papers",
                                                        "ECCV16_PreAct_Identity_Mappings_in_Deep_Residual_Networks.pdf")
doc = pymupdf.open(PDF)

# (쪽 번호 0 부터, 틀 왼쪽 위 대략 좌표) -> 곡선 색별 이름. 색은 PDF 안의 선 색 그대로다.
YEL, BLU, GRN, MAG = (0.75, 0.75, 0.0), (0.0, 0.0, 1.0), (0.0, 0.5, 0.0), (0.75, 0.0, 0.75)
PANELS = [
    (1, (178, 40), {YEL: "r1001_orig", BLU: "r1001_pre"}),         # 그림 1 오른쪽
    (6, (51, 39), {YEL: "r110_base", GRN: "r110_scale"}),          # 그림 3 (a) 상수 배 (0.5, 0.5)
    (6, (222, 39), {YEL: "r110_base", GRN: "r110_exgate"}),        # 그림 3 (b) 배타 게이트 b=-6
    (6, (51, 173), {YEL: "r110_base", GRN: "r110_scgate"}),        # 그림 3 (c) 지름길만 게이트 b=0
    (6, (222, 173), {YEL: "r110_base", GRN: "r110_conv"}),         # 그림 3 (d) 1x1 합성곱 지름길
    (10, (51, 39), {YEL: "r110_base", MAG: "r110_bnafter"}),       # 그림 6 왼쪽 덧셈 뒤 BN
    (10, (223, 39), {YEL: "r164_orig", BLU: "r164_pre"}),          # 그림 6 오른쪽
]
STEP = 500
GRID = list(range(0, 68001, STEP))


def spans(pg):
    out = []
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                out.append((s["text"].strip(), pymupdf.Rect(s["bbox"])))
    return out


def interp(pts, t):
    if t < pts[0][0] or t > pts[-1][0]:
        return None
    lo, hi = 0, len(pts) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if pts[m][0] <= t:
            lo = m
        else:
            hi = m
    (x0, y0), (x1, y1) = pts[lo], pts[hi]
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (t - x0) / (x1 - x0)


curves = {}
first = {}   # 선이 처음 나타나는 반복(틀 위 끝에서 들어오는 자리)과 마지막 반복
for page, (fx, fy), names in PANELS:
    pg = doc[page]
    drs = pg.get_drawings()
    fr = [x["rect"] for x in drs if x["items"] and x["items"][0][0] == "re" and x.get("fill") == (1.0, 1.0, 1.0)
          and abs(x["rect"].x0 - fx) < 4 and abs(x["rect"].y0 - fy) < 4 and x["rect"].height > 60][0]
    six = [r for t, r in spans(pg) if t == "6" and fr.x0 < (r.x0 + r.x1) / 2 < fr.x1 + 5 and fr.y1 < r.y0 < fr.y1 + 8][0]
    x6 = (six.x0 + six.x1) / 2
    for x in drs:
        c = x.get("color")
        if c not in names or len(x["items"]) < 10:
            continue
        r = x["rect"]
        if not (fr.x0 - 12 <= r.x0 and r.x1 <= fr.x1 + 3 and fr.y0 - 3 <= r.y0 and r.y1 <= fr.y1 + 3):
            continue
        dashed = bool(x.get("dashes")) and x["dashes"].strip() != "[] 0"
        pts = []
        for it in x["items"]:
            if it[0] == "l":
                for p in it[1:3]:
                    t = (p.x - fr.x0) / (x6 - fr.x0) * 6e4
                    f = (fr.y1 - p.y) / (fr.y1 - fr.y0)
                    v = 10 ** (math.log10(0.002) + 3 * f) if dashed else 20 * f
                    pts.append((t, v))
        pts.sort()
        key = names[c] + ("_loss" if dashed else "_err")
        vals = [interp(pts, t) for t in GRID]
        if key in curves and curves[key] is not None:
            # 같은 기준선이 여러 판에 다시 그려져 있다. 판끼리 차이의 최댓값을 적어 둔다.
            diff = max(abs(a - b) / (b if dashed else 1) for a, b in zip(vals, curves[key]) if a is not None and b is not None)
            print("  %-18s 다시 나옴 (쪽 %d) — 앞 판과의 최대 차이 %.4g%s" % (key, page + 1, diff, " (비)" if dashed else " %p"))
            continue
        curves[key] = vals
        first[key] = (round(pts[0][0]), round(pts[-1][0]))
        print("  %-18s 쪽 %d  점 %4d  x %.0f ~ %.0f" % (key, page + 1, len(pts), pts[0][0], pts[-1][0]))

with io.open(os.path.join(OUT, "curves_data.py"), "w", encoding="utf-8") as f:
    f.write("# -*- coding: utf-8 -*-\n")
    f.write("# extract_curves.py 가 원문 PDF 의 벡터 선에서 꺼내 쓴 파일이다. 손으로 고치지 않는다.\n")
    f.write("# GRID = 반복 수(500 간격). 값 = 시험 오차 % (_err) 또는 학습 손실 (_loss). None = 그 반복에 선이 없다.\n")
    f.write("# 축 밖은 틀에 붙어 잘려 있다: 오차 >= 20, 손실 >= 2, 손실 <= 0.002 는 잘린 값이다.\n")
    f.write("GRID = %r\n" % GRID)
    f.write("CURVES = {\n")
    for k in sorted(curves):
        f.write("    %r: [%s],\n" % (k, ", ".join("None" if v is None else ("%.4g" % v) for v in curves[k])))
    f.write("}\n")
    f.write("# 선의 처음과 끝 반복 (500 간격으로 줄이기 전, 반올림). 시험 오차 선은 20% 위에서는 그려져 있지 않다.\n")
    f.write("SPAN = {\n")
    for k in sorted(first):
        f.write("    %r: %r,\n" % (k, first[k]))
    f.write("}\n")
print("curves_data.py 를 썼다 (곡선 %d 개)" % len(curves))
