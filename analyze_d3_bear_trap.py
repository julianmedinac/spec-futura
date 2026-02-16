import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def get_monthly_w2_signal(data):
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
        start_date, end_date = m_data.index[0], w2_data.index[-1]
        range_data = m_data.loc[start_date:end_date]
        h, l = range_data['high'].max(), range_data['low'].min()
        c = w2_data.iloc[-1]['close']
        mid = l + (h - l) * 0.5
        monthly_signals[(year, month)] = 'BULL' if c > mid else 'BEAR'
    return monthly_signals

def analyze_d3_bear_trap(asset_key):
    print(f"\n{'='*100}")
    print(f"ANALYZING D3 BEAR TRAP (LOOK BELOW & FAIL) FOR {asset_key}")
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
        d1, d2, d3 = week_data.iloc[0], week_data.iloc[1], week_data.iloc[2]
        
        # 1. D1-D2 Rango Bajista (D2 Close below 50% of D1-D2 Range)
        d1_d2_h, d1_d2_l = max(d1['high'], d2['high']), min(d1['low'], d2['low'])
        rng_d1_d2 = d1_d2_h - d1_d2_l
        if rng_d1_d2 == 0: continue
        if d2['close'] >= (d1_d2_l + 0.5 * rng_d1_d2): continue
        
        # 2. D3 Ataca el Low (D3 Low < D1-D2 Low)
        if d3['low'] >= d1_d2_l: continue
        
        # 3. D3 Cierra arriba del 50% del rango D1-D3
        d1_d3_h, d1_d3_l = max(d1_d2_h, d3['high']), min(d1_d2_l, d3['low'])
        rng_d1_d3 = d1_d3_h - d1_d3_l
        mid_d1_d3 = d1_d3_l + (0.5 * rng_d1_d3)
        if d3['close'] <= mid_d1_d3: continue
        
        # Pattern Found!
        m_sig = monthly_signals.get((d3.name.year, d3.name.month), 'PENDING')
        week_o, week_c = d1['open'], week_data.iloc[-1]['close']
        rest_of_week = week_data.iloc[3:]
        rest_high = rest_of_week['high'].max()
        
        results.append({
            'month': d3.name.month,
            'm_signal': m_sig,
            'green_week': week_c > week_o,
            'new_high': rest_high > d1_d3_h
        })
            
    df = pd.DataFrame(results)
    if df.empty:
        print("No samples found.")
        return

    print(f"Total Bear Traps Found: {len(df)}")
    
    # Seasonality
    m_res = []
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        if not m_df.empty:
            m_res.append({
                'Month': m, 'Samples': len(m_df),
                'Green Week %': (m_df['green_week'].sum()/len(m_df))*100,
                'New High %': (m_df['new_high'].sum()/len(m_df))*100
            })
    print("\nSEASONAL PERFORMANCE:")
    print(pd.DataFrame(m_res).to_string(index=False))
    
    # Monthly Signal Alignment
    a_res = []
    for sig in ['BULL', 'BEAR', 'PENDING']:
        s_df = df[df['m_signal'] == sig]
        if not s_df.empty:
            a_res.append({
                'Monthly W2': sig, 'Samples': len(s_df),
                'Green Week %': (s_df['green_week'].sum()/len(s_df))*100,
                'New High %': (s_df['new_high'].sum()/len(s_df))*100
            })
    print("\nALIGNMENT WITH MONTHLY W2 SIGNAL:")
    print(pd.DataFrame(a_res).to_string(index=False))

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        analyze_d3_bear_trap(asset)
