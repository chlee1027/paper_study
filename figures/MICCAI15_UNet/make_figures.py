# -*- coding: utf-8 -*-
"""U-Net 노트의 그림을 만든다. 표준 라이브러리만 쓰고 바깥 데이터를 읽지 않는다.

표 값은 원문 표 1 · 2 를 옮긴 상수이고, 크기 · 파라미터 · 가중치는 여기서 계산해 찍는다.
"""
import math
import os

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = "'Malgun Gothic','Noto Sans KR',sans-serif"
INK, MUTE, LINE = "#222222", "#666666", "#cccccc"
A, B, C, D = "#2f6db3", "#c8553d", "#4a9a6a", "#8a8a8a"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(x, y, s, size=13, fill=INK, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" font-family="{FONT}">{esc(s)}</text>')


def R(x, y, w, h, fill, stroke="none"):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}"/>'


def L(x1, y1, x2, y2, stroke=LINE, width=1):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"/>'


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def conv(k, i, o):
    return k * k * i * o + o


CH = [64, 128, 256, 512, 1024]


def params():
    down, prev = [], 1
    for c in CH:
        down.append(conv(3, prev, c) + conv(3, c, c))
        prev = c
    up = [conv(2, 2 * c, c) + conv(3, 2 * c, c) + conv(3, c, c) for c in reversed(CH[:-1])]
    return down, up, conv(1, 64, 2)


def sizes(n=572):
    tr = [n]
    for _ in range(4):
        n -= 4
        tr.append(n)
        n //= 2
        tr.append(n)
    n -= 4
    tr.append(n)
    for _ in range(4):
        n *= 2
        tr.append(n)
        n -= 4
        tr.append(n)
    return tr


def fig01():
    tr = sizes()
    W, H = 860, 330
    x0, y0, pw, ph = 60, 40, 770, 230
    b = [T(x0, 24, "그림 1 의 x-y 크기를 따라간다 (내가 다시 셈): 572 입력에서 388 출력", 14, weight="bold")]
    for v in (0, 200, 400, 600):
        y = y0 + ph - ph * v / 600
        b += [L(x0, y, x0 + pw, y), T(x0 - 8, y + 4, v, 11, MUTE, "end")]
    pts = []
    for i, v in enumerate(tr):
        x = x0 + pw * i / (len(tr) - 1)
        y = y0 + ph - ph * v / 600
        pts.append((x, y))
    for i in range(len(pts) - 1):
        b.append(L(*pts[i], *pts[i + 1], A if i < 9 else B, 2))
    for i, v in enumerate(tr):
        dx = 14 if i == 0 or (i and tr[i - 1] - v > 4) else 0
        b.append(T(pts[i][0] + dx, pts[i][1] - 8, v, 11, A if i < 10 else B, "middle"))
    b += [T(x0, H - 30, "파랑: 줄이는 길. 빨강: 늘리는 길. 합성곱 둘마다 4 픽셀씩 줄고, 풀링에서 반이 된다.", 12, MUTE),
          T(x0, H - 12, f"출력 면적 / 입력 면적 = (388 / 572)^2 = {(388 / 572) ** 2:.3f}. 경계는 한쪽 (572 - 388) / 2 = 92 픽셀.", 12, MUTE)]
    save("fig01_size_trace.svg", W, H, b)


def fig02():
    down, up, f = params()
    tot = sum(down) + sum(up) + f
    rows = [(f"줄이는 길 {c}", v, A) for c, v in zip(CH, down)]
    rows += [(f"늘리는 길 {c}", v, B) for c, v in zip(reversed(CH[:-1]), up)]
    rows += [("출력 1x1", f, D)]
    W, H = 780, 60 + 28 * len(rows) + 40
    x0, pw = 150, 440
    m = max(v for _, v, _ in rows)
    b = [T(20, 24, f"단계별 파라미터 (내가 센 값, 치우침 포함, 입력 1 채널 · 출력 2 부류): 합계 {tot:,}", 14, weight="bold")]
    for i, (lab, v, col) in enumerate(rows):
        y = 44 + 28 * i
        b += [T(x0 - 8, y + 14, lab, 12, INK, "end"), R(x0, y, pw * v / m, 20, col),
              T(x0 + pw * v / m + 6, y + 15, f"{v:,} ({100 * v / tot:.1f}%)", 12, MUTE)]
    b.append(T(20, H - 12, "원문은 파라미터 수를 적지 않았다. 맨 아래 단(1024)이 전체의 45.6% 다.", 12, MUTE))
    save("fig02_params_by_stage.svg", W, H, b)


def fig03():
    W, H = 860, 290
    s = 0.33
    b = [T(20, 24, "겹침 조각: 512 x 512 이미지를 572 입력 · 388 출력으로 덮는 최소 배치 (내 계산, 원문은 조각 수를 적지 않았다)", 13, weight="bold")]
    ox, oy = 70, 72
    b.append(R(ox, oy, 512 * s, 512 * s, "#e8eef6", A))
    b.append(T(ox + 512 * s / 2, oy + 512 * s + 34, "원본 512 x 512", 12, A, "middle"))
    b.append(R(ox, oy, 388 * s, 388 * s, "none", B))
    b.append(R(ox + 124 * s, oy + 124 * s, 388 * s, 388 * s, "none", C))
    b.append(R(ox - 92 * s, oy - 92 * s, 572 * s, 572 * s, "none", D))
    for i, l in enumerate(["회색: 첫 조각의 입력 572 x 572. 위 · 왼쪽 92 픽셀은 원본 밖이라 거울상으로 채운다",
                           "빨강: 첫 조각의 출력 388 x 388", "초록: 대각 조각의 출력 388 x 388",
                           "한 변에 2 조각이면 2 x 388 = 776 >= 512 라 조각 4 개로 덮인다",
                           "한 변의 겹침은 776 - 512 = 264 픽셀",
                           "거울상까지 넣은 입력 영역은 한 변 512 + 2 x 92 = 696 픽셀"]):
        b.append(T(290, 80 + 28 * i, l, 13, INK if i < 3 else MUTE))
    save("fig03_overlap_tile.svg", W, H, b)


def fig04():
    W, H = 720, 320
    x0, y0, pw, ph = 70, 40, 610, 220
    b = [T(x0, 24, "식 (2) 의 경계 항: w0 exp(-(d1 + d2)^2 / (2 sigma^2)), w0 = 10, sigma = 5", 14, weight="bold")]
    for v in (0, 2, 4, 6, 8, 10):
        y = y0 + ph - ph * v / 10
        b += [L(x0, y, x0 + pw, y), T(x0 - 8, y + 4, v, 11, MUTE, "end")]
    pts = []
    for i in range(0, 301):
        d = i / 10
        pts.append(f"{x0 + pw * d / 30:.1f},{y0 + ph - ph * math.exp(-d * d / 50):.1f}")
    b.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{A}" stroke-width="2"/>')
    for d in (0, 2, 5, 10, 15, 20, 30):
        v = 10 * math.exp(-d * d / 50)
        x, y = x0 + pw * d / 30, y0 + ph - ph * v / 10
        lab = f"{v:.2f}" if v >= 0.1 else f"{v:.4f}"
        b += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{B}"/>', T(x + 5, y - 6, lab, 11, B),
              T(x, y0 + ph + 16, d, 11, MUTE, "middle")]
    b.append(T(x0 + pw / 2, y0 + ph + 36, "d1 + d2 (픽셀): 가장 가까운 세포 경계까지 + 둘째로 가까운 세포 경계까지", 12, MUTE, "middle"))
    save("fig04_border_weight.svg", W, H, b)


T1 = [("u-net", 0.000353, 0.0382, 0.0611), ("DIVE-SCI", 0.000355, 0.0305, 0.0584),
      ("IDSIA [2]", 0.000420, 0.0504, 0.0613), ("DIVE", 0.000430, 0.0545, 0.0582),
      ("IDSIA-SCI", 0.000653, 0.0189, 0.1027)]


def fig05():
    W, H = 880, 280
    b = [T(20, 24, "표 1 을 지표마다 따로 줄 세운다 (작을수록 좋다). 원문 표는 왜곡 오차 순이고 5 ~ 9 위가 빠져 있다", 14, weight="bold")]
    for j, (name, idx) in enumerate([("왜곡 오차", 1), ("Rand 오차", 2), ("픽셀 오차", 3)]):
        ox = 20 + j * 290
        rows = sorted(T1, key=lambda r: r[idx])
        m = max(r[idx] for r in rows)
        b.append(T(ox, 54, name, 13, weight="bold"))
        for i, r in enumerate(rows):
            y = 66 + i * 34
            col = B if r[0] == "u-net" else D
            lab = f"{r[idx]:.6f}" if idx == 1 else f"{r[idx]:.4f}"
            b += [T(ox, y + 14, r[0], 11), R(ox + 70, y, 110 * r[idx] / m, 20, col),
                  T(ox + 70 + 110 * r[idx] / m + 4, y + 15, lab, 11, MUTE)]
    b.append(T(20, H - 14, "보인 다섯 행 안에서 u-net 이 1 위인 지표는 왜곡 오차 하나고, 2 위 DIVE-SCI 와의 차이는 0.000002 다.", 12, MUTE))
    save("fig05_tab1_by_metric.svg", W, H, b)


def fig06():
    W, H = 760, 290
    rows = [("PhC-U373", [("IMCB-SG 2014", .2669), ("HOUS-US 2014", .5323), ("KTH-SE 2014", .7953), ("2015 둘째", .83), ("u-net 2015", .9203)]),
            ("DIC-HeLa", [("IMCB-SG 2014", .2935), ("2015 둘째", .46), ("KTH-SE 2014", .4607), ("u-net 2015", .7756)])]
    b = [T(20, 24, "표 2 의 IOU. 흩어짐과 시험 이미지 수는 원문에 적혀 있지 않다", 14, weight="bold")]
    for j, (n, r) in enumerate(rows):
        ox = 20 + j * 370
        b.append(T(ox, 54, n, 13, weight="bold"))
        for i, (a, v) in enumerate(r):
            y = 66 + i * 34
            b += [T(ox, y + 14, a, 11), R(ox + 95, y, 190 * v, 20, B if a.startswith("u-net") else D),
                  T(ox + 95 + 190 * v + 4, y + 15, v, 11, MUTE)]
    b.append(T(20, H - 14, "차이: U373 0.9203 - 0.83 = 0.0903, HeLa 0.7756 - 0.46 = 0.3156. 둘째 값은 원문이 소수 둘째 자리까지만 적었다.", 12, MUTE))
    save("fig06_tab2_iou.svg", W, H, b)


def fig07():
    W, H = 780, 290
    rows = [("겹침 조각 · 거울상", "그림 2 로만 보인다"), ("경계 가중치 식 (2)", "그림 3d 로만 보인다"),
            ("탄성 변형", "결론의 「덕분에」 뿐, 끈 실험을 찾지 못했다"), ("길게 잇는 연결", "끈 실험을 찾지 못했다"),
            ("드롭아웃", "뺀 값도, 비율도 적혀 있지 않다"), ("7 회전 평균", "EM 값에 쓰였고, 뺀 값은 적혀 있지 않다"),
            ("표 1 · 표 2", "최종 모델의 값이 데이터마다 한 줄씩")]
    b = [T(20, 24, "장치마다 그 장치를 뺀 값이 있는가 (읽은 8 쪽 안에서)", 14, weight="bold")]
    for i, (a, c) in enumerate(rows):
        y = 44 + i * 34
        b += [R(20, y, 740, 28, "#f4f4f4"), T(32, y + 19, a, 13), T(250, y + 19, c, 12, B if i < 6 else MUTE)]
    save("fig07_no_ablation.svg", W, H, b)


def fig08():
    W, H = 880, 190
    nodes = [("LeNet · AlexNet", ["분류: 이미지", "한 장에 부류 하나"]), ("창 밀기 CNN (2012)", ["픽셀 하나에", "조각 하나"]),
             ("FCN (이 노트는 안 읽음)", ["풀링 뒤에", "올림 층"]), ("U-Net (2015)", ["대칭 · 이어 붙이기", "작은 데이터"]),
             ("DDPM · LDM · AnoDDPM", ["같은 골격에", "시점 · 주의를 더함"])]
    b = [T(20, 24, "이 편의 자리", 14, weight="bold")]
    for i, (a, c) in enumerate(nodes):
        x = 14 + i * 174
        b += [R(x, 50, 158, 100, "#fbe9e5" if i == 3 else "#eef2f7", LINE), T(x + 79, 80, a, 11, INK, "middle", "bold")]
        for k, l in enumerate(c):
            b.append(T(x + 79, 106 + k * 18, l, 11, MUTE, "middle"))
        if i < 4:
            b.append(L(x + 158, 100, x + 174, 100, INK, 1.5))
    save("fig08_lineage.svg", W, H, b)


if __name__ == "__main__":
    for fn in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08):
        fn()
    down, up, f_ = params()
    tot = sum(down) + sum(up) + f_
    print("params", tot, "down", sum(down), "up", sum(up), "bottom share", round(down[-1] / tot, 4))
    extra = sum(9 * c * c for c in CH[:-1])
    print("concat extra", extra, round(extra / tot, 4))
    print("sizes", sizes(), "area", round((388 / 572) ** 2, 4))
    print("he std", round(math.sqrt(2 / 576), 4), "pixels 30 images", 30 * 512 * 512, round(tot / (30 * 512 * 512), 2))
