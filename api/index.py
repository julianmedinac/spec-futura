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
        1:  {'bull_50': {'prob_high': 86.5, 'prob_green': 75.7}, 'bear_50': {'prob_low': 78.0, 'prob_red': 85.4}, 'bull_75': {'prob_high': 89.7, 'prob_green': 79.5}, 'bear_25': {'prob_low': 83.3, 'prob_red': 88.9}},
        2:  {'bull_50': {'prob_high': 86.0, 'prob_green': 73.7}, 'bear_50': {'prob_low': 78.3, 'prob_red': 63.0}, 'bull_75': {'prob_high': 97.1, 'prob_green': 82.9}, 'bear_25': {'prob_low': 85.7, 'prob_red': 67.9}},
        3:  {'bull_50': {'prob_high': 79.7, 'prob_green': 76.6}, 'bear_50': {'prob_low': 73.9, 'prob_red': 71.7}, 'bull_75': {'prob_high': 90.2, 'prob_green': 85.4}, 'bear_25': {'prob_low': 84.6, 'prob_red': 69.2}},
        4:  {'bull_50': {'prob_high': 85.0, 'prob_green': 70.0}, 'bear_50': {'prob_low': 64.6, 'prob_red': 68.8}, 'bull_75': {'prob_high': 97.6, 'prob_green': 78.0}, 'bear_25': {'prob_low': 67.9, 'prob_red': 78.6}},
        5:  {'bull_50': {'prob_high': 78.3, 'prob_green': 75.0}, 'bear_50': {'prob_low': 78.7, 'prob_red': 66.0}, 'bull_75': {'prob_high': 86.1, 'prob_green': 72.2}, 'bear_25': {'prob_low': 85.7, 'prob_red': 66.7}},
        6:  {'bull_50': {'prob_high': 85.2, 'prob_green': 59.0}, 'bear_50': {'prob_low': 81.6, 'prob_red': 69.4}, 'bull_75': {'prob_high': 84.1, 'prob_green': 63.6}, 'bear_25': {'prob_low': 90.5, 'prob_red': 71.4}},
        7:  {'bull_50': {'prob_high': 81.1, 'prob_green': 64.9}, 'bear_50': {'prob_low': 68.4, 'prob_red': 60.5}, 'bull_75': {'prob_high': 91.1, 'prob_green': 73.3}, 'bear_25': {'prob_low': 82.4, 'prob_red': 58.8}},
        8:  {'bull_50': {'prob_high': 83.3, 'prob_green': 75.0}, 'bear_50': {'prob_low': 74.0, 'prob_red': 68.0}, 'bull_75': {'prob_high': 87.1, 'prob_green': 83.9}, 'bear_25': {'prob_low': 71.4, 'prob_red': 71.4}},
        9:  {'bull_50': {'prob_high': 72.6, 'prob_green': 71.0}, 'bear_50': {'prob_low': 69.6, 'prob_red': 65.2}, 'bull_75': {'prob_high': 88.9, 'prob_green': 83.3}, 'bear_25': {'prob_low': 84.0, 'prob_red': 76.0}},
        10:  {'bull_50': {'prob_high': 79.1, 'prob_green': 73.1}, 'bear_50': {'prob_low': 77.1, 'prob_red': 43.8}, 'bull_75': {'prob_high': 86.8, 'prob_green': 76.3}, 'bear_25': {'prob_low': 90.9, 'prob_red': 57.6}},
        11:  {'bull_50': {'prob_high': 76.7, 'prob_green': 76.7}, 'bear_50': {'prob_low': 68.4, 'prob_red': 68.4}, 'bull_75': {'prob_high': 84.4, 'prob_green': 82.2}, 'bear_25': {'prob_low': 61.9, 'prob_red': 66.7}},
        12:  {'bull_50': {'prob_high': 68.2, 'prob_green': 72.7}, 'bear_50': {'prob_low': 67.3, 'prob_red': 73.5}, 'bull_75': {'prob_high': 78.0, 'prob_green': 82.9}, 'bear_25': {'prob_low': 68.0, 'prob_red': 80.0}},
    },
    'ES': {
        1:  {'bull_50': {'prob_high': 87.3, 'prob_green': 69.6}, 'bear_50': {'prob_low': 78.4, 'prob_red': 78.4}, 'bull_75': {'prob_high': 97.5, 'prob_green': 82.5}, 'bear_25': {'prob_low': 93.3, 'prob_red': 100.0}},
        2:  {'bull_50': {'prob_high': 77.4, 'prob_green': 67.7}, 'bear_50': {'prob_low': 81.0, 'prob_red': 54.8}, 'bull_75': {'prob_high': 84.6, 'prob_green': 76.9}, 'bear_25': {'prob_low': 91.3, 'prob_red': 65.2}},
        3:  {'bull_50': {'prob_high': 73.8, 'prob_green': 73.8}, 'bear_50': {'prob_low': 70.0, 'prob_red': 66.0}, 'bull_75': {'prob_high': 85.7, 'prob_green': 85.7}, 'bear_25': {'prob_low': 80.0, 'prob_red': 76.7}},
        4:  {'bull_50': {'prob_high': 89.9, 'prob_green': 71.0}, 'bear_50': {'prob_low': 74.4, 'prob_red': 61.5}, 'bull_75': {'prob_high': 93.3, 'prob_green': 80.0}, 'bear_25': {'prob_low': 72.0, 'prob_red': 56.0}},
        5:  {'bull_50': {'prob_high': 76.8, 'prob_green': 69.6}, 'bear_50': {'prob_low': 74.5, 'prob_red': 70.6}, 'bull_75': {'prob_high': 83.9, 'prob_green': 71.0}, 'bear_25': {'prob_low': 78.6, 'prob_red': 67.9}},
        6:  {'bull_50': {'prob_high': 77.8, 'prob_green': 66.7}, 'bear_50': {'prob_low': 85.1, 'prob_red': 74.5}, 'bull_75': {'prob_high': 82.1, 'prob_green': 79.5}, 'bear_25': {'prob_low': 87.0, 'prob_red': 82.6}},
        7:  {'bull_50': {'prob_high': 89.0, 'prob_green': 74.0}, 'bear_50': {'prob_low': 76.9, 'prob_red': 59.0}, 'bull_75': {'prob_high': 93.0, 'prob_green': 69.8}, 'bear_25': {'prob_low': 85.7, 'prob_red': 52.4}},
        8:  {'bull_50': {'prob_high': 81.4, 'prob_green': 74.6}, 'bear_50': {'prob_low': 72.0, 'prob_red': 56.0}, 'bull_75': {'prob_high': 83.9, 'prob_green': 83.9}, 'bear_25': {'prob_low': 80.8, 'prob_red': 65.4}},
        9:  {'bull_50': {'prob_high': 80.0, 'prob_green': 71.7}, 'bear_50': {'prob_low': 79.2, 'prob_red': 70.8}, 'bull_75': {'prob_high': 91.2, 'prob_green': 79.4}, 'bear_25': {'prob_low': 87.0, 'prob_red': 82.6}},
        10:  {'bull_50': {'prob_high': 80.3, 'prob_green': 74.6}, 'bear_50': {'prob_low': 81.8, 'prob_red': 63.6}, 'bull_75': {'prob_high': 88.6, 'prob_green': 85.7}, 'bear_25': {'prob_low': 92.3, 'prob_red': 73.1}},
        11:  {'bull_50': {'prob_high': 85.7, 'prob_green': 74.6}, 'bear_50': {'prob_low': 62.5, 'prob_red': 58.3}, 'bull_75': {'prob_high': 90.9, 'prob_green': 84.1}, 'bear_25': {'prob_low': 66.7, 'prob_red': 66.7}},
        12:  {'bull_50': {'prob_high': 84.4, 'prob_green': 81.2}, 'bear_50': {'prob_low': 74.5, 'prob_red': 72.5}, 'bull_75': {'prob_high': 91.1, 'prob_green': 88.9}, 'bear_25': {'prob_low': 73.5, 'prob_red': 79.4}},
    },
    'YM': {
        1:  {'bull_50': {'prob_high': 87.8, 'prob_green': 75.7}, 'bear_50': {'prob_low': 82.6, 'prob_red': 76.1}, 'bull_75': {'prob_high': 89.6, 'prob_green': 77.1}, 'bear_25': {'prob_low': 87.0, 'prob_red': 82.6}},
        2:  {'bull_50': {'prob_high': 72.6, 'prob_green': 64.4}, 'bear_50': {'prob_low': 72.2, 'prob_red': 61.1}, 'bull_75': {'prob_high': 83.3, 'prob_green': 66.7}, 'bear_25': {'prob_low': 85.7, 'prob_red': 66.7}},
        3:  {'bull_50': {'prob_high': 81.4, 'prob_green': 78.0}, 'bear_50': {'prob_low': 75.0, 'prob_red': 64.3}, 'bull_75': {'prob_high': 86.8, 'prob_green': 89.5}, 'bear_25': {'prob_low': 76.5, 'prob_red': 70.6}},
        4:  {'bull_50': {'prob_high': 76.8, 'prob_green': 68.1}, 'bear_50': {'prob_low': 69.8, 'prob_red': 53.5}, 'bull_75': {'prob_high': 82.6, 'prob_green': 73.9}, 'bear_25': {'prob_low': 84.0, 'prob_red': 56.0}},
        5:  {'bull_50': {'prob_high': 64.9, 'prob_green': 64.9}, 'bear_50': {'prob_low': 76.4, 'prob_red': 70.9}, 'bull_75': {'prob_high': 72.4, 'prob_green': 72.4}, 'bear_25': {'prob_low': 78.1, 'prob_red': 75.0}},
        6:  {'bull_50': {'prob_high': 73.7, 'prob_green': 64.9}, 'bear_50': {'prob_low': 84.2, 'prob_red': 75.4}, 'bull_75': {'prob_high': 76.3, 'prob_green': 73.7}, 'bear_25': {'prob_low': 93.8, 'prob_red': 81.2}},
        7:  {'bull_50': {'prob_high': 80.0, 'prob_green': 72.0}, 'bear_50': {'prob_low': 75.6, 'prob_red': 51.2}, 'bull_75': {'prob_high': 87.8, 'prob_green': 81.6}, 'bear_25': {'prob_low': 85.2, 'prob_red': 59.3}},
        8:  {'bull_50': {'prob_high': 74.1, 'prob_green': 74.1}, 'bear_50': {'prob_low': 75.4, 'prob_red': 57.9}, 'bull_75': {'prob_high': 78.8, 'prob_green': 78.8}, 'bear_25': {'prob_low': 87.5, 'prob_red': 75.0}},
        9:  {'bull_50': {'prob_high': 78.6, 'prob_green': 64.3}, 'bear_50': {'prob_low': 66.7, 'prob_red': 70.4}, 'bull_75': {'prob_high': 100.0, 'prob_green': 82.4}, 'bear_25': {'prob_low': 88.5, 'prob_red': 88.5}},
        10:  {'bull_50': {'prob_high': 82.1, 'prob_green': 80.6}, 'bear_50': {'prob_low': 79.2, 'prob_red': 60.4}, 'bull_75': {'prob_high': 92.5, 'prob_green': 90.0}, 'bear_25': {'prob_low': 87.1, 'prob_red': 71.0}},
        11:  {'bull_50': {'prob_high': 70.3, 'prob_green': 76.6}, 'bear_50': {'prob_low': 72.9, 'prob_red': 56.2}, 'bull_75': {'prob_high': 73.7, 'prob_green': 86.8}, 'bear_25': {'prob_low': 69.6, 'prob_red': 69.6}},
        12:  {'bull_50': {'prob_high': 83.3, 'prob_green': 77.3}, 'bear_50': {'prob_low': 73.5, 'prob_red': 67.3}, 'bull_75': {'prob_high': 83.3, 'prob_green': 83.3}, 'bear_25': {'prob_low': 76.5, 'prob_red': 73.5}},
    },
    'GC': {
        1:  {'bull_50': {'prob_high': 78.8, 'prob_green': 77.3}, 'bear_50': {'prob_low': 69.4, 'prob_red': 55.1}, 'bull_75': {'prob_high': 81.6, 'prob_green': 79.6}, 'bear_25': {'prob_low': 70.6, 'prob_red': 64.7}},
        2:  {'bull_50': {'prob_high': 77.6, 'prob_green': 77.6}, 'bear_50': {'prob_low': 69.6, 'prob_red': 71.7}, 'bull_75': {'prob_high': 81.0, 'prob_green': 76.2}, 'bear_25': {'prob_low': 80.8, 'prob_red': 88.5}},
        3:  {'bull_50': {'prob_high': 76.5, 'prob_green': 74.5}, 'bear_50': {'prob_low': 67.8, 'prob_red': 66.1}, 'bull_75': {'prob_high': 85.0, 'prob_green': 82.5}, 'bear_25': {'prob_low': 69.6, 'prob_red': 67.4}},
        4:  {'bull_50': {'prob_high': 68.9, 'prob_green': 60.7}, 'bear_50': {'prob_low': 56.5, 'prob_red': 58.7}, 'bull_75': {'prob_high': 71.0, 'prob_green': 64.5}, 'bear_25': {'prob_low': 69.6, 'prob_red': 69.6}},
        5:  {'bull_50': {'prob_high': 84.9, 'prob_green': 79.2}, 'bear_50': {'prob_low': 70.6, 'prob_red': 66.7}, 'bull_75': {'prob_high': 83.8, 'prob_green': 78.4}, 'bear_25': {'prob_low': 65.8, 'prob_red': 65.8}},
        6:  {'bull_50': {'prob_high': 79.6, 'prob_green': 69.4}, 'bear_50': {'prob_low': 77.0, 'prob_red': 68.9}, 'bull_75': {'prob_high': 84.0, 'prob_green': 68.0}, 'bear_25': {'prob_low': 84.4, 'prob_red': 78.1}},
        7:  {'bull_50': {'prob_high': 70.7, 'prob_green': 72.4}, 'bear_50': {'prob_low': 75.0, 'prob_red': 61.5}, 'bull_75': {'prob_high': 76.3, 'prob_green': 78.9}, 'bear_25': {'prob_low': 72.2, 'prob_red': 72.2}},
        8:  {'bull_50': {'prob_high': 78.7, 'prob_green': 75.4}, 'bear_50': {'prob_low': 68.0, 'prob_red': 54.0}, 'bull_75': {'prob_high': 76.9, 'prob_green': 76.9}, 'bear_25': {'prob_low': 75.0, 'prob_red': 50.0}},
        9:  {'bull_50': {'prob_high': 65.4, 'prob_green': 69.2}, 'bear_50': {'prob_low': 67.2, 'prob_red': 60.3}, 'bull_75': {'prob_high': 70.0, 'prob_green': 75.0}, 'bear_25': {'prob_low': 62.8, 'prob_red': 62.8}},
        10:  {'bull_50': {'prob_high': 75.0, 'prob_green': 73.2}, 'bear_50': {'prob_low': 69.5, 'prob_red': 61.0}, 'bull_75': {'prob_high': 75.6, 'prob_green': 85.4}, 'bear_25': {'prob_low': 77.5, 'prob_red': 72.5}},
        11:  {'bull_50': {'prob_high': 76.3, 'prob_green': 72.9}, 'bear_50': {'prob_low': 64.2, 'prob_red': 60.4}, 'bull_75': {'prob_high': 80.0, 'prob_green': 77.5}, 'bear_25': {'prob_low': 70.7, 'prob_red': 70.7}},
        12:  {'bull_50': {'prob_high': 74.2, 'prob_green': 75.8}, 'bear_50': {'prob_low': 71.2, 'prob_red': 67.3}, 'bull_75': {'prob_high': 71.4, 'prob_green': 80.0}, 'bear_25': {'prob_low': 66.7, 'prob_red': 66.7}},
    },
}



# Source: output/charts/Multi/weekly/alpha_matrix_all_indices_weekly.png
# Only Mean Reversion kept — Bull Momentum removed (T < 1, not significant)
# Probabilities re-computed on 2015-2025 data, audited 18/02/2026
WEEKLY_ALPHA_MATRIX = {
    'NQ': {
        'mean_reversion': {'threshold': -0.0273, 'prob': 57.5, 'target': 'REBOTE MODERADO', 'grade': 'SILVER (T=2.19)'}
    },
    'ES': {
        'mean_reversion': {'threshold': -0.0233, 'prob': 66.7, 'target': 'REBOTE ALTA PROB', 'grade': 'GOLD (T=3.13)'}
    },
    'YM': {
        'mean_reversion': {'threshold': -0.0241, 'prob': 71.4, 'target': 'REBOTE POR CAPITULACIÓN', 'grade': 'GOLD (T=2.65)'}
    }
}

# --- WEEKLY BIAS & INERTIA (Daily σ Breach → Weekly Close Direction) ---
# Source: output/charts/Multi/daily/weekly_bias_inertia_matrix.png
# AUDITED 2026-03-04: All values verified against chart (Periodo 2005-2025, AUDITED 15/02/2026)
# Key: (asset, weekday, type) where weekday: 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri
WEEKLY_BIAS_TRIGGERS = {
    ('NQ', 0, 'drive'):  {'direction': 'BULL', 'prob': 82.3, 'avg_ret': '+2.82%', 't_stat': 6.53, 'grade': 'GOLD+'},
    ('NQ', 4, 'panic'):  {'direction': 'BEAR', 'prob': 84.5, 'avg_ret': '-2.44%', 't_stat': 7.40, 'grade': 'GOLD+'},
    ('ES', 0, 'drive'):  {'direction': 'BULL', 'prob': 86.5, 'avg_ret': '+2.65%', 't_stat': 7.30, 'grade': 'GOLD+'},
    ('ES', 4, 'panic'):  {'direction': 'BEAR', 'prob': 91.8, 'avg_ret': '-2.16%', 't_stat': 5.97, 'grade': 'GOLD+'},
    ('NQ', 3, 'panic'):  {'direction': 'BEAR', 'prob': 78.5, 'avg_ret': '-2.12%', 't_stat': 6.26, 'grade': 'GOLD'},
    ('YM', 2, 'panic'):  {'direction': 'BEAR', 'prob': 75.5, 'avg_ret': '-1.93%', 't_stat': 4.58, 'grade': 'GOLD'},
    ('ES', 1, 'drive'):  {'direction': 'BULL', 'prob': 75.5, 'avg_ret': '+1.75%', 't_stat': 3.65, 'grade': 'SILVER'},
    # NQ/ES Wed Drive omitted — D2 signal already establishes weekly bias by Wednesday
}

# Source: output/charts/seasonality/{ASSET}/monthly/{ASSET}_monthly_seasonality.png
# Probability of GREEN (positive) close per month — SeasonalityCalculator.hit_rate (2000-2026)
MONTHLY_BIAS = {
    'NQ': {1: 61.5, 2: 38.5, 3: 64.0, 4: 64.0, 5: 64.0, 6: 60.0, 7: 76.0, 8: 56.0, 9: 48.0, 10: 61.5, 11: 73.1, 12: 53.8},
    'ES': {1: 53.8, 2: 46.2, 3: 60.0, 4: 72.0, 5: 76.0, 6: 56.0, 7: 72.0, 8: 64.0, 9: 52.0, 10: 61.5, 11: 73.1, 12: 73.1},
    'YM': {1: 54.2, 2: 62.5, 3: 65.2, 4: 73.9, 5: 62.5, 6: 50.0, 7: 70.8, 8: 62.5, 9: 50.0, 10: 58.3, 11: 79.2, 12: 62.5},
    'GC': {1: 65.4, 2: 53.8, 3: 48.0, 4: 64.0, 5: 52.0, 6: 44.0, 7: 56.0, 8: 72.0, 9: 50.0, 10: 50.0, 11: 57.7, 12: 65.4},
}

# Source: DOR output charts (output/charts/*/daily/DOR_O2C_D_*_2020-2025_*.png)
# Asymmetric thresholds: mean + std (drive) / mean - std (panic)
SIGMA_UPPER = {'NQ': 0.01634, 'ES': 0.01324, 'YM': 0.01259, 'GC': 0.00968}
SIGMA_LOWER = {'NQ': -0.01486, 'ES': -0.01207, 'YM': -0.01180, 'GC': -0.00896}

# --- D+1 DAILY ALPHA MATRIX (Daily σ Breach → Next-Day Direction) ---
# Source: output/charts/Multi/daily/daily_alpha_matrix_weekdays.png
# AUDITED 2026-03-04: Only edges with T ≥ 1.3 included (NOISE excluded)
# Key: (asset, weekday, type) → {signal, prob, avg_ret_d1, t_stat, grade}
DAILY_ALPHA_TRIGGERS = {
    ('NQ', 1, 'panic'):  {'signal': 'REBOUND (Miércoles)', 'prob': 55.4, 'avg_ret_d1': '+0.543%', 't_stat': 2.1, 'grade': 'GOLD (T>2.1)'},
    ('YM', 4, 'panic'):  {'signal': 'REBOUND (Lunes)',     'prob': 67.9, 'avg_ret_d1': '+0.444%', 't_stat': 1.5, 'grade': 'SILVER (T>1.5)'},
    ('NQ', 3, 'drive'):  {'signal': 'REVERSION (Viernes)', 'prob': 57.8, 'avg_ret_d1': '-0.271%', 't_stat': 1.4, 'grade': 'BRONZE (T>1.3)'},
}

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
    
    # 0. Monthly Bias (Seasonal) — Always shown from day 1
    month_df = df[(df.index.month == month) & (df.index.year == year)]
    m_signals = []
    m_bias = None

    hit_rate = MONTHLY_BIAS.get(asset, {}).get(month, None)
    if hit_rate is not None and hit_rate != 50.0:
        is_bullish = hit_rate > 50
        direction_prob = round(hit_rate, 1) if is_bullish else round(100 - hit_rate, 1)
        m_bias = "ALCISTA" if is_bullish else "BAJISTA"
        m_signals.append({
            'target': 'SESGO ALCISTA' if is_bullish else 'SESGO BAJISTA',
            'prob': direction_prob,
            'status': 'ACTIVO',
            'grade': get_grade(direction_prob),
            'color': 'green' if is_bullish else 'red'
        })

    # 1. Monthly W2 — Only show if W2 signal is LOCKED (day >= 13)
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
    
    if len(week_df) >= 2 and week_df.iloc[0].name.weekday() == 0 and week_df.iloc[1].name.weekday() == 1:
        # D2 requires Mon (d1) + Tue (d2) data. Skip holiday weeks with missing days.
        # Determine if we are past the signal activation time
        # Logic: Show if it's Wednesday or later, OR if it's Tuesday after 18:00 EST (23:00 UTC)
        now_utc = datetime.utcnow()
        show_d2 = False

        if now_utc.weekday() > 1: # Wednesday (2) onwards
            show_d2 = True
        elif now_utc.weekday() == 1: # Tuesday (1)
            # 18:00 EST = 23:00 UTC
            if now_utc.hour >= 23:
                show_d2 = True

        if show_d2:
            d1, d2 = week_df.iloc[0], week_df.iloc[1]
            hi, lo = max(float(d1['High']), float(d2['High'])), min(float(d1['Low']), float(d2['Low']))
            pos = (float(d2['Close']) - lo) / (hi - lo) if (hi - lo) != 0 else 0.5
            is_bull = pos > 0.5
            w_bias = "ALCISTA" if is_bull else "BAJISTA"
            
            if pos > 0.75:
                tier_key = 'bull_75'
                target_close = 'FUERTE ALCISTA'
            elif pos > 0.50:
                tier_key = 'bull_50'
                target_close = 'CIERRE ALCISTA'
            elif pos < 0.25:
                tier_key = 'bear_25'
                target_close = 'FUERTE BAJISTA'
            else:
                tier_key = 'bear_50'
                target_close = 'CIERRE BAJISTA'

            curr_lo, curr_hi = float(week_df['Low'].min()), float(week_df['High'].max())
            
            seasonal = WEEKLY_SEASONAL.get(asset, {}).get(month, None)
            if seasonal:
                p_set = seasonal.get(tier_key)
                if p_set:
                    if is_bull:
                        w_signals.append({'target': target_close, 'prob': p_set['prob_green'], 'status': 'ACTIVO', 'grade': get_grade(p_set['prob_green']), 'color': 'green'})
                        s = 'COMPLETADO' if curr_hi > hi else 'PENDIENTE'
                        w_signals.append({'target': 'NUEVO ALTO', 'prob': p_set['prob_high'], 'status': s, 'grade': get_grade(p_set['prob_high']), 'color': 'green' if s=='PENDIENTE' else 'green'})
                    else:
                        w_signals.append({'target': target_close, 'prob': p_set['prob_red'], 'status': 'ACTIVO', 'grade': get_grade(p_set['prob_red']), 'color': 'red'})
                        s = 'COMPLETADO' if curr_lo < lo else 'PENDIENTE'
                        w_signals.append({'target': 'NUEVO BAJO', 'prob': p_set['prob_low'], 'status': s, 'grade': get_grade(p_set['prob_low']), 'color': 'red' if s=='PENDIENTE' else 'green'})

    # 3. Weekly Alpha Matrix (Mean Reversion only — Bull Momentum removed, T < 1)
    # Check if the PREVIOUS WEEK closed beyond mean reversion threshold
    previous_week = (last_date - pd.Timedelta(days=7)).isocalendar()[1]
    prev_week_df = df[(df.index.isocalendar().week == previous_week) & (df.index.isocalendar().year == (last_date - pd.Timedelta(days=7)).year)]

    alpha_signals = []
    if not prev_week_df.empty:
        pw_open = float(prev_week_df['Open'].iloc[0])
        pw_close = float(prev_week_df['Close'].iloc[-1])
        pw_ret = (pw_close - pw_open) / pw_open

        a_matrix = WEEKLY_ALPHA_MATRIX.get(asset)
        if a_matrix and pw_ret <= a_matrix['mean_reversion']['threshold']:
            r = a_matrix['mean_reversion']
            alpha_signals.append({'target': r['target'], 'prob': r['prob'], 'status': 'ACTIVO', 'grade': r['grade'], 'color': 'green'})

    # 3b. Weekly Bias & Inertia (Daily σ Breach → Weekly Close Direction)
    # Scan this week's completed bars for σ breaches that predict weekly close
    s_upper = SIGMA_UPPER.get(asset, 0.013)
    s_lower = SIGMA_LOWER.get(asset, -0.013)
    bias_candidates = []

    for idx in range(len(week_df)):
        bar = week_df.iloc[idx]
        bar_o, bar_c = float(bar['Open']), float(bar['Close'])
        bar_o2c = (bar_c - bar_o) / bar_o if bar_o != 0 else 0
        bar_weekday = bar.name.weekday()
        bar_day_name = DAY_NAMES[bar_weekday] if bar_weekday < 7 else '?'

        if bar_o2c > s_upper:
            trigger = WEEKLY_BIAS_TRIGGERS.get((asset, bar_weekday, 'drive'))
            if trigger:
                bias_candidates.append({**trigger, 'day_name': bar_day_name, 'o2c': bar_o2c})
        elif bar_o2c < s_lower:
            trigger = WEEKLY_BIAS_TRIGGERS.get((asset, bar_weekday, 'panic'))
            if trigger:
                bias_candidates.append({**trigger, 'day_name': bar_day_name, 'o2c': bar_o2c})

    bias_signals = []
    if bias_candidates:
        best = max(bias_candidates, key=lambda x: x['prob'])
        is_bull = best['direction'] == 'BULL'
        bias_signals.append({
            'target': f'SESGO SEMANAL {"ALCISTA" if is_bull else "BAJISTA"}',
            'prob': best['prob'],
            'status': 'ACTIVO',
            'grade': best['grade'],
            'color': 'green' if is_bull else 'red',
            'val': f'{best["day_name"]} cerró {best["o2c"]*100:+.2f}% → Avg {best["avg_ret"]}/sem'
        })
        # Set weekly bias if D2 hasn't set it yet
        if w_bias is None:
            w_bias = "ALCISTA" if is_bull else "BAJISTA"

    # 4. Daily Layer — D+1 Alpha (Yesterday's σ breach → TODAY's prediction)
    # Check the PREVIOUS bar for sigma breach — the signal appears on the prediction day
    d_signals = []
    if len(df) >= 2:
        prev_bar = df.iloc[-2]
        prev_o = float(prev_bar['Open'])
        prev_c = float(prev_bar['Close'])
        prev_o2c = (prev_c - prev_o) / prev_o if prev_o != 0 else 0
        prev_weekday = prev_bar.name.weekday()
        prev_day_name = DAY_NAMES[prev_weekday] if prev_weekday < 7 else '?'

        s_upper_d = SIGMA_UPPER.get(asset, 0.013)
        s_lower_d = SIGMA_LOWER.get(asset, -0.013)

        if prev_o2c > s_upper_d:
            d1_trigger = DAILY_ALPHA_TRIGGERS.get((asset, prev_weekday, 'drive'))
            if d1_trigger:
                d_signals.append({
                    'target': d1_trigger['signal'],
                    'prob': d1_trigger['prob'],
                    'status': 'ACTIVO',
                    'grade': d1_trigger['grade'],
                    'color': 'red' if 'REVERSION' in d1_trigger['signal'] else 'green',
                    'val': f'{prev_day_name} cerró {prev_o2c*100:+.2f}% (DRIVE) → Avg D+1 {d1_trigger["avg_ret_d1"]}'
                })
        elif prev_o2c < s_lower_d:
            d1_trigger = DAILY_ALPHA_TRIGGERS.get((asset, prev_weekday, 'panic'))
            if d1_trigger:
                d_signals.append({
                    'target': d1_trigger['signal'],
                    'prob': d1_trigger['prob'],
                    'status': 'ACTIVO',
                    'grade': d1_trigger['grade'],
                    'color': 'green' if 'REBOUND' in d1_trigger['signal'] else 'red',
                    'val': f'{prev_day_name} cerró {prev_o2c*100:+.2f}% (PANIC) → Avg D+1 {d1_trigger["avg_ret_d1"]}'
                })

    return {
        'monthly': {'bias': m_bias, 'signals': m_signals},
        'weekly': {'bias': w_bias, 'signals': w_signals + alpha_signals + bias_signals},
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
