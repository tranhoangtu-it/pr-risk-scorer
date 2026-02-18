"""Configuration system with YAML loading and defaults."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class AnalyzerConfig(BaseModel):
    enabled: bool = True
    weight: float = Field(ge=0.0, le=1.0)


class ScorerConfig(BaseModel):
    github_token: str | None = None
    analyzers: dict[str, AnalyzerConfig] = Field(default_factory=lambda: {
        "blast_radius": AnalyzerConfig(weight=0.25),
        "hot_path": AnalyzerConfig(weight=0.20),
        "complexity": AnalyzerConfig(weight=0.15),
        "ownership": AnalyzerConfig(weight=0.15),
        "dependency": AnalyzerConfig(weight=0.15),
        "review": AnalyzerConfig(weight=0.10),
    })
    output_format: str = "terminal"
    risk_thresholds: dict[str, int] = Field(default_factory=lambda: {
        "low": 25, "medium": 50, "high": 75,
    })

    @classmethod
    def load(cls, path: Path | None = None) -> "ScorerConfig":
        """Load config from YAML file, falling back to defaults."""
        if path is None:
            path = Path(".pr-risk-scorer.yaml")
        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()
