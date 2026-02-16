import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from scipy import stats
from src.data.data_loader import DataLoader

# VISUAL STYLE GUIDE (Strict Adherence)
BG_COLOR = '#000000'
TEXT_COLOR = '#ffffff'
ACCENT_GREEN = '#00ff44'
ACCENT_GREEN_DIM = '#003311' # Dark green background
ACCENT_RED = '#ff0044'
ACCENT_RED_DIM = '#330011' # Dark red background
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

def export_weekly_fractal_table_styled(asset_key):
    print(f"\nGenerando tabla semanal mensual (Styled & Stress Tested) para {asset_key}...")
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    results = []
    
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
            'made_new_high': made_new_high,
            'made_new_low': made_new_low,
            'is_green_week': is_green_week
        })
        
    df = pd.DataFrame(results)
    month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    # Table Data
    table_data = [] # List of lists of tuples (value, is_significant)
    
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        if m_df.empty: 
            table_data.append([(0, False), (0, False), (0, False), (0, False)])
            continue
        
        # Helper for stats
        def get_stats(series):
            if len(series) < 5: return 0.0, False
            mean = series.mean()
            # One-sample t-test against 0.5 (random chance)
            t_stat, p_val = stats.ttest_1samp(series, 0.5, alternative='two-sided')
            # Criteria: Significant (p<0.05) AND Strong Edge (>75%)
            is_sig = (p_val < 0.05) and (mean > 0.75) 
            return mean * 100, is_sig

        # Bull Signal
        bull = m_df[m_df['is_bull_signal']]
        prob_high, sig_high = get_stats(bull['made_new_high'])
        prob_green, sig_green = get_stats(bull['is_green_week'])
            
        # Bear Signal
        bear = m_df[~m_df['is_bull_signal']]
        prob_low, sig_low = get_stats(bear['made_new_low'])
        prob_red, sig_red = get_stats(~bear['is_green_week']) # Note ~ for red
            
        table_data.append([(prob_high, sig_high), (prob_green, sig_green), 
                           (prob_low, sig_low), (prob_red, sig_red)])
        
    # PLOTTING TABLE IMAGE (Styled)
    fig, ax = plt.subplots(figsize=(14, 12)) 
    ax.axis('off')
    
    # Titles
    plt.suptitle(f"{asset_key} WEEKLY FRACTAL SEASONALITY (D2 SIGNAL)", fontsize=22, fontweight='bold', color=TEXT_COLOR, y=0.95)
    plt.text(0.5, 0.90, "PROBABILITY OF OUTCOMES IF TUESDAY CLOSES >/< 50% OF MON-TUE RANGE", ha='center', color=GRAY_TEXT, fontsize=12)
    
    # Column Labels
    col_labels = ['BULL SIG (>50%)\nProb New High', 'BULL SIG (>50%)\nProb Green Close', 'BEAR SIG (<50%)\nProb New Low', 'BEAR SIG (<50%)\nProb Red Close']
    
    # Calculate cell colors and text
    cell_colors = []
    cell_text = []
    
    for i, row in enumerate(table_data):
        row_colors = []
        row_text = []
        for j, (val, is_sig) in enumerate(row):
            text = f"{val:.1f}%"
            # Color Logic
            bg = BG_COLOR # Default Black
            if is_sig:
                text += " *"
                if j < 2: # Bull Columns
                    bg = ACCENT_GREEN_DIM 
                else: # Bear Columns
                    bg = ACCENT_RED_DIM
            elif val > 75: 
                 pass # High prob but not significant

            row_colors.append(bg)
            row_text.append(text)
        cell_colors.append(row_colors)
        cell_text.append(row_text)
        
    # Create Table
    table = ax.table(cellText=cell_text, colLabels=col_labels, rowLabels=month_names, 
                     cellColours=cell_colors, loc='center', cellLoc='center')
    
    # Detailed Styling
    table.auto_set_font_size(False)
    table.set_fontsize(14)
    table.scale(1, 2.5) # Taller rows
    
    # Header Styling
    for (row, col), cell in table.get_celld().items():
        if row == 0: # Header Row
            cell.set_text_props(weight='bold', color=TEXT_COLOR)
            cell.set_facecolor(LINE_COLOR) # Dark Gray Header
            cell.set_linewidth(1)
            cell.set_edgecolor(BG_COLOR)
        elif col == -1: # Row Labels (Months)
            cell.set_text_props(weight='bold', color=GRAY_TEXT)
            cell.set_facecolor(BG_COLOR)
            cell.set_edgecolor(BG_COLOR)
        else: # Data Cells
            cell.set_edgecolor(LINE_COLOR)
            cell.set_linewidth(0.5)
            cell.set_text_props(color=TEXT_COLOR)
            
            # Highlight Text Color for High Prob
            if col >= 0 and row > 0:
                val, is_sig = table_data[row-1][col]
                if is_sig:
                    if col < 2:
                        cell.set_text_props(weight='bold', color=ACCENT_GREEN)
                    else:
                        cell.set_text_props(weight='bold', color=ACCENT_RED)
                    
    # Termination Line and Footer
    plt.text(0.5, 0.05, "* = STATISTICALLY SIGNIFICANT (p<0.05) & >75% PROBABILITY", ha='center', fontsize=10, color=GRAY_TEXT, transform=fig.transFigure)

    # Save
    output_dir = 'output/charts/strategy'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"{output_dir}/{asset_key}_weekly_fractal_seasonality_styled.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor=BG_COLOR)
    print(f"Chart saved to: {filename}")
    plt.close()

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        export_weekly_fractal_table_styled(asset)
