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

def visualize_weekly_continuation_styled():
    print(f"\nGenerando tabla de continuación semanal COMPLETA (Bull/Bear)...")
    
    loader = DataLoader()
    assets = ['NQ', 'ES', 'DJI', 'GC']
    rows = []
    
    for asset in assets:
        data = loader.download(asset, start_date='2000-01-01')
        if data.empty: continue

        data['iso_year'] = data.index.isocalendar().year
        data['week_of_year'] = data.index.isocalendar().week
        
        weekly_groups = data.groupby(['iso_year', 'week_of_year'])
        asset_results_bull = []
        asset_results_bear = []
        
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
            
            # --- BULL SCENARIO ---
            if d2_close > midpoint:
                # Condition: D3 Breakout (New High)
                d3_high = d3_data['high']
                if d3_high > d1_d2_high:
                    rest_of_week = week_data.iloc[3:] 
                    rest_high = rest_of_week['high'].max()
                    continued_higher = rest_high > d3_high # D4/D5 > D3 High
                    
                    week_open = week_data.iloc[0]['open']
                    week_close = week_data.iloc[-1]['close']
                    closed_green = week_close > week_open
                    
                    d3_close = d3_data['close']
                    closed_higher_than_d3 = week_close > d3_close
                    
                    asset_results_bull.append({
                        'continued': continued_higher,
                        'closed_fav': closed_green, # Green
                        'held_gains': closed_higher_than_d3
                    })

            # --- BEAR SCENARIO ---
            else: # d2_close <= midpoint
                # Condition: D3 Breakout (New Low)
                d3_low = d3_data['low']
                if d3_low < d1_d2_low:
                    rest_of_week = week_data.iloc[3:] 
                    rest_low = rest_of_week['low'].min()
                    continued_lower = rest_low < d3_low # D4/D5 < D3 Low
                    
                    week_open = week_data.iloc[0]['open']
                    week_close = week_data.iloc[-1]['close']
                    closed_red = week_close < week_open
                    
                    d3_close = d3_data['close']
                    closed_lower_than_d3 = week_close < d3_close
                    
                    asset_results_bear.append({
                        'continued': continued_lower,
                        'closed_fav': closed_red, # Red
                        'held_gains': closed_lower_than_d3
                    })
            
        # Calc Stats
        df_bull = pd.DataFrame(asset_results_bull)
        df_bear = pd.DataFrame(asset_results_bear)
        
        # Bull Stats
        if not df_bull.empty:
            b_cont = (df_bull['continued'].sum() / len(df_bull)) * 100
            b_green = (df_bull['closed_fav'].sum() / len(df_bull)) * 100
            b_hold = (df_bull['held_gains'].sum() / len(df_bull)) * 100
        else:
            b_cont, b_green, b_hold = 0, 0, 0
            
        # Bear Stats
        if not df_bear.empty:
            ba_cont = (df_bear['continued'].sum() / len(df_bear)) * 100
            ba_red = (df_bear['closed_fav'].sum() / len(df_bear)) * 100
            ba_hold = (df_bear['held_gains'].sum() / len(df_bear)) * 100
        else:
            ba_cont, ba_red, ba_hold = 0, 0, 0
            
        rows.append([b_cont, b_green, b_hold, ba_cont, ba_red, ba_hold])
        
    # PLOTTING TABLE IMAGE (Styled)
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis('off')
    
    col_labels = [
        'BULL: HIGHER HIGH\n(Thu/Fri > Wed)', 'BULL: CLOSE GREEN\n(Safety Check)', 'BULL: CLOSE > WED\n(Hold Potential)',
        'BEAR: LOWER LOW\n(Thu/Fri < Wed)', 'BEAR: CLOSE RED\n(Safety Check)', 'BEAR: CLOSE < WED\n(Hold Potential)'
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
            if val > 75: 
                text += " *"
                if j < 3: bg = ACCENT_GREEN_DIM # Bull Cols 0-2
                else: bg = ACCENT_RED_DIM   # Bear Cols 3-5
            elif val < 60:
                if j == 2 or j == 5: text += " !" # Warning on Hold Potential only
            
            row_text.append(text)
            row_colors.append(bg)
            
        cell_text.append(row_text)
        cell_colors.append(row_colors)
        
    table = ax.table(cellText=cell_text, colLabels=col_labels, rowLabels=assets, 
                     cellColours=cell_colors, loc='center', cellLoc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 3) 
    
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
                    if col < 3: cell.set_text_props(weight='bold', color=ACCENT_GREEN)
                    else: cell.set_text_props(weight='bold', color=ACCENT_RED)
                elif (col == 2 or col == 5) and val < 60:
                     cell.set_text_props(weight='bold', color=ACCENT_RED) # Danger hold

    plt.suptitle("WEEKLY CONTINUATION PROBABILITIES (POST-D3 BREAKOUT)", fontsize=20, fontweight='bold', color=TEXT_COLOR, y=0.95)
    plt.text(0.5, 0.90, "SCENARIO: D2 SIGNAL CONFIRMED AND D3 ALREADY BROKE OUT (NEW HIGH/LOW)", ha='center', color=GRAY_TEXT, fontsize=12)
    plt.text(0.5, 0.05, "* = STRONG CONTINUATION (>75%) | ! = HIGH REVERSAL RISK (<60% HOLD RATE)", ha='center', fontsize=10, color=GRAY_TEXT, transform=fig.transFigure)
    
    output_dir = 'output/charts/strategy'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"{output_dir}/weekly_continuation_styled.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor=BG_COLOR)
    print(f"Chart saved to: {filename}")
    plt.close()

if __name__ == "__main__":
    visualize_weekly_continuation_styled()
