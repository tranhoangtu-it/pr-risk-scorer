"""Terminal output formatter using Rich."""

from io import StringIO

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pr_risk_scorer.models import RiskLevel, RiskScore
from pr_risk_scorer.output import BaseReporter


class TerminalReporter(BaseReporter):
    """Rich terminal output with colors and tables."""

    def _get_risk_color(self, level: RiskLevel) -> str:
        """Map risk level to Rich color."""
        colors = {
            RiskLevel.LOW: "green",
            RiskLevel.MEDIUM: "yellow",
            RiskLevel.HIGH: "orange1",
            RiskLevel.CRITICAL: "red",
        }
        return colors.get(level, "white")

    def render(self, risk_score: RiskScore) -> str:
        """Return formatted string representation."""
        console = Console(file=StringIO(), force_terminal=True, width=100)
        self._render_to_console(console, risk_score)
        return console.file.getvalue()  # type: ignore

    def display(self, risk_score: RiskScore) -> None:
        """Output to stdout."""
        console = Console()
        self._render_to_console(console, risk_score)

    def _render_to_console(self, console: Console, risk_score: RiskScore) -> None:
        """Render to provided console instance."""
        color = self._get_risk_color(risk_score.risk_level)

        # Header panel
        header = Panel(
            f"[bold {color}]{risk_score.risk_level.value.upper()}[/] - "
            f"Score: {risk_score.overall_score:.1f}/100\n"
            f"Rollback Probability: {risk_score.rollback_probability:.1%}",
            title="[bold]PR Risk Assessment[/]",
            border_style=color,
        )
        console.print(header)

        # Analyzer results table
        if risk_score.analyzer_results:
            table = Table(title="Analyzer Breakdown", show_header=True, header_style="bold")
            table.add_column("Analyzer", style="cyan")
            table.add_column("Score", justify="right")
            table.add_column("Confidence", justify="right")
            table.add_column("Details", style="dim")

            for result in risk_score.analyzer_results:
                details_str = ", ".join(
                    f"{k}={v}" for k, v in result.details.items()
                )
                table.add_row(
                    result.analyzer_name,
                    f"{result.score:.1f}",
                    f"{result.confidence:.0%}",
                    details_str or "—",
                )
            console.print(table)

        # Recommendations
        if risk_score.recommendations:
            console.print("\n[bold]Recommendations:[/]")
            for rec in risk_score.recommendations:
                console.print(f"  • {rec}")

        # PR URL
        if risk_score.pr_url:
            console.print(f"\n[dim]PR: {risk_score.pr_url}[/]")
