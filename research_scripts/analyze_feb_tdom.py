import pandas as pd
import numpy as np
from src.data.data_loader import DataLoader
from config.assets import get_asset

def analyze_february_bottom_tdom(asset_key: str):
    loader = DataLoader()
    data = loader.download(asset_key, years_back=100)
    
    # Calculate Monthly Returns to identify "Bullish Februarys"
    monthly_data = data['close'].resample('ME').last()
    monthly_returns = monthly_data.pct_change()
    
    # Group data by year and month
    data['year'] = data.index.year
    data['month'] = data.index.month
    
    feb_tdom_lows = []
    
    years = data['year'].unique()
    for year in years:
        feb_data = data[(data['year'] == year) & (data['month'] == 2)].copy()
        if feb_data.empty: continue
        
        # Check if February was bullish (Close > Open of month OR positive return)
        # Using Postive Monthly Return as the filter
        feb_end_date = feb_data.index[-1]
        if feb_end_date not in monthly_returns.index: continue
        
        is_bullish = monthly_returns.loc[feb_end_date] > 0
        
        if is_bullish:
            # Assign Trading Day of Month (TDOM)
            feb_data['tdom'] = range(1, len(feb_data) + 1)
            
            # Find TDOM of the Low
            low_idx = feb_data['low'].idxmin()
            low_tdom = feb_data.loc[low_idx, 'tdom']
            
            feb_tdom_lows.append(low_tdom)
            
    if not feb_tdom_lows:
        print(f"No bullish Februarys found for {asset_key}")
        return

    # Analyze Distribution
    tdom_counts = pd.Series(feb_tdom_lows).value_counts().sort_index()
    tdom_probs = (tdom_counts / len(feb_tdom_lows)) * 100
    
    print(f"\n{'='*60}")
    print(f"TDOM OF THE BOTTOM IN BULLISH FEBRUARYS - {asset_key}")
    print(f"Sample: {len(feb_tdom_lows)} Bullish Februarys")
    print(f"{'='*60}")
    
    print("\nTop 5 Trading Days for the Bottom:")
    top_5 = tdom_probs.sort_values(ascending=False).head(5)
    for tdom, prob in top_5.items():
        print(f"  - TDOM {tdom}: {prob:.1f}%")
        
    # Group by buckets for clearer vision
    early = tdom_probs[tdom_probs.index <= 5].sum()
    mid = tdom_probs[(tdom_probs.index > 5) & (tdom_probs.index <= 12)].sum()
    late = tdom_probs[tdom_probs.index > 12].sum()
    
    print("\nConcentration by Month Segment:")
    print(f"  - Early (TDOM 1-5): {early:.1f}%")
    print(f"  - Mid (TDOM 6-12): {mid:.1f}%")
    print(f"  - Late (TDOM 13+): {late:.1f}%")

if __name__ == "__main__":
    analyze_february_bottom_tdom('GC')
