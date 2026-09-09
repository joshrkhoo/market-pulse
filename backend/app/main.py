import os
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.app.cache import TTLCache
from backend.app.config import (
    BASE_CURRENCIES,
    COMPARISON_CACHE_SECONDS,
    COMPARISON_PERIODS,
    COMPARISON_PERSPECTIVES,
    DEFAULT_BASE_CURRENCY,
    DEFAULT_PERIOD,
    INSTRUMENT_BY_SYMBOL,
    MAX_COMPARISON_SYMBOLS,
    PERIOD_CONFIG,
    SNAPSHOT_CACHE_SECONDS,
    HISTORY_CACHE_SECONDS,
)
from backend.app.models import (
    ComparisonResponse,
    HealthResponse,
    MarketHistoryResponse,
    MarketSnapshot,
    MarketsResponse,
    Period,
)
from backend.app.services.comparison import build_comparison
from backend.app.services.yfinance_client import fetch_all_snapshots, fetch_history, fetch_snapshot

# Create the FastAPI app
app = FastAPI(
    title="Market Pulse API",
    description="Global index and stock quotes for the Market Pulse dashboard",
    version="0.1.0",
)

# Local defaults plus optional CORS_ORIGINS (comma-separated) for deployed frontends
_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://market-pulse-pi-ten.vercel.app",
    "https://market-pulse.joshrkhoo.com",
]
_extra_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
_cors_origins = list(dict.fromkeys([*_DEFAULT_CORS_ORIGINS, *_extra_origins]))

# CORS is enabled to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Snapshot cache is short so last quotes can refresh while markets are open
_snapshots_cache: TTLCache[MarketsResponse] = TTLCache(ttl_seconds=SNAPSHOT_CACHE_SECONDS)
_quote_cache: TTLCache[MarketSnapshot] = TTLCache(ttl_seconds=SNAPSHOT_CACHE_SECONDS)
_history_cache: TTLCache[MarketHistoryResponse] = TTLCache(ttl_seconds=HISTORY_CACHE_SECONDS)
_comparison_cache: TTLCache[ComparisonResponse] = TTLCache(ttl_seconds=COMPARISON_CACHE_SECONDS)

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

    # Fetch the history from the data layer
    response = fetch_history(symbol, period)
    # Set the cache for the history response
    _history_cache.set(cache_key, response)
    return response


# Multi-asset comparison: rebase to 100 in each asset's own currency (local) or a base currency
@app.get("/api/markets/compare", response_model=ComparisonResponse)
def get_market_comparison(
    period: Period = Query("3M", description="Daily comparison range: 1M, 3M, 1Y, MAX"),
    base_currency: str = Query(
        DEFAULT_BASE_CURRENCY,
        description="Investor base currency for FX conversion before rebasing (used when perspective=base)",
    ),
    perspective: str = Query(
        "base",
        description="'local' rebases each asset in its own currency; 'base' converts into base_currency first",
    ),
    symbols: str | None = Query(
        None,
        description="Comma-separated Yahoo symbols; defaults to the five core indices",
    ),
) -> ComparisonResponse:
    view = perspective.lower()
    if view not in COMPARISON_PERSPECTIVES:
        raise HTTPException(
            status_code=400,
            detail=f"Perspective must be one of: {', '.join(COMPARISON_PERSPECTIVES)}",
        )

    base = base_currency.upper()
    # Base currency only matters when converting; skip the check for the local view
    if view == "base" and base not in BASE_CURRENCIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported base currency: {base_currency}",
        )
    if period not in COMPARISON_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Comparison period must be one of: {', '.join(COMPARISON_PERIODS)}",
        )

    symbol_list = None
    if symbols:
        symbol_list = [part.strip() for part in symbols.split(",") if part.strip()]
        unknown = [s for s in symbol_list if s not in INSTRUMENT_BY_SYMBOL]
        if unknown:
            raise HTTPException(status_code=404, detail=f"Unknown symbols: {', '.join(unknown)}")
        if len(symbol_list) > MAX_COMPARISON_SYMBOLS:
            raise HTTPException(
                status_code=400,
                detail=f"Compare up to {MAX_COMPARISON_SYMBOLS} symbols at once",
            )

    symbol_key = ",".join(symbol_list) if symbol_list else "indices"
    cache_key = f"compare:{period}:{view}:{base}:{symbol_key}"
    cached = _comparison_cache.get(cache_key)
    if cached is not None:
        return cached

    response = build_comparison(
        period=period, base_currency=base, symbols=symbol_list, perspective=view
    )
    _comparison_cache.set(cache_key, response)
    return response
