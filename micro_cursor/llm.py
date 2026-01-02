"""LLM client module for micro-cursor."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

try:
    from google import genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class ToolCall(BaseModel):
    """Represents a tool/function call from the LLM."""

    name: str
    arguments: dict


class LLMResult(BaseModel):
    """Result from an LLM call."""

    content_text: str | None = None
    tool_calls: list[ToolCall] = []


class LLM(ABC):
    """Provider-agnostic LLM interface."""

    @abstractmethod
    def next(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
    ) -> LLMResult:
        """Get the next response from the LLM.

        Args:
            system: System prompt/instructions
            messages: List of message dicts with 'role' and 'content' keys
            tools: Optional list of tool/function definitions for function calling

        Returns:
            LLMResult containing either text content or tool calls
        """
        ...


class OpenAILLM(LLM):
    """OpenAI LLM implementation."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize the OpenAI LLM.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name (defaults to OPENAI_MODEL env var or "gpt-4o-mini")

        Raises:
            ImportError: If openai package is not installed
            ValueError: If API key is missing
        """
        if OpenAI is None:
            raise ImportError(
                "openai package is required for OpenAI LLM. Install it with: pip install openai"
            )

        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Set it to your OpenAI API key. Get one at https://platform.openai.com/api-keys"
            )

        self.client = OpenAI(api_key=self.api_key)

    def next(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
    ) -> LLMResult:
        """Get the next response from OpenAI.

        Args:
            system: System prompt/instructions
            messages: List of message dicts with 'role' and 'content' keys
            tools: Optional list of tool/function definitions

        Returns:
            LLMResult containing either text content or tool calls
        """
        try:
            # Build messages with system prompt
            all_messages = [{"role": "system", "content": system}] + messages

            # Prepare API call parameters
            params = {
                "model": self.model,
                "messages": all_messages,
                "temperature": 0.2,
            }

            # Add tools if provided
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**params)

            message = response.choices[0].message

            # Check for tool calls
            if message.tool_calls:
                tool_calls = []
                for tool_call in message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            name=tool_call.function.name,
                            arguments=json.loads(tool_call.function.arguments),
                        )
                    )
                return LLMResult(content_text=None, tool_calls=tool_calls)

            # Return text content
            return LLMResult(content_text=message.content or "", tool_calls=[])

        except Exception as e:
            raise RuntimeError(
                f"OpenAI API call failed: {e}. Check your API key and network connection."
            ) from e


class GeminiLLM(LLM):
    """Google Gemini LLM implementation."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize the Gemini LLM.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model name (defaults to GEMINI_MODEL env var or "gemini-2.0-flash-exp")

        Raises:
            ImportError: If google-genai package is not installed
            ValueError: If API key is missing
        """
        if genai is None:
            raise ImportError(
                "google-genai package is required for Gemini LLM. "
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

    def next(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
    ) -> LLMResult:
        """Get the next response from Gemini.

        Args:
            system: System prompt/instructions
            messages: List of message dicts with 'role' and 'content' keys
            tools: Optional list of tool/function definitions

        Returns:
            LLMResult containing either text content or tool calls
        """
        try:
            # Build contents with system prompt
            # Gemini uses a different format - system instruction goes in config
            contents = []

            # Convert messages to Gemini format
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    contents.append({"role": "user", "parts": [{"text": content}]})
                elif role == "assistant":
                    contents.append({"role": "model", "parts": [{"text": content}]})

            # Prepare config
            config = {
                "temperature": 0.2,
                "system_instruction": system,
            }

            # Add tools if provided (Gemini function calling)
            if tools:
                # Convert tools to Gemini format
                gemini_tools = []
                for tool in tools:
                    gemini_tools.append(
                        {
                            "function_declarations": [
                                {
                                    "name": tool.get("function", {}).get("name", ""),
                                    "description": tool.get("function", {}).get("description", ""),
                                    "parameters": tool.get("function", {}).get("parameters", {}),
                                }
                            ]
                        }
                    )
                config["tools"] = gemini_tools

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

            # Check for function calls in Gemini response
            # Gemini returns function calls in response.candidates[0].content.parts
            tool_calls = []
            text_parts = []

            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            # Function call detected
                            func_call = part.function_call
                            args = {}
                            if hasattr(func_call, "args"):
                                # Convert args to dict if it's a dict-like object
                                if isinstance(func_call.args, dict):
                                    args = func_call.args
                                elif hasattr(func_call.args, "__dict__"):
                                    args = func_call.args.__dict__
                            tool_calls.append(
                                ToolCall(
                                    name=func_call.name if hasattr(func_call, "name") else "",
                                    arguments=args,
                                )
                            )
                        elif hasattr(part, "text") and part.text:
                            text_parts.append(part.text)

            # If we have tool calls, return them
            if tool_calls:
                return LLMResult(content_text=None, tool_calls=tool_calls)

            # Return text content (from parts or response.text)
            text_content = "".join(text_parts) if text_parts else (response.text or "")
            return LLMResult(content_text=text_content, tool_calls=[])

        except Exception as e:
            raise RuntimeError(
                f"Gemini API call failed: {e}. Check your API key and network connection."
            ) from e


def get_llm() -> LLM:
    """Get an LLM instance based on environment configuration.

    Reads LLM_PROVIDER env var to determine which provider to use:
    - "openai" -> OpenAILLM
    - "gemini" -> GeminiLLM
    - default -> OpenAILLM

    Returns:
        An LLM instance

    Raises:
        ValueError: If provider is invalid or required config is missing
        ImportError: If required package is not installed
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        return OpenAILLM()
    elif provider == "gemini":
        return GeminiLLM()
    else:
        raise ValueError(
            f"Invalid LLM_PROVIDER: {provider}. "
            "Must be 'openai' or 'gemini'. "
            f"Current value: {os.getenv('LLM_PROVIDER', 'not set')}"
        )


# Legacy classes for backward compatibility (deprecated)
class MockLLMClient:
    """Mock LLM client for testing - returns deterministic responses.

    Deprecated: Use MockLLM instead.
    """

    def __init__(self, response: str = "create_calc_demo"):
        """Initialize the mock client."""
        self.response = response

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        """Return a deterministic mock response."""
        return self.response


class OpenAIClient:
    """OpenAI client (legacy).

    Deprecated: Use OpenAILLM instead.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize the OpenAI client."""
        self._llm = OpenAILLM(api_key=api_key, model=model)
        self.api_key = self._llm.api_key
        self.model = self._llm.model
        self.client = self._llm.client

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        """Complete a conversation with OpenAI."""
        result = self._llm.next(system="", messages=messages)
        return result.content_text or ""


class GeminiClient:
    """Gemini client (legacy).

    Deprecated: Use GeminiLLM instead.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize the Gemini client."""
        self._llm = GeminiLLM(api_key=api_key, model=model)
        self.api_key = self._llm.api_key
        self.model = self._llm.model
        self.client = self._llm.client

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        """Complete a conversation with Gemini."""
        result = self._llm.next(system="", messages=messages)
        return result.content_text or ""


def get_llm_client():
    """Get an LLM client (legacy).

    Deprecated: Use get_llm() instead.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        return OpenAIClient()
    elif provider == "gemini":
        return GeminiClient()
    else:
        raise ValueError(f"Invalid LLM_PROVIDER: {provider}. Must be 'openai' or 'gemini'.")


# Protocol for backward compatibility
@runtime_checkable
class LLMClient(Protocol):
    """Legacy protocol for backward compatibility."""

    def complete(self, messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
        """Complete a conversation with the LLM."""
        ...
