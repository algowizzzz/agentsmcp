"""Client for a SAJHA MCP server over its REST API.

Discovery: ``GET  /api/tools/list``    -> {"tools": [{name, description, inputSchema, ...}]}
Execution: ``POST /api/tools/execute`` -> {"tool": name, "arguments": {...}}

The REST path is preferred over SAJHA's JSON-RPC endpoint because JSON-RPC
``tools/call`` returns dict results as Python repr text. Response unwrapping
mirrors ``agent/tools.py::_call_sajha`` in mcp-intelligence-agent so this
works against both the legacy fork and upstream v5.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Any, Optional

import httpx

from jsonflow.errors import ToolError
from jsonflow.mcp.base import ToolInfo, raw_category_of


class SajhaClient:
    def __init__(
        self,
        name: str,
        base_url: str,
        auth: Optional[dict[str, Any]] = None,
        timeout: float = 30.0,
        worker_context: Optional[dict[str, Any]] = None,
        extra_headers: Optional[dict[str, str]] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.auth = auth or {"mode": "none"}
        self.timeout = timeout
        self.worker_context = worker_context
        self.extra_headers = extra_headers or {}
        self._http = httpx.Client(timeout=timeout, trust_env=False, transport=transport)
        self._jwt: dict[str, Any] = {"token": "", "expires_at": 0.0}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ auth
    def _headers(self) -> dict[str, str]:
        mode = self.auth.get("mode", "none")
        headers = dict(self.extra_headers)
        if mode == "apikey":
            key = os.getenv(self.auth.get("api_key_env", "SAJHA_API_KEY"), "")
            if not key:
                raise ToolError(f"server {self.name}: env var {self.auth.get('api_key_env', 'SAJHA_API_KEY')} is not set")
            headers["X-API-Key"] = key
            headers["Authorization"] = key  # legacy fork reads the bare key here
        elif mode == "jwt":
            headers["Authorization"] = f"Bearer {self._get_jwt()}"
        elif mode != "none":
            raise ToolError(f"server {self.name}: unknown auth mode {mode!r}")
        return headers

    def _get_jwt(self) -> str:
        with self._lock:
            now = time.time()
            if self._jwt["token"] and now < self._jwt["expires_at"] - 60:
                return self._jwt["token"]
            user = os.getenv(self.auth.get("user_env", "SAJHA_USER"), "")
            password = os.getenv(self.auth.get("password_env", "SAJHA_PASSWORD"), "")
            if not user or not password:
                raise ToolError(f"server {self.name}: jwt auth needs user and password env vars")
            r = self._http.post(f"{self.base_url}/api/auth/login", json={"user_id": user, "password": password})
            if r.status_code != 200:
                raise ToolError(f"server {self.name}: login failed with HTTP {r.status_code}")
            data = r.json()
            token = data.get("token") or data.get("access_token")
            if not token:
                raise ToolError(f"server {self.name}: login response had no token")
            self._jwt = {"token": token, "expires_at": now + float(self.auth.get("token_ttl_seconds", 3000))}
            return token

    # ------------------------------------------------------------- discovery
    def list_tools(self) -> list[ToolInfo]:
        try:
            r = self._http.get(f"{self.base_url}/api/tools/list", headers=self._headers())
        except httpx.HTTPError as e:
            raise ToolError(f"server {self.name}: cannot list tools: {e}") from e
        if r.status_code != 200:
            raise ToolError(f"server {self.name}: tools/list returned HTTP {r.status_code}")
        payload = r.json()
        tools = payload.get("tools", payload if isinstance(payload, list) else [])
        out = []
        for t in tools:
            if not isinstance(t, dict) or "name" not in t:
                continue
            out.append(
                ToolInfo(
                    server=self.name,
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema") or t.get("input_schema") or {},
                    output_schema=t.get("outputSchema") or t.get("output_schema"),
                    raw_category=raw_category_of(t),
                )
            )
        return out

    # ------------------------------------------------------------- execution
    def call_tool(self, tool: str, arguments: dict[str, Any], timeout: Optional[float] = None) -> Any:
        args = dict(arguments)
        if self.worker_context is not None and "_worker_context" not in args:
            args["_worker_context"] = self.worker_context
        try:
            r = self._http.post(
                f"{self.base_url}/api/tools/execute",
                headers=self._headers(),
                json={"tool": tool, "arguments": args},
                timeout=timeout or self.timeout,
            )
        except httpx.TimeoutException as e:
            raise ToolError(f"{self.name}.{tool} timed out") from e
        except httpx.HTTPError as e:
            raise ToolError(f"{self.name}.{tool} failed: {e}") from e
        try:
            payload = r.json()
        except ValueError:
            payload = None
        if r.status_code != 200:
            detail = payload.get("error") if isinstance(payload, dict) else r.text[:300]
            raise ToolError(f"{self.name}.{tool} returned HTTP {r.status_code}: {detail}")
        return self._unwrap(tool, payload)

    def _unwrap(self, tool: str, payload: Any) -> Any:
        if not isinstance(payload, dict):
            return payload
        if payload.get("success") is False:
            raise ToolError(f"{self.name}.{tool}: {payload.get('error') or 'tool reported failure'}")
        result = payload["result"] if "result" in payload else payload
        # Upstream StepResult envelope: {value, error, trace, duration, confidence, _composition}
        if isinstance(result, dict) and "value" in result and ("error" in result or "_composition" in result):
            if result.get("error"):
                raise ToolError(f"{self.name}.{tool}: {result['error']}")
            result = result.get("value")
        # Tools report their own failures inside a successful envelope:
        # {"success": true, "result": {"error": "...", "success": false}}
        if isinstance(result, dict) and (result.get("success") is False or set(result) == {"error"}):
            raise ToolError(f"{self.name}.{tool}: {result.get('error') or 'tool reported failure'}")
        return result
