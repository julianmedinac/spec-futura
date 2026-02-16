"""
Timeframe Configuration for DOR Framework
Defines temporal aggregation periods and their annualization factors.
"""

from dataclasses import dataclass
from typing import Dict
from enum import Enum


class TimeframeCode(Enum):
    """Timeframe identifiers."""
    DAILY = "1D"
    WEEKLY = "1W"
    MONTHLY = "1M"
    QUARTERLY = "1Q"
    SEMIANNUAL = "6M"
    ANNUAL = "1Y"


@dataclass
class TimeframeConfig:
    """Configuration for a single timeframe."""
    name: str
    code: TimeframeCode
    pandas_freq: str  # Pandas frequency string for resampling
    periods_per_year: float  # For annualization
    description: str


# Timeframe configurations
# Based on standard financial conventions:
# - 252 trading days per year
# - 52 weeks per year
# - 12 months per year
# - 4 quarters per year
# - 2 semesters per year
# - 1 year

TIMEFRAMES: Dict[str, TimeframeConfig] = {
    "1D": TimeframeConfig(
        name="Daily",
        code=TimeframeCode.DAILY,
        pandas_freq="D",  # Will use actual trading days
        periods_per_year=252,
        description="Daily returns (trading days)"
    ),
    "1W": TimeframeConfig(
        name="Weekly",
        code=TimeframeCode.WEEKLY,
        pandas_freq="W-FRI",  # Week ending Friday
        periods_per_year=52,
        description="Weekly returns (Friday close to Friday close)"
    ),
    "1M": TimeframeConfig(
        name="Monthly",
        code=TimeframeCode.MONTHLY,
        pandas_freq="ME",  # Month end
        periods_per_year=12,
        description="Monthly returns (month-end to month-end)"
    ),
    "1Q": TimeframeConfig(
        name="Quarterly",
        code=TimeframeCode.QUARTERLY,
        pandas_freq="QE",  # Quarter end
        periods_per_year=4,
        description="Quarterly returns (quarter-end to quarter-end)"
    ),
    "6M": TimeframeConfig(
        name="Semi-Annual",
        code=TimeframeCode.SEMIANNUAL,
        pandas_freq="6ME",  # 6-month end
        periods_per_year=2,
        description="Semi-annual returns (6-month periods)"
    ),
    "1Y": TimeframeConfig(
        name="Annual",
        code=TimeframeCode.ANNUAL,
        pandas_freq="YE",  # Year end
        periods_per_year=1,
        description="Annual returns (year-end to year-end)"
    ),
}


def get_timeframe(timeframe_key: str) -> TimeframeConfig:
    """Get timeframe configuration by key."""
    if timeframe_key not in TIMEFRAMES:
        raise ValueError(f"Timeframe '{timeframe_key}' not found. Available: {list(TIMEFRAMES.keys())}")
    return TIMEFRAMES[timeframe_key]


def get_annualization_factor(timeframe_key: str) -> float:
    """
    Get the annualization factor for volatility.
    
    For volatility: multiply by sqrt(periods_per_year)
    For returns: multiply by periods_per_year
    """
    tf = get_timeframe(timeframe_key)
    return tf.periods_per_year


def list_timeframes() -> list:
    """List all available timeframe keys."""
    return list(TIMEFRAMES.keys())
