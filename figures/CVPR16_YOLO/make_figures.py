# -*- coding: utf-8 -*-
"""YOLO 노트의 그림을 만든다. 표준 라이브러리만 쓰고 바깥 데이터를 읽지 않는다.

표 값은 원문 표 1 ~ 3 · 그림 4 · 그림 5(b) 를 옮긴 상수이고, 파라미터 · 차이 · 비는 여기서 계산해 찍는다.
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


def L(x1, y1, x2, y2, stroke=LINE, width=1, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>'


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#ffffff"/>' + "".join(body) + "</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


LAYERS = [(7, 3, 64), (3, 64, 192), (1, 192, 128), (3, 128, 256), (1, 256, 256), (3, 256, 512)]
LAYERS += [(1, 512, 256), (3, 256, 512)] * 4
LAYERS += [(1, 512, 512), (3, 512, 1024)]
LAYERS += [(1, 1024, 512), (3, 512, 1024)] * 2
LAYERS += [(3, 1024, 1024)] * 4
CONV = sum(k * k * i * o + o for k, i, o in LAYERS)
FC1 = 7 * 7 * 1024 * 4096 + 4096
FC2 = 4096 * 1470 + 1470
TOTAL = CONV + FC1 + FC2

T1 = [("100Hz DPM", "07", 16.0, 100), ("30Hz DPM", "07", 26.1, 30), ("Fast YOLO", "07+12", 52.7, 155), ("YOLO", "07+12", 63.4, 45),
      ("Fastest DPM", "07", 30.4, 15), ("R-CNN Minus R", "07", 53.5, 6), ("Fast R-CNN", "07+12", 70.0, 0.5), ("Faster R-CNN VGG-16", "07+12", 73.2, 7),
      ("Faster R-CNN ZF", "07+12", 62.1, 18), ("YOLO VGG-16", "07+12", 66.4, 21)]


def fig01():
    W, H = 880, 250
    b = [T(20, 24, "YOLO 의 출력 7 x 7 x 30: 칸마다 상자 둘(x, y, w, h, 신뢰도)과 부류 20", 14, weight="bold")]
    ox, oy, cell = 40, 44, 24
    for i in range(8):
        b += [L(ox, oy + i * cell, ox + 7 * cell, oy + i * cell, D), L(ox + i * cell, oy, ox + i * cell, oy + 7 * cell, D)]
    b.append(R(ox + 3 * cell, oy + 3 * cell, cell, cell, "#fbe9e5", B))
    b.append(T(ox + 3.5 * cell, oy + 7 * cell + 18, "칸 한 변 448 / 7 = 64 픽셀", 11, MUTE, "middle"))
    x = 260
    items = [("상자 1", 5, A), ("상자 2", 5, C), ("부류 확률", 20, D)]
    for n, k, col in items:
        w = k * 18
        b += [R(x, 90, w, 40, col), T(x + w / 2, 115, f"{n} ({k})", 11, "#ffffff", "middle")]
        x += w + 4
    b += [T(260, 160, "7 x 7 x 30 = 1,470 출력, 상자 98 개. 칸마다 부류 묶음은 하나다.", 12, MUTE),
          T(260, 182, "그래서 한 이미지의 물체는 칸 수 49 개가 상한이고, 한 칸에 중심이 든 두 물체는 하나만 잡힌다.", 12, MUTE)]
    save("fig01_output_tensor.svg", W, H, b)


def fig02():
    W, H = 720, 220
    rows = [("합성곱 24 층", CONV, A), ("완전 연결 1: 7 x 7 x 1024 → 4096", FC1, B), ("완전 연결 2: 4096 → 1470", FC2, D)]
    m = max(r[1] for r in rows)
    b = [T(20, 24, f"그림 3 을 세면(내 셈, 치우침 포함) 합계 {TOTAL:,}", 14, weight="bold")]
    for i, (n, v, c) in enumerate(rows):
        y = 44 + i * 50
        b += [T(20, y + 12, n, 12), R(20, y + 18, 480 * v / m, 20, c), T(26 + 480 * v / m, y + 33, f"{v:,} ({100 * v / TOTAL:.1f}%)", 12, MUTE)]
    save("fig02_params.svg", W, H, b)


def fig03():
    W, H = 760, 400
    x0, y0, pw, ph = 70, 50, 640, 290
    def X(f):
        return x0 + pw * (math.log10(f) + 0.5) / 2.9
    def Y(m):
        return y0 + ph - ph * (m - 10) / 70
    b = [T(20, 24, "표 1: mAP 대 FPS. 세로선은 원문이 정한 실시간 30 fps. 원은 2007 학습, 네모는 2007 + 2012 학습", 13, weight="bold")]
    for m in (10, 20, 30, 40, 50, 60, 70, 80):
        b += [L(x0, Y(m), x0 + pw, Y(m)), T(x0 - 8, Y(m) + 4, m, 11, MUTE, "end")]
    for f in (1, 10, 100):
        b += [L(X(f), y0, X(f), y0 + ph), T(X(f), y0 + ph + 16, f, 11, MUTE, "middle")]
    b += [L(X(30), y0, X(30), y0 + ph, B, 1, "4 3"), T(X(30) + 4, y0 + 12, "30 fps", 11, B)]
    offs = {"30Hz DPM": (6, 14), "YOLO VGG-16": (-6, -8), "Faster R-CNN ZF": (-6, 16), "R-CNN Minus R": (-6, -8), "Faster R-CNN VGG-16": (8, -4), "Fastest DPM": (-8, -4), "Fast YOLO": (-6, -8), "YOLO": (8, -4)}
    for n, tr, m, f in T1:
        x, y = X(f), Y(m)
        col = B if "YOLO" in n else A
        if tr == "07":
            b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{D}"/>')
        else:
            b.append(R(x - 5, y - 5, 10, 10, col))
        dx, dy = offs.get(n, (8, -4))
        anchor = "end" if dx < 0 else "start"
        b.append(T(x + dx, y + dy, f"{n} {m}", 11, INK, anchor))
    b.append(T(x0 + pw / 2, H - 22, "FPS (로그). 「2 배」 는 다른 학습 데이터끼리 맞댄 값이다: 52.7 / 26.1 = 2.02", 12, MUTE, "middle"))
    save("fig03_tab1_speed_map.svg", W, H, b)


def fig04():
    W, H = 760, 230
    rows = [("Fast R-CNN", [("맞음", 71.6, C), ("위치", 8.6, A), ("유사", 4.3, D), ("기타", 1.9, "#bbbbbb"), ("배경", 13.6, B)]),
            ("YOLO", [("맞음", 65.5, C), ("위치", 19.0, A), ("유사", 6.75, D), ("기타", 4.0, "#bbbbbb"), ("배경", 4.75, B)])]
    b = [T(20, 24, "그림 4 를 띠로: 부류마다 상위 N 개 검출의 판정 (N = 그 부류의 물체 수)", 14, weight="bold")]
    for i, (n, r) in enumerate(rows):
        y = 52 + i * 62
        b.append(T(20, y, n, 12, weight="bold"))
        x = 20
        for lab, v, c in r:
            w = 7 * v
            b.append(R(x, y + 8, w, 28, c))
            if w > 26:
                b.append(T(x + w / 2, y + 27, f"{lab} {v}" if w > 56 else f"{v}", 10.5, "#ffffff", "middle"))
            x += w
    b += [T(20, 190, "위치 오차 19.0 > 나머지 합 15.5 (유사 6.75 + 기타 4.0 + 배경 4.75). 배경 비 13.6 / 4.75 = 2.86 배.", 12, MUTE),
          T(20, 212, "유사 · 기타 · 배경을 합친 오차는 Fast R-CNN 19.8, YOLO 15.5 이고, 위치까지 합치면 28.4 와 34.5 다.", 12, MUTE)]
    save("fig04_fig4_errors.svg", W, H, b)


def fig05():
    W, H = 760, 280
    rows = [("Fast R-CNN (2007 데이터)", 66.9, 72.4), ("Fast R-CNN (VGG-M)", 59.2, 72.4), ("Fast R-CNN (CaffeNet)", 57.1, 72.1), ("YOLO", 63.4, 75.0)]
    b = [T(20, 24, "표 2: 가장 좋은 Fast R-CNN(71.8)에 다른 모델을 합친다. 단독이 낮아도 합치면 오른다", 14, weight="bold")]
    for i, (n, s, c) in enumerate(rows):
        y = 50 + i * 44
        col = B if n == "YOLO" else D
        b += [T(210, y + 16, n, 12, INK, "end"), R(220, y, 5 * s, 12, "#cfd8e3"), T(224 + 5 * s, y + 11, f"단독 {s}", 11, MUTE), R(220, y + 14, 5 * c, 14, col), T(224 + 5 * c, y + 26, f"합침 {c} (+{c - 71.8:.1f})", 11, INK)]
    b.append(T(20, H - 14, "Fast R-CNN 값이 표 1 은 70.0, 표 2 는 71.8 이다. 표 2 의 모델 설정은 적혀 있지 않다.", 12, MUTE))
    save("fig05_tab2_combination.svg", W, H, b)


def fig06():
    W, H = 860, 330
    data = [("YOLO", 59.2, 53.3, 45), ("R-CNN", 54.2, 10.4, 26), ("DPM", 43.2, 37.8, 32), ("Poselets", 36.5, 17.8, None)]
    b = [T(20, 24, "그림 5(b): VOC 2007 에서 그림으로 갈 때 빠지는 양. 점으로 재면 DPM 이 덜 빠지고, 비로 재면 YOLO 가 덜 빠진다", 13, weight="bold")]
    for j, (title, idx) in enumerate((("Picasso", 2), ("People-Art", 3))):
        ox = 20 + j * 420
        b.append(T(ox, 54, title, 13, weight="bold"))
        y = 70
        for d in data:
            if d[idx] is None:
                continue
            drop = d[1] - d[idx]
            ratio = d[idx] / d[1]
            b += [T(ox, y + 14, d[0], 12), R(ox + 70, y, 3 * d[1], 10, "#cfd8e3"), R(ox + 70, y + 12, 3 * d[idx], 10, B if d[0] == "YOLO" else D),
                  T(ox + 70 + 3 * d[1] + 6, y + 18, f"{d[1]} → {d[idx]}", 11, MUTE), T(ox + 70, y + 36, f"-{drop:.1f} 점, 남은 비 {100 * ratio:.1f}%", 11, INK)]
            y += 56
    b.append(T(20, H - 12, "학습 데이터가 다르다: VOC 2007 줄은 2007, Picasso 는 2012, People-Art 는 2010 으로 배웠다.", 12, MUTE))
    save("fig06_fig5_generalization.svg", W, H, b)


def fig07():
    W, H = 760, 330
    d = [("bottle", -14.2, -10.4), ("sheep", -11.2, -9.1), ("tv", -7.9, -7.0), ("car", -7.7, -6.8), ("plant", -1.9, -4.4), ("cat", 0.3, 11.7), ("person", 3.5, 3.3), ("train", 10.4, 12.2)]
    b = [T(20, 24, "표 3: YOLO 대 R-CNN VGG · Feature Edit 의 부류별 AP 차. 원문의 「8 ~ 10%」 는 범위를 넘는다", 14, weight="bold")]
    z = 340
    b.append(L(z, 40, z, 300, INK))
    for i, (n, a, c) in enumerate(d):
        y = 46 + i * 31
        b.append(T(80, y + 16, n, 12, INK, "end"))
        for k, (v, col) in enumerate(((a, A), (c, C))):
            w = 13 * abs(v)
            x = z if v >= 0 else z - w
            b.append(R(x, y + k * 13, w, 12, col))
            b.append(T(x + w + 4 if v >= 0 else x - 4, y + k * 13 + 10, f"{v:+.1f}", 10.5, MUTE, "start" if v >= 0 else "end"))
    b += [R(560, 50, 14, 14, A), T(580, 62, "YOLO - R-CNN VGG", 12), R(560, 74, 14, 14, C), T(580, 86, "YOLO - Feature Edit", 12), T(20, H - 8, "표에 물체 크기가 없다. 「작은 물체」 는 부류 이름으로 짐작한 말이다.", 12, MUTE)]
    save("fig07_tab3_per_class.svg", W, H, b)


def fig08():
    W, H = 760, 240
    rows = [("Faster R-CNN VGG-16", "5 fps, 73.2", "7 fps, 73.2", "K40 / Titan X"), ("Faster R-CNN ZF", "17 fps, 59.9 (07 학습)", "18 fps, 62.1", "K40 / Titan X"), ("Fast R-CNN", "SS 포함 0.5 fps, 70.0", "0.5 fps, 70.0 (표 2 는 71.8)", "")]
    xs = (30, 210, 430, 640)
    b = [T(20, 24, "같은 체계의 값이 두 논문에서 다르다", 14, weight="bold")]
    for x, h in zip(xs, ("체계", "Faster R-CNN NIPS 판", "YOLO 표 1", "장비")):
        b.append(T(x, 56, h, 12, weight="bold"))
    for i, r in enumerate(rows):
        y = 68 + i * 36
        b.append(R(20, y, 720, 30, "#f4f4f4"))
        for x, s in zip(xs, r):
            b.append(T(x, y + 20, s, 12))
    b.append(T(20, H - 16, "YOLO 는 「In our tests」 라 적어 직접 잰 값임을 밝힌다. 그 조건(입력 크기 · 제안 수)은 적혀 있지 않다.", 12, MUTE))
    save("fig08_cross_paper.svg", W, H, b)


def fig09():
    W, H = 880, 190
    nodes = [("DPM", ["창 밀기", "손으로 만든 특징"]), ("R-CNN 계열", ["제안 후 분류", "Faster R-CNN 까지"]), ("MultiGrasp (2014)", ["격자 회귀", "한 물체"]), ("YOLO (이 편)", ["한 번의 회귀", "이미지 전체"]), ("후속 한 단계", ["이 노트는", "아직 안 읽음"])]
    b = [T(20, 24, "이 편의 자리", 14, weight="bold")]
    for i, (a, c) in enumerate(nodes):
        x = 14 + i * 174
        b += [R(x, 50, 158, 100, "#fbe9e5" if i == 3 else "#eef2f7", LINE), T(x + 79, 80, a, 11, INK, "middle", "bold")]
        for k, l in enumerate(c):
            b.append(T(x + 79, 106 + k * 18, l, 11, MUTE, "middle"))
        if i < 4:
            b.append(L(x + 158, 100, x + 174, 100, INK, 1.5))
    save("fig09_lineage.svg", W, H, b)


if __name__ == "__main__":
    for fn in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09):
        fn()
    print("layers", len(LAYERS), "conv", CONV, "fc1", FC1, "fc2", FC2, "total", TOTAL, "fc share", round((FC1 + FC2) / TOTAL, 4), "first 20", sum(k * k * i * o + o for k, i, o in LAYERS[:20]))
    print("sqrt", round(math.sqrt(.2) - math.sqrt(.1), 4), round(math.sqrt(.9) - math.sqrt(.8), 4))
    print("time", 1000 / 45, 1000 / 155, "YOLO/FastRCNN", (1000 / 45) / 2000)
