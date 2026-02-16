import pandas as pd
from src.data.data_loader import DataLoader

def analyze_jan_high_significance(asset_key):
    loader = DataLoader()
    print(f"Downloading {asset_key} data...")
    # Get Max History
    if asset_key == 'NQ':
        start = '1985-01-01'
    else:
        start = '1928-01-01'
        
    data = loader.download(asset_key, start_date=start)
    
    if data.empty:
        return

    data['year'] = data.index.year
    data['month'] = data.index.month
    data['quarter'] = data.index.quarter
    
    unique_years = data['year'].unique()
    
    years_with_jan_q1_high = []
    years_where_jan_is_yearly_high = []
    
    for year in unique_years:
        if year == 2026: continue # Skip current
        
        # Q1 Data
        q1_data = data[(data['year'] == year) & (data['quarter'] == 1)]
        if q1_data.empty: continue
        
        # Yearly Data
        year_data = data[data['year'] == year]
        
        # Check if Q1 High occurred in Jan
        q1_high_val = q1_data['high'].max()
        q1_high_date = q1_data['high'].idxmax()
        
        if q1_high_date.month == 1:
            years_with_jan_q1_high.append(year)
            
            # Check if this was the Yearly High
            yearly_high_val = year_data['high'].max()
            if q1_high_val == yearly_high_val:
                years_where_jan_is_yearly_high.append(year)

    count_q1_jan = len(years_with_jan_q1_high)
    count_yearly = len(years_where_jan_is_yearly_high)
    
    if count_q1_jan == 0:
        print(f"No years found with Q1 High in Jan for {asset_key}")
        return
        
    prob = (count_yearly / count_q1_jan) * 100
    
    print(f"\n--- {asset_key} ANALYSIS: JAN HIGH ---")
    print(f"Years where Q1 High was in January: {count_q1_jan}")
    print(f"Years where that Jan High held as YEARLY High: {count_yearly}")
    print(f"Probability: {prob:.1f}%")
    print(f"Years: {years_where_jan_is_yearly_high}")

if __name__ == "__main__":
    analyze_jan_high_significance('NQ')
    analyze_jan_high_significance('GSPC')
    analyze_jan_high_significance('DJI')
