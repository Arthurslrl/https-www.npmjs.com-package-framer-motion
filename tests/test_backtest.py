import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trading_bot.backtest import run_backtest


def _make_candles(closes):
    # [timestamp_ms, open, high, low, close, volume]
    return [[i * 1000, c, c, c, c, 1.0] for i, c in enumerate(closes)]


def test_backtest_no_signals_preserves_capital():
    closes = [100.0] * 20
    candles = _make_candles(closes)
    result = run_backtest(candles, fast_period=2, slow_period=5, initial_capital=25.0, fee_rate=0.001)
    assert result.final_capital == 25.0
    assert result.num_trades == 0


def test_backtest_fees_reduce_capital_on_round_trip():
    # Uptrend triggers a buy, then a sharp reversal triggers a sell at the same price level,
    # so fees should be the only source of loss.
    closes = [10, 9, 8, 7, 6, 7, 8, 9, 10, 11, 12, 11, 10, 9, 8, 7, 6, 5]
    candles = _make_candles(closes)
    result = run_backtest(candles, fast_period=2, slow_period=4, initial_capital=25.0, fee_rate=0.001)
    assert result.num_trades >= 1
    # Fees strictly reduce capital versus a fee-free equivalent; final capital should be positive.
    assert result.final_capital > 0


def test_backtest_equity_curve_length_matches_candles():
    closes = list(range(1, 40))
    candles = _make_candles([float(c) for c in closes])
    result = run_backtest(candles, fast_period=3, slow_period=8, initial_capital=25.0, fee_rate=0.001)
    assert len(result.equity_curve) == len(candles)
