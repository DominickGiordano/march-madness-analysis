# March Madness Bracket Analyzer

Python CLI tool that runs **10,000 Monte Carlo simulations** of the 2026 NCAA tournament to produce three bracket strategies — safe, balanced, and risky — with champion probabilities, upset alerts, and full advancement odds for every team.

## Quick Start

```bash
pip install -r requirements.txt

# Build historical training data (one-time, ~20s)
python scripts/build_historical_data.py

# Run full analysis (10k simulations, three brackets)
python main.py run --bracket data/2026_bracket.json

# Export all three brackets as CSVs
python main.py run --bracket data/2026_bracket.json --export all

# Upset alerts only
python main.py upsets --bracket data/2026_bracket.json

# Champion probabilities deep dive
python main.py champion --bracket data/2026_bracket.json
```

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--bracket` | required | Path to bracket JSON file |
| `--sims` | 10000 | Number of Monte Carlo simulations |
| `--export` | none | `csv`, `json`, or `all` (exports safe/balanced/risky CSVs) |
| `--no-train` | false | Skip logistic regression, use weighted composite only |
| `--injuries-file` | `data/injuries.json` | Path to injuries JSON |

## How It Works

```
Bracket JSON --> fetch_data.py --> model.py --> bracket.py --> output.py
                      |                |              |
               Barttorvik API    Historical CSV    Monte Carlo
               (live metrics)    (log. regression)  (10k sims)
                      |
               injuries.json
               (Barthag penalties)
```

1. Fill in `data/2026_bracket_template.json` with 68 teams + seeds after Selection Sunday (~5 min)
2. Tool pulls current-season efficiency metrics from [Barttorvik](https://barttorvik.com) (free, no auth)
3. Logistic regression trained on 18 years of tournament data (2008–2025, 1082 teams) scores every matchup
4. Injuries reduce affected teams' Barthag ratings before scoring
5. Monte Carlo engine runs 10,000 tournaments, randomly resolving each matchup based on win probabilities
6. Three bracket strategies are built from the simulation results

### Three Bracket Strategies

| Strategy | What it does | Upsets | Best for |
|----------|-------------|--------|----------|
| **Safe** | Always picks the favorite | ~13 | Maximizing correct picks |
| **Balanced** | Picks upsets at >40–47% probability (tighter in later rounds) | ~23 | Most bracket pools |
| **Risky** | Picks any underdog with >35% win probability | ~28 | High ceiling, differentiation |

### What You Get

- **Champion probabilities** — "Arizona wins it all in 15.5% of sims"
- **Final Four probabilities** — "Florida makes the Final Four 43% of the time"
- **Full advancement table** — S16/E8/F4/Champ % for every team
- **Upset alerts** — multi-factor detection (Barthag delta, seed diff, defensive strength, historical patterns)
- **Three complete brackets** — safe, balanced, risky — with round-by-round picks and upset counts

## Filling In the Bracket

After the Selection Sunday reveal, edit `data/2026_bracket_template.json`:

```json
{
  "regions": {
    "east": {
      "1": "Duke",
      "2": "Alabama",
      "...": "...",
      "16": "Norfolk St."
    },
    "west": { "..." : "..." },
    "south": { "..." : "..." },
    "midwest": { "..." : "..." }
  }
}
```

Team names should match Barttorvik conventions (e.g., "Connecticut" not "UConn", "North Carolina" not "UNC", "Iowa St." not "Iowa State"). The tool flags any names it can't resolve.

## Injuries

Edit `data/injuries.json` to account for injured or suspended players:

```json
{
  "injuries": [
    {
      "team": "Duke",
      "player": "John Smith",
      "impact": "star",
      "status": "out",
      "note": "ACL — out for tournament"
    }
  ]
}
```

| Impact | Barthag Penalty | Description |
|--------|----------------|-------------|
| `star` | -8% (out), -4% (questionable), -3% (limited) | Top 1–2 player on the team |
| `starter` | -4% (out), -2% (questionable), -1% (limited) | Regular starter |
| `rotation` | -2% (out), -1% (questionable), 0% (limited) | Bench contributor |

Multiple injuries stack multiplicatively. The tool auto-loads `data/injuries.json`.

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Monte Carlo over deterministic | 10k simulations capture variance — a 55% favorite loses 45% of the time |
| Barttorvik as primary data source | Free KenPom equivalent with public JSON API, no auth needed |
| Logistic regression over complex ML | Interpretable, fast, works with 6 features and ~1000 training samples |
| Defense weighted higher than offense | Every champion since 2002 had top-25 AdjD — defense wins in March |
| Champion hard filters (AdjO ≤ 40, AdjD ≤ 25) | No champion has failed these since 2002 |
| Recent era weighted 2x (2019–2025) | Transfer portal changed roster dynamics |
| Three bracket strategies | Different pools reward different approaches |
| Manual bracket + injuries input | Fast to fill in, no fragile scraping |

## Model

**Features** (6 inputs to logistic regression, also used in weighted composite):

| Feature | Weight | Source |
|---------|--------|--------|
| AdjD rank | 22% | Barttorvik — defensive efficiency rank |
| AdjO rank | 18% | Barttorvik — offensive efficiency rank |
| Barthag | 18% | Barttorvik — win probability vs average D1 team |
| Seed | 14% | Bracket — historical seed win rates are highly predictive |
| Momentum | 10% | Barttorvik — recent-window Barthag vs season Barthag |
| Win % | 8% | Barttorvik — overall record |
| SOS proxy | 10% | Derived — Barthag minus win% (harder schedule = bigger gap) |

**Upset detection** flags matchups where:
- Lower seed has higher Barthag than the favored team
- Seed differential >= 3
- Lower seed has AdjD rank <= 35
- Historically volatile matchup (5v12, 7v10, 6v11)

## Project Structure

```
march-madness-analyzer/
├── main.py                          # CLI entrypoint (typer)
├── requirements.txt
├── data/
│   ├── 2026_bracket_template.json   # Fill in after Selection Sunday
│   ├── injuries.json                # Manual injury entries
│   ├── tournament_results.csv       # Historical results 2008–2025
│   └── historical_results_2008_2025.csv  # Merged with Barttorvik metrics
├── src/
│   ├── fetch_data.py                # Barttorvik API data fetching + momentum
│   ├── model.py                     # Logistic regression + composite scoring
│   ├── bracket.py                   # Tournament sim + Monte Carlo engine
│   ├── upsets.py                    # Upset detection logic
│   ├── injuries.py                  # Injury adjustment logic
│   └── output.py                    # Rich terminal display + CSV/JSON export
├── scripts/
│   ├── build_historical_data.py     # One-time: build training dataset
│   └── fix_team_names.py            # One-time: normalize names to Barttorvik
├── output/                          # Generated bracket CSVs land here
└── docs/
    ├── PLAN.md                      # Original build plan
    └── architecture.md              # System architecture
```

## Data Sources

| Source | What | Access |
|--------|------|--------|
| [Barttorvik](https://barttorvik.com) | AdjO, AdjD, Barthag, SOS, tempo, momentum | Free JSON API (`/{year}_team_results.json`) |
| Historical tournament results | Seeds, round reached, 2008–2025 | Included in repo (`data/tournament_results.csv`) |

## Dependencies

```
pandas, numpy, requests, beautifulsoup4, scikit-learn, rich, typer
```

Python 3.12+ recommended.
