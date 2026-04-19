"""
EGI 기반 백테스팅 엔진
========================
EGI 시그널을 기반으로 과거 주가 데이터를 활용하여 투자 전략을 시뮬레이션합니다.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from egi_calculator import EGICalculator
import warnings
warnings.filterwarnings('ignore')


class EGIBacktester:
    """EGI 기반 투자 전략 백테스팅 엔진"""

    def __init__(self, tickers: List[str], initial_capital: float = 100_000_000,
                 benchmark_ticker: str = '^GSPC'):
        self.tickers = tickers
        self.initial_capital = initial_capital
        self.benchmark_ticker = benchmark_ticker
        self.results = {}
        self.portfolio_history = []

    def run_backtest(self, start_date: str = '2019-01-01',
                     end_date: str = '2026-03-01') -> Dict:
        """전체 백테스트 실행"""
        print("\n" + "=" * 70)
        print("  🚀 EGI 백테스팅 시작")
        print(f"  기간: {start_date} ~ {end_date}")
        print(f"  초기 자본: ₩{self.initial_capital:,.0f}")
        print(f"  대상 종목: {len(self.tickers)}개")
        print("=" * 70)

        # 1. 모든 종목의 EGI 분석
        egi_results = {}
        valid_tickers = []
        for ticker in self.tickers:
            calc = EGICalculator(ticker)
            result = calc.generate_full_analysis()
            if result['success']:
                egi_results[ticker] = result
                valid_tickers.append(ticker)
                print(f"  ✅ {ticker}: EGI 분석 완료")
            else:
                print(f"  ❌ {ticker}: 분석 실패 - {result.get('error', '')}")

        if not valid_tickers:
            return {'success': False, 'error': '분석 가능한 종목이 없습니다.'}

        # 2. EGI 기반 종목 선정 및 가중치 결정
        portfolio = self._select_portfolio(egi_results, valid_tickers)
        print(f"\n  📌 포트폴리오 선정: {len(portfolio)}개 종목")
        for ticker, info in portfolio.items():
            print(f"     {ticker}: 가중치 {info['weight']:.1%}, 시그널={info['signal']}")

        # 3. 주가 데이터 수집 및 수익률 시뮬레이션
        performance = self._simulate_returns(portfolio, start_date, end_date)

        # 4. 벤치마크 비교
        benchmark = self._get_benchmark_returns(start_date, end_date)

        # 5. 성과 지표 계산
        metrics = self._calculate_metrics(performance, benchmark)

        # 6. 매매 내역 생성
        trades = self._generate_trades(portfolio, egi_results)

        self.results = {
            'success': True,
            'portfolio': portfolio,
            'performance': performance,
            'benchmark': benchmark,
            'metrics': metrics,
            'trades': trades,
            'egi_results': egi_results,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': self.initial_capital
        }

        self._print_results()
        return self.results

    def _select_portfolio(self, egi_results: Dict, valid_tickers: List[str]) -> Dict:
        """EGI 기반 포트폴리오 선정"""
        portfolio = {}
        scored_tickers = []

        for ticker in valid_tickers:
            result = egi_results[ticker]
            verdict = result['investment_verdict']
            signal = verdict['signal']
            score = verdict['score']
            latest_egi = result['threshold_result']['latest_egi']

            # 매수 시그널인 종목만 포트폴리오에 포함
            if signal in ['STRONG_BUY', 'BUY', 'MODERATE_BUY']:
                scored_tickers.append({
                    'ticker': ticker,
                    'score': score,
                    'egi': latest_egi,
                    'signal': signal,
                    'company_name': result['company_name']
                })

        # HOLD 시그널도 일부 포함 (분산 투자)
        if len(scored_tickers) < 3:
            for ticker in valid_tickers:
                result = egi_results[ticker]
                verdict = result['investment_verdict']
                if verdict['signal'] == 'HOLD' and ticker not in [s['ticker'] for s in scored_tickers]:
                    scored_tickers.append({
                        'ticker': ticker,
                        'score': verdict['score'],
                        'egi': result['threshold_result']['latest_egi'],
                        'signal': 'HOLD',
                        'company_name': result['company_name']
                    })

        if not scored_tickers:
            # 최소 상위 3개 종목 선택
            for ticker in valid_tickers[:3]:
                result = egi_results[ticker]
                scored_tickers.append({
                    'ticker': ticker,
                    'score': result['investment_verdict']['score'],
                    'egi': result['threshold_result']['latest_egi'],
                    'signal': result['investment_verdict']['signal'],
                    'company_name': result['company_name']
                })

        # 점수 기반 가중치 할당
        total_score = sum(s['score'] for s in scored_tickers) or 1
        for s in scored_tickers:
            portfolio[s['ticker']] = {
                'weight': max(s['score'] / total_score, 0.05),
                'score': s['score'],
                'egi': s['egi'],
                'signal': s['signal'],
                'company_name': s['company_name']
            }

        # 가중치 정규화
        total_weight = sum(v['weight'] for v in portfolio.values())
        for ticker in portfolio:
            portfolio[ticker]['weight'] /= total_weight

        return portfolio

    def _simulate_returns(self, portfolio: Dict,
                          start_date: str, end_date: str) -> pd.DataFrame:
        """주가 데이터 기반 수익률 시뮬레이션"""
        all_prices = {}

        for ticker in portfolio:
            try:
                data = yf.download(ticker, start=start_date, end=end_date,
                                   progress=False, auto_adjust=True)
                if not data.empty:
                    # 멀티인덱스 처리
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                    all_prices[ticker] = data['Close']
            except Exception as e:
                print(f"  ⚠️ {ticker} 주가 데이터 수집 실패: {e}")

        if not all_prices:
            return pd.DataFrame()

        # 모든 종목 가격 합치기
        prices_df = pd.DataFrame(all_prices).dropna()

        if prices_df.empty:
            return pd.DataFrame()

        # 일간 수익률
        daily_returns = prices_df.pct_change().dropna()

        # 포트폴리오 수익률 = 가중 평균
        weights = []
        valid_cols = []
        for ticker in daily_returns.columns:
            if ticker in portfolio:
                weights.append(portfolio[ticker]['weight'])
                valid_cols.append(ticker)

        if not valid_cols:
            return pd.DataFrame()

        weights = np.array(weights)
        weights = weights / weights.sum()  # 재정규화

        portfolio_return = (daily_returns[valid_cols] * weights).sum(axis=1)
        portfolio_value = self.initial_capital * (1 + portfolio_return).cumprod()

        result = pd.DataFrame({
            'Portfolio_Return': portfolio_return,
            'Portfolio_Value': portfolio_value
        })

        # 개별 종목 수익률도 추가
        for ticker in valid_cols:
            result[f'{ticker}_Return'] = daily_returns[ticker]

        return result

    def _get_benchmark_returns(self, start_date: str, end_date: str) -> pd.DataFrame:
        """벤치마크 수익률 가져오기"""
        try:
            bench = yf.download(self.benchmark_ticker, start=start_date,
                                end=end_date, progress=False, auto_adjust=True)
            if isinstance(bench.columns, pd.MultiIndex):
                bench.columns = bench.columns.get_level_values(0)
            bench_return = bench['Close'].pct_change().dropna()
            bench_value = self.initial_capital * (1 + bench_return).cumprod()
            return pd.DataFrame({
                'Benchmark_Return': bench_return,
                'Benchmark_Value': bench_value
            })
        except:
            return pd.DataFrame()

    def _calculate_metrics(self, performance: pd.DataFrame,
                           benchmark: pd.DataFrame) -> Dict:
        """성과 지표 산출"""
        if performance.empty:
            return {}

        returns = performance['Portfolio_Return'].dropna()
        if returns.empty:
            return {}

        trading_days = 252

        # 총 수익률
        total_return = (performance['Portfolio_Value'].iloc[-1] /
                        self.initial_capital - 1) * 100

        # CAGR
        n_years = len(returns) / trading_days
        if n_years > 0:
            cagr = ((performance['Portfolio_Value'].iloc[-1] /
                      self.initial_capital) ** (1 / n_years) - 1) * 100
        else:
            cagr = 0

        # 연간 변동성
        volatility = returns.std() * np.sqrt(trading_days) * 100

        # 샤프비율 (무위험 이자율 3% 가정)
        rf_daily = 0.03 / trading_days
        excess_return = returns.mean() - rf_daily
        sharpe = (excess_return / returns.std()) * np.sqrt(trading_days) if returns.std() > 0 else 0

        # 소르티노비율
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else returns.std()
        sortino = (excess_return / downside_std) * np.sqrt(trading_days) if downside_std > 0 else 0

        # MDD (최대 낙폭)
        portfolio_values = performance['Portfolio_Value']
        running_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - running_max) / running_max * 100
        mdd = drawdown.min()

        # 승률
        win_rate = (returns > 0).sum() / len(returns) * 100

        # 평균 수익/손실
        avg_gain = returns[returns > 0].mean() * 100 if (returns > 0).any() else 0
        avg_loss = returns[returns < 0].mean() * 100 if (returns < 0).any() else 0

        # 벤치마크 비교
        bench_total_return = 0
        bench_cagr = 0
        alpha = 0
        if not benchmark.empty and 'Benchmark_Value' in benchmark.columns:
            bench_total_return = (benchmark['Benchmark_Value'].iloc[-1] /
                                  self.initial_capital - 1) * 100
            if n_years > 0:
                bench_cagr = ((benchmark['Benchmark_Value'].iloc[-1] /
                               self.initial_capital) ** (1 / n_years) - 1) * 100
            alpha = cagr - bench_cagr

        metrics = {
            'total_return': round(total_return, 2),
            'cagr': round(cagr, 2),
            'volatility': round(volatility, 2),
            'sharpe_ratio': round(sharpe, 4),
            'sortino_ratio': round(sortino, 4),
            'mdd': round(mdd, 2),
            'win_rate': round(win_rate, 2),
            'avg_gain': round(avg_gain, 4),
            'avg_loss': round(avg_loss, 4),
            'final_value': round(performance['Portfolio_Value'].iloc[-1], 0),
            'benchmark_total_return': round(bench_total_return, 2),
            'benchmark_cagr': round(bench_cagr, 2),
            'alpha': round(alpha, 2),
            'n_years': round(n_years, 2),
            'trading_days': len(returns)
        }
        return metrics

    def _generate_trades(self, portfolio: Dict, egi_results: Dict) -> List[Dict]:
        """매매 내역 생성"""
        trades = []
        for ticker, info in portfolio.items():
            if ticker in egi_results:
                egi_data = egi_results[ticker]['egi_data']
                for _, row in egi_data.iterrows():
                    egi_val = row['EGI']
                    if egi_val >= 150:
                        action = 'STRONG_BUY'
                    elif egi_val >= 120:
                        action = 'BUY'
                    elif egi_val >= 100:
                        action = 'HOLD'
                    elif egi_val >= 80:
                        action = 'SELL'
                    else:
                        action = 'STRONG_SELL'

                    trades.append({
                        'ticker': ticker,
                        'company_name': info.get('company_name', ticker),
                        'year': int(row['Year']),
                        'egi': round(egi_val, 2),
                        'action': action,
                        'weight': round(info['weight'], 4)
                    })

        return sorted(trades, key=lambda x: (x['year'], x['ticker']))

    def _print_results(self):
        """백테스팅 결과 출력"""
        m = self.results.get('metrics', {})
        if not m:
            print("\n  ⚠️ 성과 결과가 없습니다.")
            return

        print(f"\n{'='*70}")
        print("  📈 백테스팅 결과")
        print(f"{'='*70}")
        print(f"  총 수익률:        {m['total_return']:>+10.2f}%")
        print(f"  CAGR:             {m['cagr']:>+10.2f}%")
        print(f"  연간 변동성:      {m['volatility']:>10.2f}%")
        print(f"  샤프비율:         {m['sharpe_ratio']:>10.4f}")
        print(f"  소르티노비율:     {m['sortino_ratio']:>10.4f}")
        print(f"  최대 낙폭(MDD):   {m['mdd']:>10.2f}%")
        print(f"  승률:             {m['win_rate']:>10.2f}%")
        print(f"  최종 자산:        ₩{m['final_value']:>14,.0f}")
        print(f"{'─'*70}")
        print(f"  벤치마크 수익률:  {m['benchmark_total_return']:>+10.2f}%")
        print(f"  벤치마크 CAGR:    {m['benchmark_cagr']:>+10.2f}%")
        print(f"  Alpha (초과):     {m['alpha']:>+10.2f}%")
        print(f"{'='*70}")
