# MEMECOIN SOYUZ V1 — PAPER ONLY

V1 is deliberately non-custodial and paper-only.

The bot evaluates Solana memecoin data, applies safety filters, calculates opportunity and execution scores, and generates paper-trading signals.

## Architecture

GMGN
↓
Token data
↓
Security filter
↓
Momentum
↓
Smart Money
↓
Social / Narrative
↓
Scoring
↓
Entry / Exit
↓
Paper Trading
↓
Telegram

## IMPORTANT

This version does NOT execute real trades.

No private wallet key is required.

No automatic purchase is performed.

## Initial decision rules

- Honeypot → SKIP
- Safety Score < 60 → SKIP
- Execution Score < 50 → SKIP
- Total Score >= 72 → BUY_PAPER
- Total Score 60–71.99 → WATCH
- Total Score < 60 → SKIP

These thresholds are experimental parameters and do not guarantee profitability.

## Testing

Run:

```bash
pytest -q