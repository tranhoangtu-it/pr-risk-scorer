# PR Risk Scorer

Analyze GitHub PRs and predict failure likelihood post-merge.

## Installation

```bash
pip install pr-risk-scorer
```

For development:
```bash
git clone https://github.com/your-org/pr-risk-scorer.git
cd pr-risk-scorer
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
# Analyze a single PR
pr-risk-scorer analyze owner/repo --pr 123

# Output as JSON (for CI/CD)
pr-risk-scorer analyze owner/repo --pr 123 --output json

# Output as Markdown (for PR comments)
pr-risk-scorer analyze owner/repo --pr 123 --output markdown

# Generate report for recent PRs
pr-risk-scorer report owner/repo --since 2026-01-01

# Initialize config
pr-risk-scorer config
```

## Configuration

Run `pr-risk-scorer config` to create `.pr-risk-scorer.yaml` with defaults.

Set `GITHUB_TOKEN` environment variable for authentication.

## Risk Levels

| Level | Score Range | Meaning |
|-------|-----------|---------|
| LOW | 0-24 | Safe to merge |
| MEDIUM | 25-49 | Review recommended |
| HIGH | 50-74 | Careful review required |
| CRITICAL | 75-100 | High failure risk |

## Analyzers

- **Blast Radius**: Files changed, LOC delta, module spread
- **Hot Path**: Commit churn, file diversity
- **Ownership**: Cross-domain changes
- **Dependency**: Package file changes
- **Review**: Review coverage and quality
- **Complexity**: Code nesting, conditionals, loops
