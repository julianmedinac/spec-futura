"""
Report Generator Module
Creates comprehensive Excel and text reports with upside/downside analysis.
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class AsymmetricStats:
    """Statistics separated by upside and downside."""
    # Overall
    count: int
    mean: float
    std: float
    skewness: float
    kurtosis: float
    
    # Upside (positive returns)
    upside_count: int
    upside_mean: float
    upside_std: float  # Semi-deviation upside
    
    # Downside (negative returns)
    downside_count: int
    downside_mean: float
    downside_std: float  # Semi-deviation downside
    
    # Ratios
    upside_ratio: float  # % of positive returns
    downside_ratio: float  # % of negative returns
    volatility_asymmetry: float  # downside_std / upside_std
    
    # Annualized
    annualized_mean: float
    annualized_std: float
    annualized_upside_std: float
    annualized_downside_std: float


class ReportGenerator:
    """
    Generates comprehensive reports for return distribution analysis.
    Focuses on asymmetric risk metrics (upside vs downside).
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path("./output/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def compute_asymmetric_stats(
        self,
        returns: pd.Series,
        periods_per_year: float = 252
    ) -> AsymmetricStats:
        """
        Compute statistics with upside/downside separation.
        
        Args:
            returns: Series of returns
            periods_per_year: For annualization
            
        Returns:
            AsymmetricStats object
        """
        positive = returns[returns > 0]
        negative = returns[returns < 0]
        
        # Semi-deviations
        upside_std = positive.std(ddof=1) if len(positive) > 1 else 0
        downside_std = np.abs(negative).std(ddof=1) if len(negative) > 1 else 0
        
        # Volatility asymmetry ratio
        vol_asymmetry = downside_std / upside_std if upside_std > 0 else np.inf
        
        return AsymmetricStats(
            count=len(returns),
            mean=returns.mean(),
            std=returns.std(ddof=1),
            skewness=stats.skew(returns),
            kurtosis=stats.kurtosis(returns),
            upside_count=len(positive),
            upside_mean=positive.mean() if len(positive) > 0 else 0,
            upside_std=upside_std,
            downside_count=len(negative),
            downside_mean=negative.mean() if len(negative) > 0 else 0,
            downside_std=downside_std,
            upside_ratio=len(positive) / len(returns) if len(returns) > 0 else 0,
            downside_ratio=len(negative) / len(returns) if len(returns) > 0 else 0,
            volatility_asymmetry=vol_asymmetry,
            annualized_mean=returns.mean() * periods_per_year,
            annualized_std=returns.std() * np.sqrt(periods_per_year),
            annualized_upside_std=upside_std * np.sqrt(periods_per_year),
            annualized_downside_std=downside_std * np.sqrt(periods_per_year),
        )
    
    def generate_excel_report(
        self,
        asset_name: str,
        returns_by_timeframe: Dict[str, pd.Series],
        price_data: pd.DataFrame,
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate comprehensive Excel report.
        
        Args:
            asset_name: Name of the asset
            returns_by_timeframe: Dict of timeframe -> returns series
            price_data: Original OHLCV data
            filename: Optional custom filename
            
        Returns:
            Path to generated file
        """
        if filename is None:
            filename = f"DOR_Report_{asset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        filepath = self.output_dir / filename
        
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Formats
            header_fmt = workbook.add_format({
                'bold': True, 'bg_color': '#2E86AB', 'font_color': 'white',
                'border': 1, 'align': 'center'
            })
            pct_fmt = workbook.add_format({'num_format': '0.00%', 'align': 'right'})
            num_fmt = workbook.add_format({'num_format': '0.0000', 'align': 'right'})
            pos_fmt = workbook.add_format({'num_format': '0.00%', 'font_color': '#2E7D32'})
            neg_fmt = workbook.add_format({'num_format': '0.00%', 'font_color': '#C62828'})
            
            # 1. Summary Sheet
            self._write_summary_sheet(writer, asset_name, returns_by_timeframe, header_fmt)
            
            # 2. Asymmetric Analysis Sheet
            self._write_asymmetric_sheet(writer, returns_by_timeframe, header_fmt)
            
            # 3. Price Data Sheet
            price_data.to_excel(writer, sheet_name='Price Data', index=True)
            
            # 4. Individual timeframe sheets with returns
            for tf, returns in returns_by_timeframe.items():
                sheet_name = f'Returns_{tf}'
                returns_df = returns.to_frame(name='return')
                returns_df['return_pct'] = returns_df['return'] * 100
                returns_df.to_excel(writer, sheet_name=sheet_name, index=True)
        
        print(f"Excel report saved to: {filepath}")
        return filepath
    
    def _write_summary_sheet(
        self,
        writer,
        asset_name: str,
        returns_by_tf: Dict[str, pd.Series],
        header_fmt
    ):
        """Write summary statistics sheet."""
        # Prepare summary data
        summary_data = []
        
        periods_map = {'1D': 252, '1W': 52, '1M': 12, '1Q': 4, '6M': 2, '1Y': 1}
        
        for tf, returns in returns_by_tf.items():
            periods = periods_map.get(tf, 252)
            stats_obj = self.compute_asymmetric_stats(returns, periods)
            
            summary_data.append({
                'Timeframe': tf,
                'Count': stats_obj.count,
                'Mean (Period)': stats_obj.mean,
                'Mean (Annual)': stats_obj.annualized_mean,
                'Std (Period)': stats_obj.std,
                'Std (Annual)': stats_obj.annualized_std,
                'Upside Std (Annual)': stats_obj.annualized_upside_std,
                'Downside Std (Annual)': stats_obj.annualized_downside_std,
                'Vol Asymmetry': stats_obj.volatility_asymmetry,
                'Skewness': stats_obj.skewness,
                'Kurtosis': stats_obj.kurtosis,
                'Upside %': stats_obj.upside_ratio,
                'Downside %': stats_obj.downside_ratio,
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False, startrow=2)
        
        # Add title
        worksheet = writer.sheets['Summary']
        worksheet.write(0, 0, f'Distribution of Returns Analysis: {asset_name}', header_fmt)
        worksheet.write(1, 0, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    def _write_asymmetric_sheet(
        self,
        writer,
        returns_by_tf: Dict[str, pd.Series],
        header_fmt
    ):
        """Write detailed asymmetric analysis sheet."""
        periods_map = {'1D': 252, '1W': 52, '1M': 12, '1Q': 4, '6M': 2, '1Y': 1}
        
        asymmetric_data = []
        
        for tf, returns in returns_by_tf.items():
            periods = periods_map.get(tf, 252)
            positive = returns[returns > 0]
            negative = returns[returns < 0]
            
            asymmetric_data.append({
                'Timeframe': tf,
                'Total Obs': len(returns),
                
                # Upside
                'Upside Count': len(positive),
                'Upside %': len(positive) / len(returns) * 100,
                'Upside Mean': positive.mean() if len(positive) > 0 else 0,
                'Upside Std': positive.std() if len(positive) > 1 else 0,
                'Upside Max': positive.max() if len(positive) > 0 else 0,
                
                # Downside
                'Downside Count': len(negative),
                'Downside %': len(negative) / len(returns) * 100,
                'Downside Mean': negative.mean() if len(negative) > 0 else 0,
                'Downside Std': np.abs(negative).std() if len(negative) > 1 else 0,
                'Downside Min': negative.min() if len(negative) > 0 else 0,
                
                # Ratios
                'Gain/Loss Ratio': (positive.mean() / abs(negative.mean())) if len(negative) > 0 and negative.mean() != 0 else np.inf,
                'Vol Asymmetry (Down/Up)': (np.abs(negative).std() / positive.std()) if len(positive) > 1 and positive.std() > 0 else np.inf,
            })
        
        asym_df = pd.DataFrame(asymmetric_data)
        asym_df.to_excel(writer, sheet_name='Asymmetric Analysis', index=False, startrow=1)
        
        worksheet = writer.sheets['Asymmetric Analysis']
        worksheet.write(0, 0, 'Upside vs Downside Analysis', header_fmt)
    
    def generate_text_report(
        self,
        asset_name: str,
        returns_by_timeframe: Dict[str, pd.Series],
        filename: Optional[str] = None
    ) -> Path:
        """Generate text summary report."""
        if filename is None:
            filename = f"DOR_Report_{asset_name}_{datetime.now().strftime('%Y%m%d')}.txt"
        
        filepath = self.output_dir / filename
        
        periods_map = {'1D': 252, '1W': 52, '1M': 12, '1Q': 4, '6M': 2, '1Y': 1}
        
        lines = [
            "=" * 80,
            f"DISTRIBUTION OF RETURNS ANALYSIS: {asset_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
        ]
        
        for tf, returns in returns_by_timeframe.items():
            periods = periods_map.get(tf, 252)
            stats_obj = self.compute_asymmetric_stats(returns, periods)
            
            lines.extend([
                f"\n{'='*40}",
                f"TIMEFRAME: {tf}",
                f"{'='*40}",
                f"Observations: {stats_obj.count}",
                "",
                "OVERALL STATISTICS",
                f"  Mean (period):     {stats_obj.mean*100:+.4f}%",
                f"  Mean (annual):     {stats_obj.annualized_mean*100:+.2f}%",
                f"  Std (period):      {stats_obj.std*100:.4f}%",
                f"  Std (annual):      {stats_obj.annualized_std*100:.2f}%",
                f"  Skewness:          {stats_obj.skewness:+.3f}",
                f"  Excess Kurtosis:   {stats_obj.kurtosis:+.3f}",
                "",
                "UPSIDE (Positive Returns)",
                f"  Count:             {stats_obj.upside_count} ({stats_obj.upside_ratio*100:.1f}%)",
                f"  Mean:              {stats_obj.upside_mean*100:+.4f}%",
                f"  Std (semi-dev):    {stats_obj.upside_std*100:.4f}%",
                f"  Std (annual):      {stats_obj.annualized_upside_std*100:.2f}%",
                "",
                "DOWNSIDE (Negative Returns)",
                f"  Count:             {stats_obj.downside_count} ({stats_obj.downside_ratio*100:.1f}%)",
                f"  Mean:              {stats_obj.downside_mean*100:.4f}%",
                f"  Std (semi-dev):    {stats_obj.downside_std*100:.4f}%",
                f"  Std (annual):      {stats_obj.annualized_downside_std*100:.2f}%",
                "",
                "ASYMMETRY ANALYSIS",
                f"  Vol Asymmetry (Down/Up): {stats_obj.volatility_asymmetry:.3f}x",
                f"  Interpretation: {'Downside vol > Upside' if stats_obj.volatility_asymmetry > 1 else 'Upside vol > Downside'}",
            ])
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"Text report saved to: {filepath}")
        return filepath
