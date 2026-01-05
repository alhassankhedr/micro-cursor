# micro-cursor

A mini Cursor-style agent that uses a ReAct loop to iteratively write code, run tests, and fix bugs until tests pass.

## What it is

**micro-cursor** is a lightweight Python agent that implements a simplified version of the Cursor IDE's autonomous coding loop. Given a goal, it:

1. Plans the next action
2. Executes the action (writes/modifies code)
3. Runs tests
4. If tests fail, analyzes the error and tries again
5. Repeats until tests pass or max iterations reached

It's designed as a proof-of-concept for autonomous code generation and debugging, demonstrating how an agent can iteratively improve code quality through test-driven feedback.

## How it works

The agent uses a **ReAct (Reasoning + Acting) loop**:

```
┌─────────────────┐
│  Plan Action    │  ← Analyze current state, decide what to do
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Execute Action  │  ← Write/modify code files
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Run Tests      │  ← Execute pytest to verify correctness
└────────┬────────┘
         │
         ├─ Tests Pass? → ✓ Success!
         │
         └─ Tests Fail? → Analyze error → Loop back
```

**Current Implementation (Day 1):**
- Simple hardcoded planning logic
- Creates `calc.py` with a buggy function
- Detects the bug from test failures
- Applies a hardcoded fix
- Verifies the fix with pytest

**Future (Day 2+):**
- LLM-powered planning and code generation
- Dynamic error analysis
- Multi-file codebase understanding
- Context-aware fixes

## Quickstart

### Prerequisites

- Python 3.13+

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

micro-cursor supports multiple LLM providers. Configure your preferred provider using environment variables:

#### OpenAI (Default)

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key-here
export OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
```

Get your API key at: https://platform.openai.com/api-keys

#### Google Gemini

```bash
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your-api-key-here
export GEMINI_MODEL=gemini-2.0-flash-exp  # Optional, defaults to gemini-2.0-flash-exp
```

Get your API key at: https://aistudio.google.com/apikey

**Note:** The agent will only use the LLM when making planning decisions. If no API keys are set, the agent will use hardcoded logic (Day 1 mode).

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
1. Agent detects empty workspace and creates `calc.py` with a buggy `add()` function (returns `a - b` instead of `a + b`)
2. Agent creates `test_calc.py` with tests that expect correct addition
3. Agent runs pytest - tests fail with assertion error
4. Agent uses LLM to analyze the failure and fix the bug
5. Agent runs pytest again - tests pass! ✓

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
   - Creates `calc.py` with a buggy `add()` function (returns `a - b` instead of `a + b`)
   - Creates `test_calc.py` with correct test expectations
   - Runs pytest → **Tests fail:**
     ```
     test_calc.py::test_add FAILED
     assert -1 == 5
          +  where -1 = add(2, 3)
     ```

2. **Iteration 2**:
   - Detects the bug in `calc.py`
   - Fixes it (changes `return a - b` to `return a + b`)
   - Runs pytest → **Tests pass! ✓**

**Full log output** (saved to `.agent_log.txt`):

```
Agent run started
Goal: Create a calculator with tests
Workspace: /path/to/demo_work

=== Iteration 1 ===
Action: create_calc_demo
Running tests...
Tests failed:
test_calc.py::test_add FAILED
assert -1 == 5
     +  where -1 = add(2, 3)

=== Iteration 2 ===
Action: fix_calc_bug
Running tests...

✓ Tests passed after 2 iteration(s)!
Success summary: Goal 'Create a calculator with tests' achieved.
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
  ├── agent.py         # ReAct loop implementation
  ├── tools.py         # Workspace-constrained file operations
  └── workspace.py     # (Future) Workspace management

tests/
  ├── test_smoke.py    # Basic smoke tests
  ├── test_tools.py    # Tools class tests
  └── test_agent.py    # Agent loop tests
```

## Roadmap

### Day 2+ Ideas

- **LLM Integration**: Replace hardcoded planning with LLM-powered reasoning
  - Use OpenAI/Anthropic APIs for planning and code generation
  - Context-aware error analysis from test failures
  - Multi-step planning for complex goals

- **Enhanced Planning**:
  - Parse test failures to understand what needs fixing
  - Generate code patches instead of hardcoded fixes
  - Support multiple files and dependencies

- **Workspace Understanding**:
  - Parse existing codebase structure
  - Understand imports and dependencies
  - Track file changes across iterations

- **Better Error Handling**:
  - Handle import errors, syntax errors, type errors
  - Retry with different strategies
  - Learn from past failures

- **Extended Tooling**:
  - Git operations (commit, branch, diff)
  - Dependency management (pip, poetry)
  - Multi-language support

- **Observability**:
  - Better logging and progress tracking
  - Visualization of the agent's decision process
  - Metrics and performance tracking

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
