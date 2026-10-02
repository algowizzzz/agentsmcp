(function () {
  "use strict";
  const { h, api, toast, jsonBlock, ago, statusChip } = JF;
  const G = JFGraph;
  const S = { run: null, def: null, sel: null, timer: null, fitted: false, toolCats: {} };
  const runId = () => decodeURIComponent(location.pathname.split("/").pop());
  const fmt = (ms) => (ms == null ? "" : ms >= 1000 ? (ms / 1000).toFixed(1) + " s" : ms + " ms");
  const finished = () => ["succeeded", "failed"].includes(S.run.status);

  function analyse() {
    const st = {}, dur = {}, calls = {}, gotos = {}, order = [];
    for (const e of S.run.trace) {
      const base = (e.node || "").split("[")[0];
      if (e.event === "node_start") { st[e.node] = "running"; if (!order.includes(e.node)) order.push(e.node); }
      if (e.event === "node_end") { st[e.node] = e.status === "ok" ? "ok" : "error"; dur[e.node] = e.duration_ms; if (e.goto) gotos[e.node] = e.goto; }
      if (e.event === "tool_call" || e.event === "llm_call") (calls[base] = calls[base] || []).push(e);
    }
    if (finished()) for (const n of S.def.nodes) if (!st[n.id]) st[n.id] = "skipped";
    const edgeStates = {}, succ = G.successors(S.def);
    const ran = (id) => st[id] && st[id] !== "skipped";
    for (const n of S.def.nodes) for (const s of succ[n.id]) {
      const key = n.id + "|" + s.port + "|" + s.to;
      const taken = n.type === "router" ? gotos[n.id] === s.to && ran(s.to) : ran(n.id) && ran(s.to);
      if (taken) edgeStates[key] = "taken"; else if (finished()) edgeStates[key] = "skipped";
    }
    return { st, dur, calls, edgeStates, order };
  }

  function render() {
    const a = analyse();
    const subs = {};
    for (const n of S.def.nodes) {
      const c = a.calls[n.id] || [];
      const word = { ok: "done", error: "failed", running: "running", skipped: "not run" }[a.st[n.id]] || "waiting";
      const tools = c.filter((x) => x.event === "tool_call"), llms = c.filter((x) => x.event === "llm_call");
      subs[n.id] = [word, tools.length ? tools.length + " tool call" + (tools.length > 1 ? "s" : "") : "", llms.length ? llms.length + " LLM call" + (llms.length > 1 ? "s" : "") : "",
        n.type === "router" && S.run.trace.find((e) => e.event === "node_end" && e.node === n.id && e.goto) ? "→ " + S.run.trace.find((e) => e.event === "node_end" && e.node === n.id).goto : "",
        fmt(a.dur[n.id])].filter(Boolean).join(" · ");
    }
    G.render(document.getElementById("world"), S.def, { statuses: a.st, edgeStates: a.edgeStates, selected: S.sel, subtitles: subs, toolCats: S.toolCats,
      onNodeClick: (id) => { S.sel = id; render(); details(); } });
    if (!S.fitted) { fit(); S.fitted = true; }
    const max = Math.max(1, ...Object.values(a.dur).filter((x) => x != null));
    document.getElementById("trace").replaceChildren(...a.order.map((id) => h("button", { type: "button", class: "trace-row" + (S.sel === id ? " sel" : ""), onclick: () => { S.sel = id; render(); details(); } },
      h("div", { class: "row" }, h("span", { class: "dot " + ({ ok: "ok", error: "bad", running: "run" }[a.st[id]] || "idle") }),
        h("span", { class: "mono grow", style: { fontSize: "12.5px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }, text: id }),
        h("span", { class: "small", text: fmt(a.dur[id]) })),
      h("div", { class: "row", style: { paddingLeft: "16px" } }, h("div", { class: "bar" }, h("i", { style: { width: Math.max(2, Math.round(((a.dur[id] || 0) / max) * 100)) + "%" } })),
        h("span", { class: "small muted", text: (a.calls[id] || []).length ? (a.calls[id] || []).length + " calls" : "" })))),
      ...(finished() ? S.def.nodes.filter((n) => a.st[n.id] === "skipped").map((n) => h("button", { type: "button", class: "trace-row", style: { opacity: .6 }, onclick: () => { S.sel = n.id; render(); details(); } },
        h("div", { class: "row" }, h("span", { class: "dot idle" }), h("span", { class: "mono grow", style: { fontSize: "12.5px" }, text: n.id }), h("span", { class: "small muted", text: "not run" })))) : []));
    const r = S.run, s = r.stats || {};
    document.getElementById("run-status").replaceChildren(statusChip(r.status));
    document.getElementById("run-stats").replaceChildren(
      s.tool_calls != null ? h("span", { class: "chip", text: "Tool calls " + s.tool_calls + " / " + s.budgets.tool }) : null,
      s.llm_calls != null ? h("span", { class: "chip", text: "LLM calls " + s.llm_calls + " / " + s.budgets.llm }) : null,
      s.duration_ms != null ? h("span", { class: "chip", text: fmt(s.duration_ms) }) : null);
  }

  function fit() {
    const wrap = document.getElementById("canvas"), b = G.bbox(S.def);
    const scale = Math.max(0.4, Math.min(1.1, Math.min((wrap.clientWidth - 80) / (b.w + 80), (wrap.clientHeight - 60) / (b.h + 80))));
    document.getElementById("world").style.transform = `scale(${Math.round(scale * 20) / 20})`;
    wrap.scrollLeft = Math.max(0, (b.x - 40) * scale); wrap.scrollTop = Math.max(0, (b.y - 40) * scale);
  }

  async function details() {
    const head = document.getElementById("insp-head"), body = document.getElementById("insp-body");
    const r = S.run;
    if (!S.sel) {
      head.replaceChildren(h("b", { text: "Run summary" }), h("span", { class: "small muted", text: "Started " + ago(r.created_at) + " · " + r.trigger + " by " + r.triggered_by + " · agent v" + r.agent_version }));
      body.replaceChildren(
        r.error ? h("div", { class: "notice bad", text: r.error }) : null,
        !finished() ? h("div", { class: "notice", text: "Running. This page updates every second." }) : null,
        (r.stats && r.stats.node_errors && r.stats.node_errors.length) ? h("section", { class: "stack" }, h("h3", { class: "section-title", text: "Steps that failed but let the run continue" }),
          ...r.stats.node_errors.map((e) => h("div", { class: "notice warn small" }, h("b", { class: "mono", text: e.node }), ": " + e.error))) : null,
        h("section", { class: "stack" }, h("h3", { class: "section-title", text: "Output" }), finished() ? jsonBlock(r.output) : h("p", { class: "muted small", text: "Available when the run finishes." })),
        h("section", { class: "stack" }, h("h3", { class: "section-title", text: "Inputs" }), jsonBlock(r.inputs)),
        h("p", { class: "small muted", style: { margin: 0 }, text: "Click a step on the canvas or in the trace to see its output and every call it made." }));
      return;
    }
    const n = S.def.nodes.find((x) => x.id === S.sel);
    const a = analyse();
    head.replaceChildren(h("div", { class: "row" }, JF.icon(G.kindOf(n, S.toolCats)), h("b", { class: "mono", text: n.id }), h("div", { class: "grow" }),
      h("button", { class: "btn small", type: "button", onclick: () => { S.sel = null; render(); details(); } }, "Run summary")),
      h("span", { class: "small muted", text: G.subtitle(n) + (a.dur[n.id] != null ? " · " + fmt(a.dur[n.id]) : "") }));
    const out = h("div", { class: "stack" }, h("p", { class: "small muted", style: { margin: 0 }, text: "Loading…" }));
    const errEvent = r.trace.find((e) => e.event === "node_end" && e.node === n.id && e.status === "error");
    const calls = (r.calls || []).filter((c) => c.startsWith(n.id + "."));
    body.replaceChildren(errEvent ? h("div", { class: "notice bad", text: errEvent.error }) : null,
      h("section", { class: "stack" }, h("h3", { class: "section-title", text: "Output" }), out),
      h("section", { class: "stack" }, h("h3", { class: "section-title", text: "Calls · " + calls.length }),
        ...(calls.length ? calls.map((c) => {
          const d = h("details", {}, h("summary", { class: "mono small", text: c }));
          d.addEventListener("toggle", async () => { if (d.open && d.children.length === 1) {
            try { d.append(jsonBlock(await api("/api/runs/" + encodeURIComponent(r.id) + "/calls/" + encodeURIComponent(c)))); } catch (e) { d.append(h("div", { class: "notice bad", text: e.message })); } } });
          return d;
        }) : [h("p", { class: "small muted", style: { margin: 0 }, text: "This step made no tool or LLM calls." })])),
      h("section", { class: "stack" }, h("h3", { class: "section-title", text: "Step definition" }), jsonBlock(n)));
    try { out.replaceChildren(jsonBlock(await api("/api/runs/" + encodeURIComponent(r.id) + "/nodes/" + encodeURIComponent(n.id)))); }
    catch (e) { out.replaceChildren(h("p", { class: "small muted", style: { margin: 0 }, text: a.st[n.id] === "skipped" ? "This step did not run." : e.message })); }
  }

  async function load() {
    S.run = await api("/api/runs/" + encodeURIComponent(runId()));
    if (!S.def) {
      S.def = G.normalize(JSON.parse(JSON.stringify(S.run.definition || { nodes: [] })));
      G.autoLayout(S.def);
      document.getElementById("run-id").textContent = S.run.id;
      const link = document.getElementById("agent-link");
      link.textContent = (S.def.name || S.run.agent_id); link.href = "/app/agents/" + encodeURIComponent(S.run.agent_id);
      document.getElementById("btn-edit").href = link.href;
      document.title = "Run " + S.run.id + " · jsonflow";
    }
    render();
    if (!S.sel || !finished()) details();
    if (finished() && S.timer) { clearInterval(S.timer); S.timer = null; details(); }
  }

  document.addEventListener("DOMContentLoaded", async () => {
    try { await api("/api/me"); } catch (e) { return; }
    try {  // tool categories only colour the icons; the page works without them
      const pal = await api("/api/palette");
      for (const [cat, tools] of Object.entries(pal.categories)) for (const t of tools) S.toolCats[t.server + "/" + t.tool] = cat;
    } catch (e) { /* keep generic icons */ }
    try { await load(); } catch (e) { document.getElementById("insp-body").replaceChildren(h("div", { class: "notice bad", text: e.message })); return; }
    if (!finished()) S.timer = setInterval(() => load().catch(() => {}), 1000);
    document.getElementById("btn-rerun").onclick = async () => {
      try { const r = await api("/api/agents/" + encodeURIComponent(S.run.agent_id) + "/run", { method: "POST", body: { inputs: S.run.inputs || {} } });
        location.href = "/app/runs/" + r.run_id; } catch (e) { toast(e.message, true); }
    };
  });
})();
