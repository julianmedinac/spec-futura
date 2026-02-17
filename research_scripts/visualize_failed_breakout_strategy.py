import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from src.data.data_loader import DataLoader

# VISUAL STYLE GUIDE (Strict Adherence)
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

def visualize_failed_breakout_strategy():
    print(f"\nGenerating Failed Breakout Analysis Visual...")
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
        
        results = []
        for (year, week), week_data in weekly_groups:
            if len(week_data) < 5: continue
            d1, d2, d3 = week_data.iloc[0], week_data.iloc[1], week_data.iloc[2]
            d1_d2_h, d1_d2_l = max(d1['high'], d2['high']), min(d1['low'], d2['low'])
            if d2['close'] <= (d1_d2_l + 0.5 * (d1_d2_h - d1_d2_l)): continue
            if d3['high'] <= d1_d2_h: continue
            d1_d3_h, d1_d3_l = max(d1_d2_h, d3['high']), min(d1_d2_l, d3['low'])
            if d3['close'] >= (d1_d3_l + 0.5 * (d1_d3_h - d1_d3_l)): continue
            
            m_sig = monthly_signals.get((d3.name.year, d3.name.month), 'PENDING')
            week_o, week_c = d1['open'], week_data.iloc[-1]['close']
            rest_low = week_data.iloc[3:]['low'].min()
            results.append({'m_signal': m_sig, 'red': week_c < week_o, 'new_low': rest_low < d1_d3_l})

        df = pd.DataFrame(results)
        if df.empty: continue
        
        # Base Stats
        base_red = (df['red'].sum() / len(df)) * 100
        base_low = (df['new_low'].sum() / len(df)) * 100
        
        # Bear Context Filtered
        bear_df = df[df['m_signal'] == 'BEAR']
        bear_red = (bear_df['red'].sum() / len(bear_df)) * 100 if not bear_df.empty else 0
        bear_low = (bear_df['new_low'].sum() / len(bear_df)) * 100 if not bear_df.empty else 0
        
        final_stats.append([len(df), base_red, base_low, bear_red, bear_low])

    # Plot Table
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('off')
    col_labels = ['SAMPLES', 'BASE PROB:\nRED WEEK', 'BASE PROB:\nNEW LOW', 'BEAR MONTH:\nRED WEEK', 'BEAR MONTH:\nNEW LOW']
    
    cell_text, cell_colors = [], []
    for i, row in enumerate(final_stats):
        txt, clr = [str(int(row[0]))], [BG_COLOR]
        for j, val in enumerate(row[1:]):
            txt.append(f"{val:.1f}%")
            if val > 75: clr.append(ACCENT_RED_DIM)
            elif val > 65: clr.append('#220000')
            else: clr.append(BG_COLOR)
        cell_text.append(txt)
        cell_colors.append(clr)

    table = ax.table(cellText=cell_text, colLabels=col_labels, rowLabels=assets, cellColours=cell_colors, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(13)
    table.scale(1, 3.5)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(LINE_COLOR)
        if row == 0:
            cell.set_text_props(weight='bold', color=TEXT_COLOR)
            cell.set_facecolor(LINE_COLOR)
        elif col == -1:
            cell.set_text_props(weight='bold', color=GRAY_TEXT)
        else:
            val_str = cell.get_text().get_text().replace('%', '')
            try:
                val = float(val_str)
                if val > 75: cell.set_text_props(weight='bold', color=ACCENT_RED)
                elif val > 65: cell.set_text_props(color=ACCENT_RED)
                else: cell.set_text_props(color=TEXT_COLOR)
            except: pass

    plt.suptitle("D3 FAILED BREAKOUT: THE DEATH TRAP MATRIX", fontsize=20, fontweight='bold', color=ACCENT_RED, y=0.96)
    plt.title("Scenario: D1-D2 Bullish -> D3 High Attack -> D3 Close < 50% Range", color=GRAY_TEXT, fontsize=12, pad=20)
    plt.text(0.5, 0.05, "CRITICAL: The Bear Month filter elevates standard patterns into high-conviction Snipers (>75%).", ha='center', color=ACCENT_RED, fontsize=11, transform=fig.transFigure)

    output_path = 'output/charts/strategy/failed_breakout_matrix.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=BG_COLOR)
    print(f"File saved to: {output_path}")

if __name__ == "__main__":
    visualize_failed_breakout_strategy()
