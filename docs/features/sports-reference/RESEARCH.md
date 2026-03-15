# Research: sports-reference.com/cbb as Data Source

**Date**: 2026-03-15
**Decision it informs**: Whether to use Sports-Reference for momentum data (last 10 games) and historical tournament results, or find an alternative
**Status**: Complete

## Question
Can we reliably scrape sports-reference.com/cbb for current season stats, game logs, and 20 years of tournament results? What are the access patterns, rate limits, and alternatives?

## Findings

### 1. Current Season Data (2025-26)

Sports-Reference CBB provides comprehensive current-season data including W/L records, per-game stats, and advanced stats. However, there is no native "last 10 games" stat -- you must derive it from game logs.

**Season summary pages** (team-level):
- School page: `https://www.sports-reference.com/cbb/schools/{slug}/men/2026.html`
- Game log: `https://www.sports-reference.com/cbb/schools/{slug}/men/2026-gamelogs.html`
- Schedule/results: `https://www.sports-reference.com/cbb/schools/{slug}/men/2026-schedule.html`

The game log page contains every game with date, opponent, result (W/L), and score. To compute "last 10 games record" you scrape the game log, sort by date, take the last 10 rows, and count W vs L.

**League-wide season stats**:
- All schools: `https://www.sports-reference.com/cbb/seasons/men/2026-school-stats.html`
- Advanced stats: `https://www.sports-reference.com/cbb/seasons/men/2026-advanced-school-stats.html`
- Conference standings: `https://www.sports-reference.com/cbb/seasons/men/2026.html`

**Note on URL slug format**: School slugs are lowercase, hyphenated versions of the school name. Examples:
- Duke: `duke`
- North Carolina: `north-carolina`
- Michigan State: `michigan-state`
- Texas A&M: `texas-am`
- St. John's: `st-johns-ny`

Some slugs are non-obvious (state suffixes, abbreviations). You will need a mapping table or fallback lookup. Sports-Reference's school index page lists all active schools: `https://www.sports-reference.com/cbb/schools/`

### 2. URL Patterns (Full Reference)

| Resource | URL Pattern |
|----------|------------|
| School index | `/cbb/schools/` |
| Team season page | `/cbb/schools/{slug}/men/{year}.html` |
| Team game log | `/cbb/schools/{slug}/men/{year}-gamelogs.html` |
| Team schedule | `/cbb/schools/{slug}/men/{year}-schedule.html` |
| Season school stats | `/cbb/seasons/men/{year}-school-stats.html` |
| Season advanced stats | `/cbb/seasons/men/{year}-advanced-school-stats.html` |
| Season standings | `/cbb/seasons/men/{year}.html` |
| Tournament bracket | `/cbb/postseason/men/{year}-ncaa.html` |
| Conference tourney | `/cbb/postseason/men/{year}-{conf}.html` |

**Year convention**: The `{year}` parameter uses the ending year of the season. The 2025-26 season is `2026`. The 2024-25 season is `2025`.

**Base URL**: `https://www.sports-reference.com`

### 3. Rate Limiting and Scraping Policy

Sports-Reference has explicit scraping guidelines. Key points:

- **robots.txt**: The site has a robots.txt that allows most paths but requests responsible crawling. They do not block `/cbb/` paths for well-behaved bots.
- **Rate limiting**: Sports-Reference will **block your IP** if you make requests too quickly. They have stated in their terms that automated access should be "reasonable" and have been known to block IPs that exceed roughly **20 requests per minute**.
- **2-second delay**: The plan's `time.sleep(2)` is a reasonable baseline -- it keeps you at 30 requests/minute which is within acceptable range. However, for bulk historical scraping (20 years of tournament data), consider **3-second delays** to be safe, especially if making many sequential requests.
- **CloudFlare protection**: Sports-Reference uses CloudFlare. Aggressive scraping triggers CAPTCHA challenges or 403 blocks. A standard `requests` session with a realistic User-Agent header generally works fine at 2-3s intervals.
- **Recommended headers**: Set a `User-Agent` string that identifies your tool (e.g., `MarchMadnessAnalyzer/1.0`) rather than using the default `python-requests` agent. Some users report better success with browser-like User-Agent strings.
- **No official API**: Sports-Reference does not offer a public API. All data access is via HTML scraping or their CSV export feature.

**Verdict**: 2-second delays are likely sufficient for the ~68 game log pages needed for current season data. For the historical data build (which could be 100+ pages for 20 years of tournament results), bump to 3 seconds and consider caching aggressively.

### 4. Historical Tournament Results (2006-2025)

Tournament bracket pages are available for every year:
- URL: `https://www.sports-reference.com/cbb/postseason/men/{year}-ncaa.html`
- Years 2006 through 2025: replace `{year}` with `2006`, `2007`, ..., `2025`
- **2020**: No tournament was held (COVID). The page exists but shows "Tournament Cancelled."

Each tournament page contains:
- Full bracket with all matchups by round
- Scores for every game
- Seeds for every team
- The data is in HTML tables that BeautifulSoup can parse

**Scraping plan for historical CSV**:
- 19 pages (2006-2019, 2021-2025; skip 2020)
- At 3s delay: ~57 seconds total
- Parse each page for: team name, seed, opponent, opponent seed, score, round, result
- This gives you the training data for the logistic regression

**Alternative for historical results**: The NCAA publishes historical bracket results, and several GitHub repos maintain cleaned CSVs of tournament results going back to the 1980s. Searching for "ncaa tournament results csv github" will surface datasets like:
- `nflverse/cfbfastR` (R package but has CSVs)
- Various Kaggle datasets (e.g., "March Machine Learning Mania")

Using a pre-built CSV for historical results would eliminate the need to scrape Sports-Reference for this data entirely.

### 5. CSV Export

Sports-Reference offers a **"Share & Export"** feature on most stat tables:
- Click "Share & Export" above any table, then "Get as CSV"
- This gives you the table data as CSV text (copy-paste, not a file download)
- Programmatically, the CSV is embedded in a `<pre>` tag within a modal -- it is not a direct download URL

**For programmatic CSV access**: There is no direct CSV download endpoint. The "CSV" feature is JavaScript-driven and requires browser interaction. For scraping, parse the HTML tables directly with BeautifulSoup rather than trying to trigger the CSV export.

**Exception**: The school-stats aggregate pages sometimes have a direct CSV link pattern: `https://www.sports-reference.com/cbb/seasons/men/2026-school-stats.html` -- the table can be parsed from HTML, and pandas `read_html()` works well on these pages.

### 6. Alternative Sources for "Last 10 Games" / Momentum Data

#### Option A: Barttorvik (Recommended)
Barttorvik already provides game-by-game results via its team pages:
- URL: `https://barttorvik.com/team.php?team={team}&year=2026`
- The site provides a game results table with date, opponent, result, and advanced metrics per game
- **Key advantage**: Barttorvik is already the primary data source in the plan. Getting momentum data from the same source eliminates a second scraping dependency.
- Barttorvik also offers a team results CSV: `https://barttorvik.com/getgamestats.php?team={team}&year=2026` (returns JSON or can be parsed)

#### Option B: ESPN API (Unofficial)
- ESPN has an undocumented API at `https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{id}/schedule`
- Returns JSON with full schedule including results
- No rate limiting documentation, but it is an API (faster than scraping)
- Downside: Team IDs are ESPN-specific, need a mapping table

#### Option C: Sports-Reference (Current Plan)
- Requires scraping 68 individual game log pages
- At 2s delay: ~136 seconds just for game logs
- Adds a second scraping dependency beyond Barttorvik
- HTML parsing is straightforward with BeautifulSoup

#### Option D: Kaggle / Pre-built Datasets
- Kaggle's "March Machine Learning Mania" competition publishes cleaned regular season results CSVs annually
- Includes game-by-game results with team IDs
- Free to download but requires a Kaggle account
- May not be updated until very close to tournament time

## Recommendation

**Use Barttorvik for momentum data instead of Sports-Reference.** The plan already depends on Barttorvik for AdjO, AdjD, Barthag, and SOS. Pulling game logs from the same source:
1. Eliminates a second scraping dependency
2. Avoids Sports-Reference's CloudFlare/rate-limit friction
3. Keeps all team data fetching in one place
4. Is likely faster (Barttorvik is less aggressive about blocking)

**Use Sports-Reference only for historical tournament results (2006-2025)**, and even then, consider using a pre-built CSV from Kaggle or GitHub instead. If scraping Sports-Reference for tournament brackets, the 19-page scrape at 3s delay is manageable (~60 seconds, one-time operation).

**If you do scrape Sports-Reference**:
- Use 3-second delays (not 2) for safety
- Set a descriptive User-Agent header
- Cache all responses to disk so you never re-fetch
- Use `pandas.read_html()` for table parsing where possible (simpler than raw BeautifulSoup)
- Handle the 2020 gap (no tournament)

## Key Links / References
- Sports-Reference CBB home: https://www.sports-reference.com/cbb/
- Sports-Reference school index: https://www.sports-reference.com/cbb/schools/
- Tournament results pattern: https://www.sports-reference.com/cbb/postseason/men/{year}-ncaa.html
- Barttorvik home: https://barttorvik.com
- Kaggle March Mania: https://www.kaggle.com/c/march-machine-learning-mania (search for latest year)
- Sports-Reference robots.txt: https://www.sports-reference.com/robots.txt

## Open Questions
- [ ] Verify Barttorvik game log endpoint format for 2026 season (test `getgamestats.php` or equivalent)
- [ ] Confirm whether Kaggle 2026 dataset is available yet (usually published ~2 weeks before tournament)
- [ ] Build and validate the team name to slug mapping for all 68 tournament teams (this is needed regardless of source)
- [ ] Test whether `pandas.read_html()` works on current Sports-Reference pages (they occasionally change table markup)
