"""Node executors and the JSON -> LangGraph compiler.

The workflow controls the order of work; nodes never choose their own
successors except through router conditions written in the JSON. Budgets,
allowlists and argument validation are enforced here, at run time, so a user
editing the graph cannot remove them.
"""
from __future__ import annotations

import copy
import hashlib
import json
import operator
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Callable, Optional, TypedDict

import jsonschema
from langgraph.graph import END as LG_END
from langgraph.graph import START, StateGraph

from jsonflow.errors import BudgetExceeded, ExpressionError, JsonFlowError, LLMError, ToolError
from jsonflow.expressions import MISSING, evaluate_condition, get_path, render
from jsonflow.llm.base import LLMProvider, LLMRequest, build_provider, default_model, default_provider
from jsonflow.mcp.registry import ServerRegistry
from jsonflow.spec import END, ForEachNode, LLMNode, RouterNode, ToolNode, TransformNode, Workflow
from jsonflow.transforms import apply_steps

_REDACT = ("password", "api_key", "apikey", "token", "secret", "authorization")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: "[REDACTED]" if any(s in k.lower() for s in _REDACT) else _redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def _size(value: Any) -> int:
    try:
        return len(json.dumps(value, default=str))
    except (TypeError, ValueError):
        return -1


def _slug(label: str) -> str:
    label = label.replace("[", ".").replace("]", "")
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in label)


# --------------------------------------------------------------------------
# Run context: budgets, providers, audit trail
# --------------------------------------------------------------------------
class RunContext:
    def __init__(
        self,
        workflow: Workflow,
        registry: ServerRegistry,
        llm_providers: Optional[dict[str, LLMProvider]] = None,
        run_dir: Optional[Path] = None,
        run_id: Optional[str] = None,
    ) -> None:
        self.workflow = workflow
        self.registry = registry
        self.run_id = run_id or f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}"
        self.started_at = _now()
        self._providers: dict[str, LLMProvider] = dict(llm_providers or {})
        self._lock = threading.Lock()
        self.counts = {"tool": 0, "llm": 0}
        self.limits = {"tool": workflow.budgets.max_tool_calls, "llm": workflow.budgets.max_llm_calls}
        self.trace: list[dict[str, Any]] = []
        self.run_dir = Path(run_dir) / self.run_id if run_dir else None
        if self.run_dir:
            (self.run_dir / "nodes").mkdir(parents=True, exist_ok=True)
            (self.run_dir / "calls").mkdir(parents=True, exist_ok=True)
        today = datetime.now(timezone.utc)
        self.meta = {
            "id": self.run_id,
            "started_at": self.started_at,
            "date": today.strftime("%Y-%m-%d"),
            "date_compact": today.strftime("%Y%m%d"),
            "workflow_id": workflow.id,
            "workflow_version": workflow.version,
        }

    # budgets ---------------------------------------------------------------
    def consume(self, kind: str) -> None:
        with self._lock:
            if self.counts[kind] >= self.limits[kind]:
                raise BudgetExceeded(f"{kind} call budget of {self.limits[kind]} reached")
            self.counts[kind] += 1

    # providers -------------------------------------------------------------
    def provider(self, name: str) -> LLMProvider:
        with self._lock:
            if name not in self._providers:
                self._providers[name] = build_provider(name)
            return self._providers[name]

    # audit -----------------------------------------------------------------
    def record(self, event: dict[str, Any]) -> None:
        event = {"run_id": self.run_id, "ts": _now(), **event}
        with self._lock:
            self.trace.append(event)
            if self.run_dir:
                with open(self.run_dir / "trace.jsonl", "a") as f:
                    f.write(json.dumps(event, default=str) + "\n")

    def save(self, rel: str, payload: Any) -> Optional[str]:
        if not self.run_dir:
            return None
        path = self.run_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False))
        return str(path.relative_to(self.run_dir))

    def scope(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"inputs": state.get("inputs", {}), "nodes": state.get("nodes", {}), "run": self.meta}


# --------------------------------------------------------------------------
# Leaf executors
# --------------------------------------------------------------------------
def _validate_args(args: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    if not schema:
        return
    schema = copy.deepcopy(schema)
    if "required" in schema:
        schema["required"] = [r for r in schema["required"] if not r.startswith("_")]
    errors = sorted(jsonschema.validators.validator_for(schema)(schema).iter_errors(args), key=lambda e: list(e.path))
    if errors:
        msgs = "; ".join(f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in errors[:5])
        raise ToolError(f"{label}: arguments do not match the tool schema: {msgs}")


def run_tool(node: ToolNode, ctx: RunContext, scope: dict[str, Any], label: str) -> Any:
    info = ctx.registry.tool(node.server, node.tool)
    args = render(node.args, scope)
    if not isinstance(args, dict):
        raise ToolError(f"{label}: args must render to an object")
    _validate_args(args, info.input_schema, label)
    client = ctx.registry.client(node.server)
    last_error: Optional[Exception] = None
    for attempt in range(node.retries + 1):
        ctx.consume("tool")
        t0 = time.time()
        try:
            result = client.call_tool(node.tool, args, timeout=node.timeout)
        except ToolError as e:
            last_error = e
            ctx.record({"event": "tool_call", "node": label, "server": node.server, "tool": node.tool,
                        "args": _redact(args), "attempt": attempt + 1, "status": "error", "error": str(e),
                        "duration_ms": round((time.time() - t0) * 1000)})
            continue
        saved = ctx.save(f"calls/{_slug(label)}.tool.json", {"server": node.server, "tool": node.tool,
                                                          "args": _redact(args), "result": result})
        ctx.record({"event": "tool_call", "node": label, "server": node.server, "tool": node.tool,
                    "category": info.category, "args": _redact(args), "attempt": attempt + 1, "status": "ok",
                    "result_bytes": _size(result), "saved": saved, "duration_ms": round((time.time() - t0) * 1000)})
        if node.select:
            picked = get_path(result, node.select)
            if picked is MISSING:
                raise ToolError(f"{label}: result has no '{node.select}'")
            return picked
        return result
    raise ToolError(f"{label}: {last_error}")


def _read_text(ctx: RunContext, rel: Optional[str]) -> Optional[str]:
    return ctx.workflow.resolve_file(rel).read_text() if rel else None


def _as_prompt(value: Any) -> str:
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2, default=str)


def run_llm(node: LLMNode, ctx: RunContext, scope: dict[str, Any], label: str) -> Any:
    system_t = node.system or _read_text(ctx, node.system_file)
    prompt_t = node.prompt or _read_text(ctx, node.prompt_file)
    system = _as_prompt(render(system_t, scope)) if system_t else None
    prompt = _as_prompt(render(prompt_t, scope))
    provider_name = node.provider or ctx.workflow.defaults.get("provider") or default_provider()
    model = node.model or ctx.workflow.defaults.get("model") or default_model(provider_name)
    provider = ctx.provider(provider_name)
    schema = node.output_schema
    validator = jsonschema.validators.validator_for(schema)(schema) if schema else None
    attempts = 2 if schema else 1  # one repair retry for schema violations
    request = LLMRequest(node_id=label.split("[", 1)[0], prompt=prompt, model=model, system=system,
                         temperature=node.temperature, max_tokens=node.max_tokens, output_schema=schema)
    for attempt in range(1, attempts + 1):
        ctx.consume("llm")
        t0 = time.time()
        resp = provider.complete(request)
        problems = []
        if validator is not None:
            problems = [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in validator.iter_errors(resp.data)][:8]
        saved = ctx.save(f"calls/{_slug(label)}.llm{attempt}.json", {
            "provider": provider_name, "model": resp.model or model, "system": system, "prompt": request.prompt,
            "output": resp.data if schema else resp.text, "schema_errors": problems, "usage": resp.usage})
        ctx.record({"event": "llm_call", "node": label, "provider": provider_name, "model": resp.model or model,
                    "attempt": attempt, "status": "ok" if not problems else "schema_error",
                    "prompt_sha256": hashlib.sha256(request.prompt.encode()).hexdigest(),
                    "usage": resp.usage, "saved": saved, "duration_ms": round((time.time() - t0) * 1000)})
        if not problems:
            return resp.data if schema else resp.text
        request.prompt = (
            f"{prompt}\n\nYour previous answer did not match the required output schema.\n"
            f"Problems:\n- " + "\n- ".join(problems) + "\nReturn a corrected answer."
        )
    raise LLMError(f"{label}: output failed schema validation: {'; '.join(problems)}")


def run_transform(node: TransformNode, ctx: RunContext, scope: dict[str, Any], label: str) -> Any:
    return apply_steps(render(node.input, scope), node.steps, scope)


_LEAF: dict[type, Callable[..., Any]] = {ToolNode: run_tool, LLMNode: run_llm, TransformNode: run_transform}


def run_leaf(node: Any, ctx: RunContext, scope: dict[str, Any], label: str) -> Any:
    return _LEAF[type(node)](node, ctx, scope, label)


def run_for_each(node: ForEachNode, ctx: RunContext, scope: dict[str, Any], label: str) -> Any:
    items = render(node.items, scope)
    if items is None:
        items = []
    if not isinstance(items, list):
        raise ExpressionError(f"{label}: 'items' must render to a list, got {type(items).__name__}")
    total = len(items)
    if node.max_items is not None:
        limit = render(node.max_items, scope)
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            raise ExpressionError(f"{label}: max_items must render to a non-negative integer, got {limit!r}")
        items = items[:limit]
    results: list[Any] = [None] * len(items)
    errors: list[Optional[str]] = [None] * len(items)
    stop = threading.Event()

    def work(i: int) -> None:
        if stop.is_set():
            errors[i] = "skipped: budget exhausted"
            return
        local = dict(scope)
        local.update({"item": items[i], "index": i, node.as_: items[i]})
        try:
            results[i] = run_leaf(node.body, ctx, local, f"{label}[{i}]")
        except BudgetExceeded as e:
            stop.set()
            errors[i] = f"skipped: {e}"
        except JsonFlowError as e:
            errors[i] = str(e)
            if node.on_item_error == "fail":
                stop.set()

    if node.concurrency > 1:
        with ThreadPoolExecutor(max_workers=node.concurrency) as pool:
            list(pool.map(work, range(len(items))))
    else:
        for i in range(len(items)):
            work(i)

    failed = [(i, e) for i, e in enumerate(errors) if e and not e.startswith("skipped")]
    skipped = sum(1 for e in errors if e and e.startswith("skipped"))
    ctx.record({"event": "for_each", "node": label, "items_total": total, "items_run": len(items) - skipped,
                "items_truncated": total - len(items), "items_skipped": skipped, "items_failed": len(failed)})
    if failed and node.on_item_error == "fail":
        raise JsonFlowError(f"{label}[{failed[0][0]}]: {failed[0][1]}")
    if node.include_item:
        return [{"item": items[i], "result": results[i], "error": errors[i]} for i in range(len(items))]
    return results


# --------------------------------------------------------------------------
# Compiler
# --------------------------------------------------------------------------
def _merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    out = dict(a or {})
    out.update(b or {})
    return out


class FlowState(TypedDict, total=False):
    inputs: dict[str, Any]
    nodes: Annotated[dict[str, Any], _merge]
    errors: Annotated[list[dict[str, Any]], operator.add]


def _make_node_fn(node: Any, ctx: RunContext) -> Callable[[FlowState], dict[str, Any]]:
    def fn(state: FlowState) -> dict[str, Any]:
        scope = ctx.scope(state)
        t0 = time.time()
        ctx.record({"event": "node_start", "node": node.id, "type": node.type})
        try:
            if isinstance(node, RouterNode):
                goto = node.default
                for r in node.routes:
                    if evaluate_condition(r.when, scope):
                        goto = r.goto
                        break
                output: Any = {"goto": goto}
            elif isinstance(node, ForEachNode):
                output = run_for_each(node, ctx, scope, node.id)
            else:
                output = run_leaf(node, ctx, scope, node.id)
        except JsonFlowError as e:
            ctx.record({"event": "node_end", "node": node.id, "type": node.type, "status": "error",
                        "error": str(e), "duration_ms": round((time.time() - t0) * 1000)})
            if node.on_error == "continue" and not isinstance(node, RouterNode):
                return {"nodes": {node.id: None}, "errors": [{"node": node.id, "error": str(e)}]}
            raise
        saved = ctx.save(f"nodes/{node.id}.json", output)
        ctx.record({"event": "node_end", "node": node.id, "type": node.type, "status": "ok",
                    "output_bytes": _size(output), "saved": saved, "duration_ms": round((time.time() - t0) * 1000),
                    **({"goto": output["goto"]} if isinstance(node, RouterNode) else {})})
        return {"nodes": {node.id: output}}

    fn.__name__ = f"node_{node.id}"
    return fn


def successors(wf: Workflow) -> dict[str, list[str]]:
    """Static successor map, including every router target."""
    out: dict[str, list[str]] = {n.id: [] for n in wf.nodes}
    for i, n in enumerate(wf.nodes):
        if isinstance(n, RouterNode):
            out[n.id] = list(dict.fromkeys([r.goto for r in n.routes] + [n.default]))
        elif wf.edges is not None:
            out[n.id] = [b for a, b in wf.edges if a == n.id] or [END]
        else:
            out[n.id] = [n.next or (wf.nodes[i + 1].id if i + 1 < len(wf.nodes) else END)]
    return out


def static_predecessors(wf: Workflow) -> dict[str, list[str]]:
    """Incoming plain edges per node (router routes excluded)."""
    succ = successors(wf)
    preds: dict[str, list[str]] = {n.id: [] for n in wf.nodes}
    for n in wf.nodes:
        if isinstance(n, RouterNode):
            continue
        for t in succ[n.id]:
            if t != END:
                preds[t].append(n.id)
    return preds


def compile_workflow(wf: Workflow, ctx: RunContext):
    g = StateGraph(FlowState)
    for n in wf.nodes:
        g.add_node(n.id, _make_node_fn(n, ctx))
    g.add_edge(START, wf.start or wf.nodes[0].id)
    lg = lambda t: LG_END if t == END else t  # noqa: E731
    succ = successors(wf)
    preds = static_predecessors(wf)
    # A node with join "all" and 2+ incoming branches gets one LangGraph join edge,
    # so it runs once after every branch has finished.
    joined = {n.id for n in wf.nodes if n.join == "all" and len(preds[n.id]) > 1}
    for n in wf.nodes:
        if isinstance(n, RouterNode):
            g.add_conditional_edges(n.id, lambda s, nid=n.id: lg(s["nodes"][nid]["goto"]), {lg(t): lg(t) for t in succ[n.id]})
        else:
            for t in succ[n.id]:
                if t not in joined:
                    g.add_edge(n.id, lg(t))
    for target in joined:
        g.add_edge(preds[target], target)
    return g.compile()
