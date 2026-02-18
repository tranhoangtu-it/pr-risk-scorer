# PR Risk Scorer

Analyze GitHub PRs and predict failure likelihood post-merge. Score PRs on a 0-100 scale using 6 specialized risk analyzers.

**Status**: v0.1.0 Beta | **Coverage**: 100% (111 tests) | **License**: MIT

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

# Output as JSON (for CI/CD)
pr-risk-scorer analyze owner/repo --pr 123 --output json

# Batch analyze recent PRs
pr-risk-scorer report owner/repo --since 2026-01-01 --limit 20

# Generate custom config
pr-risk-scorer config
```

## Risk Levels

| Level | Score | Meaning |
|-------|-------|---------|
| LOW | 0-24 | Safe to merge |
| MEDIUM | 25-49 | Review recommended |
| HIGH | 50-74 | Careful review required |
| CRITICAL | 75-100 | High failure risk |

## Core Analyzers

6 specialized analyzers examine different risk dimensions:

- **Blast Radius**: Impact scope (files changed, LOC, modules)
- **Hot Path**: Code volatility (commit frequency, churn)
- **Complexity**: Code quality (nesting, conditionals, loops)
- **Ownership**: Organizational risk (cross-domain changes)
- **Dependency**: Dependency changes (package files, imports)
- **Review**: Review coverage (approvals, reviewers)

## Development Setup

### Prerequisites
- Python 3.10+
- pip or pipenv
- GitHub token (for API access)

### Local Installation

```bash
git clone https://github.com/tranhoangtu-it/pr-risk-scorer.git
cd pr-risk-scorer
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest -v

# With coverage
pytest --cov=src/pr_risk_scorer --cov-report=term-missing

# Run specific test file
pytest tests/test_cli.py -v
```

### Code Quality

```bash
# Lint code
ruff check src/ tests/

# Auto-format
ruff format src/ tests/

# Type check (optional)
mypy src/pr_risk_scorer
```

## Architecture Overview

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

**Key Components**:
- **CLI**: Typer-based interface with 3 commands
- **Analyzers**: Strategy pattern, 6 independent risk engines
- **Scoring**: Weighted aggregation with confidence & hybrid amplification
- **Output**: Factory pattern, 3 formatters for different use cases

See [System Architecture](./docs/system-architecture.md) for detailed diagrams.

## Configuration

### Auto-Generate Config

```bash
pr-risk-scorer config
# Creates: .pr-risk-scorer.yaml
```

### Example Config

```yaml
github_token: null  # Set via GITHUB_TOKEN env var
analyzers:
  blast_radius:
    enabled: true
    weight: 0.25
  hot_path:
    enabled: true
    weight: 0.20
  complexity:
    enabled: true
    weight: 0.15
  ownership:
    enabled: true
    weight: 0.15
  dependency:
    enabled: true
    weight: 0.15
  review:
    enabled: true
    weight: 0.10
output_format: terminal
risk_thresholds:
  low: 25
  medium: 50
  high: 75
```

### Configuration Priority

1. Command-line `--config /path/to/config.yaml`
2. Current directory `.pr-risk-scorer.yaml`
3. Environment variable `GITHUB_TOKEN`
4. Built-in defaults

## CI/CD Integration

### GitHub Actions Example

```yaml
name: PR Risk Assessment

on: [pull_request]

jobs:
  risk-score:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - run: pip install pr-risk-scorer

      - run: |
          pr-risk-scorer analyze \
            ${{ github.repository }} \
            --pr ${{ github.event.pull_request.number }} \
            --output json > risk-report.json

      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('risk-report.json'));
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## PR Risk Score: ${report.overall_score}\n\nLevel: **${report.risk_level.toUpperCase()}**`
            });
```

## Documentation

- [Project Overview & PDR](./docs/project-overview-pdr.md) - Goals, requirements, design
- [Code Standards](./docs/code-standards.md) - Naming, patterns, testing standards
- [System Architecture](./docs/system-architecture.md) - Components, data flow, design patterns
- [Codebase Summary](./docs/codebase-summary.md) - Module reference, dependencies
- [Project Roadmap](./docs/project-roadmap.md) - Planned features, timeline, vision

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/your-feature`)
3. Write tests (maintain 100% coverage)
4. Run linter & tests (`ruff check . && pytest`)
5. Commit with conventional format (`feat:`, `fix:`, `docs:`)
6. Submit pull request

**Code of Conduct**: Be respectful, inclusive, constructive.

## License

MIT License - See LICENSE file for details

## Support

- **Issues**: [GitHub Issues](https://github.com/tranhoangtu-it/pr-risk-scorer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tranhoangtu-it/pr-risk-scorer/discussions)
- **Email**: [email@tuth.site]

## Roadmap

- **v0.1.0** (Current): Core scoring engine, 6 analyzers, CLI ✓
- **v0.2.0** (Q1 2026): Caching, parallel analyzers, GraphQL support
- **v0.3.0** (Q2 2026): Multi-language support, trend tracking, ML tuning
- **v0.4.0** (Q3 2026): GitHub Actions, Slack, webhooks
- **v0.5.0** (Q4 2026): RBAC, audit logging, plugin system

See [Full Roadmap](./docs/project-roadmap.md) for details.

---

**Made with ❤️ by the Tran Hoang Tu**
