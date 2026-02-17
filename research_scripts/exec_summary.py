"""
Executive Summary Generator for EURUSD and GBPUSD
Generates a comprehensive O2C analysis summary table.
"""
import sys
sys.path.insert(0, '.')
from src.data.data_loader import download_asset_data
import numpy as np
import pandas as pd

PERIODS = [
    ('2005-01-01', '2025-12-31', '2005-2025'),
    ('2010-01-01', '2025-12-31', '2010-2025'),
    ('2015-01-01', '2025-12-31', '2015-2025'),
    ('2020-01-01', '2025-12-31', '2020-2025'),
    ('2023-01-01', '2026-01-31', '2023-2026'),
]

SEP = '=' * 90

for asset in ['EURUSD', 'GBPUSD']:
    print(f'\n{SEP}')
    print(f'  {asset} - RESUMEN EJECUTIVO O2C (DIARIO)')
    print(f'{SEP}\n')
    
    header = f'{"Metrica":<25}'
    for _, _, label in PERIODS:
        header += f'{label:>14}'
    print(header)
    print('-' * 95)
    
    results = []
    for start, end, label in PERIODS:
        data = download_asset_data(asset, start_date=start, end_date=end)
        o2c = ((data['close'] - data['open']) / data['open']).dropna()
        pos = o2c[o2c > 0]
        neg = o2c[o2c < 0]
        
        up_std = pos.std(ddof=1) if len(pos) > 1 else 0
        dn_std = abs(neg).std(ddof=1) if len(neg) > 1 else 0
        
        results.append({
            'label': label,
            'n': len(o2c),
            'mean': o2c.mean(),
            'std': o2c.std(ddof=1),
            'median': o2c.median(),
            'skew': o2c.skew(),
            'kurt': o2c.kurtosis(),
            'min': o2c.min(),
            'max': o2c.max(),
            'pct_pos': len(pos) / len(o2c) * 100,
            'pct_neg': len(neg) / len(o2c) * 100,
            'up_mean': pos.mean() if len(pos) > 0 else 0,
            'up_std': up_std,
            'dn_mean': neg.mean() if len(neg) > 0 else 0,
            'dn_std': dn_std,
            'vol_asym': (dn_std / up_std) if up_std > 0 else 0,
        })
    
    # Print rows
    def row(name, key, fmt_func):
        line = f'{name:<25}'
        for r in results:
            line += fmt_func(r[key])
        print(line)
    
    row('Observaciones', 'n', lambda v: f'{v:>14,}')
    print()
    row('Media', 'mean', lambda v: f'{v*100:>+13.4f}%')
    row('Std Dev', 'std', lambda v: f'{v*100:>13.4f}%')
    row('Mediana', 'median', lambda v: f'{v*100:>+13.4f}%')
    row('Curtosis', 'kurt', lambda v: f'{v:>14.2f}')
    row('Asimetria', 'skew', lambda v: f'{v:>+14.4f}')
    row('Min', 'min', lambda v: f'{v*100:>+13.4f}%')
    row('Max', 'max', lambda v: f'{v*100:>+13.4f}%')
    print()
    print('UPSIDE')
    row('  Cantidad', 'pct_pos', lambda v: f'{v:>13.1f}%')
    row('  Media', 'up_mean', lambda v: f'{v*100:>+13.4f}%')
    row('  Std Dev', 'up_std', lambda v: f'{v*100:>13.4f}%')
    print()
    print('DOWNSIDE')
    row('  Cantidad', 'pct_neg', lambda v: f'{v:>13.1f}%')
    row('  Media', 'dn_mean', lambda v: f'{v*100:>+13.4f}%')
    row('  Std Dev', 'dn_std', lambda v: f'{v*100:>13.4f}%')
    print()
    row('Vol Asym (Down/Up)', 'vol_asym', lambda v: f'{v:>13.4f}x')
    
    # Sigma bands
    print(f'\n  Sigma Bands (periodo mas reciente: {results[-2]["label"]})')
    r = results[-2]  # 2020-2025
    data = download_asset_data(asset, start_date='2020-01-01', end_date='2025-12-31')
    o2c = ((data['close'] - data['open']) / data['open']).dropna()
    mean_val = o2c.mean()
    std_val = o2c.std(ddof=1)
    
    print(f'  {"Sigma":<10} {"Superior":>14} {"Inferior":>14} {"Cuenta":>10} {"% Cuenta":>12} {"% Gauss":>12}')
    print(f'  {"-"*72}')
    from scipy.stats import norm
    for s in [0.5, 1.0, 1.5, 2.0]:
        upper = mean_val + s * std_val
        lower = mean_val - s * std_val
        count = ((o2c >= lower) & (o2c <= upper)).sum()
        pct = count / len(o2c) * 100
        gauss = (norm.cdf(s) - norm.cdf(-s)) * 100
        print(f'  {s:<10.1f} {upper*100:>+13.4f}% {lower*100:>+13.4f}% {count:>10} {pct:>11.2f}% {gauss:>11.3f}%')
    
    print()

print('\n' + '=' * 90)
print('  COMPARATIVA EURUSD vs GBPUSD (2020-2025)')
print('=' * 90)
print()

# Reload data for comparison
for asset in ['EURUSD', 'GBPUSD']:
    data = download_asset_data(asset, start_date='2020-01-01', end_date='2025-12-31')
    o2c = ((data['close'] - data['open']) / data['open']).dropna()
    pos = o2c[o2c > 0]
    neg = o2c[o2c < 0]
    
    print(f'  {asset}:')
    print(f'    Media diaria O2C:  {o2c.mean()*100:>+.4f}%')
    print(f'    Volatilidad (std): {o2c.std(ddof=1)*100:>.4f}%')
    print(f'    Dias positivos:    {len(pos)/len(o2c)*100:.1f}%')
    print(f'    Dias negativos:    {len(neg)/len(o2c)*100:.1f}%')
    print(f'    Mejor dia:         {o2c.max()*100:>+.4f}%')
    print(f'    Peor dia:          {o2c.min()*100:>+.4f}%')
    print(f'    Curtosis:          {o2c.kurtosis():.2f}')
    print(f'    Asimetria:         {o2c.skew():+.4f}')
    print()
