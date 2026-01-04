"""
Calculate MLI for All Income Classes
=====================================

Runs the 14-category MLI calculation for three income quintiles:
- Q2: Lower-middle class (25th percentile, $28k-$54k income)
- Q3: Middle class (50th percentile, $54k-$90k income)
- Q4: Upper-middle class (75th percentile, $90k-$148k income)

Then compares results to show differential impact by income class.
"""

import pandas as pd
import subprocess
import sys

print("="*70)
print("CALCULATING MLI FOR ALL INCOME CLASSES")
print("="*70)

# Calculate for each quintile
quintiles = ['Q2', 'Q3', 'Q4']
results = {}

for quintile in quintiles:
    print(f"\n{'='*70}")
    print(f"PROCESSING {quintile}")
    print(f"{'='*70}\n")
    
    # Modify the calculate script to use this quintile
    with open('calculate_mli_14cat.py', 'r') as f:
        script = f.read()
    
    # Replace QUINTILE = 'Q3' with current quintile
    modified_script = script.replace(
        "QUINTILE = 'Q3'",
        f"QUINTILE = '{quintile}'"
    )
    
    # Write temporary script
    temp_file = f'calculate_mli_14cat_{quintile.lower()}.py'
    with open(temp_file, 'w') as f:
        f.write(modified_script)
    
    # Run it
    subprocess.run([sys.executable, temp_file])
    
    # Load results
    results_file = f'mli_results_14cat_{quintile.lower()}.csv'
    results[quintile] = pd.read_csv(results_file)

# Compare results
print("\n" + "="*70)
print("COMPARISON ACROSS INCOME CLASSES (2023)")
print("="*70)

# Merge all quintiles for 2023
comparison_2023 = results['Q2'][results['Q2']['year'] == 2023][['state', 'mli']].rename(columns={'mli': 'mli_q2'})
comparison_2023 = comparison_2023.merge(
    results['Q3'][results['Q3']['year'] == 2023][['state', 'mli']].rename(columns={'mli': 'mli_q3'}),
    on='state'
)
comparison_2023 = comparison_2023.merge(
    results['Q4'][results['Q4']['year'] == 2023][['state', 'mli']].rename(columns={'mli': 'mli_q4'}),
    on='state'
)

# Calculate spread (Q4 - Q2)
comparison_2023['spread'] = comparison_2023['mli_q4'] - comparison_2023['mli_q2']

# Sort by spread
comparison_2023 = comparison_2023.sort_values('spread', ascending=False)

# States where upper class does much better than lower class
print("\nStates Where Upper Class Thrives (Biggest Q4-Q2 Spread):")
print(f"{'State':<20s} {'Q2 MLI':>8s} {'Q3 MLI':>8s} {'Q4 MLI':>8s} {'Spread':>7s}")
print("-"*60)
for _, row in comparison_2023.head(10).iterrows():
    print(f"{row['state']:<20s} {row['mli_q2']:>8.2f} {row['mli_q3']:>8.2f} {row['mli_q4']:>8.2f} {row['spread']:>7.2f}")

# States with smallest spread (more equal impact)
print("\nStates With Most Equal Impact Across Classes (Smallest Q4-Q2 Spread):")
print(f"{'State':<20s} {'Q2 MLI':>8s} {'Q3 MLI':>8s} {'Q4 MLI':>8s} {'Spread':>7s}")
print("-"*60)
for _, row in comparison_2023.tail(10).iterrows():
    print(f"{row['state']:<20s} {row['mli_q2']:>8.2f} {row['mli_q3']:>8.2f} {row['mli_q4']:>8.2f} {row['spread']:>7.2f}")

# Save comparison
comparison_2023.to_csv('mli_comparison_by_income_2023.csv', index=False)
print(f"\n✓ Saved comparison to: mli_comparison_by_income_2023.csv")

# Analyze trends over time
print("\n" + "="*70)
print("MLI CHANGES BY INCOME CLASS (2008 → 2023)")
print("="*70)

for quintile in quintiles:
    df = results[quintile]
    mli_2008 = df[df['year'] == 2008]['mli'].mean()
    mli_2023 = df[df['year'] == 2023]['mli'].mean()
    change = mli_2023 - mli_2008
    
    print(f"\n{quintile}: {mli_2008:.2f} → {mli_2023:.2f} ({change:+.2f})")

print("\n" + "="*70)
print("ALL CALCULATIONS COMPLETE!")
print("="*70)
print("\nGenerated files:")
for q in quintiles:
    print(f"  - mli_results_14cat_{q.lower()}.csv")
    print(f"  - costs_breakdown_14cat_{q.lower()}.csv")
print(f"  - mli_comparison_by_income_2023.csv")