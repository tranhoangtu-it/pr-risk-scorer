# PR Risk Scorer - Codebase Summary

## Repository Overview

**Location**: `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer`
**Size**: ~1,175 LOC source, ~2,294 LOC tests
**Coverage**: 100% (111 tests)
**Language**: Python 3.10+
**Build System**: Hatchling
**Package**: Installable via pip

## Directory Structure

```
pr-risk-scorer/
├── src/pr_risk_scorer/              # Main package
│   ├── analyzers/                   # 6 risk analyzers (518 LOC total)
│   │   ├── __init__.py              # Registry, exports ALL_ANALYZERS
│   │   ├── base_analyzer.py         # ABC BaseAnalyzer (16 LOC)
│   │   ├── blast_radius.py          # BlastRadiusAnalyzer (71 LOC)
│   │   ├── complexity.py            # ComplexityAnalyzer (111 LOC)
│   │   ├── dependency.py            # DependencyAnalyzer (82 LOC)
│   │   ├── hot_path.py              # HotPathAnalyzer (66 LOC)
│   │   ├── ownership.py             # OwnershipAnalyzer (71 LOC)
│   │   └── review.py                # ReviewAnalyzer (73 LOC)
│   ├── output/                      # Reporter pattern (3 formatters)
│   │   ├── __init__.py              # Factory, BaseReporter ABC (51 LOC)
│   │   ├── terminal_reporter.py     # Rich terminal output (79 LOC)
│   │   ├── json_reporter.py         # JSON output (16 LOC)
│   │   └── markdown_reporter.py     # Markdown output (63 LOC)
│   ├── scoring/                     # Scoring engine
│   │   ├── __init__.py              # Empty
│   │   └── weighted_scorer.py       # WeightedScorer class (55 LOC)
│   ├── __init__.py                  # Package init (3 LOC)
│   ├── cli.py                       # Typer CLI (123 LOC)
│   ├── config.py                    # YAML config system (38 LOC)
│   ├── github_client.py             # GitHub API wrapper (145 LOC)
│   └── models.py                    # Pydantic models (81 LOC)
├── tests/                           # Full test suite (111 tests, 100% coverage)
│   ├── test_analyzers/              # 6 analyzer test modules
│   ├── test_output/                 # 4 output formatter tests
│   ├── test_scoring/                # WeightedScorer tests
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_cli.py                  # CLI command tests
│   ├── test_config.py               # Config loading tests
│   └── test_github_client.py        # API client tests
├── .github/workflows/               # CI/CD
│   └── ci.yml                       # GitHub Actions pipeline
├── pyproject.toml                   # Package metadata & deps
├── README.md                        # User guide
└── .pr-risk-scorer.yaml             # Default config template
```

## Core Module Reference

### Entry Point: cli.py (123 LOC)
**Purpose**: Typer CLI interface with 3 commands
**Commands**:
- `analyze <owner/repo> --pr <num>` - Score single PR
- `report <owner/repo> --since <date>` - Batch analyze merged PRs
- `config` - Initialize default `.pr-risk-scorer.yaml`

**Key Functions**:
- `analyze()` - Fetch PR data, run analyzers, display result
- `report()` - Iterate merged PRs, batch analyze with limit
- `config_init()` - Generate YAML config template
- `main()` - Typer app entry point

**Dependencies**: typer, rich, GitHubClient, ALL_ANALYZERS, WeightedScorer, get_reporter

---

### Data Models: models.py (81 LOC)
**Purpose**: Pydantic models for type safety & validation

**Models**:
```python
RiskLevel(Enum)              # LOW, MEDIUM, HIGH, CRITICAL
FileChange(BaseModel)        # filename, additions, deletions, status, patch
ReviewData(BaseModel)        # reviewer, state, submitted_at, body
PRData(BaseModel)            # owner, repo, number, title, files, reviews, etc
AnalyzerResult(BaseModel)    # analyzer_name, score (0-100), confidence, details, recommendations
RiskScore(BaseModel)         # overall_score, risk_level, analyzer_results, recommendations
```

**Key Methods**:
- `RiskScore.level_from_score(score: float) -> RiskLevel` - Map 0-100 to risk level

---

### Configuration: config.py (38 LOC)
**Purpose**: YAML-based configuration with defaults

**Models**:
```python
AnalyzerConfig          # enabled: bool, weight: float (0-1)
ScorerConfig            # github_token, analyzers dict, output_format, risk_thresholds
```

**Key Methods**:
- `ScorerConfig.load(path: Path | None) -> ScorerConfig` - Load from YAML or defaults

**Default Weights** (sum to 1.0):
- blast_radius: 0.25
- hot_path: 0.20
- complexity: 0.15
- ownership: 0.15
- dependency: 0.15
- review: 0.10

---

### GitHub Integration: github_client.py (145 LOC)
**Purpose**: PyGithub wrapper for GitHub API interaction

**Class**: `GitHubClient`
**Key Methods**:
- `__init__(config: ScorerConfig)` - Init with token from config or env
- `fetch_pr_data(owner, repo, pr_num) -> PRData` - Fetch all PR metadata
- `fetch_blame_data()` - Get file authors (for ownership analysis)
- `get_repo_contributors() -> dict` - Fetch repo contributor stats

**Error Handling**:
- `GitHubClientError` exception for API failures
- Graceful handling of 404, 401, rate limits

**Dependencies**: PyGithub, requests

---

### Scoring Engine: scoring/weighted_scorer.py (55 LOC)
**Purpose**: Aggregate analyzer results into final risk score

**Class**: `WeightedScorer`
**Algorithm**:
1. Build weight map from ScorerConfig
2. Filter results to enabled analyzers
3. Normalize weights (sum to 1.0)
4. Calculate: `weighted_sum = Σ(score × confidence × normalized_weight)`
5. Hybrid amplification: If 2+ analyzers score >70, multiply by 1.15-1.45
6. Clamp to 0-100, calculate rollback probability (0-0.8)
7. Merge all recommendations

**Key Method**:
- `score(results: list[AnalyzerResult]) -> RiskScore`

---

### Analyzers: analyzers/ (518 LOC total)

**Base Class**: `BaseAnalyzer` (16 LOC)
- Abstract `analyze(pr_data: PRData) -> AnalyzerResult`
- All analyzers must set `name` class variable

**All Analyzers Pattern**:
1. Calculate sub-metrics from PRData
2. Compute sub-scores (0-100 each)
3. Combine with weighted formula
4. Build details dict & recommendations
5. Return AnalyzerResult

**BlastRadiusAnalyzer** (71 LOC)
- **Metrics**: Files changed, LOC delta, modules affected
- **Sub-scores**: files (50%), LOC (30%), modules (20%)
- **Thresholds**: Files >20, LOC >500, modules >5 trigger warnings
- **Recommendations**: Split PR if >50, large files reviewed carefully

**HotPathAnalyzer** (66 LOC)
- **Metrics**: Commit count, file diversity, patch size
- **Risk**: High churn in few files signals fragility
- **Details**: commits_count, distinct_files, avg_patch_size

**ComplexityAnalyzer** (111 LOC)
- **Metrics**: Max nesting depth, conditionals/loops, line length
- **Details**: max_nesting, total_conditionals, total_loops, max_line_length
- **Thresholds**: Nesting >5, long lines >120 chars flag complexity

**OwnershipAnalyzer** (71 LOC)
- **Metrics**: Directory count, unique dirs, max depth
- **Insight**: Cross-domain changes increase coordination risk
- **Details**: directories_count, unique_dirs, max_depth

**DependencyAnalyzer** (82 LOC)
- **Metrics**: Dependency file changes, import changes
- **Files**: package.json, requirements.txt, pom.xml, Gemfile, etc
- **Risk**: Dep changes high-impact but under-reviewed
- **Details**: dep_files_modified, import_changes

**ReviewAnalyzer** (73 LOC)
- **Metrics**: Approval ratio, reviewer count, review quality
- **Thresholds**: Require 2+ approvals, flag if 0-1 reviewers
- **Details**: total_reviews, approvals, requested_changes

---

### Output Formatters: output/ (209 LOC total)

**Base Class**: `BaseReporter` (ABC)
- Abstract `display(risk_score: RiskScore) -> None`

**Factory**: `get_reporter(format: str) -> BaseReporter`
- Supports: "terminal", "json", "markdown"

**TerminalReporter** (79 LOC)
- Uses Rich library for colored, formatted output
- Displays: Overall score, risk level, per-analyzer breakdown
- Shows: Details, recommendations, rollback probability
- Color-coded by risk level (green/yellow/red/red-on-white)

**JSONReporter** (16 LOC)
- Output: JSON string of RiskScore model
- Use: CI/CD pipeline integration, parsing scores
- Pretty-printed for readability

**MarkdownReporter** (63 LOC)
- Output: Markdown-formatted report
- Use: PR comments, shared documents
- Includes: Summary section, analyzer breakdown, recommendations

---

## Dependency Graph

```
cli.py
├── config.py (ScorerConfig)
├── github_client.py (GitHubClient)
├── analyzers/__init__.py (ALL_ANALYZERS)
│   └── analyzers/base_analyzer.py (BaseAnalyzer)
│       └── analyzers/*.py (6 concrete analyzers)
├── scoring/weighted_scorer.py (WeightedScorer)
└── output/__init__.py (get_reporter)
    └── output/*.py (3 reporters)

models.py (shared models used everywhere)
```

## Test Suite (111 tests, 100% coverage)

| Module | Tests | Focus |
|---|---|---|
| test_cli.py | 25 | Commands, error handling, integration |
| test_config.py | 8 | YAML loading, defaults, validation |
| test_github_client.py | 15 | API calls, mocking, error cases |
| test_analyzers/ | 40+ | Each analyzer's scoring logic |
| test_output/ | 15 | Formatters, reporter factory |
| test_scoring/ | 8 | Weighting, amplification, rollback prob |

**Test Tools**: pytest, pytest-mock (API mocking), pytest-cov (100% coverage)
**Fixtures**: conftest.py provides mock GitHubClient, PRData, config

---

## Key Patterns & Conventions

### Strategy Pattern (Analyzers)
Each analyzer is independent, swappable, implements BaseAnalyzer.
Registry (`ALL_ANALYZERS`) enables iteration without hardcoding.

### Factory Pattern (Output)
`get_reporter()` decouples CLI from specific formatters.
Easy to add new output types without modifying cli.py.

### Configuration as Code
YAML config enables customization (weights, thresholds, enables) without code changes.
Pydantic models validate configuration structure & types.

### Type Safety
All inputs/outputs type-hinted. Pydantic models validate at boundaries.
No untyped dicts or loose types.

### Error Handling
Custom exceptions (GitHubClientError) for domain errors.
Graceful CLI exit codes & user-friendly error messages.

---

## External Dependencies

| Package | Version | Purpose |
|---|---|---|
| typer | >=0.9.0 | CLI framework |
| rich | >=13.0.0 | Terminal formatting |
| PyGithub | >=2.0.0 | GitHub API client |
| pydantic | >=2.0.0 | Data validation |
| pyyaml | >=6.0 | Config file parsing |
| pytest | >=7.0.0 | Testing |
| pytest-mock | >=3.0.0 | API mocking |
| pytest-cov | >=4.0.0 | Coverage reporting |
| ruff | >=0.1.0 | Linting |

---

## Performance Characteristics

| Operation | Typical Time |
|---|---|
| Fetch PR data (GitHub API) | 0.5-1.0s |
| Analyze single PR (6 analyzers) | 0.05-0.2s |
| Generate report (10 PRs) | 5-10s |
| Output formatting | <0.01s |

**Bottleneck**: GitHub API calls (network I/O)
**Potential Optimization**: Redis cache for repeated analyses

---

**Last Updated**: 2026-02-18
**Codebase Version**: 0.1.0
**Generated from**: repomix-output.xml
