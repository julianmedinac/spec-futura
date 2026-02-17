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

def visualize_weekly_continuation_table():
    print(f"\nGenerando tabla de continuación semanal (D3 Breakout)...")
    
    loader = DataLoader()
    assets = ['NQ', 'ES', 'DJI', 'GC']
    rows = []
    
    for asset in assets:
        data = loader.download(asset, start_date='2000-01-01')
        if data.empty: continue

        data['iso_year'] = data.index.isocalendar().year
        data['week_of_year'] = data.index.isocalendar().week
        
        weekly_groups = data.groupby(['iso_year', 'week_of_year'])
        asset_results = []
        
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
            
            # Condition 1: D2 Bull Signal
            if d2_close <= midpoint: continue
            
            # Condition 2: D3 Breakout (New High)
            d3_high = d3_data['high']
            made_new_high_d3 = d3_high > d1_d2_high
            if not made_new_high_d3: continue
            
            # Outcome A: Further Highs D4/D5
            rest_of_week = week_data.iloc[3:] 
            rest_high = rest_of_week['high'].max()
            continued_higher = rest_high > d3_high
            
            # Outcome B: Weekly Close Green
            week_open = week_data.iloc[0]['open']
            week_close = week_data.iloc[-1]['close']
            closed_green = week_close > week_open
            
            # Outcome C: Close > D3 Close
            d3_close = d3_data['close']
            closed_higher_than_d3 = week_close > d3_close
            
            asset_results.append({
                'continued_higher': continued_higher,
                'closed_green': closed_green,
                'closed_higher_than_d3': closed_higher_than_d3
            })
            
        df = pd.DataFrame(asset_results)
        if df.empty: continue
        
        n = len(df)
        prob_cont = (df['continued_higher'].sum() / n) * 100
        prob_green = (df['closed_green'].sum() / n) * 100
        prob_hold = (df['closed_higher_than_d3'].sum() / n) * 100
        
        rows.append([prob_cont, prob_green, prob_hold])
        
    # PLOTTING TABLE IMAGE
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')
    
    col_labels = ['EXTEND HIGHER (THU/FRI)\n(Prob > Wed High)', 'CLOSE WEEK GREEN\n(Safety Check)', 'CLOSE > WED CLOSE\n(Hold Potential)']
    
    cell_text = []
    cell_colors = []
    
    for i, row in enumerate(rows):
        row_text = []
        row_colors = []
        for j, val in enumerate(row):
            text = f"{val:.1f}%"
            bg = BG_COLOR
            
            if j == 0 and val > 65: # Continuation Prob
                text += " *"
                bg = ACCENT_GREEN_DIM
            elif j == 1 and val > 80: # Safety Check
                text += " *"
                bg = ACCENT_GREEN_DIM
            elif j == 2 and val < 60: # Hold Risk
                text += " !"
                bg = ACCENT_RED # Warning
                
            row_text.append(text)
            row_colors.append(bg)
            
        cell_text.append(row_text)
        cell_colors.append(row_colors)
        
    table = ax.table(cellText=cell_text, colLabels=col_labels, rowLabels=assets, 
                     cellColours=cell_colors, loc='center', cellLoc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(14)
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
                if col == 0 and val > 65: cell.set_text_props(weight='bold', color=ACCENT_GREEN)
                if col == 1 and val > 80: cell.set_text_props(weight='bold', color=ACCENT_GREEN)
                if col == 2 and val < 60: cell.set_text_props(weight='bold', color=ACCENT_RED) # Danger

    plt.suptitle("WEEKLY CONTINUATION PROBABILITIES (POST-D3 BREAKOUT)", fontsize=16, fontweight='bold', color=TEXT_COLOR, y=0.92)
    plt.text(0.5, 0.86, "SCENARIO: TUESDAY BULLISH (>50%) AND WEDNESDAY ALREADY BROKE OUT", ha='center', color=GRAY_TEXT, fontsize=10)
    plt.text(0.5, 0.05, "* = STRONG SIGNAL | ! = WARNING (TAKE PROFITS)", ha='center', fontsize=10, color=GRAY_TEXT, transform=fig.transFigure)
    
    output_dir = 'output/charts/strategy'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"{output_dir}/weekly_continuation_table.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor=BG_COLOR)
    print(f"Chart saved to: {filename}")
    plt.close()

if __name__ == "__main__":
    visualize_weekly_continuation_table()
