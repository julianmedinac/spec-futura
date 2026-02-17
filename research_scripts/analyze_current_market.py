import pandas as pd
from src.data.data_loader import DataLoader
from config.assets import get_asset

def analyze_current_february(asset_key: str):
    loader = DataLoader()
    # Download data for the start of the year
    data = loader.download(asset_key, start_date='2026-01-01')
    
    if data.empty:
        print(f"No data for {asset_key} in 2026")
        return

    # Jan 2026 stats
    jan_data = data[data.index.month == 1]
    q1_high_to_date = data['close'].max()
    jan_high = jan_data['close'].max() if not jan_data.empty else 0
    
    # Feb 2026 stats
    feb_data = data[data.index.month == 2]
    if feb_data.empty:
        print(f"No February data for {asset_key}")
        return
        
    feb_open = feb_data.iloc[0]['open']
    feb_current = feb_data.iloc[-1]['close']
    is_bullish_to_date = feb_current > feb_open
    
    feb_low = feb_data['low'].min()
    feb_low_date = feb_data['low'].idxmin()
    # Calculate TDOM for Feb Low
    feb_dates = feb_data.index.unique()
    tdom_low = list(feb_dates).index(feb_low_date) + 1
    
    current_tdom = len(feb_dates)
    
    # Check Breakout
    has_broken_jan_high = (feb_data['close'] > jan_high).any() if jan_high > 0 else False

    print(f"\n--- CURRENT MARKET STATE: {asset_key} (Feb 11, 2026) ---")
    print(f"February Status: {'BULLISH' if is_bullish_to_date else 'BEARISH'} ({((feb_current/feb_open)-1)*100:+.2f}%)")
    print(f"Jan High: {jan_high:.2f}")
    print(f"Feb Low: {feb_low:.2f} (Occurrence: TDOM {tdom_low})")
    print(f"Current Price: {feb_current:.2f} (TDOM {current_tdom})")
    print(f"Has broken Jan High? {'YES' if has_broken_jan_high else 'NO'}")
    
    # Predictions
    print("\nPROBABILISTIC FORECAST:")
    if is_bullish_to_date and tdom_low <= 5:
        print("- FEB LOW LOCK: Since we are bullish and the low was TDOM 1-5, there is a ~65% probability the monthly low is already in.")
    
    if has_broken_jan_high:
        print("- YEARLY LOW LOCK: Since we broke Jan High in early Feb, probability of Yearly Low being in Q1 (Jan) is elevated (approx 77% based on our GSPC study).")
    else:
        print("- PENDING BREAKOUT: We haven't cleared Jan High yet. This is the 'line in the sand' to confirm the Yearly Low lock.")

    if is_bullish_to_date:
        print("- Q4 HIGH TARGET: If this bullish trend holds through Feb/Mar, there is an 80-92% historical probability of seeing the Yearly High in Q4 (December).")

if __name__ == "__main__":
    analyze_current_february('GC')
