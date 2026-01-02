"""Pytest configuration and fixtures."""

from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback if python-dotenv is not installed
    import os

    def load_dotenv():
        """Fallback .env loader if python-dotenv is not available."""
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"

        if env_file.exists():
            with open(env_file) as f:
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


def pytest_configure(config):
    """Load .env file before tests run."""
    # Load .env file from project root
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"

    if env_file.exists():
        load_dotenv(env_file)
