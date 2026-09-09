from dataclasses import dataclass
from datetime import time
from typing import Literal

AssetKind = Literal["index", "stock"]

"""
Regular cash-session hours in each exchange's local timezone.
Lunch breaks are treated as closed. Public holidays are not modelled.
"""
US_REGULAR = ((time(9, 30), time(16, 0)),)
ASX_REGULAR = ((time(10, 0), time(16, 0)),)
HK_REGULAR = ((time(9, 30), time(12, 0)), (time(13, 0), time(16, 0)))
JP_REGULAR = ((time(9, 0), time(11, 30)), (time(12, 30), time(15, 0)))


"""
A dataclass for a ticker (index or stock).
Includes regular trading sessions used for open/closed status.
kind controls UI wording: indexes use "level", stocks use "price".
"""
@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    region: str
    currency: str
    timezone: str
    sessions: tuple[tuple[time, time], ...]
    kind: AssetKind


# Keep the old name so existing comments/imports that say IndexInstrument still make sense.
IndexInstrument = Instrument


"""
A tuple of the core equity indices.
Use a tuple to ensure immutability and order.
"""
INDICES: tuple[Instrument, ...] = (
    Instrument("^GSPC", "S&P 500", "United States", "USD", "America/New_York", US_REGULAR, "index"),
    Instrument("^IXIC", "NASDAQ Composite", "United States", "USD", "America/New_York", US_REGULAR, "index"),
    Instrument("^AXJO", "ASX 200", "Australia", "AUD", "Australia/Sydney", ASX_REGULAR, "index"),
    Instrument("^HSI", "Hang Seng Index", "Hong Kong", "HKD", "Asia/Hong_Kong", HK_REGULAR, "index"),
    Instrument("^N225", "Nikkei 225", "Japan", "JPY", "Asia/Tokyo", JP_REGULAR, "index"),
)

"""
Individual stocks. Current quotes are shown as prices, not index levels.
"""
STOCKS: tuple[Instrument, ...] = (
    Instrument("MSFT", "Microsoft", "United States", "USD", "America/New_York", US_REGULAR, "stock"),
)

# All tickers shown on the dashboard, indices first
INSTRUMENTS: tuple[Instrument, ...] = INDICES + STOCKS

# A dictionary of instruments by Yahoo Finance symbol
INSTRUMENT_BY_SYMBOL: dict[str, Instrument] = {i.symbol: i for i in INSTRUMENTS}
INDEX_BY_SYMBOL = INSTRUMENT_BY_SYMBOL

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
# Snapshot cache is short so last quotes can refresh while markets are open
SNAPSHOT_CACHE_SECONDS = 15
HISTORY_CACHE_SECONDS = 60

# Comparison chart: base-currency performance after FX conversion + rebase to 100
DEFAULT_BASE_CURRENCY = "USD"
BASE_CURRENCIES: tuple[str, ...] = ("USD", "AUD", "EUR", "GBP", "JPY", "HKD")
# Daily intervals only for FX alignment (skip 1D/1W intraday for v1)
COMPARISON_PERIODS: tuple[str, ...] = ("1M", "3M", "1Y", "MAX")
COMPARISON_CACHE_SECONDS = 120
# Return perspectives the compare endpoint accepts (see models.Perspective)
COMPARISON_PERSPECTIVES: tuple[str, ...] = ("local", "base")
# Cap the compare set so the multi-line chart stays readable
MAX_COMPARISON_SYMBOLS = 6
