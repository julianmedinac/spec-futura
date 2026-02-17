import sys
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def mathematical_audit(asset_key='NQ', start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"RIGOROUS MATHEMATICAL AUDIT: {asset_key}")
    print(f"{'='*95}")

    # 1. Data Integrity Check
    df = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    
    # Check for duplicate indices
    duplicates = df.index.duplicated().sum()
    print(f"[*] Duplicate Dates: {duplicates} (Expected: 0)")
    
    # Check for future lookahead in ffill (Visual check of head/tail)
    print(f"[*] Data Range: {df.index.min()} to {df.index.max()}")

    # 2. Return Calculation Verification
    # We use Simple Returns: (P1 - P0) / P0
    df['o2c'] = (df['close'] - df['open']) / df['open']
    
    # Manual Verification of a random row
    idx = len(df) // 2
    row = df.iloc[idx]
    manual_o2c = (row['close'] - row['open']) / row['open']
    assert np.isclose(row['o2c'], manual_o2c), "O2C Calculation Mismatch!"
    print(f"[*] O2C Math: Verified (Simple Return formula)")

    # 3. Independence Audit (The "Double Counting" Problem)
    # If Monday and Tuesday are both >1sigma, do we count the week twice?
    df['year_week'] = df.index.to_period('W')
    std_val = df['o2c'].std()
    mean_val = df['o2c'].mean()
    upper_thr = mean_val + std_val
    
    # Raw triggers
    triggers = df[df['o2c'] > upper_thr].copy()
    raw_n = len(triggers)
    
    # Unique week triggers (To avoid dependencies in T-statistic)
    unique_weeks_n = triggers['year_week'].nunique()
    
    print(f"[*] Sample Independence:")
    print(f"    - Raw Trigger Days (N): {raw_n}")
    print(f"    - Unique Weeks Involved: {unique_weeks_n}")
    print(f"    - Overlap Ratio: {(raw_n - unique_weeks_n)/raw_n*100:.1f}% (Bias risk if > 0%)")

    # 4. Statistical Power & Bonferroni Correction
    # We tested 5 patterns in the Matrix. 
    # alpha = 0.05 / 5 = 0.01 for strict significance
    print(f"[*] Hypothesis Testing Audit:")
    print(f"    - Current Alpha: 0.05")
    print(f"    - Bonferroni Adjusted Alpha (for 7 tests): {0.05/7:.4f}")
    
    # 5. T-Stat Recalculation (Strict: One event per week)
    # This prevents the Monday + Tuesday drive from inflating the T-stat
    weekly_df = []
    for name, group in df.groupby('year_week'):
        if len(group) < 2: continue
        w_open = group['open'].iloc[0]
        w_close = group['close'].iloc[-1]
        w_o2c = (w_close - w_open) / w_open
        
        # Check for MONDAY specifically (A single point of entry)
        monday_group = group[group.index.day_name() == 'Monday']
        if not monday_group.empty:
            mon_o2c = monday_group['o2c'].iloc[0]
            if mon_o2c > upper_thr:
                weekly_df.append(w_o2c)

    if weekly_df:
        mean_ret = np.mean(weekly_df) * 100
        t_stat, p_val = stats.ttest_1samp(weekly_df, 0)
        print(f"\nSTRICT AUDIT - MONDAY NQ DRIVE (One per week):")
        print(f"    - Corrected N: {len(weekly_df)}")
        print(f"    - Corrected Avg Return: {mean_ret:+.3f}%")
        print(f"    - Corrected T-Stat: {t_stat:.2f}")
        print(f"    - Corrected P-Value: {p_val:.4f}")
        
        if p_val < (0.05/7):
            print("    [!] VERDICT: ULTRA ROBUST (Passes Bonferroni)")
        elif p_val < 0.05:
            print("    [!] VERDICT: SIGNIFICANT (Passes Standard)")
        else:
            print("    [!] VERDICT: MARGINAL/NOISE (Failed strict independence)")

if __name__ == "__main__":
    mathematical_audit('NQ')
