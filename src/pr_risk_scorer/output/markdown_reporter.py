"""Markdown output formatter for GitHub compatibility."""

from pr_risk_scorer.models import RiskScore
from pr_risk_scorer.output import BaseReporter


class MarkdownReporter(BaseReporter):
    """GitHub-flavored Markdown formatter."""

    def render(self, risk_score: RiskScore) -> str:
        """Return formatted markdown string."""
        lines = []

        # Header
        risk_emoji = {
            "low": "✅",
            "medium": "⚠️",
            "high": "🔶",
            "critical": "🚨",
        }
        emoji = risk_emoji.get(risk_score.risk_level.value, "")
        lines.append(f"# {emoji} PR Risk Assessment: {risk_score.risk_level.value.upper()}")
        lines.append("")
        lines.append(f"**Overall Score:** {risk_score.overall_score:.1f}/100")
        lines.append(f"**Rollback Probability:** {risk_score.rollback_probability:.1%}")

        if risk_score.pr_url:
            lines.append(f"**PR URL:** {risk_score.pr_url}")

        lines.append("")

        # Analyzer results table
        if risk_score.analyzer_results:
            lines.append("## Analyzer Breakdown")
            lines.append("")
            lines.append("| Analyzer | Score | Confidence | Details |")
            lines.append("|----------|-------|------------|---------|")

            for result in risk_score.analyzer_results:
                details_str = ", ".join(
                    f"{k}={v}" for k, v in result.details.items()
                ) or "—"
                lines.append(
                    f"| {result.analyzer_name} | {result.score:.1f} | "
                    f"{result.confidence:.0%} | {details_str} |"
                )
            lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        if risk_score.recommendations:
            for rec in risk_score.recommendations:
                lines.append(f"- {rec}")
        else:
            lines.append("_No recommendations at this time._")
        lines.append("")

        return "\n".join(lines)

    def display(self, risk_score: RiskScore) -> None:
        """Output markdown to stdout."""
        print(self.render(risk_score))
