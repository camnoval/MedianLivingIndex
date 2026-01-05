"""
Census Bureau Income Data Collector
Fetches median and mean household income for all US states (2004-2023)

Requirements:
    pip install requests pandas

Get your free API key at: https://api.census.gov/data/key_signup.html
"""

import requests
import pandas as pd
import time
from datetime import datetime
import json
import os
# =============================================================================
# CONFIGURATION
# =============================================================================

CENSUS_API_KEY = os.environ.get('CENSUS_API_KEY', '')  # Load from environment variable

# Census variables we need:
# B19013_001E = Median household income in the past 12 months
# B19025_001E = Aggregate household income in the past 12 months / B19025_002E = Number of households
# For mean, we actually use B19025_001E (aggregate) / universe count, but simpler to use B19113_001E

VARIABLES = {
    'median_income': 'B19013_001E',  # Median household income
    'mean_income': 'B19025_001E',     # Aggregate income (we'll calculate mean)
}

# Year ranges - ACS 1-year estimates available from 2005 onward
# 2020 had no ACS 1-year due to COVID, use 2019 or skip
YEARS = list(range(2005, 2026))  # 2005-2023
YEARS.remove(2020)  # No 2020 ACS 1-year data

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def fetch_state_income_year(year, api_key):
    """
    Fetch median and mean income for all states for a given year
    
    Args:
        year: Year to fetch (2005-2023, excluding 2020)
        api_key: Your Census API key
    
    Returns:
        DataFrame with columns: state_fips, state_name, year, median_income, mean_income
    """
    
    # Census API endpoint for ACS 1-year estimates
    base_url = f"https://api.census.gov/data/{year}/acs/acs1"
    
    # Parameters for API call
    params = {
        'get': 'NAME,B19013_001E,B19025_001E',  # State name, median income, aggregate income
        'for': 'state:*',  # All states
        'key': api_key
    }
    
    try:
        print(f"Fetching {year} data...", end=" ")
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # First row is headers
        headers = data[0]
        rows = data[1:]
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Rename columns for clarity
        df = df.rename(columns={
            'NAME': 'state_name',
            'state': 'state_fips',
            'B19013_001E': 'median_income',
            'B19025_001E': 'aggregate_income'
        })
        
        # Add year column
        df['year'] = year
        
        # Convert numeric columns
        df['median_income'] = pd.to_numeric(df['median_income'], errors='coerce')
        df['aggregate_income'] = pd.to_numeric(df['aggregate_income'], errors='coerce')
        df['state_fips'] = df['state_fips'].astype(str).str.zfill(2)
        
        print(f"✓ Got {len(df)} states")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return None
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"✗ Parse error: {e}")
        return None


def get_mean_income_year(year, api_key):
    """
    Fetch mean household income separately (aggregate / household count)
    This uses B19025 table for more accurate mean calculation
    
    Args:
        year: Year to fetch
        api_key: Census API key
    
    Returns:
        DataFrame with state_fips, mean_income
    """
    
    base_url = f"https://api.census.gov/data/{year}/acs/acs1"
    
    params = {
        'get': 'B19025_001E,B11001_001E',  # Aggregate income, Total households
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
            'state': 'state_fips',
            'B19025_001E': 'aggregate_income',
            'B11001_001E': 'total_households'
        })
        
        # Calculate mean
        df['aggregate_income'] = pd.to_numeric(df['aggregate_income'], errors='coerce')
        df['total_households'] = pd.to_numeric(df['total_households'], errors='coerce')
        df['mean_income'] = (df['aggregate_income'] / df['total_households']).round(0)
        
        df['state_fips'] = df['state_fips'].astype(str).str.zfill(2)
        
        return df[['state_fips', 'mean_income']]
        
    except Exception as e:
        print(f"    Warning: Could not calculate mean for {year}, using aggregate as proxy")
        return None


def collect_all_years(years, api_key, delay=1.0):
    """
    Collect income data for all specified years
    
    Args:
        years: List of years to fetch
        api_key: Census API key
        delay: Seconds to wait between requests (be nice to Census servers)
    
    Returns:
        Combined DataFrame with all years
    """
    
    all_data = []
    
    for year in years:
        df = fetch_state_income_year(year, api_key)
        
        if df is not None:
            # Try to get better mean calculation
            mean_df = get_mean_income_year(year, api_key)
            if mean_df is not None:
                df = df.drop('aggregate_income', axis=1)
                df = df.merge(mean_df, on='state_fips', how='left')
            else:
                # Use aggregate as rough proxy (not ideal)
                df['mean_income'] = df['aggregate_income']
                df = df.drop('aggregate_income', axis=1)
            
            all_data.append(df)
            
        time.sleep(delay)  # Be respectful to Census API
    
    if not all_data:
        print("No data collected!")
        return None
    
    # Combine all years
    combined = pd.concat(all_data, ignore_index=True)
    
    # Reorder columns
    combined = combined[['state_fips', 'state_name', 'year', 'median_income', 'mean_income']]
    
    # Sort by state and year
    combined = combined.sort_values(['state_name', 'year']).reset_index(drop=True)
    
    return combined


def add_metadata(df):
    """Add metadata columns for database storage"""
    df['data_source'] = 'US Census Bureau - American Community Survey (ACS 1-Year)'
    df['collection_date'] = datetime.now().strftime('%Y-%m-%d')
    df['currency_code'] = 'USD'
    return df


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("Census Bureau Income Data Collection")
    print("=" * 70)
    print()
    
    # Validate API key
    # Validate API key
    if not CENSUS_API_KEY:
        print("ERROR: Census API key not found!")
        print("Get one free at: https://api.census.gov/data/key_signup.html")
        print("\nThen set it as an environment variable:")
        print("  export CENSUS_API_KEY='your_key_here'")
        print("\nOr create a .env file in this directory")
        return
    
    print(f"Collecting data for years: {min(YEARS)}-{max(YEARS)}")
    print(f"Total years to fetch: {len(YEARS)}")
    print()
    
    # Collect data
    df = collect_all_years(YEARS, CENSUS_API_KEY, delay=1.0)
    
    if df is None:
        print("Data collection failed!")
        return
    
    # Add metadata
    df = add_metadata(df)
    
    # Summary statistics
    print()
    print("=" * 70)
    print("COLLECTION SUMMARY")
    print("=" * 70)
    print(f"Total records collected: {len(df)}")
    print(f"States covered: {df['state_name'].nunique()}")
    print(f"Years covered: {sorted(df['year'].unique())}")
    print(f"Date range: {df['year'].min()}-{df['year'].max()}")
    print()
    
    # Check for missing data
    missing = df[df['median_income'].isna() | df['mean_income'].isna()]
    if len(missing) > 0:
        print(f"Warning: {len(missing)} records have missing income data")
        print(missing[['state_name', 'year']])
        print()
    
    # Show sample
    print("Sample data (first 10 rows):")
    print(df.head(10).to_string(index=False))
    print()
    
    # Save to CSV
    output_file = f'census_income_data_{datetime.now().strftime("%Y%m%d")}.csv'
    df.to_csv(output_file, index=False)
    print(f"✓ Data saved to: {output_file}")
    print()
    
    # Quick validation - show 2023 data for a few states
    if 2023 in df['year'].values:
        print("2023 Sample (Selected States):")
        states_to_show = ['California', 'Texas', 'New York', 'Florida', 'Pennsylvania']
        sample_2023 = df[(df['year'] == 2023) & (df['state_name'].isin(states_to_show))]
        print(sample_2023[['state_name', 'median_income', 'mean_income']].to_string(index=False))
    
    print()
    print("=" * 70)
    print("Next step: Run the database setup script to store this data")
    print("=" * 70)


if __name__ == "__main__":
    main()