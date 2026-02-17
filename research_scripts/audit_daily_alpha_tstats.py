import sys
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def run_t_stats_analysis(start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"AUDITORIA ESTADISTICA (T-STATS): DAILY ALPHA PATTERNS")
    print(f"Periodo: {start_date} a {end_date}")
    print(f"{'='*95}")

    assets_to_load = ['NQ', 'ES', 'YM']
    data_dict = {}
    
    for asset in assets_to_load:
        df = download_asset_data(asset, start_date=start_date, end_date=end_date)
        df['o2c'] = (df['close'] - df['open']) / df['open']
        df['next_o2c'] = df['o2c'].shift(-1)
        df['weekday'] = df.index.day_name()
        
        # Calculate Global Sigma for the period
        std_val = df['o2c'].std()
        mean_val = df['o2c'].mean()
        
        data_dict[asset] = {
            'df': df,
            'upper': mean_val + std_val,
            'lower': mean_val - std_val
        }

    # Define the patterns to test (from our Daily Alpha Matrix)
    patterns = [
        {'name': 'Tuesday NQ Panic -> Wed Rebound',  'asset': 'NQ', 'day': 'Tuesday',   'cond': 'lower'},
        {'name': 'Wednesday YM Panic -> Thu Rebound', 'asset': 'YM', 'day': 'Wednesday', 'cond': 'lower'},
        {'name': 'Wednesday ES Panic -> Thu Rebound', 'asset': 'ES', 'day': 'Wednesday', 'cond': 'lower'},
        {'name': 'Thursday NQ Drive -> Fri Reversion','asset': 'NQ', 'day': 'Thursday',  'cond': 'upper'},
        {'name': 'Friday YM Panic -> Mon Rebound',    'asset': 'YM', 'day': 'Friday',    'cond': 'lower'},
        {'name': 'Friday ES Panic -> Mon Rebound',    'asset': 'ES', 'day': 'Friday',    'cond': 'lower'},
        {'name': 'Friday NQ Drive -> Mon Continuation','asset': 'NQ', 'day': 'Friday',    'cond': 'upper'}
    ]

    results = []
    
    for p in patterns:
        asset_info = data_dict[p['asset']]
        df = asset_info['df']
        threshold = asset_info[p['cond']]
        
        # Filter the trigger days
        if p['cond'] == 'lower':
            subset = df[(df['weekday'] == p['day']) & (df['o2c'] < threshold)].dropna(subset=['next_o2c'])
        else:
            subset = df[(df['weekday'] == p['day']) & (df['o2c'] > threshold)].dropna(subset=['next_o2c'])
            
        sample = subset['next_o2c']
        n = len(sample)
        
        if n > 1:
            mean_ret = sample.mean() * 100
            # T-test against null hypothesis (mean = 0)
            t_stat, p_value = stats.ttest_1samp(sample, 0)
            
            # Confidence Level
            is_significant = p_value < 0.05
            is_strong = p_value < 0.01
            
            results.append({
                'Pattern': p['name'],
                'N': n,
                'Avg Ret': f"{mean_ret:+.3f}%",
                'T-Stat': f"{t_stat:.2f}",
                'P-Value': f"{p_value:.4f}",
                'Significant': "YES (95%)" if is_significant else "NO",
                'Quality': "GOLD" if is_strong else ("SILVER" if is_significant else "NOISE")
            })

    report = pd.DataFrame(results)
    print("\nTABLA DE SIGNIFICANCIA ESTADISTICA:")
    print("-" * 110)
    print(report.to_string(index=False))
    
    print("\nNOTAS DE AUDITORIA:")
    print("[*] P-Value < 0.05: Hay menos del 5% de probabilidad de que el resultado sea azar.")
    print("[*] T-Stat > 2.0: Indica que el retorno promedio es significativamente mayor que la dispersion (Ruido).")
    print("[*] GOLD/SILVER: Patrones robustos para ejecucion sistemática.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_date', type=str, default='2015-01-01')
    parser.add_argument('--end_date', type=str, default='2025-12-31')
    args = parser.parse_args()
    
    run_t_stats_analysis(start_date=args.start_date, end_date=args.end_date)
