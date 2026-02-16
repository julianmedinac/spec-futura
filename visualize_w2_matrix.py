import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from src.data.data_loader import DataLoader
import numpy as np
import os
from datetime import datetime

# VISUAL STYLE GUIDE
BG_COLOR = '#000000'
TEXT_COLOR = '#ffffff'
ACCENT_GREEN = '#00ff44'
ACCENT_GREEN_DIM = '#006611' # For backgrounds
ACCENT_RED = '#ff0044'
ACCENT_RED_DIM = '#660011' # For backgrounds
ACCENT_NEUTRAL = '#444444' # Gray
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

def visualize_w2_signal_matrix(asset_key):
    print(f"\nGenerando matriz de probabilidad W2 para {asset_key}...")
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['year', 'month'])
    
    results = []
    
    for (year, month), month_data in weekly_groups:
        # FIX: Use drop_duplicates() to preserve chronological order. 
        # sorted() causes bugs in December (e.g., sorting week 52 and week 1 -> [1, 52] which flips order)
        weeks = month_data['week_of_year'].drop_duplicates().tolist()
        
        if len(weeks) < 2: continue
            
        w1_data = month_data[month_data['week_of_year'] == weeks[0]]
        w2_data = month_data[month_data['week_of_year'] == weeks[1]]
        
        if w1_data.empty or w2_data.empty: continue

        w1_w2_high = max(w1_data['high'].max(), w2_data['high'].max())
        w1_w2_low = min(w1_data['low'].min(), w2_data['low'].min())
        rng = w1_w2_high - w1_w2_low
        if rng == 0: continue
            
        midpoint = w1_w2_low + (rng * 0.5)
        w2_close = w2_data.iloc[-1]['close']
        
        # Signal Type
        is_bull_signal = w2_close > midpoint
        
        # Outcome 1: Close Color
        m_open = month_data.iloc[0]['open']
        m_close = month_data.iloc[-1]['close']
        is_green = m_close > m_open
        
        # Outcome 2: Extension (New High/Low)
        post_w2_data = month_data[month_data['week_of_year'] > weeks[1]] # Logic relies on week numbers? 
        # Wait, if we use week numbers, > weeks[1] might fail in Dec if week[1] is 1 (next year).
        # Robust Logic: Filter by Date (Time Index)
        w2_end_time = w2_data.index.max()
        post_w2_data = month_data[month_data.index > w2_end_time]
        
        made_new_high = False
        made_new_low = False
        
        if not post_w2_data.empty:
            rest_high = post_w2_data['high'].max()
            rest_low = post_w2_data['low'].min()
            
            made_new_high = rest_high > w1_w2_high
            made_new_low = rest_low < w1_w2_low
            
        results.append({
            'month': month,
            'is_bull_signal': is_bull_signal,
            'is_green': is_green,          # Close Outcome
            'made_new_high': made_new_high, # Extension Outcome (Bull)
            'made_new_low': made_new_low    # Extension Outcome (Bear)
        })
        
    df = pd.DataFrame(results)
    
    # AGGREGATE STATS
    # We want 2 rows per month: 
    # Row 1: Bull Sig Perf (Prob Green, Prob New High)
    # Row 2: Bear Sig Perf (Prob Red, Prob New Low)
    
    months = range(1, 13)
    month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    # Prepare Data for Heatmap
    # Columns: [Bull_Prob_Green, Bull_Prob_NewHigh, Bear_Prob_Red, Bear_Prob_NewLow]
    heatmap_data = []
    
    for m in months:
        m_df = df[df['month'] == m]
        if m_df.empty: 
            heatmap_data.append([0, 0, 0, 0])
            continue
            
        # Bull Signal Stats
        bull_cases = m_df[m_df['is_bull_signal']]
        n_bull = len(bull_cases)
        if n_bull > 0:
            prob_green = (bull_cases['is_green'].sum() / n_bull) * 100
            prob_new_high = (bull_cases['made_new_high'].sum() / n_bull) * 100
        else:
            prob_green = np.nan
            prob_new_high = np.nan
            
        # Bear Signal Stats
        bear_cases = m_df[~m_df['is_bull_signal']]
        n_bear = len(bear_cases)
        if n_bear > 0:
            # Note: Prob Red = 1 - Prob Green (approx, ignoring flat)
            prob_red = ((~bear_cases['is_green']).sum() / n_bear) * 100
            prob_new_low = (bear_cases['made_new_low'].sum() / n_bear) * 100
        else:
            prob_red = np.nan
            prob_new_low = np.nan
            
        heatmap_data.append([prob_green, prob_new_high, prob_red, prob_new_low])
        
    heatmap_arr = np.array(heatmap_data)
    
    # PLOTTING
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Create mask for NaNs
    mask = np.isnan(heatmap_arr)
    # Replace NaNs with 0 for plotting, but we will hide text
    heatmap_arr_safe = np.nan_to_num(heatmap_arr, 0)
    
    # Plot Image
    # Normalize 0-100 for color
    im = ax.imshow(heatmap_arr_safe, cmap='RdYlGn', vmin=40, vmax=100, aspect='auto')
    
    # Axis Labels
    ax.set_xticks(np.arange(4))
    ax.set_yticks(np.arange(12))
    
    # X Axis Labels (Top)
    ax.set_xticklabels(['PROB GREEN\n(Bull Sig)', 'PROB NEW HIGH\n(Bull Sig)', 'PROB RED\n(Bear Sig)', 'PROB NEW LOW\n(Bear Sig)'], fontsize=12)
    ax.xaxis.tick_top()
    
    # Y Axis Labels (Month Names)
    ax.set_yticklabels(month_names, fontsize=12)
    
    # Add Values inside Cells
    for i in range(12):
        for j in range(4):
            val = heatmap_arr[i, j]
            if np.isnan(val):
                text = "N/A"
            else:
                text = f"{val:.0f}%"
                # Highlight significant ones
                if val >= 80:
                    text += " *"
            
            # ALL TEXT BLACK as requested
            ax.text(j, i, text, ha="center", va="center", color='black', fontweight='bold', fontsize=14)
            
    # Add Separator Line between Bull and Bear Columns
    ax.axvline(1.5, color='white', linewidth=2)
    
    # Headers Grouping
    ax.text(0.5, -1.2, "BULL SIGNAL (>50%) SCENARIO", ha='center', color=ACCENT_GREEN, fontweight='bold', fontsize=12)
    ax.text(2.5, -1.2, "BEAR SIGNAL (<50%) SCENARIO", ha='center', color=ACCENT_RED, fontweight='bold', fontsize=12)
    
    # Titles
    plt.suptitle(f'{asset_key} CONDITIONAL MONTHLY PROBABILITIES MATRIX', fontsize=18, fontweight='bold', color=TEXT_COLOR, y=0.05)
    ax.set_title("Based on W2 Close relative to W1-W2 Range (50% Level)", fontsize=10, color=GRAY_TEXT, pad=40)
    
    # Cleanup
    ax.spines[:].set_visible(False)
    ax.tick_params(top=False, bottom=False, left=False, right=False)
    
    # Footer
    fig.text(0.5, 0.01, f"Probabilities based on 2000-2026 History | * = >80% Win Rate", ha='center', color=GRAY_TEXT, fontsize=9)
    
    # Create Output Dir
    output_dir = 'output/charts/strategy'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"{output_dir}/{asset_key}_w2_signal_matrix.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {filename}")
    plt.close()

if __name__ == "__main__":
    # Analyze multiple assets
    for asset in ['NQ', 'ES', 'DJI', 'GC']:
        visualize_w2_signal_matrix(asset)
    #visualize_w2_signal_matrix('GSPC')
