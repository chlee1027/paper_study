# -*- coding: utf-8 -*-
"""RD 노트가 쓰는 원문 값. make_figures.py 가 불러 쓴다. 바깥 데이터를 읽지 않는다.

이 편의 값은 CVF 게재판 표 1 ~ 7 을 PDF 글자 층에서 옮겼다.
「이 편 밖의 값」 은 이 저장소의 앞 노트 그림 코드에 이미 옮겨 둔 원 논문 값을 다시 적은 것이다.
"""
CL = ["carpet", "grid", "leather", "tile", "wood", "bottle", "cable", "capsule", "hazelnut", "metal nut",
      "pill", "screw", "toothbrush", "transistor", "zipper"]
TEX = CL[:5]

# 표 1 (이미지 AUROC). 열: MKD(128) Ours(128) | GT GN US PSVDD DAAD MF PaDiM CutPaste Ours (256)
T1_COLS = ["MKD-128", "Ours-128", "GT", "GN", "US", "PSVDD", "DAAD", "MF", "PaDiM", "CutPaste", "Ours"]
T1 = {
    "carpet":     [79.3, 99.2, 43.7, 69.9, 91.6, 92.9, 86.6, 94.0, 99.8, 93.9, 98.9],
    "grid":       [78.0, 95.7, 61.9, 70.8, 81.0, 94.6, 95.7, 85.9, 96.7, 100, 100],
    "leather":    [95.1, 100, 84.1, 84.2, 88.2, 90.9, 86.2, 99.2, 100, 100, 100],
    "tile":       [91.6, 99.4, 41.7, 79.4, 99.1, 97.8, 88.2, 99.0, 98.1, 94.6, 99.3],
    "wood":       [94.3, 98.8, 61.1, 83.4, 97.7, 96.5, 98.2, 99.2, 99.2, 99.1, 99.2],
    "bottle":     [99.4, 100, 74.4, 89.2, 99.0, 98.6, 97.6, 99.1, 99.9, 98.2, 100],
    "cable":      [89.2, 97.1, 78.3, 75.7, 86.2, 90.3, 84.4, 97.1, 92.7, 81.2, 95.0],
    "capsule":    [80.5, 89.5, 67.0, 73.2, 86.1, 76.7, 76.7, 87.5, 91.3, 98.2, 96.3],
    "hazelnut":   [98.4, 99.8, 35.9, 78.5, 93.1, 92.0, 92.1, 99.4, 92.0, 98.3, 99.9],
    "metal nut":  [73.6, 99.2, 81.3, 70.0, 82.0, 94.0, 75.8, 96.2, 98.7, 99.9, 100],
    "pill":       [82.7, 93.3, 63.0, 74.3, 87.9, 86.1, 90.0, 90.1, 93.3, 94.9, 96.6],
    "screw":      [83.3, 91.1, 50.0, 74.6, 54.9, 81.3, 98.7, 97.5, 85.8, 88.7, 97.0],
    "toothbrush": [92.2, 90.3, 97.2, 65.3, 95.3, 100, 99.2, 100, 96.1, 99.4, 99.5],
    "transistor": [85.6, 99.5, 86.9, 79.2, 81.8, 91.5, 87.6, 94.4, 97.4, 96.1, 96.7],
    "zipper":     [93.2, 94.3, 82.0, 74.5, 91.9, 97.9, 85.9, 98.6, 90.3, 99.9, 98.5],
}
T1_TEX = [87.7, 98.6, 58.5, 77.5, 91.5, 94.5, 91.0, 95.5, 98.8, 97.5, 99.5]
T1_OBJ = [87.8, 95.4, 71.6, 75.5, 85.8, 90.8, 88.8, 96.0, 93.8, 95.5, 98.0]
T1_ALL = [87.8, 96.5, 67.2, 76.2, 87.7, 92.1, 89.5, 95.8, 95.5, 96.1, 98.5]
# 쪽 이미지 · 글꼴로 읽은 굵은 칸 (256 열만). 캡션은 「부류마다 위 둘을 굵게」
T1_BOLD = {
    "carpet": ["PaDiM", "Ours"], "grid": ["CutPaste", "Ours"], "leather": ["MF", "PaDiM", "CutPaste", "Ours"],
    "tile": ["US", "Ours"], "wood": ["MF", "PaDiM", "CutPaste", "Ours"], "bottle": ["PaDiM", "Ours"],
    "cable": ["MF", "Ours"], "capsule": ["CutPaste", "Ours"], "hazelnut": ["MF", "Ours"], "metal nut": ["CutPaste", "Ours"],
    "pill": ["CutPaste", "Ours"], "screw": ["DAAD", "MF"], "toothbrush": ["PSVDD", "MF", "Ours"],
    "transistor": ["PaDiM", "Ours"], "zipper": ["MF", "CutPaste"],
}

# 표 2 (픽셀 AUROC, PRO). None 은 원문의 「-」. 열: MKD(128) Ours(128) | US MF SPADE PaDiM RIAD CutPaste Ours (256)
T2_COLS = ["MKD-128", "Ours-128", "US", "MF", "SPADE", "PaDiM", "RIAD", "CutPaste", "Ours"]
T2 = {
    "carpet":     [(95.6, None), (98.1, 95.3), (None, 87.9), (None, 87.8), (97.5, 94.7), (99.1, 96.2), (96.3, None), (98.3, None), (98.9, 97.0)],
    "grid":       [(91.8, None), (97.3, 92.6), (None, 95.2), (None, 86.5), (93.7, 86.7), (97.3, 94.6), (98.8, None), (97.5, None), (99.3, 97.6)],
    "leather":    [(98.1, None), (99.0, 98.6), (None, 94.5), (None, 95.9), (97.6, 97.2), (99.2, 97.8), (99.4, None), (99.5, None), (99.4, 99.1)],
    "tile":       [(82.8, None), (92.6, 84.8), (None, 94.6), (None, 88.1), (87.4, 75.9), (94.1, 86.0), (89.1, None), (90.5, None), (95.6, 90.6)],
    "wood":       [(84.8, None), (92.1, 82.3), (None, 91.1), (None, 84.8), (88.5, 87.4), (94.9, 91.1), (85.8, None), (95.5, None), (95.3, 90.9)],
    "bottle":     [(96.3, None), (98.2, 94.7), (None, 93.1), (None, 88.8), (98.4, 95.5), (98.3, 94.8), (98.4, None), (97.6, None), (98.7, 96.6)],
    "cable":      [(82.4, None), (97.8, 90.5), (None, 81.8), (None, 93.7), (97.2, 90.9), (96.7, 88.8), (84.2, None), (90.0, None), (97.4, 91.0)],
    "capsule":    [(95.9, None), (96.5, 87.2), (None, 96.8), (None, 87.9), (99.0, 93.7), (98.5, 93.5), (92.8, None), (97.4, None), (98.7, 95.8)],
    "hazelnut":   [(94.6, None), (98.8, 89.2), (None, 96.5), (None, 88.6), (99.1, 95.4), (98.2, 92.6), (96.1, None), (97.3, None), (98.9, 95.5)],
    "metal nut":  [(86.4, None), (96.6, 84.1), (None, 94.2), (None, 86.9), (98.1, 94.4), (97.2, 85.6), (92.5, None), (93.1, None), (97.3, 92.3)],
    "pill":       [(89.6, None), (97.0, 90.0), (None, 96.1), (None, 93.0), (96.5, 94.6), (95.7, 92.7), (95.7, None), (95.7, None), (98.2, 96.4)],
    "screw":      [(96.0, None), (98.3, 94.4), (None, 94.2), (None, 95.4), (98.9, 96.0), (98.5, 94.4), (98.8, None), (96.7, None), (99.6, 98.2)],
    "toothbrush": [(96.1, None), (98.2, 86.7), (None, 93.3), (None, 87.7), (97.9, 93.5), (98.8, 93.1), (98.9, None), (98.1, None), (99.1, 94.5)],
    "transistor": [(76.5, None), (97.6, 85.2), (None, 66.6), (None, 92.6), (94.1, 87.4), (97.5, 84.5), (87.7, None), (93.0, None), (92.5, 78.0)],
    "zipper":     [(93.9, None), (97.0, 92.3), (None, 95.1), (None, 93.6), (96.5, 92.6), (98.5, 95.9), (97.8, None), (99.3, None), (98.2, 95.4)],
}
T2_TEX = [(90.6, None), (95.8, 90.7), (None, 92.7), (None, 88.6), (92.9, 88.4), (96.9, 93.2), (93.9, None), (96.3, None), (97.7, 95.0)]
T2_OBJ = [(90.8, None), (97.6, 89.4), (None, 90.8), (None, 90.8), (97.6, 93.4), (97.8, 91.6), (94.3, None), (95.8, None), (97.9, 93.4)]
T2_ALL = [(90.7, None), (97.0, 89.9), (None, 91.4), (None, 90.1), (96.5, 91.7), (97.5, 92.1), (94.2, None), (96.0, None), (97.8, 93.9)]

# 표 3: 추론 시간(초, Intel i7) · 메모리(MB) · (AD-AUROC, AL-AUROC, AL-PRO)
T3 = [("SPADE", 1.40, 1400, (85.5, 96.5, 91.7)), ("PaDiM", 0.95, 3800, (95.5, 97.5, 92.1)),
      ("Ours", 0.31, 352, (98.5, 97.8, 93.9))]
# 표 4: MNIST F-MNIST CIFAR10 Caltech-256
T4 = [("LSA", 97.5, 92.2, 64.1, None), ("OCGAN", 97.3, 87.8, 65.7, None), ("HRN", 97.6, 92.8, 71.3, None),
      ("DAAD", 99.0, None, 75.3, None), ("MKD", 98.7, 94.5, 84.5, None), ("G2D", None, None, None, 95.7),
      ("OiG", None, None, None, 98.2), ("Ours", 99.3, 95.0, 86.5, 99.9)]
# 표 5 · 6 · 7: (AD-AUROC, AL-AUROC, PRO). 원문 표의 줄 이름은 「RPO」
T5 = [("Pre", 96.0, 96.9, 91.2), ("Pre+OCE", 97.9, 97.4, 92.4), ("Pre+OCE+MFM", 98.5, 97.8, 93.9)]
T6 = [("ResNet18", 97.9, 97.1, 91.2), ("ResNet50", 98.4, 97.7, 93.1), ("WResNet50", 98.5, 97.8, 93.9)]
T7 = [("M1", 90.1, 94.0, 88.6), ("M2", 97.5, 96.9, 92.6), ("M3", 97.2, 96.9, 89.5), ("M2,3", 98.0, 97.6, 93.2),
      ("M1,2,3", 98.5, 97.8, 93.9)]

# ---------------------------------------------------------------- 이 편 밖의 값
# DRAEM 표 1 (이미지 AUROC) 의 DRAEM · PaDiM · US · GANomaly 열, 표 2 (픽셀 AUROC) 의 DRAEM · RIAD 열
# (figures/ICCV21_DRAEM/make_figures.py 의 T1 · T2 에서 옮김)
DRAEM_IMG = {"bottle": 99.2, "capsule": 98.5, "grid": 99.9, "leather": 100, "pill": 98.9, "tile": 99.6, "transistor": 93.1,
             "zipper": 100, "cable": 91.8, "carpet": 97.0, "hazelnut": 100.0, "metal nut": 98.7, "screw": 93.9,
             "toothbrush": 100, "wood": 99.1}
DRAEM_PIX = {"bottle": 99.1, "capsule": 94.3, "grid": 99.7, "leather": 98.6, "pill": 97.6, "tile": 99.2, "transistor": 90.9,
             "zipper": 98.8, "cable": 94.7, "carpet": 95.5, "hazelnut": 99.7, "metal nut": 99.5, "screw": 97.6,
             "toothbrush": 98.1, "wood": 96.4}
DRAEM_T1_PADIM = {"bottle": 99.9, "capsule": 91.3, "grid": 96.7, "leather": 100, "pill": 93.3, "tile": 98.1, "transistor": 97.4,
                  "zipper": 90.3, "cable": 92.7, "carpet": 99.8, "hazelnut": 92.0, "metal nut": 98.7, "screw": 85.8,
                  "toothbrush": 96.1, "wood": 99.2}
DRAEM_T1_US = {"bottle": 99.0, "capsule": 86.1, "grid": 81.0, "leather": 88.2, "pill": 87.9, "tile": 99.1, "transistor": 81.8,
               "zipper": 91.9, "cable": 86.2, "carpet": 91.6, "hazelnut": 93.1, "metal nut": 82.0, "screw": 54.9,
               "toothbrush": 95.3, "wood": 97.7}
DRAEM_T1_GAN = {"bottle": 79.4, "capsule": 72.1, "grid": 74.3, "leather": 80.8, "pill": 67.1, "tile": 72.0, "transistor": 80.8,
                "zipper": 74.4, "cable": 71.1, "carpet": 82.1, "hazelnut": 87.4, "metal nut": 69.4, "screw": 100,
                "toothbrush": 70.0, "wood": 92.0}
DRAEM_T2_RIAD = {"bottle": 98.4, "capsule": 92.8, "grid": 98.8, "leather": 99.4, "pill": 95.7, "tile": 89.1, "transistor": 87.7,
                 "zipper": 97.8, "cable": 84.2, "carpet": 96.3, "hazelnut": 96.1, "metal nut": 92.5, "screw": 98.8,
                 "toothbrush": 98.9, "wood": 85.8}
DRAEM_AVG = (98.0, 97.3)
# PaDiM 원 논문 부류별 픽셀 AUROC · PRO (WRN-50-2). PatchCore 원문 표 S2 · S3 의 PaDiM 행으로 옮긴 값
# (figures/CVPR22_PatchCore/make_figures.py). 픽셀 AUROC 는 DRAEM 노트에서 PaDiM 원문과 직접 맞춘 값과 같다
PADIM_PIX = {"bottle": 98.3, "cable": 96.7, "capsule": 98.5, "carpet": 99.1, "grid": 97.3, "hazelnut": 98.2, "leather": 99.2,
             "metal nut": 97.2, "pill": 95.7, "screw": 98.5, "tile": 94.1, "toothbrush": 98.8, "transistor": 97.5,
             "wood": 94.9, "zipper": 98.5}
PADIM_PRO = {"bottle": 94.8, "cable": 88.8, "capsule": 93.5, "carpet": 96.2, "grid": 94.6, "hazelnut": 92.6, "leather": 97.8,
             "metal nut": 85.6, "pill": 92.7, "screw": 94.4, "tile": 86.0, "toothbrush": 93.1, "transistor": 84.5,
             "wood": 91.1, "zipper": 95.9}
# SPADE 원 논문 표 2 (픽셀 AUROC) · 표 3 (PRO), Uninformed Students 원 논문 표 3 의 Multiscale 열 (PRO)
# (figures/arXiv20_SPADE/make_figures.py)
SPADE_PIX = {"carpet": 97.5, "grid": 93.7, "leather": 97.6, "tile": 87.4, "wood": 88.5, "bottle": 98.4, "cable": 97.2,
             "capsule": 99.0, "hazelnut": 99.1, "metal nut": 98.1, "pill": 96.5, "screw": 98.9, "toothbrush": 97.9,
             "transistor": 94.1, "zipper": 96.5}
SPADE_PRO = {"carpet": 94.7, "grid": 86.7, "leather": 97.2, "tile": 75.9, "wood": 87.4, "bottle": 95.5, "cable": 90.9,
             "capsule": 93.7, "hazelnut": 95.4, "metal nut": 94.4, "pill": 94.6, "screw": 96.0, "toothbrush": 93.5,
             "transistor": 87.4, "zipper": 92.6}
US_PRO = {"carpet": 87.9, "grid": 95.2, "leather": 94.5, "tile": 94.6, "wood": 91.1, "bottle": 93.1, "cable": 81.8,
          "capsule": 96.8, "hazelnut": 96.5, "metal nut": 94.2, "pill": 96.1, "screw": 94.2, "toothbrush": 93.3,
          "transistor": 66.6, "zipper": 95.1}
# PatchSVDD 원 논문 부류별 이미지 AUROC (PatchCore 원문 표 S1 의 PatchSVDD 행)
PSVDD_IMG = {"bottle": 98.6, "cable": 90.3, "capsule": 76.7, "carpet": 92.9, "grid": 94.6, "hazelnut": 92.0, "leather": 90.9,
             "metal nut": 94.0, "pill": 86.1, "screw": 81.3, "tile": 97.8, "toothbrush": 100, "transistor": 91.5,
             "wood": 96.5, "zipper": 97.9}
# 원 논문이 낸 이미지 AUROC 평균 (앞 노트에서): SPADE 85.5, PaDiM(WRN-50-2) 95.3
SPADE_IMG_AVG, PADIM_IMG_AVG = 85.5, 95.3
