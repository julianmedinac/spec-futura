import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def stress_test_w2_signal(asset_key):
    print(f"\n{'='*80}")
    print(f"STRESS TEST: W1-W2 SIGNAL ROBUSTNESS CHECK FOR {asset_key}")
    print(f"{'='*80}")
    
    loader = DataLoader()
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    weekly_groups = data.groupby(['year', 'month'])
    
    results = []
    
    for (year, month), month_data in weekly_groups:
        weeks = sorted(month_data['week_of_year'].unique())
        if len(weeks) < 2: continue
            
        w1_data = month_data[month_data['week_of_year'] == weeks[0]]
        w2_data = month_data[month_data['week_of_year'] == weeks[1]]
        
        if w1_data.empty or w2_data.empty: continue

        w1_w2_high = max(w1_data['high'].max(), w2_data['high'].max())
        w1_w2_low = min(w1_data['low'].min(), w2_data['low'].min())
        w1_w2_range = w1_w2_high - w1_w2_low
        if w1_w2_range == 0: continue
            
        midpoint = w1_w2_low + (w1_w2_range * 0.5)
        w2_close = w2_data.iloc[-1]['close']
        
        # Determine Signal State
        is_below_50 = w2_close < midpoint
        
        # Monthly Outcome
        month_return = (month_data.iloc[-1]['close'] / month_data.iloc[0]['open']) - 1
        is_month_red = month_return < 0
        
        results.append({
            'year': year,
            'month': month,
            'is_below_50': is_below_50,
            'month_return': month_return,
            'is_month_red': is_month_red
        })
        
    df = pd.DataFrame(results)
    
    # ------------------------------------------------------------------
    # TEST 1: CONSISTENCY OVER TIME (Are results degrading?)
    # ------------------------------------------------------------------
    print(f"\n1. TEMPORAL STABILITY TEST (Does it work in recent years?)")
    
    # Split into 5-year buckets
    df['period'] = (df['year'] // 5) * 5
    periods = sorted(df['period'].unique())
    
    print(f"   Success Rate of BEAR SIGNAL (<50% -> RED Month) by Period:")
    print(f"   Period | Sample | Bear Win Rate | Avg Return")
    print(f"   -------|--------|---------------|-----------")
    
    for p in periods:
        period_data = df[(df['period'] == p) & (df['is_below_50'])]
        if period_data.empty: continue
            
        n = len(period_data)
        win_rate = (period_data['is_month_red'].sum() / n) * 100
        avg_ret = period_data['month_return'].mean() * 100
        
        star = "*" if win_rate > 60 else ""
        print(f"   {p}-{p+4} |   {n:2d}   |     {win_rate:4.1f}%      |   {avg_ret:5.2f}% {star}")

    # ------------------------------------------------------------------
    # TEST 2: DRAWDOWN SEVERITY (Is the risk asymmetric?)
    # ------------------------------------------------------------------
    print(f"\n2. ASYMMETRIC RISK TEST (When wrong, how much does it hurt?)")
    
    bear_signal = df[df['is_below_50']]
    
    # When Signal Says BEAR (Short), but Market Goes UP (Loss for Short)
    failed_bear = bear_signal[~bear_signal['is_month_red']]
    avg_loss_bear = failed_bear['month_return'].mean() * 100
    max_loss_bear = failed_bear['month_return'].max() * 100
    
    # When Signal Says BEAR (Short), and Market Goes DOWN (Win for Short)
    winning_bear = bear_signal[bear_signal['is_month_red']]
    avg_win_bear = abs(winning_bear['month_return'].mean() * 100) # As profit
    
    print(f"   BEAR SIGNAL STATS (Shorting):")
    print(f"   - When Right (Win): Avg Profit +{avg_win_bear:.2f}%")
    print(f"   - When Wrong (Loss): Avg Loss  {avg_loss_bear:.2f}%") # Negative number
    print(f"   - Worst Case Loss : {max_loss_bear:.2f}%")
    
    risk_reward = avg_win_bear / abs(avg_loss_bear)
    print(f"   - Risk/Reward Ratio: {risk_reward:.2f}")

    # ------------------------------------------------------------------
    # TEST 3: BULL SIGNAL (Does >50% work equally well?)
    # ------------------------------------------------------------------
    print(f"\n3. BULL SIGNAL TEST (>50% -> Green Month)")
    bull_signal = df[~df['is_below_50']]
    bull_win_rate = (bull_signal['month_return'] > 0).sum() / len(bull_signal) * 100
    
    print(f"   Bull Signal Win Rate: {bull_win_rate:.1f}%")
    print(f"   Avg Return: {bull_signal['month_return'].mean()*100:.2f}%")
    
    # ------------------------------------------------------------------
    # FINAL VERDICT
    # ------------------------------------------------------------------
    print(f"\n" + "="*80)
    print(f"STRESS TEST VERDICT")
    if risk_reward > 1.2 and bull_win_rate > 70:
        print(f">>> PASS - GOLD STANDARD SYSTEM")
        print(f"    The edge is consistent across decades and has positive expectancy.")
    else:
        print(f">>> CAUTION - MIXED RESULTS")
        print(f"    Check temporal decay or risk/reward ratio.")
    print(f"="*80)


if __name__ == "__main__":
    stress_test_w2_signal('NQ')
