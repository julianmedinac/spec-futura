import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from src.data.data_loader import DataLoader

# VISUAL STYLE GUIDE
BG_COLOR = '#000000'
TEXT_COLOR = '#ffffff'
ACCENT_GREEN = '#00ff44'
ACCENT_GREEN_DIM = '#003311'
ACCENT_RED = '#ff0044'
ACCENT_RED_DIM = '#330011'
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

def get_monthly_w2_signal(data):
    data['iso_year'] = data.index.isocalendar().year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    monthly_signals = {}
    groups = data.groupby(['iso_year', 'month'])
    for (year, month), m_data in groups:
        unique_weeks = m_data['week_of_year'].unique()
        if len(unique_weeks) < 2: continue
        w2_idx = unique_weeks[1]
        w2_data = m_data[m_data['week_of_year'] == w2_idx]
        if w2_data.empty: continue
        start_date, end_date = m_data.index[0], w2_data.index[-1]
        range_data = m_data.loc[start_date:end_date]
        h, l = range_data['high'].max(), range_data['low'].min()
        c = w2_data.iloc[-1]['close']
        mid = l + (h - l) * 0.5
        monthly_signals[(year, month)] = 'BULL' if c > mid else 'BEAR'
    return monthly_signals

def visualize_reversal_sniper_matrix():
    print(f"\nGenerating Reversal Sniper Matrix (Bull & Bear Traps)...")
    loader = DataLoader()
    assets = ['NQ', 'ES', 'DJI', 'GC']
    final_stats = []

    for asset in assets:
        data = loader.download(asset, start_date='2000-01-01')
        if data.empty: continue
        monthly_signals = get_monthly_w2_signal(data)
        data['iso_year'] = data.index.isocalendar().year
        data['week_of_year'] = data.index.isocalendar().week
        weekly_groups = data.groupby(['iso_year', 'week_of_year'])
        
        bull_traps = []
        bear_traps = []
        
        for (year, week), week_data in weekly_groups:
            if len(week_data) < 5: continue
            d1, d2, d3 = week_data.iloc[0], week_data.iloc[1], week_data.iloc[2]
            d1_d2_h, d1_d2_l = max(d1['high'], d2['high']), min(d1['low'], d2['low'])
            rng_d1_d2 = d1_d2_h - d1_d2_l
            if rng_d1_d2 == 0: continue
            m_sig = monthly_signals.get((d3.name.year, d3.name.month), 'PENDING')
            
            # --- BULL TRAP (Look Above & Fail) ---
            # Condition: D2 Bullish, D3 High Break, D3 Close < 50%
            if d2['close'] > (d1_d2_l + 0.5 * rng_d1_d2):
                if d3['high'] > d1_d2_h:
                    d1_d3_h, d1_d3_l = max(d1_d2_h, d3['high']), min(d1_d2_l, d3['low'])
                    if d3['close'] < (d1_d3_l + 0.5 * (d1_d3_h - d1_d3_l)):
                        rest_low = week_data.iloc[3:]['low'].min()
                        bull_traps.append({'m_signal': m_sig, 'new_low': rest_low < d1_d3_l})

            # --- BEAR TRAP (Look Below & Fail) ---
            # Condition: D2 Bearish, D3 Low Break, D3 Close > 50%
            if d2['close'] < (d1_d2_l + 0.5 * rng_d1_d2):
                if d3['low'] < d1_d2_l:
                    d1_d3_h, d1_d3_l = max(d1_d2_h, d3['high']), min(d1_d2_l, d3['low'])
                    if d3['close'] > (d1_d3_l + 0.5 * (d1_d3_h - d1_d3_l)):
                        rest_high = week_data.iloc[3:]['high'].max()
                        bear_traps.append({'m_signal': m_sig, 'new_high': rest_high > d1_d3_h})

        # Calculate SNIPER Probabilities (Aligned with Month)
        df_bull = pd.DataFrame(bull_traps)
        df_bear = pd.DataFrame(bear_traps)
        
        # Bull Trap Sniper (Bear Month Context)
        bt_aligned = df_bull[df_bull['m_signal'] == 'BEAR']
        bt_prob = (bt_aligned['new_low'].sum() / len(bt_aligned)) * 100 if not bt_aligned.empty else 0
        bt_samples = len(bt_aligned)
        
        # Bear Trap Sniper (Bull Month Context)
        bat_aligned = df_bear[df_bear['m_signal'] == 'BULL']
        bat_prob = (bat_aligned['new_high'].sum() / len(bat_aligned)) * 100 if not bat_aligned.empty else 0
        bat_samples = len(bat_aligned)
        
        final_stats.append([bt_samples, bt_prob, bat_samples, bat_prob])

    # Plot Table
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('off')
    col_labels = [
        'BULL TRAP SAMPLES\n(In Bear Month)', 'BULL TRAP PROB:\nNEW WEEKLY LOW',
        'BEAR TRAP SAMPLES\n(In Bull Month)', 'BEAR TRAP PROB:\nNEW WEEKLY HIGH'
    ]
    
    cell_text, cell_colors = [], []
    for i, row in enumerate(final_stats):
        txt = [str(int(row[0])), f"{row[1]:.1f}%", str(int(row[2])), f"{row[3]:.1f}%"]
        clrs = [BG_COLOR, 
                ACCENT_RED_DIM if row[1] > 75 else ('#220000' if row[1] > 65 else BG_COLOR),
                BG_COLOR,
                ACCENT_GREEN_DIM if row[3] > 75 else ('#002200' if row[3] > 65 else BG_COLOR)]
        cell_text.append(txt)
        cell_colors.append(clrs)

    table = ax.table(cellText=cell_text, colLabels=col_labels, rowLabels=assets, cellColours=cell_colors, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(14)
    table.scale(1, 4)

    # Style cells
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(LINE_COLOR)
        if row == 0:
            cell.set_text_props(weight='bold', color=TEXT_COLOR)
            cell.set_facecolor(LINE_COLOR)
        elif col == -1:
            cell.set_text_props(weight='bold', color=GRAY_TEXT)
        else:
            txt_val = cell.get_text().get_text()
            if '%' in txt_val:
                val = float(txt_val.replace('%', ''))
                if col == 1: # Bull Trap col
                    if val > 75: cell.set_text_props(weight='bold', color=ACCENT_RED)
                    elif val > 65: cell.set_text_props(color=ACCENT_RED)
                if col == 3: # Bear Trap col
                    if val > 75: cell.set_text_props(weight='bold', color=ACCENT_GREEN)
                    elif val > 65: cell.set_text_props(color=ACCENT_GREEN)
            else:
                cell.set_text_props(color=GRAY_TEXT)

    plt.suptitle("REVERSAL SNIPER MATRIX: TRAPPING THE LIQUIDITY", fontsize=20, fontweight='bold', color=TEXT_COLOR, y=0.96)
    plt.title("Pattern: D1-D2 Bias -> D3 Fakeout Attack -> D3 Reversal Close (>50% of Range)", color=GRAY_TEXT, fontsize=12, pad=30)
    plt.text(0.5, 0.05, "SNIPER CRITERIA: Signal ALIGNED with Monthly W2 context. Note the rarity of these setups (Samples).", ha='center', color=GRAY_TEXT, fontsize=10, transform=fig.transFigure)

    output_path = 'output/charts/strategy/reversal_sniper_matrix.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=BG_COLOR)
    print(f"File saved to: {output_path}")

if __name__ == "__main__":
    visualize_reversal_sniper_matrix()
