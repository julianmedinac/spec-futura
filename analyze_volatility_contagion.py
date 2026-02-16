import sys
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def analyze_volatility_contagion(asset_key, start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"ANALISIS: CONTAGIO DE VOLATILIDAD (DAILY 1s -> WEEKLY 1s) - {asset_key}")
    print(f"Periodo: {start_date} a {end_date}")
    print(f"{'='*95}")

    # 1. Download Daily Data
    df = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    if df.empty: return

    # 2. Daily Metrics
    df['o2c_daily'] = (df['close'] - df['open']) / df['open']
    std_daily = df['o2c_daily'].std()
    df['year_week'] = df.index.to_period('W')
    
    # 3. Weekly Metrics
    weekly_stats = []
    for name, group in df.groupby('year_week'):
        if len(group) < 2: continue
        w_open = group['open'].iloc[0]
        w_close = group['close'].iloc[-1]
        w_o2c = (w_close - w_open) / w_open
        
        # Check if any day in the week breached 1-sigma daily (absolute)
        daily_breach = group['o2c_daily'].abs().max() > std_daily
        
        # Check if daily breach was BULL or BEAR
        bull_breach = group['o2c_daily'].max() > std_daily
        bear_breach = group['o2c_daily'].min() < -std_daily
        
        weekly_stats.append({
            'year_week': name,
            'w_o2c': w_o2c,
            'has_daily_breach': daily_breach,
            'bull_daily_breach': bull_breach,
            'bear_daily_breach': bear_breach
        })

    weekly_df = pd.DataFrame(weekly_stats)
    std_weekly = weekly_df['w_o2c'].std()
    
    # Thresholds
    print(f"[*] Daily 1-Sigma: {std_daily*100:.2f}%")
    print(f"[*] Weekly 1-Sigma: {std_weekly*100:.2f}%")
    print("-" * 50)

    # 4. Analysis: Probability of Weekly Breach given Daily Breach
    # Case A: Bullish Contagion
    bull_weeks = weekly_df[weekly_df['bull_daily_breach']]
    n_bull = len(bull_weeks)
    prob_bull_contagion = (bull_weeks['w_o2c'] > std_weekly).mean() * 100
    
    # Case B: Bearish Contagion
    bear_weeks = weekly_df[weekly_df['bear_daily_breach']]
    n_bear = len(bear_weeks)
    prob_bear_contagion = (bear_weeks['w_o2c'] < -std_weekly).mean() * 100
    
    # Baseline for comparison (Random probability of weekly sigma)
    baseline_bull = (weekly_df['w_o2c'] > std_weekly).mean() * 100
    baseline_bear = (weekly_df['w_o2c'] < -std_weekly).mean() * 100

    print(f"BULL CONTAGION: Daily +1s -> Weekly +1s")
    print(f"  - Total weeks with Daily +1s: {n_bull}")
    print(f"  - Prob(Weekly +1s | Daily +1s): {prob_bull_contagion:.1f}% (vs Baseline: {baseline_bull:.1f}%)")
    print(f"  - Edge: {prob_bull_contagion - baseline_bull:+.1f}%")
    
    print(f"\nBEAR CONTAGION: Daily -1s -> Weekly -1s")
    print(f"  - Total weeks with Daily -1s: {n_bear}")
    print(f"  - Prob(Weekly -1s | Daily -1s): {prob_bear_contagion:.1f}% (vs Baseline: {baseline_bear:.1f}%)")
    print(f"  - Edge: {prob_bear_contagion - baseline_bear:+.1f}%")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        analyze_volatility_contagion(asset)
