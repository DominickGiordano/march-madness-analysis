# March Madness Bracket Analyzer

Python CLI + interactive React UI that runs **up to 1,000,000 Monte Carlo simulations** of the NCAA tournament. Generates **15 bracket variants** across three risk tiers (safe, balanced, risky) with champion probabilities, upset alerts, injury adjustments, tempo/style matchup analysis, and full advancement odds. The web UI lets you flip through all 15 variants, override picks, and watch confidence cascade in real time.

## Prerequisites

- **Python 3.12+** with pip
- **Node.js 18+** with npm

## Setup (first time only)

```bash
# Clone and enter the project
git clone <repo-url>
cd march-madness-analysis

# Install Python dependencies
pip install -r requirements.txt

# Install UI dependencies
cd ui && npm install && cd ..

# Build historical training data (~20 seconds)
python scripts/build_historical_data.py
```

## Running the Analysis

### Option A: Interactive Web UI (recommended)

```bash
# 1. Run simulations and generate UI data
#    Use --sims 10000 for quick results (~15s)
#    Use --sims 1000000 for production accuracy (~5 min)
python main.py ui-export --bracket data/2026_bracket.json --sims 1000000

# 2. Start the web UI
cd ui && npm run dev

# 3. Open in browser
open http://localhost:5173
```

To stop the UI server: `Ctrl+C` in the terminal running `npm run dev`.

To re-run with updated injuries or a new bracket:
```bash
# Edit data/injuries.json or data/2026_bracket.json, then:
python main.py ui-export --bracket data/2026_bracket.json --sims 1000000
# UI hot-reloads automatically if dev server is running
```

### Option B: Terminal output

```bash
# Full analysis with 3 bracket strategies
python main.py run --bracket data/2026_bracket.json --sims 10000

# Export all three brackets as CSVs
python main.py run --bracket data/2026_bracket.json --export all

# Upset alerts only
python main.py upsets --bracket data/2026_bracket.json

# Champion probability deep dive
python main.py champion --bracket data/2026_bracket.json --sims 10000
```

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--bracket` | required | Path to bracket JSON file |
| `--sims` | 10000 | Number of Monte Carlo simulations (use 1000000 for best accuracy) |
| `--export` | none | `csv`, `json`, or `all` (exports safe/balanced/risky CSVs) |
| `--no-train` | false | Skip logistic regression, use weighted composite only |
| `--injuries-file` | `data/injuries.json` | Path to injuries JSON |

## Interactive Web UI

The UI is a React SPA that loads pre-computed simulation data. No backend server needed — all interaction is client-side.

**15 Bracket Variants** — 5 per risk tier, ordered safest to riskiest:

| Tier | Variants | Upsets | Color | Description |
|------|----------|--------|-------|-------------|
| **Safe** (1–5) | Ultra Safe → Safe Aggressive | 6–9 | Greens | Mostly favorites, only obvious upsets |
| **Balanced** (6–10) | Conservative → Aggressive | 9–24 | Ambers | Selective upsets backed by statistics |
| **Risky** (11–15) | Mild Risk → Max Risk | 16–31 | Reds | Aggressive underdog picks for pool differentiation |

**UI Features:**
- **Variant selector** — 15 color-coded pills, click to load any bracket instantly
- **Click-to-override** — click any matchup to pick a different winner. Confidence cascades through all downstream rounds.
- **Locked matchups** — games with >90% model confidence are locked (1v16 blowouts, etc.)
- **Visual confidence** — win probability on every matchup, color-coded green/amber/red
- **Seed badges** — color-coded by tier (1–4 blue, 5–8 grey, 9–12 orange, 13–16 red)
- **Upset indicators** — orange borders on upset picks, pencil icon on manual overrides
- **Champion banner** — current pick, confidence %, variant label, Final Four, upset count
- **Upset alerts** — collapsible section with multi-factor upset reasoning

The full probability matrix (12,000+ pairwise matchup probabilities) is shipped to the browser, so overrides recalculate instantly.

## How It Works

```
Bracket JSON --> fetch_data.py --> injuries.py --> model.py --> bracket.py --> output.py
                      |                |              |              |              |
               Barttorvik API    injuries.json   Historical    Monte Carlo    Terminal / CSV
               (live metrics +                   CSV (logreg)   (up to 1M)         |
                tempo, WAB,                                      sims          ui-export
                momentum)                                         |                |
                                                            15 bracket      bracket-data.json
                                                             variants             |
                                                                           React UI (Vite)
                                                                          localhost:5173
```

1. Fill in bracket JSON with teams + seeds after Selection Sunday
2. Tool pulls live efficiency metrics from [Barttorvik](https://barttorvik.com) (free, no auth)
3. Injuries reduce affected teams' Barthag ratings (manual input in `injuries.json`)
4. Blended model (60% logistic regression + 40% composite) scores every matchup
5. Matchup adjustments: tempo mismatch boost, seed history anchor
6. Monte Carlo engine runs up to 1M tournaments, randomly resolving each matchup
7. 15 bracket variants built by sliding upset thresholds across three risk tiers
8. Results render in terminal OR export as JSON for the interactive web UI

## Filling In the Bracket

Edit `data/2026_bracket.json` (or `data/2026_bracket_template.json` as a starting point):

```json
{
  "regions": {
    "east": { "1": "Duke", "2": "Connecticut", ... "16": "Siena" },
    "west": { "1": "Arizona", "2": "Purdue", ... "16": "LIU" },
    "south": { "1": "Florida", "2": "Houston", ... "16": "Prairie View A&M" },
    "midwest": { "1": "Michigan", "2": "Iowa St.", ... "16": "UMBC" }
  }
}
```

Team names must match [Barttorvik](https://barttorvik.com) conventions. Common gotchas:
- "Connecticut" not "UConn"
- "North Carolina" not "UNC"
- "Iowa St." not "Iowa State" (period after St)
- "Miami FL" not "Miami (FL)"

The tool flags any names it can't resolve.

## Injuries

Edit `data/injuries.json` to account for injured, suspended, or arrested players:

```json
{
  "injuries": [
    {
      "team": "Alabama",
      "player": "Aden Holloway",
      "impact": "star",
      "status": "out",
      "note": "Arrested — felony drug charge. Off team."
    }
  ]
}
```

| Impact | Barthag Penalty | Description |
|--------|----------------|-------------|
| `star` | -8% (out), -4% (questionable), -3% (limited) | Top 1–2 player on the team |
| `starter` | -4% (out), -2% (questionable), -1% (limited) | Regular starter |
| `rotation` | -2% (out), -1% (questionable), 0% (limited) | Bench contributor |

Multiple injuries stack multiplicatively. The file supports:
- `verified_clean: true` — teams confirmed healthy after research
- `_comment` dividers — organize by conference
- Fuzzy name matching — "UConn" auto-matches to "Connecticut"

## Model

**Blended prediction**: 60% logistic regression (trained on 1082 tournament records, 2008–2025) + 40% weighted composite (uses injury-adjusted Barthag).

**Features:**

| Feature | Source | Why |
|---------|--------|-----|
| AdjD rank | Barttorvik | Defense wins in March — every champ since 2002 had top-25 AdjD |
| AdjO rank | Barttorvik | Offensive efficiency |
| Barthag | Barttorvik | Overall team strength (win prob vs avg D1 team) |
| Seed | Bracket | Historical seed win rates are highly predictive |
| WAB | Barttorvik | Wins Above Bubble — resume quality |
| Momentum | Barttorvik | Recent-window Barthag vs season Barthag (hot/cold streaks) |
| Win % | Barttorvik | Overall record |
| SOS | Barttorvik | Strength of schedule |
| eFG ratio | Barttorvik | Shooting efficiency edge |

**Matchup adjustments:**
- **Tempo mismatch** — slow defensive teams get up to +3% win boost against fast teams (they control pace, reduce possessions, increase variance)
- **Seed history anchor** — predictions blended 85/15 with historical seed-vs-seed upset rates (5v12 at 35%, 8v9 at 50%, etc.)

**Champion hard filters:** AdjO rank ≤ 40 AND AdjD rank ≤ 25 (every champion since 2002 meets these)

## Project Structure

```
march-madness-analysis/
├── main.py                          # CLI entrypoint (typer)
├── requirements.txt                 # Python dependencies
├── data/
│   ├── 2026_bracket.json            # Current bracket (filled in)
│   ├── 2026_bracket_template.json   # Blank template
│   ├── injuries.json                # Manual injury/suspension entries
│   ├── tournament_results.csv       # Historical results 2008–2025
│   └── historical_results_2008_2025.csv  # Merged with Barttorvik metrics
├── src/
│   ├── fetch_data.py                # Barttorvik API (metrics, tempo, WAB, momentum)
│   ├── model.py                     # Blended logreg + composite + matchup adjustments
│   ├── bracket.py                   # Monte Carlo engine + 15 variant builder
│   ├── upsets.py                    # Multi-factor upset detection
│   ├── injuries.py                  # Barthag penalties + fuzzy name matching
│   └── output.py                    # Terminal display + CSV/JSON/UI export
├── ui/                              # Interactive bracket visualization (React + Vite)
│   ├── src/
│   │   ├── App.tsx                  # Shell — loads data, renders everything
│   │   ├── types.ts                 # TypeScript interfaces
│   │   ├── hooks/
│   │   │   ├── useBracketData.ts    # Loads bracket-data.json
│   │   │   └── useBracketState.ts   # Variant selection, overrides, cascade
│   │   ├── lib/
│   │   │   └── cascade.ts           # Client-side override cascade recalculation
│   │   └── components/
│   │       ├── Bracket.tsx           # Full tournament layout (4 regions + FF)
│   │       ├── Region.tsx            # Single region (R64–E8)
│   │       ├── Matchup.tsx           # Matchup card (click-to-override)
│   │       ├── VariantSelector.tsx   # 15 color-coded variant pills
│   │       ├── ChampionBanner.tsx    # Champion + Final Four display
│   │       └── UpsetAlerts.tsx       # Collapsible upset alerts
│   └── public/data/                 # bracket-data.json (generated by CLI)
├── scripts/
│   ├── build_historical_data.py     # One-time: build training dataset
│   └── fix_team_names.py            # One-time: normalize names to Barttorvik
└── docs/
    ├── PLAN.md                      # Original build plan
    └── architecture.md              # System architecture
```

## Data Sources

| Source | What | Access |
|--------|------|--------|
| [Barttorvik](https://barttorvik.com) | AdjO, AdjD, Barthag, SOS, tempo, WAB, momentum | Free JSON API (`/{year}_team_results.json`) |
| Historical tournament results | Seeds, round reached, 2008–2025 | Included in repo (`data/tournament_results.csv`) |

## Dependencies

**Python:** `pandas, numpy, requests, beautifulsoup4, scikit-learn, rich, typer` — Python 3.12+

**UI:** `react, typescript, vite` — Node 18+ (`cd ui && npm install`)
