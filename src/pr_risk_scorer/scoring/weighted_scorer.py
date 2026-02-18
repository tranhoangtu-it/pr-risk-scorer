from pr_risk_scorer.models import AnalyzerResult, RiskScore, RiskLevel
from pr_risk_scorer.config import ScorerConfig


class WeightedScorer:
    def __init__(self, config: ScorerConfig | None = None):
        self.config = config or ScorerConfig()

    def score(self, results: list[AnalyzerResult]) -> RiskScore:
        if not results:
            return RiskScore(overall_score=0.0, risk_level=RiskLevel.LOW)

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
        rollback_prob = min(overall / 100.0 * 0.8, 0.8)

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
