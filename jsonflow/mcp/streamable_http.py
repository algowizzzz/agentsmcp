"""Client for any standard MCP server over Streamable HTTP (JSON-RPC 2.0).

Handles the initialize handshake, the ``Mcp-Session-Id`` header, paginated
``tools/list``, ``tools/call`` and both JSON and SSE response bodies. This is
the transport to use for MCP servers other than SAJHA.
"""
from __future__ import annotations

import itertools
import json
import threading
from typing import Any, Optional

import httpx

from jsonflow.errors import ToolError
from jsonflow.mcp.base import ToolInfo, parse_text_payload, raw_category_of

PROTOCOL_VERSION = "2025-06-18"


class StreamableHttpClient:
    def __init__(
        self,
        name: str,
        url: str,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.name = name
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        self._http = httpx.Client(timeout=timeout, trust_env=False, transport=transport)
        self._ids = itertools.count(1)
        self._session_id: Optional[str] = None
        self._protocol: Optional[str] = None
        self._lock = threading.Lock()
        self._initialized = False

    def _base_headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **self.headers}
        if self._session_id:
            h["Mcp-Session-Id"] = self._session_id
        if self._protocol:
            h["MCP-Protocol-Version"] = self._protocol
        return h

    def _post(self, body: dict[str, Any], timeout: Optional[float] = None) -> httpx.Response:
        try:
            return self._http.post(self.url, json=body, headers=self._base_headers(), timeout=timeout or self.timeout)
        except httpx.TimeoutException as e:
            raise ToolError(f"server {self.name}: request timed out") from e
        except httpx.HTTPError as e:
            raise ToolError(f"server {self.name}: {e}") from e

    @staticmethod
    def _read_message(resp: httpx.Response, req_id: int) -> dict[str, Any]:
        ctype = resp.headers.get("content-type", "")
        if "text/event-stream" in ctype:
            data_lines: list[str] = []
            for line in resp.text.splitlines() + [""]:
                if line.startswith("data:"):
                    data_lines.append(line[5:].lstrip())
                elif line == "" and data_lines:
                    msg = json.loads("\n".join(data_lines))
                    data_lines = []
                    if isinstance(msg, dict) and msg.get("id") == req_id:
                        return msg
            raise ToolError(f"no response for request {req_id} in event stream")
        msg = resp.json()
        if isinstance(msg, list):
            msg = next((m for m in msg if m.get("id") == req_id), {})
        return msg

    def _request(self, method: str, params: Optional[dict[str, Any]] = None, timeout: Optional[float] = None) -> Any:
        req_id = next(self._ids)
        resp = self._post({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}, timeout)
        if resp.status_code not in (200, 202):
            raise ToolError(f"server {self.name}: {method} returned HTTP {resp.status_code}")
        sid = resp.headers.get("mcp-session-id")
        if sid:
            self._session_id = sid
        msg = self._read_message(resp, req_id)
        if "error" in msg:
            err = msg["error"]
            raise ToolError(f"server {self.name}: {method} error {err.get('code')}: {err.get('message')}")
        return msg.get("result")

    def _ensure_initialized(self) -> None:
        with self._lock:
            if self._initialized:
                return
            result = self._request(
                "initialize",
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "jsonflow", "version": "0.1.0"},
                },
            )
            self._protocol = (result or {}).get("protocolVersion", PROTOCOL_VERSION)
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
            self._initialized = True

    def list_tools(self) -> list[ToolInfo]:
        self._ensure_initialized()
        out: list[ToolInfo] = []
        cursor: Optional[str] = None
        for _ in range(100):  # pagination guard
            result = self._request("tools/list", {"cursor": cursor} if cursor else {}) or {}
            for t in result.get("tools", []):
                out.append(
                    ToolInfo(
                        server=self.name,
                        name=t["name"],
                        description=t.get("description", ""),
                        input_schema=t.get("inputSchema") or {},
                        output_schema=t.get("outputSchema"),
                        raw_category=raw_category_of(t),
                    )
                )
            cursor = result.get("nextCursor")
            if not cursor:
                break
        return out

    def call_tool(self, tool: str, arguments: dict[str, Any], timeout: Optional[float] = None) -> Any:
        self._ensure_initialized()
        result = self._request("tools/call", {"name": tool, "arguments": arguments}, timeout) or {}
        content = result.get("content") or []
        texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        if result.get("isError"):
            raise ToolError(f"{self.name}.{tool}: {' '.join(texts) or 'tool reported an error'}")
        if result.get("structuredContent") is not None:
            return result["structuredContent"]
        if len(texts) == 1:
            return parse_text_payload(texts[0])
        if texts:
            return [parse_text_payload(t) for t in texts]
        return content
