import json
from types import SimpleNamespace

import pytest

from jsonflow.errors import LLMError, SpecError
from jsonflow.llm.anthropic_provider import AnthropicProvider
from jsonflow.llm.base import LLMRequest
from jsonflow.llm.scripted import ScriptedProvider
from jsonflow.mcp.fixture import FixtureClient
from jsonflow.mcp.registry import ServerRegistry
from jsonflow.runner import run_workflow
from jsonflow.spec import parse_workflow

TOOLS = {
    "tools": [{"name": "search", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"},
                                                                                   "n": {"type": "integer", "maximum": 5}},
                                                  "required": ["query"]}}],
    "responses": {"search": [{"match": {"query": "bad"}, "error": "upstream failure"},
                             {"result": {"results": [{"title": "t"}]}}]},
}


def _run(doc, inputs=None, llm=None, tmp_path=None, **kw):
    reg = ServerRegistry({"servers": {"s": {"allow_tools": ["*"]}}}, clients={"s": FixtureClient("s", TOOLS)})
    providers = {"anthropic": ScriptedProvider(llm or {})}
    return run_workflow(parse_workflow(doc), inputs, registry=reg, llm_providers=providers,
                        run_dir=tmp_path, **kw), reg.client("s"), providers["anthropic"]


def _for_each(items, **body_over):
    body = {"type": "tool", "server": "s", "tool": "search", "args": {"query": "{{ item }}"}, **body_over}
    return {"id": "loop", "type": "for_each", "items": items, "body": body}


def test_tool_budget_stops_loop_and_records_skips(tmp_path):
    doc = {"id": "t", "budgets": {"max_tool_calls": 2}, "nodes": [_for_each(["a", "b", "c", "d"])]}
    result, client, _ = _run(doc, tmp_path=tmp_path)
    assert result.status == "succeeded"
    assert len(client.calls) == 2 and result.stats["tool_calls"] == 2
    assert result.nodes["loop"][2:] == [None, None]
    fe = [e for e in result.trace if e["event"] == "for_each"][0]
    assert fe["items_skipped"] == 2


def test_for_each_item_errors_continue_or_fail(tmp_path):
    doc = {"id": "t", "nodes": [{**_for_each(["ok", "bad", "ok2"]), "include_item": True}]}
    result, _, _ = _run(doc, tmp_path=tmp_path)
    pairs = result.nodes["loop"]
    assert pairs[1]["result"] is None and "upstream failure" in pairs[1]["error"]
    assert pairs[0]["result"]["results"] and pairs[2]["error"] is None

    doc["nodes"][0]["on_item_error"] = "fail"
    result, _, _ = _run(doc, tmp_path=tmp_path)
    assert result.status == "failed" and "upstream failure" in result.error


def test_max_items_template_and_concurrency(tmp_path):
    doc = {"id": "t", "inputs": {"k": {"type": "integer", "default": 2}},
           "nodes": [{**_for_each(["a", "b", "c"]), "max_items": "{{ inputs.k }}", "concurrency": 3}]}
    result, client, _ = _run(doc, tmp_path=tmp_path)
    assert len(result.nodes["loop"]) == 2 and len(client.calls) == 2


def test_args_validated_against_tool_schema_before_call(tmp_path):
    doc = {"id": "t", "nodes": [{"id": "a", "type": "tool", "server": "s", "tool": "search", "args": {"query": "q", "n": 99}}]}
    result, client, _ = _run(doc, tmp_path=tmp_path)
    assert result.status == "failed" and "tool schema" in result.error and client.calls == []


def test_static_validation_catches_missing_args_and_unknown_tools(tmp_path):
    doc = {"id": "t", "nodes": [{"id": "a", "type": "tool", "server": "s", "tool": "search", "args": {}},
                                {"id": "b", "type": "tool", "server": "s", "tool": "nope", "args": {}},
                                {"id": "c", "type": "transform", "input": "{{ nodes.ghost }}"}]}
    with pytest.raises(SpecError) as e:
        _run(doc, tmp_path=tmp_path)
    msg = str(e.value)
    assert "missing required tool args ['query']" in msg and "'nope' not found" in msg and "nodes.ghost" in msg


def test_on_error_continue_keeps_running(tmp_path):
    doc = {"id": "t", "nodes": [
        {"id": "a", "type": "tool", "server": "s", "tool": "search", "args": {"query": "bad"}, "on_error": "continue"},
        {"id": "b", "type": "transform", "input": "{{ nodes.a | default('fallback') }}"}]}
    result, _, _ = _run(doc, tmp_path=tmp_path)
    assert result.status == "succeeded" and result.nodes["b"] == "fallback"
    assert result.stats["node_errors"][0]["node"] == "a"


def test_router_loop_bounded_by_max_steps(tmp_path):
    doc = {"id": "t", "budgets": {"max_steps": 6}, "nodes": [
        {"id": "a", "type": "transform", "input": 1},
        {"id": "r", "type": "router", "routes": [{"when": {"left": 1, "op": "eq", "right": 1}, "goto": "a"}]}]}
    result, _, _ = _run(doc, tmp_path=tmp_path)
    assert result.status == "failed" and "max_steps" in result.error


def test_explicit_edges_and_router_branches(tmp_path):
    doc = {"id": "t", "inputs": {"x": {"type": "integer", "default": 5}}, "nodes": [
        {"id": "r", "type": "router", "routes": [{"when": {"left": "{{ inputs.x }}", "op": "gt", "right": 3}, "goto": "big"}], "default": "small"},
        {"id": "big", "type": "transform", "input": "big"},
        {"id": "small", "type": "transform", "input": "small"},
        {"id": "done", "type": "transform", "input": "{{ nodes.big | default('') }}{{ nodes.small | default('') }}"}],
        "edges": [["big", "done"], ["small", "done"]],
        "output": "{{ nodes.done }}"}
    assert _run(doc, tmp_path=tmp_path)[0].output == "big"
    assert _run(doc, {"x": 1}, tmp_path=tmp_path)[0].output == "small"


def test_llm_schema_repair_retry_then_failure(tmp_path):
    schema = {"type": "object", "required": ["n"], "properties": {"n": {"type": "integer"}}}
    doc = {"id": "t", "nodes": [{"id": "l", "type": "llm", "prompt": "count", "output_schema": schema}], "output": "{{ nodes.l.n }}"}
    result, _, llm = _run(doc, llm={"l": [{"n": "three"}, {"n": 3}]}, tmp_path=tmp_path)
    assert result.output == 3 and result.stats["llm_calls"] == 2
    assert "did not match the required output schema" in llm.requests[1].prompt

    result, _, _ = _run(doc, llm={"l": [{"n": "x"}, {"n": "y"}]}, tmp_path=tmp_path)
    assert result.status == "failed" and "schema validation" in result.error


def test_llm_budget(tmp_path):
    doc = {"id": "t", "budgets": {"max_llm_calls": 1}, "nodes": [
        {"id": "a", "type": "llm", "prompt": "x"}, {"id": "b", "type": "llm", "prompt": "y"}]}
    result, _, _ = _run(doc, llm={"a": "1", "b": "2"}, tmp_path=tmp_path)
    assert result.status == "failed" and "budget" in result.error and result.nodes["a"] == "1"


def test_input_validation():
    doc = {"id": "t", "inputs": {"n": {"type": "integer", "required": True}}, "nodes": [{"id": "a", "type": "transform"}]}
    with pytest.raises(SpecError, match="missing required input"):
        _run(doc)
    with pytest.raises(SpecError, match="must be integer"):
        _run(doc, {"n": "5"})
    with pytest.raises(SpecError, match="unknown inputs"):
        _run(doc, {"n": 1, "zzz": 2})


def test_secrets_redacted_in_audit(tmp_path):
    tools = json.loads(json.dumps(TOOLS))
    tools["tools"][0]["inputSchema"]["properties"]["api_key"] = {"type": "string"}
    reg = ServerRegistry({"servers": {"s": {}}}, clients={"s": FixtureClient("s", tools)})
    doc = {"id": "t", "nodes": [{"id": "a", "type": "tool", "server": "s", "tool": "search", "args": {"query": "q", "api_key": "SECRET"}}]}
    result = run_workflow(parse_workflow(doc), registry=reg, run_dir=tmp_path)
    trace = (tmp_path / result.run_id / "trace.jsonl").read_text()
    call = (tmp_path / result.run_id / "calls" / "a.tool.json").read_text()
    assert "SECRET" not in trace and "SECRET" not in call


# ------------------------------------------------------------- Anthropic
class _FakeMessages:
    def __init__(self, content, stop="tool_use"):
        self.kwargs = None
        self._content, self._stop = content, stop

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(content=self._content, stop_reason=self._stop, model=kwargs["model"],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5))


def test_anthropic_provider_forces_output_tool():
    msgs = _FakeMessages([SimpleNamespace(type="tool_use", name="submit_output", input={"n": 1})])
    provider = AnthropicProvider(client=SimpleNamespace(messages=msgs))
    schema = {"type": "object", "properties": {"n": {"type": "integer"}}}
    resp = provider.complete(LLMRequest(node_id="x", prompt="p", model="claude-opus-5-5", system="s", output_schema=schema))
    assert resp.data == {"n": 1} and resp.usage == {"input_tokens": 10, "output_tokens": 5}
    assert msgs.kwargs["tool_choice"] == {"type": "tool", "name": "submit_output"}
    assert msgs.kwargs["tools"][0]["input_schema"] == schema and msgs.kwargs["system"] == "s"


def test_anthropic_provider_text_and_missing_tool():
    text = AnthropicProvider(client=SimpleNamespace(messages=_FakeMessages([SimpleNamespace(type="text", text="hi")], "end_turn")))
    assert text.complete(LLMRequest(node_id="x", prompt="p", model="m")).text == "hi"
    with pytest.raises(LLMError, match="did not return structured output"):
        text.complete(LLMRequest(node_id="x", prompt="p", model="m", output_schema={"type": "object"}))
