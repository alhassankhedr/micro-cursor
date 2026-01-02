"""Tool schema definitions for LLM function calling."""

from __future__ import annotations


def get_tool_schemas() -> list[dict]:
    """Get provider-neutral JSON schemas for all available tools.

    Returns:
        List of tool schema dictionaries in OpenAI function calling format.
        Each schema includes name, description, and parameters JSON schema.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file from the workspace. Returns the contents of the file as a string.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file (relative to workspace or absolute within workspace)",
                        },
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file in the workspace. Creates parent directories if needed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file (relative to workspace or absolute within workspace)",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files in the workspace matching a pattern. Excludes .venv, __pycache__, .git directories.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "root": {
                            "type": "string",
                            "description": "Root directory to search from (relative to workspace). Default: '.'",
                            "default": ".",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to match files. Default: '**/*' for all files",
                            "default": "**/*",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_cmd",
                "description": "Run a command and capture stdout/stderr. Returns a dictionary with returncode, stdout, and stderr.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cmd": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Command to run as a list of strings (e.g., ['python', '-m', 'pytest'])",
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Working directory (relative to workspace or absolute within workspace). Default: '.'",
                            "default": ".",
                        },
                        "timeout_sec": {
                            "type": "integer",
                            "description": "Timeout in seconds. Default: 60",
                            "default": 60,
                        },
                    },
                    "required": ["cmd"],
                },
            },
        },
    ]
