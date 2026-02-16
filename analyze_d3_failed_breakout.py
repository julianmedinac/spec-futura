import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_d3_failed_breakout(asset_key):
    print(f"\n{'='*100}")
    print(f"ANALYZING D3 FAILED BREAKOUT (LOOK ABOVE & FAIL) PATTERN FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    
    failed_attempts = 0
    total_samples = 0
    
    # Track outcomes
    week_closed_red = 0
    made_new_low = 0
    closed_below_d3 = 0
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue
            
        d1 = week_data.iloc[0]
        d2 = week_data.iloc[1]
        d3 = week_data.iloc[2]
        
        # 1. D1-D2 Rango Alcista
        # Definition: Close of D2 > Open of D1 (Green Period) OR Close D2 > 50% of D1-D2 Range?
        # User said: "D1 y D2 tienen un rango alcista". Let's use Close(D2) > Open(D1) as baseline.
        # More robust: Close(D2) > 50% of Range(D1-D2). Let's use the latter as it implies strength.
        d1_d2_high = max(d1['high'], d2['high'])
        d1_d2_low = min(d1['low'], d2['low'])
        rng_d1_d2 = d1_d2_high - d1_d2_low
        if rng_d1_d2 == 0: continue
        
        midpoint_d1_d2 = d1_d2_low + (rng_d1_d2 * 0.5)
        
        # Check if D1-D2 is structurally bullish (D2 Close > Midpoint)
        if d2['close'] <= midpoint_d1_d2: continue 
        
        # 2. D3 Marks Higher High (than D1-D2)
        d3_high = d3['high']
        broke_high = d3_high > d1_d2_high
        if not broke_high: continue
        
        # 3. D3 Closes BELOW 50% of Range(D1, D2, D3)
        # Calculate Range D1-D3
        d1_d3_high = max(d1_d2_high, d3['high'])
        d1_d3_low = min(d1_d2_low, d3['low'])
        rng_d1_d3 = d1_d3_high - d1_d3_low
        midpoint_d1_d3 = d1_d3_low + (rng_d1_d3 * 0.5)
        
        d3_close = d3['close']
        
        # THE TRAP: Is D3 Close < Midpoint(D1-D3)?
        is_failed_breakout = d3_close < midpoint_d1_d3
        
        if not is_failed_breakout: continue
        
        failed_attempts += 1
        
        # 4. Outcomes
        # A) Week Closes Red (Close < Open of Week)?
        week_open = d1['open']
        week_close = week_data.iloc[-1]['close']
        if week_close < week_open:
            week_closed_red += 1
            
        # B) Make New Low (Thu/Fri Low < Min(D1,D2,D3))?
        # Often the Trap is at the high, so does it collapse to new lows?
        # Let's check if D4/D5 low < D1_D3_Low
        rest_of_week = week_data.iloc[3:]
        rest_low = rest_of_week['low'].min()
        
        if rest_low < d1_d3_low:
            made_new_low += 1
            
        # C) Close below D3 Close (Immediate Follow Through)
        if week_close < d3['close']:
            closed_below_d3 += 1
            
    if failed_attempts == 0:
        print("No patterns found.")
        return

    prob_red = (week_closed_red / failed_attempts) * 100
    prob_new_low = (made_new_low / failed_attempts) * 100
    prob_below_d3 = (closed_below_d3 / failed_attempts) * 100
    
    print(f"Sample Size (Traps Identified): {failed_attempts}")
    print(f"PROBABILITIES AFTER FAILED BREAKOUT (D3 CLOSE < 50%):")
    print(f"1. Week Closes RED (Reversal): {prob_red:.1f}%")
    print(f"2. Week Makes NEW LOW (Thu/Fri): {prob_new_low:.1f}%")
    print(f"3. Week Closes BELOW Wednesday: {prob_below_d3:.1f}%")
    
    # Verdict
    if prob_red > 70:
        print("  -> STRONG BEARISH SIGNAL. The Trap is Real.")
    elif prob_red < 50:
        print("  -> WEAK SIGNAL. Market ignores the trap.")
    else:
        print("  -> MIXED RESULTS.")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        analyze_d3_failed_breakout(asset)
