import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def analyze_sigma_by_weekday(asset_key, start_date='2015-01-01', end_date='2025-12-31'):
    print(f"\n{'='*95}")
    print(f"ANALISIS SIGMA POR DIA DE LA SEMANA: {asset_key} ({start_date} a {end_date})")
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
    upper_threshold = mean_o2c + std_o2c
    lower_threshold = mean_o2c - std_o2c
    
    print(f"Thresholds Globales: {lower_threshold*100:.2f}% / {upper_threshold*100:.2f}%")
    
    # 4. Filter specified days: Martes, Miercoles, Jueves, Viernes
    target_days = ['Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    results = []
    
    for day in target_days:
        subset = df[df['weekday'] == day].dropna(subset=['next_o2c']).copy()
        
        # Upper Events (Drive)
        u_events = subset[subset['o2c'] > upper_threshold]
        u_count = len(u_events)
        u_cont = (u_events['next_o2c'] > 0).mean() * 100 if u_count > 0 else 0
        u_avg = u_events['next_o2c'].mean() * 100 if u_count > 0 else 0
        
        # Lower Events (Panic)
        l_events = subset[subset['o2c'] < lower_threshold]
        l_count = len(l_events)
        l_rev = (l_events['next_o2c'] > 0).mean() * 100 if l_count > 0 else 0
        l_avg = l_events['next_o2c'].mean() * 100 if l_count > 0 else 0
        
        results.append({
            'Trigger Day': day,
            'Drive Count': u_count,
            'P(Cont) Bulls': f"{u_cont:.1f}%",
            'Avg Bull $D+1$': f"{u_avg:+.3f}%",
            'Panic Count': l_count,
            'P(Rev) Bears': f"{l_rev:.1f}%",
            'Avg Bear $D+1$': f"{l_avg:+.3f}%"
        })

    print("\nRESUMEN DE PROBABILIDADES POR DIA:")
    print("-" * 95)
    report = pd.DataFrame(results)
    print(report.to_string(index=False))
    
    # Highlight highest alpha
    print("\nCONCLUSIONES ESTRUCTURALES:")
    for res in results:
        prob_rev = float(res['P(Rev) Bears'].strip('%'))
        if prob_rev > 60:
            print(f"[*] ALPHA DETECTADO: Si {asset_key} cae el {res['Trigger Day']}, el rebote al dia siguiente tiene {res['P(Rev) Bears']} prob.")
        
        prob_cont = float(res['P(Cont) Bulls'].strip('%'))
        if prob_cont < 45:
             print(f"[*] FAKE BULL DETECTADO: Si {asset_key} sube el {res['Trigger Day']}, el dia siguiente es bajista {100-prob_cont:.1f}% de las veces.")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'YM']:
        analyze_sigma_by_weekday(asset)
