# -*- coding: utf-8 -*-
"""Faster R-CNN 노트의 그림을 만든다. 표준 라이브러리만 쓰고 바깥 데이터를 읽지 않는다.

표 값은 원문 표 1 ~ 5 를, 재현율 곡선은 그림 2 의 PDF 벡터 좌표를 눈금으로 환산해 옮긴 상수다.
앵커 수 · 파라미터 · 시간 몫은 여기서 계산해 찍는다.
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


def anchors(W_, H_, st=16):
    fw, fh = W_ // st, H_ // st
    per, tot = {}, 0
    for s in (128, 256, 512):
        for name, r in (("2:1", 2.0), ("1:1", 1.0), ("1:2", 0.5)):
            w, h = s * math.sqrt(r), s / math.sqrt(r)
            k = 0
            for i in range(fw):
                for j in range(fh):
                    cx, cy = (i + .5) * st, (j + .5) * st
                    tot += 1
                    if cx - w / 2 >= 0 and cy - h / 2 >= 0 and cx + w / 2 <= W_ and cy + h / 2 <= H_:
                        k += 1
            per[(s, name)] = k
    return fw, fh, tot, sum(per.values()), per


PROP = [(128, "2:1", 188, 111), (128, "1:1", 113, 114), (128, "1:2", 70, 92), (256, "2:1", 416, 229), (256, "1:1", 261, 284),
        (256, "1:2", 174, 332), (512, "2:1", 768, 437), (512, "1:1", 499, 501), (512, "1:2", 355, 715)]

XS = (.5, .55, .6, .65, .7, .75, .8, .85, .9, .95, 1.0)
REC = {
    300: {"SS": (.815, .765, .702, .638, .563, .482, .394, .296, .189, .088, .003), "EB": (.788, .761, .729, .695, .644, .55, .401, .216, .088, .023, .003),
          "RPN ZF": (.934, .907, .859, .788, .671, .492, .276, .105, .03, .006, 0), "RPN VGG": (.964, .947, .917, .869, .781, .607, .353, .138, .037, .006, 0)},
    1000: {"SS": (.927, .886, .839, .775, .695, .597, .485, .364, .233, .101, .003), "EB": (.91, .89, .869, .836, .785, .671, .479, .247, .098, .023, .003),
           "RPN ZF": (.974, .957, .93, .876, .765, .563, .313, .118, .034, .006, 0), "RPN VGG": (.985, .971, .954, .917, .836, .658, .38, .149, .04, .006, 0)},
    2000: {"SS": (.954, .924, .876, .819, .736, .634, .512, .384, .243, .105, .003), "EB": (.954, .941, .92, .897, .842, .719, .506, .257, .101, .023, .003),
           "RPN ZF": (.981, .968, .944, .897, .788, .583, .323, .122, .034, .006, 0), "RPN VGG": (.985, .974, .957, .924, .846, .668, .391, .152, .04, .006, 0)},
}
COL = {"SS": INK, "EB": C, "RPN ZF": A, "RPN VGG": B}


def fig01():
    W, H = 880, 230
    b = [T(20, 24, "Faster R-CNN 의 짜임: 합성곱 특징을 RPN 과 Fast R-CNN 이 나눠 쓴다", 14, weight="bold")]
    boxes = [(20, "이미지", "짧은 변 600"), (170, "공유 합성곱", "ZF 5 · VGG 13 층, 걸음 16"), (360, "RPN", "3 x 3 + 1 x 1 둘, 앵커 9"), (540, "NMS 0.7 + 상위 N", "약 2k, 시험 300"), (720, "Fast R-CNN", "RoI 풀링 + 완전 연결")]
    for x, a, c in boxes:
        b += [R(x, 70, 140, 80, "#eef2f7" if a != "RPN" else "#fbe9e5", LINE), T(x + 70, 100, a, 12, INK, "middle", "bold"), T(x + 70, 124, c, 10.5, MUTE, "middle")]
    for x in (160, 330, 510, 690):
        b.append(L(x, 110, x + 10 if x == 160 else x + 30, 110, INK, 1.5))
    b += [L(240, 150, 240, 190, INK, 1), L(240, 190, 790, 190, INK, 1), L(790, 190, 790, 150, INK, 1), T(515, 208, "같은 특징 지도를 다시 쓴다 (시험 때 RPN 추가 계산 10 ms, VGG)", 12, MUTE, "middle")]
    save("fig01_pipeline.svg", W, H, b)


def fig02():
    W, H = 760, 330
    rows = []
    for name, (w_, h_) in (("1000 x 600", (1000, 600)), ("800 x 600", (800, 600))):
        fw, fh, tot, ins, per = anchors(w_, h_)
        rows.append((name, fw, fh, tot, ins, per))
    b = [T(20, 24, "경계를 넘지 않는 앵커 수 (내 계산: 칸 중심 배치 · 넓이 보존 종횡비). 원문: 약 20k, 약 6k", 14, weight="bold")]
    for j, (name, fw, fh, tot, ins, per) in enumerate(rows):
        ox = 20 + j * 370
        b.append(T(ox, 54, f"{name}: {fw} x {fh} x 9 = {tot:,}, 안쪽 {ins:,} ({100 * ins / tot:.1f}%)", 12, weight="bold"))
        m = 1650
        for i, ((s, r), v) in enumerate(per.items()):
            y = 66 + i * 26
            b += [T(ox, y + 13, f"{s}^2 {r}", 11), R(ox + 70, y, 210 * v / m, 18, A), T(ox + 74 + 210 * v / m, y + 14, f"{v:,}", 11, MUTE)]
    b.append(T(20, H - 12, "512^2 1:2 앵커는 세로 724 픽셀이라 짧은 변 600 이미지에 하나도 들어가지 않는다.", 12, MUTE))
    save("fig02_anchor_counts.svg", W, H, b)


def fig03():
    W, H = 800, 330
    b = [T(20, 24, "앵커와 학습된 평균 제안 (ZF, s = 600, 원문 표에서 내가 나눔)", 14, weight="bold"),
         T(150, 50, "넓이 / 앵커 넓이", 12, weight="bold"), T(500, 50, "가로 / 세로 (앵커 값과 맞대기)", 12, weight="bold")]
    for i, (s, r, w, h) in enumerate(PROP):
        y = 60 + i * 27
        area = w * h / (s * s)
        ratio = w / h
        target = {"2:1": 2, "1:1": 1, "1:2": .5}[r]
        b += [T(20, y + 14, f"{s}^2 {r} → {w}x{h}", 11), R(150, y, 130 * area, 18, A), T(154 + 130 * area, y + 14, f"{area:.2f}", 11, MUTE),
              R(500, y, 100 * ratio, 18, C), L(500 + 100 * target, y - 2, 500 + 100 * target, y + 20, B, 2), T(504 + 100 * ratio + (100 * max(0, target - ratio)), y + 14, f"{ratio:.2f} (앵커 {target})", 11, MUTE)]
    save("fig03_anchor_vs_proposal.svg", W, H, b)


def fig04():
    W, H = 760, 310
    data = [("상자 점수 사용", A, [(100, 55.1), (300, 56.8), (1000, 56.3)]), ("cls 끔 (무작위 N)", B, [(100, 44.6), (300, 51.4), (1000, 55.8)]), ("reg 끔 (앵커 그대로)", C, [(300, 52.1), (1000, 51.3)])]
    x0, y0, pw, ph = 70, 50, 420, 210
    def X(n):
        return x0 + pw * (math.log10(n) - 2) / 1.0
    def Y(v):
        return y0 + ph - ph * (v - 42) / 18
    b = [T(20, 24, "표 1 소거 실험: SS 2k 로 배운 Fast R-CNN + ZF 를 고정하고 시험 때 제안만 바꾼다", 14, weight="bold")]
    for v in (44, 48, 52, 56, 60):
        b += [L(x0, Y(v), x0 + pw, Y(v)), T(x0 - 8, Y(v) + 4, v, 11, MUTE, "end")]
    for n in (100, 300, 1000):
        b.append(T(X(n), y0 + ph + 18, n, 11, MUTE, "middle"))
    for name, col, pts in data:
        for (a, u), (c, v) in zip(pts, pts[1:]):
            b.append(L(X(a), Y(u), X(c), Y(v), col, 2))
        for n, v in pts:
            b += [f'<circle cx="{X(n):.1f}" cy="{Y(v):.1f}" r="4" fill="{col}"/>', T(X(n) + 6 if n < 1000 else X(n) - 6, Y(v) + (16 if name.startswith("cls") else -6), v, 11, col, "start" if n < 1000 else "end")]
    b += [L(x0, Y(55.2), x0 + pw, Y(55.2), D, 1, "4 3"), T(x0 + 8, Y(55.2) + 15, "NMS 없음 6k: 55.2", 11, D)]
    for i, (name, col, _) in enumerate(data):
        b += [R(530, 70 + i * 26, 14, 14, col), T(552, 82 + i * 26, name, 12)]
    b += [T(530, 170, "상자 점수 대 끔의 차(내 셈)", 12, weight="bold"), T(530, 192, "N = 100: 10.5", 12, MUTE), T(530, 212, "N = 300: 5.4", 12, MUTE), T(530, 232, "N = 1000: 0.5", 12, MUTE),
          T(70, H - 6, "세로: mAP (%), 가로: 제안 수(로그). 표 1 에 흩어짐이 없다.", 12, MUTE)]
    save("fig04_tab1_ablation.svg", W, H, b)


def fig05():
    W, H = 780, 270
    rows = [("VGG, SS + Fast R-CNN", 146, 1510, 174), ("VGG, RPN + Fast R-CNN", 141, 10, 47), ("ZF, RPN + Fast R-CNN", 31, 3, 25)]
    b = [T(20, 24, "표 4: 이미지 한 장의 시간 몫 (SS 는 CPU, 나머지는 K40 GPU)", 14, weight="bold")]
    for i, (n, c, p, r) in enumerate(rows):
        y = 50 + i * 62
        tot = c + p + r
        b.append(T(20, y + 14, f"{n}: {tot} ms ({1000 / tot:.1f} fps)", 12, weight="bold"))
        x = 20
        for v, col in ((c, A), (p, B), (r, C)):
            w = 730 * v / tot
            b.append(R(x, y + 22, w, 22, col))
            if w > 50:
                b.append(T(x + w / 2, y + 38, f"{v} ({100 * v / tot:.1f}%)", 11, "#ffffff", "middle"))
            x += w
    b += [R(20, 238, 14, 14, A), T(40, 250, "합성곱", 12), R(110, 238, 14, 14, B), T(130, 250, "제안", 12), R(190, 238, 14, 14, C), T(210, 250, "영역별(NMS · 풀링 · fc · softmax)", 12)]
    save("fig05_tab4_timing.svg", W, H, b)


def fig06():
    W, H = 720, 300
    x0, pw = 230, 420
    def X(v):
        return x0 + pw * (v - 64) / 10
    rows = [("SS (표 값, 원 논문 [5])", 66.9, None, D), ("SS (같은 저장소, 6 회)", 68.0, .3, INK), ("RPN+VGG, 공유 안 함", 68.5, None, A), ("RPN+VGG, 공유", 69.9, None, B)]
    b = [T(20, 24, "표 2 의 VOC 2007 학습 줄과 각주: 기준선을 어느 값으로 잡느냐에 따라 차이가 바뀐다", 14, weight="bold")]
    for v in (64, 66, 68, 70, 72, 74):
        b += [L(X(v), 44, X(v), 220), T(X(v), 238, v, 11, MUTE, "middle")]
    for i, (n, v, e, col) in enumerate(rows):
        y = 64 + i * 40
        b += [T(220, y + 4, n, 12, INK, "end"), f'<circle cx="{X(v):.1f}" cy="{y:.1f}" r="5" fill="{col}"/>', T(X(v) + (10 if e is None else 34), y + 4, v if e is None else f"{v} ± {e}", 12, col)]
        if e:
            b.append(L(X(v - e), y, X(v + e), y, col, 2))
    b += [T(20, 268, "공유 69.9 의 차이: 66.9 대비 3.0, 68.0 대비 1.9.   공유 안 함 68.5 의 차이: 66.9 대비 1.6, 68.0 대비 0.5.", 12, MUTE),
          T(20, 288, "± 0.3 이 표 전체에 하나뿐인 흩어짐이다. 뜻(표준편차 여부)은 적혀 있지 않다.", 12, MUTE)]
    save("fig06_tab2_baseline.svg", W, H, b)


def fig07():
    W, H = 900, 330
    b = [T(20, 24, "그림 2 (벡터 좌표에서 꺼내 다시 그림): 제안 수별 IoU 대 재현율. 세로선은 RPN VGG 가 SS 아래로 내려가는 자리", 13, weight="bold")]
    cross = {300: .79, 1000: .77, 2000: .765}
    for j, n in enumerate((300, 1000, 2000)):
        ox, oy, pw, ph = 50 + j * 285, 60, 245, 210
        b.append(T(ox + pw / 2, oy - 8, f"제안 {n}", 12, weight="bold", anchor="middle"))
        for v in (0, .2, .4, .6, .8, 1):
            y = oy + ph - ph * v
            b += [L(ox, y, ox + pw, y), T(ox - 6, y + 4, v, 10, MUTE, "end")]
        for x in (.5, .6, .7, .8, .9, 1.0):
            b.append(T(ox + pw * (x - .5) / .5, oy + ph + 14, x, 10, MUTE, "middle"))
        xc = ox + pw * (cross[n] - .5) / .5
        b += [L(xc, oy, xc, oy + ph, D, 1, "4 3"), T(xc + 3, oy + 12, cross[n], 10, MUTE)]
        for m, ys in REC[n].items():
            pts = " ".join(f"{ox + pw * (x - .5) / .5:.1f},{oy + ph - ph * y:.1f}" for x, y in zip(XS, ys))
            dash = ' stroke-dasharray="2 2"' if m == "SS" else (' stroke-dasharray="6 3"' if m == "EB" else "")
            b.append(f'<polyline points="{pts}" fill="none" stroke="{COL[m]}" stroke-width="{2 if m == "RPN VGG" else 1.4}"{dash}/>')
    for i, m in enumerate(REC[300]):
        b += [L(60 + i * 130, 314, 90 + i * 130, 314, COL[m], 2), T(96 + i * 130, 318, m, 12)]
    save("fig07_fig2_recall.svg", W, H, b)


def fig08():
    W, H = 660, 230
    rows = [("두 단계: RPN + ZF, 300, 1 축척", 58.7, B), ("한 단계 흉내: 조밀 20k, 1 축척", 53.8, D), ("한 단계 흉내: 조밀 20k, 5 축척", 53.9, D)]
    b = [T(20, 24, "표 5: 한 단계와 두 단계 (ZF, VOC 2007 시험)", 14, weight="bold")]
    for i, (n, v, c) in enumerate(rows):
        y = 50 + i * 42
        b += [T(20, y + 14, n, 12), R(280, y - 2, 300 * v / 60, 26, c), T(286 + 300 * v / 60, y + 16, v, 12, MUTE)]
    b.append(T(20, H - 30, "차이 4.8 점. OverFeat 자체가 아니라 Fast R-CNN 을 고쳐 흉내 낸 값이다.", 12, MUTE))
    b.append(T(20, H - 12, "VGG 값 · 시간 값 · 흩어짐이 이 표에 없다. 「더 느리다」 는 문장뿐이다.", 12, MUTE))
    save("fig08_tab5_one_two_stage.svg", W, H, b)


def fig09():
    W, H = 880, 190
    nodes = [("R-CNN (2014)", ["제안마다", "망을 따로"]), ("SPPnet · Fast R-CNN", ["합성곱 공유", "제안은 CPU"]), ("Faster R-CNN (이 편)", ["제안도 망이", "RPN + 앵커"]), ("Mask R-CNN (2017)", ["마스크 가지", "RoIAlign"]), ("YOLO (2016)", ["제안 단계를", "없앤 쪽"])]
    b = [T(20, 24, "이 편의 자리", 14, weight="bold")]
    for i, (a, c) in enumerate(nodes):
        x = 14 + i * 174
        b += [R(x, 50, 158, 100, "#fbe9e5" if i == 2 else "#eef2f7", LINE), T(x + 79, 80, a, 11, INK, "middle", "bold")]
        for k, l in enumerate(c):
            b.append(T(x + 79, 106 + k * 18, l, 11, MUTE, "middle"))
        if i < 4:
            b.append(L(x + 158, 100, x + 174, 100, INK, 1.5))
    save("fig09_lineage.svg", W, H, b)


if __name__ == "__main__":
    for fn in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09):
        fn()
    for wh in ((1000, 600), (800, 600)):
        print(wh, anchors(*wh)[:4])
    print("rpn VGG", 3 * 3 * 512 * 512 + 512 + 512 * 54 + 54, "ZF", 3 * 3 * 256 * 256 + 256 + 256 * 54 + 54)
    print("lambda balance", (10 / 2400) / (1 / 256))
    for n in REC:
        print(n, {m: (ys[0], ys[4], ys[6], ys[8]) for m, ys in REC[n].items()})
