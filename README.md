# Market Pulse

A global market dashboard that tracks five major equity indices using Yahoo Finance data.

## V1 coverage

| Market | Ticker | Region |
|---|---|---|
| S&P 500 | `^GSPC` | United States |
| NASDAQ Composite | `^IXIC` | United States |
| ASX 200 | `^AXJO` | Australia |
| Hang Seng Index | `^HSI` | Hong Kong |
| Nikkei 225 | `^N225` | Japan |

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

API docs: 

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

Dashboard:

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/markets` | Latest level and daily return for all indices |
| `GET` | `/api/markets/history?symbol=^GSPC&period=1M` | Historical close prices |

Supported chart periods: `1D`, `1W`, `1M`, `3M`, `1Y`, `MAX`.

## Tests

```bash
pytest backend/tests/
```

## Notes

- Daily percentage change uses the prior **trading** close, not the prior calendar day.
- Yahoo Finance data is delayed — this is not a real-time trading system.
- Index levels are not directly comparable across markets; use percentage returns for comparison.
