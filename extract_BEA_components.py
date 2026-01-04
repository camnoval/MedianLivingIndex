"""
Extract BEA Component RPPs
===========================

Extracts the 4 BEA Regional Price Parity components from SARPP file:
- LineCode 6: Goods RPP
- LineCode 7: Housing Services RPP  
- LineCode 8: Utilities RPP
- LineCode 9: Other Services RPP

Output: bea_component_rpps.csv
"""

import pandas as pd

print("="*70)
print("EXTRACTING BEA COMPONENT RPPs")
print("="*70)

# Load BEA data
print("\nLoading SARPP_STATE_2008_2023.csv...")
bea_df = pd.read_csv('SARPP_STATE_2008_2023.csv')

print(f"✓ Loaded {len(bea_df)} rows")

# Component mappings
COMPONENTS = {
    6: 'goods_rpp',
    7: 'housing_rpp',
    8: 'utilities_rpp',
    9: 'other_services_rpp'
}

# Extract each component
print("\nExtracting components...")

all_components = []

for linecode, component_name in COMPONENTS.items():
    print(f"  Processing LineCode {linecode}: {component_name}")
    
    # Filter for this component
    component_df = bea_df[bea_df['LineCode'] == linecode].copy()
    
    if len(component_df) == 0:
        print(f"    ⚠ Warning: No data found for LineCode {linecode}")
        continue
    
    # Get year columns (2008-2023, excluding 2020)
    years = [str(y) for y in range(2008, 2024) if y != 2020]
    
    # Reshape from wide to long
    component_long = pd.melt(
        component_df,
        id_vars=['GeoFIPS', 'GeoName'],
        value_vars=years,
        var_name='year',
        value_name=component_name
    )
    
    # Clean up
    component_long['year'] = component_long['year'].astype(int)
    component_long[component_name] = pd.to_numeric(component_long[component_name], errors='coerce')
    
    all_components.append(component_long)
    print(f"    ✓ Extracted {len(component_long)} observations")

# Merge all components
print("\nMerging components...")

result = all_components[0]
for df in all_components[1:]:
    result = result.merge(
        df,
        on=['GeoFIPS', 'GeoName', 'year'],
        how='outer'
    )

# Clean up state names and filter
result['GeoName'] = result['GeoName'].str.strip()
result = result[result['GeoName'] != 'United States']  # Remove aggregate

# Rename columns
result = result.rename(columns={'GeoName': 'state'})
result = result[['state', 'year', 'goods_rpp', 'housing_rpp', 'utilities_rpp', 'other_services_rpp']]

# Sort
result = result.sort_values(['state', 'year']).reset_index(drop=True)

# Save
output_file = 'bea_component_rpps.csv'
result.to_csv(output_file, index=False)

print(f"\n✓ Saved to {output_file}")
print(f"  Rows: {len(result)}")
print(f"  States: {result['state'].nunique()}")
print(f"  Years: {sorted(result['year'].unique())}")

# Show summary stats
print("\n" + "="*70)
print("COMPONENT RPP SUMMARY STATISTICS")
print("="*70)
print(result.describe())

# Show sample data
print("\n" + "="*70)
print("SAMPLE DATA (First 10 rows)")
print("="*70)
print(result.head(10))

# Show state variation examples (2023)
print("\n" + "="*70)
print("STATE VARIATION EXAMPLES (2023)")
print("="*70)

data_2023 = result[result['year'] == 2023].sort_values('housing_rpp')

print("\nLowest Housing Costs (2023):")
print(data_2023[['state', 'housing_rpp']].head(5).to_string(index=False))

print("\nHighest Housing Costs (2023):")
print(data_2023[['state', 'housing_rpp']].tail(5).to_string(index=False))

print("\n" + "="*70)
print("EXTRACTION COMPLETE!")
print("="*70)