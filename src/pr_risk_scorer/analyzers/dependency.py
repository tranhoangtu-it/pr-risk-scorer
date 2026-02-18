"""Analyzer for dependency and import changes risk."""

from pr_risk_scorer.analyzers.base_analyzer import BaseAnalyzer
from pr_risk_scorer.models import AnalyzerResult, PRData


class DependencyAnalyzer(BaseAnalyzer):
    """Analyzes risk from dependency and import changes."""

    name = "dependency"

    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        """Analyze dependency changes and return risk score."""
        dep_files = [
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "Gemfile",
        ]

        # Count dependency files modified
        dep_file_count = 0
        dep_loc = 0
        for file in pr_data.files:
            filename_lower = file.filename.lower()
            if any(dep_file in filename_lower for dep_file in dep_files):
                dep_file_count += 1
                dep_loc += file.additions + file.deletions

        # Count import changes in Python files
        import_changes = 0
        for file in pr_data.files:
            if file.filename.endswith(".py") and file.patch:
                # Count lines with import/from statements
                for line in file.patch.split("\n"):
                    if line.startswith("+") or line.startswith("-"):
                        stripped = line[1:].strip()
                        if stripped.startswith("import ") or stripped.startswith("from "):
                            import_changes += 1

        # Calculate component scores
        dep_file_score = min(dep_file_count / 2, 1.0) * 100
        import_change_score = min(import_changes / 10, 1.0) * 60
        dep_loc_score = min(dep_loc / 50, 1.0) * 80

        # Weighted final score
        final_score = (
            0.40 * dep_file_score + 0.35 * dep_loc_score + 0.25 * import_change_score
        )
        final_score = max(0.0, min(100.0, final_score))

        # Build recommendations
        recommendations = []
        if dep_file_count > 0:
            recommendations.append(
                "Dependency changes detected; verify compatibility and pin versions"
            )
        if import_changes >= 5:
            recommendations.append(
                "Multiple import changes; check for circular dependencies"
            )
        if dep_loc > 30:
            recommendations.append(
                "Significant dependency modifications; review security advisories"
            )

        return AnalyzerResult(
            analyzer_name=self.name,
            score=final_score,
            confidence=0.8,
            details={
                "dep_file_count": dep_file_count,
                "dep_loc": dep_loc,
                "import_changes": import_changes,
                "dep_file_score": round(dep_file_score, 2),
                "dep_loc_score": round(dep_loc_score, 2),
                "import_change_score": round(import_change_score, 2),
            },
            recommendations=recommendations,
        )
