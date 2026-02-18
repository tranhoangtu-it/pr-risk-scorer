"""JSON output formatter."""

from pr_risk_scorer.models import RiskScore
from pr_risk_scorer.output import BaseReporter


class JsonReporter(BaseReporter):
    """JSON output formatter using Pydantic serialization."""

    def render(self, risk_score: RiskScore) -> str:
        """Return formatted JSON string."""
        return risk_score.model_dump_json(indent=2)

    def display(self, risk_score: RiskScore) -> None:
        """Output JSON to stdout."""
        print(self.render(risk_score))
