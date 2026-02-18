"""BlastRadiusAnalyzer: Measures PR impact based on files changed, LOC, and modules."""

from pr_risk_scorer.analyzers.base_analyzer import BaseAnalyzer
from pr_risk_scorer.models import AnalyzerResult, PRData


class BlastRadiusAnalyzer(BaseAnalyzer):
    """Analyzes PR risk based on the scope and scale of changes."""

    name = "blast_radius"

    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        """Analyze blast radius based on files, LOC, and modules affected."""
        files_changed = len(pr_data.files)
        total_additions = sum(f.additions for f in pr_data.files)
        total_deletions = sum(f.deletions for f in pr_data.files)
        total_loc = total_additions + total_deletions

        # Extract unique directories (modules)
        unique_dirs = set()
        largest_file = {"name": "", "loc": 0}

        for file_change in pr_data.files:
            # Get directory path (module)
            parts = file_change.filename.split("/")
            if len(parts) > 1:
                unique_dirs.add(parts[0])

            # Track largest file
            file_loc = file_change.additions + file_change.deletions
            if file_loc > largest_file["loc"]:
                largest_file = {"name": file_change.filename, "loc": file_loc}

        modules_affected = len(unique_dirs)

        # Calculate sub-scores
        files_score = min(files_changed / 20, 1.0) * 100
        loc_score = min(total_loc / 500, 1.0) * 100
        module_score = min(modules_affected / 5, 1.0) * 100

        # Weighted final score
        final_score = (0.50 * files_score) + (0.30 * loc_score) + (0.20 * module_score)

        # Build details
        details = {
            "files_changed": files_changed,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "modules_affected": modules_affected,
            "largest_file": largest_file["name"],
            "largest_file_loc": largest_file["loc"],
        }

        # Generate recommendations
        recommendations = []
        if final_score > 50:
            recommendations.append("Consider splitting this PR into smaller changes")

        if largest_file["loc"] > 300:
            recommendations.append(
                f"File {largest_file['name']} has {largest_file['loc']}+ LOC changes; review carefully"
            )

        return AnalyzerResult(
            analyzer_name=self.name,
            score=final_score,
            confidence=1.0,
            details=details,
            recommendations=recommendations,
        )
