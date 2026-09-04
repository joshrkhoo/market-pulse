from datetime import datetime, timezone
import math

import pandas as pd
import yfinance as yf

from backend.app.config import (
    DEFAULT_PERIOD,
    INSTRUMENT_BY_SYMBOL,
    INSTRUMENTS,
    PERIOD_CONFIG,
    SNAPSHOT_LOOKBACK_DAYS,
    Instrument,
)
from backend.app.models import MarketHistoryResponse, MarketSnapshot, Period, PricePoint
from backend.app.services.market_hours import get_session


"""
A helper function to convert a pandas timestamp to a UTC datetime
"""
def _to_utc(ts: pd.Timestamp) -> datetime:
    if ts.tzinfo is None:
        return ts.to_pydatetime().replace(tzinfo=timezone.utc)
    return ts.to_pydatetime().astimezone(timezone.utc)


"""
A helper function to calculate the daily return percentage.
Calculated by: ((latest_price - previous_close) / previous_close) * 100
"""
def _daily_return_pct(latest: float, previous: float | None) -> float | None:
    if previous is None or previous == 0:
        return None
    return ((latest - previous) / previous) * 100


"""
Parse a numeric quote value, ignoring NaN/inf from the provider
"""
def _finite(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


"""
Read last quote, previous close, and session open from yfinance fast_info when available
"""
def _quote_from_fast_info(
    ticker: yf.Ticker,
) -> tuple[float | None, float | None, float | None]:
    try:
        info = ticker.fast_info
        last = _finite(getattr(info, "last_price", None))
        previous = _finite(getattr(info, "previous_close", None))
        session_open = _finite(getattr(info, "open", None))
        return last, previous, session_open
    except Exception:
        return None, None, None


"""
Fallback last price from 1-minute bars while the market is open
"""
def _last_price_from_intraday(ticker: yf.Ticker) -> tuple[float | None, datetime | None]:
    try:
        frame = ticker.history(period="1d", interval="1m")
        if frame.empty or "Close" not in frame.columns:
            return None, None
        closes = frame["Close"].dropna()
        if closes.empty:
            return None, None
        return float(closes.iloc[-1]), _to_utc(closes.index[-1])
    except Exception:
        return None, None


"""
Fetch the snapshot for a given ticker: current quote, session open, last close, and session status.
Indexes use a current *level*; stocks use a current *price* (same numeric field: last).
Falls back to daily OHLC if a live quote is unavailable.
"""
def fetch_snapshot(instrument: Instrument) -> MarketSnapshot:
    # Session status uses weekday + regular hours only (no public holidays)
    is_open, session_note = get_session(instrument)
    base = MarketSnapshot(
        symbol=instrument.symbol,
        name=instrument.name,
        region=instrument.region,
        currency=instrument.currency,
        timezone=instrument.timezone,
        kind=instrument.kind,
        is_open=is_open,
        session_note=session_note,
    )
    # Try to fetch the snapshot for the given instrument
    try:
        ticker = yf.Ticker(instrument.symbol)
        # Daily bars provide open, close, previous close, and a fallback last quote
        frame = ticker.history(period=SNAPSHOT_LOOKBACK_DAYS, interval="1d")
        if frame.empty or "Close" not in frame.columns:
            return base.model_copy(update={"error": "No data returned from provider"})

        bars = frame.dropna(subset=["Close"])
        if bars.empty:
            return base.model_copy(update={"error": "No close prices available"})

        latest_bar = bars.iloc[-1]
        daily_open = _finite(latest_bar["Open"]) if "Open" in bars.columns else None
        daily_close = float(latest_bar["Close"])
        daily_previous = float(bars.iloc[-2]["Close"]) if len(bars) >= 2 else None
        daily_ts = _to_utc(bars.index[-1])

        last, previous, session_open = _quote_from_fast_info(ticker)
        quote_ts = datetime.now(timezone.utc) if last is not None else None

        # If fast_info has no last quote while the market is open, use 1-minute bars
        if last is None and is_open:
            last, quote_ts = _last_price_from_intraday(ticker)

        if last is None:
            last = daily_close
            quote_ts = daily_ts
        if previous is None:
            previous = daily_previous
        if session_open is None:
            session_open = daily_open

        # While open, "close" is the last completed session close (previous close).
        # While closed, "close" is today's completed close.
        completed_close = previous if is_open else daily_close

        ret = _daily_return_pct(last, previous)
        return base.model_copy(
            update={
                "last": round(last, 2),
                "open": round(session_open, 2) if session_open is not None else None,
                "close": round(completed_close, 2) if completed_close is not None else None,
                "daily_return_pct": round(ret, 4) if ret is not None else None,
                "updated_at": quote_ts or daily_ts,
            }
        )
    # If an error occurs, return the base model with the error
    except Exception as exc:  # noqa: BLE001 - surface provider errors per instrument
        return base.model_copy(update={"error": str(exc)})

"""
A function to fetch snapshots for every configured ticker (indices and stocks)
"""
def fetch_all_snapshots() -> list[MarketSnapshot]:
    return [fetch_snapshot(instrument) for instrument in INSTRUMENTS]

"""
A function to fetch the history for a given symbol and period
"""
def fetch_history(symbol: str, period: Period = DEFAULT_PERIOD) -> MarketHistoryResponse:
    instrument = INSTRUMENT_BY_SYMBOL.get(symbol)
    if instrument is None:
        return MarketHistoryResponse(
            symbol=symbol,
            name="Unknown",
            kind="index",
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
                kind=instrument.kind,
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
            kind=instrument.kind,
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
            kind=instrument.kind,
            period=period,
            currency=instrument.currency,
            points=[],
            fetched_at=datetime.now(timezone.utc),
            error=str(exc),
        )
