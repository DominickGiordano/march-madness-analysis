"""Rich terminal output and CSV/JSON export."""

import csv
import json
from pathlib import Path

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

ROUND_LABELS = {1: "R64", 2: "R32", 3: "S16", 4: "E8", 5: "F4", 6: "Champ"}


def render_monte_carlo(mc_results, team_data: dict[str, dict], upset_alerts: list[dict]):
    """Render full Monte Carlo simulation results."""
    from src.model import CHAMPION_ADJ_D_RANK_MAX, CHAMPION_ADJ_O_RANK_MAX

    console.print()
    console.print(Panel(
        f"[bold white]2026 MARCH MADNESS BRACKET ANALYZER[/bold white]\n"
        f"[dim]{mc_results.n_sims:,} simulations[/dim]",
        style="bold blue",
        expand=False,
    ))
    console.print()

    # --- Champion Probabilities ---
    console.print("[bold]CHAMPION PROBABILITIES[/bold]")
    champ_probs = mc_results.champion_probs()
    for team, prob in champ_probs[:10]:
        seed = team_data.get(team, {}).get("seed", "?")
        bar = _prob_bar(prob, max_prob=champ_probs[0][1])
        console.print(f"  #{seed:<2} {team:<20} {bar} {prob:>6.1%}")
    console.print()

    # --- Final Four Probabilities ---
    console.print("[bold]FINAL FOUR PROBABILITIES[/bold]")
    ff_probs = mc_results.final_four_probs()
    for team, prob in ff_probs[:12]:
        seed = team_data.get(team, {}).get("seed", "?")
        bar = _prob_bar(prob, max_prob=ff_probs[0][1])
        console.print(f"  #{seed:<2} {team:<20} {bar} {prob:>6.1%}")
    console.print()

    # --- Upset Alerts ---
    if upset_alerts:
        console.print("[bold red]UPSET ALERTS[/bold red] (watch these)")
        for alert in upset_alerts:
            reasons_str = ", ".join(alert["reasons"])
            conf_bar = "!" * min(int(alert["confidence"] * 5), 5)
            console.print(f"  [{conf_bar}] R1: {alert['matchup']} — {reasons_str}")
        console.print()

    # --- Three Bracket Strategies ---
    safe = mc_results.build_safe_bracket()
    risky = mc_results.build_risky_bracket()
    balanced = mc_results.build_balanced_bracket()

    _render_three_brackets(safe, risky, balanced, team_data, mc_results)

    # --- Confidence Scores ---
    _render_confidence_table(team_data, mc_results)


def _prob_bar(prob: float, max_prob: float = 1.0, width: int = 20) -> str:
    """Render a text probability bar."""
    if max_prob <= 0:
        return " " * width
    filled = int((prob / max_prob) * width)
    return "[green]" + "█" * filled + "[/green]" + "[dim]░[/dim]" * (width - filled)


def _render_three_brackets(safe: dict, risky: dict, balanced: dict, team_data: dict, mc_results):
    """Render the three bracket strategies side by side."""

    for label, bracket, style in [
        ("SAFE BRACKET", safe, "green"),
        ("BALANCED BRACKET", balanced, "yellow"),
        ("RISKY BRACKET", risky, "red"),
    ]:
        strategy = bracket.get("strategy", "")
        champ = bracket["champion"]
        champ_prob = bracket["champion_confidence"]
        seed = team_data.get(champ, {}).get("seed", "?")
        ff = bracket["final_four"]

        desc = {
            "safe": "Pick favorites everywhere. Maximizes expected correct picks.",
            "balanced": "Selective upsets in early rounds, chalk in late rounds.",
            "risky": "Picks underdogs with >35% win probability. High ceiling if upsets hit.",
        }.get(strategy, "")

        console.print(Panel(
            f"[bold {style}]{label}[/bold {style}]  [dim]{desc}[/dim]",
            expand=True,
        ))

        console.print(f"  Champion: [bold {style}]#{seed} {champ}[/bold {style}] "
                      f"(wins title in {champ_prob:.1%} of sims)")
        console.print(f"  Final Four: {' | '.join(ff)}")
        console.print()

        # Round-by-round picks
        rounds = bracket.get("rounds", {})
        for region_name, region_data in rounds.items():
            if region_name in ("final_four", "championship"):
                continue
            if not region_data or not isinstance(region_data, dict):
                continue
            console.print(f"    [bold cyan]{region_name.upper()}[/bold cyan]")
            for round_key, round_label in [("r64", "R64"), ("r32", "R32"), ("sweet_16", "S16"), ("elite_8", "E8")]:
                matchups = region_data.get(round_key, [])
                if matchups:
                    picks = []
                    for m in matchups:
                        upset_marker = " *" if m.get("is_upset") else ""
                        picks.append(f"{m['winner']} ({m['win_prob']:.0%}){upset_marker}")
                    console.print(f"      {round_label}: {' | '.join(picks)}")

        # Final Four + Championship
        ff_matchups = rounds.get("final_four", [])
        if ff_matchups:
            console.print(f"    [bold cyan]FINAL FOUR[/bold cyan]")
            for m in ff_matchups:
                console.print(f"      {m['winner']} over {m['loser']} ({m['win_prob']:.0%})")
        champ_matchups = rounds.get("championship", [])
        if champ_matchups:
            m = champ_matchups[0]
            console.print(f"      [bold {style}]CHAMP: {m['winner']} over {m['loser']} ({m['win_prob']:.0%})[/bold {style}]")

        # Count upsets in this bracket
        upset_count = 0
        for region_data in rounds.values():
            if isinstance(region_data, dict):
                for matchups in region_data.values():
                    if isinstance(matchups, list):
                        upset_count += sum(1 for m in matchups if m.get("is_upset"))
            elif isinstance(region_data, list):
                upset_count += sum(1 for m in region_data if isinstance(m, dict) and m.get("is_upset"))

        console.print(f"\n    [dim]Total upsets picked: {upset_count}[/dim]")
        console.print()


def _render_confidence_table(team_data: dict[str, dict], mc_results):
    """Render team confidence scores with Monte Carlo probabilities."""
    from src.model import CHAMPION_ADJ_D_RANK_MAX, CHAMPION_ADJ_O_RANK_MAX

    console.print("[bold]TEAM ADVANCEMENT PROBABILITIES[/bold]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Team", style="white", width=20)
    table.add_column("Seed", justify="center", width=5)
    table.add_column("Barthag", justify="right", width=8)
    table.add_column("S16 %", justify="right", width=7)
    table.add_column("E8 %", justify="right", width=7)
    table.add_column("F4 %", justify="right", width=7)
    table.add_column("Champ %", justify="right", width=8)
    table.add_column("Filter", justify="center", width=7)

    # Build probability lookup
    champ_dict = dict(mc_results.champion_probs())
    ff_dict = dict(mc_results.final_four_probs())
    e8_dict = dict(mc_results.elite_eight_probs())

    # Sort by champion probability
    sorted_teams = sorted(
        team_data.items(),
        key=lambda x: champ_dict.get(x[0], 0),
        reverse=True,
    )

    for team_name, metrics in sorted_teams[:25]:
        passes = (
            metrics.get("adj_o_rank", 999) <= CHAMPION_ADJ_O_RANK_MAX
            and metrics.get("adj_d_rank", 999) <= CHAMPION_ADJ_D_RANK_MAX
        )
        champ_flag = "[green]YES[/green]" if passes else "[dim]no[/dim]"

        avg_round = mc_results.team_avg_round(team_name)
        s16_prob = 0.0
        advances = mc_results.team_advances.get(team_name, [])
        if advances:
            s16_prob = sum(1 for r in advances if r >= 3) / len(advances)

        table.add_row(
            team_name,
            str(metrics.get("seed", "?")),
            f"{metrics.get('barthag', 0):.4f}",
            f"{s16_prob:.0%}",
            f"{e8_dict.get(team_name, 0):.0%}",
            f"{ff_dict.get(team_name, 0):.0%}",
            f"{champ_dict.get(team_name, 0):.1%}",
            champ_flag,
        )

    console.print(table)
    console.print()


# --- Legacy single-bracket rendering (kept for backward compat) ---

def render_results(results: dict, team_data: dict[str, dict], upset_alerts: list[dict]):
    """Render single deterministic bracket results."""
    console.print()
    console.print(Panel(
        "[bold white]2026 MARCH MADNESS BRACKET ANALYZER[/bold white]",
        style="bold blue",
        expand=False,
    ))
    console.print()

    champion = results.get("champion")
    confidence = results.get("champion_confidence", 0)
    if champion:
        champ_metrics = team_data.get(champion, {})
        console.print("[bold]CHAMPION PREDICTION[/bold]")
        console.print(f"  [bold yellow]>> {champion}[/bold yellow] (confidence: {confidence:.0%})")
        if champ_metrics:
            console.print(f"     AdjO rank: {champ_metrics.get('adj_o_rank', '?')} | "
                         f"AdjD rank: {champ_metrics.get('adj_d_rank', '?')} | "
                         f"Barthag: {champ_metrics.get('barthag', 0):.4f}")
        console.print()

    final_four = results.get("final_four", [])
    if final_four:
        console.print("[bold]FINAL FOUR[/bold]")
        console.print(f"  {' | '.join(final_four)}")
        console.print()

    if upset_alerts:
        console.print("[bold red]UPSET ALERTS[/bold red] (watch these)")
        for alert in upset_alerts:
            reasons_str = ", ".join(alert["reasons"])
            conf_bar = "!" * min(int(alert["confidence"] * 5), 5)
            console.print(f"  [{conf_bar}] R1: {alert['matchup']} — {reasons_str}")
        console.print()


def export_csv(results: dict, team_data: dict[str, dict], output_path: str | Path):
    """Export picks to CSV."""
    path = Path(output_path)

    rows = []
    rounds = results.get("rounds", {})

    for region_name, region_data in rounds.items():
        if region_name in ("final_four", "championship"):
            matchups = region_data
        else:
            matchups = []
            for round_data in region_data.values():
                if isinstance(round_data, list):
                    matchups.extend(round_data)

        for m in matchups:
            if isinstance(m, dict):
                rows.append({
                    "region": region_name,
                    "round": m.get("round_name", ""),
                    "team_a": m.get("team_a", ""),
                    "team_b": m.get("team_b", ""),
                    "winner": m.get("winner", ""),
                    "win_probability": m.get("win_prob", ""),
                    "is_upset": m.get("is_upset", False),
                })

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["region", "round", "team_a", "team_b", "winner", "win_probability", "is_upset"])
        writer.writeheader()
        writer.writerows(rows)

    console.print(f"[green]Exported {len(rows)} matchups to {path}[/green]")


def export_json(results: dict, team_data: dict[str, dict], output_path: str | Path):
    """Export full results to JSON."""
    path = Path(output_path)

    output = {
        "champion": results.get("champion"),
        "champion_confidence": results.get("champion_confidence"),
        "runner_up": results.get("runner_up"),
        "final_four": results.get("final_four"),
        "region_winners": results.get("region_winners"),
        "team_scores": {
            name: {k: v for k, v in metrics.items() if isinstance(v, (int, float, str))}
            for name, metrics in team_data.items()
        },
    }

    with open(path, "w") as f:
        json.dump(output, f, indent=2)

    console.print(f"[green]Exported results to {path}[/green]")


def export_all_brackets(mc_results, team_data: dict, output_dir: str | Path):
    """Export all three bracket strategies to separate CSVs."""
    path = Path(output_dir)
    path.mkdir(exist_ok=True)

    for strategy_name, bracket in [
        ("safe", mc_results.build_safe_bracket()),
        ("balanced", mc_results.build_balanced_bracket()),
        ("risky", mc_results.build_risky_bracket()),
    ]:
        export_csv(bracket, team_data, path / f"bracket_{strategy_name}_2026.csv")


def export_ui_json(
    mc_results,
    mc_simulator,
    team_data: dict[str, dict],
    upset_alerts: list[dict],
    bracket_data: dict,
    output_path: str | Path,
    lock_threshold: float = 0.90,
):
    """Export full simulation data as a fat JSON for the React UI.

    Contains: original bracket, three strategy brackets, full pairwise probability
    matrix, team metrics, upset alerts, and advancement probabilities.

    Matchups where the favorite wins > lock_threshold of simulations are flagged
    as locked — the UI should prevent overrides on these (they're near-certain).
    """
    from datetime import datetime

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Build the three strategy brackets
    safe = mc_results.build_safe_bracket()
    balanced = mc_results.build_balanced_bracket()
    risky = mc_results.build_risky_bracket()

    def _serialize_matchup(m: dict) -> dict:
        """Convert a matchup dict to JSON-safe format with lock flag."""
        wp = m["win_prob"]
        return {
            "teamA": m["team_a"],
            "teamB": m["team_b"],
            "winner": m["winner"],
            "winProb": wp,
            "round": m["round"],
            "isUpset": m.get("is_upset", False),
            "locked": wp >= lock_threshold,
        }

    def _serialize_bracket(b: dict) -> dict:
        """Convert a bracket dict to a JSON-safe format."""
        rounds = {}
        for region_name, region_data in b.get("rounds", {}).items():
            if isinstance(region_data, dict):
                rounds[region_name] = {
                    round_key: [_serialize_matchup(m) for m in matchups]
                    for round_key, matchups in region_data.items()
                    if isinstance(matchups, list)
                }
            elif isinstance(region_data, list):
                rounds[region_name] = [
                    _serialize_matchup(m)
                    for m in region_data
                    if isinstance(m, dict)
                ]
        result = {
            "champion": b.get("champion"),
            "championConfidence": b.get("champion_confidence"),
            "runnerUp": b.get("runner_up"),
            "finalFour": b.get("final_four"),
            "regionWinners": b.get("region_winners"),
            "strategy": b.get("strategy"),
            "rounds": rounds,
        }
        # Add variant metadata if present
        if "variant_id" in b:
            result["variantId"] = b["variant_id"]
            result["variantRank"] = b["variant_rank"]
            result["color"] = b["color"]
            result["label"] = b["label"]
            result["upsetCount"] = b["upset_count"]
            result["totalLogProb"] = b["total_log_prob"]
        return result

    # Build probability matrix: all bracket teams × all bracket teams × all rounds
    # This lets the frontend compute win probability for ANY override scenario
    all_teams = list(team_data.keys())
    prob_matrix: dict[str, float] = {}

    for i, team_a in enumerate(all_teams):
        for team_b in all_teams[i + 1:]:
            for round_num in range(1, 7):
                prob = mc_simulator._get_win_prob(team_a, team_b, round_num)
                # Store as "TeamA|TeamB|round" -> P(A wins)
                prob_matrix[f"{team_a}|{team_b}|{round_num}"] = round(prob, 4)

    # Team metrics (JSON-safe)
    team_metrics = {}
    for name, metrics in team_data.items():
        team_metrics[name] = {
            k: v for k, v in metrics.items()
            if isinstance(v, (int, float, str, bool)) and k != "team"
        }

    # Advancement probabilities from MC results
    champ_dict = dict(mc_results.champion_probs())
    ff_dict = dict(mc_results.final_four_probs())
    e8_dict = dict(mc_results.elite_eight_probs())

    advancement = {}
    for team in all_teams:
        advances = mc_results.team_advances.get(team, [])
        s16_prob = sum(1 for r in advances if r >= 3) / len(advances) if advances else 0
        advancement[team] = {
            "s16": round(s16_prob, 4),
            "e8": round(e8_dict.get(team, 0), 4),
            "f4": round(ff_dict.get(team, 0), 4),
            "champ": round(champ_dict.get(team, 0), 4),
        }

    # Upset alerts (JSON-safe)
    alerts = [
        {
            "region": a["region"],
            "higherSeed": a["higher_seed"],
            "higherTeam": a["higher_team"],
            "lowerSeed": a["lower_seed"],
            "lowerTeam": a["lower_team"],
            "reasons": a["reasons"],
            "confidence": round(a["confidence"], 3),
            "matchup": a["matchup"],
        }
        for a in upset_alerts
    ]

    # Build 15 bracket variants from swing matchups
    console.print("[bold]Building bracket variants from swing matchups...[/bold]")
    variants_raw = mc_results.build_variants(n_variants=15)
    variants = [_serialize_bracket(v) for v in variants_raw]

    output = {
        "meta": {
            "nSims": mc_results.n_sims,
            "timestamp": datetime.now().isoformat(),
            "totalTeams": len(all_teams),
            "lockThreshold": lock_threshold,
        },
        "bracket": bracket_data,
        "strategies": {
            "safe": _serialize_bracket(safe),
            "balanced": _serialize_bracket(balanced),
            "risky": _serialize_bracket(risky),
        },
        "variants": variants,
        "probMatrix": prob_matrix,
        "teamData": team_metrics,
        "advancement": advancement,
        "upsetAlerts": alerts,
    }

    with open(path, "w") as f:
        json.dump(output, f)

    size_mb = path.stat().st_size / (1024 * 1024)
    console.print(f"[green]Exported UI JSON ({size_mb:.1f} MB, {len(prob_matrix)} prob entries) to {path}[/green]")
