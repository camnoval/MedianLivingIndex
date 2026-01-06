"""
MASTER SCRIPT: Run Complete MLI Market Adjustment Pipeline
===========================================================

Runs all 5 steps in sequence to integrate market rent data into your MLI.

What this does:
1. Fetches Zillow ZORI market rents & Census homeownership rates
2. Creates market rent estimates (if Zillow fails)
3. Calculates weighted housing costs (renters + owners)
4. Recalculates MLI with new housing costs
5. Generates comprehensive comparison and analysis

Usage:
    python run_all_market_adjustment.py

Time: ~5-10 minutes depending on Census API
"""

import subprocess
import sys
import os
from datetime import datetime

print("="*80)
print("MLI MARKET ADJUSTMENT - MASTER PIPELINE")
print("="*80)
print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# File paths relative to project root (two levels up from scripts/readjust_for_housing_rent_rates/)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# List of required input files with full paths
required_files = {
    'mli_results': os.path.join(project_root, 'data', 'final', 'mli_results_14cat_q3.csv'),
    'costs_breakdown': os.path.join(project_root, 'data', 'final', 'costs_breakdown_14cat_q3.csv'),
    'bea_rpps': os.path.join(project_root, 'data', 'processed', 'bea_component_rpps.csv'),
    'bls_baseline': os.path.join(project_root, 'data', 'raw', 'BLS_baseline_spending.csv')
}

# Check for required files
print("[Pre-flight] Checking for required input files...")
print(f"Project root: {project_root}")
print("-"*80)

missing_files = []
for name, filepath in required_files.items():
    if os.path.exists(filepath):
        print(f"✓ {os.path.basename(filepath)}")
    else:
        print(f"✗ {os.path.basename(filepath)} - MISSING")
        print(f"   Expected at: {filepath}")
        missing_files.append(filepath)

if missing_files:
    print(f"\n✗ Missing {len(missing_files)} required files!")
    print("\nPlease make sure these files are in the current directory:")
    for f in missing_files:
        print(f"  - {f}")
    print("\nAborting.")
    sys.exit(1)

print("\n✓ All required files present")

# Check for income data in data/raw
income_data_dir = os.path.join(project_root, 'data', 'raw')
if os.path.exists(income_data_dir):
    income_files = [f for f in os.listdir(income_data_dir) 
                   if f.startswith('census_income_data_') and f.endswith('.csv')]
else:
    income_files = []

if not income_files:
    print(f"\n✗ No census_income_data file found in {income_data_dir}!")
    print("  Looking for: census_income_data_YYYYMMDD.csv")
    sys.exit(1)

print(f"✓ Found income data: {sorted(income_files)[-1]}")

# Census API key check
if os.environ.get('CENSUS_API_KEY'):
    print("✓ Census API key found (will fetch state-specific homeownership rates)")
else:
    print("⚠ No Census API key (will use 65% national average)")
    print("  Optional: Get key at https://api.census.gov/data/key_signup.html")

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define pipeline steps (full paths)
steps = [
    {
        'name': 'Step 1: Fetch Zillow & Census Data',
        'script': os.path.join(script_dir, 'step1_fetch_zillow_census.py'),
        'required': True
    },
    {
        'name': 'Step 2: Create Market Rents',
        'script': os.path.join(script_dir, 'step2_create_market_rents.py'),
        'required': True
    },
    {
        'name': 'Step 3: Calculate Weighted Housing',
        'script': os.path.join(script_dir, 'step3_calculate_weighted_housing.py'),
        'required': True
    },
    {
        'name': 'Step 4: Recalculate MLI',
        'script': os.path.join(script_dir, 'step4_recalculate_mli.py'),
        'required': True
    },
    {
        'name': 'Step 5: Compare & Analyze',
        'script': os.path.join(script_dir, 'step5_compare_and_analyze.py'),
        'required': True
    }
]

# Run pipeline
print("\n" + "="*80)
print("RUNNING PIPELINE")
print("="*80)

start_time = datetime.now()
failed_steps = []

for i, step in enumerate(steps, 1):
    print(f"\n\n[{i}/5] {step['name']}")
    print("="*80)
    
    # Verify script exists
    if not os.path.exists(step['script']):
        print(f"\n✗ Script not found: {step['script']}")
        print(f"  Make sure all step scripts are in: {script_dir}")
        sys.exit(1)
    
    try:
        result = subprocess.run(
            [sys.executable, step['script']],
            check=True,
            capture_output=False,
            text=True,
            cwd=script_dir  # Run from script directory
        )
        
        print(f"\n✓ {step['name']} completed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {step['name']} FAILED")
        print(f"  Error code: {e.returncode}")
        
        if step['required']:
            print("\n✗ Required step failed. Aborting pipeline.")
            sys.exit(1)
        else:
            print("⚠ Optional step failed. Continuing...")
            failed_steps.append(step['name'])
    
    except FileNotFoundError as e:
        print(f"\n✗ Error running script: {e}")
        print(f"  Script path: {step['script']}")
        sys.exit(1)

# Summary
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print("\n\n" + "="*80)
print("PIPELINE COMPLETE")
print("="*80)

print(f"\nCompleted: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Duration: {duration:.0f} seconds ({duration/60:.1f} minutes)")

if failed_steps:
    print(f"\n⚠ {len(failed_steps)} optional steps failed:")
    for step in failed_steps:
        print(f"  - {step}")
else:
    print("\n✓ All steps completed successfully!")

print("\nGenerated files:")
print("  • market_rents_final.csv")
print("  • housing_costs_weighted.csv")
print("  • mli_results_14cat_q3_MARKET.csv")
print("  • costs_breakdown_14cat_q3_MARKET.csv")
print("  • market_divergence_MARKET.json")
print("  • state_rankings_comparison.csv")
print("  • detailed_comparison_report.txt")

print("\nNext steps:")
print("  1. Read: detailed_comparison_report.txt")
print("  2. Review: state_rankings_comparison.csv")
print("  3. Update your website with _MARKET.csv files")
print("  4. Replace market_divergence.json with market_divergence_MARKET.json")

print("\n" + "="*80)
print("CONGRATULATIONS! Your MLI now uses market-adjusted housing costs.")
print("="*80)