import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.data_loader import download_asset_data

def analyze_weekly_persistence(asset_key='NQ', start_date='2020-01-01', end_date='2025-12-31'):
    print(f"\n{'='*70}")
    print(f"ANALISIS DE PERSISTENCIA SEMANAL SIGMA - {asset_key} ({start_date} a {end_date})")
    print(f"{'='*70}")

    # 1. Download and Resample Data
    data = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    
    # Weekly resample: Friday Close vs Monday Open
    weekly = data.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna()
    
    # Calculate O2C (Weekly)
    weekly['o2c'] = (weekly['close'] - weekly['open']) / weekly['open']
    
    # 2. Define Sigma Thresholds (Based on agreed values)
    # User said: -2.7% and +3.5%
    upper_sigma = 0.0355  # 3.55% approx
    lower_sigma = -0.0273 # -2.73% approx
    
    # Alternatively, calculate them to be exact for the period if needed
    # but the user explicitly mentioned these values.
    # Let's use the ones calculated by the framework for 2020-2025 which are very close.
    # framework calculated: -2.736% and +3.558%
    
    print(f"Umbrales Sigma Aplicados:")
    print(f"  Upper Sigma (+1sigma): {upper_sigma*100:.2f}%")
    print(f"  Lower Sigma (-1sigma): {lower_sigma*100:.2f}%")
    print(f"Total semanas analizadas: {len(weekly)}")
    print("-" * 40)

    # 3. Identify Extreme Weeks (W0)
    weekly['is_upper_extreme'] = weekly['o2c'] > upper_sigma
    weekly['is_lower_extreme'] = weekly['o2c'] < lower_sigma
    weekly['is_extreme'] = weekly['is_upper_extreme'] | weekly['is_lower_extreme']
    
    # 4. Analyze Lead/Lag (W+1)
    weekly['next_o2c'] = weekly['o2c'].shift(-1)
    
    # Drop the last row as it has no next_o2c
    valid_extremes = weekly.dropna(subset=['next_o2c'])
    
    # --- STATISTICS ---
    
    def get_stats(subset, label):
        count = len(subset)
        if count == 0:
            return None
        
        prob_total = count / len(valid_extremes) * 100
        
        # Next week direction
        pos_next = (subset['next_o2c'] > 0).sum()
        neg_next = (subset['next_o2c'] <= 0).sum()
        
        # Continuation vs Reversal
        # For Upper Extreme: Continuation = Next is Positive, Reversal = Next is Negative
        # For Lower Extreme: Continuation = Next is Negative, Reversal = Next is Positive
        
        if "Upper" in label:
            continuation = pos_next
            reversal = neg_next
        else:
            continuation = neg_next
            reversal = pos_next
            
        avg_next = subset['next_o2c'].mean() * 100
        avg_next_pos = subset[subset['next_o2c'] > 0]['next_o2c'].mean() * 100
        avg_next_neg = subset[subset['next_o2c'] <= 0]['next_o2c'].mean() * 100
        
        return {
            'label': label,
            'count': count,
            'prob_occurence': prob_total,
            'continuation_pct': (continuation / count) * 100,
            'reversal_pct': (reversal / count) * 100,
            'avg_next_ret': avg_next,
            'avg_next_pos': avg_next_pos,
            'avg_next_neg': avg_next_neg
        }

    upper_stats = get_stats(valid_extremes[valid_extremes['is_upper_extreme']], "Upper Extreme (> +3.55%)")
    lower_stats = get_stats(valid_extremes[valid_extremes['is_lower_extreme']], "Lower Extreme (< -2.73%)")
    
    # 5. Output Results
    print(f"\n1. FRECUENCIA DE CIERRES EXTREMOS")
    print("-" * 40)
    for res in [upper_stats, lower_stats]:
        if res:
            print(f"{res['label']}:")
            print(f"  Ocurrencia: {res['count']} semanas ({res['prob_occurence']:.1f}% del tiempo)")
    
    # Total extremes
    total_ext_count = (upper_stats['count'] if upper_stats else 0) + (lower_stats['count'] if lower_stats else 0)
    total_prob = (total_ext_count / len(valid_extremes)) * 100
    print(f"Total Eventos Sigma: {total_ext_count} semanas ({total_prob:.1f}%)")
    
    print(f"\n2. COMPORTAMIENTO DE LA SEMANA SIGUIENTE (W+1)")
    print("-" * 100)
    print(f"{'Escenario':<30} | {'Cont. %':<10} | {'Rev. %':<10} | {'Prom. Total':<12} | {'Si es POS':<12} | {'Si es NEG':<12}")
    print("-" * 100)
    
    for res in [upper_stats, lower_stats]:
        if res:
            print(f"{res['label']:<30} | {res['continuation_pct']:>8.1f}% | {res['reversal_pct']:>8.1f}% | {res['avg_next_ret']:>10.3f}% | {res['avg_next_pos']:>10.3f}% | {res['avg_next_neg']:>10.3f}%")

    print(f"\nCONCLUSIONES:")
    print("-" * 40)
    if upper_stats and upper_stats['continuation_pct'] > 50:
        print(f"* El quiebre Alcista tiende a la CONTINUACION ({upper_stats['continuation_pct']:.1f}%).")
    elif upper_stats:
        print(f"* El quiebre Alcista tiende a la REVERSION ({upper_stats['reversal_pct']:.1f}%).")
        
    if lower_stats and lower_stats['continuation_pct'] > 50:
        print(f"* El quiebre Bajista tiende a la PANICO/CONTINUACION ({lower_stats['continuation_pct']:.1f}%).")
    elif lower_stats:
        print(f"* El quiebre Bajista tiende al REBOTE/REVERSION ({lower_stats['reversal_pct']:.1f}%).")

if __name__ == "__main__":
    analyze_weekly_persistence()
