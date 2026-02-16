import pandas as pd
from src.data.data_loader import DataLoader
import numpy as np

def analyze_weekly_structure(asset_key):
    print(f"\n{'='*70}")
    print(f"ANALYZING WEEKLY STRUCTURE (W1-W2) FOR {asset_key}")
    print(f"{'='*70}")
    
    loader = DataLoader()
    # Download daily data and resample to weekly for accuracy
    # Using 'ME' for month end and 'W-FRI' for weekly is standard
    # But to get "Week 1 of Month", "Week 2 of Month", we need daily data grouping
    
    # Let's execute the USER'S SPECIFIC LOGIC:
    # 1. Group days into Months.
    # 2. Inside each month, group days into Weeks (Calendar Weeks).
    # 3. Calculate Range of Week 1 + Week 2 combined.
    # 4. Check where Week 2 Closed relative to that Range.
    
    data = loader.download(asset_key, start_date='2000-01-01')
    if data.empty: return

    # Add helper columns
    data['year'] = data.index.year
    data['month'] = data.index.month
    data['week_of_year'] = data.index.isocalendar().week
    
    # We need to identify "Week Number within Month" (1, 2, 3, 4...)
    # A simple way: Rank the unique week_of_year values within each (year, month) group
    
    # Create a mapping of Date -> (Year, Month, Week_Num_In_Month)
    weekly_groups = data.groupby(['year', 'month'])
    
    results = []
    
    for (year, month), month_data in weekly_groups:
        # Get unique weeks in this month
        weeks = month_data['week_of_year'].unique()
        weeks = sorted(weeks) # Ensure 1, 2, 3...
        
        if len(weeks) < 2:
            continue # Not enough data for W1+W2 analysis
            
        # Get W1 Data
        w1_data = month_data[month_data['week_of_year'] == weeks[0]]
        w2_data = month_data[month_data['week_of_year'] == weeks[1]]
        
        if w1_data.empty or w2_data.empty:
            continue

        # Calculate W1+W2 Combined Range
        combined_high = max(w1_data['high'].max(), w2_data['high'].max())
        combined_low = min(w1_data['low'].min(), w2_data['low'].min())
        combined_range = combined_high - combined_low
        
        # Avoid division by zero
        if combined_range == 0: continue
            
        # Get W2 Close (The "Signal")
        w2_close = w2_data.iloc[-1]['close']
        
        # Condition: Are we below 50% of the range?
        # Range Position (0 = Low, 1 = High)
        range_position = (w2_close - combined_low) / combined_range
        
        is_below_50 = range_position < 0.50
        
        # Outcome: Did the Month Close Positive (Green) or Negative (Red)?
        month_open = month_data.iloc[0]['open']
        month_close = month_data.iloc[-1]['close']
        is_month_green = month_close > month_open
        is_month_red = month_close < month_open
        
        month_return = (month_close / month_open) - 1
        
        results.append({
            'year': year,
            'month': month,
            'range_pos': range_position,
            'is_below_50': is_below_50,
            'is_month_green': is_month_green,
            'is_month_red': is_month_red,
            'month_return': month_return
        })
        
    df = pd.DataFrame(results)
    
    if df.empty:
        print("No valid monthly data found.")
        return

    # --- ANALYSIS ---
    total_months = len(df)
    below_50_cases = df[df['is_below_50']]
    
    print(f"\nTotal Months Analyzed: {total_months}")
    print(f"Months Closing W2 Below 50% of Range: {len(below_50_cases)} ({len(below_50_cases)/total_months:.1%})")
    
    if len(below_50_cases) > 0:
        red_months = below_50_cases['is_month_red'].sum()
        prob_red = (red_months / len(below_50_cases)) * 100
        avg_return = below_50_cases['month_return'].mean() * 100
        
        print("\n--- RESULTS FOR 'BELOW 50%' CONDITION ---")
        print(f"Probability of RED Month: {prob_red:.1f}%")
        print(f"Average Monthly Return: {avg_return:.2f}%")
        
        # Compare to Baseline (All Months)
        baseline_red = df['is_month_red'].sum() / total_months * 100
        lift = prob_red - baseline_red
        print(f"Baseline Probability (Any Month Red): {baseline_red:.1f}%")
        print(f"Statistical Edge (Lift): {lift:+.1f}%")
        
    # INVERSE: What if we close ABOVE 50%?
    above_50_cases = df[~df['is_below_50']]
    if len(above_50_cases) > 0:
        green_months = above_50_cases['is_month_green'].sum()
        prob_green = (green_months / len(above_50_cases)) * 100
        
        print("\n--- RESULTS FOR 'ABOVE 50%' CONDITION ---")
        print(f"Probability of GREEN Month: {prob_green:.1f}%")
        print(f"Average Monthly Return: {above_50_cases['month_return'].mean()*100:.2f}%")

if __name__ == "__main__":
    analyze_weekly_structure('NQ')
    analyze_weekly_structure('GSPC')
