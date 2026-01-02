"""Agent module for micro-cursor."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from micro_cursor.tools import Tools

MAX_ITERS = 5
LOG_FILE = ".agent_log.txt"


class Agent:
    """Agent class for micro-cursor functionality."""

    def __init__(self):
        """Initialize the agent."""
        pass

    def run(self, goal: str, workspace_path: str) -> int:
        """Run the agent with a goal and workspace path.

        Args:
            goal: The goal to achieve
            workspace_path: Path to the workspace directory

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        # Ensure workspace exists
        workspace = Path(workspace_path)
        workspace.mkdir(parents=True, exist_ok=True)

        # Create tools instance
        tools = Tools(str(workspace.absolute()))

        # Create run log file
        log_path = ".agent_log.txt"
        tools.write_file(
            log_path, f"Agent run started\nGoal: {goal}\nWorkspace: {workspace.absolute()}\n\n"
        )

        # Perform iterations
        for iteration in range(1, MAX_ITERS + 1):
            self._log(tools, log_path, f"=== Iteration {iteration} ===\n")

            # Plan next step
            action = self.plan_step(tools, goal, iteration)
            if not action:
                self._log(tools, log_path, "No action planned. Exiting.\n")
                break

            # Execute action
            self._log(tools, log_path, f"Action: {action}\n")
            self._execute_action(tools, action)

            # Clear Python cache to ensure file changes are picked up
            self._clear_cache(tools)

            # Run tests
            self._log(tools, log_path, "Running tests...\n")
            # Set PYTHONPATH to workspace so pytest can find the package
            # Run pytest with verbose output to see assertion details
            test_result = tools.run_cmd(
                [sys.executable, "-m", "pytest", "-v", "--cache-clear", "."],
                cwd=".",
                env={"PYTHONPATH": str(workspace.absolute())},
            )

            if test_result["returncode"] == 0:
                # Tests passed!
                self._log(tools, log_path, f"\n✓ Tests passed after {iteration} iteration(s)!\n")
                self._log(tools, log_path, f"Success summary: Goal '{goal}' achieved.\n")
                return 0
            else:
                # Tests failed - extract and log the failing assertion
                output = test_result["stdout"] + test_result["stderr"]
                self._log(tools, log_path, f"Tests failed:\n{output}\n")

                # Extract assertion error if present
                if "AssertionError:" in output:
                    # Find the assertion line
                    lines = output.split("\n")
                    for i, line in enumerate(lines):
                        if "AssertionError:" in line or "assert" in line.lower():
                            # Log the assertion and a few lines of context
                            context_start = max(0, i - 2)
                            context_end = min(len(lines), i + 5)
                            assertion_context = "\n".join(lines[context_start:context_end])
                            self._log(
                                tools, log_path, f"Failing assertion:\n{assertion_context}\n\n"
                            )
                            break

                # Continue to next iteration

        # Max iterations reached
        self._log(
            tools, log_path, f"\n✗ Max iterations ({MAX_ITERS}) reached. Goal not achieved.\n"
        )
        return 1

    def plan_step(self, tools: Tools, goal: str, iteration: int) -> str | None:
        """Plan the next step to take.

        Day 1 simple implementation:
        - If workspace has no files, create calc.py with buggy add() and test_calc.py
        - If calc.py has the bug (returns a-b), fix it to return a+b

        Args:
            tools: Tools instance for workspace operations
            goal: The goal to achieve
            iteration: Current iteration number

        Returns:
            Action description string, or None if no action needed
        """
        files = tools.list_files()

        # Filter out log file and __pycache__
        files = [f for f in files if not f.startswith(".agent_log") and "__pycache__" not in f]

        if not files:
            # No files exist - create calc.py with buggy add() and test_calc.py
            return "create_calc_demo"

        # Check if calc.py exists and has the bug
        if "calc.py" in files:
            try:
                content = tools.read_file("calc.py")
                # Check if it has the bug (returns a - b instead of a + b)
                if "return a - b" in content or "return a-b" in content:
                    return "fix_calc_bug"
            except Exception:
                pass

        return None

    def _execute_action(self, tools: Tools, action: str) -> None:
        """Execute a planned action.

        Args:
            tools: Tools instance for workspace operations
            action: Action description string
        """
        if action == "create_calc_demo":
            # Create calc.py with intentionally buggy add function (returns a-b instead of a+b)
            tools.write_file(
                "calc.py", "def add(a, b):\n    return a - b  # BUG: should be a + b\n"
            )
            # Create test file that expects correct addition
            tools.write_file(
                "test_calc.py",
                "from calc import add\n\n"
                "def test_add():\n"
                "    assert add(2, 3) == 5\n"
                "    assert add(10, 5) == 15\n"
                "    assert add(-1, 1) == 0\n",
            )

        elif action == "fix_calc_bug":
            # Fix the bug in calc.py: change a - b to a + b
            content = tools.read_file("calc.py")
            # Replace the buggy return statement
            fixed_content = content.replace("return a - b", "return a + b")
            # Also handle if it's written as "a-b" without spaces
            fixed_content = fixed_content.replace("return a-b", "return a + b")
            tools.write_file("calc.py", fixed_content)

    def _clear_cache(self, tools: Tools) -> None:
        """Clear Python and pytest cache directories.

        Args:
            tools: Tools instance for workspace operations
        """
        workspace_path = Path(tools.workspace_path)

        # Clear pytest cache
        pytest_cache = workspace_path / ".pytest_cache"
        if pytest_cache.exists():
            shutil.rmtree(pytest_cache)

        # Clear __pycache__ directories
        for pycache in workspace_path.rglob("__pycache__"):
            if pycache.is_dir():
                shutil.rmtree(pycache)

    def _log(self, tools: Tools, log_path: str, message: str) -> None:
        """Append a message to the log file.

        Args:
            tools: Tools instance for workspace operations
            log_path: Path to log file
            message: Message to append
        """
        current_content = tools.read_file(log_path)
        tools.write_file(log_path, current_content + message)
