"""Common types for MCP clients."""
from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional, Protocol


@dataclass
class ToolInfo:
    server: str
    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: Optional[dict[str, Any]] = None
    raw_category: Optional[str] = None
    category: str = "other"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MCPClient(Protocol):
    """What the engine needs from an MCP server."""

    name: str

    def list_tools(self) -> list[ToolInfo]: ...

    def call_tool(self, tool: str, arguments: dict[str, Any], timeout: Optional[float] = None) -> Any: ...


def parse_text_payload(text: str) -> Any:
    """Turn a text tool result into data when it is JSON (or a Python repr, which SAJHA's JSON-RPC path emits)."""
    s = text.strip()
    if not s or s[0] not in "[{":
        return text
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return text


def raw_category_of(tool: dict[str, Any]) -> Optional[str]:
    meta = tool.get("metadata") or {}
    return tool.get("category") or meta.get("category") or (tool.get("annotations") or {}).get("category")
