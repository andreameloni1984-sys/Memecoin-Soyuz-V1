import pytest

from soyuz.paper import PaperTradingEngine


def test_open_position_reduces_cash():
    engine = PaperTradingEngine(starting_balance_usd=1000)

    position = engine.open_position(
        address="TOKEN1",
        symbol="TEST",
        price=2.0,
        amount_usd=25,
    )

    assert position.invested_usd == 25
    assert position.quantity == 12.5
    assert engine.cash_usd == 975


def test_price_update_calculates_unrealized_profit():
    engine = PaperTradingEngine(starting_balance_usd=1000)

    engine.open_position(
        address="TOKEN1",
        symbol="TEST",
        price=2.0,
        amount_usd=25,
    )

    position = engine.update_price(
        address="TOKEN1",
        price=3.0,
    )

    assert position.unrealized_pnl_usd == 12.5
    assert position.unrealized_pnl_pct == 50.0


def test_close_position_realizes_profit():
    engine = PaperTradingEngine(starting_balance_usd=1000)

    engine.open_position(
        address="TOKEN1",
        symbol="TEST",
        price=2.0,
        amount_usd=25,
    )

    position = engine.close_position(
        address="TOKEN1",
        price=3.0,
    )

    assert position.status == "CLOSED"
    assert position.realized_pnl_usd == 12.5
    assert engine.total_realized_pnl() == 12.5
    assert engine.cash_usd == 1012.5


def test_cannot_open_position_without_enough_balance():
    engine = PaperTradingEngine(starting_balance_usd=10)

    with pytest.raises(ValueError):
        engine.open_position(
            address="TOKEN1",
            symbol="TEST",
            price=1.0,
            amount_usd=25,
        )


def test_cannot_open_duplicate_position():
    engine = PaperTradingEngine(starting_balance_usd=1000)

    engine.open_position(
        address="TOKEN1",
        symbol="TEST",
        price=1.0,
        amount_usd=25,
    )

    with pytest.raises(ValueError):
        engine.open_position(
            address="TOKEN1",
            symbol="TEST",
            price=1.0,
            amount_usd=25,
        )