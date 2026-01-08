// MLI Interactive Application - Enhanced Version
// Updated for simple ratio calculation: MLI = Income / COL

class MLIApp {
    constructor() {
        this.data = null;
        this.marketData = null;
        this.currentYear = 2023;
        this.currentMetric = 'mli';
        this.selectedState = null;
        this.map = null;
        this.chart = null;
        this.availableYears = [];
        this.currentSort = 'mli';
        this.sortDirection = 'desc';
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadData();
            await this.loadMarketData(); // Load market divergence data
            this.setupEventListeners();
            this.createMap();
            this.updateStatsBanner();
            this.updateRankingsTable();
            this.updateInsights();
            this.populateStateSelectors();
            this.updateLegend();
            this.createSavingsTimeline(); // Create the savings timeline chart
            this.populateSavingsDistribution(); // Populate the distribution bars
            
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
    
    setupDraggablePanel() {
        const panel = document.getElementById('detailPanel');
        const header = panel.querySelector('.detail-header');
        let isDragging = false;
        let currentX, currentY, initialX, initialY;
        
        header.style.cursor = 'move';
        
        header.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('close-btn') || e.target.closest('.close-btn')) return;
            
            isDragging = true;
            initialX = e.clientX - (parseInt(panel.style.left) || 0);
            initialY = e.clientY - (parseInt(panel.style.top) || 0);
            
            panel.style.right = 'auto';
            panel.style.transition = 'none';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
            
            // Constrain to viewport
            const maxX = window.innerWidth - panel.offsetWidth;
            const maxY = window.innerHeight - panel.offsetHeight;
            
            currentX = Math.max(0, Math.min(currentX, maxX));
            currentY = Math.max(0, Math.min(currentY, maxY));
            
            panel.style.left = currentX + 'px';
            panel.style.top = currentY + 'px';
        });
        
        document.addEventListener('mouseup', () => {
            isDragging = false;
            panel.style.transition = '';
        });
    }
    
    setupEventListeners() {
        this.setupDraggablePanel();
        
        document.getElementById('yearSlider').addEventListener('input', (e) => {
            const index = parseInt(e.target.value);
            this.currentYear = this.availableYears[index];
            document.getElementById('yearDisplay').textContent = this.currentYear;
            this.updateMap();
            this.updateRankingsTable();
            this.updateStatsBanner();
            this.updateLegend();
        });
        
        document.getElementById('metricSelect').addEventListener('change', (e) => {
            this.currentMetric = e.target.value;
            this.updateMap();
            this.updateLegend();
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
        
        // Sortable table headers
        document.querySelectorAll('#rankingsTable th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                const sortKey = th.dataset.sort;
                
                // Toggle sort direction
                if (this.currentSort === sortKey) {
                    this.sortDirection = this.sortDirection === 'desc' ? 'asc' : 'desc';
                } else {
                    this.currentSort = sortKey;
                    this.sortDirection = 'desc';
                }
                
                // Update arrow indicators
                document.querySelectorAll('#rankingsTable th').forEach(h => {
                    h.classList.remove('sort-asc', 'sort-desc');
                });
                th.classList.add(`sort-${this.sortDirection}`);
                
                this.updateRankingsTable();
            });
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
    
    updateLegend() {
        const title = document.querySelector('.legend-title');
        const labels = document.querySelector('.legend-labels');
        const legendLabels = document.querySelectorAll('.legend-label');
        const gradientBar = document.querySelector('.gradient-bar');
        
        // Get current year data for all states
        const stateValues = Object.values(this.data.states)
            .map(s => s.timeseries[this.currentYear])
            .filter(v => v !== undefined);
        
        let minVal, maxVal, midVal;
        
        switch (this.currentMetric) {
            case 'mli':
                title.textContent = 'MLI Scale';
                
                // Remove inverted class
                gradientBar.classList.remove('inverted');
                
                // For MLI, use fixed conceptual values
                legendLabels[0].textContent = '0.8';
                legendLabels[1].textContent = '1.5';
                
                labels.innerHTML = `
                    <span>Deficit (Debt)</span>
                    <span>Break Even (1.0)</span>
                    <span>Surplus (Savings)</span>
                `;
                break;
                
            case 'surplus':
                const surplusVals = stateValues.map(v => v.surplus);
                minVal = Math.min(...surplusVals);
                maxVal = Math.max(...surplusVals);
                
                // Remove inverted class
                gradientBar.classList.remove('inverted');
                
                title.textContent = 'Annual Surplus/Deficit';
                legendLabels[0].textContent = this.formatCurrency(minVal);
                legendLabels[1].textContent = this.formatCurrency(maxVal);
                
                labels.innerHTML = `
                    <span>Large Deficit</span>
                    <span>Break Even ($0)</span>
                    <span>Large Surplus</span>
                `;
                break;
                
            case 'income':
                const incomeVals = stateValues.map(v => v.income);
                minVal = Math.min(...incomeVals);
                maxVal = Math.max(...incomeVals);
                midVal = (minVal + maxVal) / 2;
                
                // Remove inverted class
                gradientBar.classList.remove('inverted');
                
                title.textContent = 'Median Income';
                legendLabels[0].textContent = this.formatCurrency(minVal);
                legendLabels[1].textContent = this.formatCurrency(maxVal);
                
                labels.innerHTML = `
                    <span>Lowest</span>
                    <span>Middle (${this.formatCurrency(midVal)})</span>
                    <span>Highest</span>
                `;
                break;
                
            case 'col':
                const colVals = stateValues.map(v => v.col);
                minVal = Math.min(...colVals);
                maxVal = Math.max(...colVals);
                midVal = (minVal + maxVal) / 2;
                
                title.textContent = 'Cost of Living';
                legendLabels[0].textContent = this.formatCurrency(minVal);
                legendLabels[1].textContent = this.formatCurrency(maxVal);
                
                // Invert gradient for COL (lower is better)
                gradientBar.classList.add('inverted');
                
                labels.innerHTML = `
                    <span>Lowest (Best)</span>
                    <span>Middle (${this.formatCurrency(midVal)})</span>
                    <span>Highest (Worst)</span>
                `;
                break;
        }
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
        const bin = range / 6;
        
        // Use same red-yellow-green gradient as legend
        if (income < min + bin) return '#dc2626';
        if (income < min + bin * 2) return '#f97316';
        if (income < min + bin * 3) return '#eab308';
        if (income < min + bin * 4) return '#84cc16';
        if (income < min + bin * 5) return '#22c55e';
        return '#059669';
    }
    
    getCOLColor(col) {
        // Dynamic scale - inverted: lower COL = better (green)
        const yearValues = Object.values(this.data.states)
            .map(s => s.timeseries[this.currentYear]?.col)
            .filter(v => v !== undefined);
        
        const min = Math.min(...yearValues);
        const max = Math.max(...yearValues);
        const range = max - min;
        const bin = range / 6;
        
        // Inverted: High COL = red, low COL = green
        if (col > max - bin) return '#dc2626';
        if (col > max - bin * 2) return '#f97316';
        if (col > max - bin * 3) return '#eab308';
        if (col > max - bin * 4) return '#84cc16';
        if (col > max - bin * 5) return '#22c55e';
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
        console.log('showDetailPanel called for:', stateName);
        const stateData = this.data.states[stateName];
        
        if (!stateData) {
            console.error('No data found for state:', stateName);
            return;
        }
        
        const yearData = stateData.timeseries[this.currentYear];
        const latestData = stateData.latest;
        
        const panel = document.getElementById('detailPanel');
        console.log('Panel element:', panel);
        
        // Reset any drag positioning
        panel.style.left = '';
        panel.style.top = '';
        panel.style.right = '';
        
        // Show panel
        panel.style.display = 'block';
        
        // Add active class after a brief delay for transition
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                panel.classList.add('active');
            });
        });
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
        
        // Update highlight card color based on surplus/deficit
        const highlightCard = document.querySelector('.stat-card.highlight-card');
        if (yearData.surplus < 0) {
            highlightCard.classList.add('deficit');
        } else {
            highlightCard.classList.remove('deficit');
        }
        
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
        
        // Wait for transition to finish before hiding
        setTimeout(() => {
            panel.style.display = 'none';
        }, 300);
        
        this.selectedState = null;
        if (this.map) {
            this.map.classed('selected', false);
        }
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
        // Use 5-year change for the insight
        const currentYearIndex = this.availableYears.findIndex(y => y === this.currentYear);
        const fiveYearIndex = currentYearIndex - 5;
        
        if (fiveYearIndex >= 0) {
            const fiveYearsAgo = this.availableYears[fiveYearIndex];
            const currentYear = this.currentYear;
            
            const pastMLI = stateData.timeseries[fiveYearsAgo].mli;
            const currentMLI = stateData.timeseries[currentYear].mli;
            const change = currentMLI - pastMLI;
            const pctChange = ((change / pastMLI) * 100).toFixed(1);
            
            const insightEl = document.getElementById('trendInsight');
            
            if (change > 0) {
                insightEl.innerHTML = `
                    <strong>Improving:</strong> MLI increased by ${Math.abs(pctChange)}% from ${fiveYearsAgo} to ${currentYear}, 
                    from ${pastMLI.toFixed(3)} to ${currentMLI.toFixed(3)}. Purchasing power is improving.
                `;
            } else {
                insightEl.innerHTML = `
                    <strong>Declining:</strong> MLI decreased by ${Math.abs(pctChange)}% from ${fiveYearsAgo} to ${currentYear}, 
                    from ${pastMLI.toFixed(3)} to ${currentMLI.toFixed(3)}. Purchasing power is declining.
                `;
            }
        } else {
            // Fall back to full range if 5 years not available
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
    }
    
    createCostBreakdown(categories) {
        const container = document.getElementById('costBreakdown');
        const sortedCategories = Object.entries(categories)
            .sort((a, b) => b[1].cost - a[1].cost);
        
        const total = sortedCategories.reduce((sum, [_, data]) => sum + data.cost, 0);
        
        container.innerHTML = sortedCategories.map(([category, data]) => {
            const pct = (data.cost / total * 100).toFixed(1);
            // Capitalize category names properly
            const displayName = this.capitalizeCategory(category);
            return `
                <div class="cost-bar">
                    <div class="cost-label">${displayName}</div>
                    <div class="cost-bar-container">
                        <div class="cost-bar-fill" style="width: ${pct}%"></div>
                        <span class="cost-percentage">${pct}%</span>
                    </div>
                    <div class="cost-value">${this.formatCurrency(data.cost)}</div>
                </div>
            `;
        }).join('');
    }
    
    capitalizeCategory(category) {
        // Convert underscores to spaces and capitalize properly
        return category
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    updateRankingsTable(filter = 'all') {
        const statesData = Object.entries(this.data.states).map(([name, data]) => {
            const yearData = data.timeseries[this.currentYear];
            const firstYear = this.availableYears[0];
            const firstYearData = data.timeseries[firstYear];
            const change = yearData.mli - firstYearData.mli;
            
            // Calculate 5-year change (2018-2023 or current year - 5)
            const fiveYearIndex = this.availableYears.findIndex(y => y === this.currentYear) - 5;
            let change5yr = 0;
            if (fiveYearIndex >= 0) {
                const fiveYearsAgo = this.availableYears[fiveYearIndex];
                const fiveYearData = data.timeseries[fiveYearsAgo];
                if (fiveYearData) {
                    change5yr = yearData.mli - fiveYearData.mli;
                }
            }
            
            return {
                name,
                mli: yearData.mli,
                surplus: yearData.surplus,
                income: yearData.income,
                col: yearData.col,
                change,
                change5yr
            };
        });
        
        this.sortStates(statesData);
        
        let displayData = statesData;
        if (filter === 'top10') {
            displayData = statesData.slice(0, 10);
        } else if (filter === 'bottom10') {
            displayData = statesData.slice(-10).reverse();
        }
        
        const tbody = document.getElementById('rankingsBody');
        tbody.innerHTML = displayData.map((state, index) => {
            const rank = filter === 'bottom10' ? statesData.length - index : index + 1;
            const surplusClass = state.surplus >= 0 ? 'positive' : 'negative';
            const changeClass = state.change >= 0 ? 'change-positive' : 'change-negative';
            const change5yrClass = state.change5yr >= 0 ? 'change-positive' : 'change-negative';
            
            return `
                <tr onclick="app.selectStateFromTable('${state.name}')">
                    <td class="rank-cell">${rank}</td>
                    <td class="state-cell">${state.name}</td>
                    <td class="mli-cell">${state.mli.toFixed(3)}</td>
                    <td class="surplus-cell ${surplusClass}">${this.formatCurrency(state.surplus)}</td>
                    <td>${this.formatCurrency(state.income)}</td>
                    <td>${this.formatCurrency(state.col)}</td>
                    <td class="${change5yrClass}">${state.change5yr >= 0 ? '+' : ''}${state.change5yr.toFixed(3)}</td>
                    <td class="${changeClass}">${state.change >= 0 ? '+' : ''}${state.change.toFixed(3)}</td>
                </tr>
            `;
        }).join('');
    }
    
    sortStates(states) {
        const direction = this.sortDirection === 'asc' ? -1 : 1;
        
        states.sort((a, b) => {
            let aVal, bVal;
            
            switch (this.currentSort) {
                case 'name':
                    return direction * a.name.localeCompare(b.name);
                case 'rank':
                    aVal = a.mli; // rank is based on MLI
                    bVal = b.mli;
                    break;
                case 'mli':
                    aVal = a.mli;
                    bVal = b.mli;
                    break;
                case 'surplus':
                    aVal = a.surplus;
                    bVal = b.surplus;
                    break;
                case 'income':
                    aVal = a.income;
                    bVal = b.income;
                    break;
                case 'col':
                    aVal = a.col;
                    bVal = b.col;
                    break;
                case 'change5yr':
                    aVal = a.change5yr;
                    bVal = b.change5yr;
                    break;
                case 'change':
                    aVal = a.change;
                    bVal = b.change;
                    break;
                default:
                    return 0;
            }
            
            return direction * (bVal - aVal);
        });
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
            
            // Calculate 5-year change
            const currentYearIndex = this.availableYears.findIndex(y => y === this.currentYear);
            const fiveYearIndex = currentYearIndex - 5;
            let change5yr = 0;
            
            if (fiveYearIndex >= 0) {
                const fiveYearsAgo = this.availableYears[fiveYearIndex];
                const fiveYearData = data.timeseries[fiveYearsAgo];
                if (fiveYearData) {
                    change5yr = yearData.mli - fiveYearData.mli;
                }
            } else {
                // Fall back to full historical if 5 years not available
                const firstYear = this.availableYears[0];
                const firstYearData = data.timeseries[firstYear];
                change5yr = yearData.mli - firstYearData.mli;
            }
            
            return { name, mli: yearData.mli, change: change5yr };
        });
        
        statesData.sort((a, b) => b.mli - a.mli);
        const best = statesData.slice(0, 5);
        const worst = statesData.slice(-4).reverse();
        
        const improved = [...statesData].sort((a, b) => b.change - a.change).slice(0, 5);
        const declined = [...statesData].sort((a, b) => a.change - b.change).slice(0, 4);
        
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
    
    async loadMarketData() {
        try {
            const response = await fetch('market_divergence_corrected.json');
            this.marketData = await response.json();
            console.log('Loaded market divergence data');
        } catch (error) {
            console.error('Failed to load market data:', error);
            // Non-critical, continue without this data
        }
    }
    
    createSavingsTimeline() {
        if (!this.marketData || !this.marketData.savings_timeline) {
            console.log('No savings timeline data available');
            return;
        }
        
        const ctx = document.getElementById('savingsTimeline');
        if (!ctx) {
            console.log('Savings timeline canvas not found');
            return;
        }
        
        const timeline = this.marketData.savings_timeline;
        
        const years = timeline.map(d => d.year);
        const canSave = timeline.map(d => d.states_can_save);
        const paycheck = timeline.map(d => d.states_paycheck);
        const deficit = timeline.map(d => d.states_deficit);
        
        new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: years,
                datasets: [
                    {
                        label: 'Can Save (>5% surplus)',
                        data: canSave,
                        borderColor: '#059669',
                        backgroundColor: 'rgba(5, 150, 105, 0.2)',
                        borderWidth: 3,
                        tension: 0.4,
                        pointRadius: 4,
                        fill: true
                    },
                    {
                        label: 'Breaking Even (±5%)',
                        data: paycheck,
                        borderColor: '#6b7280',
                        backgroundColor: 'rgba(107, 114, 128, 0.2)',
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 3,
                        fill: true
                    },
                    {
                        label: 'In Deficit',
                        data: deficit,
                        borderColor: '#dc2626',
                        backgroundColor: 'rgba(220, 38, 38, 0.2)',
                        borderWidth: 3,
                        tension: 0.4,
                        pointRadius: 4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2.5,
                plugins: {
                    title: {
                        display: true,
                        text: 'State Distribution by Savings Capacity (2008-2023)',
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
                        beginAtZero: true,
                        max: 51,
                        title: {
                            display: true,
                            text: 'Number of States',
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
                            },
                            stepSize: 10
                        }
                    }
                }
            }
        });
    }
    
    populateSavingsDistribution() {
        if (!this.marketData || !this.marketData.current_snapshot_2023) {
            console.log('No savings distribution data available');
            return;
        }
        
        const snapshot = this.marketData.current_snapshot_2023;
        
        const surplus = snapshot.filter(s => s.status === 'Surplus').length;
        const neutral = snapshot.filter(s => s.status === 'Paycheck-to-Paycheck').length;
        const deficit = snapshot.filter(s => s.status === 'Deficit').length;
        
        const surplusEl = document.getElementById('states_surplus');
        const neutralEl = document.getElementById('states_neutral');
        const deficitEl = document.getElementById('states_deficit');
        
        if (surplusEl) surplusEl.textContent = surplus;
        if (neutralEl) neutralEl.textContent = neutral;
        if (deficitEl) deficitEl.textContent = deficit;
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