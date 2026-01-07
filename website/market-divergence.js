// Market Divergence Analysis - Main JavaScript

// Load data on page load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('market_divergence_corrected.json');
        const data = await response.json();
        
        initializePage(data);
        setupInteractivity(data);
    } catch (error) {
        console.error('Error loading data:', error);
        showError();
    }
});

function initializePage(data) {
    // Populate summary stats
    populateSummaryBanner(data);
    
    // Populate key findings
    populateKeyFindings(data);
    
    // Create comparison charts
    createComparisonChart('2012', data);
    createComparisonChart('2018', data);
}

function populateSummaryBanner(data) {
    const summary2012 = data.summary_2012_2023;
    const summary2018 = data.summary_2018_2023;
    
    document.getElementById('sp500_2012').textContent = `+${summary2012.sp500_total_gain.toFixed(1)}%`;
    document.getElementById('mli_2012').textContent = formatChange(summary2012.mli_total_gain);
    document.getElementById('mli_2018').textContent = formatChange(summary2018.mli_total_gain);
}

function populateKeyFindings(data) {
    const summary2012 = data.summary_2012_2023;
    const summary2018 = data.summary_2018_2023;
    const stateChanges = data.state_changes_2018_2023;
    const inflation = data.inflation_analysis;
    
    // Finding cards
    document.getElementById('finding_sp500_2012').textContent = formatChange(summary2012.sp500_total_gain);
    document.getElementById('finding_mli_2012').textContent = formatChange(summary2012.mli_total_gain);
    document.getElementById('finding_sp500_2018').textContent = formatChange(summary2018.sp500_total_gain);
    document.getElementById('finding_mli_2018').textContent = formatChange(summary2018.mli_total_gain);
    
    const losers = stateChanges.filter(s => s.mli_change < 0);
    document.getElementById('finding_states_worse').textContent = losers.length;
    
    // Finding card 4 is now static GDP data in HTML
}

function populateStateChanges(data) {
    const stateChanges = data.state_changes_2018_2023;
    
    // Count winners and losers
    const winners = stateChanges.filter(s => s.mli_change > 0);
    const losers = stateChanges.filter(s => s.mli_change < 0);
    
    document.getElementById('statesWorse').textContent = losers.length;
    document.getElementById('statesBetter').textContent = winners.length;
    
    // Top 5 winners
    const topWinners = [...stateChanges]
        .sort((a, b) => b.mli_change - a.mli_change)
        .slice(0, 5);
    
    const winnersHTML = topWinners.map(state => `
        <div class="state-rank-item">
            <span class="state-rank-name">${state.state}</span>
            <span class="state-rank-change positive">${formatChange(state.mli_change)}</span>
        </div>
    `).join('');
    
    document.getElementById('topWinners').innerHTML = winnersHTML;
    
    // Top 5 losers
    const topLosers = [...stateChanges]
        .sort((a, b) => a.mli_change - b.mli_change)
        .slice(0, 5);
    
    const losersHTML = topLosers.map(state => `
        <div class="state-rank-item">
            <span class="state-rank-name">${state.state}</span>
            <span class="state-rank-change negative">${formatChange(state.mli_change)}</span>
        </div>
    `).join('');
    
    document.getElementById('topLosers').innerHTML = losersHTML;
}

function populateInflationAnalysis(data) {
    const inflation = data.inflation_analysis;
    
    // 2012-2023 period
    const period2012 = inflation.find(p => p.period === '2012-2023');
    if (period2012) {
        document.getElementById('housing_2012').textContent = `+${period2012.housing_inflation.toFixed(1)}%`;
        document.getElementById('goods_2012').textContent = `+${period2012.goods_inflation.toFixed(1)}%`;
        document.getElementById('gap_2012').textContent = (period2012.housing_inflation - period2012.goods_inflation).toFixed(1);
    }
    
    // 2018-2023 period
    const period2018 = inflation.find(p => p.period === '2018-2023');
    if (period2018) {
        document.getElementById('housing_2018').textContent = `+${period2018.housing_inflation.toFixed(1)}%`;
        document.getElementById('goods_2018').textContent = `+${period2018.goods_inflation.toFixed(1)}%`;
        document.getElementById('gap_2018').textContent = (period2018.housing_inflation - period2018.goods_inflation).toFixed(1);
    }
}

function createComparisonChart(period, data) {
    const ctx = document.getElementById(`chart${period}`).getContext('2d');
    const comparison = period === '2012' ? data.market_comparison_2012 : data.market_comparison_2018;
    
    const years = comparison.map(d => d.year);
    const sp500 = comparison.map(d => d.sp500_indexed);
    const income = comparison.map(d => d.income_indexed);
    const col = comparison.map(d => d.col_indexed);
    const mli = comparison.map(d => d.mli_indexed);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                {
                    label: 'S&P 500',
                    data: sp500,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Median Income',
                    data: income,
                    borderColor: '#059669',
                    backgroundColor: 'rgba(5, 150, 105, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Cost of Living',
                    data: col,
                    borderColor: '#dc2626',
                    backgroundColor: 'rgba(220, 38, 38, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Real Purchasing Power (MLI)',
                    data: mli,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                title: {
                    display: true,
                    text: `Indexed Growth from ${period} (Baseline = 100)`,
                    font: {
                        family: "'IBM Plex Sans', sans-serif",
                        size: 16,
                        weight: '600'
                    },
                    padding: { bottom: 20 }
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        font: {
                            family: "'IBM Plex Sans', sans-serif",
                            size: 12
                        },
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        family: "'IBM Plex Sans', sans-serif",
                        size: 13,
                        weight: '600'
                    },
                    bodyFont: {
                        family: "'IBM Plex Mono', monospace",
                        size: 12
                    },
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y.toFixed(1);
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: "'IBM Plex Mono', monospace",
                            size: 11
                        }
                    }
                },
                y: {
                    beginAtZero: false,
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        font: {
                            family: "'IBM Plex Mono', monospace",
                            size: 11
                        },
                        callback: function(value) {
                            return value.toFixed(0);
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
    
    // Update metrics display
    const summary = period === '2012' ? data.summary_2012_2023 : data.summary_2018_2023;
    document.getElementById(`sp500_gain_${period}`).textContent = formatChange(summary.sp500_total_gain);
    document.getElementById(`income_gain_${period}`).textContent = formatChange(summary.income_total_gain);
    document.getElementById(`col_gain_${period}`).textContent = formatChange(summary.col_total_gain);
    document.getElementById(`mli_gain_${period}`).textContent = formatChange(summary.mli_total_gain);
}

function createScatterPlot(data) {
    const ctx = document.getElementById('scatterChart').getContext('2d');
    const stateChanges = data.state_changes_2018_2023;
    
    const scatterData = stateChanges.map(state => ({
        x: state.mli_2018,
        y: state.mli_2023,
        label: state.state
    }));
    
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'States',
                data: scatterData,
                backgroundColor: (context) => {
                    const point = context.raw;
                    return point.y >= point.x ? 'rgba(5, 150, 105, 0.6)' : 'rgba(220, 38, 38, 0.6)';
                },
                borderColor: (context) => {
                    const point = context.raw;
                    return point.y >= point.x ? '#059669' : '#dc2626';
                },
                borderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 1.8,
            plugins: {
                title: {
                    display: true,
                    text: '2018 vs 2023 Purchasing Power by State',
                    font: {
                        family: "'IBM Plex Sans', sans-serif",
                        size: 16,
                        weight: '600'
                    },
                    padding: { bottom: 20 }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        family: "'IBM Plex Sans', sans-serif",
                        size: 13,
                        weight: '600'
                    },
                    bodyFont: {
                        family: "'IBM Plex Mono', monospace",
                        size: 12
                    },
                    callbacks: {
                        title: function(context) {
                            return context[0].raw.label;
                        },
                        label: function(context) {
                            const change = context.raw.y - context.raw.x;
                            return [
                                `2018: ${context.raw.x.toFixed(3)}`,
                                `2023: ${context.raw.y.toFixed(3)}`,
                                `Change: ${formatChange(change)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '2018 MLI',
                        font: {
                            family: "'IBM Plex Sans', sans-serif",
                            size: 13,
                            weight: '600'
                        }
                    },
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        font: {
                            family: "'IBM Plex Mono', monospace",
                            size: 11
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '2023 MLI',
                        font: {
                            family: "'IBM Plex Sans', sans-serif",
                            size: 13,
                            weight: '600'
                        }
                    },
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        font: {
                            family: "'IBM Plex Mono', monospace",
                            size: 11
                        }
                    }
                }
            }
        },
        plugins: [{
            afterDraw: (chart) => {
                const ctx = chart.ctx;
                const xAxis = chart.scales.x;
                const yAxis = chart.scales.y;
                
                // Draw diagonal line (y = x)
                ctx.save();
                ctx.strokeStyle = '#94a3b8';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(xAxis.left, yAxis.bottom);
                ctx.lineTo(xAxis.right, yAxis.top);
                ctx.stroke();
                ctx.restore();
            }
        }]
    });
}

function setupInteractivity(data) {
    // Period tab switching
    const periodTabs = document.querySelectorAll('.period-tab');
    const periodContents = document.querySelectorAll('.period-content');
    
    periodTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const period = tab.getAttribute('data-period');
            
            // Update tabs
            periodTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update content
            periodContents.forEach(c => c.classList.remove('active'));
            document.querySelector(`.period-content[data-period="${period}"]`).classList.add('active');
        });
    });
    
    // Download button
    document.getElementById('downloadBtn').addEventListener('click', () => {
        downloadJSON(data, 'market_divergence_analysis.json');
    });
}

// Utility functions
function formatChange(value) {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
}

function downloadJSON(data, filename) {
    const dataStr = JSON.stringify(data, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function showError() {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <div style="text-align: center; padding: 60px 20px;">
            <h2 style="color: #dc2626; margin-bottom: 16px;">Error Loading Data</h2>
            <p style="color: #64748b;">Unable to load market divergence analysis. Please ensure the data file is available.</p>
        </div>
    `;
}