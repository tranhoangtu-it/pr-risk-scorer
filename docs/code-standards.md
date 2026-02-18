# PR Risk Scorer - Code Standards & Style Guide

## Python Language Standards

### Version & Environment
- **Minimum Python**: 3.10+
- **Type Hints**: Required on all functions & methods
- **Linter**: Ruff (configuration in pyproject.toml)
- **Testing**: pytest with 100% coverage requirement
- **Virtual Environment**: Use `.venv` for local development

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | snake_case | `github_client.py`, `weighted_scorer.py` |
| Classes | PascalCase | `BlastRadiusAnalyzer`, `RiskScore` |
| Functions | snake_case | `fetch_pr_data()`, `level_from_score()` |
| Constants | UPPER_SNAKE_CASE | `MAX_NESTING_DEPTH`, `DEFAULT_WEIGHT` |
| Variables | snake_case | `pr_number`, `total_loc` |
| Private members | _leading_underscore | `_github`, `_fetch_blame_data()` |
| Enum members | UPPER_SNAKE_CASE | `RiskLevel.CRITICAL` |

### Type Hints

**Required on all public APIs:**
```python
# Good
def analyze(self, pr_data: PRData) -> AnalyzerResult:
    """Analyze PR data and return risk assessment."""
    score: float = self._calculate_score(pr_data)
    return AnalyzerResult(analyzer_name=self.name, score=score)

# Bad (missing types)
def analyze(self, pr_data):
    score = self._calculate_score(pr_data)
    return AnalyzerResult(analyzer_name=self.name, score=score)
```

**Union types:**
```python
# Good (Python 3.10+)
config: Path | None = None
data: dict[str, int] = {}

# Avoid (Python 3.9 compatibility)
from typing import Optional, Dict
config: Optional[Path] = None
data: Dict[str, int] = {}
```

### Docstring Format

Use Google-style docstrings with type info:
```python
def fetch_pr_data(self, owner: str, repo: str, pr_num: int) -> PRData:
    """Fetch PR metadata, files, reviews from GitHub API.

    Args:
        owner: Repository owner (e.g., 'torvalds')
        repo: Repository name (e.g., 'linux')
        pr_num: Pull request number

    Returns:
        PRData object with all PR information

    Raises:
        GitHubClientError: If API request fails
    """
    # Implementation
```

---

## Code Organization & Structure

### Module Purpose Pattern

Each module should have a clear, single responsibility:

| Module | Responsibility | Example |
|--------|---|---|
| `models.py` | Data models only (Pydantic) | Define all request/response shapes |
| `cli.py` | CLI commands & user interaction | Parse args, format output, exit codes |
| `config.py` | Configuration loading & defaults | YAML parsing, Pydantic config models |
| `github_client.py` | External API integration | GitHub API wrapper, error handling |
| `analyzers/*.py` | Domain logic (risk analysis) | Score calculation, metrics |
| `scoring/*.py` | Aggregation logic | Combine analyzer results |
| `output/*.py` | Output formatting | Terminal, JSON, Markdown |

### Class Organization

Order class members as:
1. **Class variables** (constants)
2. **`__init__` method**
3. **Public methods** (alphabetical)
4. **Private methods** (alphabetical, prefixed with `_`)

```python
class BlastRadiusAnalyzer(BaseAnalyzer):
    """Analyzer for PR scope impact."""

    # Class constant
    name = "blast_radius"

    def __init__(self):
        """Initialize analyzer."""
        pass

    # Public methods (alphabetical)
    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        """Analyze and return result."""
        pass

    # Private methods
    def _calculate_files_score(self, count: int) -> float:
        """Helper for file-based scoring."""
        pass
```

---

## Error Handling

### Custom Exceptions

Define domain-specific exceptions:
```python
class GitHubClientError(Exception):
    """Raised when GitHub API call fails."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass
```

### Error Handling Pattern

```python
# Good: Specific exception, user-friendly message
try:
    repository = client._github.get_repo(f"{owner}/{repo}")
except Exception as e:
    console.print(f"[red]GitHub Error: {e}[/red]")
    raise typer.Exit(code=1)

# Bad: Silent failures
try:
    repository = client._github.get_repo(f"{owner}/{repo}")
except:
    pass  # Swallows error
```

### CLI Error Codes

- `0`: Success
- `1`: User error (invalid args, missing config)
- `2`: System error (API failure, file I/O)

```python
def analyze(...):
    try:
        # Implementation
    except GitHubClientError as e:
        console.print(f"[red]GitHub Error: {e}[/red]")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
```

---

## Testing Standards

### Test File Location & Naming
- Source: `src/pr_risk_scorer/{module}.py`
- Tests: `tests/test_{module}.py` or `tests/test_{category}/test_{module}.py`
- Fixture data: `tests/conftest.py`

### Test Naming Convention
```python
# Good: Describes scenario and expected outcome
def test_analyze_returns_score_between_0_and_100():
    pass

def test_blast_radius_with_20_files_scores_50():
    pass

def test_config_load_missing_file_returns_defaults():
    pass

# Bad: Unclear what's being tested
def test_analyze():
    pass

def test_blast_radius():
    pass
```

### Test Structure (Arrange-Act-Assert)

```python
def test_weighted_scorer_amplifies_when_two_high_scores():
    # Arrange
    result1 = AnalyzerResult(analyzer_name="blast_radius", score=75.0, confidence=1.0)
    result2 = AnalyzerResult(analyzer_name="complexity", score=80.0, confidence=1.0)
    scorer = WeightedScorer()

    # Act
    risk_score = scorer.score([result1, result2])

    # Assert
    assert risk_score.overall_score > 75.0  # Amplified beyond 75
```

### Mocking Pattern

Use pytest-mock for external dependencies:
```python
def test_fetch_pr_data_handles_404(mocker):
    # Mock GitHub API to return 404
    mock_github = mocker.Mock()
    mock_github.get_repo.side_effect = Exception("404 Not Found")

    client = GitHubClient()
    client._github = mock_github

    with pytest.raises(GitHubClientError):
        client.fetch_pr_data("owner", "repo", 999)
```

### Coverage Requirements
- **Minimum**: 100% line coverage
- **Tests must pass**: `pytest --cov=src/pr_risk_scorer --cov-report=term-missing`
- **CI/CD enforces**: No merge without 100% coverage

---

## Code Quality Standards

### Complexity Limits

| Metric | Limit | Reason |
|--------|-------|--------|
| File size | 200 LOC | Readability, single responsibility |
| Function length | 50 LOC | Easier to test and understand |
| Function parameters | 5 max | Reduce cognitive load |
| Nesting depth | 3 levels | Avoid deeply nested logic |
| Cyclomatic complexity | 10 max | Test coverage becomes difficult |

### Ruff Configuration

Enforced linting rules in `pyproject.toml`:
```toml
[tool.ruff]
line-length = 120
target-version = "py310"
select = ["E", "F", "W", "I"]  # Errors, flakes, warnings, imports
```

Run linter before commit:
```bash
ruff check src/ tests/
ruff format src/ tests/  # Auto-fix formatting
```

### No Magic Numbers

```python
# Good: Named constants
MIN_WEIGHT = 0.0
MAX_WEIGHT = 1.0
DEFAULT_WEIGHT = 0.15

# Bad: Unexplained numbers
if weight < 0.0 or weight > 1.0:
    raise ValueError("Weight must be 0-1")
```

---

## Common Patterns

### Pydantic Model Pattern

```python
from pydantic import BaseModel, Field

class AnalyzerResult(BaseModel):
    """Result from a single analyzer."""

    analyzer_name: str
    score: float = Field(ge=0.0, le=100.0)  # Validation
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    details: dict = Field(default_factory=dict)  # Mutable default
    recommendations: list[str] = Field(default_factory=list)
```

**Rules**:
- Use `Field()` for validation & defaults
- Use `default_factory` for mutable defaults (dict, list)
- Never use mutable defaults: `score: dict = {}`
- Validate range constraints in Field

### Strategy Pattern (Analyzers)

```python
class BaseAnalyzer(ABC):
    """Abstract base for all risk analyzers."""
    name: str = "base"

    @abstractmethod
    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        """Analyze PR data and return risk assessment."""
        ...

class BlastRadiusAnalyzer(BaseAnalyzer):
    name = "blast_radius"

    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        # Implementation
        pass
```

**Registry Pattern**:
```python
# analyzers/__init__.py
ALL_ANALYZERS = [
    BlastRadiusAnalyzer,
    HotPathAnalyzer,
    ComplexityAnalyzer,
    OwnershipAnalyzer,
    DependencyAnalyzer,
    ReviewAnalyzer,
]
```

### Factory Pattern (Output)

```python
def get_reporter(format: str) -> BaseReporter:
    """Get reporter instance for output format."""
    reporters = {
        "terminal": TerminalReporter,
        "json": JSONReporter,
        "markdown": MarkdownReporter,
    }
    reporter_cls = reporters.get(format)
    if not reporter_cls:
        raise ValueError(f"Unknown format: {format}")
    return reporter_cls()
```

---

## Configuration & Secrets

### Config Pattern

Use Pydantic models with YAML serialization:
```python
class ScorerConfig(BaseModel):
    github_token: str | None = None
    analyzers: dict[str, AnalyzerConfig] = Field(default_factory=dict)
    output_format: str = "terminal"

    @classmethod
    def load(cls, path: Path | None = None) -> "ScorerConfig":
        if path is None:
            path = Path(".pr-risk-scorer.yaml")
        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()
```

### Secrets Handling

**DO NOT commit secrets** (.env files, tokens, etc):
```python
# Good: Read from environment
token = os.getenv("GITHUB_TOKEN")

# Good: Allow config file (user responsible for security)
config = ScorerConfig.load(Path(".pr-risk-scorer.yaml"))

# Bad: Hardcoded token
TOKEN = "ghp_xxxxxxxxxxxxx"
```

---

## Development Workflow

### Before Committing

```bash
# 1. Run linter
ruff check src/ tests/
ruff format src/ tests/

# 2. Run tests
pytest -v --cov=src/pr_risk_scorer --cov-report=term-missing

# 3. Verify coverage is 100%
# 4. Check for type errors (optional, using mypy)
mypy src/pr_risk_scorer

# 5. Commit with conventional format
git add .
git commit -m "feat: add blast radius analyzer"
```

### Conventional Commit Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`
Examples:
- `feat(analyzers): add complexity analyzer`
- `fix(cli): handle missing GitHub token gracefully`
- `docs: update code standards`
- `test(blast-radius): increase coverage to 100%`
- `chore(deps): upgrade pytest to 7.4.0`

---

## Performance Considerations

### Scoring Algorithm Efficiency

Current: O(n) where n = number of files in PR
- 1000 files: ~100ms per analyzer
- Total 6 analyzers: ~600ms (acceptable)

Optimization if needed:
- Parallelize analyzers using `concurrent.futures.ThreadPoolExecutor`
- Cache file complexity metrics if re-analyzing same PR
- Lazy-load blame data only if OwnershipAnalyzer enabled

### API Call Optimization

Current: 1 PR fetch + optional blame data
- Typical: 1-2s per PR (dominated by GitHub API)

Optimization if needed:
- Add Redis caching for repeat analyses (cache key = repo+PR number)
- Batch API calls using GitHub GraphQL (fewer requests)
- Pre-calculate complexity metrics for frequently-analyzed repos

---

## Security & Compliance

### Code Review Checklist

Before merging, verify:
- [ ] All tests pass (100% coverage)
- [ ] Linter passes (`ruff check`)
- [ ] No hardcoded secrets or tokens
- [ ] Type hints on all public APIs
- [ ] Docstrings on public functions
- [ ] Error handling with user-friendly messages
- [ ] No external network calls except GitHub
- [ ] Dependencies pinned in pyproject.toml

### Input Validation

All user inputs validated via Pydantic:
```python
# CLI args auto-validated by Typer
@app.command()
def analyze(
    repo: str = typer.Argument(...),  # Required
    pr: int = typer.Option(..., "--pr"),  # Required
):
    # repo & pr already validated by typer
    pass

# Config validation
config = ScorerConfig.load(path)  # Pydantic validates structure
```

---

## Documentation Requirements

### Code Comments

Prefer self-documenting code, but explain "why" not "what":
```python
# Bad: Obvious what code does
x = y + 1  # Add 1 to y

# Good: Explains why
# Amplify score if multiple analyzers flagged risk (15% per analyzer)
amplifier = 1.0 + (0.15 * high_count)

# Good: Complex algorithm explanation
# Hybrid amplification detects consensus risk: if 2+ analyzers score >70,
# their agreement increases confidence in the risk prediction
```

### Module Docstrings

All modules start with docstring:
```python
"""BlastRadiusAnalyzer: Measures PR impact based on files changed, LOC, and modules.

This analyzer scores PRs based on the breadth (files, modules) and depth (LOC)
of changes, identifying large-impact PRs that deserve careful review.
"""
```

### README & Guides

- Keep README under 300 lines (link to detailed docs in `/docs`)
- Usage examples with common scenarios
- Configuration guide with YAML examples
- Troubleshooting section

---

**Last Updated**: 2026-02-18
**Version**: 0.1.0
**Status**: Active Development
