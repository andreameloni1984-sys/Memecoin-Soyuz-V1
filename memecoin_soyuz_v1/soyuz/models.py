from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass
class TokenSnapshot:
    """
    Snapshot dei dati disponibili per un token Solana.

    Tutti i punteggi vengono calcolati successivamente dal motore
    di scoring. Questo oggetto contiene solamente i dati osservati.
    """

    address: str
    symbol: str
    chain: str = "solana"

    # Market data
    price_usd: float = 0.0
    liquidity_usd: float = 0.0
    market_cap_usd: float = 0.0
    volume_5m_usd: float = 0.0

    # Trading activity
    buys_5m: int = 0
    sells_5m: int = 0
    price_change_5m_pct: float = 0.0

    # Holder / concentration data
    holders: int = 0
    top10_pct: float = 0.0
    dev_pct: float = 0.0
    insider_pct: float = 0.0
    bundle_pct: float = 0.0

    # Token security
    mint_authority_active: bool = False
    freeze_authority_active: bool = False
    permanent_delegate: bool = False
    transfer_hook: bool = False
    transfer_fee_bps: int = 0
    honeypot: bool = False

    # Smart Money
    smart_money_buys: int = 0
    smart_money_sells: int = 0
    smart_money_quality: float = 0.0

    # Social / narrative
    social_velocity: float = 0.0

    # Execution
    execution_slippage_pct: float = 0.0

    # Source / timestamp
    source: str = "unknown"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        """Convert the snapshot to a normal dictionary."""
        return asdict(self)


@dataclass
class Signal:
    """
    Decision produced by the Soyuz scoring engine.
    """

    address: str
    symbol: str

    decision: str

    safety_score: float
    opportunity_score: float
    execution_score: float
    total_score: float

    reasons: list[str] = field(default_factory=list)

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Paper-trading information only.
    paper_entry_usd: float = 0.0
    entry_price_usd: float = 0.0
    take_profit_price_usd: float = 0.0
    stop_loss_price_usd: float = 0.0

    def to_dict(self) -> dict:
        """Convert the signal to a normal dictionary."""
        return asdict(self)