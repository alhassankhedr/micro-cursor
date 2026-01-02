"""Agent module for micro-cursor."""

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
        tools.write_file(log_path, f"Agent run started\nGoal: {goal}\nWorkspace: {workspace.absolute()}\n\n")
        
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
            # Run pytest on tests directory explicitly
            test_result = tools.run_cmd(
                [sys.executable, "-m", "pytest", "-q", "--cache-clear", "tests/"],
                cwd=".",
                env={"PYTHONPATH": str(workspace.absolute())}
            )
            
            if test_result["returncode"] == 0:
                # Tests passed!
                self._log(tools, log_path, f"\n✓ Tests passed after {iteration} iteration(s)!\n")
                self._log(tools, log_path, f"Success summary: Goal '{goal}' achieved.\n")
                return 0
            else:
                # Tests failed
                self._log(tools, log_path, f"Tests failed:\n{test_result['stdout']}\n{test_result['stderr']}\n")
                self._log(tools, log_path, f"Failing output summary: {test_result['stdout'][:200]}...\n\n")
                # Continue to next iteration
        
        # Max iterations reached
        self._log(tools, log_path, f"\n✗ Max iterations ({MAX_ITERS}) reached. Goal not achieved.\n")
        return 1
    
    def plan_step(self, tools: Tools, goal: str, iteration: int) -> str | None:
        """Plan the next step to take.
        
        Day 1 simple implementation:
        - If workspace has no files, create a tiny python package + a failing test
        - If tests fail, apply a hardcoded fix for the known failure
        
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
            # No files exist - create initial package with failing test
            return "create_initial_package"
        
        # Check if we have the specific test file we know how to fix
        if "tests/test_calculator.py" in files:
            # We have the calculator test - check if it needs fixing
            try:
                content = tools.read_file("tests/test_calculator.py")
                if "assert add(2, 3) == 6" in content:
                    return "fix_failing_test"
            except Exception:
                pass
        
        return None
    
    def _execute_action(self, tools: Tools, action: str) -> None:
        """Execute a planned action.
        
        Args:
            tools: Tools instance for workspace operations
            action: Action description string
        """
        if action == "create_initial_package":
            # Create a tiny Python package with a failing test
            tools.write_file("my_package/__init__.py", "# My package\n")
            tools.write_file(
                "my_package/calculator.py",
                "def add(a, b):\n    return a + b\n"
            )
            # Create a test file with an intentional failure
            tools.write_file(
                "tests/test_calculator.py",
                "from my_package.calculator import add\n\n"
                "def test_add():\n"
                "    assert add(2, 3) == 6  # Intentional failure: should be 5\n"
            )
        
        elif action == "fix_failing_test":
            # Apply hardcoded fix for the known failure
            # The test expects 6 but should expect 5
            content = tools.read_file("tests/test_calculator.py")
            # Replace the incorrect assertion
            fixed_content = content.replace("assert add(2, 3) == 6", "assert add(2, 3) == 5")
            tools.write_file("tests/test_calculator.py", fixed_content)
    
    def _clear_cache(self, tools: Tools) -> None:
        """Clear Python and pytest cache directories.
        
        Args:
            tools: Tools instance for workspace operations
        """
        import shutil
        from pathlib import Path
        
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
