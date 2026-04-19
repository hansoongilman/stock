"""
EGI 시각화 모듈
================
EGI 분석 결과 및 백테스팅 성과를 차트로 시각화합니다.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 스타일 설정
COLORS = {
    'bg': '#0d1117',
    'card_bg': '#161b22',
    'text': '#c9d1d9',
    'text_dim': '#8b949e',
    'green': '#3fb950',
    'red': '#f85149',
    'yellow': '#d29922',
    'blue': '#58a6ff',
    'purple': '#bc8cff',
    'orange': '#f0883e',
    'cyan': '#39d2c0',
    'grid': '#21262d',
    'border': '#30363d'
}


def create_egi_analysis_chart(egi_results: List[Dict], save_path: str = 'c:/stock/egi_analysis.png'):
    """기업별 EGI 분석 종합 차트 생성"""
    valid_results = [r for r in egi_results if r.get('success', False)]
    if not valid_results:
        print("  ⚠️ 시각화할 데이터가 없습니다.")
        return

    n_companies = len(valid_results)
    fig = plt.figure(figsize=(24, 6 * max(n_companies, 2) + 4), facecolor=COLORS['bg'])

    # 상단 제목
    fig.suptitle('EGI (Efficiency Growth Index) 분석 리포트',
                 fontsize=24, fontweight='bold', color=COLORS['text'],
                 y=0.98)

    gs = gridspec.GridSpec(n_companies + 1, 3, figure=fig, hspace=0.4, wspace=0.3,
                           top=0.95, bottom=0.05, left=0.06, right=0.94)

    # === 각 기업별 EGI 차트 ===
    for i, result in enumerate(valid_results):
        df = result['egi_data']
        ticker = result['ticker']
        name = result['company_name']
        verdict = result['investment_verdict']
        slope = result['slope_analysis']

        # 1. EGI 추이 바 차트
        ax1 = fig.add_subplot(gs[i, 0])
        ax1.set_facecolor(COLORS['card_bg'])
        years = df['Year'].astype(int).astype(str)
        egi_vals = df['EGI'].values

        bar_colors = []
        for v in egi_vals:
            if v >= 150:
                bar_colors.append(COLORS['green'])
            elif v >= 120:
                bar_colors.append(COLORS['cyan'])
            elif v >= 100:
                bar_colors.append(COLORS['yellow'])
            elif v >= 80:
                bar_colors.append(COLORS['orange'])
            else:
                bar_colors.append(COLORS['red'])

        bars = ax1.bar(years, egi_vals, color=bar_colors, edgecolor=COLORS['border'],
                       linewidth=1, alpha=0.9, width=0.6)

        # 값 라벨
        for bar, val in zip(bars, egi_vals):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                     f'{val:.1f}%', ha='center', va='bottom',
                     fontsize=10, color=COLORS['text'], fontweight='bold')

        # 임계선
        ax1.axhline(y=150, color=COLORS['green'], linestyle='--', alpha=0.5, label='강력 시그널 (150%)')
        ax1.axhline(y=100, color=COLORS['yellow'], linestyle='--', alpha=0.5, label='손익분기 (100%)')

        ax1.set_title(f'{name}\n({ticker})', fontsize=13, fontweight='bold',
                      color=COLORS['text'], pad=10)
        ax1.set_ylabel('EGI (%)', color=COLORS['text_dim'], fontsize=10)
        ax1.tick_params(colors=COLORS['text_dim'])
        ax1.legend(fontsize=8, loc='upper left', framealpha=0.3)
        ax1.grid(axis='y', color=COLORS['grid'], alpha=0.3)
        for spine in ax1.spines.values():
            spine.set_color(COLORS['border'])

        # 2. Gain vs Loss 분해 차트
        ax2 = fig.add_subplot(gs[i, 1])
        ax2.set_facecolor(COLORS['card_bg'])

        x = np.arange(len(years))
        width = 0.35
        gain_vals = df['Total_Gain'].values / 1e9  # 10억 단위
        loss_vals = df['Total_Loss'].values / 1e9

        ax2.bar(x - width/2, gain_vals, width, label='Total Gain',
                color=COLORS['green'], alpha=0.8, edgecolor=COLORS['border'])
        ax2.bar(x + width/2, loss_vals, width, label='Total Loss',
                color=COLORS['red'], alpha=0.8, edgecolor=COLORS['border'])

        ax2.set_xticks(x)
        ax2.set_xticklabels(years)
        ax2.set_title('Gain vs Loss 비교', fontsize=12, color=COLORS['text'], pad=10)
        ax2.set_ylabel('금액 (십억)', color=COLORS['text_dim'], fontsize=10)
        ax2.tick_params(colors=COLORS['text_dim'])
        ax2.legend(fontsize=9, framealpha=0.3)
        ax2.grid(axis='y', color=COLORS['grid'], alpha=0.3)
        for spine in ax2.spines.values():
            spine.set_color(COLORS['border'])

        # 3. 투자 판정 카드
        ax3 = fig.add_subplot(gs[i, 2])
        ax3.set_facecolor(COLORS['card_bg'])
        ax3.axis('off')

        # 판정 색상
        verdict_colors = {
            'invest': COLORS['green'],
            'watch': COLORS['yellow'],
            'caution': COLORS['orange'],
            'avoid': COLORS['red']
        }
        vc = verdict_colors.get(verdict['verdict_class'], COLORS['text'])

        # 점수 원형 표시
        circle = plt.Circle((0.2, 0.72), 0.15, transform=ax3.transAxes,
                             fill=False, color=vc, linewidth=4)
        ax3.add_patch(circle)
        ax3.text(0.2, 0.72, f"{verdict['score']}", transform=ax3.transAxes,
                 ha='center', va='center', fontsize=28, fontweight='bold', color=vc)
        ax3.text(0.2, 0.55, '/100', transform=ax3.transAxes,
                 ha='center', va='center', fontsize=12, color=COLORS['text_dim'])

        # 판정 텍스트
        ax3.text(0.55, 0.78, verdict['verdict'], transform=ax3.transAxes,
                 fontsize=14, fontweight='bold', color=vc, va='center')

        # 추세 정보
        trend_labels = {
            'accelerating_growth': '🚀 가속 성장',
            'steady_growth': '📈 안정 성장',
            'stagnant': '➡️ 정체',
            'declining': '📉 하락',
            'sharp_decline': '⚠️ 급락',
            'insufficient_data': '❓ 데이터 부족'
        }
        trend_text = trend_labels.get(slope['trend'], '분석 불가')
        ax3.text(0.55, 0.65, f"추세: {trend_text}", transform=ax3.transAxes,
                 fontsize=11, color=COLORS['text'], va='center')
        ax3.text(0.55, 0.53, f"기울기: {slope['slope']:.4f}  |  가속도: {slope['acceleration']:.4f}",
                 transform=ax3.transAxes, fontsize=9, color=COLORS['text_dim'], va='center')

        # 리스크 요약
        risks = result.get('risk_factors', [])
        risk_y = 0.38
        ax3.text(0.05, risk_y + 0.06, '리스크:', transform=ax3.transAxes,
                 fontsize=11, fontweight='bold', color=COLORS['text'])
        for j, risk in enumerate(risks[:3]):
            # 이모지 제거 후 짧게
            risk_short = risk[:50] + '...' if len(risk) > 50 else risk
            ax3.text(0.05, risk_y - j * 0.08, risk_short, transform=ax3.transAxes,
                     fontsize=8, color=COLORS['text_dim'], va='center')

        for spine in ax3.spines.values():
            spine.set_color(COLORS['border'])

    # === 하단: 종합 비교 테이블 ===
    ax_table = fig.add_subplot(gs[n_companies, :])
    ax_table.set_facecolor(COLORS['card_bg'])
    ax_table.axis('off')
    ax_table.set_title('📊 기업 EGI 종합 비교', fontsize=16, fontweight='bold',
                       color=COLORS['text'], pad=15)

    # 테이블 데이터 준비
    table_data = []
    for result in valid_results:
        latest = result['egi_data'].iloc[-1]
        v = result['investment_verdict']
        s = result['slope_analysis']
        table_data.append([
            f"{result['company_name'][:15]}",
            result['ticker'],
            f"{latest['EGI']:.1f}%",
            f"{s['slope']:.3f}",
            f"{s['acceleration']:.3f}",
            f"{v['score']}/100",
            v['signal']
        ])

    # 점수 기준 정렬
    table_data.sort(key=lambda x: int(x[5].split('/')[0]), reverse=True)

    col_labels = ['기업명', '티커', '최신 EGI', '기울기', '가속도', '점수', '시그널']
    table = ax_table.table(cellText=table_data, colLabels=col_labels,
                            cellLoc='center', loc='center',
                            colWidths=[0.18, 0.1, 0.12, 0.12, 0.12, 0.12, 0.14])

    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.8)

    # 테이블 스타일링
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor(COLORS['blue'])
            cell.set_text_props(color='white', fontweight='bold')
        else:
            cell.set_facecolor(COLORS['card_bg'])
            cell.set_text_props(color=COLORS['text'])
        cell.set_edgecolor(COLORS['border'])

        # 시그널 컬러링
        if row > 0 and col == 6:
            signal = cell.get_text().get_text()
            if 'BUY' in signal:
                cell.set_text_props(color=COLORS['green'], fontweight='bold')
            elif 'SELL' in signal:
                cell.set_text_props(color=COLORS['red'], fontweight='bold')
            elif 'HOLD' in signal:
                cell.set_text_props(color=COLORS['yellow'])

    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=COLORS['bg'])
    plt.close()
    print(f"\n  💾 EGI 분석 차트 저장: {save_path}")


def create_backtest_chart(backtest_results: Dict,
                          save_path: str = 'c:/stock/backtest_results.png'):
    """백테스팅 결과 시각화"""
    if not backtest_results.get('success'):
        print("  ⚠️ 백테스팅 결과 없음")
        return

    perf = backtest_results['performance']
    bench = backtest_results['benchmark']
    metrics = backtest_results['metrics']
    portfolio = backtest_results['portfolio']
    trades = backtest_results['trades']

    fig = plt.figure(figsize=(24, 18), facecolor=COLORS['bg'])
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3,
                           top=0.93, bottom=0.05, left=0.06, right=0.94)

    fig.suptitle('EGI 전략 백테스팅 결과',
                 fontsize=24, fontweight='bold', color=COLORS['text'], y=0.97)

    # === 1. 자산 곡선 (Equity Curve) ===
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.set_facecolor(COLORS['card_bg'])

    if not perf.empty and 'Portfolio_Value' in perf.columns:
        ax1.plot(perf.index, perf['Portfolio_Value'] / 1e8, color=COLORS['cyan'],
                 linewidth=2, label='EGI 포트폴리오', zorder=3)

        if not bench.empty and 'Benchmark_Value' in bench.columns:
            # 인덱스 맞춤
            common_idx = perf.index.intersection(bench.index)
            if len(common_idx) > 0:
                ax1.plot(common_idx, bench.loc[common_idx, 'Benchmark_Value'] / 1e8,
                         color=COLORS['text_dim'], linewidth=1.5,
                         label='S&P 500', alpha=0.7, zorder=2)

        ax1.fill_between(perf.index, perf['Portfolio_Value'] / 1e8,
                         alpha=0.1, color=COLORS['cyan'])

    ax1.set_title('자산 곡선 (Equity Curve)', fontsize=14, fontweight='bold',
                  color=COLORS['text'], pad=10)
    ax1.set_ylabel('자산 (억원)', color=COLORS['text_dim'], fontsize=11)
    ax1.legend(fontsize=11, framealpha=0.3, loc='upper left')
    ax1.tick_params(colors=COLORS['text_dim'])
    ax1.grid(color=COLORS['grid'], alpha=0.3)
    for spine in ax1.spines.values():
        spine.set_color(COLORS['border'])

    # === 2. 성과 지표 대시보드 ===
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.set_facecolor(COLORS['card_bg'])
    ax2.axis('off')

    metric_items = [
        ('총 수익률', f"{metrics.get('total_return', 0):+.2f}%",
         COLORS['green'] if metrics.get('total_return', 0) > 0 else COLORS['red']),
        ('CAGR', f"{metrics.get('cagr', 0):+.2f}%",
         COLORS['green'] if metrics.get('cagr', 0) > 0 else COLORS['red']),
        ('샤프비율', f"{metrics.get('sharpe_ratio', 0):.4f}", COLORS['blue']),
        ('소르티노비율', f"{metrics.get('sortino_ratio', 0):.4f}", COLORS['purple']),
        ('MDD', f"{metrics.get('mdd', 0):.2f}%", COLORS['red']),
        ('승률', f"{metrics.get('win_rate', 0):.1f}%", COLORS['cyan']),
        ('Alpha', f"{metrics.get('alpha', 0):+.2f}%",
         COLORS['green'] if metrics.get('alpha', 0) > 0 else COLORS['red']),
        ('최종 자산', f"₩{metrics.get('final_value', 0):,.0f}", COLORS['text']),
    ]

    ax2.text(0.5, 0.97, '📊 성과 지표', transform=ax2.transAxes,
             ha='center', fontsize=14, fontweight='bold', color=COLORS['text'])

    for i, (label, value, color) in enumerate(metric_items):
        y_pos = 0.88 - i * 0.115
        ax2.text(0.08, y_pos, label, transform=ax2.transAxes,
                 fontsize=11, color=COLORS['text_dim'], va='center')
        ax2.text(0.92, y_pos, value, transform=ax2.transAxes,
                 fontsize=13, fontweight='bold', color=color, va='center', ha='right')
        # 구분선 (use plot instead of axhline, which doesn't accept transform)
        ax2.plot([0.05, 0.95], [y_pos - 0.04, y_pos - 0.04],
                 color=COLORS['grid'], alpha=0.3, transform=ax2.transAxes,
                 clip_on=False)

    for spine in ax2.spines.values():
        spine.set_color(COLORS['border'])

    # === 3. 포트폴리오 구성 (파이 차트) ===
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor(COLORS['card_bg'])

    if portfolio:
        labels = [f"{info.get('company_name', t)[:10]}\n({t})" for t, info in portfolio.items()]
        sizes = [info['weight'] * 100 for info in portfolio.values()]
        pie_colors = [COLORS['cyan'], COLORS['green'], COLORS['purple'],
                      COLORS['yellow'], COLORS['orange'], COLORS['blue'],
                      COLORS['red']][:len(labels)]

        wedges, texts, autotexts = ax3.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            colors=pie_colors, startangle=140,
            textprops={'color': COLORS['text'], 'fontsize': 9},
            pctdistance=0.75, labeldistance=1.15
        )
        for at in autotexts:
            at.set_fontweight('bold')
            at.set_fontsize(10)

    ax3.set_title('포트폴리오 구성', fontsize=14, fontweight='bold',
                  color=COLORS['text'], pad=10)

    # === 4. Drawdown 차트 ===
    ax4 = fig.add_subplot(gs[1, 1:])
    ax4.set_facecolor(COLORS['card_bg'])

    if not perf.empty and 'Portfolio_Value' in perf.columns:
        portfolio_values = perf['Portfolio_Value']
        running_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - running_max) / running_max * 100

        ax4.fill_between(drawdown.index, drawdown, alpha=0.4, color=COLORS['red'])
        ax4.plot(drawdown.index, drawdown, color=COLORS['red'],
                 linewidth=1, alpha=0.8)

        mdd_idx = drawdown.idxmin()
        ax4.annotate(f'MDD: {drawdown.min():.1f}%',
                     xy=(mdd_idx, drawdown.min()),
                     fontsize=12, fontweight='bold', color=COLORS['red'],
                     xytext=(10, -20), textcoords='offset points',
                     arrowprops=dict(arrowstyle='->', color=COLORS['red']))

    ax4.set_title('낙폭 (Drawdown)', fontsize=14, fontweight='bold',
                  color=COLORS['text'], pad=10)
    ax4.set_ylabel('낙폭 (%)', color=COLORS['text_dim'], fontsize=11)
    ax4.tick_params(colors=COLORS['text_dim'])
    ax4.grid(color=COLORS['grid'], alpha=0.3)
    for spine in ax4.spines.values():
        spine.set_color(COLORS['border'])

    # === 5. 연도별 EGI vs 매매 시그널 ===
    ax5 = fig.add_subplot(gs[2, :])
    ax5.set_facecolor(COLORS['card_bg'])

    if trades:
        # 티커별 그룹화
        trade_df = pd.DataFrame(trades)
        unique_tickers = trade_df['ticker'].unique()
        n_tickers = len(unique_tickers)
        x_positions = {}

        all_years = sorted(trade_df['year'].unique())
        x = np.arange(len(all_years))

        for i, ticker in enumerate(unique_tickers):
            ticker_trades = trade_df[trade_df['ticker'] == ticker]
            egi_by_year = {row['year']: row['egi'] for _, row in ticker_trades.iterrows()}

            y_vals = [egi_by_year.get(yr, np.nan) for yr in all_years]
            color = [COLORS['cyan'], COLORS['green'], COLORS['purple'],
                     COLORS['yellow'], COLORS['orange'], COLORS['blue']][i % 6]

            company = ticker_trades.iloc[0]['company_name'][:12]
            ax5.plot(all_years, y_vals, 'o-', color=color, linewidth=2,
                     markersize=8, label=f'{company} ({ticker})', alpha=0.9)

            # 시그널 라벨
            for _, trade in ticker_trades.iterrows():
                marker = {'STRONG_BUY': '▲', 'BUY': '△', 'HOLD': '◇',
                          'SELL': '▽', 'STRONG_SELL': '▼'}.get(trade['action'], '◇')
                mc = {'STRONG_BUY': COLORS['green'], 'BUY': COLORS['cyan'],
                      'HOLD': COLORS['yellow'], 'SELL': COLORS['orange'],
                      'STRONG_SELL': COLORS['red']}.get(trade['action'], COLORS['text'])
                ax5.annotate(marker, xy=(trade['year'], trade['egi']),
                             fontsize=14, color=mc, ha='center', va='bottom',
                             xytext=(0, 10), textcoords='offset points')

        ax5.axhline(y=150, color=COLORS['green'], linestyle='--', alpha=0.5,
                    label='강력 시그널 (150%)')
        ax5.axhline(y=100, color=COLORS['yellow'], linestyle='--', alpha=0.5,
                    label='손익분기 (100%)')

    ax5.set_title('연도별 EGI 추이 및 매매 시그널', fontsize=14, fontweight='bold',
                  color=COLORS['text'], pad=10)
    ax5.set_xlabel('연도', color=COLORS['text_dim'], fontsize=11)
    ax5.set_ylabel('EGI (%)', color=COLORS['text_dim'], fontsize=11)
    ax5.tick_params(colors=COLORS['text_dim'])
    ax5.legend(fontsize=9, framealpha=0.3, loc='upper left', ncol=3)
    ax5.grid(color=COLORS['grid'], alpha=0.3)
    for spine in ax5.spines.values():
        spine.set_color(COLORS['border'])

    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=COLORS['bg'])
    plt.close()
    print(f"  💾 백테스팅 차트 저장: {save_path}")
