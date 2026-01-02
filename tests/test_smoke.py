"""Smoke tests for micro-cursor."""

import subprocess
import sys


def test_smoke():
    """A minimal smoke test that always passes."""
    assert True


def test_cli_help_contains_run():
    """Test that CLI help output contains 'run'."""
    result = subprocess.run(
        [sys.executable, "-m", "micro_cursor", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "run" in result.stdout.lower()
