# micro-cursor

A Python project for micro-cursor functionality.

## Requirements

- Python 3.13+

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

3. Install the package in editable mode with development dependencies:
```bash
pip install -e ".[dev]"
```

## Usage

Run the CLI:
```bash
python -m micro_cursor --help
```

Run the agent with a goal:
```bash
python -m micro_cursor run --goal "Create a calculator with tests" --workspace "./work"
```

The `--workspace` argument is optional and defaults to `./work`. If the workspace directory doesn't exist, it will be created automatically.

## Example Run

Here's an example of the agent running to create a calculator demo:

```bash
$ python -m micro_cursor run --goal "Create a calculator with tests" --workspace "./demo_work"
Goal: Create a calculator with tests
Workspace: /path/to/demo_work
```

The agent will:
1. **Iteration 1**: Create `calc.py` with a buggy `add()` function (returns `a - b` instead of `a + b`) and `test_calc.py` with correct tests
2. Run pytest and detect the failure:
   ```
   test_calc.py::test_add FAILED
   assert -1 == 5
        +  where -1 = add(2, 3)
   ```
3. **Iteration 2**: Fix the bug in `calc.py` (change `return a - b` to `return a + b`)
4. Run pytest again - tests pass! ✓

The full log is saved to `.agent_log.txt` in the workspace. Here's what it contains:

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

The workspace will contain:
- `calc.py` - The fixed calculator function
- `test_calc.py` - The test file
- `.agent_log.txt` - Full execution log

## Development

Run tests:
```bash
# Activate virtual environment first
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_tools.py -v

# Run a specific test
pytest tests/test_tools.py::test_write_file_then_read_file_roundtrip -v
```

## CI/CD

This project uses GitHub Actions for continuous integration. Tests automatically run on:
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches

The CI workflow tests against:
- Python 3.13 and 3.12
- Ubuntu, macOS, and Windows runners

You can view the workflow status in the "Actions" tab of the GitHub repository.

