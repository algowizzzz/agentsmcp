"""Run a workflow end to end and persist the audit trail."""
from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from langgraph.errors import GraphRecursionError

from jsonflow.engine import RunContext, compile_workflow
from jsonflow.errors import JsonFlowError, SpecError
from jsonflow.expressions import render
from jsonflow.llm.base import LLMProvider
from jsonflow.mcp.registry import ServerRegistry
from jsonflow.spec import Workflow, load_workflow
from jsonflow.validate import validate_workflow

_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}


@dataclass
class RunResult:
    run_id: str
    status: str  # succeeded | failed
    output: Any = None
    error: Optional[str] = None
    run_dir: Optional[str] = None
    nodes: dict[str, Any] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)


def resolve_inputs(wf: Workflow, given: Optional[dict[str, Any]]) -> dict[str, Any]:
    given = dict(given or {})
    unknown = set(given) - set(wf.inputs)
    if unknown:
        raise SpecError(f"unknown inputs {sorted(unknown)}; workflow accepts {sorted(wf.inputs)}")
    out: dict[str, Any] = {}
    for name, p in wf.inputs.items():
        if name in given:
            value = given[name]
        elif p.default is not None:
            value = p.default
        elif p.required:
            raise SpecError(f"missing required input {name!r}")
        else:
            value = None
        expected = _TYPES[p.type]
        if value is not None and (not isinstance(value, expected) or (p.type in ("integer", "number") and isinstance(value, bool))):
            raise SpecError(f"input {name!r} must be {p.type}, got {type(value).__name__}")
        out[name] = value
    return out


def run_workflow(
    workflow: Workflow | str | Path,
    inputs: Optional[dict[str, Any]] = None,
    *,
    registry: Optional[ServerRegistry] = None,
    servers_config: Optional[str | Path] = None,
    llm_providers: Optional[dict[str, LLMProvider]] = None,
    run_dir: Optional[str | Path] = "runs",
    run_id: Optional[str] = None,
) -> RunResult:
    wf = workflow if isinstance(workflow, Workflow) else load_workflow(workflow)
    if registry is None:
        registry = ServerRegistry.from_file(servers_config or "config/jsonflow/servers.json")
    resolved = resolve_inputs(wf, inputs)

    report = validate_workflow(wf, registry)
    if not report.ok:
        raise SpecError("workflow failed validation:\n- " + "\n- ".join(report.errors))

    ctx = RunContext(wf, registry, llm_providers=llm_providers, run_dir=Path(run_dir) if run_dir else None, run_id=run_id)
    if ctx.run_dir:
        ctx.save("workflow.json", {"source_hash": wf.source_hash, **wf.model_dump(mode="json", by_alias=True, exclude_none=True)})
        ctx.save("inputs.json", resolved)
        for n in wf.nodes:  # snapshot prompt files so the run is reproducible after edits
            body = getattr(n, "body", n)
            for rel in (getattr(body, "prompt_file", None), getattr(body, "system_file", None)):
                if rel:
                    dest = ctx.run_dir / "files" / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(wf.resolve_file(rel), dest)
    ctx.record({"event": "run_start", "workflow_id": wf.id, "workflow_version": wf.version,
                "source_hash": wf.source_hash, "inputs": resolved, "warnings": report.warnings})

    graph = compile_workflow(wf, ctx)
    t0 = time.time()
    state: dict[str, Any] = {"inputs": resolved, "nodes": {}, "errors": []}
    status, error, output = "succeeded", None, None
    try:
        # stream() rather than invoke() so partial outputs survive a failure
        for snapshot in graph.stream(state, config={"recursion_limit": wf.budgets.max_steps}, stream_mode="values"):
            state = snapshot
        output = render(wf.output, ctx.scope(state)) if wf.output is not None else state.get("nodes", {})
    except GraphRecursionError:
        status, error = "failed", f"exceeded max_steps={wf.budgets.max_steps} (router loop?)"
    except JsonFlowError as e:
        status, error = "failed", str(e)

    stats = {"tool_calls": ctx.counts["tool"], "llm_calls": ctx.counts["llm"],
             "budgets": ctx.limits, "duration_ms": round((time.time() - t0) * 1000),
             "node_errors": state.get("errors", [])}
    ctx.record({"event": "run_end", "status": status, "error": error, **stats})
    result = RunResult(run_id=ctx.run_id, status=status, output=output, error=error,
                       run_dir=str(ctx.run_dir) if ctx.run_dir else None, nodes=state.get("nodes", {}),
                       stats=stats, warnings=report.warnings, trace=ctx.trace)
    ctx.save("result.json", {"run_id": ctx.run_id, "status": status, "error": error, "stats": stats,
                             "warnings": report.warnings, "output": output})
    return result
