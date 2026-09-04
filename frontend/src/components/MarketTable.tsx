"use client";

import type { MarketSnapshot } from "@/types/market";
import { formatLevel, formatReturn, formatTimestamp, quoteNoun, returnColor } from "@/lib/format";

interface MarketTableProps {
  markets: MarketSnapshot[];
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}

/**
 * Open/closed badge using regular exchange hours from the API
 */
function SessionBadge({ isOpen, note }: { isOpen: boolean; note: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium ${
        isOpen
          ? "bg-emerald-950 text-emerald-300 ring-1 ring-emerald-800"
          : "bg-zinc-800 text-zinc-400 ring-1 ring-zinc-700"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${isOpen ? "bg-emerald-400" : "bg-zinc-500"}`} />
      {isOpen ? "Open" : "Closed"}
      <span className="font-normal text-zinc-500">· {note}</span>
    </span>
  );
}

/**
 * A table of tickers. Current quotes auto-refresh with the dashboard poll cycle.
 * Indexes show a Level; stocks show a Price. Open/Close are session values.
 */
export function MarketTable({ markets, selectedSymbol, onSelect }: MarketTableProps) {
  return (
    <div className="overflow-x-auto overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/60">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b border-zinc-800 bg-zinc-900 text-xs uppercase tracking-wide text-zinc-400">
          <tr>
            <th className="px-4 py-3 font-medium">Market</th>
            <th className="px-4 py-3 font-medium text-right">Current</th>
            <th className="px-4 py-3 font-medium text-right">Open</th>
            <th className="px-4 py-3 font-medium text-right">Close</th>
            <th className="px-4 py-3 font-medium text-right">Daily</th>
            <th className="hidden px-4 py-3 font-medium text-right md:table-cell">Updated</th>
          </tr>
        </thead>
        <tbody>
          {markets.map((market) => {
            const isSelected = market.symbol === selectedSymbol;
            const noun = quoteNoun(market.kind);
            return (
              <tr
                key={market.symbol}
                onClick={() => onSelect(market.symbol)}
                className={`cursor-pointer border-b border-zinc-800/80 transition-colors last:border-0 hover:bg-zinc-800/50 ${
                  isSelected ? "bg-sky-950/40" : ""
                }`}
              >
                <td className="px-4 py-3">
                  <div className="font-medium text-zinc-100">{market.name}</div>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <span className="text-xs text-zinc-500">{market.region}</span>
                    <SessionBadge isOpen={market.is_open} note={market.session_note} />
                  </div>
                  {market.error && (
                    <div className="mt-1 text-xs text-amber-400">{market.error}</div>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="font-mono text-zinc-100">{formatLevel(market.last)}</div>
                  <div className="text-[11px] uppercase tracking-wide text-zinc-500">{noun}</div>
                </td>
                <td className="px-4 py-3 text-right font-mono text-zinc-300">
                  {formatLevel(market.open)}
                </td>
                <td className="px-4 py-3 text-right font-mono text-zinc-300">
                  {formatLevel(market.close)}
                </td>
                <td className={`px-4 py-3 text-right font-mono ${returnColor(market.daily_return_pct)}`}>
                  {formatReturn(market.daily_return_pct)}
                </td>
                <td className="hidden px-4 py-3 text-right text-xs text-zinc-500 md:table-cell">
                  {formatTimestamp(market.updated_at)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
