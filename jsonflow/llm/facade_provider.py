"""Adapter to this repo's multi-provider ``llm.llm_facade.LLMFacade``.

Lets llm nodes use OpenAI, Google, Bedrock and the other providers already
configured in ``config/llm/llm.json``. Set ``provider: "facade"`` and
``model: "<facade_provider>/<facade_model>"`` on the node.
"""
from __future__ import annotations

from typing import Any

from jsonflow.errors import LLMError
from jsonflow.llm.base import LLMRequest, LLMResponse


class FacadeProvider:
    name = "facade"

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def _facade(self, model: str) -> Any:
        if model not in self._cache:
            from llm.llm_facade import LLMFacade

            provider, _, name = model.partition("/")
            self._cache[model] = LLMFacade(provider=provider or None, model=name or None)
        return self._cache[model]

    def complete(self, request: LLMRequest) -> LLMResponse:
        facade = self._facade(request.model)
        prompt = f"{request.system}\n\n{request.prompt}" if request.system else request.prompt
        try:
            if request.output_schema is not None:
                data = facade.generate_structured(prompt, request.output_schema, temperature=request.temperature, max_tokens=request.max_tokens)
                return LLMResponse(data=data, model=request.model)
            text = facade.generate(prompt, temperature=request.temperature, max_tokens=request.max_tokens)
            return LLMResponse(text=text, model=request.model)
        except Exception as e:
            raise LLMError(f"facade call failed: {e}") from e
