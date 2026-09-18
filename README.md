# Crypto trading bot (SMA crossover)

A small, honest trading bot: a simple moving-average crossover strategy on
crypto (via [ccxt](https://github.com/ccxt/ccxt), works with Binance, Kraken,
and 100+ other exchanges), with a backtester, a paper-trading mode (simulated
money against live prices), and an optional live-trading mode.

**Read this before running it with real money.** No strategy here is
guaranteed to be profitable. With a small starting balance (e.g. 25€), fees
and minimum order sizes matter a lot — the backtester accounts for fees so
you can see this for yourself before risking anything.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 1. Backtest (start here)

Runs the strategy over historical candles and reports return, max drawdown,
Sharpe ratio, and win rate, with fees applied.

```bash
.venv/bin/python main.py backtest --days 90
```

Tune the strategy in `trading_bot/config.py` (or via env vars — see below)
and re-run. If a configuration doesn't show a real, fee-adjusted edge over
many months of data and market conditions, it has no business running with
real money.

## 2. Paper trading (simulated money, live prices)

Polls live market data and simulates trades against a virtual wallet — no
real orders are ever placed. Trades are logged to `trades.csv`, and the
wallet state persists to `paper_state.json` so you can stop and resume.

```bash
.venv/bin/python main.py paper
```

Run this for at least a few weeks before considering live trading. A
backtest that looks good and a strategy that survives real, current market
conditions are not the same thing.

## 3. Live trading (real money — opt-in required)

`trading_bot/live_trader.py` places real orders. It is disabled unless you
explicitly set:

```bash
export BOT_API_KEY=...            # exchange API key, trade-only permissions
export BOT_API_SECRET=...
export BOT_LIVE_CONFIRM=I_UNDERSTAND_THE_RISK
.venv/bin/python main.py live
```

Use an API key scoped to trading only (never enable withdrawals). Start with
the smallest position size your exchange allows.

## Configuration

All settings live in `trading_bot/config.py` and can be overridden with
environment variables: `BOT_EXCHANGE`, `BOT_SYMBOL`, `BOT_TIMEFRAME`,
`BOT_FAST_PERIOD`, `BOT_SLOW_PERIOD`, `BOT_CAPITAL`, `BOT_FEE_RATE`,
`BOT_POSITION_FRACTION`, `BOT_POLL_SECONDS`.

## Tests

```bash
.venv/bin/pip install pytest
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -q
```

## Why there's no "live" mode running by default

A bot that starts trading a small real balance immediately, with an
unvalidated strategy, is far more likely to lose the money to fees and bad
signals than to grow it. This project is built so the risky step (real
orders) is explicit, opt-in, and only reachable after you've looked at
backtest and paper-trading results yourself.
