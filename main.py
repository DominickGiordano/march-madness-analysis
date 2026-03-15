"""March Madness Bracket Analyzer — CLI entry point."""

from pathlib import Path

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="2026 March Madness Bracket Analyzer")


def _load_everything(bracket: str, injuries_file: str | None = None, no_train: bool = False):
    """Shared setup: load bracket, fetch data, resolve names, train model."""
    from src.bracket import build_team_data_map, get_all_bracket_teams, load_bracket
    from src.fetch_data import fetch_team_data, resolve_team_names
    from src.injuries import apply_injury_adjustments, load_injuries
    from src.model import BracketModel

    console.print("[bold]Loading bracket...[/bold]")
    bracket_data = load_bracket(bracket)
    bracket_teams = get_all_bracket_teams(bracket_data)
    console.print(f"  {len(bracket_teams)} teams loaded")

    console.print("[bold]Fetching 2026 team data from Barttorvik...[/bold]")
    team_df = fetch_team_data(2026)

    console.print("[bold]Resolving team names...[/bold]")
    name_mapping = resolve_team_names(bracket_teams, team_df)
    console.print(f"  {len(name_mapping)}/{len(bracket_teams)} resolved")

    team_data = build_team_data_map(bracket_data, team_df, name_mapping)

    injuries = load_injuries(injuries_file)
    if injuries:
        console.print("[bold]Applying injury adjustments...[/bold]")
        team_data = apply_injury_adjustments(team_data, injuries)

    console.print("[bold]Training model...[/bold]")
    model = BracketModel()
    if not no_train:
        model.train()
    if not model.trained:
        console.print("[yellow]Using weighted composite model[/yellow]")

    return bracket_data, team_data, model


@app.command()
def run(
    bracket: str = typer.Option(..., help="Path to bracket JSON file"),
    sims: int = typer.Option(10000, help="Number of Monte Carlo simulations"),
    export: str = typer.Option(None, help="Export format: 'csv' or 'json' or 'all'"),
    no_train: bool = typer.Option(False, help="Skip logistic regression, use composite model"),
    injuries_file: str = typer.Option(None, help="Path to injuries JSON (default: data/injuries.json)"),
):
    """Run Monte Carlo simulation and display safe/balanced/risky brackets."""
    from src.bracket import MonteCarloSimulator
    from src.output import export_all_brackets, export_csv, export_json, render_monte_carlo
    from src.upsets import detect_upsets

    bracket_data, team_data, model = _load_everything(bracket, injuries_file, no_train)

    console.print("[bold]Scanning for upset alerts...[/bold]")
    upset_alerts = detect_upsets(team_data, bracket_data)

    console.print(f"[bold]Running {sims:,} simulations...[/bold]")
    mc = MonteCarloSimulator(bracket_data, model, team_data)
    mc_results = mc.run(n_sims=sims)

    render_monte_carlo(mc_results, team_data, upset_alerts)

    if export:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        if export.lower() == "all" or export.lower() == "csv":
            export_all_brackets(mc_results, team_data, output_dir)
        if export.lower() == "json":
            balanced = mc_results.build_balanced_bracket()
            export_json(balanced, team_data, output_dir / "results_2026.json")


@app.command()
def upsets(
    bracket: str = typer.Option(..., help="Path to bracket JSON file"),
    injuries_file: str = typer.Option(None, help="Path to injuries JSON"),
):
    """Show upset alerts only."""
    from src.upsets import detect_upsets

    bracket_data, team_data, _ = _load_everything(bracket, injuries_file, no_train=True)
    alerts = detect_upsets(team_data, bracket_data)

    if not alerts:
        console.print("[green]No significant upset alerts detected.[/green]")
        return

    console.print(f"\n[bold red]UPSET ALERTS ({len(alerts)} found)[/bold red]\n")
    for alert in alerts:
        reasons_str = ", ".join(alert["reasons"])
        console.print(f"  [{alert['region'].upper()}] {alert['matchup']}")
        console.print(f"    Reasons: {reasons_str}")
        console.print(f"    Confidence: {alert['confidence']:.0%}")
        console.print()


@app.command()
def champion(
    bracket: str = typer.Option(..., help="Path to bracket JSON file"),
    sims: int = typer.Option(10000, help="Number of Monte Carlo simulations"),
    injuries_file: str = typer.Option(None, help="Path to injuries JSON"),
):
    """Show champion probabilities from Monte Carlo simulation."""
    from src.bracket import MonteCarloSimulator

    bracket_data, team_data, model = _load_everything(bracket, injuries_file)

    console.print(f"[bold]Running {sims:,} simulations...[/bold]")
    mc = MonteCarloSimulator(bracket_data, model, team_data)
    mc_results = mc.run(n_sims=sims)

    # Champion contenders (pass hard filters)
    contenders = model.get_champion_contenders(list(team_data.values()))
    console.print(f"\n[bold]CHAMPION CONTENDERS[/bold] ({len(contenders)} pass AdjO/AdjD filters)\n")
    contenders.sort(key=lambda x: x.get("barthag", 0), reverse=True)
    for t in contenders[:10]:
        console.print(f"  #{t['seed']} {t['team']} — Barthag: {t['barthag']:.4f}, "
                      f"AdjO: {t['adj_o_rank']}, AdjD: {t['adj_d_rank']}")

    # Monte Carlo champion probabilities
    console.print(f"\n[bold]CHAMPION PROBABILITIES[/bold] ({sims:,} simulations)\n")
    for team, prob in mc_results.champion_probs()[:15]:
        seed = team_data.get(team, {}).get("seed", "?")
        bar = "█" * int(prob * 100)
        console.print(f"  #{seed:<2} {team:<20} {bar} {prob:.1%}")

    # Final Four probabilities
    console.print(f"\n[bold]FINAL FOUR PROBABILITIES[/bold]\n")
    for team, prob in mc_results.final_four_probs()[:12]:
        seed = team_data.get(team, {}).get("seed", "?")
        console.print(f"  #{seed:<2} {team:<20} {prob:.1%}")

    console.print()


@app.command(name="ui-export")
def ui_export(
    bracket: str = typer.Option(..., help="Path to bracket JSON file"),
    sims: int = typer.Option(10000, help="Number of Monte Carlo simulations"),
    output: str = typer.Option("ui/public/data/bracket-data.json", help="Output JSON path"),
    injuries_file: str = typer.Option(None, help="Path to injuries JSON"),
):
    """Export simulation data as JSON for the React UI."""
    from src.bracket import MonteCarloSimulator
    from src.output import export_ui_json
    from src.upsets import detect_upsets

    bracket_data, team_data, model = _load_everything(bracket, injuries_file)

    console.print("[bold]Scanning for upset alerts...[/bold]")
    upset_alerts = detect_upsets(team_data, bracket_data)

    console.print(f"[bold]Running {sims:,} simulations...[/bold]")
    mc = MonteCarloSimulator(bracket_data, model, team_data)
    mc_results = mc.run(n_sims=sims)

    console.print("[bold]Building probability matrix + exporting UI JSON...[/bold]")
    export_ui_json(mc_results, mc, team_data, upset_alerts, bracket_data, output)
    console.print(f"[bold green]Done! Open the UI with: cd ui && npm run dev[/bold green]")


if __name__ == "__main__":
    app()
