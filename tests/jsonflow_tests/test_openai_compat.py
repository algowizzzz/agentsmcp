import json

import httpx
import pytest

from jsonflow.errors import LLMError
from jsonflow.llm.base import LLMRequest, default_model
from jsonflow.llm.openai_compat import OpenAICompatProvider
from jsonflow.mcp.fixture import FixtureClient
from jsonflow.mcp.registry import ServerRegistry
from jsonflow.runner import run_workflow

SCHEMA = {"type": "object", "required": ["n"], "properties": {"n": {"type": "integer"}}}


def _provider(reply, seen=None, status=200, **kw):
    def handler(req):
        if seen is not None:
            seen.append({"url": str(req.url), "headers": dict(req.headers), "body": json.loads(req.content)})
        body = reply(json.loads(req.content)) if callable(reply) else reply
        return httpx.Response(status, json=body)

    kw.setdefault("base_url", "http://llm.local/v1")
    kw.setdefault("api_key", "sk-test")
    return OpenAICompatProvider(transport=httpx.MockTransport(handler), **kw)


def _msg(**message):
    return {"model": "served-model", "choices": [{"message": {"role": "assistant", **message}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 3}}


def _tool_call(args):
    return _msg(content=None, tool_calls=[{"id": "c1", "type": "function",
                                           "function": {"name": "submit_output", "arguments": json.dumps(args)}}])


def test_tools_mode_forces_function_and_parses_arguments():
    seen = []
    p = _provider(_tool_call({"n": 4}), seen)
    resp = p.complete(LLMRequest(node_id="x", prompt="p", model="gpt-x", system="sys", output_schema=SCHEMA))
    assert resp.data == {"n": 4} and resp.model == "served-model"
    assert resp.usage == {"input_tokens": 7, "output_tokens": 3}
    req = seen[0]
    assert req["url"] == "http://llm.local/v1/chat/completions"
    assert req["headers"]["authorization"] == "Bearer sk-test"
    assert req["body"]["messages"][0] == {"role": "system", "content": "sys"}
    assert req["body"]["tool_choice"] == {"type": "function", "function": {"name": "submit_output"}}
    assert req["body"]["tools"][0]["function"]["parameters"] == SCHEMA


def test_json_schema_mode():
    seen = []
    p = _provider(_msg(content='{"n": 2}'), seen, structured="json_schema")
    assert p.complete(LLMRequest(node_id="x", prompt="p", model="m", output_schema=SCHEMA)).data == {"n": 2}
    assert seen[0]["body"]["response_format"]["json_schema"]["schema"] == SCHEMA
    assert "tools" not in seen[0]["body"]


def test_json_mode_puts_schema_in_prompt_and_strips_fences():
    seen = []
    p = _provider(_msg(content='```json\n{"n": 5}\n```'), seen, structured="json")
    assert p.complete(LLMRequest(node_id="x", prompt="p", model="m", output_schema=SCHEMA)).data == {"n": 5}
    assert seen[0]["body"]["response_format"] == {"type": "json_object"}
    assert "JSON Schema" in seen[0]["body"]["messages"][-1]["content"]


def test_plain_text_and_azure_style_headers():
    seen = []
    p = _provider(_msg(content="hello"), seen, api_key="", headers={"api-key": "azure-key"})
    assert p.complete(LLMRequest(node_id="x", prompt="p", model="m")).text == "hello"
    assert seen[0]["headers"]["api-key"] == "azure-key" and "authorization" not in seen[0]["headers"]
    assert "tools" not in seen[0]["body"] and "response_format" not in seen[0]["body"]


@pytest.mark.parametrize(
    "reply,status,msg",
    [
        (_msg(content="no tool call"), 200, "did not call submit_output"),
        ({"error": {"message": "bad key"}}, 401, "HTTP 401"),
        ({"weird": True}, 200, "unexpected body"),
    ],
)
def test_errors(reply, status, msg):
    with pytest.raises(LLMError, match=msg):
        _provider(reply, status=status).complete(LLMRequest(node_id="x", prompt="p", model="m", output_schema=SCHEMA))


def test_config_from_env_and_model_required(monkeypatch):
    monkeypatch.delenv("OPENAI_COMPAT_BASE_URL", raising=False)
    with pytest.raises(LLMError, match="OPENAI_COMPAT_BASE_URL"):
        OpenAICompatProvider()
    monkeypatch.delenv("JSONFLOW_LLM_MODEL", raising=False)
    assert default_model("anthropic") == "claude-opus-5-5"
    with pytest.raises(LLMError, match="JSONFLOW_LLM_MODEL"):
        default_model("openai_compat")
    monkeypatch.setenv("JSONFLOW_LLM_MODEL", "llama-3.3-70b")
    assert default_model("openai_compat") == "llama-3.3-70b"


def test_sector_workflow_end_to_end_on_openai_compat(monkeypatch, workflow_path, servers_config, sajha_fixture,
                                                      llm_fixture, tmp_path):
    """Full workflow with every LLM node going through the OpenAI-compatible HTTP path."""
    monkeypatch.setenv("JSONFLOW_LLM_PROVIDER", "openai_compat")
    monkeypatch.setenv("JSONFLOW_LLM_MODEL", "my-served-model")
    seen = []

    def reply(body):
        node = "extract_events" if "Articles:" in body["messages"][-1]["content"] else "assess_validation"
        return _tool_call(llm_fixture[node])

    provider = _provider(reply, seen)
    reg = ServerRegistry(servers_config, clients={"sajha": FixtureClient("sajha", sajha_fixture)})
    result = run_workflow(workflow_path, registry=reg, llm_providers={"openai_compat": provider}, run_dir=tmp_path)
    assert result.status == "succeeded", result.error
    assert [e["validation"]["validation_status"] for e in result.output["events"]] == ["corroborated", "corroborated", "not_found"]
    assert len(seen) == 2 and all(s["body"]["model"] == "my-served-model" for s in seen)
    trace = [e for e in result.trace if e["event"] == "llm_call"]
    assert {e["provider"] for e in trace} == {"openai_compat"}
