"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MarketHistoryResponse } from "@/types/market";
import { formatLevel, quoteNoun } from "@/lib/format";

/* 
A component to display the chart of a market
*/
interface MarketChartProps {
  history: MarketHistoryResponse | null;
  loading: boolean;
}

/* 
Format a chart timestamp for the x-axis.
Longer ranges include the year so labels stay meaningful (e.g. MAX history).
*/
function formatAxisDate(value: string, period: string): string {
  const date = new Date(value);
  if (period === "1D") {
    return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
  }
  if (period === "1W" || period === "1M") {
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "2-digit" });
  }
  // 3M / 1Y / MAX: prefer month + year so decades of history stay readable
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

/* 
Format a chart timestamp for the tooltip (more detail than the axis).
Always includes the year outside of 1D.
*/
function formatTooltipDate(value: string, period: string): string {
  const date = new Date(value);
  if (period === "1D") {
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/* 
A component to display the chart of a market
*/
export function MarketChart({ history, loading }: MarketChartProps) {
  if (loading) {
    return (
      <div className="flex h-80 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/40 text-sm text-zinc-400">
        Loading chart…
      </div>
    );
  }

  if (!history) {
    return (
      <div className="flex h-80 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/40 text-sm text-zinc-400">
        Select a market to view its history.
      </div>
    );
  }

  if (history.error) {
    return (
      <div className="flex h-80 items-center justify-center rounded-xl border border-amber-900/50 bg-amber-950/20 px-6 text-center text-sm text-amber-300">
        {history.error}
      </div>
    );
  }

  if (history.points.length === 0) {
    return (
      <div className="flex h-80 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/40 text-sm text-zinc-400">
        No historical data available for this period.
      </div>
    );
  }

  const data = history.points.map((point) => ({
    timestamp: point.timestamp,
    close: point.close,
  }));

  return (
    <div className="h-80 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => formatAxisDate(value, history.period)}
            stroke="#71717a"
            fontSize={12}
            minTickGap={24}
          />
          <YAxis
            domain={["auto", "auto"]}
            tickFormatter={(value: number) => formatLevel(value)}
            stroke="#71717a"
            fontSize={12}
            width={72}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              border: "1px solid #3f3f46",
              borderRadius: "8px",
            }}
            labelFormatter={(value) => formatTooltipDate(String(value), history.period)}
            formatter={(value) => [formatLevel(Number(value)), quoteNoun(history.kind)]}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#38bdf8"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
