/**
 * A function to format the level
 * This is used to format the level for the market snapshot
 * A level for an index is the equivalent to a single price of a stock at a given time
 */
export function formatLevel(value: number | null): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * A function to format the return
 * This is used to format the return for the market snapshot
 * A return is the daily return percentage of an index
 */
export function formatReturn(value: number | null): string {
  if (value === null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * A function to format the timestamp
 * This is used to format the timestamp for the market snapshot
 * A timestamp is the date and time of the market snapshot
 */
export function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(new Date(value));
}

/**
 * A function to format the return color
 * This is used to format the return color for the market snapshot
 * A return color is the color of the return for the market snapshot
 */
export function returnColor(value: number | null): string {
  if (value === null) return "text-zinc-400";
  if (value > 0) return "text-emerald-400";
  if (value < 0) return "text-rose-400";
  return "text-zinc-300";
}
