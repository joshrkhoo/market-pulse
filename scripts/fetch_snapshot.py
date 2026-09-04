#!/usr/bin/env python3
"""Fetch and print a snapshot table for configured indices and stocks."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as: python scripts/fetch_snapshot.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.services.yfinance_client import fetch_all_snapshots


def main() -> None:
    snapshots = fetch_all_snapshots()
    fetched_at = datetime.now(timezone.utc).isoformat()

    print(f"{'Market':<20} {'Kind':<8} {'Current':>12} {'Open':>12} {'Close':>12} {'Daily %':>10}")
    print("-" * 78)

    for market in snapshots:
        current = f"{market.last:,.2f}" if market.last is not None else "N/A"
        session_open = f"{market.open:,.2f}" if market.open is not None else "N/A"
        session_close = f"{market.close:,.2f}" if market.close is not None else "N/A"
        daily = (
            f"{market.daily_return_pct:+.2f}%"
            if market.daily_return_pct is not None
            else "N/A"
        )
        suffix = f"  [error: {market.error}]" if market.error else ""
        print(
            f"{market.name:<20} {market.kind:<8} {current:>12} {session_open:>12} {session_close:>12} {daily:>10}{suffix}"
        )

    print()
    print(json.dumps({"fetched_at": fetched_at, "markets": [m.model_dump() for m in snapshots]}, indent=2, default=str))


if __name__ == "__main__":
    main()
