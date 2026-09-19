# 색인 — 읽은 것과 읽으려는 것

**노트가 있는 것만 「읽었다」에 올린다.** 초록만 본 것은 「아직 안 읽음」에 둔다. 줄마다 **왜 읽었는지**를 한 조각 적어 둔다 — 반년 뒤에 그 줄이 있어야 다시 찾는다.

---

## 읽었다

| 논문 | 게재처·연도 | 한 줄 | 왜 읽었는가 | 노트 |
|---|---|---|---|---|
| **퍼셉트론** — The Perceptron: A Probabilistic Model for Information Storage | Psychological Review 1958 | 가중치를 더해 문턱을 넘으면 1을 내는 소자 하나와, 틀렸을 때만 그 입력 방향으로 가중치를 옮기는 규칙. **직선 하나로 갈리는 문제만 푼다** | 신경망의 첫 자리. **한계(XOR·기울기 없음·은닉층에 정답 없음)가 그대로 다음 논문들의 목차가 된다** | [PsychRev58_Perceptron](notes/PsychRev58_Perceptron_A_Probabilistic_Model_for_Information_Storage.md) |
| **역전파** — Learning representations by back-propagating errors | Nature 1986 | 오차의 기울기를 위층에서 아래층으로 넘겨 **은닉 유닛에도 몫을 나눈다.** 새로운 것은 연쇄 법칙 네 줄(식 4-7)이고, 가족 트리 과제에서 은닉 유닛이 **국적·세대·집안의 갈래**라는 축을 스스로 만들었다 | 퍼셉트론이 못 하던 것(기울기가 없다, 은닉층에 정답이 없다)을 그대로 푼 편. **한계 절을 논문이 적은 것과 내가 짚은 것으로 갈라 두었다** | [Nature86_Backprop](notes/Nature86_Backprop_Learning_representations_by_back_propagating_errors.md) |
| **DDPM** — Denoising Diffusion Probabilistic Models | NeurIPS 2020 | 데이터에 잡음을 더하는 고정된 과정을 거꾸로 되돌리는 신경망을 학습한다. 평균이 아니라 **더해진 잡음을 예측**하게 하고 변분 하한의 가중치를 버리자 CIFAR10 FID가 13.51에서 3.17로 내려갔다 | 확산 모델의 출발점이라 생성 모델 계열을 읽으려면 먼저 봐야 한다. 이상 탐지 쪽에서도 재구성 기반 방법(AnoDDPM 등)이 이 논문의 두 식을 그대로 쓴다 | [NeurIPS20_DDPM](notes/NeurIPS20_DDPM_Denoising_Diffusion_Probabilistic_Models.md) |

---

## 아직 안 읽음 (읽으려는 순서대로)

| 논문 | 게재처·연도 | 왜 읽으려 하는가 | 원문을 구했는가 |
|---|---|---|---|
| **DBN** — A Fast Learning Algorithm for Deep Belief Nets | Neural Computation 2006 | 역전파가 있어도 층이 깊어지면 학습이 되지 않던 시기를 다룬 편. 로지스틱의 기울기 최댓값 0.25가 층마다 곱해지는 문제와 바로 이어진다 | https://www.cs.toronto.edu/~hinton/absps/fastnc.pdf 로 열린다 |
| **DDIM** — Denoising Diffusion Implicit Models | ICLR 2021 | DDPM의 1000스텝을 10~50스텝으로 줄인다. 같은 학습 모델을 그대로 쓰므로 DDPM 다음에 바로 읽힌다 | 아직 |
| **AnoDDPM** | CVPR Workshops 2022 | 확산 모델을 이상 탐지에 쓴 편. 순방향으로 어디까지 보낼지(t₀)를 고르는 문제가 DDPM §3의 표와 바로 이어진다 | 아직 |

---

## 돌려 본 것

| 실험 | 질문 | 결과 한 줄 | 폴더 |
|---|---|---|---|
| | | | |

---

## 주제 묶음

읽은 것이 쌓이면 여기에 주제별로 다시 묶는다. **묶음 이름은 미리 정하지 않는다** — 세 편이 같은 자리에 모이면 그때 이름을 붙인다.
