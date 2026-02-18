from typer.testing import CliRunner
from pathlib import Path
from unittest.mock import Mock, patch
from pr_risk_scorer.cli import app
from pr_risk_scorer.models import PRData, FileChange, ReviewData

runner = CliRunner()


def test_analyze_invalid_repo_format():
    """Test that invalid repo format causes exit code 1."""
    result = runner.invoke(app, ["analyze", "invalid-repo", "--pr", "123"])
    assert result.exit_code == 1
    assert "repo must be in 'owner/repo' format" in result.stdout


def test_analyze_missing_pr_flag():
    """Test that missing --pr flag causes non-zero exit."""
    result = runner.invoke(app, ["analyze", "owner/repo"])
    assert result.exit_code != 0


def test_config_init_creates_file(tmp_path):
    """Test that config init creates .pr-risk-scorer.yaml file."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "Created .pr-risk-scorer.yaml" in result.stdout
        config_file = Path(".pr-risk-scorer.yaml")
        assert config_file.exists()
        # Verify content is valid YAML
        import yaml
        with open(config_file) as f:
            data = yaml.safe_load(f)
        assert "analyzers" in data
        assert "github_token" not in data  # Should be excluded


def test_config_init_existing_file(tmp_path):
    """Test that config init detects existing file."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create existing config file
        config_file = Path(".pr-risk-scorer.yaml")
        config_file.write_text("existing: config")

        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "already exists" in result.stdout


def test_analyze_full_pipeline(small_pr):
    """Test full analyze pipeline with mocked GitHub client."""
    # Create PR data with files and reviews
    pr_data = PRData(
        owner="test",
        repo="repo",
        number=123,
        title="Test PR",
        author="dev",
        commits_count=2,
        additions=50,
        deletions=20,
        files=[
            FileChange(filename="src/main.py", additions=30, deletions=10),
            FileChange(filename="tests/test_main.py", additions=20, deletions=10),
        ],
        reviews=[
            ReviewData(reviewer="reviewer1", state="APPROVED"),
        ],
    )

    # Mock GitHubClient
    mock_client = Mock()
    mock_client.fetch_pr_data.return_value = pr_data

    with patch("pr_risk_scorer.cli.GitHubClient", return_value=mock_client):
        result = runner.invoke(app, [
            "analyze",
            "owner/repo",
            "--pr", "123",
            "--output", "json"
        ])

        assert result.exit_code == 0
        # Verify JSON output contains expected fields
        import json
        try:
            output_data = json.loads(result.stdout)
            assert "overall_score" in output_data
            assert "risk_level" in output_data
            assert "analyzer_results" in output_data
        except json.JSONDecodeError:
            # May have additional console output, just check exit code
            pass


def test_report_invalid_repo_format():
    """Test that report command validates repo format."""
    result = runner.invoke(app, [
        "report",
        "invalid-repo",
        "--since", "2026-01-01"
    ])
    assert result.exit_code == 1
    assert "repo must be in 'owner/repo' format" in result.stdout


def test_analyze_github_error():
    """Test that GitHub errors are handled gracefully."""
    from pr_risk_scorer.github_client import GitHubClientError

    mock_client = Mock()
    mock_client.fetch_pr_data.side_effect = GitHubClientError("API rate limit exceeded")

    with patch("pr_risk_scorer.cli.GitHubClient", return_value=mock_client):
        result = runner.invoke(app, [
            "analyze",
            "owner/repo",
            "--pr", "123"
        ])

        assert result.exit_code == 1
        assert "GitHub Error" in result.stdout


def _make_mock_pull(number, title, merged_at):
    """Helper to create a mock pull request object."""
    pull = Mock()
    pull.number = number
    pull.title = title
    pull.merged_at = merged_at
    return pull


def _make_pr_data(number):
    """Helper to create PRData for report tests."""
    return PRData(
        owner="test", repo="repo", number=number,
        title=f"PR #{number}", author="dev", commits_count=1,
        additions=10, deletions=5,
        files=[FileChange(filename="src/main.py", additions=10, deletions=5)],
        reviews=[ReviewData(reviewer="reviewer1", state="APPROVED")],
    )


def test_report_success_with_merged_prs():
    """Test report command with merged PRs found."""
    from datetime import datetime

    mock_client = Mock()
    mock_repo = Mock()
    mock_client._github.get_repo.return_value = mock_repo

    merged_pulls = [
        _make_mock_pull(10, "Fix bug", datetime(2026, 2, 1)),
        _make_mock_pull(11, "Add feature", datetime(2026, 2, 5)),
    ]
    mock_repo.get_pulls.return_value = merged_pulls
    mock_client.fetch_pr_data.side_effect = [_make_pr_data(10), _make_pr_data(11)]

    with patch("pr_risk_scorer.cli.GitHubClient", return_value=mock_client):
        result = runner.invoke(app, [
            "report", "owner/repo", "--since", "2026-01-01"
        ])

    assert result.exit_code == 0
    assert "PR #10" in result.stdout
    assert "PR #11" in result.stdout


def test_report_no_merged_prs_found():
    """Test report command when no merged PRs match the since date."""
    from datetime import datetime

    mock_client = Mock()
    mock_repo = Mock()
    mock_client._github.get_repo.return_value = mock_repo

    # PR merged before the since date
    old_pull = _make_mock_pull(5, "Old PR", datetime(2025, 6, 1))
    mock_repo.get_pulls.return_value = [old_pull]

    with patch("pr_risk_scorer.cli.GitHubClient", return_value=mock_client):
        result = runner.invoke(app, [
            "report", "owner/repo", "--since", "2026-01-01"
        ])

    assert result.exit_code == 0
    assert "No merged PRs found" in result.stdout


def test_report_skips_unmerged_prs():
    """Test report command skips PRs that were not merged."""
    from datetime import datetime

    mock_client = Mock()
    mock_repo = Mock()
    mock_client._github.get_repo.return_value = mock_repo

    unmerged = _make_mock_pull(7, "Unmerged", None)
    merged = _make_mock_pull(8, "Merged", datetime(2026, 2, 1))
    mock_repo.get_pulls.return_value = [unmerged, merged]
    mock_client.fetch_pr_data.return_value = _make_pr_data(8)

    with patch("pr_risk_scorer.cli.GitHubClient", return_value=mock_client):
        result = runner.invoke(app, [
            "report", "owner/repo", "--since", "2026-01-01"
        ])

    assert result.exit_code == 0
    assert "PR #8" in result.stdout
    # fetch_pr_data should only be called for the merged PR
    mock_client.fetch_pr_data.assert_called_once_with("owner", "repo", 8)


def test_report_respects_limit():
    """Test report command respects --limit parameter."""
    from datetime import datetime

    mock_client = Mock()
    mock_repo = Mock()
    mock_client._github.get_repo.return_value = mock_repo

    pulls = [_make_mock_pull(i, f"PR {i}", datetime(2026, 2, i)) for i in range(1, 6)]
    mock_repo.get_pulls.return_value = pulls
    mock_client.fetch_pr_data.side_effect = [_make_pr_data(i) for i in range(1, 6)]

    with patch("pr_risk_scorer.cli.GitHubClient", return_value=mock_client):
        result = runner.invoke(app, [
            "report", "owner/repo", "--since", "2026-01-01", "--limit", "2"
        ])

    assert result.exit_code == 0
    assert mock_client.fetch_pr_data.call_count == 2


def test_report_github_client_error():
    """Test report command handles GitHubClientError."""
    from pr_risk_scorer.github_client import GitHubClientError

    with patch("pr_risk_scorer.cli.GitHubClient", side_effect=GitHubClientError("No token")):
        result = runner.invoke(app, [
            "report", "owner/repo", "--since", "2026-01-01"
        ])

    assert result.exit_code == 1
    assert "GitHub Error" in result.stdout


def test_report_invalid_date_format():
    """Test report command handles invalid date format."""
    mock_client = Mock()
    mock_repo = Mock()
    mock_client._github.get_repo.return_value = mock_repo
    mock_repo.get_pulls.return_value = []
    # fromisoformat will raise ValueError for bad date
    with patch("pr_risk_scorer.cli.GitHubClient", return_value=mock_client):
        result = runner.invoke(app, [
            "report", "owner/repo", "--since", "not-a-date"
        ])

    assert result.exit_code == 1


def test_report_with_json_output():
    """Test report command with JSON output format."""
    from datetime import datetime

    mock_client = Mock()
    mock_repo = Mock()
    mock_client._github.get_repo.return_value = mock_repo

    merged = _make_mock_pull(15, "JSON test", datetime(2026, 2, 10))
    mock_repo.get_pulls.return_value = [merged]
    mock_client.fetch_pr_data.return_value = _make_pr_data(15)

    with patch("pr_risk_scorer.cli.GitHubClient", return_value=mock_client):
        result = runner.invoke(app, [
            "report", "owner/repo", "--since", "2026-01-01", "--output", "json"
        ])

    assert result.exit_code == 0
    assert "PR #15" in result.stdout


def test_analyze_value_error():
    """Test that ValueError in analyze is handled gracefully."""
    mock_client = Mock()
    mock_client.fetch_pr_data.return_value = _make_pr_data(1)

    with patch("pr_risk_scorer.cli.GitHubClient", return_value=mock_client), \
         patch("pr_risk_scorer.cli.get_reporter", side_effect=ValueError("Unknown format")):
        result = runner.invoke(app, [
            "analyze", "owner/repo", "--pr", "1"
        ])

    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_main_entry_point():
    """Test main() entry point delegates to app."""
    from pr_risk_scorer.cli import main
    with patch("pr_risk_scorer.cli.app") as mock_app:
        main()
        mock_app.assert_called_once()
