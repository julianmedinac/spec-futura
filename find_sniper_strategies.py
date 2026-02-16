import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def find_sniper_strategies(asset_key):
    print(f"\n====================================================================================================")
    print(f"HUNTING FOR SNIPER STRATEGIES (>80% WR) - COMPOSITE PATTERNS FOR {asset_key}")
    print(f"====================================================================================================")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    data['month'] = data.index.month
    
    # Pre-calculate Monthly W2 Signal for each timestamp
    # We need to know for any given day, what was the status of W2 of THAT month?
    # This is complex because W2 happens once a month.
    # Approach: Group by Year-Month, calculate W2 signal, then map it to all days in that month?
    # Or easier: Just analyze weekly patterns and check what month they fall in, 
    # and if that month's W2 signal (if completed) aligned? 
    # Wait, the user likely means: "Does the Monthly W2 Signal filter improve the Weekly setup?"
    # Example: If Monthly W2 was Bullish -> Does Weekly D2 Bull signal perform better?
    # Yes. Let's compute Monthly W2 Status first.

    monthly_groups = data.groupby(['iso_year', 'month'])
    monthly_signals = {} # (year, month) -> 'BULL' or 'BEAR' or None
    
    for (year, month), month_data in monthly_groups:
        # Find Week 2 of this month
        # Definition of W2: The second iso-week that has data in this month? 
        # Or simple definition: The week containing the 8th-14th?
        # Let's use the standard W2 logic from previous scripts: 2nd full trading week?
        # Simplification for this script: W2 is the week where day 8-14 falls?
        # Better: Group by weeks, take the 2nd week start time.
        
        # Let's trust the 'week_of_year' relative to the month start.
        # Unique weeks in this month:
        unique_weeks = month_data['week_of_year'].unique()
        if len(unique_weeks) < 2: continue
        
        w2_idx = unique_weeks[1] # The second week
        w2_data = month_data[month_data['week_of_year'] == w2_idx]
        
        if len(w2_data) < 2: continue
        
        # Calculate W1-W2 range (approximate using month start to W2 end)
        # Actually, the W2 signal is: Close of W2 vs Range(Start Month to End W2).
        month_start_to_w2_end = month_data.loc[:w2_data.index[-1]]
        
        period_high = month_start_to_w2_end['high'].max()
        period_low = month_start_to_w2_end['low'].min()
        w2_close = w2_data.iloc[-1]['close']
        
        rng = period_high - period_low
        mid = period_low + rng * 0.5
        
        signal = 'BULL' if w2_close > mid else 'BEAR'
        monthly_signals[(year, month)] = signal

    # NOW ANALYZE WEEKLY STRATEGIES WITH THIS CONTEXT
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    
    results = []
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue
            
        d1 = week_data.iloc[0]
        d2 = week_data.iloc[1]
        
        month = d2.name.month
        
        # 1. Weekly Fractal Signal (D2)
        d1_d2_high = max(d1['high'], d2['high'])
        d1_d2_low = min(d1['low'], d2['low'])
        rng = d1_d2_high - d1_d2_low
        if rng == 0: continue
        mid = d1_d2_low + rng * 0.5
        d2_close = d2['close']
        
        weekly_signal = 'BULL' if d2_close > mid else 'BEAR'
        
        # 2. Monthly Context (W2 Signal)
        # We need the signal from the CURRENT month.
        # But wait, if we are in Week 1 or Week 2, the Monthly W2 signal hasn't happened yet!
        # The Monthly W2 signal is a filter for W3 and W4 trading.
        # So check if this week > W2 of the month.
        
        current_month_signal = monthly_signals.get((year, month), 'NEUTRAL')
        
        # Is this week AFTER W2?
        # Simple check: Is day of month > 14?
        is_post_w2 = d2.name.day > 14
        
        monthly_context = 'PENDING'
        if is_post_w2:
            monthly_context = current_month_signal
            
        # 3. Outcomes
        # D3 Breakout?
        d3 = week_data.iloc[2]
        d3_broke_high = d3['high'] > d1_d2_high
        d3_broke_low = d3['low'] < d1_d2_low
        
        # Extension (Thu/Fri)
        rest = week_data.iloc[3:]
        ext_high = rest['high'].max() > d3['high'] if d3_broke_high else False
        ext_low = rest['low'].min() < d3['low'] if d3_broke_low else False
        
        # New Weekly High/Low regardless of D3
        made_new_high = week_data['high'].max() > d1_d2_high
        made_new_low = week_data['low'].min() < d1_d2_low
        
        results.append({
            'month': month,
            'weekly_sig': weekly_signal,
            'monthly_ctx': monthly_context,
            'd3_break_high': d3_broke_high,
            'd3_break_low': d3_broke_low,
            'ext_high': ext_high,
            'ext_low': ext_low,
            'new_high_any': made_new_high,
            'new_low_any': made_new_low
        })
        
    df = pd.DataFrame(results)
    
    # --- STRATEGY 1: THE PERFECT BULL (Alignment) ---
    # Monthly Bull + Weekly Bull
    mask_bull = (df['monthly_ctx'] == 'BULL') & (df['weekly_sig'] == 'BULL')
    df_bull = df[mask_bull]
    if len(df_bull) > 10:
        wr = (df_bull['new_high_any'].sum() / len(df_bull)) * 100
        print(f"STRATEGY: MONTHLY BULL + WEEKLY BULL (Trend Alignment)")
        print(f"  -> Win Rate (New High): {wr:.1f}%  (Samples: {len(df_bull)})")
        
        # D3 Confirmation Layer
        df_bull_d3 = df_bull[df_bull['d3_break_high']]
        if len(df_bull_d3) > 5:
            wr_ext = (df_bull_d3['ext_high'].sum() / len(df_bull_d3)) * 100
            print(f"  -> IF D3 BREAKS HIGH: Extension Probability: {wr_ext:.1f}%")

    # --- STRATEGY 2: THE PERFECT BEAR (Alignment) ---
    mask_bear = (df['monthly_ctx'] == 'BEAR') & (df['weekly_sig'] == 'BEAR')
    df_bear = df[mask_bear]
    if len(df_bear) > 10:
        wr = (df_bear['new_low_any'].sum() / len(df_bear)) * 100
        print(f"\nSTRATEGY: MONTHLY BEAR + WEEKLY BEAR (Trend Alignment)")
        print(f"  -> Win Rate (New Low): {wr:.1f}%  (Samples: {len(df_bear)})")
        
        df_bear_d3 = df_bear[df_bear['d3_break_low']]
        if len(df_bear_d3) > 5:
            wr_ext = (df_bear_d3['ext_low'].sum() / len(df_bear_d3)) * 100
            print(f"  -> IF D3 BREAKS LOW: Extension Probability: {wr_ext:.1f}%")

    # --- STRATEGY 3: SEASONAL SNIPERS (Month + Weekly Sig) ---
    print(f"\nSEASONAL SNIPER SETUPS (>85% WR):")
    for m in range(1, 13):
        # Bull
        df_m = df[(df['month'] == m) & (df['weekly_sig'] == 'BULL')]
        if len(df_m) > 10:
            wr = (df_m['new_high_any'].sum() / len(df_m)) * 100
            if wr > 85:
                print(f"  -> [MONTH {m}] BULL SIGNAL: {wr:.1f}% Win Rate")
                
        # Bear
        df_m = df[(df['month'] == m) & (df['weekly_sig'] == 'BEAR')]
        if len(df_m) > 10:
            wr = (df_m['new_low_any'].sum() / len(df_m)) * 100
            if wr > 85:
                 print(f"  -> [MONTH {m}] BEAR SIGNAL: {wr:.1f}% Win Rate")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        find_sniper_strategies(asset)
