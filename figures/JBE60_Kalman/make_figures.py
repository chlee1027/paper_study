"""Kalman (1960) 노트의 책상 확인 셈과 그림.

표준 라이브러리만 쓴다. python make_figures.py 로 셈 1 ~ 9 를 찍고 그림 둘을 쓴다.
행렬이 작아(가장 큰 것이 6 x 6) 행렬 셈을 손으로 짠 함수로 한다.
"""
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------- 행렬 도구
def mat(rows):
    return [list(map(float, r)) for r in rows]


def zeros(n, m):
    return [[0.0] * m for _ in range(n)]


def eye(n):
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def T(A):
    return [list(r) for r in zip(*A)]


def mm(*Ms):
    out = Ms[0]
    for B in Ms[1:]:
        if len(out[0]) != len(B):
            raise ValueError(f"shape {len(out)}x{len(out[0])} @ {len(B)}x{len(B[0])}")
        out = [[sum(a * b for a, b in zip(r, c)) for c in zip(*B)] for r in out]
    return out


def add(A, B):
    return [[a + b for a, b in zip(r, s)] for r, s in zip(A, B)]


def sub(A, B):
    return [[a - b for a, b in zip(r, s)] for r, s in zip(A, B)]


def scale(c, A):
    return [[c * a for a in r] for r in A]


def inv(A):
    n = len(A)
    M = [list(r) + e for r, e in zip(A, eye(n))]
    for i in range(n):
        piv = max(range(i, n), key=lambda k: abs(M[k][i]))
        M[i], M[piv] = M[piv], M[i]
        d = M[i][i]
        M[i] = [x / d for x in M[i]]
        for k in range(n):
            if k != i:
                f = M[k][i]
                M[k] = [x - f * y for x, y in zip(M[k], M[i])]
    return [r[n:] for r in M]


def maxabs(A):
    return max(abs(x) for r in A for x in r)


def block(rows):
    out = []
    for row in rows:
        for i in range(len(row[0])):
            out.append([x for B in row for x in B[i]])
    return out


def randmat(rng, n, m, s=1.0):
    return [[rng.gauss(0, s) for _ in range(m)] for _ in range(n)]


def randspd(rng, n, s=1.0):
    A = randmat(rng, n, n, s)
    return add(mm(A, T(A)), scale(0.5, eye(n)))


# ---------------------------------------------------------------- 원문 식 (28) ~ (30)
def kalman_step(P, Phi, M, Q):
    """원문 식 (28) ~ (30). P 는 P*(t) = cov x~(t|t-1). 돌려주는 것은 Delta*, Phi*, P*(t+1)."""
    D = mm(Phi, P, T(M), inv(mm(M, P, T(M))))  # (28)
    Ps = sub(Phi, mm(D, M))  # (29)
    Pn = add(mm(Ps, P, T(Phi)), Q)  # (30)
    return D, Ps, Pn


def line(s=""):
    print(s)


# ---------------------------------------------------------------- 셈 1 · 2: 식 (24) 둘째 줄, 식 (32)
rng = random.Random(0)
n, p = 4, 2
P = randspd(rng, n)
Phi = randmat(rng, n, n)
M = randmat(rng, p, n)
Q = randspd(rng, n)
D, Ps, Pn = kalman_step(P, Phi, M, Q)
line("셈 1. 식 (24) 둘째 줄: Phi* P Phi*' 와 Phi* P Phi' 가 같은가 (n=4, p=2, 무작위 행렬)")
line(f"  max|Phi* P M'| = {maxabs(mm(Ps, P, T(M))):.1e}   (이것이 0 이라 두 줄이 같다)")
line(f"  max|Phi* P Phi*' - Phi* P Phi'| = {maxabs(sub(mm(Ps, P, T(Ps)), mm(Ps, P, T(Phi)))):.1e}")
line()
line("셈 2. 식 (32) 의 끝 곱 P*(t)M(t) 를 M(t)P*(t) 로 바꾸면 식 (30) 과 같은가")
P32 = add(mm(Phi, sub(P, mm(P, T(M), inv(mm(M, P, T(M))), M, P)), T(Phi)), Q)
line(f"  max|(32, M P 로 고친 것) - (30)| = {maxabs(sub(P32, Pn)):.1e}")
try:
    mm(P, M)
    line("  P M 이 정의된다")
except ValueError as e:
    line(f"  인쇄된 그대로 P*(t)M(t) 는 곱이 정의되지 않는다: {e}")
line()

# ---------------------------------------------------------------- 셈 3 · 4: 예 1
a, b, phi = 1.3, 0.7, 0.8
Phi1 = mat([[phi, 0], [0, 0]])
M1 = mat([[1, 1]])
Q1 = mat([[a * a, 0], [0, b * b]])
P = mat([[a * a, 0], [0, b * b]])  # P*(1). P*(0) = diag(0, b^2) 이면 Delta*(0) = 0, C(0) = 0
C = 1 - b * b / (a * a + b * b)  # C(1)
dev, d12 = 0.0, []
for t in range(1, 30):
    D, Ps, Pn = kalman_step(P, Phi1, M1, Q1)
    want_P = mat([[a * a + phi * phi * b * b * C, 0], [0, b * b]])
    dev = max(dev, abs(D[0][0] - phi * C), abs(D[1][0]), abs(Ps[0][0] - phi * (1 - C)),
              abs(Ps[1][0]), abs(Ps[1][1]), maxabs(sub(Pn, want_P)))
    d12.append((t, Ps[0][1], -phi * C))
    C = 1 - b * b / (a * a + b * b + phi * phi * b * b * C)
    P = Pn
line(f"셈 3. 예 1 (a={a}, b={b}, phi11={phi}): 식 (28) ~ (30) 을 돌린 값과 식 (38) 의 닫힌 꼴, t = 1 ~ 29")
line(f"  Phi*_12 를 뺀 모든 칸의 최대 차 = {dev:.1e}")
line(f"  Phi*_12: 돌린 값 {d12[0][1]:.6f} (t=1), {d12[-1][1]:.6f} (t=29). -phi11 C(t) 와의 최대 차 "
     f"{max(abs(x - y) for _, x, y in d12):.1e}")
line("  원문은 이 칸을 0 으로 적는다. x2*(t|t-1) = 0 이라 이 칸이 곱하는 값이 늘 0 이기 때문이다(원문 9 쪽).")
line()


def c_inf(r, phi=0.8, steps=2000):
    c = 0.0
    for _ in range(steps):
        c = 1 - r / (1 + r + phi * phi * r * c)
    return c


line("셈 4. 예 1 의 C(t) 가 수렴하는 값, b^2/a^2 셋 (phi11 = 0.8, C(0) = 0, 2,000 걸음)")
for r in (0.01, 1.0, 100.0):
    ci, c12 = c_inf(r), c_inf(r, steps=12)
    line(f"  b^2/a^2 = {r:>6}: C(inf) = {ci:.4f}   C(12) = {c12:.4f}   차 {abs(ci - c12):.1e}")
# 원문 43 쪽: t = inf 를 넣어 C(inf) 의 이차 방정식을 푼다. a = 1.3, b = 0.7 (b^2/a^2 = 0.29)
a, b, phi = 1.3, 0.7, 0.8
qa, qb, qc = phi * phi * b * b, a * a + b * b - phi * phi * b * b, -a * a
root = (-qb + math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa)
line(f"  a={a}, b={b}: 이차 방정식의 근 C(inf) = {root:.6f},  반복 2,000 걸음 {c_inf(b * b / (a * a)):.6f}")
line()

# ---------------------------------------------------------------- 셈 5 · 6: 예 2
a, b, phi = 1.3, 0.7, 0.6
Phi2 = mat([[1, 1, 0], [0, 1, 0], [0, 0, phi]])
M2 = mat([[1, 0, 1]])
Q2 = mat([[0, 0, 0], [0, 0, 0], [0, 0, b * b]])
P = mat([[a * a, a * a, 0], [a * a, a * a, 0], [0, 0, b * b]])  # P*(1), 원문 9 쪽
C1 = {0: b * b / (a * a)}
C2 = {0: 0.0}
for t in range(1, 1001):
    C2[t] = t - phi * (t - 1)
    C1[t] = C1[t - 1] + C2[t] ** 2
Pinv = inv(Phi2)
wP = wD = wS = wC = 0.0
for t in range(1, 201):
    c1p = C1[t - 1]
    want_P = scale(b * b / c1p, mat([
        [t * t, t, -phi * t * (t - 1)],
        [t, 1, -phi * (t - 1)],
        [-phi * t * (t - 1), -phi * (t - 1), phi ** 2 * (t - 1) ** 2 + c1p]]))
    wP = max(wP, maxabs(sub(P, want_P)) / maxabs(P))
    D, Ps, Pn = kalman_step(P, Phi2, M2, Q2)
    c1, c2 = C1[t], C2[t]
    want_D = scale(1 / c1, mat([[t * c2], [c2], [c1 - t * c2]]))
    wD = max(wD, maxabs(sub(mm(Pinv, D), want_D)))
    S = mm(Pinv, Ps, Phi2)
    want_S = scale(1 / c1, mat([  # (1,2) 칸의 C3 를 C2 로 읽은 것
        [c1 - t * c2, c1 - t * c2, -phi * t * c2],
        [-c2, c1 - c2, -phi * c2],
        [-c1 + t * c2, -c1 + t * c2, phi * t * c2]]))
    wS = max(wS, maxabs(sub(S, want_S)))
    covtt = mm(Pinv, sub(Pn, Q2), T(Pinv))
    want_C = scale(b * b / c1, mat([[t * t, t, -t * t], [t, 1, -t], [-t * t, -t, t * t]]))
    wC = max(wC, maxabs(sub(covtt, want_C)) / maxabs(covtt))
    P = Pn
line(f"셈 5. 예 2 (a={a}, b={b}, phi33={phi}): 돌린 값과 원문 9 ~ 10 쪽 닫힌 꼴, t = 1 ~ 200")
line(f"  P*(t)                       상대 차 최대 {wP:.1e}")
line(f"  Phi(t;t+1) Delta*(t)         최대 차 {wD:.1e}")
line(f"  Phi(t;t+1) Phi* Phi(t+1;t)   최대 차 {wS:.1e}   ((1,2) 칸의 C3(t) 를 C2(t) 로 읽었을 때)")
line(f"  cov x~(t|t)                 상대 차 최대 {wC:.1e}")
line()
line("셈 6. 예 2 의 t = 200 값 (원문은 t >> 1 에서 [[1,1,0],[0,1,0],[-1,-1,0]] 과 [0,0,1]' 로 적는다)")
for r in S:
    line("  " + "  ".join(f"{x:+.4f}" for x in r))
line("  Phi^-1 Delta* = " + "  ".join(f"{x[0]:+.4f}" for x in mm(Pinv, D)))
line()

# ---------------------------------------------------------------- 셈 7: 식 (39) 와 phi33 = 0 근사
line("셈 7. 식 (39) 의 근사와 정확한 합, 그리고 phi33 = 0 일 때 E x~1^2(t|t) 의 근사 (a=1.3, b=0.7)")
for ph in (0.0, 0.6):
    for t in (10, 100, 1000):
        exact = b * b / (a * a) + sum((k - ph * (k - 1)) ** 2 for k in range(1, t + 1))
        approx = (1 - ph) ** 2 * t ** 3 / 3 + ph * (1 - ph) * t ** 2 + ph ** 2 * t + b * b / (a * a)
        line(f"  phi33={ph}  t={t:>4}: C1 정확 {exact:.6g}  식 (39) {approx:.6g}  비 {approx / exact:.4f}")
err_rows = []
for t in (10, 100, 1000):
    c1 = b * b / (a * a) + sum(k * k for k in range(1, t + 1))
    exact = b * b * t * t / c1
    approx = a * a * b * b * t * t / (b * b + a * a * t ** 3 / 3)
    err_rows.append((t, exact, approx))
    line(f"  E x~1^2(t|t), phi33=0, t={t:>4}: 정확 {exact:.6g}  원문 근사 {approx:.6g}  비 {approx / exact:.4f}")
line()

# ---------------------------------------------------------------- 셈 8: 지금 쓰는 꼴과 맞추기
rng = random.Random(1)
n, p, steps = 3, 2, 60
A = scale(0.5, randmat(rng, n, n))
H = randmat(rng, p, n)
Qw = scale(0.3, randspd(rng, n))
R = mat([[0.4, 0], [0, 0.9]])
P0 = eye(n)
ys = [[[rng.gauss(0, 1)] for _ in range(p)] for _ in range(steps)]  # 관측 값 자체는 무엇이든 식 비교에는 상관없다
# 오늘 교과서 꼴(측정 잡음 R 이 있는 꼴): 예측 -> 갱신
xm, Pm, ref = zeros(n, 1), [r[:] for r in P0], []
for y in ys:
    K = mm(Pm, T(H), inv(add(mm(H, Pm, T(H)), R)))
    xh = add(xm, mm(K, sub(y, mm(H, xm))))
    Pp = mm(sub(eye(n), mm(K, H)), Pm)
    xm, Pm = mm(A, xh), add(mm(A, Pp, T(A)), Qw)
    ref.append((xm, Pm))
# 원문 꼴: 측정 잡음을 상태에 넣는다 (예 1 의 x2 처럼). 상태 [x; v], v(t+1) = u2(t), y = [H I][x; v]
Za = zeros(n, p)
PhiA = block([[A, Za], [T(Za), zeros(p, p)]])
MA = block([[H, eye(p)]])
QA = block([[Qw, Za], [T(Za), R]])
PA = block([[P0, Za], [T(Za), R]])
xa = zeros(n + p, 1)
dx = dP = 0.0
for y, (xr, Pr) in zip(ys, ref):
    D, Ps, Pn = kalman_step(PA, PhiA, MA, QA)
    xa = add(mm(Ps, xa), mm(D, y))  # 식 (21)
    PA = Pn
    dx = max(dx, maxabs(sub([r[:1] for r in xa[:n]], xr)))
    dP = max(dP, maxabs(sub([r[:n] for r in PA[:n]], Pr)))
line(f"셈 8. 원문 꼴(잡음을 상태에 넣음)과 R 이 있는 교과서 꼴, n={n}, p={p}, {steps} 걸음")
line(f"  예측값 x*(t+1|t) 최대 차 {dx:.1e},  오차 공분산 최대 차 {dP:.1e}")
K0 = mm(P0, T(H), inv(mm(H, P0, T(H))))
D0 = mm(A, P0, T(H), inv(mm(H, P0, T(H))))
line(f"  R = 0 이면 Delta* = Phi K:  max|Delta* - A K| = {maxabs(sub(D0, mm(A, K0))):.1e}")
line()

# ---------------------------------------------------------------- 셈 9: 쌍대 정리
rng = random.Random(2)
n, p, N = 3, 2, 12
Phis = [randmat(rng, n, n) for _ in range(N)]
Ms = [randmat(rng, p, n) for _ in range(N)]
Qs = [randspd(rng, n) for _ in range(N)]
P = randspd(rng, n)
fwd = [P]
for k in range(N):
    _, _, P = kalman_step(P, Phis[k], Ms[k], Qs[k])
    fwd.append(P)
# 식 (35) ~ (37) 을 T 에서 거꾸로. X(t0 + tau) -> Xhat'(T - tau)
Ph = fwd[0]
worst = 0.0
for tau in range(N):
    Phih, Mh, Qh = T(Phis[tau]), T(Ms[tau]), Qs[tau]
    Dh = mm(inv(mm(T(Mh), Ph, Mh)), T(Mh), Ph, Phih)  # (35)
    Phish = sub(Phih, mm(Mh, Dh))  # (36)
    Ph = add(mm(T(Phih), Ph, Phish), Qh)  # (37)
    worst = max(worst, maxabs(sub(Ph, fwd[tau + 1])))
line(f"셈 9. 쌍대 정리: 식 (35) ~ (37) 을 바꿔 넣은 행렬로 거꾸로 돌린 P^ 과 식 (28) ~ (30) 의 P*, {N} 걸음")
line(f"  최대 차 {worst:.1e},  P* 칸 절댓값의 최댓값 {max(maxabs(X) for X in fwd):.3g}")


# ---------------------------------------------------------------- 그림
FONT = "'Malgun Gothic','Noto Sans KR',sans-serif"


def txt(x, y, s, size=12, fill="#222222", anchor="start", bold=False):
    w = "bold" if bold else "normal"
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{w}" font-family="{FONT}">{s}</text>')


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")


COLORS = ["#2f6db3", "#8a8a8a", "#c8553d"]

# 그림 1: 예 1 의 C(t)
W, Hh, L, R_, Tp, B = 900, 380, 70, 220, 50, 60
pw, ph = W - L - R_, Hh - Tp - B
tmax = 12
X = lambda t: L + pw * t / tmax
Y = lambda v: Tp + ph * (1 - v)
body = [txt(20, 28, "예 1: 측정에 거는 무게 C(t) (원문 식 38, phi11 = 0.8, C(0) = 0)", 15, bold=True)]
for v in (0, 0.25, 0.5, 0.75, 1.0):
    body.append(f'<line x1="{L}" y1="{Y(v):.1f}" x2="{L + pw}" y2="{Y(v):.1f}" stroke="#eeeeee"/>')
    body.append(txt(L - 8, Y(v) + 4, f"{v:.2f}", 11, "#666666", "end"))
for t in range(0, tmax + 1, 2):
    body.append(txt(X(t), Tp + ph + 18, str(t), 11, "#666666", "middle"))
body.append(txt(L + pw / 2, Hh - 14, "t (관측 걸음)", 12, "#444444", "middle"))
body.append(f'<line x1="{L}" y1="{Tp + ph}" x2="{L + pw}" y2="{Tp + ph}" stroke="#999999"/>')
for (r, label), col in zip([(0.01, "b²/a² = 0.01 (잡음 작음)"), (1.0, "b²/a² = 1"), (100.0, "b²/a² = 100 (잡음 큼)")], COLORS):
    c, pts = 0.0, [(0, 0.0)]
    for t in range(1, tmax + 1):
        c = 1 - r / (1 + r + 0.64 * r * c)
        pts.append((t, c))
    body.append('<polyline fill="none" stroke="{}" stroke-width="2" points="{}"/>'.format(
        col, " ".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in pts)))
    for t, v in pts:
        body.append(f'<circle cx="{X(t):.1f}" cy="{Y(v):.1f}" r="2.5" fill="{col}"/>')
    body.append(txt(L + pw + 10, Y(pts[-1][1]) + 4, f"{label}: {pts[-1][1]:.3f}", 12, col))
body.append(txt(L + pw + 10, Tp - 10, "오른쪽 숫자 = C(12), 내 셈", 11, "#666666"))
(HERE / "fig01_example1_gain.svg").write_text(svg(W, Hh, body), encoding="utf-8")

# 그림 2: 예 2 의 위치 오차 분산, phi33 = 0
W, Hh, L, R_, Tp, B = 900, 400, 80, 240, 50, 60
pw, ph = W - L - R_, Hh - Tp - B
a, b = 1.3, 0.7
ts = sorted(set(int(round(10 ** (k / 20))) for k in range(0, 61)))
exact = []
for t in ts:
    c1 = b * b / (a * a) + t * (t + 1) * (2 * t + 1) / 6
    exact.append((t, b * b * t * t / c1, a * a * b * b * t * t / (b * b + a * a * t ** 3 / 3)))
ymin, ymax = -3.5, 0.0
X = lambda t: L + pw * math.log10(t) / 3
Y = lambda v: Tp + ph * (ymax - math.log10(v)) / (ymax - ymin)
body = [txt(20, 28, "예 2: 위치 오차 분산 E x~1²(t|t), phi33 = 0 (a = 1.3, b = 0.7)", 15, bold=True)]
for e in (0, -1, -2, -3):
    body.append(f'<line x1="{L}" y1="{Y(10 ** e):.1f}" x2="{L + pw}" y2="{Y(10 ** e):.1f}" stroke="#eeeeee"/>')
    body.append(txt(L - 8, Y(10 ** e) + 4, f"1e{e}", 11, "#666666", "end"))
for e in (0, 1, 2, 3):
    body.append(txt(X(10 ** e), Tp + ph + 18, str(10 ** e), 11, "#666666", "middle"))
body.append(txt(L + pw / 2, Hh - 14, "t (관측 걸음, 로그 눈금)", 12, "#444444", "middle"))
body.append(f'<line x1="{L}" y1="{Tp + ph}" x2="{L + pw}" y2="{Tp + ph}" stroke="#999999"/>')
for idx, col, label in ((1, COLORS[0], "정확한 값 b²t²/C1(t)"), (2, COLORS[2], "원문 근사 a²b²t²/(b² + a²t³/3)")):
    body.append('<polyline fill="none" stroke="{}" stroke-width="2" {} points="{}"/>'.format(
        col, 'stroke-dasharray="6 4"' if idx == 2 else "",
        " ".join(f"{X(row[0]):.1f},{Y(row[idx]):.1f}" for row in exact)))
body.append(txt(L + pw + 12, Tp + 20, "정확한 값 b²t²/C1(t) (원문 10 쪽 식)", 12, COLORS[0]))
body.append(txt(L + pw + 12, Tp + 40, "원문 근사 (t >> 1)", 12, COLORS[2]))
body.append(txt(L + pw + 12, Tp + 72, "근사 / 정확 (내 셈)", 12, "#444444", bold=True))
for i, (t, ex, ap) in enumerate(err_rows):
    body.append(txt(L + pw + 12, Tp + 92 + 18 * i, f"t = {t}: {ap / ex:.4f}", 12, "#444444"))
(HERE / "fig02_example2_error.svg").write_text(svg(W, Hh, body), encoding="utf-8")
line()
line("그림 둘을 썼다: fig01_example1_gain.svg, fig02_example2_error.svg")
