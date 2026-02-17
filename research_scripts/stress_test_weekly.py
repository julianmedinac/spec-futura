import pandas as pd
import numpy as np
from scipy import stats
from src.data.data_loader import DataLoader
import matplotlib.pyplot as plt

# VISUAL STYLE GUIDE
BG_COLOR = '#000000'
TEXT_COLOR = '#ffffff'
ACCENT_GREEN = '#00ff44'
ACCENT_RED = '#ff0044'
GRAY_TEXT = '#888888'
LINE_COLOR = '#333333'
FONT_FAMILY = 'monospace'

plt.rcParams.update({
    'axes.facecolor': BG_COLOR,
    'figure.facecolor': BG_COLOR,
    'axes.edgecolor': LINE_COLOR,
    'axes.labelcolor': TEXT_COLOR,
    'xtick.color': GRAY_TEXT,
    'ytick.color': GRAY_TEXT,
    'text.color': TEXT_COLOR,
    'font.family': FONT_FAMILY
})

def stress_test_weekly_fractal(asset_key):
    print(f"\n====================================================================================================")
    print(f"STRESS TESTING WEEKLY FRACTAL FOR {asset_key} (T-TEST & P-VALUES)")
    print(f"====================================================================================================")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    results = []
    
    # Baseline for Win Rates (50/50 assumption for significance test, or observed mean?)
    # We will test against 50% random chance for direction/extensions
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 2: continue
        d1_data = week_data.iloc[0]
        d2_data = week_data.iloc[1]
        
        signal_month = d2_data.name.month 
        
        d1_d2_high = max(d1_data['high'], d2_data['high'])
        d1_d2_low = min(d1_data['low'], d2_data['low'])
        rng = d1_d2_high - d1_d2_low
        if rng == 0: continue
            
        midpoint = d1_d2_low + (rng * 0.5)
        d2_close = d2_data['close']
        
        is_bull_signal = d2_close > midpoint
        
        if len(week_data) <= 2: continue
        
        # Outcomes
        rest_of_week = week_data.iloc[2:]
        rest_high = rest_of_week['high'].max()
        rest_low = rest_of_week['low'].min()
        made_new_high = rest_high > d1_d2_high
        made_new_low = rest_low < d1_d2_low
        
        week_open = week_data.iloc[0]['open']
        week_close = week_data.iloc[-1]['close']
        is_green_week = week_close > week_open
        
        results.append({
            'month': signal_month,
            'is_bull_signal': is_bull_signal,
            'made_new_high': 1 if made_new_high else 0,
            'made_new_low': 1 if made_new_low else 0,
            'is_green_week': 1 if is_green_week else 0,
            'is_red_week': 1 if not is_green_week else 0
        })
        
    df = pd.DataFrame(results)
    
    month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    significant_findings = []
    
    print(f"{'Month':<5} | {'Signal':<10} | {'Outcome':<15} | {'Win Rate':<8} | {'P-Value':<10} | {'Verdict'}")
    print(f"{'-'*5}-|-{'-'*10}-|-{'-'*15}-|-{'-'*8}-|-{'-'*10}-|-{'-'*10}")
    
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        if m_df.empty: continue
        
        # --- BULL SIGNAL TESTS ---
        bull = m_df[m_df['is_bull_signal']]
        if len(bull) > 10:
            # Test: New High
            wr_high = bull['made_new_high'].mean()
            # T-test against 0.5 (Random)
            t_stat, p_val = stats.ttest_1samp(bull['made_new_high'], 0.5, alternative='greater')
            
            if p_val < 0.05 and wr_high > 0.70:
                verdict = "SIGNIFICANT"
                print(f"{month_names[m-1]:<5} | {'BULL':<10} | {'New High':<15} | {wr_high*100:5.1f}%  | {p_val:.4f}     | {verdict}")
                significant_findings.append([month_names[m-1], 'BULL', 'NEW HIGH', wr_high*100, p_val])
            
            # Test: Green Week
            wr_green = bull['is_green_week'].mean()
            t_stat, p_val = stats.ttest_1samp(bull['is_green_week'], 0.5, alternative='greater')
            
            if p_val < 0.05 and wr_green > 0.70:
                print(f"{month_names[m-1]:<5} | {'BULL':<10} | {'Green Week':<15} | {wr_green*100:5.1f}%  | {p_val:.4f}     | SIGNIFICANT")
                # significant_findings.append([month_names[m-1], 'BULL', 'GREEN WEEK', wr_green*100, p_val]) # Optional to add to list

        # --- BEAR SIGNAL TESTS ---
        bear = m_df[~m_df['is_bull_signal']]
        if len(bear) > 10:
            # Test: New Low
            wr_low = bear['made_new_low'].mean()
            t_stat, p_val = stats.ttest_1samp(bear['made_new_low'], 0.5, alternative='greater')
            
            if p_val < 0.05 and wr_low > 0.70:
                verdict = "SIGNIFICANT"
                print(f"{month_names[m-1]:<5} | {'BEAR':<10} | {'New Low':<15}  | {wr_low*100:5.1f}%  | {p_val:.4f}     | {verdict}")
                significant_findings.append([month_names[m-1], 'BEAR', 'NEW LOW', wr_low*100, p_val])

            # Test: Red Week
            wr_red = bear['is_red_week'].mean()
            t_stat, p_val = stats.ttest_1samp(bear['is_red_week'], 0.5, alternative='greater')
            
            if p_val < 0.05 and wr_red > 0.70:
               print(f"{month_names[m-1]:<5} | {'BEAR':<10} | {'Red Week':<15}  | {wr_red*100:5.1f}%  | {p_val:.4f}     | SIGNIFICANT")

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        stress_test_weekly_fractal(asset)
