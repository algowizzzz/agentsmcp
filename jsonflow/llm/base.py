"""Provider interface. Providers only make the call; schema validation and
repair retries live in the engine so every provider behaves the same."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from jsonflow.errors import LLMError

ANTHROPIC_DEFAULT_MODEL = "claude-opus-5-5"


def default_provider() -> str:
    """Provider when neither the node nor the workflow names one."""
    return os.getenv("JSONFLOW_LLM_PROVIDER", "anthropic")


def default_model(provider: str) -> str:
    """Model when neither the node nor the workflow names one."""
    model = os.getenv("JSONFLOW_LLM_MODEL")
    if model:
        return model
    if provider == "anthropic":
        return ANTHROPIC_DEFAULT_MODEL
    raise LLMError(f"set JSONFLOW_LLM_MODEL (or 'model' on the node) for provider {provider!r}")


@dataclass
class LLMRequest:
    node_id: str
    prompt: str
    model: str
    system: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 4096
    output_schema: Optional[dict[str, Any]] = None


@dataclass
class LLMResponse:
    data: Any = None  # parsed object when output_schema was set
    text: Optional[str] = None
    model: str = ""
    usage: dict[str, Any] = field(default_factory=dict)
    stop_reason: Optional[str] = None


class LLMProvider(Protocol):
    name: str

    def complete(self, request: LLMRequest) -> LLMResponse: ...


def build_provider(name: str, **kw: Any) -> LLMProvider:
    if name == "anthropic":
        from jsonflow.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(**kw)
    if name == "openai_compat":
        from jsonflow.llm.openai_compat import OpenAICompatProvider

        return OpenAICompatProvider(**kw)
    if name == "scripted":
        from jsonflow.llm.scripted import ScriptedProvider

        return ScriptedProvider(**kw)
    if name == "facade":
        from jsonflow.llm.facade_provider import FacadeProvider

        return FacadeProvider(**kw)
    raise LLMError(f"unknown LLM provider {name!r}; available: anthropic, openai_compat, scripted, facade")
