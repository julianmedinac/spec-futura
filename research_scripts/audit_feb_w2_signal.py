import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def audit_feb_w2_signal(asset_key, target_month=2):
    print(f"\n{'='*80}")
    print(f"AUDIT: {asset_key} W2 SIGNAL BREAKDOWN FOR MONTH {target_month} (FEB)")
    print(f"{'='*80}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    # Calendar Helpers
    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    monthly_groups = data.groupby(['year', 'month'])
    
    total_months = 0
    bear_signals = 0
    bear_wins = 0 # Month ended RED
    
    print(f"{'Year':<6} | {'W2 Close':<10} | {'Midpoint':<10} | {'Signal':<10} | {'Month Ret':<10} | {'Outcome'}")
    print("-" * 75)
    
    for (year, month), month_data in monthly_groups:
        if month != target_month: continue
        
        total_months += 1
        weeks = sorted(month_data['week_of_year'].unique())
        
        if len(weeks) < 2: continue
            
        # W1 and W2 Data
        w1_data = month_data[month_data['week_of_year'] == weeks[0]]
        w2_data = month_data[month_data['week_of_year'] == weeks[1]]
        
        if w1_data.empty or w2_data.empty: continue

        # Calculate Combined W1-W2 Range
        w1_w2_high = max(w1_data['high'].max(), w2_data['high'].max())
        w1_w2_low = min(w1_data['low'].min(), w2_data['low'].min())
        w1_w2_range = w1_w2_high - w1_w2_low
        midpoint = w1_w2_low + (w1_w2_range * 0.5)
        
        # W2 Close
        w2_close = round(w2_data.iloc[-1]['close'], 2)
        midpoint = round(midpoint, 2)
        
        month_open = month_data.iloc[0]['open']
        month_close = month_data.iloc[-1]['close']
        month_ret = (month_close / month_open) - 1
        is_red = month_ret < 0
        
        # Check Signal: W2 < 50%
        if w2_close < midpoint:
            bear_signals += 1
            signal_type = "BEAR (<50%)"
            
            outcome = "WIN (RED)" if is_red else "LOSS (GREEN)"
            if is_red: bear_wins += 1
            
            print(f"{year:<6} | {w2_close:<10} | {midpoint:<10} | {signal_type:<10} | {month_ret*100:+.2f}%    | {outcome}")

    print("-" * 75)
    print(f"TOTAL FEBRUARIES ANALYZED: {total_months}")
    print(f"BEAR SIGNALS TRIGGERED (W2 < 50%): {bear_signals}")
    if bear_signals > 0:
        win_rate = (bear_wins / bear_signals) * 100
        print(f"BEAR SIGNAL WIN RATE (RED MONTH): {win_rate:.1f}% ({bear_wins}/{bear_signals})")
    else:
        print("No Signals Triggered.")

if __name__ == "__main__":
    audit_feb_w2_signal('NQ')
