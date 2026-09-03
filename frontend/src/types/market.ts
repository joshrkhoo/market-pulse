export type Period = "1D" | "1W" | "1M" | "3M" | "1Y" | "MAX";

/**
 * A type for the market snapshot
 * This is used to store the market snapshot for the markets response
 * A market snapshot is a single market at a given time
 */
export interface MarketSnapshot {
  symbol: string;
  name: string;
  region: string;
  currency: string;
  timezone: string;
  level: number | null;
  daily_return_pct: number | null;
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
  period: Period;
  currency: string;
  points: PricePoint[];
  fetched_at: string;
  error: string | null;
}

export const PERIODS: Period[] = ["1D", "1W", "1M", "3M", "1Y", "MAX"];

export const DEFAULT_SYMBOL = "^GSPC";
