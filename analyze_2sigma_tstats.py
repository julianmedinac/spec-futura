import sys
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def run_2sigma_tstat_analysis(start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"AUDITORIA ESTADISTICA (T-STATS): 2-SIGMA DAILY ALPHA PATTERNS")
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
            'upper_2s': mean_val + (2.0 * std_val),
            'lower_2s': mean_val - (2.0 * std_val)
        }

    # Define the patterns to test
    patterns = [
        {'name': 'NQ Panic 2s -> Rebound',  'asset': 'NQ', 'cond': 'lower_2s'},
        {'name': 'ES Panic 2s -> Rebound',  'asset': 'ES', 'cond': 'lower_2s'},
        {'name': 'YM Panic 2s -> Rebound',  'asset': 'YM', 'cond': 'lower_2s'},
        {'name': 'NQ Drive 2s -> Reversal', 'asset': 'NQ', 'cond': 'upper_2s'}
    ]

    results = []
    
    for p in patterns:
        asset_info = data_dict[p['asset']]
        df = asset_info['df']
        threshold = asset_info[p['cond']]
        
        if 'lower' in p['cond']:
            subset = df[df['o2c'] < threshold].dropna(subset=['next_o2c'])
        else:
            subset = df[df['o2c'] > threshold].dropna(subset=['next_o2c'])
            
        sample = subset['next_o2c']
        n = len(sample)
        
        if n > 0:
            mean_ret = sample.mean() * 100
            prob_success = ((sample > 0).mean() * 100) if 'lower' in p['cond'] else ((sample < 0).mean() * 100)
            
            if n > 1:
                t_stat, p_value = stats.ttest_1samp(sample, 0)
                sig = "YES" if p_value < 0.05 else "NO"
            else:
                t_stat, p_value, sig = 0, 1, "N/A"
            
            results.append({
                'Pattern': p['name'],
                'N': n,
                'Prob %': f"{prob_success:.1f}%",
                'Avg Ret': f"{mean_ret:+.3f}%",
                'T-Stat': f"{t_stat:.2f}",
                'P-Value': f"{p_value:.4f}",
                'Sig': sig
            })

    report = pd.DataFrame(results)
    print("\nRESULTADOS 2-SIGMA (EVENTOS EXTREMOS):")
    print("-" * 95)
    print(report.to_string(index=False))

if __name__ == "__main__":
    run_2sigma_tstat_analysis()
