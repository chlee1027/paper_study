# 색인 — 읽은 것과 읽으려는 것

**노트가 있는 것만 「읽었다」에 올린다.** 초록만 본 것은 「아직 안 읽음」에 둔다. 줄마다 **왜 읽었는지**를 한 조각 적어 둔다 — 반년 뒤에 그 줄이 있어야 다시 찾는다.

---

## 읽었다

| 논문 | 게재처·연도 | 한 줄 | 왜 읽었는가 | 노트 |
|---|---|---|---|---|
| **퍼셉트론** — The Perceptron: A Probabilistic Model for Information Storage | Psychological Review 1958 | 가중치를 더해 문턱을 넘으면 1을 내는 소자 하나와, 틀렸을 때만 그 입력 방향으로 가중치를 옮기는 규칙. **직선 하나로 갈리는 문제만 푼다** | 신경망의 첫 자리. **한계(XOR·기울기 없음·은닉층에 정답 없음)가 그대로 다음 논문들의 목차가 된다** | [PsychRev58_Perceptron](notes/PsychRev58_Perceptron_A_Probabilistic_Model_for_Information_Storage.md) |
| **역전파** — Learning representations by back-propagating errors | Nature 1986 | 오차의 기울기를 위층에서 아래층으로 넘겨 **은닉 유닛에도 몫을 나눈다.** 새로운 것은 연쇄 법칙 네 줄(식 4-7)이고, 가족 트리 과제에서 은닉 유닛이 **국적·세대·집안의 갈래**라는 축을 스스로 만들었다 | 퍼셉트론이 못 하던 것(기울기가 없다, 은닉층에 정답이 없다)을 그대로 푼 편. **한계 절을 논문이 적은 것과 내가 짚은 것으로 갈라 두었다** | [Nature86_Backprop](notes/Nature86_Backprop_Learning_representations_by_back_propagating_errors.md) |
| **DDPM** — Denoising Diffusion Probabilistic Models | NeurIPS 2020 | 데이터에 잡음을 더하는 고정된 과정을 거꾸로 되돌리는 신경망을 학습한다. 평균이 아니라 **더해진 잡음을 예측**하게 하고 변분 하한의 가중치를 버리자 CIFAR10 FID가 13.51에서 3.17로 내려갔다 | 확산 모델의 출발점이라 생성 모델 계열을 읽으려면 먼저 봐야 한다. 이상 탐지 쪽에서도 재구성 기반 방법(AnoDDPM 등)이 이 논문의 두 식을 그대로 쓴다 | [NeurIPS20_DDPM](notes/NeurIPS20_DDPM_Denoising_Diffusion_Probabilistic_Models.md) |
| **DBN** — A Fast Learning Algorithm for Deep Belief Nets | Neural Computation 2006 | 깊은 망을 한 번에 배우지 않고 **한 층씩 배워 얼리고 그 위에 또 얹는다.** 위층 가중치를 묶어 **상보 사전분포**를 만들면 사후분포가 정확히 곱꼴이 되고, 그 자리에서 한 층을 배우는 일이 **RBM 하나를 배우는 일**로 줄어든다. MNIST 순열 불변 조건에서 1.25% | 역전파 노트가 남긴 한계 하나(로지스틱 기울기 최댓값 0.25 가 층마다 곱해진다)를 그대로 받는 편. **탐욕 학습 2.49% 와 미세조정 1.25% 의 몫이 갈려 있지 않다는 것을 짚어 두었다** | [NC06_DBN](notes/NC06_DBN_A_Fast_Learning_Algorithm_for_Deep_Belief_Nets.md) |
| **LeNet** — Gradient-Based Learning Applied to Document Recognition | Proceedings of the IEEE 1998 | 가중치에 **국소 수용장 · 가중치 공유 · 부분 표본 뽑기** 셋을 걸어 2차원 모양의 이동과 일그러짐을 견디게 만든다. LeNet-5 는 연결이 340,908 개인데 **학습되는 값은 60,000 개**이고 MNIST 시험 10,000 장에서 0.95%. 뒤쪽 절반은 자르기·인식·언어 지식을 **문서 수준 벌점 하나**로 함께 배우는 그래프 변환망이다 | DBN 노트가 남긴 한계 셋(지각 불변성)과 넷(분할이 끝났다고 가정한다)을 함께 받는 편. **다만 이 논문이 여덟 해 앞이라, 한계에 답한 것이 아니라 그 자리에 이미 놓여 있던 것이다.** 논문이 문장으로만 적고 재지 않은 자리 둘(픽셀을 섞으면 · 얼마나 옮겨도 견디는가)을 실험으로 옮겼다 | [ProcIEEE98_LeNet](notes/ProcIEEE98_LeNet_Gradient_Based_Learning_Applied_to_Document_Recognition.md) |
| **AlexNet** — ImageNet Classification with Deep Convolutional Neural Networks | NIPS 2012 | 합성곱 망을 **학습되는 층 여덟 · 파라미터 6천만**으로 키우고, 커지면서 생기는 두 문제를 각각 막는다 — 느린 학습은 **ReLU 와 GPU 둘로 쪼개기**로, 과적합은 **데이터 늘리기와 드롭아웃**으로. ILSVRC-2010 에서 top-1 37.5% · top-5 17.0%(그전 최고 47.1 · 28.2), 2012 대회는 top-5 15.3% 로 우승(2등 26.2%) | LeNet 노트 17절이 다음으로 꼽은 둘(**크게 키운 편** · **최댓값 풀링으로 바꾼 편**)이 한 편에 들어 있다. **1998년의 6만 파라미터가 2012년에 6천만이 되는 자리** | [NIPS12_AlexNet](notes/NIPS12_AlexNet_ImageNet_Classification_with_Deep_Convolutional_Neural_Networks.md) |
| **오토인코더** — Reducing the Dimensionality of Data with Neural Networks | Science 2006 | RBM 을 한 층씩 쌓아 **깊은 오토인코더의 출발점을 먼저 찾고**, 펼쳐서 역전파로 재구성 오차를 줄인다. 이미지당 제곱 오차가 곡선 6 차원 1.44(주성분 18 차원 5.90) · MNIST 30 차원 3.00(13.87) · 얼굴 30 차원 126(135). 같은 사전학습으로 MNIST 분류 1.2% | 로드맵의 AE 칸. 같은 해 DBN 논문이 낸 **쌓기를 무엇에 쓰는가**를 보이는 편이다. **주성분 분석과의 비교가 파라미터 105~389 배 차이 위에 서 있고, 사전학습의 몫을 가르는 행이 본문에 없다는 것을 짚어 두었다** | [Science06_AE](notes/Science06_AE_Reducing_the_Dimensionality_of_Data_with_Neural_Networks.md) |
| **VAE** — Auto-Encoding Variational Bayes | ICLR 2014 | 표본을 뽑는 자리를 $z = \mu + \sigma \odot \varepsilon$ 으로 바꿔(**재매개변수화**) 변분 하한의 기울기를 낮은 분산으로 추정한다. 부호기를 신경망으로 두면 오토인코더 모양이 되는데 **부호기가 점이 아니라 분포를 내고, 그 분포가 $\mathcal{N}(0, I)$ 에서 멀어질수록 KL 벌점**을 받는다. MNIST · Frey Face 에서 깨어남-잠보다 하한을 빨리, 높이 올렸다 | 로드맵의 VAE 칸. 오토인코더 노트가 남긴 한계(코드에 분포가 없어 새 이미지를 만들 길이 없다)를 받는 편. **「잠재 변수를 늘려도 과적합이 늘지 않는다」가 Frey Face 에서는 눈금과 어긋나고(학습-시험 간격 60 → 180), 하한과 $\log p(x)$ 의 틈을 재지 않는다는 것을 짚어 두었다** | [ICLR14_VAE](notes/ICLR14_VAE_Auto_Encoding_Variational_Bayes.md) |
| **GAN** — Generative Adversarial Networks (**CACM 2020 개관판**, 원판은 NIPS 2014) | Communications of the ACM 2020 | 밀도를 적지 않고 **잡음을 표본으로 바꾸는 생성기**와 **진짜·가짜를 가르는 판별기**를 겨루게 한다. 학습은 최적화가 아니라 두 사람 게임의 평형 찾기라서 가능도가 필요 없는 대신 **수렴 보장이 없다**. 원 논문의 두 이론 결과(밀도 함수 공간에서 평형은 p_model = p_data 하나, 안쪽 고리로 수렴)를 옮기고 「실제로 자주 수렴에 실패한다」고 적는다 | 로드맵의 GAN 칸. VAE 노트가 남긴 한계(복호기의 픽셀별 가능도를 사람이 정한다)를 판별기에 맡기는 편. **받은 파일이 6 쪽 개관판이라 식이 하나뿐이어서 최적 판별기 · JSD · 포화를 내가 유도해 넣었고, 이론이 서는 비용(M-GAN)과 권하는 비용(NS-GAN)이 다르다는 것을 짚어 두었다** | [CACM20_GAN](notes/CACM20_GAN_Generative_Adversarial_Networks.md) |
| **VGG** — Very Deep Convolutional Networks for Large-Scale Image Recognition | ICLR 2015 | 모든 합성곱을 **3x3 · 보폭 1** 로 고정하고 깊이만 11 → 19 층으로 바꿔 잰다. 3x3 세 층은 7x7 과 수용장이 같고 파라미터가 27C² 대 49C². 설정 A → E 에서 파라미터는 1.08 배인데 계산은 2.58 배(7.61 → 19.63 G). 망 둘 앙상블 top-5 6.8%, 위치 찾기 1 등 | AlexNet 노트가 남긴 「더 깊게 · 커널을 작게 간 편」. **19 층에서 포화한다는 결론이 한 행에 서 있고, 깊이를 바꿀 때 초기화 · 계산량도 함께 바뀐다는 것과 검증 집합을 시험 집합으로도 썼다는 것을 짚어 두었다** | [ICLR15_VGG](notes/ICLR15_VGG_Very_Deep_Convolutional_Networks_for_Large_Scale_Image_Recognition.md) |
| **BN** — Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift | ICML 2015 | 층 입력을 **미니배치 평균 · 분산으로 정규화**하고 γ · β 로 표현력을 되찾는다. 핵심은 정규화를 역전파 안에 넣은 것이고, 추론 때는 모집단 통계로 고정한 선형 변환이 된다. Inception 72.2% 까지 BN 만으로 걸음 수 2.33 배 감소, BN + 변경 일곱으로 14.8 배. 앙상블 top-5 4.82% | AlexNet 노트가 남긴 「LRN 을 버리고 다른 정규화로 간 편」이자 깊은 망 학습 문제의 정규화 쪽 답. **「내부 공변량 이동」을 잰 곳은 MNIST 활성 하나뿐이고, 「14 배」가 BN 하나의 몫이 아니라는 것을 짚어 두었다** | [ICML15_BN](notes/ICML15_BN_Batch_Normalization_Accelerating_Deep_Network_Training_by_Reducing_Internal_Covariate_Shift.md) |
| **ResNet** — Deep Residual Learning for Image Recognition | CVPR 2016 | 층이 H(x) 대신 **잔차 F(x) = H(x) − x** 를 배우고 항등 지름길로 x 를 더한다. 평범한 34 층 28.54% → 잔차 34 층 25.03%(top-1 10-crop), 152 층(11.3 G)이 VGG-19(19.6 G)보다 싸고 앙상블 top-5 3.57%. 파라미터 수를 직접 세어 torchvision 과 같음을 확인했다 | 「깊으면 안 배워진다」 흐름(역전파 기울기 감소 → DBN · AE 사전학습 → ReLU → VGG → BN)의 결론이고, **PatchCore 특징 추출기(WideResNet-50)의 원형**이다. 「기울기가 건강하다」에 수치가 없고 변동 폭이 110 층 한 곳뿐이라는 것을 짚어 두었다 | [CVPR16_ResNet](notes/CVPR16_ResNet_Deep_Residual_Learning_for_Image_Recognition.md) |

---

## 아직 안 읽음 (읽으려는 순서대로)

| 논문 | 게재처·연도 | 왜 읽으려 하는가 | 원문을 구했는가 |
|---|---|---|---|
| **원 GAN** — Generative Adversarial Nets | NIPS 2014 | GAN 노트 3절 — 읽은 파일(CACM 2020)에 가치 함수 · 증명 · 알고리즘 · 실험이 없어 노트의 식 절반이 내 유도다. 원문과 맞춰 본다 | 아직 |
| **Wasserstein GAN** | arXiv 2017 | GAN 노트 9절 — 모델이 데이터에서 멀면 JSD 가 위 끝(log 2)에 붙어 평평하다(m=5 에서 97.5%). 다른 거리를 쓰면 무엇이 바뀌는지 본다 | 아직 |
| **Wide Residual Networks** | BMVC 2016 | ResNet 노트 — PatchCore 가 쓰는 WideResNet-50-2 의 원 논문. 깊이 대신 폭을 늘리면 무엇이 바뀌는지, layer2 · layer3 특징이 왜 쓸 만한지 본다 | 아직 |
| **Identity Mappings in Deep Residual Networks** | ECCV 2016 | ResNet 노트 — 더한 뒤의 ReLU 가 지름길을 순수 항등이 아니게 만들고, 1202 층이 110 층보다 나빴다. 순서를 바꾸면 무엇이 풀리는지 본다 | 아직 |
| **How Does Batch Normalization Help Optimization?** | NeurIPS 2018 | BN 노트 — 원 논문이 「내부 공변량 이동을 줄여서」라고 적지만 잰 곳이 활성 하나뿐이다. 그 설명이 맞는지 따로 잰 편 | 아직 |
| **GoogLeNet** — Going Deeper with Convolutions | CVPR 2015 | VGG 노트 — 같은 해 대회 우승 편. 1x1 · 3x3 · 5x5 를 나란히 두어 계산을 어떻게 줄였는지 본다 | 아직 |
| **Glorot · Bengio 초기화** — Understanding the difficulty of training deep feedforward neural networks | AISTATS 2010 | VGG 노트 — 논문이 「제출 뒤에 이 초기화면 사전학습이 필요 없음을 알았다」고 적는다. 분산을 맞추는 초기화가 사전학습을 어떻게 대신하는지 본다 | 아직 |
| **하한을 조이는 편** (중요도 가중 하한) | - | VAE 노트 19절 셋 — 하한과 $\log p(x)$ 의 틈을 같은 모델에서 잰 자리가 없다. 표본 여럿으로 하한을 조이면 틈이 얼마나 주는지 본다 | 편을 아직 못 골랐다 |
| **대각 가우스 근사 사후분포를 넓힌 편** (흐름 기반) | - | VAE 노트 10절 · 18절 — 각주가 「대각 가우스는 한계가 아니다」라고 적지만 실험은 대각 가우스뿐이다 | 편을 아직 못 골랐다 |
| **DDIM** — Denoising Diffusion Implicit Models | ICLR 2021 | DDPM의 1000스텝을 10~50스텝으로 줄인다. 같은 학습 모델을 그대로 쓰므로 DDPM 다음에 바로 읽힌다 | 아직 |
| **AnoDDPM** | CVPR Workshops 2022 | 확산 모델을 이상 탐지에 쓴 편. 순방향으로 어디까지 보낼지(t₀)를 고르는 문제가 DDPM §3의 표와 바로 이어진다 | 아직 |
| **층별 사전학습이 정말 필요한가를 잰 편** | - | DBN 이 답하지 않은 자리다. **직접 재 보니 이 규모(10,000 장·은닉 256)에서는 도움이 됐고 깊을수록 커졌다**([dbn_2006](experiments/dbn_2006/)). 남은 것은 **규모를 올려도 그 차이가 남는가** — 라벨이 많을수록 차이가 줄었으므로 60,000 장에서는 사라질 수 있다. 그 모양을 잰 편을 찾는다 | 편을 아직 못 골랐다 |
| **RBM 을 실수값 입력으로 넓힌 편** | - | DBN 의 한계 1 — 이진값이 아닌 값을 확률로 다룰 수 있는 이미지를 전제한다. 자연 이미지로 가려면 이 자리가 먼저다 | 아직 |
| **부분 표본 뽑기를 최댓값 풀링으로 바꾼 편** | - | LeNet 노트 15절 둘 — 이 논문의 부분 표본에는 **학습되는 계수와 바이어스**가 있어 오늘날의 최댓값 풀링과 같은 것이 아니다. **AlexNet(2012)을 읽었는데도 이 자리는 안 닫혔다** — 겹치게 할지만 재고(−0.4/−0.3) 평균 대 최댓값이나 학습되는 계수를 둘지는 재지 않는다 | 편을 아직 못 골랐다 |
| **분할 없이 글자열을 읽는 편** | - | LeNet 노트 11절 — 휴리스틱 과분할과 SDNN 중 어느 쪽도 **라벨 열만으로 배우는 문제**를 끝내지 못했다. 이 논문의 제약된 해석 그래프와 앞방향 벌점이 그쪽에서 어떤 모양으로 남는지 본다 | 아직 |

---

## 돌려 본 것

| 실험 | 질문 | 결과 한 줄 | 폴더 |
|---|---|---|---|
| **퍼셉트론 (1958)** | 노트에 적어 둔 한계 넷이 실제로 그 모양으로 나타나는가 | **가설 여섯이 모두 맞았다.** AND · OR는 50/50 멈추고 XOR는 0/50이다. 수렴 정리의 한계를 넘은 행이 80 중 0개이지만 **한계가 실제보다 한참 크다**(762 대 7). 멈춘 경계의 여유는 가장 큰 여유의 **중앙값 0.537**이라 절반쯤에서 끝난다. 네 점의 라벨링 16 중 **14가 갈리고 못 갈리는 둘은 XOR와 XNOR뿐**이다 | [perceptron_1958](experiments/perceptron_1958/) |
| **역전파 (1986)** | 논문의 두 실험이 다시 나오는가, 숫자 없이 적힌 두 문장을 숫자로 바꿀 수 있는가 | **대칭 검출은 재현된다** — 46/50이 풀리고 세 크기의 비가 늘 **1.00 : 1.98 : 3.94**다. **둘은 재현되지 않았다**: 논문의 ε = 0.01로는 가족 트리가 학습되지 않았고(엄격 0/100), **은닉 유닛을 늘리자 갇히는 비율이 오히려 올라갔다**(0.08 → 0.56, 전부 늘 0을 내는 해). 깊이마다 기울기가 **10~12배씩** 줄어든다 | [backprop_1986](experiments/backprop_1986/) |
| **DBN (2006)** | 논문에 없는 대조군 — 무작위 초기화에 같은 미세조정만 얹으면 얼마가 나오는가 | **사전학습이 세 깊이 모두 이기고 차이가 깊이를 따라 커진다**(+0.0130 → +0.0215 → +0.0245, seed 변동 폭 0.0055~0.0090). **무작위 쪽은 층을 늘려도 안 나아진다**(0.0565 → 0.0575). 라벨 100 장에서는 차이가 **0.5150** 으로 벌어진다. 기울기는 사전학습이 키우는 것이 아니라 **깊이에 걸쳐 편다**(3층 대 1층 감쇠가 14.8 배 대 4.9 배). CD 걸음 수를 올리면 **재구성 오차는 올라가고 자유 에너지 간격은 는다** — 둘이 다른 것을 잰다 | [dbn_2006](experiments/dbn_2006/) |
| **LeNet (1998)** | 세 생각 중 무엇이 얼마를 내는가. 논문이 문장으로만 적은 둘 — 픽셀을 섞으면 · 얼마나 옮겨도 견디는가 | **층별 학습되는 값 여섯이 모두 논문과 같고 합계가 정확히 60,000** 이다(시험 오차 2.01%). **픽셀을 고정 순열로 섞자 완전연결은 4.96 에서 4.87 로 변동 폭(0.25) 안**인데 합성곱은 89.90 이 됐다 — 다만 학습 오차도 89.5~90.6% 라 **「나빠진 것」이 아니라 「이 학습률에서 배우지 못한 것」**이다. **가중치 공유만 끄면 +0.64 백분율 점**(파라미터 5.5 배), **표 I 대 전부 연결은 −0.03 으로 변동 폭 안**이라 순서를 매기지 않는다. **옮겨서 견디는 폭은 ±1 픽셀** — 논문의 추정(±10 픽셀)과 같은 칸에 놓으려면 왜곡 학습을 넣고 다시 재야 한다 | [lenet_1998](experiments/lenet_1998/) |
| **AlexNet (2012)** | 새로 넣은 넷(ReLU · LRN · 겹치는 풀링 · 드롭아웃)이 각각 얼마를 내는가. **함께 끈 차이가 하나씩 끈 차이의 합과 같은가** | **아직 안 돌렸다** — 질문과 가설과 판정 규칙을 먼저 적어 두었다(여섯 조건 x seed 셋). 논문이 자기 장치를 확인한 자리(CIFAR-10 네 층 망)를 그대로 쓴다 | [alexnet_2012](experiments/alexnet_2012/) |

---

## 주제 묶음

읽은 것이 쌓이면 여기에 주제별로 다시 묶는다. **묶음 이름은 미리 정하지 않는다** — 세 편이 같은 자리에 모이면 그때 이름을 붙인다.
