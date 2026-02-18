# PR Risk Scorer - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Layer (cli.py)                      │
│  Commands: analyze │ report │ config                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────────┐  ┌──────▼──────────┐
│ GitHub Client    │  │ Config Loader   │
│ (API Fetching)   │  │ (YAML → Models) │
└───────┬──────────┘  └──────┬──────────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Analyzer Pipeline  │
        │  (6 Analyzers)      │
        │  ① BlastRadius      │
        │  ② HotPath          │
        │  ③ Complexity       │
        │  ④ Ownership        │
        │  ⑤ Dependency       │
        │  ⑥ Review           │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │ Scoring Engine      │
        │ (WeightedScorer)    │
        │ • Normalize weights │
        │ • Apply confidence  │
        │ • Hybrid amplify    │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │ Output Formatters   │
        │ ① Terminal (Rich)   │
        │ ② JSON              │
        │ ③ Markdown          │
        └─────────────────────┘
```

## Data Flow

### Analyze Command Flow

```
User runs: pr-risk-scorer analyze owner/repo --pr 123 --output terminal
    │
    ├─> Parse args (Typer)
    │
    ├─> Load config: ScorerConfig.load(".pr-risk-scorer.yaml")
    │
    ├─> Create GitHubClient(config)
    │
    ├─> client.fetch_pr_data(owner, repo, 123)
    │   └─> GitHub API calls (REST)
    │       • Get PR metadata
    │       • List files changed
    │       • Get reviews
    │       • Get commits
    │       └─> Return PRData object
    │
    ├─> For each enabled analyzer in ALL_ANALYZERS:
    │   ├─> analyzer.analyze(pr_data)
    │   │   • Calculate metrics
    │   │   • Compute score (0-100)
    │   │   • Generate recommendations
    │   │   └─> Return AnalyzerResult
    │   └─> Collect results[]
    │
    ├─> scorer = WeightedScorer(config)
    │   scorer.score(results)
    │   • Normalize weights
    │   • Multiply by confidence
    │   • Apply hybrid amplification
    │   • Calculate rollback probability
    │   └─> Return RiskScore
    │
    ├─> reporter = get_reporter("terminal")
    │   reporter.display(risk_score)
    │   • Format with Rich colors
    │   • Print to console
    │
    └─> Exit code 0 (success)
```

### Report Command Flow

```
User runs: pr-risk-scorer report owner/repo --since 2026-01-01 --limit 20
    │
    ├─> Load config
    ├─> Create GitHubClient
    ├─> Query GitHub: get closed PRs sorted by update date
    │
    ├─> For each PR (up to limit):
    │   ├─> Check if merged_at >= since date
    │   ├─> fetch_pr_data(owner, repo, pr_number)
    │   ├─> Run all enabled analyzers
    │   ├─> Score with WeightedScorer
    │   ├─> Display result
    │   └─> Loop to next PR
    │
    └─> Print summary: "Analyzed X PRs"
```

## Module Interaction Diagram

```
┌─────────────────────┐
│   cli.py            │  Entry point, command dispatch
└──────────┬──────────┘
           │
    ┌──────┼──────────────┐
    │      │              │
    ▼      ▼              ▼
┌──────┐ ┌────────┐ ┌──────────┐
│config│ │github_ │ │analyzer/ │
│.py   │ │client  │ │  .py     │
└──┬───┘ │ .py    │ │(6 files) │
   │     └────┬───┘ └────┬─────┘
   │          │         │
   └──────┬───┴─────────┴──────────────┐
           │                           │
           ▼                           ▼
        ┌─────────┐            ┌─────────────────┐
        │ models  │            │ scoring/        │
        │ .py     │            │ weighted_scorer │
        └─────────┘            └────────┬────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │ output/         │
                              │ *.py (3 files)  │
                              └─────────────────┘
```

## Analyzer Architecture

Each analyzer is independent, implements strategy pattern:

```
BaseAnalyzer (ABC)
├── name: str = "base"
├── analyze(pr_data: PRData) -> AnalyzerResult

Concrete Analyzers:
├── BlastRadiusAnalyzer
│   └── Metrics: files_changed, total_loc, modules_affected
│
├── HotPathAnalyzer
│   └── Metrics: commits_count, file_diversity, patch_size
│
├── ComplexityAnalyzer
│   └── Metrics: nesting_depth, conditionals, loops, line_length
│
├── OwnershipAnalyzer
│   └── Metrics: directory_count, unique_dirs, max_depth
│
├── DependencyAnalyzer
│   └── Metrics: dep_files_modified, import_changes
│
└── ReviewAnalyzer
    └── Metrics: approval_ratio, reviewer_count
```

**Analyzer Execution Flow**:
```
1. Extract metrics from PRData
2. Calculate sub-scores (0-100 each)
3. Combine with weighted formula
4. Build details dict & recommendations
5. Return AnalyzerResult(score, confidence, details, recommendations)
```

## Scoring Algorithm

**Weighted Aggregation with Hybrid Amplification**:

```
Input: results[] = [AnalyzerResult, ...]

Step 1: Build weight map from config
  weight_map = {
    "blast_radius": 0.25,
    "hot_path": 0.20,
    "complexity": 0.15,
    "ownership": 0.15,
    "dependency": 0.15,
    "review": 0.10,
  }

Step 2: Normalize weights (sum to 1.0)
  total_weight = sum(weight for each enabled analyzer)
  normalized_weight = weight / total_weight

Step 3: Calculate weighted sum
  weighted_sum = Σ(
    analyzer_result.score ×
    analyzer_result.confidence ×
    normalized_weight
  )

Step 4: Apply hybrid amplification
  high_count = number of analyzers with (score × confidence) > 70
  if high_count >= 2:
    amplifier = 1.0 + (0.15 × high_count)
  else:
    amplifier = 1.0

  overall_score = min(max(weighted_sum × amplifier, 0.0), 100.0)

Step 5: Map to risk level
  if overall_score < 25:    risk_level = LOW
  elif overall_score < 50:  risk_level = MEDIUM
  elif overall_score < 75:  risk_level = HIGH
  else:                     risk_level = CRITICAL

Step 6: Calculate rollback probability
  rollback_prob = min(overall_score / 100.0 × 0.8, 0.8)

Output: RiskScore(
  overall_score=round(overall_score, 1),
  risk_level=risk_level,
  analyzer_results=results,
  rollback_probability=round(rollback_prob, 3),
  recommendations=[all recs from all analyzers]
)
```

## Configuration System

```
YAML File: .pr-risk-scorer.yaml
    │
    ▼
YAML Parser (PyYAML)
    │
    ▼
Pydantic Models (ScorerConfig)
    ├── github_token: str | None
    ├── analyzers: dict[str, AnalyzerConfig]
    │   └── AnalyzerConfig(enabled: bool, weight: float)
    ├── output_format: str
    └── risk_thresholds: dict[str, int]
    │
    ▼
ScorerConfig instance
    │
    ├─> WeightedScorer(config)
    ├─> GitHubClient(config)
    └─> CLI (output format, enabled analyzers)
```

**Configuration Priority** (first match wins):
1. Command-line override `--config /path/to/custom.yaml`
2. Current directory `.pr-risk-scorer.yaml`
3. Hardcoded defaults in ScorerConfig model

**Environment Variables**:
- `GITHUB_TOKEN`: Used if not in config file

## Output Format Architecture

Factory pattern decouples formatting logic:

```
get_reporter(format: str) -> BaseReporter

  "terminal" ──→ TerminalReporter (Rich output)
  "json"     ──→ JSONReporter (JSON serialization)
  "markdown" ──→ MarkdownReporter (Markdown formatting)

Each Reporter:
├── Implements: display(risk_score: RiskScore) -> None
├── Converts RiskScore to formatted output
└── Prints to stdout
```

**Output Examples**:

Terminal (Rich):
```
╭──────────────────────────────────────────────╮
│ Risk Score: 65 (HIGH)                       │
│ Rollback Probability: 52.0%                 │
├──────────────────────────────────────────────┤
│ Blast Radius:        45 (Moderate)          │
│ Hot Path:            72 (High)              │
│ Complexity:          80 (High)              │
│ Ownership:           50 (Medium)            │
│ Dependency:          30 (Low)               │
│ Review:              42 (Medium)            │
├──────────────────────────────────────────────┤
│ Recommendations:                             │
│ • Consider splitting this PR                │
│ • Ensure 2+ reviewers for complex code      │
╰──────────────────────────────────────────────╯
```

JSON:
```json
{
  "overall_score": 65,
  "risk_level": "high",
  "rollback_probability": 0.52,
  "analyzer_results": [...],
  "recommendations": [...]
}
```

Markdown:
```markdown
# PR Risk Assessment

**Overall Score**: 65 (HIGH)

...
```

## Error Handling Architecture

```
┌─────────────────────────────────────────┐
│ User Input / External API               │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Validation Layer                        │
│ • Pydantic models validate data         │
│ • Typer validates CLI args              │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
VALID          INVALID/ERROR
    │                 │
    ▼                 ▼
Continue     Custom Exception
process      (GitHubClientError,
             ConfigError, etc)
                      │
                      ▼
              CLI Error Handler
              ├─> Print error message (Red)
              ├─> Exit code 1
              └─> No traceback (user-friendly)
```

## Performance Characteristics

| Operation | Complexity | Time |
|-----------|-----------|------|
| Fetch PR data | O(1) network | 0.5-1.0s |
| Analyze 1 PR | O(n) where n=files | 0.05-0.2s |
| Score 1 PR | O(m) where m=analyzers | <0.01s |
| Format output | O(1) | <0.01s |
| Batch report (10 PRs) | O(10) | 5-10s |

**Bottleneck**: GitHub API calls (network I/O)
**Optimization Opportunity**: Cache results for repeated analyses

## Deployment Architecture

```
┌──────────────────────────────────────┐
│ Source Code                          │
│ git clone → python -m venv → pip     │
└──────────────────────┬───────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────────┐       ┌──────────────────┐
│ Local Dev Setup  │       │ CI/CD Pipeline   │
│ .venv/bin/       │       │ GitHub Actions   │
│ pr-risk-scorer   │       │ • pytest         │
└──────────────────┘       │ • coverage       │
                           │ • ruff lint      │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │ PyPI Registry    │
                           │ pip install      │
                           └──────────────────┘
```

## Security Architecture

```
Secrets Management:
├─ GITHUB_TOKEN
│  ├─ Source 1: Environment variable (CI/CD preferred)
│  ├─ Source 2: .pr-risk-scorer.yaml (local, user-managed)
│  └─ Source 3: Hardcoded (NEVER)
│
└─ Config File
   ├─ Pydantic validation (type-safe)
   ├─ No eval() or unsafe deserialization
   ├─ YAML only (safe format)
   └─ User responsible for file permissions

Data Flow:
├─ Input validation: Typer + Pydantic
├─ API calls: PyGithub (standard library)
├─ No data persistence
├─ No external calls except GitHub
└─ Error messages: User-friendly (no stack traces)
```

## Extensibility Points

### Adding a New Analyzer

1. Create `src/pr_risk_scorer/analyzers/my_analyzer.py`:
```python
class MyAnalyzer(BaseAnalyzer):
    name = "my_analyzer"

    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        score = self._calculate_score(pr_data)
        return AnalyzerResult(
            analyzer_name=self.name,
            score=score,
            ...
        )
```

2. Add to `ALL_ANALYZERS` in `src/pr_risk_scorer/analyzers/__init__.py`

3. Add config entry in `ScorerConfig` defaults

### Adding a New Output Format

1. Create `src/pr_risk_scorer/output/my_reporter.py`:
```python
class MyReporter(BaseReporter):
    def display(self, risk_score: RiskScore) -> None:
        # Custom formatting logic
        pass
```

2. Register in `get_reporter()` factory in `src/pr_risk_scorer/output/__init__.py`

### Adding a New CLI Command

1. Create function in `src/pr_risk_scorer/cli.py`:
```python
@app.command()
def my_command(...):
    """Help text."""
    # Implementation
```

Typer automatically adds to CLI.

---

## Testing Strategy

```
Unit Tests (80% of suite)
├─ Analyzer logic (test_analyzers/*.py)
├─ Scoring logic (test_scoring/*.py)
├─ Config loading (test_config.py)
└─ Output formatters (test_output/*.py)

Integration Tests (15% of suite)
├─ CLI commands (test_cli.py)
├─ GitHub client (test_github_client.py, mocked)
└─ End-to-end flows

Mock Strategy:
├─ GitHub API: Mock via pytest-mock
├─ File I/O: Temporary directories
└─ Real data: Example PRData fixtures in conftest.py

Coverage Target: 100% line coverage
```

---

**Last Updated**: 2026-02-18
**Architecture Version**: 0.1.0
**Status**: Stable
