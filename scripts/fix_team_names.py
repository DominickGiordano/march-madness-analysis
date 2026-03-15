"""Fix team names in tournament_results.csv to match Barttorvik naming conventions.

Barttorvik uses specific abbreviations (e.g., "St." instead of "State", no parentheses
in Miami FL, etc.). This script maps our CSV names to Barttorvik-compatible names and
rewrites the CSV.
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).parent.parent / "data"
BARTTORVIK_URL = "https://barttorvik.com/{year}_team_results.json"

# Explicit name mapping: CSV name -> Barttorvik name
# Built by comparing tournament_results.csv against Barttorvik JSON responses
NAME_MAP = {
    # "State" -> "St." conversions
    "Alabama State": "Alabama St.",
    "Appalachian State": "Appalachian St.",
    "Arizona State": "Arizona St.",
    "Boise State": "Boise St.",
    "Cleveland State": "Cleveland St.",
    "Colorado State": "Colorado St.",
    "Coppin State": "Coppin St.",
    "East Tennessee State": "East Tennessee St.",
    "Florida State": "Florida St.",
    "Fresno State": "Fresno St.",
    "Georgia State": "Georgia St.",
    "Indiana State": "Indiana St.",
    "Iowa State": "Iowa St.",
    "Jacksonville State": "Jacksonville St.",
    "Kansas State": "Kansas St.",
    "Kennesaw State": "Kennesaw St.",
    "Kent State": "Kent St.",
    "Long Beach State": "Long Beach St.",
    "Michigan State": "Michigan St.",
    "Mississippi State": "Mississippi St.",
    "Mississippi Valley State": "Mississippi Valley St.",
    "Montana State": "Montana St.",
    "Morehead State": "Morehead St.",
    "Morgan State": "Morgan St.",
    "Murray State": "Murray St.",
    "New Mexico State": "New Mexico St.",
    "Norfolk State": "Norfolk St.",
    "North Dakota State": "North Dakota St.",
    "Northwestern State": "Northwestern St.",
    "Ohio State": "Ohio St.",
    "Oklahoma State": "Oklahoma St.",
    "Oregon State": "Oregon St.",
    "Penn State": "Penn St.",
    "Portland State": "Portland St.",
    "Sam Houston State": "Sam Houston St.",
    "San Diego State": "San Diego St.",
    "South Dakota State": "South Dakota St.",
    "Southeast Missouri State": "Southeast Missouri St.",
    "Utah State": "Utah St.",
    "Washington State": "Washington St.",
    "Weber State": "Weber St.",
    "Wichita State": "Wichita St.",
    "Wright State": "Wright St.",

    # "Cal State" variants
    "Cal State Fullerton": "Cal St. Fullerton",
    "CS Fullerton": "Cal St. Fullerton",
    "CSU Bakersfield": "Cal St. Bakersfield",

    # NC / North Carolina abbreviations
    "NC State": "N.C. State",
    "North Carolina State": "N.C. State",
    "NC Central": "North Carolina Central",
    "NC Greensboro": "UNC Greensboro",

    # Parenthetical formatting
    "Miami (FL)": "Miami FL",
    "Loyola (MD)": "Loyola MD",

    # Other name differences
    "College of Charleston": "Charleston",
    "Arkansas Little Rock": "Little Rock",
    "Louisiana Lafayette": "Louisiana",
    "McNeese": "McNeese St.",
    "Grambling": "Grambling St.",
    "Long Island": "LIU",
    "Ole Miss": "Mississippi",
    "Detroit": "Detroit Mercy",
    "UConn": "Connecticut",
    "UNC": "North Carolina",
    "Pitt": "Pittsburgh",
    "UMass": "Massachusetts",
    "Central Florida": "UCF",
    "St. Louis": "Saint Louis",
    "St. Mary's": "Saint Mary's",
    "St. Peter's": "Saint Peter's",
    "St. John's": "St. John's",
    "St. Bonaventure": "St. Bonaventure",
    "Matadors": "Cal St. Northridge",
    "Tampa": "South Florida",
    "Arlington": "UT Arlington",
    "Texas Arlington": "UT Arlington",
    "Texas San Antonio": "UTSA",
    "Texas A&M Corpus Christi": "Texas A&M Corpus Chris",
    "Gardner-Webb": "Gardner Webb",
    "South Alabama": "South Alabama",
    "San Diego": "San Diego",
    "IUPUI": "IU Indy",
    "Omaha": "Nebraska Omaha",
}


def fetch_barttorvik_teams(year: int) -> set[str]:
    """Fetch the set of team names from Barttorvik for a given year."""
    url = BARTTORVIK_URL.format(year=year)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = json.loads(resp.text)
    return {entry[1] for entry in data}


def main():
    csv_path = DATA_DIR / "tournament_results.csv"
    df = pd.read_csv(csv_path)

    print(f"Loaded {len(df)} records from tournament_results.csv")
    print(f"Unique teams before fix: {df['team'].nunique()}")

    # Apply name mapping
    df["team"] = df["team"].replace(NAME_MAP)

    # Remove exact duplicates that may have been created (e.g., Pitt and Pittsburgh)
    df = df.drop_duplicates(subset=["year", "team", "seed", "round_reached"])

    print(f"Unique teams after fix: {df['team'].nunique()}")

    # Validate against Barttorvik for each year
    years = sorted(df["year"].unique())
    total_records = 0
    matched_records = 0
    all_unmatched = {}

    for year in years:
        try:
            bart_teams = fetch_barttorvik_teams(year)
        except Exception as e:
            print(f"  WARNING: Could not fetch {year}: {e}")
            continue

        year_df = df[df["year"] == year]
        csv_teams_year = set(year_df["team"].unique())

        matched = csv_teams_year & bart_teams
        unmatched = csv_teams_year - bart_teams

        total_records += len(csv_teams_year)
        matched_records += len(matched)

        if unmatched:
            all_unmatched[year] = unmatched
            print(f"  {year}: {len(matched)}/{len(csv_teams_year)} matched, UNMATCHED: {sorted(unmatched)}")
        else:
            print(f"  {year}: {len(matched)}/{len(csv_teams_year)} matched (100%)")

        time.sleep(0.3)

    match_rate = matched_records / total_records * 100 if total_records else 0
    print(f"\nOverall match rate: {matched_records}/{total_records} = {match_rate:.1f}%")

    if all_unmatched:
        print("\n=== Still unmatched teams (need manual review) ===")
        all_bad = set()
        for year, teams in all_unmatched.items():
            all_bad.update(teams)
        for t in sorted(all_bad):
            print(f"  {t}")

    # Save updated CSV
    df.to_csv(csv_path, index=False)
    print(f"\nSaved updated CSV to {csv_path}")


if __name__ == "__main__":
    main()
