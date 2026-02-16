import pandas as pd
from src.data.data_loader import DataLoader
from src.seasonality.conditional_analyzer import ConditionalAnalyzer
from config.assets import get_asset

def run_reversal_analysis(asset_key: str):
    asset_config = get_asset(asset_key)
    loader = DataLoader()
    data = loader.download(asset_key, years_back=100)
    
    analyzer = ConditionalAnalyzer(data)
    result = analyzer.analyze_q2_reversal_pattern()
    
    print(f"\n{'='*50}")
    print(f"ANALYSIS: Q2 OUTSIDE REVERSAL (NQ/ES/GSPC)")
    print(f"ASSET: {asset_key}")
    print(f"{'='*50}")
    
    if result:
        print(f"Condition: Q2 made a LOWER LOW than Q1 BUT also a HIGHER HIGH than Q1.")
        print(f"Sample Size: Found in {result['sample_size']} years.")
        print(f"Years: {result['years']}")
        print(f"\nOUTCOMES:")
        print(f"- Prob(Q2 became the Yearly LOW): {result['prob_q2_is_low']:.1f}%")
        print(f"- Prob(Yearly HIGH stayed in Q4): {result['prob_q4_is_high']:.1f}%")
        
        if result['prob_q2_is_low'] > 70:
            print(f"\n>>> EDGE: This is a massive 'Stop-Run & Reverse' pattern. If Q2 clears Q1 High after making a LL, those Q2 lows are extremely unlikely to be broken.")
    else:
        print("This pattern is rare. No years found in history.")

if __name__ == "__main__":
    for asset in ['GSPC', 'NQ', 'ES']:
        run_reversal_analysis(asset)
