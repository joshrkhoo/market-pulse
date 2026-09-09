"use client";

import type { ComparisonView } from "@/types/market";
import { BASE_CURRENCIES, LOCAL_VIEW } from "@/types/market";

interface PerspectiveSelectorProps {
  value: ComparisonView;
  onChange: (view: ComparisonView) => void;
}

// "Local" rebases each asset in its own currency; the others convert into that base currency first
const VIEWS: { id: ComparisonView; label: string }[] = [
  { id: LOCAL_VIEW, label: "Local" },
  ...BASE_CURRENCIES.map((currency) => ({ id: currency, label: currency })),
];

/**
 * Return-perspective picker for the comparison chart only (not a global dashboard setting).
 * "Local" = FX-free (each series in its own currency); a currency = investor view after FX.
 */
export function PerspectiveSelector({ value, onChange }: PerspectiveSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {VIEWS.map((view) => {
        const isActive = view.id === value;
        return (
          <button
            key={view.id}
            type="button"
            onClick={() => onChange(view.id)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              isActive
                ? "bg-sky-500 text-white"
                : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
            }`}
          >
            {view.label}
          </button>
        );
      })}
    </div>
  );
}
