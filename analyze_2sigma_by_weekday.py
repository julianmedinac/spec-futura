import sys
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def analyze_2sigma_by_weekday(asset_key, start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"ANALISIS 2-SIGMA POR DIA DE LA SEMANA: {asset_key} ({start_date} a {end_date})")
    print(f"{'='*95}")

    # 1. Download Data
    df = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    if df.empty: return

    # 2. Daily O2C and Weekday
    df['o2c'] = (df['close'] - df['open']) / df['open']
    df['next_o2c'] = df['o2c'].shift(-1)
    df['weekday'] = df.index.day_name()
    
    # 3. Global Sigma Levels
    std_o2c = df['o2c'].std()
    mean_o2c = df['o2c'].mean()
    upper_2s = mean_val = mean_o2c + (2.0 * std_o2c)
    lower_2s = mean_val = mean_o2c - (2.0 * std_o2c)
    
    print(f"Thresholds 2-Sigma: {lower_2s*100:.2f}% / {upper_2s*100:.2f}%")
    
    # 4. Weekdays
    all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    results = []
    
    for day in all_days:
        subset = df[df['weekday'] == day].dropna(subset=['next_o2c']).copy()
        
        # Upper 2s (Climax)
        u_events = subset[subset['o2c'] > upper_2s]
        u_n = len(u_events)
        u_rev = (u_events['next_o2c'] < 0).mean() * 100 if u_n > 0 else 0
        u_avg = u_events['next_o2c'].mean() * 100 if u_n > 0 else 0
        
        # Lower 2s (Capitulation)
        l_events = subset[subset['o2c'] < lower_2s]
        l_n = len(l_events)
        l_rev = (l_events['next_o2c'] > 0).mean() * 100 if l_n > 0 else 0
        l_avg = l_events['next_o2c'].mean() * 100 if l_n > 0 else 0
        
        results.append({
            'Day': day,
            'Climax N': u_n,
            'P(Rev) Bulls': f"{u_rev:.1f}%",
            'Avg Bull $D+1$': f"{u_avg:+.3f}%",
            'Panic N': l_n,
            'P(Rev) Bears': f"{l_rev:.1f}%",
            'Avg Bear $D+1$': f"{l_avg:+.3f}%"
        })

    report = pd.DataFrame(results)
    print("\nRESUMEN 2nd-DEV POR DIA:")
    print("-" * 95)
    print(report.to_string(index=False))

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        analyze_2sigma_by_weekday(asset)
