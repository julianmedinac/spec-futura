import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def audit_w2_calculation(asset_key):
    print(f"\n{'!'*80}")
    print(f"AUDIT AND VERIFICATION OF W1-W2 SIGNAL CALCULATION FOR {asset_key}")
    print(f"{'!'*80}")
    
    loader = DataLoader()
    
    # 1. Download RAW Daily Data
    # ------------------------------------------------------------------
    print(f"1. Downloading raw daily data...")
    data = loader.download(asset_key, start_date='2020-01-01') # Recent sample for manual check
    
    if data.empty:
        print("No data found.")
        return

    # Add Calendar Helpers
    data['year'] = data.index.year
    data['month'] = data.index.month
    data['day'] = data.index.day
    data['week_of_year'] = data.index.isocalendar().week
    
    # 2. Select a Specific Test Case (e.g., February 2024)
    # ------------------------------------------------------------------
    # Let's pick a known month to manually verify calculations
    test_year = 2024
    test_month = 2
    
    print(f"\n2. Selecting Test Case: {test_month}/{test_year}")
    
    month_data = data[(data['year'] == test_year) & (data['month'] == test_month)]
    
    if month_data.empty:
        print("Test case data missing.")
        return
        
    print(f"   Data Points in Month: {len(month_data)}")
    print(month_data[['open', 'high', 'low', 'close', 'week_of_year']].to_string())
    
    # 3. Identify Weeks Exactly as Logic Does
    # ------------------------------------------------------------------
    weeks = sorted(month_data['week_of_year'].unique())
    print(f"\n3. Identifying Weeks present in data:")
    print(f"   Unique Week Numbers: {weeks}")
    
    if len(weeks) < 2:
        print("CRITICAL ERROR: Less than 2 weeks found in test month. Logic fails.")
        return
        
    w1_num = weeks[0]
    w2_num = weeks[1]
    print(f"   Week 1 is Week #{w1_num}")
    print(f"   Week 2 is Week #{w2_num}")
    
    # 4. Extract Data for W1 and W2
    # ------------------------------------------------------------------
    w1_data = month_data[month_data['week_of_year'] == w1_num]
    w2_data = month_data[month_data['week_of_year'] == w2_num]
    
    print(f"\n4. Verifying W1 Data (Week #{w1_num}):")
    print(w1_data[['high', 'low', 'close']])
    print(f"   W1 High: {w1_data['high'].max()}")
    print(f"   W1 Low : {w1_data['low'].min()}")
    
    print(f"\n5. Verifying W2 Data (Week #{w2_num}):")
    print(w2_data[['high', 'low', 'close']])
    print(f"   W2 High: {w2_data['high'].max()}")
    print(f"   W2 Low : {w2_data['low'].min()}")
    print(f"   W2 Close (Signal Price): {w2_data.iloc[-1]['close']}")
    
    # 5. Manual Calculation of Metrics
    # ------------------------------------------------------------------
    combined_high = max(w1_data['high'].max(), w2_data['high'].max())
    combined_low = min(w1_data['low'].min(), w2_data['low'].min())
    combined_range = combined_high - combined_low
    midpoint = combined_low + (combined_range * 0.5)
    
    print(f"\n6. Manual Calculation Audit:")
    print(f"   Combined High (Max(W1_H, W2_H)): {combined_high}")
    print(f"   Combined Low  (Min(W1_L, W2_L)): {combined_low}")
    print(f"   Range (High - Low)             : {combined_range}")
    print(f"   50% Level (Low + Range/2)      : {midpoint}")
    
    w2_close = w2_data.iloc[-1]['close']
    is_below = w2_close < midpoint
    
    print(f"\n7. Signal Determination:")
    print(f"   W2 Close ({w2_close}) < Midpoint ({midpoint}) ? {is_below}")
    
    # 8. Check Monthly Outcome
    # ------------------------------------------------------------------
    month_open = month_data.iloc[0]['open']
    month_close = month_data.iloc[-1]['close']
    is_red = month_close < month_open
    
    print(f"\n8. Monthly Outcome Verification:")
    print(f"   Month Open : {month_open}")
    print(f"   Month Close: {month_close}")
    print(f"   Is Red?    : {is_red}")
    
    print(f"\nAUDIT CONCLUSION:")
    if is_below and is_red:
        print("   Signal worked (Below 50% -> Red Month)")
    elif is_below and not is_red:
        print("   Signal failed (Below 50% -> Green Month)")
    elif not is_below and not is_red:
        print("   Signal worked (Above 50% -> Green Month)")
    else:
        print("   Signal failed (Above 50% -> Red Month)")
        
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Audit NQ for a specific known month
    audit_w2_calculation('NQ')
