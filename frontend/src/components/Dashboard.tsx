"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getMarketComparison, getMarketHistory, getMarkets } from "@/lib/api";
import { formatTimestamp, formatUpdatedAgo, quoteNoun } from "@/lib/format";
import type {
  ComparisonResponse,
  ComparisonView,
  MarketHistoryResponse,
  MarketSnapshot,
  Period,
} from "@/types/market";
import {
  COMPARISON_PERIODS,
  DEFAULT_BASE_CURRENCY,
  DEFAULT_COMPARE_SYMBOLS,
  DEFAULT_SYMBOL,
  LOCAL_VIEW,
  MARKET_POLL_SECONDS,
  MAX_COMPARISON_SYMBOLS,
} from "@/types/market";

import { ComparisonChart } from "./ComparisonChart";
import { CompareTray } from "./CompareTray";
import { MarketChart } from "./MarketChart";
import { MarketTable } from "./MarketTable";
import { PeriodSelector } from "./PeriodSelector";
import { PerspectiveSelector } from "./PerspectiveSelector";

export function Dashboard() {
  const [markets, setMarkets] = useState<MarketSnapshot[]>([]);
  const [fetchedAt, setFetchedAt] = useState<string | null>(null);
  const [marketsLoading, setMarketsLoading] = useState(true);
  const [marketsError, setMarketsError] = useState<string | null>(null);

  const [selectedSymbol, setSelectedSymbol] = useState(DEFAULT_SYMBOL);
  const [period, setPeriod] = useState<Period>("1M");
  const [history, setHistory] = useState<MarketHistoryResponse | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Comparison chart state (scoped to this section, not a global UI setting)
  const [comparePeriod, setComparePeriod] = useState<Period>("3M");
  // "LOCAL" (FX-free) or a base currency (investor view); default USD
  const [compareView, setCompareView] = useState<ComparisonView>(DEFAULT_BASE_CURRENCY);
  // Markets explicitly ticked for comparison (starts with the core indices)
  const [compareSymbols, setCompareSymbols] = useState<string[]>(DEFAULT_COMPARE_SYMBOLS);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);

  // Map the single UI selection onto the API's perspective + base currency
  const perspective = compareView === LOCAL_VIEW ? "local" : "base";
  const baseCurrency = compareView === LOCAL_VIEW ? DEFAULT_BASE_CURRENCY : compareView;

  /**
   * Toggle a market in/out of the comparison set, capped at MAX_COMPARISON_SYMBOLS
   */
  const toggleCompare = useCallback((symbol: string) => {
    setCompareSymbols((current) => {
      if (current.includes(symbol)) {
        return current.filter((item) => item !== symbol);
      }
      if (current.length >= MAX_COMPARISON_SYMBOLS) {
        return current;
      }
      return [...current, symbol];
    });
  }, []);

  // Auto-refresh UI: countdown to next poll, and seconds since last successful update
  const [secondsUntilRefresh, setSecondsUntilRefresh] = useState(MARKET_POLL_SECONDS);
  const [secondsSinceUpdate, setSecondsSinceUpdate] = useState(0);
  const refreshInFlight = useRef(false);

  /**
   * Reset the auto-refresh countdown after a successful snapshot fetch
   */
  const markQuotesFresh = useCallback(() => {
    setSecondsUntilRefresh(MARKET_POLL_SECONDS);
    setSecondsSinceUpdate(0);
  }, []);

  /**
   * A function to load the markets.
   * silent=true is used by auto-refresh so the table does not flash a loading state.
   */
  const loadMarkets = useCallback(
    async (silent = false) => {
      if (refreshInFlight.current) {
        return;
      }
      refreshInFlight.current = true;

      if (!silent) {
        setMarketsLoading(true);
      }
      setMarketsError(null);

      try {
        const response = await getMarkets();
        setMarkets(response.markets);
        setFetchedAt(response.fetched_at);
        markQuotesFresh();
      } catch (error) {
        setMarketsError(error instanceof Error ? error.message : "Failed to load markets");
        // Still reset the countdown so a failed poll does not retry in a tight loop
        setSecondsUntilRefresh(MARKET_POLL_SECONDS);
      } finally {
        refreshInFlight.current = false;
        if (!silent) {
          setMarketsLoading(false);
        }
      }
    },
    [markQuotesFresh],
  );

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

  useEffect(() => {
    void loadMarkets();
  }, [loadMarkets]);

  useEffect(() => {
    void loadHistory(selectedSymbol, period);
  }, [selectedSymbol, period, loadHistory]);

  /**
   * Load the rebase comparison for the ticked markets, selected period, and perspective.
   * "local" rebases each in its own currency; a currency converts via FX first.
   */
  useEffect(() => {
    // Nothing ticked: clear the chart and skip the request
    if (compareSymbols.length === 0) {
      setComparison(null);
      setComparisonLoading(false);
      return;
    }

    let cancelled = false;
    setComparisonLoading(true);
    void getMarketComparison(comparePeriod, baseCurrency, perspective, compareSymbols)
      .then((response) => {
        if (!cancelled) {
          setComparison(response);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setComparison({
            base_currency: baseCurrency,
            perspective,
            period: comparePeriod,
            series: [],
            fetched_at: new Date().toISOString(),
            error: error instanceof Error ? error.message : "Failed to load comparison",
          });
        }
      })
      .finally(() => {
        if (!cancelled) {
          setComparisonLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [comparePeriod, baseCurrency, perspective, compareSymbols]);

  /**
   * Tick once per second: advance "updated X ago" and the refresh countdown.
   * Skip while the tab is hidden so we do not hammer Yahoo in the background.
   */
  useEffect(() => {
    const id = window.setInterval(() => {
      if (typeof document !== "undefined" && document.hidden) {
        return;
      }
      setSecondsSinceUpdate((seconds) => seconds + 1);
      setSecondsUntilRefresh((seconds) => Math.max(0, seconds - 1));
    }, 1000);

    return () => window.clearInterval(id);
  }, []);

  /**
   * When the countdown reaches zero, poll the markets snapshot endpoint again.
   * Also refresh the 1D chart so intraday history stays current.
   */
  useEffect(() => {
    if (secondsUntilRefresh > 0) {
      return;
    }
    if (typeof document !== "undefined" && document.hidden) {
      return;
    }
    if (refreshInFlight.current) {
      return;
    }

    void loadMarkets(true);
    if (period === "1D") {
      void loadHistory(selectedSymbol, period, true);
    }
  }, [secondsUntilRefresh, loadMarkets, loadHistory, selectedSymbol, period]);

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
            Delayed last quotes (index levels and stock prices). Session status uses regular
            exchange hours and does not include public holidays. Quotes auto-refresh every{" "}
            {MARKET_POLL_SECONDS}s.
          </p>
        </div>
        <div className="flex flex-col items-stretch gap-1 sm:items-end">
          <button
            type="button"
            onClick={() => void loadMarkets()}
            disabled={marketsLoading}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-200 transition-colors hover:bg-zinc-800 disabled:opacity-50"
          >
            {marketsLoading ? "Refreshing…" : "Refresh"}
          </button>
          {fetchedAt && (
            <p className="text-xs text-zinc-500">
              Updated {formatUpdatedAgo(secondsSinceUpdate)} · Next refresh in{" "}
              {secondsUntilRefresh}s
            </p>
          )}
        </div>
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
          compareSymbols={compareSymbols}
          onToggleCompare={toggleCompare}
        />
      )}

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-medium text-zinc-100">
              {selectedMarket?.name ?? "Price history"}
            </h2>
            <p className="text-sm text-zinc-500">
              {selectedMarket?.symbol ?? selectedSymbol} · Current{" "}
              {selectedMarket ? quoteNoun(selectedMarket.kind).toLowerCase() : "level"}
              {selectedMarket
                ? ` · ${selectedMarket.is_open ? "Open" : "Closed"} · ${selectedMarket.session_note}`
                : ""}
            </p>
          </div>
          <PeriodSelector value={period} onChange={setPeriod} />
        </div>
        <MarketChart history={history} loading={historyLoading} />
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-medium text-zinc-100">Compare markets</h2>
            <p className="mt-1 max-w-2xl text-sm text-zinc-500">
              Tick markets in the table to compare them, rebased to 100 so performance lines up.{" "}
              {compareView === LOCAL_VIEW
                ? "Local view rebases each market in its own currency (no FX)."
                : `${baseCurrency} view converts each into ${baseCurrency} first, so lines include FX moves.`}{" "}
              The single-asset chart above stays in native prices.
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:items-end">
            <PeriodSelector
              value={comparePeriod}
              onChange={setComparePeriod}
              periods={COMPARISON_PERIODS}
            />
            <PerspectiveSelector value={compareView} onChange={setCompareView} />
          </div>
        </div>
        <CompareTray
          symbols={compareSymbols}
          markets={markets}
          onRemove={toggleCompare}
          onClear={() => setCompareSymbols([])}
        />
        {compareSymbols.length === 0 ? (
          <div className="flex h-80 items-center justify-center rounded-xl border border-dashed border-zinc-800 bg-zinc-900/40 text-sm text-zinc-500">
            Tick markets in the table above to compare them here.
          </div>
        ) : (
          <ComparisonChart comparison={comparison} loading={comparisonLoading} />
        )}
      </section>

      {fetchedAt && (
        <p className="text-center text-xs text-zinc-500">
          Last snapshot {formatTimestamp(fetchedAt)}. Auto-refresh every {MARKET_POLL_SECONDS}s
          (countdown in the header). Manual Refresh still available. Data via Yahoo Finance
          (delayed).
        </p>
      )}
    </div>
  );
}
