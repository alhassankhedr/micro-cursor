"""Tests for the new LLM interface."""

import os
from unittest.mock import Mock, patch

import pytest

from micro_cursor.llm import LLM, GeminiLLM, LLMResult, OpenAILLM, ToolCall, get_llm


def test_llm_result_with_text():
    """Test LLMResult with text content."""
    result = LLMResult(content_text="Hello, world!", tool_calls=[])

    assert result.content_text == "Hello, world!"
    assert result.tool_calls == []
    assert result.model_dump() == {
        "content_text": "Hello, world!",
        "tool_calls": [],
    }


def test_llm_result_with_tool_calls():
    """Test LLMResult with tool calls."""
    tool_call = ToolCall(name="read_file", arguments={"path": "test.txt"})
    result = LLMResult(content_text=None, tool_calls=[tool_call])

    assert result.content_text is None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "read_file"
    assert result.tool_calls[0].arguments == {"path": "test.txt"}


def test_tool_call_model():
    """Test ToolCall model."""
    tool_call = ToolCall(name="write_file", arguments={"path": "file.txt", "content": "data"})

    assert tool_call.name == "write_file"
    assert tool_call.arguments == {"path": "file.txt", "content": "data"}


def test_openai_llm_missing_api_key():
    """Test OpenAILLM raises error when API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            OpenAILLM()


def test_openai_llm_with_api_key():
    """Test OpenAILLM initialization."""
    with patch("micro_cursor.llm.OpenAI") as mock_openai:
        llm = OpenAILLM(api_key="test-key", model="gpt-4o-mini")

        assert llm.api_key == "test-key"
        assert llm.model == "gpt-4o-mini"
        mock_openai.assert_called_once_with(api_key="test-key")


@patch("micro_cursor.llm.OpenAI")
def test_openai_llm_next_text_response(mock_openai_class):
    """Test OpenAILLM.next() returns text response."""
    mock_client = Mock()
    mock_response = Mock()
    mock_message = Mock()
    mock_message.content = "Test response"
    mock_message.tool_calls = None
    mock_response.choices = [Mock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client

    llm = OpenAILLM(api_key="test-key", model="gpt-4o-mini")

    result = llm.next(
        system="You are a helpful assistant",
        messages=[{"role": "user", "content": "Hello"}],
    )

    assert isinstance(result, LLMResult)
    assert result.content_text == "Test response"
    assert result.tool_calls == []


@patch("micro_cursor.llm.OpenAI")
def test_openai_llm_next_tool_calls(mock_openai_class):
    """Test OpenAILLM.next() returns tool calls."""
    mock_client = Mock()
    mock_response = Mock()
    mock_message = Mock()
    mock_message.content = None
    mock_tool_call = Mock()
    mock_tool_call.function.name = "read_file"
    mock_tool_call.function.arguments = '{"path": "test.txt"}'
    mock_message.tool_calls = [mock_tool_call]
    mock_response.choices = [Mock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client

    llm = OpenAILLM(api_key="test-key", model="gpt-4o-mini")

    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]

    result = llm.next(
        system="You are a helpful assistant",
        messages=[{"role": "user", "content": "Read test.txt"}],
        tools=tools,
    )

    assert isinstance(result, LLMResult)
    assert result.content_text is None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "read_file"
    assert result.tool_calls[0].arguments == {"path": "test.txt"}


def test_gemini_llm_missing_api_key():
    """Test GeminiLLM raises error when API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("micro_cursor.llm.genai"):
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                GeminiLLM()


def test_gemini_llm_with_api_key():
    """Test GeminiLLM initialization."""
    with patch("micro_cursor.llm.genai") as mock_genai:
        mock_genai.Client.return_value = Mock()
        llm = GeminiLLM(api_key="test-key", model="gemini-2.0-flash-exp")

        assert llm.api_key == "test-key"
        assert llm.model == "gemini-2.0-flash-exp"


@patch("micro_cursor.llm.genai")
def test_gemini_llm_next_text_response(mock_genai):
    """Test GeminiLLM.next() returns text response."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.text = "Test response"
    mock_response.candidates = []
    mock_client.models.generate_content.return_value = mock_response
    mock_genai.Client.return_value = mock_client

    llm = GeminiLLM(api_key="test-key", model="gemini-2.0-flash-exp")

    result = llm.next(
        system="You are a helpful assistant",
        messages=[{"role": "user", "content": "Hello"}],
    )

    assert isinstance(result, LLMResult)
    assert result.content_text == "Test response"
    assert result.tool_calls == []


def test_get_llm_openai():
    """Test get_llm() returns OpenAILLM for openai provider."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"}):
        with patch("micro_cursor.llm.OpenAI"):
            llm = get_llm()
            assert isinstance(llm, OpenAILLM)
            assert isinstance(llm, LLM)


def test_get_llm_gemini():
    """Test get_llm() returns GeminiLLM for gemini provider."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"}):
        with patch("micro_cursor.llm.genai") as mock_genai:
            mock_genai.Client.return_value = Mock()
            llm = get_llm()
            assert isinstance(llm, GeminiLLM)
            assert isinstance(llm, LLM)


def test_get_llm_defaults_to_openai():
    """Test get_llm() defaults to openai when LLM_PROVIDER not set."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
        with patch("micro_cursor.llm.OpenAI"):
            llm = get_llm()
            assert isinstance(llm, OpenAILLM)


def test_get_llm_invalid_provider():
    """Test get_llm() raises error for invalid provider."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "invalid"}):
        with pytest.raises(ValueError, match="Invalid LLM_PROVIDER"):
            get_llm()
