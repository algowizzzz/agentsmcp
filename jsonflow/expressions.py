"""Template rendering and structured conditions.

Templates
---------
Any string inside a node's JSON may contain ``{{ expr }}``.

* A string that is exactly one expression returns the raw value, so
  ``"{{ nodes.search }}"`` yields the list itself, not its text.
* A string mixing text and expressions renders to text. Non-string values are
  inserted as JSON.

An expression is a dotted path followed by optional filters::

    nodes.collect_articles[0].title | truncate(80)
    inputs.trusted_domains | join(", ")
    nodes.maybe_missing | default([])

Roots available in the context: ``inputs``, ``nodes``, ``run`` and, inside a
for_each body or a transform step, ``item``, ``index`` and the loop alias.

There is deliberately no eval. Conditions are JSON objects instead (see
``evaluate_condition``) so a canvas editor can build them with dropdowns.
"""
from __future__ import annotations

import json
import re
from typing import Any, Mapping
from urllib.parse import urlsplit

from jsonflow.errors import ExpressionError

_FULL_RE = re.compile(r"^\s*\{\{\s*(.+?)\s*\}\}\s*$", re.S)
_PART_RE = re.compile(r"\{\{\s*(.+?)\s*\}\}", re.S)
_SEG_RE = re.compile(r"([^.\[\]]+)|\[(-?\d+)\]")
_FILTER_RE = re.compile(r"^([a-z_]+)\s*(?:\((.*)\))?$", re.S)


class _Missing:
    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return "<missing>"


MISSING = _Missing()


# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
def get_path(value: Any, path: str) -> Any:
    """Walk a dotted path such as ``a.b[0].c``. Returns MISSING when absent."""
    if path in ("", "."):
        return value
    cur = value
    pos = 0
    for m in _SEG_RE.finditer(path):
        if m.start() != pos and path[pos:m.start()] != ".":
            raise ExpressionError(f"bad path syntax: {path!r}")
        pos = m.end()
        key, idx = m.group(1), m.group(2)
        if idx is not None:
            if not isinstance(cur, list):
                return MISSING
            i = int(idx)
            if -len(cur) <= i < len(cur):
                cur = cur[i]
            else:
                return MISSING
        else:
            if isinstance(cur, Mapping) and key in cur:
                cur = cur[key]
            elif isinstance(cur, list) and key.isdigit() and int(key) < len(cur):
                cur = cur[int(key)]
            else:
                return MISSING
    if pos != len(path):
        raise ExpressionError(f"bad path syntax: {path!r}")
    return cur


# --------------------------------------------------------------------------
# Filters
# --------------------------------------------------------------------------
def _split_pipes(expr: str) -> list[str]:
    parts, depth, quote, buf = [], 0, None, []
    for ch in expr:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "|" and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    parts.append("".join(buf).strip())
    return parts


def _parse_arg(raw: str | None) -> Any:
    if raw is None or raw.strip() == "":
        return MISSING
    raw = raw.strip()
    if raw.startswith("'") and raw.endswith("'"):
        raw = json.dumps(raw[1:-1])
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ExpressionError(f"filter argument must be a JSON literal, got {raw!r}") from e


def _apply_filter(name: str, arg: Any, value: Any) -> Any:
    if name == "default":
        return (None if arg is MISSING else arg) if value is MISSING or value is None else value
    if value is MISSING:
        return MISSING
    if name == "json":
        return json.dumps(value, ensure_ascii=False, default=str)
    if name == "pretty":
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if name == "length":
        return len(value) if value is not None else 0
    if name == "join":
        sep = ", " if arg is MISSING else str(arg)
        return sep.join(str(v) for v in (value or []))
    if name == "upper":
        return str(value).upper()
    if name == "lower":
        return str(value).lower()
    if name == "first":
        return value[0] if value else None
    if name == "last":
        return value[-1] if value else None
    if name == "truncate":
        n = 200 if arg is MISSING else int(arg)
        s = "" if value is None else str(value)
        return s if len(s) <= n else s[: max(n - 1, 0)] + "…"
    if name == "pluck":
        if arg is MISSING:
            raise ExpressionError("pluck needs a field name, e.g. pluck('url')")
        out = []
        for v in value or []:
            got = get_path(v, str(arg))
            if got is not MISSING:
                out.append(got)
        return out
    if name == "domain":
        host = urlsplit(str(value or "")).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    if name == "keys":
        return list(value.keys()) if isinstance(value, Mapping) else []
    raise ExpressionError(f"unknown filter {name!r}")


# --------------------------------------------------------------------------
# Expressions and templates
# --------------------------------------------------------------------------
def evaluate(expr: str, ctx: Mapping[str, Any]) -> Any:
    parts = _split_pipes(expr)
    head = parts[0]
    if head == "":
        raise ExpressionError("empty expression")
    if len(head) >= 2 and head[0] == head[-1] == "'":
        value = head[1:-1]  # 'single-quoted' string literal
    else:
        try:
            value = json.loads(head)  # literal: number, "string", true, null, [..]
        except json.JSONDecodeError:
            value = get_path(ctx, head)
    for p in parts[1:]:
        m = _FILTER_RE.match(p)
        if not m:
            raise ExpressionError(f"bad filter syntax: {p!r}")
        value = _apply_filter(m.group(1), _parse_arg(m.group(2)), value)
    if value is MISSING:
        raise ExpressionError(f"'{head}' is not available (add '| default(...)' if it is optional)")
    return value


def _to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False, default=str)


def render(template: Any, ctx: Mapping[str, Any]) -> Any:
    """Render templates recursively inside strings, lists and dicts."""
    if isinstance(template, str):
        if "{{" not in template:
            return template
        full = _FULL_RE.match(template)
        if full and "{{" not in full.group(1):
            return evaluate(full.group(1), ctx)
        return _PART_RE.sub(lambda m: _to_text(evaluate(m.group(1), ctx)), template)
    if isinstance(template, list):
        return [render(t, ctx) for t in template]
    if isinstance(template, dict):
        return {k: render(v, ctx) for k, v in template.items()}
    return template


def references(template: Any) -> set[str]:
    """Node ids referenced as ``nodes.<id>`` anywhere in a template."""
    found: set[str] = set()
    if isinstance(template, str):
        for m in _PART_RE.finditer(template):
            head = _split_pipes(m.group(1))[0]
            if head.startswith("nodes."):
                found.add(head.split(".", 2)[1].split("[", 1)[0])
    elif isinstance(template, list):
        for t in template:
            found |= references(t)
    elif isinstance(template, dict):
        for v in template.values():
            found |= references(v)
    return found


# --------------------------------------------------------------------------
# Conditions
# --------------------------------------------------------------------------
_OPS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a is not None and a > b,
    "gte": lambda a, b: a is not None and a >= b,
    "lt": lambda a, b: a is not None and a < b,
    "lte": lambda a, b: a is not None and a <= b,
    "in": lambda a, b: a in (b or []),
    "not_in": lambda a, b: a not in (b or []),
    "contains": lambda a, b: a is not None and b in a,
    "empty": lambda a, _b: not a,
    "not_empty": lambda a, _b: bool(a),
    "truthy": lambda a, _b: bool(a),
    "falsy": lambda a, _b: not a,
    "length_gt": lambda a, b: len(a or []) > b,
    "length_gte": lambda a, b: len(a or []) >= b,
}


def evaluate_condition(cond: Mapping[str, Any], ctx: Mapping[str, Any]) -> bool:
    """Evaluate a JSON condition.

    Shapes::

        {"left": "{{ nodes.x | length }}", "op": "gt", "right": 0}
        {"all": [cond, cond]}
        {"any": [cond, cond]}
        {"not": cond}
    """
    if "all" in cond:
        return all(evaluate_condition(c, ctx) for c in cond["all"])
    if "any" in cond:
        return any(evaluate_condition(c, ctx) for c in cond["any"])
    if "not" in cond:
        return not evaluate_condition(cond["not"], ctx)
    op = cond.get("op")
    if op not in _OPS:
        raise ExpressionError(f"unknown condition op {op!r}; allowed: {sorted(_OPS)}")
    left = render(cond.get("left"), ctx)
    right = render(cond.get("right"), ctx)
    try:
        return bool(_OPS[op](left, right))
    except TypeError as e:
        raise ExpressionError(f"condition {op} cannot compare {left!r} and {right!r}") from e


CONDITION_OPS = sorted(_OPS)
