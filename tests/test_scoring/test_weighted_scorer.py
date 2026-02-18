"""Tests for weighted scoring engine."""

import pytest

from pr_risk_scorer.config import AnalyzerConfig, ScorerConfig
from pr_risk_scorer.models import AnalyzerResult, RiskLevel
from pr_risk_scorer.scoring import WeightedScorer


@pytest.fixture
def config():
    return ScorerConfig(analyzers={
        "blast_radius": AnalyzerConfig(weight=0.30),
        "hot_path": AnalyzerConfig(weight=0.25),
        "complexity": AnalyzerConfig(weight=0.20),
    })


@pytest.fixture
def scorer(config):
    return WeightedScorer(config)


def _result(name="blast_radius", score=50.0, confidence=1.0, recs=None):
    return AnalyzerResult(
        analyzer_name=name, score=score, confidence=confidence,
        recommendations=recs or [],
    )


def test_empty_results(scorer):
    result = scorer.score([])
    assert result.overall_score == 0.0
    assert result.risk_level == RiskLevel.LOW


def test_all_low_scores(scorer):
    results = [_result("blast_radius", 10), _result("hot_path", 10), _result("complexity", 10)]
    result = scorer.score(results)
    assert result.overall_score == 10.0
    assert result.risk_level == RiskLevel.LOW


def test_all_high_scores(scorer):
    results = [_result("blast_radius", 90), _result("hot_path", 90), _result("complexity", 90)]
    result = scorer.score(results)
    # 3 analyzers > 70: amplifier = 1 + 0.15*3 = 1.45; 90*1.45 = capped 100
    assert result.overall_score >= 90.0
    assert result.risk_level == RiskLevel.CRITICAL


def test_mixed_scores(scorer):
    results = [_result("blast_radius", 30), _result("hot_path", 60), _result("complexity", 20)]
    result = scorer.score(results)
    # weighted avg: (30*0.30 + 60*0.25 + 20*0.20) / 0.75 = 28/0.75 = 37.3
    assert 35.0 < result.overall_score < 40.0
    assert result.risk_level == RiskLevel.MEDIUM


def test_confidence_weighting(scorer):
    results = [_result("blast_radius", 80, confidence=0.5), _result("hot_path", 80)]
    result = scorer.score(results)
    # (80*0.5*0.30 + 80*1.0*0.25) / 0.55 = (12+20)/0.55 = 58.18
    assert 55.0 < result.overall_score < 65.0


def test_missing_analyzer(scorer):
    results = [_result("blast_radius", 50), _result("unknown_thing", 100)]
    result = scorer.score(results)
    assert result.overall_score == 50.0


def test_risk_level_thresholds():
    scorer = WeightedScorer()
    for score, level in [(20, RiskLevel.LOW), (40, RiskLevel.MEDIUM), (60, RiskLevel.HIGH), (90, RiskLevel.CRITICAL)]:
        result = scorer.score([_result("blast_radius", score)])
        assert result.risk_level == level


def test_rollback_probability(scorer):
    low = scorer.score([_result("blast_radius", 10)])
    assert low.rollback_probability < 0.1
    high = scorer.score([_result("blast_radius", 90), _result("hot_path", 90), _result("complexity", 90)])
    assert high.rollback_probability <= 0.8


def test_recommendations_merged(scorer):
    results = [
        _result("blast_radius", 30, recs=["Rec 1", "Rec 2"]),
        _result("hot_path", 40, recs=["Rec 3"]),
    ]
    result = scorer.score(results)
    assert set(result.recommendations) == {"Rec 1", "Rec 2", "Rec 3"}


def test_hybrid_amplification(scorer):
    results = [_result("blast_radius", 80), _result("hot_path", 80), _result("complexity", 30)]
    result = scorer.score(results)
    # 2 analyzers > 70: amplifier = 1.30; base ~62.67 * 1.30 = ~81.5
    assert result.overall_score > 75.0


def test_no_amplification_single_high(scorer):
    results = [_result("blast_radius", 80), _result("hot_path", 30), _result("complexity", 20)]
    result = scorer.score(results)
    # Only 1 > 70, no amplification; base ~43.3
    assert 40.0 < result.overall_score < 50.0


def test_no_matched_analyzers():
    """Test scoring when results don't match any enabled analyzer."""
    cfg = ScorerConfig(analyzers={
        "blast_radius": AnalyzerConfig(weight=0.5),
    })
    scorer = WeightedScorer(cfg)
    results = [_result("nonexistent_analyzer", 80)]
    result = scorer.score(results)
    assert result.overall_score == 0.0
    assert result.risk_level == RiskLevel.LOW
