"""
MLI Data to JSON Converter - Updated for 2019 Base Year
========================================================

Converts MLI calculation results into website-ready JSON format.

Changes from old version:
- Uses 2019 as fixed base year (not yearly floating average)
- COL is now total annual expenses (not weighted basket)
- Cleaner, more intuitive numbers

Usage:
    python generate_mli_json_updated.py

Output:
    mli_data.json - Ready for website deployment
"""

import pandas as pd
import json
from datetime import datetime

print("="*80)
print("MLI TO JSON CONVERTER (2019 BASE YEAR)")
print("="*80)
print()

# ============================================================================
# STEP 1: Load MLI Results
# ============================================================================

print("[1/3] Loading MLI calculation results...")
print("-"*80)

try:
    mli_df = pd.read_csv('mli_results_14cat_q3.csv')
    costs_df = pd.read_csv('costs_breakdown_14cat_q3.csv')
    
    print(f"✓ Loaded {len(mli_df)} MLI observations")
    print(f"✓ Loaded {len(costs_df)} cost detail records")
    
    # Verify we have purchasing_power column (new version)
    if 'purchasing_power' in mli_df.columns:
        print("✓ Data is from updated calculation (with purchasing_power)")
        # Extract 2019 reference from the data
        df_2019 = mli_df[mli_df['year'] == 2019]
        reference_2019_pp = df_2019['purchasing_power'].mean()
        print(f"✓ 2019 reference PP: {reference_2019_pp:.4f}")
    else:
        print("⚠ Warning: Data may be from old calculation")
        print("  Run calculate_mli_14cat_FIXED.py first!")
        # Calculate it anyway
        mli_df['purchasing_power'] = mli_df['median_income'] / mli_df['col_index']
        df_2019 = mli_df[mli_df['year'] == 2019]
        reference_2019_pp = df_2019['purchasing_power'].mean()
        print(f"✓ Calculated 2019 reference PP: {reference_2019_pp:.4f}")
    
except FileNotFoundError as e:
    print(f"✗ Error: {e}")
    print("\nMake sure you've run calculate_mli_14cat_FIXED.py first!")
    exit(1)

print()

# ============================================================================
# STEP 2: Build JSON Structure
# ============================================================================

print("[2/3] Building JSON data structure...")
print("-"*80)

# Create comprehensive JSON structure
data = {
    'metadata': {
        'generated': datetime.now().isoformat(),
        'version': '2.0',
        'base_year': 2019,
        'base_year_reference_pp': round(reference_2019_pp, 4),
        'description': 'MLI = 100 represents the purchasing power of the average US household in 2019 (pre-pandemic baseline)',
        'formula': 'MLI = (Median Income / Total Cost of Living) / 5.2755 × 100',
        'col_interpretation': 'Cost of Living represents total estimated annual expenses for a median household',
        'changes_from_v1': [
            'COL is now total annual expenses (not weighted basket)',
            'MLI uses fixed 2019 baseline (not yearly floating average)',
            'Removed confusing weight multipliers'
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
        'avg_mli': round(float(year_data['mli'].mean()), 2),
        'avg_income': int(year_data['median_income'].mean()),
        'avg_col': round(float(year_data['col_index'].mean()), 2),
        'avg_pp': round(float(year_data['purchasing_power'].mean()), 4)
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
            'mli': round(float(row['mli']), 2),
            'income': int(row['median_income']),
            'col': round(float(row['col_index']), 2),
            'purchasing_power': round(float(row['purchasing_power']), 4)
        }
    
    # Latest year detailed breakdown
    latest_year = data['years'][-1]
    latest_mli = state_mli[state_mli['year'] == latest_year].iloc[0]
    latest_costs = state_costs[state_costs['year'] == latest_year]
    
    data['states'][state]['latest'] = {
        'year': latest_year,
        'mli': round(float(latest_mli['mli']), 2),
        'income': int(latest_mli['median_income']),
        'col': round(float(latest_mli['col_index']), 2),
        'purchasing_power': round(float(latest_mli['purchasing_power']), 4),
        'categories': {}
    }
    
    # Category breakdown (no weights in new version)
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

# Save with nice formatting
with open('mli_data.json', 'w') as f:
    json.dump(data, f, indent=2)

file_size_kb = len(json.dumps(data)) / 1024

print(f"✓ Generated mli_data.json")
print(f"  States: {len(data['states'])}")
print(f"  Years: {len(data['years'])} ({data['years'][0]}-{data['years'][-1]})")
print(f"  File size: {file_size_kb:.1f} KB")
print()

# ============================================================================
# STEP 4: Summary & Verification
# ============================================================================

print("="*80)
print("SUMMARY WITH 2019 BASE YEAR")
print("="*80)
print()

latest_year = data['years'][-1]
latest_data = mli_df[mli_df['year'] == latest_year].sort_values('mli', ascending=False)

print(f"Top 5 States ({latest_year}):")
print(f"{'State':<20} {'MLI':>8} {'Income':>12} {'COL':>12} {'PP':>8}")
print("-"*65)
for i, (_, row) in enumerate(latest_data.head(5).iterrows(), 1):
    print(f"{row['state']:<20} {row['mli']:>8.1f} ${row['median_income']:>11,} ${row['col_index']:>11,.0f} {row['purchasing_power']:>8.3f}")

print()
print(f"Bottom 5 States ({latest_year}):")
print(f"{'State':<20} {'MLI':>8} {'Income':>12} {'COL':>12} {'PP':>8}")
print("-"*65)
for i, (_, row) in enumerate(latest_data.tail(5).iloc[::-1].iterrows(), 1):
    print(f"{row['state']:<20} {row['mli']:>8.1f} ${row['median_income']:>11,} ${row['col_index']:>11,.0f} {row['purchasing_power']:>8.3f}")

print()
print(f"National Average ({latest_year}):")
print(f"  MLI: {data['national'][latest_year]['avg_mli']:.1f}")
print(f"  Income: ${data['national'][latest_year]['avg_income']:,}")
print(f"  COL: ${data['national'][latest_year]['avg_col']:,.0f}")
print(f"  PP: {data['national'][latest_year]['avg_pp']:.4f}")

print()
print("="*80)
print("INTERPRETATION GUIDE")
print("="*80)
print()
print("MLI Score Meanings:")
print("  100 = Same purchasing power as US average in 2019 (pre-pandemic)")
print("  110 = 10% better purchasing power than 2019 baseline")
print("  90 = 10% worse purchasing power than 2019 baseline")
print()
print("COL (Cost of Living):")
print("  Total estimated annual expenses for median household")
print("  Includes: housing, food, transportation, healthcare, etc.")
print("  Adjusted by state using BEA Regional Price Parities")
print()
print("Purchasing Power:")
print("  Income / COL ratio")
print("  Example: PP = 1.05 means income is 5% higher than expenses")
print()

# Show states above/below 2019 baseline
recovery = latest_data.set_index('state')['mli'] - 100

print("States ABOVE pre-pandemic baseline (MLI > 100):")
above = recovery[recovery > 0].sort_values(ascending=False)
print(f"  {len(above)} states have better purchasing power than 2019")
if len(above) > 0:
    print(f"  Top 3: {', '.join(above.head(3).index.tolist())}")

print()
print("States BELOW pre-pandemic baseline (MLI < 100):")
below = recovery[recovery < 0].sort_values()
print(f"  {len(below)} states have worse purchasing power than 2019")
if len(below) > 0:
    print(f"  Bottom 3: {', '.join(below.head(3).index.tolist())}")

print()
print("="*80)
print("JSON GENERATION COMPLETE!")
print("="*80)
print()
print("Next steps:")
print("  1. Copy mli_data.json to your website directory")
print("  2. Open index.html in browser to test")
print("  3. Deploy to web hosting")
print()
print("The website will automatically:")
print("  - Show years 2008-2023 (or whatever is in data)")
print("  - Display COL as total annual expenses")
print("  - Use 2019 as reference baseline")
print()
print("To add 2024 data (when available in Feb 2026):")
print("  1. Download Census ACS 2024 + BEA RPPs 2024")
print("  2. Run: python calculate_mli_14cat_FIXED.py")
print("  3. Run: python generate_mli_json_updated.py")
print("  4. Replace mli_data.json on website")