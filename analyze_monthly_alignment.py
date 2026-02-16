import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_monthly_alignment(asset_key):
    print(f"\n{'='*100}")
    print(f"MONTHLY ALIGNMENT: SEASONAL BIAS vs W1-W2 SIGNAL FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    # 1. Calculate Base Seasonality (The "Trend")
    # ------------------------------------------------
    monthly_stats = []
    weekly_groups = data.groupby(['year', 'month'])
    
    # Process each month instance
    month_instances = []
    
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
        
        # Signals
        is_bull_signal = w2_close > midpoint
        is_bear_signal = w2_close < midpoint
        
        # Outcome
        m_open = month_data.iloc[0]['open']
        m_close = month_data.iloc[-1]['close']
        is_green = m_close > m_open
        is_red = m_close < m_open
        ret = (m_close / m_open) - 1
        
        month_instances.append({
            'month': month,
            'is_bull_signal': is_bull_signal,
            'is_bear_signal': is_bear_signal,
            'is_green': is_green,
            'is_red': is_red,
            'return': ret
        })
        
    df = pd.DataFrame(month_instances)
    
    # 2. Aggregation by Calendar Month
    # ------------------------------------------------
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    print(f"{'Month':<5} | {'Base Bias':<10} | {'Bull Sig Win%':<14} | {'Bear Sig Win%':<14} | {'Best Strategy':<20}")
    print(f"{'-'*5}-|-{'-'*10}-|-{'-'*14}-|-{'-'*14}-|-{'-'*20}")
    
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        if m_df.empty: continue
        
        # Base Stats
        n = len(m_df)
        base_win_rate = (m_df['is_green'].sum() / n) * 100
        
        bias = "NEUTRAL"
        if base_win_rate > 60: bias = "BULLISH"
        if base_win_rate < 40: bias = "BEARISH"
        
        # Bull Signal Performance (W2 > 50%) -> expect Green
        bull_sigs = m_df[m_df['is_bull_signal']]
        if len(bull_sigs) > 0:
            bull_perf = (bull_sigs['is_green'].sum() / len(bull_sigs)) * 100
        else:
            bull_perf = 0.0
            
        # Bear Signal Performance (W2 < 50%) -> expect Red
        bear_sigs = m_df[m_df['is_bear_signal']]
        if len(bear_sigs) > 0:
            bear_perf = (bear_sigs['is_red'].sum() / len(bear_sigs)) * 100
        else:
            bear_perf = 0.0
            
        # Strategy Selection
        strategy = ""
        if bull_perf > 80: strategy += "LONG on Bull Sig "
        if bear_perf > 80: strategy += "SHORT on Bear Sig"
        
        if strategy == "": strategy = "Trade with Caution"
        
        # Formatting
        base_str = f"{base_win_rate:.0f}% ({bias[0:4]})"
        bull_str = f"{bull_perf:.1f}% ({len(bull_sigs)})"
        bear_str = f"{bear_perf:.1f}% ({len(bear_sigs)})"
        
        print(f"{month_names[m-1]:<5} | {base_str:<10} | {bull_str:<14} | {bear_str:<14} | {strategy:<20}")

if __name__ == "__main__":
    analyze_monthly_alignment('NQ')
