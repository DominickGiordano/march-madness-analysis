# March Madness Bracket Analyzer

Python CLI + interactive React UI that runs **10,000 Monte Carlo simulations** of the 2026 NCAA tournament. Produces three bracket strategies (safe, balanced, risky) with champion probabilities, upset alerts, and full advancement odds. The web UI lets you flip between strategies, override picks, and watch confidence cascade in real time.

## Quick Start

```bash
pip install -r requirements.txt

# Build historical training data (one-time, ~20s)
python scripts/build_historical_data.py

# Option A: Terminal output
python main.py run --bracket data/2026_bracket.json

# Option B: Interactive web UI (recommended)
python main.py ui-export --bracket data/2026_bracket.json --sims 10000
cd ui && npm install && npm run dev
# Open http://localhost:5173
```

### CLI Commands

| Command | What it does |
|---------|-------------|
| `python main.py run --bracket <file>` | Full Monte Carlo analysis in terminal |
| `python main.py run --bracket <file> --export all` | Export safe/balanced/risky CSVs |
| `python main.py upsets --bracket <file>` | Upset alerts only |
| `python main.py champion --bracket <file>` | Champion probability deep dive |
| `python main.py ui-export --bracket <file>` | Export JSON for the web UI |

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--bracket` | required | Path to bracket JSON file |
| `--sims` | 10000 | Number of Monte Carlo simulations |
| `--export` | none | `csv`, `json`, or `all` (exports safe/balanced/risky CSVs) |
| `--no-train` | false | Skip logistic regression, use weighted composite only |
| `--injuries-file` | `data/injuries.json` | Path to injuries JSON |

## Interactive Web UI

The UI is a React SPA that loads pre-computed simulation data — no backend server needed.

```bash
# Generate the data
python main.py ui-export --bracket data/2026_bracket.json --sims 10000

# Start the UI
cd ui && npm run dev
# Open http://localhost:5173
```

**Features:**
- **Strategy toggle** — flip between Safe, Balanced, and Risky brackets
- **Click-to-override** — click any matchup to pick a different winner. Confidence levels cascade through downstream rounds instantly.
- **Locked matchups** — games where the model is >90% confident are locked and can't be overridden (1v16 blowouts, etc.)
- **Visual confidence** — every matchup shows win probability, color-coded green (>70%), amber (50–70%), red (<50%)
- **Seed badges** — color-coded by tier (1–4 blue, 5–8 grey, 9–12 orange, 13–16 red)
- **Upset indicators** — orange borders on upset picks, pencil icon on manual overrides
- **Champion banner** — current champion pick, confidence %, Final Four with advancement odds
- **Upset alerts** — collapsible section with multi-factor upset analysis
- **Full bracket layout** — 4 regions converging to Final Four + Championship in the center

The entire probability matrix (11,000+ pairwise matchup probabilities) is shipped to the browser, so overrides recalculate instantly — no round-trips to the server.

## How It Works

```
Bracket JSON --> fetch_data.py --> injuries.py --> model.py --> bracket.py --> output.py
                      |                |              |              |              |
               Barttorvik API    injuries.json   Historical    Monte Carlo    Terminal / CSV
               (live metrics)                    CSV (logreg)   (10k sims)         |
                                                                               ui-export
                                                                                   |
                                                                           bracket-data.json
                                                                                   |
                                                                            React UI (Vite)
                                                                           localhost:5173
```

1. Fill in `data/2026_bracket_template.json` with 68 teams + seeds after Selection Sunday (~5 min)
2. Tool pulls current-season efficiency metrics from [Barttorvik](https://barttorvik.com) (free, no auth)
3. Logistic regression trained on 18 years of tournament data (2008–2025, 1082 teams) scores every matchup
4. Injuries reduce affected teams' Barthag ratings before scoring
5. Monte Carlo engine runs 10,000 tournaments, randomly resolving each matchup based on win probabilities
6. Three bracket strategies are built from the simulation results
7. Results render in terminal OR export as JSON for the interactive web UI

### Three Bracket Strategies

| Strategy | What it does | Upsets | Best for |
|----------|-------------|--------|----------|
| **Safe** | Always picks the favorite | ~13 | Maximizing correct picks |
| **Balanced** | Picks upsets at >40–47% probability (tighter in later rounds) | ~23 | Most bracket pools |
| **Risky** | Picks any underdog with >35% win probability | ~28 | High ceiling, differentiation |

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

Multiple injuries stack multiplicatively. The file also supports `verified_clean` entries for teams confirmed healthy and `_comment` dividers for organization. The tool auto-loads `data/injuries.json` and fuzzy-matches team names (e.g., "UConn" matches "Connecticut").

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Monte Carlo over deterministic | 10k simulations capture variance — a 55% favorite loses 45% of the time |
| React SPA with pre-computed JSON | No backend needed. 11k probabilities in the browser = instant overrides |
| Locked matchups at >90% confidence | Don't waste time overriding 1v16 games |
| Blended model (60% logreg + 40% composite) | Ensures injuries always affect predictions, even when logreg is trained |
| Barttorvik as sole data source | Free KenPom equivalent with public JSON API, no auth needed |
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
│   └── output.py                    # Terminal display + CSV/JSON/UI export
├── ui/                              # Interactive bracket visualization
│   ├── src/
│   │   ├── App.tsx                  # Shell — loads data, renders everything
│   │   ├── types.ts                 # TypeScript interfaces for data schema
│   │   ├── hooks/
│   │   │   ├── useBracketData.ts    # Loads bracket-data.json
│   │   │   └── useBracketState.ts   # Strategy, overrides, cascade state
│   │   ├── lib/
│   │   │   └── cascade.ts           # Override cascade recalculation
│   │   └── components/
│   │       ├── Bracket.tsx           # Full tournament layout
│   │       ├── Region.tsx            # Single region (R64–E8)
│   │       ├── Matchup.tsx           # Matchup card with click-to-override
│   │       ├── StrategyToggle.tsx    # Safe/Balanced/Risky toggle
│   │       ├── ChampionBanner.tsx    # Champion + Final Four display
│   │       └── UpsetAlerts.tsx       # Collapsible upset alerts
│   └── public/data/                 # bracket-data.json generated by CLI
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

**Python:** `pandas, numpy, requests, beautifulsoup4, scikit-learn, rich, typer` — Python 3.12+

**UI:** `react, typescript, vite` — Node 18+ (`cd ui && npm install`)
