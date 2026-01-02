"""Tools module for micro-cursor."""

import os
import subprocess
from pathlib import Path
from typing import Dict, List


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
        except ValueError:
            raise ValueError(f"Path {path} is outside workspace directory {self.workspace_path}")
        
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
        return file_path.read_text(encoding='utf-8')
    
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
        file_path.write_text(content, encoding='utf-8')
    
    def list_files(self, root: str = ".", pattern: str = "**/*") -> List[str]:
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
    
    def run_cmd(self, cmd: List[str], cwd: str = ".", timeout_sec: int = 60) -> Dict[str, int | str]:
        """Run a command and capture stdout/stderr.
        
        Args:
            cmd: Command to run as a list of strings
            cwd: Working directory (relative to workspace or absolute within workspace)
            timeout_sec: Timeout in seconds (default: 60)
            
        Returns:
            Dictionary with keys: returncode (int), stdout (str), stderr (str).
            On timeout, returncode will be -1 and stderr will contain timeout message.
            
        Raises:
            ValueError: If cwd is outside workspace
        """
        cwd_path = self._validate_path(cwd)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd_path),
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired as e:
            # When text=True, stdout/stderr are already strings, but they might be None
            stdout = e.stdout if e.stdout else ""
            stderr = e.stderr if e.stderr else f"Command timed out after {timeout_sec} seconds"
            return {
                "returncode": -1,
                "stdout": stdout,
                "stderr": stderr
            }
