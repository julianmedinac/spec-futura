import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def run_comprehensive_analysis(asset_key, start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*90}")
    print(f"ANALISIS DOR ESTRUCTURAL: {asset_key} ({start_date} a {end_date})")
    print(f"{'='*90}")

    # 1. Download and Resample
    data = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    weekly = data.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna()
    
    weekly['o2c'] = (weekly['close'] - weekly['open']) / weekly['open']
    weekly['next_o2c'] = weekly['o2c'].shift(-1)
    
    # 2. Dynamic Sigma Calculation (15-25 period)
    mean = weekly['o2c'].mean()
    std = weekly['o2c'].std()
    upper_threshold = mean + std
    lower_threshold = mean - std
    
    print(f"Umbrales Sigma (+/- 1std):")
    print(f"  Media:  {mean*100:+.3f}% | Std Dev: {std*100:.3f}%")
    print(f"  Upper:  {upper_threshold*100:+.3f}%")
    print(f"  Lower:  {lower_threshold*100:+.3f}%")
    print("-" * 40)

    valid = weekly.dropna(subset=['next_o2c']).copy()
    
    # --- PERSISTENCE (W+1) ---
    upper_events = valid[valid['o2c'] > upper_threshold]
    lower_events = valid[valid['o2c'] < lower_threshold]
    
    u_count = len(upper_events)
    l_count = len(lower_events)
    
    u_cont = (upper_events['next_o2c'] > 0).mean() * 100 if u_count > 0 else 0
    l_rev = (lower_events['next_o2c'] > 0).mean() * 100 if l_count > 0 else 0
    
    # --- RANGE EXPANSION (W1+W2) ---
    def calc_expansion(trigger_weeks, full_weekly):
        exp_results = []
        for idx in trigger_weeks.index:
            pos = full_weekly.index.get_loc(idx)
            if pos + 1 < len(full_weekly):
                w1 = full_weekly.iloc[pos]
                w2 = full_weekly.iloc[pos+1]
                c_h = max(w1['high'], w2['high'])
                c_l = min(w1['low'], w2['low'])
                comb_range = (c_h - c_l) / w1['open'] * 100
                exp_results.append(comb_range)
        return np.mean(exp_results) if exp_results else 0

    u_range_exp = calc_expansion(upper_events, weekly)
    l_range_exp = calc_expansion(lower_events, weekly)
    
    # Output Table
    print(f"\nRESULTADOS DE ALPHA:")
    print("-" * 80)
    print(f"{'Escenario':<25} | {'Casos':<8} | {'Prob. Sig. Sem':<18} | {'Rango W1+W2 Avg':<15}")
    print("-" * 80)
    print(f"{'CLOSE > +1 Sigma':<25} | {u_count:<8} | {u_cont:>15.1f}% (C) | {u_range_exp:>13.2f}%")
    print(f"{'CLOSE < -1 Sigma':<25} | {l_count:<8} | {l_rev:>15.1f}% (R) | {l_range_exp:>13.2f}%")
    print(f"\n(C) = Continuacion (Siguiente semana alcista)")
    print(f"(R) = Reversion (Siguiente semana alcista/rebote)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_date', type=str, default='2015-01-01')
    parser.add_argument('--end_date', type=str, default='2025-12-31')
    args = parser.parse_args()
    
    for asset in ['ES', 'GC', 'YM']:
        run_comprehensive_analysis(asset, start_date=args.start_date, end_date=args.end_date)
