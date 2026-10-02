from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

from .config import (
    ENTRY_SOL, MAX_OPEN_POSITIONS, MIN_LIQUIDITY_USD, MIN_SMART_WALLETS,
    TAKE_PROFIT_PCT, STOP_LOSS_PCT, TRENDING_LIMIT, LIVE_TRADING_ENABLED,
    GMGN_WALLET_ADDRESS,
)
from .models import TokenSnapshot
from .scoring import build_signal

SOL_MINT = "So11111111111111111111111111111111111111112"


def _unwrap(payload: Any) -> Any:
    if isinstance(payload, dict):
        if "data" in payload:
            return payload["data"]
        if "result" in payload:
            return payload["result"]
    return payload


def _records(payload: Any) -> list[dict[str, Any]]:
    payload = _unwrap(payload)
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("list", "tokens", "coins", "rank", "rows", "items", "holdings"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    found = []
    for value in payload.values():
        if isinstance(value, dict):
            found.extend(_records(value))
        elif isinstance(value, list):
            found.extend(x for x in value if isinstance(x, dict))
    return found


def _token(payload: Any) -> dict[str, Any]:
    payload = _unwrap(payload)
    if isinstance(payload, dict):
        if "address" in payload or "symbol" in payload:
            return payload
        for key in ("token", "coin", "token_info"):
            value = payload.get(key)
            if isinstance(value, dict):
                return value
    raise RuntimeError("GMGN token response did not contain token data.")


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _boolish(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class GMGNCLI:
    def __init__(self) -> None:
        if shutil.which("gmgn-cli") is None:
            raise RuntimeError(
                "gmgn-cli is not installed. Install it with: npm install -g gmgn-cli"
            )

    def run(self, *args: str) -> Any:
        result = subprocess.run(
            ["gmgn-cli", *args, "--raw"],
            check=False,
            capture_output=True,
            text=True,
            timeout=45,
            env=os.environ.copy(),
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(f"gmgn-cli failed ({result.returncode}): {detail[-1200:]}")
        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError as exc:
            raise RuntimeError("gmgn-cli did not return valid JSON.") from exc

    def trending(self) -> list[dict[str, Any]]:
        return _records(self.run(
            "market", "trending", "--chain", "sol", "--interval", "5m",
            "--order-by", "volume", "--limit", str(TRENDING_LIMIT),
            "--filter", "not_risk", "--filter", "not_honeypot",
        ))

    def token_info(self, address: str) -> dict[str, Any]:
        return _token(self.run("token", "info", "--chain", "sol", "--address", address))

    def token_security(self, address: str) -> dict[str, Any]:
        payload = _unwrap(self.run("token", "security", "--chain", "sol", "--address", address))
        if isinstance(payload, dict):
            if "security" in payload and isinstance(payload["security"], dict):
                return payload["security"]
            return payload
        raise RuntimeError("GMGN security response did not contain an object.")

    def holdings(self) -> list[dict[str, Any]]:
        return _records(self.run(
            "portfolio", "holdings", "--chain", "sol", "--wallet", GMGN_WALLET_ADDRESS
        ))

    def buy(self, address: str) -> Any:
        conditions = json.dumps([
            {"order_type": "profit_stop", "side": "sell",
             "price_scale": str(TAKE_PROFIT_PCT), "sell_ratio": "100"},
            {"order_type": "loss_stop", "side": "sell",
             "price_scale": str(STOP_LOSS_PCT), "sell_ratio": "100"},
        ], separators=(",", ":"))
        return self.run(
            "cooking", "--chain", "sol", "--from", GMGN_WALLET_ADDRESS,
            "--input-token", SOL_MINT, "--output-token", address,
            "--amount", str(int(ENTRY_SOL * 1_000_000_000)),
            "--auto-slippage", "--anti-mev",
            "--condition-orders", conditions, "--sell-ratio-type", "hold_amount",
            "--yes",
        )

    def sell_all(self, address: str) -> Any:
        return self.run(
            "swap", "--chain", "sol", "--from", GMGN_WALLET_ADDRESS,
            "--input-token", address, "--output-token", SOL_MINT,
            "--percent", "100", "--auto-slippage", "--anti-mev", "--yes",
        )


def snapshot_from_gmgn(info: dict[str, Any], security: dict[str, Any]) -> TokenSnapshot:
    price = info.get("price") or {}
    stat = info.get("stat") or {}
    tags = info.get("wallet_tags_stat") or {}
    price_now = _num(price.get("price"))
    price_5m = _num(price.get("price_5m"))
    change_5m = ((price_now / price_5m) - 1) * 100 if price_5m > 0 else 0.0
    buys = int(_num(price.get("buys_5m")))
    sells = int(_num(price.get("sells_5m")))
    volume = _num(price.get("volume_5m"))
    if volume <= 0:
        volume = _num(price.get("buy_volume_5m")) + _num(price.get("sell_volume_5m"))
    top10 = _num(security.get("top_10_holder_rate"), _num(stat.get("top_10_holder_rate")))
    dev_pct = _num(security.get("dev_team_hold_rate"), _num(stat.get("dev_team_hold_rate")))
    insider = _num(security.get("suspected_insider_hold_rate"))
    bundle = _num(security.get("bundler_trader_amount_rate"))
    smart_wallets = int(_num(tags.get("smart_wallets")))
    return TokenSnapshot(
        address=str(info.get("address") or ""),
        symbol=str(info.get("symbol") or "UNKNOWN"),
        chain="solana",
        price_usd=price_now,
        liquidity_usd=_num(info.get("liquidity")),
        market_cap_usd=price_now * _num(info.get("circulating_supply")),
        volume_5m_usd=volume,
        buys_5m=buys,
        sells_5m=sells,
        price_change_5m_pct=change_5m,
        holders=int(_num(info.get("holder_count"))),
        top10_pct=top10 * 100,
        dev_pct=dev_pct * 100,
        insider_pct=insider * 100,
        bundle_pct=bundle * 100,
        mint_authority_active=not _boolish(security.get("renounced_mint"), False),
        freeze_authority_active=not _boolish(security.get("renounced_freeze_account"), False),
        honeypot=str(security.get("is_honeypot", "")).lower() == "yes",
        smart_money_buys=smart_wallets if _num(price.get("buy_volume_5m")) >= _num(price.get("sell_volume_5m")) else 0,
        smart_money_sells=smart_wallets if _num(price.get("sell_volume_5m")) > _num(price.get("buy_volume_5m")) else 0,
        smart_money_quality=min(100.0, smart_wallets * 15.0),
        source="gmgn-cli",
    )


def run_live_cycle() -> int:
    if not LIVE_TRADING_ENABLED:
        print("LIVE_TRADING_ENABLED=0 — no real orders.")
        return 0
    if not GMGN_WALLET_ADDRESS:
        raise RuntimeError("GMGN_WALLET_ADDRESS is required for live trading.")
    if not (0 < STOP_LOSS_PCT < TAKE_PROFIT_PCT):
        raise RuntimeError("Require 0 < STOP_LOSS_PCT < TAKE_PROFIT_PCT.")

    os.environ["GMGN_ALLOW_AUTOMATED_TRADES"] = "1"
    cli = GMGNCLI()
    holdings = cli.holdings()
    held = {
        str(h.get("address") or h.get("token_address") or "").strip()
        for h in holdings
        if h.get("address") or h.get("token_address")
    }
    held.discard("")
    print("LIVE GMGN | positions:", len(held))

    exits = 0
    for address in list(held):
        try:
            info = cli.token_info(address)
            security = cli.token_security(address)
            snap = snapshot_from_gmgn(info, security)
            rug = _num(security.get("rug_ratio"))
            creator_status = str(security.get("creator_token_status") or "").lower()
            if snap.price_change_5m_pct <= -10 or rug >= 0.30 or creator_status == "creator_close":
                print(f"SELL {snap.symbol} — emergency exit gate")
                cli.sell_all(address)
                exits += 1
        except Exception as exc:
            print(f"Exit check failed for {address}: {exc}")

    slots = max(0, MAX_OPEN_POSITIONS - (len(held) - exits))
    bought = 0
    for candidate in cli.trending():
        if bought >= slots:
            break
        address = str(candidate.get("address") or candidate.get("token_address") or "").strip()
        if not address or address in held:
            continue
        try:
            info = cli.token_info(address)
            security = cli.token_security(address)
            snap = snapshot_from_gmgn(info, security)
            smart = int(_num((info.get("wallet_tags_stat") or {}).get("smart_wallets")))
            rug = _num(security.get("rug_ratio"))
            top10 = _num(security.get("top_10_holder_rate"))
            creator_status = str(security.get("creator_token_status") or "").lower()
            mint_ok = _boolish(security.get("renounced_mint"), False)
            freeze_ok = _boolish(security.get("renounced_freeze_account"), False)
            open_source = str(security.get("open_source") or "").lower()
            owner_renounced = str(security.get("owner_renounced") or "").lower()
            hard_stop = (
                rug > 0.30
                or top10 > 0.50
                or creator_status == "creator_hold"
                or not mint_ok
                or not freeze_ok
                or open_source == "no"
                or owner_renounced == "no"
            )
            if hard_stop:
                continue
            if snap.liquidity_usd < MIN_LIQUIDITY_USD or smart < MIN_SMART_WALLETS:
                continue
            signal = build_signal(snap, paper_entry_usd=0)
            print(f"{signal.symbol} score={signal.total_score:.1f}")
            if signal.decision != "BUY_PAPER":
                continue
            print(f"BUY {signal.symbol}: {ENTRY_SOL} SOL | TP {TAKE_PROFIT_PCT}% | SL {STOP_LOSS_PCT}%")
            result = cli.buy(address)
            print(f"GMGN order submitted: {result}")
            bought += 1
            held.add(address)
        except Exception as exc:
            print(f"Candidate {address} skipped: {exc}")
    return bought + exits
