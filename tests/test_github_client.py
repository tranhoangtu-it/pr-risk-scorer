"""Tests for GitHub client module."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from github import GithubException

from pr_risk_scorer.github_client import GitHubClient, GitHubClientError


@pytest.fixture
def mock_github_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-123")


@pytest.fixture
def github_client(mock_github_token):
    with patch("pr_risk_scorer.github_client.Github"):
        return GitHubClient()


class TestGitHubClientInit:
    def test_init_with_token_parameter(self):
        with patch("pr_risk_scorer.github_client.Github"):
            client = GitHubClient(token="explicit-token")
            assert client.token == "explicit-token"

    def test_init_with_env_var(self, mock_github_token):
        with patch("pr_risk_scorer.github_client.Github"):
            client = GitHubClient()
            assert client.token == "test-token-123"

    def test_init_missing_token(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(GitHubClientError, match="GitHub token required"):
            GitHubClient()


class TestFetchPRData:
    def test_fetch_pr_data_success(self, github_client):
        mock_repo = Mock()
        github_client._github.get_repo.return_value = mock_repo

        mock_pr = Mock()
        mock_pr.title = "Add new feature"
        mock_pr.user.login = "test-author"
        mock_pr.base.ref = "main"
        mock_pr.head.ref = "feature-branch"
        mock_pr.commits = 5
        mock_pr.additions = 100
        mock_pr.deletions = 50
        mock_pr.created_at = datetime(2024, 1, 15, 10, 30, 0)
        mock_pr.merged_at = datetime(2024, 1, 16, 14, 20, 0)

        mock_file = Mock()
        mock_file.filename = "src/main.py"
        mock_file.additions = 80
        mock_file.deletions = 30
        mock_file.status = "modified"
        mock_file.patch = "+new code"
        mock_pr.get_files.return_value = [mock_file]

        mock_review = Mock()
        mock_review.user.login = "reviewer1"
        mock_review.state = "APPROVED"
        mock_review.submitted_at = datetime(2024, 1, 16, 12, 0, 0)
        mock_review.body = "LGTM"
        mock_pr.get_reviews.return_value = [mock_review]

        mock_repo.get_pull.return_value = mock_pr

        pr_data = github_client.fetch_pr_data("owner", "repo", 123)
        assert pr_data.owner == "owner"
        assert pr_data.number == 123
        assert pr_data.title == "Add new feature"
        assert pr_data.author == "test-author"
        assert len(pr_data.files) == 1
        assert len(pr_data.reviews) == 1
        assert pr_data.reviews[0].reviewer == "reviewer1"

    def test_fetch_pr_data_not_found(self, github_client):
        mock_repo = Mock()
        github_client._github.get_repo.return_value = mock_repo
        mock_repo.get_pull.side_effect = GithubException(
            status=404, data={"message": "Not Found"}, headers={}
        )
        with pytest.raises(GitHubClientError, match="Failed to fetch PR #999"):
            github_client.fetch_pr_data("owner", "repo", 999)

    def test_fetch_pr_data_repo_not_found(self, github_client):
        github_client._github.get_repo.side_effect = GithubException(
            status=404, data={"message": "Not Found"}, headers={}
        )
        with pytest.raises(GitHubClientError, match="Failed to fetch PR #1"):
            github_client.fetch_pr_data("nonexistent", "repo", 1)

    def test_fetch_pr_data_with_none_user(self, github_client):
        mock_repo = Mock()
        github_client._github.get_repo.return_value = mock_repo

        mock_pr = Mock()
        mock_pr.title = "Test PR"
        mock_pr.user = None
        mock_pr.base.ref = "main"
        mock_pr.head.ref = "test"
        mock_pr.commits = 1
        mock_pr.additions = 10
        mock_pr.deletions = 5
        mock_pr.created_at = None
        mock_pr.merged_at = None
        mock_pr.get_files.return_value = []
        mock_pr.get_reviews.return_value = []
        mock_repo.get_pull.return_value = mock_pr

        pr_data = github_client.fetch_pr_data("owner", "repo", 1)
        assert pr_data.author == "unknown"


class TestFetchFileBlame:
    @patch("pr_risk_scorer.github_client.requests.get")
    def test_fetch_file_blame_success(self, mock_get, github_client):
        mock_response = Mock()
        mock_response.json.return_value = [
            {"commit": {"author": {"name": "John", "date": "2024-01-15T10:30:00Z"}}}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = github_client.fetch_file_blame("owner", "repo", "src/main.py")
        assert len(result) == 1
        assert result[0]["author"] == "John"

    @patch("pr_risk_scorer.github_client.requests.get")
    def test_fetch_file_blame_error(self, mock_get, github_client):
        mock_get.side_effect = Exception("API Error")
        with pytest.raises(GitHubClientError, match="Failed to fetch blame"):
            github_client.fetch_file_blame("owner", "repo", "src/main.py")


class TestFetchRepoContributors:
    def test_fetch_repo_contributors_success(self, github_client):
        mock_repo = Mock()
        github_client._github.get_repo.return_value = mock_repo
        c1, c2 = Mock(), Mock()
        c1.login = "user1"
        c2.login = "user2"
        mock_repo.get_contributors.return_value = [c1, c2]

        result = github_client.fetch_repo_contributors("owner", "repo")
        assert result == ["user1", "user2"]

    def test_fetch_repo_contributors_error(self, github_client):
        mock_repo = Mock()
        github_client._github.get_repo.return_value = mock_repo
        mock_repo.get_contributors.side_effect = GithubException(
            status=403, data={"message": "Forbidden"}, headers={}
        )
        with pytest.raises(GitHubClientError, match="Failed to fetch contributors"):
            github_client.fetch_repo_contributors("owner", "repo")

    def test_fetch_repo_contributors_empty(self, github_client):
        mock_repo = Mock()
        github_client._github.get_repo.return_value = mock_repo
        mock_repo.get_contributors.return_value = []
        assert github_client.fetch_repo_contributors("owner", "repo") == []
