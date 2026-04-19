# EGI Backtester

EGI(Efficiency Growth Index) 지표를 활용한 파이썬 기반 주식 백테스팅 엔진입니다. 
기업의 주요 재무 데이터(영업이익, R&D 투자, 현금흐름, 판관비 등)를 바탕으로 '성장/손실 효율성 비율'을 수치화하고, 이 시그널 기반의 매매 전략이 벤치마크(S&P 500 등) 대비 유효한지 검증합니다.

## 시스템 구성

- `main.py`: 전체 분석 파이프라인 실행 스크립트
- `egi_calculator.py`: 종목별 재무 데이터 파싱 및 EGI 수치 계산
- `backtester.py`: EGI 시그널에 따른 모의 투자, 수익률 및 MDD 계산 로직
- `visualizer.py`: 성과 지표(Equity Curve) 차트 이미지 생성
- `dashboard/`: 로컬 환경에서 결과를 확인할 수 있는 정적 웹 페이지 (HTML/CSS/JS)

## 설치 및 세팅

```bash
pip install -r requirements.txt
```

## 실행 방법

기본 실행 (사전 정의된 전체 미국/한국 우량주 분석):
```bash
python main.py
```

종목을 직접 지정해서 돌려보고 싶다면 뒷부분에 티커명(Yahoo Finance 기준)을 붙여주세요:
```bash
python main.py AAPL TSLA MSFT
```

실행이 다 끝나면 폴더 안에 다음 결과물들이 자동으로 생성됩니다.
- `egi_analysis.png`
- `backtest_results.png`
- `results.json`

생성된 데이터는 `dashboard/index.html` 파일을 열어서 대시보드 형태로 쉽게 확인할 수 있습니다.
