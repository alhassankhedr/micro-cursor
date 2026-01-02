"""Tests for tool schema definitions."""

from micro_cursor.tool_schema import get_tool_schemas


def test_schema_includes_all_four_tools():
    """Test that the schema includes all four tool names."""
    schemas = get_tool_schemas()

    tool_names = {schema["function"]["name"] for schema in schemas}

    assert len(schemas) == 4, f"Expected 4 tools, got {len(schemas)}"
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "list_files" in tool_names
    assert "run_cmd" in tool_names


def test_each_tool_has_parameters_object_schema():
    """Test that each tool has a 'parameters' object schema."""
    schemas = get_tool_schemas()

    for schema in schemas:
        assert "function" in schema, f"Schema missing 'function' key: {schema}"
        function = schema["function"]
        assert "parameters" in function, f"Tool {function.get('name')} missing 'parameters'"
        parameters = function["parameters"]
        assert isinstance(parameters, dict), f"Parameters should be a dict, got {type(parameters)}"
        assert parameters.get("type") == "object", (
            f"Parameters type should be 'object', got {parameters.get('type')}"
        )
        assert "properties" in parameters, (
            f"Parameters missing 'properties' for tool {function.get('name')}"
        )


def test_read_file_schema():
    """Test read_file tool schema structure."""
    schemas = get_tool_schemas()
    read_file_schema = next(s for s in schemas if s["function"]["name"] == "read_file")

    assert read_file_schema["type"] == "function"
    function = read_file_schema["function"]
    assert function["name"] == "read_file"
    assert "description" in function
    assert "parameters" in function

    params = function["parameters"]
    assert params["type"] == "object"
    assert "path" in params["properties"]
    assert params["properties"]["path"]["type"] == "string"
    assert "path" in params["required"]


def test_write_file_schema():
    """Test write_file tool schema structure."""
    schemas = get_tool_schemas()
    write_file_schema = next(s for s in schemas if s["function"]["name"] == "write_file")

    assert write_file_schema["type"] == "function"
    function = write_file_schema["function"]
    assert function["name"] == "write_file"
    assert "description" in function

    params = function["parameters"]
    assert params["type"] == "object"
    assert "path" in params["properties"]
    assert "content" in params["properties"]
    assert params["properties"]["path"]["type"] == "string"
    assert params["properties"]["content"]["type"] == "string"
    assert "path" in params["required"]
    assert "content" in params["required"]


def test_list_files_schema():
    """Test list_files tool schema structure."""
    schemas = get_tool_schemas()
    list_files_schema = next(s for s in schemas if s["function"]["name"] == "list_files")

    assert list_files_schema["type"] == "function"
    function = list_files_schema["function"]
    assert function["name"] == "list_files"
    assert "description" in function

    params = function["parameters"]
    assert params["type"] == "object"
    assert "root" in params["properties"]
    assert "pattern" in params["properties"]
    assert params["properties"]["root"]["type"] == "string"
    assert params["properties"]["pattern"]["type"] == "string"
    # root and pattern are optional (have defaults)
    assert "root" not in params.get("required", [])
    assert "pattern" not in params.get("required", [])


def test_run_cmd_schema():
    """Test run_cmd tool schema structure."""
    schemas = get_tool_schemas()
    run_cmd_schema = next(s for s in schemas if s["function"]["name"] == "run_cmd")

    assert run_cmd_schema["type"] == "function"
    function = run_cmd_schema["function"]
    assert function["name"] == "run_cmd"
    assert "description" in function

    params = function["parameters"]
    assert params["type"] == "object"
    assert "cmd" in params["properties"]
    assert "cwd" in params["properties"]
    assert "timeout_sec" in params["properties"]
    assert params["properties"]["cmd"]["type"] == "array"
    assert params["properties"]["cmd"]["items"]["type"] == "string"
    assert params["properties"]["cwd"]["type"] == "string"
    assert params["properties"]["timeout_sec"]["type"] == "integer"
    # cmd is required, cwd and timeout_sec are optional
    assert "cmd" in params["required"]
    assert "cwd" not in params.get("required", [])
    assert "timeout_sec" not in params.get("required", [])


def test_parameter_names_match_tools_methods():
    """Test that parameter names exactly match Tools class method signatures."""
    schemas = get_tool_schemas()

    # read_file(path: str)
    read_file = next(s for s in schemas if s["function"]["name"] == "read_file")
    assert "path" in read_file["function"]["parameters"]["properties"]

    # write_file(path: str, content: str)
    write_file = next(s for s in schemas if s["function"]["name"] == "write_file")
    assert "path" in write_file["function"]["parameters"]["properties"]
    assert "content" in write_file["function"]["parameters"]["properties"]

    # list_files(root: str = ".", pattern: str = "**/*")
    list_files = next(s for s in schemas if s["function"]["name"] == "list_files")
    assert "root" in list_files["function"]["parameters"]["properties"]
    assert "pattern" in list_files["function"]["parameters"]["properties"]

    # run_cmd(cmd: list[str], cwd: str = ".", timeout_sec: int = 60)
    run_cmd = next(s for s in schemas if s["function"]["name"] == "run_cmd")
    assert "cmd" in run_cmd["function"]["parameters"]["properties"]
    assert "cwd" in run_cmd["function"]["parameters"]["properties"]
    assert "timeout_sec" in run_cmd["function"]["parameters"]["properties"]
