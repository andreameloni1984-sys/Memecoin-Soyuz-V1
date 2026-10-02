from dataclasses import asdict
from typing import Any

from .models import TokenSnapshot


class GMGNReadOnlyClient:
    """
    Read-only adapter for GMGN data.

    V1 deliberately does not contain trading or wallet-signing logic.

    The actual GMGN data transport will be connected separately after
    the exact supported interface has been verified.
    """

    def __init__(self, source: Any = None):
        self.source = source

    @property
    def available(self) -> bool:
        """Return whether a read-only data source has been configured."""
        return self.source is not None

    def get_token_snapshot(self, address: str) -> TokenSnapshot:
        """
        Retrieve a token snapshot from the configured read-only source.

        This method intentionally fails closed until a verified GMGN
        data interface is configured.
        """

        if not address.strip():
            raise ValueError("Token address cannot be empty.")

        if self.source is None:
            raise RuntimeError(
                "GMGN read-only source is not configured yet."
            )

        data = self.source.get_token(address)

        if not isinstance(data, dict):
            raise TypeError(
                "GMGN source must return a dictionary."
            )

        return self._snapshot_from_dict(data)

    @staticmethod
    def _snapshot_from_dict(data: dict[str, Any]) -> TokenSnapshot:
        """
        Convert normalized source data into a TokenSnapshot.

        Unknown fields are ignored deliberately.
        """

        allowed = set(TokenSnapshot.__dataclass_fields__.keys())

        normalized = {
            key: value
            for key, value in data.items()
            if key in allowed
        }

        if "address" not in normalized:
            raise ValueError(
                "Token data must contain an address."
            )

        if "symbol" not in normalized:
            normalized["symbol"] = "UNKNOWN"

        return TokenSnapshot(**normalized)

    @staticmethod
    def snapshot_to_dict(snapshot: TokenSnapshot) -> dict[str, Any]:
        """Convert a snapshot to a plain dictionary."""

        return asdict(snapshot)