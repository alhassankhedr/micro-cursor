"""LLM client module for micro-cursor."""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

try:
    from google import genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM clients."""

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        """Complete a conversation with the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (default: 0.2)

        Returns:
            The LLM's response as a string
        """
        ...


class MockLLMClient:
    """Mock LLM client for testing - returns deterministic responses."""

    def __init__(self, response: str = "create_calc_demo"):
        """Initialize the mock client.

        Args:
            response: The fixed response to return (default: "create_calc_demo")
        """
        self.response = response

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        """Return a deterministic mock response.

        Args:
            messages: List of message dicts (ignored in mock)
            temperature: Sampling temperature (ignored in mock)

        Returns:
            The predefined mock response
        """
        return self.response


class OpenAIClient:
    """OpenAI client using the official openai-python library."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name (defaults to OPENAI_MODEL env var or "gpt-4o-mini")

        Raises:
            ImportError: If openai package is not installed
            ValueError: If API key is missing
        """
        if OpenAI is None:
            raise ImportError(
                "openai package is required for OpenAI client. Install it with: pip install openai"
            )

        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Set it to your OpenAI API key. Get one at https://platform.openai.com/api-keys"
            )

        self.client = OpenAI(api_key=self.api_key)

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        """Complete a conversation with OpenAI.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (default: 0.2)

        Returns:
            The LLM's response content as a string

        Raises:
            Exception: If the API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(
                f"OpenAI API call failed: {e}. Check your API key and network connection."
            ) from e


class GeminiClient:
    """Google Gemini client using the google-genai library."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize the Gemini client.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model name (defaults to GEMINI_MODEL env var or "gemini-2.0-flash-exp")

        Raises:
            ImportError: If google-genai package is not installed
            ValueError: If API key is missing
        """
        if genai is None:
            raise ImportError(
                "google-genai package is required for Gemini client. "
                "Install it with: pip install google-genai"
            )

        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Set it to your Gemini API key. Get one at https://aistudio.google.com/apikey"
            )

        self.client = genai.Client(api_key=self.api_key)

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        """Complete a conversation with Gemini.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (default: 0.2)

        Returns:
            The LLM's response content as a string

        Raises:
            Exception: If the API call fails
        """
        try:
            # Convert messages to Gemini format
            # For simple single-user messages, just use the text
            # For multi-turn, convert to Content format
            if len(messages) == 1 and messages[0].get("role") == "user":
                # Simple case: just pass the text content
                contents = messages[0].get("content", "")
            else:
                # Multi-turn: convert to Content format
                # Gemini uses Content objects with role and parts
                contents = []
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        # User message: use string or Content format
                        contents.append({"role": "user", "parts": [{"text": content}]})
                    elif role == "assistant":
                        # Assistant message: use Content format
                        contents.append({"role": "model", "parts": [{"text": content}]})

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config={"temperature": temperature},
            )
            return response.text
        except Exception as e:
            raise RuntimeError(
                f"Gemini API call failed: {e}. Check your API key and network connection."
            ) from e


def get_llm_client() -> LLMClient:
    """Get an LLM client based on environment configuration.

    Reads LLM_PROVIDER env var to determine which client to use:
    - "openai" -> OpenAIClient
    - "gemini" -> GeminiClient
    - default -> OpenAIClient

    Returns:
        An LLMClient instance

    Raises:
        ValueError: If provider is invalid or required config is missing
        ImportError: If required package is not installed
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        return OpenAIClient()
    elif provider == "gemini":
        return GeminiClient()
    else:
        raise ValueError(
            f"Invalid LLM_PROVIDER: {provider}. "
            "Must be 'openai' or 'gemini'. "
            f"Current value: {os.getenv('LLM_PROVIDER', 'not set')}"
        )
