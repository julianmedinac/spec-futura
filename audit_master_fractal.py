import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def audit_monthly_w2_signal_exact(asset_key):
    print(f"\n{'='*100}")
    print(f"AUDITORIA DEFINITIVA: PATRON W2 > 50% vs < 50% (MENSUAL)")
    print(f"Activo: {asset_key}")
    print(f"Rango de Fechas: 2000-01-01 a 2026-02-16")
    print(f"Metodologia: Analisis EXACTO de senal W2 y su impacto en el RESTO del mes.")
    print(f"{'='*100}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    # Agrupar por Mes Real (Year-Month)
    monthly_groups = data.groupby(['year', 'month'])
    
    results = []
    
    for (year, month), month_data in monthly_groups:
        # Obtener semanas unicas en orden cronologico
        # Usamos drop_duplicates para preservar orden de aparicion en el index
        weeks = month_data['week_of_year'].drop_duplicates().tolist()
        
        # Necesitamos al menos 2 semanas completas para tener W1 y W2
        if len(weeks) < 2: continue
        
        w1_idx = weeks[0]
        w2_idx = weeks[1]
        
        w1_data = month_data[month_data['week_of_year'] == w1_idx]
        w2_data = month_data[month_data['week_of_year'] == w2_idx]
        
        if w1_data.empty or w2_data.empty: continue
        
        # Calcular el momento exacto donde termina W2 para separar "Antes" y "Despues"
        w2_end_time = w2_data.index.max()
        
        # Datos PRE-SIGNAL (Todo lo que paso hasta el cierre de W2)
        pre_signal_data = month_data[month_data.index <= w2_end_time]
        
        # Calcular Rango W1-W2 (Maximo y Minimo acumulado hasta el cierre de W2)
        range_high = pre_signal_data['high'].max()
        range_low = pre_signal_data['low'].min()
        rng = range_high - range_low
        
        if rng == 0: continue
            
        midpoint = range_low + (rng * 0.5)
        w2_close = w2_data.iloc[-1]['close'] # Precio de cierre de la segunda semana
        
        # Determinar Senal (Fractal)
        signal_type = 'BULL' if w2_close > midpoint else 'BEAR'
        
        # Datos POST-SIGNAL (Lo que paso el resto del mes)
        post_signal_data = month_data[month_data.index > w2_end_time]
        
        # Outcomes Defaults
        made_new_high = False
        made_new_low = False
        
        if not post_signal_data.empty:
            rest_high = post_signal_data['high'].max()
            rest_low = post_signal_data['low'].min()
            
            # Extension: Si hizo un maximo mas alto que el rango W1-W2
            made_new_high = rest_high > range_high
            # Extension: Si hizo un minimo mas bajo que el rango W1-W2
            made_new_low = rest_low < range_low
            
        # Outcome Cierre Mensual
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
    
    # Imprimir Tabla Resumen por Mes
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
             # Prob New Low en un Bull Signal es interesante saber (Falso Positivo)
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
            
            # Note: Green Prob for Bear Signal is (100 - p_red)
            print(f"{'     ':<5} | {'BEAR':<5} | {n_bear:<7} | {(100-p_red):9.1f}%   | {p_red:9.1f}% | {p_high_fail:9.1f}%   | {p_low:9.1f}%")
            print("-" * 90)
        else:
             print(f"{'     ':<5} | {'BEAR':<5} | {'0':<7} | {'N/A':<12} | {'N/A':<10} | {'N/A':<12} | {'N/A':<12}")
             print("-" * 90)

if __name__ == "__main__":
    audit_monthly_w2_signal_exact('NQ')
