# -*- coding: utf-8 -*-
"""Reverse Distillation 노트의 그림을 만들고, 노트가 인용하는 다시 계산한 값을 찍는다.

표준 라이브러리만 쓰고 바깥 데이터를 읽지 않는다. 표 값은 같은 폴더 data_rd.py 의 상수다.

  python make_figures.py

찍는 것: 표 1 · 2 의 평균 다시 내기, 부류별 이김 · 같음 · 짐, 상대 열과 원 논문 값의 대조,
DRAEM 과의 부류별 차(이 편 밖의 값), 128 대 256 의 차, 표 3 의 PaDiM 메모리를 공분산 크기로 다시 낸 값.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_rd import *  # noqa: E402,F401,F403

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def mean(v):
    v = list(v)
    return sum(v) / len(v)


# 표 1 의 256 열 (GT ~ CutPaste) 과 Ours
T1_OTHERS = list(range(2, 10))
OURS1 = 10
# 표 2 의 256 열에서 픽셀 AUROC 를 낸 열 · PRO 를 낸 열
T2_AUC_OTHERS = [4, 5, 6, 7]   # SPADE PaDiM RIAD CutPaste
T2_PRO_OTHERS = [2, 3, 4, 5]   # US MF SPADE PaDiM
OURS2 = 8


def margin_t1(k):
    r = T1[k]
    best = max(r[j] for j in T1_OTHERS)
    who = [T1_COLS[j] for j in T1_OTHERS if r[j] == best]
    return round(r[OURS1] - best, 1), who


def margin_t2(k, q):
    idx = T2_AUC_OTHERS if q == 0 else T2_PRO_OTHERS
    r = T2[k]
    best = max(r[j][q] for j in idx)
    who = [T2_COLS[j] for j in idx if r[j][q] == best]
    return round(r[OURS2][q] - best, 1), who


# ---------------------------------------------------------------- 찍기
def recount():
    print("== 표 1 평균 다시 내기 (부류 15 평균 · 질감 5 · 물체 10, 인쇄값)")
    for j, c in enumerate(T1_COLS):
        col = [T1[k][j] for k in CL]
        print(f"  {c:9s} 15={mean(col):6.2f} ({T1_ALL[j]})  질감={mean(col[:5]):6.2f} ({T1_TEX[j]})  물체={mean(col[5:]):6.2f} ({T1_OBJ[j]})")
    print("== 표 1 「SOTA 를 2.5% 넘는다」: 98.5 - 다른 열 인쇄 평균")
    print("  " + ", ".join(f"{T1_COLS[j]} {T1_ALL[OURS1] - T1_ALL[j]:.1f}" for j in T1_OTHERS))
    print("== 표 1 부류별 (256 열 여덟과 견줌)")
    w = t = l = 0
    for k in CL:
        d, who = margin_t1(k)
        w += d > 0; t += d == 0; l += d < 0
        print(f"  {k:10s} {d:+.1f} {'/'.join(who)}")
    print(f"  이김 {w} · 같음 {t} · 짐 {l}")
    print("== 표 1 굵은 칸 대 「위 둘」 (같은 값을 한 자리로 셀 때의 위 두 값)")
    for k in CL:
        names = [T1_COLS[j] for j in T1_OTHERS] + ["Ours"]
        vals = [T1[k][j] for j in T1_OTHERS] + [T1[k][OURS1]]
        top2 = sorted(set(vals), reverse=True)[:2]
        exp = [n for n, v in zip(names, vals) if v in top2]
        if sorted(exp) != sorted(T1_BOLD[k]):
            print(f"  {k}: 굵게 {T1_BOLD[k]}, 위 두 값 {top2} 의 칸 {exp}")
    print("== 표 1 상대 열과 다른 표의 대조")
    for name, ref, j in [("PaDiM", DRAEM_T1_PADIM, 8), ("US", DRAEM_T1_US, 4), ("GN", DRAEM_T1_GAN, 3), ("PSVDD", PSVDD_IMG, 5)]:
        same = sum(T1[k][j] == ref[k] for k in CL)
        print(f"  {name}: 15 칸 중 {same} 칸 같음")

    print("== 표 2 평균 다시 내기")
    for j, c in enumerate(T2_COLS):
        for q, qn in ((0, "AUROC"), (1, "PRO")):
            col = [T2[k][j][q] for k in CL]
            if None in col:
                continue
            print(f"  {c:9s} {qn:5s} 15={mean(col):6.2f} ({T2_ALL[j][q]})  질감={mean(col[:5]):6.2f} ({T2_TEX[j][q]})"
                  f"  물체={mean(col[5:]):6.2f} ({T2_OBJ[j][q]})")
    print("== 표 2 상대 열과 원 논문 값의 대조")
    for name, ref, j, q in [("PaDiM 픽셀", PADIM_PIX, 5, 0), ("PaDiM PRO", PADIM_PRO, 5, 1), ("SPADE 픽셀", SPADE_PIX, 4, 0),
                            ("SPADE PRO", SPADE_PRO, 4, 1), ("US PRO", US_PRO, 2, 1), ("RIAD 픽셀 (DRAEM 표 2)", DRAEM_T2_RIAD, 6, 0)]:
        same = sum(T2[k][j][q] == ref[k] for k in CL)
        print(f"  {name}: 15 칸 중 {same} 칸 같음")
    for q, qn in ((0, "픽셀 AUROC"), (1, "PRO")):
        w = l = 0
        for k in CL:
            d, who = margin_t2(k, q)
            w += d > 0; l += d < 0
            if d <= 0:
                print(f"  {qn} 짐: {k} {d:+.1f} {'/'.join(who)}")
        print(f"  {qn}: 이김 {w} · 짐 {l}")

    print("== DRAEM 과의 차 (이 편 밖의 값, RD - DRAEM)")
    for nm, rd, dr in (("이미지", lambda k: T1[k][OURS1], DRAEM_IMG), ("픽셀", lambda k: T2[k][OURS2][0], DRAEM_PIX)):
        ds = [(k, round(rd(k) - dr[k], 1)) for k in CL]
        print(f"  {nm}: " + ", ".join(f"{k} {d:+.1f}" for k, d in ds))
        print(f"  {nm}: RD 높음 {sum(d > 0 for _, d in ds)} · 같음 {sum(d == 0 for _, d in ds)} · 낮음 {sum(d < 0 for _, d in ds)}"
              f" · 15 평균 RD {mean(rd(k) for k in CL):.2f} DRAEM {mean(dr.values()):.2f}")

    print("== 128 대 256 (Ours, 256 - 128)")
    for k in CL:
        print(f"  {k:10s} 이미지 {T1[k][OURS1] - T1[k][1]:+.1f}  픽셀 {T2[k][OURS2][0] - T2[k][1][0]:+.1f}  PRO {T2[k][OURS2][1] - T2[k][1][1]:+.1f}")

    print("== 표 3 PaDiM 메모리를 공분산으로 다시 내기 (가정: 56 x 56 자리, 550 차원, 4 바이트)")
    b = 56 * 56 * 550 * 550 * 4
    print(f"  {b:,} 바이트 = {b / 1e6:,.1f} MB (10^6) = {b / 2 ** 20:,.1f} MiB")
    print("== 끈 실험의 차")
    for a, b_ in zip(T5, T5[1:]):
        print(f"  {a[0]} -> {b_[0]}: " + " · ".join(f"{y - x:+.1f}" for x, y in zip(a[1:], b_[1:])))


# ---------------------------------------------------------------- 그림
def bars(name, title, sub, rows, x0, sc, foot, label_who=True):
    W, H = 820, 70 + 24 * len(rows) + 40
    b = [T(20, 24, title, 14, weight="bold"), T(20, 44, sub, 11, MUTE)]
    b.append(L(x0, 56, x0, 56 + 24 * len(rows), INK))
    for i, (c, d, who) in enumerate(rows):
        y = 60 + i * 24
        w = d * sc
        col = (C if c in TEX else A) if d >= 0 else B
        b.append(R(min(x0, x0 + w), y, max(abs(w), 1.5), 16, col))
        b.append(T(20, y + 13, c + (" (질감)" if c in TEX else ""), 11))
        lab = f"{d:+.1f}" if d > 0 else ("같음" if d == 0 else f"{d:+.1f}")
        if d <= 0 and label_who and who:
            lab += f" ({who})"
        b.append(T((x0 + w + 6) if d >= 0 else (x0 + w - 6), y + 13, lab, 11, MUTE, "start" if d >= 0 else "end"))
    b.append(T(20, H - 14, foot, 11, MUTE))
    save(name, W, H, b)


def fig01():
    rows = []
    for k in CL:
        d, who = margin_t1(k)
        rows.append((k, d, "/".join(who)))
    rows.sort(key=lambda x: -x[1])
    bars("fig01_tab1_margin.svg", "표 1 · 이미지 AUROC: RD(256) 에서 그 부류의 가장 센 256 상대를 뺀 값 (내 뺄셈)",
         "이김 5 · 같음 3 · 짐 7. 평균은 98.5 로 가장 높다(캡션이 주장하는 것은 평균 순위다).", rows, 470, 60,
         "파랑 = 물체가 이김 · 초록 = 질감이 이김 · 빨강 = 짐(괄호는 그 부류의 가장 센 상대). 축척 1 점 = 60 px.")


def fig02():
    W = 900
    rows = CL
    H = 90 + 24 * len(rows) + 40
    b = [T(20, 24, "표 2 · RD(256) 에서 그 부류의 가장 센 256 상대를 뺀 값 (내 뺄셈)", 14, weight="bold"),
         T(20, 44, "왼쪽 픽셀 AUROC (상대: SPADE · PaDiM · RIAD · CutPaste), 오른쪽 PRO (상대: US · MF · SPADE · PaDiM). 둘 다 이김 7 · 짐 8.", 11, MUTE)]
    for q, x0, head in ((0, 380, "픽셀 AUROC"), (1, 720, "PRO")):
        b.append(T(x0, 72, head, 12, weight="bold", anchor="middle"))
        b.append(L(x0, 80, x0, 80 + 24 * len(rows), INK))
        sc = 20 if q == 0 else 9
        for i, k in enumerate(rows):
            d, who = margin_t2(k, q)
            y = 84 + i * 24
            w = d * sc
            b.append(R(min(x0, x0 + w), y, max(abs(w), 1.5), 16, (C if k in TEX else A) if d > 0 else B))
            lab = f"{d:+.1f}" + (f" {'/'.join(who)}" if d <= 0 else "")
            b.append(T((x0 + w + 6) if d > 0 else (x0 + w - 6), y + 13, lab, 10, MUTE, "start" if d > 0 else "end"))
            if q == 0:
                b.append(T(20, y + 13, k + (" (질감)" if k in TEX else ""), 11))
    b.append(T(20, H - 14, "축척: 왼쪽 1 점 = 20 px, 오른쪽 1 점 = 9 px. transistor 는 왼쪽 -5.0 (PaDiM), 오른쪽 -14.6 (MF).", 11, MUTE))
    save("fig02_tab2_margin.svg", W, H, b)


def fig03():
    W = 900
    H = 90 + 24 * len(CL) + 40
    b = [T(20, 24, "RD 에서 DRAEM 을 뺀 값 — 이 편의 표에는 DRAEM 이 없다 (DRAEM 표 1 · 2 와 RD 표 1 · 2 로 내 뺄셈)", 14, weight="bold"),
         T(20, 44, "평균 차는 이미지 +0.48, 픽셀 AUROC +0.50 (부류 평균). RD 가 높은 부류는 둘 다 8. 세 번째 지표는 갈린다(DRAEM 은 AP, RD 는 PRO).", 11, MUTE)]
    for q, x0, head, dr, rd in ((0, 380, "이미지 AUROC", DRAEM_IMG, lambda k: T1[k][OURS1]),
                                (1, 720, "픽셀 AUROC", DRAEM_PIX, lambda k: T2[k][OURS2][0])):
        b.append(T(x0, 72, head, 12, weight="bold", anchor="middle"))
        b.append(L(x0, 80, x0, 80 + 24 * len(CL), INK))
        for i, k in enumerate(CL):
            d = round(rd(k) - dr[k], 1)
            y = 84 + i * 24
            w = d * 25
            b.append(R(min(x0, x0 + w), y, max(abs(w), 1.5), 16, A if d > 0 else (B if d < 0 else D)))
            b.append(T((x0 + w + 6) if d >= 0 else (x0 + w - 6), y + 13, "같음" if d == 0 else f"{d:+.1f}", 10, MUTE,
                       "start" if d >= 0 else "end"))
            if q == 0:
                b.append(T(20, y + 13, k + (" (질감)" if k in TEX else ""), 11))
    b.append(T(20, H - 14, "파랑 = RD 가 높음 · 빨강 = DRAEM 이 높음. 두 편 모두 반복이 없다. 축척 1 점 = 25 px.", 11, MUTE))
    save("fig03_rd_vs_draem.svg", W, H, b)


def fig04():
    groups = [("표 5 · 병목", T5), ("표 6 · 선생 백본", T6), ("표 7 · 쓰는 층", T7)]
    W, H = 900, 520
    b = [T(20, 24, "끈 실험 세 표의 이미지 AUROC (점선: 표 1 의 CutPaste 96.1 · PaDiM 95.5, 이 편 밖의 DRAEM 98.0)", 14, weight="bold"),
         T(20, 44, "어느 표에도 반복 수가 없다. 「Pre」 는 사전학습 넷째 블록을 그대로 병목으로 쓴 줄이다.", 11, MUTE)]
    x0, lo, hi, sc = 230, 89.0, 99.0, 55
    y = 70
    for g, rows in groups:
        b.append(T(20, y + 4, g, 12, weight="bold"))
        y += 14
        for n, ad, al, pro in rows:
            w = (ad - lo) * sc
            b.append(R(x0, y, w, 18, A if n not in ("Pre", "M1") else D))
            b.append(T(x0 - 8, y + 14, n, 11, anchor="end"))
            b.append(T(x0 + w + 6, y + 14, f"{ad:.1f}  (픽셀 {al:.1f} · PRO {pro:.1f})", 10, MUTE))
            y += 24
        y += 12
    for v, lab, col, dy, anc in ((96.1, "CutPaste 96.1", D, 8, "start"), (95.5, "PaDiM 95.5", D, 8, "end"),
                                 (98.0, "DRAEM 98.0", B, 8, "middle")):
        x = x0 + (v - lo) * sc
        b.append(L(x, 76, x, y - 6, col, 1, "4 3"))
        b.append(T(x + (4 if anc == "start" else -4 if anc == "end" else 0), y + dy, lab, 10, col, anc))
    b.append(T(20, H - 12, f"막대 왼쪽 끝 = {lo:.0f}. 축척 1 점 = {sc} px.", 11, MUTE))
    save("fig04_ablation.svg", W, H, b)


def fig05():
    W = 980
    H = 90 + 24 * len(CL) + 40
    b = [T(20, 24, "RD 의 256 x 256 에서 128 x 128 을 뺀 값 (표 1 · 2 로 내 뺄셈)", 14, weight="bold"),
         T(20, 44, "transistor 는 세 지표 모두 128 이 높은 유일한 부류다. 원문 한계 절이 쓴 「128 로 97.6」 이 표 2 의 128 열 값이다.", 11, MUTE)]
    cols = [("이미지 AUROC", lambda k: T1[k][OURS1] - T1[k][1], 330), ("픽셀 AUROC", lambda k: T2[k][OURS2][0] - T2[k][1][0], 580),
            ("PRO", lambda k: T2[k][OURS2][1] - T2[k][1][1], 830)]
    for q, (head, f, x0) in enumerate(cols):
        b.append(T(x0, 72, head, 12, weight="bold", anchor="middle"))
        b.append(L(x0, 80, x0, 80 + 24 * len(CL), INK))
        for i, k in enumerate(CL):
            d = round(f(k), 1)
            y = 84 + i * 24
            w = d * 11
            b.append(R(min(x0, x0 + w), y, max(abs(w), 1.5), 16, A if d > 0 else (B if d < 0 else D)))
            b.append(T((x0 + w + 5) if d >= 0 else (x0 + w - 5), y + 13, f"{d:+.1f}", 10, MUTE, "start" if d >= 0 else "end"))
            if q == 0:
                b.append(T(20, y + 13, k + (" (질감)" if k in TEX else ""), 11))
    b.append(T(20, H - 14, "파랑 = 256 이 높음 · 빨강 = 128 이 높음. 축척 1 점 = 11 px.", 11, MUTE))
    save("fig05_res_128_vs_256.svg", W, H, b)


def fig06():
    W, H = 900, 380
    b = [T(20, 24, "이 편의 자리 — 선생-학생 계열과 이웃 계열 (이 저장소의 노트 기준)", 14, weight="bold")]

    def box(x, y, w, t1, t2, col):
        b.append(R(x, y, w, 52, "#ffffff", col))
        b.append(T(x + w / 2, y + 22, t1, 12, INK, "middle", "bold"))
        b.append(T(x + w / 2, y + 40, t2, 10, MUTE, "middle"))

    box(20, 60, 200, "US (CVPR 2020)", "같은 꼴 학생 여럿, 정상만 학습", D)
    box(250, 60, 200, "MKD (CVPR 2021)", "선생보다 작은 학생, 층 여럿 맞춤", D)
    box(480, 60, 200, "RD (CVPR 2022) 이 노트", "부호기 선생 → 복호기 학생", B)
    box(710, 60, 170, "EfficientAD (WACV 2024)", "이 큰 틀의 마지막 칸", A)
    for x1, x2 in ((220, 250), (450, 480), (680, 710)):
        b.append(L(x1, 86, x2, 86, INK, 1.5))
    box(20, 170, 200, "SPADE · PaDiM", "정상 특징을 저장", D)
    box(250, 170, 200, "PatchCore (CVPR 2022)", "저장 + 코어셋", D)
    box(480, 170, 200, "UniAD (NeurIPS 2022)", "특징 재구성, 통합 설정", D)
    box(710, 170, 170, "DRAEM (ICCV 2021)", "가짜 결함 + 분할 망", D)
    b.append(L(540, 112, 540, 170, MUTE, 1, "4 3"))
    b.append(T(548, 136, "같은 「특징을 되살린다」", 10, MUTE))
    b.append(T(548, 150, "발상, 학생 대신 변환기", 10, MUTE))
    b.append(L(660, 112, 760, 170, B, 1, "4 3"))
    b.append(T(722, 130, "RD 의 표에 없다", 10, B))
    b.append(T(20, 262, "RD 가 표 3 에서 비용을 견준 상대는 저장 계열(SPADE · PaDiM)이다. 저장하지 않고 학생 망 하나를 둔다는 것이 이 편의 비용 주장이다.", 11, MUTE))
    b.append(T(20, 284, "같은 해 같은 학회(CVPR 2022)의 PatchCore 는 RD 참고 문헌 50 건에 없다.", 11, MUTE))
    b.append(T(20, 306, "DRAEM 은 RD 의 참고 문헌에 없고, 같은 저자의 앞 편 RIAD [46] 만 있다.", 11, MUTE))
    save("fig06_lineage.svg", W, H, b)


if __name__ == "__main__":
    recount()
    for f in (fig01, fig02, fig03, fig04, fig05, fig06):
        f()
    print("그림 여섯을 썼다:", OUT)
