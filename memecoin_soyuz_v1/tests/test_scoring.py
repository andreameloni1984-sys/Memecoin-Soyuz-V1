from soyuz.models import TokenSnapshot
from soyuz.scoring import build_signal


def make_safe_token() -> TokenSnapshot:
    return TokenSnapshot(
        address="TEST_TOKEN",
        symbol="TEST",
        liquidity_usd=150_000,
        market_cap_usd=1_000_000,
        volume_5m_usd=150_000,
        buys_5m=80,
        sells_5m=20,
        price_change_5m_pct=5,
        holders=1000,
        top10_pct=30,
        dev_pct=2,
        insider_pct=5,
        bundle_pct=5,
        smart_money_buys=8,
        smart_money_sells=2,
        smart_money_quality=80,
        social_velocity=70,
        execution_slippage_pct=0.3,
        honeypot=False,
    )


def test_honeypot_is_always_skipped():
    token = make_safe_token()
    token.honeypot = True

    signal = build_signal(token)

    assert signal.decision == "SKIP"
    assert signal.safety_score == 0


def test_unsafe_token_is_skipped():
    token = make_safe_token()

    token.mint_authority_active = True
    token.freeze_authority_active = True
    token.permanent_delegate = True
    token.top10_pct = 75

    signal = build_signal(token)

    assert signal.decision == "SKIP"
    assert signal.safety_score < 60


def test_strong_token_can_generate_paper_buy():
    token = make_safe_token()

    signal = build_signal(
        token,
        paper_entry_usd=25,
    )

    assert signal.decision == "BUY_PAPER"
    assert signal.safety_score >= 60
    assert signal.execution_score >= 50
    assert signal.total_score >= 72
    assert signal.paper_entry_usd == 25


def test_bad_execution_blocks_buy():
    token = make_safe_token()

    token.liquidity_usd = 10_000
    token.execution_slippage_pct = 4

    signal = build_signal(token)

    assert signal.execution_score < 50
    assert signal.decision == "SKIP"