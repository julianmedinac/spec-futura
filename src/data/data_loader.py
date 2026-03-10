"""
Data Loader Module
Handles downloading and caching of financial data from Yahoo Finance.
Supports both standard daily bars and CME futures session reconstruction
(18:00-17:00 ET), which matches TradingView's daily candles for NQ/ES/YM.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Union
import logging
from pathlib import Path
import pytz

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

    def download_cme_session(
        self,
        asset_key: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        years_back: int = 5
    ) -> pd.DataFrame:
        """
        Download daily data using CME futures session boundaries (18:00-17:00 ET),
        reconstructed from 1-hour bars. This matches TradingView's daily candles
        for NQ, ES, YM and other CME futures.

        Args:
            asset_key: Key of the asset in ASSETS config (e.g., 'NQ')
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            years_back: Years of history if start_date not specified

        Returns:
            DataFrame with OHLCV data resampled to CME session boundaries.
            Index is the trade date (the date when the session ends at 17:00 ET).
        """
        asset = get_asset(asset_key)
        et_tz = pytz.timezone('America/New_York')

        # Resolve dates
        if end_date is None:
            end_dt = datetime.now()
        elif isinstance(end_date, str):
            end_dt = pd.to_datetime(end_date)
        else:
            end_dt = end_date

        if start_date is None:
            start_dt = end_dt - timedelta(days=years_back * 365)
        elif isinstance(start_date, str):
            start_dt = pd.to_datetime(start_date)
        else:
            start_dt = start_date

        # Fetch one extra day before start to capture overnight session
        fetch_start = start_dt - timedelta(days=2)
        # Fetch one extra day after end in case last session spills over
        fetch_end = end_dt + timedelta(days=1)

        logger.info(
            f"[CME Session] Downloading hourly {asset.name} ({asset.yahoo_symbol}) "
            f"from {start_dt.date()} to {end_dt.date()}"
        )

        ticker = yf.Ticker(asset.yahoo_symbol)
        df_h = ticker.history(
            start=fetch_start,
            end=fetch_end,
            interval='1h',
            auto_adjust=True
        )

        if df_h.empty:
            raise ValueError(
                f"No hourly data for {asset_key} ({asset.yahoo_symbol}). "
                "Note: yfinance limits hourly data to ~730 days."
            )

        # Ensure timezone-aware index in ET
        if df_h.index.tz is None:
            df_h.index = df_h.index.tz_localize('UTC')
        df_h.index = df_h.index.tz_convert(et_tz)

        # Assign each hourly bar to a CME trade date.
        # CME session: 18:00 ET (prev day) -> 17:00 ET (trade date)
        # Rule: if hour >= 18 -> belongs to NEXT calendar day's session
        #        if hour < 18  -> belongs to CURRENT calendar day's session
        def assign_trade_date(ts):
            if ts.hour >= 18:
                return (ts + timedelta(days=1)).date()
            return ts.date()

        df_h['trade_date'] = df_h.index.map(assign_trade_date)

        # Resample to daily CME candles
        df_h.columns = [col.lower().replace(' ', '_') for col in df_h.columns]
        price_cols = {c: c for c in ['open', 'high', 'low', 'close', 'volume'] if c in df_h.columns}

        agg_map = {}
        if 'open'   in df_h.columns: agg_map['open']   = 'first'
        if 'high'   in df_h.columns: agg_map['high']   = 'max'
        if 'low'    in df_h.columns: agg_map['low']    = 'min'
        if 'close'  in df_h.columns: agg_map['close']  = 'last'
        if 'volume' in df_h.columns: agg_map['volume'] = 'sum'

        daily = df_h.groupby('trade_date').agg(agg_map)
        daily.index = pd.to_datetime(daily.index)
        daily.index.name = 'Date'

        # Filter to requested date range
        daily = daily[
            (daily.index >= pd.to_datetime(start_dt.date())) &
            (daily.index <= pd.to_datetime(end_dt.date()))
        ]

        # Drop sessions with fewer than 4 hours of data (incomplete candles)
        if 'close' in daily.columns:
            bar_counts = df_h.groupby('trade_date').size()
            bar_counts.index = pd.to_datetime(bar_counts.index)
            valid_dates = bar_counts[bar_counts >= 4].index
            daily = daily[daily.index.isin(valid_dates)]

        daily = daily.sort_index()

        # Add metadata
        daily.attrs['asset_key']    = asset_key
        daily.attrs['asset_name']   = asset.name
        daily.attrs['yahoo_symbol'] = asset.yahoo_symbol
        daily.attrs['session']      = 'CME_18-17_ET'
        daily.attrs['download_date'] = datetime.now().isoformat()

        logger.info(
            f"[CME Session] Built {len(daily)} daily CME candles for {asset.name}"
        )
        return daily

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


def download_asset_data_cme(
    asset_key: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    years_back: int = 5
) -> pd.DataFrame:
    """
    Convenience function to download daily data using CME session boundaries
    (18:00-17:00 ET), matching TradingView's daily candles for futures.

    Note: yfinance limits hourly data to ~730 days, so years_back > 2
    is not recommended unless the period is within the last 2 years.

    Args:
        asset_key: Asset identifier (e.g., 'NQ', 'ES', 'YM')
        start_date: Optional start date string (YYYY-MM-DD)
        end_date: Optional end date string (YYYY-MM-DD)
        years_back: Years of history if start_date not provided

    Returns:
        DataFrame with OHLCV data resampled to CME session boundaries.
    """
    loader = DataLoader()
    return loader.download_cme_session(asset_key, start_date, end_date, years_back)
