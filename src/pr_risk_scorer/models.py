"""Shared data models for PR Risk Scorer."""

from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FileChange(BaseModel):
    """A single file changed in a PR."""

    filename: str
    additions: int = 0
    deletions: int = 0
    status: str = "modified"
    patch: str | None = None


class ReviewData(BaseModel):
    """A single review on a PR."""

    reviewer: str
    state: str  # APPROVED, CHANGES_REQUESTED, COMMENTED
    submitted_at: str | None = None
    body: str | None = None


class PRData(BaseModel):
    """All data about a PR needed for analysis."""

    owner: str
    repo: str
    number: int
    title: str
    author: str
    base_branch: str = "main"
    head_branch: str = ""
    files: list[FileChange] = Field(default_factory=list)
    reviews: list[ReviewData] = Field(default_factory=list)
    commits_count: int = 0
    additions: int = 0
    deletions: int = 0
    created_at: str | None = None
    merged_at: str | None = None


class AnalyzerResult(BaseModel):
    """Output from a single analyzer."""

    analyzer_name: str
    score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    details: dict = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


class RiskScore(BaseModel):
    """Aggregated risk assessment for a PR."""

    overall_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel
    analyzer_results: list[AnalyzerResult] = Field(default_factory=list)
    rollback_probability: float = Field(ge=0.0, le=1.0, default=0.0)
    recommendations: list[str] = Field(default_factory=list)
    pr_url: str = ""

    @staticmethod
    def level_from_score(score: float) -> RiskLevel:
        if score < 25:
            return RiskLevel.LOW
        if score < 50:
            return RiskLevel.MEDIUM
        if score < 75:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL
