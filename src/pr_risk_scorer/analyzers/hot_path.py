"""HotPathAnalyzer: Identifies high-churn areas and frequently modified files."""

from pr_risk_scorer.analyzers.base_analyzer import BaseAnalyzer
from pr_risk_scorer.models import AnalyzerResult, PRData


class HotPathAnalyzer(BaseAnalyzer):
    """Analyzes PR risk based on commit churn and file diversity."""

    name = "hot_path"

    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        """Analyze hot path risk based on commits, file diversity, and patch size."""
        commits_count = pr_data.commits_count
        files_count = len(pr_data.files)

        # Calculate churn signal
        churn_signal = min(commits_count / 10, 1.0) * 100

        # Calculate file diversity
        file_diversity = min(files_count / 15, 1.0) * 100

        # Calculate patch size signal
        files_with_patch = sum(1 for f in pr_data.files if f.patch)
        patch_size_signal = 0.0
        if files_count > 0:
            # Count lines in patches
            total_patch_lines = 0
            for file_change in pr_data.files:
                if file_change.patch:
                    total_patch_lines += len(file_change.patch.split("\n"))

            # Normalize against total files
            patch_size_signal = min((total_patch_lines / max(files_count, 1)) / 20, 1.0) * 100

        # Weighted final score
        final_score = (
            0.40 * churn_signal +
            0.35 * file_diversity +
            0.25 * patch_size_signal
        )

        # Build details
        details = {
            "commits_count": commits_count,
            "files_count": files_count,
            "files_with_patch": files_with_patch,
            "churn_signal": round(churn_signal, 2),
            "file_diversity": round(file_diversity, 2),
            "patch_size_signal": round(patch_size_signal, 2),
        }

        # Generate recommendations
        recommendations = []
        if churn_signal > 60:
            recommendations.append(
                "This PR has many commits; consider squashing and rebasing"
            )

        return AnalyzerResult(
            analyzer_name=self.name,
            score=final_score,
            confidence=0.6,
            details=details,
            recommendations=recommendations,
        )
