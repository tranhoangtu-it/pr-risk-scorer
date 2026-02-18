"""Tests for JSON reporter."""

import json

from pr_risk_scorer.models import AnalyzerResult, RiskLevel, RiskScore
from pr_risk_scorer.output.json_reporter import JsonReporter


def test_render_returns_valid_json():
    """Test that render returns valid JSON string."""
    reporter = JsonReporter()
    risk_score = RiskScore(
        overall_score=42.5,
        risk_level=RiskLevel.MEDIUM,
        rollback_probability=0.15,
    )

    result = reporter.render(risk_score)

    # Should be valid JSON
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


def test_render_contains_required_fields():
    """Test that JSON contains all required fields."""
    reporter = JsonReporter()
    risk_score = RiskScore(
        overall_score=75.3,
        risk_level=RiskLevel.HIGH,
        rollback_probability=0.42,
        pr_url="https://github.com/test/repo/pull/1",
    )

    result = reporter.render(risk_score)
    parsed = json.loads(result)

    assert parsed["overall_score"] == 75.3
    assert parsed["risk_level"] == "high"
    assert parsed["rollback_probability"] == 0.42
    assert parsed["pr_url"] == "https://github.com/test/repo/pull/1"


def test_render_with_analyzer_results():
    """Test JSON rendering with analyzer results."""
    reporter = JsonReporter()
    risk_score = RiskScore(
        overall_score=60.0,
        risk_level=RiskLevel.HIGH,
        analyzer_results=[
            AnalyzerResult(
                analyzer_name="size_analyzer",
                score=70.0,
                confidence=0.95,
                details={"lines": 500, "files": 10},
                recommendations=["Consider splitting"],
            ),
        ],
    )

    result = reporter.render(risk_score)
    parsed = json.loads(result)

    assert len(parsed["analyzer_results"]) == 1
    assert parsed["analyzer_results"][0]["analyzer_name"] == "size_analyzer"
    assert parsed["analyzer_results"][0]["score"] == 70.0
    assert parsed["analyzer_results"][0]["confidence"] == 0.95
    assert parsed["analyzer_results"][0]["details"]["lines"] == 500
    assert "Consider splitting" in parsed["analyzer_results"][0]["recommendations"]


def test_render_with_recommendations():
    """Test JSON rendering with recommendations."""
    reporter = JsonReporter()
    risk_score = RiskScore(
        overall_score=80.0,
        risk_level=RiskLevel.CRITICAL,
        recommendations=[
            "Add more unit tests",
            "Request additional code review",
        ],
    )

    result = reporter.render(risk_score)
    parsed = json.loads(result)

    assert len(parsed["recommendations"]) == 2
    assert "Add more unit tests" in parsed["recommendations"]
    assert "Request additional code review" in parsed["recommendations"]


def test_json_round_trip():
    """Test that JSON can be round-tripped back to RiskScore."""
    reporter = JsonReporter()
    original = RiskScore(
        overall_score=55.5,
        risk_level=RiskLevel.MEDIUM,
        rollback_probability=0.25,
        analyzer_results=[
            AnalyzerResult(
                analyzer_name="test_analyzer",
                score=60.0,
                confidence=0.9,
            ),
        ],
        recommendations=["Test recommendation"],
        pr_url="https://github.com/test/repo/pull/42",
    )

    json_str = reporter.render(original)
    parsed = json.loads(json_str)
    reconstructed = RiskScore.model_validate(parsed)

    assert reconstructed.overall_score == original.overall_score
    assert reconstructed.risk_level == original.risk_level
    assert reconstructed.rollback_probability == original.rollback_probability
    assert len(reconstructed.analyzer_results) == 1
    assert reconstructed.analyzer_results[0].analyzer_name == "test_analyzer"


def test_display_outputs_json():
    """Test that display outputs valid JSON to stdout."""
    reporter = JsonReporter()
    risk_score = RiskScore(
        overall_score=30.0,
        risk_level=RiskLevel.MEDIUM,
    )

    # Should not raise exception
    reporter.display(risk_score)


def test_json_formatting():
    """Test that JSON is indented for readability."""
    reporter = JsonReporter()
    risk_score = RiskScore(
        overall_score=50.0,
        risk_level=RiskLevel.MEDIUM,
    )

    result = reporter.render(risk_score)

    # Indented JSON should have newlines
    assert "\n" in result
    # Should be properly formatted
    assert "  " in result  # Check for indentation
