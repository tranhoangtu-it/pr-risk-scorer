"""Tests for HotPathAnalyzer."""

import pytest

from pr_risk_scorer.analyzers.hot_path import HotPathAnalyzer
from pr_risk_scorer.models import FileChange, PRData


@pytest.fixture
def analyzer():
    """Create a HotPathAnalyzer instance."""
    return HotPathAnalyzer()


def test_empty_pr(analyzer):
    """Test that empty PR has low score."""
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Empty PR",
        author="test_user",
        files=[],
        commits_count=0,
    )

    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "hot_path"
    assert result.score == 0.0
    assert result.confidence == 0.6
    assert result.details["commits_count"] == 0
    assert result.details["files_count"] == 0


def test_small_pr(analyzer):
    """Test that small PR (1-3 files, few commits) has low score."""
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Small PR",
        author="test_user",
        files=[
            FileChange(filename="src/main.py", additions=10, deletions=5),
            FileChange(filename="src/utils.py", additions=8, deletions=2),
        ],
        commits_count=2,
    )

    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "hot_path"
    assert result.score < 30  # Low score for small PR
    assert result.details["commits_count"] == 2
    assert result.details["files_count"] == 2


def test_large_pr(analyzer):
    """Test that large PR (20+ files, many commits) has high score."""
    files = []
    for i in range(25):
        patch = "\n".join([f"+ line {j}" for j in range(50)])
        files.append(
            FileChange(
                filename=f"file{i}.py",
                additions=50,
                deletions=30,
                patch=patch,
            )
        )

    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Large PR",
        author="test_user",
        files=files,
        commits_count=15,
    )

    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "hot_path"
    assert result.score > 60  # High score for large PR with many commits
    assert result.details["commits_count"] == 15
    assert result.details["files_count"] == 25
    assert result.details["files_with_patch"] == 25


def test_score_bounds(analyzer):
    """Test that score is always between 0 and 100."""
    # Very large PR with extreme values
    files = []
    for i in range(50):
        patch = "\n".join([f"+ line {j}" for j in range(100)])
        files.append(
            FileChange(
                filename=f"file{i}.py",
                additions=100,
                deletions=80,
                patch=patch,
            )
        )

    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Massive PR",
        author="test_user",
        files=files,
        commits_count=50,
    )

    result = analyzer.analyze(pr_data)

    assert 0 <= result.score <= 100
    assert result.confidence == 0.6


def test_recommendations(analyzer):
    """Test that recommendations are generated for high-risk scenarios."""
    # PR with many commits
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="PR with many commits",
        author="test_user",
        files=[
            FileChange(filename="src/file1.py", additions=20, deletions=10),
            FileChange(filename="src/file2.py", additions=15, deletions=5),
        ],
        commits_count=12,  # High commit count
    )

    result = analyzer.analyze(pr_data)

    # Should have recommendation about squashing commits
    assert any("squashing and rebasing" in rec for rec in result.recommendations)


def test_patch_size_calculation(analyzer):
    """Test that patch size is correctly calculated."""
    patch1 = "\n".join([f"+ line {i}" for i in range(10)])
    patch2 = "\n".join([f"- line {i}" for i in range(20)])

    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Test PR",
        author="test_user",
        files=[
            FileChange(filename="file1.py", additions=10, deletions=0, patch=patch1),
            FileChange(filename="file2.py", additions=0, deletions=20, patch=patch2),
            FileChange(filename="file3.py", additions=5, deletions=5),  # No patch
        ],
        commits_count=3,
    )

    result = analyzer.analyze(pr_data)

    assert result.details["files_with_patch"] == 2
    assert result.details["patch_size_signal"] > 0


def test_no_patches(analyzer):
    """Test PR with no patches."""
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=1,
        title="Test PR",
        author="test_user",
        files=[
            FileChange(filename="file1.py", additions=10, deletions=5),
            FileChange(filename="file2.py", additions=8, deletions=2),
        ],
        commits_count=2,
    )

    result = analyzer.analyze(pr_data)

    assert result.details["files_with_patch"] == 0
    assert result.details["patch_size_signal"] == 0.0
