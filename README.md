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
python -m micro_cursor run --goal "Create a hello world script" --workspace "./work"
```

The `--workspace` argument is optional and defaults to `./work`. If the workspace directory doesn't exist, it will be created automatically.

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

