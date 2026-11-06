# -*- coding: utf-8 -*-
r"""코어셋 노트(Sener & Savarese, ICLR 2018, arXiv v4)의 그림과 책상 계산을 만든다.

표준 라이브러리만 쓴다. 바깥 데이터를 읽지 않으므로 어디서나 다시 돌릴 수 있다.

  python make_figures.py

원문 그림 3 · 4 · 6 의 값은 PDF 안의 **벡터 좌표**에서 읽었다(crop_paper_figures.py).
눈금은 PDF 안의 흰 격자선으로 맞췄고 값은 소수 둘째 자리로 끊었다. 그림 5 의 표식 수와
덮는 반지름도 같은 스크립트가 낸다. 아래 상수 FIG34 · FIG6 · FIG5 가 그 값이다.

표준 출력에 찍히는 값이 노트의 「내가 센 것」 이다. 장난감 자료(T4 · T5 · T6)는 논문 자료가 아니다.
"""
import io
import itertools
import math
import os
import random
import sys

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

# ---------------------------------------------------------------- 원문에서 읽은 값
# 패널 이름: W = 그림 3(약지도), F = 그림 4(완전 지도). 값은 (평균, 띠의 반폭).
FIG34 = {
 'W_CIFAR10': {'x': [0.1, 0.2, 0.3, 0.4, 1.0],
   'Random': [(68.99, 2.0), (70.87, 1.7), (71.98, 1.1), (75.3, 1.6), (89.7, 0.0)],
   'Empirical': [(68.99, 2.0), (69.08, 1.4), (69.65, 1.0), (72.49, 0.8), (89.7, 0.0)],
   'Oracle': [(68.99, 2.0), (67.44, 1.5), (69.43, 1.1), (72.09, 0.9), (89.7, 0.0)],
   'DBAL': [(68.99, 2.0), (69.66, 1.6), (70.54, 1.2), (76.63, 1.0), (89.7, 0.0)],
   'BMDR': [(68.99, 2.0), (68.34, 1.4), (69.99, 1.0), (73.45, 0.8), (89.7, 0.0)],
   'CEAL': [(68.99, 2.0), (67.55, 1.4), (68.66, 1.0), (71.98, 0.9), (89.7, 0.0)],
   'KMedian': [(68.99, 2.0), (69.53, 1.58), (71.47, 1.08), (73.27, 0.94), (89.7, 0.0)],
   'Ours': [(68.99, 2.0), (74.09, 1.5), (78.96, 1.0), (82.39, 0.4), (89.7, 0.0)],
 },
 'W_CIFAR100': {'x': [0.1, 0.2, 0.3, 0.4, 1.0],
   'Random': [(30.45, 2.1), (40.82, 1.7), (47.86, 1.3), (53.66, 1.6), (64.71, 0.0)],
   'Empirical': [(30.45, 2.1), (40.32, 1.3), (48.65, 1.1), (51.44, 0.6), (64.71, 0.0)],
   'Oracle': [(30.45, 2.1), (40.17, 1.5), (48.7, 1.1), (52.83, 0.9), (64.71, 0.0)],
   'DBAL': [(30.45, 2.1), (40.56, 1.6), (48.74, 1.2), (52.08, 0.8), (64.71, 0.0)],
   'BMDR': [(30.45, 2.1), (41.14, 1.6), (46.96, 1.3), (53.4, 0.9), (64.71, 0.0)],
   'CEAL': [(30.4, 2.1), (40.3, 1.4), (46.87, 1.1), (53.03, 0.9), (65.0, 0.0)],
   'KMedian': [(30.45, 2.1), (40.15, 1.3), (47.54, 1.1), (52.74, 0.6), (64.71, 0.0)],
   'Ours': [(30.45, 2.1), (45.42, 1.6), (51.84, 1.3), (58.26, 0.9), (64.71, 0.0)],
 },
 'W_SVHN': {'x': [0.014, 0.07, 0.15, 0.6, 1.0],
   'Random': [(75.5, 2.0), (85.4, 1.7), (89.2, 1.2), (92.1, 1.1), (96.0, 0.0)],
   'Empirical': [(75.5, 2.0), (84.18, 1.5), (89.05, 1.2), (92.08, 1.1), (96.0, 0.0)],
   'Oracle': [(75.5, 2.0), (84.03, 1.6), (89.19, 1.1), (90.69, 1.3), (96.0, 0.0)],
   'DBAL': [(75.5, 2.0), (84.94, 1.5), (89.09, 1.1), (92.55, 1.3), (96.0, 0.0)],
   'BMDR': [(75.5, 2.0), (81.9, 1.5), (86.93, 1.2), (90.84, 1.0), (96.0, 0.0)],
   'CEAL': [(75.5, 2.0), (87.3, 1.5), (88.3, 1.2), (91.0, 0.9), (96.0, 0.0)],
   'KMedian': [(75.5, 2.0), (83.32, 1.5), (88.76, 1.1), (90.61, 1.3), (96.0, 0.0)],
   'Ours': [(75.5, 2.0), (92.5, 1.3), (94.6, 0.9), (95.3, 0.7), (96.0, 0.0)],
 },
 'F_CIFAR10': {'x': [0.1, 0.2, 0.3, 0.4, 1.0],
   'Random': [(60.91, 2.1), (68.66, 1.6), (70.87, 1.2), (74.2, 1.3), (89.7, 0.0)],
   'Empirical': [(60.91, 2.1), (67.54, 1.2), (71.12, 1.1), (72.18, 0.6), (89.7, 0.0)],
   'Oracle': [(60.91, 2.1), (66.33, 1.3), (69.77, 1.2), (75.3, 0.7), (89.7, 0.0)],
   'DBAL': [(60.91, 2.1), (67.55, 1.2), (71.98, 1.4), (73.09, 0.8), (89.7, 0.0)],
   'BMDR': [(60.91, 2.1), (66.21, 1.2), (68.91, 1.1), (72.37, 0.6), (89.7, 0.0)],
   'KMedian': [(60.91, 2.1), (67.35, 1.29), (70.36, 0.88), (72.19, 1.09), (89.7, 0.0)],
   'Ours': [(60.91, 2.1), (73.09, 1.6), (76.08, 1.0), (78.63, 0.6), (89.7, 0.0)],
 },
 'F_CIFAR100': {'x': [0.1, 0.2, 0.3, 0.4, 1.0],
   'Random': [(28.22, 2.2), (37.28, 1.6), (42.4, 1.4), (48.63, 1.3), (64.71, 0.0)],
   'Empirical': [(28.22, 2.2), (39.78, 1.2), (45.57, 1.1), (50.17, 0.6), (64.71, 0.0)],
   'Oracle': [(28.22, 2.2), (39.51, 1.5), (45.55, 1.2), (50.14, 0.7), (64.71, 0.0)],
   'DBAL': [(28.22, 2.2), (40.43, 1.4), (45.94, 1.3), (50.54, 0.8), (64.71, 0.0)],
   'BMDR': [(28.22, 2.2), (40.31, 1.6), (45.42, 1.2), (49.76, 0.8), (64.71, 0.0)],
   'KMedian': [(28.22, 2.2), (36.63, 1.2), (41.74, 1.1), (47.23, 0.6), (64.71, 0.0)],
   'Ours': [(28.22, 2.2), (44.5, 1.6), (50.14, 1.2), (54.41, 0.8), (64.71, 0.0)],
 },
 'F_SVHN': {'x': [0.014, 0.07, 0.15, 0.6, 1.0],
   'Random': [(67.0, 2.0), (79.0, 1.5), (86.0, 1.3), (91.0, 1.1), (96.0, 0.0)],
   'Empirical': [(67.0, 2.0), (81.1, 1.3), (87.47, 1.1), (91.14, 1.0), (96.0, 0.0)],
   'Oracle': [(67.0, 2.0), (80.67, 1.3), (87.36, 1.1), (91.19, 0.9), (96.0, 0.0)],
   'DBAL': [(67.0, 2.0), (81.12, 1.4), (88.45, 1.2), (91.16, 1.0), (96.0, 0.0)],
   'BMDR': [(67.0, 2.0), (76.49, 1.2), (83.83, 1.0), (88.85, 0.7), (96.0, 0.0)],
   'KMedian': [(67.0, 2.0), (77.82, 1.4), (85.6, 1.2), (88.63, 1.0), (96.0, 0.0)],
   'Ours': [(67.0, 2.0), (87.0, 1.1), (91.0, 0.9), (93.5, 0.8), (96.0, 0.0)],
 },
}
# 그림 6: (라벨 수, PDF y 좌표). 눈금은 y = 291.35 가 0.25, 165.15 가 0.65. x 는 10k = 357.69, 10k 당 37.355 pt.
FIG6_X_PT = [339.01, 357.69, 395.05, 469.76, 507.12]
FIG6_GREEDY_PT = [278.28, 233.56, 205.40, 171.85, 166.06]
FIG6_OURS_PT = [274.14, 226.93, 198.77, 166.89, 166.06]
# 그림 5: crop_paper_figures.py 가 낸 값. 단위는 PDF pt.
FIG5 = {
    'a': dict(R=39492, B=4998, G=5494, span=94.55, bg_max=5.418, bg_p99=1.392, bg_med=0.304, g_max=5.815, g_p99=3.104, g_med=0.578),
    'b': dict(R=40559, B=4999, G=4440, span=95.22, bg_max=6.056, bg_p99=1.431, bg_med=0.290, g_max=6.056, g_p99=2.054, g_med=0.434),
}
TABLE1 = dict(dist=104.2, greedy=2.0, mip_iter=7.5, mip_total=244.03, total=360.23)
PANELS = ['W_CIFAR10', 'W_CIFAR100', 'W_SVHN', 'F_CIFAR10', 'F_CIFAR100', 'F_SVHN']
PLABEL = {'W_CIFAR10': '약지도 CIFAR-10', 'W_CIFAR100': '약지도 CIFAR-100', 'W_SVHN': '약지도 SVHN',
          'F_CIFAR10': '완전 지도 CIFAR-10', 'F_CIFAR100': '완전 지도 CIFAR-100', 'F_SVHN': '완전 지도 SVHN'}


# ---------------------------------------------------------------- 계산
def softmax(x):
    m = max(x)
    e = [math.exp(v - m) for v in x]
    s = sum(e)
    return [v / s for v in e]


def frob(f):
    s2 = sum(v * v for v in f)
    s3 = sum(v ** 3 for v in f)
    return math.sqrt(max(0.0, s2 - 2 * s3 + s2 * s2))


def t1_softmax():
    print("\n[T1] 소프트맥스 립시츠 상수. 원문은 sqrt(C-1)/C")
    out = []
    for C in (2, 3, 5, 10, 20, 50, 100, 200, 1000):
        claim = math.sqrt(C - 1) / C
        uni = frob([1.0 / C] * C)
        two = frob([0.5, 0.5] + [0.0] * (C - 2))
        e = 1e-3
        x = [0.0, 0.0] + [-60.0] * (C - 2)
        y = [e, -e] + [-60.0] * (C - 2)
        fx, fy = softmax(x), softmax(y)
        ratio = math.sqrt(sum((a - b) ** 2 for a, b in zip(fx, fy))) / math.sqrt(2 * e * e)
        print("  C=%4d  원문 %.4f  균등점 F %.4f  (1/2,1/2,0..) F %.4f  유한 차분 비 %.4f  비/원문 %.2f" % (C, claim, uni, two, ratio, ratio / claim))
        out.append((C, claim, ratio))
    random.seed(0)
    for C in (3, 5, 10, 100):
        best = 0.0
        for _ in range(60000):
            k = random.randint(2, C)
            g = [random.gammavariate(random.choice((0.3, 1.0, 5.0)), 1.0) for _ in range(k)]
            s = sum(g)
            best = max(best, frob([v / s for v in g] + [0.0] * (C - k)))
        print("  C=%d 임의 표본 60000 개에서 F 의 최댓값 %.5f" % (C, best))
    return out


def t2_layer():
    print("\n[T2] 입력 무게 합 <= alpha 만으로 2-노름 단계가 서는가. 출력 m 개가 모두 같은 입력 하나를 무게 1 로 읽는 층")
    for m in (2, 512, 4096):
        print("  m=%d: 입력 무게 합 1, ||Wv||/||v|| = sqrt(m) = %.2f" % (m, math.sqrt(m)))


def t3_alpha():
    print("\n[T3] alpha 를 줄이면 손실이 어떻게 되나. C=10, 편향 없는 16 층을 층마다 s 배 하면 로짓이 s^16 배")
    C = 10
    claim = math.sqrt(C - 1) / C
    for s in (1.0, 0.9, 0.75, 0.5):
        scale = s ** 16
        f = softmax([20.0 * scale] + [0.0] * (C - 1))
        loss = math.sqrt((f[0] - 1) ** 2 + sum(v * v for v in f[1:]))
        print("  s=%.2f  로짓 배율 %.3e  손실 %.4f" % (s, scale, loss))
    print("  로짓 0 일 때 손실 = sqrt((C-1)/C) = %.4f, 최대 손실 sqrt(2) = %.4f" % (math.sqrt((C - 1) / C), math.sqrt(2)))
    for a in (1.0, 1.5, 2.0):
        lam = claim * a ** 16
        print("  alpha=%.1f  alpha^16=%.1f  lambda_l=%.3f  L/lambda_l=%.3e" % (a, a ** 16, lam, math.sqrt(2) / lam))
    g = 0.05
    n = 50000
    print("  두 번째 항 sqrt(L^2 log(1/g)/(2n)), L=sqrt2, g=0.05, n=50000: %.5f" % math.sqrt(2 * math.log(1 / g) / (2 * n)))


def d2(a, b):
    return abs(a - b) if not isinstance(a, tuple) else math.dist(a, b)


def radius(pts, centres, drop=0):
    ds = sorted(min(d2(p, pts[j]) for j in centres) for p in pts)
    return ds[len(ds) - 1 - drop] if drop < len(ds) else 0.0


def greedy(pts, s0, b):
    s = list(s0)
    for _ in range(b):
        u = max((i for i in range(len(pts)) if i not in s), key=lambda i: min(d2(pts[i], pts[j]) for j in s))
        s.append(u)
    return s


def opt(pts, s0, b, drop=0):
    rest = [i for i in range(len(pts)) if i not in s0]
    return min(radius(pts, list(s0) + list(c), drop) for c in itertools.combinations(rest, b))


def t4_two_opt():
    print("\n[T4] 알고리즘 1 의 2-OPT 를 s0 가 있을 때 무작위 소형 자료로 확인 (논문 자료가 아니다)")
    random.seed(1)
    trials, worst, viol, below_half = 4000, 0.0, 0, 0
    for _ in range(trials):
        n = random.randint(6, 11)
        pts = [(random.random(), random.random()) for _ in range(n)]
        s0 = random.sample(range(n), random.randint(1, 2))
        b = random.randint(1, 3)
        r = radius(pts, greedy(pts, s0, b))
        o = opt(pts, s0, b)
        if o > 0:
            worst = max(worst, r / o)
        if r > 2 * o + 1e-12:
            viol += 1
        if o < r / 2 - 1e-12:
            below_half += 1
    print("  시도 %d: 2xOPT 를 넘은 횟수 %d, OPT 가 r/2 아래로 내려간 횟수 %d, 최대 비 r/OPT %.3f" % (trials, viol, below_half, worst))


def feasible(pts, s0, b, delta, xi):
    rest = [i for i in range(len(pts)) if i not in s0]
    for c in itertools.combinations(rest, b):
        if radius(pts, list(s0) + list(c), xi) <= delta:
            return True
    return False


def alg2(pts, s0, b, xi, literal_sg, cap=1000):
    s = greedy(pts, s0, b)
    sg = s[len(s0):] if literal_sg else s
    dg = max(min(d2(p, pts[j]) for j in sg) for p in pts)
    lb, ub = dg / 2, dg
    dist = sorted({d2(a, c) for a in pts for c in pts})
    it = 0
    while ub != lb and it < cap:
        mid = (lb + ub) / 2
        if feasible(pts, s0, b, mid, xi):
            ub = max(v for v in dist if v <= mid)
        else:
            lb = min(v for v in dist if v >= mid)
        it += 1
    return dg, lb, ub, it


def t5_robust():
    print("\n[T5] 알고리즘 2 의 구간. 점 0, 1, 20, 21, 100, s0={점 0}, b=1 (논문 자료가 아니다)")
    pts = [0.0, 1.0, 20.0, 21.0, 100.0]
    s0, b = [0], 1
    g = greedy(pts, s0, b)
    print("  탐욕 선택 점 값", pts[g[-1]], " 반지름", radius(pts, g), " OPT(Xi=0)", opt(pts, s0, b), " OPT(Xi=1)", opt(pts, s0, b, 1))
    for xi, lit in ((0, False), (1, False), (0, True)):
        dg, lb, ub, it = alg2(pts, s0, b, xi, lit)
        print("  Xi=%d, s_g 에 s0 %s: 시작 ub=%.1f, 끝 lb=%.2f ub=%.2f, 반복 %d%s" % (
            xi, "뺌(글자 그대로)" if lit else "넣음", dg, lb, ub, it, " (상한에서 멈춤)" if it >= 1000 else ""))


def t6_mip():
    print("\n[T6] 식 (6) 의 변수 수와 표 1")
    n = 50000
    v = n + 2 * n * n
    print("  n=50000: u %d + w %d + xi %d = %d, 64e9 바이트 / 변수 = %.1f 바이트" % (n, n * n, n * n, v, 64e9 / v))
    print("  행렬 n^2 개 8 바이트 = %.1f GB" % (n * n * 8 / 1e9))
    t = TABLE1
    s = t['dist'] + t['greedy'] + t['mip_total']
    print("  표 1 합 %.2f, 적힌 Total %.2f, 차 %.2f (%.2f%%)" % (s, t['total'], t['total'] - s, (t['total'] - s) / t['total'] * 100))
    print("  MIP 몫 %.1f%%, 거리 행렬 %.1f%%, 탐욕 %.2f%% (분모 Total), MIP 반복 수 %.1f, log2(n^2/2) = %.1f" % (
        t['mip_total'] / t['total'] * 100, t['dist'] / t['total'] * 100, t['greedy'] / t['total'] * 100,
        t['mip_total'] / t['mip_iter'], math.log2(n * n / 2)))
    print("  Total / (거리+탐욕) = %.2f 배" % (t['total'] / (t['dist'] + t['greedy'])))
    print("  Xi = 1e-4 x 40000 = %.1f 개, b=5000 의 %.2f%%" % (1e-4 * 40000, 1e-4 * 40000 / 5000 * 100))
    print("  n=1e6 로 늘린 거리 행렬: 8 바이트로 %.1f TB, 시간 104.2 x 400 = %.1f 시간(n^2 비례 가정)" % (1e12 * 8 / 1e12, 104.2 * 400 / 3600))
    for e in (0.05, 0.1, 0.2, 0.5):
        print("  사영 뒤 보장 계수 2(1+e)/(1-e), e=%.2f: %.2f" % (e, 2 * (1 + e) / (1 - e)))


BASE = ['Random', 'Empirical', 'Oracle', 'DBAL', 'BMDR', 'CEAL', 'KMedian']


def t7_curves():
    print("\n[T7] 그림 3 · 4 칸별 비교. 가운데 세 점만 센다(첫 점은 공통 풀, 끝 점은 전부 라벨)")
    gaps = {}
    sep = tot = 0
    for p in PANELS:
        d = FIG34[p]
        row = []
        for k in (1, 2, 3):
            m, h = d['Ours'][k]
            cand = [(d[b][k][0], d[b][k][1], b) for b in BASE if b in d]
            bm, bh, bn = max(cand)
            g = m - bm
            s = g > h + bh
            sep += s
            tot += 1
            row.append((d['x'][k], m, bm, bn, g, h + bh, s))
            print("  %-10s x=%.3f  우리 %.2f  최고 상대 %s %.2f  차 %.2f  두 반폭 합 %.2f  띠 분리 %s" % (p, d['x'][k], m, bn, bm, g, h + bh, s))
        gaps[p] = row
    print("  띠가 떨어진 칸 %d / %d" % (sep, tot))
    allw = [r[4] for p in PANELS[:3] for r in gaps[p]]
    allf = [r[4] for p in PANELS[3:] for r in gaps[p]]
    print("  차 평균: 약지도 %.2f (%.2f~%.2f), 완전 지도 %.2f (%.2f~%.2f)" % (sum(allw) / 9, min(allw), max(allw), sum(allf) / 9, min(allf), max(allf)))
    smaller = 0
    for a, b in (('W_CIFAR10', 'F_CIFAR10'), ('W_CIFAR100', 'F_CIFAR100'), ('W_SVHN', 'F_SVHN')):
        for k in range(3):
            wg, fg = gaps[a][k][4], gaps[b][k][4]
            smaller += wg < fg
            print("    %s x=%.3f 약지도 %.2f 완전 %.2f" % (a, gaps[a][k][0], wg, fg))
    print("  약지도 차가 완전 지도 차보다 작은 칸 %d / 9" % smaller)
    for p in PANELS:
        d = FIG34[p]
        vs_rand = [d['Ours'][k][0] - d['Random'][k][0] for k in (1, 2, 3)]
        print("  %-10s 우리-최고상대 %s | 우리-Random %s" % (p, " ".join("%.2f" % r[4] for r in gaps[p]), " ".join("%.2f" % v for v in vs_rand)))
    for p in PANELS:
        print("  %-10s 세 칸 평균: 최고 상대와 %.2f, Random 과 %.2f" % (
            p, sum(r[4] for r in gaps[p]) / 3, sum(FIG34[p]['Ours'][k][0] - FIG34[p]['Random'][k][0] for k in (1, 2, 3)) / 3))
    print("  --- 「무작위가 낫다」")
    cnt = {}
    for meth in ('Oracle', 'DBAL'):
        win = 0
        for p in PANELS:
            d = FIG34[p]
            vals = []
            for k in (1, 2, 3):
                diff = d['Random'][k][0] - d[meth][k][0]
                win += diff > 0
                vals.append(diff)
            cnt[(meth, p)] = vals
            print("    Random-%s %-10s %s" % (meth, p, " ".join("%+.2f" % v for v in vals)))
        print("  Random 이 %s 보다 높은 칸 %d / 18" % (meth, win))
    print("  --- 「오라클 · 베이즈가 경험적 불확실성보다 낫다」")
    for meth in ('Oracle', 'DBAL'):
        win = sum(FIG34[p][meth][k][0] > FIG34[p]['Empirical'][k][0] for p in PANELS for k in (1, 2, 3))
        print("  %s > Empirical 칸 %d / 18" % (meth, win))
    print("  --- BMDR · k-Median 대 Random")
    for meth in ('BMDR', 'KMedian', 'Empirical'):
        win = sum(FIG34[p][meth][k][0] > FIG34[p]['Random'][k][0] for p in PANELS for k in (1, 2, 3))
        print("  %s > Random 칸 %d / 18" % (meth, win))
    halfs = [h for p in PANELS for m in FIG34[p] if m != 'x' for _, h in FIG34[p][m]]
    one = sum(abs(h * 10 - round(h * 10)) < 1e-6 for h in halfs)
    print("  띠 반폭 %d 칸 중 소수 한 자리로 떨어지는 칸 %d" % (len(halfs), one))
    print("  첫 점 반폭: %s" % {p: FIG34[p]['Ours'][0][1] for p in PANELS})
    return gaps, cnt


def t8_fig6():
    print("\n[T8] 그림 6 좌표")
    fx = lambda x: 10 + (x - 357.69) / 37.355 * 10
    fy = lambda y: 0.25 + (291.35 - y) / (291.35 - 165.15) * 0.40
    res = []
    for x, g, o in zip(FIG6_X_PT, FIG6_GREEDY_PT, FIG6_OURS_PT):
        k = fx(x)
        gv, ov = fy(g) * 100, fy(o) * 100
        res.append((k, gv, ov))
        print("  %5.1fk  탐욕 %.2f  우리 %.2f  차 %.2f" % (k, gv, ov, ov - gv))
    print("  --- 같은 라벨 수에서 그림 3 · 4 의 값과 맞대기 (CIFAR-100, 비 0.1 = 5k 로 셈)")
    idx = {5: 0, 10: 1, 20: 3, 50: 4}
    for kk, gv, ov in res:
        k = int(round(kk))
        if k in idx:
            i = idx[k]
            w, f = FIG34['W_CIFAR100'], FIG34['F_CIFAR100']
            wb = max(w[b][i][0] for b in BASE if b in w)
            fb = max(f[b][i][0] for b in BASE if b in f)
            print("  %dk: 그림 6 우리 %.2f | 그림 3 우리 %.2f, 그림 4 우리 %.2f | 탐욕 %.2f, 그림 3 최고 상대 %.2f(탐욕-상대 %+.2f), 그림 4 최고 상대 %.2f(탐욕-상대 %+.2f)" % (
                k, ov, w['Ours'][i][0], f['Ours'][i][0], gv, wb, gv - wb, fb, gv - fb))
    print("  40k: 그림 3 · 4 에 측정 점이 없다. 20k 와 50k 를 잇는 직선 값 약지도 %.2f 완전 지도 %.2f" % (
        58.26 + (64.71 - 58.26) * 20 / 30, 54.41 + (64.71 - 54.41) * 20 / 30))
    return res


def t9_fig5():
    print("\n[T9] 그림 5 표식 수와 평면 위 덮는 반지름 (단위 PDF pt)")
    for k, d in FIG5.items():
        print("  (%s) 파랑 %d 초록 %d 빨강 %d 합 %d | 파랑+초록 max %.3f p99 %.3f 중앙 %.3f | 초록만 max %.3f p99 %.3f 중앙 %.3f | 폭 대비 max %.2f%%" % (
            k, d['B'], d['G'], d['R'], d['B'] + d['G'] + d['R'], d['bg_max'], d['bg_p99'], d['bg_med'], d['g_max'], d['g_p99'], d['g_med'], d['bg_max'] / d['span'] * 100))


    print("  초록만 99%% 반지름 비 (b)/(a) = %.2f, 중앙값 비 %.2f" % (FIG5['b']['g_p99'] / FIG5['a']['g_p99'], FIG5['b']['g_med'] / FIG5['a']['g_med']))


# ---------------------------------------------------------------- SVG 도구 (앞 노트와 같다)
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def arrow(idd, color):
    return ('<marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>' % (idd, color))


def defs():
    return "<defs>" + arrow("af", FWD) + arrow("ar", REV) + arrow("ai", INK2) + arrow("ao", OK) + arrow("an", NO) + "</defs>"


def svg(name, w, h, body, label):
    s = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="%s" role="img" aria-label="%s">' % (w, h, w, h, FONT, esc(label)))
    s += '<rect x="0" y="0" width="100%%" height="100%%" fill="%s"/>' % BG
    s += defs() + body + "</svg>\n"
    io.open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8", newline="\n").write(s)
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
    a = '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"' % (x1, y1, x2, y2, color or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if marker:
        a += ' marker-end="url(#%s)"' % marker
    return a + "/>"


def circ(cx, cy, r, fill=None, stroke=None, sw=1.2):
    return '<circle cx="%.1f" cy="%.1f" r="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (cx, cy, r, fill or NODE, stroke or INK, sw)


def polyl(pts, stroke, sw=2, dash=None):
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
              % (x0 - 40, (y0 + y1) / 2, INK2, x0 - 40, (y0 + y1) / 2, esc(yl)))
    return s


# ---------------------------------------------------------------- 그림
def fig01():
    b = txt(380, 28, "경계에서 알고리즘까지: 단계마다 무엇을 가정하고 무엇을 쟀나", 15, weight="700")
    rows = [
        ("식 (1)", "모집단 손실을 줄이는 b 개 고르기", "목표. 라벨 없이는 못 잰다", FWD_SOFT, FWD),
        ("식 (3) · (4)", "일반화 오차 + 학습 오차 + 코어셋 손실", "앞의 둘은 작다고 두고 버린다. 수치 없음", FWD_SOFT, FWD),
        ("정리 1", "코어셋 손실 <= δ(λl + λη·L·C) + √(L²log(1/γ)/2n)", "학습 손실 0, 손실 립시츠, η 립시츠. δ 는 입력 공간", REV_SOFT, REV),
        ("보조정리 1", "λl = (√(C−1)/C)·α^(nc+nfc)", "l2 손실, 합성곱 + ReLU + 최댓값 풀링", REV_SOFT, REV),
        ("식 (5)", "min max min Δ: k-센터", "계수를 버리고 δ 만 줄인다", CODE_SOFT, CODE),
        ("알고리즘 1 · 2", "탐욕 2-OPT, 강건 MIP 이분 탐색", "Δ 는 마지막 완전연결층 활성의 l2, 교차 엔트로피로 학습", OK_SOFT, OK),
        ("그림 3 · 4 · 6", "분류 정확도만 그렸다", "δ · λ · 코어셋 손실 · 학습 오차를 잰 값이 없다", NO_SOFT, NO),
    ]
    y = 50
    for i, (a, c, d, f, st) in enumerate(rows):
        b += box(30, y, 700, 52, f, st)
        b += txt(46, y + 31, a, 12, anchor="start", weight="700")
        b += txt(160, y + 22, c, 12, anchor="start", weight="600")
        b += txt(160, y + 41, d, 11, fill=INK2, anchor="start")
        if i < len(rows) - 1:
            b += line(380, y + 52, 380, y + 66, INK2, 1.4, marker="ai")
        y += 66
    svg("fig01_chain", 760, y + 6, b, "경계에서 알고리즘까지의 단계와 가정")


def fig02():
    ks = [2, 3, 5, 10, 20, 50, 100, 200, 1000]
    x0, y0, x1, y1 = 70, 50, 690, 310
    lo, hi = math.log10(2), 3.0
    fx = lambda c: x0 + (math.log10(c) - lo) / (hi - lo) * (x1 - x0)
    fy = lambda v: y1 - v / 0.6 * (y1 - y0)
    b = txt(380, 26, "소프트맥스의 립시츠 상수: 원문의 값과 유한 차분으로 낸 값", 15, weight="700")
    b += frame(x0, y0, x1, y1, [2, 10, 100, 1000], [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], fx, fy, "부류 수 C (로그 눈금)", "||f(x) − f(y)|| / ||x − y||")
    claim = [(fx(c), fy(math.sqrt(c - 1) / c)) for c in ks]
    b += polyl(claim, REV, 2.2)
    meas = [(fx(c), fy(0.5)) for c in ks]
    b += polyl(meas, FWD, 2.2)
    for p in claim:
        b += circ(p[0], p[1], 3.5, REV, REV)
    for p in meas:
        b += circ(p[0], p[1], 3.5, FWD, FWD)
    b += txt(fx(3), fy(0.5) - 12, "내가 낸 비: 로짓 둘만 같고 나머지 −60, 모든 C 에서 0.500", 11, FWD, "start", "600")
    b += txt(fx(10) + 8, fy(0.3) - 4, "원문 √(C−1)/C: C=10 에서 0.300", 11, REV, "start", "600")
    b += txt(fx(100) - 6, fy(0.0995) + 22, "C=100 에서 0.0995 (유한 차분 비의 5.03 분의 1)", 11, REV, "end", "600")
    b += txt(380, 368, "f = (1/2, 1/2, 0, ...) 쪽의 Frobenius 값이 균등점보다 크다. C = 2 에서만 둘이 같다", 11, INK2)
    svg("fig02_softmax_lipschitz", 760, 382, b, "소프트맥스 립시츠 상수 비교")


def fig03(gaps):
    w, h = 760, 400
    x0, y0, x1, y1 = 60, 50, 730, 320
    fy = lambda v: y1 - v / 8.0 * (y1 - y0)
    b = txt(w / 2, 26, "그림 3 · 4 에서 이 편의 방법 − 가장 높은 상대 (백분율 점, 벡터 좌표로 읽음)", 15, weight="700")
    fx = lambda i: i
    for t in range(0, 9, 2):
        b += line(x0, fy(t), x1, fy(t), LINE, 1) + txt(x0 - 7, fy(t) + 4, str(t), 10, fill=MUTED, anchor="end")
    b += line(x0, y1, x1, y1, INK2) + line(x0, y0, x0, y1, INK2)
    groups = [('W_CIFAR10', 'F_CIFAR10', 'CIFAR-10'), ('W_CIFAR100', 'F_CIFAR100', 'CIFAR-100'), ('W_SVHN', 'F_SVHN', 'SVHN')]
    gw = (x1 - x0) / 3.0
    for gi, (a, c, nm) in enumerate(groups):
        gx = x0 + gi * gw
        for k in range(3):
            cx = gx + 18 + k * (gw - 30) / 3.0
            ra, rc = gaps[a][k], gaps[c][k]
            bw = 26
            for off, r, col in ((0, ra, FWD), (bw + 3, rc, REV)):
                b += bar(cx + off, fy(r[4]), bw, y1 - fy(r[4]), col)
                b += txt(cx + off + bw / 2, fy(r[4]) - 5, "%.2f" % r[4], 9, INK2)
                sep_y = fy(r[5])
                b += line(cx + off, sep_y, cx + off + bw, sep_y, INK, 1.6)
            b += txt(cx + bw + 1, y1 + 15, "x=%g" % ra[0], 10, MUTED)
        b += txt(gx + gw / 2, y1 + 34, nm, 12, weight="600")
    b += bar(70, 362, 12, 12, FWD) + txt(87, 373, "약지도(그림 3)", 11, anchor="start")
    b += bar(190, 362, 12, 12, REV) + txt(207, 373, "완전 지도(그림 4)", 11, anchor="start")
    b += line(330, 368, 352, 368, INK, 1.6) + txt(358, 373, "두 띠의 반폭 합: 막대가 이 선 위면 띠가 떨어진다", 11, anchor="start")
    svg("fig03_gap_to_best", w, h, b, "이 편의 방법과 최고 상대의 차")


def fig04(cnt):
    w, h = 760, 310
    b = txt(w / 2, 26, "「무작위가 낫다」 를 칸마다: Random − 방법 (백분율 점)", 15, weight="700")
    cols = [('Oracle', 'Oracle-Unc.'), ('DBAL', 'DBAL')]
    x0 = 170
    cw = 92
    y = 62
    b += txt(x0 + 1.5 * cw, 50, "Oracle-Unc.", 12, weight="600") + txt(x0 + 3 * cw + 40 + 1.5 * cw, 50, "DBAL", 12, weight="600")
    for p in PANELS:
        b += txt(160, y + 22, PLABEL[p], 11, anchor="end")
        for ci, (m, _) in enumerate(cols):
            base = x0 + ci * (3 * cw + 40)
            for k, v in enumerate(cnt[(m, p)]):
                f = OK_SOFT if v > 0 else NO_SOFT
                b += box(base + k * cw + 2, y, cw - 4, 32, f, LINE, rx=4)
                b += txt(base + k * cw + cw / 2, y + 21, "%+.2f" % v, 11, OK if v > 0 else NO, weight="600")
        y += 36
    b += txt(w / 2, y + 12, "칸은 왼쪽부터 가운데 세 점. 초록 = 무작위가 높다, 빨강 = 무작위가 낮다", 11, INK2)
    svg("fig04_random_vs_uncertainty", w, y + 28, b, "무작위와 불확실성 방법의 칸별 차")


def fig05(res):
    w, h = 760, 400
    x0, y0, x1, y1 = 70, 50, 720, 310
    fx = lambda k: x0 + (k - 0) / 52.0 * (x1 - x0)
    fy = lambda v: y1 - (v - 25) / 45.0 * (y1 - y0)
    b = txt(w / 2, 26, "그림 6 을 좌표로: 측정 점은 5k · 10k · 20k · 40k · 50k 다섯 곳", 15, weight="700")
    b += frame(x0, y0, x1, y1, [5, 10, 20, 40, 50], [30, 40, 50, 60, 70], fx, fy, "라벨 붙은 이미지 수 (k)", "정확도 (%)")
    pg = [(fx(k), fy(g)) for k, g, _ in res]
    po = [(fx(k), fy(o)) for k, _, o in res]
    b += polyl(pg, REV, 2) + polyl(po, PURP, 2)
    for p in pg:
        b += circ(p[0], p[1], 3.5, REV, REV)
    for p in po:
        b += circ(p[0], p[1], 3.5, PURP, PURP)
    for k, g, o in res:
        b += txt(fx(k) - (12 if k < 6 else 0), fy(o) - 10, "%.2f" % o, 10, PURP, weight="600")
        b += txt(fx(k) + 4, fy(g) + 16, "%.2f" % g, 10, REV, "start", "600")
    b += line(x0 + 30, 372, x0 + 52, 372, REV, 2) + txt(x0 + 58, 376, "탐욕(2-OPT)", 11, anchor="start")
    b += line(x0 + 170, 372, x0 + 192, 372, PURP, 2) + txt(x0 + 198, 376, "이 편의 방법(MIP)", 11, anchor="start")
    b += txt(x0 + 320, 376, "차: 1.31 · 2.10 · 2.10 · 1.57 · 0.00, 흩어짐 표시 없음", 11, INK2, "start")
    svg("fig05_fig6_coords", w, h, b, "그림 6 의 좌표")


def fig06():
    w, h = 760, 220
    t = TABLE1
    b = txt(w / 2, 26, "표 1 의 시간 (b = 5k, |s0| = 10k, 초)", 15, weight="700")
    x0, x1 = 50, 710
    y = 60
    scale = (x1 - x0) / t['total']
    x = x0
    for name, v, col in (("거리 행렬 104.2", t['dist'], FWD), ("탐욕 2", t['greedy'], OK), ("MIP 합 244.03", t['mip_total'], PURP)):
        b += bar(x, y, v * scale, 44, col)
        if v > 10:
            b += txt(x + v * scale / 2, y + 27, name, 12, "#FFFFFF", weight="600")
        x += v * scale
    rest = t['total'] - t['dist'] - t['greedy'] - t['mip_total']
    b += box(x, y, rest * scale, 44, NODE, NO, dash="3,2", rx=0)
    b += txt(x1, y - 7, "Total 360.23", 11, anchor="end", weight="600")
    b += txt(x0 + t['dist'] * scale, y + 62, "탐욕 2 초 (0.56%)", 11, OK)
    b += txt(x1 - 40, y + 62, "빈칸 %.2f 초 (적힌 합 350.23)" % rest, 11, NO, "end", "600")
    b += txt(x0, y + 100, "MIP 는 Total 의 67.7%, 반복 7.5 초를 나누면 32.5 번. 반복 수와 반복별 흩어짐은 적혀 있지 않다", 12, anchor="start")
    b += txt(x0, y + 122, "식 (6) 을 글자 그대로 넣으면 n = 50,000 에서 변수 5.0 x 10^9 개(내가 셈). 줄인 방법은 원문에 없다", 12, INK2, "start")
    svg("fig06_table1", w, 200, b, "표 1 시간 구성")


def fig07():
    w, h = 760, 300
    x0, x1 = 60, 700
    fx = lambda v: x0 + v / 100.0 * (x1 - x0)
    b = txt(w / 2, 26, "알고리즘 2 의 구간이 깨지는 장난감 (점 5 개, s0 = {0}, b = 1, 논문 자료 아님)", 15, weight="700")
    y = 90
    b += line(x0, y, x1, y, INK2, 1.4)
    for v in (0, 1, 20, 21, 100):
        col = REV if v == 0 else INK
        b += circ(fx(v), y, 5, col, col)
    b += txt(fx(0), y - 12, "s0", 11, REV, weight="600")
    b += txt(fx(100), y - 12, "100", 11)
    b += txt(fx(20.5), y - 12, "20, 21", 11)
    b += txt(fx(1) + 4, y + 20, "0, 1", 11, anchor="start")
    rows = [
        ("Ξ = 0", "탐욕이 점 100 을 고른다. 점 21 이 s0 에서 21 떨어져 반지름 21. 최적값도 21", OK),
        ("Ξ = 1", "100 을 이상점으로 두고 20 을 고르면 반지름 1. 구간 [10.5, 21] 밖이다", NO),
        ("", "글자 그대로 돌리면 ub = 1, lb = 10.5 에서 ub = lb 가 안 되어 멈추지 않는다 (상한 1,000 번)", NO),
        ("s_g", "알고리즘 1 은 s0 를 뺀 집합을 돌려주므로 s_g = {100}. 시작 ub = 100, lb = 50 이고 참값 21 이 구간 밖이다", NO),
    ]
    y = 140
    for a, t, c in rows:
        b += txt(x0, y, a, 12, c, "start", "700")
        b += txt(x0 + 50, y, t, 12, INK, "start")
        y += 32
    svg("fig07_bracket_toy", w, y + 2, b, "알고리즘 2 구간의 반례")


def fig08():
    w, h = 760, 340
    b = txt(w / 2, 26, "그림 5 를 벡터로 세면: 캡션은 1000 · 1000, 표식은 4,998 ~ 5,494", 15, weight="700")
    colw = 160
    x0 = 190
    heads = ["(a) 불확실성 오라클", "(b) 이 편의 방법"]
    for i, hd in enumerate(heads):
        b += txt(x0 + colw * i + colw / 2, 58, hd, 12, weight="600")
    rows = [
        ("파랑(처음 풀)", "{:,}".format(FIG5['a']['B']), "{:,}".format(FIG5['b']['B']), None),
        ("초록(고른 것)", "{:,}".format(FIG5['a']['G']), "{:,}".format(FIG5['b']['G']), None),
        ("빨강(나머지)", "{:,}".format(FIG5['a']['R']), "{:,}".format(FIG5['b']['R']), None),
        ("덮는 반지름, 파랑+초록, 최댓값", "%.2f" % FIG5['a']['bg_max'], "%.2f" % FIG5['b']['bg_max'], 'a'),
        ("덮는 반지름, 파랑+초록, 99%", "%.2f" % FIG5['a']['bg_p99'], "%.2f" % FIG5['b']['bg_p99'], 'a'),
        ("덮는 반지름, 초록만, 최댓값", "%.2f" % FIG5['a']['g_max'], "%.2f" % FIG5['b']['g_max'], 'a'),
        ("덮는 반지름, 초록만, 99%", "%.2f" % FIG5['a']['g_p99'], "%.2f" % FIG5['b']['g_p99'], 'b'),
    ]
    y = 70
    for nm, a, c, win in rows:
        b += txt(x0 - 12, y + 19, nm, 11, anchor="end")
        for i, v in enumerate((a, c)):
            good = win == ('a' if i == 0 else 'b')
            b += box(x0 + colw * i + 3, y, colw - 6, 30, OK_SOFT if good else NODE, LINE, rx=4)
            b += txt(x0 + colw * i + colw / 2, y + 20, v, 12, weight="600" if good else None)
        y += 34
    b += txt(w / 2, y + 16, "단위는 PDF pt(패널 폭 94.55 · 95.22 pt). 초록 칸 = 같은 줄에서 더 작다. t-SNE 평면이지 Δ 공간이 아니다", 11, INK2)
    svg("fig08_fig5_counts", w, y + 32, b, "그림 5 의 표식 수와 덮는 반지름")


def fig09():
    w, h = 760, 300
    b = txt(w / 2, 26, "같은 식, 다른 쓰임: 이 편과 PatchCore", 15, weight="700")
    head = ["", "Sener · Savarese 2018", "PatchCore 2022"]
    cx = [120, 340, 590]
    rows = [
        ("고르는 대상", "라벨을 붙일 이미지", "뱅크에 남길 조각 특징"),
        ("거리 공간", "라벨로 다시 배운 망의 끝 완전연결층", "얼린 ImageNet 망 중간 단계, 무작위 사영"),
        ("이미 있는 점", "s0 (처음 라벨 풀)", "없다 (첫 점이 안 적혔다)"),
        ("크기 제약", "|s1| <= b 를 식에 적는다", "식 (5) 에 없고 알고리즘의 l 이 대신"),
        ("이상점", "MIP 의 Ξ 로 내버려 둘 수 있다", "다루지 않는다"),
        ("반지름이 뜻하는 것", "손실 상한 (학습 손실 0 등 가정 아래)", "최근접 점수 오차 상한 (내 유도, 가정 없음)"),
    ]
    for i, t in enumerate(head):
        b += txt(cx[i], 54, t, 12, weight="700")
    y = 64
    for r in rows:
        b += box(20, y, 720, 32, NODE, LINE, rx=4)
        b += txt(cx[0], y + 21, r[0], 11, weight="600")
        b += txt(cx[1], y + 21, r[1], 11)
        b += txt(cx[2], y + 21, r[2], 11)
        y += 36
    svg("fig09_vs_patchcore", w, y + 8, b, "이 편과 PatchCore 의 쓰임 비교")


def fig10():
    w, h = 760, 170
    b = txt(w / 2, 26, "계보: 이 노트에서 확인한 인용 관계", 15, weight="700")
    b += node(30, 46, 210, 50, "Wolf 2011 · Cook 외 1998", "k-센터 · NP-난해의 인용", NODE, INK2, 12)
    b += node(30, 112, 210, 50, "Gonzalez 1985", "참고 문헌에 없다", NO_SOFT, NO, 12)
    b += node(310, 78, 190, 54, "Sener · Savarese 2018", "2-OPT 문장에 인용이 없다", FWD_SOFT, FWD, 12)
    b += node(560, 78, 170, 54, "PatchCore 2022", "뱅크 줄이기", OK_SOFT, OK, 12)
    b += line(240, 71, 308, 98, INK2, 1.4, marker="ai")
    b += line(240, 137, 308, 112, MUTED, 1.2, dash="4,3")
    b += line(500, 105, 558, 105, INK2, 1.4, marker="ai")
    b += txt(w / 2, 186, "실선: 원문의 인용. 점선: 인용이 없는 연결(바깥 지식이고 Gonzalez 원문은 읽지 않았다)", 11, INK2)
    svg("fig10_lineage", w, 200, b, "계보")


def main():
    t1_softmax()
    t2_layer()
    t3_alpha()
    t4_two_opt()
    t5_robust()
    t6_mip()
    gaps, cnt = t7_curves()
    res = t8_fig6()
    t9_fig5()
    print("\n그림")
    fig01()
    fig02()
    fig03(gaps)
    fig04(cnt)
    fig05(res)
    fig06()
    fig07()
    fig08()
    fig09()
    fig10()


if __name__ == "__main__":
    main()
