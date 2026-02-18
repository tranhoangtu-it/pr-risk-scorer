"""Tests for get_reporter factory function."""

import pytest

from pr_risk_scorer.output import get_reporter
from pr_risk_scorer.output.json_reporter import JsonReporter
from pr_risk_scorer.output.markdown_reporter import MarkdownReporter
from pr_risk_scorer.output.terminal_reporter import TerminalReporter


def test_get_reporter_terminal():
    """Test factory returns TerminalReporter for 'terminal'."""
    reporter = get_reporter("terminal")
    assert isinstance(reporter, TerminalReporter)


def test_get_reporter_json():
    """Test factory returns JsonReporter for 'json'."""
    reporter = get_reporter("json")
    assert isinstance(reporter, JsonReporter)


def test_get_reporter_markdown():
    """Test factory returns MarkdownReporter for 'markdown'."""
    reporter = get_reporter("markdown")
    assert isinstance(reporter, MarkdownReporter)


def test_get_reporter_unknown_format():
    """Test factory raises ValueError for unknown format."""
    with pytest.raises(ValueError) as exc_info:
        get_reporter("xml")

    assert "Unknown format: xml" in str(exc_info.value)
    assert "terminal" in str(exc_info.value)
    assert "json" in str(exc_info.value)
    assert "markdown" in str(exc_info.value)


def test_get_reporter_case_sensitive():
    """Test factory is case-sensitive."""
    with pytest.raises(ValueError):
        get_reporter("JSON")

    with pytest.raises(ValueError):
        get_reporter("Terminal")
