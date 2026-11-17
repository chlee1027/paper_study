# -*- coding: utf-8 -*-
"""WinCLIP 노트의 그림을 만들고, 노트가 인용하는 다시 계산한 값을 찍는다.

표준 라이브러리만 쓰고 바깥 데이터를 읽지 않는다. 값은 같은 폴더 data_winclip.py 와 appendix_classwise.json 이다.

  python make_figures.py

찍는 것(셈 1~8): 조화 평균 예시, 프롬프트 수, 표 3 쌓기와 우연 아래 값, 창 수 · 토큰 수 · 표 8 시간 나누기,
표 1 · 4 의 문장 대조, 부류별 나누기, 부록 표의 평균 대조, 표 2 · 5 · 6 · 7 의 덧셈.
"""
import json
import math
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_winclip import *  # noqa: E402,F401,F403

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "'Malgun Gothic','Noto Sans KR',sans-serif"
INK, MUTE, LINE = "#222222", "#666666", "#cccccc"
A, B, Y, D = "#2f6db3", "#c8553d", "#d9a21b", "#8a8a8a"  # 색각 이상 대비 검사를 통과한 셋 + 회색

with open(os.path.join(OUT, "appendix_classwise.json"), encoding="utf-8") as f:
    CW = json.load(f)
COLS = CW["columns"]
TEXTURE = ["Carpet", "Grid", "Leather", "Tile", "Wood"]


def cw(table, cls, col):
    return CW[table]["rows"][cls][COLS.index(col)][0]


def classes(table):
    return [c for c in CW[table]["rows"] if c != "Mean"]


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


def CIRC(x, y, r, fill, stroke="#ffffff"):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def ARROW(x1, y1, x2, y2, color=MUTE):
    ang = math.atan2(y2 - y1, x2 - x1)
    a1 = (x2 - 8 * math.cos(ang - 0.4), y2 - 8 * math.sin(ang - 0.4))
    a2 = (x2 - 8 * math.cos(ang + 0.4), y2 - 8 * math.sin(ang + 0.4))
    return (L(x1, y1, x2, y2, color, 1.5) +
            f'<polygon points="{x2:.1f},{y2:.1f} {a1[0]:.1f},{a1[1]:.1f} {a2[0]:.1f},{a2[1]:.1f}" fill="{color}"/>')


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def harmonic(xs):
    return len(xs) / sum(1 / x for x in xs)


# ---------------------------------------------------------------- 셈 1: 조화 평균
print("== 셈 1. 창 점수 모으기(식 3) 작은 예시")
EX = [0.9, 0.9, 0.9, 0.1]
print(f"  창 넷의 점수 {EX}: 산술 평균 {st.mean(EX):.3f} · 조화 평균 {harmonic(EX):.3f}")
EX2 = [0.9, 0.9, 0.9, 0.9]
print(f"  창 넷이 모두 0.9: 산술 {st.mean(EX2):.3f} · 조화 {harmonic(EX2):.3f}")

# ---------------------------------------------------------------- 셈 2: 프롬프트 수
print("== 셈 2. 조합 프롬프트 묶음의 문장 수 (부록 그림 6)")
n_n, n_a, n_t = len(STATE_NORMAL), len(STATE_ANOMALY), len(TEMPLATES)
print(f"  정상 상태 {n_n} x 틀 {n_t} = {n_n * n_t} 문장, 결함 상태 {n_a} x 틀 {n_t} = {n_a * n_t} 문장, 합 {(n_n + n_a) * n_t}")
print(f"  틀 {n_t} 개 가운데 CLIP ImageNet 80 개 목록에 같은 문장이 있는 것 {TEMPLATES_IN_CLIP80} 개, 새로 넣은 것 {n_t - TEMPLATES_IN_CLIP80} 개")

# ---------------------------------------------------------------- 셈 3: 표 3 · 표 1 의 0 장 줄
print("== 셈 3. 표 3 쌓기와 우연(50) 아래 값")
prev = None
for name, au, ap, f1 in TABLE3:
    print(f"  {name:14s} AUROC {au:5.1f}" + (f"  (+{au - prev:.1f})" if prev is not None else ""))
    prev = au
print(f"  One-class 34.2 는 우연 50 아래. 점수 부호를 뒤집으면 AUROC = 100 - 34.2 = {100 - 34.2:.1f}")
for data in ("MVTec-AD", "VisA"):
    m = MAIN[("AC", data)]
    print(f"  {data}: CLIP-AC {m['CLIP-AC_0'][0]} -> +CLIP 80 틀 {m['CLIP-AC+ens_0'][0]} ({m['CLIP-AC+ens_0'][0] - m['CLIP-AC_0'][0]:+.1f}) "
          f"· WinCLIP {m['WinCLIP_0'][0]} ({m['WinCLIP_0'][0] - m['CLIP-AC_0'][0]:+.1f})")

# ---------------------------------------------------------------- 셈 4: 창 · 토큰 · 표 8 시간
print("== 셈 4. 창 수 · 토큰 수 · 표 8 시간 나누기 (입력 240, 조각 16)")
g = INPUT // PATCH
print(f"  조각 격자 {g} x {g} = {g * g} 개, 이미지 전체 토큰 {g * g + 1} (클래스 토큰 포함)")
tok = {}
for k, s in WINDOWS.items():
    n = (g - s + 1) ** 2
    tok[k] = n * (s * s + 1)
    print(f"  {k}: 창 {s}x{s} 조각 = {s * PATCH}x{s * PATCH} 화소, 보폭 1 이면 창 {n} 개, 창마다 토큰 {s * s + 1}, 합 {tok[k]}")
t = {r[0]: r[4] for r in TABLE8}
cost = {"image": t["WinCLIP"] - t["w/o image-scale"], "mid": t["WinCLIP"] - t["w/o mid-scale"], "small": t["WinCLIP"] - t["w/o small-scale"]}
print(f"  표 8 시간에서 뺀 몫(ms): 이미지 크기 {cost['image']:.1f} · 중간 창 {cost['mid']:.1f} · 작은 창 {cost['small']:.1f}, 셋 합 {sum(cost.values()):.1f}, 남는 몫 {t['WinCLIP'] - sum(cost.values()):.1f}")
print(f"  중간 / 작은: 시간 {cost['mid'] / cost['small']:.2f} 배 · 토큰 {tok['mid'] / tok['small']:.2f} 배 · 창 수 {((g - 2) ** 2) / ((g - 1) ** 2):.2f} 배")
print(f"  조화 평균을 빼면 시간이 {t['WinCLIP'] - t['w/o Harmonic avg.']:.1f} ms 준다(무엇으로 바꿨는지 적혀 있지 않다)")
print(f"  Image tiling / WinCLIP 시간 = {t['Image tiling'] / t['WinCLIP']:.2f} 배, WinCLIP / Patch-token = {t['WinCLIP'] / t['Patch-token']:.2f} 배")
print(f"  Patch-token pAUROC 22.4 는 우연 50 아래. 부호를 뒤집으면 {100 - 22.4:.1f} (PRO · F1-max 는 이렇게 뒤집을 수 없다)")
for side in (700, 1024):
    for k, s in WINDOWS.items():
        px = s * PATCH / INPUT * side
        print(f"  원본 {side} 화소 정사각 이미지에서 {k} 창 한 변 = {px:.1f} 화소, 넓이 몫 {(s * PATCH / INPUT) ** 2 * 100:.2f}%")
Ls, Ll = 1000, 1500
n_tiles = math.ceil((Ll - Ls) / (TILE_STRIDE_MAX * Ls)) + 1
print(f"  VisA 1500 x 1000 이미지: 1000 x 1000 타일, 보폭 최대 800 -> 타일 {n_tiles} 개")

# ---------------------------------------------------------------- 셈 5: 표 1 · 4 문장 대조
print("== 셈 5. 표 1 · 4 와 본문 문장")
for key in (("AC", "MVTec-AD"), ("AC", "VisA"), ("AS", "MVTec-AD"), ("AS", "VisA")):
    d = [round(MAIN[key]["WinCLIP+_1"][i] - MAIN[key]["PatchCore_1"][i], 1) for i in range(3)]
    print(f"  {key} 1 장 WinCLIP+ - PatchCore (지표 셋): {d}")
lose = []
for key in MAIN:
    for k in SHOTS:
        for i in range(3):
            w = MAIN[key][f"WinCLIP+_{k}"][i]
            best = max(MAIN[key][f"{m}_{k}"][i] for m in METHODS[:3])
            if w <= best:
                lose.append((key, k, i, w, best))
print(f"  WinCLIP+ 가 셋 가운데 최고 이하인 칸(36 칸 중): {lose}")
m = MAIN[("AC", "MVTec-AD")]
print("  MVTec 0 장 WinCLIP 대 PatchCore 4 장:", [(m["WinCLIP_0"][i], m["PatchCore_4"][i]) for i in range(3)])
print("  MVTec WinCLIP+ 1 장 대 WinCLIP 0 장:", [(m["WinCLIP+_1"][i], m["WinCLIP_0"][i]) for i in range(3)])
print(f"  VisA 1 장 AUROC 차 {83.8 - 79.9:.1f} 대 표준편차 WinCLIP+ {STD[('AC', 'VisA', 'WinCLIP+_1')]} · PatchCore {STD[('AC', 'VisA', 'PatchCore_1')]}")

# ---------------------------------------------------------------- 셈 6: 부류별
print("== 셈 6. 부류별 (부록 표 10 · 13 · 16 · 19)")
objs = [c for c in classes("table10") if c not in TEXTURE]
for tb in ("table10", "table13", "table14", "table15"):
    tx = st.mean(cw(tb, c, "WinCLIP_0") for c in TEXTURE)
    ob = st.mean(cw(tb, c, "WinCLIP_0") for c in objs)
    print(f"  MVTec {CW[tb]['metric']:12s} 0 장 WinCLIP 질감 다섯 {tx:.2f} · 물체 열 {ob:.2f}")
gain = sorted(((cw("table10", c, "WinCLIP+_1") - cw("table10", c, "PatchCore_1"), c) for c in classes("table10")), reverse=True)
tot = sum(x for x, _ in gain)
top3 = sum(x for x, _ in gain[:3])
print("  1 장 분류 AUROC WinCLIP+ - PatchCore 부류별:", [(c, round(x, 1)) for x, c in gain])
print(f"  합 {tot:.1f} / 15 = {tot / 15:.2f}, 위 셋({', '.join(c for _, c in gain[:3])}) 몫 {top3 / tot * 100:.1f}%, 나머지 열둘 평균 {(tot - top3) / 12:.2f}")
for tb in ("table10", "table13", "table16", "table19"):
    row = []
    for k in SHOTS:
        cs = classes(tb)
        w = sum(1 for c in cs if cw(tb, c, f"WinCLIP+_{k}") > max(cw(tb, c, f"{mm}_{k}") for mm in METHODS[:3]))
        row.append(f"{k} 장 {w}/{len(cs)}")
    print(f"  WinCLIP+ 가 세 비교 상대를 모두 넘은 부류 수 {CW[tb]['data']} {CW[tb]['metric']}: {', '.join(row)}")
print("  1 장에서 50 아래:", [(c, mm, cw("table10", c, f"{mm}_1")) for c in classes("table10") for mm in METHODS if cw("table10", c, f"{mm}_1") < 50])
print("  VisA 0 장 분류 AUROC 가장 낮은 셋:", sorted((cw("table16", c, "WinCLIP_0"), c) for c in classes("table16"))[:3])

# ---------------------------------------------------------------- 셈 7: 부록 표 평균 대조
print("== 셈 7. 부록 표의 Mean 행 대 부류 평균 (반올림 한계 0.10)")
for tb in [k for k in CW if k.startswith("table")]:
    for col in COLS:
        mean = st.mean(cw(tb, c, col) for c in classes(tb))
        rep = CW[tb]["rows"]["Mean"][COLS.index(col)][0]
        if abs(mean - rep) > 0.10:
            print(f"  {tb} {CW[tb]['data']} {CW[tb]['metric']} {col}: 부류 평균 {mean:.2f} · Mean {rep}")
same = [c for c in classes("table10") if CW["table10"]["rows"][c][COLS.index("PatchCore_2")] == CW["table10"]["rows"][c][COLS.index("PatchCore_4")]]
print(f"  표 10 PatchCore 2 장 열과 4 장 열이 (평균, 표준편차) 까지 같은 부류: {len(same)} / 15")
for k in SHOTS:
    a = APPX_TABLE8[k]["WinCLIP+"][:3]
    b = MAIN[("AC", "MVTec-AD")][f"WinCLIP+_{k}"]
    print(f"  WinCLIP+ {k} 장 분류: 부록 표 8 {a} · 본문 표 1 {b} · AUROC 차 {a[0] - b[0]:+.1f}")
print(f"  부록 표 9 ViT-B/16+ 0 장 AC {APPX_TABLE9[5][2]} · 본문 표 1 {MAIN[('AC', 'MVTec-AD')]['WinCLIP_0'][0]} · 표 3 (c) {TABLE3[3][1]}")
pairs = [("RN50", "RN101"), ("RN50x4", "RN50x16"), ("ViT-B/16", "ViT-L/14")]
t9 = {r[0]: r for r in APPX_TABLE9}
for s, b in pairs:
    print(f"  {s} -> {b}: AC {t9[s][2]} -> {t9[b][2]} · AS {t9[s][3]} -> {t9[b][3]}")
for k in SHOTS:
    h, l = APPX_TABLE8[k]["PatchCore hidden ViT-B/16+"], APPX_TABLE8[k]["PatchCore last ViT-B/16+"]
    print(f"  {k} 장 PatchCore ViT-B/16+ last - hidden: " + ", ".join(f"{x - y:+.1f}" for x, y in zip(l, h)))

# ---------------------------------------------------------------- 셈 8: 표 2 · 5 · 6 · 7
print("== 셈 8. 표 2 · 5 · 6 · 7")
for i, k in enumerate((1, 2, 4, 8)):
    b, v, l = TABLE5["both"][i], TABLE5["max M^W only"][i], TABLE5["ascore0 only"][i]
    print(f"  표 5 {k} 장: 둘 다 {b} - 참조만 {v} = {b - v:+.1f}, 둘 다 - 글만 {b - l:+.1f}")
for i, k in enumerate((1, 2, 4, 8)):
    best = max(TABLE6, key=lambda r: TABLE6[r][i])
    print(f"  표 6 {k} 장: 가장 높은 줄 {best} ({TABLE6[best][i]})")
g7 = {c: round(TABLE7['+ specific states'][c] - TABLE7['WinCLIP'][c], 1) for c in TABLE7['WinCLIP']}
print(f"  표 7 오름 {g7}, 보인 셋의 합 {sum(v for c, v in g7.items() if c != 'Mean'):.1f} · 평균 오름 x 12 = {g7['Mean'] * 12:.1f}")
print(f"  표 2: WinCLIP+ 4 장 {TABLE2[2][2]}/{TABLE2[2][3]} · CutPaste {TABLE2[9][2]}/{TABLE2[9][3]} · PatchCore 전체 {TABLE2[10][2]}/{TABLE2[10][3]}")
print(f"  같은 백본(ViT-B/16+) 1 장: PatchCore(last) {APPX_TABLE8[1]['PatchCore last ViT-B/16+'][0]} · 참조만(표 5) {TABLE5['max M^W only'][0]} · 글만 {TABLE5['ascore0 only'][0]} · 둘 다 {TABLE5['both'][0]}")


# ================================================================ 그림
# 그림 1: 조화 평균 예시
body = [T(20, 28, "한 화소를 덮는 창 넷의 결함 점수와 두 평균 (식 3, 내 예시)", 15, weight="bold")]
x0, y0, h = 70, 60, 200
body += [L(x0, y0 + h, 560, y0 + h, INK), L(x0, y0, x0, y0 + h, INK)]
for v in (0, 0.5, 1.0):
    y = y0 + h - v * h
    body += [L(x0 - 4, y, x0, y, INK), T(x0 - 8, y + 4, f"{v:.1f}", 11, MUTE, "end")]
for i, v in enumerate(EX):
    bx = x0 + 25 + i * 70
    body += [R(bx, y0 + h - v * h, 44, v * h, A if v > 0.5 else D), T(bx + 22, y0 + h + 18, f"창 {i + 1}", 11, MUTE, "middle"),
             T(bx + 22, y0 + h - v * h - 6, f"{v}", 11, INK, "middle")]
ar, hr = st.mean(EX), harmonic(EX)
for v, c, lab in ((ar, Y, f"산술 평균 {ar:.2f}"), (hr, B, f"조화 평균 {hr:.2f}")):
    y = y0 + h - v * h
    body += [L(x0, y, 380, y, c, 2, "6 4"), T(390, y + 4, lab, 12, c, weight="bold")]
body += [T(20, y0 + h + 48, "창 셋이 결함(0.9)이라 해도 하나가 정상(0.1)이라 하면 조화 평균은 0.30 으로 정상 쪽에 붙는다.", 12, INK),
         T(20, y0 + h + 68, "원문: 「정상 예측(0)으로 더 무게를 둔다」. 창 넷이 모두 0.9 면 두 평균 모두 0.90 이다.", 12, MUTE)]
save("fig01_harmonic_example.svg", 640, 350, body)

# 그림 2: 조합 프롬프트 묶음
body = [T(20, 28, "조합 프롬프트 묶음: 상태 낱말 x 문장 틀 -> 평균 -> 원형 둘 (부록 그림 6, 문장 수는 내 셈)", 15, weight="bold")]
body += [R(20, 50, 200, 150, "#eef3fa", A, 6), T(30, 72, f"정상 상태 {n_n} 개", 13, A, weight="bold")]
for i, s in enumerate(STATE_NORMAL):
    body.append(T(30, 92 + i * 15, s, 11))
body += [R(20, 215, 200, 98, "#fbefec", B, 6), T(30, 237, f"결함 상태 {n_a} 개", 13, B, weight="bold")]
for i, s in enumerate(STATE_ANOMALY):
    body.append(T(30, 257 + i * 15, s, 11))
body += [R(260, 50, 230, 255, "#f6f6f6", D, 6), T(270, 72, f"문장 틀 {n_t} 개", 13, INK, weight="bold")]
for i, s in enumerate(TEMPLATES[::2][:9]):
    body.append(T(270, 92 + i * 15, s.replace(" [c].", " [c]."), 10, MUTE))
body += [T(270, 232, "... (a / the 짝으로 22 개)", 10, MUTE),
         T(270, 256, f"CLIP ImageNet 80 개에 있는 것 {TEMPLATES_IN_CLIP80}", 11, INK),
         T(270, 274, "새로 넣은 것 4: for visual inspection,", 11, INK), T(270, 290, "for anomaly detection (a / the)", 11, INK)]
body += [ARROW(222, 125, 258, 125), ARROW(222, 260, 258, 260)]
body += [R(530, 80, 180, 70, "#eef3fa", A, 6), T(540, 102, f"{n_n} x {n_t} = {n_n * n_t} 문장", 13, A, weight="bold"),
         T(540, 122, "글 부호기 -> 평균", 11), T(540, 140, "-> 정상 원형 1 개", 11),
         R(530, 205, 180, 70, "#fbefec", B, 6), T(540, 227, f"{n_a} x {n_t} = {n_a * n_t} 문장", 13, B, weight="bold"),
         T(540, 247, "글 부호기 -> 평균", 11), T(540, 265, "-> 결함 원형 1 개", 11)]
body += [ARROW(492, 125, 528, 115), ARROW(492, 260, 528, 240)]
body += [T(20, 335, "[o] 는 데이터셋의 물체 이름(bottle 등)이다. 정상 쪽 첫 줄 「[o]」 는 상태 낱말 없이 물체 이름만 넣은 것이다.", 12, INK),
         T(20, 355, "이미지 임베딩과 두 원형의 코사인으로 두 부류 소프트맥스(식 1)를 낸다. 결함 쪽 확률이 ascore0 라는 것은 내 해석이다(원문에 식이 없다).", 12, MUTE)]
save("fig02_cpe_composition.svg", 730, 375, body)

# 그림 3: 표 3 쌓기
body = [T(20, 28, "표 3: MVTec AD 0 장 분류 AUROC 를 한 단계씩 쌓기", 15, weight="bold")]
x0, xw, y0 = 170, 420, 55
def xs(v): return x0 + (v - 30) / 70 * xw
for v in (30, 50, 70, 90, 100):
    body += [L(xs(v), y0 - 5, xs(v), y0 + 5 * 38, LINE), T(xs(v), y0 + 5 * 38 + 16, f"{v}", 11, MUTE, "middle")]
body += [L(xs(50), y0 - 5, xs(50), y0 + 5 * 38, B, 1.5, "5 4"), T(xs(50) + 4, y0 - 8, "우연 50", 11, B)]
prev = None
for i, (name, au, _, _) in enumerate(TABLE3):
    y = y0 + i * 38
    col = D if i == 0 else A
    body += [T(x0 - 8, y + 18, name, 12, INK, "end"), R(x0, y + 5, xs(au) - x0, 22, col), T(xs(au) + 6, y + 21, f"{au}", 12, INK, weight="bold")]
    if prev is not None:
        body.append(T(xs(au) + 46, y + 21, f"(+{au - prev:.1f})", 11, MUTE))
    prev = au
body += [T(20, y0 + 5 * 38 + 44, "One-class(점수 = 「normal [o]」 와의 유사도에 음수)는 우연보다 15.8 낮다. 부호를 뒤집으면 65.8 이 되는 순위다(내 셈).", 12),
         T(20, y0 + 5 * 38 + 64, "가장 큰 두 몫은 결함 글을 넣은 것(+39.8)과 상태 낱말 묶음(+15.8)이다. 한 번 실행, 쌓는 순서를 바꾼 줄은 없다.", 12, MUTE)]
save("fig03_table3_steps.svg", 700, 330, body)

# 그림 4: 표 8 시간 대 pAUROC
body = [T(20, 28, "표 8: MVTec AD 0 장 분할 pAUROC 와 이미지당 시간 (EC2 G4dn)", 15, weight="bold")]
x0, y0, w, h = 80, 50, 520, 260
lo, hi = math.log10(60), math.log10(2000)
def px(ms): return x0 + (math.log10(ms) - lo) / (hi - lo) * w
def py(v): return y0 + h - (v - 0) / 100 * h
body += [L(x0, y0 + h, x0 + w, y0 + h, INK), L(x0, y0, x0, y0 + h, INK)]
for ms in (100, 200, 500, 1000, 2000):
    body += [L(px(ms), y0 + h, px(ms), y0 + h + 4, INK), T(px(ms), y0 + h + 18, f"{ms}", 11, MUTE, "middle")]
for v in (0, 25, 50, 75, 100):
    body += [L(x0 - 4, py(v), x0, py(v), INK), T(x0 - 8, py(v) + 4, f"{v}", 11, MUTE, "end")]
body += [L(x0, py(50), x0 + w, py(50), B, 1, "5 4"), T(x0 + w - 2, py(50) - 5, "우연 50", 11, B, "end"),
         T(x0 + w / 2, y0 + h + 38, "이미지당 시간 (ms, 로그 눈금)", 12, MUTE, "middle"), T(20, y0 + h / 2, "pAUROC", 12, MUTE)]
num_off = {"WinCLIP": -12, "w/o image-scale": 20, "w/o mid-scale": -12, "w/o small-scale": -12, "w/o Harmonic avg.": 20}
legend = []
for name, pa, _, _, ms, sd in TABLE8:
    col = A if name == "WinCLIP" else (Y if name.startswith("w/o") else D)
    body.append(CIRC(px(ms), py(pa), 6, col))
    if name in num_off:
        n = len(legend) + 1
        body.append(T(px(ms), py(pa) + num_off[name], str(n), 11, INK, "middle", "bold"))
        legend.append((n, name, pa, ms, sd, col))
    else:
        body.append(T(px(ms) + (10 if name == "Patch-token" else -10), py(pa) + 4, f"{name} {pa} ({ms} ms)", 11, INK,
                      "start" if name == "Patch-token" else "end"))
for i, (n, name, pa, ms, sd, col) in enumerate(legend):
    body += [CIRC(x0 + 300, y0 + 146 + i * 18, 5, col), T(x0 + 312, y0 + 150 + i * 18, f"{n}  {name}  {pa} · {ms} ms", 11, INK)]
body += [f'<circle cx="{px(95.5):.1f}" cy="{py(77.6):.1f}" r="6" fill="none" stroke="{D}" stroke-width="2" stroke-dasharray="3 2"/>',
         L(px(95.5), py(22.4) - 7, px(95.5), py(77.6) + 7, D, 1, "3 3"), T(px(95.5) + 10, py(77.6) + 4, "부호를 뒤집으면 77.6 (내 셈)", 11, D)]
body += [T(20, y0 + h + 66, "Patch-token 은 「정렬되지 않았다」 고 원문이 읽지만 22.4 는 우연보다 27.6 낮다. 순위가 거꾸로 서 있다는 뜻이다.", 12),
         T(20, y0 + h + 86, "시간은 평균 ± 표준편차가 있고 점수는 한 번 값이다. 「w/o Harmonic avg.」 가 109.5 ms 빠른 까닭은 적혀 있지 않다.", 12, MUTE)]
save("fig04_table8_time_vs_pauroc.svg", 680, 410, body)

# 그림 5: 부류별 0 장
cs = sorted(classes("table10"), key=lambda c: cw("table10", c, "WinCLIP_0"))
body = [T(20, 28, "부록 표 10 · 13: MVTec AD 0 장 WinCLIP 부류별 (분류 AUROC 순)", 15, weight="bold"),
        R(440, 42, 12, 12, A), T(458, 53, "분류 AUROC", 11), R(540, 42, 12, 12, Y), T(558, 53, "분할 pAUROC", 11)]
x0, y0, w, rh = 120, 70, 480, 22
def vx(v): return x0 + (v - 50) / 50 * w
for v in (50, 60, 70, 80, 90, 100):
    body += [L(vx(v), y0 - 4, vx(v), y0 + len(cs) * rh, LINE), T(vx(v), y0 + len(cs) * rh + 15, f"{v}", 11, MUTE, "middle")]
for i, c in enumerate(cs):
    y = y0 + i * rh
    ac, asg = cw("table10", c, "WinCLIP_0"), cw("table13", c, "WinCLIP_0")
    tex = c in TEXTURE
    body += [T(x0 - 8, y + 15, c + (" (질감)" if tex else ""), 11, INK, "end", "bold" if tex else "normal"),
             R(x0, y + 3, vx(ac) - x0, 8, A), R(x0, y + 12, vx(asg) - x0, 8, Y),
             T(vx(max(ac, asg)) + 4, y + 15, f"{ac} / {asg}", 10, MUTE)]
yb = y0 + len(cs) * rh + 40
tx_ac = st.mean(cw("table10", c, "WinCLIP_0") for c in TEXTURE); ob_ac = st.mean(cw("table10", c, "WinCLIP_0") for c in objs)
tx_as = st.mean(cw("table13", c, "WinCLIP_0") for c in TEXTURE); ob_as = st.mean(cw("table13", c, "WinCLIP_0") for c in objs)
body += [T(20, yb, f"질감 다섯 평균: 분류 {tx_ac:.2f} · 분할 {tx_as:.2f}   물체 열 평균: 분류 {ob_ac:.2f} · 분할 {ob_as:.2f} (내 셈)", 12, INK, weight="bold"),
         T(20, yb + 20, "분류는 질감이 쉽고(셋이 100.0), 분할은 Tile 77.6 처럼 질감도 낮은 부류가 있다. 0 장이라 표준편차는 0.0 이다.", 12, MUTE)]
save("fig05_classwise_zeroshot.svg", 700, yb + 40, body)

# 그림 6: 1 장 부류별 차
body = [T(20, 28, "부록 표 10: 1 장 분류 AUROC, WinCLIP+ - PatchCore 부류별 (내 뺄셈)", 15, weight="bold")]
x0, y0, rh = 130, 50, 22
zero = x0 + 60
def gx(v): return zero + v / 45 * 400
body += [L(zero, y0 - 4, zero, y0 + len(gain) * rh, INK)]
for v in (0, 10, 20, 30, 40):
    body += [L(gx(v), y0 + len(gain) * rh, gx(v), y0 + len(gain) * rh + 4, INK), T(gx(v), y0 + len(gain) * rh + 17, f"{v:+d}" if v else "0", 11, MUTE, "middle")]
for i, (v, c) in enumerate(gain):
    y = y0 + i * rh
    col = B if i < 3 else (A if v > 0 else D)
    xa, xb = (zero, gx(v)) if v >= 0 else (gx(v), zero)
    pc = cw("table10", c, "PatchCore_1")
    body += [T(x0 - 8, y + 15, c, 11, INK, "end"), R(xa, y + 4, xb - xa, 14, col),
             T(max(xb, zero) + 6, y + 15, f"{v:+.1f}  (PatchCore {pc})", 10, MUTE)]
yb = y0 + len(gain) * rh + 42
body += [T(20, yb, f"평균 +{tot / 15:.2f} 가 본문의 「9.7%」 다. 그 합의 {top3 / tot * 100:.1f}% 가 위 세 부류(빨강)에서 나온다.", 12, INK, weight="bold"),
         T(20, yb + 20, f"세 부류는 PatchCore 1 장이 44.4 · 63.6 · 73.4 인 곳이다. 나머지 열둘의 평균 차는 +{(tot - top3) / 12:.2f} 다.", 12, MUTE)]
save("fig06_oneshot_gain_by_class.svg", 700, yb + 40, body)

# 그림 7: 표 5 장 수
body = [T(20, 28, "표 5: MVTec AD 분류 AUROC, 참조 점수 · 글 점수 · 둘의 평균", 15, weight="bold")]
x0, y0, w, h = 70, 50, 480, 240
ks = (1, 2, 4, 8)
def kx(i): return x0 + 30 + i * (w - 60) / 3
def ky(v): return y0 + h - (v - 86) / 12 * h
body += [L(x0, y0 + h, x0 + w, y0 + h, INK), L(x0, y0, x0, y0 + h, INK)]
for v in (86, 89, 92, 95, 98):
    body += [L(x0 - 4, ky(v), x0, ky(v), INK), T(x0 - 8, ky(v) + 4, f"{v}", 11, MUTE, "end"), L(x0, ky(v), x0 + w, ky(v), "#eeeeee")]
for i, k in enumerate(ks):
    body.append(T(kx(i), y0 + h + 18, f"{k} 장", 11, MUTE, "middle"))
for name, col, lab in (("max M^W only", D, "참조만 (max M^W)"), ("ascore0 only", Y, "글만 (ascore0, 0 장 값)"), ("both", A, "둘의 평균 (식 6)")):
    pts = [(kx(i), ky(v)) for i, v in enumerate(TABLE5[name])]
    body.append(PL(pts, col, 2.5))
    for j, ((x, y), v) in enumerate(zip(pts, TABLE5[name])):
        body.append(CIRC(x, y, 5, col))
        if name == "both":
            body.append(T(x, y - 9, f"{v}", 10, INK, "middle"))
        elif name == "max M^W only":
            body.append(T(x - 8, y - 8, f"{v}", 10, INK, "end") if j == 2 else T(x + 8, y + 16, f"{v}", 10, INK, "start"))
        elif j == 0:
            body.append(T(x, y + 18, f"{v}", 10, INK, "middle"))
    body.append(T(x0 + w + 8, pts[-1][1] + 4, lab, 11, col, weight="bold"))
body += [T(20, y0 + h + 48, "둘의 평균 - 참조만: +5.2 · +3.4 · +2.6 · +1.8 (내 뺄셈). 참조가 늘수록 글이 보태는 몫이 준다.", 12),
         T(20, y0 + h + 68, "8 장 값은 본문 표 1 에 없고 이 표에만 있다. 표준편차가 없다.", 12, MUTE)]
save("fig07_table5_shots.svg", 760, 340, body)

# 그림 8: 계보
body = [T(20, 28, "WinCLIP 의 자리: 무엇을 가져와 어떻게 묶었나", 15, weight="bold")]
def box(x, y, w, h, title, sub, col):
    out = [R(x, y, w, h, "#ffffff", col, 6), T(x + w / 2, y + 22, title, 13, col, "middle", "bold")]
    for j, s in enumerate(sub):
        out.append(T(x + w / 2, y + 42 + j * 16, s, 11, MUTE, "middle"))
    return out
body += box(20, 50, 200, 90, "CLIP (2021)", ["이미지-글 대조 사전학습", "클래스 이름 글로 제로샷 분류", "이미지 하나에 임베딩 하나"], A)
body += box(20, 165, 200, 90, "MAE (2022)", ["가린 조각을 빼고 순전파", "-> 창마다 계산을 줄인 근거"], D)
body += box(20, 280, 200, 90, "SPADE · PatchCore", ["정상 조각 특징을 기억해 두고", "가장 가까운 거리로 결함 점수"], Y)
body += box(290, 130, 230, 150, "WinCLIP / WinCLIP+ (2023)", ["상태 낱말 x 틀 -> 원형 둘 (4.1)", "창으로 가린 이미지를 CLIP 에", "다시 넣어 창마다 클래스 토큰 (4.2)", "조화 평균 · 다중 크기", "+ 정상 1~4 장 기억과 최근접 (4.3)", "학습하는 파라미터 없음"], B)
body += box(590, 165, 200, 90, "AnomalyCLIP (2024)", ["이 큰 틀의 다음 칸", "프롬프트를 배운다", "(이 노트에서는 안 읽음)"], D)
body += [ARROW(222, 95, 288, 170), ARROW(222, 210, 288, 205), ARROW(222, 325, 288, 250), ARROW(522, 205, 588, 210)]
body += [T(20, 400, "WinCLIP 의 기본 백본은 OpenAI CLIP 이 아니라 OpenCLIP 의 LAION-400M ViT-B/16+ 다. CLIP 논문의 WIT 와 사전학습 데이터가 다르다.", 12, INK)]
save("fig08_lineage.svg", 810, 420, body)

print("== 그림 여덟을 썼다")
