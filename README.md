![micro-cursor](micro_cursor_photo.png)

# micro-cursor

A mini Cursor-style agent that uses a ReAct loop to iteratively write code, run tests, and fix bugs until tests pass.

## What it is

**micro-cursor** is a lightweight Python agent that implements a simplified version of the Cursor IDE's autonomous coding loop. Given a goal, it:

1. Uses an LLM (OpenAI or Gemini) to plan the next actions
2. Executes actions using tools (read/write files, run commands)
3. Runs tests to verify correctness
4. If tests fail, analyzes the error and tries again
5. Repeats until tests pass or max iterations reached

It's designed as a proof-of-concept for autonomous code generation and debugging, demonstrating how an agent can iteratively improve code quality through test-driven feedback using LLM-powered reasoning and tool execution.

## How it works

The agent uses a **ReAct (Reasoning + Acting) loop** powered by LLMs:

```
┌─────────────────┐
│  LLM Plans      │  ← LLM analyzes workspace state, goal, and test results
└────────┬────────┘   Uses function calling to decide which tools to use
         │
         ▼
┌─────────────────┐
│ Execute Tools   │  ← Calls tools: read_file, write_file, list_files, run_cmd
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Run Tests      │  ← Execute pytest to verify correctness
└────────┬────────┘
         │
         ├─ Tests Pass? → ✓ Success!
         │
         └─ Tests Fail? → LLM analyzes error → Loop back
```

### Available Tools

The agent has access to four workspace-constrained tools:

- **`read_file(path)`** - Read files from the workspace
- **`write_file(path, content)`** - Write or modify files in the workspace
- **`list_files(root, pattern)`** - List files matching a pattern
- **`run_cmd(cmd, cwd, timeout_sec)`** - Run commands (with safety checks for dangerous operations)

All operations are automatically constrained to the workspace directory for safety.

## Quickstart

### Prerequisites

- Python 3.12+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd micro-cursor
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

3. Install the package:
```bash
pip install -e ".[dev]"
```

### LLM Configuration

micro-cursor supports multiple LLM providers. Configure your preferred provider using environment variables or a `.env` file:

#### Using Environment Variables

**OpenAI (Default):**
```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key-here
export OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
```

**Google Gemini:**
```bash
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your-api-key-here
export GEMINI_MODEL=gemini-2.0-flash-exp  # Optional, defaults to gemini-2.0-flash-exp
```

#### Using .env File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your API keys:
   ```bash
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your-actual-api-key-here
   ```

Get API keys:
- OpenAI: https://platform.openai.com/api-keys
- Gemini: https://aistudio.google.com/apikey

**Note:** The agent requires an LLM API key to function. It uses the LLM for planning actions and generating code fixes.

### Run the Agent

```bash
python -m micro_cursor run --goal "Create a calculator with tests" --workspace "./work"
```

The `--workspace` argument is optional and defaults to `./work`. If the workspace directory doesn't exist, it will be created automatically.

## Demo: Watch it Fail Then Fix

Try the built-in demo to see the agent in action! If you run the agent with a goal about fixing tests in an empty workspace, it will automatically create a broken calculator module and then fix it.

```bash
python -m micro_cursor run --goal "Fix the failing tests in this workspace." --workspace "./work"
```

**What happens:**
1. Agent detects empty workspace and automatically seeds it with:
   - `calc.py` with a buggy `add()` function (returns `a - b` instead of `a + b`)
   - `test_calc.py` with tests that expect correct addition
2. Agent uses LLM to read the files and understand the problem
3. Agent runs pytest - tests fail with assertion error
4. LLM analyzes the test failure and decides to fix the bug
5. Agent writes the corrected `calc.py` file
6. Agent runs pytest again - tests pass! ✓

**Example output:**
```
Goal: Fix the failing tests in this workspace.
Workspace: /path/to/work

=== Iteration 1 ===
Calling LLM...
LLM requested 2 tool call(s)
Tool call 1/2: read_file({'path': 'calc.py'})
Tool call 2/2: read_file({'path': 'test_calc.py'})
Running tests...
Tests failed:
test_calc.py::test_add FAILED
    assert -1 == 5
     +  where -1 = add(2, 3)

=== Iteration 2 ===
Calling LLM...
LLM requested 1 tool call(s)
Tool call 1/1: write_file({'path': 'calc.py', 'content': 'def add(a, b):\n    return a + b\n'})
Running tests...

✓ Tests passed after 2 iteration(s)!
```

## Demo

Here's a complete example run:

```bash
$ python -m micro_cursor run --goal "Create a calculator with tests" --workspace "./demo_work"
Goal: Create a calculator with tests
Workspace: /path/to/demo_work
```

**What happens:**

1. **Iteration 1**: 
   - LLM analyzes the goal and workspace state
   - LLM decides to create `calc.py` with an `add()` function
   - LLM calls `write_file` to create `calc.py` (with a bug: returns `a - b` instead of `a + b`)
   - LLM calls `write_file` to create `test_calc.py` with test expectations
   - LLM calls `run_cmd` to run pytest → **Tests fail:**
     ```
     test_calc.py::test_add FAILED
     assert -1 == 5
          +  where -1 = add(2, 3)
     ```

2. **Iteration 2**:
   - LLM reads the test failure output
   - LLM calls `read_file` to examine `calc.py`
   - LLM identifies the bug and calls `write_file` to fix it (changes `return a - b` to `return a + b`)
   - LLM calls `run_cmd` to run pytest again → **Tests pass! ✓**

**Full log output** (saved to `.agent_log.txt`):

```
Agent run started
Goal: Create a calculator with tests
Workspace: /path/to/demo_work
LLM: OpenAI (gpt-4o-mini)

=== Iteration 1 ===
Calling LLM...
LLM requested 2 tool call(s)
Tool call 1/2: write_file({'path': 'calc.py', 'content': '...'})
Tool call 2/2: write_file({'path': 'test_calc.py', 'content': '...'})
Running tests...
Tests failed:
test_calc.py::test_add FAILED
    assert -1 == 5
     +  where -1 = add(2, 3)

=== Iteration 2 ===
Calling LLM...
LLM requested 2 tool call(s)
Tool call 1/2: read_file({'path': 'calc.py'})
Tool call 2/2: write_file({'path': 'calc.py', 'content': 'def add(a, b):\n    return a + b\n'})
Running tests...

✓ Tests passed after 2 iteration(s)!
```

**Generated files:**
- `calc.py` - The fixed calculator function
- `test_calc.py` - The test file
- `.agent_log.txt` - Full execution log

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Code Quality

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check code quality
ruff check .

# Format code
ruff format .

# Check and format
ruff check . && ruff format .
```

### Run CI Checks Locally

Before pushing to GitHub, you can run the same checks that CI runs to catch errors early:

```bash
# Run all CI checks (linting, formatting, tests, CLI)
./run_ci_checks.sh
```

This script runs:
1. `ruff check .` - Linting
2. `ruff format --check .` - Format check
3. `pytest tests/ -v` - All tests
4. `python -m micro_cursor --help` - CLI verification

**Note:** Make sure you have the package installed in editable mode:
```bash
pip install -e ".[dev]"
```

### Project Structure

```
micro_cursor/
  ├── __init__.py
  ├── __main__.py      # CLI entry point
  ├── cli.py           # Command-line interface
  ├── agent.py         # ReAct loop with LLM integration
  ├── llm.py           # LLM provider abstractions (OpenAI, Gemini)
  ├── tools.py         # Workspace-constrained file operations
  ├── tool_schema.py  # Tool definitions for LLM function calling
  └── workspace.py     # (Future) Workspace management

tests/
  ├── test_smoke.py           # Basic smoke tests
  ├── test_tools.py           # Tools class tests
  ├── test_agent.py            # Agent loop tests
  ├── test_agent_safety.py     # Dangerous command safety tests
  ├── test_llm.py              # LLM client tests
  ├── test_llm_integration.py  # Real API integration tests
  └── test_llm_tool_calling.py  # LLM tool calling tests
```

### Features

- **LLM-Powered Planning**: Uses OpenAI or Gemini for intelligent action planning
- **Tool Calling**: Native function calling support for structured tool execution
- **Safety Features**: Automatic detection and confirmation prompts for dangerous commands
- **Workspace Isolation**: All operations constrained to a workspace directory
- **Test-Driven**: Automatically runs tests and iterates based on failures
- **Cross-Platform**: Works on Linux, macOS, and Windows

### Safety

The agent includes built-in safety features to prevent accidental data loss:

- **Dangerous Command Detection**: Automatically detects potentially harmful commands (e.g., `rm -rf`, `sudo`, `dd`, etc.)
- **User Confirmation**: Prompts for confirmation before executing dangerous commands (in interactive mode)
- **Non-Interactive Safety**: Automatically refuses dangerous commands when running in non-interactive mode (CI/CD)
- **Workspace Constraints**: All file operations are automatically constrained to the workspace directory

See `micro_cursor/tools.py` for the full list of dangerous patterns.

## CI/CD

This project uses GitHub Actions for continuous integration. Tests and code quality checks automatically run on:
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches

The CI workflow:
- Tests against Python 3.13 and 3.12
- Runs on Ubuntu, macOS, and Windows
- Checks code quality with ruff
- Runs all tests with pytest

View workflow status in the "Actions" tab of the GitHub repository.

## License

See [LICENSE](LICENSE) file for details.
