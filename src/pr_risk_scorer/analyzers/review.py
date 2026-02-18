"""Analyzer for PR review coverage risk."""

from pr_risk_scorer.analyzers.base_analyzer import BaseAnalyzer
from pr_risk_scorer.models import AnalyzerResult, PRData


class ReviewAnalyzer(BaseAnalyzer):
    """Analyzes risk based on review coverage and quality."""

    name = "review"

    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        """Analyze review data and return risk score (inverted: more reviews = lower risk)."""
        review_count = len(pr_data.reviews)
        approval_count = sum(1 for r in pr_data.reviews if r.state == "APPROVED")
        changes_requested = sum(
            1 for r in pr_data.reviews if r.state == "CHANGES_REQUESTED"
        )
        reviews_with_body = sum(1 for r in pr_data.reviews if r.body and r.body.strip())

        # Calculate metrics
        review_coverage = min(approval_count / 2, 1.0)
        review_depth = (
            min(reviews_with_body / max(review_count, 1), 1.0) if review_count > 0 else 0.0
        )
        pending_changes = 1.0 if changes_requested > 0 and approval_count == 0 else 0.0

        # Inverted score: more reviews = lower risk
        base_score = (1 - 0.50 * review_coverage - 0.30 * review_depth) * 80
        final_score = base_score + pending_changes * 20
        final_score = max(0.0, min(100.0, final_score))

        # Build recommendations
        recommendations = []
        if review_count == 0:
            recommendations.append(
                "No reviews yet; PR should be reviewed before merging"
            )
        elif approval_count == 0:
            recommendations.append(
                "No approvals yet; ensure reviewers approve before merging"
            )

        if changes_requested > 0 and approval_count == 0:
            recommendations.append(
                "Outstanding change requests; address feedback before merging"
            )

        if approval_count == 1 and review_count == 1:
            recommendations.append(
                "Single reviewer only; consider additional review for critical changes"
            )

        if reviews_with_body < review_count / 2 and review_count > 0:
            recommendations.append(
                "Some reviews lack detailed comments; ensure thorough review"
            )

        return AnalyzerResult(
            analyzer_name=self.name,
            score=final_score,
            confidence=0.9,
            details={
                "review_count": review_count,
                "approval_count": approval_count,
                "changes_requested": changes_requested,
                "reviews_with_body": reviews_with_body,
                "review_coverage": round(review_coverage, 2),
                "review_depth": round(review_depth, 2),
                "pending_changes": round(pending_changes, 2),
            },
            recommendations=recommendations,
        )
