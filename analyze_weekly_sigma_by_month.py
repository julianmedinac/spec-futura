import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.data_loader import download_asset_data

def analyze_weekly_sigma_by_month(asset_key='NQ', start_date='2020-01-01', end_date='2025-12-31'):
    print(f"\n{'='*90}")
    print(f"ANALISIS DE PERSISTENCIA SEMANAL POR MES - {asset_key} ({start_date} a {end_date})")
    print(f"Umbrales: Upper > +3.55% | Lower < -2.73%")
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
    weekly['month'] = weekly.index.month
    
    # Thresholds
    upper_sigma = 0.0355
    lower_sigma = -0.0273
    
    # 2. Identify Extremes
    weekly['is_upper'] = weekly['o2c'] > upper_sigma
    weekly['is_lower'] = weekly['o2c'] < lower_sigma
    weekly['next_o2c'] = weekly['o2c'].shift(-1)
    
    valid = weekly.dropna(subset=['next_o2c']).copy()
    
    # 3. Process by Month
    month_names = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    monthly_stats = []
    
    for m in range(1, 13):
        m_data = valid[valid['month'] == m]
        total_weeks = len(m_data)
        
        if total_weeks == 0:
            continue
            
        # Upper Extremes
        u_ext = m_data[m_data['is_upper']]
        u_count = len(u_ext)
        u_prob = (u_count / total_weeks) * 100 if total_weeks > 0 else 0
        u_cont = (u_ext['next_o2c'] > 0).mean() * 100 if u_count > 0 else 0
        
        # Lower Extremes
        l_ext = m_data[m_data['is_lower']]
        l_count = len(l_ext)
        l_prob = (l_count / total_weeks) * 100 if total_weeks > 0 else 0
        l_rev = (l_ext['next_o2c'] > 0).mean() * 100 if l_count > 0 else 0
        
        monthly_stats.append({
            'Mes': month_names[m],
            'Semanas': total_weeks,
            'Freq Upper %': u_prob,
            'Cont. Upper %': u_cont,
            'Freq Lower %': l_prob,
            'Rev. Lower %': l_rev
        })
    
    df_stats = pd.DataFrame(monthly_stats)
    
    # 4. Display Results
    print(f"\nESTADISTICAS POR MES:")
    print("-" * 100)
    print(f"{'Mes':<12} | {'Semanas':<8} | {'% Freq UP':<10} | {'% Cont UP':<10} | {'% Freq LO':<10} | {'% Rev LO':<10}")
    print("-" * 100)
    
    for _, r in df_stats.iterrows():
        print(f"{r['Mes']:<12} | {r['Semanas']:<8.0f} | {r['Freq Upper %']:>9.1f}% | {r['Cont. Upper %']:>9.1f}% | {r['Freq Lower %']:>9.1f}% | {r['Rev. Lower %']:>9.1f}%")

    print(f"\nNOTAS:")
    print(f"* 'Cont. Upper %': Probabilidad de que la semana siguiente sea POSITIVA tras un cierre > +3.55%")
    print(f"* 'Rev. Lower %': Probabilidad de que la semana siguiente sea POSITIVA (Rebote) tras un cierre < -2.73%")

if __name__ == "__main__":
    analyze_weekly_sigma_by_month()
