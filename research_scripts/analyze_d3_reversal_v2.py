import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_d3_reversal_v2(asset_key):
    print(f"\n{'='*100}")
    print(f"ANALYZING D3 REVERSAL (CRITERION: D3 CLOSE < D2 OPEN) FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    
    patterns_found = 0
    closed_red = 0
    made_new_low = 0
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue
            
        d1 = week_data.iloc[0]
        d2 = week_data.iloc[1]
        d3 = week_data.iloc[2]
        
        # 1. D1 and D2 are Bullish (Two green days)
        # Using a slightly strict definition: Both days closed higher than they opened
        if not (d1['close'] > d1['open'] and d2['close'] > d2['open']): continue
        
        # 2. D3 attacks the high of D1 or D2
        d1_d2_high = max(d1['high'], d2['high'])
        if d3['high'] <= d1_d2_high: continue
        
        # 3. D3 closes BELOW the Open of D2
        if d3['close'] >= d2['open']: continue
        
        # Pattern Identified!
        patterns_found += 1
        
        # 4. Outcomes
        # New Low: Low of Thu/Fri < Low of (D1, D2, D3)
        d1_d3_low = min(d1['low'], d2['low'], d3['low'])
        rest_of_week = week_data.iloc[3:]
        th_fr_low = rest_of_week['low'].min()
        
        if th_fr_low < d1_d3_low:
            made_new_low += 1
            
        # Red Week: Friday Close < Monday Open
        week_open = d1['open']
        week_close = week_data.iloc[-1]['close']
        if week_close < week_open:
            closed_red += 1
            
    if patterns_found == 0:
        print("No patterns found with these criteria.")
        return

    prob_red = (closed_red / patterns_found) * 100
    prob_new_low = (made_new_low / patterns_found) * 100
    
    print(f"Sample Size (Traps Identified): {patterns_found}")
    print(f"PROBABILITIES AFTER D3 REVERSAL (CLOSE < D2 OPEN):")
    print(f"1. Week Closes RED (Reversal): {prob_red:.1f}%")
    print(f"2. Week Makes NEW LOW (Thu/Fri): {prob_new_low:.1f}%")
    
    # Verdict
    if prob_red > 70 or prob_new_low > 70:
        print("  -> STRONG BEARISH EDGE.")
    else:
        print("  -> MODERATE OR WEAK EDGE.")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        analyze_d3_reversal_v2(asset)
