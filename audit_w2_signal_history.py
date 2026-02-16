import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def audit_w2_signal_history(asset_key, target_month=2):
    print(f"\n{'='*90}")
    print(f"AUDIT YEAR-BY-YEAR: {asset_key} W2 BEARISH SIGNAL (<50%) FOR MONTH {target_month}")
    print(f"{'='*90}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    monthly_groups = data.groupby(['year', 'month'])
    
    total_signals = 0
    red_wins = 0      # Month Closed RED
    new_low_wins = 0  # Made New Low in W3/W4
    
    print(f"{'Year':<6} | {'W2 Condition':<12} | {'Month Ret':<10} | {'Outcome (Red)':<14} | {'New Low?':<10}")
    print("-" * 80)
    
    for (year, month), month_data in monthly_groups:
        if month != target_month: continue
        
        weeks = sorted(month_data['week_of_year'].unique())
        if len(weeks) < 2: continue
            
        # W1+W2 Context
        w1_data = month_data[month_data['week_of_year'] == weeks[0]]
        w2_data = month_data[month_data['week_of_year'] == weeks[1]]
        
        if w1_data.empty or w2_data.empty: continue

        w1_w2_high = max(w1_data['high'].max(), w2_data['high'].max())
        w1_w2_low = min(w1_data['low'].min(), w2_data['low'].min())
        w1_w2_range = w1_w2_high - w1_w2_low
        midpoint = w1_w2_low + (w1_w2_range * 0.5)
        
        w2_close = round(w2_data.iloc[-1]['close'], 2)
        
        # Check Signal
        if w2_close < midpoint:
            total_signals += 1
            
            # Outcome 1: Red Month?
            m_open = month_data.iloc[0]['open']
            m_close = month_data.iloc[-1]['close']
            is_red = m_close < m_open
            month_ret = (m_close / m_open) - 1
            
            if is_red: red_wins += 1
            
            # Outcome 2: New Low?
            # Check data strictly after W2 (Time based to be safe)
            w2_end_time = w2_data.index.max()
            post_w2_data = month_data[month_data.index > w2_end_time]
            
            made_new_low = False
            if not post_w2_data.empty:
                rest_low = post_w2_data['low'].min()
                made_new_low = rest_low < w1_w2_low
            
            if made_new_low: new_low_wins += 1
            
            # Print Row
            red_str = "WIN (RED)" if is_red else "LOSS (GREEN)"
            low_str = "YES" if made_new_low else "NO"
            
            print(f"{year:<6} | {'< 50% (Bear)':<12} | {month_ret*100:+.2f}%    | {red_str:<14} | {low_str:<10}")

    print("-" * 80)
    if total_signals > 0:
        prob_red = (red_wins / total_signals) * 100
        prob_low = (new_low_wins / total_signals) * 100
        print(f"TOTAL SIGNALS: {total_signals}")
        print(f"PROB RED MONTH: {prob_red:.1f}% ({red_wins}/{total_signals})")
        print(f"PROB NEW LOW:   {prob_low:.1f}% ({new_low_wins}/{total_signals})")
    else:
        print("No Signals Found.")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        audit_w2_signal_history(asset)
