# -*- coding: utf-8 -*-
"""CLIP 노트가 쓰는 값. 원문(PMLR v139 게재판 16 쪽 + 보충 자료 25 쪽)의 글자 층에서 옮겼고,
그림 2 · 4 는 PDF 벡터 경로와 글자 좌표로 읽었다.
"""

# 그림 4: 제로샷 CLIP 정확도 - ResNet50 특징 위 로지스틱 회귀(전부 지도) 정확도, 점.
# 이름과 값은 글자 상자의 세로 가운데가 같은 것끼리 짝지었다(27 짝 모두 차 0.0 pt).
FIG4 = [
    ("StanfordCars", 28.9), ("Country211", 23.2), ("Food101", 22.5), ("Kinetics700", 14.5),
    ("SST2", 12.4), ("SUN397", 7.8), ("UCF101", 7.7), ("HatefulMemes", 6.7), ("CIFAR10", 3.9),
    ("CIFAR100", 3.0), ("STL10", 3.0), ("FER2013", 2.8), ("Caltech101", 2.0), ("ImageNet", 1.9),
    ("OxfordPets", 1.1), ("PascalVOC2007", 0.5), ("Birdsnap", -3.2), ("MNIST", -10.0),
    ("FGVCAircraft", -11.3), ("RESISC45", -11.9), ("Flowers102", -12.5), ("DTD", -16.6),
    ("CLEVRCounts", -18.2), ("GTSRB", -18.4), ("PatchCamelyon", -19.5), ("KITTI Distance", -34.0),
    ("EuroSAT", -37.1),
]
# 본문 3.2절이 문장으로 적은 값
TEXT_32 = {"wins": 16, "of": 27, "most_improved": "STL10", "STL10_acc": 99.3,
           "Kinetics700": 14.5, "UCF101": 7.7}

# 그림 2: 이미지 수(백만) 대 제로샷 ImageNet 정확도(%), 선의 꼭짓점 좌표를 눈금으로 환산.
# x 는 2M(76.19 pt) · 400M(281.04 pt) 사이 선형, y 는 0(221.12 pt) · 40(74.98 pt) 눈금 글자 가운데.
FIG2_X = [2.0, 4.1, 8.3, 16.7, 33.4, 66.9, 133.9, 267.9, 400.0]
FIG2 = {
    "Transformer 언어 모형 (캡션 예측)": [0.25, 0.44, 1.17, 2.10, 4.54, 6.69, 9.03, 13.18, 16.01],
    "낱말 주머니 예측": [0.54, 1.22, 2.39, 4.69, 7.08, 12.01, 15.91, 21.96, 26.65],
    "낱말 주머니 대조 (CLIP)": [2.05, 3.42, 8.30, 11.57, 18.45, 23.96, 28.26, 36.60, 41.05],
}
FIG2_ARROWS = {"3X": (278.88, 146.24), "4X": (141.93, 89.84)}  # 화살표 양 끝 x (pt), 둘 다 y = 16.0%

# 표 1
TABLE1 = {"aYahoo": (72.4, 98.4), "ImageNet": (11.5, 76.2), "SUN": (23.0, 58.5)}  # (Visual N-Grams, CLIP)

# 그림 7 오른쪽: (ImageNet ResNet101, 제로샷 CLIP), top-1 %
FIG7 = {"ImageNet": (76.2, 76.2), "ImageNetV2": (64.3, 70.1), "ImageNet-A": (2.7, 77.1),
        "ImageNet-R": (37.7, 88.9), "ObjectNet": (32.6, 72.3), "ImageNet Sketch": (25.2, 60.2)}
FIG7_DELTA = {"ImageNet": 0.0, "ImageNetV2": 5.8, "ImageNet-A": 74.4, "ImageNet-R": 51.2,
              "ObjectNet": 39.7, "ImageNet Sketch": 35.0}

# 부록 B: 프롬프트
PROMPT_IMAGENET = {"template": 1.3, "ensemble80": 3.5, "together_text": "almost 5%"}
FIG14 = {"median": 5.4, "mean": 20.8, "max": 184}
FIG15 = {"r": 0.82, "slope": 1.28, "ci": (0.93, 1.79), "near_sup": 5}

# 부록 C · 본문 4절: 데이터 겹침
OVERLAP = {"datasets": 35, "none": 9, "median": 2.2, "mean": 3.2, "above_0.1": 7, "bonferroni": 2,
           "binomial_sig": 6, "ci_excl0": 5, "birdsnap_overlap": 12.1, "birdsnap_gain": 0.6,
           "country211_overlap": 21.5, "country211_gain": 0.2}

# 부록 D
ADAPT = {"zero_shot": 76.2, "gain": 9.2, "adapted": 85.4,
         "drops": {"ImageNet-R": 4.7, "ObjectNet": 3.8, "ImageNet Sketch": 2.8, "ImageNet-A": 1.9}}

# 부록 F 표 11 (Oxford-IIIT Pets, 37 품종, 3,669 장, 사람 다섯)
TABLE11 = {"Zero-shot human": (53.7, 57.0, 69.7, 63.9), "Zero-shot CLIP": (93.5, 93.5, 93.5, 93.5),
           "One-shot human": (75.7, 80.3, 78.5, 81.2), "Two-shot human": (75.7, 85.0, 79.2, 86.1)}

# 부록 G 표 12: (선형 YFCC, 선형 WIT, 제로샷 YFCC, 제로샷 WIT)
TABLE12 = {"Birdsnap": (47.4, 35.3, 19.9, 4.5), "Country211": (23.1, 17.3, 5.2, 5.3),
           "Flowers102": (94.4, 89.8, 48.6, 21.7), "GTSRB": (66.8, 72.5, 6.9, 7.0),
           "UCF101": (69.2, 74.9, 22.9, 32.0), "Stanford Cars": (31.4, 50.3, 3.8, 10.9),
           "ImageNet": (62.0, 60.8, 31.3, 27.6), "Dataset Average": (65.5, 66.6, 29.6, 30.0)}
TABLE12_WINS = {"linear": (10, 15), "zero": (19, 18)}

# 부록 I 표 18 ~ 20
COMMON = {"batch": 32768, "vocab": 49408, "epochs": 32, "max_temperature": 100.0, "weight_decay": 0.2,
          "warmup": 2000}
RESNETS = {  # 학습률, 임베딩 차원, 입력, ResNet 블록, ResNet 폭, 글 층, 글 폭, 글 머리
    "RN50": (5e-4, 1024, 224, (3, 4, 6, 3), 2048, 12, 512, 8),
    "RN101": (5e-4, 512, 224, (3, 4, 23, 3), 2048, 12, 512, 8),
    "RN50x4": (5e-4, 640, 288, (4, 6, 10, 6), 2560, 12, 640, 10),
    "RN50x16": (4e-4, 768, 384, (6, 8, 18, 8), 3072, 12, 768, 12),
    "RN50x64": (3.6e-4, 1024, 448, (3, 15, 36, 10), 4096, 12, 1024, 16),
}
VITS = {  # 학습률, 임베딩 차원, 입력, ViT 층, ViT 폭, ViT 머리, 글 층, 글 폭, 글 머리
    "ViT-B/32": (5e-4, 512, 224, 12, 768, 12, 12, 512, 8),
    "ViT-B/16": (5e-4, 512, 224, 12, 768, 12, 12, 512, 8),
    "ViT-L/14": (4e-4, 768, 224, 24, 1024, 16, 12, 768, 12),
    "ViT-L/14-336px": (2e-5, 768, 336, 24, 1024, 16, 12, 768, 12),
}
GPU_DAYS = {"RN50x64": (18, 592), "ViT-L/14": (12, 256)}  # (일, V100 수)
WIT = {"pairs": 400e6, "queries": 500000, "per_query": 20000, "yfcc_filtered": 15e6, "yfcc_share": 0.037}
CELEBA = {"top1_100": 59.2, "top1_1000": 43.3}
FAIRFACE = {"young_egregious": 32.3, "with_child": 8.7}
