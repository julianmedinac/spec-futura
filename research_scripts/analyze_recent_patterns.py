import pandas as pd
import numpy as np
from src.data.data_loader import DataLoader
from src.seasonality.extremes_analyzer import ExtremesAnalyzer
from config.assets import get_asset

def analyze_recent_regime(asset_key: str, years_back: int = 5):
    loader = DataLoader()
    data = loader.download(asset_key, years_back=10) # Get enough to have the last 5 full years
    
    analyzer = ExtremesAnalyzer(data)
    extremes_df = analyzer.analyze_extremes()
    
    # Get last N years
    recent_extremes = extremes_df.tail(years_back).copy()
    
    # Format for display
    recent_extremes['Low_Q'] = recent_extremes['low_quarter'].apply(lambda x: f"Q{int(x)}")
    recent_extremes['High_Q'] = recent_extremes['high_quarter'].apply(lambda x: f"Q{int(x)}")
    
    print(f"\n--- {asset_key} RECENT REGIME (Last {years_back} Years) ---")
    print(recent_extremes[['year', 'Low_Q', 'High_Q']].to_string(index=False))
    
    # Calculate pattern frequency
    pattern_counts = recent_extremes.groupby(['Low_Q', 'High_Q']).size().reset_index(name='count')
    pattern_counts = pattern_counts.sort_values('count', ascending=False)
    print(f"\nTop Patterns for {asset_key}:")
    for _, row in pattern_counts.iterrows():
        print(f"  {row['Low_Q']} Low -> {row['High_Q']} High: {row['count']} times")

if __name__ == "__main__":
    for asset in ['GC']:
        analyze_recent_regime(asset)
