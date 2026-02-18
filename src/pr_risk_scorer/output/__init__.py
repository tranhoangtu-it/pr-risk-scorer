"""Output formatters for PR Risk Scorer."""

from abc import ABC, abstractmethod

from pr_risk_scorer.models import RiskScore


class BaseReporter(ABC):
    """Base class for all output formatters."""

    @abstractmethod
    def render(self, risk_score: RiskScore) -> str:
        """Return formatted string representation."""
        ...

    @abstractmethod
    def display(self, risk_score: RiskScore) -> None:
        """Output to stdout."""
        ...


def get_reporter(format_name: str) -> BaseReporter:
    """Factory function to get reporter by format name.

    Args:
        format_name: One of "terminal", "json", "markdown"

    Returns:
        Instantiated reporter

    Raises:
        ValueError: If format_name is unknown
    """
    from pr_risk_scorer.output.json_reporter import JsonReporter
    from pr_risk_scorer.output.markdown_reporter import MarkdownReporter
    from pr_risk_scorer.output.terminal_reporter import TerminalReporter

    reporters = {
        "terminal": TerminalReporter,
        "json": JsonReporter,
        "markdown": MarkdownReporter,
    }
    cls = reporters.get(format_name)
    if cls is None:
        raise ValueError(
            f"Unknown format: {format_name}. Options: {list(reporters.keys())}"
        )
    return cls()


__all__ = ["BaseReporter", "get_reporter"]
