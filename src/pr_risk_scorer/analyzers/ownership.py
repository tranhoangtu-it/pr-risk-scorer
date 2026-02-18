"""OwnershipAnalyzer: Detects cross-domain changes and deep directory structures."""

from pr_risk_scorer.analyzers.base_analyzer import BaseAnalyzer
from pr_risk_scorer.models import AnalyzerResult, PRData


class OwnershipAnalyzer(BaseAnalyzer):
    """Analyzes PR risk based on ownership boundaries and domain complexity."""

    name = "ownership"

    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        """Analyze ownership risk based on cross-domain changes and directory depth."""
        if not pr_data.files:
            return AnalyzerResult(
                analyzer_name=self.name,
                score=0.0,
                confidence=0.5,
                details={
                    "unique_top_dirs": 0,
                    "max_depth": 0,
                    "cross_domain_score": 0.0,
                    "depth_score": 0.0,
                },
                recommendations=[],
            )

        # Extract top-level directories (domains)
        unique_top_dirs = set()
        max_depth = 0

        for file_change in pr_data.files:
            parts = file_change.filename.split("/")

            # Track top-level directory
            if parts:
                unique_top_dirs.add(parts[0])

            # Track maximum depth
            depth = len(parts)
            max_depth = max(max_depth, depth)

        # Calculate sub-scores
        cross_domain_score = min(len(unique_top_dirs) / 3, 1.0) * 100
        depth_score = min(max_depth / 5, 1.0) * 50

        # Weighted final score
        final_score = (0.60 * cross_domain_score) + (0.40 * depth_score)

        # Build details
        details = {
            "unique_top_dirs": len(unique_top_dirs),
            "max_depth": max_depth,
            "cross_domain_score": round(cross_domain_score, 2),
            "depth_score": round(depth_score, 2),
        }

        # Generate recommendations
        recommendations = []
        if cross_domain_score > 60:
            recommendations.append(
                "Changes span multiple domains; ensure domain experts review"
            )

        return AnalyzerResult(
            analyzer_name=self.name,
            score=final_score,
            confidence=0.5,
            details=details,
            recommendations=recommendations,
        )
