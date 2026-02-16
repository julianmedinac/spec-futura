import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_w2_implications(asset_key):
    print(f"\n{'='*80}")
    print(f"ANALYZING W2 STRUCTURAL IMPLICATIONS FOR {asset_key}")
    print(f"{'='*80}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    # Calendar Helpers
    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['year', 'month'])
    
    bear_cases = []
    bull_cases = []
    
    for (year, month), month_data in weekly_groups:
        weeks = sorted(month_data['week_of_year'].unique())
        
        if len(weeks) < 2: continue # Need at least 2 weeks
            
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
        w2_close = w2_data.iloc[-1]['close']
        
        month_open = month_data.iloc[0]['open']
        month_close = month_data.iloc[-1]['close']
        
        # Check Post-W2 Price Action (New Highs/Lows)
        post_w2_data = month_data[month_data['week_of_year'] > weeks[1]]
        
        made_new_low = False
        made_new_high = False
        
        if not post_w2_data.empty:
            rest_of_month_low = post_w2_data['low'].min()
            rest_of_month_high = post_w2_data['high'].max()
            
            made_new_low = rest_of_month_low < w1_w2_low
            made_new_high = rest_of_month_high > w1_w2_high
            
        # CASE 1: BEARISH (W2 < 50%)
        if w2_close < midpoint:
            is_month_red = month_close < month_open
            bear_cases.append({
                'is_month_red': is_month_red,
                'made_new_low': made_new_low
            })
            
        # CASE 2: BULLISH (W2 > 50%)
        else:
            is_month_green = month_close > month_open
            bull_cases.append({
                'is_month_green': is_month_green,
                'made_new_high': made_new_high
            })

    # --- REPORTING ---
    
    # Bearish Stats
    df_bear = pd.DataFrame(bear_cases)
    if not df_bear.empty:
        n_bear = len(df_bear)
        prob_red = (df_bear['is_month_red'].sum() / n_bear) * 100
        prob_new_low = (df_bear['made_new_low'].sum() / n_bear) * 100
        print(f"\n[BEARISH SIGNAL] W2 Close < 50% (n={n_bear})")
        print(f"  -> Prob RED Month: {prob_red:.1f}%")
        print(f"  -> Prob NEW LOW (W3/W4): {prob_new_low:.1f}%")

    # Bullish Stats
    df_bull = pd.DataFrame(bull_cases)
    if not df_bull.empty:
        n_bull = len(df_bull)
        prob_green = (df_bull['is_month_green'].sum() / n_bull) * 100
        prob_new_high = (df_bull['made_new_high'].sum() / n_bull) * 100
        print(f"\n[BULLISH SIGNAL] W2 Close > 50% (n={n_bull})")
        print(f"  -> Prob GREEN Month: {prob_green:.1f}%")
        print(f"  -> Prob NEW HIGH (W3/W4): {prob_new_high:.1f}%")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        analyze_w2_implications(asset)
