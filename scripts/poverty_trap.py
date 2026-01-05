"""
Poverty Trap Index Calculator
==============================

Identifies states where residents are "stuck" - costs are low but incomes
are so low that households can't save enough to relocate to better opportunities.

Methodology:
1. Calculate annual savings capacity (Income - COL)
2. Estimate cost to relocate (moving costs + 3 months rent in median state)
3. Calculate "years to escape" = Relocation cost / Annual savings
4. Poverty Trap Score = Weighted combination of:
   - Years to escape (40%)
   - Absolute savings rate (30%)
   - Income growth trajectory (30%)

Output: poverty_trap_index.csv with rankings
"""

import pandas as pd
import numpy as np

print("="*70)
print("POVERTY TRAP INDEX CALCULATOR")
print("="*70)

# Load MLI results
print("\nLoading MLI data...")
mli_df = pd.read_csv('mli_results_14cat_q3.csv')

# Focus on 2023
mli_2023 = mli_df[mli_df['year'] == 2023].copy()
mli_2008 = mli_df[mli_df['year'] == 2008].set_index('state')

print(f"✓ Loaded {len(mli_2023)} states for 2023")

# ============================================================================
# COMPONENT 1: SAVINGS CAPACITY
# ============================================================================

print("\n[1/4] Calculating savings capacity...")

# Annual savings = Income - COL
mli_2023['annual_savings'] = mli_2023['median_income'] - mli_2023['col_index']
mli_2023['savings_rate'] = (mli_2023['annual_savings'] / mli_2023['median_income']) * 100

print(f"  Savings rate range: {mli_2023['savings_rate'].min():.1f}% - {mli_2023['savings_rate'].max():.1f}%")

# ============================================================================
# COMPONENT 2: COST TO RELOCATE
# ============================================================================

print("\n[2/4] Estimating relocation costs...")

# National median housing cost (for 3 months security)
national_median_housing = mli_2023['col_index'].median() * 0.338 / 12 * 3  # 3 months of housing

# Moving costs (U-Haul + gas + misc)
MOVING_COSTS = 2500

# Job search buffer (1 month expenses at median state)
job_search_buffer = mli_2023['col_index'].median() / 12

# Total relocation cost
mli_2023['relocation_cost'] = MOVING_COSTS + national_median_housing + job_search_buffer

print(f"  Estimated relocation cost: ${mli_2023['relocation_cost'].iloc[0]:,.0f}")

# ============================================================================
# COMPONENT 3: YEARS TO ESCAPE
# ============================================================================

print("\n[3/4] Calculating years to escape...")

# Years needed to save enough to relocate
mli_2023['years_to_escape'] = mli_2023['relocation_cost'] / mli_2023['annual_savings'].clip(lower=1)

# Cap at 50 years (essentially trapped)
mli_2023['years_to_escape'] = mli_2023['years_to_escape'].clip(upper=50)

print(f"  Years to escape range: {mli_2023['years_to_escape'].min():.1f} - {mli_2023['years_to_escape'].max():.1f}")

# ============================================================================
# COMPONENT 4: INCOME GROWTH TRAJECTORY
# ============================================================================

print("\n[4/4] Analyzing income growth trajectory...")

# Calculate 15-year income growth rate
mli_2023['income_2008'] = mli_2023['state'].map(mli_2008['median_income'])
mli_2023['income_growth_15yr'] = ((mli_2023['median_income'] / mli_2023['income_2008']) - 1) * 100

print(f"  Income growth range: {mli_2023['income_growth_15yr'].min():.1f}% - {mli_2023['income_growth_15yr'].max():.1f}%")

# ============================================================================
# COMPOSITE POVERTY TRAP SCORE
# ============================================================================

print("\n[5/5] Calculating Poverty Trap Score...")

# Normalize components to 0-100 scale (higher = more trapped)

# Years to escape (normalize inversely - more years = more trapped)
years_norm = (mli_2023['years_to_escape'] / mli_2023['years_to_escape'].max()) * 100

# Savings rate (normalize inversely - lower savings = more trapped)
savings_norm = 100 - ((mli_2023['savings_rate'] - mli_2023['savings_rate'].min()) / 
                      (mli_2023['savings_rate'].max() - mli_2023['savings_rate'].min()) * 100)

# Income growth (normalize inversely - lower growth = more trapped)
growth_norm = 100 - ((mli_2023['income_growth_15yr'] - mli_2023['income_growth_15yr'].min()) / 
                     (mli_2023['income_growth_15yr'].max() - mli_2023['income_growth_15yr'].min()) * 100)

# Weighted composite (40% years, 30% savings, 30% growth)
mli_2023['poverty_trap_score'] = (
    years_norm * 0.40 +
    savings_norm * 0.30 +
    growth_norm * 0.30
)

# Classify states
mli_2023['trap_category'] = pd.cut(
    mli_2023['poverty_trap_score'],
    bins=[0, 35, 55, 75, 100],
    labels=['Mobile', 'Stable', 'Difficult', 'Trapped']
)

# ============================================================================
# RESULTS & INSIGHTS
# ============================================================================

print("\n" + "="*70)
print("POVERTY TRAP INDEX RESULTS (2023)")
print("="*70)

# Sort by trap score
results = mli_2023[['state', 'median_income', 'col_index', 'annual_savings', 'savings_rate', 
                     'years_to_escape', 'income_growth_15yr', 'poverty_trap_score', 'trap_category']].copy()
results = results.sort_values('poverty_trap_score', ascending=False)

print("\n🔴 MOST TRAPPED STATES (Top 10):")
print(f"{'State':<20s} {'Income':>10s} {'COL':>10s} {'Savings':>10s} {'Years':>7s} {'Score':>7s}")
print("-"*75)
for _, row in results.head(10).iterrows():
    print(f"{row['state']:<20s} ${row['median_income']:>9,.0f} ${row['col_index']:>9,.0f} "
          f"${row['annual_savings']:>9,.0f} {row['years_to_escape']:>6.1f}yr {row['poverty_trap_score']:>6.1f}")

print("\n\n🟢 MOST MOBILE STATES (Bottom 10):")
print(f"{'State':<20s} {'Income':>10s} {'COL':>10s} {'Savings':>10s} {'Years':>7s} {'Score':>7s}")
print("-"*75)
for _, row in results.tail(10).iloc[::-1].iterrows():
    print(f"{row['state']:<20s} ${row['median_income']:>9,.0f} ${row['col_index']:>9,.0f} "
          f"${row['annual_savings']:>9,.0f} {row['years_to_escape']:>6.1f}yr {row['poverty_trap_score']:>6.1f}")

# Category distribution
print("\n\nCATEGORY DISTRIBUTION:")
print(mli_2023['trap_category'].value_counts().sort_index())

# Key insights
print("\n\nKEY INSIGHTS:")
print("-"*70)

# Find "cheap but trapped" states (low COL, high trap score)
cheap_trapped = results[(results['col_index'] < results['col_index'].median()) & 
                        (results['poverty_trap_score'] > 60)]
print(f"\n📍 Cheap But Trapped ({len(cheap_trapped)} states):")
print(f"   Low costs but such low incomes that residents can't save to leave")
for state in cheap_trapped['state'].head(5):
    print(f"   - {state}")

# Find "expensive but mobile" states (high COL, low trap score)
expensive_mobile = results[(results['col_index'] > results['col_index'].median()) & 
                           (results['poverty_trap_score'] < 40)]
print(f"\n📍 Expensive But Mobile ({len(expensive_mobile)} states):")
print(f"   High costs but high incomes allow saving for relocation if needed")
for state in expensive_mobile['state'].head(5):
    print(f"   - {state}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

results.to_csv('poverty_trap_index.csv', index=False)
print("\n✓ Saved detailed results to: poverty_trap_index.csv")

# Create summary for media
summary = results[['state', 'poverty_trap_score', 'trap_category', 'years_to_escape', 
                   'savings_rate', 'income_growth_15yr']].copy()
summary = summary.sort_values('poverty_trap_score', ascending=False)
summary.to_csv('poverty_trap_summary.csv', index=False)
print("✓ Saved media summary to: poverty_trap_summary.csv")

print("\n" + "="*70)
print("POVERTY TRAP ANALYSIS COMPLETE!")
print("="*70)
print("\nNext steps:")
print("  1. Review poverty_trap_index.csv for full details")
print("  2. Create visualizations (map, scatter plot)")
print("  3. Write policy brief on 'cheap but trapped' states")