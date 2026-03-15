"""Scoring model: logistic regression + weighted composite fallback."""

from pathlib import Path

import numpy as np
import pandas as pd
from rich.console import Console
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

console = Console()

DATA_DIR = Path(__file__).parent.parent / "data"

# Feature columns used for model training and prediction
FEATURE_COLS = ["adj_o_rank", "adj_d_rank", "barthag", "seed", "win_pct", "momentum"]

# Weighted composite weights (fallback if logistic regression can't be trained)
COMPOSITE_WEIGHTS = {
    "adj_o_rank": -0.18,   # negative because lower rank = better
    "adj_d_rank": -0.22,   # defense weighted higher
    "barthag": 0.18,
    "seed": -0.14,         # lower seed = better
    "win_pct": 0.08,
    "sos_proxy": 0.10,
    "momentum": 1.00,      # recent barthag - season barthag (positive = trending up)
}

# Champion hard filters (every champion since 2002 meets these)
CHAMPION_ADJ_O_RANK_MAX = 40
CHAMPION_ADJ_D_RANK_MAX = 25


class BracketModel:
    """Scores matchups using logistic regression or weighted composite."""

    def __init__(self):
        self.logreg: LogisticRegression | None = None
        self.scaler: StandardScaler | None = None
        self.trained = False
        self._train_features: list[str] = FEATURE_COLS

    def train(self, historical_csv: str | Path | None = None) -> bool:
        """Train logistic regression on historical tournament data.

        Returns True if training succeeded, False if falling back to composite.
        """
        if historical_csv is None:
            historical_csv = DATA_DIR / "historical_results_2008_2025.csv"

        csv_path = Path(historical_csv)
        if not csv_path.exists():
            console.print("[yellow]No historical data found — using weighted composite model[/yellow]")
            return False

        df = pd.read_csv(csv_path)

        # Need seed and round_reached columns at minimum
        if "seed" not in df.columns or "round_reached" not in df.columns:
            console.print("[yellow]Historical data missing seed/round_reached — using composite[/yellow]")
            return False

        if len(df) < 50:
            console.print(f"[yellow]Only {len(df)} records — too few for regression, using composite[/yellow]")
            return False

        # Use whichever feature columns are available in the historical data
        available_features = [c for c in FEATURE_COLS if c in df.columns]
        if len(available_features) < 3:
            console.print(f"[yellow]Only {len(available_features)} features available — using composite[/yellow]")
            return False

        self._train_features = available_features

        # Binary target: did the team advance at least one round?
        # Train one model: P(advance) given metrics + current round
        df = df.dropna(subset=available_features + ["round_reached"])

        # Create training pairs: for each team, create one row per round they played
        # Label = 1 if they advanced, 0 if they lost in that round
        train_rows = []
        for _, row in df.iterrows():
            round_reached = int(row["round_reached"])
            for r in range(1, 8):  # rounds 1-7
                if r <= round_reached:
                    features = {col: row[col] for col in available_features}
                    features["current_round"] = r
                    features["advanced"] = 1 if r < round_reached else 0
                    # Apply era weighting
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

        Blends logistic regression (trained on historical advancement rates)
        with composite model (direct head-to-head metric comparison).
        Blending ensures injuries (which adjust barthag used by composite)
        always affect predictions, even when logreg is trained.
        """
        composite_prob = self._composite_predict(team_a, team_b)

        if self.trained and self.logreg and self.scaler:
            logreg_prob = self._logreg_predict(team_a, team_b, round_num)
            # Blend: 60% logreg (historical calibration) + 40% composite (injury-aware, direct comparison)
            return 0.6 * logreg_prob + 0.4 * composite_prob

        return composite_prob

    def _logreg_predict(self, team_a: dict, team_b: dict, round_num: int) -> float:
        """Use logistic regression to predict win probability."""
        cols = self._train_features
        features_a = [team_a.get(col, 0) for col in cols] + [round_num]
        features_b = [team_b.get(col, 0) for col in cols] + [round_num]

        X = np.array([features_a, features_b])
        X_scaled = self.scaler.transform(X)

        probs = self.logreg.predict_proba(X_scaled)[:, 1]  # P(advance)
        p_a = probs[0]
        p_b = probs[1]

        # Normalize to get head-to-head probability
        total = p_a + p_b
        if total == 0:
            return 0.5
        return p_a / total

    def _composite_predict(self, team_a: dict, team_b: dict) -> float:
        """Weighted composite score fallback."""
        score_a = self._composite_score(team_a)
        score_b = self._composite_score(team_b)

        # Convert score difference to probability using sigmoid
        diff = score_a - score_b
        prob = 1.0 / (1.0 + np.exp(-diff * 3))  # scale factor for spread
        return float(prob)

    def _composite_score(self, team: dict) -> float:
        """Compute weighted composite score for a single team."""
        score = 0.0
        for col, weight in COMPOSITE_WEIGHTS.items():
            val = team.get(col, 0)
            if val is None:
                continue
            # Normalize ranks to 0-1 scale (assuming 353 teams)
            if "rank" in col:
                val = 1.0 - (val / 353.0)  # invert so higher = better
                score += val * abs(weight)
            elif col == "seed":
                val = 1.0 - (val / 16.0)
                score += val * abs(weight)
            else:
                score += val * weight
        return score

    def passes_champion_filter(self, team: dict) -> bool:
        """Check if a team meets the historical champion profile thresholds."""
        adj_o_rank = team.get("adj_o_rank", 999)
        adj_d_rank = team.get("adj_d_rank", 999)
        return adj_o_rank <= CHAMPION_ADJ_O_RANK_MAX and adj_d_rank <= CHAMPION_ADJ_D_RANK_MAX

    def get_champion_contenders(self, teams: list[dict]) -> list[dict]:
        """Filter teams to only those meeting champion thresholds."""
        return [t for t in teams if self.passes_champion_filter(t)]
