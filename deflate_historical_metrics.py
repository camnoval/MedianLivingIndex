"""
Generate CPI Deflators from Downloaded FRED Data
=================================================

Uses the cpi_data_downloaded.csv file we just created.
"""

import pandas as pd
import json

print("="*70)
print("GENERATING CPI DEFLATORS FROM DOWNLOADED DATA")
print("="*70)

# Load the downloaded CPI data
cpi_df = pd.read_csv('cpi_data_downloaded.csv', index_col=0)

# Convert column names to integers (years)
cpi_df.columns = cpi_df.columns.astype(float).astype(int)

print("\n✓ Loaded CPI data")
print(f"  Categories: {len(cpi_df)}")
print(f"  Years: {cpi_df.columns.min()}-{cpi_df.columns.max()}")

# Show what we have
print("\nAvailable years:", sorted(cpi_df.columns.tolist()))

# Check if we have 2023
if 2023 not in cpi_df.columns:
    print("\n⚠️  2023 not in data, using most recent year as baseline")
    baseline_year = cpi_df.columns.max()
    print(f"   Baseline year: {baseline_year}")
else:
    baseline_year = 2023

# Convert to dictionary format
cpi_data = {}
for category in cpi_df.index:
    cpi_data[category] = {}
    for year in cpi_df.columns:
        value = cpi_df.loc[category, year]
        if pd.notna(value):
            cpi_data[category][int(year)] = float(value)

print(f"\nConverted to dictionary format:")
for cat, years in cpi_data.items():
    print(f"  {cat:15s}: {len(years)} years")

# Handle missing categories
if 'recreation' not in cpi_data or len(cpi_data.get('recreation', {})) == 0:
    print("\n⚠️  'recreation' missing - using 'all_items' as proxy")
    cpi_data['recreation'] = cpi_data['all_items'].copy()

if 'other' not in cpi_data or len(cpi_data.get('other', {})) == 0:
    print("⚠️  'other' missing - using 'all_items' as proxy")
    cpi_data['other'] = cpi_data['all_items'].copy()

# Calculate deflators
print("\n" + "="*70)
print(f"CALCULATING DEFLATORS (Baseline: {baseline_year})")
print("="*70)

deflators = {}

for category, values in cpi_data.items():
    if baseline_year not in values:
        print(f"\n⚠️  {category}: No {baseline_year} data, skipping")
        continue
    
    baseline_value = values[baseline_year]
    deflators[category] = {}
    
    # Get all years from 2008-2023 (excluding 2020)
    for year in range(2008, 2024):
        if year == 2020:  # No ACS data for 2020
            continue
        if year in values:
            deflators[category][year] = values[year] / baseline_value
    
    # Print summary
    if 2008 in deflators[category]:
        deflator_2008 = deflators[category][2008]
        inflation = ((1/deflator_2008) - 1) * 100
        
        print(f"\n{category.upper():20s}")
        print(f"  2008 CPI: {values[2008]:.1f}")
        print(f"  {baseline_year} CPI: {baseline_value:.1f}")
        print(f"  Deflator 2008: {deflator_2008:.4f}")
        print(f"  Inflation: +{inflation:.1f}%")

if len(deflators) == 0:
    print("\n❌ ERROR: No deflators calculated!")
    print("\nDEBUGGING INFO:")
    print(f"  Baseline year: {baseline_year}")
    print(f"  Categories in cpi_data: {list(cpi_data.keys())}")
    for cat in cpi_data:
        print(f"  {cat}: years available = {sorted(cpi_data[cat].keys())}")
    exit(1)

# Map to your BLS categories
print("\n" + "="*70)
print("MAPPING TO BLS SPENDING CATEGORIES")
print("="*70)

category_mapping = {
    'food': 'food',
    'housing': 'housing',  # Use 'shelter' for rent-only if preferred
    'transportation': 'transport',
    'healthcare': 'medical',
    'entertainment': 'recreation',
    'apparel': 'apparel',
    'education': 'education',
    'personal_insurance': 'other',
    'personal_care': 'other',
    'reading': 'other',
    'tobacco': 'other',
    'miscellaneous': 'other',
    'alcohol': 'food',
    'cash_contributions': None  # No adjustment
}

mapped_deflators = {}

for bls_cat, cpi_cat in category_mapping.items():
    if cpi_cat is None:
        # No adjustment
        years = range(2008, 2024)
        mapped_deflators[bls_cat] = {year: 1.0 for year in years if year != 2020}
        print(f"{bls_cat:20s} → No adjustment")
    elif cpi_cat in deflators:
        mapped_deflators[bls_cat] = deflators[cpi_cat]
        sample_2008 = deflators[cpi_cat].get(2008, 'N/A')
        print(f"{bls_cat:20s} → {cpi_cat:15s} (2008 deflator: {sample_2008})")
    else:
        print(f"⚠️  {bls_cat:20s} → {cpi_cat:15s} (MISSING)")

# Save results
print("\n" + "="*70)
print("SAVING RESULTS")
print("="*70)

# 1. All deflators
df_deflators = pd.DataFrame(deflators).T
df_deflators = df_deflators.reindex(sorted(df_deflators.columns), axis=1)
df_deflators.to_csv('cpi_deflators_verified.csv')
print("\n✓ cpi_deflators_verified.csv")

# 2. Mapped to BLS categories
df_mapped = pd.DataFrame(mapped_deflators).T
df_mapped = df_mapped.reindex(sorted(df_mapped.columns), axis=1)
df_mapped.to_csv('cpi_deflators_bls_categories.csv')
print("✓ cpi_deflators_bls_categories.csv ← USE THIS")

print("\nSample of mapped deflators:")
print(df_mapped.head())

# 3. Metadata
metadata = {
    'baseline_year': int(baseline_year),
    'source': 'FRED (Federal Reserve Economic Data)',
    'download_date': pd.Timestamp.now().isoformat(),
    'categories': list(mapped_deflators.keys()),
    'years': sorted([int(y) for y in df_mapped.columns]),
    'note': 'Deflators multiply baseline year costs to get historical costs'
}

with open('cpi_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("✓ cpi_metadata.json")

# Show example
print("\n" + "="*70)
print("EXAMPLE CALCULATION")
print("="*70)

if 'housing' in mapped_deflators and 2008 in mapped_deflators['housing']:
    housing_2008 = mapped_deflators['housing'][2008]
    housing_baseline = mapped_deflators['housing'][baseline_year]
    
    print(f"\nIf BLS baseline says housing = $23,650 ({baseline_year}):")
    print(f"\n2008 National Average:")
    print(f"  $23,650 × {housing_2008:.4f} = ${23650 * housing_2008:,.0f}")
    print(f"\n{baseline_year} National Average:")
    print(f"  $23,650 × {housing_baseline:.4f} = ${23650 * housing_baseline:,.0f}")
    
    inflation = ((1/housing_2008) - 1) * 100
    print(f"\nHousing inflation 2008-{baseline_year}: +{inflation:.1f}%")
    
    print("\nThen apply state RPP:")
    print("  Alabama 2008: ${:,.0f} × 0.599 = ${:,.0f}".format(
        23650 * housing_2008,
        23650 * housing_2008 * 0.599
    ))
else:
    print("\n⚠️  Cannot show example - housing data missing")

print("\n" + "="*70)
print("✓ COMPLETE - Verified with official FRED data")
print("="*70)