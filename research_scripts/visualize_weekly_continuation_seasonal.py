import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
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

def visualize_weekly_continuation_seasonal(asset_key):
    print(f"\nGenerando tabla de continuación semanal ESTACIONAL para {asset_key}...")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['iso_year', 'week_of_year'])
    results = []
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue 
        
        d1_data = week_data.iloc[0]
        d2_data = week_data.iloc[1]
        d3_data = week_data.iloc[2]
        
        d1_d2_high = max(d1_data['high'], d2_data['high'])
        d1_d2_low = min(d1_data['low'], d2_data['low'])
        rng = d1_d2_high - d1_d2_low
        if rng == 0: continue
            
        midpoint = d1_d2_low + (rng * 0.5)
        d2_close = d2_data['close']
        signal_month = d2_data.name.month 
        
        if d2_close > midpoint:
             # --- BULL SCENARIO ---
            d3_high = d3_data['high']
            if d3_high > d1_d2_high:
                rest_of_week = week_data.iloc[3:] 
                rest_high = rest_of_week['high'].max()
                continued_higher = rest_high > d3_high 
                
                week_open = week_data.iloc[0]['open']
                week_close = week_data.iloc[-1]['close']
                closed_green = week_close > week_open
                
                d3_close = d3_data['close']
                closed_higher_than_d3 = week_close > d3_close
                
                results.append({
                    'month': signal_month,
                    'type': 'BULL',
                    'continued': continued_higher,
                    'closed_fav': closed_green,
                    'held_gains': closed_higher_than_d3
                })

        else: 
            # --- BEAR SCENARIO ---
            d3_low = d3_data['low']
            if d3_low < d1_d2_low:
                rest_of_week = week_data.iloc[3:] 
                rest_low = rest_of_week['low'].min()
                continued_lower = rest_low < d3_low
                
                week_open = week_data.iloc[0]['open']
                week_close = week_data.iloc[-1]['close']
                closed_red = week_close < week_open
                
                d3_close = d3_data['close']
                closed_lower_than_d3 = week_close < d3_close
                
                results.append({
                    'month': signal_month,
                    'type': 'BEAR',
                    'continued': continued_lower,
                    'closed_fav': closed_red,
                    'held_gains': closed_lower_than_d3
                })

    df = pd.DataFrame(results)
    if df.empty: return

    month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    rows = []
    
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        
        # Bull Stats
        bull = m_df[m_df['type'] == 'BULL']
        if not bull.empty and len(bull) >= 3:
            b_cont = (bull['continued'].sum() / len(bull)) * 100
            b_green = (bull['closed_fav'].sum() / len(bull)) * 100
            b_hold = (bull['held_gains'].sum() / len(bull)) * 100
        else:
            b_cont, b_green, b_hold = 0, 0, 0

        # Bear Stats
        bear = m_df[m_df['type'] == 'BEAR']
        if not bear.empty and len(bear) >= 3:
            ba_cont = (bear['continued'].sum() / len(bear)) * 100
            ba_red = (bear['closed_fav'].sum() / len(bear)) * 100
            ba_hold = (bear['held_gains'].sum() / len(bear)) * 100
        else:
            ba_cont, ba_red, ba_hold = 0, 0, 0
            
        rows.append([b_cont, b_green, b_hold, ba_cont, ba_red, ba_hold])

    # PLOTTING TABLE IMAGE (Styled)
    fig, ax = plt.subplots(figsize=(16, 12)) # Wider
    ax.axis('off')
    
    col_labels = [
        'BULL: HIGHER HIGH\n(Thu/Fri > Wed)', 'BULL: GREEN WEEK\n(Safety)', 'BULL: HOLD GAINS\n(Close > Wed)',
        'BEAR: LOWER LOW\n(Thu/Fri < Wed)', 'BEAR: RED WEEK\n(Safety)', 'BEAR: HOLD LOWS\n(Close < Wed)'
    ]
    
    cell_text = []
    cell_colors = []
    
    for i, row in enumerate(rows):
        row_text = []
        row_colors = []
        for j, val in enumerate(row):
            text = f"{val:.1f}%"
            bg = BG_COLOR
            
            # Logic for highlighting
            # HIGH PROBABILITY (>75%) = GREEN (Good Signal)
            if val > 75: 
                text += " *"
                bg = ACCENT_GREEN_DIM 
            
            # Specific Warning Logic for HOLD columns (2 and 5)
            if (j == 2 or j == 5):
                if val < 50:
                    text += " !"
                    bg = ACCENT_RED_DIM # DANGER: Low probability of holding gains
                elif val > 60:
                    text += " *"
                    bg = ACCENT_GREEN_DIM # GOOD: High probability of holding gains (Rare)
            
            row_text.append(text)
            row_colors.append(bg)
            
        cell_text.append(row_text)
        cell_colors.append(row_colors)
        
    table = ax.table(cellText=cell_text, colLabels=col_labels, rowLabels=month_names, 
                     cellColours=cell_colors, loc='center', cellLoc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2.5) 
    
    # Header Styling
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color=TEXT_COLOR)
            cell.set_facecolor(LINE_COLOR)
            cell.set_edgecolor(BG_COLOR)
        elif col == -1:
            cell.set_text_props(weight='bold', color=GRAY_TEXT)
            cell.set_facecolor(BG_COLOR)
            cell.set_edgecolor(BG_COLOR)
        else:
            cell.set_text_props(color=TEXT_COLOR)
            cell.set_edgecolor(LINE_COLOR)
            
            if col >= 0 and row > 0:
                val = rows[row-1][col]
                # Dynamic Text Color
                if val > 75:
                    cell.set_text_props(weight='bold', color=ACCENT_GREEN)
                elif val < 50 and (col == 2 or col == 5):
                     cell.set_text_props(weight='bold', color=ACCENT_RED) # Danger hold

    plt.suptitle(f"{asset_key} WEEKLY CONTINUATION SEASONALITY (BULL & BEAR)", fontsize=20, fontweight='bold', color=TEXT_COLOR, y=0.95)
    plt.text(0.5, 0.90, "SCENARIO: D2 SIGNAL & D3 BREAKOUT -> PROB OF EXTENSION VS HOLDING GAINS", ha='center', color=GRAY_TEXT, fontsize=12)
    plt.text(0.5, 0.05, "* = STRONG ODDS (>75%) | ! = EXTENSIVE REVERSAL RISK (<50% HOLD)", ha='center', fontsize=10, color=GRAY_TEXT, transform=fig.transFigure)
    
    output_dir = 'output/charts/strategy'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"{output_dir}/{asset_key}_weekly_continuation_seasonal.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor=BG_COLOR)
    print(f"Chart saved to: {filename}")
    plt.close()

if __name__ == "__main__":
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        visualize_weekly_continuation_seasonal(asset)
