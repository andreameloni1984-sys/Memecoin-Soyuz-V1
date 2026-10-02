import os


def _get_bool(name: str, default: str = "1") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


PAPER_ONLY = _get_bool("PAPER_ONLY", "1")

ENTRY_USD = float(os.getenv("ENTRY_USD", "25"))
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "300"))

TOKEN_LIST = [
    token.strip()
    for token in os.getenv("TOKEN_LIST", "").split(",")
    if token.strip()
]

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


# ---------------------------------------------------------
# SAFETY CHECKS
# ---------------------------------------------------------

if not PAPER_ONLY:
    raise RuntimeError(
        "MEMECOIN SOYUZ V1 IS PAPER-ONLY. "
        "Set PAPER_ONLY=1."
    )

if ENTRY_USD <= 0:
    raise ValueError("ENTRY_USD must be greater than 0.")

if SCAN_INTERVAL_SECONDS < 30:
    raise ValueError(
        "SCAN_INTERVAL_SECONDS must be at least 30 seconds."
    )