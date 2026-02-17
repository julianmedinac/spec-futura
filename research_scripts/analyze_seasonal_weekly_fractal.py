import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_seasonal_weekly_fractal(asset_key):
    print(f"\n{'='*80}")
    print(f"SEASONAL ANALYSIS: W2 Fractal (D2 close > 50% vs < 50%)")
    print(f"Asset: {asset_key}")
    print(f"{'='*80}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    data['month'] = data.index.month

    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    results = []

    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue
        
        d1 = week_data.iloc[0]
        d2 = week_data.iloc[1]
        
        d1_d2_high = max(d1['high'], d2['high'])
        d1_d2_low = min(d1['low'], d2['low'])
        rng = d1_d2_high - d1_d2_low
        if rng == 0: continue
            
        midpoint = d1_d2_low + (rng * 0.5)
        d2_close = d2['close']
        
        # Determine the signal type based on D2 close
        signal_type = 'BULL' if d2_close > midpoint else 'BEAR'
        signal_month = d2.name.month

        # Calculate weekly outcome
        week_open = week_data.iloc[0]['open']
        week_close = week_data.iloc[-1]['close']
        is_green_week = week_close > week_open
        
        # Calculate extension
        # For Bull signal: new high on Thu/Fri > Max(D1, D2, D3)
        # For Bear signal: new low on Thu/Fri < Min(D1, D2, D3)
        d3 = week_data.iloc[2]
        rest_of_week = week_data.iloc[3:]
        
        if signal_type == 'BULL':
             ref_high = max(d1_d2_high, d3['high'])
             extended = rest_of_week['high'].max() > ref_high
        else:
             ref_low = min(d1_d2_low, d3['low'])
             extended = rest_of_week['low'].min() < ref_low

        results.append({
            'month': signal_month,
            'signal_type': signal_type,
            'is_green_week': is_green_week,
            'extended': extended
        })

    df = pd.DataFrame(results)
    
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    print(f"{'MONTH':<5} | {'BULL: GREEN WK%':<15} | {'BULL: EXT%':<10} | {'BEAR: RED WK%':<15} | {'BEAR: EXT%':<10}")
    print("-" * 75)

    for i, m_name in enumerate(months):
        m = i + 1
        m_df = df[df['month'] == m]
        
        # Bull Signal Stats
        bull_df = m_df[m_df['signal_type'] == 'BULL']
        if len(bull_df) > 5:
            bull_green_pct = (bull_df['is_green_week'].sum() / len(bull_df)) * 100
            bull_ext_pct = (bull_df['extended'].sum() / len(bull_df)) * 100
            bull_str = f"{bull_green_pct:13.1f}%"
            bull_ext_str = f"{bull_ext_pct:8.1f}%"
        else:
            bull_str = "    N/A      "
            bull_ext_str = "   N/A  "

        # Bear Signal Stats
        bear_df = m_df[m_df['signal_type'] == 'BEAR']
        if len(bear_df) > 5:
             # For Bear signal, we look for Red Week (NOT Green)
             bear_red_pct = ((len(bear_df) - bear_df['is_green_week'].sum()) / len(bear_df)) * 100
             bear_ext_pct = (bear_df['extended'].sum() / len(bear_df)) * 100
             bear_str = f"{bear_red_pct:13.1f}%"
             bear_ext_str = f"{bear_ext_pct:8.1f}%"
        else:
             bear_str = "    N/A      "
             bear_ext_str = "   N/A  "
             
        print(f"{m_name:<5} | {bull_str} | {bull_ext_str} | {bear_str} | {bear_ext_str}")

if __name__ == "__main__":
    analyze_seasonal_weekly_fractal('NQ')
