from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================================
# AUDITED PROBABILITY TABLES
# EVERY number here MUST have a source in the repo
# ============================================================

# Source: output/charts/strategy/W2/ (complete 12-month matrices)
# Based on 2000-2026 History | * = >80% Win Rate
W2_MONTHLY = {
    'NQ': {
        1:  {'bull': {'prob_green': 78, 'prob_high': 89}, 'bear': {'prob_red': 75, 'prob_low': 88}},
        2:  {'bull': {'prob_green': 67, 'prob_high': 87}, 'bear': {'prob_red': 91, 'prob_low': 55}},
        3:  {'bull': {'prob_green': 91, 'prob_high': 82}, 'bear': {'prob_red': 57, 'prob_low': 86}},
        4:  {'bull': {'prob_green': 86, 'prob_high': 71}, 'bear': {'prob_red': 64, 'prob_low': 73}},
        5:  {'bull': {'prob_green': 92, 'prob_high': 92}, 'bear': {'prob_red': 62, 'prob_low': 62}},
        6:  {'bull': {'prob_green': 92, 'prob_high': 83}, 'bear': {'prob_red': 69, 'prob_low': 85}},
        7:  {'bull': {'prob_green': 84, 'prob_high': 89}, 'bear': {'prob_red': 50, 'prob_low': 67}},
        8:  {'bull': {'prob_green': 71, 'prob_high': 86}, 'bear': {'prob_red': 64, 'prob_low': 64}},
        9:  {'bull': {'prob_green': 77, 'prob_high': 85}, 'bear': {'prob_red': 85, 'prob_low': 85}},
        10: {'bull': {'prob_green': 75, 'prob_high': 94}, 'bear': {'prob_red': 60, 'prob_low': 50}},
        11: {'bull': {'prob_green': 94, 'prob_high': 88}, 'bear': {'prob_red': 60, 'prob_low': 90}},
        12: {'bull': {'prob_green': 85, 'prob_high': 85}, 'bear': {'prob_red': 77, 'prob_low': 85}},
    },
    'ES': {
        1:  {'bull': {'prob_green': 67, 'prob_high': 83}, 'bear': {'prob_red': 75, 'prob_low': 88}},
        2:  {'bull': {'prob_green': 80, 'prob_high': 80}, 'bear': {'prob_red': 82, 'prob_low': 55}},
        3:  {'bull': {'prob_green': 91, 'prob_high': 100}, 'bear': {'prob_red': 64, 'prob_low': 79}},
        4:  {'bull': {'prob_green': 79, 'prob_high': 79}, 'bear': {'prob_red': 36, 'prob_low': 64}},
        5:  {'bull': {'prob_green': 92, 'prob_high': 77}, 'bear': {'prob_red': 50, 'prob_low': 67}},
        6:  {'bull': {'prob_green': 73, 'prob_high': 87}, 'bear': {'prob_red': 70, 'prob_low': 80}},
        7:  {'bull': {'prob_green': 80, 'prob_high': 90}, 'bear': {'prob_red': 80, 'prob_low': 80}},
        8:  {'bull': {'prob_green': 73, 'prob_high': 87}, 'bear': {'prob_red': 60, 'prob_low': 70}},
        9:  {'bull': {'prob_green': 85, 'prob_high': 85}, 'bear': {'prob_red': 85, 'prob_low': 85}},
        10: {'bull': {'prob_green': 75, 'prob_high': 88}, 'bear': {'prob_red': 60, 'prob_low': 60}},
        11: {'bull': {'prob_green': 88, 'prob_high': 82}, 'bear': {'prob_red': 56, 'prob_low': 100}},
        12: {'bull': {'prob_green': 100, 'prob_high': 85}, 'bear': {'prob_red': 54, 'prob_low': 85}},
    },
    'YM': {
        1:  {'bull': {'prob_green': 59, 'prob_high': 76}, 'bear': {'prob_red': 70, 'prob_low': 90}},
        2:  {'bull': {'prob_green': 81, 'prob_high': 75}, 'bear': {'prob_red': 73, 'prob_low': 64}},
        3:  {'bull': {'prob_green': 83, 'prob_high': 92}, 'bear': {'prob_red': 57, 'prob_low': 57}},
        4:  {'bull': {'prob_green': 85, 'prob_high': 85}, 'bear': {'prob_red': 38, 'prob_low': 54}},
        5:  {'bull': {'prob_green': 85, 'prob_high': 85}, 'bear': {'prob_red': 62, 'prob_low': 77}},
        6:  {'bull': {'prob_green': 64, 'prob_high': 82}, 'bear': {'prob_red': 73, 'prob_low': 73}},
        7:  {'bull': {'prob_green': 85, 'prob_high': 95}, 'bear': {'prob_red': 33, 'prob_low': 83}},
        8:  {'bull': {'prob_green': 64, 'prob_high': 86}, 'bear': {'prob_red': 58, 'prob_low': 67}},
        9:  {'bull': {'prob_green': 71, 'prob_high': 71}, 'bear': {'prob_red': 83, 'prob_low': 83}},
        10: {'bull': {'prob_green': 82, 'prob_high': 94}, 'bear': {'prob_red': 67, 'prob_low': 67}},
        11: {'bull': {'prob_green': 100, 'prob_high': 87}, 'bear': {'prob_red': 64, 'prob_low': 100}},
        12: {'bull': {'prob_green': 94, 'prob_high': 88}, 'bear': {'prob_red': 80, 'prob_low': 80}},
    },
    'GC': {
        1:  {'bull': {'prob_green': 79, 'prob_high': 84}, 'bear': {'prob_red': 71, 'prob_low': 71}},
        2:  {'bull': {'prob_green': 81, 'prob_high': 75}, 'bear': {'prob_red': 80, 'prob_low': 90}},
        3:  {'bull': {'prob_green': 36, 'prob_high': 71}, 'bear': {'prob_red': 55, 'prob_low': 64}},
        4:  {'bull': {'prob_green': 74, 'prob_high': 74}, 'bear': {'prob_red': 67, 'prob_low': 83}},
        5:  {'bull': {'prob_green': 80, 'prob_high': 67}, 'bear': {'prob_red': 80, 'prob_low': 80}},
        6:  {'bull': {'prob_green': 64, 'prob_high': 73}, 'bear': {'prob_red': 79, 'prob_low': 64}},
        7:  {'bull': {'prob_green': 67, 'prob_high': 89}, 'bear': {'prob_red': 57, 'prob_low': 86}},
        8:  {'bull': {'prob_green': 94, 'prob_high': 67}, 'bear': {'prob_red': 100, 'prob_low': 86}},
        9:  {'bull': {'prob_green': 73, 'prob_high': 73}, 'bear': {'prob_red': 67, 'prob_low': 60}},
        10: {'bull': {'prob_green': 79, 'prob_high': 93}, 'bear': {'prob_red': 83, 'prob_low': 67}},
        11: {'bull': {'prob_green': 71, 'prob_high': 79}, 'bear': {'prob_red': 58, 'prob_low': 67}},
        12: {'bull': {'prob_green': 92, 'prob_high': 92}, 'bear': {'prob_red': 62, 'prob_low': 85}},
    }
}

# Source: output/charts/strategy/D2/ (NQ_weekly_fractal_seasonality_styled.png, etc.)
# Fully audited 12-month tables for D2 Signal (Tuesday Close vs Mon-Tue Range)
WEEKLY_SEASONAL = {
    'NQ': {
        1:  {'bull': {'prob_high': 86.5, 'prob_green': 75.7}, 'bear': {'prob_low': 78.6, 'prob_red': 83.3}},
        2:  {'bull': {'prob_high': 85.5, 'prob_green': 76.4}, 'bear': {'prob_low': 78.7, 'prob_red': 63.8}},
        3:  {'bull': {'prob_high': 79.4, 'prob_green': 77.8}, 'bear': {'prob_low': 72.3, 'prob_red': 72.3}},
        4:  {'bull': {'prob_high': 85.0, 'prob_green': 70.0}, 'bear': {'prob_low': 64.6, 'prob_red': 68.8}},
        5:  {'bull': {'prob_high': 78.3, 'prob_green': 75.0}, 'bear': {'prob_low': 78.7, 'prob_red': 66.0}},
        6:  {'bull': {'prob_high': 85.2, 'prob_green': 59.0}, 'bear': {'prob_low': 81.6, 'prob_red': 69.4}},
        7:  {'bull': {'prob_high': 81.1, 'prob_green': 64.9}, 'bear': {'prob_low': 68.4, 'prob_red': 60.5}},
        8:  {'bull': {'prob_high': 83.3, 'prob_green': 75.0}, 'bear': {'prob_low': 74.0, 'prob_red': 68.0}},
        9:  {'bull': {'prob_high': 72.6, 'prob_green': 71.0}, 'bear': {'prob_low': 69.6, 'prob_red': 65.2}},
        10: {'bull': {'prob_high': 79.1, 'prob_green': 73.1}, 'bear': {'prob_low': 77.1, 'prob_red': 43.8}},
        11: {'bull': {'prob_high': 76.7, 'prob_green': 76.7}, 'bear': {'prob_low': 69.2, 'prob_red': 69.2}},
        12: {'bull': {'prob_high': 68.2, 'prob_green': 72.7}, 'bear': {'prob_low': 67.3, 'prob_red': 73.5}},
    },
    'ES': {
        1:  {'bull': {'prob_high': 87.3, 'prob_green': 69.6}, 'bear': {'prob_low': 78.4, 'prob_red': 78.4}},
        2:  {'bull': {'prob_high': 76.7, 'prob_green': 68.3}, 'bear': {'prob_low': 78.6, 'prob_red': 52.4}},
        3:  {'bull': {'prob_high': 75.0, 'prob_green': 75.0}, 'bear': {'prob_low': 70.0, 'prob_red': 66.0}},
        4:  {'bull': {'prob_high': 89.9, 'prob_green': 71.0}, 'bear': {'prob_low': 74.4, 'prob_red': 61.5}},
        5:  {'bull': {'prob_high': 76.8, 'prob_green': 69.6}, 'bear': {'prob_low': 74.5, 'prob_red': 70.6}},
        6:  {'bull': {'prob_high': 77.8, 'prob_green': 66.7}, 'bear': {'prob_low': 85.1, 'prob_red': 74.5}},
        7:  {'bull': {'prob_high': 89.0, 'prob_green': 74.0}, 'bear': {'prob_low': 76.9, 'prob_red': 59.0}},
        8:  {'bull': {'prob_high': 81.4, 'prob_green': 74.6}, 'bear': {'prob_low': 72.5, 'prob_red': 56.9}},
        9:  {'bull': {'prob_high': 80.0, 'prob_green': 71.7}, 'bear': {'prob_low': 79.2, 'prob_red': 70.8}},
        10: {'bull': {'prob_high': 80.3, 'prob_green': 74.6}, 'bear': {'prob_low': 81.8, 'prob_red': 63.6}},
        11: {'bull': {'prob_high': 85.7, 'prob_green': 74.6}, 'bear': {'prob_low': 63.3, 'prob_red': 57.1}},
        12: {'bull': {'prob_high': 84.4, 'prob_green': 81.2}, 'bear': {'prob_low': 74.5, 'prob_red': 72.5}},
    },
    'YM': {
        1:  {'bull': {'prob_high': 87.8, 'prob_green': 75.7}, 'bear': {'prob_low': 82.6, 'prob_red': 76.1}},
        2:  {'bull': {'prob_high': 73.6, 'prob_green': 65.3}, 'bear': {'prob_low': 71.4, 'prob_red': 60.0}},
        3:  {'bull': {'prob_high': 82.8, 'prob_green': 79.3}, 'bear': {'prob_low': 75.0, 'prob_red': 64.3}},
        4:  {'bull': {'prob_high': 76.8, 'prob_green': 68.1}, 'bear': {'prob_low': 69.8, 'prob_red': 53.5}},
        5:  {'bull': {'prob_high': 64.9, 'prob_green': 64.9}, 'bear': {'prob_low': 76.4, 'prob_red': 70.9}},
        6:  {'bull': {'prob_high': 73.7, 'prob_green': 64.9}, 'bear': {'prob_low': 84.2, 'prob_red': 75.4}},
        7:  {'bull': {'prob_high': 80.0, 'prob_green': 72.0}, 'bear': {'prob_low': 75.6, 'prob_red': 51.2}},
        8:  {'bull': {'prob_high': 74.1, 'prob_green': 74.1}, 'bear': {'prob_low': 75.4, 'prob_red': 57.9}},
        9:  {'bull': {'prob_high': 78.6, 'prob_green': 64.3}, 'bear': {'prob_low': 66.7, 'prob_red': 70.4}},
        10: {'bull': {'prob_high': 82.1, 'prob_green': 80.6}, 'bear': {'prob_low': 79.2, 'prob_red': 60.4}},
        11: {'bull': {'prob_high': 70.3, 'prob_green': 76.6}, 'bear': {'prob_low': 72.9, 'prob_red': 56.2}},
        12: {'bull': {'prob_high': 83.3, 'prob_green': 77.3}, 'bear': {'prob_low': 73.5, 'prob_red': 67.3}},
    },
    'GC': {
        1:  {'bull': {'prob_high': 78.8, 'prob_green': 77.3}, 'bear': {'prob_low': 69.4, 'prob_red': 55.1}},
        2:  {'bull': {'prob_high': 77.2, 'prob_green': 77.2}, 'bear': {'prob_low': 68.9, 'prob_red': 73.3}},
        3:  {'bull': {'prob_high': 76.5, 'prob_green': 74.5}, 'bear': {'prob_low': 69.0, 'prob_red': 65.5}},
        4:  {'bull': {'prob_high': 68.9, 'prob_green': 60.7}, 'bear': {'prob_low': 55.3, 'prob_red': 57.4}},
        5:  {'bull': {'prob_high': 84.9, 'prob_green': 79.2}, 'bear': {'prob_low': 70.6, 'prob_red': 66.7}},
        6:  {'bull': {'prob_high': 79.6, 'prob_green': 69.4}, 'bear': {'prob_low': 77.0, 'prob_red': 68.9}},
        7:  {'bull': {'prob_high': 70.7, 'prob_green': 72.4}, 'bear': {'prob_low': 75.0, 'prob_red': 61.5}},
        8:  {'bull': {'prob_high': 78.7, 'prob_green': 75.4}, 'bear': {'prob_low': 68.0, 'prob_red': 54.0}},
        9:  {'bull': {'prob_high': 65.4, 'prob_green': 69.2}, 'bear': {'prob_low': 67.2, 'prob_red': 60.3}},
        10: {'bull': {'prob_high': 75.0, 'prob_green': 73.2}, 'bear': {'prob_low': 69.5, 'prob_red': 61.0}},
        11: {'bull': {'prob_high': 76.3, 'prob_green': 72.9}, 'bear': {'prob_low': 64.2, 'prob_red': 60.4}},
        12: {'bull': {'prob_high': 74.2, 'prob_green': 75.8}, 'bear': {'prob_low': 69.8, 'prob_red': 66.0}},
    }
}

# Source: output/charts/Multi/weekly/alpha_matrix_all_indices_weekly.png
# Persistence and Reversion edges based on Weekly 1-Sigma moves
WEEKLY_ALPHA_MATRIX = {
    'NQ': {
        'bull_momentum':  {'threshold': 0.0355, 'prob': 61.0, 'target': 'CONTINUACIÓN FUERTE', 'grade': 'GOLD+'},
        'mean_reversion': {'threshold': -0.0273, 'prob': 55.8, 'target': 'REBOTE MODERADO', 'grade': 'MEDIUM'}
    },
    'ES': {
        'bull_momentum':  {'threshold': 0.0298, 'prob': 54.3, 'target': 'CONTINUACIÓN EN W+1', 'grade': 'MEDIUM'},
        'mean_reversion': {'threshold': -0.0233, 'prob': 65.8, 'target': 'REBOTE ALTA PROB', 'grade': 'GOLD+'}
    },
    'YM': {
        'bull_momentum':  {'threshold': 0.0290, 'prob': 56.2, 'target': 'CONTINUACIÓN EN W+1', 'grade': 'MEDIUM'},
        'mean_reversion': {'threshold': -0.0241, 'prob': 67.7, 'target': 'REBOTE POR CAPITULACIÓN', 'grade': 'GOLD+'}
    }
}

# --- DAILY SPECIFIC TRIGGERS (Validated T-stats from Daily Alpha Matrix) ---
# Key: (asset, weekday, type) where weekday: 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri
DAILY_TRIGGERS = {
    ('NQ', 1, 'panic'):  {'target': 'REBOTE MIÉRCOLES', 'prob': 55.4, 'grade': 'GOLD (T>2.1)', 'avg_ret': '+0.54%'},
    ('YM', 4, 'panic'):  {'target': 'REBOTE LUNES', 'prob': 67.9, 'grade': 'SILVER (T>1.5)', 'avg_ret': '+0.44%'},
    ('NQ', 3, 'drive'):  {'target': 'REVERSIÓN VIERNES', 'prob': 57.8, 'grade': 'BRONZE (T>1.4)', 'avg_ret': '-0.27%'},
    ('NQ', 4, 'drive'):  {'target': 'CONTINUACIÓN LUNES', 'prob': 64.5, 'grade': 'SILVER', 'avg_ret': '+0.11%'},
    ('YM', 2, 'panic'):  {'target': 'REBOTE JUEVES', 'prob': 63.3, 'grade': 'BRONZE', 'avg_ret': '-0.12%'},
}

# Source: DOR output charts (output/charts/*/daily/DOR_O2C_D_*_2020-2025_*.png)
SIGMA = {'NQ': 0.01560, 'ES': 0.01266, 'YM': 0.01219, 'GC': 0.00932}

ASSET_TICKERS = {'NQ': 'NQ=F', 'ES': 'ES=F', 'YM': 'YM=F', 'GC': 'GC=F'}
ASSET_NAMES = {'NQ': 'NASDAQ 100', 'ES': 'S&P 500', 'YM': 'DOW JONES', 'GC': 'ORO'}
DAY_NAMES = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SAB', 'DOM']

def get_grade(p):
    if p >= 90: return 'DIAMOND'
    if p >= 82: return 'GOLD+'
    if p >= 75: return 'GOLD'
    return 'SILVER'

def calc_layers(asset, df):
    # Use the LAST DATA BAR's date as reference, not the server clock.
    # This avoids timezone drift (e.g., 7pm CST = Tues UTC but data is still Mon)
    last_date = df.index[-1]
    day = last_date.day
    month = last_date.month
    year = last_date.year
    
    # 1. Monthly — Only show if W2 signal is LOCKED (day >= 13)
    month_df = df[(df.index.month == month) & (df.index.year == year)]
    m_signals = []
    m_bias = None
    if day >= 13:
        w1w2 = month_df[month_df.index.day <= 13]
        if not w1w2.empty:
            hi, lo = float(w1w2['High'].max()), float(w1w2['Low'].min())
            w2c = float(w1w2['Close'].iloc[-1])
            pos = (w2c - lo) / (hi - lo) if (hi - lo) != 0 else 0.5
            is_bear = pos < 0.5
            m_bias = "BAJISTA" if is_bear else "ALCISTA"
            
            curr_lo, curr_hi = float(month_df['Low'].min()), float(month_df['High'].max())
            probs = W2_MONTHLY.get(asset, {}).get(month, None)
            if probs:
                p_set = probs.get('bear') if is_bear else probs.get('bull')
                if p_set and is_bear:
                    m_signals.append({'target': 'CIERRE BAJISTA', 'prob': p_set['prob_red'], 'status': 'ACTIVO', 'grade': get_grade(p_set['prob_red']), 'color': 'red'})
                    s = 'COMPLETADO' if curr_lo < lo else 'PENDIENTE'
                    m_signals.append({'target': 'NUEVO BAJO', 'prob': p_set['prob_low'], 'status': s, 'grade': get_grade(p_set['prob_low']), 'color': 'red' if s=='PENDIENTE' else 'green'})
                elif p_set and not is_bear:
                    m_signals.append({'target': 'CIERRE ALCISTA', 'prob': p_set['prob_green'], 'status': 'ACTIVO', 'grade': get_grade(p_set['prob_green']), 'color': 'green'})
                    s = 'COMPLETADO' if curr_hi > hi else 'PENDIENTE'
                    m_signals.append({'target': 'NUEVO ALTO', 'prob': p_set['prob_high'], 'status': s, 'grade': get_grade(p_set['prob_high']), 'color': 'green'})
                # If p_set is None → this month/direction has no audited data → m_signals stays empty

    # 2. Weekly (D2 Fractal) — Only show AFTER Tuesday close (Tuesday 16:30 EST / 21:30 UTC)
    current_week = last_date.isocalendar()[1]
    week_df = df[(df.index.isocalendar().week == current_week) & (df.index.isocalendar().year == year)]
    w_signals = []
    w_bias = None
    
    if len(week_df) >= 2:
        # Determine if we are past the signal activation time
        # Logic: Show if it's Wednesday or later, OR if it's Tuesday after 21:30 UTC
        now_utc = datetime.utcnow()
        show_d2 = False
        
        if now_utc.weekday() > 1: # Wednesday (2) onwards
            show_d2 = True
        elif now_utc.weekday() == 1: # Tuesday (1)
            # 16:30 EST is approx 21:30 UTC. 
            if now_utc.hour > 21 or (now_utc.hour == 21 and now_utc.minute >= 30):
                show_d2 = True
                
        if show_d2:
            d1, d2 = week_df.iloc[0], week_df.iloc[1]
            hi, lo = max(float(d1['High']), float(d2['High'])), min(float(d1['Low']), float(d2['Low']))
            pos = (float(d2['Close']) - lo) / (hi - lo) if (hi - lo) != 0 else 0.5
            is_bull = pos > 0.5
            w_bias = "ALCISTA" if is_bull else "BAJISTA"
            curr_lo, curr_hi = float(week_df['Low'].min()), float(week_df['High'].max())
            
            seasonal = WEEKLY_SEASONAL.get(asset, {}).get(month, None)
            if seasonal:
                p_set = seasonal.get('bull') if is_bull else seasonal.get('bear')
                if p_set:
                    if is_bull:
                        w_signals.append({'target': 'CIERRE ALCISTA', 'prob': p_set['prob_green'], 'status': 'ACTIVO', 'grade': get_grade(p_set['prob_green']), 'color': 'green'})
                        s = 'COMPLETADO' if curr_hi > hi else 'PENDIENTE'
                        w_signals.append({'target': 'NUEVO ALTO', 'prob': p_set['prob_high'], 'status': s, 'grade': get_grade(p_set['prob_high']), 'color': 'green' if s=='PENDIENTE' else 'green'})
                    else:
                        w_signals.append({'target': 'CIERRE BAJISTA', 'prob': p_set['prob_red'], 'status': 'ACTIVO', 'grade': get_grade(p_set['prob_red']), 'color': 'red'})
                        s = 'COMPLETADO' if curr_lo < lo else 'PENDIENTE'
                        w_signals.append({'target': 'NUEVO BAJO', 'prob': p_set['prob_low'], 'status': s, 'grade': get_grade(p_set['prob_low']), 'color': 'red' if s=='PENDIENTE' else 'green'})

    # 3. Weekly Alpha Matrix (1-Sigma Persistence/Reversion)
    # Check if the PREVIOUS WEEK closed beyond alpha thresholds
    previous_week = (last_date - pd.Timedelta(days=7)).isocalendar()[1]
    prev_week_df = df[(df.index.isocalendar().week == previous_week) & (df.index.isocalendar().year == (last_date - pd.Timedelta(days=7)).year)]
    
    alpha_signals = []
    if not prev_week_df.empty:
        pw_open = float(prev_week_df['Open'].iloc[0])
        pw_close = float(prev_week_df['Close'].iloc[-1])
        pw_ret = (pw_close - pw_open) / pw_open
        
        a_matrix = WEEKLY_ALPHA_MATRIX.get(asset)
        if a_matrix:
            # Bull Momentum
            if pw_ret >= a_matrix['bull_momentum']['threshold']:
                m = a_matrix['bull_momentum']
                alpha_signals.append({'target': m['target'], 'prob': m['prob'], 'status': 'ACTIVO', 'grade': m['grade'], 'color': 'green'})
            # Mean Reversion
            elif pw_ret <= a_matrix['mean_reversion']['threshold']:
                r = a_matrix['mean_reversion']
                alpha_signals.append({'target': r['target'], 'prob': r['prob'], 'status': 'ACTIVO', 'grade': r['grade'], 'color': 'green'})

    # 4. Daily — Daily context
    d_signals = []
    sigma = SIGMA.get(asset, 0.013)

    # --- YESTERDAY'S TRIGGERS (predict today) ---
    if len(df) >= 2:
        yesterday = df.iloc[-2]
        y_o, y_c = float(yesterday['Open']), float(yesterday['Close'])
        y_o2c = (y_c - y_o) / y_o if y_o != 0 else 0
        y_weekday = yesterday.name.weekday()  # from the data, not the clock
        y_day_name = DAY_NAMES[y_weekday] if y_weekday < 7 else '?'

        if y_o2c > sigma:
            trigger = DAILY_TRIGGERS.get((asset, y_weekday, 'drive'), None)
            if trigger:
                d_signals.append({
                    'target': trigger['target'],
                    'prob': trigger['prob'],
                    'status': 'ACTIVO',
                    'grade': trigger['grade'],
                    'color': 'red' if 'REVERSIÓN' in trigger['target'] else 'green',
                    'val': f'{y_day_name} cerró {y_o2c*100:+.2f}% (>{sigma*100:.1f}%)',
                    'avg_ret': trigger['avg_ret']
                })
        elif y_o2c < -sigma:
            trigger = DAILY_TRIGGERS.get((asset, y_weekday, 'panic'), None)
            if trigger:
                d_signals.append({
                    'target': trigger['target'],
                    'prob': trigger['prob'],
                    'status': 'ACTIVO',
                    'grade': trigger['grade'],
                    'color': 'green',
                    'val': f'{y_day_name} cerró {y_o2c*100:+.2f}% (<-{sigma*100:.1f}%)',
                    'avg_ret': trigger['avg_ret']
                })

    # General expansion bias REMOVED — probabilities were not audited
    # If neither yesterday triggered nor today broke σ → d_signals stays empty → column hidden

    return {
        'monthly': {'bias': m_bias, 'signals': m_signals},
        'weekly': {'bias': w_bias, 'signals': w_signals + alpha_signals},
        'daily': {'signals': d_signals}
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        res = []
        for k, ticker in ASSET_TICKERS.items():
            try:
                t = yf.Ticker(ticker); df = t.history(period='60d', interval='1d')
                if df.empty: res.append({'asset': k, 'error': 'Empty'}); continue
                res.append({'asset': k, 'name': ASSET_NAMES[k], 'price': round(float(df['Close'].iloc[-1]), 2), 'layers': calc_layers(k, df)})
            except Exception as e: res.append({'asset': k, 'error': str(e)})
        self.wfile.write(json.dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'), 'data': res}).encode())
