"""Abstract base class for all risk analyzers."""

from abc import ABC, abstractmethod

from pr_risk_scorer.models import AnalyzerResult, PRData


class BaseAnalyzer(ABC):
    """Abstract base for all risk analyzers."""

    name: str = "base"

    @abstractmethod
    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        """Analyze PR data and return risk assessment."""
        ...
