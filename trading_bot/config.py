"""Bot configuration. Edit these values or override via environment variables."""
import os
from dataclasses import dataclass


@dataclass
class Config:
    exchange_id: str = os.environ.get("BOT_EXCHANGE", "binance")
    symbol: str = os.environ.get("BOT_SYMBOL", "BTC/USDT")
    # 1h reduces the noise-driven crossovers a 15m timeframe produces.
    timeframe: str = os.environ.get("BOT_TIMEFRAME", "1h")

    # SMA crossover strategy
    fast_period: int = int(os.environ.get("BOT_FAST_PERIOD", 20))
    slow_period: int = int(os.environ.get("BOT_SLOW_PERIOD", 50))
    # Minimum fast/slow gap (as a fraction of price) before a crossover counts,
    # to filter out chatter around the crossing point.
    min_gap_pct: float = float(os.environ.get("BOT_MIN_GAP_PCT", 0.002))

    # Capital & risk
    initial_capital: float = float(os.environ.get("BOT_CAPITAL", 25.0))
    fee_rate: float = float(os.environ.get("BOT_FEE_RATE", 0.001))  # 0.1% taker fee, typical for Binance
    position_fraction: float = float(os.environ.get("BOT_POSITION_FRACTION", 1.0))  # fraction of capital per trade

    # Paper/live trading
    poll_interval_seconds: int = int(os.environ.get("BOT_POLL_SECONDS", 60))
    state_file: str = os.environ.get("BOT_STATE_FILE", "paper_state.json")
    log_file: str = os.environ.get("BOT_LOG_FILE", "trades.csv")

    # Live trading requires explicit opt-in on top of API keys being set.
    live_trading_confirmed: bool = os.environ.get("BOT_LIVE_CONFIRM") == "I_UNDERSTAND_THE_RISK"
    api_key: str = os.environ.get("BOT_API_KEY", "")
    api_secret: str = os.environ.get("BOT_API_SECRET", "")
