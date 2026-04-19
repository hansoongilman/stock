# 📈 EGI Investment Analysis System

**Efficiency Growth Index (EGI) 기반 주식 분석 및 백테스팅 자동화 엔진**

단순한 과거 가격 모멘텀이나 전통적인 보조지표(PER, PBR 등)에 의존하는 대신, **기업 고유의 재무적 '성장 효율성'을 정량화하여 측정**하고 이를 바탕으로 한 투자 신호가 실제 시장(S&P 500) 대비 초과 수익을 달성할 수 있는지 검증하기 위해 개발된 파이썬 분석 파이프라인입니다.

---

## 🎯 설계 철학 및 핵심 개념 (Core Concept)

투자의 본질은 "기업이 벌어들인 이득(Gain)이 발생한 손실 및 비용(Loss)을 얼마나 효율적으로 상회하는가?"에 있습니다. 이 구조를 포착하기 위해 자체 지표인 **EGI(Efficiency Growth Index)**를 고안했습니다.

### 💡 EGI 산출 공식
> **EGI = (Total Gain / Total Loss) × 100**

단순 매출이나 순이익이 아닌, 미래 성장을 위한 투자와 불필요한 현금 유출을 세분화하여 다음과 같이 정의했습니다.

1. **Total Gain (성장 요인)**
   - `영업이익 (Operating Income)`: 핵심 비즈니스의 수익성
   - `R&D 투자액 (R&D Expenses)`: 단순 비용이 아닌 미래 가치를 위한 필수 성장 동력으로 간주하여 Gain으로 편입 (절대값 처리)
   - `현금성 자산 증가분`: 위기 대응 능력 및 실제 현금 창출력

2. **Total Loss (손실 및 비효율 요인)**
   - `판매비와 관리비 (SG&A)`: 매출 원가 외의 판관비 부담
   - `재고 자산 손실`: 재고 감가상각 및 악성 재고 증가분
   - `영업외 비용`: 이자 비용 및 영업 규모 외의 자본 유출

3. **EGI 분석의 의의**: EGI가 100% 미만이면 벌어들이는 요인보다 소모하는 비용과 리스크가 더 크다는 것을 의미하며, EGI가 150% 이상이면 압도적인 성장 효율성을 달성하고 있음을 뜻합니다.

---

## ⚙️ 주요 기능 및 아키텍처 (Key Features)

시스템은 `데이터 수집 -> EGI 분석 -> 백테스팅 -> 시각화 대시보드` 4단계의 파이프라인으로 매끄럽게 연결되어 있습니다.

### 1. 트렌드 및 가속도 분석 모듈 (`src/egi_calculator.py`)
- **선형 회귀 (Linear Regression)**: 다년간의 EGI 변화량에 대해 `scipy.stats`를 이용해 기울기(Slope)와 R² 값을 도출하여 추세의 신뢰도를 판별합니다.
- **가속도 산출 (Acceleration)**: EGI 수치의 2차 미분(도함수 근사치)을 계산하여 성장이 '가속' 상태인지 '둔화' 상태인지 판단합니다.
- **리스크 감지 (Risk Check)**: 판관비(SGA)가 15% 이상 급증하거나, R&D 대비 영업이익 능력이 현저히 낮아질 경우 감점 로직이 발동합니다.
- **스코어링 시스템**: 위 데이터를 종합하여 최종 평가 점수(최대 100점) 및 투자 등급(`STRONG_BUY`, `HOLD`, `STRONG_SELL` 등)을 산출합니다.

### 2. 성과 검증 백테스터 (`src/backtester.py`)
- **시계열 시뮬레이션**: 산출된 EGI 시그널을 바탕으로 과거 주가 데이터(Yahoo Finance)와 결합하여 매매 로직을 실행하는 모의 투자 엔진입니다.
- **동적 가중치 배분**: 평가 점수(Score)에 비례하여 포트폴리오 비중(Weight)을 동적으로 조절합니다.
- **벤치마크 비교**: S&P 500(`^GSPC`) 인덱스를 벤치마크로 삼고, [총 수익률, CAGR, 샤프 비율(Sharpe Ratio), 소르티노 비율(Sortino Ratio), 최대 낙폭(MDD), Alpha] 등 전문 퀀트 펀드에서 활용하는 성과 측정 지표를 모두 출력하여 전략의 객관성을 입증합니다.

### 3. 인터랙티브 대시보드 (`dashboard/` 폴더)
분석이 끝나면 로컬 환경에서 즉시 브라우저를 통해 결과를 구경할 수 있는 모던 웹 대시보드를 제공합니다.
- EGI 포트폴리오 vs S&P 500 **자산 곡선(Equity Curve) 비교 차트**
- 기업별 EGI 트렌드 미니 바 차트 및 투자 적격성 상세 판정 내역
- 매매 시그널(Trade History) 로그 조회 기능

---

## 🚀 시작하기 (Getting Started)

### 사전 준비물
- Python 3.10+ 권장
- 의존성 패키지 설치: `yfinance`, `pandas`, `numpy`, `scipy`, `matplotlib` 등

```bash
# 필수 라이브러리 설치
pip install -r requirements.txt
```

### 파이프라인 실행

```bash
# 전체 파이프라인 실행 (Apple, MSFT, Google 등 기본 우량주 풀 자동 분석)
python main.py

# 알고 싶은 특정 종목만 분석할 때 (Yahoo Finance Ticker 기준)
python main.py AAPL TSLA NVDA
```

실행이 완료되면 루트의 `results/` 폴더 내에 시각화된 차트와 `results.json`이 자동 생성됩니다.

### 대시보드 확인
분석이 끝난 후, 탐색기에서 `dashboard/index.html` 파일을 더블클릭하여 웹 브라우저로 띄우거나 아래와 같이 로컬 서버를 열면 화려하게 시각화된 리포트를 보실 수 있습니다.

```bash
python -m http.server 8000
# http://localhost:8000/dashboard/ 로 접속
```

---

## 📁 저장소 구조 (Directory Structure)

```text
c:\stock\
 ┣ 📂 src/
 ┃ ┣ 📜 egi_calculator.py   # 재무제표 파싱, EGI 스코어링 및 가속도/리스크 판별
 ┃ ┣ 📜 backtester.py       # EGI 시그널 기반 시계열 매매 시뮬레이tus
 ┃ ┗ 📜 visualizer.py       # 렌더링용 기본 정적 차트(Matplotlib) 생성
 ┣ 📂 results/              # 파이프라인 구동 시 자동 생성되는 아웃풋 폴더 (.png, .json)
 ┣ 📂 dashboard/            # results.json을 소비하여 웹에 그려주는 프론트엔드 (HTML/JS)
 ┣ 📂 portfolio/            # 개발자의 전체 깃허브 프로젝트를 전시하는 포트폴리오 웹앱 
 ┣ 📜 main.py               # 백엔드 엔진 실행 진입점 (Entry Point)
 ┣ 📜 requirements.txt
 ┗ 📜 README.md
```

---

> 이 저장소는 학술적 분석과 프로그래밍 능력을 증명하기 위해 고안된 프로젝트로, 이곳에서 제공하는 시그널과 데이터는 실제 투자에 대한 법적 권유나 보장을 의미하지 않습니다. 시스템 구조화 파악 및 코딩 포트폴리오 검토 목적으로 자유롭게 참고해 주시기 바랍니다.
