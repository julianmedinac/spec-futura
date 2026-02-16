import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_d3_bear_trap_v2(asset_key):
    print(f"\n{'='*100}")
    print(f"ANALYZING D3 BEAR TRAP (CRITERION: D3 CLOSE > D2 OPEN) FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    
    patterns_found = 0
    closed_green = 0
    made_new_high = 0
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue
            
        d1 = week_data.iloc[0]
        d2 = week_data.iloc[1]
        d3 = week_data.iloc[2]
        
        # 1. D1 and D2 are Bearish (Two red days)
        if not (d1['close'] < d1['open'] and d2['close'] < d2['open']): continue
        
        # 2. D3 attacks the low of D1 or D2
        d1_d2_low = min(d1['low'], d2['low'])
        if d3['low'] >= d1_d2_low: continue
        
        # 3. D3 closes ABOVE the Open of D2
        if d3['close'] <= d2['open']: continue
        
        # Pattern Identified!
        patterns_found += 1
        
        # 4. Outcomes
        # New High: High of Thu/Fri > High of (D1, D2, D3)
        d1_d3_high = max(d1['high'], d2['high'], d3['high'])
        rest_of_week = week_data.iloc[3:]
        th_fr_high = rest_of_week['high'].max()
        
        if th_fr_high > d1_d3_high:
            made_new_high += 1
            
        # Green Week: Friday Close > Monday Open
        week_open = d1['open']
        week_close = week_data.iloc[-1]['close']
        if week_close > week_open:
            closed_green += 1
            
    if patterns_found == 0:
        print("No patterns found with these criteria.")
        return

    prob_green = (closed_green / patterns_found) * 100
    prob_new_high = (made_new_high / patterns_found) * 100
    
    print(f"Sample Size (Traps Identified): {patterns_found}")
    print(f"PROBABILITIES AFTER D3 BEAR TRAP (CLOSE > D2 OPEN):")
    print(f"1. Week Closes GREEN (Reversal): {prob_green:.1f}%")
    print(f"2. Week Makes NEW HIGH (Thu/Fri): {prob_new_high:.1f}%")
    
    # Verdict
    if prob_green > 70 or prob_new_high > 70:
        print("  -> STRONG BULLISH EDGE.")
    else:
        print("  -> MODERATE OR WEAK EDGE.")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        analyze_d3_bear_trap_v2(asset)
