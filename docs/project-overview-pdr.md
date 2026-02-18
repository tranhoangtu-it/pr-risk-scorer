# PR Risk Scorer - Project Overview & Product Requirements

## Executive Summary

**PR Risk Scorer** is a Python CLI tool that analyzes GitHub pull requests and predicts post-merge failure likelihood through comprehensive risk assessment. It scores PRs on a 0-100 scale categorized into risk levels (LOW/MEDIUM/HIGH/CRITICAL), enabling teams to identify risky changes before merging.

**Target Users**: Engineering teams, DevOps/SRE, project managers, code review leads
**Primary Use**: Pre-merge risk evaluation, CI/CD pipeline integration, team dashboards
**Success Metric**: Teams reduce production incidents from risky PRs by 30-40%

## Product Requirements

### Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| FR-1 | Analyze single PR and generate risk score (0-100) | Complete |
| FR-2 | Generate batch reports for recent merged PRs | Complete |
| FR-3 | Support 6+ analyzers for multi-dimensional risk assessment | Complete |
| FR-4 | Provide configurable weights for each analyzer | Complete |
| FR-5 | Support multiple output formats (terminal, JSON, Markdown) | Complete |
| FR-6 | Integrate with GitHub API for data collection | Complete |
| FR-7 | Cache configuration via YAML config file | Complete |
| FR-8 | Environment variable support for GitHub token | Complete |

### Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-1 | Code coverage | 100% |
| NFR-2 | Supported Python versions | 3.10+ |
| NFR-3 | Maximum API response time | <2s per PR |
| NFR-4 | Configuration file format | YAML |
| NFR-5 | Test suite | 111 tests, fully automated |
| NFR-6 | Package distribution | PyPI, pip-installable |
| NFR-7 | CLI framework | Typer with Rich terminal output |

## Feature Overview

### Risk Analysis Engine
6 specialized analyzers examine different dimensions:
- **Blast Radius**: File count, LOC changes, module spread
- **Hot Path**: Commit frequency, code churn, patch volatility
- **Complexity**: Nesting depth, conditionals, loops, line length
- **Ownership**: Cross-domain changes, organizational complexity
- **Dependency**: Dependency file modifications, import complexity
- **Review**: Review coverage, approval ratios, review quality

### Scoring System
- **Weighted Aggregation**: Configurable per-analyzer weights (sum to 1.0)
- **Confidence Adjustment**: Scores multiplied by analyzer confidence (0-1)
- **Hybrid Amplification**: Boosts when 2+ analyzers score >70
- **Risk Level Mapping**:
  - LOW (0-24): Safe to merge
  - MEDIUM (25-49): Review recommended
  - HIGH (50-74): Careful review required
  - CRITICAL (75-100): High failure risk

### Configuration System
Users customize risk assessment via `.pr-risk-scorer.yaml`:
- Enable/disable analyzers
- Adjust per-analyzer weights
- Set risk thresholds
- Configure output format
- GITHUB_TOKEN env var support

## User Workflows

### Workflow 1: Pre-Merge Risk Check
```
Developer finishes PR → Run 'pr-risk-scorer analyze' → Review score
If HIGH/CRITICAL: Investigate findings, modify code → Re-score
If LOW/MEDIUM: Proceed to review
```

### Workflow 2: Batch Risk Reporting
```
Weekly job → Run 'pr-risk-scorer report --since YYYY-MM-DD'
Output: Dashboard with merged PR risk trends
Use: Identify patterns in risky PRs, adjust team practices
```

### Workflow 3: CI/CD Integration
```
PR created → CI trigger 'pr-risk-scorer analyze' (JSON output)
Parser: Extract score, reject if CRITICAL
Reviewer: Gets recommendation context before review
```

## Architecture & Design Patterns

### Strategy Pattern (Analyzers)
Each analyzer implements BaseAnalyzer interface:
```
BaseAnalyzer (ABC)
├── BlastRadiusAnalyzer
├── HotPathAnalyzer
├── ComplexityAnalyzer
├── OwnershipAnalyzer
├── DependencyAnalyzer
└── ReviewAnalyzer
```

### Factory Pattern (Output)
`get_reporter()` factory returns appropriate output formatter:
```
get_reporter(format) → TerminalReporter | JSONReporter | MarkdownReporter
```

### Configuration as Code
YAML config enables customization without code changes:
```yaml
analyzers:
  blast_radius:
    enabled: true
    weight: 0.25
  complexity:
    enabled: true
    weight: 0.15
risk_thresholds:
  low: 25
  medium: 50
  high: 75
```

## Acceptance Criteria

### Code Quality
- [x] 111 tests with 100% coverage
- [x] All tests passing
- [x] Ruff linting compliant
- [x] No security vulnerabilities
- [x] Modular, well-documented code

### Feature Completeness
- [x] All 6 analyzers implemented
- [x] Weighted scoring with amplification
- [x] Terminal, JSON, Markdown output
- [x] YAML configuration system
- [x] GitHub API integration
- [x] CLI with 3 commands (analyze, report, config)

### Documentation
- [x] README with installation & usage
- [x] Configuration guide
- [x] API/analyzer documentation
- [x] Example outputs

### Deployment
- [x] Installable via pip
- [x] Package on PyPI
- [x] Automated CI/CD pipeline
- [x] Pre-commit/push validation

## Known Limitations & Future Work

| Limitation | Impact | Planned Fix |
|---|---|---|
| No caching of GitHub API results | Repeat analyses slow | Redis cache layer |
| Single-language complexity detection (Python-biased) | Limited for polyglot repos | Language-agnostic AST analysis |
| No historical trend tracking | Can't detect regressions | Time-series database |
| No custom analyzer plugins | Extensibility limited to code changes | Plugin system via entry points |
| Risk thresholds static | One-size-fits-all model | ML-based threshold tuning |

## Success Metrics

| Metric | Target | Measurement |
|---|---|---|
| Installation ease | <5 min setup | First-time user tests |
| Output clarity | Instant understanding | User feedback, task completion |
| Score accuracy | Detect 80% of risky PRs | Post-merge incident correlation |
| Configuration flexibility | Teams customize 3+ params | Config adoption survey |
| Performance | <2s per PR analysis | Benchmark suite |

## Security Considerations

- GitHub token stored locally in `.pr-risk-scorer.yaml` (user responsibility)
- Env var `GITHUB_TOKEN` preferred for CI/CD
- No data persistence (stateless analysis)
- No external API calls except GitHub
- Input validation via Pydantic models
- All dependencies pinned in pyproject.toml

## Support & Maintenance

| Item | Details |
|---|---|
| Documentation | Maintained in `/docs` directory |
| Issue tracking | GitHub Issues |
| Versioning | Semantic versioning (0.x.y for beta) |
| Testing | CI/CD via GitHub Actions |
| Releases | Manual tagging + auto-PyPI push |

---

**Last Updated**: 2026-02-18
**Version**: 0.1.0 (Beta)
**Status**: Active Development
