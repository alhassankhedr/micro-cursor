"""End-to-end tests for agent demo functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from micro_cursor.agent import Agent
from micro_cursor.llm import LLMResult, ToolCall


def test_agent_demo_seeds_workspace_and_fixes():
    """End-to-end test: agent seeds demo, LLM fixes it, pytest passes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            call_count = 0

            def mock_next(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count == 1:
                    # First call: LLM reads both files to understand the bug
                    return LLMResult(
                        content_text=None,
                        tool_calls=[
                            ToolCall(name="read_file", arguments={"path": "calc.py"}),
                            ToolCall(name="read_file", arguments={"path": "test_calc.py"}),
                        ],
                    )
                elif call_count == 2:
                    # Second call: LLM fixes the bug
                    return LLMResult(
                        content_text=None,
                        tool_calls=[
                            ToolCall(
                                name="write_file",
                                arguments={
                                    "path": "calc.py",
                                    "content": "def add(a, b):\n    return a + b\n",
                                },
                            ),
                        ],
                    )
                else:
                    # Subsequent calls: no more actions needed
                    return LLMResult(content_text="Done", tool_calls=[])

            mock_llm.next.side_effect = mock_next
            mock_get_llm.return_value = mock_llm

            agent = Agent()
            result = agent.run("Fix the failing tests in this workspace.", str(workspace))

            # Agent should succeed
            assert result == 0

            # Verify demo files were created
            assert (workspace / "calc.py").exists()
            assert (workspace / "test_calc.py").exists()

            # Verify calc.py was fixed
            calc_content = (workspace / "calc.py").read_text()
            assert "return a + b" in calc_content or "return a+b" in calc_content
            assert "return a - b" not in calc_content

            # Verify tests pass (check log)
            log_file = workspace / ".agent_log.txt"
            log_content = log_file.read_text()
            assert "Tests passed" in log_content or "✓" in log_content

            # Verify LLM was called
            assert mock_llm.next.call_count >= 2


def test_agent_demo_with_pre_seeded_files():
    """Test agent fixes pre-seeded broken calc.py + test_calc.py."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Pre-seed with broken files
        (workspace / "calc.py").write_text("def add(a, b):\n    return a - b  # BUG\n")
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n"
            "def test_add():\n"
            "    assert add(2, 3) == 5\n"
            "    assert add(10, 5) == 15\n"
        )

        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            call_count = 0

            def mock_next(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count == 1:
                    # First call: LLM reads files and fixes
                    return LLMResult(
                        content_text=None,
                        tool_calls=[
                            ToolCall(name="read_file", arguments={"path": "calc.py"}),
                            ToolCall(
                                name="write_file",
                                arguments={
                                    "path": "calc.py",
                                    "content": "def add(a, b):\n    return a + b\n",
                                },
                            ),
                        ],
                    )
                else:
                    return LLMResult(content_text="Done", tool_calls=[])

            mock_llm.next.side_effect = mock_next
            mock_get_llm.return_value = mock_llm

            agent = Agent()
            result = agent.run("Fix the failing tests in this workspace.", str(workspace))

            # Agent should succeed
            assert result == 0

            # Verify calc.py was fixed
            calc_content = (workspace / "calc.py").read_text()
            assert "return a + b" in calc_content or "return a+b" in calc_content
            assert "return a - b" not in calc_content


def test_agent_demo_only_seeds_when_workspace_empty():
    """Test that demo seeding only happens when workspace is empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create a file so workspace is not empty
        (workspace / "existing.py").write_text("# Existing file\n")

        with patch("micro_cursor.agent.get_llm") as mock_get_llm:
            mock_llm = Mock()
            mock_llm.next.return_value = LLMResult(content_text="No action", tool_calls=[])
            mock_get_llm.return_value = mock_llm

            agent = Agent()
            agent.run("Fix the failing tests in this workspace.", str(workspace))

            # Demo files should NOT be created
            assert not (workspace / "calc.py").exists()
            assert not (workspace / "test_calc.py").exists()

            # Existing file should still be there
            assert (workspace / "existing.py").exists()
