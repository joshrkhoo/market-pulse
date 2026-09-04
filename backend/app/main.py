from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.app.cache import TTLCache
from backend.app.config import DEFAULT_PERIOD, INSTRUMENT_BY_SYMBOL, PERIOD_CONFIG, SNAPSHOT_CACHE_SECONDS, HISTORY_CACHE_SECONDS
from backend.app.models import (
    HealthResponse,
    MarketHistoryResponse,
    MarketSnapshot,
    MarketsResponse,
    Period,
)
from backend.app.services.yfinance_client import fetch_all_snapshots, fetch_history, fetch_snapshot

# Create the FastAPI app
app = FastAPI(
    title="Market Pulse API",
    description="Global index and stock quotes for the Market Pulse dashboard",
    version="0.1.0",
)

# CORS is enabled to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Snapshot cache is short so last quotes can refresh while markets are open
_snapshots_cache: TTLCache[MarketsResponse] = TTLCache(ttl_seconds=SNAPSHOT_CACHE_SECONDS)
_quote_cache: TTLCache[MarketSnapshot] = TTLCache(ttl_seconds=SNAPSHOT_CACHE_SECONDS)
_history_cache: TTLCache[MarketHistoryResponse] = TTLCache(ttl_seconds=HISTORY_CACHE_SECONDS)

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")

# Markets endpoint
@app.get("/api/markets", response_model=MarketsResponse)
def get_markets() -> MarketsResponse:
    # Check the cache for the markets response
    cached = _snapshots_cache.get("markets")
    # If the cache is not empty, return the cached response
    if cached is not None:
        return cached

    # Fetch the markets from Yahoo via the data layer
    response = MarketsResponse(
        markets=fetch_all_snapshots(),
        fetched_at=datetime.now(timezone.utc),
    )
    # Set the cache for the markets response and each ticker so per-symbol refresh can reuse it
    _snapshots_cache.set("markets", response)
    for market in response.markets:
        _quote_cache.set(f"snapshot:{market.symbol}", market)
    return response


# Single-ticker snapshot used by the dashboard to auto-refresh each current level/price
@app.get("/api/markets/snapshot", response_model=MarketSnapshot)
def get_market_snapshot(
    symbol: str = Query(..., description="Yahoo Finance ticker, e.g. ^GSPC or MSFT"),
) -> MarketSnapshot:
    if symbol not in INSTRUMENT_BY_SYMBOL:
        raise HTTPException(status_code=404, detail=f"Unknown symbol: {symbol}")

    cache_key = f"snapshot:{symbol}"
    cached = _quote_cache.get(cache_key)
    if cached is not None:
        return cached

    snapshot = fetch_snapshot(INSTRUMENT_BY_SYMBOL[symbol])
    _quote_cache.set(cache_key, snapshot)
    return snapshot

# Market history endpoint
@app.get("/api/markets/history", response_model=MarketHistoryResponse)

# Get the market history for a given symbol and period
def get_market_history(
    symbol: str = Query(..., description="Yahoo Finance ticker, e.g. ^GSPC"),
    period: Period = Query(DEFAULT_PERIOD, description="Chart time range"),
) -> MarketHistoryResponse:
    # Check if the symbol is valid
    if symbol not in INSTRUMENT_BY_SYMBOL:
        raise HTTPException(status_code=404, detail=f"Unknown symbol: {symbol}")
    # Check if the period is valid
    if period not in PERIOD_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

    # Create a cache key for the history response   
    cache_key = f"history:{symbol}:{period}"
    # Check the cache for the history response
    cached = _history_cache.get(cache_key)
    # If the cache is not empty, return the cached response
    if cached is not None:
        return cached

    # Fetch the history from the API
    response = fetch_history(symbol, period)
    # Set the cache for the history response
    _history_cache.set(cache_key, response)
    return response
