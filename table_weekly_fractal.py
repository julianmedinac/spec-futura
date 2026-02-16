import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def generate_weekly_fractal_table():
    print(f"\n{'='*100}")
    print(f"WEEKLY FRACTAL SUMMARY TABLE (D2 CLOSING SIGNAL)")
    print(f"{'='*100}")
    
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
        
        summary_data.append({
            'Asset': asset,
            'Bull_Win_Green': bull_win,
            'Bull_New_High': bull_ext,
            'Bear_Win_Red': bear_win,
            'Bear_New_Low': bear_ext
        })
        
    print(f"{'Asset':<6} | {'BULL SIG: Prob Green':<22} | {'BULL SIG: Prob High':<20} | {'BEAR SIG: Prob Red':<20} | {'BEAR SIG: Prob Low':<20}")
    print(f"{'-'*6}-|-{'-'*22}-|-{'-'*20}-|-{'-'*20}-|-{'-'*20}")
    
    for row in summary_data:
        asset = row['Asset']
        bg = f"{row['Bull_Win_Green']:.1f}%"
        bh = f"{row['Bull_New_High']:.1f}%"
        br = f"{row['Bear_Win_Red']:.1f}%"
        bl = f"{row['Bear_New_Low']:.1f}%"
        
        # Add stars for exceptional performance (>75%)
        if row['Bull_Win_Green'] > 75: bg += "*"
        if row['Bull_New_High'] > 75: bh += "*"
        if row['Bear_Win_Red'] > 75: br += "*"
        if row['Bear_New_Low'] > 75: bl += "*"
        
        print(f"{asset:<6} | {bg:<22} | {bh:<20} | {br:<20} | {bl:<20}")

if __name__ == "__main__":
    generate_weekly_fractal_table()
