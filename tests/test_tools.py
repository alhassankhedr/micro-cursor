"""Tests for micro_cursor.tools module."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

from micro_cursor.tools import Tools


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def tools(temp_workspace):
    """Create a Tools instance with a temporary workspace."""
    return Tools(temp_workspace)


def test_write_file_then_read_file_roundtrip(tools, temp_workspace):
    """Test that write_file followed by read_file works correctly."""
    test_path = "test_file.txt"
    test_content = "Hello, World!\nThis is a test file."
    
    # Write file
    tools.write_file(test_path, test_content)
    
    # Read file
    content = tools.read_file(test_path)
    
    assert content == test_content
    assert Path(temp_workspace) / test_path == Path(temp_workspace) / test_path


def test_list_files_excludes_pycache(tools, temp_workspace):
    """Test that list_files excludes __pycache__ directories."""
    # Create some files
    tools.write_file("file1.txt", "content1")
    tools.write_file("file2.py", "content2")
    tools.write_file("subdir/file3.txt", "content3")
    
    # Create __pycache__ directory and file
    pycache_dir = Path(temp_workspace) / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "file.cpython-313.pyc").touch()
    
    # Create .venv directory
    venv_dir = Path(temp_workspace) / ".venv"
    venv_dir.mkdir()
    (venv_dir / "file.txt").touch()
    
    # Create .git directory
    git_dir = Path(temp_workspace) / ".git"
    git_dir.mkdir()
    (git_dir / "config").touch()
    
    # List files
    files = tools.list_files()
    
    # Should include regular files but not __pycache__, .venv, or .git
    assert "file1.txt" in files
    assert "file2.py" in files
    assert "subdir/file3.txt" in files
    assert "__pycache__/file.cpython-313.pyc" not in files
    assert ".venv/file.txt" not in files
    assert ".git/config" not in files


def test_list_files_with_pattern(tools):
    """Test list_files with a specific pattern."""
    tools.write_file("file1.txt", "content1")
    tools.write_file("file2.py", "content2")
    tools.write_file("file3.txt", "content3")
    
    # List only .txt files
    txt_files = tools.list_files(pattern="*.txt")
    
    assert "file1.txt" in txt_files
    assert "file3.txt" in txt_files
    assert "file2.py" not in txt_files


def test_run_cmd_simple_python_command(tools):
    """Test that run_cmd can run a simple python -c command successfully."""
    result = tools.run_cmd(
        [sys.executable, "-c", "print('Hello from Python')"],
        cwd="."
    )
    
    assert result["returncode"] == 0
    assert "Hello from Python" in result["stdout"]
    assert result["stderr"] == ""


def test_run_cmd_with_error(tools):
    """Test run_cmd with a command that fails."""
    result = tools.run_cmd(
        [sys.executable, "-c", "import sys; sys.exit(1)"],
        cwd="."
    )
    
    assert result["returncode"] == 1


def test_write_file_outside_workspace_raises_error(tools, temp_workspace):
    """Test that write_file raises ValueError for paths outside workspace."""
    # Try to write to a path outside workspace using ../
    with pytest.raises(ValueError, match="outside workspace"):
        tools.write_file("../outside_file.txt", "content")


def test_read_file_outside_workspace_raises_error(tools):
    """Test that read_file raises ValueError for paths outside workspace."""
    with pytest.raises(ValueError, match="outside workspace"):
        tools.read_file("../outside_file.txt")


def test_list_files_outside_workspace_raises_error(tools):
    """Test that list_files raises ValueError for root outside workspace."""
    with pytest.raises(ValueError, match="outside workspace"):
        tools.list_files(root="../outside")


def test_run_cmd_outside_workspace_raises_error(tools):
    """Test that run_cmd raises ValueError for cwd outside workspace."""
    with pytest.raises(ValueError, match="outside workspace"):
        tools.run_cmd(["echo", "test"], cwd="../outside")


def test_write_file_creates_parent_directories(tools):
    """Test that write_file creates parent directories if they don't exist."""
    tools.write_file("deep/nested/path/file.txt", "content")
    
    content = tools.read_file("deep/nested/path/file.txt")
    assert content == "content"


def test_list_files_in_subdirectory(tools):
    """Test list_files from a subdirectory."""
    tools.write_file("root_file.txt", "content1")
    tools.write_file("subdir/file1.txt", "content2")
    tools.write_file("subdir/file2.txt", "content3")
    
    files = tools.list_files(root="subdir")
    # Files are returned relative to workspace, not the subdirectory root
    assert "subdir/file1.txt" in files
    assert "subdir/file2.txt" in files
    assert "root_file.txt" not in files

