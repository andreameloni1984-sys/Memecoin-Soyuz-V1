from .config import ENTRY_USD, TOKEN_LIST
from .gmgn import GMGNReadOnlyClient
from .scoring import build_signal
from .telegram import format_signal_message, send_message


def run_once() -> int:
    """
    Run one complete read-only analysis cycle.

    No real trades are executed.
    """

    print("🚀 MEMECOIN SOYUZ V1")
    print("🧪 PAPER ONLY")
    print()

    if not TOKEN_LIST:
        print("⚠️ TOKEN_LIST is empty.")
        print("Add one or more Solana token addresses to .env.")
        return 0

    client = GMGNReadOnlyClient(source=__import__("soyuz.gmgn", fromlist=["DexScreenerReadOnlySource"]).DexScreenerReadOnlySource())

    processed = 0

    for address in TOKEN_LIST:
        address = address.strip()

        if not address:
            continue

        print(f"🔎 Analysing {address}...")

        try:
            snapshot = client.get_token_snapshot(address)

            signal = build_signal(
                snapshot,
                paper_entry_usd=ENTRY_USD,
            )

            print(
                f"🪙 {signal.symbol} | "
                f"{signal.decision} | "
                f"Score {signal.total_score:.2f}"
            )

            print(
                f"🛡 Safety={signal.safety_score:.2f} | "
                f"🔥 Opportunity={signal.opportunity_score:.2f} | "
                f"⚡ Execution={signal.execution_score:.2f}"
            )

            if signal.decision == "BUY_PAPER":
                print(
                    f"💵 PAPER ENTRY: ${signal.paper_entry_usd:.2f}"
                )

            telegram_message = format_signal_message(signal)
            send_message(telegram_message)

            processed += 1

        except Exception as exc:
            print(
                f"❌ Unable to analyse {address}: {exc}"
            )

    print()
    print(f"✅ Analysis complete. Tokens processed: {processed}")

    return processed


def main() -> None:
    run_once()


if __name__ == "__main__":
    main()