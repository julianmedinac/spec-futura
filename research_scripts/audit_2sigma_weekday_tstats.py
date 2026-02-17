import sys
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def run_2sigma_weekday_audit(start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"AUDITORIA ESTADISTICA (T-STATS): 2-SIGMA WEEKDAY EXTREMES")
    print(f"Periodo: {start_date} a {end_date}")
    print(f"{'='*95}")

    assets_to_load = ['NQ', 'ES', 'YM']
    data_dict = {}
    
    for asset in assets_to_load:
        df = download_asset_data(asset, start_date=start_date, end_date=end_date)
        df['o2c'] = (df['close'] - df['open']) / df['open']
        df['next_o2c'] = df['o2c'].shift(-1)
        df['weekday'] = df.index.day_name()
        
        std_val = df['o2c'].std()
        mean_val = df['o2c'].mean()
        
        data_dict[asset] = {
            'df': df,
            'upper_2s': mean_val + (2.0 * std_val),
            'lower_2s': mean_val - (2.0 * std_val)
        }

    # Define the high-conviction 2-sigma weekday patterns found in previous analysis
    patterns = [
        {'name': 'Tue NQ Drive(2s) -> Wed Rev', 'asset': 'NQ', 'day': 'Tuesday',   'cond': 'upper'},
        {'name': 'Fri ES Panic(2s) -> Mon Reb', 'asset': 'ES', 'day': 'Friday',    'cond': 'lower'},
        {'name': 'Fri YM Panic(2s) -> Mon Reb', 'asset': 'YM', 'day': 'Friday',    'cond': 'lower'},
        {'name': 'Mon YM Panic(2s) -> Tue Reb', 'asset': 'YM', 'day': 'Monday',    'cond': 'lower'},
        {'name': 'Wed YM Panic(2s) -> Thu Reb', 'asset': 'YM', 'day': 'Wednesday', 'cond': 'lower'}
    ]

    results = []
    
    for p in patterns:
        asset_info = data_dict[p['asset']]
        df = asset_info['df']
        threshold = asset_info['upper_2s'] if p['cond'] == 'upper' else asset_info['lower_2s']
        
        if p['cond'] == 'lower':
            subset = df[(df['weekday'] == p['day']) & (df['o2c'] < threshold)].dropna(subset=['next_o2c'])
        else:
            subset = df[(df['weekday'] == p['day']) & (df['o2c'] > threshold)].dropna(subset=['next_o2c'])
            
        sample = subset['next_o2c']
        n = len(sample)
        
        if n > 1:
            mean_ret = sample.mean() * 100
            t_stat, p_value = stats.ttest_1samp(sample, 0)
            
            results.append({
                'Pattern': p['name'],
                'N': n,
                'Avg Ret': f"{mean_ret:+.3f}%",
                'T-Stat': f"{t_stat:.2f}",
                'P-Value': f"{p_value:.4f}",
                'Significant': "YES (95%)" if p_value < 0.05 else ("YES (90%)" if p_value < 0.10 else "NO")
            })

    report = pd.DataFrame(results)
    print("\nRESULTADOS T-STATS (EXTREMOS FILTRADOS POR DIA):")
    print("-" * 110)
    print(report.to_string(index=False))

if __name__ == "__main__":
    run_2sigma_weekday_audit()
