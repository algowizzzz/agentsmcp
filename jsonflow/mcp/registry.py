"""Registry of MCP servers, tool catalog, categories and allowlists.

Config file (``config/jsonflow/servers.json``)::

    {
      "servers": {
        "sajha": {
          "transport": "sajha_rest",                  # sajha_rest | mcp_http | fixture
          "base_url": "${SAJHA_BASE_URL:-http://localhost:3002}",
          "auth": {"mode": "apikey", "api_key_env": "SAJHA_API_KEY"},
          "allow_tools": ["tavily_*"],
          "deny_tools": ["*_send_*"]
        }
      },
      "categories": {
        "web": ["tavily_*_search", "browser_*"],
        "structured": ["duckdb_*"],
        "unstructured": ["pdf_read"]
      },
      "raw_category_map": {"News Search": "web"}
    }

Server-level category tags are not in the MCP spec, so the category of a tool
is resolved in this order: the server's ``raw_category_map`` applied to the
tool's own category metadata, then the name patterns in ``categories``, then
the server's ``default_category``, then ``other``.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Optional

from jsonflow.errors import SpecError, ToolError
from jsonflow.mcp.base import MCPClient, ToolInfo

CATEGORIES = ("structured", "unstructured", "web", "agents", "other")
_ENV_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return _ENV_RE.sub(lambda m: os.getenv(m.group(1), m.group(2) or ""), value)
    if isinstance(value, list):
        return [expand_env(v) for v in value]
    if isinstance(value, dict):
        return {k: expand_env(v) for k, v in value.items()}
    return value


def _matches(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


class ServerRegistry:
    def __init__(self, config: dict[str, Any], clients: Optional[dict[str, MCPClient]] = None, cache_ttl: float = 300.0):
        self.config = config
        self.servers_cfg: dict[str, dict[str, Any]] = config.get("servers", {})
        self.categories: dict[str, list[str]] = config.get("categories", {})
        self.raw_category_map: dict[str, str] = config.get("raw_category_map", {})
        self.cache_ttl = cache_ttl
        self._clients: dict[str, MCPClient] = dict(clients or {})
        self._catalog: dict[str, tuple[float, dict[str, ToolInfo]]] = {}
        self._lock = threading.Lock()
        for bad in set(self.categories) - set(CATEGORIES):
            raise SpecError(f"unknown category {bad!r}; use one of {CATEGORIES}")

    # ---------------------------------------------------------------- setup
    @classmethod
    def from_file(cls, path: str | Path, **kw: Any) -> "ServerRegistry":
        return cls(json.loads(Path(path).read_text()), **kw)

    def server_names(self) -> list[str]:
        return sorted(set(self.servers_cfg) | set(self._clients))

    def client(self, server: str) -> MCPClient:
        with self._lock:
            if server in self._clients:
                return self._clients[server]
            cfg = self.servers_cfg.get(server)
            if cfg is None:
                raise ToolError(f"unknown MCP server {server!r}; registered: {self.server_names()}")
            client = self._build_client(server, expand_env(cfg))
            self._clients[server] = client
            return client

    @staticmethod
    def _build_client(name: str, cfg: dict[str, Any]) -> MCPClient:
        transport = cfg.get("transport", "sajha_rest")
        if transport == "sajha_rest":
            from jsonflow.mcp.sajha import SajhaClient

            return SajhaClient(
                name,
                cfg["base_url"],
                auth=cfg.get("auth"),
                timeout=float(cfg.get("timeout", 30)),
                worker_context=cfg.get("worker_context"),
                extra_headers=cfg.get("headers"),
            )
        if transport == "mcp_http":
            from jsonflow.mcp.streamable_http import StreamableHttpClient

            return StreamableHttpClient(name, cfg["url"], headers=cfg.get("headers"), timeout=float(cfg.get("timeout", 30)))
        if transport == "fixture":
            from jsonflow.mcp.fixture import FixtureClient

            return FixtureClient(name, cfg["path"])
        raise SpecError(f"server {name}: unknown transport {transport!r}")

    # -------------------------------------------------------------- policy
    def is_allowed(self, server: str, tool: str) -> bool:
        cfg = self.servers_cfg.get(server, {})
        allow = cfg.get("allow_tools", ["*"])
        deny = cfg.get("deny_tools", [])
        return _matches(tool, allow) and not _matches(tool, deny)

    def categorize(self, server: str, info: ToolInfo) -> str:
        cfg = self.servers_cfg.get(server, {})
        raw_map = {**self.raw_category_map, **cfg.get("raw_category_map", {})}
        if info.raw_category and info.raw_category in raw_map:
            return raw_map[info.raw_category]
        for cat in CATEGORIES:
            if _matches(info.name, self.categories.get(cat, [])):
                return cat
        return cfg.get("default_category", "other")

    # ------------------------------------------------------------- catalog
    def tools(self, server: str, refresh: bool = False, include_blocked: bool = False) -> dict[str, ToolInfo]:
        now = time.time()
        cached = self._catalog.get(server)
        if refresh or cached is None or now - cached[0] > self.cache_ttl:
            infos = self.client(server).list_tools()
            catalog = {}
            for info in infos:
                info.server = server
                info.category = self.categorize(server, info)
                catalog[info.name] = info
            self._catalog[server] = (now, catalog)
            cached = self._catalog[server]
        tools = cached[1]
        if include_blocked:
            return dict(tools)
        return {n: t for n, t in tools.items() if self.is_allowed(server, n)}

    def tool(self, server: str, name: str) -> ToolInfo:
        if not self.is_allowed(server, name):
            raise ToolError(f"tool {server}.{name} is not allowed by the server allowlist")
        tools = self.tools(server)
        if name not in tools:
            raise ToolError(f"tool {name!r} not found on server {server!r}")
        return tools[name]

    def palette(self, servers: Optional[list[str]] = None, refresh: bool = False) -> dict[str, Any]:
        """Tool catalog grouped by category: the feed for a drag-and-drop node palette."""
        grouped: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORIES}
        errors: dict[str, str] = {}
        for server in servers or self.server_names():
            try:
                tools = self.tools(server, refresh=refresh)
            except ToolError as e:
                errors[server] = str(e)
                continue
            for info in sorted(tools.values(), key=lambda t: t.name):
                schema = dict(info.input_schema or {})
                props = {k: v for k, v in (schema.get("properties") or {}).items() if not k.startswith("_")}
                grouped[info.category].append(
                    {
                        "node_template": {"type": "tool", "server": server, "tool": info.name, "args": {}},
                        "server": server,
                        "tool": info.name,
                        "description": info.description,
                        "category": info.category,
                        "raw_category": info.raw_category,
                        "input_schema": {**schema, "properties": props},
                        "required": [r for r in schema.get("required", []) if not r.startswith("_")],
                        "has_output_schema": info.output_schema is not None,
                    }
                )
        return {"categories": grouped, "errors": errors}
