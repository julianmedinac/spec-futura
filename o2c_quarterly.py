"""
DOR Framework - Quarterly Seasonal Analysis
Calculates monthly O2C returns and filters by quarter (Q1-Q4)
to reveal seasonal patterns in monthly performance.

Q1 = January, February, March
Q2 = April, May, June
Q3 = July, August, September
Q4 = October, November, December
"""
import sys
sys.path.insert(0, '.')
from src.data.data_loader import download_asset_data
from src.returns.returns_calculator import ReturnsCalculator
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats as scipy_stats
from pathlib import Path
from datetime import datetime

PERIODS = [
    ('2005-01-01', '2025-12-31', '2005-2025'),
    ('2010-01-01', '2025-12-31', '2010-2025'),
    ('2015-01-01', '2025-12-31', '2015-2025'),
    ('2020-01-01', '2025-12-31', '2020-2025'),
    ('2023-01-01', '2026-01-31', '2023-2026'),
]
SIGMAS = [1, 1.5, 2]

QUARTERS = {
    'Q1': [1, 2, 3],
    'Q2': [4, 5, 6],
    'Q3': [7, 8, 9],
    'Q4': [10, 11, 12],
}

QUARTER_LABELS = {
    'Q1': 'Q1 (Ene-Feb-Mar)',
    'Q2': 'Q2 (Abr-May-Jun)',
    'Q3': 'Q3 (Jul-Ago-Sep)',
    'Q4': 'Q4 (Oct-Nov-Dic)',
}

# Bin config for monthly returns filtered by quarter
BIN_CONFIG = {'size': 0.01, 'min': -0.12, 'max': 0.12}  # 1.00%, -12% to +12%


def compute_monthly_o2c(asset_key, start, end):
    """Download data and compute all monthly O2C returns for a period."""
    data = download_asset_data(asset_key, start_date=start, end_date=end)
    monthly = data.resample('MS').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
    }).dropna()
    o2c = (monthly['close'] - monthly['open']) / monthly['open']
    o2c = o2c.dropna()
    o2c.name = 'o2c_monthly'
    return o2c


def filter_by_quarter(o2c, quarter_key):
    """Filter monthly O2C returns by quarter months."""
    months = QUARTERS[quarter_key]
    mask = o2c.index.month.isin(months)
    filtered = o2c[mask].copy()
    filtered.name = f'o2c_{quarter_key}'
    return filtered


def build_distribution_table(o2c):
    """Build frequency distribution table for monthly returns."""
    cfg = BIN_CONFIG
    bin_size = cfg['size']
    bin_min = cfg['min']
    bin_max = cfg['max']
    edges = np.arange(bin_min, bin_max + bin_size, bin_size)
    edges = np.round(edges, 10)
    rows = []

    for i in range(len(edges)):
        if i == 0:
            mask = o2c <= edges[i]
            intervalo = f"{edges[i]*100:.2f}%"
            clase = f"{edges[i]*100:.2f}%"
            rango = f"Menor de {edges[i]*100:.1f}%"
        else:
            lo = edges[i - 1]
            hi = edges[i]
            mask = (o2c > lo) & (o2c <= hi)
            intervalo = f"{hi*100:.2f}%"
            clase = f"{hi*100:.2f}%"
            rango = f"{lo*100:.1f} hasta {hi*100:.1f}%"

        freq = mask.sum()
        prob = freq / len(o2c) * 100
        rows.append({
            'Intervalo': intervalo,
            'Clase': clase,
            'Frecuencia': freq,
            'Rango': rango,
            'Probabilidad': prob,
        })

    # "y mayor" row
    mask_mayor = o2c > bin_max
    freq_mayor = mask_mayor.sum()
    prob_mayor = freq_mayor / len(o2c) * 100
    rows.append({
        'Intervalo': 'y mayor...',
        'Clase': '',
        'Frecuencia': freq_mayor,
        'Rango': '',
        'Probabilidad': prob_mayor,
    })

    df = pd.DataFrame(rows)
    df['Acumulado'] = df['Probabilidad'].cumsum()
    return df


def build_stats(o2c):
    """Build descriptive statistics matching Excel format."""
    return {
        'Media': f"{o2c.mean()*100:.3f}%",
        'Error tipico': f"{(o2c.std() / np.sqrt(len(o2c)))*100:.3f}%",
        'Mediana': f"{o2c.median()*100:.3f}%",
        'Moda': f"{o2c.mode().iloc[0]*100:.3f}%" if len(o2c.mode()) > 0 else "N/A",
        'Desviacion estandar': f"{o2c.std()*100:.3f}%",
        'Varianza de la muestra': f"{o2c.var()*100:.3f}%",
        'Curtosis': f"{o2c.kurtosis():.9f}",
        'Coef de asimetria': f"{o2c.skew():.9f}",
        'Rango': f"{(o2c.max() - o2c.min())*100:.3f}%",
        'Minimo': f"{o2c.min()*100:.3f}%",
        'Maximo': f"{o2c.max()*100:.3f}%",
        'Suma': f"{o2c.sum():.9f}",
        'Cuenta': f"{len(o2c)}",
    }


def build_sigma_table(o2c):
    """Build sigma table with count, %, and Gaussian comparison."""
    mean = o2c.mean()
    std = o2c.std()
    rows = []

    for sig in SIGMAS:
        superior = mean + sig * std
        inferior = mean - sig * std
        count = ((o2c >= inferior) & (o2c <= superior)).sum()
        pct = count / len(o2c) * 100
        gauss_pct = (scipy_stats.norm.cdf(sig) - scipy_stats.norm.cdf(-sig)) * 100

        rows.append({
            'Desviacion estandar': sig,
            'Superior': f"{superior*100:.3f}%",
            'Inferior': f"{inferior*100:.3f}%",
            'Cuenta': count,
            '% Cuenta': f"{pct:.2f}%",
            '% Dist Gauss': f"{gauss_pct:.3f}%",
        })

    return pd.DataFrame(rows)


def print_text_report(o2c, label, asset_key, quarter_key):
    """Print report to console."""
    q_label = QUARTER_LABELS[quarter_key]
    dist_table = build_distribution_table(o2c)
    stats_dict = build_stats(o2c)
    sigma_table = build_sigma_table(o2c)

    print()
    print("=" * 90)
    print(f"  {asset_key} - O2C MENSUAL {q_label}  |  Periodo: {label}  |  Cuenta: {len(o2c)}")
    print("=" * 90)

    # Distribution table
    print()
    print(f"{'O2C MENSUAL - ' + q_label:^90}")
    print(f"{'Intervalo':>12}  {'Clase':>10}  {'Frecuencia':>10}  {'Rango':>18}  {'Probabilidad':>12}  {'Acumulado':>12}")
    print("-" * 90)
    for _, r in dist_table.iterrows():
        print(f"{r['Intervalo']:>12}  {r['Clase']:>10}  {r['Frecuencia']:>10}  {r['Rango']:>18}  {r['Probabilidad']:>11.3f}%  {r['Acumulado']:>11.3f}%")

    # Stats
    print()
    print("-" * 40)
    for k, v in stats_dict.items():
        print(f"  {k:<26} {v:>12}")

    # Sigma table
    print()
    print(f"{'Desv Est':>10}  {'Superior':>12}  {'Inferior':>12}  {'Cuenta':>8}  {'% Cuenta':>10}  {'% Dist Gauss':>14}")
    print("-" * 75)
    for _, r in sigma_table.iterrows():
        print(f"{r['Desviacion estandar']:>10}  {r['Superior']:>12}  {r['Inferior']:>12}  {r['Cuenta']:>8}  {r['% Cuenta']:>10}  {r['% Dist Gauss']:>14}")

    print()


def generate_chart(o2c, label, asset_key, output_dir, quarter_key):
    """Generate chart matching the Excel format."""
    q_label = QUARTER_LABELS[quarter_key]
    dist_table = build_distribution_table(o2c)
    stats_dict = build_stats(o2c)
    sigma_table = build_sigma_table(o2c)

    # Adjust figure height based on number of rows in distribution table
    n_rows = len(dist_table)
    table_height = max(1.2, n_rows * 0.08)
    fig_height = 6 + table_height * 6 + 3

    fig = plt.figure(figsize=(18, fig_height))
    fig.suptitle(f"{asset_key} - O2C MENSUAL {q_label}  |  {label}", fontsize=16, fontweight='bold', y=0.98)

    gs = gridspec.GridSpec(3, 2, height_ratios=[table_height, 1, 0.35], hspace=0.35, wspace=0.3,
                           left=0.05, right=0.95, top=0.93, bottom=0.03)

    # ---- 1. Distribution Table ----
    ax_table = fig.add_subplot(gs[0, :])
    ax_table.axis('off')

    col_labels = ['Intervalo', 'Clase', 'Frecuencia', 'Rango', 'Probabilidad', 'Acumulado']
    table_data = []
    for _, r in dist_table.iterrows():
        table_data.append([
            r['Intervalo'], r['Clase'], int(r['Frecuencia']), r['Rango'],
            f"{r['Probabilidad']:.3f}%", f"{r['Acumulado']:.3f}%",
        ])

    tbl = ax_table.table(cellText=table_data, colLabels=col_labels,
                         loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7 if n_rows > 16 else 8)
    tbl.scale(1, 1.1)

    for j in range(len(col_labels)):
        tbl[0, j].set_facecolor('#4472C4')
        tbl[0, j].set_text_props(color='white', fontweight='bold')
    for i in range(1, len(table_data) + 1):
        for j in range(len(col_labels)):
            tbl[i, j].set_facecolor('#D9E2F3' if i % 2 == 0 else 'white')

    # ---- 2. Statistics Box ----
    ax_stats = fig.add_subplot(gs[1, 0])
    ax_stats.axis('off')

    stats_data = [[k, v] for k, v in stats_dict.items()]
    stats_tbl = ax_stats.table(cellText=stats_data, colLabels=['Metrica', 'Valor'],
                               loc='center', cellLoc='left')
    stats_tbl.auto_set_font_size(False)
    stats_tbl.set_fontsize(9)
    stats_tbl.scale(1, 1.3)

    for j in range(2):
        stats_tbl[0, j].set_facecolor('#4472C4')
        stats_tbl[0, j].set_text_props(color='white', fontweight='bold')
    for i in range(1, len(stats_data) + 1):
        stats_tbl[i, 0].set_text_props(fontweight='bold')
        for j in range(2):
            if i % 2 == 0:
                stats_tbl[i, j].set_facecolor('#D9E2F3')

    # ---- 3. Histogram ----
    ax_hist = fig.add_subplot(gs[1, 1])

    dist_main = dist_table[dist_table['Intervalo'] != 'y mayor...'].copy()
    bar_labels = dist_main['Clase'].values
    bar_values = dist_main['Probabilidad'].values

    colors = ['#C00000' if float(l.replace('%', '')) < 0 else '#548235' for l in bar_labels]
    x_pos = np.arange(len(bar_labels))
    ax_hist.bar(x_pos, bar_values, color=colors, edgecolor='white', width=0.85)
    ax_hist.set_xticks(x_pos[::2])
    ax_hist.set_xticklabels(bar_labels[::2], rotation=45, ha='right', fontsize=7)
    ax_hist.set_ylabel('Probabilidad %')
    ax_hist.set_title(f'O2C MENSUAL - {q_label}', fontweight='bold', fontsize=12)
    ax_hist.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.3f}%'))
    ax_hist.grid(axis='y', alpha=0.3)

    # ---- 4. Sigma Table ----
    ax_sigma = fig.add_subplot(gs[2, :])
    ax_sigma.axis('off')

    sigma_col_labels = ['Desviacion estandar', 'Superior', 'Inferior', 'Cuenta', '% Cuenta', '% Dist Gauss']
    sigma_data = []
    for _, r in sigma_table.iterrows():
        sigma_data.append([
            r['Desviacion estandar'], r['Superior'], r['Inferior'],
            int(r['Cuenta']), r['% Cuenta'], r['% Dist Gauss'],
        ])

    sig_tbl = ax_sigma.table(cellText=sigma_data, colLabels=sigma_col_labels,
                             loc='center', cellLoc='center')
    sig_tbl.auto_set_font_size(False)
    sig_tbl.set_fontsize(9)
    sig_tbl.scale(1, 1.5)

    for j in range(len(sigma_col_labels)):
        sig_tbl[0, j].set_facecolor('#4472C4')
        sig_tbl[0, j].set_text_props(color='white', fontweight='bold')
    for i in range(1, len(sigma_data) + 1):
        for j in range(len(sigma_col_labels)):
            if i % 2 == 0:
                sig_tbl[i, j].set_facecolor('#D9E2F3')

    # Save to output/charts/[ASSET]/quarterly/[Q1-Q4]/ structure
    output_path = Path(output_dir) / asset_key / 'quarterly' / quarter_key
    output_path.mkdir(parents=True, exist_ok=True)

    chart_name = f"DOR_O2C_{quarter_key}_{asset_key}_{label}_{datetime.now().strftime('%Y%m%d')}.png"
    filename = output_path / chart_name

    fig.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Chart saved: {filename}")
    return filename


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='DOR - Quarterly Seasonal O2C Analysis')
    parser.add_argument('--asset', '-a', type=str, default='NQ', help='Asset key (default: NQ)')
    parser.add_argument('--quarter', '-q', type=str, default='all',
                        choices=['Q1', 'Q2', 'Q3', 'Q4', 'all'],
                        help='Quarter to analyze (default: all)')
    parser.add_argument('--output', '-o', type=str, default='./output/charts', help='Output directory')
    args = parser.parse_args()

    asset_key = args.asset
    quarters_to_run = list(QUARTERS.keys()) if args.quarter == 'all' else [args.quarter]

    for start, end, label in PERIODS:
        print(f"\n{'='*60}")
        print(f"Downloading {asset_key} data for {label}...")
        print(f"{'='*60}")

        # Compute all monthly O2C once per period
        all_monthly_o2c = compute_monthly_o2c(asset_key, start, end)
        print(f"  Total monthly returns: {len(all_monthly_o2c)}")

        for qk in quarters_to_run:
            q_o2c = filter_by_quarter(all_monthly_o2c, qk)
            if len(q_o2c) < 3:
                print(f"  Skipping {qk} for {label}: only {len(q_o2c)} data points")
                continue
            print_text_report(q_o2c, label, asset_key, qk)
            generate_chart(q_o2c, label, asset_key, args.output, qk)
