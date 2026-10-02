"""Static checks run before a workflow starts (and by `jsonflow validate`)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from jsonflow.errors import JsonFlowError, SpecError
from jsonflow.expressions import CONDITION_OPS, references
from jsonflow.mcp.registry import ServerRegistry
from jsonflow.spec import END, ForEachNode, LLMNode, RouterNode, ToolNode, TransformNode, Workflow
from jsonflow.transforms import TRANSFORM_OPS


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _templates(node: Any) -> Iterable[Any]:
    if isinstance(node, ToolNode):
        yield node.args
    elif isinstance(node, LLMNode):
        yield node.prompt
        yield node.system
    elif isinstance(node, TransformNode):
        yield node.input
        yield node.steps
    elif isinstance(node, ForEachNode):
        yield node.items
        yield from _templates(node.body)
    elif isinstance(node, RouterNode):
        yield [r.when for r in node.routes]


def _conditions(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        if "op" in obj and ("left" in obj or obj.get("op") in ("empty", "not_empty", "truthy", "falsy")):
            yield obj
        for v in obj.values():
            yield from _conditions(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _conditions(v)


def _check_leaf(wf: Workflow, node: Any, label: str, report: Report, registry: Optional[ServerRegistry]) -> None:
    if isinstance(node, LLMNode):
        for rel in (node.prompt_file, node.system_file):
            if rel:
                try:
                    wf.resolve_file(rel)
                except SpecError as e:
                    report.errors.append(f"{label}: {e}")
    elif isinstance(node, TransformNode):
        for i, step in enumerate(node.steps):
            if step.get("op") not in TRANSFORM_OPS:
                report.errors.append(f"{label}: step {i} has unknown op {step.get('op')!r}")
    elif isinstance(node, ToolNode) and registry is not None:
        if node.server not in registry.server_names():
            report.errors.append(f"{label}: unknown MCP server {node.server!r}")
            return
        if not registry.is_allowed(node.server, node.tool):
            report.errors.append(f"{label}: tool {node.server}.{node.tool} is blocked by the server allowlist")
            return
        try:
            tools = registry.tools(node.server)
        except JsonFlowError as e:
            report.warnings.append(f"{label}: could not verify tool {node.server}.{node.tool} ({e})")
            return
        info = tools.get(node.tool)
        if info is None:
            report.errors.append(f"{label}: tool {node.tool!r} not found on server {node.server!r}")
            return
        required = [r for r in (info.input_schema or {}).get("required", []) if not r.startswith("_")]
        missing = [r for r in required if r not in node.args]
        if missing:
            report.errors.append(f"{label}: missing required tool args {missing}")
        known = set((info.input_schema or {}).get("properties", {}))
        extra = [a for a in node.args if known and a not in known]
        if extra:
            report.warnings.append(f"{label}: args not in tool schema {extra}")


def validate_workflow(wf: Workflow, registry: Optional[ServerRegistry] = None) -> Report:
    from jsonflow.engine import successors  # local import: engine imports langgraph

    report = Report()
    ids = {n.id for n in wf.nodes}
    for n in wf.nodes:
        for ref in sorted(set().union(*[references(t) for t in _templates(n)])):
            if ref not in ids:
                report.errors.append(f"{n.id}: references unknown node 'nodes.{ref}'")
        for cond in _conditions(list(_templates(n))):
            if cond.get("op") not in CONDITION_OPS:
                report.errors.append(f"{n.id}: unknown condition op {cond.get('op')!r}")
        if isinstance(n, ForEachNode):
            _check_leaf(wf, n.body, f"{n.id}.body", report, registry)
        else:
            _check_leaf(wf, n, n.id, report, registry)
    for ref in references(wf.output):
        if ref not in ids:
            report.errors.append(f"output: references unknown node 'nodes.{ref}'")

    # Branches that meet at one node.
    from jsonflow.engine import static_predecessors

    preds = static_predecessors(wf)
    router_targets = {t for n in wf.nodes if isinstance(n, RouterNode) for t in [r.goto for r in n.routes] + [n.default]}
    for n in wf.nodes:
        if n.join == "all" and n.id in router_targets:
            report.errors.append(f"{n.id}: join 'all' cannot be a router target (a skipped route would block it forever)")
        elif n.join == "any" and len(preds[n.id]) > 1:
            report.warnings.append(f"{n.id}: {len(preds[n.id])} branches lead here; it runs once per branch that arrives. "
                                   "Set join to 'all' if those branches run in parallel.")

    # Reachability from the start node.
    succ = successors(wf)
    seen, stack = set(), [wf.start or wf.nodes[0].id]
    while stack:
        cur = stack.pop()
        if cur == END or cur in seen:
            continue
        seen.add(cur)
        stack.extend(succ.get(cur, []))
    for n in wf.nodes:
        if n.id not in seen:
            report.warnings.append(f"{n.id}: unreachable from the start node")
    return report
