"""Tools module for micro-cursor."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class DangerousCommandError(Exception):
    """Exception raised when a dangerous command is detected."""

    def __init__(self, command: str, reason: str = "dangerous_command_detected"):
        """Initialize the exception.

        Args:
            command: The full command string that was flagged
            reason: Reason for blocking the command
        """
        self.command = command
        self.reason = reason
        super().__init__(f"Dangerous command detected: {command}")


# Dangerous command patterns that require user confirmation
DANGEROUS_PATTERNS = [
    "rm -rf",
    "rm -r /",
    "rm -rf /",
    "sudo",
    "mkfs",
    "dd if=",
    "shutdown",
    "reboot",
    ":(){:|:&};:",  # Fork bomb
    "chmod -R 777 /",
    "chown -R",
    "wipefs",
    "mount /",
    "umount /",
    "format",
    "fdisk",
    "parted",
    "mkfs.ext",
    "mkfs.ntfs",
    "mkfs.vfat",
    "dd of=",
    "> /dev/sd",
    "> /dev/hd",
]


class Tools:
    """Tools class for micro-cursor functionality with workspace-constrained operations."""

    def __init__(self, workspace_path: str):
        """Initialize the tools with a workspace path.

        Args:
            workspace_path: Path to the workspace directory. All file operations
                          will be constrained to this directory.
        """
        self.workspace_path = Path(workspace_path).resolve()
        if not self.workspace_path.exists():
            self.workspace_path.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: str) -> Path:
        """Validate that a path is within the workspace directory.

        Args:
            path: Path to validate (can be relative or absolute)

        Returns:
            Resolved Path object within workspace

        Raises:
            ValueError: If the path is outside the workspace directory
        """
        # Resolve the path relative to workspace
        if os.path.isabs(path):
            resolved = Path(path).resolve()
        else:
            resolved = (self.workspace_path / path).resolve()

        # Ensure the resolved path is within workspace
        try:
            resolved.relative_to(self.workspace_path)
        except ValueError as err:
            raise ValueError(
                f"Path {path} is outside workspace directory {self.workspace_path}"
            ) from err

        return resolved

    def read_file(self, path: str) -> str:
        """Read a file from the workspace.

        Args:
            path: Path to the file (relative to workspace or absolute within workspace)

        Returns:
            Contents of the file as a string

        Raises:
            ValueError: If path is outside workspace
            FileNotFoundError: If file doesn't exist
        """
        file_path = self._validate_path(path)
        return file_path.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> None:
        """Write content to a file in the workspace.

        Args:
            path: Path to the file (relative to workspace or absolute within workspace)
            content: Content to write to the file

        Raises:
            ValueError: If path is outside workspace
        """
        file_path = self._validate_path(path)
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def list_files(self, root: str = ".", pattern: str = "**/*") -> list[str]:
        """List files in the workspace matching a pattern.

        Args:
            root: Root directory to search from (relative to workspace)
            pattern: Glob pattern to match files (default: "**/*" for all files)

        Returns:
            List of file paths (relative to workspace), excluding .venv, __pycache__, .git

        Raises:
            ValueError: If root is outside workspace
        """
        root_path = self._validate_path(root)

        # Patterns to exclude
        exclude_patterns = {".venv", "__pycache__", ".git"}

        files = []
        for file_path in root_path.glob(pattern):
            if file_path.is_file():
                # Check if any part of the path matches exclude patterns
                parts = file_path.parts
                if not any(part in exclude_patterns for part in parts):
                    # Return path relative to workspace
                    try:
                        rel_path = file_path.relative_to(self.workspace_path)
                        files.append(str(rel_path))
                    except ValueError:
                        # Should not happen due to validation, but handle gracefully
                        continue

        return sorted(files)

    def _check_dangerous_command(self, cmd: list[str]) -> None:
        """Check if a command matches any dangerous pattern.

        Args:
            cmd: Command to check as a list of strings

        Raises:
            DangerousCommandError: If a dangerous pattern is detected
        """
        # Convert command list to string for inspection
        cmd_str = " ".join(cmd).lower()

        # Check against dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if pattern.lower() in cmd_str:
                raise DangerousCommandError(" ".join(cmd), "dangerous_command_detected")

    def run_cmd(
        self,
        cmd: list[str],
        cwd: str = ".",
        timeout_sec: int = 60,
        env: dict[str, str] | None = None,
        skip_safety_check: bool = False,
    ) -> dict[str, int | str]:
        """Run a command and capture stdout/stderr.

        Args:
            cmd: Command to run as a list of strings
            cwd: Working directory (relative to workspace or absolute within workspace)
            timeout_sec: Timeout in seconds (default: 60)
            env: Optional environment variables dict (default: None, uses current env)
            skip_safety_check: If True, skip dangerous command check (for internal use only)

        Returns:
            Dictionary with keys: returncode (int), stdout (str), stderr (str).
            On timeout, returncode will be -1 and stderr will contain timeout message.

        Raises:
            ValueError: If cwd is outside workspace
            DangerousCommandError: If a dangerous command is detected and not confirmed
        """
        # Check for dangerous commands (unless explicitly skipped)
        if not skip_safety_check:
            self._check_dangerous_command(cmd)

        cwd_path = self._validate_path(cwd)

        # Prepare environment
        if env is None:
            run_env = None
        else:
            run_env = os.environ.copy()
            run_env.update(env)

        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd_path),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                env=run_env,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired as e:
            # When text=True, stdout/stderr are already strings, but they might be None
            stdout = e.stdout if e.stdout else ""
            stderr = e.stderr if e.stderr else f"Command timed out after {timeout_sec} seconds"
            return {"returncode": -1, "stdout": stdout, "stderr": stderr}
