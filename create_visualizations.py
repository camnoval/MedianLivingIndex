"""
MLI Visualization Suite - Media-Ready Charts
============================================

Creates 6 high-impact visualizations for media launch:
1. MLI Rankings (2023) - Bar chart
2. MLI Heatmap Over Time - State evolution
3. Component Breakdown - California vs Texas vs Mississippi
4. MLI Change Map 2008→2023 - Geographic patterns
5. Income vs Cost Growth - Scatter plot
6. Income Class Comparison - Q2 vs Q3 vs Q4

All charts optimized for social media sharing and policy briefs.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap

# Set publication-quality style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica']
plt.rcParams['font.size'] = 10

# Load data
print("Loading MLI results...")
mli_df = pd.read_csv('mli_results_14cat_q3.csv')
costs_df = pd.read_csv('costs_breakdown_14cat_q3.csv')

print(f"Loaded {len(mli_df)} MLI observations")
print(f"Loaded {len(costs_df)} cost observations")

# ============================================================================
# CHART 1: MLI RANKINGS 2023 - Top 10 Best & Worst
# ============================================================================

def create_rankings_chart():
    """Create compelling top/bottom 10 rankings for 2023"""
    
    print("\n[1/6] Creating rankings chart...")
    
    mli_2023 = mli_df[mli_df['year'] == 2023].sort_values('mli', ascending=False)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))
    
    # Top 10
    top10 = mli_2023.head(10).iloc[::-1]  # Reverse for better visual
    colors_top = plt.cm.Greens(np.linspace(0.4, 0.9, 10))
    ax1.barh(range(10), top10['mli'], color=colors_top)
    ax1.set_yticks(range(10))
    ax1.set_yticklabels(top10['state'])
    ax1.set_xlabel('MLI Score (Higher = Better Affordability)', fontsize=12, fontweight='bold')
    ax1.set_title('Top 10 Most Affordable States (2023)', fontsize=14, fontweight='bold')
    ax1.axvline(x=100, color='gray', linestyle='--', alpha=0.5, label='National Average')
    
    # Add values on bars
    for i, (idx, row) in enumerate(top10.iterrows()):
        ax1.text(row['mli'] + 0.5, i, f"{row['mli']:.1f}", va='center', fontsize=9)
    
    # Bottom 10
    bottom10 = mli_2023.tail(10)
    colors_bottom = plt.cm.Reds(np.linspace(0.4, 0.9, 10))
    ax2.barh(range(10), bottom10['mli'], color=colors_bottom)
    ax2.set_yticks(range(10))
    ax2.set_yticklabels(bottom10['state'])
    ax2.set_xlabel('MLI Score (Lower = Worse Affordability)', fontsize=12, fontweight='bold')
    ax2.set_title('Bottom 10 Least Affordable States (2023)', fontsize=14, fontweight='bold')
    ax2.axvline(x=100, color='gray', linestyle='--', alpha=0.5, label='National Average')
    
    # Add values on bars
    for i, (idx, row) in enumerate(bottom10.iterrows()):
        ax2.text(row['mli'] + 0.5, i, f"{row['mli']:.1f}", va='center', fontsize=9)
    
    plt.suptitle('Median Living Index State Rankings 2023\nHigher Score = Better Purchasing Power for Median Households', 
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('viz_1_rankings_2023.png', bbox_inches='tight', dpi=300)
    print("  ✓ Saved: viz_1_rankings_2023.png")
    plt.close()


# ============================================================================
# CHART 2: MLI HEATMAP OVER TIME
# ============================================================================

def create_heatmap():
    """Create heatmap showing MLI evolution 2008-2023"""
    
    print("\n[2/6] Creating heatmap...")
    
    # Pivot data
    pivot = mli_df.pivot(index='state', columns='year', values='mli')
    
    # Sort by 2023 MLI
    pivot = pivot.sort_values(2023, ascending=False)
    
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Custom diverging colormap (red=bad, white=100, green=good)
    colors = ['#d73027', '#fc8d59', '#fee090', '#ffffff', '#e0f3f8', '#91bfdb', '#4575b4']
    n_bins = 100
    cmap = LinearSegmentedColormap.from_list('mli', colors, N=n_bins)
    
    # Create heatmap
    im = ax.imshow(pivot.values, cmap=cmap, aspect='auto', vmin=75, vmax=125)
    
    # Set ticks
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=8)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('MLI Score', rotation=270, labelpad=20, fontsize=12, fontweight='bold')
    
    # Add title
    ax.set_title('Median Living Index Evolution (2008-2023)\nDarker Red = Declining Affordability | Darker Blue = Improving Affordability',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax.set_ylabel('State', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('viz_2_heatmap_timeline.png', bbox_inches='tight', dpi=300)
    print("  ✓ Saved: viz_2_heatmap_timeline.png")
    plt.close()


# ============================================================================
# CHART 3: COMPONENT BREAKDOWN - 3 States
# ============================================================================

def create_component_breakdown():
    """Compare cost components across California, Texas, Mississippi"""
    
    print("\n[3/6] Creating component breakdown...")
    
    states = ['California', 'Texas', 'Mississippi']
    costs_2023 = costs_df[costs_df['year'] == 2023]
    
    # Get top 5 categories by cost for each state
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    
    for idx, state in enumerate(states):
        state_costs = costs_2023[costs_2023['state'] == state].sort_values('cost', ascending=False).head(6)
        
        # Calculate percentages
        total = state_costs['cost'].sum()
        state_costs['pct'] = (state_costs['cost'] / total) * 100
        
        # Create bar chart
        colors = plt.cm.Set3(range(len(state_costs)))
        bars = axes[idx].barh(range(len(state_costs)), state_costs['cost'], color=colors)
        axes[idx].set_yticks(range(len(state_costs)))
        axes[idx].set_yticklabels(state_costs['category'].str.replace('_', ' ').str.title())
        axes[idx].set_xlabel('Annual Cost ($)', fontsize=11, fontweight='bold')
        axes[idx].set_title(f'{state}\nTotal: ${total:,.0f}/year', fontsize=12, fontweight='bold')
        
        # Add value labels with percentages
        for i, (_, row) in enumerate(state_costs.iterrows()):
            axes[idx].text(row['cost'] + 500, i, f"${row['cost']:,.0f} ({row['pct']:.1f}%)", 
                          va='center', fontsize=9)
    
    plt.suptitle('Cost of Living Breakdown (2023): California vs Texas vs Mississippi\nMiddle Class Household Spending Patterns',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('viz_3_component_breakdown.png', bbox_inches='tight', dpi=300)
    print("  ✓ Saved: viz_3_component_breakdown.png")
    plt.close()


# ============================================================================
# CHART 4: MLI CHANGE MAP (Conceptual - shows top changers)
# ============================================================================

def create_change_analysis():
    """Show states with biggest MLI changes 2008→2023"""
    
    print("\n[4/6] Creating change analysis...")
    
    mli_2008 = mli_df[mli_df['year'] == 2008].set_index('state')['mli']
    mli_2023 = mli_df[mli_df['year'] == 2023].set_index('state')['mli']
    
    changes = (mli_2023 - mli_2008).sort_values()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 10))
    
    # Biggest declines
    declines = changes.head(15)
    colors_decline = plt.cm.Reds(np.linspace(0.4, 0.9, 15))
    ax1.barh(range(15), declines.values, color=colors_decline)
    ax1.set_yticks(range(15))
    ax1.set_yticklabels(declines.index)
    ax1.set_xlabel('MLI Change (points)', fontsize=12, fontweight='bold')
    ax1.set_title('Biggest Affordability Declines\n2008 → 2023', fontsize=13, fontweight='bold')
    ax1.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    
    for i, val in enumerate(declines.values):
        ax1.text(val - 0.5, i, f"{val:.1f}", va='center', ha='right', fontsize=9, color='white', fontweight='bold')
    
    # Biggest improvements  
    improvements = changes.tail(15).iloc[::-1]
    colors_improve = plt.cm.Greens(np.linspace(0.4, 0.9, 15))
    ax2.barh(range(15), improvements.values, color=colors_improve)
    ax2.set_yticks(range(15))
    ax2.set_yticklabels(improvements.index)
    ax2.set_xlabel('MLI Change (points)', fontsize=12, fontweight='bold')
    ax2.set_title('Biggest Affordability Improvements\n2008 → 2023', fontsize=13, fontweight='bold')
    ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    
    for i, val in enumerate(improvements.values):
        ax2.text(val + 0.5, i, f"{val:.1f}", va='center', fontsize=9, fontweight='bold')
    
    plt.suptitle('Which States Got More/Less Affordable? (2008-2023)',
                 fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('viz_4_mli_changes.png', bbox_inches='tight', dpi=300)
    print("  ✓ Saved: viz_4_mli_changes.png")
    plt.close()


# ============================================================================
# CHART 5: INCOME VS COST GROWTH SCATTER
# ============================================================================

def create_income_vs_cost_scatter():
    """Scatter plot: Did income growth keep pace with cost growth?"""
    
    print("\n[5/6] Creating income vs cost scatter...")
    
    # Calculate growth rates
    data_2008 = mli_df[mli_df['year'] == 2008][['state', 'median_income', 'col_index']].set_index('state')
    data_2023 = mli_df[mli_df['year'] == 2023][['state', 'median_income', 'col_index']].set_index('state')
    
    income_growth = ((data_2023['median_income'] / data_2008['median_income']) - 1) * 100
    cost_growth = ((data_2023['col_index'] / data_2008['col_index']) - 1) * 100
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Create scatter
    scatter = ax.scatter(income_growth, cost_growth, s=100, alpha=0.6, c=data_2023.index.map(lambda x: 1), cmap='viridis')
    
    # Add diagonal line (kept pace)
    max_val = max(income_growth.max(), cost_growth.max())
    min_val = min(income_growth.min(), cost_growth.min())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Income = Cost Growth (Kept Pace)', alpha=0.7)
    
    # Shade regions
    ax.fill_between([min_val, max_val], [min_val, max_val], max_val, alpha=0.1, color='red', label='Fell Behind (Cost > Income)')
    ax.fill_between([min_val, max_val], min_val, [min_val, max_val], alpha=0.1, color='green', label='Got Ahead (Income > Cost)')
    
    # Label interesting states
    interesting = ['California', 'Florida', 'Texas', 'Vermont', 'Alaska', 'Mississippi']
    for state in interesting:
        if state in income_growth.index:
            ax.annotate(state, 
                       (income_growth[state], cost_growth[state]),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))
    
    ax.set_xlabel('Income Growth 2008-2023 (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cost of Living Growth 2008-2023 (%)', fontsize=12, fontweight='bold')
    ax.set_title('Did Income Keep Pace with Cost of Living?\nStates Above Red Line Fell Behind', 
                 fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('viz_5_income_vs_cost_growth.png', bbox_inches='tight', dpi=300)
    print("  ✓ Saved: viz_5_income_vs_cost_growth.png")
    plt.close()


# ============================================================================
# CHART 6: INCOME CLASS COMPARISON
# ============================================================================

def create_income_class_comparison():
    """Compare Q2, Q3, Q4 MLI trends if data available"""
    
    print("\n[6/6] Creating income class comparison...")
    
    # Try to load other quintiles
    try:
        mli_q2 = pd.read_csv('mli_results_14cat_q2.csv')
        mli_q4 = pd.read_csv('mli_results_14cat_q4.csv')
        has_quintiles = True
    except:
        print("  Note: Q2/Q4 data not found, showing Q3 trends by state instead")
        has_quintiles = False
    
    if has_quintiles:
        # Plot national average for each quintile
        fig, ax = plt.subplots(figsize=(12, 7))
        
        for quintile, df, label, color in [
            ('Q2', mli_q2, 'Lower-Middle Class (Q2)', '#e41a1c'),
            ('Q3', mli_df, 'Middle Class (Q3)', '#377eb8'),
            ('Q4', mli_q4, 'Upper-Middle Class (Q4)', '#4daf4a')
        ]:
            national_avg = df.groupby('year')['mli'].mean()
            ax.plot(national_avg.index, national_avg.values, marker='o', linewidth=2.5, label=label, color=color)
        
        ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='National Average Baseline')
        ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax.set_ylabel('Average MLI Score', fontsize=12, fontweight='bold')
        ax.set_title('How Different Income Classes Fared Over Time\nNational Averages by Quintile',
                     fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
    else:
        # Show Q3 trends for select states
        fig, ax = plt.subplots(figsize=(12, 7))
        
        states = ['California', 'Texas', 'Florida', 'North Dakota', 'Vermont']
        colors = plt.cm.Set1(range(len(states)))
        
        for state, color in zip(states, colors):
            state_data = mli_df[mli_df['state'] == state]
            ax.plot(state_data['year'], state_data['mli'], marker='o', linewidth=2, label=state, color=color)
        
        ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='National Average')
        ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax.set_ylabel('MLI Score', fontsize=12, fontweight='bold')
        ax.set_title('MLI Trends: Select States (2008-2023)\nMiddle Class Affordability Over Time',
                     fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('viz_6_trends_comparison.png', bbox_inches='tight', dpi=300)
    print("  ✓ Saved: viz_6_trends_comparison.png")
    plt.close()


# ============================================================================
# RUN ALL VISUALIZATIONS
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("CREATING MLI VISUALIZATION SUITE")
    print("="*70)
    
    create_rankings_chart()
    create_heatmap()
    create_component_breakdown()
    create_change_analysis()
    create_income_vs_cost_scatter()
    create_income_class_comparison()
    
    print("\n" + "="*70)
    print("ALL VISUALIZATIONS COMPLETE!")
    print("="*70)
    print("\nGenerated files:")
    print("  1. viz_1_rankings_2023.png")
    print("  2. viz_2_heatmap_timeline.png")
    print("  3. viz_3_component_breakdown.png")
    print("  4. viz_4_mli_changes.png")
    print("  5. viz_5_income_vs_cost_growth.png")
    print("  6. viz_6_trends_comparison.png")
    print("\nThese are publication-ready and optimized for social media!")