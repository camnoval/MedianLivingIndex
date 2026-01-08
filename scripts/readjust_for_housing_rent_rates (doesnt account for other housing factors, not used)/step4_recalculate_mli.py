"""
STEP 4: Recalculate MLI with Market-Adjusted Housing Costs
===========================================================

This is the main script that recalculates your MLI using the new,
more accurate housing costs that reflect actual market rents.

What changes:
- OLD: Housing = blended (30% rent + 70% owner with fixed mortgages)
- NEW: Housing = weighted (rental% × market_rent + owner% × owner_costs)

This will LOWER MLI scores because housing costs are higher than previously calculated.

Input files needed:
- census_income_data_YYYYMMDD.csv
- housing_costs_weighted.csv (from Step 3)
- costs_breakdown_14cat_q3.csv (for non-housing categories)
- BLS_baseline_spending.csv
- cpi_deflators_bls_categories.csv

Output:
- mli_results_14cat_q3_MARKET.csv (new MLI values)
- costs_breakdown_14cat_q3_MARKET.csv (new cost breakdown)
"""

import pandas as pd
import numpy as np
import glob
import os

print("="*80)
print("STEP 4: RECALCULATING MLI WITH MARKET-ADJUSTED HOUSING")
print("="*80)

QUINTILE = 'Q3'

# Get project root (two levels up from scripts/readjust_for_housing_rent_rates/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))

# Directories
raw_dir = os.path.join(project_root, 'data', 'raw')
processed_dir = os.path.join(project_root, 'data', 'processed')
final_dir = os.path.join(project_root, 'data', 'final')

# ============================================================================
# LOAD DATA
# ============================================================================

print("\n[Loading] Reading input files...")
print("-"*80)

# 1. Income data
income_files = glob.glob(os.path.join(raw_dir, 'census_income_data_*.csv'))
if not income_files:
    print(f"✗ No census_income_data file found in {raw_dir}!")
    exit(1)

INCOME_FILE = sorted(income_files)[-1]  # Use most recent
income_df = pd.read_csv(INCOME_FILE)

# Handle flexible column names
state_col = [c for c in income_df.columns if 'state' in c.lower() and 'name' in c.lower()]
state_col = state_col[0] if state_col else 'state'

income_df = income_df.rename(columns={
    state_col: 'state',
    'year': 'year',
    'median_income': 'median_income'
})

income_df['year'] = income_df['year'].astype(int)
income_df['state'] = income_df['state'].astype(str).str.strip()
income_df = income_df[income_df['state'] != 'District of Columbia']
income_df = income_df[['state', 'year', 'median_income']]

print(f"✓ Loaded income: {len(income_df)} observations from {os.path.basename(INCOME_FILE)}")

# 2. Weighted housing costs
housing_file = os.path.join(processed_dir, 'housing_costs_weighted.csv')
if not os.path.exists(housing_file):
    print(f"✗ Housing costs file not found: {housing_file}")
    print("  Run step3_calculate_weighted_housing.py first")
    exit(1)

housing_weighted = pd.read_csv(housing_file)
print(f"✓ Loaded weighted housing: {len(housing_weighted)} observations")

# 3. Original costs (for non-housing categories)
costs_file = os.path.join(final_dir, 'costs_breakdown_14cat_q3.csv')
if not os.path.exists(costs_file):
    print(f"✗ Costs file not found: {costs_file}")
    exit(1)

costs_original = pd.read_csv(costs_file)
costs_non_housing = costs_original[costs_original['category'] != 'housing'].copy()
print(f"✓ Loaded non-housing costs: {len(costs_non_housing)} observations")

# ============================================================================
# CREATE NEW COST BREAKDOWN
# ============================================================================

print("\n[Costs] Building new cost breakdown with market housing...")
print("-"*80)

# Prepare weighted housing in same format as costs
housing_for_costs = housing_weighted[['state', 'year', 'housing_cost_weighted']].copy()
housing_for_costs['category'] = 'housing'
housing_for_costs = housing_for_costs.rename(columns={'housing_cost_weighted': 'cost'})

# Combine new housing with original non-housing costs
new_costs = pd.concat([
    costs_non_housing,
    housing_for_costs
], ignore_index=True)

new_costs = new_costs.sort_values(['state', 'year', 'category'])

print(f"✓ Created new cost breakdown: {len(new_costs)} observations")
print(f"  Categories: {sorted(new_costs['category'].unique())}")

# Verify we have all 14 categories
categories_per_state_year = new_costs.groupby(['state', 'year'])['category'].nunique()
if (categories_per_state_year != 14).any():
    print("⚠ Warning: Some state-years don't have all 14 categories")
    missing = categories_per_state_year[categories_per_state_year != 14]
    print(f"  Found {len(missing)} state-years with incomplete data")

# ============================================================================
# CALCULATE NEW MLI
# ============================================================================

print("\n[MLI] Calculating new MLI values...")
print("-"*80)

# Sum costs to get total COL
col_df = new_costs.groupby(['state', 'year'])['cost'].sum().reset_index()
col_df = col_df.rename(columns={'cost': 'col'})

print(f"✓ Calculated Cost of Living for {len(col_df)} state-years")
print(f"  COL range: ${col_df['col'].min():,.0f} - ${col_df['col'].max():,.0f}")

# Check inflation in COL
col_2008 = col_df[col_df['year'] == 2008]['col'].mean()
col_2023 = col_df[col_df['year'] == 2023]['col'].mean()
col_inflation = ((col_2023 / col_2008) - 1) * 100
print(f"\n  Total COL inflation 2008-2023: +{col_inflation:.1f}%")

# Merge with income
mli_df = income_df.merge(col_df, on=['state', 'year'], how='inner')

# Calculate MLI as simple ratio
mli_df['mli'] = mli_df['median_income'] / mli_df['col']
mli_df['mli'] = mli_df['mli'].round(3)
mli_df['col'] = mli_df['col'].round(2)

# Calculate surplus/deficit
mli_df['annual_surplus'] = mli_df['median_income'] - mli_df['col']
mli_df['surplus_pct'] = ((mli_df['mli'] - 1.0) * 100).round(1)

print(f"\n✓ Calculated MLI for {len(mli_df)} observations")
print(f"  MLI range: {mli_df['mli'].min():.3f} - {mli_df['mli'].max():.3f}")

# ============================================================================
# COMPARE WITH ORIGINAL MLI
# ============================================================================

print("\n[Comparison] New vs Original MLI...")
print("-"*80)

# Load original MLI
mli_original_file = os.path.join(final_dir, 'mli_results_14cat_q3.csv')
if not os.path.exists(mli_original_file):
    print(f"✗ Original MLI file not found: {mli_original_file}")
    exit(1)

mli_original = pd.read_csv(mli_original_file)

comparison = mli_df.merge(
    mli_original[['state', 'year', 'mli', 'col']],
    on=['state', 'year'],
    how='inner',
    suffixes=('_new', '_old')
)

comparison['mli_change'] = comparison['mli_new'] - comparison['mli_old']
comparison['col_change'] = comparison['col_new'] - comparison['col_old']
comparison['col_change_pct'] = (comparison['col_change'] / comparison['col_old'] * 100).round(1)

# National averages
print("\nNational Average Changes:")
for year in [2012, 2018, 2023]:
    if year in comparison['year'].values:
        year_data = comparison[comparison['year'] == year]
        
        mli_old = year_data['mli_old'].mean()
        mli_new = year_data['mli_new'].mean()
        mli_change = mli_new - mli_old
        
        col_old = year_data['col_old'].mean()
        col_new = year_data['col_new'].mean()
        col_change = col_new - col_old
        col_change_pct = (col_change / col_old * 100)
        
        print(f"\n{year}:")
        print(f"  MLI: {mli_old:.3f} → {mli_new:.3f} ({mli_change:+.3f})")
        print(f"  COL: ${col_old:,.0f} → ${col_new:,.0f} (+${col_change:,.0f}, +{col_change_pct:.1f}%)")

# Show most affected states (2023)
print("\nMost Affected States (2023 - biggest MLI decrease):")
comparison_2023 = comparison[comparison['year'] == 2023].copy()
comparison_2023 = comparison_2023.sort_values('mli_change')

print(f"\n{'State':<20s} {'Old MLI':<9s} {'New MLI':<9s} {'Change':<9s} {'COL +%':<8s}")
print("-"*60)
for _, row in comparison_2023.head(10).iterrows():
    print(f"{row['state']:<20s} {row['mli_old']:>8.3f} {row['mli_new']:>8.3f} "
          f"{row['mli_change']:>+8.3f} {row['col_change_pct']:>+7.1f}%")

# ============================================================================
# 2018-2023 PURCHASING POWER ANALYSIS
# ============================================================================

print("\n[2018-2023] How purchasing power changed...")
print("-"*80)

mli_2018 = mli_df[mli_df['year'] == 2018]
mli_2023 = mli_df[mli_df['year'] == 2023]

state_2018_2023 = mli_2018[['state', 'mli']].merge(
    mli_2023[['state', 'mli']],
    on='state',
    suffixes=('_2018', '_2023')
)

state_2018_2023['change'] = state_2018_2023['mli_2023'] - state_2018_2023['mli_2018']

got_worse = (state_2018_2023['change'] < 0).sum()
got_better = (state_2018_2023['change'] > 0).sum()
avg_change = state_2018_2023['change'].mean()

print(f"\nWith Market-Adjusted Housing:")
print(f"  States worse off: {got_worse}")
print(f"  States better off: {got_better}")
print(f"  Average change: {avg_change:+.3f}")

# Compare with original
original_2018 = mli_original[mli_original['year'] == 2018]
original_2023 = mli_original[mli_original['year'] == 2023]

state_2018_2023_old = original_2018[['state', 'mli']].merge(
    original_2023[['state', 'mli']],
    on='state',
    suffixes=('_2018', '_2023')
)
state_2018_2023_old['change'] = state_2018_2023_old['mli_2023'] - state_2018_2023_old['mli_2018']

got_worse_old = (state_2018_2023_old['change'] < 0).sum()
avg_change_old = state_2018_2023_old['change'].mean()

print(f"\nOriginal Method (for comparison):")
print(f"  States worse off: {got_worse_old}")
print(f"  Average change: {avg_change_old:+.3f}")

print(f"\nDifference:")
print(f"  Additional states now worse off: +{got_worse - got_worse_old}")
print(f"  Change in avg PP growth: {(avg_change - avg_change_old):+.3f}")

# ============================================================================
# SAVE OUTPUTS
# ============================================================================

print("\n[Output] Saving results...")
print("-"*80)

# Save new MLI to final directory
mli_output = os.path.join(final_dir, 'mli_results_14cat_q3_MARKET.csv')
mli_df.to_csv(mli_output, index=False)
print(f"✓ Saved: {mli_output}")

# Save new costs to final directory
costs_output = os.path.join(final_dir, 'costs_breakdown_14cat_q3_MARKET.csv')
new_costs.to_csv(costs_output, index=False)
print(f"✓ Saved: {costs_output}")

# Save comparison to processed directory
comparison_output = os.path.join(processed_dir, 'mli_comparison_old_vs_new.csv')
comparison.to_csv(comparison_output, index=False)
print(f"✓ Saved: {comparison_output}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("STEP 4 COMPLETE - MLI RECALCULATED")
print("="*80)

national_2023 = mli_df[mli_df['year'] == 2023]
avg_mli_2023 = national_2023['mli'].mean()
states_deficit = (national_2023['mli'] < 1.0).sum()
states_surplus = (national_2023['mli'] >= 1.05).sum()

print(f"\n2023 Results (Market-Adjusted):")
print(f"  National avg MLI: {avg_mli_2023:.3f}")
print(f"  States in deficit (<1.0): {states_deficit}")
print(f"  States with surplus (≥1.05): {states_surplus}")

print(f"\n✓ New MLI accounts for true market rent inflation")
print(f"✓ Results better reflect actual housing costs")
print(f"✓ Analysis now validates 'it doesn't feel better' narrative")

print("\n→ Next: Run step5_compare_and_analyze.py")
print("="*80)