# -*- coding: utf-8 -*-
r"""AnomalyCLIP 노트가 쓰는 값 가운데 tables_anomalyclip.json 에 없는 것.

표 1 \~ 5 · 7 \~ 21 과 그림 6 · 7 은 read_tables.py 가 PDF 에서 읽어 tables_anomalyclip.json 에 둔다.
여기는 막대 위 글자로 찍힌 그림 5 · 8 의 값, 표 6 의 데이터 통계, 설정값을 손으로 옮긴 것이다.
"""

# 그림 5 (9 쪽): 물체 이름 대신 object 를 쓴 판 - 물체 이름을 쓴 판. 막대 위 글자를 막대의 가로 자리로 지표에 붙였다
# (데이터셋마다 왼쪽부터 이미지 AUROC · AP · 화소 AUROC · AUPRO 차례, 범례와 같은 색).
FIG5_GAIN = {  # (image AUROC, AP, pixel AUROC, AUPRO)
    "MVTec AD": (0.8, 0.0, 0.6, 1.0),
    "VisA": (0.3, 0.5, 0.5, 0.2),
    "MPDD": (4.4, 3.3, 0.8, 0.9),
    "BTAD": (0.3, 0.3, 0.1, 1.8),
    "SDD": (0.8, 0.0, 0.4, 0.9),
    "DAGM": (0.5, 0.3, 0.7, 0.3),
    "DTD-Synthetic": (0.1, 0.0, 0.0, 0.6),
}

# 그림 8 (19 쪽): object 로 배운 뒤 시험 때만 물체 이름을 넣은 판(AnomalyCLIP_re)
FIG8 = {  # 지표: {데이터: (AnomalyCLIP, AnomalyCLIP_re)}
    "image AUROC": {"MVTec AD": (91.5, 89.1), "VisA": (82.1, 82.0)},
    "AP": {"MVTec AD": (96.2, 94.5), "VisA": (85.4, 85.0)},
    "pixel AUROC": {"MVTec AD": (91.1, 90.5), "VisA": (95.5, 95.0)},
    "AUPRO": {"MVTec AD": (81.4, 80.6), "VisA": (87.0, 86.6)},
}

# 표 6 (16 쪽): 시험 집합의 (정상, 이상) 장 수와 부류 수
TABLE6 = {
    "MVTec AD": (15, 467, 1258), "VisA": (12, 962, 1200), "MPDD": (6, 176, 282), "BTAD": (3, 451, 290),
    "SDD": (1, 181, 74), "DAGM": (10, 6996, 1054), "DTD-Synthetic": (12, 357, 947),
    "ISIC": (1, 0, 379), "CVC-ClinicDB": (1, 0, 612), "CVC-ColonDB": (1, 0, 380), "Kvasir": (1, 0, 1000),
    "Endo": (1, 0, 200), "TN3K": (1, 0, 614), "HeadCT": (1, 100, 100), "BrainMRI": (1, 98, 155),
    "Br35H": (1, 1500, 1500), "COVID-19": (1, 1341, 219),
}
MEDICAL_TUNE = (163, 380)  # 부록 B: ColonDB 이상 380 장 + Endo 분류 데이터 시험 분할의 정상 163 장

# 설정 (4.1절, 부록 A.1)
SETTINGS = {
    "backbone": "CLIP ViT-L/14@336px",
    "input": 518, "patch": 14,
    "prompt_len_E": 12, "text_deep_layers": 9, "text_deep_len": 4,
    "visual_layers": (6, 12, 18, 24), "dpam_from_layer": 6, "dpam": "V-V",
    "lambda": 1, "batch": 8, "optimizer": "Adam", "lr": 0.001, "epochs": 15, "gauss_sigma": 4,
    "gpu": "RTX 3090 24GB", "framework": "PyTorch 2.0.0",
}
# CLIP 원문 보충 자료 표 20 (CLIP-ViT 하이퍼파라미터) 의 ViT-L/14-336px 줄
CLIP_L14_336 = {"embed_dim": 768, "input": 336, "vision_layers": 24, "vision_width": 1024,
                "text_layers": 12, "text_width": 768}
