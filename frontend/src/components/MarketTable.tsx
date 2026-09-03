"use client";

import type { MarketSnapshot } from "@/types/market";
import { formatLevel, formatReturn, formatTimestamp, returnColor } from "@/lib/format";

interface MarketTableProps {
  markets: MarketSnapshot[];
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}

export function MarketTable({ markets, selectedSymbol, onSelect }: MarketTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/60">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-zinc-800 bg-zinc-900 text-xs uppercase tracking-wide text-zinc-400">
          <tr>
            <th className="px-4 py-3 font-medium">Market</th>
            <th className="px-4 py-3 font-medium text-right">Level</th>
            <th className="px-4 py-3 font-medium text-right">Daily</th>
            <th className="hidden px-4 py-3 font-medium text-right md:table-cell">Updated</th>
          </tr>
        </thead>
        <tbody>
          {markets.map((market) => {
            const isSelected = market.symbol === selectedSymbol;
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
                  <div className="text-xs text-zinc-500">{market.region}</div>
                  {market.error && (
                    <div className="mt-1 text-xs text-amber-400">{market.error}</div>
                  )}
                </td>
                <td className="px-4 py-3 text-right font-mono text-zinc-100">
                  {formatLevel(market.level)}
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
