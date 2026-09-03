from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from backend.app.config import (
    DEFAULT_PERIOD,
    INDEX_BY_SYMBOL,
    INDICES,
    PERIOD_CONFIG,
    SNAPSHOT_LOOKBACK_DAYS,
    IndexInstrument,
)
from backend.app.models import MarketHistoryResponse, MarketSnapshot, Period, PricePoint

"""
A helper function to convert a pandas timestamp to a UTC datetime
"""
def _to_utc(ts: pd.Timestamp) -> datetime:
    if ts.tzinfo is None:
        return ts.to_pydatetime().replace(tzinfo=timezone.utc)
    return ts.to_pydatetime().astimezone(timezone.utc)

"""
A helper function to calculate the daily return percentage
Calculated by: ((latest_close - previous_close) / previous_close) * 100
"""
def _daily_return_pct(closes: pd.Series) -> float | None:
    if len(closes) < 2:
        return None
    previous_close = float(closes.iloc[-2])
    latest_close = float(closes.iloc[-1])
    if previous_close == 0:
        return None
    return ((latest_close - previous_close) / previous_close) * 100

"""
A function to fetch the snapshot for a given instrument
"""
def fetch_snapshot(instrument: IndexInstrument) -> MarketSnapshot:
    base = MarketSnapshot(
        symbol=instrument.symbol,
        name=instrument.name,
        region=instrument.region,
        currency=instrument.currency,
        timezone=instrument.timezone,
    )
    # Try to fetch the snapshot for the given instrument
    try:
        # Fetch the history for the given instrument
        frame = yf.Ticker(instrument.symbol).history(
            period=SNAPSHOT_LOOKBACK_DAYS, interval="1d"
        )
        # If the frame is empty or the "Close" column is not in the frame, return an error
        if frame.empty or "Close" not in frame.columns:
            return base.model_copy(update={"error": "No data returned from provider"})
        # Get the closes for the given instrument
        closes = frame["Close"].dropna()
        # If the closes are empty, return an error
        if closes.empty:
            return base.model_copy(update={"error": "No close prices available"})
        # Get the latest timestamp for the given instrument
        latest_ts = closes.index[-1]
        # Update the base model with the latest level, daily return percentage, and updated at timestamp
        return base.model_copy(
            update={
                "level": round(float(closes.iloc[-1]), 2),
                "daily_return_pct": (
                    round(ret, 4) if (ret := _daily_return_pct(closes)) is not None else None
                ),
                "updated_at": _to_utc(latest_ts),
            }
        )
    # If an error occurs, return the base model with the error
    except Exception as exc:  # noqa: BLE001 - surface provider errors per instrument
        # Surface the error
        return base.model_copy(update={"error": str(exc)})

"""
A function to fetch all the snapshots for all the instruments
"""
def fetch_all_snapshots() -> list[MarketSnapshot]:
    return [fetch_snapshot(instrument) for instrument in INDICES]

"""
A function to fetch the history for a given symbol and period
"""
def fetch_history(symbol: str, period: Period = DEFAULT_PERIOD) -> MarketHistoryResponse:
    instrument = INDEX_BY_SYMBOL.get(symbol)
    if instrument is None:
        return MarketHistoryResponse(
            symbol=symbol,
            name="Unknown",
            period=period,
            currency="",
            points=[],
            fetched_at=datetime.now(timezone.utc),
            error=f"Unknown symbol: {symbol}",
        )
        
    # Try to fetch the history for the given symbol and period
    config = PERIOD_CONFIG[period]
    try:
        frame = yf.Ticker(symbol).history(
            period=config["period"], interval=config["interval"]
        )
        # If the frame is empty or the "Close" column is not in the frame, return an error
        if frame.empty or "Close" not in frame.columns:
            return MarketHistoryResponse(
                symbol=symbol,
                name=instrument.name,
                period=period,
                currency=instrument.currency,
                points=[],
                fetched_at=datetime.now(timezone.utc),
                error="No historical data returned from provider",
            )
        # Create the price points for the given symbol and period
        points = [
            PricePoint(timestamp=_to_utc(ts), close=round(float(close), 2))
            for ts, close in frame["Close"].dropna().items()
        ]
        # Return the market history response
        return MarketHistoryResponse(
            symbol=symbol,
            name=instrument.name,
            period=period,
            currency=instrument.currency,
            points=points,
            fetched_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        # If an error occurs, return the market history response with the error
        return MarketHistoryResponse(
            symbol=symbol,
            name=instrument.name,
            period=period,
            currency=instrument.currency,
            points=[],
            fetched_at=datetime.now(timezone.utc),
            error=str(exc),
        )
