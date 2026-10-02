import pytest

from jsonflow.errors import ExpressionError
from jsonflow.expressions import evaluate_condition, references, render

CTX = {
    "inputs": {"country": "USA", "domains": ["sec.gov", "reuters.com"], "n": 3},
    "nodes": {"search": [{"title": "A", "url": "https://www.reuters.com/x"}, {"title": "B"}], "empty": []},
    "run": {"id": "r1"},
}


def test_full_expression_returns_raw_value():
    assert render("{{ nodes.search }}", CTX) == CTX["nodes"]["search"]
    assert render("{{ inputs.n }}", CTX) == 3


def test_mixed_template_renders_text_and_json():
    assert render("Country {{ inputs.country }} n={{ inputs.n }}", CTX) == "Country USA n=3"
    assert render("d={{ inputs.domains }}", CTX) == 'd=["sec.gov", "reuters.com"]'


def test_nested_structures_and_indexing():
    out = render({"q": "{{ nodes.search[0].title }}", "l": ["{{ nodes.search[-1].title }}"]}, CTX)
    assert out == {"q": "A", "l": ["B"]}


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("{{ inputs.domains | join(', ') }}", "sec.gov, reuters.com"),
        ("{{ nodes.search | length }}", 2),
        ("{{ nodes.search | pluck('title') }}", ["A", "B"]),
        ("{{ nodes.missing | default([]) }}", []),
        ("{{ nodes.search[1].url | default(null) }}", None),
        ("{{ nodes.search[0].url | domain }}", "reuters.com"),
        ("{{ inputs.country | lower }}", "usa"),
        ("{{ 'abcdef' | truncate(4) }}", "abc…"),
    ],
)
def test_filters(expr, expected):
    assert render(expr, CTX) == expected


def test_missing_path_raises_with_hint():
    with pytest.raises(ExpressionError, match="default"):
        render("{{ nodes.nope }}", CTX)


def test_unknown_filter_raises():
    with pytest.raises(ExpressionError, match="unknown filter"):
        render("{{ inputs.n | explode }}", CTX)


def test_conditions():
    assert evaluate_condition({"left": "{{ nodes.search | length }}", "op": "gt", "right": 1}, CTX)
    assert evaluate_condition({"left": "{{ nodes.empty }}", "op": "empty"}, CTX)
    assert evaluate_condition({"all": [{"left": 1, "op": "eq", "right": 1}, {"not": {"left": 1, "op": "eq", "right": 2}}]}, CTX)
    assert evaluate_condition({"any": [{"left": "x", "op": "in", "right": ["x"]}, {"left": 0, "op": "truthy"}]}, CTX)
    with pytest.raises(ExpressionError):
        evaluate_condition({"left": 1, "op": "approximately", "right": 1}, CTX)


def test_references():
    assert references({"a": "{{ nodes.x.y }} and {{ nodes.z[0] | length }}", "b": ["{{ inputs.q }}"]}) == {"x", "z"}
