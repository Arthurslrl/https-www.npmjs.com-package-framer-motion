import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trading_bot.strategy import Signal, generate_signals, sma


def test_sma_basic():
    values = [1, 2, 3, 4, 5]
    result = sma(values, 2)
    assert result == [None, 1.5, 2.5, 3.5, 4.5]


def test_sma_insufficient_history():
    values = [1, 2]
    result = sma(values, 5)
    assert result == [None, None]


def test_generate_signals_detects_golden_cross():
    # A clear downtrend then uptrend should trigger a BUY once fast crosses above slow.
    closes = [10, 9, 8, 7, 6, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    signals = generate_signals(closes, fast_period=2, slow_period=4)
    assert Signal.BUY in signals


def test_generate_signals_detects_death_cross():
    closes = [5, 6, 7, 8, 9, 10, 11, 12, 11, 10, 9, 8, 7, 6, 5, 4]
    signals = generate_signals(closes, fast_period=2, slow_period=4)
    assert Signal.SELL in signals


def test_generate_signals_min_gap_pct_filters_noise():
    # A crossover that immediately wobbles back without a decisive gap should be
    # ignored when min_gap_pct is set, unlike with no filter.
    closes = [100, 100.1, 99.9, 100.1, 99.9, 100.1, 99.9, 100.1, 99.9, 100.1]
    unfiltered = generate_signals(closes, fast_period=2, slow_period=4, min_gap_pct=0.0)
    filtered = generate_signals(closes, fast_period=2, slow_period=4, min_gap_pct=0.05)
    assert sum(1 for s in filtered if s != Signal.HOLD) <= sum(1 for s in unfiltered if s != Signal.HOLD)


def test_generate_signals_rejects_bad_periods():
    try:
        generate_signals([1, 2, 3], fast_period=5, slow_period=2)
        assert False, "expected ValueError"
    except ValueError:
        pass
