"""Web product: auth, roles, agents, runs, settings and the MCP endpoint."""
import json
import time

import pytest
from fastapi.testclient import TestClient

from jsonflow.llm.scripted import ScriptedProvider
from jsonflow.mcp.fixture import FixtureClient
from jsonflow.mcp.streamable_http import StreamableHttpClient
from jsonflow.server import app as app_module
from jsonflow.server.app import create_app

from .conftest import CONFIG

H = {"X-Requested-With": "jsonflow"}
SUPER_PW = "Super-secret-1"
ADMIN_PW = "Admin-secret-1"


@pytest.fixture
def env(tmp_path, sajha_fixture, llm_fixture):
    app_module._LOGIN_FAILS.clear()
    scripted = ScriptedProvider(llm_fixture)
    app = create_app(tmp_path, client_overrides={"sajha": FixtureClient("sajha", sajha_fixture)},
                     llm_overrides={"anthropic": scripted, "openai_compat": scripted})
    svc = app.state.service
    svc.create_user("root", SUPER_PW, "super_admin", "Root", "test")
    svc.create_user("ana", ADMIN_PW, "admin", "Ana", "test")
    yield app, svc
    svc.shutdown()


def client_for(app, user=None, pw=None):
    c = TestClient(app)
    if user:
        r = c.post("/api/auth/login", json={"username": user, "password": pw}, headers=H)
        assert r.status_code == 200, r.text
    return c


def wait_run(c, run_id, timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = c.get(f"/api/runs/{run_id}").json()
        if r["status"] in ("succeeded", "failed"):
            return r
        time.sleep(0.05)
    raise AssertionError("run did not finish")


# ---------------------------------------------------------------- auth & roles
def test_login_csrf_lockout_and_pages(env):
    app, _ = env
    c = TestClient(app)
    assert c.post("/api/auth/login", json={"username": "root", "password": SUPER_PW}).status_code == 403  # no CSRF header
    assert c.get("/api/me").status_code == 401
    for _ in range(5):
        assert c.post("/api/auth/login", json={"username": "ana", "password": "nope"}, headers=H).status_code == 401
    assert c.post("/api/auth/login", json={"username": "ana", "password": ADMIN_PW}, headers=H).status_code == 429
    c = client_for(app, "root", SUPER_PW)
    assert c.get("/api/me").json()["role"] == "super_admin"
    for path in ["/", "/guide", "/login", "/app", "/app/agents/x", "/app/runs/x", "/app/admin"]:
        r = c.get(path)
        assert r.status_code == 200 and "text/html" in r.headers["content-type"], path
        assert "script-src 'self'" in r.headers["content-security-policy"]
    c.post("/api/auth/logout", headers=H)
    assert c.get("/api/me").status_code == 401


def test_admin_cannot_use_super_admin_endpoints(env):
    app, _ = env
    admin = client_for(app, "ana", ADMIN_PW)
    for method, path in [("get", "/api/users"), ("get", "/api/settings/servers"), ("get", "/api/settings/llm"),
                         ("get", "/api/keys"), ("get", "/api/audit"), ("delete", "/api/agents/sector_events"),
                         ("post", "/api/categories")]:
        kw = {"headers": H, "json": {}} if method == "post" else {"headers": H}
        assert getattr(admin, method)(path, **kw).status_code == 403, path
    assert admin.get("/api/agents").status_code == 200
    assert admin.get("/api/palette").status_code == 200


def test_user_management_rules(env):
    app, svc = env
    root = client_for(app, "root", SUPER_PW)
    assert root.post("/api/users", json={"username": "bob", "password": "short", "role": "admin"}, headers=H).status_code == 400
    assert root.post("/api/users", json={"username": "bob", "password": "Long-enough-1", "role": "viewer"}, headers=H).status_code == 400
    uid = root.post("/api/users", json={"username": "bob", "password": "Long-enough-1", "role": "admin"}, headers=H).json()["id"]
    me = root.get("/api/me").json()
    assert root.patch(f"/api/users/{me['id']}", json={"role": "admin"}, headers=H).status_code == 400  # self demotion
    bob = client_for(app, "bob", "Long-enough-1")
    assert root.patch(f"/api/users/{uid}", json={"active": False}, headers=H).status_code == 200
    assert bob.get("/api/me").status_code == 401  # sessions ended on disable
    assert any(a["action"] == "user.update" for a in root.get("/api/audit").json())


# ---------------------------------------------------------------- agents
def test_agent_lifecycle_versions_and_publish_rules(env):
    app, _ = env
    admin = client_for(app, "ana", ADMIN_PW)
    assert admin.post("/api/agents", json={"name": "X", "category": "Nope"}, headers=H).status_code == 400
    agent_id = admin.post("/api/agents", json={"name": "Limit Watch", "category": "Credit Risk",
                                               "description": "d"}, headers=H).json()["id"]
    assert agent_id == "limit_watch"
    a = admin.get(f"/api/agents/{agent_id}").json()
    assert a["version"] == 1 and a["validation"]["ok"]
    d = a["definition"]
    d["nodes"].append({"id": "ask", "type": "llm"})  # invalid: no prompt
    r = admin.put(f"/api/agents/{agent_id}", json={"definition": d, "version": 1}, headers=H).json()
    assert r["version"] == 2 and not r["validation"]["ok"]
    assert admin.put(f"/api/agents/{agent_id}", json={"definition": d, "version": 1}, headers=H).status_code == 409
    assert admin.post(f"/api/agents/{agent_id}/publish", json={"published": True}, headers=H).status_code == 400
    d["nodes"][-1]["prompt"] = "hello {{ inputs | json }}"
    assert admin.put(f"/api/agents/{agent_id}", json={"definition": d, "version": 2}, headers=H).json()["validation"]["ok"]
    assert admin.post(f"/api/agents/{agent_id}/publish", json={"published": True}, headers=H).status_code == 200
    assert [v["version"] for v in admin.get(f"/api/agents/{agent_id}/versions").json()] == [3, 2, 1]
    assert admin.get(f"/api/agents/{agent_id}/versions/1").json()["nodes"][0]["id"] == "start"
    d["id"] = "renamed"
    admin.put(f"/api/agents/{agent_id}", json={"definition": d}, headers=H)
    assert admin.get(f"/api/agents/{agent_id}").json()["definition"]["id"] == agent_id  # id is fixed


def test_run_seeded_agent_and_read_audit_files(env):
    app, _ = env
    admin = client_for(app, "ana", ADMIN_PW)
    agents = admin.get("/api/agents").json()
    assert [(a["id"], a["category"], a["published"]) for a in agents] == [("sector_events", "Credit Risk", True)]
    assert admin.post("/api/agents/sector_events/run", json={"inputs": {"bogus": 1}}, headers=H).status_code == 400
    run_id = admin.post("/api/agents/sector_events/run", json={"inputs": {"max_events": 2}}, headers=H).json()["run_id"]
    run = wait_run(admin, run_id)
    assert run["status"] == "succeeded", run["error"]
    assert len(run["output"]["events"]) == 2 and run["trigger"] == "ui" and run["triggered_by"] == "ana"
    assert run["trace"][0]["event"] == "run_start" and "discover_news.0.tool.json" in run["calls"]
    assert run["definition"]["id"] == "sector_events"
    assert admin.get(f"/api/runs/{run_id}/nodes/rank_events").json()[0]["event_id"] == "E1"
    assert admin.get(f"/api/runs/{run_id}/calls/extract_events.llm1.json").json()["output"]["events"]
    assert admin.get(f"/api/runs/{run_id}/nodes/..%2Fx").status_code in (400, 404)
    assert admin.get(f"/api/runs/{run_id}/calls/..%2F..%2Fjsonflow.sqlite").status_code in (400, 404)
    assert admin.get(f"/api/runs/{run_id}/calls/x.txt").status_code == 400
    assert admin.get("/api/runs?agent_id=sector_events").json()[0]["id"] == run_id


def test_palette_has_categories_logic_and_agents(env):
    app, _ = env
    pal = client_for(app, "ana", ADMIN_PW).get("/api/palette").json()
    assert {t["tool"] for t in pal["categories"]["web"]} >= {"tavily_news_search", "tavily_domain_search"}
    assert [t["tool"] for t in pal["categories"]["agents"]] == ["sector_events"]
    assert pal["categories"]["agents"][0]["raw_category"] == "Credit Risk"
    assert {x["type"] for x in pal["logic"]} == {"llm", "transform", "router"}
    assert "outlook_send_email" not in json.dumps(pal["categories"])


def test_agent_calls_agent_and_recursion_is_refused(env):
    app, _ = env
    admin = client_for(app, "ana", ADMIN_PW)
    agent_id = admin.post("/api/agents", json={"name": "Wrapper", "category": "Research"}, headers=H).json()["id"]
    d = admin.get(f"/api/agents/{agent_id}").json()["definition"]
    d["nodes"] = [{"id": "call", "type": "tool", "server": "agents", "tool": "sector_events", "args": {"max_events": 1}}]
    d["edges"] = []
    d["output"] = {"events": "{{ nodes.call.events }}"}
    admin.put(f"/api/agents/{agent_id}", json={"definition": d}, headers=H)
    assert admin.post(f"/api/agents/{agent_id}/publish", json={"published": True}, headers=H).status_code == 200
    # Once published it is a tool too, so it can (try to) call itself.
    d["nodes"].append({"id": "again", "type": "tool", "server": "agents", "tool": agent_id, "args": {}, "on_error": "continue"})
    d["edges"] = [["call", "again"]]
    saved = admin.put(f"/api/agents/{agent_id}", json={"definition": d}, headers=H).json()
    assert saved["validation"]["ok"], saved
    run = wait_run(admin, admin.post(f"/api/agents/{agent_id}/run", json={"inputs": {}}, headers=H).json()["run_id"])
    assert run["status"] == "succeeded", run["error"]
    assert len(run["output"]["events"]) == 1
    assert "recursion refused" in run["stats"]["node_errors"][0]["error"]
    child = [r for r in admin.get("/api/runs?agent_id=sector_events").json() if r["trigger"] == "agent"]
    assert child and child[0]["triggered_by"] == "ana"


# ---------------------------------------------------------------- settings
def test_settings_servers_and_llm(env):
    app, _ = env
    root = client_for(app, "root", SUPER_PW)
    cfg = root.get("/api/settings/servers").json()
    assert "sajha" in cfg["servers"]
    assert root.post("/api/settings/servers/sajha/test", headers=H).json()["ok"]
    bad = {**cfg, "servers": {**cfg["servers"], "agents": {}}}
    assert root.put("/api/settings/servers", json=bad, headers=H).status_code == 400
    assert root.put("/api/settings/servers", json=cfg, headers=H).status_code == 200
    assert root.put("/api/settings/llm", json={"provider": "openai_compat"}, headers=H).status_code == 400
    assert root.put("/api/settings/llm", json={"provider": "anthropic", "api_key_env": "sk-ant-123"}, headers=H).status_code == 400
    assert root.put("/api/settings/llm", json={"provider": "openai_compat", "base_url": "http://llm/v1", "model": "m",
                                               "api_key_env": "MY_KEY"}, headers=H).status_code == 200
    llm = root.get("/api/settings/llm").json()
    assert llm["provider"] == "openai_compat" and llm["api_key_present"] is False
    assert root.post("/api/settings/llm/test", headers=H).json()["ok"] is False  # scripted has no answer for this node


# ---------------------------------------------------------------- MCP
@pytest.fixture
def live(env):
    import socket
    import threading

    import uvicorn

    app, svc = env
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield app, svc, f"http://127.0.0.1:{port}"
    server.should_exit = True
    t.join(timeout=5)


def _mcp(base, key, path="/mcp"):
    return StreamableHttpClient("jf", f"{base}{path}", headers={"Authorization": f"Bearer {key}"})


def test_mcp_exposes_published_agents_as_tools(live):
    app, svc, base = live
    root = client_for(app, "root", SUPER_PW)
    assert TestClient(app).post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).status_code == 401
    key = root.post("/api/keys", json={"name": "sajha-agent"}, headers=H).json()["key"]
    client = _mcp(base, key)
    tools = client.list_tools()
    assert [t.name for t in tools] == ["sector_events"]
    assert tools[0].raw_category == "Credit Risk"
    assert tools[0].input_schema["properties"]["country"]["default"] == "USA"
    out = client.call_tool("sector_events", {"max_events": 1, "country": "USA"})
    assert len(out["events"]) == 1
    runs = root.get("/api/runs?agent_id=sector_events").json()
    assert runs[0]["trigger"] == "mcp" and runs[0]["triggered_by"] == "apikey:sajha-agent"
    from jsonflow.errors import ToolError

    with pytest.raises(ToolError):
        client.call_tool("sector_events", {"nope": 1})
    with pytest.raises(ToolError, match="Unknown tool"):
        client._request("tools/call", {"name": "missing", "arguments": {}})


def test_mcp_category_scoping(live):
    app, svc, base = live
    root = client_for(app, "root", SUPER_PW)
    scoped = root.post("/api/keys", json={"name": "mr", "categories": ["Market Risk"]}, headers=H).json()["key"]
    assert _mcp(base, scoped).list_tools() == []
    full = root.post("/api/keys", json={"name": "all"}, headers=H).json()
    assert [t.name for t in _mcp(base, full["key"], "/mcp/category/credit-risk").list_tools()] == ["sector_events"]
    assert _mcp(base, full["key"], "/mcp/category/research").list_tools() == []
    root.delete(f"/api/keys/{full['id']}", headers=H)
    with pytest.raises(Exception):
        _mcp(base, full["key"]).list_tools()
    info = root.get("/api/mcp/info").json()
    assert info["url"].endswith("/mcp") and info["published"] == 1
