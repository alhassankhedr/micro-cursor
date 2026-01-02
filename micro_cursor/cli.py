"""Command-line interface for micro-cursor."""

import argparse
import os
import sys
from pathlib import Path

from micro_cursor.agent import Agent


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="micro-cursor - A Python project for micro-cursor functionality"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the agent with a goal")
    run_parser.add_argument(
        "--goal",
        required=True,
        help="The goal to achieve"
    )
    run_parser.add_argument(
        "--workspace",
        default="./work",
        help="Path to the workspace directory (default: ./work)"
    )
    
    args = parser.parse_args()
    
    if args.command == "run":
        return run_command(args.goal, args.workspace)
    elif args.command is None:
        parser.print_help()
        return 0
    else:
        parser.print_help()
        return 1


def run_command(goal: str, workspace_path: str) -> int:
    """Execute the run command."""
    # Create workspace if it doesn't exist
    workspace = Path(workspace_path)
    if not workspace.exists():
        workspace.mkdir(parents=True, exist_ok=True)
    
    # Print goal and workspace path
    print(f"Goal: {goal}")
    print(f"Workspace: {workspace.absolute()}")
    
    # Call agent.run() and return its exit code
    agent = Agent()
    return agent.run(goal, str(workspace.absolute()))


if __name__ == "__main__":
    sys.exit(main())

