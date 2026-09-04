# Market Pulse

A global market dashboard that tracks major equity indices and selected stocks using Yahoo Finance data.

## Dashboard features

What the UI shows today:

- **Overview table** for each ticker: market name, region, open/closed badge, **Current** (level for indexes, price for stocks), **Open**, **Close**, **Daily %**, and last **Updated** time
- **Session status** from regular exchange hours (e.g. `Closed · Opens Fri 09:30`) — lunch breaks count as closed; public holidays are not modelled
- **Automatic refreshing** every **75 seconds**, with **Updated just now / Xs ago** and **Next refresh in Ns** next to the manual **Refresh** button
- **Historical line chart** with ranges `1D`, `1W`, `1M`, `3M`, `1Y`, `MAX`
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
├── backend/app/          # FastAPI service
├── frontend/             # Next.js dashboard
├── scripts/              # CLI utilities
└── visualisation.py      # Early yfinance + matplotlib experiment
```

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

Dashboard: to be added when deployed 

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/markets` | Current quote, open, close, and daily return for all tickers |
| `GET` | `/api/markets/snapshot?symbol=^GSPC` | Current quote for one ticker |
| `GET` | `/api/markets/history?symbol=^GSPC&period=1M` | Historical close series |

Supported chart periods: `1D`, `1W`, `1M`, `3M`, `1Y`, `MAX`.

## Tests

```bash
pytest backend/tests/
```

## Notes

- Daily percentage change uses the prior **trading** close, not the prior calendar day.
- Session status uses regular weekday hours (including lunch breaks) and does not include public holidays.
- Quotes auto-refresh every **75 seconds**. The header shows “updated X ago” and a countdown to the next poll; the manual **Refresh** button still works.
- Open is the session open. Close is the last completed session close (previous close while the market is still open). When a market is closed, Current and Close are often the same.
- Indexes are quoted as a **level**; stocks are quoted as a **price**.
- Yahoo Finance data is delayed — this is not a real-time trading system.
- Index levels are not directly comparable across markets; use percentage returns for comparison.
