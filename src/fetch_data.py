"""Fetch current-season team data from Barttorvik."""

import json
import time
from pathlib import Path

import pandas as pd
import requests
from rich.console import Console

console = Console()

BARTTORVIK_URL = "https://barttorvik.com/{year}_team_results.json"

# Field indices for the Barttorvik team_results JSON
# Full JSON has 45 fields per team; we map the ones we use.
FIELD_MAP = {
    "rank": 0,
    "team": 1,
    "conf": 2,
    "record": 3,
    "adj_o": 4,
    "adj_o_rank": 5,
    "adj_d": 6,
    "adj_d_rank": 7,
    "barthag": 8,
    "barthag_rank": 9,
    "wins": 10,
    "losses": 11,
    "conf_wins": 12,
    "conf_losses": 13,
    "conf_record": 14,
    "recent_adj_o": 29,      # adjusted offensive efficiency (recent window)
    "recent_adj_d": 30,      # adjusted defensive efficiency (recent window)
    "recent_barthag": 31,    # barthag computed from recent-window adj ratings
}


def fetch_team_data(year: int = 2026, retries: int = 3) -> pd.DataFrame:
    """Fetch all team rankings from Barttorvik for a given year.

    Returns DataFrame with columns: rank, team, conf, record, adj_o, adj_o_rank,
    adj_d, adj_d_rank, barthag, barthag_rank, wins, losses
    """
    url = BARTTORVIK_URL.format(year=year)

    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            raw = json.loads(resp.text)
            break
        except (requests.RequestException, json.JSONDecodeError) as e:
            if attempt == retries - 1:
                console.print(f"[red]Failed to fetch Barttorvik data after {retries} attempts: {e}[/red]")
                raise
            console.print(f"[yellow]Retry {attempt + 1}/{retries}...[/yellow]")
            time.sleep(2)

    rows = []
    for entry in raw:
        row = {}
        for col_name, idx in FIELD_MAP.items():
            if idx < len(entry):
                row[col_name] = entry[idx]
            else:
                row[col_name] = None
        rows.append(row)

    df = pd.DataFrame(rows)

    # Parse wins/losses from record string as fallback
    if df["wins"].isna().any():
        parts = df["record"].str.split("-", expand=True)
        df["wins"] = df["wins"].fillna(parts[0].astype(float))
        df["losses"] = df["losses"].fillna(parts[1].astype(float))

    # Compute win percentage
    total_games = df["wins"] + df["losses"]
    df["win_pct"] = (df["wins"] / total_games).round(4)

    # Compute SOS proxy: higher rank with fewer losses = stronger schedule
    # Barttorvik doesn't expose SOS directly in this endpoint, so we'll
    # use the gap between raw win% and Barthag as a proxy
    # (teams with high Barthag but lower win% faced harder schedules)
    df["sos_proxy"] = (df["barthag"] - df["win_pct"]).round(4)

    # Momentum: difference between recent-window barthag and season barthag.
    # Positive = team trending up, negative = trending down.
    # Barttorvik fields 29/30/31 use a recent-games window for adj ratings.
    # We use the difference (not ratio) to avoid wild swings for low-barthag teams.
    raw_momentum = df["recent_barthag"] - df["barthag"]
    # Clamp to +/-0.10 (covers ~99% of tournament-relevant teams)
    df["momentum"] = raw_momentum.clip(lower=-0.10, upper=0.10).round(4)

    console.print(f"[green]Fetched {len(df)} teams for {year}[/green]")
    return df


def resolve_team_names(bracket_teams: list[str], team_data: pd.DataFrame) -> dict[str, str]:
    """Map bracket team names to Barttorvik team names.

    Returns dict of {bracket_name: barttorvik_name} and prints any unresolved names.
    """
    bt_names = set(team_data["team"].values)
    resolved = {}
    unresolved = []

    # Common name variations
    aliases = {
        "UConn": "Connecticut",
        "UCONN": "Connecticut",
        "UNC": "North Carolina",
        "SMU": "Southern Methodist",
        "LSU": "Louisiana St.",
        "USC": "Southern California",
        "UCF": "Central Florida",
        "UNLV": "Nevada Las Vegas",
        "VCU": "Virginia Commonwealth",
        "BYU": "Brigham Young",
        "TCU": "Texas Christian",
        "Ole Miss": "Mississippi",
        "Pitt": "Pittsburgh",
        "Miami": "Miami FL",
        "Saint Mary's": "St. Mary's",
        "St. John's": "St. John's",
    }

    for name in bracket_teams:
        if name in bt_names:
            resolved[name] = name
        elif name in aliases and aliases[name] in bt_names:
            resolved[name] = aliases[name]
        else:
            # Fuzzy match: check if bracket name is a substring
            matches = [bt for bt in bt_names if name.lower() in bt.lower() or bt.lower() in name.lower()]
            if len(matches) == 1:
                resolved[name] = matches[0]
            else:
                unresolved.append(name)

    if unresolved:
        console.print(f"[red]Could not resolve {len(unresolved)} team names:[/red]")
        for name in unresolved:
            console.print(f"  [red]• {name}[/red]")
        console.print("[yellow]Add these to the aliases dict in fetch_data.py[/yellow]")

    return resolved


def get_team_metrics(team_data: pd.DataFrame, team_name: str) -> dict | None:
    """Get metrics for a single team by name."""
    match = team_data[team_data["team"] == team_name]
    if match.empty:
        return None
    row = match.iloc[0]
    return {
        "team": row["team"],
        "rank": int(row["rank"]),
        "adj_o": float(row["adj_o"]),
        "adj_o_rank": int(row["adj_o_rank"]),
        "adj_d": float(row["adj_d"]),
        "adj_d_rank": int(row["adj_d_rank"]),
        "barthag": float(row["barthag"]),
        "barthag_rank": int(row["barthag_rank"]),
        "win_pct": float(row["win_pct"]),
        "sos_proxy": float(row["sos_proxy"]),
        "momentum": float(row["momentum"]),
    }


if __name__ == "__main__":
    df = fetch_team_data(2026)
    console.print(df.head(20).to_string())
