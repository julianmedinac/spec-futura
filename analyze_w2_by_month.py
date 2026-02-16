import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_w2_signal_by_month(asset_key):
    print(f"\n{'='*80}")
    print(f"ANALYZING W1-W2 SIGNAL PERFORMANCE BY MONTH FOR {asset_key}")
    print(f"{'='*80}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['year', 'month'])
    
    results = []
    
    for (year, month), month_data in weekly_groups:
        weeks = sorted(month_data['week_of_year'].unique())
        if len(weeks) < 2: continue
            
        w1_data = month_data[month_data['week_of_year'] == weeks[0]]
        w2_data = month_data[month_data['week_of_year'] == weeks[1]]
        
        if w1_data.empty or w2_data.empty: continue

        w1_w2_high = max(w1_data['high'].max(), w2_data['high'].max())
        w1_w2_low = min(w1_data['low'].min(), w2_data['low'].min())
        w1_w2_range = w1_w2_high - w1_w2_low
        midpoint = w1_w2_low + (w1_w2_range * 0.5)
        
        # W2 Close
        w2_close = w2_data.iloc[-1]['close']
        
        # Determine Signal State
        is_below_50 = w2_close < midpoint
        
        # Monthly Outcome
        month_open = month_data.iloc[0]['open']
        month_close = month_data.iloc[-1]['close']
        is_month_red = month_close < month_open
        
        month_return = (month_close / month_open) - 1
        
        results.append({
            'month': month,
            'is_below_50': is_below_50,
            'is_month_red': is_month_red,
            'month_return': month_return
        })
        
    df = pd.DataFrame(results)
    
    # Analyze By Month (1-12)
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    print(f"\nMONTHLY BREAKDOWN:")
    print(f"------------|--------|----------------|------------|---------------|------------")
    print(f" Month      | Sample | BEAR WIN RATE (<50%->Red) | Avg Ret (Bear)| BULL WIN RATE (>50%->Grn) | Avg Ret (Bull)")
    print(f"------------|--------|----------------|------------|---------------|------------")
    
    for m in range(1, 13):
        m_data = df[df['month'] == m]
        if m_data.empty: continue
            
        # BEAR SIGNAL ANALYSIS
        bear_cases = m_data[m_data['is_below_50']]
        n_bear = len(bear_cases)
        
        if n_bear > 0:
            bear_win_rate = (bear_cases['is_month_red'].sum() / n_bear) * 100
            bear_avg_ret = bear_cases['month_return'].mean() * 100
        else:
            bear_win_rate = 0.0
            bear_avg_ret = 0.0
            
        # BULL SIGNAL ANALYSIS
        bull_cases = m_data[~m_data['is_below_50']]
        n_bull = len(bull_cases)
        
        if n_bull > 0:
            bull_win_rate = ((~bull_cases['is_month_red']).sum() / n_bull) * 100
            bull_avg_ret = bull_cases['month_return'].mean() * 100
        else:
            bull_win_rate = 0.0
            bull_avg_ret = 0.0
            
        total_sample = n_bear + n_bull
        
        # Highlight best performers
        bear_star = "*" if bear_win_rate > 70 else ""
        bull_star = "*" if bull_win_rate > 80 else ""
        
        print(f" {month_names[m-1]:<10} |   {total_sample:2d}   |     {bear_win_rate:4.1f}% {bear_star:<2}   |   {bear_avg_ret:5.2f}%   |     {bull_win_rate:4.1f}% {bull_star:<2}    |   {bull_avg_ret:5.2f}%")

    print(f"\nOBSERVATIONS:")
    print(f"- BEAR SIGNAL WIN RATE: Percentage of times a weak W2 (<50%) leads to a RED month.")
    print(f"- BULL SIGNAL WIN RATE: Percentage of times a strong W2 (>50%) leads to a GREEN month.")

if __name__ == "__main__":
    analyze_w2_signal_by_month('NQ')
