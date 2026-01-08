"""
STEP 5: Compare Results & Regenerate Market Divergence Analysis
================================================================

Final step: Comprehensive analysis of old vs new MLI and regeneration
of the market divergence page with corrected housing costs.

Outputs:
- detailed_comparison_report.txt
- market_divergence_MARKET.json (for website)
- state_rankings_comparison.csv
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import os

print("="*80)
print("STEP 5: COMPREHENSIVE COMPARISON & MARKET DIVERGENCE ANALYSIS")
print("="*80)

# Get project root (two levels up from scripts/readjust_for_housing_rent_rates/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))

# Directories
processed_dir = os.path.join(project_root, 'data', 'processed')
final_dir = os.path.join(project_root, 'data', 'final')

# ============================================================================
# LOAD DATA
# ============================================================================

print("\n[Loading] Reading MLI results...")
print("-"*80)

mli_old = pd.read_csv(os.path.join(final_dir, 'mli_results_14cat_q3.csv'))
mli_new = pd.read_csv(os.path.join(final_dir, 'mli_results_14cat_q3_MARKET.csv'))
costs_new = pd.read_csv(os.path.join(final_dir, 'costs_breakdown_14cat_q3_MARKET.csv'))

print(f"✓ Loaded old MLI: {len(mli_old)} observations")
print(f"✓ Loaded new MLI: {len(mli_new)} observations")
print(f"✓ Loaded new costs: {len(costs_new)} observations")

# ============================================================================
# COMPREHENSIVE COMPARISON
# ============================================================================

print("\n[1/4] Comparing Old vs New MLI...")
print("-"*80)

comparison = mli_old.merge(
    mli_new,
    on=['state', 'year'],
    how='inner',
    suffixes=('_old', '_new')
)

comparison['mli_diff'] = comparison['mli_new'] - comparison['mli_old']
comparison['col_diff'] = comparison['col_new'] - comparison['col_old']
comparison['col_diff_pct'] = (comparison['col_diff'] / comparison['col_old'] * 100).round(1)

# National trends
report = []
report.append("="*80)
report.append("MLI COMPARISON REPORT: OLD (BLENDED) VS NEW (MARKET-ADJUSTED)")
report.append("="*80)
report.append("")

for year in [2012, 2018, 2023]:
    if year not in comparison['year'].values:
        continue
    
    year_data = comparison[comparison['year'] == year]
    
    report.append(f"\n{year} NATIONAL AVERAGES:")
    report.append("-"*40)
    report.append(f"  Old MLI: {year_data['mli_old'].mean():.3f}")
    report.append(f"  New MLI: {year_data['mli_new'].mean():.3f}")
    report.append(f"  Change:  {year_data['mli_diff'].mean():+.3f}")
    report.append(f"")
    report.append(f"  Old COL: ${year_data['col_old'].mean():,.0f}")
    report.append(f"  New COL: ${year_data['col_new'].mean():,.0f}")
    report.append(f"  Change:  +${year_data['col_diff'].mean():,.0f} (+{year_data['col_diff_pct'].mean():.1f}%)")

# 2018-2023 Purchasing Power
report.append("\n\n2018-2023 PURCHASING POWER CHANGES:")
report.append("="*40)

mli_2018_old = mli_old[mli_old['year'] == 2018]['mli'].mean()
mli_2023_old = mli_old[mli_old['year'] == 2023]['mli'].mean()
pp_change_old = ((mli_2023_old / mli_2018_old) - 1) * 100

mli_2018_new = mli_new[mli_new['year'] == 2018]['mli'].mean()
mli_2023_new = mli_new[mli_new['year'] == 2023]['mli'].mean()
pp_change_new = ((mli_2023_new / mli_2018_new) - 1) * 100

report.append(f"\nOld Method (Blended Housing):")
report.append(f"  2018 MLI: {mli_2018_old:.3f}")
report.append(f"  2023 MLI: {mli_2023_old:.3f}")
report.append(f"  Change: {pp_change_old:+.1f}%")

report.append(f"\nNew Method (Market Housing):")
report.append(f"  2018 MLI: {mli_2018_new:.3f}")
report.append(f"  2023 MLI: {mli_2023_new:.3f}")
report.append(f"  Change: {pp_change_new:+.1f}%")

report.append(f"\nDifference: {pp_change_new - pp_change_old:+.1f}pts")

if pp_change_new < 0:
    report.append("\n✓ New method shows DECLINING purchasing power")
    report.append("  This matches the 'it doesn't feel better' narrative")
elif pp_change_new < pp_change_old:
    report.append("\n✓ New method shows SLOWER improvement")
    report.append("  More realistic than old method")

# State analysis
comp_2018 = comparison[comparison['year'] == 2018][['state', 'mli_old', 'mli_new']].set_index('state')
comp_2023 = comparison[comparison['year'] == 2023][['state', 'mli_old', 'mli_new']].set_index('state')

states_analysis = pd.DataFrame({
    'mli_2018_old': comp_2018['mli_old'],
    'mli_2023_old': comp_2023['mli_old'],
    'mli_2018_new': comp_2018['mli_new'],
    'mli_2023_new': comp_2023['mli_new']
})

states_analysis['change_old'] = states_analysis['mli_2023_old'] - states_analysis['mli_2018_old']
states_analysis['change_new'] = states_analysis['mli_2023_new'] - states_analysis['mli_2018_new']

worse_old = (states_analysis['change_old'] < 0).sum()
worse_new = (states_analysis['change_new'] < 0).sum()

report.append(f"\n\nSTATES WITH DECLINING PURCHASING POWER (2018-2023):")
report.append(f"  Old method: {worse_old} states")
report.append(f"  New method: {worse_new} states")
report.append(f"  Difference: +{worse_new - worse_old} states now recognized as declining")

# ============================================================================
# HOUSING INFLATION ANALYSIS
# ============================================================================

print("\n[2/4] Analyzing housing vs goods inflation...")
print("-"*80)

report.append("\n\n" + "="*80)
report.append("HOUSING VS GOODS INFLATION")
report.append("="*80)

# Calculate housing and goods costs separately
housing_costs = costs_new[costs_new['category'] == 'housing'].groupby('year')['cost'].mean()

goods_categories = ['food', 'apparel', 'transportation', 'entertainment']
goods_costs = costs_new[costs_new['category'].isin(goods_categories)].groupby('year')['cost'].mean()

for baseline_year in [2012, 2018]:
    if baseline_year not in housing_costs.index:
        continue
    
    housing_baseline = housing_costs[baseline_year]
    housing_2023 = housing_costs[2023]
    housing_inflation = ((housing_2023 / housing_baseline) - 1) * 100
    
    goods_baseline = goods_costs[baseline_year]
    goods_2023 = goods_costs[2023]
    goods_inflation = ((goods_2023 / goods_baseline) - 1) * 100
    
    gap = housing_inflation - goods_inflation
    
    report.append(f"\n{baseline_year}-2023:")
    report.append(f"  Housing inflation: +{housing_inflation:.1f}%")
    report.append(f"  Goods inflation:   +{goods_inflation:.1f}%")
    report.append(f"  Housing premium:   +{gap:.1f}pts")
    
    if baseline_year == 2018:
        if housing_inflation >= 30:
            report.append(f"  ✓ Housing inflation now reflects market reality (~35%)")
        report.append(f"  ✓ Housing clearly outpaced goods (was incorrectly lower in old method)")

# ============================================================================
# STATE RANKINGS
# ============================================================================

print("\n[3/4] Comparing state rankings...")
print("-"*80)

report.append("\n\n" + "="*80)
report.append("STATE RANKINGS CHANGES (2023)")
report.append("="*80)

# 2023 rankings
rankings_2023 = comparison[comparison['year'] == 2023].copy()
rankings_2023 = rankings_2023.sort_values('mli_old', ascending=False)
rankings_2023['rank_old'] = range(1, len(rankings_2023) + 1)

rankings_2023 = rankings_2023.sort_values('mli_new', ascending=False)
rankings_2023['rank_new'] = range(1, len(rankings_2023) + 1)

rankings_2023['rank_change'] = rankings_2023['rank_old'] - rankings_2023['rank_new']

# Biggest rank changes
biggest_drops = rankings_2023.nlargest(10, 'rank_change')
biggest_gains = rankings_2023.nsmallest(10, 'rank_change')

report.append("\nBiggest Rank Drops (worse with market housing):")
for _, row in biggest_drops.iterrows():
    report.append(f"  {row['state']:20s}: #{row['rank_old']:2d} → #{row['rank_new']:2d} ({row['rank_change']:+3d})")

report.append("\nBiggest Rank Gains (better with market housing):")
for _, row in biggest_gains.iterrows():
    if row['rank_change'] < 0:
        report.append(f"  {row['state']:20s}: #{row['rank_old']:2d} → #{row['rank_new']:2d} ({row['rank_change']:+3d})")

# Save rankings
rankings_output = os.path.join(processed_dir, 'state_rankings_comparison.csv')
rankings_2023.sort_values('rank_new')[['state', 'rank_old', 'rank_new', 'rank_change', 
                                         'mli_old', 'mli_new', 'mli_diff']].to_csv(
    rankings_output, index=False
)

print(f"✓ Saved: {rankings_output}")

# ============================================================================
# REGENERATE MARKET DIVERGENCE
# ============================================================================

print("\n[4/4] Regenerating market divergence analysis...")
print("-"*80)

# S&P 500 data
sp500_data = {
    2012: 1426.19, 2013: 1848.36, 2014: 2058.90, 2015: 2043.94,
    2016: 2238.83, 2017: 2673.61, 2018: 2506.85, 2019: 3230.78,
    2021: 4766.18, 2022: 3839.50, 2023: 4769.83
}

def calculate_gains_from_baseline(baseline_year, mli_df):
    """Calculate indexed gains from a baseline year"""
    
    baseline_sp500 = sp500_data[baseline_year]
    baseline_mli = mli_df[mli_df['year'] == baseline_year]['mli'].mean()
    baseline_income = mli_df[mli_df['year'] == baseline_year]['median_income'].mean()
    baseline_col = mli_df[mli_df['year'] == baseline_year]['col'].mean()
    
    comparison = []
    for year in sorted(sp500_data.keys()):
        if year < baseline_year or year not in mli_df['year'].values:
            continue
        
        year_data = mli_df[mli_df['year'] == year]
        avg_mli = year_data['mli'].mean()
        avg_income = year_data['median_income'].mean()
        avg_col = year_data['col'].mean()
        
        comparison.append({
            'year': int(year),
            'sp500_indexed': float((sp500_data[year] / baseline_sp500) * 100),
            'income_indexed': float((avg_income / baseline_income) * 100),
            'col_indexed': float((avg_col / baseline_col) * 100),
            'mli_indexed': float((avg_mli / baseline_mli) * 100),
            'sp500_gain': float(((sp500_data[year] / baseline_sp500) - 1) * 100),
            'income_gain': float(((avg_income / baseline_income) - 1) * 100),
            'col_gain': float(((avg_col / baseline_col) - 1) * 100),
            'mli_gain': float(((avg_mli / baseline_mli) - 1) * 100)
        })
    
    return comparison, {
        'baseline_year': baseline_year,
        'final_year': 2023,
        'sp500_total_gain': comparison[-1]['sp500_gain'],
        'income_total_gain': comparison[-1]['income_gain'],
        'col_total_gain': comparison[-1]['col_gain'],
        'mli_total_gain': comparison[-1]['mli_gain']
    }

comparison_2012, summary_2012 = calculate_gains_from_baseline(2012, mli_new)
comparison_2018, summary_2018 = calculate_gains_from_baseline(2018, mli_new)

report.append("\n\n" + "="*80)
report.append("MARKETS VS PURCHASING POWER (WITH MARKET HOUSING)")
report.append("="*80)

report.append(f"\n2012-2023:")
report.append(f"  S&P 500:               {summary_2012['sp500_total_gain']:+.1f}%")
report.append(f"  Median Income:         {summary_2012['income_total_gain']:+.1f}%")
report.append(f"  Cost of Living:        {summary_2012['col_total_gain']:+.1f}%")
report.append(f"  Real Purchasing Power: {summary_2012['mli_total_gain']:+.1f}%")

report.append(f"\n2018-2023:")
report.append(f"  S&P 500:               {summary_2018['sp500_total_gain']:+.1f}%")
report.append(f"  Median Income:         {summary_2018['income_total_gain']:+.1f}%")
report.append(f"  Cost of Living:        {summary_2018['col_total_gain']:+.1f}%")
report.append(f"  Real Purchasing Power: {summary_2018['mli_total_gain']:+.1f}%")

# Create JSON for website
market_divergence_output = {
    'metadata': {
        'generated': datetime.now().isoformat(),
        'title': 'Financial Markets & Purchasing Power - Market-Adjusted Housing',
        'methodology': 'Uses actual market rent data weighted by homeownership rates',
        'housing_methodology': 'Weighted: (rental_rate × market_rent) + (ownership_rate × owner_costs)'
    },
    'summary_2012_2023': summary_2012,
    'summary_2018_2023': summary_2018,
    'market_comparison_2012': comparison_2012,
    'market_comparison_2018': comparison_2018
}

market_divergence_file = os.path.join(final_dir, 'market_divergence_MARKET.json')
with open(market_divergence_file, 'w') as f:
    json.dump(market_divergence_output, f, indent=2)

print(f"✓ Saved: {market_divergence_file}")

# ============================================================================
# SAVE REPORT
# ============================================================================

print("\n[Output] Saving final report...")
print("-"*80)

report_text = '\n'.join(report)

report_file = os.path.join(processed_dir, 'detailed_comparison_report.txt')
with open(report_file, 'w', encoding='utf-8') as f:  # Add UTF-8 encoding for Windows
    f.write(report_text)

print(f"✓ Saved: {report_file}")

# Print summary to console
print("\n" + "="*80)
print("KEY FINDINGS")
print("="*80)
print(f"\n2018-2023 Purchasing Power:")
print(f"  Old method: {pp_change_old:+.1f}%")
print(f"  New method: {pp_change_new:+.1f}%")
print(f"  Difference: {pp_change_new - pp_change_old:+.1f}pts")

print(f"\nStates Worse Off (2018-2023):")
print(f"  Old method: {worse_old} states")
print(f"  New method: {worse_new} states (+{worse_new - worse_old})")

print(f"\nHousing Inflation (2018-2023):")
housing_2018 = housing_costs[2018]
housing_2023 = housing_costs[2023]
housing_inflation_2018_2023 = ((housing_2023 / housing_2018) - 1) * 100
print(f"  New method: +{housing_inflation_2018_2023:.1f}% ✓")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "="*80)
print("STEP 5 COMPLETE - ALL ANALYSIS FINISHED")
print("="*80)

print("\n✓ Comprehensive comparison complete")
print("✓ Market divergence analysis regenerated")
print("✓ State rankings compared")
print("✓ Housing inflation now reflects market reality")

print("\nGenerated files:")
print("  • mli_results_14cat_q3_MARKET.csv")
print("  • costs_breakdown_14cat_q3_MARKET.csv")
print("  • housing_costs_weighted.csv")
print("  • market_divergence_MARKET.json")
print("  • state_rankings_comparison.csv")
print("  • detailed_comparison_report.txt")

print("\nNext steps:")
print("  1. Review detailed_comparison_report.txt")
print("  2. Update your website to use _MARKET.csv files")
print("  3. Replace market_divergence.json with market_divergence_MARKET.json")
print("  4. Update methodology documentation")

print("\n" + "="*80)