"""
Calculate Median Living Index (MLI) - Simplified Model with 2019 Base Year
===========================================================================

Pure purchasing power calculation:
- COL = Sum of all category costs (no weights)
- Purchasing Power = Median Income / COL
- MLI = (PP / US_2019_Reference_PP) × 100

Where US_2019_Reference_PP = US average purchasing power in 2019 (pre-pandemic)

This means:
- MLI = 100: Same purchasing power as US average in 2019
- MLI > 100: Better than pre-pandemic baseline
- MLI < 100: Below pre-pandemic baseline

Formula:
    State_Category_Cost = BLS_Baseline × (State_BEA_RPP / 100)
    State_COL = sum(Category_Costs)  # No weights!
    State_PP = Median Income / COL
    MLI = (State_PP / US_2019_PP) × 100

Output: mli_results_14cat_{quintile}.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

# File paths
INCOME_FILE = 'census_income_data_20260103.csv'
BEA_RPPS_FILE = 'bea_component_rpps.csv'
BLS_BASELINE_FILE = 'BLS_baseline_spending.csv'

# Which quintile to calculate (Q2, Q3, or Q4)
QUINTILE = 'Q3'  # Middle class (50th percentile)

OUTPUT_FILE = f'mli_results_14cat_{QUINTILE.lower()}.csv'

# ============================================================================
# LOAD DATA
# ============================================================================

def load_all_data():
    """Load income, BEA RPPs, and BLS baselines"""
    
    print("="*70)
    print(f"LOADING DATA FOR {QUINTILE} (MIDDLE CLASS)")
    print("="*70)
    
    # 1. Income data
    print("\n[1/3] Loading median household income...")
    income_df = pd.read_csv(INCOME_FILE)
    
    # Flexible column detection
    state_col = [c for c in income_df.columns if 'state' in c.lower() and 'name' in c.lower()]
    if state_col:
        state_col = state_col[0]
    else:
        state_col = 'state'
    
    income_df = income_df.rename(columns={
        state_col: 'state',
        'year': 'year',
        'median_income': 'median_income'
    })
    
    income_df['year'] = income_df['year'].astype(int)
    income_df['state'] = income_df['state'].astype(str).str.strip()
    
    # Remove DC if present
    income_df = income_df[income_df['state'] != 'District of Columbia']
    income_df = income_df[['state', 'year', 'median_income']]
    
    print(f"  ✓ {len(income_df)} observations")
    
    # 2. BEA component RPPs
    print("\n[2/3] Loading BEA component RPPs...")
    bea_df = pd.read_csv(BEA_RPPS_FILE)
    bea_df['year'] = bea_df['year'].astype(int)
    bea_df['state'] = bea_df['state'].astype(str).str.strip()
    print(f"  ✓ {len(bea_df)} observations")
    
    # 3. BLS baseline spending
    print("\n[3/3] Loading BLS baseline spending...")
    baseline_df = pd.read_csv(BLS_BASELINE_FILE)
    
    # Select quintile-specific baseline
    baseline_col = f'{QUINTILE.lower()}_baseline'
    baseline_df = baseline_df[['category', baseline_col, 'bea_adjuster']].copy()
    baseline_df = baseline_df.rename(columns={baseline_col: 'baseline_spending'})
    
    print(f"  ✓ {len(baseline_df)} categories")
    print(f"  Total baseline: ${baseline_df['baseline_spending'].sum():,.0f}/year")
    
    return income_df, bea_df, baseline_df


# ============================================================================
# CALCULATE STATE-ADJUSTED COSTS
# ============================================================================

def calculate_state_costs(bea_df, baseline_df):
    """
    Calculate state-year-specific costs for each category by applying
    BEA RPP adjustments to BLS baseline spending.
    
    NO WEIGHTS - just pure costs.
    """
    
    print("\n" + "="*70)
    print("CALCULATING STATE-ADJUSTED COSTS")
    print("="*70)
    
    # Create state-year-category costs
    all_costs = []
    
    for _, cat in baseline_df.iterrows():
        category = cat['category']
        baseline = cat['baseline_spending']
        adjuster = cat['bea_adjuster']
        
        print(f"\n{category:20s} (baseline: ${baseline:>6,.0f})")
        
        if adjuster == 'none':
            # Cash contributions - no adjustment
            print(f"  → No adjustment (transfers, not consumption)")
            
            # Apply baseline to all states
            for state in bea_df['state'].unique():
                for year in bea_df['year'].unique():
                    all_costs.append({
                        'state': state,
                        'year': year,
                        'category': category,
                        'cost': baseline
                    })
        else:
            # Apply BEA RPP adjustment
            rpp_col = adjuster
            print(f"  → Adjusted by {rpp_col}")
            
            for _, row in bea_df.iterrows():
                rpp_value = row[rpp_col]
                adjusted_cost = baseline * (rpp_value / 100)
                
                all_costs.append({
                    'state': row['state'],
                    'year': row['year'],
                    'category': category,
                    'cost': adjusted_cost
                })
    
    costs_df = pd.DataFrame(all_costs)
    
    print(f"\n✓ Calculated {len(costs_df)} state-year-category costs")
    
    return costs_df


# ============================================================================
# CALCULATE MLI WITH 2019 BASE YEAR
# ============================================================================

def calculate_mli(income_df, costs_df):
    """
    Calculate MLI by:
    1. Sum costs to get state COL (NO WEIGHTS)
    2. Calculate state purchasing power (income/COL)
    3. Normalize to 2019 US average = 100
    """
    
    print("\n" + "="*70)
    print("CALCULATING MLI SCORES (2019 BASE YEAR)")
    print("="*70)
    
    # Calculate total COL for each state-year (simple sum, no weights)
    col_df = costs_df.groupby(['state', 'year'])['cost'].sum().reset_index()
    col_df = col_df.rename(columns={'cost': 'col_index'})
    
    print(f"\n✓ Calculated COL for {len(col_df)} state-years")
    print(f"  COL range: ${col_df['col_index'].min():,.0f} - ${col_df['col_index'].max():,.0f}")
    
    # Merge with income
    df = income_df.merge(col_df, on=['state', 'year'], how='inner')
    
    # Calculate state purchasing power
    df['purchasing_power'] = df['median_income'] / df['col_index']
    
    # Get 2019 US average purchasing power as reference
    df_2019 = df[df['year'] == 2019].copy()
    us_2019_reference_pp = df_2019['purchasing_power'].mean()
    
    print(f"\n2019 US Average Purchasing Power: {us_2019_reference_pp:.4f}")
    print(f"  (This becomes MLI = 100 baseline)")
    
    # Calculate MLI using 2019 base
    df['mli'] = (df['purchasing_power'] / us_2019_reference_pp) * 100
    
    # Round for readability
    df['mli'] = df['mli'].round(2)
    df['col_index'] = df['col_index'].round(2)
    
    print(f"\n✓ Calculated MLI for {len(df)} observations")
    print(f"  MLI range: {df['mli'].min():.2f} - {df['mli'].max():.2f}")
    print(f"\n  Interpretation:")
    print(f"    MLI = 100: Same purchasing power as US average in 2019")
    print(f"    MLI > 100: Better than pre-pandemic baseline")
    print(f"    MLI < 100: Below pre-pandemic baseline")
    
    return df, us_2019_reference_pp


# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

def print_summary(mli_df, costs_df):
    """Print comprehensive summary statistics"""
    
    print("\n" + "="*70)
    print(f"MLI SUMMARY STATISTICS ({QUINTILE})")
    print("="*70)
    
    # Top 10 states (2023)
    latest_year = mli_df['year'].max()
    latest_data = mli_df[mli_df['year'] == latest_year].sort_values('mli', ascending=False)
    
    print(f"\n\nTop 10 States - Best Affordability ({latest_year}):")
    for i, (_, row) in enumerate(latest_data.head(10).iterrows(), 1):
        print(f"  {i:2d}. {row['state']:20s} MLI: {row['mli']:6.2f}  Income: ${row['median_income']:>7,.0f}  COL: ${row['col_index']:>7,.0f}")
    
    # Bottom 10 states
    print(f"\n\nBottom 10 States - Worst Affordability ({latest_year}):")
    for i, (_, row) in enumerate(latest_data.tail(10).iloc[::-1].iterrows(), 1):
        print(f"  {i:2d}. {row['state']:20s} MLI: {row['mli']:6.2f}  Income: ${row['median_income']:>7,.0f}  COL: ${row['col_index']:>7,.0f}")
    
    # Changes over time (2008 to 2023)
    if 2008 in mli_df['year'].values and latest_year in mli_df['year'].values:
        print("\n\nBiggest MLI Changes (2008 → {latest_year}):")
        
        mli_2008 = mli_df[mli_df['year'] == 2008].set_index('state')['mli']
        mli_latest = mli_df[mli_df['year'] == latest_year].set_index('state')['mli']
        
        changes = (mli_latest - mli_2008).sort_values()
        
        print("\n  Largest Declines:")
        for state, change in changes.head(5).items():
            print(f"    {state:20s} {change:+6.2f} points")
        
        print("\n  Largest Improvements:")
        for state, change in changes.tail(5).iloc[::-1].items():
            print(f"    {state:20s} {change:+6.2f} points")
    
    # Cost breakdown for select states (latest year)
    print(f"\n\nCost Breakdown Examples ({latest_year}):")
    
    for example_state in ['California', 'Texas', 'Mississippi']:
        state_costs = costs_df[
            (costs_df['state'] == example_state) & 
            (costs_df['year'] == latest_year)
        ].sort_values('cost', ascending=False)
        
        print(f"\n  {example_state}:")
        total = state_costs['cost'].sum()
        for _, row in state_costs.head(5).iterrows():
            pct = (row['cost'] / total) * 100
            print(f"    {row['category']:20s} ${row['cost']:>7,.0f} ({pct:4.1f}%)")
        print(f"    {'TOTAL':20s} ${total:>7,.0f}")


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    """Execute complete MLI calculation pipeline"""
    
    print("\n" + "="*70)
    print(f"MEDIAN LIVING INDEX - SIMPLIFIED MODEL ({QUINTILE})")
    print("Using 2019 pre-pandemic baseline")
    print("="*70)
    
    # Load all data
    income_df, bea_df, baseline_df = load_all_data()
    
    # Calculate state-adjusted costs (no weights)
    costs_df = calculate_state_costs(bea_df, baseline_df)
    
    # Calculate MLI with 2019 base
    mli_df, reference_pp_2019 = calculate_mli(income_df, costs_df)
    
    # Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    mli_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✓ Saved MLI results to: {OUTPUT_FILE}")
    
    # Save detailed costs breakdown
    costs_detail_file = f'costs_breakdown_14cat_{QUINTILE.lower()}.csv'
    costs_df.to_csv(costs_detail_file, index=False)
    print(f"✓ Saved cost breakdown to: {costs_detail_file}")
    
    # Save metadata
    metadata = {
        'base_year': 2019,
        'reference_pp': reference_pp_2019,
        'quintile': QUINTILE,
        'formula': 'MLI = (Income / COL) / US_2019_PP × 100',
        'interpretation': 'MLI = 100 means same purchasing power as US average in 2019'
    }
    
    import json
    with open(f'mli_metadata_{QUINTILE.lower()}.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved metadata to: mli_metadata_{QUINTILE.lower()}.json")
    
    # Print summary
    print_summary(mli_df, costs_df)
    
    print("\n" + "="*70)
    print("CALCULATION COMPLETE!")
    print("="*70)
    print(f"\nKey Changes from Old Method:")
    print(f"  1. COL is now TOTAL annual expenses (not weighted)")
    print(f"  2. MLI uses 2019 as fixed baseline (not yearly average)")
    print(f"  3. Easier to understand and individualize")
    print(f"\nOutput files:")
    print(f"  1. {OUTPUT_FILE} - MLI scores by state-year")
    print(f"  2. {costs_detail_file} - Detailed cost breakdown")
    print(f"  3. mli_metadata_{QUINTILE.lower()}.json - Calculation metadata")
    
    return mli_df, costs_df


if __name__ == "__main__":
    mli_df, costs_df = main()