import type { MarketHistoryResponse, MarketsResponse, Period } from "@/types/market";

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
Calls the /api/markets/history endpoint to get the history of a market
*/
export function getMarketHistory(symbol: string, period: Period): Promise<MarketHistoryResponse> {
  const params = new URLSearchParams({ symbol, period });
  return fetchJson<MarketHistoryResponse>(`${API_BASE}/api/markets/history?${params}`);
}
