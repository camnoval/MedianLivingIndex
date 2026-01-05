"""
Calculate Median Living Index (MLI) - WITH INFLATION ADJUSTMENT
================================================================

The CORRECT approach that accounts for:
1. Time: CPI inflation from 2008-2023
2. Space: BEA RPP state cost differences

MLI = Median Income / Cost of Living

Where Cost of Living = Sum of:
  baseline_2023 × CPI_deflator[year] × BEA_RPP[state,year] / 100

This gives you the TRUE cost of living in each state-year, then calculates
purchasing power as a simple ratio.

Output: mli_results_14cat_q3.csv
"""

import pandas as pd
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

INCOME_FILE = 'census_income_data_20260103.csv'
BEA_RPPS_FILE = 'bea_component_rpps.csv'
BLS_BASELINE_FILE = 'BLS_baseline_spending.csv'
CPI_DEFLATORS_FILE = 'cpi_deflators_bls_categories.csv'

QUINTILE = 'Q3'  # Middle class (50th percentile)

OUTPUT_FILE = f'mli_results_14cat_{QUINTILE.lower()}.csv'
COSTS_OUTPUT_FILE = f'costs_breakdown_14cat_{QUINTILE.lower()}.csv'

# ============================================================================
# LOAD DATA
# ============================================================================

def load_all_data():
    """Load income, BEA RPPs, BLS baselines, and CPI deflators"""
    
    print("="*70)
    print(f"LOADING DATA FOR {QUINTILE} (WITH INFLATION ADJUSTMENT)")
    print("="*70)
    
    # 1. Income data
    print("\n[1/4] Loading median household income...")
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
    print("\n[2/4] Loading BEA component RPPs...")
    bea_df = pd.read_csv(BEA_RPPS_FILE)
    bea_df['year'] = bea_df['year'].astype(int)
    bea_df['state'] = bea_df['state'].astype(str).str.strip()
    print(f"  ✓ {len(bea_df)} observations")
    
    # 3. BLS baseline spending
    print("\n[3/4] Loading BLS baseline spending...")
    baseline_df = pd.read_csv(BLS_BASELINE_FILE)
    
    baseline_col = f'{QUINTILE.lower()}_baseline'
    baseline_df = baseline_df[['category', baseline_col, 'bea_adjuster']].copy()
    baseline_df = baseline_df.rename(columns={baseline_col: 'baseline_spending'})
    
    print(f"  ✓ {len(baseline_df)} categories")
    print(f"  Total 2023 baseline: ${baseline_df['baseline_spending'].sum():,.0f}/year")
    
    # 4. CPI deflators
    print("\n[4/4] Loading CPI deflators...")
    cpi_df = pd.read_csv(CPI_DEFLATORS_FILE, index_col=0)
    
    # Convert column names to integers
    cpi_df.columns = cpi_df.columns.astype(int)
    
    print(f"  ✓ {len(cpi_df)} categories")
    print(f"  Years: {cpi_df.columns.min()}-{cpi_df.columns.max()}")
    
    # Convert to dictionary for easy lookup
    cpi_deflators = {}
    for category in cpi_df.index:
        cpi_deflators[category] = cpi_df.loc[category].to_dict()
    
    return income_df, bea_df, baseline_df, cpi_deflators


# Map BLS categories to CPI deflator categories (in case names differ)
CATEGORY_MAPPING = {
    'food': 'food',
    'housing': 'housing',
    'transportation': 'transportation',
    'healthcare': 'healthcare',
    'personal_insurance': 'personal_insurance',
    'entertainment': 'entertainment',
    'apparel': 'apparel',
    'personal_care': 'personal_care',
    'reading': 'reading',
    'education': 'education',
    'tobacco': 'tobacco',
    'miscellaneous': 'miscellaneous',
    'cash_contributions': 'cash_contributions',
    'alcohol': 'alcohol'
}

def calculate_state_costs_with_inflation(bea_df, baseline_df, cpi_deflators):
    """
    Calculate TRUE state-year-specific costs accounting for BOTH:
    1. Time (CPI inflation)
    2. Space (BEA RPP state differences)
    
    Formula: cost = baseline_2023 × CPI_deflator[year] × BEA_RPP[state,year] / 100
    """
    
    print("\n" + "="*70)
    print("CALCULATING INFLATION-ADJUSTED STATE COSTS")
    print("="*70)
    print("\nFormula: cost = baseline_2023 × CPI_deflator × state_RPP")
    
    all_costs = []
    
    for _, cat in baseline_df.iterrows():
        category = cat['category']
        baseline_2023 = cat['baseline_spending']
        bea_adjuster = cat['bea_adjuster']
        
        # Get CPI deflator category
        cpi_category = CATEGORY_MAPPING.get(category, category)
        
        print(f"\n{category:20s} (2023 baseline: ${baseline_2023:>6,.0f})")
        
        if category not in cpi_deflators:
            print(f"  ⚠️  No CPI deflator for '{category}', using 1.0")
            category_deflators = {year: 1.0 for year in range(2008, 2024)}
        else:
            category_deflators = cpi_deflators[category]
        
        if bea_adjuster == 'none':
            # No regional adjustment, only time adjustment
            print(f"  → Time-adjusted only (CPI deflator)")
            
            for state in bea_df['state'].unique():
                for year in bea_df['year'].unique():
                    if year not in category_deflators:
                        continue
                    
                    deflator = category_deflators[year]
                    real_cost = baseline_2023 * deflator
                    
                    all_costs.append({
                        'state': state,
                        'year': year,
                        'category': category,
                        'cost': real_cost
                    })
        else:
            # Both time and regional adjustment
            rpp_col = bea_adjuster
            print(f"  → Time + space adjusted (CPI × {rpp_col})")
            
            for _, row in bea_df.iterrows():
                year = row['year']
                state = row['state']
                
                if year not in category_deflators:
                    continue
                
                deflator = category_deflators[year]
                rpp_value = row[rpp_col]
                
                # Apply both adjustments
                real_cost = baseline_2023 * deflator * (rpp_value / 100)
                
                all_costs.append({
                    'state': state,
                    'year': year,
                    'category': category,
                    'cost': real_cost
                })
    
    costs_df = pd.DataFrame(all_costs)
    print(f"\n✓ Calculated {len(costs_df)} state-year-category costs")
    
    # Verification: Check that costs increased over time
    print("\nVERIFICATION - Did costs inflate correctly?")
    for sample_cat in ['housing', 'food', 'transportation']:
        cat_data = costs_df[costs_df['category'] == sample_cat]
        avg_2008 = cat_data[cat_data['year'] == 2008]['cost'].mean()
        avg_2023 = cat_data[cat_data['year'] == 2023]['cost'].mean()
        inflation = ((avg_2023 / avg_2008) - 1) * 100
        print(f"  {sample_cat:15s}: 2008 avg ${avg_2008:>8,.0f} → 2023 avg ${avg_2023:>8,.0f} (+{inflation:.1f}%)")
    
    return costs_df


# ============================================================================
# MLI CALCULATION
# ============================================================================

def calculate_mli(income_df, costs_df):
    """
    Calculate MLI as simple ratio:
    MLI = Median Income / Cost of Living
    
    Now with REAL inflation-adjusted costs!
    """
    
    print("\n" + "="*70)
    print("CALCULATING MLI (INFLATION-ADJUSTED)")
    print("="*70)
    
    # Sum costs to get total COL
    col_df = costs_df.groupby(['state', 'year'])['cost'].sum().reset_index()
    col_df = col_df.rename(columns={'cost': 'col'})
    
    print(f"\n✓ Calculated COL for {len(col_df)} state-years")
    print(f"  COL range: ${col_df['col'].min():,.0f} - ${col_df['col'].max():,.0f}")
    
    # Check inflation in COL
    col_2008 = col_df[col_df['year'] == 2008]['col'].mean()
    col_2023 = col_df[col_df['year'] == 2023]['col'].mean()
    col_inflation = ((col_2023 / col_2008) - 1) * 100
    print(f"\n  Total COL inflation 2008-2023: +{col_inflation:.1f}% ✓")
    
    # Merge with income
    df = income_df.merge(col_df, on=['state', 'year'], how='inner')
    
    # Calculate MLI as simple ratio
    df['mli'] = df['median_income'] / df['col']
    
    # Round for readability
    df['mli'] = df['mli'].round(3)
    df['col'] = df['col'].round(2)
    
    print(f"\n✓ Calculated MLI for {len(df)} observations")
    print(f"  MLI range: {df['mli'].min():.3f} - {df['mli'].max():.3f}")
    
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
    print(f"MLI SUMMARY STATISTICS (INFLATION-ADJUSTED)")
    print("="*70)
    
    latest_year = mli_df['year'].max()
    latest_data = mli_df[mli_df['year'] == latest_year].sort_values('mli', ascending=False)
    
    print(f"\n\nTop 10 States - Best Purchasing Power ({latest_year}):")
    print(f"{'State':<20s} {'MLI':>6s} {'Income':>11s} {'COL':>11s} {'Surplus':>11s}")
    print("-"*65)
    for i, (_, row) in enumerate(latest_data.head(10).iterrows(), 1):
        print(f"{i:2d}. {row['state']:<20s} {row['mli']:6.3f} ${row['median_income']:>10,.0f} "
              f"${row['col']:>10,.0f} ${row['annual_surplus']:>10,.0f}")
    
    print(f"\n\nBottom 10 States - Worst Purchasing Power ({latest_year}):")
    print(f"{'State':<20s} {'MLI':>6s} {'Income':>11s} {'COL':>11s} {'Deficit':>11s}")
    print("-"*65)
    for i, (_, row) in enumerate(latest_data.tail(10).iloc[::-1].iterrows(), 1):
        print(f"{i:2d}. {row['state']:<20s} {row['mli']:6.3f} ${row['median_income']:>10,.0f} "
              f"${row['col']:>10,.0f} ${row['annual_surplus']:>10,.0f}")
    
    # Historical comparison
    print("\n\nHISTORICAL TRENDS (2008 vs 2023):")
    print("-"*70)
    
    mli_2008 = mli_df[mli_df['year'] == 2008]
    mli_2023 = mli_df[mli_df['year'] == 2023]
    
    print(f"\nNational Averages:")
    print(f"  2008: MLI = {mli_2008['mli'].mean():.3f}, Avg COL = ${mli_2008['col'].mean():,.0f}")
    print(f"  2023: MLI = {mli_2023['mli'].mean():.3f}, Avg COL = ${mli_2023['col'].mean():,.0f}")
    
    # States that improved vs declined
    comparison = mli_2008[['state', 'mli']].merge(
        mli_2023[['state', 'mli']], 
        on='state', 
        suffixes=('_2008', '_2023')
    )
    comparison['change'] = comparison['mli_2023'] - comparison['mli_2008']
    
    improved = (comparison['change'] > 0).sum()
    declined = (comparison['change'] < 0).sum()
    
    print(f"\n  States that improved: {improved}")
    print(f"  States that declined: {declined}")
    
    print("\n  Biggest improvers:")
    for _, row in comparison.nlargest(5, 'change').iterrows():
        print(f"    {row['state']:20s}: {row['mli_2008']:.3f} → {row['mli_2023']:.3f} (+{row['change']:.3f})")
    
    print("\n  Biggest decliners:")
    for _, row in comparison.nsmallest(5, 'change').iterrows():
        print(f"    {row['state']:20s}: {row['mli_2008']:.3f} → {row['mli_2023']:.3f} ({row['change']:.3f})")


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    """Execute complete MLI calculation pipeline"""
    
    print("\n" + "="*70)
    print(f"MEDIAN LIVING INDEX - INFLATION-ADJUSTED ({QUINTILE})")
    print("Real purchasing power accounting for time AND space")
    print("="*70)
    
    # Load all data
    income_df, bea_df, baseline_df, cpi_deflators = load_all_data()
    
    # Calculate inflation-adjusted state costs
    costs_df = calculate_state_costs_with_inflation(bea_df, baseline_df, cpi_deflators)
    
    # Calculate MLI
    mli_df = calculate_mli(income_df, costs_df)
    
    # Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    mli_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✓ Saved MLI results to: {OUTPUT_FILE}")
    
    costs_df.to_csv(COSTS_OUTPUT_FILE, index=False)
    print(f"✓ Saved cost breakdown to: {COSTS_OUTPUT_FILE}")
    
    # Print summary
    print_summary(mli_df)
    
    print("\n" + "="*70)
    print("CALCULATION COMPLETE!")
    print("="*70)
    print(f"\nThis version accounts for:")
    print(f"  ✓ Inflation (CPI 2008-2023)")
    print(f"  ✓ State cost differences (BEA RPPs)")
    print(f"  ✓ Income quintile ({QUINTILE})")
    
    return mli_df, costs_df


if __name__ == "__main__":
    mli_df, costs_df = main()