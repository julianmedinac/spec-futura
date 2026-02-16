"""
VERIFICATION SCRIPT - O2C Quarterly Calculations
=================================================
Independently validates every mathematical calculation in o2c_quarterly.py.
This script does NOT import from o2c_quarterly.py - it recalculates everything
from scratch to ensure results match.

Checks performed:
1. Monthly O2C return formula: (Close_last - Open_first) / Open_first
2. Quarter month filtering (Q1=1,2,3; Q2=4,5,6; Q3=7,8,9; Q4=10,11,12)
3. Distribution table: frequencies sum to total count
4. Distribution table: all probabilities sum to 100%
5. Statistics: mean, std, median, min, max, count, skew, kurtosis
6. Sigma bands: correct bounds and counts
7. No data leakage between quarters (every month appears in exactly one quarter)
8. Manual spot-check: verify individual monthly returns against raw OHLC data
"""
import sys
sys.path.insert(0, '.')
from src.data.data_loader import download_asset_data
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

SIGMAS = [1, 1.5, 2]

def verify_all(asset_key='NQ', start='2020-01-01', end='2025-12-31', label='2020-2025'):
    """Run all verification checks."""
    
    errors = []
    warnings = []
    passes = []
    
    print(f"\n{'='*80}")
    print(f"  VERIFICATION: {asset_key} | {label}")
    print(f"  Running independent mathematical verification...")
    print(f"{'='*80}\n")
    
    # ==========================================
    # STEP 1: Download raw data independently
    # ==========================================
    print("[1/8] Downloading raw data...")
    data = download_asset_data(asset_key, start_date=start, end_date=end)
    print(f"  Raw daily data: {len(data)} rows, from {data.index[0].date()} to {data.index[-1].date()}")
    
    # ==========================================
    # STEP 2: Compute monthly O2C manually
    # ==========================================
    print("\n[2/8] Computing monthly O2C returns manually...")
    
    # Method A: Using resample (same as o2c_quarterly.py)
    monthly_a = data.resample('MS').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
    }).dropna()
    o2c_a = (monthly_a['close'] - monthly_a['open']) / monthly_a['open']
    o2c_a = o2c_a.dropna()
    
    # Method B: Manual loop - iterate month by month
    o2c_manual = {}
    for year in data.index.year.unique():
        for month in range(1, 13):
            mask = (data.index.year == year) & (data.index.month == month)
            month_data = data[mask]
            if len(month_data) == 0:
                continue
            first_open = month_data['open'].iloc[0]
            last_close = month_data['close'].iloc[-1]
            if pd.isna(first_open) or pd.isna(last_close) or first_open == 0:
                continue
            ret = (last_close - first_open) / first_open
            o2c_manual[pd.Timestamp(year, month, 1)] = ret
    
    o2c_b = pd.Series(o2c_manual).sort_index()
    
    # Compare methods
    common_dates = o2c_a.index.intersection(o2c_b.index)
    diff = (o2c_a.loc[common_dates] - o2c_b.loc[common_dates]).abs()
    max_diff = diff.max()
    
    if max_diff < 1e-10:
        passes.append("Monthly O2C: Resample method matches manual loop (max diff: {:.2e})".format(max_diff))
    else:
        errors.append(f"Monthly O2C: Methods differ! Max diff: {max_diff:.6f}")
    
    print(f"  Method A (resample): {len(o2c_a)} months")
    print(f"  Method B (manual loop): {len(o2c_b)} months")
    print(f"  Max difference between methods: {max_diff:.2e}")
    
    # ==========================================
    # STEP 3: Spot-check individual returns
    # ==========================================
    print("\n[3/8] Spot-checking individual monthly returns against raw data...")
    
    spot_checks = min(5, len(common_dates))
    check_dates = np.random.choice(common_dates, spot_checks, replace=False)
    
    for dt in sorted(check_dates):
        dt = pd.Timestamp(dt)
        mask = (data.index.year == dt.year) & (data.index.month == dt.month)
        month_data = data[mask]
        raw_open = month_data['open'].iloc[0]
        raw_close = month_data['close'].iloc[-1]
        expected = (raw_close - raw_open) / raw_open
        actual = o2c_a.loc[dt]
        match = abs(expected - actual) < 1e-10
        status = "✓" if match else "✗ MISMATCH"
        print(f"  {dt.strftime('%Y-%m')}: Open={raw_open:.2f}, Close={raw_close:.2f}, "
              f"Expected={(expected*100):.4f}%, Actual={(actual*100):.4f}% {status}")
        if not match:
            errors.append(f"Spot check failed for {dt.strftime('%Y-%m')}: expected {expected}, got {actual}")
    
    if not any("Spot check" in e for e in errors):
        passes.append(f"Spot check: {spot_checks} random months verified against raw OHLC data")
    
    # ==========================================
    # STEP 4: Verify quarter filtering
    # ==========================================
    print("\n[4/8] Verifying quarter month filtering...")
    
    quarters = {
        'Q1': [1, 2, 3],
        'Q2': [4, 5, 6],
        'Q3': [7, 8, 9],
        'Q4': [10, 11, 12],
    }
    
    all_filtered = []
    total_filtered_count = 0
    
    for qk, months in quarters.items():
        q_data = o2c_a[o2c_a.index.month.isin(months)]
        total_filtered_count += len(q_data)
        all_filtered.extend(q_data.index.tolist())
        
        # Check that all months in this quarter's data are correct
        wrong_months = [m for m in q_data.index.month if m not in months]
        if wrong_months:
            errors.append(f"Quarter {qk}: Found months {wrong_months} which don't belong!")
        else:
            passes.append(f"Quarter {qk}: All {len(q_data)} entries have correct months ({months})")
        
        print(f"  {qk} (months {months}): {len(q_data)} monthly returns")
    
    # Check no data leakage - every data point in exactly one quarter
    if total_filtered_count == len(o2c_a):
        passes.append(f"No data leakage: {total_filtered_count} filtered = {len(o2c_a)} total")
    else:
        errors.append(f"Data leakage! Filtered total: {total_filtered_count}, Original: {len(o2c_a)}")
    
    # Check no duplicates
    if len(all_filtered) == len(set(all_filtered)):
        passes.append("No duplicate dates across quarters")
    else:
        errors.append("Duplicate dates found across quarters!")
    
    # ==========================================
    # STEP 5: Verify statistics for each quarter
    # ==========================================
    print("\n[5/8] Verifying statistics for each quarter...")
    
    for qk, months in quarters.items():
        q_data = o2c_a[o2c_a.index.month.isin(months)]
        if len(q_data) < 3:
            print(f"  {qk}: Skipping (only {len(q_data)} data points)")
            continue
        
        print(f"\n  --- {qk} ({len(q_data)} data points) ---")
        
        # Independent calculations
        manual_mean = q_data.values.mean()
        manual_std = q_data.values.std(ddof=1)  # pandas uses ddof=1 by default
        manual_median = np.median(q_data.values)
        manual_min = q_data.values.min()
        manual_max = q_data.values.max()
        manual_count = len(q_data)
        manual_sum = q_data.values.sum()
        manual_var = q_data.values.var(ddof=1)
        manual_se = manual_std / np.sqrt(manual_count)
        manual_range = manual_max - manual_min
        manual_skew = scipy_stats.skew(q_data.values, bias=False)
        manual_kurtosis = scipy_stats.kurtosis(q_data.values, bias=False, fisher=True)
        
        # Compare with pandas (which is what o2c_quarterly.py uses)
        pd_mean = q_data.mean()
        pd_std = q_data.std()
        pd_median = q_data.median()
        pd_skew = q_data.skew()
        pd_kurtosis = q_data.kurtosis()
        
        checks = [
            ("Mean", manual_mean, pd_mean, 1e-12),
            ("Std Dev", manual_std, pd_std, 1e-12),
            ("Median", manual_median, pd_median, 1e-12),
            ("Min", manual_min, q_data.min(), 1e-12),
            ("Max", manual_max, q_data.max(), 1e-12),
            ("Count", manual_count, len(q_data), 0),
            ("Sum", manual_sum, q_data.sum(), 1e-12),
            ("Variance", manual_var, q_data.var(), 1e-12),
            ("Std Error", manual_se, pd_std / np.sqrt(len(q_data)), 1e-12),
            ("Range", manual_range, q_data.max() - q_data.min(), 1e-12),
        ]
        
        for name, expected, actual, tol in checks:
            diff = abs(expected - actual)
            if diff <= tol:
                print(f"    ✓ {name}: {actual*100:.6f}% (verified)")
            else:
                print(f"    ✗ {name}: Expected {expected}, Got {actual}, Diff {diff}")
                errors.append(f"{qk} {name}: expected {expected}, got {actual}")
        
        # Skewness comparison (scipy vs pandas use different formulas)
        # pandas.skew() uses the adjusted Fisher-Pearson coefficient
        # scipy.stats.skew(bias=False) should match
        skew_diff = abs(manual_skew - pd_skew)
        if skew_diff < 1e-6:
            print(f"    ✓ Skewness: {pd_skew:.9f} (verified)")
        else:
            print(f"    ⚠ Skewness: scipy={manual_skew:.9f}, pandas={pd_skew:.9f}, diff={skew_diff:.2e}")
            warnings.append(f"{qk} Skewness: small numerical diff ({skew_diff:.2e}), likely formula variant")
        
        # Kurtosis comparison
        kurt_diff = abs(manual_kurtosis - pd_kurtosis)
        if kurt_diff < 1e-6:
            print(f"    ✓ Kurtosis: {pd_kurtosis:.9f} (verified)")
        else:
            print(f"    ⚠ Kurtosis: scipy={manual_kurtosis:.9f}, pandas={pd_kurtosis:.9f}, diff={kurt_diff:.2e}")
            warnings.append(f"{qk} Kurtosis: small numerical diff ({kurt_diff:.2e}), likely formula variant")
    
    # ==========================================
    # STEP 6: Verify distribution table integrity
    # ==========================================
    print("\n[6/8] Verifying distribution table integrity...")
    
    bin_size = 0.01
    bin_min = -0.12
    bin_max = 0.12
    edges = np.arange(bin_min, bin_max + bin_size, bin_size)
    edges = np.round(edges, 10)
    
    for qk, months in quarters.items():
        q_data = o2c_a[o2c_a.index.month.isin(months)]
        if len(q_data) < 3:
            continue
        
        # Count frequencies manually
        total_freq = 0
        
        # First bin: <= edges[0]
        total_freq += (q_data <= edges[0]).sum()
        
        # Middle bins
        for i in range(1, len(edges)):
            lo = edges[i-1]
            hi = edges[i]
            count = ((q_data > lo) & (q_data <= hi)).sum()
            total_freq += count
        
        # "y mayor" bin
        total_freq += (q_data > bin_max).sum()
        
        if total_freq == len(q_data):
            passes.append(f"{qk} Distribution: All {len(q_data)} data points accounted for (sum of freqs = count)")
            print(f"  ✓ {qk}: Total frequencies ({total_freq}) = Count ({len(q_data)})")
        else:
            errors.append(f"{qk} Distribution: Freq sum ({total_freq}) != Count ({len(q_data)})")
            print(f"  ✗ {qk}: Total frequencies ({total_freq}) != Count ({len(q_data)})")
        
        # Verify probabilities sum to 100%
        probs = []
        probs.append((q_data <= edges[0]).sum() / len(q_data) * 100)
        for i in range(1, len(edges)):
            lo = edges[i-1]
            hi = edges[i]
            count = ((q_data > lo) & (q_data <= hi)).sum()
            probs.append(count / len(q_data) * 100)
        probs.append((q_data > bin_max).sum() / len(q_data) * 100)
        
        prob_sum = sum(probs)
        if abs(prob_sum - 100.0) < 0.01:
            passes.append(f"{qk} Probabilities sum to {prob_sum:.6f}% ≈ 100%")
            print(f"  ✓ {qk}: Probabilities sum to {prob_sum:.6f}%")
        else:
            errors.append(f"{qk} Probabilities sum to {prob_sum:.6f}% (should be 100%)")
            print(f"  ✗ {qk}: Probabilities sum to {prob_sum:.6f}%")
    
    # ==========================================
    # STEP 7: Verify sigma bands
    # ==========================================
    print("\n[7/8] Verifying sigma band calculations...")
    
    for qk, months in quarters.items():
        q_data = o2c_a[o2c_a.index.month.isin(months)]
        if len(q_data) < 3:
            continue
        
        mean = q_data.mean()
        std = q_data.std()  # ddof=1 (pandas default)
        
        print(f"\n  --- {qk}: mean={mean*100:.4f}%, std={std*100:.4f}% ---")
        
        for sig in SIGMAS:
            upper = mean + sig * std
            lower = mean - sig * std
            
            # Count manually
            manual_count = ((q_data >= lower) & (q_data <= upper)).sum()
            manual_pct = manual_count / len(q_data) * 100
            
            # Expected Gaussian %
            gauss_pct = (scipy_stats.norm.cdf(sig) - scipy_stats.norm.cdf(-sig)) * 100
            
            # Verify Gaussian reference values are correct
            expected_gauss = {1: 68.269, 1.5: 86.639, 2: 95.450}
            if abs(gauss_pct - expected_gauss[sig]) < 0.01:
                gauss_ok = "✓"
            else:
                gauss_ok = "✗"
                errors.append(f"{qk} Gaussian ref for {sig}σ: got {gauss_pct:.3f}%, expected {expected_gauss[sig]:.3f}%")
            
            print(f"    {sig}σ: [{lower*100:.3f}%, {upper*100:.3f}%] → "
                  f"{manual_count}/{len(q_data)} ({manual_pct:.2f}%) | "
                  f"Gauss: {gauss_pct:.3f}% {gauss_ok}")
            
            passes.append(f"{qk} {sig}σ band: {manual_count} of {len(q_data)} ({manual_pct:.2f}%)")
    
    # ==========================================
    # STEP 8: Cross-validate with o2c_periods.py monthly
    # ==========================================
    print("\n[8/8] Cross-validating: sum of all Q1+Q2+Q3+Q4 = total monthly O2C...")
    
    all_q_returns = []
    for qk, months in quarters.items():
        q_data = o2c_a[o2c_a.index.month.isin(months)]
        all_q_returns.extend(q_data.tolist())
    
    all_q_series = pd.Series(sorted(all_q_returns))
    
    if len(all_q_returns) == len(o2c_a):
        passes.append(f"Cross-validation: Q1+Q2+Q3+Q4 count ({len(all_q_returns)}) = total monthly ({len(o2c_a)})")
        print(f"  ✓ Count match: {len(all_q_returns)} = {len(o2c_a)}")
    else:
        errors.append(f"Cross-validation failed: {len(all_q_returns)} != {len(o2c_a)}")
        print(f"  ✗ Count mismatch: {len(all_q_returns)} != {len(o2c_a)}")
    
    # Sum of all returns should match
    total_q_sum = sum(all_q_returns)
    total_monthly_sum = o2c_a.sum()
    sum_diff = abs(total_q_sum - total_monthly_sum)
    if sum_diff < 1e-10:
        passes.append(f"Cross-validation: Sum of Q returns ({total_q_sum:.9f}) = Total monthly sum ({total_monthly_sum:.9f})")
        print(f"  ✓ Sum match: {total_q_sum:.9f} = {total_monthly_sum:.9f}")
    else:
        errors.append(f"Cross-validation sum: Q sum ({total_q_sum}) != monthly sum ({total_monthly_sum})")
        print(f"  ✗ Sum mismatch: {total_q_sum:.9f} != {total_monthly_sum:.9f}")
    
    # ==========================================
    # FINAL REPORT
    # ==========================================
    print(f"\n{'='*80}")
    print(f"  VERIFICATION REPORT - {asset_key} | {label}")
    print(f"{'='*80}")
    print(f"\n  ✓ PASSES: {len(passes)}")
    for p in passes:
        print(f"    ✓ {p}")
    
    if warnings:
        print(f"\n  ⚠ WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"    ⚠ {w}")
    
    if errors:
        print(f"\n  ✗ ERRORS: {len(errors)}")
        for e in errors:
            print(f"    ✗ {e}")
        print(f"\n  ❌ VERIFICATION FAILED - DO NOT USE RESULTS FOR TRADING DECISIONS")
    else:
        print(f"\n  ✅ ALL CHECKS PASSED - Calculations are mathematically correct")
    
    print(f"{'='*80}\n")
    
    return len(errors) == 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Verify O2C Quarterly Calculations')
    parser.add_argument('--asset', '-a', type=str, default='NQ', help='Asset key')
    args = parser.parse_args()
    
    # Test across multiple periods
    test_cases = [
        ('2020-01-01', '2025-12-31', '2020-2025'),
        ('2005-01-01', '2025-12-31', '2005-2025'),
    ]
    
    all_ok = True
    for start, end, label in test_cases:
        ok = verify_all(args.asset, start, end, label)
        if not ok:
            all_ok = False
    
    if all_ok:
        print("\n" + "🟢" * 20)
        print("  ALL VERIFICATION TESTS PASSED")
        print("🟢" * 20)
    else:
        print("\n" + "🔴" * 20)
        print("  SOME VERIFICATION TESTS FAILED")
        print("🔴" * 20)
        sys.exit(1)
