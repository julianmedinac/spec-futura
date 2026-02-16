"""
Volatility Calculator Module
Implements various volatility estimation methods.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.timeframes import get_timeframe


class VolatilityCalculator:
    """
    Calculate and analyze volatility using multiple methods.
    
    Best Practices Applied:
    ----------------------
    1. Standard Deviation (Historical Volatility):
       - Simple and interpretable
       - Use sample std (ddof=1) for unbiased estimation
    
    2. Annualization:
       - σ_annual = σ_period × √(periods_per_year)
       - Assumes returns are i.i.d. (independent and identically distributed)
    
    3. Rolling Volatility:
       - Captures time-varying nature of volatility
       - Standard window: 21 days (1 month) or 63 days (1 quarter)
    
    4. EWMA (Exponentially Weighted Moving Average):
       - More weight to recent observations
       - RiskMetrics standard: λ = 0.94 for daily data
    
    5. Parkinson/Garman-Klass:
       - Uses high-low range for more efficient estimation
       - Better captures intraday volatility
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with OHLC data.
        
        Args:
            data: DataFrame with 'open', 'high', 'low', 'close' columns
        """
        self.data = data.copy()
        self._validate_data()
    
    def _validate_data(self):
        """Validate required columns exist."""
        required = ['close']
        for col in required:
            if col not in self.data.columns:
                raise ValueError(f"Required column '{col}' not found")
    
    def historical_volatility(
        self,
        window: Optional[int] = None,
        annualize: bool = True,
        periods_per_year: float = 252
    ) -> pd.Series:
        """
        Calculate historical (realized) volatility.
        
        Args:
            window: Rolling window size (None for full sample)
            annualize: Whether to annualize the volatility
            periods_per_year: Trading periods per year
            
        Returns:
            Series of volatility values
        """
        # Calculate log returns
        log_returns = np.log(self.data['close'] / self.data['close'].shift(1))
        
        if window is None:
            # Full sample volatility
            vol = log_returns.std(ddof=1)
            if annualize:
                vol = vol * np.sqrt(periods_per_year)
            return pd.Series([vol] * len(log_returns), index=log_returns.index, name='historical_vol')
        else:
            # Rolling volatility
            vol = log_returns.rolling(window=window).std(ddof=1)
            if annualize:
                vol = vol * np.sqrt(periods_per_year)
            vol.name = f'historical_vol_{window}d'
            return vol
    
    def ewma_volatility(
        self,
        span: Optional[int] = None,
        lambda_: float = 0.94,
        annualize: bool = True,
        periods_per_year: float = 252
    ) -> pd.Series:
        """
        Calculate EWMA (Exponentially Weighted) volatility.
        
        The RiskMetrics approach uses λ = 0.94 for daily data.
        
        Args:
            span: EWM span parameter (alternative to lambda_)
            lambda_: Decay factor (0.94 is RiskMetrics standard)
            annualize: Whether to annualize
            periods_per_year: Trading periods per year
            
        Returns:
            Series of EWMA volatility values
        """
        log_returns = np.log(self.data['close'] / self.data['close'].shift(1))
        
        if span is not None:
            ewma_var = log_returns.pow(2).ewm(span=span).mean()
        else:
            # Convert lambda to span: span = 2/(1-λ) - 1
            ewma_var = log_returns.pow(2).ewm(alpha=1-lambda_, adjust=False).mean()
        
        vol = np.sqrt(ewma_var)
        
        if annualize:
            vol = vol * np.sqrt(periods_per_year)
        
        vol.name = 'ewma_vol'
        return vol
    
    def parkinson_volatility(
        self,
        window: int = 21,
        annualize: bool = True,
        periods_per_year: float = 252
    ) -> pd.Series:
        """
        Calculate Parkinson volatility estimator.
        
        Uses high-low range, which is ~5x more efficient than close-to-close.
        
        Formula: σ² = (1/4ln(2)) × (ln(H/L))²
        
        Args:
            window: Rolling window size
            annualize: Whether to annualize
            periods_per_year: Trading periods per year
            
        Returns:
            Series of Parkinson volatility values
        """
        if 'high' not in self.data.columns or 'low' not in self.data.columns:
            raise ValueError("Parkinson volatility requires 'high' and 'low' columns")
        
        log_hl = np.log(self.data['high'] / self.data['low'])
        
        # Parkinson estimator
        parkinson_factor = 1 / (4 * np.log(2))
        variance = parkinson_factor * (log_hl ** 2)
        
        vol = np.sqrt(variance.rolling(window=window).mean())
        
        if annualize:
            vol = vol * np.sqrt(periods_per_year)
        
        vol.name = f'parkinson_vol_{window}d'
        return vol
    
    def garman_klass_volatility(
        self,
        window: int = 21,
        annualize: bool = True,
        periods_per_year: float = 252
    ) -> pd.Series:
        """
        Calculate Garman-Klass volatility estimator.
        
        More efficient than Parkinson, uses OHLC data.
        
        Args:
            window: Rolling window size
            annualize: Whether to annualize
            periods_per_year: Trading periods per year
            
        Returns:
            Series of Garman-Klass volatility values
        """
        required = ['open', 'high', 'low', 'close']
        for col in required:
            if col not in self.data.columns:
                raise ValueError(f"Garman-Klass requires '{col}' column")
        
        log_hl = np.log(self.data['high'] / self.data['low'])
        log_co = np.log(self.data['close'] / self.data['open'])
        
        # Garman-Klass estimator
        variance = 0.5 * (log_hl ** 2) - (2 * np.log(2) - 1) * (log_co ** 2)
        
        vol = np.sqrt(variance.rolling(window=window).mean())
        
        if annualize:
            vol = vol * np.sqrt(periods_per_year)
        
        vol.name = f'garman_klass_vol_{window}d'
        return vol
    
    def yang_zhang_volatility(
        self,
        window: int = 21,
        annualize: bool = True,
        periods_per_year: float = 252
    ) -> pd.Series:
        """
        Calculate Yang-Zhang volatility estimator.
        
        Combines overnight and intraday volatility.
        Most efficient estimator that handles opening jumps.
        
        Args:
            window: Rolling window size
            annualize: Whether to annualize
            periods_per_year: Trading periods per year
            
        Returns:
            Series of Yang-Zhang volatility values
        """
        required = ['open', 'high', 'low', 'close']
        for col in required:
            if col not in self.data.columns:
                raise ValueError(f"Yang-Zhang requires '{col}' column")
        
        # Overnight return
        log_oc = np.log(self.data['open'] / self.data['close'].shift(1))
        
        # Open to close return
        log_co = np.log(self.data['close'] / self.data['open'])
        
        # Rogers-Satchell component
        log_ho = np.log(self.data['high'] / self.data['open'])
        log_hc = np.log(self.data['high'] / self.data['close'])
        log_lo = np.log(self.data['low'] / self.data['open'])
        log_lc = np.log(self.data['low'] / self.data['close'])
        
        rs = log_ho * log_hc + log_lo * log_lc
        
        # Yang-Zhang estimator
        k = 0.34 / (1.34 + (window + 1) / (window - 1))
        
        overnight_var = log_oc.rolling(window=window).var()
        openclose_var = log_co.rolling(window=window).var()
        rs_var = rs.rolling(window=window).mean()
        
        variance = overnight_var + k * openclose_var + (1 - k) * rs_var
        vol = np.sqrt(variance)
        
        if annualize:
            vol = vol * np.sqrt(periods_per_year)
        
        vol.name = f'yang_zhang_vol_{window}d'
        return vol
    
    def compute_all_volatilities(
        self,
        window: int = 21,
        annualize: bool = True,
        periods_per_year: float = 252
    ) -> pd.DataFrame:
        """
        Compute all volatility estimators.
        
        Args:
            window: Rolling window size
            annualize: Whether to annualize
            periods_per_year: Trading periods per year
            
        Returns:
            DataFrame with all volatility measures
        """
        result = pd.DataFrame(index=self.data.index)
        
        # Historical
        result['historical'] = self.historical_volatility(window, annualize, periods_per_year)
        
        # EWMA
        result['ewma'] = self.ewma_volatility(annualize=annualize, periods_per_year=periods_per_year)
        
        # Range-based estimators (if data available)
        try:
            result['parkinson'] = self.parkinson_volatility(window, annualize, periods_per_year)
        except ValueError:
            pass
        
        try:
            result['garman_klass'] = self.garman_klass_volatility(window, annualize, periods_per_year)
        except ValueError:
            pass
        
        try:
            result['yang_zhang'] = self.yang_zhang_volatility(window, annualize, periods_per_year)
        except ValueError:
            pass
        
        return result
    
    def get_current_volatility_summary(
        self,
        windows: list = [21, 63, 126, 252],
        periods_per_year: float = 252
    ) -> Dict[str, float]:
        """
        Get summary of current volatility levels.
        
        Args:
            windows: List of lookback windows
            periods_per_year: Trading periods per year
            
        Returns:
            Dictionary with volatility metrics
        """
        log_returns = np.log(self.data['close'] / self.data['close'].shift(1)).dropna()
        
        result = {}
        
        # Full sample
        result['full_sample'] = log_returns.std() * np.sqrt(periods_per_year)
        
        # Rolling windows
        for w in windows:
            if len(log_returns) >= w:
                result[f'{w}d'] = log_returns.tail(w).std() * np.sqrt(periods_per_year)
        
        # Current EWMA
        ewma = self.ewma_volatility(annualize=True, periods_per_year=periods_per_year)
        result['ewma_current'] = ewma.iloc[-1]
        
        return result


def calculate_volatility(
    data: pd.DataFrame,
    method: str = 'historical',
    window: int = 21,
    annualize: bool = True,
    periods_per_year: float = 252
) -> pd.Series:
    """
    Convenience function to calculate volatility.
    
    Args:
        data: DataFrame with OHLC data
        method: 'historical', 'ewma', 'parkinson', 'garman_klass', 'yang_zhang'
        window: Rolling window size
        annualize: Whether to annualize
        periods_per_year: Trading periods per year
        
    Returns:
        Series of volatility values
    """
    calc = VolatilityCalculator(data)
    
    methods = {
        'historical': lambda: calc.historical_volatility(window, annualize, periods_per_year),
        'ewma': lambda: calc.ewma_volatility(annualize=annualize, periods_per_year=periods_per_year),
        'parkinson': lambda: calc.parkinson_volatility(window, annualize, periods_per_year),
        'garman_klass': lambda: calc.garman_klass_volatility(window, annualize, periods_per_year),
        'yang_zhang': lambda: calc.yang_zhang_volatility(window, annualize, periods_per_year),
    }
    
    if method not in methods:
        raise ValueError(f"Unknown method: {method}. Available: {list(methods.keys())}")
    
    return methods[method]()
