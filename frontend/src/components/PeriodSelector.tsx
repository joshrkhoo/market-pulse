"use client";

import type { Period } from "@/types/market";
import { PERIODS } from "@/types/market";

interface PeriodSelectorProps {
  value: Period;
  onChange: (period: Period) => void;
  /** Optional subset of periods (comparison chart uses daily ranges only) */
  periods?: Period[];
}

export function PeriodSelector({ value, onChange, periods = PERIODS }: PeriodSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {periods.map((period) => {
        const isActive = period === value;
        return (
          <button
            key={period}
            type="button"
            onClick={() => onChange(period)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              isActive
                ? "bg-sky-500 text-white"
                : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
            }`}
          >
            {period}
          </button>
        );
      })}
    </div>
  );
}
