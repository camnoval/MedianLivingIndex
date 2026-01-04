"""
MLI Data to JSON Converter - SIMPLIFIED RATIO VERSION
======================================================

Converts simple MLI ratios (Income/COL) into website-ready JSON format.

MLI interpretation:
- 1.0 = Paycheck to paycheck (income = expenses)
- 1.3 = 30% surplus
- 0.9 = 10% deficit

Usage:
    python generate_mli_json_simple.py

Output:
    mli_data.json - Ready for website deployment
"""

import pandas as pd
import json
from datetime import datetime

print("="*80)
print("MLI TO JSON CONVERTER (SIMPLE RATIO)")
print("="*80)
print()

# ============================================================================
# STEP 1: Load MLI Results
# ============================================================================

print("[1/3] Loading MLI calculation results...")
print("-"*80)

try:
    mli_df = pd.read_csv('mli_results_simple.csv')
    costs_df = pd.read_csv('costs_breakdown_simple.csv')
    
    print(f"✓ Loaded {len(mli_df)} MLI observations")
    print(f"✓ Loaded {len(costs_df)} cost detail records")
    
    # Show range
    print(f"\nMLI range: {mli_df['mli'].min():.3f} - {mli_df['mli'].max():.3f}")
    
except FileNotFoundError as e:
    print(f"✗ Error: {e}")
    print("\nMake sure you've run calculate_mli_simple.py first!")
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
        'version': '3.0',
        'formula': 'MLI = Median Income / Cost of Living',
        'description': 'Simple purchasing power ratio',
        'interpretation': {
            '1.0': 'Income exactly covers expenses (paycheck to paycheck)',
            'above_1.0': 'Income exceeds expenses (surplus for savings)',
            'below_1.0': 'Income below expenses (deficit/debt)'
        },
        'col_interpretation': 'Cost of Living = total estimated annual expenses for median household'
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
        'avg_surplus': int(year_data['annual_surplus'].mean())
    }

print(f"✓ Processed {len(data['years'])} years")

# Build state data
print("\nProcessing state data...")
for state in sorted(mli_df['state'].unique()):
    state_mli = mli_df[mli_df['state'] == state].sort_values('year')
    state_costs = costs_df[costs_df['state'] == state]
    
    data['states'][state] = {
        'name': state,
        'timeseries': {},
        'latest': {}
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
        'categories': {}
    }
    
    # Category breakdown
    for _, cost_row in latest_costs.iterrows():
        data['states'][state]['latest']['categories'][cost_row['category']] = {
            'cost': round(float(cost_row['cost']), 2)
        }

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
print("SUMMARY (SIMPLE RATIO)")
print("="*80)
print()

latest_year = data['years'][-1]
latest_data = mli_df[mli_df['year'] == latest_year].sort_values('mli', ascending=False)

print(f"Top 5 States ({latest_year}):")
print(f"{'State':<20} {'MLI':>7} {'Income':>12} {'COL':>12} {'Surplus':>12}")
print("-"*70)
for _, row in latest_data.head(5).iterrows():
    print(f"{row['state']:<20} {row['mli']:7.3f} ${row['median_income']:>11,} "
          f"${row['col']:>11,.0f} ${row['annual_surplus']:>11,.0f}")

print()
print(f"Bottom 5 States ({latest_year}):")
print(f"{'State':<20} {'MLI':>7} {'Income':>12} {'COL':>12} {'Surplus':>12}")
print("-"*70)
for _, row in latest_data.tail(5).iloc[::-1].iterrows():
    print(f"{row['state']:<20} {row['mli']:7.3f} ${row['median_income']:>11,} "
          f"${row['col']:>11,.0f} ${row['annual_surplus']:>11,.0f}")

print()
print(f"National Average ({latest_year}):")
print(f"  MLI: {data['national'][latest_year]['avg_mli']:.3f}")
print(f"  Income: ${data['national'][latest_year]['avg_income']:,}")
print(f"  COL: ${data['national'][latest_year]['avg_col']:,.0f}")
print(f"  Surplus: ${data['national'][latest_year]['avg_surplus']:,}")

print()
print("="*80)
print("INTERPRETATION GUIDE")
print("="*80)
print()
print("MLI Score Meanings:")
print("  1.0 = Income exactly covers expenses (paycheck to paycheck)")
print("  1.3 = Income is 30% higher than expenses (30% savings rate)")
print("  0.9 = Income is 10% lower than expenses (10% deficit)")
print()
print("Examples:")
print("  Mississippi: MLI = 0.93 → Spending 7% more than earning")
print("  Utah: MLI = 1.35 → Earning 35% more than spending")
print()

# Distribution analysis
paycheck = latest_data[(latest_data['mli'] >= 0.95) & (latest_data['mli'] <= 1.05)]
surplus = latest_data[latest_data['mli'] > 1.2]
deficit = latest_data[latest_data['mli'] < 1.0]

print(f"State Distribution:")
print(f"  Surplus (>20%): {len(surplus)} states")
print(f"  Paycheck-to-paycheck (±5%): {len(paycheck)} states")
print(f"  Deficit (<0%): {len(deficit)} states")

print()
print("="*80)
print("JSON GENERATION COMPLETE!")
print("="*80)

