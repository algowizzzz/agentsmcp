import json

import httpx
import pytest

from jsonflow.errors import ToolError
from jsonflow.mcp.fixture import FixtureClient
from jsonflow.mcp.sajha import SajhaClient
from jsonflow.mcp.streamable_http import StreamableHttpClient

NEWS_SCHEMA = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}


# --------------------------------------------------------------------- SAJHA
def _sajha(handler, **kw):
    return SajhaClient("sajha", "http://sajha:3002", transport=httpx.MockTransport(handler), **kw)


def test_sajha_list_tools_and_headers(monkeypatch):
    monkeypatch.setenv("SAJHA_API_KEY", "sja_test")
    seen = {}

    def handler(req):
        seen["headers"] = req.headers
        assert req.url.path == "/api/tools/list"
        return httpx.Response(200, json={"tools": [
            {"name": "tavily_news_search", "description": "news", "inputSchema": NEWS_SCHEMA, "metadata": {"category": "News Search"}}]})

    tools = _sajha(handler, auth={"mode": "apikey", "api_key_env": "SAJHA_API_KEY"}).list_tools()
    assert tools[0].name == "tavily_news_search" and tools[0].raw_category == "News Search"
    assert seen["headers"]["x-api-key"] == "sja_test"


def test_sajha_missing_api_key_is_clear(monkeypatch):
    monkeypatch.delenv("SAJHA_API_KEY", raising=False)
    client = _sajha(lambda r: httpx.Response(200, json={}), auth={"mode": "apikey", "api_key_env": "SAJHA_API_KEY"})
    with pytest.raises(ToolError, match="SAJHA_API_KEY is not set"):
        client.list_tools()


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"result": {"results": [1]}}, {"results": [1]}),                                        # legacy fork
        ({"success": True, "result": {"results": [2]}}, {"results": [2]}),                        # upstream
        ({"success": True, "result": {"value": {"results": [3]}, "error": None, "trace": []}}, {"results": [3]}),  # StepResult
    ],
)
def test_sajha_unwraps_response_shapes(payload, expected):
    def handler(req):
        body = json.loads(req.content)
        assert body == {"tool": "t", "arguments": {"query": "q", "_worker_context": {"worker_id": "w1"}}}
        return httpx.Response(200, json=payload)

    assert _sajha(handler, worker_context={"worker_id": "w1"}).call_tool("t", {"query": "q"}) == expected


@pytest.mark.parametrize(
    "status,payload,msg",
    [
        (200, {"success": False, "error": "quota"}, "quota"),
        (200, {"result": {"value": None, "error": "bad args"}}, "bad args"),
        (200, {"error": "boom"}, "boom"),
        # observed from a live SAJHA v2.9.8 server: tool failure nested in a success envelope
        (200, {"result": {"error": "No such file", "success": False}, "success": True}, "No such file"),
        (500, {"error": "Missing required parameter: query", "success": False}, "HTTP 500: Missing required"),
        (403, {"error": "Access denied"}, "HTTP 403: Access denied"),
    ],
)
def test_sajha_errors(status, payload, msg):
    client = _sajha(lambda r: httpx.Response(status, json=payload))
    with pytest.raises(ToolError, match=msg):
        client.call_tool("t", {})


def test_sajha_jwt_login_is_cached(monkeypatch):
    monkeypatch.setenv("SAJHA_USER", "u")
    monkeypatch.setenv("SAJHA_PASSWORD", "p")
    logins = []

    def handler(req):
        if req.url.path == "/api/auth/login":
            logins.append(json.loads(req.content))
            return httpx.Response(200, json={"token": "jwt123"})
        assert req.headers["authorization"] == "Bearer jwt123"
        return httpx.Response(200, json={"result": {"ok": True}})

    client = _sajha(handler, auth={"mode": "jwt"})
    client.call_tool("t", {})
    client.call_tool("t", {})
    assert logins == [{"user_id": "u", "password": "p"}]


# ------------------------------------------------------- Streamable HTTP MCP
def _mcp_handler(log, sse=False, tools_pages=None):
    pages = tools_pages or [{"tools": [{"name": "echo", "inputSchema": NEWS_SCHEMA}]}]

    def respond(msg_id, result):
        body = {"jsonrpc": "2.0", "id": msg_id, "result": result}
        if sse:
            text = f"event: message\ndata: {json.dumps(body)}\n\n"
            return httpx.Response(200, text=text, headers={"content-type": "text/event-stream"})
        return httpx.Response(200, json=body, headers={"mcp-session-id": "sess-1"})

    def handler(req):
        msg = json.loads(req.content)
        log.append((msg.get("method"), dict(req.headers)))
        method = msg.get("method")
        if method == "initialize":
            return respond(msg["id"], {"protocolVersion": "2025-06-18", "capabilities": {}, "serverInfo": {"name": "x"}})
        if method == "notifications/initialized":
            return httpx.Response(202)
        if method == "tools/list":
            cursor = (msg.get("params") or {}).get("cursor")
            idx = int(cursor) if cursor else 0
            page = dict(pages[idx])
            if idx + 1 < len(pages):
                page["nextCursor"] = str(idx + 1)
            return respond(msg["id"], page)
        if method == "tools/call":
            name = msg["params"]["name"]
            if name == "fails":
                return respond(msg["id"], {"isError": True, "content": [{"type": "text", "text": "nope"}]})
            if name == "structured":
                return respond(msg["id"], {"content": [], "structuredContent": {"a": 1}})
            if name == "pyrepr":
                return respond(msg["id"], {"content": [{"type": "text", "text": "{'a': 1, 'b': None}"}]})
            return respond(msg["id"], {"content": [{"type": "text", "text": json.dumps(msg["params"]["arguments"])}]})
        if method == "boom":
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "no"}})
        raise AssertionError(method)

    return handler


@pytest.mark.parametrize("sse", [False, True])
def test_streamable_http_handshake_list_and_call(sse):
    log = []
    pages = [{"tools": [{"name": "a", "inputSchema": {}}]}, {"tools": [{"name": "b", "inputSchema": {}}]}]
    client = StreamableHttpClient("m", "http://m/mcp", transport=httpx.MockTransport(_mcp_handler(log, sse, pages)))
    assert [t.name for t in client.list_tools()] == ["a", "b"]
    assert client.call_tool("echo", {"q": 1}) == {"q": 1}
    assert [m for m, _ in log][:2] == ["initialize", "notifications/initialized"]
    assert log[-1][1]["mcp-protocol-version"] == "2025-06-18"
    if not sse:
        assert log[-1][1]["mcp-session-id"] == "sess-1"


def test_streamable_http_result_variants():
    client = StreamableHttpClient("m", "http://m/mcp", transport=httpx.MockTransport(_mcp_handler([])))
    assert client.call_tool("structured", {}) == {"a": 1}
    assert client.call_tool("pyrepr", {}) == {"a": 1, "b": None}  # SAJHA JSON-RPC emits Python repr
    with pytest.raises(ToolError, match="nope"):
        client.call_tool("fails", {})
    with pytest.raises(ToolError, match="-32601"):
        client._request("boom")


# ------------------------------------------------------------------- Fixture
def test_fixture_client_matching_and_errors(sajha_fixture):
    c = FixtureClient("sajha", sajha_fixture)
    assert c.call_tool("tavily_news_search", {"query": "USA Hedge Funds major market risks"})["results"]
    with pytest.raises(ToolError, match="rate limit"):
        c.call_tool("tavily_news_search", {"query": "fixed income"})
    with pytest.raises(ToolError, match="no fixture response"):
        c.call_tool("unknown_tool", {})
    assert [x["tool"] for x in c.calls] == ["tavily_news_search", "tavily_news_search", "unknown_tool"]
