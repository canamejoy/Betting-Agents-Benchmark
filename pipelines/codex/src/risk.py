"""Stake sizing and bankroll risk controls."""


def flat_stake(amount: float) -> float:
    return max(0.0, amount)


def kelly_stake(
    model_prob: float,
    odds_decimal: float,
    bankroll: float,
    kelly_fraction: float,
    max_stake_pct: float,
) -> float:
    """Fractional Kelly with a cap.

    edge = model_prob - implied_prob
    b    = odds_decimal - 1  (net odds)
    kelly = edge / b
    stake = kelly * kelly_fraction * bankroll
    """
    implied_prob = 1.0 / odds_decimal
    edge = model_prob - implied_prob
    if edge <= 0 or bankroll <= 0:
        return 0.0
    b = odds_decimal - 1.0
    if b <= 0:
        return 0.0
    raw_kelly = edge / b
    stake = raw_kelly * kelly_fraction * bankroll
    cap = max_stake_pct * bankroll
    return min(stake, cap)


def apply_daily_exposure_cap(
    stake: float,
    date,
    daily_staked: dict,
    bankroll: float,
    max_daily_exposure_pct: float,
) -> float:
    """Reduce stake so daily total does not exceed cap."""
    key = str(date)
    already_staked = daily_staked.get(key, 0.0)
    cap = max_daily_exposure_pct * bankroll
    remaining = max(0.0, cap - already_staked)
    return min(stake, remaining)


def update_bankroll(bankroll: float, stake: float, result: str, odds_decimal: float) -> float:
    if result == "win":
        return bankroll + stake * (odds_decimal - 1.0)
    elif result == "loss":
        return max(0.0, bankroll - stake)
    else:  # push
        return bankroll  # stake returned implicitly (no deduction recorded)
