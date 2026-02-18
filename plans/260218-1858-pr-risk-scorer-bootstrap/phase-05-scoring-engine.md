# Phase 05: Scoring Engine

## Context Links
- [Plan Overview](./plan.md)
- [Phase 01: Foundation](./phase-01-project-setup-and-foundation.md) (dependency)
- [Research: Risk Algorithms - Section 2.1](./research/researcher-260218-1858-pr-risk-algorithms.md)

## Parallelization Info
- **Execution**: PARALLEL with Phases 02, 03, 04, 06
- **Blocked by**: Phase 01
- **Blocks**: Phase 07

## Overview
- **Priority**: P1
- **Status**: pending
- **Effort**: 0.5h
- **Description**: Weighted linear scoring engine. Takes list of `AnalyzerResult`s, applies configurable weights, produces `RiskScore` with overall score, risk level, rollback probability, and recommendations.

## Key Insights
<!-- Updated: Validation Session 1 - Hybrid scoring model -->
- **Hybrid scoring model**: Linear weighted baseline + amplification when 2+ analyzers score > 70
- Weights from config, default: blast_radius=0.25, hot_path=0.20, complexity=0.15, ownership=0.15, dependency=0.15, review=0.10
- Confidence-weighted: `effective_score = score * confidence`
- **Amplification**: `final = base_linear * (1 + 0.15 * count_high_analyzers)`, capped at 100
- Rollback probability: simple mapping from overall score (MVP)
- Thresholds: <25 Low, 25-50 Medium, 50-75 High, >75 Critical

## Requirements

### Functional
- Accept list of `AnalyzerResult` and `ScorerConfig`
- Apply weighted aggregation with confidence adjustment
- Produce `RiskScore` with level, rollback probability, merged recommendations
- Handle missing analyzers gracefully (use only what's available)

### Non-functional
- Deterministic output
- < 30 lines of core logic (KISS)
- Weights normalize to 1.0 automatically

## Architecture

```
scoring/
  __init__.py          -- re-exports
  weighted_scorer.py   -- WeightedScorer class
```

```python
class WeightedScorer:
    def __init__(self, config: ScorerConfig): ...
    def score(self, results: list[AnalyzerResult]) -> RiskScore: ...
```

## Related Code Files (EXCLUSIVE)

**Create:**
- `src/pr_risk_scorer/scoring/__init__.py`
- `src/pr_risk_scorer/scoring/weighted_scorer.py`
- `tests/test_scoring/__init__.py`
- `tests/test_scoring/test_weighted_scorer.py`

**Import (read-only):**
- `src/pr_risk_scorer/models.py` (AnalyzerResult, RiskScore, RiskLevel)
- `src/pr_risk_scorer/config.py` (ScorerConfig)

## File Ownership
| File | Owner |
|------|-------|
| `src/pr_risk_scorer/scoring/__init__.py` | Phase 05 |
| `src/pr_risk_scorer/scoring/weighted_scorer.py` | Phase 05 |
| `tests/test_scoring/__init__.py` | Phase 05 |
| `tests/test_scoring/test_weighted_scorer.py` | Phase 05 |

## Implementation Steps

### 1. Create `src/pr_risk_scorer/scoring/weighted_scorer.py`

```python
from pr_risk_scorer.models import AnalyzerResult, RiskScore, RiskLevel
from pr_risk_scorer.config import ScorerConfig


class WeightedScorer:
    def __init__(self, config: ScorerConfig | None = None):
        self.config = config or ScorerConfig()

    def score(self, results: list[AnalyzerResult]) -> RiskScore:
        if not results:
            return RiskScore(
                overall_score=0.0,
                risk_level=RiskLevel.LOW,
            )

        # Build weight map from config
        weight_map = {
            name: ac.weight
            for name, ac in self.config.analyzers.items()
            if ac.enabled
        }

        # Match results to weights; normalize
        matched = []
        for r in results:
            w = weight_map.get(r.analyzer_name, 0.0)
            if w > 0:
                matched.append((r, w))

        if not matched:
            return RiskScore(overall_score=0.0, risk_level=RiskLevel.LOW)

        total_weight = sum(w for _, w in matched)
        weighted_sum = sum(
            r.score * r.confidence * (w / total_weight)
            for r, w in matched
        )

        # Hybrid amplification: boost when 2+ analyzers score > 70
        high_count = sum(1 for r, _ in matched if r.score * r.confidence > 70)
        amplifier = 1.0 + (0.15 * high_count) if high_count >= 2 else 1.0
        overall = min(max(weighted_sum * amplifier, 0.0), 100.0)

        # Rollback probability: simple linear mapping
        rollback_prob = min(overall / 100.0 * 0.8, 0.8)  # cap at 80%

        # Merge recommendations
        all_recs = []
        for r, _ in matched:
            all_recs.extend(r.recommendations)

        return RiskScore(
            overall_score=round(overall, 1),
            risk_level=RiskScore.level_from_score(overall),
            analyzer_results=results,
            rollback_probability=round(rollback_prob, 3),
            recommendations=all_recs,
        )
```

### 2. Create `src/pr_risk_scorer/scoring/__init__.py`

```python
from pr_risk_scorer.scoring.weighted_scorer import WeightedScorer

__all__ = ["WeightedScorer"]
```

### 3. Create `tests/test_scoring/test_weighted_scorer.py`

Test cases:
- `test_empty_results` -- no results = score 0, LOW level
- `test_all_low_scores` -- all analyzers score 10 = overall ~10, LOW
- `test_all_high_scores` -- all analyzers score 90 = overall ~90, CRITICAL
- `test_mixed_scores` -- varied scores, verify weighted average
- `test_confidence_weighting` -- low confidence reduces effective score
- `test_missing_analyzer` -- result with unknown name, weight 0, excluded
- `test_risk_level_thresholds` -- verify LOW/MEDIUM/HIGH/CRITICAL boundaries
- `test_rollback_probability` -- verify rollback_prob scales with score
- `test_recommendations_merged` -- all analyzer recommendations appear in output
- `test_hybrid_amplification` -- 2+ analyzers > 70 boosts score by 15% each
- `test_no_amplification_single_high` -- only 1 analyzer > 70, no boost

## Todo List
- [ ] Create `src/pr_risk_scorer/scoring/__init__.py`
- [ ] Create `src/pr_risk_scorer/scoring/weighted_scorer.py`
- [ ] Create `tests/test_scoring/__init__.py`
- [ ] Create `tests/test_scoring/test_weighted_scorer.py`
- [ ] Verify all tests pass: `pytest tests/test_scoring/`

## Success Criteria
- `WeightedScorer().score([])` returns RiskScore with score=0, level=LOW
- Weighted average computed correctly with normalized weights
- Confidence < 1.0 reduces effective score proportionally
- Risk level matches thresholds: <25=LOW, 25-49=MEDIUM, 50-74=HIGH, >=75=CRITICAL
- Rollback probability scales with overall score, capped at 0.8
- All tests pass

## Conflict Prevention
- Only creates files in `scoring/` and `tests/test_scoring/`
- No overlap with any analyzer files or output files
- Imports only from `models.py` and `config.py`

## Risk Assessment
- **Very Low**: Simple weighted average, well-defined interface
- **Risk**: Weight normalization edge case (all weights 0)
- **Mitigation**: Guard clause returns score 0 if no matched analyzers

## Security Considerations
- Pure computation, no I/O, no secrets
- Score clamped to [0, 100], rollback to [0, 0.8]

## Next Steps
- Phase 07 wires `WeightedScorer` into pipeline after all analyzers run
