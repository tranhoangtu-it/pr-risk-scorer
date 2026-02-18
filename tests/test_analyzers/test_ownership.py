"""Tests for OwnershipAnalyzer."""

import pytest

from pr_risk_scorer.analyzers.ownership import OwnershipAnalyzer
from pr_risk_scorer.models import FileChange, PRData


@pytest.fixture
def analyzer():
    """Create an OwnershipAnalyzer instance."""
    return OwnershipAnalyzer()


def test_empty_pr(analyzer):
    """Test that empty PR has low score."""
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Empty PR",
        author="test_user",
        files=[],
    )

    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "ownership"
    assert result.score == 0.0
    assert result.confidence == 0.5
    assert result.details["unique_top_dirs"] == 0
    assert result.details["max_depth"] == 0


def test_small_pr(analyzer):
    """Test that small PR (1-3 files in same domain) has low score."""
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Small PR",
        author="test_user",
        files=[
            FileChange(filename="src/main.py", additions=10, deletions=5),
            FileChange(filename="src/utils.py", additions=8, deletions=2),
            FileChange(filename="src/helpers/helper.py", additions=5, deletions=1),
        ],
    )

    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "ownership"
    assert result.score < 40  # Low score for single domain
    assert result.details["unique_top_dirs"] == 1  # Only "src"
    assert result.details["max_depth"] == 3  # src/helpers/helper.py


def test_large_pr(analyzer):
    """Test that PR spanning multiple domains has high score."""
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Cross-domain PR",
        author="test_user",
        files=[
            FileChange(filename="frontend/src/App.tsx", additions=50, deletions=20),
            FileChange(filename="backend/api/routes.py", additions=40, deletions=10),
            FileChange(filename="database/migrations/001.sql", additions=30, deletions=0),
            FileChange(filename="docs/README.md", additions=10, deletions=5),
        ],
    )

    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "ownership"
    assert result.score > 60  # High score for multiple domains
    assert result.details["unique_top_dirs"] == 4  # frontend, backend, database, docs
    assert len(result.recommendations) > 0
    assert "multiple domains" in result.recommendations[0]


def test_score_bounds(analyzer):
    """Test that score is always between 0 and 100."""
    # PR with many top-level directories and deep nesting
    files = []
    for i in range(10):
        # Deep nesting
        path = "/".join([f"level{j}" for j in range(10)]) + f"/file{i}.py"
        files.append(
            FileChange(
                filename=path,
                additions=10,
                deletions=5,
            )
        )

    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Deep nested PR",
        author="test_user",
        files=files,
    )

    result = analyzer.analyze(pr_data)

    assert 0 <= result.score <= 100
    assert result.confidence == 0.5


def test_recommendations(analyzer):
    """Test that recommendations are generated for high-risk scenarios."""
    # PR with multiple domains
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Multi-domain PR",
        author="test_user",
        files=[
            FileChange(filename="api/routes.py", additions=20, deletions=10),
            FileChange(filename="frontend/app.tsx", additions=30, deletions=15),
            FileChange(filename="database/schema.sql", additions=25, deletions=5),
            FileChange(filename="infra/terraform/main.tf", additions=15, deletions=8),
        ],
    )

    result = analyzer.analyze(pr_data)

    # Should have recommendation about domain experts
    assert any("domain experts" in rec for rec in result.recommendations)


def test_single_file_no_directory(analyzer):
    """Test PR with single file (no directory structure)."""
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Root file PR",
        author="test_user",
        files=[
            FileChange(filename="README.md", additions=10, deletions=5),
        ],
    )

    result = analyzer.analyze(pr_data)

    assert result.details["unique_top_dirs"] == 1  # "README.md" itself
    assert result.details["max_depth"] == 1  # Just the filename
    assert result.score < 30  # Low score for single file


def test_depth_calculation(analyzer):
    """Test that directory depth is correctly calculated."""
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Test depth",
        author="test_user",
        files=[
            FileChange(filename="a/b/c/d/e/file.py", additions=10, deletions=5),
            FileChange(filename="x/y/file2.py", additions=5, deletions=2),
            FileChange(filename="root.py", additions=3, deletions=1),
        ],
    )

    result = analyzer.analyze(pr_data)

    assert result.details["max_depth"] == 6  # a/b/c/d/e/file.py
    assert result.details["unique_top_dirs"] == 3  # a, x, root.py
