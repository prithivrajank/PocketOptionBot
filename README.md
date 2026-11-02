# Pocket Option AI Analyzer

A read-only market analysis starter project intended for deployment on Render.

## Current features

- FastAPI service
- Health endpoint at `/health`
- Status endpoint at `/api/status`
- API documentation at `/docs`
- Explicit read-only posture; no order placement or trade execution

## Local setup (Windows)

```cmd
py -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Open:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## Deploy to Render

1. In Render, choose **New +** → **Blueprint** or **Web Service**.
2. Connect this GitHub repository.
3. For a Blueprint deployment, Render reads `render.yaml`.
4. For a manual Web Service, use:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Health check path: `/health`

The free web service may sleep when idle; it is not suitable for guaranteed uninterrupted real-time WebSocket processing.

## Security and market-data notes

- Do not commit broker SSIDs, cookies, authorization headers, or Telegram tokens.
- Store any required secrets only in Render Environment Variables.
- This starter does not connect to Pocket Option yet. A supported, authorized, read-only market-data source must be verified before adding an adapter.
- Signal analysis is probabilistic and does not guarantee outcomes.
- No automatic trading is implemented.
