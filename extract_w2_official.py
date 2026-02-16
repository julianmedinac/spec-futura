import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def extract_w2_official_data(asset_key, target_month=2):
    """
    Extracts the EXACT Monthly Probabilities used in the visualize_w2_matrix.py chart
    for a specific month.
    """
    # 1. Download Data (Exactly as visualize script does)
    loader = DataLoader() # Using Class defaults
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['year', 'month'])
    
    # List to store result dicts (this was missing initiation in previous attempts?)
    # No, it was initiated inside a loop maybe? Wait, checking logic.
    year_month_results = []
    
    for (year, month), month_data in weekly_groups:
        # EXACT LOGIC from visualize_w2_matrix.py lines 46-99
        weeks = month_data['week_of_year'].drop_duplicates().tolist()
        
        if len(weeks) < 2: continue
            
        w1_data = month_data[month_data['week_of_year'] == weeks[0]]
        w2_data = month_data[month_data['week_of_year'] == weeks[1]]
        
        if w1_data.empty or w2_data.empty: continue

        w1_w2_high = max(w1_data['high'].max(), w2_data['high'].max())
        w1_w2_low = min(w1_data['low'].min(), w2_data['low'].min())
        rng = w1_w2_high - w1_w2_low
        if rng == 0: continue
            
        midpoint = w1_w2_low + (rng * 0.5)
        w2_close = round(w2_data.iloc[-1]['close'], 2)
        
        is_bull_signal = w2_close > midpoint
        
        m_open = month_data.iloc[0]['open']
        m_close = month_data.iloc[-1]['close']
        is_green = m_close > m_open
        
        # New High/Low Logic (Strictly post W2)
        w2_end_time = w2_data.index.max()
        post_w2_data = month_data[month_data.index > w2_end_time]
        
        made_new_high = False
        made_new_low = False
        
        if not post_w2_data.empty:
            rest_high = post_w2_data['high'].max()
            rest_low = post_w2_data['low'].min()
            
            made_new_high = rest_high > w1_w2_high
            made_new_low = rest_low < w1_w2_low
            
        year_month_results.append({
            'month': month,
            'is_bull_signal': is_bull_signal,
            'is_green': is_green,
            'made_new_high': made_new_high,
            'made_new_low': made_new_low
        })
        
    df = pd.DataFrame(year_month_results)
    
    # Filter for Target Month
    m_df = df[df['month'] == target_month]
    if m_df.empty: 
        print(f"[{asset_key}] No data for Month {target_month}")
        return

    # EXTRACT STATS
    
    # Bear Signal Stats (< 50%)
    bear_cases = m_df[~m_df['is_bull_signal']]
    n_bear = len(bear_cases)
    
    if n_bear > 0:
        prob_red = ((~bear_cases['is_green']).sum() / n_bear) * 100
        prob_new_low = (bear_cases['made_new_low'].sum() / n_bear) * 100
        
        print(f"\n===== {asset_key} OFFICIAL STATS (FEB - BEAR SIGNAL) =====")
        print(f"   [Sample Size]: {n_bear}")
        print(f"   Probability RED MONTH:  {prob_red:.1f}%")
        print(f"   Probability NEW LOW:    {prob_new_low:.1f}%")
    else:
        print(f"[{asset_key}] No Bear Signals found for Month {target_month}")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        extract_w2_official_data(asset, target_month=2)
