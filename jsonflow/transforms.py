"""Deterministic transform steps.

A transform node takes one input value and applies ``steps`` in order. Every
step is a small JSON object with an ``op`` key, so a canvas editor can offer
them as a menu. Step arguments may contain templates; per-item arguments
(``map.fields``, ``filter.when``, ``dedupe.key`` written as a template) see
``item`` and ``index``.

Ops
---
flatten   {"path": "results"}                   list of lists, or pluck a list field and concatenate
map       {"fields": {...}, "merge": true}      build a new object per item
pick      {"fields": ["a", "b"]}                keep only listed keys
filter    {"when": <condition>}                 keep items where the condition holds
dedupe    {"key": "url", "normalize": "url"}    keep the first item per key; normalize: url | text | none
sort      {"by": [{"key": "score", "order": "desc", "rank": {...}}]}
limit     {"n": 10}
enumerate {"field": "ref", "start": 1}          add a position number to each item
lookup    {"from": [...], "field": "refs", "match": "ref", "as": "sources", "single": false}
render    {"template": ...}                     replace the value; template sees 'value'
"""
from __future__ import annotations

import re
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit, urlunsplit

from jsonflow.errors import ExpressionError
from jsonflow.expressions import MISSING, evaluate_condition, get_path, render


def _as_list(value: Any, op: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ExpressionError(f"transform op '{op}' needs a list, got {type(value).__name__}")
    return value


def _item_ctx(ctx: Mapping[str, Any], item: Any, index: int) -> dict[str, Any]:
    out = dict(ctx)
    out["item"] = item
    out["index"] = index
    return out


def _key_of(item: Any, key: Any, ctx: Mapping[str, Any], index: int) -> Any:
    if isinstance(key, str) and "{{" in key:
        return render(key, _item_ctx(ctx, item, index))
    got = get_path(item, str(key))
    return None if got is MISSING else got


def normalize_url(url: Any) -> str:
    if not isinstance(url, str) or not url:
        return ""
    parts = urlsplit(url.strip())
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path.rstrip("/")
    return urlunsplit(("", host, path, "", ""))


def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


_NORMALIZERS: dict[str, Callable[[Any], Any]] = {
    "url": normalize_url,
    "text": normalize_text,
    "none": lambda v: v,
}


# --------------------------------------------------------------------------
# Ops
# --------------------------------------------------------------------------
def _flatten(value, step, ctx):
    path = step.get("path")
    out: list[Any] = []
    for item in _as_list(value, "flatten"):
        sub = item
        if path:
            sub = get_path(item, path) if item is not None else MISSING
            if sub is MISSING or sub is None:
                continue
        if isinstance(sub, list):
            out.extend(sub)
        else:
            out.append(sub)
    return out


def _map(value, step, ctx):
    fields = step.get("fields") or {}
    merge = bool(step.get("merge", False))
    out = []
    for i, item in enumerate(_as_list(value, "map")):
        rendered = render(fields, _item_ctx(ctx, item, i))
        if merge and isinstance(item, Mapping):
            new = dict(item)
            new.update(rendered)
            out.append(new)
        else:
            out.append(rendered)
    return out


def _pick(value, step, ctx):
    keys = step.get("fields") or []
    return [{k: item.get(k) for k in keys} for item in _as_list(value, "pick") if isinstance(item, Mapping)]


def _filter(value, step, ctx):
    cond = step.get("when")
    if not isinstance(cond, Mapping):
        raise ExpressionError("filter needs a 'when' condition object")
    return [item for i, item in enumerate(_as_list(value, "filter")) if evaluate_condition(cond, _item_ctx(ctx, item, i))]


def _dedupe(value, step, ctx):
    key = step.get("key")
    norm = _NORMALIZERS.get(step.get("normalize", "none"))
    if norm is None:
        raise ExpressionError(f"dedupe normalize must be one of {sorted(_NORMALIZERS)}")
    seen: set[Any] = set()
    out = []
    for i, item in enumerate(_as_list(value, "dedupe")):
        k = norm(_key_of(item, key, ctx, i) if key else item)
        k = repr(k) if isinstance(k, (dict, list)) else k
        if k in ("", None):
            out.append(item)  # cannot dedupe without a key; keep it
            continue
        if k in seen:
            continue
        seen.add(k)
        out.append(item)
    return out


def _sort(value, step, ctx):
    items = list(_as_list(value, "sort"))
    by = step.get("by")
    if by is None:
        by = [{"key": step.get("key"), "order": step.get("order", "asc"), "rank": step.get("rank")}]
    # Stable multi-key sort: apply keys from last to first.
    for spec in reversed(by):
        key, rank = spec.get("key"), spec.get("rank")
        desc = spec.get("order", "asc") == "desc"

        def k(pair, key=key, rank=rank):
            i, item = pair
            v = _key_of(item, key, ctx, i)
            if rank is not None:
                v = rank.get(v if isinstance(v, str) else str(v), rank.get("_default", 0))
            # None sorts last in both directions.
            return (v is None, v if v is not None else 0) if not desc else (v is not None, v if v is not None else 0)

        items = [it for _, it in sorted(enumerate(items), key=k, reverse=desc)]
    return items


def _limit(value, step, ctx):
    n = step.get("n")
    if n is None:
        raise ExpressionError("limit needs 'n'")
    return _as_list(value, "limit")[: int(n)]


def _enumerate(value, step, ctx):
    field = step.get("field", "index")
    start = int(step.get("start", 0))
    out = []
    for i, item in enumerate(_as_list(value, "enumerate")):
        new = dict(item) if isinstance(item, Mapping) else {"value": item}
        new[field] = i + start
        out.append(new)
    return out


def _lookup(value, step, ctx):
    source = _as_list(step.get("from"), "lookup.from")
    field, match, as_ = step.get("field"), step.get("match"), step.get("as")
    single = bool(step.get("single", False))
    if not (field and match and as_):
        raise ExpressionError("lookup needs 'from', 'field', 'match' and 'as'")
    index: dict[Any, list[Any]] = {}
    for s in source:
        k = get_path(s, match)
        if k is not MISSING:
            index.setdefault(k, []).append(s)
    out = []
    for item in _as_list(value, "lookup"):
        if not isinstance(item, Mapping):
            out.append(item)
            continue
        wanted = get_path(item, field)
        keys = [] if wanted is MISSING or wanted is None else (wanted if isinstance(wanted, list) else [wanted])
        hits = [h for k in keys for h in index.get(k, [])]
        new = dict(item)
        new[as_] = (hits[0] if hits else None) if single else hits
        out.append(new)
    return out


def _render(value, step, ctx):
    local = dict(ctx)
    local["value"] = value
    return render(step.get("template"), local)


OPS: dict[str, Callable[[Any, dict, Mapping[str, Any]], Any]] = {
    "flatten": _flatten,
    "map": _map,
    "pick": _pick,
    "filter": _filter,
    "dedupe": _dedupe,
    "sort": _sort,
    "limit": _limit,
    "enumerate": _enumerate,
    "lookup": _lookup,
    "render": _render,
}

# Step keys rendered once, up front, with the node context (not per item).
_EAGER_KEYS = {"n", "from", "start", "path", "field", "match", "as", "single", "normalize"}


def apply_steps(value: Any, steps: list[dict[str, Any]], ctx: Mapping[str, Any]) -> Any:
    for i, raw in enumerate(steps):
        op = raw.get("op")
        if op not in OPS:
            raise ExpressionError(f"step {i}: unknown transform op {op!r}; allowed: {sorted(OPS)}")
        step = {k: (render(v, ctx) if k in _EAGER_KEYS else v) for k, v in raw.items()}
        try:
            value = OPS[op](value, step, ctx)
        except ExpressionError as e:
            raise ExpressionError(f"step {i} ({op}): {e}") from e
    return value


TRANSFORM_OPS = sorted(OPS)
