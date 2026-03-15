# Brainstorm: Frontend UI for Bracket Analyzer

**Date**: 2026-03-15
**Deadline**: 2026-03-18 (3 days)
**Constraint**: Local-only, personal tool, must integrate with existing Python Monte Carlo engine

---

## Phase 1 -- Explore (Possibility Space)

### Framework Options
- **Next.js** -- overkill for local-only, but familiar stack; SSR not needed
- **Vite + React** -- minimal setup, fast HMR, no SSR baggage; perfect for local SPA
- **Vite + Preact** -- even lighter, but React compat mode has rough edges
- **Svelte/SvelteKit** -- great for interactive UIs but learning curve vs shipping by Wednesday
- **Vue + Vite** -- fine but not in your stack preferences
- **Plain HTML + vanilla JS** -- fastest to prototype, hardest to maintain; no TypeScript strict
- **Astro** -- static-first, wrong paradigm for interactive bracket
- **Remix** -- SSR-focused, wrong fit

### Python-to-Frontend Data Bridge
- **FastAPI thin wrapper** -- add a `/api/simulation` endpoint that returns the MonteCarloResults as JSON; frontend fetches it
- **Pre-computed JSON file** -- run the CLI, dump results to JSON, frontend reads static file; simplest possible
- **Flask one-file server** -- similar to FastAPI but even simpler for tiny APIs
- **WebSocket server** -- overkill unless we want live re-simulation
- **Python subprocess from Node** -- spawn `python main.py` from a Node dev server; fragile
- **PyScript / Pyodide** -- run Python in browser; terrible for scikit-learn + pandas
- **Hybrid: static JSON + on-demand FastAPI** -- load pre-computed results instantly, hit API only for manual overrides that need re-simulation

### Manual Override / Cascade Recalculation
- **Server-side re-simulation** -- user clicks override, sends to Python backend, re-runs Monte Carlo with forced winner; accurate but slow (10k sims = ~5-10s)
- **Client-side probability propagation** -- pre-compute all pairwise win probabilities, ship them to the frontend, then when user forces a winner, recalculate downstream matchups using those probabilities (no simulation needed); fast but approximate
- **Reduced simulation count** -- re-run 1k sims instead of 10k for overrides; faster but noisier
- **Conditional probability cache** -- pre-compute "if team X wins round N, their probability of winning round N+1 against each possible opponent"; huge cache but instant lookups
- **No cascade, just show** -- let user override picks manually without recalculating downstream probabilities; simple but defeats the purpose

### Bracket Layout
- **Traditional bracket tree (SVG)** -- the classic look; hard to make responsive
- **Traditional bracket tree (CSS grid/flexbox)** -- more maintainable than SVG
- **Region tabs + bracket per region** -- show one region at a time, Final Four on separate view; simpler layout
- **Horizontal scrolling bracket** -- full 64-team bracket left-to-right; needs wide viewport
- **Vertical round-by-round cards** -- mobile-friendly but unconventional
- **Existing React bracket libraries** -- `react-brackets`, `react-tournament-bracket`, etc.; may not support the interaction model we need

### Key Interactions
- Strategy toggle (safe/balanced/risky) -- segmented control or tabs
- Click matchup to override winner
- Hover to see detailed probabilities and team stats
- Color coding for upset picks, confidence levels
- Side panel with team advancement probabilities table

---

## Phase 2 -- Converge

### Option 1: Vite + React SPA with Pre-computed JSON (Static-First)

**What**: Build a React SPA that reads pre-computed simulation results from JSON files. No backend server needed for the primary experience.

**How it works**: Run the existing CLI with `--export json` to produce a comprehensive JSON dump containing all three bracket strategies, per-matchup win probabilities, and team advancement data. The React app loads this JSON at startup. Strategy toggle swaps between pre-built brackets. For manual overrides, the app ships a pairwise probability matrix (all possible matchups) and propagates overrides client-side using those probabilities -- no server round-trip needed.

**Pros**:
- Zero backend to build or run -- `npm run dev` and you're done
- Instant strategy switching (all three brackets pre-loaded)
- Manual overrides resolve instantly (client-side math)
- Simplest deployment: just build the JSON once, then iterate on the UI
- Fastest path to a working bracket by Wednesday

**Cons / Risks**:
- Client-side cascade is approximate -- uses model's pairwise probabilities rather than full Monte Carlo re-simulation. The difference: MC accounts for the full tournament tree (who you might face in later rounds), while pairwise just gives you "A beats B with X%". For a personal bracket tool, this is fine.
- Requires a separate CLI step to regenerate data if bracket changes
- Need to extend the existing `export_json` to include the full probability matrix (currently only exports the balanced bracket)

**Best if**: You want the fastest path to interactive bracket visualization and the approximation on cascading overrides is acceptable.

---

### Option 2: Vite + React SPA with FastAPI Backend (Full Stack)

**What**: React frontend + thin FastAPI server wrapping the existing Python engine. API serves simulation data and handles override re-calculations server-side.

**How it works**: Add a `server.py` with 3-4 endpoints: `GET /api/brackets` (returns all three strategies), `GET /api/team-data` (team metrics), `POST /api/override` (accepts forced winners, re-runs targeted simulation). Frontend is Vite + React, fetches data on load, sends overrides to the API. The override endpoint either re-runs a reduced Monte Carlo (1k sims with forced outcomes) or uses the `_build_bracket` logic with forced winners injected.

**Pros**:
- Override recalculation is more accurate (uses the actual simulation engine)
- Clean separation: Python does math, React does display
- Can add features later (different sim counts, injury toggles, etc.)
- Hot-reloads on both sides during development

**Cons / Risks**:
- More moving parts: need to run both `npm run dev` and `python server.py`
- Override latency: even 1k sims takes ~0.5-1s, which is noticeable when clicking through matchups
- Need to write FastAPI wrapper code (not much, but it's scope)
- CORS setup between Vite dev server and FastAPI

**Best if**: You care about accuracy of cascading overrides more than speed, or you want to extend this tool with more backend features later.

---

### Option 3: Hybrid -- Static JSON + Optional FastAPI for Overrides

**What**: Start with Option 1 (static JSON, client-side cascade) but structure the code so a FastAPI backend can be plugged in later for server-side re-simulation.

**How it works**: Frontend loads pre-computed JSON. Client-side probability propagation handles overrides by default. The data-fetching layer uses an abstraction (e.g., a `DataProvider` that can read from static JSON or API). If you want more accurate overrides later, spin up FastAPI and flip a config flag. This is Option 1 with an escape hatch.

**Pros**:
- Ships fast like Option 1
- No backend needed day one
- Upgrade path to full accuracy without rewriting the frontend
- Best of both worlds

**Cons / Risks**:
- Slight over-engineering for a personal tool -- the abstraction layer adds complexity you may never use
- If you never add the backend, you wrote unnecessary adapter code
- Two code paths to reason about if you do add the backend

**Best if**: You suspect you'll want server-side overrides eventually but need something working by Wednesday.

---

## Phase 3 -- Recommendation

**Go with Option 1: Vite + React SPA with Pre-computed JSON.**

Here is why:

1. **Timeline**: 3 days. A backend adds scope you don't need. The bracket visualization and interaction model are the hard parts -- spend your time there, not on FastAPI plumbing.

2. **Override accuracy is fine**: For a personal bracket tool, client-side probability propagation is plenty accurate. The pairwise win probabilities from the model already account for team strength, and the main thing you're doing is asking "if I force team X to win, what's their probability against possible opponent Y in the next round?" That's a direct lookup, not an approximation crime.

3. **The data is already there**: Your `MonteCarloResults` class has `matchup_wins`, `matchup_total`, `team_advances`, and the `_prob_cache` from the simulator. You just need to serialize this to JSON. One new export function, maybe 30 lines of Python.

4. **Option 3 is premature abstraction**: You said this is a personal tool, not a product. If you ever need server-side overrides, you can add FastAPI then. YAGNI.

**Implementation sketch**:
- Extend `export_json` in `output.py` to dump the full simulation data (all three brackets + probability matrix + team data + advancement probs)
- `npm create vite@latest ui -- --template react-ts`
- Build bracket component as CSS grid (4 regions, each with 4 rounds, converging to Final Four)
- Strategy toggle as segmented control at the top
- Matchup click handler: when user overrides a winner, walk forward through the bracket tree, replacing winners and looking up new probabilities from the pre-shipped matrix
- Color-code confidence: green (>70%), yellow (50-70%), red (<50%)
- Tooltip on hover for team stats (seed, Barthag, AdjO/AdjD ranks, advancement %)

**Key files to modify/create**:
- `src/output.py` -- new `export_full_json()` function
- `ui/` -- entire Vite + React app (new directory)
- `ui/src/components/Bracket.tsx` -- main bracket grid
- `ui/src/components/Matchup.tsx` -- single matchup with click-to-override
- `ui/src/hooks/useBracketState.ts` -- state management for overrides + cascade
- `ui/src/lib/probability.ts` -- client-side cascade calculation logic
