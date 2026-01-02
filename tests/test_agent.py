"""Tests for micro_cursor.agent module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from micro_cursor.agent import Agent
from micro_cursor.llm import LLMResult, ToolCall


def test_agent_run_creates_workspace():
    """Test that agent creates workspace if it doesn't exist (mocked)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "new_workspace"
        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            mock_llm.next.return_value = LLMResult(content_text="No action needed", tool_calls=[])
            mock_get_llm.return_value = mock_llm

            agent = Agent()
            agent.run("test goal", str(workspace))

            assert workspace.exists()
            assert (workspace / ".agent_log.txt").exists()


def test_agent_run_creates_log_file():
    """Test that agent creates a log file (mocked)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            mock_llm.next.return_value = LLMResult(content_text="No action needed", tool_calls=[])
            mock_get_llm.return_value = mock_llm

            agent = Agent()
            agent.run("test goal", tmpdir)

            log_file = Path(tmpdir) / ".agent_log.txt"
            assert log_file.exists()

            content = log_file.read_text()
            assert "Agent run started" in content
            assert "test goal" in content


def test_agent_run_simulates_workspace_and_passes():
    """Test that agent runs in a temp workspace and eventually passes tests (mocked)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            call_count = 0

            def mock_next(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                # First call: create calc.py and test_calc.py
                if call_count == 1:
                    return LLMResult(
                        content_text=None,
                        tool_calls=[
                            ToolCall(
                                name="write_file",
                                arguments={
                                    "path": "calc.py",
                                    "content": "def add(a, b):\n    return a - b  # BUG: should be a + b\n",
                                },
                            ),
                            ToolCall(
                                name="write_file",
                                arguments={
                                    "path": "test_calc.py",
                                    "content": "from calc import add\n\n"
                                    "def test_add():\n"
                                    "    assert add(2, 3) == 5\n"
                                    "    assert add(10, 5) == 15\n"
                                    "    assert add(-1, 1) == 0\n",
                                },
                            ),
                        ],
                    )
                # Second call: fix the bug
                elif call_count == 2:
                    return LLMResult(
                        content_text=None,
                        tool_calls=[
                            ToolCall(
                                name="read_file",
                                arguments={"path": "calc.py"},
                            ),
                            ToolCall(
                                name="write_file",
                                arguments={
                                    "path": "calc.py",
                                    "content": "def add(a, b):\n    return a + b\n",
                                },
                            ),
                        ],
                    )
                # Subsequent calls: no more actions
                else:
                    return LLMResult(content_text="No more actions needed", tool_calls=[])

            mock_llm.next.side_effect = mock_next
            mock_get_llm.return_value = mock_llm

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


def test_agent_run_handles_max_iterations():
    """Test that agent returns 1 after max iterations if goal not achieved (mocked)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a workspace with a test that will always fail
        workspace = Path(tmpdir)
        (workspace / "tests").mkdir()
        (workspace / "tests" / "test_always_fails.py").write_text(
            "def test_always_fails():\n    assert False\n"
        )

        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            # LLM keeps trying but never fixes the issue
            mock_llm.next.return_value = LLMResult(
                content_text="I'll try to fix this", tool_calls=[]
            )
            mock_get_llm.return_value = mock_llm

            agent = Agent()
            result = agent.run("This will never pass", tmpdir)

            # Should return 1 after max iterations
            assert result == 1

            # Verify log mentions max iterations
            log_file = workspace / ".agent_log.txt"
            log_content = log_file.read_text()
            assert "Max iterations" in log_content or "✗" in log_content


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set - skipping real LLM test"
)
def test_agent_run_real_llm_simple_goal():
    """Test agent with real LLM on a simple goal (requires OPENAI_API_KEY)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple test file that will pass
        workspace = Path(tmpdir)
        (workspace / "test_simple.py").write_text("def test_simple():\n    assert True\n")

        agent = Agent()
        result = agent.run("Ensure the test passes", tmpdir)

        # Should succeed quickly since test already passes
        assert result == 0

        # Verify log file exists
        log_file = workspace / ".agent_log.txt"
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Tests passed" in log_content or "✓" in log_content


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set - skipping real LLM test"
)
def test_agent_run_real_llm_fix_bug():
    """Test agent with real LLM fixing a bug (requires OPENAI_API_KEY)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create a buggy calc.py
        (workspace / "calc.py").write_text("def add(a, b):\n    return a - b  # BUG\n")

        # Create a test that expects correct behavior
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n"
            "def test_add():\n"
            "    assert add(2, 3) == 5\n"
            "    assert add(10, 5) == 15\n"
        )

        agent = Agent()
        result = agent.run("Fix the bug in calc.py so tests pass", tmpdir)

        # Should eventually succeed after LLM fixes the bug
        assert result == 0

        # Verify calc.py was fixed
        calc_content = (workspace / "calc.py").read_text()
        assert "return a + b" in calc_content or "return a+b" in calc_content
        assert "return a - b" not in calc_content

        # Verify log shows success
        log_file = workspace / ".agent_log.txt"
        log_content = log_file.read_text()
        assert "Tests passed" in log_content or "✓" in log_content


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set - skipping real LLM test"
)
def test_agent_run_real_llm_gemini():
    """Test agent with real Gemini LLM (requires GEMINI_API_KEY)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple test file that will pass
        workspace = Path(tmpdir)
        (workspace / "test_simple.py").write_text("def test_simple():\n    assert True\n")

        # Set provider to Gemini
        original_provider = os.getenv("LLM_PROVIDER")
        os.environ["LLM_PROVIDER"] = "gemini"

        try:
            agent = Agent()
            result = agent.run("Ensure the test passes", tmpdir)

            # Should succeed quickly since test already passes
            assert result == 0

            # Verify log file exists
            log_file = workspace / ".agent_log.txt"
            assert log_file.exists()
        except RuntimeError as e:
            # Handle quota/rate limit errors gracefully
            if "429" in str(e) or "quota" in str(e).lower() or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip(f"Gemini API quota exceeded (this is expected on free tier): {e}")
            else:
                raise
        finally:
            # Restore original provider
            if original_provider:
                os.environ["LLM_PROVIDER"] = original_provider
            elif "LLM_PROVIDER" in os.environ:
                del os.environ["LLM_PROVIDER"]
