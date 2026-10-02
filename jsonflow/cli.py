"""Command line: python -m jsonflow <command>

  validate  <workflow.json>            static checks (tools resolved against live servers unless --offline)
  run       <workflow.json> [-i k=v]   run and write runs/<run_id>/
  tools     [--server s] [--category c] node palette from live MCP discovery
  graph     <workflow.json>            Mermaid diagram of the compiled graph
  schema                               JSON Schema of the workflow document format
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonflow.errors import JsonFlowError

DEFAULT_SERVERS = "config/jsonflow/servers.json"


def _parse_inputs(pairs: list[str], inputs_json: str | None) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(Path(inputs_json).read_text()) if inputs_json else {}
    for pair in pairs:
        key, sep, raw = pair.partition("=")
        if not sep:
            raise SystemExit(f"--input expects key=value, got {pair!r}")
        try:
            out[key] = json.loads(raw)
        except json.JSONDecodeError:
            out[key] = raw
    return out


def _registry(args: argparse.Namespace):
    from jsonflow.mcp.fixture import FixtureClient
    from jsonflow.mcp.registry import ServerRegistry

    config = json.loads(Path(args.servers).read_text())
    clients = {}
    for spec in args.mock_mcp or []:
        server, sep, path = spec.partition("=")
        if not sep:
            raise SystemExit("--mock-mcp expects server=fixture.json")
        clients[server] = FixtureClient(server, path)
    return ServerRegistry(config, clients=clients)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="jsonflow", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--servers", default=DEFAULT_SERVERS, help="MCP server registry JSON")
        p.add_argument("--mock-mcp", action="append", metavar="SERVER=FIXTURE", help="replace a server with a fixture file")

    p = sub.add_parser("validate"); p.add_argument("workflow"); common(p)
    p.add_argument("--offline", action="store_true", help="skip tool checks against servers")

    p = sub.add_parser("run"); p.add_argument("workflow"); common(p)
    p.add_argument("-i", "--input", action="append", default=[], metavar="KEY=VALUE", help="value is parsed as JSON when possible")
    p.add_argument("--inputs-json", help="file with an inputs object")
    p.add_argument("--mock-llm", metavar="FIXTURE", help="use scripted LLM responses instead of a live model")
    p.add_argument("--run-dir", default="runs")
    p.add_argument("--run-id", help="fixed run id (default: timestamp + random suffix)")
    p.add_argument("--quiet", action="store_true", help="print only the output JSON")

    p = sub.add_parser("tools"); common(p)
    p.add_argument("--server", action="append"); p.add_argument("--category")
    p.add_argument("--refresh", action="store_true"); p.add_argument("--json", action="store_true")

    p = sub.add_parser("graph"); p.add_argument("workflow")
    sub.add_parser("schema")

    args = ap.parse_args(argv)
    try:
        return _dispatch(args)
    except JsonFlowError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace) -> int:
    from jsonflow.spec import load_workflow, workflow_json_schema

    if args.cmd == "schema":
        print(json.dumps(workflow_json_schema(), indent=2))
        return 0

    if args.cmd == "graph":
        from jsonflow.engine import successors

        wf = load_workflow(args.workflow)
        lines = ["flowchart TD", "  START([start])", "  END_([end])"]
        for n in wf.nodes:
            label = f"{n.id}<br/><small>{n.type}" + (f": {n.tool}" if n.type == "tool" else "")
            if n.type == "for_each":
                label += f" → {n.body.type}" + (f": {n.body.tool}" if n.body.type == "tool" else "")
            label += "</small>"
            shape = ("{", "}") if n.type == "router" else ("[", "]")
            lines.append(f'  {n.id}{shape[0]}"{label}"{shape[1]}')
        lines.append(f"  START --> {wf.start or wf.nodes[0].id}")
        for src, targets in successors(wf).items():
            for t in targets:
                lines.append(f"  {src} --> {'END_' if t == 'END' else t}")
        print("\n".join(lines))
        return 0

    registry = _registry(args)

    if args.cmd == "tools":
        palette = registry.palette(args.server, refresh=args.refresh)
        if args.category:
            palette["categories"] = {args.category: palette["categories"].get(args.category, [])}
        if args.json:
            print(json.dumps(palette, indent=2))
        else:
            for cat, tools in palette["categories"].items():
                print(f"\n[{cat}] {len(tools)} tools")
                for t in tools:
                    req = ", ".join(t["required"])
                    print(f"  {t['server']}.{t['tool']}({req})  {t['description'][:90]}")
            for server, err in palette["errors"].items():
                print(f"\n! {server}: {err}", file=sys.stderr)
        return 0

    from jsonflow.validate import validate_workflow

    wf = load_workflow(args.workflow)
    if args.cmd == "validate":
        report = validate_workflow(wf, None if args.offline else registry)
        for w in report.warnings:
            print(f"warning: {w}")
        for e in report.errors:
            print(f"error: {e}")
        print("valid" if report.ok else "invalid")
        return 0 if report.ok else 1

    if args.cmd == "run":
        from jsonflow.llm.scripted import ScriptedProvider
        from jsonflow.runner import run_workflow

        providers = None
        if args.mock_llm:
            scripted = ScriptedProvider(args.mock_llm)
            providers = {"anthropic": scripted, "facade": scripted, "scripted": scripted}
        result = run_workflow(wf, _parse_inputs(args.input, args.inputs_json), registry=registry,
                              llm_providers=providers, run_dir=args.run_dir, run_id=args.run_id)
        if not args.quiet:
            print(f"run {result.run_id}: {result.status}", file=sys.stderr)
            print(f"tool calls {result.stats['tool_calls']}/{result.stats['budgets']['tool']}, "
                  f"llm calls {result.stats['llm_calls']}/{result.stats['budgets']['llm']}, "
                  f"{result.stats['duration_ms']} ms", file=sys.stderr)
            if result.run_dir:
                print(f"audit trail: {result.run_dir}", file=sys.stderr)
            if result.error:
                print(f"error: {result.error}", file=sys.stderr)
        print(json.dumps(result.output, indent=2, ensure_ascii=False, default=str))
        return 0 if result.status == "succeeded" else 1
    return 1
