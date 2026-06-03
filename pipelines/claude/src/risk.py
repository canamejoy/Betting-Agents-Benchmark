def kelly_stake(
    model_prob: float,
    odds_decimal: float,
    kelly_fraction: float,
    bankroll: float,
) -> float:
    """Fractional Kelly stake per shared_instructions formula: (edge/(odds-1)) * fraction * bankroll."""
    if odds_decimal <= 1.0:
        return 0.0
    implied_prob = 1.0 / odds_decimal
    edge = model_prob - implied_prob
    if edge <= 0:
        return 0.0
    return (edge / (odds_decimal - 1.0)) * kelly_fraction * bankroll


def cap_stake(stake: float, bankroll: float, max_stake_pct: float = 0.05) -> float:
    return min(stake, bankroll * max_stake_pct)
