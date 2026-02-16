"""
Visualization Module for DOR Framework
Creates professional charts for return distribution analysis.
Uses Simple Returns (Open-to-Close) with Upside/Downside separation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import seaborn as sns
from scipy import stats
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from datetime import datetime


# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class DORVisualizer:
    """Creates visualizations for return distribution analysis."""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path("./output/charts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Color scheme
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'positive': '#2E7D32',
            'negative': '#C62828',
            'neutral': '#546E7A',
            'sigma_lines': '#FF9800',
            'background': '#FAFAFA'
        }
    
    def plot_return_distribution(
        self,
        returns: pd.Series,
        title: str = "Return Distribution",
        timeframe: str = "",
        save: bool = True,
        show: bool = False
    ) -> plt.Figure:
        """
        Plot histogram with sigma bands and upside/downside stats.
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 11))
        fig.suptitle(f"{title} - {timeframe} (Simple Returns, Open-to-Close)", 
                     fontsize=14, fontweight='bold')
        
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        
        mean = returns.mean()
        std = returns.std()
        
        # 1. Full distribution with sigma bands
        ax1 = axes[0, 0]
        n_bins = max(10, min(60, len(returns) // 8))
        n_bins_half = max(5, n_bins // 2)
        
        if len(negative_returns) > 0:
            ax1.hist(negative_returns, bins=n_bins_half, alpha=0.7, 
                    color=self.colors['negative'], label=f'Negative (n={len(negative_returns)})', density=True)
        if len(positive_returns) > 0:
            ax1.hist(positive_returns, bins=n_bins_half, alpha=0.7, 
                    color=self.colors['positive'], label=f'Positive (n={len(positive_returns)})', density=True)
        
        # Normal fit
        x = np.linspace(returns.min(), returns.max(), 200)
        pdf = stats.norm.pdf(x, mean, std)
        ax1.plot(x, pdf, 'k-', lw=2, label='Normal fit')
        
        # Sigma bands
        sigma_colors = ['#FFC107', '#FF9800', '#FF5722', '#D32F2F']
        sigma_labels = ['0.5', '1.0', '1.5', '2.0']
        for i, sig in enumerate([0.5, 1.0, 1.5, 2.0]):
            ax1.axvline(mean + sig*std, color=sigma_colors[i], linestyle='--', alpha=0.7, lw=1)
            ax1.axvline(mean - sig*std, color=sigma_colors[i], linestyle='--', alpha=0.7, lw=1)
            if sig in [1.0, 2.0]:
                ymax = ax1.get_ylim()[1]
                ax1.text(mean + sig*std, ymax*0.95, f'+{sigma_labels[i]}s', fontsize=7, 
                        ha='center', color=sigma_colors[i], fontweight='bold')
                ax1.text(mean - sig*std, ymax*0.95, f'-{sigma_labels[i]}s', fontsize=7, 
                        ha='center', color=sigma_colors[i], fontweight='bold')
        
        ax1.axvline(mean, color='white', linestyle='-', lw=2, alpha=0.9)
        ax1.set_xlabel('Return')
        ax1.set_ylabel('Density')
        ax1.set_title('Distribution with Sigma Bands')
        ax1.legend(fontsize=8)
        
        # 2. Q-Q Plot
        ax2 = axes[0, 1]
        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title('Q-Q Plot (Normal)')
        ax2.get_lines()[0].set_markerfacecolor(self.colors['primary'])
        ax2.get_lines()[0].set_markersize(3)
        
        # 3. Sigma bands table
        ax3 = axes[1, 0]
        ax3.axis('off')
        
        sigmas = [0.5, 1.0, 1.5, 2.0]
        
        # General sigma table
        table_text = "SIGMA BANDS\n"
        table_text += "=" * 42 + "\n"
        table_text += f"{'':8s} {'Inferior':>12s} {'Superior':>12s}\n"
        table_text += "-" * 42 + "\n"
        for sig in sigmas:
            lo = (mean - sig * std) * 100
            hi = (mean + sig * std) * 100
            table_text += f"+/-{sig:.1f}s   {lo:>+10.4f}%  {hi:>+10.4f}%\n"
        
        # Upside sigma
        if len(positive_returns) > 1:
            pm, ps = positive_returns.mean(), positive_returns.std()
            table_text += f"\nUPSIDE  (Mean: {pm*100:+.4f}%, Std: {ps*100:.4f}%)\n"
            table_text += "-" * 42 + "\n"
            for sig in sigmas:
                lo = (pm - sig * ps) * 100
                hi = (pm + sig * ps) * 100
                table_text += f"+/-{sig:.1f}s   {lo:>+10.4f}%  {hi:>+10.4f}%\n"
        
        # Downside sigma
        if len(negative_returns) > 1:
            nm = negative_returns.mean()
            ns = np.abs(negative_returns).std()
            table_text += f"\nDOWNSIDE  (Mean: {nm*100:.4f}%, Std: {ns*100:.4f}%)\n"
            table_text += "-" * 42 + "\n"
            for sig in sigmas:
                lo = (nm - sig * ns) * 100
                hi = (nm + sig * ns) * 100
                table_text += f"+/-{sig:.1f}s   {lo:>+10.4f}%  {hi:>+10.4f}%\n"
        
        ax3.text(0.05, 0.95, table_text, transform=ax3.transAxes,
                fontsize=9, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        # 4. Statistics summary
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        pos_std = positive_returns.std() if len(positive_returns) > 1 else 0
        neg_std = np.abs(negative_returns).std() if len(negative_returns) > 1 else 0
        vol_asym = neg_std / pos_std if pos_std > 0 else float('inf')
        
        stats_text = (
            f"DISTRIBUTION STATISTICS\n"
            f"{'='*42}\n"
            f"Observations:    {len(returns):,}\n"
            f"Positive:        {len(positive_returns):,} ({100*len(positive_returns)/len(returns):.1f}%)\n"
            f"Negative:        {len(negative_returns):,} ({100*len(negative_returns)/len(returns):.1f}%)\n"
            f"\n"
            f"OVERALL\n"
            f"  Mean:          {mean*100:+.4f}%\n"
            f"  Std Dev:       {std*100:.4f}%\n"
            f"  Skewness:      {stats.skew(returns):+.4f}\n"
            f"  Kurtosis:      {stats.kurtosis(returns):+.4f}\n"
            f"\n"
            f"UPSIDE\n"
            f"  Mean:          {positive_returns.mean()*100:+.4f}%\n"
            f"  Std Dev:       {pos_std*100:.4f}%\n"
            f"\n"
            f"DOWNSIDE\n"
            f"  Mean:          {negative_returns.mean()*100:.4f}%\n"
            f"  Std Dev:       {neg_std*100:.4f}%\n"
            f"\n"
            f"ASYMMETRY\n"
            f"  Ratio (D/U):   {vol_asym:.4f}x\n"
            f"  VaR 95%:       {np.percentile(returns, 5)*100:.4f}%\n"
            f"  VaR 99%:       {np.percentile(returns, 1)*100:.4f}%\n"
        )
        
        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes,
                fontsize=9, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / f"distribution_{timeframe}_{datetime.now().strftime('%Y%m%d')}.png"
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close(fig)
        
        return fig
    
    def plot_volatility_comparison(
        self,
        volatilities: pd.DataFrame,
        title: str = "Volatility Estimators Comparison",
        save: bool = True
    ) -> plt.Figure:
        """Plot comparison of different volatility estimators."""
        fig, ax = plt.subplots(figsize=(14, 6))
        
        for col in volatilities.columns:
            ax.plot(volatilities.index, volatilities[col], label=col, alpha=0.8)
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Annualized Volatility')
        ax.set_title(title)
        ax.legend(loc='upper right')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / f"volatility_comparison_{datetime.now().strftime('%Y%m%d')}.png"
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
        
        plt.close(fig)
        return fig
    
    def plot_timeframe_comparison(
        self,
        returns_by_tf: Dict[str, pd.Series],
        save: bool = True
    ) -> plt.Figure:
        """Compare distributions across timeframes with sigma bands."""
        n_tf = len(returns_by_tf)
        fig, axes = plt.subplots(2, n_tf, figsize=(4 * n_tf, 9))
        
        if n_tf == 1:
            axes = axes.reshape(2, 1)
        
        fig.suptitle('Return Distributions by Timeframe (Simple Returns, Upside vs Downside)', 
                     fontsize=14, fontweight='bold')
        
        for i, (tf, returns) in enumerate(returns_by_tf.items()):
            pos = returns[returns > 0]
            neg = returns[returns < 0]
            mean = returns.mean()
            std = returns.std()
            
            # Top row: histograms with sigma lines
            ax_top = axes[0, i]
            n_bins = max(5, min(30, len(returns) // 5))
            
            if len(neg) > 0:
                ax_top.hist(neg, bins=n_bins, alpha=0.7, color=self.colors['negative'], 
                           label='Downside', density=True)
            if len(pos) > 0:
                ax_top.hist(pos, bins=n_bins, alpha=0.7, color=self.colors['positive'], 
                           label='Upside', density=True)
            
            # Sigma lines
            for sig in [1.0, 2.0]:
                ax_top.axvline(mean + sig*std, color='#FF9800', linestyle='--', alpha=0.6, lw=1)
                ax_top.axvline(mean - sig*std, color='#FF9800', linestyle='--', alpha=0.6, lw=1)
            ax_top.axvline(mean, color='white', linestyle='-', lw=1.5, alpha=0.8)
            
            ax_top.set_title(f'{tf}\n(n={len(returns)})')
            if i == 0:
                ax_top.legend(fontsize=7)
            
            # Bottom row: stats
            ax_bot = axes[1, i]
            ax_bot.axis('off')
            
            pos_std = pos.std() if len(pos) > 1 else 0
            neg_std = np.abs(neg).std() if len(neg) > 1 else 0
            ratio = neg_std / pos_std if pos_std > 0 else float('inf')
            
            stats_text = (
                f"Mean: {mean*100:+.3f}%\n"
                f"Std:  {std*100:.3f}%\n"
                f"Skew: {stats.skew(returns):+.2f}\n"
                f"Kurt: {stats.kurtosis(returns):+.2f}\n"
                f"\n"
                f"+1s:  {(mean+std)*100:+.3f}%\n"
                f"-1s:  {(mean-std)*100:+.3f}%\n"
                f"+2s:  {(mean+2*std)*100:+.3f}%\n"
                f"-2s:  {(mean-2*std)*100:+.3f}%\n"
                f"\n"
                f"Up Std:   {pos_std*100:.3f}%\n"
                f"Down Std: {neg_std*100:.3f}%\n"
                f"Ratio:    {ratio:.2f}x"
            )
            ax_bot.text(0.1, 0.95, stats_text, transform=ax_bot.transAxes,
                       fontsize=8, verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / f"timeframe_comparison_{datetime.now().strftime('%Y%m%d')}.png"
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
        
        plt.close(fig)
        return fig
    
    def plot_o2c_distribution(
        self,
        o2c: pd.Series,
        h2l: pd.Series,
        asset_name: str = "NQ",
        save: bool = True
    ) -> plt.Figure:
        """
        Plot dedicated Open-to-Close distribution with sigma bands.
        """
        fig, axes = plt.subplots(1, 3, figsize=(18, 7))
        fig.suptitle(f'{asset_name} - Open to Close Distribution (Simple Returns)', 
                     fontsize=14, fontweight='bold')
        
        mean = o2c.mean()
        std = o2c.std()
        pos = o2c[o2c > 0]
        neg = o2c[o2c < 0]
        
        # 1. O2C histogram with sigma bands
        ax1 = axes[0]
        n_bins = max(10, min(60, len(o2c) // 8))
        
        ax1.hist(neg, bins=n_bins//2, alpha=0.7, color=self.colors['negative'], 
                label=f'Negative ({len(neg)})', density=True)
        ax1.hist(pos, bins=n_bins//2, alpha=0.7, color=self.colors['positive'], 
                label=f'Positive ({len(pos)})', density=True)
        
        # Normal fit
        x = np.linspace(o2c.min(), o2c.max(), 200)
        pdf = stats.norm.pdf(x, mean, std)
        ax1.plot(x, pdf, 'k-', lw=2, alpha=0.7)
        
        # Sigma bands
        sigma_colors = ['#FFC107', '#FF9800', '#FF5722', '#D32F2F']
        for i, sig in enumerate([0.5, 1.0, 1.5, 2.0]):
            ax1.axvline(mean + sig*std, color=sigma_colors[i], linestyle='--', alpha=0.7, lw=1)
            ax1.axvline(mean - sig*std, color=sigma_colors[i], linestyle='--', alpha=0.7, lw=1)
        ax1.axvline(mean, color='white', linestyle='-', lw=2)
        
        ax1.set_title('Open-to-Close Returns')
        ax1.set_xlabel('Return')
        ax1.set_ylabel('Density')
        ax1.legend(fontsize=8)
        
        # 2. H2L histogram
        ax2 = axes[1]
        ax2.hist(h2l, bins=n_bins, alpha=0.7, color=self.colors['primary'], density=True)
        h2l_mean = h2l.mean()
        h2l_std = h2l.std()
        ax2.axvline(h2l_mean, color='white', linestyle='-', lw=2)
        for i, sig in enumerate([1.0, 2.0]):
            ax2.axvline(h2l_mean + sig*h2l_std, color=sigma_colors[i+1], linestyle='--', alpha=0.7)
        ax2.set_title(f'High-to-Low Range\nMean: {h2l_mean*100:.3f}%  Std: {h2l_std*100:.3f}%')
        ax2.set_xlabel('Range')
        ax2.set_ylabel('Density')
        
        # 3. Sigma table
        ax3 = axes[2]
        ax3.axis('off')
        
        pos_std = pos.std() if len(pos) > 1 else 0
        neg_std = np.abs(neg).std() if len(neg) > 1 else 0
        pm, nm = pos.mean(), neg.mean()
        
        table = (
            f"O2C SIGMA BANDS\n"
            f"{'='*44}\n"
            f"Obs: {len(o2c):,}  |  Pos: {len(pos):,} ({100*len(pos)/len(o2c):.1f}%)  |  Neg: {len(neg):,} ({100*len(neg)/len(o2c):.1f}%)\n"
            f"\n"
            f"GENERAL  (Mean: {mean*100:+.4f}%  Std: {std*100:.4f}%)\n"
            f"{'-'*44}\n"
            f"{'Sigma':<8} {'Inferior':>12} {'Superior':>12}\n"
        )
        for sig in [0.5, 1.0, 1.5, 2.0]:
            lo = (mean - sig*std)*100
            hi = (mean + sig*std)*100
            table += f"+/-{sig:.1f}s   {lo:>+10.4f}%  {hi:>+10.4f}%\n"
        
        table += (
            f"\nUPSIDE  (Mean: {pm*100:+.4f}%  Std: {pos_std*100:.4f}%)\n"
            f"{'-'*44}\n"
        )
        for sig in [0.5, 1.0, 1.5, 2.0]:
            lo = (pm - sig*pos_std)*100
            hi = (pm + sig*pos_std)*100
            table += f"+/-{sig:.1f}s   {lo:>+10.4f}%  {hi:>+10.4f}%\n"
        
        table += (
            f"\nDOWNSIDE  (Mean: {nm*100:.4f}%  Std: {neg_std*100:.4f}%)\n"
            f"{'-'*44}\n"
        )
        for sig in [0.5, 1.0, 1.5, 2.0]:
            lo = (nm - sig*neg_std)*100
            hi = (nm + sig*neg_std)*100
            table += f"+/-{sig:.1f}s   {lo:>+10.4f}%  {hi:>+10.4f}%\n"
        
        table += (
            f"\nASYMMETRY\n"
            f"  Ratio (D/U): {neg_std/pos_std:.4f}x\n"
        )
        
        ax3.text(0.02, 0.98, table, transform=ax3.transAxes,
                fontsize=8.5, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / f"o2c_distribution_{asset_name}_{datetime.now().strftime('%Y%m%d')}.png"
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
        
        plt.close(fig)
        return fig
