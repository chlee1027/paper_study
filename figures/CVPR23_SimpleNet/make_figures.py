# -*- coding: utf-8 -*-
"""SimpleNet 노트의 그림을 만들고, 노트가 인용하는 다시 계산한 값을 찍는다.

표준 라이브러리만 쓰고 바깥 데이터를 읽지 않는다. 값은 같은 폴더 data_simplenet.py 의 상수다.

  python make_figures.py

찍는 것: 표 1 의 평균 다시 내기, 상대 열과 원 출처의 칸 대조, 부류별 1 위 수, 오류 감소율,
그림 2 의 속도 배수, 그림 5 의 평균 선과 부류 선 평균의 차 · 표 1 과의 차, 그림 4 의 잡음 대 표준편차,
특징 지도 크기 · 적응기 파라미터 수 · 부류별 반복 수, 표 5 와 RD 표 4 의 대조.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_simplenet import *  # noqa: E402,F401,F403

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "'Malgun Gothic','Noto Sans KR',sans-serif"
INK, MUTE, LINE = "#222222", "#666666", "#cccccc"
A, B, C, D = "#2f6db3", "#c8553d", "#4a9a6a", "#8a8a8a"
SN = T1_COLS.index("SimpleNet")


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


def PL(pts, stroke, width=1.5, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{width}"{d}/>'


def CIRC(x, y, r, fill, stroke="none"):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}"/>'


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def mean(v):
    v = list(v)
    return sum(v) / len(v)


def col(j, q, classes=CL):
    return [T1[k][j][q] for k in classes]


def same(a, b, classes=CL):
    return sum(1 for k in classes if a[k] == b[k]), [k for k in classes if a[k] != b[k]]


def best_other(k, q):
    vals = [(T1[k][j][q], T1_COLS[j]) for j in range(len(T1_COLS)) if j != SN and T1[k][j][q] is not None]
    m = max(v for v, _ in vals)
    return m, [n for v, n in vals if v == m]


# ---------------------------------------------------------------- 찍기
def recount():
    print("[셈 1] 표 1 평균 다시 내기 (질감 5 · 물체 10 · 전체 15). 인쇄 값과 0.05 넘게 다르면 *")
    for j, n in enumerate(T1_COLS):
        for q, qn in ((0, "I"), (1, "P")):
            if T1["carpet"][j][q] is None:
                continue
            got = [mean(col(j, q, TEX)), mean(col(j, q, CL[5:])), mean(col(j, q))]
            pr = [T1_TEX[j][q], T1_OBJ[j][q], T1_ALL[j][q]]
            tol = 0.5 if n == "AE-SSIM" and q == 0 else 0.05
            flag = ["*" if abs(g - p) > tol + 1e-9 else " " for g, p in zip(got, pr)]
            print(f"  {n:10s} {qn}  " + "  ".join(f"{g:6.2f}/{p:<5}{f}" for g, p, f in zip(got, pr, flag)))

    print("\n[셈 2] 상대 열과 원 출처의 칸 대조 (같은 칸 / 15)")
    I = {n: {k: T1[k][j][0] for k in CL} for j, n in enumerate(T1_COLS)}
    P = {n: {k: T1[k][j][1] for k in CL} for j, n in enumerate(T1_COLS)}
    checks = [
        ("AE-SSIM I  대 MVTec AD 원문 표 3 분할 ROC AUC(픽셀)", I["AE-SSIM"], MVTEC_AESSIM_SEG_AUC),
        ("AE-SSIM P  대 US 원문 표 1 SSIM-AE PRO", P["AE-SSIM"], US_AESSIM_PRO),
        ("AE-SSIM P  대 PaDiM 원문 표 III AE-SSIM 의 PRO", P["AE-SSIM"], {k: v[1] for k, v in PADIM_T3_AESSIM.items()}),
        ("RIAD I     대 DRAEM 표 1 RIAD", I["RIAD"], DRAEM_RIAD_IMG),
        ("RIAD P     대 DRAEM 표 2 RIAD", P["RIAD"], DRAEM_RIAD_PIX),
        ("DRAEM I    대 DRAEM 표 1", I["DRAEM"], DRAEM_IMG),
        ("DRAEM P    대 DRAEM 표 2", P["DRAEM"], DRAEM_PIX),
        ("CutPaste I 대 RD 표 1 CutPaste", I["CutPaste"], RD_CP_IMG),
        ("CutPaste P 대 RD 표 2 CutPaste", P["CutPaste"], RD_CP_PIX),
        ("PaDiM I    대 RD 표 1 PaDiM(=DRAEM 구현)", I["PaDiM"], RD_T1_PADIM),
        ("PaDiM I    대 RD 표 1 MetaFormer", I["PaDiM"], RD_T1_MF),
        ("PaDiM P    대 PaDiM 원문 WR50-Rd550", P["PaDiM"], PADIM_PIX),
        ("RevDist I  대 RD 표 1 (256)", I["RevDist"], RD_IMG),
        ("RevDist P  대 RD 표 2 (256)", P["RevDist"], RD_PIX),
        ("PatchCore I 대 PatchCore 표 S1 25%", I["PatchCore"], PC_IMG["25"]),
        ("PatchCore I 대 PatchCore 표 S1 10%", I["PatchCore"], PC_IMG["10"]),
        ("PatchCore I 대 PatchCore 표 S1 1%", I["PatchCore"], PC_IMG["1"]),
        ("PatchCore P 대 PatchCore 표 S2 25%", P["PatchCore"], PC_PIX["25"]),
    ]
    for name, a, b in checks:
        n, diff = same(a, b)
        tex = sum(1 for k in TEX if a[k] == b[k])
        print(f"  {name:48s} {n:2d}/15  (질감 {tex}/5 · 물체 {n - tex}/10)" + (f"  다른 칸: {diff}" if 0 < len(diff) <= 5 else ""))
    print("  PaDiM I 의 인쇄 평균 (질감 · 물체 · 전체):", [T1_TEX[5][0], T1_OBJ[5][0], T1_ALL[5][0]],
          " RD 표 1 MF 평균:", list(RD_T1_MF_AVG.values()), " RD 표 1 PaDiM 평균:", list(RD_T1_PADIM_AVG.values()))
    print("  AE-SSIM 인쇄 평균:", [T1_TEX[0], T1_OBJ[0], T1_ALL[0]], " PaDiM 표 III AE-SSIM 평균:", list(PADIM_T3_AESSIM_AVG.values()))

    print("\n[셈 3] 부류마다 SimpleNet 이 1 위인 수 (같은 값도 1 위로 센다 / 혼자 1 위)")
    for q, qn in ((0, "I-AUROC"), (1, "P-AUROC")):
        tie = solo = 0
        for k in CL:
            m, who = best_other(k, q)
            s = T1[k][SN][q]
            tie += s >= m
            solo += s > m
        print(f"  {qn}: 같은 값 포함 {tie} · 혼자 {solo}  (원문: I 「9 out of 15」, P 「4 out of 15」)")

    print("\n[셈 4] SimpleNet 에서 그 부류의 가장 센 상대를 뺀 값")
    for q, qn in ((0, "I"), (1, "P")):
        rows = []
        for k in CL:
            m, who = best_other(k, q)
            rows.append(f"{k} {T1[k][SN][q] - m:+.1f}({'/'.join(who)})")
        print(f"  {qn}: " + ", ".join(rows))
    for q, qn in ((0, "I"), (1, "P")):
        d = [round(T1[k][SN][q] - T1[k][7][q], 1) for k in CL]
        print(f"  {qn} 대 PatchCore: 높음 {sum(x > 0 for x in d)} · 같음 {sum(x == 0 for x in d)} · 낮음 {sum(x < 0 for x in d)}")

    print("\n[셈 5] 오류 감소율")
    for tag, pc, sn in (("인쇄 평균", T1_ALL[7][0], T1_ALL[SN][0]), ("부류 평균", mean(col(7, 0)), mean(col(SN, 0)))):
        e0, e1 = 100 - pc, 100 - sn
        print(f"  {tag}: PatchCore 오류 {e0:.3f} -> SimpleNet {e1:.3f}, 감소 {(e0 - e1) / e0 * 100:.2f}%")

    print("\n[셈 6] 그림 2 (FPS 는 표식 중심을 눈금으로 환산)")
    f = {n: (x, y) for n, x, y in FIG2}
    ours = f["Ours"][0]
    for n, x, y in FIG2:
        print(f"  {n:26s} FPS {x:6.2f}  I-AUROC {y:.2f}  Ours/이것 = {ours / x:5.2f} 배")
    print("  PaDiM 두 점의 y 값과 PaDiM 원문 표 III 의 픽셀 AUROC 평균:", PADIM_T3_ALL)

    print("\n[셈 7] 그림 5: 「average」 선과 부류 선 15 개의 평균")
    for q, (dct, avg) in (("I", (FIG5_I, FIG5_I_AVG)), ("P", (FIG5_P, FIG5_P_AVG))):
        m = [mean(dct[k][i] for k in CL) for i in range(6)]
        print(f"  {q}: 그림의 average {avg}")
        print(f"     부류 평균         {[round(v, 2) for v in m]}  차 {[round(a - b, 2) for a, b in zip(avg, m)]}")
        bi = max(range(6), key=lambda i: m[i])
        print(f"     부류 평균이 가장 높은 σ = {SIGMA[bi]}, 그림의 average 가 가장 높은 σ = {SIGMA[max(range(6), key=lambda i: avg[i])]}")
        at = [k for k in CL if dct[k][1] >= max(dct[k]) - 1e-9]
        print(f"     σ=0.015 에서 자기 최댓값에 닿은 부류(같은 값 포함) {len(at)}: {at}")
    print("  σ=0.015 의 그림 값과 표 1 SimpleNet 의 차 (그림 - 표)")
    for q, dct in ((0, FIG5_I), (1, FIG5_P)):
        d = {k: round(dct[k][1] - T1[k][SN][q], 2) for k in CL}
        big = {k: v for k, v in d.items() if abs(v) >= 0.1}
        print(f"   {'IP'[q]}: |차| >= 0.1 인 부류 {len(big)}/15, 가장 큰 차 {min(d.values()):+.2f} ({min(d, key=d.get)})")

    print("\n[셈 8] 그림 4 와 잡음 σ = 0.015 (중앙값은 막대 좌표로 읽은 값)")
    for k, v in FIG4.items():
        la, ad = v["local"], v["adapted"]
        print(f"  {k:7s} 막대 합 local {la[0]:.0f} · adapted {ad[0]:.0f} / {DIM}.  adapted 중앙값 {ad[1]:.4f}, 최솟값 {ad[2]:.4f}. "
              f"σ/중앙값 = {SIGMA_DEFAULT / ad[1]:.2f}, σ/최솟값 = {SIGMA_DEFAULT / ad[2]:.2f}.  local 에서 σ 보다 작은 차원 {la[4]:.0f}")
    med = [v["adapted"][1] for v in FIG4.values()]
    print(f"  adapted 중앙값의 최대/최소 = {max(med) / min(med):.2f}")
    print(f"  잡음 벡터 길이의 기댓값 ~ σ·sqrt(C) = {SIGMA_DEFAULT * math.sqrt(DIM):.3f}")

    print("\n[셈 9] 크기")
    h2 = CROP // 8
    print(f"  224 자르기 -> 2 단계 {h2}x{h2}x512, 3 단계 {CROP // 16}x{CROP // 16}x1024 -> {h2}x{h2} 로 맞춤: 자리 {h2 * h2} 개 x {DIM} 차원")
    print(f"  적응기 FC (치우침 없음) {DIM * DIM:,} 개 = WRN50 1 ~ 3 단계 {WRN50_TO_L3_PARAMS:,} 의 {DIM * DIM / WRN50_TO_L3_PARAMS * 100:.1f}%")
    it = {k: math.ceil(N_TRAIN[k] / BATCH) * EPOCHS for k in CL}
    print(f"  반복 수 = ceil(학습 장 수 / {BATCH}) x {EPOCHS}: 최소 {min(it.values()):,} ({min(it, key=it.get)}) · "
          f"최대 {max(it.values()):,} ({max(it, key=it.get)}) · 평균 {mean(it.values()):,.0f}. 그림 7 x 축 {FIG7_X_MAX}")
    print(f"  그림 7 의 2000 반복이 학습 전체에서 차지하는 몫: {FIG7_X_MAX / max(it.values()) * 100:.1f}% ~ {FIG7_X_MAX / min(it.values()) * 100:.1f}%")

    print("\n[셈 10] 표 5 대 RD 표 4 CIFAR10 열")
    t5 = dict(T5)
    for n, v in RD_T4_CIFAR.items():
        print(f"  {n:8s} SimpleNet 표 5 {t5[n]:6}  RD 표 4 {v:6}  {'같음' if t5[n] == v else '다름'}")

    print("\n[셈 11] 끈 실험의 차")
    t2 = {n: (i, p) for n, i, p in T2}
    print(f"  표 2: 3 단계만 {t2['3']}, 2+3 {t2['2+3']}, 1+2+3 {t2['1+2+3']}.  2+3 에 1 을 더하면 I {t2['1+2+3'][0] - t2['2+3'][0]:+.1f}")
    t3 = {n: (i, p) for n, i, p in T3}
    for n in ("Ours-complex-FA", "Ours-w/o-FA", "Ours-CE"):
        print(f"  표 3: Ours - {n} = I {t3['Ours'][0] - t3[n][0]:+.1f} · P {t3['Ours'][1] - t3[n][1]:+.1f}")
    print(f"  표 4: I 범위 {min(r[1] for r in T4)} ~ {max(r[1] for r in T4)}, P 범위 {min(r[2] for r in T4)} ~ {max(r[2] for r in T4)}")


# ---------------------------------------------------------------- 그림
def fig01():
    """표 1 상대 열의 출처 대조."""
    rows = [
        ("AE-SSIM", "I-AUROC", "MVTec AD 원문 표 3 의 분할 ROC AUC (픽셀)", "15/15", B, "다른 지표를 옮김"),
        ("AE-SSIM", "P-AUROC", "PaDiM 원문 표 III AE-SSIM 의 PRO (US 원문 표 1)", "14/15", B, "다른 지표를 옮김, wood 60.5 -> 60.3"),
        ("RIAD", "I · P", "DRAEM 표 1 · 2 의 RIAD 열", "15 · 15", C, "옮긴 값과 같음"),
        ("DRAEM", "I · P", "DRAEM 원문 표 1 · 2", "15 · 15", C, "원 출처와 같음"),
        ("CutPaste", "I · P", "RD 표 1 · 2 의 CutPaste 열 (CutPaste 원문 미대조)", "15 · 15", C, "옮긴 값과 같음"),
        ("CS-Flow", "I", "원문을 받지 않았다", "-", D, "대조 못 함"),
        ("PaDiM", "I-AUROC", "질감 5 = RD 표 1 PaDiM, 물체 10 = RD 표 1 MetaFormer", "5 + 10", B, "두 방법의 열이 섞임, 평균 셋은 MetaFormer"),
        ("PaDiM", "P-AUROC", "PaDiM 원문 WR50-Rd550", "15/15", C, "원 출처와 같음"),
        ("RevDist", "I · P", "RD 원문 표 1 · 2 의 256 열", "15 · 15", C, "원 출처와 같음"),
        ("PatchCore", "I · P", "PatchCore 원문 표 S1 · S2 의 코어셋 25% 줄", "15 · 15", C, "원 출처와 같음 (그림 2 는 10% · 1% 라 적음)"),
    ]
    W, H = 980, 92 + 30 * len(rows) + 30
    b = [T(20, 24, "표 1 의 상대 열을 원 출처와 칸 단위로 맞대 본 결과 (내 대조)", 14, weight="bold"),
         T(20, 44, "빨강 = 지표가 바뀌었거나 다른 방법의 값과 섞임 · 초록 = 칸이 모두 같음 · 회색 = 대조할 원문이 없음", 11, MUTE)]
    xs = [20, 120, 210, 640, 720]
    for x, h in zip(xs, ["열", "지표", "맞댄 곳", "같은 칸", "판정"]):
        b.append(T(x, 72, h, 11, MUTE, weight="bold"))
    for i, (n, q, src, cnt, colr, verdict) in enumerate(rows):
        y = 84 + i * 30
        b.append(R(14, y, 952, 24, "#f6f6f6" if i % 2 else "#ffffff"))
        b.append(R(14, y, 5, 24, colr))
        b.append(T(xs[0] + 8, y + 16, n, 11, weight="bold"))
        b.append(T(xs[1], y + 16, q, 11))
        b.append(T(xs[2], y + 16, src, 11))
        b.append(T(xs[3], y + 16, cnt, 11))
        b.append(T(xs[4], y + 16, verdict, 11, colr))
    b.append(T(20, H - 12, "I = 이미지 AUROC, P = 픽셀 AUROC. 대조에 쓴 값은 원 논문 PDF 또는 이 저장소 앞 노트의 그림 코드에 옮긴 값이다.", 11, MUTE))
    save("fig01_value_sources.svg", W, H, b)


def fig02():
    W = 900
    H = 90 + 24 * len(CL) + 40
    b = [T(20, 24, "표 1 · SimpleNet 에서 그 부류의 가장 센 상대를 뺀 값 (내 뺄셈)", 14, weight="bold"),
         T(20, 44, "왼쪽 I-AUROC (상대 여덟), 오른쪽 P-AUROC (CS-Flow 를 뺀 일곱). 같은 값을 1 위로 세면 I 9 · P 3, 혼자 1 위는 I 3 · P 3.", 11, MUTE)]
    for q, x0, head in ((0, 380, "I-AUROC"), (1, 720, "P-AUROC")):
        b.append(T(x0, 72, head, 12, weight="bold", anchor="middle"))
        b.append(L(x0, 80, x0, 80 + 24 * len(CL), INK))
        for i, k in enumerate(CL):
            m, who = best_other(k, q)
            d = round(T1[k][SN][q] - m, 1)
            y = 84 + i * 24
            w = d * 40
            b.append(R(min(x0, x0 + w), y, max(abs(w), 1.5), 16, (C if k in TEX else A) if d > 0 else (B if d < 0 else D)))
            names = "/".join(who) if len(who) <= 2 else f"상대 {len(who)} 열"
            lab = ("같음 " + names) if d == 0 else (f"{d:+.1f}" + (f" {names}" if d < 0 else ""))
            b.append(T((x0 + w + 6) if d >= 0 else (x0 + w - 6), y + 13, lab, 10, MUTE, "start" if d >= 0 else "end"))
            if q == 0:
                b.append(T(20, y + 13, k + (" (질감)" if k in TEX else ""), 11))
    b.append(T(20, H - 14, "축척 1 점 = 40 px. 파랑 · 초록 = SimpleNet 이 혼자 높음, 회색 = 같음, 빨강 = 낮음(괄호는 가장 센 상대). 상대 열 일부는 출처가 섞여 있다(그림 1).", 11, MUTE))
    save("fig02_tab1_margin.svg", W, H, b)


def fig03():
    """그림 2 를 읽은 값으로 다시 그림."""
    W, H = 900, 470
    x0, y0, pw, ph = 90, 70, 560, 320
    fx = lambda v: x0 + v / 80 * pw
    fy = lambda v: y0 + ph - (v - 95.0) / (100.0 - 95.0) * ph
    b = [T(20, 24, "원문 그림 2 를 벡터 좌표로 읽어 다시 그림 (FPS 대 I-AUROC)", 14, weight="bold"),
         T(20, 44, "원문은 y 축을 97.0 부터 그렸다. 여기서는 95.0 부터 그려 PaDiM 의 이미지 AUROC 가 들어갈 자리를 보인다.", 11, MUTE)]
    for v in range(0, 81, 10):
        b.append(L(fx(v), y0, fx(v), y0 + ph, LINE))
        b.append(T(fx(v), y0 + ph + 16, str(v), 10, MUTE, "middle"))
    for v in (95, 96, 97, 98, 99, 100):
        b.append(L(x0, fy(v), x0 + pw, fy(v), LINE))
        b.append(T(x0 - 8, fy(v) + 4, f"{v:.1f}", 10, MUTE, "end"))
    b.append(R(x0, fy(97.0), pw, fy(95.0) - fy(97.0), "#f3ece9"))
    b.append(T(x0 + pw - 6, fy(95.2), "원문 그림이 잘라 낸 구간 (97.0 아래)", 10, B, "end"))
    for n, x, y in FIG2:
        colr = B if n.startswith("PaDiM") else (A if n == "Ours" else INK)
        b.append(CIRC(fx(x), fy(y), 4, colr))
        lab = {"PatchCore-WRN50-1024-10%": "PatchCore 「10%」 99.1", "PatchCore-WRN50_1024-1%": "PatchCore 「1%」 99.0",
               "PaDiM-WRN50-550d": "PaDiM-WRN50 97.5", "PaDiM-RN18-100d": "PaDiM-RN18 96.7",
               "ReverseDistillation": "RD 98.5"}.get(n, f"{n} {y:.1f}")
        dx = 8 if x < 60 else -8
        dy = 16 if n.endswith("_1024-1%") else -6
        b.append(T(fx(x) + dx, fy(y) + dy, f"{lab} · {x:.1f} FPS", 10, colr, "start" if dx > 0 else "end"))
    for v, lab in ((95.8, "표 1 의 PaDiM I-AUROC 95.8"), (95.3, "PaDiM 원문의 이미지 AUROC 95.3")):
        b.append(L(fx(0.67) - 6, fy(v), fx(0.67) + 6, fy(v), B, 2))
        b.append(T(fx(0.67) + 10, fy(v) + 4, lab, 10, B))
    b.append(T(x0 + pw / 2, y0 + ph + 34, "Frames per second (FPS)", 11, MUTE, "middle"))
    notes = ["PaDiM 두 점의 y 값 97.5 · 96.7 은 PaDiM 원문 표 III 의 픽셀 AUROC 평균(WR50-Rd550 97.5, R18-Rd100 96.7)과 같다.",
             "PatchCore 「10%」 점은 99.1 인데 PatchCore 원문 표 1 의 10% 는 99.0 이고 99.1 은 25% 다. 표 1 의 PatchCore 열도 25% 줄이다.",
             "「8 배 빠르다」: 77.42 / 10.50 = 7.37 (「10%」 점), 77.42 / 14.79 = 5.23 (「1%」 점). 가장 가까운 DRAEM 과는 77.42 / 67.17 = 1.15 배다."]
    for i, s in enumerate(notes):
        b.append(T(20, y0 + ph + 58 + i * 18, s, 10.5, MUTE))
    save("fig03_fig2_redrawn.svg", W, H, b)


def fig04():
    """그림 5: average 선과 부류 선 평균."""
    W, H = 940, 430
    b = [T(20, 24, "원문 그림 5 의 σ 곡선: 그림의 「average」 선 대 부류 선 15 개의 평균 (선 꼭짓점 좌표로 읽음)", 14, weight="bold"),
         T(20, 44, "네모 = 표 1 의 SimpleNet 평균 (σ = 0.015 기본값). 원문은 「σ = 0.015 가 가장 좋다」 고 적는다.", 11, MUTE)]
    panels = [("I-AUROC", FIG5_I, FIG5_I_AVG, T1_ALL[SN][0], 98.9, 99.8, 70), ("P-AUROC", FIG5_P, FIG5_P_AVG, T1_ALL[SN][1], 97.4, 98.3, 500)]
    for name, dct, avg, tab, lo, hi, x0 in panels:
        pw, ph, y0 = 380, 270, 70
        fx = lambda i: x0 + i / 5 * pw
        fy = lambda v: y0 + ph - (v - lo) / (hi - lo) * ph
        b.append(T(x0, y0 - 8, name, 12, weight="bold"))
        for i, s in enumerate(SIGMA):
            b.append(L(fx(i), y0, fx(i), y0 + ph, LINE))
            b.append(T(fx(i), y0 + ph + 16, f"{s:.3f}", 10, MUTE, "middle"))
        v = lo
        while v <= hi + 1e-9:
            b.append(L(x0, fy(v), x0 + pw, fy(v), "#eeeeee"))
            b.append(T(x0 - 6, fy(v) + 4, f"{v:.1f}", 9, MUTE, "end"))
            v = round(v + 0.1, 1)
        m = [mean(dct[k][i] for k in CL) for i in range(6)]
        b.append(PL([(fx(i), fy(a)) for i, a in enumerate(avg)], A, 2))
        b.append(PL([(fx(i), fy(a)) for i, a in enumerate(m)], B, 2, "5 3"))
        for i, a in enumerate(avg):
            b.append(CIRC(fx(i), fy(a), 3, A))
        b.append(R(fx(1) - 4, fy(tab) - 4, 8, 8, INK))
        b.append(T(fx(1) + 8, fy(tab) + 4, f"표 1 {tab}", 10, INK))
        b.append(T(fx(1) + 8, fy(avg[1]) + (14 if name == "I-AUROC" else -8), f"average {avg[1]:.2f}", 10, A))
        b.append(T(fx(1) + 8, fy(m[1]) + 14, f"부류 평균 {m[1]:.2f}", 10, B))
        b.append(T(x0 + pw / 2, y0 + ph + 32, "σ (잡음 표준편차)", 10, MUTE, "middle"))
    b.append(T(20, H - 30, "파랑 실선 = 그림에 그려진 average 선. 빨강 점선 = 같은 그림의 부류 선 15 개를 내가 평균한 값.", 11, MUTE))
    b.append(T(20, H - 12, "I 는 σ = 0.015 한 점에서만 둘이 갈리고(0.12), P 는 모든 σ 에서 0.15 ~ 0.40 갈린다. 부류 평균으로는 I 는 0.010, P 는 0.025 가 가장 높다.", 11, MUTE))
    save("fig04_sigma.svg", W, H, b)


def fig05():
    """그림 4: 차원별 표준편차의 범위와 잡음 σ."""
    W, H = 1000, 330
    x0, pw = 200, 500
    hi = 0.16
    fx = lambda v: x0 + min(v, hi) / hi * pw
    b = [T(20, 24, "원문 그림 4 를 막대 좌표로 읽은 요약: 차원 1,536 개의 표준편차가 퍼진 범위 (내가 읽음)", 14, weight="bold"),
         T(20, 44, "가는 막대 = 최솟값 ~ 최댓값, 굵은 눈금 = 중앙값. 빨강 세로선 = 잡음 σ = 0.015 (모든 부류에 같은 값).", 11, MUTE)]
    for v in (0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16):
        b.append(L(fx(v), 64, fx(v), 270, "#eeeeee"))
        b.append(T(fx(v), 286, f"{v:.2f}", 10, MUTE, "middle"))
    b.append(L(fx(0.015), 60, fx(0.015), 272, B, 1.5, "4 3"))
    y = 72
    for k, v in FIG4.items():
        for kind, colr in (("local", D), ("adapted", A)):
            n, med, lo, hi_v, below = v[kind]
            b.append(T(x0 - 10, y + 11, f"{k} · {'사전학습 특징' if kind == 'local' else '적응 뒤'}", 11, anchor="end"))
            b.append(R(fx(lo), y + 4, max(fx(hi_v) - fx(lo), 1), 6, colr))
            b.append(R(fx(med) - 1.5, y, 3, 14, INK))
            extra = f"중앙값 {med:.3f}" + (f" · σ 보다 작은 차원 {below:.0f}" if kind == "local" else f" · 최솟값 {lo:.3f}")
            if hi_v > hi:
                extra += f" · 최댓값 {hi_v:.3f} (축 밖)"
            b.append(T(x0 + pw + 14, y + 11, extra, 10, MUTE))
            y += 24
        y += 2
    b.append(T(20, H - 14, "적응 뒤에는 네 부류 모두 σ 보다 작은 차원이 없다. 중앙값 대비 σ 는 0.25 (bottle) ~ 0.47 (carpet) 로 부류마다 다르다.", 11, MUTE))
    save("fig05_feature_std.svg", W, H, b)


def fig06():
    groups = [("표 2 · 쓰는 단계", [(n, i, p) for n, i, p in T2]),
              ("표 3 · 적응기 · 손실", [(n.replace("Ours-", ""), i, p) for n, i, p in T3]),
              ("표 4 · 백본", T4),
              ("그림 6 · 조각 크기 p (그림에서 읽음)", [(f"p = {p}", i, q) for p, i, q in FIG6])]
    W, H = 960, 700
    lo, sc, x0 = 92.5, 75, 250
    b = [T(20, 24, "끈 실험의 I-AUROC (괄호는 P-AUROC). 점선은 표 1 의 PatchCore 99.1 · DRAEM 98.0", 14, weight="bold"),
         T(20, 44, "모두 MVTec AD 시험 집합의 값이고, 어느 표에도 반복 수가 없다. 진하게 = 기본 설정.", 11, MUTE)]
    y = 70
    defaults = {"2+3", "Ours", "WideResNet50", "p = 3"}
    for g, rows in groups:
        b.append(T(20, y + 4, g, 12, weight="bold"))
        y += 14
        for n, i, p in rows:
            w = (i - lo) * sc
            b.append(R(x0, y, w, 18, A if n in defaults else "#9fb8d8"))
            b.append(T(x0 - 8, y + 14, n, 11, anchor="end"))
            b.append(T(x0 + w + 6, y + 14, f"{i:.2f}  ({p:.2f})" if g.startswith("그림") else f"{i:.1f}  ({p:.1f})", 10, MUTE))
            y += 24
        y += 12
    for v, lab, colr in ((99.1, "PatchCore 99.1", B), (98.0, "DRAEM 98.0", D)):
        x = x0 + (v - lo) * sc
        b.append(L(x, 76, x, y - 6, colr, 1, "4 3"))
        b.append(T(x, y + 8, lab, 10, colr, "middle"))
    b.append(T(20, H - 12, f"막대 왼쪽 끝 = {lo}. 축척 1 점 = {sc} px. 3 단계 하나만 써도 99.2 로 PatchCore 99.1 보다 0.1 높다.", 11, MUTE))
    save("fig06_ablation.svg", W, H, b)


def fig07():
    W, H = 900, 360
    b = [T(20, 24, "이 편의 자리 — 가짜 이상으로 판별기를 배우는 계열과 사전학습 특징 계열 (이 저장소의 노트 기준)", 14, weight="bold")]

    def box(x, y, w, t1, t2, colr):
        b.append(R(x, y, w, 52, "#ffffff", colr))
        b.append(T(x + w / 2, y + 22, t1, 12, INK, "middle", "bold"))
        b.append(T(x + w / 2, y + 40, t2, 10, MUTE, "middle"))

    box(20, 60, 200, "DRAEM (ICCV 2021)", "이미지에 가짜 결함, 분할 망", D)
    box(250, 60, 200, "CutPaste (CVPR 2021)", "조각을 잘라 붙여 분류", D)
    box(480, 60, 200, "SimpleNet (CVPR 2023)", "특징에 가우스 잡음, MLP 판별", B)
    box(710, 60, 170, "EfficientAD (WACV 2024)", "이 큰 틀의 마지막 칸", A)
    for x1, x2 in ((220, 250), (450, 480), (680, 710)):
        b.append(L(x1, 86, x2, 86, INK, 1.5))
    box(20, 170, 200, "SPADE · PaDiM", "정상 특징을 저장 · 가우스", D)
    box(250, 170, 200, "PatchCore (CVPR 2022)", "2 · 3 단계 조각 특징 + 뱅크", D)
    box(480, 170, 200, "RD (CVPR 2022)", "선생 부호기 · 학생 복호기", D)
    b.append(L(350, 170, 560, 112, MUTE, 1, "4 3"))
    b.append(T(570, 146, "특징 추출(식 1 ~ 3)을 PatchCore 에서 그대로 따른다", 10, MUTE))
    b.append(T(20, 262, "SimpleNet 은 PatchCore 의 조각 특징을 받고, 뱅크와 최근접 검색 대신 「FC 한 층 + 잡음 + MLP 판별기」 를 둔다.", 11, MUTE))
    b.append(T(20, 284, "가짜 결함을 이미지가 아니라 특징 공간에 만든다는 점이 DRAEM · CutPaste 와 갈린다. 같은 설정에서 이미지 공간 결함을 쓴 줄은", 11, MUTE))
    b.append(T(20, 304, "이 편의 끈 실험(표 2 ~ 4, 그림 5 ~ 7)에 들어 있지 않다.", 11, MUTE))
    save("fig07_lineage.svg", W, H, b)


if __name__ == "__main__":
    recount()
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07):
        f()
    print("\n그림 일곱을 썼다:", OUT)
