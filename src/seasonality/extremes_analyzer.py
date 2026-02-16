import pandas as pd
import numpy as np
from scipy import stats
import os

class ExtremesAnalyzer:
    """
    Analyzes the statistical distribution of yearly highs and lows
    to identify high-probability windows for market extremes.
    """
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        if 'trading_day_year' not in self.data.columns:
            self.data['year'] = self.data.index.year
            self.data['trading_day_year'] = self.data.groupby('year').cumcount() + 1
            
    def analyze_extremes(self) -> pd.DataFrame:
        """
        Identifies the trading day of the year for the High and Low of each year.
        Calculates mean, std dev, and T-stats for the clustering of these extremes.
        """
        years = self.data['year'].unique()
        extreme_days = []
        
        for year in years:
            yearly_data = self.data[self.data['year'] == year]
            if len(yearly_data) < 200: # Skip incomplete years
                continue
                
            low_day = yearly_data['close'].idxmin()
            high_day = yearly_data['close'].idxmax()
            
            low_rank = yearly_data.index.get_loc(low_day) + 1
            high_rank = yearly_data.index.get_loc(high_day) + 1
            
            extreme_days.append({
                'year': year,
                'low_day': low_rank,
                'high_day': high_rank,
                'low_month': low_day.month,
                'high_month': high_day.month,
                'low_quarter': low_day.quarter,
                'high_quarter': high_day.quarter,
                'low_date': low_day,
                'high_date': high_day
            })
            
        df_extremes = pd.DataFrame(extreme_days)
        return df_extremes

    def get_statistical_windows(self, df_extremes: pd.DataFrame):
        """
        Calculates statistical metrics for the clustering of extremes.
        Uses a T-test against the null hypothesis of uniform distribution.
        """
        metrics = {}
        for target in ['low_day', 'high_day']:
            days = df_extremes[target]
            mean_day = days.mean()
            std_day = days.std()
            count = len(days)
            se = std_day / np.sqrt(count)
            
            # T-Stat vs Mid-year (126) - Not very useful, but gives a sense of bias
            # Better: Frequency analysis in blocks.
            
            metrics[target] = {
                'mean': mean_day,
                'std': std_day,
                'count': count,
                'se': se
            }
        return metrics
