"""GitHub API client for fetching PR data."""

import os

import requests
from github import Github, GithubException

from pr_risk_scorer.config import ScorerConfig
from pr_risk_scorer.models import FileChange, PRData, ReviewData


class GitHubClientError(Exception):
    """Raised on GitHub API failures."""


class GitHubClient:
    """Client for fetching PR data from GitHub API."""

    def __init__(self, token: str | None = None, config: ScorerConfig | None = None):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token. Falls back to GITHUB_TOKEN env var.
            config: Scorer configuration. Uses defaults if not provided.

        Raises:
            GitHubClientError: If no token is provided or found in environment.
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise GitHubClientError("GitHub token required. Set GITHUB_TOKEN env var.")
        self.config = config or ScorerConfig()
        self._github = Github(self.token)

    def fetch_pr_data(self, owner: str, repo: str, number: int) -> PRData:
        """Fetch all PR data needed for analysis.

        Args:
            owner: Repository owner (user or org).
            repo: Repository name.
            number: PR number.

        Returns:
            PRData object with all relevant PR information.

        Raises:
            GitHubClientError: If PR cannot be fetched from GitHub API.
        """
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

    def fetch_file_blame(
        self, owner: str, repo: str, filepath: str, ref: str = "main"
    ) -> list[dict]:
        """Fetch blame data for a file.

        Args:
            owner: Repository owner.
            repo: Repository name.
            filepath: Path to file in repository.
            ref: Git reference (branch, commit SHA). Defaults to 'main'.

        Returns:
            List of dicts with keys: author (str), date (str ISO format).

        Raises:
            GitHubClientError: If blame data cannot be fetched.
        """
        try:
            # Use commits API to get file history (blame approximation)
            url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            params = {"path": filepath, "sha": ref, "per_page": 10}
            headers = {"Authorization": f"token {self.token}"}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            commits = resp.json()
            return [
                {
                    "author": c["commit"]["author"]["name"],
                    "date": c["commit"]["author"]["date"],
                }
                for c in commits
            ]
        except Exception as e:
            raise GitHubClientError(f"Failed to fetch blame for {filepath}: {e}") from e

    def fetch_repo_contributors(self, owner: str, repo: str) -> list[str]:
        """Fetch list of contributor logins.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            List of contributor login names (usernames).

        Raises:
            GitHubClientError: If contributors cannot be fetched.
        """
        try:
            repository = self._github.get_repo(f"{owner}/{repo}")
            return [c.login for c in repository.get_contributors()]
        except GithubException as e:
            raise GitHubClientError(f"Failed to fetch contributors: {e}") from e
