"""Paper trading: runs the strategy against live market data with a simulated wallet.
No real orders are ever placed by this module.
"""
from __future__ import annotations

import csv
import json
import os
import time
from datetime import datetime, timezone

from .config import Config
from .data import fetch_ohlcv, get_exchange
from .strategy import Signal, generate_signals


def _load_state(state_file: str, initial_capital: float) -> dict:
    if os.path.exists(state_file):
        with open(state_file) as f:
            return json.load(f)
    return {"cash": initial_capital, "position_amount": 0.0, "entry_price": 0.0}


def _save_state(state_file: str, state: dict) -> None:
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def _log_trade(log_file: str, row: dict) -> None:
    file_exists = os.path.exists(log_file)
    with open(log_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "side", "price", "amount", "fee", "cash_after"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def run_paper_trader(config: Config, iterations: int | None = None) -> None:
    """Polls the exchange, evaluates the strategy on each new candle, and simulates trades.

    iterations: number of polling cycles to run; None means run forever (until interrupted).
    """
    exchange = get_exchange(config.exchange_id)
    state = _load_state(config.state_file, config.initial_capital)

    print(f"[paper] Starting with cash={state['cash']:.4f}, position={state['position_amount']:.6f} "
          f"on {config.symbol} ({config.timeframe})")

    count = 0
    last_candle_ts = None

    while iterations is None or count < iterations:
        candles = fetch_ohlcv(exchange, config.symbol, config.timeframe,
                               limit=max(config.slow_period + 5, 50))
        closes = [c[4] for c in candles]
        signals = generate_signals(closes, config.fast_period, config.slow_period)

        latest_ts = candles[-1][0]
        latest_price = closes[-1]
        latest_signal = signals[-1]

        if latest_ts != last_candle_ts:
            last_candle_ts = latest_ts
            _apply_signal(config, state, latest_signal, latest_price, latest_ts)
            _save_state(config.state_file, state)

        equity = state["cash"] + state["position_amount"] * latest_price
        print(f"[paper] {datetime.now(timezone.utc).isoformat()} price={latest_price:.2f} "
              f"signal={latest_signal.value} cash={state['cash']:.4f} "
              f"position={state['position_amount']:.6f} equity={equity:.4f}")

        count += 1
        if iterations is None or count < iterations:
            time.sleep(config.poll_interval_seconds)


def _apply_signal(config: Config, state: dict, signal: Signal, price: float, ts: int) -> None:
    if signal == Signal.BUY and state["position_amount"] == 0.0:
        spend = state["cash"] * config.position_fraction
        fee = spend * config.fee_rate
        state["position_amount"] = (spend - fee) / price
        state["entry_price"] = price
        state["cash"] -= spend
        _log_trade(config.log_file, {
            "timestamp": ts, "side": "buy", "price": price,
            "amount": state["position_amount"], "fee": fee, "cash_after": state["cash"],
        })
    elif signal == Signal.SELL and state["position_amount"] > 0.0:
        proceeds = state["position_amount"] * price
        fee = proceeds * config.fee_rate
        state["cash"] += proceeds - fee
        _log_trade(config.log_file, {
            "timestamp": ts, "side": "sell", "price": price,
            "amount": state["position_amount"], "fee": fee, "cash_after": state["cash"],
        })
        state["position_amount"] = 0.0
        state["entry_price"] = 0.0
