"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ComparisonResponse } from "@/types/market";
import { colorForSymbol } from "@/types/market";
import { formatReturn, returnColor } from "@/lib/format";

interface ComparisonChartProps {
  comparison: ComparisonResponse | null;
  loading: boolean;
}

/**
 * Format comparison chart dates (daily series; always include year on long ranges)
 */
function formatAxisDate(value: string, period: string): string {
  const date = new Date(value);
  if (period === "1M") {
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "2-digit" });
  }
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

function formatTooltipDate(value: string): string {
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/**
 * Multi-asset chart: each series is FX-converted into the base currency, then rebased to 100.
 * Also shows local vs base-currency window returns for each asset.
 */
export function ComparisonChart({ comparison, loading }: ComparisonChartProps) {
  if (loading) {
    return (
      <div className="flex h-80 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/40 text-sm text-zinc-400">
        Loading comparison…
      </div>
    );
  }

  if (!comparison) {
    return (
      <div className="flex h-80 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/40 text-sm text-zinc-400">
        Comparison data will appear here.
      </div>
    );
  }

  if (comparison.error) {
    return (
      <div className="flex h-80 items-center justify-center rounded-xl border border-amber-900/50 bg-amber-950/20 px-6 text-center text-sm text-amber-300">
        {comparison.error}
      </div>
    );
  }

  // Local view has no FX, so there is no base-currency return column to show
  const isLocal = comparison.perspective === "local";
  const activeSeries = comparison.series.filter((series) => series.points.length > 0);
  if (activeSeries.length === 0) {
    return (
      <div className="flex h-80 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/40 text-sm text-zinc-400">
        No comparable history for this period and base currency.
      </div>
    );
  }

  // Merge timestamps across series for a multi-line Recharts dataset
  const byTime = new Map<string, Record<string, number | string>>();
  for (const series of activeSeries) {
    for (const point of series.points) {
      const row = byTime.get(point.timestamp) ?? { timestamp: point.timestamp };
      row[series.symbol] = point.rebased;
      byTime.set(point.timestamp, row);
    }
  }
  const data = Array.from(byTime.values()).sort((a, b) =>
    String(a.timestamp).localeCompare(String(b.timestamp)),
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="h-80 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(value) => formatAxisDate(String(value), comparison.period)}
              stroke="#71717a"
              fontSize={12}
              minTickGap={28}
            />
            <YAxis
              domain={["auto", "auto"]}
              stroke="#71717a"
              fontSize={12}
              width={48}
              tickFormatter={(value: number) => value.toFixed(0)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#18181b",
                border: "1px solid #3f3f46",
                borderRadius: "8px",
              }}
              labelFormatter={(value) => formatTooltipDate(String(value))}
              formatter={(value, name) => [Number(value).toFixed(2), String(name)]}
            />
            <Legend />
            {activeSeries.map((series, index) => (
              <Line
                key={series.symbol}
                type="monotone"
                dataKey={series.symbol}
                name={series.name}
                stroke={colorForSymbol(series.symbol, index)}
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/40">
        <table className="w-full min-w-[520px] text-left text-sm">
          <thead className="border-b border-zinc-800 text-xs uppercase tracking-wide text-zinc-400">
            <tr>
              <th className="px-4 py-3 font-medium">Market</th>
              <th className="px-4 py-3 font-medium text-right">Native</th>
              <th className="px-4 py-3 font-medium text-right">Local return</th>
              {!isLocal && (
                <th className="px-4 py-3 font-medium text-right">
                  {comparison.base_currency} return
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {comparison.series.map((series) => (
              <tr key={series.symbol} className="border-b border-zinc-800/80 last:border-0">
                <td className="px-4 py-3 text-zinc-100">
                  {series.name}
                  {series.error && (
                    <div className="text-xs text-amber-400">{series.error}</div>
                  )}
                </td>
                <td className="px-4 py-3 text-right text-zinc-400">{series.native_currency}</td>
                <td className={`px-4 py-3 text-right font-mono ${returnColor(series.local_return_pct)}`}>
                  {formatReturn(series.local_return_pct)}
                </td>
                {!isLocal && (
                  <td className={`px-4 py-3 text-right font-mono ${returnColor(series.base_return_pct)}`}>
                    {formatReturn(series.base_return_pct)}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
