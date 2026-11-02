# Pocket Option AI Analyzer

A read-only market analysis API intended for Render deployment.

## Current endpoints

- `GET /` — service information
- `GET /health` — health check
- `GET /api/status` — collector and provider configuration status
- `GET /api/market-data/sync?symbol=EURUSD_otc&timeframe=60&limit=100` — fetch one historical candle batch from OTCharts
- `POST /api/candles/ingest` — accept one normalized OHLC candle using the separate ingest key
- `GET /api/candles?symbol=EURUSD_otc&timeframe=60&limit=100` — read stored candles
- `GET /docs` — interactive API docs

## OTCharts setup

Add this Render environment variable:

- Key: `OTCHARTS_API_KEY`
- Value: your private OTCharts API key

The sync endpoint makes one request for a batch of historical candles. Example:

```text
GET /api/market-data/sync?symbol=EURUSD_otc&timeframe=60&limit=100
```

Then read the stored candles:

```text
GET /api/candles?symbol=EURUSD_otc&timeframe=60&limit=100
```

The endpoint does not expose your OTCharts key. It is an on-demand historical fetch, not continuous live data. OTCharts currently states that its free tier has a limited request allowance and does not include live streaming; live ticks require a plan that includes streams. Check your account's usage and plan before making repeated requests. Use the symbols enabled for your key.

OTCharts is an independent third-party data provider, not Pocket Option and not affiliated with it. Pocket Option OTC prices are their own quote series, not interbank prices. Validate the feed against your Demo account before relying on analysis.

## Candle ingest API

The separate `POST /api/candles/ingest` endpoint uses `CANDLE_INGEST_KEY` in the `X-API-Key` header. Do not commit either key to GitHub or send it in chat.

## Storage and limitations

The current candle buffer is in memory and resets when the Render service restarts or sleeps. It is suitable for initial integration tests, not permanent history. A persistent database can be added later.

## Local setup (Windows)

```cmd
py -m venv venv
venv\\Scripts\\activate
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

## Safety

- Read-only analysis only; no order placement.
- Never commit broker SSIDs, cookies, authorization headers, or Telegram tokens.
- Signals are estimates and cannot guarantee trading outcomes.
- Render Free services can sleep when idle and cannot guarantee uninterrupted real-time collection.
