# Phase 03: Analyzers Group A (Blast Radius, Hot Path, Ownership)

## Context Links
- [Plan Overview](./plan.md)
- [Phase 01: Foundation](./phase-01-project-setup-and-foundation.md) (dependency)
- [Research: Risk Algorithms](./research/researcher-260218-1858-pr-risk-algorithms.md)

## Parallelization Info
- **Execution**: PARALLEL with Phases 02, 04, 05, 06
- **Blocked by**: Phase 01
- **Blocks**: Phase 07

## Overview
- **Priority**: P1
- **Status**: pending
- **Effort**: 1.5h
- **Description**: Implement 3 independent analyzers: BlastRadiusAnalyzer (change scope metrics), HotPathAnalyzer (historical bug density/churn), OwnershipAnalyzer (CODEOWNERS mismatch).

## Key Insights
- Blast radius + history explain ~70% of variance in defect prediction (research)
- Ownership mismatch increases defect escape by 150-200%
- Each analyzer: extends `BaseAnalyzer`, receives `PRData`, returns `AnalyzerResult`
- All scoring normalized 0-100

## Requirements

### Functional
- **BlastRadiusAnalyzer**: Score based on files changed, LOC delta, module spread
- **HotPathAnalyzer**: Score based on file churn rate and historical changes (uses file metadata from PRData)
- **OwnershipAnalyzer**: Score based on author vs expected owners for changed files

### Non-functional
- Each analyzer < 80 lines (KISS)
- Pure computation -- no API calls (data already in PRData)
- Deterministic: same PRData input = same score output

## Architecture

```
analyzers/
  blast_radius.py  -- BlastRadiusAnalyzer
  hot_path.py      -- HotPathAnalyzer
  ownership.py     -- OwnershipAnalyzer
```

Each extends `BaseAnalyzer`:
```python
class BlastRadiusAnalyzer(BaseAnalyzer):
    name = "blast_radius"
    def analyze(self, pr_data: PRData) -> AnalyzerResult: ...
```

## Related Code Files (EXCLUSIVE)

**Create:**
- `src/pr_risk_scorer/analyzers/blast_radius.py`
- `src/pr_risk_scorer/analyzers/hot_path.py`
- `src/pr_risk_scorer/analyzers/ownership.py`
- `tests/test_analyzers/__init__.py`
- `tests/test_analyzers/test_blast_radius.py`
- `tests/test_analyzers/test_hot_path.py`
- `tests/test_analyzers/test_ownership.py`

**Import (read-only):**
- `src/pr_risk_scorer/models.py` (PRData, AnalyzerResult)
- `src/pr_risk_scorer/analyzers/base_analyzer.py` (BaseAnalyzer)

## File Ownership
| File | Owner |
|------|-------|
| `src/pr_risk_scorer/analyzers/blast_radius.py` | Phase 03 |
| `src/pr_risk_scorer/analyzers/hot_path.py` | Phase 03 |
| `src/pr_risk_scorer/analyzers/ownership.py` | Phase 03 |
| `tests/test_analyzers/__init__.py` | Phase 03 |
| `tests/test_analyzers/test_blast_radius.py` | Phase 03 |
| `tests/test_analyzers/test_hot_path.py` | Phase 03 |
| `tests/test_analyzers/test_ownership.py` | Phase 03 |

## Implementation Steps

### 1. BlastRadiusAnalyzer (`blast_radius.py`)

**Scoring logic:**
- `files_score = min(files_changed / 20, 1.0) * 100` -- 20+ files = max
- `loc_score = min(total_loc_delta / 500, 1.0) * 100` -- 500+ LOC = max
- `module_score = min(unique_dirs / 5, 1.0) * 100` -- 5+ modules = max
- `final = 0.50 * files_score + 0.30 * loc_score + 0.20 * module_score`

**Details dict:**
- `files_changed`, `total_additions`, `total_deletions`, `modules_affected`, `largest_file`

**Recommendations:**
- If score > 50: "Consider splitting this PR into smaller changes"
- If single file > 300 LOC: "File X has 300+ LOC changes; review carefully"

### 2. HotPathAnalyzer (`hot_path.py`)

**Scoring logic (MVP -- without git history API):**
- Use PR-level heuristics since full git history requires separate API calls:
  - `churn_signal = min(commits_count / 10, 1.0) * 100` -- many commits = instability
  - `file_diversity = min(len(files) / 15, 1.0) * 100` -- many files = spread risk
  - `patch_size_signal = min(sum(additions+deletions per file with large patches) / total_files, 1.0) * 100`
- `final = 0.40 * churn_signal + 0.35 * file_diversity + 0.25 * patch_size_signal`
- Confidence: 0.6 (lower -- MVP heuristic without real git history)

**Recommendations:**
- If high churn signal: "This PR has many commits; consider squashing and rebasing"

**NOTE:** Full git-blame integration deferred to Phase 02's `fetch_file_blame`; this analyzer uses what's available in PRData now. Phase 07 can wire in enriched data.

### 3. OwnershipAnalyzer (`ownership.py`)

**Scoring logic:**
- Count unique directories in changed files
- For MVP: If PR author matches < 50% of top-level dirs they've touched before, risk is higher
- Heuristic: `ownership_score = (1 - author_familiarity) * 100`
- Since CODEOWNERS data requires separate file fetch, MVP uses:
  - File path depth (deeper = more specialized)
  - Number of distinct top-level directories (more = likely cross-domain)
  - `cross_domain_score = min(unique_top_dirs / 3, 1.0) * 100`
  - `depth_score = min(max_depth / 5, 1.0) * 50`
  - `final = 0.60 * cross_domain_score + 0.40 * depth_score`
- Confidence: 0.5 (no CODEOWNERS data in MVP)

**Recommendations:**
- If high cross-domain: "Changes span multiple domains; ensure domain experts review"

### 4. Create tests for each analyzer

Each test file:
- `test_empty_pr` -- empty files list returns low score
- `test_small_pr` -- 1-3 files, low score
- `test_large_pr` -- 20+ files, high score
- `test_score_bounds` -- verify 0 <= score <= 100
- `test_recommendations` -- verify recommendations generated for high-risk

Use `PRData` fixtures with varied file counts and LOC.

## Todo List
- [ ] Create `src/pr_risk_scorer/analyzers/blast_radius.py`
- [ ] Create `src/pr_risk_scorer/analyzers/hot_path.py`
- [ ] Create `src/pr_risk_scorer/analyzers/ownership.py`
- [ ] Create `tests/test_analyzers/__init__.py`
- [ ] Create `tests/test_analyzers/test_blast_radius.py`
- [ ] Create `tests/test_analyzers/test_hot_path.py`
- [ ] Create `tests/test_analyzers/test_ownership.py`
- [ ] Verify all tests pass with `pytest tests/test_analyzers/`

## Success Criteria
- Each analyzer returns `AnalyzerResult` with `score` in [0, 100]
- Empty PR (no files) returns score near 0
- Large PR (20+ files, 500+ LOC) returns score near 100 for blast radius
- All recommendations are non-empty strings
- `pytest tests/test_analyzers/test_blast_radius.py test_hot_path.py test_ownership.py` passes

## Conflict Prevention
- Only creates files in `analyzers/` (3 modules) and `tests/test_analyzers/` (3 test files + `__init__`)
- Does NOT modify `analyzers/__init__.py` -- Phase 04 owns re-exports
- No overlap with Phase 04 analyzers (dependency, review, complexity)

## Risk Assessment
- **Low**: Pure computation, no external dependencies
- **Risk**: HotPath analyzer is approximation without git history
- **Mitigation**: Low confidence score (0.6); upgrade in future phase with blame data

## Security Considerations
- No API calls, no secrets, no file system access
- Pure in-memory computation on PRData model

## Next Steps
- Phase 07 wires analyzers into pipeline
- Future: Enrich HotPathAnalyzer with git blame data from GitHubClient
