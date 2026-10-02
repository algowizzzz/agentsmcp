"""Business logic behind the web app and the MCP endpoint."""
from __future__ import annotations

import copy
import json
import os
import re
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jsonflow.errors import JsonFlowError, SpecError
from jsonflow.llm.base import LLMProvider, LLMRequest, build_provider
from jsonflow.mcp.base import MCPClient
from jsonflow.mcp.registry import CATEGORIES, ServerRegistry
from jsonflow.runner import resolve_inputs, run_workflow
from jsonflow.server import security
from jsonflow.server.agents_client import AGENTS_SERVER, AgentsClient
from jsonflow.server.db import Database, now
from jsonflow.spec import parse_workflow
from jsonflow.transforms import TRANSFORM_OPS
from jsonflow.expressions import CONDITION_OPS
from jsonflow.validate import validate_workflow

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SERVERS_FILE = REPO_ROOT / "config" / "jsonflow" / "servers.json"
EXAMPLE_WORKFLOW = REPO_ROOT / "config" / "jsonflow" / "workflows" / "sector_events.json"
DEFAULT_CATEGORIES = [
    ("Credit Risk", "Counterparty and sector credit intelligence"),
    ("Market Risk", "Market moves, liquidity and funding"),
    ("Regulatory", "Rules, filings and supervisory developments"),
    ("Research", "General research and enrichment"),
]
DEFAULT_LLM = {"provider": "anthropic", "model": "claude-opus-5-5", "base_url": "",
               "api_key_env": "ANTHROPIC_API_KEY", "structured": "tools", "timeout": 120}
DEFAULT_LIMITS = {"max_parallel_runs": 4}
_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,62}$")
_NODE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CALL_RE = re.compile(r"^[A-Za-z0-9_.\-]+\.json$")


class ServiceError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not s or not s[0].isalpha():
        s = "agent_" + s
    return s[:62]


def blank_definition(agent_id: str, name: str, category: str, description: str) -> dict[str, Any]:
    return {
        "id": agent_id, "version": "1", "name": name, "category": category, "description": description,
        "inputs": {}, "budgets": {"max_tool_calls": 20, "max_llm_calls": 10, "max_steps": 50},
        "nodes": [{"id": "start", "type": "transform", "input": "{{ inputs }}", "steps": [],
                   "description": "Starting point. Replace or connect nodes after it.", "ui": {"x": 80, "y": 120}}],
        "edges": [], "output": None,
    }


def inline_prompt_files(definition: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Stored agents keep prompts inline; convert prompt_file/system_file references."""
    d = copy.deepcopy(definition)
    for n in d.get("nodes", []):
        for node in (n, n.get("body") or {}):
            for key, inline in (("prompt_file", "prompt"), ("system_file", "system")):
                if node.get(key):
                    node[inline] = (base_dir / node.pop(key)).read_text()
    return d


class Service:
    def __init__(
        self,
        db: Database,
        data_dir: Path,
        client_overrides: Optional[dict[str, MCPClient]] = None,
        llm_overrides: Optional[dict[str, LLMProvider]] = None,
    ) -> None:
        self.db = db
        self.data_dir = Path(data_dir)
        self.runs_dir = self.data_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.client_overrides = dict(client_overrides or {})
        self.llm_overrides = dict(llm_overrides or {})
        self._registry: Optional[ServerRegistry] = None
        self._registry_lock = threading.Lock()
        limits = self.limits()
        self._pool = ThreadPoolExecutor(max_workers=int(limits["max_parallel_runs"]), thread_name_prefix="run")
        self._futures: dict[str, Future] = {}

    # ================================================================ setup
    def bootstrap(self, seed_examples: bool = True) -> None:
        if not self.db.one("SELECT name FROM categories LIMIT 1"):
            for name, desc in DEFAULT_CATEGORIES:
                self.db.run("INSERT INTO categories (name, description, created_at) VALUES (?, ?, ?)", (name, desc, now()))
        if self.db.get_setting("servers") is None:
            servers = json.loads(DEFAULT_SERVERS_FILE.read_text()) if DEFAULT_SERVERS_FILE.exists() else {"servers": {}}
            self.db.set_setting("servers", servers, "system")
        if self.db.get_setting("llm") is None:
            self.db.set_setting("llm", DEFAULT_LLM, "system")
        if self.db.get_setting("limits") is None:
            self.db.set_setting("limits", DEFAULT_LIMITS, "system")
        if seed_examples and EXAMPLE_WORKFLOW.exists() and not self.db.one("SELECT id FROM agents LIMIT 1"):
            d = inline_prompt_files(json.loads(EXAMPLE_WORKFLOW.read_text()), EXAMPLE_WORKFLOW.parent)
            d["category"] = "Credit Risk"
            d["name"] = "Sector event discovery"
            self._insert_agent(d, "system", published=True)
        # Runs that were in flight when the server stopped will never finish.
        self.db.run("UPDATE runs SET status = 'failed', error = 'interrupted by server restart', finished_at = ? "
                    "WHERE status IN ('queued', 'running')", (now(),))

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    # ================================================================ users
    def list_users(self) -> list[dict[str, Any]]:
        return self.db.all("SELECT id, username, display_name, role, active, created_at, last_login_at FROM users ORDER BY username")

    def create_user(self, username: str, password: str, role: str, display_name: str, actor: str) -> int:
        username = username.strip().lower()
        if not re.match(r"^[a-z0-9._-]{3,40}$", username):
            raise ServiceError("Username must be 3 to 40 characters: letters, digits, dot, dash or underscore.")
        if role not in security.ROLES:
            raise ServiceError("Role must be admin or super_admin.")
        problem = security.check_password_strength(password)
        if problem:
            raise ServiceError(problem)
        if self.db.one("SELECT id FROM users WHERE username = ?", (username,)):
            raise ServiceError("That username is taken.", 409)
        uid = self.db.run("INSERT INTO users (username, display_name, role, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                          (username, display_name.strip() or username, role, security.hash_password(password), now()))
        self.db.audit(actor, "user.create", username, {"role": role})
        return uid

    def _active_super_admins(self) -> int:
        return self.db.one("SELECT COUNT(*) AS n FROM users WHERE role = 'super_admin' AND active = 1")["n"]

    def update_user(self, user_id: int, changes: dict[str, Any], actor: dict[str, Any]) -> None:
        user = self.db.one("SELECT * FROM users WHERE id = ?", (user_id,))
        if not user:
            raise ServiceError("User not found.", 404)
        role = changes.get("role", user["role"])
        active = int(changes.get("active", user["active"]))
        if role not in security.ROLES:
            raise ServiceError("Role must be admin or super_admin.")
        if user["id"] == actor["id"] and (role != user["role"] or not active):
            raise ServiceError("You cannot change your own role or disable yourself.")
        losing_super = user["role"] == "super_admin" and user["active"] and (role != "super_admin" or not active)
        if losing_super and self._active_super_admins() <= 1:
            raise ServiceError("At least one active super admin must remain.")
        display = changes.get("display_name", user["display_name"]).strip() or user["username"]
        self.db.run("UPDATE users SET role = ?, active = ?, display_name = ? WHERE id = ?", (role, active, display, user_id))
        if not active or role != user["role"]:
            security.end_user_sessions(self.db, user_id)
        self.db.audit(actor["username"], "user.update", user["username"], {"role": role, "active": bool(active)})

    def set_password(self, user_id: int, password: str, actor: str) -> None:
        problem = security.check_password_strength(password)
        if problem:
            raise ServiceError(problem)
        user = self.db.one("SELECT username FROM users WHERE id = ?", (user_id,))
        if not user:
            raise ServiceError("User not found.", 404)
        self.db.run("UPDATE users SET password_hash = ? WHERE id = ?", (security.hash_password(password), user_id))
        security.end_user_sessions(self.db, user_id)
        self.db.audit(actor, "user.password", user["username"])

    # =========================================================== categories
    def list_categories(self) -> list[dict[str, Any]]:
        return self.db.all("SELECT c.name, c.description, COUNT(a.id) AS agents FROM categories c "
                           "LEFT JOIN agents a ON a.category = c.name GROUP BY c.name ORDER BY c.name")

    def create_category(self, name: str, description: str, actor: str) -> None:
        name = name.strip()
        if not 2 <= len(name) <= 60:
            raise ServiceError("Category name must be 2 to 60 characters.")
        if self.db.one("SELECT name FROM categories WHERE name = ?", (name,)):
            raise ServiceError("That category exists.", 409)
        self.db.run("INSERT INTO categories (name, description, created_at) VALUES (?, ?, ?)", (name, description.strip(), now()))
        self.db.audit(actor, "category.create", name)

    def delete_category(self, name: str, actor: str) -> None:
        used = self.db.one("SELECT COUNT(*) AS n FROM agents WHERE category = ?", (name,))["n"]
        if used:
            raise ServiceError(f"{used} agent(s) still use this category. Move them first.")
        self.db.run("DELETE FROM categories WHERE name = ?", (name,))
        self.db.audit(actor, "category.delete", name)

    # =============================================================== agents
    def _agent_row(self, agent_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM agents WHERE id = ?", (agent_id,))
        if not row:
            raise ServiceError("Agent not found.", 404)
        row["definition"] = json.loads(row["definition"])
        row["published"] = bool(row["published"])
        return row

    def list_agents(self) -> list[dict[str, Any]]:
        rows = self.db.all(
            "SELECT a.id, a.name, a.category, a.description, a.published, a.version, a.updated_by, a.updated_at, "
            "(SELECT status FROM runs r WHERE r.agent_id = a.id ORDER BY created_at DESC LIMIT 1) AS last_status, "
            "(SELECT created_at FROM runs r WHERE r.agent_id = a.id ORDER BY created_at DESC LIMIT 1) AS last_run_at, "
            "(SELECT COUNT(*) FROM runs r WHERE r.agent_id = a.id) AS run_count "
            "FROM agents a ORDER BY a.category, a.name")
        for r in rows:
            r["published"] = bool(r["published"])
        return rows

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        row = self._agent_row(agent_id)
        row["validation"] = self.validate_definition(row["definition"])
        return row

    def published_agents(self) -> list[dict[str, Any]]:
        rows = self.db.all("SELECT * FROM agents WHERE published = 1 ORDER BY category, name")
        for r in rows:
            r["definition"] = json.loads(r["definition"])
        return rows

    def _check_category(self, category: str) -> None:
        if not self.db.one("SELECT name FROM categories WHERE name = ?", (category,)):
            raise ServiceError(f"Unknown category {category!r}. A super admin can add it.")

    def _insert_agent(self, definition: dict[str, Any], actor: str, published: bool = False) -> str:
        agent_id = definition["id"]
        if not _ID_RE.match(agent_id):
            raise ServiceError("Agent id must start with a letter and use lowercase letters, digits and underscores.")
        if self.db.one("SELECT id FROM agents WHERE id = ?", (agent_id,)):
            raise ServiceError(f"An agent with id {agent_id!r} exists.", 409)
        self._check_category(definition.get("category", ""))
        text = json.dumps(definition)
        t = now()
        self.db.run("INSERT INTO agents (id, name, category, description, published, version, definition, created_by, "
                    "updated_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)",
                    (agent_id, definition.get("name") or agent_id, definition["category"], definition.get("description", ""),
                     int(published), text, actor, actor, t, t))
        self.db.run("INSERT INTO agent_versions (agent_id, version, definition, saved_by, saved_at) VALUES (?, 1, ?, ?, ?)",
                    (agent_id, text, actor, t))
        self.db.audit(actor, "agent.create", agent_id, {"category": definition["category"]})
        return agent_id

    def create_agent(self, name: str, category: str, description: str, actor: str,
                     definition: Optional[dict[str, Any]] = None) -> str:
        name = name.strip()
        if not name:
            raise ServiceError("Give the agent a name.")
        agent_id = slugify(name)
        base = agent_id
        i = 2
        while self.db.one("SELECT id FROM agents WHERE id = ?", (agent_id,)):
            agent_id = f"{base}_{i}"
            i += 1
        d = copy.deepcopy(definition) if definition else blank_definition(agent_id, name, category, description)
        d.update({"id": agent_id, "name": name, "category": category, "description": description or d.get("description", "")})
        return self._insert_agent(d, actor)

    def save_agent(self, agent_id: str, definition: dict[str, Any], actor: str, expected_version: Optional[int] = None) -> dict[str, Any]:
        row = self._agent_row(agent_id)
        if expected_version is not None and expected_version != row["version"]:
            raise ServiceError(f"Someone saved version {row['version']} after you opened version {expected_version}. "
                               "Reload to see their changes.", 409)
        if not isinstance(definition, dict) or not isinstance(definition.get("nodes"), list):
            raise ServiceError("Definition must be an object with a nodes list.")
        definition = dict(definition)
        definition["id"] = agent_id  # the id is the MCP tool name; it never changes
        category = definition.get("category") or row["category"]
        self._check_category(category)
        definition["category"] = category
        version = row["version"] + 1
        text = json.dumps(definition)
        t = now()
        self.db.run("UPDATE agents SET name = ?, category = ?, description = ?, version = ?, definition = ?, "
                    "updated_by = ?, updated_at = ? WHERE id = ?",
                    (definition.get("name") or agent_id, category, definition.get("description", ""), version, text,
                     actor, t, agent_id))
        self.db.run("INSERT INTO agent_versions (agent_id, version, definition, saved_by, saved_at) VALUES (?, ?, ?, ?, ?)",
                    (agent_id, version, text, actor, t))
        self.db.audit(actor, "agent.save", agent_id, {"version": version})
        report = self.validate_definition(definition)
        if row["published"] and not report["ok"]:
            self.db.run("UPDATE agents SET published = 0 WHERE id = ?", (agent_id,))
            self.db.audit(actor, "agent.unpublish", agent_id, "saved with validation errors")
            report["unpublished"] = True
        return {"version": version, "validation": report}

    def set_published(self, agent_id: str, published: bool, actor: str) -> None:
        row = self._agent_row(agent_id)
        if published:
            report = self.validate_definition(row["definition"])
            if not report["ok"]:
                raise ServiceError("Fix validation errors before publishing:\n" + "\n".join(report["errors"]))
        self.db.run("UPDATE agents SET published = ? WHERE id = ?", (int(published), agent_id))
        self.db.audit(actor, "agent.publish" if published else "agent.unpublish", agent_id)

    def delete_agent(self, agent_id: str, actor: str) -> None:
        self._agent_row(agent_id)
        self.db.run("DELETE FROM agents WHERE id = ?", (agent_id,))
        self.db.audit(actor, "agent.delete", agent_id)

    def list_versions(self, agent_id: str) -> list[dict[str, Any]]:
        return self.db.all("SELECT version, saved_by, saved_at FROM agent_versions WHERE agent_id = ? ORDER BY version DESC", (agent_id,))

    def get_version(self, agent_id: str, version: int) -> dict[str, Any]:
        row = self.db.one("SELECT definition FROM agent_versions WHERE agent_id = ? AND version = ?", (agent_id, version))
        if not row:
            raise ServiceError("Version not found.", 404)
        return json.loads(row["definition"])

    # =========================================================== validation
    def validate_definition(self, definition: dict[str, Any]) -> dict[str, Any]:
        try:
            wf = parse_workflow(definition)
        except SpecError as e:
            return {"ok": False, "errors": _pydantic_lines(str(e)), "warnings": []}
        try:
            report = validate_workflow(wf, self.registry_for_run(chain=[definition.get("id", "")], triggered_by="validate"))
        except JsonFlowError as e:
            return {"ok": False, "errors": [str(e)], "warnings": []}
        return {"ok": report.ok, "errors": report.errors, "warnings": report.warnings}

    # =========================================================== registries
    def servers_config(self) -> dict[str, Any]:
        return self.db.get_setting("servers", {"servers": {}})

    def shared_registry(self) -> ServerRegistry:
        with self._registry_lock:
            if self._registry is None:
                cfg = copy.deepcopy(self.servers_config())
                self._registry = ServerRegistry(cfg, clients=self.client_overrides)
            return self._registry

    def reset_registry(self) -> None:
        with self._registry_lock:
            self._registry = None

    def registry_for_run(self, chain: list[str], triggered_by: str) -> ServerRegistry:
        shared = self.shared_registry()
        cfg = copy.deepcopy(shared.config)
        cfg.setdefault("servers", {})[AGENTS_SERVER] = {"allow_tools": ["*"], "default_category": "agents"}
        clients = {name: shared.client(name) for name in shared.server_names() if name in shared._clients}
        clients.update(self.client_overrides)
        clients[AGENTS_SERVER] = AgentsClient(self, chain, triggered_by)
        reg = ServerRegistry(cfg, clients=clients)
        reg._catalog.update({k: v for k, v in shared._catalog.items() if k != AGENTS_SERVER})
        return reg

    def palette(self, refresh: bool = False) -> dict[str, Any]:
        reg = self.registry_for_run(chain=[], triggered_by="palette")
        servers = [s for s in reg.server_names() if s in self.servers_config().get("servers", {}) or s in reg._clients]
        pal = reg.palette(servers, refresh=refresh)
        if not refresh:  # keep the shared cache warm for later runs
            shared = self.shared_registry()
            shared._catalog.update({k: v for k, v in reg._catalog.items() if k != AGENTS_SERVER})
        pal["logic"] = [
            {"type": "llm", "label": "LLM call", "description": "Prompt a model; optional JSON output schema"},
            {"type": "transform", "label": "Transform", "description": "Filter, dedupe, sort, map, join data"},
            {"type": "router", "label": "Router", "description": "Branch on a condition"},
        ]
        pal["transform_ops"] = TRANSFORM_OPS
        pal["condition_ops"] = CONDITION_OPS
        pal["category_order"] = list(CATEGORIES)
        return pal

    # =============================================================== runs
    def llm_settings(self) -> dict[str, Any]:
        return {**DEFAULT_LLM, **(self.db.get_setting("llm") or {})}

    def limits(self) -> dict[str, Any]:
        return {**DEFAULT_LIMITS, **(self.db.get_setting("limits") or {})}

    def _providers(self) -> tuple[dict[str, LLMProvider], dict[str, Any]]:
        s = self.llm_settings()
        providers: dict[str, LLMProvider] = {}
        if s["provider"] == "openai_compat" and s.get("base_url"):
            providers["openai_compat"] = build_provider(
                "openai_compat", base_url=s["base_url"], api_key=os.getenv(s.get("api_key_env") or "", ""),
                structured=s.get("structured") or "tools", timeout=float(s.get("timeout") or 120))
        providers.update(self.llm_overrides)
        return providers, {"provider": s["provider"], "model": s.get("model") or None}

    def start_run(self, agent_id: str, inputs: dict[str, Any], trigger: str, triggered_by: str,
                  chain: Optional[list[str]] = None) -> str:
        row = self._agent_row(agent_id)
        try:
            wf = parse_workflow(row["definition"])
            resolve_inputs(wf, inputs)
        except SpecError as e:
            raise ServiceError(str(e))
        run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}"
        self.db.run("INSERT INTO runs (id, agent_id, agent_version, status, trigger, triggered_by, inputs, created_at) "
                    "VALUES (?, ?, ?, 'queued', ?, ?, ?, ?)",
                    (run_id, agent_id, row["version"], trigger, triggered_by, json.dumps(inputs), now()))
        self._futures[run_id] = self._pool.submit(self._execute, run_id, row, inputs, chain or [agent_id], triggered_by)
        return run_id

    def _execute(self, run_id: str, row: dict[str, Any], inputs: dict[str, Any], chain: list[str], triggered_by: str) -> None:
        self.db.run("UPDATE runs SET status = 'running', run_dir = ? WHERE id = ?", (str(self.runs_dir / run_id), run_id))
        status, output, error, stats = "failed", None, None, {}
        try:
            wf = parse_workflow(row["definition"])
            providers, defaults = self._providers()
            result = run_workflow(wf, inputs, registry=self.registry_for_run(chain, triggered_by), llm_providers=providers,
                                  run_dir=self.runs_dir, run_id=run_id, llm_defaults=defaults)
            status, output, error, stats = result.status, result.output, result.error, result.stats
        except Exception as e:  # never leave a run stuck in 'running'
            error = f"{type(e).__name__}: {e}"
        self.db.run("UPDATE runs SET status = ?, output = ?, error = ?, stats = ?, finished_at = ? WHERE id = ?",
                    (status, json.dumps(output, default=str), error, json.dumps(stats, default=str), now(), run_id))
        self._futures.pop(run_id, None)

    def run_agent_sync(self, agent_id: str, inputs: dict[str, Any], trigger: str, triggered_by: str,
                       chain: Optional[list[str]] = None, timeout: Optional[float] = None) -> dict[str, Any]:
        """Run inline in the caller's thread (MCP calls and agent-to-agent calls)."""
        row = self._agent_row(agent_id)
        if not row["published"]:
            raise ServiceError(f"Agent {agent_id!r} is not published.", 404)
        try:
            resolve_inputs(parse_workflow(row["definition"]), inputs)
        except SpecError as e:
            raise ServiceError(str(e))
        run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}"
        self.db.run("INSERT INTO runs (id, agent_id, agent_version, status, trigger, triggered_by, inputs, created_at) "
                    "VALUES (?, ?, ?, 'queued', ?, ?, ?, ?)",
                    (run_id, agent_id, row["version"], trigger, triggered_by, json.dumps(inputs), now()))
        self._execute(run_id, row, inputs, chain or [agent_id], triggered_by)
        return self.get_run(run_id, include_trace=False)

    def get_run(self, run_id: str, include_trace: bool = True) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM runs WHERE id = ?", (run_id,))
        if not row:
            raise ServiceError("Run not found.", 404)
        for k in ("inputs", "output", "stats"):
            row[k] = json.loads(row[k]) if row.get(k) else None
        if include_trace:
            trace_file = self.runs_dir / run_id / "trace.jsonl"
            row["trace"] = [json.loads(line) for line in trace_file.read_text().splitlines()] if trace_file.exists() else []
            calls_dir = self.runs_dir / run_id / "calls"
            row["calls"] = sorted(p.name for p in calls_dir.glob("*.json")) if calls_dir.exists() else []
            v = self.db.one("SELECT definition FROM agent_versions WHERE agent_id = ? AND version = ?",
                            (row["agent_id"], row["agent_version"]))
            row["definition"] = json.loads(v["definition"]) if v else None
        row.pop("run_dir", None)
        return row

    def list_runs(self, agent_id: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
        sql = ("SELECT r.id, r.agent_id, a.name AS agent_name, a.category, r.agent_version, r.status, r.trigger, "
               "r.triggered_by, r.created_at, r.finished_at, r.error FROM runs r LEFT JOIN agents a ON a.id = r.agent_id")
        args: tuple = ()
        if agent_id:
            sql += " WHERE r.agent_id = ?"
            args = (agent_id,)
        sql += " ORDER BY r.created_at DESC LIMIT ?"
        return self.db.all(sql, args + (min(int(limit), 500),))

    def run_file(self, run_id: str, kind: str, name: str) -> Any:
        if not self.db.one("SELECT id FROM runs WHERE id = ?", (run_id,)):
            raise ServiceError("Run not found.", 404)
        if kind == "nodes":
            if not _NODE_RE.match(name):
                raise ServiceError("Bad node id.")
            path = self.runs_dir / run_id / "nodes" / f"{name}.json"
        elif kind == "calls":
            if not _CALL_RE.match(name):
                raise ServiceError("Bad call name.")
            path = self.runs_dir / run_id / "calls" / name
        else:
            raise ServiceError("Unknown file kind.", 404)
        if not path.is_file():
            raise ServiceError("Not available for this run.", 404)
        return json.loads(path.read_text())

    def wait(self, run_id: str, timeout: float = 60) -> None:
        fut = self._futures.get(run_id)
        if fut:
            fut.result(timeout=timeout)

    # ============================================================= settings
    def save_servers(self, config: dict[str, Any], actor: str) -> None:
        if not isinstance(config, dict) or not isinstance(config.get("servers"), dict):
            raise ServiceError("Config must be an object with a 'servers' object.")
        if AGENTS_SERVER in config["servers"]:
            raise ServiceError(f"'{AGENTS_SERVER}' is reserved for this product's own agents.")
        for name, cfg in config["servers"].items():
            if cfg.get("transport", "sajha_rest") not in ("sajha_rest", "mcp_http", "fixture"):
                raise ServiceError(f"server {name}: transport must be sajha_rest, mcp_http or fixture")
        try:
            ServerRegistry(config)
        except JsonFlowError as e:
            raise ServiceError(str(e))
        self.db.set_setting("servers", config, actor)
        self.db.audit(actor, "settings.servers", "", {"servers": sorted(config["servers"])})
        self.reset_registry()

    def test_server(self, name: str) -> dict[str, Any]:
        try:
            tools = self.shared_registry().tools(name, refresh=True, include_blocked=True)
        except JsonFlowError as e:
            return {"ok": False, "error": str(e)}
        allowed = self.shared_registry().tools(name)
        return {"ok": True, "tools": len(tools), "allowed": len(allowed)}

    def save_llm(self, settings: dict[str, Any], actor: str) -> None:
        s = {**DEFAULT_LLM, **{k: v for k, v in settings.items() if k in DEFAULT_LLM}}
        if s["provider"] not in ("anthropic", "openai_compat"):
            raise ServiceError("Provider must be anthropic or openai_compat.")
        if s["provider"] == "openai_compat" and not s.get("base_url"):
            raise ServiceError("An OpenAI-compatible provider needs a base URL.")
        if s["structured"] not in ("tools", "json_schema", "json"):
            raise ServiceError("Structured mode must be tools, json_schema or json.")
        if s.get("api_key_env") and not re.match(r"^[A-Z_][A-Z0-9_]*$", s["api_key_env"]):
            raise ServiceError("API key variable must be an environment variable name, not the key itself.")
        self.db.set_setting("llm", s, actor)
        self.db.audit(actor, "settings.llm", "", {k: s[k] for k in ("provider", "model", "base_url", "api_key_env")})

    def llm_status(self) -> dict[str, Any]:
        s = self.llm_settings()
        return {**s, "api_key_present": bool(os.getenv(s.get("api_key_env") or ""))}

    def test_llm(self) -> dict[str, Any]:
        providers, defaults = self._providers()
        name = defaults["provider"]
        try:
            provider = providers.get(name) or build_provider(name)
            from jsonflow.llm.base import default_model

            model = defaults.get("model") or default_model(name)
            resp = provider.complete(LLMRequest(node_id="settings_test", prompt="Reply with the single word: ready",
                                                model=model, max_tokens=20))
            return {"ok": True, "model": resp.model, "reply": (resp.text or "")[:80]}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"[:400]}

    # ============================================================= api keys
    def list_keys(self) -> list[dict[str, Any]]:
        rows = self.db.all("SELECT id, name, prefix, categories, created_by, created_at, last_used_at, revoked FROM api_keys ORDER BY id DESC")
        for r in rows:
            r["categories"] = json.loads(r["categories"])
            r["revoked"] = bool(r["revoked"])
        return rows

    def create_key(self, name: str, categories: list[str], actor: str) -> dict[str, Any]:
        if not name.strip():
            raise ServiceError("Name the key after the client that will use it.")
        for c in categories:
            self._check_category(c)
        key_id, secret = security.create_api_key(self.db, name.strip(), categories, actor)
        self.db.audit(actor, "apikey.create", name, {"categories": categories})
        return {"id": key_id, "key": secret}

    def revoke_key(self, key_id: int, actor: str) -> None:
        self.db.run("UPDATE api_keys SET revoked = 1 WHERE id = ?", (key_id,))
        self.db.audit(actor, "apikey.revoke", str(key_id))

    def audit_log(self, limit: int = 200) -> list[dict[str, Any]]:
        return self.db.all("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (min(int(limit), 1000),))


def _pydantic_lines(text: str) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("For further information")]
    return lines[1:] if len(lines) > 1 else lines
