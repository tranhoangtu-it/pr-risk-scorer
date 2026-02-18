# Phase 02: GitHub Client

## Context Links
- [Plan Overview](./plan.md)
- [Phase 01: Foundation](./phase-01-project-setup-and-foundation.md) (dependency)
- [Research: Tech Architecture](./research/researcher-260218-1858-tech-architecture.md)

## Parallelization Info
- **Execution**: PARALLEL with Phases 03, 04, 05, 06
- **Blocked by**: Phase 01
- **Blocks**: Phase 07

## Overview
- **Priority**: P1
- **Status**: pending
- **Effort**: 1h
- **Description**: GitHub REST API wrapper using PyGithub. Fetches PR metadata, files, reviews, commits, blame data. Converts raw API responses into `PRData` model.

## Key Insights
- PyGithub handles pagination, rate limits, auth automatically
- REST API rate limit: 5000/hr with PAT
- Need 5 API calls per PR analysis: PR metadata, files, reviews, commits, blame
- Auth via `GITHUB_TOKEN` env var (PAT)

## Requirements

### Functional
- Fetch complete PR data into `PRData` model
- Support authentication via env var or config
- Handle API errors gracefully (rate limits, 404, auth failures)
- Fetch git blame data for changed files (for hot_path analyzer)

### Non-functional
- All GitHub calls wrapped in try/except
- Meaningful error messages on API failures
- No caching (MVP); add later

## Architecture

```
github_client.py
  GitHubClient
    ├── __init__(token, config)
    ├── fetch_pr_data(owner, repo, number) -> PRData
    ├── fetch_file_blame(owner, repo, filepath, ref) -> list[BlameEntry]
    └── fetch_repo_contributors(owner, repo) -> list[str]
```

## Related Code Files (EXCLUSIVE)

**Create:**
- `src/pr_risk_scorer/github_client.py`
- `tests/test_github_client.py`

**Import (read-only):**
- `src/pr_risk_scorer/models.py` (PRData, FileChange, ReviewData)
- `src/pr_risk_scorer/config.py` (ScorerConfig)

## File Ownership
| File | Owner |
|------|-------|
| `src/pr_risk_scorer/github_client.py` | Phase 02 |
| `tests/test_github_client.py` | Phase 02 |

## Implementation Steps

### 1. Create `src/pr_risk_scorer/github_client.py`

```python
import os
from github import Github, GithubException
from pr_risk_scorer.models import PRData, FileChange, ReviewData
from pr_risk_scorer.config import ScorerConfig


class GitHubClientError(Exception):
    """Raised on GitHub API failures."""


class GitHubClient:
    def __init__(self, token: str | None = None, config: ScorerConfig | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise GitHubClientError("GitHub token required. Set GITHUB_TOKEN env var.")
        self.config = config or ScorerConfig()
        self._github = Github(self.token)

    def fetch_pr_data(self, owner: str, repo: str, number: int) -> PRData:
        """Fetch all PR data needed for analysis."""
        try:
            repository = self._github.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(number)
        except GithubException as e:
            raise GitHubClientError(f"Failed to fetch PR #{number}: {e}") from e

        files = [
            FileChange(
                filename=f.filename,
                additions=f.additions,
                deletions=f.deletions,
                status=f.status,
                patch=f.patch,
            )
            for f in pr.get_files()
        ]

        reviews = [
            ReviewData(
                reviewer=r.user.login if r.user else "unknown",
                state=r.state,
                submitted_at=r.submitted_at.isoformat() if r.submitted_at else None,
                body=r.body,
            )
            for r in pr.get_reviews()
        ]

        return PRData(
            owner=owner,
            repo=repo,
            number=number,
            title=pr.title,
            author=pr.user.login if pr.user else "unknown",
            base_branch=pr.base.ref,
            head_branch=pr.head.ref,
            files=files,
            reviews=reviews,
            commits_count=pr.commits,
            additions=pr.additions,
            deletions=pr.deletions,
            created_at=pr.created_at.isoformat() if pr.created_at else None,
            merged_at=pr.merged_at.isoformat() if pr.merged_at else None,
        )

    def fetch_file_blame(self, owner: str, repo: str, filepath: str, ref: str = "main") -> list[dict]:
        """Fetch blame data for a file. Returns list of {author, lines, date}."""
        # PyGithub doesn't have blame API; use REST directly
        ...

    def fetch_repo_contributors(self, owner: str, repo: str) -> list[str]:
        """Fetch list of contributor logins."""
        try:
            repository = self._github.get_repo(f"{owner}/{repo}")
            return [c.login for c in repository.get_contributors()]
        except GithubException as e:
            raise GitHubClientError(f"Failed to fetch contributors: {e}") from e
```

### 2. Create `tests/test_github_client.py`

Test with mocked PyGithub objects:
- `test_fetch_pr_data_success` -- mock repo.get_pull, verify PRData fields
- `test_fetch_pr_data_not_found` -- mock 404, verify GitHubClientError
- `test_missing_token` -- no env var, verify GitHubClientError
- `test_fetch_repo_contributors` -- mock, verify list
- Use `pytest-mock` / `unittest.mock.patch`

### 3. Ensure `tests/__init__.py` exists (empty)

## Todo List
- [ ] Create `src/pr_risk_scorer/github_client.py` with GitHubClient class
- [ ] Implement `fetch_pr_data` converting API response to PRData
- [ ] Implement `fetch_file_blame` for blame data retrieval
- [ ] Implement `fetch_repo_contributors` for contributor list
- [ ] Add `GitHubClientError` custom exception
- [ ] Create `tests/test_github_client.py` with mocked tests
- [ ] Verify all tests pass

## Success Criteria
- `GitHubClient(token="test")` instantiates without error
- `fetch_pr_data` returns valid `PRData` model from mocked API
- Missing token raises `GitHubClientError` with clear message
- API 404 raises `GitHubClientError`
- All tests pass with `pytest tests/test_github_client.py`

## Conflict Prevention
- Only creates `github_client.py` and its test; no overlap with any analyzer/scorer/output
- Imports only from `models.py` and `config.py` (Phase 01, read-only)

## Risk Assessment
- **Medium**: PyGithub API surface is large; blame endpoint not natively supported
- **Mitigation**: Use raw REST call via `requests` for blame; wrap in try/except
- **Rate limits**: Not a concern for testing (all mocked)

## Security Considerations
- Token loaded from env var, never logged or serialized
- `GitHubClient.__repr__` must NOT expose token
- Token validation on init (non-empty string check)

## Next Steps
- Phase 07 wires `GitHubClient` into CLI `analyze` command
