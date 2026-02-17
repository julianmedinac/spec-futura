import pandas as pd
from src.data.data_loader import DataLoader
from config.assets import get_asset

def analyze_feb_compression_regime(asset_key: str):
    loader = DataLoader()
    data = loader.download(asset_key, years_back=100)
    
    data['year'] = data.index.year
    data['month'] = data.index.month
    
    results = []
    
    years = data['year'].unique()
    for year in years:
        feb_data = data[(data['year'] == year) & (data['month'] == 2)].copy()
        if len(feb_data) < 15: continue
        
        feb_data['tdom'] = range(1, len(feb_data) + 1)
        
        # Monthly Extremes
        abs_high = feb_data['high'].max()
        abs_low = feb_data['low'].min()
        abs_high_tdom = feb_data[feb_data['high'] == abs_high]['tdom'].iloc[0]
        abs_low_tdom = feb_data[feb_data['low'] == abs_low]['tdom'].iloc[0]
        
        # Extremes within first 7 TDOM (where we are now)
        first_week = feb_data[feb_data['tdom'] <= 7]
        fw_high = first_week['high'].max()
        fw_low = first_week['low'].min()
        
        # Condition: At TDOM 7, we have a range. 
        # But we want to know what happened in history when 
        # the monthly high and monthly low were BOTH set in the first 7 days.
        
        both_in_fw = (abs_high_tdom <= 7) and (abs_low_tdom <= 7)
        
        if both_in_fw:
            # How did the month end?
            feb_open = feb_data.iloc[0]['open']
            feb_close = feb_data.iloc[-1]['close']
            is_bullish = feb_close > feb_open
            ret = (feb_close / feb_open - 1) * 100
            
            results.append({
                'year': year,
                'high_tdom': abs_high_tdom,
                'low_tdom': abs_low_tdom,
                'is_bullish': is_bullish,
                'return': ret
            })
            
    df_res = pd.DataFrame(results)
    
    print(f"\n{'='*60}")
    print(f"HISTORICAL OUTCOME: WHEN BOTH HIGH & LOW OCCUR IN TDOM 1-7 (FEB)")
    print(f"Asset: {asset_key}")
    print(f"{'='*60}")
    
    if df_res.empty:
        print("This scenario (both extremes in first 7 days) is extremely rare!")
        return

    bulls = df_res[df_res['is_bullish']]
    bears = df_res[~df_res['is_bullish']]
    
    print(f"Sample Size: {len(df_res)} years found.")
    print(f"Bullish Monthly Closes: {len(bulls)} ({len(bulls)/len(df_res)*100:.1f}%)")
    print(f"Bearish Monthly Closes: {len(bears)} ({len(bears)/len(df_res)*100:.1f}%)")
    
    print("\nSpecific Years with this 'First Week Trap':")
    print(df_res[['year', 'high_tdom', 'low_tdom', 'return']].to_string(index=False))

if __name__ == "__main__":
    analyze_feb_compression_regime('GSPC')
