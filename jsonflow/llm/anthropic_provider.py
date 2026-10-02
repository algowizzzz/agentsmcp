"""Anthropic Messages API provider.

Structured output uses a single forced tool whose input_schema is the node's
output_schema, so the model must return an object of that shape.
"""
from __future__ import annotations

from typing import Any, Optional

from jsonflow.errors import LLMError
from jsonflow.llm.base import LLMRequest, LLMResponse

_OUTPUT_TOOL = "submit_output"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, client: Optional[Any] = None, timeout: float = 120.0) -> None:
        if client is None:
            try:
                import anthropic
            except ImportError as e:  # pragma: no cover - depends on env
                raise LLMError("the 'anthropic' package is not installed") from e
            client = anthropic.Anthropic(timeout=timeout, max_retries=2)
        self._client = client

    def complete(self, request: LLMRequest) -> LLMResponse:
        messages = [{"role": "user", "content": request.prompt}]
        kwargs: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": messages,
        }
        if request.system:
            kwargs["system"] = request.system
        if request.output_schema is not None:
            kwargs["tools"] = [
                {
                    "name": _OUTPUT_TOOL,
                    "description": "Return the final answer. Always call this tool exactly once.",
                    "input_schema": request.output_schema,
                }
            ]
            kwargs["tool_choice"] = {"type": "tool", "name": _OUTPUT_TOOL}
        try:
            msg = self._client.messages.create(**kwargs)
        except Exception as e:  # SDK raises several error types; surface them uniformly
            raise LLMError(f"anthropic call failed: {e}") from e

        usage = {}
        if getattr(msg, "usage", None) is not None:
            usage = {
                "input_tokens": getattr(msg.usage, "input_tokens", None),
                "output_tokens": getattr(msg.usage, "output_tokens", None),
            }
        text_parts, data = [], None
        for block in msg.content:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(block.text)
            elif btype == "tool_use" and block.name == _OUTPUT_TOOL:
                data = block.input
        if request.output_schema is not None and data is None:
            raise LLMError(f"model did not return structured output (stop_reason={msg.stop_reason})")
        return LLMResponse(
            data=data,
            text="".join(text_parts) or None,
            model=getattr(msg, "model", request.model),
            usage=usage,
            stop_reason=getattr(msg, "stop_reason", None),
        )
