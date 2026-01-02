"""Integration tests for LLM clients (requires real API keys)."""

import os
import pytest

from micro_cursor.llm import GeminiClient, OpenAIClient, get_llm_client


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set"
)
def test_openai_client_real_api_call():
    """Test OpenAI client with real API call."""
    client = OpenAIClient()

    messages = [
        {"role": "user", "content": "Say 'Hello, this is a test' and nothing else."}
    ]

    response = client.complete(messages, temperature=0.1)

    assert response is not None
    assert len(response) > 0
    assert "test" in response.lower() or "hello" in response.lower()
    print(f"\nOpenAI Response: {response}")


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set"
)
def test_gemini_client_real_api_call():
    """Test Gemini client with real API call."""
    import time

    client = GeminiClient()

    messages = [
        {"role": "user", "content": "Say 'Hello, this is a test' and nothing else."}
    ]

    try:
        response = client.complete(messages, temperature=0.1)

        assert response is not None
        assert len(response) > 0
        assert "test" in response.lower() or "hello" in response.lower()
        print(f"\nGemini Response: {response}")
    except RuntimeError as e:
        # Handle quota/rate limit errors gracefully
        if "429" in str(e) or "quota" in str(e).lower() or "RESOURCE_EXHAUSTED" in str(e):
            pytest.skip(f"Gemini API quota exceeded (this is expected on free tier): {e}")
        else:
            raise


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set"
)
def test_get_llm_client_openai_integration():
    """Test get_llm_client factory with OpenAI (real API)."""
    with pytest.MonkeyPatch().context() as m:
        m.setenv("LLM_PROVIDER", "openai")
        client = get_llm_client()

        assert isinstance(client, OpenAIClient)

        messages = [{"role": "user", "content": "Reply with just: OK"}]
        response = client.complete(messages, temperature=0.1)

        assert response is not None
        assert len(response) > 0
        print(f"\nFactory OpenAI Response: {response}")


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set"
)
def test_get_llm_client_gemini_integration():
    """Test get_llm_client factory with Gemini (real API)."""
    with pytest.MonkeyPatch().context() as m:
        m.setenv("LLM_PROVIDER", "gemini")
        client = get_llm_client()

        assert isinstance(client, GeminiClient)

        messages = [{"role": "user", "content": "Reply with just: OK"}]
        try:
            response = client.complete(messages, temperature=0.1)

            assert response is not None
            assert len(response) > 0
            print(f"\nFactory Gemini Response: {response}")
        except RuntimeError as e:
            # Handle quota/rate limit errors gracefully
            if "429" in str(e) or "quota" in str(e).lower() or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip(f"Gemini API quota exceeded (this is expected on free tier): {e}")
            else:
                raise

