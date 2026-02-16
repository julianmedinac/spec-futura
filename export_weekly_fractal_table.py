import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from src.data.data_loader import DataLoader

def export_weekly_fractal_table(asset_key):
    print(f"\nGenerando tabla semanal mensual para {asset_key}...")
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
            
        # Outcome: New Ext
        rest_of_week = week_data.iloc[2:]
        rest_high = rest_of_week['high'].max()
        rest_low = rest_of_week['low'].min()
        
        made_new_high = rest_high > d1_d2_high
        made_new_low = rest_low < d1_d2_low
        
        # Outcome: Close Green/Red
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
    table_data = [] # List of lists
    
    for m in range(1, 13):
        m_df = df[df['month'] == m]
        if m_df.empty: 
            table_data.append([0, 0, 0, 0])
            continue
        
        # Bull Signal
        bull = m_df[m_df['is_bull_signal']]
        if len(bull) > 0:
            prob_high = (bull['made_new_high'].sum() / len(bull)) * 100
            prob_green = (bull['is_green_week'].sum() / len(bull)) * 100
        else:
            prob_high = 0.0
            prob_green = 0.0
            
        # Bear Signal
        bear = m_df[~m_df['is_bull_signal']]
        if len(bear) > 0:
            prob_low = (bear['made_new_low'].sum() / len(bear)) * 100
            prob_red = ((~bear['is_green_week']).sum() / len(bear)) * 100
        else:
            prob_low = 0.0
            prob_red = 0.0
            
        table_data.append([prob_high, prob_green, prob_low, prob_red])
        
    # PLOTTING TABLE IMAGE
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.axis('off')
    ax.axis('tight')
    
    # Column Labels
    col_labels = ['BULL SIG\nProb New High', 'BULL SIG\nProb Green Close', 'BEAR SIG\nProb New Low', 'BEAR SIG\nProb Red Close']
    
    # Cell Text (with formatting)
    cell_text = []
    for i, row in enumerate(table_data):
        row_text = []
        for val in row:
            text = f"{val:.1f}%"
            if val > 80: text += " *"  # Star for top tier
            row_text.append(text)
        cell_text.append(row_text)
        
    # Create Table
    table = ax.table(cellText=cell_text, colLabels=col_labels, rowLabels=month_names, loc='center', cellLoc='center')
    
    # Style Table
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2) # Row height scaling
    
    # Color High Probability Cells
    for i in range(12):
        for j in range(4):
            val = table_data[i][j]
            cell = table[i+1, j] # +1 for header row
            if val > 80:
                cell.set_facecolor('#ccffcc' if j < 2 else '#ffcccc') # Light Green / Light Red
                cell.set_text_props(weight='bold')
    
    plt.title(f"{asset_key} WEEKLY FRACTAL SEASONALITY (D2 SIGNAL)", fontsize=16, fontweight='bold', y=0.98)
    
    # Footer
    plt.text(0.5, 0.05, "* = >80% Probability (High Confidence Setup)", ha='center', fontsize=10, transform=fig.transFigure)

    # Save
    output_dir = 'output/charts/strategy'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"{output_dir}/{asset_key}_weekly_fractal_seasonality.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {filename}")
    plt.close()

if __name__ == "__main__":
    export_weekly_fractal_table('NQ')
