"""
Fetch and cache FX rate series for converting native prices into a base currency.

Returned rates always mean: 1 native currency = X base currency.
If Yahoo only provides the opposite pair, the series is inverted.
"""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from backend.app.cache import TTLCache
from backend.app.config import PERIOD_CONFIG
from backend.app.models import Period
from backend.app.services.currency_convert import invert_fx_rate

# Reuse FX across assets that share the same native→base pair
_fx_cache: TTLCache[pd.Series] = TTLCache(ttl_seconds=300)


def _pair_symbol(base: str, quote: str) -> str:
    """Yahoo FX ticker for 1 base = X quote, e.g. AUDUSD=X."""
    return f"{base}{quote}=X"


"""
Fetch a close series for a Yahoo FX ticker over the given chart period.
"""
def _history_closes(yahoo_symbol: str, period: Period) -> pd.Series:
    config = PERIOD_CONFIG[period]
    frame = yf.Ticker(yahoo_symbol).history(period=config["period"], interval=config["interval"])
    if frame.empty or "Close" not in frame.columns:
        return pd.Series(dtype=float)
    closes = frame["Close"].dropna()
    if closes.empty:
        return pd.Series(dtype=float)
    # Date-normalised naive index for alignment with equity calendars
    closes = closes.copy()
    closes.index = pd.DatetimeIndex(pd.to_datetime(closes.index)).tz_localize(None).normalize()
    # '~' flips rows where duplicated is True get flipped to false and dropped.
    # bitwise / boolean NOT operator
    return closes[~closes.index.duplicated(keep="last")].sort_index()


"""
Time series of FX rates.
Return FX rates where 1 native = X base for the requested period.
Caches by (native, base, period) so USD assets share one USD→AUD series.
"""
def fetch_fx_rate_series(native: str, base: str, period: Period) -> pd.Series:
    native = native.upper()
    base = base.upper()

    # same currency, no FX conversion needed
    if native == base:
        # Unit rate; convert_to_base will forward-fill onto each price date
        today = pd.Timestamp.today().normalize()
        return pd.Series([1.0], index=pd.DatetimeIndex([today]))

    # check cache for cached rates
    cache_key = f"fx:{native}:{base}:{period}"
    cached = _fx_cache.get(cache_key)
    if cached is not None:
        return cached

    # Prefer direct pair: 1 native = X base
        # Check if yahoo finance has the direct pair
    direct = _history_closes(_pair_symbol(native, base), period)
    if not direct.empty:
        _fx_cache.set(cache_key, direct)
        return direct

    # Fall back to inverse pair: 1 base = X native → invert
        # If the direct pair is not available, use the inverse pair
    inverse = _history_closes(_pair_symbol(base, native), period)
    if inverse.empty:
        return pd.Series(dtype=float)

    inverted = inverse.map(invert_fx_rate)
    _fx_cache.set(cache_key, inverted)
    return inverted
