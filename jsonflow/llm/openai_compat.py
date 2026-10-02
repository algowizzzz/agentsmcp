"""Provider for any OpenAI-compatible Chat Completions endpoint.

Works with OpenAI, Azure OpenAI, vLLM, Ollama, LiteLLM, LM Studio, the
HuggingFace router, xAI and similar servers. Plain HTTP via httpx, so no
extra SDK is needed.

Configuration (environment):
    OPENAI_COMPAT_BASE_URL   e.g. https://api.openai.com/v1 or http://localhost:8000/v1
    OPENAI_COMPAT_API_KEY    bearer token; optional for local servers
    OPENAI_COMPAT_STRUCTURED tools | json_schema | json   (default: tools)
    OPENAI_COMPAT_HEADERS    optional JSON object of extra headers, e.g. {"api-key": "..."} for Azure

Structured output modes, for nodes with an output_schema:
    tools        force a single function call whose parameters are the schema (widest support)
    json_schema  response_format json_schema (OpenAI, recent vLLM)
    json         response_format json_object plus the schema in the prompt (most permissive)
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx

from jsonflow.errors import LLMError
from jsonflow.llm.base import LLMRequest, LLMResponse

_FN = "submit_output"
_MODES = ("tools", "json_schema", "json")


def _strip_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return s.strip()


class OpenAICompatProvider:
    name = "openai_compat"

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        structured: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 120.0,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("OPENAI_COMPAT_BASE_URL") or "").rstrip("/")
        if not self.base_url:
            raise LLMError("openai_compat provider needs OPENAI_COMPAT_BASE_URL (for example https://api.openai.com/v1)")
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_COMPAT_API_KEY", "")
        self.structured = structured or os.getenv("OPENAI_COMPAT_STRUCTURED", "tools")
        if self.structured not in _MODES:
            raise LLMError(f"OPENAI_COMPAT_STRUCTURED must be one of {_MODES}")
        extra = headers if headers is not None else json.loads(os.getenv("OPENAI_COMPAT_HEADERS") or "{}")
        self.headers = {"Content-Type": "application/json", **extra}
        if self.api_key:
            self.headers.setdefault("Authorization", f"Bearer {self.api_key}")
        self._http = httpx.Client(timeout=timeout, transport=transport)

    def _body(self, request: LLMRequest) -> dict[str, Any]:
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        prompt = request.prompt
        schema = request.output_schema
        if schema is not None and self.structured == "json":
            prompt += ("\n\nRespond with only a JSON object, no prose and no code fences, "
                       f"matching this JSON Schema:\n{json.dumps(schema)}")
        messages.append({"role": "user", "content": prompt})
        body: dict[str, Any] = {"model": request.model, "messages": messages,
                                "temperature": request.temperature, "max_tokens": request.max_tokens}
        if schema is not None:
            if self.structured == "tools":
                body["tools"] = [{"type": "function", "function": {
                    "name": _FN, "description": "Return the final answer. Always call this exactly once.",
                    "parameters": schema}}]
                body["tool_choice"] = {"type": "function", "function": {"name": _FN}}
            elif self.structured == "json_schema":
                body["response_format"] = {"type": "json_schema",
                                           "json_schema": {"name": _FN, "schema": schema}}
            else:
                body["response_format"] = {"type": "json_object"}
        return body

    def complete(self, request: LLMRequest) -> LLMResponse:
        try:
            r = self._http.post(f"{self.base_url}/chat/completions", headers=self.headers, json=self._body(request))
        except httpx.HTTPError as e:
            raise LLMError(f"openai_compat call failed: {e}") from e
        if r.status_code != 200:
            raise LLMError(f"openai_compat returned HTTP {r.status_code}: {r.text[:300]}")
        try:
            payload = r.json()
            choice = payload["choices"][0]
            message = choice["message"]
        except (ValueError, KeyError, IndexError, TypeError) as e:
            raise LLMError(f"openai_compat returned an unexpected body: {r.text[:300]}") from e

        usage = payload.get("usage") or {}
        usage = {"input_tokens": usage.get("prompt_tokens"), "output_tokens": usage.get("completion_tokens")}
        text = message.get("content") or None
        model = payload.get("model", request.model)
        stop = choice.get("finish_reason")
        if request.output_schema is None:
            return LLMResponse(text=text, model=model, usage=usage, stop_reason=stop)

        raw: Optional[str] = None
        if self.structured == "tools":
            for call in message.get("tool_calls") or []:
                fn = call.get("function") or {}
                if fn.get("name") == _FN:
                    raw = fn.get("arguments")
                    break
            if raw is None:
                raise LLMError(f"model did not call {_FN} (finish_reason={stop})")
        else:
            raw = text
        if isinstance(raw, dict):  # a few servers return parsed arguments
            return LLMResponse(data=raw, text=text, model=model, usage=usage, stop_reason=stop)
        try:
            data = json.loads(_strip_fences(raw or ""))
        except json.JSONDecodeError as e:
            raise LLMError(f"model output is not valid JSON: {(raw or '')[:200]}") from e
        return LLMResponse(data=data, text=text, model=model, usage=usage, stop_reason=stop)
