"use client";

import { useCallback, useEffect, useState } from "react";

import { getMarketHistory, getMarketSnapshot, getMarkets } from "@/lib/api";
import { formatTimestamp, quoteNoun } from "@/lib/format";
import type { MarketHistoryResponse, MarketSnapshot, Period } from "@/types/market";
import { DEFAULT_SYMBOL, MARKET_POLL_MS } from "@/types/market";

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
   * A function to load the markets.
   * silent=true is used by auto-refresh so the table does not flash a loading state.
   */
  const loadMarkets = useCallback(async (silent = false) => {
    if (!silent) {
      setMarketsLoading(true);
    }
    setMarketsError(null);

    try {
      const response = await getMarkets();
      setMarkets(response.markets);
      setFetchedAt(response.fetched_at);
    } catch (error) {
      setMarketsError(error instanceof Error ? error.message : "Failed to load markets");
    } finally {
      if (!silent) {
        setMarketsLoading(false);
      }
    }
  }, []);

  /**
   * A function to load the history.
   * A history is a list of price points. silent=true skips the chart loading placeholder.
   */
  const loadHistory = useCallback(
    async (symbol: string, selectedPeriod: Period, silent = false) => {
      if (!silent) {
        setHistoryLoading(true);
      }
      try {
        const response = await getMarketHistory(symbol, selectedPeriod);
        setHistory(response);
      } catch (error) {
        setHistory({
          symbol,
          name: symbol,
          kind: "index",
          period: selectedPeriod,
          currency: "",
          points: [],
          fetched_at: new Date().toISOString(),
          error: error instanceof Error ? error.message : "Failed to load history",
        });
      } finally {
        if (!silent) {
          setHistoryLoading(false);
        }
      }
    },
    [],
  );

  /**
   * Refresh one ticker's current level/price without reloading the whole table
   */
  const refreshTicker = useCallback(async (symbol: string) => {
    try {
      const snapshot = await getMarketSnapshot(symbol);
      setMarkets((current) =>
        current.map((market) => (market.symbol === symbol ? snapshot : market)),
      );
    } catch {
      // Keep the existing row if a single ticker refresh fails
    }
  }, []);

  useEffect(() => {
    void loadMarkets();
  }, [loadMarkets]);

  useEffect(() => {
    void loadHistory(selectedSymbol, period);
  }, [selectedSymbol, period, loadHistory]);

  const selectedMarket = markets.find((market) => market.symbol === selectedSymbol);
  const anyOpen = markets.some((market) => market.is_open);
  const tickerSymbols = markets.map((market) => market.symbol).join("|");

  /**
   * Auto-refresh each ticker's current quote on its own timer.
   * Skip while the tab is hidden. Also refresh the 1D chart so it stays current while open.
   */
  useEffect(() => {
    if (!tickerSymbols) {
      return;
    }
    const symbols = tickerSymbols.split("|");
    const timers = symbols.map((symbol, index) =>
      window.setInterval(
        () => {
          if (typeof document !== "undefined" && document.hidden) {
            return;
          }
          void refreshTicker(symbol);
          if (period === "1D" && symbol === selectedSymbol) {
            void loadHistory(selectedSymbol, period, true);
          }
        },
        MARKET_POLL_MS + index * 350,
      ),
    );
    return () => {
      timers.forEach((id) => window.clearInterval(id));
    };
  }, [tickerSymbols, refreshTicker, loadHistory, selectedSymbol, period]);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-10 sm:px-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-sky-400">
            Market Pulse
          </p>
          <h1 className="mt-1 text-3xl font-semibold text-zinc-50">Global Market Dashboard</h1>
          <p className="mt-2 max-w-2xl text-sm text-zinc-400">
            Delayed last quotes (index levels and stock prices). Session status uses regular
            exchange hours and does not include public holidays. Each ticker auto-refreshes.
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
              {selectedMarket?.symbol ?? selectedSymbol} · Current {selectedMarket ? quoteNoun(selectedMarket.kind).toLowerCase() : "level"}
              {selectedMarket
                ? ` · ${selectedMarket.is_open ? "Open" : "Closed"} · ${selectedMarket.session_note}`
                : ""}
            </p>
          </div>
          <PeriodSelector value={period} onChange={setPeriod} />
        </div>
        <MarketChart history={history} loading={historyLoading} />
      </section>

      {fetchedAt && (
        <p className="text-center text-xs text-zinc-500">
          Quotes fetched {formatTimestamp(fetchedAt)}. Each ticker auto-refreshes every 30s
          {anyOpen ? " while a market is open" : ""}
          . Data via Yahoo Finance (delayed).
        </p>
      )}
    </div>
  );
}
