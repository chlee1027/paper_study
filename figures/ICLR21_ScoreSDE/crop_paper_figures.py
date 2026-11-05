"""원문 PDF 에서 그림 몇 장을 잘라 png 로 둔다. 이 파일이 있는 폴더 기준으로 실행한다."""
import os
import pymupdf

here = os.path.dirname(os.path.abspath(__file__))
pdf = os.path.join(here, "..", "..", "papers",
                   "ICLR21_ScoreSDE_Score_Based_Generative_Modeling_through_Stochastic_Differential_Equations.pdf")
doc = pymupdf.open(pdf)
# (이름, 쪽, x0, y0, x1, y1, dpi) — 좌표는 PDF 포인트
CROPS = [
    ("paper_fig2_overview", 4, 100, 60, 512, 215, 170),
    ("paper_fig3_nfe", 8, 104, 76, 508, 192, 300),
    ("paper_fig9_pc_lsun", 23, 110, 480, 500, 625, 200),
    ("paper_fig4_conditional", 9, 104, 78, 508, 220, 170),
]
for name, page, x0, y0, x1, y1, dpi in CROPS:
    pix = doc[page - 1].get_pixmap(dpi=dpi, clip=pymupdf.Rect(x0, y0, x1, y1))
    pix.save(os.path.join(here, name + ".png"))
    print(name, pix.width, pix.height)
