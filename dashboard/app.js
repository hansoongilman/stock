/**
 * EGI Dashboard - Interactive Chart & Data Rendering
 * =====================================================
 * Loads results.json and renders the EGI analysis dashboard
 */

const COLORS = {
    cyan: '#06b6d4',
    green: '#10b981',
    red: '#ef4444',
    purple: '#8b5cf6',
    blue: '#3b82f6',
    orange: '#f97316',
    yellow: '#eab308',
    pink: '#ec4899',
    dim: '#64748b',
    text: '#e2e8f0',
    grid: '#1e293b',
    card: '#1a1f2e',
};

const PALETTE = [COLORS.cyan, COLORS.green, COLORS.purple, COLORS.blue, COLORS.orange, COLORS.pink, COLORS.yellow, COLORS.red];

Chart.defaults.color = COLORS.dim;
Chart.defaults.borderColor = COLORS.grid;
Chart.defaults.font.family = "'Inter', sans-serif";

let DATA = null;

// ─── Load Data ───
async function loadData() {
    try {
        const resp = await fetch('../results.json');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        DATA = await resp.json();
        renderAll();
    } catch (e) {
        console.error('Failed to load results.json:', e);
        document.body.innerHTML = `
            <div class="no-data" style="padding:4rem;text-align:center;">
                <h2 style="color:#e2e8f0;margin-bottom:1rem;">📊 데이터 로딩 실패</h2>
                <p style="color:#94a3b8;">먼저 <code style="color:#06b6d4;">python main.py</code>를 실행하여 results.json을 생성해주세요.</p>
                <p style="color:#64748b;margin-top:0.5rem;font-size:0.85rem;">오류: ${e.message}</p>
            </div>
        `;
    }
}

// ─── Render All ───
function renderAll() {
    renderHeader();
    renderMetrics();
    renderEquityCurve();
    renderPortfolio();
    renderCompanyCards();
    renderTradeTable();
}

// ─── Header ───
function renderHeader() {
    const timeEl = document.getElementById('generated-time');
    const countEl = document.getElementById('company-count');
    
    if (DATA.generated_at) {
        const d = new Date(DATA.generated_at);
        timeEl.textContent = `📅 ${d.toLocaleDateString('ko-KR')} ${d.toLocaleTimeString('ko-KR', {hour:'2-digit',minute:'2-digit'})}`;
    }
    countEl.textContent = `🏢 ${DATA.companies?.length || 0}개 기업`;
}

// ─── Metrics ───
function renderMetrics() {
    const grid = document.getElementById('metrics-grid');
    const m = DATA.backtest || {};
    
    const items = [
        { label: '총 수익률', value: `${(m.total_return||0) >= 0 ? '+':''}${(m.total_return||0).toFixed(2)}%`, cls: (m.total_return||0) >= 0 ? 'positive':'negative' },
        { label: 'CAGR', value: `${(m.cagr||0) >= 0 ? '+':''}${(m.cagr||0).toFixed(2)}%`, cls: (m.cagr||0) >= 0 ? 'positive':'negative' },
        { label: '샤프비율', value: (m.sharpe_ratio||0).toFixed(4), cls: (m.sharpe_ratio||0) > 1 ? 'positive' : 'neutral' },
        { label: '소르티노비율', value: (m.sortino_ratio||0).toFixed(4), cls: (m.sortino_ratio||0) > 1 ? 'positive' : 'neutral' },
        { label: '최대 낙폭', value: `${(m.mdd||0).toFixed(2)}%`, cls: 'negative', sub: 'MDD' },
        { label: '승률', value: `${(m.win_rate||0).toFixed(1)}%`, cls: (m.win_rate||0) > 50 ? 'positive' : 'neutral' },
        { label: 'Alpha', value: `${(m.alpha||0) >= 0 ? '+':''}${(m.alpha||0).toFixed(2)}%`, cls: (m.alpha||0) >= 0 ? 'positive':'negative', sub: 'vs S&P 500' },
        { label: '최종 자산', value: `₩${(m.final_value||0).toLocaleString()}`, cls: 'neutral' },
    ];
    
    grid.innerHTML = items.map(item => `
        <div class="metric-card ${item.cls}">
            <div class="metric-label">${item.label}</div>
            <div class="metric-value ${item.cls}">${item.value}</div>
            ${item.sub ? `<div class="metric-sub">${item.sub}</div>` : ''}
        </div>
    `).join('');
}

// ─── Equity Curve ───
function renderEquityCurve() {
    const ctx = document.getElementById('equityChart');
    if (!ctx) return;
    
    const equity = DATA.equity_curve || [];
    const bench = DATA.benchmark_curve || [];
    
    if (!equity.length) {
        ctx.parentElement.innerHTML = '<div class="no-data">자산 곡선 데이터가 없습니다. python main.py를 실행해주세요.</div>';
        return;
    }
    
    // 억원 단위로 변환
    const eqData = equity.map(d => ({ x: d.date, y: d.value / 1e8 }));
    const benchData = bench.map(d => ({ x: d.date, y: d.value / 1e8 }));
    
    new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'EGI 포트폴리오',
                    data: eqData,
                    borderColor: COLORS.cyan,
                    backgroundColor: 'rgba(6,182,212,0.08)',
                    borderWidth: 2.5,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.3,
                },
                {
                    label: 'S&P 500 벤치마크',
                    data: benchData,
                    borderColor: COLORS.dim,
                    borderWidth: 1.5,
                    pointRadius: 0,
                    borderDash: [6, 3],
                    fill: false,
                    tension: 0.3,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', labels: { padding: 20, usePointStyle: true, pointStyle: 'line' } },
                tooltip: {
                    backgroundColor: '#1a1f2e',
                    borderColor: '#334155',
                    borderWidth: 1,
                    titleColor: '#e2e8f0',
                    bodyColor: '#94a3b8',
                    padding: 12,
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: ₩${ctx.parsed.y.toFixed(2)}억`
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'month', displayFormats: { month: 'yyyy-MM' } },
                    grid: { color: COLORS.grid },
                    ticks: { maxTicksLimit: 12 }
                },
                y: {
                    title: { display: true, text: '자산 (억원)', color: COLORS.dim },
                    grid: { color: COLORS.grid }
                }
            }
        }
    });
}

// ─── Portfolio ───
function renderPortfolio() {
    const ctx = document.getElementById('portfolioChart');
    const tableWrap = document.getElementById('portfolio-table-wrap');
    
    const portfolio = DATA.portfolio || {};
    const entries = Object.entries(portfolio);
    
    if (!entries.length) {
        if (ctx) ctx.parentElement.innerHTML = '<div class="no-data">포트폴리오 데이터 없음</div>';
        return;
    }
    
    // Pie chart
    const labels = entries.map(([t, info]) => `${(info.company_name||t).substring(0,12)} (${t})`);
    const weights = entries.map(([, info]) => (info.weight * 100).toFixed(1));
    const colors = entries.map((_, i) => PALETTE[i % PALETTE.length]);
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: weights,
                backgroundColor: colors.map(c => c + '99'),
                borderColor: colors,
                borderWidth: 2,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '55%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { padding: 12, usePointStyle: true, pointStyle: 'circle', font: { size: 11 } }
                },
                tooltip: {
                    backgroundColor: '#1a1f2e',
                    borderColor: '#334155',
                    borderWidth: 1,
                    callbacks: {
                        label: ctx => ` ${ctx.label}: ${ctx.parsed}%`
                    }
                }
            }
        }
    });
    
    // Table
    let html = `<table><thead><tr><th>기업</th><th>티커</th><th>EGI</th><th>점수</th><th>가중치</th><th>시그널</th></tr></thead><tbody>`;
    entries.sort((a, b) => b[1].score - a[1].score);
    for (const [ticker, info] of entries) {
        const signalCls = `signal-${info.signal}`;
        html += `<tr>
            <td>${(info.company_name||ticker).substring(0,15)}</td>
            <td style="font-family:var(--font-mono);color:var(--accent-cyan)">${ticker}</td>
            <td style="font-weight:700">${info.egi?.toFixed(1) || '-'}%</td>
            <td>${info.score}/100</td>
            <td>${(info.weight*100).toFixed(1)}%</td>
            <td><span class="signal-badge ${signalCls}">${info.signal}</span></td>
        </tr>`;
    }
    html += `</tbody></table>`;
    tableWrap.innerHTML = html;
}

// ─── Company Cards ───
function renderCompanyCards() {
    const container = document.getElementById('company-cards');
    const companies = DATA.companies || [];
    
    if (!companies.length) {
        container.innerHTML = '<div class="no-data">기업 분석 데이터가 없습니다.</div>';
        return;
    }
    
    container.innerHTML = companies.map((comp, idx) => {
        const v = comp.investment_verdict || {};
        const s = comp.slope_analysis || {};
        const latest = comp.egi_data?.[comp.egi_data.length - 1] || {};
        const signal = comp.threshold_result?.signal || 'HOLD';
        const scoreClass = v.score >= 70 ? 'score-high' : v.score >= 40 ? 'score-mid' : 'score-low';
        const verdictClass = `verdict-${v.verdict_class || 'watch'}`;
        
        const trendLabels = {
            accelerating_growth: '🚀 가속 성장',
            steady_growth: '📈 안정 성장',
            stagnant: '➡️ 정체',
            declining: '📉 하락',
            sharp_decline: '⚠️ 급락',
            insufficient_data: '❓ 데이터 부족'
        };
        
        const risks = (comp.risk_factors || []).filter(r => !r.includes('✅'));

        return `
        <div class="company-card" id="card-${comp.ticker}">
            <div class="company-card-header">
                <div>
                    <div class="company-name">${comp.company_name}</div>
                    <div class="company-ticker">${comp.ticker}</div>
                </div>
                <div style="display:flex;align-items:center;gap:10px">
                    <span class="signal-badge signal-${signal}">${signal.replace('_',' ')}</span>
                    <div class="score-circle ${scoreClass}">${v.score || 0}</div>
                </div>
            </div>
            
            <div class="egi-chart-mini">
                <canvas id="egi-mini-${idx}"></canvas>
            </div>
            
            <div class="company-stats">
                <div class="stat-item">
                    <div class="stat-label">최신 EGI</div>
                    <div class="stat-value" style="color:${(latest.egi||0) >= 150 ? COLORS.green : (latest.egi||0) >= 100 ? COLORS.yellow : COLORS.red}">${(latest.egi||0).toFixed(1)}%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">기울기</div>
                    <div class="stat-value" style="color:${(s.slope||0) > 0 ? COLORS.green : COLORS.red}">${(s.slope||0).toFixed(3)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">추세</div>
                    <div class="stat-value" style="font-size:0.82rem">${trendLabels[s.trend] || '−'}</div>
                </div>
            </div>
            
            <div class="${verdictClass} verdict-bar">${v.verdict || '분석 불가'}</div>
            
            ${risks.length ? `<ul class="risk-list">${risks.map(r => `<li>${r}</li>`).join('')}</ul>` : ''}
        </div>`;
    }).join('');
    
    // Mini EGI charts
    companies.forEach((comp, idx) => {
        const canvas = document.getElementById(`egi-mini-${idx}`);
        if (!canvas || !comp.egi_data?.length) return;
        
        const labels = comp.egi_data.map(d => d.year.toString());
        const values = comp.egi_data.map(d => d.egi);
        const bgColors = values.map(v => v >= 150 ? COLORS.green+'88' : v >= 100 ? COLORS.yellow+'88' : COLORS.red+'88');
        const borderColors = values.map(v => v >= 150 ? COLORS.green : v >= 100 ? COLORS.yellow : COLORS.red);
        
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: bgColors,
                    borderColor: borderColors,
                    borderWidth: 1.5,
                    borderRadius: 4,
                    barThickness: 28
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: {
                    callbacks: { label: ctx => `EGI: ${ctx.parsed.y.toFixed(1)}%` }
                }},
                scales: {
                    x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                    y: {
                        grid: { color: COLORS.grid },
                        ticks: { font: { size: 9 }, callback: v => v + '%' }
                    }
                }
            }
        });
    });
}

// ─── Trade Table ───
function renderTradeTable() {
    const tbody = document.getElementById('trade-tbody');
    const trades = DATA.trades || [];
    
    if (!trades.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#64748b;padding:2rem;">매매 내역이 없습니다.</td></tr>';
        return;
    }
    
    const signalEmoji = {
        STRONG_BUY: '🟢', BUY: '🔵', MODERATE_BUY: '🟡',
        HOLD: '⚪', SELL: '🟠', STRONG_SELL: '🔴'
    };
    
    tbody.innerHTML = trades.map(t => {
        const egiColor = t.egi >= 150 ? COLORS.green : t.egi >= 100 ? COLORS.yellow : COLORS.red;
        return `<tr>
            <td>${t.year}</td>
            <td style="color:var(--text-primary);font-family:var(--font-sans)">${(t.company_name||t.ticker).substring(0,15)}</td>
            <td style="color:${COLORS.cyan}">${t.ticker}</td>
            <td style="color:${egiColor};font-weight:700">${t.egi.toFixed(1)}%</td>
            <td><span class="signal-badge signal-${t.action}">${signalEmoji[t.action]||''} ${t.action.replace('_',' ')}</span></td>
            <td>${(t.weight*100).toFixed(1)}%</td>
        </tr>`;
    }).join('');
}

// ─── Init ───
document.addEventListener('DOMContentLoaded', loadData);
