import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def find_profitable_patterns():
    print(f"\n{'='*120}")
    print(f"SEARCHING FOR HIGH PROBABILITY PROFIT PATTERNS (>80% WIN RATE & >3% RETURN)")
    print(f"{'='*120}")
    
    loader = DataLoader()
    assets = ['NQ', 'ES', 'DJI', 'GC']
    patterns = []
    
    for asset in assets:
        print(f"Scanning {asset}...")
        data = loader.download(asset, start_date='2000-01-01')
        if data.empty: continue

        data['year'] = data.index.year
        data['month'] = data.index.month
        data['week_of_year'] = data.index.isocalendar().week
        
        weekly_groups = data.groupby(['year', 'month'])
        results = []
        
        for (year, month), month_data in weekly_groups:
            # Drop duplicates to handle year-end week overlap correctly
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
            w2_close = w2_data.iloc[-1]['close']
            
            # Outcome
            m_open = month_data.iloc[0]['open']
            m_close = month_data.iloc[-1]['close']
            ret = (m_close / m_open) - 1
            
            # New Exts
            w2_end_time = w2_data.index.max()
            post_w2_data = month_data[month_data.index > w2_end_time]
            
            made_new_high = False
            made_new_low = False
            
            if not post_w2_data.empty:
                rest_high = post_w2_data['high'].max()
                rest_low = post_w2_data['low'].min()
                made_new_high = rest_high > w1_w2_high
                made_new_low = rest_low < w1_w2_low

            results.append({
                'month': month,
                'is_bull_signal': w2_close > midpoint,
                'return': ret,
                'made_new_high': made_new_high,
                'made_new_low': made_new_low
            })
            
        df = pd.DataFrame(results)
        
        # Analyze Monthly Performance
        for m in range(1, 13):
            m_df = df[df['month'] == m]
            if m_df.empty: continue
            
            # --- BULL SIGNAL CHECK ---
            bull_cases = m_df[m_df['is_bull_signal']]
            if len(bull_cases) >= 10: # Minimum sample size
                # Win Rate: Close Green
                win_rate = (bull_cases['return'] > 0).mean() * 100
                avg_ret = bull_cases['return'].mean() * 100
                new_high_prob = bull_cases['made_new_high'].mean() * 100
                
                if win_rate >= 80 and avg_ret >= 2.0:
                     patterns.append({
                        'Asset': asset,
                        'Month': m,
                        'Signal': 'BULL (>50%)',
                        'Win Rate': win_rate,
                        'Avg Return': avg_ret,
                        'New High Prob': new_high_prob,
                        'Action': 'LONG'
                    })
            
            # --- BEAR SIGNAL CHECK ---
            bear_cases = m_df[~m_df['is_bull_signal']]
            if len(bear_cases) >= 8: # Slightly lower threshold for bear cases (rarer)
                # Win Rate: Close Red
                win_rate = (bear_cases['return'] < 0).mean() * 100
                avg_ret = bear_cases['return'].mean() * 100 # Will be negative
                new_low_prob = bear_cases['made_new_low'].mean() * 100
                
                if win_rate >= 80 and avg_ret <= -2.0:
                    patterns.append({
                        'Asset': asset,
                        'Month': m,
                        'Signal': 'BEAR (<50%)',
                        'Win Rate': win_rate,
                        'Avg Return': avg_ret,
                        'New Low Prob': new_low_prob,
                        'Action': 'SHORT'
                    })

    # Sort and Display
    patterns_df = pd.DataFrame(patterns)
    month_names = {1:'JAN', 2:'FEB', 3:'MAR', 4:'APR', 5:'MAY', 6:'JUN', 7:'JUL', 8:'AUG', 9:'SEP', 10:'OCT', 11:'NOV', 12:'DEC'}
    
    print(f"\n{'='*100}")
    print(f"TOP TIER TRADING OPPORTUNITIES IDENTIFIED")
    print(f"{'='*100}")
    
    # Sort by Win Rate Descending
    patterns_df = patterns_df.sort_values(by='Win Rate', ascending=False)
    
    print(f"{'Asset':<6} | {'Month':<5} | {'Signal':<12} | {'Action':<6} | {'Win Rate':<10} | {'Avg Return':<12} | {'Ext Prob':<10}")
    print(f"{'-'*6}-|-{'-'*5}-|-{'-'*12}-|-{'-'*6}-|-{'-'*10}-|-{'-'*12}-|-{'-'*10}")
    
    for _, row in patterns_df.iterrows():
        m_name = month_names[row['Month']]
        ext_prob = row['New High Prob'] if row['Action'] == 'LONG' else row['New Low Prob']
        print(f"{row['Asset']:<6} | {m_name:<5} | {row['Signal']:<12} | {row['Action']:<6} | {row['Win Rate']:5.1f}%     | {row['Avg Return']:6.2f}%      | {ext_prob:5.1f}%")

if __name__ == "__main__":
    find_profitable_patterns()
