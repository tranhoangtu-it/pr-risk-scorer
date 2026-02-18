import pytest
from pr_risk_scorer.models import PRData, FileChange, ReviewData, AnalyzerResult, RiskScore, RiskLevel
from pr_risk_scorer.config import ScorerConfig


@pytest.fixture
def empty_pr():
    return PRData(owner="test", repo="repo", number=1, title="Empty PR", author="dev")


@pytest.fixture
def small_pr():
    return PRData(
        owner="test", repo="repo", number=2, title="Small fix",
        author="dev", commits_count=1, additions=10, deletions=5,
        files=[FileChange(filename="src/main.py", additions=10, deletions=5)],
        reviews=[ReviewData(reviewer="reviewer1", state="APPROVED")],
    )


@pytest.fixture
def large_pr():
    files = [FileChange(filename=f"src/module{i}/file{j}.py", additions=50, deletions=20) for i in range(5) for j in range(5)]
    return PRData(owner="test", repo="repo", number=3, title="Large refactor", author="dev", commits_count=15, additions=1250, deletions=500, files=files)


@pytest.fixture
def default_config():
    return ScorerConfig()


@pytest.fixture
def sample_risk_score():
    return RiskScore(
        overall_score=55.0, risk_level=RiskLevel.HIGH,
        analyzer_results=[AnalyzerResult(analyzer_name="blast_radius", score=70.0), AnalyzerResult(analyzer_name="review", score=40.0)],
        rollback_probability=0.44,
        recommendations=["Consider splitting", "Add more reviewers"],
        pr_url="https://github.com/test/repo/pull/1",
    )
