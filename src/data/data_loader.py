"""
Data Loader Module
Handles downloading and caching of financial data from Yahoo Finance.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Union
import logging
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.assets import get_asset, AssetConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Handles downloading and managing financial data from Yahoo Finance.
    
    Best Practices Applied:
    - Uses adjusted close prices to account for splits and dividends
    - Handles missing data appropriately
    - Provides caching mechanism for efficiency
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize DataLoader.
        
        Args:
            cache_dir: Optional directory for caching downloaded data
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def download(
        self,
        asset_key: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        years_back: int = 10
    ) -> pd.DataFrame:
        """
        Download historical data for an asset.
        
        Args:
            asset_key: Key of the asset in ASSETS config (e.g., 'NQ')
            start_date: Start date for data (default: years_back from today)
            end_date: End date for data (default: today)
            years_back: Number of years of history if start_date not specified
            
        Returns:
            DataFrame with OHLCV data and adjusted close
        """
        asset = get_asset(asset_key)
        
        # Set default dates
        if end_date is None:
            end_date = datetime.now()
        elif isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
            
        if start_date is None:
            start_date = end_date - timedelta(days=years_back * 365)
        elif isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        
        logger.info(f"Downloading {asset.name} ({asset.yahoo_symbol}) from {start_date.date()} to {end_date.date()}")
        
        # Download from Yahoo Finance
        ticker = yf.Ticker(asset.yahoo_symbol)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
        
        if df.empty:
            raise ValueError(f"No data retrieved for {asset_key}. Check symbol: {asset.yahoo_symbol}")
        
        # Clean and standardize columns
        df = self._clean_data(df)
        
        # Add metadata
        df.attrs['asset_key'] = asset_key
        df.attrs['asset_name'] = asset.name
        df.attrs['yahoo_symbol'] = asset.yahoo_symbol
        df.attrs['download_date'] = datetime.now().isoformat()
        
        logger.info(f"Downloaded {len(df)} records for {asset.name}")
        
        return df
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the downloaded data.
        
        Args:
            df: Raw DataFrame from yfinance
            
        Returns:
            Cleaned DataFrame
        """
        # Ensure index is datetime
        df.index = pd.to_datetime(df.index)
        df.index.name = 'Date'
        
        # Remove timezone info for consistency
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Standardize column names
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Keep only relevant columns
        cols_to_keep = ['open', 'high', 'low', 'close', 'volume']
        df = df[[col for col in cols_to_keep if col in df.columns]]
        
        # Handle missing values
        # Forward fill for price data (last known price)
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in df.columns:
                df[col] = df[col].ffill()
        
        # Drop rows where close is still NaN
        df = df.dropna(subset=['close'])
        
        # Sort by date
        df = df.sort_index()
        
        return df
    
    def save_to_cache(self, df: pd.DataFrame, asset_key: str) -> Path:
        """Save data to cache directory."""
        if self.cache_dir is None:
            raise ValueError("Cache directory not configured")
        
        filepath = self.cache_dir / f"{asset_key}_data.parquet"
        df.to_parquet(filepath)
        logger.info(f"Saved {asset_key} data to {filepath}")
        return filepath
    
    def load_from_cache(self, asset_key: str) -> Optional[pd.DataFrame]:
        """Load data from cache if available."""
        if self.cache_dir is None:
            return None
        
        filepath = self.cache_dir / f"{asset_key}_data.parquet"
        if filepath.exists():
            logger.info(f"Loading {asset_key} from cache: {filepath}")
            return pd.read_parquet(filepath)
        return None


def download_asset_data(
    asset_key: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    years_back: int = 10
) -> pd.DataFrame:
    """
    Convenience function to download asset data.
    
    Args:
        asset_key: Asset identifier (e.g., 'NQ', 'ES', 'SPY')
        start_date: Optional start date string (YYYY-MM-DD)
        end_date: Optional end date string (YYYY-MM-DD)
        years_back: Years of history if start_date not provided
        
    Returns:
        DataFrame with historical OHLCV data
    """
    loader = DataLoader()
    return loader.download(asset_key, start_date, end_date, years_back)
