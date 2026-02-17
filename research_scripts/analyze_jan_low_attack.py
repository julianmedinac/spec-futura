import pandas as pd
from src.data.data_loader import DataLoader
from src.seasonality.conditional_analyzer import ConditionalAnalyzer
from config.assets import get_asset

def analyze_jan_low_sweep_in_feb(asset_key: str):
    loader = DataLoader()
    data = loader.download(asset_key, years_back=100)
    
    data['year'] = data.index.year
    data['month'] = data.index.month
    
    results = []
    years = data['year'].unique()
    
    for year in years:
        y_data = data[data['year'] == year].copy()
        jan = y_data[y_data['month'] == 1]
        feb = y_data[y_data['month'] == 2]
        
        if jan.empty or feb.empty or len(feb) < 10: continue
        
        jan_low = jan['low'].min()
        jan_high = jan['high'].max()
        
        feb['tdom'] = range(1, len(feb) + 1)
        
        # Condition 1: Feb makes a Lower Low than Jan early (TDOM 1-10)
        feb_first_half = feb[feb['tdom'] <= 10]
        feb_early_low = feb_first_half['low'].min()
        feb_early_low_tdom = feb_first_half[feb_first_half['low'] == feb_early_low]['tdom'].iloc[0]
        
        if feb_early_low < jan_low:
            # We have the "Attack" on Jan Low
            
            # Condition 2: Where was the Feb High at that point?
            feb_early_high = feb_first_half['high'].max()
            feb_early_high_tdom = feb_first_half[feb_first_half['high'] == feb_early_high]['tdom'].iloc[0]
            
            # Outcome: How did the year end?
            yearly_low_date = y_data['close'].idxmin()
            yearly_high_date = y_data['close'].idxmax()
            
            # Did the Feb Low hold as the Yearly Low?
            is_feb_yearly_low = (yearly_low_date.month == 2)
            # Did it eventually break Jan High?
            ever_broke_jan_high = (y_data['high'] > jan_high).any()
            
            # Month close status
            feb_close = feb.iloc[-1]['close']
            feb_open = feb.iloc[0]['open']
            
            results.append({
                'year': year,
                'feb_low_tdom': feb_early_low_tdom,
                'feb_high_tdom': feb_early_high_tdom,
                'is_feb_yearly_low': is_feb_yearly_low,
                'ever_broke_jan_high': ever_broke_jan_high,
                'feb_return': (feb_close/feb_open - 1) * 100,
                'yearly_high_q': yearly_high_date.quarter
            })
            
    df = pd.DataFrame(results)
    
    print(f"\n{'='*70}")
    print(f"HISTORICAL REGIME: FEB ATTACKS JAN LOW EARLY (TDOM 1-10)")
    print(f"Asset: {asset_key} | Sample Size: {len(df)} years")
    print(f"{'='*70}")
    
    if df.empty:
        print("No matches found.")
        return

    # Filter for years similar to 2026 (High was early too, TDOM 1-5)
    similar_years = df[df['feb_high_tdom'] <= 5]
    
    print(f"\nSubset: Feb High also occurred early (TDOM 1-5) - Like 2026")
    print(f"Sample Size: {len(similar_years)} years")
    
    if not similar_years.empty:
        low_lock_prob = (similar_years['is_feb_yearly_low'].sum() / len(similar_years)) * 100
        recovery_prob = (similar_years['ever_broke_jan_high'].sum() / len(similar_years)) * 100
        
        print(f"- Prob(Feb Low holds as YEARLY Low): {low_lock_prob:.1f}%")
        print(f"- Prob(Market eventually recovers and breaks Jan High): {recovery_prob:.1f}%")
        print(f"- Avg Feb Return: {similar_years['feb_return'].mean():+.2f}%")
        
        print("\nHistorical Matches:")
        print(similar_years[['year', 'feb_low_tdom', 'feb_high_tdom', 'is_feb_yearly_low', 'ever_broke_jan_high', 'feb_return']].to_string(index=False))

if __name__ == "__main__":
    analyze_jan_low_sweep_in_feb('GC')
