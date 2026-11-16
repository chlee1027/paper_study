# -*- coding: utf-8 -*-
"""EfficientAD 노트의 그림을 만들고, 노트가 인용하는 다시 계산한 값을 찍는다.

표준 라이브러리만 쓰고 바깥 데이터를 읽지 않는다. 값은 같은 폴더 data_efficientad.py 의 상수다.

  python make_figures.py

찍는 것: 표 10 ~ 15 의 평균 다시 내기와 표 2 · 표 10 대조, 모음별 1 위와 차, LOCO 의 「같은 몫」,
검출 순위와 위치 순위의 순위 상관, 모음 사이 순위 상관, 표 4 · 5 의 누적 대 하나씩 빼기,
표 3 의 폭과 표준편차, 배수 문장들, 표 17 의 GPU 별 순위, 그림 1 · 6 · 8 의 좌표 읽기 대조,
PDN · 자기부호기의 수용장 · 출력 크기 · 파라미터 · 곱셈-덧셈 수, WRN-101 의 1 ~ 3 단계 파라미터,
학습 이미지 평균 장수, 어려운 특징 손실이 고르는 원소 수, 가운데 자르기 넓이.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_efficientad import *  # noqa: E402,F401,F403

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "'Malgun Gothic','Noto Sans KR',sans-serif"
INK, MUTE, LINE = "#222222", "#666666", "#cccccc"
A, B, Y, D = "#2f6db3", "#c8553d", "#d9a21b", "#8a8a8a"  # 파랑 · 빨강 · 호박색 · 회색 (색각 이상 대비 검사 통과 셋)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(x, y, s, size=12, fill=INK, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" font-family="{FONT}">{esc(s)}</text>')


def R(x, y, w, h, fill, stroke="none", rx=0):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}"/>')


def L(x1, y1, x2, y2, stroke=LINE, width=1, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>'


def CIRC(x, y, r, fill, stroke="none"):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def mean(v):
    v = list(v)
    return sum(v) / len(v)


def r1(x):
    """반올림 폭 확인용: 인쇄 자리(소수 첫째) 기준 반올림 폭 0.05 를 넘는지."""
    return math.floor(x * 10 + 0.5) / 10


def ranks(vals):
    """큰 값이 1 위. 같은 값은 평균 순위."""
    order = sorted(range(len(vals)), key=lambda i: -vals[i])
    rk = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        for k in range(i, j + 1):
            rk[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return rk


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    ma, mb = mean(ra), mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den


# ---------------------------------------------------------------- 셈
def check_means():
    print("[셈 1] 표 10 ~ 15 의 평균 다시 내기 (LOCO = 구조 · 논리 평균, 전체 = MAD · VisA · LOCO 평균)")
    print("  인쇄 값은 각각 ±0.05 의 반올림 폭을 가지므로, 인쇄 값으로 낸 평균과 인쇄 평균의 차는 0.1 까지 반올림으로 설명된다")
    bad = 0
    worst = (0.0, "")
    for name, tab in METRIC_TABLES:
        for m, v in tab.items():
            mad, visa, s, l, loco, ov = v
            lo = (s + l) / 2
            o = (mad + visa + loco) / 3
            o2 = (mad + visa + lo) / 3
            for got, want, what in ((lo, loco, "LOCO"), (o, ov, "전체")):
                if abs(got - want) > worst[0]:
                    worst = (abs(got - want), f"{name} {m} {what} {want} 대 {got:.3f}")
                if abs(got - want) > 0.1 + 1e-9:
                    bad += 1
                    print(f"  {name} {m}: {what} {want} 대 다시 낸 {got:.3f}")
    print(f"  반올림 폭 0.1 밖: {bad} 칸. 가장 큰 차 {worst[0]:.3f} ({worst[1]})")
    same = 0
    for m in METHODS:
        a = T10[m]
        b = T2[m]
        if (a[0], a[4], a[1], a[5], a[3], a[2]) == b:
            same += 1
    print(f"  표 2 와 표 10: {same} / {len(METHODS)} 줄이 같다")
    same = sum(1 for m in METHODS if (T16[m][0], T16[m][1]) == (T10[m][5], T12[m][5]))
    print(f"  표 1 · 16 의 두 성능 열과 표 10 · 12 의 전체 평균: {same} / {len(METHODS)} 줄이 같다")
    lat_same = sum(1 for m in METHODS if abs(T16[m][2] - (round(T17[m][0]) if T17[m][0] >= 10 else T17[m][0])) < 1e-9
                   or abs(T16[m][2] - T17[m][0]) <= 0.5)
    print(f"  표 1 의 지연과 표 17 의 A6000 열: {lat_same} / {len(METHODS)} 줄이 반올림 폭 안")


def check_leads():
    print("\n[셈 2] 표 10 ~ 15 의 열마다 1 위와, EfficientAD 둘을 뺀 가장 센 상대와의 차")
    for name, tab in METRIC_TABLES:
        print(f"  {name}")
        for j, c in enumerate(COLS):
            best = max(tab[m][j] for m in METHODS)
            top = [m for m in METHODS if tab[m][j] == best]
            ob = max(tab[m][j] for m in OTHERS)
            ow = [m for m in OTHERS if tab[m][j] == ob]
            dS = tab["EfficientAD-S"][j] - ob
            dM = tab["EfficientAD-M"][j] - ob
            print(f"    {c:8s} 1 위 {best} {'/'.join(top):28s} 상대 최고 {ob} {'/'.join(ow):14s} S {dS:+.1f} · M {dM:+.1f}")


def check_loco_parts():
    print("\n[셈 3] 「LOCO 에서의 앞섬은 논리 · 구조가 같은 몫」 (표 2, 구조 j=2 · 논리 j=3 · LOCO j=4)")
    for ours in OURS:
        ast = T10["AST"]
        o = T10[ours]
        print(f"  {ours} - AST: LOCO {o[4] - ast[4]:+.1f} = 논리 {o[3] - ast[3]:+.1f} 와 구조 {o[2] - ast[2]:+.1f} 의 평균")
        bl = max(T10[m][3] for m in OTHERS)
        bs = max(T10[m][2] for m in OTHERS)
        bl_n = [m for m in OTHERS if T10[m][3] == bl]
        bs_n = [m for m in OTHERS if T10[m][2] == bs]
        print(f"  {ours} - 열마다 가장 센 상대: 논리 {o[3] - bl:+.1f} ({'/'.join(bl_n)} {bl}), 구조 {o[2] - bs:+.1f} ({'/'.join(bs_n)} {bs})")
        print(f"     GCAD 묶음판의 논리 {GCAD_LOCO_LOGIC['ensemble']} 과는 {o[3] - GCAD_LOCO_LOGIC['ensemble']:+.1f}")
    lo = T10["EfficientAD-S"]
    print(f"  LOCO 둘째 자리: {sorted(((T10[m][4], m) for m in OTHERS), reverse=True)[:3]}")


def check_ranks():
    print("\n[셈 4] 순위 상관 (스피어만, 같은 값은 평균 순위)")
    det = [T10[m][5] for m in OTHERS]
    loc = [T12[m][5] for m in OTHERS]
    print(f"  상대 여덟: 검출 AU-ROC 대 AU-PRO 30% (전체 평균) rho = {spearman(det, loc):+.3f}")
    for m in OTHERS:
        print(f"    {m:13s} 검출 {ranks(det)[OTHERS.index(m)]:.0f} 위 · 위치 {ranks(loc)[OTHERS.index(m)]:.0f} 위")
    det10 = [T10[m][5] for m in METHODS]
    loc10 = [T12[m][5] for m in METHODS]
    print(f"  열 방법 모두: rho = {spearman(det10, loc10):+.3f}")
    for (a, ja), (b, jb) in ((("MAD", 0), ("VisA", 1)), (("MAD", 0), ("LOCO", 4)), (("VisA", 1), ("LOCO", 4))):
        for who, lst in (("열 방법", METHODS), ("상대 여덟", OTHERS)):
            x = [T10[m][ja] for m in lst]
            y = [T10[m][jb] for m in lst]
            print(f"  이미지 AU-ROC {a} 대 {b} ({who}): rho = {spearman(x, y):+.3f}")
    for j, c in ((0, "MAD"), (1, "VisA"), (4, "LOCO")):
        v = [T10[m][j] for m in METHODS]
        rk = ranks(v)
        print(f"  {c} 순위: " + ", ".join(f"{m} {rk[i]:.1f}" for i, m in sorted(enumerate(METHODS), key=lambda t: rk[t[0]])))
    for c, j in (("MAD", 0), ("VisA", 1), ("LOCO", 4)):
        v = [T10[m][j] for m in OTHERS if m not in ("GCAD", "S-T")]
        print(f"  {c}: GCAD · S-T 를 뺀 상대 여섯의 폭 {min(v)} ~ {max(v)} = {max(v) - min(v):.1f} 점")


def check_ablation():
    print("\n[셈 5] 표 4 (누적) 대 표 5 (하나씩 빼기), EfficientAD-S")
    gains = [round(T4[i][1] - T4[i - 1][1], 1) for i in range(1, 4)]
    drops = [round(T5[0][1] - T5[i][1], 1) for i in range(1, 4)]
    for (n, _), g, dd in zip(T4[1:], gains, drops):
        print(f"  {n:16s} 누적 표의 오름 {g:+.1f} · 뺀 표의 내림 {dd:.1f}")
    print(f"  누적 오름의 합 {sum(gains):.1f}, 하나씩 뺀 내림의 합 {sum(drops):.1f}")
    print(f"  S 의 표준편차 0.06 (다섯 번) 대비: 가장 작은 몫 0.4 = {0.4 / 0.06:.1f} 배")
    t1 = [("FastFlow", 90.0), ("DSR", 90.8), ("PatchCore", 91.1), ("PatchCoreEns", 92.1), ("AST", 92.4)]
    m = [round(t1[i][1] - t1[i - 1][1], 1) for i in range(1, 5)]
    print(f"  표 1 의 잇단 줄 차 (FastFlow -> DSR -> PatchCore -> Ens -> AST): {m}")
    print(f"  어려운 특징 손실 1.0 이 이 넷 모두 이상인가: {all(1.0 >= x for x in m)} · 0.7 로는: {all(0.7 >= x for x in m)}")
    print("[셈 5b] 표 3 (EfficientAD-M)")
    for name, rows, dflt in (("a", T3_A, DEFAULT_A), ("b", T3_B, DEFAULT_B), ("p_hard", T3_P, DEFAULT_P)):
        v = [x for _, x in rows]
        best = max(v)
        print(f"  {name}: 폭 {min(v)} ~ {best} ({best - min(v):.1f} 점), 최댓값 자리 {[k for k, x in rows if x == best]}, 기본값 {dflt} 의 값 {dict(rows)[dflt]}")
    v = [x for _, x in T3_A[:]] + [x for _, x in T3_B]
    print(f"  a · b 여섯씩의 폭 0.2 · 0.2 를 M 의 표준편차 0.09 로 나누면 {0.2 / 0.09:.1f}")
    print(f"  p_hard = 0 (손실을 끔) 은 M 에서 {dict(T3_P)[0.0]} = 기본값보다 {dict(T3_P)[0.0] - dict(T3_P)[0.999]:+.1f}, S 의 표 5 는 -0.7")
    print("[셈 5c] 표 9 의 백본 셋 폭")
    for c, d in T9.items():
        print("  " + c + ": " + ", ".join(f"{m} {max(v) - min(v):.1f}" for m, v in d.items()))


def check_ratios():
    print("\n[셈 6] 배수 문장들")
    s, ast, st, ff = T16["EfficientAD-S"], T16["AST"], T16["S-T"], T16["FastFlow"]
    print(f"  결론: 지연 AST/S = {ast[2] / s[2]:.2f} (표 17: {T17['AST'][0] / T17['EfficientAD-S'][0]:.2f}), 처리량 S/AST = {s[3] / ast[3]:.2f}")
    print(f"  부록 E: FastFlow 파라미터 / S-T = {ff[4] / st[4]:.2f} 배, (차 / S-T) = {(ff[4] - st[4]) / st[4]:.2f}")
    print(f"          처리량 FastFlow / S-T = {ff[3] / st[3]:.2f} 배, (차 / S-T) = {(ff[3] - st[3]) / st[3]:.2f}")
    print(f"          FLOPs S-T / AST = {st[5] / ast[5]:.2f} 배, 「2000 % 넘게 많다」 = (차 / AST) {100 * (st[5] - ast[5]) / ast[5]:.0f} %")
    print(f"          지연 S-T / AST: 표 1 로 {100 * (st[2] / ast[2] - 1):.1f} % · 표 17 로 {100 * (T17['S-T'][0] / T17['AST'][0] - 1):.1f} % 높다 (원문 「42 %」)")
    print(f"  처리량 S 614 장/초 = 16 장 묶음 한 번에 {16 / 614 * 1000:.1f} ms, 장당 {1000 / 614:.2f} ms (지연 2.2 ms)")
    print(f"  오류(100 - AU-ROC) 전체 평균: S {100 - s[0]:.1f}, AST {100 - ast[0]:.1f} -> AST 대비 줄어든 비율 {(s[0] - ast[0]) / (100 - ast[0]) * 100:.1f} %")
    print(f"  GPU 메모리 S 100 MB 는 다음으로 작은 DSR 314 MB 의 {100 / 314 * 100:.1f} %")
    print(f"  FLOPs: S {s[5]} 은 SimpleNet {T16['SimpleNet'][5]} 의 {s[5] / T16['SimpleNet'][5]:.2f} 배, PatchCore 백본 {T16['PatchCore'][5]} 의 {s[5] / T16['PatchCore'][5]:.2f} 배")
    print(f"  재현: AST {REPRO['AST'][0]} -> {REPRO['AST'][1]} ({REPRO['AST'][1] - REPRO['AST'][0]:+.1f}), DSR {REPRO['DSR'][0]} -> {REPRO['DSR'][1]} ({REPRO['DSR'][1] - REPRO['DSR'][0]:+.1f})")
    print(f"  SimpleNet: 원문 I {SIMPLENET_PAPER['I']} 대 이 편 MAD {T10['SimpleNet'][0]} ({T10['SimpleNet'][0] - SIMPLENET_PAPER['I']:+.1f})")
    print(f"  조기 종료를 켠 EfficientAD MAD {EAD_MAD_EARLY_STOP} 대 M {T10['EfficientAD-M'][0]} ({EAD_MAD_EARLY_STOP - T10['EfficientAD-M'][0]:+.1f}) · S {T10['EfficientAD-S'][0]} ({EAD_MAD_EARLY_STOP - T10['EfficientAD-S'][0]:+.1f})")


def check_gpu_rank():
    print("\n[셈 7] 표 17: GPU 마다 지연 순위가 A6000 과 다른 자리")
    base = sorted(T17, key=lambda m: T17[m][0])
    for g, gpu in enumerate(GPUS):
        order = sorted(T17, key=lambda m: T17[m][g])
        diff = [(i, a, b) for i, (a, b) in enumerate(zip(base, order)) if a != b]
        print(f"  {gpu:12s} " + ("같다" if not diff else "; ".join(f"{i + 1} 위 {b} (A6000 은 {a})" for i, a, b in diff)))
    for g in (2, 3):
        print(f"  {GPUS[g]}: DSR {T17['DSR'][g]} 대 FastFlow {T17['FastFlow'][g]} -> DSR 이 {100 * (1 - T17['DSR'][g] / T17['FastFlow'][g]):.1f} % 짧다")
    print(f"  S 의 가장 느린 GPU / 가장 빠른 GPU = {max(T17['EfficientAD-S']) / min(T17['EfficientAD-S']):.2f}")
    worst_s = max(T17["EfficientAD-S"])
    print(f"  S 의 가장 느린 값 {worst_s} ms 대 상대의 가장 빠른 값 GCAD {min(T17['GCAD'])} ms -> {min(T17['GCAD']) / worst_s:.2f} 배")


def check_figures():
    print("\n[셈 8] 그림 1 · 8 · 6 을 좌표로 읽어 표와 맞대기")
    x0, x3 = FIG1_X
    y88, y96 = FIG1_Y
    for m, (x, y) in FIG1.items():
        lat = 10 ** (3 * (x - x0) / (x3 - x0))
        au = 88 + (y88 - y) / (y88 - y96) * 8
        print(f"  그림 1 {m:13s} 지연 {lat:6.2f} (표 17 {T17[m][0]}) · AU-ROC {au:.2f} (표 1 {T16[m][0]})"
              + ("" if m in FIG1_LABELLED else "  <- 이름표 없음"))
    bottom = 88 + (y88 - FIG1_AXIS_BOTTOM) / (y88 - y96) * 8
    print(f"  그림 1 의 상자 아래 끝 = AU-ROC {bottom:.2f}")
    for k in ("a", "b"):
        xa, xb = FIG8_X[k]
        (va, ya), (vb, yb) = FIG8_Y[k]
        md = 0.0
        for m, (x, y) in FIG8[k].items():
            thr = (x - xa) / (xb - xa) * 1000
            val = va + (ya - y) / (ya - yb) * (vb - va)
            ref = T16[m][0] if k == "a" else T16[m][1]
            md = max(md, abs(val - ref))
            print(f"  그림 8({k}) {m:13s} 처리량 {thr:6.1f} (표 {T16[m][3]}) · 값 {val:.2f} (표 {ref})")
        print(f"  그림 8({k}) 표와의 가장 큰 차 {md:.2f}")
    y0, y2 = FIG6_Y
    for m, tops in FIG6.items():
        vals = [10 ** (2 * (y0 - t) / (y0 - y2)) for t in tops]
        print(f"  그림 6 {m:13s} " + " · ".join(f"{v:.1f}" for v in vals) + f"  (표 17 {T17[m]})")


def conv_out(n, k, s, p):
    return (n + 2 * p - k) // s + 1


PDN_S = [("Conv-1", "conv", 4, 1, 3, 128), ("AvgPool-1", "pool", 2, 2, 1, None), ("Conv-2", "conv", 4, 1, 3, 256),
         ("AvgPool-2", "pool", 2, 2, 1, None), ("Conv-3", "conv", 3, 1, 1, 256), ("Conv-4", "conv", 4, 1, 0, 384)]
PDN_M = [("Conv-1", "conv", 4, 1, 3, 256), ("AvgPool-1", "pool", 2, 2, 1, None), ("Conv-2", "conv", 4, 1, 3, 512),
         ("AvgPool-2", "pool", 2, 2, 1, None), ("Conv-3", "conv", 1, 1, 0, 512), ("Conv-4", "conv", 3, 1, 1, 512),
         ("Conv-5", "conv", 4, 1, 0, 384), ("Conv-6", "conv", 1, 1, 0, 384)]


def pdn(layers, out_ch=None, n=256, pad=True, last_k=1):
    """수용장 · 출력 크기 · 파라미터 · 곱셈-덧셈. out_ch 를 주면 마지막 last_k 개 합성곱의 출력을 그 값으로 바꾼다(학생)."""
    layers = [list(l) for l in layers]
    if out_ch:
        convs = [i for i, l in enumerate(layers) if l[1] == "conv"]
        for i in convs[-last_k:]:
            layers[i][5] = out_ch
    rf, jump, c, size = 1, 1, 3, n
    params = macs = 0
    rows = []
    for name, kind, k, s, p, ch in layers:
        p = p if pad else 0
        rf += (k - 1) * jump
        jump *= s
        size = conv_out(size, k, s, p)
        if kind == "conv":
            params += c * ch * k * k + ch
            macs += size * size * ch * c * k * k
            c = ch
        rows.append((name, size, rf))
    return rows, rf, size, params, macs


AE_ENC = [(4, 2, 1, 32), (4, 2, 1, 32), (4, 2, 1, 64), (4, 2, 1, 64), (4, 2, 1, 64), (8, 1, 0, 64)]
AE_DEC = [(3, 4), (8, 4), (15, 4), (32, 4), (63, 4), (127, 4), (64, 3)]  # (보간 뒤 크기, 합성곱 크기)


def ae(final=64):
    size, c, params, macs, sizes = 256, 3, 0, 0, []
    for k, s, p, ch in AE_ENC:
        size = conv_out(size, k, s, p)
        params += c * ch * k * k + ch
        macs += size * size * ch * c * k * k
        c = ch
        sizes.append(size)
    latent = size * size * c
    for i, (up, k) in enumerate(AE_DEC):
        up = final if i == len(AE_DEC) - 1 else up
        pad = 2 if k == 4 else 1
        size = conv_out(up, k, 1, pad)
        params += c * 64 * k * k + 64
        macs += size * size * 64 * c * k * k
        sizes.append(size)
    params += 64 * 384 * 9 + 384  # DecConv-8 (3x3, 패딩 1)
    macs += size * size * 384 * 64 * 9
    return params, macs, sizes, latent


def check_arch():
    print("\n[셈 9] PDN 과 자기부호기 (표 6 · 7 · 8, 256 x 256 입력)")
    for nm, layers, last in (("S", PDN_S, 1), ("M", PDN_M, 2)):
        for pad in (True, False):
            rows, rf, size, pt, mt = pdn(layers, pad=pad)
            _, _, _, ps, ms = pdn(layers, out_ch=768, pad=pad, last_k=last)
            print(f"  PDN-{nm} 패딩 {'있음' if pad else '없음'}: 수용장 {rf}, 출력 {size} x {size}, "
                  f"선생 파라미터 {pt:,} · 학생 {ps:,}, 곱셈-덧셈 선생 {mt / 1e9:.2f} G · 학생 {ms / 1e9:.2f} G")
            if pad:
                print("     층마다 (크기, 수용장): " + ", ".join(f"{n} {s} / {r}" for n, s, r in rows))
    for final in (64, 56):
        pa, ma, sizes, latent = ae(final)
        print(f"  자기부호기 (마지막 보간 {final}): 파라미터 {pa:,}, 곱셈-덧셈 {ma / 1e9:.2f} G, 크기 {sizes}, 잠재 {latent}")
    for nm, layers, last in (("S", PDN_S, 1), ("M", PDN_M, 2)):
        for pad, final in ((True, 64), (False, 56)):
            _, _, _, pt, mt = pdn(layers, pad=pad)
            _, _, _, ps, ms = pdn(layers, out_ch=768, pad=pad, last_k=last)
            pa, ma, _, _ = ae(final)
            tot_p = pt + ps + pa
            tot_m = mt + ms + ma
            print(f"  EfficientAD-{nm} 패딩 {'있음' if pad else '없음'}: 파라미터 {tot_p:,} ({tot_p / 1e6:.2f} 백만, 표 16 {T16['EfficientAD-' + nm][4]}), "
                  f"곱셈-덧셈 {tot_m / 1e9:.1f} G -> 그 두 배 {2 * tot_m / 1e9:.1f} G (표 16 FLOPs {T16['EfficientAD-' + nm][5]})")
    e = 384 * 64 * 64
    print(f"  어려운 특징 손실: 원소 {e:,} 개 중 0.1 % = {e * 0.001:,.0f} 개 (패딩 없는 56 x 56 이면 {384 * 56 * 56 * 0.001:,.0f})")
    print(f"  0.1^3 = {0.1 ** 3:.3f}")
    # WRN-101-2 의 줄기 + 1 ~ 3 단계: WRN-50-2 의 같은 몫에 3 단계 병목 17 개를 더한다
    blk = 1024 * 512 + 512 * 512 * 9 + 512 * 1024 + 2 * (512 + 512 + 1024)
    print(f"  WRN-101-2 1 ~ 3 단계 = WRN-50-2 의 {WRN50_STAGE123:,} + 17 x {blk:,} = {WRN50_STAGE123 + 17 * blk:,} (원문 「83 million」)")


def check_misc():
    print("\n[셈 10] 그 밖")
    known = TRAIN_IMAGES["MAD"] + TRAIN_IMAGES["VisA"]
    lo, hi = 32 * 438.5, 32 * 439.5
    print(f"  평균 439 장 x 32 = {32 * 439:,}. MVTec AD + VisA = {known:,} -> LOCO 몫 {lo - known:,.0f} ~ {hi - known:,.0f} 장 (439 의 반올림 폭)")
    print(f"  가운데 자르기: (224 / 256)^2 = {(224 / 256) ** 2 * 100:.2f} %  (원문 76.6 %), 변 비 {224 / 256 * 100:.1f} %")
    print(f"  학습 70,000 반복 (묶음 1): 평균 439 장이면 {70000 / 439:.0f} 에폭, toothbrush 60 장이면 {70000 / 60:.0f}, hazelnut 391 장이면 {70000 / 391:.0f}")
    print(f"  학습률을 줄이는 자리 66,500 / 70,000 = {66500 / 70000 * 100:.0f} %")
    print(f"  20 분에 70,000 반복이면 반복당 {20 * 60 / 70000 * 1000:.1f} ms")
    print(f"  증류: 60,000 반복 x 16 장 = {60000 * 16:,} 장 (ImageNet 학습 1,281,167 장의 {60000 * 16 / 1281167 * 100:.0f} %)")
    print(f"  전체 평균에서 LOCO 논리의 무게 = 1/3 x 1/2 = {1 / 6:.3f}")


# ---------------------------------------------------------------- 그림
SHORT = {"EfficientAD-S": "EAD-S", "EfficientAD-M": "EAD-M", "PatchCoreEns": "PatchCoreEns"}


def fig01():
    """모음 · 지표마다 EfficientAD-M 과 가장 센 상대의 차."""
    panels = [("이미지 AU-ROC (표 10)", T10), ("AU-PRO 30% (표 12)", T12), ("픽셀 AU-PRC (표 15)", T15)]
    cols = [(0, "MVTec AD"), (1, "VisA"), (2, "LOCO 구조"), (3, "LOCO 논리"), (5, "전체 평균")]
    W, H = 1000, 470
    b = [T(20, 26, "EfficientAD-M 에서 상대 여덟 가운데 가장 센 값을 뺀 차 (점, 내 뺄셈)", 15, weight="bold"),
         T(20, 46, "파랑 = EfficientAD-M 이 높음 · 빨강 = 낮음. 괄호는 그 칸의 가장 센 상대. 원문은 「검출과 위치 모두 큰 차이로 앞선다」 고 적는다.", 11, MUTE)]
    sc = 18
    for pi, (name, tab) in enumerate(panels):
        x0 = 120 + pi * 300
        b.append(T(x0 + 60, 78, name, 12, weight="bold", anchor="middle"))
        b.append(L(x0 + 60, 90, x0 + 60, 90 + 70 * len(cols) - 10, INK))
        for ci, (j, cname) in enumerate(cols):
            y = 96 + ci * 70
            if pi == 0:
                b.append(T(20, y + 22, cname, 12))
            ob = max(tab[m][j] for m in OTHERS)
            who = [m for m in OTHERS if tab[m][j] == ob]
            d = round(tab["EfficientAD-M"][j] - ob, 1)
            w = d * sc
            w = max(min(w, 180), -60)
            b.append(R(min(x0 + 60, x0 + 60 + w), y + 10, max(abs(w), 2), 18, A if d > 0 else B, rx=2))
            lab = f"{d:+.1f}"
            if d > 0:
                b.append(T(x0 + 60 + w + 6, y + 23, lab, 11, INK))
            else:
                b.append(T(x0 + 60 + w - 6, y + 23, lab, 11, INK, "end"))
            b.append(T(x0 + 60 + 4, y + 44, f"({'/'.join(who)} {ob})", 10, MUTE))
    b.append(T(20, H - 30, "축척 1 점 = 18 px. EfficientAD-S 로 보면 MVTec AD AU-ROC 에서 PatchCoreEns 보다 0.5,", 11, MUTE))
    b.append(T(20, H - 12, "AST 보다 0.1 낮다. 세 지표 모두 EfficientAD 가 다섯 번 실행 평균이고, 상대는 반복 수가 적혀 있지 않다(AST 는 MVTec AD 다섯 번).", 11, MUTE))
    save("fig01_margin_by_collection.svg", W, H, b)


def slope(b, x1, x2, y0, step, left, right, lt, rt, highlight):
    n = len(left)
    b.append(T(x1, y0 - 22, lt, 12, weight="bold", anchor="middle"))
    b.append(T(x2, y0 - 22, rt, 12, weight="bold", anchor="middle"))
    rl, rr = ranks([v for _, v in left]), ranks([v for _, v in right])
    for i, (m, v) in enumerate(left):
        j = [k for k, (mm, _) in enumerate(right) if mm == m][0]
        ya, yb = y0 + (rl[i] - 1) * step, y0 + (rr[j] - 1) * step
        colr = A if m in highlight else D
        b.append(L(x1, ya, x2, yb, colr, 2.5 if m in highlight else 1.5))
        b.append(CIRC(x1, ya, 4.5, colr, "#ffffff"))
        b.append(CIRC(x2, yb, 4.5, colr, "#ffffff"))
        b.append(T(x1 - 10, ya + 4, f"{SHORT.get(m, m)} {v}", 10.5, INK, "end"))
        b.append(T(x2 + 10, yb + 4, f"{right[j][1]} {SHORT.get(m, m)}", 10.5, INK))


def fig02():
    """순위 바뀜: 검출 대 위치 (상대 여덟 + EfficientAD 둘)."""
    W, H = 760, 450
    b = [T(20, 26, "검출 순위와 위치 순위 (표 10 · 12 의 전체 평균으로 내가 순위를 매김)", 15, weight="bold"),
         T(20, 46, "위가 1 위. 파랑 = EfficientAD 둘.", 11, MUTE)]
    left = [(m, T10[m][5]) for m in METHODS]
    right = [(m, T12[m][5]) for m in METHODS]
    slope(b, 260, 470, 96, 32, left, right, "검출 AU-ROC", "AU-PRO 30%", OURS)
    rho = spearman([T10[m][5] for m in OTHERS], [T12[m][5] for m in OTHERS])
    b.append(T(20, H - 30, f"상대 여덟만 두고 순위 상관(스피어만)을 내면 {rho:+.2f} 이다. 검출 꼴찌 GCAD 가 위치 2 위, 검출 1 위 AST 가 위치 9 위다.", 11, MUTE))
    b.append(T(20, H - 12, "모두 한 번씩의 값이고(EfficientAD 만 다섯 번 평균), 0.1 점 차로도 순위가 갈린다.", 11, MUTE))
    save("fig02_rank_det_vs_loc.svg", W, H, b)


def fig03():
    """같은 이미지 AU-ROC 의 순위: MVTec AD -> VisA -> LOCO. 열마다 이름을 붙인다."""
    W, H = 1000, 470
    b = [T(20, 26, "같은 지표(이미지 AU-ROC, 표 10)의 순위가 데이터 모음마다 바뀐다 (내가 순위를 매김)", 15, weight="bold"),
         T(20, 46, "위가 1 위. 파랑 = EfficientAD 둘. 표 2 아래 원문: 「MVTec AD 만으로 방법을 개발하면 남은 몇 장의 오분류에 설계를 과적합하기 쉽다」.", 11, MUTE)]
    cols = [("MVTec AD", 0, 230), ("VisA", 1, 470), ("LOCO", 4, 760)]
    y0, step, lw = 104, 32, 150
    pos = {}
    for name, j, x in cols:
        vals = [T10[m][j] for m in METHODS]
        rk = ranks(vals)
        b.append(T(x, y0 - 26, name, 12, weight="bold", anchor="middle" if j == 0 else "start"))
        for i, m in enumerate(METHODS):
            pos[(j, m)] = (x, y0 + (rk[i] - 1) * step)
    for (n1, j1, x1), (n2, j2, x2) in zip(cols[:-1], cols[1:]):
        for m in METHODS:
            _, ya = pos[(j1, m)]
            _, yb = pos[(j2, m)]
            xa = x1 if j1 == 0 else x1 + lw
            colr = A if m in OURS else D
            b.append(L(xa, ya, x2, yb, colr, 2.5 if m in OURS else 1.5))
    for name, j, x in cols:
        for m in METHODS:
            xx, yy = pos[(j, m)]
            colr = A if m in OURS else D
            b.append(CIRC(xx, yy, 4.5, colr, "#ffffff"))
            if j == 0:
                b.append(T(xx - 10, yy + 4, f"{SHORT.get(m, m)} {T10[m][j]}", 10.5, INK, "end"))
            else:
                b.append(T(xx + 10, yy + 4, f"{T10[m][j]} {SHORT.get(m, m)}", 10.5, INK))
                if j == 1:
                    b.append(L(xx + lw - 8, yy, xx + lw, yy, colr, 2.5 if m in OURS else 1.5))
    rr = lambda a, c, lst: spearman([T10[m][a] for m in lst], [T10[m][c] for m in lst])
    b.append(T(20, H - 30, f"순위 상관(스피어만): 열 방법 MAD-VisA {rr(0, 1, METHODS):+.2f} · MAD-LOCO {rr(0, 4, METHODS):+.2f} · VisA-LOCO {rr(1, 4, METHODS):+.2f}. "
               f"상대 여덟만 두면 {rr(0, 1, OTHERS):+.2f} · {rr(0, 4, OTHERS):+.2f} · {rr(1, 4, OTHERS):+.2f}.", 11, MUTE))
    b.append(T(20, H - 12, "GCAD · S-T 를 뺀 상대 여섯의 폭은 MVTec AD 2.4 점, VisA 9.8 점, LOCO 5.8 점이다. 한 번씩의 값이다(EfficientAD 만 다섯 번 평균).", 11, MUTE))
    save("fig03_rank_across_collections.svg", W, H, b)


def fig04():
    """표 4 · 5: 누적 대 하나씩 빼기."""
    W, H = 1000, 380
    b = [T(20, 26, "구성 요소의 몫: 차례로 더한 표 4 와 하나씩 뺀 표 5 (EfficientAD-S, 세 모음 평균 이미지 AU-ROC)", 15, weight="bold"),
         T(20, 46, "막대 길이 = 점수 차 (점). 비교 잣대: EfficientAD-S 다섯 번 실행의 표준편차는 0.06 점이다(표 1). 두 표가 몇 번 실행인지는 적혀 있지 않다.", 11, MUTE)]
    comps = ["지도 정규화", "어려운 특징 손실", "사전학습 벌점"]
    gains = [round(T4[i][1] - T4[i - 1][1], 1) for i in range(1, 4)]
    drops = [round(T5[0][1] - T5[i][1], 1) for i in range(1, 4)]
    x0, sc = 260, 260
    b.append(T(x0, 78, "0", 10, MUTE, "middle"))
    for v in (0.5, 1.0):
        b.append(L(x0 + v * sc, 84, x0 + v * sc, 300, "#eeeeee"))
        b.append(T(x0 + v * sc, 78, f"{v:.1f}", 10, MUTE, "middle"))
    b.append(L(x0, 84, x0, 300, INK))
    for i, (c, g, d) in enumerate(zip(comps, gains, drops)):
        y = 96 + i * 68
        b.append(T(x0 - 12, y + 26, c, 12, anchor="end"))
        b.append(R(x0, y + 6, g * sc, 18, A, rx=2))
        b.append(T(x0 + g * sc + 6, y + 20, f"표 4 에서 더할 때 +{g:.1f}", 11, INK))
        b.append(R(x0, y + 30, d * sc, 18, Y, rx=2))
        b.append(T(x0 + d * sc + 6, y + 44, f"표 5 에서 뺄 때 -{d:.1f}", 11, INK))
    b.append(T(20, H - 48, f"더한 몫의 합 {sum(gains):.1f} (93.2 -> 95.4) 과 뺀 몫의 합 {sum(drops):.1f} 이 다르다: 셋이 서로 겹치는 몫이 있다.", 11, MUTE))
    b.append(T(20, H - 30, "본문의 「어려운 특징 손실 하나로 +1.0, 표 1 의 잇단 상대 사이 차 이상」 은 더한 차례의 값이다. 뺀 값 0.7 로는 FastFlow -> DSR 0.8 · PatchCore -> Ens 1.0 보다 작다.", 11, MUTE))
    b.append(T(20, H - 12, "자기부호기(논리 이상 갈래)를 빼거나 PDN 을 원래 WRN-101 특징으로 바꾼 줄은 두 표 어디에도 없다.", 11, MUTE))
    save("fig04_ablation.svg", W, H, b)


def fig05():
    """비용 지표 셋: 순서가 서로 다르다. 작은 그림 셋, 축은 그림마다 로그."""
    W, H = 1000, 500
    b = [T(20, 26, "같은 열 방법을 비용 지표 셋으로 늘어놓으면 순서가 다르다 (표 16 · 17, RTX A6000)", 15, weight="bold"),
         T(20, 46, "막대는 로그 눈금. 원문은 「파라미터 수와 FLOPs 는 지연의 대리 지표로 오해를 부른다」 고 적는다. PatchCore 둘은 kNN 몫을 뺀 백본 값.", 11, MUTE)]
    panels = [("지연 ms", 2, 1, 200), ("파라미터 백만", 4, 1, 200), ("FLOPs 10^9", 5, 10, 10000)]
    order = sorted(METHODS, key=lambda m: T17[m][0])
    for pi, (name, j, lo, hi) in enumerate(panels):
        x0, pw = 140 + pi * 290, 210
        fx = lambda v: x0 + (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * pw
        b.append(T(x0, 78, name, 12, weight="bold"))
        d = lo
        while d <= hi + 1e-9:
            b.append(L(fx(d), 86, fx(d), 86 + 33 * len(order), "#eeeeee"))
            b.append(T(fx(d), 100 + 33 * len(order), f"{d:g}", 9, MUTE, "middle"))
            d *= 10
        vals = {m: (T17[m][0] if j == 2 else T16[m][j]) for m in METHODS}
        rk = ranks([-vals[m] for m in METHODS])
        for i, m in enumerate(order):
            y = 90 + i * 33
            if pi == 0:
                b.append(T(x0 - 10, y + 15, SHORT.get(m, m), 11, anchor="end"))
            v = vals[m]
            b.append(R(x0, y + 4, max(fx(v) - x0, 2), 16, A if m in OURS else D, rx=2))
            b.append(T(fx(v) + 5, y + 16, f"{v:g} ({rk[METHODS.index(m)]:.0f})", 10, INK))
    b.append(T(20, H - 30, "괄호 = 그 지표에서 작은 쪽부터 센 순위. 줄은 지연이 짧은 차례. EfficientAD-S 의 FLOPs 76 은 SimpleNet 38 의 2 배, PatchCore 백본 41 의 1.9 배인데", 11, MUTE))
    b.append(T(20, H - 12, "지연은 SimpleNet 의 0.18 배다. S-T 는 FLOPs 가 가장 많고(4,468, 괄호 순위 10) 지연은 9 위다.", 11, MUTE))
    save("fig05_cost_metrics.svg", W, H, b)


def fig06():
    """PDN 층마다 출력 크기와 수용장."""
    rows, rf, size, _, _ = pdn(PDN_S)
    rows_np, _, size_np, _, _ = pdn(PDN_S, pad=False)
    W, H = 1000, 300
    b = [T(20, 26, "PDN-S 의 층마다 출력 크기와 수용장 (표 6 의 보폭 · 커널 · 패딩으로 내가 셈, 256 x 256 입력)", 15, weight="bold"),
         T(20, 46, "본문 「출력 하나의 수용장이 33 x 33」 과 알고리즘 1 의 「384 x 64 x 64」 는 패딩이 있을 때 맞는다. 시간을 잰 설정은 패딩을 끈 것이다.", 11, MUTE)]
    x = 30
    bw = 145
    for i, ((n, s, r), (_, s2, _)) in enumerate(zip(rows, rows_np)):
        xx = x + i * (bw + 15)
        b.append(R(xx, 70, bw, 120, "#f6f6f6", LINE, rx=4))
        b.append(T(xx + bw / 2, 92, n, 12, weight="bold", anchor="middle"))
        k = PDN_S[i]
        desc = f"{k[2]}x{k[2]} {'합성곱' if k[1] == 'conv' else '평균 풀링'}, 보폭 {k[3]}, 패딩 {k[4]}"
        b.append(T(xx + bw / 2, 110, desc, 9.5, MUTE, "middle"))
        b.append(T(xx + bw / 2, 136, f"패딩 있음 {s} x {s}", 11, A, "middle"))
        b.append(T(xx + bw / 2, 156, f"패딩 없음 {s2} x {s2}", 11, B, "middle"))
        b.append(T(xx + bw / 2, 178, f"수용장 {r}", 11, INK, "middle"))
    b.append(T(20, 222, f"마지막 크기: 패딩 있음 {size} x {size}, 패딩 없음 {size_np} x {size_np}. 패딩을 끄면 원소 수가 {(size_np / size) ** 2 * 100:.1f} % 로 준다.", 11, INK))
    b.append(T(20, 242, "부록 E 는 「패딩을 끄면 PDN 통과가 80 µs 빨라지고 검출은 나빠지지 않는다」 고 적고, 표의 성능은 패딩을 끈 설정의 값이라 적는다.", 11, MUTE))
    b.append(T(20, 262, "패딩을 끈 PDN 의 출력이 56 x 56 이면 자기부호기 출력(표 8, 64 x 64)과 크기가 다르다. 둘을 어떻게 맞췄는지 원문에 적혀 있지 않다.", 11, MUTE))
    b.append(T(20, 282, "곱셈-덧셈으로 센 계산량의 두 배가 표 16 의 FLOPs 76 과 맞는 쪽은 패딩을 끈 쪽이다(패딩 있음 93, 없음 76, 셈 9).", 11, MUTE))
    save("fig06_pdn_sizes.svg", W, H, b)


def fig07():
    W, H = 1000, 380
    b = [T(20, 26, "이 편의 자리 — 선생 · 학생 계열과 이 큰 틀의 네 칸 (이 저장소의 노트 기준)", 15, weight="bold"),
         T(20, 46, "윗줄은 연도 차례이고 인용 관계가 아니다. RD 는 EfficientAD 의 참고 문헌 74 건에 없다. 점선 = EfficientAD 가 가져온 부품.", 11, MUTE)]

    def box(x, y, w, t1, t2, colr):
        b.append(R(x, y, w, 54, "#ffffff", colr, rx=4))
        b.append(T(x + w / 2, y + 23, t1, 12, INK, "middle", "bold"))
        b.append(T(x + w / 2, y + 42, t2, 10, MUTE, "middle"))

    box(20, 62, 220, "Uninformed Students (CVPR 2020)", "선생 1 + 학생 셋, 수용장 17 · 33 · 65", D)
    box(270, 62, 220, "RD (CVPR 2022)", "선생 부호기 · 거꾸로 된 학생", D)
    box(520, 62, 220, "AST (WACV 2023)", "가역 선생 · 비대칭 구조", D)
    box(770, 62, 210, "EfficientAD (WACV 2024)", "같은 꼴 선생 · 학생 + 손실 비대칭", A)
    for x1, x2 in ((240, 270), (490, 520), (740, 770)):
        b.append(L(x1, 89, x2, 89, INK, 1.5))
    box(20, 172, 220, "PatchCore (CVPR 2022)", "WRN-101 특징 -> PDN 으로 증류", D)
    box(270, 172, 220, "GCAD (IJCV 2022)", "선생 특징 공간의 자기부호기", D)
    box(520, 172, 220, "DRAEM -> SimpleNet", "가짜 이상 계열 (이 큰 틀의 1 · 3 칸)", D)
    b.append(L(130, 172, 875, 116, MUTE, 1, "4 3"))
    b.append(L(380, 172, 875, 116, MUTE, 1, "4 3"))
    b.append(T(20, 262, "EfficientAD 는 PatchCore 가 쓰는 WRN-101 특징을 작은 PDN 에 증류해 선생으로 쓰고, 같은 꼴 학생을 「어려운 특징 손실 + 사전학습 벌점」 으로 배운다.", 11, MUTE))
    b.append(T(20, 282, "논리 이상은 GCAD 처럼 선생 특징 공간의 자기부호기로 잡되, 자기부호기와 선생의 차가 아니라 자기부호기와 학생(덧붙인 출력 384)의 차를 쓴다.", 11, MUTE))
    b.append(T(20, 302, "RD 노트가 남긴 「같은 꼴 학생의 보통 증류」 는 표 3 의 p_hard = 0 · 표 4 의 PDN 줄이 가장 가깝다. 다만 그 줄에도 자기부호기 갈래가 들어 있다.", 11, MUTE))
    b.append(T(20, 322, "DRAEM · SimpleNet 은 이 편 표에 SimpleNet 만 들어 있다. DRAEM 대신 같은 저자의 다음 편 DSR(ECCV 2022)이 들어 있다.", 11, MUTE))
    save("fig07_lineage.svg", W, H, b)


if __name__ == "__main__":
    check_means()
    check_leads()
    check_loco_parts()
    check_ranks()
    check_ablation()
    check_ratios()
    check_gpu_rank()
    check_figures()
    check_arch()
    check_misc()
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07):
        f()
    print("\n그림 일곱을 썼다:", OUT)
