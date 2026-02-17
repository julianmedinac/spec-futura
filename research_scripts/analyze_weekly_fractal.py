import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_weekly_d1d2_fractal(asset_key):
    print(f"\n{'='*100}")
    print(f"ANALYZING WEEKLY FRACTAL: D1-D2 RANGE vs WEEKLY OUTCOME FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    # Calendar Helpers
    data['year'] = data.index.year
    data['week_of_year'] = data.index.isocalendar().week
    data['day_of_week'] = data.index.dayofweek # 0=Mon, 4=Fri
    
    # Identify unique weeks (Year, WeekNum)
    # Note on year boundary: ISO week 52/53 can span years, but pandas groupby handles it if we group by date or smart grouping.
    # Simple approach: Group by Isocalendar Year and Week
    data['iso_year'] = data.index.isocalendar().year
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    
    results = []
    
    print(f"Processing weekly data...")
    
    for (year, week), week_data in weekly_groups:
        # We need at least 2 trading days to define D1-D2 range
        if len(week_data) < 2: continue
            
        # Get D1 and D2 (Trading Days 1 and 2 of the week)
        # Note: D1 might be Tuesday if Monday was holiday. We take first 2 rows.
        d1_data = week_data.iloc[0]
        d2_data = week_data.iloc[1]
        
        # Calculate D1-D2 Range
        d1_d2_high = max(d1_data['high'], d2_data['high'])
        d1_d2_low = min(d1_data['low'], d2_data['low'])
        rng = d1_d2_high - d1_d2_low
        
        if rng == 0: continue
            
        midpoint = d1_d2_low + (rng * 0.5)
        d2_close = d2_data['close']
        
        # Signals AT CLOSE OF D2
        is_bull_signal = d2_close > midpoint
        
        # Outcomes based on REST OF WEEK (D3-D5)
        # If week only had 2 days, no outcome possible
        if len(week_data) <= 2: continue
            
        rest_of_week = week_data.iloc[2:] # D3 onwards
        
        # Outcome 1: Weekly Close relative to Week Open (Mon Open)
        # Or relative to D2 Close?
        # User asked: "Green Week" vs "Red Week" usually implies Friday Close > Monday Open
        week_open = week_data.iloc[0]['open']
        week_close = week_data.iloc[-1]['close']
        is_green_week = week_close > week_open
        weekly_return = (week_close / week_open) - 1
        
        # Outcome 2: New Extremes in D3-D5
        # Did we break the D1-D2 High/Low?
        rest_high = rest_of_week['high'].max()
        rest_low = rest_of_week['low'].min()
        
        made_new_high = rest_high > d1_d2_high
        made_new_low = rest_low < d1_d2_low
        
        results.append({
            'year': year,
            'week': week,
            'is_bull_signal': is_bull_signal,
            'is_green_week': is_green_week,
            'weekly_return': weekly_return,
            'made_new_high': made_new_high,
            'made_new_low': made_new_low
        })
        
    df = pd.DataFrame(results)
    
    if df.empty:
        print("No valid weeks found.")
        return

    # --- AGGREGATE STATISTICS ---
    total_weeks = len(df)
    bull_signals = df[df['is_bull_signal']]
    bear_signals = df[~df['is_bull_signal']]
    
    print(f"\nTOTAL WEEKS ANALYZED: {total_weeks}")
    
    # 1. BULL SIGNAL STATS (D2 > 50%)
    n_bull = len(bull_signals)
    prob_green_bull = (bull_signals['is_green_week'].sum() / n_bull) * 100
    prob_new_high_bull = (bull_signals['made_new_high'].sum() / n_bull) * 100
    avg_ret_bull = bull_signals['weekly_return'].mean() * 100
    
    print(f"\n--- BULL SCENARIO (D2 Close > 50% of D1-D2 Range) ---")
    print(f"Sample Size        : {n_bull} weeks ({n_bull/total_weeks:.1%})")
    print(f"Prob GREEN WEEK    : {prob_green_bull:.1f}%")
    print(f"Prob NEW HIGH (Wk) : {prob_new_high_bull:.1f}%")
    print(f"Avg Weekly Return  : {avg_ret_bull:.2f}%")
    
    # 2. BEAR SIGNAL STATS (D2 < 50%)
    n_bear = len(bear_signals)
    prob_red_bear = ((~bear_signals['is_green_week']).sum() / n_bear) * 100
    prob_new_low_bear = (bear_signals['made_new_low'].sum() / n_bear) * 100
    avg_ret_bear = bear_signals['weekly_return'].mean() * 100
    
    print(f"\n--- BEAR SCENARIO (D2 Close < 50% of D1-D2 Range) ---")
    print(f"Sample Size        : {n_bear} weeks ({n_bear/total_weeks:.1%})")
    print(f"Prob RED WEEK      : {prob_red_bear:.1f}%")
    print(f"Prob NEW LOW (Wk)  : {prob_new_low_bear:.1f}%")
    print(f"Avg Weekly Return  : {avg_ret_bear:.2f}%")
    
    # 3. STATISTICAL EDGE (LIFT)
    print(f"\n--- THE EDGE (Difference from Random) ---")
    base_green = (df['is_green_week'].sum() / total_weeks) * 100
    lift_bull = prob_green_bull - base_green
    print(f"Baseline Green Wk  : {base_green:.1f}%")
    print(f"Bull Signal Lift   : {lift_bull:+.1f}% points")
    
    # 4. CONDITIONAL PROBABILITY MATRIX (Console)
    print(f"\nMATRIX SUMMARY:")
    print(f"{'Signal':<15} | {'Prob Green':<12} | {'Prob New High':<15} | {'Prob Red':<12} | {'Prob New Low':<15}")
    print(f"{'-'*15}-|-{'-'*12}-|-{'-'*15}-|-{'-'*12}-|-{'-'*15}")
    print(f"{'BULL (>50%)':<15} | {prob_green_bull:5.1f}%       | {prob_new_high_bull:5.1f}%          | {100-prob_green_bull:5.1f}%       | {bull_signals['made_new_low'].mean()*100:5.1f}%")
    print(f"{'BEAR (<50%)':<15} | {100-prob_red_bear:5.1f}%       | {bear_signals['made_new_high'].mean()*100:5.1f}%          | {prob_red_bear:5.1f}%       | {prob_new_low_bear:5.1f}%")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        analyze_weekly_d1d2_fractal(asset)
