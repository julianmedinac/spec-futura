import pandas as pd
import numpy as np
from scipy import stats
from src.data.data_loader import DataLoader
from datetime import datetime

def analyze_gold_q1_significance():
    loader = DataLoader()
    print("Downloading Gold Futures (GC) Data...")
    # Get Max History
    # Note: Yahoo Finance (GC=F) history often starts around 2000 
    data = loader.download('GC', start_date='2000-01-01')
    
    if data.empty:
        print("No data found for GC")
        return

    # Filter for Q1 data ONLY
    q1_data = data[data.index.quarter == 1]
    
    # Calculate Q1 Returns for each year
    # We need to resample by Year-Quarter to get the return of the specific Q1
    # Resample to Quarterly
    quarterly_returns = data['close'].resample('QE').last().pct_change()
    
    # Filter for Q1 (Month 3 end)
    q1_returns = quarterly_returns[quarterly_returns.index.month == 3]
    
    # Drop first NaN if any
    q1_returns = q1_returns.dropna()
    
    # --- STATISTICS ---
    n = len(q1_returns)
    mean_return = q1_returns.mean()
    std_dev = q1_returns.std()
    hit_rate = (q1_returns > 0).sum() / n
    
    # T-Statistic (One-sample t-test against 0)
    t_stat, p_value = stats.ttest_1samp(q1_returns, 0)
    
    # Check Significance (90% and 95%)
    sig_95 = p_value < 0.05 and t_stat > 0
    sig_90 = p_value < 0.10 and t_stat > 0
    
    print("\n" + "="*60)
    print(f"GOLD (GC) Q1 SEASONALITY STATISTICAL AUDIT")
    print(f"Data Range: {q1_returns.index.year.min()} - {q1_returns.index.year.max()}")
    print("="*60)
    
    print(f"\nMetric               Value")
    print(f"----------------     -----")
    print(f"Sample Size (N)      {n}")
    print(f"Mean Return          {mean_return*100:.2f}%")
    print(f"Hit Rate (Win %)     {hit_rate*100:.1f}%")
    print(f"Std Deviation        {std_dev*100:.2f}%")
    print(f"Sharpe Ratio (Q1)    {mean_return/std_dev:.2f}")
    
    print(f"\n--- STATISTICAL SIGNIFICANCE ---")
    print(f"T-Statistic          {t_stat:.4f}")
    print(f"P-Value              {p_value:.4f}")
    
    if sig_95:
        print("\n>>> VERDICT: STATISTICALLY SIGNIFICANT (95% Confidence)")
        print("    Historically, Gold Q1 returns are clearly distinguishable from zero/noise.")
    elif sig_90:
        print("\n>>> VERDICT: WEAKLY SIGNIFICANT (90% Confidence)")
        print("    There is a bullish edge, but it's not ironclad.")
    else:
        print("\n>>> VERDICT: NOT STATISTICALLY SIGNIFICANT")
        print("    The positive mean could be due to random chance or a few outlier years.")
        
    # Best/Worst Years
    print("\nTop 5 Q1 Years:")
    print(q1_returns.nlargest(5).apply(lambda x: f"{x*100:.1f}%"))
    
    print("\nWorst 5 Q1 Years:")
    print(q1_returns.nsmallest(5).apply(lambda x: f"{x*100:.1f}%"))

if __name__ == "__main__":
    analyze_gold_q1_significance()
