"""Market data fetching via ccxt (public endpoints, no API key required)."""
from __future__ import annotations

import ccxt


def get_exchange(exchange_id: str) -> ccxt.Exchange:
    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class({"enableRateLimit": True})


def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str, timeframe: str, limit: int = 500,
                 since: int | None = None) -> list[list[float]]:
    """Returns a list of [timestamp_ms, open, high, low, close, volume]."""
    return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, since=since)


def fetch_full_history(exchange: ccxt.Exchange, symbol: str, timeframe: str,
                        since_ms: int, limit_per_call: int = 1000) -> list[list[float]]:
    """Paginate through fetch_ohlcv to build a longer history than a single call allows."""
    all_candles: list[list[float]] = []
    cursor = since_ms
    while True:
        batch = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=cursor, limit=limit_per_call)
        if not batch:
            break
        all_candles.extend(batch)
        last_ts = batch[-1][0]
        if last_ts == cursor or len(batch) < limit_per_call:
            break
        cursor = last_ts + 1
    return all_candles
