# 진행 기록

이 파일은 README 첫머리에 날짜순으로 쌓여 있던 진행 기록과, 판이 바뀐 규칙의 옛 문장을 옮겨 둔 곳이다. 지금 상태는 `README.md` 에 있다.

## 2026-11-18 까지의 「지금 있는 것」 (2026-11-18 README 에서 옮김)

- **노트 마흔넷.** 읽는 순서는 퍼셉트론에서 DDPM 까지의 로드맵을 따르고, **노트마다 한계를 적은 뒤 그 한계를 푼 편을 다음으로 읽는다.** 편마다 한 줄 요약과 읽은 까닭은 `INDEX.md` 에 있다. 이상 탐지 논문 다섯 편(MVTec AD · Uninformed Students · PaDiM · VisA · Real-IAD)은 노트가 [`beyond-mvtec`](https://github.com/chlee1027/beyond-mvtec) 저장소 `papers/notes/` 에 있어 `INDEX.md` 에 줄과 링크만 둔다.
- **두 갈래가 길어졌다.** 깊은 망을 배워지게 만드는 장치(역전파 → DBN · 오토인코더 → 사전학습은 왜 돕는가 → AlexNet → VGG → BN → ResNet → 사전 활성 ResNet → Wide ResNet)와 생성 모델(오토인코더 → VAE → GAN → Wasserstein GAN → DDPM → DDIM → Score SDE → Latent Diffusion)이다. Wide ResNet 은 연구에서 쓰는 PatchCore 의 특징 추출기(WRN-50-2)의 원 논문이다.
- **로드맵 두 갈래가 다 끝났다.** 갈래 A(이미지와 생성)는 2026-11-03 에, 갈래 B(RNN → LSTM → GRU → seq2seq → Attention → Transformer)는 2026-11-04 에 끝났다. 그다음 큰 틀로 정한 ViT 와 함께 읽은 BERT 도 2026-11-05 에 읽었다. 이어서 고른 확산 심화(DDIM → Score SDE → Latent Diffusion)도 2026-11-06 에 읽었다. 같은 날 정한 산업 이상 탐지(SPADE → 코어셋 → AnoDDPM → UniAD)도 2026-11-07 에 읽었다. 이어서 고른 분할 · 검출(U-Net → Faster R-CNN → Mask R-CNN → YOLO)도 2026-11-08 에 읽었다. 2026-11-10 에 그다음 큰 틀로 산업 이상 탐지 2막(DRAEM → Reverse Distillation → SimpleNet → EfficientAD)을 골라 첫 칸 DRAEM 을 읽었고, 2026-11-11 에 둘째 칸 Reverse Distillation 을, 2026-11-14 에 셋째 칸 SimpleNet 을, 2026-11-16 에 마지막 칸 EfficientAD 를 읽었다. **2026-11-17 에 다음 큰 틀로 CLIP 계열 제로샷 이상 탐지(CLIP → WinCLIP → AnomalyCLIP)를 골라 같은 날 첫 칸 CLIP 과 둘째 칸 WinCLIP 을, 2026-11-18 에 마지막 칸 AnomalyCLIP 을 읽었다.** 그다음 큰 틀은 아직 정하지 않았다.
- **연구에서 쓰는 방법(PatchCore)을 원문으로 읽었다.** 깊은 망 갈래의 끝자리(Wide ResNet)를 얼려 쓰는 편이라, 백본과 단계를 고른 근거를 앞 노트들의 물음과 맞춰 봤다.
- **산업 이상 탐지 네 편의 판본이 갈린다.** AnoDDPM(CVF) · UniAD(NeurIPS 본문 + 보충 자료)는 게재판이고, 코어셋은 머리글에 ICLR 2018 이 찍힌 arXiv v4(OpenReview 판은 로그인 요구로 못 받았다), SPADE 는 찾은 범위에서 학회판을 못 찾아 arXiv v3 다. **AnoDDPM 의 수치는 뇌 MRI 뿐이고 MVTec 은 가죽 이미지 둘의 그림이다.**
- **산업 이상 탐지 2막의 원문 넷을 받아 두었다.** DRAEM(CVF 본문 + 보충 자료) · Reverse Distillation(CVF)은 게재판이고, SimpleNet 은 arXiv v2, EfficientAD 는 부록 A\~F 가 붙은 arXiv v3(27쪽)다. DRAEM 은 arXiv 판과 대조하지 않았다. **EfficientAD arXiv v3 본문(1\~8쪽, 참고문헌 앞까지)의 소수점 수치 172개는 게재판(WACV 2024)과 모두 같았다(arXiv 번호와 게재판 DOI 의 숫자는 뺀 수).** 글자가 다른 자리는 저자 소속 하나(게재판에만 TU Munich), arXiv 에만 있는 문장 둘(hard feature loss 가 정상 이미지의 점수 이상치를 막는다는 문장, 총손실이 세 손실의 합이라는 문장), 「AU-ROC computed on pixel anomaly scores」가 게재판에서 「AU-ROC」로 줄어든 자리, 「Appendix X」가 게재판에서 「the supplementary material」인 자리, 인용 번호(참고문헌 수가 달라 번호가 밀린다)다.

  > 2026-11-10 에 처음 쓴 판은 「EfficientAD(IEEE Xplore)는 게재판」이었다. 그 PDF 는 모든 쪽에 학교 라이선스 문구가 찍혀 있어 공개 저장소에 올리지 않았고, 같은 날 arXiv v3 으로 바꿨다.
- **분할 · 검출 네 편은 모두 게재판을 읽었다.** U-Net(Springer) · YOLO(CVF)는 arXiv 판과 숫자가 같았다. Faster R-CNN(NIPS) · Mask R-CNN(CVF)은 arXiv v3 이 표를 더 실은 다른 판이라, 대조한 대목만 읽고 노트에 따로 적었다.
- **GAN 은 두 판을 다 읽었다.** 2020 년 개관판을 먼저 읽고 식 절반을 직접 유도해 적었고, 원판(NIPS 2014)을 읽어 그 유도를 하나씩 맞춰 봤다. 식 셋이 같았고, 개관판 노트에서 고친 자리는 그 노트 안에 날짜를 단 인용 블록으로 남겼다.
- **실험 다섯.** 넷(퍼셉트론 · 역전파 · DBN · LeNet)은 결과까지 들어 있고, AlexNet 은 질문과 가설만 적었다. **2026-11-03 부터 새 실험은 돌리지 않고 논문의 실험을 분석하는 것으로 바꿨다**(아래 「실험 하나를 넣는 절차 셋」).

## 원문 PDF 규칙의 옛 판

> 2026-11-17 까지의 판: 「PDF는 넣되 **한 편이 30MB를 넘으면 넣기 전에 한 번 생각한다** — 저장소는 지운 파일도 기록에 남긴다.」 이 판으로 올린 PDF 46 편은 2026-11-17 에 추적에서 뺐지만, 앞 커밋의 기록에는 남아 있다.

- 2026-11-18: 위 옛 판으로 올렸던 PDF 46 편을 저장소 기록 전체에서 지웠다(`git filter-repo`, 이날 앞의 커밋 해시는 모두 바뀌었다).
