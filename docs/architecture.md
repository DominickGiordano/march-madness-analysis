# Architecture — March Madness Bracket Analyzer

> Reference with @docs/architecture.md when relevant.
> Not loaded every session — only when needed.

## Overview
CLI pipeline with 5 stages: **Data Fetch → Injury Adjust → Model Score → Monte Carlo Simulate → Output**.

```
[Bracket JSON] → fetch_data.py → injuries.py → model.py → bracket.py → output.py
                      ↑                ↑            ↑           ↑
               Barttorvik API    injuries.json   Historical  10,000 sims
               (live metrics +                   CSV (logreg)  ↓
                momentum)                                   3 brackets:
                                                           safe / balanced / risky
```

User fills in bracket JSON after Selection Sunday reveal. The tool:
1. Resolves team names to Barttorvik names
2. Pulls current-season efficiency metrics + momentum
3. Applies injury-based Barthag penalties
4. Scores every matchup using logistic regression (trained on 1082 tournament records, 2008–2025)
5. Runs 10,000 Monte Carlo simulations, randomly resolving each matchup based on win probabilities
6. Builds three bracket strategies from simulation results
7. Renders champion probabilities, Final Four odds, upset alerts, and full advancement table

## Key Design Decisions
| Decision | Rationale | Date |
|----------|-----------|------|
| Monte Carlo over deterministic | Captures variance — a 55% favorite loses 45% of the time. Enables safe/risky strategies. | 2026-03-15 |
| Barttorvik as sole data source | Free KenPom equivalent with public JSON API. Sports-Reference has CloudFlare blocking. | 2026-03-15 |
| Logistic regression over complex ML | Interpretable, fast, works with 6 features and ~1000 training samples | 2026-03-15 |
| Three bracket strategies | Safe (maximize correct picks), Balanced (bracket pool optimized), Risky (high ceiling) | 2026-03-15 |
| Manual injuries JSON | No free structured injury API for college basketball. Manual input is most reliable. | 2026-03-15 |
| Momentum from Barttorvik fields 29-31 | Recent-window Barthag vs season Barthag captures hot/cold streaks without scraping game logs | 2026-03-15 |
| Rich + Typer for CLI | Rich handles probability bars and tables, Typer gives clean CLI UX | 2026-03-15 |
| Manual bracket JSON input | Human-fillable in 5 min post-reveal, no fragile bracket scraping | 2026-03-15 |

## Data Flow

1. **Input**: User provides `2026_bracket.json` with 64 teams + seeds by region
2. **fetch_data.py**: Pulls from `https://barttorvik.com/2026_team_results.json` — 45 fields per team including AdjO (field 4), AdjD (field 6), Barthag (field 8), recent-window AdjO/AdjD/Barthag (fields 29/30/31). Computes momentum as `recent_barthag / season_barthag`.
3. **injuries.py**: Loads `data/injuries.json`, filters to actionable entries (skips `_comment` dividers, `verified_clean` entries, null players). Applies multiplicative Barthag penalties: star out = 0.92x, starter out = 0.96x, etc.
4. **model.py**: Logistic regression trained on `data/historical_results_2008_2025.csv` (1082 records). Features: AdjO rank, AdjD rank, Barthag, seed, win%. Trains on available features (gracefully handles missing columns). Falls back to weighted composite if training fails.
5. **bracket.py — MonteCarloSimulator**: Runs 10,000 full tournament simulations. Each matchup resolved randomly based on model's win probability. Tracks champion counts, Final Four counts, per-matchup win frequencies, per-team advancement distributions.
6. **bracket.py — MonteCarloResults**: Builds three brackets from simulation data:
   - **Safe**: always picks the higher-probability team
   - **Balanced**: picks upsets at >40% (R64/R32), >43% (S16/E8), >47% (F4+)
   - **Risky**: picks any underdog with >35% win probability
7. **output.py**: Renders probability bars for champion/F4, three full brackets with upset counts, advancement probability table (S16/E8/F4/Champ %), and exports to CSV/JSON.

## External Dependencies
| Service | Purpose | Endpoint |
|---------|---------|----------|
| Barttorvik | Team efficiency metrics, momentum, rankings | `https://barttorvik.com/{year}_team_results.json` |

No other external dependencies. Historical data and injuries are local files.

## Model Details

### Training Data
- 18 years of tournament results (2008–2025, excluding 2020 COVID)
- 1082 team records matched to Barttorvik metrics
- Features: AdjO rank, AdjD rank, Barthag, seed, win%
- Target: binary (advanced to next round / eliminated)
- Recent era (2019–2025) weighted 2x via sample weights
- Training creates one row per round played per team (expands to ~2200 samples)

### Champion Hard Filters
Teams are eliminated from champion contention unless:
- AdjO rank ≤ 40
- AdjD rank ≤ 25

Every champion since 2002 has met these thresholds.

### Upset Detection Triggers
- Lower seed Barthag > higher seed Barthag
- Seed differential ≥ 3
- Lower seed AdjD rank ≤ 35
- Higher seed has weak defense relative to seeding (AdjD rank > 50 for seeds ≤ 6)
- Historically volatile matchup (5v12 at 35%, 7v10 at 40%, 6v11 at 37%, 8v9 at 50%)
- Multi-factor confidence score combining all signals

### Injury Model
- Multiplicative Barthag penalties by player importance and availability
- Star out: -8%, Starter out: -4%, Rotation out: -2%
- Questionable/limited have smaller penalties
- Multiple injuries on same team compound (star out + starter questionable = 0.92 × 0.98)
- Injuries file supports `verified_clean` entries for tracking researched-but-healthy teams

## Known Limitations
- [x] ~~Barttorvik URL pattern may change year-to-year~~ — Confirmed working 2008–2026
- [x] ~~Team name mapping needs manual corrections~~ — `fix_team_names.py` handles this, 100% match rate
- [x] ~~Model doesn't account for injuries~~ — Full injury system implemented
- [ ] No play-in game handling (First Four) — winners entered manually
- [ ] Injury penalties are rough estimates, not derived from data
- [ ] No coaching matchup or style-of-play adjustments
- [ ] Single-game variance is inherently high — probabilities are directional
- [ ] Momentum feature not available in historical data (only current season)
