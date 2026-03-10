"""
D3 Multi-Percentile — Styled Chart Exporter
=============================================
Generates styled PNG comparison tables for the 3-tier D3 analysis.

Per asset produces two charts:
  - Bull comparison (50% vs 75%)
  - Bear comparison (50% vs 25%)

Matches the existing D2 visual design: black bg, green/red accents, monospace.

Usage:
  python -m research_scripts.export_d3_multi_percentile_styled
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research_scripts.analyze_d3_multi_percentile import (
    analyze_asset, ASSETS, MONTH_NAMES
)

# ── Visual Style Guide (matching existing D2 charts) ──
BG_COLOR         = '#000000'
TEXT_COLOR        = '#ffffff'
ACCENT_GREEN     = '#00ff44'
ACCENT_GREEN_DIM = '#003311'
ACCENT_RED       = '#ff0044'
ACCENT_RED_DIM   = '#330011'
GRAY_TEXT        = '#888888'
LINE_COLOR       = '#333333'
FONT_FAMILY      = 'monospace'
HIGHLIGHT_BG     = '#0d1f0d'  # Subtle green tint for improved cells

plt.rcParams.update({
    'axes.facecolor':   BG_COLOR,
    'figure.facecolor': BG_COLOR,
    'axes.edgecolor':   LINE_COLOR,
    'axes.labelcolor':  TEXT_COLOR,
    'xtick.color':      GRAY_TEXT,
    'ytick.color':      GRAY_TEXT,
    'text.color':       TEXT_COLOR,
    'font.family':      FONT_FAMILY,
})

def _fmt_cell(stat_dict):
    """Format a stats dict into display text."""
    prob = stat_dict['prob']
    n = stat_dict['n']
    if np.isnan(prob) or n < 8:
        return f"N/A (n={n})", False
    sig_marker = " *" if stat_dict['is_sig'] else ""
    return f"{prob:.1f}%{sig_marker}", stat_dict['is_sig']


def _render_table(asset_key, side, results, output_dir, label_suffix=""):
    """
    Render a styled comparison table.
    side: 'bull' or 'bear'
    """
    is_bull = (side == 'bull')
    tier_base = '50%'
    tier_extreme = '75%'

    if is_bull:
        title = f"{asset_key} D3 BULL SIGNAL {label_suffix} — PERCENTILE COMPARISON"
        subtitle = "IF WEDNESDAY CLOSES ABOVE THRESHOLD OF MON-WED RANGE"
        metric_ext = 'new_high'
        metric_cls = 'green_wk'
        col_labels = [
            '50%: New High', '50%: Green Wk', '50%: N',
            '75%: New High', '75%: Green Wk', '75%: N',
            'Δ High%',
        ]
        accent = ACCENT_GREEN
        accent_dim = ACCENT_GREEN_DIM
    else:
        title = f"{asset_key} D3 BEAR SIGNAL {label_suffix} — PERCENTILE COMPARISON"
        subtitle = "IF WEDNESDAY CLOSES BELOW THRESHOLD OF MON-WED RANGE"
        metric_ext = 'new_low'
        metric_cls = 'red_wk'
        col_labels = [
            '50%: New Low', '50%: Red Wk', '50%: N',
            '25%: New Low', '25%: Red Wk', '25%: N',
            'Δ Low%',
        ]
        accent = ACCENT_RED
        accent_dim = ACCENT_RED_DIM

    cell_text = []
    cell_colors = []
    sig_map = []  # Track significance for text coloring

    for m in range(1, 13):
        r_base = results[tier_base][m][side]
        r_ext  = results[tier_extreme][m][side]

        s_base_ext = r_base[metric_ext]
        s_base_cls = r_base[metric_cls]
        s_ext_ext  = r_ext[metric_ext]
        s_ext_cls  = r_ext[metric_cls]

        txt_b_ext, sig_b_ext = _fmt_cell(s_base_ext)
        txt_b_cls, sig_b_cls = _fmt_cell(s_base_cls)
        n_base = str(s_base_ext['n'])

        txt_e_ext, sig_e_ext = _fmt_cell(s_ext_ext)
        txt_e_cls, sig_e_cls = _fmt_cell(s_ext_cls)
        n_ext = str(s_ext_ext['n'])

        # Delta
        p_b = s_base_ext['prob']
        p_e = s_ext_ext['prob']
        if np.isnan(p_b) or np.isnan(p_e) or s_ext_ext['n'] < 8:
            delta_txt = "N/A"
            delta_positive = False
        else:
            diff = p_e - p_b
            delta_txt = f"{diff:+.1f}%"
            delta_positive = diff > 0

        row_text = [txt_b_ext, txt_b_cls, n_base, txt_e_ext, txt_e_cls, n_ext, delta_txt]
        cell_text.append(row_text)

        # Cell background colors
        row_colors = [BG_COLOR] * 7
        if sig_b_ext: row_colors[0] = accent_dim
        if sig_b_cls: row_colors[1] = accent_dim
        if sig_e_ext: row_colors[3] = accent_dim
        if sig_e_cls: row_colors[4] = accent_dim
        if delta_positive and not np.isnan(p_e):
            row_colors[6] = HIGHLIGHT_BG if is_bull else '#1f0d0d'
        cell_colors.append(row_colors)

        sig_map.append([sig_b_ext, sig_b_cls, False, sig_e_ext, sig_e_cls, False, delta_positive])

    # ── Render ──
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.axis('off')

    plt.suptitle(title, fontsize=20, fontweight='bold', color=TEXT_COLOR, y=0.96)
    fig.text(0.5, 0.92, subtitle, ha='center', fontsize=11, color=GRAY_TEXT)

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        rowLabels=MONTH_NAMES,
        cellColours=cell_colors,
        loc='center',
        cellLoc='center',
    )

    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2.4)

    # Style cells
    for (row, col), cell in table.get_celld().items():
        if row == 0:  # Header
            cell.set_text_props(weight='bold', color=TEXT_COLOR, fontsize=10)
            cell.set_facecolor(LINE_COLOR)
            cell.set_linewidth(1)
            cell.set_edgecolor(BG_COLOR)
        elif col == -1:  # Row labels (months)
            cell.set_text_props(weight='bold', color=GRAY_TEXT)
            cell.set_facecolor(BG_COLOR)
            cell.set_edgecolor(BG_COLOR)
        else:  # Data cells
            cell.set_edgecolor(LINE_COLOR)
            cell.set_linewidth(0.5)
            cell.set_text_props(color=TEXT_COLOR)

            # Highlight significant cells and delta
            if row > 0 and col >= 0:
                sig_row = sig_map[row - 1]
                if col < len(sig_row) and sig_row[col]:
                    cell.set_text_props(weight='bold', color=accent)
                # N columns dimmer
                if col in (2, 5):
                    cell.set_text_props(color=GRAY_TEXT)

    # Separator line between 50% and 75% blocks (visual hint)
    fig.text(0.5, 0.05,
             "* = STATISTICALLY SIGNIFICANT (p<0.05) & >60% PROBABILITY  |  Δ = Prob change from 50% to extreme tier",
             ha='center', fontsize=9, color=GRAY_TEXT)

    # Save
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{asset_key}_d3_{side}_percentile_comparison.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor=BG_COLOR)
    print(f"  ✓ Saved: {filename}")
    plt.close()


def export_all():
    """Generate all charts for all assets."""
    
    # Generate 20 Years
    print("\n── Generating FULL HISTORY (20 Yrs) Charts ──")
    out_dir_20yr = 'output/charts/strategy/D3_Percentiles'
    for asset in ASSETS:
        results, total = analyze_asset(asset, start_date='2000-01-01')
        _render_table(asset, 'bull', results, out_dir_20yr, label_suffix="(20 YRS)")
        _render_table(asset, 'bear', results, out_dir_20yr, label_suffix="(20 YRS)")
        
    # Generate 2020+
    print("\n── Generating RECENT HISTORY (2020+) Charts ──")
    out_dir_2020 = 'output/charts/strategy/D3_Percentiles_2020'
    for asset in ASSETS:
        results, total = analyze_asset(asset, start_date='2020-01-01')
        _render_table(asset, 'bull', results, out_dir_2020, label_suffix="(2020+)")
        _render_table(asset, 'bear', results, out_dir_2020, label_suffix="(2020+)")

    print(f"\n✓ All charts saved.")


if __name__ == '__main__':
    export_all()
