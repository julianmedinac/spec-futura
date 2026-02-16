"""
Script to research seasonality patterns (Monthly & Daily).
Usage: py research_seasonality.py [--asset SYMBOL] [--month MONTH_NUM]
"""
import sys
import argparse
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from src.data.data_loader import download_asset_data
from src.seasonality.seasonality_calculator import SeasonalityCalculator
from src.seasonality.seasonality_visualizer import SeasonalityVisualizer
from src.seasonality.extremes_analyzer import ExtremesAnalyzer
from src.seasonality.conditional_analyzer import ConditionalAnalyzer
from config.assets import get_asset

def run_analysis(asset_key: str, target_month: int):
    print(f"\n{'='*60}")
    print(f"  SEASONALITY ANALYSIS: {asset_key}")
    print(f"{'='*60}")
    
    # 1. Download Data (Max history)
    # Using a very early start date to get full history available in Yahoo
    start_date = '1900-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Downloading data for {asset_key} (Max History)...")
    try:
        df = download_asset_data(asset_key, start_date, end_date)
    except Exception as e:
        print(f"Error downloading {asset_key}: {e}")
        return

    if df.empty:
        print(f"No data found for {asset_key}")
        return

    years_range = f"{df.index.year.min()}-{df.index.year.max()}"
    print(f"Data range: {years_range} ({len(df)} trading days)")

    # 2. Calculate
    calculator = SeasonalityCalculator(df)
    extremes_engine = ExtremesAnalyzer(df)
    
    # Monthly & Quarterly Stats
    monthly_stats = calculator.calculate_monthly_stats()
    quarterly_stats = calculator.calculate_quarterly_stats()
    extremes_df = extremes_engine.analyze_extremes()
    
    # 3. Visualize & Calculate Daily Stats for ALL months
    visualizer = SeasonalityVisualizer()
    
    print("Generating charts...")
    # Monthly Seasonality Bar Chart
    try:
        visualizer.plot_monthly_seasonality(monthly_stats, asset_key, years_range)
    except Exception as e:
        print(f"Error generating monthly chart: {e}")

    # Quarterly Seasonality Bar Chart
    try:
        visualizer.plot_quarterly_seasonality(quarterly_stats, asset_key, years_range)
    except Exception as e:
        print(f"Error generating quarterly chart: {e}")

    # Yearly Extremes Analysis
    try:
        visualizer.plot_yearly_extremes(extremes_df, asset_key, years_range)
        visualizer.plot_monthly_extremes(extremes_df, asset_key, years_range)
        visualizer.plot_quarterly_extremes(extremes_df, asset_key, years_range)
    except Exception as e:
        print(f"Error generating extremes charts: {e}")

    # Intra-Quarterly Daily Performance (Phase 3)
    print("Generating intra-quarterly daily performance charts...")
    for q in range(1, 5):
        try:
            q_daily_stats = calculator.calculate_quarterly_daily_seasonality(q)
            if not q_daily_stats.empty:
                visualizer.plot_quarterly_daily_performance(q_daily_stats, asset_key, q, years_range)
        except Exception as e:
            print(f"Error generating daily path for Q{q}: {e}")

    # Daily Seasonality Line Charts (All Months)
    print("Generating daily seasonality charts for all months (Standardized Scale)...")
    all_daily_stats = {}
    
    # First pass: Calculate and find global y_min/y_max
    global_min = 100.0
    global_max = 100.0
    
    for m in range(1, 13):
        try:
            daily_stats = calculator.calculate_daily_seasonality(m)
            if not daily_stats.empty:
                all_daily_stats[m] = daily_stats
                global_min = min(global_min, daily_stats['level'].min())
                global_max = max(global_max, daily_stats['level'].max())
        except Exception as e:
            print(f"Error calculating stats for month {m}: {e}")

    # Add 0.5% buffer to y_lim
    y_buffer = (global_max - global_min) * 0.1
    y_lim = (global_min - y_buffer, global_max + y_buffer)
    x_lim = (1, 23) # Standard trading month max

    # Second pass: Plot with standardized limits
    for m, daily_stats in all_daily_stats.items():
        try:
            visualizer.plot_daily_seasonality(daily_stats, asset_key, m, years_range, y_lim=y_lim, x_lim=x_lim)
        except Exception as e:
            print(f"Error plotting month {m}: {e}")

    # 4. Print Summary
    print("\n--- Monthly Summary & Statistical Significance ---")
    
    # Format for readability
    summary = monthly_stats[['mean_return', 'hit_rate', 'count', 't_stat', 'p_value']].copy()
    
    # Add 'Significant?' column based on p < 0.05 (95% confidence)
    summary['significant_95'] = summary['p_value'] < 0.05
    summary['significant_90'] = summary['p_value'] < 0.10
    
    pd.options.display.float_format = '{:.4f}'.format
    print(summary)
    
    print("\n--- Quarterly Summary ---")
    q_summary = quarterly_stats[['mean_return', 'hit_rate', 'count', 't_stat', 'p_value']].copy()
    q_summary['significant_95'] = q_summary['p_value'] < 0.05
    print(q_summary)

    # Yearly Extremes Summary
    print("\n--- Yearly Extremes Summary ---")
    low_stats = extremes_df['low_day'].describe()
    high_stats = extremes_df['high_day'].describe()
    
    print(f"AVG YEARLY LOW: Day {low_stats['mean']:.0f} (Std: {low_stats['std']:.0f})")
    print(f"AVG YEARLY HIGH: Day {high_stats['mean']:.0f} (Std: {high_stats['std']:.0f})")
    
    # Simple T-Significance check for clustering (if STD is low relative to 252 days)
    # A random distribution would have STD ~ 72 (252 / sqrt(12))
    low_significance = "CLUSTERED" if low_stats['std'] < 60 else "DISPERSED"
    high_significance = "CLUSTERED" if high_stats['std'] < 60 else "DISPERSED"
    
    print(f"Low Clustering: {low_significance}")
    print(f"High Clustering: {high_significance}")

    # Conditional Probability (Phase 4)
    print("\n--- Conditional Probability Analysis ---")
    cond_engine = ConditionalAnalyzer(df)
    results, _ = cond_engine.analyze_q2_breakout()
    
    if isinstance(results, dict):
        print(f"Condition: IF (Price in Q2 > Q1 High)")
        print(f"Outcome  : THEN (Yearly Low was in Q1)")
        print(f"----------------------------------------")
        print(f"Conditional Probability: {results['prob_conditional']:.1f}%")
        print(f"Unconditional Baseline : {results['prob_benchmark']:.1f}%")
        print(f"STATISTICAL LIFT       : {results['lift']:+.1f}%")
        print(f"Sample Size (Years)    : {results['sample_size']} of {results['total_sample']}")
        
        try:
            visualizer.plot_conditional_edge(results, asset_key, years_range)
        except Exception as e:
            print(f"Error generating conditional chart: {e}")

        if results['lift'] > 5:
            print(f">>> REGIME CONFIRMED: Breaking the Q1 high early in Q2 is a powerful indicator that the low is in.")
        else:
            print(f">>> NO SIGNIFICANT EDGE: The break of Q1 high doesn't significantly change the low probability.")

        # Monthly Confidence Progression
        print("\n--- Monthly Confidence Progression ---")
        prog_df = cond_engine.analyze_monthly_progression()
        try:
            visualizer.plot_monthly_confidence_progression(prog_df, asset_key, years_range)
            print("Monthly confidence curve generated.")
        except Exception as e:
            print(f"Error generating confidence curve: {e}")

    print("\nInterpretation:")
    print("- p_value < 0.05: Strong Evidence (95% Confidence) that the return is not zero.")
    print("- p_value < 0.10: Weak Evidence (90% Confidence).")
    print("- t_stat > 2.0 (approx): Positive return is significant.")
    print("- t_stat < -2.0 (approx): Negative return is significant.")

def main():
    parser = argparse.ArgumentParser(description="Seasonality Research")
    parser.add_argument('--asset', type=str, help='Asset key (e.g., NQ, GSPC). If not specified, runs default set.')
    parser.add_argument('--month', type=int, default=2, help='Target month for daily analysis (1-12). Default: 2 (Feb)')
    
    args = parser.parse_args()
    
    if args.asset:
        assets_to_run = [args.asset]
    else:
        # Default as requested: GSPC, NQ
        assets_to_run = ['GSPC', 'NQ']
        
    for asset in assets_to_run:
        run_analysis(asset, args.month)

if __name__ == "__main__":
    main()
