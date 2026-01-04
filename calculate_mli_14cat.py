"""
Calculate Median Living Index (MLI) - SIMPLIFIED RATIO
=======================================================

The simplest, most intuitive approach:

MLI = Median Income / Cost of Living

Interpretation:
- MLI = 1.0: Income exactly covers annual expenses (paycheck to paycheck)
- MLI = 1.3: Income is 30% higher than expenses (can save/invest 30%)
- MLI = 0.9: Income is 10% lower than expenses (going into debt)

Examples:
- Mississippi: $54,200 / $58,000 = 0.93 (spending 107% of income)
- Utah: $93,400 / $69,000 = 1.35 (35% surplus for savings/investment)

This is the purchasing power ratio - pure and simple.

Output: mli_results_simple.csv
"""

import pandas as pd
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

INCOME_FILE = 'census_income_data_20260103.csv'
BEA_RPPS_FILE = 'bea_component_rpps.csv'
BLS_BASELINE_FILE = 'BLS_baseline_spending.csv'

QUINTILE = 'Q3'  # Middle class (50th percentile)

OUTPUT_FILE = 'mli_results_simple.csv'

# ============================================================================
# LOAD DATA (same as before)
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
    
    baseline_col = f'{QUINTILE.lower()}_baseline'
    baseline_df = baseline_df[['category', baseline_col, 'bea_adjuster']].copy()
    baseline_df = baseline_df.rename(columns={baseline_col: 'baseline_spending'})
    
    print(f"  ✓ {len(baseline_df)} categories")
    print(f"  Total baseline: ${baseline_df['baseline_spending'].sum():,.0f}/year")
    
    return income_df, bea_df, baseline_df


def calculate_state_costs(bea_df, baseline_df):
    """Calculate state-year-specific costs for each category"""
    
    print("\n" + "="*70)
    print("CALCULATING STATE-ADJUSTED COSTS")
    print("="*70)
    
    all_costs = []
    
    for _, cat in baseline_df.iterrows():
        category = cat['category']
        baseline = cat['baseline_spending']
        adjuster = cat['bea_adjuster']
        
        print(f"\n{category:20s} (baseline: ${baseline:>6,.0f})")
        
        if adjuster == 'none':
            print(f"  → No adjustment")
            for state in bea_df['state'].unique():
                for year in bea_df['year'].unique():
                    all_costs.append({
                        'state': state,
                        'year': year,
                        'category': category,
                        'cost': baseline
                    })
        else:
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
# SIMPLIFIED MLI CALCULATION
# ============================================================================

def calculate_mli_simple(income_df, costs_df):
    """
    Calculate MLI as simple ratio:
    MLI = Median Income / Cost of Living
    
    No normalization, no base years - just the raw purchasing power ratio.
    """
    
    print("\n" + "="*70)
    print("CALCULATING MLI (SIMPLE RATIO)")
    print("="*70)
    
    # Sum costs to get total COL
    col_df = costs_df.groupby(['state', 'year'])['cost'].sum().reset_index()
    col_df = col_df.rename(columns={'cost': 'col'})
    
    print(f"\n✓ Calculated COL for {len(col_df)} state-years")
    print(f"  COL range: ${col_df['col'].min():,.0f} - ${col_df['col'].max():,.0f}")
    
    # Merge with income
    df = income_df.merge(col_df, on=['state', 'year'], how='inner')
    
    # Calculate MLI as simple ratio
    df['mli'] = df['median_income'] / df['col']
    
    # Round for readability
    df['mli'] = df['mli'].round(3)
    df['col'] = df['col'].round(2)
    
    print(f"\n✓ Calculated MLI for {len(df)} observations")
    print(f"  MLI range: {df['mli'].min():.3f} - {df['mli'].max():.3f}")
    
    print(f"\n  Interpretation:")
    print(f"    MLI = 1.0: Income exactly covers expenses (paycheck to paycheck)")
    print(f"    MLI > 1.0: Income exceeds expenses (surplus for savings)")
    print(f"    MLI < 1.0: Income below expenses (deficit/debt)")
    
    # Calculate surplus/deficit
    df['annual_surplus'] = df['median_income'] - df['col']
    df['surplus_pct'] = ((df['mli'] - 1.0) * 100).round(1)
    
    return df


# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

def print_summary(mli_df):
    """Print comprehensive summary statistics"""
    
    print("\n" + "="*70)
    print(f"MLI SUMMARY STATISTICS (SIMPLE RATIO)")
    print("="*70)
    
    latest_year = mli_df['year'].max()
    latest_data = mli_df[mli_df['year'] == latest_year].sort_values('mli', ascending=False)
    
    print(f"\n\nTop 10 States - Best Purchasing Power ({latest_year}):")
    print(f"{'State':<20s} {'MLI':>6s} {'Income':>11s} {'COL':>11s} {'Surplus':>11s}")
    print("-"*65)
    for i, (_, row) in enumerate(latest_data.head(10).iterrows(), 1):
        print(f"{i:2d}. {row['state']:20s} {row['mli']:6.3f} ${row['median_income']:>10,.0f} "
              f"${row['col']:>10,.0f} ${row['annual_surplus']:>10,.0f}")
    
    print(f"\n\nBottom 10 States - Worst Purchasing Power ({latest_year}):")
    print(f"{'State':<20s} {'MLI':>6s} {'Income':>11s} {'COL':>11s} {'Deficit':>11s}")
    print("-"*65)
    for i, (_, row) in enumerate(latest_data.tail(10).iloc[::-1].iterrows(), 1):
        deficit_label = "Surplus" if row['annual_surplus'] > 0 else "Deficit"
        print(f"{i:2d}. {row['state']:20s} {row['mli']:6.3f} ${row['median_income']:>10,.0f} "
              f"${row['col']:>10,.0f} ${row['annual_surplus']:>10,.0f}")
    
    # Key insights
    print("\n\nKEY INSIGHTS:")
    print("-"*70)
    
    # States at paycheck-to-paycheck (MLI ≈ 1.0)
    paycheck = latest_data[(latest_data['mli'] >= 0.95) & (latest_data['mli'] <= 1.05)]
    print(f"\n📊 Paycheck-to-Paycheck States (MLI 0.95-1.05): {len(paycheck)}")
    for state in paycheck['state'].head(5):
        print(f"   - {state}")
    
    # States with surplus (MLI > 1.2)
    surplus = latest_data[latest_data['mli'] > 1.2]
    print(f"\n💰 States with >20% Surplus (MLI > 1.2): {len(surplus)}")
    for state in surplus['state'].head(5):
        row = latest_data[latest_data['state'] == state].iloc[0]
        print(f"   - {state}: {row['surplus_pct']:.0f}% surplus (${row['annual_surplus']:,.0f}/year)")
    
    # States in deficit (MLI < 1.0)
    deficit = latest_data[latest_data['mli'] < 1.0]
    print(f"\n⚠️  States in Deficit (MLI < 1.0): {len(deficit)}")
    for state in deficit['state'].head(5):
        row = latest_data[latest_data['state'] == state].iloc[0]
        print(f"   - {state}: {row['surplus_pct']:.0f}% deficit (${row['annual_surplus']:,.0f}/year)")


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    """Execute complete MLI calculation pipeline"""
    
    print("\n" + "="*70)
    print(f"MEDIAN LIVING INDEX - SIMPLE RATIO ({QUINTILE})")
    print("Pure purchasing power: Income / Cost of Living")
    print("="*70)
    
    # Load all data
    income_df, bea_df, baseline_df = load_all_data()
    
    # Calculate state-adjusted costs
    costs_df = calculate_state_costs(bea_df, baseline_df)
    
    # Calculate MLI (simple ratio)
    mli_df = calculate_mli_simple(income_df, costs_df)
    
    # Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    mli_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✓ Saved MLI results to: {OUTPUT_FILE}")
    
    # Save detailed costs breakdown
    costs_detail_file = 'costs_breakdown_simple.csv'
    costs_df.to_csv(costs_detail_file, index=False)
    print(f"✓ Saved cost breakdown to: {costs_detail_file}")
    
    # Print summary
    print_summary(mli_df)
    
    print("\n" + "="*70)
    print("CALCULATION COMPLETE!")
    print("="*70)
    print(f"\nFormula: MLI = Median Income / Cost of Living")
    print(f"\nInterpretation:")
    print(f"  1.0 = Paycheck to paycheck (income = expenses)")
    print(f"  1.3 = 30% surplus for savings/investment")
    print(f"  0.9 = 10% deficit (going into debt)")
    
    return mli_df, costs_df


if __name__ == "__main__":
    mli_df, costs_df = main()