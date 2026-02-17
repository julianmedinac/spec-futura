import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_weekly_fractal_close_by_month(asset_key):
    print(f"\n{'='*100}")
    print(f"ANALYZING WEEKLY FRACTAL (D2 SIGNAL) CLOSING PERFORMANCE BY MONTH FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    results = []
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 2: continue
            
        d1_data = week_data.iloc[0]
        d2_data = week_data.iloc[1]
        
        signal_month = d2_data.name.month 
        
        d1_d2_high = max(d1_data['high'], d2_data['high'])
        d1_d2_low = min(d1_data['low'], d2_data['low'])
        rng = d1_d2_high - d1_d2_low
        if rng == 0: continue
            
        midpoint = d1_d2_low + (rng * 0.5)
        d2_close = d2_data['close']
        
        is_bull_signal = d2_close > midpoint
        
        if len(week_data) <= 2: continue
            
        week_open = week_data.iloc[0]['open']
        week_close = week_data.iloc[-1]['close']
        is_green_week = week_close > week_open
        
        results.append({
            'month': signal_month,
            'is_bull_signal': is_bull_signal,
            'is_green_week': is_green_week
        })
        
    df = pd.DataFrame(results)
    month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    print(f"{'Month':<5} | {'BULL SIG: Prob Green':<22} | {'BEAR SIG: Prob Red':<20}")
    print(f"{'-'*5}-|-{'-'*22}-|-{'-'*20}")
    
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        if m_df.empty: continue
        
        bull = m_df[m_df['is_bull_signal']]
        if len(bull) > 0:
            prob_green = (bull['is_green_week'].sum() / len(bull)) * 100
        else:
            prob_green = 0.0
            
        bear = m_df[~m_df['is_bull_signal']]
        if len(bear) > 0:
            prob_red = ((~bear['is_green_week']).sum() / len(bear)) * 100
        else:
            prob_red = 0.0
            
        pg_star = "*" if prob_green > 80 else ""
        pr_star = "*" if prob_red > 80 else ""
        
        print(f"{month_names[m-1]:<5} | {prob_green:5.1f}% {pg_star:<16} | {prob_red:5.1f}% {pr_star:<14}")
        
    print(f"\nTOP PERFORMING WEEKLY CLOSING SIGNALS (>80%):")
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        bull = m_df[m_df['is_bull_signal']]
        bear = m_df[~m_df['is_bull_signal']]
        
        if len(bull) > 10:
            p = (bull['is_green_week'].sum() / len(bull)) * 100
            if p > 80: print(f"- {month_names[m-1]} BULL SIGNAL: {p:.1f}% Probability of Green Weekly Close")
            
        if len(bear) > 10:
            p = ((~bear['is_green_week']).sum() / len(bear)) * 100
            if p > 80: print(f"- {month_names[m-1]} BEAR SIGNAL: {p:.1f}% Probability of Red Weekly Close")

if __name__ == "__main__":
    analyze_weekly_fractal_close_by_month('NQ')
