import type {
  ComparisonResponse,
  MarketHistoryResponse,
  MarketSnapshot,
  MarketsResponse,
  Period,
  Perspective,
} from "@/types/market";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}
 
/* 
Calls the /api/markets endpoint to get the list of markets
*/
export function getMarkets(): Promise<MarketsResponse> {
  return fetchJson<MarketsResponse>(`${API_BASE}/api/markets`);
}

/* 
Calls the /api/markets/snapshot endpoint to refresh one ticker's current quote
*/
export function getMarketSnapshot(symbol: string): Promise<MarketSnapshot> {
  const params = new URLSearchParams({ symbol });
  return fetchJson<MarketSnapshot>(`${API_BASE}/api/markets/snapshot?${params}`);
}

/* 
Calls the /api/markets/history endpoint to get the history of a market
*/
export function getMarketHistory(symbol: string, period: Period): Promise<MarketHistoryResponse> {
  const params = new URLSearchParams({ symbol, period });
  return fetchJson<MarketHistoryResponse>(`${API_BASE}/api/markets/history?${params}`);
}

/**
 * Calls /api/markets/compare — rebase each series to 100.
 * perspective="base" converts into baseCurrency first; "local" rebases in each native currency.
 */
export function getMarketComparison(
  period: Period,
  baseCurrency: string,
  perspective: Perspective,
  symbols?: string[],
): Promise<ComparisonResponse> {
  const params = new URLSearchParams({
    period,
    base_currency: baseCurrency,
    perspective,
  });
  if (symbols && symbols.length > 0) {
    params.set("symbols", symbols.join(","));
  }
  return fetchJson<ComparisonResponse>(`${API_BASE}/api/markets/compare?${params}`);
}
