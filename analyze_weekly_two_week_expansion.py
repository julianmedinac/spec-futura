import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.data_loader import download_asset_data

def analyze_two_week_expansion(asset_key='NQ', start_date='2020-01-01', end_date='2025-12-31'):
    print(f"\n{'='*80}")
    print(f"ANALISIS DE EXPANSION DE RANGO 2 SEMANAS (W1+W2) - {asset_key}")
    print(f"Condicion: W1 O2C > +3.5%")
    print(f"{'='*80}")

    # 1. Download Data
    data = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    
    # Weekly resample with OHLC
    weekly = data.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna()
    
    # Calculate O2C (Weekly)
    weekly['o2c'] = (weekly['close'] - weekly['open']) / weekly['open']
    
    # 2. Identify Trigger Weeks (W1)
    threshold = 0.035
    w1_indices = weekly[weekly['o2c'] > threshold].index
    
    results = []
    
    # 3. Calculate Combined Range for W1 + W2
    for idx in w1_indices:
        # Find position of W1
        pos = weekly.index.get_loc(idx)
        
        # Check if W2 exists
        if pos + 1 < len(weekly):
            w1 = weekly.iloc[pos]
            w2 = weekly.iloc[pos+1]
            
            combined_high = max(w1['high'], w2['high'])
            combined_low = min(w1['low'], w2['low'])
            
            # Range as % of W1 Open
            combined_range_pct = (combined_high - combined_low) / w1['open'] * 100
            w1_range_pct = (w1['high'] - w1['low']) / w1['open'] * 100
            expansion = combined_range_pct - w1_range_pct
            
            results.append({
                'Date_W1': idx.strftime('%Y-%m-%d'),
                'W1_O2C': w1['o2c'] * 100,
                'W1_Range': w1_range_pct,
                'Combined_Range': combined_range_pct,
                'Expansion': expansion,
                'W2_O2C': w2['o2c'] * 100
            })

    res_df = pd.DataFrame(results)
    
    # 4. Benchmarking (Normal 2-week range)
    # Calculate for all rolling 2-week periods
    all_ranges = []
    for i in range(len(weekly) - 1):
        w_a = weekly.iloc[i]
        w_b = weekly.iloc[i+1]
        c_h = max(w_a['high'], w_b['high'])
        c_l = min(w_a['low'], w_b['low'])
        all_ranges.append((c_h - c_l) / w_a['open'] * 100)
    
    avg_normal_range = np.mean(all_ranges)

    # 5. Output
    print(f"Eventos encontrados: {len(res_df)}")
    print("-" * 40)
    print(f"Estadisticas del Rango Combinado (W1+W2):")
    print(f"  Media:          {res_df['Combined_Range'].mean():.2f}%")
    print(f"  Mediana:        {res_df['Combined_Range'].median():.2f}%")
    print(f"  Minimo:         {res_df['Combined_Range'].min():.2f}%")
    print(f"  Maximo:         {res_df['Combined_Range'].max():.2f}%")
    print("-" * 40)
    print(f"Comparativa:")
    print(f"  Rango W1 (Promedio):          {res_df['W1_Range'].mean():.2f}%")
    print(f"  Expansion extra en W2:        {res_df['Expansion'].mean():.2f}%")
    print(f"  Rango 2-sem normal (Base):    {avg_normal_range:.2f}%")
    print("-" * 40)
    
    print(f"\nDETALLE DE EVENTOS RECIENTES (Ultimos 10):")
    print(res_df[['Date_W1', 'W1_O2C', 'W1_Range', 'Combined_Range', 'W2_O2C']].tail(10).to_string(index=False))

if __name__ == "__main__":
    analyze_two_week_expansion()
