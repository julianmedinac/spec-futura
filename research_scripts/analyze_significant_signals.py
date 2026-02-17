import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np
from scipy import stats

def analyze_significant_signals(asset_key):
    print(f"\n{'='*100}")
    print(f"AUDITING SIGNIFICANT MONTHLY SIGNALS (>70% WIN RATE) FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    # Collect signals
    signals = []
    
    weekly_groups = data.groupby(['year', 'month'])
    
    for (year, month), month_data in weekly_groups:
        weeks = sorted(month_data['week_of_year'].unique())
        if len(weeks) < 2: continue
            
        w1_data = month_data[month_data['week_of_year'] == weeks[0]]
        w2_data = month_data[month_data['week_of_year'] == weeks[1]]
        
        if w1_data.empty or w2_data.empty: continue

        w1_w2_high = max(w1_data['high'].max(), w2_data['high'].max())
        w1_w2_low = min(w1_data['low'].min(), w2_data['low'].min())
        rng = w1_w2_high - w1_w2_low
        midpoint = w1_w2_low + (rng * 0.5)
        w2_close = w2_data.iloc[-1]['close']
        
        # Monthly Return
        m_open = month_data.iloc[0]['open']
        m_close = month_data.iloc[-1]['close']
        ret = (m_close / m_open) - 1
        
        signals.append({
            'month': month,
            'is_bull_signal': w2_close > midpoint,
            'is_bear_signal': w2_close < midpoint,
            'return': ret
        })
        
    df = pd.DataFrame(signals)
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    print(f"{'Month':<5} | {'Signal Type':<10} | {'Win Rate':<8} | {'Avg Ret':<8} | {'T-Stat':<8} | {'P-Value':<8} | {'Verdict':<15}")
    print(f"{'-'*5}-|-{'-'*10}-|-{'-'*8}-|-{'-'*8}-|-{'-'*8}-|-{'-'*8}-|-{'-'*15}")
    
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        if m_df.empty: continue
        
        # Check Bull Signals
        bull_data = m_df[m_df['is_bull_signal']]['return']
        if len(bull_data) >= 5: # Minimum sample size for t-test
            win_rate = (bull_data > 0).mean() * 100
            
            if win_rate > 70:
                t_stat, p_val = stats.ttest_1samp(bull_data, 0)
                mean_ret = bull_data.mean() * 100
                verdict = "SIGNIFICANT" if p_val < 0.05 and t_stat > 0 else "NOISE/WEAK"
                
                print(f"{month_names[m-1]:<5} | {'BULL (>50%)':<10} | {win_rate:5.1f}%  | {mean_ret:5.2f}%  | {t_stat:6.2f}   | {p_val:6.4f}   | {verdict:<15}")

        # Check Bear Signals
        bear_data = m_df[m_df['is_bear_signal']]['return']
        if len(bear_data) >= 5:
            # For Bear signals, "Winning" means return < 0
            win_rate = (bear_data < 0).mean() * 100
            
            if win_rate > 70:
                # T-test against 0 (expecting negative mean)
                t_stat, p_val = stats.ttest_1samp(bear_data, 0)
                mean_ret = bear_data.mean() * 100
                # Significant if p < 0.05 and t_stat < 0 (negative return)
                verdict = "SIGNIFICANT" if p_val < 0.05 and t_stat < 0 else "NOISE/WEAK"
                
                print(f"{month_names[m-1]:<5} | {'BEAR (<50%)':<10} | {win_rate:5.1f}%  | {mean_ret:5.2f}%  | {t_stat:6.2f}   | {p_val:6.4f}   | {verdict:<15}")

if __name__ == "__main__":
    analyze_significant_signals('NQ')
