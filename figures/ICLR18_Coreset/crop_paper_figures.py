# -*- coding: utf-8 -*-
r"""코어셋 원문에서 그림을 잘라 png 로 두고, 그림 3 · 4 · 5 · 6 의 벡터 좌표를 읽어 찍는다.

PyMuPDF · numpy · scipy 가 필요하다. make_figures.py 의 상수 FIG34 · FIG6 · FIG5 가 여기서 찍힌 값이다.

  python -I crop_paper_figures.py

좌표 읽는 법: 패널마다 흰 격자선의 위치를 눈금 글자와 짝지어 축을 맞춘다. 평균 선은 원문 표식이 놓인
꺾은선이고, 띠는 반투명 다각형이라 점마다 위 · 아래 값이 함께 나온다. 평균은 띠의 가운데와 소수 둘째
자리까지 같았다(약지도 CIFAR-100 의 이 편의 방법 x = 0.3 은 평균 선에서 꼭짓점이 빠져 있어 띠에서 읽었다).
"""
import os

import numpy as np
import pymupdf
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "..", "papers", "ICLR18_Coreset_Active_Learning_for_Convolutional_Neural_Networks_A_Core_Set_Approach.pdf")
COL = {(0.894, 0.102, 0.11): 'Random', (1.0, 0.506, 0.003): 'Empirical', (0.601, 0.308, 0.632): 'Oracle',
       (0.993, 0.987, 0.199): 'DBAL', (0.304, 0.683, 0.293): 'BMDR', (0.216, 0.495, 0.72): 'KMedian',
       (0.959, 0.508, 0.745): 'Ours', (0.659, 0.341, 0.171): 'CEAL'}


def crops(d):
    for name, pno, rect in [("paper_fig1_cover", 4, (140, 62, 470, 240)),
                            ("paper_fig2_mip_variables", 6, (315, 113, 500, 250)),
                            ("paper_fig3_weak", 7, (105, 80, 510, 195)),
                            ("paper_fig4_full", 7, (105, 212, 510, 322)),
                            ("paper_fig5_tsne", 8, (108, 85, 305, 222)),
                            ("paper_fig6_greedy", 8, (310, 160, 512, 303))]:
        d[pno].get_pixmap(dpi=200, clip=pymupdf.Rect(*rect)).save(os.path.join(HERE, name + ".png"))


def key(c):
    return tuple(round(v, 3) for v in c)


def curves(pg):
    dr = pg.get_drawings()
    words = pg.get_text("words")
    panels = [x['rect'] for x in dr if x['type'] == 'f' and x.get('fill') and round(x['fill'][0], 3) == 0.918]
    panels = sorted(panels, key=lambda r: (round(r.y0 / 50), r.x0))
    names = ['W_CIFAR10', 'W_CIFAR100', 'W_SVHN', 'F_CIFAR10', 'F_CIFAR100', 'F_SVHN']
    for nm, r in zip(names, panels):
        hs, vs = set(), set()
        for x in dr:
            if x['type'] == 's' and x.get('color') and key(x['color']) == (1.0, 1.0, 1.0) and len(x['items']) == 1:
                a, b = x['items'][0][1:3]
                if abs(a.y - b.y) < .01 and r.x0 - 1 <= a.x <= r.x1 + 1 and r.y0 - 1 <= a.y <= r.y1 + 1 and abs(a.x - b.x) > .8 * r.width:
                    hs.add(round(a.y, 3))
                if abs(a.x - b.x) < .01 and r.x0 - 1 <= a.x <= r.x1 + 1 and r.y0 - 1 <= a.y <= r.y1 + 1 and abs(a.y - b.y) > .8 * r.height:
                    vs.add(round(a.x, 3))
        ylab = [(.5 * (w[1] + w[3]), float(w[4])) for w in words if r.x0 - 8 < w[2] < r.x0 + 1 and r.y0 - 6 <= .5 * (w[1] + w[3]) <= r.y1 + 6 and w[4].replace('.', '').isdigit()]
        xlab = [(.5 * (w[0] + w[2]), float(w[4])) for w in words if r.y1 - 1 < w[1] < r.y1 + 10 and r.x0 - 8 <= .5 * (w[0] + w[2]) <= r.x1 + 8 and w[4].replace('.', '').isdigit()]
        yc = [(h, min(ylab, key=lambda t: abs(t[0] - h))[1]) for h in sorted(hs)]
        xc = [(v, min(xlab, key=lambda t: abs(t[0] - v))[1]) for v in sorted(vs)]
        Y = lambda p: yc[0][1] + (p - yc[0][0]) * (yc[-1][1] - yc[0][1]) / (yc[-1][0] - yc[0][0])
        X = lambda p: xc[0][1] + (p - xc[0][0]) * (xc[-1][1] - xc[0][1]) / (xc[-1][0] - xc[0][0])
        print("==", nm)
        for x in dr:
            if x['type'] == 'f' and x.get('fill_opacity') and x['fill_opacity'] < .5 and key(x['fill']) in COL:
                pts = [x['items'][0][1]] + [i[2] for i in x['items']]
                if all(r.x0 - 1 <= q.x <= r.x1 + 1 and r.y0 - 1 <= q.y <= r.y1 + 1 for q in pts):
                    rows = {}
                    for q in pts:
                        rows.setdefault(round(X(q.x), 3), []).append(Y(q.y))
                    print(" ", COL[key(x['fill'])], [(k, round((min(v) + max(v)) / 2, 2), round((max(v) - min(v)) / 2, 2)) for k, v in sorted(rows.items())])


def fig5(pg):
    pts = {'R': [], 'B': [], 'G': []}
    for x in pg.get_drawings():
        if x['type'] != 'fs' or not x.get('fill') or len(x['items']) != 8:
            continue
        k = {(0.86, 0.371, 0.34): 'R', (0.371, 0.34, 0.86): 'B', (0.34, 0.86, 0.371): 'G'}.get(key(x['fill']))
        if k:
            r = x['rect']
            pts[k].append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2))
    A = {k: np.array(v) for k, v in pts.items()}
    split = 205.05  # 두 패널 사이 3.79 pt 빈틈의 가운데
    for nm, sel in (('a', lambda a: a[:, 0] < split), ('b', lambda a: a[:, 0] > split)):
        S = {k: A[k][sel(A[k])] for k in A}
        c = np.vstack([S['B'], S['G']])
        all_d = cKDTree(c).query(S['R'])[0]
        g_d = cKDTree(S['G']).query(S['R'])[0]
        span = np.vstack(list(S.values())).max(0) - np.vstack(list(S.values())).min(0)
        print(nm, {k: len(v) for k, v in S.items()}, 'span', span.round(2), 'blue+green max/p99/med', all_d.max().round(3), np.percentile(all_d, 99).round(3), np.median(all_d).round(3),
              'green max/p99/med', g_d.max().round(3), np.percentile(g_d, 99).round(3), np.median(g_d).round(3))


def fig6(pg):
    for x in pg.get_drawings():
        if x['type'] == 's' and x.get('color') and len(x['items']) == 4 and 310 < x['rect'].x0 < 512 and 160 < x['rect'].y0 < 303:
            pts = [x['items'][0][1]] + [i[2] for i in x['items']]
            print([round(c, 3) for c in x['color']], [(round(q.x, 2), round(q.y, 2)) for q in pts])


if __name__ == "__main__":
    doc = pymupdf.open(PDF)
    crops(doc)
    curves(doc[7])
    fig5(doc[8])
    fig6(doc[8])
