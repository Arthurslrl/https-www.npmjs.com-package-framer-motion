"""Performance metrics computed from an equity curve and trade list."""
from __future__ import annotations

import math


def max_drawdown(equity_curve: list[float]) -> float:
    """Returns the worst peak-to-trough drop as a positive fraction (e.g. 0.2 = -20%)."""
    peak = equity_curve[0]
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        drawdown = (peak - value) / peak if peak > 0 else 0.0
        worst = max(worst, drawdown)
    return worst


def sharpe_ratio(returns: list[float], periods_per_year: float) -> float:
    """Annualized Sharpe ratio assuming a 0% risk-free rate."""
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    return (mean / std) * math.sqrt(periods_per_year)


def win_rate(trade_pnls: list[float]) -> float:
    if not trade_pnls:
        return 0.0
    wins = sum(1 for pnl in trade_pnls if pnl > 0)
    return wins / len(trade_pnls)
