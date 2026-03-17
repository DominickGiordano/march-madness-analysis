"""Bracket structure and tournament simulation."""

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from rich.console import Console

from src.fetch_data import fetch_team_data, get_team_metrics, resolve_team_names
from src.model import BracketModel

console = Console()

# Standard bracket matchups by seed (R64)
# Higher seed vs lower seed in each region
SEED_MATCHUPS = [
    (1, 16), (8, 9), (5, 12), (4, 13),
    (6, 11), (3, 14), (7, 10), (2, 15),
]

ROUND_NAMES = {
    1: "Round of 64",
    2: "Round of 32",
    3: "Sweet 16",
    4: "Elite 8",
    5: "Final Four",
    6: "Championship",
}

# NCAA Final Four pairings by region name (case-insensitive)
# East plays West, South plays Midwest (standard NCAA bracket)
FINAL_FOUR_PAIRINGS = [
    ({"east", "west"}, {"south", "midwest"}),
]


def get_ff_pairings(region_names: list[str]) -> list[tuple[str, str]]:
    """Determine Final Four pairings from region names.

    Uses NCAA standard: East vs West, South vs Midwest.
    Falls back to positional pairing if region names don't match.
    """
    names_lower = [r.lower() for r in region_names]
    name_map = {r.lower(): r for r in region_names}

    # Try standard NCAA pairings
    for pair_a_set, pair_b_set in FINAL_FOUR_PAIRINGS:
        pair_a = [name_map[n] for n in names_lower if n in pair_a_set]
        pair_b = [name_map[n] for n in names_lower if n in pair_b_set]
        if len(pair_a) == 2 and len(pair_b) == 2:
            return [(pair_a[0], pair_a[1]), (pair_b[0], pair_b[1])]

    # Fallback: positional pairing
    return [(region_names[0], region_names[1]), (region_names[2], region_names[3])]


def load_bracket(bracket_path: str | Path) -> dict:
    """Load bracket JSON file.

    Expected format:
    {
        "regions": {
            "east": {"1": "Duke", "2": "...", ...},
            "west": {...},
            "south": {...},
            "midwest": {...}
        }
    }
    """
    with open(bracket_path) as f:
        data = json.load(f)

    # Validate structure
    regions = data.get("regions", {})
    if len(regions) != 4:
        console.print(f"[red]Expected 4 regions, got {len(regions)}[/red]")

    for region_name, seeds in regions.items():
        if len(seeds) < 16:
            console.print(f"[yellow]Region '{region_name}' has only {len(seeds)} seeds (expected 16)[/yellow]")

    return data


def get_all_bracket_teams(bracket: dict) -> list[str]:
    """Extract all team names from bracket."""
    teams = []
    for region_seeds in bracket["regions"].values():
        for team in region_seeds.values():
            if isinstance(team, str):
                teams.append(team)
    return teams


class TournamentSimulator:
    """Simulates the NCAA tournament bracket."""

    def __init__(self, bracket: dict, model: BracketModel, team_data: dict[str, dict]):
        self.bracket = bracket
        self.model = model
        self.team_data = team_data  # {team_name: metrics_dict}
        self.results: dict[str, list] = {}  # {round_name: [matchup_results]}

    def simulate(self) -> dict:
        """Run full tournament simulation.

        Returns dict with keys: rounds, final_four, champion, runner_up, all_picks
        """
        # Simulate each region through Elite 8
        region_winners = {}
        all_rounds = {}

        for region_name, seeds in self.bracket["regions"].items():
            region_results = self._simulate_region(region_name, seeds)
            all_rounds[region_name] = region_results
            # The winner of the region goes to Final Four
            if region_results["elite_8"]:
                region_winners[region_name] = region_results["elite_8"][0]["winner"]

        # Final Four — use standard NCAA pairings (East vs West, South vs Midwest)
        regions = list(self.bracket["regions"].keys())
        ff_matchups = get_ff_pairings(regions)

        final_four_results = []
        finalists = []

        for r1, r2 in ff_matchups:
            team_a = region_winners.get(r1)
            team_b = region_winners.get(r2)
            if team_a and team_b:
                result = self._simulate_matchup(team_a, team_b, round_num=5)
                result["region_matchup"] = f"{r1} vs {r2}"
                final_four_results.append(result)
                finalists.append(result["winner"])

        all_rounds["final_four"] = final_four_results

        # Championship
        championship_result = None
        champion = None
        runner_up = None

        if len(finalists) == 2:
            championship_result = self._simulate_matchup(finalists[0], finalists[1], round_num=6)
            champion = championship_result["winner"]
            runner_up = championship_result["loser"]
            all_rounds["championship"] = [championship_result]

        return {
            "rounds": all_rounds,
            "region_winners": region_winners,
            "final_four": list(region_winners.values()),
            "champion": champion,
            "runner_up": runner_up,
            "champion_confidence": championship_result["win_prob"] if championship_result else 0,
        }

    def _simulate_region(self, region_name: str, seeds: dict) -> dict:
        """Simulate a single region through Elite 8."""
        # R64: seed matchups
        r64_results = []
        r64_winners = []

        for high_seed, low_seed in SEED_MATCHUPS:
            team_a = seeds.get(str(high_seed))
            team_b = seeds.get(str(low_seed))

            if team_a and team_b:
                result = self._simulate_matchup(team_a, team_b, round_num=1)
                result["seeds"] = (high_seed, low_seed)
                r64_results.append(result)
                r64_winners.append(result["winner"])

        # R32: winners play in order (winner of 1v16 vs winner of 8v9, etc.)
        r32_results = []
        r32_winners = []
        for i in range(0, len(r64_winners), 2):
            if i + 1 < len(r64_winners):
                result = self._simulate_matchup(r64_winners[i], r64_winners[i + 1], round_num=2)
                r32_results.append(result)
                r32_winners.append(result["winner"])

        # Sweet 16
        s16_results = []
        s16_winners = []
        for i in range(0, len(r32_winners), 2):
            if i + 1 < len(r32_winners):
                result = self._simulate_matchup(r32_winners[i], r32_winners[i + 1], round_num=3)
                s16_results.append(result)
                s16_winners.append(result["winner"])

        # Elite 8
        e8_results = []
        for i in range(0, len(s16_winners), 2):
            if i + 1 < len(s16_winners):
                result = self._simulate_matchup(s16_winners[i], s16_winners[i + 1], round_num=4)
                e8_results.append(result)

        return {
            "r64": r64_results,
            "r32": r32_results,
            "sweet_16": s16_results,
            "elite_8": e8_results,
        }

    def _simulate_matchup(self, team_a_name: str, team_b_name: str, round_num: int = 1) -> dict:
        """Simulate a single matchup between two teams."""
        metrics_a = self.team_data.get(team_a_name, self._default_metrics(team_a_name))
        metrics_b = self.team_data.get(team_b_name, self._default_metrics(team_b_name))

        win_prob = self.model.predict_win_probability(metrics_a, metrics_b, round_num)

        winner = team_a_name if win_prob >= 0.5 else team_b_name
        loser = team_b_name if win_prob >= 0.5 else team_a_name
        final_prob = win_prob if win_prob >= 0.5 else 1 - win_prob

        return {
            "team_a": team_a_name,
            "team_b": team_b_name,
            "winner": winner,
            "loser": loser,
            "win_prob": round(final_prob, 3),
            "round": round_num,
            "round_name": ROUND_NAMES.get(round_num, f"Round {round_num}"),
            "is_upset": self._is_seed_upset(metrics_a, metrics_b, winner),
        }

    def _is_seed_upset(self, metrics_a: dict, metrics_b: dict, winner: str) -> bool:
        """Check if the result is a seed upset."""
        seed_a = metrics_a.get("seed", 8)
        seed_b = metrics_b.get("seed", 8)
        winner_seed = seed_a if winner == metrics_a.get("team") else seed_b
        loser_seed = seed_b if winner == metrics_a.get("team") else seed_a
        return winner_seed > loser_seed

    def _default_metrics(self, team_name: str) -> dict:
        """Fallback metrics for unresolved teams."""
        return {
            "team": team_name,
            "rank": 175,
            "adj_o": 105.0,
            "adj_o_rank": 175,
            "adj_d": 105.0,
            "adj_d_rank": 175,
            "barthag": 0.5,
            "barthag_rank": 175,
            "seed": 8,
            "win_pct": 0.5,
            "sos_proxy": 0.0,
        }


class MonteCarloSimulator:
    """Run thousands of tournament simulations to generate probability distributions."""

    def __init__(self, bracket: dict, model: BracketModel, team_data: dict[str, dict]):
        self.bracket = bracket
        self.model = model
        self.team_data = team_data
        # Pre-compute all R64 matchup probabilities (these don't change)
        self._prob_cache: dict[tuple[str, str, int], float] = {}

    def _get_win_prob(self, team_a: str, team_b: str, round_num: int) -> float:
        """Get cached win probability for team_a over team_b."""
        key = (team_a, team_b, round_num)
        if key not in self._prob_cache:
            metrics_a = self.team_data.get(team_a, _default_metrics(team_a))
            metrics_b = self.team_data.get(team_b, _default_metrics(team_b))
            self._prob_cache[key] = self.model.predict_win_probability(metrics_a, metrics_b, round_num)
        return self._prob_cache[key]

    def run(self, n_sims: int = 10000, seed: int | None = None) -> "MonteCarloResults":
        """Run n_sims tournament simulations.

        Each simulation randomly resolves every matchup based on win probabilities.
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        # Track results across all simulations
        champion_counts: Counter = Counter()
        final_four_counts: Counter = Counter()
        elite_eight_counts: Counter = Counter()
        sweet_sixteen_counts: Counter = Counter()

        # Track per-matchup win frequencies: {(team_a, team_b, round): team_a_wins}
        matchup_wins: dict[tuple[str, str, int], int] = defaultdict(int)
        matchup_total: dict[tuple[str, str, int], int] = defaultdict(int)

        # Track how far each team advances: {team: [round_reached_per_sim]}
        team_advances: dict[str, list[int]] = defaultdict(list)

        regions = list(self.bracket["regions"].keys())
        ff_pairings = get_ff_pairings(regions)

        for _ in range(n_sims):
            # Simulate each region
            region_winners = {}
            for region_name, seeds in self.bracket["regions"].items():
                winner, region_results = self._sim_region_random(seeds, matchup_wins, matchup_total, team_advances)
                region_winners[region_name] = winner
                elite_eight_counts[winner] += 1

            # Final Four
            ff_teams = list(region_winners.values())
            for t in ff_teams:
                final_four_counts[t] += 1

            # Semifinal 1
            sf1_a, sf1_b = region_winners[ff_pairings[0][0]], region_winners[ff_pairings[0][1]]
            sf1_winner = self._random_matchup(sf1_a, sf1_b, 5, matchup_wins, matchup_total)
            team_advances[sf1_winner].append(6)  # made championship
            loser = sf1_b if sf1_winner == sf1_a else sf1_a
            team_advances[loser].append(5)  # lost in FF

            # Semifinal 2
            sf2_a, sf2_b = region_winners[ff_pairings[1][0]], region_winners[ff_pairings[1][1]]
            sf2_winner = self._random_matchup(sf2_a, sf2_b, 5, matchup_wins, matchup_total)
            team_advances[sf2_winner].append(6)
            loser = sf2_b if sf2_winner == sf2_a else sf2_a
            team_advances[loser].append(5)

            # Championship
            champ = self._random_matchup(sf1_winner, sf2_winner, 6, matchup_wins, matchup_total)
            champion_counts[champ] += 1
            runner_up = sf2_winner if champ == sf1_winner else sf1_winner
            team_advances[champ].append(7)
            team_advances[runner_up].append(6)

        return MonteCarloResults(
            n_sims=n_sims,
            champion_counts=champion_counts,
            final_four_counts=final_four_counts,
            elite_eight_counts=elite_eight_counts,
            sweet_sixteen_counts=sweet_sixteen_counts,
            matchup_wins=dict(matchup_wins),
            matchup_total=dict(matchup_total),
            team_advances=dict(team_advances),
            team_data=self.team_data,
            bracket=self.bracket,
        )

    def _random_matchup(
        self, team_a: str, team_b: str, round_num: int,
        matchup_wins: dict, matchup_total: dict,
    ) -> str:
        """Resolve a matchup randomly based on win probability."""
        prob_a = self._get_win_prob(team_a, team_b, round_num)
        key = (team_a, team_b, round_num)
        matchup_total[key] += 1
        if random.random() < prob_a:
            matchup_wins[key] += 1
            return team_a
        return team_b

    def _sim_region_random(
        self, seeds: dict,
        matchup_wins: dict, matchup_total: dict,
        team_advances: dict,
    ) -> tuple[str, dict]:
        """Simulate one region with random outcomes. Returns (winner, results)."""
        # R64
        r64_winners = []
        for high_seed, low_seed in SEED_MATCHUPS:
            team_a = seeds.get(str(high_seed))
            team_b = seeds.get(str(low_seed))
            if team_a and team_b:
                winner = self._random_matchup(team_a, team_b, 1, matchup_wins, matchup_total)
                r64_winners.append(winner)
                loser = team_b if winner == team_a else team_a
                team_advances[winner].append(2)  # advanced to R32
                team_advances[loser].append(1)    # lost in R64

        # R32
        r32_winners = []
        for i in range(0, len(r64_winners), 2):
            if i + 1 < len(r64_winners):
                winner = self._random_matchup(r64_winners[i], r64_winners[i + 1], 2, matchup_wins, matchup_total)
                r32_winners.append(winner)
                loser = r64_winners[i + 1] if winner == r64_winners[i] else r64_winners[i]
                team_advances[winner].append(3)  # advanced to S16
                team_advances[loser].append(2)

        # Sweet 16
        s16_winners = []
        for i in range(0, len(r32_winners), 2):
            if i + 1 < len(r32_winners):
                winner = self._random_matchup(r32_winners[i], r32_winners[i + 1], 3, matchup_wins, matchup_total)
                s16_winners.append(winner)
                loser = r32_winners[i + 1] if winner == r32_winners[i] else r32_winners[i]
                team_advances[winner].append(4)  # advanced to E8
                team_advances[loser].append(3)

        # Elite 8
        if len(s16_winners) >= 2:
            winner = self._random_matchup(s16_winners[0], s16_winners[1], 4, matchup_wins, matchup_total)
            loser = s16_winners[1] if winner == s16_winners[0] else s16_winners[0]
            team_advances[winner].append(5)  # advanced to FF
            team_advances[loser].append(4)
            return winner, {}

        return s16_winners[0] if s16_winners else "", {}


class MonteCarloResults:
    """Holds and analyzes results from Monte Carlo simulation."""

    def __init__(
        self,
        n_sims: int,
        champion_counts: Counter,
        final_four_counts: Counter,
        elite_eight_counts: Counter,
        sweet_sixteen_counts: Counter,
        matchup_wins: dict,
        matchup_total: dict,
        team_advances: dict,
        team_data: dict,
        bracket: dict,
    ):
        self.n_sims = n_sims
        self.champion_counts = champion_counts
        self.final_four_counts = final_four_counts
        self.elite_eight_counts = elite_eight_counts
        self.sweet_sixteen_counts = sweet_sixteen_counts
        self.matchup_wins = matchup_wins
        self.matchup_total = matchup_total
        self.team_advances = team_advances
        self.team_data = team_data
        self.bracket = bracket

    def champion_probs(self) -> list[tuple[str, float]]:
        """Return [(team, probability)] sorted by likelihood."""
        return [
            (team, count / self.n_sims)
            for team, count in self.champion_counts.most_common()
        ]

    def final_four_probs(self) -> list[tuple[str, float]]:
        """Return [(team, probability)] sorted by likelihood."""
        return [
            (team, count / self.n_sims)
            for team, count in self.final_four_counts.most_common()
        ]

    def elite_eight_probs(self) -> list[tuple[str, float]]:
        return [
            (team, count / self.n_sims)
            for team, count in self.elite_eight_counts.most_common()
        ]

    def matchup_prob(self, team_a: str, team_b: str, round_num: int) -> float:
        """Get simulated win probability for team_a over team_b in a specific round."""
        key = (team_a, team_b, round_num)
        total = self.matchup_total.get(key, 0)
        if total == 0:
            return 0.5
        wins = self.matchup_wins.get(key, 0)
        return wins / total

    def team_avg_round(self, team: str) -> float:
        """Average round reached across all simulations."""
        rounds = self.team_advances.get(team, [])
        if not rounds:
            return 0.0
        return sum(rounds) / len(rounds)

    def build_safe_bracket(self) -> dict:
        return self._build_bracket(strategy="safe")

    def build_risky_bracket(self) -> dict:
        return self._build_bracket(strategy="risky")

    def build_balanced_bracket(self) -> dict:
        return self._build_bracket(strategy="balanced")

    def build_variants(self, n_variants: int = 15) -> list[dict]:
        """Build N bracket variants ranging from all-chalk to aggressive upsets.

        Uses a sliding upset threshold across ALL rounds (not just R64).
        Each variant applies a progressively lower bar for picking underdogs,
        which naturally produces different champions, Final Fours, and upset
        patterns as the threshold drops.

        The threshold slides from 0.55 (only pick underdog if clearly better)
        down to 0.35 (pick any underdog with a real shot).
        """
        # Threshold range: 0.55 (safest) down to 0.35 (riskiest)
        # At 0.55: underdog must have >55% to get picked (almost never)
        # At 0.50: underdog must be favored (the "chalk upsets")
        # At 0.45: near coin-flips go to underdog
        # At 0.40: classic upset territory
        # At 0.35: any underdog with a real chance gets picked
        high = 0.55
        low = 0.35

        all_variants = []
        for idx in range(n_variants):
            pct = idx / max(n_variants - 1, 1)
            threshold = high - pct * (high - low)

            bracket = self._build_bracket_with_threshold(threshold)

            total_log_prob = self._score_bracket(bracket)
            upset_count = self._count_upsets(bracket)

            # Color based on position
            if pct <= 0.33:
                color = "green"
            elif pct <= 0.66:
                color = "amber"
            else:
                color = "red"

            label = self._variant_label_from_position(idx, n_variants)

            bracket.update({
                "variant_id": idx,
                "variant_rank": idx,
                "color": color,
                "label": label,
                "upset_count": upset_count,
                "total_log_prob": round(total_log_prob, 2),
                "threshold": round(threshold, 3),
            })
            all_variants.append(bracket)

        return all_variants

    def _build_bracket_with_threshold(self, upset_threshold: float) -> dict:
        """Build a complete bracket using a single upset threshold for ALL rounds.

        For each matchup: if the underdog's sim win rate >= threshold, pick the underdog.
        Otherwise pick the favorite. This applies to every round including FF and Championship.
        """
        regions = list(self.bracket["regions"].keys())
        all_rounds = {}
        region_winners = {}

        for region_name, seeds in self.bracket["regions"].items():
            r64_results = []
            r64_winners = []
            for high_seed, low_seed in SEED_MATCHUPS:
                team_a = seeds.get(str(high_seed))
                team_b = seeds.get(str(low_seed))
                if not team_a or not team_b:
                    continue
                winner = self._pick_by_threshold(team_a, team_b, 1, upset_threshold)
                r64_results.append(self._matchup_result(team_a, team_b, winner, 1))
                r64_winners.append(winner)

            r32_results = []
            r32_winners = []
            for i in range(0, len(r64_winners), 2):
                if i + 1 < len(r64_winners):
                    winner = self._pick_by_threshold(r64_winners[i], r64_winners[i + 1], 2, upset_threshold)
                    r32_results.append(self._matchup_result(r64_winners[i], r64_winners[i + 1], winner, 2))
                    r32_winners.append(winner)

            s16_results = []
            s16_winners = []
            for i in range(0, len(r32_winners), 2):
                if i + 1 < len(r32_winners):
                    winner = self._pick_by_threshold(r32_winners[i], r32_winners[i + 1], 3, upset_threshold)
                    s16_results.append(self._matchup_result(r32_winners[i], r32_winners[i + 1], winner, 3))
                    s16_winners.append(winner)

            e8_results = []
            e8_winner = ""
            if len(s16_winners) >= 2:
                winner = self._pick_by_threshold(s16_winners[0], s16_winners[1], 4, upset_threshold)
                e8_results.append(self._matchup_result(s16_winners[0], s16_winners[1], winner, 4))
                e8_winner = winner

            all_rounds[region_name] = {
                "r64": r64_results, "r32": r32_results,
                "sweet_16": s16_results, "elite_8": e8_results,
            }
            region_winners[region_name] = e8_winner

        # Final Four + Championship
        ff_pairings = get_ff_pairings(regions)
        sf1_a, sf1_b = region_winners[ff_pairings[0][0]], region_winners[ff_pairings[0][1]]
        sf1_winner = self._pick_by_threshold(sf1_a, sf1_b, 5, upset_threshold)

        sf2_a, sf2_b = region_winners[ff_pairings[1][0]], region_winners[ff_pairings[1][1]]
        sf2_winner = self._pick_by_threshold(sf2_a, sf2_b, 5, upset_threshold)

        all_rounds["final_four"] = [
            self._matchup_result(sf1_a, sf1_b, sf1_winner, 5),
            self._matchup_result(sf2_a, sf2_b, sf2_winner, 5),
        ]

        champ = self._pick_by_threshold(sf1_winner, sf2_winner, 6, upset_threshold)
        runner_up = sf2_winner if champ == sf1_winner else sf1_winner
        all_rounds["championship"] = [self._matchup_result(sf1_winner, sf2_winner, champ, 6)]

        champ_prob = self.champion_counts.get(champ, 0) / self.n_sims

        return {
            "rounds": all_rounds,
            "region_winners": region_winners,
            "final_four": list(region_winners.values()),
            "champion": champ,
            "runner_up": runner_up,
            "champion_confidence": champ_prob,
            "strategy": "variant",
        }

    def _pick_by_threshold(self, team_a: str, team_b: str, round_num: int, upset_threshold: float) -> str:
        """Pick winner using simulation data and a single upset threshold.

        If the underdog's sim win rate >= threshold, pick the underdog.
        Otherwise pick the favorite (higher sim win rate).
        """
        key = (team_a, team_b, round_num)
        total = self.matchup_total.get(key, 0)
        if total > 0:
            prob_a = self.matchup_wins.get(key, 0) / total
        else:
            rev_key = (team_b, team_a, round_num)
            rev_total = self.matchup_total.get(rev_key, 0)
            if rev_total > 0:
                prob_a = 1.0 - (self.matchup_wins.get(rev_key, 0) / rev_total)
            else:
                prob_a = 0.5

        seed_a = self.team_data.get(team_a, {}).get("seed", 8)
        seed_b = self.team_data.get(team_b, {}).get("seed", 8)

        # Determine favorite and underdog by sim probability
        if prob_a >= 0.5:
            fav, dog = team_a, team_b
            dog_rate = 1.0 - prob_a
        else:
            fav, dog = team_b, team_a
            dog_rate = prob_a

        # Pick underdog if their win rate meets the threshold
        if dog_rate >= upset_threshold:
            return dog
        return fav

    def _variant_label_from_position(self, idx: int, total: int) -> str:
        """Generate a label based on position in the variant spectrum."""
        labels_15 = [
            "All Chalk", "Chalk+1", "Chalk+2", "Light Upsets",
            "Conservative", "Lean Safe", "Moderate",
            "Balanced", "Lean Aggressive",
            "Aggressive", "Bold", "Risky",
            "Very Risky", "Chaos Lite", "Maximum Chaos",
        ]
        if idx < len(labels_15):
            return labels_15[idx]
        return f"Variant {idx + 1}"

    def _score_bracket(self, bracket: dict) -> float:
        """Score a bracket by sum of log win probabilities."""
        log_sum = 0.0
        for region_name, region_data in bracket.get("rounds", {}).items():
            if isinstance(region_data, dict):
                for matchups in region_data.values():
                    if isinstance(matchups, list):
                        for m in matchups:
                            wp = m.get("win_prob", 0.5)
                            log_sum += np.log(max(wp, 0.01))
            elif isinstance(region_data, list):
                for m in region_data:
                    if isinstance(m, dict):
                        wp = m.get("win_prob", 0.5)
                        log_sum += np.log(max(wp, 0.01))
        return log_sum

    def _count_upsets(self, bracket: dict) -> int:
        """Count upset picks in a bracket."""
        count = 0
        for region_name, region_data in bracket.get("rounds", {}).items():
            if isinstance(region_data, dict):
                for matchups in region_data.values():
                    if isinstance(matchups, list):
                        count += sum(1 for m in matchups if m.get("is_upset"))
            elif isinstance(region_data, list):
                count += sum(1 for m in region_data if isinstance(m, dict) and m.get("is_upset"))
        return count

    def _variant_label(self, strategy: str, rank: int, total: int) -> str:
        """Human-readable label for a bracket variant."""
        labels = {
            "safe": ["Ultra Safe", "Very Safe", "Safe", "Safe+", "Safe Aggressive"],
            "balanced": ["Conservative", "Lean Safe", "Balanced", "Lean Risky", "Aggressive"],
            "risky": ["Mild Risk", "Moderate Risk", "Risky", "Very Risky", "Max Risk"],
        }
        return labels.get(strategy, [""] * total)[rank]

    def _build_bracket(self, strategy: str, threshold_offset: float = 0.0) -> dict:
        """Core bracket builder used by all three strategies."""
        regions = list(self.bracket["regions"].keys())
        all_rounds = {}
        region_winners = {}

        for region_name, seeds in self.bracket["regions"].items():
            region_result, winner = self._build_region(seeds, strategy, threshold_offset)
            all_rounds[region_name] = region_result
            region_winners[region_name] = winner

        # Final Four — use standard NCAA pairings
        ff_pairings = get_ff_pairings(regions)
        sf1_a, sf1_b = region_winners[ff_pairings[0][0]], region_winners[ff_pairings[0][1]]
        sf1_winner = self._pick_winner(sf1_a, sf1_b, 5, strategy, threshold_offset=threshold_offset)

        sf2_a, sf2_b = region_winners[ff_pairings[1][0]], region_winners[ff_pairings[1][1]]
        sf2_winner = self._pick_winner(sf2_a, sf2_b, 5, strategy, threshold_offset=threshold_offset)

        all_rounds["final_four"] = [
            self._matchup_result(sf1_a, sf1_b, sf1_winner, 5),
            self._matchup_result(sf2_a, sf2_b, sf2_winner, 5),
        ]

        # Championship
        champ = self._pick_winner(sf1_winner, sf2_winner, 6, strategy, threshold_offset=threshold_offset)
        runner_up = sf2_winner if champ == sf1_winner else sf1_winner
        all_rounds["championship"] = [self._matchup_result(sf1_winner, sf2_winner, champ, 6)]

        champ_prob = self.champion_counts.get(champ, 0) / self.n_sims

        return {
            "rounds": all_rounds,
            "region_winners": region_winners,
            "final_four": list(region_winners.values()),
            "champion": champ,
            "runner_up": runner_up,
            "champion_confidence": champ_prob,
            "strategy": strategy,
        }

    def _build_region(self, seeds: dict, strategy: str, threshold_offset: float = 0.0) -> tuple[dict, str]:
        """Build one region's bracket for a given strategy."""
        r64_results = []
        r64_winners = []
        for high_seed, low_seed in SEED_MATCHUPS:
            team_a = seeds.get(str(high_seed))
            team_b = seeds.get(str(low_seed))
            if team_a and team_b:
                winner = self._pick_winner(team_a, team_b, 1, strategy, threshold_offset=threshold_offset)
                r64_results.append(self._matchup_result(team_a, team_b, winner, 1))
                r64_winners.append(winner)

        r32_results = []
        r32_winners = []
        for i in range(0, len(r64_winners), 2):
            if i + 1 < len(r64_winners):
                winner = self._pick_winner(r64_winners[i], r64_winners[i + 1], 2, strategy, threshold_offset=threshold_offset)
                r32_results.append(self._matchup_result(r64_winners[i], r64_winners[i + 1], winner, 2))
                r32_winners.append(winner)

        s16_results = []
        s16_winners = []
        for i in range(0, len(r32_winners), 2):
            if i + 1 < len(r32_winners):
                winner = self._pick_winner(r32_winners[i], r32_winners[i + 1], 3, strategy, threshold_offset=threshold_offset)
                s16_results.append(self._matchup_result(r32_winners[i], r32_winners[i + 1], winner, 3))
                s16_winners.append(winner)

        e8_results = []
        e8_winner = ""
        if len(s16_winners) >= 2:
            winner = self._pick_winner(s16_winners[0], s16_winners[1], 4, strategy, threshold_offset=threshold_offset)
            e8_results.append(self._matchup_result(s16_winners[0], s16_winners[1], winner, 4))
            e8_winner = winner

        return {
            "r64": r64_results,
            "r32": r32_results,
            "sweet_16": s16_results,
            "elite_8": e8_results,
        }, e8_winner

    def _pick_winner(self, team_a: str, team_b: str, round_num: int, strategy: str, threshold_offset: float = 0.0) -> str:
        """Pick a winner based on strategy."""
        # Get simulated probability
        key = (team_a, team_b, round_num)
        total = self.matchup_total.get(key, 0)
        if total > 0:
            prob_a = self.matchup_wins.get(key, 0) / total
        else:
            # Fallback: check reverse key
            rev_key = (team_b, team_a, round_num)
            rev_total = self.matchup_total.get(rev_key, 0)
            if rev_total > 0:
                prob_a = 1.0 - (self.matchup_wins.get(rev_key, 0) / rev_total)
            else:
                prob_a = 0.5

        seed_a = self.team_data.get(team_a, {}).get("seed", 8)
        seed_b = self.team_data.get(team_b, {}).get("seed", 8)
        is_underdog_a = seed_a > seed_b

        # threshold_offset: negative = more upsets, positive = fewer upsets
        off = threshold_offset

        if strategy == "safe":
            # Safe uses a high bar — only pick underdog if they're actually favored
            # Offset slides how much the underdog needs to be favored
            safe_threshold = 0.50 - off  # offset +0.04 → need 0.46, offset -0.02 → need 0.52
            return team_a if prob_a >= safe_threshold else team_b

        elif strategy == "risky":
            if round_num <= 2:
                upset_threshold = 0.40 + off
            elif round_num <= 4:
                upset_threshold = 0.43 + off
            else:
                upset_threshold = 0.46 + off

            if is_underdog_a and prob_a >= upset_threshold:
                return team_a
            elif not is_underdog_a and (1 - prob_a) >= upset_threshold:
                return team_b
            return team_a if prob_a >= 0.5 else team_b

        elif strategy == "balanced":
            if round_num <= 2:
                upset_threshold = 0.45 + off
            elif round_num <= 4:
                upset_threshold = 0.47 + off
            else:
                upset_threshold = 0.49 + off

            if is_underdog_a and prob_a >= upset_threshold:
                return team_a
            elif not is_underdog_a and (1 - prob_a) >= upset_threshold:
                return team_b
            return team_a if prob_a >= 0.5 else team_b

        # Default: pick favorite
        return team_a if prob_a >= 0.5 else team_b

    def _matchup_result(self, team_a: str, team_b: str, winner: str, round_num: int) -> dict:
        """Build a matchup result dict."""
        loser = team_b if winner == team_a else team_a

        key = (team_a, team_b, round_num)
        total = self.matchup_total.get(key, 0)
        if total > 0:
            prob = self.matchup_wins.get(key, 0) / total
            win_prob = prob if winner == team_a else 1 - prob
        else:
            win_prob = 0.5

        seed_a = self.team_data.get(team_a, {}).get("seed", 8)
        seed_b = self.team_data.get(team_b, {}).get("seed", 8)
        winner_seed = seed_a if winner == team_a else seed_b
        loser_seed = seed_b if winner == team_a else seed_a

        return {
            "team_a": team_a,
            "team_b": team_b,
            "winner": winner,
            "loser": loser,
            "win_prob": round(win_prob, 3),
            "round": round_num,
            "round_name": ROUND_NAMES.get(round_num, f"Round {round_num}"),
            "is_upset": winner_seed > loser_seed,
        }


def _default_metrics(team_name: str) -> dict:
    """Fallback metrics for unresolved teams."""
    return {
        "team": team_name,
        "rank": 175,
        "adj_o": 105.0,
        "adj_o_rank": 175,
        "adj_d": 105.0,
        "adj_d_rank": 175,
        "barthag": 0.5,
        "barthag_rank": 175,
        "seed": 8,
        "win_pct": 0.5,
        "sos_proxy": 0.0,
    }


def build_team_data_map(
    bracket: dict,
    team_df,
    name_mapping: dict[str, str],
) -> dict[str, dict]:
    """Build a dict mapping bracket team names to their full metrics."""
    from src.fetch_data import get_team_metrics

    team_data = {}
    for region_name, seeds in bracket["regions"].items():
        for seed_str, team_name in seeds.items():
            bt_name = name_mapping.get(team_name, team_name)
            metrics = get_team_metrics(team_df, bt_name)
            if metrics:
                metrics["seed"] = int(seed_str)
                team_data[team_name] = metrics
            else:
                console.print(f"[yellow]No metrics for {team_name} (looked up: {bt_name})[/yellow]")
                team_data[team_name] = {
                    "team": team_name,
                    "rank": 175,
                    "adj_o": 105.0,
                    "adj_o_rank": 175,
                    "adj_d": 105.0,
                    "adj_d_rank": 175,
                    "barthag": 0.5,
                    "barthag_rank": 175,
                    "seed": int(seed_str),
                    "win_pct": 0.5,
                    "sos_proxy": 0.0,
                }
    return team_data
