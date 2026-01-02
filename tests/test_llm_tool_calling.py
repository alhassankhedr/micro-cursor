"""Tests for LLM tool calling functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from micro_cursor.agent import Agent
from micro_cursor.llm import GeminiLLM, LLMResult, OpenAILLM, ToolCall


class TestOpenAIToolCalling:
    """Tests for OpenAI tool calling."""

    @patch("micro_cursor.llm.OpenAI")
    def test_openai_returns_tool_call_write_file(self, mock_openai_class):
        """Test OpenAI returns a write_file tool call."""
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = None

        # Mock tool call for write_file
        mock_tool_call = Mock()
        mock_tool_call.function.name = "write_file"
        mock_tool_call.function.arguments = '{"path": "test.txt", "content": "Hello, world!"}'
        mock_message.tool_calls = [mock_tool_call]

        mock_response.choices = [Mock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        llm = OpenAILLM(api_key="test-key", model="gpt-4o-mini")

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["path", "content"],
                    },
                },
            }
        ]

        result = llm.next(
            system="You are a helpful assistant",
            messages=[{"role": "user", "content": "Write 'Hello, world!' to test.txt"}],
            tools=tools,
        )

        assert isinstance(result, LLMResult)
        assert result.content_text is None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "write_file"
        assert result.tool_calls[0].arguments == {"path": "test.txt", "content": "Hello, world!"}

        # Verify tools were passed to API
        call_args = mock_client.chat.completions.create.call_args
        assert "tools" in call_args.kwargs
        assert call_args.kwargs["tool_choice"] == "auto"

    @patch("micro_cursor.llm.OpenAI")
    def test_openai_returns_text_when_no_tool_calls(self, mock_openai_class):
        """Test OpenAI returns text when no tool calls are requested."""
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "I'll help you with that."
        mock_message.tool_calls = None
        mock_response.choices = [Mock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        llm = OpenAILLM(api_key="test-key", model="gpt-4o-mini")

        result = llm.next(
            system="You are a helpful assistant",
            messages=[{"role": "user", "content": "Hello"}],
            tools=None,
        )

        assert isinstance(result, LLMResult)
        assert result.content_text == "I'll help you with that."
        assert result.tool_calls == []

    @patch("micro_cursor.llm.OpenAI")
    def test_openai_multiple_tool_calls(self, mock_openai_class):
        """Test OpenAI returns multiple tool calls."""
        mock_client = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = None

        # Mock multiple tool calls
        mock_tool_call1 = Mock()
        mock_tool_call1.function.name = "read_file"
        mock_tool_call1.function.arguments = '{"path": "file1.txt"}'

        mock_tool_call2 = Mock()
        mock_tool_call2.function.name = "read_file"
        mock_tool_call2.function.arguments = '{"path": "file2.txt"}'

        mock_message.tool_calls = [mock_tool_call1, mock_tool_call2]
        mock_response.choices = [Mock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        llm = OpenAILLM(api_key="test-key", model="gpt-4o-mini")

        result = llm.next(
            system="You are a helpful assistant",
            messages=[{"role": "user", "content": "Read file1.txt and file2.txt"}],
            tools=[],
        )

        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].name == "read_file"
        assert result.tool_calls[0].arguments == {"path": "file1.txt"}
        assert result.tool_calls[1].name == "read_file"
        assert result.tool_calls[1].arguments == {"path": "file2.txt"}


class TestGeminiToolCalling:
    """Tests for Gemini tool calling."""

    @patch("micro_cursor.llm.genai")
    def test_gemini_returns_tool_call_write_file(self, mock_genai):
        """Test Gemini returns a write_file tool call."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = None

        # Mock function call part
        mock_function_call = Mock()
        mock_function_call.name = "write_file"
        mock_function_call.args = {"path": "test.txt", "content": "Hello, world!"}

        mock_part = Mock()
        mock_part.function_call = mock_function_call
        mock_part.text = None

        mock_candidate = Mock()
        mock_candidate.content.parts = [mock_part]

        mock_response.candidates = [mock_candidate]
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        llm = GeminiLLM(api_key="test-key", model="gemini-2.0-flash-exp")

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                    },
                },
            }
        ]

        result = llm.next(
            system="You are a helpful assistant",
            messages=[{"role": "user", "content": "Write 'Hello, world!' to test.txt"}],
            tools=tools,
        )

        assert isinstance(result, LLMResult)
        assert result.content_text is None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "write_file"
        assert result.tool_calls[0].arguments == {"path": "test.txt", "content": "Hello, world!"}

    @patch("micro_cursor.llm.genai")
    def test_gemini_returns_text_when_no_tool_calls(self, mock_genai):
        """Test Gemini returns text when no tool calls are requested."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "I'll help you with that."
        mock_response.candidates = []
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        llm = GeminiLLM(api_key="test-key", model="gemini-2.0-flash-exp")

        result = llm.next(
            system="You are a helpful assistant",
            messages=[{"role": "user", "content": "Hello"}],
            tools=None,
        )

        assert isinstance(result, LLMResult)
        assert result.content_text == "I'll help you with that."
        assert result.tool_calls == []

    @patch("micro_cursor.llm.genai")
    def test_gemini_multiple_tool_calls(self, mock_genai):
        """Test Gemini returns multiple tool calls."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = None

        # Mock multiple function call parts
        mock_function_call1 = Mock()
        mock_function_call1.name = "read_file"
        mock_function_call1.args = {"path": "file1.txt"}

        mock_function_call2 = Mock()
        mock_function_call2.name = "read_file"
        mock_function_call2.args = {"path": "file2.txt"}

        mock_part1 = Mock()
        mock_part1.function_call = mock_function_call1
        mock_part1.text = None

        mock_part2 = Mock()
        mock_part2.function_call = mock_function_call2
        mock_part2.text = None

        mock_candidate = Mock()
        mock_candidate.content.parts = [mock_part1, mock_part2]

        mock_response.candidates = [mock_candidate]
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        llm = GeminiLLM(api_key="test-key", model="gemini-2.0-flash-exp")

        result = llm.next(
            system="You are a helpful assistant",
            messages=[{"role": "user", "content": "Read file1.txt and file2.txt"}],
            tools=[],
        )

        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].name == "read_file"
        assert result.tool_calls[0].arguments == {"path": "file1.txt"}
        assert result.tool_calls[1].name == "read_file"
        assert result.tool_calls[1].arguments == {"path": "file2.txt"}


class TestAgentToolExecution:
    """Tests for agent executing tool calls from LLM."""

    def test_agent_executes_write_file_tool_call(self):
        """Test that agent executes a write_file tool call from LLM."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("micro_cursor.agent.get_llm") as mock_get_llm:
                mock_llm = Mock()

                # First call: LLM returns write_file tool call
                mock_llm.next.return_value = LLMResult(
                    content_text=None,
                    tool_calls=[
                        ToolCall(
                            name="write_file",
                            arguments={"path": "hello.txt", "content": "Hello, World!"},
                        )
                    ],
                )
                mock_get_llm.return_value = mock_llm

                agent = Agent()
                # Create a test file so pytest passes
                workspace = Path(tmpdir)
                (workspace / "test_pass.py").write_text("def test_pass():\n    assert True\n")

                agent.run("Create hello.txt with 'Hello, World!'", tmpdir)

                # Verify file was created by the tool call
                hello_file = workspace / "hello.txt"
                assert hello_file.exists()
                assert hello_file.read_text() == "Hello, World!"

                # Verify agent logged the tool call
                log_file = workspace / ".agent_log.txt"
                log_content = log_file.read_text()
                assert "write_file" in log_content
                assert "hello.txt" in log_content

    def test_agent_executes_multiple_tool_calls(self):
        """Test that agent executes multiple tool calls in sequence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("micro_cursor.agent.get_llm") as mock_get_llm:
                mock_llm = Mock()
                call_count = 0

                def mock_next(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1

                    if call_count == 1:
                        # First call: write two files
                        return LLMResult(
                            content_text=None,
                            tool_calls=[
                                ToolCall(
                                    name="write_file",
                                    arguments={"path": "file1.txt", "content": "Content 1"},
                                ),
                                ToolCall(
                                    name="write_file",
                                    arguments={"path": "file2.txt", "content": "Content 2"},
                                ),
                            ],
                        )
                    else:
                        # Subsequent calls: no more actions
                        return LLMResult(content_text="Done", tool_calls=[])

                mock_llm.next.side_effect = mock_next
                mock_get_llm.return_value = mock_llm

                agent = Agent()
                # Create a test file so pytest passes
                workspace = Path(tmpdir)
                (workspace / "test_pass.py").write_text("def test_pass():\n    assert True\n")

                agent.run("Create file1.txt and file2.txt", tmpdir)

                # Verify both files were created
                assert (workspace / "file1.txt").exists()
                assert (workspace / "file1.txt").read_text() == "Content 1"
                assert (workspace / "file2.txt").exists()
                assert (workspace / "file2.txt").read_text() == "Content 2"

    def test_agent_executes_read_file_tool_call(self):
        """Test that agent executes a read_file tool call from LLM."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            # Create a file to read
            (workspace / "existing.txt").write_text("Existing content")

            with patch("micro_cursor.agent.get_llm") as mock_get_llm:
                mock_llm = Mock()

                # LLM returns read_file tool call
                mock_llm.next.return_value = LLMResult(
                    content_text=None,
                    tool_calls=[
                        ToolCall(name="read_file", arguments={"path": "existing.txt"}),
                    ],
                )
                mock_get_llm.return_value = mock_llm

                agent = Agent()
                # Create a test file so pytest passes
                (workspace / "test_pass.py").write_text("def test_pass():\n    assert True\n")

                agent.run("Read existing.txt", tmpdir)

                # Verify the file was read (check log for observation)
                log_file = workspace / ".agent_log.txt"
                log_content = log_file.read_text()
                assert "read_file" in log_content
                assert "existing.txt" in log_content
                assert "Existing content" in log_content

    def test_agent_executes_list_files_tool_call(self):
        """Test that agent executes a list_files tool call from LLM."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            # Create some files
            (workspace / "file1.txt").write_text("Content 1")
            (workspace / "file2.txt").write_text("Content 2")

            with patch("micro_cursor.agent.get_llm") as mock_get_llm:
                mock_llm = Mock()

                # LLM returns list_files tool call
                mock_llm.next.return_value = LLMResult(
                    content_text=None,
                    tool_calls=[
                        ToolCall(name="list_files", arguments={"root": ".", "pattern": "*.txt"}),
                    ],
                )
                mock_get_llm.return_value = mock_llm

                agent = Agent()
                # Create a test file so pytest passes
                (workspace / "test_pass.py").write_text("def test_pass():\n    assert True\n")

                agent.run("List all .txt files", tmpdir)

                # Verify list_files was called (check log for observation)
                log_file = workspace / ".agent_log.txt"
                log_content = log_file.read_text()
                assert "list_files" in log_content
                assert "file1.txt" in log_content or "file2.txt" in log_content

    def test_agent_executes_run_cmd_tool_call(self):
        """Test that agent executes a run_cmd tool call from LLM."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            with patch("micro_cursor.agent.get_llm") as mock_get_llm:
                mock_llm = Mock()

                # LLM returns run_cmd tool call
                mock_llm.next.return_value = LLMResult(
                    content_text=None,
                    tool_calls=[
                        ToolCall(
                            name="run_cmd",
                            arguments={"cmd": ["echo", "Hello from tool"], "cwd": "."},
                        ),
                    ],
                )
                mock_get_llm.return_value = mock_llm

                agent = Agent()
                # Create a test file so pytest passes
                (workspace / "test_pass.py").write_text("def test_pass():\n    assert True\n")

                agent.run("Run echo command", tmpdir)

                # Verify run_cmd was called (check log for observation)
                log_file = workspace / ".agent_log.txt"
                log_content = log_file.read_text()
                assert "run_cmd" in log_content
                assert "Hello from tool" in log_content
