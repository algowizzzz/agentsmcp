"""Provider interface. Providers only make the call; schema validation and
repair retries live in the engine so every provider behaves the same."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from jsonflow.errors import LLMError

DEFAULT_PROVIDER = os.getenv("JSONFLOW_LLM_PROVIDER", "anthropic")
DEFAULT_MODEL = os.getenv("JSONFLOW_LLM_MODEL", "claude-opus-5-5")


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
    if name == "scripted":
        from jsonflow.llm.scripted import ScriptedProvider

        return ScriptedProvider(**kw)
    if name == "facade":
        from jsonflow.llm.facade_provider import FacadeProvider

        return FacadeProvider(**kw)
    raise LLMError(f"unknown LLM provider {name!r}; available: anthropic, scripted, facade")
