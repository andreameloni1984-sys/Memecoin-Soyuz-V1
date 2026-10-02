# MEMECOIN SOYUZ V1 — GMGN LIVE TRADER

Soyuz has paper mode by default and a separate live GMGN execution mode.

## Live flow

GMGN trending -> token info/security -> Soyuz scoring -> BUY -> GMGN Cooking -> TP/SL -> position monitoring -> SELL

The official GMGN CLI supports market discovery, token/security data, swaps, percentage sells and strategy orders. Automated non-interactive trades require GMGN_ALLOW_AUTOMATED_TRADES=1 and --yes. Soyuz enables that only inside the live process.

## Safety

Live mode can submit irreversible on-chain transactions. Keep LIVE_TRADING_ENABLED=0 until credentials and limits are configured. Never commit GMGN_API_KEY or GMGN_PRIVATE_KEY. GMGN documents GMGN_PRIVATE_KEY as an API request-signing key, not the blockchain wallet private key.

## Live variables

PAPER_ONLY=0
LIVE_TRADING_ENABLED=1
GMGN_API_KEY=...
GMGN_PRIVATE_KEY=...
GMGN_WALLET_ADDRESS=...
ENTRY_SOL=0.01
MAX_OPEN_POSITIONS=3
TRENDING_LIMIT=20
MIN_LIQUIDITY_USD=20000
MIN_SMART_WALLETS=1
TAKE_PROFIT_PCT=30
STOP_LOSS_PCT=15
SCAN_INTERVAL_SECONDS=300

Install the official CLI with:

npm install -g gmgn-cli

Then run from memecoin_soyuz_v1:

python -m soyuz.main

With LIVE_TRADING_ENABLED=0 it stays paper-only. With live mode enabled, the bot chooses candidates and can submit buys/sells through GMGN.
