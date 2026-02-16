import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_seasonal_d3_failed_breakout(asset_key):
    print(f"\n{'='*100}")
    print(f"SEASONAL ANALYSIS: D3 FAILED BREAKOUT FOR {asset_key}")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    data['month'] = data.index.month
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    results = []
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue
            
        d1 = week_data.iloc[0]
        d2 = week_data.iloc[1]
        d3 = week_data.iloc[2]
        
        d1_d2_high = max(d1['high'], d2['high'])
        d1_d2_low = min(d1['low'], d2['low'])
        rng_d1_d2 = d1_d2_high - d1_d2_low
        if rng_d1_d2 == 0: continue
        
        # Bullish start (D2 close in upper half of D1-D2 range)
        if d2['close'] <= (d1_d2_low + 0.5 * rng_d1_d2): continue 
        
        # D3 breaks high
        if d3['high'] <= d1_d2_high: continue
        
        # D3 trap: closes in lower half of D1-D3 range
        d1_d3_high = max(d1_d2_high, d3['high'])
        d1_d3_low = min(d1_d2_low, d3['low'])
        rng_d1_d3 = d1_d3_high - d1_d3_low
        midpoint_d1_d3 = d1_d3_low + 0.5 * rng_d1_d3
        
        if d3['close'] >= midpoint_d1_d3: continue
        
        # Outcomes
        week_open = d1['open']
        week_close = week_data.iloc[-1]['close']
        rest_of_week = week_data.iloc[3:]
        rest_low = rest_of_week['low'].min()
        
        results.append({
            'month': d3.name.month,
            'red_week': week_close < week_open,
            'new_low': rest_low < d1_d3_low
        })
            
    df = pd.DataFrame(results)
    if df.empty:
        print("No samples found.")
        return

    month_results = []
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        n = len(m_df)
        if n > 0:
            prob_red = (m_df['red_week'].sum() / n) * 100
            prob_low = (m_df['new_low'].sum() / n) * 100
            month_results.append({'Month': m, 'Samples': n, 'Red Week %': prob_red, 'New Low %': prob_low})
    
    res_df = pd.DataFrame(month_results)
    print(res_df.to_string(index=False))
    
    snipers = res_df[res_df['New Low %'] >= 80]
    if not snipers.empty:
        print("\n🎯 SNIPER TRAPS FOUND (>80% New Low Probability):")
        print(snipers.to_string(index=False))

if __name__ == "__main__":
    for asset in ['NQ', 'ES']:
        analyze_seasonal_d3_failed_breakout(asset)
