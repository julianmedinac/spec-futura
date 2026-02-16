import pandas as pd
from src.data.data_loader import DataLoader
from datetime import datetime

def analyze_nq_q1_high_tdoq_18():
    loader = DataLoader()
    print("Downloading NQ data...")
    # Get Max History
    data = loader.download('NQ', start_date='1985-01-01')
    
    if data.empty:
        print("No data found for NQ")
        return

    # Add columns
    data['year'] = data.index.year
    data['quarter'] = data.index.quarter
    data['month'] = data.index.month
    
    # Calculate TDOQ for each day
    # Rank days within each (Year, Quarter) group
    data['tdoq'] = data.groupby(['year', 'quarter'])['close'].transform(lambda x: range(1, len(x) + 1))
    
    years_matching = []
    
    # Iterate through years
    unique_years = data['year'].unique()
    
    print(f"\nScanning {len(unique_years)} years for NQ Q1 High at TDOQ ~18 (Range 16-20)...")
    
    for year in unique_years:
        # Get Q1 data
        q1_data = data[(data['year'] == year) & (data['quarter'] == 1)]
        
        if q1_data.empty:
            continue
            
        # Find Q1 High Date and Value
        q1_high_val = q1_data['high'].max()
        q1_high_date = q1_data['high'].idxmax()
        
        # Find TDOQ of that high
        # We need to find the row where High == q1_high_val to get its TDOQ
        # Note: idxmax gives index, we can lookup tdoq
        try:
            high_day_row = q1_data.loc[q1_high_date]
            high_tdoq = high_day_row['tdoq']
        except:
            continue
            
        # Check condition: TDOQ around 18 (Tolerance +/- 2 days: 16-20)
        # TDOQ 18 is typically late January (approx Jan 26-30)
        if 16 <= high_tdoq <= 20:
            
            # Analyze what happened THE REST OF THE YEAR
            full_year_data = data[data['year'] == year]
            
            # Yearly High/Low
            yearly_high = full_year_data['high'].max()
            yearly_low = full_year_data['low'].min()
            
            # Did Q1 High hold as Yearly High?
            is_yearly_high = (q1_high_val == yearly_high)
            
            # Did we break that Q1 High later?
            # Creating a mask for days AFTER Q1
            post_q1_data = full_year_data[full_year_data['quarter'] > 1]
            if not post_q1_data.empty:
                broke_high_later = post_q1_data['high'].max() > q1_high_val
            else:
                broke_high_later = False
                
            # Yearly Return
            year_open = full_year_data.iloc[0]['open']
            year_close = full_year_data.iloc[-1]['close']
            year_return = (year_close / year_open) - 1
            
            # Drawdown from Q1 High
            # Min low after the Q1 High date
            post_high_data = full_year_data[full_year_data.index > q1_high_date]
            if not post_high_data.empty:
                min_after_high = post_high_data['low'].min()
                drawdown = (min_after_high - q1_high_val) / q1_high_val
            else:
                drawdown = 0.0

            years_matching.append({
                'year': year,
                'high_tdoq': high_tdoq,
                'high_date': q1_high_date.strftime('%Y-%m-%d'),
                'is_yearly_high': is_yearly_high,
                'broke_high_later': broke_high_later,
                'year_return': year_return,
                'drawdown_from_high': drawdown
            })

    # Results
    if not years_matching:
        print("No matching years found.")
        return

    df_res = pd.DataFrame(years_matching)
    
    print("\n" + "="*60)
    print(f"RESULTS: NQ Q1 High occurring at TDOQ 16-20 (Late Jan)")
    print(f"Sample Size: {len(df_res)} years")
    print("="*60)
    
    print("\nMatching Years:")
    print(df_res[['year', 'high_tdoq', 'high_date', 'year_return', 'drawdown_from_high']].to_string(index=False))
    
    # Statistics
    print("\n--- STATISTICS ---")
    prob_break = df_res['broke_high_later'].mean() * 100
    avg_return = df_res['year_return'].mean() * 100
    avg_dd = df_res['drawdown_from_high'].mean() * 100
    
    print(f"Probability of Breaking Q1 High Later in Year: {prob_break:.1f}%")
    print(f"Average Yearly Return: {avg_return:.2f}%")
    print(f"Average Drawdown from Q1 High: {avg_dd:.2f}%")
    
    # Bearish Cases
    bearish_years = df_res[df_res['year_return'] < 0]
    print(f"\nBearish Years count: {len(bearish_years)} ({len(bearish_years)/len(df_res):.0%})")
    
    # 2026 Comparison
    print("\n--- 2026 CONTEXT ---")
    print("In 2026, NQ Q1 High was on Jan 27 (TDOQ 18 approx).")
    print("This matches the pattern perfectly.")
    
    if prob_break < 50:
        print("WARNING: This pattern has a bearish bias. Usually, a late Jan high (TDOQ 18) that isn't broken early suggests weakness.")
    else:
        print("This pattern is generally bullish/neutral, but watch the drawdown stats.")

if __name__ == "__main__":
    analyze_nq_q1_high_tdoq_18()
