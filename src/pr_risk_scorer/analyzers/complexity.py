"""Analyzer for code complexity risk."""

from pr_risk_scorer.analyzers.base_analyzer import BaseAnalyzer
from pr_risk_scorer.models import AnalyzerResult, PRData


class ComplexityAnalyzer(BaseAnalyzer):
    """Analyzes code complexity from patch content."""

    name = "complexity"

    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        """Analyze code complexity and return risk score."""
        max_nesting = 0
        conditionals = 0
        loops = 0
        long_lines = 0

        for file in pr_data.files:
            if not file.patch:
                continue

            # Parse patch for added lines
            for line in file.patch.split("\n"):
                if not line.startswith("+"):
                    continue

                # Remove the '+' prefix for analysis
                code_line = line[1:]

                # Count nesting depth (leading whitespace / 4 for typical indentation)
                if code_line and not code_line.isspace():
                    leading_spaces = len(code_line) - len(code_line.lstrip())
                    nesting_level = leading_spaces // 4
                    max_nesting = max(max_nesting, nesting_level)

                # Count conditionals
                stripped = code_line.strip()
                if any(
                    stripped.startswith(kw)
                    for kw in [
                        "if ",
                        "elif ",
                        "else:",
                        "else ",
                        "switch ",
                        "case ",
                    ]
                ):
                    conditionals += 1

                # Count loops
                if any(
                    stripped.startswith(kw) for kw in ["for ", "while ", "do "]
                ):
                    loops += 1

                # Count long lines (120+ chars)
                if len(code_line) > 120:
                    long_lines += 1

        # Calculate component scores
        nesting_score = min(max_nesting / 5, 1.0) * 100
        conditional_score = min(conditionals / 15, 1.0) * 100
        loop_score = min(loops / 8, 1.0) * 80
        line_length_score = min(long_lines / 10, 1.0) * 60

        # Weighted final score
        final_score = (
            0.30 * nesting_score
            + 0.30 * conditional_score
            + 0.25 * loop_score
            + 0.15 * line_length_score
        )
        final_score = max(0.0, min(100.0, final_score))

        # Build recommendations
        recommendations = []
        if max_nesting >= 4:
            recommendations.append(
                "Deep nesting detected; consider refactoring for readability"
            )
        if conditionals >= 10:
            recommendations.append(
                "High conditional complexity; consider simplifying logic"
            )
        if loops >= 5:
            recommendations.append(
                "Multiple loops added; verify performance and consider optimization"
            )
        if long_lines >= 5:
            recommendations.append(
                "Long lines detected; consider breaking into smaller statements"
            )

        return AnalyzerResult(
            analyzer_name=self.name,
            score=final_score,
            confidence=0.7,
            details={
                "max_nesting": max_nesting,
                "conditionals": conditionals,
                "loops": loops,
                "long_lines": long_lines,
                "nesting_score": round(nesting_score, 2),
                "conditional_score": round(conditional_score, 2),
                "loop_score": round(loop_score, 2),
                "line_length_score": round(line_length_score, 2),
            },
            recommendations=recommendations,
        )
