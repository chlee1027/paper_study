"""Kalman (1960) 재입력판 PDF 에서 노트에 싣는 그림을 잘라 낸다. PyMuPDF 가 필요하다.

python crop_paper_figures.py  (저장소 뿌리의 papers/ 에 PDF 가 있어야 한다)
"""
from pathlib import Path
import pymupdf

HERE = Path(__file__).resolve().parent
PDF = HERE.parents[1] / "papers" / "JBE60_Kalman_A_New_Approach_to_Linear_Filtering_and_Prediction_Problems.pdf"

# (쪽 번호(0부터), 자를 사각형(pt), 저장 이름)
CROPS = [
    (5, (309, 569, 600, 722), "paper_fig3_optimal_filter.png"),
    (7, (310, 188, 600, 316), "paper_fig4_optimal_controller.png"),
]

doc = pymupdf.open(PDF)
for page, rect, name in CROPS:
    pix = doc[page].get_pixmap(dpi=200, clip=pymupdf.Rect(*rect))
    pix.save(HERE / name)
    print(name, pix.width, "x", pix.height)
