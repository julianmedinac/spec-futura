import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def analyze_sigma_rejection(asset_key='NQ', start_date='2020-01-01', end_date='2025-12-31'):
    print(f"\n{'='*90}")
    print(f"ANALISIS DE RECHAZO SIGMA (LA REGLA DE LA MECHA) - {asset_key}")
    print(f"Periodo: {start_date} a {end_date}")
    print(f"{'='*90}")

    # 1. Download and Resample
    data = download_asset_data(asset_key, start_date=start_date, end_date=end_date)
    weekly = data.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna()
    
    # 2. Calculate O2C based components
    weekly['o2c_high'] = (weekly['high'] - weekly['open']) / weekly['open']
    weekly['o2c_low'] = (weekly['low'] - weekly['open']) / weekly['open']
    weekly['o2c_close'] = (weekly['close'] - weekly['open']) / weekly['open']
    
    # Calculate Sigma for the period
    # We use these to define the "Stretch" and the "Failure"
    mean_close = weekly['o2c_close'].mean()
    std_close = weekly['o2c_close'].std()
    
    # Thresholds
    stretch_sigma = 1.5
    failure_sigma = 0.5
    
    upper_stretch = mean_close + (stretch_sigma * std_close)
    upper_failure = mean_close + (failure_sigma * std_close)
    
    lower_stretch = mean_close - (stretch_sigma * std_close)
    lower_failure = mean_close - (failure_sigma * std_close)
    
    print(f"Configuracion del Patron:")
    print(f"  Ataque Sigma (1.5s):   {upper_stretch*100:+.2f}% (UP) | {lower_stretch*100:+.2f}% (LO)")
    print(f"  Falla de Cierre (0.5s): {upper_failure*100:+.2f}% (UP) | {lower_failure*100:+.2f}% (LO)")
    print("-" * 50)

    # 3. Identify Patterns
    # Bullish Trap: Attacked high sigma but closed low
    weekly['is_bull_trap'] = (weekly['o2c_high'] >= upper_stretch) & (weekly['o2c_close'] <= upper_failure)
    
    # Bearish Trap: Attacked low sigma but closed high
    weekly['is_bear_trap'] = (weekly['o2c_low'] <= lower_stretch) & (weekly['o2c_close'] >= lower_failure)
    
    # 4. Analyze Next Week
    weekly['next_o2c'] = weekly['o2c_close'].shift(-1)
    valid = weekly.dropna(subset=['next_o2c'])
    
    def get_trap_stats(subset, trap_type):
        count = len(subset)
        if count == 0: return None
        
        if trap_type == "BULL":
            # Success = Market went down next week
            success_count = (subset['next_o2c'] < 0).sum()
            avg_ret = subset['next_o2c'].mean() * 100
        else:
            # Success = Market went up next week
            success_count = (subset['next_o2c'] > 0).sum()
            avg_ret = subset['next_o2c'].mean() * 100
            
        return {
            'count': count,
            'prob_success': (success_count / count) * 100,
            'avg_next_ret': avg_ret
        }

    bull_stats = get_trap_stats(valid[valid['is_bull_trap']], "BULL")
    bear_stats = get_trap_stats(valid[valid['is_bear_trap']], "BEAR")
    
    # 5. Output
    print(f"\nRESULTADOS - BULL TRAP (Falla en el High)")
    if bull_stats:
        print(f"  Eventos encontrados: {bull_stats['count']}")
        print(f"  Prob. Reversion W+1:  {bull_stats['prob_success']:.1f}%")
        print(f"  Retorno Promedio W+1: {bull_stats['avg_next_ret']:+.3f}%")
    else:
        print("  No se encontraron eventos.")

    print(f"\nRESULTADOS - BEAR TRAP (Falla en el Low)")
    if bear_stats:
        print(f"  Eventos encontrados: {bear_stats['count']}")
        print(f"  Prob. Reversion W+1:  {bear_stats['prob_success']:.1f}%")
        print(f"  Retorno Promedio W+1: {bear_stats['avg_next_ret']:+.3f}%")
    else:
        print("  No se encontraron eventos.")

    # Show detail of cases
    if bull_stats and bull_stats['count'] > 0:
        print(f"\nDETALLE BULL TRAPS:")
        print(weekly[weekly['is_bull_trap']][['o2c_high', 'o2c_close', 'next_o2c']].tail(5))

    if bear_stats and bear_stats['count'] > 0:
        print(f"\nDETALLE BEAR TRAPS:")
        print(weekly[weekly['is_bear_trap']][['o2c_low', 'o2c_close', 'next_o2c']].tail(5))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_date', type=str, default='2020-01-01')
    parser.add_argument('--end_date', type=str, default='2025-12-31')
    args = parser.parse_args()

    for asset in ['NQ', 'ES', 'YM']:
        analyze_sigma_rejection(asset, start_date=args.start_date, end_date=args.end_date)
