import pandas as pd
import numpy as np
from src.data.data_loader import DataLoader

def print_seasonal_stats(asset_key):
    print(f"\n{'='*80}")
    print(f"AUDITED MONTHLY FRACTAL STATISTICS FOR {asset_key}")
    print(f"Scenario: D2 Signal + D3 Breakout -> Continuation Probability")
    print(f"{'='*80}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    results = []
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue 
        
        d1 = week_data.iloc[0]
        d2 = week_data.iloc[1]
        d3 = week_data.iloc[2]
        
        d1_d2_h = max(d1['high'], d2['high'])
        d1_d2_l = min(d1['low'], d2['low'])
        rng = d1_d2_h - d1_d2_l
        if rng == 0: continue
            
        midpoint = d1_d2_l + (rng * 0.5)
        d2_close = d2['close']
        signal_month = d2.name.month 
        
        # BULL SCENARIO
        if d2_close > midpoint:
            if d3['high'] > d1_d2_h:
                rest_high = week_data.iloc[3:]['high'].max()
                week_close = week_data.iloc[-1]['close']
                d3_close = d3['close']
                
                results.append({
                    'month': signal_month,
                    'type': 'BULL',
                    'extension': rest_high > d3['high'],
                    'hold_gains': week_close > d3_close
                })

        # BEAR SCENARIO
        else: 
            if d3['low'] < d1_d2_l:
                rest_low = week_data.iloc[3:]['low'].min()
                week_close = week_data.iloc[-1]['close']
                d3_close = d3['close']
                
                results.append({
                    'month': signal_month,
                    'type': 'BEAR',
                    'extension': rest_low < d3['low'],
                    'hold_gains': week_close < d3_close
                })

    df = pd.DataFrame(results)
    if df.empty: return

    # Print Table
    print(f"{'MONTH':<10} | {'BULL EXTENSION':<15} | {'BULL HOLD':<15} | {'BEAR EXTENSION':<15} | {'BEAR HOLD':<15}")
    print("-" * 80)
    
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    for i, m_name in enumerate(months):
        m = i + 1
        m_df = df[df['month'] == m]
        
        # Bull
        bull = m_df[m_df['type'] == 'BULL']
        if len(bull) > 5:
            b_ext = (bull['extension'].sum() / len(bull)) * 100
            b_hol = (bull['hold_gains'].sum() / len(bull)) * 100
            b_str = f"{b_ext:5.1f}%"
            h_str = f"{b_hol:5.1f}%"
        else:
            b_str = "  N/A "
            h_str = "  N/A "
            
        # Bear
        bear = m_df[m_df['type'] == 'BEAR']
        if len(bear) > 5:
            be_ext = (bear['extension'].sum() / len(bear)) * 100
            be_hol = (bear['hold_gains'].sum() / len(bear)) * 100
            be_str = f"{be_ext:5.1f}%"
            he_str = f"{be_hol:5.1f}%"
        else:
            be_str = "  N/A "
            he_str = "  N/A "
            
        print(f"{m_name:<10} | {b_str:<15} | {h_str:<15} | {be_str:<15} | {he_str:<15}")

if __name__ == "__main__":
    for asset in ['NQ']:
        print_seasonal_stats(asset)
