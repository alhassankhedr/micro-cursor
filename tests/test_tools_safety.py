"""Tests for command safety and dangerous command detection."""

import sys
import tempfile

import pytest

from micro_cursor.tools import DANGEROUS_PATTERNS, DangerousCommandError, Tools


@pytest.fixture
def tools():
    """Create a Tools instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Tools(tmpdir)


def test_dangerous_patterns_defined():
    """Test that dangerous patterns are defined."""
    assert len(DANGEROUS_PATTERNS) > 0
    assert "rm -rf" in DANGEROUS_PATTERNS
    assert "sudo" in DANGEROUS_PATTERNS


def test_normal_command_executes(tools):
    """Test that normal commands still execute successfully."""
    result = tools.run_cmd([sys.executable, "-c", "print('Hello')"])

    assert result["returncode"] == 0
    assert "Hello" in result["stdout"]


def test_dangerous_command_rm_rf_detected(tools):
    """Test that rm -rf is detected as dangerous."""
    with pytest.raises(DangerousCommandError) as exc_info:
        tools.run_cmd(["rm", "-rf", "./test"])

    assert "rm -rf" in exc_info.value.command.lower()
    assert exc_info.value.reason == "dangerous_command_detected"


def test_dangerous_command_sudo_detected(tools):
    """Test that sudo is detected as dangerous."""
    with pytest.raises(DangerousCommandError) as exc_info:
        tools.run_cmd(["sudo", "apt", "update"])

    assert "sudo" in exc_info.value.command.lower()
    assert exc_info.value.reason == "dangerous_command_detected"


def test_dangerous_command_dd_detected(tools):
    """Test that dd if= is detected as dangerous."""
    with pytest.raises(DangerousCommandError) as exc_info:
        tools.run_cmd(["dd", "if=/dev/zero", "of=/dev/sda"])

    assert "dd if=" in exc_info.value.command.lower()
    assert exc_info.value.reason == "dangerous_command_detected"


def test_dangerous_command_shutdown_detected(tools):
    """Test that shutdown is detected as dangerous."""
    with pytest.raises(DangerousCommandError) as exc_info:
        tools.run_cmd(["shutdown", "-h", "now"])

    assert "shutdown" in exc_info.value.command.lower()
    assert exc_info.value.reason == "dangerous_command_detected"


def test_skip_safety_check_allows_dangerous_command(tools):
    """Test that skip_safety_check=True allows dangerous commands (for confirmed commands)."""
    # This should not raise an exception when skip_safety_check=True
    # Note: We use a safe command that matches a pattern to test the bypass
    result = tools.run_cmd(["echo", "rm -rf test"], skip_safety_check=True)

    assert result["returncode"] == 0
    assert "rm -rf test" in result["stdout"]


def test_check_dangerous_command_method(tools):
    """Test the _check_dangerous_command method directly."""
    # Normal command should not raise
    tools._check_dangerous_command(["echo", "hello"])

    # Dangerous command should raise
    with pytest.raises(DangerousCommandError):
        tools._check_dangerous_command(["rm", "-rf", "/tmp"])


def test_dangerous_command_case_insensitive(tools):
    """Test that dangerous command detection is case-insensitive."""
    with pytest.raises(DangerousCommandError):
        tools.run_cmd(["RM", "-RF", "./test"])

    with pytest.raises(DangerousCommandError):
        tools.run_cmd(["Sudo", "apt", "update"])
