"""Tests for DependencyAnalyzer."""


from pr_risk_scorer.analyzers.dependency import DependencyAnalyzer
from pr_risk_scorer.models import FileChange, PRData


def test_dependency_file_detection():
    """Test detection of dependency files."""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=1,
        title="Update dependencies",
        author="developer",
        files=[
            FileChange(filename="requirements.txt", additions=5, deletions=2),
            FileChange(filename="package.json", additions=3, deletions=1),
            FileChange(filename="src/main.py", additions=10, deletions=0),
        ],
    )

    analyzer = DependencyAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "dependency"
    assert 0 <= result.score <= 100
    assert result.confidence == 0.8
    assert result.details["dep_file_count"] == 2
    assert result.details["dep_loc"] == 11  # 5+2+3+1
    assert len(result.recommendations) > 0
    assert any("Dependency changes" in rec for rec in result.recommendations)


def test_import_changes():
    """Test detection of import changes."""
    patch = """@@ -1,3 +1,5 @@
+import os
+from typing import Optional
 import sys
-from old_module import deprecated
+from new_module import updated
"""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=2,
        title="Refactor imports",
        author="developer",
        files=[
            FileChange(
                filename="src/module.py", additions=3, deletions=1, patch=patch
            ),
        ],
    )

    analyzer = DependencyAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.analyzer_name == "dependency"
    assert result.details["import_changes"] == 4  # 2 additions + 2 changes
    assert 0 <= result.score <= 100


def test_score_bounds():
    """Test that scores are always within bounds."""
    # Empty PR
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=3,
        title="Empty PR",
        author="developer",
        files=[],
    )

    analyzer = DependencyAnalyzer()
    result = analyzer.analyze(pr_data)

    assert 0 <= result.score <= 100
    assert result.score == 0  # No changes = no risk

    # Large PR with many dependency changes
    large_pr = PRData(
        owner="test",
        repo="test-repo",
        number=4,
        title="Major dependency update",
        author="developer",
        files=[
            FileChange(filename="requirements.txt", additions=50, deletions=30),
            FileChange(filename="package.json", additions=20, deletions=15),
            FileChange(filename="pyproject.toml", additions=10, deletions=5),
        ],
    )

    result = analyzer.analyze(large_pr)
    assert 0 <= result.score <= 100
    assert result.score > 50  # Should be high risk


def test_no_dependency_changes():
    """Test PR with no dependency changes."""
    pr_data = PRData(
        owner="test",
        repo="test-repo",
        number=5,
        title="Regular code change",
        author="developer",
        files=[
            FileChange(filename="src/main.py", additions=20, deletions=5),
            FileChange(filename="tests/test_main.py", additions=30, deletions=0),
        ],
    )

    analyzer = DependencyAnalyzer()
    result = analyzer.analyze(pr_data)

    assert result.score == 0  # No dependency files
    assert result.details["dep_file_count"] == 0
    assert result.details["dep_loc"] == 0
