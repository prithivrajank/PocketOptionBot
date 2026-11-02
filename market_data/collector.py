"""Validated, read-only OHLC candle buffer.

This module stores normalized candles received from a separately verified data
adapter. It does not log in to Pocket Option or place trades.
"""
from collections import defaultdict, deque
from threading import Lock
from typing import Deque

_STORE: dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=2000))
_LOCK = Lock()


def add_candle(candle: dict) -> dict:
    key = f"{candle['symbol']}:{candle['timeframe']}"
    with _LOCK:
        rows = _STORE[key]
        # Replace an existing candle with the same opening timestamp.
        for index, existing in enumerate(rows):
            if existing["timestamp"] == candle["timestamp"]:
                rows[index] = candle
                break
        else:
            rows.append(candle)
        return {"stored": True, "count": len(rows), "key": key}


def get_candles(symbol: str, timeframe: int, limit: int = 100) -> list[dict]:
    key = f"{symbol}:{timeframe}"
    with _LOCK:
        rows = list(_STORE.get(key, ()))
    return rows[-limit:]


def collector_status() -> dict:
    with _LOCK:
        return {
            "symbols": sorted(_STORE.keys()),
            "candles_in_memory": sum(len(rows) for rows in _STORE.values()),
        }
