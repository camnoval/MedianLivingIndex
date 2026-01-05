"""
MLI Data to JSON Converter - INFLATION-CORRECTED VERSION
=========================================================

Converts inflation-adjusted MLI data into website-ready JSON format.

MLI interpretation:
- 1.0 = Paycheck to paycheck (income = expenses)
- 1.3 = 30% surplus
- 0.9 = 10% deficit

Usage:
    python generate_mli_json.py

Output:
    mli_data.json - Ready for website deployment
"""

import pandas as pd
import json
from datetime import datetime

print("="*80)
print("MLI TO JSON CONVERTER (INFLATION-CORRECTED)")
print("="*80)
print()

# ============================================================================
# STEP 1: Load MLI Results
# ============================================================================

print("[1/3] Loading MLI calculation results...")
print("-"*80)

try:
    # Use the inflation-corrected files
    mli_df = pd.read_csv('mli_results_14cat_q3.csv')
    costs_df = pd.read_csv('costs_breakdown_14cat_q3.csv')
    
    print(f"✓ Loaded {len(mli_df)} MLI observations")
    print(f"✓ Loaded {len(costs_df)} cost detail records")
    
    # Show range
    print(f"\nMLI range: {mli_df['mli'].min():.3f} - {mli_df['mli'].max():.3f}")
    print(f"Years: {sorted(mli_df['year'].unique())}")
    
except FileNotFoundError as e:
    print(f"✗ Error: {e}")
    print("\nMake sure you've run calculate_mli.py first!")
    exit(1)

print()

# ============================================================================
# STEP 2: Build JSON Structure
# ============================================================================

print("[2/3] Building JSON data structure...")
print("-"*80)

data = {
    'metadata': {
        'generated': datetime.now().isoformat(),
        'version': '4.0',
        'formula': 'MLI = Median Income / Cost of Living',
        'description': 'Inflation-adjusted purchasing power ratio',
        'methodology': {
            'income': 'Census Bureau ACS 1-year estimates',
            'costs': 'BLS Consumer Expenditure Survey baseline × CPI deflators × BEA RPPs',
            'inflation': 'CPI-U component indices (2008-2023)',
            'state_adjustment': 'BEA Regional Price Parities'
        },
        'interpretation': {
            '1.0': 'Income exactly covers expenses (paycheck to paycheck)',
            'above_1.0': 'Income exceeds expenses (surplus for savings)',
            'below_1.0': 'Income below expenses (deficit/debt)'
        },
        'notes': [
            'Cost of Living accounts for actual inflation 2008-2023',
            'Housing inflation: ~48% (2008-2023)',
            'Overall COL inflation: ~41% (2008-2023)',
            'Middle class = Q3 (50th percentile) household income'
        ]
    },
    'years': sorted(mli_df['year'].unique().tolist()),
    'states': {},
    'national': {}
}

# Calculate national stats for each year
print("\nCalculating national statistics...")
for year in data['years']:
    year_data = mli_df[mli_df['year'] == year]
    
    data['national'][year] = {
        'avg_mli': round(float(year_data['mli'].mean()), 3),
        'avg_income': int(year_data['median_income'].mean()),
        'avg_col': round(float(year_data['col'].mean()), 2),
        'avg_surplus': int(year_data['annual_surplus'].mean()),
        'states_can_save': int((year_data['mli'] > 1.05).sum()),
        'states_paycheck_to_paycheck': int(((year_data['mli'] >= 0.95) & (year_data['mli'] <= 1.05)).sum()),
        'states_in_deficit': int((year_data['mli'] < 0.95).sum())
    }

print(f"✓ Processed {len(data['years'])} years")

# Calculate historical trends for metadata
if 2012 in data['years'] and 2023 in data['years']:
    col_2012 = data['national'][2012]['avg_col']
    col_2023 = data['national'][2023]['avg_col']
    col_inflation = ((col_2023 / col_2012) - 1) * 100
    
    mli_2012 = data['national'][2012]['avg_mli']
    mli_2023 = data['national'][2023]['avg_mli']
    mli_change = ((mli_2023 / mli_2012) - 1) * 100
    
    data['metadata']['historical_trends'] = {
        '2012_2023': {
            'col_inflation': round(col_inflation, 1),
            'mli_change': round(mli_change, 1),
            'interpretation': f"Cost of living increased {col_inflation:.0f}%, purchasing power increased {mli_change:.0f}%"
        }
    }

# Build state data
print("\nProcessing state data...")
for state in sorted(mli_df['state'].unique()):
    state_mli = mli_df[mli_df['state'] == state].sort_values('year')
    state_costs = costs_df[costs_df['state'] == state]
    
    data['states'][state] = {
        'name': state,
        'timeseries': {},
        'latest': {},
        'historical': {}
    }
    
    # Time series data
    for _, row in state_mli.iterrows():
        year = int(row['year'])
        data['states'][state]['timeseries'][year] = {
            'mli': round(float(row['mli']), 3),
            'income': int(row['median_income']),
            'col': round(float(row['col']), 2),
            'surplus': int(row['annual_surplus']),
            'surplus_pct': round(float(row['surplus_pct']), 1)
        }
    
    # Historical comparison (2012 vs 2023)
    if 2012 in state_mli['year'].values and 2023 in state_mli['year'].values:
        mli_2012 = state_mli[state_mli['year'] == 2012].iloc[0]
        mli_2023 = state_mli[state_mli['year'] == 2023].iloc[0]
        
        data['states'][state]['historical'] = {
            'mli_change_2012_2023': round(float(mli_2023['mli'] - mli_2012['mli']), 3),
            'mli_change_pct': round(((mli_2023['mli'] / mli_2012['mli']) - 1) * 100, 1),
            'col_change_2012_2023': round(float(mli_2023['col'] - mli_2012['col']), 2),
            'improved': bool(mli_2023['mli'] > mli_2012['mli'])
        }
    
    # Latest year detailed breakdown
    latest_year = data['years'][-1]
    latest_mli = state_mli[state_mli['year'] == latest_year].iloc[0]
    latest_costs = state_costs[state_costs['year'] == latest_year]
    
    data['states'][state]['latest'] = {
        'year': latest_year,
        'mli': round(float(latest_mli['mli']), 3),
        'income': int(latest_mli['median_income']),
        'col': round(float(latest_mli['col']), 2),
        'surplus': int(latest_mli['annual_surplus']),
        'surplus_pct': round(float(latest_mli['surplus_pct']), 1),
        'rank': None,  # Will calculate below
        'categories': {}
    }
    
    # Category breakdown
    for _, cost_row in latest_costs.iterrows():
        data['states'][state]['latest']['categories'][cost_row['category']] = {
            'cost': round(float(cost_row['cost']), 2)
        }

# Calculate rankings
print("\nCalculating state rankings...")
latest_year = data['years'][-1]
latest_rankings = mli_df[mli_df['year'] == latest_year].sort_values('mli', ascending=False)

for rank, (_, row) in enumerate(latest_rankings.iterrows(), 1):
    state = row['state']
    data['states'][state]['latest']['rank'] = rank

print(f"✓ Processed {len(data['states'])} states")
print()

# ============================================================================
# STEP 3: Save JSON
# ============================================================================

print("[3/3] Saving JSON file...")
print("-"*80)

with open('mli_data.json', 'w') as f:
    json.dump(data, f, indent=2)

file_size_kb = len(json.dumps(data)) / 1024

print(f"✓ Generated mli_data.json")
print(f"  States: {len(data['states'])}")
print(f"  Years: {len(data['years'])} ({data['years'][0]}-{data['years'][-1]})")
print(f"  File size: {file_size_kb:.1f} KB")
print()

# ============================================================================
# STEP 4: Summary
# ============================================================================

print("="*80)
print("SUMMARY (INFLATION-CORRECTED)")
print("="*80)
print()

latest_year = data['years'][-1]
latest_data = mli_df[mli_df['year'] == latest_year].sort_values('mli', ascending=False)

print(f"Top 5 States ({latest_year}):")
print(f"{'Rank':<5} {'State':<20} {'MLI':>7} {'Income':>12} {'COL':>12} {'Surplus':>12}")
print("-"*75)
for rank, (_, row) in enumerate(latest_data.head(5).iterrows(), 1):
    print(f"{rank:<5} {row['state']:<20} {row['mli']:7.3f} ${row['median_income']:>11,} "
          f"${row['col']:>11,.0f} ${row['annual_surplus']:>11,.0f}")

print()
print(f"Bottom 5 States ({latest_year}):")
print(f"{'Rank':<5} {'State':<20} {'MLI':>7} {'Income':>12} {'COL':>12} {'Surplus':>12}")
print("-"*75)
for rank, (_, row) in enumerate(latest_data.tail(5).iloc[::-1].iterrows(), len(latest_data)-4):
    print(f"{rank:<5} {row['state']:<20} {row['mli']:7.3f} ${row['median_income']:>11,} "
          f"${row['col']:>11,.0f} ${row['annual_surplus']:>11,.0f}")

print()
print(f"National Average ({latest_year}):")
print(f"  MLI: {data['national'][latest_year]['avg_mli']:.3f}")
print(f"  Income: ${data['national'][latest_year]['avg_income']:,}")
print(f"  COL: ${data['national'][latest_year]['avg_col']:,.0f}")
print(f"  Surplus: ${data['national'][latest_year]['avg_surplus']:,}")

print()
print("="*80)
print("KEY FINDINGS")
print("="*80)
print()

if 'historical_trends' in data['metadata']:
    trends = data['metadata']['historical_trends']['2012_2023']
    print(f"2012-2023 Trends:")
    print(f"  Cost of Living inflation: +{trends['col_inflation']:.1f}%")
    print(f"  Purchasing Power change: +{trends['mli_change']:.1f}%")
    print()

print(f"Current State Distribution ({latest_year}):")
print(f"  Can save (>5% surplus):     {data['national'][latest_year]['states_can_save']} states")
print(f"  Paycheck-to-paycheck (±5%): {data['national'][latest_year]['states_paycheck_to_paycheck']} states")
print(f"  In deficit (<-5%):          {data['national'][latest_year]['states_in_deficit']} states")

print()
print("="*80)
print("JSON GENERATION COMPLETE!")
print("="*80)
print()
print("This data accounts for:")
print("  ✓ Real inflation (CPI 2008-2023)")
print("  ✓ State cost differences (BEA RPPs)")
print("  ✓ Middle class income (Q3/median)")