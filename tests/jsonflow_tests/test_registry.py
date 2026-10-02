import pytest

from jsonflow.errors import ToolError
from jsonflow.mcp.fixture import FixtureClient
from jsonflow.mcp.registry import ServerRegistry, expand_env


def _registry(servers_config, sajha_fixture):
    return ServerRegistry(servers_config, clients={"sajha": FixtureClient("sajha", sajha_fixture)})


def test_env_expansion(monkeypatch):
    monkeypatch.setenv("X_URL", "http://real")
    monkeypatch.delenv("Y_URL", raising=False)
    assert expand_env({"a": "${X_URL}/mcp", "b": ["${Y_URL:-http://fallback}"]}) == {"a": "http://real/mcp", "b": ["http://fallback"]}


def test_categories_from_metadata_and_patterns(servers_config, sajha_fixture):
    reg = _registry(servers_config, sajha_fixture)
    tools = reg.tools("sajha")
    assert tools["tavily_news_search"].category == "web"
    assert tools["duckdb_query"].category == "structured"
    assert tools["iris_limit_lookup"].category == "structured"
    assert tools["pdf_read"].category == "unstructured"
    assert tools["generate_chart"].category == "other"


def test_allowlist_blocks_write_tools(servers_config, sajha_fixture):
    reg = _registry(servers_config, sajha_fixture)
    assert "outlook_send_email" not in reg.tools("sajha")
    assert "outlook_send_email" in reg.tools("sajha", include_blocked=True)
    with pytest.raises(ToolError, match="allowlist"):
        reg.tool("sajha", "outlook_send_email")
    with pytest.raises(ToolError, match="not found"):
        reg.tool("sajha", "does_not_exist")


def test_palette_groups_and_hides_internal_args(servers_config, sajha_fixture):
    reg = _registry(servers_config, sajha_fixture)
    palette = reg.palette(["sajha"])
    web = {t["tool"]: t for t in palette["categories"]["web"]}
    assert set(web) >= {"tavily_news_search", "tavily_domain_search", "tavily_web_search", "tavily_research_search"}
    entry = web["tavily_news_search"]
    assert "_worker_context" not in entry["input_schema"]["properties"]
    assert entry["required"] == ["query"]
    assert entry["node_template"] == {"type": "tool", "server": "sajha", "tool": "tavily_news_search", "args": {}}


def test_palette_reports_unreachable_server(servers_config, sajha_fixture):
    reg = _registry(servers_config, sajha_fixture)
    palette = reg.palette(["sajha", "generic_mcp_example"])
    assert "generic_mcp_example" in palette["errors"]
    assert palette["categories"]["web"]
