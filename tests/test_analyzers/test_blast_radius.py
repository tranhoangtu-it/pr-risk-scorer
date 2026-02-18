"""Tests for BlastRadiusAnalyzer."""

import pytest

from pr_risk_scorer.analyzers.blast_radius import BlastRadiusAnalyzer
from pr_risk_scorer.models import FileChange, PRData


@pytest.fixture
def analyzer():
    """Create a BlastRadiusAnalyzer instance."""
    return BlastRadiusAnalyzer()


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

    assert result.analyzer_name == "blast_radius"
    assert result.score == 0.0
    assert result.confidence == 1.0
    assert result.details["files_changed"] == 0
    assert result.details["total_additions"] == 0
    assert result.details["total_deletions"] == 0
    assert result.details["modules_affected"] == 0


def test_small_pr(analyzer):
    """Test that small PR (1-3 files) has low score."""
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Small PR",
        author="test_user",
        files=[
            FileChange(filename="src/main.py", additions=10, deletions=5),
            FileChange(filename="src/utils.py", additions=8, deletions=2),
            FileChange(filename="tests/test_main.py", additions=15, deletions=0),
        ],
    )

    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "blast_radius"
    assert result.score < 30  # Low score for small PR
    assert result.details["files_changed"] == 3
    assert result.details["total_additions"] == 33
    assert result.details["total_deletions"] == 7
    assert result.details["modules_affected"] == 2  # src and tests


def test_large_pr(analyzer):
    """Test that large PR (20+ files) has high score."""
    files = []
    for i in range(25):
        files.append(
            FileChange(
                filename=f"module{i % 5}/file{i}.py",
                additions=50,
                deletions=30,
            )
        )

    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Large PR",
        author="test_user",
        files=files,
    )

    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "blast_radius"
    assert result.score > 70  # High score for large PR
    assert result.details["files_changed"] == 25
    assert result.details["modules_affected"] == 5
    assert len(result.recommendations) > 0
    assert "splitting this PR" in result.recommendations[0]


def test_score_bounds(analyzer):
    """Test that score is always between 0 and 100."""
    # Very large PR to test upper bound
    files = []
    for i in range(100):
        files.append(
            FileChange(
                filename=f"module{i}/subdir/file{i}.py",
                additions=200,
                deletions=150,
            )
        )

    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Massive PR",
        author="test_user",
        files=files,
    )

    result = analyzer.analyze(pr_data)

    assert 0 <= result.score <= 100
    assert result.confidence == 1.0


def test_recommendations(analyzer):
    """Test that recommendations are generated for high-risk scenarios."""
    # PR with one very large file
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="PR with large file",
        author="test_user",
        files=[
            FileChange(filename="src/huge_file.py", additions=250, deletions=100),
            FileChange(filename="src/small.py", additions=5, deletions=2),
        ],
    )

    result = analyzer.analyze(pr_data)

    # Should have recommendation about large file
    assert any("huge_file.py" in rec for rec in result.recommendations)
    assert any("350+ LOC changes" in rec for rec in result.recommendations)


def test_largest_file_tracking(analyzer):
    """Test that largest file is correctly tracked."""
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Test PR",
        author="test_user",
        files=[
            FileChange(filename="file1.py", additions=10, deletions=5),
            FileChange(filename="file2.py", additions=50, deletions=30),
            FileChange(filename="file3.py", additions=20, deletions=10),
        ],
    )

    result = analyzer.analyze(pr_data)

    assert result.details["largest_file"] == "file2.py"
    assert result.details["largest_file_loc"] == 80
