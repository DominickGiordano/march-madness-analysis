"""Upset detection logic."""

from rich.console import Console

console = Console()

# Classic upset seed combos (historically volatile)
VOLATILE_MATCHUPS = {
    (5, 12): 0.35,   # 12-over-5 happens ~35% of the time
    (7, 10): 0.40,   # 10-over-7 is nearly a coin flip
    (6, 11): 0.37,   # 11-over-6 is common
    (8, 9): 0.50,    # true coin flip
    (3, 14): 0.15,   # rare but happens
    (4, 13): 0.20,   # 13-over-4 is a classic upset
}


def detect_upsets(team_data: dict[str, dict], bracket: dict) -> list[dict]:
    """Scan all R64 matchups for potential upsets.

    Flags a matchup as an upset alert when:
    - Lower seed has Barthag > higher seed AND
    - Seed differential >= 3 AND
    - Lower seed AdjD rank <= 35
    """
    from src.bracket import SEED_MATCHUPS

    alerts = []

    for region_name, seeds in bracket["regions"].items():
        for high_seed, low_seed in SEED_MATCHUPS:
            team_high = seeds.get(str(high_seed))
            team_low = seeds.get(str(low_seed))

            if not team_high or not team_low:
                continue

            metrics_high = team_data.get(team_high, {})
            metrics_low = team_data.get(team_low, {})

            alert = _check_upset(
                team_high, high_seed, metrics_high,
                team_low, low_seed, metrics_low,
                region_name,
            )
            if alert:
                alerts.append(alert)

    # Sort by confidence (highest first)
    alerts.sort(key=lambda x: x["confidence"], reverse=True)
    return alerts


def _check_upset(
    team_high: str, seed_high: int, metrics_high: dict,
    team_low: str, seed_low: int, metrics_low: dict,
    region: str,
) -> dict | None:
    """Check if a specific matchup triggers upset alert conditions."""
    seed_diff = seed_low - seed_high
    barthag_high = metrics_high.get("barthag", 0.5)
    barthag_low = metrics_low.get("barthag", 0.5)
    adj_d_rank_low = metrics_low.get("adj_d_rank", 999)
    adj_d_rank_high = metrics_high.get("adj_d_rank", 999)
    win_pct_low = metrics_low.get("win_pct", 0.5)

    reasons = []
    confidence = 0.0

    # Primary upset trigger: lower seed has higher Barthag
    barthag_delta = barthag_low - barthag_high
    if barthag_delta > 0:
        reasons.append(f"Barthag delta +{barthag_delta:.3f}")
        confidence += 0.3

    # Seed differential check
    if seed_diff >= 3:
        confidence += 0.1

    # Defensive mismatch: lower seed has strong defense
    if adj_d_rank_low <= 35:
        reasons.append(f"AdjD rank {adj_d_rank_low}")
        confidence += 0.2

    # Defensive mismatch: higher seed has weak defense relative to seed
    if adj_d_rank_high > 50 and seed_high <= 6:
        reasons.append(f"#{seed_high} seed weak D (rank {adj_d_rank_high})")
        confidence += 0.15

    # Hot streak bonus
    if win_pct_low >= 0.75:
        reasons.append(f"strong record ({win_pct_low:.0%})")
        confidence += 0.1

    # Historical volatility bonus
    matchup_key = (seed_high, seed_low)
    if matchup_key in VOLATILE_MATCHUPS:
        hist_rate = VOLATILE_MATCHUPS[matchup_key]
        if hist_rate >= 0.30:
            reasons.append(f"historically volatile ({hist_rate:.0%} upset rate)")
            confidence += 0.15

    # Only flag if there's a meaningful signal
    if not reasons or confidence < 0.3:
        return None

    # Must meet at least one core criterion
    core_met = barthag_delta > 0 or adj_d_rank_low <= 35 or (matchup_key in VOLATILE_MATCHUPS and VOLATILE_MATCHUPS[matchup_key] >= 0.30)
    if not core_met:
        return None

    return {
        "region": region,
        "higher_seed": seed_high,
        "higher_team": team_high,
        "lower_seed": seed_low,
        "lower_team": team_low,
        "reasons": reasons,
        "confidence": min(confidence, 1.0),
        "barthag_delta": barthag_delta,
        "matchup": f"#{seed_low} {team_low} over #{seed_high} {team_high}",
    }
