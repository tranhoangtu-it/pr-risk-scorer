# Phase 06: Output Formatters

## Context Links
- [Plan Overview](./plan.md)
- [Phase 01: Foundation](./phase-01-project-setup-and-foundation.md) (dependency)
- [Research: Tech Architecture - Section 5](./research/researcher-260218-1858-tech-architecture.md)

## Parallelization Info
- **Execution**: PARALLEL with Phases 02, 03, 04, 05
- **Blocked by**: Phase 01
- **Blocks**: Phase 07

## Overview
- **Priority**: P2
- **Status**: pending
- **Effort**: 1h
- **Description**: Three output formatters (Terminal/Rich, JSON, Markdown) implementing a common reporter interface. Each takes a `RiskScore` and renders it.

## Key Insights
- Terminal output uses Rich library: tables, color-coded risk levels, progress bars
- JSON output for CI/CD integration (machine-readable)
- Markdown output for GitHub PR comments or file reports
- Strategy pattern: all reporters share same interface

## Requirements

### Functional
- **TerminalReporter**: Rich table with risk breakdown, color-coded, recommendations
- **JsonReporter**: Structured JSON output, serializable from RiskScore
- **MarkdownReporter**: GitHub-flavored markdown with tables, risk badges

### Non-functional
- Each reporter < 60 lines
- TerminalReporter uses Rich Console, not print()
- JSON output is valid JSON (use Pydantic `.model_dump_json()`)

## Architecture

```
output/
  __init__.py              -- BaseReporter ABC, factory function
  terminal_reporter.py     -- TerminalReporter (Rich)
  json_reporter.py         -- JsonReporter
  markdown_reporter.py     -- MarkdownReporter
```

```python
class BaseReporter(ABC):
    @abstractmethod
    def render(self, risk_score: RiskScore) -> str: ...

    @abstractmethod
    def display(self, risk_score: RiskScore) -> None: ...
```

## Related Code Files (EXCLUSIVE)

**Create:**
- `src/pr_risk_scorer/output/__init__.py`
- `src/pr_risk_scorer/output/terminal_reporter.py`
- `src/pr_risk_scorer/output/json_reporter.py`
- `src/pr_risk_scorer/output/markdown_reporter.py`
- `tests/test_output/__init__.py`
- `tests/test_output/test_terminal_reporter.py`
- `tests/test_output/test_json_reporter.py`
- `tests/test_output/test_markdown_reporter.py`

**Import (read-only):**
- `src/pr_risk_scorer/models.py` (RiskScore, AnalyzerResult, RiskLevel)

## File Ownership
| File | Owner |
|------|-------|
| `src/pr_risk_scorer/output/__init__.py` | Phase 06 |
| `src/pr_risk_scorer/output/terminal_reporter.py` | Phase 06 |
| `src/pr_risk_scorer/output/json_reporter.py` | Phase 06 |
| `src/pr_risk_scorer/output/markdown_reporter.py` | Phase 06 |
| `tests/test_output/__init__.py` | Phase 06 |
| `tests/test_output/test_terminal_reporter.py` | Phase 06 |
| `tests/test_output/test_json_reporter.py` | Phase 06 |
| `tests/test_output/test_markdown_reporter.py` | Phase 06 |

## Implementation Steps

### 1. Create `src/pr_risk_scorer/output/__init__.py`

```python
from abc import ABC, abstractmethod
from pr_risk_scorer.models import RiskScore


class BaseReporter(ABC):
    @abstractmethod
    def render(self, risk_score: RiskScore) -> str:
        """Return formatted string representation."""
        ...

    @abstractmethod
    def display(self, risk_score: RiskScore) -> None:
        """Output to stdout."""
        ...


def get_reporter(format_name: str) -> BaseReporter:
    from pr_risk_scorer.output.terminal_reporter import TerminalReporter
    from pr_risk_scorer.output.json_reporter import JsonReporter
    from pr_risk_scorer.output.markdown_reporter import MarkdownReporter

    reporters = {
        "terminal": TerminalReporter,
        "json": JsonReporter,
        "markdown": MarkdownReporter,
    }
    cls = reporters.get(format_name)
    if cls is None:
        raise ValueError(f"Unknown format: {format_name}. Options: {list(reporters.keys())}")
    return cls()


__all__ = ["BaseReporter", "get_reporter"]
```

### 2. TerminalReporter (`terminal_reporter.py`)

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pr_risk_scorer.models import RiskScore, RiskLevel
from pr_risk_scorer.output import BaseReporter

RISK_COLORS = {
    RiskLevel.LOW: "green",
    RiskLevel.MEDIUM: "yellow",
    RiskLevel.HIGH: "red",
    RiskLevel.CRITICAL: "bold red",
}

class TerminalReporter(BaseReporter):
    def __init__(self):
        self.console = Console()

    def render(self, risk_score: RiskScore) -> str:
        # Build string representation (for capture/testing)
        lines = [f"Risk Score: {risk_score.overall_score}/100 ({risk_score.risk_level.value})"]
        lines.append(f"Rollback Probability: {risk_score.rollback_probability:.1%}")
        for ar in risk_score.analyzer_results:
            lines.append(f"  {ar.analyzer_name}: {ar.score:.1f} (confidence: {ar.confidence:.0%})")
        if risk_score.recommendations:
            lines.append("Recommendations:")
            for r in risk_score.recommendations:
                lines.append(f"  - {r}")
        return "\n".join(lines)

    def display(self, risk_score: RiskScore) -> None:
        color = RISK_COLORS.get(risk_score.risk_level, "white")
        # Header panel
        self.console.print(Panel(
            f"[{color}]Risk Score: {risk_score.overall_score}/100[/{color}]\n"
            f"Level: [{color}]{risk_score.risk_level.value.upper()}[/{color}]\n"
            f"Rollback Probability: {risk_score.rollback_probability:.1%}",
            title="PR Risk Assessment",
        ))
        # Analyzer breakdown table
        table = Table(title="Analyzer Breakdown")
        table.add_column("Analyzer", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Confidence", justify="right")
        for ar in risk_score.analyzer_results:
            table.add_row(ar.analyzer_name, f"{ar.score:.1f}", f"{ar.confidence:.0%}")
        self.console.print(table)
        # Recommendations
        if risk_score.recommendations:
            self.console.print("\n[bold]Recommendations:[/bold]")
            for rec in risk_score.recommendations:
                self.console.print(f"  [yellow]-[/yellow] {rec}")
```

### 3. JsonReporter (`json_reporter.py`)

```python
import json
from pr_risk_scorer.models import RiskScore
from pr_risk_scorer.output import BaseReporter

class JsonReporter(BaseReporter):
    def render(self, risk_score: RiskScore) -> str:
        return risk_score.model_dump_json(indent=2)

    def display(self, risk_score: RiskScore) -> None:
        print(self.render(risk_score))
```

### 4. MarkdownReporter (`markdown_reporter.py`)

Generates GitHub-flavored markdown:

```python
from pr_risk_scorer.models import RiskScore, RiskLevel
from pr_risk_scorer.output import BaseReporter

RISK_EMOJI = {
    RiskLevel.LOW: "LOW",
    RiskLevel.MEDIUM: "MEDIUM",
    RiskLevel.HIGH: "HIGH",
    RiskLevel.CRITICAL: "CRITICAL",
}

class MarkdownReporter(BaseReporter):
    def render(self, risk_score: RiskScore) -> str:
        lines = [
            f"# PR Risk Assessment",
            f"",
            f"**Overall Score:** {risk_score.overall_score}/100 | "
            f"**Level:** {RISK_EMOJI.get(risk_score.risk_level, '?')} | "
            f"**Rollback Probability:** {risk_score.rollback_probability:.1%}",
            f"",
            f"## Analyzer Breakdown",
            f"",
            f"| Analyzer | Score | Confidence |",
            f"|----------|------:|----------:|",
        ]
        for ar in risk_score.analyzer_results:
            lines.append(f"| {ar.analyzer_name} | {ar.score:.1f} | {ar.confidence:.0%} |")

        if risk_score.recommendations:
            lines.extend(["", "## Recommendations", ""])
            for rec in risk_score.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)

    def display(self, risk_score: RiskScore) -> None:
        print(self.render(risk_score))
```

### 5. Create tests

**test_terminal_reporter.py:**
- `test_render_returns_string` -- verify render() returns non-empty string
- `test_render_contains_score` -- verify score appears in output
- `test_display_no_error` -- verify display() runs without exception

**test_json_reporter.py:**
- `test_render_valid_json` -- json.loads(render()) succeeds
- `test_render_contains_fields` -- parsed JSON has overall_score, risk_level
- `test_round_trip` -- render then parse matches original model values

**test_markdown_reporter.py:**
- `test_render_has_header` -- contains "# PR Risk Assessment"
- `test_render_has_table` -- contains "| Analyzer |"
- `test_render_has_recommendations` -- contains "## Recommendations"
- `test_empty_recommendations` -- no recommendations section if list empty

**All reporters:**
- `test_get_reporter_factory` -- `get_reporter("json")` returns JsonReporter
- `test_get_reporter_invalid` -- `get_reporter("xml")` raises ValueError

## Todo List
- [ ] Create `src/pr_risk_scorer/output/__init__.py` with BaseReporter + factory
- [ ] Create `src/pr_risk_scorer/output/terminal_reporter.py`
- [ ] Create `src/pr_risk_scorer/output/json_reporter.py`
- [ ] Create `src/pr_risk_scorer/output/markdown_reporter.py`
- [ ] Create `tests/test_output/__init__.py`
- [ ] Create `tests/test_output/test_terminal_reporter.py`
- [ ] Create `tests/test_output/test_json_reporter.py`
- [ ] Create `tests/test_output/test_markdown_reporter.py`
- [ ] Verify all tests pass: `pytest tests/test_output/`

## Success Criteria
- `get_reporter("terminal")` returns TerminalReporter
- `get_reporter("json")` returns JsonReporter
- `get_reporter("markdown")` returns MarkdownReporter
- JSON output is valid JSON parseable by `json.loads`
- Markdown output contains table syntax and headers
- Terminal render includes score, level, analyzer breakdown
- All tests pass

## Conflict Prevention
- Only creates files in `output/` and `tests/test_output/`
- No overlap with analyzers, scoring, or CLI
- Imports only from `models.py`

## Risk Assessment
- **Very Low**: Formatting/rendering, no complex logic
- **Risk**: Rich Console output hard to test
- **Mitigation**: Test `render()` (string) not `display()` (console); display test just verifies no exception

## Security Considerations
- No secrets, no API calls
- JSON output: use Pydantic serialization (safe by default)
- Markdown: no user-injectable HTML (just model data)

## Next Steps
- Phase 07 wires `get_reporter` into CLI `--output` flag
