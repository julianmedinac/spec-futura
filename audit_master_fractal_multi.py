import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np
import sys

# Define assets to audit: ES (S&P), YM (Dow Jones/DJI), GC (Gold)
ASSETS = {
    'ES': 'S&P 500 Futures',
    'YM': 'Dow Jones Futures (Using ^DJI Proxy)', # ^DJI is closest long-term proxy
    'GC': 'Gold Futures'
}

# Fix YM symbol: Yahoo uses YM=F but history might be short. 
# We'll try YM=F, fallback to ^DJI if needed?
# Let's stick to config conventions. YM usually maps to YM=F.
# Wait, user said "YM". My data loader might need mapping.
# Checking assets.py... but I can just use the yahoo symbol directly.
# ES=F, YM=F, GC=F.

def audit_monthly_w2_signal_exact(asset_key, asset_name):
    print(f"\n{'='*100}")
    print(f"AUDITORIA DEFINITIVA: PATRON W2 > 50% vs < 50% (MENSUAL)")
    print(f"Activo: {asset_key} ({asset_name})")
    print(f"Rango de Fechas: 2000-01-01 a 2026-02-16")
    print(f"{'='*100}")
    
    symbol = asset_key
    if asset_key == 'YM': symbol = 'YM=F'
    if asset_key == 'ES': symbol = 'ES=F'
    if asset_key == 'GC': symbol = 'GC=F'

    # Fallback for YM if short history: Using ^DJI for better long term context
    if asset_key == 'YM':
        print("Using ^DJI as proxy for long-term Dow Jones history...")
        symbol = '^DJI'

    loader = DataLoader()
    data = loader.download(symbol, start_date='2000-01-01')
    if data.empty: 
        print(f"No data for {symbol}")
        return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    monthly_groups = data.groupby(['year', 'month'])
    results = []
    
    for (year, month), month_data in monthly_groups:
        weeks = month_data['week_of_year'].drop_duplicates().tolist()
        if len(weeks) < 2: continue
        
        w1_idx, w2_idx = weeks[0], weeks[1]
        w1_data = month_data[month_data['week_of_year'] == w1_idx]
        w2_data = month_data[month_data['week_of_year'] == w2_idx]
        
        if w1_data.empty or w2_data.empty: continue
        
        w2_end_time = w2_data.index.max()
        pre_signal_data = month_data[month_data.index <= w2_end_time]
        
        range_high = pre_signal_data['high'].max()
        range_low = pre_signal_data['low'].min()
        rng = range_high - range_low
        if rng == 0: continue
            
        midpoint = range_low + (rng * 0.5)
        w2_close = w2_data.iloc[-1]['close']
        signal_type = 'BULL' if w2_close > midpoint else 'BEAR'
        
        post_signal_data = month_data[month_data.index > w2_end_time]
        made_new_high = False
        made_new_low = False
        
        if not post_signal_data.empty:
            rest_high = post_signal_data['high'].max()
            rest_low = post_signal_data['low'].min()
            made_new_high = rest_high > range_high
            made_new_low = rest_low < range_low
            
        m_open = month_data.iloc[0]['open']
        m_close = month_data.iloc[-1]['close']
        is_green_month = m_close > m_open
        
        results.append({
            'month': month,
            'signal': signal_type,
            'green_month': is_green_month,
            'new_high': made_new_high,
            'new_low': made_new_low
        })
        
    df = pd.DataFrame(results)
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    print(f"{'MES':<5} | {'SENAL':<5} | {'SAMPLES':<7} | {'PROB GREEN':<12} | {'PROB RED':<10} | {'PROB NEW HI':<12} | {'PROB NEW LO':<12}")
    print("-" * 90)
    
    for i, m_name in enumerate(months):
        m = i + 1
        m_df = df[df['month'] == m]
        
        # BULL STATS
        bull = m_df[m_df['signal'] == 'BULL']
        n_bull = len(bull)
        if n_bull > 0:
            p_green = (bull['green_month'].sum() / n_bull) * 100
            p_high = (bull['new_high'].sum() / n_bull) * 100
            p_low_fail = (bull['new_low'].sum() / n_bull) * 100 
            print(f"{m_name:<5} | {'BULL':<5} | {n_bull:<7} | {p_green:9.1f}%   | {(100-p_green):9.1f}% | {p_high:9.1f}%   | {p_low_fail:9.1f}%")
        else:
            print(f"{m_name:<5} | {'BULL':<5} | {'0':<7} | {'N/A':<12} | {'N/A':<10} | {'N/A':<12} | {'N/A':<12}")

        # BEAR STATS
        bear = m_df[m_df['signal'] == 'BEAR']
        n_bear = len(bear)
        if n_bear > 0:
            p_red = ((n_bear - bear['green_month'].sum()) / n_bear) * 100
            p_low = (bear['new_low'].sum() / n_bear) * 100
            p_high_fail = (bear['new_high'].sum() / n_bear) * 100
            print(f"{'     ':<5} | {'BEAR':<5} | {n_bear:<7} | {(100-p_red):9.1f}%   | {p_red:9.1f}% | {p_high_fail:9.1f}%   | {p_low:9.1f}%")
            print("-" * 90)
        else:
             print(f"{'     ':<5} | {'BEAR':<5} | {'0':<7} | {'N/A':<12} | {'N/A':<10} | {'N/A':<12} | {'N/A':<12}")
             print("-" * 90)

if __name__ == "__main__":
    audit_monthly_w2_signal_exact('ES', 'S&P 500')
    audit_monthly_w2_signal_exact('YM', 'Dow Jones')
    audit_monthly_w2_signal_exact('GC', 'Gold')
