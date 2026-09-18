"""Live trading: places REAL orders with REAL money via the exchange API.

Disabled by default. To enable you must:
  1. Set BOT_API_KEY and BOT_API_SECRET (exchange API credentials, trade-only permissions).
  2. Set BOT_LIVE_CONFIRM=I_UNDERSTAND_THE_RISK to explicitly acknowledge the risk.
Both are required; missing either raises RuntimeError before any order can be placed.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from .config import Config
from .data import fetch_ohlcv, get_exchange
from .strategy import Signal, generate_signals


def _require_confirmation(config: Config) -> None:
    if not config.api_key or not config.api_secret:
        raise RuntimeError(
            "Live trading requires BOT_API_KEY and BOT_API_SECRET to be set."
        )
    if not config.live_trading_confirmed:
        raise RuntimeError(
            "Live trading requires BOT_LIVE_CONFIRM=I_UNDERSTAND_THE_RISK. "
            "This will place real orders with real money. Test with backtest/paper "
            "trading first."
        )


def _check_min_notional(exchange, symbol: str, capital: float) -> None:
    market = exchange.market(symbol)
    min_cost = (market.get("limits", {}).get("cost", {}) or {}).get("min")
    if min_cost and capital < min_cost:
        raise RuntimeError(
            f"Capital ({capital}) is below the exchange's minimum order size "
            f"({min_cost}) for {symbol}. Trades would be rejected."
        )


def run_live_trader(config: Config, iterations: int | None = None) -> None:
    _require_confirmation(config)

    exchange = get_exchange(config.exchange_id)
    exchange.apiKey = config.api_key
    exchange.secret = config.api_secret
    exchange.load_markets()
    _check_min_notional(exchange, config.symbol, config.initial_capital * config.position_fraction)

    print(f"[LIVE] Trading {config.symbol} with REAL funds. Ctrl+C to stop.")

    position_amount = 0.0
    count = 0
    last_candle_ts = None

    while iterations is None or count < iterations:
        candles = fetch_ohlcv(exchange, config.symbol, config.timeframe,
                               limit=max(config.slow_period + 5, 50))
        closes = [c[4] for c in candles]
        signals = generate_signals(closes, config.fast_period, config.slow_period)
        latest_ts = candles[-1][0]
        latest_signal = signals[-1]

        if latest_ts != last_candle_ts:
            last_candle_ts = latest_ts
            balance = exchange.fetch_balance()
            base, quote = config.symbol.split("/")

            if latest_signal == Signal.BUY and position_amount == 0.0:
                quote_free = balance.get(quote, {}).get("free", 0.0)
                spend = quote_free * config.position_fraction
                order = exchange.create_market_buy_order(config.symbol, None, {"cost": spend}) \
                    if exchange.has.get("createMarketOrderWithCost") \
                    else exchange.create_market_buy_order(config.symbol, spend / closes[-1])
                position_amount = order.get("filled") or order.get("amount") or 0.0
                print(f"[LIVE] BUY order placed: {order}")

            elif latest_signal == Signal.SELL and position_amount > 0.0:
                base_free = balance.get(base, {}).get("free", 0.0)
                order = exchange.create_market_sell_order(config.symbol, base_free)
                position_amount = 0.0
                print(f"[LIVE] SELL order placed: {order}")

        print(f"[LIVE] {datetime.now(timezone.utc).isoformat()} signal={latest_signal.value} "
              f"position={position_amount}")

        count += 1
        if iterations is None or count < iterations:
            time.sleep(config.poll_interval_seconds)
