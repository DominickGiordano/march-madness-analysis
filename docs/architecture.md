# Architecture — March Madness Bracket Analyzer

> Reference with @docs/architecture.md when relevant.
> Not loaded every session — only when needed.

## Overview
Two-tier system: **Python CLI** (data, model, simulation) + **React SPA** (interactive visualization).

```
[Bracket JSON] → fetch_data.py → injuries.py → model.py → bracket.py → output.py
                      ↑                ↑            ↑           ↑           |
               Barttorvik API    injuries.json   Historical  10,000 sims   |
               (live metrics +                   CSV (logreg)              |
                momentum)                                          ┌──────┴──────┐
                                                                   │             │
                                                              Terminal      ui-export
                                                              (rich)           |
                                                                        bracket-data.json
                                                                               |
                                                                        React SPA (Vite)
                                                                        localhost:5173
                                                                               |
                                                              ┌────────────────┼────────────┐
                                                              │                │             │
                                                         Strategy        Click-to-      Probability
                                                          Toggle         Override        Matrix
                                                       safe/bal/risky   + Cascade      (11k entries)
```

## Key Design Decisions
| Decision | Rationale | Date |
|----------|-----------|------|
| Monte Carlo over deterministic | Captures variance — a 55% favorite loses 45% of the time. Enables safe/risky strategies. | 2026-03-15 |
| React SPA with pre-computed JSON | No backend needed. Ship 11k probabilities to browser for instant overrides. | 2026-03-15 |
| Blended model (60% logreg + 40% composite) | Ensures injuries (Barthag adjustments) always affect predictions, even in trained model path. | 2026-03-15 |
| Locked matchups at >90% confidence | Prevents users from wasting time overriding near-certain matchups (1v16, 2v15). | 2026-03-15 |
| Barttorvik as sole data source | Free KenPom equivalent with public JSON API. Sports-Reference has CloudFlare blocking. | 2026-03-15 |
| Explicit Final Four pairings | `get_ff_pairings()` uses region names (East vs West, South vs Midwest) instead of relying on JSON key order. | 2026-03-15 |
| Three bracket strategies | Safe (maximize correct picks), Balanced (bracket pool optimized), Risky (high ceiling) | 2026-03-15 |
| Manual injuries JSON | No free structured injury API for college basketball. Fuzzy name matching handles naming inconsistencies. | 2026-03-15 |
| Momentum from Barttorvik fields 29-31 | Recent-window Barthag vs season Barthag captures hot/cold streaks without scraping game logs | 2026-03-15 |

## Data Flow — Python Pipeline

1. **Input**: User provides `2026_bracket.json` with 64 teams + seeds by region
2. **fetch_data.py**: Pulls from `https://barttorvik.com/2026_team_results.json` — 45 fields per team including AdjO (field 4), AdjD (field 6), Barthag (field 8), recent-window AdjO/AdjD/Barthag (fields 29/30/31). Computes momentum as `recent_barthag / season_barthag`.
3. **injuries.py**: Loads `data/injuries.json`, filters to actionable entries (skips `_comment` dividers, `verified_clean` entries, null players). Fuzzy-matches team names. Applies multiplicative Barthag penalties.
4. **model.py**: Blended prediction = 60% logistic regression + 40% weighted composite. Logreg trained on `data/historical_results_2008_2025.csv` (1082 records, expands to ~2200 training samples). Composite uses all features including injury-adjusted Barthag and momentum.
5. **bracket.py — MonteCarloSimulator**: Runs 10,000 full tournament simulations. Each matchup resolved randomly based on blended win probability. Caches pairwise probabilities in `_prob_cache`.
6. **bracket.py — MonteCarloResults**: Builds three brackets from simulation data using different upset thresholds per strategy.
7. **output.py — terminal**: Renders probability bars, three brackets, advancement table.
8. **output.py — `export_ui_json()`**: Serializes probability matrix (all team pairs × 6 rounds), three strategy brackets, team metrics, upset alerts, and advancement probabilities. Flags matchups >90% as `locked`.

## Data Flow — React UI

1. **useBracketData.ts**: Fetches `bracket-data.json` on mount
2. **useBracketState.ts**: Manages active strategy, override map, and computed bracket
3. **StrategyToggle**: Switches strategy → resets overrides → loads pre-computed bracket
4. **Matchup click**: User clicks losing team → triggers override → cascade.ts walks forward through bracket tree → looks up new pairwise probabilities from shipped `probMatrix` → updates all downstream matchups
5. **Locked matchups**: `locked: true` matchups are greyed out, no click handler

### Cascade Recalculation Logic (`cascade.ts`)
When a user overrides a matchup winner:
1. Set the new winner for that matchup
2. Walk forward through the bracket tree — for each downstream matchup that included the LOSER, replace with the WINNER
3. Look up new pairwise probability from `probMatrix` (try both key orderings: `"A|B|round"` and `"B|A|round"`)
4. Update win probabilities for all affected matchups
5. Propagate through Final Four and Championship if affected

The probability matrix has ~11,000 entries (all team pairs × 6 rounds), making any override scenario instantly computable client-side.

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

### Blended Prediction
```
final_probability = 0.6 × logreg_prediction + 0.4 × composite_prediction
```
- **Logreg path**: Predicts P(advance) for each team independently, normalizes to head-to-head
- **Composite path**: Direct metric comparison using weighted features including injury-adjusted Barthag
- Blending ensures injuries always affect predictions (logreg doesn't see Barthag adjustments directly)

### Champion Hard Filters
Teams eliminated from champion contention unless: AdjO rank ≤ 40 AND AdjD rank ≤ 25. Every champion since 2002 has met these.

### Upset Detection
Multi-factor confidence scoring combining: Barthag delta, seed differential, defensive strength, historical volatility (5v12, 7v10, 6v11), and win streak momentum.

### Injury Model
- Multiplicative Barthag penalties: Star out = 0.92x, Starter out = 0.96x, Rotation out = 0.98x
- Questionable/limited have smaller penalties
- Fuzzy name matching (e.g., "UConn" → "Connecticut")
- `verified_clean` entries track researched-but-healthy teams
- `_comment` dividers organize by conference

## Known Limitations
- [x] ~~Barttorvik URL pattern may change year-to-year~~ — Confirmed working 2008–2026
- [x] ~~Team name mapping needs manual corrections~~ — 100% match rate
- [x] ~~Model doesn't account for injuries~~ — Full injury system implemented
- [x] ~~No interactive visualization~~ — React UI with click-to-override
- [ ] No play-in game handling (First Four) — winners entered manually
- [ ] Injury penalties are rough estimates, not derived from data
- [ ] No coaching matchup or style-of-play adjustments
- [ ] Momentum feature not in historical data (composite only, not in logreg)
- [ ] UI is desktop-only (1440px+)
