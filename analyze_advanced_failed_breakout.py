import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def get_monthly_w2_signal(data):
    """Calculates the Monthly W2 Signal (Bull/Bear) for each month."""
    data['iso_year'] = data.index.isocalendar().year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    monthly_signals = {}
    groups = data.groupby(['iso_year', 'month'])
    
    for (year, month), m_data in groups:
        unique_weeks = m_data['week_of_year'].unique()
        if len(unique_weeks) < 2: continue
        
        w2_idx = unique_weeks[1]
        w2_data = m_data[m_data['week_of_year'] == w2_idx]
        if w2_data.empty: continue
        
        # Monthly Range from start of month to end of W2
        start_date = m_data.index[0]
        end_date = w2_data.index[-1]
        range_data = m_data.loc[start_date:end_date]
        
        h = range_data['high'].max()
        l = range_data['low'].min()
        c = w2_data.iloc[-1]['close']
        
        mid = l + (h - l) * 0.5
        monthly_signals[(year, month)] = 'BULL' if c > mid else 'BEAR'
    
    return monthly_signals

def analyze_advanced_failed_breakout(asset_key):
    print(f"\n{'='*100}")
    print(f"ADVANCED ANALYSIS: D3 FAILED BREAKOUT (LOOK ABOVE & FAIL) FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    monthly_signals = get_monthly_w2_signal(data)
    
    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    results = []
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue
            
        d1 = week_data.iloc[0]
        d2 = week_data.iloc[1]
        d3 = week_data.iloc[2]
        
        # 1. Weekly Start Bullish
        d1_d2_high = max(d1['high'], d2['high'])
        d1_d2_low = min(d1['low'], d2['low'])
        rng_d1_d2 = d1_d2_high - d1_d2_low
        if rng_d1_d2 == 0: continue
        if d2['close'] <= (d1_d2_low + 0.5 * rng_d1_d2): continue
        
        # 2. D3 Higher High
        if d3['high'] <= d1_d2_high: continue
        
        # 3. D3 Trap (Close below 50% of D1-D3 Range)
        d1_d3_high = max(d1_d2_high, d3['high'])
        d1_d3_low = min(d1_d2_low, d3['low'])
        rng_d1_d3 = d1_d3_high - d1_d3_low
        if d3['close'] >= (d1_d3_low + 0.5 * rng_d1_d3): continue
        
        # 4. Context: Monthly W2 Signal
        month = d3.name.month
        m_signal = monthly_signals.get((year, month), 'PENDING')
        
        # 5. Outcomes
        week_open = d1['open']
        week_close = week_data.iloc[-1]['close']
        rest_of_week = week_data.iloc[3:]
        rest_low = rest_of_week['low'].min()
        
        results.append({
            'month': month,
            'm_signal': m_signal,
            'red_week': week_close < week_open,
            'new_low': rest_low < d1_d3_low
        })
            
    df = pd.DataFrame(results)
    if df.empty:
        print("No patterns found.")
        return

    print(f"Total Traps Found: {len(df)}")
    
    # Seasonality
    month_stats = []
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        if not m_df.empty:
            month_stats.append({
                'Month': m,
                'Samples': len(m_df),
                'Red Week %': (m_df['red_week'].sum() / len(m_df)) * 100,
                'New Low %': (m_df['new_low'].sum() / len(m_df)) * 100
            })
    
    print("\nSEASONAL PERFORMANCE:")
    print(pd.DataFrame(month_stats).to_string(index=False))
    
    # Alignment with Monthly Signal
    print("\nALIGNMENT WITH MONTHLY W2 SIGNAL:")
    alignment_stats = []
    for sig in ['BULL', 'BEAR', 'PENDING']:
        s_df = df[df['m_signal'] == sig]
        if not s_df.empty:
            alignment_stats.append({
                'Monthly W2': sig,
                'Samples': len(s_df),
                'Red Week %': (s_df['red_week'].sum() / len(s_df)) * 100,
                'New Low %': (s_df['new_low'].sum() / len(s_df)) * 100
            })
    print(pd.DataFrame(alignment_stats).to_string(index=False))

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        analyze_advanced_failed_breakout(asset)
