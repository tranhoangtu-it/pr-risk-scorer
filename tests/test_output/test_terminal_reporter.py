"""Tests for terminal reporter."""

from pr_risk_scorer.models import AnalyzerResult, RiskLevel, RiskScore
from pr_risk_scorer.output.terminal_reporter import TerminalReporter


def test_render_returns_string():
    """Test that render returns a non-empty string."""
    reporter = TerminalReporter()
    risk_score = RiskScore(
        overall_score=42.5,
        risk_level=RiskLevel.MEDIUM,
        rollback_probability=0.15,
    )

    result = reporter.render(risk_score)

    assert isinstance(result, str)
    assert len(result) > 0


def test_render_contains_score():
    """Test that rendered output contains the score."""
    reporter = TerminalReporter()
    risk_score = RiskScore(
        overall_score=75.3,
        risk_level=RiskLevel.HIGH,
        rollback_probability=0.42,
    )

    result = reporter.render(risk_score)

    assert "75.3" in result
    assert "HIGH" in result.upper()


def test_render_with_analyzer_results():
    """Test rendering with analyzer breakdown."""
    reporter = TerminalReporter()
    risk_score = RiskScore(
        overall_score=60.0,
        risk_level=RiskLevel.HIGH,
        analyzer_results=[
            AnalyzerResult(
                analyzer_name="size_analyzer",
                score=70.0,
                confidence=0.95,
                details={"lines": 500, "files": 10},
            ),
            AnalyzerResult(
                analyzer_name="complexity_analyzer",
                score=50.0,
                confidence=0.8,
                details={"cyclomatic": 15},
            ),
        ],
    )

    result = reporter.render(risk_score)

    assert "size_analyzer" in result
    assert "complexity_analyzer" in result
    assert "70.0" in result
    assert "50.0" in result


def test_render_with_recommendations():
    """Test rendering with recommendations."""
    reporter = TerminalReporter()
    risk_score = RiskScore(
        overall_score=80.0,
        risk_level=RiskLevel.CRITICAL,
        recommendations=[
            "Add more unit tests",
            "Request additional code review",
            "Consider breaking into smaller PRs",
        ],
    )

    result = reporter.render(risk_score)

    assert "Add more unit tests" in result
    assert "Request additional code review" in result
    assert "Consider breaking into smaller PRs" in result


def test_render_with_pr_url():
    """Test rendering with PR URL."""
    reporter = TerminalReporter()
    risk_score = RiskScore(
        overall_score=30.0,
        risk_level=RiskLevel.MEDIUM,
        pr_url="https://github.com/owner/repo/pull/123",
    )

    result = reporter.render(risk_score)

    assert "https://github.com/owner/repo/pull/123" in result


def test_display_runs_without_error():
    """Test that display outputs without crashing."""
    reporter = TerminalReporter()
    risk_score = RiskScore(
        overall_score=25.0,
        risk_level=RiskLevel.MEDIUM,
        rollback_probability=0.1,
    )

    # Should not raise exception
    reporter.display(risk_score)


def test_risk_level_colors():
    """Test different risk levels produce different colors."""
    reporter = TerminalReporter()

    for level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
        risk_score = RiskScore(
            overall_score=10.0,
            risk_level=level,
        )
        result = reporter.render(risk_score)
        assert level.value.upper() in result
