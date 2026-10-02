import time

from .config import LIVE_TRADING_ENABLED, SCAN_INTERVAL_SECONDS, ENTRY_USD, TOKEN_LIST
from .live_trader import run_live_cycle
from .gmgn import DexScreenerReadOnlySource, GMGNReadOnlyClient
from .scoring import build_signal
from .telegram import format_signal_message, send_message

def run_paper_once() -> int:
    print("MEMECOIN SOYUZ V1")
    print("PAPER ONLY")
    if not TOKEN_LIST:
        print("TOKEN_LIST is empty.")
        return 0
    client = GMGNReadOnlyClient(source=DexScreenerReadOnlySource())
    processed = 0
    for address in TOKEN_LIST:
        try:
            snapshot = client.get_token_snapshot(address.strip())
            signal = build_signal(snapshot, paper_entry_usd=ENTRY_USD)
            print(f"{signal.symbol} | {signal.decision} | Score {signal.total_score:.2f}")
            send_message(format_signal_message(signal))
            processed += 1
        except Exception as exc:
            print(f"Unable to analyse {address}: {exc}")
    return processed

def main() -> None:
    if not LIVE_TRADING_ENABLED:
        run_paper_once()
        return
    print("LIVE MODE ENABLED — GMGN orders can be real on-chain trades.")
    while True:
        try:
            run_live_cycle()
        except KeyboardInterrupt:
            print("Soyuz stopped.")
            return
        except Exception as exc:
            print(f"Live cycle failed: {exc}")
        time.sleep(SCAN_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
