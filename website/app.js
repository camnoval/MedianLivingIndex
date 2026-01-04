// MLI Interactive Application
// Main application state and logic

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
            // Load data
            await this.loadData();
            
            // Initialize components
            this.setupEventListeners();
            this.createMap();
            this.updateRankingsTable();
            
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
            
            // Update year slider
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
        // Year slider
        document.getElementById('yearSlider').addEventListener('input', (e) => {
            const index = parseInt(e.target.value);
            this.currentYear = this.availableYears[index];
            document.getElementById('yearDisplay').textContent = this.currentYear;
            this.updateMap();
            this.updateRankingsTable();
        });
        
        // Metric selector
        document.getElementById('metricSelect').addEventListener('change', (e) => {
            this.currentMetric = e.target.value;
            this.updateMap();
        });
        
        // Detail panel close button
        document.getElementById('closeDetail').addEventListener('click', () => {
            this.closeDetailPanel();
        });
        
        // Tab controls
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.updateRankingsTable(e.target.dataset.tab);
            });
        });
        
        // Search box
        document.getElementById('searchBox').addEventListener('input', (e) => {
            this.filterTable(e.target.value);
        });
        
        // Sort selector
        document.getElementById('sortSelect').addEventListener('change', () => {
            this.updateRankingsTable();
        });
    }
    
    createMap() {
        // Set up SVG
        const svg = d3.select('#map');
        const width = 960;
        const height = 600;
        
        // Create projection
        const projection = d3.geoAlbersUsa()
            .scale(1200)
            .translate([width / 2, height / 2]);
        
        const path = d3.geoPath().projection(projection);
        
        // Load US states GeoJSON
        d3.json('https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json')
            .then(us => {
                const states = topojson.feature(us, us.objects.states);
                
                // Create state paths
                svg.selectAll('path')
                    .data(states.features)
                    .enter()
                    .append('path')
                    .attr('class', 'state-path')
                    .attr('d', path)
                    .attr('data-id', d => d.id)
                    .on('click', (event, d) => this.handleStateClick(d))
                    .on('mouseover', (event, d) => this.showTooltip(event, d))
                    .on('mousemove', (event, d) => this.moveTooltip(event))
                    .on('mouseout', () => this.hideTooltip());
                
                // Store map reference
                this.map = { svg, path, states };
                
                // Initial color update
                this.updateMap();
            })
            .catch(error => {
                console.error('Failed to load map:', error);
                this.showError('Failed to load map data');
            });
    }
    
    updateMap() {
        if (!this.map) return;
        
        const colorScale = this.getColorScale();
        
        this.map.svg.selectAll('path')
            .transition()
            .duration(500)
            .attr('fill', d => {
                const stateName = this.getStateName(d.id);
                const value = this.getMetricValue(stateName);
                return value ? colorScale(value) : '#ddd';
            });
    }
    
    getColorScale() {
        const metric = this.currentMetric;
        let domain, range;
        
        if (metric === 'mli') {
            domain = [75, 100, 125];
            range = ['#ef4444', '#fbbf24', '#10b981'];
        } else if (metric === 'income') {
            domain = [40000, 75000, 110000];
            range = ['#ef4444', '#fbbf24', '#10b981'];
        } else { // col
            domain = [8000, 12000, 20000];
            range = ['#10b981', '#fbbf24', '#ef4444'];
        }
        
        return d3.scaleLinear()
            .domain(domain)
            .range(range)
            .clamp(true);
    }
    
    getStateName(stateId) {
        // FIPS code to state name mapping
        const fipsToName = {
            '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas',
            '06': 'California', '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware',
            '12': 'Florida', '13': 'Georgia', '15': 'Hawaii', '16': 'Idaho',
            '17': 'Illinois', '18': 'Indiana', '19': 'Iowa', '20': 'Kansas',
            '21': 'Kentucky', '22': 'Louisiana', '23': 'Maine', '24': 'Maryland',
            '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota', '28': 'Mississippi',
            '29': 'Missouri', '30': 'Montana', '31': 'Nebraska', '32': 'Nevada',
            '33': 'New Hampshire', '34': 'New Jersey', '35': 'New Mexico', '36': 'New York',
            '37': 'North Carolina', '38': 'North Dakota', '39': 'Ohio', '40': 'Oklahoma',
            '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode Island', '45': 'South Carolina',
            '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas', '49': 'Utah',
            '50': 'Vermont', '51': 'Virginia', '53': 'Washington', '54': 'West Virginia',
            '55': 'Wisconsin', '56': 'Wyoming'
        };
        
        return fipsToName[stateId] || null;
    }
    
    getMetricValue(stateName) {
        if (!stateName || !this.data.states[stateName]) return null;
        
        const stateData = this.data.states[stateName].timeseries[this.currentYear];
        if (!stateData) return null;
        
        return stateData[this.currentMetric];
    }
    
    handleStateClick(feature) {
        const stateName = this.getStateName(feature.id);
        if (!stateName) return;
        
        this.selectedState = stateName;
        this.showDetailPanel(stateName);
        
        // Highlight selected state
        this.map.svg.selectAll('path').classed('selected', false);
        this.map.svg.selectAll(`path[data-id="${feature.id}"]`).classed('selected', true);
    }
    
    showTooltip(event, feature) {
        const stateName = this.getStateName(feature.id);
        if (!stateName) return;
        
        const stateData = this.data.states[stateName].timeseries[this.currentYear];
        if (!stateData) return;
        
        const tooltip = document.getElementById('tooltip');
        const metricLabels = {
            mli: 'MLI Score',
            income: 'Median Income',
            col: 'Cost of Living'
        };
        
        let value = stateData[this.currentMetric];
        if (this.currentMetric === 'income' || this.currentMetric === 'col') {
            value = '$' + value.toLocaleString();
        } else {
            value = value.toFixed(1);
        }
        
        tooltip.innerHTML = `
            <div class="tooltip-title">${stateName}</div>
            <div class="tooltip-value">${value}</div>
            <div>${metricLabels[this.currentMetric]}</div>
        `;
        
        tooltip.classList.add('visible');
    }
    
    moveTooltip(event) {
        const tooltip = document.getElementById('tooltip');
        tooltip.style.left = (event.pageX + 15) + 'px';
        tooltip.style.top = (event.pageY - 30) + 'px';
    }
    
    hideTooltip() {
        document.getElementById('tooltip').classList.remove('visible');
    }
    
    showDetailPanel(stateName) {
        const panel = document.getElementById('detailPanel');
        const stateData = this.data.states[stateName];
        const latest = stateData.latest;
        
        // Update header
        document.getElementById('stateName').textContent = stateName;
        
        // Calculate rank
        const allStates = Object.values(this.data.states)
            .map(s => ({ name: s.name, mli: s.latest.mli }))
            .sort((a, b) => b.mli - a.mli);
        const rank = allStates.findIndex(s => s.name === stateName) + 1;
        
        // Update stat cards
        document.getElementById('mliScore').textContent = latest.mli.toFixed(1);
        document.getElementById('mliRank').textContent = `#${rank} of 50`;
        document.getElementById('medianIncome').textContent = '$' + latest.income.toLocaleString();
        document.getElementById('costOfLiving').textContent = '$' + latest.col.toLocaleString();
        
        // Update trend chart
        this.updateTrendChart(stateData);
        
        // Update cost breakdown
        this.updateCostBreakdown(latest.categories);
        
        // Show panel
        panel.style.display = 'block';
        panel.scrollIntoView({ behavior: 'smooth' });
    }
    
    closeDetailPanel() {
        document.getElementById('detailPanel').style.display = 'none';
        this.selectedState = null;
        this.map.svg.selectAll('path').classed('selected', false);
    }
    
    updateTrendChart(stateData) {
        const ctx = document.getElementById('trendChart');
        
        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }
        
        // Prepare data
        const years = this.availableYears;
        const mliValues = years.map(year => stateData.timeseries[year]?.mli || null);
        const nationalAvg = years.map(year => this.data.national[year]?.avg_mli || 100);
        
        // Create chart
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: years,
                datasets: [
                    {
                        label: stateData.name,
                        data: mliValues,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'National Average',
                        data: nationalAvg,
                        borderColor: '#94a3b8',
                        borderDash: [5, 5],
                        tension: 0.3,
                        fill: false
                    }
                ]
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
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'MLI Score'
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
    
    updateCostBreakdown(categories) {
        const container = document.getElementById('costBreakdown');
        container.innerHTML = '';
        
        // Sort categories by cost
        const sorted = Object.entries(categories)
            .sort((a, b) => b[1].cost - a[1].cost)
            .slice(0, 10); // Top 10 categories
        
        const maxCost = sorted[0][1].cost;
        
        sorted.forEach(([category, data]) => {
            const percentage = (data.cost / maxCost) * 100;
            
            const bar = document.createElement('div');
            bar.className = 'cost-bar';
            bar.innerHTML = `
                <div class="cost-label">${category.replace(/_/g, ' ')}</div>
                <div class="cost-bar-container">
                    <div class="cost-bar-fill" style="width: ${percentage}%">
                        ${data.cost >= maxCost * 0.3 ? '$' + data.cost.toLocaleString() : ''}
                    </div>
                </div>
                <div class="cost-value">$${data.cost.toLocaleString()}</div>
            `;
            
            container.appendChild(bar);
        });
    }
    
    updateRankingsTable(filter = 'all') {
        const tbody = document.getElementById('rankingsBody');
        const sortSelect = document.getElementById('sortSelect');
        
        // Get all states with current year data
        let states = Object.values(this.data.states)
            .map(state => {
                const latest = state.latest;
                const first = state.timeseries[this.availableYears[0]];
                const change = latest.mli - (first?.mli || latest.mli);
                
                return {
                    name: state.name,
                    mli: latest.mli,
                    income: latest.income,
                    col: latest.col,
                    change: change
                };
            });
        
        // Apply sorting
        const sortValue = sortSelect.value;
        if (sortValue === 'mli-desc') {
            states.sort((a, b) => b.mli - a.mli);
        } else if (sortValue === 'mli-asc') {
            states.sort((a, b) => a.mli - b.mli);
        } else if (sortValue === 'name') {
            states.sort((a, b) => a.name.localeCompare(b.name));
        } else if (sortValue === 'income-desc') {
            states.sort((a, b) => b.income - a.income);
        } else if (sortValue === 'col-asc') {
            states.sort((a, b) => a.col - b.col);
        }
        
        // Apply filter
        if (filter === 'top10') {
            states = states.slice(0, 10);
        } else if (filter === 'bottom10') {
            states = states.slice(-10).reverse();
        }
        
        // Clear and rebuild table
        tbody.innerHTML = '';
        
        states.forEach((state, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="rank-cell">${index + 1}</td>
                <td class="state-cell">${state.name}</td>
                <td class="mli-cell">${state.mli.toFixed(1)}</td>
                <td>$${state.income.toLocaleString()}</td>
                <td>$${state.col.toLocaleString()}</td>
                <td class="${state.change >= 0 ? 'change-positive' : 'change-negative'}">
                    ${state.change >= 0 ? '+' : ''}${state.change.toFixed(1)}
                </td>
            `;
            
            row.addEventListener('click', () => {
                // Find the state on the map and show details
                this.showDetailPanel(state.name);
            });
            
            tbody.appendChild(row);
        });
    }
    
    filterTable(searchTerm) {
        const rows = document.querySelectorAll('#rankingsBody tr');
        const term = searchTerm.toLowerCase();
        
        rows.forEach(row => {
            const stateName = row.querySelector('.state-cell').textContent.toLowerCase();
            row.style.display = stateName.includes(term) ? '' : 'none';
        });
    }
    
    showError(message) {
        const main = document.querySelector('main');
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = 'padding: 2rem; background: #fee2e2; color: #991b1b; border-radius: 0.5rem; margin: 2rem 0;';
        errorDiv.textContent = message;
        main.insertBefore(errorDiv, main.firstChild);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mliApp = new MLIApp();
});