"""Fee-aware backtest engine for the SMA crossover strategy."""
from __future__ import annotations

from dataclasses import dataclass, field

from .metrics import max_drawdown, sharpe_ratio, win_rate
from .strategy import Signal, generate_signals

TIMEFRAME_TO_PERIODS_PER_YEAR = {
    "1m": 365 * 24 * 60,
    "5m": 365 * 24 * 12,
    "15m": 365 * 24 * 4,
    "1h": 365 * 24,
    "4h": 365 * 6,
    "1d": 365,
}


@dataclass
class Trade:
    side: str  # "buy" or "sell"
    timestamp: int
    price: float
    amount: float
    fee: float
    pnl: float | None = None  # filled in on the closing trade


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    final_capital: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe: float = 0.0
    win_rate_pct: float = 0.0
    num_trades: int = 0


def run_backtest(candles: list[list[float]], fast_period: int, slow_period: int,
                  initial_capital: float, fee_rate: float, position_fraction: float = 1.0,
                  timeframe: str = "15m", min_gap_pct: float = 0.0) -> BacktestResult:
    """candles: list of [timestamp_ms, open, high, low, close, volume], oldest first."""
    closes = [c[4] for c in candles]
    timestamps = [c[0] for c in candles]
    signals = generate_signals(closes, fast_period, slow_period, min_gap_pct=min_gap_pct)

    cash = initial_capital
    position_amount = 0.0
    entry_price = 0.0
    trades: list[Trade] = []
    equity_curve: list[float] = []

    for i, price in enumerate(closes):
        signal = signals[i]

        if signal == Signal.BUY and position_amount == 0.0:
            spend = cash * position_fraction
            fee = spend * fee_rate
            position_amount = (spend - fee) / price
            entry_price = price
            cash -= spend
            trades.append(Trade("buy", timestamps[i], price, position_amount, fee))

        elif signal == Signal.SELL and position_amount > 0.0:
            proceeds = position_amount * price
            fee = proceeds * fee_rate
            cash += proceeds - fee
            pnl = (price - entry_price) * position_amount - fee - trades[-1].fee
            trades.append(Trade("sell", timestamps[i], price, position_amount, fee, pnl=pnl))
            position_amount = 0.0
            entry_price = 0.0

        mark_to_market = cash + position_amount * price
        equity_curve.append(mark_to_market)

    # Liquidate any open position at the last price so results are comparable.
    if position_amount > 0.0:
        price = closes[-1]
        proceeds = position_amount * price
        fee = proceeds * fee_rate
        cash += proceeds - fee
        pnl = (price - entry_price) * position_amount - fee - trades[-1].fee
        trades.append(Trade("sell", timestamps[-1], price, position_amount, fee, pnl=pnl))
        equity_curve[-1] = cash

    final_capital = equity_curve[-1] if equity_curve else initial_capital
    period_returns = [
        (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
        for i in range(1, len(equity_curve)) if equity_curve[i - 1] > 0
    ]
    closed_pnls = [t.pnl for t in trades if t.pnl is not None]
    periods_per_year = TIMEFRAME_TO_PERIODS_PER_YEAR.get(timeframe, 365 * 24)

    return BacktestResult(
        trades=trades,
        equity_curve=equity_curve,
        final_capital=final_capital,
        total_return_pct=(final_capital - initial_capital) / initial_capital * 100,
        max_drawdown_pct=max_drawdown(equity_curve) * 100 if equity_curve else 0.0,
        sharpe=sharpe_ratio(period_returns, periods_per_year),
        win_rate_pct=win_rate(closed_pnls) * 100,
        num_trades=len(closed_pnls),
    )
