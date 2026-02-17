import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.data_loader import download_asset_data

def analyze_weekly_recurrence(asset_key='NQ', start_date='2020-01-01', end_date='2025-12-31'):
    print(f"\n{'='*80}")
    print(f"ANALISIS DE RECURRENCIA SEMANAL (> +3%) - {asset_key}")
    print(f"Periodo: {start_date} a {end_date}")
    print(f"{'='*80}")

    # 1. Download and Resample
    data = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    
    weekly = data.resample('W').agg({
        'open': 'first',
        'close': 'last'
    }).dropna()
    
    weekly['o2c'] = (weekly['close'] - weekly['open']) / weekly['open']
    
    # 2. Identify Extreme Weeks (> 3%)
    threshold = 0.03
    extreme_weeks = weekly[weekly['o2c'] > threshold].copy()
    extreme_indices = np.where(weekly['o2c'] > threshold)[0]
    
    if len(extreme_indices) < 2:
        print("No hay suficientes eventos para calcular distancias.")
        return

    # 3. Calculate Distances (in weeks)
    distances = np.diff(extreme_indices)
    
    # 4. Statistics
    print(f"Total semanas analizadas: {len(weekly)}")
    print(f"Semanas > +3%:           {len(extreme_indices)} ({len(extreme_indices)/len(weekly)*100:.1f}%)")
    print("-" * 40)
    print(f"TIEMPO DE ESPERA ENTRE EVENTOS (Semanas):")
    print(f"  Promedio:       {np.mean(distances):.1f} semanas")
    print(f"  Mediana:        {np.median(distances):.0f} semanas")
    print(f"  Minimo:         {np.min(distances)} semana(s)")
    print(f"  Maximo:         {np.max(distances)} semanas")
    print("-" * 40)
    
    # 5. Distribution of distances
    dist_counts = pd.Series(distances).value_counts().sort_index()
    print(f"\nDISTRIBUCION DE DISTANCIAS:")
    print(f"{'Distancia':<20} | {'Frecuencia':<10} | {'% del total'}")
    print("-" * 50)
    
    # Grouping some distances for readability
    for dist, count in dist_counts.items():
        if dist <= 4:
            label = f"{dist} semana(s)"
        elif dist <= 8:
            label = f"{dist} semanas (1-2 meses)"
        else:
            label = f"{dist} semanas (> 2 meses)"
            
        print(f"{label:<20} | {count:<10} | {count/len(distances)*100:>8.1f}%")

    # 6. Detail of recent sequence
    # Show the last 5 distances
    last_5_dates = extreme_weeks.index[-6:]
    print(f"\nULTIMAS 5 SECUENCIAS:")
    for i in range(len(last_5_dates)-1):
        d1 = last_5_dates[i]
        d2 = last_5_dates[i+1]
        dist = distances[-(5-i)] if i < 5 else 0 # this math is a bit loose but illustrative
        # Let's just calculate manually for clarity
        idx1 = weekly.index.get_loc(d1)
        idx2 = weekly.index.get_loc(d2)
        real_dist = idx2 - idx1
        print(f"  Entre {d1.strftime('%Y-%m-%d')} y {d2.strftime('%Y-%m-%d')}: {real_dist} semanas de espera.")

if __name__ == "__main__":
    analyze_weekly_recurrence()
