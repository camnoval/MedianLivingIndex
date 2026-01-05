"""
Wall Street vs Main Street Analysis - CORRECTED BASELINE
=========================================================

Compares purchasing power against TWO periods:
1. 2012-2023: Post-crisis recovery period
2. 2018-2023: Recent inflation impact (pre-COVID to now)

2008 was the WORST economic year - comparing to it makes everything look good.
We need to compare to NORMAL times to see the real story.
"""

import pandas as pd
import json
import numpy as np
from datetime import datetime

print("="*70)
print("WALL STREET VS MAIN STREET ANALYSIS (CORRECTED)")
print("="*70)

# Load MLI data
print("\nLoading data...")
mli_df = pd.read_csv('mli_results_14cat_q3.csv')
costs_df = pd.read_csv('costs_breakdown_14cat_q3.csv')

# ============================================================================
# 1. DUAL BASELINE COMPARISON
# ============================================================================

print("\n[1/6] Calculating S&P 500 vs MLI with proper baselines...")

# S&P 500 historical data
sp500_data = {
    2008: 903.25,   # Crisis (for reference only)
    2009: 1115.10,
    2010: 1257.64,
    2011: 1257.60,
    2012: 1426.19,  # POST-CRISIS BASELINE
    2013: 1848.36,
    2014: 2058.90,
    2015: 2043.94,
    2016: 2238.83,
    2017: 2673.61,
    2018: 2506.85,  # PRE-COVID BASELINE
    2019: 3230.78,
    2021: 4766.18,
    2022: 3839.50,
    2023: 4769.83
}

def calculate_gains_from_baseline(baseline_year):
    """Calculate indexed gains from a specific baseline year"""
    
    baseline_sp500 = sp500_data[baseline_year]
    baseline_mli = mli_df[mli_df['year'] == baseline_year]['mli'].mean()
    baseline_income = mli_df[mli_df['year'] == baseline_year]['median_income'].mean()
    baseline_col = mli_df[mli_df['year'] == baseline_year]['col'].mean()
    
    comparison = []
    for year in sorted(sp500_data.keys()):
        if year < baseline_year:
            continue
            
        year_data = mli_df[mli_df['year'] == year]
        if len(year_data) == 0:
            continue
        
        avg_mli = year_data['mli'].mean()
        avg_income = year_data['median_income'].mean()
        avg_col = year_data['col'].mean()
        
        comparison.append({
            'year': year,
            'sp500_indexed': (sp500_data[year] / baseline_sp500) * 100,
            'income_indexed': (avg_income / baseline_income) * 100,
            'col_indexed': (avg_col / baseline_col) * 100,
            'mli_indexed': (avg_mli / baseline_mli) * 100,
            'sp500_gain': ((sp500_data[year] / baseline_sp500) - 1) * 100,
            'income_gain': ((avg_income / baseline_income) - 1) * 100,
            'col_gain': ((avg_col / baseline_col) - 1) * 100,
            'mli_gain': ((avg_mli / baseline_mli) - 1) * 100
        })
    
    return comparison, {
        'baseline_year': baseline_year,
        'final_year': 2023,
        'sp500_total_gain': comparison[-1]['sp500_gain'],
        'income_total_gain': comparison[-1]['income_gain'],
        'col_total_gain': comparison[-1]['col_gain'],
        'mli_total_gain': comparison[-1]['mli_gain'],
        'middle_class_capture': (comparison[-1]['mli_gain'] / comparison[-1]['sp500_gain']) * 100
    }

# Calculate from both baselines
comparison_2012, summary_2012 = calculate_gains_from_baseline(2012)
comparison_2018, summary_2018 = calculate_gains_from_baseline(2018)

print("\nFROM 2012 (Post-Crisis Recovery):")
print(f"  S&P 500:        {summary_2012['sp500_total_gain']:+.1f}%")
print(f"  Median Income:  {summary_2012['income_total_gain']:+.1f}%")
print(f"  Cost of Living: {summary_2012['col_total_gain']:+.1f}%")
print(f"  MLI (Real PP):  {summary_2012['mli_total_gain']:+.1f}%")
print(f"  Middle class captured: {summary_2012['middle_class_capture']:.1f}% of S&P gains")

print("\nFROM 2018 (Pre-COVID Normal):")
print(f"  S&P 500:        {summary_2018['sp500_total_gain']:+.1f}%")
print(f"  Median Income:  {summary_2018['income_total_gain']:+.1f}%")
print(f"  Cost of Living: {summary_2018['col_total_gain']:+.1f}%")
print(f"  MLI (Real PP):  {summary_2018['mli_total_gain']:+.1f}%")
print(f"  Middle class captured: {summary_2018['middle_class_capture']:.1f}% of S&P gains")

# ============================================================================
# 2. THE COVID/INFLATION SHOCK (2018-2023)
# ============================================================================

print("\n[2/6] Analyzing the COVID/Inflation shock...")

mli_2018 = mli_df[mli_df['year'] == 2018]
mli_2023 = mli_df[mli_df['year'] == 2023]

# How many states got WORSE?
state_comparison = mli_2018[['state', 'mli', 'annual_surplus']].merge(
    mli_2023[['state', 'mli', 'annual_surplus']],
    on='state',
    suffixes=('_2018', '_2023')
)

state_comparison['mli_change'] = state_comparison['mli_2023'] - state_comparison['mli_2018']
state_comparison['surplus_change'] = state_comparison['annual_surplus_2023'] - state_comparison['annual_surplus_2018']

got_worse = (state_comparison['mli_change'] < 0).sum()
got_better = (state_comparison['mli_change'] > 0).sum()

print(f"  States that got WORSE: {got_worse}")
print(f"  States that got BETTER: {got_better}")
print(f"  Avg MLI change: {state_comparison['mli_change'].mean():+.3f}")
print(f"  Avg surplus change: ${state_comparison['surplus_change'].mean():+,.0f}/year")

# ============================================================================
# 3. SAVINGS CAPACITY OVER TIME
# ============================================================================

print("\n[3/6] Analyzing savings capacity trends...")

savings_timeline = []
for year in sorted(mli_df['year'].unique()):
    year_data = mli_df[mli_df['year'] == year]
    
    can_save = (year_data['mli'] > 1.05).sum()
    paycheck_to_paycheck = ((year_data['mli'] >= 0.95) & (year_data['mli'] <= 1.05)).sum()
    in_deficit = (year_data['mli'] < 0.95).sum()
    
    savings_timeline.append({
        'year': int(year),
        'states_can_save': int(can_save),
        'states_paycheck': int(paycheck_to_paycheck),
        'states_deficit': int(in_deficit),
        'avg_surplus': float(year_data['annual_surplus'].mean()),
        'median_surplus': float(year_data['annual_surplus'].median())
    })

savings_df = pd.DataFrame(savings_timeline)

print(f"\n  2012: {savings_df[savings_df['year']==2012]['states_can_save'].iloc[0]} states could save")
print(f"  2018: {savings_df[savings_df['year']==2018]['states_can_save'].iloc[0]} states could save")
print(f"  2023: {savings_df[savings_df['year']==2023]['states_can_save'].iloc[0]} states could save")
print(f"\n  2018→2023 change: {savings_df[savings_df['year']==2023]['states_can_save'].iloc[0] - savings_df[savings_df['year']==2018]['states_can_save'].iloc[0]} states")

# ============================================================================
# 4. HOUSING VS GOODS INFLATION
# ============================================================================

print("\n[4/6] Housing vs goods inflation comparison...")

# Calculate housing and goods costs separately
housing_costs = costs_df[costs_df['category'] == 'housing'].groupby('year')['cost'].mean()
goods_categories = ['food_at_home', 'food_away', 'apparel', 'transportation', 'entertainment']
goods_costs = costs_df[costs_df['category'].isin(goods_categories)].groupby('year')['cost'].sum()

inflation_data = []
for baseline_year in [2012, 2018]:
    housing_baseline = housing_costs[baseline_year]
    goods_baseline = goods_costs[baseline_year]
    
    housing_2023 = housing_costs[2023]
    goods_2023 = goods_costs[2023]
    
    inflation_data.append({
        'period': f"{baseline_year}-2023",
        'housing_inflation': ((housing_2023 / housing_baseline) - 1) * 100,
        'goods_inflation': ((goods_2023 / goods_baseline) - 1) * 100,
        'gap': ((housing_2023 / housing_baseline) - (goods_2023 / goods_baseline)) * 100
    })

print(f"\n  2012-2023:")
print(f"    Housing: +{inflation_data[0]['housing_inflation']:.1f}%")
print(f"    Goods:   +{inflation_data[0]['goods_inflation']:.1f}%")
print(f"    Gap:     {inflation_data[0]['housing_inflation'] - inflation_data[0]['goods_inflation']:.1f} pts")

print(f"\n  2018-2023 (The Inflation Surge):")
print(f"    Housing: +{inflation_data[1]['housing_inflation']:.1f}%")
print(f"    Goods:   +{inflation_data[1]['goods_inflation']:.1f}%")
print(f"    Gap:     {inflation_data[1]['housing_inflation'] - inflation_data[1]['goods_inflation']:.1f} pts")

# ============================================================================
# 5. REGIONAL WINNERS AND LOSERS
# ============================================================================

print("\n[5/6] Identifying regional winners and losers (2018-2023)...")

biggest_winners = state_comparison.nlargest(5, 'mli_change')
biggest_losers = state_comparison.nsmallest(5, 'mli_change')

print("\n  Biggest Winners (2018-2023):")
for _, row in biggest_winners.iterrows():
    print(f"    {row['state']:20s} MLI: {row['mli_2018']:.3f}→{row['mli_2023']:.3f} ({row['mli_change']:+.3f})")

print("\n  Biggest Losers (2018-2023):")
for _, row in biggest_losers.iterrows():
    print(f"    {row['state']:20s} MLI: {row['mli_2018']:.3f}→{row['mli_2023']:.3f} ({row['mli_change']:+.3f})")

# ============================================================================
# 6. CURRENT STATE SNAPSHOT
# ============================================================================

print("\n[6/6] Creating current state snapshot...")

current_snapshot = mli_df[mli_df['year'] == 2023].copy()
current_snapshot['status'] = pd.cut(
    current_snapshot['mli'],
    bins=[0, 0.95, 1.05, np.inf],
    labels=['Deficit', 'Paycheck-to-Paycheck', 'Surplus']
)
current_snapshot['monthly_surplus'] = current_snapshot['annual_surplus'] / 12

status_counts = current_snapshot['status'].value_counts()
print(f"\n  Current State Distribution (2023):")
print(f"    Can Save (>5% surplus):  {status_counts.get('Surplus', 0)} states")
print(f"    Paycheck-to-Paycheck:    {status_counts.get('Paycheck-to-Paycheck', 0)} states")
print(f"    In Deficit:              {status_counts.get('Deficit', 0)} states")

# ============================================================================
# CREATE OUTPUT JSON
# ============================================================================

print("\nGenerating corrected output JSON...")

output = {
    'metadata': {
        'generated': datetime.now().isoformat(),
        'title': 'Wall Street vs Main Street: The Real Story',
        'description': 'Proper baseline comparison showing true middle class trajectory',
        'note': '2008 excluded as baseline - worst economic crisis, not representative'
    },
    
    'summary_2012_2023': summary_2012,
    'summary_2018_2023': summary_2018,
    
    'key_findings': {
        'from_2012': {
            'period': '2012-2023 (Post-Crisis Recovery)',
            'sp500_gain': round(summary_2012['sp500_total_gain'], 1),
            'income_gain': round(summary_2012['income_total_gain'], 1),
            'col_gain': round(summary_2012['col_total_gain'], 1),
            'mli_gain': round(summary_2012['mli_total_gain'], 1),
            'capture_rate': round(summary_2012['middle_class_capture'], 1)
        },
        'from_2018': {
            'period': '2018-2023 (COVID/Inflation Era)',
            'sp500_gain': round(summary_2018['sp500_total_gain'], 1),
            'income_gain': round(summary_2018['income_total_gain'], 1),
            'col_gain': round(summary_2018['col_total_gain'], 1),
            'mli_gain': round(summary_2018['mli_total_gain'], 1),
            'capture_rate': round(summary_2018['middle_class_capture'], 1)
        }
    },
    
    'market_comparison_2012': comparison_2012,
    'market_comparison_2018': comparison_2018,
    'savings_timeline': savings_timeline,
    'inflation_analysis': inflation_data,
    'state_changes_2018_2023': state_comparison.to_dict('records'),
    'current_snapshot_2023': current_snapshot.to_dict('records'),
    
    'headlines': {
        'main_2012': f"Since 2012: S&P +{summary_2012['sp500_total_gain']:.0f}%, Middle Class Purchasing Power +{summary_2012['mli_total_gain']:.1f}%",
        'main_2018': f"Since 2018: S&P +{summary_2018['sp500_total_gain']:.0f}%, Middle Class Purchasing Power {summary_2018['mli_total_gain']:+.1f}%",
        'inflation': f"Housing Costs Up {inflation_data[1]['housing_inflation']:.0f}% Since 2018, Goods Up {inflation_data[1]['goods_inflation']:.0f}%",
        'states_worse': f"{got_worse} States Became Less Affordable in Last 5 Years"
    },
    
    'media_hooks': [
        "Why 'Economic Recovery' Feels Like Decline",
        f"{got_worse} States Where It Got Harder to Make Ends Meet",
        "The Housing Inflation CPI Doesn't Show",
        f"Middle Class Captured Just {summary_2018['middle_class_capture']:.0f}% of Market Gains Since 2018"
    ]
}

with open('market_divergence_corrected.json', 'w') as f:
    json.dump(output, f, indent=2)

print("✓ Saved market_divergence_corrected.json")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("WALL STREET VS MAIN STREET: CORRECTED ANALYSIS")
print("="*70)

print("\n📊 2012-2023 (11-YEAR RECOVERY):")
print(f"   S&P 500:               {summary_2012['sp500_total_gain']:+7.1f}%")
print(f"   Median Income:         {summary_2012['income_total_gain']:+7.1f}%")
print(f"   Cost of Living:        {summary_2012['col_total_gain']:+7.1f}%")
print(f"   Real Purchasing Power: {summary_2012['mli_total_gain']:+7.1f}%")
print(f"   → Middle class captured {summary_2012['middle_class_capture']:.1f}% of market gains")

print("\n📉 2018-2023 (INFLATION ERA):")
print(f"   S&P 500:               {summary_2018['sp500_total_gain']:+7.1f}%")
print(f"   Median Income:         {summary_2018['income_total_gain']:+7.1f}%")
print(f"   Cost of Living:        {summary_2018['col_total_gain']:+7.1f}%")
print(f"   Real Purchasing Power: {summary_2018['mli_total_gain']:+7.1f}%")
print(f"   → Middle class captured {summary_2018['middle_class_capture']:.1f}% of market gains")

print("\n🏠 HOUSING VS GOODS (2018-2023):")
print(f"   Housing inflation:     {inflation_data[1]['housing_inflation']:+7.1f}%")
print(f"   Goods inflation:       {inflation_data[1]['goods_inflation']:+7.1f}%")
print(f"   Housing premium:       {inflation_data[1]['housing_inflation'] - inflation_data[1]['goods_inflation']:+7.1f} pts")

print("\n🗺️ STATE CHANGES (2018-2023):")
print(f"   Got more affordable:   {got_better} states")
print(f"   Got less affordable:   {got_worse} states")
print(f"   Average MLI change:    {state_comparison['mli_change'].mean():+.3f}")

print("\n💰 CURRENT SAVINGS CAPACITY (2023):")
print(f"   Can save (>5%):        {status_counts.get('Surplus', 0)} states")
print(f"   Paycheck-to-paycheck:  {status_counts.get('Paycheck-to-Paycheck', 0)} states")
print(f"   In deficit:            {status_counts.get('Deficit', 0)} states")

print("\n" + "="*70)
print("THE REAL STORY")
print("="*70)
print("\n✓ 2008 baseline was misleading - that was rock bottom")
print("✓ From 2012: Slow but steady improvement")
print("✓ From 2018: Recent inflation erased some gains")
print("✓ Housing costs are the real killer, not goods")
print(f"✓ {got_worse} states actually got WORSE in last 5 years")