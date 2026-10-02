import json
import urllib.error
import urllib.request

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_message(text: str) -> bool:
    """
    Send a Telegram message.

    Returns True if Telegram accepts the request.
    Returns False when Telegram is not configured or the request fails.
    """

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    if not text.strip():
        return False

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300

    except (urllib.error.URLError, urllib.error.HTTPError):
        return False


def format_signal_message(signal) -> str:
    """Format a Soyuz signal for Telegram."""

    lines = [
        "🚀 MEMECOIN SOYUZ",
        "",
        f"🪙 {signal.symbol}",
        f"📊 Decision: {signal.decision}",
        "",
        f"🛡 Safety: {signal.safety_score:.2f}",
        f"🔥 Opportunity: {signal.opportunity_score:.2f}",
        f"⚡ Execution: {signal.execution_score:.2f}",
        f"🎯 Total: {signal.total_score:.2f}",
        "",
        "📋 Reasons:",
    ]

    for reason in signal.reasons[:8]:
        lines.append(f"• {reason}")

    if signal.decision == "BUY_PAPER":
        lines.extend(
            [
                "",
                f"💵 Paper entry: ${signal.paper_entry_usd:.2f}",
                "🧪 PAPER ONLY — NO REAL TRADE",
            ]
        )

    return "\n".join(lines)