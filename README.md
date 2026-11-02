# Pocket Option AI Analyzer

A read-only market analysis API intended for Render deployment.

## Current endpoints

- `GET /` — service information
- `GET /health` — health check
- `GET /api/status` — collector status
- `POST /api/candles/ingest` — accept one normalized OHLC candle from a trusted adapter
- `GET /api/candles?symbol=EURUSD_otc&timeframe=60&limit=100` — read stored candles
- `GET /docs` — interactive API docs

## Important: data-source status

The repository does **not** yet contain a verified Pocket Option WebSocket/API adapter. The ingest endpoint is only a secured receiver for normalized candle data; it does not fetch data from Pocket Option by itself. We must inspect and validate the actual authorized read-only data feed and its message format before implementing that adapter. Do not guess broker endpoints or copy session cookies into source code.

## Render setup

Add this Environment Variable in Render:

- Key: `CANDLE_INGEST_KEY`
- Value: a long random secret generated privately by you

The key is required to call the ingest endpoint. Do not commit it to GitHub or send it in chat.

The current candle buffer is in memory and resets when the free service restarts or sleeps. It is suitable for initial integration tests, not permanent history. A persistent database can be added later.

## Local setup (Windows)

```cmd
py -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

## Safety

- Read-only analysis only; no order placement.
- Never commit broker SSIDs, cookies, authorization headers, or Telegram tokens.
- Signals are estimates and cannot guarantee trading outcomes.
- Render Free services can sleep when idle and cannot guarantee uninterrupted real-time collection.
