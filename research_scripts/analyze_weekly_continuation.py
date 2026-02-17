import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_weekly_continuation(asset_key):
    print(f"\n{'='*100}")
    print(f"ANALYZING CONTINUATION AFTER D3 BREAKOUT FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    results = []
    
    total_bull_signals = 0
    total_d3_breakouts = 0
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue # Require full week (Mon-Fri) for this specific D3->D4/D5 analysis
            
        d1_data = week_data.iloc[0]
        d2_data = week_data.iloc[1]
        d3_data = week_data.iloc[2]
        
        # Ranges
        d1_d2_high = max(d1_data['high'], d2_data['high'])
        d1_d2_low = min(d1_data['low'], d2_data['low'])
        rng = d1_d2_high - d1_d2_low
        if rng == 0: continue
            
        midpoint = d1_d2_low + (rng * 0.5)
        d2_close = d2_data['close']
        
        # 1. Condition: D2 Bull Signal (>50%)
        if d2_close <= midpoint: continue
        total_bull_signals += 1
        
        # 2. Condition: D3 made a NEW HIGH or NEW LOW?
        # User asked: "D3 ya marcó un nuevo high"
        d3_high = d3_data['high']
        made_new_high_d3 = d3_high > d1_d2_high
        
        if not made_new_high_d3: continue
        total_d3_breakouts += 1
        
        # 3. Question: What happens on D4/D5?
        rest_of_week = week_data.iloc[3:] # D4 and D5
        
        # Outcome A: Higher High in D4/D5 compared to D3 High?
        rest_high = rest_of_week['high'].max()
        continued_higher = rest_high > d3_high
        
        # Outcome B: Weekly Close Green (vs Mon Open)
        week_open = week_data.iloc[0]['open']
        week_close = week_data.iloc[-1]['close']
        closed_green = week_close > week_open
        
        # Outcome C: Weekly Close vs D3 Close (Did we give back gains?)
        d3_close = d3_data['close']
        closed_higher_than_d3 = week_close > d3_close
        
        results.append({
            'continued_higher': continued_higher,
            'closed_green': closed_green,
            'closed_higher_than_d3': closed_higher_than_d3
        })
        
    df = pd.DataFrame(results)
    
    if df.empty:
        print("No samples found matching criteria.")
        return

    n = len(df)
    prob_continuation = (df['continued_higher'].sum() / n) * 100
    prob_green_week = (df['closed_green'].sum() / n) * 100
    prob_hold_gains = (df['closed_higher_than_d3'].sum() / n) * 100
    
    print(f"Sample Size (Weeks where D2>50% AND D3 Broke High): {n}")
    print(f"Total Bull Signals: {total_bull_signals}")
    print(f"Breakout Rate on D3: {(total_d3_breakouts/total_bull_signals)*100:.1f}%")
    
    print(f"\nPROBABILITIES AFTER D3 BREAKOUT:")
    print(f"1. Make HIGHER High on Thu/Fri?  : {prob_continuation:.1f}%")
    print(f"2. Close Week GREEN (vs Mon)?    : {prob_green_week:.1f}%")
    print(f"3. Close HIGHER than Wed Close?  : {prob_hold_gains:.1f}%")
    
    # Verdict
    print(f"\nVERDICT FOR {asset_key}:")
    if prob_continuation > 65:
        print("  -> TREND IS STRONG. HOLD FOR THU/FRI HIGH.")
    elif prob_continuation < 50:
        print("  -> EXHAUSTION LIKELY. TAKE PROFIT ON WEDNESDAY.")
    else:
        print("  -> MIXED. TIGHTEN STOPS.")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        analyze_weekly_continuation(asset)
