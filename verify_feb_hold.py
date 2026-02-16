import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.data.data_loader import DataLoader

def verify_feb_hold(asset_key):
    print(f"\n{'='*80}")
    print(f"DEEP DIVE: FEBRUARY BULL HOLD PROBABILITY FOR {asset_key}")
    print(f"{'='*80}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['iso_year'] = data.index.isocalendar().year
    data['week_of_year'] = data.index.isocalendar().week
    data['month'] = data.index.month
    
    # Filter for February only
    feb_data = data[data['month'] == 2]
    weekly_groups = feb_data.groupby(['iso_year', 'week_of_year'])
    
    processed_count = 0
    bull_signals = 0
    bull_breaks = 0
    bull_extensions = 0
    bull_holds = 0
    
    debug_list = []
    
    for (year, week), week_data in weekly_groups:
        if len(week_data) < 5: continue 
        
        d1 = week_data.iloc[0]
        d2 = week_data.iloc[1]
        
        # We need to ensure we are looking at weeks that are predominantly in Feb
        # Generally if D2 is in Feb, we count it.
        if d2.name.month != 2: continue
        
        d3 = week_data.iloc[2]
        
        d1_d2_h = max(d1['high'], d2['high'])
        d1_d2_l = min(d1['low'], d2['low'])
        rng = d1_d2_h - d1_d2_l
        if rng == 0: continue
            
        midpoint = d1_d2_l + (rng * 0.5)
        d2_close = d2['close']
        
        if d2_close > midpoint: # Bull Signal
            bull_signals += 1
            if d3['high'] > d1_d2_h: # Breakout
                bull_breaks += 1
                
                rest_high = week_data.iloc[3:]['high'].max()
                week_close = week_data.iloc[-1]['close']
                d3_close = d3['close']
                
                extended = rest_high > d3['high']
                held = week_close > d3_close
                
                if extended: bull_extensions += 1
                if held: bull_holds += 1
                
                debug_list.append({
                    'Year': year, 'Week': week,
                    'D3_Break': True,
                    'Extended': extended,
                    'Held': held,
                    'D3_Close': d3_close,
                    'W_Close': week_close
                })

    print(f"Total Bull Signals in FEB: {bull_signals}")
    print(f"Total Breakouts in FEB: {bull_breaks}")
    if bull_breaks > 0:
        ext_prob = (bull_extensions / bull_breaks) * 100
        hold_prob = (bull_holds / bull_breaks) * 100
        print(f"Extension Probability: {ext_prob:.1f}% ({bull_extensions}/{bull_breaks})")
        print(f"Hold Probability:      {hold_prob:.1f}% ({bull_holds}/{bull_breaks})")
        
        # If hold_prob is high (e.g. 67%), why did we flag it as dangerous?
        # Maybe the recent years are bad?
        print("\nLast 5 Occurrences:")
        print(pd.DataFrame(debug_list).tail(5).to_string(index=False))
        
if __name__ == "__main__":
    verify_feb_hold('NQ')
