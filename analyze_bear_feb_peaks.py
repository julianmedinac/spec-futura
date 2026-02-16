import pandas as pd
import numpy as np
from src.data.data_loader import DataLoader
from config.assets import get_asset

def analyze_bearish_february_peaks(asset_key: str):
    loader = DataLoader()
    data = loader.download(asset_key, years_back=100)
    
    # Calculate Monthly Returns
    monthly_data = data['close'].resample('ME').last()
    monthly_returns = monthly_data.pct_change()
    
    data['year'] = data.index.year
    data['month'] = data.index.month
    
    feb_tdom_highs = []
    
    years = data['year'].unique()
    for year in years:
        feb_data = data[(data['year'] == year) & (data['month'] == 2)].copy()
        if feb_data.empty: continue
        
        feb_end_date = feb_data.index[-1]
        if feb_end_date not in monthly_returns.index: continue
        
        is_bearish = monthly_returns.loc[feb_end_date] < 0
        
        if is_bearish:
            feb_data['tdom'] = range(1, len(feb_data) + 1)
            high_idx = feb_data['high'].idxmax()
            high_tdom = feb_data.loc[high_idx, 'tdom']
            feb_tdom_highs.append(high_tdom)
            
    if not feb_tdom_highs:
        print(f"No bearish Februarys found for {asset_key}")
        return

    tdom_counts = pd.Series(feb_tdom_highs).value_counts().sort_index()
    tdom_probs = (tdom_counts / len(feb_tdom_highs)) * 100
    
    print(f"\n{'='*60}")
    print(f"TDOM OF THE PEAK (HIGH) IN BEARISH FEBRUARYS - {asset_key}")
    print(f"Sample: {len(feb_tdom_highs)} Bearish Februarys")
    print(f"{'='*60}")
    
    print("\nPeak Concentration by Segment:")
    early = tdom_probs[tdom_probs.index <= 5].sum()
    mid = tdom_probs[(tdom_probs.index > 5) & (tdom_probs.index <= 12)].sum()
    late = tdom_probs[tdom_probs.index > 12].sum()
    
    print(f"  - Early Peak (TDOM 1-5): {early:.1f}%")
    print(f"  - Mid-Month Peak (TDOM 6-12): {mid:.1f}%")
    print(f"  - Late Peak (TDOM 13+): {late:.1f}%")
    
    print("\nTop 3 specific TDOM for HIGH:")
    top_3 = tdom_probs.sort_values(ascending=False).head(3)
    for tdom, prob in top_3.items():
        print(f"  - TDOM {tdom}: {prob:.1f}%")

if __name__ == "__main__":
    analyze_bearish_february_peaks('GC')
