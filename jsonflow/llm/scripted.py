"""Replays canned responses per node id. For tests, demos and dry runs.

Fixture format::

    {"extract_events": {"events": [...]},          # same answer every call
     "summarise": ["first answer", "second answer"]} # one per call, in order
"""
from __future__ import annotations

import copy
import json
import threading
from pathlib import Path
from typing import Any

from jsonflow.errors import LLMError
from jsonflow.llm.base import LLMRequest, LLMResponse


class ScriptedProvider:
    name = "scripted"

    def __init__(self, responses: dict[str, Any] | str | Path) -> None:
        if not isinstance(responses, dict):
            responses = json.loads(Path(responses).read_text())
        self.responses = responses
        self.requests: list[LLMRequest] = []
        self._counts: dict[str, int] = {}
        self._lock = threading.Lock()

    def complete(self, request: LLMRequest) -> LLMResponse:
        with self._lock:
            self.requests.append(request)
            if request.node_id not in self.responses:
                raise LLMError(f"no scripted response for node {request.node_id!r}")
            answer = self.responses[request.node_id]
            if isinstance(answer, list):
                i = self._counts.get(request.node_id, 0)
                self._counts[request.node_id] = i + 1
                if i >= len(answer):
                    raise LLMError(f"scripted responses for {request.node_id!r} exhausted")
                answer = answer[i]
        answer = copy.deepcopy(answer)
        if request.output_schema is not None:
            return LLMResponse(data=answer, model=f"scripted:{request.model}")
        return LLMResponse(text=answer if isinstance(answer, str) else json.dumps(answer), model=f"scripted:{request.model}")
