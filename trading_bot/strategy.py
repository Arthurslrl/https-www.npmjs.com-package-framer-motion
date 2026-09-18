"""SMA crossover strategy: signal generation from OHLCV candles."""
from __future__ import annotations

from enum import Enum


class Signal(Enum):
    HOLD = "hold"
    BUY = "buy"
    SELL = "sell"


def sma(values: list[float], period: int) -> list[float | None]:
    """Simple moving average, None where there isn't enough history yet."""
    result: list[float | None] = []
    running_sum = 0.0
    for i, v in enumerate(values):
        running_sum += v
        if i >= period:
            running_sum -= values[i - period]
        result.append(running_sum / period if i >= period - 1 else None)
    return result


def generate_signals(closes: list[float], fast_period: int, slow_period: int) -> list[Signal]:
    """One signal per candle: BUY on fast crossing above slow, SELL on crossing below."""
    if fast_period >= slow_period:
        raise ValueError("fast_period must be smaller than slow_period")

    fast = sma(closes, fast_period)
    slow = sma(closes, slow_period)

    signals = [Signal.HOLD] * len(closes)
    prev_diff_sign: int | None = None

    for i in range(len(closes)):
        if fast[i] is None or slow[i] is None:
            continue
        diff = fast[i] - slow[i]
        diff_sign = 1 if diff > 0 else (-1 if diff < 0 else 0)

        if prev_diff_sign is not None and diff_sign != 0 and diff_sign != prev_diff_sign:
            signals[i] = Signal.BUY if diff_sign > 0 else Signal.SELL

        if diff_sign != 0:
            prev_diff_sign = diff_sign

    return signals
