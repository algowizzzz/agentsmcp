"""MCP endpoint (Streamable HTTP, JSON responses) that exposes published agents as tools.

POST /mcp                      every published agent the API key may see
POST /mcp/category/<slug>      only agents in one category

Auth: ``Authorization: Bearer <key>`` or ``X-API-Key: <key>``. Keys are
created by a super admin and may be limited to categories.
"""
from __future__ import annotations

import json
import re
import secrets
from typing import Any, Optional

from jsonflow.server.agents_client import input_schema_for
from jsonflow.server.services import Service, ServiceError

SUPPORTED_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER_INFO = {"name": "jsonflow-agents", "version": "1.0.0"}


def category_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _error(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _ok(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


class AgentMCPServer:
    def __init__(self, service: Service) -> None:
        self.service = service

    def visible_agents(self, key: dict[str, Any], category_slug_filter: Optional[str]) -> list[dict[str, Any]]:
        allowed = json.loads(key["categories"]) if isinstance(key.get("categories"), str) else key.get("categories") or []
        out = []
        for a in self.service.published_agents():
            if allowed and a["category"] not in allowed:
                continue
            if category_slug_filter and category_slug(a["category"]) != category_slug_filter:
                continue
            out.append(a)
        return out

    def tool_for(self, agent: dict[str, Any]) -> dict[str, Any]:
        d = agent["definition"]
        return {
            "name": agent["id"],
            "title": agent["name"],
            "description": f"[{agent['category']}] {agent['description'] or agent['name']}",
            "inputSchema": input_schema_for(d),
            "category": agent["category"],
            "annotations": {"title": agent["name"], "openWorldHint": True},
            "_meta": {"category": agent["category"], "version": agent["version"]},
        }

    def handle(self, message: Any, key: dict[str, Any], category: Optional[str]) -> tuple[Optional[Any], dict[str, str]]:
        """Returns (response body or None for notifications, extra headers)."""
        if isinstance(message, list):
            replies = [r for r in (self.handle(m, key, category)[0] for m in message) if r is not None]
            return (replies or None), {}
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or "method" not in message:
            return _error(message.get("id") if isinstance(message, dict) else None, -32600, "Invalid JSON-RPC request"), {}
        req_id, method, params = message.get("id"), message["method"], message.get("params") or {}
        if req_id is None:  # notification
            return None, {}
        if method == "initialize":
            asked = params.get("protocolVersion")
            version = asked if asked in SUPPORTED_VERSIONS else SUPPORTED_VERSIONS[0]
            result = {"protocolVersion": version, "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": SERVER_INFO,
                      "instructions": "Each tool is a published agent. Tool descriptions start with the agent's category."}
            return _ok(req_id, result), {"Mcp-Session-Id": secrets.token_urlsafe(16)}
        if method == "ping":
            return _ok(req_id, {}), {}
        if method == "tools/list":
            return _ok(req_id, {"tools": [self.tool_for(a) for a in self.visible_agents(key, category)]}), {}
        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            agents = {a["id"]: a for a in self.visible_agents(key, category)}
            if name not in agents:
                return _error(req_id, -32602, f"Unknown tool {name!r}"), {}
            try:
                run = self.service.run_agent_sync(name, args, trigger="mcp", triggered_by=f"apikey:{key['name']}")
            except ServiceError as e:
                return _ok(req_id, {"isError": True, "content": [{"type": "text", "text": str(e)}]}), {}
            if run["status"] != "succeeded":
                text = f"Agent run {run['id']} failed: {run.get('error')}"
                return _ok(req_id, {"isError": True, "content": [{"type": "text", "text": text}]}), {}
            output = run["output"]
            result: dict[str, Any] = {"content": [{"type": "text", "text": json.dumps(output, ensure_ascii=False, default=str)}],
                                      "_meta": {"run_id": run["id"], "agent_version": run["agent_version"]}}
            if isinstance(output, dict):
                result["structuredContent"] = output
            return _ok(req_id, result), {}
        return _error(req_id, -32601, f"Method not found: {method}"), {}
