"use client";

import { useCallback, useEffect, useState } from "react";

import { getMarketHistory, getMarkets } from "@/lib/api";
import { formatTimestamp } from "@/lib/format";
import type { MarketHistoryResponse, MarketSnapshot, Period } from "@/types/market";
import { DEFAULT_SYMBOL } from "@/types/market";

import { MarketChart } from "./MarketChart";
import { MarketTable } from "./MarketTable";
import { PeriodSelector } from "./PeriodSelector";

export function Dashboard() {
  const [markets, setMarkets] = useState<MarketSnapshot[]>([]);
  const [fetchedAt, setFetchedAt] = useState<string | null>(null);
  const [marketsLoading, setMarketsLoading] = useState(true);
  const [marketsError, setMarketsError] = useState<string | null>(null);

  const [selectedSymbol, setSelectedSymbol] = useState(DEFAULT_SYMBOL);
  const [period, setPeriod] = useState<Period>("1M");
  const [history, setHistory] = useState<MarketHistoryResponse | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  /**
   * A function to load the markets
   */
  const loadMarkets = useCallback(async () => {
    // Change state to loading
    setMarketsLoading(true);
    setMarketsError(null);

    // Try to fetch the markets from the API
    try {
      const response = await getMarkets();
      setMarkets(response.markets);
      setFetchedAt(response.fetched_at);
      // Set the error to null
    } catch (error) {
      setMarketsError(error instanceof Error ? error.message : "Failed to load markets");
      // Set the loading to false
    } finally {
      setMarketsLoading(false);
    }
  }, []);

  /**
   * A function to load the history
   * This is used to load the history from the API
   * A history is a list of price points
   */
  const loadHistory = useCallback(async (symbol: string, selectedPeriod: Period) => {
    setHistoryLoading(true);
    // Try to fetch the history from the API
    try {
      const response = await getMarketHistory(symbol, selectedPeriod);
      setHistory(response);
    } catch (error) {
      setHistory({
        symbol,
        name: markets.find((m) => m.symbol === symbol)?.name ?? symbol,
        period: selectedPeriod,
        currency: "",
        points: [],
        fetched_at: new Date().toISOString(),
        error: error instanceof Error ? error.message : "Failed to load history",
      });
    } finally {
      setHistoryLoading(false);
    }
  }, [markets]);

  useEffect(() => {
    void loadMarkets();
  }, [loadMarkets]);

  useEffect(() => {
    void loadHistory(selectedSymbol, period);
  }, [selectedSymbol, period, loadHistory]);

  const selectedMarket = markets.find((market) => market.symbol === selectedSymbol);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-10 sm:px-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-sky-400">
            Market Pulse
          </p>
          <h1 className="mt-1 text-3xl font-semibold text-zinc-50">Global Market Dashboard</h1>
          <p className="mt-2 max-w-2xl text-sm text-zinc-400">
            Daily index levels and returns across five major equity benchmarks. Markets close at
            different times — values are not simultaneous.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadMarkets()}
          disabled={marketsLoading}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-200 transition-colors hover:bg-zinc-800 disabled:opacity-50"
        >
          {marketsLoading ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      {marketsError && (
        <div className="rounded-lg border border-rose-900/60 bg-rose-950/30 px-4 py-3 text-sm text-rose-300">
          {marketsError}
        </div>
      )}

      {marketsLoading && markets.length === 0 ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 px-4 py-10 text-center text-sm text-zinc-400">
          Loading market data…
        </div>
      ) : (
        <MarketTable
          markets={markets}
          selectedSymbol={selectedSymbol}
          onSelect={setSelectedSymbol}
        />
      )}

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-medium text-zinc-100">
              {selectedMarket?.name ?? "Price history"}
            </h2>
            <p className="text-sm text-zinc-500">
              {selectedMarket?.symbol ?? selectedSymbol} · Close price
            </p>
          </div>
          <PeriodSelector value={period} onChange={setPeriod} />
        </div>
        <MarketChart history={history} loading={historyLoading} />
      </section>

      {fetchedAt && (
        <p className="text-center text-xs text-zinc-500">
          Snapshot fetched {formatTimestamp(fetchedAt)}. Data via Yahoo Finance (delayed).
        </p>
      )}
    </div>
  );
}
