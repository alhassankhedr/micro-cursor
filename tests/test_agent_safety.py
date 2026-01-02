"""Tests for agent safety and dangerous command confirmation."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from micro_cursor.agent import Agent
from micro_cursor.llm import LLMResult, ToolCall


def test_agent_detects_dangerous_command_and_prompts():
    """Test that agent detects dangerous command and prompts user."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "test_pass.py").write_text("def test_pass():\n    assert True\n")

        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            mock_llm.next.return_value = LLMResult(
                content_text=None,
                tool_calls=[
                    ToolCall(name="run_cmd", arguments={"cmd": ["rm", "-rf", "./test"]}),
                ],
            )
            mock_get_llm.return_value = mock_llm

            agent = Agent()

            # Mock user input to refuse
            with patch("builtins.input", return_value="no"):
                agent.run("test goal", str(workspace))

                # Command should be refused
                log_file = workspace / ".agent_log.txt"
                log_content = log_file.read_text()
                assert "Dangerous command detected" in log_content
                assert "User refused" in log_content or "refused" in log_content.lower()


def test_agent_confirms_dangerous_command_with_yes():
    """Test that agent executes dangerous command when user confirms with 'yes'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "test_pass.py").write_text("def test_pass():\n    assert True\n")

        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            mock_llm.next.return_value = LLMResult(
                content_text=None,
                tool_calls=[
                    ToolCall(
                        name="run_cmd",
                        arguments={"cmd": ["echo", "rm -rf test"], "cwd": "."},
                    ),
                ],
            )
            mock_get_llm.return_value = mock_llm

            agent = Agent()

            # Mock user input to confirm
            with patch("builtins.input", return_value="yes"):
                with patch("sys.stdin.isatty", return_value=True):
                    agent.run("test goal", str(workspace))

                    # Command should be confirmed and executed
                    log_file = workspace / ".agent_log.txt"
                    log_content = log_file.read_text()
                    assert "Dangerous command detected" in log_content
                    assert "User confirmed" in log_content or "confirmed" in log_content.lower()


def test_agent_refuses_dangerous_command_in_non_interactive_mode():
    """Test that agent automatically refuses dangerous commands in non-interactive mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "test_pass.py").write_text("def test_pass():\n    assert True\n")

        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            mock_llm.next.return_value = LLMResult(
                content_text=None,
                tool_calls=[
                    ToolCall(name="run_cmd", arguments={"cmd": ["rm", "-rf", "./test"]}),
                ],
            )
            mock_get_llm.return_value = mock_llm

            agent = Agent()

            # Mock non-interactive mode
            with patch("sys.stdin.isatty", return_value=False):
                agent.run("test goal", str(workspace))

                # Command should be automatically refused
                log_file = workspace / ".agent_log.txt"
                log_content = log_file.read_text()
                assert "non-interactive mode" in log_content.lower()
                assert "refused" in log_content.lower() or "Refused" in log_content


def test_agent_logs_dangerous_command_detection():
    """Test that agent logs dangerous command detection details."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "test_pass.py").write_text("def test_pass():\n    assert True\n")

        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            mock_llm.next.return_value = LLMResult(
                content_text=None,
                tool_calls=[
                    ToolCall(name="run_cmd", arguments={"cmd": ["sudo", "apt", "update"]}),
                ],
            )
            mock_get_llm.return_value = mock_llm

            agent = Agent()

            with patch("builtins.input", return_value="no"):
                with patch("sys.stdin.isatty", return_value=True):
                    agent.run("test goal", str(workspace))

                    log_file = workspace / ".agent_log.txt"
                    log_content = log_file.read_text()

                    # Verify logging
                    assert "Dangerous command detected" in log_content
                    assert "sudo apt update" in log_content
                    assert "User response:" in log_content


def test_agent_handles_interrupted_confirmation():
    """Test that agent handles interrupted confirmation (Ctrl+C)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "test_pass.py").write_text("def test_pass():\n    assert True\n")

        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            mock_llm.next.return_value = LLMResult(
                content_text=None,
                tool_calls=[
                    ToolCall(name="run_cmd", arguments={"cmd": ["rm", "-rf", "./test"]}),
                ],
            )
            mock_get_llm.return_value = mock_llm

            agent = Agent()

            # Mock interrupted input (EOFError)
            with patch("builtins.input", side_effect=EOFError()):
                with patch("sys.stdin.isatty", return_value=True):
                    agent.run("test goal", str(workspace))

                    # Command should be refused
                    log_file = workspace / ".agent_log.txt"
                    log_content = log_file.read_text()
                    assert "interrupted" in log_content.lower() or "refused" in log_content.lower()
