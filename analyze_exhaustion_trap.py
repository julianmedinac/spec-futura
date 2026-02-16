import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def analyze_momentum_exhaustion(asset_key='NQ', start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*90}")
    print(f"ANALISIS DE FATIGA DE MOMENTUM (EXHAUSTION TRAP) - {asset_key}")
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
    
    # 2. Calculate O2C Return
    weekly['o2c'] = (weekly['close'] - weekly['open']) / weekly['open']
    
    # 3. Define Thresholds (Based on our earlier findings for NQ)
    # Using 3.0% as a robust significant threshold for all indices to compare
    threshold = 0.030 
    
    # 4. Identify Sequences
    # Sequence: W1 > threshold AND W2 > threshold
    weekly['high_momentum'] = weekly['o2c'] > threshold
    weekly['is_exhaustion_setup'] = weekly['high_momentum'] & weekly['high_momentum'].shift(1)
    
    # 5. Analyze W3 (The week following the 2-week drive)
    weekly['next_o2c'] = weekly['o2c'].shift(-1)
    
    setup_events = weekly[weekly['is_exhaustion_setup'] == True].dropna(subset=['next_o2c'])
    total_events = len(setup_events)
    
    if total_events == 0:
        print(f"No se encontraron secuencias de 2 semanas > {threshold*100:.1f}%.")
        return

    # Success Definitions for Reversal (Death Trap)
    reversals = (setup_events['next_o2c'] < 0).sum()
    continuations = (setup_events['next_o2c'] > 0).sum()
    
    avg_next_ret = setup_events['next_o2c'].mean() * 100
    
    # Benchmark: Random week probability of negative close
    random_neg_prob = (weekly['o2c'] < 0).mean() * 100

    print(f"RESULTADOS TRAS 2 SEMANAS > {threshold*100:.1f}%:")
    print(f"  Eventos encontrados: {total_events}")
    print(f"  Prob. de REVERSION (Roja) en W3:  {(reversals/total_events)*100:.1f}%")
    print(f"  Prob. de CONTINUACION (Verde) en W3: {(continuations/total_events)*100:.1f}%")
    print(f"  Retorno Promedio en W3:           {avg_next_ret:+.3f}%")
    
    print(f"\nBENCHMARK (Probabilidad Base Roja):")
    print(f"  Prob. Base de semana negativa: {random_neg_prob:.1f}%")
    
    edge = (reversals/total_events)*100 - random_neg_prob
    print(f"\nVENTAJA (Alpha de Agotamiento):")
    print(f"  Reversal Edge vs Base: {edge:+.1f}%")
    
    # Also check for EXTREME exhaustion: 3 weeks drives
    weekly['is_3w_drive'] = weekly['is_exhaustion_setup'] & weekly['high_momentum'].shift(2)
    extreme_events = len(weekly[weekly['is_3w_drive'] == True].dropna())
    if extreme_events > 0:
        print(f"\nEXTREMO: Casos de 3 semanas SEGUIDAS > {threshold*100:.1f}%: {extreme_events}")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        analyze_momentum_exhaustion(asset, start_date='2015-01-01')
