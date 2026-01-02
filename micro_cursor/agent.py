"""Agent module for micro-cursor."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from micro_cursor.llm import ToolCall, get_llm
from micro_cursor.tool_schema import get_tool_schemas
from micro_cursor.tools import Tools

MAX_ITERS = 8
MAX_TOOL_CALLS_PER_ITER = 6
LOG_FILE = ".agent_log.txt"


class Agent:
    """Agent class for micro-cursor functionality."""

    def __init__(self) -> None:
        """Initialize the agent."""
        self.llm = get_llm()
        self.tool_schemas = get_tool_schemas()

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
        log_path = LOG_FILE
        tools.write_file(
            log_path, f"Agent run started\nGoal: {goal}\nWorkspace: {workspace.absolute()}\n\n"
        )

        # Build system prompt
        system_prompt = self._build_system_prompt()

        # Conversation history
        messages: list[dict[str, str]] = []
        last_test_output: str | None = None

        # Perform iterations
        for iteration in range(1, MAX_ITERS + 1):
            self._log(tools, log_path, f"=== Iteration {iteration} ===\n")

            # Get current workspace file list
            try:
                files = tools.list_files()
                # Filter out log file and cache directories
                files = [
                    f
                    for f in files
                    if not f.startswith(".agent_log")
                    and "__pycache__" not in f
                    and ".pytest_cache" not in f
                ]
                file_list = "\n".join(files) if files else "(workspace is empty)"
            except Exception as e:
                file_list = f"Error listing files: {e}"

            # Build user message with context
            user_message = f"Goal: {goal}\n\n"
            user_message += f"Current workspace files:\n{file_list}\n\n"

            if last_test_output:
                user_message += f"Last test output:\n{last_test_output}\n\n"

            # Add log tail (last 20 lines)
            try:
                log_content = tools.read_file(log_path)
                log_lines = log_content.split("\n")
                if len(log_lines) > 20:
                    log_tail = "\n".join(log_lines[-20:])
                    user_message += f"Recent agent log:\n{log_tail}\n"
            except Exception:
                pass

            user_message += (
                "\nWhat should I do next? Use the available tools to work toward the goal."
            )

            messages.append({"role": "user", "content": user_message})

            # Call LLM
            self._log(tools, log_path, "Calling LLM...\n")
            try:
                result = self.llm.next(
                    system=system_prompt, messages=messages, tools=self.tool_schemas
                )
            except Exception as e:
                self._log(tools, log_path, f"LLM call failed: {e}\n")
                messages.append({"role": "assistant", "content": f"Error: {e}"})
                last_test_output = None
                continue

            # Handle LLM response
            if result.tool_calls:
                # Execute tool calls
                self._log(tools, log_path, f"LLM requested {len(result.tool_calls)} tool call(s)\n")
                tool_observations = self._execute_tool_calls(tools, result.tool_calls, log_path)

                # Add assistant message with tool calls
                messages.append({"role": "assistant", "content": result.content_text or ""})

                # Add tool observations (as user messages representing environment feedback)
                for observation in tool_observations:
                    messages.append({"role": "user", "content": f"Observation: {observation}"})

            elif result.content_text:
                # Text response (no tool calls)
                self._log(tools, log_path, f"LLM response: {result.content_text[:200]}...\n")
                messages.append({"role": "assistant", "content": result.content_text})

            # Clear Python cache to ensure file changes are picked up
            self._clear_cache(tools)

            # Always run pytest at end of iteration
            self._log(tools, log_path, "Running tests...\n")
            test_result = tools.run_cmd(
                [sys.executable, "-m", "pytest", "-q", "--cache-clear", "."],
                cwd=".",
                env={"PYTHONPATH": str(workspace.absolute())},
            )

            test_output = test_result["stdout"] + test_result["stderr"]
            last_test_output = test_output

            if test_result["returncode"] == 0:
                # Tests passed!
                self._log(tools, log_path, f"\n✓ Tests passed after {iteration} iteration(s)!\n")
                self._log(tools, log_path, f"Success summary: Goal '{goal}' achieved.\n")
                return 0
            else:
                # Tests failed
                self._log(tools, log_path, f"Tests failed:\n{test_output}\n")
                # Add test output as observation for next iteration
                messages.append({"role": "user", "content": f"Test output:\n{test_output}"})

        # Max iterations reached
        self._log(
            tools, log_path, f"\n✗ Max iterations ({MAX_ITERS}) reached. Goal not achieved.\n"
        )
        return 1

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM.

        Returns:
            System prompt string
        """
        return """You are micro-cursor, a coding agent that helps achieve coding goals.

You have access to the following tools:
- read_file(path): Read a file from the workspace
- write_file(path, content): Write content to a file in the workspace
- list_files(root, pattern): List files in the workspace matching a pattern
- run_cmd(cmd, cwd, timeout_sec): Run a command and capture stdout/stderr

IMPORTANT RULES:
1. You MUST stay inside the workspace directory. All file operations are automatically constrained to the workspace.
2. You MUST call tools instead of pretending you ran commands or edited files. Use the actual tool functions.
3. You should iterate until pytest passes or you hit the maximum number of iterations.
4. When tests fail, read the error messages carefully and fix the issues.
5. You can read files to understand the current state, write files to create or modify code, and run commands to test.
6. Always use the tools - do not describe what you would do, actually do it by calling the tools.

Your goal is to help achieve the user's coding goal by using these tools effectively."""

    def _execute_tool_calls(self, tools: Tools, tool_calls: list, log_path: str) -> list[str]:
        """Execute tool calls and return observations.

        Args:
            tools: Tools instance for workspace operations
            tool_calls: List of ToolCall objects
            log_path: Path to log file

        Returns:
            List of observation strings
        """
        if len(tool_calls) > MAX_TOOL_CALLS_PER_ITER:
            self._log(
                tools,
                log_path,
                f"Warning: {len(tool_calls)} tool calls requested, limiting to {MAX_TOOL_CALLS_PER_ITER}\n",
            )
            tool_calls = tool_calls[:MAX_TOOL_CALLS_PER_ITER]

        observations = []

        for i, tool_call in enumerate(tool_calls):
            self._log(
                tools,
                log_path,
                f"Tool call {i + 1}/{len(tool_calls)}: {tool_call.name}({tool_call.arguments})\n",
            )

            try:
                # Validate and execute tool call
                observation = self._execute_single_tool(tools, tool_call)
                observations.append(observation)
                self._log(tools, log_path, f"  Result: {observation[:200]}...\n")
            except Exception as e:
                error_msg = f"Error executing {tool_call.name}: {e}"
                observations.append(error_msg)
                self._log(tools, log_path, f"  Error: {error_msg}\n")

        return observations

    def _execute_single_tool(self, tools: Tools, tool_call: ToolCall) -> str:
        """Execute a single tool call.

        Args:
            tools: Tools instance for workspace operations
            tool_call: ToolCall object

        Returns:
            Observation string
        """
        name = tool_call.name
        args = tool_call.arguments

        # Validate argument types
        if name == "read_file":
            if not isinstance(args.get("path"), str):
                raise ValueError(
                    f"read_file: 'path' must be a string, got {type(args.get('path'))}"
                )
            result = tools.read_file(args["path"])
            return f"File '{args['path']}' contents:\n{result}"

        elif name == "write_file":
            if not isinstance(args.get("path"), str):
                raise ValueError(
                    f"write_file: 'path' must be a string, got {type(args.get('path'))}"
                )
            if not isinstance(args.get("content"), str):
                raise ValueError(
                    f"write_file: 'content' must be a string, got {type(args.get('content'))}"
                )
            tools.write_file(args["path"], args["content"])
            return f"Successfully wrote {len(args['content'])} characters to '{args['path']}'"

        elif name == "list_files":
            root = args.get("root", ".")
            pattern = args.get("pattern", "**/*")
            if not isinstance(root, str):
                raise ValueError(f"list_files: 'root' must be a string, got {type(root)}")
            if not isinstance(pattern, str):
                raise ValueError(f"list_files: 'pattern' must be a string, got {type(pattern)}")
            files = tools.list_files(root, pattern)
            return (
                f"Found {len(files)} file(s):\n" + "\n".join(files) if files else "No files found"
            )

        elif name == "run_cmd":
            cmd = args.get("cmd")
            if not isinstance(cmd, list):
                raise ValueError(f"run_cmd: 'cmd' must be a list, got {type(cmd)}")
            if not all(isinstance(item, str) for item in cmd):
                raise ValueError("run_cmd: 'cmd' must be a list of strings")
            cwd = args.get("cwd", ".")
            timeout_sec = args.get("timeout_sec", 60)
            if not isinstance(cwd, str):
                raise ValueError(f"run_cmd: 'cwd' must be a string, got {type(cwd)}")
            if not isinstance(timeout_sec, int):
                raise ValueError(
                    f"run_cmd: 'timeout_sec' must be an integer, got {type(timeout_sec)}"
                )
            result = tools.run_cmd(cmd, cwd=cwd, timeout_sec=timeout_sec)
            return f"Command returned {result['returncode']}:\nstdout: {result['stdout']}\nstderr: {result['stderr']}"

        else:
            raise ValueError(f"Unknown tool: {name}")

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
