"use client";

import type { MarketSnapshot } from "@/types/market";
import { colorForSymbol, MAX_COMPARISON_SYMBOLS } from "@/types/market";

interface CompareTrayProps {
  /** Symbols currently in the compare set */
  symbols: string[];
  /** All markets, used to resolve symbol → display name */
  markets: MarketSnapshot[];
  onRemove: (symbol: string) => void;
  onClear: () => void;
}

/**
 * Shows the current compare set as removable chips, the count vs the cap, and Clear all.
 * Each chip carries the market's stable color so it matches the chart legend.
 */
export function CompareTray({ symbols, markets, onRemove, onClear }: CompareTrayProps) {
  const nameOf = (symbol: string) =>
    markets.find((market) => market.symbol === symbol)?.name ?? symbol;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-medium text-zinc-400">
        Comparing {symbols.length} of {MAX_COMPARISON_SYMBOLS}
      </span>

      {symbols.length === 0 ? (
        <span className="text-xs text-zinc-500">Tick markets in the table to compare.</span>
      ) : (
        <>
          {symbols.map((symbol) => (
            <span
              key={symbol}
              className="inline-flex items-center gap-1.5 rounded-full bg-zinc-800 px-2.5 py-1 text-xs text-zinc-200"
            >
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: colorForSymbol(symbol) }}
              />
              {nameOf(symbol)}
              <button
                type="button"
                onClick={() => onRemove(symbol)}
                aria-label={`Remove ${nameOf(symbol)} from comparison`}
                className="ml-0.5 text-zinc-500 transition-colors hover:text-zinc-200"
              >
                ×
              </button>
            </span>
          ))}
          <button
            type="button"
            onClick={onClear}
            className="text-xs text-zinc-500 underline-offset-2 transition-colors hover:text-zinc-300 hover:underline"
          >
            Clear all
          </button>
        </>
      )}
    </div>
  );
}
