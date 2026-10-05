from .models import Signal, TokenSnapshot


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """Keep a score inside the 0-100 range."""
    return max(minimum, min(maximum, value))


def calculate_safety_score(token: TokenSnapshot) -> tuple[float, list[str]]:
    """
    Calculate the token safety score.

    The score starts at 100 and receives penalties for
    known structural/security risks.
    """

    score = 100.0
    reasons: list[str] = []

    if token.honeypot:
        return 0.0, ["HONEYPOT"]

    if token.mint_authority_active:
        score -= 20
        reasons.append("Mint authority active")

    if token.freeze_authority_active:
        score -= 20
        reasons.append("Freeze authority active")

    if token.permanent_delegate:
        score -= 20
        reasons.append("Permanent delegate active")

    if token.transfer_hook:
        score -= 10
        reasons.append("Transfer hook detected")

    if token.transfer_fee_bps > 300:
        score -= 15
        reasons.append("High transfer fee")

    elif token.transfer_fee_bps > 100:
        score -= 5
        reasons.append("Elevated transfer fee")

    if token.top10_pct > 70:
        score -= 25
        reasons.append("Extreme top-10 concentration")

    elif token.top10_pct > 50:
        score -= 15
        reasons.append("High top-10 concentration")

    if token.dev_pct > 10:
        score -= 20
        reasons.append("High developer allocation")

    elif token.dev_pct > 5:
        score -= 10
        reasons.append("Elevated developer allocation")

    if token.insider_pct > 20:
        score -= 15
        reasons.append("High insider concentration")

    elif token.insider_pct > 10:
        score -= 7
        reasons.append("Elevated insider concentration")

    if token.bundle_pct > 20:
        score -= 15
        reasons.append("High bundle concentration")

    elif token.bundle_pct > 10:
        score -= 7
        reasons.append("Elevated bundle concentration")

    if token.liquidity_usd < 20_000:
        score -= 25
        reasons.append("Very low liquidity")

    elif token.liquidity_usd < 50_000:
        score -= 10
        reasons.append("Low liquidity")

    if not reasons:
        reasons.append("No major structural risk detected")

    return _clamp(score), reasons


def calculate_opportunity_score(token: TokenSnapshot) -> tuple[float, list[str]]:
    """
    Calculate the opportunity score.

    Opportunity combines:
    - buy/sell pressure
    - volume relative to liquidity
    - Smart Money flow
    - Smart Money quality
    - short-term momentum
    - social velocity
    """

    score = 0.0
    reasons: list[str] = []

    total_trades = token.buys_5m + token.sells_5m

    if total_trades > 0:
        buy_ratio = token.buys_5m / total_trades

        if buy_ratio >= 0.70:
            score += 25
            reasons.append("Strong buy pressure")

        elif buy_ratio >= 0.55:
            score += 15
            reasons.append("Positive buy pressure")

        elif buy_ratio < 0.40:
            score -= 15
            reasons.append("Strong sell pressure")

    if token.liquidity_usd > 0:
        volume_ratio = token.volume_5m_usd / token.liquidity_usd

        if volume_ratio >= 1.0:
            score += 20
            reasons.append("Very strong volume/liquidity")

        elif volume_ratio >= 0.50:
            score += 15
            reasons.append("Strong volume/liquidity")

        elif volume_ratio >= 0.20:
            score += 8
            reasons.append("Healthy volume/liquidity")

    smart_flow = token.smart_money_buys - token.smart_money_sells

    if smart_flow >= 5:
        score += 20
        reasons.append("Strong Smart Money accumulation")

    elif smart_flow > 0:
        score += 10
        reasons.append("Positive Smart Money flow")

    elif smart_flow < 0:
        score -= 15
        reasons.append("Smart Money distribution")

    smart_quality = _clamp(token.smart_money_quality)

    score += smart_quality * 0.15

    if smart_quality >= 70:
        reasons.append("High Smart Money quality")

    if token.price_change_5m_pct >= 10:
        score += 15
        reasons.append("Strong short-term momentum")

    elif token.price_change_5m_pct >= 3:
        score += 8
        reasons.append("Positive short-term momentum")

    elif token.price_change_5m_pct <= -10:
        score -= 15
        reasons.append("Strong negative momentum")

    elif token.price_change_5m_pct < -3:
        score -= 8
        reasons.append("Negative short-term momentum")

    social = _clamp(token.social_velocity)

    score += social * 0.05

    if social >= 70:
        reasons.append("High narrative/social velocity")

    return _clamp(score), reasons


def calculate_execution_score(token: TokenSnapshot) -> tuple[float, list[str]]:
    """
    Calculate execution quality.

    This measures whether a theoretical trade could realistically
    be executed without excessive liquidity or slippage risk.
    """

    score = 100.0
    reasons: list[str] = []

    if token.liquidity_usd < 20_000:
        score -= 60
        reasons.append("Execution liquidity too low")

    elif token.liquidity_usd < 50_000:
        score -= 20
        reasons.append("Limited execution liquidity")

    elif token.liquidity_usd >= 100_000:
        reasons.append("Good execution liquidity")

    slippage = max(0.0, token.execution_slippage_pct)

    if slippage > 3:
        score -= 50
        reasons.append("Extreme expected slippage")

    elif slippage > 1:
        score -= 20
        reasons.append("High expected slippage")

    elif slippage <= 0.5:
        reasons.append("Low expected slippage")

    if token.volume_5m_usd <= 0:
        score -= 30
        reasons.append("No recent trading volume")

    return _clamp(score), reasons


def build_signal(
    token: TokenSnapshot,
    paper_entry_usd: float = 25.0,
    take_profit_pct: float = 30.0,
    stop_loss_pct: float = 15.0,
) -> Signal:
    """
    Build the final Soyuz decision.

    Hard safety gates are applied before the final decision.
    """

    safety_score, safety_reasons = calculate_safety_score(token)

    opportunity_score, opportunity_reasons = calculate_opportunity_score(token)

    execution_score, execution_reasons = calculate_execution_score(token)

    # Weighted overall score.
    total_score = (
        safety_score * 0.40
        + opportunity_score * 0.40
        + execution_score * 0.20
    )

    reasons = (
        safety_reasons
        + opportunity_reasons
        + execution_reasons
    )

    # ---------------------------------------------------------
    # HARD SAFETY GATES
    # ---------------------------------------------------------

    if token.honeypot:
        decision = "SKIP"
        reasons.insert(0, "HARD GATE: HONEYPOT")

    elif safety_score < 60:
        decision = "SKIP"
        reasons.insert(0, "HARD GATE: safety score below 60")

    elif execution_score < 50:
        decision = "SKIP"
        reasons.insert(0, "HARD GATE: execution score below 50")

    elif token.price_usd <= 0:
        decision = "SKIP"
        reasons.insert(0, "HARD GATE: invalid entry price")

    elif token.liquidity_usd <= 0 or token.volume_5m_usd <= 0:
        decision = "SKIP"
        reasons.insert(0, "HARD GATE: insufficient market data")

    elif total_score >= 72:
        decision = "BUY_PAPER"

    elif total_score >= 60:
        decision = "WATCH"

    else:
        decision = "SKIP"

    return Signal(
        address=token.address,
        symbol=token.symbol,
        decision=decision,
        safety_score=round(safety_score, 2),
        opportunity_score=round(opportunity_score, 2),
        execution_score=round(execution_score, 2),
        total_score=round(total_score, 2),
        reasons=reasons,
        paper_entry_usd=paper_entry_usd,
        entry_price_usd=token.price_usd,
        take_profit_price_usd=token.price_usd * (1.0 + take_profit_pct / 100.0),
        stop_loss_price_usd=token.price_usd * (1.0 - stop_loss_pct / 100.0),
    )