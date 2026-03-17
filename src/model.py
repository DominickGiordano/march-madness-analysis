"""Scoring model: logistic regression + weighted composite + matchup adjustments."""

from pathlib import Path

import numpy as np
import pandas as pd
from rich.console import Console
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

console = Console()

DATA_DIR = Path(__file__).parent.parent / "data"

# Feature columns used for model training and prediction
FEATURE_COLS = ["adj_o_rank", "adj_d_rank", "barthag", "seed", "win_pct", "momentum", "wab_norm"]

# Weighted composite weights
COMPOSITE_WEIGHTS = {
    "adj_o_rank": -0.15,   # negative because lower rank = better
    "adj_d_rank": -0.20,   # defense weighted higher — March is about defense
    "barthag": 0.15,
    "seed": -0.10,         # lower seed = better
    "win_pct": 0.05,
    "sos_proxy": 0.08,     # real SOS from Barttorvik
    "momentum": 0.80,      # recent barthag delta (values are small, ~-0.05 to +0.05)
    "wab_norm": 0.12,      # Wins Above Bubble (normalized 0-1)
    "efg_ratio": 0.08,     # shooting efficiency edge
    "tempo_norm": 0.0,     # tempo itself isn't good/bad — mismatch matters (handled separately)
}

# Historical seed upset rates — P(lower seed wins)
# Based on 25 years of tournament data (2001–2025, excluding 2020)
# These are the REAL rates — the model must respect them
SEED_UPSET_RATES = {
    (1, 16): 0.02,   # 1 upset in ~100 games (UMBC 2018)
    (2, 15): 0.06,   # ~1 per 16 games
    (3, 14): 0.13,   # ~1 every 8 games
    (4, 13): 0.21,   # ~1 every 5 games
    (5, 12): 0.35,   # classic upset seed — happens often
    (6, 11): 0.37,   # slightly more than 5v12
    (7, 10): 0.40,   # near coin flip
    (8, 9): 0.49,    # true coin flip
}

# Champion hard filters (every champion since 2002 meets these)
CHAMPION_ADJ_O_RANK_MAX = 40
CHAMPION_ADJ_D_RANK_MAX = 25


class BracketModel:
    """Scores matchups using blended logistic regression + composite + matchup adjustments."""

    def __init__(self):
        self.logreg: LogisticRegression | None = None
        self.scaler: StandardScaler | None = None
        self.trained = False
        self._train_features: list[str] = FEATURE_COLS

    def train(self, historical_csv: str | Path | None = None) -> bool:
        """Train logistic regression on historical tournament data."""
        if historical_csv is None:
            historical_csv = DATA_DIR / "historical_results_2008_2025.csv"

        csv_path = Path(historical_csv)
        if not csv_path.exists():
            console.print("[yellow]No historical data found — using composite model[/yellow]")
            return False

        df = pd.read_csv(csv_path)

        if "seed" not in df.columns or "round_reached" not in df.columns:
            console.print("[yellow]Historical data missing seed/round_reached — using composite[/yellow]")
            return False

        if len(df) < 50:
            console.print(f"[yellow]Only {len(df)} records — too few for regression[/yellow]")
            return False

        available_features = [c for c in FEATURE_COLS if c in df.columns]
        if len(available_features) < 3:
            console.print(f"[yellow]Only {len(available_features)} features — using composite[/yellow]")
            return False

        self._train_features = available_features
        df = df.dropna(subset=available_features + ["round_reached"])

        train_rows = []
        for _, row in df.iterrows():
            round_reached = int(row["round_reached"])
            for r in range(1, 8):
                if r <= round_reached:
                    features = {col: row[col] for col in available_features}
                    features["current_round"] = r
                    features["advanced"] = 1 if r < round_reached else 0
                    weight = 2.0 if row.get("recent_era", 0) == 1 else 1.0
                    features["sample_weight"] = weight
                    train_rows.append(features)
                else:
                    break

        train_df = pd.DataFrame(train_rows)
        if len(train_df) < 100:
            console.print("[yellow]Insufficient training data — using composite[/yellow]")
            return False

        X = train_df[available_features + ["current_round"]].values
        y = train_df["advanced"].values
        weights = train_df["sample_weight"].values

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.logreg = LogisticRegression(max_iter=1000, C=1.0)
        self.logreg.fit(X_scaled, y, sample_weight=weights)

        accuracy = self.logreg.score(X_scaled, y, sample_weight=weights)
        console.print(f"[green]Logistic regression trained — accuracy: {accuracy:.3f} ({len(train_df)} samples)[/green]")
        self.trained = True
        return True

    def predict_win_probability(
        self,
        team_a: dict,
        team_b: dict,
        round_num: int = 1,
    ) -> float:
        """Predict probability that team_a beats team_b.

        Blends logistic regression + composite model, then applies:
        - Tempo mismatch adjustment
        - Seed history upset boost
        """
        # Base prediction: blend logreg + composite
        composite_prob = self._composite_predict(team_a, team_b)

        if self.trained and self.logreg and self.scaler:
            logreg_prob = self._logreg_predict(team_a, team_b, round_num)
            base_prob = 0.6 * logreg_prob + 0.4 * composite_prob
        else:
            base_prob = composite_prob

        # Apply matchup adjustments
        adjusted = self._apply_tempo_mismatch(base_prob, team_a, team_b)
        adjusted = self._apply_seed_history(adjusted, team_a, team_b)

        # Clamp to [0.02, 0.98] — nothing is truly impossible or certain
        return float(np.clip(adjusted, 0.02, 0.98))

    def _logreg_predict(self, team_a: dict, team_b: dict, round_num: int) -> float:
        """Use logistic regression to predict win probability."""
        cols = self._train_features
        features_a = [team_a.get(col, 0) for col in cols] + [round_num]
        features_b = [team_b.get(col, 0) for col in cols] + [round_num]

        X = np.array([features_a, features_b])
        X_scaled = self.scaler.transform(X)

        probs = self.logreg.predict_proba(X_scaled)[:, 1]
        p_a = probs[0]
        p_b = probs[1]

        total = p_a + p_b
        if total == 0:
            return 0.5
        return p_a / total

    def _composite_predict(self, team_a: dict, team_b: dict) -> float:
        """Weighted composite score with direct metric comparison."""
        score_a = self._composite_score(team_a)
        score_b = self._composite_score(team_b)

        diff = score_a - score_b
        # Scale factor 5 (was 3) — spreads probabilities further from 0.5
        # so dominant teams get 80-95% instead of 65-75%
        prob = 1.0 / (1.0 + np.exp(-diff * 5))
        return float(prob)

    def _composite_score(self, team: dict) -> float:
        """Compute weighted composite score for a single team."""
        score = 0.0
        for col, weight in COMPOSITE_WEIGHTS.items():
            val = team.get(col, 0)
            if val is None:
                continue
            if "rank" in col:
                val = 1.0 - (val / 353.0)
                score += val * abs(weight)
            elif col == "seed":
                val = 1.0 - (val / 16.0)
                score += val * abs(weight)
            else:
                score += val * weight
        return score

    def _apply_tempo_mismatch(self, base_prob: float, team_a: dict, team_b: dict) -> float:
        """Adjust probability based on tempo mismatch.

        In March Madness, slow defensive teams have an edge against fast teams
        because they control pace and reduce possessions (fewer chances for
        the better team to assert dominance, more variance per possession).

        The adjustment is small but meaningful: up to +/- 3% shift.
        """
        tempo_a = team_a.get("tempo", 67.5)
        tempo_b = team_b.get("tempo", 67.5)
        adj_d_rank_a = team_a.get("adj_d_rank", 175)
        adj_d_rank_b = team_b.get("adj_d_rank", 175)

        tempo_diff = abs(tempo_a - tempo_b)

        # Only matters when there's a real tempo gap (>3 possessions difference)
        if tempo_diff < 3.0:
            return base_prob

        # Identify the slower team
        slower_is_a = tempo_a < tempo_b

        # The slow team benefits if they also have good defense (top 50)
        # because they can grind the game down
        if slower_is_a and adj_d_rank_a <= 50:
            # Boost team A (slow + good D)
            boost = min(tempo_diff * 0.004, 0.03)  # max 3% boost
            return base_prob + boost
        elif not slower_is_a and adj_d_rank_b <= 50:
            # Boost team B (slow + good D)
            boost = min(tempo_diff * 0.004, 0.03)
            return base_prob - boost

        return base_prob

    def _apply_seed_history(self, base_prob: float, team_a: dict, team_b: dict) -> float:
        """Anchor probability toward historical seed upset rates.

        The bigger the seed gap, the more we trust 25 years of history
        over the model's prediction. This prevents absurdities like
        1-seeds being only 92% favorites over 16-seeds.

        Anchor weights by seed gap:
        - 1v16, 2v15 (gap 14-13): 40% history (strong anchor — these barely ever upset)
        - 3v14, 4v13 (gap 11-10): 30% history
        - 5v12, 6v11 (gap 7-5):   20% history (model has more say in competitive matchups)
        - 7v10, 8v9 (gap 3-1):    15% history (near coin flips, let model differentiate)
        """
        seed_a = team_a.get("seed", 8)
        seed_b = team_b.get("seed", 8)

        if seed_a == seed_b:
            return base_prob

        higher_seed = min(seed_a, seed_b)
        lower_seed = max(seed_a, seed_b)
        a_is_higher = seed_a == higher_seed

        key = (higher_seed, lower_seed)
        hist_upset_rate = SEED_UPSET_RATES.get(key)

        if hist_upset_rate is None:
            return base_prob

        # Convert to P(team_a wins)
        if a_is_higher:
            hist_prob_a = 1.0 - hist_upset_rate
        else:
            hist_prob_a = hist_upset_rate

        # Anchor weight scales with seed gap
        seed_gap = lower_seed - higher_seed
        if seed_gap >= 13:      # 1v16, 2v15
            anchor = 0.40
        elif seed_gap >= 10:    # 3v14, 4v13
            anchor = 0.30
        elif seed_gap >= 5:     # 5v12, 6v11
            anchor = 0.20
        else:                   # 7v10, 8v9
            anchor = 0.15

        blended = (1.0 - anchor) * base_prob + anchor * hist_prob_a
        return blended

    def passes_champion_filter(self, team: dict) -> bool:
        """Check if a team meets the historical champion profile thresholds."""
        adj_o_rank = team.get("adj_o_rank", 999)
        adj_d_rank = team.get("adj_d_rank", 999)
        return adj_o_rank <= CHAMPION_ADJ_O_RANK_MAX and adj_d_rank <= CHAMPION_ADJ_D_RANK_MAX

    def get_champion_contenders(self, teams: list[dict]) -> list[dict]:
        """Filter teams to only those meeting champion thresholds."""
        return [t for t in teams if self.passes_champion_filter(t)]
