# Phase 01: Project Setup & Core Foundation

## Context Links
- [Research: Risk Algorithms](./research/researcher-260218-1858-pr-risk-algorithms.md)
- [Research: Tech Architecture](./research/researcher-260218-1858-tech-architecture.md)
- [Plan Overview](./plan.md)

## Parallelization Info
- **Execution**: SEQUENTIAL -- must complete before all other phases
- **Blocked by**: none
- **Blocks**: Phases 02, 03, 04, 05, 06, 07

## Overview
- **Priority**: P1 (Critical Path)
- **Status**: pending
- **Effort**: 1.5h
- **Description**: Bootstrap Python project with pyproject.toml, create all shared data models, config system, and abstract base class that all subsequent phases depend on.

## Key Insights
- All analyzers share `PRData` input and `AnalyzerResult` output -- these contracts must be stable
- Pydantic v2 provides validation + YAML config loading natively
- Base analyzer ABC defines the interface all 6 analyzers implement
- Risk thresholds: <25 Low, 25-50 Medium, 50-75 High, >75 Critical

## Requirements

### Functional
- Python package installable via `pip install -e .`
- All data models with Pydantic validation
- YAML config loading with defaults
- Abstract base analyzer class

### Non-functional
- Python 3.10+ compatibility
- Type hints on all public APIs
- Models must be importable without side effects

## Architecture

```
pyproject.toml          -- package metadata, deps, entry point
src/pr_risk_scorer/
  __init__.py           -- version, package exports
  models.py             -- PRData, AnalyzerResult, RiskScore, RiskLevel, FileChange, ReviewData
  config.py             -- ScorerConfig (Pydantic), YAML loading, defaults
  analyzers/
    base_analyzer.py    -- BaseAnalyzer ABC
.pr-risk-scorer.yaml    -- default config template
```

## Related Code Files (EXCLUSIVE)

**Create:**
- `pyproject.toml`
- `src/pr_risk_scorer/__init__.py`
- `src/pr_risk_scorer/models.py`
- `src/pr_risk_scorer/config.py`
- `src/pr_risk_scorer/analyzers/__init__.py` -- empty, just makes it a package (NOTE: Phase 04 populates re-exports)
- `src/pr_risk_scorer/analyzers/base_analyzer.py`
- `.pr-risk-scorer.yaml`

**NOTE**: `src/pr_risk_scorer/analyzers/__init__.py` created here as empty file. Phase 04 owns re-export content.

## File Ownership
| File | Owner |
|------|-------|
| `pyproject.toml` | Phase 01 |
| `src/pr_risk_scorer/__init__.py` | Phase 01 |
| `src/pr_risk_scorer/models.py` | Phase 01 |
| `src/pr_risk_scorer/config.py` | Phase 01 |
| `src/pr_risk_scorer/analyzers/base_analyzer.py` | Phase 01 |
| `.pr-risk-scorer.yaml` | Phase 01 |

## Implementation Steps

### 1. Create pyproject.toml
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pr-risk-scorer"
version = "0.1.0"
description = "Analyze GitHub PRs and predict failure likelihood post-merge"
requires-python = ">=3.10"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "PyGithub>=2.0.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
]

[project.scripts]
pr-risk-scorer = "pr_risk_scorer.cli:app"

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.0.0",
    "pytest-cov>=4.0.0",
]
```

### 2. Create `src/pr_risk_scorer/__init__.py`
```python
"""PR Risk Scorer - Analyze GitHub PRs for failure risk prediction."""

__version__ = "0.1.0"
```

### 3. Create `src/pr_risk_scorer/models.py`

Define all shared data models:

```python
from enum import Enum
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    LOW = "low"          # 0-24
    MEDIUM = "medium"    # 25-49
    HIGH = "high"        # 50-74
    CRITICAL = "critical" # 75-100

class FileChange(BaseModel):
    filename: str
    additions: int = 0
    deletions: int = 0
    status: str = "modified"  # added, removed, modified, renamed
    patch: str | None = None

class ReviewData(BaseModel):
    reviewer: str
    state: str  # APPROVED, CHANGES_REQUESTED, COMMENTED
    submitted_at: str | None = None
    body: str | None = None

class PRData(BaseModel):
    """All data about a PR needed for analysis."""
    owner: str
    repo: str
    number: int
    title: str
    author: str
    base_branch: str = "main"
    head_branch: str = ""
    files: list[FileChange] = Field(default_factory=list)
    reviews: list[ReviewData] = Field(default_factory=list)
    commits_count: int = 0
    additions: int = 0
    deletions: int = 0
    created_at: str | None = None
    merged_at: str | None = None

class AnalyzerResult(BaseModel):
    """Output from a single analyzer."""
    analyzer_name: str
    score: float = Field(ge=0.0, le=100.0)  # 0-100
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    details: dict = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)

class RiskScore(BaseModel):
    """Aggregated risk assessment for a PR."""
    overall_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel
    analyzer_results: list[AnalyzerResult] = Field(default_factory=list)
    rollback_probability: float = Field(ge=0.0, le=1.0, default=0.0)
    recommendations: list[str] = Field(default_factory=list)
    pr_url: str = ""

    @staticmethod
    def level_from_score(score: float) -> RiskLevel:
        if score < 25: return RiskLevel.LOW
        if score < 50: return RiskLevel.MEDIUM
        if score < 75: return RiskLevel.HIGH
        return RiskLevel.CRITICAL
```

### 4. Create `src/pr_risk_scorer/config.py`

```python
from pathlib import Path
from pydantic import BaseModel, Field
import yaml

class AnalyzerConfig(BaseModel):
    enabled: bool = True
    weight: float = Field(ge=0.0, le=1.0)

class ScorerConfig(BaseModel):
    github_token: str | None = None
    analyzers: dict[str, AnalyzerConfig] = Field(default_factory=lambda: {
        "blast_radius": AnalyzerConfig(weight=0.25),
        "hot_path": AnalyzerConfig(weight=0.20),
        "complexity": AnalyzerConfig(weight=0.15),
        "ownership": AnalyzerConfig(weight=0.15),
        "dependency": AnalyzerConfig(weight=0.15),
        "review": AnalyzerConfig(weight=0.10),
    })
    output_format: str = "terminal"  # terminal, json, markdown
    risk_thresholds: dict[str, int] = Field(default_factory=lambda: {
        "low": 25, "medium": 50, "high": 75
    })

    @classmethod
    def load(cls, path: Path | None = None) -> "ScorerConfig":
        """Load config from YAML file, falling back to defaults."""
        if path is None:
            path = Path(".pr-risk-scorer.yaml")
        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()
```

### 5. Create `src/pr_risk_scorer/analyzers/base_analyzer.py`

```python
from abc import ABC, abstractmethod
from pr_risk_scorer.models import PRData, AnalyzerResult

class BaseAnalyzer(ABC):
    """Abstract base for all risk analyzers."""

    name: str = "base"

    @abstractmethod
    def analyze(self, pr_data: PRData) -> AnalyzerResult:
        """Analyze PR data and return risk assessment."""
        ...
```

### 6. Create `.pr-risk-scorer.yaml`

Default config template with all analyzer weights.

### 7. Create empty `__init__.py` files for packages
- `src/pr_risk_scorer/analyzers/__init__.py` (empty -- Phase 04 adds exports)
- `src/pr_risk_scorer/scoring/__init__.py` -- NO, Phase 05 owns this
- `src/pr_risk_scorer/output/__init__.py` -- NO, Phase 06 owns this

Only create `analyzers/__init__.py` as empty here. Scoring and output dirs created by their respective phases.

### 8. Verify installation
```bash
pip install -e ".[dev]"
python -c "from pr_risk_scorer.models import PRData, RiskScore; print('OK')"
```

## Todo List
- [ ] Create `pyproject.toml` with all dependencies and entry point
- [ ] Create `src/pr_risk_scorer/__init__.py` with version
- [ ] Create `src/pr_risk_scorer/models.py` with all data models
- [ ] Create `src/pr_risk_scorer/config.py` with YAML loading
- [ ] Create `src/pr_risk_scorer/analyzers/base_analyzer.py` with ABC
- [ ] Create `src/pr_risk_scorer/analyzers/__init__.py` (empty)
- [ ] Create `.pr-risk-scorer.yaml` default config
- [ ] Verify `pip install -e ".[dev]"` succeeds
- [ ] Verify all models importable

## Success Criteria
- `pip install -e ".[dev]"` succeeds without errors
- `from pr_risk_scorer.models import PRData, AnalyzerResult, RiskScore` works
- `from pr_risk_scorer.config import ScorerConfig` works and loads defaults
- `from pr_risk_scorer.analyzers.base_analyzer import BaseAnalyzer` works
- All Pydantic validations enforce score ranges (0-100), confidence (0-1)

## Conflict Prevention
- This phase creates ALL shared contracts; subsequent phases only import from here
- No other phase writes to `models.py`, `config.py`, or `base_analyzer.py`
- `analyzers/__init__.py` created empty -- Phase 04 exclusively owns its content

## Risk Assessment
- **Low risk**: Standard Python project setup, well-established patterns
- **Mitigation**: Use hatchling build system (simpler than setuptools)

## Security Considerations
- `github_token` in config: loaded from env var or config, never hardcoded
- `.pr-risk-scorer.yaml` should NOT contain tokens; use `GITHUB_TOKEN` env var

## Next Steps
- After completion, all 5 parallel phases (02-06) can begin simultaneously
