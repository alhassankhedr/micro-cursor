"""Tests for micro_cursor.agent module."""

import tempfile
from pathlib import Path

from micro_cursor.agent import Agent


def test_agent_run_creates_workspace():
    """Test that agent creates workspace if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "new_workspace"
        agent = Agent()
        agent.run("test goal", str(workspace))

        assert workspace.exists()
        assert (workspace / ".agent_log.txt").exists()


def test_agent_run_creates_log_file():
    """Test that agent creates a log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = Agent()
        agent.run("test goal", tmpdir)

        log_file = Path(tmpdir) / ".agent_log.txt"
        assert log_file.exists()

        content = log_file.read_text()
        assert "Agent run started" in content
        assert "test goal" in content


def test_agent_run_simulates_workspace_and_passes():
    """Test that agent runs in a temp workspace and eventually passes tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = Agent()
        result = agent.run("Create a calculator with tests", tmpdir)

        # Agent should eventually succeed (tests pass after fix)
        assert result == 0

        # Verify files were created
        workspace = Path(tmpdir)
        assert (workspace / "calc.py").exists()
        assert (workspace / "test_calc.py").exists()

        # Verify calc.py was fixed (should have a + b, not a - b)
        calc_content = (workspace / "calc.py").read_text()
        assert "return a + b" in calc_content
        assert "return a - b" not in calc_content

        # Verify log file exists and contains success message
        log_file = workspace / ".agent_log.txt"
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Tests passed" in log_content or "✓" in log_content
        assert "Iteration 1" in log_content
        assert "Iteration 2" in log_content


def test_agent_run_handles_max_iterations():
    """Test that agent returns 1 after max iterations if goal not achieved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a workspace with a test that will always fail
        workspace = Path(tmpdir)
        (workspace / "tests").mkdir()
        (workspace / "tests" / "test_always_fails.py").write_text(
            "def test_always_fails():\n    assert False\n"
        )

        agent = Agent()
        result = agent.run("This will never pass", tmpdir)

        # Should return 1 after max iterations
        assert result == 1

        # Verify log mentions max iterations
        log_file = workspace / ".agent_log.txt"
        log_content = log_file.read_text()
        assert "Max iterations" in log_content or "✗" in log_content
