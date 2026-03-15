# March Madness Bracket Analyzer

> This file is loaded into every Claude session. Keep it lean and accurate.
> For how the workflow system works, see `docs/reference/`.

## What This Is
Python CLI tool that runs 10,000 Monte Carlo simulations of the 2026 NCAA tournament bracket. Uses logistic regression trained on 18 years of data (2008–2025), live Barttorvik efficiency metrics, injury adjustments, and momentum tracking. Outputs three bracket strategies (safe/balanced/risky), champion probabilities, upset alerts, and exportable CSVs.

## Stack
- Python 3.12+
- pandas, numpy — data manipulation
- requests — Barttorvik API calls
- scikit-learn — logistic regression model
- rich — terminal output formatting
- typer — CLI interface

## Key Commands
```bash
pip install -r requirements.txt                                          # install deps
python main.py run --bracket data/2026_bracket.json                      # full Monte Carlo analysis
python main.py run --bracket data/2026_bracket.json --sims 10000         # customize sim count
python main.py run --bracket data/2026_bracket.json --export all         # export safe/balanced/risky CSVs
python main.py upsets --bracket data/2026_bracket.json                   # upset alerts only
python main.py champion --bracket data/2026_bracket.json                 # champion probabilities
python scripts/build_historical_data.py                                  # one-time: build training CSV
```

## Important Paths
- `src/fetch_data.py` — Barttorvik API fetcher (live metrics + momentum from fields 29/30/31)
- `src/model.py` — logistic regression + weighted composite fallback
- `src/bracket.py` — deterministic sim + Monte Carlo engine (10k sims, 3 strategies)
- `src/upsets.py` — multi-factor upset detection
- `src/injuries.py` — injury Barthag adjustments from `data/injuries.json`
- `src/output.py` — rich terminal display + CSV/JSON export
- `data/injuries.json` — manual injury entries (supports verified_clean, _comment dividers)
- `data/tournament_results.csv` — historical results 2008–2025 (1082 teams)
- `scripts/fix_team_names.py` — normalizes team names to Barttorvik conventions

## Constraints
- All terminal output via `rich` — no bare `print()` calls
- Network calls have retry logic (3 attempts with 2s backoff)
- Barttorvik is the sole data source — no Sports-Reference dependency
- Barttorvik endpoint: `https://barttorvik.com/{year}_team_results.json` (works 2008–2026)
- All 68 team names must resolve to Barttorvik names — surface lookup failures clearly
- Full pipeline with 10k sims runs in ~15 seconds
- Historical model weights recent seasons (2019–2025) at 2x vs older data
- Champion filter: AdjO rank ≤ 40 AND AdjD rank ≤ 25 (hard requirement)
- injuries.json entries with null player/impact/status or verified_clean are skipped

## Lessons
- Barttorvik HTML endpoints (trank.php, team-schedule.php) have JS browser verification — only the JSON endpoints work for automated access
- The `getadvstats.php` endpoint returns player-level data, not team-level — use `{year}_team_results.json` for team rankings
- Barttorvik fields 29/30/31 are recent-window AdjO/AdjD/Barthag — use for momentum calculation
- Team name matching between data sources is fragile — `scripts/fix_team_names.py` handles the mapping
- Model gracefully degrades: trains on whatever features exist in historical data, falls back to composite if logistic regression fails

## Current Focus
Feature-complete. Waiting for Selection Sunday bracket reveal (March 15, 2026 ~6:30pm ET) to fill in `data/2026_bracket_template.json` and run final analysis. Deadline: Wednesday March 18.
