"""Entry point for running micro_cursor as a module."""

from __future__ import annotations

from pathlib import Path

# Load .env file if it exists (before importing cli to ensure env vars are available)
try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback if python-dotenv is not installed
    import os

    def load_dotenv(dotenv_path=None):
        """Fallback .env loader if python-dotenv is not available."""
        if dotenv_path is None:
            project_root = Path(__file__).parent.parent
            dotenv_path = project_root / ".env"
        else:
            dotenv_path = Path(dotenv_path)

        if dotenv_path.exists():
            with open(dotenv_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        if key and key not in os.environ:
                            os.environ[key] = value


# Load .env file from project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)

from micro_cursor.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
