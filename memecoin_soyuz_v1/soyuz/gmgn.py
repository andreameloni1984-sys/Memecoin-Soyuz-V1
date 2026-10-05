from dataclasses import asdict
from typing import Any
import json
import urllib.error
import urllib.parse
import urllib.request

from .models import TokenSnapshot


class DexScreenerReadOnlySource:
    """Public read-only market-data adapter used by Soyuz paper mode."""

    BASE_URL = "https://api.dexscreener.com/latest/dex/tokens/"
    PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"

    def discover_tokens(self, limit: int = 20) -> list[str]:
        """Discover recent Solana token addresses using a read-only public feed."""
        request = urllib.request.Request(
            self.PROFILES_URL,
            headers={"User-Agent": "Memecoin-Soyuz-V1/1.0"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                if response.status != 200:
                    raise RuntimeError("DexScreener HTTP " + str(response.status))
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise RuntimeError("DexScreener discovery failed: " + str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("DexScreener discovery returned invalid JSON.") from exc

        result = []
        seen = set()
        for item in payload if isinstance(payload, list) else []:
            if item.get("chainId") != "solana":
                continue
            address = str(item.get("tokenAddress") or "").strip()
            if address and address not in seen:
                seen.add(address)
                result.append(address)
            if len(result) >= max(1, limit):
                break
        return result

    def get_token(self, address: str) -> dict[str, Any]:
        address = address.strip()
        if not address:
            raise ValueError("Token address cannot be empty.")

        url = self.BASE_URL + urllib.parse.quote(address, safe="")
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Memecoin-Soyuz-V1/1.0"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                if response.status != 200:
                    raise RuntimeError(f"DexScreener HTTP {response.status}")
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise RuntimeError(f"DexScreener request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("DexScreener returned invalid JSON.") from exc

        pairs = [p for p in payload.get("pairs", []) if p.get("chainId") == "solana"]
        if not pairs:
            raise RuntimeError("No Solana pair found for token.")

        pair = max(
            pairs,
            key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0),
        )
        txns = (pair.get("txns") or {}).get("m5") or {}
        volume = (pair.get("volume") or {}).get("m5") or 0
        change = (pair.get("priceChange") or {}).get("m5") or 0
        liquidity = (pair.get("liquidity") or {}).get("usd") or 0
        fdv = pair.get("fdv") or pair.get("marketCap") or 0
        base = pair.get("baseToken") or {}

        return {
            "address": address,
            "symbol": base.get("symbol") or "UNKNOWN",
            "chain": "solana",
            "price_usd": float(pair.get("priceUsd") or 0),
            "liquidity_usd": float(liquidity),
            "market_cap_usd": float(fdv),
            "volume_5m_usd": float(volume),
            "buys_5m": int(txns.get("buys") or 0),
            "sells_5m": int(txns.get("sells") or 0),
            "price_change_5m_pct": float(change),
            "source": "dexscreener",
        }


class GMGNReadOnlyClient:
    """Read-only adapter. V1 never signs or sends blockchain transactions."""

    def __init__(self, source: Any = None):
        self.source = source

    @property
    def available(self) -> bool:
        return self.source is not None

    def get_token_snapshot(self, address: str) -> TokenSnapshot:
        if not address.strip():
            raise ValueError("Token address cannot be empty.")
        if self.source is None:
            raise RuntimeError("Read-only market data source is not configured.")

        data = self.source.get_token(address)
        if not isinstance(data, dict):
            raise TypeError("Market data source must return a dictionary.")
        return self._snapshot_from_dict(data)

    @staticmethod
    def _snapshot_from_dict(data: dict[str, Any]) -> TokenSnapshot:
        allowed = set(TokenSnapshot.__dataclass_fields__.keys())
        normalized = {key: value for key, value in data.items() if key in allowed}
        if "address" not in normalized:
            raise ValueError("Token data must contain an address.")
        normalized.setdefault("symbol", "UNKNOWN")
        return TokenSnapshot(**normalized)

    @staticmethod
    def snapshot_to_dict(snapshot: TokenSnapshot) -> dict[str, Any]:
        return asdict(snapshot)
