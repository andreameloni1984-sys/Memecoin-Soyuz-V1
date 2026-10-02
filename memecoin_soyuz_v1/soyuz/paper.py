from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class PaperPosition:
    """Virtual position used by the paper-trading engine."""

    address: str
    symbol: str

    entry_price: float
    quantity: float
    invested_usd: float

    opened_at: str

    current_price: float = 0.0
    closed_at: str = ""
    exit_price: float = 0.0

    realized_pnl_usd: float = 0.0
    status: str = "OPEN"

    def update_price(self, price: float) -> None:
        """Update the current virtual market price."""

        if price <= 0:
            raise ValueError("Price must be greater than 0.")

        self.current_price = price

    @property
    def unrealized_pnl_usd(self) -> float:
        """Return the current virtual profit/loss."""

        if self.current_price <= 0:
            return 0.0

        return (self.current_price - self.entry_price) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        """Return the current virtual profit/loss percentage."""

        if self.invested_usd <= 0:
            return 0.0

        return (self.unrealized_pnl_usd / self.invested_usd) * 100


class PaperTradingEngine:
    """
    Virtual trading engine.

    This class NEVER sends blockchain transactions.
    It only records simulated positions and P&L.
    """

    def __init__(self, starting_balance_usd: float = 1000.0):
        if starting_balance_usd <= 0:
            raise ValueError("Starting balance must be greater than 0.")

        self.starting_balance_usd = starting_balance_usd
        self.cash_usd = starting_balance_usd
        self.positions: dict[str, PaperPosition] = {}
        self.closed_positions: list[PaperPosition] = []

    def open_position(
        self,
        address: str,
        symbol: str,
        price: float,
        amount_usd: float,
    ) -> PaperPosition:
        """
        Open a virtual long position.

        No real order is sent.
        """

        if price <= 0:
            raise ValueError("Entry price must be greater than 0.")

        if amount_usd <= 0:
            raise ValueError("Position size must be greater than 0.")

        if amount_usd > self.cash_usd:
            raise ValueError("Insufficient paper balance.")

        if address in self.positions:
            raise ValueError("A paper position for this token is already open.")

        quantity = amount_usd / price

        position = PaperPosition(
            address=address,
            symbol=symbol,
            entry_price=price,
            quantity=quantity,
            invested_usd=amount_usd,
            opened_at=datetime.now(timezone.utc).isoformat(),
            current_price=price,
        )

        self.cash_usd -= amount_usd
        self.positions[address] = position

        return position

    def update_price(
        self,
        address: str,
        price: float,
    ) -> PaperPosition:
        """Update the market price of an open virtual position."""

        position = self.positions.get(address)

        if position is None:
            raise KeyError("No open paper position for this token.")

        position.update_price(price)

        return position

    def close_position(
        self,
        address: str,
        price: float,
    ) -> PaperPosition:
        """Close a virtual position and realize its P&L."""

        if price <= 0:
            raise ValueError("Exit price must be greater than 0.")

        position = self.positions.pop(address, None)

        if position is None:
            raise KeyError("No open paper position for this token.")

        position.exit_price = price
        position.current_price = price
        position.realized_pnl_usd = (
            price - position.entry_price
        ) * position.quantity

        position.closed_at = datetime.now(timezone.utc).isoformat()
        position.status = "CLOSED"

        proceeds = position.quantity * price
        self.cash_usd += proceeds

        self.closed_positions.append(position)

        return position

    def total_equity(
        self,
        current_prices: dict[str, float] | None = None,
    ) -> float:
        """
        Calculate current paper equity.

        current_prices can contain live/mock prices for open positions.
        """

        equity = self.cash_usd

        for address, position in self.positions.items():
            price = (
                current_prices.get(address)
                if current_prices
                else position.current_price
            )

            if price is None or price <= 0:
                price = position.entry_price

            equity += position.quantity * price

        return equity

    def total_realized_pnl(self) -> float:
        """Return total realized paper P&L."""

        return sum(
            position.realized_pnl_usd
            for position in self.closed_positions
        )

    def total_return_pct(self) -> float:
        """Return total paper return relative to starting balance."""

        if self.starting_balance_usd <= 0:
            return 0.0

        return (
            (self.total_equity() - self.starting_balance_usd)
            / self.starting_balance_usd
        ) * 100