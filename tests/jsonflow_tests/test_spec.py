import pytest

from jsonflow.errors import SpecError
from jsonflow.spec import load_workflow, parse_workflow, workflow_json_schema


def _wf(**over):
    base = {"id": "t", "nodes": [{"id": "a", "type": "transform", "input": 1}]}
    base.update(over)
    return base


def test_minimal_workflow_parses_and_hashes():
    wf = parse_workflow(_wf())
    assert wf.nodes[0].type == "transform" and len(wf.source_hash) == 64


@pytest.mark.parametrize(
    "doc,msg",
    [
        (_wf(nodes=[{"id": "a", "type": "transform"}, {"id": "a", "type": "transform"}]), "duplicate node id"),
        (_wf(nodes=[{"id": "bad id", "type": "transform"}]), "must match"),
        (_wf(edges=[["a", "zzz"]]), "edge target"),
        (_wf(nodes=[{"id": "r", "type": "router", "routes": [{"when": {"op": "truthy", "left": 1}, "goto": "nowhere"}]}]), "unknown node"),
        (_wf(nodes=[{"id": "l", "type": "llm"}]), "exactly one of 'prompt'"),
        (_wf(nodes=[{"id": "l", "type": "llm", "prompt": "x", "output_schema": {"type": "array"}}]), "type 'object'"),
        (_wf(nodes=[{"id": "x", "type": "teleport"}]), "teleport"),
        (_wf(nodes=[{"id": "a", "type": "transform", "next": "b"}]), "next 'b' does not exist"),
        (_wf(nodes=[{"id": "a", "type": "transform", "input": 1, "surprise": True}]), "Extra inputs"),
    ],
)
def test_invalid_documents(doc, msg):
    with pytest.raises(SpecError, match=msg):
        parse_workflow(doc)


def test_for_each_body_must_be_leaf():
    with pytest.raises(SpecError):
        parse_workflow(_wf(nodes=[{"id": "f", "type": "for_each", "items": [], "body": {"type": "router"}}]))


def test_sector_workflow_loads(workflow_path):
    wf = load_workflow(workflow_path)
    assert wf.id == "sector_events" and wf.base_dir == workflow_path.parent


def test_json_schema_export():
    schema = workflow_json_schema()
    assert "nodes" in schema["properties"]
