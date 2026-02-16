import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class SeasonalityCalculator:
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with a DataFrame containing at least 'close' column (and date index).
        Data should be daily.
        """
        self.data = data.copy()
        if 'close' not in self.data.columns:
            raise ValueError("Data must constrain 'close' column")
        
        # Calculate Daily Log Returns first for aggregation (more accurate for summing)
        # or Simple Returns. For consistency with the rest of the repo (DOR uses simple), 
        # we will use simple returns but handle accumulation correctly.
        # Actually, for seasonality plots showing "growth of $100", we need chainable returns.
        
        # Simple Return (Close to Close)
        self.data['pct_change'] = self.data['close'].pct_change()
        # We do NOT dropna here, because we want to keep the first row for Monthly resampling (as a base)
        # self.data.dropna(inplace=True)  <-- REMOVED
        
        self.data['month'] = self.data.index.month
        self.data['year'] = self.data.index.year
        self.data['day'] = self.data.index.day

    def calculate_monthly_stats(self) -> pd.DataFrame:
        """
        Calculates average return and hit rate (positivity rate) for each month (1-12).
        Returns a DataFrame with index 1-12 and columns ['mean_return', 'hit_rate'].
        """
        # Resample to monthly returns first to get the actual return of the month
        monthly_data = self.data['close'].resample('M').last().pct_change()
        monthly_data.dropna(inplace=True)
        
        # Group by month number
        groups = monthly_data.groupby(monthly_data.index.month)
        
        results = pd.DataFrame()
        results['mean_return'] = groups.mean()
        results['hit_rate'] = groups.apply(lambda x: (x > 0).sum() / len(x))
        results['count'] = groups.count()
        results['std_dev'] = groups.std()
        
        # T-Statistic Calculation
        results['se'] = results['std_dev'] / np.sqrt(results['count'])
        results['t_stat'] = results['mean_return'] / results['se']
        
        from scipy import stats
        results['p_value'] = 2 * (1 - stats.t.cdf(np.abs(results['t_stat']), df=results['count']-1))
        
        return results

    def calculate_quarterly_stats(self) -> pd.DataFrame:
        """
        Calculates average return and hit rate for each quarter (Q1-Q4).
        """
        # Resample to quarterly returns (Q = Quarter End)
        quarterly_data = self.data['close'].resample('Q').last().pct_change()
        quarterly_data.dropna(inplace=True)
        
        # Group by quarter
        groups = quarterly_data.groupby(quarterly_data.index.quarter)
        
        results = pd.DataFrame()
        results['mean_return'] = groups.mean()
        results['hit_rate'] = groups.apply(lambda x: (x > 0).sum() / len(x))
        results['count'] = groups.count()
        results['std_dev'] = groups.std()
        
        # T-Statistic
        results['se'] = results['std_dev'] / np.sqrt(results['count'])
        results['t_stat'] = results['mean_return'] / results['se']
        
        from scipy import stats
        results['p_value'] = 2 * (1 - stats.t.cdf(np.abs(results['t_stat']), df=results['count']-1))
        
        return results

    def calculate_daily_seasonality(self, target_month: int) -> pd.DataFrame:
        """
        Calculates the average cumulative performance for a specific month,
        aggregated by Trading Day (1st trading day, 2nd, ...).
        """
        # Filter target month
        month_data = self.data[self.data['month'] == target_month].copy()
        
        # Assign Trading Day Rank for each year
        month_data['trading_day'] = month_data.groupby('year')['day'].rank(method='first').astype(int)
        
        # Calculate mean daily return
        mean_daily_returns = month_data.pivot(index='trading_day', columns='year', values='pct_change').mean(axis=1)
        
        # Construct cumulative curve
        current_level = 100.0
        levels = []
        for r in mean_daily_returns:
            current_level *= (1 + r)
            levels.append(current_level)
            
        df_result = pd.DataFrame({'level': levels}, index=range(1, len(levels)+1))
        df_result.index.name = 'trading_day'
        return df_result

    def calculate_quarterly_daily_seasonality(self, target_quarter: int) -> pd.DataFrame:
        """
        Calculates the average cumulative performance for a specific quarter (Q1-Q4),
        aggregated by Trading Day within the quarter (1 to ~64).
        """
        # Filter target quarter
        q_data = self.data[self.data.index.quarter == target_quarter].copy()
        
        # Assign Trading Day Rank within the quarter for each year
        # We rank absolute dates within each (year, quarter) group
        q_data['trading_day'] = q_data.groupby(['year'])['close'].cumcount() + 1
        
        # Calculate mean daily return
        pivoted = q_data.pivot(index='trading_day', columns='year', values='pct_change')
        mean_daily_returns = pivoted.mean(axis=1)
        
        # Construct cumulative curve
        current_level = 100.0
        levels = []
        for r in mean_daily_returns:
            current_level *= (1 + r)
            levels.append(current_level)
            
        df_result = pd.DataFrame({'level': levels}, index=range(1, len(levels)+1))
        df_result.index.name = 'trading_day'
        return df_result
