"""
Executive Summary: 6E (Euro FX Futures) vs 6B (British Pound Futures)
"""
import sys
sys.path.insert(0, '.')
from src.data.data_loader import download_asset_data
import numpy as np
import pandas as pd
from scipy.stats import norm

PERIODS = [
    ('2005-01-01', '2025-12-31', '2005-2025'),
    ('2010-01-01', '2025-12-31', '2010-2025'),
    ('2015-01-01', '2025-12-31', '2015-2025'),
    ('2020-01-01', '2025-12-31', '2020-2025'),
    ('2023-01-01', '2026-01-31', '2023-2026'),
]

SEP = '=' * 100

for asset in ['6E', '6B']:
    print(f'\n{SEP}')
    
    # Get asset name
    from config.assets import get_asset
    asset_cfg = get_asset(asset)
    print(f'  {asset} ({asset_cfg.name}) - RESUMEN EJECUTIVO O2C (DIARIO)')
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
        zeros = (o2c == 0).sum()
        
        up_std = pos.std(ddof=1) if len(pos) > 1 else 0
        dn_std = abs(neg).std(ddof=1) if len(neg) > 1 else 0
        
        results.append({
            'label': label,
            'n': len(o2c),
            'zeros': zeros,
            'mean': o2c.mean(),
            'std': o2c.std(ddof=1),
            'median': o2c.median(),
            'skew': o2c.skew(),
            'kurt': o2c.kurtosis(),
            'min': o2c.min(),
            'max': o2c.max(),
            'pct_pos': len(pos) / len(o2c) * 100,
            'pct_neg': len(neg) / len(o2c) * 100,
            'pct_zero': zeros / len(o2c) * 100,
            'up_mean': pos.mean() if len(pos) > 0 else 0,
            'up_std': up_std,
            'dn_mean': neg.mean() if len(neg) > 0 else 0,
            'dn_std': dn_std,
            'vol_asym': (dn_std / up_std) if up_std > 0 else 0,
        })
    
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
    row('Vol Asym (Down-Up)', 'vol_asym', lambda v: f'{v:>13.4f}x')
    
    # Sigma bands for 2020-2025
    r20 = results[3]
    print(f'\n  Sigma Bands ({r20["label"]}):')
    data20 = download_asset_data(asset, start_date='2020-01-01', end_date='2025-12-31')
    o2c20 = ((data20['close'] - data20['open']) / data20['open']).dropna()
    mean_val = o2c20.mean()
    std_val = o2c20.std(ddof=1)
    
    print(f'  {"Sigma":<10} {"Superior":>14} {"Inferior":>14} {"Cuenta":>10} {"% Cuenta":>12} {"% Gauss":>12}')
    print(f'  {"-"*72}')
    for s in [0.5, 1.0, 1.5, 2.0]:
        upper = mean_val + s * std_val
        lower = mean_val - s * std_val
        count = ((o2c20 >= lower) & (o2c20 <= upper)).sum()
        pct = count / len(o2c20) * 100
        gauss = (norm.cdf(s) - norm.cdf(-s)) * 100
        print(f'  {s:<10.1f} {upper*100:>+13.4f}% {lower*100:>+13.4f}% {count:>10} {pct:>11.2f}% {gauss:>11.3f}%')
    
    # Data quality check
    print(f'\n  Calidad de datos ({r20["label"]}): {r20["zeros"]:.0f} dias con O2C=0 ({r20["pct_zero"]:.1f}%)')
    print()


# Comparative table
print(f'\n{SEP}')
print(f'  COMPARATIVA 6E vs 6B (2020-2025)')
print(f'{SEP}\n')

comp_data = {}
for asset in ['6E', '6B']:
    data = download_asset_data(asset, start_date='2020-01-01', end_date='2025-12-31')
    o2c = ((data['close'] - data['open']) / data['open']).dropna()
    pos = o2c[o2c > 0]
    neg = o2c[o2c < 0]
    comp_data[asset] = {
        'mean': o2c.mean(),
        'std': o2c.std(ddof=1),
        'pct_pos': len(pos)/len(o2c)*100,
        'pct_neg': len(neg)/len(o2c)*100,
        'max': o2c.max(),
        'min': o2c.min(),
        'kurt': o2c.kurtosis(),
        'skew': o2c.skew(),
        'up_mean': pos.mean(),
        'dn_mean': neg.mean(),
        'vol_asym': abs(neg).std(ddof=1) / pos.std(ddof=1),
    }

fmt = f'  {"Metrica":<30} {"6E (Euro)":>18} {"6B (Libra)":>18}'
print(fmt)
print(f'  {"-"*66}')

e = comp_data['6E']
b = comp_data['6B']

print(f'  {"Media diaria O2C":<30} {e["mean"]*100:>+17.4f}% {b["mean"]*100:>+17.4f}%')
print(f'  {"Volatilidad (std)":<30} {e["std"]*100:>17.4f}% {b["std"]*100:>17.4f}%')
print(f'  {"Dias positivos":<30} {e["pct_pos"]:>17.1f}% {b["pct_pos"]:>17.1f}%')
print(f'  {"Dias negativos":<30} {e["pct_neg"]:>17.1f}% {b["pct_neg"]:>17.1f}%')
print(f'  {"Media upside":<30} {e["up_mean"]*100:>+17.4f}% {b["up_mean"]*100:>+17.4f}%')
print(f'  {"Media downside":<30} {e["dn_mean"]*100:>+17.4f}% {b["dn_mean"]*100:>+17.4f}%')
print(f'  {"Mejor dia":<30} {e["max"]*100:>+17.4f}% {b["max"]*100:>+17.4f}%')
print(f'  {"Peor dia":<30} {e["min"]*100:>+17.4f}% {b["min"]*100:>+17.4f}%')
print(f'  {"Curtosis":<30} {e["kurt"]:>18.2f} {b["kurt"]:>18.2f}')
print(f'  {"Asimetria":<30} {e["skew"]:>+18.4f} {b["skew"]:>+18.4f}')
print(f'  {"Vol Asymmetry (D-U)":<30} {e["vol_asym"]:>17.4f}x {b["vol_asym"]:>17.4f}x')
print()

# Ratio comparison
print(f'  {"Ratio GBP/EUR volatilidad:":<30} {b["std"]/e["std"]:.2f}x')
print(f'  (La libra es {b["std"]/e["std"]:.2f}x mas volatil que el euro en O2C)')
print()
