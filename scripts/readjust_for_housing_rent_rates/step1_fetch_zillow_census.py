"""
STEP 1: Fetch Zillow ZORI Market Rent Data & Census Homeownership Rates
========================================================================

Run this first to download external data sources.

Requirements:
- Internet connection
- Optional: Census API key for state-specific homeownership rates

Outputs:
- zillow_zori_annual.csv
- census_homeownership_rates.csv (or _fallback.csv)
"""

import pandas as pd
import requests
from io import StringIO
import time
import os
import glob

print("="*80)
print("STEP 1: FETCHING ZILLOW ZORI & CENSUS HOMEOWNERSHIP DATA")
print("="*80)

# Get project root (two levels up from scripts/readjust_for_housing_rent_rates/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))

# Load .env file if it exists
env_file = os.path.join(project_root, '.env')
if os.path.exists(env_file):
    print(f"\nLoading environment from: {env_file}")
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    if os.environ.get('CENSUS_API_KEY'):
        print("✓ Loaded CENSUS_API_KEY from .env file")

# Output directory for generated files
output_dir = os.path.join(project_root, 'data', 'processed')
os.makedirs(output_dir, exist_ok=True)

# ============================================================================
# PART 1: ZILLOW ZORI DATA
# ============================================================================

print("\n[1/2] Downloading Zillow ZORI (Market Rent Index)...")
print("-"*80)

# Updated Zillow ZORI URL (they changed their data structure)
# Try multiple possible URLs
ZILLOW_URLS = [
    "https://files.zillowstatic.com/research/public_csvs/zori/State_zori_uc_sfrcondomfr_month.csv",
    "https://files.zillowstatic.com/research/public_csvs/zori/State_zori_uc_sfrcondomfr_sm_month.csv",
    "https://files.zillowstatic.com/research/public_csvs/zori/State_ZORI_AllHomesPlusMultifamily_Smoothed.csv"
]

zillow_success = False

for ZILLOW_URL in ZILLOW_URLS:
    try:
        print(f"Trying: {ZILLOW_URL.split('/')[-1]}")
        response = requests.get(ZILLOW_URL, timeout=30)
        response.raise_for_status()
        
        zillow_df = pd.read_csv(StringIO(response.text))
        
        # Check if it's the right format
        if 'RegionName' in zillow_df.columns or 'State' in zillow_df.columns:
            zillow_df = zillow_df[zillow_df.get('RegionType', zillow_df.get('Geography', 'state')) == 'state'].copy()
            
            # Get date columns
            date_cols = [col for col in zillow_df.columns 
                        if col not in ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName', 'State', 'Geography']]
            
            if len(date_cols) == 0:
                continue
            
            # Reshape to long format
            id_col = 'StateName' if 'StateName' in zillow_df.columns else 'State'
            zillow_long = zillow_df.melt(
                id_vars=[id_col],
                value_vars=date_cols,
                var_name='date',
                value_name='zori_rent'
            )
            
            # Convert date to datetime and extract year
            zillow_long['date'] = pd.to_datetime(zillow_long['date'])
            zillow_long['year'] = zillow_long['date'].dt.year
            
            # Calculate annual averages
            zillow_annual = zillow_long.groupby([id_col, 'year'])['zori_rent'].mean().reset_index()
            zillow_annual.columns = ['state', 'year', 'zori_monthly_rent']
            zillow_annual['zori_annual_rent'] = zillow_annual['zori_monthly_rent'] * 12
            zillow_annual = zillow_annual.dropna()
            
            if len(zillow_annual) > 0:
                output_file = os.path.join(output_dir, 'zillow_zori_annual.csv')
                zillow_annual.to_csv(output_file, index=False)
                
                print(f"✓ Downloaded Zillow ZORI data")
                print(f"  States: {zillow_annual['state'].nunique()}")
                print(f"  Years: {sorted(zillow_annual['year'].unique())}")
                print(f"✓ Saved: {output_file}")
                
                zillow_success = True
                break
                
    except Exception as e:
        continue

if not zillow_success:
    print(f"✗ Could not download Zillow data from any URL")
    print(f"  Will use fallback method in Step 2")

# ============================================================================
# PART 2: CENSUS HOMEOWNERSHIP RATES
# ============================================================================

print("\n[2/2] Fetching Census Homeownership Rates...")
print("-"*80)

CENSUS_API_KEY = os.environ.get('CENSUS_API_KEY', '')

def fetch_homeownership_census(year, api_key):
    """Fetch homeownership rate from Census ACS"""
    
    base_url = f"https://api.census.gov/data/{year}/acs/acs1"
    params = {
        'get': 'NAME,B25003_001E,B25003_002E,B25003_003E',
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
        
        df = df.rename(columns={
            'NAME': 'state',
            'B25003_001E': 'total_units',
            'B25003_002E': 'owner_occupied',
            'B25003_003E': 'renter_occupied'
        })
        
        df['total_units'] = pd.to_numeric(df['total_units'], errors='coerce')
        df['owner_occupied'] = pd.to_numeric(df['owner_occupied'], errors='coerce')
        df['renter_occupied'] = pd.to_numeric(df['renter_occupied'], errors='coerce')
        
        df['homeownership_rate'] = (df['owner_occupied'] / df['total_units'] * 100).round(1)
        df['rental_rate'] = (df['renter_occupied'] / df['total_units'] * 100).round(1)
        df['year'] = year
        
        return df[['state', 'year', 'homeownership_rate', 'rental_rate']]
        
    except Exception as e:
        return None

if CENSUS_API_KEY:
    print("Using Census API...")
    
    years = [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017,
             2018, 2019, 2021, 2022, 2023]
    
    homeownership_data = []
    
    for year in years:
        print(f"  Fetching {year}...", end=" ")
        df = fetch_homeownership_census(year, CENSUS_API_KEY)
        if df is not None:
            homeownership_data.append(df)
            print(f"✓")
        else:
            print(f"✗")
        time.sleep(0.5)
    
    if homeownership_data:
        homeownership_df = pd.concat(homeownership_data, ignore_index=True)
        output_file = os.path.join(output_dir, 'census_homeownership_rates.csv')
        homeownership_df.to_csv(output_file, index=False)
        
        print(f"\n✓ Collected {len(homeownership_df)} state-year observations")
        print(f"✓ Saved: {output_file}")
        census_success = True
    else:
        print("\n✗ No Census data collected, using fallback")
        census_success = False
else:
    print("No Census API key - using fallback")
    print("To get state-specific rates: https://api.census.gov/data/key_signup.html")
    census_success = False

# Create fallback if needed
if not census_success:
    print("\nCreating fallback homeownership rates...")
    
    states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
              'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
              'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
              'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
              'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
              'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
              'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
              'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
              'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
              'West Virginia', 'Wisconsin', 'Wyoming', 'District of Columbia']
    
    years = [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017,
             2018, 2019, 2021, 2022, 2023]
    
    fallback_data = []
    for state in states:
        for year in years:
            fallback_data.append({
                'state': state,
                'year': year,
                'homeownership_rate': 65.0,
                'rental_rate': 35.0
            })
    
    output_file = os.path.join(output_dir, 'census_homeownership_rates_fallback.csv')
    pd.DataFrame(fallback_data).to_csv(output_file, index=False)
    print(f"✓ Saved: {output_file}")
    print("  Using 65% homeownership / 35% rental for all states")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("STEP 1 COMPLETE")
print("="*80)

if zillow_success:
    print("\n✓ Zillow ZORI market rents downloaded")
else:
    print("\n⚠ Zillow download failed - will estimate from existing data in Step 2")
    print("  Note: Zillow frequently changes their data URLs")
    print("  Alternative: Manually download from https://www.zillow.com/research/data/")
    print("  Look for: 'ZORI (Smoothed): All Homes Plus Multifamily Time Series ($)'")

if census_success:
    print("✓ Census homeownership rates downloaded")
else:
    print("⚠ Using fallback homeownership rates (65% national average)")
    print("  To get state-specific rates, ensure CENSUS_API_KEY is set")

print("\n→ Next: Run step2_create_market_rents.py")
print("="*80)