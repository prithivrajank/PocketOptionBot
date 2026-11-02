from datetime import datetime, timezone
import json
import os
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from market_data.collector import add_candle, collector_status, get_candles

app = FastAPI(
    title="Pocket Option AI Analyzer",
    version="0.3.0",
    description="Read-only market analysis API. No trade execution."
)


class CandleIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=40)
    timeframe: int = Field(gt=0, le=86400, description="Candle duration in seconds")
    timestamp: int = Field(gt=0, description="Candle opening time, Unix seconds")
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_ohlc(self):
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be >= open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be <= open, close, and high")
        return self


@app.get("/")
def home():
    return {
        "project": "Pocket Option AI Analyzer",
        "status": "running",
        "mode": "read-only"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "time_utc": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/status")
def api_status():
    stats = collector_status()
    return {
        "connected": False,
        "live_data": False,
        "historical_data_available": stats["candles_in_memory"] > 0,
        "credentials_configured": bool(os.getenv("CANDLE_INGEST_KEY")),
        "otcharts_configured": bool(os.getenv("OTCHARTS_API_KEY")),
        "message": "Read-only OTCharts candle sync is on-demand; live streaming requires an OTCharts plan that includes streams.",
        "read_only": True,
        **stats,
    }


@app.post("/api/candles/ingest")
def ingest_candle(
    candle: CandleIn,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    expected_key = os.getenv("CANDLE_INGEST_KEY")
    if not expected_key:
        raise HTTPException(status_code=503, detail="CANDLE_INGEST_KEY is not configured.")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return add_candle(candle.model_dump())


@app.get("/api/market-data/sync")
def sync_otcharts_candles(
    symbol: str = Query(min_length=1, max_length=40),
    timeframe: int = Query(default=60, gt=0, le=86400, description="Candle duration in seconds"),
    limit: int = Query(default=100, ge=1, le=300),
):
    """Fetch one historical candle batch from OTCharts; this is not a live stream."""
    api_key = os.getenv("OTCHARTS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="OTCHARTS_API_KEY is not configured.")

    params = urlencode({
        "venue": "otc",
        "symbol": symbol,
        "tf": timeframe,
        "limit": limit,
    })
    request = Request(
        f"https://otcharts.com/v1/candles?{params}",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise HTTPException(status_code=502, detail=f"OTCharts returned HTTP {exc.code}: {detail}")
    except (URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach OTCharts: {exc}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=502, detail="OTCharts returned invalid JSON.")

    bars = payload.get("candles") if isinstance(payload, dict) else None
    if not isinstance(bars, list):
        raise HTTPException(status_code=502, detail="OTCharts response did not contain a candles list.")

    stored = 0
    for bar in bars:
        try:
            # OTCharts documents Pocket Option candle timestamps as UTC+2.
            candle = CandleIn(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=int(bar["time"]) - 7200,
                open=float(bar["open"]),
                high=float(bar["high"]),
                low=float(bar["low"]),
                close=float(bar["close"]),
            )
        except (KeyError, TypeError, ValueError):
            continue
        add_candle(candle.model_dump())
        stored += 1

    return {
        "provider": "OTCharts",
        "venue": "otc",
        "symbol": symbol,
        "timeframe": timeframe,
        "received": len(bars),
        "stored": stored,
        "live_stream": False,
        "note": "Historical candle batch only. Pocket Option timestamps were shifted from UTC+2 to UTC as documented by OTCharts.",
    }


@app.get("/api/candles")
def read_candles(
    symbol: str = Query(min_length=1, max_length=40),
    timeframe: int = Query(gt=0, le=86400, description="Candle duration in seconds"),
    limit: int = Query(default=100, ge=1, le=500),
):
    rows = get_candles(symbol, timeframe, limit)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(rows),
        "candles": rows,
    }
