"""
Returns Calculator Module
Implements various return calculation methods following financial best practices.
"""

import pandas as pd
import numpy as np
from typing import Optional, Literal
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.timeframes import get_timeframe, TIMEFRAMES


class ReturnsCalculator:
    """
    Calculate financial returns with various methods.
    
    Methods Available:
    -----------------
    1. Simple Returns (Default):
       - Intuitive and easy to interpret
       - Asset additive (portfolio returns)
       - Formula: R_t = (P_t - P_{t-1}) / P_{t-1}
    
    2. Log Returns (Alternative):
       - Time additive: R_total = R_1 + R_2 + ... + R_n
       - Formula: r_t = ln(P_t / P_{t-1})
    
    3. Open-to-Close Returns:
       - Intraday movement without overnight gaps
       - Formula: R_t = (Close_t - Open_t) / Open_t
    
    4. Excess Returns:
       - Returns above risk-free rate
    """
    
    def __init__(self, prices: pd.DataFrame, price_column: str = 'close'):
        """
        Initialize with price data.
        
        Args:
            prices: DataFrame with price data
            price_column: Column name for price data (default: 'close')
        """
        if price_column not in prices.columns:
            raise ValueError(f"Column '{price_column}' not found in DataFrame")
        
        self.prices = prices.copy()
        self.price_column = price_column
        self._validate_data()
    
    def _validate_data(self):
        """Validate input data."""
        if self.prices[self.price_column].isna().any():
            raise ValueError("Price data contains NaN values. Please clean data first.")
        if (self.prices[self.price_column] <= 0).any():
            raise ValueError("Price data contains non-positive values.")
    
    def simple_returns(self) -> pd.Series:
        """
        Calculate simple (arithmetic) returns.
        
        Formula: R_t = (P_t - P_{t-1}) / P_{t-1}
        
        Returns:
            Series of simple returns
        """
        returns = self.prices[self.price_column].pct_change()
        returns.name = 'simple_return'
        return returns.dropna()
    
    def log_returns(self) -> pd.Series:
        """
        Calculate logarithmic (continuously compounded) returns.
        
        Formula: r_t = ln(P_t / P_{t-1})
        
        This is the RECOMMENDED method for:
        - Time series analysis
        - Volatility estimation
        - Distribution analysis
        
        Returns:
            Series of log returns
        """
        prices = self.prices[self.price_column]
        returns = np.log(prices / prices.shift(1))
        returns.name = 'log_return'
        return returns.dropna()
    
    def open_to_close_returns(self) -> pd.Series:
        """
        Calculate Open-to-Close (intraday) simple returns.
        
        Formula: R_t = (Close_t - Open_t) / Open_t
        
        This captures intraday movement without overnight gaps.
        Consistent with the methodology in NQ DOR PRO.
        
        Returns:
            Series of O2C returns
        """
        if 'open' not in self.prices.columns:
            raise ValueError("DataFrame must contain 'open' column for O2C returns")
        
        returns = (self.prices['close'] - self.prices['open']) / self.prices['open']
        returns.name = 'o2c_return'
        return returns.dropna()
    
    def high_to_low_range(self) -> pd.Series:
        """
        Calculate High-to-Low range as percentage.
        
        Formula: R_t = (High_t - Low_t) / Low_t
        
        Returns:
            Series of H2L ranges
        """
        if 'high' not in self.prices.columns or 'low' not in self.prices.columns:
            raise ValueError("DataFrame must contain 'high' and 'low' columns")
        
        returns = (self.prices['high'] - self.prices['low']) / self.prices['low']
        returns.name = 'h2l_range'
        return returns.dropna()
    
    def excess_returns(
        self,
        risk_free_rate: float = 0.0,
        annualized: bool = True,
        periods_per_year: int = 252
    ) -> pd.Series:
        """
        Calculate excess returns (returns above risk-free rate).
        
        Args:
            risk_free_rate: Annual risk-free rate (e.g., 0.05 for 5%)
            annualized: Whether the risk_free_rate is annualized
            periods_per_year: Number of periods per year for de-annualization
            
        Returns:
            Series of excess returns
        """
        log_ret = self.log_returns()
        
        # Convert annual risk-free rate to per-period rate
        if annualized:
            rf_per_period = risk_free_rate / periods_per_year
        else:
            rf_per_period = risk_free_rate
        
        excess = log_ret - rf_per_period
        excess.name = 'excess_return'
        return excess
    
    def resample_returns(
        self,
        timeframe: str,
        return_type: Literal['simple', 'log'] = 'simple'
    ) -> pd.Series:
        """
        Calculate returns for a specific timeframe by resampling.
        
        For log returns: Sum of daily log returns = log return over period
        For simple returns: Compound daily returns = (1+R1)(1+R2)...(1+Rn) - 1
        
        Args:
            timeframe: Timeframe code ('1D', '1W', '1M', '1Q', '6M', '1Y')
            return_type: 'log' or 'simple'
            
        Returns:
            Series of resampled returns
        """
        tf_config = get_timeframe(timeframe)
        
        if timeframe == '1D':
            # Daily returns - no resampling needed
            if return_type == 'log':
                return self.log_returns()
            else:
                return self.simple_returns()
        
        if return_type == 'log':
            # For log returns: resample prices and compute log return
            # This is mathematically equivalent to summing daily log returns
            resampled_prices = self.prices[self.price_column].resample(tf_config.pandas_freq).last()
            resampled_prices = resampled_prices.dropna()
            returns = np.log(resampled_prices / resampled_prices.shift(1))
        else:
            # For simple returns: compound daily returns
            resampled_prices = self.prices[self.price_column].resample(tf_config.pandas_freq).last()
            resampled_prices = resampled_prices.dropna()
            returns = resampled_prices.pct_change()
        
        returns.name = f'{return_type}_return_{timeframe}'
        return returns.dropna()
    
    def get_all_timeframe_returns(
        self,
        return_type: Literal['simple', 'log'] = 'simple'
    ) -> dict:
        """
        Calculate returns for all configured timeframes.
        
        Args:
            return_type: 'log' or 'simple'
            
        Returns:
            Dictionary with timeframe keys and return Series values
        """
        results = {}
        for tf_key in TIMEFRAMES.keys():
            try:
                results[tf_key] = self.resample_returns(tf_key, return_type)
            except Exception as e:
                print(f"Warning: Could not compute {tf_key} returns: {e}")
        return results


def calculate_returns(
    prices: pd.DataFrame,
    timeframe: str = '1D',
    return_type: Literal['simple', 'log'] = 'simple',
    price_column: str = 'close'
) -> pd.Series:
    """
    Convenience function to calculate returns.
    
    Args:
        prices: DataFrame with price data
        timeframe: Timeframe code ('1D', '1W', '1M', '1Q', '6M', '1Y')
        return_type: 'simple' or 'log'
        price_column: Column name for prices
        
    Returns:
        Series of returns
    """
    calculator = ReturnsCalculator(prices, price_column)
    return calculator.resample_returns(timeframe, return_type)
