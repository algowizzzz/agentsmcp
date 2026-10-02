"""End to end: the USA + Hedge Funds sector events workflow on synthetic fixtures."""
import json
import subprocess
import sys

from jsonflow.llm.scripted import ScriptedProvider
from jsonflow.mcp.fixture import FixtureClient
from jsonflow.mcp.registry import ServerRegistry
from jsonflow.runner import run_workflow
from jsonflow.validate import validate_workflow
from jsonflow.spec import load_workflow

from .conftest import ROOT


def _run(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path, inputs=None):
    sajha = FixtureClient("sajha", sajha_fixture)
    llm = ScriptedProvider(llm_fixture)
    reg = ServerRegistry(servers_config, clients={"sajha": sajha})
    result = run_workflow(workflow_path, inputs, registry=reg, llm_providers={"anthropic": llm}, run_dir=tmp_path)
    return result, sajha, llm


def test_validates_against_catalog(workflow_path, servers_config, sajha_fixture):
    reg = ServerRegistry(servers_config, clients={"sajha": FixtureClient("sajha", sajha_fixture)})
    report = validate_workflow(load_workflow(workflow_path), reg)
    assert report.ok, report.errors
    assert report.warnings == []


def test_full_run(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path):
    result, sajha, llm = _run(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path)
    assert result.status == "succeeded", result.error
    out = result.output

    # Discovery: 4 queries, one fails and the run carries on.
    news_calls = [c for c in sajha.calls if c["tool"] == "tavily_news_search"]
    assert len(news_calls) == 4
    assert result.nodes["discover_news"].count(None) == 1

    # Dedupe: 8 raw articles, one duplicate URL (www/utm variant), one duplicate title.
    articles = result.nodes["collect_articles"]
    assert out["articles_considered"] == 6 == len(articles)
    assert [a["ref"] for a in articles] == [1, 2, 3, 4, 5, 6]
    assert [a["score"] for a in articles] == sorted([a["score"] for a in articles], reverse=True)
    assert all(set(a) == {"ref", "title", "url", "publisher", "published_date", "score", "excerpt"} for a in articles)

    # Ranking: low materiality dropped; high first, then medium by confidence.
    events = out["events"]
    assert [(e["event_id"], e["materiality"], e["confidence"]) for e in events] == [
        ("E1", "high", 0.9), ("E2", "medium", 0.85), ("E3", "medium", 0.7)]
    assert [s["url"] for s in events[0]["sources"]] == [articles[0]["url"], articles[2]["url"], articles[3]["url"]]

    # Validation: one trusted-domain search per event, domains passed through.
    domain_calls = [c for c in sajha.calls if c["tool"] == "tavily_domain_search"]
    assert len(domain_calls) == 3
    assert all(c["arguments"]["include_domains"][0] == "reuters.com" for c in domain_calls)
    assert [e["validation"]["validation_status"] for e in events] == ["corroborated", "corroborated", "not_found"]
    assert all("review_status" not in e for e in events)

    # Budgets and LLM calls.
    assert result.stats["tool_calls"] == 7 and result.stats["llm_calls"] == 2
    assert [r.node_id for r in llm.requests] == ["extract_events", "assess_validation"]
    assert "Sector: Hedge Funds" in llm.requests[0].prompt and "ref" in llm.requests[0].prompt
    digest = result.nodes["validation_digest"]
    assert digest[2]["validation_results"] == [] and digest[2]["validation_error"] is None


def test_audit_trail_written(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path):
    result, _, _ = _run(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path)
    run = tmp_path / result.run_id
    for rel in ["workflow.json", "inputs.json", "result.json", "trace.jsonl",
                "nodes/extract_events.json", "calls/extract_events.llm1.json",
                "calls/discover_news.0.tool.json", "files/prompts/extract_events.md"]:
        assert (run / rel).is_file(), rel
    snapshot = json.loads((run / "workflow.json").read_text())
    assert len(snapshot["source_hash"]) == 64
    events = [json.loads(line) for line in (run / "trace.jsonl").read_text().splitlines()]
    assert events[0]["event"] == "run_start" and events[-1]["event"] == "run_end"
    failed = [e for e in events if e["event"] == "tool_call" and e["status"] == "error"]
    assert len(failed) == 1 and "rate limit" in failed[0]["error"]


def test_no_news_branch(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path):
    empty = {"query": "x", "results_count": 0, "results": []}
    sajha_fixture["responses"]["tavily_news_search"] = [{"result": empty}]
    result, sajha, llm = _run(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path)
    assert result.status == "succeeded"
    assert result.output["events"] == [] and "No news" in result.output["note"]
    assert llm.requests == [] and all(c["tool"] == "tavily_news_search" for c in sajha.calls)


def test_no_material_events_skips_validation(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path):
    for e in llm_fixture["extract_events"]["events"]:
        e["materiality"] = "low"
    result, sajha, llm = _run(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path)
    assert result.status == "succeeded" and result.output["events"] == []
    assert not [c for c in sajha.calls if c["tool"] == "tavily_domain_search"]
    assert [r.node_id for r in llm.requests] == ["extract_events"]


def test_inputs_change_behaviour(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path):
    result, sajha, _ = _run(workflow_path, servers_config, sajha_fixture, llm_fixture, tmp_path,
                            inputs={"max_events": 2, "max_validations": 1, "max_articles": 4})
    assert result.output["articles_considered"] == 4
    assert len(result.output["events"]) == 2
    assert len([c for c in sajha.calls if c["tool"] == "tavily_domain_search"]) == 1
    assert all("USA Hedge Funds" in c["arguments"]["query"] for c in sajha.calls if c["tool"] == "tavily_news_search")


def test_cli_offline_run(workflow_path, tmp_path):
    cfg = ROOT / "config" / "jsonflow"
    proc = subprocess.run(
        [sys.executable, "-m", "jsonflow", "run", str(workflow_path),
         "--servers", str(cfg / "servers.json"),
         "--mock-mcp", f"sajha={cfg / 'fixtures' / 'sajha_sector_events.json'}",
         "--mock-llm", str(cfg / "fixtures" / "llm_sector_events.json"),
         "--run-dir", str(tmp_path), "--quiet", "-i", "max_events=2"],
        cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert len(json.loads(proc.stdout)["events"]) == 2
