"""Quick verification of weekly sigma band calculations."""
import sys
sys.path.insert(0, '.')
from src.data.data_loader import download_asset_data
import numpy as np
import pandas as pd

periods = [
    ('2005-01-01', '2025-12-31', '2005-2025'),
    ('2010-01-01', '2025-12-31', '2010-2025'),
    ('2015-01-01', '2025-12-31', '2015-2025'),
    ('2020-01-01', '2025-12-31', '2020-2025'),
]

for start, end, label in periods:
    data = download_asset_data('NQ', start_date=start, end_date=end)
    weekly = data.resample('W').agg({
        'open': 'first',
        'close': 'last',
    }).dropna()
    o2c = (weekly['close'] - weekly['open']) / weekly['open']
    o2c = o2c.dropna()

    mean = o2c.mean()
    std = o2c.std()

    print("=" * 70)
    print(f"  PERIODO: {label}  |  n={len(o2c)}")
    print("=" * 70)
    print(f"  Mean:  {mean*100:+.6f}%")
    print(f"  Std:   {std*100:.6f}%")
    print()
    print(f"  {'Sigma':>6}  {'mean':>10}  {'n*std':>10}  {'Superior':>12}  {'Inferior':>12}  {'Count':>6}  {'%':>8}")
    print("-" * 70)

    for sig in [0.5, 1.0, 1.5, 2.0]:
        n_std = sig * std
        sup = mean + n_std
        inf = mean - n_std
        count = ((o2c >= inf) & (o2c <= sup)).sum()
        pct = count / len(o2c) * 100
        print(f"  {sig:>6.1f}  {mean*100:>+9.4f}%  {n_std*100:>9.4f}%  {sup*100:>+11.4f}%  {inf*100:>+11.4f}%  {count:>6}  {pct:>7.2f}%")

    print()
    print("  VERIFICACION: mean - n*std")
    for sig in [0.5, 1.0, 1.5, 2.0]:
        inf = mean - sig * std
        # Also verify: is inferior = -(n*std - mean)?
        print(f"    {sig:.1f}s inf = {mean*100:+.4f}% - {sig:.1f}*{std*100:.4f}% = {mean*100:+.4f}% - {sig*std*100:.4f}% = {inf*100:+.4f}%")

    print()
    # Show the 5 worst weeks
    print("  5 peores semanas:")
    for d, v in o2c.nsmallest(5).items():
        print(f"    {d.date()}: {v*100:+.3f}%")
    print()
