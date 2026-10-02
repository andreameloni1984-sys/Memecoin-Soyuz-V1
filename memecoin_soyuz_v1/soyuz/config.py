import os

def _get_bool(name: str, default: str = "0") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}

PAPER_ONLY = _get_bool("PAPER_ONLY", "1")
LIVE_TRADING_ENABLED = _get_bool("LIVE_TRADING_ENABLED", "0")
ENTRY_USD = float(os.getenv("ENTRY_USD", "25"))
ENTRY_SOL = float(os.getenv("ENTRY_SOL", "0.01"))
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "300"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "3"))
TRENDING_LIMIT = int(os.getenv("TRENDING_LIMIT", "20"))
MIN_LIQUIDITY_USD = float(os.getenv("MIN_LIQUIDITY_USD", "20000"))
MIN_SMART_WALLETS = int(os.getenv("MIN_SMART_WALLETS", "1"))
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "30"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "15"))
GMGN_WALLET_ADDRESS = os.getenv("GMGN_WALLET_ADDRESS", "").strip()
TOKEN_LIST = [t.strip() for t in os.getenv("TOKEN_LIST", "").split(",") if t.strip()]
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

if ENTRY_USD <= 0 or ENTRY_SOL <= 0:
    raise ValueError("ENTRY_USD and ENTRY_SOL must be greater than 0.")
if SCAN_INTERVAL_SECONDS < 30:
    raise ValueError("SCAN_INTERVAL_SECONDS must be at least 30 seconds.")
if MAX_OPEN_POSITIONS < 1 or TRENDING_LIMIT < 1:
    raise ValueError("MAX_OPEN_POSITIONS and TRENDING_LIMIT must be at least 1.")
if MIN_LIQUIDITY_USD < 0 or MIN_SMART_WALLETS < 0:
    raise ValueError("Risk filters cannot be negative.")
if not (0 < STOP_LOSS_PCT < TAKE_PROFIT_PCT):
    raise ValueError("Require 0 < STOP_LOSS_PCT < TAKE_PROFIT_PCT.")
if LIVE_TRADING_ENABLED and PAPER_ONLY:
    raise RuntimeError("LIVE_TRADING_ENABLED=1 requires PAPER_ONLY=0.")
