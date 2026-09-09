"""
Convert native-currency price series into a selected base currency.

fx_rate must mean: 1 native currency = X base currency.
Conversion happens before rebasing in the comparison pipeline.
"""

from __future__ import annotations

import pandas as pd


def invert_fx_rate(rate: float) -> float:
    """Invert a quote when the provider returns base/native instead of native/base."""
    if rate == 0:
        raise ValueError("Cannot invert a zero FX rate")
    return 1.0 / rate


def align_fx_to_prices(prices: pd.Series, fx_rates: pd.Series) -> pd.Series:
    """
    Align FX rates onto asset trading dates.

    Missing FX dates (weekends/holidays) use the most recent previous valid rate.
    Never fills with 0. Dates with no prior FX rate are left as NaN and dropped later.
    """
    if prices.empty:
        return pd.Series(dtype=float)

    # Normalise to date-only indexes for asof alignment across timezones
    price_idx = pd.DatetimeIndex(pd.to_datetime(prices.index)).tz_localize(None).normalize()
    fx = fx_rates.dropna().copy()
    if fx.empty:
        return pd.Series(index=price_idx, dtype=float)

    fx.index = pd.DatetimeIndex(pd.to_datetime(fx.index)).tz_localize(None).normalize()
    fx = fx[~fx.index.duplicated(keep="last")].sort_index()

    # asof: for each price date, take the last FX observation on or before that date
    aligned = fx.reindex(price_idx.union(fx.index)).sort_index().ffill()
    return aligned.reindex(price_idx)


def convert_to_base(prices: pd.Series, fx_rates: pd.Series) -> pd.Series:
    """
    Convert native prices into the base currency.

    converted_price = native_price * fx_rate

    Drops dates where price or FX is missing. Never replaces missing values with 0.
    """
    if prices.empty:
        return pd.Series(dtype=float)

    native = prices.dropna()
    if native.empty:
        return pd.Series(dtype=float)

    fx_aligned = align_fx_to_prices(native, fx_rates)
    # Restore the original price index labels where possible
    fx_aligned.index = native.index

    converted = native.astype(float) * fx_aligned.astype(float)
    return converted.dropna()
