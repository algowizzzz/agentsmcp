(function () {
  "use strict";
  const { h, api, toast, modal, field, ago, jsonBlock } = JF;
  let me = null;
  const panel = () => document.getElementById("panel");
  const card = (...c) => h("div", { class: "card", style: { padding: "16px", marginBottom: "16px" } }, ...c);
  const fail = (e) => toast(e.message, true);

  // ---------------------------------------------------------------- users
  async function users() {
    const list = await api("/api/users");
    const uname = h("input", { class: "input", autocomplete: "off" }), dname = h("input", { class: "input" });
    const pw = h("input", { class: "input", type: "password", autocomplete: "new-password" });
    const role = h("select", { class: "input" }, h("option", { value: "admin", text: "Admin" }), h("option", { value: "super_admin", text: "Super admin" }));
    const rows = list.map((u) => {
      const roleSel = h("select", { class: "input", style: { width: "150px" }, "aria-label": "Role for " + u.username, disabled: u.id === me.id },
        h("option", { value: "admin", text: "Admin", selected: u.role === "admin" }), h("option", { value: "super_admin", text: "Super admin", selected: u.role === "super_admin" }));
      roleSel.addEventListener("change", async () => { try { await api("/api/users/" + u.id, { method: "PATCH", body: { role: roleSel.value } }); toast("Role updated; they were signed out."); } catch (e) { fail(e); users(); } });
      return h("tr", {}, h("td", {}, h("b", { text: u.display_name }), h("div", { class: "mono small muted", text: u.username })),
        h("td", {}, roleSel), h("td", {}, u.active ? h("span", { class: "chip ok", text: "Active" }) : h("span", { class: "chip bad", text: "Disabled" })),
        h("td", { class: "small muted", text: u.last_login_at ? ago(u.last_login_at) : "never" }),
        h("td", {}, h("div", { class: "row" },
          h("button", { class: "btn small", type: "button", disabled: u.id === me.id, onclick: async () => {
            try { await api("/api/users/" + u.id, { method: "PATCH", body: { active: !u.active } }); users(); } catch (e) { fail(e); } } }, u.active ? "Disable" : "Enable"),
          h("button", { class: "btn small", type: "button", onclick: () => resetPassword(u) }, "Reset password"))));
    });
    panel().replaceChildren(
      card(h("h2", { style: { fontSize: "16px", marginBottom: "12px" }, text: "Add a user" }),
        h("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px", alignItems: "end" } },
          field("Username", uname), field("Display name", dname), field("Initial password", pw), field("Role", role),
          h("button", { class: "btn primary", type: "button", onclick: async () => {
            try { await api("/api/users", { method: "POST", body: { username: uname.value, display_name: dname.value, password: pw.value, role: role.value } });
              toast("User created. Share the password with them securely."); users(); } catch (e) { fail(e); } } }, "Add user")),
        h("p", { class: "small muted", style: { margin: "8px 0 0" }, text: "Passwords need at least 10 characters with upper and lower case and a digit. Admins build and run agents; super admins also manage this page." })),
      card(h("table", { class: "tbl" }, h("thead", {}, h("tr", {}, ["Person", "Role", "Status", "Last sign-in", ""].map((t) => h("th", { text: t })))), h("tbody", {}, rows))));
  }

  function resetPassword(u) {
    const pw = h("input", { class: "input", type: "password", autocomplete: "new-password" });
    modal({ title: "Reset password for " + u.username, body: field("New password", pw, "They will be signed out everywhere."),
      actions: [{ label: "Cancel" }, { label: "Reset", primary: true, onClick: async () => {
        try { await api("/api/users/" + u.id + "/password", { method: "POST", body: { password: pw.value } }); toast("Password reset."); } catch (e) { fail(e); return true; } } }] });
  }

  // ---------------------------------------------------------------- categories
  async function categories() {
    const list = await api("/api/categories");
    const name = h("input", { class: "input" }), desc = h("input", { class: "input" });
    panel().replaceChildren(
      card(h("h2", { style: { fontSize: "16px", marginBottom: "12px" }, text: "Add a category" }),
        h("div", { style: { display: "grid", gridTemplateColumns: "1fr 2fr auto", gap: "10px", alignItems: "end" } }, field("Name", name), field("Description", desc),
          h("button", { class: "btn primary", type: "button", onclick: async () => {
            try { await api("/api/categories", { method: "POST", body: { name: name.value, description: desc.value } }); categories(); } catch (e) { fail(e); } } }, "Add")),
        h("p", { class: "small muted", style: { margin: "8px 0 0" }, text: "Every agent belongs to one category. Each category gets its own MCP endpoint." })),
      card(h("table", { class: "tbl" }, h("thead", {}, h("tr", {}, ["Category", "Description", "Agents", ""].map((t) => h("th", { text: t })))),
        h("tbody", {}, list.map((c) => h("tr", {}, h("td", {}, h("b", { text: c.name })), h("td", { class: "muted", text: c.description }), h("td", { text: String(c.agents) }),
          h("td", {}, h("button", { class: "btn small danger", type: "button", disabled: c.agents > 0, title: c.agents ? "Move its agents first" : "",
            onclick: async () => { try { await api("/api/categories/" + encodeURIComponent(c.name), { method: "DELETE" }); categories(); } catch (e) { fail(e); } } }, "Delete")))))))); 
  }

  // ---------------------------------------------------------------- servers
  async function servers() {
    const cfg = await api("/api/settings/servers");
    const ta = h("textarea", { class: "input", rows: 24, value: JSON.stringify(cfg, null, 2), "aria-label": "Server configuration" });
    const results = h("div", { class: "stack" });
    const testButtons = h("div", { class: "row", style: { flexWrap: "wrap" } }, Object.keys(cfg.servers || {}).map((name) => h("button", { class: "btn small", type: "button", onclick: async () => {
      results.prepend(h("div", { class: "notice small", text: "Testing " + name + "…" }));
      const r = await api("/api/settings/servers/" + encodeURIComponent(name) + "/test", { method: "POST" });
      results.firstChild.replaceWith(h("div", { class: "notice small " + (r.ok ? "ok" : "bad"), text: name + ": " + (r.ok ? r.tools + " tools found, " + r.allowed + " allowed" : r.error) }));
    } }, "Test " + name)));
    panel().replaceChildren(
      card(h("div", { class: "row", style: { marginBottom: "10px" } }, h("h2", { style: { fontSize: "16px" }, text: "MCP servers" }), h("div", { class: "grow" }),
          h("button", { class: "btn primary", type: "button", onclick: async () => {
            let parsed; try { parsed = JSON.parse(ta.value); } catch (e) { toast("That JSON does not parse.", true); return; }
            try { await api("/api/settings/servers", { method: "PUT", body: parsed }); toast("Saved. The tool list will reload."); servers(); } catch (e) { fail(e); } } }, "Save")),
        h("div", { class: "grid-2", style: { gridTemplateColumns: "minmax(0, 1fr) 320px" } }, ta,
          h("div", { class: "stack small", style: { color: "var(--ink-2)" } },
            h("b", { text: "Each server" }),
            h("div", {}, h("code", { text: "transport" }), ": sajha_rest for SAJHA, mcp_http for any standard MCP server."),
            h("div", {}, h("code", { text: "base_url" }), " or ", h("code", { text: "url" }), ". ", h("code", { text: "${VAR:-default}" }), " reads environment variables."),
            h("div", {}, h("code", { text: "auth" }), ": api_key_env names the variable holding the key. Never paste keys here."),
            h("div", {}, h("code", { text: "allow_tools" }), " and ", h("code", { text: "deny_tools" }), ": name patterns such as tavily_* or *_send_*. Keep write tools denied."),
            h("div", {}, h("code", { text: "raw_category_map" }), " and the top-level ", h("code", { text: "categories" }), " place tools under web, structured, unstructured or other."),
            h("b", { text: "Test", style: { marginTop: "8px" } }), testButtons, results))));
  }

  // ---------------------------------------------------------------- llm
  async function llm() {
    const s = await api("/api/settings/llm");
    const provider = h("select", { class: "input" }, [["anthropic", "Anthropic"], ["openai_compat", "OpenAI-compatible endpoint"]].map(([v, t]) => h("option", { value: v, text: t, selected: s.provider === v })));
    const model = h("input", { class: "input mono", value: s.model || "" });
    const base = h("input", { class: "input mono", value: s.base_url || "", placeholder: "https://host/v1" });
    const keyEnv = h("input", { class: "input mono", value: s.api_key_env || "", placeholder: "OPENAI_COMPAT_API_KEY" });
    const structured = h("select", { class: "input" }, [["tools", "Function calling (most servers)"], ["json_schema", "JSON schema response format"], ["json", "JSON mode, schema in the prompt"]]
      .map(([v, t]) => h("option", { value: v, text: t, selected: s.structured === v })));
    const timeout = h("input", { class: "input mono", type: "number", value: String(s.timeout || 120) });
    const compatOnly = h("div", { class: "stack" }, field("Base URL", base, "The address that serves /chat/completions."), field("Structured output method", structured));
    const sync = () => compatOnly.classList.toggle("hidden", provider.value !== "openai_compat");
    provider.addEventListener("change", () => { sync(); if (!keyEnv.value || keyEnv.value === "ANTHROPIC_API_KEY" || keyEnv.value === "OPENAI_COMPAT_API_KEY") keyEnv.value = provider.value === "anthropic" ? "ANTHROPIC_API_KEY" : "OPENAI_COMPAT_API_KEY"; });
    sync();
    const result = h("div");
    panel().replaceChildren(card(h("h2", { style: { fontSize: "16px", marginBottom: "12px" }, text: "Default model for LLM steps" }),
      h("div", { class: "stack", style: { maxWidth: "560px" } }, field("Provider", provider), field("Model", model, "Steps can override this."), compatOnly,
        field("Environment variable holding the API key", keyEnv, s.api_key_present ? "Set on the server." : "Not set on the server yet."),
        field("Timeout, seconds", timeout),
        h("div", { class: "row" }, h("button", { class: "btn primary", type: "button", onclick: async () => {
          try { await api("/api/settings/llm", { method: "PUT", body: { provider: provider.value, model: model.value, base_url: base.value, api_key_env: keyEnv.value, structured: structured.value, timeout: Number(timeout.value) } });
            toast("Saved."); llm(); } catch (e) { fail(e); } } }, "Save"),
          h("button", { class: "btn", type: "button", onclick: async () => {
            result.replaceChildren(h("div", { class: "notice small", text: "Sending a one-line test prompt…" }));
            const r = await api("/api/settings/llm/test", { method: "POST" });
            result.replaceChildren(h("div", { class: "notice small " + (r.ok ? "ok" : "bad"), text: r.ok ? "Model " + r.model + " replied: " + r.reply : r.error }));
          } }, "Test saved settings")), result)));
  }

  // ---------------------------------------------------------------- keys
  async function keys() {
    const [list, cats, info] = await Promise.all([api("/api/keys"), api("/api/categories"), api("/api/mcp/info")]);
    const name = h("input", { class: "input", placeholder: "e.g. sajha-agent-prod" });
    const boxes = cats.map((c) => { const b = h("input", { type: "checkbox", value: c.name }); return [b, h("label", { class: "row small" }, b, c.name)]; });
    panel().replaceChildren(
      card(h("h2", { style: { fontSize: "16px", marginBottom: "12px" }, text: "Create an API key" }),
        h("div", { class: "stack", style: { maxWidth: "560px" } }, field("Client name", name),
          h("div", { class: "field" }, h("span", { class: "lbl", text: "Limit to categories (none ticked = all)" }), h("div", { class: "row", style: { flexWrap: "wrap", gap: "14px" } }, boxes.map((b) => b[1]))),
          h("button", { class: "btn primary", type: "button", style: { alignSelf: "flex-start" }, onclick: async () => {
            try {
              const r = await api("/api/keys", { method: "POST", body: { name: name.value, categories: boxes.filter((b) => b[0].checked).map((b) => b[0].value) } });
              modal({ title: "Copy this key now", body: h("div", { class: "stack" }, h("p", { style: { margin: 0 }, text: "It will not be shown again." }), h("pre", { class: "json", text: r.key }),
                h("p", { class: "small muted", style: { margin: 0 }, text: "Clients send it as: Authorization: Bearer <key>" })) });
              keys();
            } catch (e) { fail(e); } } }, "Create key"))),
      card(h("h2", { style: { fontSize: "16px", marginBottom: "8px" }, text: "Endpoints" }),
        h("div", { class: "stack small" }, h("div", {}, h("b", { text: "All published agents: " }), h("code", { text: info.url })),
          ...info.categories.map((c) => h("div", {}, h("b", { text: c.name + ": " }), h("code", { text: c.url }))))),
      card(h("table", { class: "tbl" }, h("thead", {}, h("tr", {}, ["Client", "Key starts", "Categories", "Created", "Last used", ""].map((t) => h("th", { text: t })))),
        h("tbody", {}, list.map((k) => h("tr", { style: k.revoked ? { opacity: .5 } : {} }, h("td", {}, h("b", { text: k.name })), h("td", { class: "mono", text: k.prefix + "…" }),
          h("td", { text: k.categories.length ? k.categories.join(", ") : "all" }), h("td", { class: "small", text: k.created_by + ", " + ago(k.created_at) }),
          h("td", { class: "small", text: k.last_used_at ? ago(k.last_used_at) : "never" }),
          h("td", {}, k.revoked ? h("span", { class: "chip", text: "Revoked" }) : h("button", { class: "btn small danger", type: "button", onclick: async () => {
            try { await api("/api/keys/" + k.id, { method: "DELETE" }); keys(); } catch (e) { fail(e); } } }, "Revoke"))))))));
  }

  // ---------------------------------------------------------------- audit
  async function audit() {
    const list = await api("/api/audit?limit=300");
    panel().replaceChildren(card(h("table", { class: "tbl" }, h("thead", {}, h("tr", {}, ["When", "Who", "Action", "Target", "Detail"].map((t) => h("th", { text: t })))),
      h("tbody", {}, list.map((a) => h("tr", {}, h("td", { class: "small", title: a.at, text: ago(a.at) }), h("td", { text: a.actor }), h("td", {}, h("span", { class: "chip", text: a.action })),
        h("td", { class: "mono small", text: a.target }), h("td", { class: "mono small muted", style: { maxWidth: "380px", wordBreak: "break-word" }, text: a.detail })))))));
  }

  const TABS = { users, categories, servers, llm, keys, audit };
  async function show(tab) {
    document.querySelectorAll("[data-tab]").forEach((b) => b.setAttribute("aria-selected", b.dataset.tab === tab ? "true" : "false"));
    history.replaceState(null, "", "#" + tab);
    panel().replaceChildren(h("p", { class: "muted", text: "Loading…" }));
    try { await TABS[tab](); } catch (e) { panel().replaceChildren(h("div", { class: "notice bad", text: e.message })); }
  }

  document.addEventListener("DOMContentLoaded", async () => {
    me = await JF.topbar("admin", { requireUser: true });
    if (!me) return;
    if (me.role !== "super_admin") { panel().replaceChildren(h("div", { class: "notice warn", text: "This page is for super admins. Ask one if you need a change here." })); return; }
    document.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => show(b.dataset.tab)));
    show(TABS[location.hash.slice(1)] ? location.hash.slice(1) : "users");
  });
})();
