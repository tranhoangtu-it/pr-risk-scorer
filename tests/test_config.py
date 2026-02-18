"""Tests for ScorerConfig loading."""

from pathlib import Path

from pr_risk_scorer.config import ScorerConfig


def test_load_nonexistent_path_returns_defaults():
    """Test that loading from a non-existent path returns defaults."""
    config = ScorerConfig.load(Path("/tmp/nonexistent-config-12345.yaml"))
    assert config.output_format == "terminal"
    assert "blast_radius" in config.analyzers
