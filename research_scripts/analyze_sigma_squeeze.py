import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def analyze_sigma_squeeze(asset_key='NQ', start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*90}")
    print(f"ANALISIS SIGMA-SQUEEZE (COMPRESION DE VOLATILIDAD) - {asset_key}")
    print(f"Periodo: {start_date} a {end_date}")
    print(f"{'='*90}")

    # 1. Download and Resample
    data = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    weekly = data.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna()
    
    # 2. Metrics
    # Weekly Range (High-Low/Open)
    weekly['range_pct'] = (weekly['high'] - weekly['low']) / weekly['open']
    # Open-to-Close Return
    weekly['o2c_pct'] = (weekly['close'] - weekly['open']) / weekly['open']
    
    # 3. Dynamic Thresholds based on Percentiles (to ensure sample size)
    range_mean = weekly['range_pct'].mean()
    range_std = weekly['range_pct'].std()
    o2c_std = weekly['o2c_pct'].std()

    # Squeeze = Bottom 20% of historical ranges
    squeeze_threshold = weekly['range_pct'].quantile(0.20)
    # Explosion = Top 20% or > 1 Sigma
    explosion_threshold_range = range_mean + (1.0 * range_std)
    explosion_threshold_o2c = 1.0 * o2c_std
    
    print(f"Parametros:")
    print(f"  Range Mean: {range_mean*100:.2f}% | Range Std: {range_std*100:.2f}%")
    print(f"  Umbral Squeeze (Bottom 20%): < {squeeze_threshold*100:.2f}%")
    print(f"  Umbral Explosion (1.0 std range): > {explosion_threshold_range*100:.2f}%")
    print(f"  Umbral Explosion (1.0 std o2c):   > {explosion_threshold_o2c*100:.2f}%")
    print("-" * 50)

    # 4. Identify Squeeze Weeks
    weekly['is_squeeze'] = weekly['range_pct'] < squeeze_threshold
    
    # Identify 2-Week Squeeze Sequences (W1 and W2 are squeeze)
    weekly['is_2w_squeeze'] = weekly['is_squeeze'] & weekly['is_squeeze'].shift(1)
    
    # 5. Look at W3 (The week following the 2w squeeze)
    weekly['next_range'] = weekly['range_pct'].shift(-1)
    weekly['next_abs_o2c'] = weekly['o2c_pct'].shift(-1).abs()
    
    squeeze_events = weekly[weekly['is_2w_squeeze'] == True].dropna(subset=['next_range'])
    total_events = len(squeeze_events)
    
    if total_events == 0:
        print("No se encontraron secuencias de 2 semanas de squeeze.")
        return

    # Success Definitions
    # 1. Range Explosion: W3 range > explosion_threshold_range
    range_explosions = (squeeze_events['next_range'] > explosion_threshold_range).sum()
    # 2. O2C Outlier: W3 |o2c| > explosion_threshold_o2c
    o2c_explosions = (squeeze_events['next_abs_o2c'] > explosion_threshold_o2c).sum()
    # 3. Combined: Either range or o2c explodes
    any_explosion = ((squeeze_events['next_range'] > explosion_threshold_range) | 
                     (squeeze_events['next_abs_o2c'] > explosion_threshold_o2c)).sum()

    print(f"RESULTADOS:")
    print(f"  Casos de 2-Week Squeeze: {total_events}")
    print(f"  Prob. Explosion de RANGO en W3:  {(range_explosions/total_events)*100:.1f}%")
    print(f"  Prob. Explosion de O2C en W3:    {(o2c_explosions/total_events)*100:.1f}%")
    print(f"  Prob. CUALQUIER Explosion (>1s): {(any_explosion/total_events)*100:.1f}%")
    
    # Benchmark: Random week probability of explosion (>1 sigma)
    random_prob_range = (weekly['range_pct'] > explosion_threshold_range).mean() * 100
    random_prob_o2c = (weekly['o2c_pct'].abs() > explosion_threshold_o2c).mean() * 100
    
    print(f"\nBENCHMARK (Probabilidad Base):")
    print(f"  Prob. Base Explosion Rango: {random_prob_range:.1f}%")
    print(f"  Prob. Base Explosion O2C:   {random_prob_o2c:.1f}%")
    
    edge = (any_explosion/total_events)*100 - ((random_prob_range + random_prob_o2c)/2) # Rough edge
    print(f"\nVENTAJA (Alpha):")
    print(f"  Squeeze Edge vs Base: +{any_explosion/total_events * 100 - ( (weekly['range_pct'] > explosion_threshold_range) | (weekly['o2c_pct'].abs() > explosion_threshold_o2c) ).mean() * 100:.1f}%")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        analyze_sigma_squeeze(asset, start_date='2015-01-01')
