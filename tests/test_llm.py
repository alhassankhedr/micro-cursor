"""Tests for micro_cursor.llm module."""

import os
from unittest.mock import Mock, patch

import pytest

from micro_cursor.llm import (
    GeminiClient,
    LLMClient,
    MockLLMClient,
    OpenAIClient,
    get_llm_client,
)


def test_mock_llm_client_returns_expected_content():
    """Test that MockLLMClient returns the expected deterministic content."""
    client = MockLLMClient(response="create_calc_demo")

    messages = [{"role": "user", "content": "What should I do?"}]
    result = client.complete(messages, temperature=0.5)

    assert result == "create_calc_demo"
    assert isinstance(client, LLMClient)


def test_mock_llm_client_custom_response():
    """Test MockLLMClient with custom response."""
    client = MockLLMClient(response="fix_calc_bug")

    messages = [{"role": "user", "content": "Fix the bug"}]
    result = client.complete(messages)

    assert result == "fix_calc_bug"


def test_openai_client_missing_api_key():
    """Test that OpenAIClient raises error when API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
            OpenAIClient()


def test_openai_client_with_api_key():
    """Test that OpenAIClient works with API key provided."""
    with patch("micro_cursor.llm.OpenAI") as mock_openai:
        client = OpenAIClient(api_key="test-key", model="gpt-4o-mini")

        assert client.api_key == "test-key"
        assert client.model == "gpt-4o-mini"
        mock_openai.assert_called_once_with(api_key="test-key")


def test_openai_client_from_env_vars():
    """Test that OpenAIClient reads from environment variables."""
    env_vars = {
        "OPENAI_API_KEY": "test-key",
        "OPENAI_MODEL": "gpt-4o",
    }

    with patch.dict(os.environ, env_vars):
        with patch("micro_cursor.llm.OpenAI"):
            client = OpenAIClient()

            assert client.api_key == "test-key"
            assert client.model == "gpt-4o"


def test_openai_client_default_model():
    """Test that OpenAIClient defaults to gpt-4o-mini."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
        with patch("micro_cursor.llm.OpenAI"):
            client = OpenAIClient()

            assert client.model == "gpt-4o-mini"


@patch("micro_cursor.llm.OpenAI")
def test_openai_client_complete_success(mock_openai_class):
    """Test successful completion call to OpenAIClient."""
    # Mock the client and its response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client

    client = OpenAIClient(api_key="test-key", model="gpt-4o-mini")

    messages = [{"role": "user", "content": "Hello"}]
    result = client.complete(messages, temperature=0.3)

    assert result == "Test response"
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini", messages=messages, temperature=0.3
    )


def test_gemini_client_missing_api_key():
    """Test that GeminiClient raises error when API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("micro_cursor.llm.genai"):
            with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
                GeminiClient()


def test_gemini_client_with_api_key():
    """Test that GeminiClient works with API key provided."""
    with patch("micro_cursor.llm.genai") as mock_genai:
        mock_genai.Client.return_value = Mock()
        client = GeminiClient(api_key="test-key", model="gemini-2.0-flash-exp")

        assert client.api_key == "test-key"
        assert client.model == "gemini-2.0-flash-exp"
        mock_genai.Client.assert_called_once_with(api_key="test-key")


def test_gemini_client_from_env_vars():
    """Test that GeminiClient reads from environment variables."""
    env_vars = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL": "gemini-pro",
    }

    with patch.dict(os.environ, env_vars):
        with patch("micro_cursor.llm.genai") as mock_genai:
            mock_genai.Client.return_value = Mock()
            client = GeminiClient()

            assert client.api_key == "test-key"
            assert client.model == "gemini-pro"


def test_gemini_client_default_model():
    """Test that GeminiClient defaults to gemini-2.0-flash-exp."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True):
        with patch("micro_cursor.llm.genai") as mock_genai:
            mock_genai.Client.return_value = Mock()
            client = GeminiClient()

            assert client.model == "gemini-2.0-flash-exp"


@patch("micro_cursor.llm.genai")
def test_gemini_client_complete_success(mock_genai):
    """Test successful completion call to GeminiClient."""
    # Mock the client and its response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.text = "Test response"
    mock_client.models.generate_content.return_value = mock_response
    mock_genai.Client.return_value = mock_client

    client = GeminiClient(api_key="test-key", model="gemini-2.0-flash-exp")

    messages = [{"role": "user", "content": "Hello"}]
    result = client.complete(messages, temperature=0.3)

    assert result == "Test response"
    mock_client.models.generate_content.assert_called_once()


def test_get_llm_client_openai():
    """Test get_llm_client returns OpenAIClient for openai provider."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"}):
        with patch("micro_cursor.llm.OpenAI"):
            client = get_llm_client()
            assert isinstance(client, OpenAIClient)


def test_get_llm_client_gemini():
    """Test get_llm_client returns GeminiClient for gemini provider."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"}):
        with patch("micro_cursor.llm.genai") as mock_genai:
            mock_genai.Client.return_value = Mock()
            client = get_llm_client()
            assert isinstance(client, GeminiClient)


def test_get_llm_client_defaults_to_openai():
    """Test get_llm_client defaults to openai when LLM_PROVIDER not set."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
        with patch("micro_cursor.llm.OpenAI"):
            client = get_llm_client()
            assert isinstance(client, OpenAIClient)


def test_get_llm_client_invalid_provider():
    """Test get_llm_client raises error for invalid provider."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "invalid"}):
        with pytest.raises(ValueError, match="Invalid LLM_PROVIDER"):
            get_llm_client()


def test_import_works_without_keys():
    """Test that importing micro_cursor.llm works even if keys are missing."""
    # This should not raise an error
    from micro_cursor import llm  # noqa: F401

    assert llm is not None
