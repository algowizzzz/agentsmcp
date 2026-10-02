import pytest

from jsonflow.errors import ExpressionError
from jsonflow.transforms import apply_steps, normalize_url

CTX = {"inputs": {"n": 2}, "nodes": {}, "run": {}}


def test_flatten_skips_failed_items():
    value = [{"results": [1, 2]}, None, {"results": [3]}, {"other": 1}]
    assert apply_steps(value, [{"op": "flatten", "path": "results"}], CTX) == [1, 2, 3]


def test_dedupe_by_normalized_url_and_title():
    items = [
        {"url": "https://www.reuters.com/a/", "title": "Hello, World"},
        {"url": "https://reuters.com/a?utm_source=x", "title": "other"},
        {"url": "https://b.com/z", "title": "hello world"},
        {"url": "https://c.com/q", "title": "Unique"},
    ]
    out = apply_steps(items, [{"op": "dedupe", "key": "url", "normalize": "url"},
                              {"op": "dedupe", "key": "title", "normalize": "text"}], CTX)
    assert [i["url"] for i in out] == ["https://www.reuters.com/a/", "https://c.com/q"]


def test_normalize_url():
    assert normalize_url("https://www.SEC.gov/path/?a=1#f") == "//sec.gov/path"


def test_sort_multi_key_with_rank_and_none_last():
    items = [
        {"m": "medium", "c": 0.9}, {"m": "high", "c": 0.5}, {"m": "high", "c": 0.8}, {"m": "low", "c": None},
    ]
    out = apply_steps(items, [{"op": "sort", "by": [
        {"key": "m", "order": "desc", "rank": {"high": 3, "medium": 2, "low": 1}},
        {"key": "c", "order": "desc"}]}], CTX)
    assert [(i["m"], i["c"]) for i in out] == [("high", 0.8), ("high", 0.5), ("medium", 0.9), ("low", None)]

    out = apply_steps([{"s": None}, {"s": 2}, {"s": 1}], [{"op": "sort", "by": [{"key": "s"}]}], CTX)
    assert [i["s"] for i in out] == [1, 2, None]


def test_limit_uses_template_and_enumerate():
    out = apply_steps(["a", "b", "c"], [{"op": "limit", "n": "{{ inputs.n }}"}, {"op": "enumerate", "field": "ref", "start": 1}], CTX)
    assert out == [{"value": "a", "ref": 1}, {"value": "b", "ref": 2}]


def test_filter_map_pick():
    items = [{"a": 1, "b": "x"}, {"a": 0, "b": "y"}]
    out = apply_steps(items, [
        {"op": "filter", "when": {"left": "{{ item.a }}", "op": "truthy"}},
        {"op": "map", "merge": True, "fields": {"label": "{{ item.b | upper }}-{{ index }}"}},
        {"op": "pick", "fields": ["label"]},
    ], CTX)
    assert out == [{"label": "X-0"}]


def test_lookup_list_and_single():
    articles = [{"ref": 1, "t": "a"}, {"ref": 2, "t": "b"}]
    events = [{"id": "E1", "refs": [2, 1, 9]}, {"id": "E2", "refs": []}]
    out = apply_steps(events, [{"op": "lookup", "from": articles, "field": "refs", "match": "ref", "as": "src"}], CTX)
    assert [s["t"] for s in out[0]["src"]] == ["b", "a"]
    assert out[1]["src"] == []
    pairs = [{"item": {"id": "E1"}, "result": [1]}]
    out = apply_steps(events, [{"op": "lookup", "from": pairs, "field": "id", "match": "item.id", "as": "v", "single": True}], CTX)
    assert out[0]["v"]["result"] == [1] and out[1]["v"] is None


def test_render_step_and_errors():
    assert apply_steps([1, 2], [{"op": "render", "template": {"count": "{{ value | length }}"}}], CTX) == {"count": 2}
    with pytest.raises(ExpressionError, match="unknown transform op"):
        apply_steps([], [{"op": "explode"}], CTX)
    with pytest.raises(ExpressionError, match="needs a list"):
        apply_steps({"a": 1}, [{"op": "limit", "n": 1}], CTX)
