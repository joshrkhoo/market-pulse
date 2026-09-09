# Market Pulse

A global market dashboard that tracks major equity indices and selected stocks using Yahoo Finance data.

## Dashboard features

What the UI shows today:

- **Overview table** for each ticker: market name, region, open/closed badge, **Current** (level for indexes, price for stocks), **Open**, **Close**, **Daily %**, and last **Updated** time
- **Session status** from regular exchange hours (e.g. `Closed · Opens Fri 09:30`) — lunch breaks count as closed; public holidays are not modelled
- **Automatic refreshing** every **75 seconds**, with **Updated just now / Xs ago** and **Next refresh in Ns** next to the manual **Refresh** button
- **Historical line chart** with ranges `1D`, `1W`, `1M`, `3M`, `1Y`, `MAX` (native prices/levels)
- **Compare mode**: tick markets in the table (up to **6**) to plot them on one chart, rebased to 100. Clicking a row still opens its single-asset chart; the checkbox is separate
- **Return perspective** for the compare chart: **Local** rebases each market in its own currency (no FX), or pick a base currency (default **USD**) to convert via FX first. Shows **local return** vs **base-currency return** for the window
- Chart axis/tooltip dates include the **year** on longer ranges so MAX history stays readable
- Footer notes delayed Yahoo Finance data

## V1 coverage

| Market | Ticker | Region | Quote |
|---|---|---|---|
| S&P 500 | `^GSPC` | United States | Level |
| NASDAQ Composite | `^IXIC` | United States | Level |
| ASX 200 | `^AXJO` | Australia | Level |
| Hang Seng Index | `^HSI` | Hong Kong | Level |
| Nikkei 225 | `^N225` | Japan | Level |
| Microsoft | `MSFT` | United States | Price |

## Project structure

```text
market-pulse/
├── backend/app/
│   ├── main.py           # FastAPI routes + response caches
│   ├── config.py         # Instruments, periods, currencies, cache TTLs
│   ├── models.py         # Pydantic request/response models
│   ├── cache.py          # Tiny in-memory TTL cache
│   └── services/
│       ├── yfinance_client.py  # Snapshots + history from Yahoo
│       ├── market_hours.py     # Open/closed from regular session hours
│       ├── fx.py               # Fetch + cache FX rate series
│       ├── currency_convert.py # Align FX to trading dates, convert to base
│       ├── rebase.py           # Rebase a series to 100 + window return
│       └── comparison.py       # Orchestrates compare: native → FX → rebase
├── frontend/             # Next.js dashboard
├── scripts/              # CLI utilities
├── ROADMAP.md            # Deferred features / backlog
└── visualisation.py      # Early yfinance + matplotlib experiment
```

The compare pipeline is deliberately split into small services (`fx` → `currency_convert`
→ `rebase`, tied together by `comparison`) so each step is unit-testable in isolation.

## Quick start

### 1. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### 2. Snapshot script (no UI)

```bash
python scripts/fetch_snapshot.py
```

### 3. Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Live dashboard: [https://market-pulse.joshrkhoo.com/](https://market-pulse.joshrkhoo.com/)

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/markets` | Current quote, open, close, and daily return for all tickers |
| `GET` | `/api/markets/snapshot?symbol=^GSPC` | Current quote for one ticker |
| `GET` | `/api/markets/history?symbol=^GSPC&period=1M` | Historical close series (native currency) |
| `GET` | `/api/markets/compare?period=3M&perspective=base&base_currency=USD&symbols=^GSPC,^HSI` | Rebase each symbol to 100 (`perspective=local` per-currency, or `base` after FX) |

Supported single-asset chart periods: `1D`, `1W`, `1M`, `3M`, `1Y`, `MAX`.  
Comparison periods (daily): `1M`, `3M`, `1Y`, `MAX`. Perspectives: `local`, `base`. Base currencies: `USD`, `AUD`, `EUR`, `GBP`, `JPY`, `HKD`.  
Compare up to **6** symbols per request; omit `symbols` to default to the five core indices.

## How the compare chart works

**Interaction:** clicking a table row opens that market's single-asset chart (native prices).
The **checkbox** is separate — it adds/removes a market from the compare set (up to **6**).
The compare tray shows the current set as removable chips; each market keeps a **stable color**
across the table, tray, and chart legend.

**Pipeline (per market):**

1. Fetch the daily native close series from Yahoo.
2. If the perspective is **base**, fetch the FX series (`1 native = X base`), inverting the pair
   if Yahoo only quotes it the other way, and align it to the asset's trading dates — missing
   FX dates use the most recent previous rate (never filled with `0`). Same-currency assets use a
   rate of `1`. The **local** perspective skips this step entirely.
3. Convert (native × FX) when in the base perspective, then **rebase to 100** so every line
   starts at the same point and relative performance is comparable.

**Returns shown per market:**

- **Local return** — native-currency performance only (no FX).
- **Base-currency return** — includes FX; only shown in the base perspective. Conversion always
  runs *before* rebasing. Neither figure is labelled as a realised trading return.

## Caching

Responses are cached in-memory with short TTLs so the UI can poll without hammering Yahoo:

- Snapshots (`/api/markets`, `/api/markets/snapshot`): **15s**
- History (`/api/markets/history`): **60s**
- Comparison (`/api/markets/compare`): **120s** (keyed by period, perspective, base currency, symbols)
- FX rate series: **300s**

## Tests

```bash
pytest backend/tests/
```

Covers FX inversion, alignment of FX to trading dates, missing-date handling, rebasing, and the
local vs base return perspectives.

## Notes

- Daily percentage change uses the prior **trading** close, not the prior calendar day.
- Session status uses regular weekday hours (including lunch breaks) and does not include public holidays.
- Quotes auto-refresh every **75 seconds**. The header shows “updated X ago” and a countdown to the next poll; the manual **Refresh** button still works.
- Open is the session open. Close is the last completed session close (previous close while the market is still open). When a market is closed, Current and Close are often the same.
- Indexes are quoted as a **level**; stocks are quoted as a **price**.
- Yahoo Finance data is delayed — this is not a real-time trading system.
- Index levels are not directly comparable across markets; tick markets into the **compare chart** (rebased to 100) or use percentage returns.
- On the compare chart, **local return** is native-currency performance only; **base-currency return** includes FX. Conversion runs before rebasing. This is not labelled as realised return.
- The compare chart's **return perspective** and base currency are scoped to that chart (default USD). Picking **Local** hides the base-currency column and applies no FX. The single-asset chart stays in each asset’s native currency.
