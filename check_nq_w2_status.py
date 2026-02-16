import pandas as pd
from src.data.data_loader import DataLoader
from datetime import datetime, timedelta

def analyze_current_w2_status(asset_key):
    loader = DataLoader()
    print(f"\nAnalyzing Current Status for {asset_key} (Feb 2026)...")
    
    # Download Februrary 2026 data
    try:
        data = loader.download(asset_key, start_date='2026-02-01')
    except Exception as e:
        print(f"Error downloading data: {e}")
        return

    if data.empty:
        print("No data available for Feb 2026 yet.")
        return

    # Add week number
    data['week_of_year'] = data.index.isocalendar().week
    
    # Identify Week 1 and Week 2 of Feb
    # Week 1 starts Feb 1 (Sunday/Monday) -> Feb 7
    # Week 2 starts Feb 8 -> Feb 14
    
    # Get unique weeks present in data
    weeks = sorted(data['week_of_year'].unique())
    
    if len(weeks) == 0:
        print("No weekly data.")
        return
        
    w1_week_num = weeks[0]
    
    # Check if we have entered Week 2
    if len(weeks) >= 2:
        w2_week_num = weeks[1]
        print(f"Tracking Week 1 (Week {w1_week_num}) and Week 2 (Week {w2_week_num})")
    else:
        print(f"Currently in Week 1 (Week {w1_week_num}). Need to enter Week 2 to complete range.")
        w2_week_num = None
        
    # Get Data
    w1_data = data[data['week_of_year'] == w1_week_num]
    
    if w2_week_num:
        w2_data = data[data['week_of_year'] == w2_week_num]
        combined_data = pd.concat([w1_data, w2_data])
        status = "IN WEEK 2"
    else:
        combined_data = w1_data
        status = "IN WEEK 1 (PROJECTED)"
        
    # Calculate Range
    w1_w2_high = combined_data['high'].max()
    w1_w2_low = combined_data['low'].min()
    w1_w2_range = w1_w2_high - w1_w2_low
    
    # 50% Level
    midpoint_level = w1_w2_low + (w1_w2_range * 0.5)
    
    # Current Price
    current_price = data.iloc[-1]['close']
    last_date = data.index[-1].strftime('%Y-%m-%d')
    
    # Distance
    dist_to_mid = current_price - midpoint_level
    dist_pct = (dist_to_mid / w1_w2_range) * 100 if w1_w2_range > 0 else 0
    
    print(f"\n--- {asset_key} W1-W2 STRUCTURE ({status}) ---")
    print(f"Date: {last_date}")
    print(f"Combined High: {w1_w2_high:.2f}")
    print(f"Combined Low : {w1_w2_low:.2f}")
    print(f"Range Size   : {w1_w2_range:.2f}")
    print(f"-"*30)
    print(f"THE 50% LINE : {midpoint_level:.2f}")
    print(f"CURRENT PRICE: {current_price:.2f}")
    print(f"-"*30)
    
    if current_price < midpoint_level:
        print(f">>> BEARISH SIGNAL ACTIVATED <<<")
        print(f"Price is BELOW the 50% level by {abs(dist_to_mid):.2f} points.")
        print(f"Historical Probability of Red Month: 67.2%")
    else:
        print(f">>> BULLISH SIGNAL ACTIVE <<<")
        print(f"Price is ABOVE the 50% level by {dist_to_mid:.2f} points.")
        print(f"Historical Probability of Green Month: 80.6%")
        
    # Weekly Close Projection
    today = datetime.now()
    # Assuming Friday Feb 13 is the close of W2
    days_left = (4 - today.weekday()) if today.weekday() <= 4 else 0
    if days_left > 0:
        print(f"\nNOTE: Week 2 closes in {days_left} trading days (Friday).")
        print(f"The signal confirms ONLY at W2 Close.")

if __name__ == "__main__":
    analyze_current_w2_status('NQ')
