"""
DOR Framework - Main Analysis Script
Distribution of Returns Analysis for Financial Assets

This script orchestrates the complete analysis pipeline:
1. Download data from Yahoo Finance
2. Calculate returns for all timeframes
3. Analyze distributions (with upside/downside separation)
4. Generate reports and visualizations
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime

# Import framework modules
from config.assets import get_asset, list_assets, ASSETS
from config.timeframes import get_timeframe, list_timeframes, TIMEFRAMES
from src.data.data_loader import DataLoader, download_asset_data
from src.returns.returns_calculator import ReturnsCalculator
from src.distributions.distribution_analyzer import DistributionAnalyzer
from src.volatility.volatility_calculator import VolatilityCalculator
from src.reports.report_generator import ReportGenerator
from src.visualization.visualizer import DORVisualizer


def run_full_analysis(
    asset_key: str = "NQ",
    years_back: int = 10,
    output_dir: str = "./output"
) -> dict:
    """
    Run complete distribution of returns analysis.
    
    Args:
        asset_key: Asset to analyze (e.g., 'NQ', 'ES', 'SPY')
        years_back: Years of historical data
        output_dir: Output directory for reports
        
    Returns:
        Dictionary with all analysis results
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print(f"DOR FRAMEWORK - Distribution of Returns Analysis")
    print(f"Asset: {asset_key}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Download Data
    print("\n[1/5] Downloading data...")
    asset = get_asset(asset_key)
    loader = DataLoader()
    price_data = loader.download(asset_key, years_back=years_back)
    print(f"  Downloaded {len(price_data)} records from {price_data.index[0].date()} to {price_data.index[-1].date()}")
    
    # 2. Calculate Returns for All Timeframes (Simple Returns)
    print("\n[2/5] Calculating returns for all timeframes (simple returns)...")
    returns_calc = ReturnsCalculator(price_data, price_column='close')
    returns_by_tf = returns_calc.get_all_timeframe_returns(return_type='simple')
    
    # Also calculate Open-to-Close returns
    o2c_returns = returns_calc.open_to_close_returns()
    h2l_range = returns_calc.high_to_low_range()
    
    for tf, returns in returns_by_tf.items():
        print(f"  {tf}: {len(returns)} observations")
    print(f"  O2C: {len(o2c_returns)} observations")
    print(f"  H2L: {len(h2l_range)} observations")
    
    # 3. Analyze Distributions with Upside/Downside
    print("\n[3/5] Analyzing distributions...")
    analysis_results = {}
    
    periods_map = {'1D': 252, '1W': 52, '1M': 12, '1Q': 4, '6M': 2, '1Y': 1}
    
    for tf, returns in returns_by_tf.items():
        periods = periods_map.get(tf, 252)
        analyzer = DistributionAnalyzer(returns, periods_per_year=periods)
        
        # Get comprehensive stats
        stats_dict = analyzer.compute_basic_stats().to_dict()
        normality = analyzer.test_normality()
        tail_analysis = analyzer.get_tail_analysis()
        var_results = analyzer.compute_var()
        
        # Add upside/downside analysis
        positive = returns[returns > 0]
        negative = returns[returns < 0]
        
        upside_stats = {
            'upside_count': len(positive),
            'upside_pct': len(positive) / len(returns) * 100,
            'upside_mean': positive.mean() if len(positive) > 0 else 0,
            'upside_std': positive.std() if len(positive) > 1 else 0,
            'upside_std_annualized': positive.std() * np.sqrt(periods) if len(positive) > 1 else 0,
        }
        
        downside_stats = {
            'downside_count': len(negative),
            'downside_pct': len(negative) / len(returns) * 100,
            'downside_mean': negative.mean() if len(negative) > 0 else 0,
            'downside_std': np.abs(negative).std() if len(negative) > 1 else 0,
            'downside_std_annualized': np.abs(negative).std() * np.sqrt(periods) if len(negative) > 1 else 0,
        }
        
        # Volatility asymmetry
        if upside_stats['upside_std'] > 0:
            vol_asymmetry = downside_stats['downside_std'] / upside_stats['upside_std']
        else:
            vol_asymmetry = np.inf
        
        analysis_results[tf] = {
            'basic_stats': stats_dict,
            'upside': upside_stats,
            'downside': downside_stats,
            'volatility_asymmetry': vol_asymmetry,
            'normality_tests': {k: v.__dict__ for k, v in normality.items()},
            'tail_analysis': tail_analysis,
            'var': var_results,
        }
        
        # Print summary
        print(f"\n  {tf}:")
        print(f"    Mean (ann): {stats_dict['annualized_mean']*100:+.2f}%")
        print(f"    Std (ann):  {stats_dict['annualized_std']*100:.2f}%")
        print(f"    Upside Std:   {upside_stats['upside_std_annualized']*100:.2f}%")
        print(f"    Downside Std: {downside_stats['downside_std_annualized']*100:.2f}%")
        print(f"    Vol Asym:   {vol_asymmetry:.2f}x")
    
    # 4. Generate Visualizations
    print("\n[4/5] Generating visualizations...")
    viz = DORVisualizer(output_dir=output_path / "charts")
    
    # Distribution plots for each timeframe
    for tf, returns in returns_by_tf.items():
        viz.plot_return_distribution(returns, title=f"{asset.name}", timeframe=tf)
    
    # Timeframe comparison
    viz.plot_timeframe_comparison(returns_by_tf)
    
    # Open-to-Close distribution
    viz.plot_o2c_distribution(o2c_returns, h2l_range, asset_name=asset.name)
    
    # Volatility comparison (daily data)
    vol_calc = VolatilityCalculator(price_data)
    volatilities = vol_calc.compute_all_volatilities(window=21)
    viz.plot_volatility_comparison(volatilities, title=f"{asset.name} - Volatility Estimators")
    
    print(f"  Charts saved to: {output_path / 'charts'}")
    
    # 5. Generate Reports
    print("\n[5/5] Generating reports...")
    report_gen = ReportGenerator(output_dir=output_path / "reports")
    
    # Excel report
    excel_path = report_gen.generate_excel_report(
        asset_name=asset.name,
        returns_by_timeframe=returns_by_tf,
        price_data=price_data
    )
    
    # Text report
    text_path = report_gen.generate_text_report(
        asset_name=asset.name,
        returns_by_timeframe=returns_by_tf
    )
    
    # Print final summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nOutput directory: {output_path.absolute()}")
    print(f"Excel report: {excel_path}")
    print(f"Text report: {text_path}")
    
    return {
        'asset': asset_key,
        'price_data': price_data,
        'returns': returns_by_tf,
        'analysis': analysis_results,
        'output_dir': output_path,
    }


def print_available_assets():
    """Print list of available assets."""
    print("\nAvailable Assets:")
    print("-" * 40)
    for key, asset in ASSETS.items():
        print(f"  {key:6s} - {asset.name}")


def print_available_timeframes():
    """Print list of available timeframes."""
    print("\nAvailable Timeframes:")
    print("-" * 40)
    for key, tf in TIMEFRAMES.items():
        print(f"  {key:4s} - {tf.name} ({tf.periods_per_year} periods/year)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='DOR Framework - Distribution of Returns Analysis')
    parser.add_argument('--asset', '-a', type=str, default='NQ',
                        help='Asset to analyze (default: NQ)')
    parser.add_argument('--years', '-y', type=int, default=10,
                        help='Years of historical data (default: 10)')
    parser.add_argument('--output', '-o', type=str, default='./output',
                        help='Output directory (default: ./output)')
    parser.add_argument('--list-assets', action='store_true',
                        help='List available assets')
    parser.add_argument('--list-timeframes', action='store_true',
                        help='List available timeframes')
    
    args = parser.parse_args()
    
    if args.list_assets:
        print_available_assets()
    elif args.list_timeframes:
        print_available_timeframes()
    else:
        results = run_full_analysis(
            asset_key=args.asset,
            years_back=args.years,
            output_dir=args.output
        )
