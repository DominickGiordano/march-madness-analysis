# Research: Barttorvik as Primary Data Source

**Date**: 2026-03-15
**Decision it informs**: How `fetch_data.py` pulls team efficiency data (Phase 1 of PLAN.md)
**Status**: Complete (with caveats -- live endpoint verification blocked, see Open Questions)

## Question
What are the actual URL patterns, data formats, access methods, and constraints for pulling team efficiency data from barttorvik.com? Is the assumed URL `https://barttorvik.com/2026_team_results.csv` correct?

## Findings

### 1. Current Season Data Endpoints

Barttorvik exposes data through several URL patterns. The site is PHP-backed and returns data via specific query parameters.

#### Option A: `getadvstats.php` (Recommended -- Structured JSON)

```
https://barttorvik.com/getadvstats.php?year=2026&top=353
```

- Returns JSON array of all D1 teams (353 total, not just 68 tournament teams)
- Query params: `year` (season), `top` (number of teams to return)
- Fields include: team name, conference, record, AdjO, AdjD, Barthag, T-Rank, tempo, SOS-related metrics
- This is the endpoint the community and wrapper libraries actually use
- No authentication required

#### Option B: `trank.php` with CSV flag

```
https://barttorvik.com/trank.php?year=2026&csv=1
```

- Appending `&csv=1` to the T-Rank page URL triggers a CSV download
- Returns all teams with full T-Rank data
- This is the most commonly referenced "CSV export" in community guides

#### Option C: Direct CSV file (the plan's assumption)

```
https://barttorvik.com/2026_team_results.csv
```

- **This pattern is NOT confirmed as a reliable endpoint.** Barttorvik does not appear to host static CSV files at predictable year-based paths. The plan's assumption here is likely wrong.
- The CSV export is triggered via the `trank.php?csv=1` pattern, not a static file.

#### Option D: `team-tables_json.php`

```
https://barttorvik.com/team-tables_json.php?year=2026
```

- Another JSON endpoint sometimes referenced
- May return differently structured data than `getadvstats.php`

**Recommendation**: Use `getadvstats.php` as primary, `trank.php?csv=1` as fallback.

### 2. Historical Data (2006-2025)

Barttorvik has historical T-Rank data going back to at least 2008 (the site's data coverage varies by source, but most community references confirm 2008+).

**URL pattern**: Same endpoints with different `year` parameter:
```
https://barttorvik.com/getadvstats.php?year=2015&top=353
https://barttorvik.com/trank.php?year=2015&csv=1
```

Key considerations:
- Data completeness improves in more recent seasons
- Pre-2008 data may be sparse or missing -- the plan targets 2006-2025 but we may only get 2008-2025 from Barttorvik
- For 2006-2007, we may need to fall back to KenPom historical data (paywalled) or Sports-Reference
- Historical data includes: AdjO, AdjD, Barthag, tempo, SOS, conference, W-L record

### 3. Team Name / Slug Format

Barttorvik uses **full team names** (not abbreviations or IDs) as identifiers:
- Format: Title case, full name -- e.g., `"Duke"`, `"North Carolina"`, `"Michigan St."` (note the period after abbreviations)
- Saint/St. inconsistency: `"St. John's"` vs `"Saint Mary's"` -- this varies and is a known pain point
- State abbreviations: `"Michigan St."` not `"Michigan State"` (sometimes)
- The `team` parameter in per-team endpoints uses URL encoding: `team=Michigan+St.`

**Known gotchas for team name matching:**
- `"UConn"` not `"Connecticut"`
- `"UNLV"` not `"Nevada-Las Vegas"`
- `"UCF"` not `"Central Florida"`
- `"SMU"` not `"Southern Methodist"`
- Some names change over time (conference realignment, rebranding)

**Recommendation**: Build a manual alias map (~20-30 entries) for common bracket names to Barttorvik names. Pull the full team list from `getadvstats.php` at runtime and fuzzy-match against bracket input.

### 4. Rate Limiting / Access Restrictions

Barttorvik is a free, one-person site run by Bart Torvik:
- **No official API documentation** -- all endpoints are community-discovered
- **No authentication** required
- **No published rate limits**, but the site is small-scale infrastructure
- Community consensus: be respectful -- add 1-2 second delays between requests
- **No robots.txt restrictions** on data endpoints (as of community reports)
- Aggressive scraping will likely get your IP blocked
- The site occasionally goes down during peak traffic (Selection Sunday, tournament weekends)

**Practical implications for tonight (Selection Sunday):**
- The site will be under heavy load tonight. Have retry logic with exponential backoff.
- Pull data BEFORE the bracket reveal if possible (team stats don't change, only bracket placement does)
- Cache responses locally -- don't re-fetch on every run

### 5. Python Wrapper Libraries

#### Option A: `cbbpy` (Recommended)

```
pip install cbbpy
```

- **Active, maintained Python library** for college basketball data
- Has a `barttorvik` module specifically: `from cbbpy import barttorvik as bt`
- Key functions:
  - `bt.get_rankings(year=2026)` -- returns pandas DataFrame with T-Rank data
  - `bt.get_game_data(team, year)` -- per-team game logs
  - `bt.get_team_factors(year)` -- Four Factors data
- Returns DataFrames directly -- no parsing needed
- Handles URL construction and request management internally
- **Caveat**: Library updates may lag behind site changes. If Barttorvik changes an endpoint, the library breaks until updated.

#### Option B: Direct `requests` + `pandas`

```python
import requests
import pandas as pd

url = "https://barttorvik.com/getadvstats.php"
params = {"year": 2026, "top": 353}
response = requests.get(url, params=params)
data = response.json()  # or pd.read_csv() for CSV endpoint
df = pd.DataFrame(data)
```

- Full control over request handling, retries, caching
- No dependency on third-party wrapper maintenance
- More work upfront but more resilient

#### Option C: `sportsdataverse` / `hoopR`

- Primarily R-focused ecosystem, Python support limited
- Not recommended for this use case

**Recommendation**: Start with `cbbpy` for speed (we need this working tonight). Implement a direct `requests` fallback in case `cbbpy` breaks or the site is under load.

### 6. Data Fields Available

Based on `getadvstats.php` response structure, expected fields:

| Field | Description | Needed for model? |
|---|---|---|
| Team | Team name | Yes (identifier) |
| Conf | Conference | Nice to have |
| G | Games played | No |
| Wins / Losses | Record | Nice to have |
| AdjO | Adjusted offensive efficiency | **Yes (20% weight)** |
| AdjD | Adjusted defensive efficiency | **Yes (25% weight)** |
| Barthag | Power rating (win prob vs avg team) | **Yes (20% weight)** |
| T-Rank | Overall ranking | Nice to have |
| AdjT | Adjusted tempo | Nice to have |
| WAB | Wins above bubble | Nice to have |
| SOS | Strength of schedule (various flavors) | **Yes (10% weight)** |
| OppO / OppD | Opponent offensive/defensive efficiency | No |
| Conf W/L | Conference record | No |

## Recommendation

**Use `cbbpy` as primary data fetcher with direct `requests` fallback.**

1. **Fix the URL assumption in PLAN.md**: Change `https://barttorvik.com/2026_team_results.csv` to `https://barttorvik.com/getadvstats.php?year=2026&top=353` (or just use `cbbpy`).

2. **Add `cbbpy` to requirements.txt** alongside the existing deps.

3. **Build a team name alias map** in `data/team_aliases.json` for bracket-name-to-Barttorvik-name resolution. Include ~30 common mismatches.

4. **Pre-fetch data before bracket reveal tonight**: Team stats are already final. Pull and cache to `data/barttorvik_2026.csv` before the site gets hammered at 6pm ET.

5. **For historical data (2008-2025)**: Loop `getadvstats.php?year={year}` with 2-second delays. Cache each year as `data/barttorvik_{year}.csv`. For 2006-2007, accept the gap or manually source from archived data.

6. **Implement retry logic**: Exponential backoff (1s, 2s, 4s, 8s) with max 3 retries per request.

## Key Links / References

- Barttorvik main site: https://barttorvik.com
- T-Rank page (current season): https://barttorvik.com/trank.php?year=2026
- `cbbpy` PyPI: https://pypi.org/project/cbbpy/
- `cbbpy` GitHub: https://github.com/dcstats/cbbpy
- Community discussion of endpoints: various Reddit r/CollegeBasketball threads

## Open Questions

- [ ] **CRITICAL -- Verify endpoints live**: Bash was denied during research. Before writing `fetch_data.py`, run `curl` against `getadvstats.php?year=2026&top=353` and `trank.php?year=2026&csv=1` to confirm they return expected data and check response format
- [ ] **Verify `cbbpy` current version works with 2026 data**: Install and test `bt.get_rankings(year=2026)` before relying on it
- [ ] **Confirm historical data range**: Test `getadvstats.php?year=2006` and `year=2008` to determine earliest available season
- [ ] **Team name format for 2026**: Pull actual team list and check for any new naming quirks (conference realignment may have changed some names)
- [ ] **Selection Sunday site stability**: Have a plan B if barttorvik.com is down tonight -- could scrape cached Google results or use Massey Ratings as backup data source
