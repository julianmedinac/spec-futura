"""
Asset Configuration for DOR Framework
Defines available assets, their Yahoo Finance symbols, and metadata.
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class AssetClass(Enum):
    """Asset class categories."""
    FUTURES = "futures"
    EQUITY = "equity"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITY = "commodity"


@dataclass
class AssetConfig:
    """Configuration for a single asset."""
    name: str
    yahoo_symbol: str
    asset_class: AssetClass
    description: str
    trading_days_per_year: int = 252  # Default for most markets
    currency: str = "USD"


# Available assets configuration
ASSETS: Dict[str, AssetConfig] = {
    "NQ": AssetConfig(
        name="NASDAQ 100 E-mini Futures",
        yahoo_symbol="NQ=F",
        asset_class=AssetClass.FUTURES,
        description="E-mini NASDAQ 100 Futures Contract",
        trading_days_per_year=252,
        currency="USD"
    ),
    # Future assets can be added here
    "ES": AssetConfig(
        name="S&P 500 E-mini Futures",
        yahoo_symbol="ES=F",
        asset_class=AssetClass.FUTURES,
        description="E-mini S&P 500 Futures Contract",
        trading_days_per_year=252,
        currency="USD"
    ),
    "SPY": AssetConfig(
        name="SPDR S&P 500 ETF",
        yahoo_symbol="SPY",
        asset_class=AssetClass.EQUITY,
        description="S&P 500 Index ETF",
        trading_days_per_year=252,
        currency="USD"
    ),
    "QQQ": AssetConfig(
        name="Invesco QQQ Trust",
        yahoo_symbol="QQQ",
        asset_class=AssetClass.EQUITY,
        description="NASDAQ 100 Index ETF",
        trading_days_per_year=252,
        currency="USD"
    ),
    "GC": AssetConfig(
        name="Gold Futures",
        yahoo_symbol="GC=F",
        asset_class=AssetClass.COMMODITY,
        description="COMEX Gold Futures Contract",
        trading_days_per_year=252,
        currency="USD"
    ),
    "YM": AssetConfig(
        name="Dow Jones E-mini Futures",
        yahoo_symbol="YM=F",
        asset_class=AssetClass.FUTURES,
        description="E-mini Dow Jones Industrial Average Futures Contract",
        trading_days_per_year=252,
        currency="USD"
    ),
    "EURUSD": AssetConfig(
        name="Euro / US Dollar",
        yahoo_symbol="EURUSD=X",
        asset_class=AssetClass.FOREX,
        description="EUR/USD Spot Exchange Rate",
        trading_days_per_year=252,
        currency="USD"
    ),
    "GBPUSD": AssetConfig(
        name="British Pound / US Dollar",
        yahoo_symbol="GBPUSD=X",
        asset_class=AssetClass.FOREX,
        description="GBP/USD Spot Exchange Rate",
        trading_days_per_year=252,
        currency="USD"
    ),
    "6E": AssetConfig(
        name="Euro FX Futures",
        yahoo_symbol="6E=F",
        asset_class=AssetClass.FUTURES,
        description="CME Euro FX Futures Contract",
        trading_days_per_year=252,
        currency="USD"
    ),
    "6B": AssetConfig(
        name="British Pound Futures",
        yahoo_symbol="6B=F",
        asset_class=AssetClass.FUTURES,
        description="CME British Pound Futures Contract",
        trading_days_per_year=252,
        currency="USD"
    ),
    "GSPC": AssetConfig(
        name="S&P 500 Index",
        yahoo_symbol="^GSPC",
        asset_class=AssetClass.EQUITY,
        description="Standard & Poor's 500 Index",
        trading_days_per_year=252,
        currency="USD"
    ),
    "IDX": AssetConfig(
        name="NASDAQ Composite",
        yahoo_symbol="^IXIC",
        asset_class=AssetClass.EQUITY,
        description="NASDAQ Composite Index",
        trading_days_per_year=252,
        currency="USD"
    ),
    "DJI": AssetConfig(
        name="Dow Jones Industrial Average",
        yahoo_symbol="^DJI",
        asset_class=AssetClass.EQUITY,
        description="Dow Jones Industrial Average Index",
        trading_days_per_year=252,
        currency="USD"
    ),
}


def get_asset(asset_key: str) -> AssetConfig:
    """Get asset configuration by key."""
    if asset_key not in ASSETS:
        raise ValueError(f"Asset '{asset_key}' not found. Available: {list(ASSETS.keys())}")
    return ASSETS[asset_key]


def list_assets() -> List[str]:
    """List all available asset keys."""
    return list(ASSETS.keys())
