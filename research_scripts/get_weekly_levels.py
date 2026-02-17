import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.data_loader import download_asset_data

def get_weekly_stats(asset_key, start='2015-01-01', end='2025-12-31'):
    data = download_asset_data(asset_key, start_date=start, end_date=end)
    weekly = data.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
    }).dropna()
    o2c = (weekly['close'] - weekly['open']) / weekly['open']
    
    mean = o2c.mean()
    std = o2c.std()
    
    return {
        'Asset': asset_key,
        'Mean': f"{mean*100:.3f}%",
        'Std Dev': f"{std*100:.3f}%",
        '+1 Sigma': f"{(mean + std)*100:.3f}%",
        '-1 Sigma': f"{(mean - std)*100:.3f}%",
        '+1.5 Sigma': f"{(mean + 1.5*std)*100:.3f}%",
        '-1.5 Sigma': f"{(mean - 1.5*std)*100:.3f}%",
        'Count': len(o2c)
    }

assets = ['ES', 'GC', 'YM']
results = []
for a in assets:
    results.append(get_weekly_stats(a))

df = pd.DataFrame(results)
print("\nESTADISTICAS SEMANALES OPEN-TO-CLOSE (2015-2025)")
print("-" * 85)
print(df.to_string(index=False))
