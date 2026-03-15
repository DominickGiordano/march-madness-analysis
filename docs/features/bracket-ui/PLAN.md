# Plan: Bracket UI

**Status**: Draft
**Created**: 2026-03-15
**Last updated**: 2026-03-15

## Summary
Build an interactive React SPA that visualizes the March Madness bracket analyzer output. Users can toggle between safe/balanced/risky strategies, click any matchup to override the winner (with cascading recalculation), and see confidence levels on every game. The app reads a pre-computed JSON blob from the Python CLI -- no backend server needed. This needs to ship by Wednesday March 18.

## Approach
Option 1 from the brainstorm: Vite + React SPA with pre-computed JSON. The Python side exports a "fat JSON" containing all three bracket strategies, the full pairwise probability matrix, team metrics, upset alerts, and advancement probabilities. The React app loads this at startup and does all interaction client-side, including cascade recalculation using the shipped probability matrix. See `docs/features/bracket-ui/BRAINSTORM.md` for the full option analysis.

## Affected Files / Components
| File / Component | Change | Why |
|-----------------|--------|-----|
| `src/output.py` | Add `export_ui_json()` function | Serialize all simulation data to a single JSON for the frontend |
| `main.py` | Add `ui-export` CLI command | One-command way to generate the UI data file |
| `ui/` | New Vite + React + TypeScript project | Entire frontend app |
| `ui/src/types.ts` | TypeScript interfaces for the JSON schema | Shared contract between Python export and frontend |
| `ui/src/components/Bracket.tsx` | Main bracket layout (4 regions + Final Four) | Core visualization |
| `ui/src/components/Region.tsx` | Single region bracket (R64 through E8) | Reusable region component |
| `ui/src/components/Matchup.tsx` | Single matchup card with click-to-override | Atomic interaction unit |
| `ui/src/components/StrategyToggle.tsx` | Safe/Balanced/Risky segmented control | Strategy switching |
| `ui/src/components/ChampionBanner.tsx` | Champion + Final Four probability display | Top-level summary |
| `ui/src/hooks/useBracketState.ts` | Bracket state, overrides, active strategy | Central state management |
| `ui/src/lib/cascade.ts` | Client-side cascade recalculation logic | Propagate manual overrides forward through the bracket tree |
| `ui/src/lib/types.ts` | Shared TypeScript types | Keep types co-located |

## Implementation Steps

### Phase 1: Python Data Export (Day 1 morning, ~2 hours)
- [ ] **Step 1** -- Define the UI JSON schema. Document the exact shape of the output JSON before writing code. Key sections: `bracket` (original seeding), `strategies` (three pre-built brackets), `probMatrix` (all pairwise win probabilities keyed as `"TeamA|TeamB|round" -> float`), `teamData` (metrics per team), `upsetAlerts`, `advancement` (champion/FF/E8 probabilities per team), `meta` (n_sims, timestamp).
- [ ] **Step 2** -- Implement `export_ui_json(mc_results, team_data, upset_alerts, output_path)` in `src/output.py`. This function builds the fat JSON from a `MonteCarloResults` instance. The probability matrix comes from iterating `mc_results._prob_cache` (the `MonteCarloSimulator`'s cache of model-level pairwise probabilities -- this is the clean model prediction, not the noisy MC frequency). Also include MC-observed frequencies from `matchup_wins`/`matchup_total` for display.
- [ ] **Step 3** -- Add a `ui-export` command to `main.py` that runs the simulation and calls `export_ui_json`. Output to `ui/public/data/bracket-data.json` so Vite serves it as a static asset. Wire it up: `python main.py ui-export --bracket data/2026_bracket_test.json --sims 10000`.
- [ ] **Step 4** -- Run the export, validate the JSON looks right, commit.

### Phase 2: Frontend Scaffolding (Day 1 afternoon, ~2 hours)
- [ ] **Step 5** -- Scaffold the Vite project: `cd ui && npm create vite@latest . -- --template react-ts`. Add strict TypeScript config (`"strict": true`, `"noUncheckedIndexedAccess": true`). Install Tailwind CSS (utility classes are fastest for layout iteration on a deadline).
- [ ] **Step 6** -- Define TypeScript types in `ui/src/types.ts` matching the JSON schema from Step 1. All interfaces, no `any`.
- [ ] **Step 7** -- Create `ui/src/hooks/useBracketData.ts` -- loads `bracket-data.json` from `/data/bracket-data.json` on mount. Returns typed data or loading/error states.
- [ ] **Step 8** -- Build the `App.tsx` shell: loads data, renders `StrategyToggle` + `Bracket` + `ChampionBanner`. Verify it loads and displays team names. Commit.

### Phase 3: Bracket Visualization (Day 1 evening + Day 2 morning, ~5 hours -- this is the hard part)
- [ ] **Step 9** -- Build `Region.tsx` using CSS Grid. Layout: 4 columns (R64, R32, S16, E8), 8 rows for R64 matchups, collapsing as rounds progress. Each cell is a `Matchup` component. Use flexbox for vertical centering of matchup cards between their "parent" matchups. Start with one region, get it pixel-perfect, then replicate.
- [ ] **Step 10** -- Build `Matchup.tsx`. Shows two teams, seed numbers, winner highlighted, confidence percentage, and upset indicator (colored dot or border). Clickable -- clicking a team selects them as the override winner. Color-code confidence: green (>70%), amber (50-70%), red (<50%).
- [ ] **Step 11** -- Build `Bracket.tsx` -- full tournament layout. Four regions arranged in the classic bracket shape: two regions on the left (top-left and bottom-left converge to left Final Four slot), two on the right (mirrored). Final Four and Championship in the center. This is a CSS Grid with the regions as quadrants and the center column for FF/Championship.
- [ ] **Step 12** -- Build `ChampionBanner.tsx`. Shows current champion pick, their championship probability, and Final Four teams with advancement percentages. Updates reactively when strategy or overrides change.
- [ ] **Step 13** -- Visual polish pass: team colors by seed tier (1-4 blue, 5-8 gray, 9-12 orange, 13-16 red), upset picks get a dashed border, hover tooltip showing team metrics (Barthag, AdjO rank, AdjD rank, seed, win%). Commit.

### Phase 4: Interactivity (Day 2, ~3 hours)
- [ ] **Step 14** -- Build `useBracketState.ts`. State shape: `{ activeStrategy: 'safe' | 'balanced' | 'risky', overrides: Map<matchupId, teamName>, computedBracket: BracketData }`. When strategy changes, reset overrides and load the pre-computed bracket for that strategy. When an override is added, trigger cascade recalculation.
- [ ] **Step 15** -- Build `StrategyToggle.tsx`. Three-way segmented control. Switching strategies resets all manual overrides (with a confirmation if overrides exist).
- [ ] **Step 16** -- Build `ui/src/lib/cascade.ts`. When a user overrides a matchup winner: (1) set the winner for that matchup, (2) walk forward through the bracket tree -- for each downstream matchup that included the loser, replace them with the override winner, (3) for each affected matchup, look up the new pairwise probability from the probability matrix and update confidence display. The bracket tree structure is deterministic (matchup N feeds into matchup N/2 in the next round), so the walk is straightforward.
- [ ] **Step 17** -- Wire click-to-override into `Matchup.tsx`. Clicking a team triggers the override in `useBracketState`, which triggers cascade, which updates the rendered bracket. Add visual indicator for manually overridden matchups (e.g., a small pencil icon or different background).
- [ ] **Step 18** -- Add "Reset overrides" button. Add "Reset to strategy default" per-region. Commit.

### Phase 5: Final Polish (Day 2 evening, ~1 hour)
- [ ] **Step 19** -- Upset alerts sidebar or banner at the top. List the top upset alerts from the JSON with their reasons and confidence scores.
- [ ] **Step 20** -- Responsive check -- make sure it works at 1440px+ (this is a desktop tool, don't burn time on mobile). Add horizontal scroll if viewport is too narrow.
- [ ] **Step 21** -- End-to-end test: regenerate JSON from CLI, open UI, toggle strategies, make overrides, verify cascade works, check all probabilities display. Fix bugs. Final commit.

## Out of Scope
- Mobile responsive layout (desktop-only tool)
- Deployment / hosting (local `npm run dev` only)
- Backend server / FastAPI (pure static JSON approach)
- Re-running Monte Carlo from the UI
- Print/export bracket to PDF
- Animated transitions between strategies
- Dark mode toggle (pick one theme and ship it)
- Unit tests (ship first, test later if this tool persists)

## Risks / Tradeoffs
- **Bracket CSS layout is the critical path**: The traditional bracket tree layout with 4 regions converging to a center is notoriously fiddly. Mitigation: start with one region, get it working, then compose. If the full traditional layout proves too slow to build, fall back to tabbed regions (one region visible at a time) with a separate Final Four view.
- **Client-side cascade is approximate**: Uses model pairwise probabilities, not full MC re-simulation. For a personal bracket tool this is fine -- the pairwise probs already encode team strength. Accepted tradeoff.
- **Probability matrix size**: 64 teams x 64 teams x 6 rounds = ~24K entries max. In practice much smaller since most matchups never occur. JSON size is trivial.
- **`_prob_cache` access**: The `MonteCarloSimulator._prob_cache` is on the simulator instance, not on `MonteCarloResults`. Step 2 needs to pass the simulator's `_prob_cache` to the export function, or compute it fresh from the model. The cache is populated lazily during simulation, so after `mc.run()` it contains every matchup that was actually simulated. For the UI we need ALL possible pairwise matchups (not just ones that occurred in sims), so we should compute them fresh: iterate all team pairs, call `model.predict_win_probability()` for each round.

## Open Questions
- [ ] Should the probability matrix include all 6 rounds or just use round-1 probabilities everywhere? The model adjusts predictions by round (logreg uses `current_round` as a feature). Recommend: include rounds 1-6 for accuracy, it's only 6x the entries.
- [ ] Should overrides persist in localStorage so they survive page refresh? Low effort, nice UX. Recommend yes but only if time permits on Day 2.

## Skills / Agents to Use
- **Code agent (Python)**: Steps 1-4. Implement `export_ui_json` and the `ui-export` CLI command.
- **Code agent (TypeScript/React)**: Steps 5-21. Build the entire frontend. This is the bulk of the work.
- **No research agent needed**: Stack decisions are already made. React + Vite + Tailwind + TypeScript, no unknowns.
