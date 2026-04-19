"""
EGI (Efficiency Growth Index) Calculator
=========================================
EGI = (Total Gain / Total Loss) × 100

Total Gain = 영업이익(Operating Income) + R&D 투자액 + 현금성 자산 증가분
Total Loss = 판매비와 관리비(SGA) + 재고 자산 손실 + 영업외 비용(Non-Operating Expenses)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Optional, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class EGICalculator:
    """기업의 EGI(Efficiency Growth Index)를 계산하고 분석하는 클래스"""

    # EGI 임계값
    STRONG_SIGNAL_THRESHOLD = 150.0   # 강력한 성장 시그널
    MODERATE_SIGNAL_THRESHOLD = 120.0  # 보통 성장 시그널
    DANGER_THRESHOLD = 80.0            # 위험 구간

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)
        self.company_name = self._get_company_name()
        self.egi_data = None
        self.analysis_result = None

    def _get_company_name(self) -> str:
        """기업 이름 가져오기"""
        try:
            info = self.stock.info
            return info.get('longName', info.get('shortName', self.ticker))
        except:
            return self.ticker

    def _safe_get(self, df: pd.DataFrame, keys: list, default=0) -> pd.Series:
        """재무제표에서 안전하게 항목 추출 (여러 키 시도)"""
        if df is None or df.empty:
            return pd.Series(dtype=float)
        for key in keys:
            if key in df.index:
                return df.loc[key].fillna(0)
        return pd.Series([default] * len(df.columns), index=df.columns)

    def fetch_financial_data(self) -> Dict:
        """재무제표 데이터 수집 및 EGI 계산에 필요한 항목 추출"""
        try:
            # 연간 재무제표 수집
            income_stmt = self.stock.financials  # Income Statement
            balance_sheet = self.stock.balance_sheet  # Balance Sheet
            cashflow = self.stock.cashflow  # Cash Flow Statement

            if income_stmt is None or income_stmt.empty:
                raise ValueError(f"{self.ticker}: 재무제표 데이터를 찾을 수 없습니다.")

            # ========== Total Gain 구성 요소 ==========
            # 1) 영업이익 (Operating Income)
            operating_income = self._safe_get(income_stmt, [
                'Operating Income', 'EBIT', 'Operating Profit'
            ])

            # 2) R&D 투자액 (Research & Development)
            rnd_expense = self._safe_get(income_stmt, [
                'Research Development', 'Research And Development',
                'Research & Development', 'R&D Expenses'
            ])
            # R&D는 비용이지만, 미래 성장 투자로 간주하여 Gain에 포함
            rnd_expense = rnd_expense.abs()

            # 3) 현금성 자산 증가분
            cash_assets = self._safe_get(balance_sheet, [
                'Cash And Cash Equivalents', 'Cash',
                'Cash Cash Equivalents And Short Term Investments',
                'Cash Equivalents', 'Cash Financial'
            ])
            # 현금 증가분 계산 (현재 - 이전)
            cash_change = cash_assets.diff(-1).fillna(0)  # 증가분 (최신→이전 순이므로 -1)
            cash_change = cash_change.clip(lower=0)  # 증가분만 (양수만)

            # ========== Total Loss 구성 요소 ==========
            # 1) 판매비와 관리비 (SGA)
            sga = self._safe_get(income_stmt, [
                'Selling General And Administration',
                'Selling General Administrative',
                'General And Administrative Expense',
                'SGA', 'Operating Expense'
            ]).abs()

            # 2) 재고 자산 손실 (Inventory 감소분 또는 write-down)
            inventory = self._safe_get(balance_sheet, [
                'Inventory', 'Net Inventory', 'Inventories'
            ])
            inventory_loss = inventory.diff(-1).fillna(0)
            inventory_loss = inventory_loss.clip(upper=0).abs()  # 감소분 = 손실

            # 3) 영업외 비용 (Non-Operating Expenses)
            total_revenue = self._safe_get(income_stmt, [
                'Total Revenue', 'Revenue', 'Net Sales'
            ])
            gross_profit = self._safe_get(income_stmt, [
                'Gross Profit'
            ])
            # 영업외 비용 계산 (간접 추정)
            interest_expense = self._safe_get(income_stmt, [
                'Interest Expense', 'Interest Expense Non Operating',
                'Net Interest Income'
            ]).abs()
            other_expense = self._safe_get(income_stmt, [
                'Other Non Operating Income Expenses',
                'Other Income Expense', 'Other Expenses'
            ])
            other_expense_neg = other_expense.clip(upper=0).abs()

            non_operating_expense = interest_expense + other_expense_neg

            # ========== EGI 계산 ==========
            total_gain = operating_income + rnd_expense + cash_change
            total_loss = sga + inventory_loss + non_operating_expense

            # 0 방지
            total_loss = total_loss.replace(0, np.nan)

            egi = (total_gain / total_loss) * 100

            # DataFrame으로 정리
            years = pd.to_datetime(income_stmt.columns).year
            result_df = pd.DataFrame({
                'Year': years,
                'Operating_Income': operating_income.values,
                'RnD_Investment': rnd_expense.values,
                'Cash_Change': cash_change.values,
                'Total_Gain': total_gain.values,
                'SGA': sga.values,
                'Inventory_Loss': inventory_loss.values,
                'Non_Operating_Expense': non_operating_expense.values,
                'Total_Loss': total_loss.values,
                'EGI': egi.values
            }).sort_values('Year').reset_index(drop=True)

            # NaN 행 제거
            result_df = result_df.dropna(subset=['EGI'])

            self.egi_data = result_df
            return {
                'ticker': self.ticker,
                'company_name': self.company_name,
                'egi_data': result_df,
                'success': True
            }

        except Exception as e:
            return {
                'ticker': self.ticker,
                'company_name': self.company_name,
                'error': str(e),
                'success': False
            }

    def analyze_slope(self) -> Dict:
        """EGI 추세의 기울기(Slope) 및 가속도 분석"""
        if self.egi_data is None or len(self.egi_data) < 2:
            return {'slope': 0, 'acceleration': 0, 'trend': 'insufficient_data'}

        df = self.egi_data
        years = df['Year'].values.astype(float)
        egi_values = df['EGI'].values

        # 선형 회귀로 기울기 계산
        slope, intercept, r_value, p_value, std_err = stats.linregress(years, egi_values)

        # 가속도 (2차 미분 근사) - EGI 변화율의 변화
        if len(egi_values) >= 3:
            diffs = np.diff(egi_values)
            acceleration = np.mean(np.diff(diffs))
        else:
            acceleration = 0

        # 추세 판단
        if slope > 5 and acceleration > 0:
            trend = 'accelerating_growth'  # 가속 성장
        elif slope > 2:
            trend = 'steady_growth'  # 안정 성장
        elif slope > -2:
            trend = 'stagnant'  # 정체
        elif slope > -5:
            trend = 'declining'  # 하락
        else:
            trend = 'sharp_decline'  # 급격한 하락

        return {
            'slope': round(slope, 4),
            'intercept': round(intercept, 4),
            'r_squared': round(r_value ** 2, 4),
            'p_value': round(p_value, 4),
            'acceleration': round(acceleration, 4),
            'trend': trend,
            'std_err': round(std_err, 4)
        }

    def check_threshold(self) -> Dict:
        """임계점 판단 - EGI가 150%를 넘으며 가속도가 붙는지"""
        if self.egi_data is None or self.egi_data.empty:
            return {'signal': 'no_data', 'details': '데이터 불충분'}

        latest_egi = self.egi_data.iloc[-1]['EGI']
        slope_analysis = self.analyze_slope()

        signals = []

        # 임계값 체크
        if latest_egi >= self.STRONG_SIGNAL_THRESHOLD:
            if slope_analysis['acceleration'] > 0:
                signal = 'STRONG_BUY'
                signals.append(f"🟢 EGI {latest_egi:.1f}% > 150% + 가속도 양수 → 강력한 성장 시그널")
            else:
                signal = 'BUY'
                signals.append(f"🔵 EGI {latest_egi:.1f}% > 150% 하지만 가속도 감소 → 신중한 매수")
        elif latest_egi >= self.MODERATE_SIGNAL_THRESHOLD:
            if slope_analysis['slope'] > 0:
                signal = 'MODERATE_BUY'
                signals.append(f"🟡 EGI {latest_egi:.1f}% > 120% + 상승 추세 → 보통 매수 시그널")
            else:
                signal = 'HOLD'
                signals.append(f"⚪ EGI {latest_egi:.1f}% > 120% 하지만 하락 추세 → 관망")
        elif latest_egi >= 100:
            signal = 'HOLD'
            signals.append(f"⚪ EGI {latest_egi:.1f}% 이익 상태지만 강한 신호 아님 → 관망")
        elif latest_egi >= self.DANGER_THRESHOLD:
            signal = 'SELL'
            signals.append(f"🟠 EGI {latest_egi:.1f}% < 100% 비효율 경고 → 매도 추천")
        else:
            signal = 'STRONG_SELL'
            signals.append(f"🔴 EGI {latest_egi:.1f}% < 80% 심각한 비효율 → 강력 매도")

        return {
            'signal': signal,
            'latest_egi': round(latest_egi, 2),
            'details': signals,
            'slope': slope_analysis
        }

    def check_risk(self) -> List[str]:
        """리스크 체크 - 분모(비용)의 통제 여부 검증"""
        risks = []
        if self.egi_data is None or len(self.egi_data) < 2:
            return ['데이터 부족으로 리스크 분석 불가']

        df = self.egi_data

        # 1. SGA 증가율 체크
        sga_growth = df['SGA'].pct_change().dropna()
        if len(sga_growth) > 0 and sga_growth.iloc[-1] > 0.15:
            risks.append(f"⚠️ 판매비/관리비 급증 ({sga_growth.iloc[-1]*100:.1f}% 증가) - 비용 통제 실패 가능성")

        # 2. Total Loss 추이 체크
        loss_growth = df['Total_Loss'].pct_change().dropna()
        if len(loss_growth) > 0 and loss_growth.iloc[-1] > 0.20:
            risks.append(f"⚠️ 총 비용 급증 ({loss_growth.iloc[-1]*100:.1f}% 증가) - 지표 불안정 위험")

        # 3. EGI 변동성 체크
        if len(df['EGI']) >= 3:
            egi_std = df['EGI'].std()
            egi_mean = df['EGI'].mean()
            cv = (egi_std / abs(egi_mean)) * 100 if egi_mean != 0 else 0
            if cv > 30:
                risks.append(f"⚠️ EGI 변동성 높음 (변이계수 {cv:.1f}%) - 안정적 성장 불확실")

        # 4. 영업이익 마이너스 체크
        if df['Operating_Income'].iloc[-1] < 0:
            risks.append("🔴 최근 영업이익 적자 - 핵심 사업 수익성 문제")

        # 5. R&D 대비 영업이익 비율 체크
        if df['RnD_Investment'].iloc[-1] > 0:
            roi_ratio = df['Operating_Income'].iloc[-1] / df['RnD_Investment'].iloc[-1]
            if roi_ratio < 0.5:
                risks.append(f"⚠️ R&D 투자 대비 영업이익 낮음 (비율: {roi_ratio:.2f}) - R&D 효율성 의문")

        # 6. 재고 손실 증가 체크
        if len(df) >= 2 and df['Inventory_Loss'].iloc[-1] > df['Inventory_Loss'].iloc[-2] * 1.5:
            risks.append("⚠️ 재고 자산 손실 급증 - 재고 관리 리스크")

        if not risks:
            risks.append("✅ 주요 리스크 요인 감지되지 않음")

        return risks

    def generate_full_analysis(self) -> Dict:
        """전체 분석 수행 (데이터 수집 + EGI 계산 + 기울기 분석 + 임계점 + 리스크)"""
        # 1. 데이터 수집 및 EGI 계산
        fetch_result = self.fetch_financial_data()
        if not fetch_result['success']:
            return fetch_result

        # 2. 기울기 분석
        slope_analysis = self.analyze_slope()

        # 3. 임계점 판단
        threshold_result = self.check_threshold()

        # 4. 리스크 체크
        risk_factors = self.check_risk()

        # 5. 최종 투자 적격성 판단
        investment_verdict = self._generate_verdict(
            threshold_result, slope_analysis, risk_factors
        )

        self.analysis_result = {
            'ticker': self.ticker,
            'company_name': self.company_name,
            'egi_data': self.egi_data,
            'slope_analysis': slope_analysis,
            'threshold_result': threshold_result,
            'risk_factors': risk_factors,
            'investment_verdict': investment_verdict,
            'success': True
        }
        return self.analysis_result

    def _generate_verdict(self, threshold: Dict, slope: Dict, risks: List[str]) -> Dict:
        """최종 투자 적격성 판단"""
        score = 0
        reasons = []

        # EGI 절대값 점수 (0-30점)
        latest_egi = threshold['latest_egi']
        if latest_egi >= 200:
            score += 30
            reasons.append(f"EGI {latest_egi:.1f}% - 매우 높은 효율성")
        elif latest_egi >= 150:
            score += 25
            reasons.append(f"EGI {latest_egi:.1f}% - 높은 효율성")
        elif latest_egi >= 120:
            score += 18
            reasons.append(f"EGI {latest_egi:.1f}% - 양호한 효율성")
        elif latest_egi >= 100:
            score += 10
            reasons.append(f"EGI {latest_egi:.1f}% - 경계선 효율성")
        else:
            score += 0
            reasons.append(f"EGI {latest_egi:.1f}% - 비효율 상태")

        # 추세 점수 (0-30점)
        trend_scores = {
            'accelerating_growth': 30,
            'steady_growth': 22,
            'stagnant': 10,
            'declining': 5,
            'sharp_decline': 0,
            'insufficient_data': 10
        }
        trend_score = trend_scores.get(slope['trend'], 10)
        score += trend_score
        trend_labels = {
            'accelerating_growth': '가속 성장 중',
            'steady_growth': '안정적 성장',
            'stagnant': '정체 상태',
            'declining': '하락 추세',
            'sharp_decline': '급격한 하락',
            'insufficient_data': '데이터 부족'
        }
        reasons.append(f"추세: {trend_labels.get(slope['trend'], '분석 불가')}")

        # 가속도 점수 (0-20점)
        if slope.get('acceleration', 0) > 5:
            score += 20
            reasons.append("가속도 강한 양수 - 최적화 진행 중")
        elif slope.get('acceleration', 0) > 0:
            score += 15
            reasons.append("가속도 양수 - 개선 중")
        elif slope.get('acceleration', 0) > -5:
            score += 8
            reasons.append("가속도 약한 음수 - 주의 필요")
        else:
            score += 0
            reasons.append("가속도 강한 음수 - 급격한 효율 저하")

        # 리스크 감점 (0~-20점)
        risk_count = sum(1 for r in risks if '⚠️' in r or '🔴' in r)
        risk_penalty = min(risk_count * 5, 20)
        score -= risk_penalty
        if risk_count > 0:
            reasons.append(f"리스크 {risk_count}건 감지 (-{risk_penalty}점)")

        # 최종 판정
        score = max(0, min(100, score))
        if score >= 70:
            verdict = "✅ 투자 적격 (INVEST)"
            verdict_class = "invest"
        elif score >= 50:
            verdict = "🟡 관망 추천 (WATCH)"
            verdict_class = "watch"
        elif score >= 30:
            verdict = "🟠 주의 (CAUTION)"
            verdict_class = "caution"
        else:
            verdict = "🔴 회피 (AVOID)"
            verdict_class = "avoid"

        return {
            'score': score,
            'verdict': verdict,
            'verdict_class': verdict_class,
            'reasons': reasons,
            'signal': threshold['signal']
        }


def analyze_multiple_companies(tickers: List[str]) -> List[Dict]:
    """여러 기업의 EGI를 일괄 분석"""
    results = []
    for ticker in tickers:
        print(f"\n{'='*60}")
        print(f"📊 분석 중: {ticker}")
        print(f"{'='*60}")

        calc = EGICalculator(ticker)
        result = calc.generate_full_analysis()

        if result['success']:
            df = result['egi_data']
            print(f"\n{'─'*40}")
            print(f"  {result['company_name']} ({ticker})")
            print(f"{'─'*40}")
            print("\n[연도별 EGI 수치]")
            for _, row in df.iterrows():
                bar = '█' * int(min(row['EGI'], 300) / 10)
                print(f"  {int(row['Year'])}년  |  EGI: {row['EGI']:>8.2f}%  {bar}")

            print(f"\n[기울기 분석]")
            sa = result['slope_analysis']
            print(f"  Slope: {sa['slope']:.4f}  |  가속도: {sa['acceleration']:.4f}  |  R²: {sa['r_squared']:.4f}")

            print(f"\n[투자 시그널]")
            for detail in result['threshold_result']['details']:
                print(f"  {detail}")

            print(f"\n[리스크 체크]")
            for risk in result['risk_factors']:
                print(f"  {risk}")

            verdict = result['investment_verdict']
            print(f"\n[최종 판정]  점수: {verdict['score']}/100")
            print(f"  {verdict['verdict']}")
        else:
            print(f"  ❌ 분석 실패: {result.get('error', '알 수 없는 오류')}")

        results.append(result)

    return results
