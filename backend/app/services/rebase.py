"""
Rebase a price series so the first valid point is 100.
Used for multi-asset comparison charts (after FX conversion).
"""

from __future__ import annotations

import pandas as pd


def rebase_to_100(prices: pd.Series) -> pd.Series:
    """
    Convert a price series into an index starting at 100.

    rebased = price / price.iloc[0] * 100

    Raises ValueError if the series is empty or the first value is zero/NaN.
    """
    clean = prices.dropna()
    if clean.empty:
        raise ValueError("Cannot rebase an empty series")
    base = float(clean.iloc[0])
    if base == 0:
        raise ValueError("Cannot rebase when the first price is zero")
    return (clean / base) * 100


def period_return_pct(prices: pd.Series) -> float | None:
    """
    Percentage change from the first to the last valid price.
    This is a window return, not a realised trading P&L label.
    """
    clean = prices.dropna()
    if len(clean) < 2:
        return None
    start = float(clean.iloc[0])
    end = float(clean.iloc[-1])
    if start == 0:
        return None
    return ((end - start) / start) * 100
