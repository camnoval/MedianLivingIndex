"""
STEP 3: Calculate Weighted Housing Costs
========================================

Combines market rents with homeownership data to create accurate housing costs:
- Renters (35%): Pay market rent
- Owners (65%): Pay mortgage + property tax + maintenance

Formula: housing_cost = (rental_rate × market_rent) + (ownership_rate × owner_cost)

Input files needed:
- market_rents_final.csv (from Step 2)
- census_homeownership_rates.csv or _fallback.csv (from Step 1)
- costs_breakdown_14cat_q3.csv (for current owner costs)
- bea_component_rpps.csv (for adjustments)

Output:
- housing_costs_weighted.csv (new housing costs by state-year)
"""

import pandas as pd
import numpy as np
import os

print("="*80)
print("STEP 3: CALCULATING WEIGHTED HOUSING COSTS")
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

print("\n[Loading] Reading input files...")
print("-"*80)

# 1. Market rents
market_rents_file = os.path.join(processed_dir, 'market_rents_final.csv')
if not os.path.exists(market_rents_file):
    print(f"✗ Market rents file not found: {market_rents_file}")
    print("  Run step2_create_market_rents.py first")
    exit(1)

market_rents = pd.read_csv(market_rents_file)
print(f"✓ Loaded market rents: {len(market_rents)} observations")

# 2. Homeownership rates
homeownership_file = os.path.join(processed_dir, 'census_homeownership_rates.csv')
fallback_file = os.path.join(processed_dir, 'census_homeownership_rates_fallback.csv')

if os.path.exists(homeownership_file):
    homeownership_df = pd.read_csv(homeownership_file)
    print(f"✓ Loaded Census homeownership rates: {len(homeownership_df)} observations")
    using_real_data = True
elif os.path.exists(fallback_file):
    homeownership_df = pd.read_csv(fallback_file)
    print(f"✓ Loaded fallback homeownership rates (65% national average)")
    using_real_data = False
else:
    print(f"✗ No homeownership data found!")
    print(f"  Checked: {homeownership_file}")
    print(f"  Checked: {fallback_file}")
    print("  Run step1_fetch_zillow_census.py first")
    exit(1)

# 3. Current housing costs (for owner costs)
costs_file = os.path.join(final_dir, 'costs_breakdown_14cat_q3.csv')
if not os.path.exists(costs_file):
    print(f"✗ Costs file not found: {costs_file}")
    exit(1)

costs_df = pd.read_csv(costs_file)
housing_current = costs_df[costs_df['category'] == 'housing'].copy()
print(f"✓ Loaded current housing costs: {len(housing_current)} observations")

# 4. BEA RPPs (for consistency check)
bea_file = os.path.join(processed_dir, 'bea_component_rpps.csv')
if not os.path.exists(bea_file):
    print(f"✗ BEA RPPs file not found: {bea_file}")
    exit(1)

bea_df = pd.read_csv(bea_file)
print(f"✓ Loaded BEA RPPs: {len(bea_df)} observations")

# ============================================================================
# CALCULATE OWNER COSTS
# ============================================================================

print("\n[Owner Costs] Estimating owner housing costs...")
print("-"*80)

# Your current housing costs are blended (30% rent + 70% owner)
# To isolate owner costs:
# blended = 0.30×rent + 0.70×owner
# owner = (blended - 0.30×rent) / 0.70

# Merge market rents with current costs
owner_calc = housing_current.merge(
    market_rents[['state', 'year', 'annual_market_rent']],
    on=['state', 'year'],
    how='left'
)

# Calculate implied owner costs
owner_calc['owner_costs'] = (owner_calc['cost'] - 0.30 * owner_calc['annual_market_rent']) / 0.70

# Some states might have negative values due to estimation errors
# Use current blended cost × 0.85 as floor (owners typically pay 85% of blended)
owner_calc['owner_costs'] = owner_calc[['owner_costs', 'cost']].apply(
    lambda x: max(x['owner_costs'], x['cost'] * 0.85), axis=1
)

print(f"✓ Calculated owner costs for {len(owner_calc)} state-years")

# Verify owner vs rent relationship
comparison_2023 = owner_calc[owner_calc['year'] == 2023]
avg_owner_2023 = comparison_2023['owner_costs'].mean()
avg_rent_2023 = comparison_2023['annual_market_rent'].mean()
owner_to_rent_ratio = avg_owner_2023 / avg_rent_2023

print(f"\n2023 Averages:")
print(f"  Market rent: ${avg_rent_2023:,.0f}/year")
print(f"  Owner costs: ${avg_owner_2023:,.0f}/year")
print(f"  Ratio: {owner_to_rent_ratio:.2f}x", end="")

if 0.80 <= owner_to_rent_ratio <= 0.95:
    print(" ✓ (expected: 0.85-0.90)")
else:
    print(f" ⚠ (expected: 0.85-0.90, difference: {abs(owner_to_rent_ratio-0.875):.2f})")

# ============================================================================
# CALCULATE WEIGHTED HOUSING COSTS
# ============================================================================

print("\n[Weighting] Combining renter and owner costs...")
print("-"*80)

# Merge all data
weighted_housing = owner_calc[['state', 'year', 'annual_market_rent', 'owner_costs']].merge(
    homeownership_df[['state', 'year', 'homeownership_rate', 'rental_rate']],
    on=['state', 'year'],
    how='left'
)

# Fill missing homeownership rates with national average
if weighted_housing['homeownership_rate'].isna().any():
    print("⚠  Some homeownership rates missing, using 65% national average")
    weighted_housing['homeownership_rate'] = weighted_housing['homeownership_rate'].fillna(65.0)
    weighted_housing['rental_rate'] = weighted_housing['rental_rate'].fillna(35.0)

# Calculate weighted average
# housing_cost = (rental_rate/100 × market_rent) + (ownership_rate/100 × owner_cost)
weighted_housing['housing_cost_weighted'] = (
    (weighted_housing['rental_rate'] / 100 * weighted_housing['annual_market_rent']) +
    (weighted_housing['homeownership_rate'] / 100 * weighted_housing['owner_costs'])
)

# Round for readability
weighted_housing['housing_cost_weighted'] = weighted_housing['housing_cost_weighted'].round(2)

print(f"✓ Calculated weighted housing costs for {len(weighted_housing)} state-years")

# ============================================================================
# COMPARE WITH ORIGINAL
# ============================================================================

print("\n[Comparison] New vs Old housing costs...")
print("-"*80)

comparison = weighted_housing.merge(
    housing_current[['state', 'year', 'cost']].rename(columns={'cost': 'housing_cost_old'}),
    on=['state', 'year'],
    how='left'
)

comparison['cost_increase'] = comparison['housing_cost_weighted'] - comparison['housing_cost_old']
comparison['cost_increase_pct'] = (comparison['cost_increase'] / comparison['housing_cost_old'] * 100).round(1)

# National averages
print("\nNational Average Comparison:")
for year in [2012, 2018, 2023]:
    if year in comparison['year'].values:
        year_data = comparison[comparison['year'] == year]
        old_avg = year_data['housing_cost_old'].mean()
        new_avg = year_data['housing_cost_weighted'].mean()
        diff = new_avg - old_avg
        diff_pct = (diff / old_avg * 100)
        
        print(f"\n{year}:")
        print(f"  Old (blended):  ${old_avg:>10,.0f}")
        print(f"  New (weighted): ${new_avg:>10,.0f}")
        print(f"  Difference:     ${diff:>10,.0f} (+{diff_pct:.1f}%)")

# Show inflation rates
print("\nHousing Inflation Rates:")
print("-"*40)
for baseline_year in [2012, 2018]:
    if baseline_year in comparison['year'].values:
        # Old method
        old_baseline = comparison[comparison['year'] == baseline_year]['housing_cost_old'].mean()
        old_2023 = comparison[comparison['year'] == 2023]['housing_cost_old'].mean()
        old_inflation = ((old_2023 / old_baseline) - 1) * 100
        
        # New method
        new_baseline = comparison[comparison['year'] == baseline_year]['housing_cost_weighted'].mean()
        new_2023 = comparison[comparison['year'] == 2023]['housing_cost_weighted'].mean()
        new_inflation = ((new_2023 / new_baseline) - 1) * 100
        
        print(f"\n{baseline_year}-2023:")
        print(f"  Old method: +{old_inflation:.1f}%")
        print(f"  New method: +{new_inflation:.1f}%")
        print(f"  Difference: +{new_inflation - old_inflation:.1f}pts")

# ============================================================================
# SAVE OUTPUT
# ============================================================================

print("\n[Output] Saving weighted housing costs...")
print("-"*80)

output = weighted_housing[['state', 'year', 'housing_cost_weighted', 'annual_market_rent', 
                            'owner_costs', 'homeownership_rate', 'rental_rate']].copy()

output = output.sort_values(['state', 'year'])

output_file = os.path.join(processed_dir, 'housing_costs_weighted.csv')
output.to_csv(output_file, index=False)

print(f"✓ Saved: {output_file}")
print(f"  {len(output)} state-year observations")

# Show sample
print("\nSample weighted costs (2023, selected states):")
sample_states = ['California', 'Texas', 'New York', 'Florida', 'Alabama']
sample = output[
    (output['year'] == 2023) & 
    (output['state'].isin(sample_states))
].sort_values('housing_cost_weighted', ascending=False)

print(f"\n{'State':<15s} {'Weighted':<12s} {'Market Rent':<12s} {'Owner':<12s} {'% Renters':<10s}")
print("-"*70)
for _, row in sample.iterrows():
    print(f"{row['state']:<15s} ${row['housing_cost_weighted']:>10,.0f} "
          f"${row['annual_market_rent']:>10,.0f} ${row['owner_costs']:>10,.0f} "
          f"{row['rental_rate']:>8.1f}%")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("STEP 3 COMPLETE")
print("="*80)

avg_increase_2023 = comparison[comparison['year'] == 2023]['cost_increase_pct'].mean()

print(f"\n✓ Weighted housing costs calculated")
print(f"✓ Average increase vs old method: +{avg_increase_2023:.1f}%")
print(f"✓ Captures true market rent inflation")

if using_real_data:
    print("✓ Uses state-specific homeownership rates")
else:
    print("⚠ Uses national average homeownership (65%)")
    print("  For state-specific rates, provide Census API key in Step 1")

print("\n→ Next: Run step4_recalculate_mli.py")
print("="*80)