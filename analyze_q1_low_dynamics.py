import pandas as pd
from src.data.data_loader import DataLoader
from src.seasonality.extremes_analyzer import ExtremesAnalyzer
from config.assets import get_asset

def analyze_q1_low_dynamics(asset_key: str):
    loader = DataLoader()
    data = loader.download(asset_key, years_back=100) # Full history
    
    analyzer = ExtremesAnalyzer(data)
    extremes_df = analyzer.analyze_extremes()
    
    # FILTER: Years where Yearly Low was in Q1
    q1_low_years = extremes_df[extremes_df['low_quarter'] == 1].copy()
    total_q1_lows = len(q1_low_years)
    
    if total_q1_lows == 0:
        print(f"No Q1 Lows found for {asset_key}")
        return

    # 1. Month of the Low (within Q1)
    low_month_dist = q1_low_years['low_month'].value_counts(normalize=True).sort_index() * 100
    
    # 2. Quarter of the High (in those years)
    high_quarter_dist = q1_low_years['high_quarter'].value_counts(normalize=True).sort_index() * 100
    
    # 3. Month of the High (in those years)
    high_month_dist = q1_low_years['high_month'].value_counts(normalize=True).sort_index() * 100

    print(f"\n{'='*60}")
    print(f"DYNAMICS WHEN THE YEARLY LOW IS IN Q1 - ASSET: {asset_key}")
    print(f"Total Years Analyzed: {len(extremes_df)} | Years with Q1 Low: {total_q1_lows}")
    print(f"{'='*60}")
    
    print("\nMONTH OF THE LOW (Distribution within Q1):")
    for month, prob in low_month_dist.items():
        m_name = {1: "January", 2: "February", 3: "March"}[month]
        print(f"  - {m_name}: {prob:.1f}%")
        
    print("\nQUARTER OF THE HIGH (Where does the year end?):")
    for q, prob in high_quarter_dist.items():
        print(f"  - Quarter {int(q)}: {prob:.1f}%")
        
    print("\nTOP 3 MONTHS FOR THE YEARLY HIGH:")
    top_high_months = high_month_dist.sort_values(ascending=False).head(3)
    month_names = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 
                   7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
    for month, prob in top_high_months.items():
        print(f"  - {month_names[month]}: {prob:.1f}%")

if __name__ == "__main__":
    analyze_q1_low_dynamics('GC')
