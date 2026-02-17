import sys
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def audit_volatility_contagion_tstats(asset_key, start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"STRICT AUDIT: T-STATS FOR VOLATILITY CONTAGION - {asset_key}")
    print(f"Periodo: {start_date} a {end_date}")
    print(f"{'='*95}")

    # 1. Data Loading
    df = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    if df.empty: return

    # 2. Daily & Weekly Sigma Calibration
    df['o2c_daily'] = (df['close'] - df['open']) / df['open']
    std_daily = df['o2c_daily'].std()
    df['year_week'] = df.index.to_period('W')
    
    weekly_stats = []
    for name, group in df.groupby('year_week'):
        if len(group) < 2: continue
        w_open = group['open'].iloc[0]
        w_close = group['close'].iloc[-1]
        w_o2c = (w_close - w_open) / w_open
        
        # Binary triggers
        bull_breach = group['o2c_daily'].max() > std_daily
        bear_breach = group['o2c_daily'].min() < -std_daily
        
        weekly_stats.append({
            'year_week': name,
            'w_o2c': w_o2c,
            'bull_daily_breach': bull_breach,
            'bear_daily_breach': bear_breach
        })

    weekly_df = pd.DataFrame(weekly_stats)
    std_weekly = weekly_df['w_o2c'].std()
    
    # 3. T-Stat Audit for BULL CONTAGION
    bull_sample = weekly_df[weekly_df['bull_daily_breach']]['w_o2c']
    if not bull_sample.empty:
        # We test if the returns in weeks with a bull daily breach are significantly > 0
        t_stat_bull, p_val_bull = stats.ttest_1samp(bull_sample, 0)
        n_bull = len(bull_sample)
        prob_target = (bull_sample > std_weekly).mean() * 100
        avg_ret = bull_sample.mean() * 100
        
        print(f"AUDIT BULL (Daily +1s -> Weekly Close):")
        print(f"  - Observations (N): {n_bull}")
        print(f"  - Prob(Weekly +1s): {prob_target:.1f}%")
        print(f"  - Avg Weekly Return: {avg_ret:+.3f}%")
        print(f"  - T-Statistic: {t_stat_bull:.2f}")
        print(f"  - P-Value: {p_val_bull:.4f}")
        print(f"  - Result: {'SIGNIFICANT' if p_val_bull < 0.05 else 'NOISE'}")

    # 4. T-Stat Audit for BEAR CONTAGION
    bear_sample = weekly_df[weekly_df['bear_daily_breach']]['w_o2c']
    if not bear_sample.empty:
        t_stat_bear, p_val_bear = stats.ttest_1samp(bear_sample, 0)
        n_bear = len(bear_sample)
        prob_target = (bear_sample < -std_weekly).mean() * 100
        avg_ret = bear_sample.mean() * 100
        
        print(f"\nAUDIT BEAR (Daily -1s -> Weekly Close):")
        print(f"  - Observations (N): {n_bear}")
        print(f"  - Prob(Weekly -1s): {prob_target:.1f}%")
        print(f"  - Avg Weekly Return: {avg_ret:+.3f}%")
        print(f"  - T-Statistic: {t_stat_bear:.2f}")
        print(f"  - P-Value: {p_val_bear:.4f}")
        print(f"  - Result: {'SIGNIFICANT' if p_val_bear < 0.05 else 'NOISE'}")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        audit_volatility_contagion_tstats(asset)
