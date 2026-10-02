"""Pydantic models for the workflow JSON document.

The document is the single source of truth for a workflow. A future canvas
editor reads and writes exactly this format, so every field here is plain
JSON with no Python code embedded.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from jsonflow.errors import SpecError

END = "END"
_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# --------------------------------------------------------------------------
# Inputs and budgets
# --------------------------------------------------------------------------
class InputParam(_Base):
    type: Literal["string", "integer", "number", "boolean", "array", "object"] = "string"
    default: Any = None
    required: bool = False
    description: str = ""


class Budgets(_Base):
    max_tool_calls: int = Field(20, ge=0)
    max_llm_calls: int = Field(10, ge=0)
    max_steps: int = Field(50, ge=1, description="LangGraph recursion limit; bounds router loops.")


# --------------------------------------------------------------------------
# Leaf node kinds (usable at top level or as a for_each body)
# --------------------------------------------------------------------------
class _NodeBase(_Base):
    id: str = ""
    description: str = ""
    on_error: Literal["fail", "continue"] = "fail"
    next: Optional[str] = Field(None, description="Successor when 'edges' is omitted. Defaults to the next listed node; 'END' stops.")
    ui: dict[str, Any] = Field(default_factory=dict, description="Canvas metadata (position, colour). Ignored by the engine.")


class ToolNode(_NodeBase):
    """Call one tool on one registered MCP server."""

    type: Literal["tool"]
    server: str
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    select: Optional[str] = Field(None, description="Dotted path into the tool result to keep, e.g. 'results'.")
    timeout: Optional[float] = Field(None, gt=0)
    retries: int = Field(0, ge=0, le=3)


class LLMNode(_NodeBase):
    """One LLM call. With output_schema the result is validated JSON."""

    type: Literal["llm"]
    provider: Optional[str] = None
    model: Optional[str] = None
    system: Optional[str] = None
    system_file: Optional[str] = None
    prompt: Optional[str] = None
    prompt_file: Optional[str] = None
    output_schema: Optional[dict[str, Any]] = None
    temperature: float = Field(0.0, ge=0, le=1)
    max_tokens: int = Field(4096, ge=1)

    @model_validator(mode="after")
    def _check_prompt(self) -> "LLMNode":
        if bool(self.prompt) == bool(self.prompt_file):
            raise ValueError("llm node needs exactly one of 'prompt' or 'prompt_file'")
        if self.system and self.system_file:
            raise ValueError("llm node takes 'system' or 'system_file', not both")
        if self.output_schema is not None and self.output_schema.get("type") != "object":
            raise ValueError("output_schema must be a JSON Schema with type 'object'")
        return self


class TransformNode(_NodeBase):
    """Deterministic data shaping with no LLM and no tool call."""

    type: Literal["transform"]
    input: Any = None
    steps: list[dict[str, Any]] = Field(default_factory=list)


LeafNode = Annotated[Union[ToolNode, LLMNode, TransformNode], Field(discriminator="type")]


# --------------------------------------------------------------------------
# Control node kinds
# --------------------------------------------------------------------------
class ForEachNode(_NodeBase):
    """Run a leaf node once per item of a list."""

    type: Literal["for_each"]
    items: Any
    as_: str = Field("item", alias="as")
    max_items: Optional[Union[int, str]] = Field(None, description="Int, or a template such as '{{ inputs.max_validations }}'.")
    concurrency: int = Field(1, ge=1, le=16)
    include_item: bool = Field(False, description="Output [{item, result}] pairs instead of bare results.")
    on_item_error: Literal["fail", "continue"] = "continue"
    body: LeafNode


class Route(_Base):
    when: dict[str, Any]
    goto: str


class RouterNode(_NodeBase):
    """Pick the next node from ordered conditions."""

    type: Literal["router"]
    routes: list[Route] = Field(default_factory=list)
    default: str = END


Node = Annotated[Union[ToolNode, LLMNode, TransformNode, ForEachNode, RouterNode], Field(discriminator="type")]


# --------------------------------------------------------------------------
# Workflow
# --------------------------------------------------------------------------
class Workflow(_Base):
    id: str
    version: str = "0.1.0"
    name: str = ""
    description: str = ""
    inputs: dict[str, InputParam] = Field(default_factory=dict)
    budgets: Budgets = Field(default_factory=Budgets)
    defaults: dict[str, Any] = Field(default_factory=dict, description="Defaults for llm nodes: provider, model.")
    nodes: list[Node]
    edges: Optional[list[tuple[str, str]]] = Field(
        None, description="Explicit edges. When omitted, nodes run in listed order."
    )
    start: Optional[str] = None
    output: Any = None

    # Not part of the JSON document; set by load_workflow.
    base_dir: Optional[Path] = Field(None, exclude=True)
    source_hash: Optional[str] = Field(None, exclude=True)

    @field_validator("nodes")
    @classmethod
    def _unique_ids(cls, nodes: list[Any]) -> list[Any]:
        seen: set[str] = set()
        for n in nodes:
            if not n.id or not _ID_RE.match(n.id):
                raise ValueError(f"node id {n.id!r} must match {_ID_RE.pattern}")
            if n.id == END:
                raise ValueError("'END' is reserved")
            if n.id in seen:
                raise ValueError(f"duplicate node id {n.id!r}")
            seen.add(n.id)
        if not nodes:
            raise ValueError("workflow needs at least one node")
        return nodes

    @model_validator(mode="after")
    def _check_graph(self) -> "Workflow":
        ids = {n.id for n in self.nodes}
        targets = ids | {END}
        if self.start and self.start not in ids:
            raise ValueError(f"start node {self.start!r} does not exist")
        for a, b in self.edges or []:
            if a not in ids:
                raise ValueError(f"edge source {a!r} does not exist")
            if b not in targets:
                raise ValueError(f"edge target {b!r} does not exist")
        for n in self.nodes:
            if n.next is not None:
                if self.edges is not None:
                    raise ValueError(f"node {n.id!r}: use either 'next' on nodes or top-level 'edges', not both")
                if isinstance(n, RouterNode):
                    raise ValueError(f"router {n.id!r} uses 'routes'/'default', not 'next'")
                if n.next not in targets:
                    raise ValueError(f"node {n.id!r} next {n.next!r} does not exist")
            if isinstance(n, RouterNode):
                for r in n.routes:
                    if r.goto not in targets:
                        raise ValueError(f"router {n.id!r} routes to unknown node {r.goto!r}")
                if n.default not in targets:
                    raise ValueError(f"router {n.id!r} default {n.default!r} does not exist")
                if self.edges and any(a == n.id for a, _ in self.edges):
                    raise ValueError(f"router {n.id!r} must not have explicit outgoing edges")
        return self

    def node(self, node_id: str) -> Any:
        for n in self.nodes:
            if n.id == node_id:
                return n
        raise KeyError(node_id)

    def resolve_file(self, rel: str) -> Path:
        base = self.base_dir or Path.cwd()
        path = (base / rel).resolve()
        if not path.is_file():
            raise SpecError(f"file not found: {rel} (resolved to {path})")
        return path


def parse_workflow(data: dict[str, Any], base_dir: Optional[Path] = None) -> Workflow:
    try:
        wf = Workflow.model_validate(data)
    except ValidationError as e:
        raise SpecError(f"invalid workflow document:\n{e}") from e
    wf.base_dir = base_dir
    wf.source_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    return wf


def load_workflow(path: str | Path) -> Workflow:
    path = Path(path)
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise SpecError(f"cannot read workflow {path}: {e}") from e
    return parse_workflow(data, base_dir=path.parent.resolve())


def workflow_json_schema() -> dict[str, Any]:
    """JSON Schema of the document format, for editors and external validation."""
    return Workflow.model_json_schema(by_alias=True)
