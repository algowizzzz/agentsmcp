"""jsonflow: run LangGraph workflows defined entirely in JSON.

A workflow is a JSON document of nodes. Each node is an LLM call, an MCP tool
call, a deterministic transform, a for-each loop or a router. The engine
validates the document, compiles it to a LangGraph StateGraph, enforces
budgets, and writes a full audit trail for every run.

The same JSON is the save format a drag-and-drop editor will produce later.
"""
from jsonflow.spec import Workflow, load_workflow
from jsonflow.runner import RunResult, run_workflow

__all__ = ["Workflow", "load_workflow", "run_workflow", "RunResult"]
