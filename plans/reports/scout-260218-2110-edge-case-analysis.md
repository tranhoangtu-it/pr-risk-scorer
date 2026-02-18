# Scout Report: Edge Case Analysis

## Scope
- **Focus**: Score boundary conditions, API error handling, config validation, division by zero, empty data structures, missing GitHub data fields, type mismatches
- **Files Analyzed**: 19 Python files (~1175 LOC)
- **Tests Found**: 97 test functions across 13 test files

## Critical Issues Found

### 1. **Division by Zero in HotPathAnalyzer** (Line 34)
**File**: `src/pr_risk_scorer/analyzers/hot_path.py`
```python
patch_size_signal = min((total_patch_lines / max(files_count, 1)) / 20, 1.0) * 100
```
**Issue**: If `files_count = 0`, the `max(files_count, 1)` prevents division by zero, but this creates a misleading signal when there are no files. The logic should early return or set signal to 0.0 when `files_count = 0`.

### 2. **Division by Zero Risk in ReviewAnalyzer** (Line 24)
**File**: `src/pr_risk_scorer/analyzers/review.py`
```python
review_depth = (
    min(reviews_with_body / max(review_count, 1), 1.0) if review_count > 0 else 0.0
)
```
**Status**: ✅ Properly handled with conditional check.

### 3. **Empty Results List in WeightedScorer**
**File**: `src/pr_risk_scorer/scoring/weighted_scorer.py` (Line 10)
**Issue**: Returns safe default `RiskScore(overall_score=0.0, risk_level=RiskLevel.LOW)` when `results` is empty.
**Status**: ✅ Properly handled.

### 4. **Score Boundary Validation Missing in AnalyzerResult**
**File**: `src/pr_risk_scorer/models.py` (Line 57)
```python
score: float = Field(ge=0.0, le=100.0)
```
**Status**: ✅ Pydantic validation enforces bounds. Analyzers use `min(max(...), 100.0)` clamping.

### 5. **GitHub API Missing Fields Handling**
**File**: `src/pr_risk_scorer/github_client.py` (Lines 68, 81)
```python
reviewer=r.user.login if r.user else "unknown",
author=pr.user.login if pr.user else "unknown",
```
**Status**: ✅ Defensive checks for None users.

## Security Issues

### 6. **GitHub Token Exposure Risk**
**File**: `src/pr_risk_scorer/config.py` (Line 115)
```python
data.pop("github_token", None)
```
**Status**: ✅ Token is explicitly removed before writing config to YAML.

**File**: `src/pr_risk_scorer/github_client.py` (Line 29)
**Issue**: Token stored in memory but never logged. No obvious leak vectors.

## Edge Cases in Analyzers

### 7. **Empty Files List Handling**
- **BlastRadiusAnalyzer**: No explicit check for empty `pr_data.files`. Will return score 0.0 (safe).
- **OwnershipAnalyzer** (Line 14): ✅ Explicit early return for empty files.
- **ComplexityAnalyzer**: Iterates over files; handles empty list gracefully (score stays 0).
- **DependencyAnalyzer**: Iterates over files; handles empty list gracefully.

### 8. **Patch Field Optionality**
All analyzers check `if file.patch:` before accessing patch content. ✅ Properly handled.

### 9. **Empty unique_dirs Set in BlastRadiusAnalyzer**
**File**: `src/pr_risk_scorer/analyzers/blast_radius.py` (Line 38)
```python
modules_affected = len(unique_dirs)  # Can be 0
```
**Status**: ✅ Handles zero modules gracefully (score component = 0).

## Config Validation

### 10. **YAML Loading with Empty/Invalid Files**
**File**: `src/pr_risk_scorer/config.py` (Line 36)
```python
data = yaml.safe_load(f) or {}
```
**Status**: ✅ Handles None return from empty YAML files.

### 11. **Weight Bounds Validation**
**File**: `src/pr_risk_scorer/config.py` (Line 11)
```python
weight: float = Field(ge=0.0, le=1.0)
```
**Status**: ✅ Pydantic enforces weight bounds.

### 12. **Missing Analyzer in Config**
**File**: `src/pr_risk_scorer/scoring/weighted_scorer.py` (Line 23)
```python
w = weight_map.get(r.analyzer_name, 0.0)
```
**Status**: ✅ Defaults to 0.0 weight if analyzer not in config.

## Reporter Error Handling

### 13. **Terminal Reporter Output**
**File**: `src/pr_risk_scorer/output/terminal_reporter.py`
**Issue**: No try-except around Rich rendering. If malformed data causes Rich to fail, it will propagate uncaught.
**Recommendation**: Wrap `_render_to_console` in try-except.

### 14. **JSON Reporter**
**File**: `src/pr_risk_scorer/output/json_reporter.py` (Line 12)
```python
return risk_score.model_dump_json(indent=2)
```
**Status**: ✅ Pydantic handles serialization safely.

## CLI Issues

### 15. **Repo Format Validation**
**File**: `src/pr_risk_scorer/cli.py` (Line 27)
```python
if len(parts) != 2:
    console.print("[red]Error: repo must be in 'owner/repo' format[/red]")
```
**Status**: ✅ Validates repo format before API calls.

### 16. **Missing PR Number Validation**
**Issue**: CLI doesn't validate that `pr` is a positive integer. Typer may handle this, but explicit validation would be safer.

### 17. **Date Parsing in Report Command** (Line 74)
```python
since_dt = datetime.fromisoformat(since)
```
**Issue**: No try-except for invalid date formats. Wrapped in outer try-except that catches generic `Exception`, but error message won't be specific.

## Relevant Files

### Core Models & Config
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/models.py` - Pydantic models with validation
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/config.py` - Config loading with YAML

### GitHub Client
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/github_client.py` - API client with error handling

### Analyzers (6 total)
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/analyzers/blast_radius.py` - Files/LOC/modules
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/analyzers/hot_path.py` - **Division by zero risk (line 34)**
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/analyzers/complexity.py` - Nesting/conditionals/loops
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/analyzers/ownership.py` - Cross-domain changes
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/analyzers/dependency.py` - Import/package changes
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/analyzers/review.py` - Review coverage

### Scoring
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/scoring/weighted_scorer.py` - Hybrid scoring with amplification

### Reporters (3 total)
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/output/terminal_reporter.py` - Rich terminal output
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/output/json_reporter.py` - JSON serialization
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/output/markdown_reporter.py` - Not reviewed

### CLI
- `/Users/tranhoangtu/Desktop/PET/PR-Risk-Scorer/src/pr_risk_scorer/cli.py` - Typer CLI with 3 commands

## Summary of Findings

### 🔴 Fix Required
1. **HotPathAnalyzer division by zero edge case** - Line 34 needs better handling when `files_count = 0`
2. **Terminal reporter needs error boundary** - Wrap Rich rendering in try-except

### 🟡 Low Priority
3. **Date parsing error messages** - Improve specificity in CLI report command
4. **PR number validation** - Add explicit check for positive integers

### ✅ Well-Handled
- Pydantic validation on score bounds, confidence bounds, weight bounds
- Empty results/files lists in analyzers and scorer
- Missing GitHub API fields (None user objects)
- Config YAML loading with empty files
- Token not written to config file

## Unresolved Questions
- Are there integration tests for the full CLI flow with real GitHub API calls?
- Is the hybrid amplification formula (line 38 in weighted_scorer.py) tested with edge cases like all analyzers scoring exactly 70?
