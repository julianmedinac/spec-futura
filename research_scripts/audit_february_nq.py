import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def audit_february_nq_w2_signal():
    print(f"\n{'='*100}")
    print(f"AUDITING FEBRUARY NQ BEAR SIGNAL (W2 < 50%)")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download('NQ', start_date='2000-01-01')
    if data.empty: return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    # Filter for FEBRUARY ONLY
    feb_data = data[data['month'] == 2]
    weekly_groups = feb_data.groupby(['year'])
    
    bearish_cases = []
    
    for year, month_data in weekly_groups:
        # Fix: year is a tuple because we grouped by ['year']
        year_val = year[0] if isinstance(year, tuple) else year

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
        
        # Check Signal: W2 Close < Midpoint
        if w2_close < midpoint:
            
            # Check Outcome 1: Red Month?
            m_open = month_data.iloc[0]['open']
            m_close = month_data.iloc[-1]['close']
            is_red = m_close < m_open
            ret = (m_close / m_open) - 1
            
            # Check Outcome 2: New Low in W3/W4?
            post_w2_data = month_data[month_data['week_of_year'] > weeks[1]]
            
            if not post_w2_data.empty:
                rest_low = post_w2_data['low'].min()
                made_new_low = rest_low < w1_w2_low
            else:
                made_new_low = False
                
            bearish_cases.append({
                'year': year_val,
                'is_red': is_red,
                'month_return': ret,
                'made_new_low': made_new_low
            })
            
    df = pd.DataFrame(bearish_cases)
    
    if df.empty:
        print("No cases found.")
        return
        
    n = len(df)
    prob_red = (df['is_red'].sum() / n) * 100
    prob_new_low = (df['made_new_low'].sum() / n) * 100
    avg_ret = df['month_return'].mean() * 100
    
    print(f"\nSAMPLE SIZE: {n} Februarys with Bearish W2 Signal")
    print(f"Prob Red Month: {prob_red:.1f}%")
    print(f"Prob New Low  : {prob_new_low:.1f}%")
    print(f"Avg Return    : {avg_ret:.2f}%")
    
    print(f"\nCASE BY CASE BREAKDOWN:")
    print(f"{'Year':<6} | {'Red Month?':<10} | {'New Low?':<10} | {'Return':<8}")
    print(f"{'-'*6}-|-{'-'*10}-|-{'-'*10}-|-{'-'*8}")
    
    for _, row in df.iterrows():
        print(f"{int(row['year']):<6} | {str(row['is_red']):<10} | {str(row['made_new_low']):<10} | {row['month_return']*100:5.2f}%")

    print(f"\n\nANALYSIS OF DISCREPANCY:")
    discrepancy_cases = df[(df['is_red']) & (~df['made_new_low'])]
    print(f"Cases where Month was RED but NO NEW LOW was made: {len(discrepancy_cases)}")
    if not discrepancy_cases.empty:
        print(f"Years: {discrepancy_cases['year'].tolist()}")
        print("INTERPRETATION: In these years, the market bled slowly or closed near the lows established in W1/W2, but didn't crash through support.")

if __name__ == "__main__":
    audit_february_nq_w2_signal()
