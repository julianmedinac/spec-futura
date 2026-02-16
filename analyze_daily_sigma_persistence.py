import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def analyze_daily_sigma_persistence(asset_key, start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"ANALISIS DIARIO SIGMA PERSISTENCE: {asset_key} ({start_date} a {end_date})")
    print(f"{'='*95}")

    # 1. Download Data
    df = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    if df.empty:
        print(f"No hay datos para {asset_key}")
        return

    # 2. Calculate Daily O2C
    df['o2c'] = (df['close'] - df['open']) / df['open']
    df['next_o2c'] = df['o2c'].shift(-1)
    
    # 3. Calculate Sigma Levels
    mean_o2c = df['o2c'].mean()
    std_o2c = df['o2c'].std()
    
    upper_sigma = mean_o2c + std_o2c
    lower_sigma = mean_o2c - std_o2c
    
    print(f"Niveles Sigma Diarios:")
    print(f"  Media: {mean_o2c*100:+.3f}% | Std Dev: {std_o2c*100:.3f}%")
    print(f"  +1 Sigma: {upper_sigma*100:+.3f}%")
    print(f"  -1 Sigma: {lower_sigma*100:+.3f}%")
    print("-" * 40)

    # 4. Filter Patterns
    valid = df.dropna(subset=['next_o2c']).copy()
    
    upper_events = valid[valid['o2c'] > upper_sigma]
    lower_events = valid[valid['o2c'] < lower_sigma]
    
    u_count = len(upper_events)
    l_count = len(lower_events)
    total_days = len(valid)

    # 5. Calculate Probabilities
    # After Upper Sigma
    u_cont = (upper_events['next_o2c'] > 0).mean() * 100
    u_rev = (upper_events['next_o2c'] < 0).mean() * 100
    u_avg_next = upper_events['next_o2c'].mean() * 100
    
    # After Lower Sigma
    l_cont = (lower_events['next_o2c'] < 0).mean() * 100
    l_rev = (lower_events['next_o2c'] > 0).mean() * 100
    l_avg_next = lower_events['next_o2c'].mean() * 100

    # 6. Report
    print(f"Frecuencia de eventos: {((u_count + l_count) / total_days * 100):.1f}% de los días")
    print(f"\nRESULTADOS POST-CIERRE > +1 SIGMA ({u_count} casos):")
    print(f"  Prob. Continuacion (Verde): {u_cont:.1f}%")
    print(f"  Prob. Reversion (Roja):      {u_rev:.1f}%")
    print(f"  Retorno Promedio Dia+1:    {u_avg_next:+.3f}%")

    print(f"\nRESULTADOS POST-CIERRE < -1 SIGMA ({l_count} casos):")
    print(f"  Prob. Continuacion (Roja):   {l_cont:.1f}%")
    print(f"  Prob. Reversion (Verde):     {l_rev:.1f}%")
    print(f"  Retorno Promedio Dia+1:    {l_avg_next:+.3f}%")

if __name__ == "__main__":
    assets = ['NQ', 'ES', 'YM', 'GC']
    for a in assets:
        analyze_daily_sigma_persistence(a, start_date='2015-01-01')
        analyze_daily_sigma_persistence(a, start_date='2020-01-01')
