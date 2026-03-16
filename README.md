# pr-risk-scorer

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub_API-181717?style=flat-square&logo=github&logoColor=white)

GitHub PR analyzer that scores the failure risk of pull requests (0–100) using 6 specialized analysis modules.

## Risk Analyzers

| Module | What It Checks |
|--------|---------------|
| Code Quality | Complexity, code smells, anti-patterns |
| Test Coverage | Missing or insufficient tests |
| Merge Safety | Conflict potential, base branch drift |
| File Scope | Number and spread of changed files |
| Review Status | Reviewer assignments and approvals |
| History | Author's past merge success rate |

## Installation

```bash
pip install pr-risk-scorer
```

## Usage

```bash
# Score a PR
pr-risk-scorer analyze owner/repo 123

# Output JSON report
pr-risk-scorer analyze owner/repo 123 --format json
```

## Example Output

```
PR #123: Add user authentication
Risk Score: 67/100 (Medium-High)

  Code Quality:  72  ██████████░░
  Test Coverage:  45  ████████░░░░
  Merge Safety:   80  ██████████░░
  File Scope:     55  █████████░░░
```

## Tech Stack

- **CLI**: Typer
- **API**: GitHub REST API
- **Analysis**: Custom risk scoring engine

## License

See [LICENSE](./LICENSE) for details.
