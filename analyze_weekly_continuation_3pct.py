import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.data_loader import download_asset_data

def analyze_continuation_3pct(asset_key='NQ', start_date='2020-01-01', end_date='2025-12-31'):
    print(f"\n{'='*70}")
    print(f"ANALISIS DE CONTINUACION TRAS CIERRE > +3% - {asset_key}")
    print(f"Periodo: {start_date} a {end_date}")
    print(f"{'='*70}")

    # 1. Data Processing
    data = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    weekly = data.resample('W').agg({'open': 'first', 'close': 'last'}).dropna()
    weekly['o2c'] = (weekly['close'] - weekly['open']) / weekly['open']
    weekly['next_o2c'] = weekly['o2c'].shift(-1)
    
    # Trigger: Weekly Close > 3%
    threshold = 0.03
    trigger_weeks = weekly[weekly['o2c'] > threshold].dropna(subset=['next_o2c'])
    
    total_events = len(trigger_weeks)
    if total_events == 0:
        print("No se encontraron eventos con este criterio.")
        return

    # 2. Results
    pos_count = (trigger_weeks['next_o2c'] > 0).sum()
    neg_count = (trigger_weeks['next_o2c'] <= 0).sum()
    
    prob_continuation = (pos_count / total_events) * 100
    avg_next_ret = trigger_weeks['next_o2c'].mean() * 100
    
    # 3. Output
    print(f"Resultados para Nivel > +3.0%:")
    print(f"  Eventos encontrados:     {total_events}")
    print(f"  Semana siguiente POS:    {pos_count} ({prob_continuation:.1f}%)")
    print(f"  Semana siguiente NEG:    {neg_count} ({100 - prob_continuation:.1f}%)")
    print(f"  Retorno Promedio W+1:    {avg_next_ret:.3f}%")
    print("-" * 40)
    
    # Compare with the previous 3.5%
    threshold_35 = 0.0355
    trigger_35 = weekly[weekly['o2c'] > threshold_35].dropna(subset=['next_o2c'])
    prob_35 = (trigger_35['next_o2c'] > 0).mean() * 100
    
    print(f"Comparativa:")
    print(f"  Nivel > 3.0%: Prob. Continuacion = {prob_continuation:.1f}%")
    print(f"  Nivel > 3.5%: Prob. Continuacion = {prob_35:.1f}%")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_date', type=str, default='2020-01-01')
    parser.add_argument('--end_date', type=str, default='2025-12-31')
    args = parser.parse_args()
    
    analyze_continuation_3pct(start_date=args.start_date, end_date=args.end_date)
