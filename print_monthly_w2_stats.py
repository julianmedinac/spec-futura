import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.data.data_loader import DataLoader

def print_monthly_w2_stats(asset_key):
    print(f"\n{'='*90}")
    print(f"AUDITED MONTHLY W2 FRACTAL STATISTICS FOR {asset_key}")
    print(f"Scenario 1: W2 Close > 50% of W1-W2 Range (BULL SIGNAL)")
    print(f"Scenario 2: W2 Close < 50% of W1-W2 Range (BEAR SIGNAL)")
    print(f"Metrics: Prob Green/Red Month | Prob New Month High/Low (Post-W2)")
    print(f"{'='*90}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['year'] = data.index.isocalendar().year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    # Group by Month
    monthly_groups = data.groupby(['year', 'month'])
    results = []
    
    for (year, month), month_data in monthly_groups:
        # Identify W1 and W2 using actual calendar weeks within the month
        # Unique weeks
        weeks = month_data['week_of_year'].unique()
        if len(weeks) < 2: continue
        
        # W1 is first week, W2 is second
        w1_idx = weeks[0]
        w2_idx = weeks[1]
        
        w1_data = month_data[month_data['week_of_year'] == w1_idx]
        w2_data = month_data[month_data['week_of_year'] == w2_idx]
        
        if w1_data.empty or w2_data.empty: continue
        
        # Calculate W1-W2 Range
        # Combine data up to end of W2
        w2_end_time = w2_data.index.max()
        pre_signal_data = month_data[month_data.index <= w2_end_time]
        
        h = pre_signal_data['high'].max()
        l = pre_signal_data['low'].min()
        rng = h - l
        if rng == 0: continue
        
        midpoint = l + rng * 0.5
        w2_close = w2_data.iloc[-1]['close']
        
        # Signal
        is_bull = w2_close > midpoint
        
        # Outcomes
        # 1. Close Color (Green/Red Month)
        m_open = month_data.iloc[0]['open']
        m_close = month_data.iloc[-1]['close']
        is_green_month = m_close > m_open
        
        # 2. Extension (Post W2)
        post_signal_data = month_data[month_data.index > w2_end_time]
        
        made_new_high = False
        made_new_low = False
        
        if not post_signal_data.empty:
            rest_high = post_signal_data['high'].max()
            rest_low = post_signal_data['low'].min()
            made_new_high = rest_high > h
            made_new_low = rest_low < l
            
        results.append({
            'month': month,
            'signal': 'BULL' if is_bull else 'BEAR',
            'outcome_green': is_green_month,
            'outcome_new_high': made_new_high,
            'outcome_new_low': made_new_low
        })
        
    df = pd.DataFrame(results)
    
    # Print Table
    print(f"{'MONTH':<5} | {'BULL: GREEN MTH%':<16} | {'BULL: NEW HI%':<14} | {'BEAR: RED MTH%':<15} | {'BEAR: NEW LO%':<14}")
    print("-" * 80)
    
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    for i, m_name in enumerate(months):
        m = i + 1
        m_df = df[df['month'] == m]
        
        # Bull Stats
        bull = m_df[m_df['signal'] == 'BULL']
        if len(bull) >= 5:
            b_green = (bull['outcome_green'].sum() / len(bull)) * 100
            b_high = (bull['outcome_new_high'].sum() / len(bull)) * 100
            b_str = f"{b_green:5.1f}% ({len(bull)})"
            bh_str = f"{b_high:5.1f}%"
        else:
            b_str = "   N/A    "
            bh_str = "  N/A "
            
        # Bear Stats
        bear = m_df[m_df['signal'] == 'BEAR']
        if len(bear) >= 5:
            be_red = ((len(bear) - bear['outcome_green'].sum()) / len(bear)) * 100
            be_low = (bear['outcome_new_low'].sum() / len(bear)) * 100
            be_str = f"{be_red:5.1f}% ({len(bear)})"
            bl_str = f"{be_low:5.1f}%"
        else:
            be_str = "   N/A    "
            bl_str = "  N/A "
            
        print(f"{m_name:<5} | {b_str:<16} | {bh_str:<14} | {be_str:<15} | {bl_str:<14}")

if __name__ == "__main__":
    print_monthly_w2_stats('NQ')
