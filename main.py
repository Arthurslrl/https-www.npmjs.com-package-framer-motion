"""CLI entrypoint for the trading bot.

Usage:
  python main.py backtest --days 90
  python main.py paper [--iterations N]
  python main.py live [--iterations N]     # requires explicit opt-in, see live_trader.py
"""
from __future__ import annotations

import argparse
import time

from trading_bot.backtest import run_backtest
from trading_bot.config import Config
from trading_bot.data import fetch_full_history, get_exchange
from trading_bot.paper_trader import run_paper_trader


def cmd_backtest(config: Config, days: int) -> None:
    exchange = get_exchange(config.exchange_id)
    since_ms = exchange.milliseconds() - days * 24 * 60 * 60 * 1000
    print(f"Fetching {days}d of {config.timeframe} candles for {config.symbol} from {config.exchange_id}...")
    candles = fetch_full_history(exchange, config.symbol, config.timeframe, since_ms)
    print(f"Got {len(candles)} candles.")

    result = run_backtest(
        candles=candles,
        fast_period=config.fast_period,
        slow_period=config.slow_period,
        initial_capital=config.initial_capital,
        fee_rate=config.fee_rate,
        position_fraction=config.position_fraction,
        timeframe=config.timeframe,
        min_gap_pct=config.min_gap_pct,
    )

    print("\n--- Backtest results ---")
    print(f"Initial capital:   {config.initial_capital:.2f}")
    print(f"Final capital:     {result.final_capital:.2f}")
    print(f"Total return:      {result.total_return_pct:+.2f}%")
    print(f"Max drawdown:      {result.max_drawdown_pct:.2f}%")
    print(f"Sharpe (annualized): {result.sharpe:.2f}")
    print(f"Trades closed:     {result.num_trades}")
    print(f"Win rate:          {result.win_rate_pct:.1f}%")


def cmd_paper(config: Config, iterations: int | None) -> None:
    run_paper_trader(config, iterations=iterations)


def cmd_live(config: Config, iterations: int | None) -> None:
    from trading_bot.live_trader import run_live_trader
    run_live_trader(config, iterations=iterations)


def main() -> None:
    parser = argparse.ArgumentParser(description="SMA crossover crypto trading bot")
    sub = parser.add_subparsers(dest="command", required=True)

    p_backtest = sub.add_parser("backtest", help="Backtest the strategy on historical data")
    p_backtest.add_argument("--days", type=int, default=90, help="Days of history to fetch")

    p_paper = sub.add_parser("paper", help="Run the strategy against live data with simulated money")
    p_paper.add_argument("--iterations", type=int, default=None, help="Stop after N polling cycles")

    p_live = sub.add_parser("live", help="Run the strategy with REAL money (requires opt-in)")
    p_live.add_argument("--iterations", type=int, default=None, help="Stop after N polling cycles")

    args = parser.parse_args()
    config = Config()

    if args.command == "backtest":
        cmd_backtest(config, args.days)
    elif args.command == "paper":
        cmd_paper(config, args.iterations)
    elif args.command == "live":
        cmd_live(config, args.iterations)


if __name__ == "__main__":
    main()
