# -*- coding: utf-8 -*-
"""WinCLIP 노트가 쓰는 원문 값. 본문은 CVF 공개판(11 쪽), 부록은 CVF 보충 자료(11 쪽)에서 옮겼다.

보충 자료의 숫자는 arXiv v1 부록과 모두 같다(인용 번호만 다르다). 부류별 표는 arXiv v1 의 글자 층에서 뽑았다.

부록 D 의 부류별 표 10~21 은 같은 폴더 appendix_classwise.json 에 있다.
값은 (평균, 표준편차) 이고 단위는 % 다. 0 장 줄의 표준편차는 원문에 ±0.0 으로 적혀 있다.
"""

METHODS = ("SPADE", "PaDiM", "PatchCore", "WinCLIP+")
SHOTS = (1, 2, 4)

# 표 1 (분류, AUROC · AUPR · F1-max) 과 표 4 (분할, pAUROC · PRO · F1-max). 열쇠 = (과제, 데이터)
MAIN = {
    ("AC", "MVTec-AD"): {
        "CLIP-AC_0": (74.0, 89.1, 88.5), "CLIP-AC+ens_0": (74.1, 89.5, 87.8), "WinCLIP_0": (91.8, 96.5, 92.9),
        "SPADE_1": (81.0, 90.6, 90.3), "PaDiM_1": (76.6, 88.1, 88.2), "PatchCore_1": (83.4, 92.2, 90.5), "WinCLIP+_1": (93.1, 96.5, 93.7),
        "SPADE_2": (82.9, 91.7, 91.1), "PaDiM_2": (78.9, 89.3, 89.2), "PatchCore_2": (86.3, 93.8, 92.0), "WinCLIP+_2": (94.4, 97.0, 94.4),
        "SPADE_4": (84.8, 92.5, 91.5), "PaDiM_4": (80.4, 90.5, 90.2), "PatchCore_4": (88.8, 94.5, 92.6), "WinCLIP+_4": (95.2, 97.3, 94.7),
    },
    ("AC", "VisA"): {
        "CLIP-AC_0": (59.3, 67.0, 74.4), "CLIP-AC+ens_0": (58.2, 66.4, 74.0), "WinCLIP_0": (78.1, 81.2, 79.0),
        "SPADE_1": (79.5, 82.0, 80.7), "PaDiM_1": (62.8, 68.3, 75.3), "PatchCore_1": (79.9, 82.8, 81.7), "WinCLIP+_1": (83.8, 85.1, 83.1),
        "SPADE_2": (80.7, 82.3, 81.7), "PaDiM_2": (67.4, 71.6, 75.7), "PatchCore_2": (81.6, 84.8, 82.5), "WinCLIP+_2": (84.6, 85.8, 83.0),
        "SPADE_4": (81.7, 83.4, 82.1), "PaDiM_4": (72.8, 75.6, 78.0), "PatchCore_4": (85.3, 87.5, 84.3), "WinCLIP+_4": (87.3, 88.8, 84.2),
    },
    ("AS", "MVTec-AD"): {
        "Trans-MM_0": (57.5, 21.9, 12.1), "MaskCLIP_0": (63.7, 40.5, 18.5), "WinCLIP_0": (85.1, 64.6, 31.7),
        "SPADE_1": (91.2, 83.9, 42.4), "PaDiM_1": (89.3, 73.3, 40.2), "PatchCore_1": (92.0, 79.7, 50.4), "WinCLIP+_1": (95.2, 87.1, 55.9),
        "SPADE_2": (92.0, 85.7, 44.5), "PaDiM_2": (91.3, 78.2, 43.7), "PatchCore_2": (93.3, 82.3, 53.0), "WinCLIP+_2": (96.0, 88.4, 58.4),
        "SPADE_4": (92.7, 87.0, 46.2), "PaDiM_4": (92.6, 81.3, 46.1), "PatchCore_4": (94.3, 84.3, 55.0), "WinCLIP+_4": (96.2, 89.0, 59.5),
    },
    ("AS", "VisA"): {
        "Trans-MM_0": (49.4, 10.2, 3.1), "MaskCLIP_0": (60.9, 27.3, 7.3), "WinCLIP_0": (79.6, 56.8, 14.8),
        "SPADE_1": (95.6, 84.1, 35.5), "PaDiM_1": (89.9, 64.3, 17.4), "PatchCore_1": (95.4, 80.5, 38.0), "WinCLIP+_1": (96.4, 85.1, 41.3),
        "SPADE_2": (96.2, 85.7, 40.5), "PaDiM_2": (92.0, 70.1, 21.1), "PatchCore_2": (96.1, 82.6, 41.0), "WinCLIP+_2": (96.8, 86.2, 43.5),
        "SPADE_4": (96.6, 87.3, 43.6), "PaDiM_4": (93.2, 72.6, 24.6), "PatchCore_4": (96.8, 84.9, 43.9), "WinCLIP+_4": (97.2, 87.6, 47.0),
    },
}
# 표 1 · 4 의 표준편차 가운데 노트가 인용하는 것
STD = {("AC", "MVTec-AD", "WinCLIP+_1"): 2.0, ("AC", "MVTec-AD", "PatchCore_1"): 3.0,
       ("AC", "VisA", "WinCLIP+_1"): 4.0, ("AC", "VisA", "PatchCore_1"): 2.9,
       ("AC", "VisA", "WinCLIP+_4"): 1.6, ("AC", "VisA", "PatchCore_4"): 1.3}

# 표 2 (MVTec-AD, AC AUROC · AS pAUROC, 다른 논문의 값과 함께)
TABLE2 = [("WinCLIP", "0-shot", 91.8, 85.1), ("WinCLIP+", "1-shot", 93.1, 95.2), ("WinCLIP+", "4-shot", 95.2, 96.2),
          ("DifferNet", "16-shot", 87.3, None), ("TDG", "10-shot", 78.0, None), ("RegAD-L", "2-shot", 81.5, 93.3),
          ("RegAD", "4 + agg.", 88.2, 95.8), ("MKD", "full-shot", 87.7, 90.7), ("P-SVDD", "full-shot", 92.1, 95.7),
          ("CutPaste", "full-shot", 95.2, 96.0), ("PatchCore", "full-shot", 99.6, 98.2)]

# 표 3 (MVTec-AD 0 장 분류 쌓기, AUROC · AUPR · F1-max)
TABLE3 = [("One-class", 34.2, 68.9, 83.5), ("Two-class", 74.0, 89.1, 88.5), ("+ State ens.", 89.8, 95.6, 92.2),
          ("+ Prompt ens.", 90.8, 96.1, 92.5), ("+ Multi-crop", 91.8, 96.5, 92.9)]

# 표 5 (MVTec-AD 분류 AUROC, 장 수 1 · 2 · 4 · 8)
TABLE5 = {"max M^W only": (87.9, 91.0, 92.6, 94.5), "ascore0 only": (91.8, 91.8, 91.8, 91.8), "both": (93.1, 94.4, 95.2, 96.3)}
# 표 6 (MVTec-AD 분할 pAUROC, 장 수 1 · 2 · 4 · 8)
TABLE6 = {"M^P": (94.5, 94.8, 95.4, 95.8), "M^P + M^W_m": (95.1, 95.7, 96.3, 96.6), "M^P + M^W_m + M^W_s": (95.2, 96.0, 96.2, 96.5)}
# 표 7 (VisA 0 장 분류 AUROC)
TABLE7 = {"WinCLIP": {"PCB2": 51.2, "PCB4": 79.6, "Pipe fryum": 69.7, "Mean": 78.1},
          "+ specific states": {"PCB2": 56.5, "PCB4": 82.7, "Pipe fryum": 70.4, "Mean": 78.9}}
# 표 8 (MVTec-AD 0 장 분할, pAUROC · PRO · F1-max · 이미지당 시간 ms(평균, 표준편차), EC2 G4dn)
TABLE8 = [("Patch-token", 22.4, 2.3, 8.0, 95.5, 18.8), ("Image tiling", 77.9, 57.5, 25.5, 1442.1, 62.2),
          ("WinCLIP", 85.1, 64.6, 31.7, 389.4, 18.5), ("w/o image-scale", 82.0, 63.0, 29.5, 378.6, 20.2),
          ("w/o mid-scale", 84.0, 61.6, 30.5, 190.7, 13.9), ("w/o small-scale", 84.7, 63.6, 30.6, 265.4, 15.9),
          ("w/o Harmonic avg.", 81.5, 60.5, 27.3, 279.9, 22.8)]

# 부록 표 8 (MVTec-AD 장 수별, AC AUROC · AUPR · F1-max, AS pAUROC · PRO · F1-max). 머리글은 AS 를 앞에 적었으나 값은 AC 가 앞이다
APPX_TABLE8 = {
    1: {"PatchCore WRN-50-2": (83.4, 92.2, 90.5, 92.0, 79.7, 50.4), "PatchCore hidden ViT-B/16+": (79.9, 88.6, 88.7, 91.8, 74.1, 47.6),
        "PatchCore last ViT-B/16+": (83.3, 90.7, 89.8, 92.3, 74.5, 47.7), "WinCLIP+": (92.7, 96.7, 93.5, 95.2, 87.1, 55.9)},
    2: {"PatchCore WRN-50-2": (86.3, 93.8, 92.0, 93.3, 82.3, 53.0), "PatchCore hidden ViT-B/16+": (84.1, 90.7, 90.2, 93.5, 77.9, 51.4),
        "PatchCore last ViT-B/16+": (86.5, 92.3, 91.1, 93.1, 76.8, 49.8), "WinCLIP+": (94.0, 97.0, 94.0, 96.0, 88.4, 58.4)},
    4: {"PatchCore WRN-50-2": (88.8, 94.5, 92.6, 94.3, 84.3, 55.0), "PatchCore hidden ViT-B/16+": (87.5, 92.5, 91.7, 94.7, 81.2, 54.4),
        "PatchCore last ViT-B/16+": (89.9, 94.2, 92.7, 94.0, 78.9, 52.2), "WinCLIP+": (94.8, 97.5, 94.2, 96.2, 89.0, 59.5)},
}
# 부록 표 9 (MVTec-AD 0 장, 백본별, 입력 크기 · AC AUROC · AS pAUROC)
APPX_TABLE9 = [("RN50", 224, 79.8, 65.6), ("RN101", 224, 79.2, 62.4), ("RN50x4", 288, 81.9, 71.3), ("RN50x16", 384, 82.3, 65.3),
               ("ViT-B/16", 224, 86.1, 71.1), ("ViT-B/16+", 240, 90.8, 85.1), ("ViT-L/14", 224, 86.1, 64.4)]

# 부록 그림 6 (조합 프롬프트 묶음 목록). [o] 는 데이터셋의 물체 이름
STATE_NORMAL = ["[o]", "flawless [o]", "perfect [o]", "unblemished [o]", "[o] without flaw", "[o] without defect", "[o] without damage"]
STATE_ANOMALY = ["damaged [o]", "[o] with flaw", "[o] with defect", "[o] with damage"]
TEMPLATES = ["a cropped photo of the [c].", "a cropped photo of a [c].", "a close-up photo of a [c].", "a close-up photo of the [c].",
             "a bright photo of a [c].", "a bright photo of the [c].", "a dark photo of the [c].", "a dark photo of a [c].",
             "a jpeg corrupted photo of a [c].", "a jpeg corrupted photo of the [c].", "a blurry photo of the [c].", "a blurry photo of a [c].",
             "a photo of a [c].", "a photo of the [c].", "a photo of a small [c].", "a photo of the small [c].",
             "a photo of a large [c].", "a photo of the large [c].", "a photo of the [c] for visual inspection.",
             "a photo of a [c] for visual inspection.", "a photo of the [c] for anomaly detection.", "a photo of a [c] for anomaly detection."]
# 위 22 개 가운데 CLIP 저장소 notebooks/Prompt_Engineering_for_ImageNet.ipynb 의 imagenet_templates(80 개)에 같은 문장이 있는 것.
# 2026-11-17 에 그 노트북을 받아 문자열로 대조했다. 없는 넷은 visual inspection · anomaly detection 줄이다.
TEMPLATES_IN_CLIP80 = 18

# 부록 A: 입력은 짧은 변 240 으로 bicubic 크기 조정, ViT-B/16+ 는 240x240 -> 조각 225 개(15 x 15). 창 크기는 조각 단위 2x2 · 3x3, 보폭 1
INPUT = 240
PATCH = 16
WINDOWS = {"small": 2, "mid": 3}
# 부록 A: VisA 처럼 정사각형이 아닌 이미지는 짧은 변 Ls 의 정사각 타일을 긴 변을 따라 보폭 최대 0.8 Ls 로 잘라 예측을 평균한다
TILE_STRIDE_MAX = 0.8
