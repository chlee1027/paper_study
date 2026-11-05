# -*- coding: utf-8 -*-
"""1 차원 두 봉우리 혼합에 참 점수를 넣어 식 (6) 과 식 (13) 을 오일러로 풀어 본다. 신경망도 GPU 도 없다.

p0 = 0.3 N(-2, 0.25^2) + 0.7 N(2, 0.25^2), VP SDE, beta 0.1 ~ 20, t 는 1 에서 1e-3 까지. 입자 200,000 개.
W1 은 정렬한 표본끼리의 평균 절댓값 차이다. 같은 분포에서 뽑은 다른 표본 대조값(표본 잡음 바닥)은 0.0040 이다.
"""
import math
import numpy as np

bmin, bmax = 0.1, 20.0
M = np.array([-2.0, 2.0]); S = 0.25; W = np.array([0.3, 0.7])


def beta(t): return bmin + t * (bmax - bmin)
def B(t): return t * bmin + t * t * (bmax - bmin) / 2


def score(x, t):
    a = np.exp(-B(t) / 2); v = S * S * a * a + 1 - a * a
    d = x[..., None] - M * a
    lp = np.log(W) - .5 * d * d / v - .5 * np.log(v)
    lp -= lp.max(-1, keepdims=True); r = np.exp(lp); r /= r.sum(-1, keepdims=True)
    return (-(d / v) * r).sum(-1)


def run(N, kind, n=200000, seed=0, te=1e-3):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n); ts = np.linspace(1, te, N + 1)
    for i in range(N):
        t = ts[i]; dt = ts[i] - ts[i + 1]; b = beta(t); s = score(x, t)
        if kind == "sde":
            x = x + (.5 * b * x + b * s) * dt + np.sqrt(b * dt) * rng.standard_normal(n)
        else:
            x = x + (.5 * b * x + .5 * b * s) * dt
    return x


def truth(n=200000, seed=1, te=1e-3):
    rng = np.random.default_rng(seed)
    a = math.exp(-B(te) / 2); v = S * S * a * a + 1 - a * a
    return M[rng.choice(2, n, p=W)] * a + math.sqrt(v) * rng.standard_normal(n)


if __name__ == "__main__":
    T = np.sort(truth())
    print("truth", T.mean(), T.std(), (T > 0).mean(), "floor", np.abs(np.sort(truth(seed=2)) - T).mean())
    for N in (5, 10, 20, 50, 100, 200, 1000):
        for k in ("sde", "ode"):
            x = np.sort(run(N, k))
            print(N, k, round(x.mean(), 4), round(x.std(), 4), round((x > 0).mean(), 4), round(np.abs(x - T).mean(), 4))
