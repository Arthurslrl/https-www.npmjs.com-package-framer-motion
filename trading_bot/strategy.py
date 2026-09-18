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


def generate_signals(closes: list[float], fast_period: int, slow_period: int,
                      min_gap_pct: float = 0.0) -> list[Signal]:
    """One signal per candle: BUY on fast crossing above slow, SELL on crossing below.

    min_gap_pct filters noise: the fast/slow gap must reach at least this fraction
    of price before a side "counts", so a crossover that immediately wobbles back
    (common on flat/choppy price action) doesn't register as two extra trades.
    """
    if fast_period >= slow_period:
        raise ValueError("fast_period must be smaller than slow_period")

    fast = sma(closes, fast_period)
    slow = sma(closes, slow_period)

    signals = [Signal.HOLD] * len(closes)
    prev_diff_sign: int | None = None

    for i in range(len(closes)):
        if fast[i] is None or slow[i] is None or closes[i] == 0:
            continue
        diff = fast[i] - slow[i]
        gap_pct = abs(diff) / closes[i]
        if gap_pct < min_gap_pct:
            continue  # too close to call; keep waiting for a decisive move

        diff_sign = 1 if diff > 0 else -1

        if prev_diff_sign is not None and diff_sign != prev_diff_sign:
            signals[i] = Signal.BUY if diff_sign > 0 else Signal.SELL

        prev_diff_sign = diff_sign

    return signals
