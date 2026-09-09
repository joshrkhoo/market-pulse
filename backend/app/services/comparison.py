"""
Build multi-asset comparison series: FX convert into a base currency, then rebase to 100.

Local return uses native prices only.
Base-currency return uses converted prices (price move + FX move).
Neither is labelled as realised return.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from backend.app.config import (
    COMPARISON_PERIODS,
    DEFAULT_BASE_CURRENCY,
    INDICES,
    INSTRUMENT_BY_SYMBOL,
    PERIOD_CONFIG,
    Instrument,
)
from backend.app.models import (
    ComparisonPoint,
    ComparisonResponse,
    ComparisonSeries,
    Period,
    Perspective,
)
from backend.app.services.currency_convert import convert_to_base
from backend.app.services.fx import fetch_fx_rate_series
from backend.app.services.rebase import period_return_pct, rebase_to_100
from backend.app.services.yfinance_client import _to_utc


"""
Fetch a daily native close series for one instrument.
"""
def _native_close_series(instrument: Instrument, period: Period) -> pd.Series:
    config = PERIOD_CONFIG[period]
    frame = yf.Ticker(instrument.symbol).history(
        period=config["period"], interval=config["interval"]
    )
    if frame.empty or "Close" not in frame.columns:
        return pd.Series(dtype=float)
    closes = frame["Close"].dropna()
    if closes.empty:
        return pd.Series(dtype=float)
    closes = closes.copy()
    closes.index = pd.DatetimeIndex(pd.to_datetime(closes.index)).tz_localize(None).normalize()
    return closes[~closes.index.duplicated(keep="last")].sort_index()


"""
Build one comparison series for an instrument.

perspective="local": rebase the native series in its own currency (no FX, base_return stays None).
perspective="base": FX convert into base_currency first, then rebase (price move + FX move).
"""
def _build_series(
    instrument: Instrument,
    period: Period,
    base_currency: str,
    perspective: Perspective,
) -> ComparisonSeries:
    native = _native_close_series(instrument, period)
    if native.empty:
        return ComparisonSeries(
            symbol=instrument.symbol,
            name=instrument.name,
            kind=instrument.kind,
            native_currency=instrument.currency,
            local_return_pct=None,
            base_return_pct=None,
            points=[],
            error="No native price history available",
        )

    try:
        if perspective == "local":
            # No FX: each asset is rebased in its own native currency
            converted = native
            base_ret = None
        else:
            fx = fetch_fx_rate_series(instrument.currency, base_currency, period)
            if instrument.currency.upper() != base_currency.upper() and fx.empty:
                return ComparisonSeries(
                    symbol=instrument.symbol,
                    name=instrument.name,
                    kind=instrument.kind,
                    native_currency=instrument.currency,
                    local_return_pct=period_return_pct(native),
                    base_return_pct=None,
                    points=[],
                    error=f"No FX data for {instrument.currency}→{base_currency}",
                )

            if instrument.currency.upper() == base_currency.upper():
                # Unit FX aligned onto every price date
                fx = pd.Series(1.0, index=native.index)

            converted = convert_to_base(native, fx)
            if converted.empty:
                return ComparisonSeries(
                    symbol=instrument.symbol,
                    name=instrument.name,
                    kind=instrument.kind,
                    native_currency=instrument.currency,
                    local_return_pct=period_return_pct(native),
                    base_return_pct=None,
                    points=[],
                    error="Could not align FX rates with price dates",
                )
            base_ret = period_return_pct(converted)

        rebased = rebase_to_100(converted)
        points = [
            ComparisonPoint(timestamp=_to_utc(pd.Timestamp(ts)), rebased=round(float(value), 4))
            for ts, value in rebased.items()
        ]
        return ComparisonSeries(
            symbol=instrument.symbol,
            name=instrument.name,
            kind=instrument.kind,
            native_currency=instrument.currency,
            local_return_pct=(
                round(ret, 4) if (ret := period_return_pct(native)) is not None else None
            ),
            base_return_pct=round(base_ret, 4) if base_ret is not None else None,
            points=points,
        )
    except Exception as exc:  # noqa: BLE001
        return ComparisonSeries(
            symbol=instrument.symbol,
            name=instrument.name,
            kind=instrument.kind,
            native_currency=instrument.currency,
            local_return_pct=None,
            base_return_pct=None,
            points=[],
            error=str(exc),
        )


"""
Compare multiple instruments after rebasing each to 100.

perspective="base": FX convert into base_currency first, then rebase (price + FX move).
perspective="local": rebase each asset in its own native currency (no FX).
Defaults to the five core indices when symbols are omitted.
"""
def build_comparison(
    period: Period,
    base_currency: str = DEFAULT_BASE_CURRENCY,
    symbols: list[str] | None = None,
    perspective: Perspective = "base",
) -> ComparisonResponse:
    if period not in COMPARISON_PERIODS:
        return ComparisonResponse(
            base_currency=base_currency.upper(),
            perspective=perspective,
            period=period,
            series=[],
            fetched_at=datetime.now(timezone.utc),
            error=f"Period {period} is not supported for comparison (use daily ranges)",
        )

    if symbols:
        instruments = []
        for symbol in symbols:
            instrument = INSTRUMENT_BY_SYMBOL.get(symbol)
            if instrument is None:
                continue
            instruments.append(instrument)
    else:
        instruments = list(INDICES)

    series = [
        _build_series(instrument, period, base_currency.upper(), perspective)
        for instrument in instruments
    ]
    return ComparisonResponse(
        base_currency=base_currency.upper(),
        perspective=perspective,
        period=period,
        series=series,
        fetched_at=datetime.now(timezone.utc),
    )
