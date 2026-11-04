# -*- coding: utf-8 -*-
"""BERT 노트(Devlin 외, NAACL 2019 발표집 판)의 그림 열일곱을 만든다.

색과 글꼴은 저장소의 앞선 노트 그림과 맞췄다. 바깥 데이터를 읽지 않으므로 어디서나 돈다(표준 라이브러리만 쓴다).

  python make_figures.py

원문 표 1 ~ 표 8 의 수는 아래 상수 T1 ~ T8 에, 원문 그림 5 는 PDF 안의 선 좌표에서 꺼낸 값을 F5 에 옮겨 적었다.
계산으로 원문을 확인하는 그림이 여럿이다 - 3(가림 개수), 4 · 5(파라미터 수), 6 · 7(표 1 의 차), 8(표 2 의 차),
10 · 11(표 5 의 몫), 12(표 6 의 한 걸음씩), 14(표 8 대 표 5 · 7), 16(에폭 셈). 계산한 값은 돌릴 때 화면에도 찍는다.
원문 그림 1 ~ 5 는 crop_paper_figures.py 가 잘라 png 로 둔다.
"""
import io, os, math

OUT = os.path.dirname(os.path.abspath(__file__))

BG        = "#ECEFEC"
NODE      = "#F6F7F5"
INK       = "#1C232C"
INK2      = "#4E5964"
MUTED     = "#7A8590"
LINE      = "#CFD6D3"
FWD       = "#2E6B8A"   # 파랑 — 인코더 · 이 논문 쪽
FWD_SOFT  = "#D8E7EE"
REV       = "#B4552B"   # 주황 — 디코더 · 비교 상대 쪽
REV_SOFT  = "#F2DED2"
CODE      = "#9A7B00"   # 노랑 — 주의 · 원문 표에 적힌 값
CODE_SOFT = "#FFF3C4"
OK        = "#1E8449"
OK_SOFT   = "#D6EEDD"
NO        = "#C0392B"
NO_SOFT   = "#F6D9D5"
PURP      = "#8E44AD"
PURP_SOFT = "#EADCF0"
FONT = "IBM Plex Sans KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"


# ── 공통 도구 ──────────────────────────────────────────────────────────────
def svg(name, w, h, body, label):
    s = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="%s" role="img" aria-label="%s">' % (w, h, w, h, FONT, label))
    s += '<rect x="0" y="0" width="100%%" height="100%%" fill="%s"/>' % BG
    s += body + "</svg>\n"
    io.open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8").write(s)
    print("  " + name + ".svg  %dx%d" % (w, h))


def arrow(idd, color):
    return ('<marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>' % (idd, color))


def defs():
    return ("<defs>" + arrow("af", FWD) + arrow("ar", REV) + arrow("ai", INK2) + arrow("ao", OK)
            + arrow("an", NO) + arrow("ac", CODE) + "</defs>")


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, t, size=12, fill=None, anchor="middle", weight=None, style=None):
    a = 'x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s"' % (x, y, size, fill or INK, anchor)
    if weight:
        a += ' font-weight="%s"' % weight
    if style:
        a += ' font-style="%s"' % style
    return "<text %s>%s</text>" % (a, esc(t))


def box(x, y, w, h, fill=None, stroke=None, sw=1.2, rx=6, dash=None):
    a = ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-width="%s"'
         % (x, y, w, h, rx, fill or NODE, stroke or INK, sw))
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    return a + "/>"


def line(x1, y1, x2, y2, color=None, sw=1.2, dash=None, marker=None, op=None):
    a = '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"' % (
        x1, y1, x2, y2, color or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if marker:
        a += ' marker-end="url(#%s)"' % marker
    if op:
        a += ' opacity="%s"' % op
    return a + "/>"


def circ(cx, cy, r, fill=None, stroke=None, sw=1.2):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (
        cx, cy, r, fill or NODE, stroke or INK, sw)


def path(d, stroke=None, fill="none", sw=1.6, dash=None, marker=None):
    a = '<path d="%s" fill="%s" stroke="%s" stroke-width="%s"' % (d, fill, stroke or INK2, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    if marker:
        a += ' marker-end="url(#%s)"' % marker
    return a + "/>"


def polyline(pts, stroke, sw=2, dash=None):
    d = "M" + " L".join("%.1f,%.1f" % p for p in pts)
    return path(d, stroke, sw=sw, dash=dash)


def diamond(cx, cy, r, fill, stroke):
    return '<path d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f z" fill="%s" stroke="%s" stroke-width="1.2"/>' % (
        cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy, fill, stroke)


def axes(x0, y0, x1, y1, xt, yt, fx, fy, xl=None, yl=None, xfmt="%g", yfmt="%g"):
    s = line(x0, y1, x1, y1, INK2, 1.2) + line(x0, y0, x0, y1, INK2, 1.2)
    for t in xt:
        lab = xfmt(t) if callable(xfmt) else xfmt % t
        s += line(fx(t), y1, fx(t), y1 + 4, INK2, 1) + txt(fx(t), y1 + 17, lab, 10, fill=MUTED)
    for t in yt:
        lab = yfmt(t) if callable(yfmt) else yfmt % t
        s += line(x0 - 4, fy(t), x0, fy(t), INK2, 1) + txt(x0 - 7, fy(t) + 4, lab, 10, fill=MUTED, anchor="end")
        s += line(x0, fy(t), x1, fy(t), LINE, 0.8, dash="2 3")
    if xl:
        s += txt((x0 + x1) / 2, y1 + 34, xl, 11, fill=INK2)
    if yl:
        s += txt(x0, y0 - 10, yl, 11, fill=INK2, anchor="start")
    return s


def lines_at(x, y, rows, size=12, gap=21, anchor="start"):
    s = ""
    for j, r in enumerate(rows):
        if isinstance(r, tuple):
            t, c = r[0], r[1]
            w = r[2] if len(r) > 2 else None
        else:
            t, c, w = r, INK2, None
        s += txt(x, y + gap * j, t, size, fill=c, anchor=anchor, weight=w)
    return s


def pow10(v):
    e = int(math.floor(math.log10(v)))
    m = v / 10 ** e
    sup = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    if abs(m - 1) < 1e-9:
        return "10" + str(e).translate(sup)
    return ("%.1f·10" % m) + str(e).translate(sup)


print("그림을 만든다 ->", OUT)

# ── 원문의 수 ───────────────────────────────────────────────────────────────
# 표 1 (원문 4176 쪽, GLUE 시험셋). 칸 순서 = NAMES
T1_NAMES = ["MNLI-m", "MNLI-mm", "QQP", "QNLI", "SST-2", "CoLA", "STS-B", "MRPC", "RTE"]
T1_SIZE = [392, 392, 363, 108, 67, 8.5, 5.7, 3.5, 2.5]   # 학습 예시 수, 천 개
T1 = {"Pre-OpenAI SOTA": [80.6, 80.1, 66.1, 82.3, 93.2, 35.0, 81.0, 86.0, 61.7],
      "BiLSTM+ELMo+Attn": [76.4, 76.1, 64.8, 79.8, 90.4, 36.0, 73.3, 84.9, 56.8],
      "OpenAI GPT": [82.1, 81.4, 70.3, 87.4, 91.3, 45.4, 80.0, 82.3, 56.0],
      "BERT Base": [84.6, 83.4, 71.2, 90.5, 93.5, 52.1, 85.8, 88.9, 66.4],
      "BERT Large": [86.7, 85.9, 72.1, 92.7, 94.9, 60.5, 86.5, 89.3, 70.1]}
T1_AVG = {"Pre-OpenAI SOTA": 74.0, "BiLSTM+ELMo+Attn": 71.0, "OpenAI GPT": 75.1, "BERT Base": 79.6, "BERT Large": 82.1}
OTHERS = ["Pre-OpenAI SOTA", "BiLSTM+ELMo+Attn", "OpenAI GPT"]

# 표 2 (원문 4177 쪽, SQuAD 1.1). (이름, Dev F1, Test F1)
T2 = [("Human", None, 91.2), ("#1 앙상블 nlnet", None, 91.7), ("#2 앙상블 QANet", None, 90.5),
      ("BiDAF+ELMo 단일", 85.6, 85.8), ("R.M. Reader 앙상블", 87.9, 88.5),
      ("BERT Base 단일", 88.5, None), ("BERT Large 단일", 90.9, None), ("BERT Large 앙상블", 91.8, None),
      ("BERT Large 단일+TriviaQA", 91.1, 91.8), ("BERT Large 앙상블+TriviaQA", 92.2, 93.2)]

# 표 5 (원문 4178 쪽, 개발셋). 칸: MNLI-m QNLI MRPC SST-2 SQuAD
T5_NAMES = ["MNLI-m", "QNLI", "MRPC", "SST-2", "SQuAD"]
T5 = {"BERT Base": [84.4, 88.4, 86.7, 92.7, 88.5], "No NSP": [83.9, 84.9, 86.5, 92.6, 87.9],
      "LTR & No NSP": [82.1, 84.3, 77.5, 92.1, 77.8], "+ BiLSTM": [82.1, 84.1, 75.7, 91.6, 84.9]}

# 표 6 (원문 4179 쪽, 개발셋 5 재시작 평균). (L, H, A, ppl, MNLI-m, MRPC, SST-2)
T6 = [(3, 768, 12, 5.84, 77.9, 79.8, 88.4), (6, 768, 3, 5.24, 80.6, 82.2, 90.7), (6, 768, 12, 4.68, 81.9, 84.8, 91.3),
      (12, 768, 12, 3.99, 84.4, 86.7, 92.9), (12, 1024, 16, 3.54, 85.7, 86.9, 93.3), (24, 1024, 16, 3.23, 86.6, 87.8, 93.7)]

# 표 7 (원문 4179 쪽, CoNLL-2003). (이름, Dev F1, Test F1, 묶음)
T7 = [("ELMo", 95.7, 92.2, "o"), ("CVT", None, 92.6, "o"), ("CSE", None, 93.1, "o"),
      ("미세조정 Large", 96.6, 92.8, "f"), ("미세조정 Base", 96.4, 92.4, "f"),
      ("특징 Base: 임베딩", 91.0, None, "b"), ("특징 Base: 끝에서 둘째 층", 95.6, None, "b"), ("특징 Base: 마지막 층", 94.9, None, "b"),
      ("특징 Base: 끝 넷 가중합", 95.9, None, "b"), ("특징 Base: 끝 넷 잇기", 96.1, None, "b"), ("특징 Base: 12 층 가중합", 95.5, None, "b")]

# 표 8 (원문 4186 쪽, 개발셋). (MASK, SAME, RND, MNLI, NER 미세조정, NER 특징)
T8 = [(80, 10, 10, 84.2, 95.4, 94.9), (100, 0, 0, 84.3, 94.9, 94.0), (80, 0, 20, 84.1, 95.2, 94.6),
      (80, 20, 0, 84.4, 95.2, 94.7), (0, 20, 80, 83.7, 94.8, 94.6), (0, 0, 100, 83.6, 94.9, 94.6)]

# 그림 5 (원문 4186 쪽). PDF 안의 선 좌표에서 꺼낸 값. 눈금: x 200 = 131.104pt · 1,000 = 261.122pt, y 84 = 583.419pt · 76 = 669.783pt
F5_K = [30, 50, 100, 200, 400, 600, 800, 1000]
F5_MLM = [78.6, 79.6, 80.5, 82.2, 83.2, 84.0, 84.3, 84.4]
F5_LTR = [79.4, 79.8, 80.3, 81.0, 81.7, 81.9, 82.1, 82.2]


# ── 파라미터 세기 (내가 센 것) ──────────────────────────────────────────────
def layer_params(h):
    """한 층: Q · K · V 투영 + 출력 투영(치우침 포함) + 층 정규화 + FFN(4H, 치우침 포함) + 층 정규화."""
    f = 4 * h
    return 3 * (h * h + h) + (h * h + h) + 2 * h + (h * f + f) + (f * h + h) + 2 * h


def bert_parts(l, h, v, pos=512, seg=2):
    return {"tok": v * h, "pos": pos * h, "seg": seg * h, "ln": 2 * h, "layers": l * layer_params(h), "pool": h * h + h}


def pretrain_heads(h, v):
    """가림 과제 머리(H x H 변환 + 층 정규화 + 어휘 치우침, 낱말 표 공유) + 다음 문장 머리(2 x H + 2)."""
    return (h * h + h) + 2 * h + v + 2 * h + 2


BASE30K = bert_parts(12, 768, 30000)
LARGE30K = bert_parts(24, 1024, 30000)
BASE_T = sum(BASE30K.values())
LARGE_T = sum(LARGE30K.values())
print("  [파라미터] 층 하나 H=768 %d · H=1024 %d" % (layer_params(768), layer_params(1024)))
for nm, l, h in [("Base", 12, 768), ("Large", 24, 1024)]:
    for v in (30000, 30522):
        p = bert_parts(l, h, v)
        print("  [파라미터] %s V=%d 합 %d (풀러 뺌 %d, 사전학습 머리 더함 %d)" % (
            nm, v, sum(p.values()), sum(p.values()) - p["pool"], sum(p.values()) + pretrain_heads(h, v)))
print("  [파라미터] Vaswani 큰 인코더 L=6 H=1024: 층만 %d, 어휘 30,000 낱말 표 더함 %d" % (6 * layer_params(1024), 6 * layer_params(1024) + 30000 * 1024))
print("  [파라미터] L=64 H=512 (FFN 4H 가정) 층만 %d" % (64 * layer_params(512)))


def spearman(a, b):
    def rk(x):
        s = sorted(x)
        return [s.index(v) + 1 + (x.count(v) - 1) / 2.0 for v in x]
    ra, rb = rk(a), rk(b)
    n = len(a)
    return 1 - 6 * sum((p - q) ** 2 for p, q in zip(ra, rb)) / float(n * (n * n - 1))


W_DEF = 900


# ── 그림 1: 층마다 볼 수 있는 입력 ─────────────────────────────────────────
def fig01():
    W, H = W_DEF, 340
    s = defs()
    s += txt(W / 2, 28, "자리 3 의 표현이 층마다 어떤 입력을 볼 수 있나 (입력 7 토큰, 원문 그림 3 을 칸으로 옮겼다)", 14, weight="bold")
    n = 7
    cell = 26

    def grid(x0, y0, title, rows, color, soft):
        o = txt(x0 + n * cell / 2.0, y0 - 26, title, 13, fill=color, weight="bold")
        for j, (lab, seen) in enumerate(rows):
            y = y0 + j * (cell + 8)
            o += txt(x0 - 8, y + 17, lab, 10.5, fill=INK2, anchor="end")
            for i in range(n):
                f = soft if i in seen else NODE
                st = color if i == 3 else LINE
                o += box(x0 + i * cell, y, cell - 2, cell - 2, f, st, 1.6 if i == 3 else 1, rx=3)
                o += txt(x0 + i * cell + 12, y + 16, str(i), 10, fill=INK if i in seen else MUTED)
        return o

    left = set(range(0, 4))
    right = set(range(3, 7))
    all_ = set(range(7))
    s += grid(90, 90, "왼쪽만 (OpenAI GPT · LTR 줄)", [("2 층", left), ("1 층", left)], REV, REV_SOFT)
    s += grid(370, 90, "둘을 따로 배워 잇기 (ELMo)", [("왼쪽 스택 2 층", left), ("왼쪽 스택 1 층", left), ("오른쪽 스택 2 층", right), ("오른쪽 스택 1 층", right)], CODE, CODE_SOFT)
    s += grid(670, 90, "모든 층에서 양쪽 (BERT)", [("2 층", all_), ("1 층", all_)], FWD, FWD_SOFT)
    s += lines_at(30, 262, [
        ("색칠한 칸 = 자리 3 이 그 층에서 받을 수 있는 입력 자리. 굵은 테두리가 자리 3.", INK2),
        ("ELMo 는 두 스택이 층 안에서 서로의 표현을 보지 않고 맨 위에서 잇는다(원문 그림 3 캡션). 원문의 「모든 층에서 양쪽」 은 이 차이를 말한다.", INK2),
        ("이 편의 표 5 에는 ELMo 꼴(둘을 따로 배워 잇기)을 같은 조건에서 돌린 줄이 없다. 5.1 절이 말로만 견준다.", NO),
    ], size=11.5, gap=23)
    svg("fig01_context_per_layer", W, H, s, "층마다 볼 수 있는 입력")


# ── 그림 2: 자기 자신을 본다 ──────────────────────────────────────────────
def fig02():
    W, H = W_DEF, 330
    s = defs()
    s += txt(W / 2, 28, "왜 양쪽을 보는 언어 모델은 그대로 배울 수 없나 (3.1절 「see itself」 를 두 층으로 풀었다)", 14, weight="bold")

    def panel(x0, title, word, color, soft, note, hop):
        o = txt(x0 + 170, 66, title, 13, fill=color, weight="bold")
        xs = [x0 + 40 + 90 * i for i in range(4)]
        ys = {"in": 232, "l1": 164, "l2": 96}
        labs = ["my", "dog", "is", word]
        for i, x in enumerate(xs):
            o += box(x - 34, ys["in"], 68, 28, soft if i == 3 else NODE, color if i == 3 else LINE, 1.3, rx=5)
            o += txt(x, ys["in"] + 19, labs[i], 11.5, fill=INK)
            o += circ(x, ys["l1"] + 13, 13, NODE, LINE)
            o += circ(x, ys["l2"] + 13, 13, soft if i == 3 else NODE, color if i == 3 else LINE)
            o += txt(x, ys["l1"] + 17, "1", 10, fill=MUTED)
            o += txt(x, ys["l2"] + 17, "2", 10, fill=MUTED)
        if hop:
            o += line(xs[3], ys["in"], xs[1] + 8, ys["l1"] + 26, color, 2, marker="ar" if color == REV else "af")
            o += line(xs[1] + 6, ys["l1"], xs[3] - 8, ys["l2"] + 26, color, 2, marker="ar" if color == REV else "af")
        o += txt(x0 + 170, 290, note, 11.5, fill=INK2)
        return o

    s += panel(40, "가리지 않으면: 정답 낱말이 두 걸음에 자기 자리로 돌아온다", "hairy", REV, REV_SOFT, "목표 hairy = 입력 hairy. 입력 자리 → 1 층 dog → 2 층 자기 자리", True)
    s += panel(480, "가리면: 그 자리의 입력에 정답이 없다", "[MASK]", FWD, FWD_SOFT, "목표 hairy, 입력 [MASK]. 나머지 자리에서 맞혀야 한다", False)
    svg("fig02_see_itself", W, H, s, "양쪽을 보는 모델이 자기 자신을 보는 경로")


# ── 그림 3: 가림 개수 ──────────────────────────────────────────────────────
def fig03():
    W, H = W_DEF, 300
    s = defs()
    s += txt(W / 2, 28, "15% 와 80 / 10 / 10 은 열 하나에서 토큰 몇 개인가 (내가 센 것)", 14, weight="bold")
    x0, x1 = 150, 850

    def row(y, n):
        p = 0.15 * n
        parts = [("[MASK]", 0.8 * p, REV), ("무작위", 0.1 * p, CODE), ("그대로(예측 대상)", 0.1 * p, PURP), ("예측 안 함", n - p, MUTED)]
        o = txt(x0 - 10, y + 24, "길이 %d" % n, 13, anchor="end", weight="bold")
        x = float(x0)
        for lab, v, c in parts:
            w = (x1 - x0) * v / n
            o += '<rect x="%.1f" y="%d" width="%.1f" height="36" fill="%s" opacity="0.85"/>' % (x, y, w, c)
            x += w
        o += txt(x0, y + 56, "[MASK] %.2f · 무작위 %.2f · 그대로 %.2f = 예측 %.1f 개 · 예측 안 함 %.1f 개" % (0.8 * p, 0.1 * p, 0.1 * p, p, n - p), 12, fill=INK2, anchor="start")
        return o

    s += row(62, 512)
    s += row(152, 128)
    for i, (lab, c) in enumerate([("[MASK] 12.0%", REV), ("무작위 1.5%", CODE), ("그대로 1.5%", PURP), ("예측 안 함 85.0%", MUTED)]):
        s += box(150 + i * 175, 244, 14, 14, c, c, 1, rx=2) + txt(170 + i * 175, 256, lab, 11.5, fill=INK2, anchor="start")
    s += txt(W / 2, 286, "[CLS] · [SEP] 도 토큰 수에 넣었다(원문 「all WordPiece tokens」). 길이 128 이 전체 걸음의 90% 다(A.2 절).", 11, fill=INK2)
    svg("fig03_mask_counts", W, H, s, "열 하나의 가림 개수")


# ── 그림 4: 파라미터 몫 ────────────────────────────────────────────────────
def fig04():
    W, H = W_DEF, 340
    s = defs()
    s += txt(W / 2, 28, "파라미터 몫 (내가 센 것, 어휘 30,000 · 자리 512 · 문장 표지 2)", 14, weight="bold")
    x0, x1 = 150, 850
    colors = [("tok", "낱말 표", CODE), ("pos", "자리", OK), ("seg", "문장 표지", PURP), ("ln", "표 뒤 정규화", NO), ("layers", "Transformer 층", FWD), ("pool", "[CLS] 변환", REV)]
    mx = float(LARGE_T)

    def row(y, name, d):
        t = sum(d.values())
        o = txt(x0 - 10, y + 24, name, 13, anchor="end", weight="bold")
        x = float(x0)
        for k, _, c in colors:
            w = (x1 - x0) * d[k] / mx
            o += '<rect x="%.1f" y="%d" width="%.2f" height="36" fill="%s" opacity="0.9"/>' % (x, y, w, c)
            x += w
        o += txt(x0, y + 56, "합 {:,}  =  낱말 표 {:.1f}% · 자리 {:.2f}% · 문장 표지 {:.4f}% · 층 {:.1f}% · [CLS] 변환 {:.2f}%".format(
            t, 100.0 * d["tok"] / t, 100.0 * d["pos"] / t, 100.0 * d["seg"] / t, 100.0 * d["layers"] / t, 100.0 * d["pool"] / t), 12, fill=INK2, anchor="start")
        return o

    s += row(62, "Base", BASE30K)
    s += row(152, "Large", LARGE30K)
    for i, (k, lab, c) in enumerate(colors):
        s += box(90 + i * 130, 246, 14, 14, c, c, 1, rx=2) + txt(110 + i * 130, 258, lab, 11.5, fill=INK2, anchor="start")
    s += txt(W / 2, 294, "층 하나 = 12H² + 13H. H = 768 이면 7,087,872, H = 1024 면 12,596,224. 머리 수 A 는 셈에 들어가지 않는다(머리 폭 H/A x A = H).", 11.5, fill=INK2)
    s += txt(W / 2, 316, "층 정규화 자리와 [CLS] 변환(H x H + H)은 이 파일에 적혀 있지 않아 공개 구현의 꼴을 가정했다.", 11.5, fill=NO)
    svg("fig04_param_breakdown", W, H, s, "파라미터 몫")


# ── 그림 5: 파라미터 대 원문 값 ────────────────────────────────────────────
def fig05():
    W, H = W_DEF, 340
    s = defs()
    s += txt(W / 2, 28, "원문의 110M · 340M 과 내 셈 (원문 3절 · 5.2절)", 14, weight="bold")
    rows = []
    for nm, l, h, st in [("Base", 12, 768, 110), ("Large", 24, 1024, 340)]:
        a = bert_parts(l, h, 30000)
        b = bert_parts(l, h, 30522)
        rows.append((nm, st, sum(a.values()) - a["pool"], sum(a.values()), sum(b.values()), sum(b.values()) + pretrain_heads(h, 30522)))
    heads = ["", "원문", "V=30,000 [CLS] 변환 뺌", "V=30,000", "V=30,522", "V=30,522 + 사전학습 머리"]
    xs = [70, 170, 330, 500, 640, 800]
    for x, t in zip(xs, heads):
        s += txt(x, 72, t, 11.5, fill=INK2, weight="bold")
    s += line(30, 84, 870, 84, LINE)
    for j, r in enumerate(rows):
        y = 118 + j * 58
        s += txt(xs[0], y, r[0], 14, weight="bold")
        s += txt(xs[1], y, "%dM" % r[1], 14, fill=CODE, weight="bold")
        for k in range(2, 6):
            s += txt(xs[k], y, "{:,}".format(r[k]), 12.5)
            s += txt(xs[k], y + 20, "원문 대비 %+.1f%%" % (100.0 * (r[k] / (r[1] * 1e6) - 1)), 10.5, fill=MUTED)
    s += line(30, 214, 870, 214, LINE)
    s += lines_at(40, 240, [
        ("어휘 30,000 은 원문 3절의 값이다. 30,522 는 원문에 없고, Hugging Face 의 bert-base-uncased · bert-large-uncased config.json 값이다(2026-11-05 확인).", INK2),
        ("Base 는 어느 셈이든 110M 에서 -1.4 ~ +0.1% 다. Large 는 어느 셈이든 340M 보다 1.1 ~ 1.9% 작다. 원문은 셈한 방식을 적지 않는다.", INK2),
        ("낱말 표를 소프트맥스와 공유한다고 가정했다(원문에 적혀 있지 않다). 공유하지 않으면 Base 에 23,040,000 이 더해져 110M 과 맞지 않는다.", INK2),
    ], size=11.5, gap=26)
    svg("fig05_param_check", W, H, s, "원문 파라미터 값과 내 셈")


# ── 그림 6: 표 1 의 차 ─────────────────────────────────────────────────────
def fig06():
    W, H = W_DEF, 420
    s = defs()
    s += txt(W / 2, 28, "표 1: 과제마다 다른 세 줄의 최고값을 넘은 폭 (학습 예시가 많은 순)", 14, weight="bold")
    x0, x1, y0, y1 = 70, 870, 60, 330
    fy = lambda v: y1 - (y1 - y0) * v / 16.0
    n = len(T1_NAMES)
    bw = (x1 - x0) / float(n)
    for t in (0, 4, 8, 12, 16):
        s += line(x0, fy(t), x1, fy(t), LINE, 0.8, dash="2 3") + txt(x0 - 6, fy(t) + 4, str(t), 10, fill=MUTED, anchor="end")
    s += txt(x0, 50, "백분율 점 (STS-B 는 스피어만 x 100, QQP · MRPC 는 F1)", 11, fill=INK2, anchor="start")
    for i, nm in enumerate(T1_NAMES):
        best = max(T1[o][i] for o in OTHERS)
        a = T1["BERT Base"][i] - best
        b = T1["BERT Large"][i] - best
        x = x0 + i * bw + bw * 0.14
        w = bw * 0.34
        s += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x, fy(a), w, y1 - fy(a), FWD)
        s += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x + w + 2, fy(b), w, y1 - fy(b), REV)
        s += txt(x + w / 2, fy(a) - 5, "%.1f" % a, 10.5, fill=FWD)
        s += txt(x + w * 1.5 + 2, fy(b) - 5, "%.1f" % b, 10.5, fill=REV)
        s += txt(x0 + i * bw + bw / 2, y1 + 18, nm, 11)
        s += txt(x0 + i * bw + bw / 2, y1 + 34, "%gk" % T1_SIZE[i], 10, fill=MUTED)
    s += box(620, 60, 14, 14, FWD, FWD, 1, rx=2) + txt(640, 72, "BERT Base - 세 줄 최고", 11.5, fill=INK2, anchor="start")
    s += box(620, 82, 14, 14, REV, REV, 1, rx=2) + txt(640, 94, "BERT Large - 세 줄 최고", 11.5, fill=INK2, anchor="start")
    s += txt(W / 2, 390, "「모든 과제에서 큰 폭(by a substantial margin)」 의 가장 작은 칸은 Base SST-2 +0.3 · QQP +0.9, Large SST-2 +1.7 · QQP +1.8 이다.", 11, fill=INK2)
    s += txt(W / 2, 408, "흩어짐이 적혀 있지 않아 0.3 이 시작값 흔들림 밖인지 판정하지 못한다.", 11, fill=INK2)
    svg("fig06_table1_margin", W, H, s, "표 1 의 과제별 차")


# ── 그림 7: Large - Base 대 데이터 크기 ───────────────────────────────────
def fig07():
    W, H = W_DEF, 420
    s = defs()
    idx = [0, 2, 3, 4, 5, 6, 7, 8]
    size = [T1_SIZE[i] for i in idx]
    gap = [T1["BERT Large"][i] - T1["BERT Base"][i] for i in idx]
    rho = spearman(size, gap)
    print("  [표 1] Large - Base 와 학습 예시 수의 스피어만 %.3f (점 여덟, MNLI-m)" % rho)
    s += txt(W / 2, 28, "「특히 학습 데이터가 아주 적은 과제에서」: Large - Base 와 학습 예시 수 (표 1 · 표 6)", 14, weight="bold")
    x0, x1, y0, y1 = 80, 860, 60, 340
    fx = lambda v: x0 + (x1 - x0) * (math.log10(v) - math.log10(2)) / (math.log10(500) - math.log10(2))
    fy = lambda v: y1 - (y1 - y0) * v / 10.0
    s += axes(x0, y0, x1, y1, [2.5, 5, 10, 50, 100, 400], [0, 2, 4, 6, 8, 10], fx, fy, xl="학습 예시 수 (천 개, 로그 눈금)", yl="Large - Base (백분율 점)")
    for i, k in enumerate(idx):
        x, y = fx(T1_SIZE[k]), fy(gap[i])
        s += circ(x, y, 6, REV_SOFT, REV, 1.6)
        s += txt(x + 9, y - 7, "%s %.1f" % (T1_NAMES[k], gap[i]), 11, fill=REV, anchor="start")
    d6 = [("MNLI-m", 392, T6[5][4] - T6[3][4]), ("MRPC", 3.6, T6[5][5] - T6[3][5]), ("SST-2", 67, T6[5][6] - T6[3][6])]
    for nm, sz, g in d6:
        s += diamond(fx(sz), fy(g), 7, FWD_SOFT, FWD)
        s += txt(fx(sz) + (8 if nm == "MRPC" else -10), fy(g) + (-10 if nm == "MRPC" else 15), "%s %.1f" % (nm, g), 11, fill=FWD, anchor="start" if nm == "MRPC" else "end")
    s += circ(640, 76, 6, REV_SOFT, REV, 1.6) + txt(652, 80, "표 1 시험셋 (Large 만 재시작 골라내기)", 11, fill=INK2, anchor="start")
    s += diamond(640, 98, 7, FWD_SOFT, FWD) + txt(652, 102, "표 6 개발셋 (5 재시작 평균)", 11, fill=INK2, anchor="start")
    s += txt(W / 2, 396, "표 1 여덟 점의 스피어만 순위 상관 %.2f (내가 센 것). 가장 작은 넷의 차가 0.4 · 0.7 · 3.7 · 8.4 로, 크기와 한 방향으로 움직이지 않는다." % rho, 11.5, fill=INK2)
    svg("fig07_large_minus_base", W, H, s, "Large 와 Base 의 차와 학습 예시 수")


# ── 그림 8: 표 2 ──────────────────────────────────────────────────────────
def fig08():
    W, H = W_DEF, 470
    s = defs()
    s += txt(W / 2, 28, "표 2: SQuAD 1.1 F1. 본문의 +1.5 · +1.3 은 어느 줄과의 차인가", 14, weight="bold")
    x0, x1 = 300, 790
    fx = lambda v: x0 + (x1 - x0) * (v - 85) / 9.0
    y0 = 66
    for t in range(85, 95):
        s += line(fx(t), y0 - 6, fx(t), y0 + 10 * 32 - 8, LINE, 0.8, dash="2 3") + txt(fx(t), y0 - 12, str(t), 10, fill=MUTED)
    for j, (nm, dev, test) in enumerate(T2):
        y = y0 + j * 32
        s += txt(x0 - 14, y + 13, nm, 12, anchor="end", fill=FWD if nm.startswith("BERT") else INK)
        if dev is not None:
            s += circ(fx(dev), y + 9, 6, NODE, MUTED, 1.6)
            s += txt(fx(dev) - 10, y + 13, "%.1f" % dev, 10, fill=MUTED, anchor="end")
        if test is not None:
            s += circ(fx(test), y + 9, 6, FWD if nm.startswith("BERT") else CODE, INK, 1)
            s += txt(fx(test) + 10, y + 13, "%.1f" % test, 10.5, fill=INK, anchor="start")
    s += circ(820, 80, 6, NODE, MUTED, 1.6) + txt(830, 84, "Dev", 11, fill=INK2, anchor="start")
    s += circ(820, 102, 6, CODE, INK, 1) + txt(830, 106, "Test", 11, fill=INK2, anchor="start")
    s += lines_at(40, 402, [
        ("앙상블+TriviaQA 93.2 - #1 nlnet 91.7 = +1.5 로 본문과 맞다. 단일+TriviaQA 91.8 - #1 nlnet 91.7 = +0.1 이다.", INK2),
        ("본문의 「top leaderboard system 을 단일로 +1.3」 은 91.8 - #2 QANet 90.5 = +1.3 에서만 나온다(내가 센 것). 이 표에 리더보드 단일 줄은 없다.", NO),
        ("TriviaQA 를 뺀 줄은 Dev 뿐이다. 「그래도 모든 시스템을 크게 앞선다」 의 비교 상대는 Test 값이다.", NO),
    ], size=11.5, gap=21)
    svg("fig08_table2_squad", W, H, s, "표 2 SQuAD 1.1")


# ── 그림 9: 표 5 ──────────────────────────────────────────────────────────
def fig09():
    W, H = W_DEF, 420
    s = defs()
    s += txt(W / 2, 28, "표 5: 사전학습 과제 절제 (Base 짜임, 개발셋, 줄마다 흩어짐 없음)", 14, weight="bold")
    x0, x1, y0, y1 = 70, 660, 60, 350
    rows = ["BERT Base", "No NSP", "LTR & No NSP", "+ BiLSTM"]
    fx = lambda i: x0 + 40 + (x1 - x0 - 80) * i / 3.0
    fy = lambda v: y1 - (y1 - y0) * (v - 74) / 20.0
    for t in (74, 78, 82, 86, 90, 94):
        s += line(x0, fy(t), x1, fy(t), LINE, 0.8, dash="2 3") + txt(x0 - 6, fy(t) + 4, str(t), 10, fill=MUTED, anchor="end")
    for i, r in enumerate(rows):
        s += txt(fx(i), y1 + 20, r, 11.5, fill=INK2)
    cols = [FWD, OK, REV, PURP, CODE]
    for k, nm in enumerate(T5_NAMES):
        pts = [(fx(i), fy(T5[r][k])) for i, r in enumerate(rows)]
        s += polyline(pts, cols[k], 2)
        for p in pts:
            s += circ(p[0], p[1], 4, cols[k], cols[k])
        s += txt(pts[-1][0] + 8, pts[-1][1] + 4, nm, 11, fill=cols[k], anchor="start", weight="bold")
    rx = 700
    s += txt(rx, 72, "줄 사이 차 (내가 센 것)", 12, fill=INK, anchor="start", weight="bold")
    yy = 96
    for k, nm in enumerate(T5_NAMES):
        v = [T5[r][k] for r in rows]
        s += txt(rx, yy, nm, 11, fill=cols[k], anchor="start", weight="bold")
        s += txt(rx, yy + 17, "NSP %.1f · LTR %.1f · BiLSTM %+.1f" % (v[0] - v[1], v[1] - v[2], v[3] - v[2]), 10, fill=INK2, anchor="start")
        yy += 44
    s += txt(W / 2, 400, "MRPC 칸은 정확도(표 1 의 MRPC 는 F1). LTR 줄은 미세조정에서도 왼쪽만 본다 - 원문 5.1절.", 11.5, fill=INK2)
    svg("fig09_table5", W, H, s, "표 5 사전학습 과제 절제")


# ── 그림 10: 몫 나누기 ─────────────────────────────────────────────────────
def fig10():
    W, H = W_DEF, 370
    s = defs()
    s += txt(W / 2, 28, "표 5 의 Base → LTR 차를 NSP 를 뺀 몫과 LTR 로 바꾼 몫으로 (내가 센 것)", 14, weight="bold")
    x0, x1 = 120, 660
    mx = 11.0
    for j, nm in enumerate(T5_NAMES):
        y = 60 + j * 46
        a = T5["BERT Base"][j] - T5["No NSP"][j]
        b = T5["No NSP"][j] - T5["LTR & No NSP"][j]
        wa = (x1 - x0) * a / mx
        wb = (x1 - x0) * b / mx
        s += txt(x0 - 10, y + 20, nm, 12, anchor="end", weight="bold")
        s += '<rect x="%.1f" y="%d" width="%.1f" height="30" fill="%s"/>' % (x0, y, wa, CODE)
        s += '<rect x="%.1f" y="%d" width="%.1f" height="30" fill="%s"/>' % (x0 + wa, y, wb, REV)
        s += txt(x0 + wa + wb + 8, y + 20, "합 %.1f = NSP %.1f (%.1f%%) + LTR %.1f" % (a + b, a, 100 * a / (a + b), b), 11.5, fill=INK2, anchor="start")
    s += box(120, 298, 14, 14, CODE, CODE, 1, rx=2) + txt(140, 310, "NSP 를 뺀 몫 (Base - No NSP)", 11.5, fill=INK2, anchor="start")
    s += box(370, 298, 14, 14, REV, REV, 1, rx=2) + txt(390, 310, "가림 → 왼쪽만 (No NSP - LTR), 미세조정의 왼쪽 제약 포함", 11.5, fill=INK2, anchor="start")
    s += txt(W / 2, 346, "순서는 표가 정한 한 가지뿐이다. NSP 만 쓰고 가림 과제를 뺀 줄이 없어, 가림 과제만의 몫은 이 표로 뽑을 수 없다.", 11.5, fill=NO)
    svg("fig10_table5_shares", W, H, s, "표 5 차의 몫")


# ── 그림 11: GPT 와의 차 ──────────────────────────────────────────────────
def fig11():
    W, H = W_DEF, 340
    s = defs()
    s += txt(W / 2, 28, "A.4 절 「개선의 대부분은 사전학습 과제와 양방향에서」: 표 1 의 차와 표 5 의 차를 맞대면", 14, weight="bold")
    names = [("MNLI-m", 0, 0), ("QNLI", 3, 1), ("SST-2", 4, 3)]
    x0, x1, y0, y1 = 100, 620, 60, 260
    fy = lambda v: y1 - (y1 - y0) * v / 5.0
    for t in range(0, 6):
        s += line(x0, fy(t), x1, fy(t), LINE, 0.8, dash="2 3") + txt(x0 - 6, fy(t) + 4, str(t), 10, fill=MUTED, anchor="end")
    bw = (x1 - x0) / 3.0
    for i, (nm, a, b) in enumerate(names):
        g1 = T1["BERT Base"][a] - T1["OpenAI GPT"][a]
        g2 = T5["BERT Base"][b] - T5["LTR & No NSP"][b]
        x = x0 + i * bw + 30
        s += '<rect x="%.1f" y="%.1f" width="48" height="%.1f" fill="%s"/>' % (x, fy(g1), y1 - fy(g1), CODE)
        s += '<rect x="%.1f" y="%.1f" width="48" height="%.1f" fill="%s"/>' % (x + 54, fy(g2), y1 - fy(g2), FWD)
        s += txt(x + 24, fy(g1) - 5, "%.1f" % g1, 11, fill=CODE)
        s += txt(x + 78, fy(g2) - 5, "%.1f" % g2, 11, fill=FWD)
        s += txt(x + 51, y1 + 20, nm, 12)
        print("  [A.4] %s GPT→Base 시험 %.1f · LTR→Base 개발 %.1f · 비 %.0f%%" % (nm, g1, g2, 100 * g2 / g1))
    s += box(650, 70, 14, 14, CODE, CODE, 1, rx=2) + txt(670, 82, "표 1 시험셋: Base - GPT", 11.5, fill=INK2, anchor="start")
    s += box(650, 94, 14, 14, FWD, FWD, 1, rx=2) + txt(670, 106, "표 5 개발셋: Base - LTR", 11.5, fill=INK2, anchor="start")
    s += lines_at(650, 140, [
        ("비: 92% · 132% · 27%", INK, "bold"),
        ("두 차는 다른 집합에서 쟀다.", NO),
        ("Base 자신의 QNLI 는", INK2),
        ("개발 88.4 · 시험 90.5 로 2.1 다르다.", INK2),
    ], size=11.5, gap=21)
    s += txt(W / 2, 314, "데이터 · 입력 표현 · 학습률 고르기를 하나씩 GPT 값으로 되돌린 줄이 없어 「대부분」 의 비율은 원문 어디에도 잰 값이 없다.", 11.5, fill=NO)
    svg("fig11_gpt_gap", W, H, s, "GPT 와의 차와 절제 차")


# ── 그림 12: 표 6 ─────────────────────────────────────────────────────────
def fig12():
    W, H = W_DEF, 470
    s = defs()
    s += txt(W / 2, 28, "표 6: 모델 크기 (개발셋, 5 재시작 평균, 흩어짐 없음)", 14, weight="bold")
    xs = [120 + i * 132 for i in range(6)]
    y0, y1 = 60, 260
    fy = lambda v: y1 - (y1 - y0) * (v - 76) / 20.0
    for t in (76, 80, 84, 88, 92, 96):
        s += line(70, fy(t), 830, fy(t), LINE, 0.8, dash="2 3") + txt(64, fy(t) + 4, str(t), 10, fill=MUTED, anchor="end")
    for k, nm, c in [(4, "MNLI-m", FWD), (5, "MRPC", REV), (6, "SST-2", OK)]:
        pts = [(xs[i], fy(T6[i][k])) for i in range(6)]
        s += polyline(pts, c, 2)
        for i, p in enumerate(pts):
            s += circ(p[0], p[1], 4, c, c)
            off = -9 if k == 6 else (15 if k == 4 else -9)
            if k == 5 and i < 4:
                off = -9
            s += txt(p[0], p[1] + off, "%.1f" % T6[i][k], 10, fill=c)
        s += txt(pts[-1][0] + 12, pts[-1][1] + 4, nm, 11, fill=c, anchor="start", weight="bold")
    params = []
    for i, r in enumerate(T6):
        t = sum(bert_parts(r[0], r[1], 30000).values())
        params.append(t)
        s += txt(xs[i], 284, "L%d H%d A%d" % r[:3], 11.5, weight="bold")
        s += txt(xs[i], 303, "%.1fM" % (t / 1e6), 11, fill=PURP)
        s += txt(xs[i], 321, "ppl %.2f" % r[3], 11, fill=INK2)
        print("  [표 6] L%d H%d A%d %d" % (r[0], r[1], r[2], t))
    s += txt(60, 303, "내 셈", 10.5, fill=PURP, anchor="end")
    s += lines_at(40, 352, [
        ("한 군데만 바꾼 쌍(내가 고른 것): 파라미터가 같은 A 3 → 12 (L6 H768) 에서 MNLI-m +1.3 · MRPC +2.6 · SST-2 +0.6.", INK2),
        ("L 3 → 6: +4.0 · +5.0 · +2.9.  L 6 → 12: +2.5 · +1.9 · +1.6.  L 12 → 24 (H1024): +0.9 · +0.9 · +0.4.  H 768 → 1024 (A 함께): +1.3 · +0.2 · +0.4.", INK2),
        ("Base → Large 에서 파라미터 3.07 배에 MRPC +1.1. MRPC 3 층 → 24 층은 +8.0 이고 그 가운데 6.9 가 Base 까지의 걸음에서 나온다.", INK2),
        ("본문 「네 데이터셋 모두」 인데 표의 개발 정확도 칸은 셋이다(넷째는 LM 혼잡도).", NO),
    ], size=11.5, gap=23)
    svg("fig12_table6", W, H, s, "표 6 모델 크기")


# ── 그림 13: 표 7 ─────────────────────────────────────────────────────────
def fig13():
    W, H = W_DEF, 490
    s = defs()
    s += txt(W / 2, 28, "표 7: CoNLL-2003 개체명 인식 F1 (5 재시작 평균, 흩어짐 없음)", 14, weight="bold")
    x0, x1 = 250, 790
    fx = lambda v: x0 + (x1 - x0) * (v - 90) / 8.0
    y0 = 66
    for t in range(90, 99):
        s += line(fx(t), y0 - 6, fx(t), y0 + 11 * 30 - 6, LINE, 0.8, dash="2 3") + txt(fx(t), y0 - 12, str(t), 10, fill=MUTED)
    for j, (nm, dev, test, g) in enumerate(T7):
        y = y0 + j * 30
        c = {"o": INK2, "f": REV, "b": FWD}[g]
        s += txt(x0 - 14, y + 13, nm, 11.5, anchor="end", fill=c)
        if dev is not None:
            s += circ(fx(dev), y + 9, 6, NODE, c, 1.6)
            s += txt(fx(dev) + 10, y + 13, "%.1f" % dev, 10.5, fill=INK2, anchor="start")
        if test is not None:
            s += circ(fx(test), y + 9, 6, c, c)
            s += txt(fx(test) - 10, y + 13, "%.1f" % test, 10.5, fill=INK, anchor="end")
    s += circ(820, 80, 6, NODE, INK2, 1.6) + txt(830, 84, "Dev", 11, fill=INK2, anchor="start")
    s += circ(820, 102, 6, INK2, INK2) + txt(830, 106, "Test", 11, fill=INK2, anchor="start")
    s += lines_at(40, 412, [
        ("「0.3 F1 차」 = Base 미세조정 96.4 - 끝 넷 잇기 96.1. 개발셋 값이다. 특징 줄에는 시험셋 값이 하나도 없다.", INK2),
        ("미세조정 줄의 출력 머리는 선형 층 하나, 특징 줄은 무작위로 시작한 2 층 BiLSTM + 분류 층이다. 0.3 에는 머리 차이도 들어 있다.", INK2),
        ("시험셋 최고는 CSE 93.1 이고 Large 92.8 은 그 아래다. 원문 Abstract · 4 절의 「11 과제」 에 이 과제는 들어 있지 않다(내가 센 것).", NO),
    ], size=11.5, gap=23)
    svg("fig13_table7", W, H, s, "표 7 개체명 인식")


# ── 그림 14: 표 8 ─────────────────────────────────────────────────────────
def fig14():
    W, H = W_DEF, 440
    s = defs()
    s += txt(W / 2, 28, "표 8: 가림 비율 절제 (개발셋, 흩어짐 없음). 같은 말이 같은 크기에 쓰였나", 14, weight="bold")
    xs = [160, 420, 680]
    cols = [(3, "MNLI 미세조정", 83, 85), (4, "NER 미세조정", 94, 96.5), (5, "NER 특징", 93.5, 96.5)]
    y0 = 92
    for (k, nm, lo, hi), x in zip(cols, xs):
        fx = lambda v, lo=lo, hi=hi, x=x: x + 200 * (v - lo) / float(hi - lo)
        s += txt(x + 100, 56, nm, 12.5, weight="bold")
        s += line(fx(lo), y0 - 12, fx(hi), y0 - 12, LINE)
        s += txt(fx(lo), y0 - 20, "%g" % lo, 10, fill=MUTED) + txt(fx(hi), y0 - 20, "%g" % hi, 10, fill=MUTED)
        for j, r in enumerate(T8):
            y = y0 + j * 28
            c = FWD if j == 0 else INK2
            s += line(fx(lo), y, fx(hi), y, LINE, 0.6, dash="2 3")
            s += circ(fx(r[k]), y, 5, c, c)
            s += txt(fx(r[k]) + 9, y + 4, "%.1f" % r[k], 10.5, fill=c, anchor="start")
    for j, r in enumerate(T8):
        s += txt(30, y0 + j * 28 + 4, "%d / %d / %d" % r[:3], 11, fill=FWD if j == 0 else INK2, anchor="start", weight="bold" if j == 0 else None)
    s += txt(30, 58, "MASK/SAME/RND", 10.5, fill=INK2, anchor="start")
    # 다른 표의 같은 설정
    yr = y0 + 6 * 28
    s += txt(30, yr + 4, "다른 표의 같은 설정", 11, fill=REV, anchor="start")
    for x, (lo, hi), v, lab in [(xs[0], (83, 85), 84.4, "표 5"), (xs[1], (94, 96.5), 96.4, "표 7 Base"), (xs[2], (93.5, 96.5), 96.1, "표 7 끝 넷 잇기")]:
        px = x + 200 * (v - lo) / float(hi - lo)
        s += diamond(px, yr, 7, REV_SOFT, REV)
        s += txt(px - 10, yr + 4, "%s %.1f" % (lab, v), 10.5, fill=REV, anchor="end")
    s += lines_at(40, 300, [
        ("「강건하다(robust)」: 미세조정의 범위 MNLI 0.8 · NER 0.6.", INK2),
        ("「문제가 있었다(problematic)」: NER 특징 100/0/0 은 80/10/10 보다 0.9 낮다.", INK2),
        ("「훨씬 나쁘다(much worse)」: 0/0/100 은 80/10/10 보다 MNLI 0.6 · NER 미세조정 0.5 · NER 특징 0.3 낮다.", INK2),
        ("가장 큰 어긋남은 표 안이 아니라 표 사이에 있다: 같은 80/10/10 인데 NER 미세조정 95.4 대 표 7 의 96.4, 끝 넷 잇기 94.9 대 96.1.", NO),
        ("차 1.0 · 1.2 는 표 8 안 어느 줄 차이(최대 0.9)보다 크다. 표 8 은 모델 크기와 미세조정 설정을 적지 않는다.", NO),
    ], size=11.5, gap=23)
    svg("fig14_table8", W, H, s, "표 8 가림 비율 절제")


# ── 그림 15: 그림 5 ───────────────────────────────────────────────────────
def fig15():
    W, H = W_DEF, 420
    s = defs()
    s += txt(W / 2, 28, "원문 그림 5 를 PDF 의 선 좌표에서 꺼내 다시 그렸다 (MNLI 개발 정확도)", 14, weight="bold")
    x0, x1, y0, y1 = 70, 610, 60, 340
    fx = lambda v: x0 + (x1 - x0) * v / 1000.0
    fy = lambda v: y1 - (y1 - y0) * (v - 76) / 10.0
    s += axes(x0, y0, x1, y1, [0, 200, 400, 600, 800, 1000], [76, 78, 80, 82, 84, 86], fx, fy, xl="사전학습 걸음 수 k (천 걸음)", yl="MNLI 개발 정확도")
    s += line(fx(900), y0, fx(900), y1, CODE, 1.2, dash="4 4")
    s += txt(fx(900) - 4, y0 + 14, "길이 128 → 512 (A.2절 일정을 썼다면)", 10, fill=CODE, anchor="end")
    for ys, c, nm in [(F5_MLM, FWD, "가림 과제"), (F5_LTR, REV, "왼쪽만")]:
        pts = [(fx(a), fy(b)) for a, b in zip(F5_K, ys)]
        s += polyline(pts, c, 2)
        for p in pts:
            s += circ(p[0], p[1], 4, c, c)
    s += txt(fx(1000) + 8, fy(84.4) + 4, "가림 84.4", 11.5, fill=FWD, anchor="start", weight="bold")
    s += txt(fx(1000) + 8, fy(82.2) + 4, "왼쪽만 82.2", 11.5, fill=REV, anchor="start", weight="bold")
    s += box(fx(0) - 7, fy(76.5) - 7, 14, 14, NO_SOFT, NO, 1.2, rx=2)
    s += txt(fx(0) + 14, fy(76.5) + 4, "k = 0 점이 없다 (첫 점 k = 30)", 11, fill=NO, anchor="start")
    rows = [("k", "가림", "왼쪽만", "차")]
    tx = 730
    for i, h in enumerate(rows[0]):
        s += txt(tx + i * 44, 86, h, 10, fill=INK2, weight="bold")
    for j, k in enumerate(F5_K):
        y = 104 + j * 19
        for i, t in enumerate(["%d" % k, "%.1f" % F5_MLM[j], "%.1f" % F5_LTR[j], "%+.1f" % (F5_MLM[j] - F5_LTR[j])]):
            s += txt(tx + i * 44, y, t, 10, fill=INK2)
    s += txt(W / 2, 400, "두 곡선은 k = 50 과 100 사이에서 갈린다. 원문 「500k 대비 1M 에 거의 1.0%」: 500k 는 그려져 있지 않고, 400k 와 600k 를 곧은 줄로 이으면 83.6 이라 차는 0.8 이다(내가 센 것).", 10.5, fill=INK2)
    svg("fig15_fig5_steps", W, H, s, "원문 그림 5 다시 그리기")


# ── 그림 16: 에폭 셈 ──────────────────────────────────────────────────────
def fig16():
    W, H = W_DEF, 350
    s = defs()
    t_print = 1e6 * 128000 / 3.3e9
    tok_sched = 9e5 * 256 * 128 + 1e5 * 256 * 512
    e_sched = tok_sched / 3.3e9
    print("  [A.2] 256 x 512 = %d · 원문 셈 %.1f 에폭 · 길이 일정(256 열 유지) 토큰 %.3e, %.1f 에폭 · GPT 대비 %.2f 배" % (256 * 512, t_print, tok_sched, e_sched, tok_sched / 3.2e10))
    s += txt(W / 2, 28, "A.2 절 「약 40 에폭」 과 같은 절의 「90% 걸음은 길이 128」 (내가 센 것)", 14, weight="bold")
    rows = [("원문 셈: 128,000 토큰 x 100 만 걸음", 1.28e11, FWD, "1.28 x 10¹¹ 토큰 = %.1f 에폭 (원문 약 40)" % t_print),
            ("일정대로, 배치 256 열 유지", tok_sched, REV, "%.2f x 10¹⁰ 토큰 = %.1f 에폭" % (tok_sched / 1e10, e_sched)),
            ("OpenAI GPT: 32,000 낱말 x 100 만 걸음 (A.4절)", 3.2e10, CODE, "3.2 x 10¹⁰ 토큰 = %.1f 에폭 상당" % (3.2e10 / 3.3e9))]
    x0, x1 = 320, 640
    for j, (nm, v, c, t) in enumerate(rows):
        y = 62 + j * 50
        s += txt(x0 - 10, y + 22, nm, 11.5, anchor="end")
        w = (x1 - x0) * v / 1.28e11
        s += '<rect x="%.1f" y="%d" width="%.1f" height="32" fill="%s"/>' % (x0, y, w, c)
        s += txt(x0 + w + 8, y + 21, t, 11.5, fill=INK2, anchor="start")
    s += lines_at(40, 232, [
        ("A.2 절은 길이 128 구간의 배치 크기를 적지 않는다. 토큰 128,000 으로 맞췄다면(열 1,000 개) 원문 셈이 맞고, 256 열 그대로면 12.9 에폭이다.", NO),
        ("256 x 512 = 131,072 인데 원문은 128,000 이라 적는다(2.3% 작다). 열이 512 보다 짧으면 위 값들은 모두 더 작아진다(「≤ 512」).", INK2),
        ("256 열 유지라면 길이 128 구간은 32,768 토큰으로 GPT 의 32,000 과 2.4% 차이고, A.4 절의 「128,000 대 32,000」 은 100 만 걸음 중 10 만 걸음의 값이다.", INK2),
        ("자리 128 ~ 511 (512 칸의 75%) 은 마지막 10 만 걸음에만 쓰인다. 원문이 「자리 임베딩을 배우려고」 라 적는 그 구간이다.", INK2),
    ], size=11, gap=24)
    svg("fig16_epochs", W, H, s, "에폭 셈")


# ── 그림 17: 계보 ─────────────────────────────────────────────────────────
def fig17():
    W, H = W_DEF, 390
    s = defs()
    s += txt(W / 2, 28, "이 편이 놓인 자리 (원문이 인용한 관계와 이 저장소의 앞 노트)", 14, weight="bold")
    nodes = [(40, 70, "DBN · 오토인코더 2006", "층별 비지도 사전학습 후 미세조정", MUTED),
             (260, 70, "사전학습은 왜 돕는가 2010", "처음부터 학습과 견줬다", MUTED),
             (480, 70, "Transformer 2017", "인코더 · 디코더, 번역에서 처음부터", CODE),
             (680, 70, "ELMo 2018", "두 방향 LSTM, 특징 방식", REV),
             (680, 170, "OpenAI GPT 2018", "왼쪽만 Transformer, 미세조정", REV),
             (370, 170, "BERT 2019 (이 편)", "인코더만 · 가림 과제 · NSP", FWD),
             (120, 280, "ViT 2021 (다음 큰 틀)", "이미지 조각 열 위의 인코더", OK),
             (620, 280, "큰 틀 다음 칸", "사용자가 아직 정하지 않았다", MUTED)]
    for (x, y, a, b, c) in nodes:
        s += box(x, y, 190, 56, NODE, c, 1.6 if c == FWD else 1.2)
        s += txt(x + 95, y + 23, a, 12, fill=c, weight="bold")
        s += txt(x + 95, y + 43, b, 10, fill=INK2)
    s += line(575, 126, 500, 168, CODE, 1.4, marker="ac")
    s += line(680, 198, 562, 198, REV, 1.4, marker="ar")
    s += line(700, 126, 540, 168, REV, 1.4, marker="ar")
    s += line(340, 126, 420, 168, INK2, 1.2, dash="4 4", marker="ai")
    s += line(400, 226, 250, 278, OK, 1.2, dash="4 4", marker="ao")
    s += line(520, 226, 680, 278, INK2, 1.2, dash="4 4", marker="ai")
    s += txt(W / 2, 360, "점선은 원문이 적은 관계가 아니라 이 저장소에서 내가 잇는 물음이다. 사전학습의 몫을 처음부터 학습과 견준 칸은 2010 편에 있고 이 편에는 없다.", 11, fill=INK2)
    svg("fig17_lineage", W, H, s, "계보")


# ── 그 밖의 확인 ───────────────────────────────────────────────────────────
for nm, v in T1.items():
    print("  [표 1] %s 칸 아홉 평균 %.2f (원문 %.1f) · WNLI 65.1 더한 열 칸 평균 %.2f" % (nm, sum(v) / 9.0, T1_AVG[nm], (sum(v) + 65.1) / 10.0))
for n in (512, 128):
    p = 0.15 * n
    print("  [가림] 길이 %d: 예측 %.1f · MASK %.2f · 무작위 %.2f · 그대로 %.2f" % (n, p, 0.8 * p, 0.1 * p, 0.1 * p))
print("  [TPU] Base 16 칩 · Large 64 칩 = 4 배, L x H² 비 %.2f, 걸음 속도 100 만 / 4 일 = %.2f 걸음/초" % (24 * 1024 ** 2 / float(12 * 768 ** 2), 1e6 / (4 * 86400.0)))
h = 768
lstm = lambda d: 4 * (d * h + h * h + h)
print("  [표 7] 2 층 BiLSTM (방향마다 768, 입력 3072) %d, 머리 선형(라벨 9 가정) %d" % (2 * lstm(3072) + 2 * lstm(1536), 768 * 9 + 9))

fig01(); fig02(); fig03(); fig04(); fig05(); fig06(); fig07(); fig08(); fig09()
fig10(); fig11(); fig12(); fig13(); fig14(); fig15(); fig16(); fig17()
