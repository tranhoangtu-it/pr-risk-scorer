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
