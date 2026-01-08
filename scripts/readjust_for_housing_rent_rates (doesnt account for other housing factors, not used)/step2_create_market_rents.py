"""
STEP 2 ALTERNATIVE: Use Census Actual Median Rents
===================================================

Instead of estimating from blended costs, this fetches ACTUAL median
rents from Census Bureau Table B25064.

This is MORE defensible because:
1. Uses real data, not estimates
2. No circular reasoning
3. Official government statistics
4. Includes utilities (like your current method)
"""

import pandas as pd
import requests
import time
import os

print("="*80)
print("STEP 2: GETTING ACTUAL MARKET RENTS FROM CENSUS")
print("="*80)

# Get project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))

# Load .env for API key
env_file = os.path.join(project_root, '.env')
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

CENSUS_API_KEY = os.environ.get('CENSUS_API_KEY', '')

if not CENSUS_API_KEY:
    print("✗ Census API key required for this method")
    print("  Either set CENSUS_API_KEY in .env")
    print("  Or use the estimation method (current step2)")
    exit(1)

output_dir = os.path.join(project_root, 'data', 'processed')

# ============================================================================
# FETCH CENSUS MEDIAN RENTS
# ============================================================================

print("\n[Fetching] Census Bureau median rents (Table B25064)...")
print("-"*80)

years = [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017,
         2018, 2019, 2021, 2022, 2023]

def fetch_median_rent(year, api_key):
    """Fetch median gross rent from Census ACS"""
    
    base_url = f"https://api.census.gov/data/{year}/acs/acs1"
    params = {
        'get': 'NAME,B25064_001E',  # Median gross rent
        'for': 'state:*',
        'key': api_key
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        headers = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)
        
        # Keep only the columns we need, drop the 'state' FIPS code
        df = df.rename(columns={
            'NAME': 'state_name',
            'B25064_001E': 'median_monthly_rent'
        })
        
        # Only keep state_name and rent, drop the FIPS 'state' column
        df = df[['state_name', 'median_monthly_rent']].copy()
        df = df.rename(columns={'state_name': 'state'})
        
        df['median_monthly_rent'] = pd.to_numeric(df['median_monthly_rent'], errors='coerce')
        df['year'] = year
        df['annual_market_rent'] = df['median_monthly_rent'] * 12
        
        return df[['state', 'year', 'median_monthly_rent', 'annual_market_rent']]
        
    except Exception as e:
        print(f"  ✗ {year}: {e}")
        return None

all_rents = []

for year in years:
    print(f"  Fetching {year}...", end=" ")
    df = fetch_median_rent(year, CENSUS_API_KEY)
    if df is not None:
        all_rents.append(df)
        print(f"✓ {len(df)} states")
    time.sleep(0.5)

if not all_rents:
    print("\n✗ Failed to fetch rent data")
    exit(1)

market_rents = pd.concat(all_rents, ignore_index=True)
market_rents = market_rents.sort_values(['state', 'year'])

print(f"\n✓ Collected {len(market_rents)} state-year observations")

# ============================================================================
# VERIFY INFLATION
# ============================================================================

print("\n[Verification] Checking rent inflation...")
print("-"*80)

for baseline_year in [2012, 2018]:
    if baseline_year in market_rents['year'].values:
        baseline_avg = market_rents[market_rents['year'] == baseline_year]['annual_market_rent'].mean()
        current_avg = market_rents[market_rents['year'] == 2023]['annual_market_rent'].mean()
        inflation = ((current_avg / baseline_avg) - 1) * 100
        
        print(f"\n{baseline_year}-2023:")
        print(f"  Median rent: ${baseline_avg:,.0f} → ${current_avg:,.0f}")
        print(f"  Inflation: +{inflation:.1f}%")

# ============================================================================
# SAVE OUTPUT
# ============================================================================

print("\n[Output] Saving Census market rents...")
print("-"*80)

output_file = os.path.join(output_dir, 'market_rents_final.csv')
market_rents['source'] = 'census_acs_b25064'
market_rents.to_csv(output_file, index=False)

print(f"✓ Saved: {output_file}")
print(f"  {len(market_rents)} state-year observations")

# Show sample
print("\nSample Census median rents (2023):")
sample_states = ['California', 'Texas', 'New York', 'Florida', 'Alabama', 'Mississippi']
sample_2023 = market_rents[
    (market_rents['year'] == 2023) &
    (market_rents['state'].isin(sample_states))
].sort_values('median_monthly_rent', ascending=False)

for _, row in sample_2023.iterrows():
    print(f"  {row['state']:20s}: ${row['median_monthly_rent']:>6,.0f}/mo (${row['annual_market_rent']:>8,.0f}/yr)")

print("\n" + "="*80)
print("STEP 2 COMPLETE - USING CENSUS ACTUAL RENTS")
print("="*80)
print("\n✓ Real median rent data from Census Bureau")
print("✓ No estimation or back-calculation needed")
print("✓ Official government statistics")
print("\n→ Next: Run step3_calculate_weighted_housing.py")
print("="*80)