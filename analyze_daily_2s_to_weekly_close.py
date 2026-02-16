import sys
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def analyze_daily_extreme_to_weekly_close(asset_key, start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"ANALISIS: IMPACTO DE DIA 2-SIGMA EN CIERRE SEMANAL - {asset_key}")
    print(f"Periodo: {start_date} a {end_date}")
    print(f"{'='*95}")

    # 1. Download Daily Data
    df = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    if df.empty: return

    # 2. Daily O2C and Week Identifiers
    df['o2c_daily'] = (df['close'] - df['open']) / df['open']
    df['weekday'] = df.index.day_name()
    df['year_week'] = df.index.to_period('W')
    
    # Calculate Weekly O2C
    weekly_data = []
    for name, group in df.groupby('year_week'):
        if len(group) < 2: continue
        w_open = group['open'].iloc[0]
        w_close = group['close'].iloc[-1]
        w_o2c = (w_close - w_open) / w_open
        
        # Mark if any day in this week had a 2-sigma move
        std_daily = df['o2c_daily'].std()
        mean_daily = df['o2c_daily'].mean()
        upper_2s = mean_daily + (2.0 * std_daily)
        lower_2s = mean_daily - (2.0 * std_daily)
        
        # Check for specific day triggers
        for _, day_row in group.iterrows():
            trigger = None
            if day_row['o2c_daily'] > upper_2s: trigger = 'DRIVE_2S'
            elif day_row['o2c_daily'] < lower_2s: trigger = 'PANIC_2S'
            
            if trigger:
                weekly_data.append({
                    'week': name,
                    'trigger_day': day_row['weekday'],
                    'trigger_type': trigger,
                    'weekly_o2c': w_o2c
                })

    results_df = pd.DataFrame(weekly_data)
    if results_df.empty:
        print("No se encontraron eventos 2-sigma.")
        return

    # 3. Aggregate Results
    summary = []
    for (day, t_type), group in results_df.groupby(['trigger_day', 'trigger_type']):
        n = len(group)
        if n < 3: continue
        
        prob_bull_week = (group['weekly_o2c'] > 0).mean() * 100
        avg_weekly_ret = group['weekly_o2c'].mean() * 100
        
        # T-test for weekly return
        t_stat, p_val = stats.ttest_1samp(group['weekly_o2c'], 0)
        
        summary.append({
            'Trigger Day': day,
            'Type': t_type,
            'N': n,
            'P(Green Week)': f"{prob_bull_week:.1f}%",
            'Avg Week Ret': f"{avg_weekly_ret:+.2f}%",
            'T-Stat': f"{t_stat:.2f}",
            'Significant': "YES" if p_val < 0.05 else "NO"
        })

    print("\nIMPACTO EN EL CIERRE DE LA SEMANA (W1 O2C):")
    print("-" * 95)
    report = pd.DataFrame(summary).sort_values(by=['Trigger Day', 'Type'])
    print(report.to_string(index=False))

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        analyze_daily_extreme_to_weekly_close(asset)
