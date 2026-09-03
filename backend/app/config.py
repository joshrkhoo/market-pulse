from dataclasses import dataclass

"""
A dataclass for the index instruments
This is used to store the index instruments and their properties
"""
@dataclass(frozen=True)
class IndexInstrument:
    symbol: str
    name: str
    region: str
    currency: str
    timezone: str

"""
A tuple of the index instruments
Use a tuple to ensure immutability and order of the index instruments
This will be used to iterate over the index instruments
"""
INDICES: tuple[IndexInstrument, ...] = (
    IndexInstrument("^GSPC", "S&P 500", "United States", "USD", "America/New_York"),
    IndexInstrument("^IXIC", "NASDAQ Composite", "United States", "USD", "America/New_York"),
    IndexInstrument("^AXJO", "ASX 200", "Australia", "AUD", "Australia/Sydney"),
    IndexInstrument("^HSI", "Hang Seng Index", "Hong Kong", "HKD", "Asia/Hong_Kong"),
    IndexInstrument("^N225", "Nikkei 225", "Japan", "JPY", "Asia/Tokyo"),
)

# A dictionary of the index instruments by symbol
INDEX_BY_SYMBOL: dict[str, IndexInstrument] = {i.symbol: i for i in INDICES}

# User-facing chart ranges mapped to yfinance period/interval pairs.
PERIOD_CONFIG: dict[str, dict[str, str]] = {
    "1D": {"period": "1d", "interval": "5m"},
    "1W": {"period": "5d", "interval": "1h"},
    "1M": {"period": "1mo", "interval": "1d"},
    "3M": {"period": "3mo", "interval": "1d"},
    "1Y": {"period": "1y", "interval": "1d"},
    "MAX": {"period": "max", "interval": "1d"},
}

DEFAULT_PERIOD = "1M"
SNAPSHOT_LOOKBACK_DAYS = "10d"
