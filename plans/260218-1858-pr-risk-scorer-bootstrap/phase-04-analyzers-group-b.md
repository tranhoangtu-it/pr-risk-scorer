# Phase 04: Analyzers Group B (Dependency, Review, Complexity)

## Context Links
- [Plan Overview](./plan.md)
- [Phase 01: Foundation](./phase-01-project-setup-and-foundation.md) (dependency)
- [Research: Risk Algorithms](./research/researcher-260218-1858-pr-risk-algorithms.md)

## Parallelization Info
- **Execution**: PARALLEL with Phases 02, 03, 05, 06
- **Blocked by**: Phase 01
- **Blocks**: Phase 07

## Overview
- **Priority**: P1
- **Status**: pending
- **Effort**: 1.5h
- **Description**: Implement 3 analyzers (DependencyAnalyzer, ReviewAnalyzer, ComplexityAnalyzer) + populate `analyzers/__init__.py` with all 6 analyzer re-exports.

## Key Insights
- Review quality > reviewer count: one deep review beats 5 rubber-stamps (research)
- Cyclomatic complexity increase >2 per function is a risk signal
- Dependency changes (requirements.txt, package.json) have cascading impact
- This phase also owns `analyzers/__init__.py` re-exports for ALL 6 analyzers

## Requirements

### Functional
- **DependencyAnalyzer**: Score based on dependency file changes, import modifications
- **ReviewAnalyzer**: Score based on review count, depth, approval status
- **ComplexityAnalyzer**: Score based on patch complexity heuristics (nesting, conditionals)

### Non-functional
- Each analyzer < 80 lines
- Pure computation on PRData (no API calls)
- `analyzers/__init__.py` exports all 6 analyzer classes

## Architecture

```
analyzers/
  dependency.py   -- DependencyAnalyzer
  review.py       -- ReviewAnalyzer
  complexity.py   -- ComplexityAnalyzer
  __init__.py     -- re-exports all 6 analyzers (owned by this phase)
```

## Related Code Files (EXCLUSIVE)

**Create:**
- `src/pr_risk_scorer/analyzers/dependency.py`
- `src/pr_risk_scorer/analyzers/review.py`
- `src/pr_risk_scorer/analyzers/complexity.py`
- `tests/test_analyzers/test_dependency.py`
- `tests/test_analyzers/test_review.py`
- `tests/test_analyzers/test_complexity.py`

**Modify:**
- `src/pr_risk_scorer/analyzers/__init__.py` -- add re-exports for ALL 6 analyzers

**Import (read-only):**
- `src/pr_risk_scorer/models.py` (PRData, AnalyzerResult)
- `src/pr_risk_scorer/analyzers/base_analyzer.py` (BaseAnalyzer)

## File Ownership
| File | Owner |
|------|-------|
| `src/pr_risk_scorer/analyzers/dependency.py` | Phase 04 |
| `src/pr_risk_scorer/analyzers/review.py` | Phase 04 |
| `src/pr_risk_scorer/analyzers/complexity.py` | Phase 04 |
| `src/pr_risk_scorer/analyzers/__init__.py` (content) | Phase 04 |
| `tests/test_analyzers/test_dependency.py` | Phase 04 |
| `tests/test_analyzers/test_review.py` | Phase 04 |
| `tests/test_analyzers/test_complexity.py` | Phase 04 |

## Implementation Steps

### 1. DependencyAnalyzer (`dependency.py`)

**Scoring logic:**
- Detect dependency files: `requirements.txt`, `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `Gemfile`
- `dep_file_count = count of dependency files in PR changed files`
- `dep_file_score = min(dep_file_count / 2, 1.0) * 100` -- 2+ dep files = max
- Detect import changes in `.py` files (lines starting with `import` or `from` in patch)
- `import_change_score = min(import_changes / 10, 1.0) * 60`
- `loc_in_dep_files = sum additions+deletions for dep files`
- `dep_loc_score = min(loc_in_dep_files / 50, 1.0) * 80`
- `final = 0.40 * dep_file_score + 0.35 * dep_loc_score + 0.25 * import_change_score`

**Recommendations:**
- If dep files changed: "Dependency changes detected; verify compatibility and pin versions"
- If many import changes: "Multiple import changes; check for circular dependencies"

### 2. ReviewAnalyzer (`review.py`)

**Scoring logic:**
- Inverted: MORE reviews = LOWER risk
- `review_count = len(pr_data.reviews)`
- `approval_count = count where state == "APPROVED"`
- `change_request_count = count where state == "CHANGES_REQUESTED"`
- No reviews = score 100 (max risk)
- `review_coverage = min(approval_count / 2, 1.0)` -- 2 approvals = full coverage
- `review_depth = min(reviews_with_comments / max(review_count, 1), 1.0)`
- `pending_changes = 1.0 if change_request_count > 0 and approval_count == 0 else 0.0`
- `final = (1 - 0.50 * review_coverage - 0.30 * review_depth) * 80 + pending_changes * 20`
- Clamp to [0, 100]

**Recommendations:**
- If no reviews: "No reviews yet; ensure qualified reviewers approve before merge"
- If pending changes requested: "Outstanding change requests; address before merge"
- If only 1 reviewer: "Single reviewer; consider adding a second reviewer"

### 3. ComplexityAnalyzer (`complexity.py`)

**Scoring logic (heuristic -- no AST parsing for MVP):**
- Parse patches for complexity signals:
  - `nested_depth = max nesting (count leading spaces/tabs in added lines)`
  - `conditional_count = count of if/else/elif/switch/case/? in added lines`
  - `loop_count = count of for/while/do in added lines`
  - `long_functions = count of added lines with 120+ chars`
- Normalize:
  - `nesting_score = min(nested_depth / 5, 1.0) * 100`
  - `conditional_score = min(conditional_count / 15, 1.0) * 100`
  - `loop_score = min(loop_count / 8, 1.0) * 80`
  - `line_length_score = min(long_functions / 10, 1.0) * 60`
- `final = 0.30 * nesting_score + 0.30 * conditional_score + 0.25 * loop_score + 0.15 * line_length_score`
- Confidence: 0.7 (heuristic without real AST)

**Recommendations:**
- If high nesting: "Deep nesting detected; consider extracting functions"
- If many conditionals: "High conditional complexity; consider simplifying logic"

### 4. Populate `analyzers/__init__.py`

```python
from pr_risk_scorer.analyzers.base_analyzer import BaseAnalyzer
from pr_risk_scorer.analyzers.blast_radius import BlastRadiusAnalyzer
from pr_risk_scorer.analyzers.hot_path import HotPathAnalyzer
from pr_risk_scorer.analyzers.ownership import OwnershipAnalyzer
from pr_risk_scorer.analyzers.dependency import DependencyAnalyzer
from pr_risk_scorer.analyzers.review import ReviewAnalyzer
from pr_risk_scorer.analyzers.complexity import ComplexityAnalyzer

ALL_ANALYZERS = [
    BlastRadiusAnalyzer,
    HotPathAnalyzer,
    OwnershipAnalyzer,
    DependencyAnalyzer,
    ReviewAnalyzer,
    ComplexityAnalyzer,
]

__all__ = [
    "BaseAnalyzer",
    "BlastRadiusAnalyzer",
    "HotPathAnalyzer",
    "OwnershipAnalyzer",
    "DependencyAnalyzer",
    "ReviewAnalyzer",
    "ComplexityAnalyzer",
    "ALL_ANALYZERS",
]
```

**NOTE:** Phase 03 analyzers (blast_radius, hot_path, ownership) must exist when `__init__.py` imports run. This is fine at runtime since Phase 01 + Phase 03 complete before Phase 07. During Phase 04's own tests, only test files in this phase; the `__init__.py` re-exports are validated in Phase 07.

### 5. Create tests for each analyzer

Same pattern as Phase 03:
- `test_no_reviews_high_risk` -- ReviewAnalyzer with empty reviews = high score
- `test_approved_reviews_low_risk` -- 2 approvals = low score
- `test_dependency_file_detection` -- detect `requirements.txt` in changed files
- `test_complexity_nested_code` -- high nesting = high score
- `test_score_bounds` -- all scores in [0, 100]

## Todo List
- [ ] Create `src/pr_risk_scorer/analyzers/dependency.py`
- [ ] Create `src/pr_risk_scorer/analyzers/review.py`
- [ ] Create `src/pr_risk_scorer/analyzers/complexity.py`
- [ ] Update `src/pr_risk_scorer/analyzers/__init__.py` with all re-exports
- [ ] Create `tests/test_analyzers/test_dependency.py`
- [ ] Create `tests/test_analyzers/test_review.py`
- [ ] Create `tests/test_analyzers/test_complexity.py`
- [ ] Verify tests pass: `pytest tests/test_analyzers/test_dependency.py test_review.py test_complexity.py`

## Success Criteria
- Each analyzer returns `AnalyzerResult` with score in [0, 100]
- ReviewAnalyzer: no reviews = score ~80-100; 2 approvals = score ~0-20
- DependencyAnalyzer: PR with `requirements.txt` changed = higher score
- ComplexityAnalyzer: patch with deep nesting = higher score
- `analyzers/__init__.py` imports don't error (tested separately in Phase 07)
- All tests pass

## Conflict Prevention
- Does NOT touch `blast_radius.py`, `hot_path.py`, `ownership.py` (Phase 03)
- `analyzers/__init__.py` created empty in Phase 01; this phase WRITES its content
- Phase 03 does NOT modify `__init__.py`
- Test files in `tests/test_analyzers/` don't overlap with Phase 03 test files

## Risk Assessment
- **Low**: Pure computation, well-defined interfaces
- **Risk**: `__init__.py` imports Phase 03 modules; if Phase 03 not complete, imports fail
- **Mitigation**: `__init__.py` tested in Phase 07 (after all phases). Phase 04 unit tests import only their own modules.

## Security Considerations
- No API calls, no secrets
- Patch parsing: sanitize against malicious input (extremely long lines, binary patches)

## Next Steps
- Phase 07 imports `ALL_ANALYZERS` from `__init__.py` to build pipeline
