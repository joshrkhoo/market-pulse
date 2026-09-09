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

/** Daily ranges used by the FX + rebase comparison chart */
export const COMPARISON_PERIODS: Period[] = ["1M", "3M", "1Y", "MAX"];

export const DEFAULT_SYMBOL = "^GSPC";

/** Default investor base currency for the comparison chart (feature-scoped, not global UI) */
export const DEFAULT_BASE_CURRENCY = "USD";

export const BASE_CURRENCIES = ["USD", "AUD", "EUR", "GBP", "JPY", "HKD"] as const;
export type BaseCurrency = (typeof BASE_CURRENCIES)[number];

/**
 * Return perspective for the comparison chart:
 * - "local": each asset rebased in its own currency (no FX)
 * - "base": convert into a base currency first, then rebase (price move + FX move)
 */
export type Perspective = "local" | "base";

/**
 * A single comparison-chart selection value: either the FX-free "LOCAL" view
 * or one investor base currency. Mapped to {perspective, base_currency} for the API.
 */
export const LOCAL_VIEW = "LOCAL" as const;
export type ComparisonView = typeof LOCAL_VIEW | BaseCurrency;

/** Compare set is capped so the multi-line chart stays readable (mirrors the backend) */
export const MAX_COMPARISON_SYMBOLS = 6;

/** Core indices pre-selected for comparison on first load */
export const DEFAULT_COMPARE_SYMBOLS = ["^GSPC", "^IXIC", "^AXJO", "^HSI", "^N225"];

/** Fallback palette for any symbol without a fixed color */
const FALLBACK_COLORS = ["#38bdf8", "#34d399", "#fbbf24", "#f472b6", "#a78bfa", "#fb7185"];

/** Stable per-symbol colors so a market keeps its color across table, tray, and chart */
export const SYMBOL_COLORS: Record<string, string> = {
  "^GSPC": "#38bdf8",
  "^IXIC": "#34d399",
  "^AXJO": "#fbbf24",
  "^HSI": "#f472b6",
  "^N225": "#a78bfa",
  MSFT: "#fb7185",
};

/**
 * Resolve a stable chart color for a symbol, falling back to a rotating palette
 */
export function colorForSymbol(symbol: string, fallbackIndex = 0): string {
  return SYMBOL_COLORS[symbol] ?? FALLBACK_COLORS[fallbackIndex % FALLBACK_COLORS.length];
}

/**
 * One rebased point on the multi-asset comparison chart
 */
export interface ComparisonPoint {
  timestamp: string;
  rebased: number;
}

/**
 * One asset in a base-currency comparison response
 */
export interface ComparisonSeries {
  symbol: string;
  name: string;
  kind: AssetKind;
  native_currency: string;
  /** Window return in native currency (no FX) */
  local_return_pct: number | null;
  /** Window return after FX into the selected base currency */
  base_return_pct: number | null;
  points: ComparisonPoint[];
  error: string | null;
}

/**
 * Multi-asset comparison: rebase each series to 100.
 * perspective="base" converts into base_currency first; "local" rebases in each native currency.
 */
export interface ComparisonResponse {
  base_currency: string;
  perspective: Perspective;
  period: Period;
  series: ComparisonSeries[];
  fetched_at: string;
  error: string | null;
}

/** Auto-refresh interval for snapshot polling (75s sits in the 60–90s range) */
export const MARKET_POLL_MS = 75_000;

/** Seconds between automatic snapshot refreshes */
export const MARKET_POLL_SECONDS = MARKET_POLL_MS / 1000;
