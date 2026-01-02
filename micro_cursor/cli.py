"""Command-line interface for micro-cursor."""

import argparse
import sys


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
    
    args = parser.parse_args()
    return 0


if __name__ == "__main__":
    sys.exit(main())

