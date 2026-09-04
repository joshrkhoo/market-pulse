export type Period = "1D" | "1W" | "1M" | "3M" | "1Y" | "MAX";

/** Indexes are quoted as levels; stocks are quoted as prices */
export type AssetKind = "index" | "stock";

/**
 * A type for the market snapshot
 * This is used to store the market snapshot for the markets response
 * A market snapshot is a single ticker at a given time
 */
export interface MarketSnapshot {
  symbol: string;
  name: string;
  region: string;
  currency: string;
  timezone: string;
  kind: AssetKind;
  /** Current delayed quote: index level or stock price */
  last: number | null;
  /** Session open */
  open: number | null;
  /** Last completed session close */
  close: number | null;
  daily_return_pct: number | null;
  /** True during regular weekday cash-session hours */
  is_open: boolean;
  /** e.g. "Closes 16:00" or "Opens Fri 09:30" */
  session_note: string;
  updated_at: string | null;
  error: string | null;
}

/**
 * A type for the markets response
 * This is used to store the markets response
 * A markets response is a list of market snapshots
 */
export interface MarketsResponse {
  markets: MarketSnapshot[];
  fetched_at: string;
}

/**
 * A type for the price point
 * This is used to store the price point for the market history response
 * A price point is a single price at a given time
 */
export interface PricePoint {
  timestamp: string;
  close: number;
}

/**
 * A type for the market history response
 * This is used to store the market history response
 * A market history response is a list of price points
 */
export interface MarketHistoryResponse {
  symbol: string;
  name: string;
  kind: AssetKind;
  period: Period;
  currency: string;
  points: PricePoint[];
  fetched_at: string;
  error: string | null;
}

export const PERIODS: Period[] = ["1D", "1W", "1M", "3M", "1Y", "MAX"];

export const DEFAULT_SYMBOL = "^GSPC";

/** How often each ticker's current level/price is polled */
export const MARKET_POLL_MS = 30_000;
