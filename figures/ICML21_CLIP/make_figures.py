# -*- coding: utf-8 -*-
"""CLIP 노트의 그림을 만들고, 노트가 인용하는 다시 계산한 값을 찍는다.

표준 라이브러리만 쓰고 바깥 데이터를 읽지 않는다. 값은 같은 폴더 data_clip.py 의 상수다.

  python make_figures.py

찍는 것: 대조 손실 작은 예시, 묶음 크기 · 걸음 수 · GPU 일, 글 부호기 파라미터(가정 둘을 밝힘),
그림 2 의 효율 배수, 그림 4 의 승수 · 평균 · 가장 큰 오름, 표 1 · 그림 7 · 부록 B · D · G 의 셈.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_clip import *  # noqa: E402,F401,F403

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "'Malgun Gothic','Noto Sans KR',sans-serif"
INK, MUTE, LINE = "#222222", "#666666", "#cccccc"
A, B, Y, D = "#2f6db3", "#c8553d", "#d9a21b", "#8a8a8a"  # 색각 이상 대비 검사를 통과한 셋 + 회색


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


def CIRC(x, y, r, fill):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="#ffffff" stroke-width="2"/>'


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


# 대조 손실 작은 예시: 묶음 3 쌍, 코사인 유사도 행렬(행 = 이미지, 열 = 글)
SIM = [[0.30, 0.10, 0.05],
       [0.08, 0.25, 0.12],
       [0.02, 0.11, 0.28]]


def ce_rows(m):
    out = []
    for i, row in enumerate(m):
        mx = max(row)
        lse = mx + math.log(sum(math.exp(v - mx) for v in row))
        out.append(lse - row[i])
    return out


def contrastive(scale):
    lg = [[v * scale for v in r] for r in SIM]
    li = ce_rows(lg)  # 이미지마다 글 셋 중 맞는 글
    lt = ce_rows([list(c) for c in zip(*lg)])  # 글마다 이미지 셋 중 맞는 이미지
    return sum(li) / 3, sum(lt) / 3, li, lt


def interp_x(xs, ys, target, logx):
    for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if y0 <= target <= y1:
            f = (target - y0) / (y1 - y0)
            return x0 * (x1 / x0) ** f if logx else x0 + f * (x1 - x0)
    return None


# ---------------------------------------------------------------- 셈
def calc():
    print("[셈 1] 대조 손실 작은 예시 (묶음 3, 코사인 행렬 SIM)")
    for scale in (1.0, 14.3, 100.0):
        a, b, li, lt = contrastive(scale)
        print(f"  logit 배율 {scale:6.1f} (τ = {1 / scale:.3f}): 이미지 쪽 {a:.3f}, 글 쪽 {b:.3f}, 평균 {(a + b) / 2:.3f}"
              f"  (이미지별 {[round(v, 3) for v in li]})")
    print(f"  무작위로 맞힐 때의 손실 ln 3 = {math.log(3):.3f}")

    print("\n[셈 2] 묶음 · 걸음 · GPU 일")
    n = COMMON["batch"]
    print(f"  묶음 {n:,} 이면 한 걸음의 logit {n * n:,} 개, 이미지 하나의 오답 글 {n - 1:,} 개")
    seen = COMMON["epochs"] * WIT["pairs"]
    print(f"  32 에폭 x 4 억 쌍 = {seen / 1e9:.1f} 십억 장, 걸음 수 {seen / n:,.0f}")
    print(f"  4 억 = 질의 50 만 x 상한 2 만 = {WIT['queries'] * WIT['per_query'] / 1e9:.0f} 십억 의 {WIT['pairs'] / (WIT['queries'] * WIT['per_query']) * 100:.0f}%")
    for k, (dd, g) in GPU_DAYS.items():
        print(f"  {k}: {dd} 일 x V100 {g} = {dd * g:,} GPU 일")
    r = GPU_DAYS["RN50x64"][0] * GPU_DAYS["RN50x64"][1] / (GPU_DAYS["ViT-L/14"][0] * GPU_DAYS["ViT-L/14"][1])
    print(f"  비 {r:.2f}")
    print(f"  최대 온도 100 -> τ 의 아래 끝 {1 / COMMON['max_temperature']:.2f}")
    print(f"  YFCC100M 걸러 남은 1,500 만 은 WIT 4 억의 {15e6 / 4e8 * 100:.2f}%, 부록 G 는 WIT 의 3.7% 라 적음")

    print("\n[셈 3] 글 부호기 파라미터 (12 층, 폭 512, 낱말 49,408). 가정: MLP 4 배 폭, 문맥 길이 77")
    d, layers, v, ctx = 512, 12, COMMON["vocab"], 77
    per = 12 * d * d + 9 * d + 4 * d
    tok = v * d
    total = layers * per + tok + ctx * d + 2 * d
    print(f"  층 하나 {per:,}, 층 {layers} 개 {layers * per:,}, 낱말 임베딩 {tok:,}, 자리 임베딩 {ctx * d:,}")
    print(f"  합 {total:,} ({total / 1e6:.1f} 백만, 투영 행렬 512 x 임베딩 차원 제외). 그림 2 의 캡션 기준선은 「63 million」")

    print("\n[셈 4] 그림 2 의 효율 배수 (선 꼭짓점 사이를 선형 x 와 로그 x 로 보간)")
    names = list(FIG2)
    lm, bowp, bowc = (FIG2[k] for k in names)
    for logx in (False, True):
        t1 = interp_x(FIG2_X, bowp, lm[-1], logx)
        t2 = interp_x(FIG2_X, bowc, lm[-1], logx)
        print(f"  {'로그' if logx else '선형'} 보간: LM 400M 의 {lm[-1]:.2f}% 에 낱말 주머니 예측은 {t1:.1f}M ({400 / t1:.2f} 배), "
              f"대조는 {t2:.1f}M (예측 대비 {t1 / t2:.2f} 배, LM 대비 {400 / t2:.2f} 배)")
    xa = lambda x: (x - 76.19) / (281.04 - 76.19) * 398 + 2
    for k, (x1, x2) in FIG2_ARROWS.items():
        print(f"  화살표 {k}: {xa(x1):.1f}M -> {xa(x2):.1f}M, 비 {xa(x1) / xa(x2):.2f}")
    print(f"  400M 의 끝 값: " + ", ".join(f"{k} {v[-1]:.2f}" for k, v in FIG2.items()))

    print("\n[셈 5] 그림 4")
    vals = [v for _, v in FIG4]
    pos = [n for n, v in FIG4 if v > 0]
    print(f"  27 개 중 양수 {len(pos)}, 평균 {sum(vals) / len(vals):+.2f} 점, 중앙값 {sorted(vals)[13]:+.1f}")
    top = sorted(FIG4, key=lambda t: -t[1])
    rank = [n for n, _ in top].index("STL10") + 1
    print(f"  가장 크게 오른 것 {top[0]}, STL10 은 {dict(FIG4)['STL10']:+.1f} 로 {rank} 위(같은 값 CIFAR100)")
    print(f"  10 점 넘게 낮은 것 {sum(1 for v in vals if v < -10)} 개, 20 점 넘게 높은 것 {sum(1 for v in vals if v > 20)} 개")

    print("\n[셈 6] 표 1 · 그림 7 · 부록 B · D")
    for k, (a, b) in TABLE1.items():
        print(f"  표 1 {k}: {a} -> {b} ({b - a:+.1f})")
    for k, (a, b) in FIG7.items():
        print(f"  그림 7 {k}: {a} -> {b}, 차 {b - a:+.1f} (그림 {FIG7_DELTA[k]:+.1f})")
    sh = [k for k in FIG7 if k != "ImageNet"]
    ra = sum(FIG7[k][0] for k in sh) / 5
    ca = sum(FIG7[k][1] for k in sh) / 5
    print(f"  오른쪽 다섯의 평균: ResNet101 {ra:.2f}, CLIP {ca:.2f}. ImageNet 76.2 와의 틈 {76.2 - ra:.2f} -> {76.2 - ca:.2f} ({(1 - (76.2 - ca) / (76.2 - ra)) * 100:.0f}% 줄어듦)")
    p = PROMPT_IMAGENET
    print(f"  프롬프트: 템플릿 +{p['template']} + 80 개 묶음 +{p['ensemble80']} = +{p['template'] + p['ensemble80']:.1f} (원문 「almost 5%」)")
    print(f"  부록 D: {ADAPT['zero_shot']} + {ADAPT['gain']} = {ADAPT['zero_shot'] + ADAPT['gain']:.1f} (원문 {ADAPT['adapted']})")
    print(f"  그림 15: 기울기 {FIG15['slope']} 의 95% 구간 {FIG15['ci']} 이 1 을 품는다: {FIG15['ci'][0] < 1 < FIG15['ci'][1]}")

    print("\n[셈 7] 부록 G 표 12")
    for k, (ly, lw, zy, zw) in TABLE12.items():
        print(f"  {k:15s} 선형 {ly - lw:+.1f} · 제로샷 {zy - zw:+.1f}")
    print(f"  이긴 수 합: 선형 {sum(TABLE12_WINS['linear'])}, 제로샷 {sum(TABLE12_WINS['zero'])}")
    print("\n[셈 8] 부록 F 표 11: 사람 0 -> 1 장 {:+.1f}, 1 -> 2 장 {:+.1f} (전체 정확도)".format(
        TABLE11["One-shot human"][0] - TABLE11["Zero-shot human"][0],
        TABLE11["Two-shot human"][0] - TABLE11["One-shot human"][0]))


# ---------------------------------------------------------------- 그림
def fig01():
    """대조 손실을 3 x 3 행렬로."""
    W, H = 1000, 430
    b = [T(20, 26, "대조 사전학습의 손실을 묶음 3 쌍으로 셈 (그림 3 의 의사 코드를 그대로 따름, 값은 내가 고른 예)", 15, weight="bold"),
         T(20, 46, "칸 = 이미지 i 와 글 j 의 코사인 유사도. 대각선(진하게)이 실제 쌍. 행마다 · 열마다 소프트맥스 교차 엔트로피를 내 평균한다.", 11, MUTE)]
    x0, y0, c = 140, 90, 70
    for j in range(3):
        b.append(T(x0 + j * c + c / 2, y0 - 10, f"글 T{j + 1}", 12, anchor="middle", weight="bold"))
    for i in range(3):
        b.append(T(x0 - 12, y0 + i * c + c / 2 + 4, f"이미지 I{i + 1}", 12, anchor="end", weight="bold"))
        for j in range(3):
            v = SIM[i][j]
            b.append(R(x0 + j * c + 1, y0 + i * c + 1, c - 2, c - 2, A if i == j else "#e8eef6", rx=4))
            b.append(T(x0 + j * c + c / 2, y0 + i * c + c / 2 + 5, f"{v:.2f}", 14, "#ffffff" if i == j else INK, "middle"))
    rows = []
    for scale in (1.0, 14.3, 100.0):
        a, bb, _, _ = contrastive(scale)
        rows.append((scale, a, bb))
    tx = 420
    b.append(T(tx, 100, "logit = 코사인 x exp(t). t 는 배우는 값이고, 표 18 의 「최대 온도 100」 이 배율의 위 끝이다.", 12))
    b.append(T(tx, 124, "같은 유사도 행렬이라도 배율에 따라 손실이 크게 달라진다 (내 셈):", 12))
    for k, (s, a, bb) in enumerate(rows):
        b.append(T(tx + 10, 154 + k * 26, f"배율 {s:5.1f} (τ = {1 / s:.3f}):  이미지 쪽 {a:.3f} · 글 쪽 {bb:.3f} · 평균 {(a + bb) / 2:.3f}", 12, INK))
    b.append(T(tx, 248, f"아무것도 못 가르면 손실은 ln 3 = {math.log(3):.3f} 이다. 묶음이 32,768 이면 이 값이 ln 32,768 = {math.log(32768):.2f} 이고,", 12))
    b.append(T(tx, 270, "이미지 하나가 오답 글 32,767 개와 겨룬다. 한 걸음의 행렬 칸은 1,073,741,824 개다.", 12))
    b.append(T(20, H - 48, "원문은 이 묶음 구성과 목적 함수를 Sohn(2016)의 multi-class N-pair 손실로, 의료 영상의 글-이미지 쌍에 처음 쓴 것을 ConVIRT(Zhang 외 2020)로 적는다.", 11, MUTE))
    b.append(T(20, H - 30, "CLIP 이 바꾼 것은 처음부터 배우기(사전학습 가중치 없음), 비선형 투영 대신 선형 투영, 글 한 문장 뽑기 생략, 무작위 정사각 자르기 하나뿐인 증강,", 11, MUTE))
    b.append(T(20, H - 12, "그리고 온도를 하이퍼파라미터로 두지 않고 배우는 것이다(2.2절).", 11, MUTE))
    save("fig01_contrastive_example.svg", W, H, b)


def fig02():
    """그림 2 를 꼭짓점 좌표로 다시 그림."""
    W, H = 1000, 470
    x0, y0, pw, ph = 90, 70, 560, 300
    fx = lambda m: x0 + (math.log2(m) - 1) / (math.log2(400) - 1) * pw
    fy = lambda v: y0 + ph - v / 45 * ph
    b = [T(20, 26, "원문 그림 2 를 선 꼭짓점 좌표로 읽어 다시 그림 (x 는 로그 눈금으로 바꿈)", 15, weight="bold"),
         T(20, 46, "같은 ResNet50 이미지 부호기, 목표만 바꾼 세 줄. 원문 그림은 x 를 선형으로 그려 앞쪽 다섯 점이 왼쪽 30 pt 안에 몰려 있다.", 11, MUTE)]
    for m in FIG2_X:
        b.append(L(fx(m), y0, fx(m), y0 + ph, "#eeeeee"))
        b.append(T(fx(m), y0 + ph + 16, f"{m:g}M", 10, MUTE, "middle"))
    for v in range(0, 46, 5):
        b.append(L(x0, fy(v), x0 + pw, fy(v), "#eeeeee"))
        b.append(T(x0 - 8, fy(v) + 4, str(v), 10, MUTE, "end"))
    cols = [D, Y, A]
    for (k, ys), colr in zip(FIG2.items(), cols):
        pts = [(fx(m), fy(v)) for m, v in zip(FIG2_X, ys)]
        b.append(PL(pts, colr, 2.5))
        for x, y in pts:
            b.append(CIRC(x, y, 3.5, colr))
        b.append(T(pts[-1][0] + 8, pts[-1][1] + 4, f"{k} {ys[-1]:.1f}", 11, INK))
    t1 = interp_x(FIG2_X, FIG2["낱말 주머니 예측"], 16.01, True)
    t2 = interp_x(FIG2_X, FIG2["낱말 주머니 대조 (CLIP)"], 16.01, True)
    b.append(L(fx(t2), fy(16.01), fx(400), fy(16.01), INK, 1, "4 3"))
    for m, lab in ((400, "400M"), (t1, f"{t1:.0f}M"), (t2, f"{t2:.0f}M")):
        b.append(CIRC(fx(m), fy(16.01), 3, INK))
        b.append(T(fx(m), fy(16.01) - 8, lab, 10, INK, "middle"))
    b.append(T(x0 + pw / 2, y0 + ph + 36, "본 이미지 수 (로그 눈금)", 11, MUTE, "middle"))
    b.append(T(20, H - 30, f"점선 = 언어 모형이 400M 에 닿은 16.0%. 같은 값에 닿는 지점(로그 보간, 내 셈)이 낱말 주머니 예측 {t1:.0f}M (400 / {t1:.0f} = {400 / t1:.2f} 배),", 11, MUTE))
    b.append(T(20, H - 12, f"대조 {t2:.0f}M ({t1:.0f} / {t2:.0f} = {t1 / t2:.2f} 배)이다. 원문 표기는 「3X」 · 「4X」 이고, 원문 화살표 둘은 2.87 배 · 4.55 배 구간에 그려져 있다.", 11, MUTE))
    save("fig02_fig2_reread.svg", W, H, b)


def fig03():
    """그림 4 를 정렬해 다시 그림."""
    W, H = 1000, 700
    x0, sc = 470, 9
    b = [T(20, 26, "그림 4: 제로샷 CLIP - (ResNet50 특징 + 로지스틱 회귀), 27 개 데이터셋 (글자 좌표로 이름과 값을 짝지음)", 15, weight="bold"),
         T(20, 46, "본문은 「가장 많이 오른 데이터셋은 STL10」 이라 적는데, 그림의 STL10 은 +3.0 으로 CIFAR100 과 함께 10 · 11 위다. 가장 큰 오름은 StanfordCars +28.9 다.", 11, MUTE)]
    b.append(L(x0, 62, x0, 62 + 21 * 27, INK))
    for i, (n, v) in enumerate(FIG4):
        y = 64 + i * 21
        colr = A if v > 0 else B
        if n == "STL10":
            colr = Y
        b.append(R(min(x0, x0 + v * sc), y + 3, max(abs(v * sc), 2), 15, colr, rx=2))
        if v >= 0:
            b.append(T(x0 - 8, y + 15, n, 11, INK, "end"))
            b.append(T(x0 + v * sc + 6, y + 15, f"{v:+.1f}", 11, INK))
        else:
            b.append(T(x0 + 8, y + 15, n, 11, INK))
            b.append(T(x0 + v * sc - 6, y + 15, f"{v:+.1f}", 11, INK, "end"))
    vals = [v for _, v in FIG4]
    b.append(T(20, H - 30, f"양수 16 / 27 (원문과 같음). 그러나 27 개 평균은 {sum(vals) / 27:+.2f} 점이다. 10 점 이상 낮은 10 개는 위성(EuroSAT · RESISC45) · 의료(PatchCamelyon) · 셈(CLEVRCounts) ·", 11, MUTE))
    b.append(T(20, H - 12, "거리(KITTI) · 표지판(GTSRB) · 손글씨(MNIST) · 질감(DTD) · 세밀 분류(Flowers102 · FGVCAircraft)다. 호박색 = STL10. 축척 1 점 = 9 px.", 11, MUTE))
    save("fig03_fig4_sorted.svg", W, H, b)


def fig04():
    """ImageNet 제로샷: 이름만 -> 템플릿 -> 80 개 묶음, 그리고 부록 G 의 데이터 비교."""
    W, H = 1000, 400
    b = [T(20, 26, "글 쪽에서 얻는 몫: 프롬프트 (부록 B, ImageNet) 와 사전학습 데이터 (부록 G 표 12, ResNet-50)", 15, weight="bold"),
         T(20, 46, "왼쪽은 원문이 문장으로 적은 오름 둘을 쌓은 것이다. 오른쪽은 YFCC100M 걸러 낸 몫과 같은 크기의 WIT 몫으로 따로 배운 두 모형의 제로샷 차(YFCC - WIT).", 11, MUTE)]
    x0, y0, sc = 60, 90, 40
    steps = [("클래스 이름만", 0, D), ("+ 「A photo of a {label}.」", PROMPT_IMAGENET["template"], A),
             ("+ 프롬프트 80 개 묶음", PROMPT_IMAGENET["ensemble80"], Y)]
    acc = 0
    for i, (n, v, colr) in enumerate(steps):
        y = y0 + i * 50
        b.append(T(x0, y + 4, n, 12))
        if v:
            b.append(R(x0 + 210 + acc * sc, y - 12, v * sc, 22, colr, rx=2))
            b.append(T(x0 + 210 + (acc + v) * sc + 6, y + 4, f"+{v} 점", 11, INK))
            acc += v
    b.append(T(x0, y0 + 160, f"합 +{acc:.1f} 점 (원문 「almost 5%」). 80 개를 고른 방법은 적혀 있지 않다.", 11, MUTE))
    b.append(T(x0, y0 + 180, "묶음은 확률이 아니라 글 임베딩을 평균해 한 번만 계산한다.", 11, MUTE))
    x1 = 600
    b.append(L(x1 + 160, 70, x1 + 160, 70 + 26 * 8, INK))
    for i, (k, (ly, lw, zy, zw)) in enumerate(TABLE12.items()):
        y = 76 + i * 26
        dz = zy - zw
        b.append(T(x1 + 60, y + 13, k, 11, INK, "end"))
        b.append(R(min(x1 + 160, x1 + 160 + dz * 6), y + 2, max(abs(dz * 6), 2), 16, A if dz > 0 else B, rx=2))
        b.append(T(x1 + 160 + dz * 6 + (6 if dz >= 0 else -6), y + 14, f"{dz:+.1f}", 10, INK, "start" if dz >= 0 else "end"))
    b.append(T(x1, 70 + 26 * 8 + 24, "평균 -0.4 점. 데이터셋별로는 +26.9 (Flowers102) 에서 -9.1 (UCF101).", 11, MUTE))
    b.append(T(20, H - 12, "부록 G 는 「YFCC 와 WIT 는 평균이 비슷하다」 고 적는다. 그 비교는 ResNet-50 한 크기 · 32 에폭 · 묶음 2,048 이고, 400M 전체와 견준 것이 아니다.", 11, MUTE))
    save("fig04_text_side_gains.svg", W, H, b)


def fig05():
    W, H = 1000, 340
    b = [T(20, 26, "이 편의 자리 — 이 저장소의 노트와 이 큰 틀의 세 칸", 15, weight="bold")]

    def box(x, y, w, t1, t2, colr):
        b.append(R(x, y, w, 54, "#ffffff", colr, rx=4))
        b.append(T(x + w / 2, y + 23, t1, 12, INK, "middle", "bold"))
        b.append(T(x + w / 2, y + 42, t2, 10, MUTE, "middle"))

    box(20, 60, 220, "Transformer (NIPS 2017)", "글 부호기의 뼈대", D)
    box(20, 140, 220, "ViT (ICLR 2021)", "이미지 부호기 하나 (ViT-L/14)", D)
    box(20, 220, 220, "ResNet (CVPR 2016)", "이미지 부호기 다른 하나 (RN50)", D)
    box(320, 140, 230, "CLIP (ICML 2021)", "글-이미지 대조, 제로샷 분류", A)
    box(630, 100, 170, "WinCLIP (CVPR 2023)", "창 단위 제로샷 이상 탐지", D)
    box(630, 180, 170, "AnomalyCLIP (ICLR 2024)", "물체와 무관한 프롬프트 학습", D)
    for y in (87, 167, 247):
        b.append(L(240, y, 320, 167, INK, 1.2))
    b.append(L(550, 167, 630, 127, INK, 1.2))
    b.append(L(550, 167, 630, 207, INK, 1.2))
    b.append(T(820, 132, "이 큰 틀의 둘째 · 셋째 칸", 11, MUTE))
    b.append(T(20, 300, "CLIP 은 이상 탐지를 다루지 않는다. 이 큰 틀에서 이 편을 읽는 까닭은 뒤 두 편이 쓰는 「글로 분류기를 만든다」 · 「프롬프트 묶음」 · 「이미지-글 코사인」 의 원 출처라서다.", 11, MUTE))
    b.append(T(20, 320, "BERT 노트와는 「사전학습 뒤 과제마다 미세조정」 대 「사전학습 뒤 글로 과제를 적는다」 로 갈린다.", 11, MUTE))
    save("fig05_lineage.svg", W, H, b)


if __name__ == "__main__":
    calc()
    for f in (fig01, fig02, fig03, fig04, fig05):
        f()
    print("\n그림 다섯을 썼다:", OUT)
