import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def audit_weekly_continuation_logic(asset_key, target_year=2024):
    print(f"\n{'='*100}")
    print(f"AUDITING WEEKLY CONTINUATION LOGIC FOR {asset_key} ({target_year})")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date=f'{target_year}-01-01', end_date=f'{target_year}-12-31')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    
    audit_count = 0
    
    print(f"{'Week':<5} | {'D2 > 50%':<10} | {'D3 Break':<10} | {'Post-D3 High':<15} | {'Result: Cont?':<12} | {'Close > D3?':<12}")
    print(f"{'-'*5}-|-{'-'*10}-|-{'-'*10}-|-{'-'*15}-|-{'-'*12}-|-{'-'*12}")
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue
            
        d1 = week_data.iloc[0]
        d2 = week_data.iloc[1]
        d3 = week_data.iloc[2]
        
        d1_d2_high = max(d1['high'], d2['high'])
        d1_d2_low = min(d1['low'], d2['low'])
        rng = d1_d2_high - d1_d2_low
        midpoint = d1_d2_low + (rng * 0.5)
        
        # Check Signal: D2 > 50%
        is_bull = d2['close'] > midpoint
        if not is_bull: continue
        
        # Check Breakout: D3 > High(D1,D2)
        d3_high = d3['high']
        breakout = d3_high > d1_d2_high
        if not breakout: continue
        
        # Check Outcome: Further Highs
        rest_of_week = week_data.iloc[3:] # D4, D5
        rest_high = rest_of_week['high'].max()
        continued = rest_high > d3_high
        
        # Check Hold: Close > D3 Close
        week_close = week_data.iloc[-1]['close']
        d3_close = d3['close']
        held_gains = week_close > d3_close
        
        print(f"W{week:<4} | {d2['close']:.2f} > {midpoint:.2f} | {d3_high:.2f} > {d1_d2_high:.2f} | Max(D4,D5): {rest_high:.2f} | {'YES' if continued else 'NO ':<12} | {'YES' if held_gains else 'NO ':<12}")
        
        if audit_count > 10: break # Only audit first 10 occurrences
        audit_count += 1

if __name__ == "__main__":
    audit_weekly_continuation_logic('NQ')
