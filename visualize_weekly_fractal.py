import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from src.data.data_loader import DataLoader
import numpy as np
import os

# VISUAL STYLE GUIDE (Consistente con todo el proyecto)
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

def visualize_weekly_fractal_summary():
    print(f"\nGenerando imagen resumen del patrón semanal D2...")
    
    loader = DataLoader()
    assets = ['NQ', 'ES', 'DJI', 'GC']
    summary_data = []
    
    for asset in assets:
        data = loader.download(asset, start_date='2000-01-01')
        if data.empty: continue

        data['iso_year'] = data.index.isocalendar().year
        data['week_of_year'] = data.index.isocalendar().week
        
        weekly_groups = data.groupby(['iso_year', 'week_of_year'])
        results = []
        
        for (year, week), week_data in weekly_groups:
            if len(week_data) < 2: continue
            
            d1_data = week_data.iloc[0]
            d2_data = week_data.iloc[1]
            
            d1_d2_high = max(d1_data['high'], d2_data['high'])
            d1_d2_low = min(d1_data['low'], d2_data['low'])
            rng = d1_d2_high - d1_d2_low
            if rng == 0: continue
                
            midpoint = d1_d2_low + (rng * 0.5)
            d2_close = d2_data['close']
            
            if len(week_data) <= 2: continue
            
            week_open = week_data.iloc[0]['open']
            week_close = week_data.iloc[-1]['close']
            is_green_week = week_close > week_open
            
            rest_of_week = week_data.iloc[2:]
            rest_high = rest_of_week['high'].max()
            rest_low = rest_of_week['low'].min()
            
            made_new_high = rest_high > d1_d2_high
            made_new_low = rest_low < d1_d2_low
            
            results.append({
                'is_bull_signal': d2_close > midpoint,
                'is_green_week': is_green_week,
                'made_new_high': made_new_high,
                'made_new_low': made_new_low
            })
            
        df = pd.DataFrame(results)
        if df.empty: continue
            
        # Stats
        bull = df[df['is_bull_signal']]
        bear = df[~df['is_bull_signal']]
        
        bull_win = (bull['is_green_week'].sum() / len(bull)) * 100
        bull_ext = (bull['made_new_high'].sum() / len(bull)) * 100
        
        bear_win = ((~bear['is_green_week']).sum() / len(bear)) * 100
        bear_ext = (bear['made_new_low'].sum() / len(bear)) * 100
        
        summary_data.append([bull_win, bull_ext, bear_win, bear_ext])
        
    heatmap_arr = np.array(summary_data)
    
    # PLOTTING
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot Heatmap
    im = ax.imshow(heatmap_arr, cmap='RdYlGn', vmin=40, vmax=100, aspect='auto')
    
    # Axis Labels
    ax.set_xticks(np.arange(4))
    ax.set_yticks(np.arange(len(assets)))
    
    # X Axis Labels (Top)
    # Using 2 lines for clarity
    labels = [
        'BULL SIGNAL (>50%)\nProb Green Week', 
        'BULL SIGNAL (>50%)\nProb New High', 
        'BEAR SIGNAL (<50%)\nProb Red Week', 
        'BEAR SIGNAL (<50%)\nProb New Low'
    ]
    ax.set_xticklabels(labels, fontsize=11, fontweight='bold')
    ax.xaxis.tick_top()
    
    # Y Axis Labels
    ax.set_yticklabels(assets, fontsize=14, fontweight='bold')
    
    # Add Values inside Cells
    for i in range(len(assets)):
        for j in range(4):
            val = heatmap_arr[i, j]
            text = f"{val:.1f}%"
            if val >= 75: text += " *" # Star for top tier
            
            # Text Color: Black for readability on colors
            ax.text(j, i, text, ha="center", va="center", color='black', fontweight='bold', fontsize=16)
            
    # Add Separator Line
    ax.axvline(1.5, color='white', linewidth=3)
    
    # Headers
    plt.suptitle(f'WEEKLY FRACTAL STRATEGY (D2 SIGNAL)', fontsize=20, fontweight='bold', color=TEXT_COLOR, y=0.02)
    ax.set_title("Based on Tuesday Close relative to Mon-Tue Range (50% Level)", fontsize=12, color=GRAY_TEXT, pad=50)
    
    # Cleanup
    ax.spines[:].set_visible(False)
    ax.tick_params(top=False, bottom=False, left=False, right=False)
    
    # Create Output Dir
    output_dir = 'output/charts/strategy'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"{output_dir}/weekly_fractal_summary.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {filename}")
    plt.close()

if __name__ == "__main__":
    visualize_weekly_fractal_summary()
