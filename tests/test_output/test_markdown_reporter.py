"""Tests for Markdown reporter."""

from pr_risk_scorer.models import AnalyzerResult, RiskLevel, RiskScore
from pr_risk_scorer.output.markdown_reporter import MarkdownReporter


def test_render_has_header():
    """Test that markdown has proper header."""
    reporter = MarkdownReporter()
    risk_score = RiskScore(
        overall_score=42.5,
        risk_level=RiskLevel.MEDIUM,
        rollback_probability=0.15,
    )

    result = reporter.render(risk_score)

    assert "# " in result
    assert "MEDIUM" in result
    assert "42.5" in result


def test_render_has_table():
    """Test that markdown includes analyzer table."""
    reporter = MarkdownReporter()
    risk_score = RiskScore(
        overall_score=60.0,
        risk_level=RiskLevel.HIGH,
        analyzer_results=[
            AnalyzerResult(
                analyzer_name="size_analyzer",
                score=70.0,
                confidence=0.95,
                details={"lines": 500},
            ),
        ],
    )

    result = reporter.render(risk_score)

    # Check for table structure
    assert "| Analyzer |" in result
    assert "|----------|" in result
    assert "size_analyzer" in result
    assert "70.0" in result


def test_render_has_recommendations_section():
    """Test that recommendations section exists."""
    reporter = MarkdownReporter()
    risk_score = RiskScore(
        overall_score=80.0,
        risk_level=RiskLevel.CRITICAL,
        recommendations=[
            "Add more unit tests",
            "Request additional code review",
        ],
    )

    result = reporter.render(risk_score)

    assert "## Recommendations" in result
    assert "- Add more unit tests" in result
    assert "- Request additional code review" in result


def test_render_empty_recommendations():
    """Test handling of empty recommendations."""
    reporter = MarkdownReporter()
    risk_score = RiskScore(
        overall_score=20.0,
        risk_level=RiskLevel.LOW,
        recommendations=[],
    )

    result = reporter.render(risk_score)

    assert "## Recommendations" in result
    assert "No recommendations" in result


def test_render_with_pr_url():
    """Test rendering with PR URL."""
    reporter = MarkdownReporter()
    risk_score = RiskScore(
        overall_score=30.0,
        risk_level=RiskLevel.MEDIUM,
        pr_url="https://github.com/owner/repo/pull/123",
    )

    result = reporter.render(risk_score)

    assert "https://github.com/owner/repo/pull/123" in result
    assert "PR URL" in result


def test_render_risk_level_emojis():
    """Test that different risk levels get appropriate emojis."""
    reporter = MarkdownReporter()

    test_cases = [
        (RiskLevel.LOW, "✅"),
        (RiskLevel.MEDIUM, "⚠️"),
        (RiskLevel.HIGH, "🔶"),
        (RiskLevel.CRITICAL, "🚨"),
    ]

    for level, emoji in test_cases:
        risk_score = RiskScore(
            overall_score=10.0,
            risk_level=level,
        )
        result = reporter.render(risk_score)
        assert emoji in result
        assert level.value.upper() in result


def test_render_analyzer_details():
    """Test rendering of analyzer details in table."""
    reporter = MarkdownReporter()
    risk_score = RiskScore(
        overall_score=50.0,
        risk_level=RiskLevel.MEDIUM,
        analyzer_results=[
            AnalyzerResult(
                analyzer_name="complexity_analyzer",
                score=65.0,
                confidence=0.85,
                details={"cyclomatic": 20, "cognitive": 15},
            ),
        ],
    )

    result = reporter.render(risk_score)

    assert "complexity_analyzer" in result
    assert "65.0" in result
    assert "85%" in result
    assert "cyclomatic=20" in result
    assert "cognitive=15" in result


def test_render_empty_details():
    """Test rendering analyzer with no details."""
    reporter = MarkdownReporter()
    risk_score = RiskScore(
        overall_score=40.0,
        risk_level=RiskLevel.MEDIUM,
        analyzer_results=[
            AnalyzerResult(
                analyzer_name="simple_analyzer",
                score=40.0,
                confidence=1.0,
                details={},
            ),
        ],
    )

    result = reporter.render(risk_score)

    assert "simple_analyzer" in result
    # Empty details should show em dash or similar
    assert "—" in result or "-" in result


def test_display_outputs_markdown():
    """Test that display outputs to stdout."""
    reporter = MarkdownReporter()
    risk_score = RiskScore(
        overall_score=25.0,
        risk_level=RiskLevel.MEDIUM,
    )

    # Should not raise exception
    reporter.display(risk_score)


def test_markdown_formatting():
    """Test overall markdown structure and formatting."""
    reporter = MarkdownReporter()
    risk_score = RiskScore(
        overall_score=70.0,
        risk_level=RiskLevel.HIGH,
        rollback_probability=0.35,
        analyzer_results=[
            AnalyzerResult(analyzer_name="test", score=70.0, confidence=0.9),
        ],
        recommendations=["Test rec"],
        pr_url="https://github.com/test/repo/pull/1",
    )

    result = reporter.render(risk_score)

    # Check for proper markdown structure
    assert result.startswith("# ")
    assert "## Analyzer Breakdown" in result
    assert "## Recommendations" in result
    assert "**Overall Score:**" in result
    assert "**Rollback Probability:**" in result
