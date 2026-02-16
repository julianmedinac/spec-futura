import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def audit_monthly_w2_signal_exact(asset_key, asset_name):
    # Use proper keys defined in config/assets.py
    # ASSETS = { 'ES': 'ES=F', 'YM': 'YM=F', 'GC': 'GC=F', 'NQ': 'NQ=F', 'DJI': '^DJI', ... }
    
    print(f"\n{'='*100}")
    print(f"AUDITORIA DEFINITIVA: PATRON W2 > 50% vs < 50% (MENSUAL)")
    print(f"Activo: {asset_key} ({asset_name})")
    print(f"Rango de Fechas: 2000-01-01 a 2026-02-16")
    print(f"{'='*100}")

    loader = DataLoader()
    # Loader handles mapping internally if we pass the KEY (e.g. 'ES', 'YM')
    # Exception: YM might need explicit proxy if YM=F history is short?
    # Let's rely on loader. logic.
    
    # For DJI proxy, use 'DJI' key if available or '^DJI' directly if loader supports raw symbols?
    # Loader.download takes 'asset_key'. 
    
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: 
        print(f"No data for {asset_key}")
        return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    monthly_groups = data.groupby(['year', 'month'])
    results = []
    
    for (year, month), month_data in monthly_groups:
        weeks = month_data['week_of_year'].drop_duplicates().tolist()
        if len(weeks) < 2: continue
        
        # W1 is usually weeks[0], W2 is weeks[1]
        # Edge case: Year transition (Week 52 -> Week 1) is handled by groupby year/month
        # But wait, December has weeks 48, 49.. 52. January has 1, 2...
        # If a week spans across months, it is assigned to the month of the index? 
        # Yes, groupby uses index.month. 
        # But 'week_of_year' might be 52 for Jan 1st if it belongs to previous ISO year.
        # This is fine, we just need the first two chronological weeks in this month's data.
        
        w1_idx = weeks[0]
        w2_idx = weeks[1]
        
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
        
        bull = m_df[m_df['signal'] == 'BULL']
        n_bull = len(bull)
        if n_bull > 0:
            p_green = (bull['green_month'].sum() / n_bull) * 100
            p_high = (bull['new_high'].sum() / n_bull) * 100
            p_low_fail = (bull['new_low'].sum() / n_bull) * 100 
            print(f"{m_name:<5} | {'BULL':<5} | {n_bull:<7} | {p_green:9.1f}%   | {(100-p_green):9.1f}% | {p_high:9.1f}%   | {p_low_fail:9.1f}%")
        else:
            print(f"{m_name:<5} | {'BULL':<5} | {'0':<7} | {'N/A':<12} | {'N/A':<10} | {'N/A':<12} | {'N/A':<12}")

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
    audit_monthly_w2_signal_exact('DJI', 'Dow Jones (Proxy)') # Using DJI key which maps to ^DJI in config
    audit_monthly_w2_signal_exact('GC', 'Gold')
