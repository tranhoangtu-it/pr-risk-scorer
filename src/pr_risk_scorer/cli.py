from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from pr_risk_scorer.config import ScorerConfig
from pr_risk_scorer.github_client import GitHubClient, GitHubClientError
from pr_risk_scorer.analyzers import ALL_ANALYZERS
from pr_risk_scorer.scoring import WeightedScorer
from pr_risk_scorer.output import get_reporter

app = typer.Typer(name="pr-risk-scorer", help="Analyze GitHub PRs and predict failure likelihood post-merge.")
console = Console()


@app.command()
def analyze(
    repo: str = typer.Argument(..., help="Repository in 'owner/repo' format"),
    pr: int = typer.Option(..., "--pr", help="PR number to analyze"),
    output: str = typer.Option("terminal", "--output", "-o", help="Output format: terminal, json, markdown"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """Analyze a GitHub PR for risk assessment."""
    try:
        scorer_config = ScorerConfig.load(config)
        parts = repo.split("/")
        if len(parts) != 2:
            console.print("[red]Error: repo must be in 'owner/repo' format[/red]")
            raise typer.Exit(code=1)
        owner, repo_name = parts
        client = GitHubClient(config=scorer_config)
        pr_data = client.fetch_pr_data(owner, repo_name, pr)

        results = []
        for analyzer_cls in ALL_ANALYZERS:
            analyzer = analyzer_cls()
            ac = scorer_config.analyzers.get(analyzer.name)
            if ac and ac.enabled:
                results.append(analyzer.analyze(pr_data))

        risk_score = WeightedScorer(scorer_config).score(results)
        risk_score.pr_url = f"https://github.com/{repo}/pull/{pr}"
        get_reporter(output).display(risk_score)
    except GitHubClientError as e:
        console.print(f"[red]GitHub Error: {e}[/red]")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def report(
    repo: str = typer.Argument(..., help="Repository in 'owner/repo' format"),
    since: str = typer.Option(..., "--since", help="Start date (YYYY-MM-DD)"),
    output: str = typer.Option("terminal", "--output", "-o"),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max PRs to analyze"),
):
    """Generate risk report for recent merged PRs."""
    try:
        scorer_config = ScorerConfig.load(config)
        parts = repo.split("/")
        if len(parts) != 2:
            console.print("[red]Error: repo must be in 'owner/repo' format[/red]")
            raise typer.Exit(code=1)
        owner, repo_name = parts
        client = GitHubClient(config=scorer_config)
        # Fetch merged PRs via PyGithub
        from datetime import datetime
        try:
            repository = client._github.get_repo(f"{owner}/{repo_name}")
            pulls = repository.get_pulls(state="closed", sort="updated", direction="desc")
            since_dt = datetime.fromisoformat(since)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(code=1)

        analyzed = 0
        reporter = get_reporter(output)
        for pull in pulls:
            if analyzed >= limit:
                break
            if not pull.merged_at or pull.merged_at < since_dt:
                continue
            pr_data = client.fetch_pr_data(owner, repo_name, pull.number)
            results = []
            for analyzer_cls in ALL_ANALYZERS:
                analyzer = analyzer_cls()
                ac = scorer_config.analyzers.get(analyzer.name)
                if ac and ac.enabled:
                    results.append(analyzer.analyze(pr_data))
            risk_score = WeightedScorer(scorer_config).score(results)
            risk_score.pr_url = f"https://github.com/{repo}/pull/{pull.number}"
            console.print(f"\n[bold]PR #{pull.number}: {pull.title}[/bold]")
            reporter.display(risk_score)
            analyzed += 1
        if analyzed == 0:
            console.print("[yellow]No merged PRs found since {since}[/yellow]")
    except GitHubClientError as e:
        console.print(f"[red]GitHub Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("config")
def config_init():
    """Initialize default .pr-risk-scorer.yaml config file."""
    target = Path(".pr-risk-scorer.yaml")
    if target.exists():
        console.print("[yellow]Config already exists: .pr-risk-scorer.yaml[/yellow]")
        raise typer.Exit(code=0)
    default_config = ScorerConfig()
    import yaml
    data = default_config.model_dump()
    data.pop("github_token", None)
    with open(target, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    console.print("[green]Created .pr-risk-scorer.yaml[/green]")


def main():
    """Entry point for the CLI."""
    app()
