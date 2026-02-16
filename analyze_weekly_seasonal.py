import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_weekly_fractal_by_month(asset_key):
    print(f"\n{'='*100}")
    print(f"ANALYZING WEEKLY FRACTAL (D2 SIGNAL) PERFORMANCE BY MONTH FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    # Note: Calendar month of the D2 close
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    results = []
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 2: continue
            
        d1_data = week_data.iloc[0]
        d2_data = week_data.iloc[1]
        
        # Determine strict calendar month of the signal day (D2)
        signal_month = d2_data.name.month 
        
        d1_d2_high = max(d1_data['high'], d2_data['high'])
        d1_d2_low = min(d1_data['low'], d2_data['low'])
        rng = d1_d2_high - d1_d2_low
        if rng == 0: continue
            
        midpoint = d1_d2_low + (rng * 0.5)
        d2_close = d2_data['close']
        
        # Signals
        is_bull_signal = d2_close > midpoint
        
        if len(week_data) <= 2: continue
            
        rest_of_week = week_data.iloc[2:]
        rest_high = rest_of_week['high'].max()
        rest_low = rest_of_week['low'].min()
        
        made_new_high = rest_high > d1_d2_high
        made_new_low = rest_low < d1_d2_low
        
        results.append({
            'month': signal_month,
            'is_bull_signal': is_bull_signal,
            'made_new_high': made_new_high,
            'made_new_low': made_new_low
        })
        
    df = pd.DataFrame(results)
    month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    print(f"{'Month':<5} | {'BULL SIG: Prob High':<20} | {'BEAR SIG: Prob Low':<20}")
    print(f"{'-'*5}-|-{'-'*20}-|-{'-'*20}")
    
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        if m_df.empty: continue
        
        # Bull Stats
        bull = m_df[m_df['is_bull_signal']]
        if len(bull) > 0:
            prob_high = (bull['made_new_high'].sum() / len(bull)) * 100
        else:
            prob_high = 0.0
            
        # Bear Stats
        bear = m_df[~m_df['is_bull_signal']]
        if len(bear) > 0:
            prob_low = (bear['made_new_low'].sum() / len(bear)) * 100
        else:
            prob_low = 0.0
            
        # Highlight strong edges (>80%)
        ph_star = "*" if prob_high > 80 else ""
        pl_star = "*" if prob_low > 80 else ""
        
        print(f"{month_names[m-1]:<5} | {prob_high:5.1f}% {ph_star:<14} | {prob_low:5.1f}% {pl_star:<14}")
        
    # Find Best Month/Signal Combo
    print(f"\nTOP PERFORMING SEASONAL WEEKLY SIGNALS (>80%):")
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        bull = m_df[m_df['is_bull_signal']]
        bear = m_df[~m_df['is_bull_signal']]
        
        if len(bull) > 10:
            p = (bull['made_new_high'].sum() / len(bull)) * 100
            if p > 80: print(f"- {month_names[m-1]} BULL SIGNAL: {p:.1f}% Probability of New Weekly High")
            
        if len(bear) > 10:
            p = (bear['made_new_low'].sum() / len(bear)) * 100
            if p > 80: print(f"- {month_names[m-1]} BEAR SIGNAL: {p:.1f}% Probability of New Weekly Low")

if __name__ == "__main__":
    analyze_weekly_fractal_by_month('NQ')
