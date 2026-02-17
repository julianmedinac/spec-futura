import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def analyze_2sigma_dynamics(asset_key, start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"ANALISIS DE EXTREMOS 2-SIGMA: {asset_key} ({start_date} a {end_date})")
    print(f"{'='*95}")

    # 1. Download Data
    df = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    if df.empty: return

    # 2. Daily O2C
    df['o2c'] = (df['close'] - df['open']) / df['open']
    df['next_o2c'] = df['o2c'].shift(-1)
    
    # 3. Global Sigma Levels
    mean_val = df['o2c'].mean()
    std_val = df['o2c'].std()
    
    upper_2s = mean_val + (2.0 * std_val)
    lower_2s = mean_val - (2.0 * std_val)
    
    print(f"Limites 2-Sigma: {lower_2s*100:+.2f}% / {upper_2s*100:+.2f}%")
    print("-" * 50)

    # 4. Filter 2-Sigma Events
    valid = df.dropna(subset=['next_o2c']).copy()
    
    u_events = valid[valid['o2c'] > upper_2s]
    l_events = valid[valid['o2c'] < lower_2s]
    
    u_count = len(u_events)
    l_count = len(l_events)

    if u_count > 0:
        u_rev = (u_events['next_o2c'] < 0).mean() * 100
        u_avg_ret = u_events['next_o2c'].mean() * 100
        print(f"POST EUFORIA (> +2s) [{u_count} casos]:")
        print(f"  Prob. Reversion (Roja): {u_rev:.1f}%")
        print(f"  Retorno Promedio D+1:   {u_avg_ret:+.3f}%")
    
    if l_count > 0:
        l_rev = (l_events['next_o2c'] > 0).mean() * 100
        l_avg_ret = l_events['next_o2c'].mean() * 100
        print(f"\nPOST PANICO (< -2s) [{l_count} casos]:")
        print(f"  Prob. Rebote (Verde):  {l_rev:.1f}%")
        print(f"  Retorno Promedio D+1:   {l_avg_ret:+.3f}%")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        analyze_2sigma_dynamics(asset)
