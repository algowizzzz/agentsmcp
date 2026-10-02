# jsonflow — JSON-defined LangGraph workflows over MCP tools

Step 1 of the drag-and-drop workflow layer. A workflow is one JSON document. Each node is an LLM call, an MCP tool call, a deterministic transform, a for-each loop or a router. The engine validates the document, compiles it to a LangGraph `StateGraph`, enforces budgets and allowlists, and writes a full audit trail per run.

There is no canvas yet. The JSON format is the canvas's save format, so the editor can be built on top later without changing the engine.

The first workflow is Phase 1 of the sector intelligence handover (`docs/SECTOR_INTELLIGENCE_HANDOVER.md`): USA + Hedge Funds news discovery, event extraction, deduplication, ranking and trusted-domain validation.

## Quick start

```bash
pip install -r jsonflow/requirements.txt

# Offline: synthetic fixtures for SAJHA and the LLM
python -m jsonflow run config/jsonflow/workflows/sector_events.json \
  --mock-mcp sajha=config/jsonflow/fixtures/sajha_sector_events.json \
  --mock-llm config/jsonflow/fixtures/llm_sector_events.json

# Live: real SAJHA server plus any LLM (see "LLM providers")
export SAJHA_BASE_URL=http://localhost:3002 SAJHA_API_KEY=...
export ANTHROPIC_API_KEY=...            # or the OPENAI_COMPAT_* variables below
python -m jsonflow run config/jsonflow/workflows/sector_events.json -i country=USA -i sector="Hedge Funds"

python -m jsonflow tools                      # node palette from live MCP discovery, grouped by category
python -m jsonflow validate <workflow.json>   # static checks, tools resolved against live servers
python -m jsonflow graph <workflow.json>      # Mermaid diagram
python -m jsonflow schema                     # JSON Schema of the document format

python -m pytest tests/jsonflow_tests -q
```

Every run writes `runs/<run_id>/`: the exact workflow and its hash, inputs, copies of prompt files, one JSON file per node output, one file per tool and LLM call (rendered prompt, arguments, raw result), `trace.jsonl` and `result.json`. Secrets in arguments are redacted.

## The product: web app and MCP endpoint

`python -m jsonflow.server` runs jsonflow as a product: a public explainer home page and guide, sign-in, an agents dashboard, the drag-and-drop builder, run history and a super admin page. Published agents are served as MCP tools.

```bash
pip install -r jsonflow/requirements.txt
python -m jsonflow.server create-user --username you --role super_admin   # prompts for a password
python -m jsonflow.server serve --host 0.0.0.0 --port 8080                 # add --demo for offline fixtures
```

| Page | Path | Who |
|---|---|---|
| Explainer home page | `/` | everyone |
| Guide | `/guide` | everyone |
| Agents dashboard | `/app` | admin, super admin |
| Builder | `/app/agents/<id>` | admin, super admin |
| Run view | `/app/runs/<id>` | admin, super admin |
| Admin: users, categories, MCP servers, model, API keys, audit log | `/app/admin` | super admin |

**Roles.** Only two. Admins build, edit, validate, run and publish agents and see every run. Super admins also delete agents and manage users, categories, MCP servers, the default model, API keys and the audit log. There is no self sign-up, and at least one active super admin always remains.

**Agents.** Each agent belongs to one category. Every save is a new version, and every run records the version it used. Saving never fails on validation problems, but publishing and running require a valid agent, and a published agent saved with errors is unpublished.

**Agents as MCP tools.** Published agents are tools on `POST /mcp`, and each category has its own endpoint, `POST /mcp/category/<slug>`. The tool name is the agent id, the arguments are its inputs, the description starts with the category, and the result is the agent's output. Clients authenticate with `Authorization: Bearer <key>`; super admins create keys and can limit them to categories. Every call is a recorded run with trigger `mcp`.

**Agents calling agents.** Published agents also appear in the builder palette under "agents" as an in-process server, so one agent can use another as a step. Self-calls and loops are refused and chains stop at three levels.

**Storage.** One SQLite file plus run folders under `--data-dir` (default `jsonflow_data/`). Passwords are hashed with scrypt; sessions and API keys are stored only as hashes. Model and server keys are referenced by environment variable name, never stored.

**Security controls.** Session cookies are HttpOnly and SameSite=Lax, and Secure over HTTPS. State-changing API calls need a custom request header, which blocks cross-site form posts. Pages send a strict Content-Security-Policy with no inline scripts. Sign-in locks for five minutes after five failures. Run artifact paths are validated against traversal.

## Layout

| Path | Purpose |
|---|---|
| `jsonflow/spec.py` | Pydantic models of the document format |
| `jsonflow/expressions.py` | `{{ }}` templates and JSON conditions |
| `jsonflow/transforms.py` | Deterministic transform ops |
| `jsonflow/engine.py` | Node executors, budgets, audit, LangGraph compiler |
| `jsonflow/validate.py` | Static checks before a run |
| `jsonflow/runner.py` | `run_workflow()` |
| `jsonflow/mcp/` | SAJHA REST client, standard MCP Streamable HTTP client, fixture client, server registry |
| `jsonflow/llm/` | Anthropic provider, OpenAI-compatible provider, scripted provider, adapter to the repo's `LLMFacade` |
| `config/jsonflow/servers.json` | MCP server registry, allowlists, category rules |
| `config/jsonflow/workflows/` | Workflows and their prompt files |
| `config/jsonflow/fixtures/` | Synthetic SAJHA and LLM responses for offline runs |
| `jsonflow/server/` | Web product: FastAPI app, services, SQLite storage, MCP endpoint, pages and static assets |

## Document format

```json
{
  "id": "sector_events", "version": "1.0.0",
  "inputs":  {"country": {"type": "string", "default": "USA"}},
  "budgets": {"max_tool_calls": 10, "max_llm_calls": 4, "max_steps": 30},
  "defaults": {"provider": "openai_compat", "model": "my-model"},
  "nodes": [ ... ],
  "edges": [["a", "b"]],
  "output": {"events": "{{ nodes.assemble_report | default([]) }}"}
}
```

Without `edges`, nodes run in listed order. A node's `next` overrides its successor, and `"END"` stops. Routers choose their successor from `routes`. Every node accepts `description`, `on_error` (`fail` or `continue`), `join` (see below) and `ui`, which holds canvas metadata the engine ignores.

### Parallel execution

- **Inside a loop:** a `for_each` with `concurrency: N` runs up to N items at once. Tool and LLM bodies both work. Budgets are shared and thread-safe.
- **Across branches:** with `edges`, one node can lead to several. Those branches run at the same time.
- **Where branches meet:** set `"join": "all"` on the meeting node so it waits for every branch and runs once. The default `"any"` runs it each time a branch arrives, which suits branches a router chose between. Validation warns when several branches meet at a node left on `"any"`, and rejects `"all"` on a router target, because a skipped route would block it forever.

### Node types

| Type | What it does | Key fields |
|---|---|---|
| `tool` | Calls one tool on one registered MCP server. Arguments are validated against the tool's live input schema before the call. | `server`, `tool`, `args`, `select`, `timeout`, `retries` |
| `llm` | One model call. With `output_schema` the answer is forced into that JSON shape and validated, with one repair retry. | `prompt` or `prompt_file`, `system` or `system_file`, `output_schema`, `model`, `provider`, `temperature`, `max_tokens` |
| `transform` | Deterministic data shaping. No model and no tool. | `input`, `steps` |
| `for_each` | Runs a `tool`, `llm` or `transform` body once per item. | `items`, `as`, `max_items`, `concurrency`, `include_item`, `on_item_error`, `body` |
| `router` | Picks the next node from ordered conditions. | `routes: [{when, goto}]`, `default` |

### Templates

Any string may contain `{{ expr }}`. A string that is exactly one expression returns the raw value, such as a list. Mixed text renders non-strings as JSON.

Roots are `inputs`, `nodes.<id>` (a node's output), `run` (`id`, `date`, `started_at`, workflow id and version), and inside loops and transform steps `item`, `index` and the loop alias.

Filters: `default(x)`, `length`, `join(', ')`, `pluck('field')`, `first`, `last`, `upper`, `lower`, `truncate(n)`, `domain`, `json`, `pretty`, `keys`.

### Conditions

Conditions are JSON, not code, so an editor can build them with dropdowns:

```json
{"left": "{{ nodes.collect_articles | length }}", "op": "gt", "right": 0}
{"all": [cond, cond]}   {"any": [cond, cond]}   {"not": cond}
```

Ops: `eq ne gt gte lt lte in not_in contains empty not_empty truthy falsy length_gt length_gte`.

### Transform ops

`flatten`, `map`, `pick`, `filter`, `dedupe` (with `normalize: url | text`), `sort` (multi-key, with a `rank` map for enums), `limit`, `enumerate`, `lookup` (join against another list), `render`.

## LLM providers

The provider and model for an llm node come from, in order: the node's `provider` and `model`, the workflow's `defaults`, then the environment. The sector workflow sets neither, so the environment decides and the same JSON runs on any model.

```bash
export JSONFLOW_LLM_PROVIDER=openai_compat   # anthropic (default) | openai_compat | facade
export JSONFLOW_LLM_MODEL=gpt-4.1            # required for anything but anthropic
```

| Provider | Endpoint | Structured output |
|---|---|---|
| `anthropic` | Anthropic Messages API via the SDK. Default model `claude-opus-5-5`. Needs `ANTHROPIC_API_KEY`. | Forced tool call |
| `openai_compat` | Any OpenAI-compatible `/chat/completions`: OpenAI, Azure OpenAI, vLLM, Ollama, LiteLLM, LM Studio, HuggingFace router, xAI. Plain HTTP, no SDK. | `tools` forced function call (default), `json_schema` response format, or `json` mode with the schema in the prompt |
| `facade` | This repo's `llm.llm_facade.LLMFacade` and `config/llm/llm.json`. Model as `provider/model`. | Facade's own |
| `scripted` | Canned answers for tests and offline demos. | n/a |

OpenAI-compatible settings:

```bash
export OPENAI_COMPAT_BASE_URL=http://localhost:8000/v1     # server root that serves /chat/completions
export OPENAI_COMPAT_API_KEY=...                           # sent as Bearer; optional for local servers
export OPENAI_COMPAT_STRUCTURED=tools                      # use json for servers without function calling
export OPENAI_COMPAT_HEADERS='{"api-key": "..."}'          # optional, e.g. Azure
```

Whatever the provider, every answer to a node with `output_schema` is validated by the engine and gets one corrected retry.

## MCP servers and tool categories

`config/jsonflow/servers.json` registers servers, not tools. Tools are discovered at run time.

| Transport | Use |
|---|---|
| `sajha_rest` | SAJHA via `/api/tools/list` and `/api/tools/execute`. Preferred for SAJHA because its JSON-RPC `tools/call` returns dicts as Python repr text. Supports `apikey` and `jwt` auth and optional `_worker_context` injection. |
| `mcp_http` | Any standard MCP server over Streamable HTTP: initialize handshake, session header, paginated `tools/list`, `tools/call`, JSON or SSE responses. |
| `fixture` | A JSON file of canned tools and responses. |

MCP has no notion of category, so each tool is mapped to `structured`, `unstructured`, `web` or `other`. The tool's own category metadata is checked first through `raw_category_map`, then name patterns in `categories`.

Against a live SAJHA v2.9.8 server with 121 tools, the default config yields:

| Category | Tools | Examples |
|---|---|---|
| structured | 43 | `duckdb_*`, `sqlselect_*`, `iris_*`, `get_credit_limits`, `olap_*`, `yahoo_*`, EDGAR financial statements |
| unstructured | 42 | `pdf_read`, `msdoc_*`, `document_search`, `file_read`, `confluence_*`, `sharepoint_*`, EDGAR text sections |
| web | 13 | `tavily_news_search`, `tavily_domain_search`, `tavily_web_search`, `tavily_research_search`, `ir_*`, `browser_*` |
| other | 7 | `generate_chart`, `workflow_list`, `jira_*` reads |

The remaining 16 tools are blocked by `deny_tools`: anything that sends, replies, creates, updates, uploads, refreshes or runs code. Blocked tools never appear in the palette and cannot be called.

`python -m jsonflow tools --json` emits the palette a canvas needs. Each entry has a ready node template, the category, and the input schema with internal `_`-prefixed fields removed.

## The sector events workflow

`config/jsonflow/workflows/sector_events.json`:

| Node | Type | Purpose |
|---|---|---|
| `build_queries` | transform | Four discovery queries built from `country` and `sector` |
| `discover_news` | for_each → `tavily_news_search` | Broad discovery, failures per query tolerated |
| `collect_articles` | transform | Flatten, dedupe by normalized URL then title, sort by score, keep `max_articles`, number them |
| `check_articles` | router | No articles goes to `no_news` |
| `extract_events` | llm | Cluster articles into events with the handover's event schema. Sources are cited by article number, never by URL. |
| `rank_events` | transform | Drop low materiality, rank by materiality then confidence, keep `max_events`, attach cited articles |
| `check_events` | router | No material events skips validation |
| `validate_events` | for_each → `tavily_domain_search` | One trusted-domain search per top event |
| `validation_digest` | transform | Pair each event with its validation results |
| `assess_validation` | llm | Corroborated, partially corroborated, not found, contradicted or not checked |
| `assemble_report` | transform | Final event list with validation attached |

Default budget: 10 tool calls and 4 LLM calls. A normal run uses 7 and 2.

## Verification so far

- **Unit and end-to-end tests:** 101 tests, all passing, including the web API, roles and the MCP endpoint over real HTTP, with synthetic fixtures and mocked HTTP transports. One runs the whole sector workflow with both LLM nodes going through the OpenAI-compatible HTTP path.
- **Browser walkthrough:** `tests/jsonflow_browser_e2e.py` drives Chromium through the public pages, sign-in, the builder, a run, building and publishing a new agent by drag and drop, and every admin tab, with zero console errors.
- **Live SAJHA:** the archived v2.9.8 server from mcp-intelligence-agent was run locally. Discovery, categorization, palette export and validation worked against its real catalog. Its real responses exposed one bug, a tool failure nested inside a success envelope, which is now fixed and covered by a test.
- **Live Tavily through SAJHA:** all 7 tool calls succeeded in about 8 seconds. 20 real articles were deduplicated to 15, and the trusted-domain searches returned sec.gov, cftc.gov and reuters.com results.
- **Not yet verified live:** the two LLM nodes, on any provider. No model credentials were available, so those ran on scripted or mocked answers.

## Known limits

- SAJHA's `tavily_news_search` fixes its 7-day lookback on the server side, so there is no `lookback_days` input yet.
- Tavily scores below SAJHA's configured `min_score` still come through. Add a `filter` step on `item.score` if low-relevance articles crowd the list.
- `assess_validation` is told to copy URLs exactly. A deterministic check that every `trusted_urls` entry appeared in the search results is not implemented yet.
- No persistence of customer memory yet. That belongs to a later phase.
