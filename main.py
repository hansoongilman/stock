"""
EGI 기반 투자 프로그램 - 메인 실행 파일
==========================================
다양한 기업의 EGI(Efficiency Growth Index)를 분석하고
백테스팅을 통해 투자 전략의 유효성을 검증합니다.
"""

import json
import os
import sys
import io
from datetime import datetime

# Windows 콘솔 UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.egi_calculator import EGICalculator, analyze_multiple_companies
from src.backtester import EGIBacktester
from src.visualizer import create_egi_analysis_chart, create_backtest_chart


# ============================================
#  분석 대상 기업 목록
# ============================================
ANALYSIS_TICKERS = {
    # 미국 대형 기술주
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'GOOGL': 'Alphabet (Google)',
    'AMZN': 'Amazon',
    'TSLA': 'Tesla',
    'NVDA': 'NVIDIA',
    'META': 'Meta Platforms',
    # 미국 기타 대형주
    'JPM': 'JPMorgan Chase',
    'JNJ': 'Johnson & Johnson',
    'V': 'Visa',
    # 한국 대형주
    '005930.KS': 'Samsung',
    '000660.KS': 'SK Hynix',
    '035420.KS': 'NAVER',
}


def run_full_pipeline(tickers: list = None, start_date: str = '2019-01-01',
                      end_date: str = '2026-03-01',
                      initial_capital: float = 100_000_000):
    """전체 파이프라인 실행"""
    if tickers is None:
        tickers = list(ANALYSIS_TICKERS.keys())

    output_dir = 'c:/stock/results'
    os.makedirs(output_dir, exist_ok=True)

    print("+" + "=" * 65 + "+")
    print("|   EGI (Efficiency Growth Index) Investment Analysis System     |")
    print("|   Total Gain / Total Loss x 100 -> Growth Rate Strategy       |")
    print("+" + "=" * 65 + "+")
    print(f"\n  [DATE]    Analysis Period: {start_date} ~ {end_date}")
    print(f"  [CAPITAL] Initial: {initial_capital:,.0f} KRW")
    print(f"  [TARGET]  Companies: {len(tickers)}")
    print(f"  [TIME]    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # =========== STEP 1: EGI Analysis ===========
    print("\n" + "#" * 70)
    print("  STEP 1: Running EGI analysis for all companies...")
    print("#" * 70)

    egi_results = analyze_multiple_companies(tickers)

    # =========== STEP 2: EGI Charts ===========
    print("\n" + "#" * 70)
    print("  STEP 2: Generating EGI analysis charts...")
    print("#" * 70)

    create_egi_analysis_chart(egi_results,
                              save_path=os.path.join(output_dir, 'egi_analysis.png'))

    # =========== STEP 3: Backtesting ===========
    print("\n" + "#" * 70)
    print("  STEP 3: Running EGI-based backtesting...")
    print("#" * 70)

    backtester = EGIBacktester(
        tickers=tickers,
        initial_capital=initial_capital,
        benchmark_ticker='^GSPC'
    )
    backtest_results = backtester.run_backtest(
        start_date=start_date,
        end_date=end_date
    )

    # =========== STEP 4: Backtest Charts ===========
    print("\n" + "#" * 70)
    print("  STEP 4: Generating backtest result charts...")
    print("#" * 70)

    create_backtest_chart(backtest_results,
                          save_path=os.path.join(output_dir, 'backtest_results.png'))

    # =========== STEP 5: JSON Export ===========
    print("\n" + "#" * 70)
    print("  STEP 5: Exporting results to JSON...")
    print("#" * 70)

    export_data = export_results_json(egi_results, backtest_results, output_dir)

    # =========== Final Summary ===========
    print("\n" + "=" * 70)
    print("  [DONE] Analysis Complete!")
    print("=" * 70)
    print(f"\n  Generated files:")
    print(f"     -> {output_dir}/egi_analysis.png     (EGI Analysis Chart)")
    print(f"     -> {output_dir}/backtest_results.png (Backtest Result Chart)")
    print(f"     -> {output_dir}/results.json         (JSON Data)")
    print(f"     -> {output_dir}/dashboard/index.html (Web Dashboard)")
    print(f"\n  Open the web dashboard:")
    print(f"     -> Open {output_dir}/dashboard/index.html in your browser.")

    return egi_results, backtest_results


def export_results_json(egi_results: list, backtest_results: dict,
                        output_dir: str) -> dict:
    """결과를 JSON으로 내보내기 (대시보드용)"""
    export = {
        'generated_at': datetime.now().isoformat(),
        'companies': [],
        'backtest': {},
        'portfolio': {},
        'trades': []
    }

    # EGI 분석 결과
    for result in egi_results:
        if not result.get('success'):
            continue

        company_data = {
            'ticker': result['ticker'],
            'company_name': result['company_name'],
            'egi_data': [],
            'slope_analysis': result['slope_analysis'],
            'threshold_result': {
                'signal': result['threshold_result']['signal'],
                'latest_egi': result['threshold_result']['latest_egi'],
                'details': result['threshold_result']['details']
            },
            'risk_factors': result['risk_factors'],
            'investment_verdict': result['investment_verdict']
        }

        for _, row in result['egi_data'].iterrows():
            company_data['egi_data'].append({
                'year': int(row['Year']),
                'operating_income': float(row['Operating_Income']),
                'rnd_investment': float(row['RnD_Investment']),
                'cash_change': float(row['Cash_Change']),
                'total_gain': float(row['Total_Gain']),
                'sga': float(row['SGA']),
                'inventory_loss': float(row['Inventory_Loss']),
                'non_operating_expense': float(row['Non_Operating_Expense']),
                'total_loss': float(row['Total_Loss']),
                'egi': float(row['EGI'])
            })

        export['companies'].append(company_data)

    # 백테스팅 결과
    if backtest_results.get('success'):
        export['backtest'] = backtest_results.get('metrics', {})

        portfolio = backtest_results.get('portfolio', {})
        export['portfolio'] = {
            t: {
                'weight': info['weight'],
                'score': info['score'],
                'egi': info['egi'],
                'signal': info['signal'],
                'company_name': info.get('company_name', t)
            } for t, info in portfolio.items()
        }

        export['trades'] = backtest_results.get('trades', [])

        # 자산 곡선 데이터 (샘플링)
        perf = backtest_results.get('performance')
        if perf is not None and not perf.empty and 'Portfolio_Value' in perf.columns:
            # 주 단위 샘플링
            weekly = perf['Portfolio_Value'].resample('W').last().dropna()
            export['equity_curve'] = [
                {'date': d.strftime('%Y-%m-%d'), 'value': float(v)}
                for d, v in weekly.items()
            ]

        bench = backtest_results.get('benchmark')
        if bench is not None and not bench.empty and 'Benchmark_Value' in bench.columns:
            weekly_bench = bench['Benchmark_Value'].resample('W').last().dropna()
            export['benchmark_curve'] = [
                {'date': d.strftime('%Y-%m-%d'), 'value': float(v)}
                for d, v in weekly_bench.items()
            ]

    json_path = os.path.join(output_dir, 'results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(export, f, ensure_ascii=False, indent=2, default=str)

    print(f"  💾 JSON 데이터 저장: {json_path}")
    return export


if __name__ == '__main__':
    # 커맨드라인 인수로 특정 기업만 분석 가능
    if len(sys.argv) > 1:
        custom_tickers = sys.argv[1:]
        print(f"\n  🎯 사용자 지정 종목: {custom_tickers}")
        run_full_pipeline(tickers=custom_tickers)
    else:
        run_full_pipeline()
