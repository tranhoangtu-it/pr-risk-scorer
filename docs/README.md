# Documentation Hub - PR Risk Scorer

Welcome to the comprehensive documentation for PR Risk Scorer v0.1.0.

## Quick Navigation

### For Users & Getting Started
- **[README.md](../README.md)** - Installation, usage, quick start, CI/CD examples

### For Understanding the Project
- **[project-overview-pdr.md](./project-overview-pdr.md)** - Goals, requirements, product definition
  - Why this project exists
  - What problems it solves
  - Success metrics & acceptance criteria
  - Risk levels & scoring model

### For Technical Details
- **[system-architecture.md](./system-architecture.md)** - Architecture, data flow, design patterns
  - High-level system diagram
  - Component interaction
  - Analyzer architecture
  - Scoring algorithm (detailed)
  - Extensibility points
  
- **[codebase-summary.md](./codebase-summary.md)** - Module reference, dependencies
  - Directory structure with LOC counts
  - Every module documented
  - File purposes & responsibilities
  - Dependency graph
  - Performance characteristics

### For Development
- **[code-standards.md](./code-standards.md)** - Coding conventions, patterns, testing
  - Naming conventions (Python standards)
  - Type hints requirements
  - Error handling patterns
  - Testing standards (Arrange-Act-Assert)
  - Code quality limits
  - Pre-commit checklist

### For Planning & Future Work
- **[project-roadmap.md](./project-roadmap.md)** - Planned features, timeline, vision
  - Current status v0.1.0 Beta
  - v0.2.0 - v0.5.0 planned releases
  - Timeline (Q1-Q4 2026)
  - Known issues & technical debt
  - Long-term vision (3 product tiers)

---

## Key Facts About PR Risk Scorer

| Aspect | Details |
|--------|---------|
| **Purpose** | Analyze GitHub PRs, predict failure risk (0-100 score) |
| **Language** | Python 3.10+ |
| **Build** | Hatchling, distributable via pip |
| **Testing** | pytest, 111 tests, 100% coverage |
| **Size** | 1,175 LOC source, 2,294 LOC tests |
| **Risk Levels** | LOW (0-24), MEDIUM (25-49), HIGH (50-74), CRITICAL (75-100) |
| **Analyzers** | 6 independent risk assessment engines |
| **Output Formats** | Terminal (Rich), JSON, Markdown |
| **Configuration** | YAML-driven, customizable weights |

---

## Analyzer Overview

| Analyzer | Focus | Metrics |
|----------|-------|---------|
| **Blast Radius** | Impact scope | Files, LOC, modules affected |
| **Hot Path** | Code volatility | Commit frequency, churn, patch size |
| **Complexity** | Code quality | Nesting depth, conditionals, loops |
| **Ownership** | Organizational risk | Cross-domain changes, depth |
| **Dependency** | Dependency changes | Package files, import changes |
| **Review** | Review coverage | Approvals, reviewers, quality |

---

## Quick Start

### Installation
```bash
pip install pr-risk-scorer
export GITHUB_TOKEN=ghp_your_token_here
```

### Usage
```bash
# Analyze a single PR
pr-risk-scorer analyze owner/repo --pr 123

# Generate batch report
pr-risk-scorer report owner/repo --since 2026-01-01

# Initialize config
pr-risk-scorer config
```

### Output Example (Terminal)
```
╭──────────────────────────────────────────╮
│ Risk Score: 65 (HIGH)                   │
│ Rollback Probability: 52.0%             │
├──────────────────────────────────────────┤
│ Blast Radius:        45 (Moderate)      │
│ Hot Path:            72 (High)          │
│ Complexity:          80 (High)          │
│ Ownership:           50 (Medium)        │
│ Dependency:          30 (Low)           │
│ Review:              42 (Medium)        │
├──────────────────────────────────────────┤
│ Recommendations:                         │
│ • Consider splitting this PR            │
│ • Ensure 2+ reviewers                   │
╰──────────────────────────────────────────╯
```

---

## Architecture at a Glance

```
CLI (analyze/report/config)
    ↓
GitHub Client (fetch PR data) + Config Loader
    ↓
Analyzer Pipeline (6 parallel analyzers)
    ↓
Weighted Scoring Engine (aggregation + amplification)
    ↓
Output Formatters (terminal, JSON, Markdown)
```

See [system-architecture.md](./system-architecture.md) for detailed diagrams and data flow.

---

## Development Setup

### Prerequisites
- Python 3.10+
- pip or pipenv
- GitHub token (GITHUB_TOKEN env var)

### Installation
```bash
git clone https://github.com/your-org/pr-risk-scorer.git
cd pr-risk-scorer
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Testing
```bash
pytest -v                                    # Run all tests
pytest --cov                                 # With coverage
ruff check src/ tests/                       # Lint
ruff format src/ tests/                      # Format
```

---

## Code Quality Standards

### Enforcement
- **Linter**: Ruff (line-length 120, Python 3.10+)
- **Testing**: pytest, 100% coverage required
- **Type Hints**: Required on all public APIs
- **Naming**: PascalCase classes, snake_case functions/variables
- **File Size**: Max 200 LOC per file (for modules)
- **Function Complexity**: Max cyclomatic complexity 10

### Patterns Used
- **Strategy Pattern**: Analyzers (BaseAnalyzer ABC)
- **Factory Pattern**: Output formatters (get_reporter)
- **Configuration as Code**: YAML Pydantic models

See [code-standards.md](./code-standards.md) for complete guidelines.

---

## Documentation Size Compliance

All documentation files kept under 800 LOC (docs.maxLoc):

| File | Lines | Status |
|------|-------|--------|
| code-standards.md | 535 | ✓ Under limit |
| system-architecture.md | 493 | ✓ Under limit |
| project-roadmap.md | 356 | ✓ Under limit |
| codebase-summary.md | 310 | ✓ Under limit |
| project-overview-pdr.md | 198 | ✓ Under limit |
| README.md | 245 | ✓ Under limit |

**Total**: 2,137 lines across 6 files

---

## Roadmap Summary

| Version | Timeline | Focus |
|---------|----------|-------|
| **v0.1.0** (Current) | Released 2026-02-18 | Core engine, 6 analyzers, CLI |
| **v0.2.0** | Q1 2026 | Caching, parallel analyzers, GraphQL |
| **v0.3.0** | Q2 2026 | Multi-language, trends, ML tuning |
| **v0.4.0** | Q3 2026 | GitHub Actions, Slack, webhooks |
| **v0.5.0** | Q4 2026 | RBAC, audit, plugins |
| **v1.0.0** | 2027 | Stable API, enterprise features |

See [project-roadmap.md](./project-roadmap.md) for detailed roadmap.

---

## Contributing

1. **Fork** the repository
2. **Create branch** (`git checkout -b feature/your-feature`)
3. **Write tests** (maintain 100% coverage)
4. **Run linter** (`ruff check . && pytest`)
5. **Commit** with conventional format (`feat:`, `fix:`)
6. **Submit PR**

See [code-standards.md](./code-standards.md) for detailed contributing guidelines.

---

## Module Organization

```
src/pr_risk_scorer/
├── analyzers/          # 6 risk analyzers (Strategy pattern)
├── output/             # Output formatters (Factory pattern)
├── scoring/            # Weighted scoring engine
├── cli.py              # CLI interface (Typer)
├── config.py           # Configuration system (YAML)
├── github_client.py    # GitHub API wrapper
└── models.py           # Pydantic data models

tests/
├── test_analyzers/     # 40+ analyzer tests
├── test_output/        # Output formatter tests
├── test_scoring/       # Scoring algorithm tests
└── test_*.py           # CLI, config, GitHub client tests
```

See [codebase-summary.md](./codebase-summary.md) for complete module reference.

---

## Key Decisions

### Why These 6 Analyzers?
- **Blast Radius**: Measures PR scope (high correlation with bugs)
- **Hot Path**: Identifies volatile code (hard to maintain)
- **Complexity**: Evaluates code quality (nesting, conditionals)
- **Ownership**: Organizational risk (unfamiliar code domains)
- **Dependency**: Flags infrastructure changes (high impact)
- **Review**: Ensures adequate review coverage

### Why Weighted Aggregation?
- Flexible per-team customization
- Different repos need different weights
- Confidence adjustment accounts for analyzer reliability

### Why Hybrid Amplification?
- When 2+ analyzers flag HIGH risk, agreement increases confidence
- Reduces false positives from single analyzer
- Boosts score when consensus exists

---

## FAQ

### Q: How often should I run risk analysis?
A: Before merge. Use GitHub Actions to auto-trigger on PRs.

### Q: Can I customize weights?
A: Yes! Edit `.pr-risk-scorer.yaml` or pass `--config` option.

### Q: What does "Rollback Probability" mean?
A: Estimated likelihood this PR will need rollback post-merge (0-80%).

### Q: How is the overall score calculated?
A: Weighted average of 6 analyzer scores, adjusted by confidence, amplified if multiple HIGH scores.

### Q: Can I add custom analyzers?
A: In v0.1.0, extend BaseAnalyzer. In v0.5.0, plugin system planned.

### Q: Is my code data sent anywhere?
A: No. Only fetched from GitHub API, analyzed locally, no persistence.

See [project-overview-pdr.md](./project-overview-pdr.md) for more FAQs.

---

## Performance & Scalability

| Metric | Typical | Target |
|--------|---------|--------|
| Single PR analysis | 200-500ms | <200ms (v0.2.0) |
| Batch (10 PRs) | 5-10s | <2s (v0.2.0) |
| Repeat analysis | 200-500ms | <100ms (v0.2.0 cached) |
| Config load | <10ms | <10ms ✓ |
| Output format | <10ms | <10ms ✓ |

Optimization planned for v0.2.0 (caching + parallelization).

---

## Support & Resources

- **Issues**: [GitHub Issues](https://github.com/your-org/pr-risk-scorer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/pr-risk-scorer/discussions)
- **Email**: your-email@example.com
- **Documentation**: This hub + individual docs

---

## License

MIT License - See [LICENSE](../LICENSE) file

---

**Generated**: 2026-02-18
**Documentation Version**: 0.1.0
**Status**: Complete & Ready for v0.1.0 Release
