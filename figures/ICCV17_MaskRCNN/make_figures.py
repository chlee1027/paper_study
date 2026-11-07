# -*- coding: utf-8 -*-
"""Mask R-CNN 노트의 그림을 만든다. 표준 라이브러리만 쓰고 바깥 데이터를 읽지 않는다.

표 값은 원문 표 1 ~ 6 을 옮긴 상수이고, 차이 · 비 · 파라미터는 여기서 계산해 찍는다.
"""
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


def L(x1, y1, x2, y2, stroke=LINE, width=1, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>'


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def conv(k, i, o):
    return k * k * i * o + o


def fc(i, o):
    return i * o + o


FCN = 4 * conv(3, 256, 256) + conv(2, 256, 256) + conv(1, 256, 80)
MLP2 = fc(1024, 1024) + fc(1024, 80 * 28 * 28)
MLP3 = 2 * fc(1024, 1024) + fc(1024, 80 * 28 * 28)


def fig01():
    W, H = 780, 240
    rows = [("FCN: conv 256 x 4, deconv, 1 x 1", FCN, B, 33.6), ("MLP: 1024 → 1024 → 80 · 28^2", MLP2, D, 31.5), ("MLP: 1024 → 1024 → 1024 → 80 · 28^2", MLP3, D, 31.5)]
    m = max(r[1] for r in rows)
    b = [T(20, 24, "표 2e 의 마스크 가지 (R50-FPN). 파라미터는 내가 셈, MLP 의 첫 입력 층은 적혀 있지 않아 뺐다", 14, weight="bold")]
    for i, (n, v, c, ap) in enumerate(rows):
        y = 50 + i * 52
        b += [T(20, y + 12, n, 12), R(20, y + 18, 560 * v / m, 20, c), T(26 + 560 * v / m, y + 33, f"{v:,}  (AP {ap})", 12, MUTE)]
    b.append(T(20, H - 12, f"MLP 두 층 / FCN = {MLP2 / FCN:.1f} 배. 출력 하나만 80 x 28 x 28 = 62,720 차원이다.", 12, MUTE))
    save("fig01_mask_branch_params.svg", W, H, b)


def fig02():
    W, H = 860, 240
    st = 16
    rois = [(100, 100 / st, round(100 / st) * st), (120, 120 / st, round(120 / st) * st), (170, 170 / st, round(170 / st) * st)]
    b = [T(20, 24, "RoIPool 의 첫 양자화 [x / 16] 가 경계를 옮기는 양 (내 계산). RoIAlign 은 x / 16 을 그대로 쓴다", 14, weight="bold")]
    x0, sc = 40, 2.0
    y = 80
    for i in range(0, 13):
        x = x0 + sc * (i * st)
        b += [L(x, y, x, y + 16, D), T(x, y - 6, i * st, 10, MUTE, "middle")]
    b.append(L(x0, y + 8, x0 + sc * 192, y + 8, D))
    for k, (v, q, back) in enumerate(rois):
        yy = 120 + k * 32
        b += [f'<circle cx="{x0 + sc * v:.1f}" cy="{yy:.1f}" r="5" fill="{A}"/>', f'<circle cx="{x0 + sc * back:.1f}" cy="{yy:.1f}" r="5" fill="{B}"/>', L(x0 + sc * v, yy, x0 + sc * back, yy, INK, 1.5),
              T(480, yy + 4, f"경계 {v} → {v} / 16 = {q:.2f} → [·] = {round(q)} → {back} 픽셀, 이동 {abs(back - v)}", 12)]
    b += [T(480, 84, "걸음 16 이면 이동은 최대 8 픽셀, 걸음 32 면 최대 16 픽셀", 12, weight="bold")]
    save("fig02_quantization.svg", W, H, b)


def fig03():
    W, H = 720, 280
    b = [T(20, 24, "표 2c 를 두 요인으로 펼친다 (R50-C4, 평균 집계 기준, RoIPool 은 max 만 있음)", 14, weight="bold")]
    x0, y0, cw, ch = 200, 60, 220, 70
    b += [T(x0 + cw / 2, y0 - 10, "쌍선형 없음", 12, anchor="middle", weight="bold"), T(x0 + cw * 1.5, y0 - 10, "쌍선형 있음", 12, anchor="middle", weight="bold"),
          T(x0 - 10, y0 + ch / 2 + 4, "정렬 없음(양자화)", 12, anchor="end", weight="bold"), T(x0 - 10, y0 + ch * 1.5 + 4, "정렬 있음", 12, anchor="end", weight="bold")]
    cells = [(0, 0, "RoIPool  26.9 / 48.8 / 26.4", "#f4f4f4", INK), (1, 0, "RoIWarp  27.1 / 48.9 / 27.1", "#f4f4f4", INK), (0, 1, "이 칸의 값이 표에 없다", "#fbe9e5", B), (1, 1, "RoIAlign  30.3 / 51.2 / 31.5", "#e8eef6", INK)]
    for cx, cy, s, fill, col in cells:
        b += [R(x0 + cx * cw, y0 + cy * ch, cw, ch, fill, LINE), T(x0 + cx * cw + cw / 2, y0 + cy * ch + ch / 2 + 4, s, 12, col, "middle")]
    b += [T(20, H - 44, "세 값은 AP / AP50 / AP75. RoIPool 에서 쌍선형만 더하면 AP +0.2, 그 위에 정렬까지 더하면 +3.2.", 12, MUTE),
          T(20, H - 24, "캡션 「정렬이 유일한 요인」 은 정렬만 있는 칸 없이 내린 판단이다.", 12, MUTE)]
    save("fig03_tab2c_factorial.svg", W, H, b)


def fig04():
    W, H = 780, 330
    rows = [("표 2c AP (C4, 걸음 16)", 26.9, 30.3), ("표 2c AP50", 48.8, 51.2), ("표 2c AP75", 26.4, 31.5), ("표 2d AP (C5, 걸음 32)", 23.6, 30.9), ("표 2d AP50", 46.5, 51.8), ("표 2d AP75", 21.6, 32.1), ("표 6 키포인트 AP (FPN)", 59.8, 64.2), ("표 6 키포인트 AP50", 86.2, 86.6)]
    b = [T(20, 24, "RoIAlign 의 상대 향상 (내 나눔). 머리말의 「10% ~ 50%」 는 AP50 칸과 FPN 을 포함하지 않는다", 14, weight="bold")]
    for i, (n, a, c) in enumerate(rows):
        y = 44 + i * 30
        g = 100 * (c - a) / a
        b += [T(200, y + 15, n, 12, INK, "end"), R(210, y, 9 * g, 20, B if g < 10 else A), T(216 + 9 * g, y + 15, f"{a} → {c}: +{g:.1f}%", 12, MUTE)]
    b.append(T(20, H - 18, "빨강: 10% 미만. FPN 의 mask AP 는 본문에 절대 값 +1.5 만 있어 그림에 넣지 않았다.", 12, MUTE))
    save("fig04_roialign_relative.svg", W, H, b)


def fig05():
    W, H = 760, 300
    b = [T(20, 24, "표 2a 의 줄 사이에서 함께 바뀐 것: 「FPN 이 C4 를 이긴다」 는 한 요인의 비교가 아니다", 14, weight="bold")]
    head = ["", "ResNet-50-C4", "ResNet-50-FPN"]
    rows = [("mask AP (minival)", "30.3", "33.6"), ("머리 (RoI 뒤)", "res5 9 층 + 평균", "fc 2 층 · conv 4 층"), ("마스크 크기 m", "14", "28"), ("학습 RoI N (이미지당)", "64", "512"), ("시험 제안", "300", "1000"), ("RPN 앵커", "5 축척 3 비율", "5 축척 3 비율")]
    xs = (40, 300, 520)
    for x, h in zip(xs, head):
        b.append(T(x, 58, h, 13, weight="bold"))
    for i, r in enumerate(rows):
        y = 70 + i * 32
        b.append(R(30, y, 700, 28, "#f4f4f4" if i else "#e8eef6"))
        for x, s in zip(xs, r):
            b.append(T(x, y + 19, s, 12))
    b.append(T(30, H - 14, "그림 3 · 3.1절에서 옮겼다. 차이 3.3 점을 요인별로 나눈 값은 원문에 없다.", 12, MUTE))
    save("fig05_tab2a_confounds.svg", W, H, b)


def fig06():
    W, H = 780, 280
    rows = [("MNC", 24.6, D), ("FCIS + OHEM", 29.2, D), ("Mask R-CNN R101-C4", 33.1, A), ("FCIS+++ (다중 축척 · 뒤집기 · OHEM)", 33.6, D), ("Mask R-CNN R101-FPN", 35.7, B), ("Mask R-CNN X101-FPN", 37.1, B)]
    b = [T(20, 24, "표 1 test-dev mask AP. R101-C4 는 FCIS+++ 보다 0.5 낮다", 14, weight="bold")]
    for i, (n, v, c) in enumerate(rows):
        y = 48 + i * 36
        b += [T(270, y + 16, n, 12, INK, "end"), R(280, y, 11 * v, 24, c), T(286 + 11 * v, y + 17, v, 12, MUTE)]
    save("fig06_tab1.svg", W, H, b)


def fig07():
    W, H = 860, 300
    names = ["AP", "AP50", "AP75", "APS", "APM", "APL"]
    prior = [("Faster+++", (34.9, 55.7, 37.4, 15.6, 38.7, 50.9)), ("FPN", (36.2, 59.1, 39.0, 18.2, 39.0, 48.2)), ("G-RMI", (34.7, 55.5, 36.7, 13.5, 38.1, 52.0)), ("TDM", (36.8, 57.7, 39.2, 16.2, 39.8, 52.1))]
    ours = [("Mask R101", (38.2, 60.3, 41.7, 20.1, 41.1, 50.2)), ("Mask X101", (39.8, 62.3, 43.4, 22.1, 43.2, 51.2))]
    best = [max(p[1][i] for p in prior) for i in range(6)]
    b = [T(20, 24, "표 3 의 박스 AP 를 지표마다: 앞선 네 줄의 최고값과의 차 (내 셈)", 14, weight="bold")]
    x0, zero = 150, 170
    for j, (n, v) in enumerate(ours):
        for i in range(6):
            d = v[i] - best[i]
            x = x0 + i * 112 + j * 44
            h = 22 * d
            col = A if j == 0 else B
            if d >= 0:
                b.append(R(x, zero - h, 38, h, col))
                b.append(T(x + 19, zero - h - 4, f"+{d:.1f}", 11, MUTE, "middle"))
            else:
                b.append(R(x, zero, 38, -h, col))
                b.append(T(x + 19, zero - h + 14, f"{d:.1f}", 11, MUTE, "middle"))
    for i, n in enumerate(names):
        b.append(T(x0 + i * 112 + 41, 262, f"{n} ({best[i]})", 11, MUTE, "middle"))
    b.append(L(x0 - 10, zero, W - 20, zero, INK, 1))
    b += [R(20, 60, 14, 14, A), T(40, 72, "Mask R101", 12), R(20, 84, 14, 14, B), T(40, 96, "Mask X101", 12), T(20, H - 12, "괄호는 앞선 줄들의 최고값. APL 만 음수다: TDM 52.1 · G-RMI 52.0.", 12, MUTE)]
    save("fig07_tab3_by_metric.svg", W, H, b)


def fig08():
    W, H = 760, 340
    rows = [("상자 AP(사람)", [("상자만", 52.5), ("+ 마스크", 53.6), ("+ 키포인트", 50.7), ("+ 둘 다", 52.0)]), ("마스크 AP(사람)", [("마스크만", 45.8), ("+ 키포인트", 45.1)]), ("키포인트 AP", [("키포인트만", 64.2), ("+ 마스크", 64.7)])]
    b = [T(20, 24, "표 5 다중 과제 (minival, R50-FPN): 차이의 크기가 해석과 맞는가", 14, weight="bold")]
    y = 50
    for n, r in rows:
        b.append(T(20, y + 12, n, 12, weight="bold"))
        base = r[0][1]
        for lab, v in r:
            y += 24
            d = v - base
            col = D if d == 0 else (A if d > 0 else B)
            b += [T(150, y + 12, lab, 12, INK, "end"), R(160, y - 2, 6 * (v - 40), 18, col), T(166 + 6 * (v - 40), y + 12, f"{v}" + ("" if d == 0 else f"  ({d:+.1f})"), 12, MUTE)]
        y += 30
    save("fig08_tab5_multitask.svg", W, H, b)


def fig09():
    W, H = 720, 250
    rows = [("mask R50/R101-C4", [("R101-C4", 32.7, 33.1), ("R101-FPN", 35.4, 35.7), ("X101-FPN", 36.7, 37.1)]), ("keypoint", [("키포인트만", 64.2, 62.7), ("키포인트+마스크", 64.7, 63.1)])]
    b = [T(20, 24, "같은 모델의 minival 과 test-dev: 마스크는 test-dev 가 높고 키포인트는 낮다 (내가 표를 맞댐)", 14, weight="bold")]
    y = 54
    for _, r in rows:
        for lab, a, c in r:
            d = c - a
            b += [T(180, y + 14, lab, 12, INK, "end"), T(190, y + 14, f"minival {a} → test-dev {c}", 12), R(390, y, abs(d) * 90, 20, A if d > 0 else B), T(396 + abs(d) * 90, y + 15, f"{d:+.1f}", 12, MUTE)]
            y += 32
    save("fig09_minival_testdev.svg", W, H, b)


def fig10():
    W, H = 880, 190
    nodes = [("Faster R-CNN (2015)", ["상자와 부류", "RoI 풀링"]), ("FCN · U-Net", ["픽셀마다 부류", "(U-Net 은 읽음)"]), ("FPN (2017, 안 읽음)", ["층별 특징 피라미드"]), ("Mask R-CNN (이 편)", ["RoI 안에서 이진 마스크", "RoIAlign"]), ("키포인트 · 후속", ["같은 틀에", "가지를 더함"])]
    b = [T(20, 24, "이 편의 자리", 14, weight="bold")]
    for i, (a, c) in enumerate(nodes):
        x = 14 + i * 174
        b += [R(x, 50, 158, 100, "#fbe9e5" if i == 3 else "#eef2f7", LINE), T(x + 79, 80, a, 11, INK, "middle", "bold")]
        for k, l in enumerate(c):
            b.append(T(x + 79, 106 + k * 18, l, 11, MUTE, "middle"))
        if i < 4:
            b.append(L(x + 158, 100, x + 174, 100, INK, 1.5))
    save("fig10_lineage.svg", W, H, b)


if __name__ == "__main__":
    for fn in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10):
        fn()
    print("FCN", FCN, "MLP2", MLP2, "MLP3", MLP3, round(MLP2 / FCN, 2))
    print("train", 0.72 * 160000 / 3600, "h, R101 s/iter", 44 * 3600 / 160000, "epochs", 160000 * 16 / 115000)
    print("infer", 195 + 15, 1000 / 210)
