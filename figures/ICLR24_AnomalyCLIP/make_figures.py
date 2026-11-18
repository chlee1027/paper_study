# -*- coding: utf-8 -*-
r"""AnomalyCLIP 노트의 그림을 만들고, 노트가 인용하는 다시 계산한 값을 찍는다.

표준 라이브러리만 쓴다. 값은 같은 폴더의 tables_anomalyclip.json(read_tables.py 가 PDF 에서 읽은 것)과
data_anomalyclip.py(그림 5 · 8 막대 글자, 표 6, 설정), 그리고 WinCLIP 노트 그림 폴더의 appendix_classwise.json 이다.

  python make_figures.py

찍는 것(셈 1 \~ 14)과 그림 아홉.
"""
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from data_anomalyclip import CLIP_L14_336, FIG5_GAIN, FIG8, MEDICAL_TUNE, SETTINGS, TABLE6  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open(os.path.join(HERE, "tables_anomalyclip.json"), encoding="utf-8") as f:
    J = json.load(f)
with open(os.path.join(HERE, "..", "CVPR23_WinCLIP", "appendix_classwise.json"), encoding="utf-8") as f:
    WCW = json.load(f)

M = J["table1"]["methods"]
IND = list(J["table1"]["image_auroc_ap"])
MED_I = list(J["table2"]["image_auroc_ap"])
MED_P = list(J["table2"]["pixel_auroc_pro"])
AC = M.index("AnomalyCLIP")


def head(s):
    print("\n" + "=" * 8, s)


# ---------------------------------------------------------------- 셈 1 지도 식이 S_a 하나로 준다
head("셈 1. 추론 지도 식: 두 부류 소프트맥스면 S_n + S_a = 1 이라 (1/2)(1 - S_n) + (1/2) S_a = S_a")
for sa in (0.10, 0.70, 0.95):
    sn = 1 - sa
    print(f"  S_a={sa:.2f} S_n={sn:.2f} -> 0.5*(1-S_n)+0.5*S_a = {0.5 * (1 - sn) + 0.5 * sa:.2f}")

# ---------------------------------------------------------------- 셈 2 배우는 값의 수, 토큰 수, 걸음 수
head("셈 2. 배우는 값 · 조각 수 · 걸음 수 (내 셈, 가정은 노트에)")
w = CLIP_L14_336["text_width"]
prompt = 2 * SETTINGS["prompt_len_E"] * w
deep = SETTINGS["text_deep_layers"] * SETTINGS["text_deep_len"] * w
print(f"  글 프롬프트 2 x {SETTINGS['prompt_len_E']} x {w} = {prompt:,}")
print(f"  글 부호기 층 토큰 {SETTINGS['text_deep_layers']} x {SETTINGS['text_deep_len']} x {w} = {deep:,} (두 프롬프트가 나눠 쓴다고 가정)")
print(f"  합 {prompt + deep:,}")
g = SETTINGS["input"] // SETTINGS["patch"]
g0 = CLIP_L14_336["input"] // SETTINGS["patch"]
print(f"  입력 {SETTINGS['input']} / 조각 {SETTINGS['patch']} = {g} -> 조각 {g * g:,} 개 (사전학습 336 이면 {g0} x {g0} = {g0 * g0})")
for ds in ("MVTec AD", "VisA"):
    n = TABLE6[ds][1] + TABLE6[ds][2]
    steps = math.ceil(n / SETTINGS["batch"])
    print(f"  {ds} 시험 집합 {n:,} 장 / 묶음 {SETTINGS['batch']} = {steps} 걸음 x {SETTINGS['epochs']} 에폭 = {steps * SETTINGS['epochs']:,} 걸음")
print(f"  의료 배움 데이터 {MEDICAL_TUNE[0]} + {MEDICAL_TUNE[1]} = {sum(MEDICAL_TUNE)} 장")

# ---------------------------------------------------------------- 셈 3 표 1 · 2 승수와 차
head("셈 3. 표 1 · 2 에서 AnomalyCLIP 이 1 위인 칸, 2 위와의 차")


def table_rank(tab, sets, levels):
    wins, rows = 0, []
    for lvl in levels:
        for ds in sets:
            if ds not in tab[lvl]:
                continue
            v = tab[lvl][ds]
            for k in (0, 1):
                others = [(x[k], M[i]) for i, x in enumerate(v) if x is not None and i != AC]
                best = max(others)
                d = v[AC][k] - best[0]
                wins += d > 0
                rows.append((lvl, ds, k, v[AC][k], best, round(d, 1)))
    return wins, rows


for name, tab, sets in [("표 1", J["table1"], IND), ("표 2", J["table2"], MED_I + MED_P)]:
    wins, rows = table_rank(tab, sets, ["image_auroc_ap", "pixel_auroc_pro"])
    print(f"  {name}: {wins} / {len(rows)} 칸 1 위")
    for r in sorted(rows, key=lambda r: r[5])[:6]:
        print("    차가 작은 칸", r)

# ---------------------------------------------------------------- 셈 4 우연 아래 값
head("셈 4. AUROC 50 아래 칸 (거꾸로 정렬)")
for name, tab, sets in [("표 1", J["table1"], IND), ("표 2", J["table2"], MED_I + MED_P)]:
    for lvl in ("image_auroc_ap", "pixel_auroc_pro"):
        for ds in sets:
            if ds not in tab[lvl]:
                continue
            for i, x in enumerate(tab[lvl][ds]):
                if x is not None and x[0] < 50:
                    print(f"  {name} {lvl[:5]} {ds:14s} {M[i]:8s} {x[0]:5.1f} (뒤집으면 {100 - x[0]:.1f})")
CW = J["classwise"]
for t in ("table10", "table14", "table18"):
    rows = {k: v for k, v in CW[t]["rows"].items() if k != "Mean"}
    for meth in ("CLIP", "CLIP-AC", "CoOp"):
        i = M.index(meth)
        below = sorted((v[i], k) for k, v in rows.items() if v[i] < 50)
        print(f"  {t} {CW[t]['data']} 화소 AUROC {meth}: {len(below)} / {len(rows)} 부류 50 아래, 가장 낮은 셋 {below[:3]}")
tex = ["Carpet", "Grid", "Leather", "Tile", "Wood"]
r10 = CW["table10"]["rows"]
print("  표 10 CLIP 질감 다섯 평균", round(st.mean(r10[c][0] for c in tex), 2),
      "물체 열 평균", round(st.mean(v[0] for k, v in r10.items() if k not in tex + ["Mean"]), 2))

# ---------------------------------------------------------------- 셈 5 표 4 와 그림 5 · 8
head("셈 5. 표 4 쌓기와 그림 5 (object 의 몫)")
t4 = J["table4"]["rows"]
steps = list(t4)
for c, col in enumerate(J["table4"]["columns"]):
    seq = [t4[s][c][0] for s in steps]
    inc = [round(seq[k + 1] - seq[k], 1) for k in range(len(seq) - 1)]
    print(f"  {col:26s} AUROC {seq} 늘어남 {inc}")
print("  그림 5 (object - 물체 이름), 이미지 AUROC · AP · 화소 AUROC · AUPRO:")
allg = [x for v in FIG5_GAIN.values() for x in v]
for ds, v in FIG5_GAIN.items():
    print(f"    {ds:14s} {v}")
print(f"  28 값: 최소 {min(allg)} 최대 {max(allg)} 평균 {st.mean(allg):.2f}, 0.5 아래 {sum(x < 0.5 for x in allg)} 개, 1.0 넘음 {sum(x > 1.0 for x in allg)} 개")
for ds, k, c in [("MVTec AD", 0, 1), ("VisA", 0, 3), ("MVTec AD", 2, 0), ("VisA", 2, 2)]:
    lab = ["이미지 AUROC", "AP", "화소 AUROC", "AUPRO"][k]
    t2 = t4["+T2"][c][0] - t4["+T1"][c][0]
    print(f"  {ds} {lab}: T2 늘어남 {t2:.1f} 가운데 object 몫 {FIG5_GAIN[ds][k]} = {FIG5_GAIN[ds][k] / t2 * 100:.1f}%")
t1i = J["table1"]["image_auroc_ap"]
for ds in ("MVTec AD", "VisA"):
    aware = t1i[ds][AC][0] - FIG5_GAIN[ds][0]
    print(f"  {ds} 이미지 AUROC: AnomalyCLIP {t1i[ds][AC][0]} · 물체 이름으로 배운 판 {aware:.1f}(내 뺄셈) · "
          f"object 로 배우고 이름을 넣은 판(그림 8) {FIG8['image AUROC'][ds][1]} · CoOp {t1i[ds][M.index('CoOp')][0]}")

# ---------------------------------------------------------------- 셈 6 표 5
head("셈 6. 표 5 (지역 · 전역 손실)")
for r in J["table5"]["rows"]:
    print(f"  local={r['local']!s:5s} global={r['global']!s:5s} {r['values']}")
both = J["table5"]["rows"][3]["values"]
for r in J["table5"]["rows"][1:3]:
    d = [[round(r["values"][c][k] - both[c][k], 1) for k in (0, 1)] for c in range(4)]
    print(f"  ({'지역만' if r['local'] else '전역만'}) - 둘 다: {d}")
print("  둘 다 끈 줄 대 표 4 Base:", J["table5"]["rows"][0]["values"], t4["Base"])

# ---------------------------------------------------------------- 셈 7 그림 6
head("셈 7. 그림 6 (벡터 경로로 읽은 DPAM 셋)")
F6 = J["fig6"]
cnt = {"V-V": 0, "Q-Q": 0, "K-K": 0}
for metric, d in F6.items():
    print(f"  {metric}")
    for ds in IND:
        vals = {k: d[k][ds] for k in d}
        top = max(vals, key=vals.get)
        cnt[top] += 1
        print(f"    {ds:14s} " + "  ".join(f"{k} {v:5.1f}" for k, v in vals.items()) + f"   1 위 {top}")
print("  28 칸 1 위 수", cnt)
for k in ("Q-Q", "K-K"):
    for metric in F6:
        diffs = [round(F6[metric][k][ds] - F6[metric]["V-V"][ds], 1) for ds in IND]
        print(f"  {k} - V-V {metric:12s} {diffs} 평균 {st.mean(diffs):+.2f}")

# ---------------------------------------------------------------- 셈 8 그림 7
head("셈 8. 그림 7 (벡터로 읽은 하이퍼파라미터 훑기, 기본값 E=12 · M=9 · L=4 · N=4)")
DEF = {"E": "12", "M": "9", "L": "4", "N": "4"}
for key, d in J["fig7"].items():
    p = key.split()[0]
    for ds, line in d.items():
        vals = {x: round(v, 1) for x, v in line.items()}
        best = max(vals.values())
        print(f"  {key:8s} {ds:9s} {vals}  기본값 {vals[DEF[p]]} 최댓값 {best} 폭 {best - min(vals.values()):.1f}"
              + ("  <- 기본값이 최댓값" if vals[DEF[p]] == best else ""))

# ---------------------------------------------------------------- 셈 9 표 3 대 표 2
head("셈 9. 표 3 (ColonDB 로 배운 판) - 표 2 (MVTec AD 로 배운 판)")
t3 = J["table3"]["rows"]
t2 = {**J["table2"]["image_auroc_ap"], **J["table2"]["pixel_auroc_pro"]}
for ds, (vand, ac) in t3.items():
    dv = [round(vand[k] - t2[ds][M.index("VAND")][k], 1) for k in (0, 1)]
    da = [round(ac[k] - t2[ds][AC][k], 1) for k in (0, 1)]
    print(f"  {ds:13s} VAND {dv}  AnomalyCLIP {da}")

# ---------------------------------------------------------------- 셈 10 표 7
head("셈 10. 표 7 (전체 정상 이미지로 배운 PatchCore · RD4AD 와의 차)")
for lvl in ("image_auroc_ap", "pixel_auroc_pro"):
    for ds, v in J["table7"][lvl].items():
        best = [max(v[1][k], v[2][k]) for k in (0, 1)]
        print(f"  {lvl[:5]} {ds:9s} AnomalyCLIP {v[0]}  둘 중 높은 값 {best}  차 {[round(v[0][k] - best[k], 1) for k in (0, 1)]}")

# ---------------------------------------------------------------- 셈 11 표 8 · 9
head("셈 11. 표 8 · 9 (damaged 대신 다른 낱말)")
for name, tab in (("표 8", J["table8"]), ("표 9", J["table9"])):
    top, n, spread = 0, 0, []
    for lvl in ("image_auroc_ap", "pixel_auroc_pro"):
        for ds, v in tab[lvl].items():
            for k in (0, 1):
                col = [x[k] for x in v]
                n += 1
                top += col[0] == max(col)
                spread.append((round(max(col) - min(col), 1), ds, lvl[:5], k, col))
    spread.sort(reverse=True)
    print(f"  {name}: damaged 가 최댓값(같은 값 포함)인 칸 {top} / {n}")
    for s in spread[:5]:
        print("    폭이 큰 칸", s)

# ---------------------------------------------------------------- 셈 12 부류별 표
head("셈 12. 부류별 표 10 \\~ 21: Mean 행 대조, AnomalyCLIP 1 위 부류 수")
for t, d in CW.items():
    if t == "methods":
        continue
    rows = {k: v for k, v in d["rows"].items() if k != "Mean"}
    mean = d["rows"]["Mean"]
    gap = [round(st.mean(v[i] for v in rows.values()) - mean[i], 2) for i in range(6)]
    wins = sum(v[AC] > max(v[i] for i in range(6) if i != AC) for v in rows.values())
    ties = sum(v[AC] == max(v[i] for i in range(6) if i != AC) for v in rows.values())
    print(f"  {t} {d['data']:8s} {d['metric']:12s} 부류 평균 - Mean {gap}  AnomalyCLIP 1 위 {wins} / {len(rows)} (같음 {ties})")


def norm(s):
    return s.lower().replace(" ", "").replace("_", "")


head("셈 12b. 이 편 부록의 WinCLIP 열 대 WinCLIP 원문 보충 자료의 0 장 열")
PAIRS = {"table10": "table13", "table11": "table14", "table12": "table10", "table13": "table11",
         "table14": "table19", "table15": "table20", "table16": "table16", "table17": "table17"}
wi = M.index("WinCLIP")
for a, b in PAIRS.items():
    mine = {norm(k): v[wi] for k, v in CW[a]["rows"].items()}
    theirs = {norm(k): v[0][0] for k, v in WCW[b]["rows"].items()}
    diff = [(k, mine[k], theirs[k]) for k in theirs if k in mine and abs(mine[k] - theirs[k]) > 0.05]
    miss = [k for k in theirs if k not in mine]
    print(f"  {a} ({CW[a]['data']} {CW[a]['metric']}) 대 WinCLIP {b}: 어긋남 {len(diff)} {diff[:4]} 이름 못 맞춘 것 {miss}")

# ---------------------------------------------------------------- 셈 13 같은 짝이 두 칸에
head("셈 13. 표 1 · 2 안에서 (AUROC, 둘째 지표) 짝이 통째로 같은 두 칸")
seen = {}
for name, tab in (("표 1", J["table1"]), ("표 2", J["table2"])):
    for lvl in ("image_auroc_ap", "pixel_auroc_pro"):
        for ds, v in tab[lvl].items():
            for i, x in enumerate(v):
                if x is None:
                    continue
                seen.setdefault(tuple(x), []).append(f"{name} {lvl[:5]} {ds} {M[i]}")
for k, v in seen.items():
    if len(v) > 1:
        print(" ", k, v)

# ---------------------------------------------------------------- 셈 14 표 6 의 이상 비율 (AP 의 우연 기준)
head("셈 14. 표 6 의 이상 비율 = 무작위 순위의 AP 기댓값")
for ds in IND + MED_I:
    c, n, a = TABLE6[ds]
    print(f"  {ds:14s} 이상 {a} / {n + a} = {a / (n + a) * 100:.1f}%")
for ds in ("BrainMRI", "COVID-19", "SDD"):
    c, n, a = TABLE6[ds]
    src = J["table2"]["image_auroc_ap"] if ds in MED_I else J["table1"]["image_auroc_ap"]
    for i, x in enumerate(src[ds]):
        if x and x[1] < a / (n + a) * 100:
            print(f"    {ds} {M[i]} AP {x[1]} < 이상 비율 {a / (n + a) * 100:.1f} (AUROC {x[0]})")


# ================================================================ 그림
FONT = "'Malgun Gothic','Noto Sans KR',sans-serif"
INK, MUTE, LINE = "#222222", "#666666", "#cccccc"
A, B, Y, D = "#2f6db3", "#c8553d", "#d9a21b", "#8a8a8a"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(x, y, s, size=12, fill=INK, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" font-family="{FONT}">{esc(s)}</text>')


def R(x, y, w, h, fill, stroke="none", rx=0):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'


def L(x1, y1, x2, y2, stroke=LINE, width=1, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>'


def PL(pts, stroke, width=2, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{width}"{d}/>'


def CIRC(x, y, r, fill, stroke="#ffffff", sw=2):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def ARROW(x1, y1, x2, y2, color=MUTE):
    ang = math.atan2(y2 - y1, x2 - x1)
    a1 = (x2 - 7 * math.cos(ang - 0.4), y2 - 7 * math.sin(ang - 0.4))
    a2 = (x2 - 7 * math.cos(ang + 0.4), y2 - 7 * math.sin(ang + 0.4))
    return (L(x1, y1, x2, y2, color, 1.5) +
            f'<polygon points="{x2:.1f},{y2:.1f} {a1[0]:.1f},{a1[1]:.1f} {a2[0]:.1f},{a2[1]:.1f}" fill="{color}"/>')


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote", name)


def textw(s, size=11):
    return sum(size * (0.62 if ord(ch) < 128 else 1.0) for ch in s)


head("그림")

# ---- 그림 1: 프롬프트 설계 넷
b = [T(20, 28, "정상 · 결함을 적는 글: 네 설계 (상자 하나가 낱말 묶음 하나)", 15, weight="bold")]
rows = [
    ("CLIP (표 1 의 비교 상대, 부록 A.2)", "손으로 쓴 두 문장. 배우는 값 0",
     [[("A photo of a normal", "g"), ("[cls]", "y")], [("A photo of an anomalous", "g"), ("[cls]", "y")]]),
    ("WinCLIP", "상태 낱말 11 x 문장 틀 22 = 242 문장을 쪽마다 평균. 배우는 값 0",
     [[("문장 틀 22", "g"), ("정상 상태 7 (flawless 등)", "g"), ("[cls]", "y")],
      [("문장 틀 22", "g"), ("결함 상태 4 (damaged 등)", "g"), ("[cls]", "y")]]),
    ("CoOp (부록 A.2 에서 이 과제로 바꾼 판)", "배우는 낱말 N 개 + 상태 낱말 + 물체 이름",
     [[("V1 ... VN", "a"), ("normal", "g"), ("[cls]", "y")], [("V1 ... VN", "a"), ("anomalous", "g"), ("[cls]", "y")]]),
    ("AnomalyCLIP", "배우는 낱말 12 개씩 + 물체 이름 대신 object. 그리고 글 부호기 1 ~ 9 층에 층마다 배우는 토큰 4 개",
     [[("V1 ... V12", "a"), ("object", "b")], [("W1 ... W12", "a"), ("damaged", "g"), ("object", "b")]]),
]
FILL = {"a": A, "b": B, "y": Y, "g": "#e6e6e6"}
y = 62
for name, note, pr in rows:
    b.append(T(20, y, name, 13, weight="bold"))
    b.append(T(20, y + 18, note, 11, MUTE))
    yy = y + 30
    for line in pr:
        x = 40
        for text, c in line:
            wbox = textw(text) + 16
            b.append(R(x, yy, wbox, 22, FILL[c], rx=3))
            b.append(T(x + wbox / 2, yy + 15, text, 11, "#ffffff" if c in "ab" else INK, "middle"))
            x += wbox + 6
        yy += 28
    y = yy + 22
for i, (c, lab) in enumerate((("a", "배우는 낱말 임베딩"), ("b", "물체 이름을 막은 자리"),
                               ("y", "데이터셋이 주는 물체 이름"), ("g", "손으로 정한 낱말"))):
    b.append(R(40 + i * 175, y - 8, 14, 14, FILL[c], rx=2))
    b.append(T(60 + i * 175, y + 4, lab, 11))
save("fig01_prompt_designs.svg", 760, y + 22, b)

# ---- 그림 2: 이 편의 자리
cols = ["CLIP (2021)", "WinCLIP (2023)", "AnomalyCLIP (2024)"]
rowsd = [
    ("판정에 쓰는 학습", "없음 (얼린 CLIP)", "없음 (얼린 CLIP)", "보조 데이터 하나로 프롬프트만 배움"),
    ("보조 데이터", "-", "-", "MVTec AD 시험 집합 1,725 장 + 마스크"),
    ("백본 · 입력 화소", "ViT-L/14@336px · 336", "ViT-B/16+ (LAION) · 240", "ViT-L/14@336px · 518"),
    ("글", "클래스 이름 문장", "손으로 쓴 242 문장", "배우는 두 프롬프트"),
    ("조각 단위 점수", "-", "창으로 가려 여러 번 순전파", "중간 층 넷의 조각 토큰 + DPAM"),
    ("MVTec AD 분류 AUROC", "74.1 (이 편 표 1)", "91.8", "91.5"),
    ("MVTec AD 분할 pAUROC", "38.4 (이 편 표 1)", "85.1", "91.1"),
]
W, x0, cw = 900, 180, 240
b = [T(20, 28, "CLIP → WinCLIP → AnomalyCLIP: 바뀐 것", 15, weight="bold")]
for i, c in enumerate(cols):
    b.append(R(x0 + i * cw, 44, cw - 8, 26, [D, A, B][i], rx=4))
    b.append(T(x0 + i * cw + (cw - 8) / 2, 62, c, 12, "#ffffff", "middle", "bold"))
for j, r in enumerate(rowsd):
    yy = 94 + j * 30
    b.append(L(20, yy + 10, W - 20, yy + 10, "#eeeeee"))
    b.append(T(20, yy, r[0], 11, MUTE))
    for i in range(3):
        b.append(T(x0 + i * cw + 4, yy, r[i + 1], 11, INK, weight="bold" if j >= 5 and i == 2 else "normal"))
b.append(T(20, 94 + len(rowsd) * 30 + 4,
           "백본이 칸마다 다르다. WinCLIP 값은 원문 값을 옮긴 것(표 1 의 †)이고, 표 1 의 CLIP 줄이 어느 백본인지는 이 편에 적혀 있지 않다.", 11, MUTE))
save("fig02_lineage.svg", W, 94 + len(rowsd) * 30 + 22, b)

# ---- 그림 3: 표 4 의 T2 오름과 그림 5 의 object 몫
items = [("MVTec AD 이미지 AUROC", 1, 0), ("VisA 이미지 AUROC", 3, 0), ("MVTec AD 화소 AUROC", 0, 2), ("VisA 화소 AUROC", 2, 2)]
W = 800
b = [T(20, 28, "표 4 의 +T2 오름 가운데 「물체 이름 대신 object」 의 몫 (그림 5)", 15, weight="bold"),
     T(20, 48, "옅은 막대 전체 = +T1 → +T2 의 오름(표 4). 진한 부분 = object 판 − 물체 이름 판(그림 5). 두 그림이 같은 실행인지는 적혀 있지 않다", 11, MUTE)]
sx = 11
for i, (lab, c, k) in enumerate(items):
    ds = "MVTec AD" if "MVTec" in lab else "VisA"
    tot = t4["+T2"][c][0] - t4["+T1"][c][0]
    part = FIG5_GAIN[ds][k]
    yy = 76 + i * 50
    b.append(T(20, yy + 16, lab, 12))
    b.append(R(190, yy, tot * sx, 24, "#d6e2f2"))
    b.append(R(190, yy, max(part * sx, 1), 24, A))
    b.append(T(190 + tot * sx + 6, yy + 16, f"{tot:.1f} 점 중 {part} 점 ({part / tot * 100:.1f}%)", 11))
for v in range(0, 45, 10):
    b.append(L(190 + v * sx, 70, 190 + v * sx, 276, "#eeeeee"))
    b.append(T(190 + v * sx, 290, f"{v}", 10, MUTE, "middle"))
save("fig03_t2_vs_object.svg", W, 300, b)

# ---- 그림 4: 표 10 부류별 화소 AUROC, 우연 아래
rows10 = {k: v for k, v in CW["table10"]["rows"].items() if k != "Mean"}
order = tex + [k for k in rows10 if k not in tex]
W, H = 860, 360
b = [T(20, 28, "MVTec AD 부류별 화소 AUROC (부록 표 10): 50 아래는 순위가 거꾸로 선 것", 15, weight="bold")]
px0, py0, pw, ph = 60, 50, 780, 250
yv = lambda v: py0 + ph - v / 100 * ph
for v in range(0, 101, 25):
    b.append(L(px0, yv(v), px0 + pw, yv(v), "#eeeeee"))
    b.append(T(px0 - 6, yv(v) + 4, v, 10, MUTE, "end"))
b.append(L(px0, yv(50), px0 + pw, yv(50), INK, 1.2, "5,4"))
b.append(T(px0 + pw / len(order) * 5 + 4, yv(50) - 4, "우연 50", 10, INK))
step = pw / len(order)
for i, c in enumerate(order):
    x = px0 + step * (i + 0.5)
    for meth, colr, dx in (("CLIP", D, -10), ("CoOp", Y, 0), ("AnomalyCLIP", A, 10)):
        v = rows10[c][M.index(meth)]
        b.append(CIRC(x + dx, yv(v), 4.5, colr, "#ffffff", 1))
    b.append(T(x, py0 + ph + 16, c, 10, B if c in tex else INK, "middle"))
b.append(L(px0 + step * 5, py0, px0 + step * 5, py0 + ph, MUTE, 1, "2,3"))
b.append(T(px0 + step * 2.5, yv(64), "질감 다섯", 11, B, "middle"))
for i, (meth, colr) in enumerate((("CLIP", D), ("CoOp", Y), ("AnomalyCLIP", A))):
    b.append(CIRC(px0 + 10 + i * 130, H - 18, 5, colr, "#ffffff", 1))
    b.append(T(px0 + 20 + i * 130, H - 14, meth, 11))
b.append(T(px0 + 400, H - 14, "CLIP 질감 다섯 평균 25.14 · 물체 열 평균 44.97 (내 평균)", 11, MUTE))
save("fig04_below_chance_classwise.svg", W, H, b)

# ---- 그림 5: 그림 6 (DPAM 셋) 을 V-V 와의 차로
W, H = 920, 310
b = [T(20, 28, "그림 6 의 레이더를 벡터 경로로 읽어 V-V 와의 차로 다시 그림", 15, weight="bold"),
     T(20, 46, "0 위는 V-V 보다 높은 칸. 28 칸 중 V-V 17 · K-K 7 · Q-Q 4 칸에서 1 위", 11, MUTE)]
panels = ["pixel AUROC", "PRO", "image AUROC", "image AP"]
labs = {"pixel AUROC": "화소 AUROC", "PRO": "AUPRO", "image AUROC": "이미지 AUROC", "image AP": "AP"}
pw, ph, gy = 196, 190, 78
short = ["MV", "Vi", "MP", "BT", "SD", "DA", "DT"]
for p, metric in enumerate(panels):
    ox = 50 + p * 218
    yv = lambda v: gy + ph / 2 - v / 12 * (ph / 2)
    b.append(T(ox + pw / 2, gy - 8, labs[metric], 12, INK, "middle", "bold"))
    for v in (-12, -6, 0, 6, 12):
        b.append(L(ox, yv(v), ox + pw, yv(v), INK if v == 0 else "#eeeeee"))
        if p == 0:
            b.append(T(ox - 4, yv(v) + 4, f"{v:+d}" if v else "0", 10, MUTE, "end"))
    for i, ds in enumerate(IND):
        x = ox + (i + 0.5) * pw / 7
        for k, colr, dx in (("Q-Q", B, -5), ("K-K", Y, 5)):
            dv = F6[metric][k][ds] - F6[metric]["V-V"][ds]
            b.append(CIRC(x + dx, yv(dv), 4.5, colr, "#ffffff", 1))
        b.append(T(x, gy + ph + 14, short[i], 10, MUTE, "middle"))
b.append(CIRC(50, H - 16, 5, B, "#ffffff", 1)); b.append(T(60, H - 12, "Q-Q − V-V", 11))
b.append(CIRC(160, H - 16, 5, Y, "#ffffff", 1)); b.append(T(170, H - 12, "K-K − V-V", 11))
b.append(T(280, H - 12, "MV MVTec AD · Vi VisA · MP MPDD · BT BTAD · SD SDD · DA DAGM · DT DTD-Synthetic", 10, MUTE))
save("fig05_fig6_dpam_diff.svg", W, H, b)

# ---- 그림 6: 그림 7 의 훑기 넷
W, H = 900, 310
b = [T(20, 28, "그림 7 의 하이퍼파라미터 훑기를 벡터로 읽은 값 (AUPRO, 큰 동그라미 = 기본값)", 15, weight="bold"),
     T(20, 46, "AUPRO · AP 16 줄 모두 기본값이 그 줄의 최댓값이다. 값은 MVTec AD · VisA 시험 집합에서 잰 것이다", 11, MUTE)]
names = [("E", "글 프롬프트 길이 E"), ("M", "글 층 토큰 깊이 M"), ("L", "글 층 토큰 길이 L"), ("N", "쓴 시각 층 수 N")]
pw, ph, gy = 180, 170, 84
for p, (key, title) in enumerate(names):
    ox = 50 + p * 215
    d = J["fig7"][f"{key} AUPRO"]
    xs = [int(x) for x in d["MVTec AD"]]
    lo, hi = 76, 88
    xv = lambda x: ox + (x - min(xs)) / (max(xs) - min(xs)) * pw
    yv = lambda v: gy + ph - (v - lo) / (hi - lo) * ph
    b.append(T(ox + pw / 2, gy - 10, title, 12, INK, "middle", "bold"))
    for v in range(lo, hi + 1, 4):
        b.append(L(ox, yv(v), ox + pw, yv(v), "#eeeeee"))
        b.append(T(ox - 4, yv(v) + 4, v, 10, MUTE, "end"))
    for ds, colr in (("MVTec AD", A), ("VisA", B)):
        pts = [(xv(int(x)), yv(v)) for x, v in d[ds].items()]
        b.append(PL(pts, colr))
        for (x, v), (px, py) in zip(d[ds].items(), pts):
            big = x == DEF[key]
            b.append(CIRC(px, py, 6 if big else 3, "#ffffff" if big else colr, colr, 2))
    for x in xs:
        b.append(T(xv(x), gy + ph + 14, x, 10, MUTE, "middle"))
    if key == "M":
        b.append(T(xv(8), yv(77.2), "본문: 「M 이 9 일 때 떨어진다」", 10, B, "middle"))
b.append(L(50, H - 16, 70, H - 16, A, 2)); b.append(T(76, H - 12, "MVTec AD", 11))
b.append(L(160, H - 16, 180, H - 16, B, 2)); b.append(T(186, H - 12, "VisA", 11))
save("fig06_fig7_sweeps.svg", W, H, b)

# ---- 그림 7: 표 7 전체 학습 방법과의 차
W, H = 780, 310
b = [T(20, 28, "표 7: AnomalyCLIP − (PatchCore 와 RD4AD 중 높은 값)", 15, weight="bold"),
     T(20, 46, "원문은 「comparable」 이라 적는다. 0 위는 DAGM 의 이미지 지표뿐이다", 11, MUTE)]
dsets = list(J["table7"]["image_auroc_ap"])
px0, gy, ph = 80, 70, 190
yv = lambda v: gy + (12 - v) / 30 * ph
for v in (-18, -12, -6, 0, 6, 12):
    b.append(L(px0, yv(v), W - 20, yv(v), INK if v == 0 else "#eeeeee"))
    b.append(T(px0 - 6, yv(v) + 4, f"{v:+d}" if v else "0", 10, MUTE, "end"))
step = (W - 20 - px0) / len(dsets)
for i, ds in enumerate(dsets):
    x = px0 + step * i + step / 2
    for lvl, idx, colr, dx in (("image_auroc_ap", 0, A, -26), ("pixel_auroc_pro", 0, B, -8), ("pixel_auroc_pro", 1, Y, 10)):
        v = J["table7"][lvl][ds]
        dv = v[0][idx] - max(v[1][idx], v[2][idx])
        y0, y1 = sorted((yv(0), yv(dv)))
        b.append(R(x + dx, y0, 16, max(y1 - y0, 0.8), colr))
    b.append(T(x, gy + ph + 16, ds, 11, INK, "middle"))
for i, (lab, colr) in enumerate((("이미지 AUROC", A), ("화소 AUROC", B), ("PRO", Y))):
    b.append(R(px0 + i * 130, H - 26, 12, 12, colr))
    b.append(T(px0 + 18 + i * 130, H - 16, lab, 11))
save("fig07_table7_fullshot_gap.svg", W, H, b)

# ---- 그림 8: 표 3 대 표 2
W, H = 800, 340
b = [T(20, 28, "의료 데이터(ColonDB)로 배우면: 표 2(MVTec AD 로 배움) → 표 3, AUROC", 15, weight="bold"),
     T(20, 46, "VAND 의 분류 넷은 두 표에서 같은 값이다. 본문이 적지 않은 내림: AnomalyCLIP TN3K −2.3", 11, MUTE)]
dsets = list(t3)
px0, gy, ph = 70, 70, 210
yv = lambda v: gy + (100 - v) / 90 * ph
for v in range(10, 101, 15):
    b.append(L(px0, yv(v), W - 20, yv(v), "#eeeeee"))
    b.append(T(px0 - 6, yv(v) + 4, v, 10, MUTE, "end"))
step = (W - 20 - px0) / len(dsets)
for i, ds in enumerate(dsets):
    x = px0 + step * i + step / 2
    for meth, colr, dx in (("VAND", Y, -10), ("AnomalyCLIP", A, 10)):
        a0 = t2[ds][M.index(meth)][0]
        a1 = t3[ds][0 if meth == "VAND" else 1][0]
        if abs(a1 - a0) < 0.05:
            b.append(CIRC(x + dx, yv(a0), 4, colr, "#ffffff", 1))
        else:
            b.append(ARROW(x + dx, yv(a0), x + dx, yv(a1), colr))
            b.append(CIRC(x + dx, yv(a0), 3, "#ffffff", colr, 1.5))
    b.append(T(x, gy + ph + 16, ds.replace("CVC-", ""), 10, INK, "middle"))
b.append(L(px0 + step * 4, gy, px0 + step * 4, gy + ph, MUTE, 1, "2,3"))
b.append(T(px0 + step * 2, gy + 12, "분류", 11, MUTE, "middle"))
b.append(T(px0 + step * 6.5, gy + 12, "분할", 11, MUTE, "middle"))
b.append(R(px0, H - 26, 12, 12, Y)); b.append(T(px0 + 18, H - 16, "VAND", 11))
b.append(R(px0 + 100, H - 26, 12, 12, A))
b.append(T(px0 + 118, H - 16, "AnomalyCLIP (빈 동그라미 = 표 2, 화살 끝 = 표 3, 꽉 찬 동그라미 = 두 표가 같은 값)", 11))
save("fig08_table3_medical_shift.svg", W, H, b)

# ---- 그림 9: 부류별 AnomalyCLIP − WinCLIP (MVTec AD 이미지 AUROC · PRO)
r12, r11 = CW["table12"]["rows"], CW["table11"]["rows"]
cls = [k for k in r12 if k != "Mean"]
cls.sort(key=lambda c: r12[c][AC] - r12[c][wi])
d12 = [r12[c][AC] - r12[c][wi] for c in cls]
d11 = [r11[c][AC] - r11[c][wi] for c in cls]
W, H = 880, 340
b = [T(20, 28, "MVTec AD 부류별 AnomalyCLIP − WinCLIP (부록 표 12 · 11)", 15, weight="bold"),
     T(20, 46, f"평균 차: 이미지 AUROC {st.mean(d12):+.2f} · PRO {st.mean(d11):+.2f}. "
               f"이미지 AUROC 는 15 부류 중 {sum(x < 0 for x in d12)} 부류에서 WinCLIP 이 높고 {sum(x == 0 for x in d12)} 부류가 같다", 11, MUTE)]
px0, gy, ph = 60, 74, 200
yv = lambda v: gy + (40 - v) / 70 * ph
for v in range(-30, 41, 10):
    b.append(L(px0, yv(v), W - 20, yv(v), INK if v == 0 else "#eeeeee"))
    b.append(T(px0 - 6, yv(v) + 4, f"{v:+d}" if v else "0", 10, MUTE, "end"))
step = (W - 20 - px0) / len(cls)
for i, c in enumerate(cls):
    x = px0 + step * i + step / 2
    for dv, colr, dx in ((d12[i], A, -9), (d11[i], Y, 1)):
        y0, y1 = sorted((yv(0), yv(dv)))
        b.append(R(x + dx, y0, 8, max(y1 - y0, 0.8), colr))
    b.append(T(x, gy + ph + 14, c, 9, B if c in tex else INK, "middle"))
b.append(R(px0, H - 26, 12, 12, A)); b.append(T(px0 + 18, H - 16, "이미지 AUROC (표 12)", 11))
b.append(R(px0 + 170, H - 26, 12, 12, Y)); b.append(T(px0 + 188, H - 16, "화소 PRO (표 11)", 11))
b.append(T(px0 + 330, H - 16, "붉은 이름 = 질감 부류", 11, B))
save("fig09_classwise_vs_winclip.svg", W, H, b)

head("그림 9 에 쓴 값")
print("  이미지 AUROC 차 평균", round(st.mean(d12), 2), "WinCLIP 이 높은 부류", sum(x < 0 for x in d12), "같은", sum(x == 0 for x in d12))
print("  PRO 차 평균", round(st.mean(d11), 2), "WinCLIP 이 높은 부류", sum(x < 0 for x in d11), [c for c, x in zip(cls, d11) if x < 0])
print("  이미지 AUROC 차 작은 셋 · 큰 셋", [(round(x, 1), c) for x, c in sorted(zip(d12, cls))[:3]],
      [(round(x, 1), c) for x, c in sorted(zip(d12, cls))[-3:]])
