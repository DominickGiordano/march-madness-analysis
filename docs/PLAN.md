# March Madness Bracket Analyzer — Build Plan
**Status:** Ready to implement  
**Target:** Run tonight after 6pm ET bracket reveal (Selection Sunday, March 15, 2026)  
**Output:** Scored bracket picks, upset probabilities, Final Four + Champion prediction, exportable CSV/JSON

---

## What This Builds

A Python CLI tool that:
1. Ingests the 2026 bracket (manual JSON input after reveal tonight)
2. Pulls historical team efficiency data from free public sources
3. Scores every matchup using a weighted model trained on 20 years of tournament outcomes
4. Outputs: per-round picks, upset alerts, Final Four + Champion prediction, and exportable data

---

## Stack Decision

**Python** — no notebooks, clean CLI. Rationale:
- Best ecosystem for sports data (pandas, requests, scikit-learn)
- Portable — run from terminal, no Jupyter overhead
- Easy to re-run as rounds progress

**Dependencies:**
```
pandas
numpy
requests
beautifulsoup4
scikit-learn
rich          # pretty terminal output
typer         # CLI interface
```

---

## Data Sources (All Free)

| Source | What it provides | Access |
|---|---|---|
| [sports-reference.com/cbb](https://www.sports-reference.com/cbb/) | Historical season stats, SOS, W/L records 2004–2026 | Web scrape / CSV export |
| [barttorvik.com](https://barttorvik.com) | T-Rank (KenPom alternative) — AdjO, AdjD, Barthag, tempo, all free | Direct JSON/CSV API |
| [masseyratings.com](https://masseyratings.com) | Composite rankings, free historical exports | CSV |
| NCAA historical results | Seed vs. seed win rates 2006–2025 | Manual CSV (include in repo) |
| ESPN bracketology / NCAA.com | 2026 bracket seedings (post-reveal tonight) | Manual input |

**Primary analytics source: Barttorvik** — it's a free KenPom equivalent with a public API. Use this for AdjO/AdjD/Barthag for all current teams.

---

## Model Design

### Core Metrics (weighted, based on historical champion profile)

| Metric | Weight | Source | Why |
|---|---|---|---|
| AdjO rank (offensive efficiency) | 20% | Barttorvik | Champions: top 40 all-time |
| AdjD rank (defensive efficiency) | 25% | Barttorvik | Champions: top 25 all-time — defense > offense in tourney |
| Barthag (win probability vs avg D1) | 20% | Barttorvik | Best single-number team strength proxy |
| Seed | 15% | Bracket | Historical seed win rates are highly predictive |
| SOS (strength of schedule) | 10% | Barttorvik | Adjusts for conference strength |
| Recent momentum (last 10 games win%) | 10% | Sports-Reference | Hot teams win close games |

### Historical Calibration Data (include in `/data` folder)

Build a CSV with 20 years (2006–2025) of tournament results including:
- Team, seed, round reached, KenPom/T-Rank at time of tournament
- Use this to fit a logistic regression: P(team wins round) ~ f(metrics above)
- Weight recent seasons 2x (2019–2025) vs. older data

### Upset Detection Logic

Flag as **upset alert** when:
- Lower seed has Barthag > higher seed AND
- Seed differential ≥ 3 AND  
- Lower seed AdjD rank ≤ 35 (defense wins in single-elimination)

Classic upset seed combos to weight: 5-over-12, 10-over-7, 11-over-6

---

## Repo Structure

```
march-madness-analyzer/
├── README.md
├── requirements.txt
├── data/
│   ├── historical_results_2006_2025.csv    # seed, round, metrics — build this
│   ├── seed_win_rates.csv                   # 1v16, 2v15 etc. historical win %
│   └── 2026_bracket_template.json          # fill in tonight post-reveal
├── src/
│   ├── __init__.py
│   ├── fetch_data.py        # pulls Barttorvik + Sports-Reference data
│   ├── model.py             # logistic regression + scoring logic
│   ├── bracket.py           # bracket structure, matchup simulation
│   ├── upsets.py            # upset detection logic
│   └── output.py            # rich terminal display + CSV/JSON export
├── scripts/
│   └── build_historical_data.py   # one-time script to build historical CSV
└── main.py                  # CLI entrypoint
```

---

## CLI Interface

```bash
# Fetch current team data and score the bracket
python main.py run --bracket data/2026_bracket_template.json

# Output options
python main.py run --bracket data/2026_bracket.json --export csv
python main.py run --bracket data/2026_bracket.json --export json

# Show upset alerts only
python main.py upsets --bracket data/2026_bracket.json

# Show Final Four + Champion picks with confidence scores
python main.py champion --bracket data/2026_bracket.json
```

---

## Bracket JSON Input Format

Fill this in tonight after 6pm bracket reveal:

```json
{
  "regions": {
    "east": {
      "1": "Duke",
      "2": "...",
      ...
      "16": "..."
    },
    "west": { ... },
    "south": { ... },
    "midwest": { ... }
  }
}
```

The model resolves team names → Barttorvik slugs automatically.

---

## Output Format (Terminal)

```
╔══════════════════════════════════════════════════════╗
║         2026 MARCH MADNESS BRACKET ANALYZER          ║
╚══════════════════════════════════════════════════════╝

CHAMPION PREDICTION
  🏆  Duke (confidence: 68%)

FINAL FOUR
  Duke | Michigan | Florida | Houston

⚠️  UPSET ALERTS (watch these)
  R1: #11 Gonzaga over #6 Auburn — Barthag delta +0.08, AdjD rank 12
  R1: #10 Virginia over #7 Baylor — hot streak, last 10: 9-1
  R2: #5 Tennessee over #4 Iowa State — defensive mismatch

ROUND-BY-ROUND PICKS
  [Full bracket printed in ASCII bracket format]

CONFIDENCE SCORES
  [Table: team, seed, composite score, round predicted, upset flag]
```

---

## Implementation Phases

### Phase 1 — Data Layer (do first)
- [x] `fetch_data.py`: pull all 365 teams from Barttorvik JSON API (`/{year}_team_results.json`)
- [x] `build_historical_data.py`: built 18-year historical results CSV (2008–2025, 1082 records)
- [x] Validate team name → Barttorvik slug mapping (100% match rate via `fix_team_names.py`)
- [x] Momentum feature from Barttorvik fields 29/30/31 (recent-window Barthag)

### Phase 2 — Model
- [x] `model.py`: logistic regression trained on 2200 samples, 72% accuracy
- [x] Graceful feature degradation (trains on available columns, falls back to composite)
- [x] `upsets.py`: multi-factor upset detection with confidence scoring
- [x] `injuries.py`: Barthag penalty system (star/starter/rotation × out/questionable/limited)

### Phase 3 — Bracket Engine
- [x] `bracket.py`: deterministic tournament simulation (R64 → Champion)
- [x] Per-matchup win probability from logistic regression + composite
- [x] Monte Carlo engine: 10,000 simulations with random matchup resolution
- [x] Three bracket strategies: safe (favorites), balanced (selective upsets), risky (aggressive upsets)

### Phase 4 — Output + CLI
- [x] `output.py`: rich terminal display with probability bars, three brackets, advancement table
- [x] CSV/JSON export (`--export all` for three bracket CSVs)
- [x] `main.py` CLI with typer (run, upsets, champion commands)

---

## Key Historical Patterns to Encode

Based on 20-year data research:

- **#1 seeds**: Win ~40% of championships. Always viable Final Four pick.
- **Defense > offense**: Every champion since 2002 had top-25 AdjD. Non-negotiable filter.
- **Champion KenPom thresholds** (use as hard filter for champion picks):
  - AdjO rank ≤ 40
  - AdjD rank ≤ 25
- **8 vs 9**: ~50/50 — model should reflect this, don't force the 8
- **12 over 5**: Happens ~35% of the time — flag all 5-seeds with weak defenses
- **Momentum matters in R1**: Teams on 5+ win streaks entering tourney are 15% better in R1
- **Non-major conference Cinderellas**: Only make Elite 8+ if Barthag ≥ 0.85
- **Recent era weighting (2019–2025)**: Transfer portal era changed roster construction — upsets more common, weight these seasons 2x in model training

---

## Notes for Claude Code

- Use `rich` library for all terminal output — no bare prints
- All network calls should have retry logic + graceful fallbacks
- Barttorvik base URL: `https://barttorvik.com/2026_team_results.csv` (adjust year param)
- Sports-Reference has rate limiting — add `time.sleep(2)` between requests
- Build the historical CSV first before writing the model — the model is only as good as the training data
- The bracket JSON template should be human-fillable in 5 minutes post-reveal
- Validate that all 68 team names resolve before running — surface any lookup failures clearly
- Target: entire pipeline runs in < 60 seconds

---

## Tonight's Workflow

1. **6:00pm ET** — CBS Selection Sunday broadcast starts
2. **~6:30pm ET** — Bracket fully revealed
3. Fill in `data/2026_bracket.json` with all 68 teams + seeds (~5 min)
4. `python main.py run --bracket data/2026_bracket.json --export csv`
5. Review upset alerts + champion pick
6. Fill out bracket

---
*Generated: March 15, 2026 | Selection Sunday*