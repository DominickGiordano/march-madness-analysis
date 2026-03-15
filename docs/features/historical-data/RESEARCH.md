# Research: Historical NCAA Tournament Data Sources (2006-2025)

**Date**: 2026-03-15
**Decision it informs**: Where to source the 20-year historical training dataset for our logistic regression model
**Status**: Complete

## Question
What are the best free sources for historical NCAA tournament data (2006-2025) containing team, seed, round reached, efficiency metrics (AdjO/AdjD), and game-by-game results? How do we access them programmatically?

## Findings

### Option A: Kaggle "March Machine Learning Mania" Competition Datasets

Kaggle has run the "March Machine Learning Mania" competition annually since 2014. Each year they publish updated historical datasets. The most recent competition (2024 or 2025 edition) contains data going back to ~2003.

**Key datasets within the competition package:**

| File | Description | Key Columns |
|------|-------------|-------------|
| `MNCAATourneyCompactResults.csv` | Every tournament game result, compact | `Season, DayNum, WTeamID, WScore, LTeamID, LScore, WLoc, NumOT` |
| `MNCAATourneyDetailedResults.csv` | Tournament games with box score stats | Above + `WFGM, WFGA, WFGM3, WFGA3, WFTM, WFTA, WOR, WDR, WAst, WTO, WStl, WBlk, WPF` (and L equivalents) |
| `MNCAATourneySeeds.csv` | Team seeds by year | `Season, Seed, TeamID` (Seed format: "W01", "X16a" etc.) |
| `MTeams.csv` | Team ID to name mapping | `TeamID, TeamName, FirstD1Season, LastD1Season` |
| `MRegularSeasonCompactResults.csv` | Every regular season game | Same as compact tourney results |
| `MRegularSeasonDetailedResults.csv` | Regular season with box scores | Same as detailed tourney results |
| `MSeasons.csv` | Season metadata | `Season, DayZero, RegionW, RegionX, RegionY, RegionZ` |
| `MMasseyOrdinals.csv` | 100+ ranking systems by team/day | `Season, RankingDayNum, SystemName, TeamID, OrdinalRank` |
| `MConferences.csv` / `MTeamConferences.csv` | Conference affiliations by year | `Season, TeamID, ConfAbbrev` |

**What it covers well:**
- Game-by-game results back to 2003 (compact) and ~2003 (detailed)
- Seeds for every tournament team
- Box score stats (FG%, 3P%, FT%, rebounds, assists, turnovers, steals, blocks)
- Massey Ordinals include KenPom rankings (system name "POM") and many others

**What it does NOT include directly:**
- Pre-computed AdjO / AdjD / Barthag efficiency metrics
- KenPom or T-Rank style adjusted metrics (only raw ordinal ranks via Massey)
- "Round reached" as a column -- you derive this from game results + bracket structure

**How to access:**
1. **Kaggle API** (preferred): `kaggle competitions download -c march-machine-learning-mania-2024` (or whichever year is most recent). Requires a free Kaggle account and API key (`~/.kaggle/kaggle.json`).
2. **Kaggle web UI**: Download ZIP from the competition's "Data" tab. Requires accepting competition rules.
3. **No direct CSV links** -- Kaggle requires authentication for competition datasets.
4. **Alternative**: Some users re-publish the data as standalone Kaggle datasets (searchable as "march madness" on kaggle.com/datasets), which can be downloaded via `kaggle datasets download`.

**Kaggle API setup:**
```bash
pip install kaggle
# Create API token at kaggle.com -> Settings -> API -> Create New Token
# Saves kaggle.json to ~/.kaggle/
kaggle competitions download -c march-machine-learning-mania-2024
```

- Pros: Most comprehensive single download. Clean CSVs. Well-documented schema. Includes Massey Ordinals with KenPom ranks. Updated annually. Community notebooks show data wrangling patterns.
- Cons: Requires Kaggle account + API key. No pre-computed efficiency metrics (AdjO/AdjD) -- only ordinal rankings. "Round reached" must be derived. May not include 2025 tournament if the 2025 competition hasn't concluded.
- Arete fit: Good foundation but needs supplementation with Barttorvik for efficiency metrics.

### Option B: Barttorvik (barttorvik.com) -- Historical T-Rank Data

Barttorvik provides a free KenPom alternative with historical data. This is already identified as our primary analytics source in PLAN.md.

**Access methods:**

1. **CSV Export URL**: `https://barttorvik.com/2026_team_results.csv` (swap year). Returns full-season team stats.
2. **Historical archive**: `https://barttorvik.com/trank.php?year=2025&sort=&conyes=&hession=All&top=0&quad=5&venue=All&type=All&count=353` -- can be scraped or accessed via URL params. Data goes back to ~2008.
3. **No official API**, but the site exposes data via predictable URL patterns and some JSON endpoints.

**Key fields available:**
- Team name, conference
- AdjO (adjusted offensive efficiency), AdjD (adjusted defensive efficiency)
- Barthag (power rating / estimated win probability vs average D1 team)
- Tempo, SOS (strength of schedule)
- Win-loss record
- Historical data back to approximately 2008

**What it covers well:**
- The exact efficiency metrics we need (AdjO, AdjD, Barthag, SOS, tempo)
- Free, no account required
- Data at time-of-tournament (end-of-season snapshots)

**What it does NOT include:**
- Tournament bracket structure or game-by-game results
- Seeds
- Round-by-round outcomes

- Pros: Exact metrics we need for the model (AdjO, AdjD, Barthag). Free, no auth. End-of-season snapshots approximate "at time of tournament."
- Cons: No official API -- URL patterns could change. No tournament results or seeds. Historical depth only to ~2008 (not 2006). Rate limiting unknown but likely lenient.
- Arete fit: Essential complement to Kaggle data. Already identified in our plan.

### Option C: Sports Reference / College Basketball Reference

`sports-reference.com/cbb/` and `basketball-reference.com` (college section) provide comprehensive historical stats.

**Access:**
- Web scraping with BeautifulSoup (already in our deps)
- Some pages have "Share & Export" CSV/table options
- **Rate limited**: Must add delays (2-3s between requests)
- NCAA tournament brackets with results: `https://www.sports-reference.com/cbb/postseason/YYYY-ncaa.html`

**Key fields:**
- Season stats per team: W/L, SOS, SRS (Simple Rating System), pace, ORtg, DRtg
- Tournament results page shows bracket with scores
- Advanced stats: eFG%, TOV%, ORB%, FTRate
- Per-game box scores for every tournament game

**What it covers well:**
- Tournament bracket structure with results (derivable round-reached)
- SRS (similar to power rating) back to 1993
- Advanced four factors stats

**What it does NOT include:**
- KenPom/T-Rank equivalent AdjO/AdjD (SRS is close but not the same)
- Clean programmatic API -- scraping required

- Pros: Deep historical coverage. Tournament bracket pages make "round reached" easy to derive. SRS is a reasonable efficiency proxy. Already in our stack (BeautifulSoup).
- Cons: Scraping required (fragile, slow). Rate limited. SRS is not as good as Barttorvik's AdjO/AdjD. Terms of service may restrict automated scraping.
- Arete fit: Good for tournament results and as a fallback. Already planned as secondary source.

### Option D: GitHub Repos with Pre-Built Historical Data

Several GitHub repos maintain curated NCAA tournament datasets:

1. **`adambaker/historical-ncaa-tournament-results`** -- CSV with team, seed, round reached for every tournament team. Likely covers 1985-recent.
2. **`nishanthgandhidoss/Marchmadness-prediction`** and similar ML project repos -- often include cleaned training data with seeds + results.
3. **`CornellDataScience/march-madness`** -- another repo with historical bracket data.
4. **Search**: `github.com/search?q=march+madness+historical+data+csv` yields dozens of repos.

**Typical format in these repos:**
```
Year,Team,Seed,Round,AdjEM,AdjO,AdjD,Luck,SOS_AdjEM
2024,UConn,1,Champion,35.74,126.1,90.4,...
```

- Pros: Pre-cleaned, ready to use. Some include KenPom/efficiency data already merged. No scraping or API needed.
- Cons: May not be up to date (missing 2025). Data quality varies -- must validate. Licensing unclear. Finding the right repo takes time.
- Arete fit: Could save significant time if we find one with efficiency metrics already merged. Worth checking before building from scratch.

### Option E: data.world

data.world has several NCAA tournament datasets. Search for "NCAA tournament" or "march madness." Notable:
- Historical tournament results with seeds
- Some datasets include KenPom metrics

**Access:** Free account required. CSV download or API access.

- Pros: Clean datasets, some with efficiency metrics pre-joined.
- Cons: Requires account. May not be current. Smaller community than Kaggle.
- Arete fit: Low priority -- Kaggle + Barttorvik covers our needs better.

### Option F: KenPom Archive (kenpom.com)

KenPom is the gold standard for college basketball efficiency metrics. However:
- **Paid subscription required** ($25/year)
- Historical archive goes back to 2002
- No public API -- scraping required even with subscription
- Data includes: AdjO, AdjD, AdjEM, AdjTempo, Luck, SOS

- Pros: Gold standard data, exactly what the model needs.
- Cons: Paid. No API. Scraping violates ToS.
- Arete fit: Skip -- Barttorvik provides equivalent metrics for free.

## Recommended Approach

Use a **two-source strategy** combining Kaggle + Barttorvik:

### Step 1: Kaggle for tournament structure + results
Download the March Machine Learning Mania dataset. From it, extract:
- `MNCAATourneyCompactResults.csv` -- derive round reached for each team per year
- `MNCAATourneySeeds.csv` -- seeds per team per year
- `MTeams.csv` -- team ID to name mapping
- `MMasseyOrdinals.csv` -- pull KenPom ordinal rankings (system "POM") as a supplementary feature

This gives us: **year, team, seed, round reached** for 2003-2025.

### Step 2: Barttorvik for efficiency metrics
For each team-year in our Kaggle dataset, pull from Barttorvik:
- AdjO, AdjD, Barthag, SOS, tempo
- URL pattern: `https://barttorvik.com/{year}_team_results.csv`

This gives us: **AdjO, AdjD, Barthag, SOS** for ~2008-2025.

### Step 3: Merge on team name + year
Join the two datasets. This requires a team name mapping (Kaggle uses TeamID, Barttorvik uses team names/slugs). Build a mapping table.

### Step 4: Supplement gaps
- For 2006-2007 (before Barttorvik coverage): use Massey Ordinals from Kaggle as a proxy, or SRS from Sports-Reference.
- For momentum/recent form: scrape last-10-games records from Sports-Reference (only needed for current year 2026).

### Final training dataset schema:
```
Season,TeamID,TeamName,Seed,Round,AdjO,AdjD,Barthag,SOS,Tempo,MasseyOrdinal,RoundWin
2025,1234,Duke,1,6,121.3,89.2,0.9712,8.42,68.1,3,1
```

Where `Round` = furthest round reached (1=R64 loss, 2=R32, 3=S16, 4=E8, 5=F4, 6=Championship game, 7=Champion) and `RoundWin` = binary target for logistic regression.

## Kaggle API Setup (Action Items)

```bash
# 1. Install kaggle CLI
pip install kaggle

# 2. Create account at kaggle.com if needed

# 3. Generate API token: kaggle.com -> Settings -> API -> Create New Token
#    This downloads kaggle.json

# 4. Place credentials
mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json

# 5. Download the dataset
kaggle competitions download -c march-machine-learning-mania-2024 -p data/kaggle/

# OR if a 2025 edition exists:
kaggle competitions download -c march-machine-learning-mania-2025 -p data/kaggle/

# 6. Unzip
unzip data/kaggle/*.zip -d data/kaggle/
```

## Key Links / References

- Kaggle March Machine Learning Mania: `https://www.kaggle.com/competitions/march-machine-learning-mania-2024`
- Barttorvik: `https://barttorvik.com`
- Barttorvik CSV pattern: `https://barttorvik.com/{YYYY}_team_results.csv`
- Sports Reference CBB: `https://www.sports-reference.com/cbb/`
- Sports Reference tourney brackets: `https://www.sports-reference.com/cbb/postseason/{YYYY}-ncaa.html`
- KenPom (paid, for reference): `https://kenpom.com`
- GitHub search for pre-built datasets: `https://github.com/search?q=ncaa+tournament+historical+data+csv`

## Open Questions

- [ ] Confirm the exact Kaggle competition slug for the most recent (2025) edition -- may be `march-machine-learning-mania-2025` or similar
- [ ] Verify Barttorvik CSV URL pattern still works for historical years (test `https://barttorvik.com/2024_team_results.csv`)
- [ ] Determine if Barttorvik data goes back to 2006 or only 2008 -- if 2008, decide whether to truncate training window or use proxies for 2006-2007
- [ ] Check if `MMasseyOrdinals.csv` includes KenPom ("POM" system) rankings -- if so, these can substitute for Barttorvik in older years
- [ ] Assess whether a pre-built GitHub repo already has the merged dataset we need (could save hours of data wrangling)
- [ ] Confirm whether Dominick already has a Kaggle account / API key set up
