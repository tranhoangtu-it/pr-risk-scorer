# PR Risk Scorer - Technical Architecture Research Report

**Date:** 2026-02-18 | **Prepared by:** Researcher

---

## Executive Summary

PR Risk Scorer should use **Python with Click/Typer** + **GitHub REST API** for optimal balance of ecosystem maturity, developer velocity, and distribution flexibility. Recommend plugin-based analyzer architecture with pipeline pattern.

---

## 1. GitHub API Analysis

### REST vs GraphQL: Recommendation = **REST + GraphQL Hybrid**

| Aspect | REST | GraphQL | Recommendation |
|--------|------|---------|---|
| **Rate Limits** | 60 req/hr (unauthenticated), 5000/hr (token) | 5000 points/hr (calculated) | GraphQL more efficient for complex queries |
| **PR Analysis** | Separate endpoints (PR, commits, files, reviews) | Single query gets all data | GraphQL for bulk analysis, REST for simple lookups |
| **Auth Overhead** | Light (less overhead) | Heavier query construction | REST for auth flow, GraphQL for data fetching |
| **Learning Curve** | Easier (standard REST) | Steeper (query syntax) | REST for MVP, add GraphQL later |

**API Endpoints Needed:**
- `GET /repos/{owner}/{repo}/pulls/{number}` - PR metadata
- `GET /repos/{owner}/{repo}/pulls/{number}/commits` - Commit history
- `GET /repos/{owner}/{repo}/pulls/{number}/files` - Changed files
- `GET /repos/{owner}/{repo}/commits/{sha}/blame` - Code blame data
- `GET /repos/{owner}/{repo}/pulls/{number}/reviews` - Review history

**Authentication Strategy:** GitHub PAT (Personal Access Token) > GitHub App (for org-wide) > OAuth (for hosted SaaS). PAT simplest for CLI.

---

## 2. Tech Stack Comparison

### Recommended: **Python (Typer/Click)**

**Rationale:**
- Rich ecosystem (PyGithub, Octokit, gitpython)
- Rapid development, excellent for data analysis
- Rich.py for beautiful terminal output
- Easy distribution (PyPI, pip, Homebrew via formula)
- Strong regex/analysis libraries (re, ast for code parsing)

**Ecosystem:**
- CLI: Typer (modern, simple, Pydantic integration)
- GitHub API: PyGithub (mature, well-documented)
- Output formatting: Rich (beautiful tables, progress bars, JSON)
- Config: Pydantic, YAML loading
- Testing: pytest

**Alternative: TypeScript/Node.js**
- Strengths: Native JS ecosystem, @octokit/rest mature
- Weaknesses: Package distribution complexity, dependency bloat
- Use case: If targeting CI/CD integration first

**Alternative: Go**
- Strengths: Single binary, fast execution, gh-cli uses it
- Weaknesses: Steeper learning curve, less native data analysis
- Use case: When performance critical or binary distribution key

---

## 3. Recommended Architecture

### 3.1 Layered Pipeline Architecture

```
Input Layer → Analyzer Layer → Scoring Layer → Output Layer
```

**Flow:**
1. **Input**: Fetch PR data from GitHub (REST API)
2. **Analyzer**: Run modular risk analyzers
   - Files changed analyzer (large diffs)
   - Author history analyzer (new contributor)
   - Review coverage analyzer (approvals)
   - Test impact analyzer (test file changes)
   - Dependencies analyzer (major version bumps)
3. **Scoring**: Aggregate analyzer outputs with weighted scores
4. **Output**: Format results (terminal, JSON, GitHub comment)

### 3.2 Plugin/Analyzer Pattern

Each risk factor is an independent analyzer:

```python
class RiskAnalyzer(ABC):
    @abstractmethod
    def analyze(self, pr_data: PRData) -> RiskScore:
        pass

class FilesChangedAnalyzer(RiskAnalyzer): ...
class AuthorHistoryAnalyzer(RiskAnalyzer): ...
class ReviewCoverageAnalyzer(RiskAnalyzer): ...
```

**Benefits:** Easy to add/remove analyzers, testable, configurable weights

### 3.3 Configuration-Driven Approach

```yaml
analyzers:
  files_changed:
    enabled: true
    weight: 0.2
    threshold: 50
  author_history:
    enabled: true
    weight: 0.15
  review_coverage:
    enabled: true
    weight: 0.25
    min_approvals: 2

output:
  format: json  # or 'text', 'markdown'
  min_risk_level: medium
```

---

## 4. GitHub Integration Patterns

### 4.1 CLI Primary Interface (MVP)

```bash
pr-risk-scorer analyze owner/repo --pr-number 123 --output json
pr-risk-scorer report owner/repo --since 2026-02-01
pr-risk-scorer config init  # Create .pr-risk-scorer.yaml
```

### 4.2 GitHub Actions Integration (Post-MVP)

- Action publishes results as check/annotation
- Fails PR if risk > threshold
- Posts summary comment

### 4.3 Pre-commit Hook (Future)

- Run analyzer on staged changes
- Block risky commits

---

## 5. Output Formats & Reporting

**Recommended Outputs:**
- **Terminal**: Rich formatting, color-coded risk levels
- **JSON**: Machine-readable, CI/CD integration
- **GitHub PR Comment**: Rich markdown summary with link to details
- **SARIF**: Security reporting standard (future)

**Report Content:**
- Overall risk score (1-100)
- Per-analyzer risk breakdown
- Actionable recommendations
- File-level risk hotspots

---

## 6. Distribution & Packaging

### Recommended: **Multi-channel**

1. **PyPI + pip**
   ```bash
   pip install pr-risk-scorer
   ```
   - Standard Python distribution
   - Easiest for developers

2. **Homebrew** (via tap formula)
   ```bash
   brew tap pr-risk-scorer/tap
   brew install pr-risk-scorer
   ```
   - Native macOS/Linux experience

3. **Docker Image**
   ```bash
   docker run ghcr.io/owner/pr-risk-scorer analyze owner/repo --pr 123
   ```
   - CI/CD integration
   - Reproducible environment

4. **GitHub Release Binaries** (stretch: compile Python to single binary with PyInstaller)

---

## 7. Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Language** | Python 3.10+ | Balance: productivity, ecosystem, distribution |
| **CLI Framework** | Typer | Modern, type-safe, fewer dependencies than Click |
| **GitHub API** | REST (primary), GraphQL (future) | REST proven, GraphQL optimizes queries |
| **Config Format** | YAML | Human-readable, industry standard |
| **Output Lib** | Rich | Beautiful terminal output, minimal deps |
| **Testing** | pytest + pytest-mock | Industry standard, excellent fixtures |
| **Auth** | PAT default, configurable | Simple for MVP, org-wide auth later |

---

## 8. Risk Assessment & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| GitHub rate limits | Blocks analysis on large repos | Implement caching, batch queries, GraphQL optimization |
| PyPI/pip adoption | Distribution fragmentation | Homebrew tap + clear docs |
| Dependency bloat | Large install size | Minimize deps: Typer, PyGithub, Rich only |
| Code blame performance | Slow on large diffs | Async requests, progress bar, optional analysis |

---

## 9. Implementation Priorities (MVP)

1. **Phase 1:** Python base + REST API integration + files/author analyzers
2. **Phase 2:** Add review/test/dependency analyzers
3. **Phase 3:** Output formats (JSON, GitHub comment)
4. **Phase 4:** Configuration system
5. **Phase 5:** GitHub Actions action + distribution

---

## Unresolved Questions

1. **Scope Limits:** How to handle repos with 1000+ changed files in single PR?
2. **Offline Mode:** Should analyzer work without network (cached data)?
3. **Enterprise GitHub:** Support for GitHub Enterprise Server (different API)?
4. **Multi-language Support:** Analyze language-specific risk patterns (Rust vs Python)?
