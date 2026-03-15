"""Injury adjustment logic.

Applies Barthag/rating penalties based on manually-entered injury data.
"""

import json
from pathlib import Path

from rich.console import Console

console = Console()

DATA_DIR = Path(__file__).parent.parent / "data"

# Impact penalties applied to Barthag (multiplicative)
# Based on rough empirical estimates of player contribution
IMPACT_PENALTIES = {
    "star": {
        "out": 0.92,          # ~8% Barthag reduction
        "questionable": 0.96,  # ~4% if they might not play
        "limited": 0.97,       # ~3% if playing hurt
    },
    "starter": {
        "out": 0.96,
        "questionable": 0.98,
        "limited": 0.99,
    },
    "rotation": {
        "out": 0.98,
        "questionable": 0.99,
        "limited": 1.0,
    },
}


def load_injuries(injuries_path: str | Path | None = None) -> dict[str, list[dict]]:
    """Load injuries JSON and return {team_name: [injury_records]}.

    Returns empty dict if no injuries file or no injuries listed.
    """
    if injuries_path is None:
        injuries_path = DATA_DIR / "injuries.json"

    path = Path(injuries_path)
    if not path.exists():
        return {}

    with open(path) as f:
        data = json.load(f)

    raw_entries = data.get("injuries", [])

    # Filter to only actionable injury entries:
    # - Must have a "team" key (skip _comment dividers)
    # - Must have a non-null "player" (skip verified_clean / info-only entries)
    # - Must have a non-null "impact" and "status"
    # - Skip example placeholders
    injuries = []
    for entry in raw_entries:
        # Skip comment dividers (only have _comment key)
        if "_comment" in entry and "team" not in entry:
            continue
        # Skip entries without a team
        if not entry.get("team"):
            continue
        # Skip example entries
        if entry.get("team", "").upper() == "EXAMPLE_TEAM":
            continue
        # Skip verified_clean / info-only entries (no actual injury)
        if entry.get("verified_clean") or not entry.get("player"):
            continue
        # Skip entries without actionable impact/status
        if not entry.get("impact") or not entry.get("status"):
            continue
        injuries.append(entry)

    if not injuries:
        return {}

    # Group by team
    by_team: dict[str, list[dict]] = {}
    for injury in injuries:
        team = injury["team"]
        by_team.setdefault(team, []).append(injury)

    console.print(f"[yellow]Loaded {len(injuries)} injuries for {len(by_team)} teams[/yellow]")
    return by_team


def _resolve_injury_team(injury_team: str, bracket_teams: set[str]) -> str | None:
    """Try to match an injury team name to a bracket team name."""
    if injury_team in bracket_teams:
        return injury_team
    # Case-insensitive match
    lower_map = {t.lower(): t for t in bracket_teams}
    if injury_team.lower() in lower_map:
        return lower_map[injury_team.lower()]
    # Common aliases
    aliases = {
        "UConn": "Connecticut", "Michigan State": "Michigan St.",
        "Mississippi State": "Mississippi St.", "Iowa State": "Iowa St.",
        "Ohio State": "Ohio St.", "Florida State": "Florida St.",
        "NC State": "N.C. State", "Ole Miss": "Mississippi",
        "Miami (FL)": "Miami FL", "Saint Mary's": "St. Mary's",
    }
    resolved = aliases.get(injury_team)
    if resolved and resolved in bracket_teams:
        return resolved
    # Substring match
    matches = [t for t in bracket_teams if injury_team.lower() in t.lower() or t.lower() in injury_team.lower()]
    if len(matches) == 1:
        return matches[0]
    return None


def apply_injury_adjustments(
    team_data: dict[str, dict],
    injuries: dict[str, list[dict]],
) -> dict[str, dict]:
    """Apply injury-based penalties to team metrics.

    Modifies team_data in place and returns it.
    """
    if not injuries:
        return team_data

    bracket_teams = set(team_data.keys())

    for team_name, injury_list in injuries.items():
        resolved = _resolve_injury_team(team_name, bracket_teams)
        if not resolved:
            console.print(f"[dim]Injury for '{team_name}' — not in bracket (skipped)[/dim]")
            continue
        if resolved != team_name:
            console.print(f"[dim]Injury '{team_name}' → matched to '{resolved}'[/dim]")
        team_name = resolved

        metrics = team_data[team_name]
        original_barthag = metrics.get("barthag", 0.5)
        cumulative_penalty = 1.0

        for injury in injury_list:
            impact = injury.get("impact", "rotation")
            status = injury.get("status", "questionable")
            player = injury.get("player", "Unknown")

            penalty = IMPACT_PENALTIES.get(impact, {}).get(status, 1.0)
            cumulative_penalty *= penalty

            console.print(
                f"  [yellow]{team_name}[/yellow]: {player} ({impact}, {status}) "
                f"— Barthag penalty: {penalty:.2f}x"
            )

        adjusted_barthag = original_barthag * cumulative_penalty
        metrics["barthag"] = adjusted_barthag
        metrics["barthag_original"] = original_barthag
        metrics["injury_adjusted"] = True

        console.print(
            f"  [yellow]{team_name} Barthag: {original_barthag:.4f} → {adjusted_barthag:.4f}[/yellow]"
        )

    return team_data
