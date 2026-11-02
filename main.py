from datetime import datetime, timezone
import os
import secrets

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from market_data.collector import add_candle, collector_status, get_candles

app = FastAPI(
    title="Pocket Option AI Analyzer",
    version="0.2.0",
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
        "live_data": stats["candles_in_memory"] > 0,
        "credentials_configured": bool(os.getenv("CANDLE_INGEST_KEY")),
        "message": "Waiting for a verified read-only market-data adapter to send normalized candles.",
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
        raise HTTPException(
            status_code=503,
            detail="CANDLE_INGEST_KEY is not configured in the server environment."
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return add_candle(candle.model_dump())


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
