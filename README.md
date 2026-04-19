# EGI Investment Backtesting System

EGI(Efficiency Growth Index)는 기업의 성장 효율성을 정량적으로 평가하기 위해 고안된 자체 지표입니다. 이 프로젝트는 개별 기업의 재무제표 데이터를 수집해 EGI를 산출하고, 추세(Slope)와 가속도(Acceleration) 분석을 거쳐 시그널을 생성한 뒤 과거 데이터를 통해 백테스팅하는 전체 파이프라인을 구현합니다.

## EGI 산출 논리

EGI는 수익 대비 비용뿐만 아니라 미래 성장 가치와 리스크를 종합적으로 반영하기 위해 다음과 같이 정의됩니다.

**EGI = (Total Gain / Total Loss) * 100**

*   **Total Gain (성장/이익 여력)**
    *   영업이익 (Operating Income)
    *   R&D 투자액: 당장의 비용 처리되나 장기 성장 동력으로 판단하여 Gain 연산에 포함
    *   현금성 자산 증가분: 기업의 실제 가용 유동성 증가분
*   **Total Loss (비효율/비용 요인)**
    *   판관비 (SG&A)
    *   재고 자산 감소/손실분
    *   영업외 비용

EGI 수치가 100 미만일 경우 투입 비용 및 발생 리스크가 실질적 이익을 초과하는 상태로 평가하며, 150 이상일 경우 매우 높은 운영 효율을 보여주는 것으로 평가합니다.

## 시스템 아키텍처

파이프라인은 데이터 수집부터 프론트엔드 연동까지 4가지 주요 모듈로 나뉩니다.

### 1. `src/egi_calculator.py` (지표 산출 및 리스크 분석)
`yfinance`를 활용해 재무 상태표, 손익계산서, 현금흐름표를 파싱합니다.
*   **추세 분석(Slope Analysis)**: 다년간의 EGI 데이터를 `scipy.stats.linregress`로 분석하여 추세의 기울기(Slope)와 R² 신뢰도를 산출합니다.
*   **가속도 연산(Acceleration)**: EGI 수치 변화량의 2차 미분(도함수 근사치)을 계산하여 성장세의 가속 여부를 판단합니다.
*   **리스크 스크리닝**: SG&A가 전년비 15% 이상 급증하거나, R&D 대비 영업이익 능력이 낮을 경우 점수 페널티를 부여합니다.
*   **스코어링 로직**: 위 데이터들을 조합하여 0~100 사이의 팩터 스코어를 계산하고, `STRONG_BUY`에서 `STRONG_SELL`까지의 개별 시그널을 생성합니다.

### 2. `src/backtester.py` (시계열 백테스팅)
*   **포트폴리오 시뮬레이션**: 산출된 스코어를 기반으로 초기 자본금 대비 종목별 자산 가중치(Weight)를 동적으로 할당합니다.
*   **벤치마크 마크다운**: S&P 500(`^GSPC`) 인덱스 수익률을 병렬로 연산합니다.
*   **메트릭 산출**: 누적 수익률, 연평균 성장률(CAGR), Sharpe Ratio, Sortino Ratio, 최대 낙폭(MDD), Alpha 수치를 계산해 모델의 타당성을 평가합니다.

### 3. `src/visualizer.py` (정적 시각화)
*   `matplotlib`을 사용하여 EGI 추이 및 누적 자산 곡선(Equity Curve)를 `results/` 경로 내에 PNG 형태로 저장합니다.

### 4. `dashboard/` (결과 모니터링 프론트엔드)
*   전체 파이프라인 엔진이 종료될 때 내뱉는 `results.json` 파라미터 파일과 연동됩니다.
*   순수 HTML/JS 구조로 구성되어 있으며, 로컬 환경에서 시그널 및 매매 히스토리를 차트로 확인할 수 있습니다.

## 실행 가이드

환경 구축:
```bash
pip install -r requirements.txt
```

전체 백테스팅 파이프라인 구동:
```bash
# 기본 세팅된 종목 대상으로 분석
python main.py

# 특정 티커(Ticker) 대상 개별 분석
python main.py AAPL TSLA
```

구동 후 `results` 폴더에 분석 로그와 시각화 파일들이 생성되며, `dashboard/index.html` 파일을 열어 대시보드를 확인할 수 있습니다.

## 디렉토리 구조

```
c:\stock
├── src/
│   ├── egi_calculator.py   # EGI 지표 및 파생 데이터 산출
│   ├── backtester.py       # 과거 데이터 기반 모의 매매 및 메트릭 산출
│   └── visualizer.py       # 차트 생성 툴
├── results/                # 런타임에 동적 생성되는 산출물 저장소 (.png, .json)
├── dashboard/              # 로컬 모니터링용 웹 페이지
├── portfolio/              # 전체 프로젝트 포트폴리오 웹뷰
├── main.py                 # 백엔드 엔진 엔트리 포인트
└── requirements.txt
```
