(function () {
  const { h, api, toast, modal, field, ago, statusChip } = JF;
  let agents = [], categories = [], filter = "", activeCat = "";

  function card(a) {
    return h("article", { class: "card agent-card" },
      h("div", { class: "row" },
        h("a", { href: "/app/agents/" + encodeURIComponent(a.id), style: { fontWeight: 600, fontSize: "15px", textDecoration: "none", color: "var(--ink)" }, text: a.name }),
        h("div", { class: "grow" }),
        a.published ? h("span", { class: "chip pub", text: "Published" }) : h("span", { class: "chip", text: "Draft" })),
      h("div", { class: "mono small muted", text: a.id + " · v" + a.version }),
      h("p", { class: "small", style: { margin: 0, color: "var(--ink-2)", minHeight: "20px" }, text: a.description || "No description yet." }),
      h("div", { class: "row small muted" }, statusChip(a.last_status), h("span", { text: a.last_run_at ? "last run " + ago(a.last_run_at) : "" }),
        h("div", { class: "grow" }), h("span", { text: a.run_count + " runs" })),
      h("div", { class: "row" },
        h("a", { class: "btn small", href: "/app/agents/" + encodeURIComponent(a.id), text: "Open builder" }),
        h("button", { class: "btn small", type: "button", onclick: () => runDialog(a) }, "Run"),
        h("div", { class: "grow" }),
        h("span", { class: "small muted", text: "by " + a.updated_by + ", " + ago(a.updated_at) })));
  }

  function render() {
    const q = filter.toLowerCase();
    const list = agents.filter((a) => (!activeCat || a.category === activeCat) &&
      (!q || (a.name + " " + a.id + " " + a.description).toLowerCase().includes(q)));
    document.getElementById("count").textContent = agents.length + " total";
    const box = document.getElementById("agents");
    box.replaceChildren();
    const cats = categories.map((c) => c.name).filter((n) => !activeCat || n === activeCat);
    let shown = 0;
    for (const cat of cats) {
      const items = list.filter((a) => a.category === cat);
      if (!items.length && q) continue;
      shown += items.length;
      box.append(h("div", { class: "cat-head" }, h("h2", { text: cat }), h("span", { class: "small muted", text: items.length + " agent" + (items.length === 1 ? "" : "s") })),
        items.length ? h("div", { class: "agent-grid" }, items.map(card)) : h("p", { class: "small muted", style: { margin: "0 0 8px" }, text: "No agents in this category yet." }));
    }
    if (!shown && q) box.append(h("p", { class: "muted", text: "No agents match your search." }));
    const f = document.getElementById("filters");
    const chip = (label, val) => h("button", { type: "button", class: "btn small" + (activeCat === val ? " primary" : ""), "aria-pressed": activeCat === val ? "true" : "false",
      onclick: () => { activeCat = val; render(); } }, label);
    f.replaceChildren(chip("All categories", ""), categories.map((c) => chip(c.name + " · " + c.agents, c.name)));
  }

  async function runDialog(a) {
    const full = await api("/api/agents/" + encodeURIComponent(a.id));
    const inputs = full.definition.inputs || {};
    const controls = {};
    const rows = Object.entries(inputs).map(([name, p]) => {
      const def = p.default === undefined || p.default === null ? "" : (typeof p.default === "string" ? p.default : JSON.stringify(p.default));
      const el = h("input", { class: "input" + (p.type === "string" ? "" : " mono"), value: def });
      controls[name] = [el, p];
      return field(name + " (" + p.type + ")" + (p.required ? " · required" : ""), el, p.description);
    });
    if (!full.validation.ok) toast("This agent has validation problems. Open the builder to fix them.", true);
    modal({ title: "Run " + a.name, body: h("div", { class: "stack" }, rows.length ? rows : h("p", { class: "muted", text: "This agent takes no inputs." })),
      actions: [{ label: "Cancel" }, { label: "Run", primary: true, onClick: async () => {
        const vals = {};
        for (const [name, [el, p]] of Object.entries(controls)) {
          if (el.value === "") continue;
          if (p.type === "string") vals[name] = el.value;
          else { try { vals[name] = JSON.parse(el.value); } catch (e) { toast(name + " must be valid " + p.type, true); return true; } }
        }
        try { const r = await api("/api/agents/" + encodeURIComponent(a.id) + "/run", { method: "POST", body: { inputs: vals } });
          location.href = "/app/runs/" + r.run_id; } catch (e) { toast(e.message, true); return true; }
      } }] });
  }

  function newAgent() {
    const name = h("input", { class: "input", placeholder: "e.g. Limit watch" });
    const cat = h("select", { class: "input" }, categories.map((c) => h("option", { value: c.name, text: c.name })));
    const desc = h("input", { class: "input", placeholder: "What it does, in one sentence" });
    const start = h("select", { class: "input" }, h("option", { value: "blank", text: "Blank canvas" }),
      h("option", { value: "copy", text: "Copy an existing agent" }), h("option", { value: "json", text: "Paste agent JSON" }));
    const copyOf = h("select", { class: "input" }, agents.map((a) => h("option", { value: a.id, text: a.name + " (" + a.id + ")" })));
    const json = h("textarea", { class: "input", rows: 8, placeholder: '{"nodes": [...], "edges": [...]}' });
    const copyRow = field("Agent to copy", copyOf), jsonRow = field("Agent JSON", json, "Exported from the builder's JSON view.");
    const sync = () => { copyRow.classList.toggle("hidden", start.value !== "copy"); jsonRow.classList.toggle("hidden", start.value !== "json"); };
    start.addEventListener("change", sync); sync();
    modal({ title: "New agent", body: h("div", { class: "stack" }, field("Name", name, "The name also sets the id, which is the MCP tool name."),
        field("Category", cat), field("Description", desc), field("Start from", start), copyRow, jsonRow),
      actions: [{ label: "Cancel" }, { label: "Create", primary: true, onClick: async () => {
        let definition;
        try {
          if (start.value === "copy") definition = (await api("/api/agents/" + encodeURIComponent(copyOf.value))).definition;
          if (start.value === "json") definition = JSON.parse(json.value);
          const r = await api("/api/agents", { method: "POST", body: { name: name.value, category: cat.value, description: desc.value, definition } });
          location.href = "/app/agents/" + r.id;
        } catch (e) { toast(e instanceof SyntaxError ? "That JSON does not parse." : e.message, true); return true; }
      } }] });
  }

  async function loadRuns() {
    const runs = await api("/api/runs?limit=12");
    const box = document.getElementById("runs");
    box.replaceChildren(...(runs.length ? runs.map((r) => h("a", { href: "/app/runs/" + r.id, class: "trace-row", style: { textDecoration: "none", color: "inherit" } },
      h("div", { class: "row" }, h("span", { class: "dot " + ({ succeeded: "ok", failed: "bad" }[r.status] || "run") }),
        h("span", { class: "grow", style: { fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }, text: r.agent_name || r.agent_id }),
        h("span", { class: "small muted", text: ago(r.created_at) })),
      h("div", { class: "small muted", style: { paddingLeft: "16px" }, text: r.status + " · " + r.trigger + " · " + r.triggered_by }))) :
      [h("p", { class: "small muted", style: { margin: 0 }, text: "No runs yet." })]));
  }

  async function loadMcp() {
    const info = await api("/api/mcp/info");
    const box = document.getElementById("mcp");
    box.replaceChildren(
      h("div", {}, h("b", { text: info.published + " published" }), " agent" + (info.published === 1 ? "" : "s") + " available."),
      h("div", {}, h("div", { class: "muted", text: "All agents" }), h("code", { text: info.url })),
      h("details", {}, h("summary", { text: "One category per endpoint" }),
        h("div", { class: "stack", style: { marginTop: "6px" } }, info.categories.map((c) => h("div", {}, h("div", { class: "muted", text: c.name }), h("code", { text: c.url }))))),
      h("a", { href: "/guide#publish", text: "How to connect a client" }));
  }

  document.addEventListener("DOMContentLoaded", async () => {
    const user = await JF.topbar("agents", { requireUser: true });
    if (!user) return;
    [agents, categories] = await Promise.all([api("/api/agents"), api("/api/categories")]);
    render();
    document.getElementById("search").addEventListener("input", (e) => { filter = e.target.value; render(); });
    document.getElementById("new").addEventListener("click", newAgent);
    loadRuns(); loadMcp();
    setInterval(loadRuns, 10000);
  });
})();
