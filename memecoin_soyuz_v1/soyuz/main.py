import time

from .config import ENTRY_USD, LIVE_TRADING_ENABLED, STOP_LOSS_PCT, TAKE_PROFIT_PCT, TOKEN_LIST, TRENDING_LIMIT
from .live_trader import run_live_cycle
from .gmgn import DexScreenerReadOnlySource, GMGNReadOnlyClient
from .scoring import build_signal
from .telegram import format_no_trade_message, format_signal_message, send_message

def select_best_signal(signals):
    """Return exactly one BUY_PAPER candidate, or None."""
    eligible = [s for s in signals if s.decision == "BUY_PAPER"]
    if not eligible:
        return None
    return max(eligible, key=lambda s: (s.total_score, s.execution_score, s.safety_score, s.opportunity_score))


def run_paper_once() -> int:
    print("MEMECOIN SOYUZ V1")
    print("PAPER ONLY")
    client = GMGNReadOnlyClient(source=DexScreenerReadOnlySource())
    addresses = list(TOKEN_LIST)
    if not addresses:
        try:
            addresses = client.source.discover_tokens(TRENDING_LIMIT)
            print("Auto-discovered " + str(len(addresses)) + " Solana candidates.")
        except Exception as exc:
            message = format_no_trade_message("Automatic discovery failed: " + str(exc))
            print(message)
            send_message(message)
            return 0
    if not addresses:
        message = format_no_trade_message("No Solana candidates discovered.")
        print(message)
        send_message(message)
        return 0
    signals = []
    for address in addresses:
        try:
            snapshot = client.get_token_snapshot(address.strip())
            signal = build_signal(snapshot, paper_entry_usd=ENTRY_USD,
                                   take_profit_pct=TAKE_PROFIT_PCT,
                                   stop_loss_pct=STOP_LOSS_PCT)
            signals.append(signal)
        except Exception as exc:
            print(f"Unable to analyse {address}: {exc}")
    selected = select_best_signal(signals)
    if selected is None:
        message = format_no_trade_message("No token passed all Soyuz BUY_PAPER gates.")
    else:
        message = format_signal_message(selected)
    print(message)
    send_message(message)
    return len(signals)

def main() -> None:
    if LIVE_TRADING_ENABLED:
        raise RuntimeError("Live trading is intentionally disabled. Keep LIVE_TRADING_ENABLED=0.")
    run_paper_once()

if __name__ == "__main__":
    main()
