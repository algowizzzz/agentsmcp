"""Offline MCP server backed by a JSON fixture file.

Used for tests, demos and dry runs when no live server or API key is
available. Fixture format::

    {
      "tools": [{"name": "...", "description": "...", "inputSchema": {...}, "category": "News Search"}],
      "responses": {
        "tavily_news_search": [
          {"match": {"query": "regulation"}, "result": {...}},
          {"result": {...}}                      # fallback, no match
        ]
      }
    }

``match`` values are case-insensitive substrings of the stringified argument.
"""
from __future__ import annotations

import copy
import json
import threading
from pathlib import Path
from typing import Any, Optional

from jsonflow.errors import ToolError
from jsonflow.mcp.base import ToolInfo, raw_category_of


class FixtureClient:
    def __init__(self, name: str, fixture: dict[str, Any] | str | Path) -> None:
        self.name = name
        if not isinstance(fixture, dict):
            fixture = json.loads(Path(fixture).read_text())
        self.fixture = fixture
        self.calls: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def list_tools(self) -> list[ToolInfo]:
        return [
            ToolInfo(
                server=self.name,
                name=t["name"],
                description=t.get("description", ""),
                input_schema=t.get("inputSchema") or {},
                output_schema=t.get("outputSchema"),
                raw_category=raw_category_of(t),
            )
            for t in self.fixture.get("tools", [])
        ]

    def call_tool(self, tool: str, arguments: dict[str, Any], timeout: Optional[float] = None) -> Any:
        with self._lock:
            self.calls.append({"tool": tool, "arguments": copy.deepcopy(arguments)})
        rules = self.fixture.get("responses", {}).get(tool)
        if rules is None:
            raise ToolError(f"{self.name}.{tool}: no fixture response")
        for rule in rules:
            match = rule.get("match") or {}
            if all(str(v).lower() in json.dumps(arguments.get(k, ""), default=str).lower() for k, v in match.items()):
                if "error" in rule:
                    raise ToolError(f"{self.name}.{tool}: {rule['error']}")
                return copy.deepcopy(rule.get("result"))
        raise ToolError(f"{self.name}.{tool}: no fixture response matches {arguments}")
