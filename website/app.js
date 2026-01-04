// MLI Interactive Application - Enhanced Version
// Updated for simple ratio calculation: MLI = Income / COL

class MLIApp {
    constructor() {
        this.data = null;
        this.currentYear = 2023;
        this.currentMetric = 'mli';
        this.selectedState = null;
        this.map = null;
        this.chart = null;
        this.availableYears = [];
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadData();
            this.setupEventListeners();
            this.createMap();
            this.updateStatsBanner();
            this.updateRankingsTable();
            this.updateInsights();
            this.populateStateSelectors();
            
            console.log('MLI App initialized successfully');
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Failed to load data. Please refresh the page.');
        }
    }
    
    async loadData() {
        try {
            const response = await fetch('mli_data.json');
            this.data = await response.json();
            this.availableYears = this.data.years;
            this.currentYear = this.availableYears[this.availableYears.length - 1];
            
            const slider = document.getElementById('yearSlider');
            slider.max = this.availableYears.length - 1;
            slider.value = this.availableYears.length - 1;
            document.getElementById('yearDisplay').textContent = this.currentYear;
            
            console.log(`Loaded data for ${Object.keys(this.data.states).length} states`);
        } catch (error) {
            throw new Error('Data loading failed: ' + error.message);
        }
    }
    
    setupEventListeners() {
        document.getElementById('yearSlider').addEventListener('input', (e) => {
            const index = parseInt(e.target.value);
            this.currentYear = this.availableYears[index];
            document.getElementById('yearDisplay').textContent = this.currentYear;
            this.updateMap();
            this.updateRankingsTable();
            this.updateStatsBanner();
        });
        
        document.getElementById('metricSelect').addEventListener('change', (e) => {
            this.currentMetric = e.target.value;
            this.updateMap();
        });
        
        document.getElementById('closeDetail').addEventListener('click', () => {
            this.closeDetailPanel();
        });
        
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.updateRankingsTable(e.target.dataset.tab);
            });
        });
        
        document.getElementById('searchBox').addEventListener('input', (e) => {
            this.filterTable(e.target.value);
        });
        
        document.getElementById('sortSelect').addEventListener('change', () => {
            this.updateRankingsTable();
        });
        
        document.getElementById('compareBtn').addEventListener('click', () => {
            this.compareStates();
        });
    }
    
    updateStatsBanner() {
        const statesData = Object.values(this.data.states).map(state => {
            const yearData = state.timeseries[this.currentYear];
            return {
                name: state.name,
                mli: yearData.mli
            };
        });
        
        const surplus = statesData.filter(s => s.mli > 1.05).length;
        const breakEven = statesData.filter(s => s.mli >= 0.95 && s.mli <= 1.05).length;
        const deficit = statesData.filter(s => s.mli < 0.95).length;
        const avgMLI = (statesData.reduce((sum, s) => sum + s.mli, 0) / statesData.length).toFixed(3);
        
        document.getElementById('surplusStates').textContent = surplus;
        document.getElementById('breakEvenStates').textContent = breakEven;
        document.getElementById('deficitStates').textContent = deficit;
        document.getElementById('nationalMLI').textContent = avgMLI;
    }
    
    populateStateSelectors() {
        const states = Object.keys(this.data.states).sort();
        const select1 = document.getElementById('compareState1');
        const select2 = document.getElementById('compareState2');
        
        states.forEach(state => {
            select1.add(new Option(state, state));
            select2.add(new Option(state, state));
        });
    }
    
    compareStates() {
        const state1 = document.getElementById('compareState1').value;
        const state2 = document.getElementById('compareState2').value;
        
        if (!state1 || !state2) {
            alert('Please select both states to compare');
            return;
        }
        
        const data1 = this.data.states[state1].timeseries[this.currentYear];
        const data2 = this.data.states[state2].timeseries[this.currentYear];
        
        const resultDiv = document.getElementById('comparisonResult');
        resultDiv.style.display = 'grid';
        resultDiv.innerHTML = `
            <div class="compare-state">
                <h3>${state1}</h3>
                <div class="compare-metric">
                    <div class="compare-label">MLI Ratio</div>
                    <div class="compare-value">${data1.mli.toFixed(3)}</div>
                </div>
                <div class="compare-metric">
                    <div class="compare-label">Surplus/Deficit</div>
                    <div class="compare-value">${this.formatCurrency(data1.surplus)}</div>
                </div>
                <div class="compare-metric">
                    <div class="compare-label">Median Income</div>
                    <div class="compare-value">${this.formatCurrency(data1.income)}</div>
                </div>
                <div class="compare-metric">
                    <div class="compare-label">Cost of Living</div>
                    <div class="compare-value">${this.formatCurrency(data1.col)}</div>
                </div>
            </div>
            <div class="compare-divider"></div>
            <div class="compare-state">
                <h3>${state2}</h3>
                <div class="compare-metric">
                    <div class="compare-label">MLI Ratio</div>
                    <div class="compare-value">${data2.mli.toFixed(3)}</div>
                </div>
                <div class="compare-metric">
                    <div class="compare-label">Surplus/Deficit</div>
                    <div class="compare-value">${this.formatCurrency(data2.surplus)}</div>
                </div>
                <div class="compare-metric">
                    <div class="compare-label">Median Income</div>
                    <div class="compare-value">${this.formatCurrency(data2.income)}</div>
                </div>
                <div class="compare-metric">
                    <div class="compare-label">Cost of Living</div>
                    <div class="compare-value">${this.formatCurrency(data2.col)}</div>
                </div>
            </div>
        `;
    }
    
    createMap() {
        const container = document.querySelector('.map-container');
        const width = container.clientWidth;
        const height = Math.max(500, width * 0.6); // Aspect ratio
        
        const svg = d3.select('#map')
            .attr('width', '100%')
            .attr('height', height)
            .attr('viewBox', `0 0 ${width} ${height}`)
            .attr('preserveAspectRatio', 'xMidYMid meet');
        
        const projection = d3.geoAlbersUsa()
            .scale(width * 1.25)
            .translate([width / 2, height / 2]);
        
        const path = d3.geoPath().projection(projection);
        
        d3.json('https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json')
            .then(us => {
                const states = topojson.feature(us, us.objects.states);
                
                this.map = svg.selectAll('path')
                    .data(states.features)
                    .join('path')
                    .attr('class', 'state-path')
                    .attr('d', path)
                    .style('cursor', 'pointer')
                    .style('pointer-events', 'all')
                    .on('mouseover', (event, d) => this.showTooltip(event, d))
                    .on('mouseout', () => this.hideTooltip())
                    .on('click', (event, d) => {
                        console.log('State clicked:', d.properties.name);
                        this.selectState(d);
                    });
                
                this.updateMap();
            });
    }
    
    updateMap() {
        if (!this.map) return;
        
        const stateNameMap = {
            'Alabama': 'Alabama', 'Alaska': 'Alaska', 'Arizona': 'Arizona',
            'Arkansas': 'Arkansas', 'California': 'California', 'Colorado': 'Colorado',
            'Connecticut': 'Connecticut', 'Delaware': 'Delaware', 'Florida': 'Florida',
            'Georgia': 'Georgia', 'Hawaii': 'Hawaii', 'Idaho': 'Idaho',
            'Illinois': 'Illinois', 'Indiana': 'Indiana', 'Iowa': 'Iowa',
            'Kansas': 'Kansas', 'Kentucky': 'Kentucky', 'Louisiana': 'Louisiana',
            'Maine': 'Maine', 'Maryland': 'Maryland', 'Massachusetts': 'Massachusetts',
            'Michigan': 'Michigan', 'Minnesota': 'Minnesota', 'Mississippi': 'Mississippi',
            'Missouri': 'Missouri', 'Montana': 'Montana', 'Nebraska': 'Nebraska',
            'Nevada': 'Nevada', 'New Hampshire': 'New Hampshire', 'New Jersey': 'New Jersey',
            'New Mexico': 'New Mexico', 'New York': 'New York', 'North Carolina': 'North Carolina',
            'North Dakota': 'North Dakota', 'Ohio': 'Ohio', 'Oklahoma': 'Oklahoma',
            'Oregon': 'Oregon', 'Pennsylvania': 'Pennsylvania', 'Rhode Island': 'Rhode Island',
            'South Carolina': 'South Carolina', 'South Dakota': 'South Dakota', 'Tennessee': 'Tennessee',
            'Texas': 'Texas', 'Utah': 'Utah', 'Vermont': 'Vermont',
            'Virginia': 'Virginia', 'Washington': 'Washington', 'West Virginia': 'West Virginia',
            'Wisconsin': 'Wisconsin', 'Wyoming': 'Wyoming'
        };
        
        this.map.attr('fill', d => {
            const stateName = d.properties.name;
            const stateData = this.data.states[stateName];
            
            if (!stateData) return '#ccc';
            
            const yearData = stateData.timeseries[this.currentYear];
            if (!yearData) return '#ccc';
            
            let value;
            switch (this.currentMetric) {
                case 'mli':
                    value = yearData.mli;
                    return this.getMLIColor(value);
                case 'surplus':
                    value = yearData.surplus;
                    return this.getSurplusColor(value);
                case 'income':
                    value = yearData.income;
                    return this.getIncomeColor(value);
                case 'col':
                    value = yearData.col;
                    return this.getCOLColor(value);
                default:
                    return '#ccc';
            }
        });
    }
    getMLIColor(mli) {
        // MLI thresholds are conceptual and fixed - 1.0 = break even
        if (mli < 0.9) return '#dc2626';   // Deep deficit (>10%)
        if (mli < 0.95) return '#f97316';  // Deficit (5-10%)
        if (mli < 1.0) return '#eab308';   // Near break-even (0-5% deficit)
        if (mli < 1.1) return '#84cc16';   // Small surplus (0-10%)
        if (mli < 1.2) return '#22c55e';   // Good surplus (10-20%)
        return '#059669';                   // Large surplus (>20%)
    }
    
    getSurplusColor(surplus) {
        // Dynamic scale based on current year data
        const yearValues = Object.values(this.data.states)
            .map(s => s.timeseries[this.currentYear]?.surplus)
            .filter(v => v !== undefined);
        
        const min = Math.min(...yearValues);
        const max = Math.max(...yearValues);
        const range = max - min;
        const bin = range / 6;
        
        if (surplus < min + bin) return '#dc2626';
        if (surplus < min + bin * 2) return '#f97316';
        if (surplus < min + bin * 3) return '#eab308';
        if (surplus < min + bin * 4) return '#84cc16';
        if (surplus < min + bin * 5) return '#22c55e';
        return '#059669';
    }
    
    getIncomeColor(income) {
        // Dynamic scale based on current year data
        const yearValues = Object.values(this.data.states)
            .map(s => s.timeseries[this.currentYear]?.income)
            .filter(v => v !== undefined);
        
        const min = Math.min(...yearValues);
        const max = Math.max(...yearValues);
        const range = max - min;
        const bin = range / 5;
        
        if (income < min + bin) return '#fef2f2';
        if (income < min + bin * 2) return '#fef9c3';
        if (income < min + bin * 3) return '#d1fae5';
        if (income < min + bin * 4) return '#a7f3d0';
        return '#6ee7b7';
    }
    
    getCOLColor(col) {
        // Dynamic scale - inverted: lower COL = better (green)
        const yearValues = Object.values(this.data.states)
            .map(s => s.timeseries[this.currentYear]?.col)
            .filter(v => v !== undefined);
        
        const min = Math.min(...yearValues);
        const max = Math.max(...yearValues);
        const range = max - min;
        const bin = range / 5;
        
        // High COL = red, low COL = green
        if (col > max - bin) return '#dc2626';
        if (col > max - bin * 2) return '#f97316';
        if (col > max - bin * 3) return '#eab308';
        if (col > max - bin * 4) return '#84cc16';
        return '#059669';
    }
    
    showTooltip(event, d) {
        const stateName = d.properties.name;
        const stateData = this.data.states[stateName];
        
        if (!stateData) return;
        
        const yearData = stateData.timeseries[this.currentYear];
        const tooltip = document.getElementById('tooltip');
        
        let content = `<div class="tooltip-title">${stateName}</div>`;
        
        switch (this.currentMetric) {
            case 'mli':
                const interpretation = this.getMLIInterpretation(yearData.mli);
                content += `
                    <div class="tooltip-value">${yearData.mli.toFixed(3)}</div>
                    <div class="tooltip-detail">${interpretation}</div>
                `;
                break;
            case 'surplus':
                content += `
                    <div class="tooltip-value">${this.formatCurrency(yearData.surplus)}</div>
                    <div class="tooltip-detail">${yearData.surplus >= 0 ? 'Annual surplus' : 'Annual deficit'}</div>
                `;
                break;
            case 'income':
                content += `<div class="tooltip-value">${this.formatCurrency(yearData.income)}</div>`;
                break;
            case 'col':
                content += `<div class="tooltip-value">${this.formatCurrency(yearData.col)}</div>`;
                break;
        }
        
        tooltip.innerHTML = content;
        tooltip.classList.add('visible');
        tooltip.style.left = event.pageX + 10 + 'px';
        tooltip.style.top = event.pageY + 10 + 'px';
    }
    
    hideTooltip() {
        document.getElementById('tooltip').classList.remove('visible');
    }
    
    getMLIInterpretation(mli) {
        if (mli < 0.95) {
            const deficit = ((1.0 - mli) * 100).toFixed(0);
            return `${deficit}% deficit`;
        } else if (mli > 1.05) {
            const surplus = ((mli - 1.0) * 100).toFixed(0);
            return `${surplus}% surplus`;
        } else {
            return 'Break even';
        }
    }
    
    selectState(d) {
        const stateName = d.properties.name;
        this.selectedState = stateName;
        this.showDetailPanel(stateName);
        
        this.map.classed('selected', false);
        d3.select(event.currentTarget).classed('selected', true);
    }
    
    showDetailPanel(stateName) {
        const stateData = this.data.states[stateName];
        const yearData = stateData.timeseries[this.currentYear];
        const latestData = stateData.latest;
        
        const panel = document.getElementById('detailPanel');
        panel.style.display = 'block';
        setTimeout(() => panel.classList.add('active'), 10);
        document.getElementById('stateName').textContent = stateName;
        
        const ranking = this.getStateRanking(stateName);
        
        document.getElementById('mliScore').textContent = yearData.mli.toFixed(3);
        document.getElementById('mliRank').textContent = `#${ranking} of 50`;
        
        const interpEl = document.getElementById('mliInterpretation');
        interpEl.textContent = this.getMLIInterpretation(yearData.mli);
        interpEl.className = 'stat-interpretation';
        if (yearData.mli > 1.05) {
            interpEl.classList.add('surplus');
        } else if (yearData.mli < 0.95) {
            interpEl.classList.add('deficit');
        } else {
            interpEl.classList.add('breakeven');
        }
        
        document.getElementById('medianIncome').textContent = this.formatCurrency(yearData.income);
        document.getElementById('costOfLiving').textContent = this.formatCurrency(yearData.col);
        
        const surplusEl = document.getElementById('annualSurplus');
        surplusEl.textContent = this.formatCurrency(yearData.surplus);
        surplusEl.style.color = yearData.surplus >= 0 ? 'var(--green)' : 'var(--red)';
        
        const surplusLabel = document.getElementById('surplusLabel');
        surplusLabel.textContent = yearData.surplus >= 0 ? 'Available for savings' : 'Annual shortfall';
        
        this.createTrendChart(stateData);
        this.createCostBreakdown(latestData.categories);
        this.createTrendInsight(stateData);
        
        setTimeout(() => {
            document.getElementById('detailPanel').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }
    
    closeDetailPanel() {
        const panel = document.getElementById('detailPanel');
        panel.classList.remove('active');
        setTimeout(() => panel.style.display = 'none', 300);
        this.selectedState = null;
        this.map.classed('selected', false);
    }
    
    getStateRanking(stateName) {
        const statesData = Object.entries(this.data.states).map(([name, data]) => ({
            name,
            mli: data.timeseries[this.currentYear].mli
        }));
        
        statesData.sort((a, b) => b.mli - a.mli);
        return statesData.findIndex(s => s.name === stateName) + 1;
    }
    
    createTrendChart(stateData) {
        const canvas = document.getElementById('trendChart');
        const ctx = canvas.getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }
        
        const years = this.availableYears;
        const mliData = years.map(year => stateData.timeseries[year].mli);
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: years,
                datasets: [{
                    label: 'MLI Ratio',
                    data: mliData,
                    borderColor: '#0d9488',
                    backgroundColor: 'rgba(13, 148, 136, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }, {
                    label: 'Break Even (1.0)',
                    data: years.map(() => 1.0),
                    borderColor: '#f97316',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                if (context.datasetIndex === 0) {
                                    return `MLI: ${context.parsed.y.toFixed(3)}`;
                                }
                                return 'Break Even';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'MLI Ratio'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    }
                }
            }
        });
    }
    
    createTrendInsight(stateData) {
        const firstYear = this.availableYears[0];
        const lastYear = this.availableYears[this.availableYears.length - 1];
        
        const firstMLI = stateData.timeseries[firstYear].mli;
        const lastMLI = stateData.timeseries[lastYear].mli;
        const change = lastMLI - firstMLI;
        const pctChange = ((change / firstMLI) * 100).toFixed(1);
        
        const insightEl = document.getElementById('trendInsight');
        
        if (change > 0) {
            insightEl.innerHTML = `
                <strong>Improving:</strong> MLI increased by ${Math.abs(pctChange)}% from ${firstYear} to ${lastYear}, 
                from ${firstMLI.toFixed(3)} to ${lastMLI.toFixed(3)}. Purchasing power is improving.
            `;
        } else {
            insightEl.innerHTML = `
                <strong>Declining:</strong> MLI decreased by ${Math.abs(pctChange)}% from ${firstYear} to ${lastYear}, 
                from ${firstMLI.toFixed(3)} to ${lastMLI.toFixed(3)}. Purchasing power is declining.
            `;
        }
    }
    
    createCostBreakdown(categories) {
        const container = document.getElementById('costBreakdown');
        const sortedCategories = Object.entries(categories)
            .sort((a, b) => b[1].cost - a[1].cost);
        
        const total = sortedCategories.reduce((sum, [_, data]) => sum + data.cost, 0);
        
        container.innerHTML = sortedCategories.map(([category, data]) => {
            const pct = (data.cost / total * 100).toFixed(1);
            return `
                <div class="cost-bar">
                    <div class="cost-label">${category}</div>
                    <div class="cost-bar-container">
                        <div class="cost-bar-fill" style="width: ${pct}%">
                            ${pct}%
                        </div>
                    </div>
                    <div class="cost-value">${this.formatCurrency(data.cost)}</div>
                </div>
            `;
        }).join('');
    }
    
    updateRankingsTable(filter = 'all') {
        const statesData = Object.entries(this.data.states).map(([name, data]) => {
            const yearData = data.timeseries[this.currentYear];
            const firstYear = this.availableYears[0];
            const firstYearData = data.timeseries[firstYear];
            const change = yearData.mli - firstYearData.mli;
            
            return {
                name,
                mli: yearData.mli,
                surplus: yearData.surplus,
                income: yearData.income,
                col: yearData.col,
                change
            };
        });
        
        const sortValue = document.getElementById('sortSelect').value;
        this.sortStates(statesData, sortValue);
        
        let displayData = statesData;
        if (filter === 'top10') {
            displayData = statesData.slice(0, 10);
        } else if (filter === 'bottom10') {
            displayData = statesData.slice(-10).reverse();
        }
        
        const tbody = document.getElementById('rankingsBody');
        tbody.innerHTML = displayData.map((state, index) => {
            const rank = filter === 'bottom10' ? statesData.length - 9 + index : index + 1;
            const surplusClass = state.surplus >= 0 ? 'positive' : 'negative';
            const changeClass = state.change >= 0 ? 'change-positive' : 'change-negative';
            
            return `
                <tr onclick="app.selectStateFromTable('${state.name}')">
                    <td class="rank-cell">${rank}</td>
                    <td class="state-cell">${state.name}</td>
                    <td class="mli-cell">${state.mli.toFixed(3)}</td>
                    <td class="surplus-cell ${surplusClass}">${this.formatCurrency(state.surplus)}</td>
                    <td>${this.formatCurrency(state.income)}</td>
                    <td>${this.formatCurrency(state.col)}</td>
                    <td class="${changeClass}">${state.change >= 0 ? '+' : ''}${state.change.toFixed(3)}</td>
                </tr>
            `;
        }).join('');
    }
    
    sortStates(states, sortValue) {
        switch (sortValue) {
            case 'mli-desc':
                states.sort((a, b) => b.mli - a.mli);
                break;
            case 'mli-asc':
                states.sort((a, b) => a.mli - b.mli);
                break;
            case 'name':
                states.sort((a, b) => a.name.localeCompare(b.name));
                break;
            case 'surplus-desc':
                states.sort((a, b) => b.surplus - a.surplus);
                break;
            case 'income-desc':
                states.sort((a, b) => b.income - a.income);
                break;
            case 'col-asc':
                states.sort((a, b) => a.col - b.col);
                break;
        }
    }
    
    selectStateFromTable(stateName) {
        const stateFeature = { properties: { name: stateName } };
        this.selectedState = stateName;
        this.showDetailPanel(stateName);
    }
    
    filterTable(searchTerm) {
        const rows = document.querySelectorAll('#rankingsBody tr');
        const term = searchTerm.toLowerCase();
        
        rows.forEach(row => {
            const stateName = row.querySelector('.state-cell').textContent.toLowerCase();
            row.style.display = stateName.includes(term) ? '' : 'none';
        });
    }
    
    updateInsights() {
        const statesData = Object.entries(this.data.states).map(([name, data]) => {
            const yearData = data.timeseries[this.currentYear];
            const firstYear = this.availableYears[0];
            const firstYearData = data.timeseries[firstYear];
            const change = yearData.mli - firstYearData.mli;
            
            return { name, mli: yearData.mli, change };
        });
        
        statesData.sort((a, b) => b.mli - a.mli);
        const best = statesData.slice(0, 5);
        const worst = statesData.slice(-5).reverse();
        
        const improved = [...statesData].sort((a, b) => b.change - a.change).slice(0, 5);
        const declined = [...statesData].sort((a, b) => a.change - b.change).slice(0, 5);
        
        document.getElementById('bestStates').innerHTML = '<ul>' + 
            best.map(s => `<li><strong>${s.name}:</strong> ${s.mli.toFixed(3)}</li>`).join('') + 
            '</ul>';
        
        document.getElementById('worstStates').innerHTML = '<ul>' + 
            worst.map(s => `<li><strong>${s.name}:</strong> ${s.mli.toFixed(3)}</li>`).join('') + 
            '</ul>';
        
        document.getElementById('improvedStates').innerHTML = '<ul>' + 
            improved.map(s => `<li><strong>${s.name}:</strong> +${s.change.toFixed(3)}</li>`).join('') + 
            '</ul>';
        
        document.getElementById('declinedStates').innerHTML = '<ul>' + 
            declined.map(s => `<li><strong>${s.name}:</strong> ${s.change.toFixed(3)}</li>`).join('') + 
            '</ul>';
    }
    
    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }
    
    showError(message) {
        const main = document.querySelector('main');
        main.innerHTML = `
            <section class="intro">
                <h2>Error</h2>
                <p>${message}</p>
            </section>
        `;
    }
}

// Initialize app when DOM is ready
const app = new MLIApp();