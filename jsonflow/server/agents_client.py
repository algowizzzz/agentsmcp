"""In-process MCP client that exposes published agents as tools to other agents.

An agent can call another agent like any tool (server name "agents"). Calls
carry the chain of agent ids so recursion is refused and depth is bounded.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from jsonflow.errors import ToolError
from jsonflow.mcp.base import ToolInfo

if TYPE_CHECKING:  # pragma: no cover
    from jsonflow.server.services import Service

AGENTS_SERVER = "agents"
MAX_DEPTH = 3


def input_schema_for(definition: dict[str, Any]) -> dict[str, Any]:
    props, required = {}, []
    for name, p in (definition.get("inputs") or {}).items():
        prop: dict[str, Any] = {"type": p.get("type", "string")}
        if p.get("description"):
            prop["description"] = p["description"]
        if p.get("default") is not None:
            prop["default"] = p["default"]
        props[name] = prop
        if p.get("required") and p.get("default") is None:
            required.append(name)
    schema: dict[str, Any] = {"type": "object", "properties": props, "additionalProperties": False}
    if required:
        schema["required"] = required
    return schema


class AgentsClient:
    def __init__(self, service: "Service", chain: list[str], triggered_by: str) -> None:
        self.name = AGENTS_SERVER
        self.service = service
        self.chain = chain
        self.triggered_by = triggered_by

    def list_tools(self) -> list[ToolInfo]:
        out = []
        for a in self.service.published_agents():
            out.append(ToolInfo(server=AGENTS_SERVER, name=a["id"], description=a["description"] or a["name"],
                                input_schema=input_schema_for(a["definition"]), raw_category=a["category"]))
        return out

    def call_tool(self, tool: str, arguments: dict[str, Any], timeout: Optional[float] = None) -> Any:
        if tool in self.chain:
            raise ToolError(f"agent {tool!r} is already running in this chain ({' → '.join(self.chain)}); recursion refused")
        if len(self.chain) >= MAX_DEPTH:
            raise ToolError(f"agent call depth limit of {MAX_DEPTH} reached")
        run = self.service.run_agent_sync(tool, arguments, trigger="agent", triggered_by=self.triggered_by,
                                          chain=self.chain + [tool], timeout=timeout)
        if run["status"] != "succeeded":
            raise ToolError(f"agent {tool} failed: {run.get('error')}")
        return run["output"]
