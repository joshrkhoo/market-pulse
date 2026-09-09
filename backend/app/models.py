from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

"""
A type for the period
This is used to store the period for the market history response
"""
Period = Literal["1D", "1W", "1M", "3M", "1Y", "MAX"]


"""
Investor return perspective for the comparison chart:
- "local": each series rebased in its own native currency (no FX applied)
- "base": convert into the selected base currency first, then rebase (price move + FX move)
"""
Perspective = Literal["local", "base"]


"""
A model for the market snapshot
This is used to store the market snapshot for the markets response
A market snapshot is a single ticker at a given time.
Indexes expose a current *level*; stocks expose a current *price*.
Both include session open, last completed close, and session status.
"""
class MarketSnapshot(BaseModel):
    symbol: str
    name: str
    region: str
    currency: str
    timezone: str
    kind: Literal["index", "stock"] = "index"
    last: float | None = Field(
        None, description="Current delayed quote (index level or stock price)"
    )
    open: float | None = Field(None, description="Session open")
    close: float | None = Field(
        None, description="Last completed session close (previous close while the market is open)"
    )
    daily_return_pct: float | None = Field(
        None, description="Percentage change vs prior trading close"
    )
    is_open: bool = False
    session_note: str = "Closed"
    updated_at: datetime | None = None
    error: str | None = None

"""
A model for the markets response
This is used to store the markets response
A markets response is a list of market snapshots
"""
class MarketsResponse(BaseModel):
    markets: list[MarketSnapshot]
    fetched_at: datetime


"""
A model for the price point
This is used to store the price point for the market history response
A price point is a single price at a given time
"""
class PricePoint(BaseModel):
    timestamp: datetime
    close: float


"""
A model for the market history response
This is used to store the market history response
A market history response is a list of price points
"""
class MarketHistoryResponse(BaseModel):
    symbol: str
    name: str
    kind: Literal["index", "stock"] = "index"
    period: Period
    currency: str
    points: list[PricePoint]
    fetched_at: datetime
    error: str | None = None


class HealthResponse(BaseModel):
    status: str


"""
A single rebased point on the multi-asset comparison chart (starts at 100)
"""
class ComparisonPoint(BaseModel):
    timestamp: datetime
    rebased: float


"""
One asset in a base-currency comparison: local vs base window returns + rebased path
"""
class ComparisonSeries(BaseModel):
    symbol: str
    name: str
    kind: Literal["index", "stock"] = "index"
    native_currency: str
    local_return_pct: float | None = Field(
        None, description="Window return in the asset native currency (no FX)"
    )
    base_return_pct: float | None = Field(
        None, description="Window return after converting into the selected base currency"
    )
    points: list[ComparisonPoint]
    error: str | None = None


"""
Multi-asset comparison response. Chart series are rebased to 100.
perspective="base" rebases in base_currency (price + FX); "local" rebases each in its own currency.
"""
class ComparisonResponse(BaseModel):
    base_currency: str
    perspective: Perspective = "base"
    period: Period
    series: list[ComparisonSeries]
    fetched_at: datetime
    error: str | None = None
