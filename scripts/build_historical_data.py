"""Build historical tournament data CSV from Barttorvik (2008–2025).

Fetches team metrics for each season and cross-references with known tournament
results to produce a training dataset for the logistic regression model.

Output: data/historical_results_2008_2025.csv
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests
from rich.console import Console
from rich.progress import track

console = Console()

DATA_DIR = Path(__file__).parent.parent / "data"
BARTTORVIK_URL = "https://barttorvik.com/{year}_team_results.json"

# Field indices (same as fetch_data.py)
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
}

# Historical tournament results: {year: {team: {"seed": int, "round_reached": int}}}
# round_reached: 1=R64 loss, 2=R32 loss, 3=S16 loss, 4=E8 loss, 5=F4 loss, 6=Runner-up, 7=Champion
# We'll build this from a known results CSV, but include recent years inline as seed data
KNOWN_CHAMPIONS = {
    2008: "Kansas",
    2009: "North Carolina",
    2010: "Duke",
    2011: "Connecticut",
    2012: "Kentucky",
    2013: "Louisville",
    2014: "Connecticut",
    2015: "Duke",
    2016: "Villanova",
    2017: "North Carolina",
    2018: "Villanova",
    2019: "Virginia",
    # 2020: cancelled (COVID)
    2021: "Baylor",
    2022: "Kansas",
    2023: "Connecticut",
    2024: "Connecticut",
    2025: "Florida",  # placeholder — update if different
}


def fetch_season_data(year: int) -> pd.DataFrame | None:
    """Fetch Barttorvik team data for a single season."""
    url = BARTTORVIK_URL.format(year=year)
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        raw = json.loads(resp.text)
    except Exception as e:
        console.print(f"[yellow]Skipping {year}: {e}[/yellow]")
        return None

    rows = []
    for entry in raw:
        row = {"year": year}
        for col_name, idx in FIELD_MAP.items():
            if idx < len(entry):
                row[col_name] = entry[idx]
        rows.append(row)

    return pd.DataFrame(rows)


def load_tournament_results() -> pd.DataFrame:
    """Load tournament results from CSV.

    Expected format: year, team, seed, round_reached (1-7)
    """
    csv_path = DATA_DIR / "tournament_results.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)

    console.print("[yellow]No tournament_results.csv found. Building from scratch...[/yellow]")
    console.print("[yellow]We need this file with columns: year, team, seed, round_reached[/yellow]")
    console.print("[yellow]Run this script with --build-results first to generate it.[/yellow]")
    return pd.DataFrame(columns=["year", "team", "seed", "round_reached"])


def build_historical_csv():
    """Build the full historical dataset by merging Barttorvik metrics with tournament results."""
    console.print("[bold]Building historical dataset (2008–2025)...[/bold]")

    tournament_df = load_tournament_results()
    all_data = []

    years = [y for y in range(2008, 2026) if y != 2020]  # Skip 2020 (COVID)

    for year in track(years, description="Fetching seasons..."):
        season_df = fetch_season_data(year)
        if season_df is None:
            continue

        if not tournament_df.empty:
            # Merge tournament results with season metrics
            year_tourney = tournament_df[tournament_df["year"] == year]
            if not year_tourney.empty:
                merged = season_df.merge(
                    year_tourney[["year", "team", "seed", "round_reached"]],
                    on=["year", "team"],
                    how="inner",
                )
                all_data.append(merged)
                console.print(f"  [green]{year}: {len(merged)} tournament teams matched[/green]")
            else:
                console.print(f"  [yellow]{year}: no tournament results found[/yellow]")
        else:
            # No tournament results — just save the team data
            all_data.append(season_df)

        time.sleep(0.5)  # Be polite to Barttorvik

    if not all_data:
        console.print("[red]No data collected![/red]")
        return

    full_df = pd.concat(all_data, ignore_index=True)

    # Add computed features
    total_games = full_df["wins"].astype(float) + full_df["losses"].astype(float)
    full_df["win_pct"] = (full_df["wins"].astype(float) / total_games).round(4)

    # Add era weighting flag (2019+ = recent era, weighted 2x in model training)
    full_df["recent_era"] = (full_df["year"] >= 2019).astype(int)

    output_path = DATA_DIR / "historical_results_2008_2025.csv"
    full_df.to_csv(output_path, index=False)
    console.print(f"\n[bold green]Saved {len(full_df)} records to {output_path}[/bold green]")

    # Summary stats
    if "round_reached" in full_df.columns:
        champions = full_df[full_df["round_reached"] == 7]
        if not champions.empty:
            console.print("\n[bold]Champion profile (historical averages):[/bold]")
            console.print(f"  Avg AdjO: {champions['adj_o'].mean():.1f} (rank {champions['adj_o_rank'].mean():.0f})")
            console.print(f"  Avg AdjD: {champions['adj_d'].mean():.1f} (rank {champions['adj_d_rank'].mean():.0f})")
            console.print(f"  Avg Barthag: {champions['barthag'].mean():.4f}")


def build_seed_win_rates():
    """Build seed vs. seed historical win rate CSV."""
    tournament_df = load_tournament_results()
    if tournament_df.empty:
        console.print("[red]Need tournament_results.csv to build seed win rates[/red]")
        return

    # Calculate how far each seed typically advances
    seed_stats = tournament_df.groupby("seed").agg(
        avg_round=("round_reached", "mean"),
        max_round=("round_reached", "max"),
        count=("round_reached", "count"),
        champion_count=("round_reached", lambda x: (x == 7).sum()),
    ).round(3)

    output_path = DATA_DIR / "seed_win_rates.csv"
    seed_stats.to_csv(output_path)
    console.print(f"[green]Saved seed win rates to {output_path}[/green]")


if __name__ == "__main__":
    import sys

    DATA_DIR.mkdir(exist_ok=True)

    if "--seed-rates" in sys.argv:
        build_seed_win_rates()
    else:
        build_historical_csv()
